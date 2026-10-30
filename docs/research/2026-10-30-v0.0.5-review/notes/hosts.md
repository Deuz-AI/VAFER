# Host capabilities for v0.0.5 (checked 2026-10-30)

What Claude Code and OpenAI Codex can do today that matters for vafer-research and a two-skill VAFER suite. Sources: official docs read on 2026-10-30; Claude Code 2.1.314 and codex-cli 0.164.0 installed on this machine; openai/codex source on main (latest release 0.166.0, 2026-10-29). Tags: VERIFIED (with source) or UNVERIFIED.

## Summary

Both hosts can run a faster two-skill VAFER without new infrastructure. In Claude Code 2.1.314, the lead can choose a model alias and an effort level for each researcher it spawns, and up to 20 subagents run in the background. WebSearch has a new "extended" mode, WebFetch can continue a long page from an offset, and skills get `${CLAUDE_SKILL_DIR}`. Codex spawns subagents by default, but runs at most 6 at once and they cannot spawn their own. Its spawn call accepts `model` and `reasoning_effort`. Web search defaults to a cached index, and `codex exec --search` is rejected. One repository can ship both skills as a plugin to both hosts: Codex falls back to `.claude-plugin/marketplace.json` and `plugin.json`, both hosts name plugin skills `vafer:<skill>`, and the version lives in plugin.json. On Claude Code the baseline to beat is the bundled `/deep-research` workflow. Codex CLI has no built-in deep research.

## Findings

**F1. Claude Code: the lead can set each researcher's model and effort with one sentence.**
- VERIFIED: the Agent tool accepts a `model` alias for each spawn (`sonnet`, `opus`, `haiku`, `fable`) and, from v2.1.292, an `effort` level.
  - Order of precedence: the per-spawn value, then the agent file, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model.
  - Agent files in `.claude/agents/`, `~/.claude/agents/` or a plugin's `agents/` can set `model`, `effort`, `tools`, `maxTurns`, `skills` and `omitClaudeMd`.
  - Source: code.claude.com/docs/en/sub-agents.
- VERIFIED: the aliases resolve to Sonnet 5.5, Opus 5.5 and Haiku 5.5, all with `medium` effort by default (docs/en/model-config). Haiku 5.5 costs $0.10/$0.50 per million tokens (CHANGELOG 2.1.293).
- Implies: "spawn researchers with model sonnet" needs no agent files. Its effect on accuracy is unmeasured, so test it.
- Confidence: high.

**F2. Claude Code: limits, background runs and what a subagent inherits.**
- VERIFIED: up to 20 subagents run at once. One more spawn fails with "Concurrent subagent limit reached", and Claude is told not to retry.
- VERIFIED: subagents can nest 3 layers deep.
- VERIFIED: spawns start in the background. With fork mode on (the default from v2.1.302), an interactive lead cannot wait, and results arrive as notifications.
- VERIFIED: background subagents keep WebSearch, WebFetch, Bash, Read, Write, Skill and Monitor. `Workflow` is always removed.
- VERIFIED: a subagent that is not a fork starts fresh.
  - It gets its own system prompt, the task message, the CLAUDE.md hierarchy, a git snapshot and preloaded skills.
  - It does not get the conversation or the files already read.
  - Source: sub-agents page.
- Implies:
  - Standard and Deep each fit in one wave.
  - Keep "integrate each result as it arrives" (hosts.md:15), and keep the brief as the only carrier of the question, the date and the paths.
  - A lead running inside a subagent cannot start a workflow.
- Confidence: high.

**F3. Codex: subagents are on by default, but at most 6 run at once and they cannot spawn their own.**
- VERIFIED: the multi-agent tools are stable and on: `spawn_agent`, `wait_agent`, `close_agent` and others. Codex delegates when "project or skill instructions request it".
- VERIFIED: custom agents are TOML files in `.codex/agents/` and can set `model` and `model_reasoning_effort`. They cannot override the sandbox or approvals.
- VERIFIED: subagents inherit the sandbox, approvals and skills. The docs suggest `gpt-6.1-sol` for demanding agents and `gpt-6-luna` for "fast, narrowly scoped" ones. (learn.chatgpt.com/docs/agent-configuration/subagents)
- VERIFIED (source, `core/src/config/mod.rs`): `DEFAULT_AGENT_MAX_THREADS = Some(6)` and `DEFAULT_AGENT_MAX_DEPTH = 1`. An extra spawn fails with "agent thread limit reached". The cap counts threads that are open at the same time.
- VERIFIED (source, `multi_agents_spec.rs`):
  - The default spawn tool (v1) takes `model`, `reasoning_effort` and `fork_context`. When `fork_context` is omitted, the agent starts with only its prompt.
  - Spawn v2 (stable but off in 0.164.0) inherits the parent's full history by default. It also tells the model not to set `model` "unless the user explicitly asks".
