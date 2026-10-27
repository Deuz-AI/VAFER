# VAFER — Ultra Deep Research

Version **0.0.3**. “Ultra HQ” is the research-quality target, not an earned rating.

A portable research skill for Codex and Claude Code. It builds a detailed, source-linked understanding of a subject that remains useful for later questions: primary material, small details, relationships, context, competing interpretations, and known gaps.

The skill combines an adaptive research method with a local evidence store. It uses the host's existing search, browser, file, and agent capabilities. It does not require a new paid API, a custom MCP server, or global agent configuration.

## What it does

- Studies a finite core work in full when that work is the agreed research object; records partial reading honestly.
- Expands through diverse secondary sources and follows important references to their origins.
- Retains detailed contextual notes and addressable source passages instead of relying on one compressed summary.
- Checks the coverage map against independently gathered material, including neglected subtopics.
- Separates facts, interpretations, synthesis, and unresolved questions.
- Supports comprehensive study, focused follow-up, and recovery after interruption.
- Distinguishes completion within an explicit scope from a useful but partial result.

The local helper surfaces unfinished coverage and gaps as next actions, separates blocked work, flags suspect source captures, and supports quoted-phrase and source-filtered search. Its search cache updates changed records incrementally. Batched passage reads share source metadata, and CLI responses expose local execution time for measurement. These implementation improvements are covered by offline tests; they are not a measured claim of faster or better open-web research.

Version 0.0.3 adds answerable subquestions with separate evidence, context,
support and report-transfer records; source-derived gap candidates sealed before
map comparison; and small ID-based updates. Reading checkpoints can ingest,
read and record several sources in one CLI invocation using returned references.
An open-topic study can use enough context to support its claims without treating
every cited book as an agreed whole-book assignment. Old schema-1 records remain
readable; their broad coverage flags do not become semantic certifications.

It is intended for substantial research. A quick lookup or a routine summary does not need the full workflow.

## Install in a project

Copy the entire `skills/ultra-deep-research` folder from this repository into the research project:

| Host | Destination in the research project | Explicit invocation |
| --- | --- | --- |
| Codex | `.agents/skills/ultra-deep-research/` | `$ultra-deep-research` |
| Claude Code | `.claude/skills/ultra-deep-research/` | `/ultra-deep-research` |

Keep `SKILL.md`, `references/`, `scripts/`, and `agents/` together. Start a new host session if the copied skill is not discovered. The shared instructions contain the workflow; `agents/openai.yaml` only supplies Codex interface metadata. Copying the skill does not install dependencies, create custom agents, or change global settings.

The local helper needs Python 3.11 or later. From the research project, check the copied helper:

```text
python .agents/skills/ultra-deep-research/scripts/research.py doctor
```

For Claude Code, substitute `.claude/skills` for `.agents/skills`. The doctor output reports local capabilities; it cannot inspect the host's search, browser, or delegation tools. Text and Markdown are the basic interchange formats. Format-specific parsing is optional; see [artifact contracts and CLI](skills/ultra-deep-research/references/artifact-contracts.md) for supported inputs and limitations.

## Use

Ask in the language you want the research delivered in. For example:

```text
Use $ultra-deep-research to study this work in depth. Cover its structure,
minor figures, recurring motifs, historical context, competing readings,
translations, and influence. Preserve evidence for detailed follow-up questions.
```

```text
Use $ultra-deep-research to continue the existing research workspace.
Check unfinished work and changed sources before resuming.
```

```text
Using our existing research, explain this overlooked connection and show
the passages behind it. Research further only where the current material is thin.
```

Research data belongs in a topic workspace such as `research/<topic>/`, outside the installed skill. The detailed report and supporting records stay there; the chat response should identify the result, its scope, and significant remaining gaps.

Existing subscription tools may still consume the host's usage allowance. “No required paid API” does not mean unlimited or cost-free model execution. If search or delegation is unavailable, the skill adapts to accessible material and sequential work, then reports the reduced capabilities.

## Repository

```text
skills/ultra-deep-research/
  SKILL.md
  agents/openai.yaml
  references/
    research-workflow.md
    agent-protocol.md
    evidence-and-quality.md
    artifact-contracts.md
  scripts/
    research.py
    requirements-extract.txt
    vafer/
      batch.py
      store.py
      extract.py
      planning.py
      search.py
```

`research.py` is the local entry point. It handles source capture, passage references, note storage, and run state. The model performs reading, interpretation, coverage decisions, and semantic verification. The helper does not conduct autonomous web research or certify that a statement is true.

## Limits and evaluation

From the repository root, run the offline contract and extraction tests:

```text
python -m unittest discover -s tests -v
```

The [evaluation protocol](tests/evaluation.md) separates these executable checks from source-grounded behavioral trials. The included synthetic fixtures are development material, not an independent performance benchmark.

The [0.0.3 validation record](tests/v003-validation.md) retains all twelve assigned
live-research outcomes. Nine reports were available and scored 95–100 under the
fixed rubric, but three missing reports and four time-cap violations prevented
acceptance. The speed target was not established. All 113 offline tests passed;
this does not earn the “Ultra HQ” label or establish research superiority.

Tests cover the public CLI, document extraction, and recovery under simulated interrupted writes. Optional parser tests are skipped when their dependencies are absent. The shared skill format and project installation paths support both hosts; a full live Claude Code study has not yet been evaluated.

The skill cannot promise exhaustive knowledge of an open-ended field. A readable file may still be an incomplete capture; a source may be mistaken; several websites may repeat one original account. Mechanical reference and quotation checks do not establish that a source entails a claim. OCR, inaccessible material, missing host capabilities, and limited time can require a partial outcome.

There is no measured claim that this skill outperforms another research system. A useful comparison with Hyperresearch should pin its commit and this repository's commit, then give both the same tasks, source-access conditions, model capabilities, and resource limits. Keep test questions separate from the research authors. Include small-detail retrieval, cross-source explanation, competing interpretations, misleading premises, and interruption recovery. Record citation support, coverage gaps, incorrect claims, follow-up performance, time, and actual available usage data. Compare both fixed-corpus and open-web tasks, and publish failures alongside strengths.

The design review used Hyperresearch commit [`9c16854fed2d345a557e8759156a2ca5d02fa4f4`](https://github.com/jordan-gibbs/hyperresearch/tree/9c16854fed2d345a557e8759156a2ca5d02fa4f4). That review is architectural context, not a benchmark result or a claim of equivalent behavior.
