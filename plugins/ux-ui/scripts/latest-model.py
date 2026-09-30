#!/usr/bin/env python3
"""Resolve the newest available model for a Codex or Claude model family."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# In an isolated home, Codex 0.159.0 served a 294.4 s old models cache and refreshed a 304.4 s old
# one (z-lab plugin-platform-lab/latest-model-r4-0.159.0, L02x): a window in (294.4, 304.4] s,
# consistent with 300 s. The margin above
# 304.4 s keeps a cache the CLI still serves from stopping a lane.
CACHE_MAX_AGE_SECONDS = 315
CODEX_SLUG = re.compile(r"^gpt-(\d+(?:\.\d+)*)-([a-z]+)$")
CLAUDE_FAMILIES = ("opus", "sonnet", "haiku", "fable")
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}


class ResolverError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ResolverError(message)


def read_json(path, label):
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except json.JSONDecodeError as exc:
        raise ResolverError(f"cannot read {label} {path}: {exc.msg} (line {exc.lineno}, column {exc.colno})")
    except OSError as exc:
        raise ResolverError(f"cannot read {label} {path} ({exc.strerror or type(exc).__name__})")
    except UnicodeError as exc:
        raise ResolverError(f"cannot read {label} {path} ({type(exc).__name__})")


def codex_family(value):
    if re.fullmatch(r"[a-z]+", value):
        return value, None
    match = CODEX_SLUG.fullmatch(value)
    if match:
        return match.group(2), value
    raise ResolverError(f"invalid Codex family or model id: {value}")


def codex_models():
    try:
        version_result = subprocess.run(["codex", "--version"], capture_output=True, text=True)
    except OSError as exc:
        raise ResolverError(f"cannot run codex --version ({type(exc).__name__})")
    version_parts = version_result.stdout.split() if version_result.returncode == 0 else []
    if not version_parts:
        raise ResolverError("cannot determine Codex CLI version from codex --version")
    client_version = version_parts[-1]

    started = datetime.now(timezone.utc)
    try:
        result = subprocess.run(["codex", "debug", "models"], capture_output=True, text=True)
    except OSError as exc:
        raise ResolverError(f"cannot run codex debug models ({type(exc).__name__})")
    if result.returncode != 0:
        raise ResolverError(f"codex debug models exited with status {result.returncode}")
    try:
        catalog = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ResolverError(f"codex debug models returned bad JSON: {exc}")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("models"), list):
        raise ResolverError("codex debug models JSON has no models list")

    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    cache_path = codex_home / "models_cache.json"
    if not cache_path.exists():
        raise ResolverError(f"no models_cache.json in {codex_home}: catalog not refreshed (is codex logged in and online?)")
    cache = read_json(cache_path, "Codex model cache")
    if not isinstance(cache, dict):
        raise ResolverError(f"invalid Codex model cache {cache_path}: expected an object")
    if cache.get("client_version") != client_version:
        raise ResolverError(f"Codex model cache client_version {cache.get('client_version')!r} does not match codex --version {client_version!r}: catalog not refreshed by this CLI (is codex logged in and online, or does another codex install share CODEX_HOME?)")
    try:
        timestamp = cache["fetched_at"].replace("Z", "+00:00")
        timestamp = re.sub(r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)", r"\1", timestamp)
        fetched_at = datetime.fromisoformat(timestamp)
        if fetched_at.tzinfo is None:
            raise ValueError("timestamp has no timezone")
        age = (started - fetched_at.astimezone(timezone.utc)).total_seconds()
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise ResolverError(f"invalid fetched_at value {cache.get('fetched_at')!r} in Codex model cache {cache_path} ({type(exc).__name__})")
    if age > CACHE_MAX_AGE_SECONDS:
        raise ResolverError(f"Codex model cache age {age:.1f}s exceeds limit {CACHE_MAX_AGE_SECONDS}s in {cache_path}: catalog not refreshed (is codex logged in and online?)")

    def slugs(data):
        entries = data.get("models")
        if not isinstance(entries, list) or any(not isinstance(item, dict) or not isinstance(item.get("slug"), str)
                                                for item in entries):
            return None
        return [item["slug"] for item in entries]

    if slugs(cache) is None or slugs(cache) != slugs(catalog):
        raise ResolverError(f"Codex model cache slugs {slugs(cache)!r} do not match codex debug models slugs {slugs(catalog)!r} in {cache_path}: output did not come from the refreshed cache")
    return catalog["models"]


def resolve_codex(value, effort):
    family, original = codex_family(value)
    models = codex_models()
    candidates = []
    for item in models:
        if not isinstance(item, dict) or item.get("visibility") != "list":
            continue
        match = CODEX_SLUG.fullmatch(item.get("slug", ""))
        if match and match.group(2) == family:
            version = tuple(int(part) for part in match.group(1).split("."))
            candidates.append((version, item))
    if not candidates:
        raise ResolverError(f"no listed Codex model found for family {family}")
    _, chosen = max(candidates, key=lambda candidate: candidate[0])
    if effort is not None:
        levels = chosen.get("supported_reasoning_levels")
        supported = {level.get("effort") for level in levels if isinstance(level, dict)} if isinstance(levels, list) else set()
        if effort not in supported:
            raise ResolverError(f"effort {effort} is not supported by {chosen['slug']}", 3)
    if original and original != chosen["slug"]:
        print(f"latest-model: using {chosen['slug']} (newest {family}) instead of {original}", file=sys.stderr)
    return chosen["slug"]


def claude_family(value):
    if value in CLAUDE_FAMILIES:
        return value, None
    parts = value.split("-")
    matches = [part for part in parts if part in CLAUDE_FAMILIES]
    if len(matches) != 1:
        raise ResolverError(f"invalid Claude family or model id: {value}")
    return matches[0], value


def claude_settings(project):
    if "LATEST_MODEL_MANAGED_SETTINGS" in os.environ:
        paths = [Path(os.environ["LATEST_MODEL_MANAGED_SETTINGS"])]
    elif sys.platform == "darwin":
        paths = [Path("/Library/Application Support/ClaudeCode/managed-settings.json")]
    else:
        paths = [Path("/etc/claude-code/managed-settings.json")]
    config_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    paths.extend((config_dir / "settings.json", project / ".claude/settings.json",
                  project / ".claude/settings.local.json"))
    return paths


def resolve_claude(value, effort, project):
    family, original = claude_family(value)
    if effort is not None and effort not in CLAUDE_EFFORTS:
        raise ResolverError(f"effort {effort} is not supported by Claude {family}", 3)
    variable = f"ANTHROPIC_DEFAULT_{family.upper()}_MODEL"
    if os.environ.get(variable):
        raise ResolverError(f"{variable} is set in the process environment")
    for path in claude_settings(project):
        if not path.exists():
            continue
        settings = read_json(path, "Claude settings file")
        if not isinstance(settings, dict) or ("env" in settings and not isinstance(settings["env"], dict)):
            raise ResolverError(f"invalid Claude settings file {path}: expected an object with an env object")
        env = settings.get("env", {})
        if env.get(variable):
            raise ResolverError(f"{variable} is set in {path}")
    if original:
        print(f"latest-model: using {family} (newest {family}) instead of {original}", file=sys.stderr)
    return family


def main(argv=None):
    parser = Parser(prog="latest-model.py", add_help=False)
    parser.add_argument("provider", choices=("codex", "claude"))
    parser.add_argument("family_or_id")
    parser.add_argument("--effort")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    try:
        args = parser.parse_args(argv)
        if args.provider == "codex":
            resolved = resolve_codex(args.family_or_id, args.effort)
        else:
            resolved = resolve_claude(args.family_or_id, args.effort, args.project)
        print(resolved)
        return 0
    except ResolverError as exc:
        print(f"latest-model: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
