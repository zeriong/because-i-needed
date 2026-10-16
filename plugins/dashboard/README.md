<p align="center"><strong>dashboard</strong></p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>.</p>

<p align="center"><strong>See every because-i-needed mode you have on — and where each value comes from — in one line.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#what-it-shows">What it shows</a> &bull; <a href="#claude-code">Claude Code</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#how-a-plugin-joins">How a plugin joins</a> &bull; <a href="#limits-and-status">Limits and status</a> &bull; <a href="#installation">Installation</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub>Part of <a href="../../README.md">because-i-needed</a></sub></p>

---

because-i-needed plugins have switches that stay set — peer-coding's orchestration mode, a free-hands goal, a budget threshold — at the project or user level. dashboard shows them all, so a switch is never on without your knowing.

## What it shows

```
────────────────────────────────────────────────────────────────────────────────────────────────
💰budget: 80% · 5h now 24%   🙌free-hands: active 0/40 · 1 open (project) · owner lab-sess   🤝peer-coding: on (project)
```

- A dim rule, then one `{icon}label: value` entry per switch an enabled because-i-needed plugin declares, with `(project)` or `(env)` when that level decides it and a detail such as the last measured usage window or a goal's owner session. On a narrow terminal the entries wrap, one per row.
- Nothing is shown when no enabled plugin declares a switch.
- `/dashboard:audit` (Claude Code) or `$dashboard:audit` (Codex) prints the same line and, for each switch, the value set at the project and the global level. It changes nothing.

## Claude Code

The line sits above the prompt. It refreshes when the session starts, after each turn and when the usage window moves. dashboard finds the because-i-needed plugins Claude Code has installed and enabled.

## Codex

Codex gives plugins no place to draw, so on Codex the dashboard is the `$dashboard:audit` command. To keep the usage window in view, turn on Codex's own status line item in `~/.codex/config.toml` (or with `/statusline`):

```toml
[tui]
status_line = ["model-with-reasoning", "weekly-limit"]
```

It shows what is **left** of the 7-day window (for example `weekly 28% left`), not what is used. An unknown item id is dropped with a warning.

## How a plugin joins

A plugin declares its switches in `dashboard.json` at its root. Every because-i-needed plugin with a `mode` skill must, and others may (the repository's Rule 11):

```json
{ "entries": [ { "label": "peer-coding", "icon": "🤝", "status": ["bash", "scripts/mode.sh", "status", "--json"] } ] }
```

The `icon` is one emoji shown before the label (`🔹` when it is missing). The `status` command is read-only, runs in the project directory and prints one JSON object: `value`, `source` (`env`, `project`, `global` or `default`), `project` and `global` (the value at each level, or `null`), and an optional `detail`. A command that fails, takes over two seconds or prints something else shows as `error`. A plugin added later appears without a dashboard release.

Plugins loaded from a folder with `claude --plugin-dir` are not in Claude Code's install records; list their folders in `BECAUSE_I_NEEDED_PLUGIN_DIRS` (separated like `PATH`) to show them.

## Limits and status

Measured once per case on Claude Code 2.1.299 and Codex 0.162.1 ([z-lab `dashboard-lab/run-0.1.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.1.0); the Codex status line in [`codex-status-line-0.162.1`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/codex-status-line-0.162.1)):

- On Claude Code the line above showed budget, free-hands and peer-coding, and `/dashboard:audit` printed each level; with no declaring plugin there was no line (D01–D03).
- On Codex `$dashboard:audit` printed the same entries from the installed plugins, the budget entry with the 7-day window; with no declaring plugin it said so (D04–D05).
- Codex's `weekly-limit` item showed `weekly 28% left` (C02).
- Since 0.2.0 ([`run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.2.0), Claude Code 2.1.300): the rule and the `{icon}label: value` entries on one row at 200 columns, and wrapped whole, one per row, at 80 columns; the Codex audit prints the same entries (D06–D08).

Not measured: terminals other than tmux, and the bold and dim styling; plugins installed through a Claude Code marketplace (the measured line read `--plugin-dir` folders; the install records are unit-tested); the line refreshing after a switch changes mid-session; desktop and IDE surfaces.

Claude Code's plugin hooks module API that draws the line is marked early access and may change between releases.

## Installation

First add the marketplace, then install the plugin:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install dashboard@because-i-needed
```

For Codex, follow the [marketplace instructions](../../README.md#codex). `python3` must be on `PATH`.

## License

MIT. See [LICENSE](../../LICENSE).
