<p align="center"><strong>free-hands</strong></p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>.</p>

<p align="center"><strong>Give an agent a finite goal; it works through the checklist without asking or stopping.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.6.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#start">Start</a> &bull; <a href="#goal-file">Goal file</a> &bull; <a href="#expected-finish">Expected finish</a> &bull; <a href="#never-ask">Never ask</a> &bull; <a href="#hooks">Hooks</a> &bull; <a href="#the-panel">The panel</a> &bull; <a href="#stacked-prs">Stacked PRs</a> &bull; <a href="#limits-and-status">Limits and status</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#requirements">Requirements</a> &bull; <a href="#installation">Installation</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub>Part of <a href="../../README.md">because-i-needed</a></sub></p>

---

free-hands fixes your goal as a finite, checkable list, then works through every open item without asking you or stopping. When it reaches a decision you would otherwise make, five read-only panel roles advise; the main agent decides from evidence and records the decision, dissent, and how to revert it.

## Start

- Claude Code: `/free-hands:run <goal>`
- Codex: `$free-hands:run <goal>`
- Or include the word **free-hands** in a prompt. The first response is one entry question in your language. Answer yes to start the skill with that goal; answer no to get possible directions and end that turn. A mention that explains or quotes the name is not a request. While a goal is active in this session, saying “free-hands” again is a correction signal and does not ask for confirmation.

## Goal file

At the repository root, free-hands keeps `.free-hands/goal.md` and a `.free-hands/.gitignore` (`*`) so Git ignores the folder without touching `.git`. The file records one goal, its finite checklist, decisions, and resume notes:

```markdown
status: active
max_iterations: 40
iterations: 0
owner: <session id>
## Goal
<one sentence>
## Checklist
- [ ] <a finite item with a check you can run or observe>
## Decisions
## Resume
<what the next session needs to know>
```

Marks are `- [ ]` open, `- [x]` done, and `- [-] … — needs the user` for work that cannot proceed under a hard limit or another blocker. Status is `active`, `done`, `waiting`, or `paused`. Only open `[ ]` items keep the ask and stop guards engaged, and `done` or `waiting` does not end the run while any `[ ]` item is left. When every item is done, the agent records `done`; when only items needing the user remain, it records `waiting`. At `max_iterations` (40), the restore note tells the agent to set `paused`, report the open items, and stop; asking is allowed again.

