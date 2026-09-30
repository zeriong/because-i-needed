# Codex execution adapter (web and mobile)

Use `$ux-ui:build` for web and `$ux-ui:build-mobile` for mobile. The measurement
matrices, review rubrics, three-cycle limit and staged-diff approval contract are shared
with Claude Code.

## Bootstrap

- Discover the actual MCP tools exposed by this session for `chrome-devtools`,
  `mobile-mcp`, `ios-simulator` and `flutter`. Claude's `mcp__plugin_ux-ui_*` prefix
  is not a requirement on Codex. Match server identity and capabilities, not a guessed
  tool name. Retain the web bootstrap's missing-browser stop and the mobile backend
  selection/fallback rules.
- The two host manifests bundle the same four MCP servers. Node/Chrome and mobile
  SDK requirements still apply. Installing a plugin does not boot a device or install
  an SDK. Start only the backend needed for the task.
- Verify the enabled plugin's `PreToolUse` hook in `/hooks`. Codex must trust the
  current hook definition before it runs; a plugin installation alone is insufficient.
  If hooks are disabled, unsupported or untrusted, report that the automatic commit
  gate is inactive and wait for setup before claiming this workflow's hard gate works.
  Do not silently replace it with a promise to remember.

## Reviewer and MCP settings

| Variable | Default | Scope |
|---|---|---|
| `UX_UI_CODEX_REVIEW_MODEL` | newest model of the main session's family | web and mobile directors |
| `UX_UI_CODEX_REVIEW_EFFORT` | main session's resolved effort | web and mobile directors |

The model variable names a family (such as `sol` or `luna`) or a model id, and
either is resolved to the newest listed model of that family. Resolve right before
**every** director dispatch, each retry included:

```bash
python3 "<plugin>/scripts/latest-model.py" codex "<UX_UI_CODEX_REVIEW_MODEL, else the main session's model id>" --effort "<resolved review effort>"
```

Order: when `UX_UI_CODEX_REVIEW_MODEL` is set, resolve it. Otherwise resolve your own model id; a Codex
main agent may not see it (probes could not), and then your own family if you know it. If you
know neither, do not dispatch: ask the user to set `UX_UI_CODEX_REVIEW_MODEL` (a family such as `sol`),
because guessing would change the role's family.

Pass stdout to `-m` (or to a native reviewer's model field). Exit 2 (the newest cannot be
determined) and exit 3 (effort not supported) mean: do not dispatch, do not substitute
another model, and do not review the render yourself. Tell the user the resolver's
`latest-model:` message, report the missing capability, and stop that step. One exception: when the message says `catalog not refreshed` and your shell
runs sandboxed without network, first rerun that one resolver command outside the sandbox
through the host's escalation route — a sandboxed shell cannot refresh Codex's catalog —
and stop only if that is declined or fails too. Record the
effort and the id that actually ran with the review; take the id from the run (the Codex
run header `model:`, or a native reviewer's receipt), never from the reviewer's own
report. Do not reduce the review criteria. Existing `UX_UI_GLOBS` configures the same
commit-gate extension set on both hosts.

Enable only needed MCP backends through Codex's plugin MCP settings (plugin id
`ux-ui@because-i-needed` for this marketplace). A disabled backend is distinct from a server that
failed to start. Keep other plugins' settings unchanged; configuration changes must
follow the user's selected backend. Inspect the actual exposed tools on every host.
The command names in measurement references describe capabilities, not required
Codex tool prefixes. If the required capture/audit capability is unavailable, report
that missing check rather than inventing a result.

## Art director dispatch

For web use `<plugin>/agents/ux-ui-art-director.md`; for mobile use
`<plugin>/agents/ux-ui-mobile-art-director.md`. Read the body below its Claude YAML
frontmatter and give it to a fresh Codex reviewer. Include absolute paths to the
measurement directory, relevant source, rubric and design-principle references.

Use a fresh read-only reviewer execution route; use the id the resolver returned and the
resolved effort above instead of passing the Claude `opus` alias. If the host cannot restrict a subagent to
read-only execution, write a self-contained prompt file and start a separate process:

```bash
CXC_MODE=off codex exec --ephemeral -s read-only \
  -m <resolved-review-model> -c 'model_reasoning_effort="<resolved-review-effort>"' \
  -C <absolute-project-root> - < <absolute-review-prompt>
```

Give a native reviewer the same selected settings. In either route, mark the prompt
`You are reviewing measured UI`: perform only that delegated role, never start the
CXC implementation workflow. Include relevant project design instructions from
AGENTS.md, applicable overrides and CLAUDE.md; they are not interchangeable filenames.
The CLI environment override affects this child only.

The reviewer must open the real screenshots with its image-viewing tool. A reviewer
without the required MCP can inspect the saved artifacts and request missing captures
from the main agent. Missing pixels or missing required states require
`CHANGES_REQUIRED`, never an inferred approval. It must not edit source or create an
approval artifact. Wait for its verdict before continuing the shared loop.

Each retry starts a new reviewer. If no independent read-only route exists, stop and
report the missing capability. Run the existing approval command only after APPROVED;
no adapter may weaken the binding to the staged UI diff.
