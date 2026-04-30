"""
WESLR Contract Observation Layer V1

Passive observation of response contract outcomes from the /chat pipeline.
Read-only — does NOT change behavior, routing, or responses.

This module does NOT:
- store raw user messages
- store PII
- modify response behavior
- infer values
- create proposals
- use LLM
- write to public_signals.jsonl
- write to production truth files
- ever truncate/overwrite/delete existing data
"""

from __future__ import annotations

import json
import pathlib
import re

# ---------------------------------------------------------------------------
# Storage configuration
# ---------------------------------------------------------------------------

DEFAULT_PATH = "weslr/contract_observations.jsonl"

_PRODUCTION_FILES = frozenset({
    "proposal_trace.jsonl",
    "implementation_plans.jsonl",
    "diagnostic_records.jsonl",
    "state_checkpoint.json",
    "public_signals.jsonl",
})

# ---------------------------------------------------------------------------
# Forbidden fields — never allowed in observation records
# ---------------------------------------------------------------------------

_FORBIDDEN_FIELDS: frozenset[str] = frozenset({
    "message",
    "raw_message",
    "prompt",
    "raw_prompt",
    "user_input",
    "email",
    "phone",
    "address",
    "ip",
    "user_id",
    "name",
    "location",
})

# ---------------------------------------------------------------------------
# PII-like detection (conservative)
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"@")
_PHONE_RE = re.compile(r"\b\d{7,}\b")
_IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_STREET_RE = re.compile(r"\b(street|strasse|straße|road|avenue|blvd)\b", re.I)


def _has_pii_like(record: dict) -> bool:
    """Recursively scan all string keys and values for PII-like content."""
    def scan(d: dict) -> bool:
        for k, v in d.items():
            if isinstance(k, str):
                if _EMAIL_RE.search(k) or _IPV4_RE.search(k) or _STREET_RE.search(k):
                    return True
            sv = str(v)
            if isinstance(v, str):
                if _EMAIL_RE.search(sv) or _PHONE_RE.search(sv) or _IPV4_RE.search(sv) or _STREET_RE.search(sv):
                    return True
            if isinstance(v, dict):
                if scan(v):
                    return True
        return False
    return scan(record)


# ---------------------------------------------------------------------------
# Record builder (pure function — no side effects)
# ---------------------------------------------------------------------------

def build_contract_observation(
    event: dict,
    interpreted: dict,
    public_signal_record: dict | None = None,
) -> dict:
    """
    Build a contract observation record from /chat pipeline data.

    INPUTS:
        event — the safe event dict passed to capture_website_signal:
            session_id_hash, message_length_bucket, response_path,
            fallback_triggered, evidence_offer_shown, evidence_offer_accepted,
            blocked_write, topic_normalized, timestamp

        interpreted — output of interpret_human_turn() with all frame fields:
            interaction_frame, frame_turn_type, frame_reply_shape,
            response_contract, turn_type, reply_shape, path

        public_signal_record — optional output of build_public_signal_record()
            (provides signal_type). If None, signal_type defaults to null.

    RETURN:
        dict with fields:
            record_type: "contract_observation_v1"
            response_contract: str
            interaction_frame: str
            turn_type: str
            reply_shape: str
            signal_type: "S1"|"S2"|"S4"|"S5"|null
            response_path: str
            source: "website_public"
            safe_to_record: true
            raw_prompt_stored: false
            pii_stored: false
            behavior_change_allowed: false
            value_inference_allowed: false
            timestamp: str
            session_id_hash: str

    RULES:
        - Uses only metadata already allowed in public signal flow
        - Does NOT store raw message / user identity / name / email / phone / IP / location
        - safe_to_record is always true (observation is passive)
        - behavior_change_allowed is always false
        - value_inference_allowed is always false
    """
    from datetime import datetime, timezone

    # Resolve signal_type from public_signal_record if provided
    signal_type: str | None = None
    if public_signal_record is not None:
        sig = public_signal_record.get("signal_type")
        if sig in ("S1", "S2", "S4", "S5"):
            signal_type = sig

    return {
        "record_type": "contract_observation_v1",
        "response_contract": str(interpreted.get("response_contract", "unknown")),
        "interaction_frame": str(interpreted.get("interaction_frame", "unknown")),
        "turn_type": str(interpreted.get("turn_type", "statement")),
        "reply_shape": str(interpreted.get("reply_shape", "answer_directly")),
        "signal_type": signal_type,
        "response_path": str(event.get("response_path", "unknown")),
        "source": "website_public",
        "safe_to_record": True,
        "raw_prompt_stored": False,
        "pii_stored": False,
        "behavior_change_allowed": False,
        "value_inference_allowed": False,
        "timestamp": str(event.get("timestamp", datetime.now(timezone.utc).isoformat())),
        "session_id_hash": str(event.get("session_id_hash", "")),
    }


