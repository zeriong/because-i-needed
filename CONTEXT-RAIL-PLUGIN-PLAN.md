# CONTEXT-RAIL-PLUGIN-PLAN

Status: **draft, not committed, nothing ships yet.** Written 2026-10-22. The platform probes (E1+E2) were run the same
day, and G2 and most of G3 are resolved. Still blocking: G1 (English paragraph), G2b (Claude path rules), G3 leftovers, G4 (normalization), G6.
Inputs: z-lab `precedent-lab/` (5 experiments, 2026-10-10 → 10-14) and the maintainer's application of the results to a
private repository (merged 2026-10-16). This file is the pre-build brief for adding the "context rail" to this
marketplace. Root rules (`CLAUDE.md`) apply in full; this plan names the ones that bind it.

---

## 1. Goal

> Install the plugin, run its skill, and the project's rules are normalized so that agents work in the right context.

Concretely, after one run in a target project:

1. **Decisions live next to the code they govern.** A `PRECEDENT.md` beside the source holds `## <file>` → `### §<slug>`
   blocks (decision, prohibition, reason, evidence). Rules that only apply to some paths move to path-scoped rule files.
2. **A record arrives when a file does.** A PostToolUse hook puts the governing section's text into the model's context
   the moment the agent reads or edits that file — not a pointer, the text.
3. **Changing a recorded decision needs the user.** The injected section ends with a measured confirmation paragraph:
   stop before implementing, name the invalidation reason and its evidence, ask.
4. **Resident context does not grow.** Always-loaded files (`CLAUDE.md`, `AGENTS.md`, …) are only replaced or shrunk,
   measured in characters *and* bytes.
5. **Personal and project context are separated.** "Must another person's agent follow this?" → repository files;
   otherwise → git-ignored local files.

## 2. What the evidence supports

The five `*-2.1.296/` experiments share one setup:

- Claude Code headless (`claude -p`, bypass permissions), model `claude-opus-5-5`.
- One private repository with a mature record corpus (88 `PRECEDENT.md`, 589 decisions).
- Judges were separate sessions of the same model family.
- Costs are self-reported (sum ≈ $416, judge sessions excluded).

The `platform-2.1.306-0.163.0/` rows use a different setup: a synthetic one-file fixture, one run per case, and no
behavior judging — they check delivery only.

