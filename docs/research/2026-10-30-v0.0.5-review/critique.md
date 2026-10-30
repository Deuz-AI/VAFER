# v0.0.5 change list: adversarial review

Date: 2026-10-30. Role: adversarial reviewer of the two designers' proposals (speed lens SPD-1 to SPD-13, quality lens Q1 to Q19).

Inputs:
- The six notes in `notes/`, `design-speed.md` and `design-quality.md`.
- The skill at 5ebab1a: SKILL.md, the four references and `vafer_check.py`.
- The frozen v0.0.4 Yalova run folder (`.../e8210f42-.../scratchpad/t2/v04/.vafer/research/2026-10-29-yalova-tarihi/`) and the lead's transcript (`agent-ab569b7fdce2cbf4b`).
- The designers' probes, which I re-ran.

I did not trust the designers' summaries. I re-ran the key probes and added two of my own. My probes are in `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/2b233dc9-15bf-498e-93c7-9a4c6367ee83/scratchpad/v005-review/critic/`: `receipt_probe.py` and `index_probe.py`.

## Bottom line

v0.0.5 should remove steps rather than add features:
- one research wave, with the gap-finder's items folded in;
- a follow-up agent spawned as soon as a reply needs one;
- the script assembles the report;
- no editor pass, no gap wave and no improvised chores.

The one quality change with direct evidence is "open before you rule". Every error the judge found in v0.0.4 was a rejection or a "not found" that rested on a page nobody opened. The disagreement table has four B cells without a citation, and two of them are the judge's errors. So the rule, plus a high-severity flag on such cells, is a must.

The other musts are:
- a quieter, honest check;
- skill text with no Yalova priming and no fixed Turkish headings;
- the host fixes;
- researcher batching.

Changes that add stages or formats wait for a measured failure: receipt anchors, the support verifier, certainty labels and a shapes file.

Expected result for a question the size of Yalova: about 10–13 minutes and 7–8 subagents, which is about 2–2.5× the bare model, not 1.5×. Verify with cheap offline checks first. Then run one side-by-side on a fresh Turkish-local question, with the lead in a main session. The "5×" rate and the brainstorm skill come after that.

## What I verified myself

| Claim | Result | How |
|---|---|---|
| The lead waited by choice (SPD-4) | **Confirmed.** 08:59:49Z: "I'll decide on a gap wave once the sections come back." 09:03:33Z: "Waiting on section 1; then I'll send the gap wave and the adjudicator together." Spawns followed at 09:04:25–09:05:11. | Lead transcript |
| Codex `wait_agent` returns the first of several agents (SPD-4) | **Confirmed.** "Pass multiple ids to wait for whichever finishes first." | `multi_agents_spec.rs:896` |
| The judge's errors sit in unopened B cells (Q1, Q2) | **Confirmed, and sharper than claimed.** 4 of the 10 conflict rows have a B cell without `[n]`: "27 köy (derlemeler)", "4,80 metre (yaygın anlatı)", "Bir kanun (bazı derlemeler)" and "2.501 ölü, 4.472 yaralı (yabancı derlemeler)". Two of them are the judge's errors. conflicts.md C15 says "not opened". | report.md:167–180 |
| Researchers take one small step per turn (SPD-5) | **Confirmed.** 20–35 turns each, 1.08–1.52 calls per turn, 79% single-call turns overall. **Caveat:** the straggler S1 (6:04) was tool-bound, with only 35% generation, an 82 s fetch and a 75 s WebFetch. Batching therefore helps the other researchers more than the one that set the wave's end. | `speed_turns.py`, re-run |
| Drafts already read short (SPD-2, Q8) | **Confirmed for sentence length.** Drafts run 9.5–12.9 words per sentence, the lead's rewrite 12.3, the editor's version 11.0. **Not shown for structure:** the concatenation probe has 3,708 words and 28 headings, against 2,866 and 13 in the delivered report, and puts the prehistory gap section at the end. | `readab.py`, re-run on `asm_probe/run/report.md` |
| Concatenation floods the check (SPD-3) | **Confirmed.** 55 flags. Of 39 uncited items, 21 can borrow a citation from the same paragraph or table: 14 then match, and 7 become mismatches, including the 4,80 m value and the 2000 census figure. 18 have no citation nearby. | `inherit_probe.py`, re-run |
| 85 of 261 figures match only elsewhere on the page (Q2) | **Confirmed.** Most are district-table cells whose rows were never saved as receipts. In the first section the page-only rule raises 0 medium and 11 low flags. Its single medium flag elsewhere is "yüzde 85", which is correct by arithmetic. So page-only flags would have found **no real error** in this run. | `probe_support.py`, `probe_pageonly.py`, `probe_firstsec.py` |
| Receipts are never checked against snapshots (skill-audit F4, Q2.1) | **New finding.** Of 157 parsed receipts that have a snapshot, 139 match exactly, 2 match after whitespace folding and 14 (9%) do not match. Most of the misses come from **`pdftotext -layout` interleaving two-column PDFs**. For example, the "5 meters" receipt that decided C15 sits split across two columns in snapshot `7ad7e81ae2c3`. Another 9 receipt-like lines were silently not parsed. | my `receipt_probe.py` |
| The index race makes failed pages count (SPD-8, Q12) | **Real but harmless here.** 14 index rows were lost. 13 of those pages would be "ok" if fetched again. The 14th, the 930k-character Toynbee OCR book, would be "boilerplate", and that label is itself wrong for it. The race let correct content in by accident. | my `index_probe.py` |