# ---------------------------------------------------------------------------
# Validation (pure function — no side effects)
# ---------------------------------------------------------------------------

def validate_contract_observation(record: dict) -> dict:
    """
    Validate a contract observation record.

    RETURN: {"valid": bool, "reason": str, "forbidden_fields": list[str]}

    Rejects:
        - missing or wrong record_type
        - safe_to_record != true
        - raw_prompt_stored != false
        - pii_stored != false
        - behavior_change_allowed != false
        - value_inference_allowed != false
        - any forbidden field present anywhere recursively
    """
    # 1. record_type check
    if record.get("record_type") != "contract_observation_v1":
        return {"valid": False, "reason": "invalid_record_type", "forbidden_fields": []}

    # 2. safe_to_record must be True
    if record.get("safe_to_record") is not True:
        return {"valid": False, "reason": "safe_to_record_not_true", "forbidden_fields": []}

    # 3. safety flags must all be False
    for field in (
        "raw_prompt_stored",
        "pii_stored",
        "behavior_change_allowed",
        "value_inference_allowed",
    ):
        if record.get(field) is not False:
            return {"valid": False, "reason": f"{field}_not_false", "forbidden_fields": []}

    # 4. recursive forbidden field scan
    found: list[str] = []

    def scan(d: dict, prefix: str = "") -> None:
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if k in _FORBIDDEN_FIELDS:
                found.append(full)
            if isinstance(v, dict):
                scan(v, full)

    scan(record)

    if found:
        return {"valid": False, "reason": "forbidden_field_detected", "forbidden_fields": found}

    return {"valid": True, "reason": "valid", "forbidden_fields": []}


# ---------------------------------------------------------------------------
# Append store (side effect — file write)
# ---------------------------------------------------------------------------

def append_contract_observation(
    record: dict,
    path: str | None = None,
) -> dict:
    """
    Append a contract observation record to contract_observations.jsonl.

    RETURN: {"stored": bool, "reason": str, "path": str, "record_type": "contract_observation_v1"}

    Rules:
        - append-only (one JSON line per record)
        - reject invalid records
        - never write to public_signals.jsonl
        - never write to production truth files
        - never truncate/overwrite/delete existing data
        - if path is None, defaults to weslr/contract_observations.jsonl
    """
    target = path or DEFAULT_PATH
    workspace = pathlib.Path(__file__).resolve().parents[1]
    file_path = workspace / target

    # Guard: never write to public_signals.jsonl or production files
    if file_path.name in _PRODUCTION_FILES:
        return {
            "stored": False,
            "reason": "production_file_rejected",
            "path": str(file_path),
            "record_type": "contract_observation_v1",
        }

    # Step 1: structural validation
    validation = validate_contract_observation(record)
    if not validation["valid"]:
        return {
            "stored": False,
            "reason": validation["reason"],
            "path": str(file_path),
            "record_type": "contract_observation_v1",
        }

    # Step 2: recursive forbidden field scan (for raw records passed directly)
    forbidden_found: list[str] = []

    def scan(d: dict, prefix: str = "") -> None:
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if k in _FORBIDDEN_FIELDS:
                forbidden_found.append(full)
            if isinstance(v, dict):
                scan(v, full)

    scan(record)

    if forbidden_found:
        return {
            "stored": False,
            "reason": "forbidden_field_detected",
            "path": str(file_path),
            "record_type": "contract_observation_v1",
        }

    # Step 3: PII scan
    if _has_pii_like(record):
        return {
            "stored": False,
            "reason": "pii_like_content_detected",
            "path": str(file_path),
            "record_type": "contract_observation_v1",
        }

    # Append-only write
    try:
        with open(file_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        return {
            "stored": False,
            "reason": f"write_error_{type(e).__name__}",
            "path": str(file_path),
            "record_type": "contract_observation_v1",
        }

    return {
        "stored": True,
        "reason": "stored",
        "path": str(file_path),
        "record_type": "contract_observation_v1",
    }