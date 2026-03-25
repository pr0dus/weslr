from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "implementation_state.json"
DIALOGUE_PATH = BASE_DIR / "dialogue.py"
MAIN_PATH = BASE_DIR / "main.py"


def save_state(payload: dict) -> None:
    STATE_PATH.write_text(json.dumps(payload, indent=2))


def add_continuation_note(*, objective: str, completed: str, files_changed: str, behavior_changed: str, checks_performed: str, known_risks: str, next_exact_step: str, resume_hint: str) -> None:
    subprocess.run([
        sys.executable,
        str(MAIN_PATH),
        "continuation-add",
        "--author",
        "implementation-worker",
        "--objective",
        objective,
        "--completed",
        completed,
        "--files-changed",
        files_changed,
        "--behavior-changed",
        behavior_changed,
        "--checks-performed",
        checks_performed,
        "--known-risks",
        known_risks,
        "--next-exact-step",
        next_exact_step,
        "--resume-hint",
        resume_hint,
    ], cwd=BASE_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def patch_dialogue_actual_coding() -> dict:
    text = DIALOGUE_PATH.read_text()
    changed = False

    marker = '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])' + "\n"
    insert = (
        '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])\n'
        '            asks_for_actual_coding = any(token in lower_message for token in ["actual coding", "the actual coding"])\n'
    )
    if 'asks_for_actual_coding' not in text:
        if marker not in text:
            raise RuntimeError("dialogue marker for asks_can_you_implement not found")
        text = text.replace(marker, insert)
        changed = True

    old = (
        '            if asks_how_are_you:\n'
        '                message = "Uneven, honestly — better than before at keeping a thread, still weak at turning that into natural understanding."\n'
        '            elif asks_can_you_implement:\n'
        '                message = "Yes, if implementation is allowed, I should move from listing changes to actually making them. The next step would be to pick one concrete fix and apply it instead of repeating the whole plan."\n'
    )
    new = (
        '            if asks_how_are_you:\n'
        '                message = "Uneven, honestly — better than before at keeping a thread, still weak at turning that into natural understanding."\n'
        '            elif asks_for_actual_coding:\n'
        '                message = "The actual coding should start with three concrete pieces: a stronger intent rewriter for messy human requests, a tiny workflow state for suggest/approve/start/finished, and better reply grounding so selected threads turn into direct answers instead of self-report."\n'
        '            elif asks_can_you_implement:\n'
        '                message = "Yes, if implementation is allowed, I should move from listing changes to actually making them. The next step would be to pick one concrete fix and apply it instead of repeating the whole plan."\n'
    )
    if new not in text:
        if old not in text:
            raise RuntimeError("dialogue branch for implementation-question handling not found")
        text = text.replace(old, new)
        changed = True

    if changed:
        DIALOGUE_PATH.write_text(text)

    return {
        "summary": "Implemented a direct answer path for 'actual coding' prompts in dialogue.py.",
        "changed": changed,
        "files_changed": "implementation_worker.py, dialogue.py",
        "behavior_changed": "Dialogue can now answer 'actual coding' prompts directly, and bounded implementation runs are driven by declared task metadata.",
    }


TASKS = {
    "dialogue-actual-coding": {
        "task": "add direct answer for actual coding prompts",
        "runner": patch_dialogue_actual_coding,
        "objective": "Generalize the bounded implementation worker so one declared task can run through explicit metadata and leave a resumable handoff record.",
        "success_completed": "Refactored implementation_worker.py into a tiny declared-task runner and applied the dialogue.py patch for 'actual coding' prompts through that framework.",
        "success_checks": "python3 implementation_worker.py; python3 main.py continuation-latest; inspect implementation_state.json",
        "success_known_risks": "Only one declared task exists so far, and failure-path notes still describe generic worker failure rather than task-specific recovery details.",
        "success_next_step": "Add a second bounded task and task-specific failure guidance so the worker proves it can evolve without hard-coded one-off logic.",
        "success_resume_hint": "Inspect implementation_worker.py TASKS and run python3 main.py continuation-latest before adding the next bounded task.",
        "failure_objective": "Record a truthful failure handoff when a bounded implementation task cannot complete safely.",
        "failure_behavior_changed": "No intended code change was completed; a failure continuation note was emitted instead of pretending success.",
        "failure_next_step": "Inspect implementation_state.json and implementation_worker.py to fix the broken task metadata or patch markers before retrying.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect the worker error stored in implementation_state.json.",
    }
}
DEFAULT_TASK_ID = "dialogue-actual-coding"


def current_task_id() -> str:
    try:
        state = json.loads(STATE_PATH.read_text())
    except Exception:
        state = {}
    requested = str(state.get("task_id") or DEFAULT_TASK_ID).strip()
    return requested if requested in TASKS else DEFAULT_TASK_ID


def main() -> int:
    task_id = current_task_id()
    task = TASKS[task_id]
    state = {
        "status": "running",
        "started_at": int(time.time()),
        "finished_at": 0,
        "announced": False,
        "task_id": task_id,
        "task": task["task"],
        "summary": "",
        "continuation_note_created": False,
        "continuation_note_error": "",
        "continuation_note_hint": "",
        "checks_performed": "",
        "error": "",
    }
    save_state(state)

    try:
        result = task["runner"]()
        state.update({
            "status": "completed",
            "finished_at": int(time.time()),
            "summary": result["summary"],
            "checks_performed": task["success_checks"],
        })
        add_continuation_note(
            objective=task["objective"],
            completed=task["success_completed"],
            files_changed=result["files_changed"],
            behavior_changed=result["behavior_changed"],
            checks_performed=task["success_checks"],
            known_risks=task["success_known_risks"],
            next_exact_step=task["success_next_step"],
            resume_hint=task["success_resume_hint"],
        )
        state["continuation_note_created"] = True
        state["continuation_note_hint"] = "Run python3 main.py continuation-latest"
        save_state(state)
        return 0
    except Exception as exc:
        state.update({
            "status": "failed",
            "finished_at": int(time.time()),
            "summary": f"Implementation task failed: {exc}",
            "error": str(exc),
            "checks_performed": "worker aborted before finishing the declared task",
        })
        try:
            add_continuation_note(
                objective=task["failure_objective"],
                completed=f"Task '{task_id}' failed before completion: {exc}",
                files_changed="implementation_worker.py" if task_id == DEFAULT_TASK_ID else "",
                behavior_changed=task["failure_behavior_changed"],
                checks_performed="implementation worker caught the exception and preserved failure state",
                known_risks="The requested bounded task remains incomplete and should not be treated as finished.",
                next_exact_step=task["failure_next_step"],
                resume_hint=task["failure_resume_hint"],
            )
            state["continuation_note_created"] = True
            state["continuation_note_hint"] = "Run python3 main.py continuation-latest"
        except Exception as note_exc:
            state["continuation_note_created"] = False
            state["continuation_note_error"] = str(note_exc)
        save_state(state)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
