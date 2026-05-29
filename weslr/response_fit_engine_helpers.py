"""Metadata-only helpers for WESLR response fit engine boundary v1.

This module is intentionally pure, deterministic, and fail-closed.
It converts approved synthetic/redacted response-fit metadata into truth
kernel, human situation frame, answer shape, mismatch detection, operator
packets, and JSON-safe summaries.

It does not perform file I/O, network I/O, subprocess execution, runtime/chat
wiring, live response routing, provider/model/search/advisor calls, dot-weslr
IO, or any official scoring work.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "weslr_response_fit_engine_helpers_v1"
BOUNDARY_TYPE_V1 = "response_fit_engine_boundary_v1"
TRUTH_KERNEL_TYPE_V1 = "response_fit_truth_kernel_v1"
HUMAN_SITUATION_FRAME_TYPE_V1 = "response_fit_human_situation_frame_v1"
ANSWER_SHAPE_TYPE_V1 = "response_fit_answer_shape_v1"
CASE_TYPE_V1 = "response_fit_case_v1"
RESULT_PACKET_TYPE_V1 = "response_fit_result_packet_v1"
SUMMARY_TYPE_V1 = "response_fit_summary_v1"

HUMAN_SITUATION_SIGNALS_V1 = {
    "role_context",
    "domain_context",
    "expertise_level",
    "urgency_level",
    "risk_level",
    "emotional_pressure",
    "decision_burden",
    "desired_detail_level",
    "evidence_need",
    "language_style",
    "continuity_state",
    "correction_history",
    "trust_state",
    "safety_boundary_need",
}

MISMATCH_FAMILIES_V1 = {
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

CHECK_LABELS_V1 = {
    "anti_stereotype_check",
    "anti_manipulation_check",
    "continuity_check",
    "correction_check",
    "evidence_boundary_check",
}

FIT_LABELS_V1 = {
    "fit_aligned",
    "fit_partial",
    "fit_mismatch",
    "fit_inconclusive",
    "blocked_by_privacy_boundary",
    "blocked_by_runtime_boundary",
    "needs_operator_review",
}

FIT_CONFIDENCE_LABELS_V1 = {
    "high_confidence",
    "medium_confidence",
    "low_confidence",
    "inconclusive",
}

DENIED_AUTHORITY_FLAGS_V1 = {
    "final_answer_authority",
    "public_live_authority",
    "public_ux_authority",
    "voice_authority",
    "runtime_authority",
    "live_runtime_authority",
    "model_call_authority",
    "search_call_authority",
    "advisor_call_authority",
    "official_claim_authority",
    "turing_claim_authority",
    "intelligence_claim_authority",
    "certification_claim_authority",
    "public_readiness_authority",
    "voice_readiness_authority",
    "live_user_safety_readiness_authority",
    "benchmark_score_authority",
    "model_superiority_authority",
    "raw_persistence_authority",
    "private_memory_authority",
    "unknown_engine_authority",
    "automatic_lesson_promotion_authority",
}

BLOCKED_LABELS_V1 = {
    "missing_case_id",
    "missing_truth_kernel_id",
    "missing_truth_kernel",
    "missing_human_situation_frame",
    "missing_answer_shape",
    "missing_fact_labels",
    "missing_uncertainty_labels",
    "missing_evidence_boundary_labels",
    "missing_safety_boundary_labels",
    "missing_governance_boundary_labels",
    "missing_role_context",
    "missing_domain_context",
    "missing_expertise_level",
    "missing_urgency_level",
    "missing_risk_level",
    "missing_emotional_pressure",
    "missing_decision_burden",
    "missing_desired_detail_level",
    "missing_evidence_need",
    "missing_language_style",
    "missing_continuity_state",
    "missing_correction_history",
    "missing_trust_state",
    "missing_safety_boundary_need",
    "missing_length",
    "missing_tone",
    "missing_structure",
    "missing_jargon",
    "missing_evidence_depth",
    "missing_warning_position",
    "missing_directness",
    "missing_next_action",
    "raw_prompt_provided",
    "raw_response_text_provided",
    "raw_transcript_provided",
    "raw_context_provided",
    "raw_private_content_requested",
    "raw_persistence_requested",
    "dot_weslr_requested",
    "private_memory_requested",
    "live_user_content_requested",
    "provider_model_output_requested",
    "hidden_material_requested",
    "benchmark_material_requested",
    "final_answer_authority_requested",
    "public_live_authority_requested",
    "public_ux_authority_requested",
    "voice_authority_requested",
    "runtime_authority_requested",
    "live_runtime_authority_requested",
    "model_call_authority_requested",
    "search_call_authority_requested",
    "advisor_call_authority_requested",
    "official_claim_requested",
    "turing_claim_requested",
    "intelligence_claim_requested",
    "certification_claim_requested",
    "stereotype_assumption_requested",
    "manipulation_logic_requested",
    "fake_empathy_requested",
    "template_engine_requested",
    "role_personality_template_requested",
    "human_imitation_requested",
    "unknown_signal_label",
    "unknown_mismatch_family",
    "unknown_check_label",
    "unknown_fit_label",
    "unknown_fit_confidence_label",
    "unknown_authority_flag",
    "unknown_unknown_engine_role",
    "forbidden_unknown_engine_role",
    "invalid_request_shape",
    "source_registry_missing",
}

ALLOWED_UNKNOWN_ENGINE_ROLES_V1 = {
    "predict_conversation_failure_zones",
    "suggest_synthetic_scenario_variants",
    "compare_predicted_vs_observed_failure_labels",
    "compress_repeated_conversation_gaps",
}

FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1 = {
    "authority",
    "scoring",
    "certification",
    "official_turing_judge",
    "future_certainty",
    "source_license_approval",
    "runtime_live_control",
    "automatic_self_modification",
}

SENSITIVE_KEY_HINTS_V1 = (
    "raw_prompt",
    "prompt",
    "raw_response",
    "response_text",
    "raw_transcript",
    "transcript_text",
    "raw_context",
    "context_text",
    "live_user",
    "private_memory",
    "private_data",
    "private_text",
    "hidden_material",
    "benchmark_material",
    "provider_model_output",
    "final_answer",
    "dot_weslr",
    "voice",
    "public_live_authority",
    "runtime_authority",
    "official_claim",
    "turing_claim",
    "intelligence_claim",
    "certification_claim",
    "manipulation",
    "fake_empathy",
    "template",
    "stereotype",
    "persona",
    "roleplay",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        values = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = _safe_str(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _unique_sorted(labels: Iterable[str]) -> list[str]:
    if isinstance(labels, (str, bytes)):
        items = [labels]
    else:
        items = list(labels)
    return sorted(set(_safe_list(items)))


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _redact_key(key: str, value: Any) -> Any:
    key_text = _safe_str(key).lower()
    if any(hint in key_text for hint in SENSITIVE_KEY_HINTS_V1):
        return f"[redacted:{_safe_str(key) or 'sensitive'}]"
    return _json_safe(value)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _redact_key(str(key), val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        safe_items = [_json_safe(item) for item in value]
        return sorted(safe_items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return f"[redacted:{type(value).__name__}]"


def to_response_fit_json_safe_v1(value: Any) -> Any:
    """Convert supported response-fit structures to deterministic JSON-safe data."""

    return _json_safe(value)


def _dedupe_strings(*parts: Any) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for part in parts:
        for text in _safe_list(part):
            if text not in seen:
                values.append(text)
                seen.add(text)
    return values


def _build_truth_kernel_id(fact_labels: list[str], uncertainty_labels: list[str], evidence_labels: list[str], safety_labels: list[str], governance_labels: list[str]) -> str:
    return "truth::" + "|".join(
        [
            ",".join(fact_labels) or "none",
            ",".join(uncertainty_labels) or "none",
            ",".join(evidence_labels) or "none",
            ",".join(safety_labels) or "none",
            ",".join(governance_labels) or "none",
        ]
    )


def _build_situation_frame_id(signal_labels: list[str], role_context: str, domain_context: str, expertise_level: str) -> str:
    return "situation::" + "|".join([
        ",".join(signal_labels) or "none",
        role_context or "none",
        domain_context or "none",
        expertise_level or "none",
    ])


def _build_answer_shape_id(shape: Mapping[str, Any]) -> str:
    parts = [
        _safe_str(shape.get("length")) or "none",
        _safe_str(shape.get("tone")) or "none",
        _safe_str(shape.get("structure")) or "none",
        _safe_str(shape.get("jargon")) or "none",
        _safe_str(shape.get("evidence_depth")) or "none",
        _safe_str(shape.get("warning_position")) or "none",
        _safe_str(shape.get("directness")) or "none",
        _safe_str(shape.get("next_action")) or "none",
    ]
    return "shape::" + "|".join(parts)


def _normalize_label_list(value: Any, allowed: set[str], blocked_label: str) -> tuple[list[str], list[str]]:
    normalized = _safe_list(value)
    blocked: list[str] = []
    for label in normalized:
        if label not in allowed:
            blocked.append(blocked_label)
    return normalized, _unique_sorted(blocked)


def build_response_fit_truth_kernel_v1(truth_item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a metadata-only truth kernel."""

    truth = _as_mapping(truth_item)
    fact_labels = _unique_sorted(truth.get("fact_labels") or truth.get("facts") or [])
    uncertainty_labels = _unique_sorted(truth.get("uncertainty_labels") or truth.get("uncertainties") or [])
    evidence_boundary_labels = _unique_sorted(truth.get("evidence_boundary_labels") or truth.get("evidence_boundaries") or [])
    safety_boundary_labels = _unique_sorted(truth.get("safety_boundary_labels") or truth.get("safety_boundaries") or [])
    governance_boundary_labels = _unique_sorted(truth.get("governance_boundary_labels") or truth.get("governance_boundaries") or [])

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "truth_kernel_type": TRUTH_KERNEL_TYPE_V1,
        "truth_kernel_id": _safe_str(truth.get("truth_kernel_id")) or _build_truth_kernel_id(
            fact_labels,
            uncertainty_labels,
            evidence_boundary_labels,
            safety_boundary_labels,
            governance_boundary_labels,
        ),
        "fact_labels": fact_labels,
        "uncertainty_labels": uncertainty_labels,
        "evidence_boundary_labels": evidence_boundary_labels,
        "safety_boundary_labels": safety_boundary_labels,
        "governance_boundary_labels": governance_boundary_labels,
        "stable_truth": True,
        "metadata_only": True,
        "internal_only": True,
        "raw_content_stored": False,
        "truth_summary_label": _safe_str(truth.get("truth_summary_label") or truth.get("summary_label") or ""),
    }
    return to_response_fit_json_safe_v1(record)


