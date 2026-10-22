# context-rail — build guide

How to add the `context-rail` plugin to this marketplace yourself. Root `CLAUDE.md` rules apply throughout; this guide
names the ones that bite. Written 2026-10-22; not committed.

- **Measured files to ship:** z-lab `precedent-lab/build-canary-0.1.0/plugin/context-rail/`.
  - `plugin.sha256` lists their hashes. The hook asset is A′, sha256 `3c31c65f…`.
  - E4 and E5 measured exactly these bytes. Changing a skill, script or hook means a new z-lab experiment (Rule 9).
- **Reference implementation (optional):** local branch `feat/context-rail`, commit `c35b30d`, not pushed.
  - It is a complete release: plugin folder, five READMEs, CHANGELOG, marketplace 4.5.0, root READMEs, tests 108/108.
  - Diff against it, cherry-pick it, or delete it (`git branch -D feat/context-rail`).
- **History and evidence log:** `CONTEXT-RAIL-PLUGIN-PLAN.md`, which holds the gap list G1–G8 and the experiment log.

---

## 1. Decisions already made (maintainer, 2026-10-22)

Recorded in z-lab `precedent-lab/analyze/improvement-backlog.md`:

| # | Decision |
|---|---|
| D1 | Plugin name `context-rail`; skills `build` and `audit`. Evidence series stays `precedent-lab/`, following Rule 7's claude-x-codex precedent |
| D2 | z-lab company identifiers were masked by new commits, not a history rewrite |
| D3 | `build` only proposes personal items and never moves them |
| D4 | An explicit override that **names the recorded decision** is the user's confirmation. Any other conflicting request stops and asks |
| D5 | Behavior is measured on Claude Code only. Codex runs the same workflow through the marketplace, unmeasured beyond delivery |

## 2. Steps

### 2.1 Branch

