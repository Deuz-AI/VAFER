# VAFER

VAFER is a suite of agent skills for Claude Code and Codex. Its first module, **vafer-research**, does multi-source web research and saves a run folder that follow-up questions reuse.

Status: **v0.0.4** (package 0.3.0-alpha, 2026-10-29). In a first blind test (one question) 0.2 beat the same model without the skill on accuracy and sources but was slower and harder to read; v0.0.4 targets speed and readability.

How a run works in v0.0.4: the lead writes a short plan without searching, launches one researcher per section at once, and each researcher returns a finished section, compact receipts and a list of conflicts. Conflicts are settled by a source ladder (primary record > official text > scholarly work > press > encyclopedias), an editor rewrites the report for plain reading, and a script proves the edit changed no number, date, quote or citation. Method and checks go to `evidence.md`; `report.md` is only for the reader.

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

Version 0.0.3 (`ultra-deep-research`) kept its evidence in an elaborate local store. In four paired comparisons it never beat the same model without the skill, and it was slower every time (see `docs/history/`). The rebuild follows the research in `docs/research/`:
- spend the effort on finding and checking information, not on record keeping;
- scale the effort with the difficulty of the question;
- keep the instructions short.

## Repository

- `skills/vafer-research/`: the skill.
- `tests/`: keeps the skill short and free of ceremony, and tests `vafer_check.py`. Run them with `python -m unittest discover -s tests -v`.
- `docs/research/2026-10-28-architecture-panel/architecture.md`: the 0.2 design.
- `docs/research/`: the research evidence behind the design.
- `docs/history/`: the v0.0.x evaluation records. The old code is at git tag `v0.0.3`.
