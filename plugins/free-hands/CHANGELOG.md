# Changelog

## [0.3.0] - 2026-10-13

### Changed

- The goal belongs to one session. The goal file gains `owner: <session id>`, and every guard — the restore note, the
  ask and stop guards, the counter and the hard-limit shell hook — acts only in that session and the subagents it
  starts. Another session in the same repository is left alone; when its prompt mentions free-hands, the entry note
  says which session owns the run. The id comes from the hook input's `session_id`.
- The prompt hook gives the session's id (`[free-hands: session]`) on `/free-hands:run` / `$free-hands:run` and with
  the entry note; SKILL.md writes it as `owner:` when it starts, resumes or takes over a run. Running the command in
  another session moves the run there.
- A guarded goal without `owner:` (one written by 0.2.0, or an agent that left the line out) is claimed under the lock
  by the first session a hook sees. A hook input without a valid `session_id` keeps the 0.2.0 repository-wide guard.

### Why

A user ran a goal in one terminal, opened a second terminal in the same repository and typed a prompt: the second
session picked up the goal and the counter rose. `guard.py` keyed everything on the repository path.

Evidence: z-lab `free-hands-lab/session-id-0.3.0` (S01–S05, before building) on Claude Code 2.1.296 and Codex 0.162.1:
both hosts send `session_id` on every hook event, keep it across resume and compaction, and give a subagent its parent's
id; an inherited `CLAUDE_CODE_SESSION_ID` named the wrong session, so environment variables are not used.
`free-hands-lab/run-0.3.0` (O01–O06), one run per case on both hosts: with 0.2.0 a second session was handed the
running goal (Claude did its item and marked the goal done; Codex archived it and wrote its own); with 0.3.0 the
second session never touched the goal and the file stayed byte-identical; `gh pr merge 1` was denied in the owner
session and in its subagent and ran in another session; the skill wrote `owner:` from the hook note when starting a
run and replaced it when taking one over. Not measured: two sessions running at the same moment, the first-session
claim at runtime (unit tests only).

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
