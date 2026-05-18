#!/usr/bin/env python3
"""WESLR ranked state-grounded response shadow helpers V1.

Pure, in-memory structural helpers for inspecting future ranked response
formation artifacts. This module is helper-only and shadow-only: it does not
wire runtime chat/voice, generate final answers, call models/search/advisors,
execute prompts, persist state, write files, use subprocesses, or make network
calls.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import Any

HELPER_NAME_V1 = "ranked_state_grounded_response_shadow_v1"
SCHEMA_VERSION_V1 = "ranked_state_grounded_response_shadow_schema_v1"

READINESS_LABELS_V1 = [
    "ranked_response_shadow_helpers_defined",
    "shadow_only_not_runtime_wired",
    "final_answer_not_generated",
    "raw_prompt_response_not_retained",
    "qualitative_ranking_only",
    "model_search_advisor_not_called",
    "persistence_not_performed",
    "official_evaluation_not_claimed",
    "voice_downstream_not_current_priority",
]

QUALITATIVE_LABELS_V1 = {
    "strong_fit",
    "acceptable_fit",
    "weak_fit",
    "reject",
    "needs_clarification",
    "needs_evidence",
    "needs_governance",
    "not_authorized",
}

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "raw_prompt",
    "prompt_text",
    "response_text",
    "raw_response",
    "final_answer",
    "final_answer_text",
    "full_conversation",
    "hidden_prompt",
    "answer_key",
    "official_score",
    "iq_score",
    "turing_passed",
    "benchmark_certified",
}

TRUE_FORBIDDEN_FLAG_KEYS_V1 = {
    "runtime_wired": "runtime_wired_true",
    "model_call_made": "model_call_made_true",
    "search_call_made": "search_call_made_true",
    "advisor_call_made": "advisor_call_made_true",
    "persistence_performed": "persistence_performed_true",
    "final_answer_generated": "final_answer_generated_true",
    "raw_prompt_retained": "raw_prompt_retained_true",
    "raw_response_retained": "raw_response_retained_true",
}

OFFICIAL_CLAIM_MARKERS_V1 = {
    "official benchmark",
    "official score",
    "passed turing",
    "turing passed",
    "certified intelligence",
    "certification ready",
    "product readiness certified",
    "product-ready certified",
    "iq score",
    "official iq",
}

CONSCIOUSNESS_MARKERS_V1 = {
    "weslr is conscious",
    "weslr is sentient",
    "i am conscious",
    "i am sentient",
    "consciousness proven",
    "sentience proven",
}

OCC_AS_WESLR_MARKERS_V1 = {
    "occ is weslr",
    "openclaw is weslr",
    "occ/openclaw is weslr",
    "occ is part of deployed weslr",
    "openclaw is part of deployed weslr",
}

REJECT_SAFETY_LABELS_V1 = {"unsafe", "blocked", "violation", "fail", "failed", "high_risk"}
REJECT_EVIDENCE_LABELS_V1 = {"insufficient", "missing", "unsupported", "fail", "failed", "required_missing"}
REJECT_PROVENANCE_LABELS_V1 = {"missing", "failed", "fail", "unclear", "unattributed"}
REJECT_DOMAIN_LABELS_V1 = {"violation", "failed", "fail", "outside_scope", "blocked"}
CANNED_LABELS_V1 = {"canned", "template", "keyword_only", "fixed_paragraph", "scripted", "low"}


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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _safe_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return _drop_forbidden_keys(_json_safe(value))[0]
    return {"summary": _compact(value)}


def _compact(value: Any, default: str = "not_supplied") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, Mapping):
        for key in ("summary", "status", "label", "intent", "shape", "need", "boundary"):
            if value.get(key):
                return _compact(value[key], default=default)
    return _compact(str(value), default=default)


def _norm_label(value: Any, default: str = "not_supplied") -> str:
    return _compact(value, default=default).lower().replace(" ", "_").replace("-", "_")


def _drop_forbidden_keys(value: Any, path: str = "") -> tuple[Any, list[str]]:
    dropped: list[str] = []
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_s = str(key)
            key_l = key_s.lower()
            child_path = f"{path}.{key_s}" if path else key_s
            if key_l in FORBIDDEN_KEYS_V1:
                dropped.append(child_path)
                continue
            child, child_dropped = _drop_forbidden_keys(item, child_path)
            dropped.extend(child_dropped)
            clean[key_s] = child
        return clean, dropped
    if isinstance(value, list):
        clean_list = []
        for idx, item in enumerate(value):
            child, child_dropped = _drop_forbidden_keys(item, f"{path}[{idx}]")
            dropped.extend(child_dropped)
            clean_list.append(child)
        return clean_list, dropped
    if isinstance(value, tuple):
        return _drop_forbidden_keys(list(value), path)
    if isinstance(value, set):
        return _drop_forbidden_keys(sorted(value, key=repr), path)
    return _json_safe(value), dropped


def _walk(obj: Any, path: str = ""):
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_s = str(key)
            next_path = f"{path}.{key_s}" if path else key_s
            yield next_path, value
            yield from _walk(value, next_path)
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            next_path = f"{path}[{idx}]"
            yield next_path, value
            yield from _walk(value, next_path)


def _contains_any_label(value: Any, labels: set[str]) -> bool:
    values = [_norm_label(item) for item in _as_list(value)]
    return any(any(label in item for label in labels) for item in values)


def _text_blob(obj: Any) -> str:
    try:
        return json.dumps(_json_safe(obj), sort_keys=True, ensure_ascii=True).lower()
    except Exception:
        return repr(obj).lower()


def _base_metadata() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_name": HELPER_NAME_V1,
        "runtime_wired": False,
        "shadow_only": True,
        "final_answer_generated": False,
        "raw_prompt_retained": False,
        "raw_response_retained": False,
        "model_call_made": False,
        "search_call_made": False,
        "advisor_call_made": False,
        "persistence_performed": False,
        "readiness_labels": list(READINESS_LABELS_V1),
    }


def build_response_state_frame_v1(
    *,
    user_turn_interpretation: Any = None,
    inferred_need: Any = None,
    uncertainty: Any = None,
    task_type: Any = None,
    domain_context: Any = None,
    relationship_context: Any = None,
    memory_relevance: Any = None,
    continuity_relevance: Any = None,
    evidence_requirement: Any = None,
    provenance_requirement: Any = None,
    capability_boundary: Any = None,
    safety_boundary: Any = None,
    legal_moral_boundary: Any = None,
    response_obligation: Any = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    """Build an in-memory response state frame from safe metadata inputs."""

    sanitized_extra, dropped = _drop_forbidden_keys(_json_safe(extra_fields))
    frame = {
        **_base_metadata(),
        "artifact_type": "response_state_frame_v1",
        "user_turn_interpretation": _safe_mapping(user_turn_interpretation),
        "inferred_need": _safe_mapping(inferred_need),
        "uncertainty": _safe_mapping(uncertainty),
        "task_type": _compact(task_type),
        "domain_context": _safe_mapping(domain_context),
        "relationship_context": _safe_mapping(relationship_context),
        "memory_relevance": _safe_mapping(memory_relevance),
        "continuity_relevance": _safe_mapping(continuity_relevance),
        "evidence_requirement": _safe_mapping(evidence_requirement),
        "provenance_requirement": _safe_mapping(provenance_requirement),
        "capability_boundary": _safe_mapping(capability_boundary),
        "safety_boundary": _safe_mapping(safety_boundary),
        "legal_moral_boundary": _safe_mapping(legal_moral_boundary),
        "response_obligation": _safe_mapping(response_obligation),
        "candidate_responses": [],
        "ranking_trace": [],
        "post_response_observation": {},
        "sanitized_forbidden_input_fields": dropped,
    }
    if sanitized_extra:
        frame["safe_extra_metadata"] = sanitized_extra
    return frame


def build_candidate_response_v1(
    *,
    candidate_id: Any = None,
    candidate_type: Any = None,
    source_basis: Any = None,
    intended_response_shape: Any = None,
    grounding_notes: Any = None,
    evidence_fit: Any = None,
    provenance_fit: Any = None,
    domain_fit: Any = None,
    continuity_fit: Any = None,
    safety_fit: Any = None,
    uncertainty_handling: Any = None,
    actionability: Any = None,
    non_cannedness: Any = None,
    requires_model_call: bool = False,
    requires_search_call: bool = False,
    requires_advisor_call: bool = False,
    requires_governance: bool = False,
    risk_labels: Any = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    """Create a metadata-only candidate response structure."""

    sanitized_extra, dropped = _drop_forbidden_keys(_json_safe(extra_fields))
    candidate = {
        **_base_metadata(),
        "artifact_type": "candidate_response_v1",
        "candidate_id": _compact(candidate_id, default="candidate_unspecified"),
        "candidate_type": _compact(candidate_type, default="unspecified_candidate"),
        "source_basis": _safe_mapping(source_basis),
        "intended_response_shape": _safe_mapping(intended_response_shape),
        "grounding_notes": _as_list(grounding_notes),
        "evidence_fit": _compact(evidence_fit, default="unknown"),
        "provenance_fit": _compact(provenance_fit, default="unknown"),
        "domain_fit": _compact(domain_fit, default="unknown"),
        "continuity_fit": _compact(continuity_fit, default="unknown"),
        "safety_fit": _compact(safety_fit, default="unknown"),
        "uncertainty_handling": _compact(uncertainty_handling, default="unknown"),
        "actionability": _compact(actionability, default="unknown"),
        "non_cannedness": _compact(non_cannedness, default="unknown"),
        "requires_model_call": bool(requires_model_call),
        "requires_search_call": bool(requires_search_call),
        "requires_advisor_call": bool(requires_advisor_call),
        "requires_governance": bool(requires_governance),
        "risk_labels": [str(item) for item in _as_list(risk_labels)],
        "final_answer_text_present": False,
        "sanitized_forbidden_input_fields": dropped,
    }
    if sanitized_extra:
        candidate["safe_extra_metadata"] = sanitized_extra
    return candidate


def _requirement_label(state_frame: Mapping[str, Any], key: str) -> str:
    value = state_frame.get(key, {})
    return _norm_label(value)


def _evidence_required(state_frame: Mapping[str, Any]) -> bool:
    label = _requirement_label(state_frame, "evidence_requirement")
    return any(part in label for part in ("required", "needs", "sufficiency", "evidence")) and "not_required" not in label


def _provenance_required(state_frame: Mapping[str, Any]) -> bool:
    label = _requirement_label(state_frame, "provenance_requirement")
    return any(part in label for part in ("required", "needs", "provenance", "attribute")) and "not_required" not in label


def classify_candidate_rejection_v1(candidate: dict, state_frame: dict) -> dict[str, Any]:
    """Explain why a candidate is rejected or not rejected."""

    reason_labels: list[str] = []
    boundary_labels: list[str] = []

    if candidate.get("requires_model_call"):
        reason_labels.append("unauthorized_model_call_required")
        boundary_labels.append("model_boundary")
    if candidate.get("requires_search_call"):
        reason_labels.append("unauthorized_search_call_required")
        boundary_labels.append("search_boundary")
    if candidate.get("requires_advisor_call"):
        reason_labels.append("unauthorized_advisor_call_required")
        boundary_labels.append("advisor_boundary")
    if candidate.get("requires_governance"):
        reason_labels.append("governance_required")
        boundary_labels.append("governance_boundary")

    if _contains_any_label(candidate.get("safety_fit"), REJECT_SAFETY_LABELS_V1) or _contains_any_label(candidate.get("risk_labels"), REJECT_SAFETY_LABELS_V1 | {"overclaim", "unsafe"}):
        reason_labels.append("unsafe_candidate")
        boundary_labels.append("safety_boundary")
    if _contains_any_label(candidate.get("risk_labels"), {"overclaim", "unsupported_claim", "capability_overreach"}):
        reason_labels.append("overclaim_or_capability_overreach")
        boundary_labels.append("capability_boundary")
    if _evidence_required(state_frame) and _contains_any_label(candidate.get("evidence_fit"), REJECT_EVIDENCE_LABELS_V1 | {"unknown"}):
        reason_labels.append("required_evidence_not_satisfied")
        boundary_labels.append("evidence_boundary")
    if _provenance_required(state_frame) and _contains_any_label(candidate.get("provenance_fit"), REJECT_PROVENANCE_LABELS_V1 | {"unknown"}):
        reason_labels.append("required_provenance_not_satisfied")
        boundary_labels.append("provenance_boundary")
    if _contains_any_label(candidate.get("domain_fit"), REJECT_DOMAIN_LABELS_V1):
        reason_labels.append("domain_or_legal_moral_boundary_violation")
        boundary_labels.append("domain_boundary")
    if _contains_any_label(candidate.get("risk_labels"), {"legal_violation", "moral_violation"}):
        reason_labels.append("legal_or_moral_boundary_violation")
        boundary_labels.append("legal_moral_boundary")
    if _contains_any_label(candidate.get("non_cannedness"), CANNED_LABELS_V1):
        reason_labels.append("canned_template_like_candidate")
        boundary_labels.append("non_cannedness_boundary")

    reason_labels = sorted(set(reason_labels))
    boundary_labels = sorted(set(boundary_labels))
    return {
        **_base_metadata(),
        "artifact_type": "candidate_rejection_classification_v1",
        "candidate_id": candidate.get("candidate_id", "candidate_unspecified"),
        "rejected": bool(reason_labels),
        "reason_labels": reason_labels,
        "boundary_labels": boundary_labels,
        "safe_fallback_needed": bool(reason_labels),
        "governance_needed": "governance_required" in reason_labels,
        "evidence_needed": "required_evidence_not_satisfied" in reason_labels,
    }


def _positive_fit_count(candidate: Mapping[str, Any]) -> int:
    fields = ("evidence_fit", "provenance_fit", "domain_fit", "continuity_fit", "safety_fit", "uncertainty_handling", "actionability", "non_cannedness")
    positives = {"strong", "strong_fit", "sufficient", "clear", "safe", "good", "bounded", "state_grounded", "high", "actionable"}
    total = 0
    for field in fields:
        label = _norm_label(candidate.get(field))
        if any(pos in label for pos in positives):
            total += 1
    return total


def _label_for_candidate(candidate: Mapping[str, Any], classification: Mapping[str, Any]) -> str:
    if classification.get("rejected"):
        reasons = set(classification.get("reason_labels", []))
        if any(reason.startswith("unauthorized_") for reason in reasons):
            return "not_authorized"
        if "governance_required" in reasons:
            return "needs_governance"
        if "required_evidence_not_satisfied" in reasons:
            return "needs_evidence"
        return "reject"
    count = _positive_fit_count(candidate)
    if count >= 6:
        return "strong_fit"
    if count >= 3:
        return "acceptable_fit"
    return "weak_fit"


def rank_candidate_responses_v1(state_frame: dict, candidates: list[dict]) -> dict[str, Any]:
    """Return qualitative ranking trace and selected candidate metadata."""

    trace: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_label = "reject"
    label_order = {"strong_fit": 4, "acceptable_fit": 3, "weak_fit": 2, "needs_clarification": 1, "needs_evidence": 0, "needs_governance": 0, "not_authorized": 0, "reject": 0}

    for candidate in candidates:
        classification = classify_candidate_rejection_v1(candidate, state_frame)
        label = _label_for_candidate(candidate, classification)
        item = {
            "candidate_id": candidate.get("candidate_id", "candidate_unspecified"),
            "label": label,
            "rejected": bool(classification["rejected"]),
            "reason_labels": list(classification["reason_labels"]),
            "boundary_labels": list(classification["boundary_labels"]),
            "qualitative_fit_notes": {
                "positive_fit_count": _positive_fit_count(candidate),
                "qualitative_only": True,
                "official_score_claimed": False,
            },
        }
        trace.append(item)
        if not item["rejected"] and (selected is None or label_order[label] > label_order[selected_label]):
            selected = candidate
            selected_label = label

    rejected_ids = [item["candidate_id"] for item in trace if item["rejected"]]
    result = {
        **_base_metadata(),
        "artifact_type": "candidate_ranking_result_v1",
        "ranking_trace": trace,
        "selected_candidate_id": selected.get("candidate_id") if selected else None,
        "selected_label": selected_label if selected else "reject",
        "rejected_candidate_ids": rejected_ids,
        "selection_rationale": "selected highest qualitative non-rejected fit" if selected else "no safe candidate selected; safe fallback required",
        "candidate_count": len(candidates),
        "qualitative_ranking_only": True,
        "official_score_claimed": False,
    }
    return result


def self_check_selected_candidate_v1(state_frame: dict, selected_candidate: dict, ranking_result: dict) -> dict[str, Any]:
    """Perform structural self-check before future final-answer composition."""

    issues: list[str] = []
    for name, artifact in (("state_frame", state_frame), ("selected_candidate", selected_candidate), ("ranking_result", ranking_result)):
        validation = validate_ranked_response_shadow_artifact_v1(artifact)
        if not validation["valid"]:
            issues.extend(f"{name}:{reason}" for reason in validation["reason_labels"])

    if selected_candidate.get("final_answer_text_present"):
        issues.append("selected_candidate_final_answer_text_present")
    if ranking_result.get("selected_candidate_id") != selected_candidate.get("candidate_id"):
        issues.append("selected_candidate_mismatch")
    if ranking_result.get("selected_label") not in QUALITATIVE_LABELS_V1:
        issues.append("unknown_selected_label")
    if ranking_result.get("selected_label") in {"reject", "not_authorized", "needs_evidence", "needs_governance"}:
        issues.append("selected_label_not_ready_for_final_composition")

    return {
        **_base_metadata(),
        "artifact_type": "selected_candidate_self_check_v1",
        "valid": not issues,
        "passed": not issues,
        "issue_labels": sorted(set(issues)),
        "selected_candidate_id": selected_candidate.get("candidate_id"),
        "selected_label": ranking_result.get("selected_label"),
        "final_answer_text_present": bool(selected_candidate.get("final_answer_text_present")),
    }


def build_final_answer_contract_metadata_v1(state_frame: dict, selected_candidate: dict, self_check: dict) -> dict[str, Any]:
    """Build metadata describing future final-answer constraints without prose."""

    return {
        **_base_metadata(),
        "artifact_type": "final_answer_contract_metadata_v1",
        "allowed_response_shape": selected_candidate.get("intended_response_shape", {}),
        "required_uncertainty_notes": state_frame.get("uncertainty", {}),
        "required_provenance_notes": state_frame.get("provenance_requirement", {}),
        "forbidden_claims": [
            "official_benchmark_claim",
            "turing_test_claim",
            "iq_claim",
            "certification_claim",
            "product_readiness_claim",
            "consciousness_claim",
            "sentience_claim",
            "occ_as_weslr_claim",
        ],
        "boundary_notes": {
            "capability_boundary": state_frame.get("capability_boundary", {}),
            "safety_boundary": state_frame.get("safety_boundary", {}),
            "legal_moral_boundary": state_frame.get("legal_moral_boundary", {}),
            "self_check_passed": bool(self_check.get("passed")),
        },
        "final_answer_generated": False,
        "final_answer_text_present": False,
    }


def validate_ranked_response_shadow_artifact_v1(artifact: dict) -> dict[str, Any]:
    """Validate a ranked response shadow artifact for safe inspection."""

    reasons: list[str] = []
    if not isinstance(artifact, Mapping):
        return {"valid": False, "reason_labels": ["artifact_not_mapping"], "safe_to_inspect": False, **_base_metadata()}

    for path, value in _walk(artifact):
        key = path.split(".")[-1].split("[")[0].lower()
        if key in FORBIDDEN_KEYS_V1:
            reasons.append(f"forbidden_key:{key}")
        if key in TRUE_FORBIDDEN_FLAG_KEYS_V1 and value is True:
            reasons.append(TRUE_FORBIDDEN_FLAG_KEYS_V1[key])
        if key in {"official_score", "iq_score"} and isinstance(value, (int, float)):
            reasons.append("numeric_official_score_present")

    blob = _text_blob(artifact)
    if any(marker in blob for marker in OFFICIAL_CLAIM_MARKERS_V1):
        reasons.append("official_claim_marker_present")
    if any(marker in blob for marker in CONSCIOUSNESS_MARKERS_V1):
        reasons.append("consciousness_or_sentience_claim_marker_present")
    if any(marker in blob for marker in OCC_AS_WESLR_MARKERS_V1):
        reasons.append("occ_as_weslr_claim_marker_present")

    reasons = sorted(set(reasons))
    return {
        **_base_metadata(),
        "artifact_type": "ranked_response_shadow_validation_v1",
        "valid": not reasons,
        "reason_labels": reasons,
        "safe_to_inspect": not reasons,
    }


def to_ranked_response_shadow_json_safe_v1(artifact: dict) -> dict[str, Any]:
    """Return a JSON-safe copy, rejecting unsafe artifacts instead of sanitizing them."""

    validation = validate_ranked_response_shadow_artifact_v1(artifact)
    if not validation["valid"]:
        return {
            **_base_metadata(),
            "artifact_type": "ranked_response_shadow_json_safe_rejection_v1",
            "valid": False,
            "artifact_rejected": True,
            "validation": validation,
        }
    safe = _json_safe(artifact)
    safe["validation"] = validation
    return safe


def summarize_ranked_response_shadow_v1(artifact: dict) -> dict[str, Any]:
    """Return count/status-only summary with no raw content."""

    validation = validate_ranked_response_shadow_artifact_v1(artifact)
    ranking_trace = artifact.get("ranking_trace", []) if isinstance(artifact, Mapping) else []
    candidates = artifact.get("candidate_responses", []) if isinstance(artifact, Mapping) else []
    rejected_count = len([item for item in ranking_trace if isinstance(item, Mapping) and item.get("rejected")])
    return {
        **_base_metadata(),
        "artifact_type": "ranked_response_shadow_summary_v1",
        "number_of_candidates": int(artifact.get("candidate_count", len(candidates) or len(ranking_trace))) if isinstance(artifact, Mapping) else 0,
        "selected_label": artifact.get("selected_label") if isinstance(artifact, Mapping) else None,
        "rejected_count": rejected_count,
        "validation_status": "valid" if validation["valid"] else "invalid",
        "validation_reason_count": len(validation["reason_labels"]),
        "readiness_labels": list(READINESS_LABELS_V1),
        "raw_content_included": False,
    }


def render_ranked_response_shadow_markdown_v1(artifact: dict) -> str:
    """Render a safe markdown summary for review."""

    summary = summarize_ranked_response_shadow_v1(artifact)
    validation = validate_ranked_response_shadow_artifact_v1(artifact)
    lines = [
        "# Ranked Response Shadow Summary",
        "",
        f"- artifact_type: `{artifact.get('artifact_type', 'unknown') if isinstance(artifact, Mapping) else 'invalid'}`",
        f"- candidates: `{summary['number_of_candidates']}`",
        f"- selected_label: `{summary.get('selected_label')}`",
        f"- rejected_count: `{summary['rejected_count']}`",
        f"- validation_status: `{summary['validation_status']}`",
        f"- safe_to_inspect: `{validation['safe_to_inspect']}`",
        "- final_answer_generated: `False`",
        "- raw_prompt_response_retained: `False`",
        "- runtime_wired: `False`",
        "",
        "## Readiness Labels",
    ]
    lines.extend(f"- `{label}`" for label in READINESS_LABELS_V1)
    if validation["reason_labels"]:
        lines.append("")
        lines.append("## Validation Reasons")
        lines.extend(f"- `{reason}`" for reason in validation["reason_labels"])
    return "\n".join(lines)
