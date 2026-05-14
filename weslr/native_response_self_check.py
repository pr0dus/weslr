#!/usr/bin/env python3
"""WESLR native response self-check helpers V1.

Read-only inspection layer for native response drafts against source reasoning frames.
No runtime wiring, model calls, scoring, persistence, approval, or implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.native_reasoning_frame import FORBIDDEN_FIELD_NAMES, FORBIDDEN_TEXT_MARKERS, validate_native_reasoning_frame_v1
from weslr.native_response_draft import derive_native_response_mode_v1, validate_native_response_draft_v1

SELF_CHECK_TYPE_V1 = "native_response_self_check_v1"
SELF_CHECK_EXECUTION_STATUS_V1 = "non_executing_self_check_only"
ISSUE_EXECUTION_STATUS_V1 = "non_executing_self_check_issue_only"
SELF_CHECK_VALIDATION_SCHEMA_V1 = "native_response_self_check_validation_v1"
SEVERITIES = ("info", "low", "medium", "high")
BLOCKING_TYPES = {
    "capability_overclaim",
    "fake_memory_risk",
    "unsupported_identity_claim",
    "approval_implied",
    "implementation_implied",
    "official_claim_risk",
    "hidden_prompt_or_answer_key_risk",
    "forbidden_claim_present",
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
        for key in ("summary", "status", "explanation", "recommended_revision_action", "issue_type"):
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


def _make_issue(
    *,
    issue_type: str,
    severity: str,
    frame_id: Optional[str],
    draft_id: Optional[str],
    explanation: str,
    recommended_revision_action: str,
) -> Dict[str, Any]:
    seed = {
        "type": issue_type,
        "severity": severity,
        "frame": frame_id,
        "draft": draft_id,
        "explanation": explanation,
        "action": recommended_revision_action,
    }
    return {
        "issue_id": _stable_id("nrsciv1", seed),
        "issue_type": issue_type,
        "severity": severity if severity in SEVERITIES else "medium",
        "related_frame_id": frame_id,
        "related_draft_id": draft_id,
        "explanation": explanation,
        "recommended_revision_action": recommended_revision_action,
        "execution_status": ISSUE_EXECUTION_STATUS_V1,
    }


def _text_blob(value: Any) -> str:
    return json.dumps(_json_safe(value), sort_keys=True, ensure_ascii=True).lower()


def review_native_response_draft_against_frame_v1(draft: Mapping[str, Any], frame: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Inspect a draft against its source frame and return structured issues."""
    safe_draft = _json_safe(draft)
    safe_frame = _json_safe(frame)
    frame_id = safe_frame.get("frame_id")
    draft_id = safe_draft.get("draft_id")
    issues: List[Dict[str, Any]] = []

    def issue(issue_type: str, severity: str, explanation: str, action: str) -> None:
        issues.append(_make_issue(
            issue_type=issue_type,
            severity=severity,
            frame_id=frame_id,
            draft_id=draft_id,
            explanation=explanation,
            recommended_revision_action=action,
        ))

    if safe_draft.get("source_frame_id") != frame_id:
        issue("response_mode_mismatch", "high", "draft source_frame_id does not match frame_id", "rebuild draft from matching source frame")

    expected_mode = derive_native_response_mode_v1(safe_frame)
    if safe_draft.get("response_mode") != expected_mode:
        issue("response_mode_mismatch", "medium", "draft response_mode does not match frame-derived mode", "derive response mode from source frame")

    sufficiency = safe_frame.get("context_sufficiency", {}) if isinstance(safe_frame.get("context_sufficiency"), Mapping) else {}
    boundary = safe_frame.get("capability_boundary", {}) if isinstance(safe_frame.get("capability_boundary"), Mapping) else {}
    memory = safe_frame.get("memory_boundary_status", {}) if isinstance(safe_frame.get("memory_boundary_status"), Mapping) else {}
    missing = _as_list(safe_frame.get("missing_context"))

    if missing and not _as_list(safe_draft.get("missing_context_questions")):
        issue("insufficient_context_not_acknowledged", "medium", "frame missing_context is not reflected in draft", "add missing-context question or boundary note")
    if sufficiency.get("status") == "requires_evidence" and not _as_list(safe_draft.get("evidence_notes")):
        issue("evidence_required_not_acknowledged", "high", "frame requires evidence but draft has no evidence note", "add evidence-required note before preview")
    if sufficiency.get("status") == "requires_evidence" and "evidence" not in _text_blob(safe_draft.get("evidence_notes")):
        issue("missing_evidence_note", "medium", "draft evidence notes do not acknowledge evidence requirement", "state evidence boundary explicitly")
    if sufficiency.get("status") in {"partially_sufficient", "requires_user_clarification", "insufficient", "requires_evidence"} and not _as_list(safe_draft.get("uncertainty_notes")):
        issue("missing_uncertainty_note", "low", "draft lacks uncertainty note for bounded context", "add uncertainty note")
    if not safe_draft.get("next_safe_step"):
        issue("missing_next_safe_step", "medium", "draft lacks next_safe_step", "include next safe step from frame")

    if boundary.get("requires_tool") is True and "requires_tool:true" not in _text_blob(safe_draft.get("capability_notes")):
        issue("missing_boundary_note", "medium", "tool/capability boundary is not reflected", "add capability boundary note")
    if boundary.get("requires_approval") is True and "approval" not in _text_blob(safe_draft.get("approval_note")):
        issue("approval_implied", "high", "approval requirement is missing from draft", "add approval-required note without granting approval")
    if safe_frame.get("approval_required") is True and any(term in _text_blob(safe_draft.get("approval_note")) for term in ["approved", "auto approved", "granted"]):
        issue("approval_implied", "high", "draft appears to imply approval", "replace with approval-required boundary")
    if safe_frame.get("proposal_required") is True and any(term in _text_blob(safe_draft.get("proposal_note")) for term in ["implemented", "auto implemented"]):
        issue("implementation_implied", "high", "draft appears to imply implementation", "replace with proposal-only note")

    if memory.get("memory_claim_requires_supplied_context") is True and "memory_claim_requires_supplied_context" not in _text_blob(safe_draft.get("memory_boundary_note")):
        issue("missing_memory_boundary", "medium", "memory boundary is not reflected", "add memory-boundary honesty note")

    draft_validation = validate_native_response_draft_v1(safe_draft, frame=safe_frame)
    for violation in _as_list(draft_validation.get("violations")):
        category = violation.get("category") if isinstance(violation, Mapping) else "draft_validation"
        path = violation.get("path", "") if isinstance(violation, Mapping) else ""
        # Direct self-check rules above already grade omitted boundary notes; do
        # not escalate those ordinary revision findings into hard blocks.
        if category == "source_frame_contradiction" and path in {"missing_context_questions", "evidence_notes", "approval_note", "capability_notes"}:
            continue
        mapping = {
            "fake_memory": "fake_memory_risk",
            "unsupported_capability": "capability_overclaim",
            "official_iq_benchmark_or_certification": "official_claim_risk",
            "protected_test_or_answer_key": "hidden_prompt_or_answer_key_risk",
            "hidden_prompt_exposure": "hidden_prompt_or_answer_key_risk",
            "auto_approval_or_auto_implementation": "implementation_implied",
            "mystical_consciousness_or_official_test_pass_claim": "unsupported_identity_claim",
            "source_frame_contradiction": "response_mode_mismatch",
        }
        issue(mapping.get(category, "forbidden_claim_present"), "high", _compact(violation), "remove or revise unsafe draft content")

    for path, value in _walk(safe_draft):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            issue("hidden_prompt_or_answer_key_risk", "high", f"forbidden field present at {path}", "remove protected field")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("forbidden_claims_avoided", "capability_notes", "boundary_notes"))
            if not guardrail_path:
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        mapped = {
                            "fake_memory": "fake_memory_risk",
                            "unsupported_capability": "capability_overclaim",
                            "official_iq_benchmark_or_certification": "official_claim_risk",
                            "protected_test_or_answer_key": "hidden_prompt_or_answer_key_risk",
                            "hidden_prompt_exposure": "hidden_prompt_or_answer_key_risk",
                            "auto_approval_or_auto_implementation": "implementation_implied",
                            "mystical_consciousness_or_official_test_pass_claim": "unsupported_identity_claim",
                        }.get(category, "forbidden_claim_present")
                        issue(mapped, "high", f"forbidden marker found at {path}", "remove forbidden claim")
        elif isinstance(value, Mapping):
            if value.get("runtime_capability_claimed") is True or value.get("can_execute") is True:
                issue("capability_overclaim", "high", f"unsupported capability claim at {path}", "remove runtime capability claim")
            if value.get("claims_memory_without_context") is True:
                issue("fake_memory_risk", "high", f"fake memory risk at {path}", "remove unsupported memory claim")
            if value.get("mystical_consciousness_claim") is True or value.get("official_test_passed") is True:
                issue("unsupported_identity_claim", "high", f"unsupported identity/test claim at {path}", "remove unsupported identity claim")

    unique: Dict[str, Dict[str, Any]] = {}
    for item in issues:
        unique[item["issue_id"]] = item
    return list(unique.values())


