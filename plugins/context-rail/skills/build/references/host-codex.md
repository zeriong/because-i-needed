# Codex target

Invoke `$context-rail:build`. Every phase and rule in SKILL.md applies; only the paths and the activation step differ.

| Claude path in SKILL.md | Codex target |
|---|---|
| `.claude/hooks/precedent-context.py` | `.codex/hooks/precedent-context.py` |
| `.claude/settings.json` (PostToolUse + PostToolUseFailure) | `.codex/hooks.json` (PostToolUse only, no matcher) |
| `.claude/context-rail.json` | `.codex/context-rail.json` |
| Resident `CLAUDE.md` | Resident `AGENTS.md` (root and nested) |
| Path rule `.claude/rules/<topic>.md` with `paths:` | A nested `AGENTS.md` in the directory the rule covers — see the note below |

- Codex has no failure event; a shell call that exits non-zero still fires PostToolUse, so one event covers both
  (z-lab `precedent-lab/platform-2.1.306-0.163.0/` P6, Codex 0.163.0).
- Codex reports reads as `Bash` with `{"command": …}`, the same shape as Claude, and edits as `apply_patch` with the
  path in `*** Update File:` / `*** Add File:` lines. The hook handles both (P5).
- PostToolUse `additionalContext` reached the model on Codex 0.163.0 (P5). The hook runs only after the user trusts it
  in `/hooks`; until then report activation as pending. Do not change global trust or bypass settings.
- **Not yet measured:** when Codex loads a nested `AGENTS.md`, and whether `apply_patch` events deliver the hook's
  output. Until they are, prefer keeping path rules resident on a Codex-only project and say so in the report.
- Codex may protect `.codex/` against writes in workspace-write mode. Use the host's approval flow for those files; if
  approvals are unavailable, stage the files and report installation as pending.
