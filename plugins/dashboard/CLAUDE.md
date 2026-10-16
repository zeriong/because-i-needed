# dashboard — development rules

Every shared rule in the root `CLAUDE.md` applies, Rule 11 above all: this plugin is where every declared mode shows.

Contents: the `audit` skill (Codex policy in `skills/audit/agents/openai.yaml`); a Claude Code hooks module
(`hooks/hooks.json` → `hooks/register.tsx`, its state contract `types/index.d.ts`); an empty Codex hooks file
(`hooks/codex.json`, named by `.codex-plugin/plugin.json`); `scripts/dashboard.py`, the one collector both hosts use.

## Invariants

- The dashboard knows no plugin by name. It reads `dashboard.json` from every enabled because-i-needed plugin and runs
  the declared status commands (root Rule 11). **Why (maintainer decision, 2026-10-14):** a mode added later must appear
  without a dashboard release.
- Plugins are found where each host records them: Claude Code's `installed_plugins.json` filtered by the enabled list
  the module passes from `$.settings.read()` (the settings files when run from the skill), Codex's `config.toml` and the
  newest cached version; `BECAUSE_I_NEEDED_PLUGIN_DIRS` adds folders loaded with `--plugin-dir`. **Why (z-lab
  `plugin-platform-lab/mod-dual-host-2.1.299` M06):** the module reads the enabled list but no other plugin's folder.
- Layout C: `hooks/hooks.json` names the module, and the Codex manifest points `hooks` at a file with no hooks. **Why
  (`mod-dual-host-2.1.299` M04, M05; `dashboard-lab/run-0.1.0` D04):** Codex rejects a hooks file that names `modules`.
- On Codex the dashboard is a command, and the README points to Codex's own `weekly-limit` status line item. **Why
  (`dashboard-lab/codex-status-line-0.162.1` C01–C03):** Codex's status line takes built-in items only.
- The band is a dim rule as wide as `bodyColumns`, then one `{icon}label: value` entry per switch, wrapping whole.
  **Why (maintainer request, 2026-10-16; z-lab `dashboard-lab/run-0.2.0` D06–D08):** the 0.1.0 single line was hard to
  tell apart from the transcript.
- The band is drawn only when at least one entry exists; a failing status command shows as `error` and never breaks the
  others. **Why:** the user asked for the line to show only when because-i-needed plugins are registered; one broken
  plugin must not hide the rest.

## Versioning

SemVer: MAJOR for a changed `dashboard.json` contract; MINOR when what the line shows or how plugins are found
changes; PATCH for documentation.

## Evidence

z-lab `dashboard-lab/run-0.1.0` (D01–D05), `run-0.2.0` (D06–D08), `dashboard-lab/codex-status-line-0.162.1` (C01–C03),
`plugin-platform-lab/mod-dual-host-2.1.299` (M01–M07), `mod-interactive-2.1.299` (I01). Decisions in
`dashboard-lab/analyze/improvement-backlog.md`.
