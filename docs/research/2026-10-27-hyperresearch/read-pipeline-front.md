# hyperresearch read: entry router, tiers and steps 1-4

Date: 2026-10-27. Clone: `C:/Users/VECTOR/Documents/GitHub/hyperresearch` at commit `327498b` (read-only; nothing installed or run).
All paths below are relative to the clone unless they start with `VAFER/`.

Files read in full: `src/hyperresearch/skills/hyperresearch.md` (router, 339 lines), `skills/deep-research/SKILL.md` (117), `src/hyperresearch/skills/hyperresearch-1-decompose.md` (211), `...-1-5-chapter-partition.md` (94), `...-2-width-sweep.md` (350), `...-3-contradiction-graph.md` (73), `...-4-loci-analysis.md` (134), `src/hyperresearch/core/profiles.py` (497), `core/render.py` (113), `core/levers.py` (330).

Opened because those files reference them: the fetcher, loci-analyst, source-analyst and browser-fetcher agent prompts in `core/hooks.py`, the PreToolUse hook and its installer (`core/hooks.py`), `core/runs.py` (manifest, resume, ship gate), `core/codex.py` (Codex stop gate, tool-lock translation), `cli/fetch.py`, `cli/sources.py`, `cli/note.py`, `cli/levers_cmd.py`, `cli/vault_tag.py`, `cli/profile_cmd.py`, `cli/install.py`, `cli/claims_cmd.py`, `core/claims.py`, `core/independence.py`, `core/quality.py`, `core/graphrank.py`, `core/sync.py` (link extraction), `core/config.py` (ranking weights), `core/agent_docs.py` (CLAUDE.md block), golden fixtures under `tests/fixtures/golden_prompts/`, `README.md`, `CHANGELOG.md`, `docs/roadmap-2.0/phase-3-dissertation-scale.md`, `example-reports/rl-exploration-trajectory-planning.md`.

---

## 1. Summary

hyperresearch's front half is a long prompt pipeline sitting on a small Python CLI. A bootstrap skill installs rendered skills and agents. The router skill then loads one step skill at a time so each procedure arrives fresh after context compaction. It keeps its position in TodoWrite and a run manifest, and routes by a tier that step 1 chooses (light: steps 1, 2, 10, 15, 16; full: all 16 plus 14.5; dissertation: experimental chapters). The numbers (source targets, fan-out, budgets) are baked into the prompt text at install time from a "gear" (full: 55-80 sources; premier: 100-130).

Step 1 turns the query into atomic items, literal H2 headings, period-pinned filings, a tier, a response format, a citation style and posture "levers", then checks a coverage matrix against the query. Step 2 plans 40-100 searches across four lenses (breadth, canonical, adversarial, period filings). The lead agent runs those searches itself, then hands URL batches to 10-12 Sonnet fetchers. Each fetcher reads full pages, writes summaries and claims with verbatim quotes, and chases 3-8 cited primary sources. Gap waves, a redundancy audit and ranking commands follow. Step 3 pairs contradicting claims, and step 4 runs 2-3 loci analysts and assigns depth budgets.

Almost none of this is enforced in code. The ship gate checks only step-1-derived headings and length, citation density, quotes, retractions and late-step artifacts.

---

## 2. Entry router

### 2.1 Two entry points

- `skills/deep-research/SKILL.md` is a marketplace bootstrap, not the pipeline (`skills/deep-research/SKILL.md:10-14`). It runs `hyperresearch --version`, stops if the CLI is missing (`:16-29`), picks a Claude Code or Codex branch (`:31-41`), runs `hyperresearch install . --json` (or `--target codex`) and hands off with `Skill(skill: "hyperresearch", args: "<request verbatim>")` (`:43-64`). The install writes a CLAUDE.md block, skills, agents and a PreToolUse hook into the user's project (`:52-55`). If Claude Code has not loaded the new skill yet, the user has to restart the session (`:66-73`). Codex reads `.agents/skills/hyperresearch/SKILL.md` directly with `cat` (`:99-108`).
- `src/hyperresearch/skills/hyperresearch.md` is the installed router. It is a Jinja template branched on `platform` (claude/codex) and rendered with profile values (`hyperresearch.md:4-21`, `render.py:1-26`).

### 2.2 What the router tells the orchestrator

- Its role: "You do NOT do the work of any step yourself. The step skills do. You just sequence them." (`hyperresearch.md:37`). On Codex: "THE JOB IS THE PIPELINE, NOT AN ANSWER ... Spawning subagents is mandatory" (`:33`).
- Chain mechanics: one `Skill(skill: "hyperresearch-N-...")` per step (Codex: `cat .hyperresearch/codex/steps/<step>.md`). The stated reason is compaction: V7 was one 1,200-line skill whose procedure got evicted, so the orchestrator dropped the triple draft (`:49-57`, `:307-313`). The evidence offered is "Q57 (55.9, full pipeline) and Q9 (52.6, single-draft fallback)" (`:313`, `:327`). Those are two different benchmark questions, so this is not a controlled comparison.
- Tier routing table (`:84-98`): light = 1 → 2 → 10 → 15 → 16; full = all steps including 14.5; dissertation = 1 → 1.5 → [2…10 per chapter] → 6g/11 → 12…16, which is "experimental. Its length, read-budget and citation targets are configured but nothing reads them yet (#103)" (`:94`). "RESPECT THE TIER GATE" (`:96`, `:186`).
- Bootstrap (`:102-172`):
  - auto-init the vault and step skills (`:106-110`);
  - `archive-run` (`:112`);
  - resolve the canonical query, where `research/prompt.txt` is "GOSPEL" (`:114-118`);
  - mint a tag with `vault-tag <slug>`, which appends 6 random hex characters (`:120`, `cli/vault_tag.py:121-132`);
  - `run init <tag> --profile <full|light|premier|dissertation> [--budget <usd>]` (`:122-127`);
  - write `query.md` (`:129-139`);
  - classify modality (collect/synthesize/compare/forecast) (`:141-145`);
  - write a private `scaffold.md` (`:147-152`);
  - seed 16 TodoWrite items (`:163-168`) and invoke step 1.
