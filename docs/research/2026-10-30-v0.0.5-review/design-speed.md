# vafer-research v0.0.5 through the speed lens

Date: 2026-10-30. Lens: speed at equal quality. Where did the v0.0.4 Yalova run's 22:53, 11 subagents and 362 tool calls go, and what can v0.0.5 remove without lowering accuracy (8.5) or source quality (9)?

Inputs: the six notes in `notes/`, the skill at 5ebab1a, the v0.0.4 run folder and its transcripts. I measured the run again myself (helper scripts are listed at the end). Today I also checked the W&D and Budget Tracker papers and the Claude Code subagent docs.

## Summary

- **The target holds.** About 10 minutes with fewer than half the tool calls is reachable for a Standard question the size of Yalova, without cutting research depth. My projection is 8–11 minutes, 150–175 tool calls and 7–8 subagents. Confidence is medium-low: it rests on one run, and stragglers vary (the same 0.2 design took 13:39 in one run and 24:00 in another).
- **Searching is not the bottleneck.** All agents together waited 655 s on WebSearch, mostly in parallel batches. Three serial patterns cost the time instead:
  - a second research wave that started only after the slowest researcher (6:20);
  - the lead re-generating text after research ended (9:32);
  - researchers taking one small step per model turn (20–35 turns each, 76% of them with a single tool call).
- **The lead waited by choice.** Every reply woke it. It wrote "I'll decide on a gap wave once the sections come back" (11:59:49) and "Waiting on section 1; then I'll send the gap wave and the adjudicator together" (12:03:33). The skill's step order told it to wait.
- **Readability came from the researchers, not from the lead or the editor:**
  - The section drafts averaged 10.7 words per sentence, with 3 long sentences across 8 files.
  - The lead's rewrite raised that to 12.3 words and 6 long sentences.
  - The editor brought it back to 11.0 and 3, and detached 6 citations.

  The two serial rewrites largely cancelled each other out.
- **The five must-changes all remove work:**
  1. Run the gap-finder first and fold its items into the single launch.
  2. Build report.md with the script, and drop the editor and `diff`.
  3. Cut check noise, and let researchers fix their own flags in parallel.
  4. Act on each reply as it arrives, with targeted follow-up agents.
  5. Have researchers batch their tool calls and read pages through the snapshot in one call.
- **Script assembly depends on change 3.** When I concatenated the run's own drafts, the current checker raised 55 flags. The lead's rewrite raised 41.
- **Keep the quality drivers:**
  - The ladder, the calendar rule and the gap-finder produced the quality gains (prior-research F1).
  - Search counts are not the bottleneck.
  - Keep researchers on the session model unless a measured run shows otherwise.

## Where the 22:53 went, and where it could go

| Phase (v0.0.4 run) | Took | What happened | v0.0.5 projection |
|---|---|---|---|
| Read skill, write plan | 0:42 | read 4 files; plan with 12 `[prior]` rows | 0:40; the gap-finder starts first and overlaps it |
| Write 6 briefs, spawn | 1:14 | section briefs of 548–596 words, about 14 s of lead output each | ~0:25 with ~120-word briefs |
| Launch wave | 5:05 (S1 ran 6:03) | 5 researchers, 26–33 calls each | ~3:30–4:15: batching, `find`, parallel fetch, one more row each |
| Conflicts, adjudicator, 3 gap briefs | 1:09 | started only after the slowest researcher | 0: handled as each reply arrives |
| Gap wave | 5:11 | 3 researchers, 38–46 calls each | 0: its items were rows in the launch |
| Assemble | 4:36 | re-typed 24,674 characters (1:41), again after a refused write (1:31), improvised `renumber.py` | ~1:00–1:30: script plus ~600–900 words by the lead |
| Check | 1:42 | 2 crashes (fixed in 575396a), `fix1.py`, `dispo.py` | ~0:30 |
| Editor, diff, re-check | 2:43 | 12.3 → 11.0 words per sentence; 6 citations detached | 0 |
| Deliver | 0:31 | | 0:20 |
| Follow-up overhang | off the path | the adjudicator ran during the gap wave | 0–1:30 if a late reply triggers one |
| **Total** | **22:53** | 11 subagents, 362 calls, 232k output tokens | **~8–11 min**, 7–8 subagents, ~150–175 calls, roughly 120–140k output tokens |

Most of the call reduction comes from deleting the gap wave (−128 calls) and the lead's chores (about −30). Batching cuts turns more than calls: researchers would go from 211 turns to about 70.

The 22:53 also contains harness artifacts. The lead ran as a subagent, so a write was refused and cost 1:31, and check crashes have since been fixed. A HEAD run in a main session would probably take about 20 minutes. The side-by-side must re-measure HEAD under the same conditions.

## What I measured

**M1. The lead was idle because the steps told it to wait** (`lead_wake.py` on `agent-ab569b7fdce2cbf4b`).
- Notifications arrived at 11:59:47 (gap-finder), 12:02:17, 12:02:27, 12:02:50, 12:03:30 and 12:04:02.
- The lead acknowledged each and acted only at 12:04:18. It saw the Termal calendar conflict at 12:02:55 but spawned its adjudicator at 12:04:25. It knew the gap items at 11:59:49 but spawned the gap researchers at 12:04:40–12:05:11.
- SKILL.md:44 ("Mark each row", then the gap wave) and hosts.md:23 ("wait for all, then integrate") produce this behavior. hosts.md:15 says the opposite.

**M2. Researchers take one small step per model turn** (`speed_turns.py`).

