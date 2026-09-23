<p align="center">
  <strong>ux-ui-builder</strong>
</p>

<p align="center">
  <strong>Build web and mobile UI the way a studio ships it — measured on the real render, critiqued by an art director, gated at commit.</strong>
</p>

<p align="center">
  <a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-1.1.0-blue" alt="Version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
  <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#what-it-does">What it does</a> &bull;
  <a href="#the-loop">The loop</a> &bull;
  <a href="#mobile-measurement-backends">Mobile backends</a> &bull;
  <a href="#the-commit-gate">Commit gate</a> &bull;
  <a href="#faq">FAQ</a>
</p>

<p align="center">
  <a href="README.md">English</a> &bull;
  <a href="README.ko.md">한국어</a> &bull;
  <a href="README.ja.md">日本語</a> &bull;
  <a href="README.zh-CN.md">简体中文</a> &bull;
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <sub>Part of <a href="../../README.md">because-i-needed</a></sub>
</p>

---

Agents implement UI poorly when they work from imagination — invisible overflow, a missing focus ring, an unhandled empty state, a raw UUID leaking into a label. None of it shows up until you look at the real render.

**ux-ui-builder removes imagination from the loop.** Every UI change is measured on the actual render — a browser page via chrome-devtools, or a real device/simulator for mobile — critiqued by an art-director agent against the *measured* snapshots, iterated until it is both correct and elegant, and then hard-gated: you cannot commit UI the art director has not APPROVED against the exact staged diff.

## Features

- **Measured, never imagined** — the skill drives the bundled **chrome-devtools MCP** to capture the real render: default / hover / focus / loading / empty / error / long-content across mobile / tablet / desktop, plus DOM/a11y snapshots, console + network signals, and a Lighthouse audit.
- **Mobile, too** *(new in 1.1)* — a second skill, `ux-ui-builder-mobile`, detects the app's stack (React Native / Expo / Flutter / native iOS / native Android / mobile-web), picks a measurement backend that returns **real pixels** from a booted device or simulator, and captures a device × orientation × state matrix. Where no MCP can screenshot the stack, a bundled **CLI snapshot harness** (`simctl` / `adb`) does.
- **Art-director hard gate** — the `ux-ui-art-director` agent (Opus) critiques only the measured artifacts; for mobile, `ux-ui-mobile-art-director` judges by the platform idiom (Apple HIG / Material). Any critical/major defect → `CHANGES_REQUIRED`. They can re-measure states themselves (the mobile director on MCP-capable stacks; on CLI-harness-only stacks it demands the capture instead); they cannot edit code (reviewer/implementer separation).
- **Diff-bound approvals** — the approval is bound to a sha256 of the staged UI diff. Re-edit the UI and the hash changes, so the gate blocks again. "Approve once and keep editing" is structurally impossible; no stale or forged approvals.
- **Autonomous iteration** — build → measure → critique → fix → re-measure, up to 3 cycles, with no extra user prompting. Elegant frontend, first commit. (The mobile loop pauses once, at the start, to confirm the measurement backend.)
- **Zero-config** — bundles its own browser and mobile MCPs and carries its own correctness + elegance bar, so it works in a project with nothing set up. If the host project *does* define design rules, those win.
- **Conservative blast radius** — the gate only fires on genuine UI file types: web (`.tsx .jsx .vue .svelte .astro .css .scss .sass .less .html`) and mobile (`.swift .kt .dart .storyboard .xib`, Android `res/layout*/**/*.xml`). Bare `.ts`/`.js`/`.java` and non-layout `.xml` are excluded so backend-only commits are never blocked.

## Installation

### Via Claude Code plugin marketplace

1. In Claude Code, run `/plugin`.
2. Marketplaces → Add Marketplace.
3. Enter the URL: `https://github.com/zeriong/because-i-needed.git` (or a local path to this repo).
4. Install `ux-ui-builder`.

