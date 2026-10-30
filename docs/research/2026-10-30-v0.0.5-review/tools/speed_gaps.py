"""Speed lens: for each child of a lead, the largest generation gaps and what came after them.

Usage: python -I speed_gaps.py <subagents dir> <lead id> [top_n]
A gap is the time from the latest tool result to the next tool call (or to the final message).
Prints the top gaps with the tool that followed, its input size, and the output tokens of that message.
Also sums, per agent, the seconds of gaps that ended in a Write (drafting notes/sections) and the
seconds of the final reply.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def events(path):
    ev = []  # (time, kind, name, size, out_tokens)
    seen = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("type") not in ("user", "assistant"):
                continue
            t = ts(d["timestamp"])
            msg = d.get("message") or {}
            if d["type"] == "assistant":
                usage = (msg.get("usage") or {}).get("output_tokens", 0) or 0
                for x in msg.get("content") or []:
                    if not isinstance(x, dict):
                        continue
                    if x.get("type") == "tool_use" and x["id"] not in seen:
                        seen.add(x["id"])
                        inp = x.get("input") or {}
                        size = len(json.dumps(inp, ensure_ascii=False))
                        ev.append((t, "call", x["name"], size, usage))
                    elif x.get("type") == "text" and x.get("text", "").strip():
                        ev.append((t, "text", "reply", len(x["text"]), usage))
            elif isinstance(msg.get("content"), list):
                for x in msg["content"]:
                    if isinstance(x, dict) and x.get("type") == "tool_result":
                        ev.append((t, "result", "", 0, 0))
    ev.sort(key=lambda e: e[0])
    return ev


def main():
    src = Path(sys.argv[1])
    lead = sys.argv[2]
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    kids = []
    for m in sorted(src.glob("agent-*.meta.json")):
        meta = json.loads(m.read_text(encoding="utf-8"))
        if meta.get("parentAgentId") == lead:
            kids.append((m.name.removeprefix("agent-").removesuffix(".meta.json"), meta.get("description", "")))
    for aid, desc in kids:
        ev = events(src / f"agent-{aid}.jsonl")
        gaps, last_result = [], None
        for t, kind, name, size, tok in ev:
            if kind == "result":
                last_result = t
            elif last_result is not None and kind in ("call", "text"):
                g = (t - last_result).total_seconds()
                if g > 0:
                    gaps.append((g, name, size))
                last_result = None
        write_s = sum(g for g, n, s in gaps if n in ("Write", "Edit"))
        reply_s = sum(g for g, n, s in gaps if n == "reply")
        total = sum(g for g, _, _ in gaps)
        big = sorted(gaps, reverse=True)[:top]
        print(f"{aid[:8]} {desc[:30]:30} gaps {total:5.0f}s  before-Write {write_s:4.0f}s  before-reply {reply_s:4.0f}s  top "
              + ", ".join(f"{g:.0f}s->{n}({s}ch)" for g, n, s in big))


main()
