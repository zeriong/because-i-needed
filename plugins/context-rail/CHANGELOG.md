# Changelog

## [0.3.1] - 2026-10-29

### Fixed

- A decision line with a qualifier before the colon — `- Decision (range):`, `- Decision B1:` — is now a decision
  line. Compression keeps it, and `records-lint` no longer flags its block as missing a decision. Both use one
  pattern; a word that merely starts with the label (`- Decisive:`) is still not a field.

`STOP` and `STOP_SHA256` are unchanged.

### Why

Measured in z-lab `precedent-lab/`, Claude Code 2.1.312:

- **Qualified labels** (`labels-0.3.1`, E9, deterministic, 2,681 governed files of a private repository). Qualified
  decision lines injected rose from 243 to 292, in the 8 compressed files where they differed; blocks flagged
  without a decision fell from 277 to 266. No file lost a decision or fell to a lower mode, against 0.3.0 and
  against that project's own hook.
- **A brief that says the decision is already made, without naming it** (`unnamed-preauth-0.3.1`, E10). The
  paragraph is unchanged; this measures it. A fixed brief — "already decided; don't re-litigate it; update the
  entry" — to a Sonnet worker broke the prohibition 12/12 with 0.1.0's paragraph and 0/12 with A3.

### Not measured

- The Agent-tool subagent path with a long natural brief, where one such run leaked in `real-repo-0.2.0`.

## [0.3.0] - 2026-10-29

### Added

- **A record where none exists.** An edit to a governed file that no `PRECEDENT.md` covers gets one line, once per
  directory: if the change makes a decision, create `<dir>/PRECEDENT.md` beside the file with a `## <file>` section and
  a decision block. Reading such a file still gets nothing.
- The edit reminder ("if this change makes a new decision, record it there") now comes once per record even when the
  file has no section yet; before, only files with a section got it.

### Fixed

- Compression no longer attaches a dropped field's continuation lines to the decision line above it. That bloat made
  long records fall from compressed to truncated and lose decisions.
- The remaining-decision list of a truncated record ends on a whole slug, using the space that is left.
- A shell read of several files skips a file already injected and reaches the next one, instead of saying nothing.

`STOP` and `STOP_SHA256` are unchanged.

### Why

Measured in z-lab `precedent-lab/record-0.3.0/` (E8), Claude Code 2.1.312:

- **Write side** (synthetic project with no recording rule, 72 runs). Edits on paths without a record were recorded
  0/9 with no hook, 3/9 with 0.2.0 and 8/9 with 0.3.0. Edits that made no decision created no record (0/6). Files with
  a section were recorded 7/9 (0.2.0 8/9, no hook 2/9).
- **Compression** (deterministic, every governed file of a private repository, 2,681 files). Against that project's
  own arrival hook, 0.2.0 gave fewer decisions in 3 files and dropped 2 from compressed to truncated; 0.3.0 gave the
  same decisions in every file.

### Not measured

- Edits made with shell commands (`cat > file`, `sed -i`) are not seen as edits, so they get no reminder. All three
  0.3.0 runs in E8 that recorded nothing wrote the file that way.
- The keep side (traps, overrides, conflict-free edits) was not rerun with models; the paragraph is unchanged and the
  deterministic comparison above stands in for it.

## [0.2.0] - 2026-10-23

### Changed

- The confirmation paragraph (A3) now says when a brief from another agent counts. A subagent's or worker's brief is
  a confirmation only when it relays that the user named the decision and said to override it. "Go ahead anyway" or
  "a newer decision replaces whatever is recorded" is not; the agent stops and reports back to whoever assigned the
  task, so that agent can ask the user. `STOP_SHA256` changed with it.

### Why

Measured in z-lab `precedent-lab/` on synthetic fixtures, Claude Code 2.1.309 and Codex 0.163.0.

