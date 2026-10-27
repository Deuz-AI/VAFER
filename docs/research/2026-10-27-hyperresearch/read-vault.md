# hyperresearch read: vault, notes, search index, embeddings, links, MCP server, web viewer

Read on 2026-10-27 from the clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`
(version 0.12.0, HEAD `327498b`). Paths such as `core/sync.py` are relative to
`src/hyperresearch/`. Step files live in `src/hyperresearch/skills/`, so
`hyperresearch-13-gap-fetch.md` means that folder. `file:line` refers to that commit.

**What I read.** All 22 assigned files, in full. Where they pointed elsewhere I also
opened `core/config.py`, `core/patterns.py`, `core/untrusted.py`, `core/enrich.py`,
`core/fetcher.py`, `core/graphrank.py`, `core/quality.py`, `core/agent_docs.py`,
`core/claims.py` (ingest), `cli/repair.py`, `cli/sources.py`, `cli/fetch.py`
(duplicate path), `cli/fetch_batch.py`, `cli/vault_tag.py`, `cli/__init__.py`,
`cli/mcp_cmd.py` and the fetcher prompt in `core/hooks.py:3042-3216`. I also grepped every step file and agent prompt for
each vault command, to see which features the pipeline actually calls.

**What I ran.** Unlike the other reads in this folder, I ran isolated experiments.
I imported the clone's modules with the clone's own `.venv` Python (`python -I -B`).
A script in my scratchpad added the clone's `src` to `sys.path`, and every vault it
built was a throwaway in the session scratchpad. Bytecode writing was off. I
confirmed the clone did not change: `git status` stayed clean, and no `.pyc` file
is newer than my scripts. The `__pycache__` folders in `src/` date from 16:24,
before my first run, and are gitignored. I did not run the installer or the research
pipeline, and nothing touched the network. Timings come from this machine (Windows 11,
Python 3.14.6; hyperresearch officially supports 3.11 to 3.13), so read them as orders
of magnitude.

---

## 1. Bottom line

- **Within one run, the vault is the shared evidence store, and that part matters.**
  Every step builds its corpus with `note list --tag <vault_tag>` or
  `search ... --tag <vault_tag>`, and drafters, critics and the cite-checker re-read
  full source text from it. This is the only way this subsystem drives report quality.
- **Across runs it gives almost nothing, and on overlapping questions it gives less
  than nothing.** Each run mints a fresh unique tag, even when the same query is
  re-run. Fetchers skip URLs that are already in `sources` and never add the new tag,
  so the new run's tag-scoped queries cannot see those sources. Final reports carry no
  frontmatter, so they are never indexed. Section 4 has the evidence.
- **The knowledge-base features are not used by the 16-step pipeline.** That covers
  the evergreen lifecycle, index pages, auto-linker, embeddings, MinHash dedup, topic
  tree, batch edits, MCP server and web viewer. The lifecycle is one CLAUDE.md
  instruction plus mechanical `repair` rules: 100 words, a summary and any link make a
  note "evergreen", and evergreen gets a 1.5x boost in search.
- **Search is FTS5/bm25 with an implicit AND of prefix terms.** One absent word in a
  query returns zero hits (measured). JSON search output includes the full bodies of
  up to 20 notes by default, and no pipeline call limits it. 20 notes of about 10 KB
  each produced 236,614 bytes (measured).
- **Every CLI call carries local overhead**, about 0.6 s for a read and 0.9 s for a
  write at 2,000 notes. The write path holds a SQLite write lock while it resolves
  broken links with unindexed `LOWER()` joins. With no broken links a one-note sync
  took 0.7 s; with 6,000 it took 13.8 s, and 5 of 6 parallel `note update` calls then
  died with `database is locked` (default 5 s busy timeout). With no broken links,
  12 of 12 parallel writers succeeded.
- **The MCP server returns raw fetched bodies.** Its docstring says 8 read-only
  tools, but it registers 13 read-write tools. It adds neither the `<untrusted-source>`
  fence nor the open-access disclosure that the CLI adds (measured).

---

## 2. Layout and data model

**Disk layout** (`core/vault.py:12-14`, `81-126`, `139-196`):

- `.hyperresearch/` is hidden and holds `config.toml`, `hyperresearch.db` (SQLite, WAL),
  `templates/` and `exports/`.
- `research/` is the one visible directory:
  - `notes/` is flat. `parent:` is frontmatter only and does not create folders
    (`core/note.py:146-150`).
  - `index/` holds generated pages.
  - `temp/` holds stub notes. They are synced so links resolve (`core/vault.py:94-102`).
  - `runs/<vault_tag>/` holds run artifacts and is never synced (`core/sync.py:94-97`).
  - `raw/` holds PDFs and `assets/<id>/` holds images. Both paths are hard-coded as
    `research/...` (`core/fetcher.py:210`, `263`; `cli/note.py:682-696`).

**Identity.** A note's id is `slugify()` of its frontmatter id, or of its title when
there is none. The slug is Unicode-aware and capped at 80 characters and 200 bytes
(`models/note.py:56-81`). Collisions get `-2`, `-3`, ...; the suffix respects the caps
and also skips ids already in the DB (`core/note.py:67-87`, `154-161`). The id lives in
frontmatter, so `note mv` keeps it (`cli/note.py:547-630`).

**Frontmatter schema.** `NoteMeta` (`models/note.py:84-139`) has about 30 fields:
- title, id and tags (lowercased only, never slugified, `127-130`);
- created/updated and source, plus `source_domain`, `fetched_at` and `fetch_provider`;
- status (6 values), type (6), tier (5) and content_type (12);
- aliases, parent, deprecated, reviewed, expires, summary and raw_file;
- doi, utility_score, citation_count, venue, is_retracted and five `oa_*` fields.

It uses `model_config = {"extra": "ignore"}` (`:139`), which matters in section 11.

**SQLite** (`core/db.py:10-227`):
- `notes` mirrors the frontmatter and also caches the derived scores
  (authority, centrality, independence, quality).
- `note_content(body, body_plain)`, `tags`, `aliases`, and
  `links(source_id, target_ref, target_id, line_number, context)`.
- `embeddings`, `claims` with `claims_fts`, `api_cache`, `escalations`, `tag_aliases`,
  `sources(url PK, note_id FK ON DELETE SET NULL)` and `assets`.
- `notes_fts`, an FTS5 table (`porter unicode61`) over title, body_plain, tags and aliases.

**"Markdown is truth" holds only partly.** `repair` rebuilds the notes tables from
files (`cli/repair.py:35-44`). Several things live only in the DB, though: `sources` (the
URL dedup record), `claims`, `escalations`, `api_cache` and the derived scores, which
sync deliberately leaves alone (`core/sync.py:229-234`). Delete the DB and URL dedup and
claims are gone. `fetched_at` is written to frontmatter but has no column in `notes`,
so search and list output cannot show when a source was fetched; `created` is the
nearest substitute.

---

## 3. Sync engine: what runs on every command

`Vault.db` opens the connection, then runs `init_schema` on every open
(`core/vault.py:65-73`). That means `executescript` of the full DDL, an
`INSERT OR IGNORE` into `_meta`, the migration check and the post-migration indexes
(`core/db.py:240-256`, `core/migrations.py:374-396`). Every command then calls
`vault.auto_sync()` (default on, `core/config.py:234`). The MCP server does the same
on every tool call (`mcp/server.py:52-53` and the rest).

`compute_sync_plan` (`core/sync.py:70-131`) works in five steps:
1. `rglob("*.md")` over all of `research/`, including `runs/`, `raw/` and `assets/`,
   filtering as it goes.
2. Skip files at the research root (staging files) and anything under `runs/`.
3. Open each remaining file to read 16 bytes and probe for frontmatter
   (`_has_frontmatter`, `:48-67`). Files without frontmatter are never indexed.
4. Load `path, file_mtime, content_hash` for every note.
5. Hash a file only when its mtime differs.

`execute_sync` (`core/sync.py:134-217`) runs one `BEGIN IMMEDIATE` transaction (`:141`):
- It refuses id collisions (`:157-173`).
- It upserts each changed note: note row, tags (resolved through tag aliases), aliases,
  content, FTS (delete then insert) and links (`:220-328`).
- It then runs `_resolve_links_incremental`. That resets `target_id` for links to and
  from changed notes, then re-resolves **every** NULL link in the vault with four
  `UPDATE`s (`:338-398`). Two of them compare `LOWER(n.id)` or `LOWER(n.title)` against
  `LOWER(links.target_ref)`, which no index supports. Their cost is roughly
  (NULL links) x (notes), and the write lock is held the whole time.

`auto_sync` throws away the `SyncResult` (`core/vault.py:213-221`). Per-file errors such
as an invalid enum or an id collision go only into `result.errors`
(`core/sync.py:184-201`), so the note silently stays out of the index. Only an explicit
`hpr sync` prints them (`cli/main.py:155-168`), and no pipeline step calls `hpr sync`.

**Measured** (2,000 synthetic notes of 1,500 words; section 14 has the method):

| Operation | 0 broken links | 6,000 broken links |
|---|---|---|
| Initial full sync of 2,000 notes | 34.6 s | 60.2 s |
| Plan only, nothing changed (tree scan) | 0.77 s | 0.63 s |
| One changed note: plan + sync (what `note update` triggers) | 0.70 s | 13.8 s |
| `hpr note list --limit 1 -j`, end to end | 0.60-0.66 s | 0.60-0.65 s |
| `hpr note update <id> --add-tag x -j`, end to end | 0.91 s | 10.6-11.0 s |
| 6 parallel `note update` | 6/6 ok, 2 s | **5/6 failed, `database is locked`**, 12 s |
| 12 parallel `note update` (2 rounds) | 12/12 ok, 3 s | not run |
| Import of `hyperresearch.cli` alone | 0.33 s | |
| SQLite size vs markdown | 72 MB vs 21 MB | 73 MB vs 21 MB |

The failure is at `core/sync.py:141` (`BEGIN IMMEDIATE`), reached from
`cli/note.py:538-539`, after the file was already written at `cli/note.py:536`. The
markdown therefore holds the change, the index lags behind, and the agent sees exit 1
with a traceback. `get_connection` passes no `timeout` (`core/db.py:233`), so Python's
default 5 s busy timeout applies. Wave 1 of the `full` profile runs 10 to 12 fetchers in
parallel (`core/profiles.py:265`), each issuing these commands. How many broken links a
real vault accumulates is **unknown**; I did not measure it on a real vault. The
mechanism is clear, though: the per-call lock hold grows with broken links times notes,
and nothing ever prunes a vault.

---

## 4. Does the vault make later sessions better?

**No. For a re-run or an overlapping question it makes the corpus worse.** Five
independent facts combine.

1. **Every run gets a fresh, unique tag.** `vault-tag` appends a random 6-hex suffix
   that is verified unique "across re-runs of the same query" (`cli/vault_tag.py:1-16`).
   The orchestrator calls it in bootstrap step 2 (`hyperresearch.md:120`).
2. **Every corpus query is scoped to that tag:**
   - `note list --tag <vault_tag> --all -j` in `hyperresearch.md:227`,
     `hyperresearch-2-width-sweep.md:172,183`, `hyperresearch-4-loci-analysis.md:28`,
     `hyperresearch-7-source-tensions.md:29` and `hyperresearch-10-triple-draft.md:33,62,104`;
   - `--type interim` in `hyperresearch.md:230`, `hyperresearch-5-depth-investigation.md:84`
     and `hyperresearch-6-cross-locus-reconcile.md:28`;
   - `search ... --tag <vault_tag>` in `hyperresearch-8-corpus-critic.md:39`,
     `hyperresearch-10-triple-draft.md:110`, `hyperresearch-13-gap-fetch.md:37` and
     `core/hooks.py:695`.

   No step queries the vault without a tag.
3. **Already-fetched URLs are skipped and never re-tagged.**
   - The fetcher prompt reads: "Check if it's already fetched: `sources check` ...
     If not already fetched, fetch it" (`core/hooks.py:3083-3087`). It says nothing for
     the already-fetched case.
   - `hpr fetch` on a known URL returns `DUPLICATE_URL`. With `--suggested-by` it
     prepends a breadcrumb instead. Neither path adds the caller's tag
     (`cli/fetch.py:254-296`).
   - `fetch-batch` skips known URLs, and its JSON output reports only a skipped
     *count*, not which note ids those URLs map to (`cli/fetch_batch.py:85-101`, `352-359`).
4. **Claims cannot follow the source.** Claims are stored under
   `UNIQUE(note_id, claim_hash)` with `INSERT OR IGNORE` (`core/claims.py:125`). A
   re-extracted identical claim for an old note keeps the old run's `vault_tag`, so the
   new run's tag-scoped claim queries miss it too. Paraphrased claims would get the new tag.
5. **Reports are invisible.** The synthesizer is told "No YAML frontmatter"
   (`hyperresearch-11-synthesize.md:231,253`), and sync skips files without frontmatter
   (`core/sync.py:98-100`). So `research/notes/final_report_<tag>.md` never reaches
   search, MCP, the viewer or the link graph. `lint` and `citecheck` read it straight
   from disk (`cli/lint.py:84-88`, `cli/citecheck_cmd.py:51`).

**The consequence.** Re-run the same or a related question in the same folder, and the
web searches will likely find many of the same URLs (expected, not measured). Fetchers
skip them, and the new run's
`--tag` lists do not contain them. The new corpus is missing exactly the sources the
first run judged most relevant. That leaves a choice between a thinner report and extra
fetch waves to meet the source-count gates; the second effect is **inference**, and I
did not trace the gate code. A fetcher might notice the note id in the `sources check`
output and read the old note, but nothing tells it to tag that note, and later steps
will not see it.

**What does carry over** is small:
- URL dedup saves the network fetch.
- PageRank centrality and the composite quality score are computed vault-wide
  (`core/graphrank.py:74-105`). Old notes and old links therefore shift the max-normalized
  centrality of new notes.
- The auto-linker, run by `fetch-batch` and `hpr link`, adds `## Related` links from new
  notes to old notes whose title or id appears in the text (`core/linker.py:24-63`).

