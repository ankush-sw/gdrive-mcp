# Placeholders

Create a GCP project you own. Do not copy someone else's OAuth client files.

| key | type | means | mock now | wire later |
| --- | --- | --- | --- | --- |
| {{GCP_PROJECT}} | string | GCP project id | your-personal-project | Cloud Console project id |
| {{GCP_PROJECT_NAME}} | string | display name | Harbor Workspace | your project name |
| {{USER_EMAIL}} | string | Google account for OAuth | you@harbor.example | your Gmail or Workspace user |
| {{PYTHON}} | path | interpreter that has MCP deps | venv python | `~/.gdrive-mcp/server/venv/bin/python` |
| {{GDRIVE_MCP_SERVER}} | path | server.py on this machine | `server.py` in this repo | copy into `~/.gdrive-mcp/server/` |
| {{GDRIVE_MCP_DIR}} | path | creds dir env | `~/.gdrive-mcp` | same, or `GDRIVE_CREDS_DIR` |