## Ranking

Must is limited to 8. Each item below gives its merged sources, verdict, priority and effort.

| # | Change | From | Verdict | Priority | Effort |
|---|---|---|---|---|---|
| 1 | Open before you rule: "not checked" is never "no source" | Q1, SPD-4, SPD-3(4), Q2(4) | keep | must | S |
| 2 | One launch: gap-finder first, its items become rows | SPD-1, Q6 | modify | must | S |
| 3 | Act on each reply: capped follow-ups replace the gap wave and batched adjudication | SPD-4, Q6(step 2) | keep | must | S |
| 4 | Script assembles the report; no editor pass (gated) | SPD-2, Q8, Q9, Q13, Q5(diff) | modify | must | M |
| 5 | A quiet, honest check | SPD-3, Q2(2–5) | modify | must | M |
| 6 | Remove the Yalova priming and the fixed Turkish skeleton | Q4, SPD cuts, SPD-10(example) | modify | must | S |
| 7 | Host fixes: script path, interpreter, PowerShell lookup, Codex live search | Q5, SPD-10(lookup), SPD-9(Codex) | keep | must | S |
| 8 | Researchers batch their calls and read pages in one call | SPD-5, Q16(batching), Q11(passages) | keep | must | M |
| 9 | Fetch: parallel, deduplicated, race-free; keeps tables and PDFs | SPD-8, Q12(fetch) | modify | should | M |
| 10 | Short briefs; static researcher rules in one file | SPD-6, Q cut 2 | keep | should | S |
| 11 | Search tally and evidence-based stopping, without a hard clock | SPD-7, Q16 | modify | should | S |
| 12 | Receipts that count: parse them, drop spans that are not on the page | Q2(1) | modify | should | S |
| 13 | Domain ladder lines, scope rule, "both, by definition" | Q3 | modify | should | S |
| 14 | Reuse: refresh vs borrow; Quick keeps its receipts | SPD-10, Q15, SPD-12(notes) | keep | should | S |
| 15 | Suite packaging and one version label | SPD-11, Q7 | modify | should | M |
| 16 | Document permission rules for research sessions | SPD-9(allow rules) | keep | should | S |
| 17 | Calendar converter in the script | Q19 | keep | could | S |
| 18 | One model or effort arm for researchers, no default change | SPD-13 | keep | could | S |
| 19 | Quick takes narrow niche questions | SPD-12(tier) | modify | could | S |
| 20 | Numeric parsing for computed and technical questions | Q2(4 partly) | modify | could | S |
| 21 | Question shapes as one-line rules, no shapes.md | Q10 | modify | could | S |
| 22 | Scorecard folded into the side-by-side judge brief | Q17 | modify | could | S |
| 23 | Wayback fallback and a record-first search line | Q12(rest) | modify | could | S |
| 24 | Receipt anchors and support.md | Q11(rest) | drop | none | M |
| 25 | Support verifier subagent | Q18 | drop | none | M |
| 26 | Certainty words and judgment-row counter-evidence | Q14 | drop | none | S |

