#!/usr/bin/env python
"""vafer_assemble: the mechanical steps of a vafer-deep-research run, built on vafer_check.py.

Usage:
  python vafer_assemble.py fetch <run> <url> [<url> ...] [--check <path to vafer_check.py>]
  python vafer_assemble.py lint <run> <id> [--check <path to vafer_check.py>]
  python vafer_assemble.py build <run> [--order s1,s2,...] [--sources Kaynaklar]
  python vafer_assemble.py check <run> [--check <path to vafer_check.py>]

fetch  vafer_check's fetch with parallel downloads; reads PDFs through pypdf when pdftotext is missing.
lint   vafer_check's figure, quote and citation checks on one section draft, so the researcher who
       wrote it can fix it while the pages are still fresh.
build  joins <run>/front.md (optional), <run>/sections/<id>.md in order and <run>/back.md (optional)
       into <run>/report.md. Every part cites with its own local numbers [1], [2] and ends with its own
       "## Sources" list; build renumbers by first citation and writes one list.
check  vafer_check's report check; answers the flags of claims already marked † and prints the rest.

Stdlib only; pypdf is used when present. Findings are printed, not enforced: every command exits 0
unless a file is missing (exit 2).
"""
from __future__ import annotations

import argparse, concurrent.futures, datetime as dt, io, re, shutil, sys, time, urllib.parse
from pathlib import Path

TIMEOUT, DEADLINE = 20, 45  # seconds: per network operation, and for one whole download

CITE = re.compile(r"\[(\d+(?:\s*[-–—]\s*\d+)?(?:\s*[,;]\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]")
URL = re.compile(r"https?://[^\s<>()\[\]\"“”'«»]+")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
ENTRY = re.compile(r"^\s*(?:[-*]\s*)?\[(\d+)\]:?\s+(.*)$|^\s*(\d+)\.\s+(.*)$")
TITLES = ("sources", "references", "kaynaklar", "kaynakça")
SIBLING = Path(__file__).resolve().parents[2] / "vafer-research" / "scripts" / "vafer_check.py"

def norm_url(url: str) -> str:
    """Same key as vafer_check: no scheme, www., fragment, trailing slash or utm_* params."""
    parts = urllib.parse.urlsplit(url.strip().rstrip(".,;:"))
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    host = parts.netloc.lower().removeprefix("www.")
    return host + parts.path.rstrip("/") + ("?" + urllib.parse.urlencode(query) if query else "")

def expand(inner: str) -> list:
    out = []
    for piece in re.split(r"[,;]", inner):
        bounds = [int(x) for x in re.split(r"[-–—]", piece) if x.strip()]
        out.extend(range(bounds[0], bounds[-1] + 1) if len(bounds) == 2 else bounds)
    return out

def split_part(text: str) -> tuple:
    """(body lines, {local number: (url, entry text)}) of one draft."""
    lines = text.lstrip("﻿").replace("\r\n", "\n").split("\n")
    heads = [i for i, line in enumerate(lines)
             if (h := HEADING.match(line)) and h.group(1).strip().rstrip(":").casefold() in TITLES]
    if not heads:
        return lines, {}
    sources = {}
    for line in lines[heads[-1] + 1:]:
        m = ENTRY.match(line)
        url = URL.search(line) if m else None
        if url:
            sources.setdefault(int(m.group(1) or m.group(3)),
                               (url.group(0).rstrip(".,;:"), (m.group(2) or m.group(4)).strip()))
    return lines[:heads[-1]], sources

def natural(path: Path) -> list:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path.stem)]