None of these brings old evidence into a new run's corpus.

**The curation lifecycle does not create reusable quality either:**
- **Promotion is mechanical.** `repair` promotes `draft → review` at 50 or more words
  with a summary and a tag, and `review → evergreen` at 100 or more words with any link
  in or out (`cli/repair.py:163-199`). No step calls `repair`. It appears only in the
  CLAUDE.md "Curate after every session" block (`core/agent_docs.py:179-196`), which
  nothing enforces.
- **Evergreen only changes ranking.** It earns a 1.5x score multiplier in search
  (`core/config.py:225`, `search/fts.py:172-178`) and means nothing about accuracy.
- **Freshness tracking exists in schema only.** `expires` and `reviewed` are in the
  schema, but no command sets them: `note update` has no flags for them and fetch never
  writes them. They feed two lint warnings and nothing else (`cli/lint.py:1740-1764`).
  Nothing ever moves a note to `stale`. A reused fact therefore carries no as-of or
  expiry signal beyond `created`.
- **The pipeline's "curation" is per-run selection,** for example step 10's per-angle
  reading lists (`hyperresearch-10-triple-draft.md:98`), and it is discarded with the run.

---

## 5. Search: FTS, filters, ranking, embeddings

**Query preprocessing** (`search/fts.py:31-63`):
- If the raw query contains ` AND `, ` OR `, ` NOT ` or ` NEAR(`, it passes through
  verbatim and must be valid FTS5 (`:39-40`).
