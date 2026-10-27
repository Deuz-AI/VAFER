"""Retrieval behavior and incremental-cache regressions, using local fixtures."""

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "ultra-deep-research" / "scripts"))

from vafer import search as retrieval, store


class SearchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vafer-search-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = store.Workspace(self.root / "workspace")
        self.workspace.init("Compare harbor and inland settlement histories.")
        self.first = self.ingest("harbor", "The old harbor expanded in 1898. Copper ships arrived.")
        self.second = self.ingest("inland", "The old road reached the harbor in 1929. Copper markets grew.")
        self.note("harbor-note", "Copper ships used the old harbor.", self.first["refs"][0])
        self.note("inland-note", "Copper markets followed the inland road.", self.second["refs"][0])

    def ingest(self, sid, text):
        path = self.root / f"{sid}.txt"
        path.write_text(text, encoding="utf-8")
        return self.workspace.ingest(path, source_id=sid, title=sid, completeness="full")

    def note(self, nid, body, ref):
        return self.workspace.commit({"id": nid, "title": nid, "kind": "fact", "body": body,
                                      "evidence": [{"ref": ref}]})

    def search(self, query, **kwargs):
        return retrieval.search(self.workspace, query, **kwargs)

    def test_phrase_all_and_default_any_retrieve_different_evidence(self):
        self.assertEqual(len(self.search("harbor 1898")["hits"]), 2)
        self.assertEqual([r["ref"] for r in self.search("harbor 1898", mode="all")["hits"]], self.first["refs"])
        self.assertEqual([r["ref"] for r in self.search('"old harbor"')["hits"]], self.first["refs"])
        self.assertFalse(self.search('"old harbor" 1929', mode="all")["hits"])
        self.assertEqual(len(self.search('"old harbor" 1929')["hits"]), 2)

    def test_filters_apply_before_limit_and_restrict_note_evidence(self):
        result = self.search("Copper", source_id="inland", limit=1)
        self.assertEqual([r["ref"] for r in result["hits"]], self.second["refs"])
        self.assertEqual([r["id"] for r in result["note_hits"]], ["inland-note"])
        self.assertFalse(self.search("Copper", kind="notes")["hits"])
        self.assertFalse(self.search("Copper", kind="sources")["note_hits"])

    def test_note_change_does_not_read_unchanged_source_passages(self):
        self.search("Copper")
        self.note("harbor-note", "Copper ships became steamships.", self.first["refs"][0])
        with patch.object(self.workspace, "passages", side_effect=AssertionError("Unchanged source reread")):
            result = self.search("steamships")
        self.assertEqual(result["index_updates"]["sources_updated"], 0)
        self.assertEqual(result["index_updates"]["notes_updated"], 1)
        self.assertEqual([n["id"] for n in result["note_hits"]], ["harbor-note"])
        self.assertFalse(self.search("steamships")["index_updates"]["rebuilt"])

    def test_source_revision_removes_old_passages_and_stale_notes(self):
        self.search("Copper")
        updated = self.ingest("harbor", "Electric ferries now cross the bay.")
        result = self.search("Copper", source_id="harbor")
        self.assertFalse(result["hits"])
        self.assertFalse(result["note_hits"])
        self.assertEqual(result["index_updates"]["sources_updated"], 1)
        self.assertEqual(result["index_updates"]["notes_removed"], 1)
        self.assertEqual([r["ref"] for r in self.search("ferries")["hits"]], updated["refs"])

    def test_old_cache_migrates_without_changing_sources(self):
        cache = self.workspace.path(".cache", "search.sqlite")
        cache.parent.mkdir()
        with sqlite3.connect(cache) as conn:
            conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT)")
            conn.execute("INSERT INTO metadata VALUES ('signature','legacy')")
            conn.execute("CREATE TABLE plain_passages (ref TEXT,title TEXT,text TEXT)")
        conn.close()
        result = self.search('"old harbor"')
        self.assertTrue(result["index_updates"]["rebuilt"])
        self.assertEqual([r["ref"] for r in result["hits"]], self.first["refs"])
        self.assertIn("old harbor", self.workspace.read(self.first["refs"][0])["text"])

    def test_fallback_preserves_phrase_all_and_filter_semantics(self):
        self.search("Copper")
        with patch.object(retrieval, "_supports_fts", return_value=False):
            result = self.search('"old harbor" 1898', mode="all", source_id="harbor")
            self.assertEqual(result["engine"], "literal-fallback")
            self.assertEqual([r["ref"] for r in result["hits"]], self.first["refs"])
            self.assertFalse(self.search('"old harbor" 1929', mode="all")["hits"])
            self.assertFalse(self.search("oppe")["hits"])
            self.assertEqual([n["id"] for n in self.search("Copper", source_id="inland")["note_hits"]], ["inland-note"])
        self.assertEqual(len(self.search("Copper")["hits"]), 2)

    def test_failed_update_rolls_back_index_and_revision_bookkeeping(self):
        self.search("Copper")
        self.ingest("harbor", "Electric ferries now cross the bay.")
        original = self.workspace.passages
        with patch.object(self.workspace, "passages", side_effect=OSError("Simulated read interruption")):
            with self.assertRaises(OSError):
                self.search("Electric")
        with patch.object(self.workspace, "passages", wraps=original) as read:
            result = self.search("Electric")
        self.assertEqual(read.call_count, 1)
        self.assertEqual(len(result["hits"]), 1)

    def test_invalid_queries_are_explicit(self):
        for query in ('"old harbor', "---"):
            with self.assertRaises(store.ResearchError) as caught:
                self.search(query)
            self.assertEqual(caught.exception.code, "INVALID_QUERY")


if __name__ == "__main__":
    unittest.main()
