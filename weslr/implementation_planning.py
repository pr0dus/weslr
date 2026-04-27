import time
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
PLAN_FILE = _BASE_DIR / "implementation_plans.jsonl"

# Hard rule: execution is never allowed in this module
_EXECUTION_ALLOWED = False


def _write_plan(plan: dict):
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAN_FILE, "a", encoding="utf-8") as f:
        f.write(__import__("json").dumps(plan) + "\n")


def create_implementation_plan(proposal_id: str, proposal_content: dict) -> dict:
    """
    Build a structured implementation plan from a proposal_id + content.
    execution_allowed is ALWAYS False — this module never executes.
    """
    summary = proposal_content.get("summary") or proposal_content.get("proposal", "")
    score = proposal_content.get("score", 0.0)
    tier = proposal_content.get("tier", "medium")

    plan_id = f"plan-{proposal_id}-{int(time.time())}"

    # Three-phase safe plan: inspect → design → validate
    steps = [
        {
            "order": 1,
            "title": f"Inspect existing {proposal_id} implementation",
            "kind": "inspect",
            "allowed": True,
        },
        {
            "order": 2,
            "title": f"Design implementation approach for {proposal_id}",
            "kind": "design",
            "allowed": True,
        },
        {
            "order": 3,
            "title": f"Validate plan for {proposal_id} before operator review",
            "kind": "validate",
            "allowed": True,
        },
    ]

    decision_timestamp = proposal_content.get("decision_timestamp")
    trace_ref = {
        "proposal_created": None,
        "proposal_decision": decision_timestamp,
    }

    return {
        "type": "implementation_plan",
        "plan_id": plan_id,
        "proposal_id": proposal_id,
        "status": "planned",
        "execution_allowed": _EXECUTION_ALLOWED,
        "created_at": time.time(),
        "decision_timestamp": decision_timestamp,
        "trace_reference": trace_ref,
        "proposal_summary": summary,
        "proposal_score": score,
        "proposal_tier": tier,
        "steps": steps,
        "risks": [],
        "rollback_notes": [],
        "operator_approval_required": True,
    }


def record_implementation_plan(plan: dict) -> None:
    """
    Append a plan to the JSONL log.
    The plan must have been created by create_implementation_plan.
    """
    _write_plan(plan)


def load_implementation_plans(limit: int = 50) -> list[dict]:
    """
    Read the last `limit` plan records from the JSONL log.
    Returns oldest-first (chronological).
    """
    if not PLAN_FILE.exists():
        return []

    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    records = [__import__("json").loads(l) for l in all_lines[-limit:]]
    return records
