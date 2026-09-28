---
name: mode
description: Turn claude-x-codex orchestration mode on or off, or show its current status. Use only when the user asks to enable, disable, reset, or check the mode — e.g. "/claude-x-codex:mode on", "claude-x-codex mode status", "오케스트레이션 모드 켜줘/꺼줘".
disable-model-invocation: true
argument-hint: "on | off | status | clear  [--global]"
---

# claude-x-codex: mode

A one-line switch for `claude-x-codex:run`.

- **on** — every implementation task in this project goes through `run`
  (trivial requests excepted; see that skill's "Mode gate").
- **off** — you work as the single agent running in this terminal. `run` starts
  only when the user explicitly asks for it.

## What to do

Run the script with the user's arguments, then report its output as-is, including any
`hint:` or `note:` lines — they tell the user how to change the other scope. Default to
`status` when no argument is given.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/mode.sh" <on|off|status|clear> [--global]
```

Outside Claude Code plugins, the script is at `../../scripts/mode.sh` relative to this
skill's directory.

Do nothing else in this turn — don't start, stop, or resume an orchestration run.
Turning the mode off mid-run leaves the run's state in `.claude-x-codex/<feature>/`;
tell the user it can be resumed with `/claude-x-codex:run`.

## Scopes

| Command | Writes | Effect |
|---|---|---|
| `on` / `off` | `<repo>/.claude-x-codex/mode` | This project only (git-excluded) |
| `on --global` / `off --global` | `~/.config/claude-x-codex/mode` | Your default for every project |
| `clear` | removes the project flag | Falls back to your global default |
| `CXC_MODE=on\|off` env var | — | Overrides both, for one shell |

The flag file is a single line: `mode=on` or `mode=off`. Anything else
counts as unset.

## Platforms

The scripts are POSIX-tool bash (compatible with macOS's bash 3.2 and BSD utilities).

| Platform | Status |
|---|---|
| Linux | Supported |
| macOS | Supported |
| Windows + WSL | Supported (behaves as Linux) |
| Windows + Git Bash | Should work; paths follow Git Bash (`~` = `/c/Users/<you>`) |
| Windows PowerShell / cmd only | Not supported — install Git for Windows or use WSL |

On Windows, scripts must stay LF. The plugin's `.gitattributes` enforces this; if you
copy files without git, convert line endings to LF.

## How the switch reaches the main agent

- **Claude Code**: the plugin's `UserPromptSubmit` hook runs `mode.sh get` on every
  prompt and, when the mode is on, adds a short context note telling the main agent to
  route implementation work through `claude-x-codex:run`. When off, it adds nothing, so
  normal sessions pay no token cost.
- **Hosts without prompt hooks** (or if you prefer not to install the hook): add this
  line to the project's `AGENTS.md` / `CLAUDE.md`:

  ```markdown
  Before starting any implementation task, run `<plugin>/scripts/mode.sh get`.
  If it prints `on`, use the `claude-x-codex:run` skill for that task.
  ```

  This is weaker than the hook — it relies on the agent remembering to check — so
  prefer the hook where the host supports it.
