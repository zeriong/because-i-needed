# Review Rubric + APPROVED Artifact contract

The `ux-ui-art-director` agent produces a verdict. The commit gate reads it. This
file defines both the rubric the director applies and the exact artifact the gate
looks for — they must stay in sync.

---

## Verdict output (what the director returns to the builder)

```
VERDICT: APPROVED | CHANGES_REQUIRED
SEVERITY: <count of blocking findings>   (only when CHANGES_REQUIRED)
MEASURED: <list of state×breakpoint cells actually reviewed, from the capture dir>
FINDINGS:
- [critical|major|minor] <location/element> — <what is wrong, seen in which
  screenshot/snapshot> → <exact fix: token/value/structure>
...
(APPROVED → FINDINGS empty except any remaining minors; one-line pass rationale.)
```

Rules:
- **Hard gate.** Any `critical` or `major` → `CHANGES_REQUIRED`. Only `minor`
  remaining may pass (minors are logged for follow-up).
- **No imagination.** The director judges only what is visible in the provided
  measurement artifacts. If a needed state was not captured, it returns
  `CHANGES_REQUIRED` with a finding "state X not measured — capture required" rather
  than guessing.
- **Fixes are implementable.** "card gap-2 → gap-4; title text-sm → text-base
  font-medium", not "make it nicer".

## Severity mapping (to priorities, for consistency with review-gate style)

- `critical` → correctness-bar violation that breaks the render or blocks use
  (console error, broken image, unreadable contrast, raw UUID shown, missing error
  state that users will hit). Always blocking.
- `major` → clear correctness/consistency defect that ships a bad experience
  (broken hierarchy, cramped/adrift spacing, missing focus ring, inconsistent with
  app patterns). Blocking.
- `minor` → polish / elegance nits that don't block (a tighter type pairing, a
  better empty-state line). Logged, not blocking.

## APPROVED artifact (what the commit gate requires)

When and only when the director returns `VERDICT: APPROVED`, the builder skill writes:

`.ux-ui/approvals/<diff-hash>.json`

```json
{
  "verdict": "APPROVED",
  "feature": "<feature-slug>",
  "diffHash": "<sha256 of the staged UI diff — see gate script>",
  "measuredCells": ["default__desktop", "hover__desktop", "..."],
  "lighthouse": { "performance": 0, "accessibility": 0, "bestPractices": 0 },
  "remainingMinors": ["..."],
  "approvedAtEpoch": <unix seconds>,
  "measureDir": ".ux-ui/measure/<feature-slug>/"
}
```

The `diffHash` binds the approval to the exact code being committed: if the UI diff
changes after approval, the hash no longer matches and the gate blocks again. This is
what makes the approval non-forgeable and non-stale — you cannot approve once and
keep editing.

## Iteration

Fully autonomous: build → measure → review → apply fixes → re-measure → re-review.
Cap = 3 review cycles. If still `CHANGES_REQUIRED` after 3, STOP and report the
remaining blocking findings to the user (do not write an APPROVED artifact, so the
commit stays blocked).
