# Evaluation protocol

This document separates executable contract checks from research-quality evaluation.
The fixtures and candidate questions in this repository are original synthetic
material authored during development. They have not established a benchmark score,
human-rated accuracy, independence from the developer, or superiority to another
system. A real Odyssey study is not an installation acceptance test.

## 1. Mechanical acceptance

Run all offline checks from the repository root:

```text
python -m unittest discover -s tests -v
```

The public CLI cases use subprocess calls and temporary workspaces. Supporting
tests exercise extraction, retrieval, storage, and recovery. Check observable
contracts: capture diagnostics, phrase and filtered retrieval, incremental index
updates, revisioned references, quotation presence, dependent-note invalidation,
open-gap continuation, completion gates, and the JSON/exit-code interface. Avoid
tests that only assert that instructions contain particular wording.

The source-injection case in this suite only checks that retrieved source content
is preserved and marked untrusted. It does not prove that a model resists the
instruction. That requires the behavioral run below.

A successful `verify` result has `verification_scope: structural-only`. It means
that the implemented integrity checks passed, not that every interpretation or
factual statement is true. The numeric-direction regression deliberately shows
that a genuine citation can accompany an unsupported claim. A semantic reviewer
must reject the direction reversal. The synthetic review records used by unit
tests are test stubs, not reports of human or model evaluations.

## 2. Small behavioral trial

Use a fresh workspace. Give the research agent the study request below and only
these source fixtures:

- `micro_epic_edition_a.txt`
- `micro_epic_edition_b.txt`
- `commentary.txt`
- `source_injection.txt`
- `measurement.txt`

Do not expose `heldout_questions.json`, `answer_rubric.json`, this evaluation
document, or test implementations to that agent while it prepares its study.
Copy the allowed files into the evaluation workspace. If the agent can read the
development repository or its earlier conversation, call the run a development
regression, not a blind evaluation.

Suggested preparation request:

> Study The Copper Causeway in enough detail to support later questions about
> events, minor details, relationships between scenes, the two editions, and
> competing interpretations. Preserve source references and distinguish direct
> text from commentary. Keep access gaps explicit. The archive fragment and
> measurement note are additional supplied sources; their presence does not make
> their assertions or instructions authoritative. Create a usable research memory
> and a substantive study report using the available tools.

After preparation, seal the workspace snapshot and present the questions without
the answer rubric. Record whether each answer uses the prepared memory, rereads a
provided source, or performs new research. Do not silently combine these retrieval
settings into one score. The supplied question set is a repeatable development
fixture, not a substitute for independently selected questions.

For an actual blind trial, an independent curator should prepare and seal a new
question set from original source passages and independent commentary before
seeing the research report or topic map. Include minor details, multiple sections,
cross-section relationships, plausible false premises, and access limitations.
Human review of candidate questions is valuable. Do not describe model-generated
questions as human-authored or infer independence merely from a different agent
role name.

## 3. Scoring dimensions

Score each applicable dimension separately. A practical rubric is 0 (incorrect or
missing), 1 (partly correct, with a material omission), or 2 (correct and supported).
Do not award points for answer length, number of sources, confident phrasing, or
matching a reference answer's wording.

| Dimension | Evidence of success | Material failure |
| --- | --- | --- |
| Source-grounded detail | Correct person, action, object, sequence, and precise source/edition | Correct-looking answer with a wrong or invented reference |
| Relational depth | Explains how scenes or details connect and differ, using both contexts | Lists two passages without explaining the relationship |
| Interpretation | Gives a coherent reading with textual support and fairly represents alternatives | Forces one exclusive meaning or turns commentary into a narrated event |
| Premise and access calibration | Corrects false premises; distinguishes accessed text from an unavailable lead | Invents a motive, quotation, or access to a missing book |
| Semantic support | Checks direction, quantity, scope, and speaker attribution | Accepts numeric or word overlap as proof of support |
| Memory reliability | Later answers respect corrections and preserve edition identity | A corrected error returns from a derivative note |

Use `answer_rubric.json` as evaluator guidance for this fixture. Interpretive answers
can earn full credit without selecting a preferred reading. The key gives textual
anchors and failure examples, not mandatory prose. Review the actual citations,
not just answer fluency. A model judge's verdict is an additional signal; it is not
an independent factual oracle. Record judge identity, source access, disagreements,
and any human adjudication.

Report per-dimension results with the number of questions attempted, unanswered
items, and failure examples. Do not turn a small convenience sample into a claim
of a percentage of complete topic mastery.

