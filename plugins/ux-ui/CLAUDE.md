# ux-ui — development rules

Every shared rule in the root `CLAUDE.md` applies. This file holds only what is specific to ux-ui.
The original repository had no development-rules file for this plugin. Everything below was derived from facts checked in the code as of 2026-09-23.

Contents: two skills (`skills/build` for web, `skills/build-mobile` for mobile), two agents (`agents/ux-ui-art-director.md`,
`agents/ux-ui-mobile-art-director.md`, both `model: opus`), the hook `hooks/hooks.json` (PreToolUse → commit gate),
two scripts (`scripts/ui-commit-gate.sh`, `scripts/mobile-snapshot.sh`), and four MCP servers in `plugin.json`
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

## Rule 5 — Known defects (confirmed 2026-09-23, unfixed)

- The block message (`ui-commit-gate.sh` hook mode) points only to the web skill `/ux-ui:build` and chrome-devtools.
  When a mobile file (`.swift` `.kt` `.dart` `.storyboard` `.xib`, `res/layout`) is blocked it does not mention `/ux-ui:build-mobile`.
  Changing the message is a behavior change visible to installed users, so bump the version (root Rule 2).
- `skills/build-mobile/references/backend-detection.md` lines 28, 85 and 86 call `"${CLAUDE_PLUGIN_ROOT}/scripts/mobile-snapshot.sh"`.
  That variable is replaced only in SKILL.md text at skill load and is not set in the Bash environment (z-lab
  `plugin-platform-lab/skill-plugin-root-2.1.283/`, V01–V02), so a reference read later keeps it literal and the path
  resolves to `/scripts/…` — measured: a reference with that line ran `bash: /scripts/hello.sh: No such file or directory`
  3/3, and haiku never recovered (V03–V04, `reference-plugin-root-2.1.283/`). `doctor` is also in SKILL.md (fine); the two
  `capture` commands exist only here.
  Fix by pointing to the SKILL.md path — the pattern ran 3/3 in a minimal skill (V05–V06, `reference-pointer-2.1.283/`);
  it changes behavior, so measure it on this skill in z-lab and bump the version (root Rule 9, Rule 2).
  (Confirmed 2026-09-28, unfixed.)
