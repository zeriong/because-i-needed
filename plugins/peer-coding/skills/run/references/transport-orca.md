# Transport: Orca

Orca provides the runtime: runs, tasks with dependencies, workers in their own
worktrees, mid-task questions, gates, and a blocking wait. This skill provides the
policy on top. Don't reimplement Orca's protocol here.

## Load the protocol from the binary

Orca's CLI changes between releases, and the binary ships a version-matched guide.
Before dispatching anything, run:

```bash
orca skills get orchestration --full
```

Follow **that** output for exact command names, flags, and message rules. The mapping
below is conceptual; command names in it are examples and may be outdated.

## Mapping the pipeline onto Orca

| Pipeline concept | Orca concept |
|---|---|
| One feature | a run (objective = plan's Goal) |
| Plan task | a task (spec = the delegation prompt; dependencies from the plan) |
| Lane | a worker started on that task with the matching agent and model |
| Worker "Uncertain" items | the worker asks mid-task instead of returning them |
| Structured return | the worker's completion message — tell it to include the return-format sections in its summary |
| Gate 1 (plan approval), Gate 4 (merge), escalations | Orca gates |
| Waiting for workers | Orca's blocking check/wait, filtered to completion, question and escalation events |
| Rework | a new dispatch on the same task |

Waves don't need manual grouping here: declare dependencies on tasks and let
resolution unblock them. Still keep concurrently running tasks on disjoint files.

Record run and task IDs in `plan.md` so a resumed session can re-attach.

**Worktree setup.** A worker must not start before its uncommitted context exists.
Orca runs the repository's own setup hook when it creates a worktree for a worker
(`worker-start` with a new worktree and `--setup run`), but that hook is configured per
repository in Orca and can't know this plugin's install path, which changes with each
version. So make `<plugin>/scripts/worktree-setup.sh <worktree>` (with the absolute
path you resolved) the first instruction of the delegation prompt; the script finds
the main tree even when run from inside the worktree.

## Questions vs gates

- A worker question pauses **one worker**. Answer it from `plan.md`/`decisions.md`
  when you can, log the answer as a decision, and let it continue.
- A gate pauses **a task and everything depending on it** until a decision is
  recorded. Use gates for plan approval, the final merge decision, and escalations
  to the user — the things that must not proceed without a human.

A wait timeout is not a failure; long tasks are normal. Wait again.

## Model per worker

`worker-start` takes the model and reasoning effort directly — `--model <id>` and
`--effort <level>` (effort requires model) for Claude and Codex agents. Pass the id
`latest-model.py` printed for this dispatch from the lane's family (`CXC_WORKER_MODEL`,
`CXC_CLAUDE_WORKER`; SKILL.md, "Newest model per family") and
`--effort "${CXC_WORKER_EFFORT:-high}"`. Then compare the start receipt's `launch.requested`
and `launch.effective` and log the effective model — never assume a model from the
arguments alone.

## Reviewers never run as Orca workers

`worker-start` has no flag for permissions: a worker runs under the user's own setting
for new agent tabs. That can't guarantee a read-only reviewer, and reviewers must be
read-only (principle 4). So under Orca, **every review runs as the standalone
read-only call** in transport-standalone.md, started by you, with its JSON saved to
`reviews/<phase>-r<n>.json` and validated before triage. Workers still come from Orca.
