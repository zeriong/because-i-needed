#!/usr/bin/env python3
"""Check that a split plan is lossless and well-formed (forge skill, Stage 2d).

Usage:
  split-check.py plans/<slug>     # needs plan.unsplit.md, plan.md (index) and parts/
  split-check.py --self-test      # runs the built-in fixture checks

Exit 0 when every rule holds; otherwise prints one line per problem and exits 1.
Rules (references/split.md): the index block is marked and holds the part table; part names are
<category>_<A-Z><0-99>.md in ascending order; every file in parts/ is listed exactly once; each part opens
with its position line and closes with a pointer to the next part; every part starts at a heading or a
list item and leaves no code fence open (so no cut falls inside a paragraph, table or code block); and
the index header plus the parts in index order reproduce every non-empty line of the unsplit plan,
unchanged and in order.
"""
import os
import re
import sys
import tempfile

START, END = "<!-- plan-smith:index -->", "<!-- /plan-smith:index -->"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*_([A-Z])([0-9]{1,2})\.md$")
LINK = re.compile(r"\]\(parts/([^)\s]+)\)")
BOUNDARY = re.compile(r"^(#{1,6} |[-*+] |\d+[.)] )")
FIRST = re.compile(r"^> plan-smith · part (\d+)/(\d+) · ([A-Z][0-9]{1,2}) · index: \[plan\.md\]\(\.\./plan\.md\)$")


def lines(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip() for l in f.read().splitlines()]


def nonempty(ls):
    return [l for l in ls if l.strip()]


def check(plan_dir):
    errors = []
    unsplit, index, parts_dir = (os.path.join(plan_dir, p) for p in ("plan.unsplit.md", "plan.md", "parts"))
    for p in (unsplit, index, parts_dir):
        if not os.path.exists(p):
            return [f"missing: {os.path.relpath(p, plan_dir)}"]

    idx = lines(index)
    if idx.count(START) != 1 or idx.count(END) != 1 or idx.index(START) > idx.index(END):
        return ["index: needs exactly one index block, marked by the start and end comments in that order"]
    s, e = idx.index(START), idx.index(END)
    header = nonempty(idx[:s])
    if not header:
        errors.append("index: the unsplit plan's header lines must come before the index block")
    if nonempty(idx[e + 1:]):
        errors.append("index: nothing may follow the end of the index block")

    listed = [m.group(1) for l in idx[s:e] for m in LINK.finditer(l)]
    if len(listed) < 2:
        errors.append(f"index: lists {len(listed)} part(s); a split has at least 2")
    codes = []
    for name in listed:
        m = NAME.match(name)
        if not m:
            errors.append(f"name: {name} is not <category>_<A-Z><0-99>.md with a kebab-case category")
        else:
            codes.append((m.group(1), int(m.group(2)), name))
    if len(set(listed)) != len(listed):
        errors.append("index: a part is listed more than once")
    if [c[:2] for c in codes] != sorted(c[:2] for c in codes) or len({c[:2] for c in codes}) != len(codes):
        errors.append("order: part codes must strictly ascend in index order (A0 < A1 < B0 …)")
    on_disk = sorted(f for f in os.listdir(parts_dir) if not f.startswith("."))
    for f in sorted(set(on_disk) - set(listed)):
        errors.append(f"parts: {f} is on disk but not in the index")
    for f in sorted(set(listed) - set(on_disk)):
        errors.append(f"parts: {f} is in the index but not on disk")
    if errors:
        return errors

    rebuilt = list(header)
    n = len(listed)
    for k, name in enumerate(listed, 1):
        body = nonempty(lines(os.path.join(parts_dir, name)))
        if len(body) < 3:
            errors.append(f"{name}: needs its position line, content, and next line")
            continue
        m = FIRST.match(body[0])
        code = "".join(NAME.match(name).groups())
        if not m or (int(m.group(1)), int(m.group(2)), m.group(3)) != (k, n, code):
            errors.append(f"{name}: first line must be '> plan-smith · part {k}/{n} · {code} · index: [plan.md](../plan.md)'")
        nxt = listed[k] if k < n else None
        want = f"> plan-smith · next: [{nxt}]({nxt})" if nxt else "> plan-smith · next: end of plan"
        if body[-1] != want:
            errors.append(f"{name}: last line must be '{want}'")
        content = body[1:-1]
        if content and not BOUNDARY.match(content[0].lstrip()):
            errors.append(f"{name}: must start at a heading or a list item, not mid-paragraph/table: {content[0][:60]!r}")
        if sum(1 for l in content if l.lstrip().startswith("```")) % 2:
            errors.append(f"{name}: leaves a code fence open — a cut fell inside a code block")
        rebuilt += content
    if errors:
        return errors

    original = nonempty(lines(unsplit))
    if rebuilt != original:
        i = next((i for i, (a, b) in enumerate(zip(original, rebuilt)) if a != b), min(len(original), len(rebuilt)))
        want = original[i] if i < len(original) else "(end of plan)"
        got = rebuilt[i] if i < len(rebuilt) else "(end of parts)"
        errors.append(f"lossless: line {i + 1} of the unsplit plan's non-empty lines differs — "
                      f"expected {want!r}, got {got!r} ({len(original)} lines unsplit, {len(rebuilt)} rebuilt)")
    return errors


