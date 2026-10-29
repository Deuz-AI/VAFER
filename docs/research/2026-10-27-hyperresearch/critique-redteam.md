# Red team: the teardown's opportunities

Date: 2026-10-28. Scope: `teardown.md` §5 (Opportunities) and the §4 "Edge" column that feeds it. The lens has four questions:

- Which "5×" claims are hype?
- Which ideas break on real hosts: Claude Code, Codex, Windows, usage limits?
- Which ideas copy hyperresearch (HR) without beating it?
- What would a skeptical deep-research expert reject?

Inputs:

- the nine reader notes, `verified-claims.md`, and the verification and vault verdict sets;
- spot checks in the HR clone (§8);
- `skills/vafer-research/` (0.1.0-alpha), the v0.1 design spec and the deep-research SOTA `verdict.json`;
- the Codex observation: more complete and current than bare Codex, 1.5–2× slower, depth varied between runs.

Nobody has run HR end to end, and nobody has run VAFER 0.1 on Claude Code.

## 1. Verdict

§5 makes one honest statement that matters: against the bare frontier model, expect 0–5 points of report quality. The rest leans on "5× against HR", and most of those claims fail one of three tests.

- **The bare test.** Suppose bare Codex or bare Claude Code also beats HR by 5× on an axis. Then that axis is no reason to install VAFER, because users get the win by installing nothing. Time and cost fail this test: our own Codex run was 1.5–2× *slower* than bare.
- **The host test.** The flagship check (item 1) breaks on both hosts, in different places:
  - On Claude Code, the "verbatim" quotes it trusts come through WebFetch's summarizer.
  - On Codex, the script cannot reach the page, because workspace-write has no shell network.
- **The copy test.** Six of the sixteen items (2, 8, 9, 10, 11, 12) port an HR mechanism at equal or lower strength. None is labeled 5×, which is honest. Together they add instruction weight with no measured gain, which is how v0.0.3 grew.

The project's own pre-registered expectations do not support 5× either. The SOTA verdict expects supported-claim rate +3–10 points and follow-ups 30% cheaper. The spec's M4 target is "≥30% fewer searches and tokens".

Two 5× targets survive, and both are unmeasured:

- **unsupported load-bearing claims per report.** This is an error rate, so "5× fewer" means something. It is plausible only if the baseline rate is already low (about 10% or less).
- **searches and minutes per cross-session follow-up on an INDEX hit.**

The teardown misses a third candidate: **run-to-run spread in checklist coverage.** This is the defect we actually observed.

## 2. The 5× claims, one by one

| Claim (where) | Bare test | Red-team verdict |
|---|---|---|
| Time to first useful answer (§5 intro, item 5) | Fails: bare Codex finished before VAFER | Hype as a VAFER win. 5× exists only against HR full (1.5–2.5 h, 55–80 sources, 5–10K words), a different deliverable. HR light (30–40 min) is the tier closest to our Standard. If bare took about 10 minutes, VAFER took 15–20, and HR light is only about 2× slower. The claim also compares our preliminary draft with HR's finished report. |
| Cost per verified claim (§5 intro, item 6) | Fails: bare spends less than VAFER | Hype. It is cheaper because it verifies less. Ours checks a sentence against a ≤30-word quote the researcher typed; HR checks it against the full note body. The item's own caveat ("once 'verified' is defined identically") cancels the claim, because an identical definition needs page text. HR's 0.3–0.8M tokens is a reader estimate. On a subscription the real unit is share of the usage window, not dollars. |
| Searches per follow-up (§5 intro, item 4) | Passes across sessions: bare remembers nothing | Plausible per INDEX hit, but 5× is far above the project's own 30% target. The hit rate is unknown, and INDEX is per project folder. HR's "negative reuse" is partly inference: by the vault verdict, the re-run loses earlier sources from its tagged corpus and probably refetches, and the net corpus size was never measured. LongMemEval's 72.5% vs 48.5% measures memory recall, not research reuse. |
| Quotes and numbers absent from the cited page (item 1) | Passes: bare has no check | Plausible for quotes once capture is fixed (§3). Unproven for numbers: most headline numbers in our typical questions are derived (§6.3). Neither VAFER's baseline nor HR's is measured. |
| Dangling citations (item 3) | Unknown: nobody counted bare's rate | A hygiene lint. Do it, but do not call it 5×. The HR evidence shows its checker dropping markers, not how often its reports dangle. |
| Local-language primary sources (item 13) | The teardown concedes bare prompted in Turkish may match | Speculative against HR too. HR's "English-only regexes" are its sentence splitter and gates, not its search. Its agents search in whatever language the query invites. The Codex observation was not built to test language. |

