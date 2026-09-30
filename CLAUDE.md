# because-i-needed — repository rules

This repository is a Claude Code and Codex marketplace holding three plugins (harness, ux-ui, claude-x-codex).
**Shared rules live in this file**; **per-plugin rules live in `plugins/<name>/CLAUDE.md`** (loaded automatically when you read that plugin's files).
A plugin file does not repeat this file — it holds only what applies to that plugin. If the two conflict, fix both.

Every rule carries its reason. A rule whose reason is forgotten decays into ritual.

---

## Rule 1 — Only `plugins/<name>/` reaches an installed client

- On install, the cache `~/.claude/plugins/cache/because-i-needed/<plugin>/<version>/` receives **only the plugin folder**.
  The root READMEs and this file never reach users. Anything a user must read goes in the plugin README.
- `plugins/<name>/CLAUDE.md` ships in the package but is **not loaded into user sessions**
  (Claude Code reads only the working-directory hierarchy and the user's global CLAUDE.md). These files are for maintainers.
  Instructions meant for installed users go into skills, agents, or hooks.
- On Claude Code, `${CLAUDE_PLUGIN_ROOT}` written in **SKILL.md** (braced) is
  replaced with the install path when the skill loads. Shared skills define `<plugin>` there; on Codex,
  resolve that alias from the real loaded skill directory (two parents up), never from the target cwd. A reference file the skill reads later keeps the variable literal,
  and the shell does not set it, so a command there runs as `/scripts/…` and fails. Put script commands in SKILL.md; a
  reference points to them or uses a name SKILL.md defines — both ran the script 3/3 (z-lab `plugin-platform-lab/`,
  V01–V06).

**Why:** in the plan-smith 1.1.3 check the cache held zero copies of the root CHANGELOG. On 2026-09-23 the installed copy of the
enabled humanize-korean plugin contained a CLAUDE.md that was not loaded into the session context, and `claude plugin validate`
reports the same fact with the warning "CLAUDE.md at the plugin root is not loaded as project context".

## Rule 2 — A behavior change bumps the version, and every version string moves together

- Plugins are served from a **version-keyed cache**. Editing the source alone never reaches installed clients, while each client
  still reports itself as up to date. Any change that affects behavior must bump the version.
  A delivery-only release — a version bump with no content change — is legitimate.
- One plugin's version string lives in **13 places**:

  | File | Location |
  |---|---|
  | `plugins/<name>/.claude-plugin/plugin.json` | `"version"` |
  | `plugins/<name>/.codex-plugin/plugin.json` | `"version"` |
  | `.claude-plugin/marketplace.json` | that plugin entry's `"version"` (the top-level `metadata.version` is the marketplace's own version — separate) |
  | `plugins/<name>/README*.md` (5) | shields.io version badge at the top |
  | `README*.md` (5, root) | `` `vX.Y.Z` `` next to the plugin heading |

- Check: `grep -rn --include='*.md' --include='*.json' -F '<old-version>' . | grep -v CHANGELOG` must show no line for that plugin.
  When another plugin or the marketplace uses the same version string
  (e.g. harness `1.1.0` is also ux-ui's previous version), tell the matching lines apart by eye.
- Version strings, the CHANGELOG (plugins that have one) and README changes go in **one commit**. Do not split them.
- SemVer: **MAJOR** existing usage breaks / **MINOR** behavior added or changed / **PATCH** docs, typos, delivery only (no behavior change).
  Each plugin's CLAUDE.md gives its concrete criteria.

**Why:** plan-smith 1.1.1 exists for this reason alone — a rule was written into the source, and the installed copy kept serving 1.1.0.

## Rule 3 — READMEs: five languages, same commit

- Every README is five files: `README.md` (English, **the source**), `README.ko.md`, `README.ja.md`, `README.zh-CN.md`, `README.zh-TW.md`.
  Translations follow the English source.
- A README change edits **all five in the same commit**. A new plugin has all five from its first commit.
- When a concept or behavior users must understand changes, update that plugin's five READMEs; when a plugin's one-line summary
  changes, update the five root READMEs too. Internal refactors and typos don't count.
- Links: relative paths in a plugin README are relative to the plugin folder; root README links to a plugin point at `plugins/<name>`
  (the folder tree). In-page anchors in a translation are **the GitHub slug of the translated heading**. After editing READMEs,
  confirm every relative link and anchor resolves.
- Count numbers before writing them.

**Why:** maintainer decision, 2026-09-23 (published in the root README "Language policy"). READMEs drifted from reality in the
original repositories — the ux-ui-builder root README carried a 1.0.0 badge while omitting 1.1.0's mobile features.

## Rule 4 — READMEs are the only localized files; everything else is English

- **Localized:** the READMEs, and only the READMEs (five languages, Rule 3).
- **English:** every other file — `CLAUDE.md` (this file and each plugin's), `SKILL.md`, `references/*.md`, `agents/*.md`,
  messages emitted by hooks and scripts, script comments, manifests, `CHANGELOG.md`.
- **Exception — literals that must match what a user types** stay in the user's language: trigger keywords in a skill
  `description` (`"harness 만들어"`), bypass phrases (`"harness 빼고"`). Add an English gloss where the meaning is not obvious.
- This rule governs files in the repository, not the language of a conversation with the maintainer.

**Why:** maintainer decision, 2026-09-28. Until then the CLAUDE.md files were Korean while everything they govern was English.
Writing the rule down makes every future edit — a new rule, skill, or changelog entry — start in English, with no translation
step between a rule and the files it describes.

## Rule 5 — Validate manifests with the validator

- After editing `.claude-plugin/marketplace.json` or a `plugin.json`,
  `claude plugin validate .` and `claude plugin validate plugins/<name>` must pass.
  The plugin warning `CLAUDE.md at the plugin root is not loaded as project context` is **expected** —
  that file is for maintainers and is correctly not loaded (Rule 1). Investigate any other warning.
- Adding a plugin = `plugins/<name>/` (manifest, five READMEs, CLAUDE.md) + a `marketplace.json` entry + an intro section in the five root READMEs
  + its series in z-lab (Rule 9). Name it by Rule 8. The root `install.sh` reads the plugin list from `marketplace.json`, so it needs no change.

## Rule 6 — Commits

- Conventional Commits. Header ≤ 50 characters, body lines ≤ 72 characters, and the body says *why*, not *what*.
- Author and committer are always `zeriong <jaeryong95@gmail.com>`.
  **No Claude attribution** — no `Co-Authored-By`, no "Generated with", no robot emoji.
- No `--no-verify`, no amend, no force-push.

**Why:** Article 5 of the plan-smith release statute and the zeriong-commit skill's absolute rules, widened to the whole repository.

## Rule 7 — History lives in two places

This repository's history starts at `3714dd5` (2026-09-23, the commit that brought in the three plugins). Earlier history —
plan-smith ≤ 1.4.2, harness-builder 1.0.0, ux-ui-builder ≤ 1.1.0 — lives in the original repositories
`zeriong/plan-smith`, `zeriong/harness-builder`, `zeriong/ux-ui-builder`.
Checking a version boundary in git from this repository alone makes everything before that look empty.
In the naming release (plan-smith 1.5.0, harness 1.1.0, ux-ui 1.2.0), `plugins/harness-builder` moved to `plugins/harness` and
`plugins/ux-ui-builder` to `plugins/ux-ui`, and the skill folders moved to `build`, `build-mobile`, and `forge`. Read earlier file history with `git log --follow -- <current path>`.
plan-smith was retired on 2026-09-30 (marketplace 2.0.0): z-lab `plan-smith-lab/real-skill-tco-1.6.0/` measured the shipped
pipeline as a net cost where the same model plans and implements, and `plan-smith-lab/analyze/` records the decision. Its
last source is `plugins/plan-smith/` at `82d8018` and the original repository `zeriong/plan-smith`.

## Rule 8 — Naming: `/<plugin>:<skill>` reads "subject : action"

Plugin skills are invoked as `/<plugin>:<skill>` in Claude Code and `$<plugin>:<skill>` in Codex, and the plugin is the unit of installation. Name both halves this way.

- **Plugin = subject** — what it works on (`harness`, `ux-ui`). An established brand name may stay (as `plan-smith` did until it was retired).
- **Skill = verb** — what it does, chosen only from the shared vocabulary below. A verb means the same thing in every plugin.
- **No repetition** — the same word never appears on both sides of the colon.
- **One word per side** where possible. A variant goes after the verb (`build-mobile`).
- **Group by verb, not by container.** Plugins stay separate so users install only what they need and one plugin's hooks or
  MCP servers never ride along with another. The shared verbs are what make plugins of the same nature recognizable.

| Verb | Meaning |
|---|---|
| `build` | Create an artifact in the project (a harness, a UI) |
| `forge` | Distill conversation context into a document (a plan) |
| `run` | Execute a task |
| `mode` | Switch a behavior on or off |
| `audit` | Inspect, read-only |
| `review` | Evaluate a result |

- Add a verb to this table before using it. Agent names are outside this rule.
- The invocation name comes from the skill's **folder name**; the frontmatter `name` did not change it (checked on Claude Code 2.1.283).
  Keep the two identical.
- Never rename what a plugin has already written into users' projects (harness's generated `project-rules`, `review-gate.sh`,
  `harness-engineering`; ux-ui's `.ux-ui/`). If one must change, add a fallback that still reads the old name.
- The plugin name is an ingredient of other identifiers — MCP tool names `mcp__plugin_<plugin>_<server-key>` (ux-ui Rule 1),
  the install cache path, `enabledPlugins` keys. Renaming a plugin means fixing those references in the same commit.

**Why:** before the naming release each plugin and its skill shared one name, so commands repeated themselves across the colon
(`/harness-builder:harness-builder`); the maintainer decided the rename on 2026-09-28. A rename breaks existing installs — after a
marketplace update the client keeps the old registration name, and a renamed plugin shows `failed to load` (2.1.283, checked with a
directory source). So name things right the first time. The naming release shipped as MINOR only because the marketplace had no
users yet; once it does, a rename is MAJOR (Rule 2).

## Rule 9 — Skills are built and released from measurements in z-lab

Creating a skill, or changing what a skill, agent, hook or script does, starts and ends in the lab repository `z-lab`
(`github.com/zeriong/z-lab`). A change ships only with the experiment record that measured it.

- **Find the lab first.** It is normally this repository's sibling, `../z-lab`. If it isn't there, look for a local
  directory named `z-lab` whose root holds a `CLAUDE.md` and whose `origin` is `zeriong/z-lab`; if none exists, ask the
  maintainer before going further — don't build the change without it, and don't release it.
- **Follow the lab's own rules.** `z-lab/CLAUDE.md` governs the experiment work and wins over this file inside the lab:
  one series per plugin (`<plugin>-lab/`, e.g. `plan-smith-lab/`, `claude-x-codex-lab/`), a `SPEC.md` frozen before
  the run, untouched specimens, a generated `METRICS.md`, a `FINDINGS.md` that separates what was measured from what was
  not, state-aware runners, and an `analyze/` backlog that links every change to its evidence. The lab is public, but
  host details (local paths, user names, account IDs) may stay in what it stores — redacting them is not required
  (maintainer decision, 2026-09-30: the git history already carries such details).
- **What to measure before building or releasing:**
  - every CLI, platform or tool behavior the skill relies on — run it, don't recall it;
  - the new or changed mechanism itself, run with the real agent, skill or script definitions (e.g. `--plugin-dir`,
    `--agent`), against inputs from the lab's corpora where they exist;
  - any claim that the change *improves* an outcome — measured, or labelled a hypothesis in the README and CHANGELOG.
- **Release from the numbers.** The version bump (Rule 2) comes after the experiment. The CHANGELOG entry and the
  plugin's `CLAUDE.md` name the experiment path and the finding IDs they rest on. If the measurement contradicts the
  change, fix or drop the change — and re-measure in a new sibling experiment, never by editing the frozen one.
- **Decisions are recorded too.** A maintainer decision that isn't a measurement (a model choice, a threshold) goes into
  the series' `analyze/` backlog with its reason, marked as a decision.
- Documentation-only changes (PATCH) need no new experiment, but every fact they state must already have evidence.
- **Packaging changes are never measured.** Renaming the marketplace or an install id, version bumps, manifest
  metadata, install commands and README wording need no experiment and no z-lab record. When existing installs
  must move, the documented answer is to uninstall and reinstall.

**Why:** in the claude-x-codex 0.1.0 work (2026-09-28) several CLI assumptions in the first draft were wrong and were
found only by running the CLIs, and the first fix for its reviewer made it about nine times more expensive — caught only
because the lab measured it. A skill written from recall ships what the author believed, not what the tools do.
The packaging exception is a maintainer decision (2026-09-30): the marketplace rename `bin` → `because-i-needed` grew
into three experiments whose answer was "uninstall and reinstall", which the maintainer already knew.


## Rule 10 — Shared workflows, explicit host wiring

- Each plugin ships a `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. They refer to
  the same skill/resource tree. The root Claude marketplace remains the single catalog; Codex
  0.158.0 reads it directly (z-lab `plugin-platform-lab/codex-compat-0.158.0/`, P01).
- Claude-specific frontmatter (`argument-hint`, `disable-model-invocation`) remains where required
  for existing behavior. Quote description strings as valid YAML. Codex's mode policy also lives
  in `agents/openai.yaml`; the runtime loader is authoritative for dual-host discovery.
- Hooks use the existing `hooks/hooks.json` defaults on Codex. A manifest or script check does not
  establish runtime activation: Codex requires hook trust, and the runtime must execute the hook.
- The installer defaults to Claude. Explicit `--host codex` uses Codex plugin commands and rejects
  unsupported installation scopes. Keep both vendor routes covered by `tests/test_compatibility.py`.
- Changes to host wiring must retain the plugin's core contracts: isolated plan authors, measured
  UI reviews, staged-diff approvals, evidence-derived harness rules and bounded review loops.

**Why:** loading a skill does not translate its tool names, agent dispatch or generated paths.
Host adapters make those choices explicit while keeping each workflow in one shared source.
