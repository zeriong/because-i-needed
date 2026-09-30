#!/usr/bin/env bash
# ui-commit-gate.sh — hard gate: block `git commit` of UI changes that the
# ux-ui-art-director has not APPROVED against the exact staged diff.
#
# Modes:
#   (no args)                     PreToolUse hook mode. Reads the tool call JSON on
#                                 stdin; blocks (exit 2) a UI git-commit lacking a
#                                 matching APPROVED artifact. Allows everything else.
#   hash                          Print the current staged-UI diff hash (or empty).
#   approve <feature> [measDir]   Write the APPROVED artifact for the current staged
#                                 UI diff. Call ONLY after the director returns APPROVED.
#
# The approval is bound to a sha256 of the staged UI diff, so any further edit to the
# UI invalidates it and the gate blocks again. No time-based staleness needed.
set -euo pipefail

APPROVAL_DIR=".ux-ui/approvals"

# UI file extensions/paths that trigger the gate. Deliberately conservative (no bare
# .ts/.js/.java, no bare .xml) so backend-only commits are never blocked. Covers web and
# mobile UI: iOS (.swift/.storyboard/.xib), Android (Kotlin + res/layout XML), Flutter
# (.dart). Override with UX_UI_GLOBS.
DEFAULT_GLOBS='*.tsx *.jsx *.vue *.svelte *.astro *.css *.scss *.sass *.less *.html *.swift *.kt *.dart *.storyboard *.xib res/layout*/**/*.xml'

hash_cmd() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256
  elif command -v sha256sum >/dev/null 2>&1; then sha256sum
  else return 1; fi
}

# List staged UI files (added/copied/modified/renamed), excluding our own artifacts.
ui_files() (
  # Expand the configured list into words, never against files in the shell cwd.
  set -f
  local globs="${UX_UI_GLOBS:-$DEFAULT_GLOBS}"
  local pathspecs=() g
  for g in $globs; do pathspecs+=( ":(glob)**/$g" ); done
  git diff --cached --name-only -z --diff-filter=ACMR -- \
    "${pathspecs[@]}" ':(exclude,glob).ux-ui/**' 2>/dev/null || true
)

# sha256 of the staged diff content of those UI files. Empty if none staged.
staged_ui_hash() {
  local file files=()
  while IFS= read -r -d '' file; do files+=("$file"); done < <(ui_files)
  [ ${#files[@]} -eq 0 ] && { printf ''; return 0; }
  git --literal-pathspecs diff --cached -- "${files[@]}" 2>/dev/null \
    | hash_cmd | awk '{print $1}'
}

# Extract a JSON string field from stdin content using whatever parser exists.
json_field() { # $1 = full json, $2 = jq-style path, $3 = python/node dotted path
  local json="$1" jqpath="$2" pypath="$3"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r "$jqpath // empty" 2>/dev/null || true
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$json" | python3 -c "import sys,json
try:
  d=json.load(sys.stdin)
  for k in '$pypath'.split('.'):
    d=d.get(k,{}) if isinstance(d,dict) else {}
  print(d if isinstance(d,str) else '')
except Exception:
  print('')" 2>/dev/null || true
  elif command -v node >/dev/null 2>&1; then
    printf '%s' "$json" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{let o=JSON.parse(s);for(const k of '$pypath'.split('.'))o=(o&&o[k])||'';console.log(typeof o==='string'?o:'')}catch(e){console.log('')}})" 2>/dev/null || true
  else
    printf ''
  fi
}

mode="${1:-hook}"

case "$mode" in
  hash)
    cd "$(git rev-parse --show-toplevel)"
    staged_ui_hash
    ;;

  approve)
    cd "$(git rev-parse --show-toplevel)"
    feature="${2:-unknown}"
    measdir="${3:-}"
    h="$(staged_ui_hash)"
    if [ -z "$h" ]; then
      echo "ux-ui-gate: no staged UI files to approve." >&2
      exit 1
    fi
    mkdir -p "$APPROVAL_DIR"
    python3 -c 'import json, sys, time
print(json.dumps({"verdict": "APPROVED", "feature": sys.argv[1],
                  "diffHash": sys.argv[2], "measureDir": sys.argv[3],
                  "approvedAtEpoch": int(time.time())}, ensure_ascii=False))' \
      "$feature" "$h" "$measdir" > "$APPROVAL_DIR/$h.json"
    echo "ux-ui-gate: wrote $APPROVAL_DIR/$h.json"
    ;;

  hook)
    # Read the PreToolUse payload. Fail OPEN on any parse trouble — this gate must
    # never wedge the user's shell; when unsure whether it's even a commit, allow.
    input="$(cat 2>/dev/null || true)"
    [ -z "$input" ] && exit 0

    # cd into the project so git sees the right repo.
    proj="$(json_field "$input" '.cwd' 'cwd')"
    [ -z "$proj" ] && proj="${CLAUDE_PROJECT_DIR:-}"
    [ -n "$proj" ] && [ -d "$proj" ] && cd "$proj"

    cmd="$(json_field "$input" '.tool_input.command' 'tool_input.command')"
    [ -z "$cmd" ] && exit 0

    # Only care about git commits. (matches `git commit`, `git -C x commit`, amend)
    printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]])git([[:space:]]+-[^[:space:]]+|[[:space:]]+[^[:space:]]+)*[[:space:]]+commit([[:space:]]|$)' || exit 0

    command -v python3 >/dev/null 2>&1 || {
      echo 'ux-ui gate: python3 is required to resolve commit targets; gate inactive.' >&2
      exit 0
    }
    resolver="$(cd "$(dirname "$0")" && pwd)/commit-roots.py"
    blocked=0
    while IFS= read -r -d '' root; do
      cd "$root" || continue
      h="$(staged_ui_hash)"
      [ -z "$h" ] && continue
      if [ ! -f "$APPROVAL_DIR/$h.json" ] \
         || ! grep -q '"verdict"[[:space:]]*:[[:space:]]*"APPROVED"' "$APPROVAL_DIR/$h.json"; then
        blocked=1
        break
      fi
    done < <(printf '%s' "$cmd" | python3 "$resolver" "$PWD")
    [ "$blocked" = 0 ] && exit 0

    # Blocked. stderr is fed back to the agent as the reason.
    cat >&2 <<'MSG'
⛔ ux-ui gate: this commit changes UI, but no ux-ui-art-director APPROVAL
matches the exact staged diff.

Run the UI build/review loop before committing:
  → invoke ux-ui:build (web) or ux-ui:build-mobile (mobile).
Use /plugin:skill in Claude Code or $plugin:skill in Codex.
The skill will measure the real render, have the art director critique
the measured snapshots, apply fixes until APPROVED, then record the approval.
The approval is bound to the diff hash, so re-edit → re-review is required.

(If this file genuinely is not UI, override the extension set with UX_UI_GLOBS.)
MSG
    exit 2
    ;;

  *)
    echo "ux-ui-gate: unknown mode '$mode' (use: hash | approve | <hook stdin>)" >&2
    exit 1
    ;;
esac
