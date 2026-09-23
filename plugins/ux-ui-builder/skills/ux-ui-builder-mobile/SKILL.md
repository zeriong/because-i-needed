---
name: ux-ui-builder-mobile
description: Build or change any MOBILE UI end-to-end, measured and reviewed, without extra user instruction. Use whenever implementing/editing mobile UI — React Native, Flutter, native iOS (Swift/SwiftUI), native Android (Kotlin/Compose/XML), or responsive mobile-web screens, components, navigation, forms, sheets, lists. Detects the project's stack, picks the right measurement backend (an MCP that returns real screenshots, or a CLI snapshot harness when no MCP can), MEASURES the real render on device/simulator, has the ux-ui-mobile-art-director agent critique the measured snapshots, iterates until elegant and correct, then records the approval that unblocks commit. Trigger on: build/implement/fix/redesign/style a mobile screen, component, navigation, sheet, list, form; RN/Flutter/iOS/Android UI.
---

# UX/UI Builder (Mobile) — detect, measure, critique, iterate, gate

Agents implement UI poorly when they work from imagination. This skill removes
imagination from the loop for **mobile**: it first detects the app's stack, then
guarantees the art director always sees **real pixels from a real device/simulator** —
via a screenshot-capable MCP where one exists, or a **CLI snapshot harness** where none
does. Every mobile UI change is measured on the real render, critiqued by an art
director against the measured snapshots, and iterated until it is both correct and
elegant. The same commit hard-gate enforces it — you cannot commit UI the art director
has not APPROVED against the exact staged diff.

Run this loop autonomously (no extra user prompting) whenever you build or change mobile
UI. The **one** place you pause for the user is backend selection in step 0.

## Roles
- **You (main loop)** — detect the stack, plan, write the code, and MEASURE. You hold the
  mobile MCP tools, `Bash` (for the CLI snapshot harness), and the file tools.
  Measurement is *your* job and is mandatory; never hand the director imaginary states.
- **`ux-ui-mobile-art-director` agent** — critiques the measured artifacts and returns a
  verdict. It cannot edit code (reviewer/implementer separation). It may re-measure on
  MCP-capable stacks; on CLI-harness-only stacks it demands the capture instead.
- **The gate** (`scripts/ui-commit-gate.sh`, wired as a PreToolUse hook) — blocks
  `git commit` of UI unless an APPROVED artifact matches the staged diff hash. It covers
  mobile file types (`.swift .kt .dart`, iOS `.storyboard/.xib`, Android `res/layout`).

## References (read the relevant one when you reach that step)
- `references/backend-detection.md` — **read this first**: detect the stack, pick the
  measurement backend, and the exact "present choices to the user" protocol.
- `references/mobile-design-principles.md` — the mobile correctness + elegance bar (HIG /
  Material, safe areas, tap targets, gestures, keyboard, dark mode).
- `references/mobile-measurement-protocol.md` — the exact per-backend capture protocol
  (device × orientation × state matrix).
- `references/mobile-review-rubric.md` — verdict format + the APPROVED artifact contract.

---

## The loop

### 0. Bootstrap + detect stack + choose backend (read `references/backend-detection.md`)
- Detect the mobile stack from the repo (RN / Expo / Flutter / native iOS / native
  Android / responsive mobile-web). Run the harness doctor to see which backends are
  actually functional on this machine:
  `"${CLAUDE_PLUGIN_ROOT}/scripts/mobile-snapshot.sh" doctor`
