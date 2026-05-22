"""WESLR answer formation report-run V1.

Deterministic, import-safe, metadata-only report-run helpers for producing one
approved answer formation report-run result artifact. This module does not
execute answer formation, compose answers, generate final-answer prose, execute
prompts, create live dialogue, call ChatResponder, respond_chat(),
generate_chat(), providers, search, advisors, wire runtime behavior, write
.weslr state, enable feature flags, create judges or scores, make official
claims, or grant answer, composition, or runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from weslr.answer_formation_report import (
    build_answer_formation_report_v1,
    derive_answer_formation_report_labels_v1,
    render_answer_formation_report_markdown_v1,
    summarize_answer_formation_report_v1,
    to_answer_formation_report_json_safe_v1,
    validate_answer_formation_report_v1,
)

ARTIFACT_TYPE_V1 = "answer_formation_report_run_v1"
SCHEMA_VERSION_V1 = "answer_formation_report_run_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_formation_report_run_v1_invalid"

REPORT_RUN_MODULE_PATH_V1 = "weslr/answer_formation_report_run.py"
REPORT_RUN_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_report_run_v1.py"
RESULT_ARTIFACT_PATH_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md"
SOURCE_REPORT_HELPER_MODULE_PATH_V1 = "weslr/answer_formation_report.py"
SOURCE_REPORT_HELPER_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_report_v1.py"
SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1 = "weslr/answer_formation.py"
SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_v1.py"
SOURCE_REPORT_RUN_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_V1.md"
SOURCE_REPORT_RUN_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_REVIEW_V1.md"
NEXT_LANE_V1 = "REVIEW_ANSWER_FORMATION_REPORT_RUN_RESULT_V1"

ALLOWED_INPUTS_V1 = (
    "explicit_safe_answer_formation_artifact_metadata",
    "safe_answer_formation_report_artifact_metadata",
    "safe_report_helper_validation_dictionary",
    "safe_report_helper_summary_dictionary",
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
    "official_turing_test_claim",
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
    "provider_model_search_advisor_call_handle",
    "prompt_execution_handle",
    "live_dialogue_handle",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "answer_formation_executed",
    "answer_formation_authorized",
    "answer_composition_attempted",
    "answer_composition_authorized",
    "final_answer_generated",
    "final_answer_selected",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "prompt_execution_performed",
    "live_dialogue_allowed",
    "live_dialogue_performed",
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
    "respond_chat_called",
    "generate_chat_called",
    "chat_responder_modified",
    "runtime_wired",
    "user_facing_output_created",
)

AGGREGATE_LABELS_V1 = (
    "metadata_only_report_run",
    "internal_only_report_run",
    "helper_based_report_run",
    "all_source_artifacts_metadata_only",
    "all_source_artifacts_internal_only",
    "all_authority_fields_false",
    "answer_formation_not_executed",
    "answer_composition_not_attempted",
    "final_answer_not_generated",
    "runtime_not_wired",
    "prompt_execution_not_allowed",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "feature_flags_not_enabled",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
    "chat_responder_not_called",
    "result_artifact_created_in_authorized_lane",
    "safe_markdown_eligible",
    "json_safe_eligible",
)

VISIBLE_RISKS_V1 = (
    "metadata-overread",
    "report-run-as-answer-formation",
    "report-run-as-authority",
    "result-artifact-as-final-answer",
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
    "review_answer_formation_report_run_result_v1",
    "keep_answer_formation_execution_separate",
    "keep_answer_composition_separate",
    "keep_final_answer_generation_separate",
    "keep_runtime_live_chat_integration_separate",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "report_run_only",
    "helper_based",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "import_safe",
    "side_effect_free_except_result_write",
    "qualitative_only",
    "validation_before_rendering",
    "safe_markdown_only",
    "json_safe_behavior_preserved",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    *_REQUIRED_TRUE_FIELDS,
    "report_run_module_path",
    "report_run_test_module_path",
    "result_artifact_path",
    "source_report_helper_module_path",
    "source_report_helper_test_module_path",
    "source_answer_formation_helper_module_path",
    "source_answer_formation_test_module_path",
    "source_report_run_design_doc",
    "source_report_run_review_doc",
    "allowed_inputs",
    "forbidden_inputs_checked",
    "report_run_flow_labels",
    "report_helper_validation",
    "report_helper_summary",
    "report_helper_aggregate_labels",
    "json_safe_metadata",
    "markdown_safe",
    "aggregate_labels",
    "denied_authority_fields",
    "visible_risks",
    "followups",
    "safety_confirmation",
    "validation_labels",
    "blocked",
    "blocked_reasons",
    "next_lane",
    *DENIED_AUTHORITY_FIELDS_V1,
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
    "answer_formation_executed",
    "answer_formation_authorized",
    "answer_formation_not_executed",
    "final_answer_generated",
    "final_answer_selected",
    "final_answer_not_generated",
    "runtime_authority_granted",
    "runtime_not_wired",
    "prompt_execution_allowed",
    "prompt_execution_performed",
    "prompt_execution_not_allowed",
    "live_dialogue_allowed",
    "live_dialogue_performed",
    "raw_content_allowed",
    "official_claim_allowed",
    "official_claims_not_allowed",
    "provider_calls_not_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "dot_weslr_not_written",
    "runtime_wired",
}

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "raw_prompt:", "raw_response:", "real user query:"),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "provider_output_detected": ("provider output:", "model output:", "search output:", "advisor output:", "llm output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output", "chat responder runtime output"),
    "final_answer_detected": ("final answer:", "final response text:", "final_answer_text"),
    "answer_draft_detected": ("answer draft:", "draft answer:", "answer draft text", "composed reply:"),
    "official_claim_detected": ("official turing pass", "passed the turing test", "official iq", "official benchmark"),
    "judge_or_score_detected": ("official score:", "score: 100", "judge decision:"),
}
_ALLOWED_KEYS_WITH_RISK_WORDS.update(_TEXT_MARKERS)
_ALLOWED_KEYS_WITH_RISK_WORDS.update({
    "hidden_prompt_detected",
    "answer_key_detected",
    "live_dialogue_detected",
    "prompt_execution_detected",
    "provider_call_detected",
    "dot_weslr_write_detected",
    "feature_flag_detected",
    "answer_authority_detected",
    "composition_authority_detected",
    "runtime_authority_detected",
    "consciousness_claim_detected",
    "identity_confusion_detected",
})


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


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{path}[{index}]"
            yield child, item
            yield from _walk(item, child)


def _detect_unsafe_content(value: Any) -> dict[str, bool]:
    found = {label: False for label in _TEXT_MARKERS}
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if any(fragment in key for fragment in _UNSAFE_KEY_FRAGMENTS) and key not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            if "final_answer" in key or "final_response" in key:
                found["final_answer_detected"] = True
            elif "answer_draft" in key or "composed_reply" in key:
                found["answer_draft_detected"] = True
            elif "provider" in key or "model" in key or "search" in key or "advisor" in key:
                found["provider_output_detected"] = True
            elif "runtime" in key:
                found["runtime_output_detected"] = True
            elif "private" in key:
                found["private_content_detected"] = True
            elif "judge" in key or "score" in key:
                found["judge_or_score_detected"] = True
            else:
                found["raw_content_detected"] = True
        if isinstance(item, str):
            text = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in text for marker in markers):
                    found[label] = True
    return found


def _unsafe_detection_labels(validation_or_detections: Mapping[str, Any]) -> list[str]:
    return [label for label in _TEXT_MARKERS if validation_or_detections.get(label) is True]


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        _append_unique(labels, str(error).split(":", 1)[0])
    return labels


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _invalid_json_safe_wrapper_v1(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    labels = _safe_error_labels(list(reason_labels)) or ["invalid_or_unsafe_report_run"]
    return {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "blocked": True,
        "valid": False,
        "errors": labels,
        "unsafe_content_not_copied": True,
        "metadata_only": True,
        "internal_only": True,
        "report_run_only": True,
        "validation_pass_metadata_quality_evidence_only": True,
        "answer_authority_granted": False,
        "composition_authority_granted": False,
        "runtime_authority_granted": False,
        "next_lane": NEXT_LANE_V1,
    }


def build_answer_formation_report_run_v1(
    source_artifacts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    *,
    result_artifact_path: str = RESULT_ARTIFACT_PATH_V1,
) -> dict[str, Any]:
    """Build one in-memory metadata-only answer formation report-run artifact."""

    report = build_answer_formation_report_v1(source_artifacts)
    report_validation = validate_answer_formation_report_v1(report)
    report_summary = summarize_answer_formation_report_v1(report)
    report_labels = derive_answer_formation_report_labels_v1(report)
    json_safe_report = to_answer_formation_report_json_safe_v1(report)
    markdown = render_answer_formation_report_markdown_v1(report) if report_validation.get("safe_to_render") is True else ""
    markdown_safe = bool(report_validation.get("valid") is True and report_validation.get("safe_to_render") is True and markdown)

    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "report_run_only": True,
        "helper_based": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free_except_result_write": True,
        "qualitative_only": True,
        "validation_before_rendering": True,
        "safe_markdown_only": True,
        "json_safe_behavior_preserved": True,
        "report_run_module_path": REPORT_RUN_MODULE_PATH_V1,
        "report_run_test_module_path": REPORT_RUN_TEST_MODULE_PATH_V1,
        "result_artifact_path": result_artifact_path,
        "source_report_helper_module_path": SOURCE_REPORT_HELPER_MODULE_PATH_V1,
        "source_report_helper_test_module_path": SOURCE_REPORT_HELPER_TEST_MODULE_PATH_V1,
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_answer_formation_test_module_path": SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1,
        "source_report_run_design_doc": SOURCE_REPORT_RUN_DESIGN_DOC_V1,
        "source_report_run_review_doc": SOURCE_REPORT_RUN_REVIEW_DOC_V1,
        "allowed_inputs": list(ALLOWED_INPUTS_V1),
        "forbidden_inputs_checked": list(FORBIDDEN_INPUTS_V1),
        "report_run_flow_labels": [
            "explicit_safe_metadata_received",
            "runtime_handles_absent",
            "source_metadata_validated",
            "report_helper_artifact_built_in_memory",
            "report_helper_artifact_validated",
            "safe_aggregate_labels_derived",
            "json_safe_metadata_created",
            "safe_markdown_rendered_after_validation",
            "approved_result_artifact_written",
        ],
        "report_helper_validation": _json_safe(report_validation),
        "report_helper_summary": _json_safe(report_summary),
        "report_helper_aggregate_labels": list(report_labels),
        "json_safe_metadata": _json_safe(json_safe_report),
        "markdown_safe": markdown_safe,
        "aggregate_labels": list(AGGREGATE_LABELS_V1),
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "visible_risks": list(VISIBLE_RISKS_V1),
        "followups": list(FOLLOWUPS_V1),
        "safety_confirmation": [
            "no_answer_formation_execution",
            "no_answer_composition",
            "no_final_answer_generation",
            "no_runtime_wiring",
            "no_prompt_execution_or_live_dialogue",
            "no_provider_search_advisor_calls",
            "no_dot_weslr_writes",
            "no_feature_flags",
            "no_judges_or_scoring",
            "no_official_claims",
            "no_answer_authority_granted",
            "no_composition_authority_granted",
            "no_runtime_authority_granted",
            "weslr_chat_responder_py_untouched",
            "occ_openclaw_not_deployed_weslr",
        ],
        "validation_labels": [
            "validation_pass_metadata_quality_evidence_only",
            "not_answer_correctness",
            "not_answer_authority",
            "not_composition_authority",
            "not_runtime_authority",
        ],
        "blocked": False,
        "blocked_reasons": [],
        "next_lane": NEXT_LANE_V1,
    }
    for field in DENIED_AUTHORITY_FIELDS_V1:
        artifact[field] = False
    for reason in _derive_blocked_reasons(artifact):
        _append_unique(artifact["blocked_reasons"], reason)
    artifact["blocked"] = bool(artifact["blocked_reasons"])
    return artifact


def _derive_blocked_reasons(artifact: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if artifact.get("result_artifact_path") != RESULT_ARTIFACT_PATH_V1:
        reasons.append("result_artifact_path_not_approved")
    if artifact.get("markdown_safe") is not True:
        reasons.append("markdown_not_safe")
    helper_validation = artifact.get("report_helper_validation")
    if not isinstance(helper_validation, Mapping) or helper_validation.get("valid") is not True:
        reasons.append("report_helper_validation_failed")
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            reasons.append(f"authority_field_not_false:{field}")
    detections = _detect_unsafe_content(artifact)
    reasons.extend(_unsafe_detection_labels(detections))
    return list(dict.fromkeys(reasons))


def validate_answer_formation_report_run_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one report-run artifact without side effects."""

    errors: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "report_helper_validation_valid": False,
        "json_safe": False,
        "safe_to_render": False,
        "result_artifact_path_valid": False,
    }
    for label in _TEXT_MARKERS:
        result[label] = False

    if not isinstance(artifact, Mapping):
        errors.append("artifact_not_mapping")
        return result

    result["artifact_type"] = artifact.get("artifact_type")
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_invalid")
    if artifact.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")
    for field in _REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"missing_required_field:{field}")
    for field in _REQUIRED_TRUE_FIELDS:
        if artifact.get(field) is not True:
            errors.append(f"required_true_field_invalid:{field}")

    path_valid = artifact.get("result_artifact_path") == RESULT_ARTIFACT_PATH_V1
    result["result_artifact_path_valid"] = path_valid
    if not path_valid:
        errors.append("result_artifact_path_invalid")

    expected_paths = {
        "report_run_module_path": REPORT_RUN_MODULE_PATH_V1,
        "report_run_test_module_path": REPORT_RUN_TEST_MODULE_PATH_V1,
        "source_report_helper_module_path": SOURCE_REPORT_HELPER_MODULE_PATH_V1,
        "source_report_helper_test_module_path": SOURCE_REPORT_HELPER_TEST_MODULE_PATH_V1,
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_answer_formation_test_module_path": SOURCE_ANSWER_FORMATION_TEST_MODULE_PATH_V1,
        "source_report_run_design_doc": SOURCE_REPORT_RUN_DESIGN_DOC_V1,
        "source_report_run_review_doc": SOURCE_REPORT_RUN_REVIEW_DOC_V1,
        "next_lane": NEXT_LANE_V1,
    }
    for key, expected in expected_paths.items():
        if artifact.get(key) != expected:
            errors.append(f"{key}_invalid")

    allowed = [str(item) for item in _as_list(artifact.get("allowed_inputs"))]
    if any(item not in ALLOWED_INPUTS_V1 for item in allowed):
        errors.append("unknown_allowed_inputs")
    forbidden_checked = [str(item) for item in _as_list(artifact.get("forbidden_inputs_checked"))]
    if any(item not in forbidden_checked for item in FORBIDDEN_INPUTS_V1):
        errors.append("missing_forbidden_input_checks")

    safety_ok = True
    denied = artifact.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        errors.append("denied_authority_fields_not_mapping")
        safety_ok = False
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            errors.append(f"authority_field_not_false:{field}")
            safety_ok = False
        if isinstance(denied, Mapping) and denied.get(field) is not False:
            errors.append(f"denied_authority_map_not_false:{field}")
            safety_ok = False
    result["safety_booleans_valid"] = safety_ok

    helper_validation = artifact.get("report_helper_validation")
    helper_valid = isinstance(helper_validation, Mapping) and helper_validation.get("valid") is True and helper_validation.get("safe_to_render") is True
    result["report_helper_validation_valid"] = helper_valid
    if not helper_valid:
        errors.append("report_helper_validation_invalid")

    if artifact.get("markdown_safe") is not True:
        errors.append("markdown_not_safe")
    if not isinstance(artifact.get("json_safe_metadata"), Mapping):
        errors.append("json_safe_metadata_not_mapping")

    for label, detected in _detect_unsafe_content(artifact).items():
        result[label] = detected
        if detected:
            errors.append(label)

    blocked_reasons = [str(item) for item in _as_list(artifact.get("blocked_reasons"))]
    if artifact.get("blocked") is True and not blocked_reasons:
        errors.append("blocked_without_reasons")
    if artifact.get("blocked") is False and blocked_reasons:
        errors.append("blocked_reasons_present_when_not_blocked")
    if artifact.get("blocked") not in (True, False):
        errors.append("blocked_not_boolean")

    try:
        json_safe = to_answer_formation_report_run_json_safe_v1(artifact)
        result["json_safe"] = isinstance(json_safe, Mapping)
    except Exception:  # pragma: no cover - defensive only; no unsafe message is exposed.
        result["json_safe"] = False
        errors.append("json_safe_conversion_failed")

    result["safe_to_render"] = not any(bool(result[label]) for label in _TEXT_MARKERS)
    result["valid"] = not errors and artifact.get("blocked") is False
    result["blocked"] = not result["valid"]
    return result


