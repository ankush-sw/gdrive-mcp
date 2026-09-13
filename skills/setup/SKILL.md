---
name: setup
description: Install and validate the Google Workspace MCP on Cursor, Claude Desktop, Claude Code, or Codex. Use when the user pastes the gdrive-mcp repo URL, or asks to set up, install, configure, or test this Drive plugin.
---

# Setup

Walk one person from a blank machine to a passing smoke test. Human copy lives in [docs/setup.md](../../docs/setup.md). Same steps.

Repo: `https://github.com/ankush-sw/gdrive-mcp`

## Done means

`list_recent_files` returns at least one real file name on the host they asked for. Do not say it works without that call.

## Do not

- Write `${HOME}` into a Claude Desktop file picker. Claude leaves it as literal text and Save stays grey.
- Pass `-e` before the Claude Code server name. It eats `google-drive` as an env var.
- Commit `token.json` or `gcp-oauth.keys.json`.
- Move, edit, or share Drive files during setup. Read-only smoke only.
- Skip OAuth and "wire the JSON anyway."

## Detect the host

Ask once if they did not name it. Default to the host you are running in.

| Host | How you know |
| --- | --- |
| Cursor | This chat is Cursor |
| Claude Code | `claude` CLI or Claude Code IDE |
| Claude Desktop | They said Claude app / Connectors / Extensions |
| Codex | `codex` CLI |

`$HOME` below is their home. On this Mac that is `/Users/kush`. Expand it yourself. Never leave `${HOME}` or `YOUR_USERNAME` in a path you type into a GUI.

## Playbook

### 1. Clone if needed

If this repo is not on disk:

```bash
git clone https://github.com/ankush-sw/gdrive-mcp.git
cd gdrive-mcp
```

### 2. Python

Need 3.11+.

```bash
python3 --version
```

Stop if missing. Point them at python.org or Homebrew. Do not continue.

### 3. Shared server install

```bash
mkdir -p "$HOME/.gdrive-mcp/server"
cp server.py auth.py requirements.txt "$HOME/.gdrive-mcp/server/"
cd "$HOME/.gdrive-mcp/server"
python3 -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Windows venv python: `%USERPROFILE%\.gdrive-mcp\server\venv\Scripts\python.exe`

### 4. GCP keys (human click path)

They must do this in a browser. You cannot finish it for them.

1. Cloud Console → a GCP project they own
2. Enable Drive, Docs, Sheets, Slides APIs
3. APIs & Services → Credentials → Create credentials → OAuth client ID → Desktop app
4. Download JSON
5. Save it as `$HOME/.gdrive-mcp/gcp-oauth.keys.json` (that exact name)

Wait until `test -f "$HOME/.gdrive-mcp/gcp-oauth.keys.json"` is true.

### 5. Sign in

Run in a normal OS terminal, not an embedded IDE terminal (osascript / browser callback fails there):

```bash
cd "$HOME/.gdrive-mcp/server"
source venv/bin/activate
python auth.py
```

They sign in. `token.json` lands in `$HOME/.gdrive-mcp/`. Port 8087 must be free.

### 6. API smoke (before any host config)

```bash
"$HOME/.gdrive-mcp/server/venv/bin/python" -c "import json,sys; sys.path.insert(0,'.'); import server; d=json.loads(server.list_recent_files(page_size=1)); print((d.get('files') or [{}])[0].get('name','NO_FILES'))"
```

Run that from `$HOME/.gdrive-mcp/server`. Pass: a file name prints. Fail: show the error, do not wire the host yet.

`invalid_grant`: delete `token.json`, re-run `auth.py`.

### 7. Wire the host they asked for

#### Cursor

Append to `~/.cursor/mcp.json` (user) or `.cursor/mcp.json` (project). Use absolute paths. Merge into existing `mcpServers`. Do not overwrite the whole file.

```json
"Google Drive": {
  "command": "/ABS/HOME/.gdrive-mcp/server/venv/bin/python",
  "args": ["/ABS/HOME/.gdrive-mcp/server/server.py"],
  "env": {
    "GDRIVE_MCP_DIR": "/ABS/HOME/.gdrive-mcp",
    "GDRIVE_CREDS_DIR": "/ABS/HOME/.gdrive-mcp"
  }
}
```

Tell them to reload MCP / restart Cursor.

#### Claude Code

```bash
claude mcp add -s user google-drive -- \
  "$HOME/.gdrive-mcp/server/venv/bin/python" \
  "$HOME/.gdrive-mcp/server/server.py"
```

No `-e` before `google-drive`. Confirm with `claude mcp get google-drive` (Status Connected).

#### Codex

Write or merge `~/.codex/config.toml`:

```toml
[mcp_servers.google_drive]
command = "/ABS/HOME/.gdrive-mcp/server/venv/bin/python"
args = ["/ABS/HOME/.gdrive-mcp/server/server.py"]
startup_timeout_sec = 20
```

Or `codex mcp add google-drive -- "$HOME/.gdrive-mcp/server/venv/bin/python" "$HOME/.gdrive-mcp/server/server.py"`. Confirm with `codex mcp list`.

#### Claude Desktop (icon)

Shared install must already pass step 6.

```bash
cd /path/to/gdrive-mcp
npx --yes @anthropic-ai/mcpb pack
```

Then: Settings → Extensions → Advanced → Install Extension → pick `gdrive-mcp.mcpb`. Or drop the file on the Claude window.

Claude will warn that the extension can access everything on the computer and that Anthropic has not verified the developer. That is Claude's sideload consent, not a bug in this repo. Do not try to hide it in `manifest.json`. Point them at [TRUST.md](../../TRUST.md) (also packed in the `.mcpb`). JSON fallback skips that install dialog (no icon). Directory listing is the only path that can drop the "not verified" line.

Configure dialog (Save stays grey until both paths are real files):

1. Click Browse on Python.
2. In the picker: macOS **Cmd+Shift+G**, Windows file-name bar, paste `/ABS/HOME/.gdrive-mcp/server/venv/bin/python` (Windows: `...\venv\Scripts\python.exe`).
3. Browse on Credentials. Same Go-to-folder. Paste `/ABS/HOME/.gdrive-mcp`.
4. `.gdrive-mcp` is hidden. Browse will not list it until Go to Folder.
5. Save. Quit Claude fully. Reopen.

If they already have a JSON `mcpServers["Google Drive"]` entry, remove it so Connectors is not duplicated.

JSON fallback (no icon): same block as Cursor, in `~/Library/Application Support/Claude/claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`). Append. Do not wipe other keys.

### 8. Host smoke

On the live host, call `list_recent_files` with `page_size` 2. Expect two names. Do not create or move files.

Cursor / Claude Code: you can invoke the tool. Claude Desktop: ask them to type "list my 2 most recent Google Drive files" and paste what came back.

Fail: see Troubleshooting in [docs/setup.md](../../docs/setup.md).

### 9. Skills (optional)

```bash
npx skills add ankush-sw/gdrive-mcp -a cursor -a claude-code -a codex
```

Claude Desktop does not load `SKILL.md`. Fine.

### 10. Tell them what works

One short list: host, smoke file names (or count), where keys live (`~/.gdrive-mcp`). Offer exec-feedback if they have Granola or another transcript MCP.

## Prompt they can paste

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```
