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



SHELL_CASES = [  # (where, command, denied). where: "feature" = repo on feature, "main" = a clone on main.
    # direct forms and wrappers
    ("feature", "gh pr merge 1 --squash", True), ("feature", "CI=1 gh pr merge 1", True),
    ("feature", "bash -lc 'gh pr merge 1'", True), ("feature", "bash -o pipefail -c 'gh pr merge 1'", True),
    ("feature", "(gh pr merge 1)", True), ("feature", 'echo "$(gh pr merge 1)"', True),
    ("feature", "echo `gh pr merge 1`", True), ("feature", "/usr/local/bin/gh pr merge 1", True),
    ("feature", "sudo -u bob -- gh pr merge 1", True), ("feature", "env -u X gh pr merge 1", True),
    ("feature", "env -S 'gh pr merge 1'", True), ("feature", "exec -a ignored gh pr merge 1", True),
    ("feature", "time gh pr merge 1", True), ("feature", "timeout 30 gh pr merge 1", True),
    ("feature", ">/dev/null gh pr merge 1", True), ("feature", "2>/dev/null gh pr merge 1", True),
    ("feature", "{ gh pr merge 1; }", True), ("feature", "if true; then gh pr merge 1; fi", True),
    ("feature", "gh pr merge 1 2>&1 | tee log", True), ("feature", "gh pr me\\\nrge 1", True),
    ("feature", "g\\\nh pr merge 1", True), ("feature", '"g"h pr merge 1', True), ("feature", "g'h' pr merge 1", True),
    ("feature", "gh --repo o/r pr merge 1", True), ("feature", "gh pr --repo o/r merge 1", True),
    ("feature", "gh pr merge 1 --subject 'fix; cleanup'", True), ("feature", "gh pr merge 1 --subject --help", True),
    # literals, comments, heredocs
    ("feature", "gh pr merge --help", False), ("feature", "gh pr view 1", False), ("feature", "gh --repo o/r pr view 1", False),
    ("feature", "gh pr create --base main", False), ("feature", "gh issue comment 1 -b hi", False),
    ("feature", "echo 'gh pr merge 1'", False), ("feature", 'echo ";"', False),
    ("feature", "printf '%s' '$(gh pr merge 1)'", False), ("feature", 'printf "%s" "\\$(gh pr merge 1)"', False),
    ("feature", "echo hi # $(gh pr merge 1)", False), ("feature", "git status # it's safe", False),
    ("feature", "# gh pr merge 1\nls", False), ("feature", "cat <<'EOF'\ngh pr merge 1\nEOF", False),
    ("feature", "cat <<-EOF\n\tgh pr merge 1\n\tEOF", False), ("feature", "echo '<<EOF'\ngh pr merge 1\nEOF", True),
    ("feature", "# <<EOF\ngh pr merge 1\nEOF", True), ("feature", "cat <<<EOF\ngh pr merge 1\nEOF", True),
    ("feature", "bash <<'EOF'\ngh pr merge 1\nEOF", False), ("feature", "git commit -m \"it's done\"", False),
    ("feature", "git commit -m it's", True), ("feature", "command -v gh", False),
    # git push
    ("feature", "git push origin HEAD:main", True), ("feature", "git push origin +main", True),
    ("feature", "git push origin refs/heads/main", True), ("feature", "git push --repo=origin HEAD:main", True),
    ("feature", "git push origin feature", False), ("feature", "git push --force origin feature", False),
    ("feature", "git push -u origin feature", False), ("feature", "git push", False),
    ("feature", "git push --dry-run origin main", False), ("feature", "git push origin --delete old", True),
    ("feature", "git push origin :old", True), ("feature", "git push origin +:old", True),
    ("feature", "git push origin :", True), ("feature", "git push origin 'refs/heads/*:refs/heads/*'", True),
    ("feature", "git push --all origin", True), ("feature", "git push --mirror", True),
    ("feature", "git push --prune origin", True), ("feature", "git push --tags origin", False),
    ("feature", "git -C . push origin main", True), ("feature", "git switch main && git push", True),
    ("feature", "git -c remote.origin.push=HEAD:main push origin", True),
    ("feature", "git -c remote.origin.push=HEAD:feature push origin", False),
    ("feature", "git push upstream HEAD:trunk", True), ("feature", "git push origin HEAD:trunk", False),
    ("main", "git push -o ci.skip origin", True), ("main", "git push", True),
    # git merge / pull and state
    ("feature", "git merge main", False), ("feature", "git switch main && git merge feature", True),
    ("feature", "git checkout main; git merge origin/main", False), ("feature", "git switch main && git merge --abort", False),
    ("feature", "(git switch main) && git merge feature", True), ("feature", "echo $(git switch main); git merge feature", True),
    ("feature", "git switch main; cd plugins; git merge feature", True),
    ("feature", "git switch main; git -C plugins merge feature", True), ("feature", "git switch -- main && git merge x", True),
    ("main", "false && git switch feature; git merge feature", True), ("main", "true || git switch feature; git merge feature", True),
    ("main", "git checkout feature -- README.md; git merge feature", True), ("main", "git switch feature && git merge main", False),
    ("main", "git merge upstream/main", True), ("main", "git merge --message sync origin/main", False),
    ("main", "git pull", False), ("main", "git pull origin main", False), ("main", "git pull origin feature", True),
    # gh api
    ("feature", "gh api repos/o/r/pulls/1/merge", False), ("feature", "gh api -X PUT repos/o/r/pulls/1/merge", True),
    ("feature", "gh api -XPUT repos/o/r/pulls/1/merge", True), ("feature", "gh api repos/o/r/pulls/1/merge -f merge_method=squash", True),
    ("feature", "gh api repos/o/r/pulls/1/merge -fmerge_method=squash", True),
    ("feature", "gh api -H 'Accept: application/vnd.github+json' -X PUT repos/o/r/pulls/1/merge", True),
    ("feature", "gh api repos/o/r/pulls/1/merge -XGET -f x=1", False), ("feature", "gh api -X PUT 'repos/o/r/pulls/1/merge?x=1'", True),
    ("feature", "gh api -X DELETE repos/o/r/git/refs/heads/x", True), ("feature", "gh api -X DELETE repos/o/r", True),
    ("feature", "gh api graphql -f query='mutation{mergePullRequest(input:{})}'", True),
    ("feature", "gh api graphql -f query='{viewer{login}}'", False), ("feature", "gh repo delete o/r --yes", True),
    ("feature", "gh release delete v1", True), ("feature", "gh release create v1", True), ("feature", "gh release upload v1 a.zip", True),
    ("feature", "gh release view v1", False), ("feature", "gh release list", False),
    # publish / deploy / send
    ("feature", "npm publish", True), ("feature", "pnpm publish", True), ("feature", "yarn npm publish", True),
    ("feature", "npm --prefix . publish", True), ("feature", "npm publish --dry-run", False), ("feature", "npm publish --dry-run=true", False),
    ("feature", "npm publish --dry-run=false", True), ("feature", "npm publish --dry-run --no-dry-run", True),
    ("feature", "npm run publish", False), ("feature", "npx vercel --prod", True), ("feature", "npm exec -- vercel deploy", True),
    ("feature", "npm exec --package vercel -- vercel deploy", True), ("feature", "vercel", True), ("feature", "vercel env ls", False),
    ("feature", "vercel dev", False), ("feature", "docker push x/y", True), ("feature", "docker --context prod push x/y", True),
    ("feature", "docker buildx build --push .", True), ("feature", "docker buildx build --push=true .", True),
    ("feature", "docker buildx build --push=false .", False), ("feature", "docker build .", False),
    ("feature", "kubectl apply -f k.yaml", True), ("feature", "kubectl --context prod apply -f k.yaml", True),
    ("feature", "kubectl apply -f k.yaml --dry-run=client", False), ("feature", "kubectl apply -f k.yaml --dry-run=server", False),
    ("feature", "kubectl apply -f k.yaml --dry-run=none", True), ("feature", "kubectl create ns x", True),
    ("feature", "kubectl replace -f k.yaml", True), ("feature", "kubectl patch deploy x -p '{}'", True),
    ("feature", "kubectl delete pod x", True), ("feature", "kubectl get pods", False), ("feature", "kubectl diff -f k.yaml", False),
    ("feature", "kubectl --context prod get pods", False), ("feature", "terraform plan", False), ("feature", "terraform apply", True),
    ("feature", "terraform -chdir=infra destroy", True), ("feature", "terraform validate", False),
    ("feature", "helm upgrade x y", True), ("feature", "helm install x y", True), ("feature", "helm uninstall x", True),
    ("feature", "helm list", False), ("feature", "helm template x y", False), ("feature", "sendmail a@b.c", True),
    ("feature", "mail -s hi a@b.c", True), ("feature", "mutt a@b.c", True), ("feature", "cargo publish", True),
    ("feature", "cargo publish --dry-run", False), ("feature", "twine upload dist/*", True), ("feature", "gem push x.gem", True),
    ("feature", "gem build x.gemspec", False), ("feature", "netlify deploy", True), ("feature", "fly deploy", True),
    ("feature", "fly status", False), ("feature", "firebase deploy", True), ("feature", "firebase emulators:start", False),
    # delta review r2 (R07, R13, R16–R18, R22, R23)
    ("feature", "npm --loglevel verbose publish", True), ("feature", "npm --loglevel verbose run build", False),
    ("feature", "npm --prefix . exec -- vercel deploy", True), ("feature", "kubectl --request-timeout 30s apply -f k.yaml", True),
    ("feature", "kubectl --request-timeout 30s get pods", False), ("feature", "kubectl rollout restart deploy/x", True),
    ("feature", "kubectl rollout status deploy/x", False),
    ("feature", "helm --kube-apiserver https://api.example install x y", True),
    ("feature", "helm --kube-apiserver https://api.example list", False), ("feature", "helm push chart.tgz oci://r", True),
    ("main", "git switch -c feature; git merge feature", True), ("main", "git status && git switch feature && git push", False),
    ("main", "git switch -C feature; git merge main", False), ("main", "git checkout -b feature; git merge feature", True),
    ("tracker", "git push", True), ("tracker", "git push origin HEAD:work", False),
    ("feature", "git -c push.default=matching push origin", True), ("feature", "git -c remote.origin.mirror=true push origin", True),
    ("feature", "git -c remote.origin.push=refs/heads/feature:refs/heads/main push origin feature", True),
    ("feature", "git -c remote.origin.push=feature:main push origin feature", False),  # git ignores short sources
    ("main", "git -c remote.origin.push=refs/heads/main:refs/heads/feature push origin main", False),
    ("feature", "npm exec --workspace web -- vercel deploy", True), ("feature", "npm exec --workspace=web -- vercel deploy", True),
    ("feature", "npm exec --workspace web -- vercel env ls", False), ("feature", "vercel alias rm app.example.com --yes", True),
    ("feature", "git -c 'remote.origin.push=refs/heads/*:refs/heads/*' push origin main", True),
    ("main", "git pull upstream main", True), ("main", "git pull upstream feature", True),
    ("feature", "vercel redeploy abc.vercel.app", True), ("feature", "vercel promote abc.vercel.app", True),
    ("feature", "vercel rollback abc.vercel.app", True), ("feature", "vercel remove abc.vercel.app --yes", True),
    ("feature", "vercel promote status", False), ("feature", "vercel alias ls", False), ("feature", "vercel alias set a b", True),
    ("feature", "gh api repos/o/r/releases -f tag_name=v1", True), ("feature", "gh api repos/o/r/releases", False),
    ("feature", "gh api -X PATCH repos/o/r/releases/1 -F draft=false", True),
    ("feature", "gh api repos/o/r/issues/1/comments -f body=hi", False),
    # not covered on purpose (core scope)
    ("feature", "rm -rf ../outside", False), ("feature", "psql -c 'DROP TABLE x'", False),
]


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=l", "-c", "user.email=l@x", *args], cwd=cwd, check=True,
                   capture_output=True, text=True)