| | v0.0.4 researchers (8) | 0.2 researchers (4) | bare arm |
|---|---|---|---|
| Model turns | 211 (20–35 each) | 117 | 16 |
| Turns with a single tool call | 76% | 85% | 44% |
| Calls per turn | 1.31 | 1.23 | 1.56 |
| Median gap between turns | 3.2–4.0 s | 3.8–4.0 s | 3.7 s |

Each researcher also spent about one minute writing its notes (about 7.8k characters) and its section (about 4.6k characters) (`speed_gaps.py`). Thinking is redacted in the transcripts, but tool inputs explain only about half of the researchers' output tokens.

**M3. Reading one page took two or three serial turns.**
- The pattern was `head` plus `grep -n -E "terms"`, then `sed -n` over line ranges, then another grep (calls.tsv; G2 at 12:06:07–12:09:17).
- Researchers read snapshots 98 times this way (skill-audit F12), 20 times in G2 alone.
- 25 of the 34 pages read with WebFetch were also snapshotted (run-evidence F4).
- S2 spent three turns trying pypdf, fitz and pdfminer before using pdftotext, and two more improvising Julian-day formulas for the calendar conversion.

**M4. The lead regenerated the report rather than assembling it** (`assembly_overlap.py`, `briefsize.py`).
- Only 21% of the report's 8-word sequences appear in the section drafts.
- The lead merged 8 drafts (3,407 words) into a 2,406-word body with 7 chronological sections, because the gap-wave sections had to be woven in.
- That took 1:41 of generation for 24,674 characters, then 1:31 more after the refused write. The 0.2 arm did the same: 22,942 characters in 1:54.

**M5. Readability came from the drafts** (`readab.py`).