## Details

### 1. Open before you rule (must, S)

**Why.** All three errors the judge found were negative verdicts:
- 4,80 m: conflicts.md C15 says "not opened".
- "27 köy" was called unsourced, but the opened Wikipedia page cites Gingeras.
- Law 1533 stayed not found, although the model knows the number: the 0.2 arm searched it from memory.

The B-cell check is the most precise flag anyone has proposed. It catches 4 cells, 2 of them real errors, so its precision is 50%. The current checker's precision is 8%.

SPD-4's follow-up trigger alone would not have caught Law 1533, because the law number was not a headline item. Q1's "[prior] values as search terms" does catch it.

**Change.**
- **Researcher rules.** Before calling a value wrong or unsourced, open the best page that states it, and follow a lead's footnote once. In the conflict list, cite the opened page for each side or write "B not opened". Search each row's `[prior]` values (law numbers, names, figures) as quoted terms.
- **Step 1.** Put expected values into the rows as `[prior]` search terms.
- **Lead rule.** A value nobody opened is "not checked". Its verdict reads "not settled" unless a follow-up opens it.
- **Disagreement table.** Every B cell carries `[n]` or "(not opened)". `check` flags a cell with neither as high severity. It never number-matches the B column or the unknowns block.
- **Follow-up brief.** Open the page behind any value you would reject.

**Effect.** It targets the error class behind all three of the judge's errors: overturned negative verdicts would fall from 3 of 17 to at most 1. Cost: 5–10 page opens and 0–1 minute per run.

**Verify.**
- Offline: send C12 and C15 to one follow-up agent with the new brief (about 2 minutes). It should reach Gingeras and a 4,80 m page.
- Offline: the new check on the frozen report flags exactly those 4 B cells.
- Live: count overturned negative verdicts in the side-by-side judge's claim checks. Target: 0–1.

### 2. One launch with the gap-finder's items folded in (must, S)

**Why.**
- The gap wave cost 6:20 and 3 agents (38–46 calls each) for items the lead had known since 08:59:49Z.
- Q6's extra lead scout of 3–5 searches would repeat the gap-finder's own 5 searches. Each gap-finder item already comes with the URL that suggested it.
- The scout would add about 1–1.5 minutes and about 5k tokens to the lead. **Drop that part.**

**Change.**
- **Step 1.** Create the run folder and spawn the gap-finder first, with only the question, date and scope. Write plan.md while it runs. When it replies, fold each item that would change the answer into a section's rows, or into one extra section (3–6 sections in all). Then launch.
- **Delete** step 4 and the sentence "The lead does not run the gap wave alone".
- **Gap-finder brief.** 8–12 items; "your items become plan rows". For lists and comparisons, also return the record that enumerates the items, and the frame. This also fixes the frame-before-plan contradiction.
- **No-subagent mode** already runs this pass first, so every mode now runs the same way.
- If the gap-finder replies NO_WEB, launch without it.

**Effect.** −4 to −5 minutes of wall time, −3 subagents and about −100 calls. The launch starts 0–1 minute later, since the gap-finder took 0:50–1:33.

**Verify.** From first spawn to last research reply ≤ 6 minutes. No second wave. The report still covers the gap-finder's items. At most 8 subagents.

### 3. Act on each reply; capped follow-ups (must, S)

