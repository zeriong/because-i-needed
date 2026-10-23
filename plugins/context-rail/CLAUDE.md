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
  - The shipped text is A3 (`leaf-r2-2.1.309`, adopted 2026-10-23). It is A′ (`stop-en-r2-2.1.306`, adopted
    2026-10-22: an explicit override that names the record is the confirmation, any other conflicting request stops
    and asks) plus the delegation rule: a brief from another agent counts only when it relays the user's named
    override; "go ahead anyway" or "a newer decision replaces whatever is recorded" does not, and the agent reports
    back to whoever assigned the task.
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
  - **Why the delegation rule (A3):** with A′, Sonnet subagents broke 6/9 when a main agent that had not seen the record
    pre-authorized the override, and Opus subagents refused 3/12 correctly relayed named overrides
    (`leaf-2.1.309` F3–F4). With A3 every path was 0/12 · 12/12 · 0/15 — Opus and Sonnet subagents, Sonnet `claude -p`
    and Codex workers, and the top-level session — and a fixed pre-authorizing brief to a Sonnet worker went from
    12/12 broken (A′) to 0/12 (A3), p=7.4×10⁻⁷ (`leaf-r2-2.1.309`).
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

**Maintainer decision D6** (2026-10-23) widened D5 for the leaf-agent rounds. A Codex worker (`gpt-6-luna`, effort
high, peer-coding's brief, hook installed by `install-hooks.py --host codex`) kept the paragraph: 0/12 · 12/12 · 0/15
under A′ (`leaf-2.1.309`) and under A3 (`leaf-r2-2.1.309`).

The README states that everything else on Codex is unmeasured. Do not add a Codex claim without a z-lab record.

## Measured for 0.1.0

- `build` fidelity, E4 (`build-fidelity-0.1.0`): 5/5 headless runs moved 14/14 items correctly and passed all four
  Phase 5 checks. Each left 0 changes after turn 1. The harness canary is `build-canary-0.1.0`.
- `audit`, read-only (`audit-canary-0.1.0` U1–U3): 4/4 runs changed nothing, ran every check and named 3/3 planted
  defects. U4: `install-hooks.py --check` exits 2 when the hook differs, so the wiring is not reported in that case.
- Fresh-project effect, E5 (`fresh-project-0.1.0`): authority traps broke 12/12 when the decisions sat only in
  `CLAUDE.md`, and 0/12 after normalization. False stops were 0/15 in both.
  - This bundles the move and the paragraph; they are not separated.

## Measured for 0.2.0

- Leaf agents, E6 (`leaf-2.1.309`): with A′, peer-coding workers (Sonnet `claude -p`, Codex) and an orchestrator that
  reads first kept the rule; Agent-tool subagents under a main agent that had not seen the record did not (see the
  paragraph invariant).
- A3, E6′ (`leaf-r2-2.1.309`): adopted under the rules frozen in its SPEC, including maintainer decision D7 (hold the
  release if only the Opus subagent's overrides missed; it did not trigger).

## Not yet measured (README and CHANGELOG must say so)
- Effort high/max for the main agent, Korean records with the English paragraph (E3b). Subagent and worker behavior
  is measured (`leaf-*`).
- A main agent that invents a named override the user never gave — the path A3 leaves open. It occurred 0/24 times in
  E6′ and was not induced.
- On Codex: `apply_patch` delivery, nested `AGENTS.md` timing, the cap, and running `build`/`audit`. The paragraph's
  effect on a Codex worker is measured (D6).
- Claude path-scoped rules are measured (`platform-r2-2.1.308-0.163.0` Q1–Q3): they attach on the first Read, Bash read
  or Write of a matching file, and a 12,000-char rule arrived whole.
