<p align="center">
  <strong>harness-builder</strong>
</p>

<p align="center">
  <strong>Build a project-tailored Claude Code harness — from fact-based analysis, not a template.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#the-8-phase-workflow">Workflow</a> &bull;
  <a href="#the-fact-check-loop">Fact-check loop</a> &bull;
  <a href="#faq">FAQ</a>
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

Most "Claude Code harness" plugins stamp out a fixed `.claude/` skeleton and call it done. The rules they enforce are the rules *the plugin author* thought of — not the rules *your project actually needs*.

**harness-builder inverts that.** It reads your project, derives the rules from what's actually there, and only then materializes a harness that enforces *those* rules. The result is a `.claude/` directory tailored to your repo, with every rule traceable to a `file:line` citation in your own code.

## Features

- **Fact-based rule derivation** — every rule comes from a verdict on real code, not a template. Claims without a `file:line` citation are discarded.
- **Gate-first enforcement** — rules that can be checked deterministically become exit-code gates in `review-gate.sh`. Rules that can only be judged qualitatively are kept as advisory and surfaced to Claude on every prompt.
- **Side-effect-aware regression** — any patch applied during the build forces a return to Phase 1. The harness assumes one changed line can invalidate every prior verdict.
- **Two-reviewer cross-check** — before declaring done, the build fires one Opus and one Sonnet agent in parallel (fresh-spawn, no shared context) and synthesizes their JSON reports against six quality axes.
- **Worse/better case indexing** — every rule ships with a `docs/conventions/<rule>.md` containing the actual problematic code from your repo and the actual better form, with grep-friendly keywords.
- **YAGNI by default** — rules with zero violations in your repo and zero user mention are not introduced. A 5-rule harness for a 5-rule project is the success state, not a failure.

## When to use it

- Starting Claude Code work on a project that doesn't yet have a `.claude/` setup.
- Rebuilding an existing `.claude/` after the project structure changed significantly.
- You want rules tied to actual code in your repo, not abstract conventions.

**When to skip it:**

- Single-file utilities or one-shot scripts — the harness is overkill.
- Projects where you've already built and curated a `.claude/` you trust.
- Repos with no clear layering (the fact-check loop needs structure to grip on).

## Installation

### Via Claude Code plugin marketplace

1. In Claude Code, run `/plugin`.
2. Marketplaces → Add Marketplace.
3. Enter URL: `https://github.com/zeriong/because-i-needed.git`.
4. Install `harness-builder`.

### Or via CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install harness-builder@because-i-needed
```

### Or wire it directly in `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "harness-builder@because-i-needed": true }
}
```

## Quick Start

```
cd your-project
# In Claude Code:
/harness-builder:harness-builder
```

Or ask naturally — trigger keywords (Korean / English): `harness 만들어`, `build harness`, `harness 셋업`, `프로젝트 룰 추출`, `review gate 깔아줘`, `harness-builder`.

The skill will:

1. Ask four questions about your project (package manager, monorepo shape, lint/typecheck commands, any rules you want to insist on).
2. Read your codebase and run the fact-check loop on each layer.
3. Derive the rules, generate the gate script, wire the hook, write the skills, and index the conventions docs.
4. Verify everything works against a deliberately-violating sample.
5. Spawn the two-reviewer panel for a final check.

Total run usually takes multiple turns — the skill is honest about that. Wrapping with `/loop` is supported but not required.

## What it does

Output written into your project root:

```
.claude/
├── settings.json                    # UserPromptSubmit hook wiring
├── hooks/inject-context.sh          # Injects project-rules + harness-engineering on every prompt
├── scripts/review-gate.sh           # Deterministic gate — exit 0 / 1 / 2
└── skills/
    ├── project-rules/SKILL.md       # Rules derived in Phase 1–2 from your code
    └── harness-engineering/SKILL.md # 11-phase workflow for future tasks

