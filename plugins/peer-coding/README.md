<p align="center">
  <strong>peer-coding</strong>
</p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>.</p>

<p align="center">
  <strong>Claude × Codex peer orchestration — the two plan, build, and review each other's work as peers.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#commands">Commands</a> &bull;
  <a href="#how-it-works">How it works</a> &bull;
  <a href="#configuration">Configuration</a> &bull;
  <a href="#platforms">Platforms</a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <sub>Part of <a href="../../README.md">because-i-needed</a></sub>
</p>

---

Claude × Codex peer orchestration. Two agents built on different foundations fail in different ways, so each one reviews the other's work — including the main agent's own plan — and a test, not a role, settles their disagreements.

peer-coding is an unofficial community plugin. It is not made, endorsed, or supported by Anthropic or OpenAI.

## Codex

Requires Codex CLI 0.158.0 or later. Start a new session after installation. Claude commands use `/plugin:skill`; Codex uses `$plugin:skill`. The shared skills and resource files ship inside this plugin. Review and trust bundled hooks with `/hooks` before relying on automatic behavior.

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add peer-coding@because-i-needed
```

Use `$peer-coding:run`, `$peer-coding:mode on|off|status|clear`, and `$peer-coding:audit`. The mode skill requires an explicit user request on both hosts. Codex can be the main agent; the existing Codex host adapter keeps review routing across vendors. The audit includes `.codex/hooks.json` and uncommitted `.codex/` and `.agents/` context. For automatic mode, trust the UserPromptSubmit hook; explicit run does not depend on it. Claude CLI is needed for cross-vendor work when Codex is main; without it, the documented single-vendor fallback applies.

### Codex settings

The same `CXC_*` settings, mode scopes and cross-vendor review routing apply on both hosts. Mode state is locally excluded in linked Git worktrees too. The audit reports `AGENTS.override.md` precedence and malformed hook declarations without changing configuration.

Host routing uses the configured CXC reviewer model and effort; names in parentheses are defaults. A filename mention or fallback setting alone is reported as CHECK until the effective instructions are verified.

## Commands

| Command | What it does |
|---|---|
| `/peer-coding:run` | Orchestrate a task: the main agent plans and owns every gate decision, routes work to the `claude-fast` / `codex-bulk` / `main` lanes, and has each vendor review the other's work |
| `/peer-coding:mode on\|off\|status\|clear [--global]` | One-line switch for automatic orchestration. User-only: the model cannot flip it |
| `/peer-coding:audit` | Read-only check that both vendors start from the same project context; proposes fixes, changes nothing |

`on` and `off` write this project's flag (`.claude-x-codex/mode`, git-excluded); `--global` writes your default for every project (`~/.config/claude-x-codex/mode`); `clear` drops the project flag; `CXC_MODE=on|off` overrides both for one shell. With the mode off, `run` starts only when you ask for it.

## Installation

### Via Claude Code plugin marketplace

1. In Claude Code, run `/plugin`.
2. Marketplaces → Add Marketplace.
3. Enter the URL: `https://github.com/zeriong/because-i-needed.git` (or a local path to this repo).
4. Install `peer-coding`.

### Or via CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # or a local path
claude plugin install peer-coding@because-i-needed
```

### Or wire it directly in `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "peer-coding@because-i-needed": true }
}
```

- **Heads-up:** installing it registers a `UserPromptSubmit` hook. It runs on every prompt and prints nothing while the mode is off; when the mode is on, it adds a four-line note (about 100 input tokens per prompt) that routes implementation work to `run`.

## Requirements

- **Claude Code** (or Codex as the main agent), a **git** repository, and bash 3.2+.
- **Optional — Codex CLI** (`codex`). Without it, `run` switches to single-vendor mode — every review goes to a separate reviewer instance of your own vendor — and tells you so.
- **Optional — Orca** with orchestration enabled. Workers can then ask questions mid-task and gates block on your decision; without it, workers run one-way as subagents or CLI calls.
- `python3` for the audit's hook table, and `jq` when a Codex main agent runs Claude reviewers.
- Checked against Claude Code 2.1.283, Codex CLI 0.157.1, and Orca 1.4.215.

## How it works

- **Lanes** — workers run at effort `high`. `claude-fast` (Claude's newest Sonnet: UI, interaction, code taste, Claude-side tools), `codex-bulk` (Codex's newest `luna`: fully specified work such as tests for an existing contract, types, and mechanical migrations), and `main` (the main agent: tightly coupled work, or a spec still being discovered).
- **Cross-vendor review** — the reviewer's vendor always differs from the author's, and the main agent's own plan and triage decisions go to the other vendor too. Claude reviews with the newest Opus and Codex with its newest `sol`, both at effort `xhigh` — the rung just below `max` on both CLIs. For a high-risk phase (auth, payments, data migrations, …), `run` asks you before adding a review by a top model (Codex's newest `astra` or Claude's newest Opus at `max`); it never escalates on its own. Reviewers run read-only and return JSON that both CLIs enforce with a schema.
- **One rebuttal round** — a rejected blocking or major finding goes back to its reviewer once, with the reason. The reviewer concedes or counters with new evidence; if it's still unresolved, it comes to you as DISPUTED with both arguments.
- **Evidence decides** — a test, a reproduction, or a trace settles a disagreement, whichever side has it. Without evidence, you decide.
- **Context bridge** — the audit finds where the two vendors read different instruction files, hooks that bind only one vendor, and uncommitted context that worker worktrees would lack. The Codex calls `run` makes read `CLAUDE.md` through Codex's fallback setting, with no repo change; interactive Codex sessions (Orca workers, or Codex as the main agent) need the same setting in your Codex config. Anything that would change your config or the repo is proposed at plan approval.
- **State on disk** — `.claude-x-codex/` (git-excluded) keeps the plan, decisions, and reviews, so a run survives compaction and can be resumed.

When a dedicated planning skill is available, `run` hands planning to it.

## Configuration

`run` reads these from the environment and falls back to the defaults:

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

Model settings name a family, and the newest version the installed CLI offers for that family always runs. A versioned value such as `gpt-6-sol` is raised to its family's newest; if the newest cannot be determined, the lane stops and explains why.

CXC = **C**laude **×** **C**odex — the prefix of the variables you set in your shell.

## Platforms

The scripts are POSIX-tool bash (compatible with macOS's bash 3.2 and BSD utilities).

| Platform | Status |
|---|---|
| Linux | Supported |
| macOS | Supported |
| Windows + WSL | Supported (behaves as Linux) |
| Windows + Git Bash | Should work; paths follow Git Bash (`~` = `/c/Users/<you>`) |
| Windows PowerShell / cmd only | Not supported — install Git for Windows or use WSL |

On Windows, scripts must stay LF. The plugin's `.gitattributes` enforces this; if you copy files without git, convert line endings to LF.

## License

MIT. See [LICENSE](../../LICENSE).
