# Verified claims: vault, notes, search index, embeddings, links, MCP server and web viewer (vault)

Checked on 2026-10-28 against the clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`
(0.12.0, HEAD `327498b`). Paths such as `core/sync.py` are under `src/hyperresearch/`. Step
files such as `hyperresearch-13-gap-fetch.md` are in `src/hyperresearch/skills/`.

**Method.**
- I opened every cited location.
- I grepped all step files and agent prompts (`skills/*.md`, `core/hooks.py`,
  `core/agent_docs.py`) for vault commands.
- I re-ran the reader's measurements with my own scripts on copies of their two synthetic
  2,000-note vaults. The vaults differ only in broken links: 0 in one, 6,000 in the other.
  The scripts are in the session scratchpad under `verify-vault/`. They import the clone with
  its own `.venv` Python (`-I -B`).
- I added three probes:
  - read commands while another process holds the write lock;
  - MCP vs CLI on an open-access note;
  - end-to-end CLI timings.
- The clone stayed clean: `git status` was empty, and no file under `src/` is newer than my
  scripts.

## Verdicts

1. **partly**: The pipeline never lets a new run see an earlier run's sources. Each run mints a unique vault_tag, even on a re-run. Every corpus query filters by that tag. Already-fetched URLs are skipped and never get the new tag, so overlapping re-runs see fewer sources, not more. (evidence: cli/vault_tag.py:1-16; hyperresearch.md:120,227,230; hyperresearch-10-triple-draft.md:33,104,110; hyperresearch-13-gap-fetch.md:37; core/hooks.py:3083-3087; cli/fetch.py:254-296; cli/fetch_batch.py:85-101,352-359; core/claims.py:125)
   Evidence:
   - **Unique tag, re-runs included.** `cli/vault_tag.py:14-16` says the tag is "collision-safe across: re-runs of the same query". `:121-132` adds a random `secrets.token_hex(3)` suffix and checks it against existing tags. The entry skill calls it at bootstrap step 2 (`hyperresearch.md:120`).
   - **Corpus assembly is tag-scoped.**
     - `note list --tag <vault_tag>` at `hyperresearch-2-width-sweep.md:172,183`, `-4-loci-analysis.md:28`, `-7-source-tensions.md:29` and `-10-triple-draft.md:33,62,104`.
     - `search ... --tag` at `-8-corpus-critic.md:39`, `-10-triple-draft.md:110` and `-13-gap-fetch.md:37`, and in two agent prompts: the dialectic critic (`core/hooks.py:695`) and the corpus critic (`:3304`).
     - The run's note and source counts join through the tag (`core/runs.py:327-356`).
   - **Nothing re-tags an old note.** The fetcher is told "Check if it's already fetched ... If not already fetched, fetch it", with no else branch (`core/hooks.py:3083-3087`). `hpr fetch` on a known URL returns `DUPLICATE_URL`, or appends a breadcrumb when `--suggested-by` is given. Neither path adds a tag (`cli/fetch.py:253-296`).
   - **Three cited locations miss the point.**
     - `hyperresearch.md:227,230` are in the Recovery fallback list, not corpus queries.
     - `fetch-batch` is not called by any step or agent prompt. The only mention is in the Codex blurb (`core/agent_docs.py:226`).
     - `core/claims.py:125` is accurate: `INSERT OR IGNORE` keeps the old run's `vault_tag`. It has little effect, though. Cite-check reads claims by `note_id` (`core/citecheck.py:128`), step 9 reads the per-run claim JSON files (`hyperresearch-9-evidence-digest.md:33`), and no step queries claims by tag.
   - **"Never" is too strong.** Two vault-wide, untagged paths exist:
     - The PreToolUse reminder fires before every WebSearch or WebFetch (matcher at `core/hooks.py:3820`). It says "BEFORE searching the web, check existing research" and gives `search "<your query>" -j` with no tag (`:3584-3585`). Only per-project Claude installs get it (`:3683`).
     - The cite-checker's wrong-source lookup is `claims search "<key phrase>" -j`, also with no tag (`core/hooks.py:3524`).

     The `DUPLICATE_URL` error also names the old note id (`cli/fetch.py:291`).

   Correction: For the run's tag-scoped corpus the claim holds. Nothing re-tags an already-fetched note, so an overlapping re-run's corpus and counts leave those sources out. Earlier runs are not fully invisible, though. The PreToolUse reminder (Claude project installs) and the cite-checker's `claims search` read the whole vault, and the fetcher learns the old note id. None of these adds old notes to the run's tag. "Fewer sources" is untested. The tag-scoped wave and coverage checks may trigger more fetching instead (see missed).

2. **partly**: Final reports are never indexed. The synthesizer is told to write no YAML frontmatter, and sync skips files without frontmatter, so reports are invisible to hpr search, MCP, the viewer and the link graph. (evidence: src/hyperresearch/skills/hyperresearch-11-synthesize.md:231,253; core/sync.py:98-100)
   Evidence:
   - **Reports are told to carry no frontmatter.** `hyperresearch-11-synthesize.md:231` and `:253` say "No YAML frontmatter". Step 10 says the same (`-10-triple-draft.md:74`), and the polish auditor strips frontmatter as a leak (`core/hooks.py:1602`).
   - **Sync skips such files.** `core/sync.py:98-100` skips any file without frontmatter. The report sits at `research/notes/final_report_<tag>.md`, inside the synced tree.
   - **The other readers all go through the index.** Search, MCP and the viewer read SQLite, and links are extracted only from synced notes (`core/sync.py:315-328`).
   - **This reverses an earlier design.** An older changelog entry says "Synthesis notes saved as feedback loop (agent Q&A becomes searchable)" (`CHANGELOG.md:497`).
   - **The exception.** The polish auditor keeps the frontmatter block when "some wrappers require it", and then sets `status: evergreen` (`core/hooks.py:1623-1642`). A report with frontmatter is synced like any note. The repo's own bench harness strips frontmatter before grading (`codex_bench/harness.py:514,732`), which suggests reports do sometimes keep it.
   - **A lint rule still expects indexed reports.** The `workflow` rule looks for reports in the notes table (`n.id LIKE '%final_report%'`, `cli/lint.py:1558-1562`). In default runs that query cannot find the report.

   Correction: In default runs the final report is not indexed, so search, MCP, the viewer and the link graph never see it. "Never" overreaches: a report that keeps frontmatter is indexed, whether a wrapper requires it or a hygiene leak leaves it. Indexing hangs on a hygiene rule, not on design.

3. **confirmed**: `hpr search --json` returns the full bodies of up to 20 notes by default, and no pipeline search call passes --no-body, --max-tokens or --limit. Measured: 236,614 bytes for 20 hits of about 10 KB each, vs 22,983 bytes with --no-body. (evidence: cli/search.py:177; core/config.py:229; grep of src/hyperresearch/skills/*.md and core/hooks.py (calls at hyperresearch-13-gap-fetch.md:37, hyperresearch-10-triple-draft.md:110, core/hooks.py:695,3304))
   Evidence:
   - **Bodies come with `--json`.** `cli/search.py:177`: `want_body = include_body or (json_output and not no_body)`.
   - **The default limit is 20.** `cli/search.py:108-109` takes it from `core/config.py:229` (`search_default_limit: int = 20`).
   - **No call caps the output.** My grep found no vault `search` call with `--no-body`, `--max-tokens` or `--limit`. The only `--limit` in any prompt belongs to `scholar search --limit 25` (`core/agent_docs.py:77`).
   - **The calls.**
     - `-10-triple-draft.md:110`, `-13-gap-fetch.md:37` and `core/hooks.py:695,3304`.
     - `-8-corpus-critic.md:39`, which adds `--include-body` explicitly.
     - The untagged reminder at `core/hooks.py:3585`.
   - **Re-measured on a copy of the reader's synthetic vault, with a different query.** 236,978 bytes for 20 hits vs 22,910 bytes with `--no-body`. The average body was 10,592 characters, and all 20 bodies were fenced.

   Correction: None needed. The 10 KB bodies are synthetic; real paper bodies run 20,000 to 80,000 characters (comment at `core/config.py:184`). Step 8 asks for bodies on purpose.

4. **confirmed**: Sync resolves every broken link inside a BEGIN IMMEDIATE lock using unindexed LOWER() joins, with Python's default 5 s busy timeout. At 2,000 notes, a one-note sync took 0.70 s with 0 broken links vs 13.8 s with 6,000. In the 6,000 case, 5 of 6 parallel `note update` calls failed with 'database is locked'; with 0 broken links, 12 of 12 succeeded. (evidence: core/sync.py:141, 338-398; core/db.py:233; core/profiles.py:265; scratch experiment described in docs/research/2026-10-27-hyperresearch/read-vault.md section 14)
   Evidence:
   - **The lock.** `core/sync.py:141` runs `BEGIN IMMEDIATE`. Inside that transaction, `:204` calls `_resolve_links_incremental`, which re-resolves every NULL link in the vault (`:362-398`).
   - **The unindexed joins.** The joins compare `LOWER(n.id)` (`:379`), `LOWER(a.alias)` (`:387`) and `LOWER(n.title)` (`:395`). No expression index exists (`core/db.py:66-108`). `idx_aliases_alias` is `COLLATE NOCASE`, which a `LOWER()` comparison cannot use.
   - **The timeout.** `core/db.py:233` calls `sqlite3.connect(str(db_path))` with no `timeout`, so Python's 5 s default applies.
   - **The parallelism.** `core/profiles.py:265` sets `"wave1_fetchers": (10, 12)`.
   - **My replication:**

     | Measurement | 0 broken links | 6,000 broken links |
     |---|---|---|
     | One-note plan + sync, mine | 0.28 s | 11.1 s and 18.7 s (two runs) |
     | One-note plan + sync, reader's | 0.70 s | 13.8 s |
     | 6 parallel `note update`, mine | 6 of 6 succeeded | 5 of 6 failed with `database is locked`, same as the reader |

   Correction: The numbers replicate. Two refinements:
   - **Most failures lose the update.** 4 of my 5 failures hit the `auto_sync` that runs before the write (`cli/note.py:480-481`), so the update was lost, not just left unindexed. The one failure after the write (`cli/note.py:538-539`) was picked up by the next successful sync.
   - **The load is synthetic.** 6,000 broken links means 3 per note, and nobody measured the count in a real vault. The mechanism is not overstated; its severity depends on that count.

   Reads fail under the same contention too (see missed).

5. **confirmed**: The pipeline never uses embeddings, MinHash dedup, the topic tree, index pages, batch edits, the MCP server, the web viewer or repair. The draft-to-evergreen lifecycle is a CLAUDE.md instruction plus mechanical repair rules. (evidence: grep of src/hyperresearch/skills/*.md and core/hooks.py for embed/--semantic/dedup/topic/index/repair/mcp/serve (none found); core/agent_docs.py:179-196; cli/repair.py:163-199; core/config.py:148)
   Evidence:
   - **What the grep found.** Nothing for `embed`, `--semantic`, `topic`, `index`/`build_all`, `repair`, `batch` or `serve`.
     - "Dedup" appears only as the agent removing duplicate URLs from its queue (`-2-width-sweep.md:99`).
     - The only `mcp` hits are Claude-in-Chrome tool names for the browser fetcher (`core/hooks.py:3391`).
   - **No internal path reaches these features.** `build_all` is called only from `cli/index.py:25`, `cli/repair.py:217` and `cli/watch.py:67`. Promotion exists only in `repair`, and its rules are mechanical (`cli/repair.py:163-199`):
     - `draft` becomes `review` at 50 or more words with a summary and any tag.
     - `review` becomes `evergreen` at 100 or more words with any link in or out.
   - **The lifecycle is a CLAUDE.md block.** "Curate after every session" lists `repair -j` and the lifecycle (`core/agent_docs.py:179-194`).
   - **Embeddings are off by default.** `provider: str = "none"` (`core/config.py:148`).

   Correction: Accurate, with two footnotes:
   - **Near-duplicate detection does run.** Step 3's `sources independence --tag` clusters near-duplicate bodies with the same shingle and Jaccard code, pairwise (`core/independence.py:24,109-118`). Only the MinHash `dedup` command is unused.
   - **One lifecycle touch exists.** The polish auditor sets `status: evergreen` on a report that keeps frontmatter (`core/hooks.py:1632`). That is the only lifecycle step in the pipeline prompts.

6. **partly**: The MCP server returns raw fetched bodies, with no <untrusted-source> fence and no oa disclosure, unlike the CLI read paths. Its header claims 8 read-only tools while 13 read-write tools are registered. (evidence: mcp/server.py:3-4, 78-81, 93-107, 121-129 vs cli/note.py:196-226 and cli/search.py:211-217; CHANGELOG.md:494; measured in scratch experiment B8)
   Evidence:
   - **The header is stale.** `mcp/server.py:3-4` says "Exposes 8 tools ... Read-only by design". The file has 13 `@server.tool()` decorators. My probe listed all 13: check_source, create_note, fetch_url, get_backlinks, get_hubs, lint_vault, list_notes, list_sources, read_many, read_note, search_notes, update_note and vault_status. The changelog agrees ("MCP server is now read-write", `CHANGELOG.md:494`; "All 13 tools verified", `CHANGELOG.md:163`).
   - **Bodies are raw.** See `mcp/server.py:78-81`, `:101-107` and `:125-129`. The file never references `wrap_body` or `untrusted`. The CLI fences bodies at `cli/note.py:219-226` and `cli/search.py:211-217`.
   - **Probe on an open-access-substituted note:**

     | Read path | Fence | OA disclosure |
     |---|---|---|
     | MCP `read_note` | none | no `oa_*` fields; the body still opens with the banner "Open-access full text substituted" |
     | MCP `search_notes` | none | returns `oa_version: acceptedVersion` |
     | CLI `note show` | fenced | an `oa` block with `body_is_not_from_source: true` |

   Correction:
   - **The missing fence is confirmed.**
   - **"13 read-write tools" overstates.** The server is read-write, but only 3 of the 13 tools write: `fetch_url`, `create_note` and `update_note` (`mcp/server.py:298-322,325-371,374-`).
   - **"No OA disclosure" overstates.** MCP lacks the structured `oa` block that `note show` builds (`cli/note.py:196-218`). The disclosure still travels in the body, though. The CLI fetch paths prepend a blockquote banner to it (`cli/fetch.py:480-488`, text built at `core/oa.py:664-711`), and MCP returns that body verbatim. `search_notes` also returns `oa_version` (`search/fts.py:156`), just as CLI search does. CLI search has no `oa` block either, so only `note show` gives the full disclosure.
   - **MCP's own fetches get no OA rescue.** `fetch_url` goes through `core/fetcher.fetch_and_save`, which has no open-access recovery.

7. **partly**: Weakness: The vault provides no cross-session reuse, and overlapping re-runs get a thinner corpus. (evidence: cli/vault_tag.py:1-16 ("collision-safe across re-runs of the same query"). All corpus queries are scoped: hyperresearch.md:227 `note list --tag <vault_tag> --all -j`, hyperresearch-13-gap-fetch.md:37 `search ... --tag <vault_tag> --json`. Fetcher prompt core/hooks.py:3083-3087 says "If not already fetched, fetch it" and gives no retag step. cli/fetch.py:254-296 never adds tags on duplicates. cli/fetch_batch.py:352-359 reports only a skipped count. core/claims.py:125 `INSERT OR IGNORE` keeps the old vault_tag.)
   Evidence: The mechanism is the same as in claim 1, with the same caveats on `hyperresearch.md:227`, `fetch-batch` and `claims.py:125`. Further evidence:
   - Run counts join through the tag (`core/runs.py:327-356`).
   - Step 2 treats a fetch wave as done when the tagged note count reaches 80% of the URLs queued (`-2-width-sweep.md:170-175`, `core/profiles.py:305`).
   - The coverage check and Wave 2 also count by tag (`-2-width-sweep.md:179-200`).

   Correction: Somewhat overstated.
   - **"No cross-session reuse" is too absolute.** Some reuse exists:
     - the PreToolUse reminder searches the whole vault before web searches (`core/hooks.py:3584-3585`, Claude project installs only);
     - the cite-checker's `claims search` has no tag (`:3524`);
     - URL dedup saves the network fetch.

     None of these puts old evidence into the run's tagged corpus, so for the corpus the claim holds.
   - **"Thinner corpus" is inference.** Skipped URLs never count toward the wave and coverage checks. The orchestrator may therefore keep polling for the 80% wave threshold, or launch Wave 2 for items that look thin. The safer statement: an overlapping re-run loses the earlier run's sources from its corpus and probably fetches more to make up for it. The net corpus size was not measured.

8. **confirmed**: Weakness: search --json auto-includes full bodies, and the pipeline never caps output. (evidence: cli/search.py:177 `want_body = include_body or (json_output and not no_body)`. core/config.py:229 `search_default_limit: int = 20`. No --no-body, --max-tokens or --limit in any skill or agent search call (hyperresearch-13-gap-fetch.md:37, hyperresearch-10-triple-draft.md:110, core/hooks.py:695, 3304). Measured 236,614 bytes for 20 hits of about 10 KB each vs 22,983 with --no-body.)
   Evidence: Same as claim 3, re-measured (236,978 vs 22,910 bytes). The always-loaded CLAUDE.md blurb presents bodies as opt-in: `search "query" --json # Full-text search` next to `search "query" --include-body --json # Full-body search, not just titles` (`core/agent_docs.py:141-143`). That likely explains why no call caps the output.
   Correction: Not overstated as stated. Three things set the real size:
   - **Hit counts.** The tag scope and the implicit AND of all query terms (`search/fts.py:62-63`) often keep hits under 20.
   - **Real body sizes.** Real bodies are larger than the synthetic 10 KB ones.
   - **Host output caps.** The Bash tool here truncates output past 30,000 characters. That bounds the context cost of one call, but it hides lower-ranked hits and their ids, which hurts "do we have this already?" checks.

## Notes on the rest of the summary

- **"Every MCP tool call opens the database, runs schema DDL" is wrong for MCP.**
  - The server caches one `Vault` and one connection per process (`mcp/server.py:20-29`), so the DDL runs once.
  - 11 of the 13 tools call `auto_sync` on every call: a tree scan, plus a sync if files changed. `check_source` and `list_sources` do not (`mcp/server.py:264,282`).
  - For the CLI the statement holds, except that a sync runs only when the plan has changes (`core/vault.py:219-221`).
- **The per-call costs re-measure close.** End to end, at 2,000 notes with no broken links, I measured 0.52 to 0.57 s per read (`note list`, `note show`) and 0.55 to 0.85 s per `note update`. The summary says about 0.6 s and 0.9 s.

## Missed by the reader

- **Reads fail too under write contention, with a misleading error.** I measured this; the chain runs in four steps:
  1. Every open runs `init_schema` (`core/vault.py:66-72`). Its `INSERT OR IGNORE INTO _meta` needs the write lock (`core/db.py:244-247`); I confirmed that this statement is the one that blocks.
  2. While another process holds the lock past the 5 s timeout, that statement raises `database is locked`.
  3. `compute_sync_plan` reaches `vault.db` inside a `try` that treats any `OperationalError` as a fresh vault (`core/sync.py:104-111`). It then plans every note as new: 2,000 of 2,000 in my probe.
  4. The failed INSERT leaves the connection mid-transaction. `execute_sync`'s `BEGIN IMMEDIATE` (`core/sync.py:141`) then fails with `cannot start a transaction within a transaction`.

  With a writer holding the lock for 10 s, `note list`, `search` and `note show` all exited 1. So the claim-4 contention also breaks read-only agents: drafters, critics and cite-checkers.
- **The PreToolUse reminder is the only cross-run reuse nudge, and it is uncapped.**
  - Before every WebSearch or WebFetch (matcher at `core/hooks.py:3820`), it tells the agent to run `search "<your query>" -j` with no tag (`:3584-3585`). That search covers the whole vault, so it can return up to 20 full bodies from any run.
  - Only a per-project Claude `install` sets it up (`:3683`). It is skipped by `--global` (`:3706`) and by `--steps-only` (`cli/install.py:98-117`), and Codex never gets it (`core/hooks.py:3963`).
  - Its behavior therefore depends on how hyperresearch was installed. It bears on claims 1, 7 and 8.
- **Tag-scoped run accounting shapes what a re-run does.**
  - Manifest counts join through the run tag (`core/runs.py:327-356`).
  - Step 2 ends a wave when the tagged note count reaches 80% of the URLs queued (`skills/hyperresearch-2-width-sweep.md:170-175`, `core/profiles.py:305`). In an overlapping re-run the skipped URLs never count, so the threshold can be out of reach.
  - The coverage check then marks those items thin and launches Wave 2 (`:179-200`).
  - The more likely cost of the missing reuse is time and fetches, not only a thinner corpus.
- **Cite-check bypasses the run tag both ways.**
  - Mechanical triage reads claims by `note_id` (`core/citecheck.py:128`). The stale `vault_tag` on claims (`core/claims.py:125`) therefore does not hurt it.
  - The LLM cite-checker's wrong-source lookup is `claims search "<key phrase>" -j` with no tag (`core/hooks.py:3523-3525`). It can name a note from an earlier run as the correct source, and that note then enters the report without ever being in this run's corpus.
- **The CLAUDE.md blurb teaches that bodies are opt-in, but search does the opposite.** The blurb pairs `search "query" --json` ("Full-text search") with `--include-body --json` ("Full-body search, not just titles") (`core/agent_docs.py:141-143`). `cli/search.py:177` auto-includes bodies whenever `--json` is set. Agents reading the blurb have no reason to add `--no-body`, so the output cost in claims 3 and 8 is accidental, not a design choice.
