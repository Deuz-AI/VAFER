# External sweep: best-in-class deep research, late October 2026

Date: 2026-10-30. This sweep covers what the 2026-10-27 sweep (`docs/research/2026-10-27-deep-research-sota/research-*.json`) missed and repeats none of it. Method: 33 web searches and about 25 page reads. "Adoptable" means a skill of instructions plus a small stdlib Python script, running in Claude Code or Codex, could do it.

## Summary

Since the 10-27 sweep, three things matter for v0.0.5. (1) Speed: the cheapest verified levers are several tool calls per turn (−40.6% wall time and −35.9% cost at equal accuracy in one paper), a visible search budget (−40% searches at equal accuracy) and stopping on evidence sufficiency and zero novelty rather than on a query count. Reading whole pages is not the bottleneck. (2) Checking: sentences the model writes itself are unsupported 2.3–4.4× as often as copied ones, and the number/date/quote match cannot see them. Verifier strictness alone moves measured unsupported rates from 3% to 18%. Anchoring sentences to receipt IDs and BM25 re-attribution are cheap, scriptable fixes. (3) On Claude Code the real baseline is the bundled /deep-research, which refutes claims against quotes but never searches a second time. No new open-source architecture appeared, and LangChain's open_deep_research is archived.

## Findings

**F1. Claude Code's bundled /deep-research is the comparator. Its weak spot is the missing second hop.**
Evidence: N. Balic, "An autopsy of Claude Code's deep research", Steel blog, 2026-06-10, https://steel.dev/blog/claude-code-deep-research-autopsy (v2.1.170, Opus 4.8). The flow has five steps: 5 angles; 5 parallel searchers; deduplicated URLs capped at 15 sources; 2–5 claims per source, each with a direct quote and a source grade; and 3 skeptics per claim, where 2 rejections kill it. A final synthesizer lists the killed claims. In one run this took about 13 min, 98 agents, 533 tool calls and 2.36M tokens. The funnel went 77 claims → 25 verified → 21 confirmed → 7 findings. The author's verdict is that it "searches wide and never doubles back".
Implies: the 8.6-vs-5.8 test was against the bare model. On Claude Code, VAFER has to beat this workflow. VAFER has three things the workflow lacks: the gap wave (a second hop), the conflict ladder and the figure check. VAFER lacks a claim-level check on prose. Add /deep-research as an arm of the v0.0.5 side-by-side. Adopt the refute-against-the-quote check for headline claims only.
Confidence: medium (one third-party analysis of one run).

**F2. Several tool calls per turn is the cheapest verified wall-time lever.**
Evidence: Lin et al., "W&D", arXiv 2602.07359, 2026-02-07, on GPT-5-medium and 100 BrowseComp tasks. With 3 calls per turn instead of 1, accuracy was 68% vs 66%. Turns fell from 45.7 to 23.8, cost by 35.9% and wall clock by 40.6%. The "descending" schedule (wide first, then narrow) scored best, at 74%.
Implies: the researcher brief should ask for 3–5 searches in the first message, then a batch of opens and follow-ups in each later turn, narrowing as rows close. SKILL.md says this only for Quick and in rule 3. Count turns per researcher in the side-by-side. Adoptable: yes, by instruction.
Confidence: medium (a short-answer benchmark and one model).

**F3. A visible budget cuts searches without losing accuracy.**
Evidence: Liu et al. (UCSB, Google, NYU), arXiv 2511.17006, 2025-11-21. A block each turn showed the budget used and the budget remaining. At equal budgets it added 1.0–2.6 points for Gemini 2.5 Pro/Flash and Claude Sonnet 4. With a budget of 10 it matched ReAct with 100 (12.8% vs 12.6% on BrowseComp, Gemini 2.5 Pro), using 40.4% fewer searches and 31.3% less cost.
Implies: turn commit a927973's guide of 6–10 searches into a running tally the researcher keeps in its notes ("searches 5/8, opens 3/6"), with the remainder spent only on open rows. Adoptable: partly, since the subagent must count for itself.
Confidence: low to medium (absolute accuracies are low).