def build_response_fit_human_situation_frame_v1(frame_item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a metadata-only human situation frame."""

    frame = _as_mapping(frame_item)
    role_context = _safe_str(frame.get("role_context") or frame.get("role") or "")
    domain_context = _safe_str(frame.get("domain_context") or frame.get("domain") or "")
    expertise_level = _safe_str(frame.get("expertise_level") or "")
    urgency_level = _safe_str(frame.get("urgency_level") or "")
    risk_level = _safe_str(frame.get("risk_level") or "")
    emotional_pressure = _safe_str(frame.get("emotional_pressure") or "")
    decision_burden = _safe_str(frame.get("decision_burden") or "")
    desired_detail_level = _safe_str(frame.get("desired_detail_level") or "")
    evidence_need = _safe_str(frame.get("evidence_need") or "")
    language_style = _safe_str(frame.get("language_style") or "")
    continuity_state = _safe_str(frame.get("continuity_state") or "")
    correction_history = _safe_str(frame.get("correction_history") or "")
    trust_state = _safe_str(frame.get("trust_state") or "")
    safety_boundary_need = _safe_str(frame.get("safety_boundary_need") or "")

    signal_labels = _dedupe_strings(
        frame.get("human_situation_signal_labels"),
        frame.get("signal_labels"),
        [
            key
            for key, value in (
                ("role_context", role_context),
                ("domain_context", domain_context),
                ("expertise_level", expertise_level),
                ("urgency_level", urgency_level),
                ("risk_level", risk_level),
                ("emotional_pressure", emotional_pressure),
                ("decision_burden", decision_burden),
                ("desired_detail_level", desired_detail_level),
                ("evidence_need", evidence_need),
                ("language_style", language_style),
                ("continuity_state", continuity_state),
                ("correction_history", correction_history),
                ("trust_state", trust_state),
                ("safety_boundary_need", safety_boundary_need),
            )
            if value
        ],
    )

    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "human_situation_frame_type": HUMAN_SITUATION_FRAME_TYPE_V1,
        "human_situation_frame_id": _safe_str(frame.get("human_situation_frame_id")) or _build_situation_frame_id(
            signal_labels, role_context, domain_context, expertise_level
        ),
        "role_context": role_context,
        "domain_context": domain_context,
        "expertise_level": expertise_level,
        "urgency_level": urgency_level,
        "risk_level": risk_level,
        "emotional_pressure": emotional_pressure,
        "decision_burden": decision_burden,
        "desired_detail_level": desired_detail_level,
        "evidence_need": evidence_need,
        "language_style": language_style,
        "continuity_state": continuity_state,
        "correction_history": correction_history,
        "trust_state": trust_state,
        "safety_boundary_need": safety_boundary_need,
        "human_situation_signal_labels": signal_labels,
        "dynamic_signal_metadata": {
            "dynamic": True,
            "uncertain": True,
            "correctable": True,
        },
        "metadata_only": True,
        "internal_only": True,
        "raw_content_stored": False,
        "industry_context": _safe_str(frame.get("industry_context") or frame.get("domain_context") or ""),
    }
    return to_response_fit_json_safe_v1(record)


def build_response_fit_answer_shape_v1(shape_item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a metadata-only answer shape."""

    shape = _as_mapping(shape_item)
    record = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "answer_shape_type": ANSWER_SHAPE_TYPE_V1,
        "answer_shape_id": _safe_str(shape.get("answer_shape_id")) or _build_answer_shape_id(shape),
        "length": _safe_str(shape.get("length") or shape.get("length_label") or ""),
        "tone": _safe_str(shape.get("tone") or shape.get("tone_label") or ""),
        "structure": _safe_str(shape.get("structure") or shape.get("structure_label") or ""),
        "jargon": _safe_str(shape.get("jargon") or shape.get("jargon_label") or ""),
        "evidence_depth": _safe_str(shape.get("evidence_depth") or shape.get("evidence_depth_label") or ""),
        "warning_position": _safe_str(shape.get("warning_position") or shape.get("warning_position_label") or ""),
        "directness": _safe_str(shape.get("directness") or shape.get("directness_label") or ""),
        "next_action": _safe_str(shape.get("next_action") or shape.get("next_action_label") or ""),
        "metadata_only": True,
        "internal_only": True,
        "raw_content_stored": False,
        "answer_shape_notes": _safe_str(shape.get("answer_shape_notes") or shape.get("notes") or ""),
    }
    return to_response_fit_json_safe_v1(record)


