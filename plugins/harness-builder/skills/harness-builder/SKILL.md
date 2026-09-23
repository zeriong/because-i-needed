---
name: harness-builder
description: Directly investigates the target project's layering / separation-of-concerns on a fact-based basis, then uses those results to build the project-rules, review-gate.sh, UserPromptSubmit hook, and harness-engineering skill from-scratch. Does NOT copy-paste an already-written harness template. Trigger keywords (Korean / English) — "harness 만들어", "build harness", "harness 셋업", "프로젝트 룰 추출", "review gate 깔아줘", "harness-builder". Runs as an 8-phase workflow; failure at any phase forces a return to Phase 1 (absolute law). Every claim in Phase 1 must include a `file:line` citation (any claim that does not pass the fact-check loop is discarded immediately).
---

# harness-builder

When invoked from within a target project, this skill **builds a harness-engineering structure from-scratch for that project**. It does not merely stamp out the skeleton from a setup-guide — it **investigates that project's layering / concerns directly to derive rules**, and completes the structure that enforces those rules as gates, all in one breath.

The outputs of this skill are the following 7:

1. `.claude/settings.json` — wires up the `UserPromptSubmit` hook
2. `.claude/hooks/inject-context.sh` — context injection script
3. `.claude/scripts/review-gate.sh` — deterministic gate (exit 0/1/2)
4. `.claude/skills/project-rules/SKILL.md` — project-specific rules derived in Phase 1~2
5. `.claude/skills/project-rules/references/<rule>.md` — details for each rule
6. `.claude/skills/harness-engineering/SKILL.md` — 11-phase workflow (separate from this skill)
7. `docs/conventions/<rule>.md` — worse/better case + keyword index (requirement #7)

---

## Absolute laws (8 rules — internalize all before starting)

1. **Understanding layering / separation of concerns comes first** — rules emerge from analysis results. Introducing rules without analysis means discard.
2. **Every rule must be gateable** — any rule that cannot be enforced with `exit 1` in a `.sh` script is downgraded to advisory (kept in `project-rules` body but not in the gate).
3. **Phase fail → brainstorm between main + Opus agent + Sonnet agent** — each agent is a one-shot fresh spawn that only proposes patches; main synthesizes all three to author the final patch.
4. **Definition of "high quality"** — separation of responsibilities / clear concise comments / KISS / DRY / YAGNI / ease of human cognition. Every patch is self-graded against these 6 before being applied.
5. **Patch applied → return to Phase 1** — an absolute law assuming the possibility of side-effects. Even one changed line requires re-verification from the beginning.
6. **All phases complete = task complete** — the moment Phase 7 passes is done. No earlier point is done.
7. **docs indexing required** — items the user mentioned only as recommendations must still be indexed in `docs/conventions/<rule>.md` as worse/better cases. Extract keywords and organize them so they can be grepped.
8. **Every claim must pass the fact-check loop** (most important) — any claim that does not pass the following protocol is discarded:

   ```
   [Claim] "This source code follows the separation-of-responsibilities principle"
     ↓
   [Self-doubt] Does it really follow it?
     ↓
   [Direct read] Verify the file directly with Read (no memory / no inference)
     ↓
   [Scope sweep] grep every source in the same scope (same directory / same layer)
     ↓
   [Side-effect probe] Investigate the impact radius via the import/usage graph
     ↓
   [SRP test] Verify that the function/module has only one reason to change
     ↓
   [Verdict] "This source code follows the separation-of-responsibilities principle — evidence: <file:line>, <file:line>"
     ↓
   Proceed to next phase
   ```

   Any claim without a file path / line citation is an **immediate discard, restart Phase 1**.

---

## Phase 0 — Intake

Collect the following 4 items in a **single `AskUserQuestion` call** at once:

1. **Package manager** — pnpm / npm / yarn / bun / other
2. **Monorepo or not** — turborepo / nx / pnpm workspace / single / other
3. **Already-installed lint/typecheck commands** — first read `package.json` scripts, enumerate them, then confirm with the user
4. **User-recommended rules** (free-text) — "things you think absolutely must be followed" — the indexing target for docs per requirement #7

After answers, lock in TodoWrite as `harness-builder intake locked`. No re-asking in later phases.

---

## Phase 1 — Layer/Concern Reconnaissance (absolute law #8 applies)

**This Phase is the most important. The facts derived here become the foundation of the entire harness.**

### Step 1.1 — Directory layer map

Enumerate the directory structure with `tree -L 3` or `find` (find must start from `.`, not `/`). For each directory, **directly read it first** and then classify:

| Layer candidate | Identification signals (examples — varies per project) |
|---|---|
| presentation | `*.tsx` + JSX + hook calls |
| business | `use-*.ts` + state machine / pure functions |
| data | `api/*`, `repository/*`, fetch calls |
| domain | type/schema/zod definitions |
| infra | config / build / CI |

**Each classification decision must come with a `file:line` citation.** For example:

```
- src/components/admin/audit-logs/page.tsx:14 → presentation (JSX root + useState)
- src/hooks/use-audit-logs.ts:1 → business (pure hook, no JSX, delegates fetch)
- src/api/audit-logs.ts:8 → data (fetch + zod parse)
```

### Step 1.2 — Concern separation audit

Run the fact-check loop within each layer. Example:

```
[Claim] components/admin/audit-logs/page.tsx has only presentation
  ↓
[Direct read] Verify the entire page.tsx with the Read tool
  ↓
[Scope sweep] grep "useState|useEffect|fetch" src/components/admin/audit-logs/
  ↓
[Side-effect probe] grep -r "audit-logs" src/  # where is it imported?
  ↓
[SRP test] Does page.tsx also perform data fetching? Does it hold transform logic?
  ↓
[Verdict 1] page.tsx:24-31 performs a fetch directly → presentation + data mixed (violation)
[Verdict 2] use-audit-logs.ts:14 holds sort logic → business-correct
```

**Verdicts are always written together with `file:line` citations.**

### Step 1.3 — Fact-check loop pass/fail

Only loop-passing claims accumulate in `phase1-findings.md` (a temporary file). Failed claims are discarded and re-investigated. The same protocol applies to every layer.

### Step 1.4 — Output

```markdown
## Phase 1 — Layer/Concern Reconnaissance (verdicts)

### Identified layers
- presentation: src/components/**, src/app/**
- business: src/hooks/use-*.ts
- data: src/api/**, src/lib/db.ts:1-40
- domain: src/types/**, src/schemas/**

### Violations found (fact-cited)
- src/components/admin/audit-logs/page.tsx:24-31 — presentation + data mixed
- src/lib/utils.ts:88-120 — business + data mixed (calls fetch directly)

### Concerns confirmed clean (fact-cited)
- src/hooks/use-audit-logs.ts — business-only (sort logic only, no JSX / no fetch)
```

---

## Phase 2 — Convention Extraction

Based on the verdicts from Phase 1, derive the **rules that project actually needs**. Distinguish between **items already well-observed** and **items where violations were found**:

| Rule kind | Derivation trigger | Gateable? |
|---|---|---|
| layer separation | Layer mixing found in Phase 1 | possible with grep (e.g. forbid fetch in presentation) |
| naming convention | If the majority of repo files are kebab-case, codify it | regex grep |
| file length cap | Set cap based on average line count | wc -l |
| comment style | Sample the existing comment pattern | heuristic grep |
| test colocation | `__tests__/` vs `*.test.ts` pattern | find |

Derivation criteria:
- **User-recommended rules from Phase 0 are always included** (as advisory if not gateable)
- **Rules with zero Phase 1 violations and no user mention are forbidden from being introduced** (YAGNI)
- **Gateable rules go into the gate; advisory-only rules stay only in the project-rules body**

The output is `rules.json` (temporary) — each rule has `{id, title, gate: bool, severity: P0|P1|P2|P3|P4, source: "user-recommended" | "phase1-violation" | "phase1-pattern"}`.

---

## Phase 3 — docs/conventions/ worse/better case indexing (requirement #7)

Create `docs/conventions/<rule-id>.md` for each rule. **Always cite real code from the repo** (no fictional examples).

Template:

```markdown
# <rule title>

## Index keywords
<5–10 keywords that can be found via grep — identifiers/patterns that appear in rule-violating / rule-following code>

## Worse case (real repo citation)
`src/components/admin/audit-logs/page.tsx:24-31` — direct fetch in presentation
```tsx
<cited code verbatim>
```
Problem: <1–2 lines explaining why it is a problem>

## Better case (real repo citation, or code after the Phase 2 recommended fix)
`src/hooks/use-audit-logs.ts:14-28` — business hook delegates fetch
```tsx
<cited code verbatim>
```
Reason: <1–2 lines on why it is good>

## Gate hook
- Inspected via review-gate.sh `--rule=<rule-id>`
- Inspection regex / command: `<actual command>`
- P0~P4 classification on detection: <severity>
```

**No fictional examples.** Only `file:line` citations from Phase 1 may be used. If a better case does not exist in the repo, write out the post-recommended-fix code from Phase 2 explicitly ("expected form after improvement").

---

## Phase 4 — Generate gate script (`.claude/scripts/review-gate.sh`)

Use the skeleton from setup-guide §7 as the base, but **only include rules classified as gate=true in Phase 2**. Add one inspection block per rule.

Skeleton:

```bash
#!/usr/bin/env bash
# Generated by harness-builder — Phase 4 output
# Rules covered: <rule-id-1>, <rule-id-2>, ...
set -euo pipefail
IFS=$'\n\t'

MODE="full"
BASE_REF="${BASE_REF:-origin/main}"

for arg in "$@"; do
  case "$arg" in
    --mode=*) MODE="${arg#--mode=}" ;;
    --base=*) BASE_REF="${arg#--base=}" ;;
    --rule=*) RULE="${arg#--rule=}" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) printf 'unknown arg: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo 'not a git tree' >&2; exit 2; }
cd "$REPO"
errors=(); warnings=()

# Changed files (diff-scoped per setup-guide §7)
git fetch --quiet origin 2>/dev/null || warnings+=("git fetch origin failed")
changed=""
if git rev-parse --verify --quiet "$BASE_REF" >/dev/null; then
  changed=$(git diff --name-only "${BASE_REF}...HEAD" 2>/dev/null || true)
fi
[[ -z "$changed" ]] && changed=$(git diff --name-only HEAD 2>/dev/null || true)
[[ -z "$changed" ]] && changed=$(git diff --name-only 2>/dev/null || true)

printf '=== Changed files ===\n%s\n\n' "${changed:-(none)}"

# === Rule checks (one block per Phase 2 rule with gate=true) ===
# Example: layer-separation
printf '=== Rule: layer-separation ===\n'
if echo "$changed" | grep -qE '^src/components/.*\.tsx$'; then
  for f in $(echo "$changed" | grep -E '^src/components/.*\.tsx$'); do
    if grep -nE 'fetch\(|axios\.' "$f" >/dev/null 2>&1; then
      errors+=("layer-separation P1: direct fetch in presentation — $f")
    fi
  done
fi

# Example: file-length-cap
printf '=== Rule: file-length-cap ===\n'
for f in $(echo "$changed" | grep -E '\.(tsx?|jsx?)$' || true); do
  [[ -f "$f" ]] || continue
  lines=$(sed '/^\s*$/d; /^\s*\/\//d' "$f" | wc -l | tr -d ' ')
  if (( lines > 270 )); then
    errors+=("file-length-cap P2: $f $lines lines (cap 270)")
  fi
done

# CI checks (commands captured in Phase 0 intake)
if [[ "$MODE" != "refs-only" ]]; then
  printf '=== CI checks ===\n'
  for check in lint typecheck; do
    if pnpm -s "$check" >"/tmp/review-gate-$check.log" 2>&1; then
      printf -- '- %-10s PASS\n' "$check:"
    else
      printf -- '- %-10s FAIL (log: /tmp/review-gate-%s.log)\n' "$check:" "$check"
      errors+=("$check failed")
    fi
  done
fi

printf '=== Result ===\n'
for w in "${warnings[@]:-}"; do printf 'WARN: %s\n' "$w"; done
if (( ${#errors[@]} > 0 )); then
  for e in "${errors[@]}"; do printf 'FAIL: %s\n' "$e"; done
  printf 'Result: FAIL\n'
  exit 1
fi
printf 'Result: OK\n'
exit 0
```

Don't forget `chmod +x .claude/scripts/review-gate.sh`.

---

## Phase 5 — Hook wiring

`.claude/settings.json`:

```jsonc
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/inject-context.sh\"" }
        ]
      }
    ]
  }
}
```

`.claude/hooks/inject-context.sh` — use setup-guide §4 as-is (inject project-rules + harness-engineering body, support `!` or Korean/English bypass regex). Apply `chmod +x`.

---

## Phase 6 — Author skill bodies

### 6.1 `.claude/skills/project-rules/SKILL.md`

Unfold the Phase 2 `rules.json` as markdown:

```markdown
---
name: project-rules
description: <repo-name>'s coding / structural rules (derived via Phase 1 fact-check). Auto-injected into every task.
---

# Project Rules

## §1 <rule-1 title>
- Severity: P<n>
- Gate: <yes / advisory>
- Reference: docs/conventions/<rule-1>.md

<rule body — 3–6 lines>

## §2 ...
```

Each § maps 1:1 to `docs/conventions/<rule>.md`. Placing per-rule detail in a references directory is also acceptable.

### 6.2 `.claude/skills/harness-engineering/SKILL.md`

Keep the 11-phase workflow from setup-guide §5 as-is. However, **the Phase 8 Review Gate model ratio is reduced per user requirement #3 to "Opus 1 + Sonnet 1, one-shot fresh spawn, main synthesizes"** (the setup-guide's 2 Opus + 3 Sonnet 5-agent panel is judged over-engineering and not adopted).

Phase 8 step machine:

```
1. review-gate.sh --mode=full  → if exit 0, go to Step 2
2. Fresh-spawn 1 Opus + 1 Sonnet (2 parallel Agent tool_use calls in a single message)
   - input: git diff + project-rules body + detected violations (if any)
   - output (strict JSON): { findings: [{severity, file, line, issue, suggested_fix}] }
3. Main synthesizes both results + review-gate.sh output and authors the final patch
   - Self-grade against the 6 "high quality" criteria (SRP / comments / KISS / DRY / YAGNI / cognitive-ease)
4. Apply patch → return to Phase 1 (absolute law)
5. Restart from Step 1. Iteration cap = 3.
```

---

## Phase 7 — Self-Verification

Verify that the generated harness actually works:

```bash
# 1. Does the hook inject the body?
bash .claude/hooks/inject-context.sh <<< '{"prompt":"sanity"}' \
  | jq -r '.hookSpecificOutput.additionalContext' \
  | grep -E "^## §[0-9]+" \
  || { echo "FAIL: project-rules not injected"; exit 1; }

# 2. Does the bypass work?
bash .claude/hooks/inject-context.sh <<< '{"prompt":"!skip"}' \
  | jq -r '.hookSpecificOutput.additionalContext' \
  | grep -c "BYPASS MODE" \
  || { echo "FAIL: bypass not wired"; exit 1; }

# 3. Does the gate script return exit 0/1 accurately?
.claude/scripts/review-gate.sh --mode=refs-only \
  || { echo "INFO: gate returned non-zero on current state (needs review)"; }

# 4. Does the gate return exit 1 against a deliberately-violating sample diff?
#    (Pick one of the rules derived in Phase 2, author a violating case → run the gate)
```

All 3 verifications must pass for the task to be done. If any one fails, **return to Phase 1**.

---

## Phase 8 — Review Gate (requirement #3)

Even after the Phase 7 above passes once, **fire one more time before declaring final done**.

1. **Fresh-spawn 1 Opus + 1 Sonnet** (2 parallel Agent tool_use calls in a single message)
   - subagent_type: `general-purpose`
   - model: `opus` / `sonnet`
   - description: "one-shot harness review (Opus|Sonnet)"
   - prompt: the input bundle below

2. **Input bundle (identical for both agents)**:

   ```
   You are reviewing a generated Claude Code harness for repo <name>.

   ARTIFACT:
   - .claude/settings.json
   - .claude/hooks/inject-context.sh
   - .claude/scripts/review-gate.sh
   - .claude/skills/project-rules/SKILL.md
   - .claude/skills/harness-engineering/SKILL.md
   - docs/conventions/*.md
   <attach the content of each file inline>

   TASK:
   1. Verify whether rule derivation (Phase 1~2) is actually fact-based — are there rules missing file:line citations?
   2. Does the gate script really block those rules? Are there bypassable patterns?
   3. Score 0–5 + evidence against the 6 "high quality" criteria (separation-of-responsibility / comments / KISS / DRY / YAGNI / cognitive-ease)

   OUTPUT (strict JSON, no prose):
   {
     "fact_check_misses": [{"rule": "<id>", "missing_citation": "<what>"}],
     "gate_evasions": [{"rule": "<id>", "evasion": "<how to bypass the regex>"}],
     "quality_scores": {
       "srp": 0-5, "comment_clarity": 0-5, "kiss": 0-5,
       "dry": 0-5, "yagni": 0-5, "cognitive_ease": 0-5
     },
     "patches_suggested": [
       {"file": "<path>", "change": "<concrete diff or instruction>", "why": "<one line>"}
     ]
   }

   You have NO memory of prior reviewers. Treat this as first contact.
   ```

3. **Main synthesis** — receive the two JSONs and process in the following order:
   - If `fact_check_misses` is non-empty → **return to Phase 1** (absolute law triggers)
   - If `gate_evasions` is non-empty → return to Phase 4 (reinforce gate)
   - If the average of `quality_scores` < 3.5 → return to Phase 6 for low-scoring items
   - `patches_suggested` is self-graded by main against the 6 criteria, then accept / reject
   - Any patch applied (even one line) → **return to Phase 1**

4. **Regression cap = 3**. If all conditions are not passed within 3 iterations, emit a truthful failure report to the user (same format as setup-guide §8 hard-stop). Form:

   ```
   ## harness-builder — Phase 8 hard stop
   ### Iterations attempted: 3
   ### Remaining issues
   - <issue 1>: <evidence file:line>
   - <issue 2>: ...
   ### What was tried (verbatim)
   <per-iteration patch summary + result>
   ### Recommended next moves
   <2–3 concrete next actions — no "probably">
   ```

---

## Termination conditions

Declare done only when **all** of the following are satisfied:

- [ ] Phases 0~7 passed sequentially
- [ ] Phase 8's one-shot Opus + Sonnet review: fact_check_misses 0 / gate_evasions 0 / quality average ≥ 3.5
- [ ] Regression cap not exhausted

On done declaration, output to the user:

```
## harness-builder complete
### Generated files
- .claude/settings.json
- .claude/hooks/inject-context.sh
- .claude/scripts/review-gate.sh
- .claude/skills/project-rules/SKILL.md (+ references/)
- .claude/skills/harness-engineering/SKILL.md
- docs/conventions/<rule-1>.md ~ <rule-n>.md

### Derived rules (gate / advisory split)
- gate: <rule-id-1>, <rule-id-2>, ...
- advisory: <rule-id-3>, ...

### Phase 8 review result summary
- fact_check_misses: 0
- gate_evasions: 0
- quality avg: <n.n>

### Next steps
- Entering the first prompt auto-fires the hook
- Run the gate manually: `.claude/scripts/review-gate.sh --mode=full`
- To bypass the harness, prefix the prompt with `!` or "harness 빼고" (Korean: skip the harness)
```

---

## Notes for Claude when this skill loads

- **This skill does not finish in one turn.** Honestly running Phases 1~8 will take multiple turns. If cross-turn progress is needed, wrapping with `/loop` is fine, but **it must also be possible to progress phase-by-phase within a single conversation without `/loop`**.
- **The Phase 1 fact-check loop must never be done in shorthand.** No `cat | head` inference; view the actual file with the Read tool and specify `file:line`.
- **YAGNI absolutely observed.** Rules with 0 violations in Phase 1 + 0 user mention are not introduced. If 5 rules are enough, stop at 5.
- **The regression cap of 3 is never broken.** Prevents infinite oscillation (research-foundation §2 principle 5). If convergence is not achieved within 3 iterations, report failure to the user.
- **The one-shot Opus + Sonnet review is a fresh spawn.** No `agentId` / `sessionId` capture. No `SendMessage`. No round 2 (user requirement #3 is "one-shot").
- **All artifacts are written to the target project root.** This skill itself (harness-builder) is used as read-only.