def build_native_response_self_check_result_v1(frame: Mapping[str, Any], draft: Mapping[str, Any]) -> Dict[str, Any]:
    """Build non-executing self-check result for a frame/draft pair."""
    safe_frame = _json_safe(frame)
    safe_draft = _json_safe(draft)
    issues = review_native_response_draft_against_frame_v1(safe_draft, safe_frame)
    severity_counts = {severity: 0 for severity in SEVERITIES}
    type_counts: Dict[str, int] = {}
    for issue in issues:
        severity_counts[issue["severity"]] = severity_counts.get(issue["severity"], 0) + 1
        type_counts[issue["issue_type"]] = type_counts.get(issue["issue_type"], 0) + 1

    high_count = severity_counts.get("high", 0)
    medium_count = severity_counts.get("medium", 0)
    low_count = severity_counts.get("low", 0)
    blocking = any(issue["issue_type"] in BLOCKING_TYPES or issue["severity"] == "high" for issue in issues)
    if blocking:
        status = "blocked"
    elif medium_count:
        status = "revision_required"
    elif low_count:
        status = "warnings_present"
    else:
        status = "acceptable"

    safe_to_preview = status in {"acceptable", "warnings_present"}
    actions = list(dict.fromkeys(issue["recommended_revision_action"] for issue in issues))
    result_seed = {"frame": safe_frame.get("frame_id"), "draft": safe_draft.get("draft_id"), "issues": [i["issue_id"] for i in issues]}
    result: Dict[str, Any] = {
        "self_check_id": _stable_id("nrscv1", result_seed),
        "self_check_type": SELF_CHECK_TYPE_V1,
        "frame_id": safe_frame.get("frame_id"),
        "draft_id": safe_draft.get("draft_id"),
        "issue_count": len(issues),
        "issues": issues,
        "issue_counts_by_severity": severity_counts,
        "issue_counts_by_type": type_counts,
        "self_check_status": status,
        "recommended_revision_actions": actions,
        "safe_to_preview": safe_to_preview,
        "safe_to_wire_runtime": False,
        "execution_status": SELF_CHECK_EXECUTION_STATUS_V1,
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
        "validation_status": {"validated": False, "reason": "call_validate_native_response_self_check_result_v1"},
    }
    result["validation_status"] = validate_native_response_self_check_result_v1(result)
    return to_native_response_self_check_json_safe_v1(result)