| Claim | Measured | Evidence (z-lab `precedent-lab/`) |
|---|---|---|
| A pointer-only arrival hook rarely fires: agents read with Bash, not the Read tool | fired 3/14 → 14/14 once Bash reads were detected | `arrive-then-read-2.1.296/` F2 |
| Hook `additionalContext` over ~10,000 chars is dropped **whole** | 9,996 delivered / 10,046 dropped (UserPromptSubmit, 2.1.296) | `arrive-then-read-2.1.296/` F6 |
| Resident copies of records cost every turn | +39% input per turn; full corpus would not fit | `arrive-then-read-2.1.296/` F6 |
| Injecting the section text on arrival fixes the chain (prohibition line reaches the model within +1 call and before the first edit) | 3/15 → 44/45, p=4×10⁻⁹, cost −5% | `real-env-rail-2.1.296/` F3 |
| A one-line "no section" notice keeps the chain and cuts that event | 14–15/15 kept; 2,128 → 106 chars per event | `plan-rail-2.1.296/` F8 |
| Fixing the chain alone does **not** stop agents overturning records | 37/48 broke a prohibition; arm differences not significant | `real-env-rail-2.1.296/` F4 |
| The confirmation paragraph at arrival stops overturning before implementation | 0/12 vs control 10/12, p=7×10⁻⁵; 12/12 stopped before editing; cost −60% | `gate-placement-2.1.296/` F1 |
| It does not stop non-conflicting edits | false stop 0/15 (control 0/15); 95% upper bound ≈ 22%; cost +44% | `false-stop-2.1.296/` F1–F2 |
| A PreToolUse write gate blocks only what it can see | hidden gate 5/12; misses interpreter writes and skipped records; visible gate fires after implementation; Bash string matching 4/4 false positives | `gate-placement-2.1.296/` F2–F3, `plan-rail-2.1.296/` F3–F5 |
| A commit-time "record present" gate is a weak backstop | blocks skipped records 14/14, passes with a declared token or any unrelated block 14/14 | `gate-placement-2.1.296/` F4 |
| Failed read calls get no PostToolUse injection | 0 injections on 7 `is_error` read calls | `false-stop-2.1.296/` F3 |
| Memory and plugin context is a fixed per-turn cost | first turn −41%, cost −20% with both off; chain kept | `real-env-rail-2.1.296/` F1, F7 |
| Codex fires PostToolUse for shell commands | observed on Codex 0.162.1 (hook input only) | `free-hands-lab/session-id-0.3.0/` S01 |
| **2.1.306:** Read, Bash `cat`, Edit and subagent Read deliver PostToolUse context | delivered (n=1 each; subagent event carries `agent_id`) | `platform-2.1.306-0.163.0/` P1 |
| **2.1.306:** a failed Bash read arrives **only** as PostToolUseFailure | PostToolUse not fired; PostToolUseFailure delivered | `platform-2.1.306-0.163.0/` P2 |
| **2.1.306:** over-cap context is no longer dropped whole | 9,990 chars delivered; 10,050 chars persisted to a file, the model sees a ~2,500-char head preview + path; the tail (where the confirmation paragraph sits) is out of context unless the model reads the file | `platform-2.1.306-0.163.0/` P3 |
| **2.1.306:** the cap counts characters, not bytes | Hangul 4,000 chars (11,952 B) and 9,990 chars (29,922 B) delivered whole, PostToolUse and UserPromptSubmit | `platform-unit-2.1.306/` U1 |
| **2.1.306:** Bash hook input `cwd` is the post-command directory | `cd src && cat alpha.ts` → `<repo>/src` | `platform-2.1.306-0.163.0/` P4 |
| **Codex 0.163.0:** PostToolUse and UserPromptSubmit context reach the model | delivered; shell arrives as `Bash` + `{"command": …}` (same shape as Claude); edits arrive as `apply_patch` with the path in `*** Update File:`; no Read tool | `platform-2.1.306-0.163.0/` P5, P8 |
| **Codex 0.163.0:** no failure event; failed shell calls still fire PostToolUse | delivered | `platform-2.1.306-0.163.0/` P6 |
| **Codex 0.163.0:** no 10k cap observed | 9,990 / 10,050 / 30,000 chars all present in model-visible history (middle not checked); the model treats it as hidden developer context and may refuse to quote it | `platform-2.1.306-0.163.0/` P7 |

## 3. What it does not support — gaps

**Blocking** = Rule 9 forbids release until measured. **Hypothesis** = may ship only if the README and CHANGELOG label it
a hypothesis.

