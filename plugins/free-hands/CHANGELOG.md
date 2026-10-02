# Changelog

## [0.1.0] - 2026-10-01

### Added

- Added the free-hands autonomous mode for Claude Code and Codex, with a persisted finite goal checklist, session hooks, and a five-role evidence-based decision panel.
- Ported from a project-local skill.

### Why

Keep a goal moving across questions, interruptions, restarts, and compaction while recording decisions and preserving explicit hard limits.

Evidence: z-lab `free-hands-lab/run-0.1.0` (F01–F12) and `free-hands-lab/run-0.1.0-r2` (G01–G06), one run per case on
Claude Code 2.1.286–2.1.287 and Codex 0.159.3–0.160.0. Three behaviors were fixed after the first run. Measured
again: a stop request now ends as `paused` (F03 → G01), the goal folder is ignored through `.free-hands/.gitignore`
because Codex's sandbox blocks `.git/info/exclude` (F07 → G05), and the Claude main waits for every role and gets no
entry note on background-task notifications (F08 → G04). Unit tests only: a `done`/`waiting` status with open items
keeps the guard engaged (G01 did not reach it); only `## Checklist` items outside code count, and a notification quoted
in a prompt keeps the rest of the prompt (product review FH-44, FH-45). A sandboxed Codex main cannot reach the panel and
degrades to deciding alone (G06). Not measured: the ask-tool denials on both hosts, the release at `max_iterations` at
runtime, round 2, a role's write attempt, stacked PRs, and whether the panel decides better than one agent (a
hypothesis).
