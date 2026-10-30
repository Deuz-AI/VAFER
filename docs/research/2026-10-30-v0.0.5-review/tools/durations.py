import json, sys, pathlib, datetime as dt, collections
S = pathlib.Path(sys.argv[1])
def ts(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
agg = collections.defaultdict(list)
for aid in sys.argv[2:]:
    pend = {}
    for line in (S / f"agent-{aid}.jsonl").read_text(encoding="utf-8").splitlines():
        try: e = json.loads(line)
        except Exception: continue
        c = (e.get("message") or {}).get("content")
        if not isinstance(c, list) or not e.get("timestamp"): continue
        for b in c:
            if not isinstance(b, dict): continue
            if b.get("type") == "tool_use":
                name = b["name"]
                cmd = (b.get("input") or {}).get("command", "")
                if name == "Bash":
                    name = "Bash:fetch" if "vafer_check.py fetch" in cmd or ("vafer_check" in cmd and " fetch " in cmd) else "Bash:other"
                pend[b["id"]] = (name, ts(e["timestamp"]), cmd.count("http"))
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in pend:
                name, t0, nurl = pend.pop(b["tool_use_id"])
                agg[name].append(((ts(e["timestamp"]) - t0).total_seconds(), nurl))
for k, v in sorted(agg.items()):
    secs = [x for x, _ in v]
    extra = f" urls={sum(n for _, n in v)}" if k == "Bash:fetch" else ""
    print(f"{k:12s} n={len(v):3d} total={sum(secs):7.0f}s mean={sum(secs)/len(v):6.1f}s max={max(secs):6.1f}s{extra}")
