---
name: plan-smith
description: Two-stage planning pipeline. The main agent distills the whole conversation into a context packet (goals, hard constraints, rejected alternatives), a clean-context plan-writer agent drafts the plan with a proven reasoning frame + an Opus/Fable-derived writing style, and the main agent relays the plan file verbatim. Trigger on — "write a plan", "plan this", "plan-smith", "설계 플랜", "계획 짜줘", or whenever a non-trivial implementation / business / operations / learning task needs a planning document.
argument-hint: "[frame=<frame>] [style=opus|fable|relay|auto] <task description>"
---

# plan-smith — distill intent, write clean, relay lossless

When this skill loads, **you (the main agent) do not write the plan yourself.** Your only unique asset is the session context — the user's intent, nuance, and history — and you spend it entirely on intent extraction. The writing happens in a noise-free context owned by the `plan-writer` agent. This division of labor is the whole point:

- A plan the user actually wants requires **session context** → Stage 1 (you).
- Uncontaminated writing requires **isolation** → Stage 2 (plan-writer).
- Delivery that doesn't get mangled requires a **file contract** → Stage 3 (you).

**Global rules (override everything below):**
1. When a decision is hard or ambiguous, do not guess — **ask the user immediately via AskUserQuestion.** A pipeline with a chance to correct intent always beats a cleanly written plan built on the wrong intent.
2. Never delegate writing without a packet. Never relay by summary. The plan-writer never modifies the codebase.
3. Write the packet and the plan in **the language the user is conversing in** (the pipeline instructions are English; the artifacts belong to the user).

## Stage 0 — Parse arguments

Argument shape: `[frame=<frame>] [style=opus|fable|relay|auto] <task description>`

- No `frame` → select one in Stage 1 using the routing rules in [references/frames.md](references/frames.md), and record the rationale in the packet.
- No `style` → `auto`. Route using the rules in [references/styles.md](references/styles.md), and record the rationale in the packet.
- Empty task description → infer the planning target from recent conversation; if the inference is not certain, ask the user immediately.

## Stage 1 — Intent distillation (your job)

1. Read [references/frames.md](references/frames.md) and [references/styles.md](references/styles.md) (needed for routing and for copying specs in Stage 2).
1b. **Run Gate 0 first (frames.md):** is this a **decision** document or a **build-out** document? Ask "if this plan is followed literally, is the danger that we chose wrong, or that we left things out?" A complete spec whose risk is omission is a build-out → `spec-coverage`, with any other frame borrowed only for one genuinely open sub-decision. Record the answer *and its reason* in the packet — a build-out routed to a narrowing frame produces a plan that loses to no plan at all.
    Gate 0's second axis: **record the implementer** (resolved model id, a person, or "unknown") and apply the **machinery budget** (frames.md) — a weak or unknown implementer gets the plan demanding the least machinery, however capable the planner. If you cannot tell who implements, that is a `⚠guess` to resolve at the confirmation gate, and until resolved you budget for the weakest plausible implementer.
2. Using the **entire conversation** as source material, write a context packet following [references/packet-template.md](references/packet-template.md). Core fields: goal (definition of success) / hard constraints / soft preferences / **rejected alternatives and why** / decisions already made / relevant file paths with their gist / unknowns & open questions / selected frame + rationale / selected style + rationale.
   - Any field you inferred rather than confirmed from the conversation must carry a `⚠guess` marker.
   - For relevant files, never give bare paths — add "why it matters + the one-line takeaway". Assume the plan-writer knows nothing about this conversation and must reconstruct context from files alone.