- Four canonical rules (`:176-186`):
  1. Never emit bare text while subagents run, because in `-p` mode that ends the process (`:180`).
  2. Patch, never regenerate.
  3. "ARGUE, DON'T JUST REPORT".
  4. Respect the tier gate.
- Spawn contract (`:204-214`): every subagent prompt carries the query verbatim and block-quoted, a one-sentence pipeline-position statement, its specific inputs, and the run's shim file pasted verbatim. The cite-checker gets no shim.
- Recovery (`:218-245`): `run resume <tag>` returns the next step from the manifest. The fallback is a table of canonical artifacts per step (`:225-241`).
- Final gate (`:249-283`): `sources retractions` then `run finish`, which is "the ship gate", with at most 3 fix rounds before the run stays `blocked`. The rules for fixing include "length-in-range over the ceiling → spawn the synthesizer for ONE compression pass" (`:276`).
- Invariants (`:287-303`), including "Fetchers MUST chase 3-8 primary sources via citation chains" (`:300`).

### 2.3 Enforced vs instructed

| Rule | Enforced by code? | Where |
|---|---|---|
| Step order, tier gate, "never skip a step" | No. The manifest records what the agent reports (`run step`). The ship gate's tier artifacts cover only steps 12/14/15 | `runs.py:240-298`, `runs.py:808-820` |
| Tier decides required steps at the gate | Yes. The decomposition's `pipeline_tier` overrides the manifest profile | `runs.py:609-646` |
| Never end the turn mid-pipeline | Codex: Stop hook blocks once (`stop_hook_active` then lets it stop). Claude Code: instruction only. The Claude install adds only a PreToolUse hook | `codex.py:347-386`, `cli/run_cmd.py:249-294`, `hooks.py:3682-3688` |
| "Check the vault before web search", "don't use WebFetch" | Advisory only: a Node script injects `additionalContext` on every WebSearch/WebFetch | `hooks.py:3557-3604`, `hooks.py:3815-3825` |
| Budget ceiling (`--budget`) | In practice no. `estimated_usd` moves only via `hpr run spend`, which no step skill calls | `runs.py:301-324`, `runs.py:399-413` |
| Source/note ceilings | Only when `--max-sources/--max-notes` are passed (the router never mentions them) | `runs.py:381-432` |
| Tool locks (e.g. fetcher has no WebFetch) | Claude Code: agent `tools:` frontmatter. Codex: prompt discipline only ("Codex cannot enforce that list, so you must") | `hooks.py:2965`, `codex.py:137-149` |

---

## 3. Tiers, gears and scale profiles

### 3.1 Mechanics

- `Profile` is a frozen pydantic model holding every scale number (`profiles.py:112-217`). Built-ins: `light`, `full`, `premier`, `dissertation` (`profiles.py:253-423`). `GEAR_PROFILES = ("full", "premier")`; light and dissertation are runtime tiers (`profiles.py:425-432`). Users can override or extend in `.hyperresearch/config.toml` (`profiles.py:439-497`).
- Rendering: Jinja with `<< >>`, `<% %>` and `<# #>` delimiters, plus `StrictUndefined`, so a typo fails the install (`render.py:1-26`, `render.py:50-64`). The context is `p` (the installed gear) plus every profile by name plus `platform` (`render.py:67-82`). Install uses the persisted gear (`cli/install.py:70-78`). `hpr profile use <full|premier>` re-renders every installed prompt and "takes effect on the NEXT run" (`cli/profile_cmd.py:107-181`).
- Tier selection is done by the model in step 1 (`hyperresearch-1-decompose.md:108-117`; "Default is full. When uncertain, tier up."). The gate maps tier to required steps (`runs.py:627-646`). Steps are integers 1-16 only (`profiles.py:234-244`), so the half-steps 1.5 and 14.5 cannot appear in any profile.
- Per-agent models: fetchers, source-analyst, loci-analyst, depth-investigator, corpus critic, cite-checker and browser-fetcher run on Sonnet. Draft orchestrator, synthesizer, critics, patcher, polish and readability run on Opus (`profiles.py:52-64`). On Codex, agents inherit the session model unless overridden (`profiles.py:74-100`).

### 3.2 What changes per tier and gear (rendered values; checked against `tests/fixtures/golden_prompts/`)

| Knob | light (tier) | full (gear, default) | premier (gear) | dissertation (tier, experimental) |
|---|---|---|---|---|
| Steps | 1, 2, 10, 15, 16 (`profiles.py:313`) | 1-16, plus 14.5 by router text | 1-16 | 1-16 in profile; router adds 1.5 and per-chapter loop |
| Source min / target | 10 / 15-25 | 45 / 55-80 | 90 / 100-130 | 250 / 300-450 (40-80 per chapter) |
| Planned searches | 8-20 (never rendered, see W7) | 40-100 | 80-160 | gear value per chapter |
| Candidate / deduped URLs | 20-40 / 15-30 (never rendered) | 80-120 / 60-100 | 150-220 / 120-180 | gear |
| Batches × URLs | 2-3 × 8-12 | 10-12 × 8-12 | 14-18 × 8-12 | gear |
| Wave 1 / 2 / 3 fetchers | 3-5 / – / – | 10-12 / 3-5 / 2-3 | 14-18 / 5-8 / 3-5 | gear |
| Adversarial searches min | (5, inherited) | 5 | 8 | 5 |
| Utility scoring | off | on | on | on |
| Academic APIs | skipped (`width-sweep.md:14`) | yes | yes | yes |
| Fetcher chase (each) | 3-8, cap 8 | 3-8, cap 8 | 3-8, cap 8 | 3-8 |
| Source-analyst cap | 6 | 6 | 10 | 6 |
| Loci analysts / loci max | – | 2 / 6 | 3 / 10 | 2 / 20 |
| Depth budget total, brackets | – | 40; 15/10/5/3 | 80; 25/15/8/5 | 160 |
| Investigators max | – | 6 | 10 | 6 |
| Drafts | 1 | 3 | 3 | 1 per chapter |
| Word target (argumentative) | 5,000-10,000 (inherited) | 5,000-10,000 | 8,000-16,000 | 25,000-80,000 configured, unused |
| Time estimate | ~30-40 min | ~1.5-2.5 h | ~3-5 h | ~4-8 h |

