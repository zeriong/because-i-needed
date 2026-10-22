---
name: build
description: "Sets up a context rail in the current project: moves file-specific decisions out of always-loaded instruction files (CLAUDE.md, AGENTS.md) into PRECEDENT.md records beside the code, moves path-specific rules into path-scoped rule files, and installs an arrival hook that injects a file's recorded decisions, with a confirm-before-changing paragraph, the moment an agent reads or edits it. Resident instructions only shrink. Trigger keywords — \"context rail 깔아줘\", \"규칙 정규화\" (normalize the rules), \"set up context rail\", \"normalize project rules\", \"context-rail:build\"."
---

# context-rail:build

## Host setup

Claude Code uses `/context-rail:build`; Codex uses `$context-rail:build` and reads
[references/host-codex.md](references/host-codex.md) first. Set `host=claude|codex|both` from the request; default to
the current host. `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` on Claude Code, or the directory two levels above this skill's
directory on Codex — resolve it from the loaded SKILL.md path, never from the project's working directory. `<skill>` is
`<plugin>/skills/build`. Python 3.9+ and git are required.

## What this produces

1. `.claude/hooks/precedent-context.py` and its wiring in `.claude/settings.json` (PostToolUse
   `Read|Edit|Write|MultiEdit|Bash`, PostToolUseFailure `Bash`) — Codex: `.codex/hooks/…` and `.codex/hooks.json`.
2. `.claude/context-rail.json` — the source extensions the hook governs.
3. `PRECEDENT.md` records beside the code, in [references/record-format.md](references/record-format.md).
4. Path-scoped rule files for rules that apply to a set of paths.
5. Smaller resident files: each moved item is removed from where it was.

Everything is a project file, shared with everyone who clones the repository. Nothing is installed per user.

## Absolute rules

1. **Every claim cites a `file:line`** read in this run. No item is classified from memory.
2. **No invented decisions.** Records hold what the resident item or the user said; a missing field stays missing.
3. **One confirmation before writing.** The disposition table goes to the user once (Phase 3); nothing is moved,
   removed or created before the answer. Personal items are only proposed, never moved.
4. **Resident context never grows** — measured in characters and in bytes (`resident-size.py`).
5. **Done means verified** (Phase 5). A step that fails is reported as failed with its output; nothing is claimed
   without it.

## Phase 0 — Intake

- Confirm the project is a git repository and note uncommitted changes; do not stash or discard them.
- List the resident files: tracked `CLAUDE.md` and `AGENTS.md` at any depth, `.claude/CLAUDE.md`, and
  `CLAUDE.local.md` if present.
- List existing rule files (`.claude/rules/*.md`), existing `PRECEDENT.md` files, and existing hook settings.
- Record the baseline:
  `python3 "<skill>/scripts/resident-size.py" --project "<project>" > "<scratch>/resident-before.json"`
  (`<scratch>` is outside the project, e.g. the session's scratch directory).

## Phase 1 — Inventory

Read every resident file whole. Split it into items — one rule, fact or decision each — and number them (`R1`, `R2`,
…) with `file:line`. Items in code blocks or tables count. Keep the item's exact wording.

## Phase 2 — Classify

Apply [references/classify.md](references/classify.md) to every item. For each, open the code or config it talks about
and cite what you read. Record the target: the record file and `## <file>` heading, or the rule file and its `paths:`
globs, or "stays".

## Phase 3 — Confirm

Show one table — `id · source file:line · quoted item (shortened) · disposition · destination · evidence` — plus the
baseline sizes. Ask once with the host's question tool: apply as shown / apply with changes (the user names them) /
stop. Apply exactly what the answer allows.

## Phase 4 — Generate

1. Write or extend the `PRECEDENT.md` records and the path-scoped rule files.
2. Remove each moved item from its resident file. Do not add pointer lines.
3. Choose the governed extensions from the tracked files (`git ls-files`, the source extensions that hold the governed
   code) and install the hook:

```bash
python3 "<skill>/scripts/install-hooks.py" --project "<project>" --host <claude|codex|both> --extensions <e1,e2,…> --dry-run
python3 "<skill>/scripts/install-hooks.py" --project "<project>" --host <claude|codex|both> --extensions <e1,e2,…>
```

A differing existing hook stops the install; show the difference to the user before `--replace-hook`.

## Phase 5 — Verify

Run all of these; each must pass:

```bash
python3 "<project>/.claude/hooks/precedent-context.py" --self-test
python3 "<project>/.claude/hooks/precedent-context.py" --max-output "<project>"
python3 "<skill>/scripts/records-lint.py" --project "<project>"
python3 "<skill>/scripts/resident-size.py" --project "<project>" --compare "<scratch>/resident-before.json"
python3 "<skill>/scripts/install-hooks.py" --project "<project>" --host <host> --check
```

Then check fidelity by hand: every item id from Phase 1 has exactly one disposition, and every moved item's wording
is present at its destination. On Codex, the hook runs only after the user trusts it in `/hooks`; report that step as
pending until it is done.

## Phase 6 — Report

```
## context-rail:build complete
- Resident: <chars before> → <after> chars, <bytes before> → <after> bytes
- Items: <n> total — <k> stayed · <m> records · <p> path rules · <q> proposed (automation / personal / drop)
- Records: <files>; path rules: <files>; hook: <host paths>
- Checks: self-test · max-output <n> chars · records-lint · resident-size · install --check
- Not established by this run: whether agents now follow the records better (measured only in the maintainer's
  experiments; see the plugin README)
```
