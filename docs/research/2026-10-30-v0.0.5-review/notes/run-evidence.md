# Run evidence: how vafer-research behaved in real runs

Date: 2026-10-30. Sources: the 2026-10-29 three-arm test (`t2/`), the first live run (`yalova/`), session transcripts and commits aeb57d9, ce8573f, 575396a and a927973. Run-folder paths are relative to `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/e8210f42-5bc4-4715-a0fe-4bc7e2e72a35/scratchpad/`. Bare `file:line` references (report.md, notes/, sections/, conflicts.md, evidence.md, check.md, pages/) are in `t2/v04/.vafer/research/2026-10-29-yalova-tarihi/`. `SKILL.md`, `style.md` and `vafer_check.py` refer to repository HEAD (5ebab1a). Transcripts are `agent-<id>.jsonl` in that session's `subagents/` folder. Helper scripts and outputs (`runstats.py`, `busy.py`, `overlap.py`, `snapfiles.py`, `readab.py`, `out/`) are in `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/2b233dc9-15bf-498e-93c7-9a4c6367ee83/scratchpad/v005-review/`.

Arms: `t2/judge/X.md`, `Y.md` and `Z.md` are the blinded reports, not the judge's notes. Each is byte-identical to one arm's `FINAL.md`: X is the 0.2 arm, Y bare, Z v0.0.4. The judge's notes are the last message of `afb4b61ca239b5b72` (09:25:34Z). The skill copies match t1 = 178bd76, t2/v02 = aeb57d9 and t2/v04 = ce8573f. Every arm ran claude-opus-5-5 at medium effort.

## Summary

The v0.0.4 run took 22:53: research waves 10:16 (45%), the lead's work after research 9:32 (42%), planning and briefing 3:05 (13%). The lead sat idle for 10:25. The gap wave waited about 5 minutes for the slowest researcher, although the gap-finder had named its items at minute 3. The run made 362 tool calls (55 lead, 307 subagents) and 12× the bare arm's output tokens. Half of the 73 snapshots were never cited, and parallel fetches lost 14 rows of `pages/index.tsv`. Two of the judge's three faults share one cause: a value seen only in a snippet was called "unsourced". The check flagged both sentences and the lead dismissed both flags. The editor added little readability and detached 6 citations. Commits 575396a and a927973 fix the crashes, the diff and the flag count, but not the timing, rejection or fetch-race problems. The tested skill contained Yalova examples.

## Findings

**F1. Research is less than half of the wall time.**
Evidence (lead transcript `ab569b7fdce2cbf4b`, local time):

| Phase | Ends | Duration |
|---|---|---|
| Read skill, create the folder | 11:57:27 | 0:26 |
| Write plan.md (no search) | 11:57:43 | 0:16 |
| Write six briefs, spawn the launch wave | 11:58:57 | 1:14 |
| Launch wave runs (S1 finishes last, after 6:03) | 12:04:02 | 5:05 |
| Write conflicts.md, adjudicator brief and 3 gap briefs | 12:05:11 | 1:09 |
| Gap wave runs (G2 finishes last, after 5:25) | 12:10:22 | 5:11 |
| Assemble (includes 1:31 rewriting the whole report after a refused write) | 12:14:58 | 4:36 |
| Check: 2 crashes, a patch, 41 flags, fixes | 12:16:40 | 1:42 |
| Editor | 12:18:26 | 1:46 |
| diff, re-check (1 crash, 18 flags), 6 citation fixes | 12:19:23 | 0:57 |
| Deliver | 12:19:54 | 0:31 |

The 0.2 arm (`affe8cbfcbebb9c08`): one research wave of 5:44, then 6:13 (including 1:28 rewriting its report).
Implication: the work after research and the serial second wave are the biggest levers, not search counts.
Confidence: high.

**F2. The gap wave and the adjudicator waited for the slowest researcher.**
Evidence:
- The gap-finder replied at 11:59:47 (`ac1d2b7f239f64f6c`). Its list already had every item g1–g3 later covered: Kibotos 1096, the Nicaea period, 1915, the 1923 exchange, prehistory, Osmangazi and the 2025 population (evidence.md:12).
- g1–g3 were spawned at 12:04:40–12:05:11, after S1 finished at 12:04:02.
- S2 had already worked out the Rumi 1316 conversion (notes/s2.md:34) when it finished at 12:02:50. The adjudicator for that question was spawned at 12:04:25.
- HEAD SKILL.md:43–44 still runs the gap wave after "Mark each row".