Sources: `profiles.py:253-307` (full), `:309-325` (light), `:327-374` (premier), `:376-415` (dissertation). Rendered checks: `tests/fixtures/golden_prompts/skills/hyperresearch-2-width-sweep.md:14,76,89,97,103,130,193,220,287-288,303`, `.../hyperresearch-4-loci-analysis.md:12,16,61,75-78,104`, `.../agents/researcher_agent.md:9-10,209,243`.

There was a `standard` middle tier, removed in 0.8.1: "Only light and full remain ... Mid-tier fan-out ... is gone" (`CHANGELOG.md:363-364`). The result is a cliff between 5 steps / 15-25 sources and 16 steps / 55-80 sources.

### 3.3 Tier and gear gaps

- Light runs read full-gear numbers in the step-2 procedure body. Light values appear only in the tier-gate sentence (`width-sweep.md:14`), the utility gate (`:109`) and the table row (`:293`). A grep for `light\.` across skills and agents finds only `source_target`, `batch_count`, `utility_scoring`, `source_min`, `wave1_fetchers`, `waves` and `time_estimate`. `light.planned_searches`, `light.candidate_urls` and `light.deduped_urls` (`profiles.py:316-318`) are dead config.
- The gate's length target comes from the manifest profile (`runs.py:661`, `runs.py:705-730`), while drafting text comes from the gear `p.word_targets` (`hyperresearch-10-triple-draft.md:48-50`). The router offers `run init --profile premier` (`hyperresearch.md:124-126`). If that runs under an installed `full` gear, drafters target 5,000-10,000 words and the gate wants 6,400-19,200.
- Dissertation: step 1 only offers short/structured/argumentative (`decompose.md:119-125`), so the gate measures a 25k-80k-word document against argumentative's 5,000-10,000 (±20%), and the router's fix rule says to compress (`hyperresearch.md:276`). The roadmap planned "steps incl. 1.5" for this profile (`docs/roadmap-2.0/phase-3-dissertation-scale.md:106`), but the validator forbids it (`profiles.py:234-244`).

---

## 4. Step 1: decompose (inline, lead agent)

What it instructs (`hyperresearch-1-decompose.md`):

- Re-read `query.md` and extract atomic items: sub-questions, named entities with required fields, required formats, required sections, time horizons, period-pinned time periods ("the #1 cause of 'agent had the topic right but missed the rubric's exact figures'", `:42`) and scope conditions (`:34-43`).
- `required_section_headings`: an ordered list of literal H2 strings, never empty ("single highest-leverage field for instruction-following scores", `:45`). Enumerated asks map 1:1 in prompt order. Entity lists get one heading each. Narrative prompts get 4-7 derived headings (`:45-58`).
- Write `prompt-decomposition.json` (`:60-102`) with:
  - `pipeline_tier` (light/full, default full);
  - `response_format` (short 500-2,000 / structured 2,000-5,000 / argumentative 5,000-10,000 words);
  - `citation_style` (wikilink default / inline / none; the wrapper can override);
  - `levers`: register teach/survey/analyze/advocate with a confidence rule; 2-3 sentences of `domain_notes`; provisional `inference_depth` surface/standard/deep (`:108-160`).
- "Omit nothing the prompt names explicitly" (`:104`).
- Coverage-matrix self-audit (`:162-179`): every significant noun phrase maps to an atomic item with a scope check ("SaaS applications" must not narrow to "POS SaaS"), and both readings are covered when the phrase is ambiguous. Loop until zero `Gap? = YES` rows, written to `temp/coverage-matrix.md`.
- Append a tier rationale to the scaffold, then run `hpr levers render <tag>` to write four shim files (`:181-189`).

Outputs that later reach the ship gate:

- `required_section_headings` becomes a literal-substring check, `missing = [h for h in required_headings if h not in report_text]` (`runs.py:732-737`);
- `response_format` sets the length band (`runs.py:705-730`);
- levers present means the shims must exist (`runs.py:688-703`).

Nothing checks the coverage matrix, `time_periods` or atomic items.

Levers and shims (`core/levers.py`): fixed text blocks per register and per inference depth are composed additively into role shims (`levers.py:235-258`):

- research = header + domain notes + inference depth;
- drafting = header + register + domain + depth;
- critics = header + register + depth;
- polish = header + register.

The rule "Shim text must never restate a numeric budget" (`levers.py:15-17`) keeps posture separate from numbers. Enums are validated (`levers.py:198-214`). `register_confidence` is not used by code. Step 4 can upgrade depth with `levers set ... --rerender` (`cli/levers_cmd.py:67-106`).

Cost: small (one inline pass, roughly 5-15k output tokens by my estimate, a few file writes and one CLI call). It has a large effect on structure and on the gate.

## 5. Step 1.5: chapter partition (dissertation only)