- Pick the measurement backend by the matrix in `backend-detection.md`:
  - **Mobile web** → the bundled `chrome-devtools` MCP (device emulation) — no native SDK.
  - **Flutter** → the `flutter` MCP (`dart mcp-server`): widget tree + hot reload + screenshot.
  - **iOS-deep** → the `ios-simulator` MCP (idb): `screenshot`/`ui_view` + `ui_describe_all`.
  - **Native Android / cross-platform** → the `mobile-mcp` MCP:
    `mobile_take_screenshot` + `mobile_list_elements_on_screen`.
  - **React Native** → default to the **CLI snapshot harness** (`mobile-snapshot.sh`).
    `mobile-mcp` can screenshot RN at the OS level too — offer it as an alternative, but
    do not silently prefer it over the CLI path.
  - **No functional MCP for the detected stack** → the **CLI snapshot harness**
    (`mobile-snapshot.sh`), which captures real pixels via `simctl`/`adb`.
- **Present the choice to the user** (this is the single interactive pause). State the
  detected stack, the backend you recommend, its limitation, and — when the MCP path
  can't give the director a reviewable visual snapshot — that you will fall back to CLI
  command snapshots and compare via CLI-captured PNGs. Proceed once they confirm/pick.
- Ensure a target is up: the app is built and running on a **booted** simulator/emulator
  (or, for mobile-web, the dev server is reachable). Never measure against a dead target.
- Pick a `<feature-slug>`; artifacts live in `.ux-ui/measure/<slug>/`.

### 1. Plan the design (before writing code)
- Read `references/mobile-design-principles.md`. If the host project defines its own
  rules (a `CLAUDE.md` design section, a design system, platform theme), those win.
- Brainstorm a compact design intent for this feature: hierarchy, spacing scale, type
  roles, states, gesture/affordance model, and the one signature element — within the
  platform's idiom (iOS HIG vs. Material). Record it into `context.md`.

### 2. Build
- Implement the mobile UI following the plan and existing app conventions. Reuse existing
  components/tokens/theme; match the surrounding code's style and the platform idiom.

### 3. Measure (mandatory — follow `references/mobile-measurement-protocol.md` exactly)
- Drive the app to each required state and capture the device × orientation × state
  matrix using the backend chosen in step 0. Always capture **screenshots** (real pixels);
  add the a11y/view snapshot wherever the backend exposes one.
- Record console/log errors, failed network/asset loads, and any crash.
- Write everything into `.ux-ui/measure/<slug>/` including `snapshots.md`, `signals.md`,
  and `context.md` (feature, screen/route, what changed, chosen backend, design intent,
  which cells were skipped and why).

### 4. Critique (hard gate)
- Spawn the `ux-ui-mobile-art-director` agent. Give it the `.ux-ui/measure/<slug>/` path,
  the detected stack, and the chosen backend. It reviews the measured artifacts and
  returns `VERDICT: APPROVED | CHANGES_REQUIRED` (see `mobile-review-rubric.md`).

### 5. Iterate (autonomous, cap = 3)
- If `CHANGES_REQUIRED`: apply every critical/major finding exactly as instructed, then
  GO BACK TO STEP 3 (re-measure — the fix must be verified on the real render, including
  a hot reload on Flutter). Re-critique with a fresh spawn of the director.
- Repeat until `APPROVED` or 3 cycles. If still not approved after 3, STOP and report the
  remaining blocking findings. Do **not** write an approval — the commit stays blocked.

### 6. Record approval (unblocks commit)
- Only when the director returns `APPROVED`, stage your UI changes, then run from the
  project root:
  `"${CLAUDE_PLUGIN_ROOT}/scripts/ui-commit-gate.sh" approve <feature-slug> .ux-ui/measure/<slug>/`
- This writes `.ux-ui/approvals/<hash>.json` bound to the staged UI diff hash. Any further
  UI edit changes the hash → re-run the loop.

## Rules
- Measurement is never optional and never faked. No screenshot → no review → no commit.
  Every stack has a path to real pixels: an MCP screenshot, or the CLI snapshot harness.
- The director judges only measured artifacts. If a state is missing, capture it.
- Autonomous except step-0 backend selection: do not ask the user between other steps;
  stop only at the cap-3 failure or a broken environment.
- The approval binds to the diff hash, so "approve once and keep editing" is impossible.
