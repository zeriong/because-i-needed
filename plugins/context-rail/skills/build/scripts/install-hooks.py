#!/usr/bin/env python3
"""Install the context-rail arrival hook into a project without replacing unrelated host settings."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

HOOK = "precedent-context.py"
WIRING = {
    "claude": {
        "config": "settings.json",
        "command": f'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/{HOOK}"',
        "events": (("PostToolUse", "Read|Edit|Write|MultiEdit|Bash"), ("PostToolUseFailure", "Bash")),
    },
    # Codex has no failure event; a failed shell call still fires PostToolUse (z-lab platform-2.1.306-0.163.0 P6).
    "codex": {
        "config": "hooks.json",
        "command": f'python3 "$(git rev-parse --show-toplevel)/.codex/hooks/{HOOK}"',
        "events": (("PostToolUse", None),),
    },
}


def merge(hooks, event, matcher, command, config):
    entries = hooks.setdefault(event, [])
    if not isinstance(entries, list):
        raise ValueError(f"{config}: {event} must be a list")
    seen, merged = False, []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
            raise ValueError(f"{config}: invalid {event} entry")
        kept = []
        for item in entry["hooks"]:
            if not isinstance(item, dict):
                raise ValueError(f"{config}: invalid hook declaration")
            ours = item.get("type") == "command" and item.get("command") == command
            if ours and (seen or entry.get("matcher") != matcher):
                continue
            seen |= ours
            kept.append(item)
        if kept or not entry["hooks"]:
            merged.append({**entry, "hooks": kept})
    if not seen:
        entry = {"hooks": [{"type": "command", "command": command}]}
        if matcher:
            entry = {"matcher": matcher, **entry}
        merged.append(entry)
    hooks[event] = merged


def prepare(root, host, source, extensions, replace):
    agent = root / ("." + host)
    wiring = WIRING[host]
    config = agent / wiring["config"]
    hook = agent / "hooks" / HOOK
    data = json.loads(config.read_text()) if config.exists() else {}
    if not isinstance(data, dict):
        raise ValueError(f"{config}: expected a JSON object")
    data = copy.deepcopy(data)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{config}: hooks must be an object")
    for event, matcher in wiring["events"]:
        merge(hooks, event, matcher, wiring["command"], config)
    if hook.exists() and hook.read_bytes() != source and not replace:
        raise ValueError(f"{hook}: existing hook differs; review it before --replace-hook")
    original = config.read_bytes() if config.exists() else None
    config_bytes = original if original and json.loads(original) == data else (
        json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    plan = [(hook, source, 0o755),
            (config, config_bytes, config.stat().st_mode & 0o777 if config.exists() else 0o644)]
    if extensions:
        settings = agent / "context-rail.json"
        current = json.loads(settings.read_text()) if settings.exists() else {}
        if not isinstance(current, dict):
            raise ValueError(f"{settings}: expected a JSON object")
        wanted = {**current, "extensions": extensions}
        if wanted != current:
            plan.append((settings, (json.dumps(wanted, indent=2) + "\n").encode(), 0o644))
    return plan


def write_atomic(path, content, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".context-rail-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--host", choices=("claude", "codex", "both"), required=True)
    parser.add_argument("--extensions", help="comma-separated source extensions to govern, e.g. ts,tsx,css")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--replace-hook", action="store_true",
                        help="replace an existing hook copy only after reviewing its customizations")
    args = parser.parse_args()
    root = args.project.resolve(strict=True)
    source = (Path(__file__).resolve().parent.parent / "assets" / HOOK).read_bytes()
    extensions = [e.strip().lstrip(".") for e in args.extensions.split(",") if e.strip()] if args.extensions else None
    hosts = ("claude", "codex") if args.host == "both" else (args.host,)
    plan = []
    # Validate every target before making the first change.
    for host in hosts:
        plan.extend(prepare(root, host, source, extensions, args.replace_hook))
    changed = [(p, b, mode) for p, b, mode in plan
               if not p.exists() or p.read_bytes() != b or p.stat().st_mode & 0o777 != mode]
    if args.check or args.dry_run:
        print(json.dumps({"host": args.host, "changes": [str(p.relative_to(root)) for p, _, _ in changed]}))
        return 1 if args.check and changed else 0
    written = []
    try:
        for path, content, mode in changed:
            previous = (path.read_bytes(), path.stat().st_mode & 0o777) if path.exists() else None
            write_atomic(path, content, mode)
            written.append((path, previous))
    except OSError:
        for path, previous in reversed(written):
            if previous is None:
                path.unlink()
            else:
                write_atomic(path, *previous)
        raise
    result = {"host": args.host, "changed": [str(p.relative_to(root)) for p, _, _ in changed]}
    if "codex" in hosts:
        result["activation"] = "Codex runs the hook only after it is trusted in /hooks."
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f"context-rail hook setup: {error}", file=sys.stderr)
        sys.exit(2)