- Otherwise every word becomes a quoted prefix term (`"word"*`), joined by spaces,
  which FTS5 treats as an implicit AND (`:62`).
- Glued letter-digit runs are split (`gpt4o` becomes `gpt 4 o`, `:19-28`).

**Measured.** "solid state battery energy density" found 1 hit, "solid state battery
energy density 2024" found 0, and "lithium solid state" found 0 (section 14). The
pipeline's queries are agent-written keyword strings such as
`"<finding topic keywords>"` (`hyperresearch-13-gap-fetch.md:37`). The gap-fetch step
asks "does the vault have evidence on X?", so one extra keyword turns "yes" into
"no evidence" and leads to unneeded fetches or false gap claims.

**Ranking:**
- bm25 weights the columns title 10, body 1, tags 5, aliases 3 (`search/fts.py:100-110`,
  `core/config.py:221-224`).
- Status multipliers then apply: evergreen 1.5, deprecated 0.3, stale 0.7
  (`:167-179`, `core/config.py:225-227`).
- `--ranked` multiplies by `0.5 + quality` (`:186-190`).
- Both re-rankings run after SQL `ORDER BY score LIMIT ? OFFSET ?` (`:111-126`). They
  only reorder the current page and cannot surface a better note from below the bm25
  cutoff; with offset paging the order is not even consistent.
