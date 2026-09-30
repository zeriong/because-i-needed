<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>Claude Code and Codex plugins I built because I needed them — project harnesses, measured UI, and Claude × Codex orchestration.</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin%20Marketplace-orange" alt="Claude Code Plugin Marketplace"></a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

This repository is a Claude Code and Codex **plugin marketplace** with three independent plugins. Install only the ones you need.

## Codex

The same three plugins also support Codex CLI 0.158.0 or later. Install a chosen subset:

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash -s -- --host codex --only harness,ux-ui,claude-x-codex
```

Or use the CLI directly:

```bash
codex plugin marketplace add https://github.com/zeriong/because-i-needed.git
codex plugin add harness@bin
codex plugin add ux-ui@bin
codex plugin add claude-x-codex@bin
```

Start a new Codex session and invoke `$harness:build`, `$ux-ui:build`, `$ux-ui:build-mobile`, or `$claude-x-codex:run`. Use `$claude-x-codex:mode on` for automatic orchestration and `$claude-x-codex:audit` to inspect context parity. Review and trust installed hooks with `/hooks` before relying on automatic routing or the UI commit gate.

The installer defaults to Claude Code; `--host codex` selects Codex. Codex installs at user scope: omit `--scope` or use `--scope user`; project/local scope is rejected. Skills, scripts and workflow contracts are shared; each plugin includes a Codex manifest. Codex execution uses its own questions and independent agents. The harness generates `.codex/hooks.json`, `.codex/hooks/`, `.codex/scripts/review-gate.sh`, `.codex/scripts/latest-model.py` and `.agents/skills/`; existing Claude artifacts are preserved. UI measurement still requires the relevant browser/mobile tools. See each plugin's Codex section for details.

Each plugin documents its Codex settings below. Models and effort can be selected per writer/reviewer role; unconfigured roles run the newest model of the active session's family. The harness can generate Claude, Codex or both layouts. CXC retains its cross-vendor model routing. Browser/device requirements and hook trust still apply.

## Plugins

### [harness](plugins/harness) · `v1.3.0`

**Build a project-tailored Claude Code or Codex harness from fact-based analysis, not a template.** It reads your repo's actual layering and separation of concerns, derives rules that each cite a `file:line` in your code, and generates `project-rules`, a deterministic `review-gate.sh`, a `UserPromptSubmit` hook, and a `harness-engineering` skill.

- **Use it when** you start Claude Code or Codex work on a project without a harness, or the structure changed enough that the old one no longer fits.
- **Entry:** `/harness:build` or *"build harness"*

[Read the harness README →](plugins/harness)

### [ux-ui](plugins/ux-ui) · `v1.4.0`

**Build web and mobile UI measured on the real render.** It captures real screenshots (chrome-devtools for web; a mobile MCP or CLI snapshot harness for React Native / Flutter / iOS / Android), has an art-director agent critique those measured snapshots, iterates until the UI is correct and elegant, and blocks `git commit` of UI until the exact staged diff is APPROVED.

- **Use it when** you build or change any component, page, or screen and want it verified on the actual render, not imagined.
- **Entry:** `/ux-ui:build` (web) · `/ux-ui:build-mobile` (mobile), or just ask to build a UI
- **Heads-up:** installing it registers a `PreToolUse` commit-gate hook (runs before every `Bash` call, blocks only UI commits) and four MCP servers.

[Read the ux-ui README →](plugins/ux-ui)

### [claude-x-codex](plugins/claude-x-codex) · `v0.3.0`

**Claude × Codex peer orchestration.** The main agent plans and owns every gate, routes work to fast Claude or bulk Codex workers, and the two vendors review each other's work — the main agent's own plan included — with one rebuttal round and evidence, not role, deciding. An audit makes sure both vendors start from the same project instructions. Unofficial community plugin.

- **Use it when** you have both Claude Code and Codex and want a second vendor's review on every phase of a feature.
- **Entry:** `/claude-x-codex:run`, or turn on `/claude-x-codex:mode on` so implementation requests go through it
- **Heads-up:** installing it registers a `UserPromptSubmit` hook (runs on every prompt, prints nothing while the mode is off).

[Read the claude-x-codex README →](plugins/claude-x-codex)

## Retired plugins

### plan-smith — retired 2026-09-30 (last version 1.8.0)

In z-lab, plan-smith 1.6.0's pipeline (Claude Code, one task) was a net cost when the same model planned and implemented: planning alone used about 1.65× (Fable 5.1, completed) and at least 2.41× (Opus 5.5, cut off) the tokens of a whole base plan-and-implement chain, and the base plans already worked on the first try. Each figure is a single run per model. Savings were measured only on an approximated pipeline; a weaker implementer and plan quality on the real pipeline were not measured. See the [measurement](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/real-skill-tco-1.6.0) and the [retirement decision](https://github.com/zeriong/z-lab/tree/main/plan-smith-lab/analyze). The last source (1.8.0) remains in this repository's git history; versions up to 1.4.2 are at [zeriong/plan-smith](https://github.com/zeriong/plan-smith).

To remove an installed copy:

- Claude Code: `claude plugin uninstall plan-smith@bin` (add `--scope project` or `--scope local` if you installed it there).
- Codex: `codex plugin remove plan-smith@bin`.

## Installation

The installer lists the plugins and installs the ones you pick:

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
```

