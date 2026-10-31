# Host notes (checked 2026-10-31)

Host tools change. When this file and the session disagree, trust the session.

## Preflight

Do this once, at the start of step 1; a Quick run on Codex does only the search-mode query.

- Resolve the absolute path of the skill folder. Briefs carry it, so the command works from any working directory.
- Pick the interpreter: the first of `python`, `python3` and `py -3` that runs `--version`. Paste it, with the absolute script path in double quotes, into every brief.
- Search mode: on Codex, run one dated query to tell live from cached search. Name the mode, live or cached search, in the first line of your first reply.
- Subagents: note whether you can spawn them and whether they have web access.
- Shell with network: note whether the shell can reach the web, so `fetch` can run.

The result sets the fallback mode and the host line.

## Host line

Open evidence.md with one line: host; search mode; shell, Python and network; subagents; file writes. For example: `Claude Code | WebSearch | shell+python+network | subagents | files`. It tells the reader which checks could run.

## Claude Code

- WebSearch returns titles, URLs and short written summaries. Summaries are leads, not receipts: open the page. An interactive session has 200 searches, shared with subagents.
- WebFetch returns a small model's answer about the page, not the page. Outside a short list of documentation sites it caps quotes at 125 characters and paraphrases the rest. It reads at most 100,000 characters, decodes every page as UTF-8 (so windows-1254 Turkish pages arrive garbled), splits table rows into cells and cannot read PDFs. Use it only when `fetch` fails, as it often does on JavaScript-only sites.
- Snapshots: `<python> "<absolute skill folder>/scripts/vafer_check.py" fetch` through Bash, one batch per message.
- Spawn fresh `general-purpose` subagents with the Agent tool; several calls in one message run in parallel. Spawns start in the background: after spawning, do the work you can (plan.md, folding verdicts), then end your turn; each reply arrives as a notification.
- Permissions: to avoid an approval prompt on every call, allow `WebSearch`, `WebFetch`, `Edit(.vafer/**)` and `Bash(<python> "<absolute skill folder>/scripts/vafer_check.py" *)`, written with the interpreter and path the preflight found (`py -3` included), or use auto mode. Only the text before the first `*` limits a rule, so a looser one such as `python*` allows any Python code. acceptEdits mode also covers the file writes.
- A user or managed setting can deny WebSearch or WebFetch for every agent. Then there is no web search: reply that the setting blocks research and name it.
- Headless `claude -p` needs a permission mode that allows the web tools.

## Codex

- web_search reads a cached index by default. Live results need `-c web_search="live"`. For recent topics, the preflight query tells the mode; state it in the host line, and in cached mode mark volatile receipts "as indexed".
- The workspace-write sandbox has no shell network by default, so `fetch` fails; `-c sandbox_workspace_write.network_access=true` enables it. `check` needs no network and still runs on the notes.
- Opened pages arrive as line windows. Copy receipt spans from the window; a window is normal, not a broken capture.
- Codex spawns subagents when asked in plain words: "spawn one researcher per assignment". Subagents inherit the sandbox and approval settings; under `codex exec`, any action that needs a new approval fails.
- Event loop: call `wait_agent` on all running ids, handle the first that finishes, `close_agent` it; at most 6 open.
- Default `codex exec` is read-only: no run folder and no script, so use mode D.

## Windows

The interpreter is usually `python` or `py -3`. Write notes only with the host's file tools, not shell redirection, so the encoding stays UTF-8.

The lookup `rg -i -l "<ascii terms>" .vafer/research --glob plan.md` works in PowerShell and in Git Bash, because rg expands the glob itself. A missing `rg` or a missing `.vafer` folder means no earlier run: continue without reuse.

## Fallback modes

Pick a mode at the start, update it when the gap-finder or a researcher replies NO_WEB, and name it in the host line.

- **A, full:** search, subagents with web access, writable folder, shell with network.
- **B, subagents without web:** search yourself, then give each researcher 5–10 URLs to read instead of queries.
- **C, no subagents:** run the briefs yourself in sequence (see the Variants section of briefs.md).
- **D, no file writes:** keep the plan and notes in the conversation, put receipts inline, re-open up to ten headline claims, deliver the report in chat, and say "nothing saved, no automated check".

## Older VAFER folders

Folders from VAFER 0.0.x (`research/<topic>/` with run.json, sources/ and notes/) and 0.1 runs with INDEX.md are plain files. Search them with rg or grep and treat their claims as leads that carry their original dates.
