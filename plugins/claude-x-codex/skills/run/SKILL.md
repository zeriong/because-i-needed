---
name: run
description: "Cross-vendor multi-agent orchestration for coding work. The main agent plans and owns every gate decision, work is routed to fast Claude (Sonnet) or bulk Codex (Luna) workers by task type, and Claude and Codex review each other as peers — including the main agent's own plan and triage decisions, with a rebuttal round when findings are rejected. Runs from either Claude Code or Codex as the main agent, and uses Orca's orchestration runtime when available (two-way worker communication, gates) or falls back to one-way subagent/CLI calls. Use this skill when the user explicitly asks for it — names it, runs /claude-x-codex:run, or asks to orchestrate, parallelize, fan out, or run agents on a task (\"오케스트레이션으로 진행해줘\") — or when an [claude-x-codex: ON] context note is present and the request is implementation work. When the mode is off and the user hasn't asked for it, do not use this skill."
compatibility: Main agent in Claude Code or Codex. Git worktrees. Optional — the other vendor's CLI (`codex` or `claude`), and Orca (desktop runtime with orchestration enabled).
---

# claude-x-codex: run

Speed lives in the work lanes, quality lives in the gates.

`<plugin>` below means the plugin root: `${CLAUDE_PLUGIN_ROOT}` under Claude Code, or
`../..` from this skill's directory elsewhere. Shared scripts live in `<plugin>/scripts/`.

This file is the **policy**: who does what, how review works, when loops end. How
messages actually move between agents lives in `references/`, because it depends on
where you run. Read this file fully, then load exactly the references that setup tells
you to.

## Mode gate (before anything else)

Orchestration has a one-line on/off switch managed by the `mode` skill of this plugin
(`/claude-x-codex:mode`).

1. **A dispatched worker or reviewer never orchestrates.** If your prompt is a
   delegation or review prompt from this skill (it starts with `# Task <id>` or
   `You are reviewing`), do exactly that task, even if an `[claude-x-codex: ON]` note
   is present. Main starts every CLI worker and reviewer with `CXC_MODE=off` so the
   note never appears there; this rule covers workers that can't take an env var.
2. **Explicit request → always run.** If the user named this skill or asked for
   orchestration in this prompt, skip the flag and continue to Setup.