- VERIFIED (source, `core-plugins/src/manifest.rs`): Codex plugins cannot ship agents, because the manifest has no `agents` field.
- UNVERIFIED: whether subagents get web search in a live run. Their config is copied from the parent's (`child_config.rs`).
- Implies:
  - Launch at most 6 at a time: 6 sections plus the gap-finder need two batches, or `close_agent` in between.
  - Say "start each researcher without the parent's history".
  - Ask for a researcher model in plain words; v2 may ignore the request.
- Confidence: high for the defaults, medium for v2 behavior.

**F4. Claude Code WebSearch: a new extended mode, and a budget that refills.**
- VERIFIED: returns titles and URLs, with up to 8 backend searches per call, and `allowed_domains` or `blocked_domains`.
  - An interactive session has 200 searches, shared with subagents.
  - From v2.1.290 the budget refills at about 100 per hour; under `-p` it applies per turn.
  - Source: docs/en/tools-reference.
- VERIFIED (this session's tool schema and the 2.1.314 binary; not on the docs page): a required `mode`, `standard` or `extended`.
  - `extended` is "a thorough, fresh search at several times the cost and latency".
  - Use it "for hard-to-find or niche facts, very recent events … and multi-step research", or when a standard result is thin.
- UNVERIFIED: whether an extended call counts against the 200, and whether every account has the mode.
- Implies: researchers start standard and switch to extended for local, Turkish-language, recent or thin rows.
- Confidence: high that the mode exists, low on how it counts.

**F5. Claude Code WebFetch: still lossy; long pages can be read on; PDFs go through Read.**
- VERIFIED: WebFetch is "lossy by design", because a separate model answers the prompt ("use curl via Bash for the unprocessed page").
  - Each call reads 100,000 characters; from v2.1.290 an `offset` reads on.
  - The cache lasts 15 minutes and the deadline is 5 minutes.
  - Source: tools-reference.
- VERIFIED (observed today): pages on code.claude.com came back near verbatim, while learn.chatgpt.com answers said "quotes are capped at 125 characters". The docs no longer mention PDFs.
- VERIFIED: the Read tool takes PDFs page by page (`pages`, up to 20 pages per call).
- Implies: page snapshots stay the receipts. Update hosts.md:13 to "reads on with offset". Without pdftotext, use curl, then Read.
- Confidence: high.

**F6. Permission prompts cost time on Claude Code.**
- VERIFIED: in Manual mode, WebFetch asks before each fetch from a domain that is neither allowed nor preapproved. Prompts from background subagents surface in the main session.
- VERIFIED: an allow rule `WebFetch(domain:*)`, or auto mode, skips the prompts. A skill's `allowed-tools` applies to the invoking turn only (tools-reference; skills page).
- Implies: a run that touches 26 domains stalls in Manual mode. The README should recommend allow rules or auto mode. Do not add `allowed-tools`, which the hygiene test forbids (tests/test_skill_hygiene.py:21).
- Confidence: medium.

**F7. Codex web search: `codex exec --search` fails; there is no page-fetch tool.**
- VERIFIED: the modes are `disabled`, `cached`, `indexed` and `live`.
  - `cached` is the default and uses an "OpenAI-maintained index without external web access".
  - `indexed` "permits external access only when gated by the search index".
  - `tools.web_search.allowed_domains` filters domains, and hosted search ignores the sandbox's network setting.
  - Source: learn.chatgpt.com/docs/web-search; config reference.
- VERIFIED (local 0.164.0): `codex exec --search` fails with "unexpected argument '--search' found". The documented route is `-c web_search="live"`.
- VERIFIED: the hosted tool has `search`, `open_page` and `find_in_page` actions (developers.openai.com/api/docs/guides/tools-web-search).
- VERIFIED: `standalone_web_search` is "under development" and off. The Browser is not in Codex CLI or the IDE extension (learn.chatgpt.com/docs/browser).
- Implies: fix hosts.md:21 and the README to use `codex exec -c web_search="live"`.
- Confidence: high.

**F8. Skill frontmatter: each host reads a different subset.**
- VERIFIED (agentskills.io/specification): the spec fields are `name` (up to 64 characters, matching the folder), `description` (up to 1,024), `license`, `compatibility` (up to 500), `metadata` and `allowed-tools` (experimental).
- VERIFIED (docs/en/skills): Claude Code adds `when_to_use`, `disable-model-invocation`, `allowed-tools`, `model`, `effort`, `context: fork`, `agent`, `hooks` and `paths`. It ignores unknown fields and cuts description plus when_to_use at 1,536 characters.
- VERIFIED (source, `codex-rs/skills/src/parser.rs`): Codex parses only `name`, `description` and `metadata.short-description`.
- VERIFIED: in `agents/openai.yaml`, `policy.allow_implicit_invocation: false` limits a skill to explicit calls (learn.chatgpt.com/docs/build-skills).
- Implies:
  - Keep the spec-only frontmatter.
  - If brainstorm should run only when called by name, Codex can do it in openai.yaml; Claude Code would need `disable-model-invocation`, which the test forbids.
  - Neither host reads `metadata.version`.
- Confidence: high.

**F9. Size limits and staged loading.**
- VERIFIED (Claude Code): keep SKILL.md under 500 lines. The skill file is not re-read on later turns. After compaction, only the first 5,000 tokens of each skill return.
- VERIFIED (Codex): the list of available skills gets 2% of context (at most 10,000 tokens), and descriptions are cut first. A selected SKILL.md must be read in full.
- Implies: the 1,500-word body is fine. Put trigger words first in each description, and keep the binding rules near the top.
- Confidence: high.

**F10. How a skill finds its own folder.**
- VERIFIED (Claude Code): `${CLAUDE_SKILL_DIR}` is replaced in skill content (since 2.1.69), and the loaded skill starts with "Base directory for this skill: <path>" (binary).
- VERIFIED (Codex): the skill block includes `<path>`, and the model is told to resolve relative paths "relative to the directory containing that expanded SKILL.md first" (`ext/skills/src/catalog_prompt.rs`). `${CLAUDE_SKILL_DIR}` is not replaced (no match in openai/codex).
- Implies: keep `<skill folder>/scripts/vafer_check.py` (SKILL.md:53), with the lead pasting the absolute path into each brief. A bare `${CLAUDE_SKILL_DIR}` would reach Codex as literal text.
- Confidence: high.

**F11. Claude Code packaging: one plugin with two namespaced skills.**
- VERIFIED (layout): a plugin is `.claude-plugin/plugin.json` plus `skills/<skill>/SKILL.md`, and its skills appear as `/<plugin>:<skill>`. A marketplace is `.claude-plugin/marketplace.json`, whose plugin entries may use the source `"./"`.
- VERIFIED (install): `/plugin marketplace add owner/repo`, then `/plugin install vafer@<marketplace>`. From the shell, `claude plugin install vafer --marketplace owner/repo` does both in one step.
- VERIFIED (version): `version` "keeps users on that version until you change it". Without it, the version is the commit SHA. Third-party marketplaces do not auto-update by default.
- VERIFIED: cloud sessions do not load plugins installed locally.
- Sources: plugins-reference, plugins/loading, plugins/install.
- Implies: ship plugin `vafer` with `/vafer:research` and `/vafer:brainstorm`, and bump `version` on every release. Keep the copy-into-`.claude/skills/` route for cloud sessions.
- Confidence: high.

**F12. Codex packaging: Codex reads the Claude Code files.**
- VERIFIED (source):
  - Marketplace order: `.agents/plugins/marketplace.json`, then `.claude-plugin/marketplace.json`, among others (`core-plugins/src/marketplace.rs`).
  - Manifest order: `.codex-plugin/plugin.json`, then `.claude-plugin/plugin.json`, unless a root `plugin.json` declares the Agent Plugins schema (`exec-server-protocol/src/protocol.rs`).
  - Plugin sources written as path strings parse, but Claude Code's `github` object is skipped.
  - Skills are named `<plugin>:<skill>`.
- VERIFIED: `codex plugin marketplace add owner/repo` adds a marketplace, and `codex plugin add PLUGIN@MARKETPLACE` installs from it. The version comes from plugin.json. OpenAI "also accepts legacy and Claude-compatible manifests" (developers.openai.com/plugins/build/plugins).
- UNVERIFIED: a live install of a Claude-format plugin on Codex, and how a plugin skill is called with `$`.
- Implies: one layout can serve both hosts: `.claude-plugin/marketplace.json` (source `"./"`), `.claude-plugin/plugin.json` (`"version": "0.0.5"`), `skills/research/` and `skills/brainstorm/`. Install it once on each host before release.
- Confidence: medium.

**F13. The baseline on Claude Code: the bundled `/deep-research`.**
- VERIFIED: it "votes on each claim" and returns a cited report. It runs only when invoked and needs WebSearch; on Pro, Dynamic workflows must be turned on first (docs/en/workflows).
- VERIFIED (its script in the 2.1.314 binary), step by step:
  1. Split the question into 3–6 search angles.
  2. One agent per angle returns 4–6 results.
  3. Drop duplicate URLs; fetch about 15 pages with WebFetch, taking 2–5 quoted claims from each.
  4. Give the top 25 claims 3 skeptical votes each; 2 refutations kill a claim, and the default is "refuted=true if uncertain".
  5. Write a structured summary.

  That is about 100 agents at most.
- Implies: add `/deep-research` as an arm in the side-by-side.
  - Its gaps: quotes pass through WebFetch; there are no snapshots, calendar checks, Turkish source strategy, report file or reuse.
  - Its strength: wide parallel verification.
- Confidence: high.

**F14. The baseline on Codex: none in the CLI.**
- VERIFIED: deep research is a plugin in ChatGPT Work and the desktop app, and the Codex CLI only has search (learn.chatgpt.com/docs/web-search?surface=app). There is no "deep research" in openai/codex.
- Implies: the Codex baseline is bare Codex with cached search. State the live-search requirement up front.
- Confidence: medium.

**F15. Workflows: an option for Claude Code only.**
- VERIFIED: a plugin can ship `workflows/*.js` scripts that use `agent()`, `pipeline()` and `parallel()`.
  - 16 agents run at once by default, and a run can start at most 1,000.
  - Agents can share a prompt cache, and a model can be chosen per agent.
  - In Manual mode, each run asks for approval.
  - Source: docs/en/workflows.
- Implies: a workflow could enforce the pipeline exactly, but it would be a second implementation that Codex cannot run. Defer it until the SKILL.md version is measured.
- Confidence: high for the facts, medium for the recommendation.

**F16. What could make runs faster.**
- VERIFIED (Claude Code):
  - parallel calls in one message, where a failed Bash call no longer cancels the others;
  - per-researcher `model` and `effort`;
  - background Bash;
  - fast mode makes Opus "up to 2.5x faster" at a higher price. It is a user setting (docs/en/fast-mode).
- VERIFIED (Codex): `service_tier = "fast"`, `gpt-6-luna`, `reasoning_effort` per spawn, and a cap that can be raised above 6.
- Implies: the cheapest test is researchers on `sonnet` at `medium` against v0.0.4's defaults, on the Yalova question.
- Confidence: medium. The levers are verified, but their effects are not measured.

**F17. Claude Code has a built-in side-by-side command.**
- VERIFIED: `claude plugin eval` (v2.1.269+) runs each case with and without the plugin. Use `--runs 1` for a single run. Its `llm` judge "differs more the longer the text it has to read" (docs/en/plugin-evals).
- Implies: use it for smoke tests, and keep the blind fact-checking judge for scores.
- Confidence: high.

**F18. Lines in hosts.md that are out of date.**
- :11 needs the refill and `mode: extended`.
- :13 should say "reads on with offset".
- :15 should mention per-spawn `model` and `effort`.
- :21 should use `-c web_search="live"`.
- :23 should say Codex runs at most 6 subagents at once and they cannot spawn their own.
- Confidence: high.
