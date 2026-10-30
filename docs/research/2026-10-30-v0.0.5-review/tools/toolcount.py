import json, sys, collections, pathlib
S = pathlib.Path(sys.argv[1])
ids = sys.argv[2:]
grand = collections.Counter()
for aid in ids:
    p = S / f"agent-{aid}.jsonl"
    meta = json.loads((S / f"agent-{aid}.meta.json").read_text(encoding="utf-8"))
    c = collections.Counter()
    first_ts = last_ts = None
    out_tokens = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        ts = e.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        msg = e.get("message") or {}
        if e.get("type") == "assistant":
            u = msg.get("usage") or {}
            out_tokens += u.get("output_tokens", 0) or 0
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    c[b.get("name")] += 1
    grand.update(c)
    print(f"{meta.get('description')[:38]:38s} {first_ts[11:19] if first_ts else '-'}-{last_ts[11:19] if last_ts else '-'} total={sum(c.values()):3d} out_tok={out_tokens:6d} {dict(c.most_common())}")
print("GRAND", sum(grand.values()), dict(grand.most_common()))
