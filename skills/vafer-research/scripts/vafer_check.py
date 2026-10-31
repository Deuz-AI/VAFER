#!/usr/bin/env python
"""vafer_check: snapshot cited pages and check a vafer-research report against them.

Usage:
  python scripts/vafer_check.py fetch <run> [--find "a|b|c"] <url> [<url> ...]
  python scripts/vafer_check.py find <run> "a|b|c" [<url> ...]
  python scripts/vafer_check.py check <run> [--section <id>]
  python scripts/vafer_check.py assemble <run> [--title "<Sources heading>"]
  python scripts/vafer_check.py diff <old.md> <new.md>

Stdlib only; only `fetch` uses the network. `check` is advisory (exit 0; 2 when report.md or the draft is missing;
`--section` writes nothing). `assemble` exits 2 without sections/. `diff` exits 1 when an edit lost or changed a number,
citation, quote, source entry or marker line, or detached a citation; additions alone pass.
"""
from __future__ import annotations

import argparse, codecs, concurrent.futures, contextlib, datetime as dt, hashlib, html.parser, itertools, os, re
import shutil, subprocess, sys, tempfile, threading, time, unicodedata, urllib.error, urllib.parse, urllib.request
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"
PLAIN_UA = "vafer-check/0.1 (python-urllib)"
urlopen, sleep, HOSTS = urllib.request.urlopen, time.sleep, {}  # tests monkeypatch urlopen and sleep; host -> Semaphore
LOCK_WAIT, LOCK_STALE, DEADLINE = 30, 60, 30  # s: a lock waiter's patience, a dead fetch's lock age, one URL's download

BOMS = ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16"))
URL_RX = re.compile(r"(?:https?://|file:///)(?:[^\s<>()\[\]\"“”'«»]|'(?=\w)|\([^\s<>()\[\]\"“”'«»]*\))+")  # (…) in pairs
CITE = re.compile(r"\[(\d+(?:\s*[-–—]\s*\d+)?(?:\s*[,;]\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]")
NUM = re.compile(r"(?<![\w.,])(?P<neg>[-−](?=\d))?"
                 r"(?P<n>\d{1,3}(?:[.,\u00a0\u202f\u2009 ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?!\d)")
OPS = re.compile(r"[×*·/÷+−]|(?<![^\W\d_])x(?![^\W\d_])|(?<!\S)-(?!\S)")
OPMAP = {"×": "*", "*": "*", "·": "*", "x": "*", "/": "/", "÷": "/", "+": "+", "−": "-", "-": "-"}
QUOTE_RX = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|«([^»\n]+)»|„([^“”\n]+)[“”]')
RECEIPT = re.compile(r'^\s*[-*+]\s+(?:.*?—\s*(?=["“„]))?.*?["“„](?P<span>.+)["”“]\s*<?(?P<url>(?:https?:|file:/)//[^\s<>]+)>?')
URL_CITE = re.compile(r"\[((?:https?|file):[^\]\s]+(?:\s*[,;]\s*(?:https?|file):[^\]\s]+)*)\]")  # sections/<id>.md
*MONTHS, ORDS = (g.split() for g in (  # month names, one group per month (tr en es fr de it pt); ordinal words
    "ocak january jan enero janvier januar gennaio janeiro|şubat february feb febrero février februar febbraio fevereiro|"
    "mart march mar marzo mars märz março|nisan april apr abril avril aprile|mayıs may mayo mai maggio maio|haziran june "
    "jun junio juin juni giugno junho|temmuz july jul julio juillet juli luglio julho|ağustos august aug agosto août|eylül "
    "september sept sep septiembre setiembre septembre settembre setembro|ekim october oct octubre octobre oktober ottobre "
    "outubro|kasım november nov noviembre novembre novembro|aralık december dec diciembre décembre dezember dicembre "
    "dezembro|first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth "
    "fifteenth sixteenth seventeenth eighteenth nineteenth twentieth twenty-first").split("|"))
MON, ORD, OM = "|".join(w for g in MONTHS for w in g), "|".join(ORDS[::-1]), r"(?:\.?º|\.|st|nd|rd|th|er|e|ª)"
# one-token figures: ISO, dotted and written (also yearless) dates; Roman, ordinal (never cardinal) centuries; clock
# times (`special`). A range head (`d0`, `c0`: "17–18 Ağustos", "16.–19. yüzyıl") gives the token a key per end.
SPECIAL = re.compile(r"(?i)(?<![\w.,:%])(?:(?P<iy>\d{4})-(?P<im>\d{1,2})-(?P<id>\d{1,2})"
                     r"|(?P<dd>\d{1,2})[./](?P<dm>\d{1,2})[./](?P<dy>\d{4})"
                     rf"|(?:(?P<d0>\d{{1,2}}){OM}?\s*[-–—]\s*)?(?P<td>\d{{1,2}}){OM}?\s+(?:(?:of|de|di)\s+)?(?P<tm>{MON})"
                     rf"(?![^\W\d_])\.?(?:,?\s+(?:del?\s+)?(?P<ty>\d{{4}}))?|(?P<em>{MON})\.?\s+(?P<ed>\d{{1,2}})"
                     rf"(?=st|nd|rd|th|,?\s+\d{{4}}(?!\d))(?:st|nd|rd|th)?(?:,?\s+(?P<ey>\d{{4}}))?"  # Month Day: 5th or a year
                     rf"|(?:(?P<c0>\d{{1,2}}|[IVXLC]{{1,6}}|{ORD}){OM}?\s*[-–—]\s*)?(?P<c>\d{{1,2}}(?={OM})|[IVXLC]{{1,6}}|{ORD})"
                     rf"{OM}?[\s-]*(?:yüzyıl|yy\b|century|centuries|siglo|siècle|jahrhundert|jh\b|secol|século|asır|asr)"
                     r"|(?:siglo|século|secolo)s?\s+(?-i:(?P<c2>[IVXLC]{1,6})(?:\s*[-–—]\s*(?P<c3>[IVXLC]{1,6}))?)(?![^\W\d_])"
                     r"|(?P<h>[01]?\d|2[0-3])(?P<sep>[:.])(?P<mi>[0-5]\d))(?!\d)")
