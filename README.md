<div align="center">

# VAFER

**Agent skills for research you can check and ideas you can use.**

Claude Code · Codex

</div>

<br>

| Skill | You type | You get |
|---|---|---|
| [**vafer-research**](skills/vafer-research/SKILL.md) | `/vafer-research <question>` | A cited report. A script checks every number, date and quote against a saved copy of its page. |
| [**vafer-deep-research**](skills/vafer-deep-research/SKILL.md) | `/vafer-deep-research <question>` | The same method as one workflow of 10 agents. A long report with 2.8 to 4.5 times the verified facts of built-in deep research. |
| [**vafer-brainstorm**](skills/vafer-brainstorm/SKILL.md) | `/vafer-brainstorm <topic>` | 12 agents brainstorm. About 60 raw ideas become ranked concept cards in four minutes. |

```text
> /vafer-deep-research AB Yapay Zekâ Yasası (AI Act): yükümlülükler, yürürlük takvimi, cezalar …

  AB Yapay Zekâ Yasası (Tüzük (AB) 2024/1689) yapay zekâ sistemlerini risk düzeyine
  göre düzenler ve 1 Ağustos 2024'te yürürlüğe girdi. …

  Kapsam 34/34 satır · Rakam kontrolü 492/498 eşleşti, 12 uyarının hepsi yanıtlandı
  · 77 kaynak · 10 ajan · 15 dk
  .vafer/research/2026-11-10-ab-ai-act/report.md
```

## Install

Copy the skills you want from `skills/` into your project's `.claude/skills/` folder.

| Skill | Host | Needs |
|---|---|---|
| vafer-research | Claude Code, Codex | A web search tool. Subagents, Python 3 and a writable folder make it faster and let the script check the report. |
| vafer-deep-research | Claude Code | The Workflow tool, web search, Python 3, and vafer-research installed next to it. |
| vafer-brainstorm | Claude Code | The Workflow tool. |

On Codex, copy vafer-research into `.agents/skills/`, call it with `$vafer-research`, and start Codex with `--search` for live results. On Claude Code, a `deny` rule for WebSearch or WebFetch in `settings.json` blocks all research.

## How they work

```text
vafer-research        plan → researchers → settle conflicts → gap wave → assemble → edit → check
vafer-deep-research   plan → 8 researchers at once → script merges the drafts → writer → check
vafer-brainstorm      frame → 5 ideators alone → 2 builders → curator → 3 judges → concept cards
```

The two research skills rest on three ideas:

- **Receipts.** Researchers save a text copy of every page they cite and quote the exact words behind each fact.
- **A script checks the report.** It matches every cited number, date and quote against those copies and recomputes equations. The check is code, not a model grading its own work.
- **A source ladder.** The primary record comes first, then official text, scholarly work and press. Encyclopedias only point to better sources. Where sources disagree, the ladder decides and the report shows the dispute.

The brainstorm skill keeps apart three steps that spoil each other when they are mixed: having ideas, building on them, and judging them.

## Results

**vafer-research** against the same model without the skill. One question, one blind judge.

| | With the skill | Without |
|---|---|---|
| Overall score | **8.6** | 5.8 |
| Accuracy | **8.5** | 5 |
| Source quality | **9** | 3.5 |
| Wall time | 22 min | **5 min** |

**vafer-deep-research** against Claude Code's built-in `/deep-research`. Two questions on Claude Opus 5.5, blind judges.

| | This skill | Built-in |
|---|---|---|
| Distinct facts per report | **259** and **227** | 58 and 76 |
| Checked facts supported | 29 of 30 | 30 of 30 |
| Overall score | **8.7** and **8.6** | 4.6 and 6.4 |
| Readability | 6.8 and 6.9 | **8.1** and **7.5** |
| Agents and tokens | **10 agents, about 1.2 M** | about 100 agents, about 3.4 M |
| Wall time | 16 to 19 min | **7 to 9 min** |

**vafer-brainstorm**, one trial on Claude Opus 5.5: 62 raw ideas became 44 ideas in 8 themes, with 5 top picks and 2 bold bets, in 4.2 minutes for $2.73. It has not been compared with a single-agent brainstorm.

