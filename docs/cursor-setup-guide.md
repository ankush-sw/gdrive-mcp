# Google Drive MCP Setup (Cursor)

This page is the Cursor-only copy. All four hosts: [setup.md](./setup.md). Agent playbook: [../skills/setup/SKILL.md](../skills/setup/SKILL.md).

Paste into this chat if you want the agent to do it:

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```

Create your own GCP project and Desktop OAuth client. The server exposes 29 tools.

**Last updated:** September 12, 2026

## What you need

1. Cursor with MCP support
2. Python 3.11+
3. A GCP project you own, with Drive, Docs, Sheets, and Slides APIs enabled
4. A Desktop OAuth client downloaded as `gcp-oauth.keys.json`

OAuth is the only auth the server uses. API keys are optional for other Google scripts.

`auth.py` and `server.py` both honor `GDRIVE_MCP_DIR` or `GDRIVE_CREDS_DIR`. Default is `~/.gdrive-mcp`.

## Quick start

```bash
mkdir -p ~/.gdrive-mcp/server
cp server.py auth.py requirements.txt ~/.gdrive-mcp/server/
# Place your Desktop client JSON at ~/.gdrive-mcp/gcp-oauth.keys.json
cd ~/.gdrive-mcp/server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python auth.py
```

Add this block to `~/.cursor/mcp.json` (replace `YOUR_USERNAME`):

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

Restart Cursor. Settings → MCP should list the server. Smoke: one `list_recent_files` call as the Google account you signed in with.

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

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `OAuth client secrets not found` | Put `gcp-oauth.keys.json` in the dir named by `GDRIVE_MCP_DIR` |
| Server will not start | Confirm `token.json` exists and the venv has deps. Re-run `auth.py` |
| osascript errors during auth | Run `auth.py` in a normal terminal, not an embedded one |
| Scope errors after adding APIs | Delete `token.json` and re-run `auth.py` |
| Port 8087 busy | Change `PORT` in `auth.py` |

## Related

- [README.md](../README.md) (29-tool inventory and the exec-feedback workflow)
- [architecture.md](./architecture.md)
- [PLACEHOLDERS.md](../PLACEHOLDERS.md)