2b. **Fill the run stamp** (packet's first section) before anything else in the packet: the plugin version read from the plugin's own `plugin.json`, the frames.md fingerprint, and the **resolved model ids** of yourself and of the writer — `opus` / `sonnet` / `fable` are aliases whose meaning changes over time, so an alias is not a version. Also record whether this run is interactive or scripted. A plan that cannot name what produced it is not comparable to the next one.
3. Save the packet: `plans/<kebab-slug>/packet.md` (slug derived from the task; append `-2` on collision).
4. **User confirmation gate (never skip):** show the user the packet's essentials (goal / hard constraints / rejected alternatives / **deliverable type and implementer from Gate 0** / frame & style selection with rationale) and confirm via AskUserQuestion: "Here is the intent and constraints I distilled — is this correct?"
   - If any `⚠guess` fields exist, turn them into question options and confirm them in the same gate.
   - If the user corrects anything, update the packet file before proceeding.
   - **Rejection path:** if the user rejects the distillation, re-distill from their feedback and re-gate once. If the second gate also fails, stop the pipeline and report what remains unresolved — never invoke plan-writer on an unconfirmed packet. If the user explicitly defers a `⚠guess` ("I don't know either"), demote that field into the packet's "Unknowns & open questions" section (the writer treats it as an assumption/risk, not a fact) and proceed.

## Stage 2 — Isolated writing (delegate to plan-writer)

Invoke the `plan-writer` agent via the Task tool (use `plan-smith:plan-writer` if your environment requires the namespace). **The delegation prompt must be self-contained** — the plan-writer has not seen this conversation and does not know where this skill lives. The prompt must include:

1. The absolute path of the packet file.
2. The absolute output path: `plans/<slug>/plan.md`.
3. **The full spec of the selected frame** — copy the frame's **entire `###` entry** verbatim from frames.md: starting point, required components, failure mode, and any watch-outs/variant lines (watch-outs are second-order cautions — heed them, but only required components are presence-mandatory). Do not substitute a path reference.
4. **The full directive of the selected style** — copy the style's section verbatim from styles.md, plus the `## Shared boundary — do not perform the fingerprint` section, and **state the execution mode explicitly** (standalone / relay pass 1 / relay pass 2) — the styles' confession and deferral rules depend on the writer knowing whether another pass exists.
5. The **common plan template** from the end of frames.md, verbatim — and, for build-outs, the specification-rule sections that follow it (**The load-bearing path**, **Requirements get verbs, not only nouns**, **Implementer contract**, and **The machinery budget** whenever the packet's implementer profile is weak or unknown), also verbatim. The writer cannot honor rules it never receives — a batch harness that read frames.md whole masked this gap through two releases.
6. (relay pass 2 only) The absolute path of `draft.md` **and** the absolute output path of `audit.md` — the writer's input contract requires both and it will refuse to write without them.
7. (build-out only) The packet's **load-bearing path candidate** — the main agent's read of which path, if it fails, makes the artifact pointless. The writer owns the final call and may overrule it, but it must then say which path it chose instead; silence here is how a plan ends up specifying every part and no wiring.

### Per-style execution

- **opus-style or fable-style (single pass):** one invocation as above. Wait for completion, then Stage 3.
- **relay (two passes):**
  1. **Pass 1:** invoke with the opus-style directive; output path `plans/<slug>/draft.md`. The opus-style directive mandates a section titled **"Frame deviations & habit regressions"** — that confession is the fuel for pass 2.
  2. **Pass 2:** invoke with the fable-style directive **plus** the `### relay pass-2 protocol` section from styles.md, both verbatim. The prompt must additionally contain (a) the absolute path of `draft.md` and (b) the absolute output path `plans/<slug>/audit.md` (input-contract item 6); the output path of item 2 is `plans/<slug>/plan.md`. Pass-2 duties (defined in the protocol): use the draft's confession as an improvement backlog, state an independent rationale for every decision that diverges from the draft, run the T1–T6 contamination audit (especially T6: "am I diverging just to be different?"), and **keep the parts where the draft is better** — revision does not always win; execution burden and communication cost are valid reasons to keep the draft's shape.

### Stage 2c — Wiring audit (mandatory for build-outs, optional otherwise)

A plan can pass every structural check and still describe something that never runs. This pass costs one
extra agent invocation and buys the only defect class the other gates cannot see: **a path that does not close.**

Run it when Gate 0 said **build-out** (skip for decision documents, where there is usually no single
load-bearing path). Invoke `plan-writer` again — a **fresh instance**, not the one that wrote the plan, since
the author cannot audit their own omissions — with a prompt containing:

1. The absolute path of `plans/<slug>/plan.md` (read-only input).
2. The absolute output path `plans/<slug>/wiring-audit.md`.
3. The three sections from frames.md verbatim: **"The load-bearing path"**, **"Requirements get verbs, not only
   nouns"**, and **"Implementer contract"**.
4. This instruction: *report defects only, do not rewrite the plan.* For each finding: the plan's section, what
   is missing, and the smallest addition that closes it.

The audit answers exactly five questions and nothing else — it is **document-level**; it never asks anyone to
build, run, open or look at the artifact, because the pipeline produces a document and a document can only be
checked against itself:

1. Is there a load-bearing-path chain of ≤5 hops, and does **every** hop have "passes only if" *and* "first
   becomes true at"? Name every hop that does not.
2. Does the cold-start table cover **every** condition named in those hops, with no blank cells?
3. Does every hop name a symbol/step the plan **commits to creating elsewhere**? List the orphans.
4. Does every `build` requirement have its verb sentence **outside any table**? Give the count of rows vs sentences.
5. Does the implementer contract carry revival triggers, resolvable pinned versions, and — for each guarantee
   the stack was bought for — **a command with its exit status in "done"** rather than a property in prose?

Then **you** apply the outcome: hand the audit back to the writing agent (same style, same frame) to make the
minimal additions, or, if a finding is at the intent level (e.g. the load-bearing path is genuinely undecided),
take it to the user. Keep `wiring-audit.md` — it is the record of what the plan almost shipped without.

**Cost note, stated honestly:** this is roughly a 20–35% token increase on the writing stage and it does not
improve prose. It exists because the failure it catches is invisible to reading and expensive to find in code.
If the user is optimizing for speed on a decision document, skip it — that is what the build-out condition is for.

**Handling writer reports:**
- Writer returned a conflict **without writing** (unsatisfiable hard constraint, missing input): fix the packet — or ask the user — then re-invoke. Do not push it to write anyway.
- Writer **wrote the plan but flagged soft conflicts** (stale path, wrong takeaway): do not relay it as final. Resolve the conflict with the user, update the packet, and rerun Stage 2 — in relay mode, from pass 1 if the conflict predates the draft, otherwise pass 2 only.

## Stage 3 — Lossless relay (your job)

1. Read `plans/<slug>/plan.md` and present **the full text verbatim** to the user. No summarizing, no restructuring, no excerpting. Include the file path.
2. If relay mode: append audit.md's "changed decisions / kept decisions" list after the plan text, and **delegate the final merge judgment to the user** wherever draft-vs-revision choice points exist. Include the draft.md path.
3. Handle approval/edit requests as usual. If a change is at the intent level, fix the packet and rerun Stage 2; if it is wording-level, you may edit directly.
4. **Retrospective record:** once the user's verdict lands (adopted / edited / rejected), append one line to the packet's `## Retrospective` section: `outcome: <adopted|edited|rejected> — frame <name>, style <name>, model <the model that ran plan-writer>, one-line note`. This accumulation is the raw material for tuning the frame×domain routing rules — and the model field is the only data that can ever separate style effects from model effects (style×model has been fully confounded in every experiment so far).

## Divergence experiments (optional)

If the user asks to "compare across frames/styles": invoke plan-writer **in parallel with only the frame (or style) changed**, same packet. Rules:
- Output naming: `plans/<slug>/plan-<variant>.md`, where `<variant>` is the frame name (frame comparison) or style name (style comparison).
- Variants are **single-pass only** (`opus` / `fable`). `relay` is excluded from divergence experiments — it is itself a two-pass comparison; if the user wants relay quality, run relay afterward on the winning variant.
- Style-comparison variants run on the **same model** — a style is a prompt discipline; comparing styles across different models measures the model, not the style.
- In Stage 3 present each full text first; a short comparison table comes last (full texts first, comparison is auxiliary). Record in the retrospective which variant the user adopted.
