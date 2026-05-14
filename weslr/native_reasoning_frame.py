#!/usr/bin/env python3
"""WESLR native reasoning frame helpers V1.

Read-only, parser-less helper layer for composing in-memory cognition signals into an
inspectable response-planning frame. This module does not call models, wire runtime
chat/voice, write files, execute tools, or authorize implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

FRAME_TYPE_V1 = "native_reasoning_frame_v1"
EXECUTION_STATUS_V1 = "non_executing_reasoning_frame_only"
VALIDATION_SCHEMA_V1 = "native_reasoning_frame_validation_v1"

SUFFICIENCY_STATUSES = {
    "sufficient",
    "partially_sufficient",
    "insufficient",
    "requires_evidence",
    "requires_user_clarification",
    "requires_tool_or_calculation",
    "requires_approval",
}

FORBIDDEN_CLAIM_CATEGORIES = [
    "fake_memory",
    "unsupported_capability",
    "official_iq_benchmark_or_certification",
    "protected_test_or_answer_key",
    "hidden_prompt_exposure",
    "auto_approval_or_auto_implementation",
    "runtime_or_persistence_authorization_drift",
    "mystical_consciousness_or_official_test_pass_claim",
]

FORBIDDEN_FIELD_NAMES = {
    "answer_key",
    "answer_keys",
    "hidden_prompt",
    "hidden_prompts",
    "protected_test_item",
    "protected_test_items",
    "official_iq_score",
    "official_benchmark_score",
    "certification_claim",
}

FORBIDDEN_TEXT_MARKERS = {
    "fake_memory": [
        "i remember you personally",
        "i remember our private history",
        "i have personal memories of you",
        "i know you from before without records",
    ],
    "unsupported_capability": [
        "i can execute this now without tools",
        "runtime capability is available by default",
        "i can access any system",
    ],
    "official_iq_benchmark_or_certification": [
        "official iq",
        "certified iq",
        "official benchmark score",
        "officially certified",
        "passed the official benchmark",
    ],
    "protected_test_or_answer_key": [
        "answer key",
        "protected test item",
        "protected benchmark item",
    ],
    "hidden_prompt_exposure": [
        "hidden prompt",
        "system prompt secret",
    ],
    "auto_approval_or_auto_implementation": [
        "auto-approved",
        "automatically approved",
        "auto-implemented",
        "automatically implemented",
        "approval implies implementation",
    ],
    "runtime_or_persistence_authorization_drift": [
        "runtime wiring authorized",
        "persistence authorized by default",
        "write .weslr by default",
        "created .weslr runtime state",
    ],
    "mystical_consciousness_or_official_test_pass_claim": [
        "mystical consciousness",
        "soul proof",
        "officially conscious",
        "passed official tests",
    ],
}


def _json_safe(value: Any) -> Any:
    """Return a deterministic JSON-safe copy without mutating the input."""
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _compact_text(value: Any, default: str = "unspecified") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        stripped = " ".join(value.split())
        return stripped if stripped else default
    if isinstance(value, Mapping):
        for key in ("summary", "intent", "intent_summary", "meaning", "label", "status"):
            if key in value and value[key]:
                return _compact_text(value[key], default=default)
    return _compact_text(str(value), default=default)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            child = f"{path}[{index}]"
            yield from _walk(value, child)


def assess_native_context_sufficiency_v1(
    *,
    known_context: Optional[Any] = None,
    missing_context: Optional[Any] = None,
    evidence_status: Optional[Any] = None,
    uncertainty_status: Optional[Any] = None,
    capability_boundary: Optional[Any] = None,
    approval_required: bool = False,
    requires_tool: bool = False,
    user_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Classify whether supplied in-memory context is enough to answer safely."""
    known = _as_list(known_context)
    missing = _as_list(missing_context)
    evidence = _json_safe(evidence_status) if evidence_status is not None else {}
    uncertainty = _json_safe(uncertainty_status) if uncertainty_status is not None else {}
    boundary = _json_safe(capability_boundary) if capability_boundary is not None else {}

    evidence_weak = False
    if isinstance(evidence, Mapping):
        evidence_weak = evidence.get("requires_evidence") is True or evidence.get("status") in {"weak", "missing", "insufficient"}
    elif isinstance(evidence, str):
        evidence_weak = evidence.lower() in {"weak", "missing", "insufficient", "requires_evidence"}

    uncertainty_high = False
    if isinstance(uncertainty, Mapping):
        uncertainty_high = uncertainty.get("level") in {"high", "unknown"} or uncertainty.get("requires_clarification") is True
    elif isinstance(uncertainty, str):
        uncertainty_high = uncertainty.lower() in {"high", "unknown", "requires_clarification"}

    boundary_requires_tool = requires_tool or (isinstance(boundary, Mapping) and boundary.get("requires_tool") is True)
    boundary_requires_external = isinstance(boundary, Mapping) and boundary.get("requires_external_evidence") is True

    message = (user_message or "").lower()
    memory_question = "remember" in message and ("me" in message or "our" in message)
    if memory_question and not known:
        missing.append("verified memory/context record for the user or prior interaction")

    if approval_required or (isinstance(boundary, Mapping) and boundary.get("requires_approval") is True):
        status = "requires_approval"
        recommended_action = "propose_next_step_for_operator_approval"
    elif boundary_requires_tool:
        status = "requires_tool_or_calculation"
        recommended_action = "explain_tool_or_calculation_requirement"
    elif evidence_weak or boundary_requires_external:
        status = "requires_evidence"
        recommended_action = "request_or_collect_evidence_before_strong_claim"
    elif missing and not known:
        status = "insufficient"
        recommended_action = "ask_clarifying_question"
    elif missing or uncertainty_high:
        status = "partially_sufficient" if known else "requires_user_clarification"
        recommended_action = "answer_with_boundary_or_ask_clarifying_question"
    else:
        status = "sufficient"
        recommended_action = "answer_with_available_context"

    return {
        "schema_version": "native_context_sufficiency_v1",
        "status": status,
        "known": known,
        "missing": missing,
        "evidence_would_improve_confidence": _as_list(
            evidence.get("needed") if isinstance(evidence, Mapping) else None
        ) or (["stronger provenance or direct observation"] if evidence_weak else []),
        "recommended_action": recommended_action,
        "should_answer": status in {"sufficient", "partially_sufficient"},
        "should_ask": status in {"insufficient", "requires_user_clarification"} or bool(missing and not known),
        "should_propose_next_step": status in {"requires_evidence", "requires_tool_or_calculation", "requires_approval"},
    }


