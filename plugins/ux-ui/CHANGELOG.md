# Changelog

## [1.4.0] - 2026-09-30

### Changed

- Codex directors default to the newest model of the main session's family. `UX_UI_CODEX_REVIEW_MODEL` may name a family or model id and is raised to that family's newest. It is resolved before every director dispatch and retry.
- If the newest model cannot be determined, the review stops and explains why without falling back. When a sandboxed Codex main cannot refresh the catalog, it asks to rerun that resolver command outside the sandbox first. If the main cannot see its own model or family, it asks the user to set `UX_UI_CODEX_REVIEW_MODEL`.
- On Claude Code, a redirected `opus` alias stops the dispatch instead of starting a different model.

### Why

A fixed director id can become stale, and a redirected Claude alias can silently run a different reviewer. Resolving immediately before dispatch preserves the selected family and stops when that cannot be established.

Evidence: z-lab `ux-ui-lab/latest-model-1.4.0/` (R01, R02); shared resolver evidence in `plugin-platform-lab/latest-model-0.159.0/` (L01–L07), `latest-model-r2-0.159.0/` (L04r, L06r, L07r, L08), `latest-model-r3-0.159.0/` (L08i, L09), and `latest-model-r4-0.159.0/` (L02x). R01 could not start the separate `codex exec` director route from a sandboxed Codex main. R01 took the own-family branch, so the stop-and-ask branch was not exercised. Not measured: a Codex main escalating the resolver out of its sandbox (L08i shows only that the same stale home refreshed when the lab reran the resolver outside); a director actually running on the resolved Codex id; the mobile director; a Claude-host director without an override; model quality; Linux/WSL and other Claude override sources; or access-restricted and retiring models.

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
