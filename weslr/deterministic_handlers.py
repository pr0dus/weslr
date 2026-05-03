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
from weslr.reminder_handler import handle_reminder_command
from weslr.search_adapters.pubmed_adapter import search_pubmed
from weslr.search_adapters.evidence_packet_store import append_evidence_packet, load_packets, get_packet
from weslr.fact_extractor import extract_facts_with_positions, append_enriched_fact
from weslr.commands.entities import (
    entity_query,
    list_entity_types_cmd,
    list_entities_of_type,
    list_relationships_for_entity,
)


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


# ---- proposal_id normalizer (private helper, copied from interpretation.py) ----
_STOP_SUFFIXES = [" important", " important?", " high priority", " prioritized", " priority", "?"]

def _normalize_proposal_id(raw: str) -> str:
    value = raw.strip().strip('"').strip("'").strip()
    lowered = value.lower()
    for suffix in _STOP_SUFFIXES:
        if lowered.endswith(suffix):
            value = value[: -len(suffix)].strip()
            lowered = value.lower()
    return value


def handle_proposal_explanation(message: str, lowered: str) -> dict:
    """Proposal explanation — read-only. Explains why a proposal is important."""
    _triggers = ["why is ", "explain proposal ", "why prioritize "]
    for t in _triggers:
        if t in lowered:
            raw = lowered[lowered.index(t) + len(t):].strip().strip('"').strip("'")
            break
    proposal_id = _normalize_proposal_id(raw)

    if not proposal_id:
        result = build_deterministic_response(
            message=message,
            path="proposal_explanation",
            response_text="No proposal ID provided.",
            confidence="high",
            suggested_mode="observe",
        )
        result["mode_analysis"] = {"current_mode": None, "suggested_mode": "observe", "match": True, "mismatch": False, "reason": "Proposal explanation query"}
        result["mode_suggestion"] = None
        result["suggestion_surface"] = {"show": False, "priority": "low"}
        return result

    trace = load_trace(100)
    proposed_count = sum(1 for r in trace if r.get("proposal_id") == proposal_id and r.get("type") == "proposal_created")
    accepted_count = sum(1 for r in trace if r.get("proposal_id") == proposal_id and r.get("type") == "proposal_decision" and r.get("decision") == "accepted")
    rejected_count = sum(1 for r in trace if r.get("proposal_id") == proposal_id and r.get("type") == "proposal_decision" and r.get("decision") == "rejected")

    plans = load_implementation_plans(100)
    planned_count = sum(1 for p in plans if p.get("proposal_id") == proposal_id)

    iss_records = load_iss_diagnostics(50)
    related_gaps = [
        {"gap_id": g.get("gap_id"), "summary": g.get("summary"), "severity": g.get("severity")}
        for g in iss_records
        if g.get("type") == "iss_gap_signal" and (
            proposal_id in (g.get("gap_id") or "")
            or proposal_id in (g.get("summary") or "")
        )
    ]

    if accepted_count > 0 and planned_count > 0:
        priority_reasoning = f"Strong operator alignment: accepted {accepted_count} time(s), {planned_count} plan(s) exist. High priority."
    elif accepted_count > 0:
        priority_reasoning = f"Positive operator signal: accepted {accepted_count} time(s) but no plans yet. Consider planning."
    elif proposed_count > 2:
        priority_reasoning = f"Frequently proposed ({proposed_count} times) but not yet accepted. Needs operator review."
    elif proposed_count > 0:
        priority_reasoning = f"Proposed {proposed_count} time(s). No acceptance yet. Baseline priority."
    else:
        priority_reasoning = "No history found. Baseline priority based on proposal system."

    if related_gaps:
        priority_reasoning += f" {len(related_gaps)} related ISS gap(s) also detected."

    history = {"proposed": proposed_count, "accepted": accepted_count, "rejected": rejected_count, "planned": planned_count}

    parts = [f"Proposal '{proposal_id}' is important because:"]
    parts.append(f"- proposed {proposed_count} time(s)")
    if accepted_count:
        parts.append(f"- accepted {accepted_count} time(s)")
    if rejected_count:
        parts.append(f"- rejected {rejected_count} time(s)")
    if planned_count:
        parts.append(f"- planned {planned_count} time(s)")
    parts.append(f"- {len(related_gaps)} related ISS gap(s)")
    parts.append(f"\n{priority_reasoning}")
    response_text = "\n".join(parts)

    result = build_deterministic_response(
        message=message,
        path="proposal_explanation",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )
    result["mode_analysis"] = {"current_mode": None, "suggested_mode": "observe", "match": True, "mismatch": False, "reason": "Proposal explanation query"}
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    result["explanation"] = {
        "proposal_id": proposal_id,
        "history": history,
        "iss_related_gaps": related_gaps,
        "priority_reasoning": priority_reasoning,
    }
    return result


