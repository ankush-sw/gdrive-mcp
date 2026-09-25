# Install this repo

Paste this file's URL, or the repo URL, into any agent (Claude, Cursor, ChatGPT, Codex, Gemini, or another MCP host). The agent should take it from here.

```
Install https://github.com/ankush-sw/gdrive-mcp
Read AGENTS.md and skills/setup/SKILL.md. Follow the setup skill until list_recent_files passes on this host.
```

**Agent:** STOP. Open [AGENTS.md](AGENTS.md), then run [skills/setup/SKILL.md](skills/setup/SKILL.md). Do not invent a second installer. Do not finish until `list_recent_files` returns a real file name.

**Human (no agent):** [docs/setup.md](docs/setup.md)

Done means one live `list_recent_files` call on the host they asked for, not a config file that "looks right."

What the process accesses, and why Claude Desktop warns: [TRUST.md](TRUST.md) (also inside the `.mcpb`).