**Why.**
- SKILL.md:44 ("Mark each row") and hosts.md:23 ("wait for all") produce the measured idling. hosts.md:15 says the opposite.
- On Codex the loop is feasible: `wait_agent` returns the first of several agents.

**Change.**
- **Merge steps 3 and 4 into "Follow up as replies arrive".** On each reply:
  1. Append its conflicts to conflicts.md.
  2. Settle what the ladder settles.
  3. At once, spawn one follow-up for each of these: a headline conflict the ladder cannot settle; a headline row left open; a value about to be rejected that nobody opened (item 1).
- **Headline** means a sentence of the answer, a row of the at-a-glance table, or a verdict in the disagreement table.
- **Caps:** Standard 3, Deep 6, Ultra until a batch adds no new fact.
- **Ownership:** spawn only for rows that no running agent owns. Assemble while follow-ups run.
- **Briefs.** One follow-up brief replaces the adjudicator and gap-researcher briefs.
- **hosts.md, Codex (one line):** call `wait_agent` on all running ids, handle the first that finishes, `close_agent` it; at most 6 open.

**Effect.** No deliberate idling. Adjudication starts about 1:30 earlier. A late follow-up overlaps assembly.

**Verify.** Each follow-up spawns within 30 s of its trigger. Lead idle time, excluding the wait for the last reply, is under 3 minutes.

### 4. The script assembles the report; no editor pass (must, M, gated)

**Why.** Without harness artifacts, the serial work after research is about 6:30–7:30. Dropping only the editor (Q8) saves about 2:45 of that. Script assembly cuts the whole tail to about 2:30–3:00.

The refutation risk is readability. The drafts' short sentences are proven, but the delivered report's structure is not reproduced: the concatenation has 28 headings, against 13 in the delivered report, and is 30% longer. The verify step SPD-2 proposed only tests the editor, not the concatenation.

**Change.**
- **New command, `vafer_check.py assemble <run>`.** It:
  - concatenates `sections/_top.md`, the sections in plan order, and `sections/_end.md`;
  - turns `[URL]` citations into `[n]` in order of first appearance;
  - writes the Sources list, with snapshot titles, under a heading in the reader's language and behind a marker;
  - writes report.md.
- **The lead's share.** The lead writes only `_top.md` (the 5–8 sentence answer and the at-a-glance table) and `_end.md` (the disagreement table and the unknowns). It folds follow-up verdicts into the section files, trims repetition there, and runs assemble again.
- **Deletions.** The editor brief, `report.before-edit.md`, step 6, and the hosts.md:12 workaround.
- **Keep `diff` in the script for now.** The fallback below still needs it. Delete it after the side-by-side.
- **Section word budget.** Each section gets the total divided by the number of sections. The total is about 2,000 body words in Standard, about 3,000 for "detaylı" and about 1,000 for "short". `check` prints body words against the target.

**Gate (before coding, at no cost).** Rebuild the v0.0.4 concatenation, with `_top` and `_end` copied from the delivered report. Have one blind judge rank the readability of three versions:
- (a) the concatenation;
- (b) report.before-edit.md;
- (c) report.md.

If (a) is clearly worse than (c), keep the lead's rewrite without the editor. Use `assemble` only for numbering and Sources, and run the script's `diff` from the assembled draft to the rewrite.

**Effect.** The tail drops to ≤ 3 minutes. −1 subagent, about −30 lead calls, 0 detached citations, and fewer sentences the lead writes itself.

**Verify.**
- The 3-way readability ranking above.
- Side-by-side: from the last research reply to delivery ≤ 3 minutes.
- Judge readability ≥ 8.
- Body length within ±15% of the target.

### 5. A quiet, honest check (must, M)

**Why.**
- Only 1 of the final 13 flags was real, and the noise trained the lead to dismiss the two flags that mattered.
- Item 4 needs citation borrowing, or the lead faces about 55 flags.
- The page-only flags Q2 proposes found no real error on the frozen run, so count those matches but do not flag them.