def handle_plan_query_list(message: str, lowered: str) -> dict:
    """Plan list query — read-only."""
    plans = load_implementation_plans(10)
    if plans:
        lines = [f"Found {len(plans)} implementation plan(s):"]
        for p in plans:
            lines.append(
                f"- {p.get('proposal_id')} ({p.get('status')}) "
                f"[exec={p.get('execution_allowed')}]"
            )
        response_text = "\n".join(lines)
    else:
        response_text = "No implementation plans found."
    result = build_deterministic_response(
        message=message,
        path="C8_plan_query_list",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )
    result["mode_analysis"] = {"current_mode": None, "suggested_mode": "observe", "match": True, "mismatch": False, "reason": "Implementation plan list query"}
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    result["plans"] = plans
    return result


def handle_plan_query_single(message: str, lowered: str) -> dict:
    """Single plan query — read-only."""
    parts = lowered.split(" for ") if " for " in lowered else lowered.split(" plan ")
    target_id = parts[-1].strip().strip('"').strip("'")
    plans = load_implementation_plans(50)
    matched = [p for p in plans if p.get("proposal_id") == target_id]
    if matched:
        plan = matched[-1]
        steps_str = " → ".join(
            s["title"].split(" ", 1)[1] if " " in s["title"] else s["title"]
            for s in plan.get("steps", []) if s.get("allowed")
        )
        response_text = (
            f"Plan for {target_id}: Steps: {steps_str}. Status: {plan.get('status')}. "
            f"Execution allowed: {plan.get('execution_allowed')}. "
            f"Operator approval required: {plan.get('operator_approval_required')}. "
            f"Plan ID: {plan.get('plan_id')}"
        )
    else:
        response_text = f"No plan found for '{target_id}'."
    result = build_deterministic_response(
        message=message,
        path="C8_plan_query_single",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )
    result["mode_analysis"] = {"current_mode": None, "suggested_mode": "observe", "match": True, "mismatch": False, "reason": "Implementation plan query"}
    result["mode_suggestion"] = None
    result["suggestion_surface"] = {"show": False, "priority": "low"}
    if matched:
        result["plan"] = plan
    return result