- Group atomic items into 4-10 chapters, each answerable with 40-80 sources. Follow the required headings 1:1 when they exist. Fewer than ~12 items means one chapter (`chapter-partition.md:32-36`).
- Write `chapter-plan.json`, create chapter workspaces, register each chapter with `run event --type chapter-plan` (folded into the manifest by `runs.py:224-237`), and mark step 1.5 done (`:38-64`).
- Tag notes `<tag>` and `<tag>-<chN>` (`:66`). Loop steps 2-10 per chapter with up to 2 in flight and one draft per chapter. Step 6 and step 11 then run globally (`:70-80`). Check the budget at chapter boundaries (`:82`), though in practice the budget never trips (see W10).
- The rationale is a claimed "~80-source quality ceiling ... per-chapter, not per-run" (`:17`). This is experimental by the router's own statement.

---

## 6. Step 2: width sweep (the cost centre of the front half)

### 6.1 Search planning (2.1, inline)

Four lenses per atomic item (`width-sweep.md:36-64`):

- **A breadth:** core facts, last-2-years developments, each named entity.
- **B canonical:** academic APIs, seminal works, "original study" upstreams.
- **C adversarial:** "criticism of X", failures, at least one "X is wrong" search per major item.
- **D period-pinned primary filings:** mandatory when `time_periods` is set. Covers SEC EDGAR filing indexes, Companies House filing history, dated press releases, and "Earnings-call transcripts are insufficient on their own" (`:63`).

The plan is a table with a Lens column in `temp/search-plan.md` (`:66-74`): 40-100 searches for full (`:76`). A search-gap check runs against the coverage matrix before fetching (`:78-85`). "Execute searches from ALL three lenses" (`:87`; the text says three but defines four). Minimum adversarial searches: 5 for full, 8 for premier (`:89`).

### 6.2 Search execution and queue (2.2, inline)

- "Academic APIs first ... Semantic Scholar / arXiv / OpenAlex / PubMed" (`:95`), with no command named. The wired CLI is `hpr scholar search` over OpenAlex, Crossref, CORE, DOAB, RePEc, ClinicalTrials, EDGAR and FRED (`src/hyperresearch/scholar/providers/`). The pointer to it lives only in the CLAUDE.md block (`core/agent_docs.py:72-95`), which also says "when the skill file and this file disagree, the skill file wins" (`agent_docs.py:66`).
- "Execute ALL planned searches": 80-120 candidate URLs, deduped to 60-100 (`:97-99`). Wikipedia is a source hub: fetch it for its references, never cite it (`:101`).
- Partition into 10-12 non-overlapping batches of 8-12 URLs (`:103`). Batches are by URL, not by topic.

### 6.3 Utility scoring (2.3, inline; full and premier only)

Six 0-3 dimensions: authority, novelty, stance diversity, coverage, redundancy, freshness (max 18). "Select the top N URLs (where N = batch capacity × batch count)" with a constraint of ≥3 candidates per atomic item (`:111-120`). Scores go to `temp/scored-urls.md` and travel with URLs into `fetch --utility-score` (`:124`). They become 20% of the composite `quality_score` (`core/quality.py:3-53`, `core/config.py:115-118`).

At full gear the capacity (10-12 × 8-12 = 80-144) is at least the deduped queue (60-100), so the selection rarely removes anything. The scores mostly feed the composite.

### 6.4 Fetcher waves (2.4)

- Wave 1: "Spawn 10-12 fetcher subagents in ONE message", one batch each (`:130`). The spawn template says "you fetch ONLY the URLs in your batch. Do not search for additional URLs" (`:144-146`), and "If a fetcher finishes early, it's done." (`:157`).
- While waiting, the orchestrator writes to `orchestrator-notes.md` every 30-60 s "AND keeps the turn alive" (`:161-168`). It is unclear whether this is possible while foreground Task calls are in flight.
- Vault-count polling (`:170-175`) uses a bash pipeline into `python -c`. A wave is "done" at ≥80% of queued URLs, which is loose because failed fetches create no note and chased sources do.
- The fetcher agent (`core/hooks.py:2955-3217`, Sonnet, tools Bash/Read/Write/WebSearch, no WebFetch). Phase 1, per assigned URL (`hooks.py:3079-3150`):
  1. `sources check` (skip if already fetched);
  2. `hpr fetch "<url>" --tag <topic> [--utility-score N]`;
  3. `note show -j` to read the full body;
  4. deprecate it if off-topic, junk or a duplicate;
  5. write a summary sized to density (1-2 sentences up to 3-6 paragraphs) and add tags;
  6. Write `temp/claims-<note-id>.json`: 3-8, 8-15 or 15-25 claims with stance, stance_target, evidence_type, scope, `quoted_support` ("THIS IS THE MOST IMPORTANT FIELD"), numbers, entities, period, region and confidence;
  7. collect leads.

  Phase 2 is mandatory (`hooks.py:3152-3201`): chase the "3-8 most promising" leads by authority, specificity, citation frequency and relevance. Use WebSearch when only author and title are known. Fetch with `--suggested-by <citing-note> --suggested-by-reason` and process each chased source like Phase 1, capped at 8 extra. The report back covers all note ids and summaries, verdicts, chase counts, unfetched leads and long sources (`hooks.py:3203-3216`).
- Period-pinned rules in the fetcher (`hooks.py:2993-3026`): open the EDGAR or Companies House filing history, fetch the filing document for the exact named period, extract tabular line items verbatim without rounding, and report a wrong-period mismatch instead of substituting.
- The fetch CLI (`cli/fetch.py:207-529`):
  - a duplicate URL errors with `DUPLICATE_URL` unless `--suggested-by` is passed, in which case it appends a breadcrumb (`:254-296`);
  - a login wall or bot wall tries an open-access rescue first, then queues a browser-lane escalation (`:318-409`);
  - a thin page with a DOI is swapped for a legal OA copy, with the substitution disclosed (`:418-488`);
  - the breadcrumb `*Suggested by [[id]]*` is prepended to the new note's body (`:468-478`).

