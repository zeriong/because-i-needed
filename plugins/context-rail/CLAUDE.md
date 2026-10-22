# context-rail — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to context-rail.

Contents:
- `skills/build/SKILL.md` with `references/` (`record-format.md`, `classify.md`, `host-codex.md`);
- `skills/build/assets/precedent-context.py` (the arrival hook copied into projects);
- `skills/build/scripts/` (`install-hooks.py`, `resident-size.py`, `records-lint.py`);
- `skills/audit/SKILL.md`.

The plugin itself installs no hooks; `build` writes project files.

**Evidence series: z-lab `precedent-lab/`.** The series keeps its name although the plugin is `context-rail`. Root
Rule 7's claude-x-codex precedent applies.

## Invariants

- **Project files, not plugin hooks.** `build` copies the hook and merges settings into the project; `hooks/hooks.json`
  stays absent.
  - **Why:** a plugin hook runs only for the person who installed the plugin, so teammates' agents would get no
    records.
  - The measured setup was a project hook (`arrive-then-read-2.1.296`, `real-env-rail-2.1.296`).
- **Inject the section text, never a pointer.**
  - **Why:** with a pointer-only hook, the prohibition reached the model within one call of arrival and before the
    first edit in 3/15 trap runs; with the section text, 44/45 (`real-env-rail-2.1.296` F2–F3, p=4×10⁻⁹).
- **Detect Bash reads; wire PostToolUseFailure on Claude.**
  - **Why:** agents read with `cat`/`sed`. A pointer hook bound to Read fired 3/14; with Bash detection, 14/14
    (`arrive-then-read-2.1.296` F2).
  - A failed read arrives only as PostToolUseFailure on 2.1.306 (`platform-2.1.306-0.163.0` P2).
  - Codex has no failure event and fires PostToolUse on errors (P6).
- **Total output < 10,000 characters; body ≤ `bodyCap` (6,000); the paragraph goes last.**
  - **Why:** on 2.1.296 a longer context was dropped whole (`arrive-then-read-2.1.296` F6). On 2.1.306 it becomes a
    ~2,500-char preview plus a file, which cuts off the paragraph (`platform-2.1.306-0.163.0` P3).
  - The cap counts characters (`platform-unit-2.1.306` U1).
  - `--self-test` checks a 40-decision record.
- **`cd` resolution handles both hook conventions.**
  - **Why:** Claude reports the post-command `cwd` (`platform-2.1.306-0.163.0` P4). The Codex probe ran no `cd`.
  - The hook tries the other base when a path does not resolve. Self-test covers both.
- **The confirmation paragraph is pinned by sha256** (`STOP_SHA256`, checked in `--self-test`).
  - **Why:** the wording is the measured variable. Any edit is a new experiment.
  - The shipped text is A′ (`stop-en-r2-2.1.306`, adopted 2026-10-22): an explicit override that names the record is
    the confirmation, and any other conflicting request stops and asks.
  - Measured on a synthetic fixture at `xhigh`:

    | Task kind | A′ | Control |
    |---|---:|---:|
    | Authority requests that do not name the record (trap breaks) | 0/12 | 11/12 (p=9.6×10⁻⁶) |
    | Explicit overrides proceeding with an in-place record rewrite | 12/12 | — |
    | Conflict-free edits stopped | 0/15 | — |

  - The earlier English text (A) halved breaks only, 10/12 → 5/12, and was not adopted (`stop-en-2.1.306` S1–S3).
    Its breaks read the user's override as the confirmation.
  - **Maintainer rule (2026-10-22):** an explicit override that names the record counts as the confirmation.
    `references/record-format.md` says the same.
- **No PreToolUse write gate and no commit-token gate.**
  - **Why:** a hidden gate missed interpreter writes and skipped records, 5/12 (`gate-placement-2.1.296` F2–F3).
  - A visible gate denied only after implementation and false-positived on Bash 4/4 (`plan-rail-2.1.296` F3–F4).
  - A commit token passed 14/14 (`gate-placement-2.1.296` F4). In real use the token was on 22/31 agent commits
    (`real-use-2.1.299-2.1.306` R4, post-hoc).
- **Records are parsed exactly as `references/record-format.md` says.**
  - The heading, path-match, compression and field-label rules there must match the hook code.
  - Changing one changes both in the same commit.
- **Resident never grows; personal items are only proposed.**
  - **Why:** maintainer decisions G2 and G3 from the rail's origin, and 2026-10-22 ("propose only").
  - A byte-only count once hid a +15-character growth, so `resident-size.py` checks both units.
- **Fail open.** Any internal hook error exits 0 with no output, so a broken hook never blocks the agent.

## Codex

**Maintainer decision D5** (z-lab `precedent-lab/analyze/improvement-backlog.md`): behavior is measured on Claude
Code only. Codex runs the same workflow through the marketplace (`.codex-plugin`, `references/host-codex.md`,
`install-hooks.py --host codex`).

The only Codex facts claimed are the measured platform ones (with a probe hook, not this plugin's hook) (`platform-2.1.306-0.163.0` P5–P8, Codex 0.163.0):
- PostToolUse and UserPromptSubmit context reach the model;
- reads arrive as `Bash` and edits as `apply_patch`;
- there is no failure event.

The README states that everything else on Codex is unmeasured. Do not add a Codex claim without a z-lab record.

## Measured for 0.1.0

- `build` fidelity, E4 (`build-fidelity-0.1.0`): 5/5 headless runs moved 14/14 items correctly and passed all four
  Phase 5 checks. Each left 0 changes after turn 1. The harness canary is `build-canary-0.1.0`.
- `audit`, read-only (`audit-canary-0.1.0` U1–U3): 4/4 runs changed nothing, ran every check and named 3/3 planted
  defects. U4: `install-hooks.py --check` exits 2 when the hook differs, so the wiring is not reported in that case.
- Fresh-project effect, E5 (`fresh-project-0.1.0`): authority traps broke 12/12 when the decisions sat only in
  `CLAUDE.md`, and 0/12 after normalization. False stops were 0/15 in both.
  - This bundles the move and the paragraph; they are not separated.

## Not yet measured (README and CHANGELOG must say so)
- Subagent delivery behavior, effort high/max, Korean records with the English paragraph (E3b).
- On Codex: `apply_patch` delivery, nested `AGENTS.md` timing, the cap, and every behavior effect. These are out of
  scope by decision D5.
- Claude path-scoped rules are measured (`platform-r2-2.1.308-0.163.0` Q1–Q3): they attach on the first Read, Bash read
  or Write of a matching file, and a 12,000-char rule arrived whole.
