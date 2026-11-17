# Changelog

## [0.7.0] - 2026-11-17

### Changed

- When the item in progress has run past its prediction (overrun s = elapsed / prediction), the expected finish counts
  half its elapsed time again for it and scales the later items by √s, so it moves while the item runs; before, it
  only floored the item's remaining time at 10 % of its prediction and left the rest alone.
- The owner's hooks rewrite `.free-hands/eta-tick` whenever the finish as shown changes, and `status` names it in
  `watch`, so dashboard 0.3.0 redraws while an item overruns.

### Why

The maintainer reported (2026-11-17) that a 12-step goal's finish seemed to cover the first step only. A replay of
their project with 0.6.0 showed every open item was summed, but the factors — fitted on small lab tasks — made the sum
a few times too short for their 15–48 min items (z-lab `free-hands-lab/eta-local-replay-0.7.0` L03, L04); learning
faster from finished items did not help at a goal's start (L01). Using the time the running item has already spent did:
once an item had run twice its prediction, the error of the remaining time fell from 0.79 to 0.28 doublings in the real
project and from 1.03 to 0.59 in the lab (`eta-live-replay-0.7.0` V01; at four times it split on 4–7 moments, V02). The
project's numbers were used without any text (maintainer's choice). Not measured: the correction in a live session
(replay only) and the tick's redraw (the watch mechanism is dashboard-lab `run-0.3.0` D09); a recalibration on larger
tasks is the next experiment.


## [0.6.0] - 2026-11-16

### Changed

- The working agent no longer estimates. SKILL.md, the goal template and the restore note say nothing about
  estimates, so nothing about the expected finish enters the main agent's context.
