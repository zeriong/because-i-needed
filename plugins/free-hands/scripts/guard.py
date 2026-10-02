#!/usr/bin/env python3
"""free-hands hook guard. Usage: guard.py prompt|session|ask|stop  (hook JSON on stdin)

While `.free-hands/goal.md` is active and has open items (`- [ ]`), it denies the ask tool, keeps the session from
stopping (up to max_iterations) and re-injects the rules after a restart or compaction. With no active goal it only
routes the word "free-hands" in a prompt to the entry question. Any error means "no effect": a hook must never trap a
session because of a broken goal file.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

GOAL = Path(".free-hands") / "goal.md"
SKILL = Path(__file__).resolve().parents[1] / "skills" / "run" / "SKILL.md"
WORD = re.compile(r"free[-_ ]?hands", re.IGNORECASE)
COMMAND = re.compile(r"^\s*[/$]free-hands:run\b")
OPEN_ITEM = re.compile(r"^\s*- \[ \]", re.MULTILINE)
NOTIFICATION = re.compile(r"<task-notification>.*?</task-notification>", re.DOTALL)


def read_input():
    """The hook's JSON object, or None when it is missing or malformed (then the guard does nothing)."""
    try:
        data = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def project_root(data):
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        top = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(cwd)


def field(text, name):
    match = re.search(rf"^{name}:[ \t]*(\S*)[ \t]*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def number(text, name):
    value = field(text, name)
    return int(value) if value.isdigit() else None


def parse(text):
    """Goal metadata, or None when the file is not a well-formed goal (missing or invalid status/counters)."""
    if text is None:
        return None
    maximum, current = number(text, "max_iterations"), number(text, "iterations")
    if not field(text, "status") or maximum is None or maximum < 1 or current is None:
        return None
    return {"status": field(text, "status"), "max": maximum, "iterations": current, "items": open_items(text)}


def load(goal):
    try:
        return goal.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def open_items(text):
    """`- [ ]` lines under `## Checklist` only, outside fenced code — a checkbox quoted in Decisions or Resume is not an
    open item."""
    items, in_checklist, fence = [], False, None
    for line in text.splitlines():
        stripped = line.strip()
        if fence is None:
            opening = re.match(r"(`{3,}|~{3,})", stripped)
            if opening:
                fence = opening.group(1)  # CommonMark: closed by the same character, at least as long, nothing after
                continue
        else:
            closing = re.match(r"(`{3,}|~{3,})\s*$", stripped)
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence):
                fence = None
            continue
        if re.match(r"^##\s", line):
            in_checklist = re.match(r"^##\s+Checklist\s*$", line) is not None
            continue
        if in_checklist and OPEN_ITEM.match(line):
            items.append(stripped)
    return items


def emit(event, context):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}))


def restore_note(goal, info):
    if info["items"] and info["iterations"] >= info["max"]:
        return (f"[free-hands: LIMIT] Goal file: {goal} reached max_iterations with {len(info['items'])} items open. "
                "Set `status: paused`, report the open items to the user, and stop; asking is allowed again.")
    wrong = (f" The goal file says `status: {info['status']}` but {len(info['items'])} items are still `- [ ]`: set "
             "it back to active and continue, or mark each such item `- [-] … — needs the user: <why>`; if the user "
             "asked you to stop or wait, set `status: paused`." if info["status"] in FINISHED else "")
    return (f"[free-hands: ACTIVE]{wrong} Goal file: {goal}. If the free-hands rules are not in your context, read {SKILL} "
            "and the goal file before anything else. Until the goal is done: (1) never ask the user — decide with the "
            "brainstorming panel or yourself, record it under ## Decisions, continue; (2) never merge a PR or into the "
            "default branch, delete irreversibly, deploy or send anything outside — mark such items `- [-] … — needs "
            "the user: <why>`; (3) keep the goal file current (`- [x]` when an item is done; status done, waiting or "
            "paused at the end); (4) if the user asks to pause or stop, set `status: paused` first.")


ENTRY_NOTE = (
    "[free-hands: entry] The prompt mentions free-hands. If it asks to run something in free-hands mode, ask exactly "
    "one question first, in the user's language, before any reasoning or work: \"Enter free-hands mode?\" (yes/no). "
    "Claude Code: AskUserQuestion. Codex: ask it as a plain question and end the turn. On the next turn: yes → start "
    "the mode with the goal from the earlier prompt (Claude Code: the Skill tool, skill `free-hands:run`; Codex: read "
    f"{SKILL} and follow it); no → propose possible directions and end the turn without doing the work. A mention "
    "that explains, quotes or looks back at free-hands is not a request — answer it normally. When unsure, ask the "
    "entry question.")

