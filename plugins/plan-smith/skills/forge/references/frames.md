# frames.md — Reasoning Frame Library

> Provenance: a 26-domain × 26-frame empirical experiment (two full plan sets written under different design styles) and its comparative audit. Each frame's **required components** are the parts whose absence was observed to degrade the frame into decoration. **Applying a frame without its required components counts as not applying it.**
>
> A second validation corpus (25 frames × 2 scenarios × 2 writers = 100 plans + reasoning logs) later stress-tested every entry. The components held under load almost everywhere; the corpus's contributions are woven in below — load-bearing ones as new required components, second-order ones as **Watch-outs** lines. Three cross-cutting cautions from it:
> - **Example values are form, not content.** Inline examples (the 90-second triage, "blast radius × recoverability") were observed being copied verbatim as answers. Re-derive every scale and number from the domain at hand.
> - **Borrow openly.** Borrowing another frame's component is normal — expected within the no-slack trio (triage / checklist / safety-net) — but record the borrowing and its source; unattributed borrowing corrupts frame-fidelity retrospectives.
> - Validation of this kind shows the specs are *implementable*, not that they are *right* — the corpus was itself written from these specs, so treat user retrospectives (SKILL.md Stage 3) as the only accumulating correctness signal.
>
> A later controlled A/B added a fourth caution, and it is the sharpest: **frames are decision instruments; a build-out needs coverage.** Same model, same fully-specified task (browser game: 10 stages, a physics loop, a named UI requirement), one plan framed with `backward` and one unframed. The framed plan ran 38% longer yet carried 41% less implementable instruction (777 → 460 words), spent ~37% of its body narrating its own methodology to earn — by its own confession — three paragraphs of design value, explicitly cut sound / particles / mobile as "off-anchor", went silent on score, stars, background, persistence **and the stack**, and re-labelled one of the user's three stated requirements "cosmetic". In code: the unframed baseline shipped `audio.ts`, `effects.ts`, `storage.ts`, `types.ts`; the framed one had no counterpart to any of them. Run **Gate 0** below before choosing any frame.

## Frame routing

### Gate 0 — decision document, or build-out document?

Run this **before** the predicates. Ask: *if this plan is followed literally, is the danger that we chose wrong, or that we left things out?*

- **Decision** — a real either/or is open, or the cause / market / executor is unknown → the four predicates below pick the frame.
- **Build-out** — the spec is already complete and the danger is omission, thin surfaces and integration → route to **`spec-coverage`**, and pull in another frame only as a sub-tool for one genuinely open sub-decision (record the borrow).

Most narrowing frames — `backward`'s off-anchor clause, `delete-first`, `api-first`'s contract — are instruments for *cutting*. Aimed at an already-complete spec they license the omission of everything they did not happen to select, and the plan loses to an ordinary unframed engineering plan. Record Gate 0's answer and its reason in the packet.

A task can be both: a build-out containing one hard trade-off. Then `spec-coverage` owns the document and the other frame owns that one section.

**Tie-break — when genuinely unsure, choose build-out.** The two misroutings do not cost the same. A build-out sent to a narrowing frame **silently omits requirements**, and the loss surfaces only after implementation (in the observed case: no audio, no effects, no persistence layer at all). A decision sent to `spec-coverage` merely leaves one cell shallow, and the borrow rule above repairs it inside the same document. Asymmetric costs, so lean to the recoverable error.

**Second axis — who implements this?** Deliverable type picks the frame; the implementer picks the **weight**. Record in the packet who will build from this plan (a resolved model id, a person, or "unknown") and apply **the machinery budget** (see the section of that name near the end of this file). A weak or unknown implementer gets the plan that demands the least machinery, however capable the planner is — observed: plans a strong model wrote for itself, handed to a weak implementer, killed it **at the build step**, earlier than its own modest plan did.

### The four predicates

Pick frames by these four predicates, not by domain nouns:

| Predicate | Question | Direction |
|---|---|---|
| ① Location of uncertainty | What is unknown — the cause? the market's response? the executor themself? | Cause unknown → Diagnostic family. Nothing unknown, execution only → **Gate 0 decides**: a build-out goes to `spec-coverage`; Backward / Form only where a choice is genuinely still open |
| ② Rigidity of resources | Are time / money / staff / runway fixed? | Fixed or contradictory → Quantitative & Constraint family |
| ③ Executor's cognitive slack | Can the executor deliberate at execution time (outage, disaster, burnout)? | No slack → reduction / tiering / safety-net frames |
| ④ Scale agreeability | Can a severity / value / goal scale be agreed upon? | If not, quantitative / negative / verdict frames degenerate into taste wars — use multi-perspective or observation frames instead |

When several apply: the predicate producing the largest risk wins. Still ambiguous → **present the top 2 candidates with rationale and let the user choose.**

Domain hints (advisory only; predicates win):
- Greenfield design → backward / api-first / constraint-first
- Legacy & refactoring → min-diff / middle-out
- Debugging & incidents → hypothesis-loop / triage
- Business & product → premortem / unit-economics / observe-first / persona-lens
- Games & experience design → emotion-curve / failure-first
- Learning, career, personal → misconception-first / option-parallel / safety-net
- Operations, events, community → critical-path / incentive-audit / checklist

Predicate-③ frames (triage / checklist / safety-net) share components — transition asymmetry, judgment-word audits, sensory firing conditions travel freely between them. Such borrowing is a normal combination, not a purity violation; just record the source.

---

## A. Backward family — start from the destination

Shared principle: the quality of backward reasoning comes not from the direction but from the **expressiveness of the anchor**. Propositions give verdicts, narratives give causality, curves give intervals, graphs give structure.

### backward — acceptance-criteria back-chaining
- Starting point: fix at most 5 verifiable final acceptance criteria at the very top of the document, and derive every technology/design choice by working backward from them only.
- Required components:
  - **Anchor qualification test** — an anchor is a condition whose failure causes maximal rework; decorative criteria don't qualify.
  - **Off-anchor demands: architecture-only disqualification** — a requirement absent from the anchors may not *bend the architecture*; it nevertheless **stays in scope and still ships**. Write both halves, because the second half is the one that gets dropped. Two hard bans: (1) never re-classify a *stated* requirement as decorative / cosmetic to keep it off the anchor list — the anchor list derives decisions, it is not a scope filter; (2) never leave an uncovered requirement in silence — it gets an explicit build step or an explicit deferral with a trigger.
  - **Anchor intersection pass** — overlay the anchors pairwise once for collision points (long-offline retention vs GC) and mutual-support points; the best decisions come from *between* anchors, and a discovered dependency (one anchor roofing the others) dictates execution order.