## 3. Contact with real hosts

**Claude Code**

- **Quotes come from a summary.** WebFetch returns a model-written extract (hosts.md:8). Researchers save "verbatim" quotes from that extract unless told to ask for the exact sentence.
  - That advice lives only in hosts.md. briefs.md never mentions it, and briefs.md:3 says a subagent sees only its brief.
  - The lead's step-6 re-open has the same gap: SKILL.md:83 sends the lead to hosts.md only "when a tool is missing or behaves unexpectedly".
  - So on the host where curl is available, item 1 would check reports against summarizer text.
- **The real comparator is missing.** `/deep-research` ships with Claude Code. It votes on each claim, filters out failed ones and lists the ones it could not check (hosts.md:11; SOTA verdict). It has no public quality numbers.
  - The spec makes it the arm to beat on Claude Code (spec §2 "Sonuç", §4.7, §8).
  - §5 and item 16 never mention it, and `teardown.md` has no hit for it.
  - Items 1–3 have to beat claim voting, not HR's leaky triage.
- **A text-only message ends the turn.** In `claude -p` that exits the process mid-run. This is HR's documented failure (hyperresearch.md:180; PR #163: one headless run needed 13 invocations, and five exited 0 on progress messages written while subagents ran). Item 5's "show the early draft's findings while the gap wave runs" walks straight into it.
- **The search cap.** A session gets 200 WebSearch calls, shared with subagents, refilled at about 100 per hour. HR full plans 40–100 searches and runs roughly 70–200 in all (reader estimate). An HR arm can hit the cap and distort item 16.

**Codex**

- **No shell network by default.** Workspace-write has no shell network (hosts.md:18). Item 1's "or page" path, item 11's curl calls and any M2 `fetch` all need the launch flag HR already demands: `-c sandbox_workspace_write.network_access=true` (HR README.md:32, cli/install.py:316).
  - Without the flag, item 1 checks the report against notes only.
  - The good news: Codex shows pages as verbatim line windows, so quote capture is sound there.
  - Each host breaks a different half of item 1.
- **Cached search.** Web search reads a cached index by default, and a skill cannot switch it to live (hosts.md:15). The "more current" result we observed depends on how Codex was launched. No item addresses this.
- **Subagent web access.** Whether local Codex subagents get live search is unverified (SOTA verdict, confidence notes). Item 2's verifier may answer NO_WEB.
- **Turn-ending messages.** A text-only interim message ends the turn and hands control to the user, who may take the preliminary findings as the answer (item 5).
- **Project scope.** The skill writes `.vafer/research/` inside the current project, and writing elsewhere would need an approval. So INDEX is per project folder. Research questions are rarely tied to a code project, which caps item 4's hit rate.

**Windows (this machine)**

- **Console encoding.** The console code page is cp1254. In this session, a Python `print` of "→" raised UnicodeEncodeError. A naive M2 script would crash the same way on German, French or CJK quotes.
- **File encoding.** Windows PowerShell 5.1 writes UTF-16LE with `>` and adds a BOM with `Set-Content -Encoding UTF8` (read-enforcement §7, read-runs-lint §11). Notes written that way break a plain UTF-8 reader.
- **Launchers and prompts.** `python` and `py` both exist here; other machines may have only the Store alias. Claude Code in Manual mode prompts on every Bash call.
- **An HR-on-Codex arm would fail on shell, not research.** HR's prompts carry 25 POSIX `PYTHONIOENCODING=utf-8 <exe>` prefixes (counted in `core/hooks.py`), and HR's own Codex notes assume `Get-Content` on Windows (`core/codex.py:127-128`).
- **The line budget.** Item 1's "≤300 lines" has to cover UTF-8 output, utf-8-sig and UTF-16 input, Turkish decimal commas, dotted and dotless i, and one documented invocation per host. Budget for this, or the line count is fiction.

