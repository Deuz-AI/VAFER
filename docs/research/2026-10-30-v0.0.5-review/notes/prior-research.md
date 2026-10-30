# Prior research digest for v0.0.5

Date: 2026-10-30. Read: the 2026-10-27 SOTA folder (verdict.json and diagnosis.json in full; designs and research-*.json skimmed), the hyperresearch folder (STATUS.md, teardown.md, verified-claims.md, three critiques), the 2026-10-28 architecture panel, the skill at 5ebab1a, and the measured v0.0.4 run folder `C:/Users/VECTOR/AppData/Local/Temp/claude/C--Users-VECTOR-Documents-GitHub-VAFER/e8210f42-5bc4-4715-a0fe-4bc7e2e72a35/scratchpad/t2/v04/.vafer/research/2026-10-29-yalova-tarihi/` (plan.md, evidence.md, check.md, file times).

## Summary

Most of the 2026-10-27 verdict and the 2026-10-28 architecture panel is already in v0.0.4: a short router, tiers with a Quick path, rows that name their record, a fresh gap-finder, the source ladder, page snapshots with a stdlib check, fallbacks, plan-header reuse and a hygiene gate. Six verdict items were reversed on purpose (time budgets, INDEX.md, conditional fan-out, single lead writer, scout batch, eval harness first) and the verifier is held. The run shows what the reversals cost: 22 minutes is 4.4× bare against the project's own ≤1.5× bar, about 9 minutes of it serial work after research ended, and 13 check flags of which one changed the report. Word and line budgets are full. "5×" is defensible only as rates (unsupported figures, follow-up cost, list completeness), none measured against another arm. Codex, lists, follow-ups and computed figures are untested.

## Findings

### F1. The verdict's core is adopted; treat it as settled

ADOPTED (source, then location):
- Router under 1,500 words; done-when, tier table and full Quick path first (verdict add[0], add[1]): SKILL.md:15-37.
- Rows built from the question's atoms that name the record that settles them and end visibly (add[2]; architecture pillar 3): SKILL.md:17, 41.
- Fresh gap-finder that also lists the question's atoms (add[4]; teardown §5 item 6): briefs.md:60-69.
- Primary-record rule, grown into a five-rung ladder with labelled receipts (add[7]; teardown item 7; commit efccf1b): SKILL.md:43, 63.
- Page snapshots and a stdlib check. WebFetch text is never a receipt, since it leaves "at most 2 of 12" exact (add[9]; teardown items 1, 3; pillars 1-2; webfetch-spike.md:26): SKILL.md:51-55.
- NO_WEB reply, modes A-D, host line, Codex search-mode test (add[11]; pillar 7): hosts.md:5-38.
- Reuse that pulls dated receipts and dead ends (teardown item 4; pillar 5): reuse.md.
- Language rule and local record types (add[15]; teardown item 9): SKILL.md:60; briefs.md:12-16.
- House style and high-stakes scope (teardown item 8): style.md; SKILL.md:70.
- Hygiene gate (add[13]): tests/test_skill_hygiene.py.
- All 17 v0.0.3 drops and every hyperresearch (HR) import the teardown refused: commit 032a65d removed 4,384 lines, and nothing runs after the report (SKILL.md:47).

The run supports three of these directly:
- the ladder: source quality 9 vs 3.5 for bare;
- the calendar rule: only v0.0.4 got Rumi 1316 = 1900 (README.md:21);
- the gap-finder: it recovered the 1096 Kibotos omission that v0.0.3's fresh examiner had also found (evidence.md, Method).

**Implication:** change these only on new measured evidence. **Confidence:** high.

### F2. Reversed or held on purpose

