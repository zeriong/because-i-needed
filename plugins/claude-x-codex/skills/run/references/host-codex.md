# Host: Codex

You are a Codex model. Your vendor is OpenAI.

Invoke `$claude-x-codex:run` on Codex. The three sibling skills and shared scripts
ship together; resolve `<plugin>` from the loaded skill path as defined in SKILL.md.
The mode hook uses the shared `hooks/hooks.json`; review/trust it with `/hooks` for
automatic routing. Explicit `run` works independently of the prompt hook.

## Main
Run as the newest `sol` model (resolve it at Setup; if your session runs an older version, or
you can't see your own model id — a probe could not — tell the user once) at high effort or more. Don't move to the `astra` family or `max` effort on
your own for a large or high-risk feature — ask the user first. Reviewing `claude-fast` work yourself needs `CXC_REVIEW_EFFORT` (`xhigh`) or
above; below that, start the Codex reviewer form instead.

## Reaching each lane

| Lane | Standalone transport | Orca transport |
|---|---|---|
| `claude-fast` | `claude -p` worker form (transport-standalone.md) | Orca worker, agent `claude`, `--model <resolved CXC_CLAUDE_WORKER> --effort ${CXC_WORKER_EFFORT:-high}` |
| `codex-bulk` | `codex exec` worker form, which sets the effort explicitly (transport-standalone.md) | Orca worker, agent `codex`, `--model <resolved CXC_WORKER_MODEL> --effort ${CXC_WORKER_EFFORT:-high}` |
| `main` | yourself | yourself |

Check the other vendor with `command -v claude`. If missing → single-vendor mode.

## Review routing, resolved for this host

Note how this differs from the Claude Code host: here *you* are the natural reviewer
for Claude-authored work, and Luna work needs a Claude reviewer.
Resolve `CXC_REVIEW_MODEL`, `CXC_CLAUDE_REVIEWER` and `CXC_REVIEW_EFFORT` from the
environment, then resolve each model to its family's newest with `latest-model.py` (SKILL.md,
"Newest model per family") before routing. Compare actual model IDs, not aliases.
Parenthesized defaults are families and never override configured values.

| Author | Reviewer |
|---|---|
| `claude-fast` | **you**, only when your actual model is the newest of `CXC_REVIEW_MODEL` (default `sol`) and effort meets `CXC_REVIEW_EFFORT` (default `xhigh`); otherwise use the configured Codex reviewer form |
| `main` (you) | Claude newest `CXC_CLAUDE_REVIEWER` (default `opus`) at `CXC_REVIEW_EFFORT` (default `xhigh`), read-only |
| `codex-bulk` | Claude newest `CXC_CLAUDE_REVIEWER` (default `opus`) at `CXC_REVIEW_EFFORT` (default `xhigh`), read-only |
| High-risk final, only if the user approved it | Claude newest Opus at `max`, read-only |

Single-vendor mode: reviewer is a fresh newest `CXC_REVIEW_MODEL` (`sol`) instance at `CXC_REVIEW_EFFORT` (`xhigh`),
read-only, given only `plan.md`, `decisions.md`, and the diff.

## Native context
You read `AGENTS.override.md` / `AGENTS.md` and Codex config natively, and `CLAUDE.md`
only if it is listed in `project_doc_fallback_filenames`. Claude workers and reviewers
read `CLAUDE.md` and `.claude/` instead — bridge them per `context-bridge.md`. If the
repo is Claude-first (rich `.claude/`, thin or no `AGENTS.md`), you are the one missing
context: read `CLAUDE.md` and the relevant `.claude/` files yourself before planning.

## Host notes
- Because Luna and you share a vendor, don't let "Main reviews worker output" become
  the default here — it would be same-vendor review. Your own task gate (tests, scope
  check) still applies to Luna work; only the phase review goes to Claude.
- Claude runs through its CLI's print mode; it has no memory of this session. The
  delegation prompt must be fully self-contained.
- The plugin's prompt hook runs in `claude -p` sessions too; start Claude workers and
  reviewers with `CXC_MODE=off`.
