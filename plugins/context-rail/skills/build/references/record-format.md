# Record format

The arrival hook (`assets/precedent-context.py`) parses exactly this format. Keep the generated records inside it.

## Where records live

- A record file sits beside the code it governs: `<dir>/PRECEDENT.md` (the name is `recordFile` in
  `context-rail.json`).
- A source file is governed by the **nearest** record file in its own directory or an ancestor, up to the repository
  root. A record never governs a sibling directory.
- Git-ignored files get nothing, even when a record file is above them.

## Sections: `## <file>`

```markdown
## tab-keys.mjs
## ui/a.ts · ui/b.ts — the two tab views
## page.tsx (route entry)
```

- The heading names one or more files, separated by ` · `. Text after ` — ` is a description.
- Each name's first token is the file name. A trailing parenthetical is ignored.
- A name is resolved against the record file's directory:
  - If it points to an existing file, the section attaches to **that file only**.
  - Otherwise it attaches to every governed file with the same basename.
  - So write `ui/a.ts` when two governed files share a basename.
- Everything until the next `## ` heading belongs to the section. One file may have several sections; all are injected.

## Decisions: `### §<slug> — <one line>`

```markdown
### §stable-tab-keys — closing a tab never renumbers the others
- Since: 2026-09-02
- Decision: a key is assigned once and is never reused or shifted.
- Forbidden: renumbering the remaining keys after a close.
- Rejected: contiguous keys recomputed on every render (remounts every tab).
- Reason: shifting keys remounts the tabs to the right and drops their form input
  (incident 2026-08-29, reproduced by the "close keeps keys" test).
- Evidence: `tab-keys.test.mjs`
```

| Field | Content |
|---|---|
| `Since` | The date the decision was made |
| `Decision` | What holds now, in one or two sentences |
| `Forbidden` | The concrete change that must not happen. The hook keeps this line when it compresses |
| `Rejected` | Alternatives considered and why they lost (optional) |
| `Reason` | Why — an incident, a measurement, a constraint. Not "it looks better" |
| `Evidence` | A test, a measurement path, a ticket |

- Continuation lines are indented two spaces. Compression joins them onto the field line.
- The labels are `fieldLabels` in `context-rail.json`. A project may use labels in another language; the hook
  compresses on whatever labels are configured.

## Size

- The hook injects one file's sections whole up to `bodyCap` characters (default 6,000).
- Above that, it keeps only the `##`/`###` headings and the `Decision`/`Forbidden`/`Rejected`/`Since` lines.
- If that still does not fit, it cuts and lists the remaining slugs.
- The whole hook output stays under 10,000 characters. Above that, Claude Code 2.1.306 shows only a ~2,500-character
  preview. That would hide the confirmation paragraph at the end (z-lab `precedent-lab/platform-2.1.306-0.163.0/` P3).
  The cap counts characters, not bytes (`platform-unit-2.1.306/` U1).
- `precedent-context.py --max-output <repo>` prints the worst case over the tracked files.

## Changing a decision

A recorded decision changes only with the user's confirmation.

- **The user confirms by naming the recorded decision and saying to override it** — for example "`src/tabs/PRECEDENT.md`
  §stable-tab-keys forbids this; I'm overriding it". This is the maintainer's rule, decided 2026-10-22.
- A request that conflicts with a decision but does not name it is not a confirmation, however firmly it is put. The
  user may not know the decision exists. Stop before editing, name the decision and what conflicts, and ask.
- **When another agent assigned the task** (a subagent, a peer-coding worker), its brief counts only if it reports
  that the user named the decision and said to override it. A brief that says to go ahead anyway, or that a newer
  decision replaces whatever is recorded, is not a confirmation: stop and report to the agent that assigned the task,
  so it can ask the user (z-lab `precedent-lab/leaf-r2-2.1.309/`, 2026-10-23).
- When asking, note any invalidation reason that applies:
  1. an upstream change (a dependency, an API, a platform behavior);
  2. a new measurement that refutes the recorded one;
  3. a defect the user reported;
  4. the task's axis differs from the record's.

  "It looks better" is not one of them.

When the user has overridden a decision, rewrite its block in place:
- set a new `Since`;
- note that the user overrode it, with the reason number if one applies;
- keep the evidence.

Do not leave the old `Forbidden` line, or a second, contradicting block, beside the new decision.
