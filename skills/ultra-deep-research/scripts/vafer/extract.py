"""Deterministic, offline extraction with source-local passage locators.

Extracted text is untrusted source data, never executable instructions. A
successful parse does not establish that the captured document is complete.
The caller's completeness claim is preserved unless an omission is detected.
"""

from __future__ import annotations

import codecs
import importlib
import posixpath
import re
import stat
import unicodedata
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

MAX_PASSAGE_CHARS = 4000
MAX_INPUT_BYTES = 128 * 1024 * 1024
MAX_ZIP_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_ZIP_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ZIP_MEMBERS = 10000
MAX_PDF_PAGE_STREAM_BYTES = 32 * 1024 * 1024
EXTRACTOR_VERSION = "2"


class ExtractionError(ValueError):
    """The file cannot be safely or meaningfully extracted by this extractor."""


def _segments(text: str):
    """Yield bounded slices, keeping paragraph boundaries whenever possible."""
    start = 0
    while start < len(text):
        while start < len(text) and text[start].isspace():
            start += 1
        if start == len(text):
            break
        end = min(start + MAX_PASSAGE_CHARS, len(text))
        if end < len(text):
            candidates = [m.start() for m in re.finditer(r"\s", text[start:end])]
            if candidates and candidates[-1] >= MAX_PASSAGE_CHARS // 2:
                end = start + candidates[-1]
        trimmed_end = end
        while trimmed_end > start and text[trimmed_end - 1].isspace():
            trimmed_end -= 1
        if trimmed_end > start:
            yield start, trimmed_end
        start = end


def _append(passages: list[dict], text: str, locator: dict) -> None:
    for part, (start, end) in enumerate(_segments(text), 1):
        passages.append({
            "id": f"p{len(passages) + 1:06d}",
            "text": text[start:end],
            "locator": {**locator, "part": part, "char_start": start, "char_end": end},
        })


def _decode(data: bytes, *, markup: bool = False) -> str:
    encoding = "utf-8-sig"
    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        encoding = "utf-32"
    elif data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    elif markup:
        # Use an explicit declaration rather than guessing a legacy encoding.
        match = re.search(
            rb"(?:encoding\s*=\s*['\"]|charset\s*=\s*['\"]?)([A-Za-z0-9._-]+)",
            data[:4096], re.IGNORECASE,
        )
        if match:
            encoding = match.group(1).decode("ascii")
    try:
        text = data.decode(encoding)
    except (UnicodeError, LookupError) as exc:
        raise ExtractionError(f"Cannot decode text as {encoding}; provide a supported text encoding.") from exc
    if "\x00" in text:
        raise ExtractionError("Decoded text contains NUL bytes; this may be a binary or misencoded file.")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _text_passages(text: str, *, markdown: bool = False) -> list[dict]:
    passages: list[dict] = []
    paragraph: list[tuple[int, str]] = []
    headings: list[tuple[int, str]] = []

    def flush() -> None:
        if not paragraph:
            return
        joined = "\n".join(line for _, line in paragraph)
        first_line = paragraph[0][0]
        for start, end in _segments(joined):
            line_start = first_line + joined.count("\n", 0, start)
            line_end = first_line + joined.count("\n", 0, end - 1)
            locator = {
                "line_start": line_start,
                "line_end": line_end,
                "column_start": start - joined.rfind("\n", 0, start),
                # Columns are one-based; the ending column is exclusive.
                "column_end": end - joined.rfind("\n", 0, end),
            }
            if headings:
                locator["headings"] = [title for _, title in headings]
            passages.append({"id": f"p{len(passages) + 1:06d}", "text": joined[start:end], "locator": locator})
        paragraph.clear()

    for number, line in enumerate(text.split("\n"), 1):
        heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line) if markdown else None
        if heading:
            flush()
            level, title = len(heading.group(1)), heading.group(2)
            headings[:] = [(depth, name) for depth, name in headings if depth < level]
            headings.append((level, title))
            paragraph.append((number, line))
            flush()
        elif line.strip():
            paragraph.append((number, line))
        else:
            flush()
    flush()
    return passages


