# Google Workspace MCP for Cursor

29 tools for Drive, Docs, Sheets, and Slides. Native Google URLs on every result. OAuth keys you create stay in `~/.gdrive-mcp/`, not in git.

Google's Drive MCP can search, read, and create a file. This one edits a Doc, Sheet, or deck that already exists, comments, shares, and hands back the real `docs.google.com` link.

**Last updated:** September 12, 2026

## Why this exists

The job after a review is not a recap of your pitch. It is what the VP said back.

1. This server reads the Doc, Sheet, or Slides you walked (`get_doc_content`, `read_sheet`, `get_presentation`, `get_slide_content`).
2. Granola or a Zoom transcript is the room.
3. Treat the artifact as your script. Drop anything that is you dictating those slides, cells, or bullets.
4. What remains is other people in the room: reactions, decisions, quotes.

```
artifact (Drive MCP) ──┐
                       ├── drop presenter dictation ──► exec quotes
transcript (Granola) ──┘
```

The default Drive MCP cannot run that. It does not treat Slides as structured text next to the transcript.

Same Desktop OAuth client Google's own Drive MCP asks for. You own the keys.

## What else you can ask

- Find the Q4 doc and replace Q3 with Q4 in place
- Append a row to the tracking sheet
- Create a deck, then swap the placeholder on slide 2
- Share a doc as commenter and reply on the thread
- Move an export into the right folder and hand back the URL

## vs the defaults

| Surface | What it can do |
| --- | --- |
| Official local plugin (`@modelcontextprotocol/server-gdrive`) | Search and read. `drive.readonly`. No write, no comments, no share, no Slides API. |
| Google remote Drive MCP (8 tools) | Search, read, create, copy, download, metadata, permissions list. Cannot edit a Doc, Sheet, or Slide in place. |
| This server (29 tools) | In-place Doc / Sheet / Slide edits, comments and replies, share and revoke, move, upload, export, folder browse, shared and starred, native URLs. |

## Setup

You need Cursor, Python 3.11+, and a GCP project you own with Drive, Docs, Sheets, and Slides APIs enabled.

1. Create a Desktop OAuth client in Cloud Console and download it as `gcp-oauth.keys.json`.
2. Put that file at `~/.gdrive-mcp/gcp-oauth.keys.json`.
3. Copy `server.py`, `auth.py`, and `requirements.txt` into `~/.gdrive-mcp/server/`.
4. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
5. Run `python auth.py` in a normal terminal (not an embedded one). Sign in. It writes `~/.gdrive-mcp/token.json`.

Full click path: [docs/cursor-setup-guide.md](docs/cursor-setup-guide.md).

Cursor `~/.cursor/mcp.json` (replace `YOUR_USERNAME`):

```json
"Google Drive": {
  "command": "/Users/YOUR_USERNAME/.gdrive-mcp/server/venv/bin/python",
  "args": [
    "/Users/YOUR_USERNAME/.gdrive-mcp/server/server.py"
  ],
  "env": {
    "GDRIVE_MCP_DIR": "/Users/YOUR_USERNAME/.gdrive-mcp",
    "GDRIVE_CREDS_DIR": "/Users/YOUR_USERNAME/.gdrive-mcp"
  }
}
```

Restart Cursor. Smoke: one `list_recent_files` call.

Never commit `gcp-oauth.keys.json` or `token.json`.

## Tool inventory

29 tools. Matches `server.py`.

**Drive (18):** `search_drive`, `list_recent_files`, `list_folder_contents`, `list_shared_with_me`, `list_starred_files`, `get_file_metadata`, `get_file_content`, `get_file_comments`, `upload_file`, `copy_file`, `move_file`, `export_file`, `create_folder`, `create_comment`, `reply_to_comment`, `share_file`, `list_permissions`, `remove_permission`

**Docs (3):** `get_doc_content`, `update_google_doc`, `create_google_doc`

**Sheets (4):** `read_sheet`, `update_sheet_cells`, `append_sheet_rows`, `create_spreadsheet`

**Slides (4):** `get_presentation`, `get_slide_content`, `update_presentation`, `create_presentation`

## Auth

Two files, both in `~/.gdrive-mcp/`:

1. `gcp-oauth.keys.json`: Desktop OAuth client from a GCP project you own
2. `token.json`: written by `auth.py` after you sign in

No API key. No `.env`. No service account. Scopes are full Drive plus Docs, Sheets, and Slides write (needed for move, share, upload, and in-place edits). Revoke from your Google Account when you are done.

## Docs

- [Setup](docs/cursor-setup-guide.md)
- [Architecture](docs/architecture.md)
- [Building an MCP from a public API](docs/mcp-development-guide.md)

## License

MIT. Copyright (c) 2026 Ankush Rustagi
