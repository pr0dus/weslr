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


def _validate_implementation_plan(plan: dict):
    if plan.get("type") != "implementation_plan":
        raise ValueError(f"type must be 'implementation_plan', got {plan.get('type')!r}")
    if not isinstance(plan.get("plan_id"), str) or not plan["plan_id"].strip():
        raise ValueError(f"plan_id must be a non-empty string")
    if not isinstance(plan.get("proposal_id"), str) or not plan["proposal_id"].strip():
        raise ValueError(f"proposal_id must be a non-empty string")
    if plan.get("execution_allowed") is not False:
        raise ValueError(f"execution_allowed must be False, got {plan.get('execution_allowed')!r}")
    if plan.get("operator_approval_required") is not True:
        raise ValueError(f"operator_approval_required must be True")
    if not isinstance(plan.get("steps"), list) or len(plan["steps"]) == 0:
        raise ValueError(f"steps must be a non-empty list")
    if not isinstance(plan.get("risks"), list):
        raise ValueError(f"risks must be a list")
    if not isinstance(plan.get("rollback_notes"), list):
        raise ValueError(f"rollback_notes must be a list")


def record_implementation_plan(plan: dict) -> None:
    """
    Append a plan to the JSONL log.
    The plan must have been created by create_implementation_plan.
    """
    _validate_implementation_plan(plan)
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

    records = []
    for l in all_lines[-limit:]:
        try:
            records.append(__import__("json").loads(l))
        except __import__("json").JSONDecodeError:
            continue
    return records
