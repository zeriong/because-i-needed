---
name: mode
description: "Set, clear or show budget's usage threshold — the percent of the account's usage window at which every running session stops and asks whether to continue. Use only when the user asks for it, e.g. \"/budget:mode 80\", \"budget off\", \"budget status\", \"사용량 80%에서 멈춰줘\"."
disable-model-invocation: true
argument-hint: "<1-100> | off | status"
---

# budget: mode

Claude Code invokes `/budget:mode`; Codex invokes `$budget:mode`. `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` when expanded
by Claude Code, or the absolute path two directories above this skill's directory on Codex (resolve it from the loaded
SKILL.md path, not the working directory).

The threshold is one user-level setting shared by both hosts. Claude Code measures it against the five-hour window,
Codex against the 7-day window (the one Codex reports).

## What to do

Map the user's argument to one command and run it; with no argument, use `status`. Report the output as-is.

```bash
python3 "<plugin>/scripts/budget.py" set <1-100>   # a number: stop and ask at that percent
python3 "<plugin>/scripts/budget.py" off           # turn the gate off
python3 "<plugin>/scripts/budget.py" status        # show the threshold and the last measured window
```

A number outside 1–100 or anything else: say what the argument may be and run nothing.