def build(run: Path, order=None, title="Kaynaklar") -> dict:
    """Write <run>/report.md; return counts and warnings."""
    drafts = {p.stem: p for p in sorted((run / "sections").glob("*.md"), key=natural)}
    ids = [i for i in order if i in drafts] if order else list(drafts)
    warnings = [f"--order names {i}, but sections/{i}.md does not exist" for i in order or [] if i not in drafts]
    warnings += [f"sections/{i}.md is not in --order and was left out" for i in drafts if i not in ids]
    parts = [("front.md", run / "front.md")] + [(f"sections/{i}.md", drafts[i]) for i in ids] + [("back.md", run / "back.md")]
    loaded = [(name, *split_part(path.read_text(encoding="utf-8"))) for name, path in parts if path.is_file()]
    section_urls = {norm_url(url) for name, _, local in loaded if name.startswith("sections/")
                    for url, _ in local.values()}
    registry, bodies, words = {}, [], 0

    def number(name, n, local):
        if n not in local:
            warnings.append(f"{name}: [{n}] has no line under its Sources heading; the marker was dropped")
            return None
        url, entry = local[n]
        return registry.setdefault(norm_url(url), (len(registry) + 1, entry))[0]

    for name, lines, local in loaded:
        cited = set()

        def swap(m):
            cited.update(expand(m.group(1)))
            nums = sorted({g for n in expand(m.group(1)) if (g := number(name, n, local))})
            return "[" + ", ".join(map(str, nums)) + "]" if nums else ""

        body = "\n".join(CITE.sub(swap, line) for line in lines).strip()
        if not name.startswith("sections/"):
            warnings += [f"{name}: [{n}] {local[n][0]} is cited by no section" for n in sorted(cited & set(local))
                         if norm_url(local[n][0]) not in section_urls]
        warnings += [f"{name}: source [{n}] is listed but never cited" for n in sorted(set(local) - cited)]
        words += len(body.split())
        bodies.append(body)
    entries = [f"[{n}] {entry}" for n, entry in sorted(registry.values())]
    report = "\n\n".join(b for b in bodies if b) + f"\n\n## {title}\n\n" + "\n".join(entries) + "\n"
    (run / "report.md").write_text(report, encoding="utf-8", newline="")
    return {"sections": len(ids), "words": words, "sources": len(entries), "warnings": warnings}

def load_check(check_script: Path):
    sys.path.insert(0, str(check_script.resolve().parent))
    import vafer_check
    return vafer_check

def pypdf_text(raw: bytes):
    """PDF text through pypdf; None when pypdf is missing or cannot read the file."""
    try:
        import pypdf
        return "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(io.BytesIO(raw)).pages)
    except Exception:  # not installed, encrypted or damaged: the caller reports pdf-no-text
        return None

class Bounded:
    """A response whose whole body must arrive within DEADLINE seconds."""
    def __init__(self, resp):
        self.resp, self.headers, self.end = resp, resp.headers, time.monotonic() + DEADLINE
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.resp.close()
    def read(self) -> bytes:
        chunks = []
        while chunk := self.resp.read(65536):
            chunks.append(chunk)
            if time.monotonic() > self.end:
                raise TimeoutError("slow download")
        return b"".join(chunks)

def fetch(run: Path, urls, check_script: Path) -> int:
    """vafer_check's fetch, with bounded downloads in parallel so one slow host cannot hold up a batch."""
    vc = load_check(check_script)
    if not shutil.which("pdftotext"):
        vc.pdf_text = pypdf_text
    opener = vc.urlopen
    vc.urlopen = lambda req, timeout=TIMEOUT: Bounded(opener(req, timeout=min(timeout, TIMEOUT)))
    pages = run / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda url: vc.fetch_one(url, pages), urls))
    finally:
        vc.urlopen = opener
    index = pages / "index.tsv"  # read after the downloads: other researchers update it too
    lines = vc.read_text(index).splitlines() if index.exists() else []
    rows = {parts[0]: parts for parts in (line.split("\t") for line in lines) if parts[0]}
    for url, (status, name, chars) in zip(urls, results):
        rows[url] = [url, name, status, dt.date.today().isoformat()]
        saved = f" (saved {name}, {chars} chars)" if name else ""
        print(f"ok {name} {chars} {url}" if status == "ok" else f"failed {status}{saved} {url}")
    vc.write_text(index, "".join("\t".join(r) + "\n" for r in rows.values()))
    return 0

def flag_rows(vc, path: Path) -> list:
    """(line index, cells) of every flag row in check.md."""
    rows = []
    for i, line in enumerate(vc.read_text(path).splitlines()):
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 6 and re.fullmatch(r"F\d+", cells[0]):
            rows.append((i, cells))
    return rows

def check(run: Path, check_script: Path) -> tuple:
    """vafer_check's report check; flags on claims already marked † are answered, the open ones returned."""
    vc = load_check(check_script)
    result, path = vc.check(run), run / "check.md"
    body, _ = vc.parse_report(vc.read_text(run / "report.md"))
    marked = {vc.excerpt(s) for s in vc.sentences(body) if "†" in s}
    lines, answered = vc.read_text(path).splitlines(), 0
    for i, cells in flag_rows(vc, path):
        if cells[5] == "disposition:" and cells[2] in marked:
            lines[i] = lines[i][: lines[i].rindex("disposition:")] + "disposition: † (marked in the report) |"
            answered += 1
    if answered:
        vc.write_text(path, "\n".join(lines) + "\n")
        result = vc.check(run)  # run again so that the summary counts these flags as answered
    return result, [cells for _, cells in flag_rows(vc, path) if cells[5] == "disposition:"]

