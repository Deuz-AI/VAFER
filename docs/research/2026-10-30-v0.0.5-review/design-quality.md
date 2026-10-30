# v0.0.5 design, quality lens: better answers for more kinds of questions

Date: 2026-10-30. Scope: vafer-research only, plus the suite items v0.0.5 needs before the brainstorm skill. The brainstorm skill itself is not designed here.

**Basis.**
- **Notes:** the six review notes in `notes/`: skill-audit, run-evidence, prior-research, external-sweep, hosts and stress-test.
- **Skill:** the skill at 5ebab1a.
- **Run:** the frozen v0.0.4 Yalova run folder (`.../e8210f42-.../scratchpad/t2/v04/.vafer/research/2026-10-29-yalova-tarihi/`) and the blind judge's verdict (`agent-afb4b61ca239b5b72`).
- **Prior studies:** the hyperresearch teardown and the 2026-10-28 architecture.
- **Probes:** six new offline probes on the frozen run, in `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/2b233dc9-15bf-498e-93c7-9a4c6367ee83/scratchpad/v005-review/dq/`: `probe_support.py`, `probe_share2.py`, `probe_pageonly.py`, `probe_ctx.py`, `probe_sizes.py` and `probe_firstsec.py`.

## Summary

- **The measured errors are verdict errors.** v0.0.4's measured accuracy problems are not transcription errors. Every error the judge found was a verdict:
  - two rejections of values nobody opened (4.80 m; "27 köy" called unsourced);
  - one "not found" (law 1533).

  The cheapest accuracy gain is a rule: open before you rule, and do not write "no source" for a value you never checked (Q1).
- **The check claims more than it checks.** New probe: of 261 figures in cited sentences, 170 sit in a quoted receipt span, 85 (33%) match only somewhere else on the cited page, and 6 do not match.
  - Two of the page-only matches are false confirmations. A derived "yüzde 85 artış" matched "85.39‰", a 1980 growth rate. A rejected "27 köy" matched "March 27" in a 930,000-character OCR book.
  - The three most number-dense cited snapshots (the Toynbee OCR, the Resmî Gazete issue and the TÜBA chapter) contain 467, 295 and 263 of the integers 0–999, so a short number matches there by chance.
  - Span-first matching and an honest status line fix this (Q2).
- **Outside Turkish history, the ladder picks wrong winners.** It treats vendor benchmarks, pilot trials and legislative proposals as top sources and has no "different definition" verdict. Four short adjustments fix this without scores (Q3).
- **The output is Turkish by construction.** The section names and status line are fixed in Turkish, and the checker silently checks nothing under "## Fuentes" (Q4).
- **The edit guard regressed.** Step 6 runs a bare `diff`, which in PowerShell "succeeds" on a damaging edit (Q5).
- **Copy-share triage does not work in Turkish.** Claim-level checking beyond numbers is the real gap against `/deep-research` and hyperresearch. New probe: 20 of 21 cited answer units copy under 20% of their wording from their pages (Turkish prose; two-thirds of those citations are to Turkish pages, so this is not only a translation effect). Use positional triage with receipt anchors (Q11), and add a verifier only if it proves its catches (Q18).
- **Several changes remove work.** Scout-first planning, dropping the editor, an `assemble` command and a running budget each cut serial minutes. Together with the quality changes they bring a Standard run from 22 minutes to an estimated 12–14 (about 2.5× bare). The project's bar is still 1.5×.

## What "far better than hyperresearch" should mean

A 0–10 judge score cannot be 5× better, and gaps of 0.5 are noise (run-evidence F8). Claim 5× only for error rates and costs that have a denominator. Count them on the same questions with the same instrument, and always report the number of supported claims next to them, because a report that makes fewer claims can game any error rate. "Works as well on more kinds of questions" means the same rates hold on English technical, medical, legal, numeric and list questions. Matching scores alone is not enough.

**Load-bearing unit:** a sentence of the opening answer, a row of the at-a-glance table, or a verdict in the disagreement table. This gives about 30 units per Standard report.

| Rate | Definition | Instrument (no harness) | v0.0.4, Yalova | v0.0.5 target | 5× against HR? |
|---|---|---|---|---|---|
| **R1** Unsupported load-bearing claims | Load-bearing units that the cited page does not support, per report, with the supported count | A judge opens the cited page for up to 15 units per report (the 10-29 protocol) | 2 wrong of about 12 judged (the 4.80 m and "27 köy" verdicts); no unsupported prose found | ≤1 per report, ≤5% | Yes, if HR light is run on the same question. HR samples its non-numeric checks, and its triage passes "5%" against "25%" |
| **R2** Overturned negative verdicts | Share of "not found", "no source" and rejected-B verdicts that a checker overturns within 5 minutes of searching | Judge | 3 of 17 (18%): 4.80 m, 27 köy, law 1533 | ≤1 of 17 (≤6%) | Candidate. HR's conflict verdicts never reach its writer (teardown §2) |
| **R3** Weakly checked figures | Figures matched only elsewhere on the page, unmatched or unchecked, over all figures | `vafer_check check` with span-first matching (Q2) | 91 of 261 (35%): 85 page-only, 6 unmatched | ≤10%, and no page-only quantities in load-bearing units | Not claimable: HR's figure triage was never measured |
| **R4** Coverage recall and spread | Share of answer-key items covered (15–40 binary items written before the runs), and the gap between two runs | Key and judge | Not measured | Recall ≥85%, spread ≤10 points | A floor, not 5× |
| **R5** List row recall | Rows found divided by rows in a frame key (lists of 20 or more) | Frame key | Never run | ≥90%; missing rows ≤1/5 of bare's | Candidate. HR light reads 15–25 sources in all |
| **R6** Follow-up cost on a reuse hit | Searches and minutes with the earlier run folder against an empty folder; accuracy within 0.5 | Logs | Never run | ≤1/5 of the searches, ≤1/3 of the minutes | Yes. HR has no corpus reuse, so a follow-up is a new 30–40 minute run |
| G1 (guardrail) Time against bare | Wall time divided by bare's | Logs | 4.4× | Report it; the standing bar is 1.5×, and this design reaches about 2.5× | Not a 5× axis |
| G2 (guardrail) Flag precision | Real flags divided by all flags | Hand labels | 1 of 13 (8%) | ≥50%, and ≥80% before any flag binds | No |

