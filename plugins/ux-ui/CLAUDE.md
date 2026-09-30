# ux-ui — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to ux-ui.
The original repository had no development-rules file for this plugin. Everything below was derived from facts checked in the code as of 2026-09-23.

Contents: two skills (`skills/build` for web, `skills/build-mobile` for mobile), two agents (`agents/ux-ui-art-director.md`,
`agents/ux-ui-mobile-art-director.md`, both `model: opus`), the hook `hooks/hooks.json` (PreToolUse → commit gate),
three scripts (`scripts/ui-commit-gate.sh`, `scripts/commit-roots.py`, `scripts/mobile-snapshot.sh`), and four MCP servers in `plugin.json`
(`chrome-devtools`, `mobile-mcp`, `ios-simulator`, `flutter`).

---

## Rule 1 — The plugin name and the MCP server keys are part of tool names

The agents' `tools:` and SKILL.md reference MCP tools as `mcp__plugin_ux-ui_<server-key>`
(`agents/*.md` frontmatter, the Bootstrap step of `skills/build/SKILL.md`). That name is built from **the plugin name + the `mcpServers` keys in `plugin.json`**.

- Renaming the plugin or a server key changes the agents' `tools:` and the SKILL.md reference in the same commit.
  Otherwise the art directors lose their measurement tools.
- Check: `grep -rn 'mcp__plugin_' plugins/ux-ui`
- The plugin name is also embedded in the ten READMEs' `/ux-ui:build` and `/ux-ui:build-mobile` and in the commit gate's block message. Before 1.2.0 the name was `ux-ui-builder`.

## Rule 2 — Copies of one fact change in the same commit

| Fact | Source | Copies |
|---|---|---|
| UI file types | `DEFAULT_GLOBS` in `scripts/ui-commit-gate.sh` | five READMEs (Features, Commit gate, FAQ), `skills/build-mobile/SKILL.md` Roles |
| Mobile measurement backend matrix | the §2 table in `skills/build-mobile/references/backend-detection.md` | the "Mobile measurement backends" table in five READMEs |
| Approval artifact JSON format | the JSON written by `ui-commit-gate.sh approve` | `skills/build/references/review-rubric.md`, `skills/build-mobile/references/mobile-review-rubric.md` |
| Script paths and subcommands | `scripts/*.sh` | `hooks/hooks.json`, both SKILL.md files, `backend-detection.md` (`${CLAUDE_PLUGIN_ROOT}/scripts/...`) |
| Bundled MCP list | `plugin.json` `mcpServers` | agents' `tools:`, five READMEs (Installation, Requirements) |
| Art director model | `model:` in `agents/*.md` | five READMEs ("Opus") |

## Rule 3 — Commit gate invariants

`ui-commit-gate.sh` runs **right before every Bash call** an installed user makes. Therefore:

- Keep the fast path that exits `0` immediately for anything that is not `git commit`.
- **Fail open**: unparseable input, no command, not a git repository → allow (`exit 0`). Never wedge the user's shell (the intent stated in the script's comments).
- Blocking is `exit 2` plus a stderr message. The stderr reaches the agent as the reason for the block.
- Keep the default extensions conservative: no bare `.ts`/`.js`/`.java`, no non-layout `.xml` (so backend-only commits are never blocked).
- Keep the JSON parser fallback (`jq` → `python3` → `node`). Some environments have no `jq`.
- Scripts keep their executable bit (git mode `100755`). A new script gets `chmod +x` before its commit.

## Rule 4 — After editing the gate, run the source script directly

The hook running in a session is **the script in the installed cache**. Editing the source does not change the current session's hook, so run the source directly.
From the repository root (verified 2026-09-23):

```bash
G="$PWD/plugins/ux-ui/scripts/ui-commit-gate.sh"
t=$(mktemp -d) && git -C "$t" init -q && echo '<p/>' > "$t/a.html" && git -C "$t" add a.html
c='{"tool_input":{"command":"git commit -m x"}}'
echo "$c" | CLAUDE_PROJECT_DIR="$t" bash "$G" 2>/dev/null; echo "exit=$?"          # 2 — unapproved UI commit blocked
echo '{"tool_input":{"command":"ls"}}' | CLAUDE_PROJECT_DIR="$t" bash "$G"; echo "exit=$?"  # 0 — fast path
(cd "$t" && bash "$G" approve demo >/dev/null)
echo "$c" | CLAUDE_PROJECT_DIR="$t" bash "$G"; echo "exit=$?"                     # 0 — passes once this diff is approved
rm -rf "$t"
```

