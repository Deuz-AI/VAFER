#!/usr/bin/env python
"""vafer_check: snapshot cited pages and check a vafer-research report against them.

Usage:
  python scripts/vafer_check.py fetch <run> <url> [<url> ...]
  python scripts/vafer_check.py check <run> [--section <id>]
  python scripts/vafer_check.py assemble <run> [--title "<Sources heading>"]
  python scripts/vafer_check.py diff <old.md> <new.md>

Stdlib only. `check` never touches the network and is advisory (exit 0), except when the run folder,
report.md or the section draft is missing (exit 2). `check --section` writes nothing. `assemble` builds report.md
out of the sections/ drafts (exit 2 when that folder is missing). `diff` exits 1 when an edit lost or changed a number,
citation, quote or source entry, or detached a citation; additions alone pass.
"""
from __future__ import annotations

import argparse, codecs, datetime as dt, hashlib, html.parser, itertools, re, shutil, subprocess, sys
import tempfile, unicodedata, urllib.error, urllib.parse, urllib.request
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0"
PLAIN_UA = "vafer-check/0.1 (python-urllib)"
urlopen = urllib.request.urlopen  # tests monkeypatch this

BOMS = ((codecs.BOM_UTF8, "utf-8-sig"), (codecs.BOM_UTF16_LE, "utf-16"), (codecs.BOM_UTF16_BE, "utf-16"))
URL_RX = re.compile(r"https?://[^\s<>()\[\]\"“”'«»]+|file:///[^\s<>()\[\]\"“”'«»]+")
CITE = re.compile(r"\[(\d+(?:\s*[-–—]\s*\d+)?(?:\s*[,;]\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]")
NUM = re.compile(r"(?<![\w.,])(?P<neg>[-−](?=\d))?"
                 r"(?P<n>\d{1,3}(?:[.,\u00a0\u202f\u2009 ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?!\d)")
OPS = re.compile(r"[×*·/÷+−]|(?<![^\W\d_])x(?![^\W\d_])|(?<!\S)-(?!\S)")
OPMAP = {"×": "*", "*": "*", "·": "*", "x": "*", "/": "/", "÷": "/", "+": "+", "−": "-", "-": "-"}
QUOTE_RX = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|«([^»\n]+)»|„([^“”\n]+)[“”]')
RECEIPT = re.compile(r'^\s*[-*+]\s+(?P<fact>.*?)["“„](?P<span>.+)["”“]\s*<?(?P<url>(?:https?:|file:/)//[^\s<>]+)>?')
URL_CITE = re.compile(r"\[((?:https?|file):[^\]\s,;]+(?:\s*[,;]\s*(?:https?|file):[^\]\s,;]+)*)\]")  # sections/<id>.md
MONTHS = ("ocak şubat mart nisan mayıs haziran temmuz ağustos eylül ekim kasım aralık january february march april "
          "may june july august september october november december").split()
MON = "|".join(MONTHS)
ORDS = ("first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth "
        "fifteenth sixteenth seventeenth eighteenth nineteenth twentieth twenty-first").split()
# one-token figures: ISO, dotted and written dates; Roman or ordinal centuries; clock times (accepted in `special`)
SPECIAL = re.compile(r"(?<![\w.,:])(?:(?P<iy>\d{4})-(?P<im>\d{1,2})-(?P<id>\d{1,2})"
                     r"|(?P<dd>\d{1,2})[./](?P<dm>\d{1,2})[./](?P<dy>\d{4})"
                     rf"|(?P<td>\d{{1,2}})(?:\.|st|nd|rd|th)?\s+(?:of\s+)?(?P<tm>{MON})\s+(?P<ty>\d{{4}})"
                     rf"|(?P<em>{MON})\s+(?P<ed>\d{{1,2}})(?:st|nd|rd|th)?,?\s+(?P<ey>\d{{4}})"
                     rf"|(?P<c>\d{{1,2}}|[IVXLC]{{1,6}}|{'|'.join(ORDS[::-1])})(?:\.|st|nd|rd|th)?[\s-]*"
                     r"(?:yüzyıl|yy\b|century|centuries)"
                     r"|(?P<h>[01]?\d|2[0-3])(?P<sep>[:.])(?P<mi>[0-5]\d))(?!\d)", re.I)
SEVERITY = {"equation-wrong": "high", "b-unopened": "high", "dangling": "high", "quote-missing": "high",
            "lead-only": "medium", "number-mismatch": "medium", "uncited": "medium", "unverifiable": "medium",
            "label-leak": "medium"}  # every other kind is low
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
SOURCES_MARK, END_MARK = "<!-- vafer:sources -->", "<!-- vafer:end -->"
COMMENT = re.compile(r"^\s*<!--.*-->\s*$")
SOURCE_ENTRY = re.compile(r"^\s*(?:[-*]\s*)?\[(\d+)\]:?\s+(.*)$|^\s*(\d+)\.\s+(.*)$")
CHECK_LINE = re.compile(r"(?P<pre>Source check[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
MIX_LINE = re.compile(r"(?P<pre>Source mix[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
LABELS = {"primary": "primary", "official": "official", "scholarly": "scholarly", "press": "press",
          "secondary": "press", "lead": "lead", "derived": "derived"}
MIX = ("primary", "official", "scholarly", "press", "lead", "unlabelled")
LEAD_DOMAINS = ("wikipedia.org", "wikiwand.com", "quora.com", "reddit.com", "medium.com", "blogspot.com",
                "wordpress.com", "eksisozluk.com", "fandom.com", "news.google.com", "msn.com", "yahoo.com")
DATE_LINE = re.compile(r"^[\s>*_-]*(?:Tarih|Date|As of|Güncel(?:leme)?|Last updated|Updated|Erişim(?: tarihi)?)"
                       r"[*_]*[ \t]*:", re.I)
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
QMAP = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "‚": "'",
                      "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-"})