On Claude Code, report the same rates for `/deep-research`, which votes on quotes but never searches a second time (external-sweep F1; hosts F13). No arm other than VAFER has been measured with these instruments yet (prior-research F10).

## Capabilities a best-in-class deep-research skill needs

| # | Capability | v0.0.4 | Evidence |
|---|---|---|---|
| 1 | Scoping: reader, purpose, length, assumptions | partial | Questions only "if they would change what you search" (SKILL.md:33). The run's reader was assumed, and a technical workload is fixed silently (stress-test F1) |
| 2 | Rows from the question's atoms, each naming its settling record | has | SKILL.md:17, 41; the gap-finder lists atoms. But all 12 Yalova rows were `[prior]` because nothing was searched (skill-audit F10) |
| 3 | Shapes beyond narrative: comparison, computed, list, evidence review, legal | missing | Only a list variant, which contradicts step 1 and would break the 200-search cap (stress-test F4) |
| 4 | Search craft: multilingual, record-first, operators, extended mode, citation chasing | partial | Multilingual search is good (rule 2). There is no site:/filetype:, no route straight to the record, no chasing of a lead's references (skill-audit F18), and no extended mode (hosts F4) |
| 5 | Acquisition: HTML, PDF, tables, data portals, archives, scholarly indexes | partial | 12 of 63 fetches failed. Tables, hard-wrapped text and PDFs without pdftotext are rejected, so the 2025 population rests on an X post (skill-audit F7) |
| 6 | Evidence records with provenance | partial | Receipts carry span, URL, date and rung. Spans are never checked against snapshots, and `<URL>` receipts are dropped (skill-audit F4, F9) |
| 7 | Source evaluation by domain | partial | One history-shaped ladder: a vendor benchmark counts as primary, and a pilot trial ranks with a review (stress-test F10) |
| 8 | Freshness, versions and legal status | missing | Only as-of dates and "a later correction wins", which can promote a proposal (stress-test F5, F12) |
| 9 | Verdicts on conflicts and negative findings | partial | The ladder and adjudicator won the Rumi 1316 date, but no rule requires opening the losing side. That caused 3 of 17 overturned verdicts (skill-audit F15) |
| 10 | Counter-evidence for judgments | partial | Ultra only (SKILL.md:31, 44) |
| 11 | Figure checks: numbers, dates, quotes, equations, conversions | partial | Matches anywhere on the page, so 33% of matches are page-only (probe). Parentheses, %, 50M and dotted dates break it; 12 of 13 flags were noise |
| 12 | Claim-level support for prose: names, causes, comparisons, attribution | missing | Never checked (skill-audit F3). Self-written sentences fail 2.3–4.4× as often (external-sweep F8) |
| 13 | Certainty stated per conclusion | partial | Plain-words hedges with no rule (style.md rule 7) |
| 14 | Readable writing: answer first, short sentences, tables, translated quotes | has | Judge 8.5. Drafts averaged 12.3 words per sentence before the editor (run-evidence F7) |
| 15 | Length and structure control | missing | No total length: 2,858 words (about 12 minutes) against a five-minute reader (skill-audit F13) |
| 16 | Output in any language | partial | Turkish headings and status line. The checker knows only 6 Sources titles and splits sentences only in Latin, Greek and Cyrillic script (skill-audit F17) |
| 17 | Reuse and follow-ups | partial | Lookup and reuse.md exist but have never run. The lookup fails in PowerShell; a neighbouring question gets every old row; Quick saves nothing (stress-test F6, F8) |
| 18 | Effort control: parallel calls, budgets, stopping, stragglers | partial | A 6–10 search guide that was never measured. "There is no time limit". The gap wave waited 5 minutes for a straggler (run-evidence F2, F13) |
| 19 | Host robustness: Claude Code, Codex, Windows | partial | Modes A–D exist, but the bare `diff` regression, the PowerShell glob, Codex's cached search found too late and the fetch index race remain |
| 20 | Transparency of what was checked | partial | evidence.md and the host line exist, but "252/258" reads as 98% verified while 85 matches are page-only (probe; skill-audit F5) |

## Proposals, most important first

Effort: S is under a day, M is one to two days, L is longer. Word and line costs are against the hygiene caps in `tests/test_skill_hygiene.py`.

### Q1. Open before you rule; "not checked" is not "no source" (must, S)

- **Problem.** All of the judge's v0.0.4 errors were verdicts:
  - 4.80 m was rejected as "snippets, not opened", although the governor's office and the culture ministry both give it (conflicts.md C15).
  - "27 köy" was called unsourced, although the Wikipedia page S3 had opened cites Gingeras.
  - Law no. 1533 stayed NOT-FOUND after six queries. The 0.2 arm found it by searching a remembered number.

  The check flagged two of these sentences, and the lead dismissed both flags.
- **Evidence.** skill-audit F15; run-evidence F9 (a–c) and F10; judge notes; conflicts.md C12, C15; notes/s4.md "Not found: 1929 kanununun numarası".
- **Change.**
  - SKILL.md step 3, add: "Before ruling against a value, open the best page that states it, and follow a lead's footnote once. A value nobody opened is 'not checked', never 'unsourced'; its verdict stays 'not settled'."
  - SKILL.md step 1: put the values you expect (law numbers, names, dates, figures) into the rows as `[prior]` search terms.
  - briefs.md researcher rules, add: "Before you call a value wrong or unsourced, open the best page that gives it and follow a lead's reference once. In your conflict list, cite the page you opened for each side, or write 'B not opened'. Search a row's `[prior]` values as quoted terms."
  - briefs.md adjudicator brief: open the best source for each side before deciding.
  - style.md rule 8: the B cell carries `[n]` or "(not opened)". A verdict against an unopened B reads "not settled".
  - `vafer_check.py` gives such a cell a high-severity flag (Q2).
