# Codex target and execution adapter

Invoke `$harness:build`. Apply all derivation, quality, review and regression rules in
SKILL.md. Before Phase 0, set the output target to Codex unless the user explicitly
requested `host=claude` or `host=both`. The execution host selects reviewers;
the target selects file paths. Claude generating Codex output still uses its Claude panel. Use this mapping consistently in generation, review
prompts, generated skill bodies, test commands and the final file list:

| Claude path in SKILL.md | Codex target |
|---|---|
| `.claude/settings.json` | `.codex/hooks.json` (hook declarations only) |
| `.claude/hooks/inject-context.sh` | `.codex/hooks/inject-context.sh` |
| `.claude/scripts/review-gate.sh` | `.codex/scripts/review-gate.sh` |
| `.claude/scripts/latest-model.py` | `.codex/scripts/latest-model.py` |
| `.claude/skills/project-rules/` | `.agents/skills/project-rules/` |
| `.claude/skills/harness-engineering/` | `.agents/skills/harness-engineering/` |
| `docs/conventions/` | `docs/conventions/` |

Preserve existing Claude artifacts. Update only the selected host's wiring; if both
hosts are requested, derive rules once and generate both layouts with identical rule
content. Merge the new hook into existing JSON, retaining other keys and hooks and
avoiding a duplicate invocation on reruns. Do not overwrite existing AGENTS.md or
Codex configuration. These skills and the hook do not require a new AGENTS.md.

Codex may protect `.codex/` and `.agents/` against writes in workspace-write mode.
If the tool requests approval, use the host's normal approval flow for those concrete
files. If approvals are unavailable, prepare the files in a writable staging directory
with their intended relative paths and report installation as pending. Do not change
sandbox settings or call a staged draft an installed harness.

## Tools and reviewers

- Use the available user-input tool, or ask in conversation and wait. Reuse answers
  already supplied. Track the locked intake with the host's plan tool or a local note.
- Read/Glob/Grep/Write mean the host's corresponding file/search tools.
- For each place the shared procedure calls for Opus + Sonnet, Codex uses **two fresh
  independent read-only Codex reviewers**, using the resolved settings below. Give one the rule-derivation/architecture focus and the other the gate and
  implementation focus, plus the same complete input bundle. Keep both JSON contracts,
  the 3.5 threshold, main synthesis and three-iteration cap. State the actual reviewer
  models in the report; do not call Codex reviewers Opus or Sonnet.
- If the host cannot create independent read-only subagents, use two separate
  `CXC_MODE=off codex exec --ephemeral -s read-only` calls with self-contained prompt files on stdin,
  the selected reviewer model/effort explicitly passed, and the fixture/project
  as `-C`. Wait for both calls. Do not weaken isolation or silently skip a review.

## Reviewer settings

| Role | Model variable | Effort variable | Default |
|---|---|---|---|
| Architecture / derivation | `HARNESS_CODEX_ARCH_MODEL` | `HARNESS_CODEX_ARCH_EFFORT` | newest model of the main session's family / main effort |
| Gate / implementation | `HARNESS_CODEX_GATE_MODEL` | `HARNESS_CODEX_GATE_EFFORT` | newest model of the main session's family / main effort |

A model variable names a family (such as `sol` or `luna`) or a model id, and either
is resolved to the newest listed model of that family. Resolve each role right before its
dispatch, every review iteration included:

```bash
python3 "<plugin>/scripts/latest-model.py" codex "<the role's model variable, else the main session's model id>" --effort "<the role's resolved effort>"
```

Order: when the role's model variable is set, resolve it. Otherwise resolve your own model id; a Codex
main agent may not see it (probes could not), and then your own family if you know it. If you
know neither, do not dispatch: ask the user to set the role's model variable (a family such as `sol`),
because guessing would change the role's family.

Pass stdout to `-m` (or to a native fresh read-only subagent's model field). Exit 2 (the
newest cannot be determined) and exit 3 (effort not supported) mean: do not dispatch, do
not substitute another model, and do not do the review yourself. Tell the user the
resolver's `latest-model:` message and stop that step. One exception: when the message says `catalog not refreshed` and your shell
runs sandboxed without network, first rerun that one resolver command outside the sandbox
through the host's escalation route — a sandboxed shell cannot refresh Codex's catalog —
and stop only if that is declined or fails too. Record both pairs, each with the
id that actually ran, taken from the run (the Codex run header `model:`, or a native
reviewer's receipt), never from the reviewer's own report. Never claim different model
families when both resolve to the same model. Include
relevant project instructions and mark each prompt `You are reviewing a generated
harness`; it is a delegated review, not a new orchestration task. Set `CXC_MODE=off`
for each CLI child so installing CXC alongside harness does not start a nested run.

Copy the concrete reviewer recipe, JSON shape, model/effort resolution and actual gate
path into the generated harness-engineering skill. References to this build skill's
Phase 6.2 are insufficient after installation.
The generated skill resolves defaults from its current main session on every run;
never freeze the builder's model or effort into a reusable shell default. It resolves
through the project-local resolver copy, never through `<plugin>` or an installed cache path:

```bash
python3 "$(git rev-parse --show-toplevel)/.codex/scripts/latest-model.py" codex "${HARNESS_CODEX_ARCH_MODEL:-<main session model id>}" --effort "<effort>"
```

Use `HARNESS_CODEX_GATE_MODEL` and its effort for the gate reviewer.

## Hook wiring

Merge this event into `.codex/hooks.json` (no Claude settings schema):

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "bash \"$(git rev-parse --show-toplevel)/.codex/hooks/inject-context.sh\""
      }]
    }]
  }
}
```

Use the SKILL.md `install-hooks.py` commands to copy the bundled hook and resolver
(`.codex/scripts/latest-model.py`) and merge this declaration. For both targets, validate both configurations before writing either.
It resolves the project and skill directories from its own installed location, so it
also works from a subdirectory and from another worktree.

Before declaring automatic injection active, the project and exact hook definition
must be trusted by Codex (`/hooks`) and hooks must be enabled. Do not change global
trust or bypass settings. If trust remains pending, complete file generation and
direct script verification, then report that activation step as pending. Do not report
a direct script check as proof that the runtime invoked the hook.
