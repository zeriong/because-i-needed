# Changelog

## [0.2.0] - 2026-10-02

### Added

- A `PreToolUse` hook on shell commands (`scripts/guard.py shell`, `scripts/shellguard.py`) denies, while a goal is
  active, the ordinary commands that break the hard limits: merging into the default branch (`gh pr merge`, pushes and
  merges that update it, `gh api` merges), remote deletion (`git push --delete`/`:ref`/`--prune`/`--mirror`, `gh repo
  delete`, `gh release delete`), and deploy/publish/send (`npm|pnpm|yarn publish`, `docker push`, `gh release create`,
  `vercel`, `terraform apply`, `kubectl apply`, `helm install`, `sendmail`, …). The denial reaches the agent with the
  instruction to mark the item `[-]`. The goal file gains `default_branch:`.

### Changed

- SKILL.md: a denial is final; never route a limited action through a script, an interactive shell or another tool.
  Pushing branches, opening issues and PRs and commenting are allowed. The examples name peer-coding (formerly
  claude-x-codex).

### Why

The hard limits were instructions only (0.1.0 review FH-26). The hook is a backstop for a cooperative agent's ordinary
commands, not a defense against deliberate evasion; `rm`, database commands, heredoc bodies, scripts, interactive input
and other CLIs are not read (user decision, core scope).

Evidence: z-lab `free-hands-lab/run-0.2.0` (P01–P05) on Claude Code 2.1.287 and Codex 0.160.0, one run per case: the
hook denied `gh pr merge 1`, `npm publish` and `git push origin HEAD:main` before they ran on both hosts, an allowed
`gh pr view 1` ran, and without the hook the agents did run `gh pr merge 1` and `npm publish` (Claude reached the
fakes; on Codex the real binaries ran and failed — no credentials, exit 4; npm EPERM, exit 255). The full skill marked limited items `[-]` without
needing the hook (P05). The command list itself is covered by 206 unit cases. Not measured: Codex with hooks trusted
through `/hooks`, interactive sessions, commands outside the list.

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
