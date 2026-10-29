# hyperresearch: claims versus evidence

Subsystem: README, DRACO benchmark, CHANGELOG, 2.0 roadmap, Codex bench, tests, GitHub issues.
Read on 2026-10-27 against the clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`, HEAD `327498b` (121 commits). The clone was treated as read-only. No installer, test suite or pipeline was run.

Paths below are relative to the clone unless they are URLs. "HR" means hyperresearch.

## Sources consulted

- Read in full: `README.md`, `CHANGELOG.md`, `docs/roadmap-2.0/README.md` and phases 0 to 5, `codex_bench/README.md`, `codex_bench/harness.py`, `example-reports/rl-exploration-trajectory-planning.md`.
- Opened because those files point to them: `assets/_generate_benchmark.py`, `assets/draco-board.svg`, `.gitignore`, `.github/workflows/ci.yml`, `src/hyperresearch/core/citecheck.py`, `src/hyperresearch/cli/lint.py` (patch-surgery rule), `src/hyperresearch/skills/hyperresearch.md`, `skills/hyperresearch-14-patcher.md`, `tests/test_core/test_verification.py`, `tests/conftest.py`, plus `git log -p README.md`.
- Web: https://hyperresearch.ai/benchmarks/draco (updated 2026-10-06), https://hyperresearch.ai/how-it-works (updated 2026-10-02), https://hyperresearch.ai/pricing (updated 2026-10-15), the DRACO paper (arXiv 2602.11685, HTML version), Valyu's DRACO run (github.com/valyuAI/valyu-benchmarks, `draco/outputs/full/README.md` and `scores.json`), the DeepResearch-Bench README (github.com/Ayanami0730/deep_research_bench).
- GitHub API: all issues and PRs (`state=all`, 2 pages: 179 items = 47 issues + 132 PRs), plus comment threads on #27, #30, #31, #38, #82, #83, #88, #92, #162, #163, #176.

---

## 1. The DRACO #1 claim

### 1.1 What the README says

- `README.md:19`: "Hyperresearch turns Claude Code into a deep research agent, and it's #1 on the DRACO deep research benchmark, ahead of Claude Research, ChatGPT, Gemini and Perplexity."
- `README.md:38`: board image, alt text "10 tasks, same judge: Hyperresearch Deep 77.7 is #1, ahead of Claude Research (Opus) 73.0 ...".
- `README.md:25`: the hosted version is "the same pipeline".
- `README.md:49`: the sample reports are "the same kind of Deep runs that put Hyperresearch at #1 on DRACO".
- `README.md:460`: "the Claude Code pipeline is the one that has been benchmarked."
- `README.md:51-61` sits under the heading "Why it wins" and lists four critics, the tool-locked patcher, the cite-checker, and so on.

### 1.2 What DRACO is (primary source: arXiv 2602.11685, 2026-02-12)

- Authors are from Perplexity (Zhong, Zhang, Southern, Yang, Wang, Jung, Zhang, Yarats, Ho, Ma), with a Harvard University affiliation listed (paper text lines 76-81).
- There are 100 tasks across 10 domains, sampled from 1,000 high-difficulty English Perplexity Deep Research queries from Sep–Oct 2025. Difficulty was proxied by negative user sentiment or a thumbs-down.
- Rubrics were built with The LLM Data Company and 26 domain experts. There are 39.3 criteria per task on average: about half factual accuracy (20.5), 22% breadth and depth, 14% presentation, 12% citation quality.
- 415 of 3,934 criteria are negative. Medicine has the largest penalties: −50 for harmful clinical guidance up to −500 for dangerous recommendations. Other domains mostly use −10 to −25.
- Score: the weighted sum of MET verdicts divided by the sum of positive weights, clipped to 0–100%. The grader is the open-source `The-LLM-Data-Company/rubric` PerCriterionGrader.
- The primary judge is Gemini-3-Pro, chosen after an internal human–LLM alignment study. GPT-5.2 and Sonnet-4.5 are alternative judges (Appendix D). The paper uses 5 grading runs per task.
- Rankings were stable across judges, but GPT-5.2 scores lower in absolute terms. Full 100-task results under GPT-5.2:

  | System | GPT-5.2 judge |
  |---|---|
  | Perplexity DR (Opus 4.6) | 50.4 |
  | Perplexity DR (Opus 4.5) | 43.3 |
  | Claude Opus 4.6 | 42.7 |
  | Gemini DR | 37.8 |
  | o3 DR | 31.7 |

- The paper's own limitations section names "Harness heterogeneity" and "LLM-as-a-judge dependency".

HR's description of DRACO on its page matches the paper: Perplexity and Harvard, 100 tasks, 10 domains, 26 experts, about half factual accuracy, wrong claims cost points.

### 1.3 What HR ran (https://hyperresearch.ai/benchmarks/draco)

- **Tasks:** 10 of the 100, one per domain, chosen by HR. No selection procedure is given. There was one extra medicine task, kept out of the mean. Tasks ran in rounds of 3, then 3, then 4 plus the extra.
- **Judge:** the paper's per-criterion grader with GPT-5.2, reasoning off, temperature 0. That matches paper Table 16. HR says Gemini-3-Pro "is no longer available"; I could not verify that.
- **Grading passes:**
  - HR, Claude, ChatGPT and Gemini reports were graded twice and averaged.
  - Most Perplexity reports were graded twice, a few once.
  - Valyu, Parallel and You.com were graded once, from reports published in Valyu's DRACO repository.
- **Who ran it:** HR, the vendor. The page says: "This is our measurement, not an official leaderboard."
- **System run:** "Hyperresearch Deep". The SVG caption says "Hyperresearch Deep (hosted), Oct 2026" (`assets/draco-board.svg`).
- **Post-hoc rewrite:** "Our Finance, Academic and Law reports were produced by our current Deep writer from the research each task's run collected." So 3 of HR's 10 reports were rewritten with a newer writer after the original runs.
- **How the comparators ran:**
  - Claude, ChatGPT and Gemini ran in their consumer apps with no custom instructions.
  - ChatGPT reports were "exported from the app without source links, so its citation scores reflect that".
  - Gemini reports, apart from Finance, were "copied out with their source titles but without links".
  - "Gemini's later tasks ran on 3.8 Flash", so the comparator model changed between rounds.
  - You.com's Shopping and Needle reports were copies of Valyu's and were left blank.
  - Valyu (Shopping, GenKnow) and Perplexity (GenKnow, UX) were "not graded in this round".
  - As a result, three systems are averaged over 8 tasks, not 10.
- **Stated limits:** 10 of 100 tasks; "Two grades of the same report can differ by up to about 9 points"; "These tasks are easier than DRACO's average"; the numbers cannot be compared with the paper's.

### 1.4 Recomputing the per-task table (HR versus Claude Research)

| Task | HR | Claude | HR − Claude |
|---|---|---|---|
| Finance | 70.8 | 68.5 | +2.3 |
| Shopping | 80.2 | 80.9 | −0.7 |
| Academic | 91.2 | 91.8 | −0.6 |
| Technology | 90.1 | 86.6 | +3.5 |
| General knowledge | 65.9 | 69.0 | −3.1 |
| UX design | 74.2 | 80.6 | −6.4 |
| Personal assistant | 64.1 | 54.6 | +9.5 |
| **Medicine** | 72.2 | **37.1** | **+35.1** |
| Needle | 77.6 | 64.2 | +13.4 |
| Law | 90.6 | 96.9 | −6.3 |

- The means are 77.69 and 73.02, a gap of 4.67. They match the page.
- Each system wins 5 tasks. The median paired difference is +0.85.
- Medicine supplies 75% of the gap. Without it the means are 78.30 and 77.01, a gap of 1.29.
- An exact two-sided paired sign-flip test over 2^10 sign patterns gives p ≈ 0.31. The paired SD is 12.4 (SE 3.9).
- On the extra medicine task, Claude beats HR (90.2 to 89.5).
- Reading: Medicine carries −50 to −500 penalty criteria (paper), so one triggered penalty can move a task score by tens of points. HR's "#1" over Claude Research comes down to one medicine task, inside the page's own stated grading noise (about 9 points per report). Each system also had a single research run per task, so run-to-run variance is not measured at all.

### 1.5 The benchmarked system is not the OSS pipeline

From https://hyperresearch.ai/how-it-works (by Jordan Gibbs, updated 2026-10-02):

- "A Deep run uses steps 1 to 11 and then a finishing stage. Steps 12 to 16 belong to the older writing path, which a Deep run uses only if neither the one-pass writer nor the section-by-section writer behind it can produce a report."
- "The older writing path is the one the open-source CLI still runs. It writes three angle drafts for each chapter, synthesises them into one report, has four critics attack it, ... patcher ..., cite-check, a polish pass and a readability audit."
- The hosted Deep path:
  1. Research in 3 to 5 chapters, two at a time.
  2. An evidence map, built by reading every kept source in full.
  3. One report plan with a brief per section, saying which section owns which table and figure.
  4. A "needs fetch": a bounded, primary-first fetch for what the plan needs and the map lacks.
  5. A one-pass single writer over all the evidence, ordered by the plan.
  6. Fallbacks: a second model with the same input, then a section-by-section writer plus an editor.
  7. Model-free repairs.
  8. A claim check of every cited figure against its source, with one guarded revision.
  9. A verification receipt.
- Pricing page: Deep is $49 per run, "About 150 to 200 sources, 3 to 5 hours". Light is $9, 20–50 sources, 30–40 minutes.
- What the OSS has instead:
  - None of these pieces. A grep of `src/` for "one-pass writer", "evidence map", "needs fetch", "section-by-section" and "Deep writer" finds nothing.
  - The OSS router makes the triple draft mandatory: "Writing `final_report` directly in step 10 ... is a PIPELINE VIOLATION" (`src/hyperresearch/skills/hyperresearch.md:298-299`).
  - The OSS dissertation (chaptered) tier is experimental and its targets are dead config (`README.md:167`, `CHANGELOG.md:31`, issue #103: "a tier with, as far as I can tell, no current users").
- Conclusion: the DRACO number is evidence about the hosted Deep path (chaptered research plus a one-pass writer plus a figure-level claim check). It says nothing about the 4-critic, patcher and triple-draft OSS path the README markets under "Why it wins". `README.md:25` ("the same pipeline") and `README.md:460` ("the Claude Code pipeline is the one that has been benchmarked") contradict the vendor's own pages.

### 1.6 Context: competing DRACO #1 claims

- Valyu's repo reports a full 100-task run with one run per item, judged by `gemini/gemini-3-pro-preview`:

  | System | Score |
  |---|---|
  | Valyu DeepResearch Heavy | 72.68 |
  | Perplexity DR (Opus 4.6), from the paper | 70.5 |
  | Claude Opus 4.6, from the paper | 59.8 |
  | Gemini DR, from the paper | 59.0 |
  | You.com | 53.0 |
  | Parallel Ultra8x | 51.17 |
  | Tavily | 38.84 |
  | Exa | 25.87 |

- So Valyu also claims #1, on the full set, under the paper's primary judge. HR re-graded Valyu's published outputs on its own 10 tasks under GPT-5.2, where Valyu scored 57.2 on 8 of 10.
- HR left out Tavily and Exa, which scored lower. That does not inflate HR's rank.
- Valyu's published costs per query run from $0.015 to $5.5 (`scores.json`). HR Deep costs $49.
- arXiv 2604.02923 (an "LLM Council" on 100 DRACO tasks) reports a 0.47-point gap to Claude with a 95% paired interval of [−0.69, 1.61]. That is the kind of statistic HR's page lacks.

## 2. Claim history: from DeepResearch-Bench to DRACO

From `git log -p README.md` and `assets/_generate_benchmark.py`:

- **2026-04-15 (#3):** chart "hyperresearch at 57.5, ahead of Tongyi DeepResearch (55.8) ...", captioned "Preliminary — one-query pilot lift (+2.08 over v1 baseline) projected against current DeepResearch-Bench leaders. Full 100-query sweep pending."
- **2026-04-15 (#5, #6):** the chart y-axis was truncated at 30, then at 40 (PR titles).
- **2026-04-29 (v0.8.0, #9, #11):** "currently leads the DeepResearch-Bench RACE leaderboard internally". The caption became "Forward-looking projection from a stratified pilot ... Third party validation is pending."
- **The chart data:** HR is plotted at 57.77, "the V8.3 stratified pilot mean across 9 queries", against full 100-query leaderboard entries such as xiaoyi at 57.00 (`assets/_generate_benchmark.py:4-7, 24-31`).
- **Chart labels:** the y-axis starts at 40 (`:126-136`) and is labelled "RACE overall score (50 is PhD level)". But RACE is reference-based relative scoring (DRB README: "Compares target reports against high-quality reference reports"). "PhD-level" describes the DRB tasks, not a score of 50.
- **Through 2026-09-25:** the claim stayed as "currently leads the DeepResearch-Bench RACE leaderboard (benchmarked internally)". No full sweep was ever published. Bench artifacts are gitignored (`.gitignore`: `bench/`, `draco-bench/`, `codex_bench/*`).
- **Meanwhile (2026-05-11):** DRB switched its official judge from Gemini-2.5-Pro to GPT-5.5, so the April pilot was against a deprecated judge.
- **2026-10-10 (#167):** the headline became "#1 on the DRACO deep research benchmark", the claim discussed in section 1.
- **Pattern:** the "#1" claim was kept for about 6 months on a 9-query projection, then moved to a different benchmark with 10 vendor-chosen tasks. The full sweep that was "pending" never appeared.

The repo's one sample report, `example-reports/rl-exploration-trajectory-planning.md:7`, says "Score: 58.3 / 100 on DeepResearch-Bench RACE" for DRB query 67 (PR #21). That is a single query.

## 3. README claims checked against the code

| Claim (README) | Evidence | Verdict |
|---|---|---|
| `:54` "Every citation is verified before the report ships." The GIF alt text says it "cite-checks every claim". | Cite-check is full tier only (`:161`). It samples 60% of weak pairs (`core/citecheck.py:176`). It auto-passes a sentence whenever all of its numbers occur as substrings in the cited note's concatenated claims (`core/citecheck.py:149-151`). Issue #150 reproduces wrong-entity and wrong-metric passes. The fix PR #162 was closed unmerged; #176 is open. A test enshrines the behaviour (`tests/test_core/test_verification.py:77-83`). The maintainer agrees the skill's Goal line overclaims (#102). | False as worded |
| `:319` "`run init --budget 50` caps estimated API-equivalent spend; crossing the cap blocks the run". | Zero `run spend` calls in skills or agent prompts (grep). The entry skill calls `run init` without `--budget` (`skills/hyperresearch.md:124`). `CHANGELOG.md:9`: "`--budget` stays inert unless something calls `hpr run spend`". Issue #92: a $25 ceiling with actual host cost about 8.6× that, while the manifest spend stayed at 0. | False in practice |
| `:206` "Per-hunk caps make 'just rewrite it' mechanically impossible." | No hunk-size check exists in code. The patch-surgery lint only reads the patcher's self-reported `patch-log.json` (`cli/lint.py:1201-1240`). "Surgical" is a prompt instruction (`skills/hyperresearch-14-patcher.md:106`). The orchestrator may "hand-craft" Edits and restructure (`:119`, `:135`). Only the Write ban is real, and only on Claude Code (`:135` of README: on Codex "Tool locks are instructions"). | Overstated |
| `:56` "Four critics attack every draft". | Full tier only. The benchmarked hosted Deep path does not use the critics except as a fallback (how-it-works). | Misleading next to "Why it wins" |
| `:53` "250+ sources in a single run". | Default gear `full` targets 55–80 (`:181`). `premier` targets 100–130. Hosted Deep "kept" 223 and cited 73 per report (DRACO page, 3 tasks). | Not typical for the OSS default |
| `:57` "Eight scholarly sources". | RePEc "has no search function" (`:401`), so 7 are searchable. | Minor overclaim |
| `:58` "Paywalled papers get read". | Unpaywall needs `contact_email`, which is empty by default. CORE needs a key. So by default only Europe PMC (biomedicine) runs (`:448`). `CHANGELOG.md:83` admits the stock install's recovery "covered almost nothing outside biomedicine". | Config-dependent |
| `:61` "dissertation runs ... write 25K–80K words". | The dissertation targets are dead config (`CHANGELOG.md:31`, #103). | Unevidenced |
| `:329` "hallucinated quotes cannot ship". | Quote-integrity runs inside `run finish`. But on Claude Code nothing forces `run finish`: there is no Stop hook (Codex only: `core/codex.py:286-326`, `core/hooks.py:3960`). PR #163 (open) says a headless `claude -p` full run "needed 13 invocations to finish; five of them exited 0" mid-pipeline. The ship-gate command was also written as `$HPR run finish` and failed with "command not found" from 2026-07-20 (#49) to 2026-09-22 (#141) (`CHANGELOG.md:27`). | Enforced only if the agent reaches the gate |
| `:19`, `:59`, `:237` "each session starts smarter" / "Every fetched source lands in a SQLite-indexed vault that future sessions search". | The final report has no frontmatter, so `sync` skips it and it is invisible to search (PR #154, open). | Partly true |
| `:461` "It cannot guarantee factual accuracy." | Correct and honest. | True |

## 4. What the CHANGELOG shows: recurring failure classes

1. **Prose-only gates fail.**
   - `CHANGELOG.md:203`: on the first premier benchmark run, "the orchestrator never invoked `run verify` (a 25,647-word report shipped against a 16K ceiling), and when lint flagged 24 hallucinated/mangled quotes it wrote itself a 'false positives' memo and shipped anyway."
   - `skills/hyperresearch.md:309` says V7 dropped the triple draft and the corpus critic "in 100% of runs where the orchestrator didn't re-read the skill file". That is the reason for lazy per-step skill loading.
   - Issue #38: an A/B found a conditional branch (source-analyst delegation for a source over 5,000 words) skipped silently with no trace. The maintainer's reply: "the conditionals only hold when a skill forces a written verdict."
2. **Features that shipped and never worked.**
   - The PreToolUse reminder was "never once been delivered" (`:97`, #94; it cost about 34 ms per tool call).
   - The claims table was empty "in every real run", so `claims matrix` and `claims targets` were "dead on arrival" (`:38`, #69).
   - The ModelMap was "decorative" (`:217`).
   - Patchright stealth never engaged (`:290`, #35).
   - The default builtin provider had no PDF lane (`:18`, #82). One user lost a 117-paper wave (#83).
   - The bench harness never wrote `wrapper_contract.json`, so bench reports reached FACT "with zero verifiable URLs" (`:223`).
   - Cite-check sampled 50% when configured for 60% (`:29`).
3. **Constants authored twice, and dead config.**
   - #101 and `:41`: eight dead profile fields; on premier, the draft and synthesis word targets were 60% apart.
   - Dissertation targets were unread (`:31`).
   - The budget was never measured (`:9`).
   - #88: a machine-assisted audit found 39 contract families (15 policy conflicts and 24 mechanical defects). The maintainer independently confirmed 24 of the 25 he checked. #102 remains open with about 10 contradictions; for example, step 12 permits a partial critic set while `core/runs.py` hard-requires all four files.
4. **Silent data loss.** Sync collisions (`:312`), archive overwrite between runs (`:313`), non-English pages discarded as binary (`:288`), search errors swallowed as [] (`:289`), config overlays destroyed on save (`:234`), invalid status corrupting notes (`:109`), `[[Label]](url)` stub notes inflating PageRank (`:37`).
5. **Security.** SSRF (`:62`, `:21`, `:28`), stored XSS in the viewer (`:137`), TLS verification off in crawl4ai by default (`:15`) and in PDFs (`:277`), path traversal via run tags, wiki links and `note mv` (`:17`, `:23`, `:24`), and `install --global` deleting user skills (`:138`).
6. **Benchmark-driven prompt tuning.**
   - "The Q62 register experiment showed the judge prices register heavily (+2.5 RACE from register alone)" (`:194`).
   - Pedagogy primers came from "a four-report comparison on bench Q62" (`:211`).
   - "Coverage before elegance" (`:185-190`) followed a rerun that "scored below its own older baseline".
   - These are n = 1 query experiments tuned to one judge.
7. **Time inflation.** Time estimates were "re-calibrated": Light went from 3–8 min to 30–40 min, and Full from 25–60 min to 1.5–2.5 h (`:365`).

## 5. Issues and PRs

- Counts: 47 issues (9 open, 38 closed) and 132 PRs (21 open, 111 closed). The project depends heavily on outside contributors for fixes; fduple, synqing, earldodd, darlingm and maximilliangrand are frequent.
- **User complaints and failure modes:**
  - **#30 Loop at step 10:** the agent "can't seem to write the drafts". The maintainer says step 10 needs a runtime that spawns subagents and loops otherwise. It was closed as stale; "fail loudly instead of looping" was deferred to V9.
  - **#38 Deterministic orchestrator proposal:** an A/B showed silent skipping (see section 4). The maintainer's answer was written verdict artifacts, with the orchestrator staying discretionary.
  - **#83 Token cost:** one depth-investigator ran about 101 min (6,093,526 ms) and used 271K tokens. There were 10 concurrent subagents with 100–150 tool calls each, "several hours" of session, and duplicate completion notifications. The maintainer attributes this to the harness.
  - **#92 Budget inert:** the manifest stayed at zero, and the actual cost was about 8.6× a $25 ceiling. The fix in `[Unreleased]` adds count ceilings, but the entry skill does not pass them.
  - **#82 PDF failures:** the builtin provider had no PDF handling. One shipped report had sources marked "abstract only, paywalled".
  - **#150 Cite-check false positives:** the reproducer in section 3 (a numeric substring auto-pass; "`202` as supported by `2023`" per #162).
  - **#88, #102, #103:** contract incoherence; the dissertation tier was relabelled experimental.
  - **#31:** bibliographic metadata is not filterable. The maintainer: "`hpr search` exposes 23 filters and not one of them touches `doi`, `venue`, ...". This was later partly addressed by #119.
  - **#71, #76, #174:** CJK length and citation-density measurement bias. #174 is still open.
  - **#104, #126, #128, #133:** Windows-specific crashes and the `$HPR` failure.
- **Open PRs that matter:** #163 (a Stop gate for Claude Code), #154 (index the final report), #156 (cite-check resolution), #176 (the cite-check numeric fix), #177 (pin Crawl4AI below 0.9).
- **Test health:** #176 reports 1,547 cases passed before a crawl4ai TLS test failure that "also fail[s] on the unchanged base commit 9c16854", and `mypy` showing 420 errors across 59 files. #179 (2026-10-26) adapted the TLS tests.

## 6. The 2.0 roadmap: direction and reality

- **Thesis** (`docs/roadmap-2.0/README.md:7-12`): 1.x "won on process discipline". The gaps it names are ephemeral quality judgment and prose-hardcoded scale. The fix: make quality persistent and programmatic (ranking, claims, verification) and make scale a profile.
- **Phases:**
  - 0: cleanup.
  - 1: config and profiles.
  - 2: source ranking (quality_score, OpenAlex/S2 metadata, PageRank, claims table, embeddings).
  - 3: dissertation scale (run dirs, manifest and resume, chapters, budget governor).
  - 4: Chrome lane (escalation queue, human checkpoint; session handoff dropped).
  - 5: verification (cite-check, quote-integrity, numeric-consistency, retraction sweep, independence, telemetry, bench CI).
- **Status reality:**
  - The roadmap docs were added in the same commit that ticked Phases 1–5 as done: `5c8f90c`, 2026-07-19, PR #48, 102 files, +12,912/−642 lines. No later commit touches `docs/roadmap-2.0/`.
  - Phase 0 is open and has regressed. `core/hooks.py` is now 4,545 lines; the goal was under 600 (`phase-0-cleanup.md:91`), and it was 3,495 at audit (`:13`). 81 lines of `core/hooks.py` still match `Layer \d|7-phase|layercake`; the acceptance criterion is zero (`:92`).
  - Phase 2 acceptance "bench spot-run shows no RACE regression" (`phase-2-source-ranking.md:127`): no evidence is published.
  - Phase 3 acceptance "≥250 sources ... ≥25K-word report" (`phase-3-dissertation-scale.md:126`): never demonstrated (#103). The budget governor is inert (#92). The phase's own risk note says "300+ sources ≈ $200–500/run" (`:133`).
  - Phase 5 acceptance includes a nightly bench-smoke workflow (`phase-5-verification.md:86`). It was "NOT created" because `bench/` is gitignored (`CHANGELOG.md:243`). Also unmet: "3 planted defects" cite-check acceptance and numeric-consistency false positives below 10% on example-reports. No test or report shows either.
- **Direction since then:** the hosted product moved to the one-pass writer and keeps the OSS 12–16 chain only as a fallback. The OSS roadmap does not mention this. The OSS still runs "the older writing path".

## 7. The Codex bench (`codex_bench/`)

- **Purpose:** run DRB queries through HR on `codex exec` and write RACE-compatible JSONL (`codex_bench/README.md:3`).
- **What it measures is adherence, not quality.** It counts vault notes, manifest steps done and not done, tier, subagent spawns, sandbox rejections, `run verify`, escalations and token totals (`harness.py:392-508`, `:550-611`).
- **Grading:** none. `--evaluate` was removed (`README.md:44`); results must be exported to DRB's evaluator by hand.
- **Results:** none published. `codex_bench/*` is gitignored except the harness and README. `README.md:460` says the Codex port "has not been benchmarked yet".
- **Origin:** an April 2026 attempt "answered every query inline and wrote zero vault notes" under a read-only sandbox ("rejected: blocked by policy", `codex_bench/README.md:3, 21`).
- **Weaknesses:**
  - `PIPELINE_SKIPPED` fires only with zero notes and no manifest (`harness.py:623`). A run that skips most steps but writes a report classifies as OK; skips show only in `steps_not_done`.
  - "notes" counts every `.md` except the report (`:553`), including interim notes, source analyses and stubs. The README calls it "roughly the number of sources fetched" (`README.md:54`).
  - The sandbox-rejection regex runs over every raw JSONL line and includes "Access is denied" and "Operation not permitted" (`:110-114`, `:442-443`), so fetched 403 page text can inflate the count.
  - The default timeout is 3 h (`:49`), shorter than premier's 3–5 h.
  - The bench prompt injects benchmark packaging: inline `[N]` plus Sources, and a mandatory "## Opinionated Synthesis" with 5 subsections (`:59-106`). Users do not get this by default, and it may lift RACE insight scores.
- **Windows care:** the prompt goes in on stdin because "a multi-line argument does not survive codex.cmd's trip through cmd.exe" (`:322-324`). There is a suffixed run dir when Windows browser handles lock the old one (`:244-259`), and `taskkill /T /F` on timeout (`:379-385`).

## 8. Audit of the sample report

File: `example-reports/rl-exploration-trajectory-planning.md` (DRB Q67, about 10,400 words, 97 sources).

- **Header** (`:7`): 58.3 RACE, about 2 h, "80+ academic sources", the full 16-step chain.
- **Source titles:**
  - 21 of 97 titles are PDF page-header junk, for example [18] "Published as a conference paper at ICLR 2020", [38] "arXiv:2402.02025v2 [cs.LG] 8 May 2024", [87] "©2023 IEEE. Personal use of this material is permitted...".
  - 17 of 97 are truncated at the first line break, for example [8] "Curiosity in Hindsight:", [73] "Exploring Implicit Spaces for".
  - So 39% of the bibliography has broken titles. The header concedes it (`:9`).
- **Pipeline vocabulary leaks into reader prose:** "corpus" appears 16 times and "in-corpus" 4 times, plus "the corpus's CIC and CeSD notes survey these as substring references; we do not cite them directly" (`:62`).
- **Uncited parametric content is admitted:** MAX ("we do not cover MAX directly", `:44`), APT, SMM and DISCERN (`:62`), Swift and Kaufmann 2023 "named here as adjacent context" (`:195`).
- **A derived-number error got through:** "152.68% ... versus DreamerV3's 97.45% — a 55% relative improvement" (`:48`). The relative gain is 56.7%; 55.2 is the percentage-point difference. No gate checks derived arithmetic.
- **An overgeneralized thesis:** "persistently trailing on safety sub-metrics by 0.7-1.5 points" (`:23`) rests on one CaRL versus PDM-Closed comparison (`:191`), while CarPlanner 94.07 beats PDM-Closed (same section).
- **Strengths:** dense, mechanism-level content, explicit tensions with committed resolutions (`:140-158`), a regime-conditioned recommendation table (`:199-210`), and open problems ranked by leverage (`:247-265`).

## 9. Tests survey (`tests/`)

- 72 test files. A regex count of `def test_` gives about 1,197 functions (core 583, scholar 205, web 176, cli 172, graph 23, search 22, serve 14, mcp 2). About 1,547 cases run once parametrization expands (#176).
- CI (`.github/workflows/ci.yml`) runs ruff and pytest on Ubuntu with Python 3.11–3.14, plus one Windows 3.11 job. Publishing gates on the same checks.
- **What is tested:**
  - CLI and vault plumbing, sync, notes and links.
  - Profile rendering, with golden prompt fixtures byte-identical to the pre-template prompts (`tests/fixtures/golden_prompts/`, `test_prompt_golden.py`).
  - A test that every Profile field is read.
  - Verification gates: quote-integrity including the short-quote desync, CJK length and density, `run finish` blocking a hallucinated quote and an over-length report, retracted-citation blocking, independence clustering, cite-check pair extraction, triage and sampling rate (`test_verification.py`).
  - Security: the SSRF gate, XSS, TLS refusal, untrusted fences.
  - Scholar providers against recorded fixtures, OA recovery, escalations, the Codex install and stop gate.
- **What is not tested:**
  - Anything an LLM does. There is no end-to-end pipeline run and no check that agents follow the skills.
  - Report quality or benchmark regression; the bench is gitignored and there is no smoke tier.
  - The cite-check LLM tier, the planted-defects acceptance test, and numeric-consistency precision.
  - A Claude Code stop gate, since none exists.
  - Negative cases for numeric auto-pass (wrong entity, metric or unit). The existing test asserts the auto-pass (`test_verification.py:77-83`).
- **Takeaway:** strong unit coverage of the Python layer, zero coverage of the layer that produces the report. Section 4's "never worked" list (hook, claims ingest, ModelMap, `$HPR`) is exactly the integration gap these tests cannot see.

## 10. Cost and time data points

| Item | Figure | Source |
|---|---|---|
| OSS light tier | about 30–40 min | `README.md:171` |
| OSS full tier | about 1.5–2.5 h | `README.md:172` |
| OSS premier gear | about 3–5 h | `README.md:179` |
| OSS dissertation tier | about 4–8 h | `README.md:173` |
| Hosted Deep | $49 per run, 3–5 h, 150–200 sources | pricing page |
| Hosted Light | $9 per run, 30–40 min | pricing page |
| One user's full run | about 8.6× a $25 ceiling (about $215 API-equivalent) | #92 |
| One depth-investigator | 271K tokens, about 101 min | #83 |
| Roadmap's own dissertation estimate | $200–500 per run | `phase-3-dissertation-scale.md:133` |
| Comparator APIs on DRACO | $0.45–$5.5 per query | Valyu `scores.json` |
| Perplexity DR latency | 245 s average at 70.5% | DRACO paper Table 10 |

The paper also notes that "longer outputs do not necessarily achieve higher performance".

## 11. Windows notes

Fixed Windows defects listed in the CHANGELOG:

- charmap console crashes and MAX_PATH slug length (`CHANGELOG.md:509-510`)
- config.toml not written as UTF-8 (`:133`)
- a hook path with spaces (`:113`)
- `SO_REUSEADDR` port sharing on Winsock (`:43`)
- `[[-n "$kernel"]]` crashing sync (`:23`)
- `note mv` overwrite crash (`:24`)
- WinError 10048 test flakes (#104)

The maintainer develops on Windows (`ci.yml` comment), but CI has a single Windows job. The Codex harness needs cmd.exe and lock workarounds (section 7).

## 12. What this means for vafer-research

1. Do not design against "hyperresearch's 16-step chain is what wins". The vendor's own best (hosted Deep) has these parts:
   - chaptered research
   - an evidence map that reads every kept source in full
   - a section-brief plan
   - a primary-first "needs fetch" for gaps in the plan
   - a single one-pass writer
   - a figure-level claim check with one guarded revision

   The triple-draft, 4-critic and patcher stack is a fallback. There is no ablation, so treat this as the vendor's revealed preference, not proof.
2. Beating HR on DRACO is mostly about:
   - factual accuracy, which is about half the criteria
   - avoiding negative-criterion penalties, especially in medicine and law, where they reach −50 to −500
   - resolvable source URLs, since citation quality is 12% and ChatGPT and Gemini lost points just for missing links

   Length is not rewarded.
3. Any comparative claim needs:
   - the full 100 tasks, or at least 30 tasks
   - paired per-task differences with a CI or a sign test
   - at least 2 judge runs
   - an identical export path for every system
   - no post-hoc rewriting of only our own reports
4. Rules that are only instructions get dropped. Each conditional branch should leave a written verdict, including skips (`long_source_note_ids: []`), and only claim enforcement where code enforces it.
5. A figure check must match entity, metric, unit and period, not number substrings. Also check derived arithmetic.
6. Get bibliography titles from metadata (`citation_title`, Crossref, OpenAlex), not from the first PDF line. Ban pipeline vocabulary ("corpus", "notes", "in-corpus") from reader-facing prose.

## 13. Not verified or uncertain

- Whether Gemini-3-Pro is really "no longer available" (HR's stated reason for using GPT-5.2).
- How HR picked its 10 tasks, and whether the 3 rewritten reports were rewritten after a first grading.
- Whether the hosted Deep shares any code with the OSS beyond steps 1–11. The how-it-works page says the Deep run uses steps 1–11, but the OSS has no chaptered path in working order.
- Issue #92's "8.6×" figure is one user's estimate of host-session cost.
- I did not run the test suite, so the test counts come from a regex and from #176.