**Change.**
1. **Normalize:**
   - Roman-numeral and ordinal centuries (XVI. = 16. yüzyıl) and decades;
   - a full date as one token: no matching of its day or month alone, ISO and dotted dates included;
   - clock times (03.02 = 3:02).
2. **Structure:** no number matching in the B column or the unknowns block (the markers come from `assemble`), plus item 1's B-cell rule.
3. **Borrowing:** an uncited sentence or table row borrows its paragraph's or table's citations. "Uncited" is flagged only when nothing nearby is cited.
4. **Severity:** only high and medium flags need a disposition, and the open count covers only those.
5. **Honest counts:**
   - evidence.md says "N figures: S in a quoted receipt, P elsewhere on the cited page, F not found, U without evidence";
   - the reply's status line drops the match ratio and shows rows covered, open flags and time;
   - "Done when" stops promising that every figure "matches".
6. **Section check:** `check <run> --section <id>` checks one draft with `[URL]` citations. Researchers run it before replying. They fix what they can (add a citation they hold, correct a figure from its snapshot, replace a lead-only citation) and list the rest.

**Effect.** At most about 5 open medium or high flags at delivery. Flag handling takes ≤ 1 minute. The two flags that pointed at real errors become high flags that cannot be closed as false alarms.

**Verify.**
- At no cost: replay on the frozen run and on `asm_probe/run`. Every remaining medium or high flag is real or belongs to a named class.
- Unit tests for each normalization.
- Live: label every flag real or false; precision ≥ 50%.

### 6. Remove the Yalova priming and the fixed Turkish skeleton (must, S)

**Why.**
- report.md:5 repeats style.md:26, and SKILL.md:80 greps "yalova".
- The headings and status line are fixed in Turkish (SKILL.md:45, 47).
- The checker finds Sources only under six titles, and its leak rule flags the English word "researcher".

Until this goes, every side-by-side is primed or skewed.

**Change.**
- **SKILL.md step 5** names the parts by function, written in the reader's language: answer, at-a-glance table, sections, where sources disagree (topic | A | B | verdict | why), what is not known, sources.
- **Status line:** in the reader's language.
- **style.md:** function names instead of the Turkish labels, and one neutral before-and-after pair that is not about Turkish history. Neutral lookup example at SKILL.md:80.
- **Checker:**
  - find Sources by `assemble`'s marker, falling back to the last heading followed mostly by `[n] URL` lines;
  - find the check and mix lines by a fixed ASCII key;
  - limit the leak check to internal tokens;
  - skip the date line.
- CJK and Arabic sentence ends can come later.

**Verify.** No "Yalova" in the skill. Unit tests with an English and a Spanish report. The side-by-side report's first sentence is not copied from the skill.

### 7. Host fixes (must, S)

**Why.**
- The reuse glob fails in PowerShell, the author's primary shell.
- SKILL.md:53 demands an absolute path but gives relative examples, and `python3` is never offered.
- `codex exec --search` is rejected, yet the README and the compatibility line still recommend it.
- Codex's cached search is discovered too late.

**Change.**
- **One canonical command.** The lead resolves the absolute path of the skill folder and the interpreter (`python`, `python3` or `py -3`) once and pastes both into every brief.
- **Lookup:** `rg -i -l "<ascii terms>" .vafer/research --glob plan.md`.
- **Codex:** use `-c web_search="live"`, plus `-c sandbox_workspace_write.network_access=true` for fetch.
- **Preflight, one line in step 1:** search mode (on Codex, one dated query; if the results look cached, say so in the first reply line), subagents, and shell with network. It sets the fallback mode and the host line.

**Verify.**
- The lookup works in PowerShell and in Git Bash.
- The command works from another working directory.
- One Codex Quick question shows the search-mode line.

### 8. Researchers batch their calls and read pages in one call (must, M)

**Why.** Confirmed by the turn statistics. The −30–40% the speed designer projected rests on one external paper; the measured gaps between turns (about 3.5 s, times 20–35 turns) suggest −15–30%.

