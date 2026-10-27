# hyperresearch: runs, budgets, lint, escalation, quality and config

Reader notes for the VAFER study of hyperresearch (clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`, HEAD `327498b`). Static reading only: no hyperresearch code, installer or pipeline was run. Paths are relative to `src/hyperresearch/` unless they start with `tests/`.

Files read in full: `core/runs.py` (879 lines), `cli/run_cmd.py` (617), `cli/lint.py` (1835), `core/escalation.py` (179), `cli/escalation_cmd.py` (289), `core/quality.py` (75), `cli/levers_cmd.py` (106), `cli/profile_cmd.py` (243), `cli/repair.py` (274), `core/config.py` (431).

Referenced files opened in part: `core/profiles.py` (Profile model and built-in profiles), `core/levers.py` (whole), `core/codex.py` (stop gate), `core/sync.py` (what gets indexed), `core/vault.py`, `core/db.py` and `core/migrations.py` (schemas), `core/patterns.py` (WIKI_LINK_RE), `search/fts.py` (quality re-rank), `core/hooks.py` (hooks, retired agents), `core/render.py` (header), the skills `hyperresearch.md`, `-1-5-chapter-partition`, `-2-width-sweep`, `-4-loci-analysis`, `-10-triple-draft`, `-14-5-cite-check`, `-15-polish`, and `tests/test_core/test_runs.py`.

## 1. What the subsystem is

A per-run workspace `research/runs/<vault_tag>/` holds `run.json` (the manifest) and `events.jsonl`. The orchestrator agent is supposed to record every step transition with `hpr run step`. `hpr run resume` computes the next step. `hpr run finish` is the ship gate and the only path to status `done`. Around it sit an advisory lint battery (26 declared rules), a SQLite queue for blocked URLs (the "browser lane"), a composite source-quality score, per-run posture "levers" rendered into shim files, profile ("gear") management that re-renders prompts, a `repair` command, and the vault config.

The one fact that matters most: very little here binds. The ship gate binds. Everything else is either instructions to the model, opt-in, or dead in the current (3.0) layout.

## 2. Run state and resumability

**Manifest.** `init_run` (runs.py:97-159) writes `run.json` with `profile`, `profile_steps` (strings "1".."16"), status, `budget_usd`, `max_sources`, `max_notes`, `steps{}`, `chapters{}` and `spend{estimated_usd, sources_fetched, notes_written, agents_spawned}`. It is idempotent: an existing manifest comes back unchanged (runs.py:123-124), so a second `init` with a different budget or ceiling is silently ignored. There is no command to change ceilings after init (run_cmd.py has init, status, list, resume, stop-gate, abort, step, spend, reconcile, event, block, report, verify, finish).

**Writes.** `_save` writes `run.json.tmp` and calls `Path.replace` (runs.py:172-177). There is no lock. `record_event` appends to `events.jsonl`, then loads and saves the manifest again to touch `updated_at` (runs.py:180-198). One `run step ... done` does about four manifest saves and two event appends (set_step, record_event, reconcile_spend_from_disk, its record_event).

**Statuses.** Run: running, paused, blocked, done, failed, aborted (runs.py:59). Step: pending, running, done, skipped, failed (runs.py:60).

**Resume.** `resume_position` (runs.py:469-505) walks `profile_steps` and returns the first step that is not done or skipped, plus `chapters_pending`. `run_resume_position` (runs.py:516-525) narrows the walk to the tier that step 1 declared in `prompt-decomposition.json` (`pipeline_tier` wins over the manifest profile: runs.py:609-646). `run resume` returns the step's skill slug and the Codex step-file path (run_cmd.py:218-229).

Resume gaps:
- Sub-steps cannot be tracked. Profile `steps` are ints 1 to 16 (profiles.py:234-244), so 1.5 (chapter partition) and 14.5 (cite-check) are never in `profile_steps` and resume never points at them.
- Chapters break it. `steps` is keyed by step id only (runs.py:272), and `entry["chapter"]` is overwritten by each chapter. After chapter 1 finishes steps 2-10, `next_step` is 11 even though chapters 2..N are still pending. `skill_to_invoke` follows `next_step` only (run_cmd.py:226). With `chapter_concurrency: 2` (profiles.py:382), the global step status is whatever chapter wrote last.
- `run resume` flips paused, blocked or failed runs to running (run_cmd.py:203-208). That includes budget and verify blocks, with no cap. `set_status` records no event (runs.py:435-442). The test suite asserts that resume unblocks a budget block (tests/test_core/test_runs.py:344-355), so this is intended. But the entry skill makes `run resume` the orchestrator's first recovery action (skills/hyperresearch.md:222), so the agent itself lifts the block.
- Stall flag: `possibly_stalled` fires after 30 minutes without a manifest touch (runs.py:72-74, 534-542). Subagents never touch the manifest (no `run event` or `run step` in agent prompts in hooks.py), and full-tier waves run long, so the flag is noisy.

**Codex stop gate.** `run stop-gate` (run_cmd.py:249-294, codex.py:337-386) blocks ending the session when the newest run is `running`, was touched in the last 6 hours, and has a next step. It lets the stop through when `stop_hook_active` is set (run_cmd.py:276-277), so it blocks once per stop attempt. Any non-running status (blocked, paused) disables it. Claude Code has no Stop hook, only a PreToolUse reminder on WebSearch and WebFetch (hooks.py:3790-3828).

## 3. Budgets and count ceilings

**USD budget: effectively dead.**
- `estimated_usd` moves only through `add_spend` (`hpr run spend --usd`, runs.py:301-324).
- The repo carries no unit prices (runs.py:404: "this repo does not carry unit prices").
- The code comments say agents rarely call `run spend` (runs.py:294-295, 402).
- A grep of `skills/` and `core/hooks.py` finds no instruction to call `run spend`.
- So the budget never trips. Yet the CLI help calls it a "Hard ceiling" (run_cmd.py:48). The dissertation skill's "budget check at every chapter boundary" (skills/hyperresearch-1-5-chapter-partition.md:82) always sees the full budget remaining.
- Even when fed, `run resume` clears it (see above).

**Count ceilings: opt-in and coarse.**
- `--max-sources` and `--max-notes` are checked only when a step is marked done (runs.py:294-297, 381-396). The counts come from the DB: notes tagged with the vault_tag, and distinct source URLs linked to those notes (runs.py:327-356). That is a good fix for agents that never report spend (#92).
- They fire only at step boundaries, so one fan-out step can overshoot by any amount.
- The entry skill never passes them; it only mentions `--budget` (skills/hyperresearch.md:127).
- A block is force-cleared up to 3 times (runs.py:80-81, 359-378), and each clear resets a baseline so the block re-fires only when the count grows (runs.py:388-396).
- After 3 clears, `run resume` exits 1 (tests/test_core/test_runs.py:284-288), which also breaks the documented recovery path. Yet `run block --on <anything>` followed by `run resume` reaches the generic branch and sets the run back to running (run_cmd.py:203-208), which bypasses the cap. Found by reading the code; not executed.
- `reconcile_spend_from_disk` overwrites `sources_fetched` and `notes_written` (runs.py:410-413), so values added with `run spend --sources/--notes` are lost.

**What really governs cost: profile numbers in prompts.** The built-in profiles (profiles.py:253-415) are as follows:

| Profile | Steps | Sources | Drafts | Time estimate |
|---|---|---|---|---|
| light | 1, 2, 10, 15, 16 | 15-25 | 1 | ~30-40 min |
| full | 1-16 | 55-80 | 3 | ~1.5-2.5 h |
| premier | 1-16 | 100-130 | 3 | ~3-5 h |
| dissertation | chaptered | 300-450 | 1 per chapter | ~4-8 h |

- The full profile's fan-out: wave-1 fetchers 10-12, wave-2 fetchers 3-5, wave-3 fetchers 2-3, up to 6 source analysts, 2 loci analysts, up to 6 investigators, 3 drafters, the synthesizer, 4 critics, the patcher, the cite-checker, polish and readability.
- These numbers are Jinja-rendered into the installed skill and agent prompts (render.py:1-25). `profile use` re-renders every installed prompt and persists the gear (profile_cmd.py:146-157).
- Only `word_targets` and `citation_density_min` are read by Python at run time (runs.py:705-770). A grep finds no Python consumer for `draft_count`, `claims_min`, `claims_cap`, `depth_budget_total`, `gap_fetch_cap`, `wave_done_ratio` or `vault_check_interval_s` outside profiles.py.
- The only code-enforced count limits on the default path are in the browser lane: at most 25 items per run, and a utility threshold of 8.0 (config.py:96-102, escalation.py:76-85).

## 4. The ship gate (`run finish` and `verify_run`)

`finish_run` (runs.py:847-879) runs `verify_run`, records `verify{passed, failed_checks}` in the manifest, and sets status to done or to blocked(verify). The skill caps fixing at 3 rounds and then requires an honest blocked state (skills/hyperresearch.md:281, 302).

The checks in `verify_run` (runs.py:649-844):

| Check | What it actually tests | Where |
|---|---|---|
| report-exists | `research/notes/final_report_<tag>.md` exists | 668-669 |
| decomposition-readable | only emitted when the JSON is invalid | 685-686 |
| levers-rendered | the 4 shim files exist, if the decomposition declares levers | 691-703 |
| length-in-range | word count within the profile's `word_targets[response_format]`, ±20%; character-based for scripts without word boundaries; skipped when `response_format` is missing or unknown | 705-730 |
| required-headings | `h not in report_text`: a case-sensitive substring anywhere | 732-737 |
| citation-density | `[n]` and `[n, m]` markers plus every `[[...]]` per 1000 words ≥ `citation_density_min` (9.0) | 747-770 |
| no-scaffold-leak | only the literal `## User Prompt (VERBATIM` | 772-776 |
| quote-integrity, retracted-citations | the lint functions run in-process; errors fail the gate; an exception fails closed | 783-806 |
| artifact:critic-findings-{dialectic,depth,width,instruction}.json, patch-log.json | existence only, when the tier includes steps 12 and 14 | 810-817 |
| artifact:polish-log.json | existence only, when the tier includes step 15 | 818-820 |
| cite-check-resolved | runs only if step 14.5 is marked done; criticals only require `cite-check-patch-log.json` to exist | 822-842 |

The design lesson is written into the code. Bench Q62 shipped with 24 hallucinated-quote errors because the orchestrator ran lint separately and decided the failures were false positives. Folding the rules into the single gate "removes that seam" (runs.py:778-782).

Gate holes:
1. **Density counts the bibliography.** The regex runs over the full `report_text` (runs.py:747-750), not over `_report_body_only` (lint.py:102-107). Inline style writes one `[N] Title. URL` line per source (skills/hyperresearch-10-triple-draft.md:71, skills/hyperresearch-11-synthesize.md:200). At about 12 words per entry, roughly one bibliography entry per 100 body words meets the 9.0 floor with zero in-body citations. Wikilinks are counted without checking that they resolve (`WIKI_LINK_RE`, core/patterns.py:24).
2. **Critic stages can be stubbed.** The checks are existence-only, and the polish skill authorizes stubs: "If it fails a second time, write a minimal stub (`{"findings":[]}` for critic files...)" (skills/hyperresearch-15-polish.md:107). A full run whose critics all failed can pass.
3. **Cite-check is conditional on bookkeeping.** It is checked only if 14.5 is recorded done (runs.py:824), and 14.5 can never be a profile step. Criticals need only a patch log to exist, not to have been applied (runs.py:834-838).
4. **Length uses the manifest profile, but steps use the declared tier.** Word targets come from `manifest["profile"]` (runs.py:661), while step sets use the declared tier (runs.py:627-646). A premier-gear run that step 1 reclassified as light is held to premier's argumentative floor of 6400 words (8000 × 0.8, profiles.py:364). The ±20% band also forces compression passes (skills/hyperresearch.md:276).
5. **No sync before checking quotes.** The finish path never calls `auto_sync` (the `vault.db` property only opens and migrates: vault.py:66-73). The quote check reads the index as of the last sync.
6. **Headings and scaffold leaks are substring checks.** Only one of the 10 scaffold headers is gated (runs.py:772-776 against hooks.py:105-116).

## 5. Lint: what it checks and how strict it is

`hpr lint` (lint.py:235-1835) calls `auto_sync`, runs every rule or the one named by `--rule`, and prints issues. **It never exits non-zero on errors** (lint.py:1808-1835). `--fix` is declared and never used (lint.py:238). `--rule <typo>` runs nothing and prints "Vault is healthy" (lint.py:263, 1821-1823). The polish step runs 4 rules as pre-checks (skills/hyperresearch-15-polish.md:126-139), and its description of `patch-surgery` ("draft churn ... exceeds the safety threshold") does not match the code (lint.py:1201-1296 checks skipped criticals and an empty log).

Status of the 26 declared rules (lint.py:17-44) in the 3.0 layout:

| Rule | Severity | Status |
|---|---|---|
| quote-integrity | error | binding (in gate) |
| retracted-citations | error | binding (in gate); wikilinks only (lint.py:214) |
| numeric-consistency | warning | advisory; substring match against all claims and source bodies (lint.py:150-197) |
| wrapper-report | error | advisory; always active in 3.0 because query.md exists; checks the newest report by mtime |
| citation-style-preservation | error | advisory; at least one resolving wikilink, or `[N]` plus a Sources heading |
| instruction-coverage | error/warn | advisory; lowercase entity-name substring; error at 3 or more missing |
| locus-coverage | error/warn | advisory; tag `locus-<name>` not lowercased against lowercased stored tags (lint.py:1034 vs sync.py:290); global, so other runs' interims count |
| patch-surgery | error/warn | advisory |
| workflow | error | advisory; any run's scaffold.md or loci.json satisfies it |
| provenance | error/warn | advisory; rooted-tree check of `*Suggested by [[...]]` over the whole vault; ratio checks skipped when any loci.json exists |
| extract-coverage | error/warn | disabled whenever any run in the vault has loci.json (lint.py:1109) |
| scaffold-prompt | error | **vacuous**: it queries notes tagged `scaffold` (lint.py:637-642), but the 3.0 scaffold is `runs/<tag>/scaffold.md`, which sync skips (sync.py:94-97); no code or prompt creates scaffold-tagged notes |
| audit-gate (plus self-certification guard) | error | **dead**: it expects `runs[].mode` of conformance or comprehensiveness (lint.py:346-348); the auditor agent is retired (hooks.py:4178-4180); polish writes `{"mode": "hyperresearch-v8", ...}` (skills/hyperresearch-15-polish.md:113-123) |
| duplicate-ids | error | **dead**: `notes.id` is the PRIMARY KEY (db.py:20) |
| stale-indexes | n/a | **declared, not implemented** (lint.py:41) |
| missing-title, missing-tags, missing-summary, uncurated, orphaned-raw-files, broken-links, expired-notes | warning | vault hygiene |
| singleton-tags, orphaned-notes, empty-notes, stale-reviews | info | vault hygiene |

Quote-integrity in detail (lint.py:98-147):
- Every span of 5 or more words inside `"..."` or `“...”` in the body (Sources section and `[n]` markers stripped) must match an FTS5 phrase query in `notes_fts.body_plain` (porter plus unicode61: db.py:203-210).
- It checks existence in any note, not in the cited source. Sync indexes every `.md` with frontmatter under `research/`, except root files and `runs/` (sync.py:89-102), and `research/temp/` is synced (vault.py:96-101). So agent-written interim notes, extracts and stubs count as evidence.
- The final report itself carries no frontmatter, by prompt rule (skills/hyperresearch-10-triple-draft.md:74), so it is not indexed. If an agent ever adds frontmatter, the report becomes a note and every quote matches itself. Nothing enforces "no frontmatter".
- Blind spots: single curly quotes and guillemets are not covered. CJK quotes are skipped, because `len(quote.split()) < 5` (lint.py:124) on text without spaces. Elided or translated quotes fail. An unbalanced `"` (12" pipe) shifts the pairing.
- The prescribed fix is to drop the quotation marks or make the quote verbatim (skills/hyperresearch.md:277).

Cross-run bleed: `_run_artifact` returns the newest run dir that has the artifact (lint.py:57-69), and `_latest_report` the newest report by mtime (lint.py:83-95). Most queries are vault-global. Lint and `run finish` can therefore examine different reports.

## 6. Escalation queue (browser lane)

- The table is `escalations` with UNIQUE (url, vault_tag) (migrations.py:220-238). Lifecycle: queued, in_progress, then fetched, needs_human or abandoned (escalation.py:13-23).
- The fetch gate enqueues a blocked URL when the lane is enabled, its utility is ≥ 8.0 (None passes), and the run has fewer than 25 items (escalation.py:60-90, config.py:96-102).
- `claim_next` is one `UPDATE ... RETURNING` with a subquery, so claims are atomic (escalation.py:93-120).
- `escalation ingest` writes the agent-supplied page text as a draft source note with `fetch_provider: chrome`, inserts a sources row, syncs and resolves the item (escalation_cmd.py:116-218).
- CAPTCHA, 2FA and login are `needs_human`, consolidated into one message to the human.
- Codex has no browser-fetcher, so nothing drains the queue; queued items are listed once at the end (skills/hyperresearch.md:192-195).

Problems:
- Ingest does not check that the item was claimed (escalation_cmd.py:138-145). It finds the item with a 10,000-row scan.
- There is no lease or timeout on in_progress, so a crashed drainer leaves items stuck.
- NULL vault_tag rows do not dedupe, because SQLite UNIQUE treats NULLs as distinct.
- The page text is LLM-transcribed but trusted like a fetched page, including by quote-integrity.
- The "drain up to 10 items" in the skill is hard-coded; config `drain_batch_size` is unused.
- In non-interactive Claude runs the skill says to run `run block <tag> --on human-challenges` "and CONTINUE the pipeline" (skills/hyperresearch-2-width-sweep.md:282, skills/hyperresearch.md:199). After that, every `run step N --status done` raises "this block cannot be cleared with --force" (runs.py:259-269) until `run resume`. If the orchestrator presses on, 14.5 is never recorded and the cite-check gate check is silently skipped. The skill also says "the queue drains on the next `hpr run resume`", but resume only flips status.

## 7. Quality score

- `compute_quality_for_row` (quality.py:25-53) is a renormalized weighted mean of the available components:
  - tier weight, w 0.35: ground_truth 1.0, institutional 0.85, practitioner 0.7, commentary 0.4, unknown 0.6
  - utility/18, w 0.20
  - authority percentile, w 0.25
  - vault PageRank centrality, w 0.20
- Retracted sources are floored at 0.05 (config.py:105-136).
- It is consumed by `search --ranked`, which multiplies relevance by 0.5 + q, with NULL treated as 0.5 (search/fts.py:181-190). Step 10 uses it to build must-read lists (skills/hyperresearch-10-triple-draft.md:108-112), and it sorts claims (core/claims.py:289-320).
- It is recomputed only by `graph rank`, which the pipeline calls at step 2.7 only (skills/hyperresearch-2-width-sweep.md:232), and by repair and scholar enrichment. Sources fetched in steps 5, 8 and 13 are unscored, and so neutral, at step 10.
- Its inputs are mostly LLM priors (an agent-assigned tier, and a utility guessed before reading: skills/hyperresearch-2-width-sweep.md:113, 124) plus link popularity among agent-written notes.
- Renormalization can rank a sparse note above a fully scored one, and `unknown` (0.6) outranks `commentary` (0.4).
- Separately, search boosts `evergreen` notes 1.5x (config.py:225, search/fts.py:173-174), and `repair` promotes any note with 100 or more words and a link to evergreen (repair.py:183-199).

## 8. Levers (posture shims)

- Step 1 writes `levers{register: teach|survey|analyze|advocate, inference_depth: surface|standard|deep, domain_notes}` into the decomposition (levers.py:1-36).
- `render_shims` composes four role files additively: research, drafting, critics, polish (levers.py:235-258, 290-330). The orchestrator must paste each one verbatim into spawn prompts. That is instruction only (skills/hyperresearch.md:212, 303); the gate checks only that the files exist (runs.py:688-703).
- The posture texts are well written and register-specific: in teach or survey, critics must not flag hedging; in advocate, a strong steel-man is mandatory (levers.py:49-195).
- Cost: roughly 100-250 words per shim on every spawn. That is an estimate.
- `levers set` accepts arbitrary keys, and it and `read_levers` read JSON with `utf-8` (levers.py:271, 282) while runs.py uses `utf-8-sig`.

## 9. Profiles and config knobs

- `profile use` (profile_cmd.py:107-181) refuses light and dissertation as gears, persists the gear and re-renders the Claude prompts, plus the Codex prompts when Codex is installed.
- Custom `[profile.<name>]` overlays extend a built-in profile (profiles.py:463-497).
- Config (config.py) has these sections:
  - fetch timeouts and size caps
  - junk and login-wall gates
  - chrome lane
  - ranking weights
  - lint thresholds (extract 150 words, divisor 3, stale reviews 90 days)
  - embeddings (off by default)
  - scholar OA recovery (on; abstracts are replaced by full text ≥ 6000 characters; `oa_rescue_blocked` builds whole notes from an OA substitute)
- Dead knobs: no Python reference outside config.py for `exclude_patterns` (and sync.py:39 `_should_exclude` is never called), `drain_batch_size`, `scholar_enabled`, `index_pages` and `default_status`.
- `save()` writes strings without escaping (config.py:333-334). A backslash or quote in any string field yields invalid TOML that breaks every later command. It also drops comments and unknown keys whenever `profile use` saves.

## 10. Repair

`repair` (repair.py:13-274) does a force sync; stubs every broken wikilink into `research/temp/` (51-83), which makes fabricated `[[ids]]` resolve for citation-style-preservation (lint.py:1454-1461); auto-tags and auto-summarizes; promotes draft to review to evergreen by word count and links (154-209); rebuilds indexes; recomputes centrality and quality; and updates agent docs. The enrich and promote loops use bare `except Exception: pass` (141-142, 179-180, 198-199).

## 11. Windows problems (in this subsystem)

1. **BOM and encoding inconsistency.** runs.py reads JSON with `utf-8-sig` (runs.py:620, 681, 829). levers.py (271, 282) and lint.py (331, 1013, 1209, 1265, 1322, 1410) use `utf-8`. Windows PowerShell 5.1 `Set-Content -Encoding UTF8` writes a BOM. With a BOM in `prompt-decomposition.json`, `levers render` fails ("corrupt prompt-decomposition.json"), while verify_run still sees `levers` and demands the shims. The run cannot ship until the file is rewritten without the BOM.
2. **UTF-16 output from PowerShell 5.1 `>`.** Redirection in Windows PowerShell 5.1 writes UTF-16. The resulting UnicodeDecodeError is not caught by the `except (json.JSONDecodeError, OSError)` sites, so lint crashes. lint.py:1293 itself advises `echo '{...}' > research/patch-log.json`, which is also the legacy flat path that the gate does not look at.
3. **Manifest replace.** `_save` uses a fixed tmp name and `Path.replace` (runs.py:175-177). On Windows the replace fails with PermissionError while another process holds `run.json` open; only RunError and VaultError are caught in run_cmd.py. Writers are mostly the single orchestrator, so this is low risk.
4. **Config strings.** `config.save` does not escape `\` (config.py:333-334).

## 12. Weaknesses, ranked

**High**
- The USD budget is never fed, and `run resume` clears it (runs.py:301-324, 404; run_cmd.py:48, 203-208).
- Critic artifacts are checked for existence only, and the pipeline itself authorizes stubs (runs.py:811-817; skills/hyperresearch-15-polish.md:107).

**Medium**
- The citation-density floor counts bibliography `[N]` entries and unresolved wikilinks (runs.py:747-750).
- Quote-integrity checks existence anywhere in the vault, not attribution to the cited source (lint.py:127-131).
- Retracted-citation checking covers wikilinks only, so numbered (public) reports are unchecked (lint.py:214).
- The cite-check gate depends on self-reported 14.5 bookkeeping (runs.py:824).
- The human-challenges block breaks step bookkeeping for the rest of a non-interactive run (runs.py:259-269; skills/hyperresearch-2-width-sweep.md:282).
- Chaptered resume is wrong: steps are keyed without the chapter (runs.py:272; run_cmd.py:226).
- Only 2 lint rules bind; lint never fails; several rules are dead or vacuous (lint.py:41, 238, 309-708, 1711-1720, 1808-1835).
- Cost control is prompt-only: no code consumer for most profile numbers (render.py:1-25).
- BOM inconsistency on Windows (levers.py:271).

**Low to medium**
- Lint bleeds across runs (lint.py:57-95, 1109).
- Length uses the manifest profile while steps use the declared tier (runs.py:661).
- The quality score is built from priors and is stale after step 2.7.
- Quote-regex blind spots.

**Low**
- The count-ceiling cap is bypassable and ceilings are immutable.
- Stall-flag noise.
- Telemetry carries no cost data (agents_spawned and estimated_usd always 0).
- Escalation robustness (no lease, no claim check).
- Dead config knobs and unescaped TOML.
- `run event --data` with a non-object raises an uncaught TypeError (run_cmd.py:427-434).

## 13. What drives quality here

- **Yes:** the single binding ship gate with quote-integrity. Quotation marks are reserved for verbatim text, and an orchestrator cannot argue failures away. Bounded fix rounds end in an honest blocked state.
- **Yes, as cost:** the profile breadth numbers. Quality is tied to scale, but only through prompts.
- **Partly:** lever shims (genre fit), the quality score (must-read ordering), the browser lane (recovers blocked sources, Claude Code only), OA recovery (full text instead of abstracts), and the 4 polish lint pre-checks.
- **No:** budgets, count ceilings, run report telemetry, stall detection, repair promotion, and the dead lint rules.

## 14. Ideas for VAFER

- Adopt: one binding final check whose verdict the orchestrator may not re-litigate (runs.py:778-782 lesson); cap fix rounds at 2-3, then ship with the failures disclosed.
- Adopt: the writing rule that quotation marks are only for verbatim source text; a failed quote loses its marks or gets corrected.
- Adapt: verify quotes and headline numbers against the note entry for the same cited URL, not against "any note". VAFER notes already carry URL plus a verbatim quote of up to 30 words, so this is cheap.
- Adapt: count citations in the body only, and require every `[n]` to resolve to a listed source that was actually opened.
- Avoid: self-reported spend or budget bookkeeping; derive counts from files, and cap cost structurally (researcher counts, waves).
- Avoid: existence-only checks for review stages; a critic's output must cite the spans it judged, or the stage is not claimed.
- Avoid: length bands as a gate (they trigger forced compression or expansion passes).
- Adapt: keep state in plan.md checklist rows, and key any split work by (section, phase), never by phase alone.
- Adopt: list unreachable or blocked URLs once at the end as access gaps with reasons.
- Adapt: a one-line register and inference depth in plan.md, read by the writing step and by any critic.
- Avoid: numeric composite source-quality scores built from LLM priors and link popularity; keep the primary-record-first rule.
- Avoid: "newest file wins" lookups; always address the current run folder explicitly.
- Adopt for any VAFER script: read with `utf-8-sig`, catch UnicodeDecodeError, and warn agents off PowerShell 5.1 `>` redirection.
- Avoid: dead or legacy checks; every check needs a test that fails when its input is missing.

## 15. Uncertainties

- Not executed: the `run block --on x` plus `run resume` cap bypass and the BOM failure chain are from code reading only.
- Token and time costs for bookkeeping and shims are estimates, not measurements.
- How often critics actually fail and get stubbed in practice is unknown (no run logs in the clone were examined).
- Whether the drafters' citation_totals prompts already keep body density high enough that the bibliography inflation never matters in practice is unknown.