### 6.5 Coverage check, redundancy audit, ranking (2.5-2.7)

- 2.5 (inline): map sources to atomic items as well-covered 4+, adequate 2-3, thin 1, uncovered 0. Thin or uncovered items get 2-3 targeted searches and 3-5 wave-2 fetchers (`:179-200`). The goal sentence asks for "at least 3 supporting sources" per item (`:16`). The exit criterion says "no uncovered atomic items (thin is acceptable)" (`:337`), and "If you fall short after two waves, proceed anyway" (`:341`).
- 2.6 (inline, full only): "Read ... claims-<note-id>.json for every non-deprecated note" (`:210`). Cluster on >60% shared `quoted_support` and on suggested-by ancestry, tag `derivative-of`, discount derivatives in coverage counts, and run wave 3 with 2-3 fetchers if any item drops below 2 independent sources (`:204-220`).
- 2.7 (CLI, all tiers): `claims ingest`, `sources backfill-doi`, `sources score` (citations and retractions, cached APIs) and `graph rank` (PageRank plus composite) (`:224-237`). Retracted sources are flagged and floored (`quality.py:34-35`).
- 2.8: on Claude Code, one serial browser-fetcher drains up to 10 escalations through Claude-in-Chrome and never solves CAPTCHA, login or 2FA; needs-human items are consolidated into one message to the user, or `run block --on human-challenges` in `-p` mode (`:241-286`, `hooks.py:3345-3468`). On Codex the queue stays as it is and is listed at the end (`:249-254`).
- Long-source delegation: when a source is over 5,000 words, relevant and not yet analysed, spawn a source-analyst (cap 6 for full, 10 for premier) to read it end to end and write a `source-analysis` note (`:300-330`, `hooks.py:2756-2948`).

### 6.6 Fan-out arithmetic (my calculation from the rendered numbers)

Wave 1 assigns 60-100 URLs. Each fetcher must also chase 3-8 more (cap 8), which across 10-12 fetchers adds 30-96 candidates before waves 2 and 3. The README says so: "citation chasing and gap-fill fetches more than double what actually lands in the corpus" (`README.md:53`). The same step warns that "beyond ~80 sources, each additional source yields diminishing returns while degrading summarizer quality" (`width-sweep.md:296`). The sample full-tier report cites 97 numbered sources across 11,045 words, took ~2 h and scored RACE 58.3 (`example-reports/rl-exploration-trajectory-planning.md:7`; my count of `[N]` markers and words).

---

## 7. Step 3: contradiction graph (inline, full only)

- Skipped if there are no claims files (`contradiction-graph.md:27`).
- Load every `temp/claims-*.json` (`:33`) and pair contradictions on four signals: same stance_target with opposite stance, same entities with opposite conclusions, the same scope with different numbers, and overlapping scope with different evidence types (`:35-39`).
- Cluster pairs into "fights" with side_a/side_b, evidence-quality delta, scope overlap and decision relevance. Rank by relevance, then by tightness. Write `temp/contradiction-graph.json` (`:41-56`).
- Consensus claims: run `sources independence` and count clusters as one voice, with a "sum of independence scores ≥ 3.0" rule written to `temp/consensus-claims.json` (`:58`).
- Substrate limits:
  - The DB claims table drops entities, scope, period and region (`core/claims.py:124-141`), so the pairing has to be done by reading the raw JSON in the lead's context.
  - The only grouping helper, `claims targets`, groups by exact `stance_target` string (`core/claims.py:342-387`), and step 3 does not call it.
  - The independence math does not give one voice per cluster (W5).

## 8. Step 4: loci analysis (full only)

- Spawn 2 (full) or 3 (premier) loci-analysts in one message, ids a, b, c, each writing `loci-<id>.json` (`loci-analysis.md:34-57`). The analyst prompt (`hooks.py:130-329`, Sonnet, Bash/Read/Write) works as follows:
  - Stop if the corpus has fewer than 10 notes (`:208-211`).
  - Read the contradiction graph first and promote validated high-relevance fights to dialectical loci (`:213-219`).
  - Read the corpus breadth-first: "title + summary + first ~400 chars (use `note show <id> -j` and truncate)" (`:221-225`).
  - Choose 1-8 loci answerable by 3-8 more sources that the corpus "GESTURES at" but does not resolve and that are load-bearing (`:227-233`).
  - Return convergent or dialectical loci, at least one dialectical unless `skip_loci` proves the corpus is univocal (`:235-253`). Each locus carries corpus-evidence note ids, opposing positions, starting URLs and searches (`:262-298`).
- Orchestrator (inline):
  - dedupe by name or near-match, clamp to 6 (full) or 10 (premier), and keep the union of `skip_loci` (`:61-65`);
  - score importance, uncertainty, disagreement and decision impact (0-10 each, max 40) and allocate from a total of 40 (full) or 80 (premier) using brackets of up to 15/10/5/3 (`:67-81`);
  - write `loci.json` (`:83-102`) and set the investigator count to the number of loci with budget > 0, capped at 6 or 10 (`:104`);
  - reconsider `inference_depth` and possibly run `levers set ... --rerender` (`:106-112`).
- Invariant: at least one dialectical locus, or the analyst is re-spawned (`:114`). Prompt only.

---

## 9. Context management across the pipeline

What works:

