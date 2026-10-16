# Changelog

## [0.1.1] - 2026-10-16

### Changed

- `dashboard.json` declares the icon `💰` that dashboard 0.2.0 shows before the label. Nothing else changes.

### Why

Delivery release: installed copies need the new declaration for dashboard 0.2.0 to show the icon (evidence: z-lab
`dashboard-lab/run-0.2.0` D06–D08).

## [0.1.0] - 2026-10-14

### Added

- `budget:mode <1-100> | off | status`: one user-level threshold for Claude Code and Codex
  (`~/.config/because-i-needed/budget.json`).
- Claude Code: a hooks module that, once the five-hour window is at or above the threshold, holds the next tool call
  (subagents' too) and asks "지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?" in Claude Code's own dialog; 예 goes on
  for that window, 아니오 refuses the call and stops the turn.
- Codex: command hooks that read the 7-day window from the account's newest session log, refuse the call with the same
  question for the agent to end its turn with, and take 예 from the next prompt.
- `dashboard.json`: the threshold and the last measured window show on the dashboard plugin.

### Why

Agents in several sessions can use up a usage window before the user looks. A threshold the user picked stops all of
them at one point and leaves the decision to the user (maintainer request, 2026-10-14).

Evidence: z-lab `budget-lab/run-0.1.0` (R01–R09) and `run-0.1.0-r2` (R10–R12) on Claude Code 2.1.299 and Codex 0.162.1,
one run per case: the dialog, 예 and 아니오, one question for parallel subagents, the Codex end-of-turn question and its
answer, and free-hands 0.4.0 letting it through. R08 (Codex's reset time moving by a second re-asked the question) was
fixed before release and re-measured (R10–R12). Not measured: a crossing during a running turn, several interactive
sessions at once, `claude -p` at the threshold, Codex's five-hour window, `/hooks` trust.
