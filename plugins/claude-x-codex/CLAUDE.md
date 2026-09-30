# claude-x-codex — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to claude-x-codex.

Contents: three skills (`skills/run` with six references and `review.schema.json`, `skills/mode`, `skills/audit`),
the hook `hooks/hooks.json` (UserPromptSubmit → `hooks/mode-context.sh`), and three scripts in `scripts/` shared by
the skills (`mode.sh`, `context-audit.sh`, `worktree-setup.sh`). No agents, no MCP servers. The root `install.sh` is
the marketplace installer, not part of this plugin.

---

## Rule 1 — Script invariants

- `mode-context.sh` runs on **every prompt** of every installed user. It always exits `0` and prints nothing while the
  mode is off, so a normal session pays no token cost.
- `context-audit.sh` is **read-only**: it never writes a file or changes git state. The audit skill may save its
  report and add `.claude-x-codex/` to the path returned by `git rev-parse --git-path info/exclude`.
  Resolve this path instead of assuming `.git` is a directory, including in linked worktrees.
  An applicable `AGENTS.override.md` wins over `AGENTS.md`; audit it before asserting context parity.
- `worktree-setup.sh` finds the main tree through `git rev-parse --git-common-dir`, so it works from the main tree,
  a subdirectory, or inside the worktree itself. It skips anything already present (idempotent).
- `mode.sh` resolves `CXC_MODE` → project flag → global flag → `off`. The flag file is one line, `mode=on|off`;
  anything else counts as unset.
- Scripts stay LF (`.gitattributes`) and executable (git mode `100755`), and bash 3.2 compatible — no associative
  arrays, `mapfile`, or `${var,,}`.

## Rule 2 — Copies of one fact change in the same commit

| Fact | Source | Copies |
|---|---|---|
| `CXC_*` defaults | `skills/run/SKILL.md` Configuration | five READMEs (Configuration), `host-*.md`, `transport-*.md` |
| Reviewer models and efforts (Claude Opus · Codex `gpt-6-sol`, both `xhigh`; workers `high`; a top model or `max` only after asking the user) | `skills/run/SKILL.md` Review routing and Work lanes | `host-*.md` tables, `transport-standalone.md` and `transport-orca.md` commands, five READMEs (How it works) |
| Platform support | `skills/mode/SKILL.md` Platforms | five READMEs (Platforms) |
| Mode scopes and resolution order | `scripts/mode.sh` header | `skills/mode/SKILL.md` Scopes, five READMEs (Commands) |
| Review JSON shape | `skills/run/references/review.schema.json` | `templates.md` review prompt example |
| Hook note (four lines, ~100 input tokens — F21) | `hooks/mode-context.sh` | five READMEs (Heads-up: "four-line" and "about 100 input tokens") |
| What each vendor reads | `context-bridge.md` table | `context-audit.sh` parity column, `host-*.md` Native context |
| Command list | the three skill folders | five plugin READMEs (Commands), five root READMEs (Entry) |

## Rule 3 — Environment facts carry the version they were checked on, and their evidence

Checked on Claude Code 2.1.283, Codex CLI 0.157.1, and Orca 1.4.215 (2026-09-28). Raw outputs and generated metrics live in
the public lab repository `zeriong/z-lab`: `claude-x-codex-lab/` (IDs F·K·C·D·L·E) and `plugin-platform-lab/` (IDs G·H·V). When
one of these CLIs changes, re-run the affected probes there and update the versions here, in the README Requirements,
`context-bridge.md`, and `transport-standalone.md`.

- Codex `--profile <name>` loads `$CODEX_HOME/<name>.config.toml`; a legacy `[profiles.<name>]` table in `config.toml`
  makes `--profile` fail (F20).
- Codex reads `CLAUDE.md` only through `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'` (measured), or the same top-level key in
  `config.toml` (inferred: `-c` is defined as overriding that file): 3/3 with it, 0/3 without (F01). The fallback reaches nested directories (F03), never applies where `AGENTS.md`
  exists (F02), and does not follow `@path` imports (F04).
- Claude Code reads `AGENTS.md` in a directory with no `CLAUDE.md`, nested ones included (F05, F07); where both exist it
  loads only `CLAUDE.md` (F06).
- `codex exec --output-schema <file>` and `claude -p … --json-schema '<schema>' --output-format json` (object in
  `.structured_output`) both returned schema-valid reviews, 3/3 each (F09, F10).
- `codex exec` waits for EOF on an open stdin (a 15 s pipe added ~15 s, F18), so every call ends with `< /dev/null`.
  A relative `-o` resolves against the caller's directory, not `-C` (F17).
- `claude -p`: `--allowedTools` takes several values and swallows a prompt placed after it (F19).
- Reviewers cannot write: Codex `-s read-only` 0/6 (F14); the Claude reviewer form 0/6 even under `defaultMode: auto`
  (F11). Claude still runs read-only commands such as `ls` unlisted (F12, F16), and without a deny list it used `Skill`
  (a forked review) and `ReportFindings` (F13). The deny list `--disallowedTools "Skill" "ReportFindings" "Write" "Edit"
  "NotebookEdit"` removed them without any context growth, at a cost no higher than before in cross-run comparison
  (D01–D04, L01–L02); names the build lacks are ignored (checked with a made-up name). **Do not narrow with `--tools`**:
  a whitelist grew the last turn's context ~6× and cost 1.5× on haiku (C01, C02, interleaved runs) and ~9× on opus (K05, n=1).
