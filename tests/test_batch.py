"""Public checkpoint recovery and reusable-reference contracts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "skills/ultra-deep-research/scripts/research.py"


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / "study"
        self.source = self.root / "source.txt"
        self.source.write_text("The first trial measured 12 units.\n\nThe second trial measured 7 units.", encoding="utf-8")
        self.call("run", "init", "--question", "Explain measurement changes.")

    def call(self, *args, success=True):
        result = subprocess.run([sys.executable, str(CLI), *args, "--workspace", str(self.work)],
                                capture_output=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"), timeout=30)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0 if success else 1, payload)
        return payload.get("data") if success else payload["error"]

    def batch(self, operations, success=True):
        path = self.root / "checkpoint.json"
        path.write_text(json.dumps(operations), encoding="utf-8")
        return self.call("batch", "--file", str(path), success=success)

    def ingestion(self):
        return {"op": "ingest", "as": "trial", "file": str(self.source), "completeness": "full"}

    def test_checkpoint_ingests_reads_and_commits_returned_reference(self):
        result = self.batch([self.ingestion(), {"op": "read-many", "refs": ["$trial:p000001"]},
                             {"op": "commit", "value": {"id": "measurement", "title": "First trial",
                              "kind": "fact", "body": "First trial: 12 units [[$trial:p000001]]",
                              "evidence": [{"ref": "$trial:p000001", "quote": "12 units"}]}}])
        self.assertEqual(len(result["operations"]), 3)
        self.assertIn("12 units", result["operations"][1]["data"]["passages"][0]["text"])
        note = json.loads((self.work / "notes/measurement.json").read_text(encoding="utf-8"))
        self.assertEqual(note["evidence"][0]["ref"], result["aliases"]["trial"]["p000001"])
        self.assertNotIn("$trial", note["body"])
        self.assertTrue(all(row["elapsed_ms"] >= 0 for row in result["operations"]))

    def test_failure_preserves_prefix_and_skips_suffix(self):
        error = self.batch([self.ingestion(), {"op": "read-many", "refs": ["$trial:p999999"]},
                            {"op": "commit", "value": {"id": "later"}}], success=False)
        self.assertEqual(error["code"], "BATCH_STOPPED")
        self.assertEqual(error["details"]["failed_index"], 1)
        self.assertEqual(error["details"]["cause"], "INVALID_ALIAS")
        self.assertEqual(len(error["details"]["completed"]), 1)
        self.assertFalse((self.work / "notes/later.json").exists())
        self.assertEqual(len(json.loads((self.work / "sources.json").read_text())), 1)

    def test_bad_operation_preflight_does_not_mutate(self):
        error = self.batch([self.ingestion(), {"op": "delete"}], success=False)
        self.assertEqual(error["code"], "INVALID_BATCH")
        self.assertEqual(json.loads((self.work / "sources.json").read_text()), {})

    def test_duplicate_alias_rejected_before_mutation(self):
        error = self.batch([self.ingestion(), self.ingestion()], success=False)
        self.assertEqual(error["code"], "INVALID_BATCH")
        self.assertEqual(json.loads((self.work / "sources.json").read_text()), {})


if __name__ == "__main__":
    unittest.main()