- When the checklist gains open items without an estimate, the owner session's hook starts `scripts/estimator.py`
  detached (no inherited input or output; the hook returns at once and prints nothing). It runs one headless Claude
  Code session — Haiku, effort low, `--safe-mode` (no hooks, no CLAUDE.md), `--no-session-persistence`, tools Read,
  Glob and Grep — and appends minutes and a category per item to `.free-hands/estimates.jsonl`. Only under Claude Code
  (`CLAUDECODE=1` and the hook's parent is `CLAUDE_PID`; the CLI from `CLAUDE_CODE_EXECPATH` or `PATH`), at most once a minute per goal folder, one at a
  time; an item asked without an answer is not asked again in the run. `FREE_HANDS_ESTIMATOR=off` turns it off. Each
  run is a Claude Code session on the user's account (0.002–0.003 USD measured) that the budget plugin does not see.
- `eta-baseline.json` holds factors per estimator, then per working family: `haiku` (Sonnet 0.040, Opus 0.070, Fable
  0.074, default 0.061) and `self` (0.5.0's, for goals whose items still carry the agent's own `(~6m fix)`). Records
  join an estimate that lands after its item was done. `status` also watches `estimates.jsonl`.
- An item whose text the agent rewrites — often in the edit that checks it — keeps its clock and its estimate: open
  items that vanish pair, in order, with items that appear in the same edit; a leftover is marked gone.

### Why

The maintainer asked that the expected finish never cost the main agent's context: a separate agent takes the work,
updates the dashboard and is discarded, fully isolated from the work (confirmed by question, 2026-11-16: fully
isolated; only when the checklist changes; Haiku).

Evidence (z-lab `free-hands-lab`, Claude Code 2.1.325): `eta-isolated-probes-2.1.325` I01, I03–I05 (a detached child
does not hold the hook, leaves the stream empty, outlives the session; safe mode loads no hook; no transcript; the
estimate on disk 4.5 s after the hook) and `-r3` I06, I07 (from a clean environment a hook gets `CLAUDECODE=1`, not
`CLAUDE_CODE_EXECPATH`; the CLI is on `PATH` — round 1's I02 had read an inherited value, corrected);
`eta-haiku-calibrate-0.6.0` H01–H05 (78 estimator runs, no error, 6 s median; on held-out goals Haiku × factor came
within 0.68 doublings per item against 0.62 for the agents' own estimates — the isolation costs a little accuracy);
`eta-isolated-run-r2-0.6.0` J01–J05 (two Sonnet runs: no estimate text reached the main agent; the
estimator answered about 6 s after the checklist; the band showed the finish 2 s after the prompt and per item; a
rewording defect found there is fixed, checked by unit tests and a replay of the recorded run only; round 1,
`eta-isolated-run-0.6.0`, stopped because the estimator then required `CLAUDE_CODE_EXECPATH`). Not measured: Codex (no estimator is started there), Haiku as the working model, other efforts.


## [0.5.0] - 2026-11-16

### Added

- Expected finish. The agent ends every checklist item with its own estimate, `(~<minutes>m <category>)`. A new
  PostToolUse hook and the existing prompt, session and stop hooks of the owner session keep an active-time clock
  (`.free-hands/eta.json`) and append one row per finished item to `.free-hands/timings.jsonl`, the project's own
  record. `guard.py status` adds `ETA <clock>` and `~<n>m left` while the goal is active, and names the goal file in
  `watch` so dashboard 0.3.0 redraws when an item is checked.
- The prediction is estimate × a measured factor per model family (`scripts/eta-baseline.json`: Sonnet 0.080, Opus
  0.126, Fable 0.197; 0.125 for a family without one) × a project factor learned from `timings.jsonl`.

### Why

The maintainer asked for an expected completion time on the dashboard that stays as close as possible to the real one,
per model and per project (2026-11-16). Agents' own estimates were 5–12× too long on average per model family, and
too long in every category and project measured, so the estimates are kept but corrected.

Evidence (z-lab `free-hands-lab`, Claude Code 2.1.325): `eta-probes-2.1.325` T01–T06 (no hook input names the model;
PostToolUse sees every edit route; isolation), `eta-probes-r3`/`-r4` T08–T11 (a blocked Stop never ends the turn);
`eta-calibrate-0.5.0` E01–E09 (13 runs: the recorder matched an independent witness within 0.1 min per run; actual /
estimate 0.08 Sonnet, 0.13 Opus, 0.20 Fable; one factor per family cut the held-out median error from 3.3 to 0.5
doublings, category factors only to 0.74); `eta-validate-0.5.0` with `eta-validate-r2-0.5.0` W01–W04 (78 items of
held-out goals: raw 3.17 → 0.62 doublings with the family factor, 0.70 with category factors; the remaining time
shown at a goal's start within 1.42× on median, 12 of 13 goals within 2×; the project factor helped Sonnet and hurt
Opus, so no gain is claimed for it). Fixes from the product review after validation (repeated item texts, a paused
goal, the time before a typed prompt — a prompt made only of task notifications still counts —, input types, a
stale checklist under the lock, broken values, a next goal sharing one item) are unit-tested only
(`EtaTest`; backlog item 17). The project factor and the default for unmeasured
families are decisions (`analyze/improvement-backlog.md` D17, D20). Not measured: Codex, Haiku, effort levels other
than xhigh, interactive sessions beyond the dashboard case (`dashboard-lab/run-0.3.0` D09, D11).

## [0.4.1] - 2026-10-16

### Changed

- `dashboard.json` declares the icon `🙌` that dashboard 0.2.0 shows before the label. Nothing else changes.

### Why

Delivery release: installed copies need the new declaration for dashboard 0.2.0 to show the icon (evidence: z-lab
`dashboard-lab/run-0.2.0` D06–D08).

## [0.4.0] - 2026-10-14

### Changed

- While the budget plugin's usage question is open for the session, the ask and stop guards stand aside (the shell
  guard stays). SKILL.md and the restore note name it as the one exception to never-ask.

### Added

- `guard.py status` and `dashboard.json`: the goal's state (`active 3/40 · 2 open`, `paused`, `off`) shows on the
  dashboard plugin (root Rule 11).

### Why

With a goal running, free-hands 0.3.0 blocked budget's question on Claude Code and kept a gated Codex turn going until
`max_iterations`. Spending past the user's threshold is the user's decision (maintainer decision, 2026-10-14).

Evidence: z-lab `budget-lab/run-0.1.0` R04 (Claude: the dialog shown with a goal running), R07 (Codex: the gated turn
ended at once, `iterations` unchanged), `run-0.1.0-r2` R12; before: `plugin-platform-lab/mod-interactive-2.1.299` I05,
`budget-lab/codex-gate-0.1.0` B03. Status: `dashboard-lab/run-0.1.0` D01, D04.

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
