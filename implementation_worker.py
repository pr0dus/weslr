from __future__ import annotations

import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "implementation_state.json"
DIALOGUE_PATH = BASE_DIR / "dialogue.py"


def save_state(payload: dict) -> None:
    STATE_PATH.write_text(json.dumps(payload, indent=2))


def main() -> int:
    state = {
        "status": "running",
        "started_at": int(time.time()),
        "finished_at": 0,
        "announced": False,
        "task": "add direct answer for actual coding prompts",
        "summary": "",
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
    save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
