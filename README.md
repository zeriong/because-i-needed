<p align="center">
  <strong>because-i-needed</strong>
</p>

<p align="center">
  <strong>Claude Code plugins I built because I needed them — planning, project harnesses, and measured UI.</strong>
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

This repository is a Claude Code **plugin marketplace** with four independent plugins. Install only the ones you need.

## Plugins

### [plan-smith](plugins/plan-smith) · `v1.7.0`

**Forge plans through a two-stage pipeline.** The main agent distills the whole conversation into a context packet (goals, hard constraints, rejected alternatives) and confirms it with you; a clean-context `plan-writer` agent then writes the plan with a reasoning-frame library and validated writing styles, and the plan is relayed to you verbatim — no summarization loss, no context contamination.

- **Use it when** you need a plan for a migration, a launch, a build-out — anything where a long, noisy session would otherwise produce a muddled plan.
- **Entry:** `/plan-smith:forge <task>` or just *"write a plan for …"*

[Read the plan-smith README →](plugins/plan-smith)

### [harness](plugins/harness) · `v1.2.0`

**Build a project-tailored Claude Code or Codex harness from fact-based analysis, not a template.** It reads your repo's actual layering and separation of concerns, derives rules that each cite a `file:line` in your code, and generates `project-rules`, a deterministic `review-gate.sh`, a `UserPromptSubmit` hook, and a `harness-engineering` skill.

- **Use it when** you start Claude Code or Codex work on a project without a harness, or the structure changed enough that the old one no longer fits.
- **Entry:** `/harness:build` or *"build harness"*

[Read the harness README →](plugins/harness)

### [ux-ui](plugins/ux-ui) · `v1.2.0`

**Build web and mobile UI measured on the real render.** It captures real screenshots (chrome-devtools for web; a mobile MCP or CLI snapshot harness for React Native / Flutter / iOS / Android), has an art-director agent critique those measured snapshots, iterates until the UI is correct and elegant, and blocks `git commit` of UI until the exact staged diff is APPROVED.

- **Use it when** you build or change any component, page, or screen and want it verified on the actual render, not imagined.
- **Entry:** `/ux-ui:build` (web) · `/ux-ui:build-mobile` (mobile), or just ask to build a UI
- **Heads-up:** installing it registers a `PreToolUse` commit-gate hook (runs before every `Bash` call, blocks only UI commits) and four MCP servers.

[Read the ux-ui README →](plugins/ux-ui)

### [claude-x-codex](plugins/claude-x-codex) · `v0.1.0`

**Claude × Codex peer orchestration.** The main agent plans and owns every gate, routes work to fast Claude or bulk Codex workers, and the two vendors review each other's work — the main agent's own plan included — with one rebuttal round and evidence, not role, deciding. An audit makes sure both vendors start from the same project instructions. Unofficial community plugin.

- **Use it when** you have both Claude Code and Codex and want a second vendor's review on every phase of a feature.
- **Entry:** `/claude-x-codex:run`, or turn on `/claude-x-codex:mode on` so implementation requests go through it
- **Heads-up:** installing it registers a `UserPromptSubmit` hook (runs on every prompt, prints nothing while the mode is off).

[Read the claude-x-codex README →](plugins/claude-x-codex)

## Installation

The installer lists the plugins and installs the ones you pick:

```bash
curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
```

↑/↓ (or j/k) to move, space to toggle, `a` for all, enter to install, `q` to quit — everything starts selected. Options: `--all`, `--only a,b`, `--list`, `--dry-run`, `--scope user|project|local`; through a pipe, pass them after `bash -s --` (e.g. `… | bash -s -- --only harness`). It runs the same `claude plugin` commands shown below.

Or add the marketplace yourself, then install the plugins you want:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@bin
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
    "plan-smith@bin": true,
    "harness@bin": true,
    "ux-ui@bin": true,
    "claude-x-codex@bin": true
  }
}
```

## Naming

Every command reads **subject : action** — `/<plugin>:<skill>`.

- **The plugin is the subject** — what it works on (`harness`, `ux-ui`). `plan-smith` keeps its established name.
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

`review` is reserved for an upcoming plugin.

## Repository layout

```
because-i-needed/
├── .claude-plugin/marketplace.json   # lists the four plugins
├── install.sh                        # interactive installer (runs claude plugin install)
└── plugins/
    ├── plan-smith/                   # skill + plan-writer agent + split checker (+ CHANGELOG.md)
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
