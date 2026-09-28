#!/usr/bin/env bash
# Cross-vendor context parity audit. READ-ONLY: reports, never changes files.
#
# Answers three questions for the repo you run it in:
#   1. Instructions — does each vendor get the project's instructions?
#      (Claude reads CLAUDE.md, falling back to AGENTS.md where there is no CLAUDE.md;
#       Codex reads AGENTS.override.md, then AGENTS.md, then its configured fallback names)
#   2. Enforcement — which hooks exist, and for which vendor only?
#   3. Worktrees — which context files are not committed, and so will be missing
#      in a worker's worktree?
#
# Usage: context-audit.sh            (from anywhere inside the repo)
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not a git repo" >&2; exit 2; }
cd "$ROOT" || exit 2

state() {
  if [ ! -e "$1" ]; then echo "missing"
  elif git ls-files --error-unmatch "$1" >/dev/null 2>&1; then echo "tracked"
  elif git check-ignore -q "$1" 2>/dev/null; then echo "ignored"
  else echo "untracked"; fi
}

# Codex reads CLAUDE.md where there is no AGENTS.md when the user's config lists it as a fallback.
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
CODEX_CFG="$CODEX_DIR/config.toml"
fallback=""
# Top-level keys only: a key after a [table] header belongs to that table (TOML).
[ -f "$CODEX_CFG" ] && fallback="$(awk '/^[[:space:]]*\[/ { exit } /^[[:space:]]*project_doc_fallback_filenames[[:space:]]*=/ { sub(/^[^=]*=[[:space:]]*/, ""); print; exit }' "$CODEX_CFG")"
case "$fallback" in *CLAUDE.md*) codex_fallback=1 ;; *) codex_fallback=0 ;; esac

echo "# Context parity audit"
echo "repo: $ROOT"
echo

# ---------------------------------------------------------------- 1. instructions
echo "## 1. Instructions"
echo
echo "| dir | CLAUDE.md | AGENTS.md | parity |"
echo "|---|---|---|---|"
dirs="$(find . \( -name .git -o -name node_modules -o -name .claude-x-codex \) -prune -o \
          \( -name CLAUDE.md -o -name AGENTS.md \) -print 2>/dev/null \
        | while IFS= read -r f; do dirname "$f"; done | sort -u)"
[ -z "$dirs" ] && echo "| . | missing | missing | none — no instructions for either vendor |"
printf '%s\n' "$dirs" | while IFS= read -r d; do
  [ -n "$d" ] || continue
  c="$d/CLAUDE.md"; a="$d/AGENTS.md"
  cs="$(state "$c")"; as="$(state "$a")"
  parity="ok"
  if [ "$cs" != "missing" ] && [ "$as" = "missing" ]; then
    if [ "$codex_fallback" = 1 ]; then parity="ok (Codex fallback in user config)"
    else parity="GAP: Codex can't see this unless the fallback is set (see Layer 1)"; fi
  elif [ "$as" != "missing" ] && [ "$cs" = "missing" ]; then
    parity="ok (Claude Code falls back to AGENTS.md)"
  elif [ "$cs" != "missing" ] && [ "$as" != "missing" ]; then
    if grep -q '@AGENTS.md' "$c" 2>/dev/null || grep -q 'CLAUDE.md' "$a" 2>/dev/null; then
      parity="ok (pointer)"
    else
      parity="CHECK: Claude reads only CLAUDE.md, Codex only AGENTS.md — may drift"
    fi
  fi
  echo "| ${d#./} | $cs | $as | $parity |"
done
for f in CLAUDE.local.md AGENTS.override.md; do
  [ -e "$f" ] && echo && echo "note: $f exists ($(state "$f")) — personal overrides; not shared with the other vendor."
done
echo

# ---------------------------------------------------------------- 2. vendor config
echo "## 2. Vendor configuration"
echo
echo "| path | vendor | state |"
echo "|---|---|---|"
for p in .claude/settings.json .claude/settings.local.json .claude/skills .claude/agents \
         .claude/commands .claude/rules .mcp.json; do
  echo "| $p | claude | $(state "$p") |"
