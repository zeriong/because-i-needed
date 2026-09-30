# Repository instructions

Read `CLAUDE.md` at the repository root before working here. It contains the shared
maintenance rules for both Claude Code and Codex. Before changing a plugin, also read
that plugin's `plugins/<name>/CLAUDE.md`.

The two host manifests package the same skills and resources. Preserve Claude Code's
existing commands, generated paths and behavior when adding Codex support. Codex host
adapters belong inside each plugin so they survive installation of that plugin alone.
