"""
WESLR Public Signal Append Store V1

Append-only storage for safe public signal records from user_signal_intake.py.
Uses a separate observation file, not production truth files.

This module does NOT:
- store raw user messages
- store PII
- modify response behavior
- infer values
- create proposals
- change public prompt
- expose internal doctrine
- use LLM
- write to production truth JSONL files
"""

from __future__ import annotations

import json
import pathlib
import re

# ---------------------------------------------------------------------------
# Storage configuration
# ---------------------------------------------------------------------------

DEFAULT_PATH = "weslr/public_signals.jsonl"

_PRODUCTION_FILES = frozenset({
    "proposal_trace.jsonl",
    "implementation_plans.jsonl",
    "diagnostic_records.jsonl",
    "state_checkpoint.json",
})

# ---------------------------------------------------------------------------
# Forbidden fields
# ---------------------------------------------------------------------------

_FORBIDDEN_FIELDS = frozenset({
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
# PII-like detection
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"@")
_PHONE_RE = re.compile(r"\b\d{7,}\b")
_IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_STREET_RE = re.compile(r"\b(street|strasse|road|avenue|blvd)\b", re.I)


def _has_pii_like(record: dict) -> bool:
    """Scan all string keys and values for PII-like content."""
    def scan(d: dict):
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
# Validation
# ---------------------------------------------------------------------------

def validate_public_signal_record(record: dict) -> dict:
    """
    RETURN: {"valid": bool, "reason": str, "forbidden_fields": list[str]}

    Validation order:
    1. safe_to_record must be True
    2. forbidden field in record → forbidden_field_detected
    3. invalid record_type → invalid_record_type
    4. safety flag not False → <field>_not_false
    """
    # 1. safe_to_record must be True
    if record.get("safe_to_record") is not True:
        return {"valid": False, "reason": "safe_to_record_not_true", "forbidden_fields": []}

    # 2. forbidden field scan
    found: list[str] = []

    def scan_keys(d: dict, prefix: str = ""):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if k in _FORBIDDEN_FIELDS:
                found.append(full)
            if isinstance(v, dict):
                scan_keys(v, full)

    scan_keys(record)

    if found:
        return {"valid": False, "reason": "forbidden_field_detected", "forbidden_fields": found}

    # 3. record_type
    if record.get("record_type") != "public_signal_v1":
        return {"valid": False, "reason": "invalid_record_type", "forbidden_fields": []}

    # 4. all safety flags must be False
    for field in ("raw_prompt_stored", "pii_stored",
                  "behavior_change_allowed", "value_inference_allowed"):
        if record.get(field) is not False:
            return {"valid": False, "reason": f"{field}_not_false", "forbidden_fields": []}

    return {"valid": True, "reason": "valid", "forbidden_fields": []}


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------

def append_public_signal_record(record: dict, path: str | None = None) -> dict:
    """
    RETURN: {"stored": bool, "reason": str, "path": str, "record_type": "public_signal_v1"}
    """
    target = path or DEFAULT_PATH
    workspace = pathlib.Path(__file__).resolve().parents[1]
    file_path = workspace / target

    # Guard: never write to production files
    if file_path.name in _PRODUCTION_FILES:
        return {
            "stored": False,
            "reason": "production_file_rejected",
            "path": str(file_path),
            "record_type": "public_signal_v1",
        }

    # Step 1: forbidden field scan (for raw records passed directly)
    forbidden_found: list[str] = []

    def scan(d: dict, prefix: str = ""):
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
            "record_type": "public_signal_v1",
        }

    # Step 2: PII scan
    if _has_pii_like(record):
        return {
            "stored": False,
            "reason": "pii_like_content_detected",
            "path": str(file_path),
            "record_type": "public_signal_v1",
        }

    # Step 3: structural validation
    validation = validate_public_signal_record(record)
    if not validation["valid"]:
        return {
            "stored": False,
            "reason": validation["reason"],
            "path": str(file_path),
            "record_type": "public_signal_v1",
        }

    # Append-only
    try:
        with open(file_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        return {
            "stored": False,
            "reason": f"write_error_{type(e).__name__}",
            "path": str(file_path),
            "record_type": "public_signal_v1",
        }

    return {
        "stored": True,
        "reason": "stored",
        "path": str(file_path),
        "record_type": "public_signal_v1",
    }
