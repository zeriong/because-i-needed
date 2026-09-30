#!/usr/bin/env bash
# because-i-needed installer — pick plugins for Claude Code or Codex.
#
#   curl -fsSL https://raw.githubusercontent.com/zeriong/because-i-needed/main/install.sh | bash
#   ./install.sh                      # interactive (↑/↓ or j/k, space, a = all, enter, q)
#   ./install.sh --all                # everything, no prompt
#   ./install.sh --only harness,ux-ui # a subset, no prompt
#   ./install.sh --list               # show what's available
#   ./install.sh --dry-run            # print the commands instead of running them
#   ./install.sh --scope project      # passed to `claude plugin install` (user|project|local)
#   ./install.sh --host codex --all   # install with Codex CLI (user scope only)
#
# Works with bash 3.2+ (macOS default), Linux, WSL and Git Bash.
set -uo pipefail

REPO_URL="${BIN_REPO_URL:-https://github.com/zeriong/because-i-needed.git}"
RAW_URL="${BIN_RAW_URL:-https://raw.githubusercontent.com/zeriong/because-i-needed/main}"
TTY_IN="${BIN_TTY:-/dev/tty}"   # override only for testing

mode="interactive"; only=""; scope=""; dry=0; host="claude"
while [ $# -gt 0 ]; do
  case "$1" in
    --all) mode="all" ;;
    --only) mode="only"; only="${2:-}"; shift ;;
    --only=*) mode="only"; only="${1#--only=}" ;;
    --list) mode="list" ;;
    --scope) scope="${2:-}"; shift ;;
    --scope=*) scope="${1#--scope=}" ;;
    --host) [ $# -ge 2 ] || { echo '--host requires claude or codex' >&2; exit 2; }; host="$2"; shift ;;
    --host=*) host="${1#--host=}" ;;
    --dry-run) dry=1 ;;
    -h|--help) cat <<'HELP'
Usage: install.sh [--host claude|codex] [--all|--only a,b|--list] [--dry-run]
                  [--scope user|project|local]
Default host: claude. Codex supports only --scope user (or omit --scope).
Without a selection option, choose interactively with arrows, space and enter.
HELP
      exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

die() { echo "error: $*" >&2; exit 1; }
case "$host" in claude|codex) ;; *) die "unknown host: $host (use claude or codex)" ;; esac
case "$scope" in ""|user|project|local) ;; *) die "unknown scope: $scope" ;; esac
if [ "$host" = codex ] && [ -n "$scope" ] && [ "$scope" != user ]; then
  die "Codex plugin installation supports user scope only; omit --scope or use --scope user"
fi

# ------------------------------------------------------------------ catalog
# Use the local catalog only when this file itself is on disk (not piped from curl),
# so running `curl … | bash` inside some other repo never picks up the wrong catalog.
self="${BASH_SOURCE[0]:-}"
script_dir=""
[ -n "$self" ] && [ -f "$self" ] && script_dir="$(cd "$(dirname "$self")" && pwd)"
if [ -n "$script_dir" ] && [ -f "$script_dir/.claude-plugin/marketplace.json" ]; then
  catalog="$(cat "$script_dir/.claude-plugin/marketplace.json")"
else
  command -v curl >/dev/null 2>&1 || die "curl is required"
  catalog="$(curl -fsSL "$RAW_URL/.claude-plugin/marketplace.json")" || die "could not fetch marketplace.json"
fi

parse() {  # prints: line 1 = marketplace name, then "name<TAB>description" per plugin
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json,sys
d=json.load(sys.stdin); print(d.get("name",""))
for p in d.get("plugins",[]): print(p.get("name","")+"\t"+" ".join(str(p.get("description","")).split()))'
  elif command -v node >/dev/null 2>&1; then
    node -e 'let s="";process.stdin.on("data",c=>s+=c).on("end",()=>{const d=JSON.parse(s);
console.log(d.name||"");for(const p of d.plugins||[])console.log((p.name||"")+"\t"+String(p.description||"").split(/\s+/).join(" "))})'
  else
    die "python3 or node is required to read the catalog"
  fi
}
parsed="$(printf '%s' "$catalog" | parse)" || die "could not parse marketplace.json"
market="$(printf '%s\n' "$parsed" | head -1)"
[ -n "$market" ] || die "marketplace.json has no name"

names=(); descs=()
while IFS="$(printf '\t')" read -r n d; do
  [ -n "$n" ] || continue
  names+=("$n"); descs+=("$d")
