import time
import json
from pathlib import Path

RECORD_FILE = Path("weslr/iss/iss_diagnostic_records.jsonl")

_ALLOWED_PROBE_STATUS = frozenset({"ok", "degraded", "missing", "unknown"})
_ALLOWED_GAP_SEVERITY = frozenset({"low", "medium", "high"})


def make_probe_result(
    probe_id: str,
    target: str,
    status: str,
    evidence: dict | None = None,
    confidence: str = "medium",
) -> dict:
    """
    Build a probe result record.

    status must be one of: ok, degraded, missing, unknown
    Raises ValueError if status is not allowed.
    """
    if status not in _ALLOWED_PROBE_STATUS:
        raise ValueError(
            f"Invalid probe status '{status}'. "
            f"Must be one of: {', '.join(sorted(_ALLOWED_PROBE_STATUS))}"
        )
    return {
        "type": "iss_probe_result",
        "probe_id": probe_id,
        "target": target,
        "status": status,
        "evidence": evidence or {},
        "confidence": confidence,
        "timestamp": time.time(),
    }


def make_gap_signal(
    gap_id: str,
    source_probe_id: str,
    summary: str,
    severity: str = "medium",
    evidence: dict | None = None,
    confidence: str = "medium",
) -> dict:
    """
    Build a gap signal record.

    severity must be one of: low, medium, high
    Raises ValueError if severity is not allowed.
    """
    if severity not in _ALLOWED_GAP_SEVERITY:
        raise ValueError(
            f"Invalid gap severity '{severity}'. "
            f"Must be one of: {', '.join(sorted(_ALLOWED_GAP_SEVERITY))}"
        )
    return {
        "type": "iss_gap_signal",
        "gap_id": gap_id,
        "source_probe_id": source_probe_id,
        "summary": summary,
        "severity": severity,
        "evidence": evidence or {},
        "confidence": confidence,
        "timestamp": time.time(),
    }


def record_iss_diagnostic(record: dict) -> None:
    """
    Append an ISS diagnostic record (probe result or gap signal) to JSONL.

    Only accepts types: iss_probe_result, iss_gap_signal
    Append-only — no mutation of existing records.
    """
    _allowed_types = ("iss_probe_result", "iss_gap_signal")
    if record.get("type") not in _allowed_types:
        raise ValueError(
            f"record type must be one of {_allowed_types}, "
            f"got: {record.get('type')!r}"
        )
    RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RECORD_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_iss_diagnostics(limit: int = 50) -> list[dict]:
    """
    Load the last `limit` ISS diagnostic records.
    Returns an empty list if the file does not exist.
    """
    if not RECORD_FILE.exists():
        return []
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    return [json.loads(l) for l in all_lines[-limit:]]