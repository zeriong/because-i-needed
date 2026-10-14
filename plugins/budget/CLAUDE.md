# budget — development rules

Every shared rule in the root `CLAUDE.md` applies. This plugin holds every session at a user-chosen share of the
account's usage window and asks whether to go on.

Contents: the `mode` skill (Codex policy in `skills/mode/agents/openai.yaml`); a Claude Code hooks module
(`hooks/hooks.json` → `hooks/register.ts`); Codex command hooks (`hooks/codex.json` → `scripts/gate.py`, named by
`.codex-plugin/plugin.json`); `scripts/budget.py` (settings, state, status); `dashboard.json` (root Rule 11).

## Invariants

- One plugin folder serves both hosts in layout C: `hooks/hooks.json` names the module for Claude Code, and the Codex
  manifest points `hooks` at `hooks/codex.json`. **Why (z-lab `plugin-platform-lab/mod-dual-host-2.1.299` M02–M05):**
  Claude Code runs `hooks/hooks.json` and a manifest `hooks` path both, Codex rejects a hooks file that names `modules`,
  and only this layout runs each host's entry point once.
- Claude Code measures the `five_hour` window, Codex the `seven_day` window (`window_minutes: 10080`). **Why (maintainer
  decision, 2026-10-14; z-lab `budget-lab/codex-gate-0.1.0` B02):** Codex reports only the 7-day window on the measured
  account.
- Claude Code asks through `$.ui.ask` in a `tool.call` hook, one shared question per session, and on 아니오 refuses the
  call and aborts the turn. **Why (z-lab `plugin-platform-lab/mod-interactive-2.1.299` I02–I04; `budget-lab/run-0.1.0`
  R01–R05):** the dialog is the engine's own, subagents' calls pass through the hook, and one answer serves them all.
- Codex refuses the call and tells the agent to end its turn with the question; `UserPromptSubmit` takes the answer.
  The window is the newest rate-limit record among the session's rollout and the 20 most recent beside it. **Why
  (`budget-lab/codex-gate-0.1.0` B01, `-r2` B04–B08):** Codex has no plugin dialog, and a fresh session's own rollout
  has no record before its first call.
- While a session's question is open, `budget/pending/<session id>.json` holds `{"open": true, …}`; free-hands reads it
  and stands aside. Claude Code names it by `$.session.id()`, which equals the hook input's `session_id`. **Why
  (`mod-interactive-2.1.299` I05; `budget-lab/run-0.1.0` R04, R07):** free-hands 0.3.0 blocked the question and, on
  Codex, the end of the turn.
- An acknowledgement matches a window whose reset time is within 600 seconds. **Why (`budget-lab/run-0.1.0` R08 →
  `run-0.1.0-r2` R10–R12):** Codex's `resets_at` moved by one second between records and the session was asked again.
- A session with nobody to ask (`$.ui.ask` rejects) and a dismissed dialog count as 아니오. **Why (decision D-B1,
  2026-10-14, in `budget-lab/analyze/improvement-backlog.md`):** the threshold protects the user's spending; nothing goes
  past it without a 예.
- The question text "지정한 n%에 도달했습니다, 작업을 이어서 진행하시겠어요?" and the answers 예/아니오 stay Korean. **Why
  (maintainer decision, 2026-10-14; root Rule 4 exception):** the maintainer worded the question, and the answers are
  what a Codex user types.
- Any failure of budget's own code lets the call through. **Why:** a guard must never trap a session on its own error
  (the free-hands rule, shared here).

## Versioning

SemVer: MAJOR for a changed settings or state format; MINOR when a host, window or gate behavior is added or changed;
PATCH for documentation.

## Evidence

z-lab `budget-lab/run-0.1.0` (R01–R09) and `run-0.1.0-r2` (R10–R12); pre-build `budget-lab/codex-gate-0.1.0`
(B01–B03), `codex-gate-0.1.0-r2` (B04–B08), `plugin-platform-lab/mod-dual-host-2.1.299` (M01–M07),
`mod-interactive-2.1.299` (I01–I05). Decisions in `budget-lab/analyze/improvement-backlog.md`.