| # | Gap | Class | Why |
|---|---|---|---|
| G1 | **English confirmation paragraph.** The measured text is Korean (v3) and cites a repo-specific rule (`§24`). Rule 4 requires hook messages in English, and the generic text must carry the four invalidation reasons itself. The 0/12 and 0/15 results do not transfer to new wording. | Blocking | Rule 4 + Rule 9 (the mechanism itself) |
| G2 | ~~**Platform behavior on current CLIs.**~~ **Resolved 2026-10-22** on 2.1.306 (`platform-2.1.306-0.163.0/` P1–P4, n=1 each): delivery on Read/Bash/Edit/subagent, PostToolUseFailure for failed reads, post-command `cwd`. Changed behavior: over-cap output becomes a ~2.5k preview + file, not a drop. The cap counts characters (`platform-unit-2.1.306/` U1), so character limits also hold for Hangul records. Remaining: the exact boundary (between 9,990 and 10,050 chars). Re-run on each CLI bump the plugin claims support for. | Resolved (re-run per CLI) | Rule 9 ("run it, don't recall it") |
| G2b | ~~**Claude path-scoped rules.**~~ **Resolved 2026-10-22** on 2.1.308 (`platform-r2-2.1.308-0.163.0/` Q1–Q3, n=1 each).<br>• A `paths:` rule attaches as `nested_memory` on the first Read, Bash read or Write of a matching file, and not at session start.<br>• A rule without `paths:` loads at start like a resident file.<br>• A 12,000-char rule arrived whole, so the hook's 10k cap does not apply to it.<br>• 2.1.308 keeps the hook preview behavior.<br>The Codex half (apply_patch delivery, nested `AGENTS.md`, the 100k cap) hit the account usage limit; it reruns after 2026-10-27 15:32 or on another account if the maintainer allows. | Resolved (Claude) / pending (Codex) | Rule 9 |
| G3 | **Codex — mostly resolved 2026-10-22** on 0.163.0 (P5–P8). PostToolUse context reaches the model. The shell arrives as `Bash` + `{"command": …}`. There is no failure event, and errors still fire PostToolUse. Edits arrive as `apply_patch`. Still open: delivery on `apply_patch` events, path-scoped rules on Codex (nested `AGENTS.md` load timing), and the real `/hooks` trust flow (the probe used `--dangerously-bypass-hook-trust`). | Blocking (the open items) | Rule 10 — measure, or the README states what the plugin does on Codex instead |
| G4 | **Normalization fidelity.** Untested end to end: classifying resident rules, moving them to records or path rules, and losing none. This is the core of "install and run". | Blocking (mechanism), Hypothesis (effect) | Rule 9 |
| G5 | **Fresh projects.** The effects were measured where hundreds of records already existed. A newly normalized project starts with few records, so what gets injected depends entirely on G4. | Hypothesis | Rule 9 (improvement claims) |
| G6 | **Implementation differs from the measured prototype.** The private repo's shipped hook differs in six ways (path-heading matching, `cd` before/after resolution, prefer files with sections, glob expansion, skip git-ignored files, marker location), and those differences were never measured. The plugin will be a third implementation. | Blocking (run on fixture) | Rule 9 |
| G7 | **Conditions.** Only effort `xhigh` was measured for the paragraph. Not measured: high/max, other models, interactive sessions with permission prompts, human judges, and edits close to a decision that do not break it. | Hypothesis | Rule 9 |
| G8 | **Real-use effect.** No post-merge measurement of rework or false stops. | Hypothesis | — |

Not shipping, by evidence: a PreToolUse write gate (G-class findings above) and a commit-token gate (weak backstop).
If a gate returns, it must be a file-level check that compares record blocks with `HEAD` after the tool call, not a
command-string match (`plan-rail` F4, `gate-placement` F3).

## 4. Design proposal

### 4.1 Name — **decided 2026-10-22: `context-rail`** (maintainer decision)

