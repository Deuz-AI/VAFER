# vafer-research 0.2: architecture

Date: 2026-10-28. A synthesis of the design panel: six proposals (P1–P6), three judges, two red teams of the lead's draft (P3), and `webfetch-spike.md` in this folder. It starts from P1, which had the highest combined judge score, grafts in P2, P5, P4 and P6, and fixes the red teams' high-severity findings. Nothing is measured yet; every multiple is a target.

## Idea

Code, not the model, checks every cited figure against a saved copy of the page. Every part of the question ends in a visible state. Every run leaves a dated ledger the next question starts from. It has fewer serial steps than hyperresearch (HR), and the checking is done by a script, not by more agents.

## Pillars

**1. Receipts from page snapshots.** Researchers save each number, date and quote they may cite as a receipt: the shortest exact span that holds it (for a table, the row with its header, unit and period), plus the URL, the opened date, the record's own date, and primary or secondary. Where a shell has network, `vafer_check.py fetch` saves each page as a text snapshot, keeping its own charset, its table rows, the access date and a hash, and running PDFs through pdftotext when installed. Receipts are copied from the snapshot or checked against it. On Codex, researchers copy from the line window. WebFetch is used only to find and skim pages: it caps quotes at 125 characters, paraphrases the rest, turns windows-1254 Resmî Gazete text into "�", splits table rows and cannot read PDFs (the spike predicts at most 2 of 12 receipts exact).
*Beats HR:* HR judges sentences against fetcher-written `quoted_support` that no code compares with the page. *Home:* the researcher brief in briefs.md; a clause after rule 4; the script.

**2. Figure contract and a local check.** The report copies figures from receipts, and each computed figure is shown as an equation with cited inputs (`230 kWh × 2,61 TL/kWh [2] = 600,3 TL`). `vafer_check.py check <run>` matches every cited number, date and quoted span against the receipts for the same URL and against that page's snapshot. It recomputes equations, lints `[n]` markers, the Sources list and leaked labels, and reads Turkish, Greek and Bulgarian formats. Flags go to check.md, and the lead answers each one: fixed, derived, false alarm (with a reason), or † with a footnote. Nothing is deleted to clear a flag. The script replaces the draft's `Source check: pending` line, so a skipped check shows. It runs once wave 1 is in and again before delivery. It stays advisory until the logged flags prove at least 80% real. The lead re-opens only what the script could not settle, at most eight items, instead of 0.1's ten sources.
*Beats HR:* HR's triage passes "5%" against "25%" and "[12]" against "2012". It matches quotes against any note, finds zero pairs under `## Kaynaklar` and still passes, checks no arithmetic, and accepts a pre-stubbed `[]` log. HR light runs no cite-check at all. *Home:* `scripts/vafer_check.py` (stdlib only, about 450 lines and about 12 offline tests); SKILL.md steps 4 and 6; hosts.md.

**3. Rows that name their record and end visibly.** Plan rows come from three places: the question's verbatim atoms (entities, places, periods, format cues), needs an expert would expect, and the fresh gap-finder. Each row names the record that settles it (issuer, document, period, language). A row is COVERED only on that record, or on two independent records with the reason the record was out of reach. Every row ends COVERED, CONFLICT, NOT-FOUND (with queries, search mode and tool errors) or NOT SEARCHED, and a NOT SEARCHED row is never saved as a dead end. Key figures are labelled primary, derived or secondary only, and the reply carries one coverage line.
*Beats HR:* its coverage matrix is a self-audit in the lead's own context with "proceed anyway" exits, and its instruction critic runs only in full. Our aggregator exchange rate (efccf1b) becomes a visible "secondary only". *Home:* SKILL.md Done when, step 1 and rule 5; the gap-finder brief in briefs.md.

**4. Lists as frame-first tables** (about eight items or more). Build the frame from the record that enumerates the items plus a second route. Give researchers batches of rows, and fill each cell with a value, "not found (queries)" or "n/a". Close with passes by unused routes until one adds nothing, then check the count against any stated total.
*Beats HR:* its fetchers get URL batches, not rows, and light reads 15–25 sources in all. *Home:* the Variants section of briefs.md.

