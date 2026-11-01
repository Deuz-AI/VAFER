# Live check, brainstorm (PLAN.md Task 13)

Date: 2026-10-31. The prompts P1–P5 are verbatim from DESIGN §11.

## Pass criteria

These were fixed and committed before the scored runs, following DESIGN §11 "Geçme".

| Criterion | Pass |
|---|---|
| GENERIC points per answer, arm A | at most 1, and no praise |
| WRONG points | A at most B |
| Opened-page links | 3 per run, opened and verified |
| Answer | at most 350 words, no question first |
| Claude Code time | median at most 3:00, longest at most 4:00 |
| handoff.md | the six headings in every one |
| P5 | at least 3 candidate objects |
| Explicit command | triggers the skill 5 of 5 |
| "Bir sadakat kartı uygulaması yapalım." and "Ajans için bir iş planı yaz." | do not trigger the skill |
| D gate: A beats B on D by at least 2, in at least 3 of 5 prompts | pending until the author marks the NEW points |

**How words are counted:** in the final message, count tokens that contain a letter or a digit. Link targets are removed and a backticked path counts as one word, so markdown symbols such as `→`, `—`, `·` and `**` are not words.

## Arms

All arms ran on Claude Code 2.1.316 with the model pinned to Opus 5.5 (`--model claude-opus-5-5`, at the effort the author's settings give it: medium), headless (`claude -p`), each in its own temp folder outside any git repository, with the author's other plugins off (superpowers, firecrawl, playwright, frontend-design, supabase, skill-creator, usage-plus), and with `--permission-mode auto`. The author's user-level skills stay visible to every arm.
- **A:** the skill, called with `/vafer-brainstorm <prompt>`.
- **B:** the bare model, the prompt alone.
- **C:** the skill with `--disallowedTools Agent`, so it runs in single mode.

P1 ran in a temp folder that holds only a copy of `skills/`. Arms A and C also had both skills installed in `.claude/skills/`.

The author's default model changed to Fable during the session, so every scored arm pins the model. Two earlier brainstorm smoke runs on Fable took 208 and 234 s and cost about three times as much.

## Results

The scored runs used the skill at 9e90031 on 2026-11-01. One fresh blind judge per prompt saw the three answers as x, y and z in a fixed shuffled order. Each judge labelled every point, opened every link (at most 3 per answer), and gave no scores.

| Prompt | Arm | Time | Words | NEW | GENERIC | WRONG | KNOWN | Links checked | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P1 | A | 133 s | 259 | 9 | 0 | 0 | 1 | 1 supported | |
| P1 | B | 67 s | 358 | 10 | 2 | 0 | 1 | none | |
| P1 | C | 107 s | 315 | 10 | 2 | 1 | 1 | 1 supported, 1 not | |
| P2 | A | 153 s | 307 | 9 | 1 | 0 | 0 | 1 supported | |
| P2 | B | 30 s | 289 | 10 | 4 | 0 | 0 | none | closing question |
| P2 | C | 114 s | 345 | 9 | 1 | 0 | 0 | 2 supported | |
| P3 | A | 126 s | 326 | 11 | 0 | 0 | 0 | 1 supported | |
| P3 | B | 26 s | 318 | 5 | 11 | 0 | 0 | none | closing question |
| P3 | C | 103 s | 296 | 8 | 1 | 1 | 0 | 1 supported, 1 not | |
| P4 | A | 127 s | 287 | 10 | 1 | 0 | 0 | 1 supported | |
| P4 | B | 34 s | 444 | 8 | 12 | 0 | 0 | none | closing question |
| P4 | C | 99 s | 337 | 9 | 3 | 0 | 0 | 1 supported | |
| P5 | A | 117 s | 267 | 11 | 2 | 0 | 0 | none | 6 candidate objects |
| P5 | B | 24 s | 231 | 4 | 1 | 0 | 0 | none | 1 object |
| P5 | C | 61 s | 259 | 9 | 2 | 0 | 0 | none | 6 candidate objects |
| **All** | **A** | median 127 s | 259–326 | **50** | **4** | **0** | 1 | 4 of 4 supported | cost $7.33 |
| **All** | **B** | median 30 s | 231–444 | 37 | 30 | 0 | 1 | none | cost $1.14 |
| **All** | **C** | median 103 s | 259–345 | 45 | 9 | 2 | 1 | 5 of 7 supported | cost $2.71 |

Nobody praised the request, and no answer opened with a question. B ended three of five answers with a question.

### Pass criteria

| Criterion | Result |
|---|---|
| At most 1 GENERIC per answer in arm A, and no praise | **Failed on P5.** P1–P4 had 0, 1, 0 and 1 and nobody praised, but P5 had 2, both stock decision questions. ebed765 changed merge step 4 to drop questions as well as points that would fit another request, and P5 was re-run once. The re-run had 286 words, took 110 s and gave 5 objects. A fresh blind judge again found 2 GENERIC: one distribution tip and one platform question. |
| WRONG: A at most B | Passed: 0 and 0. |
| Opened-page links verified | Passed for A: all 4 links support their claims. C, in single mode, had 2 of 7 links on points whose headline the page does not state. |
| At most 350 words and no question first | Passed: A had 259–326 words and C 259–345, and no answer opened with a question. |
| Claude Code time: median at most 3:00, longest at most 4:00 | Passed: A's median was 2:07 and its longest 2:33. |
| Six headings in every handoff.md | Passed: all 10 A and C runs, and the smoke runs. |
| At least 3 candidate objects on P5 | Passed: 6 on the first run and 5 on the re-run. |
| The explicit command triggers 5 of 5 | Passed: each A run used the skill with 5 agents. |
| The two negative prompts do not trigger | Passed. "Bir sadakat kartı uygulaması yapalım." loaded no skill. "Ajans için bir iş planı yaz." loaded the author's docs skill, not this one. |
| D gate | Pending. The author marks the 131 NEW points blind. The marking sheet and its key are kept locally in `work/d-gate/` and are not committed, because the P4 points discuss the author's own accounts. |

### Smoke and trigger runs

| Run | Time | Result |
|---|---|---|
| Empty command, empty session | 8 s | It asked "What should we think about? A sentence or two is enough." and started no agents. |
| "Babam emekli oldu, evde sıkılıyor." | 112 s | No question; it showed a guess. It used 5 agents, wrote 339 words and saved a handoff with all six headings. |
| "şu fonksiyona bir isim öner" | 18 s | It used no agents and asked for the function's code, because no code was in the folder. |
| P2 with superpowers on, explicit command | 132 s | Same flow, 5 agents and 286 words. It did not turn into an interview. |
| Codex P2 (codex-cli 0.166.0, live search) | 176 / 212 / 220 s | All three runs passed, with 5 agents and all six headings. The second run's search-mode probe looked for that week's news on the topic, found none, and labelled live links "cached". 84f1406 changed the probe to search for today's date, and the third run labelled nothing "cached". |

### Changes made during this check

Each change came from a smoke or scored run and is covered by a test:
- **5801683.** Labels follow the user's language. "(unchecked)" goes only on facts. The answer no longer starts with "5/5".
- **3974538.** handoff.md is saved before the answer, and the answer is the last message. In one headless run the lead answered, saved, then ended with a short note, and `claude -p` printed only that note. This deviates from DESIGN §4 step 5.
- **ddb101a.** Each part of the answer template has its own word limit, and the top counts are now 4–5 missed points, 2–3 routes, 0–2 decisions and 0–1 research question. With DESIGN §7's counts (4–7, 2–4, 0–3, 0–2) the smoke runs gave 406–437 words. This deviates from DESIGN §7.
- **ebed765.** Merge drops questions, as well as points, that would fit another request.
- **84f1406.** On Codex, the search-mode probe searches for today's date.

### Observations

- **Value.** The blind judges found 50 NEW points against 4 GENERIC for A, and 37 against 30 for the bare model. Nearly half of the bare model's points were advice that fits any similar request.
- **Single mode (C).** Without agents, the lead found nearly as many NEW points (45), but more GENERIC ones (9). It also placed two links on points whose headline the linked page does not state.
- **Cost and time.** A costs about $1.50 and two minutes per answer, against about $0.23 and 30 s for the bare model.
- **Fable.** The author's default model changed to Fable during the session. Two earlier Fable smoke runs took 208 and 234 s at about three times the cost, so the time limits hold on Opus 5.5 at medium effort, not on Fable.
- **Side effect.** The "Ajans için bir iş planı yaz." run let the bare model publish a private Claude Docs page in the author's claude.ai account through their docs skill.
