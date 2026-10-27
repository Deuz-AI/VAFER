# Host notes (checked 2026-10-27)

Host tools change. When this file and the session disagree, trust the session.

## Claude Code

- WebSearch returns titles and URLs only. An interactive session has 200 searches, shared with subagents.
- WebFetch returns a model-written extract of the page, not the raw page (up to 100,000 characters; cross-host redirects are returned, not followed). To check a quote, ask it for the exact sentence or NOT FOUND. For raw text, use curl through Bash when the session allows it.
- Spawn subagents with the Agent tool. Several calls in one message run in parallel.
- Subagents started from a Workflow can lack web tools. The NO_WEB reply covers that case.
- Claude Code also ships `/deep-research`, a workflow the user can run directly. This skill does not call it.

## Codex

- web_search reads a cached index by default. Live results need `codex --search` or web_search = "live". For recent topics, state in the method note which mode ran.
- Opened pages arrive as line windows. A window is normal, not a broken capture.
- Codex spawns subagents when asked in plain words: "spawn one researcher per assignment, wait for all, then integrate their summaries". Subagents inherit the sandbox and approval settings; under `codex exec`, any action that needs a new approval fails.
- The workspace-write sandbox has no shell network by default, so curl may fail. Continue with the search tool.

## Fallback modes

Pick a mode at the start, update it when a researcher replies NO_WEB, and name it in the method note.

- **A, full:** search, subagents with web access, writable folder.
- **B, subagents without web:** search yourself, then give each researcher 5–10 URLs to read instead of queries.
- **C, no subagents:** run the briefs yourself in sequence (see the Variants section of briefs.md).
- **D, no file writes:** keep the plan and notes in the conversation, deliver the report in chat, and skip INDEX.

## Older VAFER folders

Folders from VAFER 0.0.x (`research/<topic>/` with run.json, sources/ and notes/) are plain files. Search them with rg or grep and treat their claims as leads that carry their original dates.
