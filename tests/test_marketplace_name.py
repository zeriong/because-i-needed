"""Guard the marketplace rename and catch stale install identifiers."""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]

# Split old identifiers so this test's fixtures do not trigger the repository scan.
STALE_ID = "@" + "bin"
PATTERNS = (
    ("install id", re.compile(re.escape(STALE_ID) + r"(?![A-Za-z0-9_-])")),
    ("cache path", re.compile("cache/" + "bin/")),
    ("JSON key", re.compile('"' + "bin" + r'"\s*:')),
)


def find_stale_markers(text):
    """Return (line_number, line, marker) for each deprecated marker."""
    hits = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for marker, pattern in PATTERNS:
            if pattern.search(line):
                hits.append((line_number, line, marker))
    return hits


def is_legacy_line(line):
    return line.rstrip().endswith(("# legacy-id", "<!-- legacy-id -->"))


def line_hit(line_number, line):
    """Build one hit tuple, or return None when the line has no stale marker."""
    line_hits = find_stale_markers(line)
    if not line_hits:
        return None
    markers = ", ".join(marker for _, _, marker in line_hits)
    return line_number, line, markers


def scan_markdown(text):
    """Scan Markdown while honoring the section and line exceptions."""
    hits = []
    ignored_section_level = None
    fence_marker = None
    heading_pattern = re.compile(r"^(#{1,6})\s+.*$")
    for line_number, line in enumerate(text.splitlines(), 1):
        if fence_marker is not None:
            closing_fence = re.fullmatch(r"\s{0,3}(`{3,}|~{3,})\s*", line)
            if (
                closing_fence
                and closing_fence.group(1)[0] == fence_marker[0]
                and len(closing_fence.group(1)) >= len(fence_marker)
            ):
                fence_marker = None
        else:
            opening_fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
            if opening_fence:
                fence_marker = opening_fence.group(1)
            else:
                heading = heading_pattern.match(line)
                if heading:
                    level = len(heading.group(1))
                    if ignored_section_level is not None and level <= ignored_section_level:
                        ignored_section_level = None
                    if "`" + "bin" + "`" in line:
                        ignored_section_level = level

        # Fenced lines remain in the section active when the fence opened.
        if ignored_section_level is not None or is_legacy_line(line):
            continue
        hit = line_hit(line_number, line)
        if hit:
            hits.append(hit)
    return hits


def scan_file(text, path):
    """Scan one file, applying the section exception only to Markdown."""
    if Path(path).suffix == ".md":
        return scan_markdown(text)
    hits = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if is_legacy_line(line):
            continue
        hit = line_hit(line_number, line)
        if hit:
            hits.append(hit)
    return hits


