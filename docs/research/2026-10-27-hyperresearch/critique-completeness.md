# Critique of the hyperresearch teardown: completeness

Date: 2026-10-28. Lens: what `teardown.md` leaves out or underweights, about hyperresearch (HR) or from our own earlier research. Only gaps that would change the opportunity list (§5) or its order are counted.

Inputs: the nine `read-*.md` notes; `verified-claims.md` and the two new verdict sets (cite-check and claims; vault, search and MCP); `skills/vafer-research/` 0.1.0-alpha; the v0.1 design spec; `docs/research/2026-10-27-deep-research-sota/verdict.json`; and the Codex observation (more complete and current than bare Codex, 1.5–2× slower, depth varied between runs). "Spot-checked" means re-read in the HR clone at 327498b for this critique. Teardown line numbers refer to `teardown.md` as it stands.

**Verdict.** The HR side is thorough, but §5 is not. Its top opportunity repeats two of HR's verified mistakes: checking against unverified LLM-written text, and a binding check with no precision bar. "5×" is measured against the weakest baselines, and the comparator our own research named (Claude Code's `/deep-research`) is missing. Writing quality, derived numbers and high-stakes penalties have no item.

## What already holds

§1–§3 match the verified record, and most corrections from the two new verdict sets are applied: 125 of 155 own-index pairs, reads also failing under lock contention, and no repeat of the refuted "1.10–1.20 spread". The gaps are almost all in how HR's lessons are carried into §2's driver list and into §5.

## Issues, most severe first

### 1. High: item 1 checks the report against unverified, LLM-written quotes

- **Where:** §5 item 1 (line 93); §3's triage bullet (line 59).
- **Gap:** The teardown omits a confirmed HR weakness. Cite-check triage judges support against fetcher-written `quoted_support` that no code ever compares with the page, and numeric-consistency has the same blind spot. Item 1 repeats it. It checks the report "against the saved quote or page", but:
  - our saved quotes are written by researchers;
  - on Claude Code they reach researchers through WebFetch, which returns a model-written extract;
  - our run folder keeps no page text in M1;
  - Codex's default sandbox has no shell network to fetch the page. The teardown notes this for item 11 (line 103) but not for item 1.

  So item 1 measures report-vs-notes drift, not "absent from the cited page". Its 5× claim and the "driven near zero" sentence (lines 91, 93) fail on Codex, the host where we observed the skill.
- **Evidence:** new verdict set, "Triage judges support against unverified LLM-extracted claims", confirmed (`citecheck.py:144-147`, `claims.py:133`, numeric-consistency at `lint.py:160-176`). `verified-claims.md`, pipeline-middle, missed item 2: digest quotes are unverified LLM text presented as verbatim. `references/hosts.md:8`: WebFetch "returns a model-written extract of the page, not the raw page". `hosts.md:18`: no shell network under workspace-write. Spec §9.6: raw page archiving off in M1. `verdict.json` helper_scope: on Codex with the network off, the check "is skipped silently" and the method line says "host-view only".
- **Fix:** Split item 1 in two.
  - (a) A report-vs-notes drift check on every host.
  - (b) Note-vs-page verification at note time. On Codex, use find_in_page over the verbatim line windows researchers already read. On Claude Code, ask WebFetch for the exact sentence or NOT FOUND, or use curl when allowed. Mark each note quote verified or unverified. This was the verification reader's own proposal (`read-verification.md` §8), and the teardown dropped it.

  Restate the 5× claim per host. On Codex, item 2 becomes the only check that reads page text, so rank it level with item 1 there.

### 2. High: item 1 makes a mechanical verdict binding without a precision bar

- **Where:** §5 item 1, "the lead may not re-interpret its verdict (HR's Q62 lesson)" (line 93); items 2 and 3 (lines 94–95).
- **Gap:** The teardown leaves out the false-positive record of HR's mechanical checks.
  - Q62 is a mixed lesson. The quote regex then in use was later shown to have turned "38 legitimate short quotes into 42 false errors", so the "false positives" memo may have been partly right.
  - Exact URL matching turns a trailing slash or a closing parenthesis into a false "dangling" critical finding. One of the listed remedies for that finding is deleting the sentence.
  - The skeptical cite-checker can return false "unsupported" verdicts when it reads truncated long bodies (plausible, not measured).
  - Triage writes no record of what it passed, so its precision cannot be measured.

  Our earlier design made `check` advisory and set a precision bar. The teardown reverses that without saying so. A noisy check, a no-reinterpretation rule and two fix rounds together will soften or delete correct sentences and add time, on the top-ranked item.
