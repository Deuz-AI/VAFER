"""Offline tests for skills/vafer-brainstorm: the workflow's control flow and skill hygiene."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL_DIR = REPOSITORY / "skills" / "vafer-brainstorm"
WORKFLOW = SKILL_DIR / "workflows" / "brainstorm.js"
MAX_SKILL_WORDS = 600
MAX_DESCRIPTION_CHARS = 450
MAX_COMPATIBILITY_CHARS = 500
MAX_WORKFLOW_LINES = 220
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
EMPHATIC = re.compile(r"\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|REQUIRED)\b")
ARGS = {"topic": "Yeni skill fikirleri", "goal": "G", "context": "C", "language": "Turkish", "run": "C:\\runs\\b\\"}
JUDGES = ["judge:value", "judge:feasibility", "judge:novelty"]


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class WorkflowTests(unittest.TestCase):
    def play(self, **scenario):
        scenario.setdefault("args", ARGS)
        out = subprocess.run(["node", str(REPOSITORY / "tests" / "brainstorm_harness.js"), str(WORKFLOW), json.dumps(scenario)],
                             capture_output=True, text=True, encoding="utf-8", check=True)
        return json.loads(out.stdout)

    def labels(self, played):
        return [c["label"] for c in played["calls"]]

    def prompt(self, played, label):
        return next(c["prompt"] for c in played["calls"] if c["label"] == label)

    def test_standard_run_diverges_builds_converges_and_writes(self):
        played = self.play()
        self.assertEqual(self.labels(played), [f"idea:{i}" for i in range(1, 6)] + ["build:1", "build:2", "curate"] + JUDGES + ["write"])
        result = played["result"]
        self.assertEqual((result["ok"], result["agents"], result["file"]), (True, 12, "C:/runs/b/brainstorm.md"))
        self.assertEqual(result["counts"], {"raw": 14, "ideas": 14, "themes": 2})
        efforts = {c["label"].split(":")[0]: c["effort"] for c in played["calls"]}
        self.assertEqual(efforts, {"idea": "medium", "build": "medium", "curate": "medium", "judge": "low", "write": "medium"})
        self.assertTrue(all(c.get("model") is None for c in played["calls"]))

    def test_quick_skips_the_build_round_and_deep_uses_every_angle(self):
        quick = self.play(args={**ARGS, "depth": "quick"})
        self.assertEqual(self.labels(quick), ["idea:1", "idea:2", "idea:3", "curate"] + JUDGES + ["write"])
        deep = self.play(args={**ARGS, "depth": "deep", "model": "opus"})
        self.assertEqual(len(self.labels(deep)), 17)
        self.assertEqual(len([x for x in self.labels(deep) if x.startswith("build")]), 4)
        self.assertTrue(all(c["model"] == "opus" for c in deep["calls"]))

    def test_ideators_work_alone_and_builders_see_the_whole_table(self):
        played = self.play()
        idea = self.prompt(played, "idea:2")
        self.assertIn("Topic: Yeni skill fikirleri", idea)
        self.assertIn("Your angle: First principles.", idea)
        self.assertNotIn("idea 1.1", idea)
        build = self.prompt(played, "build:1")
        self.assertIn("1. idea 1.1 — pitch of idea 1.1", build)
        self.assertIn("10. idea 5.2 — pitch of idea 5.2", build)
        self.assertIn("Your move: Combine.", build)

    def test_the_curator_merges_duplicates_and_no_idea_is_lost(self):
        played = self.play(merge=[[1, 3]], drop=[5])
        result = played["result"]
        self.assertEqual(result["counts"], {"raw": 14, "ideas": 13, "themes": 3})
        write = self.prompt(played, "write")
        self.assertIn("Diğer\n- idea 3.1 — pitch of idea 3.1", write)
        self.assertNotIn("idea 2.1", write)
        self.assertTrue(any("not accounted for" in line for line in played["logs"]))

    def test_ranking_and_bold_bets_are_computed_from_the_scores(self):
        scores = {"value": {"2": 5, "4": 5}, "feasibility": {"2": 5}, "novelty": {"2": 1, "7": 5, "9": 5}}
        played = self.play(scores=scores, fail=["write"], args={**ARGS, "limits": {"picks": 2}})
        result = played["result"]
        self.assertFalse(result["ok"])
        self.assertEqual([p["title"] for p in result["picks"]], ["idea 2.2", "idea 1.2"])
        self.assertEqual([p["title"] for p in result["bold"]], ["idea 4.1", "idea 5.1"])
        write = self.prompt(played, "write")
        self.assertIn("- idea 2.2 — pitch of idea 2.2 (value 5, feasibility 3, novelty 3; value: strong)", write)
        self.assertLess(write.index("idea 2.2 — pitch of idea 2.2 (value"), write.index("idea 1.2 — pitch of idea 1.2 (value"))

    def test_judges_read_the_list_from_different_places_and_gaps_get_the_middle_score(self):
        played = self.play(skip=[3])
        firsts = [re.search(r"^(\d+)\. ", self.prompt(played, label), re.M).group(1) for label in JUDGES]
        self.assertEqual(firsts, ["1", "5", "10"])
        self.assertIn("- idea 2.1 — pitch of idea 2.1 (9)", self.prompt(played, "write"))
        self.assertIn("Use the whole scale", self.prompt(played, "judge:value"))

    def test_follow_up_rounds_steer_the_ideators(self):
        args = {**ARGS, "avoid": ["Eski fikir"], "focus": "isimler", "lenses": ["Ses", {"name": "Metafor", "how": "Benzetme kur."}]}
        played = self.play(args=args)
        self.assertEqual([x for x in self.labels(played) if x.startswith("idea")], ["idea:1", "idea:2"])
        idea = self.prompt(played, "idea:2")
        for text in ("- Eski fikir", "Stay within: isimler", "Your angle: Metafor. Benzetme kur."):
            self.assertIn(text, idea)

    def test_failures_are_reported_and_ideas_survive(self):
        self.assertEqual(self.play(args={"topic": "T"})["result"]["error"], "missing args: run")
        self.assertFalse(self.play(fail=["idea"])["result"]["ok"])
        one_lost = self.play(fail=["idea:2"])["result"]
        self.assertEqual((one_lost["ok"], one_lost["counts"]["raw"]), (True, 12))
        uncurated = self.play(fail=["curate"])
        self.assertEqual(uncurated["result"]["counts"], {"raw": 14, "ideas": 14, "themes": 1})
        self.assertTrue(any("without merging" in line for line in uncurated["logs"]))
        unjudged = self.play(fail=["judge"])["result"]
        self.assertFalse(unjudged["ok"])
        self.assertEqual(len(unjudged["ideas"]), 14)
        self.assertTrue(self.play(fail=["judge:value"])["result"]["ok"])


class HygieneTests(unittest.TestCase):
    def split_skill(self):
        _, frontmatter, body = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").split("---\n", 2)
        return frontmatter, body

    def test_frontmatter(self):
        fields = {m.group(1): m.group(2).strip() for m in re.finditer(r"^([A-Za-z][\w-]*):(.*)$", self.split_skill()[0], re.M)}
        self.assertLessEqual(set(fields), ALLOWED_FRONTMATTER)
        self.assertEqual(fields["name"], "vafer-brainstorm")
        self.assertLessEqual(len(fields["description"]), MAX_DESCRIPTION_CHARS)
        self.assertLessEqual(len(fields["compatibility"]), MAX_COMPATIBILITY_CHARS)

    def test_skill_stays_short_and_matches_the_workflow(self):
        body = self.split_skill()[1]
        self.assertLessEqual(len(body.split()), MAX_SKILL_WORDS)
        self.assertIn("workflows/brainstorm.js", body)
        self.assertIn("Nothing else runs after that.", body)
        source = WORKFLOW.read_text(encoding="utf-8")
        for arg in ("topic", "goal", "context", "language", "depth", "run", "lenses", "avoid", "focus"):
            self.assertIn(f"A.{arg}", source, arg)
            self.assertRegex(body, rf"\b{arg}\b")
        for depth, agents in (("quick", 8), ("standard", 12), ("deep", 17)):
            self.assertRegex(body, rf"\| {depth} \|[^|]*\| {agents} \|")

    def test_no_emphatic_language_and_workflow_budget(self):
        for path in (SKILL_DIR / "SKILL.md", WORKFLOW):
            self.assertEqual(EMPHATIC.findall(path.read_text(encoding="utf-8")), [], path.name)
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertTrue(source.startswith("export const meta = {"))
        self.assertLessEqual(len(source.splitlines()), MAX_WORKFLOW_LINES)
        for banned in ("Date.now", "Math.random", "new Date()"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
