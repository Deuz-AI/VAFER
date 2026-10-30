# Ideation science for the brainstorm skill

2026-10-30. About 35 searches and fetches. Key numbers were checked in the primary papers unless a finding says "secondary".

## Summary

LLM brainstorming fails mostly through sameness, not low quality. One model sampled many times, many agents, or several vendors all converge on the same few ideas (only 5% unique out of 4,000; 0.71 to 0.82 similarity between different models), and LLM help makes the ideas of a group of people more alike. Prompt structure widens the spread more cheaply than extra agents: list the obvious ideas first and then push past them, ask for ideas with probabilities, and use specific roles written as one set. Independent generation followed by pooling beats discussion. Debate rounds add little over a vote and can flip right answers to wrong ones. Synthesis and peer ranking favor long, mainstream answers. Neither people nor models notice omissions unless someone walks them through categories. LLMs rank ideas by value at about chance, but they can flag common ideas and merge duplicates.

## Findings

**F1. More samples, agents or vendors do not buy diversity.**
- Evidence: Si, Yang & Hashimoto, https://arxiv.org/abs/2409.04109 (2024-09-06): of 4,000 seed ideas per topic, only about 200 (5%) were unique at cosine ≥ 0.8. "Artificial Hivemind", https://arxiv.org/abs/2510.22954 (2025-10-27): at temperature 1.0, 50 answers to one query averaged above 0.8 similarity in 79% of queries, and different models averaged 0.71 to 0.82 similarity to each other. Wenger & Kenett, https://arxiv.org/abs/2501.19361 (2025-01): many LLM families answer more alike than humans do.
- Implication: adding agents, re-rolling or mixing vendors will not widen the spread. Use 3 to 5 agents and spend the instruction text on making them differ.
- Confidence: high.

**F2. LLM help raises the average idea and narrows the spread.**
- Evidence: Doshi & Hauser, https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/ (2024-07-12): stories written with 5 GPT-4 ideas were rated 8.1% more novel and 9.0% more useful, but were more alike. Meincke, Nave & Terwiesch, https://www.nature.com/articles/s41562-025-02173-x (2025-05): idea pools made with ChatGPT were less diverse in 37 of 45 comparisons (institute summary). Anderson, Shah & Kreminski, https://arxiv.org/abs/2402.01536 (2024-02): users of one model converged on the same ideas; the authors suggest showing users what the model usually suggests.
- Implication: the value is in what is not obvious. Put "what any assistant would say" in one short, labelled block, and spend the rest of the output on what differs from it.
- Confidence: high for the effect; medium for the label as a fix.

**F3. "List the obvious, then push past it" is the cheapest strong lever.**
- Evidence: Meincke, Mollick & Terwiesch, https://arxiv.org/abs/2402.01727 (2024-01-27), 35 prompts with 1,000 GPT-4 ideas each. The best prompt was "first list 100 short titles; then make them bolder and more different, no two the same; then describe". It scored cosine 0.255, against 0.386 for the base prompt and 0.243 for groups of humans, and raised the estimated number of unique ideas from 3,700 to 4,700. Celebrity personas barely helped, and pools from different strategies overlapped little. People's later ideas are also more original (Beaty & Silvia, https://beatylab.la.psu.edu/files/2020/08/2012_Beaty_PACA.pdf, 2012).
- Implication: each generator first writes the obvious ideas as bare titles, then replaces each one or goes past it. Give agents different strategies, not only different names. This works in one context, without subagents.
- Confidence: medium-high (one domain, one model).

**F4. Ask for ideas with probabilities, and keep the unlikely ones.**
- Evidence: Zhang et al., "Verbalized Sampling", https://arxiv.org/abs/2510.01171 (2025-10-01): asking for "5 responses with their probabilities" gave 1.6 to 2.1 times the diversity of a direct prompt in creative writing, with quality about the same. Asking for responses below a probability threshold raised diversity further, and larger models gained more.
- Implication: add one line per generator: "give N ideas, each with your estimate of how likely a typical assistant is to suggest it; at least half below 0.10". The estimates also mark the obvious ideas for the merge.
- Confidence: medium-high (tested on writing, not on planning ideas).

**F5. Roles help when they are specific and written as one set.**
- Evidence: Lu et al., "LLM Discussion", https://arxiv.org/abs/2405.06373 (2024-05): four role-playing agents discussing over 5 rounds beat a single agent on originality on all four creativity tests (for example 3.47 → 4.44 on a 1-to-5 scale, judged by an LLM). Elicitron, https://arxiv.org/abs/2404.16045 (2024-04): personas written one after another in one context covered far more ground than personas written in parallel (0.87 vs 0.27 on a spread measure). Solo Performance Prompting, https://arxiv.org/abs/2307.05300 (2023-07): detailed personas made for the task beat fixed ones; only strong models benefited.
- Implication: the lead writes all lenses in one pass, each told to differ from the ones before it, and ties each to the prompt's stakes: the end user, whoever pays, a regulator, someone who tried and failed, an outsider. The lenses then run in parallel, or in one context without subagents.
- Confidence: medium.