- Deprecated notes are still returned, only down-weighted. `note list` has no default
  status filter (`cli/note.py:335-373`). The step files tell the agent to "pick ...
  non-deprecated notes" (`hyperresearch-10-triple-draft.md:62`,
  `hyperresearch-2-width-sweep.md:183`); that is an instruction, not code.

**Output size is the real cost:**
- `want_body = include_body or (json_output and not no_body)` (`cli/search.py:177`): in
  JSON mode every result carries its full body.
- The default limit is 20 (`core/config.py:229`).
- `--max-tokens` exists (`cli/search.py:189-206`), but no pipeline call passes
  `--max-tokens`, `--no-body` or `--limit` (grepped skills and `core/hooks.py`).
- Measured: 236,614 bytes with bodies vs 22,983 with `--no-body`, for 20 hits at about
  10 KB each. Real fetched papers run 20 to 80 K characters
  (`core/config.py:184-185` comment), so 20 hits can reach megabytes.
- The Bash and PowerShell tool descriptions in this environment say output beyond
  30,000 characters is truncated. How Claude Code handles that varies by version
  (**unclear**), but either way the agent sees a fraction of the results or pays for
  all of them.
- `note list --tag <vault_tag> --all -j` returns summaries, not bodies, and the fetcher
  is told to write 3 to 6 paragraph summaries for dense sources (`core/hooks.py:3106-3111`).
  At 2,000 notes with one-line summaries the output was 793,824 bytes, about 400 bytes
  of overhead per note. At 55 to 130 notes per run with long summaries, a single list
  call is plausibly 50 to 150 KB (**estimate**).

**Untrusted fencing:**
- `note show` and `search` with bodies wrap any note whose `source` is http(s) and whose
  type is not `interim`, `source-analysis`, `moc` or `index` (`core/untrusted.py:21-62`,
  `cli/note.py:219-226`, `cli/search.py:211-217`).
- The wrapper neutralizes forged fence tags and escapes the URL attribute
  (`core/untrusted.py:42-62`).
- The fence costs about 90 tokens per wrapped body.
- **MCP does not apply it at all** (section 8).

**Embeddings** (`core/embed.py`):
- The provider is `none` by default (`core/config.py:148`); voyage and openai are
  optional.
- Each note is embedded from title, summary and the first 1,500 characters of the body
  (`core/embed.py:97-104`, `core/config.py:151`). For web pages those 1,500 characters
  are often navigation text.
- The freshness stamp is `model@content_hash`, and the hash covers the raw file
  (`core/note.py:36-37`). Any frontmatter edit, such as a tag, status or summary,
  re-embeds the note (`core/embed.py:133-137`).
- Query time is brute-force cosine in pure Python over every vector (`:175-188`).
- Hybrid search fuses the FTS and semantic lists with RRF (k=60, `:191-200`,
  `cli/search.py:132-174`). Semantic-only hits come back with empty tags and snippet.
- **The pipeline never calls `embed sync` or `--semantic`** (grepped). This feature does
  not drive quality.

---

## 6. Links, graph, stubs, index pages, dedup, topics, batch

**Wiki-links.** Links are `[[target]]` or `[[target|label]]`. A trailing `(` is
rejected, and `[` is excluded from the pattern so it cannot backtrack
(`core/patterns.py:24`). Code blocks and spans are stripped by a linear scanner first
(`:63-143`). Many false targets are filtered out: footnotes, roman numerals, figure
refs, template placeholders, shell fragments and path traversal (`:146-260`). This part
is careful and hardened.

**Resolution order.** Exact id, then case-insensitive id, then alias, then title, each
with `LIMIT 1` (`core/sync.py:367-398`). Ambiguous titles, such as many fetched pages
called "Home", resolve to an arbitrary note.

**Provenance.** `hpr fetch --suggested-by <id>` prepends
`*Suggested by [[src]] — reason*` to the body, so the edge lives in the links table
(`cli/fetch.py:36-85`, `core/hooks.py:3063-3077`). This is the input PageRank calls
"many independent research chains converged" (`core/graphrank.py:1-12`).

**PageRank and quality** (`core/graphrank.py:21-105`, `core/quality.py:25-75`):
- PageRank uses damping 0.85 and at most 50 iterations, normalized by the maximum.
- The node set is every note except stubs, so `index` pages count. Once `repair` or
  `index rebuild` has run, `_index`, `_tag-*`, `_recent` (the 50 newest), `_month-*` and
  `_most-linked` (the top 30) all link to notes. That adds a recency bias, and
  `_most-linked` feeds itself: it counts inbound links that include its own previous
  edition (`indexgen/generator.py:243-265`).
- Quality is a renormalized weighted sum of tier 0.35, utility/18 0.20, authority 0.25
  and centrality 0.20, with a 0.05 floor for retracted papers.
- The pipeline calls `graph rank` in step 2 (`hyperresearch-2-width-sweep.md:232`) and
  `search --ranked` in step 10 (`hyperresearch-10-triple-draft.md:110`).
- Quality influence is therefore **partly** real: it reorders a page of hits whose
  membership bm25 already fixed.

