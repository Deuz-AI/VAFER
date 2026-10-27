"""Read-only next actions derived from declared requirements, not completed notes."""

from __future__ import annotations


def agenda(manifest: dict, invalidated_tasks=(), invalidated_coverage=(), question_progress=()) -> dict:
    tasks = {task["id"]: task for task in manifest["tasks"]}
    invalid_tasks, invalid_coverage = set(invalidated_tasks), set(invalidated_coverage)
    actionable, blocked, linked = [], [], set()
    progress = {row["id"]: row for row in question_progress}
    blocked_tasks = {}
    for kind, rows in (("gap", manifest["gaps"]), ("coverage", manifest["coverage"])):
        for row in rows:
            unresolved = not row["resolved"] if kind == "gap" else (
                row["status"] not in {"covered", "excluded"} or row["id"] in invalid_coverage)
            reason = row.get("blocked_reason") or (
                "Record the access or resource condition needed to continue."
                if kind == "coverage" and row["status"] == "blocked" else None)
            if unresolved and reason:
                for tid in row.get("task_ids", []):
                    blocked_tasks.setdefault(tid, []).append(reason)
    for kind, rows in (("gap", manifest["gaps"]), ("coverage", manifest["coverage"])):
        for row in rows:
            if kind == "gap":
                if row["resolved"]:
                    continue
                priority = 0 if row["blocking"] else 3
                question = row["description"]
            else:
                if row["status"] == "excluded" or (row["status"] == "covered" and row["id"] not in invalid_coverage):
                    continue
                priority = 1 if row["required"] else 3
                question = row["question"]
            task_ids = row.get("task_ids", [])
            linked.update(task_ids)
            unfinished = [tid for tid in task_ids if tid in tasks and
                          (tasks[tid]["status"] != "done" or tid in invalid_tasks)]
            pending = [tid for tid in unfinished if tid not in blocked_tasks]
            action = row.get("next_action") or "; ".join(tasks[tid]["title"] for tid in pending)
            if not action and kind == "coverage" and row["id"] in progress:
                state = progress[row["id"]]
                if state.get("unanswered_children"):
                    action = "Answer the unresolved subquestions: " + ", ".join(state["unanswered_children"])
                elif not state["evidence_found"]:
                    action = "Find current evidence for: " + question
                elif not state["context_read"]:
                    action = "Read enough surrounding source context to evaluate: " + question
                elif not state["answer_supported"]:
                    action = "Explain the answer and assess source support, scope and alternatives: " + question
                elif not state["reported"]:
                    action = "Carry the supported answer into the report and record its exact anchor: " + question
            item = {"kind": kind, "id": row["id"], "question": question,
                    "priority": priority, "task_ids": pending,
                    "action": action or "Plan the next investigation: " + question,
                    "needs_planning": not bool(action)}
            if kind == "gap":
                item["coverage_ids"] = row.get("coverage_ids", [])
            if any(tid in blocked_tasks for tid in unfinished):
                item["blocked_task_ids"] = [tid for tid in unfinished if tid in blocked_tasks]
            reason = row.get("blocked_reason")
            if not reason and unfinished and not pending:
                reason = "; ".join(sorted({reason for tid in unfinished for reason in blocked_tasks[tid]}))
            if reason or (kind == "coverage" and row["status"] == "blocked"):
                item["blocked_reason"] = reason or "Record the access or resource condition needed to continue."
                item["task_ids"] = unfinished
                blocked.append(item)
            else:
                actionable.append(item)
    for tid, task in tasks.items():
        if tid not in linked and (task["status"] != "done" or tid in invalid_tasks):
            actionable.append({"kind": "task", "id": tid, "priority": 2,
                               "action": task["title"], "task_ids": [tid], "needs_planning": False})
    order = lambda item: (item["priority"], item["kind"], item["id"])
    return {"next_actions": sorted(actionable, key=order), "blocked_actions": sorted(blocked, key=order)}