**F6. Generate independently, then pool.**
- Evidence: Mullen, Johnson & Salas, https://doi.org/10.1207/s15324834basp1201_1 (1991 meta-analysis): groups brainstorming together produce fewer and worse ideas than the same number of people working alone. Kohn & Smith, https://doi.org/10.1002/acp.1699 (2010): seeing others' ideas narrowed the categories people explored, and their ideas came to match their partners'. GPT-4 behaved the same way: sessions that pooled ideas and picked the best 10 gave a less diverse pool (0.428) than one base prompt (0.386) (Meincke 2024, F3).
- Implication: agents in the first wave never see each other's output or a draft list. The merge keeps one idea per cluster instead of voting for "the best".
- Confidence: high for humans; medium for the transfer to LLMs.

**F7. Extra discussion rounds mostly cost time.**
- Evidence: Choi, Zhu & Li, "Debate or Vote", https://arxiv.org/abs/2508.17536 (2025-08): across 7 benchmarks, a simple majority vote explains most of the gain credited to debate. Wynn, Satija & Hadfield, https://arxiv.org/abs/2509.05396 (2025-09-05): agents often drop a correct answer to agree with peers, and longer debates are sometimes worse. VirSci, https://arxiv.org/abs/2410.09403 (2024-10): novelty fell after a moderate number of turns. Counterpoint: Liang et al., https://arxiv.org/abs/2305.19118 (2023-05): a model reviewing its own answer stays stuck in its first framing, while an agent assigned the opposite side brings new thoughts.
- Implication: run one wave by default, so wall time is the slowest agent once. Run a second pass only for a different job: an assigned opposing view against the top few ideas, or deepening the ideas the user picks. No open "discuss and agree" rounds.
- Confidence: medium-high.

**F8. Synthesis and peer ranking favor long, mainstream answers.**
- Evidence: Karpathy's llm-council, https://github.com/karpathy/llm-council (2025-11-22): models answer alone, rank each other anonymously, then a chairman model writes the final answer. A secondary report (https://www.cxodigitalpulse.com/?p=40938) says the models kept ranking GPT-5.1 best, while Karpathy found it "a little too wordy" and disagreed. LLM judges favor longer answers and their own outputs (Zheng et al., https://arxiv.org/abs/2306.05685, 2023-06; Panickssery et al., https://arxiv.org/abs/2404.13076, 2024-04). LLM summaries under-represent minority views (Zhang et al., https://arxiv.org/abs/2311.07884, 2023-11).
- Implication: the lead clusters ideas instead of "writing the best answer", lists the ideas only one lens produced, caps each idea's length, and hides authorship if agents review each other.
- Confidence: medium (the Karpathy report is anecdotal; the bias papers are solid).

**F9. Nobody notices what is missing unless walked through categories.**
- Evidence: Fischhoff, Slovic & Lichtenstein, https://www.gwern.net/doc/statistics/prediction/1978-fischhoff.pdf (1978): people, experienced mechanics included, barely noticed when parts of a "car won't start" fault tree were removed (abstract and secondary; the PDF is a scan). Yang et al., https://arxiv.org/abs/2505.13360 (2025-05): LLMs correctly guessed requirements a prompt left out only about 41% of the time.
- Implication: the gap pass checks the prompt against a fixed list (F13) and reports only items the prompt is silent on that matter here. "Did we miss anything?" is not a method.
- Confidence: high.

**F10. Pre-mortem: state the failure as certain.**
- Evidence: Mitchell, Russo & Pennington, https://doi.org/10.1002/bdm.3960020103 (1989): outcomes stated as certain drew longer, more concrete explanations. The popular "30% more reasons" is secondhand (Klein, https://hbr.org/2007/09/performing-a-project-premortem, 2007-09). Veinott, Klein & Wiggins, https://researchr.org/publication/VeinottKW10 (2010; 178 people): the pre-mortem cut overconfidence more than a critique or a pros-and-cons list (secondary). No study shows better real outcomes.
- Implication: one lens reads: "It is six months later and this failed. Explain why, as fact." It returns risks, not verdicts.
- Confidence: medium.

**F11. An assigned opposing view and distinct perspectives beat a generic critique.**
- Evidence: Schweiger, Sandberg & Ragan, https://doi.org/10.2307/255859 (1986): groups told to argue an opposite plan, or to play devil's advocate, produced better assumptions and recommendations than groups seeking agreement. Basili et al. (1996; https://www.cs.umd.edu/projects/SoftEng/ESEG/topics/rtfault2.html): reviewers reading from different stakeholder perspectives found few defects in common, so together they covered more (secondary). Models also tilt feedback toward the user's stated view (Sharma et al., https://arxiv.org/abs/2310.13548, 2023-10).
- Implication: give each critic a named perspective and 2 or 3 concrete questions. Include one lens that lists what must be true and sketches the opposite plan. Tell every lens it may challenge the user's premise.
- Confidence: medium.