- **Evidence:** CHANGELOG.md:20 (spot-checked). `verified-claims.md`, claims-history claim 5 and missed item 3; pipeline-back missed item 2 (trailing-slash dangling; remedies include deletion, `14-5-cite-check.md:82`). Verification probe 4 (URL ending in `)` goes dangling). `read-verification.md` weakness 15. New verdict set, missed item 2 (no audit trail). `verdict.json` helper_scope: `check` "always exits 0, and its misses feed the verifier's trigger list". Spec §7 M2: warning precision ≥80%. `verdict.json` risks: the verifier "flips correct claims", mitigated by auditing 30–50 verdicts.
- **Fix:**
  - Keep item 1 advisory until a logged audit shows at least 80% precision.
  - Log every verdict, passes included.
  - In item 3, normalize URLs (scheme, `www`, trailing slash, `utm_*`, fragments).
  - The default remedy is "fix, or mark unverified", never "delete".
  - Adopt the no-reinterpretation rule only after the audit passes.

### 3. High: the comparator set omits `/deep-research` and Claude Research

- **Where:** §5 intro (line 91); item 16's arms (line 108); the DRACO paragraph (line 69).
- **Gap:** Our earlier research says the real competitor on Claude Code is the bundled `/deep-research` workflow, not bare chat. That workflow already cross-checks sources, votes on each claim, filters failed claims and lists unchecked ones as unverified. That is the territory of items 1–3 and 6. The teardown's own DRACO analysis puts hosted HR Deep roughly level with Claude Research, yet neither appears as a comparator in §5. The reader notes also hold market points that §5 ignores: Perplexity DR averaged 245 s at 70.5 on DRACO, and API deep-research systems cost $0.45–5.5 per query (reader-reported, not re-verified).

  §5's "credible" 5× axes (time, searches per follow-up, cost per verified claim) beat HR's hours and ~$215 runs, the weakest baseline available. Against `/deep-research` or commercial deep research, the time axis is minutes, and the claim-check axis may already be covered on Claude Code.
