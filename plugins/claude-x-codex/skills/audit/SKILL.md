---
name: audit
description: "Read-only check of whether Claude and Codex would start from the same project context in this repo — instruction files (CLAUDE.md / AGENTS.md), hooks that bind only one vendor, uncommitted context missing from worktrees, and tools configured for one side only. Use when the user asks to audit or check claude-x-codex readiness, cross-vendor context, or \"why does Codex not follow our rules\", or runs /claude-x-codex:audit. Changes nothing; proposes fixes."
argument-hint: "[path to repo — defaults to the current one]"
---

# claude-x-codex: audit

Claude Code invokes `/claude-x-codex:audit`; Codex invokes
`$claude-x-codex:audit`. `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` when
expanded by Claude Code, or the absolute path two directories above this skill's
directory on Codex. Resolve it from the loaded SKILL.md path, not the working directory.

Peer review between Claude and Codex only works if both start from the same ground.
This skill checks that ground and proposes how to close the gaps. It never changes
project configuration or tracked source files. Its only writes are the audit report
under `.claude-x-codex/` and that directory's local git exclusion; every proposed fix
requires the user's approval.

The policy behind each layer lives in `../run/references/context-bridge.md`. Read it
before interpreting results.

## What to do

1. Run the audit in the target repo and save the output:

   ```bash
   cd <repo>   # the user's argument, or stay in the current repo
   mkdir -p .claude-x-codex
   bash "<plugin>/scripts/context-audit.sh" | tee .claude-x-codex/context-audit.md
   ```

   Outside Claude Code plugins, the script is at `../../scripts/context-audit.sh`
   relative to this skill's directory. If `.claude-x-codex/` is new, add it to
   the path returned by `git rev-parse --git-path info/exclude` (the `mode`
   script does this too). Resolve a relative result from the target repo. Never
   assume `.git` is a directory: linked worktrees use a file. Together with the report,
   these are the only writes allowed, and neither touches a tracked file.

2. Interpret the result layer by layer, using `context-bridge.md`:

   - **Instructions** — for each GAP directory, give the fix in the order
     `context-bridge.md` Layer 1 lists: the Codex fallback that needs no repo change
     (and whether `project_doc_fallback_filenames` in the user's Codex config already
     covers it — the audit then marks the directory `ok (Codex fallback in user config)`),
     then the pointer file you would create (content included). For
     "Claude reads only CLAUDE.md, Codex only AGENTS.md", say which one looks canonical
     and why, and ask.
   - **Hooks** — classify every hook as enforcement / context injection / convenience.
     For each enforcement hook, name the check and propose how to run the same check
     from a gate command, so the other vendor's work meets the same rule. State
     plainly which rules are currently **not enforced** for the other vendor.
   - **Worktrees** — draft `.claude-x-codex/context-manifest` entries (`copy` for
     personal settings, `link` for large read-only artifacts such as code-graph
     output). List anything that looks like secrets separately and don't include it.
   - **Tools** — MCP servers or knowledge tools configured for one vendor only. Propose
     either brokering (main queries and passes results in context packs) or
     registering the tool for the other vendor.
   - **Codex profiles** — if the audit warns about legacy `[profiles.*]` tables, say
     that `--profile` fails until each is moved to its own `<name>.config.toml`.

3. End with a short readiness verdict:

   - **Ready** — no gaps that affect correctness.
   - **Ready with gaps** — list the gaps that `run` will cover with the Codex fallback,
     context packs, or the manifest, and what the user should approve.
   - **Not ready** — rules that would silently not apply to one vendor's work, with the
     smallest fix for each.

Ask which proposals to apply. Apply nothing in this skill; approved fixes are made
by the user or by `claude-x-codex:run` at its plan-approval step.