**F4. Stop on evidence, not on a count. Most late steps add nothing.**
Evidence: arXiv 2608.01913 (2026-08-03, BrowseComp-Plus) found that accuracy tracks cumulative retrieval recall, not search count. Useful evidence arrives early, then comes a long tail of low-yield steps, and the best agents issue far fewer redundant queries. RAAC (arXiv 2608.15191, 2026-08-15) uses novelty plus coverage to decide whether to continue, redirect or stop. It cut about 14 searches per task and raised accuracy by 3% on average (up to 10%). EDR (arXiv 2604.24978, 2026-04-27) sets explicit sufficiency conditions per step to prevent premature stopping. In HypoSearch (arXiv 2609.01294, 2026-09-01), bounded hypothesis branches beat 5-way parallel trajectories with fewer calls.
Implies: plan rows already name their settling record, so make that record the stop condition. A row closes when that record, or two independent ones, is in hand. A section stops after a batch that adds no new URL or fact. Tried queries are listed so they are not rerun. The only place to branch is between conflicting accounts, through the adjudicator. Adoptable: yes.
Confidence: medium.

**F5. Reading whole pages is not what makes runs slow, and filtering pages hurts open-ended reports.**
Evidence: GPT-Researcher v3.7.0 (2026-09-26), evals/context_filter/README.md in github.com/assafelovic/gpt-researcher. The test replayed 28 tasks on identical sources with a gpt-5.4 writer and judged pairs in both orders. On the 8 open-ended tasks, unfiltered pages beat filtered context 8/0/0, at 65–83% more cost, and still gave shorter reports. Writing took about 45 s whatever the input size. BM25 keeping the chunks that score at least 50% of the best one matched embeddings (14/8/6) in 0.02 s.
Implies: cut serial turns (F2) and low-yield searches (F4), not reading. A stdlib BM25 in vafer_check.py can rank snapshot passages for each sentence (F8, F9). It also lets a researcher read the relevant part of a long snapshot without a second WebFetch.
Confidence: low to medium (n=28, a vendor test, one judge family).

**F6. Keep researchers on the strong model and use cheap models only for mechanical checks.**
Evidence: DeepSearchQA, arXiv 2601.20975 (Jan 2026): "a step-function drop in utility" when scaling down. F1 was 22.24 for Claude Haiku 4.5, 27.85 for Sonnet 4.5 and 40.20 for Opus 4.5. Separately, the 10-27 sweep found cheap judges competitive at checking citations (arXiv 2607.08700).
Implies: researchers and the adjudicator stay on the main model. The support verifier (F8) may run on a smaller model, through the Claude Code Agent `model` field or a Codex custom agent.
Confidence: medium.

**F7. Live WebFetch behaviour in this session (Claude Code 2.1.314) confirms the 10-28 spike and changes two of its conclusions.**
Evidence: this session's WebFetch results, 2026-10-30; the spike itself was only predicted. On arxiv.org/abs/2602.07359 and /2609.01294, WebFetch refused to reproduce the abstracts, citing its 125-character quote limit. For an ACL Anthology PDF, the model saw only compressed bytes. The tool did save the PDF to the session's tool-results folder, and pdftotext extracted 5,054 words from it locally. Pages over 100,000 characters now come with an `offset` that reads on. A cross-host 308 redirect was returned rather than followed, one site answered 403, and responses are cached for 15 minutes.
Implies: receipts still come from snapshots. Amend hosts.md: the 100k cut is no longer final, and a PDF the shell cannot download may already be on disk after WebFetch. vafer_check.py could take that file as the snapshot, turning a † into a checked receipt.
Confidence: high for what was observed, though the PDF save was seen only once.