| Text | Words per sentence | Sentences over 25 words |
|---|---|---|
| 8 section drafts | 9.5–12.9 (mean 10.7) | 3 in total |
| report.before-edit.md (the lead's rewrite) | 12.3 | 6 |
| report.md (after the editor) | 11.0 | 3 |

**M6. Concatenation alone would flood the check** (`asm_probe/assemble_proto.py`, `inherit_probe.py`; HEAD `vafer_check.py check`).
- I concatenated the 8 drafts as written, renumbered the citations and built a Sources list. The result was 3,408 words with 184 of 189 figures matched, but 55 flags:
  - 26 uncited sentences and 13 uncited table rows;
  - 8 lead-only;
  - 5 number mismatches, all format noise: two centuries, the day number in a date, a clock time and a decade;
  - 1 quote mismatch and 2 unverifiable sources (URLs cut at "(").
- I then let an uncited sentence borrow its paragraph's citations, and an uncited row its table's. Of the 39 uncited items, 21 had a citation nearby. 14 of those then matched in full. The other 7 became sharper mismatches, among them the 4,80 m value the judge said was wrongly dismissed and an unsourced 2000 census figure.

**M7. Every brief re-typed the static rules.**
- The five launch briefs were 4.0–4.4k characters each, emitted 13–15 s apart from 11:57:58 to 11:58:54. Each researcher started when its brief was emitted.
- briefs.md:27 ("paste the short rules from style.md") is undefined, and briefs.md:3 ("put everything it needs in it") forces the copy.

**External evidence I re-checked today:**
- **W&D** (arXiv 2602.07359, Tables 1 and 3; first 100 BrowseComp tasks, GPT-5-Medium):
  - one call per turn: 66% accuracy in 45.7 turns;
  - three calls per turn: 68% in 23.8 turns, with 35.9% lower cost and 40.6% less wall time;
  - the "descending" schedule (wide first, then narrow): 74% in 23.5 turns.
- **Budget Tracker** (arXiv 2511.17006, Table 2; Gemini 2.5 Pro on BrowseComp). With a tracker and a budget of 10, accuracy was 12.8%; plain ReAct with a budget of 100 reached 12.6%. The tracker used 40.4% fewer searches and cost 31.3% less. The two accuracies are within noise (±1.2).
- **Claude Code subagents** (code.claude.com/docs/en/sub-agents):
  - each spawn accepts a `model` alias (`sonnet`, `opus`, `haiku`, `fable`) and, from v2.1.292, an `effort` level;
  - up to 20 subagents run at once, in the background by default.
- **Codex.** `wait_agent` v1 takes several ids ("Pass multiple ids to wait for whichever finishes first", multi_agents_spec.rs:896). At most 6 subagents run at once.

## Capabilities of a best-in-class deep-research skill, and v0.0.4's status

| # | Capability | v0.0.4 | Note and evidence |
|---|---|---|---|
| 1 | Scoping: reader, purpose, scope | partial | Up to 3 clarifying questions, only when they change the search (SKILL.md:33). The Yalova plan assumed the reader (skill-audit F18). |
| 2 | Decomposition into rows that name the record that settles each one | has | 4–12 rows, each naming its record (SKILL.md:41). The judge praised the primary sources (run-evidence F8). |
| 3 | Coverage discovery by a fresh gap-finder | partial | It found Kibotos 1096, 1915 and 1923 in 0:49, but its items ran as a serial 5:11 wave (run-evidence F2). |
| 4 | Query strategy: languages, variants, going straight to the record, citation chasing | partial | Two rules (SKILL.md:60–61). Law 1533 was missed after 6 queries; `[prior]` candidate values were not used as search terms (run-evidence F9). |
| 5 | Parallel tool use per agent, wide first, then narrow | missing | 76% of researcher turns issued one call, and researchers took 20–35 turns each (M2). Batching is asked for only in Quick and in rule 3. |
| 6 | Budgets and evidence-based stopping, with a visible clock | partial | A guide of 6–10 searches (briefs.md:18), no tally, no start time, and "There is no time limit" (SKILL.md:49). The straggler set the wall time (run-evidence F13). |
| 7 | Reading primary pages: tables, PDFs, OCR, JavaScript pages | partial | 12 of 63 fetches failed. The boilerplate rule rejects tables and Gutenberg or OCR text, and PDFs need pdftotext (skill-audit F7). |
| 8 | Efficient reading: from download to the relevant passage in one call | missing | 98 grep or sed reads of snapshots, and 25 pages opened twice (M3; run-evidence F4). |
| 9 | Evidence capture: exact receipts with rung labels | has | Receipt lines with span and rung (SKILL.md:74). Spans are never checked against the snapshots (skill-audit F4). |
| 10 | Source ranking across domains | partial | One ladder shaped for history: vendor benchmarks count as primary, and it has no legal status or study design (stress-test F10). |
| 11 | Conflict settling, including opening the losing side's source | partial | Ladder plus adjudicator. All three of the judge's errors were rejections without opening the source, or footnotes not followed (skill-audit F15). |
| 12 | Verification of the written text | partial | Figures are matched anywhere on the cited page, and prose is unchecked. 1 of 13 flags was real (skill-audit F3, F6; external-sweep F8). |
| 13 | Answer-first synthesis: answer, at-a-glance table, conflicts, unknowns | has | Fixed skeleton (SKILL.md:45). The judge: "tables are clean". |
| 14 | Plain writing in the user's language | has | Readability 8.5. The researchers' drafts already had the short sentences (M5). The Turkish headings are fixed for every language (stress-test F13). |
| 15 | Event-driven orchestration: no idle lead, no serial waves | missing | The lead was idle for 10:25 and waited for the whole wave by choice (M1). |
| 16 | Mechanical work done in code: assembly, renumbering, flag bookkeeping, date conversion | missing | `renumber.py`, `fix1.py`, `dispo.py`, a patched checker, the report typed twice, improvised calendar code (skill-audit F11, M3). |
| 17 | Per-role model and effort routing | missing | Every agent inherits the session model, though both hosts allow a model per spawn (hosts F1, F3). |
| 18 | Reuse for follow-ups | partial | reuse.md exists but has never been run, and the lookup fails in PowerShell (stress-test F6). |
| 19 | Robustness across hosts and fallbacks | partial | Modes A–D exist. Codex is untested, with 6 subagents at most, and its `--search` flag is rejected (hosts F3, F7). |
| 20 | Transparency: method, checks, an honest status line | partial | evidence.md and check.md exist. The status ratio leaves unchecked figures out of the count, and "Süre" has no recorded start time (skill-audit F5, F14). |

## Proposals, most important first

Each proposal removes work unless stated otherwise. Word and line budgets: SKILL.md would drop by about 30 words. The text before the loop is at 374 of 400 words, so changes to the tier table need offsetting cuts there. briefs.md would shrink by about 300 words. vafer_check.py would grow from 700 to about 780 lines, even after deleting `diff` (about 60 lines). That requires a deliberate cap change (open question 4).

### SPD-1 (must, S). Run the gap-finder first and fold its items into the single launch

- **Problem.** The gap wave was a serial second wave: 6:20 of the 22:53 (1:09 of briefing, then 5:11 of running), 3 extra subagents and 128 calls (G1 38, G2 46, G3 44). The lead already knew its items at minute 3.
- **Evidence.** run-evidence F1 and F2; skill-audit F10; prior-research F5, which raises this as a hypothesis; M1.
- **Change.**
  - SKILL.md step 1: "Create the run folder and spawn the gap-finder first; it needs only the question, date and scope. Write plan.md while it runs. When it replies, add each item that would change the answer as a row in its section, or as one extra section, then launch." Standard allows 3–6 sections, gap items included.
  - Delete step 4 as a separate wave. Open items after the launch go to SPD-4 follow-ups.
  - briefs.md: the gap-finder replies with 8–12 items. "Do the gap-finder pass first" (briefs.md:74) becomes the rule in every mode, which removes the mode-C contradiction.
  - The same first slot finds the frame for the table variant, which fixes stress-test F4's "frame before plan" contradiction.
- **Files.** SKILL.md (tier table, steps 1, 2 and 4); references/briefs.md (gap-finder, table variant, Variants); README (run flow).
- **Effect.**
  - −5 to −6 min of wall time on the measured run: research would have ended with S1 at about 12:05 instead of 12:10:22.
  - +0:00–0:40 before launch: the gap-finder took 0:49 in the v0.0.4 run and 0:54 and 1:33 in the two 0.2 runs, and it overlaps the ~0:40 of plan writing.
  - −3 subagents and about −100 calls net (−128, plus about 5 more per section for the extra rows).
- **Risk.**
  - Gap items lose their dedicated researchers (38–46 calls each) and are covered under a section's budget. The extra section mitigates this.
  - A slow gap-finder (1:33) delays the launch by about a minute.
  - If the gap-finder replies NO_WEB, launch without it, as today.
  - No ceremony is added; one phase is removed.
- **Verify.** Re-run Yalova after removing the Yalova text from the references:
  - research phase (first spawn to last research reply) ≤ 6 min;
  - the report still covers Kibotos 1096, the 1915 deportation and the 1923 exchange;
  - ≤ 8 subagents, and the judge's coverage score ≥ 8.5.

### SPD-2 (must, M). Build report.md with the script; the lead writes only the top and the conflicts; drop the editor and diff

- **Problem.** After research, the lead spent 9:32 mostly re-generating text and improvising chores (M4), and the editor pass added 2:43. The drafts were already the most readable version (M5). Step 6's bare `diff` is a regression: in PowerShell it compares two file names and reports success (stress-test F9; skill-audit F1).
- **Evidence.** M4, M5; run-evidence F1, F6 and F7; skill-audit F11.
- **Change.**
  - New `vafer_check.py assemble <run> <id> ...` (about 45 lines; prototype in `asm_probe/assemble_proto.py`):
    1. concatenates `sections/_top.md`, then `sections/<id>.md` in plan order, then `sections/_end.md`;
    2. turns `[URL]` citations into `[n]` in order of first appearance;
    3. writes Sources as `[n] <title from the snapshot's first line> <URL>` under a heading in the user's language;
    4. writes report.md, overwriting it. The section files stay the source.
  - SKILL.md step 5. The lead writes `_top.md` (the 5–8 sentence answer and the at-a-glance table) and `_end.md` (the conflicts table with verdicts, and the unknowns), citing with URLs. It folds follow-up verdicts into the affected section files and runs `assemble`. All fixes go into the section files, then the report is assembled again.
  - Delete step 6: the editor brief, report.before-edit.md and `diff`, with its 5 DiffTests.
  - `check` gains a low-severity "long sentence" flag (over 25 words) for the lead to fix in place.
  - Each brief carries a section word budget: Standard total about 2,000 words divided by the number of sections, at most 400. Concatenation then lands near v0.0.4's 2,406-word body.
  - hosts.md:12 (the refused report* write) becomes moot, because the script writes report.md.
- **Files.** SKILL.md (steps 5–6, Checking, Files); references/briefs.md (delete Editor; add the word budget); scripts/vafer_check.py; tests/test_vafer_check.py; references/hosts.md; README (run flow, script table).
- **Effect.**
  - The tail after research drops from 9:32 to about 2:00–2:30. The lead writes 600–900 words instead of about 2,900 words twice.
  - About −30 lead calls and −1 subagent.
  - Readability equal or better: 10.7 words per sentence in the drafts against 11.0 delivered.
  - Fewer self-written sentences, which are unsupported 2.3–4.4× as often as copied ones (external-sweep F8).
- **Risk.**
  - The report may read as stitched sections, with repetition and few transitions. The lead's rewrite had merged and cut 30%. SPD-1 keeps the sections in report order; "Others cover", the word budgets and the lead's trims of repetition limit the rest.
  - Questions that need interleaving (comparisons) keep the comparison table in the lead's `_top.md`.
  - This change needs SPD-3; without it, the lead faces about 55 flags (M6).
- **Verify.**
  - First, at zero cost: a blind judge compares the readability of v0.0.4's report.before-edit.md and report.md. If the edited version does not clearly win, the editor goes.
  - Then, in the side-by-side: last research reply to delivery ≤ 3 min; readability ≥ 8 from the same judge; ≤ 12 words per sentence in `readab.py`; 0 detached citations.

### SPD-3 (must, M). Cut check noise and move flag fixing into the parallel phase

- **Problem.**
  - Flag handling is serial lead work, and 12 of the 13 final flags were noise. The lead wrote `dispo.py` and dismissed the two flags that pointed at the judge's errors (run-evidence F10).
  - Concatenated drafts raise 55 flags (M6).
- **Evidence.** M6 (`asm_probe/run/check.md`, `inherit_probe.py`); skill-audit F6; prior-research F6; stress-test F11.
- **Change** (`vafer_check.py check`, about 35 lines):
  1. An uncited sentence borrows its paragraph's citations, and an uncited table row borrows its table's (cells, caption, or the sentence just above). Borrowed figures are matched like cited ones. "Uncited" is flagged only when nothing nearby is cited.
  2. Normalize centuries and Roman numerals (16. yüzyıl = XVI.), decades (1930'lar), the day or month inside a full date, clock times (03.02 = 3:02), and ISO or dotted dates.
  3. Low-severity flags are listed but need no disposition, and the status line counts only open medium and high flags.
  4. Do not exempt rejected values or "not found" sentences. They get their own kind: "rejection: open the page that carries X, or write 'not checked'". An SPD-4 follow-up resolves it; a disposition never does.
  5. `check <run> --section <id>` checks one draft that uses `[URL]` citations. Researcher rule: before replying, run it, fix what you can (add the citation you already hold, correct a figure from its snapshot), and list the rest in the reply.
- **Files.** scripts/vafer_check.py; tests/test_vafer_check.py; SKILL.md (Checking: which flags need answers); references/researcher.md (the self-check line).
- **Effect.**
  - Final open flags fall from 13 to an estimated 3–8, mostly real. Before the editor there were 41, and raw concatenation gives 55.
  - Final flag handling drops from 1:42 to about 0:30. Traceability fixes move to the researchers, 10–30 s each, in parallel.
  - Accuracy: the two flags the lead dismissed would have gone to a follow-up instead.
- **Risk.**
  - Borrowed citations weaken sentence-level attribution. Keep "citation at the end of the sentence" as the style rule, with a low-severity reminder.
  - A researcher might rewrite correct text to silence a flag. Keep "Do not delete a claim only to clear a flag."
  - About +35 script lines.
- **Verify.** At zero cost, re-run `check` on the v0.0.4 run folder and on the concatenation probe: the flags should drop, and every remaining mismatch should be either real or a named class. In the side-by-side: ≤ 5 open medium or high flags, handled by the lead in ≤ 1 min.

### SPD-4 (must, S). Act on each reply as it arrives: follow-up agents replace waves and batched adjudication

- **Problem.**
  - The lead was idle for 10:25 and waited by choice (M1).
  - The judge's three errors were each an item that one targeted follow-up could have settled: 4,80 m rejected without opening its source, "27 köy" called unsourced, and Law 1533 not found.
  - "Headline" is never defined (skill-audit F14).
- **Evidence.** M1; run-evidence F2 and F9; skill-audit F15; Codex `wait_agent` semantics (multi_agents_spec.rs:896).
- **Change.**
  - Merge SKILL.md steps 3 and 4 into one step, "Follow up as replies arrive". On each reply:
    1. Append its conflicts to conflicts.md and settle the ones the ladder can settle from the receipts already in hand.
    2. Spawn one follow-up agent at once for each of these: a headline conflict the ladder cannot settle; a headline row left NOT-FOUND or partial; a value about to be rejected whose source nobody opened.
  - Headline means anything that will appear in the answer or the at-a-glance table.
  - Caps: Standard 3, Deep 6, Ultra until a batch adds no new fact, plus one counter-evidence search per headline conclusion. Never wait for the whole wave; start assembling while follow-ups run.
  - briefs.md: the Adjudicator brief becomes Follow-up. It adds "including the page behind any value you would reject; for a not-found row, try the `[prior]` candidate values as search terms" and the verdict "both, by definition or scope".
  - hosts.md, Claude Code: act on each notification.
  - hosts.md, Codex: call `wait_agent` on all running ids; it returns the first to finish. Handle that one, `close_agent` it, and repeat, with at most 6 open at once.
- **Files.** SKILL.md (steps 3–4); references/briefs.md; references/hosts.md (lines 15 and 23).
- **Effect.**
  - No idle lead. Adjudication would have started about 1:30 earlier in the measured run.
  - A late follow-up adds at most about 2 min (the adjudicator took 1:59), during which the lead assembles.
  - Aims at the judge's three errors; an accuracy gain of about +0.5 is plausible but unmeasured.
- **Risk.**
  - Over-spawning is limited by the caps.
  - Duplicated work: spawn only for rows that no running researcher owns.
  - Codex must close finished agents to free slots.
  - The change removes the "wave" concept; it adds no ceremony.
- **Verify.** In the side-by-side transcript:
  - every follow-up spawns within 30 s of the reply that triggered it;
  - the lead is idle for less than 3 min;
  - rejected values are opened rather than dismissed.

### SPD-5 (must, M). Researchers batch their calls and read pages through the snapshot in one call

- **Problem.** M2 and M3: 20–35 turns per researcher, 76% of them single-call, two or three turns per page, 98 snapshot reads and 25 double opens. Generation took 49–69% of researcher wall time.
- **Evidence.** `speed_turns.py`, `speed_gaps.py`; run-evidence F3 and F4; skill-audit F12; W&D (verified today).
- **Change.**
  - Researcher rule: "Work in batches. Your first message reads the rules file and runs all starting queries at once (3–5 searches). After that, each message does several things together: the next searches, one fetch of every promising URL, one find over new snapshots. Go wide first, then narrow as rows close."
  - Script, about 35 lines:
    - `fetch <run> --find "<a|b|c>" <url> ...` prints, for each page, its status, file and title, and up to 3 passages. Each passage is ±2 lines around the lines with the most term hits (Turkish case folded, line-numbered), at most 1,500 characters per page.
    - `find <run> "<terms>" [<url> ...]` queries existing snapshots again.
    - The passage score can be a hit count or a stdlib BM25 (external-sweep F5).
  - WebFetch only when `fetch` fails: replace "for finding and skimming" (SKILL.md:55).
- **Files.** scripts/vafer_check.py; references/researcher.md (new, SPD-6); SKILL.md (Checking); references/hosts.md:13–14; tests.
- **Effect.**
  - Turns per researcher from 20–35 to about 10–14; snapshot reads from 98 to about 35; WebFetch calls from 41 to about 10.
  - Researcher wall time about −30–40% (W&D measured −40.6% at equal accuracy). The slowest researcher would take about 3:30–4:00 instead of 6:00.
- **Risk.**
  - Passages can hide context that a full read gives (external-sweep F5: filtering hurt open-ended writing). Keep the passages generous; researchers can still read line ranges.
  - Batching unrelated searches would not help: W&D's "ascending" schedule did worse.
  - Bound the output so researcher context does not swell.
- **Verify.** Run `speed_turns.py` on the side-by-side transcripts: single-call turns ≤ 40%, ≤ 15 turns per researcher, ≤ 5 shell reads per researcher, and the judge's accuracy unchanged.

### SPD-6 (should, S). Short briefs; the static researcher rules live in one file the subagent reads

- **Problem.** M7: the lead hand-wrote eleven briefs of about 590 words each, at about 14 s each on the launch path, and the static rules were copied every time.
- **Evidence.** `briefsize.py`; skill-audit F11; briefs.md:3 and :27.
- **Change.**
  - New references/researcher.md replaces style.md, so there are still 4 reference files and the hygiene test is unchanged. It holds everything a subagent needs that does not change between runs:
    - batching (SPD-5) and the ladder;
    - the receipt format and the rules: cite only opened pages; take figures from the highest source; follow a lead's footnote before calling a claim unsourced;
    - the budget and stop rule (SPD-7) and the self-check (SPD-3);
    - the section format and the 10 house-style rules, with a short example that has no Yalova text.
  - briefs.md keeps only the run-specific templates:
    - section researcher, about 120 words: date, question, reader, section id and title, word budget, rows with their settling records, `[prior]` values as search terms, what others cover, starting queries, run folder, script command, budget, NO_WEB;
    - follow-up (about 70 words) and gap-finder (about 90);
    - the table and finite-work variants.
  - First line of every brief: "Read {skill folder}/references/researcher.md in your first message, together with your first searches."
- **Files.** references/briefs.md; references/style.md → references/researcher.md; SKILL.md (References, step 2); README.
- **Effect.** Launch briefs take about 0:25 instead of 1:14, and follow-up briefs about 5 s instead of 15 s. Lead output drops by about 15k tokens, and every researcher gets identical rules.
- **Risk.** A subagent that skips the file breaks the receipt format; the section check surfaces it. If that happens, put the five key rules back into the brief. The extra Read runs in parallel with the first searches.
- **Verify.** The launch span (first to last researcher spawn) is ≤ 30 s, every researcher's first turn includes the Read, and `check` reports 0 unparsed receipt lines.

### SPD-7 (should, S). A visible budget and a run clock for every agent, with partial return

- **Problem.**
  - Wall time follows the slowest researcher. The same 0.2 design took 13:39 and 24:00 because one researcher ran 10:22 with 76 calls (run-evidence F13).
  - "There is no time limit" (SKILL.md:49), and the 6–10 search guide is invisible to the researcher.
  - "Süre" in the status line has no recorded start time (skill-audit F14).
- **Evidence.** prior-research F2 (the Opus 5.5 guide: budgets kept quality and finished sooner); external-sweep F3 and F4; Budget Tracker, verified today.
- **Change.**
  - The plan.md header gets `started: <time>`, taken from the lead's first shell call.
  - `fetch` and `find` end their output with "run clock m:ss".
  - Researcher rules: "Budget: about 8 searches and 4 minutes of run clock after you start. Keep a tally in your notes ('searches 5/8'). A row closes when its settling record, or two independent sources, is in hand. Stop after a batch that adds no new URL or fact, or at the budget: write up, mark the rest open, reply."
  - Open headline rows go to SPD-4 follow-ups, which get 6 searches and 2 minutes.
  - Deep doubles the budgets. Ultra has no total limit, but each agent keeps its own budget.
  - The status line takes "Süre" from `started`.
- **Files.** SKILL.md (budget sentence, plan header, step 7); references/researcher.md; scripts/vafer_check.py (about 6 lines); tests.
- **Effect.** The straggler tail is capped at about 4–5 min per researcher. Budget Tracker suggests about −40% searches at comparable accuracy. Runs vary less from one to the next.
- **Risk.** This reverses b1c91b8's deliberate removal of time budgets (open question 2). Hard rows may stay open more often; the follow-up caps must absorb them. The clock comes from the script, so it cannot drift.
- **Verify.** Longest researcher ≤ 5 min, ≤ 10 searches per researcher, and no more NOT-FOUND headline rows than v0.0.4.

### SPD-8 (should, S–M). Fetch: parallel, cached, race-free, and it keeps tables and PDFs

- **Problem.**
  - `fetch` downloads one URL at a time: 30 s timeout, then a retry. An 8-URL batch took 82 s and made S1 the launch straggler.
  - 21 of 102 URLs were downloaded twice.
  - Parallel researchers lost 14 index rows. A lost "boilerplate" row makes a failed page look valid.
  - The boilerplate rule rejects data tables and hard-wrapped primary texts.
  - Without pdftotext, a PDF is discarded.
- **Evidence.** run-evidence F4 and F5; skill-audit F7 and F8; `toolsecs.py` (the fetch calls took 251 s in total); M3 (the PDF attempts).
- **Change.**
  - A ThreadPoolExecutor with 6 workers, at most 2 per host.
  - 20 s timeout, plus one retry with backoff on 429.
  - Skip URLs that already have an "ok" snapshot.
  - Append the index under a lock file, or keep each page's status in its snapshot header and rebuild the index on read.
  - Judge boilerplate by the characters in text and table lines, not by "3 lines of 80+".
  - When pdftotext is missing, keep the raw PDF and print "pdf saved: read it with the host's PDF reader".
- **Files.** scripts/vafer_check.py (download, fetch_one, cmd_fetch, about 15 lines); tests (FetchTests); references/hosts.md.
- **Effect.** The slowest batch drops from 82 s to about 25 s, about 20 duplicate downloads go away, no rows are lost, and fewer pages fall back to WebFetch with † on primary texts.
- **Risk.** More 429s from a single host (hence the per-host cap). Concurrent writes need the lock.
- **Verify.** Unit tests with the fake opener. In the side-by-side: the longest fetch call ≤ 30 s, index rows equal snapshot files, and no improvised PDF code in the transcripts.

### SPD-9 (should, S). Remove permission stalls: document the allow rules and the Codex flags a run needs

- **Problem.**
  - In Manual mode, WebFetch prompts for each new domain, and shell calls prompt too. Prompts from background subagents surface in the main session, so a run touching about 26 domains and about 160 shell calls waits on a person.
  - The README's Codex `--search` flag is rejected. Without live search and sandbox network, `fetch` fails silently.
  - The measured runs had permissions pre-granted, so this cost is invisible in the 22:53.
- **Evidence.** hosts F6 and F7; skill-audit F2.
- **Change.**
  - README and hosts.md: for research sessions, recommend allow rules for WebSearch, WebFetch and `Bash(python* *vafer_check.py*)`, or auto mode.
  - Codex: `codex -c web_search="live" -c sandbox_workspace_write.network_access=true`.
  - Move the host line into step 1, as a preflight before planning: search mode, subagents, network.
- **Files.** README.md; references/hosts.md; SKILL.md (step 1).
- **Effect.** Unmeasured, but large for Manual-mode users, since every prompt waits for the user. Prevents silent no-fetch runs on Codex.
- **Risk.** Wider permissions are the user's choice: document them, do not enforce them. `allowed-tools` is forbidden by the hygiene test, and it only lasts one turn anyway.
- **Verify.** One run in a fresh Manual-mode session with and without the rules, counting the prompts.

### SPD-10 (should, S). Make reuse work on every shell, so follow-ups start ahead

- **Problem.**
  - `rg -i -l "yalova" .vafer/research/*/plan.md` fails in PowerShell, because the glob is not expanded. Follow-ups on Codex for Windows, or with the PowerShell tool, start from zero.
  - reuse.md seeds every earlier row, even for a neighbouring question.
- **Evidence.** stress-test F6 (probe in `scratchpad/v005-review/rgtest/`); skill-audit F17.
- **Change.**
  - SKILL.md Reuse: `rg -i -l "<folded terms>" .vafer/research --glob plan.md`, with a neutral example.
  - reuse.md separates two cases. "Same question, refresh": seed the rows and re-open volatile facts. "Neighbouring question, borrow": seed only the receipts and the Not-found and Blocked lines that match the new rows.
- **Files.** SKILL.md (Reuse); references/reuse.md.
- **Effect.** Follow-ups reuse receipts and dead ends on every host; the stress test estimates 3–8 searches saved on a Yalova follow-up.
- **Risk.** None notable; text only.
- **Verify.** Run the lookup in PowerShell and in Git Bash, plus one next-day follow-up on the side-by-side run.

### SPD-11 (should, M). Suite packaging for 0.0.5: both skills, one version, one run-folder convention

- **Problem.**
  - Today each skill is installed by copying it.
  - The version lives in SKILL.md metadata, which no host reads.
  - A brainstorm skill that searches on its own would duplicate the research rules and repeat searches that a run folder already holds.
- **Evidence.** hosts F8, F11 and F12; prior-research F7 and F13.
- **Change.**
  - Add `.claude-plugin/plugin.json` (`"name": "vafer"`, `"version": "0.0.5"`) and `.claude-plugin/marketplace.json` (source `"./"`). Codex reads the same files.
  - The version lives only in plugin.json and the README status line.
  - Every module writes `.vafer/<module>/<YYYY-MM-DD>-<slug>/` with a plan.md-style header (`question | as_of | tier | started | status`), so one `rg --glob plan.md` finds earlier work.
  - Brainstorm calls vafer-research at Quick or Standard, with its budget, instead of searching itself.
- **Files.** .claude-plugin/plugin.json and marketplace.json (new); README.md; SKILL.md frontmatter; agents/openai.yaml; tests/test_skill_hygiene.py.
- **Effect.** One install on both hosts; brainstorm sessions reuse saved research; a single version label.
- **Risk.**
  - Naming: a folder named `vafer-research` appears as `/vafer:vafer-research`. Renaming it `research` changes the hygiene test and `$vafer-research`.
  - Codex loading a Claude-format plugin has not been verified live.
  - Cloud sessions do not load local plugins, so keep the copy route.
- **Verify.** Install on both hosts. A brainstorm prompt that needs a fact should trigger a Quick run whose folder lands under `.vafer/research/`.

### SPD-12 (could, S). Let Quick take narrow niche questions, and save its receipts

- **Problem.** Every "recent, niche or local topic" goes to Standard, even with one or two sub-questions. Quick saves nothing, so "go deeper" starts from zero (stress-test F8).
- **Evidence.** SKILL.md:28–29, :33 and :37. The bare arm shows the single-agent floor (5 min, 25 calls). Its errors came from not opening primary pages (run-evidence F12), which Quick already requires.
- **Change.**
  - Quick handles one or two rows that a few opened pages can settle, including recent, niche or local facts. Standard handles three or more rows, a comparison or a written report.
  - With a shell, Quick snapshots its pages in one `fetch --find`, writes plan.md and notes/quick.md, and answers in chat.
  - "Escalate" means offering Standard with the conflicting items as rows.
- **Files.** SKILL.md (tier table and Quick section; needs cuts before the loop); references/reuse.md.
- **Effect.** Narrow niche questions take about 3–5 min instead of 10 or more, and escalations start with receipts.
- **Risk.** A local question that looks narrow can hide conflicts; Quick escalates when it finds one. Adds 1–2 calls. The tier is untested.
- **Verify.** Run two narrow questions, one local Turkish and one recent, as Quick against Standard. Compare time and the judge's claim checks.

### SPD-13 (could, S). One measured model or effort experiment for researchers on Claude Code; no default change

- **Problem.**
  - Researchers spend 49–69% of their time generating, and the host lets the lead pick a model alias and effort per spawn.
  - The judge's errors were all judgment calls, and smaller models drop sharply. DeepSearchQA F1: Haiku 4.5 22.2, Sonnet 4.5 27.9, Opus 4.5 40.2.
- **Evidence.** run-evidence F3; hosts F1 and F16 (docs verified today); external-sweep F6.
- **Change.**
  - After SPD-1 to SPD-5 land, add one arm with researchers spawned at `effort: low` on the same model, and if needed a second with `model: sonnet`.
  - Adopt it for section researchers only if the judge's accuracy stays within 0.5 and research time drops ≥ 25%. The gap-finder and follow-ups stay on the session model.
  - Skip Codex: spawn v2 discourages setting a model.
  - The README can mention fast mode, a user setting, as a way to run faster.
- **Files.** Only if adopted: references/briefs.md (the spawn line); references/hosts.md; README.
- **Effect.** Unknown. Estimated −20–35% researcher wall time if generation runs 1.5–2× faster.
- **Risk.** Lower accuracy and source quality. If adopted, it adds one more choice to every launch.
- **Verify.** The A/B arm above, with the same judge brief.

## Cuts

| Delete or shrink | Why |
|---|---|
| The editor pass, its brief, report.before-edit.md, and `vafer_check.py diff` (about 60 lines plus 5 DiffTests) | 2:43 of serial time for −1.3 words per sentence, which only undid the lead's own rewrite. It detached 6 citations, and the bare-`diff` regression goes with it (M5; run-evidence F7; stress-test F9). |
| The separate gap wave in Standard (step 4) and "The lead does not run the gap wave alone" | Replaced by gap-finder-first and follow-ups. The sentence contradicts mode C (skill-audit F14). |
| "Mark each row" as a barrier before follow-ups (SKILL.md:44) | It caused the 10:25 idle (M1). |
| The lead's full report rewrite in step 5 | It generated 25k characters at least once, and made readability worse (M4, M5). |
| Static rules inside every brief, "paste the short rules", and "put everything it needs in it" (briefs.md:3, :27) | About 14 s of lead output per brief and drift between copies (M7). |
| Two briefs (adjudicator, gap researcher) → one follow-up brief | One concept instead of two waves. |
| "There is no time limit" (SKILL.md:49) | Unbounded stragglers set the wall time (run-evidence F13). |
| WebFetch "for finding and skimming" (SKILL.md:55) | It invited 25 double opens (run-evidence F4). |
| Dispositions for low-severity flags; scripts like `dispo.py` | Bookkeeping that taught the lead to dismiss flags (skill-audit F6). |
| hosts.md:12 (the refused report* write workaround) | Moot once the script writes report.md. |
| The 600-word section cap → a budget derived from the total length (≤ 400 in Standard) | Concatenation then lands at the intended report length (skill-audit F13). |
| Yalova text in style.md's example and in SKILL.md:80 | It contaminated the only benchmark (run-evidence F14), and a clean side-by-side needs it gone. |

## One side-by-side to check SPD-1 to SPD-5

No new infrastructure: the scripts from this review already measure everything.
- **Zero-cost pre-checks:**
  - A blind judge compares the readability of v0.0.4's report.before-edit.md and report.md (decides SPD-2's editor cut).
  - Re-run `check` on the v0.0.4 folder and on `asm_probe/run` with the new rules (SPD-3).
- **Arms:**
  - HEAD v0.0.4 against v0.0.5, both with the lead in a main interactive session (skill-audit F20) and WebFetch allowed for all domains.
  - On Claude Code, optionally the bundled `/deep-research` (external-sweep F1; hosts F13).
- **Questions:**
  - Yalova, after removing Yalova text from the references, so the result compares with 22:53, 362 calls and 8.6.
  - One fresh local-history question of the same shape, for example "Mudanya'nın tarihi". Run each twice if possible, because stragglers vary.
- **Measures:**
  - wall time, tool calls and subagents (`runstats.py`);
  - turns and the share of single-call turns (`speed_turns.py`);
  - time from the last research reply to delivery;
  - the judge's claim-check accuracy (10–12 claims) and source quality;
  - readability (`readab.py`, plus the judge).
- **Pass:**
  - v0.0.5 takes ≤ 11 min and ≤ 180 calls;
  - accuracy ≥ 8.5, source quality ≥ 9 and readability ≥ 8 from the same judge brief;
  - the tail after research ≤ 3 min.

## Guardrails for the other lenses

- Do not add a serial stage after assembly. If sentence-level verification is added (external-sweep F8–F10), run it per section as each section arrives, or as a capped follow-up.
- Do not trade sources for speed. Search time was 655 s of agent time, mostly in parallel; the minutes are in serial phases and turns.
- Every script feature must replace measured agent work. Each one above does: `renumber.py`, `fix1.py`, `dispo.py`, the 98 snapshot reads, the PDF attempts, the 10:25 of waiting. That is the opposite of v0.0.3's evidence store, which added work.

## Open questions for the brainstorm

1. Which time target governs Standard: "about 10 minutes", "at most 2× the bare model on the same question", or the original "at most 1.5× bare" (7.5 min, probably out of reach without cutting depth)? And is "faster than Claude Code's /deep-research with a third of its tool calls" a speed claim you want next to the 5× goal?
2. v0.0.4 dropped time budgets on purpose (b1c91b8). Do you accept a soft budget per researcher (about 8 searches and 4 minutes, with a partial return and follow-ups for open headline rows)? Or do you keep "no limit" and live with straggler swings like 13:39 against 24:00?
3. The editor: cut it everywhere and rely on house-style drafts plus a long-sentence lint, keep it only for Deep and Ultra, or keep it? The zero-cost blind comparison of report.before-edit.md and report.md can decide.
4. Budgets: may vafer_check.py grow from 700 to about 800 lines (assemble, find, parallel fetch, run clock, quieter check), given that `diff` is deleted and each feature replaces agent work? And may style.md become researcher.md, the static rules file subagents read?
5. Models: should researchers always run on the session model, or do you want one measured arm with `effort: low` or `model: sonnet`, adopted only if accuracy holds within 0.5?
6. Quick's reach: should narrow recent, niche or local questions (one or two rows) go to Quick with snapshots and a saved folder (about 3–5 min), accepting less depth than Standard on them?

## Helper scripts and probes

All in `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/2b233dc9-15bf-498e-93c7-9a4c6367ee83/scratchpad/v005-review/`. That is a temporary folder, so copy anything worth keeping.
- `speed_turns.py`: turns, calls per turn, single-call turns, tool versus generation time, per agent.
- `speed_gaps.py`: the largest generation gaps per agent and what followed them.
- `lead_wake.py`: the lead's records between two times (notifications and reactions).
- `outparts.py`, `briefsize.py`: output token parts, and brief and write sizes with times.
- `assembly_overlap.py`: how much of the report was copied from the sections.
- `asm_probe/assemble_proto.py`, `asm_probe/inherit_probe.py`, and `asm_probe/run/` (the concatenated report.md and its check.md).