Implication: spawn gap researchers as soon as the gap-finder returns, and an adjudicator as soon as its conflict arrives. The gap wave would have ended near 12:05:30, not 12:10:22.
Confidence: high that the wait happened; medium on the size of the saving.

**F3. Where the tool calls and tokens went.**
Evidence (`runstats.py`, `out/summary.txt`):

| | v0.0.4 | 0.2 | bare |
|---|---|---|---|
| Wall time | 22:53 | 13:39 | 4:59 |
| Agents | 1+11 | 1+5 | 1 |
| Tool calls | 362 (lead 55) | 206 (lead 56) | 25 |
| WebSearch | 99 | 68 | 5 |
| WebFetch | 41 | 0 | 11 |
| Snapshot URLs requested (unique) | 102 (81) | 87 (81) | 0 |
| Shell reads of snapshots (grep, sed) | 103 | 75 | 3 |
| check runs (failed) | 10 (3) | 5, four via a wrapper (2) | 0 |
| Output tokens | 231.7k | 148.6k | 19.4k |
| Cache-read tokens | 27.4M | 17.8M | 1.2M |

- Researchers spent 49–69% of their wall time generating text, not waiting on tools (`busy.py`).
- Searches per researcher: S1 8, S2 11, S3 4, S4 12, S5 11, G1 12, G2 15, G3 17.

Implication: cost comes from agent count and generation; fewer phases save more than tighter search caps.
Confidence: high.

**F4. Pages were opened twice, and fetched more than once.**
Evidence (`overlap.py`):
- 25 of the 34 unique WebFetch URLs were also snapshotted.
- 21 of the 102 fetch URLs were repeats. The 0.2 arm made no WebFetch calls and had 6 repeats; its researchers read pages by grepping snapshots.
- `fetch` downloads one URL at a time (30 s timeout, second try on 403/429; `vafer_check.py:185–201, 232–244`).
- SKILL.md:55 sends WebFetch "for finding and skimming", which invites the double open.

Implication: snapshot first and read the snapshot, skip already-fetched URLs, and download in parallel.
Confidence: high on the counts. Low on the time saved: S1's slowest calls (an 82 s fetch, a 75 s WebFetch) delayed the wave only 32 s, because the next researcher finished just before it.

**F5. Snapshots fetched against snapshots cited, and a race on the index.**
Evidence (`snapfiles.py`):
- v0.0.4: 73 snapshot files and 36 cited sources. Every cited source has a file, and 37 files (50%) were never cited. The 0.2 arm: 75/40/35 (46%). The first live run: 78/44/34 (43%).
- `pages/index.tsv` is missing 14 of the 73 files (0.2 arm: 13 of 75; first live run: 27 of 78).
- Cause: `cmd_fetch` reads the index, downloads, then rewrites it whole (`vafer_check.py:236–243`). Example: S5's batch (12:00:51–12:01:39) added dergipark 1754677 and the dspace file. S1's 82 s batch had read the index at 12:01:12 and rewrote it at about 12:02:34 without them.
- `load_snapshots` falls back to file headers, so a lost "empty" or "boilerplate" row makes a failed page look like a valid snapshot.

Implication: use an append-only index or a lock, and store the status in the snapshot header. HEAD does not fix this.
Confidence: high.

**F6. The lead rebuilt chores by hand.**
Evidence:
- `t2/v04_tools/` holds the lead's scripts: `renumber.py` (turns URL citations into [n]), `fix1.py` (28 citation insertions), `dispo.py` (flag dispositions) and a twice-patched `vafer_check_patched.py`.
- check ran 10 times. Three runs crashed: `KeyError 'bi̇n'` twice (the first sed patch failed) and `InvalidOperation` once. The 0.2 arm hit the same two crashes.
- The harness refused `report.urls.md` ("Subagents should return findings as text…"), so the lead regenerated the whole 24,674-character report. The 0.2 arm (22,942 characters) and the first live run lost time the same way. This is a test-setup artifact: the lead ran as a subagent.