**Auto-linker** (`core/linker.py:12-138`):
- The vocabulary is every title of 15 or more characters plus **every note id,
  whatever its length** (`:26-32`).
- Each vocabulary entry is regex-searched in every target note, which costs
  O(notes x vocab) (`:84-98`).
- It then **rewrites the source file**, appending `## Related` with links (`:107-129`).
  That changes fetched text, changes the content hash, forces a re-sync, and would
  re-embed the note.
- `fetch-batch` runs it automatically after every batch (`cli/fetch_batch.py:339-348`).
- Measured: a note mentioning "ball python" and "wikipedia" got `[[python]]` and
  `[[wikipedia]]` added. These fake edges reach PageRank.
- The frontmatter split is `content.split("---", 2)` (`:74-75`), which breaks if a YAML
  value contains `---`.

**Stubs.** `graph stub` and `repair --stub` create placeholder notes for broken links
in `research/temp/`, marked by the summary prefix `Stub for [[` (`cli/graph.py:188-251`,
`cli/repair.py:51-86`, `core/note.py:18-31`). Rankers exclude them. However,
**`archive-run` moves the whole `research/temp/` tree** into `research/runs/archive-*/`
(`cli/archive.py:51`, `135-138`). The orchestrator runs `archive-run` at bootstrap step
0.5 of every run (`hyperresearch.md:112`) and calls that a cheap no-op on 3.0+ vaults.
Anything under `runs/` is unsynced, so every new run un-stubs the vault and the links
break again. Measured: the link was resolved before `archive-run` and broken after it.
This also adds to the broken-link count that slows sync (section 3).

**Index pages** (`indexgen/generator.py`):
- `build_all` **deletes every page first** (`:17-19`), then writes about 10 base pages
  plus one per tag with 3 or more notes and one per month with 3 or more notes.
- The per-tag filename is `_tag-{tag}.md` (`:107`), and tags are only lowercased
  (`models/note.py:127-130`).
- Measured: three notes tagged `ml/deep-learning` made `build_all` raise
  `FileNotFoundError` after deleting the old pages. Of 10 pages, 3 remained.
- On Windows, tags containing `: ? * < > | "` fail the same way.
- `repair` calls `build_all` with no guard (`cli/repair.py:215-217`), so the documented
  curation command crashes at step 5 of 6.
- `config.index_pages` and `auto_build_index` are never read by `build_all`; they are
  dead config.
- The pipeline never reads index pages, and search excludes them by default
  (`search/fts.py:98`).

**Dedup** (`cli/dedup.py`). Shingle Jaccard is brute force below 200 notes and
MinHash with LSH above (`:66-71`). It only reports pairs, and the pipeline never calls
it. The fetcher's "Is this a duplicate? deprecate the worse copy"
(`core/hooks.py:3096`) is pure LLM judgment with no tool support.

**Topics** (`cli/topic.py`). A tree built from `parent:` strings. The pipeline never
sets `parent` and never calls `topic` (grepped).

**Batch** (`cli/batch.py`):
- Each command loops over `_update_file_frontmatter` with no error handling
  (`:124-125`, `162-163`, `209-210`, `250-251`, `289-290`). One unparsable note aborts the
  batch halfway, after some files have already changed.
- `_batch_update_files` (`:58-73`), the helper that collects errors, is never called.
- `setattr` on the pydantic model skips validation (`:90-91`). Only `set-status`
  pre-validates (`:188-194`).

---

## 7. Note CRUD (`cli/note.py`)

- **`note new`:**
  - The duplicate warning matches only an exact id or an exact case-insensitive title
    (`:83-94`). In JSON mode it still creates the note and attaches `warning`/`similar`.
  - The `--template` path builds nested `notes/<parent>/` folders, which contradicts the
    flat-layout rule. It ignores `taken_ids` and the `_collision_id` caps (`:97-114`).
  - The sync result is ignored (`:128-130`). An id collision there would print
    "Created" for a note the index refused.
  - The JSON reply carries the top 30 tags (`:144-148`), so agents reuse the tag
    vocabulary.
- **`note show`:**
  - Batch reads take many ids in one call (`:267-290`).
  - It adds a structured `oa` block when the body came from an open-access copy
    (`:196-218`) and wraps untrusted bodies (`:219-226`).
  - `--raw` bypasses the fence (`:232-241`), and CLAUDE.md says so.
- **`note update`:**
  - It validates enums up front (`:448-478`).
  - It rewrites the whole frontmatter from `NoteMeta` (`:534-536`), which drops unknown
    keys (section 11), then syncs (`:538-539`). Each call is two full tree scans plus a
    sync.
- **`note mv`** is careful: the destination must be inside the synced tree, there is no
  silent overwrite, and case-only renames on Windows are handled (`:584-621`).
- **`note rm`** deletes the raw file and assets, with a path-traversal guard
  (`:670-705`). It hard-codes `research/` instead of `vault.research_dir` (`:682-696`).

---

## 8. MCP server (`mcp/server.py`)

The command is `hpr mcp`, over stdio, and it needs `pip install hyperresearch[mcp]`
(`cli/mcp_cmd.py`, `pyproject.toml:44`). Nothing registers it in `.mcp.json`, and no
pipeline step uses it. It exists for Claude Desktop, Cursor and similar clients
(`README.md:286`).

