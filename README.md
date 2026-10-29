# VAFER

VAFER is a suite of agent skills for Claude Code and Codex. Its first module, **vafer-research**, does multi-source web research. It writes a readable report in which every cited figure has been checked, and saves a run folder that follow-up questions reuse.

Status: **v0.0.4** (2026-10-29).

## Results

Question: "Yalova'nın tarihi" (the history of Yalova). Each arm ran the same model with the same prompt. A blind judge did not know which report came from which arm. It opened 26 cited pages, fact-checked 10–12 claims per report and scored each report out of 10.

| | v0.0.4 | v0.0.4 first draft | No skill |
|---|---|---|---|
| Overall | **8.6** | 8.1 | 5.8 |
| Accuracy | **8.5** | 8 | 5 |
| Source quality | **9** | **9** | 3.5 |
| Conflict handling | 8.5 | **9** | 5.5 |
| Readability | **8.5** | 6.5 | 8 |
| Wall time | 22 min | 13.5 min | 5 min |

What the judge's checks found:
- **Calendar conversion:** only v0.0.4 converted the Rumi calendar date correctly (1316 = 1900).
- **Errors in the no-skill report:** it put the 1999 earthquake toll for nine central neighbourhoods (1,449) as the toll for the whole province, and it got the dates and members of the 1921 Allied commission wrong.
- **Speed:** v0.0.4 is not yet faster. The fixes in `a927973` limit researcher effort and the gap wave, but no run has measured them yet.

## How a run works

1. **Plan:** the lead takes about a minute to write a plan without searching. The plan has 4–12 rows grouped into 3–6 sections, and each row names the record that would settle it.
2. **Launch:** in one message, the lead launches one researcher per section plus a gap-finder. Each researcher returns three things:
   - a finished section written in the house style;
   - receipts: one line per fact, with an exact quote from a saved copy of the page and a source label (primary, official, scholarly, press or lead);
   - a list of the conflicts it found.
3. **Settle conflicts:** a fixed source ladder decides between sources. The steps, highest first:
   1. arithmetic or a calendar check;
   2. the primary record;
   3. official or legal text;
   4. scholarly work;
   5. press;
   6. encyclopedias and aggregators, which count only as leads.

   If the ladder cannot settle a headline conflict, the lead sends it to an adjudicator.
4. **Gap wave:** this step runs only if headline rows are still open.
5. **Assemble:** the lead puts the report together. `report.md` is for the reader: the answer, an "at a glance" table, the sections, a table of where sources disagree, the unknowns and the sources. Method and checks go to `evidence.md`.
6. **Edit and check:**
   - An editor rewrites the report for plain reading.
   - `vafer_check.py diff` confirms that the edit changed, dropped or added no number, date, quote or citation.
   - `vafer_check.py check` then matches every cited number, date and quote against the saved page copies.

Tiers:

| Tier | What runs |
|---|---|
| Quick | A few searches and an answer in chat |
| Standard | The run above |
| Deep | More researchers and up to two gap waves |
| Ultra | Gap waves until one adds nothing new, plus a counter-evidence search for every conclusion |

## Install

Copy `skills/vafer-research/` into your project:

| Host | Destination | Invoke |
| --- | --- | --- |
| Claude Code | `.claude/skills/vafer-research/` | `/vafer-research <question>` |
| Codex | `.agents/skills/vafer-research/` | `$vafer-research <question>` (start Codex with `--search` for live results) |

The skill needs a web search tool. The following are optional:
- subagents;
- a shell with Python 3 and network access (the check script uses only the standard library);
- a writable folder.

Without them, the skill does the work itself, checks the headline facts by hand and answers in chat.

On Claude Code, a `deny` rule for WebSearch or WebFetch in `settings.json` blocks all research.

## The check script

`skills/vafer-research/scripts/vafer_check.py` has three commands.

| Command | What it does |
|---|---|
| `fetch <run> <url>...` | Saves a text copy of each page under `pages/`. It handles charsets, tables and PDFs (with `pdftotext`), and flags empty, boilerplate or binary pages. |
| `check <run>` | Matches every cited number, date and quote against the receipts and page copies. It understands Turkish and English number formats, including words such as "4 bin 472", and recomputes equations. It flags uncited figures, claims backed only by lead-class sources, dangling or unused citations, and method words that leak into the report. |
| `diff <old> <new>` | Exits with an error if an edit lost, changed or added a number or quote, dropped a citation, or detached a citation from its sentence. |

## Repository

- `skills/vafer-research/`: the skill, which consists of `SKILL.md`, `references/` (briefs, house style, hosts, reuse) and `scripts/`.
- `tests/`: tests for `vafer_check.py` and hygiene tests that keep the skill short. Run them with `python -m unittest discover -s tests -v`.
- `docs/research/`: the research behind the design, including the study of the hyperresearch project and the architecture panel.
- `docs/history/`: evaluation records for the v0.0.x versions. The old code is at git tag `v0.0.3`.

## Why it was rebuilt

Version 0.0.3 (`ultra-deep-research`) kept its evidence in an elaborate local store. It never beat the same model without the skill in four paired comparisons, and it was slower every time. The rebuild spends the effort on finding and checking information, not on record keeping. It scales the effort with the difficulty of the question and keeps the instructions short.