**Usage limits**

- One user estimated an HR full run at about 8.6× a $25 ceiling, roughly $215 API-equivalent (#92).
- Item 16 sends 3–5 questions through HR light and full "in an afternoon". HR full alone is 4.5–12.5 hours, runs 10–12 headless Chromiums at once, and takes a large share of a weekly subscription window.

## 4. Copies that do not beat hyperresearch

| Item | HR's version | Beats HR? | Recommendation |
|---|---|---|---|
| 2 Verifier with four verdicts | A Sonnet checker reads full note bodies | No. If the "bounded excerpt" is the researcher's own quote, it checks the extraction against itself. It also conflicts with the Opus 5 guide ("do not use subagents to verify or double-check your own work") and duplicates item 1 and step 6's re-open. | Put the four labels on step 6's existing re-open. Spawn no verifier until a side-by-side per model family shows a gain. |
| 8 Primary chase | 3–8 mandatory chases per fetcher. In HR this multiplies cost and contradicts HR's own spawn brief (read-pipeline-front W3, W4). | No | Drop the quota; rule 5 already demands the primary record. Label each key number in the report "primary" or "secondary only (reason)" instead. |
| 9 Period records, "what would overturn this?" | Step 8 pre-flight and corpus critic | Matches. Better on one point: a miss is recorded, not counted as added confidence. | Fold the period clause into rule 5. Run counter-evidence searches only for judgments and forecasts; a fact with a primary record needs the record, and rule 6 already covers contested points. |
| 10 Calibration block, explicit resolutions | Committed positions with numeric confidence bands | No | Drop the block: LLM confidence numbers are not calibrated, and nothing consumes them. Per-row and per-claim fields are what v0.0.3 runs filled with one pasted rationale (spec §1). Keep explicit conflict resolutions as a writing rule. |
| 11 OA and retraction check | PDF lane, OA rescue, seven scholarly APIs | No: strictly weaker, and curl is blocked on Codex | Concede academic acquisition. Our observed topics (tariffs, exchange rates, local history) are rarely academic. One brief line for papers is enough. |
| 12 Prompt-adherence check | A separate Opus instruction critic | No, weaker. The lead checks its own draft in the same context, the pattern that gave 1 new question from 23 self-audit candidates in v0.0.3 (spec §1). | Have the gap-finder, which already has fresh context, return the must-mention entities, periods, places and format cues as items. Plan rows then track them. |
| 14 Resumable plan.md | Manifest plus per-step skills, built because a 1,200-line skill was compacted away | It does not need to beat HR. The cited evidence does not transfer: SKILL.md (1,255 words) fits Claude Code's 5,000-token post-compaction budget. | Keep it, and fix the real gap: INDEX is written only at delivery (§6.7). |

Adding all six would push SKILL.md and briefs.md toward the spec's 1,500-word cap. SkillsBench's loss pattern is exactly that: a heavyweight pipeline crowding out the model's own strategy.

## 5. What a skeptical deep-research expert would say

1. **You cannot 5× a bounded score.** Frontier systems score 70–90 on DRACO-style rubrics. 5× only means something for error rates, latency, cost, or recall on long enumerations. State the targets that way.
2. **Metric shopping.** Time, cost and dangling citations were chosen because HR is weak on them by design. They say nothing about research quality.
3. **Circular verification.** A chain of report, then notes, then a quote the same researcher typed checks one link out of three. Without a check at capture, the chain proves consistency, not support.
4. **Effort drives quality.** The vendor's own best path (teardown §2 item 9) reads *more*: an evidence map built by reading every kept source in full, 150–200 sources, 3–5 hours. Anthropic attributes 80% of the variance across BrowseComp runs to token use (older models; not causal). The opportunities push the other way: ≤30-word quotes, bounded excerpts, summaries for the lead. That is a good trade for speed and trust, but it is not a path to 5× quality.
5. **One run per arm, with variance you already saw.** Item 16 can detect a 5× time gap, not a quality gap.
6. **Evidence transfer.**
   - SkillsBench used terminal tasks, and its "detailed" skills (N=38) still gained +14.5. §4 cites only "comprehensive +0.7, N=5".
   - TTD-DR beat 2025 competitors.
   - PANINI used gpt-oss on short answers.
   - The citation decline "79→17%" is GPT-5.4 alone. Opus 4.6 went from 80% to 58%, the average drop was 42%, and only two models were tested.
7. **The wrong input for priorities.** A competitor teardown ranks fixes by the competitor's bugs. Our own observed failures are:
   - the 1.5–2× slowdown;
   - variable depth;
   - an exchange rate taken from aggregators although the central bank figure was reachable (commit efccf1b);
   - a bare topic sent to Standard (commit b1c91b8).

   Only item 7 touches one of these, and nothing targets the slowdown.

## 6. Sharper alternatives, in priority order

1. **Re-anchor 5×.** Keep three targets:
   - (a) unsupported load-bearing claims per report;
   - (b) searches and minutes per cross-session follow-up on an INDEX hit;
   - (c) spread in checklist coverage across repeated runs of one question.

   Report time and usage-window share as ratios to bare. The bar is Standard at or under 1.5× bare, the spec's own guardrail.
2. **Verify at capture, check at write.**
   - Add one line to the Claude Code brief: "Ask WebFetch for the exact sentence that states the fact, verbatim, or NOT FOUND; save only text it returns verbatim, or use curl." On Codex, researchers copy quotes from the line window.
   - Then a local script with no network checks that every quote and every source figure in the report appears in the notes entry for the *same* cited URL.
   - Step 6's re-open uses the same verbatim prompt.
   - This beats HR on both of its flaws (`quoted_support` never checked against the page, quotes matched against any note) and needs no network on either host.
3. **A derived-number protocol.**
   - Source figures must appear in the cited quote after normalizing decimal comma, thousands separators, % and units.
   - Derived figures (currency conversions, VAT, monthly bills from per-kWh tariffs) show their inputs and the formula in the notes, and the script checks the inputs.
   - This is the real shape of the three-country electricity question.
4. **Precision before binding.**
   - Run the check as advisory first. The lead answers each flag in one line: fixed, derived (inputs [3][5]), or false alarm (reason).
   - Make it binding only after the flags prove at least 80% precise, the spec's own M2 criterion.
   - HR's Q62 quote lint was itself noisy: it turned 38 legitimate quotes into 42 errors (CHANGELOG.md:20). So "the lead may not re-interpret its verdict" is the wrong lesson to take from Q62.
5. **Diagnose variance before prescribing.**
   - Compare the Codex runs' plan.md files and method notes: researchers spawned, searches, whether the gap wave ran.
   - Likely causes: the judgment-based fan-out test (step 3), "There is no time limit" combined with Astra's tendency to stop early, cached search, and concurrency chosen by Codex.
   - Fix with tier floors, not per-row verdict text. For example: Standard always runs one gap wave unless every row is COVERED.
6. **State the Codex search mode up front.** For post-cutoff or local topics, check whether results look live, for example with a dated query from this week. If they do not, say so before researching and suggest relaunching with `--search`.
7. **Reuse that cannot lose runs.**
   - Write the INDEX line when plan.md is created, with a status, and update it at delivery.
   - The local run `.vafer/research/2026-10-27-yalova-tarihi/` stopped at "Wave 1 dispatched at 16:08". Its notes/ folder is empty and there is no INDEX.md, so no follow-up could ever find it.
   - Reuse dead ends too: NOT-FOUND queries and blocked URLs. HR has nothing like this.
   - Log the hit rate before claiming any reuse multiple.
8. **Interim findings travel with a tool call.** Put the early draft's headlines in the same message that launches the gap wave, mark them preliminary, and send none in headless runs. The early report.md on disk is the real value: insurance against a crash.
9. **A side-by-side that can actually run.**
   - Compare within a host, not across hosts:
     - Claude Code: VAFER, bare, `/deep-research` and HR light.
     - Codex: VAFER and bare.
   - Use three questions: one Turkish-local, one post-cutoff, one enumeration. Run VAFER and bare twice each, and HR full at most once.
   - Score every report the same way: ten headline claims, each checked against its cited page by hand or by one shared script, marked supported or not.
   - Run outside any git repo, and state the time and usage cost before starting.
10. **Trim.**
    - Adopt two of the copied ideas, folded into existing rules: the period clause into rule 5, and explicit conflict resolutions into the writing rules.
    - Hold items 2, 8, 10, 11 and 12 until a side-by-side shows a gain.
11. **Add the stratum the SOTA verdict expects to pay most.** It expects the largest gains on enumeration, post-cutoff and Turkish-local tasks, and the teardown has nothing for enumeration.
    - A wide-table variant has one row per entity, a completeness column, and researchers assigned by batch of rows. The spec defers it to M5.
    - This is where a multiple over bare recall is plausible.

## 7. Teardown statements to fix before they feed decisions

- **Q62** (§3, first brittleness bullet; cited by items 1 and 7).
  - Premier's word target never reached the prompt because of a template bug (commit 61e77cc).
  - The quote lint then in use was noisy, so the "false positives" memo may have been partly right.
  - Only the skipped `run verify` was a clean prose-gate failure.
- **"The sanctioned fix is to drop the quotation marks"** (§3). The lint offers two fixes, and the router reserves de-quoting for rhetorical quotes. The weakness stands, because no code can tell the two kinds apart.
- **"Nothing re-verifies them"** (§3, edits after cite-check). The gate's quote-integrity check re-checks verbatim quotes after all edits. Paraphrased claims and citation bindings are the parts never re-checked.
- **"Never indexed"** (§3, §4 Reuse row, item 4). True for default runs. A report that keeps its frontmatter is indexed.
- **"Negative for overlapping questions"** (§4 Reuse row). A safer statement: an overlapping re-run loses the earlier run's sources from its tagged corpus and probably fetches more to compensate. The untagged PreToolUse reminder and the cite-checker's claims search both read the whole vault.
- **Login-wall pages "dropped"** (§3).
  - An open-access rescue is tried first.
  - On Claude Code, a misflagged page queued for the browser lane can still be recovered.
  - The queue caps at 25 per run, and Codex never drains it.
- **"125 of 155 pairs carry their own index as a 'number'"** (§3). Every pair carries its own index. In 125 of them it is 10 or more, so it survives the two-character filter.

## 8. Spot checks behind this critique

- HR `src/hyperresearch/core/codex.py:127-134`: Codex agents read files with `Get-Content` on Windows and must fetch through the CLI, never with a browsing tool.
- HR `README.md:32,114,119` and `src/hyperresearch/cli/install.py:316`: Codex must be launched with `-c sandbox_workspace_write.network_access=true`.
- `grep -c "PYTHONIOENCODING=utf-8" src/hyperresearch/core/hooks.py` returns 25.
- A grep of `teardown.md` finds no mention of `/deep-research`, bare Claude Code, enumeration or wide tables, cached or live search, or checker precision.
- On this machine, node, codex, claude, python (3.14) and py are all on PATH. Printing "→" from Python raised UnicodeEncodeError under cp1254.
- `.vafer/research/2026-10-27-yalova-tarihi/` holds:
  - plan.md (Standard tier, four researchers, "Wave 1 dispatched at 16:08");
  - an empty notes/ folder;
  - and no INDEX.md anywhere.
- `wc -w skills/vafer-research/SKILL.md` gives 1,255 words, frontmatter included.
- Commit efccf1b: in the Codex side-by-side, the exchange rate came from aggregators although the central bank figure was reachable. Commit b1c91b8: a bare topic went to Standard, and time budgets were dropped.
- Spec M4 (line 323) targets "≥30% fewer searches and tokens" on follow-ups; the SOTA verdict's confidence notes expect "follow-ups 30% cheaper" and "S +3–10".
