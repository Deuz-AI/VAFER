# hyperresearch: steps 5-11 (depth, reconciliation, corpus critique, drafting)

Reader notes for the VAFER study of hyperresearch. Written 2026-10-27.

- Clone: `C:/Users/VECTOR/Documents/GitHub/hyperresearch`, HEAD `327498b`. Read-only; nothing installed or run.
- Paths below are relative to the clone. `skills/` means `src/hyperresearch/skills/`. `hooks.py` means `src/hyperresearch/core/hooks.py`, which holds every subagent prompt as a Python string.
- Files read in full: `skills/hyperresearch-5-depth-investigation.md`, `-6-cross-locus-reconcile.md`, `-7-source-tensions.md`, `-8-corpus-critic.md`, `-9-evidence-digest.md`, `-10-triple-draft.md`, `-11-synthesize.md`.
- Opened because those files point at them: the agent prompts in `hooks.py` (depth investigator 336-621, draft orchestrator 1901-2093, synthesizer 2103-2532, fetcher 2955-3217, corpus critic 3220-3341, loci analyst 130-329), `core/profiles.py` (every `<< p.* >>` number), `skills/hyperresearch-4-loci-analysis.md` (where loci and budgets are chosen), `core/levers.py` (the "run directives" shims), `core/runs.py` (ship gate), parts of `cli/lint.py`, `cli/note.py`, `core/claims.py`, `cli/claims_cmd.py`, `core/quality.py`, `core/codex.py`, `core/agent_docs.py`, `core/sync.py`, `skills/hyperresearch.md` (entry router), `skills/hyperresearch-1-5-chapter-partition.md`, `CHANGELOG.md`, `README.md`, `tests/test_core/test_hooks.py`, and the golden rendered prompts in `tests/fixtures/golden_prompts/`.

Numbers are the `full` profile unless stated (`core/profiles.py:253-307`). Cost figures marked "estimate" are mine, from stated assumptions, not measured.

---

## 1. Short version

Steps 5-11 run only on the `full` tier (light jumps from step 2 to a single draft in step 10, `profiles.py:313`). They turn a 55-80-source corpus into one final report:

1. **Step 5:** up to 6 Sonnet depth investigators, one per scored locus. Each writes one interim note that must end in a committed position with calibration.
2. **Step 6:** the orchestrator reconciles those positions into 3-5 cross-locus tensions (`comparisons.md`).
3. **Step 7:** the orchestrator reads 8-12 full sources and writes 3-7 expert disagreements with pre-committed resolutions (`source-tensions.json`).
4. **Step 8:** a period-pinned filing check, then one Sonnet corpus critic asking "what source would overturn this?", then 2-4 fetchers fill the gaps and `comparisons.md` gets confidence notes.
5. **Step 9:** the orchestrator filters fetcher-written claim files into an 80-120-claim digest of "verbatim" quotes grouped by atomic item.
6. **Step 10:** the orchestrator assigns three angles and a curated 20-50-note reading list to each of three Opus drafters. Each drafter reads every listed note in full and writes a complete draft.
7. **Step 11:** the orchestrator checks cross-draft factual conflicts against sources and writes a plan and outline. One fresh Opus synthesizer, limited to Read and Write, rewrites everything in two passes into `research/notes/final_report_<tag>.md`.

**Drafts are not chosen. They are dissolved:** a new writer re-authors the report from all three, guided by the orchestrator's plan.

The main structural fact for VAFER: **none of steps 5-11 is checked by the ship gate** (`core/runs.py:649-844`). Their whole value rests on prompt compliance by an orchestrator whose context, by the skill's own account, is past 200K tokens by step 11 (`skills/hyperresearch-11-synthesize.md:20`).

---

## 2. Map of the subsystem

| Step | Who does it (model) | Reads | Writes | What checks it |
|---|---|---|---|---|
| 5 Depth | K investigators in parallel, K = loci with `source_budget > 0`, max 6 (Sonnet, `profiles.py:55`, `278`). Each can spawn fetchers (Sonnet). | `loci.json`, corpus notes, `claims-*.json`, newly fetched notes | One vault note per locus: `type: interim`, tags `<tag>` + `locus-<name>` | Prompt invariant (step 5:92). Lint `locus-coverage` exists but is not in the ship gate (`lint.py:1005-1095`). |
| 6 Reconcile | Orchestrator (main session) | All interim notes in full | `comparisons.md`: 3-5 tensions (`profiles.py:280`) | Prompt only. Lint `workflow` checks existence (`lint.py:1603-1624`), not in gate. |
| 7 Tensions | Orchestrator | `comparisons.md`, 15-20 top sources' metadata, 8-12 full bodies, `contradiction-graph.json` | `temp/source-tensions.json`: 3-7 tensions | Prompt only. |
| 8 Corpus critic | Orchestrator pre-flight; 1 corpus critic (Sonnet); 2-4 fetchers (Sonnet) | `comparisons.md`, `loci.json`, `time_periods`, consensus claims, redundancy audit, source bodies | `corpus-critic-gaps.json`, `temp/corpus-critic-results.md`, edits to `comparisons.md`, new vault notes | Prompt only. |
| 9 Digest | Orchestrator | Every `claims-*.json`, consensus claims, contradiction graph | `temp/evidence-digest.md`: 80-120 claims, at least 30 (`profiles.py:286-287`) | Prompt only. |
| 10 Triple draft | Orchestrator curates; 3 draft orchestrators in parallel (Opus, `profiles.py:59`) | Decomposition, digest, comparisons, tensions, 20-50 full notes each | `temp/draft-{a,b,c}.md` | Prompt only. Re-spawn if a draft is missing or under 1,000 characters (step 10:203). |
| 11 Synthesize | Orchestrator plans; 1 synthesizer (Opus, tools `Read, Write`, `hooks.py:2116-2117`) | 3 drafts, plan, outline, conflicts, digest, comparisons, tensions, decomposition | `temp/synthesis-pass1.md`, `research/notes/final_report_<tag>.md` | Orchestrator `wc -w` against the length ceiling (step 11:226). The ship gate later checks length within ±20% (`runs.py:724-730`). |