def derive_native_capability_boundary_v1(
    *,
    capability_match: Optional[Any] = None,
    capability_boundary_result: Optional[Any] = None,
    governance_hints: Optional[Any] = None,
    requested_action: Optional[str] = None,
) -> Dict[str, Any]:
    """Derive a conservative capability boundary from supplied in-memory signals only."""
    match = _json_safe(capability_match) if capability_match is not None else {}
    supplied = _json_safe(capability_boundary_result) if capability_boundary_result is not None else {}
    governance = _json_safe(governance_hints) if governance_hints is not None else {}
    request = (requested_action or "").lower()

    def supplied_bool(key: str, default: bool = False) -> bool:
        if isinstance(supplied, Mapping) and key in supplied:
            return bool(supplied[key])
        if isinstance(match, Mapping) and key in match:
            return bool(match[key])
        return default

    requires_tool = supplied_bool("requires_tool") or any(token in request for token in ["run", "calculate", "measure", "fetch", "search"])
    requires_external_evidence = supplied_bool("requires_external_evidence") or supplied_bool("external_evidence_required")
    requires_approval = supplied_bool("requires_approval") or (
        isinstance(governance, Mapping) and bool(governance.get("approval_required"))
    )

    explicit_can_help = supplied_bool("can_help", default=bool(match or supplied or requested_action))
    can_prepare = supplied_bool("can_prepare", default=explicit_can_help)
    can_explain = supplied_bool("can_explain", default=True)
    can_analyze = supplied_bool("can_analyze", default=explicit_can_help)
    can_propose = supplied_bool("can_propose", default=True)

    cannot_claim = list(dict.fromkeys(_as_list(supplied.get("cannot_claim") if isinstance(supplied, Mapping) else None) + [
        "official IQ, benchmark, or certification status",
        "runtime capability not supported by supplied input",
        "memory or evidence not present in supplied context",
    ]))
    cannot_do_yet = _as_list(supplied.get("cannot_do_yet") if isinstance(supplied, Mapping) else None)
    if requires_tool:
        cannot_do_yet.append("perform tool-backed action inside this read-only frame")
    if requires_approval:
        cannot_do_yet.append("implement or execute without operator approval")

    return {
        "schema_version": "native_capability_boundary_v1",
        "can_help": explicit_can_help,
        "can_prepare": can_prepare,
        "can_explain": can_explain,
        "can_analyze": can_analyze,
        "can_propose": can_propose,
        "requires_tool": requires_tool,
        "requires_external_evidence": requires_external_evidence,
        "requires_approval": requires_approval,
        "cannot_claim": cannot_claim,
        "cannot_do_yet": list(dict.fromkeys(cannot_do_yet)),
        "runtime_capability_claimed": False,
        "source": "supplied_in_memory_inputs_only",
    }