- **The gap** (`leaf-2.1.309`, E6). With 0.1.0's paragraph, workers given peer-coding's brief (Sonnet `claude -p`,
  Codex `gpt-6-luna`) and an orchestrator that read the file first all kept the rule. Agent-tool subagents under an
  orchestrator that had not seen the record did not:
  - Sonnet subagents broke 6/9 when the orchestrator pre-authorized the override ("still make the change; the new
    decision supersedes the record").
  - Opus subagents refused 3/12 correctly relayed named overrides.
- **The fix** (`leaf-r2-2.1.309`, E6′, adopted). With A3:
  - every path — the top-level session, Opus and Sonnet subagents, Sonnet and Codex workers — was 0/12 broke,
    12/12 named overrides proceeded, 0/15 conflict-free edits stopped;
  - a fixed pre-authorizing brief to a Sonnet worker: 12/12 broke with 0.1.0's paragraph → 0/12 with A3
    (p=7.4×10⁻⁷).

### Not measured

- A main agent that invents a named override the user never gave (0/24 natural occurrences; not induced).
- Orca's two-way workers, interactive sessions, other models and efforts, Korean records, and running `build` and
  `audit` on Codex.

## [0.1.0] - 2026-10-22

### Added

- `context-rail:build` sets up the rail in a project, in this order:
  1. It inventories every item in the always-loaded instruction files (`CLAUDE.md`, `AGENTS.md`).
  2. It classifies each item: resident, path rule, decision record, or proposal only (automation, personal, drop).
  3. It confirms the table once with the user.
  4. It writes `PRECEDENT.md` records beside the code and `paths:`-scoped rule files, and removes moved items from
     the resident files.
  5. It installs the arrival hook and verifies the result. Resident files must not grow, in characters or in bytes.
- `context-rail:audit`: the same checks, read-only.
- `precedent-context.py`, the arrival hook.
  - On Claude Code it runs on PostToolUse (Read, Edit, Write, MultiEdit, Bash) and PostToolUseFailure (Bash). On Codex
    it runs on PostToolUse (Bash, `apply_patch`).
  - It injects the section of the nearest `PRECEDENT.md` that names the file, followed by the confirmation paragraph.
    Output stays under 10,000 characters.
- Scripts: `install-hooks.py` (merges settings, idempotent, refuses to overwrite a differing hook), `resident-size.py`
  and `records-lint.py`.

### Why

Every experiment below is in z-lab `precedent-lab/`, measured on Claude Code with Opus at effort `xhigh`.

- **Inject the section text, not a pointer** (`real-env-rail-2.1.296` F2–F3). The prohibition reached the model before
  the first edit in 3/15 trap runs with a pointer, and in 44/45 with the section text.
- **Detect shell reads and wire PostToolUseFailure.**
  - Agents read with `cat`/`sed`. A Read-only hook fired in 3/14 runs, a hook that also watched the shell in 14/14
    (`arrive-then-read-2.1.296` F2).
  - On 2.1.306 a failed shell read arrives only as PostToolUseFailure (`platform-2.1.306-0.163.0` P2).
- **Keep the output under 10,000 characters.**
  - On 2.1.306 and 2.1.308, longer output becomes a ~2,500-character preview, which drops the paragraph at the end
    (`platform-2.1.306-0.163.0` P3, `platform-r2-2.1.308-0.163.0` Q3).
  - The cap counts characters, not bytes (`platform-unit-2.1.306` U1).
- **The confirmation paragraph (A′)** — adopted in `stop-en-r2-2.1.306` R1–R4:
  - Authority requests that do not name the record broke the prohibition 0/12 with the paragraph, 11/12 without it.
  - Explicit overrides that name the record proceeded 12/12, with the record rewritten in place.
  - Conflict-free edits were stopped 0/15.
  - The earlier wording halved breaks only, 10/12 → 5/12, and was not adopted (`stop-en-2.1.306` S1–S3).
  - That an explicit, named override is the confirmation is the maintainer's decision D4
    (`precedent-lab/analyze/improvement-backlog.md`).
- **`build`** — adopted in `build-fidelity-0.1.0` B1–B3; the harness canary is `build-canary-0.1.0`.
  - Five headless runs each moved 14/14 items correctly and passed the four verification checks.
  - Each wrote nothing before the user's answer, and shrank `CLAUDE.md` from 1,906 to 540 characters.
- **`audit`** — adopted in `audit-canary-0.1.0` U1–U3.
  - Four runs changed no file and ran all five checks plus the asset comparison.
  - They named 3/3 planted defects and reported none on a healthy copy.
- **Normalization helps on this fixture** (`fresh-project-0.1.0` F1–F4).
  - Authority traps broke 12/12 with the decisions only in `CLAUDE.md`, and 0/12 after `build`.
  - False stops were 0/15 in both.
  - The move and the paragraph were measured together.
- **Path-scoped rules arrive on contact** (`platform-r2-2.1.308-0.163.0` Q1–Q2).
  - A `paths:` rule attaches on the first Read, shell read or Write of a matching file.
  - A 12,000-character rule arrived whole.
- **No write gate and no commit-token gate** (`gate-placement-2.1.296` F2–F4, `plan-rail-2.1.296` F3–F5).
  - A hidden gate missed interpreter writes, and a visible one denied only after implementation.
  - A commit token passed every case.

### Not measured

These are hypotheses, not claims:
- other models and efforts, interactive sessions, delivery to subagents;
- records in other languages with this paragraph;
- large repositories and resident files with blurry item boundaries;
- whether a user's partial approval of the table is applied faithfully.

On Codex, only the platform was measured, with a probe hook rather than this plugin's hook (Codex 0.163.0,
`platform-2.1.306-0.163.0` P5–P8): hook output reaches the model, reads arrive as `Bash` and edits as `apply_patch`,
and there is no failure event. Behavior on Codex is unmeasured by
the maintainer's decision D5.