def self_test():
    unsplit = ["# Plan", "- Reasoning frame: x / Style: opus", "", "## Goal", "g1", "", "## Steps", "1. a", "2. b",
               "## Done", "d1"]
    parts = {"overview_A0.md": ["## Goal", "g1"], "steps_B0.md": ["## Steps", "1. a", "2. b"],
             "contract_C0.md": ["## Done", "d1"]}

    def build(root, parts, order=None, drop_next=None, extra=None, rename=None):
        os.makedirs(os.path.join(root, "parts"))
        with open(os.path.join(root, "plan.unsplit.md"), "w") as f:
            f.write("\n".join(unsplit) + "\n")
        order = order or list(parts)
        rows = [f"| {n.split('_')[1][:-3]} | [{n}](parts/{n}) | x | — |" for n in order]
        with open(os.path.join(root, "plan.md"), "w") as f:
            f.write("\n".join(unsplit[:2] + ["", START, "| order | part | covers | read after |", "|---|---|---|---|"]
                              + rows + [END]) + "\n")
        for k, n in enumerate(order, 1):
            nxt = order[k] if k < len(order) else None
            last = f"> plan-smith · next: [{nxt}]({nxt})" if nxt else "> plan-smith · next: end of plan"
            code = n.split("_")[1][:-3]
            body = [f"> plan-smith · part {k}/{len(order)} · {code} · index: [plan.md](../plan.md)"] + parts[n]
            if n != drop_next:
                body.append(last)
            with open(os.path.join(root, "parts", rename.get(n, n) if rename else n), "w") as f:
                f.write("\n".join(body) + "\n")
        if extra:
            open(os.path.join(root, "parts", extra), "w").close()

    cases = [
        ("valid split", {}, True),
        ("a word changed", {"parts": {**parts, "steps_B0.md": ["## Steps", "1. a", "2. B"]}}, False),
        ("a line dropped", {"parts": {**parts, "contract_C0.md": ["## Done"]}}, False),
        ("parts out of order", {"order": ["overview_A0.md", "contract_C0.md", "steps_B0.md"]}, False),
        ("missing next line", {"drop_next": "steps_B0.md"}, False),
        ("unlisted file", {"extra": "notes_D0.md"}, False),
        ("file renamed on disk", {"rename": {"contract_C0.md": "Contract_C0.md"}}, False),
    ]
    for label, kw, want in cases:
        with tempfile.TemporaryDirectory() as root:
            build(root, kw.pop("parts", parts), **kw)
            got = not check(root)
            assert got == want, f"self-test '{label}': expected {'pass' if want else 'fail'}, got {'pass' if got else 'fail'}: {check(root)}"
    with tempfile.TemporaryDirectory() as root:
        build(root, {"Bad_A0.md": ["## Goal", "g1"], "steps_B0.md": parts["steps_B0.md"], "contract_C0.md": parts["contract_C0.md"]})
        assert any(e.startswith("name:") for e in check(root)), "self-test 'bad name' not caught"
    fence = ["# Plan", "- Reasoning frame: x / Style: opus", "## Steps", "1. a", "```js", "const x = 1;", "```", "## Done", "d1"]
    for label, cut, ok_expected in (("cut inside a code block", 5, False), ("cut mid-paragraph", 8, False), ("cut before a heading", 7, True)):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "parts"))
            open(os.path.join(root, "plan.unsplit.md"), "w").write("\n".join(fence) + "\n")
            a_lines, b_lines = fence[2:cut], fence[cut:]
            if label == "cut mid-paragraph":
                a_lines, b_lines = fence[2:8], fence[8:]
            names = ["steps_A0.md", "rest_B0.md"]
            open(os.path.join(root, "plan.md"), "w").write("\n".join(fence[:2] + [START] + [f"| x | [{n}](parts/{n}) | x | x |" for n in names] + [END]) + "\n")
            for k, (n, body) in enumerate(zip(names, (a_lines, b_lines)), 1):
                last = f"> plan-smith · next: [{names[1]}]({names[1]})" if k == 1 else "> plan-smith · next: end of plan"
                code = n.split("_")[1][:-3]
                open(os.path.join(root, "parts", n), "w").write("\n".join([f"> plan-smith · part {k}/2 · {code} · index: [plan.md](../plan.md)"] + body + [last]) + "\n")
            got = not check(root)
            assert got == ok_expected, f"self-test '{label}': expected {'pass' if ok_expected else 'fail'}, got {check(root)}"
    print(f"self-test ok ({len(cases) + 4} cases)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit(0)
    if len(sys.argv) != 2:
        print("\n".join(__doc__.strip().splitlines()[2:5]), file=sys.stderr)
        sys.exit(2)
    problems = check(sys.argv[1])
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("ok: split is lossless and well-formed")
