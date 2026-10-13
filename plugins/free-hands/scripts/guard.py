#!/usr/bin/env python3
"""free-hands hook guard. Usage: guard.py prompt|session|ask|stop  (hook JSON on stdin)

While `.free-hands/goal.md` is active and has open items (`- [ ]`), it denies the ask tool, keeps the session from
stopping (up to max_iterations) and re-injects the rules after a restart or compaction — in the session named by the
goal's `owner:` only. Other sessions in the same repository are left alone. With no active goal it only routes the word
"free-hands" in a prompt to the entry question. Any error means "no effect": a hook must never trap a session because of
a broken goal file.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shellguard  # noqa: E402

GOAL = Path(".free-hands") / "goal.md"
SKILL = Path(__file__).resolve().parents[1] / "skills" / "run" / "SKILL.md"
WORD = re.compile(r"free[-_ ]?hands", re.IGNORECASE)
COMMAND = re.compile(r"^\s*[/$]free-hands:run\b")
OPEN_ITEM = re.compile(r"^\s*- \[ \]", re.MULTILINE)
SESSION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
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


def session_of(data):
    """The host's session id from the hook input (both hosts send it on every event, z-lab S01), or None."""
    sid = data.get("session_id")
    return sid if isinstance(sid, str) and SESSION_ID.fullmatch(sid) else None


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
    return {"status": field(text, "status"), "max": maximum, "iterations": current, "items": open_items(text),
            "owner": field(text, "owner")}


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
    owner = f" This session owns the run: keep `owner: {info['owner']}` in the goal file." if info["owner"] else ""
    if info["items"] and info["iterations"] >= info["max"]:
        return (f"[free-hands: LIMIT] Goal file: {goal} reached max_iterations with {len(info['items'])} items open. "
                f"Set `status: paused`, report the open items to the user, and stop; asking is allowed again.{owner}")
    wrong = (f" The goal file says `status: {info['status']}` but {len(info['items'])} items are still `- [ ]`: set "
             "it back to active and continue, or mark each such item `- [-] … — needs the user: <why>`; if the user "
             "asked you to stop or wait, set `status: paused`." if info["status"] in FINISHED else "")
    return (f"[free-hands: ACTIVE]{wrong}{owner} Goal file: {goal}. If the free-hands rules are not in your context, "
            f"read {SKILL} and the goal file before anything else. Until the goal is done: (1) never ask the user — "
            "decide with the brainstorming panel or yourself, record it under ## Decisions, continue; (2) never merge a "
            "PR or into the default branch, delete irreversibly, deploy or send anything outside — mark such items "
            "`- [-] … — needs the user: <why>`; (3) keep the goal file current (`- [x]` when an item is done; status "
            "done, waiting or paused at the end); (4) if the user asks to pause or stop, set `status: paused` first.")


ENTRY_NOTE = (
    "[free-hands: entry] The prompt mentions free-hands. If it asks to run something in free-hands mode, ask exactly "
    "one question first, in the user's language, before any reasoning or work: \"Enter free-hands mode?\" (yes/no). "
    "Claude Code: AskUserQuestion. Codex: ask it as a plain question and end the turn. On the next turn: yes → start "
    "the mode with the goal from the earlier prompt (Claude Code: the Skill tool, skill `free-hands:run`; Codex: read "
    f"{SKILL} and follow it); no → propose possible directions and end the turn without doing the work. A mention "
    "that explains, quotes or looks back at free-hands is not a request — answer it normally. When unsure, ask the "
    "entry question.")


def session_note(sid, owner):
    """The id the agent writes as `owner:` when it starts or resumes a run, and who owns the run now."""
    if not sid:
        return ""
    other = (f" Session {owner} owns the free-hands run in this repository now; starting or resuming free-hands here "
             "moves the run to this session." if owner and owner != sid else "")
    return f" [free-hands: session] This session's id is {sid}: write `owner: {sid}` in the goal file header.{other}"


CORRECTION_NOTE = (
    " The user mentioned free-hands again during the run: treat it as a correction — the current way of working is not "
    "free-hands (for example you asked, waited or stopped). Apply it without asking. If the message asks to pause or "
    "stop, set `status: paused` first instead.")


FINISHED = ("done", "waiting")


def guarded(info):
    """Active, or marked done/waiting while `- [ ]` items are still open (an agent cannot end the run that way)."""
    return info is not None and (info["status"] == "active" or (info["status"] in FINISHED and info["items"]))


def active_goal(data):
    """(goal path, metadata, owner of a guarded goal held by another session) — metadata is None unless the goal is
    well formed, guarded and this session's. A goal without `owner:` becomes the first session's that sees it."""
    goal = project_root(data) / GOAL
    info = parse(load(goal))
    if not guarded(info):
        return goal, None, None
    sid = session_of(data)
    if sid is None:  # a host without session ids keeps the repository-wide guard
        return goal, info, None
    if not info["owner"]:
        info = claim(goal, sid)
    if info is None or info["owner"] != sid:
        return goal, None, info and info["owner"]
    return goal, info, None


