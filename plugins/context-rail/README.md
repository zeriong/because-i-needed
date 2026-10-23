<p align="center"><strong>context-rail</strong></p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>. Measured on Claude Code.</p>

<p align="center"><strong>Recorded decisions reach the agent the moment it opens the file they govern, not on every turn.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#start">Start</a> &bull; <a href="#what-it-writes">What it writes</a> &bull; <a href="#records">Records</a> &bull; <a href="#the-arrival-hook">The arrival hook</a> &bull; <a href="#changing-a-decision">Changing a decision</a> &bull; <a href="#what-was-measured">What was measured</a> &bull; <a href="#codex">Codex</a> &bull; <a href="#requirements">Requirements</a> &bull; <a href="#installation">Installation</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub>Part of <a href="../../README.md">because-i-needed</a></sub></p>

---

`CLAUDE.md` and `AGENTS.md` load on every turn, so every decision written there is paid for on every turn and is
easy to lose among the rest. context-rail moves each file-specific decision next to the code it governs, and installs
a hook that puts that decision into the agent's context when the agent reads or edits the file. The always-loaded
files only shrink.

## Start

- Claude Code: `/context-rail:build` — sets up the rail in the current repository.
- Codex: `$context-rail:build`.
- `/context-rail:audit` (Codex: `$context-rail:audit`) checks an existing rail and changes nothing.

`build` reads your instruction files, numbers every item, and shows one table: what stays, what becomes a decision
record, what becomes a path-scoped rule, and what it only proposes (automation, personal settings, rules a tool already
enforces). Nothing is written until you answer. Personal items are never moved for you.

## What it writes

All of it is project files, shared with everyone who clones the repository:

| File | Content |
|---|---|
| `<dir>/PRECEDENT.md` | Decision records for the files in that directory |
| `.claude/rules/<topic>.md` | Rules for a set of paths, with `paths:` frontmatter |
| `.claude/hooks/precedent-context.py` | The arrival hook |
| `.claude/settings.json` | The hook wired to PostToolUse (Read, Edit, Write, MultiEdit, Bash) and PostToolUseFailure (Bash); other settings are kept |
| `.claude/context-rail.json` | The source extensions the hook governs |

Items moved out of `CLAUDE.md` are removed there; no pointer line is added. `build` measures the instruction files in
characters and bytes before and after, and fails if either grew.

## Records

```markdown
## tab-keys.mjs

### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Reason: shifting keys remounts the tabs to the right and drops their form input.
- Evidence: `tab-keys.test.mjs`
```

A file is governed by the nearest `PRECEDENT.md` in its directory or above. A `## ` heading names one or more files
(`a.ts · b.ts`); a name that resolves to a real file attaches only to that file. The full format is in
[`skills/build/references/record-format.md`](skills/build/references/record-format.md).

## The arrival hook

When the agent reads a governed file — with the Read tool, or with `cat`, `sed`, `grep` and the like in a shell — or
edits it, the hook adds that file's sections to the context, followed by a short paragraph about changing them. It
fires once per file per session and agent, so subagents get the record too. A failed shell read is covered by
PostToolUseFailure.

The output is kept under 10,000 characters: sections up to 6,000 characters are injected whole, longer ones are
compressed to their headings and decision lines. Above 10,000 characters Claude Code shows only a preview, which would
cut off the paragraph at the end. Git-ignored files get nothing. Any internal error exits silently and never blocks
the agent.

## Changing a decision

The paragraph after each section says that a decision changes only with your confirmation:

- If you name the recorded decision and say to override it — "`src/tabs/PRECEDENT.md` §stable-tab-keys forbids this;
  I'm overriding it" — the agent makes the change and rewrites the decision block in place, noting that you overrode
  it.
- Any other request that conflicts with a decision, however firmly put, makes the agent stop before editing, name the
  decision and what conflicts, and ask — noting whether an upstream change, a new measurement, a reported defect, or a
  different axis applies.
