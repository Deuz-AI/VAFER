# Stress test: vafer-research v0.0.4 on eight untested question types

Date: 2026-10-30. Desk check only, with no web searches.

## Summary

Read literally, v0.0.4 is a pipeline for history questions. Outside that shape, five things go wrong:
- The source ladder ranks a vendor's own benchmark as "primary". It cannot tell a pilot study from a systematic review, and it treats a legislative proposal like the law in force.
- Conflicts have no "different definition" outcome.
- The list variant contradicts "do not search first" and would exceed the 200-search session cap.
- The checker raises false alarms on 50M, unit conversions, parentheses, percentage results and dotted dates, yet passes a wrong attribution on a long page.
- Since commit a927973, step 6 runs a bare `diff`, which in PowerShell compares two file names and reports success.

The reuse lookup also fails under PowerShell. Standard scenarios project to 20–40 minutes, and the list scenario to 45–90. The budgets leave almost no room for fixes.

## Basis

- **Read:** the whole skill, both tests, and the measured v0.0.4 run (`C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/e8210f42-5bc4-4715-a0fe-4bc7e2e72a35/scratchpad/t2/v04/.vafer/research/2026-10-29-yalova-tarihi/`).
- **Probes:** offline, with synthetic figures: `scratchpad/v005-review/stress_probe.py` (checker) and `scratchpad/v005-review/rgtest/` (PowerShell `diff` and `rg`).
- **Estimates:** scaled from the measured run (11 subagents, about 307 tool calls, 22 minutes) under the a927973 guide of 6–10 searches per section and at most three gap researchers.
- **"Prior":** marks model knowledge that was not checked.

| # | Scenario | Tier a literal lead picks | Subagents | Searches | Minutes |
|---|---|---|---|---|---|
| 1 | pgvector / Qdrant / Weaviate | Standard | 9–11 | 60–90 | 20–30 |
| 2 | Real change in the minimum wage | Standard | 8–12 | 55–90 | 25–40 |
| 3 | Intermittent fasting and remission | Standard or Deep (ambiguous) | 9–11 / 13–17 | 60–90 / 100–150 | 20–30 / 35–50 |
| 4 | EV charging operators and tariffs | Deep, table variant | 13–20 | 250–450 | 45–90, or cut off |
| 5 | EU AI Act for a 20-person SaaS | Standard | 9–11 | 60–90 | 20–30 |
| 6 | Follow-up: Yalova 1999, economic effects | Standard with reuse | 6–9 | 45–75 | 15–25 |
| 7 | Codex, no subagents, cached search | Standard in mode C | 0 | 45–65 | 35–60 |
| 8 | "kuantum bilgisayarlar" | Quick | 0 | 8 or fewer | 2–4 |

## Findings

**F1. Scenario 1: technical comparison (pgvector, Qdrant, Weaviate at 50M vectors).**

A literal lead picks Standard and, unless the user answers, fixes the workload silently: dimensions, QPS, filtering, managed or self-hosted. Scope and conditions are required only for medical, legal, financial or safety questions (SKILL.md:70).

- **Sections:** one per product, so each researcher gathers different metrics. A shared items × attributes frame exists only for lists of 8+ items (briefs.md:56).
- **Ladder:** vendor benchmarks are "the issuer's own page", which is primary (SKILL.md:63), so they outrank independent ones (F10). Engineering posts on medium.com default to lead class (vafer_check.py:42).
- **Freshness:** no rule discounts a benchmark of an older version (F12).
- **Checker (probed):** `50,000,000 × 1536 × 4 bytes ≈ 307 GB` was flagged `equation-wrong`, and "50M" was flagged against a source saying "50 million".

Implication: add a comparison shape (one frame, shared columns in every brief, a stated workload profile). Treat a vendor's claims about rivals as claims from an interested party.

Confidence: high (probed), and medium for the decomposition.

**F2. Scenario 2: real change in the Turkish minimum wage since 2020.**

A literal lead picks Standard and may ask up to three questions: net or gross, which inflation index, end date (SKILL.md:33).

