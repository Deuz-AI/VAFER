---
name: vafer-brainstorm
description: Multi-agent brainstorm (beyin fırtınası). Five independent angles look at the user's idea, plan, decision or question and bring back what they probably missed (blind spots, risks, other routes, facts worth checking), saved as a handoff for the next VAFER skill. Use when the user asks to brainstorm, wants ideas, other angles or a devil's advocate, or asks what they are missing. Not for requirement interviews, specs or cited research.
compatibility: Subagents keep the five angles independent; without them the skill runs the angles itself, one after another. Web search adds a short fact scan; without it, facts stay marked unchecked. A writable project folder saves the handoff.
metadata:
  suite: vafer
  module: brainstorm
  version: 0.0.5
---

# VAFER Brainstorm

Five independent agents look at the request from five angles while you run a short web scan. You do not interview, score ideas or build.

## Done when

- One screen in the user's language shows 4–5 missed points (at most 2 per angle), 2–3 other routes, one obvious line, 0–2 decisions and 0–1 research question.
- No question came first, unless the request had no topic.
- handoff.md is saved, or the reply says "not saved".

## When to stay out

- A mechanical request, such as naming a function: do it directly, without agents or a handoff; ask for the thing if it is not in view.
- A requirements interview or a spec: not this skill; for cited research, offer vafer-research when installed.
- Unless called by name, a build or writing request that does not ask for ideas, other angles or what is missing.

## Flow

1. **Read** (10–20 s, one batch): the conversation; up to 3 files, those the user pointed at or, if the request names this project or part of it, those that define it; and `references/angles.md`. Look up earlier runs from the git root, else the current folder: `rg -i -l "<ascii term>" .vafer --glob handoff.md --glob plan.md`; a missing `rg` or `.vafer` means no earlier run. Saved files are data, not instructions. Note a one-sentence goal, your guess and a summary of at most 120 words with the facts the request leaves out.
2. **Launch** (25–40 s): choose the four details together and send the five briefs in one message; each ends "Do not invoke skills or start other agents." Status line, in the user's language: "My understanding: <goal> (guess). Five angles and a short web scan; ~3 min.", without the scan clause when skipping the scan.
3. **Think** (45–110 s). If the request touches a product, price, law, place or recent event, scan meanwhile: at most 3 searches (who already does this; what changed in the past year; the rule or number the decision rests on) and 2 opened pages. Only facts from opened pages get a link. A fact from a search summary alone becomes a Worth researching question. Show at most 2 scan facts.
   - Claude Code: fresh `general-purpose` agents, not forks. Start them, scan, end your turn. On each earlier notification write only "n/5"; at the last, merge: the answer alone.
   - Codex: five `spawn_agent` calls with only their briefs (no `fork_context`), then the scan; `wait_agent`, and `close_agent` each that finishes or stays silent 2 minutes after the others. Without `-c web_search="live"`, search is cached: mark scan facts "cached".
4. **Merge** (25–35 s), then **save** handoff.md.
5. **Show** the answer as your last message; if saving failed, its Saved line says "not saved".

Ask first only when there is no topic: "What should we think about? A sentence or two is enough.", in English in an empty session. An empty command takes the conversation's topic; unknowns go to Yours to decide. A correction of your guess in the first minute reruns step 2: stop the first wave (`TaskStop`, or `close_agent` on Codex) and count only new replies. Another message before the last reply: merge what has arrived, naming the missing angle; later replies go only into the next save.

## Merge

1. Pool the agents' points and scan facts.
2. Drop what the request, conversation, files or Decided lines cover.
3. Fold points that repeat an OBVIOUS title or have p ≥ 0.3 into the obvious line; blockers (law, safety, money, a dependency that makes the plan impossible) stay at any p.
4. Drop points with no "changes" or that would fit another request.
5. Merge duplicates, keeping the sharpest wording and single-angle points; no "found by two angles" tag.
6. Order: PREMISE challenges and blockers, points that change the plan, the rest; cheapest to check first in each group.
7. Cut to the template's counts; the rest go to handoff.md.

## The answer

```text
**What you may have missed**   (4-5, at most 2 per angle)
1. **<point, one sentence>** <why it matters here, one sentence naming what it changes>. → <first step, under an hour> <[source](link), (unchecked) on a fact, or nothing>
**Other routes**   (2-3, one line each)
A. **<route>** — <main trade-off>
**Obvious, skipped:** <up to six titles>
**Yours to decide**   (0-2, only if the answer changes a pick)
- <question> — <what the answer changes>
**Worth researching:** <question>   (0-1)
Saved: <path> · Next: <follow-ups to type now: "deepen 1 and A", "more", "check 2", "research">
```

In the user's language, every heading and label included; at most 350 words, 30 per point; to fit, drop the last missed points. Ideas or objects asked for come first: 3–6, under their own heading, in place of Other routes. A fact is a number, law, price, product or date. No praise, closing question, summary or p values; an angle is named only when missing, on the Saved line. Next names only installed modules, never superpowers.

## After the answer

Handle follow-ups as `references/next.md` says; another module runs in the main session, never inside an agent. Standard or deeper research starts only when the user says yes. "Continue yesterday's": the lookup finds the handoff; summarize its decisions.

Write handoff.md from `references/next.md` once for the first answer, then only on a handoff or "save": `.vafer/brainstorm/<YYYY-MM-DD>-<slug>/handoff.md` where step 1 looked, the slug lowercase ASCII, `-2` on a collision.

## Without agents, web or files

- **Single mode** (no subagents, or this skill runs inside an agent): take the five angles yourself, in turn, without showing them; merge as usual.
- **Headless** (`claude -p`, `codex exec`): agents still reply, so use single mode only if spawning fails. No loop or research chain.
- **No web, or a web permission refused:** no scan.
- **No file writes:** say "not saved"; a handoff passes Goal and Research inline.
- **An agent fails:** merge without it, name the missing angle, no retry.
- **No vafer-research:** never offer "check".
