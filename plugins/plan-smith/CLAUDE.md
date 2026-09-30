# plan-smith — development rules

Every shared rule in the root `CLAUDE.md` (install boundary, version bumps, five-language READMEs, commits) applies. This file holds only what is specific to plan-smith.
It originates in the release statute at `.claude/CLAUDE.md` in `zeriong/plan-smith`. There it was a gitignored, local-only file;
moving it here, the paths were adjusted. The original statute's Article 6 ("this file is never committed") is repealed — here it is committed.

Contents: the skill `skills/forge/SKILL.md`, five references (`frames.md`, `styles.md`, `packet-template.md`, `split.md`, `host-codex.md`), the script `scripts/split-check.py`, the agent `agents/plan-writer.md`, and `CHANGELOG.md`.

---

## Rule 1 — A version bump is a set of three (missing one means it is not a release)

Handle all three in the same commit.

1. **The 13 version strings** — the table in root Rule 2.
2. **A `CHANGELOG.md` entry** — Keep a Changelog format, sorted into `Added` / `Changed` / `Fixed` / `Removed`, and
   **always with a `Why`** (what changed is recoverable from the diff; why it changed is what you will need later).
   Take version boundaries from git, not memory: `git log -p -- plugins/plan-smith/.claude-plugin/plugin.json`
   (before 1.4.2, the history of the `zeriong/plan-smith` repository — root Rule 7).
   In this repository the CHANGELOG sits inside the plugin folder, so it **reaches installed clients** (in the original repository it sat at the root and did not).
3. **README concepts** — when a **concept users must understand** (a frame, gate, pipeline stage, or style) changes or is
   added, update the five `plugins/plan-smith/README*.md`. If the one-line summary changes, the five root READMEs too. Internal refactors and typos don't count.

**Count numbers before writing them.** Frame count:

```bash
grep -cE '^### [a-z-]+ — ' plugins/plan-smith/skills/forge/references/frames.md   # 26 as of 2026-09-23
```

`grep -c '^### '` also counts six sections that are not frames (`Gate 0`, `The four predicates`, `The load-bearing path`,
`Requirements get verbs`, `Implementer contract`, `The machinery budget`) and returns 32 — don't use it.
The README's "26" means two things: the **frame count** (26 frames) and the **experiment size** (26-plan experiment). When the frame count changes, leave the experiment size alone.

**Why:** while the README said 24 frames the library held 25, and later 26.
The original statute's "subtract 2 from `grep -c '^### '`" became wrong once four specification-rule sections were added (confirmed 2026-09-23).

## Rule 2 — After a release, compare the installed copy

After bumping the version, check that the file actually changed in the cache (`~/.claude/plugins/cache/bin/plan-smith/<version>/`) —
for example, compare `frames.md` line counts.

**Why:** 1.1.1 — the document-budget and Gate 0 tie-break clauses were written into the source while the installed copy kept
serving 1.1.0 (355 lines vs 364), and they were delivered only once the version moved.

## Rule 3 — SemVer criteria

- **MAJOR** — existing usage breaks (an incompatible change to the skill interface or the packet format).
- **MINOR** — behavior grows or changes: **adding** a frame, gate, or pipeline stage, changing the routing rules.
- **PATCH** — docs, typos, delivery-only bumps. **No behavior change.**

A docs-only change never gets MINOR. An added frame never gets PATCH.

## Rule 4 — No unsupported claims in the docs

Every empirical claim in a README or the CHANGELOG ("won the A/B", "validated on N plans") carries **where the observation came from**
(which series of z-lab `plan-smith-lab/`). If it was observed once, say once, and state the limits in the same paragraph.
Behavior changes are measured there before release — root Rule 9.

**Why:** 1.1.0 came out of a controlled A/B in which **its own output lost to the frameless baseline**. The README recorded that,
so the next person can avoid the same trap. Record only the wins and the library becomes an advertisement; record the failures and it becomes a tool.

## Rule 5 — Names and invariants