**F8. The risky sentences are the ones the model writes itself, and the current check cannot see them.**
Evidence: "Copying Is Not Grounding", arXiv 2610.18442, 2026-10-13. Across 4 models and 5 corpora, sentences a model writes itself are unsupported 2.3–4.4× as often as sentences it copies. A sentence counts as copied when at least half its words sit inside verbatim matches of 5 or more words. On human labels (RAGTruth) the rates are 12.2% vs 1.9%.
Implies: paraphrased, translated, synthesized and editor-rewritten sentences pass vafer_check unchecked. Proposed triage: the script computes each cited sentence's copy share against its snapshot. Low-share headline sentences go to one fresh-context verifier, along with every sentence the editor changed. Headline sentences are the answer, the "Bir bakışta" table and the verdicts. The verifier reads the BM25 top passages and answers supported, partial or unsupported. Turkish reports built on foreign sources are almost all "authored", so cap the verifier at 10–20 sentences. Adoptable: yes.
Confidence: medium (question-answering tasks, small models, but the result holds on human labels).

**F9. Measured support rates depend on the verifier, so flags need a fixed protocol and re-attribution.**
Evidence: arXiv 2607.20527, 2026-07-10. On identical outputs, the unsupported-citation rate ranges from about 3% to 18%, depending only on verifier strictness. Agreement among verifiers on what to flag is 0.27–0.30. Deterministic BM25 re-attribution matched the best open generator.
Implies: fix one verifier brief with a stated strictness, and name it next to any rate. Before calling a sentence unsupported, the script tries BM25 re-attribution across all the run's snapshots, because the support often sits on another cited page. "Unsupported" stays a flag the lead answers. Use the same verifier to compare v0.0.4 with v0.0.5.
Confidence: medium.

**F10. Anchoring each sentence to receipt IDs at write time makes claim checks and stage tracing nearly deterministic.**
Evidence: CAMS, arXiv 2606.23989 (v5, 2026-09-11) links atomic claims to verbatim spans and clusters equivalent claims across documents. It flags conflicts and ends each sentence with claim IDs. Multi-source attribution accuracy rose from 38% to 64%, and human verification time per claim fell 3.4×. DEER, arXiv 2512.17776 (v5, 2026-07-13), checks uncited claims too. Claims that share a URL are verified together on claim-relevant chunks. PING (arXiv 2601.22984) and VeriTrail (arXiv 2505.21786, ICLR 2026) show that errors propagate across stages and are best traced to the stage that made them.
Implies: give receipts short IDs and have section drafts carry them after each sentence, for example as an HTML comment, which the editor must keep. check.md can then list factual sentences that have no receipt. It can also say whether a failure began in the receipt, the draft or the edit. Adoptable: yes, with a few brief lines and a parser.
Confidence: medium (the evidence is from summarization, not web research).

**F11. Fabricated and dead URLs are common, and a liveness check nearly removes them.**
Evidence: Rao, Wong and Callison-Burch, arXiv 2604.03173, 2026-04-03, over 221k citation URLs. Of these, 3–13% were hallucinated (no Wayback record) and 5–18% did not resolve. Deep research agents hallucinate URLs more often than search-augmented LLMs. Their urlhealth tool cut non-resolving URLs 6–79×, to under 1%.
Implies: vafer_check should flag each cited URL that has neither a snapshot nor a receipt. When the shell has network, it should also test liveness for citations read only through WebFetch. Adoptable: yes (stdlib).
Confidence: high.