**Change.**
- **Researcher rule.** The first message runs the 3–5 starting searches, together with the rules read if item 10 lands. Each later message batches the next searches, one fetch of every promising URL, and one passage query over the new snapshots. Go wide first, then narrow.
- **`fetch <run> --find "a|b|c" <url>...`** prints, for each page, its status, file and title, and up to 3 line-numbered passages around the best term hits. Text is Turkish-folded; at most 1,500 characters per page.
- **`find <run> "<terms>" [<url>...]`** queries existing snapshots again.
- **WebFetch** is used only when fetch fails. This replaces "for finding and skimming" at SKILL.md:55.

**Effect.**
- Turns per researcher fall from 20–35 to about 12–16.
- Shell reads of snapshots fall from 98 to about 35, and WebFetch calls from 41 to about 10.
- Researcher wall time falls by 15–30%.

**Verify.** On the side-by-side transcripts, `speed_turns.py` shows ≤ 40% single-call turns and ≤ 16 turns per section researcher. The judge's accuracy is not lower.

### 9–16 (should)

- **9. Fetch.**
  - **Why:** S1's 82 s sequential fetch set the end of the launch wave, and 21 of 102 URLs were downloaded twice. The race and the boilerplate rule interact: fixing only the race would have excluded the Toynbee OCR as "boilerplate".
  - **Change:**
    - a thread pool with at most 2 workers per host, a 20 s timeout, and backoff on 429 or 503;
    - skip URLs that already have an ok snapshot;
    - write the status into the snapshot header, and rebuild the index from the headers;
    - judge boilerplate by characters, counting table rows as content;
    - without pdftotext, keep the raw PDF as `pdf-saved` for the host's PDF reader;
    - **read PDFs in reading order** (drop `-layout` for prose PDFs; see Missing).
  - **Verify:** unit tests; re-fetch the run's 12 failed URLs; the longest fetch call ≤ 30 s.
- **10. Short briefs.** researcher.md replaces style.md, so there are still 4 reference files. Under item 2, brief writing sits on the critical path after the gap-finder returns, so this gain adds to item 2's (1:14 → about 0:25). Minimal fallback: "read style.md" instead of "paste the short rules".
- **11. Search tally and stopping.**
  - **Keep:** about 8 searches per researcher (Deep 16) with a tally in the notes. A row closes when its settling record, or two independent sources, is in hand. Stop a row after a batch that adds nothing new.
  - **Keep:** opening the page behind a value you would reject is always within budget (item 1). plan.md gets `started:`, so the status line's time is real.
  - **Drop the hard 4-minute clock for now.** b1c91b8 removed time budgets on purpose, the 6–10 search guide has never run, and the external evidence comes from short-answer benchmarks.
- **12. Receipts that count.**
  - Accept `<URL>` autolinks and inner quotes, and list unparsed lines.
  - A span counts only if it occurs in its snapshot after whitespace, hyphenation and case folding. Unmatched spans are **dropped silently and counted, not flagged**, because a strict rule would raise about 14 false alarms per run, mostly from PDF layout.
  - Unverified receipts never match.
- **13. Domain ladder.**
  - Trim it to about 80 words in the researcher rules:
    - an issuer's claims about its own performance or about rivals count as press;
    - health: guideline or review > RCT > observational > opinion;
    - law: label the status (in force, applies from, adopted, proposed, guidance);
    - a figure settles a row only when its place, period, unit and definition match;
    - a "definition or scope" conflict type, with the verdict "both, by definition".
  - Keep one copy of the ladder.
  - It cannot be verified on a history question; verify it on one non-history question in the second round.
