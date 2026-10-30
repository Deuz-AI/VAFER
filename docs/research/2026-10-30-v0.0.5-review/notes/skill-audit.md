# vafer-research v0.0.4: skill audit (2026-10-30)

Evidence sources (times are UTC):
- **Package:** `skills/vafer-research/` and `tests/` at commit 5ebab1a. All 48 tests pass.
- **Run** (`run/` below): the v0.0.4 Yalova run, which used the skill as it stood before a927973. Path: `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/e8210f42-5bc4-4715-a0fe-4bc7e2e72a35/scratchpad/t2/v04/.vafer/research/2026-10-29-yalova-tarihi/`.
- **Transcripts** (`tx/`): `C:/Users/VECTOR/.claude/projects/C--Users-VECTOR-Documents-GitHub-VAFER/e8210f42-5bc4-4715-a0fe-4bc7e2e72a35/subagents/`. The lead is `agent-ab569b7fdce2cbf4b` (08:57:01–09:19:54) and the judge is `agent-afb4b61ca239b5b72`.
- **My probes and counters:** `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/2b233dc9-15bf-498e-93c7-9a4c6367ee83/scratchpad/v005-review/`.

## Summary

v0.0.4 reads lean, but its time and context go to mechanical work, and its checker verifies less than the skill claims. Findings from the one Yalova run:
- **Lead load:** the lead's context peaked near 210k tokens. It hand-wrote eleven briefs, re-typed the report, and improvised scripts for renumbering, citation fixes and dispositions.
- **Gap wave:** a 50-second gap-finder triggered a six-minute serial gap wave.
- **Checker:** `vafer_check` matches numbers anywhere on the cited page, trusts receipts without checking them against snapshots, and drops unverifiable figures from its denominator. Twelve of its thirteen flags were noise.
- **Fetcher:** it rejects data tables, hard-wrapped texts and, without pdftotext, PDFs. Its index races.
- **Residual errors:** the judge's only errors were conflict and "not found" verdicts, which the checker cannot see.
- **Regression:** step 6 regressed to a bare `diff`.
- **Constraints:** Turkish and Yalova assumptions and exhausted budgets constrain v0.0.5.

## Findings

**F1. Step 6 lost the guard command (a regression in a927973).**
- *Evidence:*
  - SKILL.md:46 now says "Run `diff <run>/report.before-edit.md <run>/report.md`". The copy used in the run said `python scripts/vafer_check.py diff …`.
  - The Checking section (SKILL.md:51–55) documents only `fetch` and `check`.
  - On this host, `diff` resolves to GNU diff 3.12 in Git Bash and to `Compare-Object` in PowerShell 5.1. Neither guards facts, and GNU diff of a rewritten report dumps the whole text into context.
- *v0.0.5:* name the script in step 6. The README's "guarded by vafer_check diff" is currently untrue of the skill text.
- *Confidence:* high.

**F2. The script call breaks outside the skill folder and off Windows.**
- *Evidence:*
  - SKILL.md:53 demands an absolute path, then gives two relative examples (`python scripts/vafer_check.py`); hosts.md:14 repeats them.
  - `python3`, the usual name on macOS and Linux, is never offered (hosts.md:29 rules it out for Windows only).
  - In the run, the lead fixed every brief by hand (final report, item 7).
  - A failed fetch is silent: researchers fall back to WebFetch and to receipts marked unverified.
- *v0.0.5:* one canonical command with a `python` / `python3` / `py -3` fallback.
- *Confidence:* high for the text, medium for frequency.

**F3. The check proves a number occurs somewhere on the cited page, not that the page supports the sentence.**
- *Evidence:*
  - It pools every number from the cited URL's receipts and snapshot (vafer_check.py:474–481, 295–296).
  - In probes, "29 Kasım 1923 [1]" against a page saying "29 Ekim 1923" scored 2/2 matched. A population of 98.347 matched a page where 98.347 is hectares.
  - Never checked:
    - uncited years and integers up to 10 (:538);
    - uncited quotes (quotes are checked only under `if cited:`, :525–536);
    - names, causal and comparative claims, and qualitative claims;
    - which table row or period a figure came from.
  - SKILL.md:19 still promises that every cited number, date and quote "matches".
- *v0.0.5:* describe the check honestly; accuracy gains must come from elsewhere (F15).
- *Confidence:* high.