- The documented transport forms ran end to end: `codex-bulk` worker in a linked worktree → gate → Codex and Claude
  reviewers with schemas; main tree untouched (F15, L01).
- The UserPromptSubmit hook runs in `claude -p` too, loads without the `plugin.json` `hooks` field, and is not loaded
  twice when the field is present (H01–H03). `CXC_MODE=on` adds ~98 input tokens per prompt (F21).
- `disable-model-invocation: true` keeps a skill listed but rejects the model's Skill call; the slash command still works (G07).
- Orca `worker-start` takes `--model` and `--effort` and has no permission flag (F23).
- In a skill, `${CLAUDE_PLUGIN_ROOT}` (braced) is replaced with the plugin path in the SKILL.md text at load; the unbraced
  form is not, the Bash environment has no such variable (V01–V02), and a reference file read later keeps it literal, so a
  command copied from one fails with exit 127 (V03). So scripts are called from SKILL.md text, and references name them as
  `<plugin>/…`, which `run` defines in SKILL.md — that form ran the script 3/3 (V06).
- Effort (E1–E6): Claude `--effort` takes `low, medium, high, xhigh, max`; Codex `gpt-6-sol` takes `low … xhigh, max, ultra`
  (`ultra` = max plus automatic task delegation), `gpt-6-luna` up to `max`. So `xhigh` is the same rung on both — one below
  `max`. `claude -p --model opus --effort xhigh` and `--model sonnet --effort high` run; an unknown value only warns on stderr
  and falls back to the default. Codex `-c model_reasoning_effort="xhigh"` shows in the run header, and a misspelled value
  passes local checks unchanged. Claude Code subagent definitions and the Agent tool have no effort setting, so workers and
  reviewers use the `claude -p` forms on either host.

**Why:** the first draft of this plugin assumed several of these wrongly — profile tables inside `config.toml`, the
`--allowedTools` argument order, Claude not reading `AGENTS.md` — and the first fix for the reviewer (`--tools`) made it
nine times more expensive. Each was found only by running the CLI and counting.

## Rule 4 — After editing a script, run it

The hook running in a session is the installed copy (root Rule 1), so test the source directly, in temp directories,
with `CODEX_HOME` and `XDG_CONFIG_HOME` pointed at temp directories so the real user config is neither read nor written.
At minimum:

```bash
AP="$PWD/plugins/claude-x-codex"
T=$(mktemp -d) && git -C "$T" init -q
(cd "$T" && XDG_CONFIG_HOME="$T/cfg" bash "$AP/scripts/mode.sh" on >/dev/null)
echo '{"prompt":"x"}' | (cd "$T" && XDG_CONFIG_HOME="$T/cfg" CLAUDE_PLUGIN_ROOT="$AP" bash "$AP/hooks/mode-context.sh"); echo "exit=$?"  # note, 0
echo '{"prompt":"x"}' | (cd "$T" && CXC_MODE=off CLAUDE_PLUGIN_ROOT="$AP" bash "$AP/hooks/mode-context.sh"); echo "exit=$?"            # nothing, 0
before="$(git -C "$T" status --porcelain)"; (cd "$T" && CODEX_HOME="$T/codex" bash "$AP/scripts/context-audit.sh" >/dev/null)
[ "$before" = "$(git -C "$T" status --porcelain)" ] && echo read-only
rm -rf "$T"
```

When you change `worktree-setup.sh`, also run it from inside a linked worktree and confirm the copies land.

To check the hook itself, don't look for its output in `claude -p --output-format stream-json`: Claude Code 2.1.283 emits
no UserPromptSubmit hook events there (G06). Compare the result event's input tokens (input + cache_creation +
cache_read) for the same prompt with `CXC_MODE=on` and `off`, using `--setting-sources project --plugin-dir <plugin>
--tools ""` so nothing else varies; `on` should be about 100 tokens higher (F21).

## Codex compatibility evidence — 0.2.0

See z-lab `claude-x-codex-lab/codex-compat-0.2.0/` and `codex-mode-json-0.2.0/` (C01–C04) and the shared
`plugin-platform-lab/codex-final-0.158.0/` packaging/installer checks. These records
cover host wiring and the named fixture paths, not quality improvements. Keep the
existing workflow invariants when changing an adapter.

Additional setting-parity checks: z-lab `claude-x-codex-lab/codex-parity-0.2.0/` (C05, C06).

Re-review fixes: z-lab `claude-x-codex-lab/codex-rereview-0.2.0/` (C07, C08).
Host routing consistently honors configured reviewer model/effort. Audit reports pointer/fallback mentions as checks rather than treating a filename substring as proof of equivalent instructions.
