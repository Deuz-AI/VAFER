# hyperresearch, back half: critics, gap fetch, patcher, cite-check, polish, readability (steps 12-16) and the subagent roster

Date: 2026-10-27. Clone: `C:/Users/VECTOR/Documents/GitHub/hyperresearch`, HEAD `327498b`, plugin version 0.12.0 (`.claude-plugin/plugin.json`).

Method. Read-only. Nothing in the clone was installed, imported or run. Two checks were run outside it:

- a standalone script in the session scratchpad (`citecheck-probe/probe.py`) that copies the regex lines of `core/citecheck.py` and runs them on sample sentences;
- an `ast` parse of `core/hooks.py`, read as text, to measure prompt sizes and count `{{` in each agent template.

Files read in full: the six step files, `core/agent_docs.py` and `core/templates.py`. I followed references from those into:

- `core/hooks.py` (agent prompts and installers)
- `core/profiles.py`, `core/render.py`, `core/codex.py`, `core/levers.py`, `core/config.py`
- `core/citecheck.py`, `cli/citecheck_cmd.py`
- `core/runs.py` (`verify_run`, `finish_run`, resume logic)
- `cli/lint.py` (quote-integrity, numeric-consistency, retracted-citations, patch-surgery) and `cli/search.py`
- `skills/hyperresearch.md` (the router's final gate), `README.md`, `CHANGELOG.md`, `docs/roadmap-2.0/phase-5-verification.md`
- `example-reports/rl-exploration-trajectory-planning.md` and `tests/test_core/test_verification.py`

All paths below are relative to `src/hyperresearch/` unless they start with a top-level folder.

---

## 1. Summary

Steps 12-16 are a correction layer that runs after the final report has already been synthesized in step 11.

1. **Step 12.** Four Opus critics (dialectic, depth, width, instruction) read the report and the vault, then write capped findings JSON without exact patches. The caps are 12, 12, 10 and 15 at the `full` gear.
2. **Step 13.** The orchestrator runs a gap fetch when a finding names a topic that has 0-1 vault notes. It handles at most 5 gaps with 2-4 Sonnet fetchers.
3. **Step 14.** One Opus patcher applies the findings as surgical Edits. On Claude Code it is tool-locked to Read+Edit. It logs to a pre-stubbed JSON file and sends H2 restructures back to the orchestrator.
4. **Step 14.5 (cite-check).**
   - Python splits the report into sentence-citation pairs.
   - A pair auto-passes when its numbers or a 6-word shingle appear in the cited note's extracted claims.
   - Dangling citations become critical findings.
   - A Sonnet checker judges the rest, and a second patcher pass fixes what it flags.
5. **Step 15.** An Opus polish auditor strips pipeline-vocabulary leaks, meta-discourse, filler and hedges.
6. **Step 16.** An Opus readability recommender writes up to 50 JSON suggestions. The orchestrator applies the ones it chooses.

The binding ship gate (`run finish`) checks length, headings, citation density, quote integrity, retractions and whether artifact files exist. Most "critical findings must be fixed" rules are instructions to the orchestrator, not enforced.

---

## 2. Step by step

### Step 12: four parallel critics (`skills/hyperresearch-12-critics.md`)

- **Tier gate.** Full tier only; light skips to step 15 (`12-critics.md:13`). The four critics are spawned "In ONE message" (`:31`).
- **Spawn contract.** Each spawn gets four things (`:37-58`):
  - the verbatim query, block-quoted, labelled "gospel";
  - the query file path;
  - a pipeline-position paragraph;
  - the inputs (`draft_path`, `output_path`, `vault_tag`, plus `decomposition_path` for the instruction critic only), with `shims/critics.md` pasted verbatim at the end as RUN DIRECTIVES.
- **Partial set.** The step may proceed with a partial set of critics, but "**Do NOT skip the instruction-critic specifically** — it's the only critic measuring prompt adherence, which is the dimension with the widest variance" (`:60`).
- **Orchestrator stays out.** "Do not read the findings yourself and apply them." (`:62`)
- **Exit check.** All four JSONs exist and "Each is valid JSON with a `findings` array" (`:68-69`). The orchestrator checks this; no code does.

The critic prompts live in `core/hooks.py`. All four run on `model: << p.models.critics >>`, which defaults to opus (`profiles.py:61`), with `tools: Bash, Read, Write`.

| Critic | What it checks | Severity scale | Cap (full / premier / dissertation) | Where |
|---|---|---|---|---|
| dialectic | Counter-evidence the draft ignores, hedges or straw-mans. It searches the vault (`search ... --tag <vault_tag> -j`) for notes that disagree, reads suspect notes in full, and proposes "a sentence to insert, a qualifier to add, a citation to include". Its commitment standard depends on the register (teach/survey vs advocate). | critical = "the draft asserts something that the vault's own evidence contradicts"; major = ignores a counter-position the vault covers; minor = a hedge would strengthen | 12 / 16 / 24 | `hooks.py:627-755` (procedure `:686-702`, severity `:727-739`, cap `:740`) |
| depth | Places where the draft skates over substance that the depth-investigator interim notes support. It lists every interim note (`note list --type interim`), compares each note's Synthesis with the draft, and flags missing numbers or quotes, unexplained mechanisms, blanded-out disagreements and dropped citations. Its headline rule: "A developed quantitative mechanism is compressed to a bare mention ... Flag it `major`". The evidence field must cite the interim note. | critical = the thesis rests on a shallow claim that an interim note disproves | 12 / 16 / 24 | `hooks.py:761-874` (`:816-842`, `:866-867`) |
| width | Corpus clusters the draft omits or under-treats. It takes every noun phrase in the verbatim query as ground truth, lists all notes, reads `temp/coverage-gaps.md` and the decomposition, then skims 2-3 notes per candidate cluster. It also runs a **bloat check**: B1 content dilution and B2 exec-summary/conclusion repetition, at most 2 findings, justified by "top-performing reports average 45-55KB while bottom performers average 65-70KB". | critical = a cluster the query explicitly asks about is entirely missing | 10 / 14 / 20 (cap minus 2 is for coverage, 2 for bloat) | `hooks.py:880-1026` (`:919-922`, `:939-949`, `:983`, `:989-1019`) |
| instruction | Prompt adherence against the verbatim query and `prompt-decomposition.json`. Details below the table. | critical = an item the prompt names is entirely missing, or the format is fundamentally wrong | 15 / 18 / 30 (cap minus 3 is for instruction-following, 3 for readability) | `hooks.py:1036-1354` |

What the instruction critic checks, in order:

- **Phrase extraction.** Every noun phrase, imperative and format cue in the verbatim query.
- **Decomposition gaps.** Anything the decomposition narrowed or dropped is a `decomposition-gap` finding, severity critical (`:1106-1116`).
- **Structural mirror check, run first.** The ordered `^## ` headings are compared element-wise with `required_section_headings`. Every mismatch is a critical finding with `requires_orchestrator_restructure: true` (`:1118-1144`).
- **Per-item check.** Coverage, format, order and sufficiency for each atomic item (`:1147-1154`).
- **`vague-recommendation`.** A recommendation lacks the thresholds or numbers the vault holds (`:1199-1240`).
- **Readability-structural checks R1-R6**, at most 3 findings (`:1242-1315`):
  - R1: missing definitions
  - R2: citation density below 9 per 1000 words (body only)
  - R3: no forward-looking analysis
  - R4: no comparison table for 3+ entities across 2+ dimensions
  - R5: missing section primers
  - R6: dropped comparison axes

Common output schema (`hooks.py:708-721`): `{critic_type, findings:[{severity, location, issue, evidence, recommendation}]}`. The instruction critic adds `atomic_item`, `failure_mode` and `requires_orchestrator_restructure` (`:1159-1172`). All four critics are told "**Do NOT include `old_text` / `new_text` exact patches.** The revisor agent handles the exact wording" (`:723`).

Register shims (`core/levers.py:86-113`, `:183-195`) change what the critics count as a failure:

- teach and survey: hedged neutrality is correct, so flag unfair representation instead;
- advocate: a weak steel-man is a critical finding;
- surface or deep inference depth: different rules on inference chains.

### Step 13: post-critic gap fetch (`skills/hyperresearch-13-gap-fetch.md`)

1. **Select findings** (`:30-33`). The selection rule is three bullets whose AND/OR relation is never stated:
   - `failure_mode` is missing, under-covered or missing-forward-analysis;
   - "`failure_mode` is any width-critic finding";
   - severity is major or critical.
2. **Check the vault** (`:35-39`). For each selected finding, run `{hpr_path} search "<finding topic keywords>" --tag <vault_tag> --json`. Two or more relevant notes means the gap is covered; 0-1 means it is "fetch-worthy".
3. **Cap** (`:41`). `<< p.gap_fetch_cap >>`: 5 at full, 8 at premier, 10 at dissertation (`profiles.py:301,368,410`). Gaps are ranked by severity, then by how many findings they resolve.
4. **Fetch** (`:45-69`). The orchestrator writes 2-3 search queries per gap, collects URLs, and spawns `<< p.gap_fetch_fetchers >>` fetchers (2-4 at full, 3-5 at premier; `profiles.py:302,369`). Each gets the URLs and `extra_tags: ["post-critic-fill"]`. Fetchers follow the step-2 procedure, including the mandatory "Phase 2: Chase primary sources (MANDATORY — do NOT skip)", up to `fetcher_chase_cap` = 8 extra sources each (`hooks.py:3152-3158`, `:3198`).
5. **Update the digest** (`:71`). The orchestrator appends new claims to `temp/evidence-digest.md` under `### Post-critic gap fill`.
6. **Log** (`:73-75`). Results go to `temp/post-critic-fetch-log.md`. Unfilled gaps are flagged "so the patcher knows to acknowledge the limitation rather than fabricate".
7. **Claimed cost.** "small ... near-no-op" (`:84`).

### Step 14: tool-locked patcher (`skills/hyperresearch-14-patcher.md`, agent `hooks.py:1363-1532`)

- **Skip gate (optional).** If `skip-patcher.txt` exists, an inline `python -c` writes a minimal log (`:36-49`).
- **Pre-stub the log** (`:53-63`):
  - The orchestrator first writes the canonical stub `{"total_findings":0,"applied":[],"skipped":[],"conflicts":[],"orchestrator_escalated":[]}` with `echo ... >` (`:58`).
  - The reason: "The patcher is tool-locked to `[Read, Edit]` — it cannot Write. Edit can only modify files that already exist."
- **Spawn once** (`:67-99`). The patcher receives the draft, all four findings paths, the stubbed log and the evidence digest. It also gets `shims/critics.md`, not the polish shim (`:98`).
- **What the patcher agent does:**
  - Model: opus (`profiles.py:62`). Tools: `Read, Edit` (`hooks.py:1374`).
  - "You are the ONE step in the pipeline that modifies the draft's substance" (`:1391`).
  - Invariant (`:1396-1411`): "REVISE SURGICALLY, NEVER REGENERATE". The same passage admits the lock is not mechanical: "The tool lock doesn't prevent this (Edit will accept any old_string/new_string pair that matches exactly); YOU prevent this by sizing edits intentionally."
  - Procedure (`:1443-1482`): merge all findings and sort by severity; send `requires_orchestrator_restructure` findings straight to escalation; spot-check that each finding's `evidence` exists, and skip it if hallucinated; dedupe, preferring the higher severity when findings conflict; make a minimal Edit with `old_string` copied verbatim; match the citation style; fill the log via Edit.
  - Writing rule "Integrate, don't caveat" (`:1492-1523`): scope a claim by the counter-evidence ("X holds in A; in B, Y because Z") rather than append "though this may differ".
- **Orchestrator review** (`:112-125`):
  - A skipped critical is "a pipeline blocker — resolve it yourself before step 15".
  - Look at conflicts and at "patch too large" skips.
  - If the log is still the empty stub, parse the JSON out of the Task result and write it with Bash.
- **Escalations** (`:129-138`). The orchestrator applies H2 moves, renames and insertions by hand-written Edit. It may write "a short evidence-grounded paragraph" for a new heading, and logs the changes in `orchestrator-restructure-log.md`.
- **Constraints** (`:142-146`). The orchestrator must not apply revisions itself in 14.2. It re-spawns once if the patcher returns empty, and never re-runs the patcher on unchanged findings.

### Step 14.5: cite-check (`skills/hyperresearch-14-5-cite-check.md`, `core/citecheck.py`, agent `hooks.py:3471-3554`)

**Mechanical triage**, run by `{hpr_path} citecheck extract <tag> -j`, which writes `cite-check-pairs.json`.

- **Pairing.**
  - Sentences are split by `(?<=[.!?])\s+(?=[A-Z一-鿿])|\n+` (`citecheck.py:30`).
  - `[N]` markers resolve through the `## Sources` section. Each line must match `^\s*\[(\d{1,3})\]\s+(.+)$` (`:31-32,55-57`).
  - The entry's URL must equal `sources.url` exactly. If it doesn't, the fallback is `rest.split("http")[0].strip(" .–-")`, which must equal a note title exactly (`:60-73`).
  - `[[note-id]]` wikilinks resolve against note ids (`:97-99`). Grouped `[7, 12]` markers produce one pair per number (`:93-96`).
- **Auto-pass** (`:114-173`). A pair passes when every number of 2+ characters in the sentence appears somewhere in the cited note's whole concatenated claims blob (claim text, quoted support, numbers). If the sentence has no such numbers, any 6-word shingle found in the blob is enough.
- **Dangling** (`:138-141`). A pair whose note id is None. Step 14.5 turns each one into a critical finding: "Dangling citations are findings immediately ... Each one becomes a `critical` finding" (`14-5:40`).
- **Sampling** (`:176-196`, `14-5:37`). Every "strong" pair is kept, plus 60% of the weak ones.
  - A pair is strong when the sentence contains `%`, `$`, billion, million, increase, decrease, grew or fell, or any digit at all (`:36`, `:105`).

**LLM tier.**

- One Sonnet `hyperresearch-cite-checker` with `Bash, Read, Write` (`hooks.py:3482-3483`); two run in parallel when there are more than about 40 pairs (`14-5:48`).
- Procedure:
  - Read the cited note with `PYTHONIOENCODING=utf-8 {hpr_path} note show <id> -j`, up to 5 ids per call (`hooks.py:3510-3514`).
  - Judge "does the note's content support the sentence AS WRITTEN?": supported, partially-supported, unsupported, or wrong-source. For wrong-source, find the right note with `claims search` (`:3516-3526`).
  - "Judge the SOURCE-SENTENCE binding only" (`:3527-3528`).
  - "Verdicts default SKEPTICAL" (`:3550-3551`).
- Output (`:3530-3546`). A bare JSON array, written only for non-supported verdicts. Critical covers unsupported number-bearing claims and wrong-source; everything else is major.

**Second patcher pass** (`14-5:74-84`).

- The orchestrator appends the dangling findings, pre-stubs `cite-check-patch-log.json`, and spawns one more patcher.
- Fix repertoire: "swap to `correct_note_id`, soften the claim to what the source supports, or delete the sentence when nothing supports it".

**Ordering.** It runs after step 14 and before step 15, so that "polish sees the corrected text" (`14-5:9-10`). The cite-checker gets no register shim: "verification never softens by mode" (`hyperresearch.md:212`, `levers.py:19-20`).

**Probe results.** These came from the standalone copy of `citecheck.py:30-36,105,149-159`:

- "The firm pivoted to cloud services [3]." is **strong**, because the marker digit "3" matches `_NUMBER_RE`. So for `[N]`-style reports every needs-llm pair is sampled, and the 0.6 rate never applies.
- "The firm pivoted to cloud services after the merger [23]." against claims mentioning "fiscal 2023" **auto-passes**. The marker digits "23" are found inside "2023", and nothing semantic is checked.
- "Growth was 12% in 2021 [4]." against "In 2021 the agency hired 12% more staff." **auto-passes**: every number appears somewhere in the note's claims.
- "Firms in the U.S. Department of Energy program, e.g. Acme, grew 5% [2]." splits into "Firms in the U.S." / "Department of Energy program, e.g." / "Acme, grew 5% [2]." The checker then judges a fragment.

`tests/test_core/test_verification.py:93-114` builds pair dicts by hand, so the `strong` computation and the marker-digit leak are not covered by tests.

### Step 15: polish auditor (`skills/hyperresearch-15-polish.md`, agent `hooks.py:1539-1892`)

The step runs for all tiers (`:15`). The orchestrator pre-stubs `polish-log.json` (`:33-35`) and spawns the auditor once with `shims/polish.md` (`:65`). Model: opus. Tools: `Read, Edit` (`hooks.py:1550-1551`).

Checks, in the order the prompt applies them (`:1594-1841`):

1. **Hygiene leaks.**
   - Scaffold-only section headers (canonical list at `hooks.py:105-117`), YAML frontmatter, prompt echoes and preamble lines.
   - Non-verbatim quotation marks: "The ship gate mechanically rejects any quoted span it cannot find verbatim in the vault" (`:1606-1612`).
   - Citation pass-through: citations stay untouched, except that adjacent stacks may be merged into one grouped bracket (`:1613-1618`).
   - Frontmatter field fixes (`:1623-1642`).
2. **Inline pipeline-vocabulary denylist** (`:1644-1695`). Locus N, Tension N, comparisons.md, committed position, cross-locus, width corpus, depth investigation, "per the scaffold", "hyperresearch", `[I\d+]` and `[[interim-*]]`. Each gets a semantic rewrite and counts as a critical fix. The justification: "Audits of past runs found 13 of 15 reports containing at least one of these terms" (`:1649-1651`).
3. **Prompt adherence** (`:1717-1727`). The auditor flags mismatches and escalates format flips; it never invents items.
4. **Filler and meta-discourse** (`:1729-1762`). Filler such as "It is worth noting", "Importantly"; meta-discourse such as "This report examines", "This section maps", "as discussed in section N".
5. **Hedge-striking** (`:1764-1811`). "Data X suggests Y" → "Data X shows Y"; "X tends to cause Y [3][5]" → "X causes Y [3][5]". Hedge-stacks collapse. A hedge stays when "the evidence is absent or weak". This depends on register: off in teach and survey, maximal in advocate (`levers.py:115-139`).
6. **Repetition** (`:1813-1831`). Notably, exec summary vs Opinionated Synthesis: edit the synthesis so it advances the argument.
7. **Readability** (`:1833-1841`). Split sentences over about 50 words and paragraphs over about 200 words.

Rules:

- "Never fabricate content".
- "do not touch the Sources list — it is a product feature" (`:1881`).
- "Net length after polish should be ≤ net length before" (`:1883-1885`); the orchestrator's sanity check rests on the auditor's self-reported `chars_removed` (`15:83`).
- Escalations: the orchestrator has "one shot" to restructure by hand-written Edit, then ships (`15:79-81`).
- Integrity gate: existence `test -f` checks. If an agent fails twice, write a stub (`{"findings":[]}`) and log it (`15:91-107`).
- Lint pre-checks (`15:126-139`): wrapper-report, locus-coverage, scaffold-prompt, patch-surgery. "These four rules are pre-checks. The BINDING gate is `{hpr_path} run finish <vault_tag>`" (`15:140`).

### Step 16: readability audit (`skills/hyperresearch-16-readability-audit.md`, agent `hooks.py:2541-2748`)

- **Why it exists.** It runs for all tiers, because readability is where "small structural changes ... yield outsized scoring gains" (`16:18`). Recommendations are split from application because "an Edit-based reformatter (V7-style) sometimes makes changes that hurt the argument" (`16:22`).
- **Recommender.** Opus, with `Read, Write` (`hooks.py:2553-2554`). It writes up to `readability_rec_cap` recommendations: 50 at full, 60 at premier, 100 at dissertation (`profiles.py:303,370,411`). Each one carries `{id, category, severity, section, current (verbatim anchor), recommended (exact replacement), rationale}` plus a summary (`hooks.py:2658-2689`).
- **Categories and thresholds** (`:2596-2654`):
  - merge-paragraphs: adjacent paragraphs under 300 EN / 200 CJK chars on the same sub-topic; highest priority.
  - break-paragraph: over 1500 EN / 800 CJK chars.
  - make-list: 3+ items in prose.
  - make-table: 3+ entities across 2+ dimensions.
  - bold-keyterms.
  - split-sentence: over 150 EN / 80 CJK chars.
  - remove-hr: every `---`.
  - add-whitespace.
- **Recommender rules** (`:2723-2736`): no substantive additions or deletions; no H2 text changes; never touch the opening thesis paragraph or existing tables. The prompt calls non-ASCII retyping "the #1 failure mode" (`:2718-2719`).
- **Orchestrator.** It applies chosen recommendations with direct Edit calls in the **main context**, ordered remove-hr → merges and breaks → lists and tables → bold → splits → whitespace (`16:131-137`). The heuristics sort recommendations into apply confidently, apply with judgment, apply skeptically and always skip (`16:88-109`). Decisions are logged to `readability-decisions.json`, including `edit_failures` and the measured `net_char_delta_actual` (`16:145-159`).
- **End of pipeline, Claude branch** (`16:178-180`): "Return to the entry skill (`hyperresearch`). Mark all todos complete. Tell the user the final report path. You're done." The Codex branch instead says to run `run finish` first (`16:176`).

### The router's final gate (`skills/hyperresearch.md:249-283`, `core/runs.py:649-879`)

`run finish` runs `verify_run`. If it passes, the manifest is set to done; if not, it is set to `blocked (verify)`. The router allows at most 3 fix rounds (`hyperresearch.md:281`). The fix for a length overrun is "spawn the synthesizer for ONE compression pass ... Do not re-run the critics afterward — go straight back to `run finish`" (`:276`).

What `verify_run` actually checks:

- `report-exists` (`runs.py:669`)
- `decomposition-readable`, only when the file fails to parse (`:675-686`)
- `levers-rendered`, only if levers were declared (`:691-703`)
- `length-in-range`: ±20% of the profile range. The word count is `len(report_text.split())` over the **whole file, Sources list included** (`:705-730`).
- `required-headings`: each heading must appear **as a substring anywhere** in the text (`:732-737`).
- `citation-density`: at least 9 per 1000 words. Every `[N]` group in the **whole file**, Sources list included, is counted, plus wikilinks (`:747-770`).
- `no-scaffold-leak`: only the string "## User Prompt (VERBATIM" (`:772-776`).
- In-process content lints (`:783-806`):
  - `quote-integrity` (error): every quoted span of 5+ words must be an FTS phrase match in **any** vault note body (`lint.py:98,110-147`).
  - `retracted-citations` (error): scans **wikilinks only** (`lint.py:214`).
- Artifact existence: four critic files plus patch-log when the tier includes steps 12 and 14; polish-log when it includes 15 (`:811-820`).
- `cite-check-resolved`, only when step 14.5 is recorded done (`:824`). It passes if the findings file exists and, when there are criticals, `cite-check-patch-log.json` exists (`:834-838`).

---

## 3. Blocking vs advisory

| Rule | Stated where | Enforced by | Blocks ship? |
|---|---|---|---|
| All 4 critic files exist | `12:68`, `15:94-105` | `run finish`, existence only (`runs.py:811-817`) | Yes, but the stubs that 15.4 tells the orchestrator to write satisfy it (`15:107`) |
| Critic files are valid JSON with a findings array | `12:69` | orchestrator | No |
| Instruction critic must run | `12:60` | orchestrator | No |
| Critical critic findings applied | `14:116-119`, `14:153`, `hooks.py:1486-1487,1530-1531` | orchestrator; patch-surgery lint error, a pre-check that is **not** in `run finish` | No |
| Patch log not empty | `14:125`, `14:152` | orchestrator; patch-surgery warning (`lint.py:1273-1296`) | No |
| `orchestrator_escalated` handled | `14:154` | orchestrator | No |
| Dangling citation is critical | `14-5:40` | orchestrator | Only indirectly, via the existence check below |
| Cite-check criticals applied or escalated | `14-5:92` | orchestrator | **No.** The gate checks only that `cite-check-patch-log.json` exists (`runs.py:834-838`), and the orchestrator pre-stubs it before the patcher runs (`14-5:76-80`) |
| cite-check-findings.json exists | `14-5:91` | `run finish` (`runs.py:823-826`) | Only if 14.5 was recorded done (`runs.py:824`) |
| Polish shortens the report | `15:83`, `hooks.py:1883-1885` | orchestrator reads the self-report | No |
| polish-log exists | `15:93` | `run finish` (`runs.py:818-820`) | Yes, existence |
| wrapper-report, locus-coverage, scaffold-prompt, patch-surgery | `15:126-139` | lint pre-checks | No ("pre-checks", `15:140`) |
| quote-integrity | `hyperresearch.md:272,277` | `run finish` (`runs.py:789-804`) | Yes |
| retracted-citations | same | `run finish` | Yes, wikilinks only |
| numeric-consistency | `hyperresearch.md:281` | lint warning | No |
| length ±20%, required headings, density floor, scaffold header | `hyperresearch.md:272` | `run finish` | Yes, but the checks are weak (see section 8) |
| Readability decisions | `16:145-168` | orchestrator | No |
| `run finish` is run at all | `hyperresearch.md:249-283,302` | Claude Code: instruction only, and step 16's last line says "You're done." (`16:178-180`); there is no Claude Stop hook (`hooks.py:3791-3828` installs only a PreToolUse hook). Codex: a Stop hook blocks while the run is `running` and the manifest has a next step (`codex.py:337-386`) | Partly |

---

## 4. Subagent roster

The models are the Claude defaults (`profiles.py:52-64`). Tools come from each agent's frontmatter in `core/hooks.py`. Sizes come from the `ast` parse of the raw templates.

| Agent | Model | Tools | Role | Steps | Prompt size |
|---|---|---|---|---|---|
| hyperresearch-fetcher | sonnet | Bash, Read, Write, WebSearch (`hooks.py:2964-2965`) | Fetch, summarize, extract claims, mandatory primary-source chase (3-8) | 2, 8, 13 | 12.6K chars |
| hyperresearch-source-analyst | sonnet | Bash, Read, Write (`:2768-2769`) | Deep read of one long source | on demand | not measured |
| hyperresearch-loci-analyst | sonnet | Bash, Read, Write (`:141-142`) | Find depth loci | 4 | not measured |
| hyperresearch-depth-investigator | sonnet | Bash, Read, Write, Task (`:347-348`) | Interim note per locus | 5 | not measured |
| hyperresearch-corpus-critic | sonnet | Bash, Read, Write (`:3231-3232`) | Pre-draft gap analysis | 8 | not measured |
| hyperresearch-draft-orchestrator | opus | Bash, Read, Write (`:1911-1912`) | Angle drafts (3x) | 10 | not measured |
| hyperresearch-synthesizer | opus | Read, Write (`:2116-2117`) | Final report, two passes | 11 | 23.6K chars |
| hyperresearch-dialectic-critic | opus | Bash, Read, Write (`:636-637`) | Counter-evidence | 12 | 6.6K |
| hyperresearch-depth-critic | opus | Bash, Read, Write (`:770-771`) | Under-used interim evidence | 12 | 5.5K |
| hyperresearch-width-critic | opus | Bash, Read, Write (`:888-889`) | Coverage gaps and bloat | 12 | 6.9K |
| hyperresearch-instruction-critic | opus | Bash, Read, Write (`:1048-1049`) | Prompt adherence and structure | 12 | 16.2K |
| hyperresearch-patcher | opus | **Read, Edit** (`:1373-1374`) | Applies findings | 14, 14.5 | 8.5K |
| hyperresearch-cite-checker | sonnet | Bash, Read, Write (`:3482-3483`) | Citation binding verdicts | 14.5 | 3.4K |
| hyperresearch-polish-auditor | opus | **Read, Edit** (`:1550-1551`) | Hygiene, filler, hedges | 15 | 17.3K |
| hyperresearch-readability-recommender | opus | Read, Write (`:2553-2554`) | JSON readability suggestions | 16 | 8.0K |
| hyperresearch-browser-fetcher | sonnet | Bash, Read, Write, ToolSearch (`:3357-3358`) | Drives the user's real Chrome for the escalation queue; Claude Code only (`:3632-3633`) | 2.8 | not measured |

How the roster changes on Codex (`core/codex.py`):

- The `model` key is omitted unless `codex_models` sets it, so agents inherit the session model.
- `model_reasoning_effort` is "high" for opus-class roles and "medium" otherwise (`:115-117`).
- Every agent runs with `sandbox_mode = "workspace-write"` (`:261`).
- The tool lists become prose: "Codex cannot enforce that list, so you must." (`:147-149`). README admits it too: "Tool locks are instructions, not enforcement" (`README.md:135`).

Installed prompts and `{{`:

- `_install_instruction_critic_agent` and `_install_readability_reformatter_agent` pass the raw template without `.format()` (`hooks.py:4063-4072`, `:4117`). The install-time render uses `<< >>` Jinja delimiters and does not collapse `{{` (`render.py:50-61`, `hooks.py:55-72`).
- So the installed instruction critic (4 occurrences) and readability recommender (4) keep `{{ ... }}` in their JSON schemas. The dialectic critic and polish auditor are `.format()`ed, so theirs collapse to `{`.
- The comment at `hooks.py:4064-4065` says "the .format() call is harmless", but no `.format()` call is made.

---

## 5. `core/agent_docs.py` and `core/templates.py`

`agent_docs.py` is installer plumbing.

- It writes a marked section (`<!-- hyperresearch:start/end -->`) into CLAUDE.md, or AGENTS.md for Codex, at the vault root (`:299-353`).
- The Claude blurb is about 12.6K characters, roughly 3K tokens, loaded in every session in that project (`:25-205`). The Codex blurb is about 4.2K characters, because Codex caps AGENTS.md at 32 KiB (`:208-265`).
- It names the roster and the tool-lock invariant (`:60-62`), the run commands, the scholar-first search order, OA-substitution caveats and the untrusted-content fence.
- Small facts:
  - The CLI path is rewritten with forward slashes because "bash on Windows eats backslashes" (`:311-312`).
  - The blurb leaves out the date so the prompt cache survives (`:313-314`).
  - The executable is resolved venv-first, including the Windows `Scripts/` layout (`:269-296`).
- It has no direct effect on report quality.

`templates.py` holds six vault note templates (note, concept, reference, guide, comparison, moc) that `note new --template` uses (`cli/note.py:96-114`). The report pipeline does not use them.

- `render_template` is a plain string replace into `title: "{{ title }}"` (`templates.py:10,205`), so a title containing `"` breaks the YAML.
- The template path in `note.py` drops body, summary and source, and builds ids with accumulating suffixes (`note.py:107-112`).
- None of this matters for report quality.

---

## 6. Cost model

No per-step telemetry for steps 12-16 is stored in the repo. Every figure below is a structural estimate, not a measurement. The full gear quotes "~1.5–2.5 hours" end to end (`profiles.py:306`); the sample report says "Wall-clock: ~2 hours" (`example-reports/rl-exploration-trajectory-planning.md:5`).

**Spawns in steps 12-16 at the full tier:** 9-14 in total. 8 of them are Opus by default (4 critics, 1-2 patchers, polish, recommender); the fetchers and cite-checkers are Sonnet.

| Step | Spawns |
|---|---|
| 12 | 4 critics |
| 13 | 0-4 fetchers |
| 14 | 1 patcher |
| 14.5 | 1-2 cite-checkers and 0-1 patcher |
| 15 | 1 polish auditor |
| 16 | 1 recommender |

**What drives the context load:**

- **Critics.**
  - Each reads the full report (5-10K words argumentative at full, 8-16K at premier; `profiles.py:291,364`).
  - The vault searches are heavy. `search --json` **automatically includes full note bodies** for up to 20 results: "Auto-include body in JSON mode" (`cli/search.py:176-186`, `config.py:229`). One dialectic or width search can pull tens of thousands of tokens.
  - The depth critic reads every interim note: up to 6 at full, 10 at premier (`profiles.py:275,348`).
- **Gap fetch.** The vault check runs in the **orchestrator's own context**, so with the same `--json` default each fetch-worthy candidate can dump up to 20 bodies into the main context. Each fetcher must also chase up to 8 primary sources (`hooks.py:3154,3198`), so the claim "near-no-op" (`13:84`) is optimistic whenever any gap fires.
- **Patcher.** It reads up to 49 findings (12+12+10+15 at full; 64 at premier, 98 at dissertation; `profiles.py:300,367,409`), the report and the evidence digest (80-120 claims with quotes at full). Each applied finding costs at least one Edit turn.
- **Cite-check.**
  - The Python triage is cheap.
  - Because of the marker-digit bug, every `[N]`-cited pair that misses auto-pass is sent to the LLM. One or two Sonnet checkers each read full note bodies, 5 ids per call.
  - The 11K-word sample report has 252 `[N]` groups and 97 sources, so the LLM tier can plausibly reach a three-digit number of pairs split across only 2 checkers (`14-5:48`).
  - A second Opus patcher pass follows.
- **Polish.** One Opus pass over the report with many small Edits.
- **Readability.** The Opus recommender writes up to 50 recommendations, each carrying full `current` and `recommended` text (often whole paragraphs or tables). The orchestrator then applies them by Edit calls **in the main context**, late in a multi-hour session.
- **Always-on cost.** The CLAUDE.md blurb adds about 3K tokens to every session in the project.

---

## 7. What drives quality, in my assessment

1. **Instruction critic.** It is the most clearly targeted lever. It checks the verbatim query's named entities, sub-questions and format cues, plus the H2 order the prompt implies, and routes structural fixes to an agent with Write access (`hooks.py:1092-1144`, `14:129-138`). The authors call this "the dimension with the widest variance" (`12:60`). The repo contains no ablation.
2. **Depth and dialectic critics, plus integrate-by-scoping.** They pull evidence the pipeline already paid for (interim-note numbers, mechanisms, counter-positions) back into the report as scoped claims instead of hedges (`hooks.py:830-837`, `:1492-1523`). This is plausibly real "insight" gain. There is no measurement.
3. **Polish hygiene and meta-discourse stripping.** This is valuable, but the problem is partly self-inflicted: the leaks come from the pipeline's own vocabulary (Locus N, Tension N, comparisons.md). The authors measured "13 of 15 reports" with inline leaks (`hooks.py:1649-1651`).
4. **Quote-integrity in the ship gate.** It is the only content check that is mechanical and actually blocks (`runs.py:783-806`). A code comment says bench Q62 "shipped with 24 hallucinated-quote errors" before this was folded into the gate (`runs.py:779-782`).
5. **Cite-check.** Correct in intent, and the only binding check at the claim level (FACT), but undermined by its triage bugs, its existence-only gate, and the edits that come after it (section 8).
6. **Readability audit.** Unclear. The authors claim "outsized scoring gains" (`16:18`) and tie readability to RACE (`hooks.py:1244`), with no data in the repo.
7. **Benchmark tuning.** Several rules are tuned to a RACE judge on a few queries:
   - the bloat KB thresholds (`hooks.py:991-993`);
   - "+2.5 RACE from register alone" on Q62 (`CHANGELOG.md:194`);
   - pedagogy primers from "a four-report comparison on bench Q62" (`CHANGELOG.md:211`).

   They may not generalize. The only published sample scores 58.3/100 RACE (`example-reports/...:5`).

---

## 8. Weaknesses (ranked)

### High

1. **The cite-check auto-pass is leaky.**
   - Citation marker digits count as sentence numbers, and numbers are matched against the whole note's claims blob (`citecheck.py:104-105,149-151`).
   - Probe: "pivoted to cloud services [23]" passes because the note mentions 2023. "Growth was 12% in 2021 [4]" passes against an unrelated "hired 12% more staff in 2021".
   - The sentence-level FACT check silently approves unsupported sentences, and the README's "Every citation is verified" (`README.md:54`) overstates it.
2. **The ship gate does not verify that criticals were fixed.**
   - `cite-check-resolved` passes as soon as `cite-check-patch-log.json` exists (`runs.py:834-838`), and the orchestrator pre-stubs that file before the patcher runs (`14-5:76-80`).
   - Critic files and patch logs are existence-checked only, and 15.4 tells the orchestrator to write stubs when an agent fails twice (`15:107`).
   - patch-surgery (critical-skipped) is a non-binding pre-check (`15:140`, `runs.py:783-806`).
   - In short, no critic or cite-check finding mechanically blocks shipping.
3. **Claims change after verification and are never re-checked.**
   - Polish runs after 14.5 and strips hedges: "X tends to cause Y [3][5]" → "X causes Y [3][5]" (`hooks.py:1791-1793`). The polish auditor cannot read sources (Read/Edit, report only), so its test "if the same paragraph provides evidence" (`:1806-1811`) amounts to "a citation is present".
   - Step 16 merges and splits sentences and builds lists after cite-check (`16:131-137`).
   - The length fix at the gate re-runs the **synthesizer** after every check (`hyperresearch.md:276`).
   - None of these re-runs cite-check. Calibration can degrade after the binding check, and citations can drift from the sentences they were checked against.
4. **Cite-check sits outside the step machinery.**
   - Profile `steps` are integers 1-16 (`profiles.py:123,240-241`). `profile_steps` copies them (`runs.py:139`). `resume_position` walks only those (`runs.py:469-505`), so after step 14 `run resume` points to step 15.
   - The router seeds "todos for all 16 step skill invocations using the integer step numbers" (`hyperresearch.md:163-166`).
   - The gate checks cite-check only if 14.5 was recorded done (`runs.py:824`).
   - After a context compaction, or with an orchestrator that just follows `run resume`, the only step-level FACT check is skipped and the gate never notices.

### Medium

5. **Dangling false positives can delete valid content.**
   - `[N]` resolution needs an exact URL match. The fallback is an exact title match on `rest.split("http")[0]` (`citecheck.py:60-73`), but the synthesizer's Sources format is `[1] Author(s). "Title." *Publication*, Year. URL` (`hooks.py:2394`), which can never equal a note title.
   - Any URL drift therefore makes the citation "dangling", which is an automatic critical finding (`14-5:40`), and the fix repertoire includes "delete the sentence" (`14-5:82`). This failure is plausible from the code; I did not see it in a run.
6. **Unmapped `[N]` markers are never checked.**
   - A body `[N]` with no parseable Sources line is silently dropped: `if num in numbered_map:` (`citecheck.py:95`).
   - Sources lines formatted as `- [1] ...` or `1. ...` do not match `^\s*\[(\d{1,3})\]\s+` (`:31,55-57`), so the whole cite-check passes empty.
   - The patcher is never told to add Sources entries for new gap-fill citations (`hooks.py:1477-1480`).
7. **The citation-density floor is close to vacuous for `[N]` style.** The gate counts every `[N]` group in the whole file, the Sources list included (`runs.py:747-750`), while the instruction critic counts body citations only (`hooks.py:1259-1261`). Ninety-seven Sources lines in an 11K-word report already supply about 9 per 1000 words. The word count also includes Sources (`runs.py:725`), pushing reports toward the length ceiling.
8. **There is no per-hunk cap.**
   - README: "Per-hunk caps make "just rewrite it" mechanically impossible" (`README.md:206`).
   - The patcher prompt: "Edit will accept any old_string/new_string pair that matches exactly; YOU prevent this by sizing edits intentionally" (`hooks.py:1408-1411`).
   - The old 500-char cap (`CHANGELOG.md:395`) is gone. `grep` finds no hunk cap in `src`.
9. **The tool locks protect against the wrong thing.**
   - Critics are told "You do NOT have Edit tools. You cannot modify the draft." (`hooks.py:654-655`), yet they hold Write and Bash (`:637`) and could overwrite it.
   - The recommender is "Tool-locked to [Read, Write] — cannot Edit" (`hooks.py:2551`, `16:56-57`), but Write can replace the report wholesale.
   - The patcher's Edit can modify any existing file, CLAUDE.md and `.claude/settings.json` included. It also reads raw note files, which bypass the untrusted-source fence (`agent_docs.py:161-163`). That is a small but real prompt-injection surface.
   - On Codex every lock is prose (`codex.py:147-149`).
10. **The gap-fetch trigger is ill-defined.** It filters on `failure_mode` (`13:30-33`), but only the instruction critic emits that field. The width critic's fields are `severity, location, issue, evidence, recommendation` (`hooks.py:971-973`), and "failure_mode is any width-critic finding" cannot be evaluated. Selection is left to orchestrator judgment.
11. **The handoff from gap fetch to patcher is broken.** Unfilled gaps are flagged "so the patcher knows to acknowledge the limitation rather than fabricate" (`13:75`), but `post-critic-fetch-log.md` is not among the patcher's inputs (`14:87-96`, `hooks.py:1420-1441`). Gap-fill claims are also never `claims ingest`ed; only step 2 runs that command (`skills/hyperresearch-2-width-sweep.md:229`). So the cite-check triage and the cite-checker's `claims search` cannot see them (`citecheck.py:127-130`).
12. **Gap-fetch context blowup.** The vault check `search ... --json` returns up to 20 full bodies (`13:37`, `cli/search.py:176-186`, `config.py:229`), into the orchestrator's context, once per candidate finding.
13. **Claude Code can skip the final gate.** Step 16's Claude branch ends with "You're done." (`16:178-180`), and Claude has no Stop hook (`hooks.py:3791-3828`). The `run finish` instruction lives only in the router (`hyperresearch.md:249-283`), which is older context by step 16.
14. **The cite-checker does not scale.** At most two checkers run (`14-5:48`), each reading full bodies per pair, and every `[N]` pair counts as strong. On long reports the context and cost grow with the citation count, and the 0.6 sample rate never applies.
15. **Retraction and quote checks are partial.**
    - `retracted-citations` scans wikilinks only (`lint.py:214`), so inline-style reports (the benchmark and public-deliverable style) are never checked.
    - `quote-integrity` accepts a quote found in **any** vault note, only checks quotes of 5+ words, and only double quotes (`lint.py:98,110-147`). A misattributed quote passes.
16. **There is no path for a wrong thesis.** Critics may report "the draft picks the wrong thesis given the evidence" as an orchestrator concern (`hooks.py:751-754`), but step 12 says "Do not read the findings yourself" (`12:62`), and step 14.4 handles only `orchestrator_escalated` H2 entries (`14:129-138`). The architecture cannot recover a wrong thesis after step 11.
17. **Critic pressure is mostly additive and collides with the length gate.**
    - Instruction critic R1-R6 add primers, definitions, tables and forward analysis (`hooks.py:1250-1311`).
    - The depth critic asks to "develop it to the depth the interim note supports" (`:836-837`).
    - The patcher mostly inserts (`:1475-1476`).
    - Bloat gets only 2 findings (`:1018`), and the gate's length ceiling triggers a synthesizer rewrite (`hyperresearch.md:276`).
    - This growth-then-regenerate loop is plausible from the rules; I did not measure it.
18. **The Sources list is untouchable and unvalidated.** Polish must "not touch the Sources list" (`hooks.py:1881`), and nothing validates titles. The shipped sample has at least 13 of 97 titles truncated, e.g. "[2] Exploration in Deep Reinforcement Learning: A." (`example-reports/...:275`), plus `:287`, `:293`, `:297`. The root cause is probably title extraction upstream.

### Low

19. **Doubled braces in installed prompts.** The instruction-critic and readability-recommender installs keep `{{`/`}}` in their JSON schemas (`hooks.py:4064-4066,4117`). Step 16.1 asks for "a JSON array" (`16:66`), while the schema is an object (`hooks.py:2661-2688`).
20. **patch-surgery is fragile and misdescribed.** It detects a critical skip by `e.get("severity") == "critical"` inside `skipped` entries (`lint.py:1222-1226`), but the patcher prompt never defines an entry schema (`hooks.py:1481-1482`). Step 15 describes the rule as "draft churn ... exceeds the safety threshold" (`15:138`); no churn is measured (`lint.py:1201-1296`).
21. **Stale and inconsistent prompt text.**
    - Agents call themselves "Layer 5/6/7 of the 7-phase pipeline" while the spawn prompt says step 12 of V8 (`hooks.py:648,1385,1561`).
    - "revisor" vs patcher.
    - The recommender comment says "Tool-locked to [Read, Edit]" (`hooks.py:2536-2537`).
    - "merged draft from step 10" (`12:24`).
    - "(full tier only)" on two of the four findings paths (`14:90-91`).
    - The polish shim references a "one-kicker-per-section budget" (`levers.py:117-118`) that exists only in the synthesizer prompt (`hooks.py:2442`).
22. **Windows fragility.**
    - Bash-only snippets in skill prose: `echo '...' > patch-log.json` (`14:58`, `15:34`) and `for f in ...; test -f` (`15:96-105`).
    - `python -c` with `pathlib.Path(f).read_text()` in the locale encoding (`14:41-46`).
    - `PYTHONIOENCODING=utf-8 {hpr_path} ...` prefixes (`hooks.py:3512`, `:3044-3047`), which are a parse error in PowerShell. Codex on Windows uses PowerShell (`codex.py:127-128`).
    - lint reads the patch log as `utf-8`, not `utf-8-sig` (`lint.py:1209`). A PowerShell-written stub with a BOM would show up as "not valid JSON". This is plausible; I did not reproduce it.
23. **The sentence splitter breaks on abbreviations** ("U.S. Department", "e.g. Acme"; `citecheck.py:30`, probe), so the checker judges fragments.
24. **Benchmark-specific constants are baked into prompts:** KB thresholds and RACE references (`hooks.py:991-993,1244`, `16:18`).

---

## 9. Ideas for vafer-research

- Adopt a dedicated prompt-adherence critic: diff the report against the verbatim question's named entities, sub-questions and format cues. Check heading order mechanically and use the model only for semantic coverage.
- Adopt findings-only critics with `location / issue / evidence / recommendation` and per-critic caps (about 10-15) so the load-bearing findings are not buried.
- Adopt the depth critic's "developed quantitative mechanism compressed to a bare mention" check. It is cheap and targets insight directly.
- Adopt "integrate by scoping, don't append caveats" as a writing rule for VAFER's "Where sources disagree".
- Keep VAFER's verify-last rule ("Nothing else runs after the report"). Avoid hyperresearch's post-verification hedge-stripping and readability edits; if anything edits after verification, re-verify only the sentences it touched.
- Avoid hedge removal keyed to the presence of a citation. Match claim strength to the source wording that was checked.
- Adapt cite-check pairing, fixed:
  - strip markers before extracting numbers;
  - match numbers within the same claim or quote, not the whole note;
  - treat an unresolvable `[n]` as a hard error instead of dropping it;
  - resolve citations by URL normalization, not exact string match.
- Adopt a mechanical quote check: every quoted span must appear in the saved note for the **cited** source. VAFER notes already store verbatim quotes of 30 words or less, so a script can grep them.
- Adopt a hard check that every `[n]` maps to a sources-list entry with an opened URL, and that every entry is cited at least once. Count density on the body only.
- Avoid gates that check whether files exist. Check content: every critical finding id must have an applied, rejected-with-reason or escalated record.
- Avoid tool locks as the safety story. They hold on one host only and protect against the wrong failure. Make correctness rest on checks that run after the edit (diff size, verified-sentence set).
- Avoid search calls that dump full bodies into the orchestrator. Keep notes as summaries plus quotes, and load bodies on demand in subagents.
- When a gap wave fails, the "Not established (queries tried)" line must reach the writer. hyperresearch's fetch log never reaches its patcher.
- Fix length before verification, never by a full regeneration after it.
- Adapt register levers (teach / survey / analyze / advocate) to set what reviewers count as a defect. It is cheap, and the authors claim +2.5 RACE from register alone on one query.
- Adapt the readability pass as a mechanical lint (paragraph and sentence length, a table for comparisons of 3+ entities across 2+ dimensions, no horizontal rules), applied by the single writer before verification.
- Avoid leaking internal pipeline vocabulary into prose to begin with, instead of paying a polish pass to remove it. Give the writer reader-facing labels and grep a short denylist.
- Avoid bash-only snippets in skill prose (`echo >` stubs, `VAR=x cmd`, `python -c` without `encoding=`). Give shell-neutral instructions or both syntaxes.
- Validate the sources list too (no truncated titles, URL present, access date). hyperresearch ships truncated titles because the Sources list is off-limits to polish.

---

## 10. Key claims for independent check

1. The cite-check mechanical triage auto-passes sentences on number substrings. The citation marker's own digits count, and they are matched against the cited note's whole claims blob, so a non-numeric sentence citing `[23]` passes when "23" appears anywhere in that note's claims (e.g. "2023"). Every `[N]` sentence is flagged strong, so the 0.6 sample rate never applies to inline style. Evidence: `core/citecheck.py:33,36,104-105,149-151,190-192`; scratchpad probe output.
2. `run finish` does not verify that critical findings were applied. `cite-check-resolved` requires only that `cite-check-patch-log.json` exists, which the orchestrator pre-stubs before the patcher runs. Critic and patch artifacts are existence-checked. patch-surgery is not part of the gate. Evidence: `core/runs.py:783-842`; `skills/hyperresearch-14-5-cite-check.md:76-80`; `skills/hyperresearch-15-polish.md:107,126-140`.
3. Claim-strength edits happen after the cite-check and are never re-verified: polish hedge-stripping ("X tends to cause Y [3][5]" → "X causes Y [3][5]"), step 16 merges and splits, and the length-fix synthesizer respawn. Evidence: `core/hooks.py:1781-1811`; `skills/hyperresearch-14-5-cite-check.md:9-10`; `skills/hyperresearch-16-readability-audit.md:131-137`; `skills/hyperresearch.md:276`; `core/runs.py:822-842`.
4. Step 14.5 is not in any profile's step list. `run resume` goes from 14 to 15, the Codex Stop hook ignores 14.5, and `verify_run` checks cite-check only if 14.5 was recorded done. Evidence: `core/profiles.py:123,236-244`; `core/runs.py:139,469-505,824`; `core/codex.py:373-375`.
5. The "tool lock" blocks Write and Bash for the patcher and polish auditor on Claude Code only. It does not limit edit size (no per-hunk cap exists, despite README). The read-only critics and the recommender hold Write. On Codex all locks are prose. Evidence: `core/hooks.py:637,654-655,1374,1408-1411,1551,2551-2554`; `README.md:135,206`; `core/codex.py:140-149`; `CHANGELOG.md:395`.
6. The gap fetch selects findings by a `failure_mode` field that only the instruction critic emits. Its "unfilled gap" signal is logged to a file the patcher never receives. Its vault check pulls up to 20 full note bodies per search into the orchestrator. Evidence: `skills/hyperresearch-13-gap-fetch.md:30-39,73-75`; `core/hooks.py:971-973,1420-1441`; `skills/hyperresearch-14-patcher.md:87-96`; `cli/search.py:176-186`; `core/config.py:229`.

## 11. Not verified or uncertain

- I did not run the pipeline, so all costs and timings are structural estimates.
- I did not check whether `sources.url` stores the requested or the redirected URL, which decides how often dangling false positives happen. `agent_docs.py:107-108` says `source:` is the requested URL.
- The sample report may predate the meta-discourse and calm-citation rules (`CHANGELOG.md:212-213`). Its surviving "The rest of the report builds the case." (`example-reports/...:23`) is weak evidence that polish misses such sentences.
- The BOM and PowerShell failure of the stub logs is inferred from the code (`lint.py:1209`), not reproduced.