### Or via CLI

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git   # or a local path
claude plugin install ux-ui-builder@because-i-needed
```

### Or wire it directly in `~/.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "because-i-needed": {
      "source": { "source": "git", "url": "https://github.com/zeriong/because-i-needed.git" }
    }
  },
  "enabledPlugins": { "ux-ui-builder@because-i-needed": true }
}
```

Installing registers everything automatically: the four MCP servers (`chrome-devtools`, `mobile-mcp`, `ios-simulator`, `flutter`), the commit-gate hook, the `ux-ui-art-director` and `ux-ui-mobile-art-director` agents, and the `ux-ui-builder` and `ux-ui-builder-mobile` skills.

## Requirements

- **Web**: **Node.js** (the bundled `chrome-devtools-mcp` runs via `npx`), a local **Chrome**, and a runnable **dev server** for the project whose UI you are building.
- **Mobile**: the platform SDK for your stack — Xcode + simulators (iOS, macOS-only), Android SDK + emulator, or the Flutter SDK — with the app running on a booted device/simulator. The mobile MCPs (`@mobilenext/mobile-mcp`, `ios-simulator-mcp`, `dart mcp-server`) start only where their tool is installed; the `mobile-snapshot.sh` harness needs only `simctl`/`adb`.
- **git** work tree, and `shasum`/`sha256sum` (present on macOS/Linux by default).

## Quick Start

```
cd your-project
# In Claude Code, just build UI. When you implement or change a screen:
/ux-ui-builder:ux-ui-builder          # web
/ux-ui-builder:ux-ui-builder-mobile   # mobile (RN / Flutter / iOS / Android / mobile-web)
```

Both skills also trigger on their own when you ask to build, fix, redesign or style a component, page, screen, form, sheet, list or layout.

The web skill will:

1. Self-check the browser MCP and your dev server (starts it if needed).
2. Plan a design intent for this specific feature (not a templated default).
3. Build the UI.
4. Measure the real render across the state × breakpoint matrix.
5. Hand the measurement to the art director for critique.
6. Apply fixes and re-measure until `APPROVED` (cap = 3).
7. Record the approval that unblocks your commit.

The mobile skill runs the same loop, but step 1 first detects your stack, runs the harness `doctor`, and asks you to confirm the measurement backend — the only interactive pause — and step 4 measures a device × orientation × state matrix on the booted target.

If you try to commit UI without a matching approval, the gate blocks it and tells you to run the loop.

## What it does

```
your-project/
└── .ux-ui/
    ├── measure/<feature>/        # screenshots, snapshots.md, signals.md, context.md
    └── approvals/<diff-hash>.json # the APPROVED artifact the commit gate checks
```

The plugin itself ships:

```
plugins/ux-ui-builder/
├── .claude-plugin/plugin.json          # manifest + bundled MCPs (chrome-devtools, mobile-mcp, ios-simulator, flutter)
├── hooks/hooks.json                    # PreToolUse → commit gate
├── scripts/
│   ├── ui-commit-gate.sh               # gate: hash | approve <feature> [dir] | hook-block (web + mobile types)
│   └── mobile-snapshot.sh              # CLI snapshot harness: doctor | capture <ios|android> <dir> <label>
├── agents/
│   ├── ux-ui-art-director.md           # web art director (measures + critiques, Opus)
│   └── ux-ui-mobile-art-director.md    # mobile art director (HIG / Material idiom, Opus)
└── skills/
    ├── ux-ui-builder/                  # web: measure → critique → iterate → gate
    │   ├── SKILL.md
    │   └── references/
    │       ├── design-principles.md    # correctness + elegance bar (self-contained)
    │       ├── measurement-protocol.md # exact chrome-devtools capture protocol
    │       └── review-rubric.md        # verdict format + APPROVED artifact contract
    └── ux-ui-builder-mobile/           # mobile: detect → measure → critique → iterate → gate
        ├── SKILL.md
        └── references/
            ├── backend-detection.md          # detect the stack + pick a real-pixel backend
            ├── mobile-design-principles.md   # HIG / Material, safe areas, tap targets, gestures, keyboard, dark mode
            ├── mobile-measurement-protocol.md # per-backend capture (device × orientation × state)
            └── mobile-review-rubric.md       # verdict format + APPROVED artifact contract
