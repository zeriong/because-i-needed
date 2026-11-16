# free-hands — development rules

Every shared rule in the root `CLAUDE.md` applies. This plugin gives an agent a finite goal checklist and instructions to continue without asking; a five-role read-only panel advises on user-level decisions, and the main agent decides from evidence.

Contents: the `run` skill and Codex adapter, five read-only panel roles, `dashboard.json`, `hooks/hooks.json` (UserPromptSubmit, SessionStart, PreToolUse for the ask tool and for Bash, PostToolUse, Stop), `scripts/guard.py`, `scripts/shellguard.py`, `scripts/eta.py` with `scripts/eta-baseline.json`, `scripts/panel.py`, and a byte-identical `scripts/latest-model.py` copy.

## Invariants

- Keep `.free-hands/goal.md` and the `- [ ]`, `- [x]`, `- [-]` marks unchanged. **Why (root Rule 8):** these identifiers are persisted in users' repositories; renaming them would strand active goals.
- Guards fail open on malformed hook input, malformed or unreadable goal files, lock timeouts, and failed writes. Stop is blocked only after the incremented iteration counter is on disk. Metadata counts only when the whole value is valid (`iterations: 0 x` is malformed). **Why (FH-03, FH-17, FH-24):** broken state or I/O must not trap a user's session, and a stop blocked without a durable counter could run past `max_iterations`.
- Keep fail-open scoped to ask/stop guards and restore notes. The prompt hook routes entry without a goal file. **Why (FH-06):** entry happens before any goal file exists.
- Keep the restore note's goal path, skill path and its rules (never ask; the panel; the hard limits; keep the goal file current; pause first). **Why (D4a/FH-05):** the skill body is not reloaded after compaction and this file never loads in user sessions, so the SessionStart/UserPromptSubmit note is the only carrier; shortening it drops rules.
- Every guard acts only in the session named by the goal's `owner:` — the hook input's `session_id`, never an
  environment variable. Another session in the same repository gets no restore note, no ask or stop guard, no counter
  and no shell guard; it only learns, when its prompt mentions free-hands, who owns the run. A guarded goal without
  `owner:` is claimed under the lock by the first session a hook sees; an input without a valid `session_id` keeps the
  repository-wide guard. The skill writes `owner:` from the `[free-hands: session]` note when it starts, resumes or
  takes over a run. **Why (user report, 2026-10-13; z-lab `session-id-0.3.0` S01–S05):** a second terminal in the
  repository picked up the running goal and raised its counter. Both hosts send `session_id` on every event, keep it
  across resume and compaction, and give a subagent its parent's id; an inherited `CLAUDE_CODE_SESSION_ID` named the
  wrong session.
- While budget's question is open for the session (`$XDG_CONFIG_HOME/because-i-needed/budget/pending/<session id>.json`
  holds `"open": true`), the ask and stop guards stand aside; the shell guard does not. The skill and the restore note
  name it as the one exception to never-ask. **Why (maintainer decision, 2026-10-14: the usage question outranks
  free-hands; z-lab `plugin-platform-lab/mod-interactive-2.1.299` I05, `budget-lab/codex-gate-0.1.0` B03 →
  `budget-lab/run-0.1.0` R04, R07, `-r2` R12):** 0.3.0 blocked the question on Claude Code and, on Codex, the end of the
  gated turn.
- `guard.py status` prints the goal's state for the dashboard (root Rule 11, `dashboard.json`), with the expected finish
  while the goal is active and the goal file in `watch`. **Why (`dashboard-lab/run-0.1.0` D01, D04; `run-0.3.0` D09):**
  the dashboard redraws mid-turn only when a watched file changes.