def _merge_case_components(
    case_item: Mapping[str, Any] | None,
    truth_kernel: Mapping[str, Any] | None,
    human_situation_frame: Mapping[str, Any] | None,
    answer_shape: Mapping[str, Any] | None,
) -> dict[str, Any]:
    case = dict(_as_mapping(case_item))
    if truth_kernel is not None:
        case["truth_kernel"] = _as_mapping(truth_kernel)
    if human_situation_frame is not None:
        case["human_situation_frame"] = _as_mapping(human_situation_frame)
    if answer_shape is not None:
        case["answer_shape"] = _as_mapping(answer_shape)
    return case


def _collect_blocked_for_raw_and_authority(case: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    blocked_labels: list[str] = []
    denied_authority_flags: list[str] = []

    for key in (
        "raw_prompt",
        "prompt",
        "raw_response_text",
        "response_text",
        "raw_transcript",
        "transcript_text",
        "raw_context",
        "context_text",
        "raw_private_context",
        "raw_private_data",
        "raw_text",
        "private_text",
        "live_user_text",
        "live_user_content",
        "private_memory",
        "private_memory_text",
        "hidden_material",
        "benchmark_material",
        "provider_model_output",
        "final_answer",
    ):
        if _safe_str(case.get(key)):
            if key in {"raw_prompt", "prompt"}:
                blocked_labels.append("raw_prompt_provided")
            elif key in {"raw_response_text", "response_text", "raw_text", "final_answer"}:
                blocked_labels.append("raw_response_text_provided")
            elif key in {"raw_transcript", "transcript_text"}:
                blocked_labels.append("raw_transcript_provided")
            elif key in {"raw_context", "context_text", "raw_private_context", "raw_private_data", "private_text", "live_user_text", "live_user_content"}:
                blocked_labels.append("raw_context_provided")
            elif key in {"private_memory", "private_memory_text"}:
                blocked_labels.append("private_memory_requested")
            elif key in {"hidden_material"}:
                blocked_labels.append("hidden_material_requested")
            elif key in {"benchmark_material"}:
                blocked_labels.append("benchmark_material_requested")
            elif key in {"provider_model_output"}:
                blocked_labels.append("provider_model_output_requested")

    for key in (
        "raw_private_content_requested",
        "raw_persistence_requested",
        "dot_weslr_requested",
        "private_memory_requested",
        "live_user_content_requested",
        "provider_model_output_requested",
        "hidden_material_requested",
        "benchmark_material_requested",
        "final_answer_authority",
        "public_live_authority",
        "public_ux_authority",
        "voice_authority",
        "runtime_authority",
        "live_runtime_authority",
        "model_call_authority",
        "search_call_authority",
        "advisor_call_authority",
        "official_claim_authority",
        "turing_claim_authority",
        "intelligence_claim_authority",
        "certification_claim_authority",
        "public_readiness_authority",
        "voice_readiness_authority",
        "live_user_safety_readiness_authority",
        "benchmark_score_authority",
        "model_superiority_authority",
        "raw_persistence_authority",
        "private_memory_authority",
        "unknown_engine_authority",
        "automatic_lesson_promotion_authority",
        "stereotype_assumption_requested",
        "manipulation_logic_requested",
        "fake_empathy_requested",
        "template_engine_requested",
        "role_personality_template_requested",
        "human_imitation_requested",
        "public_claim_authority",
    ):
        if _safe_bool(case.get(key)):
            if key in DENIED_AUTHORITY_FLAGS_V1:
                denied_authority_flags.append(key)
            if key in {"raw_private_content_requested", "raw_persistence_requested", "raw_persistence_authority", "private_memory_authority", "private_memory_requested", "dot_weslr_requested"}:
                blocked_labels.append("raw_private_content_requested")
            elif key in {"live_user_content_requested", "public_live_authority", "public_ux_authority", "voice_authority", "public_claim_authority", "public_readiness_authority", "voice_readiness_authority", "live_user_safety_readiness_authority"}:
                blocked_labels.append("public_live_authority_requested")
            elif key in {"runtime_authority", "live_runtime_authority", "model_call_authority", "search_call_authority", "advisor_call_authority", "unknown_engine_authority"}:
                blocked_labels.append("runtime_authority_requested")
            elif key in {"final_answer_authority"}:
                blocked_labels.append("final_answer_authority_requested")
            elif key in {"official_claim_authority", "turing_claim_authority", "intelligence_claim_authority", "certification_claim_authority"}:
                blocked_labels.append("official_claim_requested")
            elif key in {"provider_model_output_requested", "benchmark_material_requested", "benchmark_score_authority", "model_superiority_authority", "hidden_material_requested"}:
                blocked_labels.append("provider_model_output_requested")
            elif key in {"stereotype_assumption_requested"}:
                blocked_labels.append("stereotype_assumption_requested")
            elif key in {"manipulation_logic_requested"}:
                blocked_labels.append("manipulation_logic_requested")
            elif key in {"fake_empathy_requested"}:
                blocked_labels.append("fake_empathy_requested")
            elif key in {"template_engine_requested", "role_personality_template_requested", "human_imitation_requested"}:
                blocked_labels.append("template_engine_requested")
            elif key in {"automatic_lesson_promotion_authority"}:
                blocked_labels.append("automatic_lesson_promotion_requested")
            else:
                blocked_labels.append("unknown_authority_flag")

    return blocked_labels, denied_authority_flags


def _collect_unknown_engine_role_labels(case: Mapping[str, Any]) -> list[str]:
    roles = _safe_list(case.get("unknown_engine_roles") or case.get("unknown_engine_role_labels") or [])
    blocked: list[str] = []
    for role in roles:
        if role in FORBIDDEN_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("forbidden_unknown_engine_role")
        elif role not in ALLOWED_UNKNOWN_ENGINE_ROLES_V1:
            blocked.append("unknown_unknown_engine_role")
    return _unique_sorted(blocked)


def validate_response_fit_case_v1(
    case_item: Mapping[str, Any] | None = None,
    truth_kernel: Mapping[str, Any] | None = None,
    human_situation_frame: Mapping[str, Any] | None = None,
    answer_shape: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a response-fit case and fail closed on unsupported input."""

    case = _merge_case_components(case_item, truth_kernel, human_situation_frame, answer_shape)
    normalized_case = to_response_fit_json_safe_v1(case)
    if not isinstance(normalized_case, dict):
        normalized_case = {}

    blocked_labels: list[str] = []

    case_id = _safe_str(normalized_case.get("case_id") or normalized_case.get("id"))
    truth_kernel_record = _as_mapping(normalized_case.get("truth_kernel"))
    situation_frame_record = _as_mapping(normalized_case.get("human_situation_frame"))
    answer_shape_record = _as_mapping(normalized_case.get("answer_shape"))

    if not case_id:
        blocked_labels.append("missing_case_id")
    if not truth_kernel_record and not _safe_str(normalized_case.get("truth_kernel_id")):
        blocked_labels.append("missing_truth_kernel")
        blocked_labels.append("missing_truth_kernel_id")
    if not situation_frame_record:
        blocked_labels.append("missing_human_situation_frame")
    if not answer_shape_record:
        blocked_labels.append("missing_answer_shape")

    fact_labels = _unique_sorted(truth_kernel_record.get("fact_labels") or [])
    uncertainty_labels = _unique_sorted(truth_kernel_record.get("uncertainty_labels") or [])
    evidence_boundary_labels = _unique_sorted(truth_kernel_record.get("evidence_boundary_labels") or [])
    safety_boundary_labels = _unique_sorted(truth_kernel_record.get("safety_boundary_labels") or [])
    governance_boundary_labels = _unique_sorted(truth_kernel_record.get("governance_boundary_labels") or [])
    if truth_kernel_record:
        if not fact_labels:
            blocked_labels.append("missing_fact_labels")
        if not uncertainty_labels:
            blocked_labels.append("missing_uncertainty_labels")
        if not evidence_boundary_labels:
            blocked_labels.append("missing_evidence_boundary_labels")
        if not safety_boundary_labels:
            blocked_labels.append("missing_safety_boundary_labels")
        if not governance_boundary_labels:
            blocked_labels.append("missing_governance_boundary_labels")

    role_context = _safe_str(situation_frame_record.get("role_context"))
    domain_context = _safe_str(situation_frame_record.get("domain_context"))
    expertise_level = _safe_str(situation_frame_record.get("expertise_level"))
    urgency_level = _safe_str(situation_frame_record.get("urgency_level"))
    risk_level = _safe_str(situation_frame_record.get("risk_level"))
    emotional_pressure = _safe_str(situation_frame_record.get("emotional_pressure"))
    decision_burden = _safe_str(situation_frame_record.get("decision_burden"))
    desired_detail_level = _safe_str(situation_frame_record.get("desired_detail_level"))
    evidence_need = _safe_str(situation_frame_record.get("evidence_need"))
    language_style = _safe_str(situation_frame_record.get("language_style"))
    continuity_state = _safe_str(situation_frame_record.get("continuity_state"))
    correction_history = _safe_str(situation_frame_record.get("correction_history"))
    trust_state = _safe_str(situation_frame_record.get("trust_state"))
    safety_boundary_need = _safe_str(situation_frame_record.get("safety_boundary_need"))

    if not role_context:
        blocked_labels.append("missing_role_context")
    if not domain_context:
        blocked_labels.append("missing_domain_context")
    if not expertise_level:
        blocked_labels.append("missing_expertise_level")
    if not urgency_level:
        blocked_labels.append("missing_urgency_level")
    if not risk_level:
        blocked_labels.append("missing_risk_level")
    if not emotional_pressure:
        blocked_labels.append("missing_emotional_pressure")
    if not decision_burden:
        blocked_labels.append("missing_decision_burden")
    if not desired_detail_level:
        blocked_labels.append("missing_desired_detail_level")
    if not evidence_need:
        blocked_labels.append("missing_evidence_need")
    if not language_style:
        blocked_labels.append("missing_language_style")
    if not continuity_state:
        blocked_labels.append("missing_continuity_state")
    if not correction_history:
        blocked_labels.append("missing_correction_history")
    if not trust_state:
        blocked_labels.append("missing_trust_state")
    if not safety_boundary_need:
        blocked_labels.append("missing_safety_boundary_need")

    length = _safe_str(answer_shape_record.get("length"))
    tone = _safe_str(answer_shape_record.get("tone"))
    structure = _safe_str(answer_shape_record.get("structure"))
    jargon = _safe_str(answer_shape_record.get("jargon"))
    evidence_depth = _safe_str(answer_shape_record.get("evidence_depth"))
    warning_position = _safe_str(answer_shape_record.get("warning_position"))
    directness = _safe_str(answer_shape_record.get("directness"))
    next_action = _safe_str(answer_shape_record.get("next_action"))

    if not length:
        blocked_labels.append("missing_length")
    if not tone:
        blocked_labels.append("missing_tone")
    if not structure:
        blocked_labels.append("missing_structure")
    if not jargon:
        blocked_labels.append("missing_jargon")
    if not evidence_depth:
        blocked_labels.append("missing_evidence_depth")
    if not warning_position:
        blocked_labels.append("missing_warning_position")
    if not directness:
        blocked_labels.append("missing_directness")
    if not next_action:
        blocked_labels.append("missing_next_action")

    # Raw/private content and authority checks.
    raw_blocked, denied_authority_flags = _collect_blocked_for_raw_and_authority(normalized_case)
    blocked_labels.extend(raw_blocked)
    blocked_labels.extend(_collect_unknown_engine_role_labels(normalized_case))

    # Unknown labels for explicit label fields.
    signal_labels = _safe_list(situation_frame_record.get("human_situation_signal_labels") or normalized_case.get("human_situation_signal_labels") or normalized_case.get("signal_labels"))
    for label in signal_labels:
        if label not in HUMAN_SITUATION_SIGNALS_V1:
            blocked_labels.append("unknown_signal_label")
            break

    mismatch_families = _safe_list(normalized_case.get("mismatch_families") or normalized_case.get("expected_mismatch_families") or [])
    for family in mismatch_families:
        if family not in MISMATCH_FAMILIES_V1:
            blocked_labels.append("unknown_mismatch_family")
            break

    check_labels = _safe_list(normalized_case.get("check_labels") or [])
    for label in check_labels:
        if label not in CHECK_LABELS_V1:
            blocked_labels.append("unknown_check_label")
            break

    fit_label = _safe_str(normalized_case.get("fit_label") or "")
    if fit_label and fit_label not in FIT_LABELS_V1:
        blocked_labels.append("unknown_fit_label")
    fit_confidence_label = _safe_str(normalized_case.get("fit_confidence_label") or "")
    if fit_confidence_label and fit_confidence_label not in FIT_CONFIDENCE_LABELS_V1:
        blocked_labels.append("unknown_fit_confidence_label")

    # Deterministic blocked flags from specific forbidden content.
    if normalized_case.get("stereotype_assumption") or normalized_case.get("stereotype_assumption_requested"):
        blocked_labels.append("stereotype_assumption_requested")
    if normalized_case.get("manipulation_logic") or normalized_case.get("manipulation_logic_requested"):
        blocked_labels.append("manipulation_logic_requested")
    if normalized_case.get("fake_empathy") or normalized_case.get("fake_empathy_requested"):
        blocked_labels.append("fake_empathy_requested")
    if normalized_case.get("template_engine") or normalized_case.get("template_engine_requested") or normalized_case.get("persona_template"):
        blocked_labels.append("template_engine_requested")
    if normalized_case.get("human_imitation") or normalized_case.get("human_imitation_requested"):
        blocked_labels.append("human_imitation_requested")

    # Unknown / missing source registry style gate.
    if normalized_case.get("source_registry_missing"):
        blocked_labels.append("source_registry_missing")

    blocked_labels = _unique_sorted(blocked_labels)
    valid = not blocked_labels
    blocked = not valid

    if blocked_labels and any(label in blocked_labels for label in ("raw_private_content_requested", "raw_prompt_provided", "raw_response_text_provided", "raw_transcript_provided", "raw_context_provided", "private_memory_requested", "hidden_material_requested", "benchmark_material_requested")):
        fit_label = "blocked_by_privacy_boundary"
    elif blocked_labels and any(label in blocked_labels for label in ("final_answer_authority_requested", "public_live_authority_requested", "runtime_authority_requested", "unknown_authority_flag")):
        fit_label = "blocked_by_runtime_boundary"
    elif blocked_labels:
        fit_label = "needs_operator_review"
    elif not fit_label:
        fit_label = "fit_aligned"

    if not fit_confidence_label:
        fit_confidence_label = "inconclusive" if blocked_labels else "high_confidence"

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "case_type": CASE_TYPE_V1,
        "valid": valid,
        "blocked": blocked,
        "case_status": "valid" if valid else "blocked",
        "case_id": case_id,
        "truth_kernel_id": _safe_str(truth_kernel_record.get("truth_kernel_id") or normalized_case.get("truth_kernel_id") or ""),
        "truth_kernel": truth_kernel_record,
        "human_situation_frame": situation_frame_record,
        "answer_shape": answer_shape_record,
        "fit_label": fit_label,
        "fit_confidence_label": fit_confidence_label,
        "mismatch_families": mismatch_families,
        "check_labels": check_labels,
        "blocked_labels": blocked_labels,
        "denied_authority_flags": _unique_sorted(denied_authority_flags),
        "operator_review_required": True,
        "normalization_notes": {
            "metadata_only": True,
            "internal_only": True,
            "raw_content_stored": False,
        },
        "normalized_case": normalized_case,
    }


def _evidence_boundary_check(truth_kernel: Mapping[str, Any], answer_shape: Mapping[str, Any]) -> bool:
    return bool(_safe_list(truth_kernel.get("evidence_boundary_labels"))) and bool(_safe_str(answer_shape.get("evidence_depth")))


def _anti_stereotype_check(case: Mapping[str, Any]) -> bool:
    forbidden = (
        "stereotype_assumption",
        "stereotype_assumption_requested",
        "template_engine",
        "template_engine_requested",
        "persona_template",
        "role_personality_template_requested",
        "human_imitation",
        "human_imitation_requested",
    )
    return not any(_safe_bool(case.get(key)) for key in forbidden)


def _anti_manipulation_check(case: Mapping[str, Any]) -> bool:
    forbidden = (
        "manipulation_logic",
        "manipulation_logic_requested",
        "fake_empathy",
        "fake_empathy_requested",
        "flattery_optimization",
        "deception_requested",
    )
    return not any(_safe_bool(case.get(key)) for key in forbidden)


def detect_response_fit_mismatch_v1(
    case_item: Mapping[str, Any] | None = None,
    truth_kernel: Mapping[str, Any] | None = None,
    human_situation_frame: Mapping[str, Any] | None = None,
    answer_shape: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect response-fit mismatches using metadata only."""

    case = _merge_case_components(case_item, truth_kernel, human_situation_frame, answer_shape)
    truth = build_response_fit_truth_kernel_v1(case.get("truth_kernel") or case.get("truth"))
    situation = build_response_fit_human_situation_frame_v1(case.get("human_situation_frame") or case.get("situation"))
    shape = build_response_fit_answer_shape_v1(case.get("answer_shape") or case.get("shape"))

    mismatches: list[str] = []
    blocked_labels: list[str] = []

    validation = validate_response_fit_case_v1(case)
    blocked_labels.extend(validation.get("blocked_labels") or [])

    if blocked_labels:
        if any(label in blocked_labels for label in ("raw_private_content_requested", "raw_prompt_provided", "raw_response_text_provided", "raw_transcript_provided", "raw_context_provided", "private_memory_requested", "hidden_material_requested", "benchmark_material_requested")):
            fit_label = "blocked_by_privacy_boundary"
        elif any(label in blocked_labels for label in ("final_answer_authority_requested", "public_live_authority_requested", "runtime_authority_requested", "unknown_authority_flag")):
            fit_label = "blocked_by_runtime_boundary"
        else:
            fit_label = "needs_operator_review"
        fit_confidence_label = "inconclusive"
    else:
        fit_label = "fit_aligned"
        fit_confidence_label = "high_confidence"

    desired_detail = _safe_str(situation.get("desired_detail_level"))
    urgency = _safe_str(situation.get("urgency_level"))
    risk = _safe_str(situation.get("risk_level"))
    emotional_pressure = _safe_str(situation.get("emotional_pressure"))
    evidence_need = _safe_str(situation.get("evidence_need"))
    language_style = _safe_str(situation.get("language_style"))
    continuity_state = _safe_str(situation.get("continuity_state"))
    correction_history = _safe_str(situation.get("correction_history"))

    length = _safe_str(shape.get("length"))
    tone = _safe_str(shape.get("tone"))
    structure = _safe_str(shape.get("structure"))
    jargon = _safe_str(shape.get("jargon"))
    evidence_depth = _safe_str(shape.get("evidence_depth"))
    warning_position = _safe_str(shape.get("warning_position"))
    directness = _safe_str(shape.get("directness"))
    next_action = _safe_str(shape.get("next_action"))

    if desired_detail in {"high", "detailed", "expanded"} and length in {"short", "brief", "minimal"}:
        mismatches.append("too_simple")
    if desired_detail in {"low", "brief", "minimal"} and length in {"long", "verbose", "expanded"}:
        mismatches.append("too_verbose")
    if evidence_need in {"high", "strong", "deep"} and evidence_depth in {"low", "thin", "minimal"}:
        mismatches.append("evidence_depth_mismatch")
    if evidence_need in {"low", "minimal"} and evidence_depth in {"deep", "heavy", "extensive"}:
        mismatches.append("too_verbose")
    if urgency in {"high", "urgent", "immediate"} and directness not in {"direct", "very_direct", "action_first"}:
        mismatches.append("wrong_urgency")
        mismatches.append("actionability_mismatch")
    if risk in {"high", "dangerous", "safety_critical"} and warning_position not in {"early", "up_front", "first"}:
        mismatches.append("wrong_risk_posture")
    if emotional_pressure in {"high", "stressed", "frustrated", "overwhelmed"} and tone in {"cold", "robotic", "generic"}:
        mismatches.append("missed_emotional_pressure")
        mismatches.append("human_perceived_ai_tone")
    if continuity_state in {"ongoing", "continued", "prior_context"} and structure in {"standalone", "context_free"}:
        mismatches.append("lost_continuity")
    if correction_history in {"corrected", "recent_correction", "prior_fix"} and not any(token in next_action for token in ("correct", "acknowledge", "adjust", "revise")):
        mismatches.append("ignored_correction")
    if language_style in {"plain", "nontechnical", "simple"} and jargon in {"high", "technical", "dense"}:
        mismatches.append("jargon_mismatch")
    if language_style in {"technical", "expert"} and jargon in {"low", "plain", "minimal"}:
        mismatches.append("too_simple")
    if tone in {"generic", "canned", "robotic"} or structure in {"template", "canned"}:
        mismatches.append("too_generic")
        mismatches.append("human_perceived_ai_tone")
    if structure in {"template", "roleplay", "persona"}:
        mismatches.append("answer_shape_mismatch")
    if case.get("industry_context") and not _safe_str(case.get("industry_context")):
        mismatches.append("industry_context_mismatch")
    if _safe_bool(case.get("template_engine_requested")) or _safe_bool(case.get("persona_template_requested")):
        mismatches.append("answer_shape_mismatch")

    mismatches = _unique_sorted(mismatches)

    if blocked_labels:
        fit_label = validation.get("fit_label") or fit_label
        fit_confidence_label = "inconclusive"
    elif mismatches:
        fit_label = "fit_partial" if len(mismatches) <= 2 else "fit_mismatch"
        fit_confidence_label = "medium_confidence" if len(mismatches) <= 2 else "low_confidence"
    else:
        fit_label = "fit_aligned"
        fit_confidence_label = "high_confidence"

    check_labels = [
        label
        for label, passed in (
            ("anti_stereotype_check", _anti_stereotype_check(case)),
            ("anti_manipulation_check", _anti_manipulation_check(case)),
            ("continuity_check", "lost_continuity" not in mismatches),
            ("correction_check", "ignored_correction" not in mismatches),
            ("evidence_boundary_check", _evidence_boundary_check(truth, shape)),
        )
        if passed
    ]

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "fit_label": fit_label,
        "fit_confidence_label": fit_confidence_label,
        "mismatch_families": mismatches,
        "check_labels": check_labels,
        "blocked_labels": _unique_sorted(blocked_labels),
        "denied_authority_flags": _unique_sorted(validation.get("denied_authority_flags") or []),
        "truth_kernel": truth,
        "human_situation_frame": situation,
        "answer_shape": shape,
        "raw_content_stored": False,
        "operator_review_required": True,
    }


def _recommended_revision_type(mismatches: list[str], blocked_labels: list[str]) -> str:
    if blocked_labels:
        if any(label in blocked_labels for label in ("raw_private_content_requested", "raw_prompt_provided", "raw_response_text_provided", "raw_transcript_provided", "raw_context_provided", "private_memory_requested", "hidden_material_requested", "benchmark_material_requested")):
            return "remove_raw_content_and_redact"
        if any(label in blocked_labels for label in ("final_answer_authority_requested", "public_live_authority_requested", "runtime_authority_requested", "unknown_authority_flag")):
            return "remove_runtime_or_authority_claims"
        return "operator_review_required"
    if not mismatches:
        return "no_revision_needed"
    if "too_verbose" in mismatches:
        return "reduce_length_and_focus"
    if "too_simple" in mismatches:
        return "increase_detail"
    if "wrong_urgency" in mismatches:
        return "increase_directness_and_actionability"
    if "wrong_risk_posture" in mismatches:
        return "move_warning_earlier"
    if "evidence_depth_mismatch" in mismatches:
        return "adjust_evidence_depth"
    if "jargon_mismatch" in mismatches:
        return "adjust_language_register"
    if "ignored_correction" in mismatches:
        return "acknowledge_correction"
    if "lost_continuity" in mismatches:
        return "restore_continuity"
    if "fake_empathy" in mismatches or "human_perceived_ai_tone" in mismatches or "too_generic" in mismatches:
        return "remove_template_or_robotic_tone"
    return "adjust_answer_shape"


def build_response_fit_result_packet_v1(
    case_item: Mapping[str, Any] | None = None,
    validation_result: Mapping[str, Any] | None = None,
    mismatch_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a safe operator review packet."""

    case = _as_mapping(case_item)
    validation = _as_mapping(validation_result) or validate_response_fit_case_v1(case)
    mismatch = _as_mapping(mismatch_result) or detect_response_fit_mismatch_v1(case)

    blocked_labels = _unique_sorted(
        list(validation.get("blocked_labels") or []) + list(mismatch.get("blocked_labels") or [])
    )
    denied_authority_flags = _unique_sorted(
        list(validation.get("denied_authority_flags") or []) + list(mismatch.get("denied_authority_flags") or [])
    )
    mismatch_families = _unique_sorted(mismatch.get("mismatch_families") or [])
    check_labels = _unique_sorted(mismatch.get("check_labels") or [])
    fit_label = _safe_str(mismatch.get("fit_label") or validation.get("fit_label") or "needs_operator_review")
    fit_confidence_label = _safe_str(mismatch.get("fit_confidence_label") or validation.get("fit_confidence_label") or "inconclusive")

    checks = {
        label: label in check_labels
        for label in sorted(CHECK_LABELS_V1)
    }

    packet = {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "packet_type": RESULT_PACKET_TYPE_V1,
        "packet_status": "blocked" if blocked_labels else fit_label,
        "case_id": _safe_str(case.get("case_id") or validation.get("case_id") or ""),
        "truth_kernel_id": _safe_str(validation.get("truth_kernel_id") or case.get("truth_kernel_id") or ""),
        "fit_label": fit_label,
        "fit_confidence_label": fit_confidence_label,
        "truth_kernel": validation.get("truth_kernel") or mismatch.get("truth_kernel") or case.get("truth_kernel") or {},
        "human_situation_frame": validation.get("human_situation_frame") or mismatch.get("human_situation_frame") or case.get("human_situation_frame") or {},
        "answer_shape": validation.get("answer_shape") or mismatch.get("answer_shape") or case.get("answer_shape") or {},
        "mismatch_families": mismatch_families,
        "check_labels": check_labels,
        "checks": checks,
        "recommended_revision_type": _recommended_revision_type(mismatch_families, blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "operator_review_required": True,
        "raw_content_stored": False,
        "metadata_only": True,
        "internal_only": True,
        "validation_summary": {
            "valid": _safe_bool(validation.get("valid")),
            "blocked": _safe_bool(validation.get("blocked")),
            "case_status": _safe_str(validation.get("case_status") or "blocked"),
        },
        "mismatch_summary": {
            "mismatch_count": len(mismatch_families),
            "check_count": len(check_labels),
        },
    }
    return to_response_fit_json_safe_v1(packet)


def summarize_response_fit_cases_v1(value: Mapping[str, Any] | Iterable[Any]) -> dict[str, Any]:
    """Return a safe metadata-only summary of response-fit cases or results."""

    if isinstance(value, Mapping) and "records" in value:
        items = value["records"]
    else:
        items = value

    normalized_results: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, Mapping) and {"valid", "blocked", "truth_kernel"}.issubset(set(item.keys())):
            normalized_results.append(validate_response_fit_case_v1(item))
        elif isinstance(item, Mapping) and {"fit_label", "mismatch_families", "checks"}.issubset(set(item.keys())):
            packet_status = _safe_str(item.get("packet_status") or item.get("fit_label") or "needs_operator_review")
            normalized_results.append(
                {
                    "valid": packet_status not in {"blocked", "blocked_by_privacy_boundary", "blocked_by_runtime_boundary"},
                    "blocked": packet_status in {"blocked", "blocked_by_privacy_boundary", "blocked_by_runtime_boundary"},
                    "blocked_labels": item.get("blocked_labels") or [],
                    "denied_authority_flags": item.get("denied_authority_flags") or [],
                    "fit_label": item.get("fit_label") or packet_status,
                    "fit_confidence_label": item.get("fit_confidence_label") or "inconclusive",
                    "case_status": "blocked" if packet_status in {"blocked", "blocked_by_privacy_boundary", "blocked_by_runtime_boundary"} else "valid",
                    "mismatch_families": item.get("mismatch_families") or [],
                }
            )
        else:
            normalized_results.append(validate_response_fit_case_v1(item))

    blocked_labels = _unique_sorted(label for result in normalized_results for label in result.get("blocked_labels", []))
    denied_authority_flags = _unique_sorted(flag for result in normalized_results for flag in result.get("denied_authority_flags", []))
    mismatch_families = _unique_sorted(family for result in normalized_results for family in result.get("mismatch_families", []))

    fit_label_counts: dict[str, int] = {}
    fit_confidence_counts: dict[str, int] = {}
    case_status_counts: dict[str, int] = {}
    for result in normalized_results:
        fit_label = _safe_str(result.get("fit_label") or "needs_operator_review")
        fit_label_counts[fit_label] = fit_label_counts.get(fit_label, 0) + 1
        fit_conf = _safe_str(result.get("fit_confidence_label") or "inconclusive")
        fit_confidence_counts[fit_conf] = fit_confidence_counts.get(fit_conf, 0) + 1
        case_status = _safe_str(result.get("case_status") or ("valid" if _safe_bool(result.get("valid")) else "blocked"))
        case_status_counts[case_status] = case_status_counts.get(case_status, 0) + 1

    return {
        "helper_type": HELPER_TYPE_V1,
        "boundary_type": BOUNDARY_TYPE_V1,
        "summary_type": SUMMARY_TYPE_V1,
        "total_records": len(normalized_results),
        "valid_records": sum(1 for result in normalized_results if _safe_bool(result.get("valid"))),
        "blocked_records": sum(1 for result in normalized_results if _safe_bool(result.get("blocked"))),
        "blocked_label_count": len(blocked_labels),
        "blocked_labels": blocked_labels,
        "denied_authority_flags": denied_authority_flags,
        "mismatch_family_count": len(mismatch_families),
        "mismatch_families": mismatch_families,
        "fit_label_counts": fit_label_counts,
        "fit_confidence_label_counts": fit_confidence_counts,
        "case_status_counts": case_status_counts,
        "raw_content_stored": False,
        "metadata_only": True,
        "internal_only": True,
    }


__all__ = [
    "HELPER_TYPE_V1",
    "BOUNDARY_TYPE_V1",
    "TRUTH_KERNEL_TYPE_V1",
    "HUMAN_SITUATION_FRAME_TYPE_V1",
    "ANSWER_SHAPE_TYPE_V1",
    "CASE_TYPE_V1",
    "RESULT_PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "HUMAN_SITUATION_SIGNALS_V1",
    "MISMATCH_FAMILIES_V1",
    "CHECK_LABELS_V1",
    "FIT_LABELS_V1",
    "FIT_CONFIDENCE_LABELS_V1",
    "DENIED_AUTHORITY_FLAGS_V1",
    "build_response_fit_truth_kernel_v1",
    "build_response_fit_human_situation_frame_v1",
    "build_response_fit_answer_shape_v1",
    "validate_response_fit_case_v1",
    "detect_response_fit_mismatch_v1",
    "build_response_fit_result_packet_v1",
    "summarize_response_fit_cases_v1",
    "to_response_fit_json_safe_v1",
]
