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
| The generated file tree (`.claude/settings.json`, `hooks/inject-context.sh`, `scripts/review-gate.sh`, `scripts/latest-model.py`, `skills/project-rules`, `skills/harness-engineering`, `docs/conventions/<rule>.md`) | the output list at the top, `## harness:build complete` |
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

## Rule 4 — Every reviewer runs the newest model of its family

The architecture and gate reviewers (Codex) and the Opus and Sonnet panel (Claude) run the newest model of their family
that the installed CLI and account offer, resolved right before each dispatch with `scripts/latest-model.py`
(byte-identical in every plugin). The maintainer upgrades the CLIs; the plugin only chooses the newest available model.

- Codex: `HARNESS_CODEX_ARCH_MODEL` and `HARNESS_CODEX_GATE_MODEL` name a family or an id and are resolved to its family's
  newest; unset, the main session's model id is used. The commands live in `references/host-codex.md`.
- Claude Code: the panel keeps the `opus` / `sonnet` aliases; SKILL.md's Host setup runs the resolver's `claude` mode
  first, because an `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` override would silently run an older model.
- The generated harness-engineering skill resolves through a project-local copy, `.<host>/scripts/latest-model.py`, which
  `skills/build/scripts/install-hooks.py` installs beside the hook (same dry-run / check / idempotent behavior; a differing
  existing copy needs `--replace-hook`). It never references the plugin's install path, which does not exist for the project's other users.
- Exit 2 or 3 stops the review: no fallback model, and the main agent never reviews itself.
- Write no versioned model id in a skill, reference or script — use placeholders (`<resolved id>`); a pin-scan test fails on one.
- Record each reviewer's id from the run (Codex run header `model:`, a native reviewer's receipt), never from the reviewer's report.

**Why:** measured in z-lab `plugin-platform-lab/latest-model-0.159.0/` (L01–L07) and
`latest-model-r2-0.159.0/`, `-r3-`, `-r4-` (L04r–L09, L02x; L08/L08i: a sandboxed shell cannot refresh the catalog,
so a sandboxed main reruns the resolver outside the sandbox before stopping): the live Codex catalog listed a newer model than the
bundled one, `-m <resolved id>` ran it, an `ANTHROPIC_DEFAULT_SONNET_MODEL` override made the `sonnet` alias run Haiku, and a Codex agent's
statement of its own model was wrong (plan-smith-lab N03). Wired skill: z-lab `harness-lab/latest-model-1.3.0/` (M01, M02; a full build was not measured). The generated skill outlives the builder session, so it needs its own resolver.

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