1. Procedures are loaded just in time: each step skill is loaded fresh with `Skill` (Claude) or `cat` (Codex) only when needed (`hyperresearch.md:49-57`).
2. State lives on disk: every step reads its inputs by path (scaffold, query, decomposition, matrices, plans, JSONs), and "each step is self-contained and reads its inputs from disk" (`hyperresearch.md:325`).
3. Durable position: TodoWrite or plan items (`:163-168`), the manifest with `run step` and `events.jsonl` (`runs.py:180-298`), and `run resume`, which takes the tier from the decomposition into account (`runs.py:516-526`), with an artifact-scan fallback (`hyperresearch.md:225-242`).
4. Source bodies are read by subagents. The lead sees summaries through `note list --json`, which includes `summary` (`cli/note.py:375-392`). Long sources go to source-analyst digests.
5. Subagents do not depend on the lead's context: the spawn contract carries the verbatim query, the pipeline position and the shim (`hyperresearch.md:204-214`).

What leaks into the lead's context:

1. **Search execution:** all 40-100 planned searches (80-160 at premier) are run by the lead, because fetchers are told not to search (`width-sweep.md:87`, `:97`, `:144-146`). Each WebSearch result (my estimate is roughly 1-2k tokens) also triggers the PreToolUse reminder (`hooks.py:3581-3602`).
2. **URL scoring:** 80-120 URLs × 6 dimensions, written inline (`:111-122`).
3. **Fetcher reports:** each returns all note ids and summaries (`hooks.py:3206`). Across 15-20 fetchers that is tens of thousands of tokens by my estimate.
4. **Claims:** step 2.6 reads every claims file (`width-sweep.md:210`) and step 3 loads them all again (`contradiction-graph.md:33`). At 60-200 notes × 3-25 claims this can run from about 100k to several hundred thousand tokens (my estimate). On a 200k-context lead this forces compaction inside the step, in the middle of the corpus.
5. **Loci analysts:** they are told to read ~400 characters per note via `note show -j`, but that command returns the full body. The only reduced view is `--meta` (`cli/note.py:161-227`).

---

## 10. Cost (tokens, time, tool calls)

- The project gives no dollar figures: "Dollar-cost estimates removed from the product" (`CHANGELOG.md:219`).
- The roadmap's own figure: "300+ sources ≈ $200–500/run" for dissertation scale (`docs/roadmap-2.0/phase-3-dissertation-scale.md:133`). Scaling that linearly to a full-gear corpus of ~60-150 notes gives roughly tens to low hundreds of dollars API-equivalent per run. This is my extrapolation and is unverified.
- Time: light ~30-40 min, full ~1.5-2.5 h, premier ~3-5 h, dissertation ~4-8 h (`profiles.py:306,324,373,414`; recalibrated from observed runs per `CHANGELOG.md:365`). The repo has no per-step timing for steps 1-4.
- Subagents in steps 2-4 at full: 10-12 + 3-5 + 0-3 fetchers, 0-6 source-analysts, 0-1 browser-fetcher and 2 loci-analysts, so about 15-29 Sonnet agents. At premier, about 22-45.
- Tool calls (my estimate from the per-URL procedure in `hooks.py:3081-3194`):
  - per assigned URL: about 6 calls (check, fetch, show, summary, tag, claims write);
  - per chased URL: about 7;
  - per fetcher: about 70-130;
  - wave 1 total: about 700-1,500;
  - lead in steps 1-4: about 100-300 (searches, CLI, file writes, claims reads).
- Tokens (my estimate): each fetcher reads 15-20 full bodies (about 100-300k tokens of source text before re-sends) and writes 10-60k tokens of summaries and claims. The width sweep therefore dominates cost before drafting.

---

## 11. Weaknesses (detail)

W1, high. **The lead does bulk work inline.** It runs all the searches, scores the URLs and reads all claims twice. See section 9 for evidence. Impact: compaction in the middle of a step, claims that are dropped or never read, and slower steps 2-3.

W2, high. **Front-half rules are prompt text.** The gate checks no step 1-4 artifact except headings, length and shims (`runs.py:649-844`; tier artifacts only for 12/14/15 at `:808-820`). Exits allow shortfalls ("proceed anyway", `width-sweep.md:341`). Source minimums, ≥3 sources per item, the adversarial floor, the zero-gap matrix (`decompose.md:179`) and the dialectical invariant (`loci-analysis.md:114`) are unverified, so output quality depends on how well the model complies, and the manifest cannot show whether coverage happened.

W3, medium. **The fan-out overshoots its own target.** See 6.6. The cost and time grow while the step itself predicts declining summarizer quality.

W4, medium. **Conflicting fetcher instructions.** The spawn prompt says "Do not search for additional URLs" and "If a fetcher finishes early, it's done" (`width-sweep.md:144-146`, `:157`). The agent prompt says Phase 2 is "NON-OPTIONAL ... use WebSearch to locate it" (`hooks.py:3154`, `:3181-3182`), and router invariant 12 sides with chasing (`hyperresearch.md:300`). Behaviour is unpredictable: either fewer primaries or unplanned searching.

W5, medium. **Independence math.** A k-member cluster gets root 1.0 and members 1/k each (`independence.py:127-143`), so it sums to 1 + (k-1)/k. Five reprints count as 1.8, against "count each cluster as ONE voice" (`contradiction-graph.md:58`) and the README ("five reprints ... the weight of one source", `README.md:55`). The docstring says independence also feeds the quality composite (`independence.py:15-16`), but `quality.py` never reads it. Two syndicated stories can make false "consensus" that the draft then asserts without hedging.

W6, medium. **PageRank credits the wrong end.** The breadcrumb wiki-link sits in the chased note (`fetch.py:468-478`), and links are stored as source_id = the containing note (`sync.py:317-327`). So rank flows from primaries to the secondary or hub that suggested them, the opposite of the docstring's "many independent research chains converged on this source" (`graphrank.py:4-8`). Centrality is 20% of `quality_score` (`config.py:118`) and is computed only at step 2.7 (`width-sweep.md:232`). Step 10's ranked curation is biased toward hubs and secondary sources.

