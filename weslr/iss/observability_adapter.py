#!/usr/bin/env python3
"""ISS observability adapter — convert evaluator output to AuditEvent-compatible format.

Does NOT write files. Observability.py is a read-only query layer (get_routing_timeline,
get_governance_decisions, get_proposal_lifecycle). ISS emits AuditEvent-compatible dicts
that can be consumed by external observability pipelines.
"""

import json
import sys
import time
from datetime import datetime, timezone

# AuditEvent field types:
#   timestamp: int  (Unix timestamp)
#   event_type: str  ("routing" or "governance")
#   proposal_id: str
#   action: str
#   actor: str
#   from_status: Optional[str]
#   to_status: Optional[str]
#   notes: str = ""
#   details: Dict[str, Any] = field(default_factory=dict)


SEVERITY_MAP = {
    "OK": "info",
    "DEGRADED": "warning",
    "BROKEN": "error",
}


def build_audit_event(evaluator_result: dict) -> dict:
    """Convert evaluator output to AuditEvent-compatible dict."""
    overall = evaluator_result.get("overall_status", "UNKNOWN")
    system = evaluator_result.get("system", "unknown")
    severity = SEVERITY_MAP.get(overall, "info")

    # Build probe_id as proposal_id stand-in
    import uuid
    probe_id = f"iss-probe-{uuid.uuid4().hex[:12]}"

    timestamp = int(time.time())
    timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

    # Map status to from_status/to_status
    if overall == "OK":
        from_status = None
        to_status = "operational"
    elif overall == "DEGRADED":
        from_status = "operational"
        to_status = "degraded"
    else:  # BROKEN
        from_status = "degraded"
        to_status = "broken"

    # Build action name
    broken = evaluator_result.get("broken", [])
    degraded = evaluator_result.get("degraded", [])
    if broken:
        action = f"probe_failed:{','.join(broken)}"
    elif degraded:
        action = f"probe_degraded:{','.join(degraded)}"
    else:
        action = "probe_ok"

    # Build notes
    recommended = evaluator_result.get("recommended_next_step", "observe_only")
    notes = f"ISS probe [{system}] status={overall} recommended_next_step={recommended}"

    # Build details with full evaluator output
    details = {
        "system": system,
        "overall_status": overall,
        "severity": severity,
        "broken": broken,
        "degraded": degraded,
        "recommended_next_step": recommended,
        "evidence": evaluator_result.get("evidence", {}),
        "timestamp_iso": timestamp_str,
    }

    event = {
        "timestamp": timestamp,
        "event_type": "governance",  # probe result is a governance-scope event
        "proposal_id": probe_id,
        "action": action,
        "actor": "iss_adapter",
        "from_status": from_status,
        "to_status": to_status,
        "notes": notes,
        "details": details,
    }

    return event


def validate_ok() -> dict:
    sample = {
        "system": "exec",
        "overall_status": "OK",
        "broken": [],
        "degraded": [],
        "recommended_next_step": "observe_only",
        "evidence": {
            "git": {"status": "OK", "exit_code": 0},
            "python": {"status": "OK", "exit_code": 0},
            "node": {"status": "OK", "exit_code": 0},
        },
    }
    return build_audit_event(sample)


def validate_broken() -> dict:
    sample = {
        "system": "exec",
        "overall_status": "BROKEN",
        "broken": ["git"],
        "degraded": [],
        "recommended_next_step": "operator_review_required",
        "evidence": {
            "git": {"status": "BROKEN", "exit_code": 1},
            "python": {"status": "OK", "exit_code": 0},
            "node": {"status": "OK", "exit_code": 0},
        },
    }
    return build_audit_event(sample)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        print("=== OK CASE ===")
        ok_event = validate_ok()
        print(json.dumps(ok_event, indent=2))
        print("\n=== BROKEN CASE ===")
        broken_event = validate_broken()
        print(json.dumps(broken_event, indent=2))
    elif len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                evaluator_result = json.load(f)
        except Exception:
            evaluator_result = json.loads(sys.argv[1])
        print(json.dumps(build_audit_event(evaluator_result), indent=2))
    else:
        print("Usage: observability_adapter.py [--validate|<evaluator_json>]")


if __name__ == "__main__":
    main()