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

## Results

(pending: the runs start after this commit)