def _capture_quality(passages: list[dict], *, capture_kind: str, format_name: str,
                     raw_text: str | None = None) -> dict:
    """Flag observable capture defects, never source truth or topical relevance.

    Host metadata and UI-only screens are useful diagnostics but remain source
    data: retain every passage, and do not interpret instructions in them.
    """
    if not passages:
        return {"status": "empty", "reasons": ["no-text"]}
    if format_name not in {"txt", "md", "html"}:
        return {"status": "usable", "reasons": []}
    text = raw_text if raw_text is not None else "\n".join(p["text"] for p in passages)
    reasons: list[str] = []
    headers = list(re.finditer(
        r"^.*\bSource:\s*(?:open|find|click|screenshot)\(.*?\bTotal lines:\s*(\d+)[^\n]*$",
        text, re.MULTILINE,
    ))
    host_capture = capture_kind in {"host-snapshot", "excerpt"} or bool(headers)
    source_line = re.compile(r"^L(\d+)(?:@P\d+)?:[ \t]?(.*)$", re.MULTILINE)
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        shown = {int(match[1]) for match in source_line.finditer(text, header.end(), end)}
        if shown and len(shown) < int(header[1]):
            reasons.append("host-lines-omitted")
            break
    if host_capture and re.search(
        r"^\s*(?:Warning:\s*)?(?:output|response|content) (?:was )?truncated\b|"
        r"\[\.\.\.\s*(?:\d+\s+(?:tokens|lines|characters)\s+)?(?:omitted|truncated)\b[^\]]*\]",
        text, re.MULTILINE | re.IGNORECASE,
    ):
        reasons.append("truncation-marker")

    if host_capture or format_name == "html":
        def normalized(value: str) -> str:
            return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                           if not unicodedata.combining(c))

        # An actual policy document is a valid research object. A UI label alone
        # must not invalidate it; require a separate consent/modal signal.
        privacy = re.compile(r"\b(?:cookies?|privacy|cerez|gizlilik|kisisel veri\w*)\b")
        controls = re.compile(
            r"^(?:modal content|accept all(?: cookies)?|reject all(?: cookies)?|"
            r"manage cookies|cookie settings|cookie preferences|close|"
            r"tumunu kabul et|tumunu reddet|kabul et|reddet|cerez ayarlari|kapat)[.!]?$"
        )
        numbered = [match[2].strip() for match in source_line.finditer(text) if match[2].strip()]
        body = numbered or [line.strip() for line in text.splitlines() if line.strip()]
        title = next((line.strip() for line in text.splitlines() if line.strip()), "")
        # In numbered host output, the first line is usually the page title;
        # for extracted HTML it is usually the first visible heading.
        policy_title = bool(re.search(
            r"\b(?:privacy policy|cookie policy|cookie notice|gizlilik|cerez politikasi)\b",
            normalized(title),
        ))
        normalized_body = [normalized(line) for line in body]
        has_control = any(controls.fullmatch(line) for line in normalized_body)
        has_privacy = any(privacy.search(line) for line in normalized_body)
        other = [original for original, line in zip(body, normalized_body)
                 if not controls.fullmatch(line) and not privacy.search(line)]
        # Permit only a few short site/agency labels around the consent text.
        # Any substantive article paragraph prevents the UI-only diagnosis.
        if (has_control and has_privacy and not policy_title
                and len(other) <= 3 and sum(len(line) for line in other) <= 160):
            reasons.append("website-chrome-only")
    return {"status": "suspect" if reasons else "usable", "reasons": reasons}


_IGNORED_TAGS = {"script", "style", "head", "template", "noscript"}
_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "body", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "tbody", "td", "th", "thead", "tr", "ul",
}


def _normal_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "")


def _clean_markup(text: str) -> str:
    return "\n".join(line.strip() for line in text.split("\n")).strip()


