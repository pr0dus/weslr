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


def main() -> int:
    state = {
        "status": "running",
        "started_at": int(time.time()),
        "finished_at": 0,
        "announced": False,
        "task": "add direct answer for actual coding prompts",
        "summary": "",
        "continuation_note_created": False,
        "continuation_note_error": "",
        "continuation_note_hint": "",
    }
    save_state(state)

    text = DIALOGUE_PATH.read_text()
    marker = '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])\n'
    insert = (
        '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])\n'
        '            asks_for_actual_coding = any(token in lower_message for token in ["actual coding", "the actual coding"])\n'
    )
    if 'asks_for_actual_coding' not in text:
        text = text.replace(marker, insert)

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
        text = text.replace(old, new)

    DIALOGUE_PATH.write_text(text)
    state.update({
        "status": "completed",
        "finished_at": int(time.time()),
        "summary": "Implemented a direct answer path for 'actual coding' prompts in dialogue.py.",
    })
    try:
        add_continuation_note(
            objective="Leave an automatic resumable handoff record after a bounded implementation-worker change.",
            completed="Updated dialogue.py to answer 'actual coding' prompts directly and recorded the result automatically from implementation_worker.py.",
            files_changed="implementation_worker.py, dialogue.py",
            behavior_changed="Bounded implementation runs now create a structured continuation note automatically when they complete successfully.",
            checks_performed="Implementation worker finished and invoked main.py continuation-add.",
            known_risks="This worker currently records a success-path note only for this specific bounded task; failure-path note emission is not implemented yet.",
            next_exact_step="Generalize the implementation worker so task metadata declares its own continuation-note payload and can emit failure notes too.",
            resume_hint="Run python3 CircleForge/main.py continuation-latest and inspect implementation_state.json for the most recent worker outcome.",
        )
        state["continuation_note_created"] = True
        state["continuation_note_hint"] = "Run python3 main.py continuation-latest"
    except Exception as exc:
        state["continuation_note_created"] = False
        state["continuation_note_error"] = str(exc)
    save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
