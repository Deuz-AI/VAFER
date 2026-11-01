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

(pending: the runs start after this commit)
