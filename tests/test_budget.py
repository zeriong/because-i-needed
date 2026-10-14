"""budget: the user-level threshold and the Codex gate (rollout reading, deny, answer)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "budget" / "scripts"
QUESTION = "지정한 80%에 도달했습니다, 작업을 이어서 진행하시겠어요?"


def limits(used, resets=1800000000, minutes=10080):
    return {"limit_id": "codex", "primary": {"used_percent": used, "window_minutes": minutes, "resets_at": resets},
            "secondary": None}


class BudgetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.xdg = self.tmp / "xdg"
        self.sessions = self.tmp / "codex" / "sessions" / "2026" / "10" / "14"
        self.sessions.mkdir(parents=True)
        self.env = {**os.environ, "XDG_CONFIG_HOME": str(self.xdg)}

    def tearDown(self):
        subprocess.run(["rm", "-rf", str(self.tmp)])

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "budget.py"), *args], env=self.env, capture_output=True,
                              text=True)

    def rollout(self, name, *records):
        path = self.sessions / f"rollout-2026-10-14T00-00-00-{name}.jsonl"
        lines = [json.dumps({"timestamp": ts, "type": "event_msg", "payload": {"type": "token_count",
                                                                              "rate_limits": rl}})
                 for ts, rl in records]
        path.write_text("\n".join([json.dumps({"timestamp": "x", "type": "session_meta"})] + lines) + "\n")
        return path

    def gate(self, mode, payload):
        proc = subprocess.run([sys.executable, str(SCRIPTS / "gate.py"), mode], input=json.dumps(payload),
                              env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout) if proc.stdout.strip() else None

    def test_threshold_is_set_cleared_and_validated(self):
        self.assertEqual(json.loads(self.cli("status", "--json").stdout)["value"], "off")
        self.assertEqual(self.cli("set", "80").returncode, 0)
        state = json.loads(self.cli("status", "--json").stdout)
        self.assertEqual((state["value"], state["source"], state["global"], state["project"]), ("80%", "global", "80%", None))
        for bad in (["set", "0"], ["set", "101"], ["set", "x"], ["set"], ["nope"]):
            self.assertEqual(self.cli(*bad).returncode, 2, bad)
        (self.xdg / "because-i-needed" / "budget.json").write_text('{"percent": true}')
        self.assertEqual(json.loads(self.cli("status", "--json").stdout)["value"], "off")
        self.cli("set", "70")
        self.assertEqual(self.cli("off").returncode, 0)
        self.assertEqual(json.loads(self.cli("status", "--json").stdout)["value"], "off")

    def test_gate_denies_past_the_threshold_from_the_newest_rollout(self):
        self.cli("set", "80")
        own = self.rollout("own")  # a fresh session: no rate-limit record yet (budget-lab B01)
        self.rollout("other", ("2026-10-14T01:00:00Z", limits(50)), ("2026-10-14T02:00:00Z", limits(85)))
        out = self.gate("pretool", {"session_id": "s-1", "transcript_path": str(own)})
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(QUESTION, reason)
        pending = json.loads((self.xdg / "because-i-needed" / "budget" / "pending" / "s-1.json").read_text())
        self.assertIs(pending["open"], True)
        usage = json.loads((self.xdg / "because-i-needed" / "budget" / "usage.json").read_text())
        self.assertEqual((usage["kind"], usage["used"], usage["host"]), ("seven_day", 85, "codex"))
        self.assertEqual(json.loads(self.cli("status", "--json").stdout)["detail"], "7d now 85%")

    def test_answers_unlock_or_hold(self):
        self.cli("set", "80")
        own = self.rollout("own", ("2026-10-14T02:00:00Z", limits(90)))
        payload = {"session_id": "s-2", "transcript_path": str(own)}
        self.assertIsNotNone(self.gate("pretool", payload))
        hold = self.gate("prompt", {**payload, "prompt": "아니오"})
        self.assertIn("has not confirmed", hold["hookSpecificOutput"]["additionalContext"])
        self.assertIsNotNone(self.gate("pretool", payload))
        go = self.gate("prompt", {**payload, "prompt": " 예 "})
        self.assertIn("chose to continue", go["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.gate("pretool", payload))
        self.assertIsNone(self.gate("prompt", {**payload, "prompt": "다음 작업"}))  # nothing pending: no note
        self.rollout("own", ("2026-10-14T02:00:00Z", limits(91, resets=1800000001)))  # Codex's reset time jitters
        self.assertIsNone(self.gate("pretool", payload))
        self.rollout("own", ("2026-10-14T02:00:00Z", limits(91, resets=1900000000)))  # a new window asks again
        self.assertIsNotNone(self.gate("pretool", payload))

    def test_same_window_tolerates_seconds_and_reads_both_formats(self):
        sys.path.insert(0, str(SCRIPTS))
        import budget
        self.assertTrue(budget.same_window(1800000000, 1800000001))
        self.assertTrue(budget.same_window("2026-10-14T13:00:00.000Z", "2026-10-14T13:00:05Z"))
        self.assertFalse(budget.same_window(1800000000, 1800018000))  # five hours later: a new window
        for a, b in ((None, 1), ("x", "x"), (True, True)):
            self.assertFalse(budget.same_window(a, b))

    def test_gate_stays_out_of_the_way(self):
        own = self.rollout("own", ("2026-10-14T02:00:00Z", limits(90)))
        payload = {"session_id": "s-3", "transcript_path": str(own)}
        self.assertIsNone(self.gate("pretool", payload))  # no threshold set
        self.cli("set", "95")
        self.assertIsNone(self.gate("pretool", payload))  # under the threshold
        self.rollout("own", ("2026-10-14T02:00:00Z", limits(99, minutes=300)))
        self.assertIsNone(self.gate("pretool", payload))  # Codex's gate reads the 7-day window only
        for bad in ({"session_id": "a b", "transcript_path": str(own)}, {"transcript_path": str(own)}, {}):
            self.assertIsNone(self.gate("pretool", bad))
        proc = subprocess.run([sys.executable, str(SCRIPTS / "gate.py"), "pretool"], input="{broken", env=self.env,
                              capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
