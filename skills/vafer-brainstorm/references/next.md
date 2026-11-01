# Next

Read this before you write handoff.md, a follow-up or a module's exact line.

## handoff.md

Headings stay in English, the text under them in the user's language. "In the user's words" carries tone, feel and principles word for word. Terms are the request's key words in ASCII, for the lookup. Every Missed point names its basis.

```markdown
# <short ASCII title>
Prompt (verbatim): "<the user's words>"
<YYYY-MM-DD> | brainstorm | <5 agents | single> | status: <open | handed off: <module>>
Terms (ASCII): <folded terms>
From: <earlier .vafer paths, if any>

## Goal
<1-3 sentences in the user's terms>
In the user's words: "<tone, feel, principles>"
Constraints: <...>
Decided: <choice> (<date>; user | Claude's call)
Guess: <assumption> (guess)

## Missed
1. <point> — <why> — <basis: given | user file <path> | .vafer/<run> (<date>) | <URL> (opened <date>) | model, unchecked>
Obvious (not shown): <titles>

## Options
A. <route> — <main trade-off>   (after deepening: How | First test | Against)

## Open questions
1. <question> — <what the answer changes>

## Research
1. Q: <question> | Why | Scope | Tier: Quick|Standard|Deep | Must cover   (after the run: Run: <path> (<date>) — <answer>)

## Next
<module> — <exact line for this host, e.g. /vafer-research Quick: <Q> (handoff: <path>)>
```

In Research, Q is a ready question in the user's language; Why names the option it settles; Scope gives the place, period, unit and reader; Tier is Quick for one fact or a stable topic, Standard for a comparison, several sub-questions, or a recent, niche or local topic; Must cover lists 0–5 items. A deepened Missed point takes an option's after-deepening fields.

## Readers

- **vafer-research** reads the Goal and one Research item: Q verbatim, Scope as its scope, each Must cover item as a `[brainstorm]` plan row. It asks nothing more.
- **Planning** reads every section, follows the Decided lines and asks the Open questions itself.
- **Frontend** reads the Goal, Options and Decided lines.
- **anatomy** does not read handoffs yet: its command carries the goal, the chosen object and any numbers the figure needs.

No module edits another module's file.

## The Next line

Offer a module only when the skill list shows it, and write its command as the list shows the skill.

- Claude Code: `/vafer-research <Tier>: <Q> (handoff: <path>)`, or `/vafer:vafer-research` with the plugin `vafer`.
- Codex: `$vafer-research`, or `$vafer:vafer-research` with the plugin (a form not yet checked).

With nothing saved, end the command with `(goal: <Goal>; scope: <Scope>; must cover: <items>)` in place of `(handoff: <path>)`. Another installed module gets its own command with the goal, the chosen option and, if it reads handoffs, `(handoff: <path>)`. When headless, Next gives one full command, on Codex single-quoted: `codex exec -c web_search="live" --sandbox workspace-write -c sandbox_workspace_write.network_access=true '$vafer-research …'`.

## Follow-ups

- **"Deepen 2 and B"** (at most 3 picks; ~1:30–2:00): one developer per pick and one counter agent for all, in one wave (`references/angles.md`), while you run at most 2 searches per pick for who already did it; a fact seen only in their summaries becomes a Research question. Show each pick in ≤120 words: **<pick>** How · First test · Against.
- **"More":** see `references/angles.md`.
- **"Check 2":** vafer-research Quick on that point.
- **An answer or a correction:** a `Decided:` line; the points it settles drop; no new wave.
- **"You decide":** "If X matters, A; if Y matters, B", recorded as Claude's call.
- **"Continue yesterday's":** the lookup finds the handoff; summarize its decisions.
- **"Research", "plan", a page or a figure** ("this" is the last pick): for a point with no Research item, add one and save first. A named module or Quick research runs at once; Standard shows its line, tier and time and waits for yes. When it starts, set the status to `handed off: <module>`; after a research run, add its Run line.
