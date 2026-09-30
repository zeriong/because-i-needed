# Codex execution adapter

Apply the same packet, frame, style, confirmation, audit, split and verbatim-relay
contracts as SKILL.md. A style never selects a model.

## Questions and tools

Use the host's user-input tool when available; otherwise ask in the conversation and
wait for the answer. A non-interactive session needs the user's confirmation already
in its input before Stage 2. Do not manufacture confirmation. Use the host's file and
shell tools for Read/Glob/Grep/Write operations mentioned in the shared instructions.

## Writer settings

| Environment variable | Default | Applies to |
|---|---|---|
| `PLAN_SMITH_CODEX_MODEL` | newest model of the main session's family | every writer, audit and split |
| `PLAN_SMITH_CODEX_EFFORT` | main session's resolved effort | every writer, audit and split |

Resolve the effort once per run. The model setting names a family (such as `sol` or
`luna`) or a model id, and either is resolved to the newest listed model of
that family. Resolve the model right before **each** writer dispatch, including every
relay pass, audit and split:

```bash
python3 "<plugin>/scripts/latest-model.py" codex "<PLAN_SMITH_CODEX_MODEL, else the main session's model id>" --effort "<resolved effort>"
```

Order: when `PLAN_SMITH_CODEX_MODEL` is set, resolve it. Otherwise resolve your own model id; a Codex
main agent may not see it (probes could not), and then your own family if you know it. If you
know neither, do not dispatch: ask the user to set `PLAN_SMITH_CODEX_MODEL` (a family such as `sol`),
because guessing would change the role's family.

Pass stdout to `-m` (or to the native subagent's model field). Exit 2 (the newest cannot
be determined) and exit 3 (effort not supported) mean: do not dispatch, do not substitute
another model, and do not write the plan yourself. Tell the user the resolver's
`latest-model:` message and stop that step. One exception: when the message says `catalog not refreshed` and your shell
runs sandboxed without network, first rerun that one resolver command outside the sandbox
through the host's escalation route — a sandboxed shell cannot refresh Codex's catalog —
and stop only if that is declined or fails too. Record the effort and the id that actually
ran in the packet's run stamp; take the id from the run (the Codex run header `model:`,
or a native subagent's receipt), never from the writer's own report. Style selection
never sets these values. A model override does not authorize broader filesystem
permissions.

## Every plan-writer invocation

The Markdown agent at `<plugin>/agents/plan-writer.md` is the writer's complete role
definition. Codex does not need a registered Claude `plan-smith:plan-writer` agent.

1. Read the agent body below its YAML frontmatter. Include it in a self-contained
   delegation prompt together with every input required by the current stage.
   Resolve resource references against the absolute plugin root. Mark the prompt as
   a delegated plan-writer task: perform only this role, do not start the CXC workflow.
   Include the relevant project instructions explicitly so both hosts use the same rules.
2. Spawn a fresh Codex subagent with **no inherited conversation history** when the
   host supports that option. For example, use `fork_turns="none"` on hosts exposing
   that parameter. Use the id the resolver just returned and the resolved effort above.
   Do not pass Claude model aliases, or reuse an earlier writer thread for another pass.
3. If the available subagent API cannot guarantee a fresh context, write that prompt
   to a temporary file and use a fresh `codex exec` process instead. Pass the
   resolver's id and the effort explicitly. Run from the target project:

   ```bash
   CXC_MODE=off codex exec --ephemeral -s workspace-write \
     -m <resolved id> -c 'model_reasoning_effort="<resolved-writer-effort>"' \
     -C <absolute-project-root> - < <absolute-prompt-file>
   ```

   `CXC_MODE=off` applies only to this child, preserving the main mode.
   The redirected prompt ends at EOF. Do not broaden permissions if execution fails.
   The writer may write only the designated planning artifacts, never project code.
4. Wait for completion, read the artifact files, and apply the normal next stage.
   If no isolated execution route is available, report the missing capability; the
   main agent must not silently become the writer.

The same dispatch applies to single-pass writing, both relay passes, wiring audits,
split mode and optional divergence experiments. A fresh writer receives only its
explicit packet and stage inputs, including the previous draft where relay requires it.
