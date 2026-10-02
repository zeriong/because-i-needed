"""Run with python3 -m unittest discover -s tests -v. No installed settings are changed."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(args, cwd, *, payload=None, env=None):
    return subprocess.run(args, cwd=cwd, input=payload, text=True, capture_output=True,
                          env={**os.environ, **(env or {})})


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bin-compat-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "project with spaces"
        self.repo.mkdir()
        run(["git", "init", "-q"], self.repo).check_returncode()

    def test_installer_routes_each_host_and_preserves_claude_scope(self):
        bin_dir = Path(self.temp.name) / "bin"
        bin_dir.mkdir()
        log = Path(self.temp.name) / "calls"
        for name in ("claude", "codex"):
            f = bin_dir / name
            f.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                         'with open(os.environ["BIN_TEST_LOG"],"a") as f: '
                         'f.write(json.dumps([os.path.basename(sys.argv[0]),*sys.argv[1:]])+"\\n")\n'
                         'if os.environ.get("BIN_TEST_FAIL") == "marketplace" and "marketplace" in sys.argv: sys.exit(1)\n'
                         'if os.environ.get("BIN_TEST_FAIL") == "plugin" and "harness@because-i-needed" in sys.argv: sys.exit(1)\n')
            f.chmod(0o755)
        env = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "BIN_TEST_LOG": str(log)}
        installer = ["bash", str(ROOT / "install.sh"), "--only", "harness"]
        for host, extra, expected in [
            ("claude", ["--scope", "project"], ["claude", "plugin", "install", "harness@because-i-needed", "--scope", "project"]),
            ("codex", ["--host", "codex", "--scope", "user"], ["codex", "plugin", "add", "harness@because-i-needed"]),
        ]:
            with self.subTest(host=host):
                log.write_text("")
                result = run(installer + extra, self.repo, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual(calls[0][:4], [host, "plugin", "marketplace", "add"])
                self.assertEqual(calls[1], expected)
        log.write_text("")
        result = run(installer + ["--host", "codex", "--scope", "project"], self.repo, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(log.read_text(), "")
        result = run(installer + ["--host", "codex"], self.repo, env={**env, "BIN_TEST_FAIL": "marketplace"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(log.read_text().splitlines()), 1)
        result = run(installer + ["--host", "codex"], self.repo, env={**env, "BIN_TEST_FAIL": "plugin"})
        self.assertNotEqual(result.returncode, 0)

    def test_installer_dry_run_list_and_invalid_host(self):
        installer = ["bash", str(ROOT / "install.sh")]
        result = run(installer + ["--host=codex", "--all", "--dry-run"], self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.count("+ codex plugin add "), 4)
        for name in ("harness", "ux-ui", "peer-coding", "free-hands"):
            self.assertIn(f"+ codex plugin add {name}@", result.stdout)
        self.assertNotIn("plan-smith", result.stdout)
        self.assertNotIn("+ claude", result.stdout)
        self.assertEqual(run(installer + ["--host", "codex", "--list"], self.repo).returncode, 0)
        self.assertNotEqual(run(installer + ["--host", "unknown", "--all"], self.repo).returncode, 0)
        self.assertNotEqual(run(installer + ["--host"], self.repo).returncode, 0)

    def test_ui_gate_both_payloads_and_stale_approval(self):
        gate = ROOT / "plugins/ux-ui/scripts/ui-commit-gate.sh"
        for vendor in ("claude", "codex"):
            with self.subTest(vendor=vendor):
                (self.repo / "screen.html").write_text("<main>" + vendor + "</main>")
                run(["git", "add", "screen.html"], self.repo).check_returncode()
                payload = json.dumps({"cwd": str(self.repo), "tool_name": "Bash",
                                      "hook_event_name": "PreToolUse", "tool_input": {"command": "git commit -m test"}})
                env = {"CLAUDE_PROJECT_DIR": str(self.repo) if vendor == "claude" else ""}
                denied = run(["bash", str(gate)], self.repo, payload=payload, env=env)
                self.assertEqual(denied.returncode, 2, denied.stderr)
                feature, measure = 'fixture "quoted"', 'measure \\ path'
                run(["bash", str(gate), "approve", feature, measure], self.repo).check_returncode()
                digest = run(["bash", str(gate), "hash"], self.repo).stdout.strip()
                approval = json.loads((self.repo / ".ux-ui/approvals" / (digest + ".json")).read_text())
                self.assertEqual((approval["feature"], approval["measureDir"]), (feature, measure))
                self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload, env=env).returncode, 0)
                (self.repo / "screen.html").write_text("<main>changed " + vendor + "</main>")
                run(["git", "add", "screen.html"], self.repo).check_returncode()
                self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload, env=env).returncode, 2)
        for payload in ("not-json", "{}", json.dumps({"tool_input": {"command": "git status"}})):
            self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload).returncode, 0)
        run(["git", "rm", "--cached", "-f", "screen.html"], self.repo).check_returncode()
        (self.repo / "logic.py").write_text("x = 1\n")
        run(["git", "add", "logic.py"], self.repo).check_returncode()
        payload = json.dumps({"cwd": str(self.repo), "tool_input": {"command": "git commit -m backend"}})
        self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload).returncode, 0)

    def test_ui_gate_filename_safe_hashes_and_glob_shadowing(self):
        gate = ROOT / "plugins/ux-ui/scripts/ui-commit-gate.sh"
        (self.repo / "shadow.tsx").write_text("untracked shell glob match")
        payload = json.dumps({"cwd": str(self.repo), "tool_input": {"command": "git commit -m test"}})
        for name in ("src/actual.tsx", "src/화면.tsx", "src/my screen.tsx", "src/line\nbreak.tsx", "src/[id].tsx"):
            with self.subTest(name=name):
                source = self.repo / name
                source.parent.mkdir(exist_ok=True)
                source.write_text("<p>before</p>")
                run(["git", "--literal-pathspecs", "add", "--", name], self.repo).check_returncode()
                before = run(["bash", str(gate), "hash"], self.repo).stdout.strip()
                self.assertTrue(before)
                run(["bash", str(gate), "approve", "fixture"], self.repo).check_returncode()
                source.write_text("<p>after</p>")
                run(["git", "--literal-pathspecs", "add", "--", name], self.repo).check_returncode()
                after = run(["bash", str(gate), "hash"], self.repo).stdout.strip()
                self.assertNotEqual(before, after)
                self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload).returncode, 2)
                run(["git", "--literal-pathspecs", "rm", "--cached", "-f", "--", name], self.repo).check_returncode()

    def test_ui_gate_resolves_commit_worktree_and_nested_approval(self):
        import shlex
        gate = ROOT / "plugins/ux-ui/scripts/ui-commit-gate.sh"
        target = self.repo / "other repo"
        target.mkdir()
        run(["git", "init", "-q"], target).check_returncode()
        (target / "screen.html").write_text("<p>target</p>")
        run(["git", "add", "screen.html"], target).check_returncode()
        nested = target / "subdir"
        nested.mkdir()
        commands = [
            "git -C " + shlex.quote(str(target)) + " commit -m test",
            "cd " + shlex.quote(str(target)) + " && git commit -m test",
            "git -C " + shlex.quote(str(self.repo)) + " -C 'other repo' commit -m test",
        ]
        for command in commands:
            payload = json.dumps({"cwd": str(self.repo), "tool_input": {"command": command}})
            self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload).returncode, 2)
        run(["bash", str(gate), "approve", "fixture"], nested).check_returncode()
        self.assertTrue((target / ".ux-ui/approvals").is_dir())
        self.assertFalse((nested / ".ux-ui").exists())
        fake_bin = self.repo / "fake-bin"
        fake_bin.mkdir()
        marker = self.repo / "must-not-execute"
        fake_git = fake_bin / "git"
        fake_git.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(marker)) + "\n")
        fake_git.chmod(0o755)
        payload = json.dumps({"cwd": str(self.repo), "tool_input": {
            "command": "env PATH=" + shlex.quote(str(fake_bin)) + " git commit -m test"}})
        run(["bash", str(gate)], self.repo, payload=payload)
        self.assertFalse(marker.exists(), "The resolver must not execute a command-supplied git binary")
        for command in commands:
            payload = json.dumps({"cwd": str(self.repo), "tool_input": {"command": command}})
            self.assertEqual(run(["bash", str(gate)], self.repo, payload=payload).returncode, 0)

    def test_harness_injection_for_both_layouts_and_bypass(self):
        source = ROOT / "plugins/harness/skills/build/assets/inject-context.sh"
        for host in ("claude", "codex"):
            agent_dir = self.repo / ("." + host)
            dest = agent_dir / "hooks/inject-context.sh"
            dest.parent.mkdir(parents=True)
            shutil.copy2(source, dest)
            skills = self.repo / ".agents/skills" if host == "codex" else agent_dir / "skills"
            for name, body in (("project-rules", "## §1 Fixture rule"), ("harness-engineering", "## Phase 8 Fixture review")):
                skill = skills / name / "SKILL.md"
                skill.parent.mkdir(parents=True, exist_ok=True)
                skill.write_text("---\nname: " + name + "\ndescription: fixture\n---\n\n" + body)
            nested = self.repo / "nested"
            nested.mkdir(exist_ok=True)
            result = run(["bash", str(dest)], nested, payload=json.dumps({"prompt": "implement"}))
            self.assertEqual(result.returncode, 0, result.stderr)
            context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("## §1 Fixture rule", context)
            self.assertIn("## Phase 8 Fixture review", context)
            self.assertNotIn("description:", context)
            for bypass in ("!skip", "harness 빼고 해줘", "without harness", "SKIP HARNESS", "no harness"):
                result = run(["bash", str(dest)], nested, payload=json.dumps({"prompt": bypass}))
                self.assertIn("BYPASS MODE", result.stdout)
                self.assertIn("Fixture rule", result.stdout)
                self.assertNotIn("Fixture review", result.stdout)
            (skills / "project-rules/SKILL.md").unlink()
            result = run(["bash", str(dest)], nested, payload='{"prompt":"implement"}')
            self.assertIn("HARNESS SETUP INCOMPLETE", result.stdout)
            result = run(["bash", str(dest)], nested, payload='{"prompt":"!skip"}')
            self.assertIn("HARNESS SETUP INCOMPLETE", result.stdout)
            self.assertIn("BYPASS MODE", result.stdout)
            self.assertEqual(run(["bash", str(dest)], nested, payload="invalid").returncode, 0)

    def test_mode_prompt_hook_and_context_audit(self):
        plugin = ROOT / "plugins/peer-coding"
        mode_env = {"XDG_CONFIG_HOME": str(Path(self.temp.name) / "config"), "CXC_MODE": ""}
        for state in ("on", "off"):
            result = run(["bash", str(plugin / "scripts/mode.sh"), state], self.repo, env=mode_env)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run(["bash", str(plugin / "scripts/mode.sh"), "get"], self.repo, env=mode_env)
            self.assertEqual(result.stdout.strip(), state)
        for mode in ("off", "on"):
            result = run(["bash", str(plugin / "hooks/mode-context.sh")], self.repo,
                         payload='{"prompt":"implement"}', env={"CXC_MODE": mode, "CLAUDE_PLUGIN_ROOT": str(plugin)})
            self.assertEqual(result.returncode, 0)
            self.assertEqual("[peer-coding: ON]" in result.stdout, mode == "on")
            if mode == "on":
                context = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(context["hookEventName"], "UserPromptSubmit")
                self.assertIn("[peer-coding: ON]", context["additionalContext"])
                self.assertIn("peer-coding:run", context["additionalContext"])
                self.assertIn("peer-coding:mode", context["additionalContext"])
            else:
                self.assertEqual(result.stdout, "")
        for invocation in ("/peer-coding:mode off", "$peer-coding:mode off"):
            result = run(["bash", str(plugin / "hooks/mode-context.sh")], self.repo,
                         payload=json.dumps({"prompt": invocation}),
                         env={"CXC_MODE": "on", "CLAUDE_PLUGIN_ROOT": str(plugin)})
            self.assertEqual(result.stdout, "", invocation)
        for name in (".claude/settings.json", ".codex/hooks.json"):
            p = self.repo / name
            p.parent.mkdir(exist_ok=True)
            p.write_text(json.dumps({"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "fixture-hook"}]}]}}))
        p = self.repo / ".agents/skills/example/SKILL.md"
        p.parent.mkdir(parents=True)
        p.write_text("fixture")
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        result = run(["bash", str(plugin / "scripts/context-audit.sh")], self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in (".claude/settings.json", ".codex/hooks.json", ".agents/"):
            self.assertIn(name, result.stdout)
        self.assertIn("| .codex/hooks.json | UserPromptSubmit |", result.stdout)
        after = {str(p.relative_to(self.repo)): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

        (self.repo / "CLAUDE.md").write_text("Use the original rules.\n")
        (self.repo / "AGENTS.md").write_text("Do not read CLAUDE.md. Use different rules.\n")
        result = run(["bash", str(plugin / "scripts/context-audit.sh")], self.repo)
        self.assertIn("CHECK: pointer text found", result.stdout)
        self.assertNotIn("ok (pointer)", result.stdout)

    def test_manifests_share_skills_and_mcp_definitions(self):
        for plugin in (ROOT / "plugins").iterdir():
            claude = json.loads((plugin / ".claude-plugin/plugin.json").read_text())
            codex = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(claude["name"], codex["name"])
            self.assertEqual(claude["version"], codex["version"])
            self.assertTrue((plugin / codex["skills"]).is_dir())
            if "mcpServers" in claude:
                self.assertEqual(codex["mcpServers"], claude["mcpServers"])

    def test_harness_setup_preserves_settings_and_is_idempotent(self):
        installer = ROOT / "plugins/harness/skills/build/scripts/install-hooks.py"
        for host in ("claude", "codex"):
            agent = self.repo / ("." + host)
            agent.mkdir()
            config = agent / ("settings.json" if host == "claude" else "hooks.json")
            config.write_text(json.dumps({"keep": {"value": 7}, "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "keep-stop"}]}],
                "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "keep-prompt"}]}]}}))
            skills = self.repo / ".agents/skills" if host == "codex" else agent / "skills"
            for name in ("project-rules", "harness-engineering"):
                p = skills / name / "SKILL.md"
                p.parent.mkdir(parents=True)
                p.write_text("---\nname: " + name + "\ndescription: fixture\n---\n\n## " + name)
        args = ["python3", str(installer), "--project", str(self.repo), "--host", "both"]
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(run(args + ["--dry-run"], self.repo).returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})
        result = run(args, self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        nested = self.repo / "nested"
        nested.mkdir()
        for host in ("claude", "codex"):
            config = self.repo / ("." + host) / ("settings.json" if host == "claude" else "hooks.json")
            data = json.loads(config.read_text())
            self.assertEqual(data["keep"], {"value": 7})
            self.assertEqual(data["hooks"]["Stop"][0]["hooks"][0]["command"], "keep-stop")
            commands = [h["command"] for e in data["hooks"]["UserPromptSubmit"] for h in e["hooks"]]
            self.assertEqual(commands[0], "keep-prompt")
            self.assertEqual(len(commands), 2)
            injected = run(["bash", "-c", commands[1]], nested, payload='{"prompt":"implement"}',
                           env={"CLAUDE_PROJECT_DIR": str(self.repo)})
            self.assertEqual(injected.returncode, 0, injected.stderr)
            self.assertIn("## project-rules", injected.stdout)
            # An existing duplicate of this hook is removed without removing other hooks.
            data["hooks"]["UserPromptSubmit"].append(data["hooks"]["UserPromptSubmit"][-1])
            config.write_text(json.dumps(data))
        self.assertEqual(run(args, self.repo).returncode, 0)
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(json.loads(run(args, self.repo).stdout)["changed"], [])
        self.assertEqual(run(args + ["--check"], self.repo).returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})
        # Invalid second-host settings must leave the first host and all files alone.
        (self.repo / ".codex/hooks.json").write_text('{"hooks": []}')
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.assertEqual(run(args, self.repo).returncode, 2)
        self.assertEqual(before, {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_harness_setup_preserves_custom_hook(self):
        installer = ROOT / "plugins/harness/skills/build/scripts/install-hooks.py"
        hook = self.repo / ".codex/hooks/inject-context.sh"
        hook.parent.mkdir(parents=True)
        hook.write_text("#!/bin/sh\necho custom\n")
        args = ["python3", str(installer), "--project", str(self.repo), "--host", "codex"]
        self.assertEqual(run(args, self.repo).returncode, 2)
        self.assertIn("custom", hook.read_text())
        self.assertFalse((self.repo / ".codex/hooks.json").exists())
        self.assertEqual(run(args + ["--replace-hook"], self.repo).returncode, 0)
        self.assertNotIn("echo custom", hook.read_text())

    def test_linked_worktree_mode_exclusion_and_override_audit(self):
        # Reuse existing history in a disposable clone; never create a commit.
        main = Path(self.temp.name) / "main"
        linked = Path(self.temp.name) / "linked tree"
        run(["git", "clone", "-q", "--no-hardlinks", "--no-checkout", str(ROOT), str(main)], self.repo).check_returncode()
        run(["git", "worktree", "add", "-q", "--detach", str(linked), "HEAD"], main).check_returncode()
        self.assertTrue((linked / ".git").is_file())
        mode = ROOT / "plugins/peer-coding/scripts/mode.sh"
        args = ["bash", str(mode), "on"]
        env = {"CXC_MODE": "", "XDG_CONFIG_HOME": str(Path(self.temp.name) / "config")}
        self.assertEqual(run(args, linked, env=env).returncode, 0)
        self.assertEqual(run(["git", "check-ignore", "-q", ".claude-x-codex/mode"], linked).returncode, 0)
        self.assertEqual(run(["bash", str(mode), "get"], linked, env=env).stdout.strip(), "on")
        (self.repo / "CLAUDE.md").write_text("@AGENTS.md\n")
        (self.repo / "AGENTS.md").write_text("Shared rule\n")
        (self.repo / "AGENTS.override.md").write_text("Different rule\n")
        (self.repo / ".codex").mkdir()
        (self.repo / ".codex/hooks.json").write_text('{"hooks":{"UserPromptSubmit":[42]}}')
        audit = ROOT / "plugins/peer-coding/scripts/context-audit.sh"
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        result = run(["bash", str(audit)], self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CHECK: Codex selects AGENTS.override.md", result.stdout)
        self.assertIn("invalid: expected an entry with a hooks list", result.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})



class LatestModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="latest-model-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.codex_home = self.root / "codex-home"
        self.codex_home.mkdir()
        self.fixture = self.root / "codex-fixture.json"
        fake_codex = self.bin_dir / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "from datetime import datetime, timezone\n"
            "with open(os.environ['LATEST_MODEL_FIXTURE'], encoding='utf-8') as stream: data=json.load(stream)\n"
            "if sys.argv[1:] == ['--version']:\n"
            "    print(data.get('version_output', 'codex-cli ' + data.get('version', '0.159.0')))\n"
            "    sys.exit(data.get('version_exit', 0))\n"
            "if sys.argv[1:] == ['debug', 'models']:\n"
            "    if data.get('refresh_cache'):\n"
            "        cache = {'fetched_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),\n"
            "                 'client_version': data.get('version', '0.159.0'),\n"
            "                 'models': data.get('catalog', {'models': []})['models']}\n"
            "        with open(os.path.join(os.environ['CODEX_HOME'], 'models_cache.json'), 'w', encoding='utf-8') as stream: json.dump(cache, stream)\n"
            "    if 'models_output' in data: print(data['models_output'])\n"
            "    else: print(json.dumps(data.get('catalog', {'models': []})))\n"
            "    sys.exit(data.get('models_exit', 0))\n"
            "sys.exit(9)\n", encoding="utf-8")
        fake_codex.chmod(0o755)
        self.models = [
            {"slug": "gpt-6.1-sol", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max", "ultra")},
            {"slug": "gpt-6-astra", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max", "ultra")},
            {"slug": "gpt-6-sol", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max", "ultra")},
            {"slug": "gpt-6-luna", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max")},
            {"slug": "gpt-5.6-terra", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max", "ultra")},
            {"slug": "gpt-5.6-sol", "visibility": "list", "supported_reasoning_levels": self.levels("low", "medium", "high", "xhigh", "max", "ultra")},
            {"slug": "gpt-reserve", "visibility": "hide", "supported_reasoning_levels": []},
        ]
        self.write_fixture()
        self.base_env = {
            "PATH": str(self.bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "CODEX_HOME": str(self.codex_home),
            "HOME": str(self.root),
            "CLAUDE_CONFIG_DIR": str(self.root / "claude-config"),
            "LATEST_MODEL_MANAGED_SETTINGS": str(self.root / "managed-settings.json"),
            "LATEST_MODEL_FIXTURE": str(self.fixture),
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "",
            "ANTHROPIC_DEFAULT_FABLE_MODEL": "",
        }
        (self.root / "claude-config").mkdir()
        self.script = ROOT / "plugins/peer-coding/scripts/latest-model.py"

    @staticmethod
    def levels(*names):
        return [{"effort": name, "description": name} for name in names]

    def write_fixture(self, models=None, **extra):
        catalog = {"models": self.models if models is None and hasattr(self, "models") else (models or [])}
        data = {"version": "0.159.0", "catalog": catalog, **extra}
        self.fixture.write_text(json.dumps(data), encoding="utf-8")
        return catalog

    def write_cache(self, catalog=None, **changes):
        if catalog is None:
            data = json.loads(self.fixture.read_text(encoding="utf-8"))["catalog"]
        else:
            data = catalog
        cache = {
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "client_version": "0.159.0",
            "etag": "fixture", "identity": "fixture", "models": data["models"],
        }
        cache.update(changes)
        (self.codex_home / "models_cache.json").write_text(json.dumps(cache), encoding="utf-8")

    def call(self, *args, env=None, project=None):
        return run([sys.executable, str(self.script), *args], project or self.project,
                   env={**self.base_env, **(env or {})})

    def assert_failure(self, result, code):
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("latest-model:"), result.stderr)
        self.assertEqual(len(result.stderr.splitlines()), 1, result.stderr)

    def test_codex_newest_model_per_family_and_numeric_versions(self):
        catalog = self.write_fixture()
        self.write_cache(catalog)
        for family, expected in (("sol", "gpt-6.1-sol"), ("luna", "gpt-6-luna"),
                                 ("astra", "gpt-6-astra"), ("terra", "gpt-5.6-terra")):
            with self.subTest(family=family):
                result = self.call("codex", family)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected + "\n", ""))
        numeric = [
            {"slug": "gpt-6.9-sol", "visibility": "list", "supported_reasoning_levels": self.levels("high")},
            {"slug": "gpt-6.10-sol", "visibility": "list", "supported_reasoning_levels": self.levels("high")},
            {"slug": "gpt-6.11-sol", "visibility": "hide", "supported_reasoning_levels": self.levels("high")},
        ]
        catalog = self.write_fixture(numeric)
        self.write_cache(catalog)
        self.assertEqual(self.call("codex", "sol").stdout, "gpt-6.10-sol\n")

    def test_codex_family_the_plugin_has_never_seen_resolves_from_the_catalog(self):
        catalog = self.write_fixture([
            {"slug": "gpt-7-nova", "visibility": "list", "supported_reasoning_levels": self.levels("high")},
            {"slug": "gpt-7.2-nova", "visibility": "list", "supported_reasoning_levels": self.levels("high")},
        ])
        self.write_cache(catalog)
        self.assertEqual(self.call("codex", "nova").stdout, "gpt-7.2-nova\n")
        self.assertEqual(self.call("codex", "gpt-7-nova").stdout, "gpt-7.2-nova\n")
        self.assert_failure(self.call("codex", "sol"), 2)

    def test_codex_versioned_input_raised_line_and_refresh_between_calls(self):
        catalog = self.write_fixture()
        self.write_cache(catalog)
        result = self.call("codex", "gpt-6-sol")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "gpt-6.1-sol\n")
        self.assertEqual(result.stderr, "latest-model: using gpt-6.1-sol (newest sol) instead of gpt-6-sol\n")
        newer = self.models + [{"slug": "gpt-6.2-sol", "visibility": "list",
                                "supported_reasoning_levels": self.levels("high")}]
        catalog = self.write_fixture(newer)
        self.write_cache(catalog)
        self.assertEqual(self.call("codex", "sol").stdout, "gpt-6.2-sol\n")

    def test_codex_accepts_long_and_three_digit_timestamp_fractions(self):
        catalog = self.write_fixture()
        fixed_times = ("2026-09-30T02:28:47.359384123Z", "2026-09-30T02:28:47.359Z")
        for fetched_at in fixed_times:
            with self.subTest(fetched_at=fetched_at):
                self.write_cache(catalog, fetched_at=fetched_at)
                result = self.call("codex", "sol")
                self.assert_failure(result, 2)
                self.assertIn("Codex model cache age", result.stderr)
                self.assertNotIn("invalid fetched_at", result.stderr)
        for fraction in ("123456789", "123"):
            with self.subTest(fraction=fraction):
                fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + "." + fraction + "Z"
                self.write_cache(catalog, fetched_at=fetched_at)
                result = self.call("codex", "sol")
                self.assertEqual((result.returncode, result.stdout), (0, "gpt-6.1-sol\n"), result.stderr)

    def test_codex_verifies_cache_after_cli_refreshes_stale_cache(self):
        old_catalog = self.write_fixture()
        self.write_cache(old_catalog, fetched_at="2000-01-01T00:00:00Z")
        newer = self.models + [{"slug": "gpt-6.3-sol", "visibility": "list",
                                "supported_reasoning_levels": self.levels("high")}]
        catalog = self.write_fixture(newer, refresh_cache=True)
        result = self.call("codex", "sol")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "gpt-6.3-sol\n", ""))

    def test_codex_version_uses_last_whitespace_token(self):
        catalog = self.write_fixture(version="0.160.0-alpha.3",
                                     version_output="codex-cli 0.160.0-alpha.3")
        self.write_cache(catalog, client_version="0.160.0-alpha.3")
        result = self.call("codex", "sol")
        self.assertEqual((result.returncode, result.stdout), (0, "gpt-6.1-sol\n"), result.stderr)

    def test_codex_cache_and_cli_failures_exit_two_without_stdout(self):
        catalog = self.write_fixture()
        missing = self.call("codex", "sol")
        self.assert_failure(missing, 2)
        self.assertIn(f"no models_cache.json in {self.codex_home}: catalog not refreshed (is codex logged in and online?)", missing.stderr)
        self.write_cache(catalog, fetched_at="2000-01-01T00:00:00Z")
        stale = self.call("codex", "sol")
        self.assert_failure(stale, 2)
        self.assertRegex(stale.stderr, r"age [0-9.]+s exceeds limit [0-9]+s")
        self.assertIn("catalog not refreshed (is codex logged in and online?)", stale.stderr)
        self.write_cache(catalog, client_version="0.1.0")
        mismatch = self.call("codex", "sol")
        self.assert_failure(mismatch, 2)
        self.assertIn("'0.1.0'", mismatch.stderr)
        self.assertIn("'0.159.0'", mismatch.stderr)
        self.write_cache(catalog, models=[{"slug": "gpt-6-sol"}])
        mismatch = self.call("codex", "sol")
        self.assert_failure(mismatch, 2)
        self.assertIn("output did not come from the refreshed cache", mismatch.stderr)
        self.write_cache(catalog)
        self.write_fixture(catalog["models"], models_exit=7)
        self.assert_failure(self.call("codex", "sol"), 2)
        self.write_fixture(catalog["models"], models_output="not json")
        self.assert_failure(self.call("codex", "sol"), 2)
        self.write_fixture(catalog["models"], version_exit=1)
        self.assert_failure(self.call("codex", "sol"), 2)
        self.write_fixture([], )
        empty = json.loads(self.fixture.read_text(encoding="utf-8"))["catalog"]
        self.write_cache(empty)
        self.assert_failure(self.call("codex", "sol"), 2)
        self.assert_failure(self.call("codex", "gpt-5.5"), 2)
        self.assert_failure(self.call("codex", "o3"), 2)

    def test_codex_missing_binary_and_unsupported_effort(self):
        catalog = self.write_fixture()
        self.write_cache(catalog)
        self.assert_failure(self.call("codex", "luna", "--effort", "ultra"), 3)
        self.assert_failure(self.call("codex", "sol", "--effort", "nonsense"), 3)
        self.assert_failure(self.call("codex", "sol", env={"PATH": str(self.root / "empty-path")}), 2)

    def test_claude_aliases_and_effort(self):
        for value, alias in (("opus", "opus"), ("claude-opus-5-5", "opus"),
                             ("claude-3-5-sonnet-20241022", "sonnet"),
                             ("claude-haiku-4-5", "haiku"), ("claude-fable-1-0", "fable")):
            with self.subTest(value=value):
                result = self.call("claude", value, "--effort", "xhigh")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, alias + "\n")
                self.assertEqual(result.stderr, "" if value == alias else
                                 f"latest-model: using {alias} (newest {alias}) instead of {value}\n")
        self.assert_failure(self.call("claude", "claude-opus-sonnet-5"), 2)
        self.assert_failure(self.call("claude", "codex-model"), 2)
        self.assert_failure(self.call("claude", "opus", "--effort", "ultra"), 3)

    def test_claude_environment_and_each_settings_location_override(self):
        env_result = self.call("claude", "sonnet", env={"ANTHROPIC_DEFAULT_SONNET_MODEL": "custom"})
        self.assert_failure(env_result, 2)
        self.assertIn("environment", env_result.stderr)
        paths = [
            self.root / "managed-settings.json",
            self.root / "claude-config/settings.json",
            self.project / ".claude/settings.json",
            self.project / ".claude/settings.local.json",
        ]
        for path in paths:
            with self.subTest(path=str(path)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "custom"}}), encoding="utf-8")
                result = self.call("claude", "opus")
                self.assert_failure(result, 2)
                self.assertIn("ANTHROPIC_DEFAULT_OPUS_MODEL", result.stderr)
                self.assertIn(str(path), result.stderr)
                path.unlink()

    def test_claude_invalid_settings_file_is_named(self):
        path = self.project / ".claude/settings.local.json"
        path.parent.mkdir()
        path.write_text("not json", encoding="utf-8")
        result = self.call("claude", "opus")
        self.assert_failure(result, 2)
        self.assertIn(str(path), result.stderr)

    def test_latest_model_copies_are_byte_identical_and_executable(self):
        paths = [ROOT / f"plugins/{name}/scripts/latest-model.py" for name in
                 ("peer-coding", "free-hands", "harness", "ux-ui")]
        for path in paths:
            self.assertTrue(path.is_file(), str(path))
            self.assertTrue(path.stat().st_mode & 0o111, str(path))
            self.assertEqual(path.read_bytes(), paths[0].read_bytes(), str(path))


if __name__ == "__main__":
    unittest.main()
