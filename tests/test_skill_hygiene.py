# tests/test_skill_hygiene.py
"""Suite-wide instruction hygiene for every skill under skills/, and the plugin that ships them."""

from __future__ import annotations

import ast
import importlib
import json
import re
import unittest
from pathlib import Path

from skillcheck import BANNED_PHRASES, EMPHATIC, REPOSITORY, SKILLS, split_skill

TESTS = Path(__file__).resolve().parent
PLUGIN = REPOSITORY / ".claude-plugin"
# what a skill's own module asserts with assertLessEqual: body words, words before the core heading
# (MAX_WORDS_BEFORE_LOOP in research, _FLOW in brainstorm), reference words, description and compatibility
BUDGETS = ("MAX_SKILL_WORDS", "MAX_WORDS_BEFORE_[A-Z]+", "MAX_REFERENCE_WORDS", "MAX_DESCRIPTION_CHARS",
           "MAX_COMPATIBILITY_CHARS")
MAX_PLUGIN_DESCRIPTION_CHARS = 160


def skill_dirs() -> list[Path]:
    return sorted(path.parent for path in SKILLS.glob("*/SKILL.md"))


def manifest(name: str) -> dict:
    return json.loads((PLUGIN / name).read_text(encoding="utf-8"))


def upper_bounds(module: Path) -> set[str]:
    """The names a test module passes as the bound, the second argument, of assertLessEqual."""
    calls = [node for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))) if isinstance(node, ast.Call)]
    return {call.args[1].id for call in calls if getattr(call.func, "attr", None) == "assertLessEqual"
            and len(call.args) > 1 and isinstance(call.args[1], ast.Name)}


def metadata_version(skill_dir: Path) -> str | None:
    """The `version:` line under the frontmatter's `metadata:` block, without quotes."""
    block = re.search(r"^metadata:[ \t]*\n((?:[ \t]+.*(?:\n|$))*)", split_skill(skill_dir)[0], re.M)
    match = block and re.search(r"^[ \t]+version:[ \t]*(.*?)[ \t]*$", block.group(1), re.M)
    return match.group(1).strip("\"'") if match else None


class SuiteHygieneTests(unittest.TestCase):
    def test_no_emphatic_or_reasoning_language(self):
        for path in sorted(SKILLS.glob("*/**/*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(EMPHATIC.findall(text), [], path)
            for phrase in BANNED_PHRASES:
                self.assertNotIn(phrase, text.lower(), path)

    def test_every_skill_has_a_row(self):
        # nothing else holds a new skill to a size; the module is matched by its SKILL_DIR, since a folder
        # name also turns up in other modules' strings ("$vafer-research" in the brainstorm tests)
        modules = {}
        for path in sorted(TESTS.glob("test_*_skill.py")):
            modules[getattr(importlib.import_module(path.stem), "SKILL_DIR", None)] = path
        skills = skill_dirs()
        self.assertTrue(skills)
        for skill_dir in skills:
            with self.subTest(skill=skill_dir.name):
                self.assertIn(skill_dir, modules, f"no tests/test_*_skill.py sets SKILL_DIR to {skill_dir.name}")
                path = modules[skill_dir]
                bounds = upper_bounds(path)
                for budget in BUDGETS:
                    found = any(re.fullmatch(budget, name) for name in bounds)
                    self.assertTrue(found, f"{path.name} has no assertLessEqual(..., {budget})")

    def test_versions_equal_plugin_json(self):
        # plugin.json holds the one version label; no host reads metadata.version, so only this keeps them equal
        version = manifest("plugin.json")["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        skills = skill_dirs()
        self.assertTrue(skills)
        for skill_dir in skills:
            self.assertEqual(metadata_version(skill_dir), version, skill_dir.name)

    def test_plugin_and_marketplace_json(self):
        plugin, marketplace = manifest("plugin.json"), manifest("marketplace.json")
        self.assertEqual(plugin["name"], "vafer")
        self.assertEqual(marketplace["name"], "vafer")
        entry = marketplace["plugins"][0]
        self.assertEqual((entry["name"], entry["source"]), ("vafer", "./"))
        # one plain sentence, the same in the plugin list and on the plugin
        self.assertEqual(entry["description"], plugin["description"])
        self.assertRegex(plugin["description"], r"^[^.]+\.$")
        self.assertLess(len(plugin["description"]), MAX_PLUGIN_DESCRIPTION_CHARS)


if __name__ == "__main__":
    unittest.main()
