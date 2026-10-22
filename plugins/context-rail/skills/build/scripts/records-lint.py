#!/usr/bin/env python3
"""Read-only checks of a project's decision records against references/record-format.md.

usage: records-lint.py --project <dir>
Prints JSON. Exit 1 when a record has an orphan heading (names no governed file) or a decision block without a
Decision line. Governed files without a section are reported, not failed: most files need no record.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "assets" / "precedent-context.py"
spec = importlib.util.spec_from_file_location("precedent_context", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, required=True)
    a = ap.parse_args()
    root = str(a.project.resolve(strict=True))
    agent = os.path.join(root, ".claude") if os.path.isdir(os.path.join(root, ".claude")) else os.path.join(root, ".codex")
    cfg = hook.config(agent)
    tracked = [os.path.join(root, p) for p in subprocess.run(["git", "-C", root, "ls-files"], capture_output=True,
                                                             text=True).stdout.split("\n") if p]
    ext = re.compile(r"\.(" + "|".join(map(re.escape, cfg["extensions"])) + r")$")
    records = [p for p in tracked if os.path.basename(p) == cfg["recordFile"]]
    governed = {}
    for f in tracked:
        if ext.search(f):
            r = hook.nearest_record(f, root, cfg["recordFile"])
            if r:
                governed.setdefault(r, []).append(f)
    report = {"records": len(records), "orphan_headings": [], "blocks_without_decision": [],
              "governed_files": sum(len(v) for v in governed.values()), "governed_without_section": 0}
    label = cfg["fieldLabels"][0]
    for r in records:
        lines = open(r, encoding="utf-8").read().split("\n")
        rel = os.path.relpath(r, root)
        files = governed.get(r, [])
        for i, line in enumerate(lines, 1):
            if line.startswith("## ") and not any(
                    hook.matches(n, os.path.dirname(r), f) for n in hook.heading_names(line) for f in files):
                report["orphan_headings"].append(f"{rel}:{i}")
        block = None
        for i, line in enumerate(lines + ["## end"], 1):
            if line.startswith(("### ", "## ")):
                if block and not block[1]:
                    report["blocks_without_decision"].append(f"{rel}:{block[0]}")
                block = (i, False) if line.startswith("### ") else None
            elif block and line.startswith(f"- {label}:"):
                block = (block[0], True)
        report["governed_without_section"] += sum(1 for f in files if not hook.sections(r, f))
    print(json.dumps(report, indent=2))
    return 1 if report["orphan_headings"] or report["blocks_without_decision"] else 0


if __name__ == "__main__":
    sys.exit(main())
