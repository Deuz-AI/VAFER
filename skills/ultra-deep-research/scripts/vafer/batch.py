"""Small sequential reading checkpoints; successful prefixes survive a failure."""

from __future__ import annotations

import re
import time

from .store import ResearchError, identifier


OPS = {
    "ingest": {"file", "source_url", "title", "edition", "capture_kind", "completeness", "source_id", "required"},
    "commit": {"value"}, "patch": {"value"}, "read-many": {"refs"},
    "audit-seal": {"value"}, "audit-resolve": {"value"}, "status": set(),
}
ALIAS = re.compile(r"\$([A-Za-z0-9][A-Za-z0-9_-]{0,79}):(p\d{6})")


def checkpoint(workspace, operations):
    """One workspace lock is held by the CLI. No hidden network or model calls."""
    if not isinstance(operations, list) or not 1 <= len(operations) <= 100:
        raise ResearchError("INVALID_BATCH", "Supply an array of 1 to 100 operations.")
    names = set()
    for operation in operations:
        if not isinstance(operation, dict) or operation.get("op") not in OPS:
            raise ResearchError("INVALID_BATCH", "Unknown batch operation.")
        op = operation["op"]
        if set(operation) - (OPS[op] | {"op", "as"}):
            raise ResearchError("INVALID_BATCH", f"Unknown fields for {op}.")
        if "as" in operation:
            name = identifier(operation["as"], "batch alias")
            if op != "ingest" or name in names:
                raise ResearchError("INVALID_BATCH", "Only ingests can define unique aliases.")
            names.add(name)
    aliases, results = {}, []

    def expand(value):
        if isinstance(value, list):
            return [expand(item) for item in value]
        if isinstance(value, dict):
            return {key: expand(item) for key, item in value.items()}
        if isinstance(value, str):
            def substitute(match):
                name, pid = match.groups()
                ref = aliases.get(name, {}).get(pid)
                if ref is None:
                    raise ResearchError("INVALID_ALIAS", f"No returned passage for {match.group(0)}.")
                return ref
            # Only whole reference values and citation tokens, never source text/paths.
            if ALIAS.fullmatch(value):
                return ALIAS.sub(substitute, value)
            return re.sub(r"\[\[(\$[A-Za-z0-9_-]+:p\d{6})\]\]",
                          lambda match: "[[" + ALIAS.sub(substitute, match.group(1)) + "]]", value)
        return value

    for index, operation in enumerate(operations):
        started = time.perf_counter()
        op = operation["op"]
        try:
            if op == "ingest":
                data = workspace.ingest(**{key: value for key, value in operation.items() if key in OPS[op]})
                if "as" in operation:
                    aliases[operation["as"]] = {ref.rsplit(":", 1)[1]: ref for ref in data["refs"]}
            elif op == "read-many":
                data = workspace.read_many(expand(operation["refs"]))
            elif op == "status":
                data = workspace.status()
            else:
                method = {"commit": "commit", "patch": "patch", "audit-seal": "audit_seal",
                          "audit-resolve": "audit_resolve"}[op]
                data = getattr(workspace, method)(expand(operation["value"]))
            if op == "patch":
                data = {key: data[key] for key in ("status", "next_actions", "blocked_actions")}
            results.append({"index": index, "op": op, "data": data,
                            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
        except (ResearchError, OSError, ValueError, TypeError, KeyError) as exc:
            raise ResearchError("BATCH_STOPPED", str(exc), {
                "failed_index": index, "failed_op": op,
                "cause": getattr(exc, "code", "RECORD_ERROR"),
                "completed": results, "aliases": aliases,
                "atomic": False, "recovery": "Inspect completed operations; retry the failed operation and remaining suffix."
            }) from exc
    return {"operations": results, "aliases": aliases, "atomic": False}