If you changed the extensions, run it once more with a file of that extension.

## Rule 5 — Host adapters and resource paths

- Codex uses the shared art-director bodies through an independent read-only execution route;
  Claude retains its registered Opus agents and MCP tool allowlists. Discover actual MCP tool
  names on Codex instead of requiring Claude's namespaced prefix.
- Keep script commands in SKILL.md's host setup, with a plugin-root alias that works on both
  hosts. Backend references point to those commands. Never depend on a shell expanding an
  unset CLAUDE_PLUGIN_ROOT in a reference file.
- The gate's diagnostic names both web and mobile skills and both host invocation prefixes.
  Its exit semantics, extension list and staged-diff hash remain shared.
- Both host manifests must declare the same four MCP servers inline; do not add a second
  default `.mcp.json` that Claude might also discover.
- Resolve `UX_UI_CODEX_REVIEW_MODEL` and `UX_UI_CODEX_REVIEW_EFFORT` for both directors.
  CLI reviewers use `CXC_MODE=off`; native reviewers receive the same delegated role.
  Missing or disabled MCP backends must remain visible in the measurement report.

## Rule 6 — Every art director runs the newest model of its family

Web and mobile directors run the newest model of their family that the installed CLI and account offer, resolved right
before each dispatch (each retry too) with `scripts/latest-model.py` (byte-identical in every plugin). The maintainer
upgrades the CLIs; the plugin only chooses the newest available model.

- Codex: `UX_UI_CODEX_REVIEW_MODEL` names a family or an id and is resolved to its family's newest; unset, the main
  session's model id is used. The command lives in `skills/build/references/host-codex.md`.
- Claude Code: the agents keep `model: opus`; both SKILL.md files run the resolver's `claude` mode first, because an
  `ANTHROPIC_DEFAULT_OPUS_MODEL` override would silently run an older model.
- Exit 2 or 3 stops the step: no fallback model, and the main agent never reviews the render itself.
- Write no versioned model id in a skill, reference, agent or script — use placeholders (`<resolved id>`); a pin-scan test fails on one.
- Record the id that ran with the review, taken from the run (Codex run header `model:`, a native reviewer's receipt), never from the reviewer's report.

**Why:** measured in z-lab `plugin-platform-lab/latest-model-0.159.0/` (L01–L07) and
`latest-model-r2-0.159.0/`, `-r3-`, `-r4-` (L04r–L09, L02x; L08/L08i: a sandboxed shell cannot refresh the catalog,
so a sandboxed main reruns the resolver outside the sandbox before stopping): the live Codex catalog listed a newer model than the
bundled one, `-m <resolved id>` ran it, an `ANTHROPIC_DEFAULT_SONNET_MODEL` override made the `sonnet` alias run Haiku (measured for
`sonnet` only; the resolver applies the same check to `opus`), and a Codex agent's
statement of its own model was wrong (plan-smith-lab N03). Wired skill: z-lab `ux-ui-lab/latest-model-1.4.0/` (R01, R02; R01: from a sandboxed Codex main the separate `codex exec`
director route could not start).

## Codex compatibility evidence — 1.3.0

See z-lab `ux-ui-lab/codex-compat-1.3.0/` and `codex-compat-1.3.0-full-access/` (U01–U03) and the shared
`plugin-platform-lab/codex-final-0.158.0/` packaging/installer checks. These records
cover host wiring and the named fixture paths, not quality improvements. Keep the
existing workflow invariants when changing an adapter.

Additional setting-parity checks: z-lab `ux-ui-lab/codex-parity-1.3.0/` (U04, U05).

Re-review fixes: z-lab `ux-ui-lab/codex-rereview-1.3.0/` (U06–U08).
UI hashing no longer expands configured globs in the shell or loses Unicode/newline filenames. Resolve literal commit targets (including git -C), and store approvals at the worktree root even from nested directories. The target resolver requires Python 3.8+.

Approval metadata must remain valid JSON for quoted names and measurement paths.
