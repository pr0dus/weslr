import json
import time
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
TRACE_FILE = _BASE_DIR / "proposal_trace.jsonl"


def _write_event(event: dict):
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def record_proposal(proposal_id: str, content: dict):
    _write_event({
        "type": "proposal_created",
        "proposal_id": proposal_id,
        "content": content,
        "timestamp": time.time(),
    })


def record_decision(proposal_id: str, decision: str):
    _write_event({
        "type": "proposal_decision",
        "proposal_id": proposal_id,
        "decision": decision,
        "timestamp": time.time(),
    })


def load_trace(limit: int = 50):
    if not TRACE_FILE.exists():
        return []

    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]

    return [json.loads(l) for l in lines]
