# Privacy

This file ships inside `gdrive-mcp.mcpb`. Same text on GitHub: [PRIVACY.md](https://github.com/ankush-sw/gdrive-mcp/blob/main/PRIVACY.md).

This connector runs on your computer. The author does not host your Drive files or your OAuth token.

**Last updated:** September 12, 2026

## What is collected

Nothing is sent to the author or to this GitHub repo.

The local process stores two files in the folder you configure (default `~/.gdrive-mcp/`):

1. `gcp-oauth.keys.json`: the Desktop OAuth client you downloaded from *your* GCP project
2. `token.json`: the token Google issued after you signed in

## How it is used

`server.py` uses that token to call Google Drive, Docs, Sheets, and Slides APIs when a host (Claude, Cursor, ChatGPT, Codex, Gemini, or another MCP client) invokes a tool. Google's handling of that traffic is in [Google's privacy policy](https://policies.google.com/privacy).

## Sharing

No third party besides Google (and the AI host you already run) sees tool results. The host is whichever MCP client you run on your machine.

## Retention

Tokens stay on disk until you delete `token.json` or revoke the app at [Google Account permissions](https://myaccount.google.com/permissions). This project does not keep a copy.

## Contact

Issues: [github.com/ankush-sw/gdrive-mcp/issues](https://github.com/ankush-sw/gdrive-mcp/issues)

Full audit note: [TRUST.md](TRUST.md)