def build_native_answer_plan_v1(frame_or_inputs: Optional[Mapping[str, Any]] = None, **inputs: Any) -> Dict[str, Any]:
    """Build a structured response plan without generating the final response."""
    data: Dict[str, Any] = {}
    if frame_or_inputs:
        data.update(_json_safe(frame_or_inputs))
    data.update(_json_safe(inputs))

    sufficiency = data.get("context_sufficiency") or data.get("evidence_status") or {}
    boundary = data.get("capability_boundary") or {}
    missing = _as_list(data.get("missing_context"))
    forbidden = _as_list(data.get("forbidden_claims"))

    status = sufficiency.get("status") if isinstance(sufficiency, Mapping) else str(sufficiency or "unspecified")
    requires_approval = bool(data.get("approval_required")) or (isinstance(boundary, Mapping) and bool(boundary.get("requires_approval")))
    requires_tool = isinstance(boundary, Mapping) and bool(boundary.get("requires_tool"))
    requires_evidence = status == "requires_evidence" or (isinstance(boundary, Mapping) and bool(boundary.get("requires_external_evidence")))

    steps: List[str] = []
    if data.get("intent_summary"):
        steps.append("state_interpreted_intent")
    if data.get("known_context"):
        steps.append("use_known_context_with_boundaries")
    if missing:
        steps.append("identify_missing_context")
    if requires_evidence:
        steps.append("name_evidence_needed")
    if requires_tool:
        steps.append("explain_tool_or_calculation_needed")
    if requires_approval:
        steps.append("separate_proposal_from_approval")
    if not steps:
        steps.append("answer_minimally_with_uncertainty_boundary")

    avoid_claims = list(dict.fromkeys(forbidden + _as_list(boundary.get("cannot_claim") if isinstance(boundary, Mapping) else None)))

    return {
        "schema_version": "native_answer_plan_v1",
        "direct_answer_needed": status in {"sufficient", "partially_sufficient"},
        "explain_boundary": bool(missing or requires_tool or requires_approval or requires_evidence),
        "cite_or_reference_evidence": bool(data.get("provenance_refs") or requires_evidence),
        "ask_clarifying_question": status in {"insufficient", "requires_user_clarification"},
        "propose_next_step": status in {"requires_evidence", "requires_tool_or_calculation", "requires_approval"} or bool(data.get("proposal_required")),
        "break_into_steps": len(steps) > 1 or bool(data.get("task_decomposition")),
        "warn_about_uncertainty": status not in {"sufficient"} or bool(data.get("uncertainty_status")),
        "avoid_claims": avoid_claims,
        "steps": steps,
        "final_response_generation": "not_performed",
    }


