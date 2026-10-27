# Research workflow

Use the relevant mode. Follow-ups do not restart the comprehensive workflow.

## Comprehensive study

### Define the object and scope

Preserve the user's research question separately from presentation requirements. Resolve only ambiguities that change the work; otherwise state reasonable assumptions and proceed.

Set `reading_scope` through `run patch`:

- `finite-work`: the user asks to study a selected book, corpus, or specification as a whole. Identify its version and structural units; track necessary whole-work reading as tasks. Missing required units keep the result partial.
- `open-topic`: the object is a subject, event, mechanism, or system examined through selected sources. Explain source selection and read context sufficient for each consequential claim. A book cited for one claim does not become a mandatory whole-book reading task.

Exclusions chosen to bound the assignment differ from central requirements that remain unanswered. Preserve both honestly.

### Build an answerable map

Use the user's request and an independent overview, source index, or system structure before drafting. Record questions with their origins. A broad period or component is a grouping, not an answered question: split it when locations, phases, mechanisms, alternatives, or consequences need distinct answers. Useful structures depend on the subject:

| Subject | Questions worth distinguishing |
| --- | --- |
| A work | What occurs, who perceives it, how sections connect, how editions or interpretations differ |
| Science | Mechanism, experimental evidence, measurement conditions, alternatives, limits |
| Technical systems | Data flow, interfaces, failure behavior, versions, design tradeoffs |
| History or institutions | Actors, geography, sequence, incentives, material change, consequences, source disagreements |

Keep the smallest useful question record. An `origin`, open status, and concrete `next_action` are enough initially. Add evidence, reading, support, and report location only as the work happens. A reusable answer can live in one note referenced by `answer_note`; do not duplicate it in the question. New discoveries extend the map. Excluding or narrowing a requirement needs a reason; lack of evidence does not justify erasing it.

### Challenge the map before the report is finished

Give a fresh examiner the original research question and independent source access, withholding the draft, notes, and current map. Ask it to derive concrete missing-topic candidates from source structure: a neglected phase, an alternative mechanism, a geographic distinction, or a causal link. Each candidate needs the source URL and a source-specific basis. A generic request to find omissions is insufficient.

Seal those candidates with `run audit-seal` before comparing them with the existing work. Then inspect the map and use `run audit-resolve` to map each candidate to an existing or newly added question, or explain its exclusion. Give valuable unanswered questions a reachable next action before continuing research. The seal preserves order and content, not the examiner's independence or the truth of its judgment.

When fresh context is unavailable, use independently selected sources in a separate pass, record method `self`, and disclose that the examiner already knows the study. Do not describe this as blind review. Budget delegated work within the task's total limits and record its elapsed time and available consumption.

### Read and integrate coherent batches

Inspect actual returned text: selected lines, navigation, or a PDF extraction can omit the needed context. For a suspect capture, fetch surrounding content, use an accessible alternative, or narrow the claim. Record the remaining access condition if none succeeds. A source inaccessible in this run may still settle the historical question; do not turn access failure into an unresolved scholarly dispute.

Preserve details that change interpretation: actor or speaker, date and phase, place or population, edition or version, units, method, and source origin. Retain useful small details and connections alongside addressable passages; do not replace sources with an exhaustive list of atomic claims. Search with terms and variants found while reading, and follow consequential secondary citations to their origins when feasible. Copies of one account are one evidence family.

Use `read-many` for bounded passage groups and `batch` for capture, reading, note, and map operations in a coherent checkpoint. The [CLI contracts](artifact-contracts.md) include a worked sequence. Inspect output before declaring it read; a batch that hides truncated text has saved no understanding. Submit only changed records with `run patch`. Separate tasks are useful for substantial work or handoffs, not mandatory duplicates of every question.

### Choose the next investigation

Use `run status` to inspect questions, capture recovery, audit comparisons, and blocked work. Prioritize the action that can improve the answer: resolve a required gap, check a consequential uncertainty, explain a relationship, or inspect an independent candidate. Another source repeating an established claim is low value.

Keep these stages separate: evidence exists; relevant context was read; an answer is supported; the report communicates that answer. Finishing a reading task cannot complete the other stages. If sources support the events but not their relationship, retain an explanatory gap instead of covering it with a chronology.

After a material correction, inspect dependent notes and explanations. Reuse completed reading and unchanged records. Reserve time for synthesis and review; adding sources until the delivery deadline is not a stopping rule.

### Synthesize and check

Organize the report around the requested explanation. Connect evidence to mechanisms, consequences, relationships, and significant alternatives. Attribute interpretations and label inferences; do not invent causality to satisfy a question.

Compare the draft with the preserved questions and sealed candidates. Mark report transfer only where the actual answer appears, using a specific `report_anchor`. A heading or cited paragraph alone does not establish that all parts were answered. Reopen consequential claims and inspect their semantic support using [evidence and quality](evidence-and-quality.md).

## Focused follow-up

Find the intended workspace and version. Search retained notes and sources, then reopen supporting passages. Use quoted phrases, source/kind filters, or all-term matching; broaden to variants and neighboring passages before declaring evidence absent.

Answer directly when retained material suffices. Save only a new reusable connection or correction. Investigate missing parts if authorized, updating affected branches; do not rerun comprehensive mapping, acquisition, and report production for a small question. Distinguish an answer recovered from existing material from one completed through new research.

## Recovery after interruption

Inspect `run status`, then use `run resume` to reopen interrupted or invalidated work. Reconcile worker artifacts, verify the current scope and source revisions, and inspect unanswered requirements even if no task is pending. Resume the earliest affected work, preserving useful completed reading. Before a handoff, retain the next action and any access or resource condition.

## Stop with a justified scope

Complete within scope when necessary reading, required answers, explanatory connections, report transfer, and substantive checks are adequate. Open-topic research can stop when additional accessible literature mainly repeats established knowledge and meaningful alternatives have been examined.

Keep the result partial when central evidence, coverage, or required checking remains missing, or the resource limit stops the work. State the gap, its effect on the answer, and the next useful investigation. Structural verification is an integrity check, not a research-quality score.