**F4. Receipts count as evidence without being compared to snapshots, and "unverified" changes nothing.**
- *Evidence:*
  - `texts()` merges receipt spans with the snapshot (:474–476). The unverified marker is parsed (:378) and then ignored (:463–464).
  - Probes:
    - Snapshot "2.501", receipt "2.504" plus an invented quote: "1 of 1 figures matched, 0 flags".
    - A receipt marked "official; unverified" (a WebFetch paraphrase, per SKILL.md:53) counted as matched.
  - Codex's default sandbox has no network (hosts.md:24), so there are no snapshots. `check` then only compares the report with notes the same agents wrote.
- *v0.0.5:* require each receipt span to occur in its snapshot, and exclude unverified receipts from matching.
- *Confidence:* high.

**F5. The match ratio hides unchecked figures and reaches the user as a verification rate.**
- *Evidence:*
  - `check_number` returns without counting when no cited URL has evidence (:485–488).
  - In a probe, five figures cited to an unsnapshotted source gave "2 of 2 figures matched" and a single "unverifiable" flag.
  - The status line (SKILL.md:47; in the run, "Kaynak kontrolü 252/258") reads as 98% verified, and the lead who wrote the report dispositions every flag.
- *v0.0.5:* count unchecked figures, or keep the ratio out of the user-facing line.
- *Confidence:* high.

**F6. The skill manufactures most of its own flags, and the noise trained the lead to dismiss the one that mattered.**
- *Evidence:* run/check.md has 13 flags: 9 false alarms, 3 "derived" and 1 †.

  | Cause | Flags |
  |---|---|
  | Rejected values in the mandatory "Ayrışan kaynaklar" B column (style.md:14) | F10–F12 |
  | "Not found" sentences that name the figure | F1, F2, F7 |
  | "16. yüzyıl" against "XVI." | F4, F13 |
  | Calendar conversions the skill requires | F5, F8, F9 |
  | A splitter bug, since fixed | F6 |

  - The lead wrote `dispo.py` just to fill in dispositions.
  - F10 ("4,80 not found") pointed at the verdict the judge later found wrong (F15), and was closed as a false alarm.
  - `diff` adds its own noise:
    - Removing a repeated figure, which style.md:16 and briefs.md:52 demand, reports "number missing" and "citation missing" (probe).
    - A translated quote in quotation marks gives "quote-mismatch" (probe).
- *v0.0.5:* exempt the rejected column, centuries and declared conversions, or flags will keep being rubber-stamped.
- *Confidence:* high.

**F7. The fetcher rejects the top rungs of the ladder.**
- *Evidence:*
  - **Boilerplate rule:** a page with fewer than three lines of 80 or more characters is "boilerplate" (:228).
    - In the run, the Project Gutenberg text (922 lines, 2 of them long) and the archive.org Toynbee OCR failed this way, so primary 1921 material became "unverified" (run/evidence.md).
    - In probes, a 25-row statistics table and 6,000 characters of hard-wrapped prose were both rejected as boilerplate.
  - **PDFs:** they need `pdftotext` (:171–183). Without it the status is `pdf-no-text` and the PDF is discarded (:211–214). On this machine pdftotext comes from MSYS2.
  - **Missing instructions:** SKILL.md:53 covers only empty, boilerplate and doc-binary pages. `pdf-no-text`, http-429 and JavaScript-only pages get no instruction, and WebFetch cannot read PDFs (SKILL.md:55).
  - **In the run:** 12 of 63 fetches failed, mostly on official and scholarly hosts (Atatürk Ansiklopedisi ×3, TÜİK, DergiPark 429 ×2). The 2025 population ended up resting on a governor's X post and a DHA report.
- *v0.0.5:*
  - Keep raw PDFs for the host's own reader.
  - Treat table-shaped text as content.
  - Back off on 429.
  - Add a route for data portals.
- *Confidence:* high.

**F8. `pages/index.tsv` races under parallel researchers.**
- *Evidence:*
  - `cmd_fetch` reads the index, downloads sequentially (up to 30 seconds per URL), then rewrites the whole file (:232–243).
  - In the run there are 73 snapshot files but only 63 index rows; 14 files have no row, and fetches overlapped from 08:59 to 09:08.
  - A lost row also loses a failed status, so an empty or boilerplate page can return as evidence through the header scan (:409–411).
- *v0.0.5:* make index updates safe under concurrency.
- *Confidence:* high.

**F9. Receipt parsing fails silently on natural forms.**
- *Evidence:*
  - A receipt written with `<https://…>` is dropped (:33, probe). That is the placeholder shape in SKILL.md:74 and briefs.md:22, and the Markdown autolink form.
  - A span that contains a straight quote is truncated (probe).
  - Nothing warns. The URL loses its rung label and falls back to the domain list.
- *v0.0.5:* accept autolinks and inner quotes, or have `check` report unparsed receipt lines.
- *Confidence:* high for the mechanism, medium for frequency.