W7, medium. **The light tier reads full-gear numbers.** See 3.3. The procedure body says "Spawn 10-12 fetcher subagents" and "Aim for 80-120 candidate URLs" (rendered fixture lines 97 and 130), while the light-specific planned searches and URL counts are never rendered. Light runs can over-search and over-spawn, so the advertised 30-40 minutes is not protected.

W8, medium. **Prior-run sources are invisible to the current run.** The fetcher skips any URL that `sources check` finds (`hooks.py:3083-3087`). `fetch` on a duplicate never adds a tag (`fetch.py:254-296`). Run-scoped steps select by exact tag (`cli/note.py:347-349`). The "compounding vault" (`README.md:59`) does not feed coverage, loci or curation, and the run either refetches elsewhere or reports a gap.

W9, medium. **`citation_style: "none"` cannot ship.** It is offered at `decompose.md:139`, but the citation-density floor of 9 per 1,000 words is applied unconditionally (`runs.py:747-770`, `profiles.py:298`), and `verify_run` never reads the style. A user who asks for no citations gets a blocked run or citations anyway.

W10, medium. **The budget governor is inert.** `run init --budget` is offered (`hyperresearch.md:127`) and advertised as "caps estimated API-equivalent spend" (`README.md:319`), but nothing increments `estimated_usd` without `hpr run spend` (`runs.py:301-324`, `:399-413`), and no step skill calls it. The user gets no cost ceiling.

W11, medium. **The dissertation length gate.** See 3.3. Experimental runs get compressed to about 7,500 words or stay blocked.

W12, low. **Manifest profile vs gear mismatch.** See 3.3. `run init --profile premier` under the full gear makes the gate's length target and the drafting text disagree.

W13, low. **Loci flavour enum mismatch.** `loci.json` uses `"dialectical|synthesis|technical"` (`loci-analysis.md:90`), but the analysts emit `"convergent"` or `"dialectical"` (`hooks.py:235-242`, `:269`). The merged JSON is inconsistent.

W14, low. **Stale tier pointer.** Step 4 says light should "proceed directly to step 9" (`loci-analysis.md:14`), while the router and profile say 1, 2, 10, 15, 16 (`hyperresearch.md:90`, `profiles.py:313`). The loci analyst still describes "Layer 2 of the 7-phase pipeline" (`hooks.py:152-160`). This shows the prompts drifting apart.

W15, low. **Claims example vs ingester.** The fetcher example is a single object (`hooks.py:3122-3137`), while `_iter_claim_dicts` accepts only a list or `{claims: [...]}` (`claims.py:75-83`). A literal bare object ingests zero claims with no error.

W16, low. **Coverage thresholds do not agree.** The goal is ≥3 per item (`width-sweep.md:16`), "well-covered" means 4+ (`:186`), and the exit accepts thin (`:337`).

W17, low. **Utility scoring does not select.** See 6.3. It costs tokens and has little effect.

W18, low. **API names drift.** Step 2 names Semantic Scholar, arXiv and PubMed (`:45`, `:95`), which are not wired providers, and the fetcher says "Semantic Scholar: search the API" (`hooks.py:3186`). The wired `scholar search` is mentioned only in CLAUDE.md, which defers to the skill (`agent_docs.py:66`, `:72-83`). The agent may hand-assemble API calls against CLAUDE.md's "Do NOT hand-assemble API URLs" (`agent_docs.py:83`).

W19, low. **Ambiguous tags.** `--tag <topic>` appears in the fetcher (`hooks.py:3047`, `:3087`) and `--tag <topic-tag>` and `--tag scholar-results` in the browser-fetcher (`hooks.py:3429`, `:3450`). Escalations are keyed on the first tag (`fetch.py:684`), so notes or escalations can fall outside the run.

W20, low. **No completion guard on Claude Code.** Only PreToolUse is installed (`hooks.py:3682-3688`), so finishing a 1.5-2.5 h run depends on "NEVER EMIT BARE TEXT" (`hyperresearch.md:180`).

W21, low. **Windows.**
- The hook needs `node` on PATH (`hooks.py:3823`); the native Claude Code install does not ship Node, so every WebSearch and WebFetch produces a hook error.
- Bash-only snippets (`hyperresearch.md:254-261` for-loop, `width-sweep.md:172` env prefix plus `python -c` with `\"` escapes) fail on Codex/PowerShell, which `codex.py:127-129` acknowledges exists.
- The `PYTHONIOENCODING` prefix applies only to the first command in the pipe, so the `python -c` consumer reads stdin in the ANSI code page (Python before 3.15 without UTF-8 mode). This is low risk because the CLI already forces UTF-8 output (`cli/__init__.py:23-29`).

W22, low. **Weak evidence for the router design.** It compares Q57 and Q9, two different questions (`hyperresearch.md:313`).

W23, low. **Half-steps are invisible to the manifest.** 1.5 and 14.5 cannot be profile steps (`profiles.py:234-244`), so `run resume` never routes there. Cite-check is verified only if the agent recorded 14.5 as done (`runs.py:822-842`).

W24, low (design). **URL-batch partitioning.** No fetcher owns a sub-question (`width-sweep.md:103`), so coverage is assembled only by the lead after a whole wave, and chases can duplicate across fetchers. The duplicate-URL handling prevents refetching but not wasted lead-finding.

W25, low. **Overlapping labels.** Modality (router), response_format, register and tier (step 1) are four classifiers with overlapping meaning (`hyperresearch.md:141-145`, `decompose.md:108-160`) and no rule for resolving conflicts.