- **Evidence:** spec §2 conclusion ("Claude Code'da gerçek rakip `/deep-research`"), §4.7 and open decision 3. `verdict.json` claim 5, confirmed: it "fans out searches, fetches and cross-checks sources, votes on each claim, filters out failed claims and lists claims it could not check as unverified". `hosts.md:11`. Teardown line 69 ("roughly level with Claude Research"). `read-claims-history.md` §10.
- **Fix:** Add `/deep-research` on Claude Code as an arm in item 16 (it is the spec's arm D). Restate each 5× claim against the best comparator per host. Keep the spec's rule: if `/deep-research` wins one-off reports on Claude Code, VAFER's case there rests on reuse, Plan integration, follow-ups and Codex.

### 4. Medium: derived figures and table cells break item 1's number rule

- **Where:** §5 item 1 (line 93); §2 driver 1 (line 24), which cites the sample report only for its source count.
- **Gap:** The sample report contains a derived number that passed every HR gate: "152.68% ... versus DreamerV3's 97.45% — a 55% relative improvement". The inputs give +56.7% relative, or +55.2 points. No HR gate checks derived arithmetic, and neither would item 1.

  Our main use case is full of derived figures. The three-country electricity question needs currency conversions, per-kWh prices and tax-inclusive totals. Item 1 requires every number to appear in the cited quote or page, and a derived figure never does. So the check either flags every legitimate calculation, or exempts them all and checks none.

  Table cells have a similar problem. Our rule 5 sends researchers to tariff tables, and a 30-word quote rarely captures a cell together with its header, unit and period. HR's PDF lane extracts no tables and does no OCR. HR also files "wrong magnitude" as partially-supported, so it is only "major".
- **Evidence:** example report line 48 (spot-checked); `read-claims-history.md` §8 and §12 item 5. `SKILL.md:55` ("tariff table"). `read-acquisition.md` §4 (`web/pdf.py:186-204`). `read-verification.md` weakness 10 (`hooks.py:3519-3521, 3545`).
- **Fix:**
  - In item 1, exempt only numbers marked as derived. Each must show its inputs, with [n], and the operation, and the script recomputes it.
  - Quote a table value as the row, the column header, the unit and the period.
  - In item 2, treat any mismatch in number, unit, date or magnitude as critical, whatever the verdict label.

### 5. Medium: the 5× metrics reward writing fewer quotes, numbers and citations

- **Where:** §5 items 1 and 3 (lines 93, 95); line 91.
- **Gap:** HR never checks uncited sentences. Pairs exist only for sentences with a marker, and the density gate counts citations, not coverage. The teardown omits this. Its 5× metrics are miss counts per report ("quotes and numbers absent from the cited page", "dangling citations"). Both fall to zero if the writer stops quoting or citing.

  Our spec forbids this: the co-primary metric S must not fall, and inflating the rate by writing fewer claims counts as gaming. The earlier helper design also flagged "factual paragraphs that contain numbers but no citation", and the teardown's item 1 drops that flag.
- **Evidence:** `read-verification.md` weakness 11 (`citecheck.py:100`, `runs.py:747-770`). Spec §6, metric S ("az iddia yazarak oranı şişirmek oyun sayılır"). `verdict.json` helper_scope.
- **Fix:** Add the uncited-number flag to item 1. Report every 5× rate together with the count of supported claims, as spec §6 does.

### 6. Medium: no opportunity addresses the writing itself

- **Where:** §2 driver 4 (line 27), compared with §5 (lines 93–108).
- **Gap:** The teardown calls HR's fresh single writer "where the prose is made". DRACO gives 22% of its weight to breadth and depth and 14% to presentation. Yet no item in §5 touches writing.

  The readers list writer rules that are not benchmark tricks:
  - state each idea and each piece of evidence once (a redundancy pass);
  - "choose which sources to cite for a point, never which points to make";
  - put coverage and mechanism depth before elegance;
  - use a table when 3 or more entities are compared on 2 or more dimensions;
  - flag a "developed quantitative mechanism compressed to a bare mention" (from the depth critic);
  - scope a claim by its counter-evidence instead of appending caveats.

  SKILL.md's five writing rules include none of these.
- **Evidence:** teardown line 27. `read-claims-history.md` §1.2 (rubric shares). `read-pipeline-middle.md` §8–9 (`hooks.py:2278-2343`). `read-pipeline-back.md` §9 (`hooks.py:830-837, 1492-1523`). `SKILL.md:60-66`.
- **Fix:** Add one word-budgeted writing item with three or four of these rules. State why the RACE-tuned rules (primers, citation-count targets, KB thresholds) stay out.

### 7. Medium: the sample report's output defects are missing

- **Where:** §2 driver 1 (line 24); §3 (lines 45–65); item 3 (line 95).
- **Gap:** The only full OSS report in the repo is cited for "97 sources, 87 on arXiv" and its RACE score. The reader's audit of it found:
  - 38 of 97 bibliography titles broken: 21 are PDF page-header junk (for example "[18] Published as a conference paper at ICLR 2020" and "[87] ©2023 IEEE. Personal use of this material is permitted...") and 17 are truncated (for example "[8] Curiosity in Hindsight:");
  - pipeline vocabulary in reader prose ("corpus" 16 times);
  - uncited general knowledge, admitted in the text;
  - an overgeneralized thesis;
  - the derived-number error in issue 4.

  HR's polish auditor exists because "13 of 15 reports" leaked pipeline terms. Its Sources list is off-limits to polish, so broken titles ship.

  These are the cheapest defects to beat, and our design has the same exposure. Step 4 writes `[GAP]` markers and priors into `report.md`. Plan rows use COVERED, PARTIAL, OPEN and NOT-FOUND. Titles come through WebFetch extracts.
- **Evidence:** `read-claims-history.md` §8. Example report lines 287, 307, 347, 417 and 445, plus the "corpus" count (spot-checked). `read-pipeline-back.md` weakness 18 (`hooks.py:1649-1651, 1881`). `SKILL.md:42`.
- **Fix:** Extend item 3's mechanical check. Every source needs a real title, not a PDF header line, an arXiv stamp or a copyright line. The delivered report contains no internal labels: `[GAP]`, `[prior]`, row statuses, "researcher", "wave", "notes". Uncited general-knowledge sentences are marked as inference.

### 8. Medium: DRACO's scoring structure is not turned into opportunities

- **Where:** the DRACO paragraph (line 69); §5.
- **Gap:** The teardown reports that Medicine, "where penalties reach −500", supplies 75% of HR's margin over Claude Research, but draws no lesson from it.
  - The verified correction rules out grading noise: the 35.1-point Medicine gap is far outside the page's 9-point re-grade spread. Medicine is where DRACO's −50 to −500 penalties live. So the largest single swing on the board most likely came from a safety penalty, not from breadth (inference; the page does not say).
  - About half of DRACO's rubric criteria test factual accuracy, and 12% test citation quality. ChatGPT and Gemini lost points just for missing links.
  - The DRACO paper notes that "longer outputs do not necessarily achieve higher performance".
  - Our own S1 tasks carry 3–5 negative items each.
- **Evidence:** `verified-claims.md`, claims-history claim 2 (penalty quote from arXiv 2602.11685 and the re-grade correction). `read-claims-history.md` §1.2, §10 and §12 item 2. Spec §6 (S1).
- **Fix:**
  - Add a small high-stakes item. For medical, legal, financial or safety questions, state the scope, conditions and contraindications next to any recommendation, and never present a dangerous or jurisdiction-wrong instruction as advice.
  - Raise item 3, since resolvable links score directly.
  - Keep length out of every gate; item 15 already says so.

### 9. Medium: drivers 3 and 4 rest on handoffs HR's own pipeline breaks

- **Where:** §2 drivers 3 and 4 (lines 26–27); items 9 and 10 (lines 101–102), whose evidence is "HR design".
- **Gap:** The teardown leaves out these verified or spot-checked breaks:
  - Step 4 drops each locus's `corpus_evidence` and `opposing_positions` before step 5. Investigators can start without their seed notes or the two sides; some note ids survive only in the rationale prose.
  - Step 7 promises that "every tension named here becomes a subsection in the final report". No drafter or synthesizer prompt asks for it.
  - Step 8 treats a failed counter-search as support ("the committed position gains confidence"). It writes downgrades only to `comparisons.md`, not to the interim notes the drafters read in full.
  - The synthesizer prompt never reads `synthesis-conflicts.md`, the only source-checked artifact of step 11. Only the spawn template passes its path. So the "source-checked verdicts on cross-draft conflicts" in driver 4 reach the writer only as one-line plan entries.

  Drivers 3 and 4 are designed but only partly delivered, which weakens the only evidence for items 9 and 10. §5 also misses the lesson that transfers: every artifact needs a named consumer.
- **Evidence:** `verified-claims.md`, pipeline-middle claim 3 (confirmed) and missed items 1 and 4. `7-source-tensions.md:84` (no consumer in `src/`, spot-checked). `8-corpus-critic.md:117` (spot-checked). `11-synthesize.md:174`, and `hooks.py:2103-2532` contains no reference (spot-checked).
- **Fix:** Demote drivers 3 and 4 to "designed, partly delivered". In items 9 and 10, name the consumer: CONFLICT verdicts and calibration blocks must appear in "Where sources disagree". A failed counter-search leaves confidence unchanged; item 9 already records it as "searched, not found", which is right.

### 10. Medium: item 16 is mis-costed and not controlled

- **Where:** §5 item 16 (line 108).
- **Gap:**
  - **Cost.** "Cost: an afternoon" ignores HR's own numbers: 30–40 min per light run and 1.5–2.5 h per full run (line 47). One user put a full run at about $215 API-equivalent (line 49). Three to five questions through both tiers is 6–16 hours of HR alone, before usage limits. That defeats the aim of a quick side-by-side.
  - **Host.** Unless HR runs on Claude Code, the test measures Windows breakage. On Codex, 25 agent commands carry a POSIX prefix that PowerShell rejects, and the Stop hook is off under `codex exec` (line 67). The Codex port has never been benchmarked.
  - **Isolation.** HR puts about 3K tokens of CLAUDE.md and about 3.5K tokens of skill listings into every session of its project (line 43). Arms that share a folder are contaminated. The spec runs each trial in a fresh directory with a clean profile.
  - **Tier.** HR light, the only time-comparable tier, runs neither critics nor cite-check (steps 1, 2, 10, 15, 16). "Verification versus HR" therefore means something different for each tier.
- **Evidence:** teardown lines 43, 47, 49 and 67. Spec §6 (test setup). `profiles.py:313`; `14-5-cite-check.md:15`; `12-critics.md:13`.
- **Fix:**
  - Use 2–3 questions.
  - On Claude Code, in the sandbox project from STATUS.md: HR light on every question and HR full on one, plus bare Claude Code and `/deep-research`.
  - On Codex: bare Codex and vafer-research.
  - Give each arm a clean folder.
  - Name the HR tier in every comparison.

### 11. Medium: the opportunities have no instruction budget

- **Where:** §4 "Instructions" row (line 75); §5 items 1–14.
- **Gap:** SKILL.md is about 1,250 words with frontmatter, against the spec's 1,500-word cap. The list adds twelve rule sets or checks.

  Our earlier research is why compactness is the edge the teardown claims. SkillsBench found compact skills +19.0 and comprehensive ones +0.7. For GPT-6 Astra, the user's Codex model, "overly specific guidance can now hinder results", and a skill's root should be a minimal router. The main risk in `verdict.json` is that ceremony "creeps back, as it did in every 0.0.x version".

  The teardown prices items in spawns and page opens, never in instruction words.
- **Evidence:** `wc -w SKILL.md` = 1,255. Spec §3, principle 7. Spec K5 and K7. `verdict.json` claims 7 and 11, and its risks.
- **Fix:**
  - Give each item a word cost and a home: SKILL.md, `briefs.md`, a reference read on demand, or the script.
  - Rank items by expected gain per word.
  - Put the researcher-side rules (items 8, 10 and 13) in `briefs.md`.
  - Put item 11 in a reference that is read only for academic topics.

### 12. Low: "not found" can be a tool failure

- **Where:** items 7 and 9 (lines 99, 101).
- **Gap:** "Not found" can hide a tool failure on both sides.
  - HR's scholar search turns any 429 or 5xx into an empty list that looks like "no results".
  - HR's vault search ANDs every keyword, so one extra term gives zero hits. Step 13 reads that as "no evidence".
  - On our side, Codex web_search reads a cached index by default.
  - Claude Code allows 200 searches per session, shared with subagents.

  Items 7 and 9 turn "searched, not found (queries)" into a finding without recording any of this. Cached mode is also a possible cause of "depth varied between runs".
- **Evidence:** `read-acquisition.md` weakness 7 (`scholar/base.py:189-210`). `read-vault.md` §5 (measured: one added keyword gave zero hits). `hosts.md:7` and `:15`.
- **Fix:** NOT-FOUND rows record the search mode and any tool error, rate limit or blocked page. Those count as access gaps, not findings. Lookups in INDEX.md and in notes match any of the terms, not all of them.

### 13. Low: our own slowdown is reported but not addressed

- **Where:** §4 "Time" and "Evidence" rows (lines 84, 87); item 5 (line 97).
- **Gap:** The Codex observation (1.5–2× bare time) appears only as evidence. Item 5 hides the wait; no item shortens it. The spec caps time only on easy prompts (at most 1.15× bare). For Standard it asks for a quality gain instead (ΔR ≥ +3), so 1.5–2× is acceptable only if item 16 shows that gain.

  HR's history shows how pipeline time drifts. Once measured, its estimates rose from 3–8 to 30–40 min (light) and from 25–60 min to 1.5–2.5 h (full). The front reader's "light loci" idea fits here: rank OPEN, PARTIAL and CONFLICT rows by decision impact × uncertainty, and aim the gap wave at the top 1–3.

  The evidence table also says "One Codex run", but "depth varied between runs" means there were several.
- **Evidence:** CHANGELOG.md:365 (spot-checked). Spec §6 guardrails and §7 M1. `read-pipeline-front.md` §12.
- **Fix:**
  - Add per-phase timing to item 16.
  - Add one time item: prioritize the gap wave as above.
  - State how many Codex runs the observation rests on.

### 14. Low: "read whole" overstates HR's breadth

- **Where:** §2 driver 1 (line 24); §4 "Breadth" row (line 76).
- **Gap:** The teardown does not apply a verified correction. The host truncates long `note show` output (about 30,000 characters on Claude Code), so fetchers do not see whole long papers. Drafters hit the same limit. Only 6 long sources per run get a source analyst. 87 of the sample's 97 sources are arXiv, the easiest kind to fetch.
- **Evidence:** `verified-claims.md`, acquisition claim 6 and pipeline-middle claim 9; `profiles.py:270-271`; `read-acquisition.md` §8.
- **Fix:** Reword driver 1 and the Breadth row. This lowers the pressure to copy HR's breadth (item 8) and supports item 2's bounded excerpts.

### 15. Low: item 13 lacks verified evidence that exists

- **Where:** §5 item 13 (line 105), "Evidence: our Codex observation only".
- **Gap:** HR's cite-check finds zero pairs when the Sources heading is anything other than `## Sources` or `## References`, which includes a Turkish `## Kaynaklar`. Its empty path then writes `[]`, and the gate passes. Its sentence splitter does not split before the Turkish capitals Ş, Ç, İ, Ö and Ü. Quote-integrity skips single quotes, guillemets and scripts written without spaces. A Turkish report with a localized heading therefore gets a silent, empty cite-check. That is a concrete failure to test with the Turkish question in item 16.
- **Evidence:** `read-verification.md` probes 5 and 7. New verdict set, claim 3, confirmed (`citecheck.py:48`; `14-5-cite-check.md:42`). `read-enforcement.md` §3 (`lint.py:98, 124`).
- **Fix:** Cite this as item 13's HR evidence. Carry the constraints into item 1's script: Turkish capitals and month names, «» and ‘’ quotes, and a match only on the original span when a quote is followed by its translation (`SKILL.md:66`).

### 16. Low: item 4 imports saved text without marking where it came from

- **Where:** §5 item 4 (line 96).
- **Gap:** HR treats LLM-written interim and source-analysis notes as trusted because of their type, so page text paraphrased into them escapes the untrusted fence. Its `auto_tag` copies run tags into other runs' corpora (measured). Its freshness fields are never set.

  Item 4 copies saved quotes "into the current run's notes", where they look the same as pages opened in this run. The Reuse section already keeps original citations and dates (`SKILL.md:78`), and the spec lists memory poisoning as a risk. Copying without a marker loses that distinction.
- **Evidence:** `read-verification.md` §3.10 (`untrusted.py:21`). `read-vault.md` §4 and §8 (`enrich.py:27-38`). Spec §8 risk table.
- **Fix:** Each reused entry carries "reused from <run>, opened <date>, verified or unverified" and stays data. Volatile entries are re-opened before they are cited as current.

## What §5 would look like with these gaps closed

1. Item 1 is split into a report-vs-notes drift check (every host) and note-vs-page verification at note time (per host). It stays advisory until audited precision reaches 80%. It has rules for derived figures, table cells and uncited numbers, and it handles Turkish. Its 5× claim is stated per host.
2. Item 2, the verifier, ranks level with item 1 on Codex. Number, unit, date and magnitude mismatches are critical, and its verdicts are audited.
3. Item 3 moves up and adds URL normalization, real titles, and a ban on internal labels in the report.
4. Two new items: writing rules (issue 6) and a scope and harm guard for high-stakes questions (issue 8).
5. Items 7 and 9 record the search mode and tool errors in NOT-FOUND rows. Items 9 and 10 name their consumer.
6. Item 4 marks reused text with its provenance.
7. A new item, or part of item 5: prioritize the gap wave to save time, and measure time per phase.
8. Item 16: two or three questions; `/deep-research` and bare Claude Code as arms; HR on Claude Code in an isolated folder; the HR tier named; an honest cost.
9. Across the list: a word cost for each item, and ranking by gain per word under the 1,500-word cap.

## Smaller omissions that do not change the ranking

- Claims written in steps 8 and 13 are never ingested, and ingest drops entities, scope, period and region (new verdict set, missed item 5).
- The cite-checker's untagged `claims search` can pull an earlier run's note into a report (vault verdict, missed item 4). An overlapping re-run probably costs extra fetch waves, not only a thinner corpus (vault verdict, missed item 3).
- "Never indexed" (line 65) overreaches. A report that keeps its frontmatter is indexed, and quote-integrity can then match the report's own quotes (vault verdict, claim 2; `verified-claims.md`, enforcement, missed item 5).
- The always-loaded CLAUDE.md block calls `run verify` the ship gate and never mentions `run finish` (`verified-claims.md`, enforcement, missed item 4).
- Junk-gate false positives are not mentioned next to the login-wall bullet (line 63). For example, a page titled "Cloudflare Q3 2024 earnings" is rejected as a bot page (`verified-claims.md`, acquisition, missed item 3).
- Two readers left open whether HR's step-5 investigators can spawn fetchers on Claude Code. Our earlier research answers it: Claude Code subagents can nest up to three levels deep (`verdict.json`, claude_code_vs_codex; not re-checked). So the delegation works on Claude Code but not on Codex.