def handle_system_definition_query(message: str, lowered: str) -> dict:
    """WESLR system definition — read-only."""
    response_text = (
        "WESLR is a Continuity Intelligence System — not a chatbot, but a system that observes, "
        "reasons, and evolves through structure. It answers using deterministic system knowledge, "
        "tracks capabilities and gaps over time, and evolves through governed learning rather than "
        "uncontrolled AI behavior."
    )
    return build_deterministic_response(
        message=message,
        path="system_definition_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_origin_query(message: str, lowered: str) -> dict:
    """WESLR origin — read-only."""
    response_text = (
        "WESLR was created to demonstrate how intelligent systems can evolve safely — without "
        "uncontrolled self-modification or data collection. It's a testbed for governed learning, "
        "where humans remain in control while the system improves through structured observation."
    )
    return build_deterministic_response(
        message=message,
        path="origin_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_comparison_query(message: str, lowered: str) -> dict:
    """WESLR vs. other AI — read-only."""
    response_text = (
        "WESLR doesn't use LLMs for conversational responses in this demo — it uses deterministic "
        "system logic. It doesn't generate answers from training data; it answers from registered "
        "system knowledge and tracked state. The goal is less guessing, more continuity, and no "
        "uncontrolled self-modification."
    )
    return build_deterministic_response(
        message=message,
        path="comparison_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_continuity_explanation(message: str, lowered: str) -> dict:
    """Why continuity matters — read-only."""
    response_text = (
        "Continuity matters because intelligence requires consistency over time. WESLR tracks state, "
        "capabilities, gaps, proposals, and plans across sessions so progress is not lost between "
        "restarts. This allows governed evolution — improvements are built on previous state instead "
        "of isolated prompts."
    )
    return build_deterministic_response(
        message=message,
        path="continuity_explanation",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_improvement_query(message: str, lowered: str) -> dict:
    """How WESLR improves — read-only."""
    response_text = (
        "WESLR improves through governed evolution: gaps are observed, proposals are created, "
        "decisions are recorded, and implementation plans are linked. There is no uncontrolled "
        "self-improvement. Every meaningful change must be reviewed, approved, and traceable."
    )
    return build_deterministic_response(
        message=message,
        path="improvement_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_usage_guidance(message: str, lowered: str) -> dict:
    """Usage guidance — read-only."""
    response_text = (
        "Try these system queries:\n"
        "- show system overview\n"
        "- show diagnostics\n"
        "- show weslr status\n"
        "- show iss probes\n"
        "- show implementation plans\n"
        "- explain plan iss.not_integrated\n"
        "- explain proposal iss.not_integrated"
    )
    return build_deterministic_response(
        message=message,
        path="usage_guidance",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_agi_clarification(message: str, lowered: str) -> dict:
    """AGI clarification — read-only."""
    response_text = (
        "No — WESLR is not AGI. It is a governed, deterministic continuity system that uses "
        "structured state and explicit rules. The goal is safe, observable behavior, not "
        "uncontrolled general intelligence."
    )
    return build_deterministic_response(
        message=message,
        path="agi_clarification",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_self_improvement_clarification(message: str, lowered: str) -> dict:
    """Self-improvement clarification — read-only."""
    response_text = (
        "WESLR is not self-improving in the uncontrolled sense. It can evolve only through governed "
        "processes: gaps, proposals, decisions, plans, approval, and traceable implementation. "
        "There is no autonomous self-modification."
    )
    return build_deterministic_response(
        message=message,
        path="self_improvement_clarification",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_learning_clarification(message: str, lowered: str) -> dict:
    """Learning boundary clarification — read-only."""
    response_text = (
        "WESLR does not directly learn from public users. Public interaction may produce anonymous "
        "operational signals, but it cannot create memories, change behavior, or mutate capabilities. "
        "WESLR learns from observed patterns only under governance and operator approval."
    )
    return build_deterministic_response(
        message=message,
        path="learning_clarification",
        response_text=response_text,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
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
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "explanation",
    },
    {
        "id": "proposal_explanation",
        "path": "proposal_explanation",
        "triggers": ["why is ", "explain proposal ", "why prioritize "],
        "match_type": "prefix",
        "priority": 72,
        "handler_fn": "handle_proposal_explanation",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "explanation",
    },
    {
        "id": "plan_query_list",
        "path": "C8_plan_query_list",
        "triggers": ["show implementation plans", "list plans", "show plans"],
        "match_type": "prefix",
        "priority": 70,
        "handler_fn": "handle_plan_query_list",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "plan",
    },
    {
        "id": "plan_query_single",
        "path": "C8_plan_query_single",
        "triggers": ["show plan for ", "get plan for "],
        "match_type": "prefix",
        "priority": 71,
        "handler_fn": "handle_plan_query_single",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "plan",
    },
    {
        "id": "iss_intake_query",
        "path": "ISS_intake_query",
        "triggers": ["show iss intake proposals", "show proposals from iss", "show converted iss proposals", "list iss proposals"],
        "match_type": "prefix",
        "priority": 67,
        "handler_fn": "handle_iss_intake_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "iss",
    },
    {
        "id": "system_definition_query",
        "path": "system_definition_query",
        "triggers": ["what is weslr", "what is WESLR"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_system_definition_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "origin_query",
        "path": "origin_query",
        "triggers": ["why was weslr created", "why did you create weslr", "why was WESLR created"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_origin_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "comparison_query",
        "path": "comparison_query",
        "triggers": ["how is weslr different from", "how is WESLR different from"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_comparison_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "continuity_explanation",
        "path": "continuity_explanation",
        "triggers": ["why continuity matters", "why does continuity matter", "why is continuity important"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_continuity_explanation",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "improvement_query",
        "path": "improvement_query",
        "triggers": ["how does weslr improve", "how is weslr improved", "how does weslr evolve", "how does WESLR improve", "how is WESLR improved", "how does WESLR evolve"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_improvement_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "next_step_query",
        "path": "next_step",
        "triggers": [
            "what should i try next",
            "what should i do next",
        ],
        "match_type": "prefix",
        "priority": 57,
        "handler_fn": "handle_next_step_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "usage_guidance",
        "path": "usage_guidance",
        "triggers": [
            "what can i try",
            "what can i ask",
            "show me what to try",
            "what can you do",
            "what can you do?",
        ],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_usage_guidance",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "agi_clarification",
        "path": "agi_clarification",
        "triggers": ["is this agi", "is weslr agi", "is WESLR agi"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_agi_clarification",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "self_improvement_clarification",
        "path": "self_improvement_clarification",
        "triggers": ["is weslr self-improving", "can weslr improve itself", "is WESLR self-improving", "can WESLR improve itself"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_self_improvement_clarification",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "learning_clarification",
        "path": "learning_clarification",
        "triggers": ["can weslr learn from users", "does weslr learn from me", "can WESLR learn from users", "does WESLR learn from me"],
        "match_type": "prefix",
        "priority": 65,
        "handler_fn": "handle_learning_clarification",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "self_identity_query",
        "path": "self_identity",
        "triggers": ["what are you", "who are you", "what is this", "what can you do"],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_self_identity_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "self",
    },
    {
        "id": "capability_help_query",
        "path": "capability_help",
        "triggers": [
            "what can you help me with",
            "what can i ask you",
            "what can i do",
        ],
        "match_type": "prefix",
        "priority": 58,
        "handler_fn": "handle_capability_help_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "guided_chat",
    },
    {
        "id": "improvement_explanation_query",
        "path": "improvement_explanation",
        "triggers": [
            "how do you improve",
            "how do you improve over time",
            "how do you learn",
            "how do you get better",
            "i want to understand how you improve",
            "i want to understand how you improve over time",
            "want to understand how you improve",
            "want to understand how you improve over time",
            "understand how you improve",
            "understand how you improve over time",
            "explain how you improve",
            "explain how you improve over time",
        ],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_improvement_explanation_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "explanation",
    },
    {
        "id": "uncertainty_explanation_query",
        "path": "uncertainty_explanation",
        "triggers": [
            "what happens if you do not know something",
            "what happens if you don't know",
            "what if you do not know",
            "what if you don't know",
        ],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_uncertainty_explanation_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "boundary",
    },
    {
        "id": "memory_boundary_query",
        "path": "memory_boundary",
        "triggers": [
            "can you remember what we talked about earlier",
            "do you remember what we talked about",
            "can you remember this conversation",
        ],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_memory_boundary_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "boundary",
    },
    {
        "id": "simple_followup_query",
        "path": "simple_followup",
        "triggers": [
            "can you explain that more simply",
            "say that simpler",
            "make it simpler",
        ],
        "match_type": "prefix",
        "priority": 55,
        "handler_fn": "handle_simple_followup_query",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "simplification",
    },
    {
        "id": "reminder_command",
        "path": "reminder_command",
        "triggers": [
            "remind me ",
            "show my reminders",
            "cancel reminder ",
        ],
        "match_type": "prefix",
        "priority": 88,
        "handler_fn": "handle_reminder_command",
        "read_only": False,
        "writes": [".weslr/reminders.jsonl", ".weslr/reminder_events.jsonl", ".weslr/pending_messages.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/reminders.jsonl", ".weslr/reminder_events.jsonl", ".weslr/pending_messages.jsonl"],
        "side_effects": ["threading.Timer scheduled for reminder firing"],
        "write_guard": None,
        "category": "reminder",
    },
    {
        "id": "entity_query",
        "path": "entity_query",
        "triggers": ["/entity ", "entity ", "/entity[", "entity["],
        "match_type": "prefix",
        "priority": 75,
        "handler_fn": "handle_entity",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "entity",
    },
    {
        "id": "entity_list",
        "path": "entity_list",
        "triggers": ["/entities", "entities", "/entities type", "/entities relationship"],
        "match_type": "prefix",
        "priority": 75,
        "handler_fn": "handle_entities",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "entity",
    },
    {
        "id": "pubmed_search",
        "path": "pubmed_search",
        "triggers": ["search pubmed ", "pubmed search "],
        "match_type": "prefix",
        "priority": 90,
        "handler_fn": "handle_pubmed_search",
        "read_only": True,
        "writes": [".weslr/external_evidence_packets.jsonl", ".weslr/fact_assertions.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/external_evidence_packets.jsonl", ".weslr/fact_assertions.jsonl"],
        "side_effects": ["writes external_evidence_packets.jsonl", "appends facts to fact_assertions.jsonl"],
        "write_guard": None,
        "category": "pubmed",
    },
]


def handle_iss_intake_query(message: str, lowered: str) -> dict:
    """ISS intake proposal query — read-only."""
    try:
        trace = load_trace(100)
    except Exception:
        trace = []
    iss_intake_proposals = [
        {
            "proposal_id": r.get("proposal_id"),
            "source_gap_id": r.get("content", {}).get("source_gap_id", ""),
            "summary": r.get("content", {}).get("summary", ""),
            "severity": r.get("content", {}).get("severity", ""),
            "timestamp": r.get("timestamp"),
        }
        for r in trace
        if r.get("type") == "proposal_created"
        and r.get("content", {}).get("source") == "ISS"
        and r.get("content", {}).get("operator_requested_intake") is True
    ]
    iss_intake_grouped = []
    if not iss_intake_proposals:
        response_text = "No ISS intake proposals found."
    else:
        grouped = {}
        for p in iss_intake_proposals:
            pid = p["proposal_id"]
            ts = p.get("timestamp")
            if pid not in grouped:
                grouped[pid] = {
                    "proposal_id": pid,
                    "source_gap_id": p["source_gap_id"],
                    "summary": p["summary"],
                    "severity": p["severity"],
                    "confidence": p.get("confidence", ""),
                    "count": 0,
                    "first_seen": ts,
                    "last_seen": ts,
                }
            grouped[pid]["count"] += 1
            if ts is not None:
                if grouped[pid]["first_seen"] is None or ts < grouped[pid]["first_seen"]:
                    grouped[pid]["first_seen"] = ts
                if ts > grouped[pid]["last_seen"]:
                    grouped[pid]["last_seen"] = ts
        iss_intake_grouped = list(grouped.values())
        total_events = len(iss_intake_proposals)
        lines = [f"Found {len(iss_intake_grouped)} unique ISS intake proposal(s) from {total_events} trace event(s):"]
        for g in iss_intake_grouped:
            lines.append(
                f"- {g['proposal_id']} from {g['source_gap_id']} "
                f"({g['severity']}), seen {g['count']} time(s)"
            )
        response_text = "\n".join(lines)
    result = build_deterministic_response(
        message=message,
        path="ISS_intake_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )
    result["iss_intake_proposals"] = iss_intake_proposals
    result["iss_intake_grouped"] = iss_intake_grouped
    result["iss_intake_count"] = len(iss_intake_proposals)
    result["iss_intake_unique_count"] = len(iss_intake_grouped)
    return result


# ---- Natural self-conversation handlers ----

def handle_self_identity_query(message: str, lowered: str) -> dict:
    """Self identity — explain WESLR briefly as continuity-first system."""
    response_text = (
        "I am WESLR — a deterministic continuity system that tracks your interests, "
        "observes patterns over time, and helps you explore topics with evidence. "
        "I don't learn from public users, I don't act autonomously, and I don't claim AGI. "
        "My goal is safe, observable behavior under operator control."
    )
    return build_deterministic_response(
        message=message,
        path="self_identity",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_capability_help_query(message: str, lowered: str) -> dict:
    """Capability help — useful examples in natural language."""
    response_text = (
        "I can help you explore topics with evidence, track your interests, "
        "review diagnostic gaps, understand implementation plans, and surface "
        "consistent patterns across sessions. Try asking about system status, "
        "diagnostics, or specific topics you want to investigate. "
        "I can also explain my boundaries and limitations if you're curious."
    )
    return build_deterministic_response(
        message=message,
        path="capability_help",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_improvement_explanation_query(message: str, lowered: str) -> dict:
    """Improvement explanation — explain observation→patterns→review→improvement."""
    response_text = (
        "I improve by observing patterns across sessions, reviewing diagnostic gaps, "
        "and evolving under operator guidance. This happens through ISS (ISS Signal System) "
        "which tracks patterns, proposes improvements, and requires operator approval "
        "before any changes. There's no autonomous learning — only governed evolution."
    )
    return build_deterministic_response(
        message=message,
        path="improvement_explanation",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_uncertainty_explanation_query(message: str, lowered: str) -> dict:
    """Uncertainty explanation — explain boundary when WESLR doesn't know."""
    response_text = (
        "If I don't know something or can't find relevant evidence, I'll tell you "
        "I'm uncertain and keep unverified things separate from established knowledge. "
        "This boundary helps ensure reliability — I'd rather say 'I don't know' than "
        "make unverified claims. You can help by providing specific context or evidence."
    )
    return build_deterministic_response(
        message=message,
        path="uncertainty_explanation",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_memory_boundary_query(message: str, lowered: str) -> dict:
    """Memory boundary — honest explanation of current staging capabilities."""
    response_text = (
        "Current staging preserves session metadata and operational signals for "
        "pattern observation, but it doesn't store full conversational history "
        "like human memory. I can track interests and patterns over time, but "
        "specific conversation details aren't retained between sessions. "
        "This is intentional — privacy-first design."
    )
    return build_deterministic_response(
        message=message,
        path="memory_boundary",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_next_step_query(message: str, lowered: str) -> dict:
    """Next step suggestions — helpful next moves for new users."""
    response_text = (
        "Here are some things you can try:\n"
        "- ask what WESLR is\n"
        "- ask what WESLR can do\n"
        "- ask how WESLR improves over time\n"
        "- ask what happens when WESLR is unsure\n"
        "- ask for a simple explanation of a topic"
    )
    return build_deterministic_response(
        message=message,
        path="next_step",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_simple_followup_query(message: str, lowered: str) -> dict:
    """Simple followup — honest no-context boundary in staging."""
    response_text = (
        "I can simplify, but I need the topic again because this staging surface "
        "does not yet use full conversational context. Please tell me what you "
        "want simplified, and I'll give you a clear, concise explanation."
    )
    return build_deterministic_response(
        message=message,
        path="simple_followup",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_pubmed_search(message: str, lowered: str) -> dict:
    """PubMed literature search — writes evidence packet + extracts facts."""
    import re
    import uuid
    from datetime import datetime, timezone

    # Extract query: "search pubmed <query>" or "pubmed search <query>"
    m = re.match(r"(?:search\s+)?pubmed\s+(?:search\s+)?(.+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="pubmed_search",
            response_text="Usage: /search pubmed <query> (e.g., 'BRCA1 breast cancer survival')",
            confidence="high",
            suggested_mode="observe",
        )
    query = m.group(1).strip()
    if not query:
        return build_deterministic_response(
            message=message,
            path="pubmed_search",
            response_text="Usage: /search pubmed <query> — please provide a search query.",
            confidence="high",
            suggested_mode="observe",
        )

    # Run search
    try:
        pmids, articles = search_pubmed(query, max_results=10)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="pubmed_search",
            response_text=f"PubMed search failed: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if not articles:
        return build_deterministic_response(
            message=message,
            path="pubmed_search",
            response_text=f"PubMed returned no results for '{query}'.",
            confidence="high",
            suggested_mode="observe",
        )

    # Build and store evidence packet
    packet_id = f"pm_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:6]}"
    packet = {
        "record_type": "external_evidence_packet_v1",
        "packet_id": packet_id,
        "source": "pubmed",
        "query": query,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "result_count": len(articles),
        "results": articles,
        "authority": "external_evidence_unverified",
        "automatic_change": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }
    append_evidence_packet(packet)


    # Extract facts from each abstract (synchronous for V1)
    fact_count = 0
    BASE_TRUST = 0.70  # PubMed abstract base trust
    for article in articles:
        abstract = article.get("abstract", "") or ""
        if not abstract:
            continue
        pmid = article.get("pmid", "")
        title = article.get("title", "") or ""
        journal = article.get("journal", "") or ""
        year = article.get("year", "") or ""
        authors = article.get("authors", []) or []
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        citation = f"{author_str} ({year}). {title}. {journal}." if title else ""


        raw_facts = extract_facts_with_positions(
            text=abstract,
            page=1,
            line_start=0,
            domain="cancer_research",
        )
        for fact in raw_facts:
            cs = fact.get("char_start", 0)
            ce = fact.get("char_end", 0)
            line_start = abstract[:cs].count("\n") + 1
            line_end = abstract[:ce].count("\n") + 1

            enriched = {
                "record_type": "fact_assertion_v1",
                "subject": fact["subject"],
                "predicate": fact["predicate"],
                "object": fact["object"],
                "source_event_ref": f"pubmed:{pmid}",
                "source_doc_id": None,
                "source_reference": {
                    "type": "pubmed_abstract",
                    "pmid": pmid,
                    "citation": citation,
                    "page": 1,
                    "line_range": [line_start, line_end],
                },
                "source_type": "pubmed_abstract",
                "trust_score": round(BASE_TRUST * fact["confidence"], 3),
                "domains": ["cancer_research"],
                "extraction_pattern": fact.get("pattern_id", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "authority": "extracted_from_pubmed",
                "automatic_action": False,
                "hidden_learning": False,
                "raw_prompt_stored": False,
                "fact_data": fact.get("fact_data", {}),
            }
            # Append via fact_extractor helper
            append_enriched_fact(enriched)
            fact_count += 1

    # Build response
    top = articles[0]
    top_authors = ", ".join(top.get("authors", [])[:2])
    if len(top.get("authors", [])) > 2:
        top_authors += " et al."
    response_text = (
        f"PubMed search for '{query}' returned {len(articles)} results. "
        f"Evidence packet {packet_id} stored. "
        f"{fact_count} facts extracted from abstracts.\n\n"
        f"Top result: {top.get('title', 'N/A')}\n"
        f"  Authors: {top_authors} ({top.get('year', 'N/A')})\n"
        f"  Journal: {top.get('journal', 'N/A')}\n"
        f"  PMID: {top.get('pmid', 'N/A')} — {top.get('url', 'N/A')}\n"
    )
    return build_deterministic_response(
        message=message,
        path="pubmed_search",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- Entity Query Handlers ----

def handle_entity(message: str, lowered: str) -> dict:
    """Handle /entity <name> — show entity summary."""
    # Extract entity name: "/entity <name>" or "entity <name>"
    entity_name = lowered
    for prefix in ("/entity ", "entity ", "/entity[", "entity["):
        if lowered.startswith(prefix):
            entity_name = lowered[len(prefix):].strip()
            break

    if not entity_name:
        return build_deterministic_response(
            message=message,
            path="entity_query",
            response_text="Usage: /entity <name>  (e.g., /entity NCT04551452)",
            confidence="high",
            suggested_mode="observe",
        )

    response_text = entity_query(entity_name)
    return build_deterministic_response(
        message=message,
        path="entity_query",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_entities(message: str, lowered: str) -> dict:
    """Handle /entities or /entities type <type> or /entities relationship <rel>."""
    # "entities type ClinicalTrial" or "entities type <type>"
    if " type " in lowered or lowered.startswith("type "):
        # Extract type name
        parts = lowered.split(" type ", 1)
        entity_type = parts[1].strip() if len(parts) > 1 else ""
        response_text = list_entities_of_type(entity_type)
    elif " relationship " in lowered or lowered.startswith("relationship "):
        # Extract relationship type
        parts = lowered.split(" relationship ", 1)
        rel_type = parts[1].strip() if len(parts) > 1 else ""
        response_text = list_relationships_for_entity(rel_type)
    else:
        # List all entity types
        response_text = list_entity_types_cmd()

    return build_deterministic_response(
        message=message,
        path="entity_list",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


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
