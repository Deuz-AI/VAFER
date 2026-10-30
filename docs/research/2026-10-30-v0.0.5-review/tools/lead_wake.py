"""Print the lead's records between two local times: type, time, and a short text of user/assistant content."""
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
path, t0, t1 = sys.argv[1], sys.argv[2], sys.argv[3]
for line in open(path, encoding="utf-8"):
    d = json.loads(line)
    if d.get("type") not in ("user", "assistant"):
        continue
    t = dt.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")) + dt.timedelta(hours=3)
    s = t.strftime("%H:%M:%S")
    if not (t0 <= s <= t1):
        continue
    msg = d.get("message") or {}
    c = msg.get("content")
    parts = []
    if isinstance(c, str):
        parts.append("TEXT:" + c[:300])
    else:
        for x in c or []:
            if not isinstance(x, dict):
                continue
            if x.get("type") == "text":
                parts.append("TEXT:" + x["text"][:300])
            elif x.get("type") == "tool_use":
                parts.append("CALL:" + x["name"] + ":" + json.dumps(x.get("input"), ensure_ascii=False)[:160])
            elif x.get("type") == "tool_result":
                r = x.get("content")
                r = r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
                parts.append("RESULT:" + r[:200])
    print(s, d["type"], " | ".join(parts).replace("\n", " ")[:600])
