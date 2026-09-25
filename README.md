# Google Workspace MCP

One local server with full CRUD on Drive, Docs, Sheets, and Slides. Search, create, edit in place, comment, share, move. Plus three skills the official Drive MCP does not ship: prefill a deck, recap what the room said (not your pitch), and file work from other tools into a folder you can share.

Works on any host that can run a local MCP server: Claude, Cursor, ChatGPT, Codex, Gemini, and others. You create the Desktop OAuth client. Keys stay in `~/.gdrive-mcp/`.

**Last updated:** September 25, 2026

## vs the official Drive MCP

What most hosts list as "Google Drive" is either the local readonly plugin (`@modelcontextprotocol/server-gdrive`) or [Google's Drive remote](https://developers.google.com/workspace/drive/api/guides/configure-mcp-server) (8 tools: search, read, create, copy, download, metadata, permissions list, recent). That is Drive-only, and it is not full CRUD.

This server is one process for the whole Workspace surface: Drive **and** Docs, Sheets, and Slides.

| Capability | Official Drive MCP | This server |
| --- | --- | --- |
| Search and read Drive files | ✅ | ✅ |
| Create a new Drive file | Remote only | ✅ |
| Full CRUD on Drive (move, folders, comments, share, revoke) | ❌ | ✅ |
| Full CRUD on Google Docs | ❌ | ✅ |
| Full CRUD on Google Sheets | ❌ | ✅ |
| Full CRUD on Google Slides | ❌ | ✅ |
| Native `docs.google.com` URL on results | ❌ | ✅ |
| Structured slide text for a transcript diff | ❌ | ✅ |
| Bundled workflow skills | ❌ | ✅ |

Google also ships separate remotes for Docs, Sheets, and Slides. Those can write if you install all of them. They still omit comments, share, this skill pack, and a single local connector you own.

Same Desktop OAuth shape Google's Drive MCP asks for. You own the GCP project and the keys.

## Get started

Paste this into any agent. The repo URL is enough.

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```

Human checklist and host JSON: [docs/setup.md](docs/setup.md). What the process touches: [TRUST.md](TRUST.md).

## The package

```
Notion Slack Linear GitHub Granola
              |
              v
     this MCP + skills
              |
              v
  deck, folder, share, quotes
```

This repo is the Workspace write side and the playbooks. It does not include Notion, Slack, Linear, GitHub, or Granola. Pair those MCPs when the workflow needs them.

| Scenario | Skill | What you say |
| --- | --- | --- |
| Prefill or manage a deck | [slides-outline](skills/slides-outline/SKILL.md) | "Turn this plan into a Slides outline, then build it" or "Give me a table I can paste into Gemini" |
| Recap a review without replaying your pitch | [exec-feedback](skills/exec-feedback/SKILL.md) | "Diff the deck against the Granola transcript. Keep what they said." |
| Pull other tools into a shareable Drive folder | [drive-cleanup](skills/drive-cleanup/SKILL.md) | "Make a folder from this Linear epic and Slack thread, then share it" |

Install the skills (Claude Desktop does not load project `SKILL.md`):

```bash
npx skills add ankush-sw/gdrive-mcp -a cursor -a claude-code -a codex
```

Or copy `skills/<name>` into `.cursor/skills/`, `.claude/skills/`, or `.agents/skills/`. [setup](skills/setup/SKILL.md) is the install playbook, not a business workflow.

## 1. Slides: outline, then build or paste

You already have the content in chat, a Doc, a Sheet, or a markdown file. You need a deck you can stand up, or a tight outline you can drop into Gemini for generation.

How it runs:

1. The skill reads the source and writes an outline table (title, bullets, layout). It does not create a deck yet.
2. You mark the outline.
3. Either the agent builds it in Drive (`create_presentation`), or you copy the table into Gemini.

Paste:

```
Read this plan and make a Slides outline table. Wait for my edits.
Then either build the deck in Drive or format the table for Gemini.
```

Skill: [slides-outline](skills/slides-outline/SKILL.md).

## 2. Exec feedback: drop your talking points

Nobody needs a recap of the slides you just walked. They need what the CEO, the VP, or anyone else in the room said back.

Treat the Doc, Sheet, or deck as your script. Treat Granola, Zoom, Fireflies, Otter, or a pasted transcript as the room. Drop any line that is you dictating those slides or speaker notes. What remains is reactions, decisions, and quotes.

```
deck or doc (this MCP)
transcript (your meeting tool)
        |
        v
drop presenter dictation
        |
        v
exec quotes and decisions
```

The official Drive MCP cannot do this. It does not hand back structured slide text next to a transcript.

Paste:

```
Here is the deck URL and the Granola link.
Pull exec feedback. Drop anything that matches my slides or notes.
```

Skill: [exec-feedback](skills/exec-feedback/SKILL.md). If no transcript MCP is connected, paste the export.

| Vendor | Typical hook |
| --- | --- |
| Granola | Cursor plugin, or `https://mcp.granola.ai/mcp` |
| Zoom, Fireflies, Otter | That product's MCP or an export |
| None | Paste the transcript. Drive tools still run. |

## 3. Share pack: other tools into Drive

You have the work in Notion, Slack, Linear, or GitHub. You want a Drive folder you can send internally or outside the company, not another pile of Untitled files.

How it runs:

1. The other MCP reads the page, thread, issue, or repo.
2. This MCP creates or tidies the folder, writes a Doc / Sheet / Slide if you asked, then `share_file`.
3. [drive-cleanup](skills/drive-cleanup/SKILL.md) indexes first and moves only after you approve. Same skill if Drive is already a mess.

This repo does not ship those other MCPs. Connect the ones you already use.

Paste:

```
Pull the Linear epic and the Slack thread.
Create a Drive folder, file a summary Doc, and share it as commenter with this list.
```

## Tools

29 tools. Full list in [docs/architecture.md](docs/architecture.md).

**Drive:** search, recent, folders, shared, starred, metadata, content, comments, upload, copy, move, export, create folder, comment, reply, share, list permissions, revoke

**Docs / Sheets / Slides:** create, read, and update in place

## Docs

- [Setup (human)](docs/setup.md)
- [Setup (agent)](skills/setup/SKILL.md)
- [Trust and privacy](TRUST.md)
- [Security (how to report)](SECURITY.md)
- [Architecture](docs/architecture.md)

## License

MIT. Copyright (c) 2026 Ankush Rustagi. Drive mark: see [TRUST.md](TRUST.md#marks).
