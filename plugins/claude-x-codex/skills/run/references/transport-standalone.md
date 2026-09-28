# Transport: standalone (no Orca)

Communication is one-way: you send a delegation prompt, the worker returns once.
Workers can't ask questions mid-task, so the delegation prompt must anticipate them and
the return's "Uncertain" section carries what's left. Blocking for the user (Gates 1
and 4, escalations) means stopping and asking in the conversation.

These forms were checked on Codex CLI 0.157.1 and Claude Code 2.1.283. CLI flags differ
between versions; check `codex exec --help` / `claude --help` once per session and adapt.

Rules that hold for every call below:

- **`CXC_MODE=off`** in front, so a worker or reviewer never receives the mode note and
  starts orchestrating itself.
- **`< /dev/null`** at the end. `codex exec` appends piped stdin to its prompt and waits for
  EOF — a pipe held open for 15 s delayed a call by that long — and an agent's shell may
  leave stdin open.
- Codex gets `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'`, so it reads `CLAUDE.md`
  in directories without `AGENTS.md` (context-bridge.md, Layer 1).

## Worktrees

```bash
git worktree add .claude-x-codex/wt/<id> -b cxc/<feature>/<id>
<plugin>/scripts/worktree-setup.sh .claude-x-codex/wt/<id>   # materialize uncommitted context
# cleanup at finish
git worktree remove .claude-x-codex/wt/<id>
```

## Codex worker (`codex-bulk`)

```bash
F="$PWD/.claude-x-codex/<feature>"   # absolute, so the paths don't depend on where you cd
CXC_MODE=off codex exec -m "${CXC_WORKER_MODEL:-gpt-6-luna}" -c model_reasoning_effort="${CXC_WORKER_EFFORT:-high}" \
  -C .claude-x-codex/wt/<id> -s workspace-write \
  -c 'project_doc_fallback_filenames=["CLAUDE.md"]' \
  -o "$F/returns/<id>.md" \
  "$(cat "$F/tasks/<id>.md")" < /dev/null
```

`-o` writes the agent's last message to the file; stdout carries the progress log. A relative
`-o` resolves against the caller's directory, not the `-C` directory.

## Codex reviewer

```bash
F="$PWD/.claude-x-codex/<feature>"; P=<plugin>/skills/run/references
CXC_MODE=off codex exec -m "${CXC_REVIEW_MODEL:-gpt-6-sol}" -c model_reasoning_effort="${CXC_REVIEW_EFFORT:-xhigh}" \
  -s read-only -c 'project_doc_fallback_filenames=["CLAUDE.md"]' \
  --output-schema "$P/review.schema.json" \
  -o "$F/reviews/<phase>-r<n>.json" \
  "$(cat "$F/reviews/<phase>-prompt.md")" < /dev/null
```

`--output-schema` makes the final message conform to the review schema, and `-s read-only`
keeps the reviewer from writing: told to create a file, it could not (the shell write failed).
Delta re-reviews use the same model and effort. A high-risk final review uses
`CXC_FINAL_MODEL`, and only after the user approved it.
The run header prints `reasoning effort:` — Codex doesn't check the value locally, so a
misspelled level reaches the run unchanged.

Codex profiles are separate files, `$CODEX_HOME/<name>.config.toml` (default
`~/.codex/cxc-review.config.toml`), selected with `--profile cxc-review`. A legacy
`[profiles.<name>]` table inside `config.toml` makes `--profile` fail on current CLIs;
the audit warns about it.

## Claude worker (`claude-fast`)

```bash
cd .claude-x-codex/wt/<id> && CXC_MODE=off claude -p "$(cat ../../<feature>/tasks/<id>.md)" \
  --model "${CXC_CLAUDE_WORKER:-sonnet}" --effort "${CXC_WORKER_EFFORT:-high}" --permission-mode acceptEdits \
  > ../../<feature>/returns/<id>.md < /dev/null
```

Grant only the permissions the task needs: `--permission-mode` (`acceptEdits` lets it
edit files) plus `--allowedTools` for the commands its "done when" runs. Read-only shell
commands such as `ls` run without being listed. Put the prompt right after `-p`:
`--allowedTools` takes several values and would swallow a prompt placed after it. Use this
form from either host: a native subagent can't pin its effort.

## Claude reviewer

```bash
CXC_MODE=off claude -p "$(cat .claude-x-codex/<feature>/reviews/<phase>-prompt.md)" \
  --model "${CXC_CLAUDE_REVIEWER:-opus}" --effort "${CXC_REVIEW_EFFORT:-xhigh}" \
  --allowedTools "Read" "Grep" "Glob" "Bash(git diff:*)" "Bash(git log:*)" \
  --disallowedTools "Skill" "ReportFindings" "Write" "Edit" "NotebookEdit" \
  --json-schema "$(cat <plugin>/skills/run/references/review.schema.json)" \
  --output-format json < /dev/null \
  | jq '.structured_output' > .claude-x-codex/<feature>/reviews/<phase>-r<n>.json
```

With `--json-schema`, the conforming object is the `structured_output` field of the
JSON result. `--allowedTools` grants only reading and `git diff`/`git log`; Claude Code also
runs read-only commands such as `ls` or `git status` unlisted, and denies writes — told to
create a file, this reviewer could not, even under a user `defaultMode` of `auto`. Tools that
need no permission stay available unless removed, and a reviewer was seen starting a forked
review through `Skill`; `--disallowedTools` removes those. Prefer this deny list to narrowing
with `--tools`: in the same review, a `--tools` whitelist grew the last turn's context about
sixfold and cost about 1.5× (haiku). Don't widen the allow list. An unknown `--effort` value
only prints a warning on stderr and runs at the default effort, so check stderr once.

## Parallelism

Launch ready tasks in the background (`&`) up to `CXC_PARALLEL`, then `wait`. Check
each return file exists and follows the return format before running its task gate.
