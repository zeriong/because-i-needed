"""free-hands ETA: per-item estimates in the goal file, hook-measured actual times, and the expected finish.

The agent ends each checklist item with its own estimate, `(~<minutes>m <category>)`. Hooks of the owner session call
observe(): it keeps an active-time clock (gaps after a turn that really ended are not counted), and when an item turns
`[x]` or `[-]` it appends the active time since the previous completion to `.free-hands/timings.jsonl`, the project's
own record. predict() turns the open items' estimates into minutes: a factor per model family and category shipped in
eta-baseline.json (measured in z-lab), times a project factor learned from that record. Every failure means no record
and no ETA, never an error the session sees.
"""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time

STATE = "eta.json"
HISTORY = "timings.jsonl"
BASELINE = Path(__file__).resolve().parent / "eta-baseline.json"
CATEGORIES = ("docs", "fix", "feature", "refactor", "test", "research", "ops")
ESTIMATE = re.compile(r"\(~\s*(\d+(?:\.\d+)?)\s*m(?:in)?\b[ ,]*([A-Za-z]*)\s*\)")
ITEM = re.compile(r"^\s*- \[([ xX-])\]\s?(.*)$")
NEEDS_USER = re.compile(r"\s+—\s+needs the user\b.*$")
FAMILIES = ("fable", "opus", "sonnet", "haiku")
CAP = 20 * 60          # a quiet gap longer than this is not work, unless a tool call ran that long
FLOOR = 0.1            # an overrunning item keeps this share of its prediction
RECENT = 60            # project factor: the newest records only
PRIOR = 3              # project factor: weight of "no adjustment" against the project's own records
TAIL = 256 * 1024      # bytes read from the end of the transcript (the model) and of the record
LONGEST = 24 * 60      # minutes: an estimate or a measured item beyond a day is not a usable record


def checklist(text):
    """[(mark, key, minutes or None, category or None)] for `- [ ]`/`[x]`/`[-]` lines under `## Checklist`, outside
    fenced code (the same scope guard.open_items uses). A text that repeats gets ` #2`, ` #3` so each line keeps its
    own key."""
    items, in_checklist, fence, seen = [], False, None, {}
    for line in (text or "").splitlines():
        stripped = line.strip()
        if fence is None:
            opening = re.match(r"(`{3,}|~{3,})", stripped)
            if opening:
                fence = opening.group(1)
                continue
        else:
            closing = re.match(r"(`{3,}|~{3,})\s*$", stripped)
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence):
                fence = None
            continue
        if re.match(r"^##\s", line):
            in_checklist = re.match(r"^##\s+Checklist\s*$", line) is not None
            continue
        match = ITEM.match(line) if in_checklist else None
        if not match:
            continue
        body = match.group(2)
        estimate = ESTIMATE.search(body)
        minutes = category = None
        if estimate:
            value = float(estimate.group(1))
            minutes = value if 0 < value <= LONGEST else None
            word = estimate.group(2).lower()
            category = word if minutes and word in CATEGORIES else None
            body = body[:estimate.start()]
        key = NEEDS_USER.sub("", body).strip()
        if key:
            seen[key] = seen.get(key, 0) + 1
            items.append((match.group(1).lower(), key if seen[key] == 1 else f"{key} #{seen[key]}", minutes, category))
    return items


def goal_id(text):
    """A run's identity: its `## Goal` section. A new goal (the old file renamed) starts a new clock."""
    match = re.search(r"^##\s+Goal\s*$(.*?)(?=^##\s|\Z)", text or "", re.MULTILINE | re.DOTALL)
    return hashlib.sha256((match.group(1).strip() if match else "").encode()).hexdigest()[:16]


def family(model):
    name = model.lower() if isinstance(model, str) else ""
    return next((f for f in FAMILIES if f in name), None)


