# Changelog

## [0.3.0] - 2026-09-30

### Changed

- Model settings now name a family. Every worker, reviewer, rebuttal and delta re-review resolves the newest model immediately before dispatch; versioned settings are raised to that family's newest. If the newest cannot be determined, the lane stops and reports why without a fallback. A sandboxed Codex main reruns that resolver command outside the sandbox first.
- Dispatch logs record the model id from the run itself, never a worker self-report. The Claude reviewer's raw JSON is retained.

### Fixed

- Quote plugin paths in documented shell commands so install paths containing spaces remain a single argument.

### Why

Pinned model ids age out, while a silent fallback or self-reported id cannot establish which model actually ran. Quoted paths make the documented commands work from installations whose path contains spaces.

Evidence: z-lab `claude-x-codex-lab/latest-model-0.3.0/` (W01–W03) and `latest-model-0.3.0-own-id/` (W04); shared resolver evidence in `plugin-platform-lab/latest-model-0.159.0/` (L01–L07), `latest-model-r2-0.159.0/` (L04r, L06r, L07r, L08), `latest-model-r3-0.159.0/` (L08i, L09), and `latest-model-r4-0.159.0/` (L02x). Not measured: a full orchestration run; a Codex main escalating the resolver out of its sandbox (the cache stayed fresh in W01–W04; L08i shows only that the same stale home refreshed when the lab reran the resolver outside the sandbox); Linux/WSL and other Claude override sources; access-restricted or retiring models; model quality; Orca workers reaching readiness; and repeated W04 runs. The resolver's platform and override-channel limits are recorded in the shared findings.

## [0.2.0] - 2026-09-29

### Changed

- Codex packaging and explicit mode invocation policy; emit structured prompt-hook context on both hosts, audit Codex hooks and uncommitted context, and resolve scripts from the installed skill path.

- Linked-worktree mode exclusions, host-aware invocation hints, AGENTS.override.md precedence and malformed-hook audit diagnostics.

### Fixed

- Host routing consistently honors configured reviewer model/effort. Audit reports pointer/fallback mentions as checks rather than treating a filename substring as proof of equivalent instructions.

### Why

Codex invoked the plain-text hook without delivering its context; structured additionalContext reached both Codex and Claude.

Evidence: z-lab `claude-x-codex-lab/codex-compat-0.2.0/` and `codex-mode-json-0.2.0/` (C01–C04). Compatibility checks cover the recorded fixtures, not
comparative model quality or every browser/device environment.
Additional setting-parity evidence: z-lab `claude-x-codex-lab/codex-parity-0.2.0/` (C05, C06).


Re-review evidence: z-lab `claude-x-codex-lab/codex-rereview-0.2.0/` (C07, C08); the source snapshot and pre-edit specification are in `plugin-platform-lab/codex-rereview-0.158.0/`.
