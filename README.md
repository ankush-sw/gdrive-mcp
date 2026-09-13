# Google Workspace MCP

29 tools for Drive, Docs, Sheets, and Slides. Native Google URLs on every result. OAuth keys you create stay in `~/.gdrive-mcp/`, not in git.

Works on Cursor, Claude Desktop, Claude Code, and Codex. Same Python server. Each host gets its own config snippet.

**Paste this into any agent** (Cursor, Claude Code, Codex). The blank URL is [SETUP.md](SETUP.md) (`https://github.com/ankush-sw/gdrive-mcp/blob/main/SETUP.md`). The repo URL works too.

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```

The agent clones, walks OAuth, wires this host, and does not stop until a real Drive file name comes back. Human checklist: [docs/setup.md](docs/setup.md).

Google's Drive MCP can search, read, and create a file. This one edits a Doc, Sheet, or deck that already exists, comments, shares, and hands back the real `docs.google.com` link.

**Last updated:** September 12, 2026

## Why this exists

The job after a review is not a recap of your pitch. It is what the VP said back.

1. This server reads the Doc, Sheet, or Slides you walked (`get_doc_content`, `read_sheet`, `get_presentation`, `get_slide_content`).
2. Your meeting tool is the room. Use Granola if that is your stack, or Zoom / Fireflies / Otter / a pasted transcript if it is not. See [Transcripts](#transcripts).
3. Treat the artifact as your script. Drop anything that is you dictating those slides, cells, or bullets.
4. What remains is other people in the room: reactions, decisions, quotes.

```
artifact (this MCP) ──┐
                      ├── drop presenter dictation ──► exec quotes
transcript (your MCP) ┘
```

The default Drive MCP cannot run that. It does not treat Slides as structured text next to the transcript.

Same Desktop OAuth client Google's own Drive MCP asks for. You own the keys.

## Skills

Four Agent Skills ([spec](https://agentskills.io/specification)) ship in `skills/`. They are folders with `SKILL.md`, not Cursor plugins.

| Skill | Job |
| --- | --- |
| [setup](skills/setup/SKILL.md) | Install, wire a host, smoke-test. Start here. |
| [exec-feedback](skills/exec-feedback/SKILL.md) | Artifact + transcript, keep only what others said |
| [slides-outline](skills/slides-outline/SKILL.md) | Port Cursor / Claude Code work into a Slides outline, then build |
| [drive-cleanup](skills/drive-cleanup/SKILL.md) | Index Drive, propose folders and names, move after you approve |

Install into Cursor, Claude Code, and Codex (Claude Desktop does not load project `SKILL.md`):

```bash
npx skills add ankush-sw/gdrive-mcp -a cursor -a claude-code -a codex
```

Or copy `skills/<name>` into that host's skills dir (`.cursor/skills/`, `.claude/skills/`, `.agents/skills/`).

## Transcripts

This repo does not include a meeting MCP. Pair it with the vendor you already pay for.

| Vendor | Typical hook |
| --- | --- |
| Granola | Cursor plugin, or HTTP MCP `https://mcp.granola.ai/mcp` on Claude Code / Desktop / Codex. `query_granola_meetings` for an open question. `list_meetings` / `get_meetings` / `get_meeting_transcript` when you have a `notes.granola.ai` URL. |
| Zoom, Fireflies, Otter | That product's MCP or an export you paste |
| None | Paste the transcript. The Drive tools still run. |

Check that the transcript MCP is connected before you run exec-feedback. If it is not, say so and ask for a file.

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

## Setup (once)

You need Python 3.11+ and a GCP project you own with Drive, Docs, Sheets, and Slides APIs enabled.

