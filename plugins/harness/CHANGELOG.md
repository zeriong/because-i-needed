# Changelog

## [1.3.0] - 2026-09-30

### Changed

- Codex architecture and gate reviewers default to the newest model of the main session's family. A set `HARNESS_CODEX_*_MODEL` value may name a family or model id and is raised to that family's newest (M02). The installer copies the resolver to `.<host>/scripts/latest-model.py`; the generated harness-engineering skill resolves through that project-local copy at each invocation.
- If the newest model cannot be determined, the review stops and explains why without falling back. When a sandboxed Codex main cannot refresh the catalog, it asks to rerun that resolver command outside the sandbox first. If the main cannot see its own model or family, it asks the user to set the reviewer variable.
- On Claude Code, both the builder's own Opus/Sonnet panel and the generated skill's panel check for a redirected `ANTHROPIC_DEFAULT_<FAMILY>_MODEL` alias before dispatch.

### Why

Generated projects must resolve reviewer models from their own installed files at run time, and stale or redirected model settings must not silently select a different reviewer.

Evidence: z-lab `harness-lab/latest-model-1.3.0/` (M01, M02); shared resolver evidence in `plugin-platform-lab/latest-model-0.159.0/` (L01–L07), `latest-model-r2-0.159.0/` (L04r, L06r, L07r, L08), `latest-model-r3-0.159.0/` (L08i, L09), and `latest-model-r4-0.159.0/` (L02x). M02 measured `HARNESS_CODEX_ARCH_MODEL=gpt-6-sol` resolving to `gpt-6.1-sol`. Not measured: the stop-and-ask branch (M01/M02 did not exercise it); a Codex main escalating the resolver out of its sandbox (L08i shows only that the same stale home refreshed when the lab reran the resolver outside); a full build copying the recipe into the generated skill; the builder's own Claude Opus/Sonnet panel and alias-override check; the generated Claude panel and its alias-override check (the alias-override stop was measured only inside ux-ui's wired skill in R02); model quality, Linux/WSL and other Claude override sources, or access-restricted and retiring models.

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