**F10. The plan is written without searching, so gap-finder items cost a serial wave.**
- *Evidence:*
  - SKILL.md:41 says "Do not search first", and all 12 plan rows in the run are tagged [prior].
  - The gap-finder took 50 seconds (08:58:57–08:59:47) and found Kibotos 1096, the 1915 deportation and the 1923 exchange.
  - It runs alongside the launch wave, so these items needed a serial gap wave (09:04:40–09:10:22). Its researchers were heavier than the section researchers: 38–46 tool calls against 26–33.
  - Without subagents, the gap-finder runs first instead (briefs.md:74), so the modes are inconsistent.
- *v0.0.5:* the niche and recent topics the skill's description targets will suffer more from a prior-only plan.
- *Confidence:* high for the run, medium for the generalisation.

**F11. The lead is the serial bottleneck and the context sink.**
- *Evidence:*
  - **Context and output:** the lead's context grew from 44k to about 210k tokens, and it produced about 78k output tokens.
  - **Reading before acting:** before planning, it read SKILL.md, briefs, style and hosts (about 3,500 words). It then read the checker source to learn the Sources and evidence-line formats, which SKILL.md never states.
  - **Briefs:** eight researcher briefs ran to 548–619 words each; all 11 briefs total 77k characters. briefs.md:3 and the undefined "paste the short rules" (:27) force re-typing the ladder and style rules every time.
  - **Re-typing the report:** it read 33k characters of drafts and re-typed the 25k-character report. It did this twice because the test harness refused report* file names.
  - **Improvised scripts:** it renumbered 36 sources with an improvised `renumber.py` holding a hand-typed URL-to-title map (briefs.md:24). It also wrote `fix1.py` for 6 citations the editor detached, wrote `dispo.py`, and patched the checker.
  - **Time:** assembly took 6.5 of the 23 minutes. The report text is generated three times (researchers, lead, editor), and the editor's own benefit was never isolated.
- *v0.0.5:* move concatenation, renumbering, the Sources list and flag bookkeeping into the script, and put static brief text in a file the subagent reads.
- *Confidence:* high.

**F12. Exact-span receipts cost the most tool calls and add almost nothing to verification.**
- *Evidence:*
  - Researchers made 126 Bash calls (98 grep, sed or cat over snapshots, plus 22 fetches) and 41 WebFetch calls.
  - 25 of the 34 WebFetched pages were also snapshotted, and about 80 URLs were snapshotted for 36 that were cited.
  - When a snapshot exists, the check matches against the whole page, so the span adds nothing. Spans are never validated either (F4).
  - Receipts still provide the rung label, fallback text and some reading discipline.
- *v0.0.5:* decide what receipts are for; a rung line per source may suffice.
- *Confidence:* medium.

**F13. The length target contradicts the structure.**
- *Evidence:*
  - style.md:3 assumes "a reader who has five minutes".
  - The structure allows 3–6 sections (SKILL.md:41) of up to 600 words each (briefs.md:24), plus gap-wave sections; Deep allows up to 10 researchers.
  - The run's report has 2,858 words, about 12 minutes of reading. Nothing sets a total length.
- *v0.0.5:* set a total length from the reader's purpose, so gap-wave sections do not lengthen the report by default.
- *Confidence:* high.

**F14. Some trigger words are undefined and some rules contradict each other.**
- *Undefined:* "headline" row, claim, conflict or conclusion (SKILL.md:31, 43, 44, 55, 63; briefs.md:18), "key fact" (:18), "material fact" and "would change the answer" (:44). The gap-wave and Ultra stopping decisions rest on them, and the run's lead called the trigger vague (item 9).
- *Contradictions:*
  - Deep allows "up to 10" researchers at one per section, but plans have 3–6 sections (:41–42).
  - "The lead does not run the gap wave alone" (:44) conflicts with the no-subagent mode (:42; briefs.md:74).
  - hosts.md is read only "when a tool is missing" (:86), yet the host line needs it every run (:45).
  - `report.before-edit.md` collides with the rule against file names starting with report (hosts.md:12).
  - There is no PARTIAL row state (:17), although the leak check expects one (vafer_check.py:57). The run invented "Kapsam 15/15 (4'ü kısmi)".
  - "Süre" (elapsed time) needs a start time the lead is never told to record.
- *v0.0.5:* define the trigger terms operationally and remove the contradictions.
- *Confidence:* high.

