"""Metadata-only response fit self-check v1.

This layer evaluates formed candidate response paths before any renderer
could produce user-facing prose. It is pure, deterministic, import-safe,
and fail-closed.

No model/provider calls. No runtime wiring. No state writes. No final prose.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from weslr.candidate_response_formation import (
    CandidateResponseFormationPacket,
    CandidateResponsePath,
    form_candidate_responses_v1,
    summarize_candidate_response_formation_packet_v1,
    to_candidate_response_formation_json_safe_v1,
)
from weslr.response_fit_engine_helpers import CHECK_LABELS_V1

PACKET_TYPE_V1 = "response_fit_self_check_v1"
SUMMARY_TYPE_V1 = "response_fit_self_check_summary_v1"

FIT_STATUSES_V1 = {
    "fit",
    "fit_with_boundaries",
    "needs_revision",
    "needs_clarification",
    "needs_evidence",
    "needs_owner_approval",
    "blocked",
    "unknown_friction",
}

RECOMMENDED_NEXT_ACTIONS_V1 = {
    "render_bounded_answer_later",
    "ask_clarifying_question_later",
    "request_evidence_later",
    "render_partial_supported_answer_later",
    "render_refusal_boundary_later",
    "route_unknown_friction_later",
    "escalate_owner_review_later",
    "block_no_render",
}

MISMATCH_LABELS_V1 = {
    "too_generic",
    "too_verbose",
    "too_technical",
    "too_simple",
    "wrong_urgency",
    "wrong_risk_posture",
    "fake_empathy",
    "missed_emotional_pressure",
    "ignored_correction",
    "lost_continuity",
    "evidence_depth_mismatch",
    "jargon_mismatch",
    "actionability_mismatch",
    "answer_shape_mismatch",
    "industry_context_mismatch",
    "human_perceived_ai_tone",
}

QUALITY_PRESSURE_LABELS_V1 = {
    *MISMATCH_LABELS_V1,
    "canned_template_risk",
    "authority_drift_risk",
    "unsupported_claim_risk",
    "final_text_too_early",
}

SELF_CHECK_LABELS_V1 = {
    *CHECK_LABELS_V1,
    "fit_before_render_check",
    "candidate_ranking_check",
    "authority_drift_check",
    "final_text_too_early_check",
    "raw_prompt_leak_check",
}

_RAW_LEAK_LABELS_V1 = {
    "raw_prompt_provided",
    "raw_response_text_provided",
    "raw_transcript_provided",
    "raw_context_provided",
    "raw_private_content_requested",
    "raw_persistence_requested",
    "private_memory_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
}

_AUTHORITY_BLOCK_LABELS_V1 = {
    "public_live_authority_requested",
    "public_ux_authority_requested",
    "voice_authority_requested",
    "runtime_authority_requested",
    "live_runtime_authority_requested",
    "model_call_authority_requested",
    "search_call_authority_requested",
    "advisor_call_authority_requested",
    "final_answer_authority_requested",
    "official_claim_requested",
    "turing_claim_requested",
    "intelligence_claim_requested",
    "certification_claim_requested",
    "public_readiness_authority_requested",
    "voice_readiness_authority_requested",
    "live_user_safety_readiness_authority_requested",
    "benchmark_score_authority_requested",
    "model_superiority_authority_requested",
    "raw_persistence_authority_requested",
    "private_memory_authority_requested",
    "unknown_engine_authority_requested",
    "automatic_lesson_promotion_requested",
}

_FORBIDDEN_INPUT_KEYS_V1 = {
    *(_RAW_LEAK_LABELS_V1),
    "raw_prompt_text",
    "prompt_text",
    "raw_response_text",
    "response_text",
    "final_answer_text",
    "final_answer_prose",
    "answer_draft_text",
    "composed_reply_text",
    "live_dialogue_transcript",
    "live_dialogue_transcript_content",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "answer_key",
    "private_content",
    "hidden_prompt",
}

_CANDIDATE_PRIORITY_V1 = {
    "refusal_boundary_candidate": 100,
    "clarification_candidate": 96,
    "evidence_needed_candidate": 95,
    "governance_escalation_candidate": 94,
    "unknown_friction_candidate": 93,
    "continuity_recap_candidate": 92,
    "memory_honesty_candidate": 91,
    "correction_repair_candidate": 90,
    "relationship_feedback_candidate": 89,
    "conflict_contradiction_candidate": 88,
    "non_canned_specificity_candidate": 87,
    "directness_concern_candidate": 86,
    "benchmark_evaluation_candidate": 85,
    "scientific_discovery_guidance_candidate": 84,
    "implementation_plan_candidate": 83,
    "workflow_next_lane_candidate": 82,
    "teaching_explanation_candidate": 81,
    "language_discovery_candidate": 80,
    "stepwise_plan_candidate": 79,
    "partial_supported_candidate": 78,
    "bounded_uncertainty_candidate": 77,
    "direct_bounded_candidate": 76,
}

class ValidationError(ValueError):
    pass


def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe({field: getattr(value, field) for field in value.__dataclass_fields__})
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _normalize_labels(turn_labels: Any) -> list[str]:
    if turn_labels is None:
        return []
    if isinstance(turn_labels, str):
        values = [turn_labels]
    elif isinstance(turn_labels, Mapping):
        values = [str(v) for v in turn_labels.values()]
    else:
        try:
            values = [str(v) for v in turn_labels]
        except TypeError:
            values = [str(turn_labels)]
    normalized: list[str] = []
    for value in values:
        text = _safe_text(value).lower().replace("/", " ").replace("_", " ").replace("-", " ")
        if text:
            normalized.append(" ".join(text.split()))
    return _dedupe_preserve(normalized)


def _normalize_context_signals(context_signals: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    if not context_signals or not isinstance(context_signals, Mapping):
        return {}
    return {str(key): value for key, value in context_signals.items()}


def _contains_any(blob: str, phrases: Sequence[str]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _truthy(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().lower() in {"true", "yes", "1", "on"})


def _is_forbidden_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in _FORBIDDEN_INPUT_KEYS_V1 or any(marker in lowered for marker in ("raw_prompt", "raw_response", "final_answer", "composed_reply", "live_dialogue_transcript", "provider_output", "model_output", "search_output", "advisor_output", "runtime_output", "private_content", "hidden_prompt"))


def _safe_context_signal_keys(context_signals: Mapping[str, Any]) -> list[str]:
    return _dedupe_preserve(sorted(key for key in context_signals.keys() if not _is_forbidden_key(key)))


def _unsafe_input_labels(context_signals: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for key, value in context_signals.items():
        lowered = key.lower()
        if _is_forbidden_key(key):
            if any(marker in lowered for marker in ("raw_prompt", "prompt_text", "prompt")):
                labels.append("raw_prompt_provided")
            if any(marker in lowered for marker in ("raw_response", "response_text", "model_output", "provider_output")):
                labels.append("raw_response_text_provided")
            if any(marker in lowered for marker in ("transcript", "live_dialogue")):
                labels.append("raw_transcript_provided")
            if any(marker in lowered for marker in ("raw_context", "context_text")):
                labels.append("raw_context_provided")
            if any(marker in lowered for marker in ("private_memory", "memory")):
                labels.append("private_memory_requested")
            if any(marker in lowered for marker in ("hidden_prompt", "hidden_material")):
                labels.append("hidden_material_requested")
            if any(marker in lowered for marker in ("benchmark", "score", "eval")):
                labels.append("benchmark_material_requested")
        if lowered in {"runtime_authority", "model_provider_used", "generates_final_text", "writes_state"} and _truthy(value):
            labels.append(f"{lowered}_requested")
        if lowered in _AUTHORITY_BLOCK_LABELS_V1 and _truthy(value):
            labels.append(lowered)
    return _dedupe_preserve(labels)


def _labels_blob(values: Sequence[str]) -> str:
    return " ".join(values)


def _candidate_active(candidate_type: str, labels_blob: str, context_signals: Mapping[str, Any]) -> bool:
    ctx_values = [value for key, value in context_signals.items() if key not in {"source", "origin", "producer", "adapter"}]
    ctx_blob = _labels_blob(_normalize_labels(ctx_values))
    blob = f"{labels_blob} {ctx_blob}".strip()
    if candidate_type == "direct_bounded_candidate":
        return _contains_any(blob, ("who are you", "status", "identity", "about you", "what are you", "weslr", "what can you do", "what capabilities are active", "current ability", "can you do", "can i upload", "can i pay", "marketplace active", "public pilot", "upload files", "upload", "files", "pay", "marketplace", "pilot", "public"))
    if candidate_type == "clarification_candidate":
        return not labels_blob or _contains_any(blob, ("clarify", "clarification", "ambiguous", "unclear", "missing", "what do you mean"))
    if candidate_type == "bounded_uncertainty_candidate":
        return _contains_any(blob, ("uncertain", "uncertainty", "unsure", "maybe", "not sure"))
    if candidate_type == "refusal_boundary_candidate":
        return _contains_any(blob, ("unsafe", "privacy", "not allowed", "forbidden", "boundary", "refusal", "cannot"))
    if candidate_type == "evidence_needed_candidate":
        return _contains_any(blob, ("evidence", "source", "proof", "verify", "current", "latest"))
    if candidate_type == "partial_supported_candidate":
        return _contains_any(blob, ("partial", "supported", "portion", "split", "some parts"))
    if candidate_type == "stepwise_plan_candidate":
        return _contains_any(blob, ("task", "plan", "steps", "workflow", "checklist"))
    if candidate_type == "implementation_plan_candidate":
        return _contains_any(blob, ("implementation", "build", "code")) or (_contains_any(blob, ("next lane", "lane")) and _contains_any(blob, ("implementation",)))
    if candidate_type == "workflow_next_lane_candidate":
        return _contains_any(blob, ("next lane", "sequence", "roadmap", "what next", "handoff"))
    if candidate_type == "governance_escalation_candidate":
        return _truthy(context_signals.get("needs_owner_approval")) or _contains_any(blob, ("approval", "escalate", "operator review", "decision needed", "blocked"))
    if candidate_type == "teaching_explanation_candidate":
        return _contains_any(blob, ("teach", "teaching", "explain", "explanation", "education", "lesson"))
    if candidate_type == "language_discovery_candidate":
        return _contains_any(blob, ("language", "grammar", "vocabulary", "translation", "words"))
    if candidate_type == "scientific_discovery_guidance_candidate":
        return _contains_any(blob, ("scientific", "research", "discovery", "experiment", "capability guidance"))
    if candidate_type == "benchmark_evaluation_candidate":
        return _contains_any(blob, ("benchmark", "evaluation", "turing", "readiness", "assessment"))
    if candidate_type == "unknown_friction_candidate":
        return _contains_any(blob, ("unknown", "unclear", "ambiguous", "stuck", "friction", "failed", "what is ", "what does ", "what's ", "unfamiliar")) or not labels_blob
    if candidate_type == "memory_honesty_candidate":
        return _contains_any(blob, ("memory", "remember", "recall", "continuity", "do you remember"))
    if candidate_type == "continuity_recap_candidate":
        return _contains_any(blob, ("continuity", "thread", "follow up", "previous point", "what were we doing"))
    if candidate_type == "relationship_feedback_candidate":
        return _contains_any(blob, ("relationship", "feedback", "tone", "trust", "preference", "frustration"))
    if candidate_type == "correction_repair_candidate":
        return _contains_any(blob, ("correction", "wrong", "revise", "fix", "actually"))
    if candidate_type == "conflict_contradiction_candidate":
        return _contains_any(blob, ("conflict", "contradiction", "inconsistent", "both true", "clash"))
    if candidate_type == "non_canned_specificity_candidate":
        return _contains_any(blob, ("canned", "template", "boilerplate", "generic", "repeated"))
    if candidate_type == "directness_concern_candidate":
        return _contains_any(blob, ("directness", "too direct", "concern", "friction", "loaded"))
    return False


def _candidate_priority(candidate_type: str) -> int:
    return _CANDIDATE_PRIORITY_V1.get(candidate_type, 0)


def _fit_status_for_candidate(candidate_type: str, labels_blob: str) -> str:
    if candidate_type == "clarification_candidate":
        return "needs_clarification"
    if candidate_type == "evidence_needed_candidate":
        return "needs_evidence"
    if candidate_type == "governance_escalation_candidate":
        return "needs_owner_approval"
    if candidate_type == "unknown_friction_candidate":
        return "unknown_friction"
    if candidate_type == "refusal_boundary_candidate":
        return "fit_with_boundaries"
    if candidate_type in {
        "bounded_uncertainty_candidate",
        "memory_honesty_candidate",
        "continuity_recap_candidate",
        "relationship_feedback_candidate",
        "correction_repair_candidate",
        "conflict_contradiction_candidate",
        "workflow_next_lane_candidate",
        "implementation_plan_candidate",
        "stepwise_plan_candidate",
        "teaching_explanation_candidate",
        "language_discovery_candidate",
        "scientific_discovery_guidance_candidate",
        "partial_supported_candidate",
        "direct_bounded_candidate",
        "benchmark_evaluation_candidate",
    }:
        return "fit_with_boundaries" if candidate_type != "direct_bounded_candidate" else "fit"
    if candidate_type in {"non_canned_specificity_candidate", "directness_concern_candidate"}:
        if _contains_any(labels_blob, ("template", "generic", "boilerplate", "canned", "too direct", "concern")):
            return "needs_revision"
        return "fit_with_boundaries"
    return "needs_revision"


def _fit_label_for_status(status: str) -> str:
    return {
        "fit": "fit_aligned",
        "fit_with_boundaries": "fit_partial",
        "needs_revision": "fit_mismatch",
        "needs_clarification": "fit_inconclusive",
        "needs_evidence": "fit_inconclusive",
        "needs_owner_approval": "needs_operator_review",
        "unknown_friction": "fit_inconclusive",
        "blocked": "blocked_by_runtime_boundary",
    }.get(status, "needs_operator_review")


def _fit_confidence_label_for_status(status: str) -> str:
    return {
        "fit": "high_confidence",
        "fit_with_boundaries": "medium_confidence",
        "needs_revision": "medium_confidence",
        "needs_clarification": "inconclusive",
        "needs_evidence": "inconclusive",
        "needs_owner_approval": "low_confidence",
        "unknown_friction": "inconclusive",
        "blocked": "inconclusive",
    }.get(status, "inconclusive")


def _next_action_for_status(status: str, candidate_type: str) -> str:
    if status == "blocked":
        return "block_no_render"
    if status == "needs_clarification":
        return "ask_clarifying_question_later"
    if status == "needs_evidence":
        return "request_evidence_later"
    if status == "needs_owner_approval":
        return "escalate_owner_review_later"
    if status == "unknown_friction":
        return "route_unknown_friction_later"
    if candidate_type == "refusal_boundary_candidate":
        return "render_refusal_boundary_later"
    if candidate_type == "partial_supported_candidate":
        return "render_partial_supported_answer_later"
    return "render_bounded_answer_later"


def _candidate_quality_pressures(candidate_type: str, labels_blob: str) -> list[str]:
    pressures: list[str] = []
    if candidate_type == "non_canned_specificity_candidate" and _contains_any(labels_blob, ("template", "generic", "boilerplate", "canned")):
        pressures.append("canned_template_risk")
    if candidate_type == "directness_concern_candidate" and _contains_any(labels_blob, ("directness", "too direct", "concern")):
        pressures.append("human_perceived_ai_tone")
    if candidate_type == "benchmark_evaluation_candidate":
        pressures.append("unsupported_claim_risk")
    if candidate_type == "governance_escalation_candidate":
        pressures.append("authority_drift_risk")
    if candidate_type == "evidence_needed_candidate":
        pressures.append("final_text_too_early")
    if candidate_type == "clarification_candidate":
        pressures.append("actionability_mismatch")
    if candidate_type == "refusal_boundary_candidate":
        pressures.append("wrong_risk_posture")
    return _dedupe_preserve(pressures)


def _candidate_mismatch_labels(candidate_type: str, labels_blob: str) -> list[str]:
    mismatches: list[str] = []
    if candidate_type == "direct_bounded_candidate" and _contains_any(labels_blob, ("generic", "vague", "broad")):
        mismatches.append("too_generic")
    if candidate_type == "partial_supported_candidate" and _contains_any(labels_blob, ("full", "all", "complete")):
        mismatches.append("answer_shape_mismatch")
    if candidate_type == "teaching_explanation_candidate" and _contains_any(labels_blob, ("technical", "jargon")):
        mismatches.append("too_technical")
    if candidate_type == "language_discovery_candidate" and _contains_any(labels_blob, ("jargon", "technical")):
        mismatches.append("jargon_mismatch")
    if candidate_type == "scientific_discovery_guidance_candidate" and _contains_any(labels_blob, ("industry", "domain")):
        mismatches.append("industry_context_mismatch")
    if candidate_type == "relationship_feedback_candidate" and _contains_any(labels_blob, ("frustration", "tone", "trust")):
        mismatches.extend(["fake_empathy", "human_perceived_ai_tone"])
    if candidate_type == "correction_repair_candidate":
        mismatches.append("ignored_correction")
    if candidate_type in {"continuity_recap_candidate", "memory_honesty_candidate"}:
        mismatches.append("lost_continuity")
    if candidate_type == "non_canned_specificity_candidate":
        mismatches.append("canned_template_risk")
    if candidate_type == "directness_concern_candidate":
        mismatches.append("human_perceived_ai_tone")
    if candidate_type == "benchmark_evaluation_candidate":
        mismatches.append("unsupported_claim_risk")
    if candidate_type == "refusal_boundary_candidate":
        mismatches.append("wrong_risk_posture")
    if candidate_type == "governance_escalation_candidate":
        mismatches.append("authority_drift_risk")
    if candidate_type == "evidence_needed_candidate":
        mismatches.append("evidence_depth_mismatch")
    if candidate_type == "stepwise_plan_candidate":
        mismatches.append("actionability_mismatch")
    if candidate_type == "implementation_plan_candidate":
        mismatches.append("too_technical")
    if candidate_type == "workflow_next_lane_candidate":
        mismatches.append("too_verbose")
    return _dedupe_preserve([label for label in mismatches if label in MISMATCH_LABELS_V1])


def _self_check_labels() -> list[str]:
    return sorted({*CHECK_LABELS_V1, "fit_before_render_check", "candidate_ranking_check", "authority_drift_check", "final_text_too_early_check", "raw_prompt_leak_check"})


def _candidate_summary_from_formation(formation_packet: CandidateResponseFormationPacket) -> dict[str, Any]:
    summary = summarize_candidate_response_formation_packet_v1(formation_packet)
    return _json_safe(summary)


def _blocked_labels_from_context(context_signals: Mapping[str, Any]) -> list[str]:
    labels = _unsafe_input_labels(context_signals)
    if _truthy(context_signals.get("runtime_authority")):
        labels.append("runtime_authority_requested")
    if _truthy(context_signals.get("model_provider_used")):
        labels.append("model_provider_output_requested")
    if _truthy(context_signals.get("generates_final_text")):
        labels.append("final_answer_authority_requested")
    if _truthy(context_signals.get("writes_state")):
        labels.append("raw_persistence_requested")
    if _truthy(context_signals.get("official_claim_requested")):
        labels.append("official_claim_requested")
    if _truthy(context_signals.get("turing_claim_requested")):
        labels.append("turing_claim_requested")
    if _truthy(context_signals.get("intelligence_claim_requested")):
        labels.append("intelligence_claim_requested")
    if _truthy(context_signals.get("certification_claim_requested")):
        labels.append("certification_claim_requested")
    if _truthy(context_signals.get("search_call_authority_requested")):
        labels.append("search_call_authority_requested")
    if _truthy(context_signals.get("advisor_call_authority_requested")):
        labels.append("advisor_call_authority_requested")
    if _truthy(context_signals.get("automatic_lesson_promotion_requested")):
        labels.append("automatic_lesson_promotion_requested")
    return _dedupe_preserve(labels)


def _candidate_result_dict(candidate: CandidateResponsePath, *, accepted: bool, rejected: bool, revision_required: bool, fit_status: str, labels_blob: str, context_signals: Mapping[str, Any], reason: str) -> dict[str, Any]:
    fit_labels = [_fit_label_for_status(fit_status)]
    quality_pressures = _candidate_quality_pressures(candidate.candidate_type, labels_blob)
    mismatches = _candidate_mismatch_labels(candidate.candidate_type, labels_blob)
    blocked_labels = _blocked_labels_from_context(context_signals)
    if candidate.candidate_type == "clarification_candidate":
        quality_pressures.append("final_text_too_early")
    if candidate.candidate_type == "unknown_friction_candidate":
        quality_pressures.append("actionability_mismatch")
    if candidate.candidate_type == "memory_honesty_candidate":
        quality_pressures.append("lost_continuity")
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_type": candidate.candidate_type,
        "route_id": candidate.route_id,
        "method_id": candidate.method_id,
        "shape_id": candidate.shape_id,
        "case_id": candidate.case_id,
        "accepted": accepted,
        "rejected": rejected,
        "revision_required": revision_required,
        "fit_status": fit_status,
        "fit_labels": fit_labels,
        "self_check_labels": _self_check_labels(),
        "quality_pressure_labels": _dedupe_preserve([*quality_pressures, *candidate.quality_pressure_labels]),
        "mismatch_labels": mismatches,
        "blocked_labels": blocked_labels,
        "reason": reason,
        "selected": bool(candidate.selected),
        "generates_final_text": False,
        "selection_score": candidate.selection_score,
    }


def _final_candidate_type(candidates: Sequence[CandidateResponsePath], labels_blob: str, context_signals: Mapping[str, Any]) -> str:
    active_candidates = [candidate for candidate in candidates if _candidate_active(candidate.candidate_type, labels_blob, context_signals)]
    if not active_candidates:
        if not labels_blob:
            return "clarification_candidate"
        if _contains_any(labels_blob, ("unknown", "friction", "stuck", "failed")):
            return "unknown_friction_candidate"
        return "clarification_candidate"
    if _truthy(context_signals.get("unknown_detected")) or _contains_any(labels_blob, ("unknown word", "unknown phrase", "unknown term", "unfamiliar", "what is ", "what does ")):
        for candidate in active_candidates:
            if candidate.candidate_type == "unknown_friction_candidate":
                return candidate.candidate_type
    if _contains_any(labels_blob, ("weslr", "who are you", "what are you", "what can you do", "what capabilities are active", "current ability", "upload", "files", "pay", "marketplace", "pilot", "public", "boundary")):
        for candidate in active_candidates:
            if candidate.candidate_type == "direct_bounded_candidate":
                return candidate.candidate_type
    active_candidates.sort(key=lambda candidate: (-_candidate_priority(candidate.candidate_type), -candidate.selection_score, candidate.candidate_id))
    return active_candidates[0].candidate_type


def _fit_status_for_context(context_signals: Mapping[str, Any], candidate_type: str, labels_blob: str) -> str:
    if any(_truthy(context_signals.get(key)) for key in ("runtime_authority", "model_provider_used", "generates_final_text", "writes_state")):
        return "blocked"
    if any(_truthy(context_signals.get(key)) for key in ("official_claim_requested", "turing_claim_requested", "intelligence_claim_requested", "certification_claim_requested")):
        return "blocked"
    if candidate_type == "clarification_candidate":
        return "needs_clarification"
    if candidate_type == "evidence_needed_candidate":
        return "needs_evidence"
    if candidate_type == "governance_escalation_candidate":
        return "needs_owner_approval"
    if candidate_type == "unknown_friction_candidate":
        return "unknown_friction"
    if candidate_type == "refusal_boundary_candidate":
        return "fit_with_boundaries"
    if candidate_type == "partial_supported_candidate":
        return "fit_with_boundaries"
    if candidate_type == "benchmark_evaluation_candidate":
        return "fit_with_boundaries"
    if candidate_type in {"non_canned_specificity_candidate", "directness_concern_candidate"} and _contains_any(labels_blob, ("template", "generic", "boilerplate", "canned", "too direct", "concern")):
        return "needs_revision"
    if candidate_type in {
        "bounded_uncertainty_candidate",
        "memory_honesty_candidate",
        "continuity_recap_candidate",
        "relationship_feedback_candidate",
        "correction_repair_candidate",
        "conflict_contradiction_candidate",
        "workflow_next_lane_candidate",
        "implementation_plan_candidate",
        "stepwise_plan_candidate",
        "teaching_explanation_candidate",
        "language_discovery_candidate",
        "scientific_discovery_guidance_candidate",
        "non_canned_specificity_candidate",
        "directness_concern_candidate",
    }:
        return "fit_with_boundaries"
    if candidate_type == "direct_bounded_candidate":
        return "fit"
    return "needs_revision"


def build_response_fit_self_check_packet_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> "ResponseFitSelfCheckPacket":
    normalized_labels = _normalize_labels(turn_labels)
    normalized_context_signals = _normalize_context_signals(context_signals)
    safe_context_signal_keys = _safe_context_signal_keys(normalized_context_signals)
    labels_blob = _labels_blob(normalized_labels)

    formation_packet = form_candidate_responses_v1(normalized_labels, context_signals=normalized_context_signals)
    formation_summary = summarize_candidate_response_formation_packet_v1(formation_packet)
    formation_json = to_candidate_response_formation_json_safe_v1(formation_packet)

    blocked_labels = _blocked_labels_from_context(normalized_context_signals)
    blocked = bool(blocked_labels)

    candidates = list(formation_packet.candidates)
    final_candidate_type = _final_candidate_type(candidates, labels_blob, normalized_context_signals)
    candidate_map = {candidate.candidate_type: candidate for candidate in candidates}
    final_candidate = candidate_map.get(final_candidate_type) or candidate_map.get(formation_summary.selected_candidate_type) or formation_packet.candidates[0]

    fit_status = _fit_status_for_context(normalized_context_signals, final_candidate.candidate_type, labels_blob)
    if blocked:
        fit_status = "blocked"

    candidate_results: list[dict[str, Any]] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    revision_required_ids: list[str] = []

    for candidate in candidates:
        accepted = False
        rejected = False
        revision_required = False
        reason = "signal mismatch"

        if blocked:
            rejected = True
            reason = "blocked by authority or raw content boundary"
        elif candidate.candidate_type == final_candidate.candidate_type:
            accepted = True
            reason = "selected fit candidate"
        elif _candidate_active(candidate.candidate_type, labels_blob, normalized_context_signals):
            revision_required = True
            reason = "compatible alternative candidate"
        else:
            rejected = True
            reason = "signal mismatch"

        result = _candidate_result_dict(
            candidate,
            accepted=accepted,
            rejected=rejected,
            revision_required=revision_required,
            fit_status=fit_status if candidate.candidate_type == final_candidate.candidate_type else ("needs_revision" if revision_required else "blocked" if blocked else "needs_revision"),
            labels_blob=labels_blob,
            context_signals=normalized_context_signals,
            reason=reason,
        )
        candidate_results.append(result)
        if accepted:
            accepted_ids.append(candidate.candidate_id)
        if rejected:
            rejected_ids.append(candidate.candidate_id)
        if revision_required:
            revision_required_ids.append(candidate.candidate_id)

    if blocked:
        final_candidate_id = ""
    else:
        final_candidate_id = final_candidate.candidate_id

    fit_labels = [_fit_label_for_status(fit_status)]
    confidence_label = _fit_confidence_label_for_status(fit_status)
    recommended_next_action = _next_action_for_status(fit_status, final_candidate.candidate_type)

    mismatch_labels = _dedupe_preserve([label for item in candidate_results for label in item["mismatch_labels"]])
    quality_pressure_labels = _dedupe_preserve([label for item in candidate_results for label in item["quality_pressure_labels"]])

    summary = {
        "packet_type": PACKET_TYPE_V1,
        "fit_status": fit_status,
        "selected_candidate_id": formation_packet.selected_candidate_id,
        "final_candidate_id": final_candidate_id,
        "final_candidate_type": final_candidate.candidate_type,
        "candidate_count": len(candidate_results),
        "accepted_candidate_count": len(accepted_ids),
        "rejected_candidate_count": len(rejected_ids),
        "revision_required_candidate_count": len(revision_required_ids),
        "blocked": blocked,
        "recommended_next_action": recommended_next_action,
        "fit_label": fit_labels[0],
        "fit_confidence_label": confidence_label,
        "candidate_summary": _candidate_summary_from_formation(formation_packet),
    }

    packet = ResponseFitSelfCheckPacket(
        packet_type=PACKET_TYPE_V1,
        turn_labels=normalized_labels,
        safe_context_signal_keys=safe_context_signal_keys,
        candidate_summary=summary,
        selected_candidate_id=formation_packet.selected_candidate_id,
        candidate_fit_results=tuple(_json_safe(candidate_results)),
        accepted_candidate_ids=tuple(accepted_ids),
        rejected_candidate_ids=tuple(rejected_ids),
        revision_required_candidate_ids=tuple(revision_required_ids),
        final_candidate_id=final_candidate_id,
        fit_status=fit_status,
        fit_labels=tuple(fit_labels),
        self_check_labels=tuple(_self_check_labels()),
        quality_pressure_labels=tuple(quality_pressure_labels),
        mismatch_labels=tuple(mismatch_labels),
        blocked_labels=tuple(blocked_labels),
        needs_clarification=fit_status == "needs_clarification",
        needs_evidence=fit_status == "needs_evidence",
        needs_owner_approval=fit_status == "needs_owner_approval",
        blocked=blocked,
        recommended_next_action=recommended_next_action,
        safe_metadata={
            "formation_packet": formation_json,
            "formation_summary": _json_safe(formation_summary),
            "selected_candidate_type": formation_summary.selected_candidate_type,
            "final_candidate_type": final_candidate.candidate_type,
            "fit_confidence_label": confidence_label,
            "accepted_candidate_ids": accepted_ids,
            "rejected_candidate_ids": rejected_ids,
            "revision_required_candidate_ids": revision_required_ids,
            "safe_context_signal_keys": safe_context_signal_keys,
            "unsafe_context_signal_keys": _dedupe_preserve(sorted(key for key in normalized_context_signals.keys() if _is_forbidden_key(key))),
            "blocked_labels": blocked_labels,
            "fit_label": fit_labels[0],
            "fit_status": fit_status,
            "recommended_next_action": recommended_next_action,
            "runtime_authority_detected": _truthy(normalized_context_signals.get("runtime_authority")),
            "model_provider_used_detected": _truthy(normalized_context_signals.get("model_provider_used")),
            "generates_final_text_detected": _truthy(normalized_context_signals.get("generates_final_text")),
            "writes_state_detected": _truthy(normalized_context_signals.get("writes_state")),
        },
        runtime_authority=False,
        model_provider_used=False,
        generates_final_text=False,
        writes_state=False,
    )

    return packet


def check_candidate_response_fit_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> "ResponseFitSelfCheckPacket":
    return build_response_fit_self_check_packet_v1(turn_labels, context_signals=context_signals)


def to_response_fit_self_check_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet)


def validate_response_fit_self_check_packet_v1(packet: Any) -> bool:
    data = to_response_fit_self_check_json_safe_v1(packet) if is_dataclass(packet) else dict(packet) if isinstance(packet, Mapping) else None
    if data is None:
        raise ValidationError("packet must be a mapping or dataclass")

    required = [
        "packet_type",
        "turn_labels",
        "safe_context_signal_keys",
        "candidate_summary",
        "selected_candidate_id",
        "candidate_fit_results",
        "accepted_candidate_ids",
        "rejected_candidate_ids",
        "revision_required_candidate_ids",
        "final_candidate_id",
        "fit_status",
        "fit_labels",
        "self_check_labels",
        "quality_pressure_labels",
        "mismatch_labels",
        "blocked_labels",
        "needs_clarification",
        "needs_evidence",
        "needs_owner_approval",
        "blocked",
        "recommended_next_action",
        "safe_metadata",
        "runtime_authority",
        "model_provider_used",
        "generates_final_text",
        "writes_state",
    ]
    for field_name in required:
        if field_name not in data:
            raise ValidationError(f"missing required field: {field_name}")

    if data["packet_type"] != PACKET_TYPE_V1:
        raise ValidationError("packet_type mismatch")
    if data["fit_status"] not in FIT_STATUSES_V1:
        raise ValidationError("unknown fit_status")
    if data["recommended_next_action"] not in RECOMMENDED_NEXT_ACTIONS_V1:
        raise ValidationError("unknown recommended_next_action")

    for field_name in ("runtime_authority", "model_provider_used", "generates_final_text", "writes_state"):
        if data[field_name] is not False:
            raise ValidationError(f"{field_name} must be false")

    if not isinstance(data["turn_labels"], list):
        raise ValidationError("turn_labels must be a list")
    if not isinstance(data["safe_context_signal_keys"], list):
        raise ValidationError("safe_context_signal_keys must be a list")
    if not isinstance(data["candidate_summary"], dict):
        raise ValidationError("candidate_summary must be a dict")
    if not isinstance(data["candidate_fit_results"], list):
        raise ValidationError("candidate_fit_results must be a list")
    if not isinstance(data["accepted_candidate_ids"], list):
        raise ValidationError("accepted_candidate_ids must be a list")
    if not isinstance(data["rejected_candidate_ids"], list):
        raise ValidationError("rejected_candidate_ids must be a list")
    if not isinstance(data["revision_required_candidate_ids"], list):
        raise ValidationError("revision_required_candidate_ids must be a list")
    if not isinstance(data["fit_labels"], list):
        raise ValidationError("fit_labels must be a list")
    if not isinstance(data["self_check_labels"], list):
        raise ValidationError("self_check_labels must be a list")
    if not isinstance(data["quality_pressure_labels"], list):
        raise ValidationError("quality_pressure_labels must be a list")
    if not isinstance(data["mismatch_labels"], list):
        raise ValidationError("mismatch_labels must be a list")
    if not isinstance(data["blocked_labels"], list):
        raise ValidationError("blocked_labels must be a list")
    if not isinstance(data["safe_metadata"], dict):
        raise ValidationError("safe_metadata must be a dict")

    if not data["selected_candidate_id"]:
        raise ValidationError("selected_candidate_id must not be empty")
    if data["blocked"] is False and not data["final_candidate_id"]:
        raise ValidationError("final_candidate_id required when packet is not blocked")

    if len(_dedupe_preserve(data["accepted_candidate_ids"])) != len(data["accepted_candidate_ids"]):
        raise ValidationError("accepted_candidate_ids must be unique")
    if len(_dedupe_preserve(data["rejected_candidate_ids"])) != len(data["rejected_candidate_ids"]):
        raise ValidationError("rejected_candidate_ids must be unique")
    if len(_dedupe_preserve(data["revision_required_candidate_ids"])) != len(data["revision_required_candidate_ids"]):
        raise ValidationError("revision_required_candidate_ids must be unique")

    if set(data["accepted_candidate_ids"]) & set(data["rejected_candidate_ids"]):
        raise ValidationError("accepted and rejected candidate ids must not overlap")
    if set(data["accepted_candidate_ids"]) & set(data["revision_required_candidate_ids"]):
        raise ValidationError("accepted and revision_required candidate ids must not overlap")

    if data["final_candidate_id"] and data["final_candidate_id"] not in set(data["accepted_candidate_ids"]):
        raise ValidationError("final_candidate_id must be accepted")

    result_ids: list[str] = []
    allowed_candidate_types = {
        "direct_bounded_candidate",
        "clarification_candidate",
        "bounded_uncertainty_candidate",
        "refusal_boundary_candidate",
        "evidence_needed_candidate",
        "partial_supported_candidate",
        "stepwise_plan_candidate",
        "implementation_plan_candidate",
        "workflow_next_lane_candidate",
        "governance_escalation_candidate",
        "teaching_explanation_candidate",
        "language_discovery_candidate",
        "scientific_discovery_guidance_candidate",
        "benchmark_evaluation_candidate",
        "unknown_friction_candidate",
        "memory_honesty_candidate",
        "continuity_recap_candidate",
        "relationship_feedback_candidate",
        "correction_repair_candidate",
        "conflict_contradiction_candidate",
        "non_canned_specificity_candidate",
        "directness_concern_candidate",
    }
    for result in data["candidate_fit_results"]:
        if not isinstance(result, dict):
            raise ValidationError("candidate_fit_results entries must be dicts")
        for field_name in ("candidate_id", "candidate_type", "route_id", "method_id", "shape_id", "case_id", "fit_status", "fit_labels", "self_check_labels", "quality_pressure_labels", "mismatch_labels", "blocked_labels", "reason", "accepted", "rejected", "revision_required", "generates_final_text"):
            if field_name not in result:
                raise ValidationError(f"candidate_fit_results missing {field_name}")
        if result["candidate_type"] not in allowed_candidate_types:
            raise ValidationError("unknown candidate_type")
        if result["fit_status"] not in FIT_STATUSES_V1:
            raise ValidationError("unknown candidate fit_status")
        if not isinstance(result["fit_labels"], list):
            raise ValidationError("candidate fit_labels must be a list")
        if not isinstance(result["self_check_labels"], list):
            raise ValidationError("candidate self_check_labels must be a list")
        if not isinstance(result["quality_pressure_labels"], list):
            raise ValidationError("candidate quality_pressure_labels must be a list")
        if not isinstance(result["mismatch_labels"], list):
            raise ValidationError("candidate mismatch_labels must be a list")
        if not isinstance(result["blocked_labels"], list):
            raise ValidationError("candidate blocked_labels must be a list")
        if result["generates_final_text"] is not False:
            raise ValidationError("candidate generates_final_text must be false")
        if result["accepted"] and result["rejected"]:
            raise ValidationError("candidate cannot be accepted and rejected")
        if result["rejected"] and not result["reason"]:
            raise ValidationError("rejected candidates must include reasons")
        if result["revision_required"] and result["accepted"]:
            raise ValidationError("revision-required candidate cannot be accepted")
        result_ids.append(result["candidate_id"])

    if data["selected_candidate_id"] not in set(result_ids):
        raise ValidationError("selected_candidate_id must exist in candidate_fit_results")
    if data["final_candidate_id"] and data["final_candidate_id"] not in set(result_ids):
        raise ValidationError("final_candidate_id must exist in candidate_fit_results")

    summary = data["candidate_summary"]
    for field_name in ("fit_status", "selected_candidate_id", "final_candidate_id", "candidate_count"):
        if field_name not in summary:
            raise ValidationError(f"candidate_summary missing {field_name}")
    if summary["fit_status"] not in FIT_STATUSES_V1:
        raise ValidationError("candidate_summary fit_status unknown")
    if summary["selected_candidate_id"] != data["selected_candidate_id"]:
        raise ValidationError("candidate_summary selected_candidate_id mismatch")
    if summary["final_candidate_id"] != data["final_candidate_id"]:
        raise ValidationError("candidate_summary final_candidate_id mismatch")

    if data["runtime_authority"] or data["model_provider_used"] or data["generates_final_text"] or data["writes_state"]:
        raise ValidationError("authority drift detected")

    blocked_label_set = set(data["blocked_labels"])
    if blocked_label_set & _RAW_LEAK_LABELS_V1:
        raise ValidationError("raw prompt leakage detected")
    if blocked_label_set & _AUTHORITY_BLOCK_LABELS_V1:
        raise ValidationError("authority drift detected")
    if any(flag for flag in (data["safe_metadata"].get("runtime_authority_detected"), data["safe_metadata"].get("model_provider_used_detected"), data["safe_metadata"].get("generates_final_text_detected"), data["safe_metadata"].get("writes_state_detected")) if flag is True):
        raise ValidationError("authority drift detected")

    return True


@dataclass(frozen=True, slots=True)
class ResponseFitSelfCheckSummary:
    packet_type: str
    fit_status: str
    selected_candidate_id: str
    final_candidate_id: str
    accepted_candidate_count: int
    rejected_candidate_count: int
    revision_required_candidate_count: int
    blocked: bool
    recommended_next_action: str
    mismatch_label_count: int
    blocked_label_count: int


@dataclass(frozen=True, slots=True)
class CandidateSelfCheckResult:
    candidate_id: str
    candidate_type: str
    route_id: str
    method_id: str
    shape_id: str
    case_id: str
    accepted: bool
    rejected: bool
    revision_required: bool
    fit_status: str
    fit_labels: tuple[str, ...] = field(default_factory=tuple)
    self_check_labels: tuple[str, ...] = field(default_factory=tuple)
    quality_pressure_labels: tuple[str, ...] = field(default_factory=tuple)
    mismatch_labels: tuple[str, ...] = field(default_factory=tuple)
    blocked_labels: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""
    selected: bool = False
    generates_final_text: bool = False


@dataclass(frozen=True, slots=True)
class ResponseFitSelfCheckPacket:
    packet_type: str
    turn_labels: list[str]
    safe_context_signal_keys: list[str]
    candidate_summary: dict[str, Any]
    selected_candidate_id: str
    candidate_fit_results: tuple[dict[str, Any], ...]
    accepted_candidate_ids: tuple[str, ...]
    rejected_candidate_ids: tuple[str, ...]
    revision_required_candidate_ids: tuple[str, ...]
    final_candidate_id: str
    fit_status: str
    fit_labels: tuple[str, ...]
    self_check_labels: tuple[str, ...]
    quality_pressure_labels: tuple[str, ...]
    mismatch_labels: tuple[str, ...]
    blocked_labels: tuple[str, ...]
    needs_clarification: bool
    needs_evidence: bool
    needs_owner_approval: bool
    blocked: bool
    recommended_next_action: str
    safe_metadata: dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    generates_final_text: bool = False
    writes_state: bool = False


def summarize_response_fit_self_check_packet_v1(packet: Any) -> ResponseFitSelfCheckSummary:
    data = to_response_fit_self_check_json_safe_v1(packet)
    return ResponseFitSelfCheckSummary(
        packet_type=str(data.get("packet_type", PACKET_TYPE_V1)),
        fit_status=str(data.get("fit_status", "blocked")),
        selected_candidate_id=str(data.get("selected_candidate_id", "")),
        final_candidate_id=str(data.get("final_candidate_id", "")),
        accepted_candidate_count=len(data.get("accepted_candidate_ids", [])),
        rejected_candidate_count=len(data.get("rejected_candidate_ids", [])),
        revision_required_candidate_count=len(data.get("revision_required_candidate_ids", [])),
        blocked=bool(data.get("blocked", False)),
        recommended_next_action=str(data.get("recommended_next_action", "block_no_render")),
        mismatch_label_count=len(data.get("mismatch_labels", [])),
        blocked_label_count=len(data.get("blocked_labels", [])),
    )


def to_response_fit_self_check_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet)


def check_candidate_response_fit_v1(turn_labels: Any, context_signals: Mapping[str, Any] | None = None) -> ResponseFitSelfCheckPacket:
    return build_response_fit_self_check_packet_v1(turn_labels, context_signals=context_signals)


__all__ = [
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "FIT_STATUSES_V1",
    "RECOMMENDED_NEXT_ACTIONS_V1",
    "MISMATCH_LABELS_V1",
    "QUALITY_PRESSURE_LABELS_V1",
    "SELF_CHECK_LABELS_V1",
    "CandidateSelfCheckResult",
    "ResponseFitSelfCheckPacket",
    "ResponseFitSelfCheckSummary",
    "build_response_fit_self_check_packet_v1",
    "check_candidate_response_fit_v1",
    "validate_response_fit_self_check_packet_v1",
    "summarize_response_fit_self_check_packet_v1",
    "to_response_fit_self_check_json_safe_v1",
]
