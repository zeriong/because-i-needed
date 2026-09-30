"""Fail when a plugin's instructions or scripts name a model version.

Every dispatch resolves the newest model of its family at run time
(scripts/latest-model.py), so a versioned id written into a skill, agent, hook or
script would pin an older model once a newer one ships.
Run with python3 -m unittest discover -s tests -v.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("skills", "agents", "hooks", "scripts")
FAMILY = r"(?:opus|sonnet|haiku|fable)"
PIN = re.compile(r"\bgpt-\d+(?:\.\d+)*-[a-z]+\b"
                 rf"|\bclaude-{FAMILY}-\d"
                 rf"|\bclaude-\d+(?:-\d+)*-{FAMILY}\b")


class ModelPinTests(unittest.TestCase):
    def test_no_versioned_model_ids_in_plugin_instructions(self):
        hits = []
        for plugin in sorted((ROOT / "plugins").iterdir()):
            for area in SCANNED:
                for path in sorted((plugin / area).rglob("*")):
                    if not path.is_file():
                        continue
                    try:
                        text = path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
                    for number, line in enumerate(text.splitlines(), 1):
                        for match in PIN.finditer(line):
                            hits.append(f"{path.relative_to(ROOT)}:{number}: {match.group(0)}")
        self.assertEqual(hits, [], "versioned model ids pin an older model:\n" + "\n".join(hits))

    def test_pattern_catches_the_pins_it_exists_for(self):
        for pinned in ("gpt-6-sol", "gpt-6.1-sol", "gpt-5.6-luna", "claude-opus-5-5", "claude-sonnet-4",
                       "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "--model claude-3-haiku-20240307"):
            self.assertRegex(pinned, PIN)
        for family in ("sol", "luna", "opus", "gpt-<n>-sol", "claude-opus-<n>", "claude-x-codex"):
            self.assertNotRegex(family, PIN)


if __name__ == "__main__":
    unittest.main()
