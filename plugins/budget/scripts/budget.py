#!/usr/bin/env python3
"""budget settings and state. Usage: budget.py set <1-100> | off | status [--json]

The threshold is user-level, shared by Claude Code and Codex: $XDG_CONFIG_HOME/because-i-needed/budget.json (default
~/.config). Runtime state lives beside it under budget/: pending/<session>.json ({"open": true, …} while the session's
question is open — free-hands reads it), acks/<session>.json once its user said yes for a window, usage.json with the
last window a host reported.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import time

STATE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "because-i-needed"
CONFIG = STATE / "budget.json"
RUNTIME = STATE / "budget"
WINDOWS = {"five_hour": "5h", "seven_day": "7d"}
SESSION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    tmp.write_text(json.dumps(value))
    os.replace(tmp, path)


def threshold():
    """The configured percent (1-100), or None when the gate is off or the file is malformed."""
    value = (read_json(CONFIG) or {}).get("percent")
    return value if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 100 else None


def reset_seconds(value):
    """A window's reset time as epoch seconds: Codex reports seconds, Claude Code an ISO 8601 string."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def same_window(a, b):
    """Two readings of one window: Codex's reset time moves by a second between records (z-lab budget-lab run-0.1.0
    XB2), while a new window resets five hours or seven days later."""
    a, b = reset_seconds(a), reset_seconds(b)
    return a is not None and b is not None and abs(a - b) <= 600


def session_file(kind, sid):
    return RUNTIME / kind / f"{sid}.json"


def record_usage(kind, used, resets_at, host):
    write_json(RUNTIME / "usage.json", {"kind": kind, "used": used, "resets_at": resets_at, "host": host,
                                        "at": int(time.time())})


def status():
    n = threshold()
    usage = read_json(RUNTIME / "usage.json") or {}
    detail = None
    if usage.get("kind") in WINDOWS and isinstance(usage.get("used"), (int, float)):
        detail = f"{WINDOWS[usage['kind']]} now {usage['used']:g}%"
    value = f"{n}%" if n else "off"
    return {"value": value, "source": "global" if n else "default", "project": None, "global": value if n else None,
            "detail": detail}


def main(argv):
    command = argv[0] if argv else "status"
    if command == "set" and len(argv) == 2 and argv[1].isdigit() and 1 <= int(argv[1]) <= 100:
        write_json(CONFIG, {"percent": int(argv[1])})
        print(f"budget: stop and ask at {argv[1]}% of the usage window (Claude Code: 5-hour, Codex: 7-day). "
              f"Saved in {CONFIG}.")
    elif command == "off" and len(argv) == 1:
        CONFIG.unlink(missing_ok=True)
        print(f"budget: off. Removed {CONFIG}.")
    elif command == "status" and argv[1:] in ([], ["--json"]):
        state = status()
        if argv[1:] == ["--json"]:
            print(json.dumps(state))
        else:
            line = f"budget: {state['value']}" + (f" ({state['detail']})" if state["detail"] else "")
            print(line + ("" if state["value"] != "off" else " — set one with `budget:mode <1-100>`"))
    else:
        print("usage: budget.py set <1-100> | off | status [--json]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
