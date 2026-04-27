#!/usr/bin/env python3
"""ISS audit adapter — convert evaluator output into AuditLedger-compatible events.

Does NOT write to iss_records.jsonl. Routes through AuditLedgerEngine only.
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add workspace to path for imports
WORKSPACE = "/data/data/com.termux/files/home/.openclaw/workspace"
sys.path.insert(0, WORKSPACE)

from weslr.audit_ledger import (
    AuditLedgerEngine,
    AuditSource,
    LedgerEvent,
    LedgerEventType,
)


LEDGER_STORAGE = f"{WORKSPACE}/weslr/audit_ledger/"
AUDIT_LEDGER_ID = "iss_probe_ledger"
LEDGER_NAME = "ISS Probe Audit Ledger"
LEDGER_DESCRIPTION = "Audit ledger for ISS probe results routed through AuditLedgerEngine"


def build_probe_event(evaluator_result: dict) -> dict:
    """Build an audit-compatible event dict from evaluator output."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    probe_id = f"probe_{uuid.uuid4().hex[:12]}"

    event_type = LedgerEventType.PROPOSAL_CREATED.value  # best fit; no probe-specific type exists

    # Encode evaluator output as evidence reference
    evidence_ref = json.dumps({
        "system": evaluator_result.get("system", "unknown"),
        "overall_status": evaluator_result.get("overall_status", "UNKNOWN"),
        "broken": evaluator_result.get("broken", []),
        "degraded": evaluator_result.get("degraded", []),
        "recommended_next_step": evaluator_result.get("recommended_next_step", "observe_only"),
        "evidence": evaluator_result.get("evidence", {}),
    }, separators=(",", ":"))

    event = {
        "event_id": f"event_{probe_id}",
        "event_type": event_type,
        "timestamp": timestamp,
        "source": AuditSource.SYSTEM.value,
        "actor_id": "iss_adapter",
        "actor_role": "system",
        "affected_object_id": probe_id,
        "affected_object_type": "probe_result",
        "evidence_references": [evidence_ref],
        "approval_status": None,
        "approval_notes": None,
        "before_state": {"status": "probe_scheduled"},
        "after_state": {
            "status": evaluator_result.get("overall_status", "UNKNOWN"),
            "system": evaluator_result.get("system", "unknown"),
            "broken": evaluator_result.get("broken", []),
            "degraded": evaluator_result.get("degraded", []),
            "recommended_next_step": evaluator_result.get("recommended_next_step", "observe_only"),
        },
        "context_id": "iss",
        "deployment_role": None,
        "capability_boundary_id": None,
        "escalation_id": None,
        "level": "INFO",
        "created_at": timestamp,
        "author": "iss_adapter",
    }

    return event


def record_to_audit(evaluator_result: dict) -> dict:
    """Write evaluator result to AuditLedgerEngine. Returns the written event."""
    # Ensure storage path exists
    Path(LEDGER_STORAGE).mkdir(parents=True, exist_ok=True)

    # Create or get engine
    engine = AuditLedgerEngine(storage_path=LEDGER_STORAGE)

    # Create dedicated ISS ledger if it doesn't exist
    if engine.get_ledger(AUDIT_LEDGER_ID) is None:
        engine.create_ledger(
            ledger_id=AUDIT_LEDGER_ID,
            name=LEDGER_NAME,
            description=LEDGER_DESCRIPTION,
            author="iss_adapter",
        )

    # Build event
    event_dict = build_probe_event(evaluator_result)

    # Get ISS ledger and add event
    ledger = engine.get_ledger(AUDIT_LEDGER_ID)
    ledger.add_event(event_dict)

    # Persist
    from weslr.audit_ledger import AuditLedger
    engine._save_ledger(ledger)

    return event_dict


def main():
    # Default sample if no input
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

    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                evaluator_result = json.load(f)
        except Exception:
            evaluator_result = json.loads(sys.argv[1])
    else:
        evaluator_result = sample

    event = record_to_audit(evaluator_result)
    print(json.dumps(event, indent=2))


if __name__ == "__main__":
    main()