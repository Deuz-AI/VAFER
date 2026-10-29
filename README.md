# VAFER

VAFER is a suite of agent skills for Claude Code and Codex. Its first module, **vafer-research**, does multi-source web research and saves a run folder that follow-up questions reuse.

Status: **0.2.0-alpha** (2026-10-29). It has not yet been measured against the same model without the skill.

## What it does

- Picks a tier before it starts:
  - **Quick:** a few searches and an answer in chat, at about the cost of asking the model directly.
  - **Standard:** a short plan, parallel researchers when the question splits, an early draft, then one targeted wave to fill the gaps.
  - **Deep:** more researchers and up to two gap waves, for exhaustive lists and high-stakes questions.
  - **Ultra:** Deep, with gap waves repeated until one finds nothing new and a counter-evidence search for every conclusion.
- Cites only pages it actually opened. Key numbers, dates and quotes come from the primary record or from two independent sources. Summaries and news count only as leads.
- Says plainly what it could not establish and which queries it tried, instead of filling gaps from memory.
- Writes in the user's language, with inline citations and an as-of date.
- Checks its own figures: `scripts/vafer_check.py` saves a text copy of every cited page and matches each number, date and quote in the report against it, recomputes derived figures and lints citations. Anything it cannot confirm is fixed or marked †.
- Saves `plan.md`, notes, page copies and `report.md` under `.vafer/research/`, so a follow-up question starts from earlier work and re-checks only what may have changed.

## Install

Copy `skills/vafer-research/` into your project:

| Host | Destination | Invoke |
| --- | --- | --- |
| Claude Code | `.claude/skills/vafer-research/` | `/vafer-research <question>` |
| Codex | `.agents/skills/vafer-research/` | `$vafer-research <question>` (start Codex with `--search` for live results) |

The skill needs a web search tool. Subagents, a shell with Python and network access, and a writable folder are optional; without them it falls back to doing the work itself, checking headline facts by hand and answering in chat.

## Why it was rebuilt

Version 0.0.3 (`ultra-deep-research`) kept its evidence in an elaborate local store. In four paired comparisons it never beat the same model without the skill, and it was slower every time (see `docs/history/`). The rebuild follows the research summarized in `docs/superpowers/specs/2026-10-27-vafer-research-v0.1-design.md`:
- spend the effort on finding and checking information, not on record keeping;
- scale the effort with the difficulty of the question;
- keep the instructions short.

## Repository

- `skills/vafer-research/`: the skill.
- `tests/test_skill_hygiene.py`: keeps the skill short and free of ceremony. Run it with `python -m unittest discover -s tests -v`.
- `docs/superpowers/`: the design and the plans.
- `docs/research/`: the research evidence behind the design.
- `docs/history/`: the v0.0.x evaluation records. The old code is at git tag `v0.0.3`.