- **14. Reuse.** Refresh (the same question) versus borrow (a neighbouring question: import only receipts and dead ends that match in scope). Drop the `check` header field. Quick, when it has a shell, saves plan.md and notes. This is the most credible 5× rate against hyperresearch, which has no corpus reuse.
- **15. Packaging.**
  - **Add:** `.claude-plugin/plugin.json` (vafer, 0.0.5) and `marketplace.json` (source "./"); keep metadata.version equal, asserted by a hygiene test that loops over both skills.
  - **Why should, not must:** this is a release step, and it changes no research behavior. Copy installs work on both hosts today, and Codex has not been verified by a live install.
  - **Brainstorm design:** folder renaming and the shared `.vafer/<module>/` convention are decisions for the brainstorm skill's design.
- **16. Permission docs.** The README and hosts.md recommend allow rules for WebSearch, WebFetch and `Bash(python* *vafer_check.py*)`, or auto mode. Documented, not enforced.

### 17–23 (could)

- **17. Calendar converter:** Hijri and Rumi to Gregorian, with unit tests (Rumi 1316 = from 14 March 1900; 1 Muharram 1316 = 22 May 1898). It replaces S2's two improvised turns and turns 3 "derived" flags into receipts.
- **18. One model or effort arm:** test researchers at `effort: low` or on `sonnet` only after the musts land. Adopt it only if accuracy stays within 0.5 and research time drops at least 25%.
- **19. Quick for narrow niche questions:** test 2 questions as Quick against Standard before changing routing. Local questions are where VAFER earns its gains, so do not route them to Quick unmeasured.
- **20. Numeric parsing:** k/M/bn suffixes, percentage results, and parentheses through an `ast` walker. These are real checker bugs (from stress-test probes), but no question in the next side-by-side exercises them.
- **21. Shapes as one-liners:** comparison → one shared frame; computed → researchers return inputs, the lead computes; list → the gap-finder returns the frame. No shapes.md: it would be a 5th reference file, and no non-history question has been tested.
- **22. Scorecard:** put three counted measures into the side-by-side judge brief (overturned negative verdicts, flag precision, time and calls). No separate document; the 5× rates are a brainstorm decision.
- **23. Wayback and record-first search:** one Wayback try for 404 or 410; "follow a lead's references once" already sits in item 1.

### 24–26 (dropped)

- **24. Receipt anchors and support.md (Q11).**
  - **Why drop:** the judge found no unsupported prose in v0.0.4. Anchors change every researcher's output format, and support.md has no reader unless the verifier (25) ships. That is the v0.0.3 pattern: records kept for their own sake.
  - **Kept elsewhere:** the `passages` idea lives on in item 8.
- **25. Support verifier (Q18).** It adds a spawn and a stage after the report, and no catch has been measured. Revisit it only if a judged run shows unsupported load-bearing prose.
- **26. Certainty words and judgment rows (Q14).** They add labels and searches against no measured failure (conflict handling scored 8.5). style.md rule 7 already covers plain-word uncertainty.

## Missing

No proposal addresses these:

- **PDF reading order (should; must if item 12 ships).**
  - `pdftotext -layout` interleaves two-column scholarly PDFs such as DergiPark's. Several PDF snapshots have hundreds of lines wider than 110 characters.
  - It breaks receipt spans and quote checks: it causes most of the 14 unmatched spans, including the 5 m receipt behind C15. It also makes grep reading harder.
  - Fix: use reading order for prose PDFs, and keep `-layout` only for table-heavy ones, or save both.
- **A Codex smoke run (should).** Codex has never run the skill. The musts change Codex instructions (the `wait_agent` loop, the live-search preflight). Run one Standard question on Codex before claiming support.
- **Binding pass criteria for the side-by-side (should).** Fix them before running:
  - claim-level errors and negative-verdict errors, counted;
  - time and tool calls;
  - two runs per VAFER arm when affordable, because 0.5-point gaps are noise and the same design took 13:39 in one run and 24:00 in another.
