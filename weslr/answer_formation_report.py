"""WESLR answer formation report helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
answer formation report artifacts. These helpers summarize answer formation
metadata artifacts only. They do not execute answer formation, compose answers,
generate final-answer prose, choose final answers, call ChatResponder,
respond_chat(), generate_chat(), providers, search, advisors, wire runtime,
persist state, write files, create judges or scores, make official claims, or
grant answer, composition, or runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr.answer_formation import (
    ADDITIONAL_FALSE_FIELDS_V1 as SOURCE_ADDITIONAL_FALSE_FIELDS_V1,
    ALLOWED_CANDIDATE_REJECTION_LABELS_V1 as SOURCE_ALLOWED_CANDIDATE_REJECTION_LABELS_V1,
    ALLOWED_GATE_STATUSES_V1 as SOURCE_ALLOWED_GATE_STATUSES_V1,
    FALSE_AUTHORITY_FIELDS_V1 as SOURCE_FALSE_AUTHORITY_FIELDS_V1,
    validate_answer_formation_artifact_v1,
    summarize_answer_formation_artifact_v1,
)

ARTIFACT_TYPE_V1 = "answer_formation_report_v1"
SCHEMA_VERSION_V1 = "answer_formation_report_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_formation_report_v1_invalid"

SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1 = "weslr/answer_formation.py"
SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_v1.py"
SOURCE_ANSWER_FORMATION_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_V1.md"
SOURCE_ANSWER_FORMATION_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_REVIEW_V1.md"
SOURCE_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
SOURCE_REPORT_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_HELPERS_V1.md"
SOURCE_REPORT_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_HELPERS_REVIEW_V1.md"
FUTURE_REPORT_HELPER_MODULE_PATH_V1 = "weslr/answer_formation_report.py"
FUTURE_REPORT_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_report_v1.py"
NEXT_LANE_V1 = "REVIEW_ANSWER_FORMATION_REPORT_HELPERS_IMPLEMENTATION_V1"

ALLOWED_METADATA_INPUTS_V1 = (
    "safe_source_path_label",
    "safe_artifact_type_label",
    "safe_schema_version_label",
    "validation_status_label",
    "blocked_status_boolean",
    "blocked_reason_label",
    "gate_status_label",
    "gate_count",
    "candidate_type_label",
    "candidate_count",
    "selected_candidate_metadata_presence_boolean",
    "candidate_rejection_reason_label",
    "no_authority_field_label",
    "no_authority_boolean",
    "visible_risk_label",
    "followup_label",
    "summary_label",
    "aggregate_label",
    "json_safe_eligibility_label",
    "markdown_safe_eligibility_label",
    "next_lane_label",
)

FORBIDDEN_INPUTS_V1 = (
    "real_user_query_text",
    "raw_prompt_text",
    "raw_response_text",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue_transcript_content",
    "final_answer_prose",
    "final_response_text",
    "answer_draft_text",
    "composed_reply_text",
    "official_benchmark_claim",
    "official_turing_claim",
    "official_iq_claim",
    "certification_claim",
    "product_readiness_claim",
    "consciousness_sentience_claim",
    "official_score",
    "judge_decision",
    "scoring_result",
    "dot_weslr_state_payload",
    "feature_flag_activation_payload",
    "runtime_wiring_payload",
    "chat_responder_call",
    "respond_chat_call",
    "generate_chat_call",
)

FALSE_AUTHORITY_FIELDS_V1 = (
    "answer_formation_attempted",
    "answer_formation_authorized",
    "answer_composition_attempted",
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
    "chat_responder_called",
    "chat_responder_modified",
    "runtime_wired",
    "user_facing_output_created",
)

REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "report_metadata_not_answer_text",
    "answer_formation_report_not_final_answer",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "report_existence_not_runtime_authority",
    "answer_formation_execution_requires_separate_approval",
    "answer_composition_requires_separate_approval",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "occ_openclaw_not_deployed_weslr",
)

VISIBLE_RISKS_V1 = (
    "metadata-overread",
    "report-as-authority",
    "artifact/report-as-authority",
    "validation-pass-as-authority",
    "helper-existence-as-authority",
    "renderer wording drift",
    "final-answer-prose leak",
    "candidate-metadata-as-answer-draft",
    "aggregate-label-as-readiness",
    "state-frame-as-runtime-authority",
    "OCC/WESLR identity confusion",
    "implementation-as-runtime-authority",
    "future-lane-compression-risk",
)

FOLLOWUPS_V1 = (
    "review_report_helper_implementation_in_separate_lane",
    "keep_answer_formation_execution_separate",
    "keep_answer_composition_separate",
    "keep_final_answer_dry_run_separate",
    "keep_runtime_live_chat_separate",
)

ALLOWED_AGGREGATE_LABELS_V1 = (
    "all_source_artifacts_metadata_only",
    "all_source_artifacts_internal_only",
    "all_authority_fields_false",
    "answer_formation_not_attempted",
    "answer_composition_not_attempted",
    "final_answer_not_generated",
    "runtime_not_wired",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
    "blocked_artifacts_present",
    "visible_risks_present",
    "validation_errors_present",
    "safe_markdown_eligible",
    "json_safe_eligible",
)

SUMMARY_LABELS_V1 = (
    "metadata_only_report",
    "internal_only_report",
    "helper_only_report",
    "report_only_metadata",
    "non_runtime_report",
    "answer_formation_not_attempted",
    "answer_composition_not_attempted",
    "final_answer_not_generated",
    "runtime_not_wired",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "helper_only",
    "report_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "import_safe",
    "side_effect_free",
    "in_memory_only",
    "qualitative_only",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    *_REQUIRED_TRUE_FIELDS,
    "source_answer_formation_helper_module_path",
    "source_answer_formation_test_module_path",
    "source_answer_formation_helpers_design_doc",
    "source_answer_formation_helpers_review_doc",
    "source_answer_formation_helpers_implementation_review_doc",
    "source_report_helpers_design_doc",
    "source_report_helpers_review_doc",
    "future_report_helper_module_path",
    "future_report_test_module_path",
    "allowed_metadata_inputs",
    "forbidden_inputs_checked",
    "source_artifact_summary",
    "validation_summary",
    "gate_summary",
    "candidate_summary",
    "rejection_summary",
    "aggregate_labels",
    "blocked",
    "blocked_reasons",
    "visible_risks",
    "followups",
    "summary_labels",
    "validation_labels",
    "required_false_no_authority_fields",
    "required_no_authority_labels",
    "next_lane",
    *FALSE_AUTHORITY_FIELDS_V1,
)

_UNSAFE_KEY_FRAGMENTS = (
    "real_user_query",
    "raw_prompt",
    "raw_response",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue",
    "final_answer_prose",
    "final_response_text",
    "answer_draft_text",
    "composed_reply_text",
    "official_score",
    "judge_decision",
    "scoring_result",
    "dot_weslr_state_payload",
    "feature_flag_activation",
    "runtime_wiring_payload",
)

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | {
    "source_answer_formation_helper_module_path",
    "source_answer_formation_test_module_path",
    "answer_formation_attempted",
    "answer_formation_authorized",
    "answer_formation_not_attempted",
    "answer_formation_execution_requires_separate_approval",
    "answer_formation_report_not_final_answer",
    "final_answer_generated",
    "final_answer_not_generated",
    "final_answer_generation_requires_separate_approval",
    "runtime_authority_granted",
    "runtime_not_wired",
    "runtime_wiring_requires_separate_approval",
    "raw_content_allowed",
    "official_claim_allowed",
    "official_claims_not_allowed",
    "report_metadata_not_answer_text",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "provider_calls_not_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "dot_weslr_not_written",
}

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "raw_prompt:", "raw_response:", "real user query:"),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "hidden_prompt_detected": ("hidden prompt:", "system prompt hidden"),
    "answer_key_detected": ("answer key:", "correct answer:"),
    "provider_output_detected": ("provider output:", "model output:", "search output:", "advisor output:", "llm output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output", "chat responder runtime output"),
    "live_dialogue_detected": ("live dialogue transcript", "live dialogue:"),
    "final_answer_detected": ("final answer:", "final answer prose", "final response text:", "final_answer_text"),
    "answer_draft_detected": ("answer draft:", "draft answer:", "answer draft text", "composed reply:"),
    "official_claim_detected": (
        "official turing pass",
        "passed the turing test",
        "official iq",
        "official benchmark",
        "certified product-ready",
        "product readiness certified",
    ),
    "judge_or_score_detected": ("official score:", "score: 100", "judge decision:", "judge_authority_granted=true"),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
    "provider_call_detected": ("model_call_made=true", "search_call_made=true", "advisor_call_made=true", "provider_call_made=true"),
    "dot_weslr_write_detected": ("write .weslr", ".weslr write", "dot_weslr_write_performed=true"),
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag"),
    "answer_authority_detected": ("answer authority granted", "answer_authority_granted=true", "approved for live answers"),
    "composition_authority_detected": ("composition authority granted", "answer_composition_authorized=true"),
    "runtime_authority_detected": ("runtime authority granted", "runtime_authority_granted=true"),
    "consciousness_claim_detected": ("weslr is conscious", "weslr is sentient", "consciousness proven", "sentience proven"),
    "identity_confusion_detected": ("occ is weslr", "openclaw is weslr", "occ/openclaw is weslr"),
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(deepcopy(value))
    if isinstance(value, set):
        return sorted(deepcopy(value), key=repr)
    return [deepcopy(value)]


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _text(value: Any) -> str:
    return value.lower() if isinstance(value, str) else ""


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            child = f"{path}[{idx}]"
            yield child, item
            yield from _walk(item, child)


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        _append_unique(labels, str(error).split(":", 1)[0])
    return labels


def _unsafe_detection_labels(validation_or_detections: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for label in _TEXT_MARKERS:
        if validation_or_detections.get(label) is True:
            _append_unique(labels, label)
    return labels


def _detect_unsafe_content(value: Any) -> dict[str, bool]:
    found = {label: False for label in _TEXT_MARKERS}
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        key_l = key.lower()
        if any(fragment in key_l for fragment in _UNSAFE_KEY_FRAGMENTS) and key_l not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            if "final_answer" in key_l or "final_response" in key_l:
                found["final_answer_detected"] = True
            elif "answer_draft" in key_l or "composed_reply" in key_l:
                found["answer_draft_detected"] = True
            elif "provider" in key_l or "model" in key_l or "search" in key_l or "advisor" in key_l:
                found["provider_output_detected"] = True
            elif "runtime" in key_l:
                found["runtime_output_detected"] = True
            elif "private" in key_l:
                found["private_content_detected"] = True
            elif "hidden" in key_l:
                found["hidden_prompt_detected"] = True
            elif "answer_key" in key_l:
                found["answer_key_detected"] = True
            elif "judge" in key_l or "score" in key_l:
                found["judge_or_score_detected"] = True
            else:
                found["raw_content_detected"] = True
        text = _text(item)
        if not text:
            continue
        for label, markers in _TEXT_MARKERS.items():
            if any(marker in text for marker in markers):
                found[label] = True
    return found


def _invalid_json_safe_wrapper_v1(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    labels = _safe_error_labels(list(reason_labels)) or ["invalid_or_unsafe_report"]
    return {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "blocked": True,
        "valid": False,
        "errors": labels,
        "unsafe_content_not_copied": True,
        "metadata_only": True,
        "internal_only": True,
        "report_only": True,
        "report_metadata_not_answer_text": True,
        "answer_formation_report_not_final_answer": True,
        "validation_pass_not_answer_authority": True,
        "validation_pass_not_composition_authority": True,
        "next_lane": NEXT_LANE_V1,
    }


def _count_values(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _safe_source_artifact_summaries(source_artifacts: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for artifact in source_artifacts:
        if not isinstance(artifact, Mapping):
            summaries.append({
                "artifact_type": "artifact_not_mapping",
                "valid": False,
                "blocked": True,
                "validation_error_labels": ["artifact_not_mapping"],
            })
            continue
        source_summary = summarize_answer_formation_artifact_v1(artifact)
        summaries.append({
            "artifact_type": str(source_summary.get("artifact_type", "unknown_artifact_type")),
            "valid": bool(source_summary.get("valid")),
            "blocked": bool(source_summary.get("blocked")),
            "metadata_only": bool(source_summary.get("metadata_only")),
            "internal_only": bool(source_summary.get("internal_only")),
            "helper_only": bool(source_summary.get("helper_only")),
            "all_authority_flags_false": bool(source_summary.get("all_authority_flags_false")),
            "gate_status_count": int(source_summary.get("gate_status_count", 0)),
            "candidate_count": int(source_summary.get("candidate_count", 0)),
            "rejection_label_count": int(source_summary.get("rejection_label_count", 0)),
            "validation_error_labels": [str(label) for label in _as_list(source_summary.get("validation_error_labels"))],
            "next_lane": str(source_summary.get("next_lane", "unknown_next_lane")),
        })
    return summaries


def _derive_gate_summary(source_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    statuses: list[str] = []
    for artifact in source_artifacts:
        gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
        if isinstance(gates, Mapping):
            for status in gates.values():
                statuses.append(str(status))
    return {
        "gate_status_counts": _count_values(statuses),
        "allowed_gate_statuses": list(SOURCE_ALLOWED_GATE_STATUSES_V1),
        "gate_status_total": len(statuses),
    }


def _derive_candidate_summary(source_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    labels: list[str] = []
    selected_count = 0
    total = 0
    for artifact in source_artifacts:
        metadata = artifact.get("candidate_formation_metadata") if isinstance(artifact, Mapping) else None
        if not isinstance(metadata, Mapping):
            continue
        for label in _as_list(metadata.get("candidate_type_labels")):
            labels.append(str(label))
        count = metadata.get("candidate_count", 0)
        if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
            total += count
        if metadata.get("selected_candidate_metadata_present") is True:
            selected_count += 1
    return {
        "candidate_type_label_counts": _count_values(labels),
        "candidate_count_total": total,
        "selected_candidate_metadata_present_count": selected_count,
    }


def _derive_rejection_summary(source_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    labels: list[str] = []
    for artifact in source_artifacts:
        metadata = artifact.get("candidate_rejection_metadata") if isinstance(artifact, Mapping) else None
        if isinstance(metadata, Mapping):
            labels.extend(str(label) for label in _as_list(metadata.get("rejection_reason_labels")))
    return {
        "rejection_label_counts": _count_values(labels),
        "allowed_rejection_labels": list(SOURCE_ALLOWED_CANDIDATE_REJECTION_LABELS_V1),
        "rejection_label_total": len(labels),
    }


def derive_answer_formation_report_labels_v1(report_or_metadata: Mapping[str, Any]) -> list[str]:
    """Derive safe aggregate labels from report metadata only."""

    labels: list[str] = []
    summaries = _as_list(report_or_metadata.get("source_artifact_summary")) if isinstance(report_or_metadata, Mapping) else []
    validation_summary = report_or_metadata.get("validation_summary", {}) if isinstance(report_or_metadata, Mapping) else {}

    if summaries and all(isinstance(item, Mapping) and item.get("metadata_only") is True for item in summaries):
        _append_unique(labels, "all_source_artifacts_metadata_only")
    if summaries and all(isinstance(item, Mapping) and item.get("internal_only") is True for item in summaries):
        _append_unique(labels, "all_source_artifacts_internal_only")
    if isinstance(report_or_metadata, Mapping):
        if all(report_or_metadata.get(flag) is False for flag in FALSE_AUTHORITY_FIELDS_V1):
            _append_unique(labels, "all_authority_fields_false")
        if report_or_metadata.get("answer_formation_attempted") is False:
            _append_unique(labels, "answer_formation_not_attempted")
        if report_or_metadata.get("answer_composition_attempted") is False:
            _append_unique(labels, "answer_composition_not_attempted")
        if report_or_metadata.get("final_answer_generated") is False:
            _append_unique(labels, "final_answer_not_generated")
        if report_or_metadata.get("runtime_wired") is False:
            _append_unique(labels, "runtime_not_wired")
        if report_or_metadata.get("provider_call_made") is False:
            _append_unique(labels, "provider_calls_not_made")
        if report_or_metadata.get("dot_weslr_write_performed") is False:
            _append_unique(labels, "dot_weslr_not_written")
        if report_or_metadata.get("judge_authority_granted") is False and report_or_metadata.get("scoring_authorized") is False:
            _append_unique(labels, "judges_scoring_not_authorized")
        if report_or_metadata.get("official_claim_allowed") is False:
            _append_unique(labels, "official_claims_not_allowed")
    if any(isinstance(item, Mapping) and item.get("blocked") is True for item in summaries):
        _append_unique(labels, "blocked_artifacts_present")
    if isinstance(report_or_metadata, Mapping) and _as_list(report_or_metadata.get("visible_risks")):
        _append_unique(labels, "visible_risks_present")
    if isinstance(validation_summary, Mapping) and validation_summary.get("validation_error_labels"):
        _append_unique(labels, "validation_errors_present")
    _append_unique(labels, "safe_markdown_eligible")
    _append_unique(labels, "json_safe_eligible")
    return labels


def _validation_summary_from_sources(source_artifacts: list[Mapping[str, Any]]) -> dict[str, Any]:
    error_labels: list[str] = []
    valid_count = 0
    blocked_count = 0
    for artifact in source_artifacts:
        validation = validate_answer_formation_artifact_v1(artifact) if isinstance(artifact, Mapping) else {"valid": False, "blocked": True, "errors": ["artifact_not_mapping"]}
        if validation.get("valid") is True:
            valid_count += 1
        if validation.get("blocked") is True:
            blocked_count += 1
        for label in _safe_error_labels(_as_list(validation.get("errors"))):
            _append_unique(error_labels, label)
        for label in _unsafe_detection_labels(validation):
            _append_unique(error_labels, label)
    return {
        "source_artifact_count": len(source_artifacts),
        "valid_source_artifact_count": valid_count,
        "blocked_source_artifact_count": blocked_count,
        "validation_error_labels": error_labels,
        "validation_pass_means_metadata_quality_evidence_only": True,
    }


def _derive_blocked_reasons(report: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    detections = _detect_unsafe_content(report)
    for label, detected in detections.items():
        if detected:
            _append_unique(reasons, label)
    for flag in FALSE_AUTHORITY_FIELDS_V1:
        if report.get(flag) is not False:
            _append_unique(reasons, f"authority_flag_not_false:{flag}")
    validation_summary = report.get("validation_summary")
    if isinstance(validation_summary, Mapping) and validation_summary.get("blocked_source_artifact_count", 0):
        _append_unique(reasons, "blocked_source_artifacts_present")
    if isinstance(validation_summary, Mapping) and validation_summary.get("validation_error_labels"):
        _append_unique(reasons, "source_validation_errors_present")
    return reasons


def build_answer_formation_report_v1(
    source_artifacts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    *,
    allowed_metadata_inputs: list[str] | tuple[str, ...] | None = None,
    forbidden_inputs_checked: list[str] | tuple[str, ...] | None = None,
    visible_risks: list[str] | tuple[str, ...] | None = None,
    followups: list[str] | tuple[str, ...] | None = None,
    summary_labels: list[str] | tuple[str, ...] | None = None,
    validation_labels: list[str] | tuple[str, ...] | None = None,
    blocked_reasons: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe in-memory answer formation report metadata artifact."""

    safe_sources = [item for item in _as_list(source_artifacts) if isinstance(item, Mapping)]
    validation_summary = _validation_summary_from_sources(safe_sources)
    report: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "helper_only": True,
        "report_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free": True,
        "in_memory_only": True,
        "qualitative_only": True,
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_answer_formation_test_module_path": SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1,
        "source_answer_formation_helpers_design_doc": SOURCE_ANSWER_FORMATION_HELPERS_DESIGN_DOC_V1,
        "source_answer_formation_helpers_review_doc": SOURCE_ANSWER_FORMATION_HELPERS_REVIEW_DOC_V1,
        "source_answer_formation_helpers_implementation_review_doc": SOURCE_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1,
        "source_report_helpers_design_doc": SOURCE_REPORT_HELPERS_DESIGN_DOC_V1,
        "source_report_helpers_review_doc": SOURCE_REPORT_HELPERS_REVIEW_DOC_V1,
        "future_report_helper_module_path": FUTURE_REPORT_HELPER_MODULE_PATH_V1,
        "future_report_test_module_path": FUTURE_REPORT_TEST_MODULE_PATH_V1,
        "allowed_metadata_inputs": _as_list(allowed_metadata_inputs) or list(ALLOWED_METADATA_INPUTS_V1),
        "forbidden_inputs_checked": _as_list(forbidden_inputs_checked) or list(FORBIDDEN_INPUTS_V1),
        "source_artifact_summary": _safe_source_artifact_summaries(safe_sources),
        "validation_summary": validation_summary,
        "gate_summary": _derive_gate_summary(safe_sources),
        "candidate_summary": _derive_candidate_summary(safe_sources),
        "rejection_summary": _derive_rejection_summary(safe_sources),
        "aggregate_labels": [],
        "blocked": False,
        "blocked_reasons": _as_list(blocked_reasons),
        "visible_risks": _as_list(visible_risks) or list(VISIBLE_RISKS_V1),
        "followups": _as_list(followups) or list(FOLLOWUPS_V1),
        "summary_labels": list(dict.fromkeys([*SUMMARY_LABELS_V1, *[str(item) for item in _as_list(summary_labels)]])),
        "validation_labels": _as_list(validation_labels) or ["validation_pass_metadata_quality_evidence_only"],
        "required_false_no_authority_fields": {field: False for field in FALSE_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for flag in FALSE_AUTHORITY_FIELDS_V1:
        report[flag] = False
    report["aggregate_labels"] = derive_answer_formation_report_labels_v1(report)
    for reason in _derive_blocked_reasons(report):
        _append_unique(report["blocked_reasons"], reason)
    report["blocked"] = bool(report["blocked_reasons"])
    return report


def validate_answer_formation_report_v1(report: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one answer formation report without side effects."""

    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "warnings": warnings,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "source_artifact_summary_valid": False,
        "validation_summary_valid": False,
        "gate_summary_valid": False,
        "candidate_summary_valid": False,
        "rejection_summary_valid": False,
        "aggregate_labels_valid": False,
        "safe_to_render": False,
        "json_safe": False,
    }
    for label in _TEXT_MARKERS:
        result[label] = False

    if not isinstance(report, Mapping):
        errors.append("artifact_not_mapping")
        return result

    result["artifact_type"] = report.get("artifact_type")
    if report.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_invalid")
    if report.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")

    for field in _REQUIRED_FIELDS:
        if field not in report:
            errors.append(f"missing_required_field:{field}")

    for field in _REQUIRED_TRUE_FIELDS:
        if report.get(field) is not True:
            errors.append(f"required_true_field_invalid:{field}")

    safety_ok = True
    for flag in FALSE_AUTHORITY_FIELDS_V1:
        if report.get(flag) is not False:
            safety_ok = False
            errors.append(f"authority_flag_not_false:{flag}")
    result["safety_booleans_valid"] = safety_ok

    required_false = report.get("required_false_no_authority_fields")
    if not isinstance(required_false, Mapping):
        errors.append("required_false_no_authority_fields_not_mapping")
    else:
        for flag in FALSE_AUTHORITY_FIELDS_V1:
            if required_false.get(flag) is not False:
                errors.append(f"required_false_map_invalid:{flag}")

    expected_paths = {
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_answer_formation_test_module_path": SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1,
        "source_answer_formation_helpers_design_doc": SOURCE_ANSWER_FORMATION_HELPERS_DESIGN_DOC_V1,
        "source_answer_formation_helpers_review_doc": SOURCE_ANSWER_FORMATION_HELPERS_REVIEW_DOC_V1,
        "source_answer_formation_helpers_implementation_review_doc": SOURCE_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1,
        "source_report_helpers_design_doc": SOURCE_REPORT_HELPERS_DESIGN_DOC_V1,
        "source_report_helpers_review_doc": SOURCE_REPORT_HELPERS_REVIEW_DOC_V1,
        "future_report_helper_module_path": FUTURE_REPORT_HELPER_MODULE_PATH_V1,
        "future_report_test_module_path": FUTURE_REPORT_TEST_MODULE_PATH_V1,
        "next_lane": NEXT_LANE_V1,
    }
    for key, expected in expected_paths.items():
        if report.get(key) != expected:
            errors.append(f"{key}_invalid")

    allowed_inputs = [str(item) for item in _as_list(report.get("allowed_metadata_inputs"))]
    unknown_inputs = [item for item in allowed_inputs if item not in ALLOWED_METADATA_INPUTS_V1]
    if unknown_inputs:
        errors.append("unknown_allowed_metadata_inputs")
        result["unknown_allowed_metadata_inputs"] = unknown_inputs

    forbidden_checked = [str(item) for item in _as_list(report.get("forbidden_inputs_checked"))]
    missing_forbidden_checks = [item for item in FORBIDDEN_INPUTS_V1 if item not in forbidden_checked]
    if missing_forbidden_checks:
        errors.append("missing_forbidden_input_checks")
        result["missing_forbidden_input_checks"] = missing_forbidden_checks

    no_authority_labels = [str(item) for item in _as_list(report.get("required_no_authority_labels"))]
    missing_no_authority_labels = [item for item in REQUIRED_NO_AUTHORITY_LABELS_V1 if item not in no_authority_labels]
    if missing_no_authority_labels:
        errors.append("missing_no_authority_labels")
        result["missing_no_authority_labels"] = missing_no_authority_labels

    source_summary = report.get("source_artifact_summary")
    source_summary_ok = isinstance(source_summary, list) and all(isinstance(item, Mapping) for item in source_summary)
    if not source_summary_ok:
        errors.append("source_artifact_summary_invalid")
    result["source_artifact_summary_valid"] = source_summary_ok

    validation_summary = report.get("validation_summary")
    validation_summary_ok = isinstance(validation_summary, Mapping)
    if not validation_summary_ok:
        errors.append("validation_summary_not_mapping")
    else:
        for key in ("source_artifact_count", "valid_source_artifact_count", "blocked_source_artifact_count"):
            value = validation_summary.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"validation_summary_count_invalid:{key}")
                validation_summary_ok = False
        if not isinstance(validation_summary.get("validation_error_labels", []), list):
            errors.append("validation_error_labels_not_list")
            validation_summary_ok = False
    result["validation_summary_valid"] = validation_summary_ok

    gate_summary = report.get("gate_summary")
    gate_summary_ok = isinstance(gate_summary, Mapping) and isinstance(gate_summary.get("gate_status_counts"), Mapping)
    if not gate_summary_ok:
        errors.append("gate_summary_invalid")
    else:
        for status in gate_summary.get("gate_status_counts", {}):
            if status not in SOURCE_ALLOWED_GATE_STATUSES_V1:
                errors.append("gate_summary_unknown_status")
                gate_summary_ok = False
    result["gate_summary_valid"] = gate_summary_ok

    candidate_summary = report.get("candidate_summary")
    candidate_summary_ok = isinstance(candidate_summary, Mapping)
    if not candidate_summary_ok:
        errors.append("candidate_summary_not_mapping")
    else:
        total = candidate_summary.get("candidate_count_total", 0)
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            errors.append("candidate_count_total_invalid")
            candidate_summary_ok = False
    result["candidate_summary_valid"] = candidate_summary_ok

    rejection_summary = report.get("rejection_summary")
    rejection_summary_ok = isinstance(rejection_summary, Mapping)
    if not rejection_summary_ok:
        errors.append("rejection_summary_not_mapping")
    else:
        labels = rejection_summary.get("rejection_label_counts", {})
        if not isinstance(labels, Mapping):
            errors.append("rejection_label_counts_not_mapping")
            rejection_summary_ok = False
        else:
            for label in labels:
                if label not in SOURCE_ALLOWED_CANDIDATE_REJECTION_LABELS_V1:
                    errors.append("unknown_rejection_summary_label")
                    rejection_summary_ok = False
    result["rejection_summary_valid"] = rejection_summary_ok

    aggregate_labels = [str(item) for item in _as_list(report.get("aggregate_labels"))]
    unknown_aggregate_labels = [label for label in aggregate_labels if label not in ALLOWED_AGGREGATE_LABELS_V1]
    if unknown_aggregate_labels:
        errors.append("unknown_aggregate_labels")
        result["unknown_aggregate_labels"] = unknown_aggregate_labels
    result["aggregate_labels_valid"] = not unknown_aggregate_labels

    detections = _detect_unsafe_content(report)
    for label, detected in detections.items():
        result[label] = detected
        if detected:
            errors.append(label)

    blocked_reasons = [str(item) for item in _as_list(report.get("blocked_reasons"))]
    if report.get("blocked") is True and not blocked_reasons:
        errors.append("blocked_without_reasons")
    if report.get("blocked") is False and blocked_reasons:
        errors.append("blocked_reasons_present_when_not_blocked")
    if report.get("blocked") not in (True, False):
        errors.append("blocked_not_boolean")

    try:
        json_safe = to_answer_formation_report_json_safe_v1(dict(report))
        result["json_safe"] = isinstance(json_safe, Mapping)
    except Exception:  # pragma: no cover - defensive only; no unsafe message is exposed.
        result["json_safe"] = False
        errors.append("json_safe_conversion_failed")

    result["safe_to_render"] = not any(bool(result[label]) for label in _TEXT_MARKERS)
    result["valid"] = not errors and report.get("blocked") is False
    result["blocked"] = not result["valid"]
    return result


def summarize_answer_formation_report_v1(report: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one answer formation report using safe labels only."""

    validation = validate_answer_formation_report_v1(report)
    validation_summary = report.get("validation_summary") if isinstance(report, Mapping) else None
    gate_summary = report.get("gate_summary") if isinstance(report, Mapping) else None
    candidate_summary = report.get("candidate_summary") if isinstance(report, Mapping) else None
    rejection_summary = report.get("rejection_summary") if isinstance(report, Mapping) else None
    safe_error_labels = _safe_error_labels(validation["errors"])
    for label in _unsafe_detection_labels(validation):
        _append_unique(safe_error_labels, label)
    return {
        "artifact_type": str(report.get("artifact_type", INVALID_ARTIFACT_TYPE_V1)) if isinstance(report, Mapping) and validation["valid"] else INVALID_ARTIFACT_TYPE_V1,
        "schema_version": str(report.get("schema_version", "")) if isinstance(report, Mapping) and validation["valid"] else "",
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "metadata_only": bool(isinstance(report, Mapping) and report.get("metadata_only") is True),
        "helper_only": bool(isinstance(report, Mapping) and report.get("helper_only") is True),
        "report_only": bool(isinstance(report, Mapping) and report.get("report_only") is True),
        "all_authority_fields_false": bool(validation["safety_booleans_valid"]),
        "source_artifact_count": validation_summary.get("source_artifact_count", 0) if isinstance(validation_summary, Mapping) else 0,
        "valid_source_artifact_count": validation_summary.get("valid_source_artifact_count", 0) if isinstance(validation_summary, Mapping) else 0,
        "blocked_source_artifact_count": validation_summary.get("blocked_source_artifact_count", 0) if isinstance(validation_summary, Mapping) else 0,
        "gate_status_counts": dict(gate_summary.get("gate_status_counts", {})) if isinstance(gate_summary, Mapping) else {},
        "candidate_count_total": candidate_summary.get("candidate_count_total", 0) if isinstance(candidate_summary, Mapping) else 0,
        "rejection_label_counts": dict(rejection_summary.get("rejection_label_counts", {})) if isinstance(rejection_summary, Mapping) else {},
        "visible_risk_count": len(_as_list(report.get("visible_risks"))) if isinstance(report, Mapping) else 0,
        "followup_count": len(_as_list(report.get("followups"))) if isinstance(report, Mapping) else 0,
        "validation_error_labels": safe_error_labels,
        "safe_summary_labels": _as_list(report.get("summary_labels")) if isinstance(report, Mapping) and validation["valid"] else [],
        "next_lane": str(report.get("next_lane", NEXT_LANE_V1)) if isinstance(report, Mapping) and report.get("next_lane") == NEXT_LANE_V1 else NEXT_LANE_V1,
    }


def _safe_blocked_markdown_v1(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reason_labels = _safe_error_labels(_as_list(validation.get("errors")))
    for label in _unsafe_detection_labels(validation):
        _append_unique(reason_labels, label)
    if not reason_labels:
        reason_labels = ["invalid_or_blocked_report"]
    lines = [
        "# Answer Formation Report V1 — Blocked",
        "",
        "## Result Status",
        f"- valid: `{bool(validation.get('valid'))}`",
        "- blocked: `True`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- report_only: `True`",
        "",
        "## Safe Reason Labels",
    ]
    for reason in reason_labels:
        lines.append(f"- `{reason}`")
    lines.extend([
        "",
        "## Safe No-Authority Fields",
        "- `answer_formation_attempted=false`",
        "- `answer_formation_authorized=false`",
        "- `answer_composition_attempted=false`",
        "- `answer_composition_authorized=false`",
        "- `final_answer_generated=false`",
        "- `answer_authority_granted=false`",
        "- `composition_authority_granted=false`",
        "- `runtime_authority_granted=false`",
        "- `prompt_execution_allowed=false`",
        "- `live_dialogue_allowed=false`",
        "- `raw_content_allowed=false`",
        "- `official_claim_allowed=false`",
        "- `model_call_made=false`",
        "- `search_call_made=false`",
        "- `advisor_call_made=false`",
        "- `provider_call_made=false`",
        "- `dot_weslr_write_performed=false`",
        "- `feature_flag_enabled=false`",
        "- `judge_authority_granted=false`",
        "- `scoring_authorized=false`",
        "",
        "## Safety Confirmation",
        "- `unsafe_content_not_rendered`",
        "- `report_metadata_not_answer_text`",
        "- `answer_formation_report_not_final_answer`",
        "- `validation_pass_not_answer_authority`",
        "- `validation_pass_not_composition_authority`",
        "- `runtime_wiring_requires_separate_approval`",
        f"- next_lane: `{summary.get('next_lane', NEXT_LANE_V1)}`",
    ])
    return "\n".join(lines) + "\n"


def render_answer_formation_report_markdown_v1(report: Mapping[str, Any]) -> str:
    """Render validation-gated safe Markdown for one answer formation report."""

    validation = validate_answer_formation_report_v1(report)
    summary = summarize_answer_formation_report_v1(report)
    if validation["valid"] is not True or validation["safe_to_render"] is not True:
        return _safe_blocked_markdown_v1(validation, summary)

    lines = [
        "# Answer Formation Report V1",
        "",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- metadata_only: `{summary['metadata_only']}`",
        f"- helper_only: `{summary['helper_only']}`",
        f"- report_only: `{summary['report_only']}`",
        f"- all_authority_fields_false: `{summary['all_authority_fields_false']}`",
        f"- future_report_helper_module_path: `{report.get('future_report_helper_module_path')}`",
        f"- future_report_test_module_path: `{report.get('future_report_test_module_path')}`",
        f"- source_answer_formation_helper_module_path: `{report.get('source_answer_formation_helper_module_path')}`",
        f"- source_answer_formation_test_module_path: `{report.get('source_answer_formation_test_module_path')}`",
        "",
        "## Source Artifact Counts",
        f"- source_artifact_count: `{summary['source_artifact_count']}`",
        f"- valid_source_artifact_count: `{summary['valid_source_artifact_count']}`",
        f"- blocked_source_artifact_count: `{summary['blocked_source_artifact_count']}`",
        "",
        "## Gate Status Counts",
    ]
    for key, count in sorted(summary["gate_status_counts"].items()):
        lines.append(f"- `{key}`: `{count}`")
    if not summary["gate_status_counts"]:
        lines.append("- `none`")

    lines.extend([
        "",
        "## Candidate And Rejection Counts",
        f"- candidate_count_total: `{summary['candidate_count_total']}`",
    ])
    for key, count in sorted(summary["rejection_label_counts"].items()):
        lines.append(f"- rejection_label `{key}`: `{count}`")
    if not summary["rejection_label_counts"]:
        lines.append("- rejection_label `none`: `0`")

    lines.extend(["", "## Aggregate Labels"])
    for label in _as_list(report.get("aggregate_labels")):
        lines.append(f"- `{label}`")

    lines.extend(["", "## Visible Risks"])
    for label in _as_list(report.get("visible_risks")):
        lines.append(f"- `{label}`")

    lines.extend(["", "## Followups"])
    for label in _as_list(report.get("followups")):
        lines.append(f"- `{label}`")

    lines.extend(["", "## Validation Labels"])
    for label in _as_list(report.get("validation_labels")):
        lines.append(f"- `{label}`")

    lines.extend([
        "",
        "## Safety Confirmation",
        "- `report_metadata_not_answer_text`",
        "- `answer_formation_report_not_final_answer`",
        "- `validation_pass_not_answer_authority`",
        "- `validation_pass_not_composition_authority`",
        "- `runtime_wiring_requires_separate_approval`",
        f"- next_lane: `{summary['next_lane']}`",
    ])
    return "\n".join(lines) + "\n"


def to_answer_formation_report_json_safe_v1(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe deep copy of one answer formation report."""

    detections = _detect_unsafe_content(report)
    detection_labels = _unsafe_detection_labels(detections)
    if detection_labels:
        return _invalid_json_safe_wrapper_v1(detection_labels)
    safe = _json_safe(report)
    if not isinstance(safe, dict):
        return _invalid_json_safe_wrapper_v1(["artifact_not_mapping"])
    return safe
