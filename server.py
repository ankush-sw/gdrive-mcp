"""
Google Workspace MCP Server

A FastMCP server providing full read/write access to Google Drive, Docs,
Sheets, and Slides. Local stdio MCP. Any host that can spawn a stdio server.

Tools:
  Drive:   search_drive, list_recent_files, list_folder_contents,
           list_shared_with_me, list_starred_files, get_file_metadata,
           get_file_content, get_file_comments,
           upload_file, copy_file, move_file, export_file, create_folder,
           create_comment, reply_to_comment,
           share_file, list_permissions, remove_permission
  Docs:    get_doc_content, update_google_doc, create_google_doc
  Sheets:  read_sheet, update_sheet_cells, append_sheet_rows,
           create_spreadsheet
  Slides:  get_presentation, get_slide_content, update_presentation,
           create_presentation
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import mimetypes

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

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
CLIENT_SECRETS = CREDS_DIR / "gcp-oauth.keys.json"
TOKEN_PATH = CREDS_DIR / "token.json"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_drive_service = None
_docs_service = None
_sheets_service = None
_slides_service = None


def _get_credentials() -> Credentials:
    """Load or create OAuth credentials, refreshing if expired."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS.exists():
                raise FileNotFoundError(
                    f"OAuth client secrets not found at {CLIENT_SECRETS}. "
                    "Download from Google Cloud Console and place there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return creds


def _drive():
    global _drive_service
    if _drive_service is None:
        _drive_service = build("drive", "v3", credentials=_get_credentials())
    return _drive_service


def _docs():
    global _docs_service
    if _docs_service is None:
        _docs_service = build("docs", "v1", credentials=_get_credentials())
    return _docs_service


def _sheets():
    global _sheets_service
    if _sheets_service is None:
        _sheets_service = build("sheets", "v4", credentials=_get_credentials())
    return _sheets_service


def _slides():
    global _slides_service
    if _slides_service is None:
        _slides_service = build("slides", "v1", credentials=_get_credentials())
    return _slides_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DRIVE_FILE_FIELDS = (
    "id, name, mimeType, webViewLink, createdTime, modifiedTime, size, "
    "owners, shared, starred, parents"
)

MIME_URL_MAP = {
    "application/vnd.google-apps.document": "https://docs.google.com/document/d/{id}/edit",
    "application/vnd.google-apps.spreadsheet": "https://docs.google.com/spreadsheets/d/{id}/edit",
    "application/vnd.google-apps.presentation": "https://docs.google.com/presentation/d/{id}/edit",
    "application/vnd.google-apps.form": "https://docs.google.com/forms/d/{id}/edit",
}


def _format_file(f: dict) -> dict:
    """Normalize a Drive file resource into a clean dict with a URL."""
    url = f.get("webViewLink") or MIME_URL_MAP.get(
        f.get("mimeType", ""), "https://drive.google.com/file/d/{id}/view"
    ).format(id=f["id"])

    owners = f.get("owners", [])
    owner_name = owners[0].get("displayName", "") if owners else ""

    return {
        "id": f["id"],
        "name": f.get("name", ""),
        "mimeType": f.get("mimeType", ""),
        "url": url,
        "createdTime": f.get("createdTime", ""),
        "modifiedTime": f.get("modifiedTime", ""),
        "size": f.get("size", ""),
        "owner": owner_name,
        "shared": f.get("shared", False),
        "starred": f.get("starred", False),
    }


def _list_files(q: str | None = None, page_size: int = 20, page_token: str | None = None, order_by: str = "modifiedTime desc") -> dict:
    """Shared helper for Drive file listing queries."""
    params: dict[str, Any] = {
        "pageSize": min(page_size, 100),
        "fields": f"nextPageToken, files({DRIVE_FILE_FIELDS})",
        "orderBy": order_by,
    }
    if q:
        params["q"] = q
    if page_token:
        params["pageToken"] = page_token

    result = _drive().files().list(**params).execute()
    files = [_format_file(f) for f in result.get("files", [])]

    out: dict[str, Any] = {"files": files, "count": len(files)}
    if result.get("nextPageToken"):
        out["nextPageToken"] = result["nextPageToken"]
    return out


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(name="Google Workspace MCP")


# ---- Drive: Search & Browse -----------------------------------------------

@mcp.tool()
def search_drive(query: str, page_size: int = 20, page_token: str | None = None) -> str:
    """Search for files in Google Drive by name or content.

    Returns file name, MIME type, URL, dates, owner, and metadata for each match.

    Args:
        query: Search text (matches file names and contents).
        page_size: Results per page, max 100.
        page_token: Token for fetching the next page of results.
    """
    q = f"fullText contains '{query}' and trashed = false"
    return json.dumps(_list_files(q=q, page_size=page_size, page_token=page_token), indent=2)


@mcp.tool()
def list_recent_files(page_size: int = 20, page_token: str | None = None) -> str:
    """List recently modified files in Google Drive, newest first.

    Args:
        page_size: Number of files to return, max 100.
        page_token: Token for fetching the next page.
    """
    return json.dumps(
        _list_files(q="trashed = false", page_size=page_size, page_token=page_token, order_by="modifiedTime desc"),
        indent=2,
    )


@mcp.tool()
def list_folder_contents(folder_id: str, page_size: int = 50, page_token: str | None = None) -> str:
    """List files inside a specific Google Drive folder.

    Args:
        folder_id: The ID of the folder to browse.
        page_size: Results per page, max 100.
        page_token: Token for the next page.
    """
    q = f"'{folder_id}' in parents and trashed = false"
    return json.dumps(_list_files(q=q, page_size=page_size, page_token=page_token), indent=2)


@mcp.tool()
def list_shared_with_me(page_size: int = 20, page_token: str | None = None) -> str:
    """List files that others have shared with you.

    Args:
        page_size: Results per page, max 100.
        page_token: Token for the next page.
    """
    q = "sharedWithMe = true and trashed = false"
    return json.dumps(_list_files(q=q, page_size=page_size, page_token=page_token), indent=2)


@mcp.tool()
def list_starred_files(page_size: int = 20, page_token: str | None = None) -> str:
    """List your starred/important files in Google Drive.

    Args:
        page_size: Results per page, max 100.
        page_token: Token for the next page.
    """
    q = "starred = true and trashed = false"
    return json.dumps(_list_files(q=q, page_size=page_size, page_token=page_token), indent=2)


# ---- Drive: File Details ---------------------------------------------------

@mcp.tool()
def get_file_metadata(file_id: str) -> str:
    """Get detailed metadata for a file including URL, owner, dates, and size.

    Args:
        file_id: The Google Drive file ID.
    """
    f = _drive().files().get(
        fileId=file_id,
        fields=DRIVE_FILE_FIELDS,
    ).execute()
    return json.dumps(_format_file(f), indent=2)


@mcp.tool()
def get_file_content(file_id: str) -> str:
    """Read the text content of a file from Google Drive.

    Google Workspace files are auto-exported: Docs as Markdown,
    Sheets as CSV, Slides as plain text. Other files returned as UTF-8 text.

    Args:
        file_id: The Google Drive file ID.
    """
    meta = _drive().files().get(fileId=file_id, fields="mimeType, name").execute()
    mime = meta.get("mimeType", "")

    export_map = {
        "application/vnd.google-apps.document": "text/markdown",
        "application/vnd.google-apps.spreadsheet": "text/csv",
        "application/vnd.google-apps.presentation": "text/plain",
        "application/vnd.google-apps.drawing": "image/png",
    }

    if mime in export_map:
        content = _drive().files().export(fileId=file_id, mimeType=export_map[mime]).execute()
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)

    content = _drive().files().get_media(fileId=file_id).execute()
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return str(content)


