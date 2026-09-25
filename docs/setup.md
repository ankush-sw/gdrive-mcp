# Google Drive MCP Setup

Human checklist. Agents: read [skills/setup/SKILL.md](../skills/setup/SKILL.md) instead and do not stop until `list_recent_files` passes.

**Last updated:** September 12, 2026

## Paste this into an agent

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```

## What you need

1. Python 3.11+
2. A GCP project you own, with Drive, Docs, Sheets, and Slides APIs enabled
3. A Desktop OAuth client downloaded as `gcp-oauth.keys.json`
4. One MCP host: Claude, Cursor, ChatGPT, Codex, Gemini, or any client that can run a local stdio server

OAuth is the only auth the server uses. Keys stay in `~/.gdrive-mcp/`.

## Shared install

```bash
mkdir -p ~/.gdrive-mcp/server
cp server.py auth.py requirements.txt ~/.gdrive-mcp/server/
# Save the Desktop client JSON as ~/.gdrive-mcp/gcp-oauth.keys.json
cd ~/.gdrive-mcp/server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python auth.py
```

Run `auth.py` in a normal OS terminal, not an embedded IDE one.

Smoke before you touch any host config:

```bash
cd ~/.gdrive-mcp/server
./venv/bin/python -c "import json,server; d=json.loads(server.list_recent_files(page_size=1)); print((d.get('files') or [{}])[0].get('name'))"
```

A file name should print. Then wire one host. Full snippets: [README](../README.md).

## Host config

Replace paths with your real home directory. Do not leave `YOUR_USERNAME` or `${HOME}` in a GUI field.

| Host | Where it goes | How you know it worked |
| --- | --- | --- |
| Cursor | `~/.cursor/mcp.json` | Settings → MCP lists Google Drive. One `list_recent_files`. |
| Claude Desktop | Install `gdrive-mcp.mcpb` (below). JSON fallback has no icon. | Quit and reopen. Connectors shows the Drive G mark. Ask for 2 recent files. |
| Claude Code | `claude mcp add -s user google-drive -- …` (no `-e` before the name) | `claude mcp list` shows `google-drive` connected. |
| Codex | `~/.codex/config.toml` `[mcp_servers.google_drive]` | `codex mcp list` shows the server. |

### Claude Desktop icon (`.mcpb`)

1. Shared install above must already pass the Python smoke.
2. In this repo: `npx --yes @anthropic-ai/mcpb pack`
3. Claude Desktop → Settings → Extensions → Advanced → Install Extension → pick `gdrive-mcp.mcpb`
4. Claude will warn that the extension can access everything on the computer, and that Anthropic has not verified the developer. That dialog is Claude's, not ours. You cannot turn it off in `manifest.json`. Click through if you trust this repo. Details: [Claude Desktop warning](#claude-desktop-warning).
5. Configure. Save stays grey until both paths are real:
   - Click Browse on Python. macOS: **Cmd+Shift+G**. Paste `/Users/YOU/.gdrive-mcp/server/venv/bin/python`
   - Browse on Credentials. Same Go to Folder. Paste `/Users/YOU/.gdrive-mcp`
   - That folder is hidden. Browse will not list it until Go to Folder.
   - Claude does not expand `${HOME}`. If you see that string, delete it and paste the absolute path.
6. Save. Quit Claude fully. Reopen.
7. If Connectors shows two Google Drives, remove the JSON `mcpServers` block you added earlier.

Windows: type the full path in the file-name bar of the picker. Python is `...\venv\Scripts\python.exe`. Config fallback: `%APPDATA%\Claude\claude_desktop_config.json`.

### Claude Desktop warning

Sideloading a `.mcpb` always shows:

> Installing will grant this extension access to everything on your computer. Any developer information shown has not been verified by Anthropic.

We cannot rewrite that text. Local MCP bundles have no sandbox and no `permissions` block. Claude shows the same consent for every Advanced → Install Extension file.

| What you want | What actually works |
| --- | --- |
| Avoid that install dialog | Use the JSON fallback in `claude_desktop_config.json` (no icon). Same `server.py`, no `.mcpb` installer. |
| Drop "not verified by Anthropic" | Get listed in Anthropic's desktop directory. Form: [clau.de/desktop-extention-submission](https://clau.de/desktop-extention-submission). Needs a real privacy policy, tool annotations, and review. |
| Self-sign with `mcpb sign` | Does not change the dialog. Orgs can require a signature. Signing has also broken installs. |

What we touch, and how to read the code: [TRUST.md](../TRUST.md) (also inside the `.mcpb`). Privacy: [PRIVACY.md](../PRIVACY.md).

## Expected layout

```
~/.gdrive-mcp/
  gcp-oauth.keys.json
  token.json
  server/
    server.py
    auth.py
    requirements.txt
    venv/
```

Never commit `gcp-oauth.keys.json` or `token.json`.

## Skills

```bash
npx skills add ankush-sw/gdrive-mcp -a cursor -a claude-code -a codex
```

Claude Desktop does not load `SKILL.md`. Use the MCP tools there, or run a skill from Claude Code / Cursor.

## Transcripts

Pair this server with Granola (`https://mcp.granola.ai/mcp` or the Cursor plugin) or another meeting MCP. See the README Transcripts section.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `OAuth client secrets not found` | Put `gcp-oauth.keys.json` in `~/.gdrive-mcp` |
| Server will not start | Confirm `token.json` exists and the venv has deps. Re-run `auth.py` |
| osascript errors during auth | Run `auth.py` in a normal terminal, not an embedded one |
| Scope errors after adding APIs | Delete `token.json` and re-run `auth.py` |
| Port 8087 busy | Change `PORT` in `auth.py` |
| Host sees no tools | Absolute paths. Restart the host. |
| Claude Desktop Save grey | Paths are still `${HOME}/...` or empty. Browse + Cmd+Shift+G. Paste absolute paths. |
| Browse cannot find `.gdrive-mcp` | Hidden folder. Cmd+Shift+G (macOS) and paste the full path. |
| Claude Code rejects `google-drive` | You put `-e` before the server name. Use the command in the README. |
| `invalid_grant` | Token expired. Delete `token.json`, run `auth.py` again. |
| Claude Desktop "access to everything" warning | Expected on every sideloaded `.mcpb`. See [Claude Desktop warning](#claude-desktop-warning). |

## Related

- [README.md](../README.md)
- [setup skill](../skills/setup/SKILL.md)
- [architecture.md](./architecture.md)
- [TRUST.md](../TRUST.md)
