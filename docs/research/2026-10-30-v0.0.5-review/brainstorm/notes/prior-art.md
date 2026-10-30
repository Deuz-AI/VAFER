# Prior art: brainstorming skills, councils and products

Date: 2026-10-30. Star counts are from the GitHub API that day. "Agents" means model calls per run.

## Summary

Superpowers' brainstorming (v7.0.0) is a one-question-at-a-time requirements interview ending in an approved design doc; its wide thinking stays private. Its v7 opener drew a 26-comment backlash over pointless questions, and its maintainers declined a divergent "pre-brainstorm" skill as standalone-plugin material: VAFER's gap. Council tools (llm-council and ports, Mysti, PAL) run parallel independent answers, optional anonymous ranking, then one merged answer; users report chairman bias, failed syntheses, stalls and token cost. BMAD has rich techniques, heavy ceremony, and loses soft ideas downstream. Studies show LLM ideas are alike; reasoning first, ordinary personas, discussion and web input widen them. Products mostly give generic one-shot lists; flattery is the loudest complaint. Design: name it vafer-brainstorm, ask nothing up front, run 3–5 parallel lens agents once, skip ranking, return a short "what you missed" list plus a handoff.

## Findings

### F1. Superpowers' brainstorming is a requirements interview

- **Finding.** Unless the request is already complete, it asks one open question per message, plays back each understood part in 200–300 words, sizes the work and, for a project, writes a design doc. A fresh "builder" subagent lists what it would still ask; the user answers only what changes the build. A hard gate blocks building until approval, then writing-plans runs. It is good at drawing out intent and non-goals and at stopping premature building. Its wide thinking stays private ("Think wide privately"), offered options count as steering, and web research is only offered.
- **Evidence.** `~/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/skills/brainstorming/SKILL.md`:26-39, 43, 83-90, 112-143, 160-193, 199; `builder-check-prompt.md`:6-22.
- **Implies.** VAFER brainstorm is the opposite move: agents do the wide thinking and show it, and the user picks. Interviews, docs and gates belong to planning.
- **Confidence.** High.

### F2. Pure brainstorming fills a gap superpowers declined

- **Finding.** superpowers#1766 asked for a divergent "pre-brainstorm" skill. A commenter said superpowers' skill "wears the name of divergence but performs convergence" and named two missing kinds of widening: ambition ("what could this become") and alternative approaches ("3–5 mechanistically distinct approaches", plus the request's hidden assumption). Told "just pick the best one and start writing the spec", an agent without a skill collapsed to one option in 2 of 2 runs. With his divergence skill it held the choice, but only an explicit line stopped it from inventing a default and moving on; he recommends a "produces options, decides/specs nothing" contract. Closed 2026-10-21: "It could live in a standalone plugin." Users also ask for prior-art research before design (#2129).
- **Evidence.** https://github.com/obra/superpowers/issues/1766 (2026-06-16; comment 2026-07-04); https://github.com/obra/superpowers/issues/2129 (2026-08-12).
- **Implies.** Cover both kinds of widening plus outside facts. The skill raises points; it never decides or writes specs. "Just decide for me" gets one recommendation with its alternatives, then the handoff.
- **Confidence.** High that the gap exists; medium that users want it as the default first step.

### F3. The trigger will likely collide with superpowers

