"""Per agent: wall time, time with at least one tool call in flight (union of intervals), the rest
(model thinking/writing), the slowest calls, and output tokens.

Usage: python -I busy.py <subagents dir> <agent id> [<agent id> ...]
An agent id may be followed by ":children" to include every child of that lead.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def analyse(path: Path):
    meta = json.loads(path.with_name(path.stem + ".meta.json").read_text(encoding="utf-8"))
    calls, first, last, out_tok, mids = {}, None, None, 0, set()
    big_writes = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("type") not in ("user", "assistant"):
                continue
            t = ts(d["timestamp"])
            first, last = first or t, t
            msg = d.get("message") or {}
            if d["type"] == "assistant":
                if msg.get("id") not in mids:
                    mids.add(msg.get("id"))
                    out_tok += (msg.get("usage") or {}).get("output_tokens", 0) or 0
                for x in msg.get("content") or []:
                    if isinstance(x, dict) and x.get("type") == "tool_use" and x["id"] not in calls:
                        inp = x.get("input") or {}
                        calls[x["id"]] = [t, None, x["name"], inp]
                        if x["name"] == "Write":
                            big_writes.append((len(inp.get("content", "")), inp.get("file_path", "")[-40:]))
            elif isinstance(msg.get("content"), list):
                for x in msg["content"]:
                    if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in calls:
                        c = calls[x["tool_use_id"]]
                        if c[1] is None:
                            c[1] = t
    ivs = sorted((c[0], c[1]) for c in calls.values() if c[1])
    busy, cur_s, cur_e = dt.timedelta(), None, None
    for s, e in ivs:
        if cur_e is None or s > cur_e:
            if cur_e:
                busy += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e:
        busy += cur_e - cur_s
    wall = (last - first).total_seconds()
    slow = sorted(((c[1] - c[0]).total_seconds(), c[2]) for c in calls.values() if c[1])[-3:]
    return meta, wall, busy.total_seconds(), out_tok, len(calls), slow, big_writes


def main():
    src = Path(sys.argv[1])
    ids = []
    for arg in sys.argv[2:]:
        if arg.endswith(":children"):
            lead = arg.split(":")[0]
            ids.append(lead)
            for m in sorted(src.glob("agent-*.meta.json")):
                if json.loads(m.read_text(encoding="utf-8")).get("parentAgentId") == lead:
                    ids.append(m.name.removeprefix("agent-").removesuffix(".meta.json"))
        else:
            ids.append(arg)
    tw = tb = 0
    for i in ids:
        meta, wall, busy, tok, n, slow, writes = analyse(src / f"agent-{i}.jsonl")
        tw += wall
        tb += busy
        print(f"{i[:8]} {meta.get('description', '')[:34]:34} wall {wall:6.0f}s tools-in-flight {busy:5.0f}s "
              f"model {wall - busy:5.0f}s ({100 * (wall - busy) / wall:3.0f}%) calls {n:3d} out_tok {tok:6d} "
              f"slowest {[(int(s), nm) for s, nm in slow]} writes {[w for w in writes if w[0] > 3000]}")
    print(f"sum wall {tw:.0f}s, tools {tb:.0f}s, model {tw - tb:.0f}s ({100 * (tw - tb) / tw:.0f}%)")


main()