- **Expected effect.** It removes the error class behind 3 of the 17 negative verdicts (R2: from 18% to 6% or less), the class for which the judge docked accuracy and conflicts.
- **Cost.** One or two extra page opens per contested conflict, inside the researcher time already spent (8–12 opens per section). Wall time grows by 0–1 minute, only if the slowest researcher holds the conflict. Tool calls grow by 5–10 per run.
- **Risk.** Low, and no new stage. Chasing a lead is capped at once.
- **Verify.** Cheap first: give conflicts C12 and C15 from the frozen run to one adjudicator with the new brief (about 2 minutes). It should reach Gingeras and the 4.80 m pages. Then, on one fresh question, the judge counts overturned "not found" and rejected verdicts.

### Q2. An honest, quiet figure check: span first, receipts validated, gaps counted (must, M)

- **Problem.** The check matches a number anywhere on the cited page, trusts receipts without comparing them with snapshots, and leaves figures without evidence out of its denominator. Twelve of its thirteen flags were noise.
- **Evidence.**
  - The status line "252/258" reads as verified.
  - New probe (`probe_support.py`, `probe_pageonly.py`, `probe_ctx.py`, `probe_sizes.py`): of 261 figures in cited sentences, 170 are in a receipt span and 85 match only elsewhere on the page. Of those 85, 40 are years, 5 are small integers and 40 are other quantities. Most of those quantities are district-table cells whose rows were never saved as receipts.
  - False confirmations: "yüzde 85 artış" (correct by arithmetic, 311.635 / 168.593 = 1.848) matched "85.39‰" in the cited 2019 article. "27 köy" matched "March 27" in the Toynbee OCR.
  - The three most number-dense cited snapshots contain 26–47% of the integers 0–999. Toynbee's OCR alone is 929,736 characters long.
  - Notes: skill-audit F3–F6 and F9; run-evidence F10; stress-test F2, F5 and F11.
- **Change (`vafer_check.py`).**
  1. `load_receipts`: accept `<URL>` autolinks and inner quotes, and report unparsed receipt lines. A span counts only if `qnorm(span)` occurs in that URL's snapshot, when one exists. Spans marked unverified never match.
  2. `Checker.check_number`: match anchored spans first (Q11), then receipt spans for the cited URL, then the whole page. Count four outcomes: in span, page only, not found, unchecked. Severity of a page-only match:
     - medium for a quantity in a load-bearing unit, and for a percentage anywhere, since percentages are usually derived and belong in an equation;
     - low and listed without a disposition for year-like numbers (3–4 digits up to 2100, or a number before a century or month word) and for small integers.

     On the frozen run this rule gives 0 medium and 11 low page-only items in the first section, plus "yüzde 85" as one medium flag (`probe_firstsec.py`).
  3. Summary written to evidence.md: "N figures: S in quoted spans, P elsewhere on the page, F not found, U unchecked". The reply's status line shows "S of N figures in quoted passages · † k".
  4. Cut the noise:
     - Skip number matching in the disagreement table's B column (after `<!-- vafer:conflicts -->`) and in the unknowns list (after `<!-- vafer:unknowns -->`). Instead, flag any B cell without `[n]` as high severity (Q1).
     - Read Roman-numeral centuries (XVI. as 16. yüzyıl or 16th century).
     - Read k, M, bn, milyon and billion on results.
     - Accept percentage results (compare r, r/100 and r+100).
     - Treat ISO and dotted dates as one token.
     - Evaluate equations with parentheses through a restricted `ast` walker that replaces `evaluate()`.
     - Split before a digit that follows "]." (the "… [1]. 1923'te" merge).
  5. Only high- and medium-severity flags need a disposition.
