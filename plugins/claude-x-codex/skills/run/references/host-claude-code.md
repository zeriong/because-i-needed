# Host: Claude Code

You are Claude. Your vendor is Anthropic.

## Main
Run as the newest Opus (the `opus` alias). Use high effort or more for planning and triage; ordinary effort is fine
for task gates. Reviewing `codex-bulk` work yourself needs `CXC_REVIEW_EFFORT` (`xhigh`)
or `max`; below that, start the Claude reviewer form instead.

## Reaching each lane

| Lane | Standalone transport | Orca transport |
|---|---|---|
| `claude-fast` | `claude -p` worker form in the task's worktree (transport-standalone.md) | Orca worker, agent `claude`, `--model <resolved CXC_CLAUDE_WORKER> --effort ${CXC_WORKER_EFFORT:-high}` |
| `codex-bulk` | `codex exec` worker form (transport-standalone.md) | Orca worker, agent `codex`, `--model <resolved CXC_WORKER_MODEL> --effort ${CXC_WORKER_EFFORT:-high}` |
| `main` | yourself | yourself |

A native subagent can't pin its effort — subagent definitions and the Agent tool take a
model but no effort, so it runs at your session's — which is why `claude-fast` uses the
CLI form. Check the other vendor with `command -v codex`. If missing → single-vendor mode.

## Review routing, resolved for this host

Resolve `CXC_REVIEW_MODEL`, `CXC_CLAUDE_REVIEWER` and `CXC_REVIEW_EFFORT` from the
environment, then resolve each model to its family's newest with `latest-model.py` (SKILL.md,
"Newest model per family") before routing. Compare actual model IDs, not aliases.
Parenthesized defaults are families and never override configured values.

| Author | Reviewer |
|---|---|
| `claude-fast` | Codex newest `CXC_REVIEW_MODEL` (default `sol`) at `CXC_REVIEW_EFFORT` (default `xhigh`), read-only |
| `main` (you) | Codex newest `CXC_REVIEW_MODEL` (default `sol`) at `CXC_REVIEW_EFFORT` (default `xhigh`), read-only |
| `codex-bulk` | **you**, only when your actual model is the newest of `CXC_CLAUDE_REVIEWER` (default `opus`) and effort meets `CXC_REVIEW_EFFORT` (default `xhigh`); otherwise use the configured Claude reviewer form |
| High-risk final, only if the user approved it | Codex newest `CXC_FINAL_MODEL` (default `astra`), read-only |

Single-vendor mode: the reviewer is a fresh newest `CXC_CLAUDE_REVIEWER` (default `opus`)
instance through the Claude reviewer form at `CXC_REVIEW_EFFORT` (default `xhigh`),
given only `plan.md`, `decisions.md`, and the diff.

## Native context
You read `CLAUDE.md`, `.claude/` skills, rules, hooks and MCP natively (and `AGENTS.md`
in directories with no `CLAUDE.md`). Codex workers and reviewers read none of the
`CLAUDE.md` side unless it is bridged — follow `context-bridge.md`, and remember that
your hooks never fire on Codex-written code.

## Host notes
- CLI workers return only their final message. Tell them to use the return format
  exactly; you don't see their intermediate reasoning.
- This plugin's `UserPromptSubmit` hook also fires in `claude -p` sessions. Start every
  CLI worker and reviewer with `CXC_MODE=off` so they don't receive the mode note.
- Pair with hooks (`PreToolUse`/`Stop`) for hard gates such as the cycle cap.
