# free-hands — development rules

Every shared rule in the root `CLAUDE.md` applies. This plugin gives an agent a finite goal checklist and instructions to continue without asking; a five-role read-only panel advises on user-level decisions, and the main agent decides from evidence.

Contents: the `run` skill and Codex adapter, five read-only panel roles, `hooks/hooks.json` (UserPromptSubmit, SessionStart, PreToolUse, Stop), `scripts/guard.py`, `scripts/panel.py`, and a byte-identical `scripts/latest-model.py` copy.

## Invariants

- Keep `.free-hands/goal.md` and the `- [ ]`, `- [x]`, `- [-]` marks unchanged. **Why (root Rule 8):** these identifiers are persisted in users' repositories; renaming them would strand active goals.
- Guards fail open on malformed hook input, malformed or unreadable goal files, lock timeouts, and failed writes. Stop is blocked only after the incremented iteration counter is on disk. Metadata counts only when the whole value is valid (`iterations: 0 x` is malformed). **Why (FH-03, FH-17, FH-24):** broken state or I/O must not trap a user's session, and a stop blocked without a durable counter could run past `max_iterations`.
- Keep fail-open scoped to ask/stop guards and restore notes. The prompt hook routes entry without a goal file. **Why (FH-06):** entry happens before any goal file exists.
- Keep the restore note's goal path, skill path and its rules (never ask; the panel; the hard limits; keep the goal file current; pause first). **Why (D4a/FH-05):** the skill body is not reloaded after compaction and this file never loads in user sessions, so the SessionStart/UserPromptSubmit note is the only carrier; shortening it drops rules.
- `FREE_HANDS_ROLE` disables the guard in panel children so their work cannot change the main goal or its counter. **Why (FH-04):** Codex panel children load the same plugin hooks in the same repository; without it a child's Stop hook would raise the parent's counter and keep the child from finishing.
- Keep the hard limits in `skills/run/SKILL.md` and its restore note as rules for the agent: no PR merge or merge into the default branch, irreversible deletion, deployment, publication, or external sending. A blocked item is marked as needing the user and skipped while the run continues. Hooks do not block these commands. **Why (maintainer decision, 2026-10-01; FH-26):** these boundaries preserve decisions for the user, and documenting their instruction source avoids implying that a command guard enforces them.
- The panel advises; it never turns a failed check into a pass. Fix a failing check or mark the item as needing the user. Never forge approval, bypass a gate, or claim an unrun check passed. **Why (FH-14):** a panel recommendation cannot change the observed result of a check or authorize bypassing its gate.
- Keep script commands only in `skills/run/SKILL.md`. Reference files may explain a route, but must not introduce commands that depend on an unexpanded `CLAUDE_PLUGIN_ROOT` (root Rule 1). **Why:** Claude expands the variable in skill content, but not in later-read reference files.
- Resolve the newest model of each role's family with `scripts/latest-model.py` immediately before every dispatch and retry. Keep this file byte-identical to the copies in the other plugins; do not write versioned model IDs in plugin files. **Why (D9/FH-10):** an alias redirect or a stale catalog would silently run an older model; `tests/test_compatibility.py` checks that the copies are identical.

## Versioning

Use SemVer for this plugin: MAJOR for a breaking goal-file format or command change; MINOR when a rule, role, or hook behavior is added or changed; PATCH for documentation changes. **Why (root Rule 2):** installed copies are version-keyed, so changes must be classified and released consistently.

## Evidence

z-lab `free-hands-lab/run-0.1.0` (F01–F12) and `run-0.1.0-r2` (G01–G06); decisions and changes in
`free-hands-lab/analyze/improvement-backlog.md`.

- Hooks and restore note on both hosts: F01, F02, F04, G02. Entry routing: F06. `FREE_HANDS_ROLE`: F05.
- `done`/`waiting` with open items stays guarded: F03 (observed escape) → G01 (stop request now `paused`; the guard
  path itself is unit-tested only).
- `.free-hands/.gitignore` instead of `.git/info/exclude`: F07 → G05.
- Wait for every role; notifications are not prompts: F08 → G04.
- Codex panel: `codex exec -s read-only` children run the resolved models (F09); native subagents have no read-only
  control (F10); a sandboxed main has no network for them and degrades (G06).
- Open items are `- [ ]` under `## Checklist` outside fenced code; notification blocks are stripped from prompts
  (review FH-44, FH-45; unit tests on the real script only).
- Agents rewrote `iterations` (F04, G03): `max_iterations` bounds the loop only while the agent leaves the counter alone.
- Not measured: AskUserQuestion / `request_user_input` denials (F11), the max release and write failure at runtime,
  round 2, a role's write attempt, stacked PRs, decision quality.