- **Dependency:** the wave is parallel (SKILL.md:42), but the calculation section needs the nominal and CPI sections, so it repeats their searches or waits. Nothing says "researchers fetch the inputs; the lead computes".
- **Conflicts:** published "real change" figures differ mostly by definition: net or gross, base month, TÜİK or ENAG, mid-year raises, the 2022 AGİ change (prior). The conflict types (briefs.md:25) have no "definition" type, and the ladder ranks the official index first (SKILL.md:43), so a method dispute gets a winner instead of "both, by definition".
- **Checker (probed):** `evaluate()` ignores parentheses (vafer_check.py:304–314), so a correct `(a / b) / (c / d) − 1` was flagged. `− 1 = %55,2` fails, while `× 100 − 100 = %55,2` passes. `28.12.2023` was read as 28.12 and flagged.
- **Flag load:** none of the measured run's 13 flags found an error (F11). A numbers-heavy report raises dozens, each needing a written disposition, and the definitions readers need go to evidence.md (F13).

Implication: add a computed-answer shape (inputs from researchers, arithmetic by the lead, definitions in one report paragraph) and a "definition" conflict type.

Confidence: high.

**F3. Scenario 3: medical evidence review (intermittent fasting and type 2 diabetes remission).**

- **Tier:** "contested high-stakes" fits Deep (SKILL.md:30) and "three or more sub-questions" fits Standard (SKILL.md:29), so the cost roughly doubles or not depending on the reading.
- **Ladder:** every paper is "scholarly", so a 36-patient trial and a systematic review share a rung, and an agency's lay page ("official") outranks both.
- **Conflicts:** the adjudicator's verdicts (briefs.md:45) and the five-column conflict table (style.md:14) cannot express design, size, follow-up or bias. The gap-finder's "errors that sources commonly make" (briefs.md:66) may catch DiRECT, a diet-replacement trial (prior), cited as fasting evidence.
- **Safety:** one sentence covers it (SKILL.md:70).
- **Checker:** the word "researcher" in English prose triggers `label-leak` (probe; vafer_check.py:57–58).

Implication: add a health ladder (guideline or systematic review > RCT > observational > opinion). Give design, n and follow-up beside each effect, add a certainty sentence, and require a harms row.

Confidence: high on the gap; medium on how much the output suffers.

**F4. Scenario 4: exhaustive list with prices (EV charging operators in Türkiye).**

A literal lead picks Deep (SKILL.md:30), then meets four contradictions:
- **Frame:** step 1 forbids searching (SKILL.md:41), but the table variant writes a searched frame into plan.md (briefs.md:58) without saying who searches or when.
- **Assignments:** step 2 assigns sections; the variant assigns batches of rows.
- **Assembly:** step 5 assembles "from the section drafts" (600 words each, briefs.md:24), but row batches return cells.
- **Effort:** the 6–10 search guide (briefs.md:18) does not fit a batch of 15 operators.

The budget breaks too. If EPDK's licence list (prior; size unchecked) holds 100 or more operators, 2–4 searches each means 250–450 searches, past the 200-search cap in hosts.md:11. No rule says to rank by network size. App-only or JavaScript tariff pages make `fetch` return boilerplate, so † marks pile up. The report has no home for a 100-row table or a CSV, although lists of 20+ items are a "5x" axis (architecture.md:89).

Implication: give lists their own shape:
- a frame scout that may search;
- budgeted batch filling with a priority order;
- a closing pass for missing items;
- a CSV file beside report.md;
- columns defined up front (AC, DC, VAT, as-of date).

Confidence: high on the contradictions; medium on the search count.

**F5. Scenario 5: legal (EU AI Act for a 20-person SaaS in 2026).**

- **Branching:** the answer depends on role (provider or deployer), use case (high-risk, transparency, minimal) and use of third-party general-purpose models. Nothing asks for branches or a role × obligation × date table.
- **Ladder:** it has no legal status. The Regulation, the Commission's November 2025 Digital Omnibus proposal to delay high-risk deadlines (prior; October 2026 status unchecked), guidelines and codes of practice all count as "official or legal text" (SKILL.md:63). "A later correction beats an earlier statement" (SKILL.md:43) can then promote a proposal over the law in force.
- **Checker:** pools are whole pages (vafer_check.py:477–481). A sentence giving an SME the €35 million / 7% ceiling passed with 0 flags against a page holding both figures in another clause (probe). On the full Regulation, every article number "matches".

