"""context-rail: the arrival hook, its installer and the record checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "plugins" / "context-rail" / "skills" / "build"
HOOK = BUILD / "assets" / "precedent-context.py"
INSTALL = BUILD / "scripts" / "install-hooks.py"
LINT = BUILD / "scripts" / "records-lint.py"
SIZE = BUILD / "scripts" / "resident-size.py"


def run(*argv, stdin=None, cwd=None):
    return subprocess.run([sys.executable, *map(str, argv)], input=stdin, capture_output=True, text=True, cwd=cwd)


def repo(tmp):
    root = Path(tmp)
    (root / "src").mkdir()
    (root / "src" / "a.ts").write_text("x\n")
    (root / "src" / "PRECEDENT.md").write_text("## a.ts\n\n### §k — keep\n- Decision: keep.\n- Forbidden: drop.\n")
    (root / "CLAUDE.md").write_text("# project\n\nRecorded decisions live in `PRECEDENT.md` beside the code.\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return root


class HookTests(unittest.TestCase):
    def test_self_test_passes(self):
        result = run(HOOK, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("FAIL", result.stdout)

    def test_hook_mode_echoes_event_and_fails_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            event = {"hook_event_name": "PostToolUseFailure", "tool_name": "Bash", "session_id": "t1",
                     "tool_input": {"command": "cat src/a.ts && ls nope"}, "cwd": str(root)}
            out = json.loads(run(HOOK, stdin=json.dumps(event)).stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "PostToolUseFailure")
            self.assertIn("§k", out["additionalContext"])
            self.assertTrue(out["additionalContext"].endswith("a note that the user overrode it."))
            broken = run(HOOK, stdin="not json")
            self.assertEqual((broken.returncode, broken.stdout), (0, ""))

    def test_an_edit_with_no_record_says_where_to_create_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            (root / "lib").mkdir()
            (root / "lib" / "b.ts").write_text("x\n")
            event = {"hook_event_name": "PostToolUse", "tool_name": "Read", "session_id": "t2",
                     "tool_input": {"file_path": str(root / "lib" / "b.ts")}, "cwd": str(root)}
            self.assertEqual(run(HOOK, stdin=json.dumps(event)).stdout, "")
            event["tool_name"] = "Edit"
            out = json.loads(run(HOOK, stdin=json.dumps(event)).stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("create lib/PRECEDENT.md with a `## b.ts` section", out)
            self.assertEqual(run(HOOK, stdin=json.dumps(event)).stdout, "")

    def test_worst_case_output_stays_under_the_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            result = run(HOOK, "--max-output", root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertLess(int(result.stdout.split()[0]), 10000)


class InstallerTests(unittest.TestCase):
    def test_merges_both_hosts_preserves_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            (root / ".claude").mkdir()
            (root / ".claude" / "settings.json").write_text(json.dumps(
                {"permissions": {"allow": ["Bash(ls)"]},
                 "hooks": {"PostToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "echo x"}]}]}}))
            first = run(INSTALL, "--project", root, "--host", "both", "--extensions", "ts")
            self.assertEqual(first.returncode, 0, first.stderr)
            settings = json.loads((root / ".claude" / "settings.json").read_text())
            self.assertEqual(settings["permissions"], {"allow": ["Bash(ls)"]})
            self.assertEqual(len(settings["hooks"]["PostToolUse"]), 2)
            self.assertEqual(settings["hooks"]["PostToolUseFailure"][0]["matcher"], "Bash")
            codex = json.loads((root / ".codex" / "hooks.json").read_text())
            self.assertNotIn("matcher", codex["hooks"]["PostToolUse"][0])
            self.assertEqual(json.loads((root / ".claude" / "context-rail.json").read_text()), {"extensions": ["ts"]})
            self.assertTrue(os.access(root / ".claude" / "hooks" / "precedent-context.py", os.X_OK))
            check = run(INSTALL, "--project", root, "--host", "both", "--extensions", "ts", "--check")
            self.assertEqual((check.returncode, json.loads(check.stdout)["changes"]), (0, []))

    def test_refuses_a_differing_hook_and_malformed_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            self.assertEqual(run(INSTALL, "--project", root, "--host", "claude").returncode, 0)
            with open(root / ".claude" / "hooks" / "precedent-context.py", "a") as f:
                f.write("# local change\n")
            self.assertEqual(run(INSTALL, "--project", root, "--host", "claude").returncode, 2)
            (root / ".codex").mkdir()
            (root / ".codex" / "hooks.json").write_text("[1]")
            result = run(INSTALL, "--project", root, "--host", "codex", "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / ".codex" / "hooks").exists())


class RecordCheckTests(unittest.TestCase):
    def test_lint_flags_orphans_and_blocks_without_a_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            self.assertEqual(run(LINT, "--project", root).returncode, 0)
            with open(root / "src" / "PRECEDENT.md", "a") as f:
                f.write("\n## gone.ts\n\n### §x — x\n- Reason: r\n")
            report = run(LINT, "--project", root)
            self.assertEqual(report.returncode, 1)
            data = json.loads(report.stdout)
            self.assertEqual(len(data["orphan_headings"]), 1)
            self.assertEqual(len(data["blocks_without_decision"]), 1)

    def test_lint_accepts_a_qualified_decision_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            with open(root / "src" / "PRECEDENT.md", "a") as f:
                f.write("\n### §q — qualified\n- Decision (range): clamp.\n\n### §w — wording\n- Decisive: no.\n")
            data = json.loads(run(LINT, "--project", root).stdout)
            self.assertEqual(len(data["blocks_without_decision"]), 1)
            self.assertTrue(data["blocks_without_decision"][0].endswith(":10"))

    def test_resident_size_fails_on_growth_in_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp)
            before = Path(tmp) / "before.json"
            before.write_text(run(SIZE, "--project", root).stdout)
            self.assertEqual(run(SIZE, "--project", root, "--compare", before).returncode, 0)
            with open(root / "CLAUDE.md", "a") as f:
                f.write("한\n")
            self.assertEqual(run(SIZE, "--project", root, "--compare", before).returncode, 1)


if __name__ == "__main__":
    unittest.main()
