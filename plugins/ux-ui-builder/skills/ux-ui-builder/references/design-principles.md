# Design Principles — self-contained aesthetic + correctness bar

This plugin must work in a project with **zero prior configuration**. So it carries
its own design bar here rather than depending on any host repo's rules. If the host
project *does* define design rules (e.g. a `CLAUDE.md` design section, a design-tokens
file, a component library), those win — read them first and treat this file as the
floor beneath them.

Two layers matter, and they are judged separately:

- **Correctness** — is the render actually right? (states designed, no raw
  identifiers, no console errors, accessible, consistent). Non-negotiable.
- **Elegance** — is it distinctive and intentional, not a templated default?

---

## A. Correctness bar (blocking — a violation cannot ship)

1. **Cognitive hierarchy.** Primary action/information reads first; secondary is
   dimmed/smaller. One clear focal point per view.
2. **Spacing rhythm.** Padding/margin/gap come from a consistent scale, not ad-hoc
   pixels. Nothing cramped, nothing adrift. Alignment (left/right/baseline) holds.
3. **No raw identifiers.** Never expose UUIDs, enum codes, DB/field paths
   (`names.0.use`), raw ISO timestamps, or system vocabulary. Show human labels,
   resolved display values, and human-readable formats.
4. **All states designed.** loading / empty / error / long-content each have an
   intentional design. No bare spinners, no blank screens, no unhandled overflow.
5. **Consistency.** Matches the app's existing patterns (button/badge/card/table/modal
   conventions, spacing units). A new screen should look like it belongs.
6. **Readability & contrast.** Type size, line-height, and contrast suit sustained
   real use. Meets WCAG AA contrast.
7. **Interaction affordance & a11y.** Interactive elements look interactive; hover /
   focus / active / disabled are visually distinct; keyboard-navigable; accessible
   names present; tap targets ≥ 44px; `prefers-reduced-motion` respected.

## B. Elegance bar (distinctiveness — avoid the templated look)

Adapted from the `frontend-design` skill. The goal is UI that reads as a deliberate
choice, not an AI default.

- **Escape the default cluster.** AI UI clusters around a few looks: cream +
  high-contrast serif + terracotta; near-black + one acid accent; hairline-rule
  broadsheet. These are defaults, not choices. If the project has a real visual
  direction, follow it exactly; where an axis is free, don't spend that freedom on a
  cliché.
- **Type carries personality.** Deliberate display/body pairing and a clear type
  scale with intentional weights and spacing — not a neutral delivery vehicle.
- **Structure encodes meaning.** Numbering, eyebrows, dividers should encode
  something true (a real sequence), not decorate. Question every ornamental marker.
- **Motion serves the subject.** One orchestrated moment beats scattered effects.
  Too much motion reads as AI-generated; restraint reads as intent.
- **Spend boldness once.** Let one signature element be memorable; keep everything
  around it quiet and disciplined. Chanel's rule: remove one accessory before leaving.
- **Copy is design material.** Name things by what the user controls, active voice,
  sentence case, consistent verbs across a flow. Errors explain what happened and how
  to fix it; empty states invite action.

## C. Clinical / data-dense contexts (when applicable)

Many admin/EHR/dashboard UIs are data-dense and used for long sessions. There,
elegance means *disciplined density*: legibility over decoration, scannable tables,
predictable layout, and never sacrificing the correctness bar for a flourish. Apply
the elegance bar with restraint — the signature element should not cost clarity.