- Estimates come from the agent, actual times only from hooks. Each item ends with the agent's `(~<minutes>m
  <category>)`, written once when it plans; the owner session's hooks (every PostToolUse, and prompt, session and stop)
  keep an active-time clock in `.free-hands/eta.json` and append one row per finished item to
  `.free-hands/timings.jsonl`. Keep both names (root Rule 8: they live in users' projects). **Why (run-0.1.0 F04, r2
  G03; z-lab `free-hands-lab/analyze` D16):** agents rewrote the counter they were given, so a self-reported duration is
  not a measurement.
- The clock does not count the gap after a turn that ended (an allowed Stop), before a new session or before a prompt
  (a turn interrupted with Esc sends no Stop), and counts a gap over 20 minutes only as far as the tool call's
  `duration_ms` covers it. A paused goal with items open is not timed. Items finished in one edit share the time by
  estimate; an item that first appears already checked while the run is under way joins that edit. The goal file is
  read again under the lock and the clock never moves back. The model comes from the transcript tail, the effort from
  the hook input. **Why (`eta-probes-2.1.325` T01–T04; `eta-calibrate-0.5.0` E09; product review, 2026-11-16):** no
  hook input names the model; PostToolUse follows every edit route and reports the tool's duration; parallel hook
  processes and a user's thinking time must not become an item's time.
- Prediction = estimate × the shipped factor for the model family and category (`eta-baseline.json`, family keys only —
  no versioned model id) × the project factor from `timings.jsonl`, shrunk toward 1 with weight 3. The agent never
  reads its record to estimate. **Why (analyze D17):** one correction path; the agent correcting itself as well would
  be corrected twice.
- The recorder and the prediction fail open like the guards: a broken state or record means no row and no ETA, never
  a changed guard decision; the stop decision is printed and flushed before the clock is fed, and a hook input of the
  wrong type (a `transcript_path` that is not a string) is ignored. **Why (product review, 2026-11-16):** an integer
  path once closed stdout and dropped a block whose counter was already on disk.
- `FREE_HANDS_ROLE` disables the guard in panel children so their work cannot change the main goal or its counter. **Why (FH-04):** Codex panel children load the same plugin hooks in the same repository; without it a child's Stop hook would raise the parent's counter and keep the child from finishing.
- Keep the hard limits in `skills/run/SKILL.md` and its restore note as rules for the agent: no PR merge or merge into the default branch, irreversible deletion, deployment, publication, or external sending. A blocked item is marked as needing the user and skipped while the run continues. **Why (maintainer decision, 2026-10-01; FH-26):** these boundaries preserve decisions for the user.
- The shell hook (`guard.py shell`, `scripts/shellguard.py`) is a backstop with a fixed list, on while the goal is guarded (not tied to open items or `max_iterations`): merges into the default branch, remote deletions, deploy/publish/send. `rm` and database commands, heredoc bodies, scripts, interactive input and other CLIs are deliberately not read (user, 2026-10-02: core scope). A command that names a covered tool but does not parse is denied; any other failure lets the command run. It is built for a cooperative agent's ordinary commands, not against deliberate evasion (the rules forbid that). GitHub issues, PRs and comments are allowed (user, 2026-10-02). **Why:** the rules stay the contract; the hook catches the common commands without stalling normal work. Extend the list only with a case in `SHELL_CASES` (tests/test_free_hands.py) for the new deny and its near misses.
- The panel advises; it never turns a failed check into a pass. Fix a failing check or mark the item as needing the user. Never forge approval, bypass a gate, or claim an unrun check passed. **Why (FH-14):** a panel recommendation cannot change the observed result of a check or authorize bypassing its gate.
- Keep script commands only in `skills/run/SKILL.md`. Reference files may explain a route, but must not introduce commands that depend on an unexpanded `CLAUDE_PLUGIN_ROOT` (root Rule 1). **Why:** Claude expands the variable in skill content, but not in later-read reference files.
- Resolve the newest model of each role's family with `scripts/latest-model.py` immediately before every dispatch and retry. Keep this file byte-identical to the copies in the other plugins; do not write versioned model IDs in plugin files. **Why (D9/FH-10):** an alias redirect or a stale catalog would silently run an older model; `tests/test_compatibility.py` checks that the copies are identical.

## Versioning

Use SemVer for this plugin: MAJOR for a breaking goal-file format or command change; MINOR when a rule, role, or hook behavior is added or changed; PATCH for documentation changes. **Why (root Rule 2):** installed copies are version-keyed, so changes must be classified and released consistently.

## Evidence

0.5.0 expected finish (Claude Code only; Codex not measured, maintainer request 2026-11-16): z-lab
`free-hands-lab/eta-probes-2.1.325` T01–T06 and `-r2`…`-r4` T07–T11 (hook inputs, edit routes, isolation, a blocked
Stop never ends the turn); `eta-calibrate-0.5.0` E01–E09 (recorder = witness; agents overestimate 5–12×; family
factors, post-hoc better than category factors); `eta-validate-0.5.0` + `eta-validate-r2-0.5.0` W01–W04 (held-out
3.17 → 0.62 doublings; the project factor mixed); `dashboard-lab/run-0.3.0` D09–D11 (the band per item, mid-turn).
Decisions D14–D21 and items 14–18 in `free-hands-lab/analyze/improvement-backlog.md`; review fixes unit-tested
only (`EtaTest`).

0.4.0 budget exception and status: z-lab `budget-lab/run-0.1.0` R04, R07, `run-0.1.0-r2` R12; `dashboard-lab/run-0.1.0`
D01, D04; unit tests in `GuardTest`.

0.3.0 session ownership: z-lab `free-hands-lab/session-id-0.3.0` S01–S05 (the hosts' session ids) and
`free-hands-lab/run-0.3.0` O01–O06 (0.2.0 control reproduced the report; another session left alone; owner and its
subagent still denied; the skill writes and replaces `owner:`); unit tests in `GuardTest`.

0.2.0 shell hook: z-lab `free-hands-lab/run-0.2.0` P01–P04 (denied before running on both hosts; allowed command and
controls ran), P05 (the rules alone kept the limits in the full skill); the list in `SHELL_CASES`.

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