1. Create a Desktop OAuth client in Cloud Console and download it as `gcp-oauth.keys.json`.
2. Put that file at `~/.gdrive-mcp/gcp-oauth.keys.json`.
3. Copy `server.py`, `auth.py`, and `requirements.txt` into `~/.gdrive-mcp/server/`.
4. `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
5. Run `python auth.py` in a normal terminal (not an embedded one). Sign in. It writes `~/.gdrive-mcp/token.json`.

Full click path: [docs/setup.md](docs/setup.md).

Never commit `gcp-oauth.keys.json` or `token.json`.

Then add **one** of the host blocks below. Replace `YOUR_USERNAME`. Smoke on every host: one `list_recent_files` call.

### Cursor

`~/.cursor/mcp.json` (user) or `.cursor/mcp.json` (project):

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

Restart Cursor. Settings → MCP should list the server.

### Claude Desktop

Use the `.mcpb` bundle so Connectors shows the official Google Drive mark. Finish the shared setup first (venv + `auth.py`).

```bash
npx --yes @anthropic-ai/mcpb pack
```

Then in Claude Desktop: Settings → Extensions → Advanced → Install Extension, and pick `gdrive-mcp.mcpb`. Or drop the file on the Claude window.

Claude will warn that the extension can access everything on the computer and that Anthropic has not verified the developer. Expected for every sideloaded `.mcpb`. We cannot change that text. The bundle includes [TRUST.md](TRUST.md) and [PRIVACY.md](PRIVACY.md) (same files on GitHub). To avoid that install dialog, use the JSON fallback below (same server, no icon).

Claude does not expand `${HOME}` in that form. Click Browse on each field. In the file picker press Cmd+Shift+G (macOS) and paste:

1. Python: `/Users/YOUR_USERNAME/.gdrive-mcp/server/venv/bin/python`
2. Credentials folder: `/Users/YOUR_USERNAME/.gdrive-mcp`

The folder is hidden. Browse will not list it until you Go to Folder.

Quit Claude and reopen. Connectors should list Google Drive with the Drive G mark.

`icon.png` is Google's 2026 Drive product mark ([brand page](https://developers.google.com/workspace/drive/api/guides/branding)). Resized to 512×512 only. Google Drive is a trademark of Google Inc.

JSON fallback (no icon): `~/Library/Application Support/Claude/claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`)

```json
{
  "mcpServers": {
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
  }
}
```

If you install the `.mcpb`, remove this JSON block so you do not get two connectors.

### Claude Code

```bash
claude mcp add -s user google-drive -- \
  /Users/YOUR_USERNAME/.gdrive-mcp/server/venv/bin/python \
  /Users/YOUR_USERNAME/.gdrive-mcp/server/server.py
```

The server already reads `~/.gdrive-mcp`. Do not pass `-e` before the server name. Claude Code treats extra words after `-e` as env vars and will reject `google-drive`.

`claude mcp list` should show `google-drive` connected. Project file alternative: root `.mcp.json` with the same `command` / `args` / `env` object as Cursor.

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.google_drive]
command = "/Users/YOUR_USERNAME/.gdrive-mcp/server/venv/bin/python"
args = ["/Users/YOUR_USERNAME/.gdrive-mcp/server/server.py"]
startup_timeout_sec = 20

[mcp_servers.google_drive.env]
GDRIVE_MCP_DIR = "/Users/YOUR_USERNAME/.gdrive-mcp"
GDRIVE_CREDS_DIR = "/Users/YOUR_USERNAME/.gdrive-mcp"
```

Or: `codex mcp add google-drive -- /Users/YOUR_USERNAME/.gdrive-mcp/server/venv/bin/python /Users/YOUR_USERNAME/.gdrive-mcp/server/server.py` and then add the two env keys. `codex mcp list` to confirm.

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

- [What this accesses (trust)](TRUST.md)
- [Privacy](PRIVACY.md)
- [Setup (human)](docs/setup.md)
- [Setup (agent skill)](skills/setup/SKILL.md)
- [Architecture](docs/architecture.md)
- [Building an MCP from a public API](docs/mcp-development-guide.md)

## License

MIT. Copyright (c) 2026 Ankush Rustagi