**F12. To spot copies of one account, text overlap finds mirrors, but paraphrased retellings need provenance on the receipt.**
Evidence: Tumre et al. (TCS), NAACL 2025 Industry (PDF read). MinHash and SimHash work on copies that share their surface text but degrade on well-paraphrased rewrites. Engineering repos give each cluster of copies one vote, using shingle Jaccard ≥ 0.8 (github.com/maguerrieri/provenance #212); these are unvalidated proposals. The CircularCheck thesis (Tartu, 2025) found self-referencing citation structures the most reliable sign of circular reporting. No study measures how often LLM researchers count copies as independent.
Implies: vafer_check can compute 5-word-shingle Jaccard between the snapshots cited for one fact and print "one account: [3] [7] [9]". Paraphrased retellings are the likely pattern on local-history topics such as Yalova, where municipal pages, blogs and Wikipedia retell one another (inferred; I did not check this against the run). For those, researchers record whom a page cites or copies ("via [5]"), and the check counts distinct origins.
Confidence: medium on the method, low on its impact.

**F13. Within the deep-research tier, longer reports do not score better, and judges of long reports are unstable.**
Evidence: in Caesar (arXiv 2604.20855, v3 2026-05-08), length correlated with judge score at r = 0.47 across all agents but −0.13 within the deep-research tier. DEER found little link between word count and scores across 800 reports. In GPT-Researcher's test (F5), the preferred reports were shorter. LongJudgeBench (arXiv 2606.01629, v4 2026-08-28) found long-form judges unstable across scenarios.
Implies: keep the answer first. Give each tier a word guide rather than a minimum, and have the editor cut repetition. Judge at least one length-matched pair.
Confidence: low to medium.

**F14. Products since mid-2026 split into fast and max modes and compose search in code, with little new citation checking.**
Evidence: Google's "Deep Research Max" post (2026-04-21) describes two agents on Gemini 3.1 Pro. Deep Research is "optimized for speed and efficiency" for interactive use. Max uses "extended test-time compute" for background jobs. No verification step is described. Perplexity's "Rethinking Search as Code Generation" (2026-06-01) has the model write Python over search primitives: fan-out, extract, URL and key dedupe, filter and rerank. State is kept in files, and the model plans from a coverage summary. Its self-reported scores are DSQA 0.871 and BrowseComp 0.805 (GPT-5.5), and token use fell 85.1% in a CVE case. I found no documented OpenAI deep-research change after March 2026, when the legacy mode was removed (per release notes seen in search results), and no new documentation for Research on claude.ai.
Implies: at 22 minutes, VAFER Standard sits near "max". v0.0.5 should give Standard a time target set from the side-by-side, with the 13.5-minute first draft as a reference point. Search as code is not adoptable, because host search is not callable from Python. Its principles of deduplication, state on disk and planning from a coverage summary are already in VAFER.
Confidence: medium (vendor pages, few numbers).

**F15. Open source offers no new architecture, and the main competitor samples its non-numeric citation checks.**
Evidence: GitHub API, 2026-10-30. langchain-ai/open_deep_research is archived (last push 2026-08-10), and LangChain's work now goes into deepagents. GPT-Researcher released v3.7.0 (2026-09-26). STORM was last pushed 2025-09-30, Tongyi DeepResearch 2026-02-27 and MiroThinker 2026-07-06. hyperresearch released v0.13.0 on 2026-10-27, after the teardown's v0.12.0. It formalizes Codex support with a Stop hook and enforces source and note count ceilings. Its notes say the cite-check "Goal states that non-numeric citations are sampled".
Implies: checking the support of every headline sentence (F8–F10) would be a measurable difference from hyperresearch. It also matches the teardown's 5× candidate metric, unsupported load-bearing claims per report.
Confidence: high for the repository facts.

**F16. The newest benchmarks use real-user tasks with value-, date- and URL-level rubrics, and none is in Turkish.**
Evidence: LifeSearch (arXiv 2610.18092, 2026-10-13) has 203 Chinese and English real-user tasks and over 4,000 rubrics covering values, units, dates and URLs. The best of 12 agents, GPT-5.6 Sol, scored 63.4%, and judge and human rankings agreed at ρ = 0.89. DailyReport (arXiv 2606.12871, 2026-06-11) found that all 17 systems fall short on 150 everyday tasks. In DeepResearch Bench II v3 (2026-09-10), the strongest systems satisfy fewer than 50% of the rubrics. STALE (arXiv 2605.06527) shows that agents recognize an outdated memory yet fail to apply the update.
Implies: score the side-by-side on coverage plus value, unit, date and URL correctness for about 10 claims, as the 10-29 judge did. Add one post-cutoff or local Turkish question besides Yalova. In Reuse, re-check time-sensitive rows from an earlier run rather than reloading them.
Confidence: medium.

## Could not verify

- Claims seen only in secondary sources: the Fable 5 multi-agent "0.8× median speedup" cited by Steel, PTAH's 1,328 s → 459 s (arXiv 2605.29861), and Perplexity Computer routing work across 20+ models (MarkTechPost returned 403). FlashResearch's "up to 5×" (arXiv 2510.05145) is the authors' own claim.
- No measurement exists of how often LLM researchers count copies of one account as independent, or of small-model researchers inside Claude Code.
