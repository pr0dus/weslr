"""
WESLR Review Interface V1

Read-only inspection layer for contract proposal review records.
Loads from weslr/contract_proposal_review_log.jsonl.

Does NOT:
- write to any file
- change proposal status
- approve/reject/defer
- modify contracts
- expose PII or raw prompts
- use LLM
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from .public_pilot_storage_privacy_safety import (
    build_public_pilot_quarantine_result_v1,
    require_public_pilot_storage_surface_not_quarantined_v1,
)

# ---------------------------------------------------------------------------
# Storage paths
# ---------------------------------------------------------------------------

DEFAULT_PROPOSAL_LOG_PATH = "weslr/contract_proposal_review_log.jsonl"

# ---------------------------------------------------------------------------
# Forbidden fields — never exposed
# ---------------------------------------------------------------------------

_FORBIDDEN_FIELDS = frozenset({
    "raw_prompt",
    "prompt",
    "message",
    "user_input",
    "raw_message",
    "email",
    "phone",
    "ip",
    "address",
    "name",
    "location",
})


def _strip_forbidden(record: dict) -> dict:
    """Return a copy with all forbidden fields removed."""
    return {k: v for k, v in record.items() if k not in _FORBIDDEN_FIELDS}


# ---------------------------------------------------------------------------
# Load all raw records from the proposal log
# ---------------------------------------------------------------------------


def _load_raw_records(log_path: str | None = None, *, public_pilot_mode: bool = False, authorization_metadata: dict[str, Any] | None = None) -> list[dict]:
    """Load all parseable records from the proposal log, stripping forbidden fields.


    Malformed lines are skipped silently. Forbidden fields are stripped from
    every record. Returns a safe, read-only copy of each record.
    """
    path = pathlib.Path(log_path or DEFAULT_PROPOSAL_LOG_PATH)
    if public_pilot_mode:
        require_public_pilot_storage_surface_not_quarantined_v1(
            path,
            public_pilot_mode=True,
            authorization_metadata=authorization_metadata,
        )
    if not path.exists():
        return []

    records = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            # Malformed line — skip silently
            continue
        if rec:
            # Always load, then strip — never reject a record for having
            # forbidden fields (strip them instead)
            records.append(_strip_forbidden(rec))
    return records


# ---------------------------------------------------------------------------
# load_pending_contract_reviews
# ---------------------------------------------------------------------------

def load_pending_contract_reviews(log_path: str | None = None, *, public_pilot_mode: bool = False, authorization_metadata: dict[str, Any] | None = None) -> list[dict]:
    """
    Return all review records where proposal_status == "pending_review".

    Each returned dict is a read-only copy with forbidden fields stripped.

    Returns:
        List[dict] — each dict has record_type, proposal_id, generated_at,
        pattern_type, contract, response_path, evidence_summary,
        operator_action_requested, automatic_change, proposal_status
    """
    records = _load_raw_records(log_path, public_pilot_mode=public_pilot_mode, authorization_metadata=authorization_metadata)
    pending = []
    for rec in records:
        if rec.get("proposal_status") == "pending_review":
            pending.append(_strip_forbidden(rec))
    return pending


# ---------------------------------------------------------------------------
# get_contract_review_by_id
# ---------------------------------------------------------------------------

def get_contract_review_by_id(
    proposal_id: str,
    log_path: str | None = None,
    *,
    public_pilot_mode: bool = False,
    authorization_metadata: dict[str, Any] | None = None,
) -> dict | None:
    """
    Return the review record with the given proposal_id, or None if not found.

    Returns None for missing, malformed, or unsafe records.
    """
    if not proposal_id or not isinstance(proposal_id, str):
        return None

    records = _load_raw_records(log_path, public_pilot_mode=public_pilot_mode, authorization_metadata=authorization_metadata)
    for rec in records:
        if rec.get("proposal_id") == proposal_id:
            return _strip_forbidden(rec)
    return None


# ---------------------------------------------------------------------------
# summarize_pending_reviews
# ---------------------------------------------------------------------------

def summarize_pending_reviews(log_path: str | None = None, *, public_pilot_mode: bool = False, authorization_metadata: dict[str, Any] | None = None) -> dict:
    """
    Return a read-only summary of all pending reviews.

    Returns:
        {
            "total_pending": int,
            "by_pattern_type": {str: int},
            "by_contract": {str: int},
            "by_response_path": {str: int},
            "records": list[dict]  # lightweight copies, no PII/raw
        }
    """
    pending = load_pending_contract_reviews(log_path, public_pilot_mode=public_pilot_mode, authorization_metadata=authorization_metadata)

    by_pattern_type: dict[str, int] = {}
    by_contract: dict[str, int] = {}
    by_response_path: dict[str, int] = {}

    for rec in pending:
        pt = rec.get("pattern_type", "unknown")
        ct = rec.get("contract", "unknown")
        rp = rec.get("response_path", "unknown")
        by_pattern_type[pt] = by_pattern_type.get(pt, 0) + 1
        by_contract[ct] = by_contract.get(ct, 0) + 1
        by_response_path[rp] = by_response_path.get(rp, 0) + 1

    # Lightweight record copies — strip nested forbidden fields too
    lightweight_records = []
    for rec in pending:
        lr = {
            "proposal_id": rec.get("proposal_id"),
            "generated_at": rec.get("generated_at"),
            "pattern_type": rec.get("pattern_type"),
            "contract": rec.get("contract"),
            "response_path": rec.get("response_path"),
            "operator_action_requested": rec.get("operator_action_requested"),
            "automatic_change": rec.get("automatic_change"),
            "proposal_status": rec.get("proposal_status"),
            "evidence_summary": rec.get("evidence_summary"),
        }
        lightweight_records.append(lr)

    return {
        "total_pending": len(pending),
        "by_pattern_type": by_pattern_type,
        "by_contract": by_contract,
        "by_response_path": by_response_path,
        "records": lightweight_records,
    }



def get_public_pilot_review_quarantine_result(log_path: str | None = None) -> dict:
    """Return blocked/quarantined metadata without reading review records."""
    return build_public_pilot_quarantine_result_v1(
        "review_interface",
        ["public_pilot_raw_review_access_quarantined"],
        path_label=str(log_path or DEFAULT_PROPOSAL_LOG_PATH),
    )

# ---------------------------------------------------------------------------
# CLI (read-only inspection)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python review_interface.py <list|summary|get> [proposal_id]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "list":
        pending = load_pending_contract_reviews()
        print(f"Pending reviews: {len(pending)}")
        for rec in pending:
            print(f"  {rec['proposal_id']}  {rec['pattern_type']}  contract={rec['contract']}")

    elif cmd == "summary":
        summary = summarize_pending_reviews()
        print(f"Total pending: {summary['total_pending']}")
        print(f"By pattern_type: {summary['by_pattern_type']}")
        print(f"By contract: {summary['by_contract']}")
        print(f"By response_path: {summary['by_response_path']}")

    elif cmd == "get" and len(sys.argv) >= 3:
        proposal_id = sys.argv[2]
        rec = get_contract_review_by_id(proposal_id)
        if rec:
            print(json.dumps(rec, indent=2))
        else:
            print(f"Proposal {proposal_id} not found")

    else:
        print("Usage: python review_interface.py <list|summary|get> [proposal_id]")
