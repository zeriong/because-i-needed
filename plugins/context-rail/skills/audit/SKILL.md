---
name: audit
description: "Read-only check of a project's context rail: resident instruction size, the arrival hook's wiring and self-test, the worst-case injection size, and the PRECEDENT.md records' format. Changes nothing; proposes fixes. Trigger keywords — \"context rail 점검\" (check the context rail), \"audit context rail\", \"context-rail:audit\"."
---

# context-rail:audit

Read-only. Never edits a file, never installs, never moves an item; if a fix is needed, name it and point to
`/context-rail:build` (Codex: `$context-rail:build`). `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` on Claude Code, or the
directory two levels above this skill's directory on Codex. `<build>` is `<plugin>/skills/build`.

Run each check and report its output; a check that cannot run is reported as not run, with the reason.

```bash
python3 "<build>/scripts/resident-size.py" --project "<project>"
python3 "<build>/scripts/install-hooks.py" --project "<project>" --host <claude|codex|both> --check
python3 "<project>/.claude/hooks/precedent-context.py" --self-test
python3 "<project>/.claude/hooks/precedent-context.py" --max-output "<project>"
python3 "<build>/scripts/records-lint.py" --project "<project>"
```

On Codex use `.codex/hooks/precedent-context.py`. Also compare the installed hook with the plugin's asset
(`<build>/assets/precedent-context.py`); a difference means the project runs a modified or older hook.

Report:

```
## context-rail:audit
- Resident: <files with lines / chars / bytes>
- Hook: wired <yes/no per host> · self-test <pass/fail> · same as plugin asset <yes/no> · worst case <n> chars (< 10,000)
- Records: <n> files · orphan headings <list> · blocks without a decision line <list> · governed files without a section <n>
- Proposed fixes: <each with the file:line it rests on>
```
