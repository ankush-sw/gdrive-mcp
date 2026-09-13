---
name: exec-feedback
description: Pull executive reactions out of a meeting by treating a Drive Doc, Sheet, or Slides as the presenter's script and dropping matching transcript lines. Use when the user wants exec quotes, what leadership said back, or a review recap that is not a replay of the pitch.
---

# Exec feedback

The job after a review is what other people in the room said. Not a recap of the slides.

## When to use

- "What did the VP actually say?"
- Recap a review, readout, or exec walkthrough
- Pair a Drive artifact with a meeting transcript

## Transcript source (do this first)

This skill does not store transcripts. Pull them from the user's meeting tool.

1. Ask which vendor they use. Do not assume Granola.
2. Use that vendor's MCP or export. Typical options:
   - Granola: Cursor plugin, or the HTTP MCP at `https://mcp.granola.ai/mcp` (Claude Code, Claude Desktop, Codex). Prefer `query_granola_meetings` for an open question, `list_meetings` / `get_meetings` / `get_meeting_transcript` when they pasted a `notes.granola.ai` URL.
   - Zoom, Fireflies, Otter, or a pasted `.vtt` / `.txt`: read the file they give you. Do not invent a connector.
3. If no transcript MCP is connected, say so and ask for a paste or export. Do not skip to Drive-only guesswork.

## Drive tools

Use this Google Workspace MCP:

- Slides: `get_presentation`, then `get_slide_content` for each slide you walked
- Docs: `get_doc_content`
- Sheets: `read_sheet`
- Search: `search_drive` or `list_recent_files` if they named the file and did not paste an ID

## Playbook

1. Identify the artifact. Confirm title and URL with the user before treating it as the script.
2. Pull the transcript from their vendor (see above).
3. Read the artifact as structured text (slide titles and bullets, doc headings, sheet row labels).
4. Drop any transcript span that is the presenter dictating that same text. Near-paraphrase counts as dictation.
5. Keep other speakers: reactions, decisions, questions, quotes, "let's do X."
6. Return a short list: quote or paraphrase, speaker if known, timestamp or meeting label if you have it. End with decisions and open questions.

## Do not

- Recap the pitch
- Invent quotes
- Move or edit the Drive file unless they asked
- Send the transcript to a third-party crawler
