# Changelog

## [1.3.0] - 2026-09-29

### Added

- Codex manifest, matching MCP configuration and independent read-only art-director dispatch. Shared staged-diff gate, mobile script resolution, and diagnostics for both hosts.

- Configurable Codex director model and reasoning effort, per-server MCP setup guidance, and explicit missing-measurement reporting for both web and mobile.

### Fixed

- UI hashing no longer expands configured globs in the shell or loses Unicode/newline filenames. Resolve literal commit targets (including git -C), and store approvals at the worktree root even from nested directories. The target resolver requires Python 3.8+.

- Serialize approval metadata as JSON so quoted names and backslashes remain valid.

### Why

Codex tool discovery and reviewer dispatch differ while measurement and approval contracts must stay shared.

Evidence: z-lab `ux-ui-lab/codex-compat-1.3.0/` and `codex-compat-1.3.0-full-access/` (U01–U03). Compatibility checks cover the recorded fixtures, not
comparative model quality or every browser/device environment.
Additional setting-parity evidence: z-lab `ux-ui-lab/codex-parity-1.3.0/` (U04, U05).


Re-review evidence: z-lab `ux-ui-lab/codex-rereview-1.3.0/` (U06–U08); the source snapshot and pre-edit specification are in `plugin-platform-lab/codex-rereview-0.158.0/`.
