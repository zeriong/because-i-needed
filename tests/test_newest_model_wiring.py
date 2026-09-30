"""Run with python3 -m unittest discover -s tests -v. No installed settings are changed."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "plugins/harness/skills/build/scripts/install-hooks.py"
RESOLVER = ROOT / "plugins/harness/scripts/latest-model.py"
ADAPTERS = {
    "plan-smith": ROOT / "plugins/plan-smith/skills/forge/references/host-codex.md",
    "ux-ui": ROOT / "plugins/ux-ui/skills/build/references/host-codex.md",
    "harness": ROOT / "plugins/harness/skills/build/references/host-codex.md",
}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, env=dict(os.environ))


class HarnessResolverInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bin-newest-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "project with spaces"
        self.repo.mkdir()

    def install(self, host, *flags):
        return run(["python3", str(INSTALLER), "--project", str(self.repo), "--host", host, *flags], self.repo)

    def snapshot(self):
        return {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}

    def test_resolver_is_copied_byte_identical_for_each_host(self):
        expected = RESOLVER.read_bytes()
        for host, hosts in (("claude", ["claude"]), ("codex", ["codex"]), ("both", ["claude", "codex"])):
            with self.subTest(host=host):
                self.setUp()
                result = self.install(host)
                self.assertEqual(result.returncode, 0, result.stderr)
                for name in ("claude", "codex"):
                    copy = self.repo / ("." + name) / "scripts/latest-model.py"
                    if name in hosts:
                        self.assertEqual(copy.read_bytes(), expected)
                        self.assertTrue(os.access(copy, os.X_OK))
                    else:
                        self.assertFalse(copy.exists())
                        self.assertFalse((self.repo / ("." + name)).exists())

    def test_resolver_copy_is_idempotent_and_checked(self):
        args = ("--dry-run",)
        for host, name in (("claude", "claude"), ("codex", "codex")):
            target = f".{name}/scripts/latest-model.py"
            dry = self.install(host, *args)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn(target, json.loads(dry.stdout)["changes"])
            self.assertFalse((self.repo / f".{name}").exists())
            checked = self.install(host, "--check")
            self.assertEqual(checked.returncode, 1)
            self.assertIn(target, json.loads(checked.stdout)["changes"])
        self.assertEqual(self.install("both").returncode, 0)
        before = self.snapshot()
        again = self.install("both")
        self.assertEqual(json.loads(again.stdout)["changed"], [])
        self.assertEqual(self.install("both", "--check").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_restoring_a_deleted_copy_touches_only_that_file(self):
        self.assertEqual(self.install("both").returncode, 0)
        unrelated = self.repo / ".claude/scripts/review-gate.sh"
        unrelated.write_text("#!/bin/sh\nexit 0\n")
        (self.repo / ".codex/scripts/latest-model.py").unlink()
        before = self.snapshot()
        result = self.install("both")
        self.assertEqual(json.loads(result.stdout)["changed"], [".codex/scripts/latest-model.py"])
        after = self.snapshot()
        self.assertEqual({p: b for p, b in after.items() if p.name != "latest-model.py"},
                         {p: b for p, b in before.items() if p.name != "latest-model.py"})
        self.assertEqual((self.repo / ".codex/scripts/latest-model.py").read_bytes(), RESOLVER.read_bytes())

    def test_differing_resolver_needs_replace_flag(self):
        copy = self.repo / ".codex/scripts/latest-model.py"
        copy.parent.mkdir(parents=True)
        copy.write_text("# customized\n")
        self.assertEqual(self.install("codex").returncode, 2)
        self.assertEqual(copy.read_text(), "# customized\n")
        self.assertFalse((self.repo / ".codex/hooks.json").exists())
        self.assertEqual(self.install("codex", "--replace-hook").returncode, 0)
        self.assertEqual(copy.read_bytes(), RESOLVER.read_bytes())


class CodexAdapterWiringTests(unittest.TestCase):
    def test_each_plugin_ships_the_same_resolver(self):
        expected = RESOLVER.read_bytes()
        for name in ("plan-smith", "ux-ui", "harness", "claude-x-codex"):
            self.assertEqual((ROOT / "plugins" / name / "scripts/latest-model.py").read_bytes(), expected, name)

    def test_adapters_resolve_the_newest_model_before_dispatch(self):
        for name, path in ADAPTERS.items():
            with self.subTest(plugin=name):
                text = path.read_text()
                self.assertIn('scripts/latest-model.py" codex ', text)
                self.assertIn("newest model of the main session's family", text)
                self.assertIn("latest-model:", text)
                self.assertNotIn("main session's resolved model", text)
                self.assertNotIn("main model / effort", text)
                self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)

    def test_harness_generated_workflow_uses_the_project_local_resolver(self):
        workflow = (ROOT / "plugins/harness/skills/build/references/workflow.md").read_text()
        self.assertIn('"$(git rev-parse --show-toplevel)/.codex/scripts/latest-model.py" codex ', workflow)
        self.assertIn('"$(git rev-parse --show-toplevel)/.claude/scripts/latest-model.py" claude ', workflow)
        self.assertNotIn("<plugin>", workflow)
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", workflow)
        adapter = ADAPTERS["harness"].read_text()
        self.assertIn('"$(git rev-parse --show-toplevel)/.codex/scripts/latest-model.py" codex ', adapter)

    def test_claude_hosts_check_the_alias_before_dispatch(self):
        skills = (
            ROOT / "plugins/plan-smith/skills/forge/SKILL.md",
            ROOT / "plugins/ux-ui/skills/build/SKILL.md",
            ROOT / "plugins/ux-ui/skills/build-mobile/SKILL.md",
            ROOT / "plugins/harness/skills/build/SKILL.md",
        )
        for path in skills:
            with self.subTest(skill=str(path.relative_to(ROOT))):
                text = path.read_text()
                self.assertIn('scripts/latest-model.py" claude ', text)
                self.assertIn("exit 2", text)

    def test_harness_skill_defines_plugin_alias_and_lists_the_resolver(self):
        text = (ROOT / "plugins/harness/skills/build/SKILL.md").read_text()
        self.assertIn("`<plugin>` is `${CLAUDE_PLUGIN_ROOT}`", text)
        self.assertGreaterEqual(text.count(".claude/scripts/latest-model.py"), 3)

    def test_plan_smith_run_stamp_names_no_versioned_id(self):
        text = (ROOT / "plugins/plan-smith/skills/forge/references/packet-template.md").read_text()
        self.assertNotIn("claude-opus-", text)
        self.assertIn("never the writer's self-report", text)


if __name__ == "__main__":
    unittest.main()


class PluginPathQuotingTests(unittest.TestCase):
    """A plugin root can contain spaces (Codex under "Application Support"), so every
    `<plugin>/…` path in a skill's shell code must be quoted."""

    def test_code_blocks_quote_plugin_paths(self):
        root = Path(__file__).resolve().parents[1]
        hits = []
        for doc in sorted((root / "plugins").glob("*/skills/**/*.md")):
            shell = None  # None: outside a fence; True/False: inside a shell / other fence
            for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("```"):
                    shell = stripped[3:] in ("", "bash", "sh", "shell", "zsh") if shell is None else None
                    continue
                if shell and re.search(r'(^|[^"])<plugin>/', line):
                    hits.append(f"{doc.relative_to(root)}:{number}: {line.strip()}")
        self.assertEqual(hits, [], "unquoted <plugin> paths:\n" + "\n".join(hits))

    def test_documented_resolver_line_runs_from_a_path_with_spaces(self):
        root = Path(__file__).resolve().parents[1]
        doc = (root / "plugins/claude-x-codex/skills/run/references/transport-standalone.md").read_text()
        line = next(l for l in doc.splitlines() if 'latest-model.py" claude "${CXC_CLAUDE_WORKER' in l)
        with tempfile.TemporaryDirectory(prefix="plugin root ") as temp:
            plugin = Path(temp) / "Application Support" / "claude-x-codex"
            (plugin / "scripts").mkdir(parents=True)
            shutil.copy2(root / "plugins/claude-x-codex/scripts/latest-model.py", plugin / "scripts")
            env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_DEFAULT_", "CXC_"))}
            env.update(HOME=temp, CLAUDE_CONFIG_DIR=str(Path(temp) / "cfg"),
                       LATEST_MODEL_MANAGED_SETTINGS=str(Path(temp) / "managed.json"))
            script = line.replace("<plugin>", str(plugin)) + '\necho "$M"'
            result = subprocess.run(["bash", "-c", script], cwd=temp, env=env, capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "sonnet"), result.stderr)