def validate_native_response_self_check_result_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate self-check result safety and non-runtime boundary."""
    safe = _json_safe(result)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe.get("self_check_type") != SELF_CHECK_TYPE_V1:
        add("schema", "self_check_type", "self_check_type must be native_response_self_check_v1")
    if safe.get("execution_status") != SELF_CHECK_EXECUTION_STATUS_V1:
        add("execution", "execution_status", "self-check must remain non-executing")
    if safe.get("safe_to_wire_runtime") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_wire_runtime", "safe_to_wire_runtime must remain false in this phase")
    if safe.get("auto_approved") is True or safe.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    side_effects = safe.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES:
            add("hidden_prompt_or_answer_key_risk", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("issue_type", "recommended_revision_action", "issue_counts_by_type", "Safety Boundaries"))
            if not guardrail_path:
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        mapped = {
                            "fake_memory": "fake_memory_risk",
                            "unsupported_capability": "capability_overclaim",
                            "official_iq_benchmark_or_certification": "official_claim_risk",
                            "protected_test_or_answer_key": "hidden_prompt_or_answer_key_risk",
                            "hidden_prompt_exposure": "hidden_prompt_or_answer_key_risk",
                            "auto_approval_or_auto_implementation": "implementation_implied",
                            "mystical_consciousness_or_official_test_pass_claim": "unsupported_identity_claim",
                        }.get(category, "forbidden_claim_present")
                        add(mapped, path, f"forbidden marker for {category}")
        elif isinstance(value, Mapping):
            if value.get("runtime_capability_claimed") is True or value.get("can_execute") is True:
                add("capability_overclaim", path, "unsupported capability claim")
            if value.get("claims_memory_without_context") is True:
                add("fake_memory_risk", path, "fake memory risk")
            if value.get("mystical_consciousness_claim") is True or value.get("official_test_passed") is True:
                add("unsupported_identity_claim", path, "unsupported identity/test claim")

    valid = not violations
    return {
        "schema_version": SELF_CHECK_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def summarize_native_response_self_check_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return compact deterministic summary of a self-check result."""
    safe = _json_safe(result)
    return {
        "self_check_id": safe.get("self_check_id"),
        "frame_id": safe.get("frame_id"),
        "draft_id": safe.get("draft_id"),
        "self_check_status": safe.get("self_check_status"),
        "issue_count": safe.get("issue_count", 0),
        "issue_counts_by_severity": safe.get("issue_counts_by_severity", {}),
        "issue_counts_by_type": safe.get("issue_counts_by_type", {}),
        "safe_to_preview": bool(safe.get("safe_to_preview")),
        "safe_to_wire_runtime": False,
        "execution_status": safe.get("execution_status"),
        "recommended_revision_action_count": len(_as_list(safe.get("recommended_revision_actions"))),
        "validation_status": validate_native_response_self_check_result_v1(safe)["validation_status"],
    }