**5. Memory as a by-product.** There is no save step. The plan.md header is written before the first search and serves as the index. It holds the question verbatim; terms folded to plain ASCII in English, the user's language and the sources' languages (`rg -i` misses İ/i, measured); and `as_of | tier | status | check`. Notes become a dated ledger with typed `Source:`, `Caution:`, `Not found:` and `Blocked:` lines that carry host, search mode and date. Every tier starts with one lookup. On a hit the lead:
- seeds rows from the earlier run;
- re-opens dated facts, once per URL;
- recomputes derived figures;
- lists what changed;
- opens the reply with "answer unchanged" or "answer changed: old → new [n]".

Saved text may add rows but never removes rows or skips checks, and the gap-finder never sees it. INDEX.md goes.
*Beats HR:* each HR run gets a fresh tag, already-fetched URLs are never re-tagged, freshness fields are never set and dead ends are not kept. A follow-up is a new 30–40 minute run. *Home:* the Files and Reuse sections of SKILL.md; a new references/reuse.md (about 450 words, read only on a hit).

**6. A loop with fewer serial steps.** The gap-finder starts in the first message, alongside the scout searches. On Claude Code, researchers and the gap-finder are fresh `general-purpose` subagents, never forks, because a fork inherits the whole conversation. Subagents start in the background, and with fork mode on (the default since v2.1.302) an interactive lead cannot wait for them, so it integrates each result as it arrives. Codex and `claude -p` keep synchronous waves. report.md is drafted while wave 1 reads and then edited section by section, never regenerated. plan.md is about 300 words of rows, edited in place. Two floors apply: three or more row groups means spawning researchers, and Standard always runs one gap wave unless every row is COVERED. There are no time limits.
*Beats HR:* about 5 serial stages against about 22 in HR full (estimate), and a lead context far from compaction. *Home:* SKILL.md steps 1–5; hosts.md.

**7. Honest host modes.** The method note opens with a host line: host, search mode, shell and network, subagents, file writes.
- If the run folder cannot be written (the default `codex exec` is read-only), one line says "nothing saved, no automated check". Researchers then reply with receipts inline, and the lead re-opens up to ten headline claims.
- In cached or unknown Codex search mode, volatile receipts read "as indexed", and the first line suggests live search.
- On Windows the script forces UTF-8 output, reads BOM and UTF-16 files, and runs as `python` or `py -3`, never `python3`. Notes are written only with the host's file tools.

*Beats HR:* 22 of HR's Codex commands fail in PowerShell, and resume and the Codex Stop hook skip cite-check. *Home:* hosts.md; `compatibility`; step 0.

**Budget and build order.** The SKILL.md body grows from 1,170 to about 1,450 words (cap 1,500), with the text before the loop held at 400. briefs.md grows from 521 to about 900 words and hosts.md from 360 to about 600; reuse.md is new at about 450. The hygiene test swaps its no-scripts rule for one stdlib script of at most 500 lines. Build in this order, with a quick side-by-side after each step: instructions (pillars 1, 3, 6, 7), then the script (2), then memory (5), then lists (4).

## What the user sees

Quick answers look as they do today, but their figures come from page text. A Standard reply is the report's opening answer plus two lines, for example "Kapsam: 14/16 satır; bulunamadı: Bulgaristan gece tarifesi (sorgular…)" and "Kaynak kontrolü (script, sayfa kopyası): 41 rakamın 39'u eşleşti; 2'si denklem; 1'i †". A follow-up names the run it reuses and opens with whether the answer changed.

## What we take from hyperresearch, and what we leave out

**Take:**
- subagents that read sources and write quoted notes per source;
- page text held by code, here as snapshots;
- the instruction critic's checklist, moved to the fresh gap-finder before drafting;
- period-pinned primary records, without a chase quota;
- cite-check, made deterministic and tied to the cited URL;
- quote integrity, for every quote style and checked against the same source;
- dangling-citation detection, extended to unused sources, ranges and any Sources heading;
- verdicts for re-opened pages, without "delete" or "soften";
- freshness fields, actually filled in;
- "what source would overturn this?", where a miss adds no confidence;
- the lesson that prose-only checks get skipped.

