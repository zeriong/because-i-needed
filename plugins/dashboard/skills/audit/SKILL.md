---
name: audit
description: "Show the state of every because-i-needed mode the user has on — peer-coding, free-hands, budget and any plugin that declares one — with where each value comes from (project, global or default). Read-only. Use when the user asks what is on, e.g. \"/dashboard:audit\", \"show my modes\", \"모드 상태 보여줘\"."
---

# dashboard: audit

Claude Code invokes `/dashboard:audit`; Codex invokes `$dashboard:audit`. `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` when
expanded by Claude Code, or the absolute path two directories above this skill's directory on Codex (resolve it from the
loaded SKILL.md path, not the working directory).

Run the one command for your host from the project directory and report its output as-is. It changes nothing.

```bash
python3 "<plugin>/scripts/dashboard.py" --host claude   # Claude Code
python3 "<plugin>/scripts/dashboard.py" --host codex    # Codex
```

On Codex there is no line above the prompt. If the user wants the usage window always in view, point them to Codex's own
status line: `[tui] status_line = ["model-with-reasoning", "weekly-limit"]` in `~/.codex/config.toml` (or `/statusline`).
It shows what is left of the 7-day window, not what is used.
