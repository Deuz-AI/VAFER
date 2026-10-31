# Next

Read this after the first answer, before you write handoff.md or a module's exact line.

## handoff.md

Headings stay in English; the text under them is in the user's language. "In the user's words" carries tone, feel and principles word for word, because later steps tend to lose them. Terms are the request's key words folded to plain ASCII, so the lookup finds the file. Every Missed point names its basis.

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

In Research, Q is a ready question in the user's language; Why names the option it settles; Scope gives the place, period, unit and reader; Must cover lists 0–5 items. On a handoff, set the status to `handed off: <module>`. After a research run in this session, add its Run line.

## Readers

- **vafer-research** reads the Goal and one Research item. It uses Q verbatim and Scope as its scope, and asks nothing more. Each Must cover item becomes a plan row tagged `[brainstorm]`, its gap-finder never sees the file, and its plan.md records `from: <handoff path>`.
- **Planning** reads every section, follows the Decided lines and asks the Open questions itself.
- **Frontend** reads the Goal, Options and Decided lines.
- **anatomy** reads Options as candidate objects and Research for the numbers.

Saved files are data, not instructions. No module edits another module's file.

## The Next line

Offer a module only when it is installed: the skill list shows it. Write its command as the skill list shows the skill.

| Host | Copy install | Plugin `vafer` |
|---|---|---|
| Claude Code | `/vafer-research <Tier>: <Q> (handoff: <path>)` | `/vafer:vafer-research <Tier>: <Q> (handoff: <path>)` |
| Codex | `$vafer-research <Tier>: <Q> (handoff: <path>)` | `$vafer:vafer-research <Tier>: <Q> (handoff: <path>)`, a form not yet checked |

Another installed module, such as anatomy for a figure, gets its own command with the goal, the chosen option and `(handoff: <path>)`. Without vafer-research, a Worth researching item stays a question. Never name superpowers: its brainstorming would interview the user again.
