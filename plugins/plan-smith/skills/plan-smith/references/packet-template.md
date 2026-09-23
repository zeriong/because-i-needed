# packet-template.md — Context Packet

The packet is the **only** channel through which session context reaches the plan-writer. Anything not in the packet does not exist for the writer. Write it so that someone who never saw the conversation can reconstruct the intent from the packet plus the referenced files alone.

Marking rule: any field inferred rather than confirmed from the conversation carries `⚠guess`. Every `⚠guess` must be resolved at the user confirmation gate before delegation.

```markdown
# Context Packet — <task slug>
- Date: <YYYY-MM-DD>
- Requested by: <user>
- Language of artifacts: <the language the user converses in>

## Run stamp — record, never guess
<!-- A plan whose producing version and model are unknown cannot be compared to a later one.
     This pipeline's own A/B lost the model version of half its artifacts and had to recover it
     from raw transcripts; two rounds were nearly mislabelled. Fill every line or mark it unknown. -->
- plan-smith version: <from the plugin's own `.claude-plugin/plugin.json`, sibling of the plugin's `skills/` directory — not from memory; if the file cannot be found, write "unknown" rather than inferring from a path>
- frames.md fingerprint: <line count, or a digest if you can compute one>
- Main agent model: <resolved id, e.g. claude-opus-5 — an alias like "opus" is NOT a version>
- plan-writer model: <resolved id of the writing agent; state it if it differs from the main agent>
- Skill invocation: <interactive `/plan-smith` | batch/scripted — comparability requires the same harness>

## Task (one line)
<what is being planned, in one sentence>

## Background (why now)
<2–5 lines: what happened in the session/project that led here>

## Goal — definition of success
<what must be true for this plan to have succeeded; measurable where possible>

## Hard constraints
- <constraint — source: user said / project config / platform limit>   ← never invent; cite where each came from

## Soft preferences
- <preference the user showed but did not mandate>

## Rejected alternatives (and why)
- <option> — rejected because <reason, from the conversation>          ← prevents the writer from re-proposing them

## Decisions already made
- <decision> — <where it was settled>

## Relevant files & paths
- `<path>` — why it matters + one-line takeaway                        ← no bare paths

## Unknowns & open questions
- <what is genuinely not known; the writer should carry these into the plan's assumptions/risks, not resolve them by invention>

## Deliverable type (Gate 0)
- Type: <decision | build-out>
- Rationale: <followed literally, is the danger a wrong choice or an omission?>
- (build-out) Frame is `spec-coverage`; any other frame is borrowed for one named sub-decision only: <which, or none>
- **Implementer**: <who builds from this plan — resolved model id / person / "unknown". Not optional: the implementer picks the plan's *weight*>
- (weak or unknown implementer) **Machinery budget applies** — no build chain, no config-referencing-config, dependencies as complete copyable strings; see frames.md "The machinery budget"

## Load-bearing path candidate (build-out only)
<!-- Which single path, if it fails, makes the artifact pointless? Not the most complex path — the one
     everything else is decoration around. You have the session context, so you are better placed than the
     writer to know what the user actually came for; the writer owns the final call and may overrule you,
     but it must then name the path it chose instead. Leave this blank rather than guessing, and say so. -->
- Path: <trigger → … → the observable effect the user came for>
- Why this one: <what becomes pointless if it fails>

## Frame selection
- Frame: <name>
- Rationale: <which routing predicate(s) fired; why this frame over the runner-up>

## Style selection
- Style: <opus|fable|relay>
- Execution mode: <standalone | relay (pass 1 feeds pass 2)>        ← the writer must know whether another pass exists; confessions may defer work to a later pass only if one is real
- Rationale: <which auto-routing signal fired, or user override>

## Output contract
- Plan file: `plans/<slug>/plan.md`
- (relay) Draft: `plans/<slug>/draft.md`, Audit: `plans/<slug>/audit.md`

## Retrospective
<!-- appended after user verdict: outcome: <adopted|edited|rejected> — frame <name>, style <name>, one-line note -->
```
