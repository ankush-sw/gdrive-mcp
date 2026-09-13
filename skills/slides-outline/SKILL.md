---
name: slides-outline
description: Turn Cursor or Claude Code work (chat, markdown, a Doc, a Sheet) into a Google Slides outline, then build the deck after the user approves. Use when they want a readout deck, a working outline in Slides, or to port agent output into a presentation.
---

# Slides outline

Port work you already have in the editor into a deck you can stand up and talk from. Outline first. Build second.

## When to use

- "Put this chat / plan / doc into Slides"
- Working readout from a coding or PM session
- New deck from a Doc, Sheet, or local markdown

## Sources

Read the source fresh. Do not reuse an earlier summary.

| Source | How to read it |
| --- | --- |
| Local markdown or chat | `Read` the file, or use the current conversation |
| Google Doc | `get_doc_content` |
| Google Sheet | `read_sheet` |
| Existing deck | `get_presentation` then `get_slide_content` |

If they name a Drive file, `search_drive` first and confirm the URL.

## Playbook

1. **Outline table.** Do not create a presentation yet.

   | Slide | Title | Content summary | Layout | Source |
   | --- | --- | --- | --- | --- |
   | 1 | Title | Name, audience, date | Title | New |

   Rules: one idea per slide. Split dense lists. Add a divider between sections. Last slide is next steps or links.

2. **Wait.** Do not call `create_presentation` until they approve or mark the outline.

3. **Build.**
   - `create_presentation` with the agreed title
   - `update_presentation` with `createSlide` ops (meaningful `objectId` values)
   - Add title + body text boxes (`createShape` TEXT_BOX + `insertText`). Condense. Do not paste a whole sheet row.

4. **Read back.** `get_slide_content` on each new slide. Fix mismatches.

5. Hand back the `docs.google.com/presentation` URL.

## Text rules

- Title in one box at the top. Body below.
- One or two sentences per bullet.
- Image still in another file: put `[IMAGE: copy from …]` and skip pixels.

## Do not

- Build the deck before the outline is accepted
- Restyle with a brand system unless they named one
- Delete slides on an existing deck they still present from (propose a copy first)