def lint(run: Path, sid: str, check_script: Path) -> list:
    """Flags for one section draft, from vafer_check's own checks."""
    vc = load_check(check_script)
    body, sources = vc.parse_report(vc.read_text(run / "sections" / f"{sid}.md"))
    checker, seen = vc.Checker(run), {}
    for sentence in vc.sentences(body):
        cited = checker.check_sentence(sentence, sources)
        for n in cited:
            seen.setdefault(n, sentence)
        urls = [sources[n] for n in cited if n in sources]
        if urls and all(checker.is_lead(u) for u in urls):
            checker.flag("lead-only", sentence, urls, "every cited source is lead-class (wiki, forum, blog, aggregator)")
    for n, sentence in seen.items():
        if n not in sources:
            checker.flag("dangling", sentence, [], f"[{n}] has no line under ## Sources")
    for n, url in sorted(sources.items()):
        if n not in seen:
            checker.flag("unused", f"[{n}] {url}", [url], "listed under ## Sources but never cited")
        if not checker.has_evidence(url):
            checker.flag("unverifiable", f"[{n}] {url}", [url], "no page snapshot and no receipt for this URL")
    for line in body:
        for m in vc.LEAK.finditer(line):
            checker.flag("label-leak", line, [], f"method word `{m.group(0)}` in the section text")
    return checker.flags

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python vafer_assemble.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_p = sub.add_parser("build", help="merge front.md, sections and back.md into report.md")
    build_p.add_argument("run", type=Path)
    build_p.add_argument("--order", default="", help="comma-separated section ids")
    build_p.add_argument("--sources", default="Kaynaklar", help="heading of the merged sources list")
    lint_p = sub.add_parser("lint", help="check one section draft against receipts and snapshots")
    lint_p.add_argument("run", type=Path)
    lint_p.add_argument("id")
    fetch_p = sub.add_parser("fetch", help="download pages into <run>/pages, PDFs included")
    fetch_p.add_argument("run", type=Path)
    fetch_p.add_argument("urls", nargs="+")
    check_p = sub.add_parser("check", help="check report.md and print the flags that still need an answer")
    check_p.add_argument("run", type=Path)
    for p in (lint_p, fetch_p, check_p):
        p.add_argument("--check", type=Path, default=SIBLING, help="path to vafer_check.py")
    args = parser.parse_args(argv)
    if args.cmd in ("fetch", "check") and not args.check.is_file():
        print(f"error: missing {args.check}", file=sys.stderr)
        return 2
    if args.cmd == "fetch":
        return fetch(args.run, args.urls, args.check)
    if args.cmd == "check":
        if not (args.run / "report.md").is_file():
            print(f"error: missing {args.run / 'report.md'}", file=sys.stderr)
            return 2
        result, still_open = check(args.run, args.check)
        print(f"{result['summary']}\nSource mix: {result['mix']}")
        for cells in still_open[:60]:
            print(f"{cells[0]} {cells[1]}: {cells[4]} | in: {cells[2]}")
        print(f"{len(still_open)} open: answer each in the disposition cell of check.md" if still_open else "no open flags")
        return 0
    if args.cmd == "build":
        if not list((args.run / "sections").glob("*.md")):
            print(f"error: no section drafts in {args.run / 'sections'}", file=sys.stderr)
            return 2
        result = build(args.run, [i.strip() for i in args.order.split(",") if i.strip()], args.sources)
        print(f"built report.md: {result['sections']} sections, {result['words']} words, {result['sources']} sources")
        print("\n".join(f"warning: {w}" for w in result["warnings"]) or "no warnings")
        return 0
    if not (args.run / "sections" / f"{args.id}.md").is_file() or not args.check.is_file():
        print(f"error: missing sections/{args.id}.md or {args.check}", file=sys.stderr)
        return 2
    flags = lint(args.run, args.id, args.check)
    for f in flags[:60]:
        print(f"{f['kind']}: {f['detail']} | in: {f['excerpt']}")
    print(f"lint: {len(flags)} flag{'s' if len(flags) != 1 else ''}" if flags else "lint: clean")
    return 0

if __name__ == "__main__":
    sys.exit(main())
