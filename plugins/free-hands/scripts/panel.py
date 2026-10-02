#!/usr/bin/env python3
"""free-hands brainstorming panel: the deterministic half of the protocol, shared by both hosts.

  panel.py models --host claude|codex          resolve every role's newest model (JSON on stdout)
  panel.py run <round-dir> --brief <brief.json> [--roles r1,r2]
                                               Codex route: start the roles as read-only `codex exec` children
  panel.py tally <round-dir> --brief <brief.json> --attempt 1|2
                                               validate the replies in <round-dir>/<role>.json and say what is next

A round directory is `round1/` or `round2/`; its name decides the round. tally prints JSON with `next`:
`retry` (attempt 1 only: re-run the listed roles once), `decide` (one option, or round 2 is over), `round2` (it wrote
`round2-brief.json` next to the round directory) or `decide-alone` (fewer than three valid replies).
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts" / "latest-model.py"
SCHEMA = ROOT / "skills" / "run" / "references" / "role.schema.json"
ROLES = {  # role: (Claude family, Codex family, Codex effort, web search)
    "quick-thinker": ("sonnet", "luna", "medium", False),
    "deep-thinker": ("opus", "sol", "xhigh", False),
    "evidence-hunter": ("sonnet", "luna", "high", True),
    "trend-tracker": ("sonnet", "luna", "high", True),
    "devils-advocate": ("opus", "sol", "high", False),
}
CONFIDENCE = {"low", "medium", "high"}
MIN_VALID = 3
TIME_LIMIT = 600


def resolve(host, role):
    claude, codex, effort, _ = ROLES[role]
    argv = [sys.executable, str(RESOLVER), host, claude if host == "claude" else codex]
    if host == "codex":
        argv += ["--effort", effort]
    proc = subprocess.run(argv, capture_output=True, text=True)
    if proc.returncode == 0 and proc.stdout.strip():
        return {"model": proc.stdout.strip(), "effort": effort if host == "codex" else None}
    return {"error": (proc.stderr.strip() or f"resolver exit {proc.returncode}"), "exit": proc.returncode}


def cmd_models(args):
    print(json.dumps({role: resolve(args.host, role) for role in ROLES}, indent=1))


def role_prompt(role):
    text = (ROOT / "agents" / f"{role}.md").read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def brief_text(brief_path):
    return Path(brief_path).read_text(encoding="utf-8")


def child_argv(role, resolved, out_file, prompt):
    """`--search` is a top-level Codex flag: it goes before `exec` (`codex exec --search` is rejected)."""
    argv = ["codex"] + (["--search"] if ROLES[role][3] else [])
    return argv + ["exec", "--ephemeral", "-s", "read-only", "-m", resolved["model"],
                   "-c", f'model_reasoning_effort="{resolved["effort"]}"', "--output-schema", str(SCHEMA),
                   "-o", str(out_file), prompt]


def cmd_run(args):
    out = Path(args.round_dir)
    out.mkdir(parents=True, exist_ok=True)
    roles = args.roles.split(",") if args.roles else list(ROLES)
    unknown = [role for role in roles if role not in ROLES]
    if unknown:
        sys.exit(f"panel: unknown roles {unknown}; known: {sorted(ROLES)}")
    brief = brief_text(args.brief)
    metas, children = {}, {}
    try:
        for role in roles:
            for stale in (f"{role}.json", f"{role}.meta.json", f"{role}.log"):  # only this attempt's reply counts
                (out / stale).unlink(missing_ok=True)
            resolved = resolve("codex", role)
            metas[role] = {"role": role, **resolved}
            if "model" not in resolved:
                continue
            prompt = (f"{role_prompt(role)}\n\n# Decision brief\n\n{brief}\n\n"
                      "Return only the JSON object the output schema describes.")
            env = dict(os.environ, FREE_HANDS_ROLE=role, CXC_MODE="off")
            log = open(out / f"{role}.log", "w")
            try:
                proc = subprocess.Popen(child_argv(role, resolved, out / f"{role}.json", prompt),
                                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, env=env)
            except OSError as error:
                log.close()
                metas[role].update(exit=None, error=f"could not start: {error}")
                continue
            children[role] = (proc, log, time.monotonic())
        for role, (proc, log, start) in children.items():
            try:
                metas[role]["exit"] = proc.wait(timeout=max(1, TIME_LIMIT - (time.monotonic() - start)))
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                metas[role].update(exit=None, error=f"time limit {TIME_LIMIT}s")
                (out / f"{role}.json").unlink(missing_ok=True)
    finally:
        for role, (proc, log, _) in children.items():
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            log.close()
    for role, meta in metas.items():
        if role in children:
            header = re.search(r"^model:\s*(\S+)", (out / f"{role}.log").read_text(errors="replace"), re.MULTILINE)
            meta["ran"] = header.group(1) if header else None
        (out / f"{role}.meta.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps(metas, indent=1))


FIELDS = {"option", "new_option", "reasons", "evidence", "risks", "confidence", "would_change_if"}


def strings(value, non_empty=False):
    if not isinstance(value, list) or (non_empty and not value):
        return False
    return all(isinstance(v, str) and (v.strip() or not non_empty) for v in value)


def problems(reply, option_ids):
    """Check a reply against role.schema.json; return None or what is wrong. Never raises on any JSON value."""
    if not isinstance(reply, dict):
        return "not a JSON object"
    if set(reply) != FIELDS:
        return f"fields must be exactly {sorted(FIELDS)}"
    option, new_option = reply["option"], reply["new_option"]
    if not isinstance(option, str) or not (option in option_ids or option == "NEW"):
        return f"option must be one of {sorted(option_ids)} or NEW"
    if not isinstance(new_option, str) or (option == "NEW" and not new_option.strip()):
        return "new_option must be a string, non-empty when option is NEW"
    if not strings(reply["reasons"], non_empty=True):
        return "reasons must be a non-empty list of strings"
    evidence = reply["evidence"]
    if not (isinstance(evidence, list) and all(isinstance(e, dict) and set(e) == {"claim", "source"}
                                               and isinstance(e["claim"], str) and isinstance(e["source"], str)
                                               for e in evidence)):
        return "evidence must be a list of {claim, source}"
    if not strings(reply["risks"]):
        return "risks must be a list of strings"
    if not isinstance(reply["confidence"], str) or reply["confidence"] not in CONFIDENCE:
        return f"confidence must be one of {sorted(CONFIDENCE)}"
    if not isinstance(reply["would_change_if"], str):
        return "would_change_if must be a string"
    return None


def cmd_tally(args):
    round_dir = Path(args.round_dir)
    round_no = 2 if round_dir.name == "round2" else 1
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    option_ids = {o["id"] for o in brief.get("options", [])}
    valid, invalid, missing = {}, {}, []
    for role in ROLES:
        path = round_dir / f"{role}.json"
        if not path.is_file():
            missing.append(role)
            continue
        try:
            reply = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            invalid[role] = f"unreadable: {error}"
            continue
        issue = problems(reply, option_ids)
        if issue:
            invalid[role] = issue
        else:
            valid[role] = reply
    result = {"round": round_no, "attempt": args.attempt, "valid": sorted(valid), "invalid": invalid,
              "missing": missing, "options": {}}
    for role, reply in valid.items():
        key = reply["option"] if reply["option"] != "NEW" else f"NEW: {reply['new_option'].strip()}"
        result["options"].setdefault(key, []).append(role)
    result["options"] = {key: sorted(roles) for key, roles in result["options"].items()}
    failed = missing + sorted(invalid)
    if failed and args.attempt == 1:
        result["next"], result["retry"] = "retry", failed
    elif len(valid) < MIN_VALID:
        result["next"] = "decide-alone"
    elif len(result["options"]) == 1 or round_no == 2:
        result["next"] = "decide"
    else:
        result["next"] = "round2"
        positions = [{"role": role, **{k: valid[role][k] for k in
                                       ("option", "new_option", "reasons", "evidence", "risks", "confidence")
                                       if k in valid[role]}} for role in sorted(valid)]
        second = dict(brief, round=2, positions=positions,
                      instruction="Round 2: read every round-1 position. Keep or change your option, and answer the "
                                  "strongest point against it. A new option is allowed only if it beats all of them.")
        target = round_dir.parent / "round2-brief.json"
        target.write_text(json.dumps(second, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        result["round2_brief"] = str(target)
    print(json.dumps(result, indent=1, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    models = sub.add_parser("models")
    models.add_argument("--host", choices=("claude", "codex"), required=True)
    run = sub.add_parser("run")
    run.add_argument("round_dir")
    run.add_argument("--brief", required=True)
    run.add_argument("--roles")
    tally = sub.add_parser("tally")
    tally.add_argument("round_dir")
    tally.add_argument("--brief", required=True)
    tally.add_argument("--attempt", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    {"models": cmd_models, "run": cmd_run, "tally": cmd_tally}[args.command](args)


if __name__ == "__main__":
    main()
