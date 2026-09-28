#!/usr/bin/env bash
# UserPromptSubmit hook: when claude-x-codex mode is on, add a context note.
# Prints nothing when off, so normal sessions pay no token cost.
# Never blocks the prompt: always exits 0.
set -uo pipefail

MODE_SH="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/scripts/mode.sh"
input="$(cat)"

# Don't inject into the toggle command itself.
if printf '%s' "$input" | grep -q 'claude-x-codex:mode'; then exit 0; fi

mode="$(bash "$MODE_SH" get 2>/dev/null || echo off)"

if [ "$mode" = "on" ]; then
  cat <<'NOTE'
[claude-x-codex: ON] For implementation work in this prompt, use the
`claude-x-codex:run` skill (start at its "Mode gate"). Questions, explanations and
trivial edits may be handled directly — say so in one line. The user can turn this
off with /claude-x-codex:mode off.
NOTE
fi
exit 0
