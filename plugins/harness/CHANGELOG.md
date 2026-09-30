# Changelog

## [1.2.0] - 2026-09-29

### Added

- Codex target paths and independent reviewers; a bundled public eleven-phase workflow and portable injection asset. Preserve existing Claude files, merge host hooks, and report protected-directory installation separately from generated drafts.

- Configurable architecture/gate reviewer settings and a self-contained generated review protocol. A bundled hook installer preserves unrelated settings, rejects malformed configs, and is idempotent. Injection no longer needs shell heredoc temporary files.

### Fixed

- Bypass retains project-rules while omitting workflow enforcement, as promised by the existing READMEs. The new bundled asset had omitted both. Measured on both host layouts in z-lab `harness-lab/codex-bypass-1.2.0/` (H07).

- Reusable workflows resolve model/effort defaults per invocation and use numeric quality scores with separate evidence, avoiding builder-default persistence and incompatible nested score objects.

### Why

A Codex host needs its own hook/skill locations, and installed clients cannot read private setup guides.

Evidence: z-lab `harness-lab/codex-compat-1.2.0/` and `codex-compat-1.2.0-full-access/` (H01–H03). Compatibility checks cover the recorded fixtures, not
comparative model quality or every browser/device environment.
Additional setting-parity evidence: z-lab `harness-lab/codex-parity-1.2.0/` (H04–H06).


Re-review evidence: z-lab `harness-lab/codex-rereview-1.2.0/` (H08); the source snapshot and pre-edit specification are in `plugin-platform-lab/codex-rereview-0.158.0/`.
