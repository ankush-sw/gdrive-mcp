"""One-time auth script. Run to generate token.json."""

import json
import os
import subprocess
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
]

CREDS_DIR = Path(
    os.environ.get("GDRIVE_MCP_DIR")
    or os.environ.get("GDRIVE_CREDS_DIR")
    or (Path.home() / ".gdrive-mcp")
)
TOKEN_PATH = CREDS_DIR / "token.json"
PORT = 8087

flow = InstalledAppFlow.from_client_secrets_file(
    str(CREDS_DIR / "gcp-oauth.keys.json"), SCOPES
)
flow.redirect_uri = f"http://localhost:{PORT}/"

auth_url, state = flow.authorization_url(
    access_type="offline", prompt="consent"
)

# Open browser via macOS open command directly
print(f"Opening browser for auth...", flush=True)
subprocess.run(["open", auth_url])
print(f"Waiting for callback on localhost:{PORT}...", flush=True)

# Minimal callback handler
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h2>Auth complete. You can close this tab.</h2></body></html>")

    def log_message(self, format, *args):
        pass

server = HTTPServer(("localhost", PORT), CallbackHandler)
server.handle_request()

if not auth_code:
    print("ERROR: No auth code received.", flush=True)
    sys.exit(1)

print("Got auth code, exchanging for token...", flush=True)
flow.fetch_token(code=auth_code)
creds = flow.credentials

TOKEN_PATH.write_text(creds.to_json())
print(f"Auth successful!", flush=True)
print(f"Scopes: {creds.scopes}", flush=True)
print(f"Token saved to: {TOKEN_PATH}", flush=True)
