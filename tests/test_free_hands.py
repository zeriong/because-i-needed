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
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "free-hands"
GUARD = PLUGIN / "scripts" / "guard.py"
PANEL = PLUGIN / "scripts" / "panel.py"
ROLES = ("quick-thinker", "deep-thinker", "evidence-hunter", "trend-tracker", "devils-advocate")


def goal_text(status="active", items=("- [ ] first", "- [x] second"), max_iterations="40", iterations="0", owner=None):
    lines = [f"status: {status}"]
    if max_iterations is not None:
        lines.append(f"max_iterations: {max_iterations}")
    if iterations is not None:
        lines.append(f"iterations: {iterations}")
    if owner is not None:
        lines.append(f"owner: {owner}")
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
        # never the real CLI: a test that wants the estimator passes CLAUDECODE and a fake CLI itself
        environ = {k: v for k, v in os.environ.items()
                   if k not in ("FREE_HANDS_ROLE", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_EXECPATH", "CLAUDECODE", "CLAUDE_PID")}
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
        environ = {k: v for k, v in os.environ.items()
                   if k not in ("FREE_HANDS_ROLE", "CLAUDE_CODE_EXECPATH", "CLAUDECODE", "CLAUDE_PID")}
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

    def test_another_session_is_left_alone(self):
        self.write(goal_text(owner="session-a"))
        b = {"session_id": "session-b"}
        for mode, extra in (("ask", {"tool_name": "AskUserQuestion"}), ("stop", {}), ("session", {"source": "startup"}),
                            ("prompt", {"prompt": "README 오타 하나만 고쳐줘"}),
                            ("shell", {"tool_input": {"command": "gh pr merge 1"}})):
            self.assertIsNone(self.hook(mode, {**b, **extra}), mode)
        self.assertEqual(self.goal.read_text(), goal_text(owner="session-a"))
        context = self.hook("prompt", {**b, "prompt": "free-hands 진행 상황 알려줘"})["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[free-hands: entry]", context)
        self.assertIn("This session's id is session-b: write `owner: session-b`", context)
        self.assertIn("Session session-a owns the free-hands run", context)
        a = {"session_id": "session-a"}
        self.assertEqual(self.hook("ask", a)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.hook("shell", {**a, "tool_input": {"command": "gh pr merge 1"}})
                         ["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("keep `owner: session-a`", self.hook("session", a)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook("stop", a)["decision"], "block")
        self.assertIn("iterations: 1", self.goal.read_text())

    def test_an_unowned_goal_becomes_the_first_sessions(self):
        self.write(goal_text())
        self.assertEqual(self.hook("stop", {"session_id": "session-a"})["decision"], "block")
        text = self.goal.read_text()
        self.assertIn("iterations: 1\nowner: session-a\n", text)
        self.assertIsNone(self.hook("stop", {"session_id": "session-b"}))
        self.assertIsNone(self.hook("session", {"session_id": "session-b"}))
        self.assertEqual(self.goal.read_text(), text)

    def test_concurrent_first_sessions_leave_one_owner(self):
        self.write(goal_text())
        threads = [threading.Thread(target=self.hook, args=("stop", {"session_id": sid})) for sid in ("s-1", "s-2")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        text = self.goal.read_text()
        self.assertEqual(text.count("owner:"), 1)
        self.assertIn("iterations: 1", text)

    def test_the_run_moves_when_the_owner_line_changes(self):
        self.write(goal_text(owner="session-a"))
        self.write(goal_text(owner="session-b"))  # what the skill writes when session B starts or resumes the run
        self.assertIsNone(self.hook("stop", {"session_id": "session-a"}))
        self.assertEqual(self.hook("stop", {"session_id": "session-b"})["decision"], "block")
        self.assertIn("iterations: 1", self.goal.read_text())

    def test_the_command_prompt_gives_the_session_id(self):
        out = self.hook("prompt", {"session_id": "session-a", "prompt": "/free-hands:run finish the migration"})
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("This session's id is session-a: write `owner: session-a`", context)
        self.assertNotIn("owns the free-hands run", context)
        self.write(goal_text(owner="session-a"))
        out = self.hook("prompt", {"session_id": "session-b", "prompt": "$free-hands:run"})
        self.assertIn("Session session-a owns the free-hands run", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.goal.read_text(), goal_text(owner="session-a"))

    def test_without_a_valid_session_id_the_guard_is_repository_wide(self):
        self.write(goal_text(owner="session-a"))
        for payload in ({}, {"session_id": "two words"}, {"session_id": "x\nowner: y"}, {"session_id": 7}):
            self.assertEqual(self.hook("ask", payload)["hookSpecificOutput"]["permissionDecision"], "deny", payload)
        self.write(goal_text())
        self.hook("ask", {"session_id": "x\nowner: y"})
        self.assertEqual(self.goal.read_text(), goal_text())

    def test_an_open_budget_question_lets_asking_and_stopping_through(self):
        self.write(goal_text(owner="session-a"))
        xdg = self.tmp / "xdg"
        pending = xdg / "because-i-needed" / "budget" / "pending" / "session-a.json"
        a, env = {"session_id": "session-a"}, {"XDG_CONFIG_HOME": str(xdg)}
        self.assertEqual(self.hook("ask", a, env=env)["hookSpecificOutput"]["permissionDecision"], "deny")
        pending.parent.mkdir(parents=True)
        pending.write_text('{"open": true, "threshold": 80}')
        self.assertIsNone(self.hook("ask", a, env=env))
        self.assertIsNone(self.hook("stop", a, env=env))
        self.assertIn("iterations: 0", self.goal.read_text())
        self.assertEqual(self.hook("shell", {**a, "tool_input": {"command": "gh pr merge 1"}}, env=env)
                         ["hookSpecificOutput"]["permissionDecision"], "deny")  # the hard limits stay
        for closed in ('{"open": false}', "not json", "[]"):
            pending.write_text(closed)
            self.assertEqual(self.hook("ask", a, env=env)["hookSpecificOutput"]["permissionDecision"], "deny", closed)
        pending.write_text('{"open": true}')
        self.assertEqual(self.hook("ask", {}, env=env)["hookSpecificOutput"]["permissionDecision"], "deny")  # no id

    def test_status_prints_the_dashboard_contract(self):
        def status():
            result = subprocess.run([sys.executable, str(GUARD), "status"], cwd=self.repo / "sub", capture_output=True,
                                    text=True)
            return json.loads(result.stdout)
        self.assertEqual(status(), {"value": "off", "source": "default", "project": None, "global": None,
                                    "detail": None, "watch": [str(self.goal.resolve()),
                                                              str(self.goal.resolve().parent / "estimates.jsonl")]})
        self.write(goal_text(owner="0123456789abcdef", iterations="3"))
        self.assertEqual(status()["value"], "active 3/40 · 1 open")
        self.assertEqual((status()["source"], status()["detail"]), ("project", "owner 01234567"))
        self.write(goal_text(status="paused"))
        self.assertEqual(status()["value"], "paused 0/40 · 1 open")
        self.write(goal_text(status="done", items=("- [x] a",)))
        self.assertEqual(status()["value"], "done")

    def test_root_comes_from_the_hook_cwd(self):
        self.write(goal_text())
        out = self.hook("ask", {"cwd": str(self.repo / "sub")})
        self.assertIn(str(self.goal), out["hookSpecificOutput"]["permissionDecisionReason"])
        plain = self.tmp / "plain"
        (plain / ".free-hands").mkdir(parents=True)
        (plain / ".free-hands" / "goal.md").write_text(goal_text())
        self.assertIsNotNone(self.hook("ask", {"cwd": str(plain)}))


def load_eta():
    import importlib.util
    spec = importlib.util.spec_from_file_location("free_hands_eta", PLUGIN / "scripts" / "eta.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EtaTest(unittest.TestCase):
    tearDown, write, hook = GuardTest.tearDown, GuardTest.write, GuardTest.hook

    def setUp(self):
        GuardTest.setUp(self)
        self.eta = load_eta()
        self.eta.BASELINE = self.tmp / "no-baseline.json"  # estimates as written unless a test sets factors
        self.folder = self.goal.parent

    def rows(self):
        path = self.folder / "timings.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def step(self, items, now, event="post", ended=False, **data):
        self.write(goal_text(items=items, owner="s1"))
        self.eta.observe(self.folder, self.goal.read_text(), event, data, now=now, ended=ended)

    def test_items_carry_an_estimate_and_a_category(self):
        text = goal_text(items=("- [ ] fix the pager (~6m fix)", "- [x] write docs (~2.5min, docs)",
                                "- [-] deploy it (~3m ops) — needs the user: deploys are off", "- [ ] no estimate",
                                "- [ ] odd (~0m fix)", "- [ ] other (~4m chores)", "```", "- [ ] quoted (~1m fix)",
                                "```"))
        self.assertEqual(self.eta.checklist(text), [
            (" ", "fix the pager", 6.0, "fix"), ("x", "write docs", 2.5, "docs"), ("-", "deploy it", 3.0, "ops"),
            (" ", "no estimate", None, None), (" ", "odd", None, None), (" ", "other", 4.0, None)])

    def test_a_finished_item_records_the_active_time_since_the_previous_one(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~8m docs)", "- [ ] c (~2m docs)"), 1000)
        self.step(("- [x] a (~4m fix)", "- [ ] b (~8m docs)", "- [ ] c (~2m docs)"), 1300, effort={"level": "xhigh"})
        self.step(("- [x] a (~4m fix)", "- [x] b (~8m docs)", "- [-] c (~2m docs) — needs the user: x"), 1900)
        rows = self.rows()
        self.assertEqual([(r["item"], r["actual_min"], r["batch"], r["outcome"]) for r in rows],
                         [("a", 5.0, 1, "done"), ("b", 8.0, 2, "done"), ("c", 2.0, 2, "skipped")])
        self.assertEqual((rows[0]["est_min"], rows[0]["cat"], rows[0]["effort"]), (4.0, "fix", "xhigh"))

    def test_gaps_after_an_ended_turn_or_without_a_long_tool_call_are_not_work(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), 0)
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), 60, event="stop", ended=True)
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), 9000, event="prompt")
        self.step(("- [x] a (~4m fix)", "- [ ] b (~4m fix)"), 9120)
        self.step(("- [x] a (~4m fix)", "- [ ] b (~4m fix)"), 9120 + 7200)  # two quiet hours, no tool ran
        self.step(("- [x] a (~4m fix)", "- [x] b (~4m fix)"), 9120 + 7200 + 1800 + 60, duration_ms=1800 * 1000)
        self.assertEqual([r["actual_min"] for r in self.rows()], [3.0, 30.0])

    def test_a_new_session_does_not_count_the_time_in_between(self):
        self.step(("- [ ] a (~4m fix)",), 0)
        self.step(("- [ ] a (~4m fix)",), 600, event="session", source="resume")
        self.step(("- [x] a (~4m fix)",), 660)
        self.assertEqual([r["actual_min"] for r in self.rows()], [1.0])

    def test_a_new_goal_starts_a_new_clock_and_keeps_the_record(self):
        self.step(("- [ ] a (~4m fix)",), 0)
        self.step(("- [x] a (~4m fix)",), 120)
        other = goal_text(items=("- [ ] z (~1m docs)",), owner="s1").replace("ship it", "next goal")
        self.goal.write_text(other)
        self.eta.observe(self.folder, other, "post", {}, now=500)
        self.goal.write_text(other.replace("- [ ] z", "- [x] z"))
        self.eta.observe(self.folder, self.goal.read_text(), "post", {}, now=560)
        self.assertEqual([(r["item"], r["actual_min"]) for r in self.rows()], [("a", 2.0), ("z", 1.0)])

    def test_the_model_comes_from_the_transcript_tail(self):
        transcript = self.tmp / "t.jsonl"
        transcript.write_text("\n".join(json.dumps(e) for e in (
            {"type": "assistant", "message": {"model": "claude-opus-9-9"}}, {"type": "user", "message": {}},
            {"type": "assistant", "message": {"model": "claude-sonnet-9-9"}}, {"type": "system"})) + "\n")
        self.assertEqual(self.eta.model_from_transcript(str(transcript)), "claude-sonnet-9-9")
        self.assertIsNone(self.eta.model_from_transcript(str(self.tmp / "missing")))
        self.step(("- [ ] a (~4m fix)",), 0, transcript_path=str(transcript))
        self.step(("- [x] a (~4m fix)",), 60, transcript_path=str(transcript))
        self.assertEqual((self.rows()[0]["model"], self.rows()[0]["family"]), ("claude-sonnet-9-9", "sonnet"))

    def test_the_prediction_uses_the_baseline_and_the_projects_record(self):
        base = self.tmp / "baseline.json"
        base.write_text(json.dumps({"families": {"sonnet": {"all": 2.0, "fix": 3.0}}}))
        self.eta.BASELINE = base
        transcript = self.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-9"}}) + "\n")
        items = ("- [ ] a (~4m fix)", "- [ ] b (~5m docs)", "- [ ] c")
        self.step(items, 0, transcript_path=str(transcript))
        expected = self.eta.predict(self.folder, self.goal.read_text(), now=0)
        self.assertEqual((expected["minutes"], expected["unestimated"], expected["family"]), (22.0, 1, "sonnet"))
        later = self.eta.predict(self.folder, self.goal.read_text(), now=600)  # 10 of a's 12 minutes used
        self.assertAlmostEqual(later["minutes"], 12.0)
        with open(self.folder / "timings.jsonl", "a") as record:
            for _ in range(3):
                record.write(json.dumps({"outcome": "done", "est_min": 5, "actual_min": 40, "family": "sonnet",
                                         "cat": "docs"}) + "\n")
        slow = self.eta.predict(self.folder, self.goal.read_text(), now=0)
        self.assertAlmostEqual(slow["project"], 2.0)  # 4x slower than the baseline, shrunk: exp(3 ln 4 / 6)
        self.assertAlmostEqual(slow["minutes"], 44.0)

    def test_a_completion_the_clock_has_not_recorded_restarts_the_next_item(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~6m fix)"), 0)
        self.write(goal_text(items=("- [x] a (~4m fix)", "- [ ] b (~6m fix)"), owner="s1"))  # no hook ran yet
        self.assertAlmostEqual(self.eta.predict(self.folder, self.goal.read_text(), now=600)["minutes"], 6.0)
        self.eta.observe(self.folder, self.goal.read_text(), "post", {}, now=600)
        # a took 10 minutes for 4 estimated: the project factor is 2.5 ** (1 / (1 + 3)); b has used 1 minute
        self.assertAlmostEqual(self.eta.predict(self.folder, self.goal.read_text(), now=660)["minutes"],
                               6 * 2.5 ** 0.25 - 1)

    def test_a_family_without_a_factor_takes_the_default(self):
        base = {"self": {"sonnet": {"all": 0.1, "fix": 0.2}, "default": {"all": 0.5}}, "haiku": {"sonnet": {"all": 2.0}}}
        self.assertEqual([self.eta.factor(base, fam, cat) for fam, cat in
                          (("sonnet", "fix"), ("sonnet", "docs"), ("haiku", "fix"), (None, None))], [0.2, 0.1, 0.5, 0.5])
        self.assertEqual(self.eta.factor(base, "sonnet", "fix", "haiku"), 2.0)
        self.assertEqual(self.eta.factor(base, "opus", "fix", "haiku"), 1.0)
        self.assertEqual(self.eta.factor({}, "sonnet", "fix"), 1.0)
        shipped = json.loads((PLUGIN / "scripts" / "eta-baseline.json").read_text())["estimators"]
        self.assertTrue({"sonnet", "opus", "fable", "default"} <= set(shipped["self"]))
        self.assertTrue(all(0 < cell["all"] < 5 for cells in shipped.values() for cell in cells.values()))

    def test_an_item_added_already_finished_mid_run_joins_that_edits_batch(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~4m docs)"), 0)
        self.step(("- [x] a (~4m fix)", "- [x] extra (~4m fix)", "- [ ] b (~4m docs)"), 480)
        self.assertEqual([(r["item"], r["actual_min"], r["batch"]) for r in self.rows()],
                         [("a", 4.0, 2), ("extra", 4.0, 2)])
        self.step(("- [x] a (~4m fix)", "- [x] extra (~4m fix)", "- [ ] b renamed (~4m docs)"), 500)
        self.step(("- [x] a (~4m fix)", "- [x] extra (~4m fix)", "- [x] b renamed (~4m docs)"), 560)
        self.assertEqual(self.rows()[-1]["item"], "b renamed")
        self.assertFalse(self.eta.pending(self.folder, self.goal.read_text()))  # the old key "b" no longer counts

    def test_repeated_texts_keep_their_own_keys(self):
        self.step(("- [ ] run tests (~2m test)", "- [ ] run tests (~2m test)"), 0)
        self.step(("- [x] run tests (~2m test)", "- [ ] run tests (~2m test)"), 60)
        for now in (70, 80, 90):
            self.step(("- [x] run tests (~2m test)", "- [ ] run tests (~2m test)"), now)
        self.assertEqual([(r["item"], r["actual_min"]) for r in self.rows()], [("run tests", 1.0)])
        self.assertEqual([k for _, k, _, _ in self.eta.checklist(self.goal.read_text())], ["run tests", "run tests #2"])

    def test_the_time_before_a_prompt_is_the_users(self):
        self.step(("- [ ] a (~4m fix)",), 0)
        self.step(("- [ ] a (~4m fix)",), 900, event="prompt")  # a turn interrupted with Esc sends no Stop
        self.step(("- [x] a (~4m fix)",), 960)
        self.assertEqual([r["actual_min"] for r in self.rows()], [1.0])

    def test_rewording_the_goal_keeps_the_clock(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), 0)
        reworded = goal_text(items=("- [x] a (~4m fix)", "- [ ] b (~4m fix)"), owner="s1").replace("ship it", "ship it now")
        self.goal.write_text(reworded)
        self.eta.observe(self.folder, reworded, "post", {}, now=120)
        self.assertEqual([(r["item"], r["actual_min"]) for r in self.rows()], [("a", 2.0)])

    def test_the_goal_file_is_read_again_under_the_lock(self):
        self.step(("- [ ] a (~4m fix)",), 0)
        self.write(goal_text(items=("- [x] a (~4m fix)",), owner="s1"))
        self.eta.observe(self.folder, goal_text(items=("- [ ] a (~4m fix)",), owner="s1"), "post", {}, now=60)
        self.eta.observe(self.folder, goal_text(items=("- [ ] a (~4m fix)",), owner="s1"), "post", {}, now=30)
        self.assertEqual([r["actual_min"] for r in self.rows()], [1.0])  # a stale text and a late clock change nothing
        self.assertEqual(json.loads((self.folder / "eta.json").read_text())["last"], 60)

    def test_a_prompt_of_task_notifications_is_the_runs_time(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)",), owner="s1"))
        self.hook("post", {"session_id": "s1"})
        state = json.loads((self.folder / "eta.json").read_text())
        state.update(last=time.time() - 600, active=0.0)
        (self.folder / "eta.json").write_text(json.dumps(state))
        notice = "<task-notification><task-id>x</task-id><status>completed</status></task-notification>"
        self.hook("prompt", {"session_id": "s1", "prompt": notice})
        self.assertGreater(json.loads((self.folder / "eta.json").read_text())["active"], 590)
        state.update(last=time.time() - 600, active=0.0)
        (self.folder / "eta.json").write_text(json.dumps(state))
        self.hook("prompt", {"session_id": "s1", "prompt": "also add a test"})
        self.assertEqual(json.loads((self.folder / "eta.json").read_text())["active"], 0.0)

    def test_a_next_goal_sharing_one_item_starts_its_own_clock(self):
        self.step(("- [ ] a (~4m fix)", "- [ ] run tests (~2m test)"), 0)
        self.step(("- [x] a (~4m fix)", "- [x] run tests (~2m test)"), 300)
        nxt = goal_text(items=("- [ ] b (~4m fix)", "- [ ] c (~4m docs)", "- [ ] run tests (~2m test)"),
                        owner="s1").replace("ship it", "next goal")
        self.goal.write_text(nxt)
        self.eta.observe(self.folder, nxt, "post", {}, now=900)
        self.goal.write_text(nxt.replace("- [ ] b", "- [x] b"))
        self.eta.observe(self.folder, self.goal.read_text(), "post", {}, now=960)
        self.assertEqual(self.rows()[-1]["item"], "b")
        self.assertEqual(self.rows()[-1]["actual_min"], 1.0)  # not the 10 minutes since the last goal's end

    def test_odd_values_never_stop_the_clock(self):
        self.step(("- [ ] a (~4m Fix)",), 0, transcript_path=1)
        self.assertEqual(self.eta.checklist(self.goal.read_text())[0][2:], (4.0, "fix"))
        (self.folder / "eta.json").write_text(json.dumps({"goal": self.eta.goal_id(self.goal.read_text()),
                                                         "items": {"a": {"mark": " ", "est": 4, "cat": "fix"}},
                                                         "active": "x", "mark": None, "last": "y", "model": 7}))
        transcript = self.tmp / "t.jsonl"
        transcript.write_text('{"type": "assistant", "message": null}\n')
        self.step(("- [x] a (~4m Fix)",), 60, transcript_path=str(transcript))
        self.assertEqual(len(self.rows()), 1)
        with open(self.folder / "timings.jsonl", "a") as record:
            record.write('{"outcome": "done", "est_min": 2, "actual_min": 1, "family": ["sonnet"], "cat": {}}\n')
        self.write(goal_text(items=("- [x] a (~4m Fix)", "- [ ] b (~4m fix)"), owner="s1"))
        self.assertIsNotNone(self.eta.predict(self.folder, self.goal.read_text(), now=90))

    def test_a_paused_goal_is_not_timed(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), owner="s1"))
        self.hook("post", {"session_id": "s1"})
        before = json.loads((self.folder / "eta.json").read_text())["last"]
        self.write(goal_text(status="paused", items=("- [ ] a (~4m fix)", "- [ ] b (~4m fix)"), owner="s1"))
        self.hook("post", {"session_id": "s1"})
        self.assertEqual(json.loads((self.folder / "eta.json").read_text())["last"], before)

    def estimate_rows(self, *rows):
        run = self.eta.run_of(json.loads((self.folder / "eta.json").read_text()))
        with open(self.folder / "estimates.jsonl", "a") as out:
            for item, minutes in rows:
                out.write(json.dumps({"run": run, "item": item, "minutes": minutes, "cat": "fix",
                                      "estimator": "haiku"}) + "\n")

    def test_the_isolated_estimators_answers_drive_the_prediction(self):
        base = self.tmp / "baseline.json"
        base.write_text(json.dumps({"estimators": {"haiku": {"default": {"all": 0.5}}}}))
        self.eta.BASELINE = base
        self.step(("- [ ] a", "- [ ] b", "- [ ] c"), 0)
        self.assertEqual(self.eta.unestimated(self.folder, self.goal.read_text())[1], ["a", "b", "c"])
        self.assertIsNone(self.eta.predict(self.folder, self.goal.read_text(), now=0))
        self.estimate_rows(("a", 8), ("b", 4), ("c", None))  # c was asked and got no answer
        self.assertEqual(self.eta.unestimated(self.folder, self.goal.read_text())[1], [])
        expected = self.eta.predict(self.folder, self.goal.read_text(), now=0)
        self.assertEqual((expected["minutes"], expected["unestimated"]), (6.0, 1))
        self.step(("- [x] a", "- [ ] b", "- [ ] c"), 300)
        self.assertEqual([(r["est_min"], r["estimator"]) for r in self.rows()], [(8, "haiku")])

    def test_an_estimate_that_lands_after_the_item_still_counts(self):
        self.step(("- [ ] a", "- [ ] b"), 0)
        self.step(("- [x] a", "- [ ] b"), 120)
        self.assertIsNone(self.rows()[0]["est_min"])
        self.estimate_rows(("a", 4))
        self.assertEqual([(r["est_min"], r["actual_min"], r["estimator"]) for r in self.eta.records(self.folder)],
                         [(4, 2.0, "haiku")])

    def fake_claude(self, reply, code=0):
        fake = self.tmp / "fake-claude"
        fake.write_text("#!/usr/bin/env python3\nimport json, os, sys\n"
                        "open(os.environ['FAKE_ARGV'], 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                        f"print({json.dumps(json.dumps(reply))})\nsys.exit({code})\n")
        fake.chmod(0o755)
        # the hook runs as this test's child, as a hook runs as Claude Code's (CLAUDE_PID = its parent; r3 I06)
        return {"CLAUDECODE": "1", "CLAUDE_PID": str(os.getpid()), "CLAUDE_CODE_EXECPATH": str(fake),
                "FAKE_ARGV": str(self.tmp / "argv.jsonl")}

    def wait_for(self, path, seconds=8):
        end = time.time() + seconds
        while time.time() < end and not path.exists():
            time.sleep(0.1)
        time.sleep(0.3)
        return path.exists()

    def test_the_hook_starts_the_isolated_estimator(self):
        self.write(goal_text(items=("- [ ] fix the pager", "- [x] done before"), owner="s1"))
        answer = {"items": [{"n": 1, "minutes": 7, "category": "Fix"}]}
        env = self.fake_claude({"result": json.dumps(answer), "modelUsage": {"claude-haiku-9": {}},
                                "total_cost_usd": 0.001})
        self.assertIsNone(self.hook("post", {"session_id": "s1"}, env=env))  # nothing reaches the session
        self.assertTrue(self.wait_for(self.folder / "estimates.jsonl"))
        row = json.loads((self.folder / "estimates.jsonl").read_text().splitlines()[0])
        self.assertEqual((row["item"], row["minutes"], row["cat"], row["model"]), ("fix the pager", 7, "fix",
                                                                                  "claude-haiku-9"))
        argv = json.loads((self.tmp / "argv.jsonl").read_text().splitlines()[0])
        for flag in ("--safe-mode", "--no-session-persistence", "--tools"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--model") + 1], "haiku")
        self.assertIn("1. fix the pager", argv[1])
        self.assertNotIn("done before", argv[1])

    def test_a_failing_estimator_is_not_asked_again_and_can_be_turned_off(self):
        self.write(goal_text(items=("- [ ] a",), owner="s1"))
        env = self.fake_claude({"error": "auth"}, code=1)
        self.hook("post", {"session_id": "s1"}, env={**env, "FREE_HANDS_ESTIMATOR": "off"})
        time.sleep(1)
        self.assertFalse((self.tmp / "argv.jsonl").exists())
        self.hook("post", {"session_id": "s1"}, env=env)
        self.assertTrue(self.wait_for(self.folder / "estimator.log"))
        self.assertIsNone(json.loads((self.folder / "estimates.jsonl").read_text())["minutes"])  # asked, no answer
        self.write(goal_text(items=("- [ ] a", "- [ ] b"), owner="s1"))
        self.hook("post", {"session_id": "s1"}, env=env)  # b is new, but the last start is under a minute old
        time.sleep(1)
        self.assertEqual(len((self.tmp / "argv.jsonl").read_text().splitlines()), 1)
        self.hook("post", {"session_id": "s2"}, env=env)  # another session never starts one
        self.hook("post", {"session_id": "s1"}, env={k: v for k, v in env.items() if k != "CLAUDECODE"})  # not Claude Code
        self.hook("post", {"session_id": "s1"}, env={**env, "CLAUDE_PID": "1"})  # inherited: its parent is not that pid
        time.sleep(1)
        self.assertEqual(len((self.tmp / "argv.jsonl").read_text().splitlines()), 1)

    def test_without_a_path_from_the_host_the_cli_comes_from_path(self):
        self.write(goal_text(items=("- [ ] a",), owner="s1"))
        env = self.fake_claude({"result": json.dumps({"items": [{"n": 1, "minutes": 3, "category": "docs"}]})})
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        shutil.copy2(env.pop("CLAUDE_CODE_EXECPATH"), bin_dir / "claude")  # as from a user's terminal (r3 I06, I07)
        self.hook("post", {"session_id": "s1"}, env={**env, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"})
        self.assertTrue(self.wait_for(self.folder / "estimates.jsonl"))
        self.assertEqual(json.loads((self.folder / "estimates.jsonl").read_text())["minutes"], 3)

    def test_an_item_reworded_while_it_is_checked_keeps_its_estimate(self):
        self.step(("- [ ] a: fix the pager", "- [ ] b: add docs"), 0)
        self.estimate_rows(("a: fix the pager", 4), ("b: add docs", 2))
        self.assertEqual(self.eta.unestimated(self.folder, self.goal.read_text())[1], [])
        self.write(goal_text(status="done", items=("- [x] a: pager fixed, 12 tests pass", "- [x] b: docs added"),
                             owner="s1"))
        self.assertTrue(self.eta.pending(self.folder, self.goal.read_text()))  # the last edit is still timed
        self.eta.observe(self.folder, self.goal.read_text(), "post", {}, now=360)
        self.assertEqual([(r["item"], r["was"], r["est_min"], r["actual_min"]) for r in self.rows()],
                         [("a: pager fixed, 12 tests pass", "a: fix the pager", 4, 4.0),
                          ("b: docs added", "b: add docs", 2, 2.0)])
        self.assertFalse(self.eta.pending(self.folder, self.goal.read_text()))

    def test_a_reworded_open_item_is_not_estimated_again(self):
        self.step(("- [ ] a: fix the pager", "- [ ] b: add docs"), 0)
        self.estimate_rows(("a: fix the pager", 4), ("b: add docs", 2))
        self.step(("- [ ] a: fix the pager in render.py", "- [ ] b: add docs"), 60)
        self.assertEqual(self.eta.unestimated(self.folder, self.goal.read_text())[1], [])
        self.assertAlmostEqual(self.eta.predict(self.folder, self.goal.read_text(), now=60)["minutes"], 5.0)
        self.step(("- [ ] b: add docs",), 120)  # a removed: gone, not done, and the clock does not wait for it
        self.assertEqual(self.rows(), [])
        self.assertTrue(self.eta.pending(self.folder, self.goal.read_text()))
        self.step(("- [x] b: add docs",), 180)
        self.assertFalse(self.eta.pending(self.folder, self.goal.read_text()))

    def test_no_estimate_means_no_prediction(self):
        self.write(goal_text(items=("- [ ] a", "- [x] b (~3m fix)")))
        self.assertIsNone(self.eta.predict(self.folder, self.goal.read_text()))

    def test_the_post_hook_records_only_the_owner_and_the_edit_that_ends_the_run(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)",), owner="s1"))
        self.hook("post", {"session_id": "s2"})
        self.assertFalse((self.folder / "eta.json").exists())
        self.hook("post", {"session_id": "s1"})
        self.assertTrue((self.folder / "eta.json").exists())
        self.write(goal_text(status="done", items=("- [x] a (~4m fix)",), owner="s1"))
        self.hook("post", {"session_id": "s1"})
        self.assertEqual([r["item"] for r in self.rows()], ["a"])
        self.hook("post", {"session_id": "s1"})
        self.assertEqual(len(self.rows()), 1)
        self.assertIsNone(self.hook("post", {"session_id": "s1"}, env={"FREE_HANDS_ROLE": "quick-thinker"}))

    def test_the_stop_hook_still_blocks_and_ends_the_clock_when_it_lets_go(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)",), owner="s1"))
        self.assertEqual(self.hook("stop", {"session_id": "s1"})["decision"], "block")
        self.assertFalse(json.loads((self.folder / "eta.json").read_text())["idle"])
        self.write(goal_text(items=("- [x] a (~4m fix)",), owner="s1", status="done"))
        self.assertIsNone(self.hook("stop", {"session_id": "s1"}))  # the last item's run ends: recorded, then idle
        self.assertTrue(json.loads((self.folder / "eta.json").read_text())["idle"])
        self.assertEqual([r["item"] for r in self.rows()], ["a"])

    def test_status_shows_the_expected_finish_while_active(self):
        def status():
            result = subprocess.run([sys.executable, str(GUARD), "status"], cwd=self.repo / "sub", capture_output=True,
                                    text=True)
            return json.loads(result.stdout)
        self.write(goal_text(items=("- [ ] a (~4m fix)", "- [ ] b"), owner="0123456789abcdef"))
        out = status()
        self.assertRegex(out["value"], r"^active 0/40 · 2 open · ETA \d\d:\d\d\+$")
        self.assertRegex(out["detail"], r"^~\d+m left · owner 01234567$")
        self.write(goal_text(status="paused", items=("- [ ] a (~4m fix)",)))
        self.assertEqual(status()["value"], "paused 0/40 · 1 open")

    def test_non_finite_or_huge_records_never_break_the_status(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)",), owner="s1"))
        (self.folder / "timings.jsonl").write_text(
            '{"outcome": "done", "est_min": 1, "actual_min": Infinity, "family": "sonnet"}\n'
            '{"outcome": "done", "est_min": NaN, "actual_min": 3}\n'
            '{"outcome": "done", "est_min": 1e308, "actual_min": 1e308}\n'
            '{"outcome": "done", "est_min": true, "actual_min": 2}\n')
        self.assertEqual(self.eta.records(self.folder), [])
        result = subprocess.run([sys.executable, str(GUARD), "status"], cwd=self.repo / "sub", capture_output=True,
                                text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(json.loads(result.stdout)["value"], r"^active 0/40 · 1 open · ETA \d\d:\d\d$")

    def test_a_broken_record_or_state_is_ignored(self):
        self.write(goal_text(items=("- [ ] a (~4m fix)",), owner="s1"))
        (self.folder / "eta.json").write_text("{not json")
        (self.folder / "timings.jsonl").write_text("[1]\nnot json\n")
        self.assertAlmostEqual(self.eta.predict(self.folder, self.goal.read_text(), now=0)["minutes"], 4.0)
        self.hook("post", {"session_id": "s1"})
        self.assertEqual(json.loads((self.folder / "eta.json").read_text())["items"]["a"]["est"], 4.0)


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
        # never the real CLI: a test that wants the estimator passes CLAUDECODE and a fake CLI itself
        environ = {k: v for k, v in os.environ.items()
                   if k not in ("FREE_HANDS_ROLE", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_EXECPATH", "CLAUDECODE", "CLAUDE_PID")}
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