@mcp.tool()
def get_file_comments(file_id: str, page_size: int = 20) -> str:
    """Read comments and discussions on a Google Drive file.

    Args:
        file_id: The Google Drive file ID.
        page_size: Max comments to return.
    """
    result = _drive().comments().list(
        fileId=file_id,
        pageSize=min(page_size, 100),
        fields="comments(id, content, author(displayName), createdTime, resolved, replies(content, author(displayName), createdTime))",
    ).execute()

    comments = result.get("comments", [])
    if not comments:
        return json.dumps({"comments": [], "message": "No comments found."}, indent=2)

    formatted = []
    for c in comments:
        entry = {
            "id": c["id"],
            "author": c.get("author", {}).get("displayName", ""),
            "content": c.get("content", ""),
            "createdTime": c.get("createdTime", ""),
            "resolved": c.get("resolved", False),
            "replies": [
                {
                    "author": r.get("author", {}).get("displayName", ""),
                    "content": r.get("content", ""),
                    "createdTime": r.get("createdTime", ""),
                }
                for r in c.get("replies", [])
            ],
        }
        formatted.append(entry)

    return json.dumps({"comments": formatted, "count": len(formatted)}, indent=2)


# ---- Drive: File Operations ------------------------------------------------

@mcp.tool()
def upload_file(local_path: str, parent_folder_id: str = "", name: str = "") -> str:
    """Upload a local file to Google Drive.

    MIME type is detected automatically from the file extension.

    Args:
        local_path: Absolute path to the local file to upload.
        parent_folder_id: Optional Drive folder ID to upload into. Defaults to root.
        name: Optional filename in Drive. Defaults to the local filename.
    """
    path = Path(local_path).expanduser().resolve()
    if not path.exists():
        return json.dumps({"error": f"File not found: {local_path}"})

    file_name = name or path.name
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"

    file_metadata: dict[str, Any] = {"name": file_name}
    if parent_folder_id:
        file_metadata["parents"] = [parent_folder_id]

    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
    result = _drive().files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, mimeType, webViewLink",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "name": result.get("name", file_name),
        "mimeType": result.get("mimeType", mime_type),
        "url": result.get("webViewLink", f"https://drive.google.com/file/d/{result['id']}/view"),
        "message": "File uploaded successfully.",
    }, indent=2)