- **A failed or silent subagent (could).** Now that the lead acts on each reply, nothing says what to do when a researcher errors, turns out to have no web access mid-run, or never replies. One line: spawn it again once, then cover its headline rows with a follow-up or mark them NOT SEARCHED.
- **Compaction (could).** The lead's context reached 210k tokens in v0.0.4. Claude Code restores only the first 5,000 tokens of a skill after compaction, and Codex mode C keeps 45–65 searches in one context. Add one line: after compaction, re-read plan.md and conflicts.md.
- **A run-wide search count (could).** Deep (6 × 16 searches plus 6 follow-ups) approaches the 200-search session cap, which refills at about 100 per hour. Nothing tells the lead to count.
- **Copies of one account (could).** The 2025 population rested on the governor's post and on Wikipedia carrying the same figure, and the source mix counts URLs, not origins.

## Tensions and how I resolved them

1. **The lead's rewrite vs script assembly (speed vs readability).** The blind 3-way readability check at no cost (item 4's gate) decides. If assembly loses, keep the rewrite without the editor; that still saves about 2:45.
2. **Gap-finder first (SPD-1) vs a scout, then plan (Q6).** I chose gap-finder only. It already searches, and a lead scout costs 1–1.5 minutes and about 5k tokens of lead context.
3. **Exempting rejected values (Q2, skill-audit) vs a "rejection" flag kind (SPD-3).** Both: do not number-match the B column or the unknowns block, but require `[n]` or "(not opened)" in every B cell. That turns the noise into the exact check that would have caught the judge's errors.
4. **Citation borrowing (SPD-3) vs per-sentence anchors (Q11).** Borrowing defines the checker's evidence pool; the style rule (a citation at the end of the sentence) stays. Anchors are deferred.
5. **Budgets (SPD-7, Q16) vs open before ruling (Q1) and the deliberate "no time limit" (b1c91b8).** A soft search tally and an evidence-based stop, with no hard clock. Opening the page behind a value you would reject is always allowed. Open headline rows go to follow-ups.
6. **Script growth vs the 700-line cap and the v0.0.3 lesson.** The musts add about 150 lines, even with `diff` kept. Raise the cap once, to about 900, with the rule that every feature replaces measured agent work. State the file formats in SKILL.md so the lead never reads the script, which it did in v0.0.4. Delete `diff` once assembly is proven.
7. **Reference cap of 4.** researcher.md replaces style.md (item 10). No shapes.md (item 21).
8. **Length: about 2,000 words (SPD-2) vs 1,500 (Q13).** I chose about 2,000 by default, with the reader's request words overriding it. The judge scored a 2,406-word body 8.5 for readability. The test question asked for "detaylı", so 1,500 would cut coverage for no measured gain. The final number is the author's call.
9. **What the reply's status line shows.** It shows rows covered, open medium and high flags, and time. Figure counts go to evidence.md.
10. **Codex procedure vs "detailed recipes hinder Astra".** The Codex event loop stays one line in hosts.md. The musts remove more procedure (the gap wave, the editor, `diff`, pasted rules) than they add.
11. **Version label: only in plugin.json (SPD-11) vs kept equal everywhere (Q7).** Keep metadata.version equal to plugin.json, with a test, matching the author's "single version label" commit.

## Order of work and verification

1. **Text-only musts first: items 6, 7, 1, 2 and 3.** Item 6 must land before any run.
2. **Checks at no cost, offline:**
   - the 3-way readability ranking (item 4's gate);
   - replay the new check on the frozen run and on `asm_probe/run` (items 1, 5);
   - one follow-up agent on C12 and C15 (item 1).
3. **Script musts: items 5, 4 and 8,** with unit tests.
4. **One side-by-side.** A fresh Turkish-local question, not Yalova. Arms: v0.0.5, v0.0.4 HEAD and bare, with the lead in a main session; each VAFER arm twice if affordable. **Pass:**
   - v0.0.5 takes ≤ 13 minutes with ≤ 8 subagents;
   - judge accuracy ≥ v0.0.4's on the same question;
   - at most 1 overturned negative verdict;
   - readability ≥ 8;
   - ≤ 5 open medium or high flags, with precision ≥ 50%.
5. **Then the shoulds,** with one non-history question (for item 13), one next-day follow-up (item 14) and one Codex smoke run.