Implication: label legal status (in force, applies from, adopted, proposed, guidance), and match a cited number against its receipt span before the whole page.

Confidence: high on the ladder and the checker; medium on the example facts.

**F6. Scenario 6: follow-up on an existing Yalova run.**

- **Lookup:** in PowerShell (Codex on Windows, or the PowerShell tool), the lookup in SKILL.md:80, `rg -i -l "yalova" .vafer/research/*/plan.md`, fails with os error 123 and exit 2 because the glob is not expanded. `--glob plan.md` works.
- **Seeding:** reuse.md:12 says to seed "the earlier rows and their states" and never remove a row, which would put 15 history rows into a checklist about the economics of 1999. Line 11 ("only the notes for the rows you need") suggests the opposite.
- **Mismatches:** reuse.md:7 expects a `check` field the measured plan.md header lacks, and "answer changed: old → new" (reuse.md:17) means nothing for a new question.
- **Savings:** the row-11 receipts and the Blocked and Not found lines save about 3–8 searches.
- **Scope:** provincial data for 1999 is thin, so national figures will crowd in. No rule checks a figure's place, which was the bare model's error (README.md:22).

Implication: separate "refresh the same question" from "borrow receipts for a neighbouring question". Fix the glob, and add a scope check (place, period, unit).

Confidence: high.

**F7. Scenario 7: Codex with no subagents and cached search.**

- **Search mode:** hosts.md is read only when a tool fails (SKILL.md:86) or at assembly (SKILL.md:45). Cached search never fails visibly, so the up-front mode test (hosts.md:21) comes too late, and the design's "first line suggests live search" (architecture.md:38) never reached hosts.md.
- **Context:** mode C holds 45–65 searches and 40–60 page windows in one context, so compaction is likely, with no instruction to re-read plan.md.
- **Gap wave:** "The lead does not run the gap wave alone" (SKILL.md:44) contradicts mode C.
- **Fetch:** without sandbox network, fetch fails in a way SKILL.md:53 does not list, and its fallback, WebFetch, is absent on Codex. PDFs fail in PowerShell here too: pdftotext is only on Git Bash's PATH.
- **Check:** it runs on the lead's own receipts ("note receipts", vafer_check.py:584), but the status line reads like a page check. The manual re-check triggers only "without a shell" (SKILL.md:55), so it never runs.
- **Dates:** receipts say "opened 2026-10-30" for cached content, and style.md:15 bars mentioning that in the report.

Implication: add a host preflight before planning (search mode, subagents, network). Put the "as indexed" date in the report's date line, and re-check by hand whenever no snapshots exist.

Confidence: high on the contradictions; medium on the timing.

**F8. Scenario 8: a bare topic ("kuantum bilgisayarlar").**

A literal lead picks Quick (SKILL.md:33): one batch of searches, 2–5 page opens, a chat answer with links and a date, and an offer to go deeper. The result roughly matches the bare model plus opened sources.
- **Ambiguities:** the same paragraph allows clarifying questions, so an interactive lead may ask first. "Escalate" (SKILL.md:37) does not say to what.
- **Follow-up:** Quick saves nothing, so "go deeper" starts from zero.

Implication: low priority. Define "escalate", and let Quick save a minimal notes file.

Confidence: medium.

**F9. Regression: step 6's diff no longer calls the script.**

- **Evidence:** commit a927973 replaced `python scripts/vafer_check.py diff …` with a bare `diff <run>/report.before-edit.md <run>/report.md` (SKILL.md:46). The Checking section names only `fetch` and `check`.
- **PowerShell probe:** in Windows PowerShell 5.1, `diff` is `Compare-Object`. On an edit that changed 2.324,70 to 2.342,70 and dropped [1], it listed the two file names and reported success. `vafer_check.py diff` on the same pair reported 4 problems and exited 1.
- **GNU diff:** it shows every rewritten line, about 2,900 words to read by hand.
- **Backstop:** the later `check` catches changed cited numbers, not deleted facts.

Implication: restore the script call.

Confidence: high.

**F10. The ladder and the conflict model are shaped for history.**