**F15. Conflict and "not found" verdicts have no evidence rule, and they caused the judge's only v0.0.4 errors.**
- *Evidence:*

  | Case | What the run did | What the judge found |
  |---|---|---|
  | C15, 4.80 m | Rejected as "snippets, not opened" (run/conflicts.md) | The governor's office and the culture ministry both give 4.80 m |
  | C12, "27 köy" | Called unsourced because only Wikipedia carried it | Wikipedia cites Gingeras |
  | Law no. 1533 | Stayed NOT-FOUND | The v0.2 arm found it |

  - The ladder (SKILL.md:43) ranks sources. It does not require opening the losing side's best source before ruling against it, or chasing a lead's footnote before declaring a claim unsourced; briefs.md:16 says only "use them to find higher sources".
  - Negative findings ("bulunamadı") go into the report, and their flags were closed as false alarms.
- *v0.0.5:* this is the clearest accuracy lever.
- *Confidence:* high.

**F16. The model's own calendar arithmetic outranks every source, with no tool behind it.**
- *Evidence:*
  - SKILL.md:43 says "a calendar check beats any source; convert … yourself", and briefs.md:18 adds "do not copy a conversion".
  - Nothing deterministic converts dates. The checker flags conversions, and the lead closes them as "derived" (check.md F5, F8, F9).
  - The conversion was right on Yalova, but a wrong one would silently override correct sources.
- *v0.0.5:* add a converter to the script.
- *Confidence:* medium.

**F17. Turkish and Yalova assumptions are hard-coded, and the only benchmark is contaminated.**
- *Evidence:*
  - **Turkish skill text:**
    - Turkish headings and status line (SKILL.md:45, 47).
    - `rg -i -l "yalova"` (:80).
    - Turkish phrases and table headers (style.md:7, 9, 13, 14) and "X'e göre" (briefs.md:52).
  - **Checker language limits:**
    - `SOURCE_TITLES` covers only English, Turkish, Greek and Bulgarian (:35). In a probe, "## Fuentes" or "## Quellen" made every citation dangling and checked 0 figures.
    - The check and source-mix labels (:37–38), number-scale words (:52–55) and leak check (:57–58) are Turkish or English only.
    - Sentence splitting (:48) needs a Latin, Greek or Cyrillic capital, so CJK, Arabic and Hebrew text never splits. A sentence that starts with a digit merges with the previous one: "… [1]. 1923'te … [2]." stays one unit (probe), and that pattern is common in Turkish history prose.
  - **Contamination:** the report's first sentence (run/report.md:5) repeats style.md:26 verbatim ("Yalova'nın ne zaman kurulduğu bilinmiyor"). The lead flagged contamination (item 8), but a927973 fixed only the briefs example.
- *v0.0.5:* make headings, the status line and the checker's vocabularies language-neutral, and replace the Yalova style example before the next side-by-side.
- *Confidence:* high.

**F18. Guidance a strong deep-research agent needs is missing.**
- *Evidence:*
  - **Scoping:** questions are allowed only if they "would change what you search" (SKILL.md:33). The reader's purpose is never asked, and "Reader" in the run's plan.md was assumed.
  - **Query strategy:** two rules (:60–61). Nothing covers site: or filetype: operators, going straight to the record or catalogue (gazette archive, statistics API), date-bounded queries, or citation chasing.
  - **Source independence:** "copies … count once" (:63) gives no way to detect copies, and the source mix counts URLs, not origins.
  - **Stopping:** Ultra is unbounded ("There is no time limit", :49), and there is no run-wide search budget. hosts.md:11 notes a 200-search session cap, and a Standard run already used 99 WebSearch calls.
- *v0.0.5:* add compact guidance on these points within the word budget (F19).
- *Confidence:* medium.

**F19. The hygiene budgets are nearly exhausted.**
- *Evidence:* tests/test_skill_hygiene.py:13–19 sets these limits; the line cap already yields dense lines such as vafer_check.py:275.

  | Item | Used | Limit |
  |---|---|---|
  | SKILL.md body | 1,431 words | 1,500 |
  | Words before the loop | 374 | 400 |
  | References | 4 | 4 |
  | briefs.md | 927 words | 1,000 |
  | vafer_check.py | 700 lines | 700 |
- *v0.0.5:* every addition needs equal cuts or a deliberate budget change.
- *Confidence:* high.

**F20. The measured run differs from real use.**
- *Evidence:*
  - The lead ran as a background subagent at spawn depth 1, with researchers at depth 2 (tx/*.meta.json). That caused the report* write refusal and a re-write, so the 22 minutes include harness overhead.
  - There was one question, primed by the style example (F17).
  - The fixes in a927973 are unmeasured.
- *v0.0.5:* run the next side-by-side with the lead in a main session, on a fresh question.
- *Confidence:* high.
