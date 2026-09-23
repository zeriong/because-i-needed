#!/usr/bin/env bash
# mobile-snapshot.sh — the mobile UI-review harness's guaranteed real-pixel capture path.
#
# When no debugging MCP can hand the ux-ui-mobile-art-director a reviewable screenshot for
# the detected stack (e.g. a React Native app with no functional mobile MCP), this script
# captures the currently-booted simulator/emulator straight from the platform SDK the
# developer already has — so the director never has to review from imagination.
#
# Modes:
#   doctor                                 Report which backends are available on this
#                                          machine (simctl / adb / flutter / dart) and
#                                          whether a simulator/emulator is booted.
#   capture <ios|android> <out-dir> <label>
#                                          Capture one screenshot into
#                                          <out-dir>/<label>.png (real pixels). On Android
#                                          also dump the view hierarchy to
#                                          <out-dir>/<label>.uihierarchy.xml (best-effort).
#
# The MCP tools cannot be probed from a shell; the skill checks those in-session. This
# script only covers the CLI-native backends.
set -euo pipefail

have() { command -v "$1" >/dev/null 2>&1; }

ios_booted() { have xcrun && xcrun simctl list devices 2>/dev/null | grep -q '(Booted)'; }
android_device() { have adb && [ -n "$(adb devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1}')" ]; }

doctor() {
  echo "ux-ui mobile snapshot — backend doctor"
  echo "  xcrun simctl (iOS) : $(have xcrun && echo yes || echo no)"
  echo "  iOS sim booted     : $(ios_booted && echo yes || echo 'no — boot one with: xcrun simctl boot <udid>')"
  echo "  adb (Android)      : $(have adb && echo yes || echo no)"
  echo "  Android device/emu : $(android_device && echo yes || echo 'no — start an emulator or connect a device')"
  echo "  flutter            : $(have flutter && echo yes || echo no)"
  echo "  dart (flutter MCP) : $(have dart && echo yes || echo no)"
  echo
  echo "Note: mobile MCP tools (mobile-mcp / ios-simulator / flutter / chrome-devtools) are"
  echo "checked by the skill in-session, not here. Prefer an MCP that returns screenshots;"
  echo "use this harness when none is functional for the detected stack."
}

capture() {
  local platform="${1:-}" outdir="${2:-}" label="${3:-}"
  if [ -z "$platform" ] || [ -z "$outdir" ] || [ -z "$label" ]; then
    echo "usage: mobile-snapshot.sh capture <ios|android> <out-dir> <label>" >&2
    exit 1
  fi
  mkdir -p "$outdir"
  local png="$outdir/$label.png"

  case "$platform" in
    ios)
      have xcrun || { echo "mobile-snapshot: 'xcrun' not found (need Xcode command-line tools, macOS only)." >&2; exit 1; }
      ios_booted || { echo "mobile-snapshot: no booted iOS simulator. Boot one first (xcrun simctl boot <udid>)." >&2; exit 1; }
      xcrun simctl io booted screenshot "$png"
      echo "captured: $png"
      echo "note: iOS CLI capture is pixels-only; use ios-simulator/mobile MCP for the a11y tree."
      ;;
    android)
      have adb || { echo "mobile-snapshot: 'adb' not found (need the Android SDK platform-tools)." >&2; exit 1; }
      android_device || { echo "mobile-snapshot: no Android device/emulator connected (check 'adb devices')." >&2; exit 1; }
      adb exec-out screencap -p > "$png"
      echo "captured: $png"
      # View hierarchy for raw-identifier / label / tap-target checks (best-effort).
      local xml="$outdir/$label.uihierarchy.xml"
      if adb shell uiautomator dump /sdcard/ux-ui-dump.xml >/dev/null 2>&1 \
         && adb exec-out cat /sdcard/ux-ui-dump.xml > "$xml" 2>/dev/null \
         && [ -s "$xml" ]; then
        adb shell rm -f /sdcard/ux-ui-dump.xml >/dev/null 2>&1 || true
        echo "captured: $xml"
      else
        rm -f "$xml" 2>/dev/null || true
        echo "note: view-hierarchy dump unavailable (uiautomator failed); screenshot captured only."
      fi
      ;;
    *)
      echo "mobile-snapshot: unknown platform '$platform' (use: ios | android)." >&2
      exit 1
      ;;
  esac
}

mode="${1:-doctor}"
case "$mode" in
  doctor)  doctor ;;
  capture) shift; capture "$@" ;;
  *) echo "mobile-snapshot: unknown mode '$mode' (use: doctor | capture)" >&2; exit 1 ;;
esac
