---
name: drive-cleanup
description: Index Google Drive files, propose folders and names, then organize only after the user approves. Also use when they have Notion, Slack, Linear, or GitHub output and want a Drive folder they can share. Use when Drive is messy, they want a file inventory, or they ask to label, file, or tidy Docs, Sheets, and Slides.
---

# Drive cleanup

Index first. Propose a filing plan. Move only after they say yes.

This server has no Drive-labels API. "Label" here means a clear name and a folder, not a Google label chip.

## When to use

- "What is actually in my Drive?"
- File Untitled docs, duplicate decks, or downloads
- Propose a folder tree and rename scheme
- "I have Notion / Slack / Linear / GitHub output. Put it in a Drive folder I can share."

## Tools

- Inventory: `list_recent_files`, `search_drive`, `list_folder_contents`, `list_shared_with_me`, `list_starred_files`
- Inspect: `get_file_metadata` (and `get_doc_content` / `get_slide_content` / `read_sheet` only when the name is useless)
- Act, after approval: `create_folder`, `move_file` (optional `new_name`), `copy_file` if they want a safety copy, `create_google_doc` / `create_spreadsheet` / `create_presentation` when they asked for a new file, `share_file` when they named recipients
- Other products: read Notion, Slack, Linear, or GitHub through *their* MCP. This repo does not include those servers.

## Playbook

0. **Share pack (if they named another tool).** Read that MCP first (page, thread, issue, repo). Summarize what will land in Drive. Then continue at step 1 with a new or existing folder as the scope. Do not invent a Notion or Slack connector.
1. **Scope.** Ask: My Drive vs a folder ID vs shared-with-me. Default: last 50 recent files plus any folder they named. Do not page the whole Drive unless they asked.
2. **Index.** Table:

   | Name | Type | Modified | Owner | URL | Current folder | Suggested name | Suggested folder |
   | --- | --- | --- | --- | --- | --- | --- | --- |

   Cluster by project, date, or type. Flag Untitled, duplicates, and items sitting in root.
3. **Plan.** Folder names you would create, files that would move, files you would leave. No moves in this step.
4. **Wait.** They approve the plan, or a subset (by row).
5. **Apply.** `create_folder` as needed, then `move_file` only for approved rows. Create the Doc / Sheet / Slide they asked for. `share_file` only if they named recipients. Return new URLs.

## Rules

- Shared-with-me: do not move someone else's file into your tree unless they own it or they explicitly want a `copy_file`.
- Trash: this server does not trash. Say so if they ask to delete.
- Batch cap: 20 moves per confirmation. Show the next batch if more remain.

## Do not

- Move or rename in the same turn as the first index
- Invent a labels product this MCP does not expose
- Touch files outside the approved list