done <<EOF
$(printf '%s\n' "$parsed" | tail -n +2)
EOF
count=${#names[@]}
[ "$count" -gt 0 ] || die "no plugins listed in marketplace.json"

if [ "$mode" = "list" ]; then
  echo "Marketplace: $market"
  i=0; while [ $i -lt "$count" ]; do printf '  %-18s %s\n' "${names[$i]}" "${descs[$i]}"; i=$((i+1)); done
  exit 0
fi

# ------------------------------------------------------------------ selection
sel=(); i=0; while [ $i -lt "$count" ]; do sel+=(1); i=$((i+1)); done   # default: all selected

if [ "$mode" = "only" ]; then
  i=0; while [ $i -lt "$count" ]; do sel[i]=0; i=$((i+1)); done
  IFS=',' read -r -a wanted <<<"$only"
  for w in "${wanted[@]}"; do
    found=0; i=0
    while [ $i -lt "$count" ]; do [ "${names[$i]}" = "$w" ] && { sel[i]=1; found=1; }; i=$((i+1)); done
    [ $found = 1 ] || die "unknown plugin: $w (see --list)"
  done
elif [ "$mode" = "interactive" ]; then
  if ! { [ -r "$TTY_IN" ] && : <"$TTY_IN"; } 2>/dev/null; then
    echo "No terminal available for selection — installing all. Use --only to choose." >&2
  else
    cursor=0          # 0 = "All", 1..count = plugins
    rows=$((count + 1))
    all_on() { local k=0; while [ $k -lt "$count" ]; do [ "${sel[$k]}" = 1 ] || return 1; k=$((k+1)); done; return 0; }
    draw() {
      local r=0 mark label
      printf '\033[%dA' "$rows" >&2 2>/dev/null || true
      while [ $r -lt $rows ]; do
        if [ $r -eq 0 ]; then
          all_on && mark="x" || mark=" "; label="All  (default)"
        else
          [ "${sel[$((r-1))]}" = 1 ] && mark="x" || mark=" "
          label="$(printf '%-18s %s' "${names[$((r-1))]}" "${descs[$((r-1))]}")"
        fi
        if [ $r -eq $cursor ]; then printf '\033[2K\033[1m ▸ [%s] %s\033[0m\n' "$mark" "$label" >&2
        else printf '\033[2K   [%s] %s\n' "$mark" "$label" >&2; fi
        r=$((r+1))
      done
    }
    echo "" >&2
    echo "  $market — select plugins   ↑/↓ move · space toggle · a all · enter install · q quit" >&2
    echo "" >&2
    r=0; while [ $r -lt $rows ]; do echo "" >&2; r=$((r+1)); done
    exec 3<"$TTY_IN"   # open once; reopening per key would rewind a non-tty input
    printf '\033[?25l' >&2; trap 'printf "\033[?25h" >&2' EXIT
    draw
    while :; do
      IFS= read -rsn1 -u 3 key || break
      if [ "$key" = $'\033' ]; then IFS= read -rsn2 -u 3 rest || true; key="$key$rest"; fi
      case "$key" in
        $'\033[A'|k) [ $cursor -gt 0 ] && cursor=$((cursor-1)) ;;
        $'\033[B'|j) [ $cursor -lt $((rows-1)) ] && cursor=$((cursor+1)) ;;
        " ")
          if [ $cursor -eq 0 ]; then
            v=1; all_on && v=0
            i=0; while [ $i -lt "$count" ]; do sel[i]=$v; i=$((i+1)); done
          else
            i=$((cursor-1)); [ "${sel[$i]}" = 1 ] && sel[i]=0 || sel[i]=1
          fi ;;
        a) v=1; all_on && v=0; i=0; while [ $i -lt "$count" ]; do sel[i]=$v; i=$((i+1)); done ;;
        q) printf '\033[?25h' >&2; echo "Cancelled." >&2; exit 130 ;;
        "") break ;;   # enter
      esac
      draw
    done
    exec 3<&-
    printf '\033[?25h' >&2
  fi
fi

chosen=(); i=0
while [ $i -lt "$count" ]; do [ "${sel[$i]}" = 1 ] && chosen+=("${names[$i]}"); i=$((i+1)); done
[ ${#chosen[@]} -gt 0 ] || { echo "Nothing selected."; exit 0; }

# ------------------------------------------------------------------ install
run() {
  if [ $dry = 1 ]; then printf '+ %s\n' "$*"; return 0; fi
  "$@"
}
if [ $dry = 0 ]; then command -v "$host" >/dev/null 2>&1 || die "$host CLI not found on PATH"; fi

echo ""
echo "Adding marketplace '$market' ($REPO_URL)"
if [ "$host" = codex ]; then
  run codex plugin marketplace add "$REPO_URL" || die "could not register the Codex marketplace"
else
  run claude plugin marketplace add "$REPO_URL" \
    || echo "  (already added or failed — continuing; run 'claude plugin marketplace update $market' if plugins look stale)"
fi

failed=0
for p in "${chosen[@]}"; do
  echo "Installing $p@$market"
  if [ "$host" = codex ]; then run codex plugin add "$p@$market" || failed=$((failed+1))
  elif [ -n "$scope" ]; then run claude plugin install "$p@$market" --scope "$scope" || failed=$((failed+1))
  else run claude plugin install "$p@$market" || failed=$((failed+1)); fi
done

echo ""
if [ $failed -gt 0 ]; then
  echo "$failed plugin(s) failed to install. Re-run with --only <name> after fixing the error above."
  exit 1
fi
if [ "$host" = codex ]; then
  echo "Done. Start a new Codex session to load: ${chosen[*]}"
  echo 'Use $plugin:skill (for example $plan-smith:forge). Review plugin hooks with /hooks before use.'
else
  echo "Done. Start a new Claude Code session (or run /reload-plugins) to load: ${chosen[*]}"
fi