@mcp.tool()
def copy_file(file_id: str, new_name: str = "", parent_folder_id: str = "") -> str:
    """Create a copy of an existing file in Google Drive.

    Useful for duplicating templates (PRDs, weekly status, etc.).

    Args:
        file_id: The Drive file ID to copy.
        new_name: Name for the copy. Defaults to "Copy of <original>".
        parent_folder_id: Optional folder ID to place the copy in.
    """
    body: dict[str, Any] = {}
    if new_name:
        body["name"] = new_name
    if parent_folder_id:
        body["parents"] = [parent_folder_id]

    result = _drive().files().copy(
        fileId=file_id,
        body=body,
        fields="id, name, mimeType, webViewLink",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "name": result.get("name", ""),
        "mimeType": result.get("mimeType", ""),
        "url": result.get("webViewLink", f"https://drive.google.com/file/d/{result['id']}/view"),
        "message": "File copied successfully.",
    }, indent=2)


@mcp.tool()
def move_file(file_id: str, new_parent_id: str, new_name: str = "") -> str:
    """Move a file to a different folder in Google Drive, optionally renaming it.

    Args:
        file_id: The Drive file ID to move.
        new_parent_id: The destination folder ID.
        new_name: Optional new name for the file.
    """
    current = _drive().files().get(fileId=file_id, fields="parents").execute()
    old_parents = ",".join(current.get("parents", []))

    body: dict[str, Any] = {}
    if new_name:
        body["name"] = new_name

    result = _drive().files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=old_parents,
        body=body,
        fields="id, name, parents, webViewLink",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "name": result.get("name", ""),
        "parents": result.get("parents", []),
        "url": result.get("webViewLink", ""),
        "message": "File moved successfully.",
    }, indent=2)