Subagent sessions per full run in this subsystem:

- up to 6 investigators, plus an unknown number of investigator-spawned fetchers;
- 1 corpus critic and 2-4 fetchers;
- 3 drafters;
- 1 synthesizer, plus at most 1 compression re-spawn.

That is 13-15 named spawns plus nested fetchers.

---

## 3. Step by step

### Step 5: depth investigation

**How it chooses what to dig into.** Step 5 itself chooses nothing. It spawns one investigator per locus in `loci.json` with `source_budget > 0`, capped at `investigator_max` = 6 (`skills/hyperresearch-5-depth-investigation.md:32`). The choice happens in step 4:

- Two Sonnet loci analysts read each note's "title + summary + first ~400 chars" and deliberately not full bodies (`hooks.py:221-225`).
- They read the step 3 contradiction graph first and promote validated high-relevance fight clusters straight to `dialectical` loci (`hooks.py:193-200`, `213-219`).
- They use claim files to find opposing claims (`hooks.py:201-204`).
- Each proposes 1-8 loci, and every locus must cite at least one corpus note id (`hooks.py:300-314`).
- The orchestrator dedupes, clamps to 6, and scores each locus 0-10 on importance, uncertainty, disagreement and decision impact. The composite is the plain sum, max 40 (`skills/hyperresearch-4-loci-analysis.md:67-73`).
- Budgets are bracketed: 30-40 gets up to 15 new sources, 20-29 up to 10, 10-19 up to 5, under 10 gets 0-3 (step 4:75-81, `profiles.py:276-279`). The stated total is 40, but six top-bracket loci could claim 90. Nothing enforces the total.
- At least one dialectical locus is mandatory unless an analyst justifies its absence (step 4:114).

All four scores and the dedupe are LLM judgments. Cluster size from the contradiction graph is the only quasi-mechanical signal (step 4:70).

**Spawn contract.** Each investigator gets the verbatim query, a pipeline-position sentence, the locus (name, one_line, flavor, source_budget, rationale) and the research shim pasted verbatim (step 5:34-74; shim composition in `levers.py:235-258`). The prompt orders it to read full source text, not summaries (step 5:62-66).

**What the investigator does** (`hooks.py:336-621`):

1. Reads the locus's `corpus_evidence` notes in full via `note show` (`hooks.py:425-428`).
2. Reads matching `claims-<id>.json` files, targeting claims with opposing `stance` on the same `stance_target` (`hooks.py:430-435`).
3. Plans its budget, defaulting to 10 if none is given (`hooks.py:437-441`).
4. Delegates all fetching to `hyperresearch-fetcher` subagents through the Task tool, and is told "Do NOT call fetch directly" (`hooks.py:443-450`).
5. Prefers academic APIs (`hooks.py:452-455`) and quotes load-bearing passages (`hooks.py:457-459`).
6. Checks for an existing interim note before creating one, which guards against a duplicate failure mode seen in past runs (`hooks.py:463-479`).
7. Writes ONE interim note with fixed sections: what the corpus said, what the new sources say, evidence synthesis (one steelman subsection per side for dialectical loci), committed position, open questions, sources (`hooks.py:498-593`).

**The committed-position block** is the mechanism this step exists for (`hooks.py:529-553`). It holds:

- one argumentative paragraph;
- Position;
- Confidence, with numeric bands: high above 80%, medium 50-80%, low 30-50%;
- Boundary conditions;
- What would change this position;
- Evidence weight.

The block is reinforced by "prescriptive specificity": state thresholds, percentages and named mechanisms instead of directions (`hooks.py:555-582`). The worked examples use invented numbers and a placeholder citation ("per Zhang 2022 [N]"). An "unanswerable" locus must still commit, for example to "the burden of proof falls on..." (`hooks.py:611-615`).

**Orchestrator side.**

- If more than 50% of investigators fail, stop and ask the user (step 5:80). There is no user in `-p` mode.
- Then list and batch-read all interim notes and "hold the Committed Position sections in your context" (step 5:82-90).
- An interim note without `## Committed position` gets re-spawned (step 5:92).

**Codex.** Subagents cannot spawn subagents (`core/codex.py:132`, `core/agent_docs.py:224`). The translator replaces the delegation rule with "run `fetch`/`fetch-batch` yourself" (`codex.py:171-181`, `212-215`).

**Claude Code.** The design depends on a subagent spawning subagents. The only test is that the word "Task" appears in the rendered prompt (`tests/test_core/test_hooks.py:175-176`). I could not verify from the clone whether Claude Code exposes Task to subagents. My understanding of Anthropic's docs is that it does not. If so, investigators either do no new fetching or break the "do not call fetch directly" rule. **Unsure; worth an independent check.**

### Step 6: cross-locus reconciliation

The orchestrator (`skills/hyperresearch-6-cross-locus-reconcile.md`):

