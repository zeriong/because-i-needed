# harness — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to harness.
The original repository had no development-rules file for this plugin. Everything below was derived from facts checked in the code as of 2026-09-23.

Contents: a single skill, `skills/build/SKILL.md`. No agents, hooks, scripts, or references.
The skill generates a `.claude/` harness **in the target project** — the plugin itself installs no hooks.

---

## Rule 1 — SKILL.md and the READMEs must state the same facts

The five READMEs restate these facts from SKILL.md. A change to one in SKILL.md changes the five READMEs in the same commit.

| Fact | Source in SKILL.md |
|---|---|
| The 8-phase workflow and the per-phase responsibility table | `## Phase 0` through `## Phase 8` |
| The generated file tree (`.claude/settings.json`, `hooks/inject-context.sh`, `scripts/review-gate.sh`, `skills/project-rules`, `skills/harness-engineering`, `docs/conventions/<rule>.md`) | the output list at the top, `## harness:build complete` |
| The 6 trigger keywords | frontmatter `description` |
| The 6 quality axes and rejection below a 3.5 average | `## Absolute laws` item 4, `## Phase 8` |
| Regression cap = 3 | `## Phase 6` (6.2), `## Phase 8`, `## Notes for Claude` |
| Opus 1 + Sonnet 1, one-shot review | `## Phase 6` (6.2), `## Phase 8` |
| YAGNI — no rule with zero violations and zero user mentions | `## Phase 2`, `## Notes for Claude` |

## Rule 2 — SKILL.md references only files inside the plugin

An installed user's Claude can read only the plugin folder (root Rule 1).
Documents SKILL.md relies on go in `skills/build/references/`, referenced by relative path.

**Known defect (confirmed 2026-09-23, unfixed):** SKILL.md tells Claude to "use as-is" sections of private documents —
`setup-guide` §4 (`inject-context.sh`), §5 (the 11-phase workflow), §7 (gate script skeleton and diff range),
§8 (hard-stop report format), and `research-foundation` §2. The originals live in `~/WorkSpace/Z-Work/__private__MY-CONFIG/claude/harness/`
and are not in the plugin, so an installed copy cannot read those sections and Claude fills them in by guesswork.
The README's list of harness bypass phrases (`!`, `harness 빼고`, `without harness`, `skip harness`, `no harness`) also comes
from setup-guide §4, not from SKILL.md.

- To fix it, move the needed sections into `references/` and point SKILL.md at those files.
  That publishes private documents in a public repository, so **the maintainer decides which sections move.**
- It changes behavior, so bump the version (root Rule 2).
- The README requirement `bash 4+` has no basis in SKILL.md either. Treat it as unsupported until checked against the generated scripts.

## Rule 3 — Names

The plugin name `harness` and the skill folder name `build` are embedded in the ten READMEs' `/harness:build` and in SKILL.md's
report headings (`## harness:build …`). A rename changes all of them together (root Rule 8). Before 1.1.0 the name was `harness-builder`.
