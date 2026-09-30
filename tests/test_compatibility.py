"""Run with python3 -m unittest discover -s tests -v. No installed settings are changed."""
import json
import os
from pathlib import Path
import shutil
import subprocess
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
                         'if os.environ.get("BIN_TEST_FAIL") == "plugin" and "harness@bin" in sys.argv: sys.exit(1)\n')
            f.chmod(0o755)
        env = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "BIN_TEST_LOG": str(log)}
        installer = ["bash", str(ROOT / "install.sh"), "--only", "harness"]
        for host, extra, expected in [
            ("claude", ["--scope", "project"], ["claude", "plugin", "install", "harness@bin", "--scope", "project"]),
            ("codex", ["--host", "codex", "--scope", "user"], ["codex", "plugin", "add", "harness@bin"]),
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
        plugin = ROOT / "plugins/claude-x-codex"
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
            self.assertEqual("[claude-x-codex: ON]" in result.stdout, mode == "on")
            if mode == "on":
                context = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual(context["hookEventName"], "UserPromptSubmit")
                self.assertIn("[claude-x-codex: ON]", context["additionalContext"])
            else:
                self.assertEqual(result.stdout, "")
        result = run(["bash", str(plugin / "hooks/mode-context.sh")], self.repo,
                     payload='{"prompt":"$claude-x-codex:mode off"}', env={"CXC_MODE": "on", "CLAUDE_PLUGIN_ROOT": str(plugin)})
        self.assertEqual(result.stdout, "")
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
        mode = ROOT / "plugins/claude-x-codex/scripts/mode.sh"
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
        audit = ROOT / "plugins/claude-x-codex/scripts/context-audit.sh"
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        result = run(["bash", str(audit)], self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CHECK: Codex selects AGENTS.override.md", result.stdout)
        self.assertIn("invalid: expected an entry with a hooks list", result.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
