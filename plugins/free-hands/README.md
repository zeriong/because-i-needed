<p align="center"><strong>free-hands</strong></p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>.</p>

<p align="center"><strong>Give an agent a finite goal; it works through the checklist without asking or stopping.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#start">Start</a> &bull; <a href="#goal-file">Goal file</a> &bull; <a href="#never-ask">Never ask</a> &bull; <a href="#hooks">Hooks</a> &bull; <a href="#the-panel">The panel</a> &bull; <a href="#stacked-prs">Stacked PRs</a> &bull; <a href="#limits-and-status">Limits and status</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#requirements">Requirements</a> &bull; <a href="#installation">Installation</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub>Part of <a href="../../README.md">because-i-needed</a></sub></p>

---

free-hands fixes your goal as a finite, checkable list, then works through every open item without asking you or stopping. When it reaches a decision you would otherwise make, five read-only panel roles advise; the main agent decides from evidence and records the decision, dissent, and how to revert it.

## Start

- Claude Code: `/free-hands:run <goal>`
- Codex: `$free-hands:run <goal>`
- Or include the word **free-hands** in a prompt. The first response is one entry question in your language. Answer yes to start the skill with that goal; answer no to get possible directions and end that turn. A mention that explains or quotes the name is not a request. While a goal is active, saying “free-hands” again is a correction signal and does not ask for confirmation.

## Goal file

At the repository root, free-hands keeps `.free-hands/goal.md` and a `.free-hands/.gitignore` (`*`) so Git ignores the folder without touching `.git`. The file records one goal, its finite checklist, decisions, and resume notes:

```markdown
status: active
max_iterations: 40
iterations: 0
## Goal
<one sentence>
## Checklist
- [ ] <a finite item with a check you can run or observe>
## Decisions
## Resume
<what the next session needs to know>
```

Marks are `- [ ]` open, `- [x]` done, and `- [-] … — needs the user` for work that cannot proceed under a hard limit or another blocker. Status is `active`, `done`, `waiting`, or `paused`. Only open `[ ]` items keep the ask and stop guards engaged, and `done` or `waiting` does not end the run while any `[ ]` item is left. When every item is done, the agent records `done`; when only items needing the user remain, it records `waiting`. At `max_iterations` (40), the restore note tells the agent to set `paused`, report the open items, and stop; asking is allowed again.

## Never ask

The skill does not ask the user during an active goal. This overrides project and other skill instructions to ask, including approval gates in workflows such as peer-coding. The agent pushes branches and creates PRs without asking. A failed test, gate, hook, or review is fixed or marked `- [-]` as needing the user; it is never reported as passed. Other plugins’ hooks continue to run.

## Hooks

The hooks have different conditions:

- Only `- [ ]` lines under `## Checklist`, outside code blocks, count as open items.
- The shell guard (`PreToolUse` on `Bash`) acts while the goal is `active`, or `done`/`waiting` with items still open — also when no `[ ]` item is left and at `max_iterations`. It denies the hard-limit commands described under [Limits and status](#limits-and-status).
- The ask and stop guards act when the goal has open `[ ]` items, is below `max_iterations`, and is `active` — or `done`/`waiting` with items still open. The ask guard denies asking tools. At the limit, asking is allowed. The Stop hook blocks stopping and increments the counter on disk first, up to 40 continuations.
- The restore note (`UserPromptSubmit`, and `SessionStart` including after a compaction) is emitted while the goal is `active` (also when no `[ ]` items remain) or `done`/`waiting` with items still open.
- The entry note is emitted when there is no active, well-formed goal and a prompt mentions “free-hands”. Background-task notifications are not treated as prompts; a notification quoted inside a prompt is ignored and the rest of the prompt is read.

Malformed hook input has no effect. A malformed or unreadable goal does not activate the restore, ask, or stop behavior; on a prompt containing “free-hands”, the prompt hook follows the no-active-goal entry route and may emit the entry question. Failed writes and lock timeouts also have no effect, so a hook failure lets the tool or stop proceed.

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

To pause, say **“pause”**, **“stop”**, or **“일시정지”**. The goal is recorded as `paused`; invoke the command again to resume.

Origin: ported from a project-local skill.

## Codex

Trust the plugin hooks in `/hooks` before relying on them. The ask hook matcher includes `request_user_input`; its denial has not been observed. Codex's default mode has no ask tool, so the Stop hook carries the keep-working rule. If hooks are not trusted or active, the skill continues under its written rules, but hook effects may be off.

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