@mcp.tool()
def export_file(file_id: str, export_mime_type: str, save_path: str = "") -> str:
    """Export a Google Workspace file to a different format.

    Common export MIME types:
      Docs  -> "application/pdf", "text/plain", "text/markdown",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      Sheets -> "application/pdf", "text/csv",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      Slides -> "application/pdf",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    Args:
        file_id: The Drive file ID to export.
        export_mime_type: Target MIME type for the export.
        save_path: Optional local path to save the exported file. If empty, returns text content.
    """
    content = _drive().files().export(fileId=file_id, mimeType=export_mime_type).execute()

    if save_path:
        out = Path(save_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            out.write_bytes(content)
        else:
            out.write_text(str(content))
        return json.dumps({
            "file_id": file_id,
            "exported_to": str(out),
            "mime_type": export_mime_type,
            "size_bytes": out.stat().st_size,
            "message": "File exported and saved successfully.",
        }, indent=2)

    if isinstance(content, bytes):
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return json.dumps({
                "error": "Binary export content cannot be displayed. Use save_path to write to disk.",
                "file_id": file_id,
                "mime_type": export_mime_type,
            }, indent=2)
    return str(content)


@mcp.tool()
def create_folder(name: str, parent_folder_id: str = "") -> str:
    """Create a new folder in Google Drive.

    Args:
        name: Name of the new folder.
        parent_folder_id: Optional parent folder ID. Defaults to root.
    """
    metadata: dict[str, Any] = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]

    result = _drive().files().create(
        body=metadata,
        fields="id, name, webViewLink",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "name": result.get("name", name),
        "url": result.get("webViewLink", f"https://drive.google.com/drive/folders/{result['id']}"),
        "message": "Folder created successfully.",
    }, indent=2)


# ---- Drive: Comments (write-back) -----------------------------------------

@mcp.tool()
def create_comment(file_id: str, content: str) -> str:
    """Add a comment to a Google Drive file.

    Args:
        file_id: The Drive file ID to comment on.
        content: The comment text.
    """
    result = _drive().comments().create(
        fileId=file_id,
        body={"content": content},
        fields="id, content, author(displayName), createdTime",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "author": result.get("author", {}).get("displayName", ""),
        "content": result.get("content", ""),
        "createdTime": result.get("createdTime", ""),
        "message": "Comment created successfully.",
    }, indent=2)


@mcp.tool()
def reply_to_comment(file_id: str, comment_id: str, content: str) -> str:
    """Reply to an existing comment on a Google Drive file.

    Args:
        file_id: The Drive file ID.
        comment_id: The comment ID to reply to (from get_file_comments).
        content: The reply text.
    """
    result = _drive().replies().create(
        fileId=file_id,
        commentId=comment_id,
        body={"content": content},
        fields="id, content, author(displayName), createdTime",
    ).execute()

    return json.dumps({
        "id": result["id"],
        "author": result.get("author", {}).get("displayName", ""),
        "content": result.get("content", ""),
        "createdTime": result.get("createdTime", ""),
        "message": "Reply created successfully.",
    }, indent=2)


# ---- Drive: Permissions ---------------------------------------------------

@mcp.tool()
def share_file(file_id: str, email: str, role: str = "reader", notify: bool = True, message: str = "") -> str:
    """Share a file or folder with a user by email.

    Args:
        file_id: The Drive file or folder ID.
        email: Email address of the person to share with.
        role: Permission level. One of: "reader", "commenter", "writer", "organizer".
        notify: Whether to send a notification email. Defaults to True.
        message: Optional message to include in the notification email.
    """
    permission_body: dict[str, Any] = {
        "type": "user",
        "role": role if role != "organizer" else "writer",
        "emailAddress": email,
    }

    params: dict[str, Any] = {
        "fileId": file_id,
        "body": permission_body,
        "sendNotificationEmail": notify,
        "fields": "id, role, type, emailAddress",
    }
    if message and notify:
        params["emailMessage"] = message

    result = _drive().permissions().create(**params).execute()

    return json.dumps({
        "permissionId": result.get("id", ""),
        "role": result.get("role", role),
        "email": email,
        "message": f"File shared with {email} as {role}.",
    }, indent=2)


