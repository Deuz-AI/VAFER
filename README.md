# VAFER

VAFER is a set of agent skills for Claude Code and Codex. Version 0.0.5 has two skills:

- **vafer-brainstorm** looks at your idea, plan, decision or question from five angles. It shows, on one screen, what you may have missed.
- **vafer-research** does web research across many sources. It writes a readable report and checks every cited figure against a saved copy of its page.

Status: **v0.0.5** (2026-10-31).

## Start here

```text
/vafer-brainstorm <your idea>
```

For example: `/vafer-brainstorm I'm thinking of putting solar panels on my roof. Does it make sense?`

With the plugin, the command is `/vafer:vafer-brainstorm`. On Codex, with a copied skill folder, it is `$vafer-brainstorm`.

If you also use superpowers: superpowers may take the word 'brainstorm'; use the explicit command.

## How the modules fit

VAFER is planned as a hub of modules that pass work to each other. Brainstorm is the front door: it looks at an idea before you act, and saves a handoff file for the next module. Research comes next: it can take a question from that file and answer it with checked sources. Planning, frontend and anatomy are later modules. The anatomy skill draws interactive isometric figures. It is a separate MIT-licensed skill by Ryan ([github.com/wheresryan22/anatomy](https://github.com/wheresryan22/anatomy)), not part of this repository. When it is installed, brainstorm can already hand it a figure idea.

## Install

### Claude Code

As a plugin, with both skills:

```text
/plugin marketplace add Deuz-AI/VAFER
/plugin install vafer@vafer
```

The commands are then `/vafer:vafer-brainstorm` and `/vafer:vafer-research`.

Or copy a skill folder, `skills/<name>/`, from this repository. `<name>` is `vafer-brainstorm` or `vafer-research`.

| Copy it to | Works in | Commands |
|---|---|---|
| `.claude/skills/<name>/` | that project | `/vafer-brainstorm`, `/vafer-research` |
| `~/.claude/skills/<name>/` | all your projects | `/vafer-brainstorm`, `/vafer-research` |

Cloud sessions do not load plugins installed on your computer, so use a project copy there.

### Codex

Copy a skill folder, `skills/<name>/`, from this repository:

| Copy it to | Works in | Commands |
|---|---|---|
| `.agents/skills/<name>/` | that project | `$vafer-brainstorm`, `$vafer-research` |
| `~/.codex/skills/<name>/` | all your projects | `$vafer-brainstorm`, `$vafer-research` |

The project route was checked with a test skill on codex-cli 0.166.0.

The plugin route is not yet verified live:

```text
codex plugin marketplace add Deuz-AI/VAFER
codex plugin add vafer@vafer
```

Codex searches a cached index by default. For fresh results, start it with `-c web_search="live"`:

```text
codex -c web_search="live"
```

For research, also add `-c sandbox_workspace_write.network_access=true`. Codex's workspace-write sandbox has no network by default, and the script's `fetch` command needs it.

`codex exec` runs in a read-only sandbox by default, so it saves no run files. Add `--sandbox workspace-write` to save them. The single quotes keep the shell from reading `$vafer-research` as a variable:

```text
codex exec -c web_search="live" --sandbox workspace-write -c sandbox_workspace_write.network_access=true '$vafer-research <question>'
```

A Standard research run on Codex has not been tested yet.

### What the skills need

- **vafer-research** needs a web search tool. The rest is optional: subagents, a shell with Python 3 and network access for the check script, and a writable project folder. Without subagents, it does the researchers' work itself. Without a shell, it checks up to ten headline facts by hand. Without a writable folder, it answers in chat and saves nothing.
- **vafer-brainstorm** runs with or without extra tools. Without subagents, it takes the five angles itself, one after another (single mode). Without web search, there is no scan, and facts stay marked unchecked. Without a writable folder, the answer says "not saved".
- Both look for earlier runs with `rg` (ripgrep). Without `rg`, they skip that lookup. Research's `fetch` uses `pdftotext`, when it is installed, to save PDFs as text for the check.

### Permissions on Claude Code

By default, WebFetch asks before it opens each new site, and subagents' prompts appear in your main session. To avoid a prompt on every call, use auto mode, or allow these in `.claude/settings.json` (one project) or `~/.claude/settings.json` (all projects):

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch",
      "Edit(.vafer/**)",
      "Bash(python \"/absolute/path/to/vafer-research/scripts/vafer_check.py\" *)"
    ]
  }
}
```

In the last rule, use the interpreter that runs on your machine (`python`, `python3` or `py -3`) and the absolute path of your `vafer-research` folder. A looser rule such as `Bash(python*)` lets any Python code run. The acceptEdits mode also covers the file writes.

A `deny` rule for WebSearch or WebFetch, in your settings or in a managed setting, blocks research. Brainstorm then skips its web scan.

## vafer-brainstorm

Brainstorm does not interview you. It shows its guess of your goal in one status line and starts at once. If you correct the guess in the first minute, it starts again. It asks a question first only when there is no topic at all.

1. The main agent reads the conversation, up to 3 files you pointed at, and earlier VAFER runs on the topic.
2. Five independent agents look at the request, one angle each. They work only from what they know, with no web and no files.

   | Angle | What it brings back |
   |---|---|
   | Routes | other ways to the goal: much smaller, much bigger, buy it, or do nothing |
   | Blind spots | what the request is silent on, such as who pays, how success is checked, or legal and privacy questions |
   | Failure | the plan has failed: the first warning signs, and one failure that comes from success |
   | One person | an ordinary person's first encounter with the result: what they want and what stops them |
   | Far field | ways a distant field solved the same kind of problem |

3. Meanwhile, if the request touches a product, price, law, place or recent event, the main agent runs a short web scan: at most 3 searches and 2 opened pages. Only facts from opened pages get a link. A fact seen only in a search summary becomes a question worth researching.
4. It merges the points and drops what you already said. It saves `handoff.md` in `.vafer/brainstorm/<date>-<slug>/`, then shows the answer.

The answer is one screen of at most 350 words, in your language:

- **What you may have missed:** 4–5 points. Each says why it matters here and gives a first step that takes under an hour.
- **Other routes:** 2–3 routes, one line each, with the main trade-off. If you asked for ideas, 3–6 ideas take this place.
- **Obvious, skipped:** up to six titles that any assistant would give.
- **Yours to decide:** up to 2 questions whose answer changes a choice.
- **Worth researching:** at most one question.
- **Saved** and **Next:** the handoff path and the follow-ups you can ask for.

A number, law, price, product or date without a link is marked "(unchecked)". There is no praise, summary or closing question. In early test runs on Claude Code with Opus 5.5, a first answer took about 2–3 minutes.

Follow-ups:

- **"deepen 1 and A"** (up to 3 picks): one agent per pick makes it concrete, and one more argues against the picks. Each pick comes back as How, First test and Against.
- **"more":** the points that did not fit on the screen, or a new wave of angles when few are left.
- **"check 2":** a Quick vafer-research run on point 2.
- **"research":** passes the question and the handoff to vafer-research. Standard or deeper research starts only when you say yes.
- **An answer or a correction:** recorded as a decision. The points it settles drop out.

Brainstorm stays out of mechanical requests, such as naming a function: it just does them. It is not for requirement interviews or specs. For cited research, it offers vafer-research.

## vafer-research

```text
/vafer-research <question>
```

| Tier | Use it for | What runs |
|---|---|---|
| Quick | one fact, a definition, a stable topic, or a follow-up that saved research answers | the main agent alone: up to 8 searches and 5 opened pages, with the answer in chat |
| Standard | three or more sub-questions, a comparison, a recent, niche or local topic, or a written report | the six steps below |
| Deep | exhaustive lists, many entities, contested high-stakes decisions, synthesis across fields | Standard with up to 10 researchers and 6 follow-ups |
| Ultra | when you ask for ultra or exhaustive research | Deep, with follow-ups until a batch adds no new fact, plus one counter-evidence follow-up per headline conclusion |

Name a tier to choose it, for example `/vafer-research Deep: <question>`. A bare topic starts as Quick, and the skill offers to go deeper.

### How a Standard run works

1. **Preflight and plan.** The main agent checks the host once: the Python interpreter, the search mode, subagents and network. Before it searches, it starts a gap-finder. This agent sees only the question, the date and the scope, and lists what a complete answer must cover. Meanwhile, the main agent writes plan.md: 4–12 rows in 3–6 sections, each row naming the record that would settle it. It adds the gap-finder's items when they arrive.
2. **Launch, in one message.** The main agent starts one researcher per section, all at once. Each researcher writes its section and saves receipts: one line per fact, with an exact quote from a saved copy of the page and a source label. The report body is about 2,000 words: 3,000 if you ask for detail, 1,000 for a short report.
3. **Follow up as replies arrive.** The main agent marks the rows and settles conflicts with the source ladder below. It starts a follow-up agent at once when the answer depends on a conflict the ladder cannot settle or on an open row, and when a value is about to be rejected but nobody opened its page. Standard allows 3 follow-ups and 8 agents in all, the gap-finder included.
4. **Assemble.** The main agent writes the opening answer, the at-a-glance table and the closing part: where sources disagree and what is not known. `assemble` joins them with the sections into report.md and numbers the citations. The main agent then rewrites report.md for flow. `diff` lists any figure, quote or citation that the rewrite lost, changed or added, so the main agent can fix it. Method and checks go to evidence.md.
5. **Check.** `check` matches every cited number, date and quote against the receipts and the saved pages. The main agent answers every high and medium flag: fixed, derived, a false alarm with its reason, or marked † (unverified). It runs the check again until no high or medium flag is open.
6. **Deliver.** The reply gives the answer in 5–8 sentences, one status line such as "Coverage 14/16 rows · 0 open flags · 11 min", and the paths of report.md and evidence.md.

The source ladder settles conflicts. Arithmetic and calendar checks beat any source. Then, highest first:

1. the primary record: an archive, a text from the time, a dataset, the issuer's own page;
2. official or legal text;
3. scholarly work;
4. reputable press;
5. encyclopedias, aggregators and blogs, which only lead to better sources.

Each run saves its files in `.vafer/research/<date>-<slug>/`. report.md is for the reader: the answer, an at-a-glance table, the sections, where sources disagree, what is not known, and the sources. evidence.md holds the method and the checks. The folder also keeps plan.md, the receipts in notes/, the drafts in sections/, the saved pages in pages/, conflicts.md and check.md.

A later question on the same topic starts from the earlier run. Dated facts are opened again; stable facts keep their citation and date. A request that ends with `(handoff: <path>)` takes its question and scope from a brainstorm handoff.

## The check script

`skills/vafer-research/scripts/vafer_check.py` uses only the Python 3 standard library. Only `fetch` needs the network. The skill runs it as `<python> "<absolute skill folder>/scripts/vafer_check.py" <command>`. It has five commands:

- `fetch <run> [--find "a|b|c"] [--refresh] <url>...` saves a text copy of each page in `<run>/pages/`, up to 8 pages at a time. It handles charsets, tables and PDFs (with `pdftotext`), and marks empty, boilerplate and binary pages. It reuses a good copy unless you pass `--refresh`. `--find` also prints up to 3 passages per page that contain the terms.
- `find <run> "a|b|c" [<url>...]` prints the passages that contain the terms, from the saved copies.
- `check <run> [--section <id>]` matches every cited number, date and quote against the receipts and the saved copies. It writes its flags to check.md, and the Source check and Source mix lines to evidence.md. With `--section`, it checks one section draft and writes nothing.
- `assemble <run> [--title "<heading>"]` joins `sections/_top.md`, the sections in plan order and `sections/_end.md` into report.md. It numbers the citations and lists the sources with their page titles. `--title` sets the sources heading in the reader's language. If report.md was edited after the last assembly, it is kept, and only report.assembled.md is rewritten.
- `diff <old> <new>` lists what an edit lost, changed or added. It exits with an error if a number or quote was lost, changed or added, a citation was dropped or detached from its sentence, a source changed, or a marker line went missing.

`check` reads numbers written in Turkish and English, such as "4 bin 472" and "1.2 million". It also reads dates with month names in seven languages, and centuries, including Roman numerals. It recomputes equations. It finds the report's parts by marker lines, so it works in any report language. It flags:

- figures without a citation, and figures or quotes not found in their sources;
- wrong equations;
- claims cited only to leads, such as Wikipedia, forums or blogs;
- dangling or unused citations;
- a rejected value in the disagreement table with neither a citation nor a †;
- internal labels that leak into the report.

High and medium flags need an answer in check.md. Low ones do not.

## Results

v0.0.5 live results are pending: a research test against the previous version and no skill, and a brainstorm test against no skill, run next.

### Previous results (v0.0.4)

Question: "Yalova'nın tarihi" (the history of Yalova). Each arm ran the same model with the same prompt. A blind judge did not know which report came from which arm. It opened 26 cited pages, fact-checked 10–12 claims per report and scored each report out of 10.

| | v0.0.4 | v0.0.4 first draft | No skill |
|---|---|---|---|
| Overall | **8.6** | 8.1 | 5.8 |
| Accuracy | **8.5** | 8 | 5 |
| Source quality | **9** | **9** | 3.5 |
| Conflict handling | 8.5 | **9** | 5.5 |
| Readability | **8.5** | 6.5 | 8 |
| Wall time | 22 min | 13.5 min | 5 min |

What the judge's checks found:

- **Calendar conversion:** only v0.0.4 converted the Rumi calendar date correctly (1316 = 1900).
- **Errors in the no-skill report:** it put the 1999 earthquake toll for nine central neighbourhoods (1,449) as the toll for the whole province, and it got the dates and members of the 1921 Allied commission wrong.
- **Speed:** v0.0.4 took more than four times as long as the run without the skill. v0.0.5 removes steps to cut this time.

## Repository

- `skills/vafer-brainstorm/`: `SKILL.md`, `references/` (`angles.md` holds the agents' briefs; `next.md` holds the handoff template and the follow-ups) and `agents/openai.yaml` (how Codex shows the skill).
- `skills/vafer-research/`: `SKILL.md`, `references/` (briefs, researcher rules and house style, hosts, reuse), `scripts/vafer_check.py` and `agents/openai.yaml`.
- `.claude-plugin/`: `plugin.json` (the plugin `vafer`, version 0.0.5) and `marketplace.json`.
- `tests/`: tests for `vafer_check.py`, and tests that keep both skills short and their wording plain. Run them with `python -m pytest -q tests`, or without pytest, with `python -m unittest discover -s tests`.
- `docs/research/`: the research behind the design, including the v0.0.5 review and the brainstorm design.
- `docs/history/`: evaluation records for the v0.0.x versions. Version 0.0.3, which never beat the same model without the skill, is at git tag `v0.0.3`.
