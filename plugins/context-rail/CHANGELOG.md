# Changelog

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
