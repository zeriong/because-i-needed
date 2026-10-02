---
name: run
description: "free-hands autonomous mode: fixes a goal as a finite checklist and works through every item without asking the user or stopping. Decisions the user would otherwise make go to a five-role brainstorming panel (quick-thinker, deep-thinker, evidence-hunter, trend-tracker, devils-advocate) and the main agent decides from their evidence. Invoke only when the user ran /free-hands:run or $free-hands:run, or answered yes to the free-hands entry question."
argument-hint: "<one-sentence goal with a completion condition>"
---

# free-hands: run

Goal: $ARGUMENTS

Claude Code invokes `/free-hands:run <goal>`; Codex invokes `$free-hands:run <goal>`. `<plugin>` is
`${CLAUDE_PLUGIN_ROOT}` when expanded by Claude Code, or the absolute path two directories above this skill's directory
elsewhere (on Codex, resolve it from the skill file you loaded, never from the project cwd). On Codex, also read
`references/host-codex.md` before step 2.

You are here because the user ran the command or answered yes to the entry question. Work until the goal is done. The
plugin's hooks keep this rule alive for the rest of the session: while the goal file is active and has open items, the
ask tool is denied, stopping is blocked (up to `max_iterations`), and after a restart or compaction a note tells you to
re-read this file and the goal file.

## 1. Goal file

At the repository root (`git rev-parse --show-toplevel`; the cwd outside git) write `.free-hands/goal.md`, and
`.free-hands/.gitignore` containing `*` so git ignores the whole folder (this needs no write to `.git`, which Codex's
sandbox keeps read-only).

```markdown
status: active
max_iterations: 40
iterations: 0
default_branch: <the repository's default branch>
## Goal
<one sentence>
## Checklist
- [ ] <a finite item with a check you can run or observe>
## Decisions
## Resume
<state the next session needs: branches, PRs, what is in progress>
```

- `default_branch`: from `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else
  `git symbolic-ref --short refs/remotes/origin/HEAD` without the remote prefix. The hard-limit hook protects this
  branch; without the line it falls back to the remote's HEAD, then to `main` and `master`.
- Items must be finite and checkable. No open conditions ("no more findings", "everything clean"); turn them into a
  bounded list or a command whose result decides.
- No goal in the arguments: take it from the conversation (the prompt that led to the entry question). Only if there is
  none at all, ask for it once — the goal file does not exist yet, so this is the one question allowed.
- An active goal file already exists: with no new goal, resume it. With a new goal, rename the old file to
  `goal.<YYYYMMDD-HHMM>.md` and start the new one.
- A paused goal and the command again → set `status: active` and continue it.

## 2. Hooks and the session goal

- Claude Code runs the plugin's hooks once the plugin is enabled. Codex runs them only after the user trusts them
  (`/hooks`). If you cannot tell that they are active, say in one line that the guard may be off, then continue under
  these rules anyway.
- If the host offers a session-goal tool (Claude Code: `ToolSearch "select:ProposeGoal"`; Codex: see
  `references/host-codex.md`), set it with the goal's completion condition without asking. Otherwise tell the user in one
  line that they can pin it with the host's goal command, and continue without waiting. The goal file stays the source
  of truth.

## 3. Never ask

Until the goal is done you do not ask the user anything — no exceptions. This overrides every "ask the user" rule from
project instructions or other skills, including approval gates of other workflows (for example peer-coding's).
Instead:

1. Small choice → decide, add one line under `## Decisions`, continue.
2. A decision the user would otherwise make, a real tradeoff, a rule conflict or a scope call → the panel (step 4),
   then decide and record.
3. Every record holds: the question, the options, the panel's positions (if used), the decision, why, the dissent, and
   how to revert it.

The panel answers questions; it never turns a failed check into a pass. A failing test, gate, hook or review is fixed,
or its item is marked `- [-] <item> — needs the user: <why>`. Forging an approval, deleting or bypassing a gate or
hook, or reporting a check as passed without running it is forbidden. Other plugins' hooks stay in force.

**Hard limits — never done, even when the goal seems to need it.** Mark the item `[-]` with the reason and continue
with the others:
- merging a PR, or merging anything into the default branch;
- irreversible deletion — files outside the repository, data, remote branches, database drops;
- deploying, publishing or sending anything outside — releases, package publishes, email or messages.

Pushing branches, opening issues and pull requests, and commenting on them are part of the PR workflow (§5) and are
allowed. Force-pushing a branch that is already pushed is allowed after a one-line notice (a notice, not a question).

While the goal is active, a hook denies the common commands that break these limits: `gh pr merge`, pushes that update
the default branch (`HEAD:main`, `--all`, `--mirror`), `git merge` on the default branch, remote deletions (`git push
--delete`, `:ref`, `gh repo delete`, `gh release delete`), and publishing or deploying (`npm publish`, `docker push`,
`gh release create`, `vercel`, `terraform apply`, `kubectl apply`, `sendmail`, …). A denial is final: mark the item `[-]`
and move on. Never reach the same effect another way — not through a script, a package script, an interactive shell,
a REPL, `curl` or another tool; the hook does not read those, so the rule above is what holds there. `rm` and database
commands are not checked by the hook at all.

