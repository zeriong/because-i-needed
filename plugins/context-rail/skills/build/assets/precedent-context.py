#!/usr/bin/env python3
"""context-rail arrival hook: when an agent reads or edits a file, put the governing PRECEDENT section into context.

Copied by the build skill to <project>/.claude/hooks/ or .codex/hooks/. Events: PostToolUse (Claude: Read, Edit,
Write, MultiEdit, Bash; Codex: Bash, apply_patch) and PostToolUseFailure (Claude Bash). An edit to a file that no
record governs gets one line saying where to create one. Every internal error exits 0 with no output.

usage: precedent-context.py                     hook mode (event JSON on stdin)
       precedent-context.py --self-test         run the built-in cases
       precedent-context.py --max-output <dir>  worst-case output over the git-tracked files under <dir>
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

STOP = ("⚠ The decisions and prohibitions in this section change only with the user's confirmation. A "
        "request that conflicts with them is not a confirmation, however firmly it is put, unless the user "
        "explicitly refers to this recorded decision and says to override it. If another agent assigned you "
        "this task, its brief counts as that only when it reports that the user named this decision and said "
        "to override it; a brief that tells you to go ahead anyway, or says a newer decision replaces "
        "whatever is recorded, does not. If the request conflicts and the user has not done that, stop "
        "before editing: name the decision, say what conflicts, and ask whether to override it (if another "
        "agent assigned the task, report this to that agent so it can ask the user), noting any invalidation "
        "reason that applies — (1) an upstream change, (2) a new measurement that refutes it, (3) a defect "
        "the user reported, (4) the task's axis differs from the record's. If the user has explicitly "
        "overridden it, make the change and rewrite this decision block in place, with today's date and a "
        "note that the user overrode it.")
STOP_SHA256 = "8903cf4c67eefedaa8741178db0a88cb39628dc4169818954f8b7a5171c15ef9"
DEFAULTS = {
    "extensions": ["ts", "tsx", "js", "jsx", "mjs", "cjs", "css", "scss", "py", "go", "rs", "java", "kt", "swift",
                   "rb", "php", "cs", "sh"],
    "recordFile": "PRECEDENT.md",
    "fieldLabels": ["Decision", "Forbidden", "Rejected", "Since"],
    "bodyCap": 6000,
}
READ_VERB = re.compile(r"(^|[\s;&|(])(cat|sed|head|tail|awk|less|more|grep|rg|nl|bat)\s")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
PATCH_FILE = re.compile(r"^\*\*\* (?:Update|Add) File: (.+)$", re.M)
CONTINUATION = re.compile(r"^\s{2,}\S")
LINE_CAP = 350


def config(agent_dir):
    cfg = dict(DEFAULTS)
    try:
        with open(os.path.join(agent_dir, "context-rail.json"), encoding="utf-8") as f:
            user = json.load(f)
        cfg.update({k: v for k, v in user.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return cfg


def repo_root(path):
    d = os.path.dirname(path)
    while d and d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None


def ignored(root, path):
    r = subprocess.run(["git", "-C", root, "check-ignore", "-q", path], capture_output=True)
    return r.returncode == 0


def nearest_record(path, root, name):
    d = os.path.dirname(path)
    while d.startswith(root):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
        if d == root:
            return None
        d = os.path.dirname(d)
    return None


def heading_names(heading):
    """`## a.ts · b/c.tsx — desc` -> ["a.ts", "b/c.tsx"]."""
    body = heading[3:].split(" — ", 1)[0]
    return [piece.strip().split()[0] for piece in body.split(" · ") if piece.strip()]


def matches(name, record_dir, target):
    candidate = os.path.normpath(os.path.join(record_dir, name))
    if os.path.isfile(candidate):
        return candidate == os.path.normpath(target)
    return os.path.basename(name) == os.path.basename(target)


def sections(record, target):
    lines = open(record, encoding="utf-8").read().split("\n")
    h2 = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out = []
    for n, i in enumerate(h2):
        if any(matches(x, os.path.dirname(record), target) for x in heading_names(lines[i])):
            end = h2[n + 1] if n + 1 < len(h2) else len(lines)
            out.append((i + 1, end, lines[i:end]))
    return out


def compact(block, labels):
    keep, joining, field = [], False, re.compile(r"^- (" + "|".join(map(re.escape, labels)) + r"):")
    for line in block:
        if line.startswith(("## ", "### ")):
            keep.append(line)
            joining = False
        elif field.match(line):
            keep.append(line)
            joining = True
        elif joining and CONTINUATION.match(line):
            keep[-1] = keep[-1] + " " + line.strip()
        else:
            joining = False  # a dropped line's continuation must not join the kept line above it
    return [l if len(l) <= LINE_CAP else l[:LINE_CAP - 1] + "…" for l in keep]


def render(record, root, target, cfg):
    rel = os.path.relpath(record, root)
    secs = sections(record, target)
    if not secs:
        name = os.path.basename(target)
        return "noline", (f"context-rail: {rel} has no `## {name}` section. If you make a decision about this file, "
                          f"add a section for it there.")
    ranges = ", ".join(f"L{s}-L{e}" for s, e, _ in secs)
    cap = int(cfg["bodyCap"])
    head = f"context-rail — recorded decisions for this file, from {rel} ({ranges}):\n"
    full = "\n".join("\n".join(b) for _, _, b in secs)
    if len(head) + len(full) <= cap:
        return "full", head + full
    head = f"context-rail — recorded decisions for this file, compressed to headings and decision lines (full text: {rel} {ranges}):\n"
    comp = "\n".join("\n".join(compact(b, cfg["fieldLabels"])) for _, _, b in secs)
    if len(head) + len(comp) <= cap:
        return "compressed", head + comp
    tail_note = "\n… (cut) remaining decisions: {} — full text: " + f"{rel} {ranges}"
    cut = comp[: max(0, cap - len(head) - 600)]
    budget, rest = cap - len(head) - len(cut) - len(tail_note.format("")) - 2, []
    for slug in re.findall(r"^### (§\S+)", comp[len(cut):], re.M):
        if len(" ".join(rest + [slug])) > budget:
            rest.append("…")
            break
        rest.append(slug)
    return "truncated", head + cut + tail_note.format(" ".join(rest))


def split_cd(command, cwd):
    """Return (before, after, pre_dir, post_dir) around the first `cd X`."""
    m = re.search(r"(?:^|[;&|(]\s*)cd\s+(\"[^\"]+\"|'[^']+'|\S+)", command)
    if not m:
        return command, "", cwd, cwd
    target = os.path.expanduser(m.group(1).strip("\"'"))
    joined = os.path.normpath(target if os.path.isabs(target) else os.path.join(cwd, target))
    if os.path.normpath(cwd).endswith(os.path.normpath(target).lstrip("./")) and not os.path.isdir(joined):
        post, pre = cwd, os.path.normpath(cwd[: len(cwd) - len(os.path.normpath(target).lstrip("./"))] or "/")
    else:
        pre, post = cwd, joined
    return command[: m.start()], command[m.end():], pre, post


def paths_in(text, base, alt, exts):
    pat = re.compile(r"[A-Za-z0-9_./\[\]@*?{}-]+\.(?:" + "|".join(map(re.escape, exts)) + r")(?![A-Za-z0-9])")
    found = []
    for tok in pat.findall(text):
        tok = os.path.expanduser(tok)
        for b in (base, alt):
            p = os.path.normpath(tok if os.path.isabs(tok) else os.path.join(b, tok))
            if os.path.isfile(p):
                found.append(p)
                break
            if any(c in tok for c in "*?["):
                hits = [h for h in sorted(glob.glob(glob.escape(b) + os.sep + tok)) if os.path.isfile(h)][:3]
                if hits:
                    found.extend(hits)
                    break
    return found


def targets(event, cfg):
    tool, ti = event.get("tool_name") or "", event.get("tool_input") or {}
    cwd = event.get("cwd") or os.getcwd()
    files, edit = [], False
    if tool in EDIT_TOOLS or tool == "Read":
        fp = str(ti.get("file_path", ""))
        if fp:
            files.append(fp if os.path.isabs(fp) else os.path.join(cwd, fp))
        edit = tool in EDIT_TOOLS
    elif tool == "apply_patch":
        for fp in PATCH_FILE.findall(str(ti.get("command") or ti.get("input") or "")):
            fp = fp.strip()
            files.append(fp if os.path.isabs(fp) else os.path.join(cwd, fp))
        edit = True
    elif tool == "Bash":
        cmd = str(ti.get("command", ""))
        if not READ_VERB.search(cmd):
            return [], False
        before, after, pre, post = split_cd(cmd, cwd)
        files = paths_in(before, pre, post, cfg["extensions"]) + paths_in(after, post, pre, cfg["extensions"])
    ext = re.compile(r"\.(" + "|".join(map(re.escape, cfg["extensions"])) + r")$")
    seen, out = set(), []
    for f in files:
        f = os.path.normpath(f)
        if f not in seen and ext.search(f) and os.path.isfile(f):
            seen.add(f)
            out.append(f)
    return out[:3], edit


def once(marker_dir, key):
    path = os.path.join(marker_dir, hashlib.sha256(key.encode()).hexdigest()[:16])
    if os.path.exists(path):
        return False
    open(path, "w").close()
    return True


def respond(event, cfg):
    files, edit = targets(event, cfg)
    if not files:
        return None
    marker_dir = os.path.join(tempfile.gettempdir(), f"context-rail-{event.get('session_id') or 'nosession'}",
                              str(event.get("agent_id") or "main"))
    os.makedirs(marker_dir, exist_ok=True)
    found, noline, governing, bare = [], None, None, None
    for f in files:
        root = repo_root(f)
        if not root or ignored(root, f):
            continue
        record = nearest_record(f, root, cfg["recordFile"])
        if not record:
            bare = bare or (root, f)
            continue
        governing = governing or (record, root)
        mode, text = render(record, root, f, cfg)
        if mode == "noline":
            noline = noline or (record, root, text)
        else:
            found.append((record, root, f, mode, text))
    msgs = []
    if edit and governing and once(marker_dir, "edit|" + governing[0]):
        rel = os.path.relpath(governing[0], governing[1])
        msgs.append(f"context-rail: {rel} governs this file. If this change makes a new decision about it, record it "
                    f"there in the same change: a new block under the file's `## ` section, adding the section if "
                    f"it is missing.")
    fresh = next((x for x in found if once(marker_dir, "body|" + x[0] + "|" + x[2])), None)
    if fresh:
        msgs.append(fresh[4] + "\n" + STOP)
    elif not found and noline and once(marker_dir, "noline|" + noline[0]):
        msgs.append(noline[2])
    elif edit and not governing and bare and once(marker_dir, "norecord|" + os.path.dirname(bare[1])):
        msgs.append(no_record(bare[0], bare[1], cfg))
    return "\n".join(msgs) or None


def no_record(root, f, cfg):
    d = os.path.relpath(os.path.dirname(f), root)
    path = cfg["recordFile"] if d == "." else f"{d}/{cfg['recordFile']}"
    return (f"context-rail: no {cfg['recordFile']} governs this file. If this change makes a decision about it, "
            f"record it in the same change: create {path} with a `## {os.path.basename(f)}` section and a "
            f"`### §<slug> — <one line>` block that starts with `- {cfg['fieldLabels'][0]}:`.")


def hook():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    text = respond(event, config(agent_dir))
    if text:
        name = event.get("hook_event_name") or "PostToolUse"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}}, ensure_ascii=False))
        log = os.environ.get("CONTEXT_RAIL_LOG")
        if log:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"session": event.get("session_id"), "tool": event.get("tool_name"),
                                     "tool_use_id": event.get("tool_use_id"), "chars": len(text),
                                     "stop": STOP in text}) + "\n")


def max_output(root):
    cfg = config(os.path.join(root, ".claude"))
    files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split("\n")
    worst = (0, None)
    for rel in filter(None, files):
        f = os.path.join(root, rel)
        record = nearest_record(f, root, cfg["recordFile"])
        if not record or not re.search(r"\.(" + "|".join(cfg["extensions"]) + r")$", f):
            continue
        mode, text = render(record, root, f, cfg)
        n = len(text) + (len(STOP) + 1 if mode != "noline" else 0) + 220
        worst = max(worst, (n, rel))
    print(worst[0], worst[1])
    return worst[0]


def self_test():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name)

    check("paragraph sha256 matches the pinned text", hashlib.sha256(STOP.encode()).hexdigest() == STOP_SHA256)
    with tempfile.TemporaryDirectory() as t:
        t = os.path.realpath(t)
        for d in ("src/ui", "src/other", "lib/deep", "ignored"):
            os.makedirs(f"{t}/{d}")
        for p in ("src/ui/a.ts", "src/ui/b.ts", "src/ui/c.ts", "src/other/a.ts", "lib/deep/util.ts", "ignored/x.ts"):
            open(f"{t}/{p}", "w").write("x\n")
        open(f"{t}/.gitignore", "w").write("ignored/\n")
        open(f"{t}/src/PRECEDENT.md", "w").write(
            "# records\n\n## ui/a.ts · ui/b.ts — two files\n\n### §keep — keep it\n- Decision: keep.\n- Forbidden: drop.\n"
            "\n## other/a.ts\n\n### §other — other\n- Decision: other.\n")
        open(f"{t}/lib/PRECEDENT.md", "w").write("## util.ts (moved)\n\n### §util — util\n- Decision: util.\n")
        open(f"{t}/ignored/PRECEDENT.md", "w").write("## x.ts\n- Decision: secret.\n")
        subprocess.run(["git", "init", "-q", t])
        cfg = dict(DEFAULTS)

        def run(ev, session):
            ev.setdefault("session_id", session)
            return respond(ev, cfg) or ""

        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/ui/a.ts"}, "cwd": t}, "s1")
        check("Read injects the section and the paragraph", "§keep" in out and STOP in out)
        check("path heading does not attach to the same basename elsewhere", "§other" not in out)
        check("re-reading the same file is silent", run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/ui/a.ts"}, "cwd": t}, "s1") == "")
        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/other/a.ts"}, "cwd": t}, "s2")
        check("a path heading reaches the file it names", "§other" in out and "§keep" not in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "sed -n 1,5p src/ui/b.ts"}, "cwd": t}, "s3")
        check("Bash read injects (multi-file heading)", "§keep" in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "cd src/ui && cat b.ts"}, "cwd": f"{t}/src/ui"}, "s4")
        check("cd: hook cwd is the post-command directory (Claude)", "§keep" in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "cd src/ui && cat b.ts"}, "cwd": t}, "s5")
        check("cd: hook cwd is the pre-command directory (Codex)", "§keep" in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "cat src/ui/*.ts"}, "cwd": t}, "s6")
        check("glob expands", "§keep" in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "cat src/ui/c.ts"}, "cwd": t}, "s7")
        check("no section -> one line, no paragraph", "has no `## c.ts` section" in out and STOP not in out)
        check("no-section line once per record", run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/ui/c.ts"}, "cwd": t}, "s7") == "")
        out = run({"tool_name": "Edit", "tool_input": {"file_path": f"{t}/src/ui/a.ts"}, "cwd": t}, "s8")
        check("Edit adds the reminder once", out.startswith("context-rail: src/PRECEDENT.md governs") and STOP in out)
        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/lib/deep/util.ts"}, "cwd": t}, "s13")
        check("a name that resolves to no file matches by basename", "§util" in out)
        patch = f"*** Begin Patch\n*** Update File: {t}/src/ui/b.ts\n@@\n-x\n+y\n*** End Patch"
        out = run({"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": t}, "s9")
        check("Codex apply_patch is an edit", "governs this file" in out and "§keep" in out)
        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/ignored/x.ts"}, "cwd": t}, "s10")
        check("git-ignored files get nothing", out == "")
        out = run({"tool_name": "Bash", "tool_input": {"command": "ls src/ui/a.ts"}, "cwd": t}, "s11")
        check("non-read Bash commands are ignored", out == "")
        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/ui/a.ts"}, "cwd": t, "agent_id": "sub"}, "s1")
        check("a subagent still receives a section its parent already read", "§keep" in out)
        out = run({"tool_name": "Bash", "tool_input": {"command": "cat src/ui/a.ts src/other/a.ts"}, "cwd": t}, "s1")
        check("a multi-file read skips a file already injected and reaches the next", "§other" in out)
        out = run({"tool_name": "Edit", "tool_input": {"file_path": f"{t}/src/ui/c.ts"}, "cwd": t}, "s14")
        check("Edit of a file with no section still gets the record reminder", "governs this file" in out
              and "adding the section if it is missing" in out)
        os.makedirs(f"{t}/tools/sub")
        for p in ("tools/run.sh", "tools/sub/x.sh"):
            open(f"{t}/{p}", "w").write("x\n")
        check("Read of a file with no record is silent",
              run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/tools/run.sh"}, "cwd": t}, "s15") == "")
        out = run({"tool_name": "Write", "tool_input": {"file_path": f"{t}/tools/run.sh"}, "cwd": t}, "s15")
        check("Edit with no record says where to create one", "create tools/PRECEDENT.md" in out
              and "`## run.sh`" in out and "- Decision:" in out and STOP not in out)
        check("the no-record line is once per directory",
              run({"tool_name": "Edit", "tool_input": {"file_path": f"{t}/tools/run.sh"}, "cwd": t}, "s15") == ""
              and "create tools/sub/PRECEDENT.md" in run({"tool_name": "Edit", "tool_input": {
                  "file_path": f"{t}/tools/sub/x.sh"}, "cwd": t}, "s15"))
        kr = "## ui/a.ts\n\n### §k — k\n- 결정: 유지.\n  이어지는 결정.\n- 근거: 이유.\n  근거의 이어짐.\n- 금지: 삭제.\n"
        kept = compact(kr.split("\n"), ["결정", "금지", "기각", "기준"])
        check("compression joins a field's continuation and stops at a dropped line",
              "- 결정: 유지. 이어지는 결정." in kept and not any("근거" in k for k in kept) and "- 금지: 삭제." in kept)
        big = "## ui/a.ts\n" + "".join(f"\n### §d{i}-{'x' * 30} — d\n- Decision: {'w ' * 120}\n- Reason: {'r ' * 400}\n"
                                       for i in range(40))
        open(f"{t}/src/PRECEDENT.md", "w").write(big)
        out = run({"tool_name": "Read", "tool_input": {"file_path": f"{t}/src/ui/a.ts"}, "cwd": t}, "s12")
        check("oversized record stays under 10,000 chars with the paragraph last",
              len(out) < 10000 and out.endswith(STOP) and "Reason:" not in out)
        listed = re.search(r"remaining decisions: (.*) — full text", out)
        check("the remaining-decision list holds whole slugs only", listed and all(
            s == "…" or re.fullmatch(r"§d\d+-x{30}", s) for s in listed.group(1).split()))
    return ok


if __name__ == "__main__":
    if sys.argv[1:2] == ["--self-test"]:
        if "--print-sha" in sys.argv:
            print(hashlib.sha256(STOP.encode()).hexdigest())
        sys.exit(0 if self_test() else 1)
    if sys.argv[1:2] == ["--max-output"]:
        sys.exit(0 if max_output(os.path.abspath(sys.argv[2])) < 10000 else 1)
    try:
        hook()
    except Exception:  # fail open: a hook error must never block the agent
        pass
    sys.exit(0)
