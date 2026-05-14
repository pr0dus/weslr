#!/usr/bin/env python3
"""WESLR native response assembly helpers V1.

Read-only assembly layer that combines a native reasoning frame, native response
 draft, and native response self-check into an inspectable response candidate.
This module does not wire runtime chat/voice, call models, execute tools,
persist state, score benchmarks, or authorize implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_reasoning_frame import FORBIDDEN_FIELD_NAMES, FORBIDDEN_TEXT_MARKERS
from weslr.native_response_draft import DRAFT_TYPE_V1, validate_native_response_draft_v1
from weslr.native_response_self_check import SELF_CHECK_TYPE_V1, validate_native_response_self_check_result_v1

CANDIDATE_TYPE_V1 = "native_response_candidate_v1"
CANDIDATE_EXECUTION_STATUS_V1 = "non_executing_response_candidate_only"
CANDIDATE_VALIDATION_SCHEMA_V1 = "native_response_candidate_validation_v1"
SECTION_KEYS_V1 = (
    "direct_answer",
    "boundary",
    "missing_context",
    "evidence",
    "capability",
    "uncertainty",
    "next_safe_step",
    "proposal_or_approval",
)


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
        for key in ("summary", "intent_summary", "status", "recommended_action", "safe_next_step", "explanation", "issue_type"):
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


def _string_items(values: Any) -> List[str]:
    return [_compact(item) for item in _as_list(values) if _compact(item, "")]


def derive_native_response_sections_v1(frame: Mapping[str, Any], draft: Mapping[str, Any], self_check: Mapping[str, Any]) -> Dict[str, Any]:
    """Derive deterministic response sections from frame, draft, and self-check fields."""
    safe_frame = _json_safe(frame)
    safe_draft = _json_safe(draft)
    safe_check = _json_safe(self_check)

    mode = safe_draft.get("response_mode") or "explain_boundary"
    outline = _as_list(safe_draft.get("answer_outline"))
    direct = [_compact(item.get("summary") if isinstance(item, Mapping) else item) for item in outline]
    direct = [item for item in direct if item and item != "not_supplied"]
    if not direct:
        direct = [f"response_mode:{_compact(mode)}"]

    boundary = _string_items(safe_draft.get("boundary_notes"))
    if safe_check.get("self_check_status") in {"blocked", "revision_required"}:
        boundary.append(f"revision_required_by_self_check:{safe_check.get('self_check_status')}")
    if safe_frame.get("execution_status"):
        boundary.append("candidate_is_inspection_only_not_runtime_output")

    missing_context = _string_items(safe_draft.get("missing_context_questions"))
    if mode == "insufficient_context" and not missing_context:
        missing_context.append("missing_context_required_before_safe_answer")

    evidence = _string_items(safe_draft.get("evidence_notes"))
    sufficiency = safe_frame.get("context_sufficiency", {}) if isinstance(safe_frame.get("context_sufficiency"), Mapping) else {}
    if mode == "evidence_required" or sufficiency.get("status") == "requires_evidence":
        if not evidence:
            evidence.append("evidence_required_before_strong_claim")

    capability = _string_items(safe_draft.get("capability_notes"))
    capability_boundary = safe_frame.get("capability_boundary", {}) if isinstance(safe_frame.get("capability_boundary"), Mapping) else {}
    if capability_boundary.get("requires_tool") is True and not any("requires_tool" in item for item in capability):
        capability.append("requires_tool:true")
    if capability_boundary.get("requires_approval") is True and not any("requires_approval" in item for item in capability):
        capability.append("requires_approval:true")

    uncertainty = _string_items(safe_draft.get("uncertainty_notes"))
    uncertainty_status = safe_frame.get("uncertainty_status")
    if uncertainty_status and not uncertainty:
        uncertainty.append(_compact(uncertainty_status))

    next_safe_step = [_compact(safe_draft.get("next_safe_step"), "answer_with_available_context")]

    proposal_or_approval = []
    for key in ("proposal_note", "approval_note"):
        note = _compact(safe_draft.get(key), "")
        if note:
            proposal_or_approval.append(note)
    if safe_frame.get("approval_required") is True and not any("approval" in item.lower() for item in proposal_or_approval):
        proposal_or_approval.append("operator_approval_required_before_execution")
    if safe_frame.get("proposal_required") is True and not any("proposal" in item.lower() for item in proposal_or_approval):
        proposal_or_approval.append("proposal_only_not_implementation")

    return {
        "direct_answer": direct,
        "boundary": boundary or ["candidate_is_non_executing_inspection_artifact"],
        "missing_context": missing_context,
        "evidence": evidence,
        "capability": capability,
        "uncertainty": uncertainty,
        "next_safe_step": next_safe_step,
        "proposal_or_approval": proposal_or_approval,
    }


def assemble_native_response_candidate_v1(frame: Mapping[str, Any], draft: Mapping[str, Any], self_check: Mapping[str, Any]) -> Dict[str, Any]:
    """Assemble a JSON-safe inspectable native response candidate."""
    safe_frame = _json_safe(frame)
    safe_draft = _json_safe(draft)
    safe_check = _json_safe(self_check)
    sections = derive_native_response_sections_v1(safe_frame, safe_draft, safe_check)
    self_check_status = safe_check.get("self_check_status", "unknown")
    safe_to_preview = bool(safe_check.get("safe_to_preview")) and self_check_status not in {"blocked", "revision_required"}
    omitted = list(dict.fromkeys(_as_list(safe_draft.get("forbidden_claims_avoided"))))
    if safe_check.get("issue_count", 0):
        omitted.extend(f"self_check_issue:{_compact(issue)}" for issue in _as_list(safe_check.get("issues")))

    seed = {
        "frame": safe_frame.get("frame_id"),
        "draft": safe_draft.get("draft_id"),
        "self_check": safe_check.get("self_check_id"),
        "mode": safe_draft.get("response_mode"),
        "status": self_check_status,
    }
    candidate: Dict[str, Any] = {
        "candidate_id": _stable_id("nrcv1", seed),
        "candidate_type": CANDIDATE_TYPE_V1,
        "source_frame_id": safe_frame.get("frame_id"),
        "source_draft_id": safe_draft.get("draft_id"),
        "source_self_check_id": safe_check.get("self_check_id"),
        "response_mode": safe_draft.get("response_mode"),
        "response_sections": sections,
        "safety_notes": [
            "inspectable_candidate_only",
            "not_final_or_live_runtime_output",
            "no_model_call_or_tool_execution_performed",
            "safe_to_wire_runtime:false",
        ],
        "omitted_claims": omitted,
        "self_check_status": self_check_status,
        "safe_to_preview": safe_to_preview,
        "safe_to_wire_runtime": False,
        "final_chat_output": False,
        "live_runtime_output": False,
        "execution_status": CANDIDATE_EXECUTION_STATUS_V1,
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
        "validation_status": {"validated": False, "reason": "call_validate_native_response_candidate_v1"},
    }
    candidate["validation_status"] = validate_native_response_candidate_v1(candidate, frame=safe_frame, draft=safe_draft, self_check=safe_check)
    return to_native_response_candidate_json_safe_v1(candidate)


def validate_native_response_candidate_v1(
    candidate: Mapping[str, Any],
    frame: Optional[Mapping[str, Any]] = None,
    draft: Optional[Mapping[str, Any]] = None,
    self_check: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate candidate safety, non-runtime boundary, and optional source consistency."""
    safe = _json_safe(candidate)
    safe_frame = _json_safe(frame) if frame is not None else None
    safe_draft = _json_safe(draft) if draft is not None else None
    safe_check = _json_safe(self_check) if self_check is not None else None
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe.get("candidate_type") != CANDIDATE_TYPE_V1:
        add("schema", "candidate_type", "candidate_type must be native_response_candidate_v1")
    if safe.get("execution_status") != CANDIDATE_EXECUTION_STATUS_V1:
        add("execution", "execution_status", "candidate must remain non-executing")
    if safe.get("safe_to_wire_runtime") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_wire_runtime", "safe_to_wire_runtime must remain false")
    if safe.get("final_chat_output") is True or safe.get("live_runtime_output") is True:
        add("runtime_or_persistence_authorization_drift", "$", "candidate cannot claim final/live runtime output")
    if safe.get("auto_approved") is True or safe.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    side_effects = safe.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    sections = safe.get("response_sections", {})
    if not isinstance(sections, Mapping):
        add("schema", "response_sections", "response_sections must be a mapping")
    else:
        for key in SECTION_KEYS_V1:
            if key not in sections:
                add("schema", f"response_sections.{key}", "required response section missing")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            add("protected_test_or_answer_key", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("omitted_claims", "safety_notes", "boundary", "capability"))
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
        if safe.get("source_frame_id") != safe_frame.get("frame_id"):
            add("source_id_mismatch", "source_frame_id", "candidate source_frame_id does not match frame")
    if safe_draft is not None:
        draft_validation = validate_native_response_draft_v1(safe_draft, frame=safe_frame) if safe_frame is not None else validate_native_response_draft_v1(safe_draft)
        if not draft_validation.get("valid"):
            add("source_draft", "draft", "source draft is not valid")
        if safe_draft.get("draft_type") != DRAFT_TYPE_V1:
            add("source_draft", "draft_type", "source draft type mismatch")
        if safe.get("source_draft_id") != safe_draft.get("draft_id"):
            add("source_id_mismatch", "source_draft_id", "candidate source_draft_id does not match draft")
        if safe.get("response_mode") != safe_draft.get("response_mode"):
            add("source_contradiction", "response_mode", "candidate response_mode does not match draft")
        expected_sections = derive_native_response_sections_v1(safe_frame or {}, safe_draft, safe_check or {})
        candidate_sections = safe.get("response_sections", {}) if isinstance(safe.get("response_sections"), Mapping) else {}
        for key in ("missing_context", "evidence", "capability", "proposal_or_approval"):
            expected = set(_string_items(expected_sections.get(key)))
            actual = set(_string_items(candidate_sections.get(key)))
            if expected and not expected.issubset(actual):
                add("source_contradiction", f"response_sections.{key}", f"candidate omits required {key} notes")
    if safe_check is not None:
        check_validation = validate_native_response_self_check_result_v1(safe_check)
        if not check_validation.get("valid"):
            add("source_self_check", "self_check", "source self-check is not valid")
        if safe_check.get("self_check_type") != SELF_CHECK_TYPE_V1:
            add("source_self_check", "self_check_type", "source self-check type mismatch")
        if safe.get("source_self_check_id") != safe_check.get("self_check_id"):
            add("source_id_mismatch", "source_self_check_id", "candidate source_self_check_id does not match self-check")
        status = safe_check.get("self_check_status")
        if safe.get("self_check_status") != status:
            add("source_contradiction", "self_check_status", "candidate self_check_status does not match self-check")
        if status in {"blocked", "revision_required"}:
            if safe.get("safe_to_preview") is True:
                add("source_contradiction", "safe_to_preview", "blocked/revision-required candidate cannot be preview-safe")
            boundary_blob = json.dumps(_json_safe(safe.get("response_sections", {}).get("boundary", []))).lower() if isinstance(safe.get("response_sections"), Mapping) else ""
            if "revision_required" not in boundary_blob:
                add("source_contradiction", "response_sections.boundary", "blocked/revision-required self-check must be reflected in boundary")

    valid = not violations
    return {
        "schema_version": CANDIDATE_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def render_native_response_candidate_preview_v1(candidate: Mapping[str, Any]) -> str:
    """Render deterministic safe Markdown for inspection only."""
    safe = _json_safe(candidate)
    sections = safe.get("response_sections", {}) if isinstance(safe.get("response_sections"), Mapping) else {}

    def bullet_lines(values: Any) -> List[str]:
        items = _string_items(values)
        return [f"- {item}" for item in items] if items else ["- none"]

    lines = [
        "# Native Response Candidate",
        "## Mode",
        f"- {_compact(safe.get('response_mode'), 'unknown')}",
        "## Drafted Response Sections",
    ]
    lines.extend(bullet_lines(sections.get("direct_answer")))
    for title, key in (
        ("Boundaries", "boundary"),
        ("Missing Context", "missing_context"),
        ("Evidence", "evidence"),
        ("Capability", "capability"),
        ("Uncertainty", "uncertainty"),
        ("Next Safe Step", "next_safe_step"),
        ("Proposal / Approval", "proposal_or_approval"),
    ):
        lines.append(f"## {title}")
        lines.extend(bullet_lines(sections.get(key)))
    lines.append("## Self-Check Status")
    lines.append(f"- {_compact(safe.get('self_check_status'), 'unknown')}")
    lines.append("## Non-Execution Disclaimer")
    lines.append(f"- {CANDIDATE_EXECUTION_STATUS_V1}")
    lines.append("- safe_to_wire_runtime:false")
    lines.append("- not_final_or_live_runtime_output")
    return "\n".join(lines)


def to_native_response_candidate_json_safe_v1(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe candidate copy; no persistence, no file writes."""
    return _json_safe(candidate)


__all__ = [
    "CANDIDATE_TYPE_V1",
    "CANDIDATE_EXECUTION_STATUS_V1",
    "derive_native_response_sections_v1",
    "assemble_native_response_candidate_v1",
    "validate_native_response_candidate_v1",
    "render_native_response_candidate_preview_v1",
    "to_native_response_candidate_json_safe_v1",
]
