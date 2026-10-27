---
name: ultra-deep-research
description: Build detailed, source-linked subject knowledge through comprehensive research, literature study, and close reading, with persistent evidence for follow-up questions and interrupted-work recovery. Use for substantial multi-source study or continuing an existing research workspace; not for quick lookups or routine summaries.
---

# Ultra Deep Research

Build source-linked understanding for the requested answer and later questions. Use the user's language, scope, destination, and resource limits. Records should change the next investigation or strengthen the answer.

## Choose the mode

- **Comprehensive study:** build answerable questions, investigate gaps, and explain findings. Read [research workflow](references/research-workflow.md#comprehensive-study).
- **Focused follow-up:** retrieve existing evidence and answer directly; investigate only missing parts. Read [focused follow-up](references/research-workflow.md#focused-follow-up).
- **Resume:** inspect open work, blockers, and changed inputs. Read [recovery](references/research-workflow.md#recovery-after-interruption).

For a plan or analysis-only request, stay at that level.

## Establish capabilities and state

Use existing host tools and accessible material; no new paid API, provider account, custom MCP server, or global configuration is required. Read [agent protocol](references/agent-protocol.md) before delegating or adapting to a missing capability.

Keep topic data in a separate workspace, such as `research/<topic>/`. Read [artifact contracts and CLI](references/artifact-contracts.md) before local operations. Check the helper once per environment:

```text
python <skill-directory>/scripts/research.py doctor
```

Capture sources once with provenance and returned references. Inspect the actual text and capture warnings. Recover missing context, find an alternative, or narrow the affected claim. A failed fetch is an access gap, not evidence of historical or scientific uncertainty.

If Python or writable storage is unavailable, disclose the limitation and retain useful host-level evidence.

## Let questions drive research

Before drafting, derive answerable questions from the user's request and independent source structure. Give each its `origin`; split broad branches where distinct mechanisms, places, periods, or alternatives require separate answers. Preserve unanswered questions as the map expands.

Before comparing against notes or the draft, have a fresh examiner derive missing-topic candidates from independent sources and seal them with `run audit-seal`. Then compare, add valuable gaps to the map with next actions, and record decisions with `run audit-resolve`. If fresh context is unavailable, do a separate source-driven pass and label it `self`; sealing alone does not establish independence.

Keep evidence found, context read, supported answer, and report transfer distinct. Reuse one answer or note instead of copying it across records. Explain mechanisms and relationships: correct dates or a valid citation do not answer a causal question. Read [evidence and quality](references/evidence-and-quality.md) for semantic checks and source independence.

Choose the next useful action with `run status`; blocked work stays visible. Use `batch` for coherent reading checkpoints and `run patch` for changed rows. Avoid per-study integration scripts and duplicate notes that add no reusable detail.

Declare `finite-work` when the selected work must be read in full. For `open-topic`, read enough context to evaluate the requested claims and explain source selection; an unconsumed literature universe does not automatically require `partial`.

## Deliver an honest outcome

Use `complete-within-scope` only when necessary reading, required questions, report transfer, and substantive review support it. Use `partial` for missing central evidence, answers, or checks, including resource stops.

Finalize the report before recording reviews; substantive changes invalidate them. Run verification and finish when local storage is available. Mechanical checks establish artifact integrity, not truth or research quality. Link the deliverable and state its achieved scope and material limitations.
