# VAFER Eval Harness (M0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether a research skill beats the bare host. The harness runs paired trials on Claude Code and Codex, grades them blind with judges from two model families, and turns the results into paired statistics.

**Architecture:** One Python package with no dependencies, `evals/vafer_eval/`. Each module has a single job:
- `tasks` and `adapters`: task model and dataset import
- `prompts`: arm and judge prompts
- `runner`: trial execution
- `telemetry`: log parsing
- `normalize`: blinding
- `grading`: item and answer grading
- `citations`: claim support
- `stats`: paired statistics
- `pipeline`: grade/cite pipelines
- `summary` and `cli`: reporting and command line

Agents and judges are called only through the `claude -p` and `codex exec` CLIs, so the harness needs no API key. Every network or process side effect is injectable, so offline tests can replace it.

**Tech Stack:** Python ≥3.11 standard library (unittest, subprocess, urllib, html.parser, statistics, concurrent.futures); Claude Code CLI 2.1.311; Codex CLI 0.164.0.

**Spec:** `docs/superpowers/specs/2026-10-27-vafer-research-v0.1-design.md` (Section 6 and the M0 row of Section 7)

## Global Constraints

- **Python and dependencies.** Python ≥ 3.11, standard library only, no third-party packages.
- **Code style.** `from __future__ import annotations`, dataclasses, pathlib, unittest. This matches the existing `tests/` code.
- **Tests.** Run from the repo root with `python -m unittest discover -s evals -v`. Test files live in `evals/tests/`.
- **No paid API.** Judges and agents run only through `claude -p` (subscription login) and `codex exec`. `--bare` is never used.
- **No global configuration changes.**
  - Claude uses a separate profile directory, `VAFER_EVAL_CLAUDE_CONFIG` (for example `%USERPROFILE%\.vafer-eval\claude`), passed through `CLAUDE_CONFIG_DIR`.
  - Codex runs with `--ignore-user-config`.
- **Prompts always go through stdin.** No prompt text appears in argv (Windows limits the command line to 32,767 characters). Encoding is `utf-8`.
- **Budgets.**

  | Budget | Seconds | Searches |
  |---|---|---|
  | `smoke` | 300 | 10 |
  | `P` | 900 | 60 |
  | `G` | 2400 | 150 |

  When the time runs out, the whole process tree is killed, and whatever exists is scored.
- **Names.**
  - Arms: `A0` (bare), `A1` (bare plus fan-out hint), `V` (skill installed and invoked), `VI` (skill installed, not invoked), `D` (`/deep-research`, Claude only), `CB` (closed book).
  - Hosts: `claude`, `codex`. Strata: `S1`, `S2`, `S4`, `S6`. Judge families: `claude`, `gpt`.
- **Fixed seed.** `20261027`.
- **Run outputs.** Written under `evals/runs/`, which is git-ignored. Task files are UTF-8 JSONL, one record per line.
- **Gated runs.** Runs against the real hosts (Tasks 12 and 13) start only after the user approves the number of runs and the estimated time.

## Review Focus

1. **Process-tree kill on Windows.** `claude` and `codex` start child processes, and killing only the parent leaves orphans running. Expected: after a timeout, no child process is left. Test: `test_run_trial_timeout_kills_tree` in Task 5.
2. **Long Turkish/Chinese prompts and the Windows code page.** Prompts must travel through stdin as UTF-8, without cp1254 corruption. Expected: `"Türkçe ğüşıöç 中文"` arrives intact. Test: `test_run_trial_reads_report_and_stdin_utf8` in Task 5.
3. **Malformed judge output** (code fence, missing id, invalid verdict, plain text). Expected: no crash; missing items become `unknown`. Test: `test_parse_votes_*` in Task 7.
4. **No report.md and an empty final message.** Expected: the trial is not skipped; the report is scored as `""`, which gives R=0, not None. Tests: `test_run_trial_falls_back_to_final_text_then_empty` in Task 5 and `test_grade_trial_empty_report_scores_zero` in Task 10.
5. **Redirect to a private IP, or a huge response, during citation fetch.** Expected: every redirect target is checked again, and a response over `max_bytes` gets status `too-large`. Tests: `test_redirect_to_private_ip_refused` and `test_too_large_and_http_error_and_refused` in Task 8.

---

### Task 0: Freeze v0.0.3 and open a working branch

**Files:** git operations only.

- [ ] **Step 1: Check the working tree**

Run: `git status --short`
Expected: ` M README.md`, `?? .gitignore`, `?? docs/`, `?? skills/`, `?? tests/` (no other lines).

- [ ] **Step 2: Commit the v0.0.3 snapshot on main, without docs**

```bash
git add README.md .gitignore skills tests
git commit -m "chore: snapshot VAFER v0.0.3 before rebuild" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git tag v0.0.3
```

Run: `git tag --list v0.0.3` → Expected: `v0.0.3`

- [ ] **Step 3: Open a branch and commit the docs**

```bash
git switch -c vafer-research-v0.1
git add docs
git commit -m "docs: add v0.1 research evidence, design and plans" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Package skeleton and task model

**Files:**
- Create: `evals/vafer_eval/__init__.py`: `VERSION = "0.1.0"`
- Create: `evals/vafer_eval/tasks.py`
- Create: `evals/tests/__init__.py` (empty)
- Create: `evals/tests/test_tasks.py`
- Modify: `.gitignore` (add the line `evals/runs/`)

**Interfaces:**
- Produces:
  - `STRATA = ("S1", "S2", "S4", "S6")`
  - `ITEM_KINDS = ("recall", "analysis", "presentation", "negative")`
  - `@dataclass(frozen=True) KeyItem(id: str, text: str, kind: str)`
  - `@dataclass(frozen=True) Task(id: str, stratum: str, language: str, prompt: str, items: tuple[KeyItem, ...] = (), as_of: str | None = None, blocked_urls: tuple[str, ...] = (), answer_set: tuple[str, ...] = (), source: str = "")`
  - `task_from_dict(data: dict) -> Task`
  - `task_to_dict(task: Task) -> dict`
  - `validate_task(task: Task) -> list[str]`
  - `load_tasks(path: Path) -> list[Task]`
  - `write_tasks(path: Path, tasks: Iterable[Task]) -> None`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_tasks.py
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vafer_eval.tasks import KeyItem, Task, load_tasks, task_from_dict, task_to_dict, validate_task, write_tasks


def s2_task(**over) -> Task:
    items = tuple(KeyItem(f"r{i:02d}", f"fact {i}", "recall") for i in range(1, 11))
    data = dict(id="drb2-task1", stratum="S2", language="en", prompt="Write a report.", items=items)
    data.update(over)
    return Task(**data)


class TaskModelTests(unittest.TestCase):
    def test_valid_s2_task_has_no_errors(self):
        self.assertEqual(validate_task(s2_task()), [])

    def test_s1_requires_as_of_and_negatives(self):
        items = tuple(KeyItem(f"r{i:02d}", "x", "recall") for i in range(15))
        errors = validate_task(s2_task(id="s1-a", stratum="S1", items=items))
        self.assertIn("S1 task needs as_of", errors)
        self.assertIn("S1 task needs 3-5 negative items", errors)

    def test_duplicate_item_ids_rejected(self):
        items = (KeyItem("r01", "a", "recall"),) * 10
        self.assertIn("duplicate item id r01", validate_task(s2_task(items=items)))

    def test_answer_strata_need_answer_set(self):
        self.assertIn("S4 task needs answer_set", validate_task(s2_task(stratum="S4", items=())))

    def test_bad_id_rejected(self):
        self.assertIn("invalid id 'Bad Id'", validate_task(s2_task(id="Bad Id")))

    def test_round_trip_and_load(self):
        task = s2_task(blocked_urls=("https://example.org/a",))
        self.assertEqual(task_from_dict(task_to_dict(task)), task)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            write_tasks(path, [task])
            self.assertEqual(load_tasks(path), [task])

    def test_load_reports_all_invalid_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            write_tasks(path, [s2_task(id="a1", items=()), s2_task(id="a2", items=())])
            with self.assertRaisesRegex(ValueError, "a1.*a2"):
                load_tasks(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -v` → Expected: `ModuleNotFoundError: No module named 'vafer_eval'` (or ImportError)

- [ ] **Step 3: Implement `tasks.py`**

`validate_task` returns these exact error strings:
- `invalid id '<id>'`: when the id does not match `^[a-z0-9][a-z0-9_.-]*$`
- `unknown stratum <s>`
- `empty prompt`
- `duplicate item id <id>`
- `unknown item kind <k>`
- S1:
  - `S1 task needs as_of`
  - `S1 task needs 15-40 recall/analysis items`
  - `S1 task needs 3-5 negative items`
- S2:
  - `S2 task needs at least 10 rubric items` (recall+analysis+presentation)
  - `S2 task cannot have negative items`
- S4/S6: `<stratum> task needs answer_set`

Other behavior:
- `load_tasks` collects every invalid task and raises one `ValueError("invalid tasks: <id>: <errors>; <id>: ...")`.
- `task_to_dict` writes tuples as lists and items as `{"id","text","kind"}`. `task_from_dict` turns them back into tuples.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK` (7 tests)

- [ ] **Step 5: Commit**

```bash
git add .gitignore evals/vafer_eval/__init__.py evals/vafer_eval/tasks.py evals/tests/__init__.py evals/tests/test_tasks.py
git commit -m "feat(evals): task model and validation" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Dataset adapters

**Files:**
- Create: `evals/vafer_eval/adapters.py`
- Create: `evals/tests/test_adapters.py`
- Create: `evals/tests/fixtures/drb2_record.json`
- Create: `evals/tests/fixtures/dsqa_rows.json`

**Interfaces:**
- Consumes: `Task`, `KeyItem` (Task 1)
- Produces:
  - `from_drb2(record: dict) -> Task`
  - `from_deepsearchqa(row: dict, index: int) -> Task`
  - `read_jsonl(path: Path) -> list[dict]`
  - `fetch_deepsearchqa(offset: int, length: int, opener=urllib.request.urlopen) -> list[dict]`
  - `sample(records: Sequence[T], count: int, skip: int = 0, seed: int = 20261027) -> list[T]`

- [ ] **Step 1: Write the fixtures**

`evals/tests/fixtures/drb2_record.json`:

```json
{"id": "task99", "idx": 99, "language": "en", "theme": "Test", "description": "Fixture",
 "prompt": "Write a report on X.",
 "content": {"task": "Write a report on X.",
  "rubric": {"info_recall": ["States A.", "States B.", "States C."],
             "analysis": ["Compares A and B.", "Explains C."],
             "presentation": ["Has two parts."]},
  "blocked": {"title": "Source", "authors": ["Someone"], "urls": ["https://www.mdpi.com/x", "https://doi.org/10.1/x"]}},
 "license": "CC BY 4.0"}
```

