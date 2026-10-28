# Critique of teardown.md: accuracy

Date: 2026-10-28. Lens: are the teardown's factual claims about hyperresearch and about vafer-research supported by the reader notes, the verified claims (`verified-claims.md`, `verify-verification.md`, `verify-vault.md`) and the code?

**Verdict.** The mechanism claims about hyperresearch hold up. The problems are elsewhere:

- The DRACO section claims more than the verification supports.
- Four claims are repeated without their qualifiers: that sources are "read whole", the "100% of runs" quote, the Q62 example, and "negative reuse".
- The teardown miscounts our own evidence ("One Codex run").

None of this reverses a recommendation, but the high and medium issues should be fixed before the teardown goes to the team.

## Method

- I read all nine reader notes, the three verification files, our SKILL.md and its two references, the design spec (evidence table K1–K18) and `verdict.json`, then checked each teardown sentence against them.
- I ran these spot checks:
  - **Clone (327498b):**
    - `core/hooks.py` is 4,545 lines.
    - The cited quotes are verbatim at `hyperresearch.md:309, 313` and `1-decompose.md:117`.
    - The `{hpr_path}` substitution is unquoted (`hooks.py:69`).
    - The scholar providers need keys: `core_oa.py:76-77`, `fred.py:81-82`, `edgar.py:124-125`.
    - The sample report has 97 Sources entries, 87 of them on arXiv.
    - CHANGELOG.md:20 and :203, and commit 61e77cc, say what the verifier reports.
  - **Sandbox install:**
    - It contains 19 Claude skills (the router plus 18 step skills), 16 Claude agents, 15 Codex TOML agents, and a `node` PreToolUse hook.
    - The installed CLAUDE.md is 15,491 characters and contains the CLI path 40 times.
    - The env prefix appears 25 times in the Claude agents, and 20 times in the Codex agents plus 2 in the Codex step files.
  - **Windows PowerShell 5.1:** I ran the POSIX env prefix.

## What holds up

These claims match the verified verdicts and need no change:

- **Ship gate:**
  - It is the sole path to `done`.
  - It counts citation density over the whole file.
  - It checks retractions for wikilink-style citations only.
  - It checks critic, patch and polish artifacts for existence only.
  - It treats `[]` as a resolved cite-check log.
  - Declaring `light` drops the critic checks.
- **Step 14.5:** it sits outside the integer profile steps, so resume and the Codex Stop hook skip it.
- **Cite-check triage:**
  - Wrong numbers pass: "grew 5%" against a 25% claim, and "[12]" against "2012".
  - Sampling never applies to numbered citations.
  - Unmapped markers vanish.
- **Independence:** a cluster of k copies counts as 1+(k−1)/k voices, and nothing exposes the scores.
- **PageRank:** quality is applied after the SQL LIMIT, and the suggested-by edge points the wrong way.
- **Search:** `search --json` returns full bodies with no cap.
- **Vault:**
  - SQLite contention appears at 6,000 broken links.
  - The MCP server, embeddings and the viewer are unused by the pipeline.
- **Gates and hooks:**
  - The login wall fails on Federal Register, EBA and AEA titles.
  - The Codex Stop hook has soft spots.
  - The tool locks are real only on Claude Code.
  - Quote-integrity matches against any note.
  - The budget is inert.
- **DRACO arithmetic:** 5–5 tasks, Medicine supplies 75%, the gap is 1.29 without it, p ≈ 0.31.
- **Counts:**
  - 18 step skills, 16 agents and 15 TOML agents.
  - About 163K characters of agent prompts.
  - About 1,200 tests.
  - 97 sources, 87 on arXiv.

## Issues (most severe first)

### 1. High: DRACO is attributed to the one-pass writer, and is said to show nothing about the OSS pipeline

- **Where:** §2 item 9 ("The hosted "Deep" product behind the DRACO score runs ... one one-pass writer ... (verified)"); §3 "What DRACO #1 shows" ("measures ... the one-pass-writer path"; "DRACO says nothing about the OSS pipeline"); §4 "Evidence of quality".
- **Problem:** The verifier marked this "partly" and made two corrections the teardown does not carry:
  - The DRACO page credits only 3 of HR's 10 reports (Finance, Academic, Law) to the "current Deep writer" and never says which writer produced the other 7. The one-pass writer is therefore shown for the current design, not for the scored board.
  - Hosted Deep runs the chaptered research steps that the OSS also ships, so DRACO is weak evidence about the research front end. It is evidence of nothing about the writing chain (steps 10–16).

  The teardown also contradicts itself. The same paragraph says the board measures "the one-pass-writer path" and that "three of HR's ten reports came from a newer writer". If only 3 came from the current writer, the writer of the other 7 is unknown. This matters because §2 item 9 ("revealed preference") and §5 item 15 ("Do not import triple drafts...") lean on this attribution.