Implication: move renumbering into the script, run the lead as the main agent in tests, and write the draft under a neutral name.
Confidence: high.

**F7. The editor made a small readability gain and created a real risk.**
Evidence:
- Words per sentence, from `readab.py`: 12.3 in report.before-edit.md and 11.0 after the editor. Sentences over 25 words: 6, then 3. The 0.2 arm had 16.5 words per sentence and 19 long sentences; the bare arm 14.6 and 19.
- The editor said "Every number and every [n] marker matches" (`a9721ec15809ecddb`), and `diff` printed "clean" (12:18:29).
- The re-check then found 6 sentences whose citations the editor's splits had detached.
- The judge's readability praise ("sentences are short… tables are clean") and its complaints about X (density, untranslated English, the "Source check" header) concern things the house-style drafts and the evidence.md split had fixed before the editor ran.

Implication: in the side-by-side, try a run without the editor, or with a sentence-length lint. If the editor stays, keep the detached-citation diff from a927973.
Confidence: medium, because nobody scored the pre-edit draft.

**F8. What the judge rewarded and penalized** (scores for accuracy / coverage / sources / conflicts / readability / usefulness).

| Arm | Scores | Judge, verbatim |
|---|---|---|
| Z, v0.0.4 | 8.5/8.5/9/8.5/8.5/8.5 | "goes to primary sources (Socrates, Procopius, Cmd.1478, the RG text, the district earthquake table). It solves the hamam date by reasoning X and Y missed… Its sentences are short and its tables are clean. Weak spots: it wrongly dismisses 4.80 m, overstates "27 köy" as unsourced, and failed to find law no. 1533." |
| X, 0.2 | 8/8/9/9/6.5/8 | "best legal and administrative precision (Kanun 1533, KHK lists) and the best catch on "795 vs 7.954". It loses on readability: it is dense, quotes English untranslated and opens with a "Source check" header full of jargon." |
| Y, bare | 5/7.5/3.5/5.5/8/5 | "reads smoothly but has no inline citations. It gives the province a death toll that only covers nine mahalles, and its commission membership and dates are wrong" |

The judge marked Z's 1997 provincial population (163.916) as "?". The cited page has that figure (snapshot `pages/1a198455ec12.txt`, lines 171 and 203), so this is a judge miss.
Implication: the judge is useful but not exact; 0.5-point gaps are noise.
Confidence: high.

**F9. The errors that survived into v0.0.4.**
Evidence:
- (a) **4.80 m.** report.md:176 says "B'nin dayanağı bulunamadı" (no basis found for B). The judge: "Valilik and KTB both give 4.80 m." S4's own draft had said "Kaynaklar ayrışıyor" (sources differ; sections/s4.md:19). The lead's verdict was "drop 4.80 | not opened" (conflicts.md:19).
- (b) **27 villages.** report.md:114 says no primary source was found, and :174 says "27 rakamının kaynağı yok" (the figure has no source). S3 had opened the Wikipedia page, labelled it a lead (notes/s3.md:24) and never followed its footnote. The judge: "cited to Gingeras on Wikipedia".
- (c) **Law 1533 missing.** S4 ran 6 queries aimed at the 1929 law and logged it as not found (notes/s4.md:28). The 0.2 researcher searched `"1533" … kanun 1929` from memory and found Resmî Gazete 1366. The first live run also had Law 1533.

Implication: open the page behind a value before rejecting it, cite that page in the "Ayrışan kaynaklar" table, and write "not checked" rather than "no source". Put `[prior]` candidate values into briefs as search terms.
Confidence: high.

