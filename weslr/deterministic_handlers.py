"""WESLR deterministic handler registry — read-only query dispatch.

Single registry entry point. Each entry is a declarative mapping:
  id          — unique handler identifier
  path        — deterministic response path label
  triggers    — list of prefix trigger strings
  match_type  — "prefix" for now
  priority    — higher = checked first (sorted descending at dispatch)
  handler_fn  — name of handler function in this module
  read_only   — True (no writes)
  writes      — empty list
  requires_confirmation — False
  category    — "iss", "plan", etc.

Extracted handlers are pure read-only query responders.
No execution, no proposals, no state changes.
"""

from __future__ import annotations

from typing import Optional

from weslr.response_formatter import build_deterministic_response
from weslr.iss.probe_registry import get_probe_registry
from weslr.iss.probe_planning import create_probe_plan
from weslr.state_checkpoint import get_state_checkpoint
from weslr.iss.diagnostic_records import load_iss_diagnostics
from weslr.implementation_planning import load_implementation_plans
from weslr.proposal_traceability import load_trace


# ---- Handler functions ----

def handle_iss_probe_plan(message: str, lowered: str) -> dict:
    """ISS probe planning — read-only."""
    raw_probe_id = lowered.split("plan probe ", 1)[-1].split("how would you check ", 1)[-1].strip().strip('"').strip("'")
    probe_id = raw_probe_id.strip()
    probes = get_probe_registry()
    matched = next((p for p in probes if p["probe_id"] == probe_id), None)
    if not matched:
        return build_deterministic_response(
            message=message,
            path="ISS_probe_plan",
            response_text="No probe found for '" + probe_id + "'",
            confidence="high",
            suggested_mode="observe",
        )
    plan = create_probe_plan(matched)
    return build_deterministic_response(
        message=message,
        path="ISS_probe_plan",
        response_text="Probe '" + probe_id + "' can be checked in " + str(len(plan["steps"])) + " steps. Execution is not allowed.",
        payload={"probe_plan": plan},
        confidence="high",
        suggested_mode="observe",
    )


def handle_iss_probe_registry(message: str, lowered: str) -> dict:
    """ISS probe registry query — read-only."""
    probes = get_probe_registry()
    return build_deterministic_response(
        message=message,
        path="ISS_probe_registry_query",
        response_text="ISS has " + str(len(probes)) + " defined probe stubs. Execution allowed: False for all.",
        payload={"probe_registry": probes, "probe_count": len(probes)},
        confidence="high",
        suggested_mode="observe",
    )


def handle_operator_overview(message: str, lowered: str) -> dict:
    """Operator system overview — read-only, aggregates checkpoint + ISS + plans."""
    checkpoint = get_state_checkpoint()
    diagnostics = load_iss_diagnostics(20)
    plans = load_implementation_plans(10)
    gaps = [d for d in diagnostics if d.get("type") == "iss_gap_signal"]
    probes = [d for d in diagnostics if d.get("type") == "iss_probe_result"]
    ok_count = sum(1 for p in probes if p.get("status") == "ok")
    deg_count = sum(1 for p in probes if p.get("status") == "degraded")
    layer_ids = [l["id"] for l in checkpoint.get("layers", [])]

    response_text = (
        f"WESLR overview:\n"
        f"- {len(layer_ids)} layers confirmed\n"
        f"- {len(gaps)} diagnostic gap(s)\n"
        f"- {len(plans)} implementation plan(s)\n"
        f"- ISS probes: {ok_count} ok, {deg_count} degraded\n"
        f"System is deterministic, non-executing, and operator-controlled."
    )

    result = build_deterministic_response(
        message=message,
        path="operator_overview",
        response_text=response_text,
        payload={
            "overview": {
                "checkpoint": checkpoint,
                "gaps": gaps,
                "plans": plans,
                "summary": {
                    "layers_confirmed": len(layer_ids),
                    "gap_count": len(gaps),
                    "plan_count": len(plans),
                },
            },
        },
        confidence="high",
        suggested_mode="observe",
    )
    result["mode_analysis"] = {
        "current_mode": None,
        "suggested_mode": "observe",
        "match": True,
        "mismatch": False,
        "reason": "System overview query",
    }
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    return result


def handle_state_checkpoint(message: str, lowered: str) -> dict:
    """State checkpoint query — read-only."""
    cp = get_state_checkpoint()
    layer_ids = [l["id"] for l in cp.get("layers", [])]
    response_text = (
        f"WESLR checkpoint {cp['version']}: {cp['status']}. "
        f"Confirmed layers: {', '.join(layer_ids)}. "
        f"Execution allowed: {cp['execution_allowed']}. "
        f"Learning enabled: {cp['learning_enabled']}. "
        f"Autonomous changes: {cp['autonomous_changes_enabled']}."
    )
    result = build_deterministic_response(
        message=message,
        path="state_checkpoint_query",
        response_text=response_text,
        payload={"state_checkpoint": cp},
        confidence="high",
        suggested_mode="observe",
    )
    result["mode_analysis"] = {
        "current_mode": None,
        "suggested_mode": "observe",
        "match": True,
        "mismatch": False,
        "reason": "State checkpoint query",
    }
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    return result


