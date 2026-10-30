"""Probe: if an uncited sentence (or table row) inherits the citations of its paragraph (or table),
how many 'uncited' flags turn into matched figures, and how many into mismatches?

Usage: python -I inherit_probe.py <path to vafer_check.py> <run>
Imports vafer_check read-only from its folder; never writes into the run.
"""
import importlib.util
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("vc", sys.argv[1])
vc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vc)
run = Path(sys.argv[2])
text = vc.read_text(run / "report.md")
body, sources = vc.parse_report(text)
checker = vc.Checker(run)

# blocks: paragraphs (blank-line separated) and tables (consecutive | lines)
blocks, cur = [], []
for line in body:
    if not line.strip() or vc.HEADING.match(line):
        if cur:
            blocks.append(cur)
        cur = []
        continue
    if cur and (line.lstrip().startswith("|") != cur[-1].lstrip().startswith("|")):
        blocks.append(cur)
        cur = []
    cur.append(line)
if cur:
    blocks.append(cur)

stats = {"uncited_with_numbers": 0, "inherit_available": 0, "all_match": 0, "some_mismatch": 0, "no_cite_in_block": 0}
mism = []
for blk in blocks:
    sents = vc.sentences(blk)
    block_cites = [n for s in sents for m in vc.CITE.finditer(s) for n in vc.expand_cites(m.group(1))]
    urls = [sources[n] for n in dict.fromkeys(block_cites) if n in sources]
    for s in sents:
        if vc.CITE.search(s):
            continue
        nums = [n for n in vc.numbers(vc.mask(s)) if not vc.is_year(n) and not vc.is_small_int(n)]
        if not nums:
            continue
        stats["uncited_with_numbers"] += 1
        ev = [u for u in urls if checker.has_evidence(u)]
        if not ev:
            stats["no_cite_in_block"] += 1
            continue
        stats["inherit_available"] += 1
        bad = [n.text.strip() for n in nums if not any(vc.num_matches(n, checker.pool(u)) for u in ev)]
        if bad:
            stats["some_mismatch"] += 1
            mism.append((s[:110], bad))
        else:
            stats["all_match"] += 1
print(stats)
for s, bad in mism:
    print("MISMATCH:", bad, "|", s)
