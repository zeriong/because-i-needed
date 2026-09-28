#!/usr/bin/env bash
# Materialize uncommitted context into a worker's worktree.
#
# A git worktree contains only committed files. Local agent settings, personal
# instruction overrides and knowledge-tool output (e.g. a code graph) are usually
# ignored, so workers would silently run without them. This copies or links the
# paths listed in the manifest from the main tree into the worktree.
#
# Manifest (.claude-x-codex/context-manifest), one entry per line:
#   copy <path>    # default; the worker gets its own copy
#   link <path>    # symlink to the main tree; for large read-only artifacts
#   <path>         # same as copy
#   # comment
#
# Usage: worktree-setup.sh <worktree-path> [manifest]
# Works from the main tree or from inside the worktree itself.
set -euo pipefail

WT="${1:?usage: worktree-setup.sh <worktree-path> [manifest]}"
# The main tree, even when run from inside a linked worktree (where --show-toplevel
# would return the worktree): the common git dir always belongs to the main tree.
ROOT="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)"
MAN="${2:-$ROOT/.claude-x-codex/context-manifest}"

[ -d "$WT" ] || { echo "worktree not found: $WT" >&2; exit 2; }
[ -f "$MAN" ] || { echo "no manifest at $MAN — nothing to materialize"; exit 0; }

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in ''|\#*) continue ;; esac
  case "$line" in
    "copy "*) mode="copy"; path="${line#copy }" ;;
    "link "*) mode="link"; path="${line#link }" ;;
    *)        mode="copy"; path="$line" ;;
  esac
  path="${path%/}"
  src="$ROOT/$path"; dst="$WT/$path"
  if [ ! -e "$src" ]; then echo "skip (not in main tree): $path"; continue; fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then echo "skip (already in worktree): $path"; continue; fi
  mkdir -p "$(dirname "$dst")"
  if [ "$mode" = link ]; then ln -s "$src" "$dst"; else cp -R "$src" "$dst"; fi
  echo "$mode: $path"
done < "$MAN"
