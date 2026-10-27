# Agent protocol and host mapping

Use existing host capabilities. The skill defines responsibilities and artifacts; it does not create a new agent runtime or assume that Codex and Claude expose identical tool names.

## Capability check

At the start of a study, identify which capabilities are actually available:

| Capability | Use | Fallback |
| --- | --- | --- |
| Search | Discover public sources and terminology | Use provided documents, accessible references, and known source collections; report reduced discovery |
| Browser or source reader | Inspect pages and source context | Read accessible local files or public alternate copies; record inaccessible material |
| File access and Python | Maintain the local evidence store | Keep a clearly identified temporary host-level record; do not claim durable CLI verification |
| Delegation | Assign independent reading and review work | Perform roles sequentially; label the review as self-review |
| Format-specific parser | Extract addressable content | Use the host's document reader or a text capture; preserve capture completeness and original location |

“Available” means exposed and usable in this session, not mentioned in documentation. `doctor` checks the local Python environment only. Do not install packages, connect providers, or change global settings merely to make a preferred path available.

For Codex, use the session's available search/browser, shell, patch, and delegation tools. For Claude Code, use the corresponding available search/browser, file/shell, and task-delegation tools. Consult the live tool descriptions for exact invocation and limits. No custom agent names, model overrides, or per-agent permission controls are required by this skill.

## Responsibilities

- **Coordinator:** owns the scope, shared source/note/run records, task allocation, conflict resolution, and final integration.
- **Reader or topic investigator:** reads an assigned source or branch, captures contextual detail and relationships, and returns evidence-linked notes plus gaps.
- **Coverage auditor:** builds an independent view of the subject from reference material, then identifies absent or distorted areas in the current map.
- **Evidence reviewer:** checks whether important statements are supported by their actual passages and conditions; distinguishes real conflicts from scope differences.
- **Question examiner:** prepares source-grounded questions without seeing the report or coverage map, where the host can provide an independent context.
- **Synthesizer:** produces the requested integrated account from the checked records and reopens underlying passages when needed.

These are roles, not a mandatory roster. Combine roles when appropriate, but do not call an author checking its own work an independent review. Use fresh-context reviewers where independence contributes value. Do not prescribe a model or spawn count; respect the host's actual capacity and the user's resource limits.

## Assignment contract

Give each worker a bounded task with:

1. The user's research question and relevant scope/version requirements.
2. Its assigned source, structural units, or coverage question, and the gap it should resolve.
3. Existing source and note references, plus any prerequisite results.
4. The expected output and its owned workspace path.
5. Access constraints, available tools, and any explicit resource limit.
6. A request to distinguish reading completed, findings, interpretations, and unresolved gaps.

Pass enough context to avoid misreading the task. Do not paste the entire research history into every worker or hide information required for correct interpretation. For blind question generation, withhold the current report and map but provide the original question, permitted sources, and relevant scope.

## Worker return contract

Return concise coordination information and detailed artifacts:

- What was actually read, with source revisions and passage ranges or structural units.
- New supported details and source references; short exact quotations only where useful.
- Context needed to interpret those details, including speaker, edition, time, method, and limitations where relevant.
- Relationships to existing notes and any conflicting evidence or alternative interpretation.
- Which assigned questions remain unanswered, their next useful action, and any access or dependency blocker.
- The artifact path and whether the assigned work is complete or partial.

Do not convert an unvisited URL, a title, or a search snippet into a claim of full reading. Do not fill a required-looking field with invented evidence.

For newly acquired material not yet in the canonical store, return its local capture path, origin metadata, completeness, and original locators. The coordinator ingests it and obtains canonical references before committing evidence-linked notes. Workers must not invent references to material that has not been ingested.

## Shared-state discipline

Workers own separate task outputs. The coordinator validates and merges them through the local helper. Only the coordinator commits canonical sources, notes, and run updates; this avoids competing updates to shared metadata or SQLite state. Workers may inspect existing records but must not rewrite another worker's artifacts.

Choose non-overlapping assignments where possible and share newly discovered source identities before duplicate acquisition. Integrate returned work at useful checkpoints: ingest captures, commit coherent notes, and update the linked questions/actions together. A completed worker task may still leave its coverage question open. The coordinator remains responsible for these links and resolving inconsistent versions or terminology.

Delegation is limited to the current research task. Do not create user-owned chats, send messages to external services, publish reports, or install tools as a side effect of research.

## Failure and constrained operation

If a worker fails, keep its useful artifacts, identify what is missing, and reassign or handle that bounded task. Repeating the same inaccessible fetch is not a research method. Seek an accessible legitimate copy or record the gap.

If the host has fewer simultaneous slots than independent tasks, schedule batches. If it has no delegation, run the same roles sequentially. Record which reviews were independent and which were self-review; reduced parallelism alone does not make a study invalid, but it changes the evidence for claims about independent checking.

Do not keep spawning when the user asks to stop or a specified resource limit is reached. Persist the achieved state and return an honest partial result with a useful continuation point.
