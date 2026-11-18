#!/usr/bin/env python3
"""free-hands isolated estimator. Usage: estimator.py <.free-hands folder> <repository root> <claude CLI>

Started by the owner session's PostToolUse hook as a detached process (guard.py), never by the main agent: the main
agent's context holds no estimate. It asks a separate headless Claude Code session (Haiku, safe mode — no hooks,
plugins' hooks or CLAUDE.md; no saved session; read-only tools) how long each open checklist item without an estimate
will take, and appends the answers to `.free-hands/estimates.jsonl`. One estimator runs at a time per goal folder; it
loops while the checklist keeps gaining unestimated items. Every failure is logged to `estimator.log` and leaves no
estimate — the dashboard then shows no expected finish for those items.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eta  # noqa: E402

MODEL = "haiku"
EFFORT = "low"
TIMEOUT = 180
BUDGET = "0.25"
ROUNDS = 3
PROMPT = """You estimate how long an autonomous coding agent (Claude, working alone in this repository with shell, read
and edit tools, running tests and fixing what fails) will take for each checklist item below, in wall-clock minutes
from starting the item to finishing its check. Read the code you need first; change nothing. Then answer with exactly
one JSON object and nothing else:
{"items": [{"n": <item number>, "minutes": <number>, "category": "<one of docs, fix, feature, refactor, test, research, ops>"}]}

Goal: %s

Checklist:
%s"""


def command(execpath, prompt):
    """The isolated session (z-lab free-hands-lab eta-isolated-probes I03, I04)."""
    return [execpath, "-p", prompt, "--safe-mode", "--no-session-persistence", "--model", MODEL, "--effort", EFFORT,
            "--tools", "Read", "Glob", "Grep", "--allowedTools", "Read", "Glob", "Grep", "--output-format", "json",
            "--max-budget-usd", BUDGET]


def goal_sentence(text):
    lines = eta.section(text, "Goal").strip().splitlines()
    return lines[0].strip() if lines else ""


def ask(execpath, cwd, goal, keys):
    """[(key, minutes, category)] for the numbered keys, and the model that answered; raises on any failure."""
    listing = "\n".join(f"{n}. {key}" for n, key in enumerate(keys, 1))
    env = dict(os.environ, FREE_HANDS_ROLE="estimator", CXC_MODE="off")
    proc = subprocess.run(command(execpath, PROMPT % (goal, listing)), cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"exit {proc.returncode}: {proc.stderr[-300:]}")
    result = json.loads(proc.stdout)
    text = result.get("result") or ""
    answer = json.loads(text[text.index("{"):text.rindex("}") + 1])
    models = list((result.get("modelUsage") or {}).keys())
    rows = []
    for entry in answer.get("items") or []:
        n, minutes = entry.get("n"), entry.get("minutes")
        if isinstance(n, int) and 1 <= n <= len(keys) and eta.usable(minutes):
            category = str(entry.get("category") or "").lower()
            rows.append((keys[n - 1], float(minutes), category if category in eta.CATEGORIES else None))
    return rows, (models[0] if models else MODEL), result.get("total_cost_usd")


def main():
    folder, cwd = Path(sys.argv[1]), Path(sys.argv[2])
    execpath = sys.argv[3] if len(sys.argv) > 3 else None
    if not execpath or not folder.is_dir():
        return
    with open(folder / "estimator.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return  # one already runs; it looks again before it exits
        for _ in range(ROUNDS):
            try:
                text = (folder / "goal.md").read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                return
            run, keys = eta.unestimated(folder, text)
            if not keys:
                return
            started = time.time()
            try:
                rows, model, cost = ask(execpath, cwd, goal_sentence(text), keys)
            except Exception as error:  # timeout, auth, a reply that is not JSON: log it, write no estimate
                rows, model, cost = [], MODEL, None
                with open(folder / "estimator.log", "a", encoding="utf-8") as log:
                    log.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "keys": len(keys),
                                          "error": str(error)[:500]}) + "\n")
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            seconds = round(time.time() - started, 1)
            answered = {key for key, _, _ in rows}
            # an item the reply left out, or a failed call, is recorded as asked: it is not asked again in this run
            rows += [(key, None, None) for key in keys if key not in answered]
            with open(folder / eta.ESTIMATES, "a", encoding="utf-8") as out:
                out.write("".join(json.dumps({"v": 1, "at": stamp, "run": run, "item": eta.ref(key), "minutes": minutes,
                                              "cat": category, "estimator": MODEL, "model": model,
                                              "seconds": seconds, "cost_usd": cost}) + "\n"
                                  for key, minutes, category in rows))
            if len(answered) < len(keys):
                return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