def engaged(info):
    return info is not None and info["items"] and info["iterations"] < info["max"]


def peek_owner(data):
    """The owner of the repository's guarded goal, read without claiming it."""
    info = parse(load(project_root(data) / GOAL))
    return info["owner"] if guarded(info) else ""


def on_prompt(data):
    prompt = data.get("prompt") or ""
    sid = session_of(data)
    if COMMAND.match(prompt):  # the skill is starting: tell it the id to write as owner (z-lab S05)
        note = session_note(sid, peek_owner(data))
        if note:
            emit("UserPromptSubmit", note.strip())
        return
    # A background task's completion arrives as a prompt made only of <task-notification> blocks; it is not something
    # the user typed. A notification quoted inside a real prompt is removed and the rest is kept.
    prompt = NOTIFICATION.sub("", prompt)
    goal, info, other = active_goal(data)
    if info is not None:
        emit("UserPromptSubmit", restore_note(goal, info) + (CORRECTION_NOTE if WORD.search(prompt) else ""))
    elif WORD.search(prompt):
        emit("UserPromptSubmit", ENTRY_NOTE + session_note(sid, other))


def on_session(data):
    goal, info, _ = active_goal(data)
    if info is not None:
        emit("SessionStart", restore_note(goal, info))


def on_ask(data):
    goal, info, _ = active_goal(data)
    if not engaged(info):
        return
    reason = (f"free-hands: asking the user is off while the goal is open ({len(info['items'])} items left in "
              f"{goal}). Decide with the brainstorming panel or yourself, record the decision under ## Decisions, "
              "and continue.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def on_shell(data):
    """Deny a shell command that breaks a hard limit while the goal is guarded (core scope: merge, remote deletion,
    deploy/publish/send). The limits last as long as the run, not as long as items are open."""
    goal, info, _ = active_goal(data)
    if info is None:
        return
    command = (data.get("tool_input") or {}).get("command")
    if isinstance(command, list):
        command = shlex.join(str(part) for part in command)
    if not isinstance(command, str) or not command.strip():
        return
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    declared = field(load(goal) or "", "default_branch") or None
    hit, source = shellguard.check(command, cwd, declared)
    if not hit:
        return
    category, part = hit
    branches = f" Default branch: {declared}." if declared else f" Default branch from {source}."
    if category == "unparsable":
        reason = ("free-hands: this command mentions a tool the hard limits cover but could not be parsed safely. "
                  "Split it into simple commands without heredocs or unbalanced quotes and run them one by one.")
    else:
        reason = (f"free-hands hard limit ({category}): `{part}` is never run during a free-hands run.{branches} "
                  "Do not reach the same effect another way. Mark the item `- [-] … — needs the user: <why>` in "
                  f"{goal} and continue with the other items.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def rewrite(goal, change):
    """Apply change(text, info) -> new text or None under the goal's lock; return the metadata now on disk, or None when
    nothing was written or the write cannot be confirmed."""
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
        updated = change(text, info) if guarded(info) else None
        if updated is None:
            return None
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
        return parse(load(goal))


def claim(goal, sid):
    """Write `owner: <sid>` into a guarded goal that has no owner yet; return the metadata on disk afterwards."""
    def change(text, info):
        if info["owner"]:
            return None
        return re.sub(r"^(iterations:.*)$", rf"\1\nowner: {sid}", text, count=1, flags=re.MULTILINE)
    return rewrite(goal, change) or parse(load(goal))


def bump(goal, sid=None):
    """Increment iterations under a lock, only while the goal is still this session's; return (new, max, open items)
    only if the new value reached the disk."""
    expected = {}

    def change(text, info):
        if not engaged(info) or (sid and info["owner"] != sid):
            return None
        expected["new"] = info["iterations"] + 1
        return re.sub(r"^iterations:.*$", f"iterations: {expected['new']}", text, count=1, flags=re.MULTILINE)
    after = rewrite(goal, change)
    if after is None or after["iterations"] != expected.get("new"):
        return None
    return after["iterations"], after["max"], after["items"]


def on_stop(data):
    goal, info, _ = active_goal(data)
    if not engaged(info):
        return
    result = bump(goal, session_of(data))
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
        {"prompt": on_prompt, "session": on_session, "ask": on_ask, "stop": on_stop,
         "shell": on_shell}.get(mode, lambda _: None)(data)
    except Exception:  # a hook never traps the session on its own failure
        return


if __name__ == "__main__":
    main()
    sys.exit(0)