done
for p in .codex .codex/config.toml .agents; do
  echo "| $p | codex (project) | $(state "$p") |"
done
profiles=""
for f in "$CODEX_DIR"/cxc-*.config.toml; do
  [ -f "$f" ] && profiles="$profiles$(basename "$f" .config.toml) "
done
legacy=""
if [ -f "$CODEX_CFG" ]; then
  legacy="$(grep -Eo '^\[profiles\.[^]]+\]' "$CODEX_CFG" | tr -d '[]' | sed 's/^profiles\.//' | tr '\n' ' ')"
  echo "| $CODEX_CFG | codex (user) | present; project_doc_fallback_filenames: ${fallback:-unset} |"
else
  echo "| $CODEX_CFG | codex (user) | missing |"
fi
echo "| $CODEX_DIR/cxc-*.config.toml | codex (user profiles) | ${profiles:-none} |"
if [ -n "$legacy" ]; then
  echo
  echo "warning: $CODEX_CFG has legacy [profiles.*] tables ($legacy). Recent Codex CLIs refuse"
  echo "--profile while they exist; move each into $CODEX_DIR/<name>.config.toml."
fi
echo

# ---------------------------------------------------------------- 3. hooks
echo "## 3. Hooks (enforcement that may bind only one vendor)"
echo
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import json, os
rows = []
for f in (".claude/settings.json", ".claude/settings.local.json"):
    if not os.path.isfile(f):
        continue
    try:
        data = json.load(open(f))
    except Exception as e:
        rows.append((f, "?", "?", f"unreadable: {e}"))
        continue
    for event, entries in (data.get("hooks") or {}).items():
        for entry in entries or []:
            for h in entry.get("hooks") or []:
                rows.append((f, event, entry.get("matcher", "*"), h.get("command", h.get("type", "?"))))
if not rows:
    print("No Claude hooks in project settings.")
else:
    print("| file | event | matcher | command |")
    print("|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    print()
    print("These run only when **Claude** acts. Classify each: enforcement → move its check")
    print("into a shared gate script; context injection → cover it in the context pack;")
    print("convenience → ignore.")
PY
else
  echo "python3 not found — inspect .claude/settings*.json \"hooks\" manually."
fi
if [ -f .codex/config.toml ] && grep -qi 'hook' .codex/config.toml; then
  echo
  echo "Codex project config mentions hooks — these run only when **Codex** acts."
fi
echo

# ---------------------------------------------------------------- 4. worktree gaps
echo "## 4. Not committed → missing in worker worktrees"
echo
gaps=""
for p in CLAUDE.local.md AGENTS.override.md .claude/settings.local.json .mcp.json; do
  s="$(state "$p")"
  if [ "$s" = "ignored" ] || [ "$s" = "untracked" ]; then gaps="$gaps- $p ($s)
"; fi
done
if [ -d .claude ]; then
  ign="$(git ls-files --others --ignored --exclude-standard --directory .claude 2>/dev/null \
         | grep -v '^\.claude/settings\.local\.json$' | sed 's/^/- /; s/$/ (ignored)/')"
  unt="$(git ls-files --others --exclude-standard --directory .claude 2>/dev/null \
         | sed 's/^/- /; s/$/ (untracked)/')"
  [ -n "$ign" ] && gaps="$gaps$ign
"
  [ -n "$unt" ] && gaps="$gaps$unt
"
fi
if [ -n "$gaps" ]; then printf '%s' "$gaps"; else echo "(no uncommitted agent context files found)"; fi
echo
echo "Ignored top-level entries (candidates for knowledge-tool output, e.g. code graphs):"
git status --ignored --porcelain=v1 2>/dev/null | sed -n 's/^!! //p' \
  | grep -vE '^(node_modules|dist|build|out|coverage|\.next|\.turbo|\.cache|\.claude-x-codex|\.DS_Store)/?$' \
  | grep -v '/.' | sed 's/^/- /' | head -30
echo
echo "Add the ones workers need to .claude-x-codex/context-manifest (policy: skills/run/references/context-bridge.md)."
