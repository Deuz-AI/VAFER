# tests/test_skill_hygiene.py
"""Suite-wide instruction hygiene for every skill under skills/."""

from __future__ import annotations

import unittest

from skillcheck import BANNED_PHRASES, EMPHATIC, SKILLS


class SuiteHygieneTests(unittest.TestCase):
    def test_no_emphatic_or_reasoning_language(self):
        for path in sorted(SKILLS.glob("*/**/*.md")):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(EMPHATIC.findall(text), [], path)
            for phrase in BANNED_PHRASES:
                self.assertNotIn(phrase, text.lower(), path)

if __name__ == "__main__":
    unittest.main()