Use a topic branch or commit on `main`; recent history does both. The last eight commits went to `main` directly, and
earlier work landed through PRs (#2–#4). The root `CLAUDE.md` sets no branch rule.

### 2.2 Plugin folder

```
plugins/context-rail/
├── .claude-plugin/plugin.json      name, description, version 0.1.0, author, homepage, repository, keywords
├── .codex-plugin/plugin.json       same + "skills": "./skills/", license MIT, interface{displayName, shortDescription,
│                                   longDescription, developerName, category, capabilities, defaultPrompt}
├── CLAUDE.md                       maintainer rules (2.3)
├── README.md + README.ko/ja/zh-CN/zh-TW.md   (2.4)
├── CHANGELOG.md                    (2.5)
└── skills/                         copy verbatim from the z-lab snapshot
    ├── build/SKILL.md
    ├── build/assets/precedent-context.py
    ├── build/scripts/{install-hooks.py, resident-size.py, records-lint.py}
    ├── build/references/{record-format.md, classify.md, host-codex.md}
    └── audit/SKILL.md
```

Copy `skills/` byte for byte, then prove it:

```bash
S=../z-lab/precedent-lab/build-canary-0.1.0
cp -R "$S/plugin/context-rail/skills" plugins/context-rail/
(cd plugins && find context-rail/skills -type f | sort | xargs shasum -a 256) | diff - <(grep context-rail/skills "$S/plugin.sha256" | sort -k2)
```

No `hooks/hooks.json`. The plugin installs no hooks; `build` writes project files.

### 2.3 `plugins/context-rail/CLAUDE.md` (maintainer rules)

State each invariant with its reason and evidence ID:

- **Project files, not plugin hooks.** A plugin hook runs only for the installer, so teammates' agents would get no
  records.
- **Inject the section text, not a pointer.** 3/15 → 44/45 (`real-env-rail-2.1.296` F2–F3).
- **Detect shell reads, and wire PostToolUseFailure on Claude.**
  - A Read-only hook fired 3/14, one that also watched the shell 14/14 (`arrive-then-read-2.1.296` F2).
  - A failed read arrives only as PostToolUseFailure (`platform-2.1.306-0.163.0` P2).
- **Total output < 10,000 chars, body ≤ 6,000, paragraph last.**
  - Longer output becomes a ~2,500-char preview on 2.1.306/2.1.308 (`platform-2.1.306-0.163.0` P3,
    `platform-r2-2.1.308-0.163.0` Q3).
  - The cap counts characters (`platform-unit-2.1.306` U1).
- **`cd` resolution handles both hook `cwd` conventions** (P4).
- **The paragraph is pinned by sha256 (`STOP_SHA256`).** Any wording change is a new experiment. Results for A′
  (`stop-en-r2-2.1.306` R1–R4):

  | Task | A′ | Without the paragraph |
  |---|---:|---:|
  | Trap breaks | 0/12 | 11/12 |
  | Explicit overrides that proceeded | 12/12 | — |
  | Conflict-free edits stopped | 0/15 | — |

  The earlier wording A was not adopted (`stop-en-2.1.306` S1–S3).
- **No write gate and no commit-token gate** (`gate-placement-2.1.296` F2–F4, `plan-rail-2.1.296` F3–F5).
- **`references/record-format.md` must match the hook code.** Change both in one commit.
- **Resident never grows, in chars and bytes; personal items are only proposed** (D3).
- **Fail open.**
- **Codex: claim delivery only** (`platform-2.1.306-0.163.0` P5–P8; D5).
- **The series is `precedent-lab/`** (D1).

### 2.4 READMEs (Rule 3: five languages, same commit; Rule 4: only READMEs are localized)

The English file is the source. Follow the header block of the other plugins: title, hosts line, one-line summary,
badges, anchor nav, language links, "Part of because-i-needed".

Sections:
1. **Start** — `/context-rail:build`, `$context-rail:build`, `audit`. One confirmation table before any write;
   personal items are never moved.
2. **What it writes** — `PRECEDENT.md`, `.claude/rules/*.md` (`paths:`), the hook, the settings wiring, and
   `context-rail.json`. Moved items are removed; there is no pointer line; resident size is checked in chars and bytes.
3. **Records** — example block, the nearest-record rule, heading matching, and a link to
   `skills/build/references/record-format.md`.
4. **The arrival hook** — which events, once per file per session and agent, the 10k cap and why, git-ignored files,
   fail-open.
5. **Changing a decision** — D4 in user terms: a named override proceeds and rewrites in place; anything else stops
   and asks.
6. **What was measured** — the table in §3 below, plus the "Not measured" list in §4.
7. **Codex** — the same workflow; delivery measured on 0.163.0 (P5–P8); behavior unmeasured; trust in `/hooks`.
8. **Requirements** (`python3` ≥ 3.9, `git`), **Installation**, **License**.

Translation headings follow existing usage:

| Language | Start | Requirements | Installation | License |
|---|---|---|---|---|
| ko | 시작하기 | 요구사항 | 설치 | 라이선스 |
| ja | 開始 | 必要条件 | インストール | ライセンス |
| zh-CN | 开始 | 要求 | 安装 | 许可证 |
| zh-TW | 開始 | 需求 | 安裝 | 授權 |

The anchor nav in each translation uses the GitHub slug of the translated heading.

### 2.5 `CHANGELOG.md` — `## [0.1.0] - <date>`

- **Added:**
  - `build` (inventory → classify → one confirmation → generate → verify);
  - `audit`;
  - the hook (events, cap);
  - the three scripts.
- **Why:** the claims in §3, each with its experiment path and finding IDs (Rule 9).
- **Not measured:** the list in §4, plus the Codex delivery-only note (D5).

### 2.6 Marketplace and root files

- `.claude-plugin/marketplace.json`:
  - Append the `context-rail` entry: `source ./plugins/context-rail`, version `0.1.0`, `category: development`, and a
    description ending "(writes project files only; the plugin itself adds no hooks)".
  - Bump `metadata.version` 4.4.0 → 4.5.0. A new plugin is a MINOR release; dashboard and budget did 4.2.0 → 4.3.0.
- Root `README.md`, `.ko`, `.ja`, `.zh-CN`, `.zh-TW` — make the same eight edits in each:
  1. The tagline gains "decision records that arrive with the file".
  2. Plugin count six → seven. Chinese files also have the digit form `6个` / `6個` on the Codex line.
  3. Add `,context-rail` to the Codex `--only` list.
  4. Add `codex plugin add context-rail@because-i-needed`.
  5. Add `$context-rail:build` to the Codex invocation sentence.
  6. Add a new `### [context-rail](plugins/context-rail) · \`v0.1.0\`` section after budget: bold summary, **Use it
     when**, **Entry**, **Heads-up** ("adds no hooks of its own; build writes a hook into your project after you
     confirm; measured on Claude Code only"), and the README link.
  7. Add `claude plugin install context-rail@because-i-needed` and `"context-rail@because-i-needed": true` in
     Installation.
  8. In the repository layout: "lists the seven plugins", `budget/` becomes `├──`, and a new
     `└── context-rail/ # 2 skills + project hook asset + 3 scripts`.
- Root `CLAUDE.md` line 3: "holding seven plugins (…, budget, context-rail)".
- No `dashboard.json`: there is no `mode` skill (Rule 11).

### 2.7 Tests

- New `tests/test_context_rail.py` covering:
  - `--self-test` passes;
  - hook mode echoes the event name and fails open on bad input;
  - `--max-output` stays under 10k;
  - the installer merges both hosts, keeps unrelated settings, is idempotent (`--check` clean), refuses a differing
    hook and refuses malformed settings;
  - `records-lint` flags orphan headings and blocks without a decision;
  - `resident-size --compare` fails on growth in characters.
- `tests/test_compatibility.py` `test_installer_dry_run_list_and_invalid_host`: change the count 6 → 7 and add
  `"context-rail"` to the name tuple.

### 2.8 Verify

```bash
claude plugin validate .                       # must pass
claude plugin validate plugins/context-rail    # passes with warnings:
                                               #   CLAUDE.md not loaded (expected, Rule 5)
                                               #   icon missing (harness has the same)
                                               #   LICENSE taken from repo root
python3 -m unittest discover -s tests          # all pass (108 on the reference branch)
grep -rn --include='*.md' --include='*.json' -F '4.4.0' . | grep -v CHANGELOG   # must print nothing
```

- The version `0.1.0` must appear in 13 places: 2 manifests, 1 marketplace entry, 5 plugin README badges, and 5 root
  README headings.
- Every relative link and anchor in the ten READMEs must resolve (Rule 3).
- Re-run the sha comparison from 2.2.

### 2.9 Commit (Rules 2, 6)

- One commit holds the version strings, CHANGELOG and READMEs.
- Author `zeriong <jaeryong95@gmail.com>`. No attribution footer, no amend, no force-push.
- Header ≤ 50 chars, e.g. `feat: add the context-rail plugin`. The body says why and cites the evidence.

## 3. Claims you may make (all measured on Claude Code, Opus, effort `xhigh`, headless)

| Claim | Number | z-lab `precedent-lab/` |
|---|---|---|
| Section text, not a pointer, reaches the model before the first edit | 3/15 → 44/45 | `real-env-rail-2.1.296` F2–F3 |
| The paragraph stops conflicting requests that do not name the record | 11/12 → 0/12 broke | `stop-en-r2-2.1.306` R1 |
| …lets explicit named overrides through, rewriting the record in place | 12/12 | `stop-en-r2-2.1.306` R2 |
| …does not stop conflict-free edits | 0/15 | `stop-en-r2-2.1.306` R3 |
| `build` moves items correctly | 5/5 runs, 14/14 items, 4/4 checks; `CLAUDE.md` 1,906 → 540 chars | `build-fidelity-0.1.0` B1–B3 |
| A normalized project keeps decisions better than the same decisions in `CLAUDE.md` | 12/12 → 0/12 broke; 0/15 false stops in both | `fresh-project-0.1.0` F1–F4 |
| Path-scoped rules attach on first contact (Read, shell read, Write); a 12k rule arrives whole | — | `platform-r2-2.1.308-0.163.0` Q1–Q2 |
| Codex 0.163.0 delivers PostToolUse context; reads arrive as `Bash`, edits as `apply_patch`; there is no failure event | — | `platform-2.1.306-0.163.0` P5–P8 |

Two caveats:
- The E5 effect bundles the move and the paragraph; they were not separated.
- The trap results come from synthetic fixtures (12–15 runs per cell) and one private repository.

## 4. Must be stated as not measured

- Other models and efforts, interactive sessions, delivery to subagents.
  - Subagents received 96% of real-use paragraphs (`real-use-2.1.299-2.1.306` R1).
- Records written in other languages with the English paragraph.
- Large repositories, resident files with blurry item boundaries, and partial approval of the table.
- The boundary of "names the record": a file name only, or "the old rule".
- On Codex, everything beyond delivery: `apply_patch` delivery, nested `AGENTS.md` timing, the cap, and every
  behavior effect.

## 5. Follow-ups (backlog, not required for 0.1.0)

- E3b: Korean records with A′, subagent delivery, effort high/max.
- Conflict-free edits close to a decision (same function, unrelated branch).
- Codex behavior, if the maintainer lifts D5.
