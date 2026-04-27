import json
import time
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
TRACE_FILE = _BASE_DIR / "proposal_trace.jsonl"

_KNOWN_TRACE_TYPES = frozenset({"proposal_created", "proposal_decision"})


def _write_event(event: dict):
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _validate_proposal_created(proposal_id: str, content: dict):
    if not isinstance(proposal_id, str) or not proposal_id.strip():
        raise ValueError(f"proposal_id must be a non-empty string, got {proposal_id!r}")
    if not isinstance(content, dict):
        raise ValueError(f"content must be a dict, got {type(content).__name__}")


def _validate_proposal_decision(proposal_id: str, decision: str):
    if not isinstance(proposal_id, str) or not proposal_id.strip():
        raise ValueError(f"proposal_id must be a non-empty string, got {proposal_id!r}")
    if not isinstance(decision, str) or not decision.strip():
        raise ValueError(f"decision must be a non-empty string, got {decision!r}")


def record_proposal(proposal_id: str, content: dict):
    _validate_proposal_created(proposal_id, content)
    _write_event({
        "type": "proposal_created",
        "proposal_id": proposal_id,
        "content": content,
        "timestamp": time.time(),
    })


def record_decision(proposal_id: str, decision: str):
    _validate_proposal_decision(proposal_id, decision)
    _write_event({
        "type": "proposal_decision",
        "proposal_id": proposal_id,
        "decision": decision,
        "timestamp": time.time(),
    })


def _validate_trace_record_read(record: dict) -> bool:
    """
    Lightweight read-side validation for trace records.
    Returns True if structurally valid, False otherwise.
    Silently skips invalid records — does not raise.
    """
    if not isinstance(record, dict):
        return False
    if record.get("type") not in _KNOWN_TRACE_TYPES:
        return False
    if not isinstance(record.get("proposal_id"), str) or not record["proposal_id"].strip():
        return False
    if "timestamp" not in record:
        return False
    return True


def load_trace(limit: int = 50):
    if not TRACE_FILE.exists():
        return []
    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]
    records = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not _validate_trace_record_read(record):
            continue
        records.append(record)
    return records


def proposal_exists(proposal_id: str, source_gap_id: str) -> bool:
    """Check if a proposal with the given ID and source gap already exists."""
    records = load_trace(200)
    for r in records:
        if r.get("type") == "proposal_created":
            if r.get("proposal_id") == proposal_id:
                if r.get("content", {}).get("source_gap_id") == source_gap_id:
                    return True
    return False