**F12. Questions surface what users did not think of.**
- Evidence: Li, Tamkin, Goodman & Andreas, https://arxiv.org/abs/2310.11589 (2023-10): questions asked by the model captured preferences better than prompts users wrote themselves in 2 of 3 domains, took no more effort, and raised points users had not anticipated. In Elicitron (F5), simulated users raised more hidden needs than a human interview baseline (untested for significance).
- Implication: end with at most 3 questions only the user can answer (values and trade-offs). One lens may act out the end user's day to find hidden needs. No interview before starting.
- Confidence: medium.

**F13. A compact checklist of what requests leave out.**
- Evidence: DARPA's Heilmeier questions, https://www.darpa.mil/about/heilmeier-catechism (1975–77): the goal without jargon, how it is done today, what is new, who cares, risks, cost, time, and how success will be checked. Kahneman, Lovallo & Sibony, https://hbr.org/2011/06/the-big-idea-before-you-make-that-big-decision (2011-06): 12 checks, including real alternatives, dissent, sunk cost and the worst case. Browning, https://i2insights.org/2019/11/05/detecting-unknown-unknowns-in-projects/ (2019-11-05): look at the result, process, people, tools, goals and context.
- The checklist:
  1. the goal and the why behind it
  2. who it is for, and who decides and pays
  3. how success will be checked, and when
  4. constraints: budget, time, skills, platform, language
  5. current practice and prior art
  6. alternatives, including doing nothing, buying, or a smaller version
  7. risks and failure modes
  8. assumptions that must hold
  9. dependencies: people, data, systems, approvals
  10. legal, safety and privacy issues
  11. second-order effects: what changes downstream, at scale, over time
- Implication: this list is the gap pass. Report at most about 5 items the prompt is silent on.
- Confidence: medium-high (standard practice lists, not tested together as a set).

**F14. LLMs cannot rank ideas by value.**
- Evidence: in Si et al. (F1), the best LLM judge agreed with expert reviewers 53.3% of the time, against 56.1% for experts with each other and 50% for chance. Wen et al., https://arxiv.org/abs/2506.00794 (2025-06): off-the-shelf frontier models did no better than chance at predicting which of two research ideas would work better. Si, Hashimoto & Yang, https://arxiv.org/abs/2506.20803 (2025-06-25): once 43 experts carried the ideas out, LLM ideas lost more score than human ideas, reversing the ranking.
- Implication: never give a "best idea" verdict or scores. Order ideas by properties anyone can check, and let the user pick.
- Confidence: high.

**F15. Cheap filters for generic ideas.**
- Evidence: models can judge how unusual an idea is: fine-tuned LLM scores on a standard creativity test correlated up to r = .81 with human raters (Organisciak et al. 2023, https://openscoring.du.edu/research). They cannot judge whether an idea is new to its field: the AI Scientist's literature check often labeled established methods, such as micro-batching for SGD, as novel (Beel et al., https://arxiv.org/abs/2502.14297, 2025-02).
- Implication: cheapest first: (1) merge near-duplicates by meaning; (2) demote ideas on the obvious list or with a high stated probability (F4); (3) require each remaining idea to say how it works and what to check first; (4) for the 1 to 3 ideas the user picks, search for prior work (vafer-research or WebSearch) instead of trusting the model's memory.
- Confidence: medium.

**F16. Generate many, then let the user pick from a varied shortlist.**
- Evidence: Girotra, Meincke, Terwiesch & Ulrich, https://mackinstitute.wharton.upenn.edu/2023/new-working-paper-finds-chatgpt-a-better-innovation-ideator-than-mba-students/ (2023): GPT-4's product ideas had higher average purchase intent than students' (46.8% vs 40.4%), and most of the top ideas were GPT-4's (secondary). In Si 2024, the same AI ideas scored 5.81 for novelty when a human chose them and 5.64 when the AI did (a small gap, not tested).
- Implication: ideas are cheap; choosing is the hard part, and the user is the best judge available (F14). Show 6 to 10 ideas, one per cluster, each with a line on why it might matter and what to check first.
- Confidence: medium-high.

## What the evidence implies, and what is missing

- Implied flow: lenses written in one pass, plus the obvious list; one parallel wave of isolated agents; a merge that clusters and keeps single-lens ideas; a gap pass against F13; at most 3 questions; a second pass only for ideas the user picks.
- Not found: no test of a round that shows agents all ideas so far and asks only for new ones (seeing others' ideas narrows people, F6, so it is untested). No study on Turkish prompts or on Claude Code or Codex subagents. Most diversity numbers measure text similarity on product or writing tasks.