class _HTMLBlocks(HTMLParser):
    """Conservative visible-text fallback; locators are explicitly synthetic."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ignored: list[str] = []
        self.parts: list[str] = []
        self.blocks: list[str] = []
        self.pre_depth = 0

    def flush(self) -> None:
        text = _clean_markup("".join(self.parts))
        if text:
            self.blocks.append(text)
        self.parts.clear()

    def handle_starttag(self, tag: str, attrs) -> None:
        if self.ignored:
            if tag in _IGNORED_TAGS:
                self.ignored.append(tag)
            return
        if tag in _IGNORED_TAGS:
            self.flush()
            self.ignored.append(tag)
        elif tag in _BLOCK_TAGS:
            self.flush()
            if tag == "pre":
                self.pre_depth += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.ignored:
            if tag in self.ignored:
                index = len(self.ignored) - 1 - self.ignored[::-1].index(tag)
                del self.ignored[index:]
            return
        if tag in _BLOCK_TAGS:
            self.flush()
            if tag == "pre":
                self.pre_depth = max(0, self.pre_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            self.parts.append(data if self.pre_depth else _normal_text(data))


def _html(data: bytes) -> tuple[list[dict], str, str, list[str], bool]:
    raw = _decode(data, markup=True)
    warnings = [
        "HTML block locators address extracted text, not original DOM positions. "
        "Script-generated content is not executed; extraction may omit content."
    ]
    extractor, version = "stdlib-html", EXTRACTOR_VERSION
    extracted: str | None = None
    try:
        module = importlib.import_module("trafilatura")
    except ImportError:
        warnings.append("Optional trafilatura is unavailable; using basic HTML visible-text extraction.")
    else:
        try:
            candidate = module.extract(raw, output_format="txt", include_comments=False, include_tables=True, favor_recall=True)
            if isinstance(candidate, str) and candidate.strip():
                extracted = candidate
                extractor = "trafilatura"
                version = str(getattr(module, "__version__", "unknown"))
            else:
                warnings.append("Trafilatura returned no main text; using basic HTML visible-text extraction.")
        except Exception as exc:
            warnings.append(f"Trafilatura failed ({type(exc).__name__}); using basic HTML visible-text extraction.")
    if extracted is not None:
        blocks = re.split(r"\n\s*\n", extracted)
    else:
        parser = _HTMLBlocks()
        try:
            parser.feed(raw)
            parser.close()
            parser.flush()
        except Exception as exc:
            raise ExtractionError(f"HTML parsing failed: {type(exc).__name__}.") from exc
        if parser.ignored:
            warnings.append("HTML has an unclosed ignored element; some text could not be recovered.")
        blocks = parser.blocks
    passages: list[dict] = []
    for index, block in enumerate(blocks, 1):
        _append(passages, block, {"block": index, "synthetic": True})
    # Main-content extraction and non-rendered HTML cannot establish full coverage.
    return passages, extractor, version, warnings, True


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _xml(data: bytes, label: str) -> ET.Element:
    # The marker is ASCII in UTF-8 and NUL-interleaved in UTF-16/32.
    if b"<!ENTITY" in data.replace(b"\x00", b"").upper():
        raise ExtractionError(f"Entity declarations are not supported in EPUB XML: {label}.")
    try:
        return ET.fromstring(data)
    except (ET.ParseError, ValueError) as exc:
        raise ExtractionError(f"Malformed EPUB XML: {label}.") from exc


def _member_path(base: str, href: str) -> str:
    try:
        parts = urlsplit(href)
    except ValueError as exc:
        raise ExtractionError("Invalid EPUB resource reference.") from exc
    path = unquote(parts.path)
    if parts.scheme or parts.netloc or path.startswith("/") or "\\" in path or "\x00" in path:
        raise ExtractionError("EPUB resources must be local, safe archive paths.")
    normalized = posixpath.normpath(posixpath.join(posixpath.dirname(base), path))
    if normalized in {".", ".."} or normalized.startswith("../") or re.match(r"^[A-Za-z]:", normalized):
        raise ExtractionError("EPUB resource reference escapes the archive root.")
    return normalized


def _check_archive(archive: zipfile.ZipFile) -> set[str]:
    infos = archive.infolist()
    if len(infos) > MAX_ZIP_MEMBERS:
        raise ExtractionError("EPUB has too many archive members.")
    if sum(info.file_size for info in infos) > MAX_ZIP_UNCOMPRESSED_BYTES:
        raise ExtractionError("EPUB exceeds the uncompressed size limit.")
    names: set[str] = set()
    for info in infos:
        name = info.filename
        # ZipInfo normalizes Windows separators and truncates NUL on read.
        # Inspect the original header name as well as its normalized value.
        original_name = info.orig_filename
        if not name or name.startswith("/") or "\\" in original_name or "\x00" in original_name or ".." in name.split("/") or re.match(r"^[A-Za-z]:", name):
            raise ExtractionError("EPUB contains an unsafe archive member path.")
        if info.flag_bits & 1:
            raise ExtractionError("Encrypted EPUB archive members are not supported.")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ExtractionError("EPUB symbolic-link archive members are not supported.")
        if info.file_size > MAX_ZIP_MEMBER_BYTES:
            raise ExtractionError("EPUB member exceeds the size limit.")
        normalized = posixpath.normpath(name)
        if normalized in names:
            raise ExtractionError("EPUB contains duplicate archive member paths.")
        names.add(normalized)
    return names


def _xhtml_passages(root: ET.Element, filename: str, *, linear: bool) -> list[dict]:
    passages: list[dict] = []
    headings: list[tuple[int, str]] = []
    paragraph_number = 0

    def inline(element: ET.Element) -> str:
        tag = _local_name(element.tag)
        if tag in _IGNORED_TAGS:
            return ""
        if tag == "br":
            return "\n"
        return _normal_text(element.text) + "".join(inline(child) + _normal_text(child.tail) for child in element)

    def emit(text: str, fragment: str | None) -> None:
        nonlocal paragraph_number
        text = _clean_markup(text)
        if not text:
            return
        paragraph_number += 1
        locator: dict = {"file": filename, "paragraph": paragraph_number, "linear": linear}
        if fragment:
            locator["fragment"] = fragment
        if headings:
            locator["headings"] = [title for _, title in headings]
        _append(passages, text, locator)

    def walk(element: ET.Element, inherited_fragment: str | None = None) -> None:
        tag = _local_name(element.tag)
        if tag in _IGNORED_TAGS:
            return
        fragment = element.get("id") or element.get("{http://www.w3.org/XML/1998/namespace}id") or inherited_fragment
        if re.fullmatch(r"h[1-6]", tag):
            text = _clean_markup(inline(element))
            level = int(tag[1])
            headings[:] = [(depth, title) for depth, title in headings if depth < level]
            if text:
                headings.append((level, text))
            emit(text, fragment)
            return
        parts = [_normal_text(element.text)]
        for child in element:
            child_tag = _local_name(child.tag)
            if child_tag in _BLOCK_TAGS:
                emit("".join(parts), fragment)
                parts.clear()
                walk(child, fragment)
            else:
                parts.append(inline(child))
            parts.append(_normal_text(child.tail))
        emit("".join(parts), fragment)

    body = next((node for node in root.iter() if _local_name(node.tag) == "body"), None)
    if body is None:
        raise ExtractionError(f"EPUB XHTML has no body: {filename}.")
    walk(body)
    return passages


def _epub(path: Path) -> tuple[list[dict], list[str], bool]:
    warnings: list[str] = []
    passages: list[dict] = []
    partial = False
    try:
        with zipfile.ZipFile(path) as archive:
            names = _check_archive(archive)

            def read(name: str) -> bytes:
                if name not in names:
                    raise ExtractionError(f"EPUB references a missing archive member: {name}.")
                return archive.read(name)

            if "META-INF/encryption.xml" in names:
                encryption = _xml(read("META-INF/encryption.xml"), "encryption.xml")
                if any(_local_name(node.tag) == "encrypteddata" for node in encryption.iter()):
                    raise ExtractionError("Encrypted EPUB resources are not supported.")
            container = _xml(read("META-INF/container.xml"), "container.xml")
            rootfiles = [node for node in container.iter() if _local_name(node.tag) == "rootfile"]
            if not rootfiles or not rootfiles[0].get("full-path"):
                raise ExtractionError("EPUB container does not identify a package document.")
            if len(rootfiles) > 1:
                warnings.append("EPUB has multiple renditions; only the first package was processed.")
                partial = True
            opf_path = _member_path("", rootfiles[0].get("full-path", ""))
            package = _xml(read(opf_path), opf_path)
            manifest = next((node for node in package if _local_name(node.tag) == "manifest"), None)
            spine = next((node for node in package if _local_name(node.tag) == "spine"), None)
            if manifest is None or spine is None:
                raise ExtractionError("EPUB package requires both a manifest and a spine.")
            items: dict[str, ET.Element] = {}
            for item in manifest:
                if _local_name(item.tag) != "item":
                    continue
                identity = item.get("id")
                if not identity or identity in items or not item.get("href"):
                    raise ExtractionError("EPUB manifest has a missing or duplicate item identity.")
                items[identity] = item
            refs = [node for node in spine if _local_name(node.tag) == "itemref"]
            if not refs:
                raise ExtractionError("EPUB spine is empty.")
            visited: set[str] = set()
            for ref in refs:
                identity = ref.get("idref", "")
                if identity not in items:
                    raise ExtractionError("EPUB spine references an unknown manifest item.")
                item = items[identity]
                filename = _member_path(opf_path, item.get("href", ""))
                if filename in visited:
                    raise ExtractionError("EPUB spine repeats a resource; reading order is ambiguous.")
                visited.add(filename)
                if filename not in names:
                    raise ExtractionError(f"EPUB references a missing archive member: {filename}.")
                media_type = item.get("media-type", "")
                if media_type not in {"application/xhtml+xml", "text/html"}:
                    warnings.append(f"Unsupported spine resource was not read: {filename} ({media_type or 'unknown media type'}).")
                    partial = True
                    continue
                root = _xml(read(filename), filename)
                omitted_kinds = sorted({
                    _local_name(node.tag) for node in root.iter()
                    if _local_name(node.tag) in {
                        "img", "svg", "math", "audio", "video", "canvas",
                        "object", "embed", "iframe", "script",
                    }
                })
                if omitted_kinds:
                    warnings.append(
                        f"EPUB resource {filename} contains content not fully represented by "
                        f"text extraction: {', '.join(omitted_kinds)}."
                    )
                    partial = True
                current = _xhtml_passages(root, filename, linear=ref.get("linear", "yes") != "no")
                if not current:
                    warnings.append(f"EPUB spine resource yielded no text: {filename}.")
                    partial = True
                passages.extend(current)
            for item in items.values():
                if item.get("media-type") not in {"application/xhtml+xml", "text/html"}:
                    continue
                if "nav" in item.get("properties", "").split():
                    continue
                filename = _member_path(opf_path, item.get("href", ""))
                if filename not in visited:
                    warnings.append(f"Textual EPUB resource outside the spine was not read: {filename}.")
                    partial = True
    except ExtractionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ExtractionError(f"Cannot read EPUB archive: {type(exc).__name__}.") from exc
    return passages, warnings, partial


def _pdf_inline_image(contents) -> bool:
    return contents is not None and any(operator == b"INLINE IMAGE" for _, operator in contents.operations)


def _pdf_image_resources(resources, reader, *, seen=None, depth: int = 0) -> bool:
    """Find image XObjects, including images inside nested form resources.

    Resource presence is deliberately conservative: an unused image resource
    may also require review. This does not attempt to understand vector art.
    """
    if resources is None:
        return False
    if depth > 32:
        raise ValueError("PDF form resources exceed the inspection depth limit")
    seen = set() if seen is None else seen
    resources = resources.get_object()
    key = ("resources", id(resources))
    if key in seen:
        return False
    seen.add(key)
    objects = resources.get("/XObject")
    if objects is None:
        return False
    for reference in objects.get_object().values():
        obj = reference.get_object()
        subtype = obj.get("/Subtype")
        if subtype == "/Image":
            return True
        if subtype != "/Form":
            continue
        key = ("form", id(obj))
        if key in seen:
            continue
        seen.add(key)
        if _pdf_image_resources(obj.get("/Resources"), reader, seen=seen, depth=depth + 1):
            return True
        if len(obj.get_data()) > MAX_PDF_PAGE_STREAM_BYTES:
            raise ValueError("PDF form exceeds the inspection size limit")
        from pypdf.generic import ContentStream
        if _pdf_inline_image(ContentStream(obj, reader)):
            return True
    return False


def _pdf(path: Path) -> tuple[list[dict], str, list[str], bool]:
    try:
        module = importlib.import_module("pypdf")
    except ImportError as exc:
        raise ExtractionError("PDF extraction requires the optional pypdf package.") from exc
    try:
        reader = module.PdfReader(str(path))
        if reader.is_encrypted:
            raise ExtractionError("Encrypted PDFs are not supported by the offline extractor.")
        count = len(reader.pages)
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"Cannot parse PDF: {type(exc).__name__}.") from exc
    passages: list[dict] = []
    warnings: list[str] = [
        "PDF extraction is text-only. Vector graphics, spatial layout, and visual meaning "
        "are not verified; a full-source claim still requires source-based review."
    ]
    partial = False
    for index in range(count):
        try:
            page = reader.pages[index]
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > MAX_PDF_PAGE_STREAM_BYTES:
                warnings.append(f"PDF physical page {index + 1} exceeds the content-stream size limit and was not extracted.")
                partial = True
                continue
            text = page.extract_text() or ""
            if not isinstance(text, str):
                raise ValueError("PDF extractor returned non-text content")
        except Exception as exc:
            warnings.append(f"PDF physical page {index + 1} could not be extracted ({type(exc).__name__}).")
            partial = True
            continue
        if not text.strip():
            warnings.append(f"PDF physical page {index + 1} yielded no text; it may be blank or require separate OCR.")
            partial = True
            continue
        try:
            has_images = _pdf_inline_image(contents) or _pdf_image_resources(page.get("/Resources"), reader)
        except Exception as exc:
            warnings.append(
                f"PDF physical page {index + 1} visual-resource inspection was incomplete "
                f"({type(exc).__name__}); extracted text does not establish full coverage."
            )
            partial = True
        else:
            if has_images:
                warnings.append(
                    f"PDF physical page {index + 1} contains image content not represented by "
                    "text extraction; separate visual review or OCR is required."
                )
                partial = True
        for paragraph, block in enumerate(re.split(r"\n\s*\n", text), 1):
            _append(passages, block, {"physical_page": index + 1, "paragraph": paragraph})
    return passages, str(getattr(module, "__version__", "unknown")), warnings, partial


def extract_file(
    path: Path, *, capture_kind: str = "original-file", completeness: str = "unknown"
) -> dict:
    """Extract a local file without network access or inferred source facts.

    ``char_start``/``char_end`` are zero-based offsets within the extracted
    paragraph or block, not byte offsets into the original file. Text-file
    line and column locators address the decoded, newline-normalized file.
    ``full`` is only a caller claim about source access, not semantic accuracy.
    """
    if capture_kind not in {"original-file", "host-snapshot", "excerpt"}:
        raise ExtractionError("capture_kind must be original-file, host-snapshot, or excerpt.")
    if completeness not in {"full", "partial", "unknown"}:
        raise ExtractionError("completeness must be full, partial, or unknown.")
    path = Path(path)
    try:
        if not path.is_file():
            raise ExtractionError("Extraction requires an existing regular file.")
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ExtractionError("Input file exceeds the extraction size limit.")
        suffix = path.suffix.lower()
        format_name = {".txt": "txt", ".md": "md", ".markdown": "md", ".html": "html", ".htm": "html", ".xhtml": "html", ".epub": "epub", ".pdf": "pdf"}.get(suffix)
        if format_name is None:
            raise ExtractionError(f"Unsupported file format: {suffix or '(no extension)' }.")
        extractor, version = f"stdlib-{format_name}", EXTRACTOR_VERSION
        warnings: list[str] = []
        partial = False
        raw_text: str | None = None
        if format_name in {"txt", "md"}:
            raw_text = _decode(path.read_bytes())
            passages = _text_passages(raw_text, markdown=format_name == "md")
        elif format_name == "html":
            passages, extractor, version, warnings, partial = _html(path.read_bytes())
        elif format_name == "epub":
            passages, warnings, partial = _epub(path)
        else:
            passages, version, warnings, partial = _pdf(path)
            extractor = "pypdf"
    except ExtractionError:
        raise
    except OSError as exc:
        raise ExtractionError(f"Cannot read input file: {type(exc).__name__}.") from exc
    if not passages:
        warnings.append("No text passages were extracted; this source has not been read in full.")
        partial = True
    if capture_kind == "excerpt":
        warnings.append("This capture is an excerpt and cannot establish full-source coverage.")
        partial = True
    quality = _capture_quality(passages, capture_kind=capture_kind,
                               format_name=format_name, raw_text=raw_text)
    diagnostics = {
        "host-lines-omitted": "Host output includes only some of the declared source lines; inspect surrounding source text when needed.",
        "truncation-marker": "Host output contains an explicit truncation marker; omitted content was not captured.",
        "website-chrome-only": "Capture appears limited to consent or modal text and short site labels; inspect or recapture the intended page body.",
    }
    for reason in quality["reasons"]:
        if reason in diagnostics:
            warnings.append(diagnostics[reason])
    if quality["status"] != "usable":
        partial = True
    # EPUB files reset their local counters; provide unique IDs across the book.
    for index, passage in enumerate(passages, 1):
        passage["id"] = f"p{index:06d}"
    return {
        "format": format_name,
        "extractor": extractor,
        "extractor_version": version,
        "completeness": "partial" if partial else completeness,
        "capture_quality": quality,
        "warnings": warnings,
        "passages": passages,
    }
