"""Speed lens: per agent, model turns, tool calls per turn, tool time vs generation time.

Usage: python -I speed_turns.py <subagents dir> <lead id> [<lead id> ...]
For each lead and its children: turns (assistant message ids that issued >=1 tool call),
calls/turn, single-call turns, wall, tools-in-flight seconds, generation seconds,
WebSearch/WebFetch/Bash counts, and the time from spawn to first tool call.
Also prints, per researcher, the gap between consecutive turns (median) to show serial latency.
"""
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def analyse(path: Path):
    meta = json.loads(path.with_name(path.stem + ".meta.json").read_text(encoding="utf-8"))
    calls, msgs, first, last = {}, {}, None, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("type") not in ("user", "assistant"):
                continue
            t = ts(d["timestamp"])
            first, last = first or t, t
            msg = d.get("message") or {}
            if d["type"] == "assistant":
                mid = msg.get("id")
                for x in msg.get("content") or []:
                    if isinstance(x, dict) and x.get("type") == "tool_use" and x["id"] not in calls:
                        calls[x["id"]] = [t, None, x["name"], mid]
                        msgs.setdefault(mid, []).append(x["id"])
            elif isinstance(msg.get("content"), list):
                for x in msg["content"]:
                    if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("tool_use_id") in calls:
                        c = calls[x["tool_use_id"]]
                        if c[1] is None:
                            c[1] = t
    ivs = sorted((c[0], c[1]) for c in calls.values() if c[1])
    busy, cs, ce = dt.timedelta(), None, None
    for s, e in ivs:
        if ce is None or s > ce:
            if ce:
                busy += ce - cs
            cs, ce = s, e
        else:
            ce = max(ce, e)
    if ce:
        busy += ce - cs
    wall = (last - first).total_seconds()
    per_turn = [len(v) for v in msgs.values()]
    names = [c[2] for c in calls.values()]
    first_call = min((c[0] for c in calls.values()), default=first)
    # serial gap: time from the last result of turn k to the first call of turn k+1
    turn_rows = []
    for mid, ids in msgs.items():
        starts = [calls[i][0] for i in ids]
        ends = [calls[i][1] for i in ids if calls[i][1]]
        turn_rows.append((min(starts), max(ends) if ends else min(starts)))
    turn_rows.sort()
    gaps = [(b[0] - a[1]).total_seconds() for a, b in zip(turn_rows, turn_rows[1:]) if b[0] >= a[1]]
    return {
        "desc": meta.get("description", "")[:34], "wall": wall, "busy": busy.total_seconds(),
        "turns": len(per_turn), "calls": len(calls), "single": sum(1 for n in per_turn if n == 1),
        "max": max(per_turn, default=0), "ws": names.count("WebSearch"), "wf": names.count("WebFetch"),
        "bash": names.count("Bash") + names.count("PowerShell"),
        "boot": (first_call - first).total_seconds(),
        "gap_med": statistics.median(gaps) if gaps else 0, "gap_sum": sum(gaps),
    }


def main():
    src = Path(sys.argv[1])
    for lead in sys.argv[2:]:
        ids = [lead]
        for m in sorted(src.glob("agent-*.meta.json")):
            if json.loads(m.read_text(encoding="utf-8")).get("parentAgentId") == lead:
                ids.append(m.name.removeprefix("agent-").removesuffix(".meta.json"))
        print(f"== lead {lead[:8]}")
        print("agent    desc                               wall  tools  gen%  turns calls c/turn single max  WS WF Bash boot gapmed gapsum")
        tot = {"turns": 0, "calls": 0, "single": 0}
        for i in ids:
            r = analyse(src / f"agent-{i}.jsonl")
            for k in tot:
                tot[k] += r[k]
            cpt = r["calls"] / r["turns"] if r["turns"] else 0
            gen = 100 * (r["wall"] - r["busy"]) / r["wall"] if r["wall"] else 0
            print(f"{i[:8]} {r['desc']:34} {r['wall']:5.0f} {r['busy']:6.0f} {gen:4.0f}% {r['turns']:6d} {r['calls']:5d} "
                  f"{cpt:6.2f} {r['single']:6d} {r['max']:3d} {r['ws']:3d} {r['wf']:2d} {r['bash']:4d} {r['boot']:4.0f} "
                  f"{r['gap_med']:6.1f} {r['gap_sum']:6.0f}")
        print(f"TOTAL turns {tot['turns']} calls {tot['calls']} single-call turns {tot['single']} "
              f"({100 * tot['single'] / max(tot['turns'], 1):.0f}%)")


main()
