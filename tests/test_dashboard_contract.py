"""Root Rule 11: every mode is declared to the dashboard, and every declared status command keeps the contract."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"env", "project", "global", "default"}


class DashboardContractTest(unittest.TestCase):
    def test_every_mode_skill_is_declared(self):
        for plugin in sorted((ROOT / "plugins").iterdir()):
            if (plugin / "skills" / "mode").is_dir():
                self.assertTrue((plugin / "dashboard.json").is_file(), f"{plugin.name} has a mode skill but no dashboard.json")

    def test_every_declared_status_command_prints_the_contract(self):
        declared = sorted((ROOT / "plugins").glob("*/dashboard.json"))
        self.assertTrue(declared)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            env = {k: v for k, v in os.environ.items() if not k.startswith("CXC_") and k != "FREE_HANDS_ROLE"}
            env.update(XDG_CONFIG_HOME=str(Path(tmp) / "xdg"), HOME=str(Path(tmp) / "home"),
                       CLAUDE_CONFIG_DIR=str(Path(tmp) / "claude"))
            for path in declared:
                root = path.parent
                for entry in json.loads(path.read_text())["entries"]:
                    with self.subTest(plugin=root.name, label=entry["label"]):
                        self.assertIsInstance(entry["label"], str)
                        self.assertTrue(isinstance(entry.get("icon"), str) and 0 < len(entry["icon"]) <= 4)
                        argv = [str(root / a) if i and (root / a).exists() else a for i, a in enumerate(entry["status"])]
                        start = time.monotonic()
                        proc = subprocess.run(argv, cwd=repo, env=env, capture_output=True, text=True, timeout=5)
                        self.assertLess(time.monotonic() - start, 1.0)
                        self.assertEqual(proc.returncode, 0, proc.stderr)
                        state = json.loads(proc.stdout)
                        self.assertIsInstance(state["value"], str)
                        self.assertIn(state["source"], SOURCES)
                        for level in ("project", "global"):
                            self.assertTrue(state[level] is None or isinstance(state[level], str), level)
                        self.assertTrue(state.get("detail") is None or isinstance(state["detail"], str))


if __name__ == "__main__":
    unittest.main()