def build_native_reasoning_frame_v1(
    *,
    user_message: Optional[str] = None,
    request_summary: Optional[str] = None,
    meaning_vector_result: Optional[Any] = None,
    meaning_summary: Optional[Any] = None,
    response_obligation_result: Optional[Any] = None,
    selected_context_bundle: Optional[Any] = None,
    memory_context_hints: Optional[Any] = None,
    evidence_sufficiency_result: Optional[Any] = None,
    capability_match: Optional[Any] = None,
    capability_boundary_result: Optional[Any] = None,
    uncertainty_result: Optional[Any] = None,
    self_model_or_identity_status: Optional[Any] = None,
    task_problem_decomposition_result: Optional[Any] = None,
    provenance_refs: Optional[Any] = None,
    governance_safety_hints: Optional[Any] = None,
    known_context: Optional[Any] = None,
    missing_context: Optional[Any] = None,
    proposal_required: bool = False,
    approval_required: bool = False,
    forbidden_claims: Optional[Any] = None,
) -> Dict[str, Any]:
    """Compose supplied in-memory signals into a JSON-safe native reasoning frame."""
    raw_known = _as_list(known_context)
    if selected_context_bundle is not None:
        raw_known.append({"selected_context_bundle": _json_safe(selected_context_bundle)})
    if memory_context_hints is not None:
        raw_known.append({"memory_context_hints": _json_safe(memory_context_hints)})

    raw_missing = _as_list(missing_context)
    message = user_message or request_summary or ""
    lowered = message.lower()
    if "remember" in lowered and ("me" in lowered or "our" in lowered) and not raw_known:
        raw_missing.append("verified memory record before making a memory claim")

    capability_boundary = derive_native_capability_boundary_v1(
        capability_match=capability_match,
        capability_boundary_result=capability_boundary_result,
        governance_hints=governance_safety_hints,
        requested_action=message,
    )
    approval = bool(approval_required or capability_boundary.get("requires_approval"))

    context_sufficiency = assess_native_context_sufficiency_v1(
        known_context=raw_known,
        missing_context=raw_missing,
        evidence_status=evidence_sufficiency_result,
        uncertainty_status=uncertainty_result,
        capability_boundary=capability_boundary,
        approval_required=approval,
        user_message=message,
    )

    evidence_status = _json_safe(evidence_sufficiency_result) if evidence_sufficiency_result is not None else {
        "status": context_sufficiency["status"],
        "evidence_required": context_sufficiency["status"] == "requires_evidence",
    }
    uncertainty_status = _json_safe(uncertainty_result) if uncertainty_result is not None else {
        "status": "bounded_by_supplied_context",
        "confidence_boundary": context_sufficiency["status"],
    }

    identity_status = _json_safe(self_model_or_identity_status) if self_model_or_identity_status is not None else {
        "status": "stable_weslr_identity_when_supplied_by_runtime",
        "persona_switching": False,
        "claim_boundary": "operational_self_awareness_only_not_mystical_consciousness",
    }
    memory_boundary_status = {
        "fake_memory_forbidden": True,
        "memory_claim_requires_supplied_context": True,
        "memory_context_supplied": bool(raw_known),
    }

    forbidden = list(dict.fromkeys(_as_list(forbidden_claims) + FORBIDDEN_CLAIM_CATEGORIES))

    frame_seed = {
        "message": message,
        "meaning": meaning_summary if meaning_summary is not None else meaning_vector_result,
        "known": raw_known,
        "missing": raw_missing,
        "evidence": evidence_status,
        "boundary": capability_boundary,
        "approval": approval,
    }

    frame: Dict[str, Any] = {
        "frame_id": _stable_id("nrfv1", frame_seed),
        "frame_type": FRAME_TYPE_V1,
        "intent_summary": _compact_text(request_summary or user_message, default="unspecified_intent"),
        "meaning_summary": _compact_text(meaning_summary if meaning_summary is not None else meaning_vector_result, default="meaning_not_supplied"),
        "known_context": _json_safe(raw_known),
        "missing_context": _json_safe(raw_missing),
        "context_sufficiency": context_sufficiency,
        "evidence_status": evidence_status,
        "capability_boundary": capability_boundary,
        "uncertainty_status": uncertainty_status,
        "answer_plan": {},
        "safe_next_step": context_sufficiency["recommended_action"],
        "proposal_required": bool(proposal_required or context_sufficiency["should_propose_next_step"]),
        "approval_required": approval,
        "response_obligations": _json_safe(response_obligation_result) if response_obligation_result is not None else {
            "answer_with_boundaries": True,
            "avoid_fabrication": True,
            "do_not_execute": True,
        },
        "identity_stability_status": identity_status,
        "memory_boundary_status": memory_boundary_status,
        "task_decomposition": _json_safe(task_problem_decomposition_result) if task_problem_decomposition_result is not None else [],
        "provenance_refs": _json_safe(_as_list(provenance_refs)),
        "forbidden_claims": forbidden,
        "execution_status": EXECUTION_STATUS_V1,
        "validation_status": {"validated": False, "reason": "call_validate_native_reasoning_frame_v1"},
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
        },
    }
    frame["answer_plan"] = build_native_answer_plan_v1(frame)
    frame["validation_status"] = validate_native_reasoning_frame_v1(frame)
    return to_native_reasoning_frame_json_safe_v1(frame)