@mcp.tool()
def list_permissions(file_id: str) -> str:
    """List all permissions (who has access) for a file or folder.

    Args:
        file_id: The Drive file or folder ID.
    """
    result = _drive().permissions().list(
        fileId=file_id,
        fields="permissions(id, role, type, emailAddress, displayName)",
    ).execute()

    permissions = result.get("permissions", [])
    formatted = []
    for p in permissions:
        formatted.append({
            "id": p.get("id", ""),
            "role": p.get("role", ""),
            "type": p.get("type", ""),
            "email": p.get("emailAddress", ""),
            "name": p.get("displayName", ""),
        })

    return json.dumps({
        "file_id": file_id,
        "permissions": formatted,
        "count": len(formatted),
    }, indent=2)


@mcp.tool()
def remove_permission(file_id: str, permission_id: str) -> str:
    """Remove a user's access to a file or folder.

    Use list_permissions first to find the permission_id to remove.

    Args:
        file_id: The Drive file or folder ID.
        permission_id: The permission ID to remove.
    """
    _drive().permissions().delete(
        fileId=file_id,
        permissionId=permission_id,
    ).execute()

    return json.dumps({
        "file_id": file_id,
        "permission_id": permission_id,
        "message": "Permission removed successfully.",
    }, indent=2)


# ---- Google Docs -----------------------------------------------------------

@mcp.tool()
def get_doc_content(document_id: str) -> str:
    """Read the full text content of a Google Doc using the Docs API.

    Returns the document title and body text extracted from the structural elements.

    Args:
        document_id: The Google Docs document ID.
    """
    doc = _docs().documents().get(documentId=document_id).execute()
    title = doc.get("title", "")

    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"].get("elements", []):
                text_content = run.get("textRun", {}).get("content", "")
                if text_content:
                    text_parts.append(text_content)

    return json.dumps({
        "title": title,
        "documentId": document_id,
        "content": "".join(text_parts),
    }, indent=2)


@mcp.tool()
def update_google_doc(document_id: str, operations: list[dict]) -> str:
    """Insert, replace, or delete text in a Google Doc.

    Each operation is a dict with a single key matching a Docs API batchUpdate
    request type. Common operations:

    Insert text at index:
      {"insertText": {"location": {"index": 1}, "text": "Hello world"}}

    Replace all occurrences:
      {"replaceAllText": {"containsText": {"text": "old", "matchCase": true}, "replaceText": "new"}}

    Delete a range:
      {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 10}}}

    Args:
        document_id: The Google Docs document ID.
        operations: List of batchUpdate request objects.
    """
    if not operations:
        return json.dumps({"error": "No operations provided."})

    result = _docs().documents().batchUpdate(
        documentId=document_id,
        body={"requests": operations},
    ).execute()

    return json.dumps({
        "documentId": result.get("documentId", document_id),
        "replies": len(result.get("replies", [])),
        "message": f"Applied {len(operations)} operation(s) successfully.",
    }, indent=2)


@mcp.tool()
def create_google_doc(title: str, body_text: str = "") -> str:
    """Create a new Google Doc with optional initial content.

    Args:
        title: Title of the new document.
        body_text: Plain text to insert as the document body. Leave empty for a blank doc.
    """
    doc = _docs().documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    url = f"https://docs.google.com/document/d/{doc_id}/edit"

    if body_text:
        _docs().documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": body_text}}]},
        ).execute()

    return json.dumps({
        "documentId": doc_id,
        "title": title,
        "url": url,
        "message": "Document created successfully.",
    }, indent=2)


# ---- Google Sheets ---------------------------------------------------------

@mcp.tool()
def read_sheet(spreadsheet_id: str, range: str = "", sheet_name: str = "") -> str:
    """Read data from a Google Spreadsheet.

    Args:
        spreadsheet_id: The spreadsheet ID from the URL.
        range: A1 notation range like 'Sheet1!A1:D10'. If empty, reads the whole first sheet.
        sheet_name: Sheet tab name. Used only if range is empty.
    """
    if not range:
        range = f"{sheet_name}!A:ZZ" if sheet_name else "A:ZZ"

    result = _sheets().spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range,
    ).execute()

    rows = result.get("values", [])
    return json.dumps({
        "spreadsheetId": spreadsheet_id,
        "range": result.get("range", range),
        "rows": len(rows),
        "data": rows,
    }, indent=2)


