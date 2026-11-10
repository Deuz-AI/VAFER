# vafer-deep-research 0.1.0: evaluation record

Date: 2026-11-10. Host: Claude Code 2.1.322 on Windows, Python 3.15. Every research agent, writer and judge ran on Claude Opus 5.5. The protocol was written before the first research run. Raw material (protocol, prompts, reports, run folders, judge output) is in the ignored `work/deep-research-eval/` folder.

## Question

Does `vafer-deep-research` at standard depth give at least twice the verified information of Claude Code's built-in `/deep-research`, on the same question and model, without being less accurate?

## Arms and questions

| Arm | Command |
|---|---|
| Baseline | `claude -p --model claude-opus-5-5 "/deep-research <question>"` in an empty folder |
| Treatment | `claude -p --model claude-opus-5-5 "/vafer-deep-research <question>"` in a folder with both VAFER skills installed |

One run per arm per question. Neither question was used while the skill was written.

- **q1:** İznik'in (antik Nikaia) tarihi: kuruluşundan Cumhuriyet dönemine kadar önemli dönemler, olaylar ve tarihleriyle ayrıntılı bir araştırma raporu hazırla.
- **q2:** Sodyum-iyon bataryalar 2026 itibarıyla ne durumda? Başlıca üreticiler, ticari ürünler, enerji yoğunluğu, maliyet, güvenlik ve lityum-iyon (LFP) ile karşılaştırma içeren ayrıntılı bir araştırma raporu hazırla.

## How the reports were judged

The four reports were frozen and copied as `report_A.md` and `report_B.md` into a folder that held nothing else. The assignment was fixed in the protocol (q1: A is the baseline; q2: A is the treatment). The judges were fresh agents with web access that were not told what the two systems were.

1. One extractor listed the distinct, question-relevant atomic claims of both reports under one rule; a fact counts once per report.
2. For each report a verifier checked 15 claims, evenly spaced through the list, against the cited source or the best source it could find.
3. Two judges scored each report from 0 to 10 on accuracy, depth, source quality, conflict handling and readability, gave an overall score, and named errors and omissions. They opened 3 to 8 cited pages per question.

Verified information is the claim count times the share of checked claims that were supported.

## Results

| | q1 baseline | q1 treatment | q2 baseline | q2 treatment |
|---|---|---|---|---|
| Report length (words) | 893 | 4,449 | 1,363 | 4,496 |
| Distinct source URLs | 6 | 70 | 9 | 78 |
| Atomic claims (extractor) | 58 | 259 | 76 | 227 |
| Checked claims supported | 15 of 15 | 15 of 15 | 15 of 15 | 14 of 15 |
| Checked claims wrong | 0 | 0 | 0 | 0 |
| The report's own citation supports the claim | 5 of 15 | 14 of 15 | 9 of 15 | 14 of 15 |
| Verified information | 58 | 259 | 76 | 212 |
| Overall score, two judges | 4.6, 4.6 | 8.7, 8.7 | 5.9, 6.8 | 8.5, 8.6 |
| Accuracy (mean of two) | 7.5 | 8.3 | 7.6 | 8.1 |
| Depth | 3.5 | 9.3 | 5.5 | 9.3 |
| Source quality | 4.4 | 8.7 | 6.4 | 8.1 |
| Conflict handling | 5.9 | 9.2 | 6.2 | 9.2 |
| Readability | 8.1 | 6.8 | 7.5 | 6.9 |
| Preferred by | 0 of 2 | 2 of 2 | 0 of 2 | 2 of 2 |

- **Verified information:** 4.5 times the baseline on q1 and 2.8 times on q2, 3.6 on average. The target of 2.0 was met on both questions.
- **Accuracy:** no checked claim was wrong in either arm. On q2 one treatment claim could not be verified (its source is a 48 MB PDF the verifier could not parse), so the treatment's supported share is 93% against 100%. Averaged over both questions it is 97% against 100%. The protocol allowed 5 points and did not say whether per question or on average; on q2 alone the gap is 7 points.
- **Overlap:** 42 of the baseline's 58 claims on q1 also appear in the treatment report, and 34 of 76 on q2. On q2 the baseline holds facts the treatment missed, among them two peer-reviewed thermal-runaway studies and a Wood Mackenzie report of 5 November 2026.
- **Script check of the treatment reports:** 481 of 491 cited figures matched the page snapshots on q1 and 394 of 462 on q2. Every flag was answered.

### What the judges said

