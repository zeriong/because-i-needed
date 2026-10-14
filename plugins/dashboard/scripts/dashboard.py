#!/usr/bin/env python3
"""Collect the state every enabled because-i-needed plugin declares in its dashboard.json (root Rule 11).

Usage: dashboard.py --host claude|codex [--enabled name@market,...] [--cwd DIR] [--json]

Plugins are found where each host records installs: Claude Code's installed_plugins.json (enabled per --enabled, or
the settings files when it is absent), Codex's config.toml and plugin cache. BECAUSE_I_NEEDED_PLUGIN_DIRS adds plugin
folders loaded from disk (`--plugin-dir`), counted as enabled. Each declared status command runs read-only with the
project as its working directory; a command that fails, times out or prints something else shows as an error.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

MARKET = "because-i-needed"
SELF = "dashboard"
TIMEOUT = 2


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def version_key(name):
    return [int(part) if part.isdigit() else part for part in re.split(r"[.-]", name)]


def claude_enabled(cwd):
    """enabledPlugins merged from the user, project and local settings files (later wins)."""
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    enabled = {}
    for path in (home / "settings.json", Path(cwd) / ".claude" / "settings.json",
                 Path(cwd) / ".claude" / "settings.local.json"):
        enabled.update((read_json(path) or {}).get("enabledPlugins") or {})
    return {name for name, on in enabled.items() if on is True}


def claude_roots(enabled, cwd):
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    records = (read_json(home / "plugins" / "installed_plugins.json") or {}).get("plugins") or {}
    roots = {}
    for key, entries in records.items():
        name, _, market = key.partition("@")
        if market != MARKET or key not in enabled or not isinstance(entries, list):
            continue
        local = [e for e in entries if isinstance(e, dict) and e.get("projectPath") and
                 Path(cwd).resolve().is_relative_to(Path(e["projectPath"]).resolve())]
        chosen = (local or [e for e in entries if isinstance(e, dict)])[:1]
        if chosen and chosen[0].get("installPath"):
            roots[name] = Path(chosen[0]["installPath"])
    return roots


def codex_roots():
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    try:
        lines = (home / "config.toml").read_text().splitlines()
    except OSError:
        lines = []
    enabled, table = set(), None
    for line in lines:
        header = re.match(r'^\s*\[\s*plugins\."([^"]+)"\s*\]\s*$', line)
        if header:
            table = header.group(1)
            continue
        if line.strip().startswith("["):
            table = None
        elif table and re.match(r"^\s*enabled\s*=\s*true\s*(#.*)?$", line):
            enabled.add(table)
    roots = {}
    for key in enabled:
        name, _, market = key.partition("@")
        cache = home / "plugins" / "cache" / MARKET / name
        if market == MARKET and cache.is_dir():
            versions = sorted((p for p in cache.iterdir() if p.is_dir()), key=lambda p: version_key(p.name))
            if versions:
                roots[name] = versions[-1]
    return roots


def extra_roots():
    roots = {}
    for folder in filter(None, os.environ.get("BECAUSE_I_NEEDED_PLUGIN_DIRS", "").split(os.pathsep)):
        manifest = read_json(Path(folder) / ".claude-plugin" / "plugin.json") or {}
        if manifest.get("name"):
            roots[manifest["name"]] = Path(folder)
    return roots


def run_status(root, argv, cwd):
    argv = [str(root / a) if i and (root / a).exists() else a for i, a in enumerate(argv)]
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT,
                              stdin=subprocess.DEVNULL)
        state = json.loads(proc.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"value": "error", "source": "default", "project": None, "global": None, "error": True}
    if proc.returncode != 0 or not isinstance(state, dict) or not isinstance(state.get("value"), str):
        return {"value": "error", "source": "default", "project": None, "global": None, "error": True}
    return state


def collect(host, enabled, cwd):
    roots = claude_roots(enabled, cwd) if host == "claude" else codex_roots()
    roots.update(extra_roots())
    entries = []
    for name in sorted(roots):
        if name == SELF:
            continue
        declared = read_json(roots[name] / "dashboard.json") or {}
        for entry in declared.get("entries") or []:
            if isinstance(entry, dict) and isinstance(entry.get("label"), str) and isinstance(entry.get("status"), list):
                entries.append({"plugin": name, "label": entry["label"], **run_status(roots[name], entry["status"], cwd)})
    return entries


def line(entries):
    parts = []
    for e in entries:
        where = f" ({e['source']})" if e.get("source") in ("env", "project") else ""
        detail = f" · {e['detail']}" if e.get("detail") else ""
        parts.append(f"{e['label']} {e['value']}{where}{detail}")
    return f"{MARKET} │ " + " │ ".join(parts) if parts else ""


def main():
    parser = argparse.ArgumentParser(description="Show the state because-i-needed plugins declare.")
    parser.add_argument("--host", choices=("claude", "codex"), required=True)
    parser.add_argument("--enabled", help="comma-separated plugin keys (name@marketplace); default: settings files")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    enabled = set(filter(None, (args.enabled or "").split(","))) if args.enabled is not None else claude_enabled(args.cwd)
    entries = collect(args.host, enabled, args.cwd)
    if args.json:
        print(json.dumps({"entries": entries, "line": line(entries)}))
    elif entries:
        print(line(entries))
        for e in entries:
            levels = f"project: {e.get('project') or 'unset'}   global: {e.get('global') or 'unset'}"
            print(f"  {e['label']}: {e['value']} (source: {e['source']})   {levels}")
    else:
        print(f"No enabled {MARKET} plugin declares a state to show.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