- **Evidence:**
  - `verified-claims.md`, claims-history #1 (verdict "partly", correction 3) and #7 (correction).
  - `read-claims-history.md` §1.3 ("Post-hoc rewrite"), §1.5, and §13 ("Whether the hosted Deep shares any code with the OSS beyond steps 1–11").
- **Fix:** Rewrite as: "The board measures hosted Deep (Oct 2026, chaptered research). Only 3 of the 10 HR reports are credited to the current Deep writer, and the writer of the other 7 is not stated. DRACO is weak, indirect evidence about the research steps: the hosted product runs them chaptered, which the OSS offers only in its experimental dissertation tier. It is no evidence about the OSS writing chain, Codex, or statistical superiority." Mark §2 item 9 "partly verified", and present the hosted design as the vendor's current design, not as the design that was scored.

### 2. Medium: "read whole" describes the instruction, not what the host delivers

- **Where:**
  - §1 step 2 ("read every body whole") and step 10 ("each read 20–50 notes whole").
  - §2 driver 1 ("each read whole by a fetcher").
  - §3 Tokens ("fetchers read 100–150 pages whole").
  - §4 Breadth ("55–80 sources read whole").
- **Problem:** The verifier corrected this (acquisition #6, "partly"). Claude Code's Bash tool truncates output at about 30,000 characters, so `note show -j` shows a fetcher only the start of a long paper. The acquisition reader, whose 0.5–1.5M-token estimate the teardown reuses, wrote "long PDFs get read only from the start". Drafters read 5–8 notes per call, so truncation is likely there too, and a single over-long note has no remedy (pipeline-middle #4 and #9). Sources over 5,000 words are handed to source analysts, capped at 6 per full run. Breadth with full-text reading is driver #1, so the qualifier matters.
- **Evidence:**
  - `verified-claims.md`, acquisition #6, pipeline-middle #4 and #9.
  - `read-acquisition.md:414-420`.
  - `read-pipeline-front.md` §6.5 (`profiles.py:270-271`).
- **Fix:** "Told to read every body in full. On Claude Code, output past about 30K characters is cut, so long sources are read from the start unless one of at most 6 source analysts takes them." Label the 0.5–1.5M tokens an upper estimate.

### 3. Medium: the "100% of runs" quote drops its condition

- **Where:** §2 driver 8 (the orchestrator "silently dropped" the corpus critic and the triple draft in "100% of runs").
- **Problem:** The source sentence is: "This happened in 100% of runs where the orchestrator didn't re-read the skill file" (`skills/hyperresearch.md:309`, checked). Without the condition, a near-tautology reads as a measured failure rate. The verifier calls the evidence anecdotal: a V7-era self-report with no run count.
- **Evidence:** `src/hyperresearch/skills/hyperresearch.md:309`; `verified-claims.md`, claims-history #12 (correction).
- **Fix:** Quote the whole sentence and label it "V7-era self-report, no run count".

### 4. Medium: the Q62 example is used without the caveats the verifier attached

- **Where:** §3 Brittleness, first bullet ("shipped 25,647 words against a 16K ceiling and dismissed 24 quote flags as 'false positives'"); §5 item 7 (evidence).
- **Problem:** The run predates `run finish`, and two of its three symptoms are confounded:
  - **The length overrun:** premier's 8–16K target "never reached the prompt", because the synthesizer's word table was hardcoded to full-gear numbers (commit 61e77cc, checked).
  - **The quote flags:** the quote regex in use then was later shown to turn "38 legitimate short quotes into 42 false errors" (CHANGELOG.md:20). The "false positives" memo may therefore have been partly right.

  The clean evidence that prose gates get skipped is the `run verify` that was never invoked, plus #38.
- **Evidence:** `verified-claims.md`, claims-history #5 (correction) and missed item 2; CHANGELOG.md:20 and :203; `git show 61e77cc`.
- **Fix:** Keep the skipped `run verify` and the #38 quote. Add the template bug and the noisy regex, and do not describe the 24 flags as 24 hallucinations.

### 5. Medium: reuse is called "negative", and reports are said to be "never" indexed

- **Where:** §3 Brittleness, last bullet ("final reports carry no frontmatter and are never indexed"); §4 "Reuse across sessions" ("Negative for overlapping questions"); §5 intro ("negative reuse").
- **Problem:** Both underlying verdicts were "partly" (`verify-vault.md` #1, #2 and #7).
  - **Thinner corpus is inferred, not measured.** Skipped URLs never count toward the tag-scoped 80% wave check or the coverage check. The likely cost is therefore extra fetching and extra waves. The net corpus size was not measured.
  - **Some cross-run reuse exists:**
    - On per-project Claude installs, the PreToolUse reminder tells the agent to run an untagged vault search before every WebSearch and WebFetch (`hooks.py:3584-3585`).
    - The cite-checker's `claims search` is untagged (`hooks.py:3524`).
    - URL dedup saves the network fetch.
  - **Some reports are indexed.** A report that keeps frontmatter, which polish allows "when a wrapper requires it", is indexed (`hooks.py:1623-1642`).

  "Negative reuse" is also one of the three baselines in §5's 5× argument.
- **Evidence:** `verify-vault.md` verdicts 1, 2 and 7, and its missed items 2–4.
- **Fix:** "No corpus reuse. An overlapping re-run's tagged corpus omits the sources fetched earlier, and the run probably refetches or adds waves to compensate (unmeasured). Default reports are not indexed." In §5, replace "negative reuse" with "no corpus reuse".

### 6. Medium: our own evidence is miscounted as "One Codex run"

- **Where:** §4 "Evidence of quality" (vafer column: "One Codex run: ... variable depth"); also "Portability" ("one Codex observation") and §5 item 13.
- **Problem:** The observation is one question (electricity bills in three countries) run more than once on Codex: "its depth varied between runs". The teardown's own Completion-control row says the same. "One Codex run" both understates the evidence and hides that run-to-run variance is itself the main finding.
- **Evidence:** the observation in the task brief; teardown §4, Completion-control row.
- **Fix:** "One question, several Codex runs: more complete and more current than bare Codex, 1.5–2× slower, depth varied between runs."

### 7. Medium: the literature evidence for "Ours" edges and 5× claims loses its qualifiers

- **Where:** §4 Instructions ("SkillsBench: compact +19, comprehensive +0.7, N=5"); §4 Early draft ("TTD-DR, verified"); §5 intro ("expect 0–5 points"); §5 item 1 ("citation support falls 79→17% with depth"); §5 item 4 ("files plus agent 72.5% vs RAG 48.5% (verified)").
- **Problem:** The numbers match the spec's verified column (K5, K8, K11, K16). The qualifiers that the spec and `verdict.json` attach are dropped, and they are the ones that weaken the inference drawn:
  - **TTD-DR and SkillsBench:** `verdict.json` lists both among evidence that "overreach[es]".
    - TTD-DR compared Gemini-2.5-Pro against o3-era OpenAI DR; the spec marks K11 "2025, old competitors".
    - SkillsBench's "comprehensive" bucket is N=5 deterministic terminal tasks, and its "detailed" bucket (N=38) still gained +14.5.
  - **79→17%:** this is GPT-5.4 alone. Opus 4.6 fell from 80% to 58%, and only two models were ablated (spec K8).
  - **"0–5 points":** this drops the exception "except on breadth/enumeration, post-cutoff and Turkish-local tasks" (`verdict.json`, design_critique). Those are exactly the cases VAFER targets.
  - **LongMemEval-V2:** this is question answering over stored agent trajectories. Files plus agent scored 72.5% against 69.3% for an off-the-shelf coding agent (`research-evaluation.json`). It supports "plain files are enough", not "pull-style reuse beats skipping".
- **Fix:** Carry each qualifier in one clause. Write the §4 edges as "ours by design (evidence from older backbones)".

### 8. Medium: the Hosts paragraph asserts host differences that are unverified

- **Where:** §3 Hosts ("Claude Code gets real tool allowlists, the browser lane and the reminder hook ..."; "Codex gets ... subagents that cannot spawn subagents"); §1 step 5.
- **Problem:** Three claims need qualifying:
  - **Nested spawning.** Step 5's investigators must spawn fetchers through Task (`hooks.py:348, 443-450`). Both the pipeline-middle and the enforcement readers flagged that Claude Code subagents probably cannot spawn subagents either. This is unverified, but it is consistent with this critique's own subagent session, which has no Agent tool. If it holds, step 5 either fetches nothing new on Claude Code or breaks its "Do NOT call fetch directly" rule. A spawn count that includes investigator-spawned fetchers would then be too high.
  - **Browser lane.** The browser fetcher's allowlist is `Bash, Read, Write, ToolSearch`. Whether that reaches the Claude-in-Chrome MCP tools is unverified (`read-enforcement.md` §5 and §11).
  - **Reminder hook.** It is installed only by per-project installs, not by `--global` or `--steps-only` (`verified-claims.md`, enforcement #1).
- **Fix:** List nested spawning as an open question for Claude Code ("probably the same as Codex"). Mark the browser lane as unverified, and qualify the hook by install mode.

### 9. Low: the gap-directed-search row omits hyperresearch's pre-draft gap waves

- **Where:** §4 "Early draft, gap-directed search" ("First draft at step 10; critics then gap-fetch").
- **Problem:** hyperresearch runs three gap-directed fetches before any draft:
  - step 2.5's coverage check launches wave 2 for thin items;
  - step 2.6 launches wave 3;
  - step 8's period-pinned check and corpus critic launch 2–4 gap fetchers.

  The real contrast is coverage-directed search (theirs) against draft-directed search (ours).
- **Evidence:** `read-pipeline-front.md` §6.5 (`width-sweep.md:179-220`); `read-pipeline-middle.md`, step 8 (`8-corpus-critic.md:31-58, 88-113`).
- **Fix:** "Coverage-directed waves 2–3 and a pre-draft corpus critic; first draft at step 10" against "draft after wave 1; gap wave aimed at the draft's [GAP] rows".

### 10. Low: the "seven scholarly APIs" carry no default-config caveat

- **Where:** §1 Acquisition.
- **Problem:** The OA rescue is qualified "with default config", but the APIs are not:
  - CORE needs CORE_API_KEY, FRED needs FRED_API_KEY, and EDGAR needs HYPERRESEARCH_CONTACT_EMAIL, so 4 of the 7 work by default.
  - No step skill names `hpr scholar search`. Step 2 names "Semantic Scholar / arXiv / OpenAlex / PubMed", three of which are not wired; only the CLAUDE.md blurb names the command.
- **Evidence:** `scholar/providers/core_oa.py:76-77`, `fred.py:81-82`, `edgar.py:124-125` (checked); `verified-claims.md`, acquisition missed item 5.
- **Fix:** "Seven scholarly APIs behind `hpr scholar search` (four work without keys). Only CLAUDE.md names the command, not the step-2 procedure."

### 11. Low: three gate bullets in §3 are slightly overstated

- **Where:** §3 Brittleness, bullets 2, 5 and 6.
- **Problem:**
  - **(a) "pre-stubs them before the agents run":** true for patch-log, polish-log and cite-check-patch-log. Critic files are stubbed only after a second failure (`15-polish.md:107`). The gate also parses the cite-check findings and fails on invalid JSON (`runs.py:828-841`).
  - **(b) "the sanctioned fix is to drop the quotation marks":** the lint says "Fix the quote or drop the quotation marks", and the router reserves dropping them for rhetorical quotes. The real point is that no code can tell the two kinds of quote apart (enforcement #5).
  - **(c) "nothing re-verifies them":**
    - The gate's quote-integrity check re-checks verbatim quotes after every edit.
    - Step 16 mostly re-binds citations rather than changing claim strength.
    - Hedge-stripping depends on the register setting.
    - The compression rewrite is the router's remedy after a failed gate, not part of the gate (pipeline-back #3 and #9).
- **Fix:** Tighten the three wordings.

### 12. Low: two cite-check details are imprecise

- **Where:** §3 Brittleness, bullet 4 ("in the sample 125 of 155 pairs carry their own index as a 'number'"); §1 step 14.5 ("a Sonnet checker judges the rest").
- **Problem:**
  - All 155 pairs carry their own index. The 125 are the pairs whose own index is 10 or higher, which survive the two-character filter and enter the substring test. The 155 pairs come from a mock vault the verifier built (`verify-verification.md` #1).
  - "Judges the rest" holds for the numbered citation style. In the wikilink style, which is the default (`1-decompose.md:137`), weak pairs whose note ids contain no digits are sampled at 60%.
- **Fix:** "125 of 155 pairs (mock vault) carry an own index of 10 or more, which enters the substring test." "Judges every remaining numbered pair, or a 60% sample of weak wikilink pairs."

### 13. Low: login-walled pages are rejected, not always dropped

- **Where:** §3 Brittleness ("every Federal Register document and EBA and AEA pages are dropped").
- **Problem:** These pages fail the automated fetch after an OA rescue attempt, and the fetcher is told not to retry. On Claude Code they can enter the browser-lane queue (utility at least 8, at most 25 per run, drained 10 at a time), and `escalation ingest` does not re-run the gate. On Codex nothing drains the queue.
- **Evidence:** `verified-claims.md`, acquisition #3 (correction).
- **Fix:** "Rejected with 'do not retry'. On Claude Code a capped browser lane may recover a few; on Codex they are lost."

### 14. Low: "5–6 CLI calls per URL" mixes tool calls with CLI processes

- **Where:** §3 Tool calls.
- **Problem:** The figure 5–6 counts tool calls, including the Write of the claims file. The verified count is 4–5 CLI processes per URL: `sources check`, `fetch`, `note show`, and `note update` twice.
- **Evidence:** `verified-claims.md`, acquisition #2 (correction 3); `read-acquisition.md:401-405`.
- **Fix:** "4–5 CLI processes (5–6 tool calls) per URL."

### 15. Low: four Windows details are off

- **Where:** §3 Hosts, Windows sentence.
- **Problem:**
  - **(a) The "25 agent commands"** are counted in the source and in the Claude install, where 5 of them belong to the Claude-only browser fetcher. A Codex install carries 20 in the agents plus 2 in the step files.
  - **(b) PowerShell gives no parse error.** It raises CommandNotFoundException ("The term 'PYTHONIOENCODING=utf-8' is not recognized ..."), which I confirmed in Windows PowerShell 5.1.
  - **(c) The settings.json overwrite is not Windows-specific.** It happens on any JSON parse failure on any OS, and it hits the project-level file (enforcement #6).
  - **(d) Not "every command" breaks.** The bootstrap and manifest commands use the bare `hyperresearch` name, not the baked path.
- **Fix:** Adjust all four.

### 16. Low: the always-on footprint is understated

- **Where:** §1 Entry ("~3K tokens"); §2 "Always-on footprint"; §4 Instructions ("~6.5K tokens always loaded").
- **Problem:** The 3.1K-token figure is the template's size (12,529 characters). The installed block in the sandbox is 15,491 characters, about 3.9K tokens at four characters per token, because the absolute CLI path is substituted 40 times. Longer install paths add more.
- **Fix:** "~3–4K tokens"; "~7K always loaded".

### 17. Low: #92 is reported as a measurement

- **Where:** §3 Tokens and money ("One user measured about 8.6× ... roughly $215 API-equivalent").
- **Problem:** #92 is one user's estimate of host-session cost on v0.10.0, and the $215 is our multiplication. On current main the manifest still records $0, but it now reconciles source and note counts from disk.
- **Evidence:** `verified-claims.md`, claims-history #4 (correction).
- **Fix:** "One user estimated the host-session cost of a run on v0.10.0 at about 8.6× a $25 ceiling (~$215), while the manifest recorded $0."

### 18. Low: the §2 ceremony list overstates three items

- **Where:** §2 "Ceremony or pure cost": "Dead machinery: ... count ceilings, telemetry, stall detection"; "Inline utility scoring ... select almost nothing"; "dropped by the vendor's own Deep path".
- **Problem:**
  - **Count ceilings** work but are opt-in, unreleased, and never passed by the entry skill.
  - **Telemetry** is partly alive: `sources_fetched` and `notes_written` are reconciled at every step-done, and only the cost fields are dead.
  - **Stall detection** works but fires noisily (after 30 minutes).
  - **Utility scores** also decide which blocked URLs enter the browser-lane queue (score of at least 8.0) and feed `quality_score`.
  - **"Dropped by the Deep path"** is not settled. The vendor's page says "A Deep run uses steps 1 to 11", which in OSS numbering includes the triple draft and the synthesizer. The verifier flagged that wording as inconsistent with the same page's description of the older writing path.
- **Fix:** Say "unused by the pipeline" for the count ceilings, "partial" and "noisy" for telemetry and stall detection, and add the escalation gate to utility scoring. Describe the triple draft as "replaced in the vendor's current Deep design (its pages are inconsistent on steps 10–11)".

### 19. Low: the DRACO paragraph lacks five fair qualifiers

- **Where:** §3 "What DRACO #1 shows"; §4 "Evidence of quality" (hyperresearch column).
- **Problem:**
  - **(a) Task selection:** the page states one task per domain, though not how each was chosen.
  - **(b) The judge:** GPT-5.2 is one of the DRACO paper's alternative judges, with the paper's grader settings and rankings stable across judges.
  - **(c) Uneven comparators:** the unevenness does not touch Claude Research, the runner-up, which was run and graded like HR. HR's three newer-writer reports sum to −4.6 points against Claude, so they do not produce the lead.
  - **(d) The earlier DeepResearch-Bench claim** carried "(benchmarked internally)" and a "Forward-looking projection" caption for most of its life.
  - **(e) The 58.3 sample** probably predates the current rules and used DeepResearch-Bench's Gemini-2.5-Pro judge, which DeepResearch-Bench replaced on 2026-05-11.
- **Evidence:** `verified-claims.md`, claims-history #2, #6 and #8; `read-claims-history.md` §1.2, §1.3 and §2; `read-pipeline-back.md` §11.
- **Fix:** Add one clause per qualifier. The net conclusion stands.

### 20. Low: hyperresearch does not deliver at step 11

- **Where:** §5 item 5 ("HR delivers nothing before step 11").
- **Problem:** In the full tier the report file first exists at step 11, but the user receives it only after steps 12–16 and `run finish`. The light tier writes it at step 10. The 30–150-minute comparison already assumes nothing arrives until the end.
- **Fix:** "HR delivers nothing until the run ends."

### 21. Low: the cite-check token cost is an upper bound

- **Where:** §5 intro ("six-figure-token cite-check"); §5 item 6 ("reads ~97 full bodies (0.3–0.8M tokens, estimate) for 155 pairs").
- **Problem:** Three things lower the figure:
  - Auto-passed pairs never reach the checker (`citecheck.py:187-189, 208-213`).
  - The 155 pairs come from a mock vault with no claims, so the auto-pass count is unknown.
  - The checker reads 5 notes per `note show` call (`hooks.py:3510-3514`), and Claude Code cuts each output near 30K characters. About 20 calls therefore return at most about 150K tokens unless notes are re-read one at a time.
- **Fix:** "Up to ~97 notes, bounded by host truncation (order of 10^5 tokens). The 0.3–0.8M figure assumes untruncated reads."

### 22. Low: "Effect: nothing lost" is unsupported

- **Where:** §5 item 15.
- **Problem:** §2 says no component has been ablated. The do-not-import list also includes "four critics", although §2 names the instruction critic as a plausible driver and §5 item 12 adopts its checklist again.
- **Fix:** "Effect: unmeasured. We expect little loss, and item 12 keeps the instruction critic's checklist."

### 23. Low: "English-only regexes" overgeneralizes, and the evidence cited for item 13 does not show local-language coverage

- **Where:** §4 "Local-language sources"; §5 item 13.
- **Problem:** "No language rule" for search holds; a grep finds none. But several regexes do handle CJK text:
  - the cite-check sentence splitter accepts CJK sentence starts (`citecheck.py:30`);
  - the length and density checks switch to characters for CJK (`runs.py:710-716, 756-762`);
  - the readability thresholds have CJK values (`hooks.py:2600-2643`).

  The English-only parts are:
  - the login-wall and junk signal lists (`web/base.py:78-87, 119-138`);
  - the `## Sources|References` heading regex (`citecheck.py:48`);
  - quote-integrity, which skips CJK quotes and guillemets (`lint.py:98, 124`).

  The Codex observation recorded completeness and currency, not local-language coverage.
- **Fix:** "No rule to search in local languages. English-only gates for login walls, junk pages, Sources headings and quotes." For item 13's evidence: "none yet; test in item 16".

### 24. Low: two descriptions of our skill are off

- **Where:** §4 Instructions ("SKILL.md ~1,100 words"); §5 item 4 ("Cost: already in SKILL.md").
- **Problem:**
  - SKILL.md has 1,170 words in its body, or 1,255 with frontmatter.
  - Item 4's step "copy the saved quote, URL and access date into the current run's notes" is not in SKILL.md. Its Reuse section says to read only the notes needed, answer from them with their original citations, re-check volatile facts, and research only what is new.
- **Fix:** Say "~1,200 words". For item 4, write "partly in SKILL.md (answer from saved notes); copying into the current run is new".
