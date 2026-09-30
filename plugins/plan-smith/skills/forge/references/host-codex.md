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
| `PLAN_SMITH_CODEX_MODEL` | main session's resolved model | every writer, audit and split |
| `PLAN_SMITH_CODEX_EFFORT` | main session's resolved effort | every writer, audit and split |

Resolve these once per run and record the effective values in the packet. Explicit
user choices win. Verify the model supports the selected effort; do not invent a
model id or silently change settings when unknown. Style selection never sets these
values. A model override does not authorize broader filesystem permissions.

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
   that parameter. Use the resolved writer model and effort above. Do not pass Claude model
   aliases, or reuse an earlier writer thread for another pass.
3. If the available subagent API cannot guarantee a fresh context, write that prompt
   to a temporary file and use a fresh `codex exec` process instead. Pass the main
   writer model and effort explicitly. Run from the target project:

   ```bash
   CXC_MODE=off codex exec --ephemeral -s workspace-write \
     -m <resolved-writer-model> -c 'model_reasoning_effort="<resolved-writer-effort>"' \
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
