#!/usr/bin/env python3
"""peer-coding settings: the model family and effort each worker lane and reviewer uses.

Resolution per setting (first match wins):
  1. its CXC_* env var                         — per-shell override
  2. <repo>/.claude-x-codex/settings           — this project
  3. Claude Code /config                       — pluginConfigs in <claude config dir>/settings.json
  4. ~/.config/claude-x-codex/settings         — your default everywhere
  5. the default below

A file holds `key=value` lines (keys as in SETTINGS); a value that fails validation counts as unset. A /config value
outside the declared options counts as unset, as Claude Code itself treats it. Session-only Claude settings
(`--settings`, managed settings) are not read.

Usage:
  settings.py get <setting>                       → the value in effect
  settings.py env                                 → `CXC_…=…` assignments for a dispatch shell (eval); not
                                                    exported, so a later load in the same shell reads the stores again
  settings.py status                              → every setting, its value and where it came from
  settings.py status --json [--role worker|reviewer]
                                                  → all levels, or one dashboard entry (root Rule 11)
  settings.py set <setting> <value> [--global]    → writes the project file (or the global one)
  settings.py unset <setting> [--global]          → removes it from the project file (or the global one)
"""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

EFFORTS = ("low", "medium", "high", "xhigh", "max")
# name, file and userConfig key, env var, default, the values /config offers (plugin.json userConfig options)
SETTINGS = (
    ("codex-worker", "codex_worker", "CXC_WORKER_MODEL", "terra", ("terra", "luna", "sol", "astra")),
    ("codex-reviewer", "codex_reviewer", "CXC_REVIEW_MODEL", "sol", ("sol", "astra", "terra", "luna")),
    ("claude-worker", "claude_worker", "CXC_CLAUDE_WORKER", "sonnet", ("sonnet", "opus", "haiku", "fable")),
    ("claude-reviewer", "claude_reviewer", "CXC_CLAUDE_REVIEWER", "opus", ("opus", "fable", "sonnet", "haiku")),
    ("worker-effort", "worker_effort", "CXC_WORKER_EFFORT", "high", EFFORTS),
    ("review-effort", "review_effort", "CXC_REVIEW_EFFORT", "xhigh", EFFORTS),
)
ROLES = {"worker": ("codex-worker", "claude-worker", "worker-effort"),
         "reviewer": ("codex-reviewer", "claude-reviewer", "review-effort")}
MARKET_ID = "peer-coding@because-i-needed"
INLINE_IDS = ("peer-coding@inline", "peer-coding")
MODEL = re.compile(r"^[a-z][a-z0-9.-]*$")
PRECEDENCE = ("env", "project", "global", "default")
LABEL = {"env": "env", "project": "project", "config": "global (/config)", "file": "global (file)",
         "default": "default"}


class Setting:
    def __init__(self, name, key, env, default, options):
        self.name, self.key, self.env, self.default, self.options = name, key, env, default, options
        self.is_effort = options == EFFORTS

    def valid(self, value):
        return value in EFFORTS if self.is_effort else bool(MODEL.match(value))


BY_NAME = {row[0]: Setting(*row) for row in SETTINGS}


def project_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


ROOT = project_root()
PROJECT_FILE = ROOT / ".claude-x-codex" / "settings"
USER_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "claude-x-codex" / "settings"
CLAUDE_SETTINGS = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "settings.json"


def read_file(path):
    values = {}
    try:
        lines = Path(path).read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return values
    for line in lines:
        key, sep, value = line.strip().partition("=")
        setting = next((s for s in BY_NAME.values() if s.key == key.strip()), None)
        if sep and setting and setting.valid(value.strip()):
            values[setting.key] = value.strip()
    return values


def plugin_ids():
    """The pluginConfigs key Claude Code stores this copy's /config choices under."""
    installed = "/plugins/cache/" in Path(__file__).resolve().as_posix()
    return (MARKET_ID,) if installed else INLINE_IDS + (MARKET_ID,)


def as_dict(value):
    return value if isinstance(value, dict) else {}