3. **Otherwise read the flag**: `<plugin>/scripts/mode.sh get` (an `[claude-x-codex: ON]` context note means it's on).
   - **off** → don't orchestrate. Do the task yourself as the single agent in this
     terminal, and don't mention orchestration.
   - **on** → orchestrate implementation work. Handle these directly instead, with a
     one-line note (`orchestration skipped: <reason>`) so the user can force it by
     asking explicitly: questions and explanations, reviews of existing code with no
     changes, and edits small enough that writing a plan would cost more than doing
     them (roughly: one file, a few lines, no design choice).
4. A run already in progress in `.claude-x-codex/<feature>/` is not stopped by switching the
   mode off; it just won't start new runs. Resume it only when the user asks.

## Setup (do this first, every run)

1. **Identify the host** — the product you, the main agent, are running in.
   Claude Code sets `CLAUDECODE=1`; if unsure, you know which vendor's model you are.
   Load `references/host-claude-code.md` or `references/host-codex.md`.
2. **Identify the transport.** Run `orca status --json`. If it succeeds and
   orchestration is enabled, load `references/transport-orca.md`. Otherwise load
   `references/transport-standalone.md`. Reviews always use the standalone read-only
   calls, even under Orca (transport-orca.md says why), so load both under Orca.
3. **Check the other vendor is reachable** (the host file says how). If it isn't, run
   in **single-vendor mode**: every lane uses your own vendor, and every review is done
   by a separate reviewer instance of your strongest model that sees only the plan and
   the diff. Tell the user this mode is active — it's weaker than cross-vendor review.
4. **Bridge context both ways.** Load `references/context-bridge.md` and run the audit
   (`<plugin>/scripts/context-audit.sh`); save its output to `.claude-x-codex/context-audit.md`.
   If the user already ran `/claude-x-codex:audit` in this repo, reuse that result unless
   the host changed. Fix
   what you can without repo changes (Codex fallback instruction files, context manifest,
   context packs) and collect the rest — pointer files, gate scripts — as proposals for
   the plan-approval step. Rerun the audit when the host differs from the last run.
5. Load `references/templates.md` when you reach the plan step.

## Core principles

1. **Claude and Codex are peers, not a chain of command.** The whole value of this
   skill is that two agents with different foundations cover each other's blind spots.
   Two copies of the same agent can go faster on what it already does well, but they
   share its weaknesses; a different colleague is what raises quality. So critique
   flows in both directions at the same level: each vendor reviews the other's work,
   *including the main agent's own plan and triage decisions*, and a rejected finding
   gets a reply, not silence. Being the main agent means owning the process, not
   outranking the other vendor's judgment.
2. **Evidence decides, not role.** When the two vendors disagree, a test, a
   reproduction, or a concrete trace settles it — whichever side has it wins. If
   neither can produce evidence, the user decides. This keeps peer review from turning
   into an endless debate.
3. **The author and the reviewer are different vendors.** Same-model self-review barely
   changes outcomes; different vendors fail in uncorrelated ways. Claude-authored work
   is reviewed by Codex, Codex-authored work by Claude.
4. **Reviewers report, they never rewrite.** Static reviewers that rewrite working code
   often make it worse. Reviewers run read-only and return findings; the main agent
   verifies each finding against tests before accepting it.
5. **Tests are the cheapest reviewer.** Where a deterministic gate (tests, typecheck,
   lint) can verify a task, don't spend an AI review on it.
6. **Peers share the same ground.** Every agent, of either vendor, main or worker,
   starts from the same project context: the same instructions, the same rules
   enforced, the same knowledge of the codebase. Context flows both ways — nothing
   assumes one vendor is the source of truth and the other a recipient. Where the two
   vendors read different files, bridge them (`references/context-bridge.md`).
7. **Handoffs are where quality leaks.** A worker knows only its delegation prompt, the
   plan file, and the bridged context. Every delegation is self-contained; every
   return is structured.
8. **Every loop has a ceiling.** Loops end on "no blocking findings" or a cycle cap,
   never on "the reviewer is happy".

## Roles, lanes, and routing

Rules below are written relative to vendors, not to a fixed main agent, so they hold
whether Claude Code or Codex is the host. "Main" is always you.

### Main (you)
Requirement interview, planning, task decomposition, every gate decision, triage of
review findings, integration. Run at your host's strongest setting (host file lists
the model). Stay lean: read diffs, gate results, and structured returns — not workers'
exploration logs — so your context stays useful for the whole feature.

### Work lanes

| Lane | Model · effort (default) | Route here when |
|---|---|---|
| `claude-fast` | Claude newest `CXC_CLAUDE_WORKER` (`sonnet`) · `CXC_WORKER_EFFORT` (`high`) | Fast feedback and code taste matter: UI, interaction, styling, design-system work; needs Claude-side tools or MCP servers |
| `codex-bulk` | Codex newest `CXC_WORKER_MODEL` (`luna`) · `CXC_WORKER_EFFORT` (`high`) | The correct result is already fully specified: tests for an existing contract, types, mechanical migrations, repetitive mappings, fixtures, docs from code |
| `main` | you | Tightly coupled cross-layer changes; spec still being discovered; tasks smaller than their delegation prompt |

Splitting coupled work costs more in coordination than it saves in parallelism. When
in doubt between a worker lane and `main`, choose `main`.

### Review routing

The reviewer's vendor must differ from the author's vendor. Every cross-vendor review —
the plan review, phase reviews, and delta re-reviews — uses these reviewers:

