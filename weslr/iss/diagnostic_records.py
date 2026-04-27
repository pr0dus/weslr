import time
import json
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
RECORD_FILE = _BASE_DIR / "iss_diagnostic_records.jsonl"

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


def _validate_iss_diagnostic_record(record: dict):
    allowed_types = ("iss_probe_result", "iss_gap_signal")
    rec_type = record.get("type")
    if rec_type not in allowed_types:
        raise ValueError(f"record type must be one of {allowed_types}, got {rec_type!r}")
    if "timestamp" not in record:
        raise ValueError("timestamp is required")
    if rec_type == "iss_probe_result":
        if not isinstance(record.get("probe_id"), str) or not record["probe_id"].strip():
            raise ValueError("probe_id must be a non-empty string")
        if not isinstance(record.get("target"), str) or not record["target"].strip():
            raise ValueError("target must be a non-empty string")
        if record.get("status") not in _ALLOWED_PROBE_STATUS:
            raise ValueError(f"status must be one of {', '.join(sorted(_ALLOWED_PROBE_STATUS))}")
        if not isinstance(record.get("evidence"), dict):
            raise ValueError("evidence must be a dict")
    elif rec_type == "iss_gap_signal":
        if not isinstance(record.get("gap_id"), str) or not record["gap_id"].strip():
            raise ValueError("gap_id must be a non-empty string")
        if not isinstance(record.get("source_probe_id"), str) or not record["source_probe_id"].strip():
            raise ValueError("source_probe_id must be a non-empty string")
        if not isinstance(record.get("summary"), str) or not record["summary"].strip():
            raise ValueError("summary must be a non-empty string")
        if record.get("severity") not in _ALLOWED_GAP_SEVERITY:
            raise ValueError(f"severity must be one of {', '.join(sorted(_ALLOWED_GAP_SEVERITY))}")
        if not isinstance(record.get("evidence"), dict):
            raise ValueError("evidence must be a dict")


def record_iss_diagnostic(record: dict) -> None:
    """
    Append an ISS diagnostic record (probe result or gap signal) to JSONL.

    Only accepts types: iss_probe_result, iss_gap_signal
    Append-only — no mutation of existing records.
    """
    _validate_iss_diagnostic_record(record)
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
    records = []
    for l in all_lines[-limit:]:
        try:
            records.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    return records
