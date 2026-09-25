# Building Custom MCP Servers from Public APIs

A practical guide for turning any well-documented, OAuth-authenticated public API into a custom MCP server any host can run. Based on lessons learned building the Google Workspace MCP (Drive, Docs, Sheets, Slides).

This isn't theory. Every section comes from a real problem encountered during development.

---

## Table of Contents

- [When to Build a Custom MCP](#when-to-build-a-custom-mcp)
- [Prerequisites](#prerequisites)
- [Step 1: Map the API Surface](#step-1-map-the-api-surface)
- [Step 2: Design Your Tool Set](#step-2-design-your-tool-set)
- [Step 3: Set Up OAuth Credentials](#step-3-set-up-oauth-credentials)
- [Step 4: Build the Server](#step-4-build-the-server)
- [Step 5: Handle Authentication](#step-5-handle-authentication)
- [Step 6: Configure Cursor](#step-6-configure-cursor)
- [Step 7: Test End-to-End](#step-7-test-end-to-end)
- [Tool Design Principles](#tool-design-principles)
- [Common Pitfalls](#common-pitfalls)
- [Framework Options](#framework-options)

---

## When to Build a Custom MCP

Build a custom server when:

- **Existing MCP servers are too limited.** The community server only supports search but you need read/write. Or it hardcodes scopes you can't change.
- **You need multiple APIs in one server.** Google Drive + Docs + Sheets + Slides as a single connection, not four separate MCP servers.
- **You want native URLs and metadata.** Generic servers often return IDs without links. A custom server can format results exactly how you need them.
- **The API is well-documented with client libraries.** Google, GitHub, Slack, Notion, Linear, Salesforce, Datadog all qualify.

Don't build a custom server when:

- An existing MCP server already does what you need. Check [MCP servers directory](https://github.com/modelcontextprotocol/servers) and npm/PyPI first.
- The API is internal or undocumented. You'll spend more time reverse-engineering than building.
- You only need one or two simple calls. A quick script or direct API call is faster than standing up a full MCP server.

---

## Prerequisites

**For any custom MCP server, you need:**

1. A working API with documentation and a client library (Python or Node.js)
2. OAuth credentials or API keys for authentication
3. Python 3.11+ with `fastmcp` (recommended) or Node.js with `@modelcontextprotocol/sdk`
4. Cursor IDE with MCP support enabled

**Time estimate:** 2-4 hours for a server with 10-20 tools, including auth setup and testing.

---

## Step 1: Map the API Surface

Before writing any code, list every API endpoint you want to expose. Group them by capability:

```
GOOGLE WORKSPACE EXAMPLE
────────────────────────
Read operations:
  - Drive: search, list recent, list folder, get metadata, get content
  - Docs: get document text
  - Sheets: read cell range
  - Slides: get presentation, get slide text

Write operations:
  - Docs: insert/replace/delete text, create document
  - Sheets: write cell range
  - Slides: modify slides, create presentation

Browse operations:
  - Drive: shared with me, starred, folder contents, comments
```

This inventory becomes your tool list. Each line maps to one MCP tool.

---

## Step 2: Design Your Tool Set

**Naming.** Use `verb_noun` format: `search_drive`, `get_file_content`, `update_sheet_cells`. The agent reads these names when deciding which tool to call, so clarity matters.

**Granularity.** One tool per distinct operation. Don't combine "search" and "list recent" into a single "find files" tool with a mode parameter. Separate tools are easier for the agent to reason about.

**Parameters.** Use the minimum required parameters. Add optional parameters with sensible defaults. Every parameter needs a clear docstring because the agent reads it.

```python
@mcp.tool()
def search_drive(
    query: str,
    page_size: int = 20,
    page_token: str | None = None
) -> str:
    """Search for files in Google Drive by name or content.

    Args:
        query: Search text (matches file names and contents).
        page_size: Results per page, max 100.
        page_token: Token for fetching the next page of results.
    """
```

**Return format.** Always return JSON strings, not Python objects. Include enough context for the agent to present useful results: names, URLs, dates, not just IDs.

**Pagination.** For list operations, accept `page_size` and `page_token`. Return `nextPageToken` in the response when there are more results. Cap `page_size` at a reasonable maximum (100 for most APIs).

---

## Step 3: Set Up OAuth Credentials

Most APIs worth building an MCP for use OAuth 2.0. The setup pattern is consistent:

1. **Create a project** in the API provider's developer console
2. **Enable the specific APIs** you need
3. **Create OAuth credentials** (Desktop app type for local servers)
4. **Configure the consent screen** with the scopes you need
5. **Download the client secret** as JSON

**Key scoping decision:** Request the minimum scopes that cover your tool set. Read-only scopes for read-only tools. Write scopes only for tools that modify data. You can always add scopes later by re-authorizing.

**Store credentials outside your repo.** Use `~/.your-app-name/` or `~/.config/your-app-name/`. Never commit client secrets or tokens to git.

---

## Step 4: Build the Server

### With FastMCP (Python, recommended)

```python
from fastmcp import FastMCP

mcp = FastMCP(name="My API Server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description for the agent."""
    result = call_the_api(param)
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

FastMCP handles all protocol details. You write normal Python functions with type hints and docstrings. It generates the JSON Schema for parameters automatically.

### Server structure pattern

```python
# 1. Configuration (scopes, paths, constants)
SCOPES = [...]
CREDS_DIR = Path(...)

# 2. Auth (credential loading, token refresh)
def _get_credentials(): ...

# 3. Service builders (lazy initialization)
def _api_client(): ...

# 4. Helpers (shared formatting, pagination)
def _format_result(): ...
def _list_items(): ...

# 5. Tools (decorated functions, grouped by API)
@mcp.tool()
def search_items(): ...

# 6. Entry point
mcp.run(transport="stdio")
```

Keep tool functions thin. They should validate input, call the API, format the response, and return. Business logic belongs in helper functions.

---

## Step 5: Handle Authentication

**The hardest part of the whole project.** Not because OAuth is complex, but because the server runs as a child process of Cursor with limited terminal and browser access.

### The problem

MCP servers communicate via stdio. They can't open a browser window. They can't prompt the user for input. The first-time OAuth flow needs both.

### The solution: separate auth script

Write a standalone `auth.py` that:

1. Reads the client secret from disk
2. Opens the browser for Google/provider sign-in
3. Runs a temporary localhost HTTP server to capture the callback
4. Exchanges the auth code for tokens
5. Saves the tokens to disk

The MCP server then reads the saved tokens at startup. It handles refresh automatically but never needs to open a browser.

### macOS-specific fix

Python's `webbrowser.open()` often fails in Cursor's terminal because `osascript` can't run in that context. Use `subprocess.run(["open", url])` directly:

```python
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

# Build the auth URL from your OAuth flow
auth_url = flow.authorization_url(access_type="offline")[0]

# Open browser directly (bypasses webbrowser module)
subprocess.run(["open", auth_url])

# Capture callback on localhost
server = HTTPServer(("localhost", 8087), CallbackHandler)
server.handle_request()
```

### Token refresh in the server

```python
def _get_credentials():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return creds
```

This handles 99% of cases. The only time re-auth is needed is when scopes change or the user revokes access.

---

## Step 6: Configure Cursor

Add your server to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "My API Server": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/server.py"],
      "env": {
        "CREDS_DIR": "/path/to/credentials"
      }
    }
  }
}
```

**Use absolute paths.** Cursor spawns the process from an unpredictable working directory. Relative paths break.

**Use the venv Python.** Don't rely on system Python or `python3` being in PATH. Point directly to the venv binary.

**Pass config via environment variables.** Don't hardcode paths in the server. Use `os.environ.get()` with sensible defaults.

---

## Step 7: Test End-to-End

Before relying on Cursor to test, verify the server works standalone:

```python
import subprocess, json, time, os

proc = subprocess.Popen(
    ['./venv/bin/python', 'server.py'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

# Send initialize
init = json.dumps({
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {'protocolVersion': '2024-11-05',
               'capabilities': {},
               'clientInfo': {'name': 'test', 'version': '1.0'}}
})
proc.stdin.write((init + '\n').encode())
proc.stdin.flush()
time.sleep(1)

# Send tools/list
tools_req = json.dumps({
    'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}
})
proc.stdin.write((tools_req + '\n').encode())
proc.stdin.flush()
time.sleep(2)

proc.stdin.close()
# Parse and verify responses
```

This catches issues before they become mysterious "MCP server failed to start" errors in Cursor.

---

## Tool Design Principles

**1. Descriptive tool names.** The agent picks tools based on name and description. `search_drive` is better than `query` or `find`.

**2. Docstrings are your API docs.** The agent reads the docstring to understand when and how to use the tool. Be specific about what the tool returns and what the parameters do.

**3. Return full context.** Don't return just an ID. Return the name, URL, dates, and any metadata the agent might need to answer the user's question without making another call.

**4. Handle pagination.** For any endpoint that can return many results, accept `page_size` and `page_token`. This prevents accidentally dumping thousands of results into the context window.

**5. Keep tools stateless.** Each tool call should work independently. Don't rely on previous calls setting up state. The agent might call tools in any order.

**6. Use shared helpers.** When multiple tools call the same API with different filters (like Drive's `files.list` with different queries), extract the shared logic into a helper function.

---

## Common Pitfalls

**Browser auth fails in Cursor's terminal.** Python's `webbrowser` module uses `osascript` on macOS, which doesn't work in Cursor's embedded terminal. Always use `subprocess.run(["open", url])` in your auth script.

**Hardcoded scopes in existing servers.** Many community MCP servers hardcode their OAuth scopes. If you need different scopes, you can't just configure them. This is the main reason to build a custom server.

**Credentials in git.** Easy to accidentally commit. Use a directory outside your repo (`~/.app-name/`) and add the credential paths to `.gitignore` as a safety net.

**Port conflicts during auth.** If your auth callback port is in use, the auth flow fails silently (the browser shows "connection refused"). Use a specific, unusual port or `port=0` to auto-assign.

**Token scope mismatch.** If you add new tools that need a new scope, you must delete the old token and re-authorize. The existing token won't automatically gain new scopes.

**Piping issues with stdio.** When testing manually via pipe (`echo '...' | python server.py`), the server may not get all messages before stdin closes. Use a subprocess with `proc.stdin.write()` and `proc.stdin.flush()` for reliable testing.

---

## Framework Options

| Framework | Language | Strengths |
|-----------|----------|-----------|
| **FastMCP** | Python | Minimal boilerplate, auto-generates schemas from type hints, great for API wrappers |
| **MCP Python SDK** | Python | Official SDK, more control, lower level |
| **MCP TypeScript SDK** | Node.js | Official SDK, good if your API has a JS client library |
| **Custom (raw JSON-RPC)** | Any | Full control, no dependencies, more work |

For most API-wrapping use cases, FastMCP is the fastest path. It turns a decorated Python function into a fully compliant MCP tool with schema, validation, and error handling.

---

**Version:** 1.0
**Last Updated:** February 2026