- Failure mode: back-chaining toward a predetermined conclusion. Prevention: for each criterion, write down explicitly *which alternatives it kills*.
- Second failure mode (observed, costly): **the anchor list silently becomes the scope list.** Everything off-anchor goes unbuilt, and an item killed as an *alternative* is never re-instated as a *feature* — one plan killed "score-threshold clear" as a judgment rule, after which "score" existed in the document only as a dead alternative and the score/star system was never specified at all. Prevention: after the kills-list, sweep the spec once and mark **every** requirement build / defer; a requirement that appears in the plan only as a rejected alternative is a defect, not a decision.
- Watch-outs: audit each criterion's **resolution** too ("would a coarser granularity still satisfy the purpose, or did this flow backward from the preferred solution?" — the kills-list audits alternatives, not granularity); **pathless anchors** — every anchor must appear in ≥1 step as preparation + verification, not only on judgment day; **measurability bias** — the qualification test selects measurable conditions, so close with one sweep ("which decisive category has no anchor because it resists measurement?"); where a canonical answer already dominates the domain, the frame's value shifts from producing the answer to drawing the boundary where the canon is *not* forced; **canon ends the derivation, not the specification** — noting "this choice is canonical, not derived" is honest, but the plan must still *state the choice and what it is bought for* ("TypeScript, so the stage schema and the state machine are checkable"). Observed failure: a plan logged the stack as canon and then contained **zero** stack sentences, so the implementer's defaults filled the vacuum (a CDN script tag plus a `document.write` fallback to a vendored file nobody created), and the plan's own self-declared highest-value item — a schema keystone — shipped with nothing enforcing it.
- Lightweight variant (low reuse threshold): just "write the completion criteria at the top of the document first" captures half the value.

### premortem — autopsy back-construction
- Starting point: take "N months from now, this plan has failed" as an accomplished fact, write the autopsy report first, then reverse-construct the plan to prevent the causes of death.
- Required components:
  - **Tense lock** — not "it might fail" but "it is dead — why?". If the death has no declarer and no moment (a quiet stall, "temporarily paused"), that is itself a cause of death; the plan needs a termination/landing rule with a default.
  - **Narrative + checklist pairing** — a chronological narrative finds causal chains and novel causes; a checklist pass protects coverage. Either alone is half a frame.
  - **Sweep with a pass criterion + absorption duty** — the checklist sweep must find ≥1 cause absent from the narrative (else it failed — change categories and retry), and every found category must be wired into a step/gate/risk (found-but-unabsorbed is still a miss).
- Failure mode: narrative immersion eats coverage (in the experiment, a whole regulatory-risk category was silently dropped). Always close with the checklist sweep.
- Watch-outs: fix the sweep's category list *before* writing the narrative (or use a narrative-independent standard list: regulatory/legal, money, security, testing, organization, health, users) — categories derived from the narrative make the coverage guarantee circular; the tense lock demands concrete numbers and those numbers are fiction — open the autopsy with one sentence declaring them narrative devices, or readers circulate them as estimates.

### emotion-curve — experience-curve back-derivation
- Starting point: define the emotional/experiential sequence the user must feel as a curve first, then place the mechanisms that produce each segment by working backward.
- Required components:
  - **Translation into occurrence conditions** — emotions can't be implemented directly; translate to observable specs (attribution clarity, visible proximity-to-goal, friction budgets in numbers).
  - **A curve with valleys** — a monotonically rising curve is the ascending-narrative habit in the frame's clothes; deliberate descents/valleys get their own survival specs.
  - **Domain-of-definition skepticism** — the decisive emotion often occurs *outside* the design unit (between sessions, between steps).
- Failure mode: the curve becomes decoration and discussion regresses to mechanics. Prevention: every feature proposal answers "which segment of the curve is this for?"
- Watch-outs: note *who* can observe the emotion — a zero-slack executor (speaker on stage) needs the spec split into rehearsal-time proxies + a few sensory runtime triggers; back-derivation outputs not only each mechanism but its **planting time** (valley mechanisms needing a precondition are planted before the valley); where observation data exists, make the curve a falsifiable hypothesis (done criteria include the observation that would *reject* it — tags can be attached post-hoc, a rejectable prediction cannot); population labels (D3, D14) must not leak into per-person triggers — fire on observed signals, not the calendar.

