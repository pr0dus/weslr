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