```

## The loop

| Step | Responsibility |
|------|----------------|
| 0 | **Bootstrap** — confirm the browser MCP + dev server; pick a feature slug. *Mobile:* detect the stack, run `mobile-snapshot.sh doctor`, confirm the backend with you, make sure the app runs on a booted target |
| 1 | **Plan** — a compact design intent for *this* feature; avoid AI-default looks (mobile: within the platform idiom) |
| 2 | **Build** — implement, reusing existing components/tokens |
| 3 | **Measure** — capture the real state × breakpoint matrix + audits (mobile: device × orientation × state) — mandatory |
| 4 | **Critique** — spawn `ux-ui-art-director` (web) or `ux-ui-mobile-art-director` (mobile) on the measured artifacts (hard gate) |
| 5 | **Iterate** — apply fixes, go back to step 3, re-review (cap = 3) |
| 6 | **Record approval** — only on APPROVED; unblocks the commit for this exact diff |

Measurement is never optional and never faked. **No screenshot → no review → no commit.**

## Mobile measurement backends

Every mobile stack has a path to real pixels. The skill prefers an MCP that returns both a screenshot and an a11y/view tree, then any MCP that returns a screenshot, then the CLI harness:

| Detected stack | Preferred backend | Screenshot | A11y / structure |
|----------------|-------------------|------------|------------------|
| Mobile-web | `chrome-devtools` MCP (bundled) | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP (`dart mcp-server`) | screenshot tool | widget tree + hot reload |
| Native iOS | `ios-simulator` MCP (idb, macOS-only) | `screenshot` / `ui_view` | `ui_describe_all` |
| React Native | **CLI snapshot harness** (default; `mobile-mcp` offered as an alternative) | `mobile-snapshot.sh capture …` | `adb uiautomator dump` (Android); pixels-only (iOS) |
| Native Android / cross-platform | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| Any stack, no functional MCP | **CLI snapshot harness** | `mobile-snapshot.sh capture …` | `adb uiautomator dump` (Android); pixels-only (iOS) |

Full rules and tie-breakers: [`backend-detection.md`](skills/ux-ui-builder-mobile/references/backend-detection.md).

## The commit gate

A `PreToolUse` hook runs `ui-commit-gate.sh` before every `Bash` call. It:

1. Allows anything that is not a `git commit` (fast path).
2. Allows commits with no staged UI files.
3. For a UI commit, computes a sha256 of the staged UI diff and looks for
   `.ux-ui/approvals/<hash>.json` with `verdict: APPROVED`.
4. If found → allow. Otherwise → **exit 2**, blocking the commit with a message telling
   you to run the loop.

Because the approval is bound to the diff hash, any further UI edit invalidates it —
the gate is non-forgeable and never stale. Web and mobile UI share the same gate.

Override which files count as UI with the `UX_UI_GLOBS` env var. Artifacts live
under `.ux-ui/`; add it to `.gitignore` if you don't want to commit them.

## FAQ

**Why not just let the model eyeball a screenshot it took?**
Because "took a screenshot once" isn't a discipline. This plugin *mandates* the full state × breakpoint matrix, a11y snapshots, and console/network/Lighthouse signals, then blocks the commit until an independent art-director agent signs off on those artifacts. Enforcement, not vibes.

**Does this rebuild the browser automation as a custom MCP?**
No. Browser automation already exists as `chrome-devtools-mcp`, which this plugin bundles (the mobile MCPs likewise). The value added is the *orchestration and enforcement* — measure → critique → iterate → gate — which lives in a skill + agent + hook, because an MCP server cannot spawn Claude Code subagents or drive a review loop.

**Why an art director instead of just the main model?**
Separation. The building agent is invested in its own work; a fresh agent judging only the measured artifacts, unable to edit the code, catches what the builder rationalizes away. It's the same reason studios have a review step.

**Will it block my backend commits?**
No. The gate only triggers on UI file types and deliberately excludes bare `.ts`/`.js`/`.java` and non-layout `.xml`. Backend-only commits pass untouched.

**Can I approve once and keep editing?**
No — that's the point. The approval is bound to the staged UI diff hash. Change one line of UI and the hash no longer matches, so the gate blocks again until you re-run the loop.

**My mobile stack has no MCP that can screenshot it. Now what?**
The CLI snapshot harness (`mobile-snapshot.sh`) captures real PNGs straight from the simulator/emulator via `simctl`/`adb`, and the art director reviews those. The one thing it never does is review imagined states.

**What if it can't reach the dev server, Chrome, or a booted device?**
It stops and tells you, rather than falling back to reviewing imaginary states. A broken environment is a hard stop, by design.

## License

MIT. See [LICENSE](../../LICENSE).

## Acknowledgments

The measure-then-critique discipline draws on the `frontend-design` skill (aesthetic direction) and the `chrome-devtools-mcp` plugin (browser measurement). The hard-gate and diff-bound-approval pattern follows the review-gate design from the author's harness-engineering work.
