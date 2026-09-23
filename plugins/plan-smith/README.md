<p align="center">
  <strong>plan-smith</strong>
</p>

<p align="center">
  <strong>Forge plans like a smithy — the main agent distills intent, a clean-context writer forges the plan, and it is delivered verbatim.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.4.2-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#the-pipeline">The pipeline</a> &bull;
  <a href="#frames--styles">Frames & styles</a> &bull;
  <a href="#measured-results">Measured results</a> &bull;
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

Long sessions produce bad plans for a structural reason: the agent that knows your intent best is also the one whose context is the most polluted — dozens of tool outputs, repeated file dumps, dead ends. Writing a plan there means writing through noise. Writing it in a fresh subagent means losing the intent.

**plan-smith refuses the trade-off by splitting the job.** The main agent spends its one unique asset — session context — entirely on *intent distillation*, producing a structured context packet. A clean-context `plan-writer` agent then forges the plan from the packet, guided by a battle-tested reasoning-frame library and one of two validated writing styles. The finished plan is relayed **verbatim** — never summarized.

## What it does

- **Intent distillation, not main-agent writing** — the skill extracts goals, hard constraints, **rejected alternatives**, settled decisions, and relevant files from the whole conversation into a packet. Extraction is far more robust to context noise than composition is.
- **One confirmation gate** — before any writing happens, the packet is shown to you: *"here is the intent and constraints I distilled — correct?"* Every inferred field is marked `⚠guess` and confirmed. A pipeline that can correct intent always beats a clean draft of the wrong intent.
- **Clean-context forging** — `plan-writer` runs with no session noise: packet + frame spec + style directive only. Read-only toward your codebase; writes only its designated output file(s) — the plan, plus audit.md in relay pass 2 — and returns paths, not text.
- **A reasoning-frame library that earns its keep** — 26 frames (backward-chaining, premortem, back-of-envelope, constraint-first, incentive accounting, …) distilled from a 26-plan empirical experiment, stress-tested by a 100-plan validation corpus, and **corrected by a controlled A/B in which a framed plan lost to an unframed baseline** on a spec-complete build — the fix is `spec-coverage` plus the Gate 0 routing rule below. Each frame ships with its **required components** (the parts whose absence turns it into decoration) and routing predicates for auto-selection.
- **Two validated writing styles + relay** — `opus`-style (coverage-first disciplined draft, honest confession log) and `fable`-style (structure-auditing revision, judgment encoded as rules). **Relay mode** chains them: draft → confession → adversarial revision with a T1–T6 contamination audit — the strongest pipeline observed in the source experiment.
- **Gate 0: it knows when a frame would hurt** *(new in 1.1)* — before any frame is chosen the pipeline asks *"followed literally, is the danger that we chose wrong, or that we left things out?"* A complete spec whose risk is omission is a **build-out** and routes to `spec-coverage` (a requirement × surface completeness matrix), because narrowing frames license the omission of whatever they did not select. This rule exists because a framed plan lost to an unframed one — see the FAQ.
- **It specifies the wiring, not only the parts** *(new in 1.2)* — a build-out plan must carry a **load-bearing path**: the one path whose failure makes the artifact pointless, written as a chain of ≤5 hops where every hop names its guard *and where that guard first becomes true*, plus a cold-start table with no blank cells. Every `build` requirement also owes a **verb sentence outside the table** (*when ⟨actor⟩ does ⟨action⟩, ⟨result⟩ happens; its absence shows up as ⟨symptom⟩*). This exists because a plan scored full marks on surface coverage and shipped an artifact whose primary interaction did nothing — every part present, the chain through them never written down.
- **A wiring audit before you ever see the plan** *(new in 1.2)* — for build-outs, a **second, fresh** plan-writer instance audits the finished plan against five document-level questions (unfilled hops, blank cold-start cells, hops naming symbols the plan never creates, ledger rows lacking verb sentences, guarantees claimed in prose instead of a command in "done"). An author cannot audit their own omissions. Costs ~20–35% more tokens on the writing stage and buys the one defect class reading cannot see.
- **It budgets the machinery to the implementer** *(new in 1.3)* — Gate 0 now also records **who implements this plan**, because every part a plan demands (a build chain, a pinned dependency, a config referencing another config) is one more surface a weak implementer can fail to reproduce. In a 9-cell transfer test, a strong model's plans handed to the weakest model killed it *at the build step* in five of six cells, earlier than its own modest plan did. A weak or unknown implementer therefore gets the plan demanding the least machinery — no build chain, dependencies as complete copyable strings, no command-form completion criteria it cannot run.
- **Copyable glue — validated before release** *(new in 1.4)* — for weak or unknown implementers the plan now carries **verbatim copyable blocks** for the highest-risk connective code: the dependency alias line, a symbol table with exact signatures, and initial state declarations. What is copyable does not get hallucinated — making the CDN URL copyable had already taken phantom versions from five incidents to zero, and the residual deaths were glue recalled instead of copied. Unlike earlier releases, this clause passed a pre-registered gate *before* shipping: against an informed baseline (n=4 each), glue deaths 1 vs 2 and ladder median L5 vs split — including the test family's **first stage CLEAR**.
- **Lossless delivery + retrospective data** — the plan file is presented in full, and every outcome (adopted / edited / rejected) is appended to the packet, accumulating data to tune frame routing over time.

