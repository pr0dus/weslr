#!/usr/bin/env python3
"""WESLR native response draft helpers V1.

Read-only helper layer that turns a validated native reasoning frame into an
inspectable response-draft structure. This module does not wire chat/voice,
call models, execute tools, persist state, or authorize implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_reasoning_frame import (
    EXECUTION_STATUS_V1 as FRAME_EXECUTION_STATUS_V1,
    FRAME_TYPE_V1,
    FORBIDDEN_FIELD_NAMES,
    FORBIDDEN_TEXT_MARKERS,
    validate_native_reasoning_frame_v1,
)

DRAFT_TYPE_V1 = "native_response_draft_v1"
DRAFT_EXECUTION_STATUS_V1 = "non_executing_response_draft_only"
DRAFT_VALIDATION_SCHEMA_V1 = "native_response_draft_validation_v1"
RESPONSE_MODES_V1 = {
    "answer",
    "clarify",
    "explain_boundary",
    "propose_next_step",
    "refuse_or_redirect",
    "insufficient_context",
    "evidence_required",
}


def _json_safe(value: Any) -> Any:
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


def _compact(value: Any, default: str = "not_supplied") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, Mapping):
        for key in ("summary", "intent_summary", "status", "recommended_action", "safe_next_step"):
            if value.get(key):
                return _compact(value[key], default=default)
    return _compact(str(value), default=default)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def derive_native_response_mode_v1(frame: Mapping[str, Any]) -> str:
    """Derive a conservative response mode from a native reasoning frame."""
    safe = _json_safe(frame)
    sufficiency = safe.get("context_sufficiency", {}) if isinstance(safe.get("context_sufficiency"), Mapping) else {}
    status = sufficiency.get("status") or safe.get("evidence_status", {}).get("status") if isinstance(safe.get("evidence_status"), Mapping) else None
    boundary = safe.get("capability_boundary", {}) if isinstance(safe.get("capability_boundary"), Mapping) else {}
    plan = safe.get("answer_plan", {}) if isinstance(safe.get("answer_plan"), Mapping) else {}

    cannot_do = _as_list(boundary.get("cannot_do_yet"))
    requires_evidence = status == "requires_evidence" or boundary.get("requires_external_evidence") is True
    requires_approval = safe.get("approval_required") is True or boundary.get("requires_approval") is True
    requires_tool_or_boundary = status == "requires_tool_or_calculation" or boundary.get("requires_tool") is True or bool(cannot_do)

    if status == "insufficient":
        return "insufficient_context"
    if status == "requires_user_clarification" or plan.get("ask_clarifying_question") is True:
        return "clarify"
    if requires_evidence:
        return "evidence_required"
    if requires_tool_or_boundary:
        return "explain_boundary"
    if requires_approval or safe.get("proposal_required") is True or plan.get("propose_next_step") is True:
        return "propose_next_step"
    if status in {"sufficient", "partially_sufficient", None}:
        return "answer"
    return "explain_boundary"


def build_native_response_draft_v1(frame: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a JSON-safe response draft from a native reasoning frame."""
    safe_frame = _json_safe(frame)
    response_mode = derive_native_response_mode_v1(safe_frame)
    sufficiency = safe_frame.get("context_sufficiency", {}) if isinstance(safe_frame.get("context_sufficiency"), Mapping) else {}
    boundary = safe_frame.get("capability_boundary", {}) if isinstance(safe_frame.get("capability_boundary"), Mapping) else {}
    plan = safe_frame.get("answer_plan", {}) if isinstance(safe_frame.get("answer_plan"), Mapping) else {}
    evidence = safe_frame.get("evidence_status", {})
    uncertainty = safe_frame.get("uncertainty_status", {})
    identity = safe_frame.get("identity_stability_status", {})
    memory = safe_frame.get("memory_boundary_status", {})

    missing_context = _as_list(safe_frame.get("missing_context"))
    cannot_do = _as_list(boundary.get("cannot_do_yet"))
    cannot_claim = _as_list(boundary.get("cannot_claim"))
    forbidden_claims = _as_list(safe_frame.get("forbidden_claims"))

    answer_outline = [
        {"part": "intent", "summary": _compact(safe_frame.get("intent_summary"), "state_interpreted_intent")},
        {"part": "mode", "summary": response_mode},
    ]
    for step in _as_list(plan.get("steps"))[:8]:
        answer_outline.append({"part": "planned_step", "summary": _compact(step)})

    boundary_notes = []
    if sufficiency.get("status"):
        boundary_notes.append(f"context_status:{sufficiency.get('status')}")
    if cannot_do:
        boundary_notes.extend(f"cannot_do_yet:{_compact(item)}" for item in cannot_do)
    if safe_frame.get("execution_status") == FRAME_EXECUTION_STATUS_V1:
        boundary_notes.append("source_frame_is_non_executing")

    evidence_notes = []
    if isinstance(evidence, Mapping):
        if evidence.get("status"):
            evidence_notes.append(f"evidence_status:{evidence.get('status')}")
        if evidence.get("evidence_required") or sufficiency.get("status") == "requires_evidence":
            evidence_notes.append("stronger_evidence_required_before_strong_claim")
        evidence_notes.extend(f"needed:{_compact(item)}" for item in _as_list(evidence.get("needed")))
    else:
        evidence_notes.append(_compact(evidence))

    capability_notes = [
        f"can_explain:{bool(boundary.get('can_explain', False))}",
        f"can_propose:{bool(boundary.get('can_propose', False))}",
        f"requires_tool:{bool(boundary.get('requires_tool', False))}",
        f"requires_approval:{bool(boundary.get('requires_approval', False))}",
    ]

    uncertainty_notes = []
    if isinstance(uncertainty, Mapping):
        for key in ("status", "level", "confidence_boundary"):
            if uncertainty.get(key):
                uncertainty_notes.append(f"{key}:{_compact(uncertainty.get(key))}")
    elif uncertainty:
        uncertainty_notes.append(_compact(uncertainty))
    if plan.get("warn_about_uncertainty"):
        uncertainty_notes.append("answer_should_warn_about_uncertainty")

    proposal_required = bool(safe_frame.get("proposal_required"))
    approval_required = bool(safe_frame.get("approval_required"))
    draft_seed = {
        "frame_id": safe_frame.get("frame_id"),
        "mode": response_mode,
        "next": safe_frame.get("safe_next_step"),
        "missing": missing_context,
    }

    draft: Dict[str, Any] = {
        "draft_id": _stable_id("nrdv1", draft_seed),
        "draft_type": DRAFT_TYPE_V1,
        "source_frame_id": safe_frame.get("frame_id"),
        "response_mode": response_mode,
        "answer_outline": answer_outline,
        "boundary_notes": boundary_notes,
        "missing_context_questions": [f"clarify:{_compact(item)}" for item in missing_context],
        "evidence_notes": evidence_notes,
        "capability_notes": capability_notes,
        "uncertainty_notes": uncertainty_notes,
        "next_safe_step": _compact(safe_frame.get("safe_next_step"), "answer_with_available_context"),
        "proposal_note": "proposal_only_not_implementation" if proposal_required else "no_proposal_required_by_frame",
        "approval_note": "operator_approval_required_before_execution" if approval_required else "no_approval_granted_or_required_by_draft",
        "identity_note": _compact(identity, "stable_identity_boundary_not_supplied"),
        "memory_boundary_note": "memory_claim_requires_supplied_context" if isinstance(memory, Mapping) and memory.get("memory_claim_requires_supplied_context") else "no_memory_claim_made_by_draft",
        "forbidden_claims_avoided": list(dict.fromkeys(forbidden_claims + cannot_claim)),
        "execution_status": DRAFT_EXECUTION_STATUS_V1,
        "final_chat_output": False,
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
            "prompt_specific_script": False,
        },
        "validation_status": {"validated": False, "reason": "call_validate_native_response_draft_v1"},
    }
    draft["validation_status"] = validate_native_response_draft_v1(draft, frame=safe_frame)
    return to_native_response_draft_json_safe_v1(draft)