1. Re-reads every interim note (step 6:28), so the same notes now enter its context a second time after step 5.4.
2. Lays the committed positions side by side (6:36).
3. Asks five relationship questions of every pair: same facts but different meaning; different evidence and opposite conclusions; one assumes what another complicates; special case of a general claim; convergence via different mechanisms (6:38-43).
4. Keeps the 3-5 strongest and rejects orthogonal or restating pairs (6:45).

Each tension in `comparisons.md` records: the two loci with `[[interim-X]]` links and one-line positions, the dynamic in 2-3 sentences, one sentence on how the draft must engage it, and a calibration note (6:47-62). Calibration synthesis weights high-confidence over low-confidence positions and flags a shared "what would change my mind" condition as a genuine open question (6:62).

Contract: every tension must become a visible argumentative beat in the final report (6:64). A single-locus run still writes the file (6:19).

There is no subagent. The cost is orchestrator context. Quality depends entirely on the orchestrator's reading at this point in the run.

### Step 7: source tensions

The orchestrator (`skills/hyperresearch-7-source-tensions.md`):

- Re-reads `comparisons.md` as the first candidates (7:35).
- Surveys the 15-20 highest-quality sources and reads the full bodies of the 8-12 most likely to contain disagreements. Its stated reason: "Tensions hide in nuance that summaries flatten" (7:37).
- Scans for six disagreement types, such as institutional vs academic or industry vs independent (7:38-43).
- Treats any high-relevance contradiction cluster that did not become a locus as an "orphan tension" (7:45).
- Ranks candidates by decision relevance, evidence quality and reader value, dropping trivially resolved, definitional and off-query ones (7:47-52).
- **Pre-commits a resolution** for each: name, Side A's best case with evidence, Side B's, and the committed reading with its load-bearing reason (7:54-58).

Output: JSON with `side_a/side_b` (position, evidence, proponents as note ids), `resolution`, `origin` and `decision_relevance` (7:60-82).

Dangling contract: step 7 says its output feeds "step 10's mandatory Source Tensions section" and that "every tension named here becomes a subsection in the final report" (7:8, 7:17, 7:84). No later prompt asks for such a section. Grep over `src/` finds the phrase only in step 7. The drafter just reads the file (`hooks.py:1989`). The synthesizer uses it as a list of comparison dimensions and disagreements (`hooks.py:2206-2210`, `2283-2285`). When `required_section_headings` is set, extra H2s are forbidden (`hooks.py:2036-2038`, `2217-2220`).

### Step 8: pre-draft corpus critic

**Pre-flight, orchestrator only** (`skills/hyperresearch-8-corpus-critic.md:31-58`). For every `time_periods` entry in the decomposition:

- search the vault for the primary filing of that exact period;
- open it and check the actual reporting period ("A Q1 2025 10-Q does NOT satisfy Q3 2024");
- log any miss as a `critical` gap (`pp-N`) with ready search queries such as `site:sec.gov 10-Q "period ended September 30, 2024"`.

The stated rationale: numerical-precision misses are "the largest single category of avoidable factual-accuracy failures" (8:58). This pairs with the fetcher's period-pinned rules (`hooks.py:2993-3026`).

**Corpus critic, one Sonnet subagent** (`hooks.py:3220-3341`). For each committed position and tension it:

- names the evidence that would weaken it and the source type that would strengthen it (3268-3276);
- opens the 2-3 notes each position rests on and checks the text really supports it, because "Summaries and interim notes can drift" (3278-3288);
- asks whether consensus claims rest on independent or derivative sources (3290-3299);
- searches the vault for overturning evidence (3301-3305).

It outputs 3-8 gaps (`cc-N`) with type `overturning|strengthening|independent-verification`, search queries, source type and priority (3307-3327).

Conflicts inside this step:

- The schema allows `medium` priority (3317), but the next line allows only critical and high (3324).
- It must not "re-litigate the investigators' positions" (3338-3340), yet step 2 of its own procedure is exactly checking those positions against the source.
- A detected misreading has no gap type of its own and can only come out as a fetch request.

**Fetch wave.** The orchestrator merges the `pp-` and `cc-` gaps (8:88) and spawns 2-4 fetchers, one `gap_id` per spawn template (8:90-113). How 8 or more gaps map onto 4 fetchers is not specified.

Fetchers carry their standard "Phase 2 chase primary sources (MANDATORY)" of 3-8 extra fetches each (`hooks.py:3152-3158`, `3164-3165`, `3198-3201`). So a targeted gap fill also adds unrequested primaries.

**Assessment** (8:115-118):

- An overturning source found means: lower the position's confidence in `comparisons.md`, and do not re-run depth.
- **Not found means "the committed position gains confidence"**, logged as "adversarial search ... returned no substantive challenges."
- The interim notes themselves are never updated. Drafters read the interim notes in full (step 10:116) and also read `comparisons.md`, so they can see two different confidence levels.

### Step 9: evidence digest

The orchestrator (`skills/hyperresearch-9-evidence-digest.md`):

1. Reads every `claims-*.json` for non-deprecated tagged notes (9:33).
2. Keeps claims with `confidence: high` or `evidence_type` empirical/statistical, prefers ones with `numbers` and `quoted_support`, and caps at 80-120 (9:35).
3. Groups them by atomic item on holistic topic overlap, with an "Ungrouped" tail (9:37).
4. Adds consensus claims tagged `[consensus]` and the top 3-5 contested pairs with both quotes (9:39-41).

Output: one H3 per atomic item, with bullets of claim, blockquoted `quoted_support`, and `[source-note-id]` (9:43-61). It is described as the drafter's "PRIMARY EVIDENCE LAYER" (step 10:29), "higher fidelity than fetcher summaries" (9:16).

