#!/usr/bin/env python3
"""budget's Codex hooks. Usage: gate.py pretool|prompt  (hook JSON on stdin)

Codex has no ask dialog for a plugin, so past the threshold PreToolUse denies the call and tells the agent to end its
turn with the question; the user's next prompt answers it. The window is the newest rate-limit record among this
session's rollout and the account's recent rollouts beside it (a fresh session's own rollout has none before its first
call — z-lab budget-lab codex-gate-0.1.0 B01, r2 B04). Codex reports the 7-day window (window_minutes 10080). Any error
means no effect: the gate never traps a session because of its own failure.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import budget  # noqa: E402

SEVEN_DAYS = 10080
QUESTION = "지정한 {n}%에 도달했습니다, 작업을 이어서 진행하시겠어요?"
YES = {"예", "네", "yes", "y", "계속", "continue"}


def last_limits(path):
    """(timestamp, rate_limits) of the file's newest rate-limit record, or None."""
    found = None
    try:
        lines = Path(path).read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in lines:
        if '"rate_limits"' not in line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        stack = [event]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if isinstance(node.get("rate_limits"), dict):
                    found = (str(event.get("timestamp") or ""), node["rate_limits"])
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return found


def newest_window(transcript):
    """The 7-day window of the newest record among this session's rollout and the 20 most recently written beside it."""
    if not transcript:
        return None
    path = Path(transcript)
    files = [path]
    sessions = path.parents[3] if len(path.parents) > 3 else None
    if sessions is not None and sessions.is_dir():
        files += sorted(sessions.rglob("rollout-*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)[:20]
    records = [r for r in (last_limits(f) for f in dict.fromkeys(files)) if r]
    if not records:
        return None
    limits = max(records, key=lambda r: r[0])[1]
    for key in ("primary", "secondary"):
        window = limits.get(key)
        if isinstance(window, dict) and window.get("window_minutes") == SEVEN_DAYS:
            return window
    return None


def on_pretool(data, sid):
    n = budget.threshold()
    if n is None:
        return None
    window = newest_window(data.get("transcript_path"))
    if not window or not isinstance(window.get("used_percent"), (int, float)):
        return None
    used, resets_at = window["used_percent"], window.get("resets_at")
    budget.record_usage("seven_day", used, resets_at, "codex")
    ack = budget.read_json(budget.session_file("acks", sid)) or {}
    if used < n or budget.same_window(ack.get("resets_at"), resets_at):
        return None
    budget.write_json(budget.session_file("pending", sid), {"open": True, "resets_at": resets_at, "used": used,
                                                           "threshold": n})
    reason = (f"budget: the 7-day usage window is at {used:g}% (threshold {n}%). Do not run anything else and do not "
              f"work around this. End your turn now and ask the user exactly: \"{QUESTION.format(n=n)}\" (예/아니오)")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def on_prompt(data, sid):
    pending = budget.read_json(budget.session_file("pending", sid)) or {}
    if pending.get("open") is not True:
        return None
    if (data.get("prompt") or "").strip().lower().rstrip(".!") in YES:
        budget.write_json(budget.session_file("acks", sid), {"resets_at": pending.get("resets_at")})
        budget.session_file("pending", sid).unlink(missing_ok=True)
        note = "budget: the user chose to continue past the threshold; carry on with the work."
    else:
        note = ("budget: the user has not confirmed continuing past the usage threshold. Do not run tools; if they "
                "want to go on, they answer 예.")
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": note}}


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return
    if not isinstance(data, dict):
        return
    sid = data.get("session_id")
    if not isinstance(sid, str) or not budget.SESSION_ID.fullmatch(sid):
        return
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        out = {"pretool": on_pretool, "prompt": on_prompt}.get(mode, lambda *_: None)(data, sid)
    except Exception:  # the gate never traps a session on its own failure
        return
    if out:
        print(json.dumps(out))


if __name__ == "__main__":
    main()
