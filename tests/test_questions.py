"""Question-driven research gates: completeness is more than a valid citation."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ultra-deep-research" / "scripts"))
from vafer.store import ResearchError, Workspace, atomic_json


class QuestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vafer-questions-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = Workspace(self.root / "study")
        self.ws.init("Explain the harbour's development and its economic effects.")
        self.source = self.root / "register.txt"
        self.source.write_text("The harbour opened in 1850.\n\nThe railway arrived in 1870 and expanded the freight catchment.", encoding="utf-8")
        self.record = self.ws.ingest(self.source, completeness="full", required=True)
        self.ref = self.record["refs"][0]
        self.ws.path("report.md").write_text(f"The harbour opened in 1850. [[{self.ref}]]", encoding="utf-8")

    def question(self, **extra):
        return {"id": "opening", "question": "When did the harbour open?", "required": True,
                "status": "open", "origin": {"kind": "user", "basis": "Requested development history."}, **extra}

    def answered(self, **extra):
        return self.question(status="covered", evidence=[self.ref], context_read=True,
                             answer="It opened in 1850.",
                             support={"judgment": "supported", "rationale": "The register identifies the harbour opening, not its construction start."},
                             report_anchor="The harbour opened in 1850.", **extra)

    def seal(self):
        return self.ws.audit_seal({"id": "overview", "reviewer": "source examiner", "method": "self",
            "candidates": [{"id": "railway", "question": "How did the railway change the freight catchment?",
                            "source_url": "https://example.test/transport-register", "basis": "Transport register, railway paragraph: a new inland freight connection."}]})

    def checks(self):
        return {c["name"]: c for c in self.ws.verify()["checks"]}

    def test_valid_evidence_is_not_read_context_supported_answer_or_delivery(self):
        self.ws.patch({"coverage": [self.question(evidence=[self.ref], status="covered")]})
        progress = self.ws.status()["question_progress"][0]
        self.assertTrue(progress["evidence_found"])
        self.assertFalse(progress["context_read"])
        self.assertFalse(progress["answer_supported"])
        self.assertFalse(progress["reported"])
        self.assertIn("surrounding source context", self.ws.status()["next_actions"][0]["action"])
        self.assertFalse(self.checks()["required-coverage"]["ok"])

    def test_unsupported_meaning_is_actionable_despite_exact_citation(self):
        row = self.answered()
        row["answer"] = "The harbour closed in 1850."
        row["support"] = {"judgment": "unsupported", "rationale": "The source says opened; reversing the event changes the meaning."}
        self.ws.patch({"coverage": [row]})
        self.assertFalse(self.ws.status()["question_progress"][0]["answer_supported"])
        self.assertIn("assess source support", self.ws.status()["next_actions"][0]["action"])

    def test_report_anchor_requires_delivery_not_just_a_completed_note(self):
        self.ws.patch({"coverage": [self.answered()]})
        self.assertTrue(self.ws.status()["question_progress"][0]["reported"])
        self.ws.path("report.md").write_text(f"Only a different topic. [[{self.ref}]]", encoding="utf-8")
        status = self.ws.status()
        self.assertFalse(status["question_progress"][0]["reported"])
        self.assertEqual(status["invalidated_coverage"], ["opening"])
        self.assertEqual(self.ws.resume()["coverage"][0]["status"], "open")

    def test_broad_parent_cannot_hide_unanswered_required_child(self):
        parent = self.answered()
        child = self.question(id="rail", parent_id="opening", question="Why did rail access change the harbour's economy?")
        self.ws.patch({"coverage": [parent, child]})
        self.assertIn("opening", self.ws.status()["invalidated_coverage"])
        self.assertFalse(self.checks()["required-coverage"]["ok"])
        self.assertEqual(self.ws.status()["question_progress"][0]["unanswered_children"], ["rail"])

    def test_question_omission_and_provenance_erasure_fail_without_writing(self):
        self.ws.patch({"coverage": [self.question()]})
        before = self.ws.path("run.json").read_bytes()
        for payload in ({"coverage": []}, {"coverage": [{k: v for k, v in self.question().items() if k != "origin"}]}):
            with self.assertRaises(ResearchError):
                self.ws.update(payload)
            self.assertEqual(self.ws.path("run.json").read_bytes(), before)

    def test_explicit_scope_changes_keep_original_question_and_reason(self):
        self.ws.patch({"coverage": [self.question()]})
        with self.assertRaises(ResearchError):
            self.ws.patch({"coverage": [{"id": "opening", "question": "When was it built?"}]})
        self.ws.patch({"coverage": [{"id": "opening", "question": "When was it built?",
                                    "scope_change_reason": "User clarified construction, rather than opening."}]})
        self.assertEqual(self.ws.manifest()["coverage"][0]["scope_history"][0]["question"], "When did the harbour open?")
        with self.assertRaises(ResearchError):
            self.ws.patch({"coverage": [{"id": "opening", "question": "Who built it?"}]})
        with self.assertRaises(ResearchError):
            self.ws.patch({"coverage": [{"id": "opening", "status": "excluded"}]})

    def test_patch_updates_only_affected_question_and_can_clear_blocker(self):
        self.ws.patch({"coverage": [self.question(status="blocked", blocked_reason="Archive closed."),
                                     self.question(id="rail", question="When did rail arrive?", evidence=[self.ref])]})
        original = copy.deepcopy(self.ws.manifest()["coverage"][1])
        with patch.object(self.ws, "assert_current_ref", wraps=self.ws.assert_current_ref) as read:
            self.ws.patch({"coverage": [{"id": "opening", "blocked_reason": None, "status": "open"}]})
            # status inspects evidence, but update itself does not reload unchanged records.
            self.assertEqual(read.call_count, 2)
        result = self.ws.manifest()["coverage"]
        self.assertNotIn("blocked_reason", result[0])
        self.assertEqual(result[1], original)

    def test_new_evidence_reopens_prior_support_without_repeating_unrelated_rows(self):
        self.ws.patch({"coverage": [self.answered()]})
        self.ws.patch({"coverage": [{"id": "opening", "evidence": [self.record["refs"][1]]}]})
        row = self.ws.manifest()["coverage"][0]
        self.assertEqual(row["status"], "open")
        self.assertNotIn("support", row)
        self.assertNotIn("context_read", row)

    def test_answer_note_reuses_evidence_and_correction_reopens_support(self):
        note = {"id": "finding", "title": "Opening", "kind": "fact", "body": "It opened in 1850.", "evidence": [{"ref": self.ref}]}
        self.ws.commit(note)
        row = self.answered()
        row.pop("answer")
        row.pop("evidence")
        row["answer_note"] = "finding"
        self.ws.patch({"coverage": [row]})
        self.assertTrue(self.ws.status()["question_progress"][0]["reported"])
        note["body"] = "The recorded opening date is 1850; the construction start is unspecified."
        self.ws.commit(note)
        self.assertFalse(self.ws.status()["question_progress"][0]["answer_supported"])
        self.ws.patch({"coverage": [{"id": "opening", "next_action": "Recheck the revised note."}]})
        self.assertEqual(self.ws.manifest()["coverage"][0]["status"], "open")

    def test_audit_seal_is_immutable_and_every_candidate_requires_decision(self):
        seal = self.seal()
        with self.assertRaises(ResearchError):
            self.seal()
        with self.assertRaises(ResearchError):
            self.ws.audit_resolve({"id": "overview", "decisions": []})
        self.assertEqual(self.ws.manifest()["map_audits"][0]["candidates_sha256"], seal["candidates_sha256"])
        self.assertTrue(any(a["kind"] == "map-audit" for a in self.ws.status()["next_actions"]))

    def test_audit_candidate_becomes_unanswered_map_question_before_completion(self):
        self.ws.patch({"coverage": [self.answered()]})
        self.seal()
        self.assertFalse(self.checks()["source-derived-map-audit"]["ok"])
        with self.assertRaises(ResearchError):
            self.ws.audit_resolve({"id": "overview", "decisions": [{"candidate_id": "railway", "coverage_id": "rail", "rationale": "Needs a new branch."}]})
        self.ws.patch({"coverage": [self.question(id="rail", question="How did rail change the freight catchment?")]})
        self.ws.audit_resolve({"id": "overview", "decisions": [{"candidate_id": "railway", "coverage_id": "rail", "rationale": "The original map only recorded the opening; the new branch asks about the economic connection."}]})
        self.assertTrue(self.checks()["source-derived-map-audit"]["ok"])
        self.assertFalse(self.checks()["required-coverage"]["ok"])
        self.assertEqual(len(self.ws.manifest()["coverage"]), 2)

    def test_excluded_candidate_remains_visible_with_reason_and_self_label(self):
        self.seal()
        result = self.ws.audit_resolve({"id": "overview", "decisions": [{"candidate_id": "railway", "exclusion_reason": "User requested the pre-1860 harbour only; the railway is later."}]})
        self.assertEqual(result["method"], "self")
        self.assertIn("exclusion_reason", result["decisions"][0])
        with self.assertRaises(ResearchError):
            self.ws.audit_resolve({"id": "overview", "decisions": []})

    def test_changed_map_can_be_recompared_without_rewriting_sealed_candidates(self):
        self.ws.patch({"coverage": [self.question()]})
        seal = self.seal()
        decisions = [{"candidate_id": "railway", "coverage_id": "opening", "rationale": "Initial source comparison, retained for audit."}]
        self.ws.audit_resolve({"id": "overview", "decisions": decisions})
        self.ws.patch({"coverage": [{"id": "opening", "question": "How did rail change the freight catchment?",
                                    "scope_change_reason": "Independent overview exposed the missing mechanism."}]})
        self.assertFalse(self.checks()["source-derived-map-audit"]["ok"])
        result = self.ws.audit_resolve({"id": "overview", "decisions": [
            {"candidate_id": "railway", "coverage_id": "opening", "rationale": "The revised question now asks for the actual freight mechanism."}]})
        self.assertTrue(self.checks()["source-derived-map-audit"]["ok"])
        self.assertEqual(result["candidates_sha256"], seal["candidates_sha256"])
        self.assertEqual(result["comparison_history"][0]["decisions"][0]["mapped_question"], "When did the harbour open?")

    def test_open_topic_context_can_use_partial_capture_but_finite_core_cannot(self):
        partial = self.ws.ingest(self.source, source_id="excerpt", capture_kind="excerpt", completeness="partial", required=True)
        self.ws.patch({"coverage": [self.question(evidence=[self.ref, partial["refs"][0]], context_read=True)],
                       "reading_scope": {"kind": "open-topic", "rationale": "Research the harbour; the whole register is not the requested object."}})
        self.assertTrue(self.checks()["required-source-context"]["ok"])
        self.ws.patch({"reading_scope": {"kind": "finite-work", "rationale": "Now study the complete register."}})
        self.assertFalse(self.checks()["required-sources-full"]["ok"])

    def test_legacy_workspace_keeps_original_gates_and_readability(self):
        legacy = self.ws.manifest()
        legacy["tool_version"] = "0.0.2"
        legacy["coverage"] = [{"id": "old", "question": "When?", "required": True, "status": "covered", "evidence": [self.ref]}]
        atomic_json(self.ws.path("run.json"), legacy)
        self.assertEqual(self.ws.status()["question_progress"], [])
        self.assertTrue(self.checks()["required-coverage"]["ok"])
        self.assertNotIn("source-derived-map-audit", self.checks())

    def test_question_parent_cycles_are_rejected_before_writing(self):
        before = self.ws.path("run.json").read_bytes()
        with self.assertRaises(ResearchError):
            self.ws.patch({"coverage": [self.question(parent_id="rail"), self.question(id="rail", parent_id="opening")]})
        self.assertEqual(before, self.ws.path("run.json").read_bytes())

    def test_task_title_patch_cannot_reapprove_changed_note_dependency(self):
        note = {"id": "finding", "title": "Opening", "kind": "fact", "body": "It opened in 1850.", "evidence": [{"ref": self.ref}]}
        self.ws.commit(note)
        self.ws.patch({"tasks": [{"id": "read", "title": "Evaluate register", "status": "done", "inputs": ["finding"]}]})
        note["body"] = "The opening date is recorded as 1850; construction began earlier."
        self.ws.commit(note)
        self.assertEqual(self.ws.status()["invalidated_tasks"], ["read"])
        result = self.ws.patch({"tasks": [{"id": "read", "title": "Evaluate updated register"}]})
        self.assertEqual(result["tasks"][0]["status"], "pending")
        self.assertFalse(self.checks()["tasks-complete"]["ok"])
        self.ws.patch({"tasks": [{"id": "read", "status": "done"}]})
        self.assertTrue(self.checks()["tasks-complete"]["ok"])

    def test_new_task_inputs_require_renewed_completion(self):
        self.ws.patch({"tasks": [{"id": "read", "title": "Evaluate source", "status": "done", "inputs": [self.ref]}]})
        result = self.ws.patch({"tasks": [{"id": "read", "inputs": [self.record["refs"][1]]}]})
        self.assertEqual(result["tasks"][0]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
