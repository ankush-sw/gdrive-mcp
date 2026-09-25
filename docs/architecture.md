# Architecture: Custom Google Workspace MCP Server

How the server works, how it authenticates, and how requests flow from any MCP host through this process to Google APIs and back. Read this if you want to understand the system design, extend it, or build something similar for a different API.

---

## Table of Contents

- [System Overview](#system-overview)
- [Components](#components)
- [MCP Protocol and Transport](#mcp-protocol-and-transport)
- [OAuth Authentication Flow](#oauth-authentication-flow)
- [Request Lifecycle](#request-lifecycle)
- [API-to-Tool Mapping](#api-to-tool-mapping)
- [URL Construction](#url-construction)
- [Error Handling](#error-handling)
- [Security Model](#security-model)
- [Design Decisions](#design-decisions)

---

## System Overview

```
MCP HOST (Claude, Cursor, ChatGPT, Codex, Gemini, ...)
────────────────────────────────
  Agent
     |
     | stdin/stdout (JSON-RPC 2.0)
     v
PYTHON SERVER (FastMCP)
───────────────────────
  server.py
     |
     | HTTPS (google-api-python-client)
     v
GOOGLE APIs
───────────
  Drive API v3
  Docs API v1
  Sheets API v4
  Slides API v1
```

The server is a local Python process. Cursor spawns it as a child process and communicates over stdio using JSON-RPC 2.0 (the MCP protocol). The server translates MCP tool calls into Google API requests using OAuth 2.0 credentials stored on disk.

---

## Components

### Cursor IDE (Client)

Cursor acts as the MCP client. When you make a request in Composer, the agent decides which MCP tool to call, serializes the arguments as JSON-RPC, and writes them to the server's stdin. It reads the response from stdout.

Cursor manages the server lifecycle: it spawns the process on first use, keeps it alive for the session, and kills it on shutdown.

### FastMCP Server (server.py)

The server uses [FastMCP](https://github.com/jlowin/fastmcp), a Python framework that handles:

- MCP protocol negotiation (initialize, tools/list, tools/call)
- JSON-RPC serialization and deserialization
- Tool registration via `@mcp.tool()` decorators
- Input validation from tool parameter type hints
- stdio transport (reads stdin, writes stdout)

The server itself has no web framework, no HTTP listener, and no background threads. It's a single-threaded process that reads one request at a time from stdin.

### Google API Clients

Three service objects are lazily initialized on first use:

- `_drive()` returns a Drive API v3 client
- `_docs()` returns a Docs API v1 client
- `_sheets()` returns a Sheets API v4 client
- `_slides()` returns a Slides API v1 client

All four share the same OAuth credentials. The `google-api-python-client` library handles HTTP connection pooling, retries, and JSON parsing.

### Credential Storage

```
~/.gdrive-mcp/
  gcp-oauth.keys.json       Client ID + secret (never changes)
  token.json                 Access token + refresh token (auto-refreshed)

~/.config/{{API_KEYS_DIR}}/
  keys.env                   Shared API keys (not used by the MCP server directly)
```

OAuth credentials live outside any git repo. The server reads them at startup and refreshes expired tokens automatically. API keys are loaded separately for scripts and Gemini tooling.

---

## MCP Protocol and Transport

MCP uses JSON-RPC 2.0 over stdio. The protocol has three phases:

**1. Initialize.** Cursor sends an `initialize` request. The server responds with its capabilities (tools, resources, prompts) and protocol version.

```json
{"jsonrpc":"2.0","id":1,"method":"initialize",
 "params":{"protocolVersion":"2024-11-05",
           "clientInfo":{"name":"cursor","version":"1.0"}}}
```

**2. List tools.** Cursor requests the tool catalog. The server returns all 29 tools with their names, descriptions, and parameter schemas (auto-generated from Python type hints and docstrings).

**3. Call tools.** When the agent decides to use a tool, Cursor sends a `tools/call` request with the tool name and arguments. The server executes it and returns the result.

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call",
 "params":{"name":"search_drive",
           "arguments":{"query":"roadmap","page_size":10}}}
```

All communication is synchronous from the server's perspective: read request, process, write response, repeat. FastMCP handles the protocol layer so the tool functions only deal with business logic.

---

## OAuth Authentication Flow

Initial authorization happens once via `auth.py`. After that, the server handles token refresh automatically.

### First-time auth (auth.py)

```
USER runs auth.py
     |
     | 1. Build auth URL with scopes
     v
BROWSER opens Google sign-in
     |
     | 2. User approves scopes
     v
GOOGLE redirects to localhost:8087
     |
     | 3. auth.py captures the auth code
     v
auth.py exchanges code for tokens
     |
     | 4. Writes access + refresh token
     v
~/.gdrive-mcp/token.json saved
```

The auth script runs a minimal HTTP server on localhost to capture the OAuth callback. It bypasses Python's `webbrowser` module (which fails in Cursor's terminal on macOS) and uses `subprocess.run(["open", url])` directly.

### Token refresh (server.py, automatic)

When the server starts or when a token expires mid-session, `_get_credentials()` checks validity and refreshes using the stored refresh token. No browser interaction needed.

```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN_PATH.write_text(creds.to_json())
```

### OAuth Scopes

Four scopes cover all 29 tools (matches `SCOPES` in `server.py` and `auth.py`):

| Scope | Grants |
|-------|--------|
| `drive` | Search, list, read, upload, copy, move, export, create folders, comments, share |
| `documents` | Read and write Google Docs |
| `spreadsheets` | Read and write Google Sheets |
| `presentations` | Read and write Google Slides |

Adding a new scope requires deleting `token.json` and re-running `auth.py`.

---

## Request Lifecycle

A complete request from user query to response:

```
1. User asks Cursor: "find my roadmap docs"
      |
2. Agent selects tool: search_drive
      |
3. Cursor writes JSON-RPC to server stdin
      |
4. FastMCP routes to search_drive()
      |
5. search_drive() builds Drive API query:
   q = "fullText contains 'roadmap' and trashed = false"
      |
6. google-api-python-client sends HTTPS request
   to googleapis.com/drive/v3/files
      |
7. Google returns JSON file list
      |
8. _format_file() normalizes each result:
   adds URL, extracts owner name, flattens metadata
      |
9. Server returns JSON string to Cursor via stdout
      |
10. Agent presents results to user
```

Total round-trip is typically 1-3 seconds, dominated by the Google API call (step 6).

---

## API-to-Tool Mapping

Each tool maps to one or two Google API calls:

| Tool | API | Method(s) |
|------|-----|-----------|
| `search_drive` | Drive v3 | `files.list` with `fullText contains` query |
| `list_recent_files` | Drive v3 | `files.list` ordered by `modifiedTime desc` |
| `list_folder_contents` | Drive v3 | `files.list` with `parents` filter |
| `list_shared_with_me` | Drive v3 | `files.list` with `sharedWithMe = true` |
| `list_starred_files` | Drive v3 | `files.list` with `starred = true` |
| `get_file_metadata` | Drive v3 | `files.get` with field selection |
| `get_file_content` | Drive v3 | `files.export` (Workspace files) or `files.get_media` (binary) |
| `get_file_comments` | Drive v3 | `comments.list` with nested replies |
| `get_doc_content` | Docs v1 | `documents.get`, then extract text from body elements |
| `update_google_doc` | Docs v1 | `documents.batchUpdate` with user-provided operations |
| `create_google_doc` | Docs v1 | `documents.create`, optionally `documents.batchUpdate` |
| `read_sheet` | Sheets v4 | `spreadsheets.values.get` |
| `update_sheet_cells` | Sheets v4 | `spreadsheets.values.update` |
| `get_presentation` | Slides v1 | `presentations.get`, then summarize slides |
| `get_slide_content` | Slides v1 | `presentations.get`, then extract text from target slide |
| `update_presentation` | Slides v1 | `presentations.batchUpdate` with user-provided operations |
| `create_presentation` | Slides v1 | `presentations.create` |

---

## URL Construction

Every file result includes a clickable Google URL. The server tries `webViewLink` from the Drive API first (most reliable). If that's missing, it falls back to a MIME-type-based template:

```python
MIME_URL_MAP = {
    "application/vnd.google-apps.document":
        "https://docs.google.com/document/d/{id}/edit",
    "application/vnd.google-apps.spreadsheet":
        "https://docs.google.com/spreadsheets/d/{id}/edit",
    "application/vnd.google-apps.presentation":
        "https://docs.google.com/presentation/d/{id}/edit",
    "application/vnd.google-apps.form":
        "https://docs.google.com/forms/d/{id}/edit",
}
```

For non-Workspace files (PDFs, images, etc.), the fallback is `https://drive.google.com/file/d/{id}/view`.

---

## Error Handling

The server handles errors at two levels:

**Google API errors** (4xx/5xx from googleapis.com) propagate as `HttpError` exceptions. FastMCP catches these and returns them as MCP error responses. Common causes: expired token (re-auth needed), file not found, insufficient permissions.

**Input validation** happens through Python type hints. FastMCP rejects calls with missing required arguments or wrong types before the tool function runs.

**Scope errors** occur when the token doesn't include a needed scope (e.g., trying to edit Slides without the `presentations` scope). The fix is always: delete `token.json`, update SCOPES in both `server.py` and `auth.py`, re-run auth.

---

## Security Model

**Credentials on disk.** Both the client secret and tokens are stored as plain JSON files at `~/.gdrive-mcp/`. They aren't encrypted. Anyone with read access to your home directory can use them. This is the same model used by `gcloud` CLI and most Google client libraries.

**Scopes match the tools.** The server requests full `drive` plus Docs, Sheets, and Slides write. That is required for move, share, upload, comments, and in-place edits. It is not a readonly Drive client. Revoke from your Google Account when you uninstall.

**No network exposure.** The server has no HTTP listener. It communicates only via stdin/stdout with Cursor. The auth script's HTTP server runs on localhost for a single request and shuts down immediately.

**Token refresh.** Refresh tokens don't expire unless revoked. Access tokens expire after 1 hour and are refreshed automatically. If you revoke access in your Google Account settings, the server stops working until you re-authorize.

---

## Design Decisions

**Why Python over Node.js?** The existing Node.js MCP servers for Google Drive (`@modelcontextprotocol/server-gdrive`, `@isaacphi/mcp-gdrive`) had hardcoded scopes and limited tool sets. Python's `google-api-python-client` provides clean, well-documented access to all Google APIs. FastMCP made the protocol layer trivial.

**Why FastMCP?** It handles all MCP protocol details (JSON-RPC, tool registration, parameter schemas) with minimal boilerplate. A tool is just a decorated function with type hints and a docstring. No manual schema writing.

**Why stdio transport?** Cursor's MCP integration for local servers uses stdio (spawns a child process, pipes stdin/stdout). SSE transport is for remote servers. Since this server runs locally with user credentials, stdio is simpler and more secure.

**Why store credentials outside the repo?** OAuth secrets and tokens must never end up in git. `~/.gdrive-mcp/` keeps them in the home directory, the same pattern as `gcloud`.

**Why a separate auth.py?** The server itself can't reliably open a browser (it runs as a child process of Cursor with limited terminal capabilities). A separate auth script runs interactively, opens the browser, captures the callback, and saves the token. The server just reads the token file.

---

**Version:** 1.4
**Last Updated:** September 12, 2026