def _iss_base():
    """Shared ISS diagnostics loading — read-only."""
    records = load_iss_diagnostics(20)
    probes = [r for r in records if r.get("type") == "iss_probe_result"]
    gaps = [r for r in records if r.get("type") == "iss_gap_signal"]
    return records, probes, gaps


def _iss_mode(result: dict) -> dict:
    """Attach mode_analysis and suggestion surface to an ISS response."""
    result["mode_analysis"] = {
        "current_mode": None,
        "suggested_mode": "observe",
        "match": True,
        "mismatch": False,
        "reason": "ISS diagnostics query",
    }
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    return result


def handle_iss_query_all(message: str, lowered: str) -> dict:
    """ISS full diagnostics query — read-only."""
    records, probes, gaps = _iss_base()
    ok_count = sum(1 for p in probes if p.get("status") == "ok")
    deg_count = sum(1 for p in probes if p.get("status") == "degraded")
    response_text = (
        f"Diagnostics: Probes: {ok_count} ok, {deg_count} degraded. Gaps: {len(gaps)} total"
    )
    result = build_deterministic_response(
        message=message,
        path="ISS_query_all",
        response_text=response_text,
        payload={"diagnostics": records},
        confidence="high",
        suggested_mode="observe",
    )
    return _iss_mode(result)


def handle_iss_query_gaps(message: str, lowered: str) -> dict:
    """ISS gap signals query — read-only."""
    records, probes, gaps = _iss_base()
    response_text = (
        f"Gaps: {len(gaps)} " + ", ".join(
            f"[{g.get('severity')}] {g.get('summary', '')[:60]}" for g in gaps[-5:]
        ) if gaps else "No gap signals recorded."
    )
    result = build_deterministic_response(
        message=message,
        path="ISS_query_gaps",
        response_text=response_text,
        payload={"gaps": gaps[-5:]},
        confidence="high",
        suggested_mode="observe",
    )
    return _iss_mode(result)


def handle_iss_query_probes(message: str, lowered: str) -> dict:
    """ISS probe results query — read-only."""
    records, probes, gaps = _iss_base()
    response_text = (
        f"Probe results: {len(probes)} " + ", ".join(
            f"[{p.get('status')}] {p.get('target', '')[:60]} ({p.get('confidence')})"
            for p in probes[-5:]
        ) if probes else "No probe results recorded."
    )
    result = build_deterministic_response(
        message=message,
        path="ISS_query_probes",
        response_text=response_text,
        payload={"probes": probes[-5:]},
        confidence="high",
        suggested_mode="observe",
    )
    return _iss_mode(result)


def handle_plan_explanation(message: str, lowered: str) -> dict:
    """Plan explanation — read-only. Explains why a plan exists."""
    _triggers = ["why does plan ", "explain plan ", "why was plan "]
    for t in _triggers:
        if lowered.startswith(t):
            raw = lowered[len(t):].strip().strip('"').strip("'")
            break
    for suffix in [" exist", " created", "?", " exist?", " created?"]:
        if raw.endswith(suffix):
            raw = raw[:-len(suffix)].strip()
    proposal_id = raw

    if not proposal_id:
        return build_deterministic_response(
            message=message,
            path="plan_explanation",
            response_text="No proposal ID provided.",
            confidence="high",
            suggested_mode="observe",
            payload={"plan_explanation": {"proposal_id": "", "plan_found": False}},
        )

    plans = []
    trace = []
    diagnostics = []
    try:
        plans = load_implementation_plans(100)
    except Exception:
        pass
    try:
        trace = load_trace(200)
    except Exception:
        pass
    try:
        diagnostics = load_iss_diagnostics(100)
    except Exception:
        pass

    matched_plans = [p for p in plans if p.get("proposal_id") == proposal_id]
    plan = matched_plans[-1] if matched_plans else None

    if not plan:
        return build_deterministic_response(
            message=message,
            path="plan_explanation",
            response_text="No implementation plan found for '" + proposal_id + "'.",
            confidence="high",
            suggested_mode="observe",
            payload={"plan_explanation": {"proposal_id": proposal_id, "plan_found": False}},
        )

    created_records = [r for r in trace if r.get("proposal_id") == proposal_id and r.get("type") == "proposal_created"]
    decision_records = [r for r in trace if r.get("proposal_id") == proposal_id and r.get("type") == "proposal_decision"]
    proposal_created_count = len(created_records)
    decision_count = len(decision_records)
    latest_decision = decision_records[-1]["decision"] if decision_records else "unknown"

    source_gap_ids = []
    for r in created_records:
        gap_id = r.get("content", {}).get("source_gap_id", "")
        if gap_id and gap_id not in source_gap_ids:
            source_gap_ids.append(gap_id)

    iss_gaps = [d for d in diagnostics if d.get("type") == "iss_gap_signal"]
    iss_related_gaps = []
    for g in iss_gaps:
        gid = g.get("gap_id", "")
        if any(gid == sg or gid.endswith(sg) or sg.endswith(gid) for sg in source_gap_ids):
            iss_related_gaps.append({"gap_id": gid, "summary": g.get("summary", ""), "severity": g.get("severity", "")})
        elif proposal_id in (g.get("summary", "") or ""):
            iss_related_gaps.append({"gap_id": gid, "summary": g.get("summary", ""), "severity": g.get("severity", "")})

    plan_explanation = {
        "proposal_id": proposal_id,
        "plan_found": True,
        "plan_id": plan.get("plan_id", ""),
        "plan_status": plan.get("status", ""),
        "execution_allowed": plan.get("execution_allowed", False),
        "operator_approval_required": plan.get("operator_approval_required", True),
        "proposal_created_count": proposal_created_count,
        "decision_count": decision_count,
        "latest_decision": latest_decision,
        "source_gap_ids": source_gap_ids,
        "iss_related_gaps": iss_related_gaps,
    }

    if source_gap_ids:
        response_text = (
            "Plan '" + plan.get("plan_id", "") + "' exists because proposal '" + proposal_id + "' "
            + "was created from ISS gap '" + str(source_gap_ids[0]) + "' and later accepted by the operator. "
            + "The plan is non-executing: execution_allowed=" + str(plan.get("execution_allowed", False)) + ", "
            + "operator_approval_required=" + str(plan.get("operator_approval_required", True)) + "."
        )
    else:
        response_text = (
            "Plan '" + plan.get("plan_id", "") + "' exists because proposal '" + proposal_id + "' "
            + "was accepted by the operator. No ISS source gap is linked. "
            + "The plan is non-executing: execution_allowed=" + str(plan.get("execution_allowed", False)) + ", "
            + "operator_approval_required=" + str(plan.get("operator_approval_required", True)) + "."
        )

    return build_deterministic_response(
        message=message,
        path="plan_explanation",
        response_text=response_text,
        payload={"plan_explanation": plan_explanation},
        confidence="high",
        suggested_mode="observe",
    )


