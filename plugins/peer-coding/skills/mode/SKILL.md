---
name: mode
description: "Turn peer-coding orchestration mode on or off, set which model family and effort its workers and reviewers use, or show the current state. Use only when the user asks to enable, disable, reset, or check the mode or these settings — e.g. \"/peer-coding:mode on\", \"/peer-coding:mode codex-reviewer astra\", \"peer-coding mode status\", \"오케스트레이션 모드 켜줘/꺼줘\", \"리뷰어 모델 astra로 바꿔줘\" (switch the reviewer model to astra)."
disable-model-invocation: true
argument-hint: "on | off | status | clear  [--global]   ·   <setting> <value> | <setting> unset  [--global]"
---

# peer-coding: mode

Claude Code invokes `/peer-coding:mode`; Codex invokes
`$peer-coding:mode`. `<plugin>` is `${CLAUDE_PLUGIN_ROOT}` when
expanded by Claude Code, or the absolute path two directories above this skill's
directory on Codex. Resolve it from the loaded SKILL.md path, not the working directory.

A one-line switch for `peer-coding:run`, and the place to choose its models and efforts.

- **on** — every implementation task in this project goes through `run`
  (trivial requests excepted; see that skill's "Mode gate").
- **off** — you work as the single agent running in this terminal. `run` starts
  only when the user explicitly asks for it.

## What to do

Run the command that matches the user's arguments, then report its output as-is, including
any `hint:` or `note:` lines — they tell the user how to change the other scope or what still
overrides the value. Default to `status` when no argument is given.

```bash
"<plugin>/scripts/mode.sh" <on|off|clear> [--global]                    # the mode
python3 "<plugin>/scripts/settings.py" set <setting> <value> [--global]  # a model or effort
python3 "<plugin>/scripts/settings.py" unset <setting> [--global]        # back to the next level
"<plugin>/scripts/mode.sh" status && python3 "<plugin>/scripts/settings.py" status   # status
```

Outside Claude Code plugins, the scripts are in `../../scripts/` relative to this skill's
directory. Map the user's words onto a setting name ("the reviewer" on its own means the
other vendor's reviewer, `codex-reviewer` when you are Claude and `claude-reviewer` when you are
Codex); if the words fit no setting, run `status` and show the names.

Do nothing else in this turn — don't start, stop, or resume an orchestration run.
Turning the mode off mid-run leaves the run's state in `.claude-x-codex/<feature>/`;
tell the user it can be resumed with `/peer-coding:run` on Claude Code or
`$peer-coding:run` on Codex.

## Model settings

| Setting | Chooses | Default | Values |
|---|---|---|---|
| `codex-worker` | the `codex-bulk` lane's model family | `terra` | a Codex family: `terra`, `luna`, `sol`, `astra` |
| `codex-reviewer` | the Codex reviewer's family | `sol` | as above |
| `claude-worker` | the `claude-fast` lane's model family | `sonnet` | a Claude family: `sonnet`, `opus`, `haiku`, `fable` |
| `claude-reviewer` | the Claude reviewer's family | `opus` | as above |
| `worker-effort` | both vendors' workers | `high` | `low`, `medium`, `high`, `xhigh`, `max` |
| `review-effort` | both vendors' reviewers | `xhigh` | as above |

A model setting names a family; each dispatch runs the newest version of it. A family this
version doesn't list is stored with a `note:`, and a dispatch stops the lane if the CLI has no
model in it. Each setting resolves first match wins: its `CXC_*` variable → this project
(`.claude-x-codex/settings`, git-excluded) → Claude Code's `/config` → your global file
(`~/.config/claude-x-codex/settings`) → the default. `unset` removes the value at one level.

On Claude Code the same six are rows of `/config` (type `peer-coding` to find them); a choice
there is your global default and wins over the global file, so `set … --global` prints a
`note:` when `/config` already holds that setting. Codex has no settings menu for plugins, so
there the command is the way to set them. Settings passed only for one session (`--settings`,
managed settings) are not read. A model or effort set here is the user's choice: `run` uses
it as set, `astra` or `max` included, without asking again.

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

- **Claude Code and Codex**: the plugin's `UserPromptSubmit` hook runs `mode.sh get` on every
  prompt and, when the mode is on, adds a short context note telling the main agent to
  route implementation work through `peer-coding:run`. When off, it adds nothing, so
  normal sessions pay no token cost. On Codex, review and trust the installed hook
  in `/hooks`; installing the plugin alone does not trust it. Report whether this
  automatic route is active before describing mode as automatic.
- **Hosts without prompt hooks** (or if you prefer not to install the hook): add this
  line to the project's `AGENTS.md` / `CLAUDE.md`:

  ```markdown
  Before starting any implementation task, run `<plugin>/scripts/mode.sh get`.
  If it prints `on`, use the `peer-coding:run` skill for that task.
  ```

  This is weaker than the hook — it relies on the agent remembering to check — so
  prefer the hook where the host supports it.
