"""
WESLR Artificial Analysis Index V1 — Pass 1

Read-only attention analysis of Pass 1 signal sources.
Builds structured operator attention summary from:
  - weslr/public_signals.jsonl
  - weslr/contract_observations.jsonl
  - weslr/contract_insufficiency_log.jsonl
  - weslr/contract_proposal_review_log.jsonl

Rules:
- AAI ranks attention. It does not decide truth.
- operator approval always required for any state change
- automatic_change is always false
- Never writes to any JSONL or production file
- Malformed lines are skipped silently
- Missing files return empty/safe summaries
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Storage paths
# ---------------------------------------------------------------------------

_PUBLIC_SIGNALS_PATH = "weslr/public_signals.jsonl"
_CONTRACT_OBSERVATIONS_PATH = "weslr/contract_observations.jsonl"
_CONTRACT_INSUFFICIENCY_LOG_PATH = "weslr/contract_insufficiency_log.jsonl"
_CONTRACT_PROPOSAL_REVIEW_LOG_PATH = "weslr/contract_proposal_review_log.jsonl"


# ---------------------------------------------------------------------------
# Attention levels
# ---------------------------------------------------------------------------

_LEVEL_LABELS = {
    0: "suppress",
    1: "track",
    2: "summary",
    3: "ask",
    4: "interrupt",
}

_AUTOMATIC_CHANGE = False
_AUTHORITY = "attention_only"


# ---------------------------------------------------------------------------
# Level 0 — suppress/noise
# ---------------------------------------------------------------------------

def _classify_observation(record: dict) -> dict:
    """
    Individual contract_observation records are level 0 (suppress).
    These are operational noise — 31 records as of Pass 1 inspection.
    Only escalate if a record contains evidence of privacy/truth/governance issue.
    """
    # Check for forbidden field presence (would indicate data leak)
    forbidden_in_record = any(
        k in ("raw_prompt", "prompt", "message", "user_input", "email",
              "phone", "ip", "address", "name", "location")
        for k in record.keys()
    )
    # Check safety flags
    raw_prompt_stored = record.get("raw_prompt_stored") is True
    pii_stored = record.get("pii_stored") is True
    behavior_change = record.get("behavior_change_allowed") is True

    if forbidden_in_record or raw_prompt_stored or pii_stored or behavior_change:
        # Something is wrong — escalate to level 3
        return {
            "attention_level": 3,
            "classification": "ask",
            "reason": "contract_observation_record_has_safety_violation",
            "source": "contract_observation",
            "record_id": record.get("timestamp", "unknown"),
            "requires_operator_action": True,
            "authority": _AUTHORITY,
        }

    return {
        "attention_level": 0,
        "classification": "suppress",
        "reason": "individual_observation_record_noise",
        "source": "contract_observation",
        "record_id": record.get("timestamp", "unknown"),
        "requires_operator_action": False,
        "authority": _AUTHORITY,
    }


# ---------------------------------------------------------------------------
# Level 1 — track silently
# ---------------------------------------------------------------------------

def _classify_public_signal(record: dict) -> dict:
    """
    Public signal records are level 1 (track) — operational metrics.
    Volume is normal. Suppress unless anomalous spike or privacy issue.
    """
    return {
        "attention_level": 1,
        "classification": "track",
        "reason": "public_signal_operational_metric",
        "source": "public_signal",
        "record_id": record.get("session_id_hash", "unknown"),
        "requires_operator_action": False,
        "authority": _AUTHORITY,
    }


# ---------------------------------------------------------------------------
# Level 2 — periodic summary
# ---------------------------------------------------------------------------

def _classify_insufficiency_record(record: dict) -> dict:
    """
    Contract insufficiency records with proposal_ready=True
    belong in periodic summary (level 2).
    """
    proposal_ready = record.get("proposal_ready") is True
    pattern_type = record.get("pattern_type", "unknown")
    contract = record.get("contract", "unknown")
    occurrence_count = record.get("occurrence_count", 0)

    if proposal_ready:
        return {
            "attention_level": 2,
            "classification": "summary",
            "reason": f"insufficiency_proposal_ready_pattern_{pattern_type}_contract_{contract}",
            "source": "contract_insufficiency",
            "record_id": record.get("detected_at", "unknown"),
            "requires_operator_action": False,
            "authority": _AUTHORITY,
            "pattern_type": pattern_type,
            "contract": contract,
            "occurrence_count": occurrence_count,
        }
    else:
        return {
            "attention_level": 1,
            "classification": "track",
            "reason": "insufficiency_not_yet_proposal_ready",
            "source": "contract_insufficiency",
            "record_id": record.get("detected_at", "unknown"),
            "requires_operator_action": False,
            "authority": _AUTHORITY,
        }


# ---------------------------------------------------------------------------
# Level 3 — ask operator
# ---------------------------------------------------------------------------

def _classify_proposal_review_record(record: dict) -> dict:
    """
    Pending contract proposal review records are level 3 (ask operator).
    Proposals require operator review — not automatic, not urgent.
    """
    proposal_id = record.get("proposal_id", "unknown")
    pattern_type = record.get("pattern_type", "unknown")
    contract = record.get("contract", "unknown")

    return {
        "attention_level": 3,
        "classification": "ask",
        "reason": f"pending_review_proposal_{proposal_id}_pattern_{pattern_type}",
        "source": "contract_proposal_review",
        "record_id": proposal_id,
        "requires_operator_action": True,
        "authority": _AUTHORITY,
        "pattern_type": pattern_type,
        "contract": contract,
    }


# ---------------------------------------------------------------------------
# Level 4 — urgent interruption (critical breach only)
# ---------------------------------------------------------------------------

def _classify_critical_breach(record: dict) -> dict:
    """
    Critical breach: PII stored, truth authority compromised,
    governance violation, or forbidden content in a record.
    """
    return {
        "attention_level": 4,
        "classification": "interrupt",
        "reason": "critical_privacy_truth_or_governance_breach",
        "source": "critical",
        "record_id": "breach_detected",
        "requires_operator_action": True,
        "authority": _AUTHORITY,
    }


# ---------------------------------------------------------------------------
# classify_attention_item
# ---------------------------------------------------------------------------

def classify_attention_item(record: dict) -> dict:
    """
    Classify a single record into AAI attention levels.

    INPUT:
        record — dict with at minimum a "record_type" field

    RETURN:
        dict with:
            attention_level: 0|1|2|3|4
            classification: "suppress"|"track"|"summary"|"ask"|"interrupt"
            reason: str
            source: str
            record_id: str
            requires_operator_action: bool
            authority: "attention_only"
    """
    if not isinstance(record, dict):
        return {
            "attention_level": 0,
            "classification": "suppress",
            "reason": "malformed_record",
            "source": "unknown",
            "record_id": "unknown",
            "requires_operator_action": False,
            "authority": _AUTHORITY,
        }

    record_type = record.get("record_type", "unknown")

    if record_type == "contract_observation_v1":
        return _classify_observation(record)

    if record_type == "public_signal_v1":
        return _classify_public_signal(record)

    if record_type == "contract_insufficiency_v1":
        return _classify_insufficiency_record(record)

    if record_type == "contract_proposal_review_v1":
        return _classify_proposal_review_record(record)

    # Unknown type — suppress
    return {
        "attention_level": 1,
        "classification": "track",
        "reason": f"unknown_record_type_{record_type}",
        "source": "unknown",
        "record_id": "unknown",
        "requires_operator_action": False,
        "authority": _AUTHORITY,
    }


# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------

def _read_jsonl(path: str, limit: int = 1000) -> list[dict]:
    """Read last N lines from a JSONL file. Skip malformed lines."""
    p = pathlib.Path(path)
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []
    records = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if isinstance(rec, dict):
                records.append(rec)
        except json.JSONDecodeError:
            continue
    return records


# ---------------------------------------------------------------------------
# build_attention_summary
# ---------------------------------------------------------------------------

def build_attention_summary(
    public_signals_path: str = _PUBLIC_SIGNALS_PATH,
    contract_observations_path: str = _CONTRACT_OBSERVATIONS_PATH,
    insufficiency_log_path: str = _CONTRACT_INSUFFICIENCY_LOG_PATH,
    proposal_review_log_path: str = _CONTRACT_PROPOSAL_REVIEW_LOG_PATH,
    max_records_per_source: int = 1000,
) -> dict:
    """
    Build a structured operator attention summary from Pass 1 sources.

    RETURN:
        {
            "record_type": "aai_attention_summary_v1",
            "generated_at": "ISO-8601",
            "authority": "attention_only",
            "automatic_change": False,
            "levels": {
                "0": [...],   suppress
                "1": [...],   track
                "2": [...],   summary
                "3": [...],   ask
                "4": [...]    interrupt
            },
            "operator_message": "...",
            "counts": { "total": N, "level_0": N, "level_1": N, ... },
            "sources_read": [...]
        }
    """
    now = datetime.now(timezone.utc).isoformat()

    # Read all sources
    public_signals = _read_jsonl(public_signals_path, max_records_per_source)
    contract_observations = _read_jsonl(contract_observations_path, max_records_per_source)
    insufficiency_records = _read_jsonl(insufficiency_log_path, max_records_per_source)
    proposal_reviews = _read_jsonl(proposal_review_log_path, max_records_per_source)

    sources_read = [
        public_signals_path,
        contract_observations_path,
        insufficiency_log_path,
        proposal_review_log_path,
    ]

    # Classify all records
    levels: dict[int, list[dict]] = {0: [], 1: [], 2: [], 3: [], 4: []}

    for rec in contract_observations:
        classified = classify_attention_item(rec)
        lvl = classified["attention_level"]
        levels[lvl].append(classified)

    for rec in public_signals:
        classified = classify_attention_item(rec)
        lvl = classified["attention_level"]
        levels[lvl].append(classified)

    for rec in insufficiency_records:
        classified = classify_attention_item(rec)
        lvl = classified["attention_level"]
        levels[lvl].append(classified)

    for rec in proposal_reviews:
        classified = classify_attention_item(rec)
        lvl = classified["attention_level"]
        levels[lvl].append(classified)

    counts = {str(k): len(v) for k, v in levels.items()}
    counts["total"] = sum(counts.values())

    # Build operator message
    level_3_count = len(levels[3])
    level_4_count = len(levels[4])
    level_2_count = len(levels[2])

    if level_4_count > 0:
        operator_message = (
            f"AAI ALERT: {level_4_count} critical attention item(s) require immediate operator review. "
            "Critical privacy, truth, or governance breach detected."
        )
    elif level_3_count > 0:
        operator_message = (
            f"{level_3_count} item(s) require operator review. "
            "Not urgent — review at next convenient interaction. "
            "No automatic changes will be made."
        )
    elif level_2_count > 0:
        operator_message = (
            f"No immediate operator action required. "
            f"{level_2_count} item(s) accumulated for periodic summary. "
            "All signals operating within normal parameters."
        )
    else:
        operator_message = (
            "No immediate operator action required. "
            "All Pass 1 sources operating within normal parameters. "
            "Level 0 (noise) records are suppressed. Level 1 (tracking) records are logged."
        )

    return {
        "record_type": "aai_attention_summary_v1",
        "generated_at": now,
        "authority": _AUTHORITY,
        "automatic_change": _AUTOMATIC_CHANGE,
        "levels": {str(k): v for k, v in levels.items()},
        "operator_message": operator_message,
        "counts": counts,
        "sources_read": sources_read,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    summary = build_attention_summary()
    print(json.dumps(summary, indent=2, default=str))