| Tool | What it does | Notes |
|---|---|---|
| `search_notes` | FTS search with tag/status/parent/scholarly filters | **Full raw body per hit** (`:78-81`), no fence, default limit 10 |
| `read_note` | One note with metadata and body | Raw body, no `oa` block, no fence (`:93-107`) |
| `read_many` | Comma-separated ids | Same (`:121-132`) |
| `list_notes` | Summaries, no bodies | `limit=0` means all (`:162`) |
| `get_backlinks` / `get_hubs` | Link-table queries | Hubs count index-page links too |
| `vault_status` | Counts, top tags, links, words | |
| `lint_vault` | 4 rules only: missing tags/summary, broken links, orphans | The CLI linter has far more |
| `check_source` / `list_sources` | Reads the `sources` table | No auto_sync; **orphan bug** (below) |
| `fetch_url` | Calls `fetch_and_save` | Every `ValueError` is labelled `DUPLICATE_URL` (`:319-320`) |
| `create_note` | `write_note` + `enrich_note_file` + sync | Auto-tags from the vault vocabulary (below); returns a Windows backslash path (`:370`) |
| `update_note` | status/tags/summary | Validates status (`:389-402`); drops unknown frontmatter keys |

Findings, all measured in section 14:
- **The header is stale.** It says "Exposes 8 tools ... Read-only by design" (`:3-4`),
  but 13 tools are registered. The CHANGELOG made it read-write long ago
  (`CHANGELOG.md:494`).
- **No untrusted fence and no OA disclosure.** The CLI wraps fetched bodies and exposes
  `oa.body_is_not_from_source`; MCP does neither. A Desktop or Cursor client gets raw
  attacker-controllable page text, and cannot tell a preprint substitute from the
  publisher's text. `tests/test_mcp/` holds only `test_update_note.py`, so this gap is
  untested.