def render_native_response_self_check_markdown_v1(result: Mapping[str, Any]) -> str:
    """Render deterministic markdown summary for inspection only."""
    safe = _json_safe(result)
    lines = [
        "# Native Response Self-Check",
        "## Status",
        f"- {safe.get('self_check_status', 'unknown')}",
        f"- issues:{safe.get('issue_count', 0)}",
        "## Issues",
    ]
    issues = _as_list(safe.get("issues"))
    if not issues:
        lines.append("- none")
    else:
        for item in issues:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('severity')}:{item.get('issue_type')}:{_compact(item.get('explanation'))}")
    lines.append("## Recommended Revision Actions")
    actions = _as_list(safe.get("recommended_revision_actions"))
    lines.extend([f"- {_compact(action)}" for action in actions] or ["- none"])
    lines.append("## Safety Boundaries")
    lines.append(f"- safe_to_preview:{bool(safe.get('safe_to_preview'))}")
    lines.append("- safe_to_wire_runtime:false")
    lines.append("## Non-Execution Disclaimer")
    lines.append(f"- {SELF_CHECK_EXECUTION_STATUS_V1}")
    return "\n".join(lines)


def to_native_response_self_check_json_safe_v1(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Return JSON-safe self-check copy; no persistence, no file writes."""
    return _json_safe(result)


__all__ = [
    "SELF_CHECK_TYPE_V1",
    "SELF_CHECK_EXECUTION_STATUS_V1",
    "ISSUE_EXECUTION_STATUS_V1",
    "review_native_response_draft_against_frame_v1",
    "build_native_response_self_check_result_v1",
    "validate_native_response_self_check_result_v1",
    "summarize_native_response_self_check_v1",
    "render_native_response_self_check_markdown_v1",
    "to_native_response_self_check_json_safe_v1",
]