def read_config():
    try:
        configs = as_dict(as_dict(json.loads(CLAUDE_SETTINGS.read_text())).get("pluginConfigs"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    values = {}
    for plugin in plugin_ids():
        options = as_dict(as_dict(configs.get(plugin)).get("options"))
        for setting in BY_NAME.values():
            value = options.get(setting.key)
            if setting.key not in values and isinstance(value, str) and value in setting.options:
                values[setting.key] = value
    return values


def levels():
    project, config, user = read_file(PROJECT_FILE), read_config(), read_file(USER_FILE)
    table = {}
    for setting in BY_NAME.values():
        table[setting.name] = {"env": os.environ.get(setting.env) or None, "project": project.get(setting.key),
                               "config": config.get(setting.key), "file": user.get(setting.key),
                               "default": setting.default}
    return table


def resolve(level):
    """(value, store) — store is env, project, config, file or default."""
    for store in ("env", "project", "config", "file", "default"):
        if level[store]:
            return level[store], store
    raise AssertionError("default is always set")


def source(store):
    return {"config": "global", "file": "global"}.get(store, store)


def role_entry(role, table):
    names = ROLES[role]
    resolved = {name: resolve(table[name]) for name in names}
    codex, claude, effort = (resolved[name][0] for name in names)

    def summary(pick):
        parts = []
        for prefix, name in zip(("codex", "claude", "effort"), names):
            value = pick(table[name])
            if value:
                parts.append(f"{prefix} {value}")
        return " · ".join(parts) or None

    stores = [source(store) for _, store in resolved.values()]
    return {"value": f"codex {codex} · claude {claude}", "source": min(stores, key=PRECEDENCE.index),
            "project": summary(lambda level: level["project"]),
            "global": summary(lambda level: level["config"] or level["file"]),
            "detail": f"effort {effort}"}


def exclude_state_dir():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-path", "info/exclude"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return
    if out.returncode != 0 or not out.stdout.strip():
        return
    exclude = Path(out.stdout.strip())
    exclude = exclude if exclude.is_absolute() else ROOT / exclude
    try:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        text = exclude.read_text() if exclude.exists() else ""
        if ".claude-x-codex/" not in text.splitlines():
            with exclude.open("a") as handle:
                handle.write(("\n" if text and not text.endswith("\n") else "") + ".claude-x-codex/\n")
    except OSError as error:
        # e.g. a sandbox that keeps .git read-only: the setting is saved, only the exclude line is missing
        print(f"  note: could not add .claude-x-codex/ to {exclude} ({error.strerror or error})")


def write_value(path, setting, value):
    """Rewrite one key in a settings file; a file that exists but can't be read is left alone (OSError)."""
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        lines = []
    except UnicodeDecodeError as error:
        raise OSError(f"{path} is not UTF-8 text ({error.reason})") from error
    kept = [line for line in lines if line.strip().partition("=")[0].strip() != setting.key]
    if value is not None:
        kept.append(f"{setting.key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in kept))


def shadow_note(setting, written_level, value, store):
    if store == "env":
        return f"  note: still {value} here because {setting.env} is set — unset it in this shell to use the files"
    if store == "project" and written_level == "global":
        return f"  note: still {value} here because this project sets it — 'peer-coding:mode {setting.name} unset' to follow global"
    if store == "config" and written_level == "global":
        return (f"  note: still {value} here because Claude Code's /config sets it, which wins over the global file — "
                "change it there, or set it for this project")
    return None


def print_status(table):
    print("peer-coding settings (value · source)")
    for setting in BY_NAME.values():
        value, store = resolve(table[setting.name])
        print(f"  {setting.name:<16} {value:<8} {LABEL[store]}")
    print(f"  order: CXC_* env → project ({PROJECT_FILE}) → Claude Code /config → global ({USER_FILE}) → default")
    print("  set: 'peer-coding:mode <setting> <value>' for this project, add '--global' for every project;"
          " on Claude Code also /config (search \"peer-coding\")")


def usage():
    sys.stderr.write("usage: settings.py get <setting> | env | status [--json [--role worker|reviewer]] | "
                     "set <setting> <value> [--global] | unset <setting> [--global]\n"
                     f"settings: {', '.join(BY_NAME)}\n")
    return 2


def main(argv):
    is_global = "--global" in argv
    args = [a for a in argv if a != "--global"]
    cmd = args[0] if args else "status"
    table = levels()
    if cmd == "get" and len(args) == 2 and args[1] in BY_NAME:
        print(resolve(table[args[1]])[0])
    elif cmd == "env" and len(args) == 1:
        for setting in BY_NAME.values():
            print(f"{setting.env}={shlex.quote(resolve(table[setting.name])[0])}")
    elif cmd == "status" and args[1:] == []:
        print_status(table)
    elif cmd == "status" and args[1:2] == ["--json"] and len(args) == 2:
        print(json.dumps({"settings": {name: dict(level, value=resolve(level)[0], store=resolve(level)[1],
                                                  source=source(resolve(level)[1]))
                                       for name, level in table.items()},
                          "files": {"project": str(PROJECT_FILE), "config": str(CLAUDE_SETTINGS),
                                    "global": str(USER_FILE)}}))
    elif cmd == "status" and args[1:3] == ["--json", "--role"] and len(args) == 4 and args[3] in ROLES:
        print(json.dumps(role_entry(args[3], table)))
    elif cmd in ("set", "unset") and len(args) == (3 if cmd == "set" else 2) and args[1] in BY_NAME:
        setting = BY_NAME[args[1]]
        value = args[2].strip().lower() if cmd == "set" else None
        if value is not None and not setting.valid(value):
            allowed = ", ".join(EFFORTS) if setting.is_effort else "a lowercase family name such as " + ", ".join(setting.options)
            sys.stderr.write(f"settings.py: {setting.name} takes {allowed}\n")
            return 2
        path = USER_FILE if is_global else PROJECT_FILE
        try:
            write_value(path, setting, value)
        except OSError as error:
            sys.stderr.write(f"settings.py: {path} left unchanged: {error.strerror or error}\n")
            return 1
        if not is_global:
            exclude_state_dir()
        effective, store = resolve(levels()[setting.name])
        done = f"set {value} in" if value is not None else "cleared in"
        print(f"peer-coding {setting.name}: {done} {path} → effective: {effective} (source: {LABEL[store]})")
        if value is not None and not setting.is_effort and value not in setting.options:
            print(f"  note: {value} is not a family this version lists ({', '.join(setting.options)}); "
                  "each dispatch resolves it and stops the lane if the CLI has none")
        note = shadow_note(setting, "global" if is_global else "project", effective, store)
        if note:
            print(note)
    else:
        return usage()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