def summarize_answer_formation_report_run_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one report-run artifact using safe labels, counts, and booleans."""

    validation = validate_answer_formation_report_run_v1(artifact)
    return {
        "artifact_type": str(artifact.get("artifact_type", INVALID_ARTIFACT_TYPE_V1)) if validation["valid"] else INVALID_ARTIFACT_TYPE_V1,
        "schema_version": str(artifact.get("schema_version", "")) if validation["valid"] else "",
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "metadata_only": bool(isinstance(artifact, Mapping) and artifact.get("metadata_only") is True),
        "internal_only": bool(isinstance(artifact, Mapping) and artifact.get("internal_only") is True),
        "report_run_only": bool(isinstance(artifact, Mapping) and artifact.get("report_run_only") is True),
        "helper_based": bool(isinstance(artifact, Mapping) and artifact.get("helper_based") is True),
        "all_authority_fields_false": bool(validation["safety_booleans_valid"]),
        "result_artifact_path": RESULT_ARTIFACT_PATH_V1,
        "markdown_safe": bool(isinstance(artifact, Mapping) and artifact.get("markdown_safe") is True),
        "json_safe": bool(validation["json_safe"]),
        "visible_risk_count": len(_as_list(artifact.get("visible_risks"))) if isinstance(artifact, Mapping) else 0,
        "followup_count": len(_as_list(artifact.get("followups"))) if isinstance(artifact, Mapping) else 0,
        "validation_error_labels": _safe_error_labels(validation["errors"]),
        "next_lane": NEXT_LANE_V1,
    }


def _safe_blocked_markdown_v1(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reason_labels = _safe_error_labels(_as_list(validation.get("errors")))
    for label in _unsafe_detection_labels(validation):
        _append_unique(reason_labels, label)
    if not reason_labels:
        reason_labels = ["invalid_or_blocked_report_run"]
    lines = [
        "# WESLR Answer Formation Report Run Result V1 — Blocked",
        "",
        "## Result Status",
        f"- valid: `{bool(validation.get('valid'))}`",
        "- blocked: `True`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- report_run_only: `True`",
        "",
        "## Safe Reason Labels",
    ]
    for reason in reason_labels:
        lines.append(f"- `{reason}`")
    lines.extend([
        "",
        "## Safety Confirmation",
        "- `unsafe_content_not_rendered`",
        "- `no_answer_formation_execution`",
        "- `no_answer_composition`",
        "- `no_final_answer_generation`",
        "- `no_runtime_wiring`",
        "- `no_provider_search_advisor_calls`",
        "- `no_dot_weslr_writes`",
        "- `no_authority_granted`",
        f"- next_lane: `{summary.get('next_lane', NEXT_LANE_V1)}`",
    ])
    return "\n".join(lines) + "\n"


def render_answer_formation_report_run_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render validation-gated safe Markdown for one report-run artifact."""

    validation = validate_answer_formation_report_run_v1(artifact)
    summary = summarize_answer_formation_report_run_v1(artifact)
    if validation["valid"] is not True or validation["safe_to_render"] is not True:
        return _safe_blocked_markdown_v1(validation, summary)

    lines = [
        "# WESLR Answer Formation Report Run Result V1",
        "",
        "Layer: `WESLR_CANON_ALIGNMENT` result artifact only",
        "",
        "## Result Status",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- metadata_only: `{summary['metadata_only']}`",
        f"- internal_only: `{summary['internal_only']}`",
        f"- report_run_only: `{summary['report_run_only']}`",
        f"- helper_based: `{summary['helper_based']}`",
        f"- all_authority_fields_false: `{summary['all_authority_fields_false']}`",
        f"- result_artifact_path: `{summary['result_artifact_path']}`",
        f"- markdown_safe: `{summary['markdown_safe']}`",
        f"- json_safe: `{summary['json_safe']}`",
        "",
        "## Source Paths",
        f"- report_run_module_path: `{artifact.get('report_run_module_path')}`",
        f"- report_run_test_module_path: `{artifact.get('report_run_test_module_path')}`",
        f"- source_report_helper_module_path: `{artifact.get('source_report_helper_module_path')}`",
        f"- source_report_helper_test_module_path: `{artifact.get('source_report_helper_test_module_path')}`",
        f"- source_answer_formation_helper_module_path: `{artifact.get('source_answer_formation_helper_module_path')}`",
        f"- source_answer_formation_test_module_path: `{artifact.get('source_answer_formation_test_module_path')}`",
        "",
        "## Validation Labels",
    ]
    for label in _as_list(artifact.get("validation_labels")):
        lines.append(f"- `{label}`")

    lines.extend(["", "## Aggregate Labels"])
    for label in _as_list(artifact.get("aggregate_labels")):
        lines.append(f"- `{label}`")

    lines.extend(["", "## Denied Authority Fields"])
    for field in DENIED_AUTHORITY_FIELDS_V1:
        lines.append(f"- `{field}=false`")

    lines.extend(["", "## Visible Risks"])
    for risk in _as_list(artifact.get("visible_risks")):
        lines.append(f"- `{risk}`")

    lines.extend(["", "## Followups"])
    for followup in _as_list(artifact.get("followups")):
        lines.append(f"- `{followup}`")

    lines.extend(["", "## Safety Confirmation"])
    for label in _as_list(artifact.get("safety_confirmation")):
        lines.append(f"- `{label}`")
    lines.extend([
        "- validation pass is metadata quality evidence only",
        "- OCC/OpenClaw remains separate from deployed WESLR",
        "",
        "## Next Lane",
        f"- `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def to_answer_formation_report_run_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe deep copy or safe invalid wrapper for one report-run."""

    detections = _detect_unsafe_content(artifact)
    detection_labels = _unsafe_detection_labels(detections)
    if detection_labels:
        return _invalid_json_safe_wrapper_v1(detection_labels)
    safe = _json_safe(artifact)
    if not isinstance(safe, dict):
        return _invalid_json_safe_wrapper_v1(["artifact_not_mapping"])
    return safe


def write_answer_formation_report_run_result_v1(
    artifact: Mapping[str, Any] | None = None,
    *,
    result_artifact_path: str = RESULT_ARTIFACT_PATH_V1,
) -> dict[str, Any]:
    """Write exactly the approved report-run result artifact from safe Markdown."""

    report_run = dict(artifact) if isinstance(artifact, Mapping) else build_answer_formation_report_run_v1(result_artifact_path=result_artifact_path)
    if report_run.get("result_artifact_path") != result_artifact_path:
        report_run["result_artifact_path"] = result_artifact_path
    validation = validate_answer_formation_report_run_v1(report_run)
    if validation["valid"] is not True or validation["safe_to_render"] is not True:
        return {
            "written": False,
            "path": result_artifact_path,
            "validation": _json_safe(validation),
            "artifact": _invalid_json_safe_wrapper_v1(validation.get("errors", [])),
        }
    if result_artifact_path != RESULT_ARTIFACT_PATH_V1:
        return {
            "written": False,
            "path": result_artifact_path,
            "validation": _json_safe(validation),
            "artifact": _invalid_json_safe_wrapper_v1(["result_artifact_path_invalid"]),
        }
    markdown = render_answer_formation_report_run_markdown_v1(report_run)
    path = Path(result_artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown)
    return {
        "written": True,
        "path": result_artifact_path,
        "validation": _json_safe(validation),
        "artifact": to_answer_formation_report_run_json_safe_v1(report_run),
    }


def run_answer_formation_report_run_v1() -> dict[str, Any]:
    """Execute the approved metadata-only report-run and write the result artifact."""

    artifact = build_answer_formation_report_run_v1()
    return write_answer_formation_report_run_result_v1(artifact)


if __name__ == "__main__":
    result = run_answer_formation_report_run_v1()
    if result.get("written") is not True:
        raise SystemExit(1)
    print(result["path"])
