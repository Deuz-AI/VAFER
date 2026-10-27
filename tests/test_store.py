"""Failure-injection checks for durable research state, without network access."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "ultra-deep-research" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from vafer import extract, store


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vafer-recovery-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = store.Workspace(self.root / "workspace")
        self.workspace.init("Study the supplied short source.")
        self.source = self.root / "source.txt"
        self.source.write_text("The copper cup has a crescent-shaped dent.\n", encoding="utf-8")

    def ingest(self):
        return self.workspace.ingest(self.source, completeness="full", required=True)

    def test_changed_extractor_creates_revision_for_identical_bytes(self):
        first = self.ingest()
        original = extract.extract_file

        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            result["extractor_version"] += "-updated"
            return result

        with patch.object(extract, "extract_file", side_effect=changed):
            second = self.ingest()
            repeated = self.ingest()
        self.assertNotEqual(first["revision"], second["revision"])
        self.assertTrue(self.workspace.read(first["refs"][0])["historical"])
        self.assertTrue(repeated["deduplicated"])
        self.assertEqual(second["revision"], repeated["revision"])

    def interrupted_ingest(self):
        original = store.atomic_json

        def write(path, value):
            if path.name == "sources.json":
                raise OSError("Simulated interruption after revision staging")
            original(path, value)

        with patch.object(store, "atomic_json", side_effect=write):
            with self.assertRaises(OSError):
                self.ingest()
        return self.ingest()

    def test_recovers_initial_revision_after_catalog_write_interruption(self):
        recovered = self.interrupted_ingest()
        self.assertEqual(self.workspace.catalog()[recovered["source_id"]], recovered["revision"])
        self.assertIn("crescent-shaped", self.workspace.read(recovered["refs"][0])["text"])

    def test_recovers_updated_revision_without_rolling_back_history(self):
        original = self.ingest()
        self.source.write_text("The repaired cup has a circular patch.\n", encoding="utf-8")
        recovered = self.interrupted_ingest()
        self.assertNotEqual(original["revision"], recovered["revision"])
        self.assertTrue(self.workspace.read(original["refs"][0])["historical"])
        self.source.write_text("The copper cup has a crescent-shaped dent.\n", encoding="utf-8")
        with self.assertRaises(store.ResearchError) as caught:
            self.ingest()
        self.assertEqual(caught.exception.code, "HISTORICAL_IMPORT")

    def test_interrupted_note_commit_invalidates_review_of_earlier_state(self):
        ref = self.ingest()["refs"][0]
        report = self.workspace.path("report.md")
        report.write_text(f"The cup has a dent. [[{ref}]]\n", encoding="utf-8")
        self.workspace.update({"report": "report.md", "reviews": {
            "scope": {"status": "passed", "reviewer": "test-stub", "method": "self", "details": "Synthetic test only."}
        }})
        note = {"id": "cup", "title": "Cup", "kind": "fact", "body": "The dent is crescent-shaped.",
                "evidence": [{"ref": ref}]}
        with patch.object(self.workspace, "save_manifest", side_effect=OSError("Simulated interruption")):
            with self.assertRaises(OSError):
                self.workspace.commit(note)
        self.assertIn("scope", self.workspace.status()["invalidated_reviews"])
        resumed = self.workspace.resume()
        self.assertEqual(resumed["reviews"]["scope"]["status"], "pending")
        self.assertIn("cup", self.workspace.notes())

    def test_cache_is_rebuildable_without_source_loss(self):
        self.ingest()
        first = self.workspace.search("crescent")
        self.workspace.path(".cache", "search.sqlite").unlink()
        rebuilt = self.workspace.search("crescent")
        self.assertEqual(first["hits"], rebuilt["hits"])

    def test_os_lock_excludes_another_writer_and_releases_after_exit(self):
        command = [sys.executable, str(SCRIPTS / "research.py"), "run", "resume",
                   "--workspace", str(self.workspace.root)]
        with store.workspace_lock(self.workspace.root):
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "WORKSPACE_BUSY")
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_search_waits_for_a_short_cache_write_lock(self):
        self.ingest()
        command = [sys.executable, str(SCRIPTS / "research.py"), "search",
                   "--workspace", str(self.workspace.root), "--query", "crescent"]
        with store.workspace_lock(self.workspace.root):
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding="utf-8")
            time.sleep(0.3)
        output, errors = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 0, output + errors)
        self.assertTrue(json.loads(output)["data"]["hits"])


if __name__ == "__main__":
    unittest.main()
