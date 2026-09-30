# Transport: standalone (no Orca)

Communication is one-way: you send a delegation prompt, the worker returns once.
Workers can't ask questions mid-task, so the delegation prompt must anticipate them and
the return's "Uncertain" section carries what's left. Blocking for the user (Gates 1
and 4, escalations) means stopping and asking in the conversation.

These forms were checked on Codex CLI 0.157.1 and Claude Code 2.1.283, and ids resolved by
`latest-model.py` ran on Codex CLI 0.159.0 and Claude Code 2.1.284. CLI flags differ
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
"<plugin>/scripts/worktree-setup.sh" .claude-x-codex/wt/<id>   # materialize uncommitted context
# cleanup at finish
git worktree remove .claude-x-codex/wt/<id>
```

## Codex worker (`codex-bulk`)

```bash
F="$PWD/.claude-x-codex/<feature>"   # absolute, so the paths don't depend on where you cd
M=$(python3 "<plugin>/scripts/latest-model.py" codex "${CXC_WORKER_MODEL:-luna}" --effort "${CXC_WORKER_EFFORT:-high}") || exit
CXC_MODE=off codex exec -m "$M" -c model_reasoning_effort="${CXC_WORKER_EFFORT:-high}" \
  -C .claude-x-codex/wt/<id> -s workspace-write \
  -c 'project_doc_fallback_filenames=["CLAUDE.md"]' \
  -o "$F/returns/<id>.md" \
  "$(cat "$F/tasks/<id>.md")" < /dev/null > "$F/returns/<id>.log" 2>&1
```

A resolver failure stops here (SKILL.md, "Newest model per family"). `-o` writes the agent's
last message to the file; the log carries the progress and the run header, whose `model:` line
is the id to log. A relative `-o` resolves against the caller's directory, not the `-C` directory.

## Codex reviewer

```bash
F="$PWD/.claude-x-codex/<feature>"; P="<plugin>/skills/run/references"
M=$(python3 "<plugin>/scripts/latest-model.py" codex "${CXC_REVIEW_MODEL:-sol}" --effort "${CXC_REVIEW_EFFORT:-xhigh}") || exit
CXC_MODE=off codex exec -m "$M" -c model_reasoning_effort="${CXC_REVIEW_EFFORT:-xhigh}" \
  -s read-only -c 'project_doc_fallback_filenames=["CLAUDE.md"]' \
  --output-schema "$P/review.schema.json" \
  -o "$F/reviews/<phase>-r<n>.json" \
  "$(cat "$F/reviews/<phase>-prompt.md")" < /dev/null > "$F/reviews/<phase>-r<n>.log" 2>&1
```

`--output-schema` makes the final message conform to the review schema, and `-s read-only`
keeps the reviewer from writing: told to create a file, it could not (the shell write failed).
Delta re-reviews use the same family and effort, resolved again. A high-risk final review
resolves `CXC_FINAL_MODEL` (default `astra`), and runs only after the user approved it.
The run header prints `reasoning effort:` — Codex doesn't check the value locally, so a
misspelled level reaches the run unchanged.

Codex profiles are separate files, `$CODEX_HOME/<name>.config.toml` (default
`~/.codex/cxc-review.config.toml`), selected with `--profile cxc-review`. A legacy
`[profiles.<name>]` table inside `config.toml` makes `--profile` fail on current CLIs;
the audit warns about it.

## Claude worker (`claude-fast`)

```bash
cd .claude-x-codex/wt/<id> || exit; R=../../<feature>/returns
M=$(python3 "<plugin>/scripts/latest-model.py" claude "${CXC_CLAUDE_WORKER:-sonnet}" --effort "${CXC_WORKER_EFFORT:-high}" --project "$PWD") || exit
CXC_MODE=off claude -p "$(cat ../../<feature>/tasks/<id>.md)" \
  --model "$M" --effort "${CXC_WORKER_EFFORT:-high}" --permission-mode acceptEdits \
  --output-format json > "$R/<id>.raw.json" < /dev/null
jq -r '.result' "$R/<id>.raw.json" > "$R/<id>.md"
jq -r '.modelUsage | keys[]' "$R/<id>.raw.json"   # the id that ran
```

Grant only the permissions the task needs: `--permission-mode` (`acceptEdits` lets it
edit files) plus `--allowedTools` for the commands its "done when" runs. Read-only shell
commands such as `ls` run without being listed. Put the prompt right after `-p`:
`--allowedTools` takes several values and would swallow a prompt placed after it. Use this
form from either host: a native subagent can't pin its effort.

## Claude reviewer

```bash
F=.claude-x-codex/<feature>/reviews
M=$(python3 "<plugin>/scripts/latest-model.py" claude "${CXC_CLAUDE_REVIEWER:-opus}" --effort "${CXC_REVIEW_EFFORT:-xhigh}" --project "$PWD") || exit
CXC_MODE=off claude -p "$(cat "$F/<phase>-prompt.md")" \
  --model "$M" --effort "${CXC_REVIEW_EFFORT:-xhigh}" \
  --allowedTools "Read" "Grep" "Glob" "Bash(git diff:*)" "Bash(git log:*)" \
  --disallowedTools "Skill" "ReportFindings" "Write" "Edit" "NotebookEdit" \
  --json-schema "$(cat "<plugin>/skills/run/references/review.schema.json")" \
  --output-format json < /dev/null > "$F/<phase>-r<n>.raw.json"
jq '.structured_output' "$F/<phase>-r<n>.raw.json" > "$F/<phase>-r<n>.json"
jq -r '.modelUsage | keys[]' "$F/<phase>-r<n>.raw.json"   # the id that ran
```

With `--json-schema`, the conforming object is the `structured_output` field of the
JSON result; keep the raw file, since the review schema has no room for the model id. `--allowedTools` grants only reading and `git diff`/`git log`; Claude Code also
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
