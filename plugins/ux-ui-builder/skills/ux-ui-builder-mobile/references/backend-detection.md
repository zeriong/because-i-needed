# Backend Detection + Selection — pick a real-pixel measurement path per stack

The mobile world has no single "chrome-devtools." Different stacks debug through
different tools, and some have no MCP that gives the art director a reviewable *visual*
snapshot at all. So this skill **detects the stack, then guarantees real pixels** — from
a screenshot-capable MCP where one exists, or from a **CLI snapshot harness** where none
does. This file is step 0 of the loop.

---

## 1. Detect the stack (read the repo — do not guess)

Match top-down; a repo can hit more than one (e.g. RN with native modules) — pick the
one that owns the screen you are changing.

| Stack | Signals (files / deps) |
|-------|------------------------|
| **Flutter** | `pubspec.yaml` with a `flutter:` section, `lib/main.dart`, `*.dart` widgets |
| **React Native (Expo)** | `package.json` dep `expo`, `app.json`/`app.config.*`, `expo` in scripts |
| **React Native (bare)** | `package.json` dep `react-native`, `metro.config.js`, sibling `ios/` + `android/` |
| **Native iOS** | `*.xcodeproj`/`*.xcworkspace`, `Package.swift`, `*.swift`, `Info.plist`, `*.storyboard`/`*.xib` |
| **Native Android** | `settings.gradle(.kts)`, `build.gradle(.kts)`, `AndroidManifest.xml`, `*.kt`/`*.java`, `res/layout/` |
| **Responsive mobile-web** | a web framework (`next`/`vite`/`react-dom`/`vue`/`svelte`) and **no** native shell |

Also run the harness doctor to see what is actually installed and booted:

```
"${CLAUDE_PLUGIN_ROOT}/scripts/mobile-snapshot.sh" doctor
```

It reports which of `xcrun simctl`, `adb`, `flutter`/`dart`, and a booted
simulator/emulator are present, and whether the plugin's mobile MCP tools are live in
this session.

## 2. Choose the measurement backend

Prefer, in order: an MCP that returns **both a real screenshot and an a11y/view tree**;
then any MCP that returns a screenshot; then the **CLI snapshot harness** (always
available when the platform SDK is installed — which it must be to run the app at all).

| Detected stack | Preferred backend | Screenshot tool | A11y / structure |
|----------------|-------------------|-----------------|------------------|
| Mobile-web | `chrome-devtools` MCP (bundled) | `take_screenshot` + `emulate`/`resize_page` | `take_snapshot` |
| Flutter | `flutter` MCP (`dart mcp-server`) | screenshot tool | widget tree + hot reload |
| Native iOS | `ios-simulator` MCP (idb) | `screenshot` / `ui_view` | `ui_describe_all` |
| **React Native** | **CLI snapshot harness** (default) | `mobile-snapshot.sh capture …` | `adb uiautomator dump` (Android); pixels-only (iOS) |
| Native Android / cross-platform | `mobile-mcp` MCP | `mobile_take_screenshot` | `mobile_list_elements_on_screen` |
| **Any stack, no functional MCP** | **CLI snapshot harness** | `mobile-snapshot.sh capture …` | `adb uiautomator dump` (Android); pixels-only (iOS) |

Notes that decide ties:
- **React Native defaults to the CLI snapshot harness.** RN has no RN-specific
  visual-review MCP, and the director cannot review a JS component tree — it needs
  pixels. So capture RN via `mobile-snapshot.sh` (`simctl`/`adb`) by default and say so
  when presenting the choice. `mobile-mcp` *can* screenshot an RN app at the OS level, so
  offer it as an alternative when it is functional — but do not silently pick it over the
  CLI path.
- **Flutter** is the one true "devtools" case: the `flutter` MCP exposes the widget tree
  and hot reload, shrinking the re-measure loop to seconds. Use it when Flutter is
  detected and the MCP is live.
- **iOS-deep** (`ios-simulator` MCP) is macOS-only (needs Xcode + idb). On non-macOS or
  when idb is missing, fall back to `mobile-mcp` or the CLI harness.

## 3. Present the choice to the user (the one interactive pause)

Before measuring, tell the user — briefly — the detected stack, the recommended backend,
its limitation, and the fallback. Then let them confirm or pick. Template:

> Detected **<stack>**. Recommended measurement backend: **<backend>** (<one-line
> capability>). Limitation: <e.g. "iOS-only", "requires a booted emulator">.
> If that backend can't give a reviewable snapshot on this machine, I'll set up **CLI
> command snapshots** (`mobile-snapshot.sh`) and have the art director review the
> CLI-captured PNGs instead. Proceed with <backend>, or choose another?

Only this step is interactive. Once the backend is chosen, run the rest of the loop
autonomously.

## 4. The CLI snapshot harness (guaranteed fallback)

When no MCP gives the director real pixels for the detected stack, wire up the harness.
It captures the currently-booted simulator/emulator screen straight from the platform
SDK the developer already has:

```
# one screenshot (+ Android view-hierarchy dump when available)
"${CLAUDE_PLUGIN_ROOT}/scripts/mobile-snapshot.sh" capture ios     .ux-ui/measure/<slug> default__iphone15
"${CLAUDE_PLUGIN_ROOT}/scripts/mobile-snapshot.sh" capture android .ux-ui/measure/<slug> default__pixel7
```

- iOS: `xcrun simctl io booted screenshot` → real PNG (pixels only).
- Android: `adb exec-out screencap -p` → real PNG, plus `adb exec-out uiautomator dump`
  → `<label>.uihierarchy.xml` for raw-identifier / label checks.
- You drive the app to each state yourself (in the app, or via an MCP's tap/swipe if one
  is partially available) and call `capture` once per cell. The PNGs land in the same
  `.ux-ui/measure/<slug>/` directory the art director reads — identical review contract,
  just a different capture source.

This is what makes the promise hold on every stack: **the art director never reviews from
imagination, even where no debugging MCP exists.**