class ShellGuardTest(unittest.TestCase):
    """scripts/shellguard.py decisions on realistic repositories, and guard.py's shell mode around them."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("free_hands_shellguard", PLUGIN / "scripts" / "shellguard.py")
        cls.sg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sg)
        cls.tmp = Path(tempfile.mkdtemp())
        origin, upstream = cls.tmp / "origin.git", cls.tmp / "upstream.git"
        git("init", "-q", "--bare", "-b", "main", str(origin), cwd=cls.tmp)
        git("init", "-q", "--bare", "-b", "trunk", str(upstream), cwd=cls.tmp)
        repo = cls.tmp / "repo"
        git("init", "-q", "-b", "main", str(repo), cwd=cls.tmp)
        (repo / "README.md").write_text("x\n")
        (repo / "plugins").mkdir()
        (repo / "plugins" / "a.txt").write_text("a\n")
        git("add", "-A", cwd=repo)
        git("commit", "-q", "-m", "init", cwd=repo)
        git("remote", "add", "origin", str(origin), cwd=repo)
        git("push", "-q", "-u", "origin", "main", cwd=repo)
        git("remote", "set-head", "origin", "main", cwd=repo)
        git("remote", "add", "upstream", str(upstream), cwd=repo)
        git("push", "-q", "upstream", "main:trunk", cwd=repo)
        git("fetch", "-q", "upstream", cwd=repo)
        git("remote", "set-head", "upstream", "trunk", cwd=repo)
        git("checkout", "-q", "-b", "feature", cwd=repo)
        git("push", "-q", "-u", "origin", "feature", cwd=repo)
        clone = cls.tmp / "main"
        git("clone", "-q", str(origin), str(clone), cwd=cls.tmp)
        git("remote", "add", "upstream", str(upstream), cwd=clone)
        git("fetch", "-q", "upstream", cwd=clone)
        git("fetch", "-q", "origin", "feature:refs/remotes/origin/feature", cwd=clone)
        git("branch", "-q", "feature", "origin/feature", cwd=clone)
        tracker = cls.tmp / "tracker"  # a branch whose upstream and push target is upstream/trunk
        git("clone", "-q", str(origin), str(tracker), cwd=cls.tmp)
        git("remote", "add", "upstream", str(upstream), cwd=tracker)
        git("fetch", "-q", "upstream", cwd=tracker)
        git("remote", "set-head", "upstream", "trunk", cwd=tracker)
        git("checkout", "-q", "-b", "work", "--track", "upstream/trunk", cwd=tracker)
        git("config", "push.default", "upstream", cwd=tracker)
        cls.where = {"feature": str(repo), "main": str(clone), "tracker": str(tracker)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_decisions(self):
        wrong = [(where, cmd, want) for where, cmd, want in SHELL_CASES
                 if bool(self.sg.check(cmd, self.where[where])[0]) != want]
        self.assertEqual(wrong, [])
        for where in self.where.values():  # the cases never changed a repository
            self.assertEqual(subprocess.run(["git", "-C", where, "status", "--porcelain"], capture_output=True,
                                            text=True).stdout, "")

    def test_the_default_branch_comes_from_the_goal_then_the_push_remote(self):
        repo = self.where["feature"]
        self.assertTrue(self.sg.check("git push origin HEAD:trunk", repo, "trunk")[0])
        self.assertFalse(self.sg.check("git push origin HEAD:main", repo, "trunk")[0])
        self.assertEqual(self.sg.check("git push upstream HEAD:trunk", repo)[1], "upstream/HEAD")
        plain = self.tmp / "plain"
        git("init", "-q", "-b", "work", str(plain), cwd=self.tmp)
        git("commit", "-q", "--allow-empty", "-m", "i", cwd=plain)
        hit, source = self.sg.check("git push here HEAD:master", str(plain))
        self.assertTrue(hit)
        self.assertEqual(source, "assumed: main and master")
        other = self.tmp / "other"
        git("init", "-q", "-b", "main", str(other), cwd=self.tmp)
        git("commit", "-q", "--allow-empty", "-m", "i", cwd=other)
        self.assertTrue(self.sg.check(f"git --git-dir={other}/.git --work-tree={other} merge feature", repo)[0])
        for cd in ("cd -- plugins", "cd -P plugins", "cd -q plugins", "cd -LP plugins", "cd plugins"):  # R24
            self.assertTrue(self.sg.check(f"{cd} && git push origin HEAD:trunk", repo, "trunk")[0], cd)
        main = self.where["main"]
        self.assertFalse(self.sg.check("cd -- . && git merge origin/main", main, "main")[0])
        # R25: env -C runs only its own command elsewhere; the next command runs in the shell's directory
        self.assertTrue(self.sg.check(f"env -C {repo} git status; git merge feature", main)[0])
        self.assertTrue(self.sg.check(f"env --chdir={repo} git status; git merge feature", main)[0])
        self.assertFalse(self.sg.check(f"env -C {repo} git merge main", main)[0])
        # R13: a branch checked out in another worktree cannot be switched to; R16: the named remote's default
        holder = self.tmp / "holder"
        git("worktree", "add", "-q", str(holder), "feature", cwd=main)
        self.addCleanup(git, "worktree", "remove", "--force", str(holder), cwd=main)
        self.assertTrue(self.sg.check("git switch feature; git merge feature", main)[0])
        tracker = self.where["tracker"]
        git("branch", "-q", "trunk", "origin/main", cwd=tracker)
        self.assertTrue(self.sg.check("git switch trunk && git -c push.default=current push upstream", tracker)[0])
        self.assertFalse(self.sg.check("git switch trunk && git -c push.default=current push origin", tracker)[0])

    def hook(self, payload, env=None):
        environ = {k: v for k, v in os.environ.items() if k not in ("FREE_HANDS_ROLE", "CLAUDE_PROJECT_DIR")}
        result = subprocess.run([sys.executable, str(GUARD), "shell"], input=json.dumps(payload), capture_output=True,
                                text=True, cwd=self.tmp, env={**environ, **(env or {})})
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def write_goal(self, text):
        goal = Path(self.where["feature"]) / ".free-hands"
        goal.mkdir(exist_ok=True)
        (goal / "goal.md").write_text(text)
        self.addCleanup(shutil.rmtree, goal, True)

    def test_the_hook_denies_only_while_the_goal_is_guarded(self):
        payload = {"cwd": self.where["feature"], "tool_name": "Bash", "tool_input": {"command": "gh pr merge 1"}}
        self.assertIsNone(self.hook(payload))
        self.write_goal(goal_text(items=("- [x] all done",)))  # active with no open item: the limits still hold
        out = self.hook(payload)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("hard limit (merge)", out["permissionDecisionReason"])
        self.assertIn("- [-]", out["permissionDecisionReason"])
        self.write_goal(goal_text(max_iterations="1", iterations="1"))  # at the limit: still guarded
        self.assertIsNotNone(self.hook(payload))
        self.assertIsNone(self.hook({**payload, "tool_input": {"command": "git status"}}))
        self.assertIsNotNone(self.hook({**payload, "tool_input": {"command": ["gh", "pr", "merge", "1"]}}))
        self.assertIsNone(self.hook(payload, env={"FREE_HANDS_ROLE": "quick-thinker"}))
        for status in ("paused", "done"):
            self.write_goal(goal_text(status=status, items=("- [x] all done",)))
            self.assertIsNone(self.hook(payload), status)

    def test_the_hook_reads_the_declared_default_branch_and_ignores_bad_input(self):
        self.write_goal(goal_text().replace("status: active", "status: active\ndefault_branch: trunk"))
        push = {"cwd": self.where["feature"], "tool_input": {"command": "git push origin HEAD:trunk"}}
        reason = self.hook(push)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Default branch: trunk", reason)
        self.assertIsNone(self.hook({**push, "tool_input": {"command": "git push origin HEAD:main"}}))
        unparsable = self.hook({**push, "tool_input": {"command": "git commit -m it's"}})
        self.assertIn("could not be parsed", unparsable["hookSpecificOutput"]["permissionDecisionReason"])
        for bad in ({"cwd": self.where["feature"]}, {"cwd": self.where["feature"], "tool_input": {"command": 3}}):
            self.assertIsNone(self.hook(bad))

if __name__ == "__main__":
    unittest.main()