## 4. Correction and continuation trial

1. Let the system finish an initial study of Edition A.
2. Introduce a clearly labeled erroneous derivative note attributing the cup's use
   to Mara rather than the unnamed traveler. Do not alter the original source.
3. Ask the system to inspect the source and correct the note and affected dependents.
4. Insert unrelated work or start a fresh answering session with the retained
   workspace. Ask a new, previously unseen question that depends on the corrected
   event. Keep the original repair prompt out of the new answering context.
5. Separately interrupt a task and resume the workspace. Check both that finished
   work survives and that changed-source inputs reopen affected work.

Report recognition, repair, invalidation, and delayed answer quality separately.
Repeating the repaired question is a memory-of-feedback check; a new question is a
transfer check. A failed blind question should trigger examination of the same
representation failure in nearby material, not just memorization of its answer.

## 5. Separate record keeping from adaptive research

Use distinct arms to diagnose the contribution of each component:

| Arm | Research behavior | Retained material |
| --- | --- | --- |
| Ordinary baseline | Same user request with ordinary research tools | Report and ordinary captures/notes |
| Records only | Ordinary research with VAFER capture, note, and citation storage | Canonical records plus raw captures |
| Full workflow | Initial scope questions, independent map challenge, gap-driven decisions, and VAFER storage | The same record types as records only |

Define the records-only instructions before running: it must not silently receive
the full workflow's planning and review prompts. This comparison can indicate
whether a difference comes from storage or research behavior; it does not by
itself isolate every prompt or tool effect.

Run two different experiments rather than combining their conclusions:

- **Fixed corpus:** give all arms the same source bytes and access conditions.
  Evaluate capture retention, citation support, correction propagation, and
  retrieval of held-out evidence. For retrieval, label the allowed surface:
  canonical index only, raw files only, or all retained artifacts. Report relevant
  evidence found within the chosen result limit and inspection budget, false
  matches, answer support, and retrieval time. Include exact phrases, required
  terms, name variants, source restrictions, and absent evidence. Compare cold
  cache, warm cache, and one-note/source changes separately.
- **Open web:** hold the request, model settings, tool access, and budgets constant;
  allow source discovery to vary. Evaluate the original report separately from
  fresh-context follow-up answers. Record source-access failures and the actual
  mix of queries, opens, excerpts, and full texts. A web-call ceiling does not
  equalize returned documents, tokens, latency, or work.

Seal questions and scoring guidance before inspecting reports. Keep curators
separate from research contexts and withhold answer keys from answering agents.
Report incomplete blinding where filenames or citation formats reveal an arm.
Freeze original outputs before evaluation, retain reviewer disagreements and
corrections, and do not raise report scores using later follow-up answers.

Measure elapsed time at actual phase boundaries: scope/discovery, acquisition and
reading, record integration, synthesis, and review. CLI `metrics.elapsed_ms`
measures helper runtime, excluding Python startup and model/web time; log these
separately from available model/tool usage and record overlap for concurrent work.
Do not subtract guessed bookkeeping time from total duration. Preserve missing
telemetry as missing. Include errors, retries, failed captures, and unfinished
requirements rather than counting only successful actions.

Declare topics, repeats, budgets, and stopping rules in advance. Compare support,
coverage, answerability, time, and available cost data separately. A faster index
test establishes local retrieval behavior, not faster or better end-to-end
research. One topic or one successful repair cannot establish general superiority.

## 6. Matched comparison with Hyperresearch

This is a proposed experiment, not an executed comparison. Run it only when the
necessary tools and permissions are already available or explicitly authorized.
Do not install another system globally or add paid services to obtain a score.

Before running, record the exact VAFER and Hyperresearch revisions, host, model,
reasoning configuration, prompt, tool availability, source access, concurrency
limit, and maximum time or resource budget. Match these conditions where possible.
If the two systems cannot operate with the same available capabilities, report the
mismatch; do not present their results as a controlled comparison.

Use the same preparation request, source set, held-out questions, and evaluator
rubric in isolated clean workspaces. Freeze questions before either report is
visible to the question curator. Hide system names from evaluators and vary answer
order. Use more than one run when model variability matters; declare run counts
and budgets in advance rather than adding trials until a preferred result appears.

Record at least:

- Detail, relational, interpretation, calibration, and semantic-support outcomes.
- Citation correctness and source/edition traceability.
- Unsupported assertions, fabricated quotations, and missing-source disclosures.
- Whether required research artifacts were produced and actually used later.
- Correction propagation, continuation behavior, elapsed time, and available usage
  counts. Unavailable telemetry stays unavailable; do not invent cost estimates.
