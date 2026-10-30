"""Count tool calls, wall time and tokens per agent in the session's subagent transcripts.

Usage: python -I runstats.py <subagents dir> <out dir>
Reads every agent-*.jsonl (top level only) plus its .meta.json; writes
  agents.tsv     one row per agent
  calls.tsv      one row per tool call (agent, time, tool, short input, error flag, result seconds)
  summary.txt    per-arm totals and per-agent tables for the two Yalova tests
Only "assistant" records are counted (api-request-blob records duplicate them).
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import re
import sys
from pathlib import Path

T2_MARK = "2026-10-29-yalova-tarihi"


def ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def local(t: dt.datetime) -> str:
    return (t + dt.timedelta(hours=3)).strftime("%H:%M:%S")


def short_input(name: str, inp: dict) -> str:
    if name in ("Bash", "PowerShell"):
        return re.sub(r"\s+", " ", inp.get("command", ""))[:300]
    if name == "WebSearch":
        return inp.get("query", "")
    if name == "WebFetch":
        return inp.get("url", "")
    if name in ("Read", "Write", "Edit", "NotebookEdit"):
        return inp.get("file_path", "")
    if name == "Agent":
        return inp.get("description", "")
    if name == "ToolSearch":
        return inp.get("query", "")
    if name in ("Glob", "Grep"):
        return f'{inp.get("pattern", "")} @ {inp.get("path", "")}'
    return json.dumps(inp, ensure_ascii=False)[:200]


def classify_bash(cmd: str) -> str:
    c = cmd
    if "vafer_check" in c:
        for sub in ("fetch", "check", "diff"):
            if re.search(rf"vafer_check\w*\.py\"?'?\s+{sub}\b", c):
                return f"vafer_check {sub}"
        return "vafer_check other"
    if re.search(r"\bdate\b", c) and len(c) < 60:
        return "date"
    if re.search(r"\b(python|py)\b", c):
        return "python other"
    if re.search(r"\b(cp|mv|copy|move|Copy-Item|Move-Item|Rename-Item)\b", c):
        return "copy/move"
    if re.search(r"\b(ls|dir|Get-ChildItem|find|wc|cat|head|tail|grep|sed|Get-Content|Select-String)\b", c):
        return "inspect"
    if re.search(r"\b(curl|wget|Invoke-WebRequest|pdftotext)\b", c):
        return "download"
    if re.search(r"\bmkdir\b|New-Item", c):
        return "mkdir"
    return "other"


def fetch_url_count(cmd: str) -> int:
    m = re.search(r"vafer_check[\w.]*\.py\"?'?\s+fetch\s+(.*)", cmd, re.S)
    if not m:
        return 0
    return len(re.findall(r"https?://", m.group(1)))


def result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
    return ""


def load(path: Path) -> dict:
    meta_path = path.with_name(path.stem + ".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    agent = {"id": path.stem.removeprefix("agent-"), "desc": meta.get("description", ""),
             "parent": meta.get("parentAgentId", ""), "calls": [], "first": None, "last": None,
             "t2": False, "out_tokens": 0, "in_tokens": 0, "cache_read": 0, "cache_create": 0,
             "msgs": set(), "first_prompt": "", "final_text": ""}
    pending = {}
    seen_ids = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if T2_MARK in line:
                agent["t2"] = True
            d = json.loads(line)
            typ = d.get("type")
            if typ not in ("user", "assistant"):
                continue
            t = ts(d["timestamp"]) if d.get("timestamp") else None
            if t:
                agent["first"] = agent["first"] or t
                agent["last"] = t
            msg = d.get("message") or {}
            content = msg.get("content")
            if typ == "user" and not agent["first_prompt"]:
                agent["first_prompt"] = result_text(content) if not isinstance(content, str) else content
            if typ == "assistant":
                mid = msg.get("id")
                if mid and mid not in agent["msgs"]:
                    agent["msgs"].add(mid)
                    u = msg.get("usage") or {}
                    agent["out_tokens"] += u.get("output_tokens", 0) or 0
                    agent["in_tokens"] += u.get("input_tokens", 0) or 0
                    agent["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
                    agent["cache_create"] += u.get("cache_creation_input_tokens", 0) or 0
                for item in content if isinstance(content, list) else []:
                    if item.get("type") == "tool_use" and item["id"] not in seen_ids:
                        seen_ids.add(item["id"])
                        call = {"id": item["id"], "t": t, "name": item["name"],
                                "input": short_input(item["name"], item.get("input") or {}),
                                "raw": item.get("input") or {}, "err": False, "rt": None, "res": ""}
                        agent["calls"].append(call)
                        pending[item["id"]] = call
                    elif item.get("type") == "text" and item.get("text", "").strip():
                        agent["final_text"] = item["text"]
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        call = pending.get(item.get("tool_use_id"))
                        if call and call["rt"] is None:
                            call["err"] = bool(item.get("is_error"))
                            call["rt"] = t
                            call["res"] = result_text(item.get("content"))[:4000]
    return agent


def counts(calls) -> collections.Counter:
    c = collections.Counter()
    for call in calls:
        c[call["name"]] += 1
        if call["name"] in ("Bash", "PowerShell"):
            c["  bash:" + classify_bash(call["raw"].get("command", ""))] += 1
            c["  fetch-urls"] += fetch_url_count(call["raw"].get("command", ""))
        if call["err"]:
            c["  errors"] += 1
        if call["name"] == "Read" and "/pages/" in call["input"].replace("\\", "/"):
            c["  read:snapshot"] += 1
    return c


def fmt_dur(a, b) -> str:
    if not a or not b:
        return "?"
    s = int((b - a).total_seconds())
    return f"{s // 60}m{s % 60:02d}s"


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    agents = {a["id"]: a for a in (load(p) for p in sorted(src.glob("agent-*.jsonl")))}

    with open(out / "agents.tsv", "w", encoding="utf-8") as fh:
        fh.write("id\tdesc\tparent\tt2\tstart\tend\twall\tcalls\tout_tokens\tcache_read\n")
        for a in agents.values():
            fh.write(f'{a["id"]}\t{a["desc"]}\t{a["parent"]}\t{a["t2"]}\t'
                     f'{local(a["first"]) if a["first"] else ""}\t{local(a["last"]) if a["last"] else ""}\t'
                     f'{fmt_dur(a["first"], a["last"])}\t{len(a["calls"])}\t{a["out_tokens"]}\t{a["cache_read"]}\n')
    with open(out / "calls.tsv", "w", encoding="utf-8") as fh:
        fh.write("agent\tdesc\ttime\ttool\tkind\terr\tsecs\tinput\n")
        for a in agents.values():
            for c in a["calls"]:
                secs = f'{(c["rt"] - c["t"]).total_seconds():.0f}' if c["rt"] and c["t"] else ""
                kind = classify_bash(c["raw"].get("command", "")) if c["name"] in ("Bash", "PowerShell") else ""
                fh.write(f'{a["id"]}\t{a["desc"]}\t{local(c["t"]) if c["t"] else ""}\t{c["name"]}\t{kind}\t'
                         f'{int(c["err"])}\t{secs}\t{c["input"]}\n')

    arms = {
        "t2 v0.0.4": "ab569b7fdce2cbf4b",
        "t2 v0.2 (first draft)": "affe8cbfcbebb9c08",
        "t2 bare": "a5d8156d1758e2822",
        "t2 judge": "afb4b61ca239b5b72",
        "t1 vafer (0.2.0-alpha, first live run)": "ae3c486b6eb775c52",
        "t1 bare": "afdc4aedb2c52b348",
        "t1 judge": "a45b0f6660286003a",
    }
    lines = []
    for arm, lead in arms.items():
        if lead not in agents:
            lines.append(f"## {arm}: lead {lead} missing")
            continue
        members = [agents[lead]] + [a for a in agents.values() if a["parent"] == lead]
        total = collections.Counter()
        lines.append(f"## {arm}")
        lines.append(f"lead {lead}: {local(agents[lead]['first'])} -> {local(agents[lead]['last'])} "
                     f"({fmt_dur(agents[lead]['first'], agents[lead]['last'])})")
        lines.append("agent | role | start | end | wall | calls | WebSearch | WebFetch | Bash | Read | Write/Edit | "
                     "Agent | fetch-urls | vc fetch/check/diff | errors | out tok")
        for a in members:
            c = counts(a["calls"])
            total += c
            role = "LEAD" if a["id"] == lead else a["desc"]
            lines.append(" | ".join(str(x) for x in (
                a["id"][:8], role, local(a["first"]), local(a["last"]), fmt_dur(a["first"], a["last"]),
                len(a["calls"]), c["WebSearch"], c["WebFetch"], c["Bash"] + c["PowerShell"], c["Read"],
                c["Write"] + c["Edit"], c["Agent"], c["  fetch-urls"],
                f'{c["  bash:vafer_check fetch"]}/{c["  bash:vafer_check check"]}/{c["  bash:vafer_check diff"]}',
                c["  errors"], a["out_tokens"])))
        lines.append(f"TOTAL calls {sum(len(a['calls']) for a in members)}; agents {len(members)} "
                     f"(subagents {len(members) - 1}); out tokens {sum(a['out_tokens'] for a in members)}; "
                     f"cache-read tokens {sum(a['cache_read'] for a in members)}")
        lines.append("by tool: " + ", ".join(f"{k}={v}" for k, v in sorted(total.items()) if not k.startswith("  ")))
        lines.append("bash kinds: " + ", ".join(f"{k.strip()}={v}" for k, v in sorted(total.items()) if k.startswith("  ")))
        lines.append("")
    (out / "summary.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
