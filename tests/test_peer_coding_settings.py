import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "peer-coding"
SCRIPT = PLUGIN / "scripts" / "settings.py"
ROWS = (
    ("codex-worker", "codex_worker", "CXC_WORKER_MODEL", "terra"),
    ("codex-reviewer", "codex_reviewer", "CXC_REVIEW_MODEL", "sol"),
    ("claude-worker", "claude_worker", "CXC_CLAUDE_WORKER", "sonnet"),
    ("claude-reviewer", "claude_reviewer", "CXC_CLAUDE_REVIEWER", "opus"),
    ("worker-effort", "worker_effort", "CXC_WORKER_EFFORT", "high"),
    ("review-effort", "review_effort", "CXC_REVIEW_EFFORT", "xhigh"),
)


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("CXC_")}
        for key, directory in (("HOME", "home"), ("XDG_CONFIG_HOME", "xdg"),
                               ("CLAUDE_CONFIG_DIR", "claude")):
            path = base / directory
            path.mkdir()
            self.env[key] = str(path)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=self.env, check=True)
        self.project = self.repo / ".claude-x-codex" / "settings"
        self.global_file = Path(self.env["XDG_CONFIG_HOME"]) / "claude-x-codex" / "settings"
        self.config = Path(self.env["CLAUDE_CONFIG_DIR"]) / "settings.json"

    def run_settings(self, *args, env=None, script=SCRIPT):
        result = subprocess.run(["python3", str(script), *args], cwd=self.repo,
                                env=env or self.env, capture_output=True, text=True)
        return result

    def write_file(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def write_project(self, content):
        self.write_file(self.project, content)

    def write_global(self, content):
        self.write_file(self.global_file, content)

    def write_config(self, configs):
        self.write_file(self.config, json.dumps({"pluginConfigs": configs}))

    def assert_get(self, name, value, **kwargs):
        result = self.run_settings("get", name, **kwargs)
        self.assertEqual((result.returncode, result.stdout.strip()), (0, value), result.stderr)

    def test_defaults_and_shell_exports(self):
        for name, _, _, default in ROWS:
            with self.subTest(name=name):
                self.assert_get(name, default)
        result = self.run_settings("env")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         [f"{env}={default}" for _, _, env, default in ROWS])
        command = f'eval "$(python3 {shlex.quote(str(SCRIPT))} env)"; echo "$CXC_WORKER_MODEL"'
        shell = subprocess.run(["bash", "-c", command], cwd=self.repo, env=self.env,
                               capture_output=True, text=True)
        self.assertEqual((shell.returncode, shell.stdout.strip()), (0, "terra"), shell.stderr)

    def test_precedence_and_status(self):
        self.write_project("codex_reviewer=terra\n")
        self.write_global("codex_reviewer=luna\n")
        self.write_config({"peer-coding@inline": {"options": {"codex_reviewer": "astra"}}})
        env = dict(self.env, CXC_REVIEW_MODEL="gamma")
        for value, store, source in (("gamma", "env", "env"), ("terra", "project", "project"),
                                     ("astra", "config", "global"), ("luna", "file", "global"),
                                     ("sol", "default", "default")):
            with self.subTest(store=store):
                self.assert_get("codex-reviewer", value, env=env)
                result = self.run_settings("status", "--json", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                row = json.loads(result.stdout)["settings"]["codex-reviewer"]
                self.assertEqual((row["value"], row["store"], row["source"]), (value, store, source))
            if store == "env":
                env.pop("CXC_REVIEW_MODEL")
            elif store == "project":
                self.project.unlink()
            elif store == "config":
                self.config.unlink()
            elif store == "file":
                self.global_file.unlink()

    def test_inline_config_ids_fall_through_per_key(self):
        self.write_config({
            "peer-coding@inline": {"options": {"codex_worker": "astra"}},
            "peer-coding": {"options": {"codex_worker": "luna", "codex_reviewer": "terra"}},
            "peer-coding@because-i-needed": {"options": {"codex_worker": "sol", "codex_reviewer": "astra", "claude_worker": "haiku"}},
        })
        for name, value in (("codex-worker", "astra"), ("codex-reviewer", "terra"),
                            ("claude-worker", "haiku")):
            with self.subTest(name=name):
                self.assert_get(name, value)

    def test_installed_config_uses_only_marketplace_id(self):
        copy = Path(self.temp.name) / "plugins/cache/because-i-needed/peer-coding/1.2.0/scripts/settings.py"
        copy.parent.mkdir(parents=True)
        shutil.copyfile(SCRIPT, copy)
        self.write_config({"peer-coding@inline": {"options": {"codex_worker": "astra", "claude_worker": "opus"}},
                           "peer-coding": {"options": {"claude_worker": "haiku"}},
                           "peer-coding@because-i-needed": {"options": {"codex_worker": "luna"}}})
        self.assert_get("codex-worker", "luna", script=copy)
        self.assert_get("claude-worker", "sonnet", script=copy)

    def test_config_rejects_values_outside_options(self):
        self.write_config({"peer-coding@inline": {"options": {"review_effort": "ultra", "codex_worker": "nova"}}})
        self.write_global("review_effort=low\ncodex_worker=luna\n")
        self.assert_get("review-effort", "low")
        self.assert_get("codex-worker", "luna")

    def test_reloading_in_the_same_shell_reads_the_stores_again(self):
        load = f'eval "$(python3 {shlex.quote(str(SCRIPT))} env)"; echo "$CXC_WORKER_MODEL"'
        command = f"{load}; mkdir -p .claude-x-codex; echo codex_worker=astra > .claude-x-codex/settings; {load}"
        shell = subprocess.run(["bash", "-c", command], cwd=self.repo, env=self.env, capture_output=True, text=True)
        self.assertEqual((shell.returncode, shell.stdout.split()), (0, ["terra", "astra"]), shell.stderr)

    def test_subshell_loads_survive_an_exporting_shell(self):
        load = f'(eval "$(python3 {shlex.quote(str(SCRIPT))} env)"; echo "$CXC_WORKER_MODEL")'
        command = (f"set -a; export CXC_WORKER_MODEL=; {load}; mkdir -p .claude-x-codex; "
                   f"echo codex_worker=astra > .claude-x-codex/settings; {load}")
        shell = subprocess.run(["bash", "-c", command], cwd=self.repo, env=self.env, capture_output=True, text=True)
        self.assertEqual((shell.returncode, shell.stdout.split()), (0, ["terra", "astra"]), shell.stderr)

    def test_malformed_config_is_ignored(self):
        for content in ("not json", json.dumps(["top", "level", "list"]),
                        *(json.dumps({"pluginConfigs": bad}) for bad in (["invalid"], "invalid", 3, True)),
                        json.dumps({"pluginConfigs": {"peer-coding@inline": ["invalid"]}}),
                        json.dumps({"pluginConfigs": {"peer-coding@inline": {"options": ["invalid"]}}}),
                        json.dumps({"pluginConfigs": {"peer-coding@inline": {"options": "invalid"}}})):
            with self.subTest(content=content):
                self.write_file(self.config, content)
                for name, _, _, default in ROWS:
                    self.assert_get(name, default)

    def test_invalid_file_values_are_unset(self):
        self.write_project("worker_effort=ultra\ncodex_worker=Terra\n")
        self.write_global("worker_effort=ultra\ncodex_worker=Terra\n")
        self.assert_get("worker-effort", "high")
        self.assert_get("codex-worker", "terra")

    def test_project_set_and_git_exclude_are_idempotent(self):
        for _ in range(2):
            result = self.run_settings("set", "codex-worker", "astra")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("effective: astra (source: project)", result.stdout)
        self.assertEqual(self.project.read_text(), "codex_worker=astra\n")
        path = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=self.repo,
                              env=self.env, capture_output=True, text=True, check=True).stdout.strip()
        exclude = Path(path)
        if not exclude.is_absolute():
            exclude = self.repo / exclude
        self.assertEqual(exclude.read_text().splitlines().count(".claude-x-codex/"), 1)

    def test_exclude_without_a_final_newline_keeps_its_last_rule(self):
        path = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=self.repo,
                              env=self.env, capture_output=True, text=True, check=True).stdout.strip()
        exclude = Path(path) if Path(path).is_absolute() else self.repo / path
        exclude.write_text("build/")
        result = self.run_settings("set", "codex-worker", "astra")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(exclude.read_text().splitlines(), ["build/", ".claude-x-codex/"])

    def test_unreadable_file_is_left_unchanged(self):
        for label, content in (("unreadable", b"codex_reviewer=astra\n"), ("not utf-8", b"codex_reviewer=astra\n\xff\n")):
            with self.subTest(label=label):
                self.project.parent.mkdir(parents=True, exist_ok=True)
                self.project.write_bytes(content)
                if label == "unreadable":
                    self.project.chmod(0o200)
                try:
                    result = self.run_settings("set", "codex-worker", "luna")
                finally:
                    self.project.chmod(0o600)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn("left unchanged", result.stderr)
                self.assertEqual(self.project.read_bytes(), content)

    def test_set_preserves_other_lines_and_deduplicates_key(self):
        self.write_project("# note\nfoo=bar\ncodex_worker=luna\nclaude_worker=opus\ncodex_worker=sol\n")
        for value in ("terra", "astra"):
            self.assertEqual(self.run_settings("set", "codex-worker", value).returncode, 0)
        self.assertEqual(self.project.read_text().splitlines(),
                         ["# note", "foo=bar", "claude_worker=opus", "codex_worker=astra"])

    def test_global_set_does_not_create_project_file(self):
        result = self.run_settings("set", "codex-worker", "astra", "--global")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.global_file.read_text(), "codex_worker=astra\n")
        self.assertFalse(self.project.exists())

    def test_set_validation_and_normalization(self):
        result = self.run_settings("set", "worker-effort", "ultra")
        self.assertEqual(result.returncode, 2)
        for effort in ("low", "medium", "high", "xhigh", "max"):
            self.assertIn(effort, result.stderr)
        self.assertFalse(self.project.exists())
        self.assertFalse(self.global_file.exists())
        result = self.run_settings("set", "codex-worker", "Astra")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codex_worker=astra", self.project.read_text())
        result = self.run_settings("set", "codex-worker", "nova")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codex_worker=nova", self.project.read_text())
        self.assertTrue(any(line.startswith("  note:") for line in result.stdout.splitlines()))

    def test_shadow_notes(self):
        self.write_config({"peer-coding@inline": {"options": {"codex_reviewer": "astra"}}})
        result = self.run_settings("set", "codex-reviewer", "luna", "--global")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any("note:" in line and "/config" in line for line in result.stdout.splitlines()))
        self.config.unlink()
        env = dict(self.env, CXC_REVIEW_MODEL="gamma")
        result = self.run_settings("set", "codex-reviewer", "luna", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any("note:" in line and "CXC_REVIEW_MODEL" in line for line in result.stdout.splitlines()))
        result = self.run_settings("set", "codex-reviewer", "luna", "--global")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any("note:" in line and "unset" in line for line in result.stdout.splitlines()))
        self.project.unlink()
        result = self.run_settings("set", "codex-reviewer", "luna", "--global")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any("note:" in line for line in result.stdout.splitlines()))

    def test_unset_removes_only_selected_key_and_falls_back(self):
        self.write_project("# note\ncodex_worker=astra\nclaude_worker=opus\n")
        self.write_global("codex_worker=luna\n")
        result = self.run_settings("unset", "codex-worker")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.project.read_text(), "# note\nclaude_worker=opus\n")
        self.assert_get("codex-worker", "luna")

    def test_invalid_commands_show_usage(self):
        for args in (("get", "unknown"), ("set", "unknown", "sol"), ("get",), ("set", "codex-worker")):
            with self.subTest(args=args):
                result = self.run_settings(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)

    def test_dashboard_roles_and_sources(self):
        self.write_project("codex_worker=astra\nclaude_worker=opus\nworker_effort=low\n"
                           "codex_reviewer=terra\nclaude_reviewer=haiku\nreview_effort=high\n")
        self.write_global("codex_worker=luna\nclaude_worker=haiku\nworker_effort=medium\n"
                          "codex_reviewer=luna\nclaude_reviewer=sonnet\nreview_effort=low\n")
        self.write_config({"peer-coding@inline": {"options": {"codex_worker": "sol", "review_effort": "max"}}})
        env = dict(self.env, CXC_CLAUDE_WORKER="fable")
        expected = {
            "worker": {"value": "codex astra · claude fable", "detail": "effort low", "source": "env",
                       "project": "codex astra · claude opus · effort low",
                       "global": "codex sol · claude haiku · effort medium"},
            "reviewer": {"value": "codex terra · claude haiku", "detail": "effort high", "source": "project",
                         "project": "codex terra · claude haiku · effort high",
                         "global": "codex luna · claude sonnet · effort max"},
        }
        for role in expected:
            with self.subTest(role=role):
                start = time.monotonic()
                result = self.run_settings("status", "--json", "--role", role, env=env)
                self.assertLess(time.monotonic() - start, 1)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected[role])

    def test_dashboard_empty_stores_and_global_source(self):
        for role, model, effort in (("worker", "codex terra · claude sonnet", "high"),
                                    ("reviewer", "codex sol · claude opus", "xhigh")):
            result = self.run_settings("status", "--json", "--role", role)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"value": model, "detail": f"effort {effort}",
                                                         "source": "default", "project": None, "global": None})
        self.write_global("worker_effort=low\nreview_effort=high\n")
        for role in ("worker", "reviewer"):
            result = self.run_settings("status", "--json", "--role", role)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["source"], "global")

    def test_manifest_and_documentation_match_settings(self):
        spec = importlib.util.spec_from_file_location("peer_coding_settings", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, self.env, clear=True), patch.object(sys, "dont_write_bytecode", True):
            spec.loader.exec_module(module)
        config = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())["userConfig"]
        self.assertEqual(set(config), {key for _, key, _, _ in ROWS})
        self.assertEqual([row[:4] for row in module.SETTINGS], list(ROWS))
        run_doc = (PLUGIN / "skills/run/SKILL.md").read_text()
        mode_lines = (PLUGIN / "skills/mode/SKILL.md").read_text().splitlines()
        for name, key, env, default, options in module.SETTINGS:
            with self.subTest(name=name):
                self.assertEqual(config[key]["default"], default)
                self.assertEqual(config[key]["options"], list(options))
                self.assertIn(f"| `{name}` | `{env}` | `{default}` |", run_doc)
                self.assertTrue(any(line.startswith(f"| `{name}` |") and f"`{default}`" in line
                                    for line in mode_lines))


if __name__ == "__main__":
    unittest.main()
