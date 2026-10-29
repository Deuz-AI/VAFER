# hyperresearch: hooks, ship gate, stop gate, tool locks, installation

Notes from reading the hyperresearch clone at `C:/Users/VECTOR/Documents/GitHub/hyperresearch`
(HEAD 327498b, 2026-10-26; package version 0.12.0, Codex support in `[Unreleased]`).
All paths below are relative to that clone unless they start with `VAFER/`.

## Scope and method

- Read in full: `src/hyperresearch/core/hooks.py` (4545 lines: about 3400 lines of agent
  prompt templates plus about 1000 lines of installer code), `cli/install.py`, `core/codex.py`,
  `core/platforms.py`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`.
- Opened because those files reference them: `cli/run_cmd.py` (stop-gate, verify, finish),
  `core/runs.py` (ship gate logic), `cli/lint.py` (quote-integrity, retracted-citations,
  skip-detection rules), `core/sync.py` (what gets indexed), `core/agent_docs.py`
  (CLAUDE.md/AGENTS.md), `core/render.py`, `core/vault.py`, `cli/setup.py`, `cli/main.py`,
  the entry skill `skills/hyperresearch.md`, step skills 5, 11, 14, the plugin bootstrap skill
  `skills/deep-research/SKILL.md`, tests for the stop gate, CHANGELOG, README.
- `C:/Users/VECTOR/Documents/GitHub/hyperresearch-sandbox` does not exist, so no generated install
  was available. I did not run the installer or the pipeline. Two static checks were run from my
  scratchpad (reading source text only, never importing the package): prompt sizes and which agent
  installers leave `{{` in the installed prompt. I also ran a one-line Python check of
  `json.loads` on a BOM-prefixed string.

## 1. What gets installed where

`platforms.py:58-75` holds the path table. `install.py` has four modes.

| Mode | Files written |
|---|---|
| `install .` (Claude, default) | `.hyperresearch/` (config.toml, hyperresearch.db, templates/) and `research/{notes,index,temp}` (`vault.py:139-196`); `CLAUDE.md` marked section (`agent_docs.py:299-353`); `.hyperresearch/hook.js` and `.claude/settings.json` PreToolUse entry (`hooks.py:3781-3828`); `.claude/skills/hyperresearch/SKILL.md` entry router (`hooks.py:4308-4331`); 18 step skills `.claude/skills/hyperresearch-N-*/SKILL.md` (`hooks.py:4359-4478`); 16 agents `.claude/agents/hyperresearch-*.md` (`hooks.py:3607-3634`); prunes retired agents and skill dirs (`hooks.py:4234-4288`); crawl4ai switch plus `playwright install chromium` subprocess (`install.py:324-381`) |
| first `install .` in a TTY, Claude only | diverts to the setup TUI (`install.py:206-214`), which writes the same files plus provider and login-profile config (`setup.py:115-156`) and ignores `--profile`/`--name` |
| `install . --target codex` | vault; `AGENTS.md` (about 1K tokens); `.codex/hooks.json` Stop entry `<hpr> run stop-gate` (`hooks.py:3959-3989`, `codex.py:289-328`); `.agents/skills/hyperresearch/SKILL.md` plus `agents/openai.yaml` with `allow_implicit_invocation: true` (`hooks.py:4334-4356`, `codex.py:271-279`); 18 plain step files `.hyperresearch/codex/steps/*.md` (`hooks.py:4481-4530`); 15 TOML agents `.codex/agents/*.toml` (no browser-fetcher, `hooks.py:3632-3633`), each `sandbox_mode = "workspace-write"` and `model_reasoning_effort` high for opus roles, medium otherwise (`codex.py:115-117, 252-264`) |
| `--global` | Claude: `~/.claude/skills/hyperresearch/` and `~/.claude/agents/` only, with no hook, vault, CLAUDE.md or step skills (`hooks.py:3691-3746`). Codex: `~/.agents/skills/hyperresearch/` and `~/.codex/agents/`; it never touches `~/.codex/config.toml` or hooks (`hooks.py:3700-3703`). On first use in a project the entry skill bootstraps `hyperresearch init .` and `install --steps-only .` (`skills/hyperresearch.md:106-110`; `install.py:98-133`) |
| plugins | `.claude-plugin/*` and `.codex-plugin/plugin.json` plus `.agents/plugins/marketplace.json` publish one bootstrap skill, `skills/deep-research/SKILL.md`. It checks the CLI, runs `hyperresearch install .` (or `--target codex`) mid-session, then hands off (`deep-research/SKILL.md:16-112`). The plugins ship no hooks and no agents. |

Notes on installation:
- The roster has 18 step skills (`hooks.py:4359-4378`), but the docs and help text say "16"
  throughout (`install.py:26,31`; `hooks.py:3710`).
- Global install users never get the PreToolUse hook. `install_global_hooks` skips it
  (`hooks.py:3705-3707`) and the `--steps-only` bootstrap does not add it (`install.py:98-133`).
- Codex global bootstrap writes the wrong docs file. `hyperresearch init` calls
  `Vault.init` with the default `platforms=("claude",)` (`main.py:16-26`, `vault.py:144,191-194`),
  so the project gets a CLAUDE.md, and `--steps-only` never writes AGENTS.md.
- The absolute CLI path from `_resolve_executable()` (`agent_docs.py:269-296`) is baked into
  CLAUDE.md, every skill, every agent and hook.js. If the venv moves, every installed prompt is
  stale until a reinstall.

## 2. Inventory: what is structural and what is only instructions

### Structural (code decides)

1. **Ship gate `run finish`** (`run_cmd.py:576-617`, `runs.py:847-879`). Runs `verify_run` and
   flips the manifest to `done` on pass or `blocked (verify)` on fail. It is the only path to
   `done`. Nothing forces anyone to call it on Claude Code.
2. **Codex Stop hook** (`codex.py:347-386`, `run_cmd.py:249-294`). Prints
   `{"decision":"block"}` while the newest run is `running`, was touched within 6 hours, and has a
   `next_step` in its manifest. Codex only.
3. **Claude PreToolUse hook** (`hooks.py:3557-3604`, `3815-3825`). Matcher `WebSearch|WebFetch`.
   It always exits 0 and injects a 703-character reminder as `additionalContext`. It never denies.
4. **Subagent tool allowlists** through `tools:` frontmatter (Claude Code only). See section 5.
5. **Count ceilings** `--max-sources/--max-notes` at `run step done` (`runs.py:381-396`). Opt-in;
   the entry skill does not pass them by default (CHANGELOG.md:9).
6. **Budget governor** (`runs.py:316-323`). Fires only if something calls `hpr run spend`. The
   authors say it "stays inert unless something calls `hpr run spend`" (CHANGELOG.md:9).

### Instruction-only (prompt text the model may ignore)

- Run every tier step; do not skip; triple draft and synthesizer are mandatory
  (`skills/hyperresearch.md:286-303`).
- "NEVER EMIT BARE TEXT WHILE TASKS ARE RUNNING", because on Claude `-p` a text-only reply ends
  the process and "the pipeline dies" (`skills/hyperresearch.md:180`). Claude has no Stop hook to
  catch this.
- "The gate's verdict is final... Maximum 3 rounds" (`skills/hyperresearch.md:274-281`).
- The spawn contract: verbatim query plus shim pasted unedited (`skills/hyperresearch.md:204-214`).
- Critics, cite-checker and readability recommender "never modify the report", but they hold
  Write, and critics and cite-checker also hold Bash.
- Every Codex tool lock: "Codex cannot enforce that list, so you must." (`codex.py:146-149`).
- Fetcher "Phase 2 MANDATORY" (`hooks.py:3152-3158`). Draft-orchestrator "VERIFICATION GATE: read
  every must_read id" (`hooks.py:2023-2028`). The orchestrator's own patch-not-regenerate rule
  (`skills/hyperresearch-14-patcher.md:119, 138`).

## 3. The ship gate in detail (`runs.py:649-844`)

| Check | What it really verifies | Gap |
|---|---|---|
| report-exists (668-669) | file at `research/notes/final_report_<tag>.md` | none |
| length-in-range (705-730) | `len(text.split())` within [low*0.8, high*1.2]; character-based for CJK | counts the Sources section and URLs too; skipped when `response_format` is missing from the decomposition |
| required-headings (732-737) | `h not in report_text`, a substring test | no order check; a heading string anywhere in the prose passes |
| citation-density (747-770) | `[N]`/`[N, M]` regex plus wikilinks over the **whole** text, floor 9 per 1000 words (`profiles.py:298`) | the inline-style `## Sources` list (`[1] Title. URL`, ...) counts toward density, so a 60-entry bibliography supplies about 60 of the roughly 68 citations a 7,500-word report needs; it does not check that `[N]` resolves to a source |
| no-scaffold-leak (772-776) | only `## User Prompt (VERBATIM` | the other 9 `SCAFFOLD_ONLY_SECTION_HEADERS` (`hooks.py:105-116`) are not checked |
| quote-integrity (783-806, `lint.py:110-147`) | each double-quoted span of 5 or more words FTS-phrase-matches some vault note | see below |
| retracted-citations (`lint.py:200-232`) | wikilink targets with `is_retracted=1` | inline `[N]` style is never checked (`lint.py:214` iterates `WIKI_LINK_RE` only) |
| tier artifacts (810-820) | `critic-findings-*.json` x4, `patch-log.json`, `polish-log.json` **exist** | existence only; the orchestrator pre-stubs patch-log and polish-log **before** spawning the agents (`skills/hyperresearch-14-patcher.md:53-59`, `skills/hyperresearch-15-polish.md:34`), and the `skip-patcher.txt` path writes patch-log without running the patcher (`14-patcher.md:36-49`) |
| cite-check-resolved (822-842) | only when manifest step 14.5 is `done`: findings exist, and a patch log exists if any finding is critical | skipping 14.5 entirely skips the check; it does not verify that the criticals were fixed |
| levers-rendered (691-703) | shim files exist when the decomposition declares levers | n/a |

What the gate never checks:
- Manifest step statuses, apart from the 14.5 condition. Steps 2-11, 13 and 16 can be skipped
  silently. Step 16 has no artifact check at all.
- The lint rules that do detect skips: `workflow` (scaffold, loci without interim notes,
  comparisons.md missing; `lint.py:1573-1640`), `locus-coverage` (`lint.py:1018-1085`),
  `patch-surgery` (critical findings skipped; `lint.py:1201-1290`) and `instruction-coverage`.
  All are error severity, but `verify_run` folds in only quote-integrity and retracted-citations
  (`runs.py:783-806`). The README advertises them as "structurally enforced" (README.md:323-330).

Quote-integrity specifics:
- The pattern matches only `"..."` and curly double quotes (`lint.py:98`). Single quotes, `«»`
  and CJK `「」` are never verified, and fewer than 5 words is skipped (`lint.py:124`).
- The match is vault-wide, not against the cited note (`lint.py:128-131`). Every synced note is
  in FTS regardless of type (`sync.py:309-313`), including LLM-written `interim` and
  `source-analysis` notes. A quote fabricated by a depth investigator in its interim note
  therefore passes when the report repeats it.
- The final report sits in `research/notes/`. If it carries YAML frontmatter, sync indexes it
  (`sync.py:89-100`), and the report then matches its own quotes. Frontmatter is normally
  stripped, but the polish auditor allows keeping it when "a wrapper requires it"
  (`hooks.py:1623-1642`). Many commands auto-sync, including citecheck (`citecheck_cmd.py:49`).
- The suggested fix is "Fix the quote or drop the quotation marks" (`lint.py:143-144`). The gate
  therefore enforces quotation-mark hygiene, not claim support.
- It is fail-closed on FTS exceptions (`lint.py:132-133`), which is good.

Why it exists (CHANGELOG.md:203): "the orchestrator never invoked `run verify` (a 25,647-word
report shipped against a 16K ceiling), and when lint flagged 24 hallucinated/mangled quotes it
wrote itself a 'false positives' memo and shipped anyway." Their fix made `finish` the only path
to `done` and folded the lints in. It did not make calling `finish` mandatory on Claude Code. A
second incident: for a period, 14 of 19 skills spelled the CLI `$HPR`, so `$HPR run finish` ran
as `run finish` and failed with command not found (CHANGELOG.md:27). The gate was silently absent.

## 4. The Codex stop gate in detail

Decision (`codex.py:347-386`):
- Look only at `list_runs(vault)[0]`, the newest by `started_at` (`runs.py:445-461`).
- Block only if `status == "running"` (`codex.py:342, 361`), `updated_at` is within 6 hours
  (`337, 363-371`), and `run_resume_position(...)["next_step"]` is not None (`373-375`).

Ways the gate goes silent:
- **No run yet.** If the model answers inline without `run init`, `list_runs` is empty and the
  gate returns None (`codex.py:357-359`). That is exactly the failure the hook was built for:
  "The Stop hook exists because an earlier Codex attempt answered inline and never touched the
  vault" (CHANGELOG.md:5). If an older run under 6 hours is still `running`, the gate instead
  pushes the model toward the wrong run.
- **Every step self-recorded as done or skipped.** `resume_position` treats `skipped` as done
  (`runs.py:489`). The gate is then silent even though `run finish` never ran, and the test
  `test_stop_gate_silent_when_all_steps_done` locks this in (`tests/test_core/test_codex_install.py:413-419`).
- **Any non-running status**: blocked (including a **failed ship gate**, `runs.py:871-872`),
  paused, aborted, failed, done (`codex.py:339-342`). `run abort` and `run block --on <anything>`
  are one-command exits (`run_cmd.py:297-317, 449-470`).
- **`stop_hook_active`** returns silently (`run_cmd.py:274-277`;
  `tests/test_cli/test_install_codex.py:203-206`). The gate forces at most one continuation per
  stop chain. If Codex follows Claude Code's semantics, that is one nudge per user turn, which in
  `codex exec` is the whole session. I did not verify Codex's exact semantics.
- **`HYPERRESEARCH_STOP_GATE=0`** (`run_cmd.py:265-266`), and any exception (`run_cmd.py:293-294`),
  which fails open by design.
- **Untrusted hooks.** In `codex exec` the hook runs only with `--dangerously-bypass-hook-trust`
  (README.md:123; `install.py:318-320`). The default non-interactive run has no gate.
- `run resume` flips any `blocked` (verify or budget) or `paused` run back to `running`
  (`run_cmd.py:203-208`), which contradicts "budget/verify blocks keep their existing behavior"
  (`runs.py:76-78`). The router tells a confused orchestrator to run `resume` first
  (`skills/hyperresearch.md:222`).

Net: the stop gate enforces "keep recording steps in the manifest", not "pass the ship gate".
It costs one Python CLI start per stop attempt. It never wedges a session, which is a good
property.

## 5. Tool locks

| Agent (Claude `tools:`) | Line | What the lock really prevents | What the prompt claims |
|---|---|---|---|
| patcher: Read, Edit | `hooks.py:1374` | creating or overwriting files, shell, spawning | "enforced at the tool level" (1378-1381), but it also admits "The tool lock doesn't prevent this (Edit will accept any old_string/new_string pair...)" (1408-1411) |
| polish-auditor: Read, Edit | 1551 | same | same |
| synthesizer: Read, Write | 2117 | shell and spawning; it cannot count words mechanically, yet is told to "Count your words before finishing pass 2" (2311-2314); the orchestrator does the real count at step 11.7 (`11-synthesize.md:226,235`) | "Cannot Bash, cannot spawn subagents" (true) |
| readability-recommender: Read, Write | 2554 | shell and Edit, but **Write can overwrite the report** | "You do NOT modify the report" (2560) |
| 4 critics: Bash, Read, Write | 637, 771, 889, 1049 | nothing relevant; Bash and Write can rewrite the draft | "You do NOT have Edit tools. You cannot modify the draft." (654-655) |
| cite-checker: Bash, Read, Write | 3483 | nothing relevant | "Never edits the report" |
| fetcher: Bash, Read, Write, WebSearch | 2965 | WebFetch (structural) | n/a |
| depth-investigator: Bash, Read, Write, Task | 348 | nothing; told "Do NOT call fetch directly. Delegate to hyperresearch-fetcher via the Task tool" (443-445). Claude Code's docs, as I recall, say subagents cannot spawn subagents; if so this instruction cannot be followed on Claude. Not verified here. | n/a |
| draft-orchestrator: Bash, Read, Write | 1912 | spawning; the comment at 1898 says "Full tool access including Task", which is stale | n/a |
| browser-fetcher: Bash, Read, Write, ToolSearch | 3358 | possibly the Chrome MCP tools themselves, since they are not in the allowlist. Whether ToolSearch can surface MCP tools through an explicit `tools:` allowlist is unverified. | n/a |

- On Codex there are no locks. The `tools:` line becomes prose through `_tool_discipline`
  (`codex.py:137-190`) and every agent gets `sandbox_mode = "workspace-write"` (`codex.py:261`).
  The authors say so: "the Read+Edit tool locks are instructions rather than enforcement"
  (CHANGELOG.md:5; README.md:135).
- README.md:206 says "Per-hunk caps make 'just rewrite it' mechanically impossible", and
  CHANGELOG.md:395 says "Every hunk is capped at 500 chars of net expansion". No cap exists in the
  code or prompts (I grepped for it). README.md:327 says "Steps 14, 15, 16 are tool-locked to
  [Read, Edit]", but step 16's agent is Read, Write, and the orchestrator applies its
  recommendations with full tools.
- The orchestrator (main session) is never locked. Step 14 explicitly says "(you have Write/Edit
  access; the lock applies only to the patcher subagent)" (`14-patcher.md:119`).
- Real value of the patcher and polish locks on Claude: a patch pass cannot wholesale-rewrite the
  synthesized report, so the critic-driven edits are layered on the synthesizer's text rather than
  replacing it. That is the only lock that plausibly protects report quality.

## 6. How a run is (not) prevented from skipping steps

Claude Code:
- Step procedures load fresh per step through the Skill tool (`skills/hyperresearch.md:49-57`).
  This is the strongest anti-skip mechanism and it is about context, not enforcement. Their
  evidence: V7's single 1200-line skill was compacted away, the model "silently dropped Layer 3.7
  ... replace[d] the triple-draft ensemble with a single draft" "in 100% of runs where the
  orchestrator didn't re-read the skill file" (`skills/hyperresearch.md:307-309`). Q57 scored 55.9
  with the full pipeline and Q9 scored 52.6 with the single-draft fallback (line 327).
- TodoWrite plus the manifest (`run step`) are memory aids. They are self-reported.
- Ship gate artifact checks catch only missing critic, patch and polish files, and the
  orchestrator pre-stubs two of those itself.
- No Stop hook. Nothing structural ensures `run finish` is ever called.

Codex:
- Same, plus the stop gate (section 4), which keys off the self-reported manifest.

## 7. Windows behavior

Claude Code on Windows uses Git Bash for its Bash tool, so POSIX syntax in prompts works.
Problems:
1. **`.claude/settings.json` data loss.** `_install_claude_hook` reads with `encoding="utf-8"`,
   swallows `JSONDecodeError` and continues with `{}` (`hooks.py:3799-3804`), then writes the file
   back with only its hook (3827). A UTF-8 BOM, which Windows PowerShell 5.1 `Set-Content
   -Encoding UTF8` writes, makes `json.loads` raise "Unexpected UTF-8 BOM" (checked locally). The
   user's permissions, hooks and env in that file are then replaced by the hook alone. The Codex
   path refuses in the same situation, with the comment "overwriting it would destroy them"
   (`hooks.py:3971-3981`).
2. **Corpus-critic gets backslash paths.** `CORPUS_CRITIC_AGENT.replace("{hpr_path}", hpr_path)`
   uses the raw `_resolve_executable()` path (`hooks.py:4155`). Every other installer converts to
   forward slashes first, because "bash on Windows eats backslashes" (`agent_docs.py:311`). The
   step-8 agent's two CLI commands become `C:\Users\...\hyperresearch.exe`, which bash mangles.
3. **The CLI path is substituted unquoted** into every skill and agent prompt (`hooks.py:69`). A
   user directory with a space (`C:/Users/First Last/...`) splits every `{hpr_path} ...` command.
   The hook script path was quoted after #98 (CHANGELOG.md:113); the prompts were not.
4. **The hook needs `node` on PATH** (`hooks.py:3823`). Claude Code's native installer does not
   need Node; without it every web call shows a hook error.
5. **`.claude/settings.json` stores an absolute hook path.** Moving or cloning the project breaks
   it, and reinstalling never repairs it, because any command containing "hyperresearch" counts
   as already installed (`hooks.py:3809-3813`; acknowledged in CHANGELOG.md:113).

Codex on Windows uses PowerShell for its shell, which `codex.py:128` acknowledges with
`Get-Content`. Problems:
6. **25 agent-prompt commands use `PYTHONIOENCODING=utf-8 <exe> ...`** (counted in `hooks.py`;
   `hooks.py:3044` says "On Windows, ALWAYS prefix..."), plus 2 in step files. That is POSIX
   env-prefix syntax, and PowerShell treats `PYTHONIOENCODING=utf-8` as a command name, which
   fails. The prefix is also redundant, because the CLI already reconfigures stdout and stderr to
   UTF-8 (`cli/__init__.py:20-29`, `_output.py:26-38`).
7. Stubs written with `echo '{...}' > file` (`14-patcher.md:58`, `15-polish.md:34`) produce
   UTF-16LE under Windows PowerShell 5.1. `lint.py:1209` reads patch-log as utf-8. This depends
   on which PowerShell Codex uses, which I did not verify. `for f in ...; do test -f` loops
   (`skills/hyperresearch.md:254-261`) are bash-only.
8. **Stop hook command.** It is quoted only when the path contains whitespace, and the code
   itself notes that "a quoted leading token is a parse error in PowerShell" (`codex.py:292-299`).
   If Codex runs hooks through PowerShell, which I did not verify, the gate silently does nothing
   for users with spaces in their path.

## 8. Other fragility

- **Unescaped `{{ }}` in installed prompts.** `_install_instruction_critic_agent` and
  `_install_readability_reformatter_agent` apply no `.format()` (`hooks.py:4063-4072, 4106-4129`),
  even though the comment claims "the .format() call is harmless". `_install_corpus_critic_agent`
  uses `.replace` (4155). The installed instruction-critic (4), readability-recommender (4) and
  corpus-critic (2) prompts therefore show doubled-brace JSON examples (`{{ "findings": [ {{ ... }}`).
  I confirmed this statically. Low impact, because models usually de-escape, but it raises the
  odds of malformed output JSON. The golden tests pin the pre-`.format` render, so they cannot
  catch this (`tests/test_core/test_prompt_golden.py:171-179`).
- **Bootstrap and manifest commands use the bare `hyperresearch` name**: `init`,
  `install --steps-only`, `vault-tag`, `run init`, `run step` and `run resume`
  (`skills/hyperresearch.md:107-127, 222`). Only the gate uses `{hpr_path}` (line 269). CLAUDE.md
  warns the CLI "may not be on your system PATH" (`agent_docs.py:29`). If it is not on PATH,
  `run init`/`run step` fail, which breaks both resume and the Codex stop gate. The step-5 spawn
  template also uses bare `hyperresearch note show` (`5-depth-investigation.md:63`).
- **Mid-session install versus session-start loading.** The plugin bootstrap installs
  `.claude/agents/*` mid-session, and its own text says "Claude Code loads new subagents at
  session start" (`deep-research/SKILL.md:66-73`). It only checks that the skill is available.
  If the subagent types are missing in that first session, the `subagent_type: hyperresearch-*`
  spawns (`11-synthesize.md:153`, `14-patcher.md:73`, ...) have no fallback, and the tool locks
  disappear if the model improvises with general agents. Whether this happens depends on the
  Claude Code version.
- **Version skew.** The Codex plugin manifest says 0.12.0 (`.codex-plugin/plugin.json:3`), the
  same as the package (`pyproject.toml:7`), but `--target codex` is `[Unreleased]`
  (CHANGELOG.md:5). A `pip install hyperresearch` from PyPI may lack `--target`. I did not check
  PyPI.
- **Stop gate scope.** The gate uses the vault's newest run, not this session's run, so
  concurrent sessions in one vault can block each other.
- **Fragile idempotency check.** Claude hook detection is a substring match on "hyperresearch"
  (`hooks.py:3812`), and an `h` that is not a dict crashes the installer.
- **Process-global render state** (`hooks.py:32-52`). The per-file installers infer the platform
  from global state set by the last `_set_render_state`. That is correct today and easy to break.
- **Benchmark tuning in enforcement prompts.** "Reports that are significantly longer than
  reference norms score LOWER ... top-performing reports average 45-55KB"
  (`hooks.py:991-994`). The critics are tuned to RACE dimensions (`hooks.py:1244-1248`). Gate
  numbers such as length and density encode a benchmark's preferences, not the reader's.

## 9. Cost of this subsystem

Measured from the source text; tokens are approximated as chars/4.
- CLAUDE.md blurb: 12,529 chars, about 3.1K tokens, loaded in **every** Claude session in the
  project, research or not (`agent_docs.py:25-205`). Codex AGENTS.md blurb: 4,113 chars, about
  1K tokens.
- Skill listing: all 19 skill frontmatters total 13,925 chars, about 3.5K tokens, listed per
  session. The authors estimate about 3K tokens of "system-reminder noise" (`hooks.py:3710-3715`).
  On top of that, 16 agent descriptions appear in the Task tool listing.
- PreToolUse reminder: about 175 tokens and one `node` process per WebSearch/WebFetch call,
  including fetcher subagents' WebSearch calls (project hooks apply inside subagents). Inside a
  fetcher the reminder's "use subagents to fetch in parallel" (`hooks.py:3593`) cannot be
  followed, because fetchers have no Task tool.
- Ship gate: one local CLI call, plus up to 3 fix rounds. The length failure path re-spawns the
  synthesizer for a compression rewrite (`skills/hyperresearch.md:276`), which is the most
  expensive single remedy.
- Manifest bookkeeping: 2 CLI calls per step (`running`, `done`) for about 17 steps; each `done`
  also reconciles counts from SQLite (`runs.py:296-297`).
- Agent prompts total about 163K chars (about 41K tokens) across 16 templates. The biggest per
  spawn are the synthesizer (23.5K chars), polish auditor (17.3K) and instruction critic (16.2K).
  The entry skill template is 32K chars (both platform branches; the rendered size is smaller).
- First install may download Chromium through Playwright or Patchright (`install.py:367-381`).

## 10. Ideas for VAFER

Adopt:
- One terminal gate command that is the **only** way to mark a run complete and records the
  verdict durably. Add a bounded fix loop (3 rounds) and the "change the report, never
  re-interpret the gate" rule.
- A Stop hook **on Claude Code too**, keyed on "gate passed" (or an explicit, user-visible abort),
  not on "next step is None". Keep their safety properties: an env-var off switch, fail-open on
  exceptions, a staleness window, and a guard against infinite loops.
- Step procedures as files read on demand, the Codex layout, on both platforms. That means no
  skill-listing tax and no dependence on skill hot-reload, while keeping the fresh-procedure
  benefit.
- Edit-only patch agents on Claude Code (Read, Edit). This is the one lock with real quality
  value: critic edits cannot become regeneration.
- A verbatim-quote check, but scoped to the **cited source's fetched text**, excluding
  LLM-authored notes and the report itself, and covering single, curly and CJK quotes.

Adapt:
- Replace existence-only artifact checks with content checks: findings files schema-valid, patch
  log entries count equal to the sum of findings, report hash changed between steps 11 and 14 if
  any finding was applied, and never satisfiable by orchestrator stubs.
- Derive step completion from verified artifacts, not from `run step` self-reports. Fold the
  skip-detection lints (loci without interim notes, missing comparisons, skipped criticals) into
  the gate.
- Compute citation density over the body only, and check that every `[N]` resolves to a listed
  source and every listed source is cited.
- Check retractions for every citation style.

Avoid:
- Overwriting user settings on parse failure. Read with `utf-8-sig` and refuse on error.
- Baking an absolute, unquoted CLI path into every prompt. Use one quoted invocation (for example
  `python -m vafer`) or a project-relative wrapper.
- POSIX-only syntax (`VAR=x cmd`, `echo > file`, `for/test` loops) in prompts that can run under
  PowerShell. Write stubs through the CLI instead.
- Recovery commands that silently clear budget or verify blocks.
- An always-loaded footprint (a 3K-token CLAUDE.md block plus 18 listed skills) in every session
  of a project.
- Claiming locks that do not exist (critics "cannot modify the draft", "per-hunk caps") in docs
  or prompts. It misleads both the model and the user.
- Reminder-only hooks for rules that matter. Either deny, with a reason, or do not hook.
- Installing agents mid-session and assuming they are spawnable; ship them so they load at
  session start, or fall back explicitly.

## 11. Open questions (not verified here)

- Does Codex reset `stop_hook_active` within a turn? This decides whether the gate gives one
  nudge per session or more.
- Do Claude Code subagents get a working Task tool? This decides whether the depth-investigator's
  "delegate via Task" instruction is followable.
- Can an explicit `tools:` allowlist reach MCP tools through ToolSearch? This decides whether the
  browser-fetcher can work at all.
- Which shell does Codex use for hooks and commands on Windows, PowerShell 5.1 or 7?
- Is PyPI 0.12.0 missing `--target`?
