"""Behavioral regression checks for unfinished research and bounded evidence reads."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ultra-deep-research" / "scripts"))
from vafer import extract
from vafer.store import Workspace, ResearchError


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vafer-planning-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = Workspace(self.root / "research")
        self.ws.init("Study a harbour and its transport history.")
        self.source = self.root / "source.txt"
        self.source.write_text("The harbour opened in 1850.\n\nThe railway arrived in 1870.", encoding="utf-8")
        self.ingested = self.ws.ingest(self.source, completeness="full")
        self.ref = self.ingested["refs"][0]

    def task(self, status="done"):
        return {"id": "read", "title": "Read the harbour register", "status": status, "inputs": [self.ref]}

    def coverage(self, **extra):
        return {"id": "transport", "question": "How did transport change?", "required": True,
                "status": "open", "evidence": [], **extra}

    def gap(self, **extra):
        return {"id": "rail", "description": "Railway connections remain unexplained.",
                "blocking": True, "resolved": False, **extra}

    def test_finished_tasks_do_not_hide_unplanned_gaps_or_coverage(self):
        self.ws.update({"tasks": [self.task()], "coverage": [self.coverage()], "gaps": [self.gap()]})
        before = self.ws.path("run.json").read_bytes()
        status = self.ws.status()
        self.assertEqual([(a["kind"], a["id"]) for a in status["next_actions"]],
                         [("gap", "rail"), ("coverage", "transport")])
        self.assertTrue(all(a["needs_planning"] for a in status["next_actions"]))
        self.assertEqual(before, self.ws.path("run.json").read_bytes())
        resumed = self.ws.resume()
        self.assertEqual(resumed["next_tasks"], [])  # Compatibility field names only actual tasks.
        self.assertEqual(len(resumed["next_actions"]), 2)

    def test_linked_pending_task_provides_action_without_duplicate_task_item(self):
        self.ws.update({"tasks": [self.task("pending")],
                        "gaps": [self.gap(task_ids=["read"])]})
        actions = self.ws.status()["next_actions"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["task_ids"], ["read"])
        self.assertFalse(actions[0]["needs_planning"])

    def test_completed_link_does_not_resolve_gap(self):
        self.ws.update({"tasks": [self.task()], "gaps": [self.gap(task_ids=["read"])]})
        self.assertTrue(self.ws.status()["next_actions"][0]["needs_planning"])

    def test_shared_blocked_task_is_not_scheduled_through_another_requirement(self):
        self.ws.update({"tasks": [self.task("pending")],
                        "coverage": [self.coverage(task_ids=["read"])],
                        "gaps": [self.gap(task_ids=["read"], coverage_ids=["transport"],
                                          blocked_reason="Archive access required.")]})
        state = self.ws.status()
        self.assertEqual(state["next_actions"], [])
        self.assertEqual(len(state["blocked_actions"]), 2)
        gap = next(a for a in state["blocked_actions"] if a["kind"] == "gap")
        self.assertEqual(gap["coverage_ids"], ["transport"])

    def test_blocked_work_is_visible_without_becoming_an_automatic_retry(self):
        self.ws.update({"tasks": [self.task("pending")], "gaps": [self.gap(
            task_ids=["read"], next_action="Read the archive after access is restored.",
            blocked_reason="Archive temporarily inaccessible.")]})
        state = self.ws.resume()
        self.assertEqual(state["next_actions"], [])
        self.assertEqual(state["blocked_actions"][0]["id"], "rail")
        self.assertEqual(state["blocked_actions"][0]["task_ids"], ["read"])

    def test_dangling_links_and_deleting_linked_tasks_are_rejected(self):
        with self.assertRaises(ResearchError):
            self.ws.update({"gaps": [self.gap(task_ids=["absent"])]})
        self.ws.update({"tasks": [self.task()], "gaps": [self.gap(task_ids=["read"])]})
        before = self.ws.path("run.json").read_bytes()
        with self.assertRaises(ResearchError):
            self.ws.update({"tasks": []})
        self.assertEqual(before, self.ws.path("run.json").read_bytes())

    def test_resolved_and_excluded_requirements_leave_agenda(self):
        self.ws.update({"gaps": [self.gap(resolved=True)],
                        "coverage": [self.coverage(status="excluded", required=False)]})
        self.assertEqual(self.ws.status()["next_actions"], [])

    def test_stale_covered_evidence_is_visible_before_resume(self):
        self.ws.update({"coverage": [self.coverage(status="covered", evidence=[self.ref])]})
        self.source.write_text("The corrected harbour opening date is 1852.", encoding="utf-8")
        self.ws.ingest(self.source, completeness="full")
        state = self.ws.status()
        self.assertEqual(state["invalidated_coverage"], ["transport"])
        self.assertEqual(state["next_actions"][0]["id"], "transport")

    def test_empty_covered_branch_is_actionable_and_reopens_on_resume(self):
        self.ws.update({"coverage": [self.coverage(status="covered")]})
        self.assertEqual(self.ws.status()["next_actions"][0]["id"], "transport")
        self.assertEqual(self.ws.resume()["coverage"][0]["status"], "open")

    def test_excluded_branch_stays_excluded_when_its_old_evidence_changes(self):
        self.ws.update({"coverage": [self.coverage(status="excluded", required=False, evidence=[self.ref])]})
        self.source.write_text("The harbour register was corrected.", encoding="utf-8")
        self.ws.ingest(self.source, completeness="full")
        state = self.ws.resume()
        self.assertEqual(state["coverage"][0]["status"], "excluded")
        self.assertEqual(state["invalidated_coverage"], [])
        self.assertEqual(state["next_actions"], [])

    def test_covered_branch_cannot_hide_linked_blocking_gap(self):
        self.ws.update({"coverage": [self.coverage(status="covered", evidence=[self.ref])],
                        "gaps": [self.gap(coverage_ids=["transport"])]})
        checks = {c["name"]: c for c in self.ws.verify()["checks"]}
        self.assertFalse(checks["coverage-gap-consistency"]["ok"])

    def test_identical_update_preserves_review_and_does_not_mutate_input(self):
        payload = {"tasks": [self.task()], "coverage": [self.coverage()]}
        original = copy.deepcopy(payload)
        self.ws.update(payload)
        self.assertEqual(payload, original)
        self.ws.path("report.md").write_text(f"Harbour study [[{self.ref}]]", encoding="utf-8")
        self.ws.update({"report": "report.md", "reviews": {"scope": {
            "status": "passed", "reviewer": "test", "method": "self", "details": "Synthetic test."}}})
        review = self.ws.status()["reviews"]["scope"]
        self.ws.update(payload)
        self.assertEqual(review, self.ws.status()["reviews"]["scope"])
        self.ws.update({"gaps": [self.gap()]})
        self.assertEqual(self.ws.status()["reviews"]["scope"]["status"], "pending")

    def test_batch_reads_load_each_revision_once_and_keep_full_text(self):
        refs = self.ingested["refs"]
        singles = [self.ws.read(ref) for ref in refs]
        with patch.object(self.ws, "passages", wraps=self.ws.passages) as calls:
            batch = self.ws.read_many(refs)
            self.assertEqual(calls.call_count, 1)
        self.assertEqual(len(batch["sources"]), 1)
        for single, result in zip(singles, batch["passages"]):
            self.assertEqual(single["text"], result["text"])
            self.assertEqual(single["locator"], result["locator"])
            self.assertEqual(single["source"], batch["sources"][result["source_key"]])
            self.assertTrue(result["untrusted"])
        for invalid in ([], "wrong", [self.ref] * 101, [self.ref, "invalid"]):
            with self.assertRaises(ResearchError):
                self.ws.read_many(invalid)

    def test_legacy_extraction_metadata_still_verifies(self):
        original = extract.extract_file
        def legacy(*args, **kwargs):
            result = original(*args, **kwargs)
            result.pop("capture_quality", None)
            return result
        with patch.object(extract, "extract_file", side_effect=legacy):
            self.ws.ingest(self.source, source_id="legacy", completeness="full")
        checks = {c["name"]: c for c in self.ws.verify()["checks"]}
        self.assertTrue(checks["source-integrity"]["ok"], checks["source-integrity"])


if __name__ == "__main__":
    unittest.main()
