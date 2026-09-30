# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Why every change is tied to a version bump:** plugins are served from a
version-keyed cache (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`).
Editing a file in the source tree does **not** reach an installed client — the
version has to move. Release 1.1.1 exists for that reason alone.

---

## [1.8.0] - 2026-09-30

### Changed

- The Codex writer defaults to the newest model of the main session's family. `PLAN_SMITH_CODEX_MODEL` accepts a family or model id and is raised to that family's newest; resolution happens before every writer pass, audit and split.
- On Claude Code, each plan-writer call receives the family alias for the main session's own model. A redirected Claude alias stops the step, and the run stamp records the writer id from the run.
- If a Codex main cannot see its own id or family and the setting is unset, it asks for `PLAN_SMITH_CODEX_MODEL` instead of guessing.
- When the resolver reports `catalog not refreshed` inside a sandbox, the Codex main first reruns that one resolver command outside the sandbox before stopping the step.

### Why

A pinned writer model can become stale, and inheriting the main session's id can select an older version. Resolving each dispatch keeps every pass current and makes the run record reflect the model that executed.

Evidence: z-lab `plan-smith-lab/latest-model-1.8.0/` (N01, N02) and `latest-model-1.8.0-own-id/` (N03); shared resolver evidence in `plugin-platform-lab/latest-model-0.159.0/` (L01–L07), `latest-model-r2-0.159.0/` (L04r, L06r, L07r, L08), `latest-model-r3-0.159.0/` (L08i, L09), and `latest-model-r4-0.159.0/` (L02x). N03 took the own-family branch; the stop-and-ask branch was not measured. Also not measured: the redirected-alias stop inside forge (N02 ran without an override; the resolver's stop was measured in L06/L06r and a wired-skill stop only in ux-ui R02); a main on a family other than `sol`; a Codex main escalating the resolver out of its sandbox (L08i shows only that the same stale home refreshed when the lab reran the resolver outside); relay passes, wiring audits and splits; an older Claude main id; and model quality.

## [1.7.0] - 2026-09-29

### Added

- Codex manifest and host adapter for questions, fresh plan writers, relay passes, audits and lossless splits. Both hosts share the original frame/style library and artifact contracts.

- Configurable Codex writer model and reasoning effort, recorded before every isolated pass; delegated CLI writers disable CXC orchestration for that child.

### Why

Codex must dispatch an independent writer without relying on Claude's registered Task agent.

Evidence: z-lab `plan-smith-lab/codex-compat-1.7.0/` (S01, S02). Compatibility checks cover the recorded fixtures, not
comparative model quality or every browser/device environment.
Additional setting-parity evidence: z-lab `plan-smith-lab/codex-parity-1.7.0/` (S03).

## [1.6.0] — 2026-09-28

A plan over 20,000 characters now arrives as an index plus ordered parts. No change to frames,
styles, the packet contract, the quality gates, or the wiring audit.

### Added

- **Stage 2d — split.** After the plan is final (and, for build-outs, after the Stage 2c additions),
  the main agent measures it with `wc -m`. Over 20,000 characters, a fresh `plan-writer` in split
  mode moves it into `plans/<slug>/plan.md` — an index that holds pointers only — and
  `plans/<slug>/parts/<category>_<A0–Z99>.md`, where the letter is the phase and the number the order
  within it, and every part ends with a pointer to the next.
- `references/split.md` — when to split, the main agent's procedure, and the protocol the writer
  receives verbatim: every non-empty line moves unchanged and in order, cuts fall only at headings or
  between steps, and the only new lines are the index block and two navigation lines per part.
- `scripts/split-check.py` — confirms a split is lossless and well-formed (every line reappears once and
  in order; names, order and next-pointers valid; every part starts at a heading or list item and leaves
  no code fence open). `--self-test` runs its own fixtures. On two failed
  checks the main agent restores the unsplit plan and relays it instead.

### Changed

- Stage 3 relays a split plan as the index followed by every part, in order, each with its path —
  design invariant 4 (verbatim relay) is unchanged in substance; its wording now covers split plans.
- `plan-writer` gains a split mode: it writes the index and the parts and nothing else, and reports
  defects instead of fixing them.
- The retrospective line records `split N parts` or `unsplit` and the plan's character count. The
  packet template's comment also gains the `model` field Stage 3 already required.
- Divergence variants and relay drafts are never split; an adopted variant over the threshold is copied
  to `plan.md` and split there.

### Why

- Requested by the maintainer for two reasons, both **hypotheses that have not been measured**: a long
  plan read in ordered pieces is less likely to have parts skipped, and pointer-ordered files are easier
  for an agent to work through. Nothing here claims either effect; the retrospective field exists so that
  outcomes can be compared between split and unsplit plans.
- The split comes **after** the gates because every gate and the wiring audit judge the whole plan —
  cross-references such as the load-bearing path's hops span sections, so checking parts one at a time
  would miss exactly what those checks exist for. Moving text instead of rewriting it keeps that judgment
  valid, and a line-by-line check can prove the move, which a rewrite could not offer.
- Characters, not words or lines, because plans are written in the user's language. The 20,000 threshold
  and the 10,000-character part target are (c) declared arbitrary; the first retrospectives that record
  split outcomes replace them.

### Measured before release

z-lab `plan-smith-lab/split-1.6.0/` (repository rule 9): the real `plan-writer` definition, given only the
split protocol, split three corpus plans of 20,344 / 32,073 / 36,970 characters twice each. The checker
passed **6/6 on the first attempt** (S1); parts ranged 6–11 with none over the 10,000-character target
(S2); the plan with 26 code fences was never cut inside a block (S3); each split cost $0.66–1.08 (median
$0.79) and 142–252 s on opus (S6). Splits are not deterministic — the same plan gave 8 and 11 parts (S5).
Not measured: any effect on implementers, the retry path in a real run, the full pipeline with Stage 3
relay, other models.

The checker command lives in SKILL.md, not in `references/split.md`: `${CLAUDE_PLUGIN_ROOT}` is replaced in
SKILL.md text when the skill loads, but a reference file read later keeps it literal and the command
fails with exit 127 (z-lab `plugin-platform-lab/skill-plugin-root-2.1.283/` V01–V02,
`reference-plugin-root-2.1.283/` V03, 3/3 each). A reference that points to the SKILL.md command ran
the script 3/3 (`reference-pointer-2.1.283/` V05).

## [1.5.0] — 2026-09-28

Rename. No change to skill behaviour, frames, styles, the packet contract, or the
`plan-writer` agent — only names and paths moved.

### Changed

- The skill is now `forge`: invoke `/plan-smith:forge` instead of `/plan-smith:plan-smith`.
  The folder moved from `skills/plan-smith/` to `skills/forge/`, and the frontmatter `name` matches.
- The marketplace is now named `bin` (the repository URL is unchanged): install with
  `claude plugin install plan-smith@bin`.

### Why

- With the plugin and the skill sharing one name, the command read `plan-smith:plan-smith`. The
  repository now names every command "subject : action" — plugin = what it works on, skill = a
  verb from a shared vocabulary (`build`, `forge`, `run`, `mode`, `audit`, `review`). `forge` is the
  verb for "distill conversation context into a document". The plugin keeps its established name.
- Changing an invocation name would normally be MAJOR. It ships as MINOR because the marketplace has
  no users yet, so no existing usage breaks.

## [1.4.2] — 2026-08-13

Documentation only. 1.4.1 put the measured economics in the **root** READMEs — which, per this
project's own delivery rule, never reach an installed client: the cache packages `plugins/plan-smith/`
and nothing above it. This release carries the evidence to where users actually read it.

### Added

- "Measured results" section in **both packaged READMEs** (`plugins/plan-smith/README.md`, `.ko.md`):
  total cost to a working artifact 65.5% cheaper (5.38M vs 15.58M tokens, repair loop included),
  the stage split (plan 3.0× dearer, implementations 42% cheaper, repairs 13.5× cheaper), the
  mechanism (defect class: one un-copied symbol versus cross-component contract mismatches, under
  identical repair prompts), the receipts for side effects (phantom versions 5→0, 4/4 reproduction
  consistency, all family CLEARs from plan-smith cells), and the limits in the same breath.

## [1.4.1] — 2026-08-13

Documentation only — the pre-registered outcome of the total-cost experiment, published whichever
way it pointed. It pointed favorably.

### Added

- FAQ entry "Does the token cost pay for itself?" in both root READMEs, carrying the measured
  economics: cost to a **working** artifact with the repair loop included, weak implementer, fixed
  repair-prompt template. The plan costs 3.0× more to write, implementations come out 42% cheaper,
  repairs 13.5× cheaper (the defect classes differ: one un-copied symbol versus cross-component
  contract mismatches), total 65.5% cheaper to four working artifacts — with the limits stated in
  the same breath: tiny repair sample, one task, one weak implementer, and the gap shrinks with
  strong implementers. Raw data and per-chain forensics live in the lab (`plan-smith-lab/tco/`).

### Errata

- The 1.4.1 version-bump commit claimed this content but carried only the version strings: the
  editing script died on a mis-remembered FAQ anchor *after* the bump was staged, and the commit
  went out under a message describing work it did not contain. This commit delivers the claimed
  content. History is not rewritten here; the slip stays visible.

## [1.4.0] — 2026-08-13

The first release **gated by its validation instead of validated after shipping.** The draft sat
uncommitted in the source tree until a pre-registered A/B passed; the rules below were frozen and
committed to the lab before any cell ran.

A review pass had found three defects. The sharpest: **the v1.2/1.3 rule sections never reached the
isolated production writer** — Stage 2's delegation list copies the frame spec, the style directive
and the common template, but not the load-bearing path, verb-sentence, implementer-contract or
machinery-budget sections; the batch harness read frames.md whole and masked this through two
releases. Second, the run stamp lacked the plugin.json location and produced an observed "unknown"
stamp. Third, the residual failure class in transfer testing was **glue recalled instead of copied**
— an undefined `setState`, an unaliased `Composite` — while the one thing made copyable (the CDN URL)
had taken phantom versions from five incidents to zero.

### Added

- **Copyable glue** (machinery budget, weak/unknown implementer): the plan carries **verbatim
  copyable blocks** for the highest-risk connective code — the dependency alias line, a symbol table
  naming each file's public functions with exact signatures, and initial state declarations. Not
  implementation: the plan pinning the joints the implementer would otherwise recall, because what is
  copyable does not get hallucinated. One quality-gate item extended accordingly.

### Fixed

- Stage 2 delegation item 5 now hands the writer, for build-outs, the four specification-rule
  sections verbatim — the writer cannot honor rules it never receives.
- Run stamp names the plugin.json location (`.claude-plugin/plugin.json`) and forbids inferring a
  version from a path, which is exactly what happened in the 1.3 validation run.

### Gate verdict (pre-registered, run `wf_32c69d79-148`, before this commit existed)

Informed opus baseline vs this draft, haiku implementing four times each, plan as the only input.
Primary metric — glue deaths (uncaught missing-symbol errors): **1 vs 2**. Secondary — ladder median:
**L5 vs a L1/L5 split**, and the glue arm produced the test family's **first stage CLEAR**. Both
pre-registered conditions held, so this release exists. Recorded with the same honesty as before:
n=4, one task, one weak model — and the glue arm's one remaining death was itself a glue symbol
(`worldSettled`), so the clause reduced the class without eliminating it.

## [1.3.0] — 2026-08-13

Driven by the first experiment in which someone other than the planner implemented the plan —
and the result **inverted**. Nine cells: the weakest model implemented three times each from its own
plan, from a strong model's baseline plan, and from a strong model's 1.2.0 plan-smith plan. Handed the
strong plans, it died **at the build step** in five of six cells — earlier than on its own modest plan —
each time failing to reproduce one demanded part: a phantom `@types` pin (twice), a tsconfig that
references a file never written (twice), a deep import that does not exist (once). The 1.2.0 plan,
heaviest of the three, failed all three replicas while its implementer notes announced the validation
chain ready. The implementer's own plan had one moving part, a CDN URL; the one replica that got it
right reached the fire level immediately.

The lesson: **every part a plan demands is one more surface a weak implementer can fail to
reproduce.** A plan optimized for completeness is optimized for a reader who can absorb machinery;
weak implementers need plans optimized for reproducibility.

### Added

- **Gate 0's second axis — who implements this?** The packet records the implementer (resolved model
  id, a person, or "unknown"); when unknown, it is a `⚠guess` resolved at the confirmation gate and
  budgeted for the weakest plausible implementer until then.
- **`### The machinery budget`** (`frames.md`) — deliverable type picks the frame, the implementer
  picks the *weight*. Weak or unknown implementer: **no build chain**, few files, no
  config-referencing-config, every dependency a **complete copyable string** (the full URL with exact
  version — recall hallucinates: the same phantom `matter-js 2.0.20` appeared across three independent
  runs), and no command-form completion criteria the implementer cannot run — it will write
  "validation chain ready" over an artifact that fails the chain's first step. Strong implementer:
  1.2.0 discipline applies as written.
- One quality-gate item binding the plan's demanded machinery to the packet's implementer profile.

### Pre-registered validation (recorded before the verdict exists)

The cheapest rival to this clause is a single packet line naming the implementer. The acceptance test
therefore compares against an **informed baseline**, not an ignorant one: same weak implementer, n=3,
arm A = baseline plan told who implements, arm B = 1.3.0 plan-smith. The clause earns its place only
if B beats A on the graded ladder; if B ≈ A, this changelog gets that verdict appended — the release
stays either way, because history is not rewritten here.

### Validation verdict (2026-08-13, same day — run `wf_c2740e64-b67`)

**B ≈ A.** Ladder medians tied at L5 (A: L5/L5/L0, B: L5/L1/L5; one implementer slip each side).
The clause's *standalone* additive effect was not observed at n=3. What the run did show is the size
of the information effect the clause rides on: uninformed opus plans had put the weak implementer at
**below-build** (5 of 6 cells dead at install/build); one line naming the implementer moved both arms
to **median L5**, with both planners independently converging on no-build, globals-over-modules,
pinned real-version CDN — the machinery budget's own prescriptions. The knowledge was in the model;
the clause codifies it rather than adds to it. Phantom dependency versions: zero in six cells,
against five phantom incidents in the uninformed run — a copyable URL leaves recall nothing to
hallucinate. The clause stays as codification with its packet field doing the measurable work, and
this verdict is the recorded reason no stronger claim is made.

## [1.2.0] — 2026-08-01

The second release driven by a failure of this plugin's own output — and this time the plan
**passed every existing gate.** A controlled round-2 A/B scored a `spec-coverage` build-out plan
**7/7** on a rubric fixed before the run: Gate 0 fired, routing was correct, all seven required
surfaces were specified, no requirement was demoted, the stack was named with what it bought.
The artifact built from it had a dead primary interaction.

Reading the code showed why, and it was not a missing part. The launch path crossed five layers,
every layer existed, and each one carried a guard. Nothing in the plan ever wrote the chain down,
so nobody checked that the guards can all hold at the same moment. **1.1 taught the pipeline to
stop dropping surfaces; 1.2 teaches it to specify that the surfaces are connected.**

Two more findings from the same round shaped the rest of this release: one plan reached 3,026 words
of which **67% were table rows**, leaving ~334 words of executable instruction; and one
implementation resurrected an alternative its plan had rejected by name, declaring a dependency
version that had never been published.

### Added

- **`## Load-bearing path`** — a required section for build-outs. Pick the one path whose failure
  makes the artifact pointless (a game's launch, a form's submit-to-persisted, a pipeline's first
  record landing, an approval flow's first request) and write it as a chain of **≤5 hops**. Every hop
  carries three columns: its name, the condition that must hold for it to pass, and **where that
  condition first becomes true**. Followed by a **cold-start table** covering every condition named
  in those hops — initial value, who changes it, when. **A blank cell is a defect in the plan.**
  Two hard rules: a hop whose "first becomes true at" cannot be filled means the plan is unfinished,
  and a hop may only name symbols the plan commits to creating elsewhere.
- **Verb sentences** — every requirement marked `build` owes one sentence **outside any table**:
  *when ⟨actor⟩ does ⟨action⟩, ⟨observable result⟩ happens; its absence shows up as ⟨symptom⟩*.
  Rows are the ledger; sentences are the instruction. Rows without sentences are a stub inventory.
- **`## Implementer contract`** — the plan's last and shortest section, for what must survive the gap
  to someone who never saw the conversation: rejections carry **revival triggers** (an unexplained
  prohibition gets overturned), dependencies are pinned to **versions that resolve**, and any guarantee
  the stack was bought for is claimed with **the command and its exit status in "done"**, not as a
  property in prose. Three round-2 plans bought compile-time checking and shipped code that did not
  compile, because nothing in "done" referred to the build.
- **Stage 2c — wiring audit** (`SKILL.md`) — for build-outs, a **second, fresh** `plan-writer` instance
  audits the finished plan against five document-level questions and writes `wiring-audit.md`; the main
  agent then has the writer make the minimal additions. An author cannot audit their own omissions,
  which is why the auditor is a different instance. Roughly **+20–35% tokens** on the writing stage,
  spent on the one defect class that reading cannot see. Skipped for decision documents.
- **`Load-bearing path candidate`** in the packet template, and input-contract item 7 for `plan-writer`
  — the main agent has the session context and is better placed to know what the user came for; the
  writer owns the final call but must name the path it chose instead.
- Three quality-gate items and two `spec-coverage` required components wired to the above.

### Deliberately not added

An instruction to "review whether the code will actually work". It is unfalsifiable (an agent can
assert it), it arrives after the cost is sunk, and in two validation corpora self-review language was
counted as credit for defects that were never fixed. A plan cannot verify anything — so every rule in
this release is checkable **by reading the plan against itself**, and none of them asks anyone to build,
run, open or look at the artifact.

## [1.1.3] — 2026-08-01

Documentation only. No change to skill behaviour, frames, or agent definitions.

### Added

- `CHANGELOG.md` — this file. Release history reconstructed from
  `git log -p -- plugins/plan-smith/.claude-plugin/plugin.json`, which is the
  only authority on where each version boundary actually fell.
- A repo rule (local, untracked) requiring that `CHANGELOG.md` and both READMEs
  be updated as part of any version bump, rather than after it.

### Notes

- `frames.md` is unchanged at 364 lines / **26 frames** (verified by counting
  `### ` headings: 28 total, minus `Gate 0` and `The four predicates`, which are
  routing sections rather than frames).

## [1.1.2] — 2026-07-29

### Added

- **Run stamp in the context packet** (`packet-template.md`) — the packet's first
  section now records the plugin version read from `plugin.json`, a `frames.md`
  fingerprint, the **resolved model ids** of both the main agent and the writer,
  and whether the run was interactive or scripted.
- `SKILL.md` step **2b** makes filling the stamp the first thing that happens in
  the packet.

### Why

Aliases are not versions. `opus` resolved to `claude-opus-4-8` on 2026-07-25 and
to `claude-opus-5` on 2026-07-29, and the pipeline's own A/B lost the model
version of half its artifacts — two rounds were nearly mislabelled and had to be
recovered from raw transcripts. A plan that cannot name what produced it is not
comparable to the next one.

## [1.1.1] — 2026-07-28

### Changed

- Version bump only, so installed clients pull the clauses added after 1.1.0.

### Why

The changes in the preceding commit (document budget, Gate 0 tie-break) were
written into the source tree but the installed plugin kept serving 1.1.0 from
cache while reporting itself up to date. The bump is the delivery mechanism, not
a code change.

## [1.1.0] — 2026-07-28

The first release driven by a **failure of this plugin's own output**. A
controlled A/B on a spec-complete task (browser game: 10 stages, physics loop, a
named UI requirement) had a `backward`-framed plan **lose to an unframed
baseline** — 38% longer, 41% less implementable instruction (777 → 460 words),
~37% of the body narrating its own methodology, and sound / particles /
persistence / stack absent from the shipped code.

### Added

- **`Gate 0` routing** (`frames.md`, `SKILL.md` step 1b) — before any frame is
  chosen, ask *if this plan is followed literally, is the danger that we chose
  wrong, or that we left things out?* A complete spec whose risk is omission is a
  **build-out** and routes to `spec-coverage`; other frames may be borrowed for a
  single genuinely open sub-decision, and the borrow is recorded.
  **Tie-break: when genuinely unsure, choose build-out** — the two misroutings do
  not cost the same. A build-out sent to a narrowing frame silently omits
  requirements; a decision sent to `spec-coverage` merely leaves one cell shallow.
- **`spec-coverage` frame** (26th frame) — requirement × surface completeness
  matrix, with required components: a no-silent-drop ledger
  (`build` / `defer (+trigger)` / `n-a (+reason)`, blank = defect), a **quality
  floor per surface**, a **content axis** distinct from the mechanics axis, a
  dependency-ordered thin end-to-end slice whose polish step is **named**, and a
  **named delivery stack with the reason it was bought**.
- **Document budget** rule — methodology argument belongs in the packet; in the
  plan the frame and style get *the header line only*. One test governs every
  paragraph: would a reader who must build this be worse off if it were deleted?
  A matching quality-gate item asks whether the body is **majority implementable
  instruction**.
- Deliverable type (from Gate 0) added to the user confirmation gate.

### Changed

- **Off-anchor clause rewritten** — a requirement absent from the anchors may not
  *bend the architecture*, but it **stays in scope and still ships**. Two hard
  bans: never re-classify a stated requirement as decorative/cosmetic to keep it
  off the anchor list (the anchor list derives decisions, it is not a scope
  filter), and never leave an uncovered requirement in silence — it gets an
  explicit build step or an explicit deferral with a trigger.
- New watch-out: **canon ends the derivation, not the specification.** Noting "this
  choice is canonical, not derived" is honest, but the plan must still state the
  choice and what it buys ("TypeScript, so the stage schema and the state machine
  are checkable"). Observed failure: a plan logged the stack as canon and then
  contained **zero** stack sentences, so implementer defaults filled the vacuum.
- New failure mode recorded: **the anchor list silently becomes the scope list** —
  an item killed as an *alternative* is never re-instated as a *feature*. One plan
  killed "score-threshold clear" as a judgment rule, after which score existed in
  the document only as a dead alternative and the score/star system was never
  specified.

## [1.0.0] — 2026-07-19

Initial release.

### Added

- **Two-stage pipeline** — the main agent distills the whole conversation into a
  self-contained context packet (goals, hard constraints, rejected alternatives);
  a clean-context `plan-writer` agent drafts the plan; the main agent relays the
  plan file verbatim.
- **`plan-writer` agent** restricted to `Read / Glob / Grep / Write` — read-only
  toward the codebase, writes exactly one output file.
- **Frame library** (`frames.md`) — reasoning frames in 6 families, each with a
  starting point, **required components** (the parts whose absence turns the frame
  into decoration), failure mode, and corpus-derived watch-outs, plus four routing
  predicates.
- **Style library** (`styles.md`) — `opus-style`, `fable-style`, and `relay`,
  distilled from a controlled 26-plan experiment run under two model fingerprints
  and stress-tested against a 100-plan validation corpus. Styles are prompt
  discipline, not model selection.
- **Packet template** (`packet-template.md`), skill entry point (`SKILL.md`),
  bilingual READMEs (`README.md` / `README.ko.md`), MIT licence, and a local
  directory marketplace (`.claude-plugin/marketplace.json`).

---

## Open items (not scheduled)

- **`analogical` frame is absent.** It existed in the original planning playground
  and was dropped when `frames.md` was distilled; `spec-coverage` took the 26th
  slot. A 76-topic corpus generated against 1.1.2 had to fall back to the
  playground's own description for that one topic. Restoring it would change plugin
  behaviour and therefore make any corpus generated afterwards a different spec, so
  it is deliberately left undone pending a decision.
- **`relay` is a single observation.** It produced the strongest artifact in the
  experiment it came from, and the pipeline still treats it as promising rather
  than proven. Retrospectives accumulate the evidence.

[1.4.2]: https://github.com/zeriong/plan-smith/releases/tag/v1.4.2
[1.4.1]: https://github.com/zeriong/plan-smith/releases/tag/v1.4.1
[1.4.0]: https://github.com/zeriong/plan-smith/releases/tag/v1.4.0
[1.3.0]: https://github.com/zeriong/plan-smith/releases/tag/v1.3.0
[1.2.0]: https://github.com/zeriong/plan-smith/releases/tag/v1.2.0
[1.1.3]: https://github.com/zeriong/plan-smith/releases/tag/v1.1.3
[1.1.2]: https://github.com/zeriong/plan-smith/releases/tag/v1.1.2
[1.1.1]: https://github.com/zeriong/plan-smith/releases/tag/v1.1.1
[1.1.0]: https://github.com/zeriong/plan-smith/releases/tag/v1.1.0
[1.0.0]: https://github.com/zeriong/plan-smith/releases/tag/v1.0.0