# ---- Registry ----

HANDLER_REGISTRY = [
    {
        "id": "iss_probe_plan",
        "path": "ISS_probe_plan",
        "triggers": ["plan probe ", "how would you check "],
        "match_type": "prefix",
        "priority": 85,
        "handler_fn": "handle_iss_probe_plan",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
    {
        "id": "iss_probe_registry_query",
        "path": "ISS_probe_registry_query",
        "triggers": [
            "show iss probes",
            "show probe registry",
            "list probes",
            "what can iss check",
        ],
        "match_type": "prefix",
        "priority": 80,
        "handler_fn": "handle_iss_probe_registry",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
    {
        "id": "operator_overview",
        "path": "operator_overview",
        "triggers": [
            "show system overview",
            "weslr overview",
            "system overview",
            "show full status",
        ],
        "match_type": "prefix",
        "priority": 75,
        "handler_fn": "handle_operator_overview",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "operator",
    },
    {
        "id": "state_checkpoint_query",
        "path": "state_checkpoint_query",
        "triggers": [
            "show weslr status",
            "show architecture status",
            "show state checkpoint",
            "weslr checkpoint",
            "system checkpoint",
        ],
        "match_type": "prefix",
        "priority": 74,
        "handler_fn": "handle_state_checkpoint",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "operator",
    },
    {
        "id": "iss_query_all",
        "path": "ISS_query_all",
        "triggers": [
            "show diagnostics",
            "show iss diagnostics",
            "list diagnostics",
        ],
        "match_type": "prefix",
        "priority": 70,
        "handler_fn": "handle_iss_query_all",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
    {
        "id": "iss_query_gaps",
        "path": "ISS_query_gaps",
        "triggers": ["show gaps"],
        "match_type": "prefix",
        "priority": 69,
        "handler_fn": "handle_iss_query_gaps",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
    {
        "id": "iss_query_probes",
        "path": "ISS_query_probes",
        "triggers": ["show probe results"],
        "match_type": "prefix",
        "priority": 68,
        "handler_fn": "handle_iss_query_probes",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "iss",
    },
    {
        "id": "plan_explanation",
        "path": "plan_explanation",
        "triggers": ["why does plan ", "explain plan ", "why was plan "],
        "match_type": "prefix",
        "priority": 73,
        "handler_fn": "handle_plan_explanation",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "category": "explanation",
    },
]


# ---- Dispatch ----

def dispatch_deterministic_handler(message: str, lowered: str) -> Optional[dict]:
    """
    Sort registry by priority descending, try prefix match, return handler result.
    Returns None if no trigger matches.
    """
    sorted_handlers = sorted(HANDLER_REGISTRY, key=lambda h: h["priority"], reverse=True)
    for entry in sorted_handlers:
        for trigger in entry["triggers"]:
            if lowered.startswith(trigger):
                handler_fn_name = entry["handler_fn"]
                handler_fn = globals().get(handler_fn_name)
                if handler_fn is not None:
                    return handler_fn(message, lowered)
    return None