`owner:` is the session the goal belongs to. The agent writes it from a hook note when it starts or resumes a run; see [Hooks](#hooks).

## Expected finish

The agent working on the goal never estimates and never sees an estimate. When the checklist gains items without one, the hook of the session that owns the goal starts a separate, short-lived estimator in the background: a headless Claude Code session on Haiku in safe mode (no hooks, no plugin hooks, no CLAUDE.md, read-only tools, no saved session). It reads the code it needs, writes one line per item — minutes and a category (`docs`, `fix`, `feature`, `refactor`, `test`, `research`, `ops`) — to `.free-hands/estimates.jsonl`, and exits. The hook returns at once and prints nothing, so none of this enters the agent's context. Set `FREE_HANDS_ESTIMATOR=off` to turn the estimator off.

From then on the hooks of the owner session time each item:

- An active-time clock in `.free-hands/eta.json`. Time after a turn that ended, before a new session, before a prompt you type, or while the goal is paused does not count; a quiet gap over 20 minutes counts only as long as a tool call reports it ran.
- One row per finished item in `.free-hands/timings.jsonl`: the item, the measured minutes, the model and the effort; the estimate is joined from `estimates.jsonl`, also when it arrived after the item was done. This is your project's own record. It stays in the project folder, Git ignores it, and it is kept when a new goal starts.

The [dashboard](../dashboard) shows the expected finish as a clock time, `ETA 15:40`, with the minutes left in the detail (`~25m left`); a `+` after the time means some open items have no estimate yet. With dashboard 0.3.0 the line changes when an item is checked or when estimates arrive, also in the middle of a turn.

The expected finish adds up, over the open items, the estimate × a factor for the model family doing the work × a factor for this project:

- **Model factor**, measured in z-lab. Haiku's estimates were far longer than the work took: the items took 0.040 of Haiku's estimate when Sonnet did them, 0.070 with Opus and 0.074 with Fable — the shipped factors ([`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0), 26 measured goal runs at effort xhigh). A working model without a measured factor (Haiku, Codex's models) uses their mean, 0.061 — a choice, not a measurement. Goals written by 0.5.0, whose items still carry the agent's own `(~6m fix)`, keep 0.5.0's factors for those estimates.
- **Project factor**: how much longer or shorter this project's items took than the model factor predicted, learned from the newest 60 rows of `timings.jsonl` and pulled toward 1 while the record is short. A new project starts at 1.

## Never ask

The skill does not ask the user during an active goal. This overrides project and other skill instructions to ask, including approval gates in workflows such as peer-coding. The agent pushes branches and creates PRs without asking. A failed test, gate, hook, or review is fixed or marked `- [-]` as needing the user; it is never reported as passed. Other plugins’ hooks continue to run.

The one exception is the [budget](../budget) plugin's usage question: when budget stops a call because your usage threshold is reached, the agent does what it says — in Claude Code's dialog, or on Codex by ending the turn with the question. Spending past your threshold is your decision, not the panel's.

## Hooks

The hooks have different conditions:

- The guards and the restore note below act only in the session named by `owner:` and in the subagents it starts. Another session in the same repository — a second terminal, or a `claude -p` that another tool starts — gets no restore note, no ask or stop guard, no counter and no shell guard; when its prompt mentions “free-hands”, the entry note says which session owns the run. Running `/free-hands:run` (Codex: `$free-hands:run`) in that session moves the run there. A goal without `owner:`, such as one written by 0.2.0, becomes the first session's that a hook sees.
- Only `- [ ]` lines under `## Checklist`, outside code blocks, count as open items.
- The clock of the [expected finish](#expected-finish) (`PostToolUse` on every tool, plus the prompt, session and stop hooks) runs only in the owner session and its subagents, like the guards; panel children never feed it. It also records the edit that checks the last item and ends the run. The same hooks start the estimator, at most once a minute, only under Claude Code.
- The shell guard (`PreToolUse` on `Bash`) acts while the goal is `active`, or `done`/`waiting` with items still open — also when no `[ ]` item is left and at `max_iterations`. It denies the hard-limit commands described under [Limits and status](#limits-and-status).
- The ask and stop guards act when the goal has open `[ ]` items, is below `max_iterations`, and is `active` — or `done`/`waiting` with items still open. The ask guard denies asking tools. At the limit, asking is allowed. The Stop hook blocks stopping and increments the counter on disk first, up to 40 continuations. While budget's usage question is open in the session, neither guard acts.
- The restore note (`UserPromptSubmit`, and `SessionStart` including after a compaction) is emitted while the goal is `active` (also when no `[ ]` items remain) or `done`/`waiting` with items still open.
- The entry note is emitted when there is no active, well-formed goal and a prompt mentions “free-hands”. Background-task notifications are not treated as prompts; a notification quoted inside a prompt is ignored and the rest of the prompt is read.

Malformed hook input has no effect. A malformed or unreadable goal does not activate the restore, ask, or stop behavior; on a prompt containing “free-hands”, the prompt hook follows the no-active-goal entry route and may emit the entry question. Failed writes and lock timeouts also have no effect, so a hook failure lets the tool or stop proceed. A broken `eta.json` or `timings.jsonl` means no record and no expected finish; it never changes what a guard decides.

## The panel

The five roles read the same brief independently in round 1; the main agent waits for every dispatched role before tallying. Round 2 runs only when round 1 disagrees. A missing or invalid reply is retried once; fewer than three valid replies means **panel degraded**, and the main agent decides alone. A role whose latest model cannot be resolved is skipped and counted as missing; no substitute model is used. In Claude Code, an `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` redirect makes roles in that family unavailable. The main agent verifies load-bearing claims and decides by evidence, not votes: checked facts, then sourced evidence, then reasoning. The record includes each position, dissent, decision, and how to revert it.

| Role | Focus | Claude model family |
|---|---|---|
| `quick-thinker` | Fast first-principles call | `sonnet` |
| `deep-thinker` | Consequences, edge cases, second-order effects | `opus` |
| `evidence-hunter` | Documentation and source evidence | `sonnet` |
| `trend-tracker` | Recent changes, with dates | `sonnet` |
| `devils-advocate` | Strongest case against the leading option | `opus` |

Each role uses the newest available model in its family. On Claude Code, record the family alias passed by the resolver and “id not visible”; the Agent tool does not show the model ID that ran. On Codex, record the model reported by the child run instead.

## Stacked PRs

Every PR title ends in ` (n)`, increasing through the run. The first PR targets the repository's integration branch; each later PR is based on the previous branch. The user merges PRs in stack order; after an earlier PR is merged, the agent retargets the next PR to the integration branch when needed, then merges `origin/<integration>` into each later branch and pushes it. A blocked batch is not skipped, so stack order is merge order.

## Limits and status

The panel deciding better than one agent is a **hypothesis, not a measured result**. What was measured, once per case, on Claude Code 2.1.286–2.1.287 and Codex 0.159.3–0.160.0 ([z-lab `free-hands-lab`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab): `run-0.1.0`, `run-0.1.0-r2`):

- The hooks inject the restore note at session start, on every prompt and after a compaction (F01, F04, G02). On Claude Code the stop guard blocks while items are open and counts on disk (F02); on Codex one block is evidenced, because Codex prints no hook events (F04).
- The entry question, its yes and no answers, and an explanatory mention behave as described on both hosts, except that Codex asked the question in English to a Korean prompt and answered “no” with a plain acknowledgement instead of directions (F06).
- A stop request ends as `paused`; an item that needs the user ends as `[-]` with `waiting` (G01, G03).
- Panel children started with `FREE_HANDS_ROLE` leave the parent's goal alone (F05).
- The five roles run on their families' newest models and return valid replies on both hosts; the Claude main waits for all five (F08, F09, G04).

Not measured: the denial of `AskUserQuestion` (headless Claude Code has no such tool) and of Codex's `request_user_input` (the agent never called it); the release at `max_iterations` and a failed counter write at runtime (unit tests only); round 2 (every panel agreed); a role's write attempt being blocked (none tried); interactive `/hooks` trust; stacked PRs. Agents rewrote `iterations` themselves in four runs (F04, G03), so the limit holds only while the agent leaves the counter alone.

The skill and restore note give the agent these hard limits:

- Never merge a PR or merge anything into the default branch.
- Never irreversibly delete files outside the repository, data, remote branches, or databases.
- Never deploy, publish, or send anything outside (such as a release, package, email, or message).

Mark such checklist items `- [-]` with the reason and continue with other items. Force-pushing a branch that was already pushed is allowed after a one-line notice. Pushing branches, opening issues and PRs, and commenting on them are allowed.

Since 0.2.0 a shell hook also denies the ordinary commands that break them while a goal is active: `gh pr merge`; pushes and merges that update the default branch (`default_branch:` in the goal file, else the push remote's HEAD, else `main` and `master`); `gh api` merges and release creation; remote deletions (`git push --delete`, `:ref`, `--prune`, `--mirror`, `gh repo delete`, `gh release delete`); and `npm`/`pnpm`/`yarn publish`, `cargo publish`, `twine upload`, `gem push`, `docker push`, `docker buildx build --push`, `gh release create`, `vercel` deploys, `netlify deploy`, `fly deploy`, `firebase deploy`, `terraform apply`, `kubectl apply`, `helm install`/`upgrade`, `sendmail`, `mail` and `mutt`. `--help`/`-h` passes for every listed CLI except `sendmail`, `mail` and `mutt`, which are always denied, and `terraform`, whose help flag is `-help`; `--dry-run` passes for `git push`, `npm`/`pnpm`/`yarn publish`, `cargo publish`, `kubectl` and `helm`. On both hosts the hook denied `gh pr merge 1`, `npm publish` and `git push origin HEAD:main` before they ran, and the denial reached the agent ([z-lab `run-0.2.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.2.0), P01–P04).

The hook is a backstop for a cooperative agent's ordinary commands, not a defense against deliberate evasion — the rules forbid evasion. It does not read `rm`, database commands, heredoc bodies, scripts (`npm run deploy`), commands typed into an interactive session, or other CLIs and HTTP calls (`curl`).

Since 0.3.0 a goal belongs to one session. Measured once per case on Claude Code 2.1.296 and Codex 0.162.1 ([z-lab `run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/run-0.3.0)): under 0.2.0 a second session in the same repository was handed the running goal and worked on it (O01); under 0.3.0 it was left alone and the goal file stayed byte-identical (O02); `gh pr merge 1` was still denied in the owner session and in its subagent, and ran in another session (O03–O05); the skill wrote `owner:` from the hook's note when it started a run and replaced it when it took one over (O06). Both hosts send the session id with every hook event and keep it across resume and compaction ([`session-id-0.3.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/session-id-0.3.0), S01–S03). Not measured: two sessions running at the same moment.

Since 0.4.0 the [budget](../budget) question gets through, and the goal shows on the [dashboard](../dashboard). On Claude Code 2.1.299 and Codex 0.162.1 ([z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab), [`dashboard-lab`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab)): with a goal running, budget's dialog was shown, which 0.3.0 had blocked; on Codex the gated turn ended at once, while 0.3.0's stop guard kept it going three more times (budget-lab R04, R07, R12; codex-gate B03). `guard.py status` gave the dashboard `active 0/40 · 1 open` on both hosts (dashboard-lab D01, D04).

Since 0.5.0 the goal shows an expected finish. Measured on Claude Code 2.1.325 with Sonnet, Opus and Fable at effort xhigh, on three projects of different size ([z-lab `eta-calibrate-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-calibrate-0.5.0), [`eta-validate-r2-0.5.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-validate-r2-0.5.0)): the hooks' times matched an independent log within 0.1 minute in every run (E01). On goals the factors were not fitted on, the model factor brought the median error from 3.2 doublings — the raw estimates were about 9× too long — to 0.6, about 1.5× (W01). The remaining time shown when a checklist was written was within 1.42× of what the goal took on median, and within 2× for 12 of 13 goals (W04). The project factor helped Sonnet and hurt Opus in these runs (W03), so no gain from it is claimed. The dashboard line changed after each finished item, mid-turn ([`dashboard-lab/run-0.3.0`](https://github.com/zeriong/z-lab/tree/main/dashboard-lab/run-0.3.0), D09). Not measured: Codex, Haiku, other effort levels, projects with a longer record.

Since 0.6.0 the estimate comes from that isolated estimator. Measured on Claude Code 2.1.325 in two headless free-hands runs with Sonnet and one interactive session ([z-lab `eta-isolated-run-r2-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-isolated-run-r2-0.6.0)): nothing about estimates appeared in the working agent's stream, and every free-hands hook output was empty of it (J01); the estimator answered about 6 seconds after the checklist was written, logged no error and kept no session (J02); the line showed `ETA` 2 seconds after the prompt and moved with each finished item (J04). One estimator run cost 0.002–0.003 USD. On goals its factors were not fitted on, Haiku × factor came within 0.68 doublings per item and 0.66 per goal (median), against 0.62 and 0.51 for the agents' own estimates in 0.5.0 — keeping estimates out of the agent's context costs a little accuracy ([`eta-haiku-calibrate-0.6.0`](https://github.com/zeriong/z-lab/tree/main/free-hands-lab/eta-haiku-calibrate-0.6.0), H04, H05). An agent that rewrites an item's text while checking it is matched by position; that fix was checked by replaying a recorded run, not in a new one (J05).

To pause, say **“pause”**, **“stop”**, or **“일시정지”**. The goal is recorded as `paused`; invoke the command again to resume.

Origin: ported from a project-local skill.

## Codex

Trust the plugin hooks in `/hooks` before relying on them. The ask hook matcher includes `request_user_input`; its denial has not been observed. Codex's default mode has no ask tool, so the Stop hook carries the keep-working rule. If hooks are not trusted or active, the skill continues under its written rules, but hook effects may be off. On Codex the hooks still time items, but no estimator is started (it needs the Claude Code CLI the hook runs under), so no expected finish is shown unless the goal was written by 0.5.0 with inline estimates; `$dashboard:audit` shows what there is (Codex has no live line). Not measured on Codex.

The panel runs one `codex exec -s read-only` child per role (native subagents take a model but no read-only control, so they are not used — F10). Children can search the web whatever the role; `--search` is added for `evidence-hunter` and `trend-tracker` (F09). The children need network: from a sandboxed main, `panel.py run` must run outside the sandbox through an approved escalation, or the session must allow network. Otherwise every child fails, and the run continues with the main deciding alone, recorded as **panel degraded** (G06).

## Requirements

- `python3` to run the hooks; it must be available on `PATH`.
- `git` to find the repository root.
- `gh` for the stacked PR workflow.
- Codex CLI (`codex`) for the Codex panel route.

## Installation

First add the marketplace, then install the plugin:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install free-hands@because-i-needed
```

For Codex, follow the [marketplace instructions](../../README.md#codex).

## License

MIT. See [LICENSE](../../LICENSE).
