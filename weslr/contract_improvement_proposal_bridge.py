"""
WESLR Contract Improvement Proposal Bridge V1

Reads proposal-ready insufficiency evidence from the insufficiency log and
produces operator-reviewable proposal records.

Does NOT:
- change behavior
- auto-approve proposals
- apply any contract change
- modify production truth files (proposal_trace.jsonl, implementation_plans.jsonl)
- change _CONTRACT_REPLIES or response text
- use LLM inference
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Storage configuration
# ---------------------------------------------------------------------------

DEFAULT_INSUFFICIENCY_LOG_PATH = "weslr/contract_insufficiency_log.jsonl"
DEFAULT_PROPOSAL_LOG_PATH = "weslr/contract_proposal_review_log.jsonl"

# ---------------------------------------------------------------------------
# Deduplication key components (fields that make a proposal unique)
# ---------------------------------------------------------------------------
_DEDUP_KEY_FIELDS = ("pattern_type", "contract", "response_path", "stable_across_checks")

# ---------------------------------------------------------------------------
# Proposal ID counter (per-run, monotonic)
# ---------------------------------------------------------------------------

_proposal_counter: int = 0


def _next_proposal_id() -> str:
    """Generate a deterministic proposal ID within this run."""
    global _proposal_counter
    _proposal_counter += 1
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"CP-{today}-{_proposal_counter:03d}"


def _reset_counter() -> None:
    """Reset counter — for testing only."""
    global _proposal_counter
    _proposal_counter = 0


# ---------------------------------------------------------------------------
# Record validation
# ---------------------------------------------------------------------------

_PII_PATTERNS = (
    "@",
    "http://",
    "https://",
    ".com",
    ".org",
    ".de",
    "www.",
    "phone:",
    "contact:",
    "0x",
    "192.168.",
    "10.",
    "172.",
)


def _has_pii(value) -> bool:
    """Check a single value for PII signals."""
    if isinstance(value, str):
        lower = value.lower()
        for pat in _PII_PATTERNS:
            if pat in lower:
                return True
    return False


def _forbidden_fields() -> frozenset:
    return frozenset({
        "raw_prompt",
        "prompt",
        "message",
        "user_input",
        "email",
        "phone",
        "ip",
        "address",
        "raw_message",
    })


def _is_valid_proposal_record(record: dict) -> bool:
    """Validate record is not a disallowed proposal record."""
    for field in _forbidden_fields():
        if field in record:
            return False
    return True


# ---------------------------------------------------------------------------
# Proposal record builder
# ---------------------------------------------------------------------------

def _build_proposal_record(evidence: dict, proposal_id: str) -> dict:
    """Build a contract_proposal_review_v1 record from insufficiency evidence."""
    return {
        "record_type": "contract_proposal_review_v1",
        "proposal_id": proposal_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pattern_type": evidence.get("pattern_type", "unknown"),
        "contract": evidence.get("contract", "unknown"),
        "response_path": evidence.get("response_path", "unknown"),
        "evidence_summary": {
            "occurrence_count": evidence.get("occurrence_count", 0),
            "signal_types_seen": evidence.get("signal_types_seen", []),
            "frame_distribution": evidence.get("frame_distribution", {}),
            "stable_across_checks": evidence.get("stable_across_checks", 0),
            "window_size": evidence.get("window_size", 0),
        },
        "operator_action_requested": "review_contract_outcome",
        "automatic_change": False,
        "proposal_status": "pending_review",
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _proposal_dedup_key(evidence: dict) -> str:
    """Build a deduplication key from evidence fields."""
    parts = []
    for field in _DEDUP_KEY_FIELDS:
        parts.append(str(evidence.get(field, "")))
    return "::".join(parts)


def _load_existing_proposal_keys(log_path: str) -> set[str]:
    """Load all existing proposal dedup keys from the proposal log."""
    p = pathlib.Path(log_path)
    if not p.exists():
        return set()
    keys = set()
    with open(p) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("record_type") == "contract_proposal_review_v1":
                    # Reconstruct dedup key from stored record
                    parts = []
                    for field in _DEDUP_KEY_FIELDS:
                        if field in rec.get("evidence_summary", {}):
                            parts.append(str(rec["evidence_summary"][field]))
                        elif field in rec:
                            parts.append(str(rec[field]))
                        else:
                            parts.append("")
                    keys.add("::".join(parts))
            except Exception:
                continue
    return keys


# ---------------------------------------------------------------------------
# Main bridge function
# ---------------------------------------------------------------------------

def generate_proposals(
    insufficiency_log_path: str | None = None,
    proposal_log_path: str | None = None,
) -> dict:
    """
    Read insufficiency log, extract proposal_ready=True evidence,
    deduplicate, and append review records to proposal log.

    Returns dict with:
        - generated: count of new review records appended
        - skipped_duplicates: count skipped as already proposed
        - skipped_non_ready: count skipped as not proposal_ready
        - malformed: count skipped as unreadable
        - total_processed: total lines read from source
    """
    log_path = insufficiency_log_path or DEFAULT_INSUFFICIENCY_LOG_PATH
    proposal_path = proposal_log_path or DEFAULT_PROPOSAL_LOG_PATH

    result = {
        "generated": 0,
        "skipped_duplicates": 0,
        "skipped_non_ready": 0,
        "malformed": 0,
        "total_processed": 0,
    }

    log_p = pathlib.Path(log_path)
    if not log_p.exists():
        # Source log missing — safe to return empty
        return result

    # Pre-load existing dedup keys (only for records from this log path)
    existing_keys = _load_existing_proposal_keys(proposal_path)

    new_records = []
    for line in log_p.read_text().splitlines():
        result["total_processed"] += 1
        if not line.strip():
            continue
        try:
            evidence = json.loads(line)
        except Exception:
            result["malformed"] += 1
            continue

        # Skip records that look like disallowed proposal submissions
        if not _is_valid_proposal_record(evidence):
            result["malformed"] += 1
            continue

        # Filter: only proposal_ready=True
        if not evidence.get("proposal_ready"):
            result["skipped_non_ready"] += 1
            continue

        # Filter: stable_across_checks >= 3
        if evidence.get("stable_across_checks", 0) < 3:
            result["skipped_non_ready"] += 1
            continue

        # Filter: insufficiency_confirmed == true (when present)
        if "insufficiency_confirmed" in evidence and not evidence["insufficiency_confirmed"]:
            result["skipped_non_ready"] += 1
            continue

        # Filter: record type must be contract_insufficiency_v1 or have pattern info
        if evidence.get("record_type") not in (
            "contract_insufficiency_v1",
            "contract_proposal_review_v1",
        ) and not evidence.get("pattern_type"):
            result["malformed"] += 1
            continue

        # Check PII in string values
        has_pii = False
        for v in evidence.values():
            if _has_pii(v):
                has_pii = True
                break
        if has_pii:
            result["malformed"] += 1
            continue

        # Deduplication check
        dedup_key = _proposal_dedup_key(evidence)
        if dedup_key in existing_keys:
            result["skipped_duplicates"] += 1
            continue

        # Build and record
        existing_keys.add(dedup_key)
        proposal_id = _next_proposal_id()
        record = _build_proposal_record(evidence, proposal_id)
        new_records.append(record)
        result["generated"] += 1

    # Append all new records
    if new_records:
        try:
            with open(proposal_path, "a") as f:
                for rec in new_records:
                    f.write(json.dumps(rec) + "\n")
        except Exception:
            # Fire-and-forget — if write fails, report zero generated
            result["generated"] = 0
            result["malformed"] = result["total_processed"]

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    log_path = sys.argv[2] if len(sys.argv) > 2 else None
    proposal_path = sys.argv[3] if len(sys.argv) > 3 else None
    result = generate_proposals(log_path, proposal_path)
    print(json.dumps(result, indent=2))
