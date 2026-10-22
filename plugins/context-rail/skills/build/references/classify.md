# Classifying resident items

Every item inventoried in Phase 1 gets exactly one disposition. Decide with evidence (a `file:line` in the code, the
config, or the item's own text), never from recall.

| Disposition | Test | Destination |
|---|---|---|
| **Resident** | An agent needs it before opening any file: response language, commit and PR policy, safety rules, how to run the project, where things are | Stays where it is |
| **Path rule** | It applies to a set of paths, not to one decision: "components under `src/ui/` use …", "migrations are append-only" | A path-scoped rule file (Claude: `.claude/rules/<topic>.md` with `paths:` frontmatter; Codex: see `host-codex.md`) |
| **Record** | It is a decision about specific files, with a reason: "we do not X in `a.ts` because Y" | `PRECEDENT.md` in the nearest directory that contains all the files it names (`record-format.md`) |
| **Automation** | "Every time X, do Y", "before committing, run Z" | Propose a hook or a script. Never write one silently |
| **Personal** | Only this user follows it: their language, their tools, their machine's paths, their plugins | Propose `CLAUDE.local.md` or `.claude/settings.local.json` (both git-ignored). Never move it yourself |
| **Drop** | Code or tooling already enforces it: a lint rule, a type, a CI step | Propose removal and cite the enforcer (`config:line`). Removal needs the user's confirmation like everything else |

## Rules

- **Do not invent decisions.** A record's `Decision`, `Forbidden` and `Reason` come from the item's own text or from
  the user. Leave a missing field out. If an item has no reason at all, it is not a decision: it is a path rule or
  resident.
- **Do not split one item across destinations.** If an item mixes a general rule with a file-specific decision, the
  disposition table shows it as two items (`R12a`, `R12b`), each quoting its part.
- **Path rules need real paths.** Every `paths:` glob must match at least one tracked file (`git ls-files`); report
  globs that match nothing instead of writing them.
- **Records need real files.** Every `## <file>` heading must name a governed file; `records-lint.py` must report no
  orphan headings after generation.
- **Moving is removing.** An item moved out of a resident file is deleted there in the same change; a pointer line
  in its place is not added. The arrival hook is the pointer.
- **Resident never grows.** Measure before and after with `resident-size.py`; the total must not grow in characters
  or in bytes.
- **When unsure, keep it resident** and say why in the table. A wrong move hides a rule; a kept item only costs size.
