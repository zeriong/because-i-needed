# Context bridge

Goal: **every agent starts from the same project context, whichever vendor it is and
whichever vendor is main.** A worker that doesn't know the project's conventions
produces work the other vendor then rejects for the wrong reasons, and a reviewer that
doesn't know them flags things the project decided on purpose. Peer review only works
between peers who share the same ground.

The bridge is symmetric. Nothing below assumes Claude is the "source" and Codex the
"target"; a repo may start from either side, or have both.

## What each vendor reads natively

| Layer | Claude Code | Codex |
|---|---|---|
| Project instructions | `CLAUDE.md` (root + nested), `@path` imports; falls back to `AGENTS.md` in a directory with no `CLAUDE.md` | `AGENTS.override.md`, else `AGENTS.md` (root + nested), else the names in `project_doc_fallback_filenames` |
| Personal overrides | `CLAUDE.local.md` | `AGENTS.override.md` |
| Enforcement | hooks in `.claude/settings*.json` | `.codex/hooks.json` / config hooks (if configured and trusted) |
| Procedures | `.claude/skills/`, `.claude/agents/`, `.claude/rules/` | `.agents/skills/`, installed plugin skills, `.codex/agents/` |
| Tools | MCP servers (`.mcp.json`, user config) | MCP servers (`config.toml`) |

The instruction rows were checked on Claude Code 2.1.283 and Codex CLI 0.157.1 (three runs
each): where a directory has both files, Claude loads only `CLAUDE.md` and Codex only
`AGENTS.md`; a nested `CLAUDE.md` reached Codex through the fallback, and a nested `AGENTS.md`
reached Claude, like the root ones. The other Codex cells
vary by version; treat them as "check locally".

Each layer is bridged differently, because each fails differently.

## Layer 1 — Instructions: point, never copy

Copies drift. Bridge the gap the audit reports, preferring fixes that change nothing
in the repo:

- **Only `CLAUDE.md` exists — Codex can't see it.**
  1. *No repo change:* make Codex read `CLAUDE.md` as a fallback. Every standalone
     Codex call passes `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'`
     (transport-standalone.md does this). Interactive Codex sessions — Orca workers,
     or Codex as main — can't take that flag; the same key in the user's
     `~/.codex/config.toml` covers them, so propose it. The fallback applies in every
     directory with no `AGENTS.md`, nested ones included, and nowhere else. Codex reads
     the file as plain text and does not follow Claude's `@path` imports, so list the
     imported files in the context pack.
  2. *Repo change:* a pointer `AGENTS.md`, for teammates who run Codex outside this skill:
     ```markdown
     # Agent instructions
     This project's instructions live in CLAUDE.md (and nested CLAUDE.md files in
     subdirectories). Read them before starting and follow them as if written here.
     Files referenced from them with `@path` are part of the instructions.
     ```
- **Only `AGENTS.md` exists** — nothing to do on current Claude Code, which falls back
  to it. On an older version, or with its built-in `agents-md` plugin disabled, create a
  `CLAUDE.md` containing `@AGENTS.md` (Claude Code imports the file).
- **Both exist and neither points to the other** — each vendor reads a different file,
  and the fallback doesn't help (it applies only where `AGENTS.md` is missing). Don't
  merge them. Report possible drift to the user and let them choose which one is
  canonical; until then, put the other file's instructions in each worker's context
  pack. A `@AGENTS.md` line in `CLAUDE.md` makes Claude read both.

Apply the same rule to every nested directory the audit reports. A present
`AGENTS.override.md` takes precedence over `AGENTS.md` and all fallback names in
that directory. Read and bridge its actual instructions before calling a pointer
file sufficient; never overwrite a personal override during bridging.

Pointer files are repo changes that affect teammates, and the user config is theirs.
**Propose them and wait for approval**; don't create them silently. If the user
declines, include the missing side's instructions in each delegation prompt's context
pack instead (Layer 4).

## Layer 2 — Enforcement: one gate, two callers

A hook binds only the vendor that fires it. Code written by the other vendor never
passes through it, so a rule enforced only in a hook silently disappears in half the
lanes.

For each hook the audit lists, classify it:

- **Enforcement** (blocks or fails on a rule: lint, forbidden imports, file boundaries,
  design-system usage) → the check must also run in the shared gate. Best form: move
  the check into a script, have the hook call the script, and add the same script to
  the plan's gate command. Both vendors' work then meets the same rule — Claude's
  through the hook at write time, everyone's through the gate at task time.
- **Context injection** (adds reminders or state to the prompt) → cover it in the
  context pack for the other vendor's workers.
- **Convenience** (notifications, formatting on save, logging) → ignore.

Record the classification in `plan.md` under Decisions. If an enforcement hook can't
be turned into a script, say so to the user: that rule is not enforced in the other
vendor's lanes.

## Layer 3 — Worktrees: materialize what isn't committed

Worktrees contain committed files only. Local settings, personal overrides, and
knowledge-tool output are usually ignored and would be missing for every worker.

Write `.claude-x-codex/context-manifest` from the audit's section 4:

```
# personal overrides — copies, so a worker's edits can't leak back
copy CLAUDE.local.md
copy .claude/settings.local.json
# large read-only artifacts — links, to avoid copying
link <code-graph-output-dir>
```

Run `<plugin>/scripts/worktree-setup.sh <worktree>` right after creating each worktree. It
finds the main tree itself, so it also works when a worker runs it from inside its own
worktree. Ask the user before adding anything that looks like secrets (`.env`,
credentials) — workers from the other vendor would see them.

## Layer 4 — Tools and knowledge: main is the broker

Tools such as MCP servers or code-graph tools may be configured for only one vendor.
Don't try to configure every tool for every agent. Instead, **main queries its own
tools and hands the results over**:

- Before writing a delegation prompt, use whatever knowledge tools you have (code
  graph, docs search, MCP) to find the modules, patterns, and dependents the task
  touches. Put the results in the delegation's **Context pack** — file paths with one
  line on why each matters, not raw dumps.
- Point workers to procedure files by path: "read `.claude/skills/<name>/SKILL.md`
  before starting" works for either vendor, since a skill file is just markdown. The
  worker follows the procedure; it just can't auto-trigger it.
- Tell reviewers which project rules apply to the diff, with file paths, so they
  review against the project, not against generic taste.

If a tool is central to the project for both sides (e.g. every task needs the graph),
suggest registering it for the other vendor too — as a proposal to the user.

## When to run the audit

The user can run it on its own with `/peer-coding:audit`; `run` also runs it:

- on the first run in a repo, and whenever `plan.md` is created for a new feature;
- after the host changes (Claude Code ↔ Codex), since which side is "native" flips.

Save the audit output to `.claude-x-codex/context-audit.md` and summarize the gaps to the
user in the plan-approval step: which gaps you bridged, which need their approval, and
which remain (with the risk).
