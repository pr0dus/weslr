#!/usr/bin/env python3
"""WESLR Frontier Intelligence non-scoring shadow review helpers V1.

Helper-only comparison surface for inspecting an existing live chat response beside
Frontier Intelligence dry-run shadow metadata. This module does not replace live
answers, wire runtime/chat/voice/UI/CLI, call models, score benchmarks, persist
state, or authorize implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping

from weslr.native_reasoning_frame import FORBIDDEN_FIELD_NAMES, FORBIDDEN_TEXT_MARKERS

REVIEW_TYPE_V1 = "frontier_intelligence_shadow_review_v1"
REVIEW_VALIDATION_SCHEMA_V1 = "frontier_intelligence_shadow_review_validation_v1"
REVIEW_EXECUTION_STATUS_V1 = "non_executing_shadow_review_only"

FORBIDDEN_FIELD_NAMES_V1 = set(FORBIDDEN_FIELD_NAMES) | {
    "score",
    "scores",
    "numeric_score",
    "official_score",
    "official_scores",
    "benchmark_score",
    "grade",
    "grades",
    "pass_fail",
    "passed",
    "failed",
    "answer_key",
    "answer_keys",
    "hidden_prompt",
    "hidden_prompts",
}

EXECUTABLE_OR_AUTHORIZATION_MARKERS_V1 = (
    "executable artifact",
    "runnable artifact",
    "run this command",
    "execute this command",
    "runtime wiring authorized",
    "runtime-wired",
    "replace live output",
    "safe to replace live output",
    "sent to user",
    "final live output",
    "public superiority claim",
    "official evaluation",
    "official result",
)

PASS_FAIL_MARKERS_V1 = (
    "pass/fail",
    "passed",
    "failed",
    "grade:",
    "final grade",
    "scored",
    "numeric score",
)

GENERIC_RESPONSE_MARKERS_V1 = (
    "quick steps",
    "top 3 actions",
    "describe the issue",
    "i can help",
    "let me know",
    "what would you like",
    "try a simple plan",
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
        for key in ("summary", "intent_summary", "status", "response_mode", "slice_status", "next_safe_step", "self_check_status"):
            if value.get(key):
                return _compact(value[key], default=default)
    return _compact(str(value), default=default)


def _string_items(value: Any) -> List[str]:
    return [item for item in (_compact(v, "") for v in _as_list(value)) if item]


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


def _existing_content(existing_response: Any) -> str:
    if isinstance(existing_response, str):
        return existing_response
    if isinstance(existing_response, Mapping):
        return _compact(existing_response.get("content") or existing_response.get("reply") or existing_response.get("response"), "")
    return _compact(getattr(existing_response, "content", None), "")


def _preview_card_from_shadow(frontier_shadow_metadata: Any) -> Dict[str, Any]:
    safe = _json_safe(frontier_shadow_metadata or {})
    if not isinstance(safe, Mapping):
        return {}
    card = safe.get("preview_card")
    return card if isinstance(card, dict) else {}


def _candidate_preview_from_card(card: Mapping[str, Any]) -> List[str]:
    return _string_items(card.get("candidate_preview_summary"))


def derive_frontier_shadow_review_findings_v1(existing_response: Any, candidate_or_preview: Any) -> Dict[str, List[str]]:
    """Derive non-scoring shadow review signals from supplied in-memory objects."""
    existing_text = _existing_content(existing_response)
    preview = _json_safe(candidate_or_preview or {})
    if not isinstance(preview, Mapping):
        preview = {}

    findings: Dict[str, List[str]] = {
        "comparison_findings": [],
        "safety_findings": ["runtime_replacement_not_authorized"],
        "improvement_signals": [],
        "regression_signals": [],
        "missing_context_signals": [],
        "capability_boundary_signals": [],
        "evidence_boundary_signals": [],
    }

    if not preview:
        findings["regression_signals"].append("metadata_missing")
        findings["comparison_findings"].append("candidate_not_available")
        return findings

    existing_lower = existing_text.lower()
    if not existing_text:
        findings["comparison_findings"].append("existing_response_missing")
    elif len(existing_text.split()) <= 18 or _contains_any(existing_lower, GENERIC_RESPONSE_MARKERS_V1):
        findings["comparison_findings"].append("existing_response_generic")

    candidate_items = _candidate_preview_from_card(preview)
    if candidate_items:
        findings["comparison_findings"].append("frontier_candidate_preview_available")
    else:
        findings["comparison_findings"].append("candidate_not_available")
        findings["regression_signals"].append("candidate_not_available")

    missing_context = _string_items(preview.get("missing_context_summary"))
    if missing_context:
        findings["missing_context_signals"].append("candidate_has_missing_context_boundary")
        findings["improvement_signals"].append("candidate_surfaces_missing_context_boundary")

    evidence = " ".join(_string_items(preview.get("evidence_summary"))).lower()
    uncertainty = " ".join(_string_items(preview.get("uncertainty_summary"))).lower()
    if evidence or uncertainty:
        findings["evidence_boundary_signals"].append("candidate_has_evidence_boundary")
        findings["improvement_signals"].append("candidate_surfaces_evidence_boundary")
    else:
        findings["regression_signals"].append("candidate_omits_uncertainty")

    next_safe_step = _compact(preview.get("next_safe_step"), "")
    if next_safe_step:
        findings["improvement_signals"].append("candidate_has_next_safe_step")

    capability_text = " ".join(_string_items(preview.get("capability_boundary_summary"))).lower()
    if capability_text:
        findings["capability_boundary_signals"].append("candidate_has_capability_boundary")
    if "can_execute:true" in capability_text or "requires_tool:false" in capability_text and "execute" in " ".join(candidate_items).lower():
        findings["regression_signals"].append("candidate_overclaims_capability")

    encoded_candidate = json.dumps(preview, sort_keys=True).lower()
    if "i remember you personally" in encoded_candidate or "claims_memory_without_context" in encoded_candidate:
        findings["regression_signals"].append("candidate_implies_memory_without_source")

    self_check = preview.get("self_check_summary", {}) if isinstance(preview.get("self_check_summary"), Mapping) else {}
    if _compact(self_check.get("self_check_status"), "").lower() in {"blocked", "revision_required"}:
        findings["safety_findings"].append("candidate_blocked_by_self_check")
        findings["regression_signals"].append("candidate_blocked_by_self_check")

    if preview.get("safe_to_wire_runtime") is True or preview.get("final_chat_output") is True or preview.get("live_runtime_output") is True:
        findings["safety_findings"].append("runtime_authorization_drift_detected")
    else:
        findings["safety_findings"].append("safe_to_wire_runtime_false")

    return {key: list(dict.fromkeys(values)) for key, values in findings.items()}


def _summary_existing_response(existing_response: Any) -> Dict[str, Any]:
    content = _existing_content(existing_response)
    return {
        "available": bool(content),
        "summary": content[:320] if content else "not_supplied",
        "source": "existing_live_chat_response_supplied_to_review_helper",
    }


def _recommendation(shadow_metadata: Mapping[str, Any], findings: Mapping[str, List[str]]) -> str:
    if not shadow_metadata:
        return "insufficient_metadata"
    regressions = set(findings.get("regression_signals", []))
    safety = set(findings.get("safety_findings", []))
    if "candidate_not_available" in regressions or "metadata_missing" in regressions:
        return "insufficient_metadata"
    if "candidate_blocked_by_self_check" in safety or "runtime_authorization_drift_detected" in safety:
        return "candidate_blocked"
    if findings.get("improvement_signals"):
        return "candidate_promising_for_future"
    return "needs_more_review"


def build_frontier_intelligence_shadow_review_v1(existing_response: Any, frontier_shadow_metadata: Any) -> Dict[str, Any]:
    """Build a JSON-safe, non-scoring shadow comparison review object."""
    safe_shadow = _json_safe(frontier_shadow_metadata or {})
    if not isinstance(safe_shadow, Mapping):
        safe_shadow = {}
    preview_card = _preview_card_from_shadow(safe_shadow)
    findings = derive_frontier_shadow_review_findings_v1(existing_response, preview_card)
    preview_summary = safe_shadow.get("preview_summary") if isinstance(safe_shadow.get("preview_summary"), Mapping) else {}
    review = {
        "review_id": _stable_id("fishrv1", {"existing": _summary_existing_response(existing_response), "shadow": safe_shadow}),
        "review_type": REVIEW_TYPE_V1,
        "existing_response_summary": _summary_existing_response(existing_response),
        "frontier_candidate_summary": {
            "available": bool(_candidate_preview_from_card(preview_card)),
            "preview_items": _candidate_preview_from_card(preview_card)[:5],
            "candidate_returned_as_content": False,
        },
        "frontier_preview_summary": {
            "available": bool(preview_card),
            "card_id": preview_card.get("card_id"),
            "card_type": preview_card.get("card_type"),
            "slice_status": preview_card.get("slice_status") or preview_summary.get("slice_status"),
            "safe_to_preview": bool(preview_card.get("safe_to_preview") or preview_summary.get("safe_to_preview")),
            "safe_to_wire_runtime": False,
        },
        "comparison_findings": findings["comparison_findings"],
        "safety_findings": findings["safety_findings"],
        "improvement_signals": findings["improvement_signals"],
        "regression_signals": findings["regression_signals"],
        "missing_context_signals": findings["missing_context_signals"],
        "capability_boundary_signals": findings["capability_boundary_signals"],
        "evidence_boundary_signals": findings["evidence_boundary_signals"],
        "recommendation": _recommendation(safe_shadow, findings),
        "safe_to_replace_live_output": False,
        "safe_to_wire_runtime": False,
        "execution_status": REVIEW_EXECUTION_STATUS_V1,
        "non_replacement_disclaimer": "shadow_review_only_not_scoring_not_grading_not_runtime_wired",
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "ui_or_frontend_integration": False,
            "cli_integration": False,
            "runner": False,
            "scoring_engine": False,
            "numeric_scores": False,
            "pass_fail_grading": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
            "prompt_specific_script": False,
        },
        "validation_status": {"validated": False, "reason": "call_validate_frontier_intelligence_shadow_review_v1"},
    }
    review["validation_status"] = validate_frontier_intelligence_shadow_review_v1(review)
    return to_frontier_intelligence_shadow_review_json_safe_v1(review)


def validate_frontier_intelligence_shadow_review_v1(review: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate review as safe, non-runtime, non-scoring inspection metadata."""
    safe = _json_safe(review)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    if safe.get("review_type") != REVIEW_TYPE_V1:
        add("schema", "review_type", "review_type must be frontier_intelligence_shadow_review_v1")
    if safe.get("safe_to_wire_runtime") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_wire_runtime", "safe_to_wire_runtime must remain false")
    if safe.get("safe_to_replace_live_output") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_replace_live_output", "live output replacement is not authorized")
    if safe.get("auto_approved") is True or safe.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    side_effects = safe.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in (
            "model_calls", "runtime_wiring", "chat_or_voice_changes", "ui_or_frontend_integration", "cli_integration",
            "runner", "scoring_engine", "numeric_scores", "pass_fail_grading", "persistence",
            "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script",
        ):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES_V1:
            add("protected_test_answer_key_score_or_grade", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("non_replacement_disclaimer", "safety_findings", "recommendation", "validation_status"))
            if not guardrail_path:
                if _contains_any(value, EXECUTABLE_OR_AUTHORIZATION_MARKERS_V1):
                    add("executable_or_runtime_replacement_marker", path, "runtime/executable/replacement marker is forbidden")
                if _contains_any(value, PASS_FAIL_MARKERS_V1):
                    add("pass_fail_or_numeric_grading", path, "pass/fail or numeric grading marker is forbidden")
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        add(category, path, f"forbidden marker for {category}")
        elif isinstance(value, Mapping):
            if value.get("claims_memory_without_context") is True:
                add("fake_memory", path, "memory claim without supplied context")
            if value.get("fake_self_awareness_claim") is True:
                add("fake_self_awareness", path, "fake self-awareness claim")
            if value.get("mystical_consciousness_claim") is True or value.get("official_test_passed") is True:
                add("mystical_consciousness_or_official_test_pass_claim", path, "forbidden identity/test claim")
            if value.get("auto_approval") is True or value.get("auto_implementation") is True:
                add("auto_approval_or_auto_implementation", path, "auto approval/implementation is forbidden")
            if value.get("persistence") is True or value.get("weslr_runtime_state_created") is True:
                add("runtime_or_persistence_authorization_drift", path, "persistence/runtime state is forbidden")

    valid = not violations
    return {
        "schema_version": REVIEW_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def render_frontier_intelligence_shadow_review_markdown_v1(review: Mapping[str, Any]) -> str:
    """Render deterministic safe Markdown for shadow review inspection only."""
    safe = _json_safe(review)

    def bullets(values: Any) -> List[str]:
        items = _string_items(values)
        return [f"- {item}" for item in items] if items else ["- none"]

    existing = safe.get("existing_response_summary", {}) if isinstance(safe.get("existing_response_summary"), Mapping) else {}
    candidate = safe.get("frontier_candidate_summary", {}) if isinstance(safe.get("frontier_candidate_summary"), Mapping) else {}
    lines = [
        "# Frontier Intelligence Shadow Review",
        "## Existing Response Summary",
        f"- {_compact(existing.get('summary'), 'not_supplied')}",
        "## Native Candidate Summary",
    ]
    lines.extend(bullets(candidate.get("preview_items")))
    lines.append("## Review Signals")
    lines.extend(bullets(safe.get("comparison_findings")))
    lines.extend(bullets(safe.get("improvement_signals")))
    lines.extend(bullets(safe.get("regression_signals")))
    lines.append("## Safety Findings")
    lines.extend(bullets(safe.get("safety_findings")))
    lines.append("## Recommendation")
    lines.append(f"- {_compact(safe.get('recommendation'), 'needs_more_review')}")
    lines.append("## Non-Replacement Boundary")
    lines.append("- shadow_review_only")
    lines.append("- safe_to_replace_live_output:false")
    lines.append("- safe_to_wire_runtime:false")
    lines.append(f"- {REVIEW_EXECUTION_STATUS_V1}")
    return "\n".join(lines)


def to_frontier_intelligence_shadow_review_json_safe_v1(review: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe review copy; no persistence, no file writes."""
    return _json_safe(review)


__all__ = [
    "REVIEW_TYPE_V1",
    "REVIEW_EXECUTION_STATUS_V1",
    "build_frontier_intelligence_shadow_review_v1",
    "derive_frontier_shadow_review_findings_v1",
    "validate_frontier_intelligence_shadow_review_v1",
    "render_frontier_intelligence_shadow_review_markdown_v1",
    "to_frontier_intelligence_shadow_review_json_safe_v1",
]
