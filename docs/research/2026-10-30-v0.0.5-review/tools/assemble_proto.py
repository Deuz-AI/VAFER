"""Prototype of a `vafer_check.py assemble` command (speed-lens probe, not for the repo).

Usage: python -I assemble_proto.py <run> <section ids in order...>
Concatenates sections/<id>.md in the given order (optionally _top.md first and _end.md last),
turns [URL] citations into [n] in first-appearance order, writes report.md with a Sources list
whose titles come from the snapshot's first body line. Prints counts.
"""
import re
import sys
from pathlib import Path

URL_CITE = re.compile(r"\[(https?://[^\]\s]+)\]")


def snapshot_titles(run: Path) -> dict:
    titles = {}
    for p in (run / "pages").glob("*.txt"):
        text = p.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("URL:"):
            continue
        url = text.split("\n", 1)[0][4:].strip()
        body = text.split("\n\n", 1)[1] if "\n\n" in text else ""
        first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        titles[url] = first[:120]
    return titles


def main():
    run, ids = Path(sys.argv[1]), sys.argv[2:]
    parts = []
    for name in ["_top", *ids, "_end"]:
        f = run / "sections" / f"{name}.md"
        if f.exists():
            parts.append(f.read_text(encoding="utf-8").strip())
    text = "\n\n".join(parts)
    order, num = [], {}

    def repl(m):
        url = m.group(1).rstrip(".,;:")
        if url not in num:
            num[url] = len(order) + 1
            order.append(url)
        return f"[{num[url]}]"

    text = URL_CITE.sub(repl, text)
    text = re.sub(r"\](\s*)\[(\d+)\]", lambda m: f"]{m.group(1)}[{m.group(2)}]", text)
    titles = snapshot_titles(run)
    src = ["", "## Kaynaklar", ""] + [f"[{n}] {titles.get(u, '')} {u}".replace("  ", " ") for n, u in
                                      ((num[u], u) for u in order)]
    (run / "report.md").write_text(text + "\n" + "\n".join(src) + "\n", encoding="utf-8", newline="")
    print(f"sections {len(parts)}, words {len(text.split())}, sources {len(order)}")


main()