**Leave out:**
- triple drafts, the synthesizer, the four critics, and patcher or polish edits after the check;
- number-substring triage and pair sampling;
- gates that only check files exist, and length bands;
- the SQLite vault, per-run tags, PageRank, and quality and independence scores;
- lead-run searching with URL scoring, chase quotas and source quotas;
- a headless browser per URL;
- hooks, tool locks and the always-on CLAUDE.md block;
- confidence bands;
- scholarly APIs (academic acquisition is conceded).

**Held until an ablation shows a gain:**
- a verifier subagent (the Opus 5 guide advises against it);
- a skeptic subagent;
- researchers on a faster model tier;
- rows written from model knowledge;
- text-fragment check links;
- a user-level library.

## 5x claims

| Axis | Target | Measured by | Confidence |
|---|---|---|---|
| Unsupported numbers, dates and quotes the report does not mark † (causes are not checked) | ≤1/5 of HR light's rate and ≤1/3 of bare's; supported count at least bare's; † on ≤10% of claims; not worse than `/deep-research` | The script's audit mode extracts every figure, date and quote from every arm's report and matches it against snapshots taken at run end by one fetcher; a person checks each non-match and 10 random matches per report | Medium where snapshots exist; low on Codex without shell network |
| Searches per follow-up when the answer or its sources are saved | ≤1/5 of a fresh run's, accuracy within 2 points | 3 domains × 4 follow-ups in fresh sessions; arms: memory, empty folder, bare, bare given the folder; counts from logs | Low to medium: the hit rate is unknown, and memory is per folder |
| Missing rows in lists of 20+ items | ≤1/5 of bare's and HR light's | One enumeration with a frame key (for example, 30 metropolitan water tariffs), with 10 cells opened | Low: the mechanism's evidence is one task |

**Not 5x:**
- Time: 0.1 already takes about a tenth of HR light's time, and bare beats both. Report time as a ratio to bare, with Standard at most 1.5× bare as a test guardrail.
- Quality of a single report: parity with HR light, 0–5 points over bare.
- Run-to-run spread: a floor; claiming more needs five or more runs.

With about 40 claims per report, the test shows direction, not a precise ratio.

## Side-by-side (about two days, no harness)

Use three questions, with answer keys written first:
- the TR/GR/BG electricity bill (computed figures);
- a dated Turkish-local history question;
- a post-cutoff enumeration.

**Claude Code** comes first, since nobody has run 0.1 there:
- 0.2, 0.1 and bare, twice each;
- `/deep-research` and HR light once per question;
- HR full once, if approved.

**Codex:**
- the same three arms, launched with `--sandbox workspace-write -c web_search="live"`;
- one default `codex exec` arm, for the read-only path.

Log every arm's settings. Since v2.1.302, `claude -p` starts in Manual mode, which denies the web tools, so pass `--permission-mode auto`. Keep a mechanism only if removing it moves its own number.

## Spikes before building

1. Run 0.1 once on Claude Code. Does "wait for all" break? Do background researchers keep their web tools? Does the lead deliver early?
2. Snapshot reach on the electricity question. How many primary records can a stdlib fetch read (HTML, XML, PDF with or without pdftotext, JavaScript-only pages, 403s)? Do WebFetch's predicted failures hold when it is actually called?
3. Codex on Windows. Does python run in the sandbox? Does `network_access=true` enable `fetch`? Does the default `codex exec` fall cleanly into the read-only path? Do subagents get web search?
4. Matcher precision. Run a prototype over the 0.1 Codex reports and HR's sample report, and label the flags by hand.
5. Diff the two Codex runs whose depth varied before adding floors.

## Questions for the user

1. Which 5x do you mean: fewer wrong numbers, cheaper follow-ups, complete lists, or something else?
2. Your Claude Code settings deny WebSearch and WebFetch. Is that deliberate, and which search tool should the skill use there?
3. Which host do you research on most, and can Codex be launched with workspace-write and live search?
4. Do you research from one project folder or many? Memory is per folder unless you want a user-level library.
5. Is a stdlib script of about 450 lines acceptable? Are equations, † footnotes and the two status lines acceptable in Turkish reports?
6. Should the test run HR full (1.5–2.5 h, a large share of the usage window), or HR light only?