@mcp.tool()
def update_sheet_cells(spreadsheet_id: str, range: str, values: list[list[str]]) -> str:
    """Write data to cells in a Google Spreadsheet.

    Args:
        spreadsheet_id: The spreadsheet ID.
        range: A1 notation range like 'Sheet1!A1:B2'. Must match the dimensions of values.
        values: 2D array of cell values, e.g. [["Name", "Score"], ["Alice", "95"]].
    """
    result = _sheets().spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    return json.dumps({
        "spreadsheetId": spreadsheet_id,
        "updatedRange": result.get("updatedRange", ""),
        "updatedCells": result.get("updatedCells", 0),
        "updatedRows": result.get("updatedRows", 0),
        "message": "Cells updated successfully.",
    }, indent=2)


@mcp.tool()
def append_sheet_rows(spreadsheet_id: str, values: list[list[str]], range: str = "A1", sheet_name: str = "") -> str:
    """Append rows to the end of data in a Google Spreadsheet.

    Unlike update_sheet_cells which overwrites a specific range, this appends
    after the last row that contains data.

    Args:
        spreadsheet_id: The spreadsheet ID.
        values: 2D array of row values, e.g. [["Alice", "95"], ["Bob", "87"]].
        range: A1 notation starting point for finding the table. Defaults to "A1" (first sheet).
        sheet_name: Sheet tab name. If provided, overrides the range sheet reference.
    """
    target = f"{sheet_name}!{range}" if sheet_name else range

    result = _sheets().spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=target,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()

    updates = result.get("updates", {})
    return json.dumps({
        "spreadsheetId": spreadsheet_id,
        "updatedRange": updates.get("updatedRange", ""),
        "updatedRows": updates.get("updatedRows", 0),
        "updatedCells": updates.get("updatedCells", 0),
        "message": f"Appended {len(values)} row(s) successfully.",
    }, indent=2)


@mcp.tool()
def create_spreadsheet(title: str, sheet_names: list[str] | None = None) -> str:
    """Create a new Google Spreadsheet.

    Args:
        title: Title of the new spreadsheet.
        sheet_names: Optional list of sheet tab names. Defaults to a single "Sheet1".
    """
    body: dict[str, Any] = {"properties": {"title": title}}
    if sheet_names:
        body["sheets"] = [
            {"properties": {"title": name}} for name in sheet_names
        ]

    result = _sheets().spreadsheets().create(body=body).execute()
    ss_id = result["spreadsheetId"]
    sheets_created = [s["properties"]["title"] for s in result.get("sheets", [])]

    return json.dumps({
        "spreadsheetId": ss_id,
        "title": title,
        "url": f"https://docs.google.com/spreadsheets/d/{ss_id}/edit",
        "sheets": sheets_created,
        "message": "Spreadsheet created successfully.",
    }, indent=2)


# ---- Google Slides ---------------------------------------------------------

def _extract_slide_text(slide: dict) -> list[str]:
    """Recursively extract text from all shapes on a slide."""
    texts = []
    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        text_obj = shape.get("text", {})
        for te in text_obj.get("textElements", []):
            run = te.get("textRun", {})
            content = run.get("content", "")
            if content.strip():
                texts.append(content)
        # Also check tables
        table = element.get("table", {})
        for row in table.get("tableRows", []):
            for cell in row.get("tableCells", []):
                cell_text = cell.get("text", {})
                for te in cell_text.get("textElements", []):
                    run = te.get("textRun", {})
                    content = run.get("content", "")
                    if content.strip():
                        texts.append(content)
    return texts