CORRECTION_NOTE = (
    " The user mentioned free-hands again during the run: treat it as a correction — the current way of working is not "
    "free-hands (for example you asked, waited or stopped). Apply it without asking. If the message asks to pause or "
    "stop, set `status: paused` first instead.")


FINISHED = ("done", "waiting")


def guarded(info):
    """Active, or marked done/waiting while `- [ ]` items are still open (an agent cannot end the run that way)."""
    return info is not None and (info["status"] == "active" or (info["status"] in FINISHED and info["items"]))


def active_goal(data):
    """(goal path, metadata) — metadata is None unless the goal is well formed and guarded."""
    goal = project_root(data) / GOAL
    info = parse(load(goal))
    return (goal, info) if guarded(info) else (goal, None)


def engaged(info):
    return info is not None and info["items"] and info["iterations"] < info["max"]


def on_prompt(data):
    prompt = data.get("prompt") or ""
    if COMMAND.match(prompt):
        return
    # A background task's completion arrives as a prompt made only of <task-notification> blocks; it is not something
    # the user typed. A notification quoted inside a real prompt is removed and the rest is kept.
    prompt = NOTIFICATION.sub("", prompt)
    goal, info = active_goal(data)
    if info is not None:
        emit("UserPromptSubmit", restore_note(goal, info) + (CORRECTION_NOTE if WORD.search(prompt) else ""))
    elif WORD.search(prompt):
        emit("UserPromptSubmit", ENTRY_NOTE)


def on_session(data):
    goal, info = active_goal(data)
    if info is not None:
        emit("SessionStart", restore_note(goal, info))


def on_ask(data):
    goal, info = active_goal(data)
    if not engaged(info):
        return
    reason = (f"free-hands: asking the user is off while the goal is open ({len(info['items'])} items left in "
              f"{goal}). Decide with the brainstorming panel or yourself, record the decision under ## Decisions, "
              "and continue.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def bump(goal):
    """Increment iterations under a lock; return (new, max, open items) only if the new value reached the disk."""
    lock_path = goal.with_name(goal.name + ".lock")
    with open(lock_path, "a") as lock:
        deadline = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    return None
                time.sleep(0.05)
        text = load(goal)
        info = parse(text)
        if not guarded(info) or not engaged(info):
            return None
        new = info["iterations"] + 1
        updated = re.sub(r"^iterations:.*$", f"iterations: {new}", text, count=1, flags=re.MULTILINE)
        fd, tmp = tempfile.mkstemp(dir=goal.parent, prefix=goal.name + ".tmp.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write(updated)
                out.flush()
                os.fsync(out.fileno())
            os.replace(tmp, goal)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        if (parse(load(goal)) or {}).get("iterations") != new:
            return None
        return new, info["max"], info["items"]


def on_stop(data):
    goal, info = active_goal(data)
    if not engaged(info):
        return
    result = bump(goal)
    if result is None:
        return
    new, maximum, items = result
    last = (" This is the last continuation: if items are still open when you stop, set `status: paused` and report "
            "them." if new >= maximum else "")
    status = field(load(goal) or "", "status")
    wrong = (f" `status: {status}` does not end the run while items are open — set it back to active, mark items "
             "`- [-] … — needs the user: <why>`, or set `status: paused` if the user asked you to stop or wait."
             if status in FINISHED else "")
    reason = (f"free-hands: {len(items)} items still open — keep working, do not stop or ask (continuation "
              f"{new}/{maximum}).{wrong}{last} Goal file: {goal}; rules: {SKILL}.\nOpen items:\n" + "\n".join(items))
    print(json.dumps({"decision": "block", "reason": reason}))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if os.environ.get("FREE_HANDS_ROLE"):
        return
    data = read_input()
    if data is None:
        return
    try:
        {"prompt": on_prompt, "session": on_session, "ask": on_ask, "stop": on_stop}.get(mode, lambda _: None)(data)
    except Exception:  # a hook never traps the session on its own failure
        return


if __name__ == "__main__":
    main()
    sys.exit(0)
