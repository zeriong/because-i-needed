"""free-hands: the hook guard and the panel's deterministic protocol."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "free-hands"
GUARD = PLUGIN / "scripts" / "guard.py"
PANEL = PLUGIN / "scripts" / "panel.py"
ROLES = ("quick-thinker", "deep-thinker", "evidence-hunter", "trend-tracker", "devils-advocate")


def goal_text(status="active", items=("- [ ] first", "- [x] second"), max_iterations="40", iterations="0"):
    lines = [f"status: {status}"]
    if max_iterations is not None:
        lines.append(f"max_iterations: {max_iterations}")
    if iterations is not None:
        lines.append(f"iterations: {iterations}")
    return "\n".join(lines + ["## Goal", "ship it", "## Checklist", *items, "## Decisions", "## Resume", ""])


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        (self.repo / "sub").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.goal = self.repo / ".free-hands" / "goal.md"

    def tearDown(self):
        for path in self.tmp.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        shutil.rmtree(self.tmp)

    def write(self, text):
        self.goal.parent.mkdir(exist_ok=True)
        self.goal.write_text(text)

    def hook(self, mode, payload=None, env=None):
        data = {"cwd": str(self.repo / "sub"), **(payload or {})}
        environ = {k: v for k, v in os.environ.items() if k not in ("FREE_HANDS_ROLE", "CLAUDE_PROJECT_DIR")}
        result = subprocess.run([sys.executable, str(GUARD), mode], input=json.dumps(data), capture_output=True,
                                text=True, cwd=self.tmp, env={**environ, **(env or {})})
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def test_ask_is_denied_only_while_active_with_open_items(self):
        self.write(goal_text())
        out = self.hook("ask", {"tool_name": "AskUserQuestion"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("1 items left", out["hookSpecificOutput"]["permissionDecisionReason"])
        self.write(goal_text(status="paused"))
        self.assertIsNone(self.hook("ask"))
        for status in ("done", "waiting"):  # a finished status cannot end the run while items are open
            self.write(goal_text(status=status))
            self.assertEqual(self.hook("ask")["hookSpecificOutput"]["permissionDecision"], "deny", status)
            self.write(goal_text(status=status, items=("- [x] a", "- [-] b — needs the user: merge")))
            self.assertIsNone(self.hook("ask"), status)
        self.write(goal_text(status="finished"))
        self.assertIsNone(self.hook("ask"))
        self.write(goal_text(items=("- [x] a", "- [-] b — needs the user: merge")))
        self.assertIsNone(self.hook("ask"))
        self.write("not a goal file\n")
        self.assertIsNone(self.hook("ask"))
        self.goal.write_bytes(b"\xff\xfe\x00")
        self.assertIsNone(self.hook("ask"))
        self.goal.unlink()
        self.assertIsNone(self.hook("ask"))

    def test_stop_blocks_only_after_the_counter_is_on_disk(self):
        self.write(goal_text(iterations="0"))
        out = self.hook("stop")
        self.assertEqual(out["decision"], "block")
        self.assertIn("- [ ] first", out["reason"])
        self.assertIn("continuation 1/40", out["reason"])
        self.assertIn("iterations: 1", self.goal.read_text())

    def test_stop_is_allowed_at_max_and_warns_on_the_last_continuation(self):
        self.write(goal_text(max_iterations="2", iterations="1"))
        out = self.hook("stop")
        self.assertIn("last continuation", out["reason"])
        self.assertIn("iterations: 2", self.goal.read_text())
        self.assertIsNone(self.hook("stop"))
        self.assertIn("iterations: 2", self.goal.read_text())

    def test_malformed_counters_mean_no_effect(self):
        for max_iterations, iterations in (("many", "0"), ("40", "-1"), (None, "0"), ("40", None), ("0", "0"),
                                           ("40", "0 garbage"), ("40", "0 999"), ("40 x", "0")):
            text = goal_text(max_iterations=max_iterations, iterations=iterations)
            self.write(text)
            for mode in ("stop", "ask", "session"):
                self.assertIsNone(self.hook(mode), (mode, max_iterations, iterations))
            self.assertEqual(self.goal.read_text(), text)

    def test_at_the_limit_asking_is_allowed_and_the_note_says_pause(self):
        self.write(goal_text(max_iterations="2", iterations="2"))
        self.assertIsNone(self.hook("ask"))
        self.assertIsNone(self.hook("stop"))
        context = self.hook("session")["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[free-hands: LIMIT]", context)
        self.assertIn("status: paused", context)

    def test_malformed_hook_input_means_no_effect(self):
        self.write(goal_text())
        environ = {k: v for k, v in os.environ.items() if k not in ("FREE_HANDS_ROLE",)}
        for raw in ("{broken", "[1, 2]", ""):
            for mode in ("ask", "stop", "prompt"):
                result = subprocess.run([sys.executable, str(GUARD), mode], input=raw, capture_output=True, text=True,
                                        cwd=self.repo, env={**environ, "CLAUDE_PROJECT_DIR": str(self.repo)})
                self.assertEqual((result.returncode, result.stdout), (0, ""), (raw, mode))
        self.assertIn("iterations: 0", self.goal.read_text())

    def test_the_temporary_file_never_follows_a_planted_link(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("free_hands_guard", GUARD)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        self.write(goal_text())
        outside = self.tmp / "outside.txt"
        outside.write_text("keep me")
        for pid in (os.getpid(), 4242):
            (self.goal.parent / f"goal.md.tmp.{pid}").symlink_to(outside)
        real_getpid = guard.os.getpid
        guard.os.getpid = lambda: 4242
        try:
            self.assertIsNotNone(guard.bump(self.goal))
        finally:
            guard.os.getpid = real_getpid
        self.assertEqual(outside.read_text(), "keep me")
        self.assertIn("iterations: 1", self.goal.read_text())

    def test_stop_is_allowed_when_the_counter_cannot_be_written(self):
        self.write(goal_text())
        self.goal.parent.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            self.assertIsNone(self.hook("stop"))
        finally:
            self.goal.parent.chmod(0o755)
        self.assertIn("iterations: 0", self.goal.read_text())

    def test_concurrent_stops_each_count(self):
        self.write(goal_text())
        threads = [threading.Thread(target=self.hook, args=("stop",)) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertIn("iterations: 2", self.goal.read_text())

    def test_a_finished_status_with_open_items_keeps_the_run_going(self):
        self.write(goal_text(status="waiting"))
        out = self.hook("stop")
        self.assertEqual(out["decision"], "block")
        self.assertIn("`status: waiting` does not end the run", out["reason"])
        self.assertIn("iterations: 1", self.goal.read_text())
        context = self.hook("session")["hookSpecificOutput"]["additionalContext"]
        self.assertIn("says `status: waiting`", context)
        self.assertIn("status: paused", context)

    def test_only_checklist_items_outside_code_count(self):
        quoted = goal_text(status="done", items=("- [x] first",)).replace(
            "## Decisions", "## Decisions\n- example: `- [ ] like this`\n```markdown\n- [ ] quoted item\n```\n- [ ] note")
        quoted = quoted.replace("## Resume", "## Resume\n- [ ] resume line")
        self.write(quoted)
        for mode in ("ask", "stop", "session"):
            self.assertIsNone(self.hook(mode), mode)
        fenced = goal_text(items=("```", "- [ ] inside a fence", "```", "- [x] done"))
        self.write(fenced)
        self.assertIsNone(self.hook("ask"))
        for status in ("done", "waiting"):
            for outer, inner in (("````", "```"), ("~~~~", "~~~"), ("```", "~~~")):
                nested = goal_text(status=status, items=("- [x] done",)).replace(
                    "## Decisions", f"## Decisions\n{outer}markdown\n{inner}\n## Checklist\n- [ ] example\n{inner}\n"
                                    f"- [ ] still inside\n{outer}")
                self.write(nested)
                self.assertIsNone(self.hook("ask"), (status, outer, inner))
        self.write(goal_text(items=("- [ ] real", "```", "- [ ] fenced", "```")))
        self.assertIn("1 items left", self.hook("ask")["hookSpecificOutput"]["permissionDecisionReason"])

    def test_stop_is_allowed_without_open_items_or_goal(self):
        self.write(goal_text(items=("- [x] a", "- [-] b — needs the user: deploy")))
        self.assertIsNone(self.hook("stop"))
        self.write(goal_text(status="paused"))
        self.assertIsNone(self.hook("stop"))
        self.goal.unlink()
        self.assertIsNone(self.hook("stop"))

    def test_role_children_are_never_guarded(self):
        self.write(goal_text())
        for mode in ("ask", "stop", "session", "prompt"):
            self.assertIsNone(self.hook(mode, {"prompt": "free-hands"}, env={"FREE_HANDS_ROLE": "deep-thinker"}))
        self.assertIn("iterations: 0", self.goal.read_text())

    def test_restore_note_only_while_active(self):
        self.write(goal_text())
        out = self.hook("session", {"source": "compact"})
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn(str(self.goal), context)
        self.assertIn(str(PLUGIN / "skills" / "run" / "SKILL.md"), context)
        out = self.hook("prompt", {"prompt": "continue"})
        self.assertIn("[free-hands: ACTIVE]", out["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("again during the run", out["hookSpecificOutput"]["additionalContext"])
        self.write(goal_text(status="done", items=("- [x] first",)))
        self.assertIsNone(self.hook("session"))
        self.assertIsNone(self.hook("prompt", {"prompt": "continue"}))

    def test_prompt_routes_the_word(self):
        out = self.hook("prompt", {"prompt": "free-hands로 이 이슈 다 처리해줘"})
        self.assertIn("[free-hands: entry]", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIsNone(self.hook("prompt", {"prompt": "fix the login bug"}))
        notice = "<task-notification>agent free-hands:deep-thinker completed</task-notification>"
        self.assertIsNone(self.hook("prompt", {"prompt": notice}))
        for command in ("/free-hands:run finish the migration", "  $free-hands:run finish the migration"):
            self.assertIsNone(self.hook("prompt", {"prompt": command}))
        self.write(goal_text())
        out = self.hook("prompt", {"prompt": "이건 free-hands 가 아니잖아"})
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[free-hands: ACTIVE]", context)
        self.assertIn("again during the run", context)
        context = self.hook("prompt", {"prompt": notice})["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[free-hands: ACTIVE]", context)
        self.assertNotIn("again during the run", context)
        quoted = f"free-hands 아니잖아, 이 로그 봐: {notice}"
        self.assertIn("again during the run", self.hook("prompt", {"prompt": quoted})["hookSpecificOutput"]["additionalContext"])
        self.goal.unlink()
        out = self.hook("prompt", {"prompt": f"free-hands로 이 로그를 고쳐줘: {notice}"})
        self.assertIn("[free-hands: entry]", out["hookSpecificOutput"]["additionalContext"])

    def test_root_comes_from_the_hook_cwd(self):
        self.write(goal_text())
        out = self.hook("ask", {"cwd": str(self.repo / "sub")})
        self.assertIn(str(self.goal), out["hookSpecificOutput"]["permissionDecisionReason"])
        plain = self.tmp / "plain"
        (plain / ".free-hands").mkdir(parents=True)
        (plain / ".free-hands" / "goal.md").write_text(goal_text())
        self.assertIsNotNone(self.hook("ask", {"cwd": str(plain)}))


def reply(option, **extra):
    return {"option": option, "new_option": "", "reasons": ["because"], "evidence": [{"claim": "c", "source": "s"}],
            "risks": [], "confidence": "medium", "would_change_if": "x", **extra}


class PanelTallyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.brief = self.tmp / "brief.json"
        self.brief.write_text(json.dumps({"question": "q", "options": [{"id": "A", "text": "a"},
                                                                     {"id": "B", "text": "b"}]}))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def round(self, name, replies):
        directory = self.tmp / name
        directory.mkdir(exist_ok=True)
        for role, value in replies.items():
            path = directory / f"{role}.json"
            path.write_text(value if isinstance(value, str) else json.dumps(value))
        return directory

    def tally(self, directory, attempt):
        result = subprocess.run([sys.executable, str(PANEL), "tally", str(directory), "--brief", str(self.brief),
                                 "--attempt", str(attempt)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_consensus_decides_in_round_one(self):
        out = self.tally(self.round("round1", {role: reply("A") for role in ROLES}), 1)
        self.assertEqual((out["round"], out["next"], out["options"]), (1, "decide", {"A": sorted(ROLES)}))
        self.assertFalse((self.tmp / "round2-brief.json").exists())

    def test_split_writes_a_round_two_brief_with_every_position(self):
        replies = {role: reply("A" if i < 3 else "B") for i, role in enumerate(ROLES)}
        out = self.tally(self.round("round1", replies), 1)
        self.assertEqual(out["next"], "round2")
        second = json.loads((self.tmp / "round2-brief.json").read_text())
        self.assertEqual(second["round"], 2)
        self.assertEqual(sorted(p["role"] for p in second["positions"]), sorted(ROLES))
        self.assertEqual(second["question"], "q")

    def test_round_two_always_decides(self):
        replies = {role: reply("A" if i < 3 else "B") for i, role in enumerate(ROLES)}
        self.assertEqual(self.tally(self.round("round2", replies), 1)["next"], "decide")

    def test_failures_retry_once_then_count_as_missing(self):
        replies = {role: reply("A") for role in ROLES[:3]}
        replies[ROLES[3]] = "{broken"
        out = self.tally(self.round("round1", replies), 1)
        self.assertEqual(out["next"], "retry")
        self.assertEqual(sorted(out["retry"]), sorted(ROLES[3:]))
        out = self.tally(self.tmp / "round1", 2)
        self.assertEqual(out["next"], "decide")
        self.assertEqual(out["missing"], [ROLES[4]])
        self.assertIn(ROLES[3], out["invalid"])

    def test_missing_replies_are_not_agreement(self):
        out = self.tally(self.round("round1", {ROLES[0]: reply("A"), ROLES[1]: reply("A")}), 2)
        self.assertEqual(out["next"], "decide-alone")

    def test_any_json_value_is_validated_without_crashing(self):
        bad = {ROLES[0]: reply("A", confidence=[]), ROLES[1]: reply("A", confidence={}),
               ROLES[2]: {k: v for k, v in reply("A").items() if k != "new_option"},
               ROLES[3]: reply("A", extra="x"), ROLES[4]: reply("A", new_option=3)}
        out = self.tally(self.round("round1", bad), 2)
        self.assertEqual(sorted(out["invalid"]), sorted(ROLES))
        self.assertEqual(out["next"], "decide-alone")

    def test_contract_violations_are_invalid(self):
        bad = {ROLES[0]: reply("C"), ROLES[1]: reply("NEW"), ROLES[2]: reply("A", confidence="sure"),
               ROLES[3]: reply("A", reasons=[]), ROLES[4]: reply("NEW", new_option="split the table")}
        out = self.tally(self.round("round1", bad), 2)
        self.assertEqual(sorted(out["invalid"]), sorted(ROLES[:4]))
        self.assertEqual(out["options"], {"NEW: split the table": [ROLES[4]]})
        self.assertEqual(out["next"], "decide-alone")


class PanelRunTest(unittest.TestCase):
    """The Codex route, with a fake resolver and a fake `codex` that records how it was started."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.plugin = self.tmp / "free-hands"
        shutil.copytree(PLUGIN, self.plugin)
        (self.plugin / "scripts" / "latest-model.py").write_text(
            "import sys\nhost, family = sys.argv[1], sys.argv[2]\n"
            "if family == 'sol' and '--fail-sol' in open(__file__ + '.flags').read():\n"
            "    print('latest-model: no listed model', file=sys.stderr); sys.exit(2)\n"
            "print(f'fake-{host}-{family}')\n")
        (self.plugin / "scripts" / "latest-model.py.flags").write_text("")
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        codex = bin_dir / "codex"
        codex.write_text(
            "#!/usr/bin/env python3\nimport json, os, sys\nargv = sys.argv[1:]\n"
            "out = argv[argv.index('-o') + 1]\nmodel = argv[argv.index('-m') + 1]\n"
            "print('model: ' + model)\n"
            "json.dump({'argv': argv, 'role': os.environ.get('FREE_HANDS_ROLE'), 'cxc': os.environ.get('CXC_MODE')},"
            " open(out + '.call', 'w'))\n"
            "json.dump({'option': 'A', 'new_option': '', 'reasons': ['r'], 'evidence': [], 'risks': [],"
            " 'confidence': 'low', 'would_change_if': ''}, open(out, 'w'))\n")
        codex.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
        self.brief = self.tmp / "brief.json"
        self.brief.write_text(json.dumps({"question": "q", "options": [{"id": "A", "text": "a"}]}))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_panel(self, *args):
        result = subprocess.run([sys.executable, str(self.plugin / "scripts" / "panel.py"), *args],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_children_are_read_only_role_scoped_and_use_the_resolved_model(self):
        out_dir = self.tmp / "round1"
        meta = self.run_panel("run", str(out_dir), "--brief", str(self.brief))
        for role in ROLES:
            call = json.loads((out_dir / f"{role}.json.call").read_text())
            argv = call["argv"]
            self.assertEqual(call["role"], role)
            self.assertEqual(call["cxc"], "off")
            self.assertEqual(argv[argv.index("-s") + 1], "read-only")
            web = role in ("evidence-hunter", "trend-tracker")
            self.assertEqual(argv[0] == "--search", web, role)
            self.assertEqual(argv[1 if web else 0], "exec", role)
            family = "sol" if role in ("deep-thinker", "devils-advocate") else "luna"
            self.assertEqual(argv[argv.index("-m") + 1], f"fake-codex-{family}")
            self.assertEqual(meta[role]["ran"], f"fake-codex-{family}")
            self.assertIn("Decision brief", argv[-1])
        tally = subprocess.run([sys.executable, str(PANEL), "tally", str(out_dir), "--brief", str(self.brief),
                                "--attempt", "1"], capture_output=True, text=True)
        self.assertEqual(json.loads(tally.stdout)["next"], "decide")

    def test_a_role_whose_model_cannot_be_resolved_is_not_started(self):
        (self.plugin / "scripts" / "latest-model.py.flags").write_text("--fail-sol")
        out_dir = self.tmp / "round1"
        meta = self.run_panel("run", str(out_dir), "--brief", str(self.brief), "--roles", "deep-thinker,quick-thinker")
        self.assertEqual(meta["deep-thinker"]["exit"], 2)
        self.assertFalse((out_dir / "deep-thinker.json").exists())
        self.assertTrue((out_dir / "quick-thinker.json").exists())

    def test_stale_replies_are_removed_before_a_role_runs(self):
        out_dir = self.tmp / "round1"
        out_dir.mkdir()
        for role in ROLES:
            (out_dir / f"{role}.json").write_text(json.dumps(reply("A")))
        (self.plugin / "scripts" / "latest-model.py.flags").write_text("--fail-sol")
        self.run_panel("run", str(out_dir), "--brief", str(self.brief))
        for role in ("deep-thinker", "devils-advocate"):
            self.assertFalse((out_dir / f"{role}.json").exists(), role)
        tally = subprocess.run([sys.executable, str(PANEL), "tally", str(out_dir), "--brief", str(self.brief),
                                "--attempt", "2"], capture_output=True, text=True)
        self.assertEqual(sorted(json.loads(tally.stdout)["missing"]), ["deep-thinker", "devils-advocate"])

    def test_a_child_that_cannot_start_is_recorded_and_the_rest_still_run(self):
        self.env["PATH"] = "/nonexistent"
        out_dir = self.tmp / "round1"
        result = subprocess.run([sys.executable, str(self.plugin / "scripts" / "panel.py"), "run", str(out_dir),
                                 "--brief", str(self.brief)], capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        meta = json.loads(result.stdout)
        self.assertTrue(all("could not start" in meta[role]["error"] for role in ROLES), meta)

    @unittest.skipUnless(shutil.which("codex"), "codex CLI not installed")
    def test_the_real_codex_cli_accepts_the_child_arguments(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("free_hands_panel", PANEL)
        panel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(panel)
        for role in ROLES:
            argv = panel.child_argv(role, {"model": "probe", "effort": "high"}, self.tmp / "x.json", "prompt")
            result = subprocess.run(argv[:-1] + ["--help"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, (role, result.stderr[-300:]))

    def test_unknown_roles_are_refused_before_any_file_is_touched(self):
        victim = self.tmp / "victim"
        for suffix in (".json", ".meta.json", ".log"):
            Path(f"{victim}{suffix}").write_text("keep")
        out_dir = self.tmp / "round1"
        for roles in (str(victim), f"../{victim.name}", "quick-thinker,nobody"):
            result = subprocess.run([sys.executable, str(self.plugin / "scripts" / "panel.py"), "run", str(out_dir),
                                     "--brief", str(self.brief), "--roles", roles], capture_output=True, text=True,
                                    env=self.env)
            self.assertNotEqual(result.returncode, 0, roles)
            self.assertIn("unknown roles", result.stderr)
        for suffix in (".json", ".meta.json", ".log"):
            self.assertEqual(Path(f"{victim}{suffix}").read_text(), "keep")
        self.assertFalse((out_dir / "quick-thinker.json").exists())

    def test_models_lists_every_role(self):
        out = self.run_panel("models", "--host", "claude")
        self.assertEqual(sorted(out), sorted(ROLES))
        self.assertEqual(out["deep-thinker"]["model"], "fake-claude-opus")


if __name__ == "__main__":
    unittest.main()
