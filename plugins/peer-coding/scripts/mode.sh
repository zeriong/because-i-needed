#!/usr/bin/env bash
# peer-coding mode flag: one line, `mode=on` or `mode=off`.
#
# Resolution order (first match wins):
#   1. CXC_MODE env var            (on|off) — per-shell override
#   2. <repo>/.claude-x-codex/mode       — this project
#   3. ~/.config/claude-x-codex/mode   — your default everywhere
#   4. off
#
# Usage:
#   mode.sh get                 → prints on|off
#   mode.sh status              → prints value and where it came from
#   mode.sh on|off [--global]   → writes the project flag (or the global one)
#   mode.sh clear [--global]    → removes the project flag (or the global one)
set -euo pipefail

USER_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/claude-x-codex/mode"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PROJECT_FILE="$ROOT/.claude-x-codex/mode"

read_flag() {
  [ -f "$1" ] || return 0
  grep -Eo '^mode=(on|off)$' "$1" | head -1 | cut -d= -f2 || true
}

resolve() {
  case "${CXC_MODE:-}" in
    on|off) echo "$CXC_MODE env:CXC_MODE"; return ;;
  esac
  local v
  v="$(read_flag "$PROJECT_FILE")"; [ -n "$v" ] && { echo "$v $PROJECT_FILE"; return; }
  v="$(read_flag "$USER_FILE")";    [ -n "$v" ] && { echo "$v $USER_FILE"; return; }
  echo "off default"
}

exclude_state_dir() {
  local exclude
  exclude="$(git -C "$ROOT" rev-parse --git-path info/exclude 2>/dev/null)" || return 0
  case "$exclude" in /*) ;; *) exclude="$ROOT/$exclude" ;; esac
  mkdir -p "$(dirname "$exclude")"
  grep -qxF '.claude-x-codex/' "$exclude" 2>/dev/null || echo '.claude-x-codex/' >> "$exclude"
}

target_file() {
  if [ "${1:-}" = "--global" ]; then echo "$USER_FILE"; else echo "$PROJECT_FILE"; fi
}

cmd="${1:-status}"; shift || true

case "$cmd" in
  get)
    resolve | cut -d' ' -f1
    ;;
  status)
    read -r value source <<<"$(resolve)"
    echo "peer-coding mode: $value (source: $source)"
    echo '  invoke skills with / in Claude Code or $ in Codex'
    g="$(read_flag "$USER_FILE")"; p="$(read_flag "$PROJECT_FILE")"
    echo "  project: ${p:-unset}   global: ${g:-unset}"
    case "$source" in
      env:*)
        echo "  hint: CXC_MODE overrides both files — unset it in this shell to use them" ;;
      "$PROJECT_FILE")
        echo "  hint: this project overrides global — 'peer-coding:mode clear' to follow global" ;;
      "$USER_FILE")
        if [ "$value" = "on" ]; then
          echo "  hint: disable everywhere: 'peer-coding:mode off --global'  ·  this project only: 'peer-coding:mode off'"
        else
          echo "  hint: enable everywhere: 'peer-coding:mode on --global'  ·  this project only: 'peer-coding:mode on'"
        fi ;;
      default)
        echo "  hint: 'peer-coding:mode on' for this project, '--global' for every project" ;;
    esac
    ;;
  on|off)
    file="$(target_file "${1:-}")"
    mkdir -p "$(dirname "$file")"
    echo "mode=$cmd" > "$file"
    [ "$file" = "$PROJECT_FILE" ] && exclude_state_dir
    read -r value source <<<"$(resolve)"
    echo "peer-coding mode: set $cmd in $file → effective: $value (source: $source)"
    if [ "$file" = "$USER_FILE" ] && [ "$value" != "$cmd" ]; then
      echo "  note: still $value here because $source overrides global — 'peer-coding:mode clear' to follow global"
    fi
    ;;
  clear)
    file="$(target_file "${1:-}")"
    rm -f "$file"
    read -r value source <<<"$(resolve)"
    echo "peer-coding mode: cleared $file → effective: $value (source: $source)"
    ;;
  *)
    echo "usage: mode.sh get | status | on|off [--global] | clear [--global]" >&2
    exit 2
    ;;
esac
