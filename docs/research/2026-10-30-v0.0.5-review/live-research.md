# Live side-by-side, research (PLAN.md Task 12)

Date: 2026-10-31. Question, verbatim: "Mudanya'nın tarihi hakkında detaylı bir araştırma raporu istiyorum."

## Pass criteria

These were fixed and committed before any arm ran.

| Criterion | Pass |
|---|---|
| Wall time and subagents, v0.0.5 | at most 13 min, at most 8 subagents |
| Judge accuracy | v0.0.5 at least v0.0.4 |
| Overturned negative verdicts | at most 1 |
| Readability | at least 8 of 10 |
| Open high or medium flags in check.md | at most 5, with precision at least 50% |
| Last research reply to delivery | at most 3 min |

## Arms

All arms ran at the same time, on Claude Code 2.1.316 with the model pinned to Opus 5.5 (`--model claude-opus-5-5`, at the effort the author's settings give it: medium). Each ran headless (`claude -p`) in its own temp folder outside any git repository, with the author's other plugins off (superpowers, firecrawl, playwright, frontend-design, supabase, skill-creator, usage-plus), and with `--permission-mode auto`. The author's user-level skills stay visible to every arm.
- **v0.0.5:** the plugin loaded from the repository with `--plugin-dir`, prompt `/vafer:vafer-research <question>`.
- **v0.0.4:** `skills/vafer-research` from branch `vafer-research-v0.0.4`, copied into the arm's `.claude/skills/`, prompt `/vafer-research <question>`.
- **Bare:** no skill, the question alone.

**Deviation from the plan's command:** the arms use `--permission-mode auto` instead of `acceptEdits` with an allow list. Under the allow list, any command outside it is refused in a headless run, and v0.0.4's commands differ from v0.0.5's. Auto mode treats both versions alike.

## Run history

The runs took place on 2026-11-01. The author's 5-hour Claude usage limit interrupted the first two attempts.

1. **12:22.** All three arms started together. The bare arm finished in 7.3 min, before the limit. At about 12:32 every API call stalled. The two VAFER leads were left waiting, and headless `claude -p` stopped v0.0.5's two follow-ups 10 minutes after the lead's last turn. **We keep the bare arm's result from this attempt.**
2. **14:24.** Only v0.0.5 and v0.0.4 ran. Both stopped at about 7.5 min with "You've hit your 5-hour limit".
3. **16:33.** v0.0.5 and v0.0.4 ran together after the limit reset, with the skill at 84f1406. Both finished.
4. **17:07.** v0.0.5 ran once more after 66fbfbe, which addresses the failed time and flag criteria (step 7 allows one re-run).

The bare arm used the author's docs skill and published its report as a private Claude Docs page in the author's claude.ai account. Its text was rebuilt from the run's tool calls for judging.

## Results

| | v0.0.5 (attempt 3) | v0.0.5 (re-run) | v0.0.4 | Bare |
|---|---|---|---|---|
| Wall time | 14.3 min | 17.2 min | 23.8 min | 7.3 min |
| Subagents | 8 | 8 | 10 | 0 |
| Tool calls (lead + subagents) | 55 + 209 | 47 + 202 | 47 + 275 | 45 |
| Cost (API-equivalent) | $11.59 | $11.83 | $15.07 | $2.17 |
| Last research reply to delivery | 4.8 min | 4.5 min | 2.0 min | — |
| report.md, whole file | 3,730 words (body 2,123) | 3,724 words (body 2,127) | 3,425 words | 2,435 words |
| Figures checked by the script | 216 | 232 | 334 | — |
| High or medium flags to answer | 23 | 37 | 36 | — |

In the first v0.0.5 run, the gap-finder took 1.1 min and the four section researchers 2.9–4.3 min. The three follow-ups started as replies arrived and took 2.0–4.0 min each. Most of the overrun came after the last reply: the lead folded in the follow-ups, then ran check five times and assemble three times while it answered 23 flags.

### Blind judges

Two fresh judges each read three reports as x, y and z. Judge 1 saw attempt 3's v0.0.5 report, and judge 2 saw the re-run's. Both got the same v0.0.4 and bare reports.

Each judge opened the cited pages and checked 14–16 claims per report. Scores are out of 10, in the order accuracy / source quality / conflict handling / readability / overall.

| Judge | v0.0.5 | v0.0.4 | Bare | Ranking |
|---|---|---|---|---|
| 1 | 8 / 8 / 8 / **8** / 7.9; 13 supported, 1 wrong; 0 overturned | **9 / 9 / 9** / 7 / **8.7**; 12 supported, 1 unsupported, 2 unverifiable; 2 overturned | 6.5 / 4 / 5.5 / 8 / 6; 12 supported, 2 wrong; 3 overturned | v0.0.4, v0.0.5, bare |
| 2 | 8.5 / 8.5 / 7.5 / 7.5 / 8.5; 12 supported, 2 wrong, 1 unsupported; 2 overturned | **9 / 9 / 9.5** / 7 / **9**; 13 supported, 1 wrong; 0 overturned | 7 / 5 / 5.5 / 8 / 6.5; 11 supported, 2 unsupported, 1 wrong; 0 overturned | v0.0.4, v0.0.5, bare |

The judges' main points:
- **v0.0.5**
  - It rests mostly on academic and official sources.
  - Attempt 3 corrected the popular 1661 mosque date to 1560–61 and confirmed the 17 June 1892 railway opening.
  - Attempt 3 put a mübadil total in its summary that the cited paper itself calls unreliable.
  - The re-run doubted two values (44 BC and 14 October) that academic papers settle.
- **v0.0.4**
  - It found more of the academic literature: archive-based demography and both armistice papers.
  - It was the most precise of the three reports.
  - It was the hardest to read.
- **Bare**
  - It reads well.
  - It rests on Wikipedia and Küre and repeats weak dates as fact.

### Flag precision

A separate agent labelled every high or medium flag real or false. A lead-only flag counts as real even when the lead later marked the claim with †.

| Run | Flags | Real | Precision |
|---|---|---|---|
| v0.0.5 (attempt 3) | 23 | 16 (all the lead-only flags) | 70% |
| v0.0.4 | 36 | 17 | 47% |

All 7 false flags in v0.0.5 are number-mismatch or uncited flags on values that are derived or not in the report: a Hijri year converted to a Gregorian one, a date computed from a cited date, a split sentence, and a century inside a "not found" statement.

The re-run raised 37 flags: 28 lead-only and 9 number-mismatch. They were not labelled. Its researchers marked weak claims with † as 66fbfbe asks, but check still flagged sentences that carry a †.

74a3772 stops that. When check is re-run on the two delivered v0.0.5 reports, the flags fall from 23 to 7 and from 37 to 18. Those reports also carry the daggers the lead added, so a live run will show a smaller drop.

### Pass criteria

| Criterion | Attempt 3 | Re-run |
|---|---|---|
| At most 13 min, at most 8 subagents | Failed: 14.3 min, 8 subagents | Failed: 17.2 min, 8 subagents |
| Judge accuracy at least v0.0.4's | Failed: 8 against 9 | Failed: 8.5 against 9 |
| At most 1 overturned negative | Passed: 0 | Failed: 2 |
| Readability at least 8 | Passed: 8 | Failed: 7.5 |
| At most 5 open high or medium flags, precision at least 50% | Count failed (23); precision passed (70%) | Count failed (37); not labelled |
| At most 3 min from the last research reply to delivery | Failed: 4.8 min | Failed: 4.5 min |

### Codex Quick smoke

These runs used codex-cli 0.166.0 with `-c web_search="live"`, and the skill sat in the project's `.agents/skills/`. The prompt was `$vafer-research Quick: TÜİK'in Ekim 2026'da açıkladığı yıllık TÜFE enflasyonu yüzde kaç?`.
- **Answers:** all three runs answered 29.73%. They dated the figure correctly: announced on 5 October and covering September 2026. They took the number from the official SBB page, because TÜİK's own page needs JavaScript.
- **Search mode:** the first two runs (82 s and 91 s) did not name the mode in the answer. After 84f1406, which probes with today's date and names the mode beside the checked date, the third run (69 s) ended with "*Kontrol: 1 Kasım 2026 · canlı arama.*".
- **Not run:** a Standard run on Codex.

### Deviations from PLAN.md Task 12

- **Number of runs.** Step 3 asks for each VAFER arm to run twice when the first pair finishes within 30 min. v0.0.4 ran to the end only once: the usage limit stopped its first two attempts, and the author's quota was the constraint. v0.0.5's second run is the step 7 re-run after a fix, not a plain repeat.
- **Measurement.** Step 4 names `tools/runstats.py` and `tools/speed_turns.py`. Both read the October session layout. Wall time, subagents, tool calls and the tail after the last reply were instead taken from each headless run's session transcript and subagent files.

## Conclusion

On this question v0.0.5 is faster and cheaper than v0.0.4: 14–17 min against 24, $11.6–11.8 against $15.1, and 8 subagents against 10. Its flags are fewer and more often real. Both blind judges still ranked v0.0.4's report above it on accuracy and overall: 8 and 8.5 against 9, and 7.9 and 8.5 against 8.7 and 9. Both VAFER versions clearly beat the bare model on accuracy and source quality.

The time target of 13 min was not met. Most of the overrun is the lead's serial work after the last reply.

The depth v0.0.5 lost came with the gap-wave researchers and the editor that it removed. On this run, v0.0.4's extra searching found the academic papers that settle two of the values v0.0.5's re-run left in doubt.

Next steps for v0.0.6:
- Measure 74a3772 live.
- Test whether one late gap researcher, spawned as the sections return, buys back the missing depth within the time target.