def validate_native_response_draft_v1(draft: Mapping[str, Any], frame: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Validate a response draft and optional source-frame consistency."""
    safe_draft = _json_safe(draft)
    safe_frame = _json_safe(frame) if frame is not None else None
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe_draft.get("draft_type") != DRAFT_TYPE_V1:
        add("schema", "draft_type", "draft_type must be native_response_draft_v1")
    if safe_draft.get("execution_status") != DRAFT_EXECUTION_STATUS_V1:
        add("execution", "execution_status", "draft must remain non-executing")
    if safe_draft.get("response_mode") not in RESPONSE_MODES_V1:
        add("schema", "response_mode", "unknown response mode")
    if safe_draft.get("final_chat_output") is True:
        add("runtime_or_persistence_authorization_drift", "final_chat_output", "draft cannot claim final public output")

    side_effects = safe_draft.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    if safe_draft.get("auto_approved") is True or safe_draft.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    for path, value in _walk(safe_draft):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            add("protected_test_or_answer_key", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("forbidden_claims_avoided", "capability_notes", "boundary_notes"))
            if not guardrail_path:
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        add(category, path, f"forbidden marker for {category}")
        elif isinstance(value, Mapping):
            if value.get("claims_memory_without_context") is True:
                add("fake_memory", path, "memory claim without supplied context")
            if value.get("runtime_capability_claimed") is True or value.get("can_execute") is True:
                add("unsupported_capability", path, "unsupported capability claim")
            if value.get("mystical_consciousness_claim") is True or value.get("official_test_passed") is True:
                add("mystical_consciousness_or_official_test_pass_claim", path, "forbidden identity/test claim")

    if safe_frame is not None:
        frame_validation = validate_native_reasoning_frame_v1(safe_frame)
        if not frame_validation.get("valid"):
            add("source_frame", "frame", "source frame is not valid")
        if safe_draft.get("source_frame_id") != safe_frame.get("frame_id"):
            add("source_frame", "source_frame_id", "draft source_frame_id does not match frame")

        frame_mode = derive_native_response_mode_v1(safe_frame)
        if safe_draft.get("response_mode") == "answer" and frame_mode != "answer":
            add("source_frame_contradiction", "response_mode", "draft overstates answer mode against frame boundary")

        sufficiency = safe_frame.get("context_sufficiency", {}) if isinstance(safe_frame.get("context_sufficiency"), Mapping) else {}
        boundary = safe_frame.get("capability_boundary", {}) if isinstance(safe_frame.get("capability_boundary"), Mapping) else {}
        missing = _as_list(safe_frame.get("missing_context"))
        missing_questions = _as_list(safe_draft.get("missing_context_questions"))

        if missing and not missing_questions:
            add("source_frame_contradiction", "missing_context_questions", "draft omits required missing-context boundary")
        if sufficiency.get("status") == "requires_evidence" and not _as_list(safe_draft.get("evidence_notes")):
            add("source_frame_contradiction", "evidence_notes", "draft omits required evidence warning")
        if safe_frame.get("approval_required") is True and "approval" not in _compact(safe_draft.get("approval_note"), "").lower():
            add("source_frame_contradiction", "approval_note", "draft omits approval boundary")
        if boundary.get("requires_tool") is True and not _as_list(safe_draft.get("capability_notes")):
            add("source_frame_contradiction", "capability_notes", "draft omits capability boundary")

    valid = not violations
    return {
        "schema_version": DRAFT_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def render_native_response_draft_preview_v1(draft: Mapping[str, Any]) -> str:
    """Render a deterministic safe inspection preview for a response draft."""
    safe = _json_safe(draft)

    def bullet_lines(values: Any) -> List[str]:
        items = _as_list(values)
        return [f"- {_compact(item)}" for item in items] if items else ["- none"]

    sections = [
        ("Response Mode", [f"- {_compact(safe.get('response_mode'))}"]),
        ("Answer Outline", bullet_lines([item.get("summary") if isinstance(item, Mapping) else item for item in _as_list(safe.get("answer_outline"))])),
        ("Boundaries", bullet_lines(safe.get("boundary_notes"))),
        ("Missing Context", bullet_lines(safe.get("missing_context_questions"))),
        ("Evidence", bullet_lines(safe.get("evidence_notes"))),
        ("Capability", bullet_lines(safe.get("capability_notes"))),
        ("Uncertainty", bullet_lines(safe.get("uncertainty_notes"))),
        ("Next Safe Step", [f"- {_compact(safe.get('next_safe_step'))}"]),
    ]
    lines: List[str] = []
    for title, body in sections:
        lines.append(f"## {title}")
        lines.extend(body)
    lines.append("## Execution")
    lines.append(f"- {DRAFT_EXECUTION_STATUS_V1}")
    return "\n".join(lines)


def to_native_response_draft_json_safe_v1(draft: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe draft copy; no persistence, no file writes."""
    return _json_safe(draft)


__all__ = [
    "DRAFT_TYPE_V1",
    "DRAFT_EXECUTION_STATUS_V1",
    "derive_native_response_mode_v1",
    "build_native_response_draft_v1",
    "validate_native_response_draft_v1",
    "render_native_response_draft_preview_v1",
    "to_native_response_draft_json_safe_v1",
]