def number(value, default=0.0):
    """A finite float from a state field, else the default (a hand-edited state must not stop the clock)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return default


def tail_lines(path):
    """The lines in the last TAIL bytes of a file (a partial first line is dropped), or [] when unreadable."""
    if not isinstance(path, (str, Path)) or not str(path):
        return []
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - TAIL))
            lines = handle.read().decode("utf-8", "replace").splitlines()
    except (OSError, ValueError):
        return []
    return lines[1:] if size > TAIL else lines


def model_from_transcript(path):
    """The model of the newest assistant message in the session transcript (hook inputs carry no model; z-lab
    eta-probes T01)."""
    for line in reversed(tail_lines(path)):
        if '"assistant"' not in line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") if isinstance(entry, dict) and entry.get("type") == "assistant" else None
        model = message.get("model") if isinstance(message, dict) else None
        if isinstance(model, str) and model and not model.startswith("<"):
            return model
    return None


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path, data):
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".tmp.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class Locked:
    """An exclusive lock on `.free-hands/eta.lock`; acquired is False after a 2 s timeout (the caller then skips)."""

    def __init__(self, folder):
        self.path, self.handle, self.acquired = folder / "eta.lock", None, False

    def __enter__(self):
        self.handle = open(self.path, "a")
        deadline = time.monotonic() + 2
        while True:
            try:
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.acquired = True
                return self
            except BlockingIOError:
                if time.monotonic() > deadline:
                    return self
                time.sleep(0.02)

    def __exit__(self, *exc):
        self.handle.close()


def fresh(goal, now):
    return {"goal": goal, "started": now, "active": 0.0, "mark": 0.0, "last": now, "idle": False, "items": {},
            "model": None, "effort": None}


def advance(state, now, event, data):
    """Add the gap since the previous event to the active clock. Not counted: the gap after a turn that ended (an
    allowed Stop), before a new session, or before a prompt (the user's time — a turn interrupted with Esc sends no
    Stop); a gap over CAP counts only as long as the tool call reports it ran."""
    last = number(state.get("last"), None)
    gap = max(0.0, now - last) if last is not None else 0.0
    starting = event == "prompt" or (event == "session" and data.get("source") in ("startup", "resume", "clear"))
    active = number(state.get("active"))
    if not state.get("idle") and not starting:
        if gap > CAP:
            ran = number(data.get("duration_ms"))
            gap = min(gap, ran / 1000.0) if ran > 0 else 0.0
        active += gap
    state["active"] = active
    state["last"] = max(now, last) if last is not None else now  # a late process never moves the clock back
    state["idle"] = False


def share(finished, elapsed):
    """Split the active time since the previous completion among the items finished in one edit, by estimate."""
    weights = [minutes or 0 for _, minutes, _, _ in finished]
    total = sum(weights)
    if total <= 0 or 0 in weights:
        return [elapsed / len(finished)] * len(finished)
    return [elapsed * w / total for w in weights]


def same_run(state, goal, text):
    """The clock belongs to this goal: the same `## Goal` text, or — after the agent rewords the goal — most items in
    common both ways. One shared boilerplate item ("run the tests") does not carry a finished goal's clock into the
    next one."""
    if state.get("goal") == goal:
        return True
    keys, known = {key for _, key, _, _ in checklist(text)}, set(state["items"])
    shared = len(keys & known)
    return shared * 2 > len(keys) and shared * 2 > len(known)


def observe(folder, text, event, data, now=None, ended=False):
    """Record one hook event of the owner session. `ended` marks a Stop that lets the turn end. The goal file is read
    again under the lock, so a hook process that waited for it never records an older checklist."""
    if not folder.is_dir():
        return
    with Locked(folder) as lock:
        if not lock.acquired:
            return
        try:
            text = (folder / "goal.md").read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass
        now = time.time() if now is None else now
        state_path = folder / STATE
        goal = goal_id(text)
        state = read_json(state_path)
        if not state or not isinstance(state.get("items"), dict) or not same_run(state, goal, text):
            state = fresh(goal, now)
        state["goal"] = goal
        advance(state, now, event, data)
        effort = data.get("effort")
        if isinstance(effort, dict) and isinstance(effort.get("level"), str):
            state["effort"] = effort["level"]
        finished = []
        known = state.setdefault("items", {})
        running = bool(known)  # a run already under way: an item that first appears finished was done just now
        for mark, key, minutes, category in checklist(text):
            previous = known.get(key)
            if not isinstance(previous, dict):
                known[key] = {"mark": mark, "est": minutes, "cat": category}
                if running and mark in ("x", "-"):
                    finished.append((key, minutes, category, mark))
                continue
            if previous.get("est") is None and minutes is not None:
                previous.update(est=minutes, cat=category)
            if previous.get("mark") == " " and mark in ("x", "-"):
                finished.append((key, previous.get("est"), previous.get("cat"), mark))
            previous["mark"] = mark
        if finished or not isinstance(state.get("model"), str):
            found = model_from_transcript(data.get("transcript_path"))
            state["model"] = found or (state.get("model") if isinstance(state.get("model"), str) else None)
        if finished:
            elapsed = max(0.0, state["active"] - number(state.get("mark")))
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
            rows = []
            for (key, minutes, category, mark), seconds in zip(finished, share(finished, elapsed)):
                rows.append({"v": 1, "at": stamp, "goal": goal, "item": key[:200], "cat": category,
                             "est_min": minutes, "actual_min": round(seconds / 60.0, 2), "batch": len(finished),
                             "outcome": "done" if mark == "x" else "skipped", "model": state["model"],
                             "family": family(state["model"]), "effort": state.get("effort")})
            with open(folder / HISTORY, "a", encoding="utf-8") as history:
                history.write("".join(json.dumps(row) + "\n" for row in rows))
            state["mark"] = state["active"]
        if ended:
            state["idle"] = True
        write_json(state_path, state)


def pending(folder, text):
    """True while the clock of this goal still holds an open item (the last item's edit may also end the run)."""
    state = read_json(folder / STATE)
    if not state or not isinstance(state.get("items"), dict) or not same_run(state, goal_id(text), text):
        return False
    keys = {key for _, key, _, _ in checklist(text)}  # an item renamed mid-run leaves its old key open: not counted
    return any(isinstance(item, dict) and item.get("mark") == " " and key in keys
               for key, item in state["items"].items())


def baseline():
    data = read_json(BASELINE) or {}
    return data.get("families") if isinstance(data.get("families"), dict) else {}


def factor(base, fam, category):
    """The family's factor for the category, else for all its items; a family without one takes `default`."""
    for cell in (base.get(fam) if fam else None, base.get("default")):
        if isinstance(cell, dict):
            for key in (category, "all"):
                value = cell.get(key) if key else None
                if isinstance(value, (int, float)) and value > 0:
                    return float(value)
    return 1.0


def usable(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value <= LONGEST


def records(folder):
    """The project's finished items with both an estimate and a measured time, newest last. A hand-edited or broken
    row (`Infinity`, `NaN`, zero, beyond a day) is skipped."""
    rows = []
    for line in tail_lines(folder / HISTORY):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("outcome") == "done" and usable(row.get("est_min")) \
                and usable(row.get("actual_min")):
            rows.append({"est_min": row["est_min"], "actual_min": row["actual_min"],
                         "family": row.get("family") if isinstance(row.get("family"), str) else None,
                         "cat": row.get("cat") if isinstance(row.get("cat"), str) else None})
    return rows[-RECENT:]


def project_factor(rows, base):
    """How much longer (or shorter) this project's items took than the shipped baseline predicted — the project's
    complexity — shrunk toward 1 while the record is small."""
    residuals = [math.log(r["actual_min"] / (r["est_min"] * factor(base, r.get("family"), r.get("cat"))))
                 for r in rows]
    return math.exp(sum(residuals) / (len(residuals) + PRIOR)) if residuals else 1.0


def predict(folder, text, now=None):
    """{"eta": epoch seconds, "minutes": remaining, "unestimated": n} for the open items, or None when no open item
    has an estimate."""
    now = time.time() if now is None else now
    open_items = [(key, minutes, category) for mark, key, minutes, category in checklist(text) if mark == " "]
    estimated = [(key, minutes, category) for key, minutes, category in open_items if minutes]
    if not estimated:
        return None
    state = read_json(folder / STATE)
    if state and (not isinstance(state.get("items"), dict) or not same_run(state, goal_id(text), text)):
        state = None
    base = baseline()
    fam = family(state.get("model")) if state else None
    adjust = project_factor(records(folder), base)
    elapsed = 0.0
    known = state.get("items") if state and isinstance(state.get("items"), dict) else {}
    # an item the goal file shows finished but the clock has not recorded yet finished just now (the dashboard may
    # read the file before the PostToolUse hook has run): the next item has used no time yet
    unrecorded = any(isinstance(known.get(key), dict) and known[key].get("mark") == " " and mark in ("x", "-")
                     for mark, key, _, _ in checklist(text))
    if state and not unrecorded:
        last = number(state.get("last"), None)
        live = max(0.0, now - last) if last is not None else 0.0
        elapsed = number(state.get("active")) - number(state.get("mark"))
        elapsed += live if not state.get("idle") and live <= CAP else 0.0
    total = 0.0
    for index, (key, minutes, category) in enumerate(estimated):
        expected = minutes * factor(base, fam, category) * adjust
        if index == 0 and open_items[0][0] == key:  # the item in progress has already used part of its time
            expected = max(expected - elapsed / 60.0, expected * FLOOR)
        total += expected
    if not math.isfinite(total) or total > 365 * LONGEST:  # a broken state must not reach the clock
        return None
    return {"eta": now + total * 60.0, "minutes": total, "unestimated": len(open_items) - len(estimated),
            "family": fam, "project": adjust}


def clock(epoch, now=None):
    """A local wall-clock time, with the date when it is not today."""
    now = time.time() if now is None else now
    local, today = time.localtime(epoch), time.localtime(now)
    same = (local.tm_year, local.tm_yday) == (today.tm_year, today.tm_yday)
    return time.strftime("%H:%M" if same else "%m-%d %H:%M", local)


def duration(minutes):
    minutes = max(1, int(round(minutes)))
    return f"{minutes}m" if minutes < 60 else f"{minutes // 60}h{minutes % 60:02d}m"
