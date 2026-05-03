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
from weslr.commands.propose import handle_propose_pv_material
from weslr.commands.discover import handle_discover
from weslr.nanotechnology_discovery import handle_propose_nanotechnology
from weslr.communications_discovery import handle_propose_communication
from weslr.combinatorial_materials import handle_propose_combination
from weslr.combinatorial_chemistry import handle_propose_chemistry
from weslr.chemistry_reaction_predictor import handle_predict_reaction as handle_reaction_predict
from weslr.commands.temporal_commands import handle_temporal_command
from weslr.commands.spatial_commands import handle_molecule_command

import re


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
    {
        "id": "arxiv_search",
        "path": "arxiv_search",
        "triggers": ["search arxiv ", "arxiv ", "/search arxiv ", "/arxiv "],
        "match_type": "prefix",
        "priority": 90,
        "handler_fn": "handle_arxiv_search",
        "read_only": True,
        "writes": [".weslr/external_evidence_packets.jsonl", ".weslr/fact_assertions.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/external_evidence_packets.jsonl", ".weslr/fact_assertions.jsonl"],
        "side_effects": ["writes external_evidence_packets.jsonl", "appends facts to fact_assertions.jsonl"],
        "write_guard": None,
        "category": "arxiv",
    },
    {
        "id": "pubchem_search",
        "path": "pubchem_search",
        "triggers": ["/search pubchem ", "/pubchem "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_search_pubchem",
        "read_only": True,
        "writes": [".weslr/fact_assertions.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/fact_assertions.jsonl"],
        "side_effects": ["appends compound facts to fact_assertions.jsonl"],
        "write_guard": None,
        "category": "pubchem",
    },
    {
        "id": "facts_after",
        "path": "facts_after",
        "triggers": ["facts about ", "/facts about ", "about "],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_facts_about_after",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "facts",
    },
    {
        "id": "facts_before",
        "path": "facts_before",
        "triggers": ["facts about "],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_facts_about_before",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "facts",
    },
    {
        "id": "facts_between",
        "path": "facts_between",
        "triggers": ["facts about "],
        "match_type": "prefix",
        "priority": 60,
        "handler_fn": "handle_facts_between",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "facts",
    },
    {
        "id": "explore",
        "path": "explore",
        "triggers": ["/explore "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_explore_cmd",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "explore",
    },
    {
        "id": "propose_combination",
        "path": "propose_combination",
        "triggers": ["/propose combination"],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_propose_combination",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "propose",
    },
    {
        "id": "propose_chemistry",
        "path": "propose_chemistry",
        "triggers": ["/propose chemistry", "/chemistry propose"],
        "match_type": "regex",
        "priority": 95,
        "handler_fn": "handle_propose_chemistry_cmd",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "propose",
    },
    {
        "id": "reaction_prediction",
        "path": "reaction_prediction",
        "triggers": ["/predict reaction ", "/reaction predict "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_reaction_predict_cmd",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "chemistry",
    },
    {
        "id": "action_propose",
        "path": "action_propose",
        "triggers": ["/propose "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_propose_action",
        "read_only": True,
        "writes": [".weslr/action_proposals.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/action_proposals.jsonl"],
        "side_effects": ["appends to action_proposals.jsonl"],
        "write_guard": None,
        "category": "actions",
    },
    {
        "id": "actions_list",
        "path": "actions_list",
        "triggers": ["/actions list"],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_actions_list",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "actions",
    },
    {
        "id": "actions_approve",
        "path": "actions_approve",
        "triggers": ["/actions approve "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_actions_approve",
        "read_only": False,
        "writes": [".weslr/action_proposals.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/action_proposals.jsonl"],
        "side_effects": ["appends status-change event to action_proposals.jsonl"],
        "write_guard": None,
        "category": "actions",
    },
    {
        "id": "actions_reject",
        "path": "actions_reject",
        "triggers": ["/actions reject "],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_actions_reject",
        "read_only": False,
        "writes": [".weslr/action_proposals.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/action_proposals.jsonl"],
        "side_effects": ["appends status-change event to action_proposals.jsonl"],
        "write_guard": None,
        "category": "actions",
    },
    {
        "id": "actions_run",
        "path": "actions_run",
        "triggers": ["/actions run"],
        "match_type": "prefix",
        "priority": 95,
        "handler_fn": "handle_actions_run",
        "read_only": True,
        "writes": [".weslr/action_runner_dry_run.jsonl"],
        "requires_confirmation": False,
        "write_paths": [".weslr/action_runner_dry_run.jsonl"],
        "side_effects": ["logs dry-run to action_runner_dry_run.jsonl"],
        "write_guard": None,
        "category": "actions",
    },
    {
        "id": "tenant_list",
        "path": "tenant_list",
        "triggers": ["/tenant list"],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_tenant_list",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "tenant",
    },
    {
        "id": "tenant_switch",
        "path": "tenant_switch",
        "triggers": ["/tenant switch "],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_tenant_switch",
        "read_only": False,
        "writes": ["tenants/<id>/tenant_config.json"],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": ["sets thread-local current tenant"],
        "write_guard": None,
        "category": "tenant",
    },
    {
        "id": "tenant_create",
        "path": "tenant_create",
        "triggers": ["/tenant create "],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_tenant_create",
        "read_only": False,
        "writes": ["tenants/<id>/tenant_config.json", "tenants/<id>/.weslr/"],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": ["creates tenant directory and config"],
        "write_guard": None,
        "category": "tenant",
    },
    {
        "id": "tenant_info",
        "path": "tenant_info",
        "triggers": ["/tenant info "],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_tenant_info",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "tenant",
    },
    {
        "id": "domains_list",
        "path": "domains_list",
        "triggers": ["/domains"],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_domains_list",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "metadata",
    },
    {
        "id": "propose_discover_with_domain",
        "path": "discover",
        "triggers": [r"^(?:/propose\s+discover|/discover)\s+(\w+)$"],
        "match_type": "regex",
        "priority": 97,
        "handler_fn": "handle_discover_cmd",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "propose",
    },
    {
        "id": "propose_discover_no_domain",
        "path": "discover",
        "triggers": [r"^(?:/propose\s+discover|/discover)$"],
        "match_type": "regex",
        "priority": 96,
        "handler_fn": "handle_discover_cmd",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "propose",
    },
    # ── Symbolic Mathematics ────────────────────────────────────────────────────
    {
        "id": "math_solve",
        "path": "math_solve",
        "triggers": ["/solve", "solve ", "math solve", "equation solve"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_solve",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_derivative",
        "path": "math_derivative",
        "triggers": ["/derivative", "derivative ", "d/d", "differentiate"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_derivative",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_integral",
        "path": "math_integral",
        "triggers": ["/integral", "integral ", "integrate", "∫"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_integral",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_simplify",
        "path": "math_simplify",
        "triggers": ["/simplify", "simplify ", "simplify("],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_simplify",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_evaluate",
        "path": "math_evaluate",
        "triggers": ["/evaluate", "evaluate "],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_evaluate",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_expand",
        "path": "math_expand",
        "triggers": ["/expand", "expand "],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_expand",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "math_optimal",
        "path": "math_optimal",
        "triggers": ["optimal ", "find optimal", "solve for optimal", "/optimal"],
        "match_type": "prefix",
        "priority": 45,
        "handler_fn": "handle_optimal",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "symbolic_math",
    },
    {
        "id": "ode_propose",
        "path": "ode_propose",
        "triggers": ["/ode propose", "ode propose"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_ode_propose",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "ode",
    },
    {
        "id": "ode_solve",
        "path": "ode_solve",
        "triggers": ["/ode solve", "ode solve"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_ode_solve",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "ode",
    },
    {
        "id": "ode_list",
        "path": "ode_list",
        "triggers": ["/ode list_templates", "/ode list", "ode list_templates", "ode list"],
        "match_type": "prefix",
        "priority": 50,
        "handler_fn": "handle_ode_list",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "ode",
    },
    {
        "id": "quantum",
        "path": "quantum",
        "triggers": ["/quantum", "quantum "],
        "match_type": "prefix",
        "priority": 55,
        "handler_fn": "handle_quantum",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "quantum",
    },
    {
        "id": "causal_propose",
        "path": "causal_propose",
        "triggers": ["/propose cause", "/refine cause", "/causal"],
        "match_type": "prefix",
        "priority": 56,
        "handler_fn": "handle_causal_propose",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "causality",
    },
    {
        "id": "temporal",
        "path": "temporal",
        "triggers": ["/timeseries", "/forecast", "/alert on forecast"],
        "match_type": "prefix",
        "priority": 56,
        "handler_fn": "handle_temporal",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "temporal",
    },
    {
        "id": "molecular_geometry",
        "path": "molecular_geometry",
        "triggers": ["/molecule", "molecule ", "/propose shape"],
        "match_type": "prefix",
        "priority": 56,
        "handler_fn": "handle_molecule",
        "read_only": True,
        "writes": [],
        "requires_confirmation": False,
        "write_paths": [],
        "side_effects": [],
        "write_guard": None,
        "category": "spatial",
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


# ---- arXiv Search Handler ----

def handle_arxiv_search(message: str, lowered: str) -> dict:
    """Handle /search arxiv <query> [--domain <domain>] — arXiv literature search."""
    import re

    # Extract query: "/search arxiv <query>" or "search arxiv <query>"
    m = re.match(r"(?:search\s+)?arxiv\s+(?:search\s+)?(.+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="arxiv_search",
            response_text="Usage: /search arxiv <query> (e.g., 'MAPbI3 perovskite stability')",
            confidence="high",
            suggested_mode="observe",
        )
    query = m.group(1).strip()

    # Extract optional --domain
    domain_match = re.search(r"--domain\s+(\S+)", m.group(0))
    domain = domain_match.group(1) if domain_match else None

    if not query:
        return build_deterministic_response(
            message=message,
            path="arxiv_search",
            response_text="Usage: /search arxiv <query> — please provide a search query.",
            confidence="high",
            suggested_mode="observe",
        )

    try:
        from weslr.search_adapters.arxiv_adapter import search_and_store, format_search_results
        result = search_and_store(query, max_results=10, domain=domain)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="arxiv_search",
            response_text=f"arXiv search failed: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    result_count = result.get("result_count", 0)
    fact_count = result.get("fact_count", 0)
    articles = result.get("articles", [])

    if result_count == 0:
        response_text = f"arXiv search for '{query}' returned no results."
    else:
        response_text = (
            f"arXiv search for '{query}' returned {result_count} results. "
            f"Evidence packet stored. {fact_count} facts extracted from abstracts.\n\n"
        )
        response_text += format_search_results(articles)

    return build_deterministic_response(
        message=message,
        path="arxiv_search",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- PubChem Search Handler ----

def handle_search_pubchem(message: str, lowered: str) -> dict:
    """Handle /search pubchem <query> or /pubchem <query> — compound property search."""
    import re
    from datetime import datetime, timezone

    m = re.match(r"^(?:/search\s+pubchem|/pubchem)\s+(.+)$", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="pubchem_search",
            response_text=(
                "Usage: /search pubchem <compound>  or  /pubchem <compound>\n"
                "  e.g., /search pubchem aspirin\n"
                "       /search pubchem CCO --smiles\n"
                "       /pubchem C6H12O6 --formula"
            ),
            confidence="high",
            suggested_mode="observe",
        )

    query = m.group(1).strip()
    search_type = "name"
    if query.endswith(" --smiles"):
        query = query[:-8].strip()
        search_type = "smiles"
    elif query.endswith(" --formula"):
        query = query[:-10].strip()
        search_type = "formula"

    if not query:
        return build_deterministic_response(
            message=message,
            path="pubchem_search",
            response_text="Please provide a compound name, SMILES, or formula.",
            confidence="high",
            suggested_mode="observe",
        )

    # Run search
    try:
        from weslr.search_adapters.pubchem_adapter import search_pubchem, format_compound_info, store_compound_fact
        result = search_pubchem(query, search_type=search_type)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="pubchem_search",
            response_text=f"PubChem search failed: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if result.get("error"):
        return build_deterministic_response(
            message=message,
            path="pubchem_search",
            response_text=f"PubChem error: {result['error']}",
            confidence="high",
            suggested_mode="observe",
        )

    # Format display
    display = format_compound_info(result)

    # Store fact
    try:
        store_compound_fact(result)
    except Exception:
        pass  # non-fatal; still show results

    # Build URL
    cid = result.get("cid", "")
    url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else ""

    response_text = (
        f"PubChem search for '{query}' (type={search_type}):\n\n"
        f"{display}\n\n"
        f"Source: {url}"
    )

    return build_deterministic_response(
        message=message,
        path="pubchem_search",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- Temporal Facts Handlers ----

def handle_facts_about_after(message: str, lowered: str) -> dict:
    """Handle /facts about <entity> after <year> — facts published after a given year."""
    import re

    # Pattern: /facts about <entity> after <year>
    m = re.match(
        r"(?:facts\s+about|about)\s+(\S[\w\s\-\.]*?)\s+after\s+(\d{4})",
        lowered
    )
    if not m:
        return build_deterministic_response(
            message=message,
            path="facts_after",
            response_text=(
                "Usage: /facts about <entity> after <year>\n"
                "  e.g., /facts about BRCA1 after 2020"
            ),
            confidence="high",
            suggested_mode="observe",
        )

    entity = m.group(1).strip()
    year = int(m.group(2))

    try:
        from weslr.fact_extractor import load_facts
        facts = load_facts(subject=entity, after_year=year, limit=50)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="facts_after",
            response_text=f"Error loading facts: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if not facts:
        response_text = f"No facts found for '{entity}' published after {year}."
    else:
        lines = [f"Facts about '{entity}' published after {year}: {len(facts)} total", ""]
        for f in facts[:20]:
            pred = f.get("predicate", "?")
            obj = f.get("object", "")[:60]
            yr = f.get("year", f.get("publication_year", "?"))
            lines.append(f"  [{pred}] {obj}  ({yr})")
        if len(facts) > 20:
            lines.append(f"  ... and {len(facts) - 20} more. Narrow your query or increase limit.")
        response_text = "\n".join(lines)

    return build_deterministic_response(
        message=message,
        path="facts_after",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_facts_about_before(message: str, lowered: str) -> dict:
    """Handle /facts about <entity> before <year> — facts published before a given year."""
    import re

    m = re.match(
        r"(?:facts\s+about|about)\s+(\S[\w\s\-\.]*?)\s+before\s+(\d{4})",
        lowered
    )
    if not m:
        return build_deterministic_response(
            message=message,
            path="facts_before",
            response_text=(
                "Usage: /facts about <entity> before <year>\n"
                "  e.g., /facts about NCT04551452 before 2015"
            ),
            confidence="high",
            suggested_mode="observe",
        )

    entity = m.group(1).strip()
    year = int(m.group(2))

    try:
        from weslr.fact_extractor import load_facts
        facts = load_facts(subject=entity, before_year=year, limit=50)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="facts_before",
            response_text=f"Error loading facts: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if not facts:
        response_text = f"No facts found for '{entity}' published before {year}."
    else:
        lines = [f"Facts about '{entity}' published before {year}: {len(facts)} total", ""]
        for f in facts[:20]:
            pred = f.get("predicate", "?")
            obj = f.get("object", "")[:60]
            yr = f.get("year", f.get("publication_year", "?"))
            lines.append(f"  [{pred}] {obj}  ({yr})")
        if len(facts) > 20:
            lines.append(f"  ... and {len(facts) - 20} more.")
        response_text = "\n".join(lines)

    return build_deterministic_response(
        message=message,
        path="facts_before",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_facts_between(message: str, lowered: str) -> dict:
    """Handle /facts about <entity> between <year1> and <year2>."""
    import re

    m = re.match(
        r"(?:facts\s+about|about)\s+(\S[\w\s\-\.]*?)\s+between\s+(\d{4})\s+and\s+(\d{4})",
        lowered
    )
    if not m:
        return build_deterministic_response(
            message=message,
            path="facts_between",
            response_text=(
                "Usage: /facts about <entity> between <year1> and <year2>\n"
                "  e.g., /facts about perovskite between 2018 and 2023"
            ),
            confidence="high",
            suggested_mode="observe",
        )

    entity = m.group(1).strip()
    year1 = int(m.group(2))
    year2 = int(m.group(3))

    if year1 >= year2:
        return build_deterministic_response(
            message=message,
            path="facts_between",
            response_text=f"Error: first year ({year1}) must be less than second year ({year2}).",
            confidence="high",
            suggested_mode="observe",
        )

    try:
        from weslr.fact_extractor import load_facts
        facts = load_facts(subject=entity, after_year=year1, before_year=year2, limit=50)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="facts_between",
            response_text=f"Error loading facts: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if not facts:
        response_text = f"No facts found for '{entity}' between {year1}–{year2}."
    else:
        lines = [f"Facts about '{entity}' ({year1}–{year2}): {len(facts)} total", ""]
        for f in facts[:20]:
            pred = f.get("predicate", "?")
            obj = f.get("object", "")[:60]
            yr = f.get("year", f.get("publication_year", "?"))
            lines.append(f"  [{pred}] {obj}  ({yr})")
        if len(facts) > 20:
            lines.append(f"  ... and {len(facts) - 20} more.")
        response_text = "\n".join(lines)

    return build_deterministic_response(
        message=message,
        path="facts_between",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_timeline(message: str, lowered: str) -> dict:
    """Handle /timeline <entity> — chronological list of facts about entity."""
    import re
    from collections import defaultdict

    # Pattern: /timeline <entity>
    m = re.match(r"(?:timeline)\s+(\S.+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="entity_timeline",
            response_text="Usage: /timeline <entity>  (e.g., /timeline MAPbI3)",
            confidence="high",
            suggested_mode="observe",
        )

    entity = m.group(1).strip()

    try:
        from weslr.fact_extractor import load_facts
        facts = load_facts(subject=entity, limit=200)
    except Exception as e:
        return build_deterministic_response(
            message=message,
            path="entity_timeline",
            response_text=f"Error loading facts: {e}",
            confidence="medium",
            suggested_mode="observe",
        )

    if not facts:
        # Also try object match
        facts = load_facts(obj=entity, limit=200)

    if not facts:
        response_text = f"No facts found for '{entity}'. Try searching PubMed or arXiv first."
        return build_deterministic_response(
            message=message,
            path="entity_timeline",
            response_text=response_text,
            confidence="high",
            suggested_mode="observe",
        )

    # Group by year
    by_year: Dict[int, List[Dict]] = defaultdict(list)
    for f in facts:
        yr = f.get("year", f.get("publication_year", 0))
        try:
            yr = int(yr)
        except (TypeError, ValueError):
            yr = 0
        by_year[yr].append(f)

    lines = [f"Timeline for '{entity}': {len(facts)} facts", ""]
    for yr in sorted(by_year.keys(), reverse=True):
        if yr == 0:
            label = "unknown year"
        else:
            label = str(yr)
        lines.append(f"━━ {label} ━━")
        for f in by_year[yr][:10]:
            pred = f.get("predicate", "?")
            obj = f.get("object", "")[:60]
            src = f.get("source_type", "?")
            lines.append(f"  [{pred}] {obj}  (src: {src})")
        if len(by_year[yr]) > 10:
            lines.append(f"  ... and {len(by_year[yr]) - 10} more")
        lines.append("")

    response_text = "\n".join(lines).rstrip()
    return build_deterministic_response(
        message=message,
        path="entity_timeline",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- Action Proposal Handlers ----

def handle_propose_action(message: str, lowered: str) -> dict:
    """Handle /propose <action_type> <description> — propose an external action."""
    import re

    # Pattern: /propose <action_type> <description>
    m = re.match(r"/propose\s+(\S+)\s+(.+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="action_propose",
            response_text=(
                "Usage: /propose <action_type> <description>\n"
                "  Available types: simulation, email, robot_move, printer_job, http_request\n"
                "  Example: /propose simulation Run batch job for material MAPbI3\n\n"
                "  All actions require operator approval before execution.\n"
                "  Use /actions list to see pending actions."
            ),
            confidence="high",
            suggested_mode="observe",
        )

    action_type = m.group(1).strip()
    description = m.group(2).strip()

    from weslr.action_proposals import propose_action
    result = propose_action(action_type, {}, description)

    if result.get("status") == "error":
        response_text = f"Error: {result.get('message', 'Unknown error')}"
    else:
        response_text = result.get("message", "")

    return build_deterministic_response(
        message=message,
        path="action_propose",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_actions_list(message: str, lowered: str) -> dict:
    """Handle /actions list — list pending and approved action proposals."""
    from weslr.action_proposals import list_pending_actions, list_approved_actions, format_action_summary

    pending = list_pending_actions()
    approved = list_approved_actions()

    lines = []
    if pending:
        lines.append(f"Pending actions: {len(pending)}")
        for a in pending:
            lines.append(format_action_summary(a))
            lines.append("")
    else:
        lines.append("No pending actions.")

    if approved:
        lines.append(f"Approved (not yet executed): {len(approved)}")
        for a in approved:
            lines.append(format_action_summary(a))
            lines.append("")

    response_text = "\n".join(lines) or "No action proposals found."
    return build_deterministic_response(
        message=message,
        path="actions_list",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_actions_approve(message: str, lowered: str) -> dict:
    """Handle /actions approve <action_id> — approve a pending action."""
    import re

    m = re.match(r"/actions approve\s+(\S+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="actions_approve",
            response_text="Usage: /actions approve <action_id>",
            confidence="high",
            suggested_mode="observe",
        )

    action_id = m.group(1).strip()
    from weslr.action_proposals import approve_action
    result = approve_action(action_id)
    response_text = result.get("message", str(result))

    return build_deterministic_response(
        message=message,
        path="actions_approve",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_actions_reject(message: str, lowered: str) -> dict:
    """Handle /actions reject <action_id> — reject a pending action."""
    import re

    m = re.match(r"/actions reject\s+(\S+)", lowered)
    if not m:
        return build_deterministic_response(
            message=message,
            path="actions_reject",
            response_text="Usage: /actions reject <action_id>",
            confidence="high",
            suggested_mode="observe",
        )

    action_id = m.group(1).strip()
    from weslr.action_proposals import reject_action
    result = reject_action(action_id)
    response_text = result.get("message", str(result))

    return build_deterministic_response(
        message=message,
        path="actions_reject",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_actions_run(message: str, lowered: str) -> dict:
    """Handle /actions run — execute all approved actions (dry-run or real)."""
    from weslr.action_runner_dummy import run_approved_actions

    result = run_approved_actions()
    response_text = result.get("message", str(result))

    return build_deterministic_response(
        message=message,
        path="actions_run",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- Tenant Command Handlers ----

def handle_tenant_list(message: str, lowered: str) -> dict:
    """Handle /tenant list — show all tenants and active status."""
    from weslr.tenant_manager import list_tenants
    tenants = list_tenants()
    if not tenants:
        response_text = "No tenants configured. Use /tenant create <id> --domain <domain> to create one."
    else:
        lines = ["Tenants:", ""]
        for t in tenants:
            active = " ◀ active" if t.get("is_active") else ""
            domain = t.get("domain", "unknown")
            tid = t.get("tenant_id", "?")
            lines.append(f"  {tid}  (domain: {domain}){active}")
        response_text = "\n".join(lines)
    return build_deterministic_response(
        message=message,
        path="tenant_list",
        response_text=response_text,
    )


def handle_tenant_create(message: str, lowered: str) -> dict:
    """Handle /tenant create <id> --domain <domain>."""
    from weslr.tenant_manager import init_tenant

    # Parse /tenant create <id> --domain <domain>
    m = re.match(r"/tenant create\s+([a-zA-Z0-9_]+)(.*)", lowered)
    if not m:
        return build_deterministic_response(
            message=message, path="tenant_create",
            response_text="Usage: /tenant create <id> --domain <domain>\n  e.g., /tenant create oncology_team --domain cancer_research",
        )

    tenant_id = m.group(1)
    domain_match = re.search(r"--domain\s+(\S+)", m.group(2))
    domain = domain_match.group(1) if domain_match else "cancer_research"

    try:
        config = init_tenant(tenant_id, domain)
        response_text = (
            f"Tenant '{tenant_id}' created.\n"
            f"  Domain: {domain}\n"
            f"  Config written to tenants/{tenant_id}/tenant_config.json"
        )
    except ValueError as e:
        response_text = f"Error: {e}"
    except Exception as e:
        response_text = f"Error creating tenant: {e}"

    return build_deterministic_response(message=message, path="tenant_create", response_text=response_text)


def handle_tenant_switch(message: str, lowered: str) -> dict:
    """Handle /tenant switch <id>."""
    from weslr.tenant_manager import switch_tenant

    # Extract tenant ID after "/tenant switch "
    parts = lowered.split(None, 2)
    if len(parts) < 3:
        return build_deterministic_response(
            message=message, path="tenant_switch",
            response_text="Usage: /tenant switch <id>",
        )
    tenant_id = parts[2].strip()

    try:
        config = switch_tenant(tenant_id)
        response_text = (
            f"Switched to tenant '{tenant_id}'\n"
            f"  Domain: {config.get('domain', '?')}\n"
            f"  All queries will now use tenants/{tenant_id}/"
        )
    except ValueError as e:
        response_text = f"Error: {e}"
    except Exception as e:
        response_text = f"Error switching tenant: {e}"

    return build_deterministic_response(message=message, path="tenant_switch", response_text=response_text)


def handle_tenant_info(message: str, lowered: str) -> dict:
    """Handle /tenant info <id>."""
    from weslr.tenant_manager import get_tenant_info

    parts = lowered.split(None, 2)
    if len(parts) < 3:
        return build_deterministic_response(
            message=message, path="tenant_info",
            response_text="Usage: /tenant info <id>",
        )
    tenant_id = parts[2].strip()

    info = get_tenant_info(tenant_id)
    if not info:
        response_text = f"Tenant '{tenant_id}' not found."
    else:
        lines = [f"Tenant: {tenant_id}", ""]
        for k, v in info.items():
            if k != "tenant_id":
                lines.append(f"  {k}: {v}")
        response_text = "\n".join(lines)

    return build_deterministic_response(message=message, path="tenant_info", response_text=response_text)


def handle_domains_list(message: str, lowered: str) -> dict:
    """Handle /domains — list available domain schemas."""
    from pathlib import Path

    schema_dir = Path(__file__).parent.parent / "schemas"
    domain_files = sorted(schema_dir.glob("*.json"))
    domains = [f.stem for f in domain_files if f.stem != "base"]

    if not domains:
        response_text = "No domain schemas found in weslr/schemas/"
    else:
        lines = ["Available domain schemas:", ""]
        for d in domains:
            lines.append(f"  - {d}")
        lines.append("")
        lines.append("Use --domain when searching: /search pubmed <query> --domain <name>")
        response_text = "\n".join(lines)

    return build_deterministic_response(message=message, path="domains_list", response_text=response_text)


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


def handle_reaction_predict_cmd(message: str, lowered: str) -> dict:
    """Reaction prediction — read-only."""
    match = re.search(r"^(?:/predict\s+reaction|/reaction\s+predict)\s+(.+)$", lowered)
    reactants = match.group(1).strip() if match else ""
    response_text = handle_reaction_predict(reactants)
    return build_deterministic_response(
        message=message,
        path="reaction_prediction",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_propose_chemistry_cmd(message: str, lowered: str) -> dict:
    """Chemistry proposal — read-only. Handles /propose chemistry and /chemistry propose."""
    match = re.search(r"^(?:/propose\s+chemistry|/chemistry\s+propose)(?:\s+.*)?$", lowered)
    response_text = handle_propose_chemistry(message=message, tenant_id=None, limit=10)
    return build_deterministic_response(
        message=message,
        path="propose_chemistry",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_discover_cmd(message: str, lowered: str) -> dict:
    """Unified discover command — /propose discover [domain]."""
    # Extract domain from: /propose discover <domain> or /discover <domain>
    m = re.match(r"^(?:/propose\s+discover|/discover)(?:\s+(\w+))?$", lowered)
    domain = m.group(1) if m else None
    response_text = handle_discover(domain=domain, tenant_id=None, limit=10)
    return build_deterministic_response(
        message=message,
        path="discover",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


def handle_explore_cmd(message: str, lowered: str) -> dict:
    """Goal-driven hypothesis generation — /explore <goal>."""
    from weslr.commands.explore import handle_explore
    response_text = handle_explore(message=message, lowered=lowered)
    return build_deterministic_response(
        message=message,
        path="explore",
        response_text=response_text,
        confidence="high",
        suggested_mode="observe",
    )


# ---- Symbolic Mathematics Handlers ----

def handle_solve(message: str, lowered: str) -> dict:
    """Handle /solve <equation> [for <variable>]."""
    from weslr.symbolic_math import solve_equation, format_solve_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_solve",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    # Strip the /solve prefix
    body = lowered
    for prefix in ("/solve ", "solve "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    if not body.strip():
        return build_deterministic_response(
            message=message, path="math_solve",
            response_text="Usage: /solve <equation>  e.g., /solve 2*x + 3 = 7  or  /solve x**2 - 4 = 0 for x",
            confidence="high",
        )

    # Extract optional variable: "... for x" or "... var x"
    variable = None
    eq_text = body
    for sep in (" for ", " var ", " wrt "):
        if sep in body:
            parts = body.split(sep, 1)
            eq_text = parts[0].strip()
            variable = parts[1].strip().rstrip(".")
            break

    result = solve_equation(eq_text, variable)
    text = format_solve_output(result)
    return build_deterministic_response(
        message=message, path="math_solve",
        response_text=text,
        confidence="high",
    )


def handle_derivative(message: str, lowered: str) -> dict:
    """Handle /derivative <expr> [variable]."""
    from weslr.symbolic_math import differentiate, format_derivative_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_derivative",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    body = lowered
    for prefix in ("/derivative ", "derivative "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    if not body.strip():
        return build_deterministic_response(
            message=message, path="math_derivative",
            response_text="Usage: /derivative <expr> [variable]  e.g., /derivative x**2 sin(x) x",
            confidence="high",
        )

    parts = body.rstrip().split()
    if len(parts) >= 2:
        expr = " ".join(parts[:-1])
        variable = parts[-1]
    else:
        expr = parts[0]
        variable = "x"

    result = differentiate(expr, variable)
    text = format_derivative_output(result)
    return build_deterministic_response(
        message=message, path="math_derivative",
        response_text=text,
        confidence="high",
    )


def handle_integral(message: str, lowered: str) -> dict:
    """Handle /integral <expr> [variable]."""
    from weslr.symbolic_math import integrate, format_integral_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_integral",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    body = lowered
    for prefix in ("/integral ", "integral ", "integrate "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    parts = body.rstrip().split()
    if len(parts) >= 2:
        expr = " ".join(parts[:-1])
        variable = parts[-1]
    else:
        expr = parts[0]
        variable = "x"

    result = integrate(expr, variable)
    text = format_integral_output(result)
    return build_deterministic_response(
        message=message, path="math_integral",
        response_text=text,
        confidence="high",
    )


def handle_simplify(message: str, lowered: str) -> dict:
    """Handle /simplify <expr>."""
    from weslr.symbolic_math import simplify, format_simplify_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_simplify",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    body = lowered
    for prefix in ("/simplify ", "simplify ", "simplify("):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    result = simplify(body.strip())
    text = format_simplify_output(result)
    return build_deterministic_response(
        message=message, path="math_simplify",
        response_text=text,
        confidence="high",
    )


def handle_evaluate(message: str, lowered: str) -> dict:
    """Handle /evaluate <expr> {var:val,...}  or  /evaluate <expr> var=val."""
    from weslr.symbolic_math import evaluate_expression, is_available
    import re

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_evaluate",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    body = lowered
    for prefix in ("/evaluate ", "evaluate "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    # Parse substitutions: look for {...} or key=val patterns
    # Try {x: 2, y: 3} style
    braces = re.search(r"\{(.+?)\}", body)
    if braces:
        expr = body[:braces.start()].strip()
        subs_str = braces.group(1)
        subs: dict[str, float] = {}
        for pair in subs_str.split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                subs[k.strip()] = float(v.strip())
            elif "=" in pair:
                k, v = pair.split("=", 1)
                subs[k.strip()] = float(v.strip())
    else:
        # Try key=value space-separated
        parts = body.rstrip().split()
        expr = parts[0]
        subs = {}
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                subs[k.strip()] = float(v.strip())

    if not expr.strip():
        return build_deterministic_response(
            message=message, path="math_evaluate",
            response_text="Usage: /evaluate x**2 + y {x: 2, y: 3}  or  /evaluate x+y x=2 y=3",
            confidence="high",
        )

    result = evaluate_expression(expr, subs)
    if result["ok"]:
        text = f"{expr} = {result['value']}"
    else:
        text = f"Error: {result['note']}"
    return build_deterministic_response(
        message=message, path="math_evaluate",
        response_text=text,
        confidence="high",
    )


def handle_expand(message: str, lowered: str) -> dict:
    """Handle /expand <expr>."""
    from weslr.symbolic_math import expand_expr, format_expand_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_expand",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    body = lowered
    for prefix in ("/expand ", "expand "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    result = expand_expr(body.strip())
    text = format_expand_output(result)
    return build_deterministic_response(
        message=message, path="math_expand",
        response_text=text,
        confidence="high",
    )


def handle_optimal(message: str, lowered: str) -> dict:
    """Handle 'optimal <equation> with respect to <variable>' or '/optimal <eq> <var>'."""
    from weslr.symbolic_math import solve_for_optimal, format_optimal_output, is_available

    if not is_available():
        return build_deterministic_response(
            message=message, path="math_optimal",
            response_text="SymPy not installed – install with: pip install sympy",
            confidence="high",
        )

    # Parse: "optimal -0.01*T**2 + 0.5*T + 10 with respect to T" or "optimal ... T"
    sense = "max"
    eq = lowered
    var = "x"

    # strip prefixes
    for prefix in ("optimal ", "find optimal ", "solve for optimal ", "/optimal "):
        if eq.startswith(prefix):
            eq = eq[len(prefix):]
            break

    # Extract variable after "with respect to" or last token
    if "with respect to" in eq:
        parts = eq.split("with respect to", 1)
        eq = parts[0].strip()
        var = parts[1].strip().split()[0] if parts[1].strip() else "x"
    elif "wrt" in eq:
        parts = eq.split("wrt", 1)
        eq = parts[0].strip()
        var = parts[1].strip().split()[0] if parts[1].strip() else "x"
    elif "for" in eq:
        parts = eq.split("for", 1)
        eq = parts[0].strip()
        var = parts[1].strip().split()[0] if parts[1].strip() else "x"
    else:
        toks = eq.strip().split()
        if len(toks) > 1:
            var = toks[-1]
            eq = " ".join(toks[:-1])

    if "min" in lowered.lower():
        sense = "min"

    result = solve_for_optimal(eq, var, sense)
    text = format_optimal_output(result)
    return build_deterministic_response(
        message=message, path="math_optimal",
        response_text=text,
        confidence="high",
    )


# ---- ODE Handlers ----

def handle_ode_propose(message: str, lowered: str) -> dict:
    """Handle /ode propose <description>."""
    from weslr.ode_proposer import propose_ode, format_ode_proposal

    body = message  # preserve original case
    for prefix in ("/ode propose ", "ode propose "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    if not body.strip():
        return build_deterministic_response(
            message=message, path="ode_propose",
            response_text="Usage: /ode propose <description>\nExample: /ode propose tumor growth with chemotherapy",
            confidence="high",
        )

    variables = None  # could be extended to parse variables from message
    candidates = propose_ode(body, variables=variables)
    text = format_ode_proposal(body, candidates)
    return build_deterministic_response(
        message=message, path="ode_propose",
        response_text=text,
        confidence="high",
    )


def handle_ode_solve(message: str, lowered: str) -> dict:
    """Handle /ode solve <equation> [initial=...time=...]."""
    from weslr.ode_proposer import solve_ode

    body = message  # preserve original case for ODE equations
    for prefix in ("/ode solve ", "ode solve "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break

    # Parse initial= and time= kwargs from message (not lowered)
    initial_conditions = {}
    time_range = None

    import re
    ic_match = re.search(r'initial\s*=\s*([A-Za-z_][A-Za-z0-9_]*(?:\s*=\s*[\d.]+\s*,?\s*)+)', body)
    if ic_match:
        try:
            pairs = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([\d.]+)', ic_match.group(1))
            initial_conditions = {k: float(v) for k, v in pairs}
        except Exception:
            pass

    time_match = re.search(r'time\s*=\s*\(([\d.]+)\s*,\s*([\d.]+)\)', body)
    if time_match:
        time_range = (float(time_match.group(1)), float(time_match.group(2)))

    # Strip kwargs to get ODE string
    ode_str = re.sub(r'initial\s*=\s*\([^)]{1,200}\)\s*', '', body)
    ode_str = re.sub(r'time\s*=\s*\([\d.,.\s]{1,50}\)\s*', '', ode_str)
    ode_str = ode_str.strip()

    if not ode_str:
        return build_deterministic_response(
            message=message, path="ode_solve",
            response_text="Usage: /ode solve <equation> [initial=(var=value,...) time=(t0,t1)]\nExample: /ode solve dX/dt = r*X initial=(X=0.1,r=0.5) time=(0,10)",
            confidence="high",
        )

    result = solve_ode(ode_str, initial_conditions=initial_conditions, time_range=time_range)
    if result["ok"]:
        text = f"Equation: {ode_str}\nSolution: {result['solution']}\nNote: {result['note']}"
    else:
        text = f"Equation: {ode_str}\n{result['note']}"
    return build_deterministic_response(
        message=message, path="ode_solve",
        response_text=text,
        confidence="high",
    )


def handle_ode_list(message: str, lowered: str) -> dict:
    """Handle /ode list_templates."""
    from weslr.ode_proposer import list_templates

    templates = list_templates()
    lines = [f"Available ODE templates ({len(templates)}):"]
    for t in templates:
        eq = t.get("equation", t.get("equation_str", ""))
        conf = t.get("confidence", 0)
        domain = ",".join(t.get("domain", []))
        lines.append(f"  [{t['name']}]  conf={conf}  {eq}  ({domain})")
    text = "\n".join(lines)
    return build_deterministic_response(
        message=message, path="ode_list",
        response_text=text,
        confidence="high",
    )


# ---- Quantum Handlers ----

def handle_quantum(message: str, lowered: str) -> dict:
    """Handle /quantum state|apply|measure|reset commands."""
    from weslr.commands.quantum_commands import handle_quantum as q_handle

    text = q_handle(message, lowered)
    return build_deterministic_response(
        message=message, path="quantum",
        response_text=text,
        confidence="high",
    )


# ---- Causal Handlers ----

def handle_causal_propose(message: str, lowered: str) -> dict:
    """Handle /propose cause, /refine cause, /causal commands."""
    from weslr.commands.causality_commands import handle_causal_propose as c_handle

    text = c_handle(message, lowered)
    return build_deterministic_response(
        message=message, path="causal_propose",
        response_text=text,
        confidence="high",
    )


# ---- Temporal Handlers ----

def handle_temporal(message: str, lowered: str) -> dict:
    """Handle /timeseries, /forecast, /alert commands."""
    text = handle_temporal_command(message, lowered)
    return build_deterministic_response(
        message=message, path="temporal",
        response_text=text,
        confidence="high",
    )


# ---- Spatial Handlers ----


def handle_molecule(message: str, lowered: str) -> dict:
    """Handle /molecule and /propose shape commands."""
    text = handle_molecule_command(message, lowered)
    return build_deterministic_response(
        message=message, path="molecular_geometry",
        response_text=text,
        confidence="high",
    )


# ---- Dispatch ----

def dispatch_deterministic_handler(message: str, lowered: str) -> Optional[dict]:
    """
    Sort registry by priority descending, try prefix match, return handler result.
    Returns None if no trigger matches.
    """
    sorted_handlers = sorted(HANDLER_REGISTRY, key=lambda h: h["priority"], reverse=True)
    for entry in sorted_handlers:
        match_type = entry.get("match_type", "prefix")
        if match_type == "regex":
            for trigger in entry["triggers"]:
                if re.search(trigger, lowered):
                    handler_fn_name = entry["handler_fn"]
                    handler_fn = globals().get(handler_fn_name)
                    if handler_fn is not None:
                        return handler_fn(message, lowered)
        else:
            for trigger in entry["triggers"]:
                if lowered.startswith(trigger):
                    handler_fn_name = entry["handler_fn"]
                    handler_fn = globals().get(handler_fn_name)
                    if handler_fn is not None:
                        return handler_fn(message, lowered)
    return None
