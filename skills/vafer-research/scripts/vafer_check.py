#!/usr/bin/env python
"""vafer_check: snapshot cited pages and check a vafer-research report against them.

Usage:
  python scripts/vafer_check.py fetch <run> <url> [<url> ...]
  python scripts/vafer_check.py check <run>
  python scripts/vafer_check.py diff <old.md> <new.md>

Stdlib only. `check` never touches the network and is advisory (exit 0),
except when the run folder or report.md is missing (exit 2). `diff` exits 1 when an edit lost or
changed a number, citation, quote or source entry, or detached a citation; additions alone pass.
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
RECEIPT = re.compile(r'^\s*[-*+]\s+(?P<fact>.*?)["“„](?P<span>[^"“”\n]+)["”“]\s*(?P<url>https?://\S+|file:///\S+)')
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
SOURCE_TITLES = ("sources", "references", "kaynaklar", "kaynakça", "πηγές", "източници")
SOURCE_ENTRY = re.compile(r"^\s*(?:[-*]\s*)?\[(\d+)\]:?\s+(.*)$|^\s*(\d+)\.\s+(.*)$")
CHECK_LINE = re.compile(r"(?P<pre>(?:Source check|Kaynak kontrolü)[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
MIX_LINE = re.compile(r"(?P<pre>(?:Source mix|Kaynak dağılımı)[*_]*[ \t]*:[*_]*[ \t]*)(?P<val>[^\r\n]*)", re.I)
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
LEAK = re.compile(r"\[GAP\]|\[prior\]|\bCOVERED\b|\bPARTIAL\b|\bNOT-FOUND\b|\bNOT SEARCHED\b"
                  r"|(?i:\bresearcher\b|\bgap wave\b|\bwave 1\b)")
QMAP = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "‚": "'",
                      "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-"})
QUOTE_FLAGS = {"near": ("quote-near", "matches only after Turkish-aware case folding"),
               "missing": ("quote-mismatch", "quoted span not found in cited snapshots or receipts")}
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

def numbers(text: str, masked=False) -> list:
    """All number tokens in text (citations and URLs excluded), written-out scales included."""
    text = text if masked else mask(text)
    out = [Num(m.start(), m.end(), m.group(0), spelled(m)) for m in SPELL.finditer(text)
           if m.group("n") or m.group("yuz") or m.group("tail")]
    spans = [(n.start, n.end) for n in out]
    out += [Num(m.start(), m.end(), m.group(0), parse_number(m.group("n"), bool(m.group("neg"))))
            for m in NUM.finditer(text) if not any(s <= m.start() < e for s, e in spans)]
    return sorted(out, key=lambda n: n.start)

def rounds_to(src: Decimal, value: Decimal, places: int) -> bool:
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
        except (ArithmeticError, InvalidOperation):
            continue
        first = got if first is None else first
        for rv, rd in result.cands:
            if abs(got - rv) <= abs(rv) * Decimal("0.005") or rounds_to(got, rv, rd):
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

def load_receipts(run: Path) -> tuple:
    """Receipt spans and (label, unverified) pairs from notes/*.md, both keyed by normalized URL."""
    spans, labels = {}, {}
    for path in sorted((run / "notes").glob("*.md")):
        for line in read_text(path).splitlines():
            if m := RECEIPT.match(line):
                spans.setdefault(norm_url(m.group("url")), []).append(m.group("span"))
                labels.setdefault(norm_url(m.group("url")), []).append(receipt_label(line[m.end():]))
    return spans, labels

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

def parse_report(text: str):
    """Return (body_lines, sources {n: url})."""
    lines = text.splitlines()
    heads = [i for i, line in enumerate(lines) if (h := HEADING.match(line))
             and any(t.casefold() in h.group(1).casefold() for t in SOURCE_TITLES)]
    cut = heads[-1] if heads else None
    sources = {}
    for line in lines[cut + 1:] if cut is not None else []:
        m = SOURCE_ENTRY.match(line)
        url = URL_RX.search(line) if m else None
        if url:
            sources[int(m.group(1) or m.group(3))] = url.group(0).rstrip(".,;:")
    return (lines[:cut] if cut is not None else lines), sources

def sentences(body_lines) -> list:
    """Split body prose into sentences; table rows stay whole; skip headings, fences, check and date lines."""
    out, fenced = [], False
    for line in body_lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if (fenced or HEADING.match(line) or CHECK_LINE.search(line) or MIX_LINE.search(line)
                or DATE_LINE.match(line) or not line.strip()):
            continue
        line, parts = LIST_MARK.sub("", line, count=1).strip(), []
        if line.startswith("|"):
            out.append(line)
            continue
        cuts = [0] + [m.end() for m in SENT_END.finditer(line)] + [len(line)]
        for part in (line[a:b].strip() for a, b in zip(cuts, cuts[1:])):
            if parts and (re.fullmatch(r"(?:\s*\[[^\]]+\]\s*[.,;]?)+", part) or ABBR.search(parts[-1])):
                parts[-1] += " " + part
            else:
                parts.append(part)
        out.extend(p for p in parts if p.strip())
    return out

def excerpt(text: str, limit=140) -> str:
    text = squash(text).replace("|", "\\|")
    return text if len(text) <= limit else text[:limit - 1] + "…"

class Checker:
    """Holds evidence for one run and collects flags."""
    def __init__(self, run: Path):
        (self.receipts, self.labels), self.snaps = load_receipts(run), load_snapshots(run)
        self.flags, self._pool = [], {}
        self.figures = self.matched = self.eq_ok = self.eq_bad = 0
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
    def pool(self, url: str) -> list:
        key = norm_url(url)
        if key not in self._pool:
            self._pool[key] = [c for t in self.texts([url]) for n in numbers(t) for c in n.cands]
        return self._pool[key]
    def flag(self, kind, sentence, urls, detail):
        self.flags.append({"kind": kind, "excerpt": excerpt(sentence), "urls": list(dict.fromkeys(urls)),
                           "detail": detail})
    def check_number(self, num: Num, urls, sentence):
        urls = [u for u in urls if self.has_evidence(u)]
        if not urls:
            return
        self.figures += 1
        if any(num_matches(num, self.pool(u)) for u in urls):
            self.matched += 1
        else:
            low = " (year; low severity)" if is_year(num) else ""
            self.flag("number-mismatch", sentence, urls, f"{num.text.strip()} not found in cited sources{low}")
    def check_sentence(self, sentence: str, sources: dict):
        masked = mask(sentence)
        cites = [(m.start(), expand_cites(m.group(1))) for m in CITE.finditer(sentence)]
        cited = [n for _, ns in cites for n in ns]
        urls = [sources[n] for n in cited if n in sources]
        nums = numbers(masked, masked=True)
        used = set()
        uncited, low = ("uncited-table", " (table row; low severity)") if sentence.startswith("|") else ("uncited", "")
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
                elif not cited:
                    self.flag(uncited, sentence, [], f"equation input {num.text.strip()} has no citation{low}")
        rest = [n for n in nums if n.start not in used]
        if cited:
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
            loose = [n.text.strip() for n in rest if not is_year(n) and not is_small_int(n)]
            if loose:
                self.flag(uncited, sentence, [], "numbers without citation: " + ", ".join(loose) + low)
        return cited

def old_dispositions(path: Path) -> dict:
    """Filled-in dispositions of a previous check.md, keyed by (kind, report excerpt), in row order."""
    old = {}
    for line in read_text(path).splitlines() if path.exists() else []:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) >= 6 and re.fullmatch(r"F\d+", cells[0]):
            disp = " | ".join(cells[5:]).strip()
            if disp.removeprefix("disposition:").strip():
                old.setdefault((cells[1], cells[2]), []).append(disp)
    return old

def check(run: Path) -> dict:
    """Run every check; write check.md and update the Source check line."""
    report_path = run / "report.md"
    text = read_text(report_path)
    body, sources = parse_report(text)
    checker = Checker(run)
    first_seen = {}
    h2 = [i for i, line in enumerate(body) if line.startswith("## ")]
    cut = h2[1] if len(h2) > 1 else len(body)  # first section: text before the second `## ` heading
    for first, part in ((True, body[:cut]), (False, body[cut:])):
        for sentence in sentences(part):
            cited = checker.check_sentence(sentence, sources)
            for n in cited:
                first_seen.setdefault(n, sentence)
            urls = [sources[n] for n in cited if n in sources]
            if urls and all(checker.is_lead(u) for u in urls):
                checker.flag("lead-only", sentence, urls, "every cited source is lead-class (wiki, forum, blog, "
                             "aggregator)" + (" (first section; high severity)" if first else " (medium severity)"))
    for n, sentence in first_seen.items():
        if n not in sources:
            checker.flag("dangling", sentence, [], f"[{n}] has no entry in the sources section")
    for n, url in sorted(sources.items()):
        if n not in first_seen:
            checker.flag("unused", f"[{n}] {url}", [url], "source entry is never cited in the body")
        if not checker.has_evidence(url):
            checker.flag("unverifiable", f"[{n}] {url}", [url], "no page snapshot and no receipt for this URL")
    for line in (line for line in body if not CHECK_LINE.search(line)):
        for m in LEAK.finditer(line):
            checker.flag("label-leak", line, [], f"internal label `{m.group(0)}` in report body")

    evidence = "page snapshots" if checker.snaps else "note receipts"
    eqs = (f"{checker.eq_ok} equation{'s' if checker.eq_ok != 1 else ''} correct"
           + (f", {checker.eq_bad} wrong" if checker.eq_bad else ""))
    old = old_dispositions(run / "check.md")  # holds filled-in dispositions only
    disps = [(old.get((f["kind"], f["excerpt"])) or ["disposition:"]).pop(0) for f in checker.flags]
    count = len(checker.flags)
    summary = (f"script, {evidence} — {checker.matched} of {checker.figures} figures matched, {eqs}, "
               f"{count} flag{'s' if count != 1 else ''}, {disps.count('disposition:')} open (check.md)")
    cited_urls = {norm_url(sources[n]): sources[n] for n in first_seen if n in sources}
    classes = [checker.source_class(u) for u in cited_urls.values()]
    mix = ", ".join(f"{classes.count(c)} {c}" for c in MIX)

    rows = ["# Source check", "", summary, "", f"Source mix: {mix}", "",
            "| id | kind | report excerpt | cited | expected / found | disposition |",
            "|---|---|---|---|---|---|"]
    for i, (f, disp) in enumerate(zip(checker.flags, disps), 1):
        urls = ", ".join(f["urls"]) or "—"
        rows.append(f"| F{i} | {f['kind']} | {f['excerpt']} | {urls} | {excerpt(f['detail'], 200)} | {disp} |")
    rows += ["", "Disposition: fixed / derived / false alarm: <reason> / † (marked unverified, with a footnote).", ""]
    write_text(run / "check.md", "\n".join(rows))

    path = run / "evidence.md" if (run / "evidence.md").exists() else report_path  # never both
    old_text = read_text(path)
    updated = CHECK_LINE.sub(lambda m: m.group("pre") + summary, old_text)
    if path != report_path:
        updated = MIX_LINE.sub(lambda m: m.group("pre") + mix, updated)
    if updated != old_text:
        write_text(path, updated)
    return {"summary": summary, "mix": mix, "flags": checker.flags, "figures": checker.figures,
            "matched": checker.matched, "eq_ok": checker.eq_ok, "eq_bad": checker.eq_bad}

def doc_items(text: str) -> tuple:
    """Numbers, citation markers and 4+ word quotes of a report body as (keys, label, unit); sources; sentences."""
    body, sources = parse_report(text)
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
    sub.add_parser("check", help="check <run>/report.md (offline, advisory)").add_argument("run", type=Path)
    diff_p = sub.add_parser("diff", help="compare an edited report with its previous version")
    diff_p.add_argument("old", type=Path)
    diff_p.add_argument("new", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "fetch":
        return cmd_fetch(args.run, args.urls)
    if args.cmd == "diff":
        if not args.old.is_file() or not args.new.is_file():
            print(f"error: file missing: {args.old if not args.old.is_file() else args.new}", file=sys.stderr)
            return 2
        changes = diff(read_text(args.old), read_text(args.new))
        bad = sum("(ok)" not in c for c in changes)  # additions alone pass
        print("\n".join(changes + [f"diff: {bad} problem{'s' if bad != 1 else ''}"
                                    if bad else "diff: clean (numbers, citations, quotes, sources kept)"]))
        return 1 if bad else 0
    if not args.run.is_dir() or not (args.run / "report.md").is_file():
        print(f"error: run folder or report.md missing: {args.run}", file=sys.stderr)
        return 2
    result = check(args.run)
    print(f"{result['summary']}\nSource mix: {result['mix']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