**F10. Which check flags were real catches and which were false alarms.**
Evidence:
- Final check.md, 13 flags: 1 real catch (F3, lead-only, resolved with †); 3 derived calendar bounds (F5, F8, F9); 9 false alarms. Two of those are checker gaps: F4 (Roman numeral "XVI.") and F6 (split at "Cmd.", fixed in a927973). Seven are numbers mentioned only to reject them or list them as unknown (F1, F2, F7, F10–F13).
- F7 (report.md:114) and F10 (:176) flagged the very claims the judge called wrong; `t2/v04_tools/dispo.py` lines 11 and 13 dismissed both.
- Before the editor: 41 flags (17 uncited, 9 uncited table rows, 14 mismatches, 1 lead-only). Adding a citation to an already-snapshotted page cleared 28: real traceability gaps, no factual errors. One more was cleared by rewriting "03.02" as "3:02" to match the source.
- The 0.2 arm's 8 final flags were all false alarms: number words ("sixth", "Sekiz yüz"), Roman numerals, OCR spacing, URLs cut at "(" by `URL_RX` (`vafer_check.py:26`).

Implication: the check is a traceability tool and caught no factual error in this run. Cut its noise and give rejected values their own syntax. Do not let the lead dismiss conflict-table flags without opening the source.
Confidence: high.

**F11. The calendar rule fixed the bath date.**
Evidence:
- The judge on the bath repair year: "Z is right; X and Y are wrong."
- The 0.2.0-alpha skill got it wrong in both runs. The first-run judge: "B copies TDV's '1316 (1898)'."
- S2 computed the correct year (notes/s2.md:34). The adjudicator confirmed it in 1:59, off the critical path (notes/adj1.md).

Implication: keep the calendar rule in the briefs, and keep adjudicators running in parallel.
Confidence: high.

**F12. What the bare model did better.**
Evidence:
- It finished in 4:59 against 22:53 (4.6× faster), with 25 tool calls against 362 and 12× fewer output tokens.
- Readability: 8 against 6.5 for the 0.2 arm (v0.0.4: 8.5). In the first live run, 8 against 7: "A flows better", with "broader coverage of the 1930s" (`a45b0f6660286003a`).
- It had no inline citations in either test, and it repeated Wikipedia errors in both: commission dates and members, the scope of the 1999 death toll, the "1930" district date and "American" officers.

Implication: the skill earns its accuracy and source-quality gains, but it costs 4–5× the time.
Confidence: high.

**F13. Wall time follows the slowest researcher, and it varies a lot.**
Evidence:
- The same 0.2.0-alpha design took 24:00 in the first live run and 13:39 in the second test.
- In the first live run, R4 alone took 10:22 (76 calls, 20 searches, 15 fetches) while the lead waited 10:23.
- The 6–10 searches guide in a927973 has not been measured.

Implication: one run per arm cannot rank speed. Design for stragglers, with a deadline or partial return, not for average effort.
Confidence: medium.

**F14. Limits on how far the results can be trusted.**
Evidence:
- The v0.0.4 copy under test had a Yalova example in briefs.md (ce8573f:34–36: the occupation section, Cmd. 1478 and starting queries). a927973 removed it.
- style.md:22–28 and SKILL.md:80 in HEAD still contain Yalova text. report.md:5 nearly matches style.md:26.
- One question, one run per arm, one model judge (its WebFetch was denied; it used curl).
- The bare arm's prompt did not have the "use subagents" line.

Implication: remove Yalova from the references and run the side-by-side on a different question.
Confidence: high.

**F15. Which fixes address which problems.**

| Problem | Commit | Status |
|---|---|---|
| Roman-numeral and abbreviation splits; written-out numbers; "ok" on empty, boilerplate and .doc pages; check-line placement; lost dispositions; WebSearch summaries (from the first live run) | aeb57d9 | Fixed; did not recur except for Roman-numeral centuries |
| Crashes on "BİN" and on huge numbers | 575396a | Fixed; covered by unit tests only |
| "13 flags open" after every flag was answered; splits at "Cmd." and ".³"; editor detaching citations while diff stayed clean; check run before the editor; relative script path; Yalova example in briefs.md; vague gap trigger; no effort cap; check line written into report.md | a927973 | Fixed, but not measured in a run |

Not addressed: the serial gap wave and adjudicator (F2); duplicate opens and sequential downloads (F4); the index race (F5); hand-built chores and the editor's cost (F6, F7); rejecting unopened values and self-dismissed flags (F9, F10); check noise from Roman-numeral centuries, number words, URLs with "(", clock times and rejected numbers (F10); `[prior]` values unused as queries (F9); the 12× token cost (F3); Yalova text in style.md (F14).
