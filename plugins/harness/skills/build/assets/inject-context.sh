#!/usr/bin/env bash
# Copy to the target project's .claude/hooks/ or .codex/hooks/ directory.
# Resolves generated skills from this file, independent of the invocation cwd.
set -uo pipefail
agent_dir="$(cd "$(dirname "$0")/.." && pwd)" || exit 1
exec python3 -c '
import json
from pathlib import Path
import re
import sys

agent_dir = Path(sys.argv[1])
try:
    payload = json.load(sys.stdin)
except (ValueError, OSError):
    sys.exit(0)
prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""
if not isinstance(prompt, str):
    sys.exit(0)

bypass = bool(re.search(r"^\s*!|harness\s*빼고|\b(?:without|skip|no)\s+harness\b", prompt, re.I))
skills = agent_dir.parent / ".agents" / "skills" if agent_dir.name == ".codex" else agent_dir / "skills"
bodies = []
for name in (("project-rules",) if bypass else ("project-rules", "harness-engineering")):
    source = skills / name / "SKILL.md"
    try:
        body = source.read_text(encoding="utf-8")
    except OSError:
        bodies.append(f"HARNESS SETUP INCOMPLETE: missing {source}. Repair before claiming the harness is active.")
        continue
    body = re.sub(r"\A---\r?\n.*?\r?\n---(?:\r?\n|\Z)", "", body, count=1, flags=re.S)
    bodies.append(body.strip())
if bypass:
    bodies.append("BYPASS MODE: skip the harness workflow for this request only.")
context = "\n\n".join(bodies)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}, ensure_ascii=False))
' "$agent_dir"