def validate_native_reasoning_frame_v1(frame: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a native reasoning frame against V1 safety/doctrine boundaries."""
    safe_frame = _json_safe(frame)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe_frame.get("frame_type") != FRAME_TYPE_V1:
        add("schema", "frame_type", "frame_type must be native_reasoning_frame_v1")
    if safe_frame.get("execution_status") != EXECUTION_STATUS_V1:
        add("execution", "execution_status", "frame must remain non-executing")

    side_effects = safe_frame.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    if safe_frame.get("approval_required") is True and safe_frame.get("implementation_status") in {"implemented", "auto_implemented"}:
        add("auto_approval_or_auto_implementation", "implementation_status", "approval cannot imply implementation")
    if safe_frame.get("auto_approved") is True or safe_frame.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    boundary = safe_frame.get("capability_boundary", {})
    if isinstance(boundary, Mapping):
        if boundary.get("runtime_capability_claimed") is True or boundary.get("can_execute") is True or boundary.get("can_write_files") is True:
            add("unsupported_capability", "capability_boundary", "unsupported runtime/write capability claim")

    for path, value in _walk(safe_frame):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            add("protected_test_or_answer_key", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            # Claim-boundary lists intentionally name prohibited claim classes; do not
            # reject the frame for carrying its own guardrails.
            guardrail_path = any(
                segment in path
                for segment in ("forbidden_claims", "cannot_claim", "avoid_claims")
            )
            if not guardrail_path:
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        add(category, path, f"forbidden marker for {category}")
        elif isinstance(value, Mapping):
            if value.get("claims_memory_without_context") is True:
                add("fake_memory", path, "memory claim without supplied context")
            if value.get("mystical_consciousness_claim") is True:
                add("mystical_consciousness_or_official_test_pass_claim", path, "mystical consciousness claim")
            if value.get("official_test_passed") is True:
                add("mystical_consciousness_or_official_test_pass_claim", path, "official test pass claim")

    valid = not violations
    return {
        "schema_version": VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def summarize_native_reasoning_frame_v1(frame: Mapping[str, Any]) -> Dict[str, Any]:
    """Return deterministic, count-oriented frame summary for inspection."""
    safe = _json_safe(frame)
    validation = validate_native_reasoning_frame_v1(safe)
    answer_plan = safe.get("answer_plan", {}) if isinstance(safe.get("answer_plan"), Mapping) else {}
    return {
        "frame_id": safe.get("frame_id"),
        "frame_type": safe.get("frame_type"),
        "execution_status": safe.get("execution_status"),
        "intent_summary": safe.get("intent_summary"),
        "context_sufficiency_status": safe.get("context_sufficiency", {}).get("status") if isinstance(safe.get("context_sufficiency"), Mapping) else None,
        "known_context_count": len(_as_list(safe.get("known_context"))),
        "missing_context_count": len(_as_list(safe.get("missing_context"))),
        "provenance_ref_count": len(_as_list(safe.get("provenance_refs"))),
        "proposal_required": bool(safe.get("proposal_required")),
        "approval_required": bool(safe.get("approval_required")),
        "safe_next_step": safe.get("safe_next_step"),
        "answer_plan_flags": {
            "direct_answer_needed": bool(answer_plan.get("direct_answer_needed")),
            "ask_clarifying_question": bool(answer_plan.get("ask_clarifying_question")),
            "propose_next_step": bool(answer_plan.get("propose_next_step")),
            "warn_about_uncertainty": bool(answer_plan.get("warn_about_uncertainty")),
        },
        "validation_status": validation["validation_status"],
        "violation_count": validation["violation_count"],
    }


def to_native_reasoning_frame_json_safe_v1(frame: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe frame copy; no persistence, no file writes."""
    return _json_safe(frame)


__all__ = [
    "FRAME_TYPE_V1",
    "EXECUTION_STATUS_V1",
    "assess_native_context_sufficiency_v1",
    "derive_native_capability_boundary_v1",
    "build_native_answer_plan_v1",
    "build_native_reasoning_frame_v1",
    "validate_native_reasoning_frame_v1",
    "summarize_native_reasoning_frame_v1",
    "to_native_reasoning_frame_json_safe_v1",
]