PRICE = re.compile(r"(?:yüzde|%|\btl|[$€₺£]|dolar|euro)\s*(?:\S+\s+)?$", re.I)  # a rate or price word before a number
SEVERITY = {**dict.fromkeys("equation-wrong b-unopened dangling quote-missing marker-missing".split(), "high"),
            **dict.fromkeys("lead-only number-mismatch uncited unverifiable label-leak".split(), "medium")}  # else low
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
SOURCES_MARK, END_MARK = "<!-- vafer:sources -->", "<!-- vafer:end -->"
PLAN_ID = re.compile(r"^#{2,4}\s+([A-Za-z]{1,3}\d{1,2})\b")  # a plan.md heading's section id
COMMENT = re.compile(r"^\s*<!--.*-->\s*$")
SOURCE_ENTRY = re.compile(r"^\s*(?:[-*]\s*)?\[(\d+)\]:?\s+(.*)$|^\s*(\d+)\.\s+(.*)$")
CHECK_LINE = re.compile(r"(?P<pre>Source check[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
MIX_LINE = re.compile(r"(?P<pre>Source mix[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
LABELS = {**{k: k for k in ("primary", "official", "scholarly", "press", "lead", "derived")}, "secondary": "press"}
MIX = ("primary", "official", "scholarly", "press", "lead", "unlabelled")
LEAD_DOMAINS = ("wikipedia.org", "wikiwand.com", "quora.com", "reddit.com", "medium.com", "blogspot.com",
                "wordpress.com", "eksisozluk.com", "fandom.com", "news.google.com", "msn.com", "yahoo.com")
JUNK = re.compile(r"^\W*(?:(?:skip|jump) to\b|search\b|(?:e-?)?(?:issn|isbn)\b)|:$|\|.*\||^[\W\d]*$", re.I)  # no title
LIST_MARK = re.compile(r"^\s*(?:\d+[.)]|[-*+]|>)\s+")
# sentence end: mark plus footnote markers (.³ .[^3]) before space + capital; never a period before a digit
SENT_END = re.compile(r"[.!?…](?:[⁰¹²³⁴-⁹]+|\[\^\d+\])*(?=\s+[\[(“\"«„A-ZÇĞİÖŞÜÂÎÛΑ-ΩА-Я])|[!?…](?=\s+\d)")
# a part ending in one of these (Roman numeral, single letter, short abbreviation, M.Ö.) never ends a sentence
ABBR = re.compile(r"(?:^|[\s(\[\"“'])(?:[IVXLCDM]{1,6}|[^\W\d_]|(?i:dr|prof|doç|yrd|av|op|müh|sn|hz|vb|vs|vd|bkz|yy|cmd"
                  r"|ss|örn|no|nr|st|mr|mrs|ms|ltd|şti|inc|co|jr|vol|pp|ed|krş|çev|haz))\.$|(?:[^\W\d_]\.){2,}$")
SPELL = re.compile(r"(?<![\w.,])(?:(?P<n>\d+(?:[.,]\d+)?)\s*|(?P<yuz>yüz)\s+)?"
                   r"(?P<m>bin|thousand|milyon|million|milyar|billion|trilyon|trillion)(?![^\W\d_])"
                   r"(?:(?<=bin|and)\s+(?P<tail>\d{1,3})(?!\d|[.,]\d))?", re.I)
SCALE = {"bin": 3, "thousand": 3, "milyon": 6, "million": 6, "milyar": 9, "billion": 9, "trilyon": 12, "trillion": 12}
OLE_MAGIC = b"\xd0\xcf\x11\xe0"
LEAK = re.compile(r"\[(?:GAP|prior|brainstorm)\]|\b(?:COVERED|PARTIAL|NOT-FOUND|NOT SEARCHED)\b"
                  r"|\b(?:notes|sections)/[\w.-]+\.md\b|\bpages/[\w-]+\.txt\b")  # internal tokens only
QMAP = str.maketrans("“”„«»‘’‚‐‑‒–—―−", '"""""' + "'''" + "-" * 7)  # curly quotes and dashes to plain ones
QUOTE_FLAGS = {"near": ("quote-near", "matches only after Turkish-aware case folding"),
               "missing": ("quote-missing", "quoted span not found in cited snapshots or receipts")}
Num = namedtuple("Num", "start end text cands")

def setup_console() -> None:  # UTF-8 on stdout/stderr: Windows consoles default to a legacy code page
    for stream in (s for s in (sys.stdout, sys.stderr) if hasattr(s, "reconfigure")):
        stream.reconfigure(encoding="utf-8", errors="replace")
def decode_bytes(data: bytes, hints=()) -> tuple:  # by BOM, then the hinted charsets, UTF-8, windows-1254
    bom = next((enc for mark, enc in BOMS if data.startswith(mark)), None)
    for enc in filter(None, [bom, *hints, "utf-8"]):
        with contextlib.suppress(LookupError, UnicodeDecodeError):
            return data.decode(enc).lstrip("\ufeff"), enc
    return data.decode("cp1254", errors="replace"), "windows-1254"
def read_text(path) -> str:  # a local text file, honouring UTF-8/UTF-16 BOMs
    return decode_bytes(Path(path).read_bytes())[0]
def write_text(path, text: str) -> None:  # UTF-8, without newline translation
    Path(path).write_text(text, encoding="utf-8", newline="")
def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
def tr_fold(text: str) -> str:
    return text.replace("İ", "i").replace("I", "i").replace("ı", "i").casefold()
MONTH = {tr_fold(w): i for i, g in enumerate(MONTHS, 1) for w in g}  # folded month name -> month number

def norm_url(url: str) -> str:  # no scheme, www., fragment, trailing slash, utm_* params or %-escapes
    parts = urllib.parse.urlsplit(url.strip().rstrip(".,;:"))
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    host = parts.netloc.lower().removeprefix("www.")
    return host + urllib.parse.unquote(parts.path).rstrip("/") + ("?" + urllib.parse.urlencode(query) if query else "")

class _HTMLText(html.parser.HTMLParser):
    """HTML to plain text: blocks on their own lines, table rows as `a | b | c`. `meta` keeps each <meta> content by
    name or property, and the text of the first <title> before <body> as "<title>" (`lasttag` is the open tag)."""
    SKIP = {"script", "style", "nav", "noscript", "template", "svg", "head"}
    BLOCK = set("p div br li h1 h2 h3 h4 h5 h6 section article header footer ul ol table blockquote pre dt dd main aside "
                "figure figcaption form hr title caption".split())
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.buf, self.skip, self.row, self.cell, self.meta = [], [], 0, None, None, {}
    def handle_starttag(self, tag, attrs):
        if tag == "meta" and (a := dict(attrs)).get("content"):
            self.meta.setdefault((a.get("name") or a.get("property") or "").lower(), a["content"])
        if tag == "body":
            self.skip = 0
            self.meta.setdefault("<title>", "")  # a <title> in the body labels an svg icon
        if tag in self.SKIP:
            self.skip += 1
        elif self.skip:
            return
        elif tag in ("tr", "td", "th"):
            if tag == "tr" or self.row is None:  # a cell outside a row opens one
                self.end_row()
                self.flush()
                self.row = []
            if tag != "tr":
                self.close_cell()
                self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")
        elif tag in self.BLOCK and self.cell is None:
            self.flush()
    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif self.skip:
            return
        elif tag in ("td", "th"):
            self.close_cell()
        elif tag in ("tr", "table"):
            self.end_row()
        elif tag in self.BLOCK and self.cell is None:
            self.flush()
    def handle_data(self, data):
        if self.lasttag == "title" and "<title>" not in self.meta:
            self.meta["<title>"] = data
        if not self.skip:
            (self.cell if self.cell is not None else self.buf).append(data)
    def close_cell(self):
        if self.cell is not None and self.row is not None:
            self.row.append(squash("".join(self.cell)))
        self.cell = None
    def end_row(self):
        self.close_cell()
        if self.row and any(self.row):
            self.lines.append(" | ".join(self.row))
        self.row = None
    def flush(self):
        text, self.buf = squash("".join(self.buf)), []
        if text:
            self.lines.append(text)
    def text(self) -> str:
        self.close()
        self.end_row()
        self.flush()
        return "\n".join(self.lines)
def html_to_text(markup: str) -> tuple:  # (text, title): citation_title or og:title meta, else the first <title>
    (parser := _HTMLText()).feed(markup)
    return parser.text(), squash(next(filter(None, map(parser.meta.get, ("citation_title", "og:title", "<title>"))), ""))

def pdf_text(raw: bytes, layout: bool = False, touch=lambda: None) -> str | None:
    """pdftotext in reading order (≤ 50 s) or with `-layout` (≤ 30 s), after `touch`; None if missing, failed or late."""
    if not (exe := shutil.which("pdftotext")):
        return None
    touch()
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / "in.pdf", Path(tmp) / "out.txt"
        src.write_bytes(raw)
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            subprocess.run([exe, *["-layout"][:layout], "-enc", "UTF-8", str(src), str(out)], check=True,
                           capture_output=True, timeout=30 if layout else 50)
            return read_text(out)
    return None

def download(url: str):
    """(raw, content_type, header_charset), or raise RuntimeError(reason). 2 at a time per host, DEADLINE s per URL in
    all; a 403 retries with a plain agent; 429/503 wait Retry-After (≤ 10 s), else 2 s then 5 s. Non-ASCII is escaped."""
    agents, waits, ascii_url = [BROWSER_UA, PLAIN_UA], [2, 5], urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~")
    with HOSTS.setdefault(urllib.parse.urlsplit(url).hostname or "", threading.Semaphore(2)):
        end = time.time() + DEADLINE
        while True:
            try:
                req = urllib.request.Request(ascii_url, headers={"User-Agent": agents[0], "Accept": "*/*"})
                with urlopen(req, timeout=min(20, max(1, end - time.time()))) as resp:
                    raw = b"".join(itertools.takewhile(lambda _: time.time() < end, iter(lambda: resp.read(1 << 16), b"")))
                    if time.time() >= end:  # a body still coming in at the deadline
                        raise TimeoutError(f"body over {DEADLINE} s")
                    return raw, resp.headers.get_content_type(), resp.headers.get_content_charset()
            except urllib.error.HTTPError as exc:
                after = str((exc.headers or {}).get("Retry-After") or "").strip()
                exc.close()
                wait = min(int(after), 10) if after.isdigit() else (waits or [0])[0]
                if exc.code in (429, 503) and waits and time.time() + wait < end:
                    waits.pop(0)
                    sleep(wait)
                elif exc.code == 403 and len(agents) > 1:
                    agents.pop(0)
                else:
                    raise RuntimeError(f"http-{exc.code}") from None
            except Exception as exc:  # one bad URL must not stop the batch
                raise RuntimeError(squash(f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}").replace(" ", "_"))

@contextlib.contextmanager
def locked(lock: Path):
    """Hold `lock` (exclusive create): one fetch per URL. A waiter goes on without it after LOCK_WAIT s (writes are
    atomic); a lock older than LOCK_STALE s is a killed fetch's and is broken. Yields `touch` to keep a held lock fresh."""
    mine, start = False, time.time()
    while time.time() - start < LOCK_WAIT:
        with contextlib.suppress(FileExistsError, PermissionError):
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            mine = True
            break
        with contextlib.suppress(OSError):
            if time.time() - lock.stat().st_mtime > LOCK_STALE:
                lock.unlink()
        time.sleep(0.05)
    try:
        yield lambda: mine and lock.exists() and os.utime(lock)
    finally:
        if mine:
            lock.unlink(missing_ok=True)
def save(path: Path, data) -> None:
    """Write whole to this writer's own temp file, then move it into place (retried while Windows holds it open)."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_bytes(data) if isinstance(data, bytes) else write_text(tmp, data)
        for wait in (0.2, 0.5, 1, 2):
            with contextlib.suppress(PermissionError):
                return os.replace(tmp, path)
            time.sleep(wait)
        os.replace(tmp, path)
    finally:  # no temp file outlives a failure
        tmp.unlink(missing_ok=True)

def snap_head(path: Path) -> tuple:  # (header dict, body) of a snapshot; an empty header when it has none
    head, _, body = (text := read_text(path).replace("\r\n", "\n")).partition("\n\n")
    return (dict(ln.partition(": ")[::2] for ln in head.splitlines()), body) if text.startswith("URL:") else ({}, text)
def first_line(body: str) -> str:  # a title: the first 20+ character line, URLs removed, that JUNK does not match
    return next((t[:120].rstrip() for ln in body.splitlines()
                 if len(t := squash(URL_RX.sub(" ", ln))) >= 20 and not JUNK.search(t)), "")
def ok_snapshot(path: Path):  # (status, file, chars, title) of an ok snapshot at `path`, else None
    with contextlib.suppress(OSError):  # Windows refuses to open a file that is being replaced
        if path.exists() and (old := snap_head(path))[0].get("Status") == "ok":
            return "ok", path.name, len(old[1]), old[0].get("Title") or first_line(old[1])
def page_status(body: str) -> str:  # empty: < 200 characters; boilerplate: < 400 in 40+ character lines and table rows
    rows = [s for s in map(str.strip, body.splitlines()) if len(s) >= 40 or len(re.split(r"\||\t", s.strip("|"))) > 1]
    return "empty" if len(body.strip()) < 200 else "boilerplate" if sum(map(len, rows)) < 400 else "ok"

def fetch_one(url: str, pages: Path) -> tuple:  # (status, file, chars, title); an ok snapshot is not fetched again
    path, title = pages / (hashlib.sha1(norm_url(url).encode("utf-8")).hexdigest()[:12] + ".txt"), ""
    if hit := ok_snapshot(path):  # before the lock too, so a held or stale lock never delays a finished page
        return hit
    with locked(path.with_suffix(".lock")) as touch:
        if hit := ok_snapshot(path):
            return hit
        try:
            raw, ctype, header_cs = download(url)
        except RuntimeError as exc:
            return str(exc), "-", 0, ""
        if raw.startswith(OLE_MAGIC) or ctype == "application/msword":
            return "doc-binary", "-", 0, ""
        if ctype == "application/pdf" or raw.lstrip()[:4] == b"%PDF":
            if (text := pdf_text(raw, touch=touch)) is None or page_status(text) != "ok":  # scanned: for a PDF reader
                save(path.with_suffix(".pdf"), raw)
                return "pdf-saved", path.with_suffix(".pdf").name, len(raw), ""
            if layout := pdf_text(raw, True, touch):
                save(path.with_name(path.stem + ".layout.txt"), layout)
            charset = "pdf"
        else:
            meta = re.search(rb"<meta[^>]+charset=[\"']?\s*([\w.:-]+)", raw[:8192], re.I)
            text, charset = decode_bytes(raw, [header_cs, meta and meta.group(1).decode("ascii", "ignore")])
            if "html" in ctype or re.search(r"<(html|body|p|div|table)\b", text[:4096], re.I):
                text, title = html_to_text(text)
        body = text.replace("\r\n", "\n")
        status, title = page_status(body), title[:120].rstrip() or first_line(body)
        save(path, f"URL: {url}\nFetched: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
                   f"Status: {status}\nCharset: {charset}\nSHA256: {hashlib.sha256(raw).hexdigest()}\nTitle: {title}\n\n{body}")
        return status, path.name, len(body), title

def passages(text: str, terms: list[str], limit: int = 3, max_chars: int = 1500) -> list[str]:
    """Line-numbered ±2-line windows around the lines with the most term hits (Turkish case folding), best first."""
    terms, lines = [tr_fold(t.strip()) for t in terms if t.strip()], text.split("\n")
    hits = sorted(((len([t for t in terms if t in f]), sum(map(f.count, terms)), -i)
                   for i, f in enumerate(map(tr_fold, lines))), reverse=True)
    out, taken, room = [], [], max_chars
    for lo, hi in ((max(0, -h[2] - 2), min(len(lines), 3 - h[2])) for h in hits if h[0]):
        if len(out) < limit and room > 0 and not any(lo < b and a < hi for a, b in taken):
            block = "\n".join(f"{n + 1}: {lines[n][:299] + '…' * (len(lines[n]) > 300)}" for n in range(lo, hi)
                              if lines[n].strip())[:room]
            out, room, taken = out + [block], room - len(block), taken + [(lo, hi)]
    return out
def show(body: str, terms: str, head: str = "") -> list:  # print one body's passages, indented, after `head`
    if found := passages(body, terms.split("|")):
        print(*([head] if head else []), *("  " + block.replace("\n", "\n  ") for block in found), sep="\n")
    return found

def cmd_fetch(run: Path, urls, find: str | None = None) -> int:  # 8 workers; a line per URL, passages with --find
    (pages := run / "pages").mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for job in [pool.submit(fetch_one, url, pages) for url in urls]:  # one failure stays on its own line
            res = (f"error:{type(job.exception()).__name__}", "-", 0, "") if job.exception() else job.result()
            print(" ".join(map(str, res)).strip())
            if find and res[0] == "ok":
                show(snap_head(pages / res[1])[1], find)
    return 0
def cmd_find(run: Path, terms: str, urls=()) -> int:
    """Passages of the ok snapshots (all, or those of `urls`) under their URLs; then pages without hits, URLs without one."""
    want, snaps = {norm_url(u): u for u in urls}, load_snapshots(run, heads := {})  # the body, not a PDF's layout copy
    misses = sum(not show(heads[key][1], terms, heads[key][0]["URL"]) for key in snaps if not want or key in want)
    gone = [u for key, u in want.items() if key not in snaps]
    print(f"{plural(misses, 'page')} without hits; {plural(len(gone), 'URL')} without a snapshot"
          + (": " + " ".join(gone) if gone else ""))
    return 0

def parse_number(token: str, negative=False) -> list:  # (value, decimals) readings: two if ambiguous, none if mixed
    t = re.sub(r"[\s\u00a0\u202f\u2009]", "", token)
    with contextlib.suppress(InvalidOperation):  # 1,234.567,8 has no reading
        if "." in t and "," in t:
            dec = "." if t.rfind(".") > t.rfind(",") else ","
            t = t.replace("," if dec == "." else ".", "").replace(dec, ".")
            cands = [(Decimal(t), len(t.split(".")[1]))]
        else:
            cands = [(Decimal(t), 0)] if t.isdigit() else []
            for sep in ".,":
                if sep not in t:
                    continue
                if t.count(sep) > 1:
                    cands = [(Decimal(t.replace(sep, "")), 0)]
                    break
                whole, frac = t.split(sep)
                cands = [(Decimal(f"{whole}.{frac}"), len(frac))]
                if len(frac) == 3 and 1 <= len(whole) <= 3 and whole != "0":
                    cands.append((Decimal(whole + frac), 0))
        return [(-v if negative else v, d) for v, d in cands]
    return []
def mask(text: str) -> str:  # citation markers and URLs blanked out, so their digits are never read as numbers
    for rx in (URL_RX, CITE):
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text
def spelled(m) -> list:  # readings of `4 bin 472`, `bin 550`, `12,3 milyon`, `1.2 million`, `yüz bin`
    exp, tail = SCALE.get(tr_fold(m.group("m")), 0), int(m.group("tail") or 0)
    base = parse_number(m.group("n")) if m.group("n") else [(Decimal(100 if m.group("yuz") else 1), 0)]
    return [(v.scaleb(exp) + tail, d - exp if d and not tail else 0) for v, d in base]
def roman(s: str) -> int:
    vals = [{"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}[c] for c in s.upper()]
    return sum(-v if i + 1 < len(vals) and v < vals[i + 1] else v for i, v in enumerate(vals))
def special(m, text: str) -> list:  # keys, one per range end: "date 1923-10-29", "date --10-29", "century 16", "time 3:02"
    g = m.groupdict()
    if g["c"] or g["c2"]:
        ns = [int(c) if c.isdigit() else ORDS.index(c) + 1 if c in ORDS else roman(c)
              for c in (x.lower() for x in (g["c0"], g["c"], g["c2"], g["c3"]) if x)]
        return [f"century {n}" for n in ns if 0 < n <= 21]
    if g["h"]:  # a dotted time needs "saat" before it, am/pm after it, or a 'de/'te suffix not after a rate or price
        before, after = text[:m.start()], text[m.end():]  # ("at 3.45" and "yüzde 3.45'te" are decimals)
        ok = (g["sep"] == ":" or re.search(r"\bsaat\s*$", before, re.I) or re.match(r"\s*[ap]\.?m\b", after, re.I)
              or re.match(r"['’][dt][ae]\b", after, re.I) and not PRICE.search(before))
        return [f"time {int(g['h'])}:{g['mi']}"] if ok else []
    y, mo, *ds = next((g[a], g[b], *map(g.get, c)) for a, b, *c in (("iy", "im", "id"), ("dy", "dm", "dd"),
                                                                     ("ty", "tm", "d0", "td"), ("ey", "em", "ed")) if g[b])
    cap = y or mo[0].isupper()  # a yearless date needs a capital month: "5 may" is a verb
    mo = int(mo) if mo.isdigit() else MONTH.get(tr_fold(mo), 0)
    return [f"date {y or '-'}-{mo:02}-{int(d):02}" for d in ds if d and cap and 1 <= mo <= 12 and 1 <= int(d) <= 31]

def numbers(text: str, masked=False) -> list:  # tokens (no citations, URLs): one-token figures, scales, plain numbers
    text, out = (text if masked else mask(text)), []
    for m in SPECIAL.finditer(text):
        if keys := special(m, text):
            out.append(Num(m.start(), m.end(), m.group(0), [(k, 0) for k in keys]))
            text = text[:m.start()] + " " * (m.end() - m.start()) + text[m.end():]
    out += [Num(m.start(), m.end(), m.group(0), spelled(m)) for m in SPELL.finditer(text)
            if m.group("n") or m.group("yuz") or m.group("tail")]
    spans = [(n.start, n.end) for n in out]
    out += [Num(m.start(), m.end(), m.group(0), parse_number(m.group("n"), bool(m.group("neg"))))
            for m in NUM.finditer(text) if not any(s <= m.start() < e for s, e in spans)]
    return sorted((n for n in out if n.cands), key=lambda n: n.start)

def rounds_to(src, value, places: int) -> bool:
    if not isinstance(src, Decimal) or not isinstance(value, Decimal):
        return src == value  # one-token keys match only themselves
    with contextlib.suppress(ArithmeticError):
        return src == value or src.quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP) == value
    return False
def date_parts(key) -> set:  # "date 1923-10-29" -> {"date --10-29", 1923}; empty for any other reading
    return {"date -" + key[9:], Decimal(key[5:9])} if re.match(r"date \d", str(key)) else set()
def num_matches(num: Num, pool, toks=()) -> bool:
    """A reading of `num` (a range: either end) in `pool`; a full date needs its yearless key and year. With no token of
    its kind there, a date or century matches its plain parts: century; day; day and year ≤ 25 characters apart."""
    if any(p <= {s for s, _ in pool} if (p := date_parts(v)) else any(rounds_to(s, v, d) for s, _ in pool)
           for v, d in num.cands):
        return True
    kind, vals = str(num.cands[0][0]).split()[0], {s for s, _ in pool}
    if kind not in ("date", "century") or any(str(s).startswith(kind + " ") for s in vals):
        return False
    return any(Decimal(k[8:]) in vals if kind == "century" else Decimal(k[-2:]) in vals if k[5] == "-" else
               any(near(ns, Decimal(k[-2:]), Decimal(k[5:9])) for ns in toks) for k in (str(v) for v, _ in num.cands))
def near(ns, a, b, gap: int = 25) -> bool:  # readings a and b within `gap` characters among one text's tokens
    xs, ys = ([n.start for n in ns if v in dict(n.cands)] for v in (a, b))
    return any(abs(x - y) <= gap for x in xs for y in ys)
def is_year(num: Num, text: str = "", lo: int = 1900) -> bool:  # 4 digits in lo–2100, or after MÖ/MS/AD, before BC/AD
    return (num.text.isdigit() and len(num.text) == 4 and lo <= int(num.text) <= 2100 or bool(
        re.search(r"\b(?:M\.?Ö\.?|M\.?S\.?|AD)\s*$", text[:num.start]) or re.match(r"\s*(?:BCE?|AD)\b", text[num.end:])))
def is_small_int(num: Num) -> bool:
    return num.text.lstrip("-−").isdigit() and abs(int(num.text.lstrip("-−"))) <= 10

def evaluate(vals, ops):  # with the usual precedence (× ÷ before + −)
    terms = [vals[0]]
    for op, val in zip(ops, vals[1:]):
        terms[-1:] = [terms[-1] * val] if op == "*" else [terms[-1] / val] if op == "/" else [terms[-1], val if op == "+" else -val]
    return sum(terms)
def equation_ok(chain, ops, result) -> tuple:  # every reading of the inputs: (ok, value of the first reading)
    first = None
    for combo in itertools.product(*[[v for v, _ in n.cands] for n in chain]):
        with contextlib.suppress(ArithmeticError, InvalidOperation, TypeError):
            got = evaluate(list(combo), ops)
            first = got if first is None else first
            if any(isinstance(rv, Decimal) and abs(got - rv) <= abs(rv) * Decimal("0.005") or rounds_to(got, rv, rd)
                   for rv, rd in result.cands):
                return True, got
    return False, first
def find_equations(masked: str, nums: list) -> list:  # (inputs, ops, result, eq_pos) per `=`/`≈` after an op chain
    out, start = [], 0
    for m in re.finditer(r"[=≈]", masked):
        left = [n for n in nums if n.start >= start and n.end <= m.start()]
        right = [n for n in nums if n.start >= m.end()]
        if not left or not right:
            continue
        chain, ops = [left[-1]], []
        for prev in reversed(left[:-1]):
            if not (found := OPS.findall(masked[prev.end:chain[0].start])):
                break
            chain.insert(0, prev)
            ops.insert(0, OPMAP[found[-1]])
        if len(chain) >= 2:
            out.append((chain, ops, right[0], m.start()))
            start = right[0].end
    return out

def qnorm(text: str) -> str:
    return squash(unicodedata.normalize("NFC", text).translate(QMAP))
def quote_status(quote: str, texts) -> str:  # 'exact', 'near' (Turkish-aware case fold) or 'missing'
    parts = [p for p in (q.strip(" .,;:") for q in re.split(r"\.\.\.|…|\[\.\.\.\]", qnorm(quote))) if p]
    for status, fold in (("exact", str), ("near", tr_fold)):
        if all(any(fold(p) in h for h in [fold(qnorm(t)) for t in texts]) for p in parts):
            return status
    return "missing"

def expand_cites(inner: str) -> list:
    bounds = [[int(x) for x in re.split(r"[-–—]", piece) if x.strip()] for piece in re.split(r"[,;]", inner)]
    return [n for b in bounds for n in (range(b[0], b[-1] + 1) if len(b) == 2 else b)]
def receipt_label(line: str) -> tuple:  # (label or None, unverified) from the last parenthesised field
    words = re.findall(r"[^\W\d_]+", fields[-1].lower()) if (fields := re.findall(r"\(([^()]*)\)", line)) else []
    return next((LABELS[w] for w in words if w in LABELS), None), "unverified" in words
def loose(text: str) -> str:  # case (Turkish-aware), quotes and dashes folded; whitespace and hyphenation dropped
    return re.sub(r"[\s­-]+", "", tr_fold(unicodedata.normalize("NFC", text).translate(QMAP)))
def load_receipts(run: Path, snaps=None) -> tuple:
    """notes/*.md receipt spans and (label, unverified) pairs by normalized URL, and parse stats; unverified spans and
    spans absent from their URL's snapshot are left out and counted, not flagged."""
    spans, labels, hay, snaps = {}, {}, {}, snaps or {}
    stats = {"parsed": 0, "dropped": 0, "unverified": 0, "unparsed": []}
    for path in sorted((run / "notes").glob("*.md")):
        for line in read_text(path).splitlines():
            if not (m := RECEIPT.match(line)):
                if re.match(r"\s*[-*+]\s", line) and URL_RX.search(line) and re.search(r'["“”„]', line):
                    stats["unparsed"].append(line.strip())
                continue
            key, (label, unverified) = norm_url(m.group("url")), receipt_label(line[m.end():])
            stats["parsed"] += 1
            labels.setdefault(key, []).append((label, unverified))
            parts = [p for p in re.split(r'"?(?:\[\.\.\.\]|\.\.\.|…)"?|"[/,;]?"', loose(m.group("span"))) if p]
            if unverified:
                stats["unverified"] += 1
            elif key in snaps and not all(p in hay.setdefault(key, loose(snaps[key])) for p in parts):
                stats["dropped"] += 1
            else:
                spans.setdefault(key, []).append(m.group("span"))
    return spans, labels, stats
def lead_domain(url: str) -> bool:
    host = (urllib.parse.urlsplit(url.strip()).hostname or "").removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in LEAD_DOMAINS)

def load_snapshots(run: Path, heads: dict | None = None) -> dict:
    """Ok snapshot texts (plus any PDF `-layout` copy) by normalized URL; `heads` gets (header, body) per URL, ok ones
    first. Status: the header's, else a legacy index.tsv's. An unreadable file (being replaced, on Windows) is skipped."""
    pages, snaps, heads = run / "pages", {}, {} if heads is None else heads
    rows = [ln.split("\t") for ln in read_text(index).splitlines()] if (index := pages / "index.tsv").exists() else []
    failed = {p[1] for p in rows if len(p) >= 3 and p[1] and p[2] != "ok"}  # saved for inspection only
    for path in sorted(pages.glob("*.txt")) if pages.exists() else []:
        with contextlib.suppress(OSError):
            head, body = snap_head(path)
            if "URL" in head and (key := norm_url(head["URL"])) not in snaps:
                ok, lay = head.get("Status", "ok") == "ok" and path.name not in failed, path.with_suffix(".layout.txt")
                heads[key] = (head, body) if ok or key not in heads else heads[key]
                if ok:
                    snaps[key] = body + ("\n\n" + read_text(lay) if lay.exists() else "")
    return snaps

def is_entry(line: str) -> bool:
    return bool(SOURCE_ENTRY.match(line) and URL_RX.search(line))
def sources_start(lines) -> int | None:
    """Line the sources follow: SOURCES_MARK, else the last heading whose section (up to the next heading of its level
    or higher) is mostly `[n] ... URL` lines, moved up past each heading before it with only entries between."""
    if marks := [i for i, line in enumerate(lines) if line.strip() == SOURCES_MARK]:
        return marks[-1]
    heads = [(i, len(ln.lstrip()) - len(ln.lstrip().lstrip("#"))) for i, ln in enumerate(lines) if HEADING.match(ln)]
    content = lambda a, b: [ln for ln in lines[a:b] if ln.strip() and not HEADING.match(ln)]
    for k, (i, lv) in reversed(list(enumerate(heads))):
        rest = content(i + 1, next((j for j, up in heads[k + 1:] if up <= lv), len(lines)))
        if (hits := sum(map(is_entry, rest))) and 2 * hits >= len(rest):
            while k and all(map(is_entry, content(heads[k - 1][0] + 1, heads[k][0]))):  # a list split by sub-headings
                k -= 1
            return heads[k][0]
def parse_report(text: str):
    """Return (body lines before END_MARK, sources {n: url, the line's last URL}, END block lines up to the sources)."""
    lines = text.splitlines()
    cut = sources_start(lines)
    top, sources = (lines if cut is None else lines[:cut]), {}
    for line in lines[cut + 1:] if cut is not None else []:
        if is_entry(line) and (m := SOURCE_ENTRY.match(line)):
            sources[int(m.group(1) or m.group(3))] = URL_RX.findall(line)[-1].rstrip(".,;:")
    end = next((i for i, line in enumerate(top) if line.strip() == END_MARK), None)
    return (top, sources, []) if end is None else (top[:end], sources, top[end + 1:])

def split_line(line: str) -> list:  # never inside a one-token figure ("im 16. Jahrhundert", "am 29. Oktober 1923")
    keep = [m.span() for m in SPECIAL.finditer(line) if special(m, line)]
    parts, cuts = [], [0, *(m.end() for m in SENT_END.finditer(line) if all(not a < m.end() < b for a, b in keep)), len(line)]
    for part in (line[a:b].strip() for a, b in zip(cuts, cuts[1:])):
        if parts and (re.fullmatch(r"(?:\s*\[[^\]]+\]\s*[.,;]?)+", part) or ABBR.search(parts[-1])):
            parts[-1] += " " + part
        else:
            parts.append(part)
    return [p for p in parts if p.strip()]
def date_line(line: str) -> bool:
    """`<label>: <date>` in any language: 8 words at most, no citation, a date or year, else only day numbers."""
    m = re.match(r"[\s>*_-]*[^\W\d][^:]{0,30}:[*_]*(.+)", line)
    nums = numbers(m.group(1)) if m and len(line.split()) <= 8 and not CITE.search(line) else []
    big = [str(n.cands[0][0]).startswith("date") or is_year(n, lo=1000) for n in nums]
    return any(big) and all(b or n.text.isdigit() and int(n.text) <= 31 for b, n in zip(big, nums))
def groups(lines) -> list:
    """(first line index, sentences, is_table) per paragraph, list item or table: a citation's borrowing scope. Table
    rows stay whole; headings, fences, comments, check lines and (before the first `## `) date lines end a group."""
    out, fenced, cur, top = [], False, None, True
    for i, line in enumerate(lines):
        top = top and not line.startswith("## ")
        if line.lstrip().startswith("```"):
            fenced, cur = not fenced, None
            continue
        if (fenced or HEADING.match(line) or COMMENT.match(line) or CHECK_LINE.search(line) or MIX_LINE.search(line)
                or top and date_line(line) or not line.strip()):
            cur = None
            continue
        if (mark := LIST_MARK.match(line)) and (s := SPECIAL.match(line.lstrip())) and special(s, line.lstrip()):
            mark = None  # "16. yüzyılda ..." opens with a figure, not a list number
        text = (line[mark.end():] if mark else line).strip()
        table = text.startswith("|")
        if cur is None or (mark and not table) or table != cur[2]:
            out.append(cur := (i, [], table))
        cur[1].extend([text] if table else split_line(text))
    return [g for g in out if g[1]]
def sentences(body_lines) -> list:  # body prose split into sentences (see `groups`)
    return [s for _, sents, _ in groups(body_lines) for s in sents]
def excerpt(text: str, limit=140) -> str:
    text = squash(text).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1] + "…"

class Checker:
    """Holds evidence for one run, checks report lines and collects flags."""
    def __init__(self, run: Path):
        self.snaps = load_snapshots(run)
        self.receipts, self.labels, self.rstats = load_receipts(run, self.snaps)
        self.flags, self._pool, self.first_seen, self.eq_ok, self.eq_bad = [], {}, {}, 0, 0
        self.counts = {"quoted": 0, "page": 0, "missing": 0, "none": 0}
    def has_evidence(self, url: str) -> bool:
        return norm_url(url) in self.receipts or norm_url(url) in self.snaps
    def labels_of(self, url: str) -> list:
        return [lab for lab, _ in self.labels.get(norm_url(url), []) if lab and lab != "derived"]
    def is_lead(self, url: str) -> bool:
        return all(lab == "lead" for lab in labs) if (labs := self.labels_of(url)) else lead_domain(url)
    def source_class(self, url: str) -> str:  # the dominant receipt label (ties: the stronger), else lead or unlabelled
        if not (labs := self.labels_of(url)):
            return "lead" if lead_domain(url) else "unlabelled"
        return max(MIX[:5], key=lambda lab: (labs.count(lab), -MIX.index(lab)))
    def texts(self, urls) -> list:
        return [t for key in map(norm_url, urls)
                for t in self.receipts.get(key, []) + ([self.snaps[key]] if key in self.snaps else [])]
    def pool(self, url: str, kind: str) -> tuple:
        """(readings plus full dates' date_parts, tokens per text) of a URL's receipt spans ("quoted") or snapshot."""
        key = (norm_url(url), kind)
        if key not in self._pool:
            toks = [numbers(t) for t in (self.receipts.get(key[0], []) if kind == "quoted" else [self.snaps.get(key[0], "")])]
            got = [c for ns in toks for n in ns for c in n.cands]
            self._pool[key] = got + [(p, 0) for v, _ in got for p in date_parts(v)], toks
        return self._pool[key]
    def flag(self, kind, sentence, urls, detail, severity=None):
        self.flags.append({"kind": kind, "severity": severity or SEVERITY.get(kind, "low"), "excerpt": excerpt(sentence),
                           "urls": list(dict.fromkeys(urls)), "detail": detail})
    def check_number(self, num: Num, urls, sentence):
        urls = [u for u in urls if self.has_evidence(u)]
        found = next((k for k in ("quoted", "page") if any(num_matches(num, *self.pool(u, k)) for u in urls)), "missing")
        self.counts[found if urls else "none"] += 1
        if urls and found == "missing":  # a year is low, historical too: counts are written 1.500 or 1,500
            self.flag("number-mismatch", sentence, urls, f"{num.text.strip()} not found in cited sources"
                      + " (year)" * (year := is_year(num, sentence, 1000)), "low" if year else None)
    def check_sentence(self, sentence: str, sources: dict, borrowed=()):  # uncited, it borrows its group's citations
        masked = mask(sentence)
        cites = [(m.start(), expand_cites(m.group(1))) for m in CITE.finditer(sentence)]
        cited = [n for _, ns in cites for n in ns]
        scope = cited or list(borrowed)
        urls = [sources[n] for n in scope if n in sources]
        nums, used = numbers(masked, masked=True), set()
        uncited = "uncited-table" if sentence.startswith("|") else "uncited"
        for chain, ops, result, eq_pos in find_equations(masked, nums):
            used.update(n.start for n in chain + [result])
            ok, got = equation_ok(chain, ops, result)
            self.eq_ok, self.eq_bad = self.eq_ok + ok, self.eq_bad + (not ok)
            if not ok:
                self.flag("equation-wrong", sentence, urls, "could not evaluate" if got is None
                          else f"computed {got:f} but report says {result.text.strip()}")
            for i, num in enumerate(chain):
                stop = chain[i + 1].start if i + 1 < len(chain) else eq_pos
                own = [sources[n] for pos, ns in cites if num.end <= pos < stop for n in ns if n in sources]
                if own:
                    self.check_number(num, own, sentence)
                elif num.cands and num.cands[0][1] == 0:
                    continue  # bare integer input (12 months, 100 %): treated as a constant
                elif urls:
                    self.check_number(num, urls, sentence)
                elif not scope:
                    self.flag(uncited, sentence, [], f"equation input {num.text.strip()} has no citation")
        rest = [n for n in nums if n.start not in used]
        if scope:
            for num in rest:
                self.check_number(num, urls, sentence)
            ev_urls = [u for u in urls if self.has_evidence(u)]
            for quote in (next(g for g in m.groups() if g) for m in QUOTE_RX.finditer(sentence) if ev_urls):
                if len(quote.split()) >= 4 and (status := quote_status(quote, self.texts(ev_urls))) != "exact":
                    self.flag(QUOTE_FLAGS[status][0], sentence, ev_urls, f"“{excerpt(quote, 80)}”: {QUOTE_FLAGS[status][1]}")
        elif loose_nums := [n.text.strip() for n in rest if not is_year(n) and not is_small_int(n)]:
            self.flag(uncited, sentence, [], "numbers without citation: " + ", ".join(loose_nums))
        return cited
    def note_cites(self, text: str):
        for n in (n for m in CITE.finditer(text) for n in expand_cites(m.group(1))):
            self.first_seen.setdefault(n, text)
    def check_group(self, sents, sources, first=False):
        borrowed = [n for s in sents for m in CITE.finditer(s) for n in expand_cites(m.group(1))]
        for sentence in sents:
            cited = self.check_sentence(sentence, sources, borrowed)
            self.note_cites(sentence)
            if (urls := [sources[n] for n in cited if n in sources]) and all(self.is_lead(u) for u in urls):
                self.flag("lead-only", sentence, urls, "every cited source is lead-class (wiki, forum, blog, "
                          "aggregator)", "high" if first else None)
    def check_end(self, end, sources):
        """END block: its disagreement table (the first with 5+ columns: topic, A, B, verdict, why) is checked without
        the B column's text, but with its citations (a B cell needs `[n]` or †); the rest only registers citations."""
        gs = groups(end)
        table = next((g for g in gs if g[2] and g[1][0].strip().strip("|").count("|") >= 4), None)
        for sentence in (s for g in gs if g is not table for s in g[1]):
            self.note_cites(sentence)
        rows, shown, n = [], {}, len(self.flags)
        for k, row in enumerate(table[1] if table else []):
            cells = row.strip().strip("|").split("|")
            if k and len(cells) > 2 and not re.fullmatch(r"[\s:|-]+", row):
                b = cells[2].strip()
                self.note_cites(b)
                if b.strip("—–- ") and not CITE.search(b) and "†" not in b:
                    self.flag("b-unopened", row, [], f"B value `{excerpt(b, 60)}` has neither [n] nor †: open its page "
                              "and cite it, or mark it †")
                cells[2] = " " + " ".join(m.group(0) for m in CITE.finditer(b)) + " "  # a verdict may take B's value
            rows.append("|" + "|".join(cells) + "|")
            shown[excerpt(rows[-1])] = excerpt(row)
        self.check_group(rows, sources)
        for f in self.flags[n:]:  # an excerpt shows the row as the report has it
            f["excerpt"] = shown.get(f["excerpt"], f["excerpt"])
    def scan(self, body, sources, end=(), cut=0, unused=True):  # body (lead-only high before `cut`), END, sources, leaks
        for i, sents, _ in groups(body):
            self.check_group(sents, sources, i < cut)
        self.check_end(end, sources)
        for n, sentence in ((n, s) for n, s in self.first_seen.items() if n not in sources):
            self.flag("dangling", sentence, [], f"[{n}] has no entry in the sources section")
        for n, url in sorted(sources.items()):
            if unused and n not in self.first_seen:
                self.flag("unused", f"[{n}] {url}", [url], "source entry is never cited in the body")
            if not self.has_evidence(url):
                self.flag("unverifiable", f"[{n}] {url}", [url], "no page snapshot and no receipt for this URL")
        for line, m in ((ln, m) for ln in [*body, *end] if not CHECK_LINE.search(ln) for m in LEAK.finditer(ln)):
            self.flag("label-leak", line, [], f"internal label `{m.group(0)}` in report body")

def old_dispositions(path: Path) -> dict:  # a previous check.md's filled-in dispositions by (kind, excerpt), in order
    old = {}
    for line in read_text(path).splitlines() if path.exists() else []:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 7 and re.fullmatch(r"F\d+", cells[0]) and (
                disp := " | ".join(cells[6:]).strip()).removeprefix("disposition:").strip():
            old.setdefault((cells[2], cells[3]), []).append(disp)
    return old
def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"
def check(run: Path) -> dict:  # run every check; write check.md and the Source check and Source mix lines
    report_path = run / "report.md"
    body, sources, end = parse_report(text := read_text(report_path))
    checker = Checker(run)
    h2 = [i for i, line in enumerate(body) if line.startswith("## ")]
    checker.scan(body, sources, end, h2[1] if len(h2) > 1 else len(body))  # first section: before the second `## `
    for k in (END_MARK, SOURCES_MARK):  # an assembled report keeps both marker lines
        if k not in text and (END_MARK in text or SOURCES_MARK in text or (run / "report.assembled.md").is_file()):
            checker.flag("marker-missing", f"`{k}`", [], "restore this line: without it the END block and sources are misread")
    flags, c, rs = checker.flags, checker.counts, checker.rstats
    old = old_dispositions(run / "check.md")  # holds filled-in dispositions only
    asked = [f for f in flags if f["severity"] != "low"]
    disps = [(old.get((f["kind"], f["excerpt"])) or ["disposition:"]).pop(0) for f in asked]
    open_n = sum(d == "disposition:" or f["kind"] == "b-unopened" and not d.lower().startswith(("fixed", "†"))
                 for f, d in zip(asked, disps))  # an unopened B value is never a false alarm
    eqs = f"{checker.eq_ok} equations correct" + (f", {checker.eq_bad} wrong" if checker.eq_bad else "")
    summary = (f"script — {sum(c.values())} figures: {c['quoted']} in a quoted receipt, {c['page']} elsewhere on the "
               f"cited page, {c['missing']} not found, {c['none']} without evidence; {eqs}; {open_n} open high/medium "
               f"flags of {len(asked)} (check.md)")
    cited_urls = {norm_url(sources[n]): sources[n] for n in checker.first_seen if n in sources}
    classes = [checker.source_class(u) for u in cited_urls.values()]
    mix = ", ".join(f"{classes.count(k)} {k}" for k in MIX)
    rows = ["# Source check", "", summary, "", f"Source mix: {mix}", "",
            f"Receipts: {rs['parsed']} parsed, {rs['dropped']} not in their snapshot (dropped), {rs['unverified']} "
            f"unverified, {len(rs['unparsed'])} unparsed", *[f"- unparsed: {excerpt(u, 160)}" for u in rs["unparsed"][:5]],
            "", "| id | severity | kind | report excerpt | cited | expected / found | disposition |",
            "|---|---|---|---|---|---|---|"]
    rows += [f"| F{i} | {f['severity']} | {f['kind']} | {f['excerpt']} | {', '.join(f['urls']) or '—'} | "
             f"{excerpt(f['detail'], 200)} | {disp} |" for i, (f, disp) in enumerate(zip(asked, disps), 1)]
    rows += ["", "Disposition: fixed / derived / false alarm: <reason> / † (marked unverified, with a footnote).",
             "A b-unopened flag closes only as fixed or †.", "",
             "## Low (no answer needed)", "", "| id | kind | report excerpt | cited | expected / found |",
             "|---|---|---|---|---|"]
    rows += [f"| L{i} | {f['kind']} | {f['excerpt']} | {', '.join(f['urls']) or '—'} | {excerpt(f['detail'], 200)} |"
             for i, f in enumerate((f for f in flags if f["severity"] == "low"), 1)]
    write_text(run / "check.md", "\n".join(rows + [""]))
    path = run / "evidence.md" if (run / "evidence.md").exists() else report_path  # never both
    updated = CHECK_LINE.sub(lambda m: m.group("pre") + summary, old_text := read_text(path))
    updated = updated if path == report_path else MIX_LINE.sub(lambda m: m.group("pre") + mix, updated)
    if updated != old_text:
        write_text(path, updated)
    return {"summary": summary, "mix": mix, "flags": flags, "open": open_n, "counts": dict(c), "figures": sum(c.values()),
            "matched": c["quoted"] + c["page"], "eq_ok": checker.eq_ok, "eq_bad": checker.eq_bad}

def check_section(run: Path, sid: str) -> list:  # flags of a draft, sections/<sid>.md, cited by `[URL]`; writes nothing
    urls = []
    body = URL_CITE.sub(numberer({}, urls), read_text(run / "sections" / f"{sid}.md")).splitlines()
    (checker := Checker(run)).scan(body, dict(enumerate(urls, 1)), unused=False)
    return checker.flags
def numberer(nums: dict, urls: list):  # a URL_CITE callback: `[URL, URL]` -> `[n, m]`, new URLs numbered by first use
    def renumber(m):  # only a comma or semicolon before the next URL splits: URLs may hold them
        keys = [(norm_url(u), u.rstrip(".,;:")) for u in re.split(r"\s*[,;]\s*(?=(?:https?|file):)", m.group(1))]
        for key, u in ((k, u) for k, u in keys if k not in nums):  # checked as it goes: a repeat is numbered once
            urls.append(u)
            nums[key] = len(urls)
        return "[" + ", ".join(str(nums[k]) for k, _ in keys) + "]"
    return renumber
def section_order(run: Path) -> list:  # plan.md heading ids in order, then other sections/*.md (not _top/_end) by name
    plan = read_text(run / "plan.md").splitlines() if (run / "plan.md").is_file() else []
    ids = list(dict.fromkeys(m.group(1).lower() for line in plan if (m := PLAN_ID.match(line))))
    return ids + sorted(p.stem for p in (run / "sections").glob("*.md") if p.stem.lower() not in ("_top", "_end", *ids))
def cmd_assemble(run: Path, title: str = "Sources") -> int:
    """Join the drafts, `[URL]` as `[n]`, titled sources after SOURCES_MARK, into report.md and report.assembled.md;
    a report.md that differs from report.assembled.md (or has none) is kept, and only the copy is written."""
    secs, renumber = run / "sections", numberer({}, urls := [])
    if not secs.is_dir():
        print(f"error: sections folder missing: {secs}", file=sys.stderr)
        return 2
    files = {p.stem.lower(): p for p in secs.glob("*.md") if p.is_file()}  # an id names its draft in any case
    def part(sid):  # a draft without marker lines: assemble writes each marker once
        if path := files.get(sid.lower()):
            return "\n".join(s for s in read_text(path).splitlines() if s.strip() not in (END_MARK, SOURCES_MARK)).strip()
        print(f"warning: sections/{sid}.md missing", file=sys.stderr)
    drafts = [t for t in map(part, section_order(run)) if t is not None]
    body = URL_CITE.sub(renumber, "\n\n".join(t for t in [part("_top"), *drafts] if t))
    end, heads = URL_CITE.sub(renumber, part("_end") or ""), {}
    for raw in re.findall(r"\[(?:https?|file):[^\]]*\]", body + "\n" + end):
        print(f"warning: citation left unnumbered (write [URL] or [URL, URL]): {raw}", file=sys.stderr)
    load_snapshots(run, heads)
    titles = {key: squash(URL_RX.sub(" ", head.get("Title") or "")) or first_line(text)
              for key, (head, text) in heads.items()}  # a title never holds a URL: the line's last URL is the source
    refs = [" ".join(filter(None, (f"[{n}]", titles.get(norm_url(u)), u))) for n, u in enumerate(urls, 1)]
    blocks = [body, END_MARK + ("\n" + end if end else ""), "\n".join([SOURCES_MARK, f"## {title}", "", *refs])]
    text, out, copy = "\n\n".join(blocks) + "\n", run / "report.md", run / "report.assembled.md"
    edited = out.is_file() and (not copy.is_file() or read_text(out).splitlines() != read_text(copy).splitlines())
    for path in [copy] if edited else [out, copy]:
        write_text(path, text)
    print(f"{(copy if edited else out).name}: {len(drafts)} sections, {len(body.split())} body words, {len(urls)} sources"
          + " (report.md was edited after assembly, so it is kept: carry these changes into it, then run diff)" * edited)
    return 0

def doc_items(text: str) -> tuple:  # numbers, citations and 4+ word quotes as (keys, label, unit); sources; sentences
    body, sources, end = parse_report(text)
    items, sents = {"numbers": [], "citations": [], "quotes": []}, sentences(body + end)
    for unit in sents + [line.strip() for line in body + end if HEADING.match(line)]:
        items["numbers"] += [(frozenset(v for v, _ in n.cands), n.text.strip(), unit) for n in numbers(unit)]
        items["citations"] += [(frozenset([c]), f"[{c}]", unit) for m in CITE.finditer(unit)
                               for c in expand_cites(m.group(1))]
        items["quotes"] += [(frozenset([qnorm(q)]), f"“{excerpt(q, 80)}”", unit) for m in QUOTE_RX.finditer(unit)
                            if len((q := next(g for g in m.groups() if g)).split()) >= 4]
    return items, sources, sents
def detached(old_sents, new_sents) -> list:  # cited old sentences whose closest new one (numbers, words) has no citation
    def feats(s):
        return ({v for n in numbers(s) for v, _ in n.cands}, set(re.findall(r"[^\W\d_]{3,}", tr_fold(mask(s)))), s)
    new, out = [feats(s) for s in new_sents], []
    for vals, words, s in (feats(s) for s in old_sents if CITE.search(s)):
        score = lambda n: (len(vals & n[0]), sum(map(len, words & n[1])))
        best = max(new, key=score, default=None)
        if best and any(score(best)) and not CITE.search(best[2]):
            out.append(f"citation detached: {excerpt(s, 120)} -> now: {excerpt(best[2], 120)}")
    return out
def pair(old, new) -> tuple:  # match items sharing a key, same sentence first: (unmatched old, unmatched new)
    old, new = list(old), list(new)
    for same in (True, False):
        for item in list(old):
            if hit := next((x for x in new if x[0] & item[0] and (not same or qnorm(x[2]) == qnorm(item[2]))), None):
                old.remove(item)
                new.remove(hit)
    return old, new
def diff(old_text: str, new_text: str) -> list:  # what an edit lost, changed or added; [] for a pure rephrase
    (old, old_src, old_sents), (new, new_src, new_sents) = doc_items(old_text), doc_items(new_text)
    out = [f"marker missing: {k}" for k in (END_MARK, SOURCES_MARK) if old_text.count(k) > new_text.count(k)]
    for kind in old:
        lost, added = pair(old[kind], new[kind])
        name = "quote missing or altered" if kind == "quotes" else f"{kind[:-1]} missing"
        out += [f"{name}: {label} (was in: {excerpt(unit, 120)})" for _, label, unit in lost]
        ok = " (ok)" if kind not in ("numbers", "quotes") else ""  # an edit may add citations, never facts
        out += [f"{kind[:-1]} added{ok}: {label} (in: {excerpt(unit, 120)})" for _, label, unit in added]
    for n, a, b in ((n, old_src.get(n), new_src.get(n)) for n in sorted(set(old_src) | set(new_src))):
        if not a or norm_url(a) != (b and norm_url(b)):
            out.append(f"source [{n}] changed: {a} -> {b or '(none)'}" if a else f"source [{n}] added (ok): {b}")
    return out + detached(old_sents, new_sents)

def main(argv=None) -> int:
    setup_console()
    parser = argparse.ArgumentParser(prog="python scripts/vafer_check.py", description=__doc__ and __doc__.splitlines()[0])
    sub, path = parser.add_subparsers(dest="cmd", required=True), {"type": Path}
    for name, hlp, opts in (
            ("fetch", "download pages into <run>/pages", [("run", path), ("urls", {"nargs": "+"}), ("--find", {
                "metavar": "A|B", "help": "also print up to 3 passages per page for these terms"})]),
            ("find", "print passages for `a|b|c` from the ok snapshots", [("run", path), ("terms", {}),
                                                                         ("urls", {"nargs": "*"})]),
            ("check", "check <run>/report.md, or one draft with --section (offline, advisory)", [("run", path), (
                "--section", {"metavar": "ID", "help": "check sections/<ID>.md only; writes nothing"})]),
            ("assemble", "write <run>/report.md from sections/ with numbered citations", [("run", path), (
                "--title", {"default": "Sources", "help": "Sources heading, in the reader's language"})]),
            ("diff", "compare an edited report with its previous version", [("old", path), ("new", path)])):
        p = sub.add_parser(name, help=hlp)
        for opt, kw in opts:
            p.add_argument(opt, **kw)
    args = parser.parse_args(argv)
    if args.cmd in ("fetch", "find", "assemble"):
        return (cmd_fetch(args.run, args.urls, args.find) if args.cmd == "fetch" else cmd_assemble(args.run, args.title)
                if args.cmd == "assemble" else cmd_find(args.run, args.terms, args.urls))
    need = [args.old, args.new] if args.cmd == "diff" else [args.run / "sections" / f"{args.section}.md"
                                                             if args.section else args.run / "report.md"]
    if missing := next((p for p in need if not p.is_file()), None):
        print(f"error: file missing: {missing}", file=sys.stderr)
        return 2
    if args.cmd == "diff":
        changes = diff(read_text(args.old), read_text(args.new))
        bad = sum("(ok)" not in c for c in changes)  # additions alone pass
        print(*changes, f"diff: {plural(bad, 'problem')}" if bad else "diff: clean (numbers, citations, quotes, sources "
              "and markers kept)", sep="\n")
        return 1 if bad else 0
    if args.section:
        flags = check_section(args.run, args.section)
        sev = [f["severity"] for f in flags]
        print(f"section {args.section}: {len(flags)} flags ({sev.count('high')} high, {sev.count('medium')} medium, "
              f"{sev.count('low')} low)", *(f"{f['severity']} {f['kind']}: {f['excerpt']} — {f['detail']}".replace(
                  "\\|", "|") + (" — " + " ".join(f["urls"]) if f["urls"] else "") for f in flags), sep="\n")
        return 0
    result = check(args.run)
    print(f"{result['summary']}\nSource mix: {result['mix']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