## Installation

### Via Claude Code plugin marketplace

1. In Claude Code, run `/plugin`.
2. Marketplaces → Add Marketplace.
3. Enter the URL: `https://github.com/zeriong/because-i-needed.git` (or a local path to this repo).
4. Install `plan-smith`.

### Or via CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # or a local path
claude plugin install plan-smith@because-i-needed
```

### Or wire it directly in `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "plan-smith@because-i-needed": true }
}
```

## Usage

```
/plan-smith:plan-smith migrate the session store from Redis to Postgres
/plan-smith:plan-smith frame=premortem style=relay launch plan for the paid newsletter
/plan-smith:plan-smith style=fable review and harden the deploy runbook
```

Or just ask naturally — *"write a plan for X"* triggers the skill. Arguments:

| Argument | Values | Default |
|---|---|---|
| `frame` | any frame in [frames.md](skills/plan-smith/references/frames.md) | auto-routed by 4 predicates, rationale recorded |
| `style` | `opus` \| `fable` \| `relay` \| `auto` | `auto` — routed by task signals, rationale recorded |

Artifacts land in `plans/<slug>/`: `packet.md`, `plan.md` (+ `draft.md`, `audit.md` in relay mode).

## The pipeline

```
Stage 1 — Intent distillation (main agent)
  conversation ──▶ context packet ──▶ user confirmation gate («⚠guess» fields resolved)

Stage 2 — Isolated writing (plan-writer agent, fresh context)
  packet + frame spec + style directive ──▶ plans/<slug>/plan.md
  relay: opus-style draft (+ confession) ──▶ fable-style revision (+ T1–T6 audit)

Stage 2c — Wiring audit (fresh plan-writer instance; build-outs only)
  plan.md ──▶ 5 document-level questions ──▶ wiring-audit.md ──▶ minimal additions

Stage 3 — Lossless relay (main agent)
  plan file presented verbatim ──▶ user verdict ──▶ retrospective line appended to packet
