# hyperresearch read: acquisition (search, fetch, PDFs, open access, scholarly APIs)

Read on 2026-10-27 from the clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`
(version 0.12.0, HEAD `327498b`). The clone was treated as read-only. I did not
run its installer or pipeline, and I imported none of its code. Code paths
such as `web/base.py` are relative to `src/hyperresearch/`. The pipeline step
files live in `src/hyperresearch/skills/`, so `skills/hyperresearch-2-width-sweep.md`
and `...-2-width-sweep.md` both mean that folder. `README.md`, `pyproject.toml`
and `example-reports/` are at the clone root. `file:line` refers to that commit.

All 30 assigned files were read in full. I also opened these files where the
assigned ones referenced them: `core/config.py`, `core/profiles.py`, `core/hooks.py`
(the fetcher subagent prompt), `cli/install.py`, `cli/note.py` (`note show`),
`core/escalation.py`, `core/sync.py`, `core/db.py`, `core/agent_docs.py`,
`core/untrusted.py`, `mcp/server.py`, `skills/hyperresearch-2-width-sweep.md`,
`README.md`, `pyproject.toml` and `example-reports/`.

Anything marked **estimate** was not measured. Anything marked **platform** depends
on Claude Code or Codex behaviour, not on hyperresearch code.

---

## 1. Bottom line

- **Search is the agent's job and fetching is Python's.** The 16-step pipeline
  never calls a Python search provider. The orchestrator and the fetcher
  subagents search with the host's built-in WebSearch. Python fetches, extracts,
  gates, stores and enriches. `provider.search()` has exactly one caller,
  `cli/research.py:62` (`hpr research`), and no pipeline step uses that command.
- **The real fetch path is one CLI process per URL.** Sonnet fetcher subagents
  (10–12 in parallel in wave 1 of the `full` profile) each run `hpr fetch "<url>"`,
  then `note show`, then `note update`. With the default crawl4ai provider, every
  `hpr fetch` launches and tears down a fresh headless Chromium
  (`web/crawl4ai_provider.py:395-397`). `fetch-batch`, which reuses one browser
  through `arun_many`, is not what the fetcher prompt uses (`core/hooks.py:3084-3090`).
- **The quality drivers here are the PDF lane, crawl4ai's stealth browser and
  open-access substitution.** OA substitution swaps a paywalled abstract for a
  legal full text, but out of the box it covers only Europe PMC's biomedical
  subset (`core/oa.py:238-245`, `README.md:448`). The example report cites 97
  unique URLs, and 87 of them are arXiv, the easiest source to fetch.
- **The login-wall and junk gates are crude substring matches with real false
  positives.** A title containing "auth", "register", "sso", "sign in" or "log in"
  marks the page as a login wall. That catches "Professor…", "Association…",
  "Authority…", "Federal Register…" and "Design in…". The source is then dropped
  or queued for the human browser lane (`web/base.py:78-102`,
  `cli/fetch.py:365-382`). The probe in §14 reproduces this.
- **The cost is mostly LLM reading, not HTTP.** `note show -j` returns the whole
  body with no cap (`cli/note.py:162-227`). The fetcher reads every page it
  fetches, then writes a summary and 3–25 claims with verbatim quotes. The
  `full` profile targets 55–80 sources from 80–120 candidate URLs and
  40–100 planned searches, in about 1.5–2.5 h (`core/profiles.py:257-306`).

---

## 2. Who does what: agent versus Python

| Work | Done by | Where |
|---|---|---|
| Search plan in 3–4 lenses (breadth, citation depth, adversarial, period-pinned filings) | Orchestrator LLM | `skills/hyperresearch-2-width-sweep.md:30-80` |
| Web searches (40–100 planned in `full`) | Orchestrator, host WebSearch | step 2.2, `skills/...-2-width-sweep.md:93-99` |
| Academic discovery (`hpr scholar search`) | Orchestrator runs the CLI; Python queries the APIs and dedups | `core/agent_docs.py:73-86`, `cli/scholar_cmd.py` |
| URL dedup (exact string), utility scoring 0–18, batching | Orchestrator LLM | step 2.2–2.3, `...-2-width-sweep.md:97-124` |
| Fetch, extract, PDF, SSRF, gates, OA swap, DOI capture, note write, index | Python (`hpr fetch`) | `cli/fetch.py` |
| Relevance check, junk check, dedup by reading, summary, tags | Fetcher LLM (Sonnet) | `core/hooks.py:3079-3119` |
| Claims JSON with verbatim quotes (3–25 per source) | Fetcher LLM | `core/hooks.py:3120-3150` |
| Chase 3–8 cited primary sources per fetcher (WebSearch for URLs) | Fetcher LLM | `core/hooks.py:3152-3200`, `core/profiles.py:272-273` |
| Blocked-page escalation to the user's real Chrome | Browser-fetcher LLM via Claude-in-Chrome (Claude Code only) | `core/hooks.py:3347-3360`, `core/escalation.py:60-90` |
| Citation counts, venue, retractions, authority percentile | Python (`hpr sources score`, `sources retractions`) | `core/scholar.py:284-497` |

The fetcher's tools are `Bash, Read, Write, WebSearch` (`core/hooks.py:2965`), and
its model is `sonnet` by default (`core/profiles.py:52`). The agent docs forbid
WebFetch for source pages (`core/agent_docs.py:41`), so every page read goes
through `hpr fetch` and then `note show`.

---

## 3. Web providers and keys

Construction happens in `web/base.py:185-242`. The config default is `builtin`
(`core/config.py:243`), but Crawl4AI is a hard dependency (`pyproject.toml:32`), and
`hpr install` switches the vault to `crawl4ai` whenever it imports
(`cli/install.py:336-337`). In practice, runs use crawl4ai.

| Provider | Search | Fetch | Key / cost | Notes |
|---|---|---|---|---|
| `builtin` | no (`web/builtin.py:200-204`) | httpx through the SSRF gate, bs4 or stdlib extraction | free | No JS. Sends UA `hyperresearch/0.1` (`web/safe_http.py:41`, `web/builtin.py:212-216`), which many sites block. Fences code so `[[ ... ]]` is not read as a wiki-link (`web/builtin.py:24-58`). |
| `crawl4ai` | no (`web/crawl4ai_provider.py:589-593`) | local headless Chromium with patchright stealth (`UndetectedAdapter`) and PruningContentFilter `fit_markdown` | free, local | The pipeline is tuned for this one (`README.md:353`). Details in §4. |
| `exa` | yes, neural | `/contents` | `EXA_API_KEY` (paid; free tier exists) | Text capped at **8,000 chars** for both search and fetch (`web/exa_provider.py:41,76,94`). No PDF lane. `get_provider` passes no options (`web/base.py:213-216`). |
| `tavily` | yes, `search_depth="advanced"` | `extract` | `TAVILY_API_KEY` | Search `content` is Tavily's snippet, not the page (`web/tavily_provider.py:88`). |
| `parallel` | yes | `web_fetch` with full content | **no key**: Parallel Search MCP at `search.parallel.ai/mcp` (`web/parallel_provider.py:63`) | One MCP connection per call (`web/parallel_provider.py:118-137`). Session id is random per process (`web/parallel_provider.py:66`). README calls it "search only" (`README.md:355`), yet it fetches. |
| `serply` | yes, Google SERP | `/v1/request` as markdown | `SERPLY_API_KEY` | Search then fetches each hit **serially** (`web/serply_provider.py:70-81`). Fetch truncates to 8,000 chars (`web/serply_provider.py:88`). |

Since the pipeline never calls search, the four API providers matter to it only
as fetch backends. As fetch backends, Exa and Serply are worse than crawl4ai:
they cap content at 8,000 chars and skip the PDF lane, so a paper arrives truncated.

---

## 4. The fetch pipeline (`hpr fetch`, `cli/fetch.py:207-669`)

Order of operations:

1. `Vault.discover()` and `auto_sync()` (`cli/fetch.py:240-250`). Every CLI call
   rescans `research/**.md` and opens each file to probe its frontmatter
   (`core/sync.py:89-102`).
2. Exact-string duplicate check against `sources.url`
   (`core/fetcher.py:11-23`, `cli/fetch.py:254-296`). There is no URL
   canonicalization. `canonical_url` exists, but only for post-hoc independence
   scoring (`core/independence.py:36,94`).
3. A domain list (LinkedIn, X, Facebook, Instagram, TikTok) forces a visible
   browser when a login profile exists (`cli/fetch.py:298-304`, `core/config.py:45-48`).
4. `prov.fetch(url)`. On an exception, it attempts **OA rescue**
   (`cli/fetch.py:352-361`).
5. **Login-wall gate**: rescue, otherwise enqueue an escalation and exit with
   `AUTH_REQUIRED` (`cli/fetch.py:363-382`).
6. **Junk gate**: rescue, otherwise escalate if it is a bot wall and exit with
   `JUNK_CONTENT` (`cli/fetch.py:384-409`). PDF-lane failure reasons are appended (#82).
7. DOI or arXiv capture from the URL, meta tags and body (`cli/fetch.py:414-416`).
8. **OA substitution** when the page is thin and has a DOI (`cli/fetch.py:429-434`).
9. Tier and content-type heuristics (`cli/fetch.py:88-204,440-441`). For example,
   any `.gov` domain is `ground_truth`, PDFs are `paper`, and Wikipedia is `institutional`.
10. Write the note, save the raw PDF to `research/raw/<id>.pdf`, sync, record the
    source with `INSERT OR IGNORE`, and clean up if a race was lost
    (`cli/fetch.py:490-611`).

### crawl4ai lane (`web/crawl4ai_provider.py`)

- `BrowserConfig` keeps TLS verification on, and the crawl4ai flags
  `--ignore-certificate-errors*` are stripped from the launch on 0.7.3–0.9.4
  (`web/crawl4ai_provider.py:114-126,162-197,258-261`).
- Run config: `simulate_user=True`, `screenshot=True` on **every** fetch,
  `page_timeout` 30 s, and a JS smart-wait that waits 2 s and then polls
  `innerText.length` every 500 ms until it is stable twice. That gives a floor of
  about 3 s and a ceiling of about 11 s (`web/crawl4ai_provider.py:90-111,271-278`;
  `core/config.py:39-42`). The screenshot is discarded unless `--save-assets` is set.
- `fit_markdown` is preferred over `raw_markdown` (`web/crawl4ai_provider.py:415-423`).
  PruningContentFilter is lossy. Whether it drops data tables in practice is
  **unverified**.
- A navigation failure only raises for certificate errors
  (`web/crawl4ai_provider.py:401-403`). Every other failure (timeout, DNS,
  `ERR_ABORTED` on a download) comes back as empty content and is reported as
  junk, "Empty or near-empty content". The real error is lost, and the URL is
  not escalated.
- Redirect SSRF: the entry URL is checked before navigation, and the final URL
  after it (`web/crawl4ai_provider.py:200-225,305-307,404-409`). The code itself
  says blind SSRF through the request survives. Subresource loads (img, iframe,
  script) from a hostile page are not gated at all. This is my inference from
  the code: no request interception exists.
- `fetch_many` runs one browser for a batch via `arun_many`, and remaps results,
  which arrive in completion order, back to the URL each one requested
  (`web/crawl4ai_provider.py:460-587`). Concurrency comes from crawl4ai's default
  dispatcher, since none is configured. The defaults were **not checked**.
- `_fetch_visible` (login profile and visible window) always ignores certificate
  errors (`web/crawl4ai_provider.py:347-356`).
- On Windows, stdout and stderr are forced to UTF-8 at import
  (`web/crawl4ai_provider.py:35-44`, also `cli/__init__.py:21-31`).

### PDF lane (`web/pdf.py`)

- A URL is treated as a PDF when the path ends in `.pdf`, contains `/pdf/` or
  `/pdfs/`, or is an arXiv `/abs/` or `/pdf/` link (`web/pdf.py:35-48`). arXiv
  `/abs/` is rewritten to `/pdf/…​.pdf` (`web/pdf.py:133-139`). Magic bytes
  `%PDF-` decide in the end (`web/pdf.py:161-167`). The builtin lane also detects
  PDFs after download (`web/builtin.py:177-185`).
- The download uses a Chrome UA, a 25 MB cap and a 30 s timeout, with TLS
  verified and no unverified retry (`web/pdf.py:75-81,100-130`; `core/config.py:15,29`).
- Extraction is `pymupdf page.get_text("text")` per page, with pages joined by
  `---` (`web/pdf.py:184-207`). It keeps no layout, does no table handling and
  has **no OCR**: a scanned PDF fails with "no extractable text layer"
  (`web/pdf.py:198-204`).
- The title is the first line on page 1 longer than 10 chars (`web/pdf.py:208-214`).
  That is often a running header or an arXiv stamp (plausible, not measured).
- Failure reasons are kept in a module-level dict of 256 entries and surfaced
  next to the junk verdict (`web/pdf.py:274-299`).
- A PDF over 25 MB is refused. The lane then falls back to the browser, which
  gets binary or empty content, and the source is lost. Large government and
  IMF-style reports are at risk. The cap is configurable through `max_pdf_bytes`.

### SSRF gate and HTTP (`web/safe_http.py`)

- Only http and https are allowed. Every resolved address is checked: private,
  loopback, link-local, multicast, reserved, unspecified, CGNAT, IPv4-mapped and
  6to4 are all unwrapped and refused (`web/safe_http.py:99-119,228-286`).
- Redirects are followed manually, at most 5, with each hop re-checked. A
  Content-Length precheck and a streamed byte cap apply (10 MB HTML, 25 MB PDF,
  2 MB image) (`web/safe_http.py:289-353`).
- DNS rebinding is an accepted residual risk, documented at `web/safe_http.py:16-21`.
- An IDNA 2008 normalisation bug was fixed, so the checked host is the one httpx
  connects to (`web/safe_http.py:122-143,254-272`, commit `545946e`).
- There are no retries, no 429 handling and no HTTP/2 in this layer.

### Gates (`web/base.py:75-163`, thresholds `core/config.py:52-63`)

- **Login wall**: a substring match on the title, or content under 1,000 chars
  with a login word in its first 500 chars, or a URL path containing `/login`,
  `/signin`, `/signup`, `/auth`, `/sso` or `/register`. Any one of the three
  is enough (`web/base.py:87-102`). `/auth` also matches `/authors/` and `/authority/`.
- **Junk**: content under 300 chars. Or a bot signal in the title or the first
  2,000 chars of content: "cloudflare", "ray id", "access denied", "captcha" and
  others (`web/base.py:119-128`). Or an error signal: "an error occurred", "page
  not found", "the page you requested" and others (`web/base.py:131-138`). Then
  come PDF binary markers, a 5% binary or control-character ratio (deliberately
  not `ord>127`, `web/base.py:19-32`), and a cookie wall under 1,500 chars.
- `hpr fetch` applies both gates. **`fetch-batch` applies only the login gate**
  (`cli/fetch_batch.py:162-167`). `hpr research` applies only the login gate,
  with default thresholds (`cli/research.py:244`). The MCP `fetch_url` applies
  both but does no OA (`core/fetcher.py:134-165`).
- The fetcher prompt then tells the agent not to retry an AUTH_REQUIRED
  (`core/hooks.py:3030-3033`). A false-positive login wall is therefore final,
  unless the browser lane picks it up.

### Escalation lane

`maybe_enqueue_blocked_fetch` queues a blocked URL when the chrome lane is
enabled, the utility score is at least 8 (or absent), and fewer than 25 items
are queued for the run (`core/escalation.py:60-90`, `core/config.py:96-101`).
Exactly one browser-fetcher subagent drains the queue serially in the user's
real Chrome, through Claude-in-Chrome. CAPTCHAs, logins and 2FA always go to the
human (`core/hooks.py:3347-3360`). Codex has no browser lane, so queued items stay
queued (`skills/hyperresearch-2-width-sweep.md:249`).

---

## 5. Open-access substitution and rescue (`core/oa.py`)

- **Trigger for substitution**: the result is not a PDF, a DOI was found, and
  either the content is under 6,000 chars or the body contains a paywall phrase
  such as "purchase pdf" or "access through your institution"
  (`core/oa.py:89-101,187-207`; `core/config.py:185`).
- **Trigger for rescue**: the source could not be read at all. That means a
  fetch exception, a login wall, or junk including bot walls
  (`core/oa.py:859-882`; `cli/fetch.py:335-409`; `cli/fetch_batch.py:170-191`).
  The DOI comes from the URL and meta tags only, never the body.
- **Resolvers, in order** (`core/oa.py:215-245`):
  1. Unpaywall runs **only if `[scholar] contact_email` is set in
     config.toml** (`core/oa.py:238-239,771`). The order is best location,
     PDFs before landing pages, then version rank (published, accepted, submitted).
  2. Europe PMC needs no key and covers the OA subset only. It returns JATS
     `fullTextXML`, which is parsed into markdown with sections, keeping the
     abstract and dropping references (`core/oa.py:316-348,570-632`).
  3. CORE runs **only if `CORE_API_KEY` is set**. It tries CORE's own
     `fullText`, then CORE's PDF, then the source URLs CORE harvested
     (`core/oa.py:398-476`).
- `_try_candidates` makes at most 3 attempts. Each candidate URL is gated by
  `check_oa_url`, which refuses credentials, bare hostnames and private
  addresses, and ignores the allowlist. A candidate must pass the junk gate,
  beat the original length ("never shrink") and reach 6,000 chars
  (`core/oa.py:133-171,753-832`; `core/config.py:190`).
- **Disclosure**: a blockquote banner goes at the top of the body, and the
  wording differs for substituted and rescued notes. The note also gets `oa_*`
  frontmatter, an `oa` block in `note show -j`, and CLI and JSON fields
  (`core/oa.py:664-727`, `cli/note.py:195-219`, `cli/fetch.py:634-666`). Any
  version other than published gets a "Quote this source with care" line.
- **Docstring versus code**: the docstring says Europe PMC and CORE are resolved
  lazily, only after earlier copies fail (`core/oa.py:226-230`). In fact
  `_try_candidates` materialises the whole generator with
  `list(iter_oa_candidates(...))` (`core/oa.py:766`), so all three resolvers are
  queried up front. The metadata is cached, so the cost is small.
- Two different contact-email settings exist. Unpaywall reads
  `[scholar] contact_email` (`core/config.py:183`). OpenAlex and Crossref polite
  pools, and EDGAR, read the environment variable `HYPERRESEARCH_CONTACT_EMAIL`
  (`scholar/base.py:69-77`). Neither feeds the other.
- A placeholder contact is sent in spite of the README. Enrichment and OA HTTP
  send `User-Agent: hyperresearch (mailto:research@example.com)`
  (`core/scholar.py:161`, `core/oa.py:537`). The README says "No placeholder is
  ever sent on your behalf" (`README.md:409`). That sentence is true only of the
  discovery package.

### DOI extraction (`core/scholar.py:40-94`)

The priority is a URL DOI, then an arXiv URL, then a `citation_doi` or
`dc.identifier` meta tag, then a body `DOI:` marker in the first 20,000 chars.

- A URL DOI is read **only when the host is doi.org** (`core/scholar.py:79-82`).
  Publisher paths like `dl.acm.org/doi/10.1145/...` and
  `onlinelibrary.wiley.com/doi/10.1002/...` yield nothing from the URL.
- The meta regex requires `name=` before `content=` (`core/scholar.py:42-46`).
- The body regex needs a `DOI` token directly before the number, so
  `https://doi.org/10.x` links in a body are missed (`core/scholar.py:49`).
- Consequence for rescue: after a hard failure there is no HTML, so a 403 on a
  publisher URL finds no DOI and cannot be rescued. Only doi.org links can be.
- Consequence for substitution: a thin press release or news story that carries
  "DOI: 10.x" for the study it covers can be replaced by the paper. Its own
  quotes are lost, and the banner calls it "an abstract or paywall page". The
  content type then becomes `paper` and the tier `institutional`
  (`cli/fetch.py:414-441`). With default config, only Europe PMC can supply the
  paper, so this mainly hits biomedical press releases.

---

## 6. Scholarly discovery (`scholar/*`, `hpr scholar search`)

The registry, in merge-precedence order, is openalex, crossref, core, repec, doab,
clinicaltrials, edgar, fred (`scholar/registry.py:22-31`). The `--scope papers`
set is `scholar/registry.py:35`.

| Provider | Key | Coverage / behaviour | Where |
|---|---|---|---|
| OpenAlex | none; env email adds the polite pool | `search=`, up to 200 per page, abstract rebuilt from the inverted index, OA PDF from `best_oa_location`. Full work objects, no `select=`. | `scholar/providers/openalex.py:160-235` |
| Crossref | none; env email adds the polite pool | `query=`, up to 100 rows, JATS abstract stripped, abstracts often missing, `link` PDFs mostly similarity-checking only | `scholar/providers/crossref.py:164-305` |
| CORE | `CORE_API_KEY` required | v3 search excluding `fullText`. Citation counts are often a wrong 0. | `scholar/providers/core_oa.py:76-123,289-300` |
| DOAB | none | OA books via legacy DSpace REST, Solr-sanitised query. **About 0.6 s per record**, so it pages 20 at a time, at most 100. | `scholar/providers/doab.py:38-41,89-92,114-124` |
| ClinicalTrials.gov | none | v2 `query.term`, NCT id, phase, status, sponsor | `scholar/providers/clinicaltrials.py:104-184` |
| SEC EDGAR | `HYPERRESEARCH_CONTACT_EMAIL` required (403 without a mailto UA) | EFTS full-text search, deduplicated by accession, no abstract | `scholar/providers/edgar.py:16-29,126-170` |
| FRED | `FRED_API_KEY` | Series search, uncached so the key never reaches `api_cache`. "Not exercised against the live API." | `scholar/providers/fred.py:13-27,97-103` |
| RePEc | n/a | Always unavailable: the RePEc API has no search | `scholar/providers/repec.py:84-119` |

Behaviour of `hpr scholar search` (`cli/scholar_cmd.py:42-167`):

- Providers are queried **sequentially**, by design (`cli/scholar_cmd.py:56-58`).
  The stated reason is a global per-host limiter. But the limiter is per-host,
  so calls to different hosts could run concurrently at no politeness cost. As
  it stands, latency is the sum of all providers, and DOAB alone adds about
  12–15 s for 25 records (estimate from the docstring timings).
- `--limit` applies per provider, and the merged list is not capped
  (`cli/scholar_cmd.py:112-117`).
- Dedup goes by DOI first, then title fingerprint with year ±1. Field values
  are merged (`scholar/dedup.py:143-185`). The merged list is ordered by
  provider precedence, then first-seen order (`scholar/dedup.py:184`), not by
  cross-provider relevance. The agent docs still call it "one ranked list"
  (`core/agent_docs.py:83`).
- Output is `json.dumps(indent=2)` (`cli/_output.py:34`) and includes full
  abstracts and full author lists. With about 4 keyless providers × 25 records,
  this is likely well over 100 KB (**estimate**). Claude Code truncates Bash
  output at about 30,000 chars (**platform**), so the orchestrator probably sees
  only the first OpenAlex records. That defeats the stated reason for the
  per-provider limit.
- Rate limiting: `_throttle` is a module-level dict, so it is **per process**
  (`scholar/base.py:54,213-219`). Each CLI call is a new process, so there is
  no politeness across calls or across parallel subagents.
- Retries: the discovery HTTP layer (`scholar/base.py:189-210`) has **no retry
  and no 429 handling**. Any non-200 becomes `None`, then `[]`, and looks
  exactly like "no results": `per_source` shows 0 and `failed` stays empty.
  The enrichment layer, by contrast, retries a 429 three times, honours
  Retry-After and raises `RateLimitedError` (`core/scholar.py:116-120,198-238`).
- Caching: successful bodies go into `api_cache` with a 30-day TTL
  (`scholar/base.py:222-257`, `core/config.py:125`).
- **Instruction conflict**: step 2 tells the orchestrator to "hit Semantic
  Scholar / arXiv / OpenAlex / PubMed BEFORE web search"
  (`skills/hyperresearch-2-width-sweep.md:45,95`). The fetcher prompt says
  "Semantic Scholar: search the API" (`core/hooks.py:3186`). But the scholar
  registry has no Semantic Scholar, arXiv or PubMed provider, and the agent
  docs say "Do NOT hand-assemble API URLs" (`core/agent_docs.py:83`). The
  model has to improvise.

### Enrichment and retractions (`core/scholar.py:284-497`, `cli/sources.py`)

- `lookup_metadata` asks OpenAlex for citations, venue and `is_retracted`, with a
  minimal `select=`. Semantic Scholar is used for arXiv ids and as the DOI fallback.
- `score_sources` runs serially over DOI-bearing notes, writes the frontmatter
  and the DB, and never lets an S2 "unknown" erase an OpenAlex retraction
  (`core/scholar.py:452-460`). It then computes the authority percentile of
  `log1p(citations)` within the vault (`core/scholar.py:384-403`).
- `sources retractions` is the ship-time sweep with `fresh=True`
  (`cli/sources.py:171-215`). `sources independence` clusters syndicated copies
  (`cli/sources.py:218-253`).

---

## 7. Divergent fetch paths

There are four code paths that save web content as notes, and they apply
different gates.

| Path | Used by | Login gate | Junk gate | OA rescue / substitution | Tier and type | Source key |
|---|---|---|---|---|---|---|
| `hpr fetch` (`cli/fetch.py`) | fetcher subagents | yes | yes | yes / yes | yes | requested URL |
| `hpr fetch-batch` (`cli/fetch_batch.py`) | mentioned in Codex agent docs (`core/agent_docs.py:226`) | yes | **no** | yes / yes | **no** (auto-enrich instead) | `result.url`: the final URL for builtin, the rewritten `/pdf/` URL for arXiv (`cli/fetch_batch.py:163`; `web/pdf.py:249,263`) |
| MCP `fetch_url` → `fetch_and_save` (`mcp/server.py:298-322`, `core/fetcher.py:86-281`) | MCP clients | yes | yes | **no** | **no** | requested URL, **upsert** (can take a row from another note, `core/fetcher.py:244-255`) |
| `hpr research` (`cli/research.py`) | nobody in the pipeline | yes (default gates) | **no** | **no** | **no** | `result.url` |

Further details:

- `fetch-batch` with `builtin` or the API providers has no `fetch_many`, so it
  runs **serially** (`cli/fetch_batch.py:122-139`). Its asset call omits
  `max_image_bytes` and `allow_private_hosts` (`cli/fetch_batch.py:312-316`).
- `hpr research` builds the provider without `settings` or `gates`
  (`cli/research.py:50-54`), so the vault's TLS, timeout and allowlist settings
  are ignored. It also saves the search-result `content` directly, which for
  Tavily is a snippet.
- Because sources are keyed by `result.url` in `fetch-batch` and `research`,
  re-requesting the same input URL misses the duplicate check.

---

## 8. Volume, speed and cost

Profile numbers come from `core/profiles.py:253-307` (`full`), `:309-326` (`light`)
and `:327-375` (`premier`).

| Profile | Sources target | Planned searches | Candidate URLs | Wave 1 fetchers × batch | Chase per fetcher | Stated time |
|---|---|---|---|---|---|---|
| light | 15–25 (min 10) | 8–20 | 20–40 | 3–5 × 8–12 | 3–8 | ~30–40 min |
| full | 55–80 (min 45) | 40–100 | 80–120 | 10–12 × 8–12 | 3–8 (cap 8) | ~1.5–2.5 h |
| premier | 100–130 (min 90) | 80–160 | 150–220 | 14–18 × 8–12 | 3–8 | ~3–5 h |
| dissertation | 300–450 | per chapter | per chapter | per chapter | — | ~4–8 h |

After wave 1 come wave 2 (3–5 fetchers), wave 3 (2–3), the corpus-critic
fetchers in step 8 (2–4) and the gap fetchers in step 13 (2–4).

**Per-URL work for a fetcher** (`core/hooks.py:3079-3150`): `sources check`,
`fetch`, `note show -j` (full body), `note update --summary`, `note update
--add-tag`, and a Write of `claims-<id>.json`. That is about 5–6 tool calls per
URL. Each call starts Python, discovers the vault and auto-syncs, which opens
every note file.

**Wall time per URL** (**estimate**, not measured): Python and crawl4ai import,
plus Chromium launch, plus navigation, plus 3–11 s of smart-wait, plus a
screenshot. Roughly 8–20 s inside the CLI, plus model latency for 5–6 turns, so
about 1 minute per URL per fetcher. A batch of 8–12 URLs plus 3–8 chased leads
then takes about 15–30 min per fetcher. That is consistent with the stated
1.5–2.5 h for a full run.

**Tokens** (**estimate**): the fetchers read every fetched body in full. Claude
Code's 30k-char Bash limit (**platform**) is the only cap, so long PDFs get read
only from the start. The full profile fetches roughly 100–150 URLs with chasing.
At typical 2–8k tokens per page, that is on the order of 0.5–1.5 M input
tokens of page text, before per-turn context re-sends. Pages over 5,000 words
are flagged for the source-analyst subagent (`core/hooks.py:3117`), capped at 6
per run in `full` (`core/profiles.py:270-271`).

**Searches** (**estimate**): 40–100 orchestrator WebSearch calls, plus Phase-2
lead searches by 10–12 fetchers, gives roughly 70–200 searches per full run.

**Machine load** (**estimate**): 10–12 concurrent Python processes, each with its
own headless Chromium, which plausibly needs several GB of RAM. They all write
one SQLite DB in WAL mode with Python's default 5 s busy timeout
(`core/db.py:233`).

**Empirical hint**: `example-reports/rl-exploration-trajectory-planning.md`
(87 KB) cites 97 unique URLs, 87 of them on `arxiv.org`. The acquisition stack's
strongest highway is arXiv, through the PDF lane.

---

## 9. Windows notes

- UTF-8 is forced at CLI import and crawl4ai import (`cli/__init__.py:21-31`,
  `web/crawl4ai_provider.py:35-44`), so console crashes are handled.
- The fetcher prompt says "On Windows, ALWAYS prefix commands with
  `PYTHONIOENCODING=utf-8`" and shows `PYTHONIOENCODING=utf-8 {hpr} fetch ...`
  (`core/hooks.py:3044-3104`). That is POSIX syntax. It works in Claude Code's
  Git Bash. The Codex agents are rendered from the same bodies
  (`core/codex.py:4-17`), and Codex on Windows runs PowerShell (**platform**),
  where this line is a command error. The prefix is redundant anyway, since the
  CLI sets UTF-8 itself.
- Per-URL Chromium launches and per-command full-vault file probes
  (`core/sync.py:89-102`) are slower on Windows, where process creation and
  antivirus file scans cost more (**plausible**).
- `cli/__init__.py:13-18` still warns that Python 3.14 is unsupported, while
  `pyproject.toml:11` allows `<3.15`. The local interpreter here is 3.14.6.

---

## 10. Mechanisms (condensed)

| Mechanism | Where | Drives quality? | Cost |
|---|---|---|---|
| Agent-side search plan and WebSearch execution | step-2 md `30-99` | yes: decides what exists in the corpus | 40–100 searches, orchestrator context |
| Fetcher subagents: per-URL fetch, read, summarise, claims, chase | `core/hooks.py:2955-3200` | yes: claims and quotes feed the evidence digest | about 5–6 tool calls per URL; full-body reads; 10–12 Sonnet agents in parallel |
| crawl4ai stealth headless fetch with fit_markdown | `web/crawl4ai_provider.py:228-458` | yes: reaches JS and bot-shy pages, cleaner text | a new Chromium per fetch; 3–11 s wait; a screenshot every time |
| PDF lane (URL shape, magic bytes, arXiv abs→pdf, pymupdf) | `web/pdf.py:35-299` | yes: full papers instead of abstracts | up to 25 MB download; no OCR or tables |
| Builtin httpx lane | `web/builtin.py:155-273` | partly: a fallback only | cheap; blocked by many sites |
| Paid and keyless search providers | `web/*_provider.py` | no for the pipeline (search unused) | keys or credits; 8k caps |
| SSRF gate, TLS policy, byte caps | `web/safe_http.py:228-353` | no (safety) | a double DNS lookup per hop; complexity |
| Junk and login-wall gates | `web/base.py:75-163` | partly: keep CAPTCHA and error pages out, but lose real pages | trivial CPU; lost sources |
| Escalation to a real-Chrome browser-fetcher | `core/escalation.py:60-90`, `core/hooks.py:3347` | partly | serial; human for CAPTCHA and login; none on Codex |
| OA substitution and rescue (Unpaywall, Europe PMC, CORE) | `core/oa.py:187-882` | partly or yes for academic topics; default is biomedical only | up to 3 lookups and 3 downloads per thin or blocked DOI page |
| Substitution disclosure (banner, `oa_*` fields, `note show` block) | `core/oa.py:664-727` | partly: prevents quoting preprints as the version of record | tiny |
| DOI and arXiv capture | `core/scholar.py:40-94` | partly: gates OA and enrichment | regex |
| Scholar discovery registry (8 providers) and dedup | `scholar/*`, `cli/scholar_cmd.py` | partly: canonical papers, books, trials, filings | sequential, about 10–25 s per query; large JSON |
| `api_cache` and per-host throttle | `scholar/base.py:213-257`, `core/scholar.py:241-276` | no | per-process only |
| Citation enrichment, retraction sweep, authority percentile | `core/scholar.py:284-497` | partly: a retraction ship gate and ranking input | one OpenAlex call per DOI, serial |
| Tier and content-type heuristics | `cli/fetch.py:88-204` | unclear: they feed `quality_score` (`w_tier` 0.35, `core/config.py:115`) | trivial |
| Untrusted-content wrapping on `note show` | `core/untrusted.py:29-49` | no: protects against prompt injection | tiny |
| Auto-enrich tags and summary (fetch-batch and research only) | `core/enrich.py:10-110` | no | trivial |

---

## 11. Weaknesses (most severe first)

1. **Login-wall gate false positives (high).** `title_match = any(s in title_lower
   for s in login_signals)` uses the signals "auth", "register", "sso", "sign in",
   "log in" and others (`web/base.py:78-87,102`). Probed: "Professor Smith on…",
   "Association for Computing Machinery", "Authority and Legitimacy", "The Federal
   Register: 2024 rule", "Design Interfaces…" and "Catalog Index…" are all flagged.
   The path rule `/auth` also hits `/authors/`. The result is an exit with
   `AUTH_REQUIRED` (`cli/fetch.py:365-382`), and the fetcher is told "Do NOT
   retry" (`core/hooks.py:3033`). Primary sources such as regulators named
   "Authority" and the Federal Register are silently lost, or sent to a serial
   human lane that Codex does not have.
2. **Fetch cost structure (high for cost and time).** It is one process per URL
   with a fresh Chromium (`web/crawl4ai_provider.py:396`), `screenshot=True` and
   `simulate_user=True` on every fetch (`web/crawl4ai_provider.py:271-278`), and
   a full-vault file probe per command (`core/sync.py:89-102`). On top of that,
   every body is read in full by a Sonnet subagent (`cli/note.py:162-227`,
   `core/hooks.py:3090`). This is why a full run takes about 1.5–2.5 h.
3. **Junk-gate false positives (medium).** Substring matches on "cloudflare",
   "ray id", "access denied", "captcha", "an error occurred" or "the page you
   requested" in the first 2,000 chars of real content mark it as a bot or
   error page (`web/base.py:119-138`). Probed: articles about Cloudflare, CAPTCHA
   research, FOIA "access denied" rulings and experiments where "an error
   occurred" were all rejected.
4. **OA rescue only works for doi.org URLs after hard failures (medium).** A URL
   DOI is read only for doi.org hosts (`core/scholar.py:79-82`), and rescue after
   an exception has no HTML (`cli/fetch.py:355`, `cli/fetch_batch.py:173`).
   Publisher URLs that return 403 are lost even when an OA copy exists.
5. **Default OA coverage is biomedical only (medium).** Unpaywall needs
   `[scholar] contact_email`, CORE needs `CORE_API_KEY` (`core/oa.py:238-245,417-419`),
   and `hpr install` prompts for neither. A user who sets
   `HYPERRESEARCH_CONTACT_EMAIL` still has no Unpaywall (`scholar/base.py:69-72`
   versus `core/config.py:183`).
6. **Substitution keyed on a DOI found in the body (medium).** A thin press
   release or news story that cites "DOI: 10.x" can be replaced by the paper
   (`cli/fetch.py:414-434`, `core/oa.py:187-201`). The secondary source's own
   content disappears, the banner calls it a paywall page, and the tier is
   upgraded.
7. **Discovery failures look like "no results" (medium).** There is no retry
   and no 429 handling in `scholar/base.py:189-210`. Any non-200 becomes `[]`,
   and `failed` stays empty (`cli/scholar_cmd.py:93-104`). Throttling on the
   OpenAlex anonymous pool is invisible.
8. **Instruction conflict on academic sources (medium).** Step 2 demands
   Semantic Scholar, arXiv and PubMed (`...-2-width-sweep.md:45,95`), and the
   fetcher prompt says "search the API" (`core/hooks.py:3186`). The registry has
   none of them, and the docs forbid hand-built API URLs (`core/agent_docs.py:83`).
9. **Scholar output size versus host truncation (medium, plausible).** The output
   is pretty-printed JSON with full abstracts and author lists
   (`cli/_output.py:34`). Truncation by the host at about 30k chars would hide
   every provider after OpenAlex.
10. **`fetch-batch` writes junk pages (medium; the pipeline does not use it).**
    It never calls `looks_like_junk` (`cli/fetch_batch.py:162-167`, confirmed by
    grep). It also keys sources by `result.url` (`cli/fetch_batch.py:163`).
11. **crawl4ai failure reasons are dropped (low–medium).** Only certificate
    errors are inspected (`web/crawl4ai_provider.py:401-403`). Timeouts, DNS
    failures and download aborts become "Empty or near-empty content", with no
    escalation and a misleading message.
12. **URL dedup is exact-string (low–medium).** `WHERE url = ?`
    (`core/fetcher.py:20`). utm parameters, `www`, http versus https and trailing
    slashes produce duplicate notes, which inflate the source-count gates.
    Canonicalisation exists, but only post hoc (`core/independence.py:36`).
13. **Lossy PDF extraction and a 25 MB cap (low–medium).** `get_text("text")`
    gives no tables and no OCR (`web/pdf.py:186-204`). The title heuristic is
    weak (`web/pdf.py:208-214`). Larger reports are lost after a wasted
    download (`core/config.py:29`).
14. **Exa and Serply as fetch backends truncate at 8,000 chars and skip the PDF
    lane (low–medium if configured)** (`web/exa_provider.py:41`,
    `web/serply_provider.py:45,88`).
15. **Sequential scholar providers despite per-host limits; per-process
    throttle (low).** `cli/scholar_cmd.py:56-58,93-104`; `scholar/base.py:54`.
16. **Eager OA resolution contradicts the "lazy" docstring (low).**
    `core/oa.py:226-230` versus `:766`.
17. **The README's placeholder claim is false (low).** `README.md:409` versus
    `core/scholar.py:161` and `core/oa.py:537`.
18. **The Windows Codex prompt prefix is POSIX-only (low–medium, platform).**
    `core/hooks.py:3044-3047`.
19. **The SSRF residue is documented (low).** DNS rebinding
    (`web/safe_http.py:16-21`), blind SSRF through browser redirects
    (`web/crawl4ai_provider.py:203-207`), and ungated subresources (inferred).
20. **Stale modules (low).** RePEc is a permanently unavailable stub that the
    agent docs still list as coverage (`scholar/providers/repec.py:84-92`,
    `core/agent_docs.py:92`). FRED was never run live
    (`scholar/providers/fred.py:26-27`). `hpr research` is a legacy loop with
    weaker gates.

---

## 12. Ideas for VAFER

- Adopt a keyless DOI → open-access recipe for the papers a report actually
  cites: OpenAlex `works/doi:<doi>?select=best_oa_location,is_retracted`, Europe
  PMC `fullTextXML`, and Unpaywall when the user gives an email.
- Prefer structured full text over PDF text: arXiv HTML (`arxiv.org/html/<id>`)
  and Europe PMC JATS. hyperresearch rewrites abs→pdf and loses structure.
- State the version (preprint, accepted, published) next to every paper
  citation, as hyperresearch's banner does, and do not quote a preprint as the
  version of record.
- Run a retraction check on cited DOIs before shipping. It costs one OpenAlex
  call per DOI.
- Avoid substring login and junk gates. Let the reading model judge the page,
  and record "blocked: <reason>" with the URL in the notes.
- Never swap a page's content for a paper found through a DOI in its body. Cite
  the paper as its own source.
- Read DOIs from any URL path (`/doi/10.…`) and from `citation_doi` meta in
  either attribute order. Resolve title to DOI through Crossref or OpenAlex
  when a publisher blocks.
- Canonicalise URLs before dedup and before counting: scheme, `www`, trailing
  slash, `utm_*` and `fbclid`, fragments.
- Count independent records, not URLs, so syndicated copies count once.
- Keep scholarly API responses small: `select=` fields, `per-page` of 10 or
  less, no full abstracts unless asked.
- Query different API hosts in parallel. Per-host politeness does not need
  cross-host serialisation.
- Treat a 429 or 5xx as "unknown" and say so in the method note. Never report
  it as "no results".
- Do not pour whole pages into subagent context. Use targeted WebFetch extracts,
  and save full reads for the sources behind headline facts.
- Do not spawn a browser per URL. Keep host WebFetch as the default and use
  curl only for raw text or exact quotes.
- Copy the period-pinned filing rule (fetch the filing for the named period and
  copy table line items verbatim) into VAFER's primary-record rule.
- Give researchers the EDGAR full-text search template, and note that it
  returns 403 without a User-Agent that carries a contact email.
- List blocked URLs with their reason under "Not established" instead of in a
  hidden queue.
- Keep prompt commands shell-neutral. A `VAR=x cmd` prefix breaks under Windows
  PowerShell in Codex.
- Large PDFs: look for the HTML or per-chapter version of big reports.
  hyperresearch drops anything over 25 MB.
- Beat it on time: hyperresearch spends about 1.5–2.5 h for 55–80 sources.
  VAFER Standard can reach the primary records with far fewer opens.
- Avoid provider sprawl: six web providers ship, and the pipeline uses only the
  fetch side of one.

---

## 13. Key claims for an independent check

1. Web search in the pipeline is agent-side (host WebSearch). Python providers'
   `search()` is reachable only through `hpr research`. Evidence: the only call
   site is `cli/research.py:62`; builtin and crawl4ai raise `NotImplementedError`
   (`web/builtin.py:200-204`, `web/crawl4ai_provider.py:589-593`); the fetcher
   tools are `Bash, Read, Write, WebSearch` (`core/hooks.py:2965`).
2. Fetching is one `hpr fetch` process per URL from 10–12 parallel Sonnet
   fetchers, and each one launches a fresh headless Chromium. Evidence:
   `core/hooks.py:3084-3090`; `web/crawl4ai_provider.py:395-397`;
   `core/profiles.py:52,258-265`; `cli/install.py:336-337`.
3. The login-wall gate rejects ordinary titles by substring ("auth", "register",
   "sso", "log in", "sign in"), and the fetcher is told not to retry. Evidence:
   `web/base.py:78-102`, `cli/fetch.py:365-382`, `core/hooks.py:3030-3033`; the
   probe in §14.
4. With default config, OA recovery is Europe PMC only. Rescue after a hard
   failure works only for doi.org URLs. Evidence: `core/oa.py:238-245,417-419`;
   `core/config.py:183`; `README.md:448`; `core/scholar.py:79-82`;
   `cli/fetch.py:355`.
5. `fetch-batch` and `hpr research` never run the junk gate. Evidence:
   `looks_like_junk` is called only at `cli/fetch.py:388`,
   `core/fetcher.py:151` and `core/oa.py:810`.
6. `note show -j` returns the full body uncapped, and the fetcher reads every
   page this way. Evidence: `cli/note.py:162-227`, `core/hooks.py:3090`.

---

## 14. Probe

`C:\Users\VECTOR\AppData\Local\Temp\claude\C--Users-VECTOR-Documents-GitHub-VAFER\e8210f42-5bc4-4715-a0fe-4bc7e2e72a35\scratchpad\hr-probe\probe_gates.py`
re-implements the gate signal lists and DOI regexes, copied verbatim from
`web/base.py` and `core/scholar.py`. It imports nothing from the clone.

Output:

- login wall flagged True: "Author guidelines…", "The Federal Register: 2024 rule",
  "Professor Smith on monetary policy", "Association for Computing Machinery",
  "Lessons from the 2008 crisis", "Design Interfaces for Agents",
  "Catalog Index of Stars", "Authority and Legitimacy". False only for
  "Mississippi flood report".
- junk flagged: a Cloudflare article ("Bot detection"), "an error occurred in 3
  of 40 trials" ("Error page"), a FOIA "Access denied" ruling ("Bot detection"),
  a CAPTCHA paper ("Bot detection").
- URL DOI: found for `doi.org/...`; **None** for dl.acm.org `/doi/10.1145/...`,
  wiley `/doi/10.1002/...`, springer `/article/10.1007/...` and sciencedirect
  `/pii/...`; arXiv gives `arXiv:2305.10601`.
- meta DOI: matched when `name` comes first, **not** when `content` comes first.
  Body regex: matches `DOI: 10.x`, misses a `https://doi.org/10.x` link.

## 15. Not verified

- crawl4ai `arun_many` default concurrency, and whether PruningContentFilter
  drops tables.
- Real per-URL latency, token totals and RAM use. All figures above are
  estimates.
- Exact Bash output truncation limits in the current Claude Code and Codex
  versions.
- Whether OpenAlex still serves anonymous traffic without an API key as of
  2026-10.
