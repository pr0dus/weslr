"""WESLR write handler registry — state-changing operations.

Single registry entry point. Each entry is a declarative mapping:
  id            — unique handler identifier
  path          — response path label
  triggers      — list of prefix trigger strings
  match_type    — "prefix" for now
  priority      — higher = checked first
  handler_fn    — name of handler function in this module
  read_only     — False for write handlers
  writes        — [DEPRECATED] list of write targets
  write_paths   — declared JSONL files written by this handler
  side_effects  — human-readable action tags
  write_guard   — idempotency guard function name, or None
  requires_confirmation — True if operator confirmation required before write
  category      — "iss", "plan", etc.

Write handlers are dispatched separately from read handlers.
They are called after the read-handler dispatcher returns None.
"""

from __future__ import annotations

from typing import Optional

from weslr.response_formatter import build_write_response
from weslr.iss.diagnostic_records import load_iss_diagnostics
from weslr.proposal_traceability import record_proposal, proposal_exists


# ---- Write Handlers ----


def handle_iss_controlled_proposal_intake(message: str, lowered: str) -> dict:
    """
    ISS controlled proposal intake — converts an ISS gap into a traced proposal.
    Operator-requested write; no execution allowed.
    """
    raw = None
    for t in (
        "convert iss suggestion ",
        "convert iss gap ",
        "create proposal from iss ",
        "turn iss gap ",
    ):
        if lowered.startswith(t):
            raw = lowered[len(t):].strip().strip('"').strip("'")
            break

    if not raw:
        return build_write_response(
            message=message,
            path="ISS_controlled_proposal_intake",
            action_performed="proposal_check",
            affected_ids=[],
            response_text="No ISS gap ID provided.",
            write_confirmed=False,
            extra={"intake_result": {"created": False, "reason": "missing_id"}},
        )

    # Normalize: handle "gap.xxx" prefix
    if raw.startswith("gap."):
        requested_gap_id = raw
        proposal_id = raw[4:].strip()
    else:
        proposal_id = raw
        requested_gap_id = "gap." + raw

    # Load ISS records and find matching gap
    try:
        records = load_iss_diagnostics(50)
    except Exception:
        records = []

    gaps = [r for r in records if r.get("type") == "iss_gap_signal"]
    matched = None
    for g in gaps:
        if g.get("gap_id") == requested_gap_id or g.get("gap_id", "").endswith(proposal_id):
            matched = g
            break

    if not matched:
        return build_write_response(
            message=message,
            path="ISS_controlled_proposal_intake",
            action_performed="proposal_check",
            affected_ids=[proposal_id],
            response_text=f"No ISS gap found for '{raw}'. Use 'show gaps' to inspect available gaps.",
            write_confirmed=False,
            extra={
                "intake_result": {
                    "created": False,
                    "reason": "gap_not_found",
                    "requested_id": raw,
                }
            },
        )

    source_gap_id = matched.get("gap_id", "")

    # Idempotency guard — do not write if already exists
    if proposal_exists(proposal_id, source_gap_id):
        return build_write_response(
            message=message,
            path="ISS_controlled_proposal_intake",
            action_performed="proposal_check",
            affected_ids=[proposal_id],
            response_text=f"ISS suggestion '{proposal_id}' is already a traced proposal.",
            write_confirmed=False,
            extra={
                "intake_result": {
                    "created": False,
                    "reason": "already_exists",
                    "proposal_id": proposal_id,
                    "source_gap_id": source_gap_id,
                }
            },
        )

    # Record proposal trace (created, not approved)
    proposal_payload = {
        "summary": matched.get("summary", ""),
        "source": "ISS",
        "source_gap_id": source_gap_id,
        "severity": matched.get("severity", "medium"),
        "confidence": matched.get("confidence", "medium"),
        "suggested": True,
        "operator_requested_intake": True,
    }
    record_proposal(proposal_id, proposal_payload)

    return build_write_response(
        message=message,
        path="ISS_controlled_proposal_intake",
        action_performed="proposal_created",
        affected_ids=[proposal_id],
        response_text=f"ISS suggestion '{proposal_id}' was converted into a traced proposal. It is not approved and no implementation plan was created.",
        write_confirmed=True,
        extra={
            "intake_result": {
                "created": True,
                "proposal_id": proposal_id,
                "source_gap_id": source_gap_id,
                "approval_status": "not_approved",
                "plan_created": False,
                "execution_allowed": False,
            }
        },
    )


# ---- Registry ----

WRITE_HANDLER_REGISTRY = [
    {
        "id": "iss_controlled_proposal_intake",
        "path": "ISS_controlled_proposal_intake",
        "triggers": [
            "convert iss suggestion ",
            "convert iss suggestion",
            "convert iss gap ",
            "convert iss gap",
            "create proposal from iss ",
            "turn iss gap ",
        ],
        "match_type": "prefix",
        "priority": 66,
        "handler_fn": "handle_iss_controlled_proposal_intake",
        "read_only": False,
        "writes": ["weslr/proposal_trace.jsonl"],
        "write_paths": ["weslr/proposal_trace.jsonl"],
        "side_effects": ["proposal_created"],
        "write_guard": "proposal_exists",
        "requires_confirmation": False,
        "category": "iss",
    },
]


# ---- Dispatch ----

def dispatch_write_handler(message: str, lowered: str) -> Optional[dict]:
    """
    Sort write registry by priority descending, try prefix match, return handler result.
    Returns None if no trigger matches.
    """
    sorted_handlers = sorted(WRITE_HANDLER_REGISTRY, key=lambda h: h["priority"], reverse=True)
    for entry in sorted_handlers:
        for trigger in entry["triggers"]:
            if lowered.startswith(trigger):
                handler_fn_name = entry["handler_fn"]
                handler_fn = globals().get(handler_fn_name)
                if handler_fn is not None:
                    return handler_fn(message, lowered)
    return None
