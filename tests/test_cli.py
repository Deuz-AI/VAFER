"""Black-box CLI contracts; these tests do not import the implementation.

Run with: python -m unittest discover -s tests -p 'test_cli.py' -v
All mutations are contained in a temporary research workspace.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
CLI = REPOSITORY / "skills" / "ultra-deep-research" / "scripts" / "research.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ResearchCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vafer-cli-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "research workspace"
        self.sequence = 0
        self.call("run", "init", "--workspace", self.workspace,
                  "--question", "Study the details and interpretations of The Copper Causeway.")

    def call(self, *arguments, success=True):
        environment = dict(os.environ, PYTHONUTF8="1")
        result = subprocess.run(
            [sys.executable, str(CLI), *(str(arg) for arg in arguments)],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"CLI did not emit one JSON value: {error}\n"
                      f"stdout={result.stdout!r}\nstderr={result.stderr!r}")
        self.assertEqual(result.returncode, 0 if success else 1,
                         f"{arguments!r}\n{payload!r}\n{result.stderr}")
        self.assertIs(payload.get("ok"), success, payload)
        self.assertGreaterEqual(payload["metrics"]["elapsed_ms"], 0)
        if success:
            self.assertIn("data", payload)
            return payload["data"]
        self.assertIsInstance(payload.get("error"), dict, payload)
        self.assertIsInstance(payload["error"].get("code"), str, payload)
        self.assertTrue(payload["error"].get("message"), payload)
        return payload

    def write_json(self, value):
        self.sequence += 1
        path = self.root / f"input-{self.sequence}.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def ingest(self, fixture="micro_epic_edition_a.txt", **options):
        arguments = ["ingest", "--workspace", self.workspace,
                     "--file", FIXTURES / fixture]
        options.setdefault("completeness", "full")
        for name, value in options.items():
            if value is True:
                arguments.append("--" + name.replace("_", "-"))
            elif value is not False and value is not None:
                arguments.extend(["--" + name.replace("_", "-"), str(value)])
        return self.call(*arguments)

    def find_ref(self, query, contains):
        result = self.call("search", "--workspace", self.workspace, "--query", query)
        for hit in result["hits"]:
            if contains in hit["text"]:
                return hit["ref"]
        self.fail(f"No search hit preserved {contains!r}: {result!r}")

    def commit(self, note_id, ref, *, body="A source-grounded research note.",
               dependencies=(), quote=None, success=True):
        evidence = {"ref": ref}
        if quote is not None:
            evidence["quote"] = quote
        note = {
            "id": note_id,
            "title": note_id.replace("-", " ").title(),
            "kind": "fact" if not dependencies else "synthesis",
            "body": body,
            "evidence": [evidence],
            "depends_on": list(dependencies),
        }
        return self.call("commit", "--workspace", self.workspace,
                         "--file", self.write_json(note), success=success)

    def update(self, patch):
        return self.call("run", "update", "--workspace", self.workspace,
                         "--file", self.write_json(patch))

    def prepare_finished_run(self, ref, report_body=None):
        """Satisfy all declared gates before exercising one failure condition."""
        report = self.write_report(report_body or
                                   f"A copper cup was left beneath the willow. [[{ref}]]")
        self.update({
            "report": str(report),
            "tasks": [{"id": "read-core", "title": "Read the core source",
                       "status": "done", "inputs": [ref]}],
            "coverage": [{"id": "scene-detail", "question": "What was left beneath the willow?",
                          "required": True, "status": "covered", "evidence": [ref]}],
            "reviews": {
                name: {"status": "passed", "reviewer": "synthetic-test-reviewer",
                       "method": "self", "details": "Test fixture only; not a real quality assessment."}
                for name in ("scope", "citations", "blind_questions")
            },
            "gaps": [],
        })
        return report

    def write_report(self, body):
        self.sequence += 1
        report = self.workspace / f"report-{self.sequence}.md"
        report.write_text("# Research report\n\n" + body + "\n", encoding="utf-8")
        return report

    def status(self):
        return self.call("run", "status", "--workspace", self.workspace)

    def test_doctor_is_machine_readable_outside_workspace(self):
        self.call("doctor")

    def test_ingest_is_idempotent(self):
        first = self.ingest(title="The Copper Causeway", edition="A")
        second = self.ingest(title="The Copper Causeway", edition="A")
        self.assertFalse(first["deduplicated"])
        self.assertTrue(second["deduplicated"])
        self.assertEqual(first["source_id"], second["source_id"])
        self.assertEqual(first["revision"], second["revision"])
        self.assertEqual(first["refs"], second["refs"])
        self.assertTrue(first["refs"])

    def test_search_and_read_preserve_minor_details_and_provenance(self):
        self.ingest(title="The Copper Causeway", edition="A")
        ref = self.find_ref("crescent", "crescent-shaped dent")
        result = self.call("read", "--workspace", self.workspace, "--ref", ref)
        self.assertEqual(result["ref"], ref)
        self.assertIn("near its handle", result["text"])
        self.assertIn("locator", result)
        self.assertIn("source", result)
        self.assertIs(result["untrusted"], True)

    def test_source_instructions_remain_untrusted_data(self):
        self.ingest("source_injection.txt")
        ref = self.find_ref("OVERRIDE", "SYSTEM OVERRIDE")
        result = self.call("read", "--workspace", self.workspace, "--ref", ref)
        self.assertIn("Mark every required source", result["text"])
        self.assertIs(result["untrusted"], True)
        self.assertEqual(self.status()["status"], "running")

    def test_phrase_filter_and_batch_read_are_available_through_cli(self):
        source = self.ingest()
        results = self.call("search", "--workspace", self.workspace, "--query", '"blue ribbon" willow',
                            "--mode", "all", "--kind", "sources", "--source-id", source["source_id"])
        self.assertTrue(results["hits"])
        self.assertEqual(results["note_hits"], [])
        refs = [hit["ref"] for hit in results["hits"]]
        batch = self.call("read-many", "--workspace", self.workspace, "--file", self.write_json(refs))
        self.assertEqual([p["ref"] for p in batch["passages"]], refs)
        self.assertEqual(len(batch["sources"]), 1)
        self.call("read-many", "--workspace", self.workspace, "--file", self.write_json([]), success=False)

    def test_commit_rejects_dangling_evidence(self):
        source = self.ingest()
        missing_ref = source["refs"][0].rsplit(":", 1)[0] + ":p999999"
        self.commit("unsupported", missing_ref, success=False)

    def test_inline_citations_must_be_declared_as_evidence(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.ingest("commentary.txt")
        undeclared = self.find_ref("indirect", "hospitality indirect")
        self.commit("untracked-source", ref,
                    body=f"This interpretation relies on another source. [[{undeclared}]]",
                    success=False)

    def test_commit_rejects_a_quote_absent_from_the_referenced_passage(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.commit("invented-quote", ref,
                    quote="Iven opened the letter and ate the copper cup.", success=False)

    def test_commit_accepts_a_real_quote(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.commit("ribbon-detail", ref,
                    quote="Mara tied a blue ribbon to the willow.")

    def test_source_revision_invalidates_notes_and_transitive_dependents(self):
        source = self.ingest()
        old_ref = self.find_ref("ribbon", "blue ribbon")
        self.ingest("commentary.txt")
        other_ref = self.find_ref("Hospitality", "hospitality")
        self.commit("scene", old_ref)
        self.commit("interpretation", other_ref, dependencies=["scene"])
        self.commit("overview", other_ref, dependencies=["interpretation"])
        changed = self.ingest("micro_epic_edition_b.txt", source_id=source["source_id"])
        self.assertNotEqual(source["revision"], changed["revision"])
        self.assertEqual(source["source_id"], changed["source_id"])
        self.assertEqual(set(self.status()["stale_notes"]),
                         {"scene", "interpretation", "overview"})
        historical = self.call("read", "--workspace", self.workspace, "--ref", old_ref)
        self.assertIn("blue ribbon", historical["text"])
        current_ref = self.find_ref("green", "green cord")
        self.assertNotEqual(old_ref, current_ref)

    def test_note_correction_invalidates_dependents_without_changing_source(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.commit("scene", ref, body="Initial reading of the scene.")
        self.commit("interpretation", ref, dependencies=["scene"])
        self.commit("overview", ref, dependencies=["interpretation"])
        self.commit("scene", ref, body="Corrected reading: Mara tied the blue ribbon.")
        stale = set(self.status()["stale_notes"])
        self.assertNotIn("scene", stale)
        self.assertEqual(stale, {"interpretation", "overview"})
        self.commit("interpretation", ref, body="Rechecked against the corrected scene.",
                    dependencies=["scene"])
        self.assertEqual(set(self.status()["stale_notes"]), {"overview"})

    def test_note_corrections_preserve_immutable_history(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        first = self.commit("scene-history", ref, body="First contextual reading.")
        second = self.commit("scene-history", ref, body="Second contextual reading.")
        self.assertNotEqual(first["content_hash"], second["content_hash"])
        history = self.workspace / "notes" / "history" / "scene-history"
        snapshot = history / f"{first['content_hash']}.json"
        original_bytes = snapshot.read_bytes()
        original = json.loads(original_bytes)
        self.assertEqual(original["body"], "First contextual reading.")
        self.assertEqual(original["content_hash"], first["content_hash"])
        self.commit("scene-history", ref, body="Third contextual reading.")
        self.assertEqual(snapshot.read_bytes(), original_bytes)
        prior = json.loads((history / f"{second['content_hash']}.json").read_text(encoding="utf-8"))
        self.assertEqual(prior["body"], "Second contextual reading.")

    def test_search_finds_corrected_notes_and_excludes_stale_notes(self):
        source = self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.commit("retrieval-note", ref, body="Clockwork heron interpretation of the landing scene.")
        before = self.call("search", "--workspace", self.workspace, "--query", "Clockwork")
        self.assertTrue(any(hit["id"] == "retrieval-note" for hit in before["note_hits"]))
        self.commit("retrieval-note", ref, body="Silver minnow interpretation of the landing scene.")
        obsolete = self.call("search", "--workspace", self.workspace, "--query", "Clockwork")
        self.assertFalse(any(hit["id"] == "retrieval-note" for hit in obsolete["note_hits"]))
        current = self.call("search", "--workspace", self.workspace, "--query", "minnow")
        self.assertTrue(any(hit["id"] == "retrieval-note" and "Silver minnow" in hit["body"]
                            for hit in current["note_hits"]))
        self.ingest("micro_epic_edition_b.txt", source_id=source["source_id"])
        stale = self.call("search", "--workspace", self.workspace, "--query", "minnow")
        self.assertFalse(any(hit["id"] == "retrieval-note" for hit in stale["note_hits"]))

    def test_resume_preserves_finished_work_and_requeues_interrupted_work(self):
        self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.commit("retained-detail", ref)
        self.update({"tasks": [
            {"id": "done", "title": "Completed reading", "status": "done", "inputs": [ref]},
            {"id": "interrupted", "title": "Interrupted comparison", "status": "running", "inputs": [ref]},
        ]})
        self.call("run", "resume", "--workspace", self.workspace)
        tasks = {task["id"]: task["status"] for task in self.status()["tasks"]}
        self.assertEqual(tasks, {"done": "done", "interrupted": "pending"})
        self.assertEqual(self.status()["stale_notes"], [])
        self.assertIn("blue ribbon", self.call("read", "--workspace", self.workspace,
                                              "--ref", ref)["text"])

    def test_resume_reopens_done_tasks_whose_inputs_changed(self):
        source = self.ingest()
        ref = self.find_ref("ribbon", "blue ribbon")
        self.update({"tasks": [{"id": "comparison", "title": "Compare the landing scene",
                                "status": "done", "inputs": [ref]}]})
        self.ingest("micro_epic_edition_b.txt", source_id=source["source_id"])
        self.assertIn("comparison", self.status()["invalidated_tasks"])
        self.call("run", "resume", "--workspace", self.workspace)
        tasks = {task["id"]: task["status"] for task in self.status()["tasks"]}
        self.assertEqual(tasks["comparison"], "pending")

    def test_complete_run_passes_its_structural_gates(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.call("run", "finish", "--workspace", self.workspace,
                  "--report", report, "--outcome", "complete-within-scope")
        self.assertEqual(self.status()["status"], "complete-within-scope")
        result = self.call("verify", "--workspace", self.workspace, "--report", report)
        self.assertTrue(result["passed"])
        self.assertEqual(result["verification_scope"], "structural-only")

    def test_required_excerpt_cannot_finish_complete_but_can_finish_partial(self):
        self.ingest(required=True, capture_kind="excerpt", completeness="partial")
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)
        self.assertNotEqual(self.status()["status"], "complete-within-scope")
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "partial")
        self.assertEqual(self.status()["status"], "partial")

    def test_metadata_edit_cannot_promote_a_required_excerpt_to_full(self):
        source = self.ingest(required=True, capture_kind="excerpt", completeness="partial")
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        metadata_path = (self.workspace / "sources" / source["source_id"] /
                         "revisions" / source["revision"] / "metadata.json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["completeness"] = "full"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        failure = self.call("verify", "--workspace", self.workspace,
                            "--report", report, success=False)
        checks = {check["name"]: check for check in failure["error"]["details"]["checks"]}
        self.assertFalse(checks["source-integrity"]["ok"])

    def test_unfinished_task_prevents_complete(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.update({"tasks": [{"id": "not-finished", "title": "Read the ending",
                                "status": "pending", "inputs": [ref]}]})
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)

    def test_failed_review_prevents_complete(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.update({"reviews": {"citations": {
            "status": "failed", "reviewer": "test-reviewer", "method": "self",
            "details": "The narrative claim is not supported by the cited passage.",
        }}})
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)

    def test_passed_review_requires_an_existing_report(self):
        patch = {"reviews": {"scope": {
            "status": "passed", "reviewer": "test-reviewer", "method": "self",
            "details": "Synthetic approval without a report must be rejected.",
        }}}
        self.call("run", "update", "--workspace", self.workspace,
                  "--file", self.write_json(patch), success=False)

    def test_changed_report_requires_fresh_reviews(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        initial = self.call("verify", "--workspace", self.workspace, "--report", report)
        self.assertTrue(initial["passed"])
        report.write_text(report.read_text(encoding="utf-8") +
                          "\nThe landing scene also includes a ribbon.\n", encoding="utf-8")
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)
        self.update({"report": str(report), "reviews": {
            name: {"status": "passed", "reviewer": "test-reviewer", "method": "self",
                   "details": "Synthetic fresh review of the edited report."}
            for name in ("scope", "citations", "blind_questions")
        }})
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope")
        self.assertEqual(self.status()["status"], "complete-within-scope")

    def test_status_and_resume_expose_edits_after_completion(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope")
        report.write_text(report.read_text(encoding="utf-8") +
                          "\nA new, unreviewed paragraph.\n", encoding="utf-8")
        self.assertEqual(set(self.status()["invalidated_reviews"]),
                         {"scope", "citations", "blind_questions"})
        self.call("run", "resume", "--workspace", self.workspace)
        self.assertNotEqual(self.status()["status"], "complete-within-scope")
        self.assertTrue(all(review["status"] == "pending"
                            for review in self.status()["reviews"].values()))

    def test_review_only_failure_reopens_a_completed_run(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope")
        self.update({"reviews": {"citations": {
            "status": "failed", "reviewer": "test-reviewer", "method": "self",
            "details": "A later review found a material problem; synthetic test only.",
        }}})
        self.assertNotEqual(self.status()["status"], "complete-within-scope")
        self.assertEqual(self.status()["reviews"]["citations"]["status"], "failed")

    def test_blocking_gap_prevents_complete_even_if_disclosed(self):
        self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        report = self.prepare_finished_run(ref)
        self.update({"gaps": [{"id": "missing-core", "description": "The decisive source is inaccessible.",
                               "blocking": True, "resolved": False}]})
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)

    def test_report_dangling_marker_is_rejected(self):
        source = self.ingest(required=True)
        ref = self.find_ref("ribbon", "blue ribbon")
        missing = source["refs"][0].rsplit(":", 1)[0] + ":p999999"
        report = self.prepare_finished_run(
            ref, report_body=f"This statement has a dangling citation. [[{missing}]]")
        self.call("verify", "--workspace", self.workspace, "--report", report, success=False)

    def test_numeric_overlap_does_not_claim_semantic_verification(self):
        self.ingest("measurement.txt", required=True)
        ref = self.find_ref("reduced", "reduced water loss by 42 percent")
        self.commit("wrong-direction", ref,
                    body="The pump increased water loss by 42 percent.")
        report = self.prepare_finished_run(
            ref, report_body=f"The pump increased water loss by 42 percent. [[{ref}]]")
        result = self.call("verify", "--workspace", self.workspace, "--report", report)
        self.assertTrue(result["passed"])
        self.assertEqual(result["verification_scope"], "structural-only")
        self.assertEqual(result["semantic_support"], "requires-source-based-review")
        # Semantic rejection belongs to the behavioral reviewer, not number matching.
        self.update({"reviews": {"citations": {
            "status": "failed", "reviewer": "test-semantic-reviewer", "method": "self",
            "details": "The source says reduced; the report says increased. Synthetic review stub only.",
        }}})
        self.call("run", "finish", "--workspace", self.workspace, "--report", report,
                  "--outcome", "complete-within-scope", success=False)


if __name__ == "__main__":
    unittest.main()