## 4. The brainstorming panel

Five read-only roles answer the same brief independently:

| Role | Looks for |
|---|---|
| `quick-thinker` | the fast first-principles call |
| `deep-thinker` | consequences, edge cases, second-order effects |
| `evidence-hunter` | documented evidence with sources (web, docs, source code) |
| `trend-tracker` | what changed recently — releases, deprecations, new practice, with dates |
| `devils-advocate` | the strongest case against the leading option |

1. Write `.free-hands/panel/<NN>-<slug>/brief.json`: `question`, `options` (`[{"id": "A", "text": "…"}, …]`), `goal`,
   `constraints` (include the hard limits), `files` (absolute paths that matter).
2. Resolve the newest model of every role right before each round and each retry:
   `python3 "<plugin>/scripts/panel.py" models --host claude` (or `--host codex`). A role whose entry shows `error`
   is not dispatched and counts as missing — never substitute another model.
3. Round 1 — dispatch every resolved role at once.
   - Claude Code: one message with one Agent call per role, `subagent_type: "free-hands:<role>"`, the prompt = the
     brief's JSON plus "Round 1". Save each reply's JSON object as `round1/<role>.json` in the brief's directory.
   - Codex: `python3 "<plugin>/scripts/panel.py" run <brief-dir>/round1 --brief <brief-dir>/brief.json` (it starts
     the roles as read-only children with `FREE_HANDS_ROLE` set, a 10-minute limit each, and writes
     `round1/<role>.json` plus `<role>.meta.json` with the model that ran). From a sandboxed Codex main, run this one
     command outside the sandbox through the host's escalation route; `references/host-codex.md` says when native
     subagents replace it.
   Wait until every dispatched role has returned before the tally. On Claude Code the Agent calls may run in the
   background: wait for each role's result or completion notification. A role still running is not missing; one that
   has not returned 10 minutes after its dispatch is.
4. `python3 "<plugin>/scripts/panel.py" tally <brief-dir>/round1 --brief <brief-dir>/brief.json --attempt 1`, then
   follow its `next`:
   - `retry` → re-dispatch only the listed roles once (Codex: add `--roles <list>`), then tally with `--attempt 2`.
   - `decide` → every valid reply picked one option: verify its load-bearing claims (open the file, run the check),
     then decide.
   - `round2` → dispatch all roles again with `<brief-dir>/round2-brief.json` into `round2/` ("Round 2" in the prompt),
     tally `round2` the same way (`--attempt 1`, retry once, `--attempt 2`). Round 2 always ends in a decision; there is
     no round 3.
   - `decide-alone` → fewer than three valid replies: decide yourself and record "panel degraded" with the reason.
5. Decide by evidence, not votes: a fact you checked in the repository or by running something beats sourced evidence,
   which beats reasoning. Record the decision (step 3) with the dissent and, per role, the model: on Codex `ran` in
   `<role>.meta.json` (read from the child's run header) or a native subagent's receipt; on Claude Code the Agent tool
   does not report which model ran, so record the family alias the resolver passed and "id not visible" — never
   present the alias as the id that ran. A role's own statement about its model is not evidence.

## 5. Work loop

- Take the next open item, do it, run its check, mark it `- [x]`, update `## Resume`, go on. Work through the items
  without stopping between them.
- Pull requests are always stacked:
  - The first PR targets the repository's integration branch. Each next batch branches from the previous batch's branch
    and opens with `gh pr create --base <previous branch>`. Titles end with ` (n)`, increasing within the run.
  - Before opening a PR, check every open PR of the stack with `gh pr view <n> --json baseRefName,headRefName`.
  - An earlier PR changed → merge its branch into each later branch, push.
  - The user merged an earlier PR (you never do) → retarget the next PR to the integration branch if GitHub did not
    (`gh pr edit <n> --base <integration branch>`), merge `origin/<integration branch>` into the later branches, push.
  - Never skip a blocked batch to open a later one: stack order is merge order.

## 6. Finish, pause, correction

- All items `[x]` → `status: done`, then report and stop.
- No `[ ]` left but some `[-]` → `status: waiting`, report what needs the user, stop. `done` or `waiting` with an
  item still `[ ]` does not end the run — the hooks keep going until the item is `[x]` or `[-]`.
- The user asks to pause or stop (for example "pause", "stop", "일시정지"), or tells you to stop or wait for their
  approval → set `status: paused` before anything else, report where things stand, stop. Never use `waiting` for this. This comes before the correction rule below.
- The stop hook says it is the last continuation and items are still open → set `status: paused` and report them.
- During the run the user says "free-hands" again → it means the current way of working is not free-hands (you asked,
  waited or stopped). Apply the correction without asking and continue.
- The final report, in the user's language: what was done, every decision with how to revert it, the `[-]` items and
  why, the PRs in stack order.