- When another agent assigned the task — a subagent, or a worker such as peer-coding's — its brief counts only if it
  reports that you named the decision and said to override it. A brief that says to go ahead anyway, or that a newer
  decision replaces whatever is recorded, does not: the agent stops and reports back to whoever assigned it, so that
  agent can ask you.

## What was measured

All measurements are in [z-lab `precedent-lab/`](https://github.com/zeriong/z-lab/tree/main/precedent-lab), on Claude
Code 2.1.296–2.1.309 and Codex 0.163.0, headless; Opus at effort `xhigh` unless a row names other agents.

| Claim | Result | Experiment |
|---|---|---|
| Injecting the section text, not a pointer, puts the prohibition in context before the first edit | 3/15 → 44/45 trap runs | `real-env-rail-2.1.296` |
| The paragraph stops conflicting requests that do not name the record | broke the prohibition: 11/12 without it → 0/12 with it | `stop-en-r2-2.1.306` |
| …and still lets an explicit override through | 12/12 proceeded and rewrote the record in place | `stop-en-r2-2.1.306` |
| …and does not stop conflict-free edits | 0/15 stopped | `stop-en-r2-2.1.306` |
| `build` moves items to the right place | 5/5 runs: 14/14 items, all checks passing, `CLAUDE.md` 1,906 → 540 chars | `build-fidelity-0.1.0` |
| `audit` checks without changing anything and names planted defects | 4/4 runs: 0 files changed, all checks run, 3/3 planted defects named, no false defects | `audit-canary-0.1.0` |
| A project normalized by `build` keeps its decisions better than the same decisions in `CLAUDE.md` | broke the prohibition under authority requests: 12/12 resident → 0/12 normalized; 0/15 false stops in both | `fresh-project-0.1.0` |
| Path-scoped rules load on first contact with a matching file | Read, shell read and Write all attached the rule | `platform-r2-2.1.308-0.163.0` |
| A brief from another agent counts as confirmation only when it relays your named override | under a main agent's "go ahead anyway" brief, Sonnet subagents broke 6/9 with 0.1.0's paragraph; with that sentence fixed in the brief, 12/12 broke with 0.1.0's → 0/12 with 0.2.0's | `leaf-2.1.309`, `leaf-r2-2.1.309` |
| Agents that receive the task from another agent keep the rule | Opus and Sonnet subagents, Sonnet `claude -p` and Codex `gpt-6-luna` workers, every path: 0/12 broke, 12/12 overrides proceeded, 0/15 stopped | `leaf-r2-2.1.309` |

The trap and build results come from synthetic fixtures and from one private repository, with 12–15 runs per cell.
**Not measured:** other models or efforts, interactive sessions and Orca's two-way workers, records written in other
languages with this paragraph, large repositories, and running `build` and `audit` on Codex.

## Codex

The same skills install the same hook on Codex (`$context-rail:build`, `install-hooks.py --host codex` → `.codex/hooks/`,
`.codex/hooks.json`).

- **Platform** (Codex 0.163.0, with a probe hook):
  - PostToolUse output reaches the model.
  - Shell reads arrive as `Bash`, and edits as `apply_patch`.
  - A failed shell call still fires PostToolUse.
- **This plugin's hook on Codex** (installed with `install-hooks.py --host codex`): a Codex worker (`gpt-6-luna`,
  effort high, given peer-coding's brief) kept the rule — 0/12 broke, 12/12 overrides proceeded, 0/15 stopped
  (`leaf-r2-2.1.309`).
- **Not measured:** running `build` and `audit` on Codex, when nested `AGENTS.md` files load, and `apply_patch`
  delivery.

Trust the hook in `/hooks` before relying on it.

## Requirements

- `python3` (3.9 or newer) on `PATH`.
- `git` — the hook finds the repository root and skips ignored files with it.

## Installation

First add the marketplace, then install the plugin:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install context-rail@because-i-needed
```

For Codex, follow the [marketplace instructions](../../README.md#codex).

## License

MIT. See [LICENSE](../../LICENSE).
