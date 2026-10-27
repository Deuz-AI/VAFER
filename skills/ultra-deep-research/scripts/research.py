#!/usr/bin/env python3
"""Local VAFER research tools. Every command emits one JSON response."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import importlib.util
import json
import platform
from pathlib import Path
import sqlite3
import sys
import time

from vafer import __version__
from vafer.store import ResearchError, Workspace, read_json, workspace_lock


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ResearchError("INVALID_ARGUMENT", message)


def parser():
    root = Parser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True, parser_class=Parser)
    commands.add_parser("doctor", help="Inspect local runtime capabilities without network calls.")
    def workspace(name, help_text):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--workspace", required=True)
        return command
    ingest = workspace("ingest", "Capture a local source file as an immutable revision.")
    ingest.add_argument("--file", required=True)
    for name in ("source-url", "title", "edition", "source-id"):
        ingest.add_argument("--" + name)
    ingest.add_argument("--capture-kind", choices=("original-file", "host-snapshot", "excerpt"), default="original-file")
    ingest.add_argument("--completeness", choices=("full", "partial", "unknown"), default="unknown")
    ingest.add_argument("--required", action="store_true")
    search = workspace("search", "Search current source passages and notes; results are untrusted data.")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--mode", choices=("any", "all"), default="any")
    search.add_argument("--source-id")
    search.add_argument("--kind", choices=("all", "sources", "notes"), default="all")
    read = workspace("read", "Read a current or historical passage and its provenance.")
    read.add_argument("--ref", required=True)
    read_many = workspace("read-many", "Read 1 to 100 references from a JSON array, with shared source metadata.")
    read_many.add_argument("--file", required=True)
    commit = workspace("commit", "Validate and merge one contextual note from JSON.")
    commit.add_argument("--file", required=True)
    batch = workspace("batch", "Apply a reading checkpoint; successful operations survive a later failure.")
    batch.add_argument("--file", required=True)
    verify = workspace("verify", "Check structural integrity and recorded reviews; not factual truth.")
    verify.add_argument("--report")
    run = commands.add_parser("run", help="Manage research state.")
    actions = run.add_subparsers(dest="action", required=True, parser_class=Parser)
    for action in ("init", "update", "patch", "audit-seal", "audit-resolve", "status", "resume", "finish"):
        command = actions.add_parser(action)
        command.add_argument("--workspace", required=True)
        if action == "init":
            command.add_argument("--question", required=True)
            command.add_argument("--mode", choices=("study", "followup"), default="study")
        if action in {"update", "patch", "audit-seal", "audit-resolve"}:
            command.add_argument("--file", required=True)
        if action == "finish":
            command.add_argument("--report", required=True)
            command.add_argument("--outcome", choices=("complete-within-scope", "partial"), required=True)
    return root


def doctor():
    with sqlite3.connect(":memory:") as connection:
        try:
            connection.execute("CREATE VIRTUAL TABLE test USING fts5(text)")
            fts5 = True
        except sqlite3.OperationalError:
            fts5 = False
    return {"version": __version__, "python": platform.python_version(), "python_supported": sys.version_info >= (3, 11),
            "sqlite": sqlite3.sqlite_version, "fts5": fts5,
            "optional_extractors": {name: importlib.util.find_spec(name) is not None for name in ("pypdf", "trafilatura")},
            "network_calls": False, "host_tools": "Discover search, browser, vision and delegation in the active host session."}


def execute(args):
    if args.command == "doctor":
        return doctor()
    workspace = Workspace(args.workspace)
    mutating = args.command in {"ingest", "commit", "search", "batch"} or (args.command == "run" and args.action != "status")
    # Search only writes its disposable cache; serialize it with source commits.
    # Readers can arrive together; wait briefly for another search's cache write.
    with workspace_lock(workspace.root, timeout=5 if args.command == "search" else 0) if mutating else nullcontext():
        if args.command == "ingest":
            return workspace.ingest(args.file, source_url=args.source_url, title=args.title, edition=args.edition,
                                    capture_kind=args.capture_kind, completeness=args.completeness,
                                    source_id=args.source_id, required=args.required)
        if args.command == "search":
            return workspace.search(args.query, args.limit, mode=args.mode, source_id=args.source_id, kind=args.kind)
        if args.command == "read":
            return workspace.read(args.ref)
        if args.command == "read-many":
            return workspace.read_many(read_json(Path(args.file)))
        if args.command == "commit":
            return workspace.commit(read_json(Path(args.file)))
        if args.command == "batch":
            from vafer.batch import checkpoint
            return checkpoint(workspace, read_json(Path(args.file)))
        if args.command == "verify":
            result = workspace.verify(args.report)
            if not result["passed"]:
                raise ResearchError("VERIFICATION_FAILED", "Structural completion checks failed.", result)
            return result
        if args.action == "init":
            return workspace.init(args.question, args.mode)
        if args.action == "update":
            return workspace.update(read_json(Path(args.file)))
        if args.action in {"patch", "audit-seal", "audit-resolve"}:
            return getattr(workspace, args.action.replace("-", "_"))(read_json(Path(args.file)))
        if args.action == "status":
            return workspace.status()
        if args.action == "resume":
            return workspace.resume()
        return workspace.finish(args.report, args.outcome)


def main(argv=None):
    started = time.perf_counter()
    def emit(payload):
        payload["metrics"] = {"elapsed_ms": round((time.perf_counter() - started) * 1000, 3)}
        print(json.dumps(payload, ensure_ascii=False))
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        args = parser().parse_args(argv)
        value = execute(args)
        emit({"ok": True, "data": value})
        return 0
    except ResearchError as exc:
        error = {"code": exc.code, "message": str(exc)}
        if exc.details is not None:
            error["details"] = exc.details
        emit({"ok": False, "error": error})
        return 1
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        emit({"ok": False, "error": {"code": "RECORD_ERROR", "message": str(exc)}})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