| Reviewer vendor | Model (newest of the family) | Effort (default) |
|---|---|---|
| Claude | `CXC_CLAUDE_REVIEWER` (`opus`) | `CXC_REVIEW_EFFORT` (`xhigh`) |
| Codex | `CXC_REVIEW_MODEL` (`sol`) | `CXC_REVIEW_EFFORT` (`xhigh`) |

`xhigh` is the same rung on both CLIs — one below `max` (Codex's `ultra` sits above `max`
and adds task delegation) — so the two reviewers sit on the same rung. Neither CLI
rejects a misspelled level: Claude warns and falls back to its default, Codex passes it
through. Spell it exactly.

- **If your vendor differs from the author's** and you are running as the newest model of
  that table's reviewer family (resolved as below) at the review effort or higher, review
  it yourself. (Claude Code host:
  you review `codex-bulk` work. Codex host: you review `claude-fast` work.) Otherwise
  start your vendor's reviewer as a separate read-only call — being main doesn't make
  your session's model or effort the reviewer's.
- **Otherwise**, start a read-only reviewer from the other vendor, per the table.
- **High-risk phases** (auth, permissions, data integrity, payments, production data
  migrations) use the same reviewers. Never move to a top model or `max` effort on your
  own — an extra final review from the other vendor's top model (Codex newest
  `CXC_FINAL_MODEL`, family `astra`, or Claude newest Opus at `max`) runs only if the user approves it. Ask at plan
  approval for every phase marked `Risk: high`, and again whenever a phase turns out
  high-risk later: with the AskUserQuestion tool on Claude Code, in the conversation on
  other hosts (an Orca gate under Orca). Record the answer in `decisions.md`.

A phase with mixed authors gets one review per author vendor, each scoped to its files.

### Review lenses — use each vendor for what the other misses

Give each reviewer its own lens, so the pair covers more ground than either would
alone. These are starting points drawn from how the two are commonly observed to
differ; adjust them when your own results say otherwise.

- **Codex reviewing Claude's work**: correctness under adversarial input, edge cases,
  error paths, off-by-one and state bugs, whether tests actually exercise the change,
  and places where Claude's fluent code hides an unverified assumption.
- **Claude reviewing Codex's work**: intent and design — does it solve the problem in
  `plan.md` rather than just the literal task, consistency with existing patterns and
  naming, readability and UX coherence, and over-literal implementations that pass
  tests but miss the point.

Both lenses always include blocking correctness issues; the lens adds emphasis, it
doesn't narrow scope.

### Configuration

Read these from the environment, falling back to defaults. A model setting names a
**family**; what runs is always the newest version of that family (next section):

| Variable | Default |
|---|---|
| `CXC_WORKER_MODEL` | `luna` |
| `CXC_REVIEW_MODEL` | `sol` |
| `CXC_FINAL_MODEL` | `astra` |
| `CXC_CLAUDE_WORKER` | `sonnet` |
| `CXC_CLAUDE_REVIEWER` | `opus` |
| `CXC_REVIEW_EFFORT` | `xhigh` |
| `CXC_WORKER_EFFORT` | `high` |
| `CXC_MAX_CYCLES` | `3` |
| `CXC_PARALLEL` | `3` |

`CXC_FINAL_MODEL` is used only for a high-risk final review the user approved.

### Newest model per family

Every dispatch — worker, reviewer, rebuttal, delta re-review — resolves its model right
before it starts, never once per run and never from memory:

```bash
python3 "<plugin>/scripts/latest-model.py" codex "${CXC_REVIEW_MODEL:-sol}" --effort "${CXC_REVIEW_EFFORT:-xhigh}"
python3 "<plugin>/scripts/latest-model.py" claude "${CXC_CLAUDE_WORKER:-sonnet}" --effort "${CXC_WORKER_EFFORT:-high}" --project "<child's working directory>"
```