- **Expected effect.**
  - On the frozen run, about 6 flags that need a disposition instead of 13: the Kibotos lead-only flag, four unopened B cells (two of them the judge's real errors) and the page-only "yüzde 85". Precision rises to 50–65% from 8%.
  - Dispositions take about one minute less.
  - The status line stops over-claiming, and researchers start saving the table rows they use as receipts.
- **Effort and budget.** About +90 net lines; the script is at its 700-line cap (see open questions).
- **Risk.** Researchers do a little more work (whole table rows as receipts). Page-only flags could become new noise, so they are medium only in load-bearing units and for percentages. No new stage.
- **Verify.** First an offline replay on the frozen run, without web access: compare the flags with the judge's findings. Add unit tests for 50M, %, ISO and dotted dates, parentheses, XVI. and `<URL>` receipts. Then one live run.

### Q3. One ladder, four domain adjustments, two conflict types, one scope rule (must, S)

- **Problem.** The ladder:
  - ranks a vendor's own benchmark as primary;
  - cannot tell a pilot study from a systematic review;
  - treats a legislative proposal like the law in force, and its "later correction wins" can promote that proposal.

  Conflicts have no "different definition" outcome, so a method dispute (net or gross wage, TÜİK or ENAG) gets a false winner. Nothing checks a figure's place, period and unit. That was the bare model's measured error: the toll for nine neighbourhoods given as the province's.
- **Evidence.** stress-test F1–F3, F5, F10, F12 and its harm ranking (#1); skill-audit F18; README results.
- **Change.** In the briefs.md researcher brief, replace the ladder line and "For {domain}, look first for: {record types}" with the ladder followed by these lines:
  > - An issuer's claims about its own performance or about rivals count as press until an independent source confirms them; its own specs, prices and terms stay primary.
  > - Health and science: guideline or systematic review > randomized trial > observational study > case report or opinion. Give design, size and follow-up with each effect.
  > - Law: label status (in force; applies from <date>; adopted; proposed; guidance). Only text in force answers what applies now.
  > - Changing facts (prices, versions, rankings, rules): record the source's own date or version; among equal rungs the newer record wins.
  > - A figure settles a row only when its place, period, unit and definition match the row; otherwise record it with its own scope.

  Further changes:
  - Conflict types gain "definition or scope" and "status or version". The adjudicator's verdicts gain "both, by definition".
  - SKILL.md keeps one ladder and points to briefs.md (step 3 and rule 5), saving about 60 words.
  - style.md: state each definition where the report uses it, and let the date line name the oldest as-of date of any changing fact.
- **Expected effect.** Correct winners in stress-test scenarios 1–3 and 5, where today "biased headlines pass every check". It also guards against the bare model's scope error. Speed is unchanged.
- **Effort and budget.** briefs.md grows by about 120 words; SKILL.md shrinks by about 60. Q8 and Q10 pay for it.
- **Risk.** Low. The rules mostly do not trigger on history questions.
- **Verify.** One run on the intermittent-fasting question (T2D remission) or the EU AI Act question. The judge checks how vendor claims, pilot trials and proposals were ranked, and whether definition conflicts read "both, by definition".

### Q4. A report and a checker that work in any language; remove the Yalova text (must, S–M)

- **Problem.**
  - "Bir bakışta", "Ayrışan kaynaklar", "Bilinmeyenler" and the status line are fixed in Turkish, even for English questions.
  - The checker finds Sources under six titles only: "## Fuentes" makes every citation dangling and checks 0 figures.
  - Sentence splitting needs a Latin, Greek or Cyrillic capital letter.
  - The leak check flags the English word "researcher".
  - style.md's Yalova example primed the tested run (report.md:5 nearly copies style.md:26), and SKILL.md:80 greps "yalova".
- **Evidence.** skill-audit F17; stress-test F3 and F13; run-evidence F14; vafer_check.py:35, 37–38, 48, 57–58.
- **Change.**
  - SKILL.md step 5: "Write report.md in the reader's language, in this order, naming each part in that language:
    - the answer (5–8 sentences);
    - an at-a-glance table;
    - the body sections;
    - where sources disagree (topic | A | B | verdict | why), after `<!-- vafer:conflicts -->`;
    - what is not known, after `<!-- vafer:unknowns -->`;
    - sources."
  - SKILL.md step 7: the status line is in the reader's language.
  - style.md: names by function instead of the Turkish labels, and one neutral before-and-after pair on a topic other than Turkish history. An English health source written up in Turkish would also show the quote rule.
  - `vafer_check.py`:
    - find Sources by structure: the last heading followed mostly by `[n] … URL` lines;
    - find the check and source-mix lines by a fixed ASCII key;
    - add `。！？؟` as sentence ends;
    - run the leak check on internal tokens only;
    - skip the date line under the title.
  - SKILL.md:80: a neutral lookup example.
- **Expected effect.** Checks work on reports in any language, and English reports raise no false leak flags. Future side-by-sides are no longer primed by the skill's own text. The script loses its title vocabularies.
- **Risk.** Markers are invisible in rendered Markdown but visible in plain text. Low.
- **Verify.**
  - Unit tests with Spanish, German and Japanese Sources headings and sentences.
  - One English run (the technical comparison) shows English section names and no leak flags.

### Q5. Restore the edit guard and fix the host breaks that drop checks silently (must, S)

- **Problem.** Since a927973, step 6 runs a bare `diff`. In PowerShell 5.1 that is `Compare-Object`, which "succeeds" on an edit that changed 2.324,70 to 2.342,70 and dropped `[1]`. On the same edit, `vafer_check.py diff` reports 4 problems. Further breaks:
  - The script examples are relative paths, and `python3` is never offered.
  - The reuse lookup fails in PowerShell (os error 123).
  - Codex's cached search mode is discovered too late for recent topics.
- **Evidence.** skill-audit F1, F2; stress-test F6, F7, F9; hosts F7.
- **Change.**
  - Step 6 runs `<python> <skill folder>/scripts/vafer_check.py diff <run>/draft.md <run>/report.md`. The name draft.md also avoids the harness's refusal of names that start with "report".
  - The Checking section gives one canonical command. The lead resolves the absolute script path and the interpreter (`python`, `python3` or `py -3`) once and pastes both into every brief.
  - The lookup becomes `rg -i -l --glob plan.md "<ascii term>" .vafer/research`.
  - hosts.md, Codex: before planning a recent or changing topic, run one dated query. If the results look cached, say so in the first reply line and the host line, and suggest `-c web_search="live"`.
- **Expected effect.** No silent fact loss after edits, a reuse lookup that works on Windows and Codex, and fewer stale answers on Codex. Speed is unchanged.
- **Verify.**
  - Run both diff commands and the lookup in PowerShell and Git Bash on a two-file probe.
  - Run one Codex Quick question on a dated topic.

### Q6. Scout first, so gap-finder items become wave-1 rows (must, S)

- **Problem.** The plan is written without searching, so all 12 rows were `[prior]`. The gap-finder named Kibotos 1096, 1915 and the 1923 exchange in 50 seconds. Its items still waited for the slowest researcher and became a serial wave (12:04:40–12:10:22). The list variant needs a searched frame that step 1 forbids. On Codex, 5 researchers plus the gap-finder already fill the 6-thread cap.
- **Evidence.** skill-audit F10; run-evidence F1, F2; prior-research F5; stress-test F4; hosts F3.
- **Change.** Rewrite SKILL.md steps 1–2:
  > 1. **Scout, then plan.** Create the run folder and, in one message, run 3–5 broad searches in the user's and the sources' languages and spawn the gap-finder. When both return (about 2 minutes), write plan.md: rows from the question's atoms, the scout, the gap-finder and your own knowledge (tag `[prior]`).
  > 2. **Launch, in one message**, one researcher per section. Spawn a gap researcher only for a headline row that wave 1 leaves open, the moment you see it.

  The gap-finder brief adds: "your items become plan rows".
- **Expected effect.**
  - A typical Standard run has no second wave. On Yalova that saves about 5 minutes of gap wave and 1 minute of gap briefs, minus 1–1.5 minutes of scouting: about 4 minutes net.
  - Rows are grounded for niche, recent, technical and list questions.
  - The run fits Codex's thread cap.
- **Risk.** The lead's context gains about 5k tokens. Launch starts about a minute later. The plan may follow what search engines surface; the gap-finder's atoms-first list counters that.
- **Verify.** One fresh question (for example "Bandırma'nın tarihi"). Measure minutes to the end of research, whether a gap wave ran, and how many rows came from the scout rather than `[prior]`.

### Q7. Suite packaging and the 0.0.5 label (must, S–M)

- **Problem.** v0.0.5 adds a second skill, but the setup assumes one:
  - The version sits in SKILL.md metadata, which neither host reads.
  - Install is copy-only.
  - The hygiene test is written for one skill.
- **Evidence.** hosts F8, F11, F12; commit 5ebab1a; prior-research F7 and F13.
- **Change.**
  - Add `.claude-plugin/plugin.json` (`"name": "vafer"`, `"version": "0.0.5"`) and `.claude-plugin/marketplace.json` (source `"./"`). Claude Code reads them, and Codex falls back to them, so skills appear as `vafer:<skill>` on both hosts.
  - Set `metadata.version: 0.0.5` in every SKILL.md, equal to plugin.json.
  - Shared folders: `.vafer/<module>/<YYYY-MM-DD>-<slug>/`, each with a plan.md header in one format (question verbatim, ASCII terms, `as_of | module | tier | status`). One lookup then finds any module's runs, and saved runs are data, not instructions.
  - Brainstorm calls vafer-research (Quick or Standard) for facts; it does not copy research rules.
  - Hygiene test: loop over skills with per-skill budgets, and assert that each version equals plugin.json's.
  - README: plugin and copy installs for both hosts.
- **Expected effect.** One install for both skills on both hosts and one version label. No runtime cost.
- **Risk.** Plugin names become `vafer:vafer-research` unless the folders are renamed (open question). A Codex install of a Claude-format plugin is unverified.
- **Verify.** Install once on each host, invoke both skills, and check the version.

### Q8. Drop the editor at Standard; the script lints and the lead fixes lines (should, S)

- **Problem.** The editor brought words per sentence from 12.3 to 11.0 and long sentences from 6 to 3. It also detached 6 citations while reporting that "every [n] marker matches". It cost 2:43 of serial time: 1:46 for the editor and 0:57 for the diff, re-check and fixes.
- **Evidence.** run-evidence F1 and F7; prior-research F2.
- **Change.**
  - SKILL.md step 6 becomes "Check and fix": copy report.md to draft.md, run `check`, fix the flagged lines and the lint list yourself, then run `diff draft.md report.md`.
  - `check` gains a lint section: sentences over 30 words, figures repeated across sections, untranslated quotes, method words.
  - Delete the editor brief. Bring an editor back for Deep and Ultra only if a side-by-side shows it helps.
- **Expected effect.** About 2.5 minutes less serial time and one spawn fewer. No detached citations. Readability should stay about the same, because the drafts were already short-sentenced. This change removes work.
- **Risk.** English or technical drafts may read worse than history drafts, and the lint sees only mechanics.
- **Verify.** One question, with and without the editor. Compare words per sentence, long sentences, detached citations and blind readability.

### Q9. `vafer_check.py assemble`: the script does the chores the lead improvised (should, M)

- **Problem.** The lead's improvised chores:
  - It re-typed the 25k-character report twice.
  - It renumbered 36 sources with an improvised script and a hand-typed URL-to-title map.
  - It wrote `fix1.py` and `dispo.py`.

  Its context grew from 44k to about 210k tokens, and assembly took 4:36.
- **Evidence.** skill-audit F11; run-evidence F1 and F6.
- **Change.** A new `assemble <run>` command:
  - concatenates sections/*.md in plan order into draft.md;
  - turns `[URL]` citations into `[n]`;
  - builds Sources with titles from each snapshot's `<title>` or the notes' source line;
  - keeps receipt anchors (Q11);
  - leaves marked slots for the answer, the at-a-glance table, the disagreements and the unknowns, which the lead writes.

  SKILL.md step 5 and the brief's "the lead renumbers" shrink accordingly.
- **Expected effect.** Two to three minutes less lead time, a much smaller lead context, and no hand-typed title maps. This change removes work.
- **Risk.** Drafts must keep the `[URL]` format, and the script must handle missing sections.
- **Verify.** Run `assemble` on the frozen run's sections and compare with report.before-edit.md. In the next live run, time the span from the last researcher's return to delivery.

### Q10. Question shapes: comparison, computed, list, evidence, legal (should, M)

- **Problem.** Read literally, v0.0.4 is a pipeline for history questions:
  - In a comparison, each researcher gathers different metrics and the workload is fixed silently.
  - A computed answer needs inputs from several sections.
  - The list variant contradicts step 1 and would exceed the 200-search cap.
  - Medical reviews lack design, size and harms.
  - Legal answers need branches by role and date.
- **Evidence.** stress-test F1–F5 and F13; prior-research F12; architecture pillar 4.
- **Change.** A new `references/shapes.md` (at most 600 words). It is read only when plan.md says `shape: comparison | computed | list | evidence | legal`; the default is narrative.
  - **comparison:** one frame (items × attributes, unit, as-of) shared by every brief. A stated profile (workload, budget, region) is asked once in interactive sessions or stated as an assumption in the first sentence.
  - **computed:** researchers return inputs with period, unit and definition. The lead computes each derived figure as an equation with cited inputs and adds one definitions paragraph.
  - **list:** the scout builds the frame from the enumerating record plus one independent route, ranked by size. Researchers get batches of rows with about 2 searches per row and at most 20 per researcher. Each cell holds a value with its receipt, "not found (queries)" or "n/a". A closing pass uses an unused route. `table.csv` sits beside report.md, and the report states "N of M items (source of M)".
  - **evidence:** rows are outcomes and harms. Each effect comes with design, size, follow-up and effect size, plus a certainty word. A harms row is required, and scope sits next to any recommendation.
  - **legal:** a role × obligation × date table, status labels, and a "what may change" line for proposals.

  Move the table variant and the tariff example out of briefs.md into shapes.md.
- **Expected effect.** Removes the contradictions in five of the eight stress-test scenarios, keeps list runs inside the search cap, and gives lists a CSV.
- **Risk.** A fifth reference file (the cap is 4) and one more choice at planning. Cap the file at 600 words to keep it from growing.
- **Verify.**
  - One list question with a frame key: row recall, with searches under 150.
  - One computed question: equations recomputed by `check`.

### Q11. Receipt anchors and a span-first support pack for load-bearing units (should, M)

- **Problem.** Prose claims go unchecked:
  - Names, causes and comparisons are never checked, and a wrong attribution on a long page passes.
  - Paraphrased and translated sentences are the riskiest: unsupported 2.3–4.4× as often as copied ones.
  - Copy share cannot pick them out in a Turkish report. New probe (`probe_share2.py`): 20 of 21 cited answer units copy under 20% of their wording from their pages, even with stemmed 3-word matching, and two-thirds of those citations point to Turkish pages.

  Receipts also lack a stated purpose (skill-audit F12) unless the check uses them. hyperresearch samples non-numeric checks, and `/deep-research` votes on quotes.
- **Evidence.** skill-audit F3 and F12; external-sweep F8–F10 and F15; stress-test F5.
- **Change.**
  - **Notes.** One source line per URL, `S2: <URL> (opened <date>; rung; source date or version)`, and receipts written as `R2.4 [S2] <fact> — "<span>"`. A table row with its header is one span.
  - **Drafts.** Each factual sentence ends with `[URL]<!--R2.4-->`. `assemble` and `diff` keep the comments.
  - **`check`.** Numbers and quotes match anchored spans first (Q2). For each load-bearing unit, `check` writes `support.md`: the unit, its anchored spans (at most 2), or the best BM25 passage (at most 60 words) from the cited snapshots when it has no anchor, plus its figure status. A load-bearing unit with no anchor and no passage containing its key terms gets a medium flag.
  - **Optional `passages <run> <url> <terms>`.** It returns ranked passages and replaces some of the 98 grep and sed reads.
  - **Codex.** Without snapshots, anchors use the receipts copied from line windows.
- **Expected effect.**
  - Misattribution and unanchored load-bearing claims surface.
  - R1 becomes countable.
  - Receipts get a job.
  - Fewer shell reads.

  Speed is neutral to slightly slower for researchers (they write IDs) and faster for the lead.
- **Effort.** About 80–100 lines.
- **Risk.** Researchers write more. Anchors lost in hand edits show up in `diff`.
- **Verify.** In the next live run, count load-bearing units with anchors, page-only quantities among them, and how many support.md entries a person judges unsupported.

### Q12. Acquisition: tables, PDFs, 429s, archives, data portals and scholarly routes (should, M)

- **Problem.** 12 of 63 fetches failed, mostly on official and scholarly hosts:
  - The "boilerplate" rule rejected the Gutenberg Cmd. 1478 text, the archive.org Toynbee OCR, a 25-row statistics table and hard-wrapped prose.
  - PDFs without pdftotext are discarded.
  - HTTP 429 (rate-limit) errors get no backoff.
  - TÜİK's table was unreachable, so the 2025 population rests on an X post.
  - The parallel index lost 14 rows.
  - Search guidance has no route straight to the record, no operators, no extended mode and no citation chasing.
- **Evidence.** skill-audit F7, F8 and F18; run-evidence F4 and F5; hosts F4 and F5; external-sweep F7.
- **Change.**
  - **`fetch`:**
    - Judge content by characters outside short link-like lines, counting table rows and CSV or JSON lines as content.
    - Keep an unconverted PDF as `pages/<hash>.pdf` with status `pdf-saved`, and tell the agent to read it with the host's PDF reader (Read with pages on Claude Code) and mark spans "pdf".
    - On 429 or 503, wait (Retry-After, or 5 seconds) and retry once, sending one request per host at a time.
    - Download different hosts in parallel.
    - On 404, 410 or an empty or script-only page, try `https://web.archive.org/web/2026id_/<url>` once, with status `archived <timestamp>`.
    - Write each status into the snapshot header, and append index lines under a lock file.
  - **briefs.md, one line:** "Go to the record first: the issuer's site (site:), its data portal or official gazette, a scholarly index (DergiPark, PubMed or Europe PMC, arXiv, the DOI page), filetype:pdf for reports. Follow the best secondary source's references once. On Claude Code, use WebSearch's extended mode when results are thin, local, recent or non-English."
- **Expected effect.** Fewer † marks and unverified primary sources, more official statistics actually opened, and the index race fixed.
- **Speed and cost.** Parallel downloads save time. Wayback adds one request per failure, and extended searches cost more per call.
- **Risk.** Wayback copies can be stale; the timestamp travels with them. How extended mode counts against the quota is unverified.
- **Verify.** Re-fetch the run's 12 failed URLs plus 5 PDFs and CSVs and count the recoveries. In the next run, count † marks and unverified receipts.

### Q13. Length from the reader's purpose (should, S)

- **Problem.** style.md promises a five-minute read, but nothing sets the total length. With 3–6 sections of up to 600 words, plus gap sections, the report reached 2,858 words (about 12 minutes). Researchers spent 49–69% of their wall time generating text, and longer reports do not score better within the deep-research tier.
- **Evidence.** skill-audit F13; run-evidence F3; external-sweep F13.
- **Change.**
  - The plan.md header records `reader | purpose | length`.
  - Defaults: Quick at most 300 words; Standard body at most 1,500 words (about 6–7 minutes) plus tables; Deep at most 3,000. An explicit request ("detaylı", "short") wins.
  - Each brief gets the section's share of the budget (typically 250–350 words) instead of 600.
  - `check` prints body words against the target.
- **Expected effect.** Shorter, more focused reports, and 1–2 minutes less researcher generation per wave.
- **Risk.** A judge may score coverage lower. Long tables move to a CSV or an appendix.
- **Verify.** A blind, length-matched pair on one question, with words and reading minutes recorded.

### Q14. Certainty in plain words, and counter-evidence for judgment rows (should, S)

- **Problem.** Hedges ("kesin değil", "muhtemelen") follow no rule. Counter-evidence is searched only in Ultra, yet medical, legal and technical answers turn on judgments: causes, comparisons and recommendations.
- **Evidence.** teardown §5 item 7; stress-test F3 and F5; SKILL.md:31 and 44.
- **Change.**
  - style.md rule 7: give each headline conclusion one certainty word in the reader's language:
    - firm: a primary record, or two independent official or scholarly sources that agree;
    - likely: one good source and no conflict;
    - uncertain: leads only, an unresolved conflict, or inference.
  - Plan rows that state a judgment are tagged `judgment`. Their researcher runs one search for the strongest counter-evidence, records the hit or the miss, and the report states the strongest counter-point beside the verdict. Ultra keeps one search per conclusion.
- **Expected effect.** Clear confidence for readers and better conflict handling on contested questions.
- **Cost.** One to three more searches per run.
- **Risk.** Labels nobody reads are ceremony. Here the reader reads them; keep them to three words and no numbers.
- **Verify.** On the medical question, every conclusion carries a certainty word and a counter-point; the judge scores conflict handling.

### Q15. Reuse that pays on follow-ups (should, S–M)

- **Problem.** Reuse has never run, and it has several gaps:
  - The lookup fails in PowerShell.
  - reuse.md seeds every earlier row even for a neighbouring question, which would put 15 history rows into a question about the economics of 1999.
  - The header lacks the `check` field that reuse.md expects.
  - Quick saves nothing, so "go deeper" starts from zero.
  - Borrowed figures get no scope check.
- **Evidence.** stress-test F6 and F8; prior-research F10; external-sweep F16.
- **Change.** reuse.md gets two modes:
  - **Refresh** (the same question): seed the rows, re-open changing facts, recompute derived figures, and open with "answer unchanged" or "answer changed".
  - **Borrow** (a neighbouring question): write a fresh plan, and import as dated leads only the receipts and dead ends whose place, period and unit match a row.

  Also:
  - Quick writes plan.md and notes for the pages it opened.
  - Drop the `check` field from reuse.md.
  - Use the lookup from Q5.
- **Expected effect.** Half or fewer of the searches on a hit (target R6: at most a fifth of a fresh run's), and deeper runs that start with sources.
- **Risk.** Stale borrowed facts. Their dates and the re-open rule limit this.
- **Verify.** A next-day follow-up on a fresh run folder against an empty folder: searches, minutes, accuracy.

### Q16. A running budget and evidence-based stopping (should, S)

- **Problem.** "There is no time limit", and the 6–10 search guide was never measured. Researcher searches ranged from 4 to 17, and gap researchers made 38–46 tool calls. Wall time follows the slowest researcher: in the first live run, R4 alone took 10:22.
- **Evidence.** run-evidence F3 and F13; prior-research F2 and F4; external-sweep F2–F4.
- **Change.**
  - briefs.md rules: "Send 3–5 searches in your first message and batch opens in each later turn. Keep a tally in your notes (searches 6/10 · opens 7/12). A row closes when its settling record, or two independent records, are in hand. Stop a row after a batch that adds no new fact or URL, and list the queries tried. Spend extra searches only on an open headline row."
  - SKILL.md: replace "There is no time limit" with "Effort follows the budget in the brief; Ultra may extend it."
- **Expected effect.** 20–40% fewer searches at similar accuracy (external evidence from one paper each) and less spread between researchers. This change removes work.
- **Risk.** Hard rows may stop early; the headline-row exception covers them.
- **Verify.** In the next run, compare searches, tool calls and researcher durations with v0.0.4's.

### Q17. A one-page scorecard of rates, not a harness (should, S)

- **Problem.** "5×" holds only as a rate, and none has been measured against another arm. Holistic scores move with the judge and a single run. On Claude Code the real baseline is `/deep-research`.
- **Evidence.** prior-research F8, F10 and F11; external-sweep F1 and F9; critique-redteam §1.
- **Change.** One page (`docs/scorecard.md` or a README section) holds:
  - rates R1–R6 and both guardrails;
  - the 10-29 judge protocol (open every cited page, for up to 15 load-bearing units per report);
  - answer keys written before the runs (15–40 binary items, 3–5 of them negative);
  - the arms: v0.0.5, v0.0.4 and bare; `/deep-research` once per question; HR light once if approved.

  No code. Write an `audit` wrapper (fetch any report's cited URLs and run `check`) only if counting by hand proves too slow.
- **Expected effect.** v0.0.5 claims rest on counted rates with a denominator.
- **Risk.** It could turn into evaluation infrastructure; keep it to one page and hand counts.
- **Verify.** Apply it to the first v0.0.5 side-by-side.

### Q18. A bounded support verifier for load-bearing units, gated (could, M)

- **Problem.** No script can judge whether a paraphrase or translation keeps the source's meaning. `/deep-research` uses three skeptics per claim. The architecture held a verifier back because the Opus 5 guide warns against verify subagents.
- **Evidence.** external-sweep F1, F6, F8 and F9; architecture "held"; teardown §5 item 2.
- **Change.**
  - After `check`, one fresh subagent reads support.md only and labels at most 15 units: supported, partial (with the fix), unsupported or wrong-source. It takes them in this order: page-only figures, units without figures, verdicts.
  - Its strictness is fixed in the brief: "supported only if the passage says it; a faithful translation counts; inference counts only if the report marks it".
  - It runs while the lead fixes flags.
  - Ship it only if two side-by-sides show at least one real catch per report that the script missed.
- **Cost.** One spawn and 1–2 minutes, mostly in parallel.
- **Risk.** It is exactly the ceremony that sank v0.0.3 if it never catches anything; hence the gate.
- **Verify.** Run it on two reports (one Turkish, one English); a person checks every "unsupported" label.

### Q19. A calendar converter in the script (could, S)

- **Problem.** "A calendar check beats any source", yet the model converts Hijri and Rumi dates in its head. The check then flags the conversions, and the lead closes them as "derived".
- **Evidence.** skill-audit F16; run-evidence F11; check.md F5, F8 and F9.
- **Change.** `vafer_check.py convert hijri|rumi <year>[-<month>-<day>]` prints the Gregorian range. It uses the tabular Hijri calendar, and treats Rumi as the Julian-based year that starts on 1 March, with the 13-day offset. Researchers save the output as a derived receipt that `check` accepts.
- **Expected effect.** The ladder's top rung rests on code, and 3 of the 13 Yalova flags disappear.
- **Effort.** About 35 lines.
- **Risk.** Calendar edge cases, such as the 1917 reform.
- **Verify.** Unit tests: Rumi 1316 starts on 14 March 1900, and 1 Muharram 1316 is 22 May 1898.

## Where these proposals cost time and tool calls

| Adds | Removes |
|---|---|
| Q1: 5–10 page opens per run; 0–1 minute | Q6: the serial gap wave, about 4 minutes net |
| Q6: about 1 minute before launch; 3–5 lead searches | Q8: the editor and its re-check, about 2.5 minutes and 1 spawn |
| Q11: receipt IDs in researcher output | Q9: lead assembly chores, 2–3 minutes and most of the lead's context growth |
| Q12: one Wayback request per failure; extended searches cost more | Q16: 20–40% of searches |
| Q14: 1–3 counter-evidence searches | Q2: about 7 needless dispositions |
| Q18 (gated): 1 spawn and 1–2 minutes, mostly parallel | Q13: shorter sections, less researcher generation time |

Estimated Standard run time: on the Yalova timeline, 22:53 becomes about 12–14 minutes (scout 2:15, briefs 0:45, one wave about 5:00, conflicts 0:30, assembly 2:00, check 0:45, fixes 0:30, delivery 0:30). That is about 2.5× bare, still above the project's 1.5× bar.

## Cuts

1. **The editor pass and its brief at Standard.** It detached 6 citations for a 1.3-word drop in sentence length, at 2:43 serial (run-evidence F7).
2. **"Paste the short rules from style.md" in every brief.** Researchers read style.md themselves. The lead hand-wrote 77k characters of briefs (skill-audit F11).
3. **Fixed Turkish headings, table header and status line, plus the Yalova example and `yalova` lookup.** They break other languages and primed the tested run (skill-audit F17).
4. **The match ratio in the reply's status line.** Its 252/258 reads as verification while 85 matches are page-only. Honest counts go to evidence.md (Q2).
5. **The second copy of the source ladder in SKILL.md** (step 3 and rule 5). One copy stays in the brief, which the researchers read.
6. **"There is no time limit."** Replaced by a running budget (Q16).
7. **WebFetch as the default skimmer when the shell works.** 25 of 34 WebFetched pages were also snapshotted (run-evidence F4). Snapshot first; use WebFetch only for pages the fetcher cannot read.
8. **The table variant and the tariff example in briefs.md.** They move to shapes.md (Q10).
9. **Deep's second gap wave and "up to 10 researchers".** These contradict the 3–6 sections, and scouting first makes the wave rare. Run a second wave only for an open headline row.
10. **The script's title, check-line and leak vocabularies.** Structural markers replace them (Q4).
11. **Dispositions for low-severity flags.** They trained the lead to rubber-stamp (skill-audit F6).
12. **The rung label on every receipt line.** One source line per URL carries it (Q11).
13. **"Older VAFER folders" in hosts.md.** About 45 words for folders only the author has. Keep one line.

## Budget ledger (estimates)

| Item | Now / cap | After | Note |
|---|---|---|---|
| SKILL.md body | 1,431 / 1,500 words | about 1,375 | Q1, Q5, Q6, Q10, Q11, Q13–Q15 add; Q3, Q8, Q9, the trimmed Checking and Writing paragraphs cut |
| Words before the loop | 374 / 400 | about 370 | |
| briefs.md | 927 / 1,000 | about 890 | Q1, Q3, Q11, Q12, Q14, Q16 add; the editor, table variant, tariff example and paste rule are cut |
| style.md, hosts.md, reuse.md | 437, 619, 318 / 1,000 | about 500, 630, 400 | |
| Reference files | 4 / 4 | 5 | shapes.md, read only for non-narrative shapes |
| vafer_check.py | 700 / 700 lines | about 1,000 | The model does not load script code into context once SKILL.md states the formats the lead had to read from source; a larger script is code, not ceremony |

## A side-by-side that fits the "product first" rule

1. **Offline, no web (minutes):**
   - replay Q2, Q4 and Q19 on the frozen Yalova run;
   - run one adjudicator on C12 and C15 for Q1;
   - re-fetch the 12 failed URLs for Q12.
2. **After the musts, one fresh Turkish-local question** (not Yalova). Arms: v0.0.5, v0.0.4 and bare, with the lead in a main session (skill-audit F20). Count R1–R3, G1 and G2.
3. **After the shoulds:**
   - one English technical comparison, with v0.0.5, bare and `/deep-research`;
   - one of the medical, computed or list questions;
   - one next-day follow-up on step 2's run folder (R6).

   Score every arm with the one-page scorecard (Q17), and run each VAFER arm twice before claiming a gain between versions (prior-research F8).

## Open questions for the brainstorm

1. Which 5× do you want to claim first: fewer unsupported load-bearing claims, cheaper follow-ups or complete lists? Will you pay for its denominator? Each HR light run takes 30–40 minutes, and nobody has run one. On Claude Code, `/deep-research` is the bar.
2. What should a Standard report be for you: about 1,500 words (6–7 minutes) by default, with "detaylı" lifting it? Do you want a CSV or an appendix for long tables?
3. After Turkish history, which question types matter most to you: technical comparisons, health, law, numbers or lists? Each needs one shape and one test question in v0.0.5.
4. Is one bounded verifier subagent acceptable (one spawn, 1–2 minutes) if it catches unsupported prose the script cannot? Or should checks stay script-only, with the open-before-ruling rule carrying accuracy?
5. May the script grow to about 1,000 lines and the references to 5 files, or must every addition be paid for with cuts?
6. Plugin naming: rename the folders so skills show as `vafer:research` and `vafer:brainstorm`, or keep `vafer-research` and `vafer-brainstorm` so copy installs and Codex's `$vafer-research` keep working?
