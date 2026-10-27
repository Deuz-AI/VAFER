"""Versioned source records, contextual notes, and resumable research workspaces.

The records are authoritative; SQLite is a disposable search index. Verification
checks integrity and recorded review results, never the truth of natural language.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import __version__

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
REF_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_-]{0,79})@([a-f0-9]{16}):(p\d{6})$")
CITATION_RE = re.compile(r"\[\[([^\[\]\n]+)\]\]")
REVIEW_NAMES = ("scope", "citations", "blind_questions")
QUESTION_FIELDS = {"parent_id", "origin", "context_read", "answer", "answer_note", "support", "report_anchor"}
MAX_SOURCE_BYTES = 100 * 1024 * 1024


class ResearchError(ValueError):
    """An actionable error safe to return through the command-line interface."""

    def __init__(self, code: str, message: str, details=None):
        super().__init__(message)
        self.code = code
        self.details = details


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def identifier(value: str, kind: str = "identifier") -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ResearchError("INVALID_ID", f"Invalid {kind}: use letters, digits, '-' or '_', up to 80 characters.")
    return value


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchError("INVALID_RECORD", f"Cannot read JSON record {path.name}: {exc}") from exc


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def atomic_json(path: Path, value) -> None:
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def contained(root: Path, path: Path) -> Path:
    target = path.resolve()
    if not target.is_relative_to(root.resolve()):
        raise ResearchError("OUTSIDE_WORKSPACE", "The path must stay inside the research workspace.")
    return target


@contextmanager
def workspace_lock(root: Path, timeout: float = 0):
    """OS locks are released on process death, allowing interrupted runs to resume."""
    root.mkdir(parents=True, exist_ok=True)
    path = contained(root, root / ".write.lock")
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise ResearchError("WORKSPACE_BUSY", "Another writer is using this workspace; retry after it finishes.") from exc
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class Workspace:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    def path(self, *parts: str) -> Path:
        return contained(self.root, self.root.joinpath(*parts))

    def manifest(self) -> dict:
        path = self.path("run.json")
        if not path.exists():
            raise ResearchError("NOT_INITIALIZED", "Initialize this workspace with 'run init' first.")
        value = read_json(path)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ResearchError("SCHEMA_VERSION", "Unsupported workspace schema; expected version 1.")
        return value

    def save_manifest(self, value: dict) -> None:
        value["updated_at"] = now()
        atomic_json(self.path("run.json"), value)

    def catalog(self) -> dict:
        value = read_json(self.path("sources.json"))
        if not isinstance(value, dict):
            raise ResearchError("INVALID_RECORD", "sources.json must be an object.")
        for sid, revision in value.items():
            identifier(sid, "source ID")
            if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{16}", revision):
                raise ResearchError("INVALID_RECORD", "Invalid source revision in catalog.")
        return value

    def init(self, question: str, mode: str = "study") -> dict:
        if not question.strip():
            raise ResearchError("EMPTY_QUESTION", "A research question is required.")
        if self.path("run.json").exists():
            existing = self.manifest()
            if existing["question"] != question or existing["mode"] != mode:
                raise ResearchError("ALREADY_INITIALIZED", "Workspace exists; use run update to change its scope.")
            return existing
        # Refuse to adopt half-created or unrelated user data silently.
        for name in ("sources.json", "sources", "notes"):
            if self.path(name).exists():
                raise ResearchError("WORKSPACE_CONFLICT", f"Existing {name} requires inspection before initialization.")
        manifest = {
            "schema_version": 1, "tool_version": __version__, "question": question,
            "mode": mode, "status": "running", "created_at": now(),
            "tasks": [], "coverage": [], "gaps": [], "required_sources": [],
            "reviews": {key: {"status": "pending"} for key in REVIEW_NAMES},
            "report": None,
        }
        atomic_json(self.path("sources.json"), {})
        self.path("sources").mkdir(exist_ok=True)
        self.path("notes").mkdir(exist_ok=True)
        self.save_manifest(manifest)
        return manifest

    def revision_dir(self, sid: str, revision: str) -> Path:
        identifier(sid, "source ID")
        if not re.fullmatch(r"[a-f0-9]{16}", revision):
            raise ResearchError("INVALID_REF", "Invalid source revision.")
        return self.path("sources", sid, "revisions", revision)

    def metadata(self, sid: str, revision: str) -> dict:
        return read_json(contained(self.root, self.revision_dir(sid, revision) / "metadata.json"))

    def passages(self, sid: str, revision: str) -> list[dict]:
        path = contained(self.root, self.revision_dir(sid, revision) / "passages.jsonl")
        try:
            return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ResearchError("INVALID_RECORD", f"Cannot read source passages: {exc}") from exc

    def read(self, ref: str) -> dict:
        match = REF_RE.fullmatch(ref)
        if not match:
            raise ResearchError("INVALID_REF", f"Invalid passage reference: {ref}")
        sid, revision, pid = match.groups()
        if not (self.revision_dir(sid, revision) / "metadata.json").is_file():
            raise ResearchError("MISSING_REF", f"Unknown source revision: {ref}")
        source = self.metadata(sid, revision)
        for passage in self.passages(sid, revision):
            if passage["id"] == pid:
                return {"ref": ref, "text": passage["text"], "locator": passage["locator"],
                        "source": source, "historical": self.catalog().get(sid) != revision,
                        "untrusted": True,
                        "content_role": "source_data_not_instructions"}
        raise ResearchError("MISSING_REF", f"Unknown source passage: {ref}")

    def assert_current_ref(self, ref: str) -> dict:
        value = self.read(ref)
        if value["historical"]:
            raise ResearchError("STALE_REF", f"Reference uses a superseded source revision: {ref}")
        return value

    def read_many(self, refs: list[str]) -> dict:
        """Read bounded evidence batches with each source revision loaded once."""
        if not isinstance(refs, list) or not 1 <= len(refs) <= 100 or any(not isinstance(ref, str) for ref in refs):
            raise ResearchError("INVALID_REF", "Supply an array of 1 to 100 passage references.")
        catalog, sources, indexed, results = self.catalog(), {}, {}, []
        for ref in refs:
            match = REF_RE.fullmatch(ref)
            if not match:
                raise ResearchError("INVALID_REF", f"Invalid passage reference: {ref}")
            sid, rev, pid = match.groups()
            key = f"{sid}@{rev}"
            if key not in sources:
                if not (self.revision_dir(sid, rev) / "metadata.json").is_file():
                    raise ResearchError("MISSING_REF", f"Unknown source revision: {ref}")
                sources[key] = self.metadata(sid, rev)
                indexed[key] = {p["id"]: p for p in self.passages(sid, rev)}
            passage = indexed[key].get(pid)
            if passage is None:
                raise ResearchError("MISSING_REF", f"Unknown source passage: {ref}")
            results.append({"ref": ref, "text": passage["text"], "locator": passage["locator"],
                            "source_key": key, "historical": catalog.get(sid) != rev,
                            "untrusted": True, "content_role": "source_data_not_instructions"})
        return {"passages": results, "sources": sources, "untrusted": True}

    def notes(self) -> dict[str, dict]:
        result = {}
        for path in sorted(self.path("notes").glob("*.json")):
            contained(self.root, path)
            note = read_json(path)
            if not isinstance(note, dict) or note.get("id") != path.stem:
                raise ResearchError("INVALID_RECORD", f"Invalid note record: {path.name}")
            identifier(note["id"], "note ID")
            result[note["id"]] = note
        return result

    def stale_notes(self) -> list[str]:
        catalog, notes = self.catalog(), self.notes()
        stale = set()
        for nid, note in notes.items():
            if note.get("status") == "stale":
                stale.add(nid)
            for evidence in note.get("evidence", []):
                match = REF_RE.fullmatch(evidence.get("ref", ""))
                if not match or catalog.get(match[1]) != match[2]:
                    stale.add(nid)
            for dependency in note.get("depends_on", []):
                parent = notes.get(dependency)
                if not parent or note.get("dependency_hashes", {}).get(dependency) != parent.get("content_hash"):
                    stale.add(nid)
        changed = True
        while changed:
            changed = False
            for nid, note in notes.items():
                if nid not in stale and any(dep in stale for dep in note.get("depends_on", [])):
                    stale.add(nid)
                    changed = True
        return sorted(stale)

    def mark_stale(self) -> list[str]:
        stale = self.stale_notes()
        for nid in stale:
            note = read_json(self.path("notes", f"{nid}.json"))
            if note.get("status") != "stale":
                note["status"] = "stale"
                atomic_json(self.path("notes", f"{nid}.json"), note)
                self.write_note_view(note)
        return stale

    @staticmethod
    def reset_reviews(manifest: dict) -> None:
        manifest["reviews"] = {key: {"status": "pending"} for key in REVIEW_NAMES}
        manifest["status"] = "running"
        manifest.pop("verification", None)

    def ingest(self, file: str | Path, *, source_url: str | None = None, title: str | None = None,
               edition: str | None = None, capture_kind: str = "original-file",
               completeness: str = "unknown", source_id: str | None = None,
               required: bool = False) -> dict:
        from .extract import ExtractionError, extract_file
        manifest = self.manifest()
        path = Path(file).expanduser().resolve()
        if not path.is_file():
            raise ResearchError("SOURCE_MISSING", "The supplied source file does not exist.")
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise ResearchError("SOURCE_TOO_LARGE", "Source files must be at most 100 MiB; split larger sources explicitly.")
        raw = path.read_bytes()
        try:
            extracted = extract_file(path, capture_kind=capture_kind, completeness=completeness)
        except ExtractionError as exc:
            raise ResearchError("EXTRACTION_FAILED", str(exc)) from exc
        if path.read_bytes() != raw:
            raise ResearchError("SOURCE_CHANGED", "The source changed during extraction; retry with a stable file.")
        title = title or path.name
        identity = {"origin": source_url or str(path), "edition": edition or ""}
        sid = identifier(source_id or "s" + digest(identity)[:16], "source ID")
        provenance = {"raw_sha256": digest(raw), "extraction_sha256": digest(extracted), "capture_kind": capture_kind,
                      "declared_completeness": completeness, "title": title, **identity}
        revision_hash = digest(provenance)
        revision = revision_hash[:16]
        target = self.revision_dir(sid, revision)
        catalog = self.catalog()
        if (target / "metadata.json").exists():
            meta = self.metadata(sid, revision)
            if meta.get("revision_sha256") != revision_hash:
                raise ResearchError("HASH_COLLISION", "Source revision collision; source was not changed.")
            if catalog.get(sid) != revision:
                if meta.get("previous_revision") != catalog.get(sid):
                    raise ResearchError("HISTORICAL_IMPORT", "This content is an older revision. Read it by reference or import it as a separate source.")
                # Recover a fully staged revision interrupted before catalog commit.
                catalog[sid] = revision
                atomic_json(self.path("sources.json"), catalog)
                self.mark_stale()
                self.reset_reviews(manifest)
            deduplicated = True
        else:
            payload = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in extracted["passages"])
            original_name = "original" + (path.suffix.lower() or ".txt")
            meta = {"source_id": sid, "revision": revision, "revision_sha256": revision_hash,
                    "previous_revision": catalog.get(sid),
                    "sha256": digest(raw), "extraction_sha256": digest(extracted),
                    "title": title, "url": source_url, "original_path": str(path),
                    "edition": edition, "captured_at": now(), "capture_kind": capture_kind,
                    "declared_completeness": completeness, "completeness": extracted["completeness"],
                    "format": extracted["format"], "extractor": extracted["extractor"],
                    "extractor_version": extracted["extractor_version"], "warnings": extracted["warnings"],
                    "passage_count": len(extracted["passages"]), "original_file": original_name,
                    "passages_sha256": digest(payload.encode("utf-8"))}
            if "capture_quality" in extracted:
                meta["capture_quality"] = extracted["capture_quality"]
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = Path(tempfile.mkdtemp(prefix=".ingest-", dir=target.parent))
            try:
                (temp / original_name).write_bytes(raw)
                atomic_text(temp / "passages.jsonl", payload)
                atomic_json(temp / "metadata.json", meta)
                if target.exists():
                    raise ResearchError("REVISION_CONFLICT", "An incomplete revision directory requires inspection.")
                os.replace(temp, target)
            finally:
                if temp.exists():
                    # Only files created above in this verified temporary directory.
                    for child in temp.iterdir():
                        child.unlink()
                    temp.rmdir()
            catalog[sid] = revision
            atomic_json(self.path("sources.json"), catalog)
            self.mark_stale()
            self.reset_reviews(manifest)
            deduplicated = False
        if required and sid not in manifest["required_sources"]:
            manifest["required_sources"].append(sid)
            self.reset_reviews(manifest)
        self.save_manifest(manifest)
        return {"source_id": sid, "revision": revision,
                "refs": [f"{sid}@{revision}:{p['id']}" for p in self.passages(sid, revision)],
                "completeness": meta["completeness"], "warnings": meta["warnings"],
                "capture_quality": meta.get("capture_quality", {"status": "unassessed", "reasons": []}),
                "deduplicated": deduplicated}

    def write_note_view(self, note: dict) -> None:
        lines = [f"# {note['title']}", "", f"Kind: {note['kind']} | Status: {note['status']}", "",
                 note["body"], "", "## Evidence", ""]
        for entry in note["evidence"]:
            lines.append(f"- [[{entry['ref']}]]")
            if entry.get("quote"):
                lines.append("  " + entry["quote"].replace("\n", "\n  "))
        atomic_text(self.path("notes", f"{note['id']}.md"), "\n".join(lines) + "\n")

    def commit(self, value: dict) -> dict:
        manifest = self.manifest()
        if not isinstance(value, dict):
            raise ResearchError("INVALID_NOTE", "A note must be a JSON object.")
        allowed = {"id", "title", "kind", "body", "evidence", "depends_on", "context", "source_family"}
        if set(value) - allowed:
            raise ResearchError("INVALID_NOTE", "Unknown note fields: " + ", ".join(sorted(set(value) - allowed)))
        nid = identifier(value.get("id", ""), "note ID")
        for key in ("title", "body"):
            if not isinstance(value.get(key), str) or not value[key].strip():
                raise ResearchError("INVALID_NOTE", f"Note {key} must be nonempty text.")
        if value.get("kind") not in {"fact", "interpretation", "synthesis", "question"}:
            raise ResearchError("INVALID_NOTE", "Note kind must be fact, interpretation, synthesis, or question.")
        evidence = value.get("evidence", [])
        if not isinstance(evidence, list) or (not evidence and value["kind"] != "question"):
            raise ResearchError("MISSING_EVIDENCE", "Non-question notes require at least one source passage.")
        for entry in evidence:
            if not isinstance(entry, dict) or set(entry) - {"ref", "quote"} or not isinstance(entry.get("ref"), str):
                raise ResearchError("INVALID_EVIDENCE", "Evidence entries require ref and optional quote.")
            passage = self.assert_current_ref(entry["ref"])
            if "quote" in entry:
                if not isinstance(entry["quote"], str) or not entry["quote"].strip():
                    raise ResearchError("INVALID_QUOTE", "A supplied quote must be nonempty text.")
                norm = lambda text: " ".join(unicodedata.normalize("NFC", text).split())
                if norm(entry["quote"]) not in norm(passage["text"]):
                    raise ResearchError("QUOTE_MISMATCH", f"Quote is not present in {entry['ref']}.")
        inline_refs = CITATION_RE.findall(value["body"])
        if value["body"].count("[[") != len(inline_refs) or value["body"].count("]]") != len(inline_refs):
            raise ResearchError("INVALID_REF", "Malformed note citation markers.")
        for ref in inline_refs:
            self.assert_current_ref(ref)
            if ref not in {entry["ref"] for entry in evidence}:
                raise ResearchError("MISSING_EVIDENCE", "Every inline note citation must also appear in evidence.")
        dependencies = value.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            raise ResearchError("INVALID_DEPENDENCY", "depends_on must be a list of note IDs.")
        notes = self.notes()
        stale = set(self.stale_notes())
        for dep in dependencies:
            identifier(dep, "dependency")
            if dep not in notes or dep in stale:
                raise ResearchError("INVALID_DEPENDENCY", f"Dependency {dep} is missing or stale.")
        graph = {key: item.get("depends_on", []) for key, item in notes.items()}
        graph[nid] = dependencies
        def visit(key, trail):
            if key in trail:
                raise ResearchError("DEPENDENCY_CYCLE", "Note dependencies must not contain cycles.")
            for dep in graph.get(key, []):
                visit(dep, trail | {key})
        visit(nid, set())
        note = {**value, "evidence": evidence, "depends_on": dependencies,
                "dependency_hashes": {dep: notes[dep]["content_hash"] for dep in dependencies}}
        note["content_hash"] = digest(note)
        previous = notes.get(nid)
        note["status"] = "current"
        note["updated_at"] = now()
        if previous and previous.get("content_hash") != note["content_hash"]:
            history = self.path("notes", "history", nid, f"{previous['content_hash']}.json")
            if not history.exists():
                atomic_json(history, previous)
        atomic_json(self.path("notes", f"{nid}.json"), note)
        self.write_note_view(note)
        invalidated = self.mark_stale()
        if not previous or previous.get("content_hash") != note["content_hash"]:
            self.reset_reviews(manifest)
            self.save_manifest(manifest)
        return {"id": nid, "status": "current", "content_hash": note["content_hash"], "invalidated_notes": invalidated}

    def task_invalidations(self, manifest: dict) -> list[str]:
        stale = set(self.stale_notes())
        notes = self.notes()
        bad = []
        for task in manifest["tasks"]:
            for item in task.get("inputs", []):
                if "@" in item:
                    try:
                        self.assert_current_ref(item)
                    except ResearchError:
                        bad.append(task["id"])
                        break
                elif item not in notes or item in stale:
                    bad.append(task["id"])
                    break
                elif task.get("input_hashes", {}).get(item) != notes[item]["content_hash"]:
                    bad.append(task["id"])
                    break
        return sorted(set(bad))

    def research_hash(self, manifest: dict) -> str:
        state = {key: manifest[key] for key in ("question", "mode", "tasks", "coverage", "gaps", "required_sources")}
        for key in ("reading_scope", "map_audits"):
            if key in manifest:
                state[key] = manifest[key]
        state["sources"] = self.catalog()
        state["notes"] = {nid: {"hash": note["content_hash"], "status": note["status"]}
                          for nid, note in self.notes().items()}
        return digest(state)

    def coverage_evidence(self, row: dict) -> list[str]:
        """Reuse a note's evidence without requiring a second copy in the map."""
        if row.get("answer_note"):
            note = self.notes().get(row["answer_note"], {})
            return list(dict.fromkeys(row.get("evidence", []) + [e["ref"] for e in note.get("evidence", [])]))
        return row.get("evidence", [])

    def question_progress(self, manifest: dict, report: str | Path | None = None) -> list[dict]:
        path = self.report_path(report or manifest.get("report"))
        text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
        notes, stale = self.notes(), set(self.stale_notes())
        progress = []
        for row in manifest["coverage"]:
            if not QUESTION_FIELDS.intersection(row) or row["status"] == "excluded":
                continue
            refs = self.coverage_evidence(row)
            current = bool(refs)
            for ref in refs:
                try:
                    self.assert_current_ref(ref)
                except ResearchError:
                    current = False
            note_id = row.get("answer_note")
            answer = bool(row.get("answer")) or (note_id in notes and note_id not in stale and
                row.get("answer_note_hash") == notes[note_id].get("content_hash"))
            supported = current and row.get("context_read") is True and answer and row.get("support", {}).get("judgment") == "supported"
            delivered = supported and bool(row.get("report_anchor")) and row["report_anchor"] in text
            progress.append({"id": row["id"], "evidence_found": current,
                             "context_read": row.get("context_read") is True,
                             "answer_supported": bool(supported), "reported": bool(delivered),
                             "support_assessment": "researcher-declared; not machine-verified"})
        states = {p["id"]: p for p in progress}
        rows = {r["id"]: r for r in manifest["coverage"]}
        for row in manifest["coverage"]:
            if row.get("parent_id") in states and row.get("required"):
                child_complete = row["status"] == "covered" and (states.get(row["id"], {}).get("reported", bool(self.coverage_evidence(row))))
                if not child_complete:
                    parent = row["parent_id"]
                    visited = set()
                    while parent in states and parent not in visited:
                        visited.add(parent)
                        states[parent]["reported"] = False
                        states[parent].setdefault("unanswered_children", []).append(row["id"])
                        parent = rows[parent].get("parent_id")
        return progress

    def audit_errors(self, manifest: dict) -> list[str]:
        rows = {r["id"]: r for r in manifest["coverage"]}
        errors = []
        for audit in manifest.get("map_audits", []):
            if digest(audit["candidates"]) != audit.get("candidates_sha256"):
                errors.append(audit["id"] + ": candidate seal changed")
            if not audit.get("decisions"):
                errors.append(audit["id"] + ": compare sealed candidates with the map")
            for decision in audit.get("decisions", []):
                if "coverage_id" in decision:
                    row = rows.get(decision["coverage_id"], {})
                    if row.get("question") != decision.get("mapped_question") or row.get("status") == "excluded":
                        errors.append(audit["id"] + ": mapped question changed or excluded")
        return errors

    def invalidated_reviews(self, manifest: dict) -> list[str]:
        path = self.report_path(manifest.get("report"))
        report_hash = digest(path.read_bytes()) if path.is_file() else None
        research_hash = self.research_hash(manifest)
        return [name for name, review in manifest["reviews"].items()
                if review.get("status") == "passed" and
                (report_hash is None or review.get("report_sha256") != report_hash or
                 review.get("research_sha256") != research_hash)]

    def status(self) -> dict:
        from .planning import agenda
        manifest = self.manifest()
        stale = self.stale_notes()
        tasks = self.task_invalidations(manifest)
        reviews = self.invalidated_reviews(manifest)
        coverage = []
        progress = self.question_progress(manifest)
        covered_ids = {r["id"] for r in manifest["coverage"] if r["status"] == "covered"}
        coverage.extend(p["id"] for p in progress if p["id"] in covered_ids and not p["reported"])
        for row in manifest["coverage"]:
            if row["status"] == "excluded":
                continue
            if row["status"] == "covered" and not self.coverage_evidence(row):
                coverage.append(row["id"])
                continue
            for ref in self.coverage_evidence(row):
                try:
                    self.assert_current_ref(ref)
                except ResearchError:
                    coverage.append(row["id"])
                    break
        capture_warnings = []
        for sid, rev in self.catalog().items():
            quality = self.metadata(sid, rev).get("capture_quality", {})
            if quality.get("status") in {"suspect", "empty"}:
                capture_warnings.append({"source_id": sid, "revision": rev, **quality})
        coverage = sorted(set(coverage))
        actions = agenda(manifest, tasks, coverage, progress)
        used_sources = {ref.split("@")[0] for row in manifest["coverage"] if row["status"] != "excluded"
                        for ref in self.coverage_evidence(row)} | set(manifest["required_sources"])
        for warning in capture_warnings:
            affected = [row for row in manifest["coverage"] if row["status"] != "excluded" and
                        any(ref.startswith(warning["source_id"] + "@") for ref in self.coverage_evidence(row))]
            assessed = bool(affected) and all(row.get("context_read") is True and
                       row.get("support", {}).get("judgment") == "supported" for row in affected)
            if warning["source_id"] in used_sources and not assessed:
                actions["next_actions"].append({"kind": "capture", "id": warning["source_id"], "priority": 1,
                    "action": "Inspect the missing source context; fetch its body, use an independent alternative, or narrow the dependent claim.",
                    "needs_planning": False, "task_ids": [], "reasons": warning.get("reasons", [])})
        for error in self.audit_errors(manifest):
            actions["next_actions"].append({"kind": "map-audit", "id": error.split(":")[0], "priority": 1,
                "action": error, "needs_planning": False, "task_ids": []})
        if progress and not manifest.get("map_audits"):
            actions["next_actions"].append({"kind": "map-audit", "id": "independent-candidates", "priority": 1,
                "action": "Derive missing-question candidates from independent source structure without using the current map or draft, then seal them before comparison.",
                "needs_planning": False, "task_ids": []})
        actions["next_actions"].sort(key=lambda item: (item["priority"], item["kind"], item["id"]))
        if manifest["status"] == "complete-within-scope" and (stale or tasks or reviews or coverage):
            manifest["status"] = "running"
        return {**manifest, "stale_notes": stale, "invalidated_tasks": tasks,
                "invalidated_reviews": reviews, "invalidated_coverage": coverage,
                "capture_warnings": capture_warnings, "question_progress": progress, **actions}

    def report_path(self, value: str | Path | None = None) -> Path:
        if value is None:
            value = self.manifest().get("report") or "report.md"
        path = Path(value)
        return contained(self.root, path if path.is_absolute() else self.root / path)

    def patch(self, patch: dict) -> dict:
        """Upsert only changed rows; omitted requirements and fields survive."""
        if not isinstance(patch, dict):
            raise ResearchError("INVALID_UPDATE", "A patch must be an object.")
        payload, manifest, changed_ids = copy.deepcopy(patch), self.manifest(), {}
        invalid_tasks = set(self.task_invalidations(manifest)) if "tasks" in payload else set()
        for collection in ("tasks", "coverage", "gaps"):
            if collection not in payload:
                continue
            if not isinstance(payload[collection], list):
                raise ResearchError("INVALID_UPDATE", f"{collection} must be an array.")
            rows = {r["id"]: copy.deepcopy(r) for r in manifest[collection]}
            seen = set()
            for change in payload[collection]:
                if not isinstance(change, dict):
                    raise ResearchError("INVALID_UPDATE", "Changed rows must be objects.")
                rid = identifier(change.get("id", ""))
                if rid in seen:
                    raise ResearchError("INVALID_UPDATE", f"Duplicate {collection} ID: {rid}")
                seen.add(rid)
                row = rows.get(rid, {})
                if collection == "tasks" and row and "status" not in change:
                    if rid in invalid_tasks or ("inputs" in change and change["inputs"] != row.get("inputs", [])):
                        row["status"] = "pending"
                if collection == "coverage" and row:
                    scope_changed = (("question" in change and change["question"] != row["question"]) or
                                     (row["required"] and change.get("required") is False))
                    if scope_changed and "scope_change_reason" not in change:
                        row.pop("scope_change_reason", None)
                    dependencies = {"evidence", "answer", "answer_note", "question"}
                    note_changed = bool(row.get("answer_note")) and row.get("answer_note_hash") != self.notes().get(row["answer_note"], {}).get("content_hash")
                    if note_changed or any(k in change and row.get(k) != change[k] for k in dependencies):
                        for key in ("context_read", "support", "report_anchor"):
                            if key not in change:
                                row.pop(key, None)
                        if "status" not in change:
                            row["status"] = "open"
                for key, value in change.items():
                    if value is None and key not in {"id", "question", "required", "status", "title", "description", "blocking", "resolved"}:
                        row.pop(key, None)
                    else:
                        row[key] = value
                rows[rid] = row
            changed_ids[collection] = seen
            for row in (rows[rid] for rid in seen):
                for generated in ("input_hashes", "answer_note_hash", "scope_history"):
                    row.pop(generated, None)
            payload[collection] = list(rows.values())
        return self.update(payload, _changed_ids=changed_ids)

    def audit_seal(self, payload: dict) -> dict:
        """Freeze source-derived candidates before a later map comparison."""
        if not isinstance(payload, dict) or set(payload) != {"id", "reviewer", "method", "candidates"}:
            raise ResearchError("INVALID_AUDIT", "Audit seal needs id, reviewer, method, candidates.")
        aid = identifier(payload["id"], "audit ID")
        if payload["method"] not in {"independent-agent", "human", "self"} or not isinstance(payload["reviewer"], str) or not payload["reviewer"].strip():
            raise ResearchError("INVALID_AUDIT", "Declare the reviewer and actual independent-agent/human/self method.")
        candidates = payload["candidates"]
        if not isinstance(candidates, list) or not candidates:
            raise ResearchError("INVALID_AUDIT", "Supply source-derived candidate questions before comparing the map.")
        seen = set()
        for candidate in candidates:
            if not isinstance(candidate, dict) or set(candidate) != {"id", "question", "source_url", "basis"}:
                raise ResearchError("INVALID_AUDIT", "Candidates need id, question, source_url and source-specific basis.")
            cid = identifier(candidate["id"])
            if cid in seen or any(not isinstance(candidate[k], str) or not candidate[k].strip() for k in ("question", "source_url", "basis")):
                raise ResearchError("INVALID_AUDIT", "Candidate IDs must be unique and source/question fields nonempty.")
            seen.add(cid)
        manifest = self.manifest()
        if any(a["id"] == aid for a in manifest.get("map_audits", [])):
            raise ResearchError("AUDIT_SEALED", "This audit is sealed; use a new ID for a genuinely new audit.")
        record = {**copy.deepcopy(payload), "candidates_sha256": digest(candidates), "sealed_at": now(),
                  "independence": "declared; context separation is not machine-verifiable"}
        manifest.setdefault("map_audits", []).append(record)
        self.reset_reviews(manifest)
        self.save_manifest(manifest)
        return record

    def audit_resolve(self, payload: dict) -> dict:
        if not isinstance(payload, dict) or set(payload) != {"id", "decisions"}:
            raise ResearchError("INVALID_AUDIT", "Audit resolution needs id and decisions.")
        manifest = self.manifest()
        audit = next((a for a in manifest.get("map_audits", []) if a["id"] == payload["id"]), None)
        if not audit:
            raise ResearchError("INVALID_AUDIT", "Seal candidates before comparing the map.")
        if digest(audit["candidates"]) != audit["candidates_sha256"]:
            raise ResearchError("INVALID_AUDIT", "Candidate seal changed.")
        decisions = copy.deepcopy(payload["decisions"])
        if not isinstance(decisions, list):
            raise ResearchError("INVALID_AUDIT", "Decisions must be an array.")
        rows, seen = {r["id"]: r for r in manifest["coverage"]}, set()
        for decision in decisions:
            if not isinstance(decision, dict) or set(decision) not in (
                    {"candidate_id", "coverage_id", "rationale"}, {"candidate_id", "exclusion_reason"}):
                raise ResearchError("INVALID_AUDIT", "Map candidate_id to coverage_id with comparison rationale, or give exclusion_reason.")
            cid = identifier(decision["candidate_id"])
            if cid in seen:
                raise ResearchError("INVALID_AUDIT", "Duplicate candidate decision.")
            seen.add(cid)
            reason = decision.get("rationale", decision.get("exclusion_reason"))
            if not isinstance(reason, str) or not reason.strip():
                raise ResearchError("INVALID_AUDIT", "Give the actual comparison or exclusion reason.")
            if "coverage_id" in decision:
                row = rows.get(decision["coverage_id"])
                if not row or row["status"] == "excluded":
                    raise ResearchError("INVALID_AUDIT", "Add the unanswered candidate to active coverage before resolving it.")
                decision["mapped_question"] = row["question"]
        if seen != {c["id"] for c in audit["candidates"]}:
            raise ResearchError("INVALID_AUDIT", "Every sealed candidate needs one decision; candidates cannot disappear.")
        if audit.get("decisions"):
            audit.setdefault("comparison_history", []).append({"decisions": audit["decisions"], "compared_at": audit["compared_at"]})
        audit["decisions"], audit["compared_at"] = decisions, now()
        self.reset_reviews(manifest)
        self.save_manifest(manifest)
        return audit

    def update(self, patch: dict, *, _changed_ids: dict | None = None) -> dict:
        manifest = self.manifest()
        before = {key: copy.deepcopy(manifest.get(key)) for key in
                  ("question", "mode", "tasks", "coverage", "gaps", "report", "reading_scope")}
        patch = copy.deepcopy(patch)
        allowed = {"question", "mode", "tasks", "coverage", "reviews", "gaps", "report", "reading_scope"}
        if not isinstance(patch, dict) or set(patch) - allowed:
            raise ResearchError("INVALID_UPDATE", "Update fields: question, mode, tasks, coverage, reviews, gaps, report, reading_scope.")
        if "question" in patch and (not isinstance(patch["question"], str) or not patch["question"].strip()):
            raise ResearchError("INVALID_UPDATE", "question must be nonempty text.")
        if "mode" in patch and patch["mode"] not in {"study", "followup"}:
            raise ResearchError("INVALID_UPDATE", "mode must be study or followup.")
        if "reading_scope" in patch:
            scope = patch["reading_scope"]
            if (not isinstance(scope, dict) or set(scope) != {"kind", "rationale"}
                    or scope["kind"] not in {"finite-work", "open-topic"}
                    or not isinstance(scope["rationale"], str) or not scope["rationale"].strip()):
                raise ResearchError("INVALID_UPDATE", "reading_scope requires kind finite-work/open-topic and a nonempty rationale.")
        for collection in ("tasks", "coverage", "gaps"):
            if collection not in patch:
                continue
            rows = patch[collection]
            if not isinstance(rows, list):
                raise ResearchError("INVALID_UPDATE", f"{collection} must be an array.")
            seen = set()
            for row in rows:
                if not isinstance(row, dict):
                    raise ResearchError("INVALID_UPDATE", f"{collection} entries must be objects.")
                rid = identifier(row.get("id", ""))
                if rid in seen:
                    raise ResearchError("INVALID_UPDATE", f"Duplicate {collection} ID: {rid}")
                seen.add(rid)
                if _changed_ids is not None and rid not in _changed_ids.get(collection, set()):
                    continue
                if collection == "tasks":
                    if set(row) - {"id", "title", "status", "inputs"}:
                        raise ResearchError("INVALID_UPDATE", "Task fields: id, title, status, inputs.")
                    if not isinstance(row.get("title"), str) or not row["title"].strip():
                        raise ResearchError("INVALID_UPDATE", "Tasks need a title.")
                    if row.get("status") not in {"pending", "running", "done", "failed"}:
                        raise ResearchError("INVALID_UPDATE", "Invalid task status.")
                    if not isinstance(row.get("inputs", []), list):
                        raise ResearchError("INVALID_UPDATE", "Task inputs must be an array.")
                    snapshots = {}
                    for item in row.get("inputs", []):
                        if not isinstance(item, str):
                            raise ResearchError("INVALID_UPDATE", "Task inputs must be reference strings or note IDs.")
                        if "@" in item:
                            self.assert_current_ref(item)
                        else:
                            identifier(item)
                            notes = self.notes()
                            if item not in notes or item in self.stale_notes():
                                raise ResearchError("INVALID_DEPENDENCY", f"Task input {item} is missing or stale.")
                            snapshots[item] = notes[item]["content_hash"]
                    row["input_hashes"] = snapshots
                elif collection == "coverage":
                    if set(row) - ({"id", "question", "required", "status", "evidence", "task_ids", "next_action", "blocked_reason",
                                    "exclusion_reason", "scope_change_reason"} | QUESTION_FIELDS):
                        raise ResearchError("INVALID_UPDATE", "Unknown coverage field.")
                    if not isinstance(row.get("question"), str) or not row["question"].strip():
                        raise ResearchError("INVALID_UPDATE", "Coverage entries need a question.")
                    if not isinstance(row.get("required"), bool):
                        raise ResearchError("INVALID_UPDATE", "Coverage required must be a boolean.")
                    if row.get("status") not in {"open", "covered", "blocked", "excluded"}:
                        raise ResearchError("INVALID_UPDATE", "Invalid coverage status.")
                    if not isinstance(row.get("evidence", []), list):
                        raise ResearchError("INVALID_UPDATE", "Coverage evidence must be an array of passage references.")
                    for ref in row.get("evidence", []):
                        self.assert_current_ref(ref)
                    for key in ("parent_id", "answer_note"):
                        if key in row:
                            identifier(row[key], key)
                    for key in ("answer", "report_anchor", "exclusion_reason", "scope_change_reason"):
                        if key in row and (not isinstance(row[key], str) or not row[key].strip()):
                            raise ResearchError("INVALID_UPDATE", f"{key} must be nonempty text.")
                    if "context_read" in row and not isinstance(row["context_read"], bool):
                        raise ResearchError("INVALID_UPDATE", "context_read must be a boolean, declared after inspecting context.")
                    if "origin" in row:
                        origin = row["origin"]
                        if (not isinstance(origin, dict) or set(origin) != {"kind", "basis"}
                                or origin["kind"] not in {"user", "independent-source", "discovery"}
                                or not isinstance(origin["basis"], str) or not origin["basis"].strip()):
                            raise ResearchError("INVALID_UPDATE", "origin needs kind user/independent-source/discovery and a source-specific basis.")
                    if "support" in row:
                        support = row["support"]
                        if (not isinstance(support, dict) or set(support) != {"judgment", "rationale"}
                                or support["judgment"] not in {"supported", "partial", "unsupported"}
                                or not isinstance(support["rationale"], str) or not support["rationale"].strip()):
                            raise ResearchError("INVALID_UPDATE", "support needs a judgment and semantic rationale; it is researcher-declared.")
                    if "answer" in row and "answer_note" in row:
                        raise ResearchError("INVALID_UPDATE", "Use answer or answer_note, avoiding duplicate answer records.")
                    if "answer_note" in row:
                        note = self.notes().get(row["answer_note"])
                        if not note or row["answer_note"] in self.stale_notes() or note["kind"] == "question":
                            raise ResearchError("INVALID_DEPENDENCY", "answer_note must identify a current substantive note.")
                        row["answer_note_hash"] = note["content_hash"]
                    previous = next((r for r in manifest["coverage"] if r["id"] == rid), None)
                    if previous:
                        if "origin" in previous and row.get("origin") != previous["origin"]:
                            raise ResearchError("SCOPE_CHANGE", "Preserve the original question provenance; add new discoveries separately.")
                        if previous["question"] != row["question"] or (previous["required"] and not row["required"]):
                            if not row.get("scope_change_reason"):
                                raise ResearchError("SCOPE_CHANGE", "Changing a preserved question or removing its requirement needs scope_change_reason.")
                            row["scope_history"] = previous.get("scope_history", []) + [{
                                "question": previous["question"], "required": previous["required"],
                                "reason": row["scope_change_reason"], "changed_at": now()}]
                        elif previous.get("scope_history"):
                            row["scope_history"] = previous["scope_history"]
                    if row["status"] == "excluded" and (QUESTION_FIELDS.intersection(row) or previous) and not row.get("exclusion_reason"):
                        raise ResearchError("SCOPE_CHANGE", "Excluded questions require an explicit exclusion_reason.")
                else:
                    if set(row) - {"id", "description", "blocking", "resolved", "task_ids", "coverage_ids", "next_action", "blocked_reason"}:
                        raise ResearchError("INVALID_UPDATE", "Unknown gap field.")
                    if not isinstance(row.get("description"), str) or not row["description"].strip():
                        raise ResearchError("INVALID_UPDATE", "Gaps need a description.")
                    if not all(isinstance(row.get(key), bool) for key in ("blocking", "resolved")):
                        raise ResearchError("INVALID_UPDATE", "Gap blocking/resolved must be booleans.")
                if collection in {"coverage", "gaps"}:
                    for key in ("next_action", "blocked_reason"):
                        if key in row and (not isinstance(row[key], str) or not row[key].strip()):
                            raise ResearchError("INVALID_UPDATE", f"{key} must be nonempty text; omit it when not applicable.")
                    for key in ("task_ids", "coverage_ids"):
                        if key in row:
                            if not isinstance(row[key], list):
                                raise ResearchError("INVALID_UPDATE", f"{key} must be an array of IDs.")
                            for value in row[key]:
                                identifier(value)
                            if len(set(row[key])) != len(row[key]):
                                raise ResearchError("INVALID_UPDATE", f"{key} must not contain duplicate IDs.")
        question_changed = "question" in patch and patch["question"] != manifest["question"]
        if "coverage" in patch and {r["id"] for r in manifest["coverage"]} - {r["id"] for r in patch["coverage"]}:
            raise ResearchError("SCOPE_REMOVAL", "Preserve existing questions; explicitly exclude with a reason instead of deleting them.")
        for key in ("question", "mode", "tasks", "coverage", "gaps", "reading_scope"):
            if key in patch:
                manifest[key] = patch[key]
        if question_changed:
            for task in manifest["tasks"]:
                task["status"] = "pending"
            for item in manifest["coverage"]:
                if item["status"] != "excluded":
                    item["status"] = "open"
        if "report" in patch:
            if not isinstance(patch["report"], str):
                raise ResearchError("INVALID_UPDATE", "report must be a workspace-relative or absolute path.")
            path = self.report_path(patch["report"])
            manifest["report"] = path.relative_to(self.root).as_posix()
        task_ids = {row["id"] for row in manifest["tasks"]}
        coverage_ids = {row["id"] for row in manifest["coverage"]}
        parents = {row["id"]: row.get("parent_id") for row in manifest["coverage"]}
        for cid in parents:
            seen, parent = {cid}, parents[cid]
            while parent is not None:
                if parent not in parents or parent in seen:
                    raise ResearchError("INVALID_UPDATE", "Question parents must exist and cannot form cycles.")
                seen.add(parent)
                parent = parents[parent]
        for row in manifest["coverage"] + manifest["gaps"]:
            if set(row.get("task_ids", [])) - task_ids or set(row.get("coverage_ids", [])) - coverage_ids:
                raise ResearchError("INVALID_UPDATE", "Linked task and coverage IDs must exist in the updated run.")
        if any(manifest.get(key) != value for key, value in before.items()):
            self.reset_reviews(manifest)
        if "reviews" in patch:
            manifest["status"] = "running"
            manifest.pop("verification", None)
            reviews = patch["reviews"]
            if not isinstance(reviews, dict) or set(reviews) - set(REVIEW_NAMES):
                raise ResearchError("INVALID_REVIEW", "Review names: scope, citations, blind_questions.")
            for key, value in reviews.items():
                if not isinstance(value, dict) or set(value) - {"status", "reviewer", "method", "details"}:
                    raise ResearchError("INVALID_REVIEW", "Review fields: status, reviewer, method, details.")
                if value.get("status") not in {"pending", "passed", "failed"}:
                    raise ResearchError("INVALID_REVIEW", "Review status must be pending, passed, or failed.")
                if value["status"] in {"passed", "failed"}:
                    if not all(isinstance(value.get(k), str) and value[k].strip() for k in ("reviewer", "details")):
                        raise ResearchError("INVALID_REVIEW", "Completed reviews require reviewer and details.")
                    if value.get("method") not in {"independent-agent", "human", "self"}:
                        raise ResearchError("INVALID_REVIEW", "Review method must disclose independent-agent, human, or self.")
                record = dict(value)
                if value["status"] == "passed":
                    path = self.report_path(manifest.get("report"))
                    if not path.is_file():
                        raise ResearchError("REPORT_MISSING", "Write the report before recording a passed review.")
                    record["report_sha256"] = digest(path.read_bytes())
                    record["research_sha256"] = self.research_hash(manifest)
                    record["reviewed_at"] = now()
                manifest["reviews"][key] = record
        self.save_manifest(manifest)
        return self.status()

    def resume(self) -> dict:
        manifest = self.manifest()
        stale = self.mark_stale()
        invalidated = set(self.task_invalidations(manifest))
        changed = bool(stale or invalidated or self.invalidated_reviews(manifest))
        incomplete_questions = {p["id"] for p in self.question_progress(manifest) if not p["reported"]}
        for task in manifest["tasks"]:
            if task["status"] == "running" or task["id"] in invalidated:
                task["status"] = "pending"
                changed = True
        for row in manifest["coverage"]:
            if row["status"] == "excluded":
                continue
            if row["status"] == "covered" and (not self.coverage_evidence(row) or row["id"] in incomplete_questions):
                row["status"] = "open"
                changed = True
            for ref in self.coverage_evidence(row):
                try:
                    self.assert_current_ref(ref)
                except ResearchError:
                    row["status"] = "open"
                    changed = True
                    break
        if changed:
            self.reset_reviews(manifest)
        elif manifest["status"] == "partial":
            manifest["status"] = "running"
        self.save_manifest(manifest)
        return {**self.status(), "resumed": True,
                "next_tasks": [t["id"] for t in manifest["tasks"] if t["status"] != "done"]}

    def search(self, query: str, limit: int = 10, *, mode: str = "any",
               source_id: str | None = None, kind: str = "all") -> dict:
        from .search import search
        return search(self, query, limit, mode=mode, source_id=source_id, kind=kind)

    def verify(self, report: str | Path | None = None) -> dict:
        manifest = self.manifest()
        checks = []
        def check(name, ok, detail):
            checks.append({"name": name, "ok": bool(ok), "detail": detail})
        catalog = self.catalog()
        source_errors = []
        for sid, rev in catalog.items():
            try:
                meta = self.metadata(sid, rev)
                directory = self.revision_dir(sid, rev)
                filename = meta["original_file"]
                if Path(filename).name != filename:
                    raise ResearchError("INVALID_RECORD", "Invalid original file name.")
                raw = contained(self.root, directory / filename).read_bytes()
                passages_raw = contained(self.root, directory / "passages.jsonl").read_bytes()
                if digest(raw) != meta["sha256"] or digest(passages_raw) != meta["passages_sha256"]:
                    source_errors.append(f"{sid}: stored content changed")
                entries = self.passages(sid, rev)
                extracted = {key: meta[key] for key in ("format", "extractor", "extractor_version", "completeness", "warnings")}
                if "capture_quality" in meta:
                    extracted["capture_quality"] = meta["capture_quality"]
                extracted["passages"] = entries
                extraction_hash = digest(extracted)
                provenance = {"raw_sha256": digest(raw), "extraction_sha256": extraction_hash,
                              "capture_kind": meta["capture_kind"], "declared_completeness": meta["declared_completeness"],
                              "title": meta["title"], "origin": meta["url"] or meta["original_path"],
                              "edition": meta["edition"] or ""}
                revision_hash = digest(provenance)
                if (extraction_hash != meta["extraction_sha256"] or revision_hash != meta["revision_sha256"]
                        or revision_hash[:16] != rev or meta["source_id"] != sid or meta["revision"] != rev):
                    source_errors.append(f"{sid}: source metadata or revision identity changed")
                if len({p["id"] for p in entries}) != len(entries) or len(entries) != meta["passage_count"]:
                    source_errors.append(f"{sid}: passage count or IDs are inconsistent")
            except (ResearchError, OSError, KeyError, TypeError) as exc:
                source_errors.append(f"{sid}: {exc}")
        check("source-integrity", not source_errors, source_errors)
        required_errors = []
        open_topic = manifest.get("reading_scope", {}).get("kind") == "open-topic"
        for sid in manifest["required_sources"]:
            try:
                contextual = any(row.get("context_read") is True and row["status"] != "excluded" and
                                 any(ref.startswith(f"{sid}@{catalog.get(sid)}:") for ref in self.coverage_evidence(row))
                                 for row in manifest["coverage"])
                empty = sid in catalog and self.metadata(sid, catalog[sid]).get("capture_quality", {}).get("status") == "empty"
                if sid not in catalog or empty or (not contextual if open_topic else self.metadata(sid, catalog[sid])["completeness"] != "full"):
                    required_errors.append(sid)
            except ResearchError:
                required_errors.append(sid)
        check("required-source-context" if open_topic else "required-sources-full", not required_errors, required_errors)
        note_errors = []
        for nid, note in self.notes().items():
            original_hash = note.get("content_hash")
            payload = {key: value for key, value in note.items() if key not in {"content_hash", "status", "updated_at"}}
            if digest(payload) != original_hash:
                note_errors.append(f"{nid}: note record edited outside commit")
            for evidence in note.get("evidence", []):
                try:
                    passage = self.assert_current_ref(evidence["ref"])
                    if "quote" in evidence:
                        norm = lambda text: " ".join(unicodedata.normalize("NFC", text).split())
                        if norm(evidence["quote"]) not in norm(passage["text"]):
                            note_errors.append(f"{nid}: quote mismatch")
                except (ResearchError, KeyError, TypeError) as exc:
                    note_errors.append(f"{nid}: {exc}")
        check("note-integrity", not note_errors, note_errors)
        stale = self.stale_notes()
        check("notes-current", not stale, stale)
        unfinished = [task["id"] for task in manifest["tasks"] if task["status"] != "done"]
        invalidated = self.task_invalidations(manifest)
        check("tasks-complete", not unfinished and not invalidated, {"unfinished": unfinished, "invalidated": invalidated})
        required_coverage = [row for row in manifest["coverage"] if row["required"]]
        coverage_errors = []
        progress = self.question_progress(manifest, report)
        incomplete_questions = {p["id"] for p in progress if not p["reported"]}
        for row in required_coverage:
            if row["status"] != "covered" or not self.coverage_evidence(row) or row["id"] in incomplete_questions:
                coverage_errors.append(row["id"])
            for ref in self.coverage_evidence(row):
                try:
                    self.assert_current_ref(ref)
                except ResearchError:
                    coverage_errors.append(row["id"])
        check("required-coverage", bool(required_coverage) and not coverage_errors, coverage_errors or "At least one required covered area with evidence is needed.")
        if any(QUESTION_FIELDS.intersection(row) for row in manifest["coverage"]):
            audit_errors = self.audit_errors(manifest)
            check("source-derived-map-audit", bool(manifest.get("map_audits")) and not audit_errors,
                  audit_errors or "Seal candidates before comparison; method is declared, not machine-certified.")
        gaps = [gap["id"] for gap in manifest["gaps"] if gap["blocking"] and not gap["resolved"]]
        check("blocking-gaps-resolved", not gaps, gaps)
        covered = {row["id"] for row in manifest["coverage"] if row["status"] == "covered"}
        conflicts = [{"gap": gap["id"], "coverage": sorted(covered.intersection(gap.get("coverage_ids", [])))}
                     for gap in manifest["gaps"] if gap["blocking"] and not gap["resolved"]
                     and covered.intersection(gap.get("coverage_ids", []))]
        check("coverage-gap-consistency", not conflicts, conflicts)
        path = self.report_path(report)
        report_exists = path.is_file()
        check("report-exists", report_exists, str(path))
        text = path.read_text(encoding="utf-8-sig") if report_exists else ""
        report_hash = digest(path.read_bytes()) if report_exists else None
        refs = CITATION_RE.findall(text)
        citation_errors = []
        for ref in refs:
            try:
                self.assert_current_ref(ref)
            except ResearchError as exc:
                citation_errors.append(str(exc))
        if text.count("[[") != len(refs) or text.count("]]") != len(refs):
            citation_errors.append("Malformed citation markers.")
        check("report-citations", bool(refs) and not citation_errors,
              citation_errors or f"{len(refs)} passage citation(s); semantic support is not inferred.")
        for name in REVIEW_NAMES:
            review = manifest["reviews"].get(name, {})
            research_matches = review.get("research_sha256") == self.research_hash(manifest)
            accepted = (review.get("status") == "passed" and bool(review.get("reviewer"))
                        and bool(review.get("details")) and review.get("method") in {"independent-agent", "human", "self"}
                        and report_hash is not None and review.get("report_sha256") == report_hash and research_matches)
            check(f"review:{name}", accepted,
                  {"status": review.get("status", "pending"), "method": review.get("method"),
                   "matches_report": bool(report_hash) and review.get("report_sha256") == report_hash,
                   "matches_research": research_matches})
        return {"passed": all(item["ok"] for item in checks), "verification_scope": "structural-only",
                "semantic_support": "requires-source-based-review", "checks": checks,
                "report_sha256": report_hash,
                "independent_reviews": [name for name in REVIEW_NAMES if manifest["reviews"].get(name, {}).get("method") in {"human", "independent-agent"}]}

    def finish(self, report: str | Path, outcome: str) -> dict:
        manifest = self.manifest()
        path = self.report_path(report)
        if not path.is_file():
            raise ResearchError("REPORT_MISSING", "Write the report before finishing, including a partial report.")
        result = self.verify(path)
        manifest["report"] = path.relative_to(self.root).as_posix()
        manifest["verification"] = result
        manifest["status"] = outcome if result["passed"] or outcome == "partial" else "partial"
        self.save_manifest(manifest)
        if outcome == "complete-within-scope" and not result["passed"]:
            raise ResearchError("VERIFICATION_FAILED", "Completion checks failed; run remains partial.", result)
        return {**self.status(), "verification": result}