- Pass stdout as the child's model. A versioned setting (`gpt-<n>-sol`, `claude-opus-<n>`)
  is reduced to its family and resolved to the newest, with a note on stderr: there is no
  pinning exception. Codex's newest is the highest listed `gpt-<version>-<family>` in the
  refreshed `codex debug models` catalog; Claude's is the family alias, which the CLI maps
  to its latest model.
- **Exit 2** (the newest can't be determined: no CLI, catalog not refreshed, no listed model
  in the family, or `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` redirecting the alias) or **exit 3**
  (effort unsupported): don't start that child and don't substitute another model. Show the
  user the script's message and stop the lane. Upgrading or logging in to a CLI is the
  user's step; choosing the newest model the CLI offers is yours.
- A sandboxed shell can't refresh Codex's catalog: once the cache is older than the CLI's
  refresh window, the script stops with `catalog not refreshed` although the newest model
  is obtainable. When your shell runs sandboxed without network (a Codex main agent), rerun
  that one resolver command outside the sandbox through the host's escalation route before
  stopping the lane.
- Record the id that actually ran, taken from the run: the Codex run header `model:`,
  Claude's `modelUsage`, Orca's `launch.effective`. A worker's own report is not evidence.
  Log it in `decisions.md` (dispatch log, review header). A run outside the requested
  family, or older than an id already logged for that family in this feature, is a failed
  dispatch.
- A delta re-review keeps the family and effort; if a newer version appeared since the
  first review, the newer one runs.
- You can't switch your own model. At Setup, resolve your family; if your session runs an
  older version, tell the user once (a new session fixes it) — the lanes still get the newest.

## State on disk

Orchestration state lives in files so it survives compaction and can be resumed.
Even under Orca — whose runtime tracks runs, tasks and workers — keep these, because
Orca records *what happened*, not *why you decided*.

```
.claude-x-codex/<feature>/
├── ../context-audit.md    # latest parity audit (shared by all features)
├── ../context-manifest    # uncommitted context to materialize in worktrees
├── plan.md          # single source of truth
├── decisions.md     # triage log with reasons
├── tasks/<id>.md    # delegation prompts
├── returns/<id>.md  # structured returns
├── reviews/<phase>-r<n>.json
└── cycles           # "<phase> <count>" per line
```

Add `.claude-x-codex/` to the local exclude file resolved by
`git rev-parse --git-path info/exclude` on first use (also works in linked worktrees) so nothing leaks into a shared
repo. Record transport IDs (e.g. Orca run/task IDs) in `plan.md` next to each task.

## Pipeline

### 1. Plan — Gate 1
Interview the user until goal, constraints, and non-goals are clear. If the repo has a
dedicated planning skill, use it and extend its output to the plan template in
`references/templates.md`. Every task gets a lane, a file scope, dependencies, and a
"done when" that a command can check. Tasks that run concurrently touch disjoint files.

**Get the plan reviewed by the other vendor** before showing it to the user. The plan
is your own artifact, so by principle 1 it is reviewed like any other; it's also the
cheapest point to catch a design error. Triage that review the same way as code
reviews (step 6, including the rebuttal round), then revise the plan.

**Stop for the user's approval of the plan** (transport file says how to block), and
show them any plan findings you rejected with your reasons — the user should see
where the two vendors disagreed. In the same step, ask about the extra final review for
each `Risk: high` phase (see Review routing). Parallel work on a wrong plan is the most expensive
failure here.

### 2. Dispatch
Create one isolated worktree per task, then run `<plugin>/scripts/worktree-setup.sh <worktree>`
so uncommitted context (local settings, overrides, knowledge-tool output) is present.
Write each delegation from the template, including its **Project context** section:
the instruction files to read, procedure files to follow, and a context pack you built
from your own tools. Dispatch up to `CXC_PARALLEL` tasks whose dependencies are met —
all ready tasks before waiting on any of them.

### 3. Handle questions while work runs
Under Orca, workers can ask mid-task. Answer from `plan.md` and `decisions.md` when the
answer is there; log new decisions to `decisions.md`. Escalate to the user only when
the answer would change an approved decision or touch shared code the plan didn't
cover. Under standalone transport, workers can't ask — their "Uncertain" section is
where these land, and you resolve them at the task gate.

