# Measurement Protocol — chrome-devtools measurement (mandatory)

The whole point of this plugin: **agents implement UI poorly when they work from
imagination. So we never review from imagination — we measure the real render and
review that.** This file is the exact, deterministic capture protocol. The builder
skill runs it; the art director reviews its output.

If a step here cannot run (dev server down, MCP unavailable), STOP and fix the
environment first. Never fall back to reviewing hand-written HTML or guessed states.

---

## 0. Preconditions (self-check before any capture)

1. A dev server is reachable at a known URL (default `http://localhost:3000`, or the
   project's configured port). If not running, start it (or ask the project's run
   skill to) and wait until it responds.
2. The `chrome-devtools` MCP server is available (tools prefixed
   `chrome-devtools__*` in this session). If not, the plugin's MCP is misconfigured —
   see the skill's bootstrap section.
3. An output directory exists for artifacts: `.ux-ui/measure/<feature-slug>/`.
   Screenshots and the verdict artifact go here.

## 1. Navigate + settle

- `navigate_page` to the target route.
- `wait_for` the primary content selector (not a fixed sleep). The page must be
  visually settled: fonts loaded, skeletons resolved, above-the-fold images decoded.
- `list_console_messages` — record every error/warning. Console errors are a
  **blocking** finding (a broken render often only shows in the console).
- `list_network_requests` — record any 4xx/5xx or failed asset. Broken images/fonts
  are a blocking finding even if the layout "looks" fine.

## 2. Capture the required state matrix

For the feature under review, capture a screenshot for **every applicable** cell.
Skip a cell only if the state genuinely cannot exist for this UI, and say so.

Interaction / data states (rows):
- `default` — nominal, populated with realistic data (never lorem/placeholder that
  hides overflow).
- `hover` — hover the primary interactive element(s) (`hover` then screenshot).
- `focus` — keyboard-focus the primary control (`press_key` Tab / focus) — the focus
  ring MUST be visible.
- `active/pressed` — where it matters (buttons, toggles).
- `loading` — the in-flight state (throttle or intercept if needed).
- `empty` — zero-data state.
- `error` — failed-request / validation-error state.
- `long-content` — overflow / truncation / wrapping with realistically long values.

Viewport breakpoints (columns) — use `resize_page` before each capture:
- `mobile` 375×812
- `tablet` 768×1024
- `desktop` 1440×900

At minimum capture: default + hover + focus + loading + empty + error at desktop,
and default + long-content at mobile. Add cells the feature warrants.

Use `take_snapshot` (the a11y/DOM text snapshot) in addition to `take_screenshot`
for each key state — the snapshot exposes raw identifiers, missing labels, and DOM
structure the pixel screenshot can hide.

## 3. Audits (objective, not opinion)

- `lighthouse_audit` (or performance trace) on the primary route. Record
  Performance / Accessibility / Best-Practices scores. Accessibility < 90 is a
  blocking finding.
- Accessibility pass via the a11y snapshot: every interactive element reachable by
  keyboard, has an accessible name, tap targets ≥ 44px, color-contrast adequate.
  (See the `a11y-debugging` skill from chrome-devtools-mcp for the deep checklist.)
- Reduced motion: confirm animations respect `prefers-reduced-motion`.

## 4. Package for review

Write, into `.ux-ui/measure/<feature-slug>/`:
- the screenshots, named `<state>__<breakpoint>.png`
- `snapshots.md` — the DOM/a11y text snapshots per state
- `signals.md` — console errors, network failures, lighthouse scores
- `context.md` — what feature/route this is, what changed in this diff, the design
  intent (from the plan), and which state cells were skipped and why.

Hand this directory to the `ux-ui-art-director` agent. Everything it reviews is a
real measurement — no cell is described, only shown.