- **`check_source` reports orphans as fetched.** Once a note is deleted, `sources.note_id`
  becomes NULL, and `check_source` returns `{"exists": true, "note_id": null}`. The fetch
  path treats that same row as not a duplicate (`core/fetcher.py:11-23`; the fix for
  #84 is in `CHANGELOG.md:96`). The CLI `sources check` has the same bug
  (`cli/sources.py:81-87`), and the fetcher prompt follows "check, and fetch only if not
  already fetched", so the fetcher skips URLs whose note was deleted.
- **Contamination.** `create_note` runs `enrich_note_file` (`:360`). `auto_tag` scores a
  tag whenever **any single word** of it appears in the body (`core/enrich.py:27-38`),
  and run tags look like `china-rail-x9f2a1`. Measured: a note "Solar adoption in China"
  came back tagged `['solar', 'china-rail-x9f2a1']`, which puts it into another run's
  tag-scoped corpus. `repair --enrich` does the same for untagged notes
  (`cli/repair.py:121-128`).
- **Scaling.** FastMCP runs sync tools inline on its loop thread
  (`web/crawl4ai_provider.py:49` comment), so one cached connection is safe. But a slow
  `fetch_url` blocks every other tool call, and every call pays an `auto_sync` scan.

---

## 9. Web viewer (`serve/server.py`)

- **Server.** `hpr serve` runs a stdlib `ThreadingHTTPServer` bound to `127.0.0.1`,
  default port 8080 (`:605-640`). It disables `SO_REUSEADDR` on Windows
  (`:587-602`, careful) and opens one SQLite connection per request (`:349-363`).
- **Pages.** Home lists all notes, plus note pages with backlinks, tag pages, tag list,
  search (FTS limit 50), `/graph` and `/api/graph` (`:365-388`). The snippet is escaped
  before `<mark>` is injected, against XSS (`:532-542`).
- **Graph.** Client-side force layout, O(n²) per tick, about 340 ticks (`:203-239`).
  This is fine for hundreds of notes and slow for thousands (**estimate**).
- **Stale data.** No `auto_sync` runs, so the view reflects the last CLI sync.
- **No Host check.** No Host-header validation or auth exists on a localhost server
  that serves private vault content. That is the DNS-rebinding risk class (**low**,
  class-level, not tested).
- The pipeline never uses it. It is for humans only.

---

## 10. Agent docs injection (part of `Vault.init`)

`Vault.init` injects the CLAUDE.md blurb (`core/vault.py:191-194`,
`core/agent_docs.py:25-205`). It is about 180 lines, and a fresh vault's CLAUDE.md
measured 15,491 characters (1,836 words), roughly 3.9 K tokens. It loads in every Claude
Code session opened in that folder, research or not. It carries:
- the "Curate after every session" ritual, which the pipeline never performs;
- the lifecycle `draft → review → evergreen` and the untrusted-content policy;
- a "Searching the vault" section that teaches `search ... --json` with auto-included
  bodies.

The Codex blurb is shorter (`:210-265`).

---

## 11. Weaknesses (most severe first)

1. **No cross-session reuse; overlapping re-runs get a thinner corpus.** Section 4 has
   the evidence: `cli/vault_tag.py:1-16`, the tag-scoped queries, `core/hooks.py:3083-3087`,
   `cli/fetch.py:254-296`, `cli/fetch_batch.py:352-359`, `core/claims.py:125`,
   `hyperresearch-11-synthesize.md:231`. Severity **high**.
2. **Search output explodes.** `search --json` auto-includes up to 20 full bodies, and
   the pipeline never caps it (`cli/search.py:177`, `core/config.py:229`). Measured
   236,614 bytes for 20 notes of about 10 KB. Severity **high** for cost and for the
   reliability of gap checks under host output caps.
3. **The write lock is held during O(broken links x notes) resolution, with a 5 s busy
   timeout, under 10 to 12 parallel fetchers.** Evidence: `core/sync.py:141`, `367-398`,
   `core/db.py:233`, `core/profiles.py:265`. Measured 13.8 s per one-note sync and 5 of 6
   parallel writers failing at 6,000 broken links; 0 failures with 0 broken links.
   Severity **medium**, because it depends on how many broken links a real vault
   accumulates, which I did not measure.
4. **Implicit-AND query semantics.** A keyword list with one absent term returns zero
   hits, and step 13's "does the vault have evidence?" check uses exactly such lists
   (`search/fts.py:42-63`, `hyperresearch-13-gap-fetch.md:37`). Severity **medium**.
5. **Notes drop out of the index silently.** An invalid enum value, or an id collision,
   removes the note from the index. `auto_sync` discards the errors
   (`core/vault.py:213-221`, `core/frontmatter.py:34`, `core/sync.py:184-201`); measured.
   Severity **medium**.
6. **MCP returns raw bodies.** There is no untrusted fence and no OA disclosure; the
   docstring claims read-only with 8 tools; `check_source` has the orphan bug; any
   `ValueError` becomes `DUPLICATE_URL` (`mcp/server.py:3-4`, `78-81`, `93-107`, `257-271`,
   `319-320`); measured. Severity **medium**, but only for MCP users.
7. **Final reports are never indexed**, because they have no frontmatter
   (`hyperresearch-11-synthesize.md:231,253`, `core/sync.py:98-100`). Severity
   **medium** for reuse.
8. **Frontmatter rewrites drop unknown keys.** `extra: "ignore"` plus `model_dump`
   (`models/note.py:139`, `core/frontmatter.py:38-50`) means `author`, which fetch writes
   (`core/fetcher.py:177-178`), is never stored. Hand-added keys such as
   `authors`, `published` or `vault_tag` vanish on the next `note update`, batch or
   `repair`; measured. Severity **medium-low**.
9. **Deprecated notes stay in results**, only down-weighted by 0.3x in search and not
   filtered at all in `note list`. Excluding them is an instruction to the LLM
   (`search/fts.py:175-176`, `cli/note.py:335-373`). Severity **medium-low**.
10. **Index rebuild is destructive and crashes on unsafe tags.** It deletes all pages
    first and dies on tags with `/` or Windows-reserved characters; `repair` does not
    guard the call (`indexgen/generator.py:17-19`, `107`, `cli/repair.py:215-217`);
    measured. Severity **medium-low**.
11. **`archive-run`, which runs every run, sidelines `research/temp/` stubs** out of the
    index, and links break again (`cli/archive.py:51`, `135-138`, `hyperresearch.md:112`);
    measured. Severity **low-medium**.
12. **The auto-linker produces false links and rewrites fetched text.** Short ids are
    always in the vocabulary (`core/linker.py:31-32`, `107-129`), and `fetch-batch` runs
    it automatically (`cli/fetch_batch.py:339-348`); measured. Severity **low-medium**.
13. **`auto_tag` spreads other runs' tags** through single-word overlap
    (`core/enrich.py:27-38`, `mcp/server.py:360`, `cli/repair.py:121-128`); measured.
    Severity **low-medium**.
14. **The lifecycle is mechanical and never run.** Evergreen means 100 words plus any
    link, yet it earns a 1.5x boost; `expires` and `reviewed` are never set
    (`cli/repair.py:163-199`, `core/config.py:225`, `cli/lint.py:1740-1764`). Severity **low-medium**.
15. **`--ranked` and status boosts reorder only within the SQL `LIMIT` page**
    (`search/fts.py:111-126`, `167-190`). Severity **low**.
16. **Per-call overhead.** Every call eagerly imports over 30 subcommand modules
    (`cli/__init__.py`), runs schema DDL on open (`core/vault.py:65-73`) and scans the
    tree (`core/sync.py:89-102`). Measured 0.6 s per read and 0.9 s per write at 2,000
    notes. The fetcher loop runs about 5 calls per source (`sources check`, `fetch`,
    `note show`, 1 or 2 `note update`; `core/hooks.py:3083-3104`), about 3 to 5 s of local
    overhead per source before network and LLM time (**estimate** built from measured
    parts). Severity **low-medium**.
17. **The CLAUDE.md blurb costs about 15.5 K characters per session** in the vault folder
    (`core/agent_docs.py:25-205`); measured. Severity **low**.
18. **Storage amplification.** Each body is stored three times in SQLite (body,
    body_plain and the FTS copy) on top of the `.md` file (`core/db.py:75-79`, `202-210`).
    Measured 72 MB of SQLite for 21 MB of markdown. Severity **low**.
19. **Windows and portability.** MCP and fetch return backslash paths
    (`mcp/server.py:370`, `core/fetcher.py:277`). `research/` is hard-coded in fetch,
    `rm` and citecheck (`core/fetcher.py:210`, `263`, `cli/note.py:682-696`,
    `cli/citecheck_cmd.py:51`). `note new --template` creates nested folders
    (`cli/note.py:104-106`). Severity **low**.
20. **Embeddings add little.** Only the first 1,500 characters are embedded, any
    frontmatter edit re-embeds the note, the feature is off by default, and the pipeline
    never uses it (`core/embed.py:97-104`, `133-137`, `core/config.py:148-151`). Severity
    **low**.
21. **Web viewer.** No Host check, an O(n²) graph layout and no sync
    (`serve/server.py:365-388`, `203-239`). Severity **low**.
22. **Batch commands are partial and unvalidated.** One bad note aborts the batch
    halfway, and the error-collecting helper is dead code (`cli/batch.py:58-73`,
    `84-95`, `124-125`). Severity **low**.

---

## 12. What actually drives report quality here

- **Yes:**
  - Durable full source text for the whole run, readable in batches with `note show`.
  - Tag-scoped corpus assembly: the run's tag and per-chapter tags
    (`hyperresearch-1-5-chapter-partition.md:66`).
  - Per-source LLM curation by the fetcher: summaries, deprecations and claims with
    verbatim quotes (`core/hooks.py:3092-3140`).
- **Partly:**
  - The untrusted fence on CLI reads.
  - FTS search for gap checks, weakened by implicit AND.
  - Quality-ranked ordering in step 10.
  - Structured `oa`, tier and content-type metadata shown to readers.
- **No:**
  - The lifecycle, index pages, auto-linker, embeddings, dedup, topic tree and batch
    edits.
  - The MCP server and the web viewer.
  - Cross-run carry-over. For overlapping runs it is **negative**.

---

## 13. Ideas for VAFER

1. **Reuse at the question level** (INDEX.md, as already designed), and never let a
   "seen before" check hide evidence. When a URL or fact was used before, pull its saved
   quote, URL and access date into the current run's notes instead of skipping it.
2. **Make the report itself findable** through the INDEX line and plain grep. Do not
   make indexing depend on frontmatter that the writing step is told to omit.
3. **No shared database for parallel researchers.** Per-researcher notes files, VAFER's
   current `notes/<researcher-id>.md`, cannot contend for a lock.
4. **Return paths and short snippets from any search, never full bodies.** Keep every
   tool result well under the host's output cap, and read selectively afterwards.
5. **Use any-term matching for "do we already have this?" checks,** such as several
   `rg -i -e` patterns, or OR in a query. Report zero-hit queries as such and never as
   "no evidence".
6. **Treat saved research as data on every read path.** VAFER's Reuse rule already says
   so; hyperresearch fences only some paths, and MCP none.
7. **Carry an access date and a volatility class on every saved fact,** and re-check
   volatile ones on reuse. hyperresearch has `expires`/`reviewed` fields that nothing sets.
8. **Base any quality mark on verification,** for example "quote re-checked on date X",
   and never on word counts or link counts.
9. **Avoid automatic substring linking and single-word auto-tagging.** They fabricate
   provenance and leak notes across runs.
10. **Keep the always-loaded instructions small.** hyperresearch's CLAUDE.md block is
    about 15.5 K characters in every session.
11. **Store the cited passage (30 words or fewer) with URL and date as the default unit.**
    Optionally keep raw text only for pages behind headline facts, so that VAFER's final
    re-check survives link rot. That is the useful part of hyperresearch's full-text store
    without its size.
12. **Exclude rejected sources by construction,** with a separate section or file. Do
    not rely on an instruction to skip them.
13. **Never delete derived files before validating their inputs.** hyperresearch deletes
    all index pages, then crashes on a tag.
14. **If VAFER ever caches pages, key them by a normalized URL,** and show what was found
    in the cache. `fetch-batch` reports only a count of what it skipped.

---

## 14. Experiments (method and raw results)

Scripts sat in the session scratchpad under `hr-exp/scripts/` and ran as
`.venv/Scripts/python.exe -I -B <script> <clone>/src <scratch vault>` from a scratch
working directory. All vaults were created fresh under the scratchpad's
`hr-exp/vaults/`.

- **Unit checks** (`exp_unit.py`):
  - `NoteMeta(title=..., author=...)` serialized without `author`.
  - A parse and serialize round trip dropped `authors`, `published` and `vault_tag`.
  - `status: bogus` raised `ValidationError`.
  - `preprocess_query('solid state battery energy density 2024')` gave
    `"solid"* "state"* "battery"* "energy"* "density"* "2024"*`.
  - `gpt4o latency` gave `"gpt"* "4"* "o"* "latency"*`.
  - `battery OR anode` passed through raw.
- **Behaviour checks** (`exp_vault.py`):
  - B0: CLAUDE.md measured 15,491 characters and 1,836 words.
  - B2: a bad-enum note was not indexed. `auto_sync()` returned `None`, and only an
    explicit `execute_sync` showed the `ValidationError`.
  - B3: the three FTS queries returned 1, 0 and 0 hits (section 5).
  - B4: `auto_link` added `['python', 'wikipedia']` to the "Snake husbandry" note.
  - B5: `enrich_note_file` produced the tags `['solar', 'china-rail-x9f2a1']`.
  - B6: the link was resolved after the stub was created; after `archive_run` plus sync
    it was unresolved again and the stub was no longer indexed.
  - B7: the first `build_all` built 10 pages. Tagging 3 notes `ml/deep-learning` made it
    raise `FileNotFoundError` with 3 pages left.
  - B8: MCP `search_notes` and `read_note` bodies were unwrapped. The 13 registered
    tools are `check_source, create_note, fetch_url, get_backlinks, get_hubs,
    lint_vault, list_notes, list_sources, read_many, read_note, search_notes,
    update_note, vault_status`. `check_source` after deleting the note returned
    `exists: true, note_id: null`, while `existing_live_note_for_url` returned None.
- **Scale** (`exp_scale_build.py`, `run_cli.py`): 2,000 notes of 1,500 random words
  from a 30-word vocabulary, one tag, and 0 or 3 broken links per note. The numbers are
  in the section 3 table.
  - In the 12-writer test, my first attempt used ids that did not exist, and 3 of 12
    failed per round with `NOT_FOUND`. The rerun with valid ids gave 12 of 12 succeeding
    in both rounds.
  - Search size: 236,614 bytes with bodies vs 22,983 bytes with `--no-body`, at an
    average body of 10,232 bytes. `note list --all -j` over 2,000 notes: 793,824 bytes.
