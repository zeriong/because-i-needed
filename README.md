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

This repository is a Claude Code **plugin marketplace** with three independent plugins. Install only the ones you need.

## Plugins

### [plan-smith](plugins/plan-smith) · `v1.4.2`

**Forge plans through a two-stage pipeline.** The main agent distills the whole conversation into a context packet (goals, hard constraints, rejected alternatives) and confirms it with you; a clean-context `plan-writer` agent then writes the plan with a reasoning-frame library and validated writing styles, and the plan is relayed to you verbatim — no summarization loss, no context contamination.

- **Use it when** you need a plan for a migration, a launch, a build-out — anything where a long, noisy session would otherwise produce a muddled plan.
- **Entry:** `/plan-smith:plan-smith <task>` or just *"write a plan for …"*

[Read the plan-smith README →](plugins/plan-smith)

### [harness-builder](plugins/harness-builder) · `v1.0.0`

**Build a project-tailored Claude Code harness from fact-based analysis, not a template.** It reads your repo's actual layering and separation of concerns, derives rules that each cite a `file:line` in your code, and generates `project-rules`, a deterministic `review-gate.sh`, a `UserPromptSubmit` hook, and a `harness-engineering` skill.

- **Use it when** you start Claude Code work on a project with no `.claude/` setup, or the structure changed enough that the old one no longer fits.
- **Entry:** `/harness-builder:harness-builder` or *"build harness"*

[Read the harness-builder README →](plugins/harness-builder)

### [ux-ui-builder](plugins/ux-ui-builder) · `v1.1.0`

**Build web and mobile UI measured on the real render.** It captures real screenshots (chrome-devtools for web; a mobile MCP or CLI snapshot harness for React Native / Flutter / iOS / Android), has an art-director agent critique those measured snapshots, iterates until the UI is correct and elegant, and blocks `git commit` of UI until the exact staged diff is APPROVED.

- **Use it when** you build or change any component, page, or screen and want it verified on the actual render, not imagined.
- **Entry:** `/ux-ui-builder:ux-ui-builder` (web) · `/ux-ui-builder:ux-ui-builder-mobile` (mobile), or just ask to build a UI
- **Heads-up:** installing it registers a `PreToolUse` commit-gate hook (runs before every `Bash` call, blocks only UI commits) and four MCP servers.

[Read the ux-ui-builder README →](plugins/ux-ui-builder)

## Installation

Add the marketplace once, then install the plugins you want:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install plan-smith@because-i-needed
claude plugin install harness-builder@because-i-needed
claude plugin install ux-ui-builder@because-i-needed
```

Or in Claude Code: `/plugin` → Marketplaces → Add Marketplace → `https://github.com/zeriong/because-i-needed.git`, then install from the list.

Or wire it directly in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": {
    "plan-smith@because-i-needed": true,
    "harness-builder@because-i-needed": true,
    "ux-ui-builder@because-i-needed": true
  }
}
```

## Repository layout

```
because-i-needed/
├── .claude-plugin/marketplace.json   # lists the three plugins
└── plugins/
    ├── plan-smith/                   # skill + plan-writer agent (+ CHANGELOG.md)
    ├── harness-builder/              # skill
    └── ux-ui-builder/                # 2 skills + 2 agents + commit-gate hook + 4 MCPs
```

Each plugin folder is self-contained: its README, manifest, and everything it ships live under `plugins/<name>/`.

## Language policy

- Every README in this repository — this one and each plugin's — ships in **five languages**: `README.md` (English, the source), `README.ko.md` (한국어), `README.ja.md` (日本語), `README.zh-CN.md` (简体中文), `README.zh-TW.md` (繁體中文).
- A README change updates all five in the same commit. A new plugin ships all five from its first commit.
- Files Claude consumes directly — `SKILL.md`, `references/*.md`, `agents/*.md` — stay in English.

## License

MIT. See [LICENSE](LICENSE).