### 4. Task gate — Gate 2 (light, every task)
1. Run the task's "done when" command and the plan's gate command in its worktree.
   The gate is what holds both vendors to rules that hooks enforce for only one.
2. Check the diff stays inside the declared file scope.
3. Resolve or log every "Uncertain" item.

Pass → merge into the feature branch and unblock dependents. Fail → rework prompt to
the same lane with the raw failing output. Two failures → the task moves to `main`.
Don't read every line of passing work here; that is the phase review's job.

When a phase's tasks are all merged, run the full gate command on the feature branch
and fix integration breaks before review.

### 5. Phase review — Gate 3 (heavy, once per phase)
Route per the review rules. Reviewers get `plan.md`, `decisions.md`, and the phase
diff, and return JSON in the schema from `references/review.schema.json`. Both CLIs
enforce that schema (transport-standalone.md shows the flags); still validate the
file before triage, and if it doesn't parse, re-run once — don't hand-repair reviewer output.

### 6. Triage and rebuttal
Classify every finding as ACCEPT / REJECT / DEFER in `decisions.md`, with a reason.
Accept blocking or major findings only after reproducing them with a test or command —
reviewer claims are hypotheses, and so are your reasons for rejecting them.

**Rejected blocking and major findings go back to the reviewer once.** Send each one
with your reason and any evidence (rebuttal prompt in `templates.md`). The reviewer
either concedes, or counters with new evidence. Then:

- Reviewer concedes → the rejection stands.
- Reviewer counters with evidence you can reproduce → accept the finding.
- Still unresolved → write a test that would distinguish the two positions if one can
  be written; otherwise mark it DISPUTED and bring it to the user with both arguments.

One round only. The point is that the other vendor hears why and can answer, not that
the two argue until one gives up. Minors and nits skip this round.

The rejected list, with the reviewer's reply, is what stops the next review from
re-raising the same point.

### 7. Fix → gate → delta re-review
Route accepted fixes through the normal lanes. Run the full gate; nothing goes to a
reviewer red. Increment `cycles`. Re-review only the fix diff plus the status of
previously accepted findings, with the same reviewers and effort — the smaller diff is
what keeps it cheap.

### 8. Exit
- **Phase done**: no unresolved blocking or major findings; minors are deferred.
- **Escalate to the user** when `cycles` reaches `CXC_MAX_CYCLES`, when a finding is
  DISPUTED after the rebuttal round, or when a fix would change an approved decision.
  Present both vendors' positions with their evidence, side by side and without
  favoring your own, and stop.
- **Finish**: full gate on the feature branch, clean up worktrees, summarize shipped
  work, deferred findings and open uncertainties. **Never merge to the base branch
  yourself** — block for the user's decision (Gate 4).

## Resuming
After a restart or compaction, read `plan.md`, `decisions.md`, and `cycles` first; under
Orca, also query the run's current task and worker state. Files and the runtime are the
state; your memory of the conversation is not.

## Anti-patterns
- Treating the other vendor as a subordinate: rejecting findings without sending
  them back, skipping review of your own plan or code, or summarizing disagreements
  to the user in your own favor.
- Forwarding reviewer findings to workers without triage.
- Heavy review after every task instead of per phase.
- Parallelizing tasks that share files.
- Letting a reviewer write code.
- Moving any agent to a top model or `max` effort without asking the user first.
- Assuming one vendor's context is the default: sending a worker off without the
  instructions, rules, or knowledge the other vendor would have had natively.
- Letting a routing rule silently become same-vendor review after a host change —
  re-check the review rules whenever the host differs from last run.
- Treating this file as enforcement. The review schema is enforced by the CLIs; for
  the other hard guarantees, pair this file with hooks — e.g. one that fails when
  `cycles` exceeds `CXC_MAX_CYCLES`.