About the treatment:
- It covers every period or sub-topic, cites primary and official records at the claim, and its table of disputes gives a reasoned verdict for each.
- It is long and dense, and some disputes are repeated. This is why it loses on readability.
- It missed conflicts between its own sources: the start of the Greek occupation of İznik (July 1920 from Wikipedia, 21 September 1920 in TDV) and CRU's cost-parity year (2028 in one source, 2032 in another).
- Some dates are firm in the opening table and hedged in the body. Two citations point to the wrong source number.

About the baseline:
- It is short, readable and mostly correct.
- Its vote step dropped well-documented events, so whole periods are missing (Bithynia and Rome on q1) and major producers are unreported (q2).
- Most claims have no claim-level citation, and its sources are mostly encyclopedias on q1.
- Wording from its pipeline leaks into the report ("rejected 0-3").

## Time and cost

| | q1 baseline | q1 treatment | q2 baseline | q2 treatment |
|---|---|---|---|---|
| Agents | 102 | 10 | 105 | 10 |
| Agent tokens | 3.24 M | 1.14 M | 3.57 M | 1.20 M |
| Wall time | 6.7 min | about 18 min | 8.6 min | about 19 min |
| Logged cost | $17.96 | $12.98 plus the writer | $21.71 | $13.01 plus the writer |

The treatment times are the sum of its stages, because the runs were interrupted (see below): plan 1.9 and 1.7 minutes, the slowest of eight researchers 6.9 and 8.4 minutes, the writer 8.8 and 9.0 minutes. Ten agents contributed to each judged report; the tokens also include the critic of the interrupted gap wave. The writer's cost was not logged in dollars; it used 0.24 M tokens per report.

## Deviations from the protocol

1. **Interrupted runs.** Both treatment runs hit the account's usage limit about 10 minutes in, after all eight sections were written and before the writer started. The Write stage was run 3.5 hours later with the workflow's `finish` mode on Opus 5.5. The writer brief had two small additions by then (cite figures inside tables, shorter notes).
2. **No gap wave.** At the time, standard depth started a gap wave when a headline row was open. Both runs started one and the limit stopped it. The judged reports therefore contain no gap sections, and the shipped standard depth has no gap wave. Deep and ultra run it; no judged report covers them.
3. **Held-out question.** The protocol names a third question for a final comparison. Only the treatment was run on it, to confirm that the finished skill works end to end (see below). There is no baseline and no judging for it, so it supports no comparison.

## Changes made after the judged runs

These follow from the timings and from the judges' notes. The unit tests and the final run cover them; no blind judging does.

- Page snapshots are downloaded in parallel with a 45-second limit per page. One sequential batch had taken 206 seconds because of slow hosts.
- `vafer_assemble.py check` answers the flags of claims already marked † and prints only the open ones. The writers had spent minutes filling in 47 and more such cells by hand.
- PDFs are read through pypdf when pdftotext is missing.
- The briefs now tell researchers to report a conflict between two of their own sources and not to add their own dispute tables. They tell the writer to look in the page snapshots for a stronger source behind a lead-only headline date, and to hedge a date in the opening table the way the body does.

## Final end-to-end run

One uninterrupted headless run of the finished skill on the held-out question, on Opus 5.5: "AB Yapay Zekâ Yasası (AI Act): yükümlülükler, yürürlük takvimi, cezalar ve 2025–2026'da önerilen değişiklikler hakkında ayrıntılı bir araştırma raporu hazırla."

| | Result |
|---|---|
| Wall time | 16.0 min: plan 2.1, the slowest of eight researchers 5.5, writer 7.7 |
| Agents and tokens | 10 agents, 0.93 M tokens, $13.60 |
| Report | 4,695 words, 77 sources: 10 primary, 43 official, 1 scholarly, 13 press, 4 lead, 6 unlabelled |
| Coverage | 34 of 34 rows settled |
| Script check | 492 of 498 cited figures matched; 12 flags, all answered |

The lead followed SKILL.md: it announced the depth, the agents and the time, launched the workflow, and delivered the answer, the status line, the two paths and the notes. Against the judged runs, the slowest researcher took 5.5 minutes instead of 6.9 and 8.4, the writer 7.7 instead of 8.8 and 9.0, and the final check raised 12 flags instead of 57 and 75. The question differs, so these comparisons are indicative. No baseline was run on this question and no judge read this report.

## Limits

- One run per arm and two judged questions: the result shows direction, not a precise multiple.
- The judges are models. No person adjudicated.
- The reports differ in format, so the blinding is partial.
- The claim counts come from one extractor. Script counts point the same way (numbers in the text: 108 against 513, and 165 against 499).
- The treatment is about twice as slow as the baseline (16 minutes in the final run, against 6.7 and 8.6 minutes for the baseline on other questions), and its reports are harder to read at first pass.
- The writer is now the longest stage. It still writes evidence.md by hand, which took 73 seconds in the final run; a script could build that file from the notes.