| Verdict item | v0.0.4 | Why | Urgency after the run |
|---|---|---|---|
| Time budget in each brief; stop at 70% (add[10], workflow[5]) | "There is no time limit" (SKILL.md:49); a927973 added only 6-10 searches and 8-12 opens per section (briefs.md:18) | b1c91b8: "researchers stop when their assignment is answered". The red team later listed "no time limit" plus Astra's early stopping as a likely cause of uneven depth (critique-redteam.md:145) | More: 4.4× bare. Opus 5.5 guide: teams given a budget kept comparable quality and finished considerably sooner, searching and verifying "a little less" (verdict claim 2) |
| INDEX.md (add[12]) | The plan.md header, written before the first search, is the index (SKILL.md:41, 80) | A run that died mid-wave left no INDEX line (critique-redteam.md:148-151) | Unchanged: reuse untested |
| Fan out only for ≥3 independent sub-questions (add[3]) | Always one researcher per section, 3-6 sections | A floor against uneven depth across Codex runs (teardown item 6; pillar 6) | Unchanged: Yalova fans out under either rule; narrow questions untested |
| Single lead writer (add[6]) | Researchers write sections; one fresh editor, guarded by `diff` (SKILL.md:45-46) | ce8573f, after the first 0.2.0 Yalova report read poorly (style.md's "before" example comes from it) | Keep, but cost it: readability 6.5 → 8.5 (n=1); the edit stage is serial |
| Scout batch, then re-tier (workflow[2]) | "Do not search first" (SKILL.md:41) | Launch in one message (pillar 6) | More (F5) |
| Triggered verifier for ≤8 claims (add[8]) | Held (architecture.md:75-76) | The Opus 5 guide advises against verify subagents | Less: accuracy 8.5; 252/258 figures matched |
| Eval harness before code (add[14]) | One blind side-by-side (README.md:7-23) | Author: product first | Keep rejected; see F11 |
| Drop the "ultra" framing (drop[16]) | Ultra tier is back on request (SKILL.md:31) | The user wants an explicit maximum mode | Low |
| Academic acquisition | Conceded (architecture.md:73) | Topics are rarely academic | Low |

### F3. Partly or not adopted

| Item (source) | Status | Urgency |
|---|---|---|
| Early draft after wave 1 (add[5]) | PARTLY: section drafts are on disk by 12:04, but report.md exists only after the gap wave | Unchanged |
| Gap-finder at "zero added wall time" (add[4]) | PARTLY: its items started a serial second wave | More (F5) |
| Trust the check only at ≥80% flag precision (pillar 2; critique-completeness #2) | PARTLY: advisory and logged, but precision was about 1/13 | More (F6) |
| Computed figures as equations (pillar 2) | Unexercised: "0 equations correct" (check.md) | Unchanged until a computed-figure question runs |
| Counter-evidence search per headline conclusion (teardown item 7) | PARTLY: Ultra only (SKILL.md:44) | Less: conflict handling 8.5 |
| Time as a ratio to bare, per-phase times (teardown item 5; architecture.md:92) | PARTLY: total minutes only (SKILL.md:47) | More (F4) |
| Search budget per run (Standard ≤60, Deep ≤150, inside Claude Code's 200 per session; verdict effort_scaling) | PARTLY: a per-section guide only | Medium; higher for Deep |
| Audit mode: score any arm's report with one fetcher (architecture.md:87) | NOT ADOPTED: the script has only fetch, check, diff | More if any 5× is claimed (F10) |
| Side-by-side on three question types with `/deep-research`, HR light and Codex (teardown item 11; architecture.md:98-114) | PARTLY: one question, one host, one run per arm | More (F12) |
| Spikes 2-5: electricity-question snapshots, Codex on Windows, matcher precision, diff of the uneven Codex runs (architecture.md:116-122) | NOT DONE (no record found; the run gives a rough precision figure, F6) | More for Codex |
| Dual-lens and contested-decision variants; heavy mode (verdict M5) | NOT ADOPTED; the verdict deferred them | Less |
| Real titles in Sources, `Caution:` lines, lateral reading | NOT ADOPTED | Low |

### F4. Time is the guardrail v0.0.4 broke, and much of it is not research

Every prior document set Standard at ≤1.5× bare (verdict effort_scaling; teardown §5; architecture.md:92). v0.0.4 took 4.4× (22 vs 5 minutes) and 1.6× the 0.2.0 draft's 13.5.

File times:
- 11:57:28: run folder;
- 12:02-12:04: five section drafts;
- 12:06: adjudicator;
- 12:08:40-12:10:10: gap-wave sections;
- 12:14: assembled.txt;
- 12:16:41: report.before-edit.md;
- 12:19:11: report.md and check.md.

After research ended at about 12:10, roughly 9 minutes went to:
- assembly and renumbering;
- two check crashes and a patched copy (since fixed in 575396a);
- 13 dispositions;
- the editor and a re-check.

The a927973 fixes are unmeasured.

**Implication:** cut the serial tail and the second wave before touching breadth. Log phases from file times, merge serial stages, and test an elapsed-time signal for the lead. The extra 8.5 minutes over the draft bought no measurable quality (F8). **Confidence:** medium (one run; file times bound phases loosely).

### F5. The gap-finder pays, but in parallel it produced a serial second wave

All 12 plan rows were `[prior]`, since there was no scout batch. The gap-finder's items triggered the 3-researcher gap wave, about 6 of the 22 minutes (evidence.md, Method). Those items were Kibotos 1096, the 1915 deportation, the 1923 exchange and the Osmangazi bridge. "Zero added wall time" holds only when no gap wave follows.
**Implication:** test the gap-finder (at most 5 searches) before launch, so that its items become wave-1 rows. This might trade 1-2 minutes for a whole wave. **Confidence:** medium-low; it is a hypothesis.

### F6. The check verifies figures well, but its flags cost more than they find

252 of 258 figures matched. Of 13 flags, 9 were false alarms, 3 derived calendar bounds, and 1 produced a † for a Kibotos date cited only to Wikipedia (check.md F1-F13). a927973 fixed sentence splits such as "Cmd." Three false-alarm classes remain:
- figures in the "B says" column of "Ayrışan kaynaklar", which the report's own ruling rejects (F10-F12);
- "not found" sentences that name the unsupported figure (F1, F2, F7, F13);
- Roman-numeral centuries (F4).

Against the ≥80% bar, precision was about 8%, or 31% counting derived flags as correct.
**Implication:** downgrade these three classes, and require dispositions only for medium- and high-severity flags. The script sits at its 700-line cap (tests/test_skill_hygiene.py:19). **Confidence:** high on the counts, medium on the fix.

### F7. Instruction and script budgets are full

Usage against the hygiene test's own caps:
- SKILL.md body: 1,431 of 1,500 words;
- text before the loop: 374 of 400;
- briefs.md: 927 of 1,000;
- reference files: 4 of 4;
- vafer_check.py: 700 of 700 lines.

The verdict's top risk is ceremony creeping back, "as it did in every 0.0.x version". Critique-completeness #11 asks for a word cost per item.
**Implication:** every v0.0.5 addition needs an offsetting deletion; rank changes by gain per word. The brainstorm skill needs its own files, since overlapping modules degrade rule-following (verdict risks[11]). **Confidence:** high.

### F8. What the blind test can and cannot support

The test used one question, one run per arm and one judge, with a holistic 0-10 score backed by 10-12 claim checks. The prior research calls single runs and single-judge holistic scores anti-patterns. LiveResearchBench saw run-to-run swings of over 50 points under direct rating, and DeepResearch Bench found that isolated scoring gives "uniformly high scores". The gap over bare (8.6 vs 5.8) is large and backed by claim checks (README.md:22). The gap between versions (8.6 vs 8.1) is not evidence. The lead also ran as a subagent (evidence.md line 1), not in the interactive mode that architecture pillar 6 flagged.
**Implication:** judge v0.0.5 on claim checks and time, and run each arm twice before claiming a gain between versions. **Confidence:** high.

### F9. hyperresearch: quality drivers and costs

No component is isolated: there is no ablation, only one sample report (58.3 RACE, one query). Plausible drivers (teardown.md:20-32):
- 55-80 sources read in full by subagents (Bash output is cut near 30K characters);
- curated notes per source;
- a fresh single writer;
- a quote-integrity gate;
- an instruction critic;
- one step skill at a time, against compaction.

Its adversarial pre-draft work is only partly delivered, and its cite-check passes "grew 5%" against a 25% claim and trusts quotes the fetchers wrote. The vendor's own hosted path has moved to an evidence map, a one-pass writer and a figure-level claim check (teardown.md:32). On DRACO that hosted product ties Claude Research 5-5 on ten vendor-chosen tasks (p≈0.31).

Costs:
- 30-40 minutes for light and 1.5-2.5 hours for full (estimates);
- 70-200 searches and 35-60 spawns per full run;
- about $215 API-equivalent for one full run (issue #92);
- a fresh Chromium per URL;
- about 7K tokens always loaded;
- no corpus reuse.

**Implication:** VAFER now covers HR's verified weak point, page-level figure checks. HR still leads on breadth (v0.0.4 cited 36 sources) and on academic acquisition. The time edge has shrunk: 22 minutes against HR light's estimated 30-40, where the architecture claimed "about a tenth". The teardown's §4 table describes 0.1.0-alpha and is stale. **Confidence:** high on mechanisms (85 claims checked, none refuted; STATUS.md:21); low on HR's output, which nobody here has run.

### F10. What "5×" can honestly mean

Bounded quality scores cannot improve 5×. Expect 0-5 points over bare, more on lists, post-cutoff and Turkish-local tasks (teardown.md:90). Defensible targets are rates (critique-redteam.md:31-36; architecture.md:83-96):
- **Unsupported claims:** figures, dates and quotes not marked † at no more than 1/5 of HR light's rate and 1/3 of bare's, with at least bare's count of supported claims, because fewer claims is gaming.
- **Follow-ups:** searches per follow-up on a reuse hit at no more than 1/5 of a fresh run's, with accuracy within 2 points.
- **Lists:** missing rows in lists of 20+ at no more than 1/5 of bare's.

Coverage spread across runs is a floor, not a 5× target. Time is no 5× axis, because bare beats both. So far, only VAFER's own 252/258 has been measured. No arm has been measured with the same instrument, and no follow-up or list question has been run.
**Implication:** in the brainstorm, choose one or two rates and build only their instrument. **Confidence:** high on the framing, low on reachability.

### F11. Rubrics and benchmarks the prior research found useful

- **Binary rubric items from expert sources, graded one at a time.** ResearchRubrics: binary agrees about 20 points better than ternary. DRB-II: recall spans 23-40 while presentation spans 75-92, and a key must score ≥90% on its own source.
- **Claim-level citation checks with one shared fetcher**, reported with the supported-claim count. DeepResearch Bench FACT is the model. Support falls as tool calls rise: Opus 4.6 went from 80% to 58% (arXiv 2605.06635).
- **Two judge families, judging chunks rather than whole reports.** RuVerBench: 91-95% accuracy, with judge errors overlapping only 16%. REFLECT: holistic judges catch under 55% of planted failures.
- **Pairwise or reference-relative judging** for overall quality. RACE agrees with experts 71% of the time, against 59% for a plain prompt.
- **WideSearch row-F1** for lists, plus probes: pro and con framings (DeepTRACE), false premises, blocked sources.
- **Benchmarks near their ceiling:** DRACO (bare Opus 5.5 scores 87.4%, and the judge moves scores 10-25 points) and BrowseComp (about 91%). Use them only if a pilot shows headroom.
- **Audited answer keys:** one-shot expert keys were about 61% accurate (DeepFact).

**Implication:** the v0.0.5 kit needs no harness:
- a key written before the runs, with 15-40 binary items and 3-5 negative ones;
- every cited figure checked with one fetcher;
- row-F1 for a list question;
- time and tool calls from the logs.

**Confidence:** high on the sources, medium on transfer.

### F12. The untested areas are where the research expects the gains

The verdict expects the largest gains on lists, post-cutoff and Turkish-local tasks, and it named Codex with GPT-6 Astra the first host (open_decisions[0]). v0.0.4 has been tested only on Turkish-local history, on Claude Code. Untested:
- the table variant (briefs.md:56-58);
- reuse;
- equations for computed figures;
- Codex with cached search and no shell network (hosts.md:21-25);
- how Astra handles a more procedural skill. OpenAI says detailed recipes hinder Astra (verdict claim 11).

**Implication:** add a list question with a frame key and the TR/GR/BG electricity bill, repeat one question on Codex, and test one next-day follow-up. **Confidence:** high.

### F13. Decisions still open for the brainstorm

Still open across STATUS.md:33-39, architecture.md:124-131 and the verdict's open decisions:
- which 5× the user means;
- which host comes first;
- whether the user-level deny on WebSearch and WebFetch is deliberate (webfetch-spike.md:5);
- whether memory stays per project folder or becomes a user-level library;
- whether HR full joins the test;
- whether VAFER defers to `/deep-research` on Claude Code if that wins one-shot reports.

The verdict also has Brainstorming call the Quick or Standard tier rather than copy its rules (memory_and_plan_integration).
**Implication:** settle these first, and have the brainstorm skill call vafer-research rather than duplicate it. **Confidence:** high.
