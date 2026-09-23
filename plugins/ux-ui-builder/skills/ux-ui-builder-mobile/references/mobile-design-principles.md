# Mobile Design Principles — self-contained correctness + elegance bar

This skill works in a project with zero prior configuration, so it carries its own
mobile design bar. If the host project defines its own rules (a `CLAUDE.md` design
section, a design system, a platform theme, tokens), those win — read them first and
treat this file as the floor beneath them.

Two layers, judged separately:

- **Correctness** — is the render actually right on a real device? Non-negotiable.
- **Elegance** — is it a deliberate, native-feeling choice, not a templated default?

Follow the platform idiom: **iOS → Apple HIG**, **Android → Material**. A screen should
feel like it belongs on its platform, not like a web page in a shell.

---

## A. Correctness bar (blocking — a violation cannot ship)

1. **Safe areas & insets.** Content and controls respect the safe-area insets — status
   bar, notch / Dynamic Island, home indicator, rounded corners, and the software
   keyboard. Nothing important sits under the notch or is clipped by the home indicator.
2. **Tap targets.** Interactive targets are at least **44×44 pt (iOS)** / **48×48 dp
   (Android)** with adequate spacing; no two hit areas overlap or crowd.
3. **Thumb reach & ergonomics.** Primary actions sit in the comfortable thumb zone
   (lower half / bottom bar), not stranded in a top corner. Destructive actions are not
   where a thumb rests by default.
4. **Cognitive hierarchy.** One clear focal point per screen; primary reads first,
   secondary is dimmed/smaller. Navigation title, back affordance, and primary action
   are unmistakable.
5. **Spacing rhythm.** Padding/margins/gaps come from a consistent scale (e.g. 4/8 pt
   grid), not ad-hoc pixels. Alignment holds across list rows, form fields, and cards.
6. **No raw identifiers.** Never expose UUIDs, enum codes, field paths, or raw ISO
   timestamps. Show human labels, resolved values, and localized/human formats.
7. **All states designed.** loading (skeleton/spinner with layout), empty, error, and
   long-content each have an intentional design. No blank screens, no unhandled overflow,
   no text that truncates the meaning away.
8. **Keyboard handling.** The keyboard never covers the focused field or the submit
   button; the view scrolls/insets so the active input stays visible; return-key type and
   input type (email/number/etc.) are correct; there is a way to dismiss the keyboard.
9. **Gestures & affordance.** Interactive elements look interactive; pressed/disabled
   states are visually distinct; swipe/long-press actions are discoverable, not hidden;
   scroll and pull-to-refresh behave. Respects `reduce motion`.
10. **Readability & contrast.** Type size, line-height, and contrast suit a handheld
    screen at arm's length and meet WCAG AA. Supports Dynamic Type / font scaling without
    breaking layout.
11. **Dark mode & orientation.** If the app supports dark mode, the screen is correct in
    both; colors come from semantic tokens, not hardcoded hex. Rotation (or explicit
    lock) is handled without clipping.
12. **No console/log errors, no broken assets.** Runtime warnings, missing images/fonts,
    and crashes are blocking even if the layout "looks" fine.

## B. Elegance bar (distinctiveness — avoid the templated look)

Adapted from the `frontend-design` skill, for mobile. The goal is UI that reads as a
deliberate, native choice — not a generic cross-platform default.

- **Native idiom over generic.** Use the platform's real components and motion
  (iOS sheets/segmented controls/large titles; Material bottom sheets/FAB/ripples) rather
  than a lowest-common-denominator look, unless the brand deliberately overrides.
- **Type carries personality.** A deliberate display/body pairing and a clear scale with
  intentional weights — not the default system font at one size everywhere.
- **Structure encodes meaning.** Section grouping, list separators, and headers should
  encode something true, not decorate.
- **Motion serves the subject.** One orchestrated transition (shared element, sheet
  spring) beats scattered effects. Restraint reads as intent; over-animation reads as AI.
- **Spend boldness once.** Let one signature element be memorable; keep everything around
  it quiet and disciplined.
- **Copy is design material.** Sentence case, active voice, consistent verbs; errors say
  what happened and how to fix it; empty states invite the next action.

## C. Data-dense mobile contexts (when applicable)

Long lists, dashboards, and forms used for sustained sessions: elegance means disciplined
density — legible rows, predictable layout, generous tap targets despite the density, and
never sacrificing the correctness bar for a flourish.
