# styles.md — Writing Styles (Opus / Fable / Relay)

> Provenance: two full 26-plan sets were written under the same frame instructions by two models with distinct planning fingerprints, then comparatively audited; a later 2×50-plan validation corpus confirmed both directives are followable under load and supplied the integrity rules below. The audit distilled each fingerprint into a reproducible **writing directive** — a style is intended as a prompt-level discipline, not a model selection. Caveat: that portability is a design hypothesis, not a verified fact — in both corpora each style only ever ran on the model it was distilled from (zero cross runs), so record the executing model in retrospectives (SKILL.md Stage 3) and let real usage test it.
>
> The two styles are complementary by construction: **opus-style** ("the disciplined conformist") optimizes breadth, adoptability, and honest self-report; **fable-style** ("the auditing revisionist") optimizes structural re-definition, rule-encoded judgment, and adversarial depth. The experiment's strongest artifacts came from running them **in sequence (relay)** — the conformist's confession log became the revisionist's improvement backlog.

---

## opus-style — the disciplined conformist

Use when: first drafts, stakeholder-facing documents, coverage-critical risk reviews, anything an organization must digest — and always as **pass 1 of relay**.

Directives for the writer:

1. **Entry ritual — interrogate yourself first.** Open the work (in your head, and briefly in the plan's framing) with: "given this task, my reflexive habit would be X — and X is exactly what the frame forbids/demands." Name your own inertia before writing. This self-audit is what keeps the frame honest.
2. **Obey the frame literally.** Follow the frame's mandated starting point and structure to the letter. When the frame and your instinct conflict, the frame wins; record the conflict instead of resolving it silently.
3. **Coverage before depth.** Prefer completeness of the risk/assumption/alternative space over depth on any single item. Run a checklist sweep at the end: "what category did I not mention at all?" A dropped category is worse than a shallow one.
4. **Land on adoptable practice.** Converge on solutions an organization can actually absorb — pilots, incremental rollouts, verify-then-expand. Boldness is not this style's job.
5. **Rejected alternatives get revival conditions.** When you reject an option, state the condition under which the rejection flips.
6. **Plain naming, compact prose.** Modest compound names ("pain score", "temptation log") over coined jargon. Keep the document short and readable; narrative closings, not epigrams.
7. **Confession log — mandatory.** End the plan with a section titled **"Frame deviations & habit regressions"**: where you drifted back to reflexive planning, which section is weakest and why, what you would attack if you were the reviewer (name the specific section), and any place you chose convention over the frame. Be specific and honest — in relay mode this section is the *fuel* for pass 2, and the experiment showed the confession's quality caps the next pass's improvement ceiling. Three integrity rules (the validation corpus caught confessions drifting into performance):
   - **Anchor every item to the body.** Each confessed defect must point to the section/sentence it lives in, checked against the *final* text — the corpus produced confessions of defects the body had already fixed, which poison a relay backlog with false positives.
   - **No boilerplate.** Time-axis / ascending-narrative regression is presumed by default; confess it only with task-specific content ("steps 1–4 are per-pipeline parallel but numbered as a ladder"), never as the ritual sentence — 40 of 50 logs repeating the same line made the channel noise.
   - **No deferral outside relay.** Unless explicitly told this is relay pass 1, there is no "next pass" — naming one ("a fable pass would pin these thresholds") is a license to skip work. A defect you know how to fix (an operational definition, a gate threshold) gets one direct fix attempt *before* it may be confessed; confess only what survives the attempt.
8. **Numbers carry their measurement.** Every number in the done criteria gets one line: who measures it, with what, how. An arbitrary value is marked arbitrary and given a lifespan (its first-measurement replacement point) — but the lifespan does not waive the definition duty: "we'll measure it later" laundering was this style's most repeated leak (39 of 50 validation logs).

Boundaries (self-audit before returning):
- Did the convergence instinct pick a "safe default" (a pilot, a phased rollout) where the task actually needed a structural answer? If suspected, say so in the confession.
- Did the ascending-narrative habit (every week/phase strictly bigger than the last) sneak into a domain where regression is normal? Flag it.
- Did you export the hardest sub-problem into a bolded load-bearing assumption? Bolding is not a defense: any "everything hangs on this" assumption needs (a) its cheapest early verification action and (b) a one-line fallback path for the world where it breaks.

## fable-style — the auditing revisionist

Use when: adversarial review, red-teaming an existing plan, designs squeezed by contradictory constraints, plans whose operating rules matter more than prose (runbooks, gates, roadmaps) — and always as **pass 2 of relay**.

Directives for the writer:

1. **Entry ritual — interrogate the frame first.** Open with: "this frame's failure modes are A and B; here is how this plan will avoid becoming decoration." Diagnose the tool before using it.
2. **Attempt at least one level shift.** Before accepting the problem as posed, try to re-define its representational form once: cache → build artifact, weekly schedule → state machine, question → probe, feature → file format. If the shift fails, keep the standard form and say why — a plan that keeps the standard form is not a lesser plan. If it succeeds, the plan changes category, not degree. Honesty clause: if the shifted form converges with domain canon or the industry's standard answer, book it as *canon re-arrival*, not as a shift. (In a 50-plan validation run the failure branch never fired once — a 100% shift rate means the directive is producing shifts, not discovering them.)
3. **Fix meaning before numbers.** Any scale gets an operational definition ("damage 5 = irrecoverable money movement"); any allocation gets a goal sentence first ("an allocation debate is a goal debate in disguise"). Numbers without fixed meaning are theater. Meaning-fixing does not manufacture grounded values — mark every hand-set number as an *initial value* with its replacement trigger (which first measurement replaces it, when, read by whom); where even an initial value would anchor falsely, an honest blank beats a confident guess.
4. **Encode judgment as rules.** Wherever a future decision could be political, deferred, or panic-driven, convert it now into a gate with a default, a threshold with a pre-committed action, a circuit breaker, or a transition rule. "Only a gate with a default is a working gate."
5. **Apply the frame recursively.** When the frame kills an option and a survivor takes its place, run the frame again on the survivor (the second ledger, the audit of the observation plan itself).
6. **Search the gaps between units.** The decisive point is often *between* the stages everyone models — between sessions, between the first and second contribution, at chain merge points. Spend one explicit pass looking there.
7. **Attribution accounting.** For each structural device in the plan, note (briefly, in the plan's notes or your return message) where it came from: the frame's demand, this style's discipline, or domain canon. This is the standalone version of relay's T6 self-interrogation — in validation it was the practice most correlated with honest, body-consistent self-reports.
8. **Mandatory self-boundaries** (the experiment's recorded costs of this style — audit before returning):
   - **Coverage audit:** structural immersion loses breadth (a narrative autopsy once silently dropped an entire regulatory category). Not a mental sweep — write it as a fixed-title section ("Coverage self-audit") in the plan, and give every caught item a landing place (an assumption, a risk, or a step-0 entry). In validation only ~40% of plans showed the sweep at all, and the ones that did recovered real categories (legal/regulatory, off-curve exits).
   - **Operational-burden audit:** rule-encoding can bury the executor (a burnout-recovery state machine whose daily check-ins were themselves a load). Ask: does the person running this plan have the cognitive slack for my rules? If not, simplify — a conventional skeleton carrying only your best components may beat your full structure. The audit only counts if it *removes* at least one rule or states why none could go — an audit that ends by adding a cap ("≤30 min/week upkeep") has added another rule, not reduced the load.
   - **Jargon budget:** each new coinage gets an operational definition in its first sentence; before returning, replace any undefined coinage with plain words. Epigrams are seasoning, not structure.

## Shared boundary — do not perform the fingerprint

Both styles were distilled from real corpora, and writers who know these directives tend to *perform* them. Three rules keep the discipline honest:
- Never invoke the other style or another pass by name in the plan or its notes ("a fable pass would dig here") — outside an explicitly declared relay there is no other pass, and inside one, do your own pass's work.
- Cite a style directive only together with the concrete decision it changed; a directive quoted without a changed decision is costume.
- Self-assess with body coordinates, not grade words: "§3 shows the buffer component carried load", not "fidelity: high". Self-reports are narratives — every claimed strength or defect must be checkable against the final text.

## relay — draft, confess, audit, revise (two passes)

Use when: high-stakes or hard-to-reverse decisions, plans worth double cost, anything the user will act on for months. This mode reproduces the experiment's strongest observed pipeline: **an honest first pass whose self-criticism becomes the second pass's backlog.** (Evidence grade: observed once, in a sequential — i.e. contaminated — run; the validation corpus did not re-test relay. Treat it as promising-but-unverified until Stage 3 retrospectives accumulate.)

**Pass 1 — opus-style**, output `draft.md`. All opus-style directives apply; the confession log is non-negotiable.

**Pass 2 — fable-style**, output `plan.md` + `audit.md`. All fable-style directives apply, plus the protocol below.

### relay pass-2 protocol

> This subsection — from here to the end of rule 5 — is what the main agent pastes **verbatim** into the pass-2 prompt, together with the fable-style directive.

1. **The confession is your backlog — after triage.** Read the draft's "Frame deviations & habit regressions" section first, and classify every item against the draft's body: **present in body** (real backlog) / **already resolved in body** (the log described an earlier draft — do not re-fix; re-fixing a resolved item is T6 by definition) / **boilerplate** (generic regression talk — ignore). Validation found confessions miscalibrated in *both* directions, including confessed defects the body had already fixed.
2. **Independent rationale for every divergence.** Wherever you change a decision of the draft, state a reason that stands without referencing the draft ("the draft chose X, but Y because <evidence>", where <evidence> would convince someone who never saw the draft).
3. **Contamination audit (T1–T6) — write it into audit.md.** Classify every convergence/divergence with the draft:
   - T1 arithmetic-forced convergence (the math decides; agreement means nothing)
   - T2 instruction-forced convergence (the frame/template decides)
   - T3 domain-canon convergence (industry common sense)
   - T4 productive borrowing (the draft's confession triggered this improvement — credit it)
   - T5 undecidable (could be anchoring, could be independent)
   - **T6 differentiation reflex** — interrogate yourself: "am I diverging here because it is better, or because it is *different*?" Divergences that survive T6 need the independent rationale of rule 2; those that don't survive get reverted to the draft's choice.
4. **Revision does not always win.** Execution burden, communication cost, and organizational digestibility are valid grounds to keep the draft's shape. Record kept decisions with the same care as changed ones.
5. **audit.md format:** `## Changed decisions` (each: what / draft's version / new version / independent rationale / T-classification), `## Kept decisions` (each: what / why the draft wins), `## Confession follow-up` (which confessed items were addressed, which were judged fine as-is).

### main-agent duties after pass 2 (not part of the writer's paste)

The main agent then relays `plan.md` verbatim, appends the audit's changed/kept lists, and **delegates any remaining draft-vs-revision choice points to the user** — the final merge authority is human.

---

## Auto-routing (style=auto)

Signals → style. When signals conflict, ask the user (per the skill's global rule). Record the chosen style *and the rationale* in the packet.

| Signal in the task/context | Style |
|---|---|
| First draft of anything; document consumed mainly by people (proposal, stakeholder brief); breadth of risk coverage is the point | **opus** |
| Reviewing/red-teaming an existing plan; constraints look contradictory; the artifact is operating rules (runbook, gate design, allocation with cut lines); the problem smells "stuck" and may need re-framing | **fable** |
| Hard to reverse, high blast radius, months of execution hang on it; the user signals "make it thorough / this matters" | **relay** |
| Default when nothing above fires | **opus** for human-consumed plans, **fable** for system/ops-consumed plans |

Two reminders:
- A style is a writing discipline, **not** a model choice. Do not switch models to switch styles. (Discipline-portability across models is still a hypothesis — see Provenance; the retrospective's model field is what will eventually confirm or kill it.)
- Style names are internal shorthand for the two validated fingerprints; in user-facing text, describe them by behavior ("coverage-first disciplined draft" / "structure-auditing revision") rather than assuming the user knows the lore.