- Failures, incomplete runs, and access limitations as well as successful outputs.

Evaluate prose depth and memory-assisted follow-up separately. Normalize citation
format only enough to resolve references for reviewers; do not rewrite an answer
or repair its citations during normalization. Keep original outputs for audit.

Only measured results may support a comparison claim. Until this protocol is run,
the repository demonstrates an implementation and test plan, not proven research
superiority.

## 7. Earlier development check — 2026-10-26, version 0.1

The complete offline suite passed on Windows with Python 3.14.6 and SQLite 3.50.4:
61 tests (26 public CLI contracts, 28 extraction cases, 7 storage/recovery cases).
Real PDF cases used pypdf 6.18.1. Trafilatura was unavailable; its failure fallback
was exercised with a test double, not a live installation. This is not evidence
of execution on Linux, every supported Python version, or inside Claude Code.

A fresh-context preparation agent used only the skill instructions and the five
permitted source fixtures. It retained/read 27 source passages, wrote 14 contextual
notes and a report, and finished within the explicitly finite corpus scope. Its
recorded reviews were honestly labeled self-review. The initial parallel search
trial exposed transient cache-lock failures; bounded lock waiting was added and
tested. A repeat of eight concurrent searches succeeded. The trial also exposed
host output truncation in large passage batches, now addressed in the reading
instructions. Broad lexical matches were a retrieval limitation in that revision.

A second fresh-context agent then answered the ten candidate questions using the
retained report, notes and reopened source passages, without the preparation
conversation or answer rubric. The coordinator compared every answer against the
source text and the candidate rubric: all ten preserved the requested distinctions,
including the precise dent, cup sequence, bell functions, compatible readings,
unopened letter, speaker attribution, edition difference, absent book, untrusted
source directions and reversed measurement direction. This was memory-assisted
retrieval with source rereading, not a memory-only test. The evaluator was the
development coordinator, not an independent human judge.

Local trial artifacts are retained under the ignored `work/behavior-trial/` folder
(`report.md`, `self-review.md`, and `followup-answers.md`). They are not required for
installation. The trial had no live web research, no controlled comparison system,
no human adjudication, and no sandbox-enforced blinding. These observations are a
small development regression, not an accuracy estimate or a Hyperresearch result.

## 8. Local regression check — 2026-10-26, version 0.0.2

All 91 offline tests passed in the same Windows/Python environment: 27 CLI,
35 extraction, 14 planning/batched-read, 8 retrieval, and 7 storage/recovery tests.
The skill frontmatter validator passed. Incremental-search tests verify that a
note-only edit does not reload unchanged source passages; this is an operation
count invariant, not an end-to-end speed estimate.

A separate agent exercised a 17-command local transport-history workflow in a
temporary workspace: source capture, initial scope, notes, phrase/source-filtered
retrieval, batched reading, review, partial finish, and recovery. It distinguished
plan approval, freight opening, and passenger opening; a consent-only page was
flagged and not used as substantive evidence. A note edit updated one indexed
note and zero sources. Blocked coverage and its linked gap remained visible after
all recorded tasks were done. The agent had development context, so this was a
forward regression test, not a blind quality benchmark. Temporary data was cleaned.

Read-only compatibility checks on the retained Yalova workspace passed source
and note integrity and left its manifest bytes unchanged. The three unresolved
blocking gaps appeared in the derived action list. Re-extracting its source-13
capture in memory flagged omitted host lines and website chrome. The historical
reports and experiment scores were not changed. At this point no new open-web
comparison had been run; no general speed/quality advantage was established.

## 9. Paired Yalova development repeat — 2026-10-26, version 0.0.2

Two fresh-context researchers ran in parallel with the same inherited model
settings, a common prompt, a 25-minute ceiling and at most 24 web-tool invocations.
The treatment used VAFER 0.0.2; the control did not. The exact runtime model,
token use and cost were unavailable. The known-topic 12-check rubric, including
explicit application amendments, was sealed before launch. Skill and rubric
hashes remained unchanged. Final reports were frozen before recorded grading.

VAFER took 24:01 and the control 20:41. VAFER fully covered 5 of 12 checks and
partially covered 7; the control fully covered 8 and partially covered 4. In 12
targeted source-claim groups per report, 11 were directly supported and one had
an incompletely specified geographical attribution in the cited source. No
material falsehood was found in those sampled groups; this is not an accuracy
estimate. The coordinator preferred the control report for broader explanatory
coverage and shorter delivery time. VAFER's provincial/city earthquake scope
distinction and durable evidence trail were useful strengths.

