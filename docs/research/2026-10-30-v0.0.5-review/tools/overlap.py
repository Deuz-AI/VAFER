import json, sys, pathlib, re
S = pathlib.Path(sys.argv[1])
sys.path.insert(0, r"C:/Users/VECTOR/Documents/GitHub/VAFER/skills/vafer-research/scripts")
sys.dont_write_bytecode = True
from vafer_check import norm_url
wf, fe = set(), set()
for aid in sys.argv[2:]:
    for line in (S / f"agent-{aid}.jsonl").read_text(encoding="utf-8").splitlines():
        try: e = json.loads(line)
        except Exception: continue
        c = (e.get("message") or {}).get("content")
        if not isinstance(c, list) or e.get("type") != "assistant": continue
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input") or {}
                if b["name"] == "WebFetch" and inp.get("url"):
                    wf.add(norm_url(inp["url"]))
                elif b["name"] == "Bash" and "vafer_check" in inp.get("command", "") and "fetch" in inp.get("command", ""):
                    for u in re.findall(r"https?://[^\s\"']+", inp["command"]):
                        fe.add(norm_url(u))
print("WebFetch URLs:", len(wf), " snapshot URLs:", len(fe), " both:", len(wf & fe), " WebFetch-only:", len(wf - fe))
