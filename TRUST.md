# What this plugin is, and how to check it

This file ships inside `gdrive-mcp.mcpb` (unzip the bundle, or open the installed extension folder). The same text is on GitHub so you can compare: [TRUST.md](https://github.com/ankush-sw/gdrive-mcp/blob/main/TRUST.md).

**Last updated:** September 12, 2026

- **Source:** [github.com/ankush-sw/gdrive-mcp](https://github.com/ankush-sw/gdrive-mcp)
- **Privacy (in this bundle and on GitHub):** [PRIVACY.md](PRIVACY.md)
- **Anthropic directory:** not listed. This page will say so here when that changes.

## What this is

A local Python MCP server. Cursor, Claude Desktop, Claude Code, or Codex starts `server.py` on your machine. The process talks to Google Drive, Docs, Sheets, and Slides with a Desktop OAuth token *you* created. 29 tools. Native `docs.google.com` links on results.

It is not Google's official Drive connector. It is not an Anthropic-reviewed directory extension. It is this public repo, packed as `gdrive-mcp.mcpb` so Claude Desktop can show an icon.

## Why Claude says it can access everything

Claude Desktop shows this on every sideloaded `.mcpb`:

> Installing will grant this extension access to everything on your computer. Any developer information shown has not been verified by Anthropic.

That text is Claude's. We cannot change it in `manifest.json`.

Local MCP bundles have no sandbox. The Python process runs as you. Claude warns because any local extension *could* read your disk. "Not verified by Anthropic" means you installed from a file (Advanced → Install Extension), not from Settings → Extensions → Browse.

Wiring the same `server.py` through `claude_desktop_config.json` is the same process and the same Google scopes. You just never see that install dialog. No icon on that path.

## What we actually access

**On disk (this machine)**

- Reads `gcp-oauth.keys.json` and `token.json` in the folder you pick (`~/.gdrive-mcp` by default).
- Does not index Desktop, Documents, or the rest of your home folder.
- Does not upload this repo or your files to the author.

**On the network**

- Calls Google APIs only (`googleapis.com`) with your token.
- No analytics, crash reporter, or other host in `server.py` / `auth.py`.

**On Google (the scopes in `SCOPES`)**

| Scope | What Google lets the token do |
| --- | --- |
| `https://www.googleapis.com/auth/drive` | Search, read, upload, copy, move, export, folders, comments, share |
| `https://www.googleapis.com/auth/documents` | Read and write Docs |
| `https://www.googleapis.com/auth/spreadsheets` | Read and write Sheets |
| `https://www.googleapis.com/auth/presentations` | Read and write Slides |

Tools run when you (or the host) ask. The server does not scan Drive in the background.

You own the GCP project and the OAuth client. Revoke the app from your [Google Account](https://myaccount.google.com/permissions).

## What is not claimed

| Check | Status |
| --- | --- |
| Anthropic desktop directory review | Not submitted. No "verified by Anthropic" badge. |
| Third-party pentest / SOC 2 | None. |
| Code-signed `.mcpb` from Anthropic | None. `mcpb sign` does not change the warning. |
| Sandbox or OS permission prompt | None. Same as every local MCP. |

If someone pastes a badge we do not have, treat the listing as wrong.

## Audit it yourself

The program is two files. They are in this bundle next to this page.

1. `server.py`: tools and `SCOPES` (around line 43). On GitHub: [server.py](https://github.com/ankush-sw/gdrive-mcp/blob/main/server.py)
2. `auth.py`: browser sign-in. Same `SCOPES`. On GitHub: [auth.py](https://github.com/ankush-sw/gdrive-mcp/blob/main/auth.py)
3. `requirements.txt`: `fastmcp` plus Google client libs.

From a clone or an unpacked `.mcpb`:

```bash
# Scopes in both files should match
grep -n 'googleapis.com/auth' server.py auth.py

# No extra hosts in the server
grep -nE 'https?://' server.py auth.py
```

Network lines should be Google API URLs and `docs.google.com` / `drive.google.com` links in responses. If you see another host, stop.

Pack only from this repo: `npx --yes @anthropic-ai/mcpb pack`. Do not install a `.mcpb` from a random Drive link.

Compare this file to GitHub. If they differ, do not install that bundle.

## Related

- [docs/setup.md](docs/setup.md) (GitHub / clone; not inside the `.mcpb`)
- [docs/architecture.md](docs/architecture.md)
- [PRIVACY.md](PRIVACY.md)