@mcp.tool()
def get_presentation(presentation_id: str) -> str:
    """Get metadata and slide overview for a Google Slides presentation.

    Returns the title, number of slides, slide dimensions, and a summary
    of each slide (index, objectId, and text preview).

    Args:
        presentation_id: The Google Slides presentation ID.
    """
    pres = _slides().presentations().get(presentationId=presentation_id).execute()
    title = pres.get("title", "")
    slides = pres.get("slides", [])
    page_size = pres.get("pageSize", {})

    slide_summaries = []
    for i, slide in enumerate(slides):
        texts = _extract_slide_text(slide)
        preview = " ".join(texts)[:200]
        slide_summaries.append({
            "index": i,
            "objectId": slide.get("objectId", ""),
            "textPreview": preview,
            "elementCount": len(slide.get("pageElements", [])),
        })

    return json.dumps({
        "presentationId": presentation_id,
        "title": title,
        "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
        "slideCount": len(slides),
        "pageSize": page_size,
        "slides": slide_summaries,
    }, indent=2)


@mcp.tool()
def get_slide_content(presentation_id: str, slide_index: int = 0) -> str:
    """Read the full text content of a specific slide in a presentation.

    Returns all text from shapes, text boxes, and tables on the slide.

    Args:
        presentation_id: The Google Slides presentation ID.
        slide_index: Zero-based index of the slide to read (default: first slide).
    """
    pres = _slides().presentations().get(presentationId=presentation_id).execute()
    slides = pres.get("slides", [])

    if slide_index < 0 or slide_index >= len(slides):
        return json.dumps({
            "error": f"Slide index {slide_index} out of range. Presentation has {len(slides)} slides.",
        }, indent=2)

    slide = slides[slide_index]
    texts = _extract_slide_text(slide)

    elements = []
    for pe in slide.get("pageElements", []):
        el_info: dict[str, Any] = {
            "objectId": pe.get("objectId", ""),
            "type": "shape" if "shape" in pe else "table" if "table" in pe else "image" if "image" in pe else "other",
        }
        shape = pe.get("shape", {})
        if shape:
            el_info["shapeType"] = shape.get("shapeType", "")
            shape_texts = []
            for te in shape.get("text", {}).get("textElements", []):
                run = te.get("textRun", {})
                content = run.get("content", "")
                if content.strip():
                    shape_texts.append(content)
            el_info["text"] = "".join(shape_texts)
        elements.append(el_info)

    return json.dumps({
        "presentationId": presentation_id,
        "slideIndex": slide_index,
        "objectId": slide.get("objectId", ""),
        "fullText": "\n".join(texts),
        "elements": elements,
    }, indent=2)


@mcp.tool()
def update_presentation(presentation_id: str, operations: list[dict]) -> str:
    """Update a Google Slides presentation using batchUpdate requests.

    Each operation is a dict with a single key matching a Slides API batchUpdate
    request type. Common operations:

    Insert text into a shape:
      {"insertText": {"objectId": "shape_id", "text": "Hello", "insertionIndex": 0}}

    Replace all text matching a tag:
      {"replaceAllText": {"containsText": {"text": "{{placeholder}}", "matchCase": true}, "replaceText": "actual value"}}

    Delete text from a shape:
      {"deleteText": {"objectId": "shape_id", "textRange": {"type": "ALL"}}}

    Create a new slide:
      {"createSlide": {"insertionIndex": 1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}}

    Delete a slide:
      {"deleteObject": {"objectId": "slide_object_id"}}

    Args:
        presentation_id: The Google Slides presentation ID.
        operations: List of batchUpdate request objects.
    """
    if not operations:
        return json.dumps({"error": "No operations provided."})

    result = _slides().presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": operations},
    ).execute()

    return json.dumps({
        "presentationId": result.get("presentationId", presentation_id),
        "replies": len(result.get("replies", [])),
        "message": f"Applied {len(operations)} operation(s) successfully.",
    }, indent=2)


@mcp.tool()
def create_presentation(title: str) -> str:
    """Create a new blank Google Slides presentation.

    Args:
        title: Title of the new presentation.
    """
    pres = _slides().presentations().create(body={"title": title}).execute()
    pres_id = pres["presentationId"]

    return json.dumps({
        "presentationId": pres_id,
        "title": title,
        "url": f"https://docs.google.com/presentation/d/{pres_id}/edit",
        "message": "Presentation created successfully.",
    }, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
