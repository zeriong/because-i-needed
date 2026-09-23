---
name: ux-ui-builder
description: Build or change any frontend UI end-to-end, measured and reviewed, without extra user instruction. Use whenever implementing/editing UI — components, pages, screens, styles, layout, design tweaks. Drives chrome-devtools to MEASURE the real render, has the ux-ui-art-director agent critique the measured snapshots, iterates until elegant and correct, then records the approval that unblocks commit. Trigger on: build/implement/fix/redesign/style a component, page, screen, form, dashboard, modal, layout.
---

# UX/UI Builder — measure, critique, iterate, gate

Agents implement UI poorly when they work from imagination. This skill removes
imagination from the loop: **every UI change is measured on the real render, critiqued
by an art director against the measured snapshots, and iterated until it is both
correct and elegant.** A commit hard-gate enforces it — you cannot commit UI that the
art director has not APPROVED against the exact staged diff.

Run this loop autonomously (no extra user prompting) whenever you build or change UI.

## Roles
- **You (main loop)** — plan, write the code, and MEASURE. You have the
  `chrome-devtools` MCP tools and the file tools. Measurement is *your* job and is
  mandatory; never hand the director imaginary states.
- **`ux-ui-art-director` agent** — critiques the measured artifacts and returns a
  verdict. It cannot edit code (reviewer/implementer separation). It may re-measure.
- **The gate** (`scripts/ui-commit-gate.sh`, wired as a PreToolUse hook) — blocks
  `git commit` of UI unless an APPROVED artifact matches the staged diff hash.

## References (read the relevant one when you reach that step)
- `references/design-principles.md` — the correctness + elegance bar (self-contained).
- `references/measurement-protocol.md` — the exact chrome-devtools capture protocol.
- `references/review-rubric.md` — verdict format + the APPROVED artifact contract.

---

## The loop

### 0. Bootstrap (self-check — zero-config)
- Confirm the `chrome-devtools` MCP tools are present in this session
  (`mcp__plugin_ux-ui-builder_chrome-devtools__*`). If missing, the plugin's MCP
  server failed to start (needs Node + Chrome). Tell the user how to fix, then stop.
- Find the dev server URL (project config; default `http://localhost:3000`). If it is
  not running, start it (prefer the project's own run/dev script) and wait until it
  responds. Never measure against a dead server.
- Pick a `<feature-slug>` for this change; artifacts live in `.ux-ui/measure/<slug>/`.

### 1. Plan the design (before writing code)
- Read `references/design-principles.md`. If the host project defines its own design
  rules (a `CLAUDE.md` design section, design tokens, a component library), read those
  — they win.
- Brainstorm a compact design intent for this specific feature: hierarchy, spacing
  scale, type roles, states, and the one signature element. Avoid the templated AI
  defaults called out in the principles. Keep this short; record it into
  `context.md` so the director knows the intent.

### 2. Build
- Implement the UI following the plan and existing app conventions. Reuse existing
  components/tokens; match the surrounding code's style.

### 3. Measure (mandatory — follow `references/measurement-protocol.md` exactly)
- Navigate, settle, and capture the required state × breakpoint matrix
  (default / hover / focus / loading / empty / error / long-content across
  mobile / tablet / desktop as applicable).
- Capture both screenshots and DOM/a11y snapshots. Record console errors, network
  failures, and a lighthouse audit.
- Write everything into `.ux-ui/measure/<slug>/` including `snapshots.md`,
  `signals.md`, and `context.md` (feature, route, what changed, design intent, which
  cells were skipped and why).

### 4. Critique (hard gate)
- Spawn the `ux-ui-art-director` agent. Give it the `.ux-ui/measure/<slug>/` path and
  the context. It reviews the measured artifacts and returns
  `VERDICT: APPROVED | CHANGES_REQUIRED` with findings (see `review-rubric.md`).

### 5. Iterate (autonomous, cap = 3)
- If `CHANGES_REQUIRED`: apply every critical/major finding exactly as instructed,
  then GO BACK TO STEP 3 (re-measure — the fix must be verified on the real render,
  not assumed). Re-critique with a fresh spawn of the director.
- Repeat until `APPROVED` or 3 cycles. If still not approved after 3, STOP and report
  the remaining blocking findings to the user. Do **not** write an approval — the
  commit stays blocked by design.

### 6. Record approval (unblocks commit)
- Only when the director returns `APPROVED`, run from the project root:
  `"${CLAUDE_PLUGIN_ROOT}/scripts/ui-commit-gate.sh" approve <feature-slug> .ux-ui/measure/<slug>/`
  (stage your UI changes first — the approval is bound to the staged UI diff hash).
- This writes `.ux-ui/approvals/<hash>.json`. The gate will now allow the commit for
  exactly this diff. Any further UI edit changes the hash → re-run the loop.

## Rules
- Measurement is never optional and never faked. No screenshot → no review → no commit.
- The director judges only measured artifacts. If a state is missing, capture it.
- Fully autonomous: do not ask the user between steps; only stop at the cap-3 failure
  or a broken environment.
- The approval binds to the diff hash, so "approve once and keep editing" is impossible.
