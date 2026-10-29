# Host notes (checked 2026-10-28)

Host tools change. When this file and the session disagree, trust the session.

## Host line

Open the method note with one line: host; search mode; shell, Python and network; subagents; file writes. For example: `Claude Code | WebSearch | shell+python+network | subagents | files`. It tells the reader which checks could run.

## Claude Code

- WebSearch returns titles, URLs and short written summaries. Summaries are leads, not receipts: open the page. An interactive session has 200 searches, shared with subagents.
- When the skill itself runs inside a subagent, the harness may refuse a new file named report.md; write the draft under another name and rename it.
- WebFetch returns a small model's answer about the page, not the page. Outside a short list of documentation sites it caps quotes at 125 characters and paraphrases the rest. It reads at most 100,000 characters, decodes every page as UTF-8 (so windows-1254 Turkish pages arrive garbled), splits table rows into cells and cannot read PDFs. Use it to find and skim; take receipts from snapshots.
- Snapshots: `python scripts/vafer_check.py fetch` through Bash. If a site refuses the download, mark that page's receipts unverified rather than dropping them.
- Spawn fresh `general-purpose` subagents with the Agent tool; several calls in one message run in parallel. If they run in the background, integrate each result as it arrives instead of waiting for all.
- A user or managed setting can deny WebSearch or WebFetch for every agent. Then there is no web search: reply that the setting blocks research and name it.
- Headless `claude -p` needs a permission mode that allows the web tools.

## Codex

- web_search reads a cached index by default. Live results need `codex --search` or web_search = "live". For recent topics, test the mode up front with a dated query and state it in the host line; in cached mode, mark volatile receipts "as indexed".
- Opened pages arrive as line windows. Copy receipt spans from the window; a window is normal, not a broken capture.
- Codex spawns subagents when asked in plain words: "spawn one researcher per assignment, wait for all, then integrate their summaries". Subagents inherit the sandbox and approval settings; under `codex exec`, any action that needs a new approval fails.
- The workspace-write sandbox has no shell network by default, so `fetch` fails; `-c sandbox_workspace_write.network_access=true` enables it. `check` needs no network and still runs on the notes.
- Default `codex exec` is read-only: no run folder and no script. Say "nothing saved, no automated check" and use mode D.

## Windows

Run the script as `python` or `py -3`, not `python3`. Write notes only with the host's file tools, not shell redirection, so the encoding stays UTF-8.

## Fallback modes

Pick a mode at the start, update it when a researcher replies NO_WEB, and name it in the host line.

- **A, full:** search, subagents with web access, writable folder, shell with network.
- **B, subagents without web:** search yourself, then give each researcher 5–10 URLs to read instead of queries.
- **C, no subagents:** run the briefs yourself in sequence (see the Variants section of briefs.md).
- **D, no file writes:** keep the plan and notes in the conversation, put receipts inline, re-open up to ten headline claims, and deliver the report in chat.

## Older VAFER folders

Folders from VAFER 0.0.x (`research/<topic>/` with run.json, sources/ and notes/) and 0.1 runs with INDEX.md are plain files. Search them with rg or grep and treat their claims as leads that carry their original dates.