The samples are small: one run per arm, and the judges are models. In the deep-research comparison no checked fact was wrong in either arm; the one unsupported fact could not be verified either way. The full records are [vafer-research 0.0.4](docs/history/v0.0.4-results.md) and [vafer-deep-research 0.1.0](docs/history/vafer-deep-research-evaluation.md).

## More

<details>
<summary><b>Depths and timings</b></summary>

<br>

| Skill | Depth | What runs | Agents | Time |
|---|---|---|---|---|
| vafer-research | Quick | A few searches and an answer in chat | none | a minute or two |
| | Standard | One wave of section researchers, an editor and the source check | 5 to 8 | about 22 min |
| | Deep | More researchers and up to two gap waves | | |
| | Ultra | Gap waves until one adds nothing new, and a counter-evidence search for every conclusion | | |
| vafer-deep-research | standard | A planner, 8 researchers and a writer | 10 | about 16 min |
| | deep | 12 researchers and up to two gap waves | up to 24 | 30 to 45 min |
| | ultra | 14 researchers, up to four gap waves and a counter-evidence search | up to 40 | 60 to 90 min |
| vafer-brainstorm | quick | 3 ideators, no builders | 8 | about 3 min |
| | standard | 5 ideators and 2 builders | 12 | about 4 min |
| | deep | 8 ideators and 4 builders | 17 | about 8 min |

Measured: vafer-research Standard, vafer-deep-research standard and vafer-brainstorm standard. The other times are estimates.

- A deep research run that is cut off after its research, for example by a usage limit, is finished from the drafts on disk with `finish: true`.
- A second brainstorm round can steer away from the earlier ideas (`avoid`), stay inside one theme (`focus`) or use angles of your own (`lenses`).

</details>

<details>
<summary><b>Scripts</b></summary>

<br>

`skills/vafer-research/scripts/vafer_check.py`

| Command | What it does |
|---|---|
| `fetch <run> <url>...` | Saves a text copy of each page under `pages/`. It handles charsets, tables and PDFs (with `pdftotext`), and flags empty, boilerplate or binary pages. |
| `check <run>` | Matches every cited number, date and quote against the receipts and page copies. It reads Turkish and English number formats, including words such as "4 bin 472", and recomputes equations. It flags uncited figures, claims backed only by lead-class sources, dangling or unused citations, and method words that leak into the report. |
| `diff <old> <new>` | Exits with an error if an edit lost, changed or added a number or quote, dropped a citation, or detached a citation from its sentence. |

`skills/vafer-deep-research/scripts/vafer_assemble.py`

| Command | What it does |
|---|---|
| `fetch <run> <url>...` | The same snapshots, downloaded in parallel with a 45-second limit per page. It reads PDFs through pypdf when `pdftotext` is missing. |
| `lint <run> <id>` | Runs the figure, quote and citation checks on one section draft. |
| `build <run>` | Merges `front.md`, the section drafts and `back.md` into `report.md` with one citation numbering and one sources list. |
| `check <run>` | Runs the report check, answers the flags of claims already marked † and prints the flags still open. |

Both scripts need only Python's standard library. pypdf is used for PDFs when it is installed.

</details>

<details>
<summary><b>Repository</b></summary>

<br>

```text
skills/
  vafer-research/        SKILL.md · references/ · scripts/vafer_check.py
  vafer-deep-research/   SKILL.md · workflows/deep-research.js · scripts/vafer_assemble.py
  vafer-brainstorm/      SKILL.md · workflows/brainstorm.js
tests/                   python -m unittest discover -s tests
docs/research/           the research behind the design
docs/history/            evaluation records
```

The tests run offline. The two workflow tests need Node. Version 0.0.3 of the research skill is at git tag `v0.0.3`; [why it was rebuilt](docs/history/v0.0.4-results.md#why-004-was-a-rebuild).

</details>

<br>

<div align="center">
<sub>vafer-research 0.0.4 · vafer-deep-research 0.1.0 · vafer-brainstorm 0.1.0</sub>
</div>
