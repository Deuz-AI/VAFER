"""Snapshot files on disk (by their URL header) vs. index.tsv vs. cited sources."""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
def norm(u):
    u = re.sub(r"^https?://", "", u.strip().strip("<>").rstrip(").,;")); u = re.sub(r"^www\.", "", u)
    return u.rstrip("/").lower()
for run in map(Path, sys.argv[1:]):
    pages = run / "pages"
    files = {}
    for p in pages.glob("*.txt"):
        head = p.read_text(encoding="utf-8", errors="replace")[:600]
        if head.startswith("URL:"):
            body = p.read_text(encoding="utf-8", errors="replace").split("\n\n", 1)[-1]
            files[norm(head.split("\n", 1)[0][4:])] = (p.name, len(body))
    idx = {}
    for line in (pages / "index.tsv").read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) > 2: idx[norm(parts[0])] = parts[2]
    report = (run / "report.md").read_text(encoding="utf-8")
    m = re.search(r"^#+\s*(Kaynaklar|Sources|Kaynakça)\s*$", report, re.M | re.I)
    cited = {norm(u) for u in re.findall(r"https?://\S+", report[m.end():] if m else "")}
    on_disk = set(files)
    print(f"## {run.parent.parent.parent.name}/{run.name}")
    print(f"snapshot files {len(files)}; index rows {len(idx)}; files missing from index {len(on_disk - set(idx))}; "
          f"index rows w/o file {len(set(idx) - on_disk)}")
    print(f"cited {len(cited)}; cited with a file {len(cited & on_disk)}; cited with no file {len(cited - on_disk)}; "
          f"files never cited {len(on_disk - cited)} ({100*len(on_disk - cited)//max(1,len(on_disk))}%)")
    tiny = sorted((n, u) for u, (f, n) in files.items() if n < 1500)
    print("small snapshot bodies (<1500 chars):", [(n, u[:60], idx.get(u, 'NOT-IN-INDEX'), 'CITED' if u in cited else '') for n, u in tiny])
    for u in sorted(cited - on_disk): print("   cited, no snapshot file:", u[:110])
    print()