Where the claims come from: each fetcher writes 3-25 claims per source. `quoted_support` is labeled "THE MOST IMPORTANT FIELD ... the evidence digest surfaces these quotes directly to the drafter as primary evidence" (`hooks.py:3120-3139`).

- Ingest stores `quoted_support` as given, with no check against the note body (`core/claims.py:126-147`).
- The CLI can list claims only by note, tag and limit (`cli/claims_cmd.py:77-95`). It has no confidence or type filter, so step 9's mechanical filter is done by an LLM reading raw JSON.
- `claims targets`, a stance-target grouping that would help steps 7 and 9, exists (`claims_cmd.py:150-160`) but neither step references it.

### Step 10: triple draft

**10.0** reads `response_format` and `citation_style`. Targets: short 500-2,000 words, structured 2,000-5,000, argumentative 5,000-10,000 (golden render `tests/fixtures/golden_prompts/skills/hyperresearch-10-triple-draft.md:48-50`). The instruction is to aim for the middle (10:52).

**Light tier** (10:56-76) skips everything below. The orchestrator itself reads 8-15 notes and writes the final report directly.

**10.1 Angles** (10:80-94). Topics with tensions get A "strongest thesis", B "steelman contrarian: defend the MINORITY view", and C "synthesis reconciler: boundary conditions". Surveys and collections get A breadth, B depth on 3-4 items, and C practitioner recommendations. The angles are written to `temp/draft-angles.md`.

