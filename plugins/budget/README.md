<p align="center"><strong>budget</strong></p>

<p align="center">Works only with <strong>Claude Code</strong> and <strong>Codex CLI</strong>.</p>

<p align="center"><strong>Pick a share of your usage window; when it is reached, every running session stops and asks whether to go on.</strong></p>

<p align="center"><a href=".claude-plugin/plugin.json"><img src="https://img.shields.io/badge/version-0.1.1-blue" alt="Version"></a> <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a> <a href="https://docs.claude.com/en/docs/claude-code/plugins"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-orange" alt="Claude Code Plugin"></a></p>

<p align="center"><a href="#start">Start</a> &bull; <a href="#how-it-works">How it works</a> &bull; <a href="#settings-and-state">Settings and state</a> &bull; <a href="#limits-and-status">Limits and status</a> &bull; <a href="#requirements">Requirements</a> &bull; <a href="#installation">Installation</a></p>

<p align="center"><a href="README.md">English</a> &bull; <a href="README.ko.md">한국어</a> &bull; <a href="README.ja.md">日本語</a> &bull; <a href="README.zh-CN.md">简体中文</a> &bull; <a href="README.zh-TW.md">繁體中文</a></p>

<p align="center"><sub>Part of <a href="../../README.md">because-i-needed</a></sub></p>

---

budget watches the usage window your account reports and holds every session at the share you chose. When the window reaches it, the next tool call in each running session — its subagents' calls included — waits for one question: **"지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?"** (You have reached the n% you set — continue the work?). Answer 예 to go on, 아니오 to stop. The [dashboard](../dashboard) plugin shows the threshold you set.

## Start

- Claude Code: `/budget:mode 80` · Codex: `$budget:mode 80` — stop and ask at 80%.
- `/budget:mode off` turns it off; `/budget:mode status` shows the threshold and the last measured window.
- The threshold is one setting for your user account, shared by Claude Code and Codex.

## How it works

**Claude Code** measures the **five-hour** window. Claude Code reports it to plugins after each turn and whenever it moves a whole point. When it is at or above the threshold, budget holds the next tool call and asks in Claude Code's own question dialog (chip `budget`, options 예 and 아니오).

- 예: the call goes on, and that session is not asked again until the window resets.
- 아니오: the call is refused and the turn stops.
- One question answers every call that arrives while it is open, so parallel subagents are asked once.
- A run with nobody to answer (`claude -p`) and a dismissed dialog count as 아니오.

**Codex** measures the **7-day** window, the only one Codex reports. budget reads the newest figure in the account's recent session logs (`~/.codex/sessions`), so a new session is held from its first call. Codex has no dialog a plugin can open, so budget refuses the call and tells the agent to end its turn with the same question. Answer 예 (also `네`, `yes`, `y`, `계속`, `continue`) to go on; any other answer keeps the session stopped. Trust the plugin's hooks in `/hooks` first.

**With [free-hands](../free-hands):** free-hands never asks during a goal, with one exception: this question. While budget's question is open in a session, free-hands 0.4.0 lets it through and does not keep the turn going.

## Settings and state

- `~/.config/because-i-needed/budget.json` (under `$XDG_CONFIG_HOME` when it is set): `{"percent": 80}`. `/budget:mode` writes it; `off` removes it.
- `~/.config/because-i-needed/budget/`: `pending/<session>.json` while a session's question is open, `acks/<session>.json` after 예 for a window, `usage.json` with the last window a host reported (the dashboard shows it).
- A new window asks again. A reset time that moves by seconds counts as the same window, because Codex's reported reset time shifts by a second between readings.

## Limits and status

Measured once per case on Claude Code 2.1.299 and Codex 0.162.1 ([z-lab `budget-lab`](https://github.com/zeriong/z-lab/tree/main/budget-lab): `run-0.1.0`, `run-0.1.0-r2`; the facts they rest on in `codex-gate-0.1.0`, `codex-gate-0.1.0-r2` and z-lab `plugin-platform-lab/mod-interactive-2.1.299`):

- Claude Code showed the dialog; 예 let the call run, and 아니오 stopped the turn ("Interrupted"). Under the threshold nothing happened. Two parallel subagents were asked once. After 예, later calls ran without another question (R01–R05, R10).
- Codex ended the turn with the question and ran nothing. 예 unlocked the session, and later calls ran without another question; under the threshold nothing happened (R06, R09, R11).
- With free-hands running a goal, the question was shown on Claude Code. On Codex the gated turn ended at once; under free-hands 0.3.0 the stop guard kept it going three more times (R04, R07, R12; codex-gate B03).

Not measured: a threshold crossed while a turn is already running (a turn can go past the threshold before Claude Code's next report); several interactive sessions at once; a `claude -p` run at the threshold; Codex's five-hour window (not reported on the measured account); Codex hooks trusted through `/hooks` rather than bypassed.

Claude Code's plugin hooks module API that budget uses is marked early access and may change between releases.

## Requirements

- Claude Code with plugin hooks modules (measured on 2.1.299) or Codex CLI (measured on 0.162.1).
- `python3` on `PATH`, for the Codex hooks and `/budget:mode`.

## Installation

First add the marketplace, then install the plugin:

```bash
claude plugin marketplace add https://github.com/zeriong/because-i-needed.git
claude plugin install budget@because-i-needed
```

For Codex, follow the [marketplace instructions](../../README.md#codex).

## License

MIT. See [LICENSE](../../LICENSE).