↑/↓ (or j/k) to move, space to toggle, `a` for all, enter to install, `q` to quit — everything starts selected. Options: `--all`, `--only a,b`, `--list`, `--dry-run`, `--scope user|project|local`; through a pipe, pass them after `bash -s --` (e.g. `… | bash -s -- --only harness`). It runs the same `claude plugin` commands shown below.

Or add the marketplace yourself, then install the plugins you want:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness@bin
claude plugin install ux-ui@bin
claude plugin install claude-x-codex@bin
```

Or in Claude Code: `/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git`, then install from the list.

Or wire it directly in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "bin": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "harness@bin": true,
    "ux-ui@bin": true,
    "claude-x-codex@bin": true
  }
}
```

## Naming

Every command reads **subject : action** — `/<plugin>:<skill>`.

- **The plugin is the subject** — what it works on (`harness`, `ux-ui`).
- **The skill is a verb** from one shared vocabulary, and a verb means the same thing in every plugin.
- Plugins stay separate, so you install only what you need and one plugin's hooks or MCP servers never come along with another.

| Verb | Meaning |
|---|---|
| `build` | Create an artifact in your project (a harness, a UI) |
| `forge` | Distill the conversation into a document (a plan) |
| `run` | Execute a task |
| `mode` | Switch a behavior on or off |
| `audit` | Inspect, read-only |
| `review` | Evaluate a result |

`forge` and `review` have no plugin at the moment.

## Repository layout

```
because-i-needed/
├── .claude-plugin/marketplace.json   # lists the three plugins
├── install.sh                        # interactive installer (--host claude|codex)
└── plugins/
    ├── harness/                      # skill
    ├── ux-ui/                        # 2 skills + 2 agents + commit-gate hook + 4 MCPs
    └── claude-x-codex/               # 3 skills + prompt hook + 3 scripts
```

Each plugin folder is self-contained: its README, manifest, and everything it ships live under `plugins/<name>/`.

## Language policy

- Every README in this repository — this one and each plugin's — ships in **five languages**: `README.md` (English, the source), `README.ko.md` (한국어), `README.ja.md` (日本語), `README.zh-CN.md` (简体中文), `README.zh-TW.md` (繁體中文).
- A README change updates all five in the same commit. A new plugin ships all five from its first commit.
- READMEs are the only translated files. Everything else — `CLAUDE.md`, `SKILL.md`, `references/*.md`, `agents/*.md`, `CHANGELOG.md`, hook messages — is written in English. Trigger phrases that must match what a user types stay in the user's language.

## License

MIT. See [LICENSE](LICENSE).