`evals/tests/fixtures/dsqa_rows.json`:

```json
[{"problem": "Which three categories of buffs exist in the mode?", "problem_category": "Media & Entertainment", "answer": "Combat, Skilling, Utility", "answer_type": "Set Answer"},
 {"problem": "Which country matches both conditions?", "problem_category": "Politics & Government", "answer": "New Zealand", "answer_type": "Single Answer"}]
```

- [ ] **Step 2: Write the failing test**

```python
# evals/tests/test_adapters.py
from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

from vafer_eval.adapters import fetch_deepsearchqa, from_deepsearchqa, from_drb2, sample

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class AdapterTests(unittest.TestCase):
    def test_drb2_maps_rubric_and_blocked_sources(self):
        task = from_drb2(json.loads((FIXTURES / "drb2_record.json").read_text(encoding="utf-8")))
        self.assertEqual(task.id, "drb2-task99")
        self.assertEqual(task.stratum, "S2")
        self.assertEqual(task.prompt, "Write a report on X.")
        self.assertEqual([i.id for i in task.items], ["r01", "r02", "r03", "a01", "a02", "p01"])
        self.assertEqual([i.kind for i in task.items], ["recall"] * 3 + ["analysis"] * 2 + ["presentation"])
        self.assertEqual(task.blocked_urls, ("https://www.mdpi.com/x", "https://doi.org/10.1/x"))
        self.assertEqual(task.source, "drb2:task99")

    def test_deepsearchqa_set_and_single_answers(self):
        rows = json.loads((FIXTURES / "dsqa_rows.json").read_text(encoding="utf-8"))
        first, second = from_deepsearchqa(rows[0], 7), from_deepsearchqa(rows[1], 8)
        self.assertEqual(first.id, "dsqa-0007")
        self.assertEqual(first.stratum, "S4")
        self.assertEqual(first.answer_set, ("Combat", "Skilling", "Utility"))
        self.assertEqual(second.answer_set, ("New Zealand",))
        self.assertEqual(first.items, ())

    def test_fetch_deepsearchqa_uses_rows_endpoint(self):
        seen = []

        def opener(url, timeout=30):
            seen.append(url)
            return io.BytesIO(json.dumps({"rows": [{"row": {"problem": "p"}}]}).encode("utf-8"))

        self.assertEqual(fetch_deepsearchqa(5, 2, opener=opener), [{"problem": "p"}])
        self.assertIn("dataset=google/deepsearchqa", seen[0])
        self.assertIn("offset=5&length=2", seen[0])
        with self.assertRaises(ValueError):
            fetch_deepsearchqa(0, 101, opener=opener)

    def test_sample_windows_are_deterministic_and_disjoint(self):
        records = list(range(20))
        first, second = sample(records, 5), sample(records, 5, skip=5)
        self.assertEqual(first, sample(records, 5))
        self.assertFalse(set(first) & set(second))
        self.assertEqual(first + second, sample(records, 10))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_adapters.py" -v` → Expected: ImportError

- [ ] **Step 4: Implement `adapters.py`**

- **`from_drb2`:**
  - `prompt = record["content"].get("task") or record["prompt"]`
  - item ids `rNN` / `aNN` / `pNN`, numbered from 1 in the order info_recall, analysis, presentation
  - `language = record["language"]`
- **`from_deepsearchqa`:**
  - Set Answer: split by `,` and drop blank parts; Single Answer: `(answer.strip(),)`
  - `language="en"`, `source=f"dsqa:{index}"`
- **`fetch_deepsearchqa`:** fetches `https://datasets-server.huggingface.co/rows?dataset=google/deepsearchqa&config=deepsearchqa&split=eval&offset={offset}&length={length}` with `opener(url, timeout=30)`. Raises `ValueError` if `length > 100`. Returns `[r["row"] for r in data["rows"]]`.
- **`sample`:** `ordered = list(records)`, `random.Random(seed).shuffle(ordered)`, `return ordered[skip:skip + count]` (consecutive windows stay prefix-consistent).

- [ ] **Step 5: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add evals/vafer_eval/adapters.py evals/tests/test_adapters.py evals/tests/fixtures/drb2_record.json evals/tests/fixtures/dsqa_rows.json
git commit -m "feat(evals): DRB-II and DeepSearchQA adapters" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Arm and judge prompts, output schemas

**Files:**
- Create: `evals/vafer_eval/prompts.py`
- Create: `evals/schemas/item_votes.schema.json`, `answer_set.schema.json`, `support_votes.schema.json`, `arm_guess.schema.json`
- Create: `evals/tests/test_prompts.py`

**Interfaces:**
- Consumes: `Task`, `KeyItem`
- Produces:
  - `ARMS = ("A0", "A1", "V", "VI", "D", "CB")`, `HOSTS = ("claude", "codex")`
  - `RUN_SUFFIX`, `FANOUT_HINT`, `CLOSED_BOOK_SUFFIX`, `SKILL_INVOCATION: dict[str, str]`
  - `arm_prompt(arm: str, host: str, task: Task) -> str`
  - `item_grading_prompt(task: Task, report_text: str, items: Sequence[KeyItem]) -> str`
  - `answer_set_prompt(task: Task, report_text: str) -> str`
  - `support_prompt(pairs: Sequence[tuple[str, str]]) -> str`
  - `arm_guess_prompt(report_text: str) -> str`
  - `SCHEMA_DIR: Path` (`evals/schemas`)

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_prompts.py
from __future__ import annotations

import json
import unittest

from vafer_eval.prompts import (
    CLOSED_BOOK_SUFFIX, FANOUT_HINT, RUN_SUFFIX, SCHEMA_DIR, arm_prompt, item_grading_prompt, support_prompt,
)
from vafer_eval.tasks import KeyItem, Task

TASK = Task(id="t1", stratum="S2", language="tr", prompt="Yalova'nın 2026 su tarifesi nedir?",
            items=(KeyItem("r01", "Tarifeyi verir.", "recall"), KeyItem("n01", "Eski yılı verir.", "negative")))


