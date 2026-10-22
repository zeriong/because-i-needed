#!/usr/bin/env python3
"""Measure the always-loaded instruction files of a project in lines, characters and bytes.

usage: resident-size.py --project <dir> [--compare <earlier.json>]
Prints JSON. With --compare, also prints the delta per file and in total, and exits 1 if the total grew in
characters or in bytes (the rail's rule: resident context is only replaced or shrunk).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

NAMES = ("CLAUDE.md", "AGENTS.md")


def resident_files(root):
    tracked = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True).stdout.split("\n")
    found = {p for p in tracked if p and Path(p).name in NAMES}
    for extra in (".claude/CLAUDE.md", "CLAUDE.local.md"):
        if (root / extra).is_file():
            found.add(extra)
    return sorted(found)


def measure(root):
    out = {}
    for rel in resident_files(root):
        data = (root / rel).read_bytes()
        text = data.decode("utf-8", errors="replace")
        out[rel] = {"lines": text.count("\n"), "chars": len(text), "bytes": len(data)}
    out["_total"] = {k: sum(v[k] for f, v in out.items()) for k in ("lines", "chars", "bytes")}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--compare", type=Path)
    a = ap.parse_args()
    now = measure(a.project.resolve(strict=True))
    if not a.compare:
        print(json.dumps(now, indent=2))
        return 0
    before = json.loads(a.compare.read_text())
    keys = sorted(set(before) | set(now))
    zero = {"lines": 0, "chars": 0, "bytes": 0}
    delta = {k: {m: now.get(k, zero)[m] - before.get(k, zero)[m] for m in zero} for k in keys}
    grew = delta["_total"]["chars"] > 0 or delta["_total"]["bytes"] > 0
    print(json.dumps({"now": now, "delta": delta, "grew": grew}, indent=2))
    return 1 if grew else 0


if __name__ == "__main__":
    sys.exit(main())