- The plugin name `plan-smith` is embedded in SKILL.md's agent reference (`plan-smith:plan-writer`) and in the ten READMEs'
  `/plan-smith:forge`; the skill folder name `forge` is also embedded in the `agents/plan-writer.md` description and in
  `references/packet-template.md`. A rename changes all of them together (root Rule 8). Before 1.5.0 the skill was named `plan-smith`.
- When editing `SKILL.md` or `agents/plan-writer.md`, keep the five README "Design invariants" intact (the main agent never writes the plan /
  no drafting without a confirmed packet / the writer's input is self-contained / verbatim relay — a split plan as its index and every
  part in order / a style is not a model choice). The Stage 2d split moves text and must never rewrite it; `scripts/split-check.py`
  is what proves that, so keep its rules and `references/split.md` in step (`--self-test` after any change to either). Evidence for
  the 1.6.0 split: z-lab `plan-smith-lab/split-1.6.0/` (S1: 6/6 lossless on the first attempt; its effect on implementers is
  unmeasured). Keep the checker command in SKILL.md: `${CLAUDE_PLUGIN_ROOT}` is replaced only in SKILL.md text, not in a
  reference file or the shell, and `split.md` pointing to it ran the script 3/3 (z-lab `plugin-platform-lab/`, V01–V05).
  Breaking one is a design change: agree on it with the maintainer first, and update the README invariant list with it.

## Rule 6 — Every plan-writer runs the newest model of its family

Every writer pass, wiring audit and split runs the newest model of the main session's family that the installed CLI
and account offer, resolved right before each dispatch with `scripts/latest-model.py` (byte-identical in every plugin).
The maintainer upgrades the CLIs; the plugin only chooses the newest available model.

- Codex: `PLAN_SMITH_CODEX_MODEL` names a family or an id and is resolved to its family's newest; unset, the main session's
  model id is used. The command lives in `references/host-codex.md`; the packet run stamp records the id that ran.
- Claude Code: the writer stays `model: inherit`; SKILL.md runs the resolver's `claude` mode first, because an
  `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` override would silently run an older model.
- Exit 2 or 3 stops the step. No fallback model, and the main agent never writes the plan itself.
- Write no versioned model id in a skill, reference or agent — use placeholders (`<resolved id>`); a pin-scan test fails on one.
- Take a run's model id from the run (Codex run header `model:`, a native subagent's receipt), never from the worker's report.

**Why:** measured in z-lab `plugin-platform-lab/latest-model-0.159.0/` (L01–L07) and
`latest-model-r2-0.159.0/`, `-r3-`, `-r4-` (L04r–L09, L02x; L08/L08i: a sandboxed shell cannot refresh the catalog,
so a sandboxed main reruns the resolver outside the sandbox before stopping): the live Codex catalog listed a newer model than the
bundled one, `-m <resolved id>` ran it, an `ANTHROPIC_DEFAULT_SONNET_MODEL` override made the `sonnet` alias run Haiku, and a Codex agent's
statement of its own model was wrong (plan-smith-lab N03). Wired skill: z-lab `plan-smith-lab/latest-model-1.8.0/` (N01, N02) and `latest-model-1.8.0-own-id/` (N03).

## Codex compatibility evidence — 1.7.0

See z-lab `plan-smith-lab/codex-compat-1.7.0/` (S01, S02) and the shared
`plugin-platform-lab/codex-final-0.158.0/` packaging/installer checks. These records
cover host wiring and the named fixture paths, not quality improvements. Keep the
existing workflow invariants when changing an adapter.

Writer settings are `PLAN_SMITH_CODEX_MODEL` and `PLAN_SMITH_CODEX_EFFORT`; the effort defaults
to the main session's resolved effort, the model per Rule 6. Apply them to every fresh pass; never derive
them from a style name. CLI children use `CXC_MODE=off` only for the delegated role.
See also z-lab `plan-smith-lab/codex-parity-1.7.0/` (S03) for explicit fresh dispatch.
