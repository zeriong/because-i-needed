# Changelog

## [0.1.0] - 2026-10-14

### Added

- Claude Code: one line above the prompt with the state every enabled because-i-needed plugin declares in its
  `dashboard.json` (root Rule 11), refreshed at session start, after each turn and when the usage window moves; no line
  when nothing is declared.
- `dashboard:audit`: the same line with each switch's project and global value, on both hosts.
- Codex: the README shows how to keep the 7-day window in Codex's own status line (`weekly-limit`).

### Why

Switches that stay set — peer-coding's mode, a free-hands goal, a budget threshold — were invisible until they acted
(maintainer request, 2026-10-14).

Evidence: z-lab `dashboard-lab/run-0.1.0` (D01–D05) on Claude Code 2.1.299 and Codex 0.162.1, one run per case: the line
and the audit with budget, free-hands and peer-coding; no line without a declaration; the Codex audit from installed
plugins. `dashboard-lab/codex-status-line-0.162.1` (C02): `weekly-limit` shows `weekly 28% left`. Not measured: plugins
installed through a Claude Code marketplace (unit tests), the line after a switch changes mid-session.
