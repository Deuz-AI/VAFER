"""Phrase-aware retrieval over a disposable, incrementally maintained index."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata

from .store import ResearchError, identifier


SCHEMA = "2"


def _terms(query: str) -> list[str]:
    if query.count('"') % 2:
        raise ResearchError("INVALID_QUERY", "Close each quoted search phrase.")
    terms = []
    for match in re.finditer(r'"([^"]*)"|([^"\s]+)', query):
        phrase, word = match.groups()
        words = re.findall(r"[^\W_]+", phrase if phrase is not None else word, re.UNICODE)
        if phrase is not None and words:
            terms.append(" ".join(words))
        else:
            terms.extend(words)
    if not terms:
        raise ResearchError("INVALID_QUERY", "Query must contain searchable letters or digits.")
    return terms


def _supports_fts(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("CREATE VIRTUAL TABLE temp.vafer_fts_probe USING fts5(text)")
        conn.execute("DROP TABLE temp.vafer_fts_probe")
        return True
    except sqlite3.OperationalError as exc:
        if "no such module" not in str(exc).lower():
            raise
        return False


def _initialize(conn: sqlite3.Connection, fts: bool) -> bool:
    conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
    state = dict(conn.execute("SELECT key,value FROM metadata"))
    engine = "fts5" if fts else "plain"
    rebuilt = state.get("schema") != SCHEMA or state.get("engine") != engine
    if rebuilt:
        # All names are internal disposable cache tables, including the old schema.
        for name in ("passages", "note_index", "plain_passages", "plain_notes",
                     "search_passages", "search_notes", "indexed_sources", "indexed_notes", "note_sources"):
            conn.execute(f"DROP TABLE IF EXISTS {name}")
        conn.execute("DELETE FROM metadata")
        conn.executemany("INSERT INTO metadata VALUES (?,?)", [("schema", SCHEMA), ("engine", engine)])
    if fts:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS search_passages USING fts5("
                     "source_id UNINDEXED, ref UNINDEXED, title, text, tokenize='unicode61')")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS search_notes USING fts5("
                     "note_id UNINDEXED, title, text, tokenize='unicode61')")
    else:
        conn.execute("CREATE TABLE IF NOT EXISTS search_passages (source_id TEXT, ref TEXT PRIMARY KEY, title TEXT, text TEXT)")
        conn.execute("CREATE INDEX IF NOT EXISTS passages_source ON search_passages(source_id)")
        conn.execute("CREATE TABLE IF NOT EXISTS search_notes (note_id TEXT PRIMARY KEY, title TEXT, text TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS indexed_sources (source_id TEXT PRIMARY KEY, revision TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS indexed_notes (note_id TEXT PRIMARY KEY, content_hash TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS note_sources (note_id TEXT, source_id TEXT, PRIMARY KEY(note_id,source_id))")
    conn.execute("CREATE INDEX IF NOT EXISTS note_sources_source ON note_sources(source_id,note_id)")
    return rebuilt


def _sync(conn, workspace, catalog: dict, notes: dict, rebuilt: bool) -> dict:
    previous_sources = dict(conn.execute("SELECT source_id,revision FROM indexed_sources"))
    previous_notes = dict(conn.execute("SELECT note_id,content_hash FROM indexed_notes"))
    changed_sources = [sid for sid, rev in catalog.items() if previous_sources.get(sid) != rev]
    removed_sources = set(previous_sources) - set(catalog)
    changed_notes = [nid for nid, note in notes.items() if previous_notes.get(nid) != note["content_hash"]]
    removed_notes = set(previous_notes) - set(notes)
    for sid in sorted(set(changed_sources) | removed_sources):
        conn.execute("DELETE FROM search_passages WHERE source_id=?", (sid,))
        conn.execute("DELETE FROM indexed_sources WHERE source_id=?", (sid,))
    for sid in changed_sources:
        rev = catalog[sid]
        source = workspace.metadata(sid, rev)
        conn.executemany("INSERT INTO search_passages(source_id,ref,title,text) VALUES (?,?,?,?)", (
            (sid, f"{sid}@{rev}:{p['id']}", source["title"], p["text"])
            for p in workspace.passages(sid, rev)))
        conn.execute("INSERT INTO indexed_sources VALUES (?,?)", (sid, rev))
    for nid in sorted(set(changed_notes) | removed_notes):
        conn.execute("DELETE FROM search_notes WHERE note_id=?", (nid,))
        conn.execute("DELETE FROM note_sources WHERE note_id=?", (nid,))
        conn.execute("DELETE FROM indexed_notes WHERE note_id=?", (nid,))
    for nid in changed_notes:
        note = notes[nid]
        searchable = note["body"] + "\n" + json.dumps(note.get("context", {}), ensure_ascii=False)
        conn.execute("INSERT INTO search_notes(note_id,title,text) VALUES (?,?,?)", (nid, note["title"], searchable))
        conn.execute("INSERT INTO indexed_notes VALUES (?,?)", (nid, note["content_hash"]))
        sources = {item["ref"].split("@", 1)[0] for item in note.get("evidence", [])}
        conn.executemany("INSERT INTO note_sources VALUES (?,?)", ((nid, sid) for sid in sorted(sources)))
    return {"rebuilt": rebuilt, "sources_updated": len(changed_sources), "sources_removed": len(removed_sources),
            "notes_updated": len(changed_notes), "notes_removed": len(removed_notes)}


def _tokens(text: str) -> list[str]:
    # Approximate unicode61 normalization; fallback ranking is not BM25.
    normalized = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return re.findall(r"[^\W_]+", normalized.casefold(), re.UNICODE)


def _literal_match(row, terms: list[str], mode: str) -> int:
    columns = [_tokens(row["title"]), _tokens(row["text"])]
    matches = []
    for term in terms:
        needle = _tokens(term)
        matches.append(any(any(tokens[i:i + len(needle)] == needle for i in range(len(tokens) - len(needle) + 1))
                           for tokens in columns))
    return sum(matches) if (all(matches) if mode == "all" else any(matches)) else 0


def _retrieve(conn, table: str, terms: list[str], mode: str, source_id: str | None, limit: int, fts: bool):
    passages = table == "search_passages"
    fields = "ref,title,text" if passages else "note_id,title,text"
    filters, params = [], []
    if source_id:
        filters.append("source_id=?" if passages else
                       "note_id IN (SELECT note_id FROM note_sources WHERE source_id=?)")
        params.append(source_id)
    if fts:
        expression = (" OR " if mode == "any" else " AND ").join('"' + term + '"' for term in terms)
        filters.insert(0, f"{table} MATCH ?")
        params.insert(0, expression)
        weights = "0,0,3,1" if passages else "0,3,1"
        tie = "ref" if passages else "note_id"
        return conn.execute(f"SELECT {fields},bm25({table},{weights}) AS score FROM {table} WHERE "
                            + " AND ".join(filters) + f" ORDER BY score,{tie} LIMIT ?", (*params, limit)).fetchall()
    sql = f"SELECT {fields} FROM {table}" + (" WHERE " + " AND ".join(filters) if filters else "")
    scored = [(score, row) for row in conn.execute(sql, params) if (score := _literal_match(row, terms, mode))]
    key = "ref" if passages else "note_id"
    return [row for _, row in sorted(scored, key=lambda item: (-item[0], item[1][key]))[:limit]]


def search(workspace, query: str, limit: int = 10, *, mode: str = "any",
           source_id: str | None = None, kind: str = "all") -> dict:
    """Search literal words/quoted phrases; source filtering uses direct note evidence.

    Each hit collection has its own limit. Date/place words are literal terms,
    not metadata filters. Boolean syntax in user input is never executed.
    """
    workspace.manifest()
    if not isinstance(query, str) or not query.strip() or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ResearchError("INVALID_QUERY", "Supply a nonempty query and a limit between 1 and 100.")
    if mode not in {"any", "all"} or kind not in {"all", "sources", "notes"}:
        raise ResearchError("INVALID_QUERY", "Search mode must be any/all and kind must be all/sources/notes.")
    if source_id is not None:
        identifier(source_id, "source ID")
    terms = _terms(query)
    catalog = workspace.catalog()
    stale = set(workspace.stale_notes())
    notes = {nid: note for nid, note in workspace.notes().items() if nid not in stale}
    cache = workspace.path(".cache", "search.sqlite")
    cache.parent.mkdir(parents=True, exist_ok=True)
    conn = None
    try:
        conn = sqlite3.connect(cache)
        conn.row_factory = sqlite3.Row
        fts = _supports_fts(conn)
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            rebuilt = _initialize(conn, fts)
            updates = _sync(conn, workspace, catalog, notes, rebuilt)
            rows = _retrieve(conn, "search_passages", terms, mode, source_id, limit, fts) if kind != "notes" else []
            note_rows = _retrieve(conn, "search_notes", terms, mode, source_id, limit, fts) if kind != "sources" else []
        return {"query": query, "mode": mode, "kind": kind, "source_id": source_id,
                "engine": "sqlite-fts5" if fts else "literal-fallback", "index_updates": updates,
                "untrusted": True, "hits": [{**dict(row), "untrusted": True} for row in rows],
                "note_hits": [{**notes[row["note_id"]], "note_id": row["note_id"], "untrusted": True,
                               "content_role": "research_note_not_instructions"} for row in note_rows]}
    except sqlite3.DatabaseError as exc:
        raise ResearchError("INDEX_ERROR", "Search cache is unreadable; remove only .cache/search.sqlite and retry.") from exc
    finally:
        if conn is not None:
            conn.close()