- **Evidence:** one ladder for every domain (SKILL.md:43, :63), with the issuer's own page as primary, four conflict types (briefs.md:25) and four verdicts (briefs.md:45). The only domain hook is free text, "For {domain}, look first for: {record types}" (briefs.md:16). Independence scores were left out on purpose (architecture.md:68).
- **Effect:** scenarios 1–6 each mis-rank evidence. The checker verifies transcription, not validity, so it cannot see this.

Implication: without adding scores, make three short additions:
- an issuer's claims about itself or rivals count as press until confirmed independently;
- a "definition or scope differs" conflict type, with "both, by definition" as a verdict;
- a five-line domain table (health, law, software, statistics, prices).

Confidence: high.

**F11. Checker precision outside history.**

- **False alarms (probes):** 50M, unit conversions, parentheses, percentage results, ISO dates (`2024-10-30` raises "10 not found"), dotted dates, and "researcher" as a leaked label.
- **Missed:** a wrong attribution on a long page.
- **Measured precision:** none of 13 flags found an error, while the design keeps the check advisory until 80% of flags are real (architecture.md:14).
- **Room:** the script is at its 700-line cap (test_skill_hygiene.py:19).

Implication: cut false alarms first:
- skip the conflict table's B column and NOT-FOUND sentences;
- read %, k/M/bn and dates;
- match against receipt spans first.

Confidence: high.

**F12. Freshness and status are not modelled.**

- **Evidence:** the only time rules are as-of dates (SKILL.md:59) and "later correction beats earlier" (SKILL.md:43). Volatility appears only in reuse.md:13.
- **Effect:** nothing discounts old benchmarks (1), stale tariffs (4), proposals (5) or cached pages (7).

Implication: for volatile facts, record the source's own date and version, prefer the newest record of equal rank, and print the oldest as-of date in the report.

Confidence: medium-high.

**F13. One report skeleton, in Turkish, built for history.**

- **Evidence:** the fixed headings "Bir bakışta", "Ayrışan kaynaklar" and "Bilinmeyenler" (SKILL.md:45) and the Turkish status line (SKILL.md:47) also apply to English questions (1, 3, 5).
- **Method:** "Evidence and method go to evidence.md" (style.md:3) removes definitions from the report (2).
- **Missing slots:** assumptions (1, 5), a decision table (1, 5), study quality (3), a long table or CSV (4).

Implication: name sections by function in the reader's language. Keep definitions and assumptions in the report and research method in evidence.md.

Confidence: medium.

**F14. The budgets leave almost no room.**

- **Evidence:** the SKILL.md body is at 1,431 of 1,500 words, the text before the loop at 374 of 400, briefs.md at 927 of 1,000, the script at 700 of 700 lines, and references at 4 of 4 (test_skill_hygiene.py:13–19).
- **Room left:** hosts.md (619 words), style.md (437) and reuse.md (318).

Implication: fixes must replace text, move it into those files, or raise a cap deliberately.

Confidence: high.

**F15. Time.**

- **Evidence:** the measured Standard run took 22 minutes against the bare model's 5, which is 4.4 times bare. The design's guardrail is 1.5 times (architecture.md:92), and SKILL.md:49 sets no time limit.
- **Effect:** the per-section guide does not bound the gap wave, the adjudicator or the flag dispositions.

Implication: cutting false alarms (F11) is the cheapest saving.

Confidence: medium (scaled from one run).

## Recurring problems, ranked by harm

1. **History-shaped ladder and conflicts (F10).** Biased headlines pass every check (1, 2, 3, 5).
2. **Lists (F4).** Contradictory steps and the search cap break a "5x" axis.
3. **Checker precision (F11).** False alarms cost time; long pages get false assurance (1, 2, 4, 5).
4. **No freshness or status model (F12, F7).** Stale answers look current (1, 4, 5, 7).
5. **Editor guard regression (F9).** Any run can lose facts silently; trivial fix.
6. **Fixed Turkish skeleton (F13).** No assumptions, definitions or appendix (1–5).
7. **Fragile hosts (F6, F7).** PowerShell breaks reuse; mode C contradicts itself; a notes-only check reads as a page check.
8. **Time (F15).** 4–8 times bare in every Standard scenario.
9. **Reuse refreshes only the same question (F6).** The follow-up axis gains little.

The budget headroom (F14) limits every fix above.
