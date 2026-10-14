"""dashboard: finding enabled because-i-needed plugins on each host and showing what they declare."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "dashboard" / "scripts" / "dashboard.py"


def fake_plugin(root, name, entries):
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": name, "version": "1.0.0"}))
    (root / "dashboard.json").write_text(json.dumps({"entries": entries}))
    return root


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self.status = self.tmp / "status.py"
        self.status.write_text("import json,sys\nprint(json.dumps({'value': sys.argv[1], 'source': 'global', "
                               "'project': None, 'global': sys.argv[1]}))\n")
        self.env = {k: v for k, v in os.environ.items() if k != "BECAUSE_I_NEEDED_PLUGIN_DIRS"}
        self.env.update(CLAUDE_CONFIG_DIR=str(self.tmp / "claude"), CODEX_HOME=str(self.tmp / "codex"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_dashboard(self, *args, env=None):
        proc = subprocess.run([sys.executable, str(SCRIPT), *args, "--cwd", str(self.repo), "--json"],
                              env={**self.env, **(env or {})}, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def entry(self, value):
        return {"label": "alpha", "status": [sys.executable, str(self.status), value]}

    def test_claude_reads_installed_and_enabled_plugins(self):
        cache = self.tmp / "claude" / "plugins" / "cache"
        alpha = fake_plugin(cache / "alpha", "alpha", [self.entry("on")])
        other = fake_plugin(cache / "other", "other", [self.entry("x")])
        off = fake_plugin(cache / "off", "off", [self.entry("y")])
        (self.tmp / "claude" / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
            "alpha@because-i-needed": [{"scope": "user", "installPath": str(alpha)}],
            "other@another-market": [{"scope": "user", "installPath": str(other)}],
            "off@because-i-needed": [{"scope": "user", "installPath": str(off)}]}}))
        out = self.run_dashboard("--host", "claude", "--enabled", "alpha@because-i-needed,other@another-market")
        self.assertEqual([(e["plugin"], e["value"]) for e in out["entries"]], [("alpha", "on")])
        self.assertEqual(out["line"], "because-i-needed │ alpha on")
        (self.tmp / "claude" / "settings.json").write_text(json.dumps({"enabledPlugins": {"off@because-i-needed": True}}))
        self.assertEqual([e["plugin"] for e in self.run_dashboard("--host", "claude")["entries"]], ["off"])

    def test_codex_reads_config_and_the_newest_cached_version(self):
        cache = self.tmp / "codex" / "plugins" / "cache" / "because-i-needed" / "alpha"
        fake_plugin(cache / "0.9.0", "alpha", [self.entry("old")])
        fake_plugin(cache / "0.10.0", "alpha", [self.entry("new")])
        (self.tmp / "codex" / "config.toml").write_text(
            '[plugins."alpha@because-i-needed"]\nenabled = true\n\n[plugins."beta@because-i-needed"]\nenabled = false\n')
        out = self.run_dashboard("--host", "codex")
        self.assertEqual([e["value"] for e in out["entries"]], ["new"])

    def test_extra_folders_errors_and_the_dashboard_itself(self):
        alpha = fake_plugin(self.tmp / "dev" / "alpha", "alpha", [self.entry("on")])
        broken = fake_plugin(self.tmp / "dev" / "broken", "broken", [{"label": "broken", "status": ["false"]}])
        me = fake_plugin(self.tmp / "dev" / "dashboard", "dashboard", [self.entry("self")])
        dirs = os.pathsep.join(map(str, (alpha, broken, me)))
        out = self.run_dashboard("--host", "codex", env={"BECAUSE_I_NEEDED_PLUGIN_DIRS": dirs})
        self.assertEqual([(e["plugin"], e["value"]) for e in out["entries"]], [("alpha", "on"), ("broken", "error")])
        self.assertEqual(self.run_dashboard("--host", "codex")["entries"], [])
        self.assertEqual(self.run_dashboard("--host", "codex")["line"], "")

    def test_the_repository_plugins_show_through_their_declarations(self):
        dirs = os.pathsep.join(str(ROOT / "plugins" / p) for p in ("budget", "free-hands", "peer-coding"))
        out = self.run_dashboard("--host", "claude", "--enabled", "",
                                 env={"BECAUSE_I_NEEDED_PLUGIN_DIRS": dirs, "XDG_CONFIG_HOME": str(self.tmp / "x")})
        self.assertEqual([(e["label"], e["value"]) for e in out["entries"]],
                         [("budget", "off"), ("free-hands", "off"), ("peer-coding", "off")])


if __name__ == "__main__":
    unittest.main()
