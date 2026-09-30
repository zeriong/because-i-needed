# Changelog

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