```

Why the split works: *wanting the right plan* requires session context (Stage 1's resource); *uncontaminated writing* requires isolation (Stage 2's resource); *undamaged delivery* requires a file contract (Stage 3's rule). One agent can't hold all three — a pipeline can.

## Components

| Component | Path | Role |
|---|---|---|
| Skill `plan-smith` | [`skills/plan-smith/SKILL.md`](skills/plan-smith/SKILL.md) | Pipeline orchestration for the **main agent**: Stage 1 intent distillation → packet + user confirmation gate, Stage 2 delegation, **Stage 2c wiring audit** (build-outs, fresh writer instance), Stage 3 verbatim relay + retrospective record. |
| Frame library | [`skills/plan-smith/references/frames.md`](skills/plan-smith/references/frames.md) | 26 reasoning frames in 6 families — each with starting point, **required components**, failure mode, watch-outs — plus Gate 0 + 4-predicate routing, the common plan template, and the three specification rules every build-out owes: **load-bearing path** (a ≤5-hop chain whose guards each say where they first become true, plus a cold-start table), **verb sentences outside the ledger**, and the **implementer contract** (revival triggers, pinned versions, and the command whose exit status proves any guarantee the stack was bought for) — plus **Gate 0's implementer axis and the machinery budget** (1.3): a weak or unknown implementer gets the plan demanding the least machinery, with the highest-risk glue as **verbatim copyable blocks** (1.4, gate-validated pre-release). |
| Style directives | [`skills/plan-smith/references/styles.md`](skills/plan-smith/references/styles.md) | `opus`-style (coverage-first disciplined draft + confession log), `fable`-style (structure-auditing revision + rule-encoded judgment), and the `relay` two-pass protocol with T1–T6 contamination audit. |
| Packet template | [`skills/plan-smith/references/packet-template.md`](skills/plan-smith/references/packet-template.md) | The context packet contract — the only channel from session to writer. |
| Agent `plan-writer` | [`agents/plan-writer.md`](agents/plan-writer.md) | Clean-context author. Self-contained input contract, read-only toward the codebase, writes only its designated output file(s) (plan, plus audit.md in relay pass 2), returns paths — never the plan text. |

## Frames & styles

- **[frames.md](skills/plan-smith/references/frames.md)** — 26 frames in 6 families (backward, negative/failure, quantitative/constraint, diagnostic, multi-perspective, form), each with starting point, required components, failure mode, and corpus-derived watch-outs. Routing runs **Gate 0 first** — *decision document or build-out?* (a complete spec whose risk is omission goes to `spec-coverage`, because narrowing frames license omission) — then four predicates: *where is the uncertainty / how rigid are resources / how much cognitive slack does the executor have / can a scale be agreed*.
- **[styles.md](skills/plan-smith/references/styles.md)** — the two writing disciplines and the relay protocol. A style is a prompt-level discipline, **not** a model choice — designed to run on any model (cross-model portability is still being validated through retrospectives).

## Measured results

Every claim below is a lab measurement, not an estimate (data: z-lab `plan-smith-lab/`, series `tco/`, `transfer/`).

**Total cost to a *working* artifact** (repair loop included; weak implementer, fixed repair-prompt template, n=4 chains per arm):

| Stage | baseline plan | plan-smith v1.4 |
|---|---|---|
| Plan (opus) | 229k | 689k — **3.0× dearer** (reads four skill docs) |
| Implementations ×4 (haiku) | 6,968k | 4,069k — **42% cheaper** |
| Repairs to DONE | **8,380k** (4 rounds) | **620k** (1 round) — **13.5× cheaper** |
| **Total, 4 working artifacts** | **15.58M** | **5.38M — 65.5% cheaper** |

In round numbers: baseline 100 + repairs 116 = 216; plan-smith 66, done. The mechanism, not just the number: the repair prompts were identical templates, so the gap comes from the **defect class each plan produces** — plan-smith's one failure was a single symbol its copyable blocks had missed (one-line fix; that chain ended in the test family's first stage CLEAR), while the baseline's failures were cross-component contract mismatches (one interface rebuild, one three-round whack-a-mole).

**Side effects with receipts:** phantom dependency versions 5 → 0 once URLs became copyable strings; 4/4 replicas reproduced the identical CDN line and file layout; the only stage CLEARs in the whole test family came from plan-smith cells.

**Limits, stated in the same breath:** small repair sample (2 chains vs 1), one task, one weak implementer — the gap shrinks with strong implementers, which succeed without the skill. Half the baseline repair bill rides on a single chain.

## Design invariants

1. The main agent **never writes the plan** — it distills intent; extraction survives context noise, composition doesn't.
2. **No writing without a confirmed packet** — every inferred field is `⚠guess`-marked and resolved with the user first. When a decision is ambiguous, ask immediately.
3. The writer's inputs are **self-contained** (packet + inline frame/style specs) — no session access, no path guessing.
4. **Verbatim relay** — the plan file is presented in full; summaries are a contract violation.
5. Styles are **prompt disciplines, not model choices** — distilled from a 26-plan controlled experiment and stress-tested in a 100-plan validation corpus; relay chaining and cross-model portability remain promising-but-unverified, with retrospectives accumulating the evidence.

## Changelog

Release history, and *why* each frame or rule was added, lives in
**[CHANGELOG.md](CHANGELOG.md)**. Worth knowing before you pin a version: the
plugin is served from a **version-keyed cache**, so editing the source tree does
not reach an installed client — every behavioural change ships as a version bump,
and 1.1.1 exists for that reason alone.

## FAQ

**Why doesn't the main agent just write the plan?** Because its context is polluted by the very session that gave it the intent. Extraction (signal-picking) survives noise; composition doesn't. plan-smith uses the polluted context for the only job it's still good at.

**Doesn't the subagent lose the conversation's nuance?** That's what the packet is for — goals, constraints, *rejected alternatives* (so the writer doesn't re-propose them), settled decisions, and per-file gists, all confirmed by you at the gate before writing begins.

**When is relay worth double cost?** Hard-to-reverse or high-blast-radius decisions, plans you'll execute for months. The audit trail (`audit.md`) records what the revision changed, what it kept, and why — final merge authority stays with you.

**Can a frame make a plan *worse*?** Yes — and it did, which is why 1.1 exists. In a controlled A/B (same model, same fully-specified task: a browser game with 10 stages, a physics loop and a named UI requirement), the `backward`-framed plan ran 38% longer than the unframed baseline yet carried **41% less implementable instruction**, spent ~37% of its body narrating its own methodology, cut sound/particles/mobile as "off-anchor", went silent on score, stars, persistence *and the stack*, and re-labelled one of the user's three stated requirements "cosmetic". The baseline shipped `audio.ts`, `effects.ts`, `storage.ts`, `types.ts`; the framed one shipped none of them. Three fixes followed: an anchor list may no longer act as a scope filter, "this choice is canonical" may end a derivation but never a specification, and **Gate 0** now diverts build-outs away from narrowing frames entirely.

**Does the token cost pay for itself?** Measured, not estimated — see [Measured results](#measured-results) for the full table. Cost to a *working* artifact, repair loop included: the plan-smith plan cost **3.0× more to write**, then earned it back twice over — implementations **42% cheaper**, repairs **13.5× cheaper** — for a total of **5.38M vs 15.58M tokens (65.5% cheaper)** to four working artifacts. The gap comes from the defect class: plan-smith's one failure was a one-line missed symbol, while the baseline's were cross-component contract mismatches. Honest limits, recorded in the lab: tiny repair sample, one task, one weak implementer; with a strong implementer the gap shrinks (strong models succeed without the skill). Full data: z-lab `plan-smith-lab/tco/`.

**What are the styles based on?** A controlled experiment: the same 26 planning tasks were executed under two distinct model fingerprints, then comparatively audited. The audit distilled each fingerprint into a reproducible writing directive; chaining them (relay) produced the strongest artifacts in that experiment — single-run evidence, so the pipeline treats relay as promising rather than proven and accumulates retrospectives to test it.

## License

MIT. See [LICENSE](../../LICENSE).
