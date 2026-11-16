# Changelog

## [0.3.0] - 2026-11-16

### Added

- A status may name absolute file paths in `watch` (`scripts/dashboard.py` passes them on). On Claude Code the module
  re-reads them after every tool call and redraws the band when one changed — also inside a turn. No plugin is named
  in the dashboard and no timer runs.

### Why

A free-hands goal is worked through inside one turn, and a Stop that free-hands blocks does not end that turn, so 0.2.0
showed a goal's progress only when the whole run ended (z-lab `free-hands-lab/eta-probes-r3-2.1.325`, `-r4` T08). A
mod's `tool.call` handler sees the tool's effect on disk and can redraw mid-turn (`-r4` T09, T10).

Evidence: z-lab `dashboard-lab/run-0.3.0` on Claude Code 2.1.325: with free-hands 0.5.0 naming its goal file, the band
changed after each of three finished items, 1.4–2.0 s after each (D09); 0.2.0 changed once in the same run and skipped
a state (D10). Not measured: Codex (unchanged: a command), the time a refresh adds to a tool call, terminals other than
tmux.

## [0.2.0] - 2026-10-16

### Changed

- The band is a dim rule as wide as the band, then one `{icon}label: value` entry per declared switch (bold label,
  the deciding level and the detail dimmed); entries wrap whole on a narrow terminal. The audit prints the same form.
- `dashboard.json` entries take an `icon` (one emoji; `🔹` when missing).

### Why

The 0.1.0 line was hard to tell apart from the transcript (maintainer request, 2026-10-16).

Evidence: z-lab `dashboard-lab/run-0.2.0` (D06–D08) on Claude Code 2.1.300 and Codex 0.162.1: the rule and the entries
on one row at 200 columns, wrapped whole at 80 columns, and the Codex audit in the same form. Not measured: styling,
terminals other than tmux.

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
