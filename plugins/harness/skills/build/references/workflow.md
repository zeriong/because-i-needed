# Generated harness-engineering contract

This public contract is self-contained. It is based on the requirements in this
plugin, and does not require a private setup guide or research document.

Generate the project-specific `harness-engineering/SKILL.md` with these eleven phases.
Use the selected host's real paths and reviewer dispatch; retain the project's
existing commands and include only rules derived from the target repository.

0. **Intake:** resolve the requested outcome, scope and constraints; reuse already
   answered questions. A bypass-marked request skips this workflow.
1. **Reconnaissance:** read affected code, check claims against files and usages, and
   record `file:line` evidence. Recheck the affected scope after any patch.
2. **Rules:** select the applicable project-rules and convention references. Separate
   deterministic gate rules from advisory guidance; introduce no unsupported rules.
3. **Plan:** choose the smallest change satisfying the confirmed outcome and name
   the checks that establish success. Resolve material unknowns before implementation.
4. **Implement:** make the scoped change following the evidenced project conventions.
5. **Behavior checks:** run the relevant existing tests and add coverage where behavior
   changes or a regression needs it. Record failures and their evidence.
6. **Static checks:** run the lint/typecheck commands locked in intake; record the
   actual results, including any unavailable checks.
7. **Documentation:** update affected convention examples and user-facing behavior
   documentation; keep citations and keyword indexes consistent with the code.
8. **Review gate:** run `review-gate.sh --mode=full`, then obtain the two independent
   one-shot reviews specified in the generated review section below. Main synthesizes the results;
   reviewers propose changes only. Grade patches against the six quality axes. Every
   applied patch returns to Phase 1. Stop after three review/regression iterations
   with the remaining findings if the gate does not pass.
9. **Final verification:** verify the actual final diff, tests and remaining findings.
   Never call an unavailable or failed check a pass.
10. **Delivery:** report changed behavior, evidence and limitations. Commit or publish
    only when the user has authorized that action.

The prompt hook injects the generated project-rules and this generated workflow body.
For a bypass prompt (`!` prefix, `harness 빼고`, `without harness`, `skip harness`,
`no harness`), retain project-rules and replace the workflow body with a short
`BYPASS MODE` note. Bypass applies to this harness
workflow only and does not disable other project instructions or unrelated hooks.

## Review section to include in the generated skill

Resolve this section for the selected host; do not leave references to the build
plugin or its SKILL.md. Name the actual project-local gate and rule paths.

- Run the project's gate in full mode first: exit 0 passes, exit 1 is a violation,
  exit 2 is a configuration/execution error. A missing command is not a pass.
- Invoke two fresh, independent read-only reviewers with no prior review history.
  Claude uses its Opus and Sonnet panel. Codex uses architecture and gate reviewers;
  embed the `HARNESS_CODEX_ARCH_MODEL`, `HARNESS_CODEX_ARCH_EFFORT`,
  `HARNESS_CODEX_GATE_MODEL` and `HARNESS_CODEX_GATE_EFFORT`
  resolution rules from the adapter. The effort defaults to the main session's actual
  value; the model is resolved to the newest model of its family.
  Resolve defaults at each invocation of the generated skill, not at generation time.
  Do not hardcode the builder session's model or effort as a future default. If the
  current values are unavailable, require explicit role settings before dispatch.
- Resolve every reviewer's model right before its dispatch through the project-local
  resolver copy that `install-hooks.py` installed, never through the build plugin's
  install path. Embed the selected host's command with real paths, for example on Codex
  `python3 "$(git rev-parse --show-toplevel)/.codex/scripts/latest-model.py" codex "${HARNESS_CODEX_ARCH_MODEL:-<main session model id>}" --effort "<effort>"`
  (the gate reviewer uses `HARNESS_CODEX_GATE_MODEL`), passing stdout to `-m` or the native
  subagent's model field. On Claude, before each spawn run
  `python3 "$(git rev-parse --show-toplevel)/.claude/scripts/latest-model.py" claude <opus|sonnet> --project "$(git rev-parse --show-toplevel)"`.
  On exit 2 (the newest cannot be determined, or an `ANTHROPIC_DEFAULT_<FAMILY>_MODEL`
  override would run an older model) or exit 3 (effort not supported), do not dispatch, do
  not substitute another model, and do not review yourself: report the resolver's
  `latest-model:` message and stop the review. Record each reviewer's effort and the id
  that actually ran, taken from the run, never from the reviewer's own report.
  Embed the available native dispatch route or the separate `CXC_MODE=off codex exec
  --ephemeral -s read-only` recipe with explicit model, effort, cwd and prompt-file stdin.
- Give both the same complete diff, rule bodies, convention evidence, generated file
  contents and direct verification results. Add the individual role focus. Each must
  return JSON with `findings`, `fact_check_misses`, `gate_evasions`, `quality_scores`
  (srp, comment_clarity, kiss, dry, yagni, cognitive_ease; each a numeric 0–5),
  `quality_evidence` (the same six keys with evidence strings), and `patches_suggested`.
  Keep scores numeric; do not nest score/evidence objects under `quality_scores`.
  Reviewers report only; main owns edits.
- Main verifies findings, requires no fact-check misses or gate evasions and an average
  of at least 3.5 from **each** reviewer, and records its synthesis. Any applied patch
  returns to Phase 1. Three review/regression iterations is the hard limit; report
  unresolved findings instead of inventing approval.
