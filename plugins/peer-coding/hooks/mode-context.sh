#!/usr/bin/env bash
# UserPromptSubmit hook: when peer-coding mode is on, add a context note.
# Prints nothing when off, so normal sessions pay no token cost.
# Never blocks the prompt: always exits 0.
set -uo pipefail

MODE_SH="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/scripts/mode.sh"
input="$(cat)"

# Don't inject into the toggle command itself.
if printf '%s' "$input" | grep -q 'peer-coding:mode'; then exit 0; fi

mode="$(bash "$MODE_SH" get 2>/dev/null || echo off)"

if [ "$mode" = "on" ]; then
  # Structured context is consumed by both hosts; plain stdout is not reliable on Codex.
  cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[peer-coding: ON] For implementation work in this prompt, use the\n`peer-coding:run` skill (start at its \"Mode gate\"). Questions, explanations and\ntrivial edits may be handled directly — say so in one line. The user can turn this\noff with the `peer-coding:mode` skill (argument: off)."}}
JSON
fi
exit 0
