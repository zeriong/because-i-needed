# Mobile Measurement Protocol — capture the real render (mandatory)

The point of this plugin: **agents implement UI poorly from imagination, so we never
review from imagination — we measure the real render and review that.** This file is the
exact capture protocol for mobile. Which tool you call depends on the backend chosen in
`backend-detection.md`; the *matrix you must capture* is the same for all of them.

If a step here cannot run (no booted device, backend not functional), STOP and fix the
environment — start the simulator/emulator, build+launch the app, or switch to the CLI
snapshot harness. Never fall back to reviewing source or guessed states.

---

## 0. Preconditions (self-check before any capture)

1. A target is live: the app is built and running on a **booted** simulator/emulator, or
   (mobile-web) the dev server is reachable. Confirm with
   `mobile-snapshot.sh doctor` / `mobile_list_available_devices` / `simctl list`.
2. The chosen backend is functional (its MCP tools are present, or `simctl`/`adb` exist
   for the CLI harness).
3. An output directory exists: `.ux-ui/measure/<feature-slug>/`.

## 1. Navigate + settle

- Launch/route to the target screen (`mobile_launch_app` / `launch_app` / in-app
  navigation; for mobile-web `navigate_page`).
- Wait until visually settled: fonts loaded, skeletons resolved, images decoded, no
  in-flight spinner. Prefer a content check over a fixed sleep.
- Collect logs/console: device log (`adb logcat` slice / Xcode console / RN Metro /
  `list_console_messages` for web). Runtime errors and crashes are **blocking**.

## 2. Capture the required matrix

For the feature under review, capture a screenshot for **every applicable** cell. Skip a
cell only if it genuinely cannot exist for this UI, and say so in `context.md`.

Interaction / data states (rows):
- `default` — nominal, realistic data (never placeholder that hides overflow).
- `pressed` — the primary control's pressed/active state.
- `focus-keyboard` — a text field focused **with the software keyboard open** (verify the
  field and submit stay visible — see principle 8).
- `loading` — in-flight state (skeleton/spinner with layout).
- `empty` — zero-data state.
- `error` — failed-request / validation-error state.
- `long-content` — overflow / truncation / wrapping / Dynamic-Type-max.

Device breakpoints (columns) — capture at least a small phone, a large phone, and (if the
app targets it) a tablet:
- **iOS**: iPhone SE (small), iPhone 15 / 15 Pro (large), iPad (tablet).
- **Android**: a compact phone, a large phone (e.g. Pixel 7), a tablet.
Switch device with `simctl`/AVD or the MCP device tools before capturing that column.

Also capture, at least once:
- **Orientation**: landscape for any screen not locked to portrait.
- **Dark mode**: if the app supports it, the `default` cell in dark.

Minimum matrix: `default + loading + empty + error + focus-keyboard + long-content` on one
large phone, plus `default` on a small phone and (if supported) dark mode. Add cells the
feature warrants (gesture states, sheets, tabs).

For each key cell, also capture the **structure snapshot** where the backend exposes one
(`mobile_list_elements_on_screen` / `ui_describe_all` / widget tree / `take_snapshot` /
Android `uiautomator dump`) — it exposes raw identifiers, missing accessibility labels,
and tap-target sizes the pixel screenshot hides.

## 3. Audits (objective, not opinion)

- **Tap targets**: from the structure snapshot, confirm interactive frames ≥ 44 pt (iOS)
  / 48 dp (Android).
- **Accessibility**: every interactive element has an accessible label/role and is
  reachable by the platform screen reader; contrast adequate.
- **Safe areas**: confirm nothing critical sits under notch/Dynamic Island/home indicator
  (inspect the top/bottom insets in the screenshot).
- **Reduced motion**: confirm animations respect the OS reduce-motion setting.
- **Mobile-web only**: `lighthouse_audit` on the route; accessibility < 90 is blocking.

## 4. Package for review

Write, into `.ux-ui/measure/<feature-slug>/`:
- the screenshots, named `<state>__<device>.png` (add `__dark` / `__landscape` suffixes).
- `snapshots.md` — the structure/a11y snapshots per state (paste the tool output / link
  the `uiautomator` XML).
- `signals.md` — log/console errors, crashes, failed assets, audit scores, tap-target and
  safe-area findings.
- `context.md` — feature, screen/route, what changed, **detected stack + chosen backend**,
  design intent (from the plan), and which cells were skipped and why.

Hand this directory to the `ux-ui-mobile-art-director` agent. Everything it reviews is a
real measurement — no cell is described, only shown.