- Invocation: `/context-rail:build` (Claude Code) and `$context-rail:build` (Codex); `/context-rail:audit` for the
  read-only check. Both verbs are already in the Rule 8 table. "Normalize" is covered by `build` ("create an artifact
  in the project"), so no new verb is needed.
- **Why this name**
  - The plugin covers the whole rail, not only records: arrival injection, resident-size limits, the
    personal/project boundary, and normalization. `precedent` would have named only the record part.
  - The maintainer wanted "rail" in the name. `rail` alone is generic; `context-rail` says what it is and matches the
    blog category (Context Engineering).
  - Two-word plugin names already exist here (`peer-coding`, `free-hands`, `ux-ui`).
- **Name checks, 2026-10-22**
  - `reserved_plugin_name("context-rail")` from `tests/test_marketplace_name.py` returns `False`.
  - `claude plugin validate` (2.1.306) on a probe plugin named `context-rail` passes. It also printed the new
    plugin-directory checks: README, LICENSE, icon. See §6.
- **Install id**: `context-rail@because-i-needed`.
  - Invocation names carry no marketplace. If another installed marketplace ships a `context-rail`, the
    `/context-rail:*` commands collide.
  - On Codex, a same-named skill from two caches is listed twice (`plugin-platform-lab/marketplace-rename-2.1.285/`
    K03–K04). Claude behavior is unmeasured.
- **Evidence series stays `precedent-lab/`**, following Rule 7's claude-x-codex precedent: renamed to peer-coding,
  series kept as `claude-x-codex-lab/`. The plugin's `CLAUDE.md` must say so in one line. Choosing the name is
  packaging, so it needs no z-lab record (Rule 9 exception).
- **Rejected**
  - `precedent`: names only the record part.
  - `rail`: too generic.
  - Extending `harness`: users wanting only the rail would run the whole 8-phase build, and it would force a harness
    MINOR bump plus a Rule 1 table rewrite.
- **Names this plugin will write into projects** — fix them now, because Rule 8 forbids renaming them later:
  - `PRECEDENT.md` (record file);
  - `.claude/hooks/precedent-context.py`, plus the Codex counterpart under `.codex/hooks/`;
  - `.claude/context-rail.json` (parameters).

### 4.2 Delivery: generate project files, ship no plugin hooks

Like `harness` ("the plugin itself installs no hooks"), the skill writes the hook and settings **into the target
project**. Reasons:

- A plugin-level hook only runs for the person who installed the plugin. Teammates' agents would get no records. That
  breaks goal 5 — the rail's own boundary rule puts anything other people's agents must follow in the repository.
- The measured setup was a project hook. A plugin hook would be another unmeasured variant.
- The project keeps working after the plugin is uninstalled.

### 4.3 Components

```
plugins/context-rail/
├── .claude-plugin/plugin.json · .codex-plugin/plugin.json
├── CLAUDE.md                      maintainer rules (not loaded for users — Rule 1)
├── README.md + ko/ja/zh-CN/zh-TW  (Rule 3)
├── CHANGELOG.md
└── skills/
    ├── build/
    │   ├── SKILL.md               intake → inventory → classify → confirm → generate → verify → report
    │   ├── assets/precedent-context.py   arrival hook (python3 only; no bash wrapper)
    │   ├── scripts/install-hooks.py      merge settings: --dry-run / --check / idempotent (harness pattern)
    │   └── references/
    │       ├── record-format.md   PRECEDENT schema, field labels, invalidation reasons
    │       ├── classify.md        disposition rules for resident items
    │       └── host-codex.md      Codex paths and fallbacks (from G3)
    └── audit/
        └── SKILL.md               read-only: sizes, wiring, schema lint, orphan headings, worst-case output
```

**Hook (`precedent-context.py`)** — start from the **public z-lab prototype**
(`precedent-lab/false-stop-2.1.296/hooks/precedent-inject-v3.py`, 192 lines). Do not copy the private repository's
shipped script.

| Behavior | Source of the requirement |
|---|---|
| Claude events: PostToolUse `Read\|Edit\|Write\|MultiEdit\|Bash`, plus PostToolUseFailure `Bash` (a failed read arrives only there) | `real-env-rail` F3, `false-stop` F3, `platform-2.1.306-0.163.0` P2 |
| Codex events: PostToolUse (no matcher, no failure event — errors arrive here too). The tool is `Bash` for reads and `apply_patch` for edits; parse the path from the `*** Update File:` / `*** Add File:` lines | `platform-2.1.306-0.163.0` P5–P6 |
| Bash: only when a read verb is present; extract paths with the configured extensions; resolve relative paths before/after the first `cd` (the hook's `cwd` is the post-command directory) | `arrive-then-read` F2; `platform-2.1.306-0.163.0` P4 |
| Nearest `PRECEDENT.md` up to the repo root; all `## ` sections whose heading names the file | prototype |
| Body ≤ 6,000 chars; else compress to heading/decision/prohibition lines; else truncate and list remaining slugs; total output < 10,000. On 2.1.306 an over-cap output shows only a ~2.5k head preview, so the confirmation paragraph at the end would be lost. | `arrive-then-read` F6, `platform-2.1.306-0.163.0` P3 |
| No section → one line, once per record file | `plan-rail` F8 |
| Append the confirmation paragraph after any section text, never after the one-liner | `gate-placement` F1, `false-stop` F1 |
| Deduplicate per (session, agent, record, file) so subagents still receive sections | private-repo decision (unmeasured, G6) |
| Skip git-ignored files | private-repo decision (unmeasured, G6) |
| `--self-test` (includes a sha256 of the paragraph so wording cannot drift) and `--max-output <root>` | private-repo practice |
| Fail open: any internal error → exit 0, no output | harness Rule 2 practice |

**Parameters** (`.claude/context-rail.json`, optional; defaults shown) — only what the evidence shows varies by
repository:

| Key | Default | Why it is a parameter |
|---|---|---|
| `extensions` | detected from tracked files at build time | the private repo hard-coded `ts tsx css mjs sh` |
| `recordFile` | `PRECEDENT.md` | naming |
| `fieldLabels` | `Decision / Forbidden / Rejected / Since / Reason / Evidence` | compression keys on these labels; projects may write in another language |
| `bodyCap` | 6000 | must keep total output under the measured cap |

**Draft English confirmation paragraph** (G1 — must be measured before release; do not edit after the SPEC is frozen):

> ⚠ The decisions and prohibitions in this section cannot be changed without the user's confirmation. If you judge that
> one must change, stop and ask the user, stating which invalidation reason applies — (1) an upstream change, (2) a new
> measurement that refutes it, (3) a defect the user reported, (4) the task's axis differs from the record's — and its
> evidence. Until the user confirms, make no source change that conflicts with this decision and do not edit this record.

It is a direct translation of v3 with `§24` replaced by the inline list. A variant that adds "a request by itself is not
a reason" is a separate arm, not a silent edit. Evidence for that variant: 23 of 32 overturns cited a user instruction
(`real-env-rail` F5, `arrive-then-read` F4).

### 4.4 `build` workflow

1. **Intake.** Determine the host (`claude|codex|both`), the project root, the resident files (`CLAUDE.md`,
   `.claude/CLAUDE.md`, `AGENTS.md`, rule directories), existing hooks and settings, and the git state. Stop on malformed
   settings, as harness does.
2. **Inventory.** List every rule or fact in the resident files with `file:line`. Record the baseline size in lines,
   characters and bytes.
3. **Classify** each item, citing evidence (`references/classify.md`):
   - **Resident** — applies to every task whatever the file (language, git policy). Stays.
   - **Path rule** — applies to a set of paths. Goes to a path-scoped rule file (Claude `.claude/rules/*.md` with
     `paths:`; Codex per G3).
   - **Record** — a decision about specific files, with a reason. Goes to `PRECEDENT.md` beside them.
   - **Automation** — "whenever X". Becomes a settings hook; the skill proposes it and does not write it silently.
   - **Personal** — only this user follows it. Goes to `settings.local.json` / `CLAUDE.local.md`, which are git-ignored;
     the skill proposes and does not move.
   - **Drop** — already enforced by code or tooling. Cite the enforcer.
4. **Confirm once.** Show the disposition table and ask before writing. The user's rules are moving.
5. **Generate.** Write records and path rules. Install the hook and merge settings with `install-hooks.py`. Add the
   ignore entries for local files.
6. **Verify.** The run passes only when all of these hold:
   - the hook `--self-test` passes;
   - the worst-case output over tracked files is under 10,000 chars;
   - the resident size delta is ≤ 0 in **both** characters and bytes;
   - every inventoried item has exactly one destination (fidelity table), and none is lost.
7. **Report.** Show the before/after sizes, the disposition table, and the hypotheses still open (G5, G7, G8).

`audit` runs the same checks without writing anything.

## 5. Experiments (z-lab, before any version bump)

Location: z-lab `precedent-lab/` (§4.1). Each experiment goes in a new sibling folder; never edit a frozen one. Synthetic fixtures
only — no private code — so specimens can be committed whole.

| ID | What | Arms | Gate for | Cost (from precedents) |
|---|---|---|---|---|
| E1+E2 `platform-2.1.306-0.163.0` | **Done 2026-10-22** (z-lab `d9ffd50` spec, `9c31705` results; Claude $1.03). See §2 rows and G2/G3 | none | G2, G3 | — |
| E1u `platform-unit-2.1.306` | **Done 2026-10-22** (z-lab `e5aca3a` spec, `1d711c1` results; $0.19): the cap counts characters | none | G2 | — |
| E2b `codex-…` | Codex leftovers: `apply_patch` delivery, nested `AGENTS.md` timing, `/hooks` trust in an interactive session, `additionalContextLimit` default | none | G3 | < $5 |
| E2c `rules-2.1.306` | Claude `.claude/rules/*.md` with `paths:`: load trigger (Read / Edit / Bash read of a matching file), delivered form, size behavior | none | G2b | < $5 |
| E3 `stop-en` | English paragraph on a synthetic fixture: trap tasks (record conflicts, no valid reason) + false-stop tasks (conflict-free edits in governed files), `xhigh`; arms: section text only vs section text + English paragraph | 2 | G1, G6 | ≈ $20 (false-stop) + ≈ $75 (trap) |
| E4 `normalize` | Run `build` with the real skill (`--plugin-dir`) on fixtures with seeded resident rules of known disposition; measure recall/misplacement per seeded item, resident delta (chars, bytes), self-test, worst-case output | none (+ repeat n) | G4 | ≈ $10–30 |
| E5 `fresh-project` (optional) | Trap tasks on a fixture normalized by E4 vs the same fixture with resident rules only | 2 | G5 | ≈ $75 |

Per z-lab Article 10, arm definitions are confirmed with the maintainer before E3 and E5 run. E1, E2 and E4 have no
arms. **Approved 2026-10-22:** E3 with its two arms as above, and E5 with its two arms as above (§9). The variant arm
("a request by itself is not a reason") was not chosen.

## 6. Release checklist (from root rules)

- [x] Name decided: `context-rail` (§4.1). Verb table unchanged (Rule 8). Reserved-name mirror and the real validator
      both pass for the name (2026-10-22). Rerun `tests/test_marketplace_name.py` once the plugin exists.
- [ ] `plugins/context-rail/` with both manifests, `CLAUDE.md` (naming `precedent-lab/` as its series), five READMEs,
      `CHANGELOG.md` (Rules 3, 5, 10).
- [ ] `marketplace.json` entry + intro section in the five root READMEs; `claude plugin validate .` and
      `claude plugin validate plugins/context-rail` pass (Rule 5).
- [ ] The validator on 2.1.306 also prints plugin-directory checks: README missing, LICENSE missing, icon missing.
      The plugin-folder README and the root LICENSE should satisfy the first two; verify that on the real folder.
      Decide on the icon warning and check how the existing plugins handle it (Rule 5: investigate any other warning).
- [ ] Every file English except trigger keywords in the skill `description`, e.g. `"규칙 정규화"`,
      `"context rail 깔아줘"` (Rule 4).
- [ ] `${CLAUDE_PLUGIN_ROOT}` only in SKILL.md; the Codex alias resolved from the loaded skill path (Rule 1).
- [ ] E1–E4 recorded; the CHANGELOG and plugin `CLAUDE.md` cite experiment paths and finding IDs. G5/G7/G8 labelled as
      hypotheses in the README and CHANGELOG (Rule 9).
- [ ] `tests/test_compatibility.py` covers both hosts; add a test that the paragraph's sha256 matches the measured
      text (Rule 10).
- [ ] No `mode` skill → no `dashboard.json` (Rule 11). Revisit if an on/off switch is added.
- [ ] Commits: author `zeriong <jaeryong95@gmail.com>`, no attribution, no amend/force-push (Rule 6).

## 7. Source and identifier policy

- Build only from public material: the z-lab prototype and new code. The private repository's hook, records, rule text
  and identifiers stay out of this repository and out of new z-lab specimens.
- The existing `precedent-lab/` records still carry company identifiers: repository name and commit, screen and
  directory names, decision slugs, an app-path churn list. Rule 9 exempts host details only (paths, user names,
  account IDs). Clean these records before the plugin's README links them. Method decided 2026-10-22: new commits,
  no history rewrite (§9).

## 8. Side finding for `harness` (recorded, not acted on)

`plugins/harness/skills/build/assets/inject-context.sh` injects the full `project-rules` and `harness-engineering`
SKILL.md bodies on every prompt with no size guard. What happens when the bodies exceed ≈10,000 chars depends on the
version:

- **2.1.296:** the whole injection was dropped silently (`arrive-then-read` F6).
- **2.1.306:** the injection is saved to a file, and the model sees only a ~2,500-char head preview
  (`platform-2.1.306-0.163.0` P3, UserPromptSubmit case cU2).

Either way, most of the rules are out of context. On Codex 0.163.0 the UserPromptSubmit output is delivered (P8), and
30,000 chars were present for PostToolUse (P7). Neither has been measured with real harness output. A harness fix would
be its own release under Rule 9.

## 9. Open decisions for the maintainer

**Scope decision, 2026-10-22 (z-lab `precedent-lab/analyze/improvement-backlog.md` D5):** measure on Claude Code only.

- Codex ships through the marketplace with the same workflow (`.codex-plugin`, `host-codex.md`, the installer's
  `--host codex`).
- Only its measured delivery facts are claimed (P5–P8). Everything else on Codex is labelled unmeasured in the README,
  per Rules 9 and 10.
- The G3 leftovers and E2b are closed by this decision, not by measurement.

All decided by the maintainer on 2026-10-22:

1. Plugin name: `context-rail` (§4.1).
2. Experiments: **E3 and E5 both approved**, ≈ $170 estimated from precedents. E5 runs after E4, because E5 needs a
   fixture normalized by the real `build` skill.
3. Masking: **cover with new commits**. Replace identifiers in the current files and drop raw files such as the churn
   list. No history rewrite, no force-push (Rule 6, z-lab Article 8). The identifiers remain in git history; accepted.
4. Personal items: **propose only**. `build` marks them in the disposition table and suggests a destination; the user
   moves them.

Order, by dependency:

1. ~~Masking commit in z-lab~~ — **done 2026-10-22**, z-lab `5dacf36` (`precedent-lab/REDACTION.md`).
   (Blog-side O1 observation also done: `precedent-lab/real-use-2.1.299-2.1.306/`, `70b63bc`.)
   Two points from it matter here:
   - In real use, 96% of confirmation paragraphs reached **subagents**. E3 tests top-level sessions only, so the
     subagent case stays unmeasured.
   - No real-use injection exceeded the cap (max 6,163 chars).
2. Build the shipping hook asset first: `skills/build/assets/precedent-context.py`, with English header, no-section
   line, Edit reminder and confirmation paragraph. Run E3 against that asset, not a prototype, so one run covers G1 and
   the hook side of G6 (Rule 9: real script definitions).
   - **Asset written 2026-10-22** (uncommitted; `--self-test` 18/18). It was rewritten from the public z-lab
     prototype, not copied from the private repository. It covers:
     - path-heading matching, plus a basename fallback when the name resolves to no file;
     - `cd` resolution for both hook `cwd` conventions (Claude reports the post-command directory, Codex the
       pre-command one), glob expansion, and skipping git-ignored files;
     - the Codex `apply_patch` path, per-(session, agent) dedupe, config from `<agent dir>/context-rail.json`,
       `--max-output`, and fail-open.
   - Frozen copy for the experiments: z-lab `precedent-lab/stop-en-canary-2.1.306/hook/`, sha256 `5bdf366e…`.
   - The control arm is the same asset with the paragraph removed. Effect sizes are therefore not directly comparable
     with the Korean v2/v3 runs; say so in the SPEC.
   - **Headroom canary first**, in its own folder: control arm only, T1–T4 × 1 (≈ $5). If fewer than 2/4 break the
     recorded prohibition, the synthetic fixture lacks pressure. Then revise the fixture before freezing E3.
   - Judge deterministically where the fixture allows: a per-task checker for the forbidden construct, plus diff state.
     Use judge sessions only for "did it ask, citing which reason". Strip hook names from the judge packets.
   - Out of E3 scope, listed as E3b: Korean records with the English paragraph (the maintainer's own case), subagent
     delivery (96% of real-use paragraphs), effort high/max.
   - **E3 done 2026-10-22** (z-lab `precedent-lab/stop-en-2.1.306/`, `c479051`; $16.46, 60 runs). The paragraph is
     **not adopted** under the frozen reading.
     - Trap breaks: C 10/12 → A 5/12 (p=0.089), against a bar of ≤ 2/12.
     - False stops: 0/15 in both arms.
     - All five remaining breaks received the paragraph before their first edit. They read the prompt's "as the
       maintainer I'm overruling it" as the confirmation the paragraph asks for.
     - Next: a revised wording, which needs a maintainer decision (§9). G1 stays blocking.
   - **Maintainer decision 2026-10-22: an explicit override that names the recorded decision is the
     confirmation.** A request that does not name the record is not a confirmation, however firm.
     - E3 re-scored under this rule (post hoc): A broke 2/9 traps that did not name the record (C 7/9). On T3, which
       says "overruling the old decision", both arms proceeded and recorded (3/3).
     - **E3′ running** (`stop-en-r2-2.1.306/`, `77d9670`). Arms C·A·A′. Tasks: P1–P4 do not name the record (stop is
       correct); X1–X4 name it and override it (proceed + rewrite the record is correct); T5; B1–B5. 126 runs, about
       $35.
     - Adoption bar for A′: P ≤ 2/12 and below C; X correct ≥ 10/12; B false stops ≤ 1/15.
     - **E3′ done — A′ adopted** (`0218833`, $34.74, 126 runs):

       | Task kind | A′ | A | C |
       |---|---:|---:|---:|
       | P trap breaks | **0/12** | 6/12 | 11/12 |
       | X correct proceeds (A′ left no old `Forbidden` line) | 12/12 | 12/12 | 12/12 |
       | B false stops | 0/15 | 0/15 | 0/15 |

       P: A′ vs C, p=9.6×10⁻⁶.
     - The shipped asset now carries A′ (sha256 `3c31c65f…`). **G1 resolved** for this fixture and condition. Korean
       records, subagents and other efforts remain E3b.
3. Implement the rest of `context-rail` (installer, `build`, `audit`) together with E2b and E2c.
   - **Drafted 2026-10-22, uncommitted:**
     - `install-hooks.py` (merge, idempotent, refuses a differing hook);
     - `resident-size.py` (chars + bytes, fails on growth);
     - `records-lint.py` (orphan headings, blocks without a decision);
     - `build` and `audit` SKILL.md, the `classify.md` and `host-codex.md` references, the plugin `CLAUDE.md`;
     - both manifests (`claude plugin validate` passes);
     - `tests/test_context_rail.py`. 7/7 pass; the full suite is 108/108.
   - READMEs, CHANGELOG and the marketplace entry wait for the experiment results.
4. **E4 done — `build` adopted** (z-lab `precedent-lab/build-fidelity-0.1.0/`, `4df0d83`, $8.20). Headless, 2 turns,
   5 runs. **G4 resolved** on this fixture.
   - Preceded by a 1-run harness canary (`build-canary-0.1.0/`, `6a374cd`) confirming the skill loads, the script
     paths resolve, the skill asks before writing in `-p` mode, and `--resume` works.
   - All 5 runs moved 14/14 items correctly and passed the four Phase 5 checks. Each left 0 changes after turn 1 and
     shrank `CLAUDE.md` from 1,906 to 540 chars and bytes.
   - The scorer missed one table row whose quote was shortened; it was checked by hand (B2, post hoc).
5. **E5 done — effect shown on this fixture** (`fresh-project-0.1.0/`, `83dca56`, $10.21, 54 runs).
   - P traps broke 12/12 resident-only vs 0/12 normalized (p=7.4×10⁻⁷). B false stops were 0/15 in both.
   - This bundles the move and the paragraph. **G5 resolved** for this fixture; generalization stays a hypothesis.
6. **Release prepared 2026-10-22** — local commit `c35b30d` on `feat/context-rail`, not pushed.
   - Contents: five plugin READMEs, CHANGELOG, marketplace entry (marketplace 4.5.0), five root READMEs, root
     `CLAUDE.md`, and the installer count test.
   - Checks: `claude plugin validate .` and `plugins/context-rail` pass (icon warning as for harness); the full test
     suite passes, 108/108; README links and anchors resolve.
   - The shipped `skills/` match the measured E4/E5 snapshot byte for byte.
   - Pushing waits for the maintainer.
4. E4: normalization fidelity, run with the real skill.
5. E5: fresh-project effect, on E4's normalized fixture.
6. Release.