### critical-path — timeline back-calculation + critical path
- Starting point: draw the D-day preconditions as a **dependency graph** first (the calendar is merely the graph's projection), identify the chains and merge points through which delay propagates, then set back-calculated milestones.
- Required components:
  - **Buffer currencies** — time / quantity (over-provisioning) / parallelism (multiple candidates), plus **direction** where error costs are asymmetric (contract so you can only miss in the cheap direction: floor commitments, upward-only adjustments); chosen per node, never spread evenly.
  - **Gates with defaults and decision deadlines** — "only a gate with a default is a working gate"; at merge points the strongest default is not waiting but **cutting the slow input edge** (invitation without photos, launch without the pricing page — merge points are designed to be severable, not endured).
  - **Node splitting** — after drawing the graph, ask each edge "does it depend on the whole node or a part?"; fat nodes ("price finalized") create false serialization — split them (pricing structure vs the numbers) and watch nodes fall off the critical path.
  - **Identification of uncontrollable nodes** with a treatment, not just a label — front-load it, control the observation resolution instead of the value, absorb it via contract terms, or exclude it from the success verdict.
- Failure mode: filling in a calendar backwards with no dependency justification — and the regression recurs *at the projection step*: annotate every projected calendar item with its source node.
- Watch-outs: buffer *size* is derived (from the recovery work if the gate fails), and parallel buffers get their real cost (double contracts, coordination) on the books; in convention-heavy domains a graph fed with customary lead times just reproduces the customary calendar ("graph theater") — state the graph's real contributions (zero-slack chains, severable edges) separately from the dates, and make re-projection with actually quoted lead times a verification step.

## B. Negative & failure family — start by removing the bad

Shared principle: the real design variable of a negative frame is not the failure list but the **choice of severity scale**. Change the scale and the same frame produces a different plan.

### failure-first — failure conditions first
- Starting point: enumerate the "failed states" first, and adopt only decisions that structurally foreclose each failure mode.
- Required components:
  - **An explicit severity scale, consumed** — declare what severity measures (e.g. "replay-killing power", "unrecoverability") before sorting, and let the ordering drive ≥1 real decision (resource allocation, a pre-committed deletion order, the conflict-verdict function). A scale declared but never consumed is an entry ritual.
  - **Conflict-resolution step between countermeasures** — where the blockers collide is the real design difficulty.
  - **Adversarial verification with attacker incentives** — whether a blocker is structure or etiquette can only be judged by testers tasked with *causing* the failure; a successful attack is recorded as the attacker's credit, or the verification decays into polite sparring.
- Failure mode: mistaking etiquette ("let's not do X, everyone") for structural foreclosure. What structure cannot prevent, a sentence will not.
- Watch-outs: where structure genuinely can't foreclose (human behavior), grade honestly instead of overclaiming — grade 1 = structurally impossible, grade 2 = cannot occur *unrecorded*, grade 0 = etiquette; downgrade when an assumption breaks; and beware the circular done-criterion — when a blocker removes the failure's medium, "0 failures of that kind" is satisfied by definition, so measure something the blocker does not auto-satisfy.

### safety-net — worst-case safety net
- Starting point: the document's center is the safety net (minimum guaranteed floor), not the optimistic path. Define success as "the floor never collapsed", not "the target was reached".
- Required components:
  - **One fallback state** — a single safe state reachable from anywhere; the floor is a thing you adjust, never violate. Qualified by two tests: *full-window habitability* (pre-compute that staying in the fallback for the whole remaining window doesn't kill the venture/life; if it does, the floor is wrong) and *progressive-damage exclusion* (a spreading leak/corruption won't converge under a freeze — give it an explicit exception path; forbid auto-actions more aggressive than the fallback).
  - **Transition asymmetry** — downshift immediate & automatic; upshift slow & conditional.
  - **Reinterpretation of non-firing** — if the safety mechanism never fired, suspect detection failure before celebrating; where possible implement as periodic active probes (synthetic fault injection, test alarms, check-completion rates), not only a post-hoc audit.
- Failure mode: the safety net's upkeep becomes a burden itself — size the check-in cost to the executor's cognitive slack (predicate ③). If shared with an organization, a hybrid (a conventional weekly skeleton carrying only the safety-net components) is valid.
- Watch-outs: where downshift has institutional deadlines (academic, contractual), compile the *descent price table* (per-transition free windows + post-deadline costs, with alerts) at planning time, or "immediate & automatic" is fiction; each floor item needs a live detector wired to it (a floor sensed only after the window is a post-mortem item); symmetric failure — the **bottom trap**: cheap downshift makes the machine settle at the floor, so after N periods there trigger a *plan-viability review* (re-tries the plan itself, not the state).

### misconception-first — predicted-misconception first
- Starting point: list the points where the learner's/executor's existing knowledge will interfere (misconceptions) first, and make the correction schedule the skeleton of the plan.
- Required components:
  - **Precondition check** — only valid when there is prior knowledge to interfere (powerless on a blank slate).
  - **A sealed list** — "things we deliberately do not touch yet", with unsealing conditions, is part of the plan.
  - **Predict → collide → reconstruct task design** — correction happens through engineered collisions, not exposition; with three lifecycle rules: place each correction at the misconception's *firing* time, not its learning time (some lie dormant); closure needs ≥1 spaced re-test (they relapse); predict the *second-order* misconceptions the correction breeds (overcorrection) and schedule a recovery pass.
  - **An operationalized ordering axis** — justify each adjacent pair with one sentence ("uncorrected X contaminates learning Y this way"); unjustifiable pairs are declared arbitrary.
- Failure mode: building the misconception list, then teaching in difficulty order anyway (the regression re-enters at the *ordering* layer under a new axis's name).
- Watch-outs: **collision misfire** — if the task data/environment has no detonator (duplicate keys, NULLs, 1-to-many), predictions never get betrayed and collision degrades into exposition; engineered collisions include *data design*, and for self-learners the collision tasks must come from a third party (mentor, problem bank, AI) or the predictor already knows the answer; scope honestly — the frame only maps interference, so attach non-interfering cargo (syntax, tooling) through a separate channel and explicitly list positive-transfer assets to avoid wasted collisions and morale damage.

## C. Quantitative & constraint family — start from numbers and walls

Two shared principles: ① this family's weakest point is **input arbitrariness** — the antidote is fixing the *meaning* of numbers before producing them (operationalized scales, a goal sentence). ② The frame is not finished until you find the **currency the ledger misses** (time, morale, trust).

### envelope — back-of-envelope calculation
- Starting point: before designing, estimate throughput / storage / cost to the order of magnitude, and make those numbers the basis of every technology choice. Ban product & architecture nouns inside the calculation section (domain unit nouns — vector, chunk — stay allowed where the units themselves are technical; a ban you can't keep breeds declaration-body mismatch).
- Required components:
  - **Choice of reading unit** — the same number is scary as a rate and trivial as a volume; read each axis twice (a spike may be a volume problem, not a rate problem).
  - **A sensitivity table** — which assumption flips the conclusion, at what numeric point — with **non-numeric forcing axes as explicit rows** (regulation, quality floors): the envelope can't compute them, and off-table they get silently dropped or smuggled in.
  - **Redesign triggers** — pre-commit, in numbers, what you do when a number flips; include *downward* triggers too (non-use → withdrawal verdict): triggers turn a one-shot document into an operating instrument panel.
  - **First-measurement milestones** for hand-picked inputs (unit prices, behavior rates, distributions) — cap their lifespan; conclusions are conditional until then.
- Failure mode: calculating and then concluding independently of the calculation ("1,157 eps, I see. So we'll use Kafka.").

### unit-economics — unit economics first
- Starting point: build the per-unit (one customer, one transaction) profit model first; develop the execution plan only under conditions where it holds. If it doesn't hold, propose the pivot under which it does.
- Required components:
  - **Recursive application** — re-run the ledger on whatever alternative replaced the one your first ledger killed (the "organic CAC ≈ $0" illusion → the ledger of the author's *time*); the designated-default pivot is also a recursion target (at least a stub ledger).
  - **Hidden-currency search** — costs outside the balance sheet: founder hours, emotional labor.
  - **Time-to-viability, stated** — the duration *and* the amount of each currency burned surviving it (cash figure, founder hours); duration alone is half the component. When recursion keeps converging on one unbuyable variable (e.g. churn), that is the signal to re-define the plan as that variable's measurement instrument.
- Failure mode: feeding optimistic benchmark numbers straight in — cap their lifespan with a first-measurement milestone.
- Watch-outs: run a **sign-stability check** — if the contribution margin's sign flips within the unmeasured variables' plausible ranges, the verdict is "cannot conclude"; better, express the verdict as the required threshold of the least-trusted variable (condition inversion) instead of a point estimate; beware arbitrariness *migrating* — lifespan-stamping the inputs pushes it into gate thresholds (referral %, hour caps, CAC ceilings), which need a basis or re-derivation milestone too.

### risk-matrix — probability × damage ordering
- Starting point: order failure scenarios by (probability × damage) and cover from the top only. Coverage/completeness metrics are never targets.
- Required components:
  - **Operationalized scales** — what "damage 5" means, in a sentence; a scale is only a scale when two people can score independently *and* the scorer can source its inputs.
  - **Baseline tense on the probability axis** — declare what design the scores assume ("proceeding the habitual way, no countermeasures"), and re-declare when re-scoring after mitigations, or the plan justifies itself with the probabilities it lowered.
  - **An irreversible-damage policy, declared before scoring** — choose one: pure multiplication (irreversibility lives inside D; re-raising rank is double counting) or a lexicographic override ("D-max does not trade against probability"); undeclared mixing is a failure mode, and below-line low-P × irreversible-D tail items get revival/review triggers instead of pure non-coverage.
  - **A cut line** — below-line items are recorded as "deliberately uncovered": a decision, not an omission.
  - **A topology-exception rule** — order may be violated only when a lower item is infrastructure for the higher ones, and only once (exceptions multiply, frames die). The sort is a *coverage* priority, not an execution timetable.
- Failure mode: "it's hard, so later" silently reordering priorities — difficulty cannot change rank; reducing the difficulty becomes step 1 of that item.
- Watch-outs: when the scorer is also the designer, watch for reverse-scoring (tuning P·D to crown a preferred #1, or nudging items below the cut line) — finish scoring and fix the cut line *before* designing countermeasures, then seal; the sort's real output is the rationale column — when several top risks cite the same sentence as their probability basis, that sentence is the true enemy.

### budget-allocation — resource-allocation trade-off
- Starting point: declare the fixed budget (person-weeks, money) — then **audit it**: deduct operating tax, measurement costs, and the buffer as line items to get the *net* budget that is actually allocatable (allocating the nominal budget is allocating money that doesn't exist). Plan as a portfolio with explicit opportunity-cost comparison. Start from a candidate list that exceeds the budget so cuts are forced.
- Required components:
  - **Goal sentence first** — "an allocation debate is a goal debate in disguise"; agree what value even means before scoring.
  - **The buffer as a line item** — not leftovers: an explicit allocation with usage rules.
  - **A critical-mass column** — each item's minimum effective allocation; "full critical mass or zero" turns the uniform-trimming ban from etiquette into arithmetic.
  - **A pre-committed cut order** — decide now what gets cut first on overrun (mid-flight cut decisions turn political); cuts are whole-line-item only (partially deducting an in-flight item pushes it below critical mass, and redistributing a cut item's budget is uniform trimming through the back door).
  - **A ledger admission gate** — candidates enter only with a one-line value basis (ideally two independent estimates converging) and an attachable verdict gate; estimates carry first-measurement lifetimes.
  - **Conversion of big bets into information purchases** — a large uncertain bet is answered not by shrinking it (still ignorant) but by buying knowledge (a small validation spike).
- Failure mode: uniform trimming ("a little off everything") — the worst allocation, pushing every axis below critical mass.

### constraint-first — constraints first
- Starting point: erect the constraints (budget, staffing, SLA) as walls first and design only inside them. State explicitly what the constraints forced you to give up.
- Required components:
  - **Contradiction test first** — prove whether the constraints' intersection is empty before designing; first decompose which dimension each constraint actually bites (a stated total may bind as a distribution or a timing).
  - **Break the premise of the structure** — if contradictory, don't shave the requirement; the utility of tight constraints is forcing you to doubt the premises of the obvious answer.
  - **Refinement vs. relaxation** — splitting a requirement to specify who it protects is refinement; lowering it is relaxation. Distinguish and disclose honestly.
- Failure mode: quietly punching holes in a constraint (free tiers etc.) — if you must, declare it as an assumption **with a numeric limit and a breach consequence** ("$20/month cap; beyond it, re-scope or the plan is void"); a bare declaration only normalizes the hole.
- Watch-outs: classify collisions honestly — a true contradiction (needs premise-breaking) vs a mere out-of-wall demand (rejection suffices); calling everything a contradiction kills the verdict's force; hidden walls count (the decisive contradiction may run between a stated wall and one buried inside a requirement — erect it explicitly before judging); this frame is a court, not a source of ideas — pair it with a deliberately over-budget candidate list (borrow budget-allocation's opening) or the gate has nothing to judge; **post-verdict slack** — once the contradiction resolves the tension releases and steps regress into a generic build sequence, so tag each step with which wall (or premise-break) it descends from.

## D. Diagnostic family — diagnosis before prescription

Shared principle: valid only while the cause is opaque; when the cause is obvious, diagnosis is mere delay. And **without runway (slack to afford observation), this family is a luxury.**

### hypothesis-loop — hypothesis–experiment cycle
- Starting point: separate observed facts from conjecture, raise 3+ hypotheses each paired with a rejection/acceptance experiment, then loop observe → update. The primary goal is not the fix but a **reproduction recipe**.
- Required components:
  - **Pre-registered rejection conditions** — set before the experiment; post-hoc interpretation turns any data into evidence for the favored hypothesis. With symmetric **promotion conditions**: a cause is confirmed only by a holdout prediction landing (a sentence written before looking, about data the analysis didn't use) or by induce-and-ablate reproduction — a post-hoc story cannot promote.
  - **The measurement-artifact hypothesis as row 0** — "the number itself is a counting/definition/query artifact" is the first ledger row, and no other experiment is interpreted until it settles (if the instrumentation is guilty, all other data is contaminated).
  - **An extinction/indeterminate default** — the pre-defined output for "all hypotheses rejected/held" or timebox exhausted: a default action, "cannot determine" accepted as valid, and an interrogation of the single-phenomenon premise (cluster the data, re-run the ledger per cluster).
  - **Experiment cost as a first-class ledger field** — run the cheap experiments in parallel first.
  - **Coordinate-system skepticism** — the same data may cluster only after changing coordinates (uniform in UTC can be clustered in local time).
- Failure mode: premature convergence (digging only the favored hypothesis); instrumentation scattering without hypotheses; **loop linearization** — written down, the observe→update loop flattens into an ascending step pipeline, and a "loop" label doesn't prevent it — encode the return paths as gates/rules.
- Watch-outs: pre-registration kills reinterpretation but not threshold arbitrariness — give each threshold a one-line basis, or register a revision protocol (revising a threshold demotes its hypothesis to "hold" and leaves a ledger entry).

### observe-first — observation & data first
- Starting point: before strategy, design "what to measure and how" as an observation plan; write strategy only as branches (if–then) on observation outcomes.
- Required components:
  - **The decision-link principle** — every metric is paired with "the decision this data will split"; delete orphan metrics (this frame fails through profligacy, not haste).
  - **Pre-fixed verdict thresholds** — each branch's firing threshold, the indeterminate case, and a default branch fixed before data arrives; include a **no-ignition branch** ("no branch fired" is a regular branch meaning the target may live outside the observation unit — "don't intervene" and "move the target" become legitimate conclusions).
  - **Baseline freeze** — no interventions during observation; put the observation apparatus itself on the contamination list (measurement contact is an intervention — exclude contacted cohorts). Prefer retrospective logs (Hawthorne-free by construction), and cap measurement burden (on overflow, cut metrics); when the phenomenon's reading unit is longer than the window (90-day retention vs a 4-week observation), retrospective mining is the primary source and forward observation covers only what logs can't say.
  - **Ordering rationale between branches** — not all if–thens are equal; state the causal reason for which branch goes first.
- Failure mode: four weeks later you have "interesting data" and no decidable branch. Second failure — **then-side regression**: the frame disciplines *when* to intervene while the interventions regress to the catalog you banned at entry; re-define the observation unit once, and check that at least one branch's intervention could not have been written without this observation design.
- Watch-outs: guard the thresholds' arbitrariness — check the verdict survives the threshold being 2× off, or use direction-consistency instead of magnitudes on small samples.

### middle-out — spike-centered conditional planning
- Starting point: place an analysis spike targeting the most uncertain point at the center of the plan, and write a conditional plan whose earlier/later steps differ by the spike's branch outcome.
- Required components:
  - **Pre-fixed verdict numbers** — choose thresholds before seeing data, sourced from something independent of the data under judgment (financial facts, irreversibility asymmetry, external benchmarks), source stated; on a first cycle grounded numbers are impossible in principle, so a sensitivity line ("which number moving how far flips the branch") is mandatory.
  - **A stop branch** — "this may not be the real problem at all" as a regular branch (a spike's best payoff is avoided wasted work); consider an *entrance* version too — a qualification gate on opening the spike at all (if the problem lies outside what the spike can measure, or no one agreed to be bound by the verdict, don't start it).
  - **A spike budget cap** — deadline overrun = the valid result "undecidable"; pair "undecidable" with a pre-fixed default action chosen by irreversibility asymmetry (the cheap-to-reverse side is the default; the expensive side is earned by evidence).
- Failure mode: the spike stretches into analysis paralysis.
- Watch-outs: with two unknowns (most real decisions), order the probes — cheap decisive hard gates first, and the problem's *existence* upstream of the solution's *efficacy* (a working solution to a phantom problem is still waste).

## E. Multi-perspective family — parallel viewpoints

### persona-lens — parallel persona lenses
- Starting point: write the **strongest objections** of 2–4 key stakeholders first, each in that person's own voice, then converge on a proposal that passes all of them.
- Required components:
  - **No strawmen** — the quality of the objections caps the quality of the proposal; include the most painful question each person would actually ask.
  - **Common-target discovery** — the solution is not the union of counters but the *shared premise* all objections attack, changed; with a **premise qualification test**: the premise qualifies only if every objection is explainable as its derivative; if one survives, the common term is shallow — dig deeper.
  - **A closing sweep for unowned risks** — after the lenses converge, sweep once for risk categories *no chosen persona would ever raise* (license contamination, junior growth paths); they vanish silently because nobody speaks for them.
- Failure mode: verbal patching (declaring passage via reframing alone) — structure, not wording, must guarantee the pass. Make it checkable: the done criteria require each persona's questions to point to the structural device answering them, by step number — unpointable = the patch was verbal; what structure cannot guarantee is recorded as residue, not passed.
- Watch-outs: outsider personas (customers, end users) are the anemia risk — the author can't introspect them, their objections come out thinner, and the sections they own lose verification density; check they weren't flattened into proxy statements.

### option-parallel — parallel options
- Starting point: no single recommendation. Design 2–3 tracks as complete plans of equal weight in parallel, and delegate the choice to the reader.
- Required components:
  - **A viability pre-check** — every track must pass minimum viability (assets, resources) before the frame applies; if arithmetic collapses the choice to one option, this is a constraint problem, not a choice problem — route to constraint-first.
  - **Bundled measurement instruments** — delegate, don't abandon; instead of introspective questions (contaminated by self-image), provide sampled experiences (probes) with reading rules (measure energy response, not skill — "the sustainable track is the one that drains you least"), and each probe must include the track's *death zones* (worst season, full-pipeline completion, ≥2 repeated deadlines): a probe sampling only pleasant parts measures novelty; read after return/completion, not during.
  - **Common-core identification** — the period during which choice can be deferred = the period spent building assets no track wastes.
  - **A switching deadline and switching costs, stated.**
- Failure mode: three tracks on the surface, one favored underneath (betrayed by asymmetric length and tone) — enforce equivalence as a document rule (same item skeleton per track, a length-deviation cap) checked in the done criteria, not as an intention.
- Watch-outs: **permanent deferral / track shopping** — prevent with hard gates carrying pre-declared defaults (and a switch-count cap); but a default track is a backdoor for favoritism, so designate it only by a pre-declared rule (e.g. lowest return cost), with that rule's sentence in the document.

### dialectic — now-camp vs. later-camp
- Starting point: for each contested issue, pit the strongest arguments of both camps and issue a verdict.
- Required components:
  - **A pre-fixed verdict function** — e.g. failure-cost asymmetry = blast radius × recoverability (dialectic without a function is a taste war); operationalized to where two people scoring independently reach the same verdict *before* any verdict is issued (axes named but not scorable = pre-judgments in disguise; unused axes are deleted or marked decoration), with a pre-fixed tiebreak for issues the first axis can't split.
  - **Split verdicts as a detection trigger** — "if both camps validly claim the losing condition, the issue was mis-composed — split it before judging"; splits are the function's output, not the author's intuition.
  - **Loser's-argument promotion** — the verdict's product is not a winner but constraints: the losing camp's strongest argument becomes a design constraint on the winner (an unpromoted loser argument is a strawman signal).
  - **Re-verdict triggers** — even the winning side gets numeric conditions under which the verdict flips.
- Failure mode: theater with a predetermined conclusion, or a verdict-free draw ("both have a point").
- Watch-outs: if you re-run the function on the winner's enforcement mechanism, declare the new scale — silent currency drift breaks the function's unity.

### incentive-audit — incentive accounting
- Starting point: model what each actor in the system **pays and receives, in explicit currencies**, and reject any policy whose incentives don't align — no matter how good it looks.
- Required components:
  - **Named currencies** — time / reputation / trust / risk ("motivation"-level prose can't support verdicts); every named currency is used in ≥1 verdict (naming more than you circulate turns the ledger into decoration). Intrinsic currencies (conscience, craft pride) go on the books too, with their properties (privately paid, decays with repetition, crowded out on contact with money) — zeroing them out is the cynicism slide.
  - **The deficit-actor check** — if an actor runs a sustained deficit, the model is missing an actor or a currency ("if the books don't balance, someone's not on the ledger"); iterate until they balance, and audit *surviving* policies the same way — a policy that persists without effect is paying somebody; find the recipient (that trace often re-defines the whole problem).
  - **An issuing-authority check, early** — the prescriptions presuppose authority over payment channels (evaluation systems, contracts, budgets); verify in step 1 that the sponsor holds it — a late-broken authority assumption maximizes redesign cost.
  - **Between-stage search** — pipelines die between stages, not at them (between the first and second contribution, etc.).
- Failure mode: over-applying to systems that don't run on voluntary participation (organizations with mandate power).

## F. Form family — the artifact's shape disciplines the thinking

### spec-coverage — requirement × surface completeness matrix
- Starting point: before any architecture, build the matrix of **every requirement × every surface it touches** (screens, states, content units, inputs, failure paths) — drawn from the spec *and* from what the artifact plainly needs in order to feel finished. That matrix is the document's top substantive section; architecture is then chosen to serve it.
- Required components:
  - **No-silent-drop ledger** — every cell is `build` / `defer (+ trigger)` / `n-a (+ reason)`. A blank cell is a defect in the plan, not a scope decision. Anything the spec states explicitly may only be `build`.
  - **Quality floor per surface** — one sentence per user-facing surface saying what "finished" means there (destruction *feedback*, score *legibility*, progression *persisting* across visits). Without it, breadth degenerates into an inventory of stubs. Each `build` cell owes its **verb sentence outside the table** (see "Requirements get verbs, not only nouns" at the end of this file) — the ledger row is not the instruction, and a matrix of 41 rows carrying ~334 words of instruction has been observed.
  - **The load-bearing path, wired** — the matrix proves surfaces are *listed*; it cannot prove the artifact *runs*. This frame therefore owes the `## Load-bearing path` chain and its cold-start table (see the end of this file). Observed failure of skipping it: full marks on surface coverage, primary interaction dead.
  - **Content axis, not only mechanics axis** — if the spec says ten stages, the plan owes ten stages of authored content with a difficulty curve, not one stage plus a loader. Mechanics coverage is not content coverage.
  - **Dependency-ordered build with a thin end-to-end slice first** — one path through the entire loop before any surface is polished, then breadth, then polish. The polish/content step must exist as a **named step**; if it is not named it does not happen (observed: a plan whose step list ended at "author the remaining stages" shipped no audio and no effects layer at all).
  - **Named delivery stack, with the reason it was bought** — even when the choice is canonical, state it and state what it enforces; an unspecified stack is filled by implementer defaults.
- Failure mode: the matrix goes wide and empty (a stub inventory) — the quality floor is the counterweight; or it degenerates into an unordered feature list — dependency ordering is the counterweight.
- Watch-outs: this frame deliberately does **not** resolve hard trade-offs — when a genuine either/or shows up inside a cell, borrow the matching frame for that cell only and record the borrow (Gate 0); resist the pull toward the narrowing frames, whose scope-cutting is exactly what a complete spec does not need; and keep the matrix at surface granularity — one row per requirement × surface, not per function, or the matrix becomes the implementation.

### api-first — user code first
- Starting point: write the ~10 lines of code the user will actually type at the top of the document first, and design the internals only in whatever direction makes that example true.
- Required components:
  - **Reflect the user's existing world** — the example comes from the data shapes and call sites users already have, not the author's taste; at planning time this is achievable only as *procedure* (the example precedes observation): include a discovery step 0 (mine real call sites/logs) with a rejection gate, and mark the draft "v1 = hypothesis, to be replaced by discovery findings".
  - **Pin edge cases into the contract** — deliberately include the ambiguous case (an example is a dispute-prevention contract, not a happy-path showcase); in governed domains pin the negative paths (refusal, masking, cost cut-off) as fully-specified *regular* responses, not exceptions.
  - **The example is an executable spec** — doctest it, declaring what the contract locks (field structure) and what stays free (wording, ordering, backward-compatible additions), or every surface becomes contractual and improvements read as breaking changes.
- Failure mode: sketching a lazy example and jumping straight to internals. Also **spec-source dualization**: contract clauses the example's code can't express (interaction, timing, wording-vs-field) leak into prose and stop being maintained — bind them as named tests in the same corpus.
- Watch-outs: the example corpus itself needs governance (a size cap, retirement rules) sized to the team.

### delete-first — deletion first / minimalism
- Starting point: lay out a generous list of candidate features, then delete everything that is not a necessary condition of a one-sentence core purpose (burden of proof on the feature — presumption of guilt).
- Required components:
  - **The deletion lever** — don't shave features one by one; first find the structural decision (storage format etc.) that makes several unnecessary *at once*. If item-by-item interrogation acquits everyone, the unit is wrong — raise the defendant one level (apps → the storage format, pages → the objection they answer); levers live at the shared layer.
  - **Named replacements** — a deletion without a designated replacement is a missing feature; stood up and round-trip-tested *before* the deletion executes, not merely named.
  - **A re-entry gate** — survivors regenerate deleted complexity (delete 7 apps, admit 7 plugins = a move, not a diet): install a standing default-deny gate on the surviving container (new candidates show a failed attempt within the existing structure, or prove necessity).
  - **Recorded revival conditions** — with a measurable threshold and a designated measurer (an unfounded threshold re-politicizes the revival hearing).
- Failure mode: leaving the premise that justified deletion (user type etc.) implicit — the more aggressive the deletion, the heavier the assumption disclosure.
- Watch-outs: **merge/hide disguises** — fix the counting unit (maintenance surface) before counting; a merge is deletion only if the maintenance surface shrinks, and hiding (removing navigation) is not deletion; **hold verdicts** are political sanctuaries — convert undecidable defendants into threshold-embedded conditional verdicts; if the user dictated a deletion quota ("cut half"), the one-sentence-purpose trial outranks it — the quota is a ceiling, not a target.

### min-diff — minimal-diff conservatism
- Starting point: every step must be independently deployable and independently rollback-able. A step whose rollback can't be written in one sentence is too big — split it and come back.
- Required components:
  - **One-sentence rollback as an admission gate** — it judges side-effect reversibility, not just diff size: a step with an irreversible side effect (deploy, publish) fails however small its diff, which back-derives side-effect isolation (dry-run, scratch targets) as an entry precondition; the document must show ≥1 step the gate actually split or isolated (a gate with no kills on record is a declaration).
  - **Separation of porting and improving** — behavior-preserving commits never mix with improvement commits (when a bug appears you must tell which caused it); corollary: *real bugs revealed by the tooling are preserved* in porting commits (tag + ticket, fix separately) — the most virtuous-looking temptation breaks behavior-preservation best.
  - **A temptation log** — record and reject big-bang / while-we're-here urges explicitly; at planning time it's a hypothesis, so give it runtime operating rules (who records, when) and an interpretation rule ("an empty log is evidence of recording failure, not discipline"), and put its being-kept into the done criteria.
  - **Rule of three** — extract shared code only after the third duplication.
- Failure mode: the seepage of "since we're at it".
- Watch-outs: structural limit — min-diff is **progress-blind**: it prevents regression but never forces completion, so import progress devices from outside (CI ratchets, a cutover deadline, WIP caps) and mark their external origin.

### first-principles — first principles
- Starting point: citing convention is banned. Reduce "why does this create value" to at most 3 axioms, and deduce the system from the axioms alone.
- Required components:
  - **Judge axioms by deductive yield** — not true/false but how many design decisions they generate (a good axiom changes even the unit of the output); record the rejected axiom candidates, because axiom *selection*, not deduction, is this frame's real design variable.
  - **The 3-axiom cap** — more axioms overlap and blur the deduction.
  - **The divergence reality test** — if the deduction produced no conclusion that conflicts with convention, self-verdict the run as restatement, not derivation (≥1 convention-conflicting conclusion is the minimum evidence of independence).
  - **Honesty about limits** — a pure run is impossible in principle (the author's knowledge is precedent); when a reconstructed conclusion re-meets good convention, record it as corroboration.
- Failure mode: re-narrating what you already know in axiom language and mistaking it for independent derivation. In "Approach & steps", tag each step with its source axiom — an untaggable step is inertia: delete it or reclassify as corroboration.
- Watch-outs: **pseudo-axioms** — unproven completeness claims ("X happens through exactly A and B") smuggled in as axioms; neither truth- nor yield-interrogation catches them (high yield makes them *easier* to pass); verification thresholds do not deduce from axioms — never present a number as if it did; tag it per the quality gate.

### checklist — checklist reductionism
- Starting point: reduce everything to checklists requiring no judgment. Where judgment remains, make the judgment now, at authoring time, and convert it into a conditional.
- Required components:
  - **Three layers of judgment removal** — conditions become sensory ("if dangerous" → "if you smell gas"), coordination becomes pre-assignment (no runtime negotiation), and unclassified situations get **one fallback action per sensorily-distinguishable type** (objects vs situations — merging them creates a new "which type is this?" judgment; type discrimination must not itself require judgment).
  - **Fallback reachability verification** — the fallback (abort/rollback/stop) must be reachable at every point: making irreversible steps reversible (expand/contract etc.) is the compile checklist's priority-0 item, and the fallback's cost (false-positive abort, redeploy) is measured next to it (an uncosted fallback gets bypassed at runtime by "let's watch it a bit longer").
  - **Compile-time / runtime separation** — the quality of the runtime checklist is decided by the preparation checklist (a half-prepared document is more dangerous than none).
  - **A judgment-word audit** — hunt down "promptly", "as appropriate" and replace them.
- Failure mode: applying it to domains that need deliberation (this frame is exclusively for high-stress / low-cognition situations). But mixed domains (a high-stress day with deliberation islands — a wire transfer, a defect-severity call) call not for rejection but for *banishing the judgment along the time axis*: spend the deliberation in the compile window (D-1), leave only a one-check comparison at runtime.
- Watch-outs: **checkbox theater** — removing judgment from conditions doesn't stop reflexive false checks at the recording layer; make pass verdicts *artifact existence* (pasted command output, binary artifact checks), not checkmarks. Done-sentence canon: "an executor with no prior experience completes the run with the runtime document alone — zero external questions, zero improvised judgments" (count them).

### triage — time-pressure tiering
- Starting point: organize actions strictly into available-time tiers (5 minutes / 30 minutes / afterwards), annotating every action with its side effects and firing conditions.
- Required components:
  - **One ultra-cheap classification** — neither blind hemostasis nor full diagnosis; a triage with its own budget cap (cap expiry is itself a valid classification: route to the default). The default track is chosen by a **reversibility rule** — only a track whose mis-triage cost is reversible / asymmetrically cheap qualifies, and the cost it burns (evidence, capacity) is named and knowingly paid; include a mis-triage recovery device (reclassification in a later tier).
  - **A compile-time asset list** — the runtime tiers presuppose prepared assets (isolation switches, toggles, snapshot bundles, dashboards, contact lists): require the list + a rehearsal check as part of the frame, instead of sealing it into a load-bearing assumption.
  - **A forbidden-actions section** — the bad moves a pressured brain will reach for; write each as temptation grammar (why you'll want it) → real cost → designated substitute, and enforce the top bans structurally (two-person confirm, ban list distributed to whoever'd order the move) — sentences don't stop pressed brains.
  - **The evidence-vs-speed trade-off, stated** — stabilizing destroys evidence; in evidence-preserving incidents, order within tiers by volatility × irreversibility (capture what disappears first; put what can't be undone behind a gate).
- Failure mode: the plan ballooning in the "afterwards" tier once pressure lifts (the center of gravity belongs in the early tiers) — enforce with a hard cap (afterwards ≤ N pointer items, default 3; overflow to a separate backlog) and check the *inter-tier* weight distribution too: capping the tail can displace bloat into the middle tiers.

---

## Common plan template

The default skeleton for the plan-writer. When a frame demands its own structure, the frame wins — but the following items must exist under some name.

```markdown
# [Plan title]
- Reasoning frame: [name] / Style: [opus|fable|relay]
- One-line summary

## The frame's mandated starting point   ← differs per frame; must be the top substantive section
## Problem definition / goal
## Explicit assumptions                   ← each with "impact if wrong"; bold any assumption the whole plan hangs on
## Approach & steps                       ← organized by dependency, not chronology: each step states
                                            its precondition (which step's output it consumes, or
                                            "independent/parallel") + its verification + which acceptance
                                            criterion/anchor it serves; calendar labels only as
                                            projections of stated dependencies
## Load-bearing path                      ← the one path that must close, as a chain (see below). Build-outs: mandatory
## Alternatives & rejection rationale     ← at least 1; **each rejection carries a revival trigger**
## Risks & mitigations
## Definition of "done"                   ← at least one measurably testable sentence is mandatory
                                            (e.g. "kill the origin and leave it down 24h — every existing link still resolves")
## Implementer contract                   ← terse, at the end: pinned stack, revival triggers, the command that proves the claim
```

### The load-bearing path — specify the wiring, not only the parts

A plan can name every part, order them by dependency, and still describe something that never runs, because **the parts existing is not the parts being connected.** Observed: a plan carried a 41-row coverage matrix and ~930 words of instruction, scored full marks on surface coverage, and shipped an artifact whose primary interaction did nothing — every layer was present, and the chain through them was never written down, so nobody checked that the conditions guarding each hop can all hold at the same moment.

Pick the **one** path whose failure makes the artifact pointless — not the most complex one, the load-bearing one. It is domain-shaped: a game's launch, a form's submit-to-persisted, a pipeline's first record landing in the sink, a CLI's first successful command, an approval flow's first request reaching a decider. Write it as a chain of **≤5 hops**, and give every hop three things:

| hop | name | passes only if | that condition first becomes true at |
|---|---|---|---|
| 1 | the named trigger / entry symbol | the guard on this hop | the step (or caller) that sets it |
| … | … | … | … |
| n | the observable effect | — | — |

Then, in the same section, a **cold-start table**: every state, flag, queue or precondition that appears in a "passes only if" cell, with its value at first entry, who changes it, and when that runs. **A blank cell is a defect in the plan, not a detail for later.**

Two hard rules, because both failures are cheap to avoid on paper and expensive to find later:
- **If you cannot fill "first becomes true at" for a hop, the plan is unfinished.** That column is where "the parts exist" turns into "the path closes"; it is answerable or it is not, and unlike a promise to review something it cannot be satisfied by asserting it.
- **The chain names symbols/steps that the plan elsewhere commits to creating.** A hop naming something the plan never introduces is a gap, not shorthand.

This section is *specification*, not verification. It does not ask anyone to run, open, watch or inspect the artifact — a plan cannot verify anything, and an instruction to "check that it works" is unfalsifiable, arrives after the cost is sunk, and in two validation corpora such self-review language was consistently counted as credit for defects that were never fixed. What this section does is force the wiring to be *decided* while it is still a sentence.

### Requirements get verbs, not only nouns

A coverage matrix counts **surfaces** (nouns), and nouns are cheap: rows can be added faster than instructions can be written. Observed: one plan reached 3,026 words of which **67% were table rows**, leaving ~334 words of actual instruction — the frame had routed correctly and its components were present, yet the quality floor never turned into anything an implementer could execute.

So every requirement marked `build` owes **one sentence, outside any table**, in this shape:

> When ⟨actor⟩ does ⟨action⟩, ⟨observable result⟩ happens; its absence shows up as ⟨the visible symptom⟩.

Rules: it may not be a table row (tables are the ledger; sentences are the instruction), and the third clause may not restate the second in the negative ("it doesn't happen" is not a symptom). Rows without their sentence are an inventory of stubs.

### Implementer contract — the plan's last section, and the shortest

Whoever builds this will not have the conversation, the packet, or the author. Three things must survive that gap, each one line:

- **Rejected alternatives carry revival triggers.** "X was rejected (because Y). **If Y is observed to be false, reopen it.**" A rejection with no trigger reads to the builder as an unexplained prohibition, and unexplained prohibitions get overturned — observed: a plan rejected hand-rolling a subsystem by name and chose a library; the implementation declared the library, imported it nowhere, and hand-rolled the subsystem anyway.
- **The stack is pinned to versions that resolve.** Naming a dependency without a version that actually exists is worse than naming none — observed: a declared dependency version that had never been published, which fails at install time, after the work is done.
- **Any guarantee the plan claims to buy is claimed with the command that proves it.** If the plan says a tool is bought because it "checks X at build time", then "done" must name the invocation and its exit status (`<the project's build/typecheck command> exits 0`), not the property. Observed: three plans bought compile-time checking in their stack section and shipped code that did not compile, because the guarantee was asserted in prose and nothing in "done" referred to it. This is a **written completion criterion**, not a request that someone go and look.

**Document budget — methodology argument belongs in the packet, not the plan.** The packet already carries `Deliverable type`, `Frame selection + rationale` and `Style selection + rationale`; a plan that re-argues them is paying twice for one decision, out of the same page budget that has to specify the work. In the plan, the frame and style get **the header line only**. Routing arguments, "why not frame X", canon debates and provenance defences stay in the packet.

Two exemptions, both placed at the **end** and both terse: the style-mandated confession (`Frame deviations & habit regressions`) and the relay audit — and the relay audit lives in `audit.md`, not in the plan. Everything else is measured by one test: **would a reader who must build this thing be worse off if the paragraph were deleted?** If not, it is methodology narration and it goes to the packet.

Observed cost of ignoring this: one plan spent ~37% of its body on methodology self-narration to earn — by its own confession — three paragraphs of design value, and the displaced pages were exactly the requirements that never got built.

### The machinery budget — fit the plan to the implementer

A plan's demands are not free. **Every part it requires — a build chain, a pinned dependency, a config file that references another config file — is one more surface the implementer can fail to reproduce.** A strong implementer absorbs that cost. A weak one dies of it, and dies *earlier* than it would have on its own: in a 9-cell transfer test, the weakest model given a strong model's plans failed **at the build step** in five of six cells (a phantom `@types` pin twice, a tsconfig referenced but never written twice, a deep import that does not exist once), while given its own modest no-build plan it reached the fire level the one time its single moving part — one CDN URL — was right.

Budget the machinery to the implementer recorded in the packet:

- **Weak or unknown implementer** — the best plan demands the least machinery: **no build chain** (plain files a browser or runtime loads directly), few files, no config that references another config, and every external dependency written as a **complete copyable string** — the full URL with its exact version, not a name to recall, because recall hallucinates (the same phantom `matter-js 2.0.20` appeared across three independent runs). Command-form completion criteria are wasted here — an implementer that cannot run commands will write "validation chain ready" over an artifact that fails the chain's first step; give it checks it can perform by reading its own output.
  **Extend copyability to the glue.** The plan carries **verbatim copyable blocks** for the highest-risk connective code: the dependency alias line (e.g. `const { Engine, World, Bodies, Body, Composite, Events } = Matter;`), a symbol table naming each file's public functions with their exact signatures, and the initial state declarations. This is not implementation — it is the plan pinning the joints the implementer would otherwise recall. What is copyable does not get hallucinated: making the CDN URL copyable took phantom dependency versions from five incidents to zero in the same test family, and the failures that remained were exactly glue recalled instead of copied — an undefined `setState`, an unaliased `Composite`.
- **Strong implementer** — the full discipline in this file applies as written; machinery is affordable, and the wiring rules above are the binding constraint.

Prescriptive plans buy consistency either way — **including consistent breakage** (the heaviest plan in the same test failed all three replicas at the same spot). The machinery budget decides what that consistency replicates.

Quality gate (plan-writer self-check):
- [ ] **Machinery budget:** does the machinery this plan demands match the packet's implementer profile? For a weak/unknown implementer: no build chain, no config-referencing-config, every dependency a complete copyable string, **the highest-risk glue present as verbatim copyable blocks** (dependency alias line, symbol table with exact signatures, initial state declarations), and no command-form completion criteria it cannot run.
- [ ] **Load-bearing path:** is there a chain of ≤5 hops for the one path whose failure makes the artifact
      pointless, with all three columns filled — and does the cold-start table have **no blank cells**?
      Every "passes only if" condition needs a "first becomes true at". A hop naming a symbol the plan
      never commits to creating is a gap. (Build-outs: this gate is mandatory.)
- [ ] **Verbs, not only nouns:** does every `build` requirement have its one sentence outside any table
      — *when ⟨actor⟩ does ⟨action⟩, ⟨result⟩ happens; its absence shows up as ⟨symptom⟩*?
      Count them against the ledger rows: rows without sentences are a stub inventory.
- [ ] **Implementer contract:** does every rejection carry a revival trigger, is every dependency pinned to
      a version that resolves, and for each guarantee the stack was bought for, does "done" name **the
      command and its exit status** rather than the property?
- [ ] Is the body **majority implementable instruction**? Frame/style rationale must not appear outside the header line (it belongs to the packet); confession sits at the end and stays terse. A plan that is longer than the unframed version while saying less about the work has failed this gate, not passed it.
- [ ] For each required component, can you point to **one decision it killed or flipped**? A component you cannot trace to a decision is "present but unapplied" — and an unapplied component counts as an unapplied frame. (Both validation corpora showed self-grades inflate exactly here: "all components present" ≠ applied.)
- [ ] Does every threshold / coefficient / multiplier carry one of three tags — **(a) derived** (one-line basis), **(b) lifetime-capped** (the first measurement that replaces it, when and by whom), or **(c) declared arbitrary** (or left honestly blank)? An untagged number fails the gate.
- [ ] Are the steps ordered by dependency/verification rationale rather than build-order chronology — or is the chronological order justified? (Timeline regression is the single most reproduced failure across 150 validation plans.)
- [ ] Does "done" contain a measurably testable sentence — one the plan's own blockers cannot auto-satisfy? (If a blocker removes the failure's medium, "0 failures" is circular.)
- [ ] Does every assumption carry an "if wrong"? A load-bearing ("everything hangs on this") assumption additionally needs its cheapest early verification and a one-line fallback path — bolding is not a defense.
- [ ] Does nothing violate the packet's hard constraints?