**10.2 Curated reading lists** (10:98-138). The orchestrator lists all notes ("You should have 50-100 candidates", a fixed number even on premier's 100-130-source gear, `profiles.py:336`) and runs one `search --ranked` per atomic item. `--ranked` folds a composite `quality_score` into relevance: tier, utility, citation authority and PageRank, with retractions floored (`core/quality.py:25-53`). Selection rules:

- Every list includes ALL interim notes and the relevant source-analysis notes (10:115-116).
- A favors dominant-direction sources and digest high-confidence citations.
- B favors minority and critique sources, the contested side's proponents from `source-tensions.json`, and even the lower-quality side of contradiction pairs (10:118).
- C favors boundary-condition, comparative and case-study sources (10:119).
- Overlap is expected. "Differentiation comes from the angle-specific extras (the 5-15 sources unique to each draft's list)" (10:121).
- Size: 20-50 notes, leaning 35-50 for argumentative (10:123).

**10.3 Spawn 3 drafters in one message** (10:142-181). Each gets its draft id, angle, ID list, artifact paths, format, citation style, modality and the drafting shim. The drafter (`hooks.py:1901-2093`, tools Bash, Read, Write):

- reads the artifacts, with no vault survey (1980-1993);
- batch-reads every listed note in chunks of 5-8 with `note show ... -j`, re-reading one at a time when output is truncated (2002-2008);
- confirms by self-count that every ID appeared in some `note show` call (2023-2028);
- does no fetching and spawns no subagents (2017-2021);
- writes a complete draft that honors the required headings exactly, covers every atomic item, uses numbered hierarchical headings, puts the executive summary first, commits a reading at the end of every section, stays above the citation-density floor of 9 per 1,000 words, includes one interpretive beat per 2-3 factual claims, includes a forward-looking paragraph and defines terms (2034-2083).

The orchestrator is told to keep making tool calls while drafters run ("never emit bare text") and to write synthesis thoughts into `orchestrator-notes.md`. The drafters "will take 5-15 minutes each" (10:183).

**10.4 Validation** (10:187-205): all three files exist and none is "trivially short" (under 1,000 characters for argumentative, 500 for structured). Otherwise re-spawn that drafter. There is no content or reading check beyond the drafter's own report-back.

### Step 11: synthesize

**Why a separate writer** (11:20): "the orchestrator has been running for 30+ minutes and 200K+ tokens of context ... full of stale subagent dispatch logic." The synthesizer is a fresh session limited to Read and Write.

**Orchestrator prep:**

- **11.1** Read all three drafts in full and the drafters' report-backs (11:37-45).
- **11.2** For each substantive contradiction *between drafts*, read both cited sources with `note show` and write a verdict to `synthesis-conflicts.md` (11:49-65). This is the only point in steps 5-11 where the final-report path is checked against source text, and only where two drafts disagree.
- **11.3** `synthesis-plan.md` (11:69-102): core thesis; the 3-7 strongest beats and which draft each came from; section structure; per-section commitments (evidence from which draft, which committed position, which tension); "where drafts disagreed: commit to <side> because..."; length targets for pass 1 and pass 2.
- **11.4** `synthesis-outline.md`, 50-200 words, 1-2 sentences per H2 (11:106-131).
- **11.5** Gate: the files exist and are non-trivial. "The synthesizer cannot do strategic planning — it can only execute the plan" (11:135-143).

**The synthesizer** (`hooks.py:2103-2532`):

- **Invariant: "SYNTHESIZE, NEVER GRAFT".** Do not paste paragraphs. Write in one voice; "The reader cannot tell that 3 drafts existed" (2140-2153).
- **Phase 1** reads query, decomposition, plan, outline, all three drafts (noting the strongest beat, the most specific evidence, the disagreements and the overlaps for each section), then comparisons, tensions and digest (2183-2210).
- **Pass 1** (2212-2324) runs 15-20% over target. It:
  - honors headings exactly and uses numbered hierarchy, because flat headings "score lower on instruction-following" (2217-2222);
  - aims for 80-150 total citations for argumentative (2230-2241);
  - covers every atomic item from any draft;
  - engages tensions and commits (with register-dependent exceptions);
  - includes forward-looking analysis and inline definitions;
  - uses tables when 3+ entities are compared on 2+ dimensions;
  - opens each major section with a 3-5-sentence plain-language "pedagogy primer" (2267-2277);
  - puts coverage and developed mechanisms ahead of elegance (2278-2300).
- **Length rule** (2311-2322): the target's top is a hard ceiling. "Selectivity ... is choosing which SOURCES to cite for a point, not which POINTS to make."
- **Pass 2** (2326-2504):
  - redundancy first: each idea and each piece of evidence once (2331-2343);
  - voice-break repair (2345-2358);
  - weak-section rewrite;
  - length cuts that remove prose, never points (2366-2387);
  - calm citation placement: one point per sentence, grouped `[7, 12]`, never stacked `][`, at most 3 per group, numbers and quotes keep their own anchor (2397-2415);
  - register discipline: no meta-discourse, hedge only unverified specifics, at most one dramatic "kicker" per section, varied rhythm (2417-2454);
  - hygiene and a six-item structural checklist (2456-2504).
- **No further passes**, no self re-spawn (2517-2519).

**Orchestrator validation** (11:210-237):

- A mechanical word count against the ceiling, with exactly one allowed compression re-spawn whose input is the synthesizer's own final report (11:226, 11:235).
- Required H2s present; citation style matched; `grep -c ']['` returns 0; primers spot-checked in 3 sections; no frontmatter or pipeline vocabulary.
- If pass 2 is longer than pass 1, something went wrong (11:233).
- Other failures get a hand-made Edit, not a re-spawn (11:237).
- After this step the report is write-once and changes only through patcher and polish hunks (11:241-243).

---

## 4. How evidence flows from notes into the report

```
web page --fetch--> vault note (full body, SQLite + .md) --fetcher--> summary + claims-<id>.json (quoted_support, numbers)
                                   |                                             |
          step 5 investigator reads corpus notes + claims, fetches more          |
                                   v                                             |
                     interim note (trusted, unfenced; committed position,        |
                     quotes, [[note-id]] links)                                  |
                                   |                                             |
          step 6 orchestrator ---> comparisons.md (positions, tensions)          |
          step 7 orchestrator ---> source-tensions.json (sides, proponent ids)   |
          step 8 critic+fetchers -> new notes (+claims), comparisons.md notes    |
                                   |                                 step 9 ---> evidence-digest.md (80-120 quotes + ids)
                                   v                                             |
          step 10: 3 drafters read 20-50 FULL note bodies each (incl. all interim notes)
                   + digest + comparisons + tensions --> draft-a/b/c.md ([[id]] or [N] citations)
                                   |
          step 11: orchestrator reads drafts, re-checks only cross-draft contradictions against sources
                   synthesizer reads drafts + digest + plan (NOT instructed to read source bodies)
                                   v
                        final_report_<tag>.md
```

Consequences:

- Most claims reach the final report two hops from the source text (drafter, then synthesizer). Claims routed through interim notes are three hops (investigator, drafter, synthesizer). Only digest quotes are carried as text, and they were never checked at extraction (`core/claims.py:126-147`).
- An error that all three drafts share passes step 11.2 unseen, for example one taken from a shared interim note or digest claim. Those come from the same inputs (step 10:115-121).
- The downstream backstops are outside this subsystem: cite-check (step 14.5) and the ship gate's `quote-integrity`. The latter accepts a quoted span if it appears in **any** vault note body (`cli/lint.py:110-148`, query at about 128-131). Interim notes and source-analysis notes are vault notes with frontmatter, so they are indexed (`core/sync.py:96-99`). A "quote" an investigator mangled in its interim note, then copied forward, therefore passes. The final report itself is not indexed, because it must have no frontmatter, so it cannot match itself.
- Untrusted-content fencing wraps web note bodies (`cli/note.py:221-224`, `core/untrusted.py:42-62`). Interim and source-analysis notes arrive unfenced as "trusted" (`hooks.py:371-373`). Fetched text an investigator paraphrases into an interim note therefore loses its fence.

---

## 5. Cost model

Assumptions for the estimates: full gear, argumentative format, 6 loci, about 70 corpus notes averaging about 3,000 words (about 4K tokens). Real note lengths vary widely, and I did not measure them.

| Step | Sessions | Peak context per session (estimate) | Notes |
|---|---|---|---|
| 5 | Up to 6 Sonnet investigators + nested fetchers | 50-120K | Nominal 40 new sources. Fetchers' mandatory chase (3-8 each) can push the real count above budget. |
| 6 | Orchestrator | +20-40K to main context | The interim notes are read for the second time (step 5:82-90, step 6:28). |
| 7 | Orchestrator | +40-70K | 8-12 full bodies plus a metadata list. |
| 8 | 1 Sonnet critic + 2-4 Sonnet fetchers | Critic 40-80K | Pre-flight searches are cheap. |
| 9 | Orchestrator | +75-135K if claims are read raw (500-900 claims at about 150 tokens each) | The skill says "read all claims files". How the orchestrator does it (many Reads or an ad-hoc script) is unspecified. |
| 10 | 3 Opus drafters | 150-250K each, from 35-50 full notes, digest and artifacts | Can approach or exceed a 200K window. Output 7-13K tokens each. "5-15 minutes each" (10:183). |
| 11 | Orchestrator + 1 Opus synthesizer | Synthesizer 45-75K input; output 15-30K tokens (pass 1 + pass 2) | "5-15 minutes" (11:206). Plus a possible compression re-spawn. |

- Cumulative billed input is several times the peak, because each turn re-sends context (mostly cache reads).
- The whole full run is quoted at about 1.5-2.5 hours (`profiles.py:306`). I could not isolate how much of that steps 5-11 take.
- The most expensive single items are the three Opus drafters (full-body reading plus full-length writing) and the synthesizer's output.
- The main-context load from steps 5.4, 6, 7, 9, 10.2 and 11.1 is what pushes the orchestrator past 200K. That load is what the per-step skill loading is designed to survive (`skills/hyperresearch.md:57`).

---

## 6. Enforced by code vs only by prompt

| Rule | Enforced? | Evidence |
|---|---|---|
| One interim note per locus, ending in a committed position | Prompt. Lint `locus-coverage` checks per-locus existence only, and it is not part of the ship gate. | step 5:92; `lint.py:1005-1095`; `runs.py:783-806` folds in only quote-integrity and retracted-citations |
| `comparisons.md` exists | Lint `workflow`, not in the gate. Its interim-note count is vault-wide, not per run (`lint.py:1568-1571`). | `lint.py:1603-1624` |
| `source-tensions.json`, digest, angles, source lists, three drafts, plan, outline, pass 1 | **Not checked anywhere** | Grep of `lint.py` and `runs.py` |
| Source budget per locus, total of 40 | Prompt only. Optional run-wide `max_sources`/`max_notes` ceilings exist. | step 4:75-81; `runs.py:381-397` |
| Drafter read every listed note | The drafter's own count | `hooks.py:2023-2028` |
| Synthesizer cannot run Bash or spawn agents | **Yes on Claude Code** (tool allowlist); instruction-only on Codex | `hooks.py:2117`; `codex.py:137-170` |
| Final length within ±20% of the target range | **Yes** (ship gate), plus the orchestrator's `wc -w` at 11.7 | `runs.py:724-730`; step 11:226 |
| Citation density at least 9 per 1,000 words | **Yes** (ship gate) | `runs.py:747-770` |
| Quoted spans of 5+ words exist in the vault | **Yes**, but against any vault note | `lint.py:110-148` |
| Required H2s present | **Yes**, as a substring match | `runs.py:732-737` |

---

## 7. Weaknesses

Severity reflects impact on report quality, cost or reliability.

1. **High: the core differentiators are prompt-only.** The ship gate verifies the final report, the critic, patch and polish logs, and cite-check (`runs.py:808-842`). It never verifies that depth, reconciliation, tensions, digest, three drafts or synthesis happened. The project documents this failure: in V7 the orchestrator "silently dropped Layer 3.7 (corpus critic), rewrote its todo to replace the triple-draft ensemble with a single draft ... This happened in 100% of runs where the orchestrator didn't re-read the skill file" (`skills/hyperresearch.md:309`; also step 10:16). V8's fix is reloading each step's prompt, not checking. A degraded run can still finish as `done`.
2. **High: the final writer works second-hand, and the fidelity backstop is loose.** The synthesizer works from drafts and the digest (`hooks.py:2183-2210`). Only cross-draft contradictions are checked against sources (step 11:53-63). `quote-integrity` accepts a quote found in any vault note, including LLM-written interim and source-analysis notes (`lint.py:110-148`). Digest quotes are never verified at ingest (`claims.py:126-147`), yet they are presented as "verbatim ... primary evidence" (step 9:16, step 10:29).
3. **High (cost), medium (quality): unbounded full-body reading.** Each drafter must read all 20-50 notes in full (`hooks.py:1968-1971`, `2002-2028`). `note show` has no paging or size cap (`cli/note.py:219-226`). Claude Code middle-truncates long Bash output: the default is about 30,000 characters, configurable through `BASH_MAX_OUTPUT_LENGTH` (host behavior, from memory; verify). A 5-8-note batch, or a single long note, can come back truncated. The prompt's remedy, re-reading one note at a time (2006-2008), does not fix a single over-long note. Its "verification gate" counts IDs passed to `note show`, not content seen. Peak context for 35-50 notes plausibly approaches a 200K window (estimate).
4. **Medium: schema drift between the locus producer, merger and consumer.**
   - The analyst emits `convergent|dialectical` with `corpus_evidence`, `opposing_positions` and `suggested_*` (`hooks.py:235-242`, `264-289`).
   - The merged `loci.json` schema lists `dialectical|synthesis|technical` and drops those fields (step 4:83-102).
   - Step 5 passes only name, one_line, flavor, budget and rationale (step 5:48-53).
   - The investigator expects the full object (`hooks.py:396-398`), starts from `corpus_evidence` (425-428), and has postures only for convergent and dialectical (405-421).
   - Investigators may start without their seed notes or the two sides. The "synthesis" and "technical" flavors get no posture.
5. **Medium (unsure): nested spawning on Claude Code.** The investigator must spawn fetchers through Task (`hooks.py:348`, `443-450`). Only a string-presence test covers it (`test_hooks.py:175-176`). If Task is unavailable inside subagents, step 5 adds little new evidence or violates its own rule. The project's Codex port assumes no nesting (`codex.py:132`, `171-181`).
6. **Medium: budgets are not real limits, and fetchers multiply them.** The brackets allow 90 against a stated 40 (step 4:75-81). Every fetcher spawned for depth or gap-fill runs a mandatory 3-8-source chase (`hooks.py:3152-3158`, `3198-3201`). The result is cost blowup and vault bloat, and drafters' lists then compete for space.
7. **Medium: absence of evidence counted as confirmation.** "Overturning source NOT found: the committed position gains confidence" (step 8:117), after 2-4 fetchers ran a few queries. This pushes toward over-committed reports. The critic's misreading findings have no gap type of their own (`hooks.py:3313`), and it is told not to re-litigate (3338-3340). Weakened confidence is written to `comparisons.md` but not to the interim notes that every drafter reads in full (step 8:116, step 10:116).
8. **Medium: a dangling "mandatory Source Tensions section".** Promised at step 7:8, 7:17 and 7:84; never required downstream; and when headings are prescribed, it is forbidden by the no-extra-H2 rule (`hooks.py:2036-2038`). The step's self-declared "single highest-leverage move" has no consumer contract.
9. **Medium: the synthesizer's citation instructions contradict each other.** Pass 1 always uses `[N]` with a Sources list (`hooks.py:2230-2241`). The default `wikilink` style wants `[[note-id]]` and no Sources section (step 11:191-196; `hooks.py:2393`). Pass 2 must map numbers back to note IDs, with a real risk of wrong or lost citations in the default mode.
10. **Medium: strategic choices are made in the most degraded context.** Angles, per-draft lists, conflict verdicts, the core thesis and per-section commitments are all written by the orchestrator (10.1-10.2, 11.2-11.4) after "200K+ tokens" (11:20). "The synthesizer ... can only execute the plan" (11:143).
11. **Medium: step 9 is a mechanical filter done by an LLM.** It reads hundreds of claims (9:33). The CLI cannot filter by confidence or type (`claims_cmd.py:77-95`). Tension finding in step 7 also ignores `claims targets` (`claims_cmd.py:150-160`). The filter's bias toward numbers and empirical evidence (9:35) can starve qualitative, legal or historical questions.
12. **Medium (cost), unclear (quality): the triple draft's value is unmeasured.**
    - Release 0.7.0 replaced "the three-parallel-drafts-plus-merger ensemble" with one draft (`CHANGELOG.md:390`). V8 restored a triple draft. The justification in the repo is anecdotal (`hyperresearch.md:309`).
    - The only quantitative claim is the whole pipeline's 10-task DRACO score: 77.7 against Claude Research's 73.0 (`README.md:38`).
    - All three drafts share every interim note, the source analyses, the digest and the tensions (step 10:115-121), which limits real diversity.
    - Validation is existence plus more than 1,000 characters against a 5,000-10,000-word target (10:203).
13. **Low-medium: the synthesizer is asked to count without a counter.** It is told to "Count your words" and to count citations (`hooks.py:2313-2314`, `2493-2498`) while limited to Read and Write. The real check comes afterwards (step 11:226) and can trigger a full Opus compression re-spawn (11:235).
14. **Low-medium: invented precision.** The investigator is pushed toward exact thresholds, with fabricated example numbers and a placeholder citation (`hooks.py:555-582`). The fallback "say so explicitly" exists (579-582), but nothing checks numbers in interim notes. `numeric-consistency` only warns (`lint.py`, `_check_numeric_consistency`).
15. **Medium on Windows: shell problems.**
    - `{hpr_path}` is substituted unquoted (`hooks.py:69`; `agent_docs.py:311-312`; `install.py:234`). Any install path containing a space, such as a Windows username "First Last", breaks every CLI command in this subsystem. The project's own stop-hook code knows paths can contain spaces (`codex.py:292-298`).
    - The bash-only `PYTHONIOENCODING=utf-8 cmd` prefix (step 8:39; `hooks.py:2004`, `3282`, `3304`) and `wc`/`grep` (step 11:226-229) fail under PowerShell, which Codex uses on Windows. JSON output already writes UTF-8 bytes (`cli/_output.py:26-37`), so the prefix is unnecessary there anyway.
    - `mkdir -p research/temp` targets the wrong folder (`hooks.py:485` vs `493`). This is harmless with the Write tool.
16. **Low: the dissertation tier cannot run step 11 as written.** Chapter mode sends 25K-80K words through step 11 (`1-5-chapter-partition.md:78-80`; `profiles.py:397-400`). Step 11 gates on `draft-{a,b,c}.md` (11:141), and a Read+Write synthesizer must emit the whole document in one Write. That is very likely beyond one response's output budget. Step 6 has no cross-chapter procedure, although chapter mode re-runs it globally.
17. **Low: stale or contradictory prompt text.**
    - The drafter still says the main orchestrator writes the final draft (`hooks.py:1950-1952`).
    - The interim template says "3-10 new sources" while budgets go up to 15 (`hooks.py:513`).
    - Step 10.2 fixes the candidate count at "50-100" (10:106).
    - `comparisons.md` uses `[[interim-X]]` links (6:54) that the synthesizer must strip (`hooks.py:2463`).
    - "Ask the user" at step 5:80 has no user in `-p` mode.
18. **Low, unclear: waiting behavior.** The "never emit bare text" rule with "one vault count check per minute" (10:183, 11:206) only makes sense if spawns run in the background. In the foreground it does nothing. In the background it burns orchestrator turns, and one slip ends a `-p` run (`hyperresearch.md:180`).
19. **Design note, not a bug: judge-tuned rules.** Many rules cite benchmark scoring: "insight score suffers" (6:64); flat headings "score lower" (`hooks.py:2221-2222`); an 80-150 citation target (2232); "+2.5 RACE from register alone" (`CHANGELOG.md:194`); primers adopted after a judge comparison (`CHANGELOG.md:211`). They help on a judged benchmark. For an ordinary user they can produce long, citation-dense reports of 5,000-10,000 words.

---

## 8. What plausibly drives quality

- **Committed positions with calibration fields.** These turn each investigator's output into claims with confidence, boundary conditions and falsifiers. That gives steps 6, 8 and 11 something to reconcile and to hedge honestly on (`hooks.py:529-553`). The synthesizer is told to carry interim mechanism depth into the report (`hooks.py:2296-2297`).
- **The fresh-context two-pass synthesizer** with concrete, specific rules: one voice, a redundancy pass, primers, inline definitions, tables, calm citations, "prune citations, never points". This is where prose quality is made. The rules are backed by documented regressions and fixes (`CHANGELOG.md:185`, `207`, `211`, `213`).
- **Plan, outline and source-checked conflict verdicts before writing** (step 11:49-131). These decide the thesis and where to commit.
- **Pre-draft adversarial work:** the period-pinned filing check (step 8:31-58) and the corpus critic's re-reading of sources behind positions (`hooks.py:3278-3288`). Corrections made before drafting cost nothing; after drafting they need patches (step 8:16).
- **Unclear: three angled drafts.** They plausibly surface counterarguments that a single draft would underplay (the steelman-contrarian angle), but there is no measurement, and the cost is about three full Opus drafts.

---

## 9. Ideas for VAFER

Adopt:

- A closing calibration block in each researcher reply (position, confidence, boundary conditions, what would change it, evidence weight). It is cheap and feeds "Where sources disagree".
- Explicit resolutions for disagreements: for each conflict, state which side has the better evidence and why, instead of listing both sides (step 7:54-58).
- A period-pinned primary-record check before drafting: a figure for "Q3 2024" must come from the Q3 2024 record (step 8:31-58).
- A conflict check that opens both cited pages when researchers disagree and writes a one-line verdict. This maps onto VAFER's CONFLICT rows (step 11:49-63).
- The writing rules "choose which sources to cite per point, never which points to make" and "coverage and mechanism depth before elegance" (`hooks.py:2278-2322`).
- A redundancy pass after VAFER's section-by-section writing, so each fact appears once (`hooks.py:2331-2343`).
- Write-once after the final write, with one permitted compression pass triggered by a mechanical word count (step 11:226-243).

Adapt:

- Score checklist items (importance, uncertainty, decision impact) to decide researcher count and depth, and record the allocation in plan.md so it can be checked.
- For heavy Deep runs, give the final write to one fresh writer subagent with a compact brief, and let it open notes, not only drafts.
- For contested questions, replace three full drafts with one short "strongest minority case" outline that the single writer must answer.
- Run a pre-draft "what would overturn this?" search on each headline conclusion, and record a miss as "searched, not found (queries)", never as added confidence.

Avoid:

- Three full drafts plus a merger by default: an unmeasured cost of about three extra full Opus drafts per run.
- Telling any agent to read 20-50 full documents. Keep VAFER's "load only that section's notes" and its notes with quotes of at most 30 words.
- Checking quotes against "anywhere in the corpus". Check each quote against the page it is cited to; VAFER's re-open-headline-sources step already points this way.
- Prompt-only mandatory steps. If VAFER claims a step always runs, its artifact should be checkable.
- Dangling promises between steps. Every section VAFER promises must be named in the writer's instructions.
- One artifact described by several schemas. Define each artifact once.
- Rubric-chasing mandates (numbered headings, citation-count targets, very long reports) unless VAFER explicitly decides to optimize for a judge.
- On Windows: unquoted executable paths and bash-only environment prefixes in instructions that may run under PowerShell.

---

## 10. Key claims for an independent check

1. Steps 5-11 produce no artifact the ship gate checks: `core/runs.py:649-844`, especially 783-806 and 808-842. Grep `draft-a` in `cli/lint.py` and `core/runs.py` and expect zero hits.
2. The three drafts are rewritten by a fresh Opus synthesizer limited to Read and Write, working from drafts and the digest. Only cross-draft contradictions are checked against sources: step 11:18-20, 49-65, 143; `hooks.py:2116-2117`, 2140-2153, 2183-2210.
3. What depth investigates is decided by LLM judgment in step 4. Loci come from summaries and contradiction clusters and are scored on four 0-10 dimensions with unenforced budget brackets. Seed fields are dropped between producer and consumer: step 4:67-102; `hooks.py:221-225`, 264-289, 396-398, 425-428; step 5:48-53.
4. Drafter reading is unbounded: step 10:100-123; `hooks.py:1968-1971`, 2002-2028; `cli/note.py:219-226`; `profiles.py:290`.
5. The triple draft's contribution is unmeasured in the repo: `CHANGELOG.md:390`; `skills/hyperresearch.md:309`; step 10:16; `README.md:38`.
6. The quote check accepts a quoted span found in any vault note, and interim notes are vault notes: `cli/lint.py:110-148`; `core/sync.py:96-99`.

---

## 11. Things I could not settle from the clone

- Whether Claude Code lets a subagent use Task, which decides whether step 5 fetches anything. See weakness 5.
- The exact Bash output cap and truncation behavior in the Claude Code version the author used, and the context window of the Opus drafters (200K vs 1M). The test suite assumes Sonnet's 1M window for the source analyst (`test_hooks.py:183-186`).
- Real note lengths and claim counts, so all token figures above are estimates.
- Whether steps 10 and 11 spawn in the foreground or background in practice.