QUOTE_FLAGS = {"near": ("quote-near", "matches only after Turkish-aware case folding"),
               "missing": ("quote-missing", "quoted span not found in cited snapshots or receipts")}
Num = namedtuple("Num", "start end text cands")

def setup_console() -> None:
    """Force UTF-8 on stdout/stderr (Windows consoles default to a legacy code page)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def decode_bytes(data: bytes, hints=()) -> tuple:
    """Decode by BOM, then the hinted charsets, then UTF-8, then windows-1254."""
    bom = next((enc for mark, enc in BOMS if data.startswith(mark)), None)
    for enc in filter(None, [bom, *hints, "utf-8"]):
        try:
            return data.decode(enc).lstrip("\ufeff"), enc
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("cp1254", errors="replace"), "windows-1254"

def read_text(path) -> str:
    """Read a local text file, honouring UTF-8/UTF-16 BOMs."""
    return decode_bytes(Path(path).read_bytes())[0]

def write_text(path, text: str) -> None:
    """Write UTF-8 without newline translation."""
    Path(path).write_text(text, encoding="utf-8", newline="")

def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def norm_url(url: str) -> str:
    """Normalize a URL: no scheme, www., fragment, trailing slash or utm_* params."""
    url = url.strip().rstrip(".,;:")
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    host = parts.netloc.lower().removeprefix("www.")
    return host + parts.path.rstrip("/") + ("?" + urllib.parse.urlencode(query) if query else "")

class _HTMLText(html.parser.HTMLParser):
    """HTML to plain text: blocks on their own lines, table rows as `a | b | c`."""
    SKIP = {"script", "style", "nav", "noscript", "template", "svg", "head"}
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "header",
             "footer", "ul", "ol", "table", "blockquote", "pre", "dt", "dd", "main", "aside", "figure",
             "figcaption", "form", "hr", "title", "caption"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.buf, self.skip, self.row, self.cell = [], [], 0, None, None
    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.skip = 0
        if tag in self.SKIP:
            self.skip += 1
        elif self.skip:
            return
        elif tag == "tr":
            self.end_row()
            self.flush()
            self.row = []
        elif tag in ("td", "th"):
            if self.row is None:
                self.flush()
                self.row = []
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
        text = squash("".join(self.buf))
        self.buf = []
        if text:
            self.lines.append(text)
    def text(self) -> str:
        self.close()
        self.end_row()
        self.flush()
        return "\n".join(self.lines)

def html_to_text(markup: str) -> str:
    parser = _HTMLText()
    parser.feed(markup)
    return parser.text()

def pdf_text(raw: bytes):
    """Run `pdftotext -layout`; return None when it is unavailable or fails."""
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / "in.pdf", Path(tmp) / "out.txt"
        src.write_bytes(raw)
        try:
            subprocess.run([exe, "-layout", "-enc", "UTF-8", str(src), str(out)], check=True,
                           capture_output=True, timeout=120)
            return read_text(out)
        except (OSError, subprocess.SubprocessError):
            return None

def download(url: str):
    """Return (raw, content_type, header_charset) or raise RuntimeError(reason)."""
    reason = "error"
    for agent in (BROWSER_UA, PLAIN_UA):
        req = urllib.request.Request(url, headers={"User-Agent": agent, "Accept": "*/*"})
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read(), resp.headers.get_content_type(), resp.headers.get_content_charset()
        except urllib.error.HTTPError as exc:
            reason = f"http-{exc.code}"
            exc.close()
            if exc.code not in (403, 429):
                break
        except Exception as exc:  # one bad URL must not stop the batch
            reason = squash(f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}").replace(" ", "_")
            break
    raise RuntimeError(reason)

def fetch_one(url: str, pages: Path):
    """Fetch one URL into pages/; return (status, file, chars)."""
    try:
        raw, ctype, header_cs = download(url)
    except RuntimeError as exc:
        return str(exc), "", 0
    if raw.startswith(OLE_MAGIC) or ctype == "application/msword":
        return "doc-binary", "", 0
    if ctype == "application/pdf" or raw.lstrip()[:4] == b"%PDF":
        text, charset = pdf_text(raw), "pdf"
        if text is None:
            return "pdf-no-text", "", 0
    else:
        meta = re.search(rb"<meta[^>]+charset=[\"']?\s*([\w.:-]+)", raw[:8192], re.I)
        hints = [h for h in (header_cs, meta and meta.group(1).decode("ascii", "ignore")) if h]
        text, charset = decode_bytes(raw, hints)
        if "html" in ctype or re.search(r"<(html|body|p|div|table)\b", text[:4096], re.I):
            text = html_to_text(text)
    name = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12] + ".txt"
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    head = f"URL: {url}\nFetched: {stamp}\nCharset: {charset}\nSHA256: {hashlib.sha256(raw).hexdigest()}\n\n"
    body = text.replace("\r\n", "\n")
    write_text(pages / name, head + body)
    if len(body.strip()) < 200:
        return "empty", name, len(text)
    if sum(len(line.strip()) >= 80 for line in body.splitlines()) < 3:
        return "boilerplate", name, len(text)  # mostly menus and link lists
    return "ok", name, len(text)

def cmd_fetch(run: Path, urls) -> int:
    pages = run / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    index = pages / "index.tsv"
    lines = read_text(index).splitlines() if index.exists() else []
    rows = {parts[0]: parts for parts in (line.split("\t") for line in lines) if parts[0]}
    for url in urls:
        status, name, chars = fetch_one(url, pages)
        rows[url] = [url, name, status, dt.date.today().isoformat()]
        saved = f" (saved {name}, {chars} chars)" if name else ""
        print(f"ok {name} {chars}" if status == "ok" else f"failed {status}{saved}")
    write_text(index, "".join("\t".join(r) + "\n" for r in rows.values()))
    return 0

def parse_number(token: str, negative=False) -> list:
    """Candidate (value, decimals) readings of a number token; ambiguous ones yield two."""
    t = re.sub(r"[\s\u00a0\u202f\u2009]", "", token)
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

def mask(text: str) -> str:
    """Blank out citation markers and URLs so their digits are never read as numbers."""
    for rx in (URL_RX, CITE):
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text

def spelled(m) -> list:
    """Readings of a written-out number: `4 bin 472`, `bin 550`, `12,3 milyon`, `1.2 million`, `yüz bin`."""
    exp, tail = SCALE.get(m.group("m").replace("İ", "i").replace("I", "ı").lower().replace("ı", "i"), 0), int(m.group("tail") or 0)
    base = parse_number(m.group("n")) if m.group("n") else [(Decimal(100 if m.group("yuz") else 1), 0)]
    return [(v.scaleb(exp) + tail, d - exp if d and not tail else 0) for v, d in base]

def roman(s: str) -> int:
    vals = [{"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}[c] for c in s.upper()]
    return sum(-v if i + 1 < len(vals) and v < vals[i + 1] else v for i, v in enumerate(vals))

def special(m, text: str):
    """Key of a one-token figure ("date 1923-10-29", "century 16", "time 3:02"), or None to read it as numbers."""
    g = m.groupdict()
    if g["c"]:
        c = g["c"].lower()
        n = int(c) if c.isdigit() else ORDS.index(c) + 1 if c in ORDS else roman(c)
        return f"century {n}" if 0 < n <= 21 else None
    if g["h"]:  # a dotted time needs "saat"/"at" before it or a suffix/am/pm after it
        ok = (g["sep"] == ":" or re.search(r"\b(?:saat|at)\s*$", text[:m.start()], re.I)
              or re.match(r"['’]?[dt][ae]\b|\s*[ap]\.?m\b", text[m.end():], re.I))
        return f"time {int(g['h'])}:{g['mi']}" if ok else None
    y, mo, d = next((g[a], g[b], g[c]) for a, b, c in (("iy", "im", "id"), ("dy", "dm", "dd"), ("ty", "tm", "td"),
                                                        ("ey", "em", "ed")) if g[a])
    mo = int(mo) if mo.isdigit() else [tr_fold(x) for x in MONTHS].index(tr_fold(mo)) % 12 + 1
    return f"date {int(y)}-{mo:02}-{int(d):02}" if 1 <= mo <= 12 and 1 <= int(d) <= 31 else None

def numbers(text: str, masked=False) -> list:
    """All number tokens in text (citations and URLs excluded): one-token dates, centuries and times, written-out
    scales, then plain numbers."""
    text, out = (text if masked else mask(text)), []
    for m in SPECIAL.finditer(text):
        if key := special(m, text):
            out.append(Num(m.start(), m.end(), m.group(0), [(key, 0)]))
            text = text[:m.start()] + " " * (m.end() - m.start()) + text[m.end():]
    out += [Num(m.start(), m.end(), m.group(0), spelled(m)) for m in SPELL.finditer(text)
            if m.group("n") or m.group("yuz") or m.group("tail")]
    spans = [(n.start, n.end) for n in out]
    out += [Num(m.start(), m.end(), m.group(0), parse_number(m.group("n"), bool(m.group("neg"))))
            for m in NUM.finditer(text) if not any(s <= m.start() < e for s, e in spans)]
    return sorted(out, key=lambda n: n.start)

def rounds_to(src, value, places: int) -> bool:
    if not isinstance(src, Decimal) or not isinstance(value, Decimal):
        return src == value  # one-token keys match only themselves
    try:
        return src == value or src.quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP) == value
    except ArithmeticError:
        return False

def num_matches(num: Num, pool) -> bool:
    return any(rounds_to(s, v, d) for v, d in num.cands for s, _ in pool)

def is_year(num: Num) -> bool:
    return num.text.isdigit() and len(num.text) == 4 and 1900 <= int(num.text) <= 2100

def is_small_int(num: Num) -> bool:
    return num.text.lstrip("-−").isdigit() and abs(int(num.text.lstrip("-−"))) <= 10

def evaluate(vals, ops):
    """Evaluate with usual precedence (× ÷ before + −)."""
    terms = [vals[0]]
    for op, val in zip(ops, vals[1:]):
        if op == "*":
            terms[-1] *= val
        elif op == "/":
            terms[-1] /= val
        else:
            terms.append(val if op == "+" else -val)
    return sum(terms)

def equation_ok(chain, ops, result) -> tuple:
    """Try every reading of the inputs; return (ok, computed value of the first reading)."""
    first = None
    for combo in itertools.product(*[[v for v, _ in n.cands] for n in chain]):
        try:
            got = evaluate(list(combo), ops)
        except (ArithmeticError, InvalidOperation, TypeError):
            continue
        first = got if first is None else first
        for rv, rd in result.cands:
            if isinstance(rv, Decimal) and abs(got - rv) <= abs(rv) * Decimal("0.005") or rounds_to(got, rv, rd):
                return True, got
    return False, first

def find_equations(masked: str, nums: list) -> list:
    """Return (inputs, ops, result, eq_pos) for each `=`/`≈` with an operator chain on its left."""
    out, start = [], 0
    for m in re.finditer(r"[=≈]", masked):
        left = [n for n in nums if n.start >= start and n.end <= m.start()]
        right = [n for n in nums if n.start >= m.end()]
        if not left or not right:
            continue
        chain, ops = [left[-1]], []
        for prev in reversed(left[:-1]):
            found = OPS.findall(masked[prev.end:chain[0].start])
            if not found:
                break
            chain.insert(0, prev)
            ops.insert(0, OPMAP[found[-1]])
        if len(chain) >= 2:
            out.append((chain, ops, right[0], m.start()))
            start = right[0].end
    return out

def qnorm(text: str) -> str:
    return squash(unicodedata.normalize("NFC", text).translate(QMAP))

def tr_fold(text: str) -> str:
    return text.replace("İ", "i").replace("I", "i").replace("ı", "i").casefold()

def quote_status(quote: str, texts) -> str:
    """'exact', 'near' (Turkish-aware case fold) or 'missing'."""
    parts = [p for p in (q.strip(" .,;:") for q in re.split(r"\.\.\.|…|\[\.\.\.\]", qnorm(quote))) if p]
    hay = [qnorm(t) for t in texts]
    if all(any(p in h for h in hay) for p in parts):
        return "exact"
    folded = [tr_fold(h) for h in hay]
    if all(any(tr_fold(p) in h for h in folded) for p in parts):
        return "near"
    return "missing"

def expand_cites(inner: str) -> list:
    out = []
    for piece in re.split(r"[,;]", inner):
        bounds = [int(x) for x in re.split(r"[-–—]", piece) if x.strip()]
        out.extend(range(bounds[0], bounds[-1] + 1) if len(bounds) == 2 else bounds)
    return out

def receipt_label(line: str) -> tuple:
    """(label, unverified) from the last parenthesised field; label None when absent."""
    groups = re.findall(r"\(([^()]*)\)", line)
    words = re.findall(r"[^\W\d_]+", groups[-1].lower()) if groups else []
    return next((LABELS[w] for w in words if w in LABELS), None), "unverified" in words

def loose(text: str) -> str:
    """Fold case (Turkish-aware), quotes and dashes; drop whitespace and hyphenation."""
    return re.sub(r"[\s­-]+", "", tr_fold(unicodedata.normalize("NFC", text).translate(QMAP)))

def load_receipts(run: Path, snaps=None) -> tuple:
    """Receipt spans and (label, unverified) pairs from notes/*.md, both keyed by normalized URL, and parse stats.
    Unverified spans, and spans absent from their URL's snapshot, are left out and counted, not flagged."""
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
            parts = [p for p in map(loose, re.split(r"\[\.\.\.\]|\.\.\.|…", m.group("span"))) if p]
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

def snapshot_body(text: str) -> str:
    text = text.replace("\r\n", "\n")
    return text.split("\n\n", 1)[1] if text.startswith("URL:") and "\n\n" in text else text

def load_snapshots(run: Path) -> dict:
    """Snapshot texts keyed by normalized URL, via index.tsv, then file headers."""
    pages, snaps, failed = run / "pages", {}, set()
    index = pages / "index.tsv"
    if index.exists():
        for line in read_text(index).splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[1] and parts[2] != "ok":
                failed.add(parts[1])  # saved for inspection only (empty / boilerplate)
            elif len(parts) >= 3 and parts[1] and (pages / parts[1]).exists():
                snaps[norm_url(parts[0])] = snapshot_body(read_text(pages / parts[1]))
    for path in sorted(pages.glob("*.txt")) if pages.exists() else []:
        if path.name not in failed and (text := read_text(path)).startswith("URL:"):
            snaps.setdefault(norm_url(text.split("\n", 1)[0][4:].strip()), snapshot_body(text))
    return snaps

def is_entry(line: str) -> bool:
    return bool(SOURCE_ENTRY.match(line) and URL_RX.search(line))

def sources_start(lines) -> int | None:
    """Line the sources follow: SOURCES_MARK, else the last heading mostly followed by `[n] ... URL` lines."""
    marks = [i for i, line in enumerate(lines) if line.strip() == SOURCES_MARK]
    if marks:
        return marks[-1]
    for i in reversed([i for i, line in enumerate(lines) if HEADING.match(line)]):
        rest = [line for line in lines[i + 1:] if line.strip()]
        hits = sum(map(is_entry, rest))
        if hits and 2 * hits >= len(rest):
            return i
    return None

def parse_report(text: str):
    """Return (body lines before END_MARK, sources {n: url}, END block lines up to the sources)."""
    lines = text.splitlines()
    cut = sources_start(lines)
    top, sources = (lines if cut is None else lines[:cut]), {}
    for line in lines[cut + 1:] if cut is not None else []:
        if is_entry(line):
            m = SOURCE_ENTRY.match(line)
            sources[int(m.group(1) or m.group(3))] = URL_RX.search(line).group(0).rstrip(".,;:")
    end = next((i for i, line in enumerate(top) if line.strip() == END_MARK), None)
    return (top, sources, []) if end is None else (top[:end], sources, top[end + 1:])

def split_line(line: str) -> list:
    parts, cuts = [], [0] + [m.end() for m in SENT_END.finditer(line)] + [len(line)]
    for part in (line[a:b].strip() for a, b in zip(cuts, cuts[1:])):
        if parts and (re.fullmatch(r"(?:\s*\[[^\]]+\]\s*[.,;]?)+", part) or ABBR.search(parts[-1])):
            parts[-1] += " " + part
        else:
            parts.append(part)
    return [p for p in parts if p.strip()]

def groups(lines) -> list:
    """(first line index, sentences, is_table) per paragraph, list item or table: a citation's borrowing scope.
    Table rows stay whole; headings, fences, comments, check and date lines are skipped and end a group."""
    out, fenced, cur = [], False, None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced, cur = not fenced, None
            continue
        if (fenced or HEADING.match(line) or COMMENT.match(line) or CHECK_LINE.search(line) or MIX_LINE.search(line)
                or DATE_LINE.match(line) or not line.strip()):
            cur = None
            continue
        text = LIST_MARK.sub("", line, count=1).strip()
        table = text.startswith("|")
        if cur is None or (LIST_MARK.match(line) and not table) or table != cur[2]:
            out.append(cur := (i, [], table))
        cur[1].extend([text] if table else split_line(text))
    return [g for g in out if g[1]]

def sentences(body_lines) -> list:
    """Body prose split into sentences (see `groups`)."""
    return [s for _, sents, _ in groups(body_lines) for s in sents]

def excerpt(text: str, limit=140) -> str:
    text = squash(text).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1] + "…"

class Checker:
    """Holds evidence for one run, checks report lines and collects flags."""
    def __init__(self, run: Path):
        self.snaps = load_snapshots(run)
        self.receipts, self.labels, self.rstats = load_receipts(run, self.snaps)
        self.flags, self._pool, self.first_seen = [], {}, {}
        self.counts = {"quoted": 0, "page": 0, "missing": 0, "none": 0}
        self.eq_ok = self.eq_bad = 0
    def has_evidence(self, url: str) -> bool:
        return norm_url(url) in self.receipts or norm_url(url) in self.snaps
    def labels_of(self, url: str) -> list:
        return [lab for lab, _ in self.labels.get(norm_url(url), []) if lab and lab != "derived"]
    def is_lead(self, url: str) -> bool:
        labs = self.labels_of(url)
        return all(lab == "lead" for lab in labs) if labs else lead_domain(url)
    def source_class(self, url: str) -> str:
        """Dominant receipt label (ties go to the stronger label); lead-domain or unlabelled without one."""
        labs = self.labels_of(url)
        if not labs:
            return "lead" if lead_domain(url) else "unlabelled"
        return max(MIX[:5], key=lambda lab: (labs.count(lab), -MIX.index(lab)))
    def texts(self, urls) -> list:
        return [t for key in map(norm_url, urls)
                for t in self.receipts.get(key, []) + ([self.snaps[key]] if key in self.snaps else [])]
    def pool(self, url: str, kind: str) -> list:
        """Number readings of a URL's receipt spans ("quoted") or of its snapshot ("page")."""
        key = (norm_url(url), kind)
        if key not in self._pool:
            texts = self.receipts.get(key[0], []) if kind == "quoted" else [self.snaps.get(key[0], "")]
            self._pool[key] = [c for t in texts for n in numbers(t) for c in n.cands]
        return self._pool[key]
    def flag(self, kind, sentence, urls, detail, severity=None):
        self.flags.append({"kind": kind, "severity": severity or SEVERITY.get(kind, "low"), "excerpt": excerpt(sentence),
                           "urls": list(dict.fromkeys(urls)), "detail": detail})
    def check_number(self, num: Num, urls, sentence):
        urls = [u for u in urls if self.has_evidence(u)]
        found = next((k for k in ("quoted", "page") if any(num_matches(num, self.pool(u, k)) for u in urls)), "missing")
        self.counts[found if urls else "none"] += 1
        if urls and found == "missing":
            self.flag("number-mismatch", sentence, urls, f"{num.text.strip()} not found in cited sources"
                      + (" (year)" if is_year(num) else ""), "low" if is_year(num) else None)
    def check_sentence(self, sentence: str, sources: dict, borrowed=()):
        """Check one sentence; without citations of its own it uses `borrowed` (its paragraph's or table's)."""
        masked = mask(sentence)
        cites = [(m.start(), expand_cites(m.group(1))) for m in CITE.finditer(sentence)]
        cited = [n for _, ns in cites for n in ns]
        scope = cited or list(borrowed)
        urls = [sources[n] for n in scope if n in sources]
        nums = numbers(masked, masked=True)
        used = set()
        uncited = "uncited-table" if sentence.startswith("|") else "uncited"
        for chain, ops, result, eq_pos in find_equations(masked, nums):
            used.update(n.start for n in chain + [result])
            ok, got = equation_ok(chain, ops, result)
            if ok:
                self.eq_ok += 1
            else:
                self.eq_bad += 1
                self.flag("equation-wrong", sentence, urls,
                          f"computed {got:f} but report says {result.text.strip()}" if got is not None
                          else "could not evaluate")
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
            for m in QUOTE_RX.finditer(sentence):
                quote = next(g for g in m.groups() if g)
                if len(quote.split()) < 4 or not ev_urls:
                    continue
                status = quote_status(quote, self.texts(ev_urls))
                if status != "exact":
                    kind, detail = QUOTE_FLAGS[status]
                    self.flag(kind, sentence, ev_urls, f"“{excerpt(quote, 80)}”: {detail}")
        else:
            loose_nums = [n.text.strip() for n in rest if not is_year(n) and not is_small_int(n)]
            if loose_nums:
                self.flag(uncited, sentence, [], "numbers without citation: " + ", ".join(loose_nums))
        return cited
    def note_cites(self, text: str):
        for m in CITE.finditer(text):
            for n in expand_cites(m.group(1)):
                self.first_seen.setdefault(n, text)
    def check_group(self, sents, sources, first=False):
        borrowed = [n for s in sents for m in CITE.finditer(s) for n in expand_cites(m.group(1))]
        for sentence in sents:
            cited = self.check_sentence(sentence, sources, borrowed)
            self.note_cites(sentence)
            urls = [sources[n] for n in cited if n in sources]
            if urls and all(self.is_lead(u) for u in urls):
                self.flag("lead-only", sentence, urls, "every cited source is lead-class (wiki, forum, blog, "
                          "aggregator)", "high" if first else None)
    def check_end(self, end, sources):
        """END block: its first table is checked without the B column (a B cell needs `[n]` or †); the rest
        (unknowns) only registers citations."""
        gs = groups(end)
        table = next((g for g in gs if g[2]), None)
        for sentence in (s for g in gs if g is not table for s in g[1]):
            self.note_cites(sentence)
        rows = []
        for k, row in enumerate(table[1] if table else []):
            cells = row.strip().strip("|").split("|")
            if k and len(cells) > 2 and not re.fullmatch(r"[\s:|-]+", row):
                b = cells[2].strip()
                self.note_cites(b)
                if b.strip("—–- ") and not CITE.search(b) and "†" not in b:
                    self.flag("b-unopened", row, [], f"B value `{excerpt(b, 60)}` has no [n] and no † (not opened)")
                cells[2] = " "
            rows.append("|" + "|".join(cells) + "|")
        self.check_group(rows, sources)
    def scan(self, body, sources, end=(), cut=0, unused=True):
        """Check body groups (lead-only is high before line `cut`), the END block, sources and leaks."""
        for i, sents, _ in groups(body):
            self.check_group(sents, sources, i < cut)
        self.check_end(end, sources)
        for n, sentence in self.first_seen.items():
            if n not in sources:
                self.flag("dangling", sentence, [], f"[{n}] has no entry in the sources section")
        for n, url in sorted(sources.items()):
            if unused and n not in self.first_seen:
                self.flag("unused", f"[{n}] {url}", [url], "source entry is never cited in the body")
            if not self.has_evidence(url):
                self.flag("unverifiable", f"[{n}] {url}", [url], "no page snapshot and no receipt for this URL")
        for line in (line for line in list(body) + list(end) if not CHECK_LINE.search(line)):
            for m in LEAK.finditer(line):
                self.flag("label-leak", line, [], f"internal label `{m.group(0)}` in report body")

def old_dispositions(path: Path) -> dict:
    """Filled-in dispositions of a previous check.md, keyed by (kind, report excerpt), in row order."""
    old = {}
    for line in read_text(path).splitlines() if path.exists() else []:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 7 and re.fullmatch(r"F\d+", cells[0]):
            disp = " | ".join(cells[6:]).strip()
            if disp.removeprefix("disposition:").strip():
                old.setdefault((cells[2], cells[3]), []).append(disp)
    return old

def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"

def check(run: Path) -> dict:
    """Run every check; write check.md and update the Source check line."""
    report_path = run / "report.md"
    text = read_text(report_path)
    body, sources, end = parse_report(text)
    checker = Checker(run)
    h2 = [i for i, line in enumerate(body) if line.startswith("## ")]
    checker.scan(body, sources, end, h2[1] if len(h2) > 1 else len(body))  # first section: before the second `## `
    flags, c, rs = checker.flags, checker.counts, checker.rstats
    old = old_dispositions(run / "check.md")  # holds filled-in dispositions only
    asked = [f for f in flags if f["severity"] != "low"]
    disps = [(old.get((f["kind"], f["excerpt"])) or ["disposition:"]).pop(0) for f in asked]
    open_n = disps.count("disposition:")
    eqs = f"{plural(checker.eq_ok, 'equation')} correct" + (f", {checker.eq_bad} wrong" if checker.eq_bad else "")
    summary = (f"script — {plural(sum(c.values()), 'figure')}: {c['quoted']} in a quoted receipt, {c['page']} elsewhere "
               f"on the cited page, {c['missing']} not found, {c['none']} without evidence; {eqs}; "
               f"{open_n} open high/medium flag{'' if open_n == 1 else 's'} of {len(flags)} (check.md)")
    cited_urls = {norm_url(sources[n]): sources[n] for n in checker.first_seen if n in sources}
    classes = [checker.source_class(u) for u in cited_urls.values()]
    mix = ", ".join(f"{classes.count(k)} {k}" for k in MIX)

    rows = ["# Source check", "", summary, "", f"Source mix: {mix}", "",
            f"Receipts: {rs['parsed']} parsed, {rs['dropped']} not in their snapshot (dropped), {rs['unverified']} "
            f"unverified, {len(rs['unparsed'])} unparsed", *[f"- unparsed: {excerpt(u, 160)}" for u in rs["unparsed"][:5]],
            "", "| id | severity | kind | report excerpt | cited | expected / found | disposition |",
            "|---|---|---|---|---|---|---|"]
    for i, (f, disp) in enumerate(zip(asked, disps), 1):
        rows.append(f"| F{i} | {f['severity']} | {f['kind']} | {f['excerpt']} | {', '.join(f['urls']) or '—'} | "
                    f"{excerpt(f['detail'], 200)} | {disp} |")
    rows += ["", "Disposition: fixed / derived / false alarm: <reason> / † (marked unverified, with a footnote).", "",
             "## Low (no answer needed)", "", "| id | kind | report excerpt | cited | expected / found |",
             "|---|---|---|---|---|"]
    rows += [f"| L{i} | {f['kind']} | {f['excerpt']} | {', '.join(f['urls']) or '—'} | {excerpt(f['detail'], 200)} |"
             for i, f in enumerate((f for f in flags if f["severity"] == "low"), 1)]
    write_text(run / "check.md", "\n".join(rows + [""]))

    path = run / "evidence.md" if (run / "evidence.md").exists() else report_path  # never both
    old_text = read_text(path)
    updated = CHECK_LINE.sub(lambda m: m.group("pre") + summary, old_text)
    if path != report_path:
        updated = MIX_LINE.sub(lambda m: m.group("pre") + mix, updated)
    if updated != old_text:
        write_text(path, updated)
    return {"summary": summary, "mix": mix, "flags": flags, "open": open_n, "counts": dict(c),
            "figures": sum(c.values()), "matched": c["quoted"] + c["page"], "eq_ok": checker.eq_ok,
            "eq_bad": checker.eq_bad}

def check_section(run: Path, sid: str) -> list:
    """Check one researcher draft, sections/<sid>.md, whose citations are `[URL]`; write nothing."""
    sources, nums = {}, {}
    def renumber(m):
        ns = [nums.setdefault(norm_url(u), len(nums) + 1) for u in re.split(r"\s*[,;]\s*", m.group(1))]
        for n, u in zip(ns, re.split(r"\s*[,;]\s*", m.group(1))):
            sources.setdefault(n, u)
        return "[" + ", ".join(map(str, ns)) + "]"
    body = URL_CITE.sub(renumber, read_text(run / "sections" / f"{sid}.md")).splitlines()
    checker = Checker(run)
    checker.scan(body, sources, unused=False)
    return checker.flags

PLAN_ID = re.compile(r"^#{2,4}\s+([A-Za-z]{1,3}\d{1,2})\b")

def section_order(run: Path) -> list:
    """Section ids in plan.md heading order, then other sections/*.md (not _top/_end) by name."""
    plan = read_text(run / "plan.md").splitlines() if (run / "plan.md").is_file() else []
    ids = list(dict.fromkeys(m.group(1).lower() for line in plan if (m := PLAN_ID.match(line))))
    return ids + sorted(p.stem for p in (run / "sections").glob("*.md") if p.stem not in ("_top", "_end", *ids))

def cmd_assemble(run: Path, title: str = "Sources") -> int:
    """Join the drafts into report.md; `[URL]` citations become `[n]`; sources follow SOURCES_MARK."""
    secs, nums, urls = run / "sections", {}, []
    if not secs.is_dir():
        print(f"error: sections folder missing: {secs}", file=sys.stderr)
        return 2
    def part(sid):
        if (secs / f"{sid}.md").is_file():
            return read_text(secs / f"{sid}.md").replace("\r\n", "\n").strip()
        print(f"warning: sections/{sid}.md missing", file=sys.stderr)
    def renumber(m):
        keys = [(norm_url(u), u.rstrip(".,;:")) for u in re.split(r"\s*[,;]\s*", m.group(1))]
        for key, u in keys:
            if key not in nums:
                nums[key] = len(urls) + 1
                urls.append(u)
        return "[" + ", ".join(str(nums[k]) for k, _ in keys) + "]"
    drafts = [t for t in map(part, section_order(run)) if t is not None]
    body = URL_CITE.sub(renumber, "\n\n".join(t for t in [part("_top"), *drafts] if t))
    end, snaps = URL_CITE.sub(renumber, part("_end") or ""), load_snapshots(run)
    heads = [next((ln.strip() for ln in snaps.get(norm_url(u), "").splitlines() if ln.strip()), "")[:120] for u in urls]
    entries = [" ".join(filter(None, (f"[{n}]", h, u))) for n, (h, u) in enumerate(zip(heads, urls), 1)]
    blocks = [body, END_MARK + ("\n" + end if end else ""), "\n".join([SOURCES_MARK, f"## {title}", "", *entries])]
    write_text(run / "report.md", "\n\n".join(blocks) + "\n")
    print(f"report.md: {len(drafts)} sections, {len(body.split())} body words, {len(urls)} sources")
    return 0

def doc_items(text: str) -> tuple:
    """Numbers, citation markers and 4+ word quotes of a report body as (keys, label, unit); sources; sentences."""
    body, sources, end = parse_report(text)
    body += end
    items, sents = {"numbers": [], "citations": [], "quotes": []}, sentences(body)
    for unit in sents + [line.strip() for line in body if HEADING.match(line)]:
        items["numbers"] += [(frozenset(v for v, _ in n.cands), n.text.strip(), unit) for n in numbers(unit)]
        items["citations"] += [(frozenset([c]), f"[{c}]", unit) for m in CITE.finditer(unit)
                               for c in expand_cites(m.group(1))]
        items["quotes"] += [(frozenset([qnorm(q)]), f"“{excerpt(q, 80)}”", unit) for m in QUOTE_RX.finditer(unit)
                            if len((q := next(g for g in m.groups() if g)).split()) >= 4]
    return items, sources, sents

def detached(old_sents, new_sents) -> list:
    """Old cited sentences whose closest new sentence (shared numbers, then shared words) has no citation."""
    def feats(s):
        return ({v for n in numbers(s) for v, _ in n.cands}, set(re.findall(r"[^\W\d_]{3,}", tr_fold(mask(s)))), s)
    new, out = [feats(s) for s in new_sents], []
    for vals, words, s in (feats(s) for s in old_sents if CITE.search(s)):
        score = lambda n: (len(vals & n[0]), sum(map(len, words & n[1])))
        best = max(new, key=score, default=None)
        if best and any(score(best)) and not CITE.search(best[2]):
            out.append(f"citation detached: {excerpt(s, 120)} -> now: {excerpt(best[2], 120)}")
    return out

def pair(old, new) -> tuple:
    """Match items sharing a key, same sentence first; return (unmatched old, unmatched new)."""
    old, new = list(old), list(new)
    for same in (True, False):
        for item in list(old):
            hit = next((x for x in new if x[0] & item[0] and (not same or qnorm(x[2]) == qnorm(item[2]))), None)
            if hit:
                old.remove(item)
                new.remove(hit)
    return old, new

def diff(old_text: str, new_text: str) -> list:
    """What an edit lost, changed or added; added citations and sources carry "(ok)". An empty list means a pure rephrase."""
    (old, old_src, old_sents), (new, new_src, new_sents) = doc_items(old_text), doc_items(new_text)
    out = []
    for kind in old:
        lost, added = pair(old[kind], new[kind])
        name = "quote missing or altered" if kind == "quotes" else f"{kind[:-1]} missing"
        out += [f"{name}: {label} (was in: {excerpt(unit, 120)})" for _, label, unit in lost]
        ok = " (ok)" if kind not in ("numbers", "quotes") else ""  # an edit may add citations, never facts
        out += [f"{kind[:-1]} added{ok}: {label} (in: {excerpt(unit, 120)})" for _, label, unit in added]
    for n in sorted(set(old_src) | set(new_src)):
        a, b = old_src.get(n), new_src.get(n)
        if not a:
            out.append(f"source [{n}] added (ok): {b}")
        elif norm_url(a) != (b and norm_url(b)):
            out.append(f"source [{n}] changed: {a} -> {b or '(none)'}")
    return out + detached(old_sents, new_sents)

def main(argv=None) -> int:
    setup_console()
    parser = argparse.ArgumentParser(prog="python scripts/vafer_check.py",
                                     description="Snapshot pages and check a vafer-research report.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    fetch_p = sub.add_parser("fetch", help="download pages into <run>/pages")
    fetch_p.add_argument("run", type=Path)
    fetch_p.add_argument("urls", nargs="+")
    check_p = sub.add_parser("check", help="check <run>/report.md, or one draft with --section (offline, advisory)")
    check_p.add_argument("run", type=Path)
    check_p.add_argument("--section", metavar="ID", help="check sections/<ID>.md only; writes nothing")
    asm_p = sub.add_parser("assemble", help="write <run>/report.md from sections/ with numbered citations")
    asm_p.add_argument("run", type=Path)
    asm_p.add_argument("--title", default="Sources", help="Sources heading, in the reader's language")
    diff_p = sub.add_parser("diff", help="compare an edited report with its previous version")
    diff_p.add_argument("old", type=Path)
    diff_p.add_argument("new", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "fetch":
        return cmd_fetch(args.run, args.urls)
    if args.cmd == "assemble":
        return cmd_assemble(args.run, args.title)
    if args.cmd == "diff":
        if not args.old.is_file() or not args.new.is_file():
            print(f"error: file missing: {args.old if not args.old.is_file() else args.new}", file=sys.stderr)
            return 2
        changes = diff(read_text(args.old), read_text(args.new))
        bad = sum("(ok)" not in c for c in changes)  # additions alone pass
        print("\n".join(changes + [f"diff: {bad} problem{'s' if bad != 1 else ''}"
                                    if bad else "diff: clean (numbers, citations, quotes, sources kept)"]))
        return 1 if bad else 0
    if args.section:
        if not (args.run / "sections" / f"{args.section}.md").is_file():
            print(f"error: section draft missing: {args.run / 'sections' / args.section}.md", file=sys.stderr)
            return 2
        flags = check_section(args.run, args.section)
        sev = [f["severity"] for f in flags]
        print(f"section {args.section}: {len(flags)} flags ({sev.count('high')} high, {sev.count('medium')} medium, "
              f"{sev.count('low')} low)")
        for f in flags:
            print(f"{f['severity']} {f['kind']}: {f['excerpt']} — {f['detail']}")
        return 0
    if not args.run.is_dir() or not (args.run / "report.md").is_file():
        print(f"error: run folder or report.md missing: {args.run}", file=sys.stderr)
        return 2
    result = check(args.run)
    print(f"{result['summary']}\nSource mix: {result['mix']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
