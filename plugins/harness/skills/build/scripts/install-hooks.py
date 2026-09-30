#!/usr/bin/env python3
"""Install the bundled prompt hook and model resolver without replacing unrelated host settings."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile


def prepare(root, host, source, resolver, replace):
    agent = root / ("." + host)
    config = agent / ("settings.json" if host == "claude" else "hooks.json")
    hook = agent / "hooks/inject-context.sh"
    script = agent / "scripts/latest-model.py"
    data = json.loads(config.read_text()) if config.exists() else {}
    if not isinstance(data, dict):
        raise ValueError(f"{config}: expected a JSON object")
    data = copy.deepcopy(data)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{config}: hooks must be an object")
    entries = hooks.setdefault("UserPromptSubmit", [])
    if not isinstance(entries, list):
        raise ValueError(f"{config}: UserPromptSubmit must be a list")
    command = ('bash "$CLAUDE_PROJECT_DIR/.claude/hooks/inject-context.sh"'
               if host == "claude" else
               'bash "$(git rev-parse --show-toplevel)/.codex/hooks/inject-context.sh"')
    seen = False
    merged = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
            raise ValueError(f"{config}: invalid UserPromptSubmit entry")
        kept = []
        for item in entry["hooks"]:
            if not isinstance(item, dict):
                raise ValueError(f"{config}: invalid hook declaration")
            ours = (entry.get("matcher", "") in ("", "*") and
                    item.get("type") == "command" and item.get("command") == command)
            if ours and seen:
                continue
            if ours:
                seen = True
            kept.append(item)
        if kept or not entry["hooks"]:
            merged.append({**entry, "hooks": kept})
    if not seen:
        merged.append({"hooks": [{"type": "command", "command": command}]})
    hooks["UserPromptSubmit"] = merged
    if hook.exists() and hook.read_bytes() != source and not replace:
        raise ValueError(f"{hook}: existing hook differs; review it before --replace-hook")
    if script.exists() and script.read_bytes() != resolver and not replace:
        raise ValueError(f"{script}: existing resolver differs; review it before --replace-hook")
    # Preserve original formatting when the semantic configuration is unchanged.
    original = config.read_bytes() if config.exists() else None
    config_bytes = original if original and json.loads(original) == data else (
        json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    return [(hook, source, 0o755),
            (script, resolver, 0o755),
            (config, config_bytes, config.stat().st_mode & 0o777 if config.exists() else 0o644)]


def write_atomic(path, content, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".harness-", dir=path.parent)
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
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--replace-hook", action="store_true",
                        help="replace an existing hook or resolver copy only after reviewing its customizations")
    args = parser.parse_args()
    root = args.project.resolve(strict=True)
    source = (Path(__file__).resolve().parent.parent / "assets/inject-context.sh").read_bytes()
    # This file sits three directories below the plugin root (skills/build/scripts/).
    resolver = (Path(__file__).resolve().parents[3] / "scripts/latest-model.py").read_bytes()
    hosts = ("claude", "codex") if args.host == "both" else (args.host,)
    plan = []
    # Validate every target before making the first change.
    for host in hosts:
        plan.extend(prepare(root, host, source, resolver, args.replace_hook))
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
    print(json.dumps({"host": args.host, "changed": [str(p.relative_to(root)) for p, _, _ in changed],
                      "activation": "Verify generated skill bodies and host hook trust separately."}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f"harness hook setup: {error}", file=sys.stderr)
        sys.exit(2)