def scan_repository(root=ROOT, paths=None):
    """Scan tracked and untracked repository files, or an explicit path list."""
    if paths is None:
        paths = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    hits = []
    for relative_path in paths:
        path = Path(relative_path)
        if path.name == "CHANGELOG.md" or path.parts[:1] == (".claude-x-codex",):
            continue
        try:
            content = (root / path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line, markers in scan_file(content, path):
            hits.append(f"{relative_path}:{line_number}: {line} [{markers}]")
    return hits


class MarketplaceNameTests(unittest.TestCase):
    def test_marketplace_name(self):
        manifest = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(manifest.get("name"), "because-i-needed")

    def test_repository_has_no_stale_marketplace_references(self):
        hits = scan_repository()
        self.assertFalse(hits, "\n".join(hits))

    def test_scan_patterns(self):
        stale_examples = (
            "plan-smith" + STALE_ID,
            "cache/" + "bin/" + "x",
            '"' + "bin" + '": {',
        )
        for example in stale_examples:
            with self.subTest(example=example):
                self.assertTrue(find_stale_markers(example))

        current_examples = (
            "@binary",
            "bin/",
            "@because-i-needed",
            "BIN_REPO_URL",
        )
        for example in current_examples:
            with self.subTest(example=example):
                self.assertFalse(find_stale_markers(example))

    def test_scan_exceptions(self):
        allowed = "# Moving from `bin`\nplan-smith" + STALE_ID + "\n## Details\ncache/" + "bin/" + "x\n# Current\n"
        self.assertFalse(scan_markdown(allowed))
        self.assertFalse(scan_markdown("plan-smith" + STALE_ID + " # legacy-id\n"))
        self.assertFalse(scan_markdown("plan-smith" + STALE_ID + " <!-- legacy-id -->\n"))

    def test_fenced_markdown_probes_and_section_closure(self):
        probe_a = "## Moving from `bin`\n```bash\n# remove the old registration\nclaude plugin uninstall plan-smith" + STALE_ID + "\n```"
        self.assertEqual(scan_markdown(probe_a), [])

        probe_b = "## Install\n```bash\n# not `bin` anymore\nclaude plugin install ux-ui" + STALE_ID + "\n```\nmore ux-ui" + STALE_ID + "\n## Next"
        hits = scan_markdown(probe_b)
        self.assertEqual([hit[0] for hit in hits], [4, 6])

        tilde_fence = "## Current\n~~~bash\n# Moving from `bin`\n~~~\nplain plan-smith" + STALE_ID + "\n"
        self.assertEqual([hit[0] for hit in scan_markdown(tilde_fence)], [5])

        info_string_is_not_a_closer = (
            "## Current\n```bash\nx\n```bash\n# Moving from `bin`\n```\nplan-smith"
            + STALE_ID
            + "\n```\nafter plan-smith"
            + STALE_ID
        )
        self.assertEqual([hit[0] for hit in scan_markdown(info_string_is_not_a_closer)], [7, 9])

        after_closed = "## Moving from `bin`\nignored plan-smith" + STALE_ID + "\n### Details\nignored cache/" + "bin/" + "x\n## Current\nplain plan-smith" + STALE_ID + "\n"
        self.assertEqual([hit[0] for hit in scan_markdown(after_closed)], [6])
        self.assertEqual([hit[0] for hit in scan_markdown("plain plan-smith" + STALE_ID + "\n")], [1])

    def test_non_markdown_probe_does_not_apply_heading_exception(self):
        text = "#!/usr/bin/env bash\n# handle old `bin` installs\nclaude plugin install harness" + STALE_ID + "\nrun x\n"
        self.assertEqual([hit[0] for hit in scan_file(text, "fixture.sh")], [3])

    def test_repository_scan_accepts_temp_root_and_explicit_paths(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            files = {
                "README.md": "Current name: plan-smith" + STALE_ID + "\n",
                "skills/reference.md": "Use cache/" + "bin/" + "plugin\n",
                "fixture.py": "value = 'harness" + STALE_ID + "'\n",
                "install.sh": "#!/usr/bin/env bash\n# handle old `bin` installs\nclaude plugin install harness" + STALE_ID + "\nrun x\n",
                "CHANGELOG.md": "Old name: plan-smith" + STALE_ID + "\n",
                ".claude-x-codex/notes.md": "Old name: plan-smith" + STALE_ID + "\n",
                "sub/.claude-x-codex/x.md": "Nested old name: plan-smith" + STALE_ID + "\n",
                "marked.md": "plan-smith" + STALE_ID + " <!-- legacy-id -->\n",
                "marked.py": "# plan-smith" + STALE_ID + " # legacy-id\n",
            }
            for name, content in files.items():
                file_path = root / name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")

            hits = scan_repository(root, files)

        self.assertEqual(len(hits), 5, "\n".join(hits))
        self.assertTrue(any(hit.startswith("README.md:1:") for hit in hits), hits)
        self.assertTrue(any(hit.startswith("skills/reference.md:1:") for hit in hits), hits)
        self.assertTrue(any(hit.startswith("fixture.py:1:") for hit in hits), hits)
        self.assertTrue(any(hit.startswith("install.sh:3:") for hit in hits), hits)
        self.assertTrue(any(hit.startswith("sub/.claude-x-codex/x.md:1:") for hit in hits), hits)
        self.assertFalse(any(hit.startswith("CHANGELOG.md:") for hit in hits), hits)
        self.assertFalse(any(hit.startswith(".claude-x-codex/") for hit in hits), hits)
        self.assertFalse(any("marked." in hit for hit in hits), hits)



def reserved_plugin_name(name):
    """Mirror of Claude Code's reserved-name check (2.1.287), compared on alphanumeric tokens (case and separators
    ignored): the name's tokens may not start with a reserved run followed by more tokens, may not spell an exact
    reserved name, and `official` may not touch `claude`/`anthropic` once separators are dropped (`officialclaude`,
    `my-claudeofficial`). `official-tools-for-claude` only warns."""
    tokens = [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]
    if "".join(tokens) in {"claude", "anthropic", "anthropics", "claudecode", "claudemods"}:
        return True
    for i in range(1, len(tokens)):
        if "".join(tokens[:i]) in {"claude", "anthropic", "anthropics", "ccplugin"}:
            return True
    flat = "".join(tokens)
    return any(word in flat for word in ("officialclaude", "claudeofficial", "officialanthropic", "anthropicofficial"))


class ReservedPluginNameTest(unittest.TestCase):
    """Claude Code 2.1.287 rejects plugin names that pass as Anthropic's own (claude-x-codex had to be renamed)."""

    REJECTED = ("claude-x-codex", "CLAUDE-tools", "claude_tools", "cc_plugin_tools", "cc-plugin-x", "official-claude",
                "claude-official", "official-anthropic-x", "anthropic-helper", "anthropics-x", "claude-code",
                "claude-mods", "claude", "c.l.a.u.d.e-tools", "c.c.plugin-tools", "officialclaude", "my-claudeofficial",
                "my-officialanthropic", "x-officialclaude-y")
    ALLOWED = ("peer-coding", "harness", "ux-ui", "free-hands", "cc-peer", "c-c-peer", "claudetools", "cc-plugin",
               "anthropicsx", "my-claude", "official-tools-for-claude", "officialtools", "my-claude-tools")
    # Checked against `claude plugin validate` on Claude Code 2.1.287 (review F1, F2); the last one only warns.

    def test_mirror_classifies_known_names(self):
        for name in self.REJECTED:
            self.assertTrue(reserved_plugin_name(name), name)
        for name in self.ALLOWED:
            self.assertFalse(reserved_plugin_name(name), name)

    def test_no_marketplace_plugin_uses_a_reserved_name(self):
        catalog = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        for entry in catalog["plugins"]:
            self.assertFalse(reserved_plugin_name(entry["name"]), entry["name"])
            for manifest in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
                data = json.loads((ROOT / entry["source"] / manifest).read_text())
                self.assertFalse(reserved_plugin_name(data["name"]), (entry["name"], manifest))

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
    def test_mirror_agrees_with_the_real_validator(self):
        with TemporaryDirectory() as temp:
            for name in ("c.l.a.u.d.e-tools", "c.c.plugin-tools", "claude_tools", "official-anthropic-x", "claudetools",
                         "cc-plugin", "official-tools-for-claude", "officialclaude", "my-claudeofficial", "peer-coding"):
                plugin = Path(temp) / name
                (plugin / ".claude-plugin").mkdir(parents=True)
                (plugin / "skills" / "run").mkdir(parents=True)
                (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps(
                    {"name": name, "version": "1.0.0", "description": "probe", "author": {"name": "lab"}}))
                (plugin / "skills" / "run" / "SKILL.md").write_text('---\nname: run\ndescription: "probe"\n---\nx\n')
                result = subprocess.run(["claude", "plugin", "validate", str(plugin)], capture_output=True, text=True)
                self.assertEqual(result.returncode != 0, reserved_plugin_name(name), (name, result.stdout[-300:]))

    @unittest.skipUnless(shutil.which("claude"), "claude CLI not installed")
    def test_the_marketplace_passes_the_real_validator(self):
        result = subprocess.run(["claude", "plugin", "validate", str(ROOT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout[-600:])

if __name__ == "__main__":
    unittest.main()
