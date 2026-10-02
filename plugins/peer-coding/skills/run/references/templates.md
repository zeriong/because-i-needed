# Templates

## plan.md

```markdown
# <Feature>
Host: <claude-code|codex> · Transport: <orca|standalone> · Mode: <cross-vendor|single-vendor>
Transport IDs: <e.g. Orca run ID>

## Goal
## Non-goals
## Decisions
- <decision> — rejected alternatives: <...> — reason: <one line>
## Gate command
<e.g. pnpm test && pnpm typecheck && pnpm lint && ./scripts/check-rules.sh>
## Context bridge
- Instructions: <ok | Codex fallback | pointer added | proposed | declined → included in context packs>
- Hooks → gate: <hook> → <script in gate | context pack | ignored | NOT ENFORCED for other vendor>
- Manifest: <entries, or none>

## Phase 1: <name>
Risk: normal | high   (high → extra top-model final review: asked, <approved | declined>)
- T1 [claude-fast] <title> — files: <paths> — deps: none — done when: <command>
- T2 [codex-bulk]  <title> — files: <paths> — deps: none — done when: <command>
- T3 [main]        <title> — files: <paths> — deps: T1, T2 — done when: <command>
```

## Delegation prompt

```markdown
# Task <id>: <title>
## Context
<2–5 sentences: the feature and where this task fits. Point to plan.md sections.>
## Project context
Read before starting: <instruction files for this project, e.g. CLAUDE.md / AGENTS.md,
  plus nested ones under the task's directories>
Follow these procedures: <paths to relevant skill/rule files, e.g. .claude/skills/x/SKILL.md>
Context pack (from main's tools):
- <path> — <why it matters: pattern to follow, dependent to keep working, contract>
Rules checked by the gate that you won't see as hooks: <one line each>
## Scope
Files you may change: <paths>
Files to read for patterns: <paths>
Do not change: <paths or areas>
## Requirements
<numbered, concrete>
## Constraints
<conventions, libraries to use or avoid, relevant decisions from plan.md>
## Done when
<exact command(s) that must pass>
## If you are unsure
<Orca: ask the coordinator before touching anything outside Scope.
 Standalone: don't guess on scope — stay inside it and list the question under Uncertain.>
## Return format
### Changed files
### Key decisions        (choices the spec didn't dictate)
### Uncertain            (assumptions, TODOs, unverified points)
### Gate result          (the done-when command and its outcome)
```

Under Orca, put the worktree setup command (transport-orca.md) first in the prompt.

Test: could a capable engineer who never saw this conversation do the task from this
prompt alone? If not, add what's missing.

## Review prompt

```markdown
You are reviewing phase <n> of a feature, written by another model.
Read the project's instructions (<CLAUDE.md / AGENTS.md paths>), the rules that apply
to this diff (<paths>), .claude-x-codex/<feature>/plan.md and .claude-x-codex/<feature>/decisions.md,
then review `git diff <base>...HEAD -- <files>`. Judge against this project's rules,
not general taste; a deliberate project convention is not a finding.

- Report findings only. Do not rewrite code that works.
- Don't re-raise items rejected in decisions.md unless you have new evidence.
- For a delta re-review: review only the fix diff and report whether each previously
  accepted finding is resolved.

Your lens: <Codex reviewing Claude → adversarial correctness, edge cases, error
paths, test coverage of the change, unverified assumptions behind fluent code |
Claude reviewing Codex → intent vs plan.md, design and pattern consistency,
readability and UX coherence, over-literal solutions that pass tests but miss the point>.
Blocking correctness issues are always in scope regardless of lens.

Output only JSON in this shape, nothing else:
```

```json
{
  "findings": [
    {
      "id": "F1",
      "severity": "blocking | major | minor | nit",
      "file": "path/to/file",
      "line": 0,
      "issue": "what is wrong",
      "evidence": "why you believe it (code path, input, failing case)",
      "suggestion": "direction for a fix, not a rewrite"
    }
  ],
  "resolved": ["F1"],
  "verdict": "pass | changes_requested"
}
```

The CLIs enforce this shape from `review.schema.json`; the example is for the prompt.

## Rebuttal prompt

```markdown
You reviewed phase <n> earlier. The author side rejected the findings below.
For each, read the reason and evidence, re-check the code, and reply.
- Concede if the reason holds.
- Counter only with new, concrete evidence (a failing input, a code path, a test).
  Restating the original claim is not a counter.

<F2 [major] — your finding — rejection reason — evidence offered>

Output only JSON:
{"replies":[{"id":"F2","position":"concede | counter","evidence":"..."}]}
```

## decisions.md

```markdown
## Phase <n> · Review r<k> (reviewer: <id that ran>, <effort>)
- F1 [blocking] ACCEPT — reproduced with <test/command>
- F2 [major]    REJECT — contradicts Decision "<name>" in plan.md
  - rebuttal: concede | counter (<evidence>) → final: REJECT | ACCEPT | DISPUTED
- F3 [minor]    DEFER  — out of scope for this phase

## High-risk reviews
- Phase <n>: asked at <plan approval | later> → approved | declined

## Worker questions
- T2: "<question>" → <answer> (source: plan.md Decisions | new decision)

## Dispatch log
- T1 [codex-bulk] <id that ran> · <effort> (source: run header | modelUsage | launch.effective)
```
