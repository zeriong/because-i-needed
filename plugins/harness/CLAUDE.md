# harness — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to harness.
The original repository had no development-rules file for this plugin. Everything below was derived from facts checked in the code as of 2026-09-23.

Contents: `skills/build/SKILL.md`, the host adapter and public workflow in `references/`, and
`assets/inject-context.sh` and `scripts/install-hooks.py`, all inside `skills/build/`.
The skill generates a `.claude/` harness on Claude Code, or a
`.codex/` + `.agents/skills/` harness on Codex, **in the target project**. The plugin itself installs no hooks.

---

## Rule 1 — SKILL.md and the READMEs must state the same facts

The five READMEs restate these facts from SKILL.md. A change to one in SKILL.md changes the five READMEs in the same commit.

| Fact | Source in SKILL.md |
|---|---|
| Intake plus eight build phases and the per-phase responsibility table | `## Phase 0` through `## Phase 8` |
| The generated file tree (`.claude/settings.json`, `hooks/inject-context.sh`, `scripts/review-gate.sh`, `skills/project-rules`, `skills/harness-engineering`, `docs/conventions/<rule>.md`) | the output list at the top, `## harness:build complete` |
| The 6 trigger keywords | frontmatter `description` |
| The 6 quality axes and rejection below a 3.5 average | `## Absolute laws` item 4, `## Phase 8` |
| Regression cap = 3 | `## Phase 6` (6.2), `## Phase 8`, `## Notes for Claude` |
| Opus 1 + Sonnet 1, one-shot review | `## Phase 6` (6.2), `## Phase 8` |
| YAGNI — no rule with zero violations and zero user mentions | `## Phase 2`, `## Notes for Claude` |

## Rule 2 — SKILL.md references only files inside the plugin

An installed user's Claude can read only the plugin folder (root Rule 1).
Documents SKILL.md relies on go in `skills/build/references/`, referenced by relative path.

The previous release depended on private setup-guide/research-foundation sections. The public
`references/workflow.md` now defines the required eleven phases using this plugin's published
contracts, and `assets/inject-context.sh` supplies the injection mechanism. No private document
was copied. Keep these resources packaged and the generated skills project-specific.

On Codex, use `references/host-codex.md` for output paths and two independent reviewers. Keep
Claude's Opus + Sonnet panel. Preserve existing configuration when merging hooks. Protected
Codex directories may require write approval; a staged draft is not an installed harness.
The injection asset needs bash 3.2+ and Python 3; self-verification also uses jq.
Use the bundled installer to merge hooks without replacing unrelated settings. Resolve
both Codex reviewer model/effort pairs explicitly and embed the review procedure in the
generated workflow so it remains usable without this builder. The hook reads stdin
without a shell heredoc temporary file, including in read-only reviewer processes.

## Rule 3 — Names

The plugin name `harness` and the skill folder name `build` are embedded in the ten READMEs' `/harness:build` and in SKILL.md's
report headings (`## harness:build …`). A rename changes all of them together (root Rule 8). Before 1.1.0 the name was `harness-builder`.

## Codex compatibility evidence — 1.2.0

See z-lab `harness-lab/codex-compat-1.2.0/` and `codex-compat-1.2.0-full-access/` (H01–H03) and the shared
`plugin-platform-lab/codex-final-0.158.0/` packaging/installer checks. These records
cover host wiring and the named fixture paths, not quality improvements. Keep the
existing workflow invariants when changing an adapter.

Additional setting-parity checks: z-lab `harness-lab/codex-parity-1.2.0/` (H04–H06).

Bypass always keeps project-rules while omitting the workflow body: z-lab
`harness-lab/codex-bypass-1.2.0/` (H07). Test both host layouts against that existing README contract.

Re-review fixes: z-lab `harness-lab/codex-rereview-1.2.0/` (H08).
Reusable workflows resolve model/effort defaults per invocation and use numeric quality scores with separate evidence, avoiding builder-default persistence and incompatible nested score objects.