- **Finding.** Superpowers' description says "You MUST use this before any creative work ... or planning anything new". Its using-superpowers skill, loaded every session, says three things: invoke a skill at "even a 1% chance", run process skills first ("'Let's build X' → superpowers:brainstorming first"), and brainstorm before plan mode. "Brainstorm" also matches its name.
- **Evidence.**
  - Superpowers: SKILL.md:3; `using-superpowers/SKILL.md`:11, 22, 28-30; superpowers#2514 (2026-10-14).
  - Codex: `policy.allow_implicit_invocation: false` makes a skill explicit-only (https://developers.openai.com/codex/skills).
  - VAFER's test forbids Claude Code's `disable-model-invocation`; Codex cuts descriptions first when the skill list exceeds 2% of context (`docs/research/2026-10-30-v0.0.5-review/notes/hosts.md`:95-98, 104).
- **Implies.** Name it `vafer-brainstorm`. Open the description with triggers superpowers lacks ("what am I missing", "blind spots", "other angles", "devil's advocate", "beyin fırtınası") and say "not a requirements interview or design doc". End each run with a short "decided / still open" block; superpowers' fixes make it read context first, so it should not re-ask what is decided. Test with both installed.
- **Confidence.** Medium (read from the texts; not run live).

### F4. Pointless questions are the top complaint

- **Finding.** superpowers#2530, "v7's brainstorm questions are rather annoying", drew 26 comments in two weeks: questions like "the HR person asks during an initial job screening", questions the code or spec already answered, "lots of words to say nothing". One user found the "skip the questions" opener in 9 of 12 v7 sessions, against 0 of 134 on v6. The maintainers' fixes (#2560 merged; #2571 and #2644 in testing): read what the user pointed at first; ask only when the answer changes what gets built and nothing answers it yet; otherwise state what you will do and why. A commenter: "zero questions is a legitimate outcome."
- **Evidence.** https://github.com/obra/superpowers/issues/2530 (2026-10-16 to 2026-10-29).
- **Implies.** No opening or closing question. Read the conversation, files and code first. Ask one question only if its answer would change the whole run; otherwise state the assumption in one line.
- **Confidence.** High.

### F5. Agent skills surveyed

| Tool (stars) | How it works | Agents | Output | Complaints |
|---|---|---|---|---|
| superpowers brainstorming (309k*) | interview → doc → builder check → gate | 1 + 1 checker | approved design doc | pointless questions #2530; slow, costly #743; fires too often #2514 |
| karpathy/llm-council (26.1k; 2025-11) | answers → anonymous ranking → chairman | 4 + chairman, ~9 calls | answers, rankings, final answer | chairman bias #3; failed synthesis #64 #83 #95 #113; setup, cost #35 #153; unmaintained |
| amgadelgamal/claude-council (29; 2026-06) | the same, with Claude subagent personas | 4 + 4 reviewers | verdict table, consensus, dissent | none filed; ~173k tokens, ~2.5 min a run |
| gcpdev/llm-council-skill (482; 2026-01) | asks ChatGPT and Gemini by API | 2 + host | plan with attribution | none filed; needs two API keys |
| team-attention/agent-council (141; 2025-12) | Codex/Gemini CLIs answer; host chairs | 2+ + host | synthesis | none filed; needs Node and each CLI |
| DeepMyst/Mysti (1.2k) | 2 agents, 5 strategies, up to 3 rounds | 2 | synthesis | stalls #31 #50 |
| PAL MCP `consensus` (11.8k*) | models argue for, against or neutral | 2+ + host | synthesis | callers overwrite each other #395; thinking mode ignored #361 |
| BMAD bmad-brainstorming (54.8k*) | coach, 3 stances, 108 techniques, log | 1 | log, report, HTML keepsake | rushes #1249; drops soft ideas #1674; vague #2011 |
| andrehuang/research-companion (723; 2026-03) | Seed → Diverge → Evaluate → Deepen → Frame → Decide | 3 | Pursue/Refine/Kill | few issues |
| skymanbp/cc-tree (94) | 12-angle tree grown until it converges | 1 | shortlist with sources | "minutes to hours" per run |
| Six Hats skills (agentic-qe 520; clawfu-skills 150) | one agent wears all six hats | 1 | six-part analysis | none found |
| Devil's-advocate skills (notmanas 92; jeremylongshore 2.9k*) | a critic at each step | 1 | critique | same model, same blind spots |

\* Stars for the whole project. Codex's curated openai/skills catalog (28.4k) has no brainstorm skill; define-goal is the closest.

- **Evidence.** The repos above on github.com; issue numbers are per repo; the claude-council README's "Example (real run)".
- **Implies.** All of them start with parallel independent answers. Cost and complaints build up after that, in ranking, extra rounds and logs.
- **Confidence.** High for the README and issue content; stars only roughly measure use.

### F6. Keep the council's parallel pass; drop its ranking and rounds

- **Finding.** Users say the chairman overrides minority views (llm-council#3). Peer review doubles the agents to rank answers on "accuracy and insight", which picks a winner rather than widening the spread, and an LLM judge favors the side running on its own model (Liang et al., EMNLP 2024). Debates over several rounds stall (Mysti#31: "Agent silent for 90s — aborting"). An all-Claude council gets "independence from isolation and personas, not cross-vendor diversity".
- **Evidence.** https://github.com/karpathy/llm-council/issues/3 (2025-11-23); https://arxiv.org/abs/2305.19118; https://github.com/DeepMyst/Mysti/issues/31 (2026-03-24); https://github.com/amgadelgamal/claude-council.
- **Implies.** Run one parallel round of fresh-context agents. The lead curates rather than judges: it merges duplicates, keeps dissent and odd items, and names the lens behind each. It writes with what has arrived by a deadline, and reports a stuck agent instead of waiting. Other vendors' models stay optional.
- **Confidence.** Medium (dropping ranking is untested for brainstorming).

### F7. BMAD: good techniques, too much ceremony, ideas lost later

- **Finding.** bmad-brainstorming is one coach with three stances: Facilitator ("You do not supply ideas"), Creative Partner, and Ideate for me. It aims "past 100 ideas", draws on 108 techniques, logs each idea through a script, and offers a browser setup page. Users report that v6 rushed to finish (#1249), the PRD step silently dropped soft ideas about tone and feel (#1674), and the output was too vague to build on (#2011). Brainstorming with several models was declined as "against the idea of brainstorming as pulling ideas from the human" (#1449).
- **Evidence.** https://github.com/bmad-code-org/BMAD-METHOD/tree/main/skills/bmad-brainstorming (SKILL.md:12, 37-45, 53; mode-facilitator.md:5; mode-autonomous.md:5-6); issues #1249 (2026-01-04), #1674 (2026-02-16), #2011 (2026-03-15), #1449 (reply 2026-02-18).
- **Implies.** VAFER's mode is BMAD's "Ideate for me" without the log, the browser page or the technique menu. Techniques become hidden agent lenses. The handoff keeps soft points (tone, feel, principles) in the user's own words, so planning cannot drop them.
- **Confidence.** High.

### F8. LLM ideas are alike unless the skill builds in variety

- **Finding.** With ChatGPT, idea pools narrowed in 37 of 45 comparisons; in one task 94% of ideas overlapped and nine people named their toy "Build-a-Breeze Castle". LLM research ideas were rated more novel but slightly less feasible than experts', and new ideas plateaued as generation scaled. Reasoning step by step before listing gave the most varied ideas, near human groups. Causes: early answers fix later ones, and the model pools its knowledge; reasoning plus ordinary personas (not "Steve Jobs") beat humans on variety. Discussion with role-play beat a single model on creativity tests.
- **Evidence.** Meincke, Nave, Terwiesch, Nature Human Behaviour (https://mackinstitute.wharton.upenn.edu/2025/new-in-nature-chatgpt-decreases-idea-diversity-in-brainstorming/, 2025-05-14); Si, Yang, Hashimoto (https://arxiv.org/abs/2409.04109, 2024-09-06); Meincke, Mollick, Terwiesch (https://arxiv.org/abs/2402.01727, 2024-01-27); Deng, Brucks, Toubia (https://arxiv.org/abs/2602.20408, 2026-02-23); Lu et al., COLM 2024 (https://arxiv.org/abs/2405.06373).
- **Implies.** Give each agent a different lens and a different input (the web, the user's files). Use ordinary viewpoints: a user, an operator, a competitor. Have agents reason before they list, and merge duplicates at the lead. In the side-by-side test, count items new to the user, not total ideas.
- **Confidence.** High that LLM ideas are alike; medium on which fixes carry over to agent skills.

### F9. Lenses that find what the user missed

- **Finding.** research-companion's Brainstormer looks for links to other fields and for "strategic ignorance" (assumptions a field never checks); its Idea Critic returns Pursue, Refine or Kill. Six Hats covers facts, risks, benefits, creativity, feelings and process. Devil's-advocate skills attack each step. Google's AI co-scientist combines the best ideas and adds sharply different ones. cc-tree lists five failures: shallow coverage, put-off branches, false variety ("six branches that are one branch with the nouns swapped"), stopping when it gets hard, and claims with no source.
- **Evidence.** https://github.com/andrehuang/research-companion (2026-03-26); https://github.com/proffesor-for-testing/agentic-qe; https://github.com/notmanas/claude-code-skills; https://docs.cloud.google.com/gemini/enterprise/docs/co-scientist-and-alphaevolve (announced Feb 2025); https://github.com/skymanbp/cc-tree.
- **Implies.** Use a fixed set of 3–5 lenses:
  - hidden assumptions;
  - failure (pre-mortem, devil's advocate);
  - other people affected;
  - what others already did, with facts from the web;
  - one unconstrained "what could this become".

  cc-tree's five failures make a ready checklist for the side-by-side test.
- **Confidence.** Medium.

### F10. Product brainstorming: generic lists and flattery

- **Finding.** Gemini's premade "Brainstormer" Gem, Notion AI's "Brainstorm ideas" and FigJam AI's sticky notes return one-shot lists. Reviews say they lack the user's context, need editing, look "generic" (a FigJam review title), and can invent items (Miro AI added "profile management", which was not on the board). Miro Sidekicks are role agents, such as a Product Leader that "challenges your product thinking". I found no brainstorm feature in Perplexity. Flattery draws the loudest complaints: OpenAI rolled back a GPT-4o update for it on 2025-04-29, and Claude Code#3382 ("You're absolutely right!" about everything, 2025-07-12) has 1,373 reactions.
- **Evidence.** https://support.google.com/gemini/answer/15235907; https://www.eesel.ai/blog/notion-ai-brainstorming; https://help.figma.com/hc/en-us/articles/16822138920343; https://www.gartner.com/reviews/product/figjam (review title); https://help.miro.com/hc/en-us/articles/29902701849618-Sidekicks-overview; https://www.pragmaticcoders.com/?p=25065; https://techcrunch.com/2025/04/29/openai-explains-why-chatgpt-became-too-sycophantic; https://github.com/anthropics/claude-code/issues/3382.
- **Implies.** The bare model already gives a generic list; that is the baseline to beat. VAFER's edge is the user's context (conversation, files, code), facts from the web, and one agent free to say the premise is wrong. No praise, no filler.
- **Confidence.** Medium. The product reviews are anecdotal; the evidence on flattery is strong.

### F11. Speed and cost decide whether people keep using it

- **Finding.** superpowers#743 (27 comments): "With plain claude code it's done in 2 minutes" and "Slow. Bye tokens." Anthropic reports that multi-agent runs use about 15 times the tokens of a chat, and that they suit broad questions with independent directions. claude-council uses 100–200k tokens per question; skipping peer review halves that. Codex runs at most 6 subagents at once, and they cannot start their own.
- **Evidence.** https://github.com/obra/superpowers/issues/743 (2026-03-15); https://www.anthropic.com/engineering/multi-agent-research-system (2025-06-13); claude-council README; `docs/research/2026-10-30-v0.0.5-review/notes/hosts.md`:35-38.
- **Implies.** Brainstorming is broad, so parallel agents fit. Target 1–3 minutes: at most 5 agents in one wave (within Codex's limit of 6), one round and short briefs. Without subagents, run the lenses one after another in one context. Without web access, drop the web lens and say so in one line.
- **Confidence.** Medium.

### F12. A first-step skill must know when to stay out

- **Finding.** Some users run brainstorming as "the entrypoint to all work" (#2530). Others say forceful wording makes it fire too often (#2514, #2377) and the work grows "once the chain started (brainstorming → plan → SDD on a request that should have been a one-page note)". A manual-only mode was declined (#2000); a fork sets `allow_implicit_invocation: false`.
- **Evidence.** https://github.com/obra/superpowers/issues/2514 (2026-10-14); https://github.com/obra/superpowers/issues/2000; https://github.com/ChenTingToDo/brainstorming-manual.
- **Implies.** Say when to skip: specific, mechanical or settled requests go straight to work. Use no "MUST" wording. End by proposing the next module (planning, research or frontend), and wait for the user's go.
- **Confidence.** Medium.

### F13. What the output should look like

- **Finding.** Useful shapes: attribution with dissent kept (claude-council), clear verdicts (research-companion), a source per item (cc-tree). Users reject vague output (BMAD#2011), dropped soft ideas (BMAD#1674), words without content (superpowers#2530) and stock phrases (Claude Code#77136, 139 comments).
- **Evidence.** As cited in F5–F9; https://github.com/anthropics/claude-code/issues/77136 (2026-07-13).
- **Implies.** Fit the output on one screen, in the user's language:
  - 5–8 items, most important first;
  - for each item, what the user may have missed, why it matters, and what to do or which module comes next;
  - a source link for each web fact;
  - dissent kept;
  - a two-line "decided / still open" handoff;
  - no closing question.
- **Confidence.** Medium (a synthesis of the sources above).
