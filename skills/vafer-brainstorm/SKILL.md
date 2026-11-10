---
name: vafer-brainstorm
description: Multi-agent brainstorming run as one Claude Code workflow. Ideators work alone from different angles, builders combine their ideas, three judges score every idea, and the best become short concept cards. Use when the user asks to brainstorm or wants ideas, options, names, features, angles or strategies on a topic (beyin fırtınası, fikir üret, fikir bul), or types /vafer-brainstorm. Not for questions of fact; use vafer-research for those.
compatibility: Claude Code with the Workflow tool and a writable project folder. No web access is needed. Without the Workflow tool the skill falls back to subagents or to working alone.
metadata:
  suite: vafer
  module: brainstorm
  version: 0.1.0
---

# VAFER Brainstorm

A brainstorm goes wrong when three things happen at once: having ideas, building on them and judging them. The workflow keeps them apart. Ideators work alone, each from a different angle, so nobody anchors on the first idea. Builders then combine and stretch what is on the table. Only after that do three judges score every idea, each on one criterion. You frame the topic, launch, and deliver.

## Frame the topic

The ideas can only be as good as the frame. Settle three things from the conversation, and from the project's files when the topic is about them:

- **Topic:** the user's words, verbatim.
- **Goal:** what a good idea would achieve, in one sentence.
- **Context:** who it is for, the means and limits (time, money, skills, tools), what already exists or was tried, and what to stay away from.

In an interactive session, ask at most three questions, and only when the answers would change the ideas. Otherwise state your assumptions in one line and go.

## Launch

| Depth | Use when | Agents | Typical time |
|---|---|---|---|
| quick | A small or casual ask | 8 | about 3 min |
| standard | The default | 12 | about 4 min |
| deep | The user wants many ideas, or the decision is a big one | 17 | about 8 min |

Tell the user the depth, the number of agents and the expected time in one line. Then:

```
Workflow({
  scriptPath: "<this skill's folder>/workflows/brainstorm.js",
  args: {
    topic: "<the user's words, verbatim>",
    goal: "<what a good idea would achieve>",
    context: "<audience, means and limits, what exists, what to avoid>",
    language: "<language of the ideas, for example Turkish>",
    depth: "standard",
    run: "<project>/.vafer/brainstorm/<YYYY-MM-DD>-<ascii-slug>"
  }
})
```

Write the run path absolute, with forward slashes, and pass `args` as an object. Three more args are optional:

- `lenses`: your own angles as `[{name, how}]`, when the default ones fit the topic badly. The defaults are the user's seat, first principles, borrowed from elsewhere, inversion and extremes; deep adds the pragmatist, the contrarian and the trend rider. For a name, angles such as sound, metaphor and other languages fit better.
- `avoid`: the titles from an earlier round, so that a new round goes elsewhere.
- `focus`: one theme or idea to stay within, for a round of variations.

The call returns at once, and the result arrives later as a task notification. Do not brainstorm the topic yourself in the meantime.

If `Workflow` is not among your tools, run the same steps with subagents: one ideator per angle in a single message, then merge, score and write up yourself. With no subagents, write the ideas under each angle before you judge any of them.

## Deliver

When the result arrives, reply in the user's language with:

- the `summary`;
- the top picks and the bold bets, each as its title and one line;
- one status line built from `counts` and `agents`, for example `62 ham fikir → 44 fikir, 8 tema · 12 ajan · 4 dk`, and the path in `file`, which holds the full cards and every idea.

End with one offer: a deeper look at one pick, another round that steers away from these ideas, or checking a pick against the facts with `vafer-research`. Nothing else runs after that. When `ok` is false, say what failed and show the ideas the result still carries.
