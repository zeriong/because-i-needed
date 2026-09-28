# Mobile Review Rubric + APPROVED Artifact contract

The `ux-ui-mobile-art-director` agent produces a verdict; the commit gate reads it. This
file defines the rubric the director applies and the exact artifact the gate looks for —
they must stay in sync. The APPROVED artifact and gate are **shared with the web builder**
(same `scripts/ui-commit-gate.sh`, same `.ux-ui/approvals/<hash>.json`).

---

## Verdict output (what the director returns to the builder)

```
VERDICT: APPROVED | CHANGES_REQUIRED
SEVERITY: <count of blocking findings>   (only when CHANGES_REQUIRED)
STACK/BACKEND: <detected stack> via <measurement backend>
MEASURED: <list of state×device cells actually reviewed, from the capture dir>
FINDINGS:
- [critical|major|minor] <screen/element> — <what is wrong, seen in which
  screenshot/snapshot> → <exact fix: token/value/constraint/component>
...
(APPROVED → FINDINGS empty except any remaining minors; one-line pass rationale.)
```

Rules:
- **Hard gate.** Any `critical` or `major` → `CHANGES_REQUIRED`. Only `minor` may pass
  (minors are logged for follow-up).
- **No imagination.** The director judges only what is visible in the measurement
  artifacts. If a needed state (keyboard-open, empty, error, small phone, dark, …) was not
  captured, it returns `CHANGES_REQUIRED` with "state X not measured — capture required"
  rather than guessing.
- **Fixes are implementable.** "row minHeight 36→48dp; move CTA into bottom safe-area
  inset", not "make it nicer".

## Severity mapping

- `critical` → correctness violation that breaks the render or blocks use: crash /
  runtime error, content clipped by notch or keyboard, tap target unusably small, raw
  UUID/ISO shown, missing error state users will hit, unreadable contrast.
- `major` → clear correctness/consistency defect that ships a bad experience: broken
  hierarchy, cramped/adrift spacing, primary action out of thumb reach, missing pressed
  state, off-idiom for the platform, dark-mode breakage.
- `minor` → polish / elegance nits that don't block. Logged, not blocking.

## APPROVED artifact (what the commit gate requires)

When and only when the director returns `VERDICT: APPROVED`, the builder skill runs
`ui-commit-gate.sh approve …`, which writes:

`.ux-ui/approvals/<diff-hash>.json`

```json
{
  "verdict": "APPROVED",
  "feature": "<feature-slug>",
  "diffHash": "<sha256 of the staged UI diff — see gate script>",
  "measureDir": ".ux-ui/measure/<feature-slug>/",
  "approvedAtEpoch": <unix seconds>
}
```

The `diffHash` binds the approval to the exact code being committed: if the UI diff
changes after approval, the hash no longer matches and the gate blocks again. Non-forgeable
and never stale — you cannot approve once and keep editing. The mobile gate covers
`.swift .kt .dart`, iOS `.storyboard/.xib`, and Android `res/layout*/**/*.xml` (see the
gate script's `DEFAULT_GLOBS`; override with `UX_UI_GLOBS`).

## Iteration

Fully autonomous: build → measure → review → apply fixes → re-measure → re-review.
Cap = 3 review cycles. If still `CHANGES_REQUIRED` after 3, STOP and report the remaining
blocking findings (do not write an APPROVED artifact, so the commit stays blocked).
