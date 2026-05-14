#!/usr/bin/env python3
"""WESLR native response dry vertical slice helpers V1.

In-memory dry-run helper that composes the native response chain:
reasoning frame -> response draft -> self-check -> response candidate.
This module does not wire chat/voice, call models, execute tools, persist state,
score benchmarks, or authorize implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_reasoning_frame import (
    FORBIDDEN_FIELD_NAMES,
    FORBIDDEN_TEXT_MARKERS,
    build_native_reasoning_frame_v1,
    validate_native_reasoning_frame_v1,
)
from weslr.native_response_draft import build_native_response_draft_v1, validate_native_response_draft_v1
from weslr.native_response_self_check import build_native_response_self_check_result_v1, validate_native_response_self_check_result_v1
from weslr.native_response_assembly import (
    assemble_native_response_candidate_v1,
    render_native_response_candidate_preview_v1,
    validate_native_response_candidate_v1,
)

DRY_SLICE_TYPE_V1 = "native_response_dry_vertical_slice_v1"
DRY_SLICE_EXECUTION_STATUS_V1 = "non_executing_dry_slice_only"
DRY_SLICE_VALIDATION_SCHEMA_V1 = "native_response_dry_slice_validation_v1"
EXECUTABLE_MARKERS_V1 = (
    "executable artifact",
    "runnable artifact",
    "run this command",
    "execute this command",
    "runtime wiring authorized",
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
        for key in ("summary", "intent_summary", "status", "recommended_action", "safe_next_step", "self_check_status", "slice_status"):
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


def _derive_slice_status(frame: Mapping[str, Any], draft: Mapping[str, Any], self_check: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    check_status = self_check.get("self_check_status")
    if check_status == "blocked":
        return "blocked"
    if check_status == "revision_required":
        return "revision_required"
    mode = draft.get("response_mode") or candidate.get("response_mode")
    if mode in {"insufficient_context", "clarify"}:
        return "insufficient_context"
    if mode == "evidence_required":
        return "evidence_required"
    context_status = frame.get("context_sufficiency", {}).get("status") if isinstance(frame.get("context_sufficiency"), Mapping) else None
    if context_status == "requires_evidence":
        return "evidence_required"
    if context_status in {"insufficient", "requires_user_clarification"}:
        return "insufficient_context"
    if bool(candidate.get("safe_to_preview")):
        return "candidate_ready_for_preview"
    return "revision_required"


def build_native_response_dry_slice_v1(
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
    """Build the full native response chain in memory and return one dry slice."""
    frame = build_native_reasoning_frame_v1(
        user_message=user_message,
        request_summary=request_summary,
        meaning_vector_result=meaning_vector_result,
        meaning_summary=meaning_summary,
        response_obligation_result=response_obligation_result,
        selected_context_bundle=selected_context_bundle,
        memory_context_hints=memory_context_hints,
        evidence_sufficiency_result=evidence_sufficiency_result,
        capability_match=capability_match,
        capability_boundary_result=capability_boundary_result,
        uncertainty_result=uncertainty_result,
        self_model_or_identity_status=self_model_or_identity_status,
        task_problem_decomposition_result=task_problem_decomposition_result,
        provenance_refs=provenance_refs,
        governance_safety_hints=governance_safety_hints,
        known_context=known_context,
        missing_context=missing_context,
        proposal_required=proposal_required,
        approval_required=approval_required,
        forbidden_claims=forbidden_claims,
    )
    draft = build_native_response_draft_v1(frame)
    self_check = build_native_response_self_check_result_v1(frame, draft)
    candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
    slice_status = _derive_slice_status(frame, draft, self_check, candidate)
    safe_to_preview = slice_status == "candidate_ready_for_preview" and bool(candidate.get("safe_to_preview"))

    seed = {
        "frame": frame.get("frame_id"),
        "draft": draft.get("draft_id"),
        "self_check": self_check.get("self_check_id"),
        "candidate": candidate.get("candidate_id"),
        "status": slice_status,
    }
    result: Dict[str, Any] = {
        "slice_id": _stable_id("nrdsv1", seed),
        "slice_type": DRY_SLICE_TYPE_V1,
        "frame": frame,
        "draft": draft,
        "self_check": self_check,
        "candidate": candidate,
        "slice_status": slice_status,
        "safe_to_preview": safe_to_preview,
        "safe_to_wire_runtime": False,
        "final_chat_output": False,
        "live_runtime_output": False,
        "execution_status": DRY_SLICE_EXECUTION_STATUS_V1,
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
        "validation_status": {"validated": False, "reason": "call_validate_native_response_dry_slice_v1"},
    }
    result["validation_status"] = validate_native_response_dry_slice_v1(result)
    return to_native_response_dry_slice_json_safe_v1(result)


def validate_native_response_dry_slice_v1(slice_result: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate dry-slice chain integrity and safety/non-runtime boundaries."""
    safe = _json_safe(slice_result)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe.get("slice_type") != DRY_SLICE_TYPE_V1:
        add("schema", "slice_type", "slice_type must be native_response_dry_vertical_slice_v1")
    if safe.get("execution_status") != DRY_SLICE_EXECUTION_STATUS_V1:
        add("execution", "execution_status", "dry slice must remain non-executing")
    if safe.get("safe_to_wire_runtime") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_wire_runtime", "safe_to_wire_runtime must remain false")
    if safe.get("final_chat_output") is True or safe.get("live_runtime_output") is True:
        add("runtime_or_persistence_authorization_drift", "$", "dry slice cannot claim final/live runtime output")
    if safe.get("auto_approved") is True or safe.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    side_effects = safe.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    frame = safe.get("frame", {}) if isinstance(safe.get("frame"), Mapping) else {}
    draft = safe.get("draft", {}) if isinstance(safe.get("draft"), Mapping) else {}
    self_check = safe.get("self_check", {}) if isinstance(safe.get("self_check"), Mapping) else {}
    candidate = safe.get("candidate", {}) if isinstance(safe.get("candidate"), Mapping) else {}

    for name, obj in (("frame", frame), ("draft", draft), ("self_check", self_check), ("candidate", candidate)):
        if not obj:
            add("schema", name, f"{name} is required")

    if frame and not validate_native_reasoning_frame_v1(frame).get("valid"):
        add("chain_component", "frame", "frame validation failed")
    if draft and not validate_native_response_draft_v1(draft, frame=frame).get("valid"):
        add("chain_component", "draft", "draft validation failed")
    if self_check and not validate_native_response_self_check_result_v1(self_check).get("valid"):
        add("chain_component", "self_check", "self-check validation failed")
    if candidate and not validate_native_response_candidate_v1(candidate, frame=frame, draft=draft, self_check=self_check).get("valid"):
        add("chain_component", "candidate", "candidate validation failed")

    if draft.get("source_frame_id") != frame.get("frame_id"):
        add("source_id_mismatch", "draft.source_frame_id", "draft does not reference frame")
    if self_check.get("frame_id") != frame.get("frame_id"):
        add("source_id_mismatch", "self_check.frame_id", "self-check does not reference frame")
    if self_check.get("draft_id") != draft.get("draft_id"):
        add("source_id_mismatch", "self_check.draft_id", "self-check does not reference draft")
    if candidate.get("source_frame_id") != frame.get("frame_id"):
        add("source_id_mismatch", "candidate.source_frame_id", "candidate does not reference frame")
    if candidate.get("source_draft_id") != draft.get("draft_id"):
        add("source_id_mismatch", "candidate.source_draft_id", "candidate does not reference draft")
    if candidate.get("source_self_check_id") != self_check.get("self_check_id"):
        add("source_id_mismatch", "candidate.source_self_check_id", "candidate does not reference self-check")
    if candidate.get("self_check_status") != self_check.get("self_check_status"):
        add("source_contradiction", "candidate.self_check_status", "candidate does not reflect self-check status")

    expected_status = _derive_slice_status(frame, draft, self_check, candidate) if frame and draft and self_check and candidate else None
    if expected_status and safe.get("slice_status") != expected_status:
        add("source_contradiction", "slice_status", "slice_status does not reflect chain state")
    if self_check.get("self_check_status") in {"blocked", "revision_required"} and safe.get("safe_to_preview") is True:
        add("source_contradiction", "safe_to_preview", "blocked/revision-required dry slice cannot be preview-safe")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            add("protected_test_or_answer_key", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("forbidden_claims", "cannot_claim", "avoid_claims", "omitted_claims", "safety_notes", "boundary", "capability"))
            if not guardrail_path:
                if _contains_any(value, EXECUTABLE_MARKERS_V1):
                    add("executable_or_runnable_marker", path, "executable/runnable marker is forbidden")
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

    valid = not violations
    return {
        "schema_version": DRY_SLICE_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def summarize_native_response_dry_slice_v1(slice_result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return deterministic count/status summary of a dry slice."""
    safe = _json_safe(slice_result)
    frame = safe.get("frame", {}) if isinstance(safe.get("frame"), Mapping) else {}
    draft = safe.get("draft", {}) if isinstance(safe.get("draft"), Mapping) else {}
    self_check = safe.get("self_check", {}) if isinstance(safe.get("self_check"), Mapping) else {}
    candidate = safe.get("candidate", {}) if isinstance(safe.get("candidate"), Mapping) else {}
    return {
        "slice_id": safe.get("slice_id"),
        "frame_id": frame.get("frame_id"),
        "draft_id": draft.get("draft_id"),
        "self_check_id": self_check.get("self_check_id"),
        "candidate_id": candidate.get("candidate_id"),
        "response_mode": draft.get("response_mode") or candidate.get("response_mode"),
        "self_check_status": self_check.get("self_check_status"),
        "slice_status": safe.get("slice_status"),
        "issue_count": self_check.get("issue_count", 0),
        "safe_to_preview": bool(safe.get("safe_to_preview")),
        "safe_to_wire_runtime": False,
        "missing_context_count": len(_as_list(frame.get("missing_context"))),
        "forbidden_claim_count": len(_as_list(frame.get("forbidden_claims"))) + len(_as_list(candidate.get("omitted_claims"))),
    }


def render_native_response_dry_slice_markdown_v1(slice_result: Mapping[str, Any]) -> str:
    """Render safe deterministic Markdown for dry-slice inspection only."""
    safe = _json_safe(slice_result)
    frame = safe.get("frame", {}) if isinstance(safe.get("frame"), Mapping) else {}
    draft = safe.get("draft", {}) if isinstance(safe.get("draft"), Mapping) else {}
    self_check = safe.get("self_check", {}) if isinstance(safe.get("self_check"), Mapping) else {}
    candidate = safe.get("candidate", {}) if isinstance(safe.get("candidate"), Mapping) else {}
    candidate_preview = render_native_response_candidate_preview_v1(candidate) if candidate else "- none"
    lines = [
        "# Native Response Dry Slice",
        "## Frame Summary",
        f"- frame_id:{_compact(frame.get('frame_id'), 'unknown')}",
        f"- context_status:{_compact(frame.get('context_sufficiency', {}).get('status') if isinstance(frame.get('context_sufficiency'), Mapping) else None, 'unknown')}",
        "## Draft Summary",
        f"- draft_id:{_compact(draft.get('draft_id'), 'unknown')}",
        f"- response_mode:{_compact(draft.get('response_mode'), 'unknown')}",
        "## Self-Check Summary",
        f"- self_check_id:{_compact(self_check.get('self_check_id'), 'unknown')}",
        f"- status:{_compact(self_check.get('self_check_status'), 'unknown')}",
        f"- issues:{self_check.get('issue_count', 0)}",
        "## Candidate Preview",
        candidate_preview,
        "## Safety Boundaries",
        f"- safe_to_preview:{bool(safe.get('safe_to_preview'))}",
        "- safe_to_wire_runtime:false",
        "- no_model_calls:true",
        "- no_persistence:true",
        "## Non-Execution Disclaimer",
        f"- {DRY_SLICE_EXECUTION_STATUS_V1}",
        "- not_final_or_live_runtime_output",
    ]
    return "\n".join(lines)


def to_native_response_dry_slice_json_safe_v1(slice_result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe dry-slice copy; no persistence, no file writes."""
    return _json_safe(slice_result)


__all__ = [
    "DRY_SLICE_TYPE_V1",
    "DRY_SLICE_EXECUTION_STATUS_V1",
    "build_native_response_dry_slice_v1",
    "validate_native_response_dry_slice_v1",
    "summarize_native_response_dry_slice_v1",
    "render_native_response_dry_slice_markdown_v1",
    "to_native_response_dry_slice_json_safe_v1",
]
