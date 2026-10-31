# Briefs

A subagent sees only its brief and the files it names, so put everything else in the brief. Send all of a launch's briefs in one message. On Claude Code, use fresh `general-purpose` subagents, not forks. `{cmd}` is the full command, `<python> <absolute skill folder>/scripts/vafer_check.py`.

## Gap-finder

Spawn it first, before you write plan.md.

```text
Today is {date}. Question: {question, verbatim}. Scope: {scope}.
Without seeing anyone else's work, use at most 5 searches to find what a complete answer has to cover. Your items become plan rows.
First list the question's own atoms: named entities, places, periods, units and format cues.
Then add sub-topics, phases, alternatives, recent changes, and errors that sources commonly make.
For a list or a comparison, also name the record that enumerates the items, and the frame: one row per item, one column per attribute.
If you have no web search tool, reply only: NO_WEB
Reply with 8-12 items, one line each: the item, why it matters, the record that settles it, and the URL that suggested it.
```

## Section researcher

```text
Read {skill folder}/references/researcher.md first and follow it.
Today is {date}. Question: {question, verbatim}. Reader: {who, in which language}.
Your section: {id} {title}. Rows, each with its settling record and [prior] terms: {rows}.
Word budget: {words}. Others cover: {one line per other section}; do not duplicate them.
Start with: {2-4 short queries, in the languages of the best sources}.
Run folder: {run}. Command: {cmd}.
Write receipts to {run}/notes/{id}.md and the section to {run}/sections/{id}.md, cited as [URL].
If you have no web search tool, reply only: NO_WEB
Reply in at most 200 words: rows settled and rows open; the conflict list, one line each (claim | A says, source, rung | B says, source, rung or "B not opened" | type | suggested verdict); searches and pages opened; the two file paths.
```

## Example (one section of a tariff comparison)

```text
Your section: S1 İSKİ (Istanbul) residential water tariffs in 2026. Rows: tariff per m³ by band (record: İSKİ tariff table, 2026; [prior] "İSKİ su tarifesi"); date and decision of the change (record: İBB council decision); share of the bill that is wastewater fee (record: İSKİ tariff table).
Others cover: ASKİ (Ankara); İZSU (İzmir); national rules on water pricing.
Start with: "İSKİ su tarifesi 2026", "İBB meclis kararı su tarifesi 2026", "İSKİ tarife değişikliği".
```

## Follow-up

Spawn one as soon as its trigger appears: a headline conflict the ladder cannot settle, an open headline row, or a value about to be rejected that nobody opened.

```text
Read {skill folder}/references/researcher.md first and follow it.
Today is {date}. Question: {question, verbatim}. Settle one item: {claim or row}.
What is known: {A: statement, source, rung; B: statement, source, rung or "not opened"}.
Open the page behind any value you would reject, and follow a lead's footnote once. Check any arithmetic or calendar conversion yourself.
Run folder: {run}. Command: {cmd}. Write receipts to {run}/notes/{id}.md.
If you have no web search tool, reply only: NO_WEB
Reply in at most 150 words: the verdict (A, B, both partly, both by definition, or unresolved), the deciding receipt lines, and one sentence a reader can understand.
```

## Table variant (lists of about eight items or more)

Build the frame before filling it: find the record that enumerates the items plus one independent route to the same set, and write the frame in plan.md, one row per item and one column per attribute. The gap-finder's frame is a starting point. Give each researcher a batch of rows instead of a section: "Your rows: {items}. Columns: {attributes, with unit and period}. Fill every cell with a value and its receipt, 'not found (queries)' or 'n/a (reason)'. Report items missing from the frame." Run passes through unused routes until one adds no item, then compare the count with any total the sources state.

## Variants

- **Finite work** (a book, report, standard or dataset the user supplied or named): assign researchers by structural unit (chapters, sections, tables) and ask each to report what its unit says, with locations, before interpreting it.
- **No subagents:** run the same briefs yourself, one after another; run the gap-finder pass first and label it a self-check in evidence.md.
- **Subagents without web:** search yourself, then give each researcher 5–10 URLs to read instead of queries.