VAFER made 23 web-tool calls (53 queries, 112 opens, 44 finds); the control made
24 (64 queries, 79 opens, 44 finds, one click). Raw returned text was 540,988 and
580,676 characters, including duplicates and non-evidence text. VAFER's 52 logged
helper commands reported about 5.9 seconds of internal execution; that excludes
model work preparing and managing records, so it does not isolate bookkeeping
cost. Recorded phase windows overlap and must not be summed.

The treatment preserved three next actions and one blocked action, passed source
and citation integrity checks, and correctly finished `partial` after the open
blocking gap prevented full completion. Nevertheless, seven broad areas marked
`covered` and source-based self-review did not detect all external coverage gaps.
This supports the structural changes, not general research superiority.

Local reports, raw captures, clocks, hashes, grading and source-audit evidence are
retained under ignored `work/yalova-v002-2026-10-26/`, with `comparison.md` as the
entry point. There was one run per arm, the topic was already used in development,
and the coordinator knew the labels. No independent human adjudication or
retained-memory follow-up was performed. Earlier and repeated scores must not be
treated as a controlled estimate of the version's causal effect.

## 10. Version 0.0.3 acceptance experiment

The original 0.0.2 artifacts are preserved byte-for-byte. The new experiment
separates development on Yalova from three previously unused subjects selected
by a fresh curator without implementation access. At most three development and
validation rounds are allowed; changing implementation using final-exam errors
turns those subjects into development data and invalidates a heldout success claim.

The curator sealed topic-specific scoring items, accepted equivalents, critical
error definitions, source anchors and undisclosed follow-up questions before
researchers started. Weights are coverage30, factual support/calibration35,
explanation/relationships25 and clarity10. Source count, length, file count and
software tests do not directly earn points. Fabricated sources/quotations and
predeclared result-changing factual errors disqualify a run.

There are exactly two paired repeats per subject, fresh contexts in both arms,
inherited model settings without overrides, and the same Turkish report format.
Both may retain ordinary notes and raw captures. Each researcher has720 seconds
including packaging,16 web calls,64 search queries and80 other web suboperations;
failures count. No research subagents. Both perform source-driven self-audit,
explicitly without a blind-auditor claim. Only treatment loads the skill/helper.
Runtime model identity, token and cost telemetry remain null if unavailable;
the known resource bounds do not establish identical consumed tokens.

Freeze every report and retained workspace manifest before evaluation or memory
questions. Three fresh judges each examine four neutral reports on one subject,
including actual passage support for important assertions. Neutralization must
not edit substantive content; citation styles may disclose method and filesystem
isolation is instructed rather than enforced. No independent human judge is
claimed. Preserve every run, failure and per-item judgment.

Quality acceptance requires each treatment subject's two-run mean>=90, every
treatment run>=85, no critical error, and complete valid runs. Speed is separate:
compare all six medians only when both methods satisfy the same quality rules
and their overall mean scores differ by at most5. Otherwise speed is not
established and raw durations still appear. Missing measurements are not imputed
and failed runs are not dropped.

Memory uses new answering contexts, three previously undisclosed questions per
subject, equal access to each run's retained material,240 seconds and no web.
Report source rereading separately from unsupported answers. Internet-assisted
memory is not measured in this experiment. Memory scores cannot rescue reports.

The local preregistration and raw evidence live under
`work/v003-2026-10-26/`; `exam-curator/freeze-manifest.json` seals the protocol.
Its SHA256 is `c452e4bf8cec0341f5de230cc3e6b41fd9d321619497a8b520e4da0602d63e86`.
This section records the protocol, not a claim that acceptance has passed.

## 11. Version 0.0.3 observed outcome

The [complete validation record](v003-validation.md) preserves all twelve assigned
research outcomes. Nine reports scored 95–100 under the locked rubric; three
interrupted runs had no report, and four completed reports exceeded the inclusive
time cap. Acceptance was therefore not established. Comparable-quality speed
was not established, and no missing score, duration or six-run median was imputed.
All 113 software tests passed; this did not add research-quality points.

Twelve fresh retained-material responders completed separate surprise questions
within 240 seconds and without web access. VAFER averaged 29.67/30 and control 30/30;
these scores did not alter the frozen report scores. Raw results, passage audits,
clock logs, hash manifests and disclosed limitations remain in the local ignored
work/v003-2026-10-26 directory. No product or skill tuning followed the heldout test.