docs/conventions/
├── <rule-1>.md                      # Worse-case + better-case (real code from your repo) + keyword index
├── <rule-2>.md
└── ...
```

After the build, every user prompt in your project automatically loads `project-rules` and the harness phases. Frontend code? Your derived layer-separation rule fires. Edit a 300-line component? Your derived file-length cap blocks it. The rules are yours, not the plugin's.

The plugin itself ships a single skill: [`skills/harness-builder/SKILL.md`](skills/harness-builder/SKILL.md) — the 8-phase build below.

## The 8-Phase Workflow

| Phase | Responsibility | Fact-check loop required |
|-------|----------------|--------------------------|
| 0 | **Intake** — package manager, monorepo shape, existing scripts, user-recommended rules | — |
| 1 | **Layer / Concern Reconnaissance** — every claim cites `file:line` | ✅ mandatory |
| 2 | **Convention Extraction** — Phase 1 verdicts become rules | ✅ |
| 3 | **`docs/conventions/<rule>.md`** — worse / better case indexed from real repo code | ✅ |
| 4 | **Gate script** (`review-gate.sh`) generation | — |
| 5 | **Hook wiring** (`UserPromptSubmit`) | — |
| 6 | **Skill bodies** (`project-rules` + `harness-engineering`) | — |
| 7 | **Self-verification** — sample diff exercises the gate | — |
| 8 | **Review gate** — Opus + Sonnet 1-shot review, main synthesizes patches | — |

**Any patch applied at Phase 8 forces regression back to Phase 1.** This is an absolute rule, not a heuristic — side-effects are assumed to invalidate prior verdicts. Iteration cap is 3; if convergence isn't reached, the skill emits a truthful failure report and waits for your decision.

## The Fact-Check Loop

This is the single most important rule in the skill. Every claim Phase 1 makes about your code must pass:

```
Claim:        "src/components/admin/audit-logs/page.tsx has only presentation"
              ↓
Self-doubt:   "Really? Let me verify."
              ↓
Direct read:  Read tool opens the file — no memory, no inference
              ↓
Scope sweep:  grep "useState|useEffect|fetch" across the same directory
              ↓
Side-effect:  grep -r for imports of this module
              ↓
SRP test:     Does it have exactly one reason to change?
              ↓
Verdict:      "presentation + data mixed — page.tsx:24-31 calls fetch()"
              with citation to file:line
              ↓
Proceed to next phase
```

Claims that skip any step are **discarded** and Phase 1 restarts. This is what makes the derived rules trustworthy — they aren't from a model's intuition, they're from verifiable facts in your repo.

## Definition of "high quality"

Every patch the skill considers applying is self-graded against six axes (each 0–5):

| Axis | What it means |
|------|---------------|
| **SRP** | One reason to change per module |
| **Comment clarity** | Terse, essentials-only, ≤ 2 lines |
| **KISS** | Simplest form that solves the problem |
| **DRY** | No duplicated logic across modules |
| **YAGNI** | No speculative features or rules |
| **Cognitive ease** | A human reader can parse it without effort |

Patches below an average of 3.5 are rejected; if the rejection rate is high, the relevant phase regresses.

## Bypassing the harness

After the build, every user prompt fires the injection hook. To bypass for a single turn:

- Prefix the prompt with `!` (e.g. `!just answer this`)
- Or include a recognized bypass phrase (Korean / English): `harness 빼고`, `without harness`, `skip harness`, `no harness`

Bypass mode disables the phase enforcement for that turn but keeps project-rules visible.

## FAQ

**Why not just hand me a `.claude/` template?**
Because the template would enforce *someone else's* rules. The point of this skill is to enforce *your project's* rules — derived from its actual code. A 200-LOC component in your codebase doesn't mean the same thing as a 200-LOC component in someone else's; the cap should come from yours.

**What's the difference between this and a linter / ESLint config?**
Linters check syntax and known anti-patterns. This skill checks structural concerns (layer separation, SRP, file length, naming) that linters don't model well, and it ties each rule to a `file:line` in your repo so violations have context. It's complementary, not a replacement.

**Why two reviewers instead of five?**
The setup-guide this skill descends from uses a 2-Opus + 3-Sonnet 5-agent panel. For a one-shot review at the end of a build, that's over-engineering — the marginal benefit of agents 3–5 doesn't justify the latency. One Opus + one Sonnet captures most of the model-diversity benefit at a fifth of the cost.

**What happens if Phase 1 says my project is already perfectly layered?**
Then no layer-separation rule gets introduced. YAGNI applies — rules with zero violations and zero user mention are forbidden from being added. If your only concern is naming, you get a one-rule harness.

**Can I edit the generated `.claude/` after the build?**
Yes. The output is yours. The skill doesn't track or re-sync the generated files. If you re-run `/harness-builder:harness-builder`, you'll need to handle the merge yourself.

**Does this work on non-frontend projects?**
The layer signals in Phase 1 are tuned for frontend repos (`*.tsx`, `use-*.ts`, `api/*`). For a Go service or a Python backend, the skill will need different layer-identification signals — which is exactly the kind of thing Phase 0's free-text question is for. The skill's *workflow* is project-agnostic; only the heuristics in Phase 1 are tuned.

## Requirements

- `git`, `jq`, `bash 4+`
- Target project must be a git work tree
- Claude Code with plugin support

## License

MIT. See [LICENSE](../../LICENSE).

## Acknowledgments

The 8-phase workflow descends from a private harness setup-guide and research-foundation written by the author. The fact-check loop pattern is influenced by CRITIC (Gou et al. 2023) and the Anthropic Multi-Agent Research System engineering blog. The convergence cap (= 3) is from Reflexion (Shinn et al. 2023).
