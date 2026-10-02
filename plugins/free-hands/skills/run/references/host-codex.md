# Codex adapter

Read with `SKILL.md`; every command lives there. This file says how its steps map onto Codex.

## Entry and asking

- `$free-hands:run <goal>` enters at once. The word "free-hands" in a prompt makes the `UserPromptSubmit` hook add an
  entry note: ask the entry question as a plain question and end the turn; on "yes", read this skill's `SKILL.md`
  (the note gives its absolute path) and follow it.
- Codex's default mode has no ask tool, so "asking" means ending the turn with a question — the `Stop` hook is what
  keeps a run going. When `request_user_input` is available (plan mode, or the feature turned on), the `PreToolUse`
  hook denies it while the goal is open.
- The hard-limit hook checks each shell command when it starts. Input typed into a session that is already open
  (`write_stdin`) is not checked, so never open an interactive shell or client to run a limited action.
- The hooks run only after the user trusts them in `/hooks`. Without that, the rules in `SKILL.md` still hold but
  nothing enforces them; say so in one line (a notice, not a question) and continue.

## Session goal

Codex has a goals feature. If this session exposes a tool that sets a goal, set it with the goal's completion
condition; otherwise tell the user in one line how to pin it, and continue. The goal file stays the source of truth.

## The panel

- Each role's instructions are the body of `<plugin>/agents/<role>.md` below its Claude frontmatter. Codex ignores the
  frontmatter's `tools` and `model`, so neither read-only access nor the model comes from the file.
- Use `panel.py run` (the command in `SKILL.md`): one `codex exec -s read-only` child per role, `FREE_HANDS_ROLE` and
  `CXC_MODE=off` set so neither free-hands nor peer-coding acts inside it. Native subagents are not used: they take a
  model and an effort but no read-only control.
- Children can search the web whatever the role; `--search` is added for `evidence-hunter` and `trend-tracker`.
- The children need network. From a sandboxed main they fail ("Transport channel closed"), so run that one command
  outside the sandbox through the host's escalation route. If that is not available, the tally says `decide-alone`:
  decide yourself and record "panel degraded" with the reason.
- The model that ran is `ran` in `<round>/<role>.meta.json`, read from the child's run header — not from the reply.
- `panel.py models` exits a role with `error` when the newest model cannot be determined (`exit` 2) or the effort is
  not supported (3). That role is missing for the round. When the message says `catalog not refreshed` and your
  shell is sandboxed without network, rerun that one resolver command outside the sandbox first.