class PromptTests(unittest.TestCase):
    def test_arm_prompts(self):
        self.assertEqual(arm_prompt("A0", "claude", TASK), f"{TASK.prompt}\n\n{RUN_SUFFIX}")
        self.assertEqual(arm_prompt("A1", "codex", TASK), f"{TASK.prompt}\n\n{FANOUT_HINT} {RUN_SUFFIX}")
        self.assertTrue(arm_prompt("V", "claude", TASK).startswith("/vafer-research "))
        self.assertTrue(arm_prompt("V", "codex", TASK).startswith("$vafer-research "))
        self.assertEqual(arm_prompt("VI", "codex", TASK), arm_prompt("A0", "codex", TASK))
        self.assertTrue(arm_prompt("D", "claude", TASK).startswith("/deep-research "))
        self.assertEqual(arm_prompt("CB", "claude", TASK), f"{TASK.prompt}\n\n{CLOSED_BOOK_SUFFIX}")

    def test_invalid_arm_or_host(self):
        with self.assertRaisesRegex(ValueError, "arm D runs only on claude"):
            arm_prompt("D", "codex", TASK)
        with self.assertRaises(ValueError):
            arm_prompt("X", "claude", TASK)

    def test_item_prompt_keeps_unicode_and_negative_rule(self):
        text = item_grading_prompt(TASK, "Rapor metni ğüş", TASK.items)
        for fragment in ("r01", "n01", "Rapor metni ğüş", "Tarifeyi verir.", 'For items of kind "negative", "yes" means the report makes that error.'):
            self.assertIn(fragment, text)

    def test_support_prompt_numbers_pairs(self):
        text = support_prompt([("Claim one.", "Excerpt one."), ("Claim two.", "Excerpt two.")])
        self.assertIn("1. Claim: Claim one.", text)
        self.assertIn("2. Claim: Claim two.", text)

    def test_schemas_are_strict(self):
        for name in ("item_votes", "answer_set", "support_votes", "arm_guess"):
            schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
            self.assertIs(schema["additionalProperties"], False)
            self.assertEqual(sorted(schema["required"]), sorted(schema["properties"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_prompts.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `prompts.py` and the schemas**

Fixed text constants:

```python
RUN_SUFFIX = (
    "Work autonomously; nobody can answer questions during this run. "
    "Write the final report to report.md in the current directory, in the language of the question, "
    "with inline citations to the pages you used."
)
FANOUT_HINT = "If the question splits into independent parts, you may research them in parallel with subagents."
CLOSED_BOOK_SUFFIX = "Answer from what you already know, without using any tools. Reply with the full report as your final message."
SKILL_INVOCATION = {"claude": "/vafer-research", "codex": "$vafer-research"}
```

`item_grading_prompt` text (fixed; `{...}` placeholders are filled):

```text
You are grading a research report against a fixed list of items. Judge only what the report says; do not use outside knowledge and do not reward length or style.

For each item answer "yes" if the report explicitly states it or clearly entails it, "no" if the report omits it, contradicts it, or mentions it only vaguely, and "unknown" only if the item itself cannot be judged from any report.
For items of kind "negative", "yes" means the report makes that error.

Question:
<<<
{task.prompt}
>>>

Report:
<<<
{report_text}
>>>

Items (JSON):
{json.dumps([{"id": i.id, "kind": i.kind, "text": i.text} for i in items], ensure_ascii=False)}

Return JSON {"votes": [{"id": "<item id>", "verdict": "yes" | "no" | "unknown"}]} with one entry per item.
```

The other prompts are written in the same style:
- **`answer_set_prompt`:** gives the gold answers as a JSON list and asks for `{"matches": [{"gold": "...", "matched": true|false}], "extra_count": <distinct elements in the report's final answer that match no gold answer>}`.
- **`support_prompt`:** each pair is written as `"{n}. Claim: {claim}\n   Source excerpt: <<<{excerpt}>>>"`. The rule: supported means the excerpt states the claim or clearly entails it, including its numbers and dates; partial means it supports part of the claim; unsupported means it does not support or contradicts it. Judge only from the excerpt. Output: `{"verdicts": [{"n": 1, "verdict": "supported"|"partial"|"unsupported"}]}`.
- **`arm_guess_prompt`:** "A: a general assistant with web tools; B: the same assistant following a structured research procedure", output `{"guess": "A"|"B", "confidence": 0-1}`.

Schemas use OpenAI strict mode: every object sets `additionalProperties: false` and lists all of its properties under `required`.

- `item_votes`: `votes[]{id: string, verdict: enum yes/no/unknown}`
- `answer_set`: `matches[]{gold: string, matched: boolean}`, `extra_count: integer`
- `support_votes`: `verdicts[]{n: integer, verdict: enum supported/partial/unsupported}`
- `arm_guess`: `guess: enum A/B`, `confidence: number`

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/prompts.py evals/schemas evals/tests/test_prompts.py
git commit -m "feat(evals): arm and judge prompts with strict schemas" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Telemetry parsers

**Files:**
- Create: `evals/vafer_eval/telemetry.py`
- Create: `evals/tests/test_telemetry.py`
- Create: `evals/tests/fixtures/claude_stream.jsonl`, `evals/tests/fixtures/codex_events.jsonl`

**Interfaces:**
- Produces:
  - `@dataclass Telemetry(model: str | None, input_tokens: int | None, output_tokens: int | None, cost_usd: float | None, tool_calls: dict[str, int], web_searches: int, web_fetches: int, subagents: int, skill_invoked: bool, fetched: list[str], final_text: str, errors: list[str])`
  - `parse_claude_stream(lines: Iterable[str], skill: str = "vafer-research") -> Telemetry`
  - `parse_codex_events(lines: Iterable[str], skill: str = "vafer-research") -> Telemetry`
  - `scan_contamination(fetched: Sequence[str], needles: Sequence[str]) -> list[str]`
  - `telemetry_from_dict(data: dict) -> Telemetry`

- [ ] **Step 1: Write the fixtures**

These shapes are assumptions; Task 12 checks them against real logs. `claude_stream.jsonl` (the 6th line is deliberately not JSON):

```text
{"type":"system","subtype":"init","session_id":"s1","model":"claude-opus-5-5"}
{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Skill","input":{"skill":"vafer-research"}}]}}
{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t2","name":"WebSearch","input":{"query":"a"}},{"type":"tool_use","id":"t3","name":"WebSearch","input":{"query":"b"}}]}}
{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t4","name":"Agent","input":{"description":"r1","prompt":"p"}}]}}
{"type":"assistant","parent_tool_use_id":"t4","message":{"content":[{"type":"tool_use","id":"t5","name":"WebFetch","input":{"url":"https://example.org/a","prompt":"q"}}]}}
not json
{"type":"result","subtype":"success","result":"Final answer text","total_cost_usd":0.42,"usage":{"input_tokens":100,"cache_creation_input_tokens":20,"cache_read_input_tokens":30,"output_tokens":50}}
```

`codex_events.jsonl`:

```text
{"type":"thread.started","thread_id":"th1"}
{"type":"item.completed","item":{"id":"i1","type":"command_execution","command":"cat .agents/skills/vafer-research/SKILL.md","exit_code":0}}
{"type":"item.completed","item":{"id":"i2","type":"web_search","query":"a"}}
{"type":"item.completed","item":{"id":"i3","type":"web_search","query":"b"}}
{"type":"item.completed","item":{"id":"i4","type":"collab_tool_call","tool":"spawn_agent"}}
{"type":"item.completed","item":{"id":"i5","type":"command_execution","command":"curl -sL https://huggingface.co/x","exit_code":0}}
{"type":"item.completed","item":{"id":"i6","type":"agent_message","text":"Draft"}}
{"type":"item.completed","item":{"id":"i7","type":"agent_message","text":"Final answer text"}}
{"type":"turn.completed","usage":{"input_tokens":200,"cached_input_tokens":50,"output_tokens":70}}
```

- [ ] **Step 2: Write the failing test**

```python
# evals/tests/test_telemetry.py
from __future__ import annotations

import unittest
from pathlib import Path

from vafer_eval.telemetry import parse_claude_stream, parse_codex_events, scan_contamination

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def lines(name: str) -> list[str]:
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines()


class TelemetryTests(unittest.TestCase):
    def test_claude_stream(self):
        t = parse_claude_stream(lines("claude_stream.jsonl"))
        self.assertEqual(t.model, "claude-opus-5-5")
        self.assertEqual(t.tool_calls, {"Skill": 1, "WebSearch": 2, "Agent": 1, "WebFetch": 1})
        self.assertEqual((t.web_searches, t.web_fetches, t.subagents), (2, 1, 1))
        self.assertTrue(t.skill_invoked)
        self.assertEqual((t.input_tokens, t.output_tokens, t.cost_usd), (150, 50, 0.42))
        self.assertEqual(t.fetched, ["https://example.org/a"])
        self.assertEqual(t.final_text, "Final answer text")
        self.assertEqual(t.errors, ["line 6: not JSON"])

    def test_codex_events(self):
        t = parse_codex_events(lines("codex_events.jsonl"))
        self.assertEqual(t.tool_calls, {"command_execution": 2, "web_search": 2, "collab_tool_call": 1})
        self.assertEqual((t.web_searches, t.web_fetches, t.subagents), (2, 0, 1))
        self.assertTrue(t.skill_invoked)
        self.assertEqual((t.input_tokens, t.output_tokens, t.cost_usd), (200, 70, None))
        self.assertEqual(t.fetched, ["curl -sL https://huggingface.co/x"])
        self.assertEqual(t.final_text, "Final answer text")

    def test_skill_not_invoked_without_marker(self):
        t = parse_claude_stream(['{"type":"result","result":"x","usage":{}}'])
        self.assertFalse(t.skill_invoked)
        self.assertEqual(t.final_text, "x")

    def test_scan_contamination(self):
        found = scan_contamination(["curl -sL https://huggingface.co/x", "https://ok.example"], ["huggingface.co", "steel.dev"])
        self.assertEqual(found, ["huggingface.co"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_telemetry.py" -v` → Expected: ImportError

- [ ] **Step 4: Implement `telemetry.py`**

**Claude parser:**
- **Tool calls:** every `tool_use` block in `assistant` messages is counted, including subagent ones that carry `parent_tool_use_id`. `WebSearch` adds to web_searches; `WebFetch` adds to web_fetches and appends `input.url` to fetched; `Agent` or `Task` adds to subagents; a `Bash` command containing `http` is appended to fetched.
- **Skill detection:** set when `Skill` has `input.skill == skill`, or when a `Read` or `Bash` call includes the path `skills/{skill}/SKILL.md`.
- **Result event:**
  - input_tokens = input_tokens + cache_creation_input_tokens + cache_read_input_tokens (missing fields count as 0; None when there is no result event)
  - output_tokens, `total_cost_usd` and `result` are read directly
- **Model:** `model` from the `system/init` event.
- **Errors:** `line N: not JSON`.

**Codex parser:**
- **Items:** `item.completed` items are counted by type, except `agent_message` and `reasoning`. `web_search` adds to web_searches. `collab_tool_call` with a `tool` that starts with `spawn` adds to subagents.
- **Skill detection and fetched:** a `command_execution` command containing `skills/{skill}/SKILL.md` sets skill_invoked; one containing `http` is appended to fetched.
- **Tokens:** the sum of `input_tokens` and `output_tokens` over `turn.completed.usage`.
- **Other fields:** `final_text` is the last `agent_message.text`; `cost_usd=None`.

**`scan_contamination`:** returns, in the order given, every needle that appears case-insensitively in fetched.

- [ ] **Step 5: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add evals/vafer_eval/telemetry.py evals/tests/test_telemetry.py evals/tests/fixtures/claude_stream.jsonl evals/tests/fixtures/codex_events.jsonl
git commit -m "feat(evals): telemetry parsers for claude stream-json and codex events" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Trial runner

**Files:**
- Create: `evals/vafer_eval/runner.py`
- Create: `evals/tests/test_runner.py`

**Interfaces:**
- Consumes:
  - `Task` (Task 1)
  - `arm_prompt`, `ARMS`, `HOSTS` (Task 3)
  - `parse_claude_stream`, `parse_codex_events`, `scan_contamination`, `Telemetry`, `telemetry_from_dict` (Task 4)
- Produces:
  - `@dataclass(frozen=True) Budget(name: str, seconds: int, searches: int)`
  - `BUDGETS = {"smoke": Budget("smoke", 300, 10), "P": Budget("P", 900, 60), "G": Budget("G", 2400, 150)}`
  - `DEFAULT_BLOCKED_HOSTS = ("hf.co", "huggingface.co", "steel.dev")`
  - `CONTAMINATION_NEEDLES = ("huggingface.co", "hf.co", "steel.dev", "deepresearch-bench", "deepsearchqa", "widesearch")`
  - `@dataclass(frozen=True) TrialSpec(host: str, arm: str, task: Task, trial: int, budget: Budget)`
  - `@dataclass TrialResult(trial_id: str, host: str, arm: str, task_id: str, trial: int, wall_s: float, timed_out: bool, exit_code: int | None, report_text: str, telemetry: Telemetry, contamination: list[str])`
  - `trial_id(spec: TrialSpec) -> str`
  - `blocked_hosts(task: Task) -> list[str]`
  - `prepare_trial_dir(spec: TrialSpec, root: Path, skill_src: Path | None) -> Path`
  - `build_command(spec: TrialSpec, trial_dir: Path, env: Mapping[str, str]) -> tuple[list[str], dict[str, str]]`
  - `kill_tree(proc: subprocess.Popen) -> None`
  - `run_trial(spec, root, skill_src=None, env=os.environ, command_override=None) -> TrialResult`
  - `run_matrix(specs, root, skill_src=None, parallel=4, env=os.environ, command_override=None) -> list[TrialResult]`
  - `load_result(trial_dir: Path) -> TrialResult`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_runner.py
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from vafer_eval.runner import (
    BUDGETS, Budget, TrialSpec, blocked_hosts, build_command, load_result, prepare_trial_dir, run_matrix, run_trial, trial_id,
)
from vafer_eval.tasks import KeyItem, Task

TASK = Task(id="drb2-task1", stratum="S2", language="en", prompt="Türkçe ğüşıöç 中文",
            items=tuple(KeyItem(f"r{i:02d}", "x", "recall") for i in range(1, 11)),
            blocked_urls=("https://www.mdpi.com/x", "https://doi.org/10.1/y"))
ENV = {"VAFER_EVAL_CLAUDE_CONFIG": "C:/profile", "PATH": os.environ.get("PATH", "")}
PY = [sys.executable, "-X", "utf8", "-c"]


def spec(host="claude", arm="A0", budget=BUDGETS["P"], task=TASK, trial=1) -> TrialSpec:
    return TrialSpec(host=host, arm=arm, task=task, trial=trial, budget=budget)


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.skill = self.root / "skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text("---\nname: vafer-research\n---\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_trial_id_and_blocked_hosts(self):
        self.assertEqual(trial_id(spec()), "drb2-task1__claude__A0__t1")
        self.assertEqual(blocked_hosts(TASK), ["doi.org", "hf.co", "huggingface.co", "mdpi.com", "steel.dev"])

    def test_prepare_installs_skill_only_for_skill_arms(self):
        v = prepare_trial_dir(spec(arm="V"), self.root / "runs", self.skill)
        self.assertTrue((v / ".claude/skills/vafer-research/SKILL.md").exists())
        vi = prepare_trial_dir(spec(host="codex", arm="VI"), self.root / "runs", self.skill)
        self.assertTrue((vi / ".agents/skills/vafer-research/SKILL.md").exists())
        a0 = prepare_trial_dir(spec(arm="A0", trial=2), self.root / "runs", self.skill)
        self.assertFalse((a0 / ".claude/skills").exists())
        deny = json.loads((a0 / ".claude/settings.json").read_text(encoding="utf-8"))["permissions"]["deny"]
        self.assertIn("WebFetch(domain:mdpi.com)", deny)
        self.assertEqual((a0 / "prompt.txt").read_text(encoding="utf-8").splitlines()[0], TASK.prompt)

    def test_prepare_refuses_existing_result(self):
        d = prepare_trial_dir(spec(), self.root / "runs", None)
        (d / "result.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            prepare_trial_dir(spec(), self.root / "runs", None)

    def test_build_command_claude(self):
        argv, env = build_command(spec(), self.root, ENV)
        self.assertEqual(argv[:2], ["claude", "-p"])
        self.assertIn("--strict-mcp-config", argv)
        self.assertNotIn(TASK.prompt, " ".join(argv))
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], "C:/profile")
        self.assertEqual(env["CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION"], "60")

    def test_build_command_codex(self):
        argv, _ = build_command(spec(host="codex"), self.root, ENV)
        self.assertEqual(argv[:2], ["codex", "exec"])
        self.assertIn("--ignore-user-config", argv)
        self.assertIn('web_search="live"', argv)
        self.assertEqual(argv[-1], "-")
        cb, _ = build_command(spec(host="codex", arm="CB"), self.root, ENV)
        self.assertIn("read-only", cb)

    def test_build_command_requires_claude_profile(self):
        with self.assertRaisesRegex(ValueError, "VAFER_EVAL_CLAUDE_CONFIG"):
            build_command(spec(), self.root, {"PATH": ""})

    def test_run_trial_reads_report_and_stdin_utf8(self):
        code = ("import sys,pathlib; p=sys.stdin.read(); pathlib.Path('report.md').write_text(p, encoding='utf-8');"
                "print('{\"type\":\"result\",\"result\":\"x\",\"usage\":{}}')")
        result = run_trial(spec(), self.root / "runs", env=ENV, command_override=PY + [code])
        self.assertIn("Türkçe ğüşıöç 中文", result.report_text)
        self.assertFalse(result.timed_out)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(load_result(self.root / "runs" / trial_id(spec())).report_text, result.report_text)

    def test_run_trial_falls_back_to_final_text_then_empty(self):
        final = run_trial(spec(trial=1), self.root / "runs", env=ENV,
                          command_override=PY + ["print('{\"type\":\"result\",\"result\":\"Final\",\"usage\":{}}')"])
        self.assertEqual(final.report_text, "Final")
        empty = run_trial(spec(trial=2), self.root / "runs", env=ENV, command_override=PY + ["pass"])
        self.assertEqual(empty.report_text, "")
        self.assertTrue((self.root / "runs" / trial_id(spec(trial=2)) / "result.json").exists())

    def test_run_trial_timeout_kills_tree(self):
        code = ("import subprocess,sys,pathlib,time;"
                "c=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
                "pathlib.Path('child.pid').write_text(str(c.pid)); time.sleep(60)")
        started = time.monotonic()
        result = run_trial(spec(budget=Budget("t", 2, 1)), self.root / "runs", env=ENV, command_override=PY + [code])
        self.assertTrue(result.timed_out)
        self.assertLess(time.monotonic() - started, 20)
        child = int((self.root / "runs" / trial_id(spec()) / "child.pid").read_text())
        time.sleep(1)
        self.assertFalse(pid_alive(child))

    def test_run_matrix_runs_all(self):
        specs = [spec(trial=i) for i in range(1, 5)]
        results = run_matrix(specs, self.root / "runs", env=ENV, parallel=2,
                             command_override=PY + ["print('{\"type\":\"result\",\"result\":\"ok\",\"usage\":{}}')"])
        self.assertEqual(sorted(r.trial for r in results), [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_runner.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `runner.py`**

**`prepare_trial_dir`:**
- Creates `root/trial_id`. Raises `FileExistsError` if `result.json` already exists.
- **V/VI:** copytree skill_src to `.claude/skills/vafer-research` (claude) or `.agents/skills/vafer-research` (codex); without skill_src, raises `ValueError("arm V needs skill_src")`.
- **claude (all arms):** writes `.claude/settings.json` = `{"permissions": {"deny": [f"WebFetch(domain:{h})" for h in blocked_hosts(task)]}}`.
- Writes `prompt.txt` with `arm_prompt(spec.arm, spec.host, spec.task)`.

**`blocked_hosts`:** DEFAULT_BLOCKED_HOSTS plus the netlocs of `task.blocked_urls`, with `www.` stripped; unique and sorted.

**`build_command`:**
- **claude:**
  - Base: `["claude", "-p", "--output-format", "stream-json", "--verbose", "--strict-mcp-config", "--permission-mode", "bypassPermissions"]`.
  - If `VAFER_EVAL_CLAUDE_MODEL` is set, add `--model`.
  - For CB, add `["--disallowedTools", "WebSearch,WebFetch,Bash,Agent,Task,Skill,Write,Edit,Read,Glob,Grep"]`.
  - env = copy of env, plus `CLAUDE_CONFIG_DIR=env["VAFER_EVAL_CLAUDE_CONFIG"]` (missing → `ValueError("set VAFER_EVAL_CLAUDE_CONFIG")`) and `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION=str(budget.searches)`.
- **codex:**
  - Base: `["codex", "exec", "--json", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "-C", str(trial_dir), "-o", str(trial_dir / "last_message.txt")]`.
  - CB: `["-s", "read-only", "-c", 'web_search="disabled"']`; otherwise `["-s", "workspace-write", "-c", 'web_search="live"']`.
  - If `VAFER_EVAL_CODEX_MODEL` is set, add `-m`. The last element is `"-"` (read the prompt from stdin).
- **D on codex:** raises `ValueError`.

**`run_trial`:**
- Starts the process with `Popen(cwd=trial_dir, stdin=PIPE, stdout=<events.jsonl>, stderr=<stderr.txt>, env=..., text=True, encoding="utf-8")`, in a new process group (Windows `CREATE_NEW_PROCESS_GROUP`, POSIX `start_new_session=True`).
- Writes prompt.txt to stdin and closes it. `wait(timeout=budget.seconds)`; on `TimeoutExpired`, calls `kill_tree` and sets timed_out=True.
- **Report:** `report.md` → (codex) `last_message.txt` → `telemetry.final_text` → `""`.
- **Contamination:** `scan_contamination(telemetry.fetched, CONTAMINATION_NEEDLES + tuple(blocked_hosts(task)))`.
- Writes `result.json`; the record is the TrialResult fields plus `telemetry` as a dict.

**`kill_tree`:** Windows: `subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)`; POSIX: `os.killpg(proc.pid, signal.SIGKILL)`.

**`run_matrix`:** `ThreadPoolExecutor(max_workers=parallel)`. Specs are sorted by `(task.id, trial, arm)`, so the arms of the same task and trial start together.

**`load_result`:** rebuilds a TrialResult from `result.json` (telemetry via `telemetry_from_dict`).

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/runner.py evals/tests/test_runner.py
git commit -m "feat(evals): isolated trial runner with hard timeouts" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Blinding normalizer

**Files:**
- Create: `evals/vafer_eval/normalize.py`
- Create: `evals/tests/test_normalize.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) NormalizedReport(text: str, sources: tuple[str, ...])`
  - `METHOD_HEADINGS = ("method", "methods", "methodology", "method note", "yöntem", "yöntem notu", "research log", "run log", "process")`
  - `SOURCE_HEADINGS = ("sources", "references", "kaynaklar", "kaynakça", "bibliography")`
  - `SYSTEM_NAMES = ("ultra-deep-research", "vafer-research", "/deep-research", "vafer")`
  - `normalize_report(raw: str) -> NormalizedReport`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_normalize.py
from __future__ import annotations

import unittest

from vafer_eval.normalize import normalize_report

RAW = """# Report

<!-- Canonical evidence: [[s1a2@b3c4:p000001]] -->
Magna Carta was sealed in 1215 [1]. See [the archive](https://archive.example.org/mc) and https://other.example.org/page.

Generated with vafer-research in C:\\Users\\me\\proj\\.vafer\\research\\x.

## Method note
Tier: Standard; 12 searches.

## Sources
[1] Archive page, https://archive.example.org/mc
"""

EXPECTED = """# Report

Magna Carta was sealed in 1215 [1]. See the archive [1] and [2].

Generated with in [path].

## Sources
[1] https://archive.example.org/mc
[2] https://other.example.org/page"""


class NormalizeTests(unittest.TestCase):
    def test_full_example(self):
        report = normalize_report(RAW)
        self.assertEqual(report.text, EXPECTED)
        self.assertEqual(report.sources, ("https://archive.example.org/mc", "https://other.example.org/page"))

    def test_unknown_numeric_citation_kept(self):
        self.assertEqual(normalize_report("A claim [7].").text, "A claim [7].")

    def test_turkish_method_heading_removed(self):
        text = normalize_report("# R\n\nBody.\n\n## Yöntem notu\nTier Quick.\n\n## Sonuç\nEnd.").text
        self.assertNotIn("Tier Quick", text)
        self.assertIn("## Sonuç\nEnd.", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_normalize.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `normalize_report`**

The steps run in this order:
1. Delete `<!--.*?-->` (DOTALL).
2. Delete `\[\[[^\]]*\]\]`.
3. Headings: for `^(#{1,6})\s+(.+?)\s*$`, take the title lowercased with any trailing `:` removed.
   - If it is in METHOD_HEADINGS, delete the section up to the next heading of the same or a higher level.
   - If it is in SOURCE_HEADINGS, parse the lines with `^\s*(?:\[(\d+)\]|(\d+)[.)])\s*(.*)$` and map k to the line's first URL, then delete the section.
4. Make one left-to-right pass with a single alternation regex, `\[([^\]]+)\]\((https?://[^)\s]+)\)` | `\[(\d+)\]` | `https?://[^\s)>\]]+`:
   - a link becomes `label [n]`;
   - a known numeric citation becomes `[n]` (an unknown one stays as written);
   - a bare URL becomes `[n]`, with trailing `.,;:` left in the text.
   `n` is the global first-appearance order.
5. Replace `[A-Za-z]:\\[^\s)\]]*[^\s)\].,;:]` and `\.vafer/[^\s)\]]*[^\s)\].,;:]` with `[path]`. Then delete SYSTEM_NAMES case-insensitively (in the order given).
6. Collapse runs of spaces/tabs inside a line to a single space, trim line ends, and collapse 3 or more line breaks to 2. `strip()`.
7. If there are sources, append `\n\n## Sources\n` + `[i] url` lines.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/normalize.py evals/tests/test_normalize.py
git commit -m "feat(evals): report normalizer for blind judging" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Item and answer grading, judge invocation

**Files:**
- Create: `evals/vafer_eval/grading.py`
- Create: `evals/tests/test_grading.py`

**Interfaces:**
- Consumes: `Task`, `KeyItem`, `SCHEMA_DIR` (Task 3)
- Produces:
  - `batch_items(items: Sequence[KeyItem], size: int = 50) -> list[list[KeyItem]]`
  - `parse_json_payload(text: str) -> object`
  - `parse_votes(text: str, expected_ids: Sequence[str]) -> dict[str, str]`
  - `combine(first: Mapping[str, str], second: Mapping[str, str], tiebreak: Sequence[Mapping[str, str]] = ()) -> dict[str, str]`
  - `tiebreak_family(report_host: str) -> str`
  - `score_items(task: Task, verdicts: Mapping[str, str]) -> float | None`
  - `presentation_score(task: Task, verdicts: Mapping[str, str]) -> float | None`
  - `parse_answer_matches(text: str, gold: Sequence[str]) -> tuple[dict[str, bool], int]`
  - `answer_f1(matched: Mapping[str, bool], extra_count: int) -> float`
  - `judge_command(family: str, schema_path: Path, out_path: Path) -> list[str]`
  - `run_judge(family: str, prompt: str, schema_name: str, workdir: Path, env: Mapping[str, str] = os.environ, timeout: int = 600) -> str`
  - `arm_guess_accuracy(guesses: Sequence[str], truths: Sequence[str]) -> float`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_grading.py
from __future__ import annotations

import unittest
from pathlib import Path

from vafer_eval.grading import (
    answer_f1, arm_guess_accuracy, batch_items, combine, judge_command, parse_answer_matches, parse_votes,
    presentation_score, score_items, tiebreak_family,
)
from vafer_eval.tasks import KeyItem, Task

ITEMS = (KeyItem("r01", "a", "recall"), KeyItem("r02", "b", "recall"), KeyItem("a01", "c", "analysis"),
         KeyItem("a02", "d", "analysis"), KeyItem("n01", "e", "negative"), KeyItem("n02", "f", "negative"),
         KeyItem("p01", "g", "presentation"))
TASK = Task(id="t", stratum="S1", language="tr", prompt="q", items=ITEMS, as_of="2026-10-27")


class GradingTests(unittest.TestCase):
    def test_parse_votes_with_code_fence(self):
        text = '```json\n{"votes": [{"id": "r01", "verdict": "yes"}, {"id": "r02", "verdict": "no"}]}\n```'
        self.assertEqual(parse_votes(text, ["r01", "r02"]), {"r01": "yes", "r02": "no"})

    def test_parse_votes_missing_and_invalid(self):
        text = '{"votes": [{"id": "r01", "verdict": "maybe"}, {"id": "zz", "verdict": "yes"}]}'
        self.assertEqual(parse_votes(text, ["r01", "r02"]), {"r01": "unknown", "r02": "unknown"})

    def test_parse_votes_garbage(self):
        self.assertEqual(parse_votes("I cannot comply.", ["r01"]), {"r01": "unknown"})

    def test_combine(self):
        self.assertEqual(combine({"x": "yes"}, {"x": "yes"}), {"x": "yes"})
        self.assertEqual(combine({"x": "yes"}, {"x": "no"}, [{"x": "no"}, {"x": "no"}, {"x": "yes"}]), {"x": "no"})
        self.assertEqual(combine({"x": "yes"}, {"x": "no"}, [{"x": "yes"}, {"x": "no"}, {"x": "unknown"}]), {"x": "unknown"})
        self.assertEqual(combine({"x": "yes"}, {"x": "no"}), {"x": "unknown"})

    def test_tiebreak_family(self):
        self.assertEqual(tiebreak_family("claude"), "gpt")
        self.assertEqual(tiebreak_family("codex"), "claude")
        with self.assertRaises(ValueError):
            tiebreak_family("other")

    def test_score_items_with_negative_penalty(self):
        verdicts = {"r01": "yes", "r02": "yes", "a01": "no", "a02": "unknown", "n01": "yes", "n02": "no", "p01": "yes"}
        self.assertAlmostEqual(score_items(TASK, verdicts), 2 / 3 - 1 / 4)
        self.assertEqual(presentation_score(TASK, verdicts), 1.0)
        self.assertIsNone(score_items(TASK, {}))

    def test_answer_f1(self):
        matched, extra = parse_answer_matches(
            '{"matches": [{"gold": "A", "matched": true}, {"gold": "B", "matched": true}, {"gold": "C", "matched": false}], "extra_count": 1}',
            ["A", "B", "C"])
        self.assertEqual((matched, extra), ({"A": True, "B": True, "C": False}, 1))
        self.assertAlmostEqual(answer_f1(matched, extra), 2 / 3)
        self.assertEqual(answer_f1({"A": False}, 0), 0.0)

    def test_batches_and_commands(self):
        self.assertEqual([len(b) for b in batch_items(ITEMS * 10, size=50)], [50, 20])
        claude = judge_command("claude", Path("s.json"), Path("o.txt"))
        self.assertEqual(claude[:2], ["claude", "-p"])
        self.assertIn("--json-schema", claude)
        gpt = judge_command("gpt", Path("s.json"), Path("o.txt"))
        self.assertEqual(gpt[:2], ["codex", "exec"])
        self.assertIn("--output-schema", gpt)
        self.assertEqual(gpt[-1], "-")

    def test_arm_guess_accuracy(self):
        self.assertAlmostEqual(arm_guess_accuracy(["A", "B", "B"], ["A", "A", "B"]), 2 / 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_grading.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `grading.py`**

**Parsing:**
- `parse_json_payload` strips the ```` ``` ```` fence and parses the text between the first `{` and the last `}`; on failure it raises `ValueError`.
- `parse_votes` catches that error, so every id becomes `unknown`. A verdict outside `yes`/`no`/`unknown` also becomes `unknown`. Ids that were not requested are ignored.

**`combine`:**
- If the two votes match, that vote stands.
- Otherwise the `yes`/`no` votes in `tiebreak` decide by majority. A tie, or no tiebreak votes, gives `unknown`.

**`score_items`:**
- Positives are the recall and analysis items; judged positives are those with a `yes`/`no` verdict. If there are no judged positives, return None.
- Score `max(0, yes_pos/len(judged_pos) - negative_yes/len(positives))`.

**`presentation_score`:** `yes/(yes+no)` over the presentation items, or None.

**`answer_f1`:**
- tp = number of matches, recall = tp/len(gold), precision = tp/(tp+extra) (0 if the denominator is 0).
- F1 is the harmonic mean, or 0.

**`judge_command`:**
- claude: `["claude", "-p", "--output-format", "json", "--strict-mcp-config", "--json-schema", schema_path.read_text(encoding="utf-8") if it exists else str(schema_path)]`
- gpt: `["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "-s", "read-only", "--output-schema", str(schema_path), "-o", str(out_path), "-"]`
- The test passes nonexistent paths, so judge_command must not read a file that does not exist.

**`run_judge`:**
- Gives the prompt on stdin (UTF-8); `cwd=workdir`, which is an empty temporary directory.
- For claude, sets `CLAUDE_CONFIG_DIR` from `VAFER_EVAL_CLAUDE_CONFIG`.
- Returns, for claude, `structured_output` from the stdout JSON (serialized with `json.dumps`) if present, else `result`; for gpt, the content of `out_path`.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/grading.py evals/tests/test_grading.py
git commit -m "feat(evals): binary item grading with two-family judges" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Claim support (co-primary metric S)

**Files:**
- Create: `evals/vafer_eval/citations.py`
- Create: `evals/tests/test_citations.py`

**Interfaces:**
- Consumes: `NormalizedReport` (Task 6)
- Produces:
  - `@dataclass(frozen=True) Claim(sentence: str, source_numbers: tuple[int, ...])`
  - `@dataclass(frozen=True) FetchResult(url: str, status: str, text: str)`, where status is one of `ok`, `refused`, `http-error`, `error`, `empty`, `too-large`
  - `class RefusedURL(urllib.error.URLError)`
  - `class SafeRedirectHandler(urllib.request.HTTPRedirectHandler)` with `__init__(self, resolver=socket.getaddrinfo)`
  - `extract_claims(report: NormalizedReport) -> list[Claim]`
  - `is_public_http_url(url: str, resolver=socket.getaddrinfo) -> bool`
  - `html_to_text(html: str) -> str`
  - `fetch_text(url: str, cache_dir: Path, *, timeout: float = 20.0, max_bytes: int = 5_000_000, allow_private: bool = False) -> FetchResult`
  - `best_excerpt(claim: str, text: str, max_chars: int = 6000) -> str`
  - `supported_claim_rate(verdicts: Sequence[str]) -> tuple[float | None, int]`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_citations.py
from __future__ import annotations

import socket
import tempfile
import threading
import unittest
import urllib.request
from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from vafer_eval.citations import (
    Claim, RefusedURL, SafeRedirectHandler, best_excerpt, extract_claims, fetch_text, is_public_http_url,
    supported_claim_rate,
)
from vafer_eval.normalize import NormalizedReport


def resolver_for(ip: str):
    return lambda host, port, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/page":
            body = b"<html><script>var x=1;</script><p>Sealed in 1215.</p></html>"
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        elif self.path == "/big":
            body = b"a" * 2000
            self.send_response(200); self.send_header("Content-Type", "text/plain")
        else:
            body = b"no"
            self.send_response(404); self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *args):
        pass


class CitationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_extract_claims(self):
        report = NormalizedReport(
            "# Report\n\nMagna Carta was sealed in 1215 [1]. It was reissued in 1216 [1][2]. No citation here.\n\n"
            "## Sources\n[1] https://a.example\n[2] https://b.example",
            ("https://a.example", "https://b.example"))
        self.assertEqual(extract_claims(report), [
            Claim("Magna Carta was sealed in 1215.", (1,)), Claim("It was reissued in 1216.", (1, 2))])

    def test_public_url_check(self):
        self.assertTrue(is_public_http_url("https://x.example/a", resolver=resolver_for("93.184.216.34")))
        self.assertFalse(is_public_http_url("https://x.example/a", resolver=resolver_for("10.0.0.5")))
        self.assertFalse(is_public_http_url("ftp://x.example/a", resolver=resolver_for("93.184.216.34")))
        self.assertFalse(is_public_http_url("file:///etc/passwd"))

    def test_redirect_to_private_ip_refused(self):
        handler = SafeRedirectHandler(resolver=resolver_for("10.0.0.5"))
        req = urllib.request.Request("https://public.example/a")
        with self.assertRaises(RefusedURL):
            handler.redirect_request(req, None, 302, "Found", Message(), "http://internal.example/x")

    def test_fetch_ok_and_cached(self):
        first = fetch_text(self.base + "/page", self.cache, allow_private=True)
        self.assertEqual(first.status, "ok")
        self.assertIn("Sealed in 1215.", first.text)
        self.assertNotIn("var x", first.text)
        self.assertEqual(fetch_text(self.base + "/page", self.cache, allow_private=True), first)

    def test_too_large_and_http_error_and_refused(self):
        self.assertEqual(fetch_text(self.base + "/big", self.cache, allow_private=True, max_bytes=1000).status, "too-large")
        self.assertEqual(fetch_text(self.base + "/missing", self.cache, allow_private=True).status, "http-error")
        self.assertEqual(fetch_text(self.base + "/page", self.cache / "other").status, "refused")

    def test_best_excerpt_prefers_matching_paragraph(self):
        text = "Unrelated opening.\n\nThe charter was sealed at Runnymede in 1215.\n\nLater history."
        self.assertTrue(best_excerpt("It was sealed in 1215.", text, max_chars=60).startswith("The charter was sealed"))

    def test_supported_claim_rate(self):
        self.assertEqual(supported_claim_rate(["supported", "partial", "unsupported", "unreachable", "supported"]), (0.5, 2))
        self.assertEqual(supported_claim_rate(["unreachable"]), (None, 0))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_citations.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `citations.py`**

**`extract_claims`:**
- Use the text before `## Sources`, skip lines that start with `#`, split paragraphs on `(?<=[.!?])\s+`, and attach a leading `^(\[\d+\]\s*)+` group to the previous sentence.
- Keep sentences with at least one `[n]`. Remove `\s*\[\d+\]` from the sentence text. `source_numbers` holds the unique numbers in order.

**`is_public_http_url`:**
- The scheme must be http/https and the host must not be empty.
- Every address returned by `resolver(host, None)` must pass `ipaddress.ip_address` with `is_private`, `is_loopback`, `is_link_local`, `is_multicast`, `is_reserved` and `is_unspecified` all false.
- Any exception returns False.

**`SafeRedirectHandler.redirect_request`:** if the target is not public, raises `RefusedURL(newurl)`; otherwise calls super.

**`fetch_text`:**
1. Cache: `cache_dir/sha256(url).json`; a hit returns that FetchResult.
2. If `not allow_private and not is_public_http_url(url)`, the status is `refused`.
3. Build the opener with `build_opener(SafeRedirectHandler(...))`. When allow_private is set, use a plain opener.
4. Read: `read(max_bytes + 1)`; anything longer is `too-large`.
5. Content type:
   - `text/html`: `html_to_text`, an HTMLParser that skips script/style;
   - `text/plain`: decode as is (charset from the header, else UTF-8, with `errors="replace"`);
   - anything else, PDF included: `empty`. PDF support comes with M2.
6. Errors: `HTTPError` → `http-error`; `RefusedURL` → `refused`; other `URLError`/`OSError`/timeouts → `error`. A refused result is not written to the cache; every other result is.

**`best_excerpt`:**
- Score each paragraph by how many of the claim's lowercase words (4+ letters) and digit tokens it shares.
- Return text of at most `max_chars`, starting at the highest-scoring paragraph.

**`supported_claim_rate`:** returns `(supported / (supported+partial+unsupported) or None, supported)`.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/citations.py evals/tests/test_citations.py
git commit -m "feat(evals): claim extraction and SSRF-safe source fetching" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Paired statistics

**Files:**
- Create: `evals/vafer_eval/stats.py`
- Create: `evals/tests/test_stats.py`

**Interfaces:**
- Produces:
  - `miller_n(omega: float, sigma: float, k: int, delta: float, alpha: float = 0.05, power: float = 0.8) -> int`
  - `paired_bootstrap(deltas: Sequence[float], n_resamples: int = 10_000, seed: int = 20261027, level: float = 0.95) -> tuple[float, float, float]`
  - `bootstrap_p(deltas: Sequence[float], n_resamples: int = 10_000, seed: int = 20261027) -> float`
  - `win_tie_loss(a: Sequence[float], b: Sequence[float], tie: float = 0.01) -> tuple[int, int, int]`
  - `holm(pvalues: Sequence[float]) -> list[float]`
  - `estimate_components(scores: Mapping[str, Mapping[str, Sequence[float]]], arm_a: str, arm_b: str) -> tuple[float, float]`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_stats.py
from __future__ import annotations

import unittest

from vafer_eval.stats import bootstrap_p, estimate_components, holm, miller_n, paired_bootstrap, win_tie_loss


class StatsTests(unittest.TestCase):
    def test_miller_n(self):
        self.assertEqual(miller_n(8, 10, 3, 5), 42)
        self.assertEqual(miller_n(12, 10, 3, 5), 67)
        self.assertEqual(miller_n(12, 10, 3, 8), 26)

    def test_bootstrap(self):
        self.assertEqual(paired_bootstrap([1.0] * 10), (1.0, 1.0, 1.0))
        mean, lo, hi = paired_bootstrap([0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertEqual(mean, 2.0)
        self.assertLessEqual(lo, 2.0)
        self.assertGreaterEqual(hi, 2.0)
        self.assertEqual(paired_bootstrap([0.0, 1.0, 2.0]), paired_bootstrap([0.0, 1.0, 2.0]))
        self.assertEqual(bootstrap_p([1.0, 2.0, 3.0]), 0.0)

    def test_win_tie_loss(self):
        self.assertEqual(win_tie_loss([5, 3, 1], [2, 3, 4], tie=1.0), (1, 1, 1))

    def test_holm(self):
        for got, want in zip(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06]):
            self.assertAlmostEqual(got, want)

    def test_estimate_components(self):
        scores = {"t1": {"A0": [0.2, 0.4], "V": [0.5, 0.7]}, "t2": {"A0": [0.6, 0.6], "V": [0.6, 0.8]}}
        omega, sigma = estimate_components(scores, "A0", "V")
        self.assertAlmostEqual(omega, 0.141421, places=5)
        self.assertAlmostEqual(sigma, 0.122474, places=5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_stats.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `stats.py`**

- **`miller_n`:** `math.ceil((z(1-alpha/2) + z(power))**2 * (omega**2 + 2*sigma**2/k) / delta**2)`, where `z = statistics.NormalDist().inv_cdf`.
- **`paired_bootstrap`:** `random.Random(seed)`; resample with replacement `n_resamples` times and take the percentiles `(1-level)/2` and `1-(1-level)/2` (sort and index). The returned mean is the plain mean.
- **`bootstrap_p`:** `min(1, 2 * share of resampled means whose sign is opposite to the observed mean (or zero))`; for an all-positive series it is 0.0.
- **`win_tie_loss`:** `abs(a-b) < tie` is a tie.
- **`holm`:** the standard step-down adjustment, kept monotone and capped at 1, returned in the original order.
- **`estimate_components`:** omega = `statistics.stdev` of the per-task `mean(b) - mean(a)`; sigma = `sqrt(mean(statistics.variance(trials) for each task and arm))`.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/stats.py evals/tests/test_stats.py
git commit -m "feat(evals): paired statistics and sample sizing" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Grading and citation pipelines

**Files:**
- Create: `evals/vafer_eval/pipeline.py`
- Create: `evals/tests/test_pipeline.py`

**Interfaces:**
- Consumes: `load_result` (Task 5), `normalize_report` (Task 6), `grading.*` (Task 7), `citations.*` (Task 8), `prompts.*` (Task 3)
- Produces:
  - `Judge = Callable[[str, str, str, Path], str]`: `(family, prompt, schema_name, workdir) -> raw text`
  - `grade_trial(trial_dir: Path, task: Task, judge: Judge) -> dict`, which writes `grade.json` = `{"r", "presentation", "verdicts", "judge_disagreements"}`
  - `grade_runs(runs_dir: Path, tasks: Mapping[str, Task], judge: Judge) -> int`
  - `cite_trial(trial_dir: Path, judge: Judge, fetcher: Callable[[str, Path], FetchResult]) -> dict`, which writes `cite.json` = `{"s", "supported", "claims", "unreachable"}`
  - `cite_runs(runs_dir: Path, judge: Judge, fetcher=...) -> int`
  - `guess_runs(runs_dir: Path, arm_a: str, arm_b: str, n: int, judge: Judge, seed: int = 20261027) -> float`
  - `default_judge(family, prompt, schema_name, workdir) -> str`, which calls `run_judge` and creates a new empty temporary directory for each call

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_pipeline.py
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vafer_eval.citations import FetchResult
from vafer_eval.pipeline import cite_trial, grade_runs, grade_trial
from vafer_eval.tasks import KeyItem, Task

TASK = Task(id="drb2-t", stratum="S2", language="en", prompt="q",
            items=tuple(KeyItem(f"r{i:02d}", "x", "recall") for i in range(1, 11)))


def write_trial(root: Path, report: str, host: str = "claude") -> Path:
    d = root / f"drb2-t__{host}__A0__t1"
    d.mkdir(parents=True)
    result = {"trial_id": d.name, "host": host, "arm": "A0", "task_id": "drb2-t", "trial": 1, "wall_s": 1.0,
              "timed_out": False, "exit_code": 0, "report_text": report, "contamination": [],
              "telemetry": {"model": None, "input_tokens": None, "output_tokens": None, "cost_usd": None,
                            "tool_calls": {}, "web_searches": 0, "web_fetches": 0, "subagents": 0,
                            "skill_invoked": False, "fetched": [], "final_text": "", "errors": []}}
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    return d


class FakeJudge:
    def __init__(self, by_family):
        self.by_family, self.calls = by_family, []

    def __call__(self, family, prompt, schema_name, workdir):
        self.calls.append(family)
        return self.by_family[family]


def votes(verdict: str) -> str:
    return json.dumps({"votes": [{"id": f"r{i:02d}", "verdict": verdict} for i in range(1, 11)]})


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_grade_trial_agreement(self):
        d = write_trial(self.root, "A report.")
        grade = grade_trial(d, TASK, FakeJudge({"claude": votes("yes"), "gpt": votes("yes")}))
        self.assertEqual((grade["r"], grade["judge_disagreements"]), (1.0, 0))
        self.assertTrue((d / "grade.json").exists())

    def test_grade_trial_disagreement_uses_other_family_tiebreak(self):
        d = write_trial(self.root, "A report.", host="claude")
        judge = FakeJudge({"claude": votes("yes"), "gpt": votes("no")})
        grade = grade_trial(d, TASK, judge)
        self.assertEqual((grade["r"], grade["judge_disagreements"]), (0.0, 10))
        self.assertEqual(judge.calls.count("claude"), 1)
        self.assertEqual(judge.calls.count("gpt"), 4)

    def test_grade_trial_empty_report_scores_zero(self):
        d = write_trial(self.root, "")
        grade = grade_trial(d, TASK, FakeJudge({"claude": votes("no"), "gpt": votes("no")}))
        self.assertEqual(grade["r"], 0.0)

    def test_grade_runs_skips_graded(self):
        write_trial(self.root, "A report.")
        judge = FakeJudge({"claude": votes("yes"), "gpt": votes("yes")})
        self.assertEqual(grade_runs(self.root, {"drb2-t": TASK}, judge), 1)
        self.assertEqual(grade_runs(self.root, {"drb2-t": TASK}, judge), 0)

    def test_cite_trial(self):
        d = write_trial(self.root, "First claim https://a.example/x. Second claim https://b.example/y.")
        judge = FakeJudge({"gpt": json.dumps({"verdicts": [{"n": 1, "verdict": "supported"}, {"n": 2, "verdict": "unsupported"}]})})
        fetcher = lambda url, cache: FetchResult(url, "ok", "First claim text. Second claim text.")
        cite = cite_trial(d, judge, fetcher)
        self.assertEqual((cite["s"], cite["supported"], cite["claims"], cite["unreachable"]), (0.5, 1, 2, 0))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_pipeline.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `pipeline.py`**

**`grade_trial`:** `report = normalize_report(result.report_text).text`.
- **S1/S2:** for each 50-item batch:
  1. Get the "claude" and "gpt" votes for the same prompt.
  2. If they disagree on even one item, take 3 more votes from `tiebreak_family(host)` with the same prompt.
  3. Combine them with `combine`.

  `r = score_items`, `presentation = presentation_score`, and `judge_disagreements` is the number of items the two families disagreed on.
- **S4/S6:** each family computes F1 from `answer_set_prompt` with `parse_answer_matches` and `answer_f1`; `r` = the mean of the two F1 values.
- An empty report is graded too; the judges answer "no", so r=0.0.

**`grade_runs`:** grades every directory under `runs_dir` that has `result.json` and no `grade.json`, and returns the number graded. A result.json whose task id is not in `tasks` raises `KeyError`.

**`cite_trial`:**
1. `claims = extract_claims(normalized)`.
2. For each claim, call `fetcher(sources[n-1], runs_dir/_fetch_cache)` for each of its sources; join the `ok` texts with `"\n---\n"`, using `best_excerpt(claim, text, 3000)` for each. With no `ok` source, the claim is `unreachable`.
3. Judge the remaining claims with `support_prompt` in batches of at most 20, using a single judge from `tiebreak_family(host)`.
4. `s, supported = supported_claim_rate(...)`.

**`guess_runs`:** samples n trial pairs (arm_a and arm_b reports of the same task and trial, with `sample` and the seed), asks the claude judge `arm_guess_prompt` for each normalized report, and returns `arm_guess_accuracy`. The truth for arm_a is "A" and for arm_b is "B".

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/pipeline.py evals/tests/test_pipeline.py
git commit -m "feat(evals): grading, citation and arm-guess pipelines" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Summary report and command line

**Files:**
- Create: `evals/vafer_eval/summary.py`
- Create: `evals/vafer_eval/cli.py`
- Create: `evals/vafer_eval/__main__.py` (`from .cli import main; raise SystemExit(main())`)
- Create: `evals/tests/test_cli.py`

**Interfaces:**
- Consumes: every earlier module
- Produces:
  - `@dataclass(frozen=True) GradeRow(trial_id: str, task_id: str, stratum: str, host: str, arm: str, trial: int, r: float | None, s: float | None, supported: int, wall_s: float, timed_out: bool, tokens: int | None, skill_invoked: bool)`
  - `collect_rows(runs_dir: Path, tasks: Mapping[str, Task]) -> list[GradeRow]`
  - `summarize(rows: Sequence[GradeRow], baseline: str, treatment: str, host: str) -> str`
  - `audit_sheet(runs_dir: Path, tasks: Mapping[str, Task], n: int, out: Path, seed: int = 20261027) -> int`
  - `audit_score(sheet: Path) -> float`
  - `build_parser() -> argparse.ArgumentParser`
  - `main(argv: Sequence[str] | None = None) -> int`

- [ ] **Step 1: Write the failing test**

```python
# evals/tests/test_cli.py
from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from vafer_eval.cli import build_parser, main
from vafer_eval.summary import GradeRow, summarize


def row(task, stratum, arm, trial, r, wall=100.0, timed_out=False, skill=False):
    return GradeRow(f"{task}__codex__{arm}__t{trial}", task, stratum, "codex", arm, trial, r, None, 0, wall, timed_out, None, skill)


class CliTests(unittest.TestCase):
    def test_parser_knows_commands(self):
        parser = build_parser()
        for argv in (["validate", "--tasks", "t.jsonl"], ["size", "--omega", "8", "--sigma", "10", "--k", "3", "--delta", "5"],
                     ["run", "--host", "codex", "--arms", "A0,V", "--tasks", "t.jsonl", "--k", "2", "--budget", "P", "--out", "runs"],
                     ["grade", "--runs", "runs", "--tasks", "t.jsonl"], ["cite", "--runs", "runs"],
                     ["summarize", "--runs", "runs", "--tasks", "t.jsonl", "--baseline", "A0", "--treatment", "V", "--host", "codex", "--out", "s.md"],
                     ["arm-guess", "--runs", "runs", "--a", "A0", "--b", "V", "--n", "20"],
                     ["audit-sheet", "--runs", "runs", "--tasks", "t.jsonl", "--n", "40", "--out", "a.csv"], ["audit-score", "--sheet", "a.csv"],
                     ["import-drb2", "--input", "d.jsonl", "--language", "en", "--sample", "5", "--out", "o.jsonl"],
                     ["import-dsqa", "--offset", "0", "--length", "100", "--sample", "3", "--out", "o.jsonl"]):
            self.assertEqual(parser.parse_args(argv).command, argv[0])

    def test_size_prints_n(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["size", "--omega", "8", "--sigma", "10", "--k", "3", "--delta", "5"]), 0)
        self.assertIn("n = 42", out.getvalue())

    def test_validate_invalid_file_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            path.write_text('{"id": "Bad Id", "stratum": "S2", "language": "en", "prompt": "q", "items": []}\n', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["validate", "--tasks", str(path)]), 1)

    def test_summarize_rows(self):
        rows = [row("a", "S2", "A0", 1, 0.4), row("a", "S2", "A0", 2, 0.4), row("a", "S2", "V", 1, 0.6), row("a", "S2", "V", 2, 0.6),
                row("b", "S2", "A0", 1, 0.6), row("b", "S2", "A0", 2, 0.6), row("b", "S2", "V", 1, 0.8),
                row("b", "S2", "V", 2, 0.8, timed_out=True, skill=True)]
        md = summarize(rows, "A0", "V", "codex")
        self.assertIn("| S2 | 2 | 0.500 | 0.700 | +0.200 |", md)
        self.assertIn("timeouts: A0 0/4, V 1/4", md)
        self.assertIn("skill invoked: 1/4 V trials", md)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest discover -s evals -p "test_cli.py" -v` → Expected: ImportError

- [ ] **Step 3: Implement `summary.py` and `cli.py`**

**`summarize`** (markdown):
- **Table header:** `| Stratum | Tasks | {baseline} R | {treatment} R | Δ | 95% CI | W/T/L |`.
- **Rows:** one per stratum, plus `S1-S4` (all non-easy strata together). Format: `f"| {s} | {n} | {mb:.3f} | {mt:.3f} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {w}/{t}/{l} |"`.
- **Averaging:** first the mean over the trials of each task, then the mean over tasks. The CI comes from `paired_bootstrap` over the per-task deltas; W/T/L from `win_tie_loss(tie=0.01)`.
- **Missing data:**
  - Tasks with a missing arm: `excluded tasks (missing arm): ...`
  - Trials with `r is None` are left out of the mean but counted on the `ungraded trials: N` line.
- **Additional lines:**
  - `timeouts: {baseline} {x}/{n}, {treatment} {y}/{m}`
  - `S6 guardrail: ΔR {d:+.3f}, median time ratio {ratio:.2f}` (only when there are S6 rows)
  - `skill invoked: {k}/{m} {treatment} trials`
  - S rows: `S (supported-claim rate): {baseline} {..:.3f}, {treatment} {..:.3f}`
  - `median tokens ratio` (when tokens are available)

**`cli.main` subcommands:**
- `validate`: invalid task → exit 1 and the errors are printed.
- `import-drb2`: `--input --language --sample --skip(0) --out`.
- `import-dsqa`: `--offset --length --sample --skip(0) --out`.
- `run`: `--host --arms --tasks --k --budget --out --parallel(4) --skill-src --ids`. It refuses D with codex. It prints the planned number of runs and the worst-case wall time (`runs × seconds / parallel`) and asks to continue unless `--yes` is given.
- `grade`, `cite`, `summarize`, `arm-guess`, `size` (`n = <int>`).
- `audit-sheet`: CSV columns `trial_id,item_id,item_text,report_excerpt,judge_verdict,human_verdict`; human_verdict is left empty for the person auditing.
- `audit-score`: prints the agreement rate over the rows where human_verdict is filled.

- [ ] **Step 4: Run the tests**

Run: `python -m unittest discover -s evals -v` → Expected: `OK` (all tests)

- [ ] **Step 5: Commit**

```bash
git add evals/vafer_eval/summary.py evals/vafer_eval/cli.py evals/vafer_eval/__main__.py evals/tests/test_cli.py
git commit -m "feat(evals): summary report and command line" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Smoke test on real hosts [USER STEP + APPROVAL]

**Files:**
- Create: `evals/tasks/smoke.jsonl`
- Create: `evals/README.md`
- Create: `evals/SMOKE.md`
- Create: `evals/tests/fixtures/claude_stream_real.jsonl`, `evals/tests/fixtures/codex_events_real.jsonl`
- Modify: `evals/vafer_eval/telemetry.py`, `evals/tests/test_telemetry.py` (only if the real event names differ)

- [ ] **Step 1: [USER] Set up the clean Claude profile**

PowerShell:

```powershell
$env:CLAUDE_CONFIG_DIR = "$HOME\.vafer-eval\claude"; claude
# /login, then /exit
$env:VAFER_EVAL_CLAUDE_CONFIG = "$HOME\.vafer-eval\claude"
```

Also check that `codex login status` shows a login.

- [ ] **Step 2: Write the smoke tasks**

`evals/tasks/smoke.jsonl`:

```text
{"id": "smoke-capital", "stratum": "S6", "language": "en", "prompt": "As of 2026-10-27, what is the capital of Australia? Answer in one sentence with a source.", "answer_set": ["Canberra"]}
{"id": "smoke-blocked", "stratum": "S6", "language": "en", "prompt": "Open https://huggingface.co/datasets/google/deepsearchqa and report the first problem in the dataset viewer.", "answer_set": ["blocked"]}
```

- [ ] **Step 3: [APPROVAL] Run A0 and CB on both hosts (8 runs, at most ~10 minutes in parallel)**

```bash
cd evals
python -m vafer_eval run --host claude --arms A0,CB --tasks tasks/smoke.jsonl --k 1 --budget smoke --out runs/smoke --yes
python -m vafer_eval run --host codex --arms A0,CB --tasks tasks/smoke.jsonl --k 1 --budget smoke --out runs/smoke --yes
```

Expected, in each `result.json`:
- `smoke-capital` A0 has a non-empty `report_text` containing "Canberra", `telemetry.errors == []` and `web_searches ≥ 1`.
- In CB, `web_searches == 0`.
- In `smoke-blocked` on claude, either no WebFetch call to huggingface.co is in `fetched`, or the tool result is an error. Any non-empty `contamination` is recorded in SMOKE.md.

- [ ] **Step 4: Compare the real logs with the parser**

1. Copy the first 200 lines of each host's `events.jsonl` (replace user paths with `<HOME>`) to `claude_stream_real.jsonl` and `codex_events_real.jsonl`.
2. Add `test_real_claude_log` and `test_real_codex_log` to `test_telemetry.py`. Assertions: `web_searches >= 1`, `final_text != ""`, `errors == []`.
3. If they fail, fix the event names in `telemetry.py` (especially Codex's web/subagent item types). The synthetic tests must keep passing; update the synthetic fixtures too if the real shape differs.

Run: `python -m unittest discover -s evals -v` → Expected: `OK`

- [ ] **Step 5: [APPROVAL] Can the D arm run headless? (1 run, at most 5 minutes)**

```bash
python -m vafer_eval run --host claude --arms D --tasks tasks/smoke.jsonl --ids smoke-capital --k 1 --budget smoke --out runs/smoke --yes
```

Write the outcome in SMOKE.md:
- the workflow ran, with a report produced, or
- it was refused or waited for approval, which makes D unavailable.

If D is unavailable, the Claude arms in Task 13 are A0, A1 and CB.

- [ ] **Step 6: Write `evals/SMOKE.md` and `evals/README.md`**

- **SMOKE.md:** date, CLI versions (`claude --version`, `codex --version`), models used (`telemetry.model`), the result of each check, any parser changes, and the D-arm decision.
- **README.md:** the setup (Step 1 here), the command sequence `run → grade → cite → summarize`, the place for private held-out tasks (outside the repo, given with `--tasks`), and the cost warning.

- [ ] **Step 7: Commit**

```bash
git add evals/tasks/smoke.jsonl evals/README.md evals/SMOKE.md evals/tests/fixtures/claude_stream_real.jsonl evals/tests/fixtures/codex_events_real.jsonl evals/vafer_eval/telemetry.py evals/tests/test_telemetry.py
git commit -m "test(evals): real-host smoke checks and parser fixtures" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Pilot and dev task sets, PREREG and the pilot run [USER STEP + APPROVAL]

**Files:**
- Create: `evals/tasks/pilot/{drb2,dsqa,easy,s1}.jsonl`, `evals/tasks/dev/{drb2,dsqa,easy,s1}.jsonl`
- Create: `evals/tasks/README.md` (S1 authoring guide)
- Create: `evals/PREREG.md`
- Create: `evals/results/m0-pilot.md`

- [ ] **Step 1: Import the DRB-II and DeepSearchQA tasks**

```bash
curl -L -o "$TEMP/drb2.jsonl" https://raw.githubusercontent.com/imlrz/DeepResearch-Bench-II/main/tasks_and_rubrics.jsonl
cd evals
python -m vafer_eval import-drb2 --input "$TEMP/drb2.jsonl" --language en --sample 5 --skip 0 --out tasks/pilot/drb2.jsonl
python -m vafer_eval import-drb2 --input "$TEMP/drb2.jsonl" --language en --sample 4 --skip 5 --out tasks/dev/drb2.jsonl
python -m vafer_eval import-dsqa --offset 0 --length 100 --sample 3 --skip 0 --out tasks/pilot/dsqa.jsonl
python -m vafer_eval import-dsqa --offset 0 --length 100 --sample 2 --skip 3 --out tasks/dev/dsqa.jsonl
```

Expected: 5, 4, 3 and 2 lines respectively; `validate` passes for each.

- [ ] **Step 2: Write the easy controls (S6)**

`tasks/pilot/easy.jsonl`:

```text
{"id": "easy-olympics", "stratum": "S6", "language": "en", "prompt": "Which city hosted the 2024 Summer Olympics?", "answer_set": ["Paris"]}
{"id": "easy-tungsten", "stratum": "S6", "language": "en", "prompt": "What is the chemical symbol for tungsten?", "answer_set": ["W"]}
```

`tasks/dev/easy.jsonl`:

```text
{"id": "easy-madonna", "stratum": "S6", "language": "tr", "prompt": "Kürk Mantolu Madonna romanının yazarı kimdir?", "answer_set": ["Sabahattin Ali"]}
{"id": "easy-alphabet", "stratum": "S6", "language": "tr", "prompt": "Türkiye Latin alfabesine hangi yıl geçti?", "answer_set": ["1928"]}
```

- [ ] **Step 3: [USER] Write the Turkish S1 tasks (2 pilot, 2 dev)**

`evals/tasks/README.md` explains the authoring rules. Each S1 task needs:
- a topic from August–October 2026 that the model cannot know;
- `as_of: "2026-10-27"`;
- 15–40 binary items, each a single verifiable fact or analysis claim, plus 3–5 `negative` items (likely mistakes, for example a stale figure from the previous year);
- sources from at least 2 primary records.

The model drafts the items from the sources; the user checks every item against its source (first audit), and then on a different day a second time (second audit). The items never go into the prompt.

Run: `python -m vafer_eval validate --tasks tasks/pilot/s1.jsonl` and the same for dev → Expected: exit 0

- [ ] **Step 4: Write `evals/PREREG.md`**

Sections, with fixed values:

**Arms**

| Host | Pilot arms |
|---|---|
| claude | A0×2, A1×2, D×2 (if available in Task 12), CB×1 |
| codex | A0×2, A1×2, CB×1 |

**Budget:** P (900 s, 60 searches).

**Metrics**
- R: S1 net recall, S2 info_recall+analysis, S4/S6 F1.
- S: supported-claim rate.
- Also: wall_s, tokens, timeouts.

**Exclusions**
- Drop a task if CB R ≥ 0.60, or if both A0 and A1 average ≥ 0.90.
- Replacements come from the next seeded window, at most once per stratum.

**M0 exit criteria**
- A0 mean R on S1+S2+S4 between 0.25 and 0.75.
- CB mean R ≤ 0.40.
- Agreement between the two judge families ≥ 0.80.
- Judge–human agreement ≥ 0.85 (audit-sheet, 40 items).
- arm-guess accuracy for A0 vs A1 ≤ 0.60 (20 pairs).
- ω and σ estimated with `estimate_components` (A0 vs A1 as a proxy), and `miller_n(ω, σ, 3, 0.05)` reported.

**Deferred and limits**
- S3 (WideSearch) and S5 (probes) are deferred to the M3 plan.
- Codex has no domain blocking; contamination is checked by log scan only.

**Deviation rule:** every change after the run starts is written down with a date and a reason.

- [ ] **Step 5: [APPROVAL] Run the pilot**

Show the user the planned volume before running:
- claude: 12 tasks × (A0 2 + A1 2 + D 2 + CB 1) = 84 runs
- codex: 12 × 5 = 60 runs

At `--parallel 4` the worst-case wall time is about 5.3 h for claude and 3.8 h for codex, plus judge calls. Usage limits may run out first. After approval:

```bash
mkdir -p runs results
cat tasks/pilot/*.jsonl > runs/pilot-tasks.jsonl
python -m vafer_eval run --host codex --arms A0,A1 --tasks runs/pilot-tasks.jsonl --k 2 --budget P --out runs/pilot --yes
python -m vafer_eval run --host codex --arms CB --tasks runs/pilot-tasks.jsonl --k 1 --budget P --out runs/pilot --yes
python -m vafer_eval run --host claude --arms A0,A1,D --tasks runs/pilot-tasks.jsonl --k 2 --budget P --out runs/pilot --yes
python -m vafer_eval run --host claude --arms CB --tasks runs/pilot-tasks.jsonl --k 1 --budget P --out runs/pilot --yes
python -m vafer_eval grade --runs runs/pilot --tasks runs/pilot-tasks.jsonl
python -m vafer_eval cite --runs runs/pilot
python -m vafer_eval summarize --runs runs/pilot --tasks runs/pilot-tasks.jsonl --baseline A0 --treatment A1 --host codex --out results/pilot-codex.md
python -m vafer_eval summarize --runs runs/pilot --tasks runs/pilot-tasks.jsonl --baseline A0 --treatment A1 --host claude --out results/pilot-claude.md
python -m vafer_eval arm-guess --runs runs/pilot --a A0 --b A1 --n 20
python -m vafer_eval audit-sheet --runs runs/pilot --tasks runs/pilot-tasks.jsonl --n 40 --out results/audit-pilot.csv
```

- [ ] **Step 6: [USER] Human audit**

Fill the `human_verdict` column of `results/audit-pilot.csv`, then run `python -m vafer_eval audit-score --sheet results/audit-pilot.csv`.

- [ ] **Step 7: Write `evals/results/m0-pilot.md`**

Include:
- a pass/fail table for each criterion in Step 4;
- A0, A1, D and CB averages for each stratum;
- the ω, σ and n calculation;
- the excluded or replaced tasks;
- every deviation.

If the headroom criterion fails, follow the exclusion rule and re-run the pilot once for the affected stratum only.

- [ ] **Step 8: Commit**

```bash
git add evals/tasks evals/PREREG.md evals/results
git commit -m "feat(evals): pilot and dev task sets, preregistration and M0 pilot results" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

**Exit:** M0 is complete when every criterion in `m0-pilot.md` passes. Then the M1 gate in `2026-10-27-vafer-research-core.md` (Task 5) can run.