---

## 12. Ideas for vafer-research (VAFER/skills/vafer-research/SKILL.md v0.1.0-alpha)

- Adopt: a phrase-level scope check in plan.md. Each significant query phrase maps to a checklist row, and a narrowed scope counts as a gap (from the coverage matrix in `decompose.md:162-179`).
- Adopt: period-pinned extraction. When the question names a fiscal period or dated event, add a row for the filing of that exact period and a scout query aimed at it (Lens D, fetcher rules).
- Keep and strengthen VAFER's thin lead. Researchers search and read; the lead sees ≤300-word summaries. This is VAFER's biggest structural advantage over hyperresearch's inline search and claims loading.
- Keep researcher ownership by sub-question instead of URL batches, so each researcher answers for its row's coverage.
- Adapt the adversarial floor per contested row (at least one criticism or counter-evidence query) instead of a global count.
- Adapt citation chasing: briefs should ask researchers to follow up to N primaries cited by secondary pages and record "found via <URL>".
- Adopt a one-line posture field in plan.md (teach / survey / analyze / advocate) to steer the report voice. Skip the four-file shim machinery.
- Adopt a light "loci" pass: after wave 1, rank OPEN, PARTIAL and CONFLICT rows by decision impact × uncertainty and spend the gap wave on the top 1-3.
- Adopt for contested topics: at least one CONFLICT row examined with each side's best evidence (from the dialectical-locus invariant).
- Adopt legal open-access rescue for paywalled papers (Unpaywall, Europe PMC, CORE), disclosed in the notes.
- Avoid unenforceable numeric targets. Any rule VAFER keeps should be checkable in one pass (every [n] resolves, every quote appears in notes), or be dropped.
- Avoid pre-fetch utility scoring. In hyperresearch it costs tokens and selects almost nothing.
- Avoid PageRank and composite quality scores. hyperresearch's version is inverted. Label each source primary or secondary instead.
- Keep VAFER's "copies of one account count once". Do not copy the 1/k-per-member independence weighting.
- Keep three tiers. hyperresearch's light/full cliff (5 vs 16 steps, 30 min vs 2 h) is the gap VAFER's Standard tier fills.
- Keep each tier's numbers inside that tier's own section, so a lighter tier never reads a heavier tier's counts.
- Key reuse by topic and question through INDEX.md, not by a per-run tag. hyperresearch's tag scoping hides prior-run sources.
- Do not offer an output option the final check rejects (hyperresearch's citation_style "none").
- Keep instructions shell-agnostic. hyperresearch's bash snippets and Node hook break on Windows and Codex/PowerShell.
- Avoid depending on a single turn lasting hours. Keep the VAFER Deep state resumable from plan.md with one "next action" line.
- Do not split SKILL.md into per-step files while it stays short (83 lines). hyperresearch needed that only because one prompt grew to 1,200 lines.

---

## 13. Key claims for independent checking

1. In steps 1-4, the only rules enforced in code are the step-1 outputs the ship gate reads (literal required headings, the response_format length band, shim files present). Source minimums, per-item coverage, the adversarial floor, the zero-gap coverage matrix and the dialectical-locus invariant are prompt text, with explicit "proceed anyway" escapes. Evidence: `runs.py:649-844` (esp. `:705-737`, `:808-820`); `width-sweep.md:336-341`; `loci-analysis.md:114`.
2. The lead runs the 40-100 planned searches, scores 80-120 URLs and reads every claims file in its own context (twice: 2.6 and 3). Fetchers are told not to search and must return every summary. Evidence: `width-sweep.md:87,97,107-122,144-146,157,210`; `contradiction-graph.md:33`; `hooks.py:3203-3211`.
3. Scale numbers are rendered into skill text at install time from one gear (`p`). A light-tier run sees full-gear counts in the step-2 body, and `light.planned_searches`, `light.candidate_urls` and `light.deduped_urls` are rendered nowhere. Evidence: `render.py:67-82`; `profiles.py:309-325`; `width-sweep.md:14,76,97,103,130,293`; golden fixture `tests/fixtures/golden_prompts/skills/hyperresearch-2-width-sweep.md:14,76,97,103,130,287`.
4. The independence audit weights a k-copy cluster at 1 + (k-1)/k (five reprints = 1.8 voices), against step 3's "count each cluster as ONE voice" and the README. Evidence: `independence.py:127-143`; `contradiction-graph.md:58`; `README.md:55`.
5. Vault PageRank credits the suggesting (secondary or hub) note rather than the chased primary, because the `--suggested-by` breadcrumb wiki-link is written into the chased note. Centrality is 20% of `quality_score` and is computed once at step 2.7. Evidence: `fetch.py:468-478`; `sync.py:317-327`; `graphrank.py:4-8,36-58`; `config.py:115-118`; `width-sweep.md:232`.
6. A URL fetched in an earlier run is skipped by fetchers without adding the current run's tag, and run-scoped steps select notes by exact tag, so prior-run sources do not count toward coverage, loci or curation. Evidence: `hooks.py:3083-3087`; `fetch.py:254-296`; `cli/note.py:347-349`; `cli/sources.py:64-97`.

## 14. Unsure / not verified

- Whether Claude Code lets the orchestrator append notes while a single-message batch of foreground Task calls is running (`width-sweep.md:161-168`). If it cannot, that instruction has no effect.
- Real per-step time and token figures. The repo has only whole-run time estimates and the sample's ~2 h. My token and tool-call figures are derived from the prompt procedures, not measured.
- How often fetchers actually skip Phase 2 under the conflicting instructions (W4), or write bare-object claims files (W15).
- The README's DRACO and sample results come from the hosted "Deep" version (`README.md:38-49`). Whether that matches this package's full or premier gear is not stated.
