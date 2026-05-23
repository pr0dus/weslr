"""WESLR answer formation dry-run execution V1.

Deterministic, metadata-only execution helpers for one approved internal dry-run
result artifact. This module uses the existing answer formation dry-run helpers
with synthetic metadata only. It does not execute real answer formation, compose
answers, generate final-answer prose, answer user queries, execute prompts,
create live dialogue, call ChatResponder/respond_chat/generate_chat, call
providers/search/advisors, wire runtime behavior, write .weslr state, enable
feature flags, create judges or scores, make official claims, or grant answer,
composition, runtime, or official evaluation authority.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from weslr.answer_formation_dry_run import (
    DENIED_AUTHORITY_FIELDS_V1 as DRY_RUN_DENIED_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1 as DRY_RUN_FORBIDDEN_INPUTS_V1,
    HELPER_MODULE_PATH_V1 as DRY_RUN_HELPER_MODULE_PATH_V1,
    REQUIRED_NO_AUTHORITY_LABELS_V1 as DRY_RUN_REQUIRED_NO_AUTHORITY_LABELS_V1,
    TEST_MODULE_PATH_V1 as DRY_RUN_TEST_MODULE_PATH_V1,
    build_answer_formation_dry_run_artifact_v1,
    render_answer_formation_dry_run_artifact_markdown_v1,
    summarize_answer_formation_dry_run_artifact_v1,
    to_answer_formation_dry_run_artifact_json_safe_v1,
    validate_answer_formation_dry_run_artifact_v1,
)

ARTIFACT_TYPE_V1 = "answer_formation_dry_run_execution_result_v1"
SCHEMA_VERSION_V1 = "answer_formation_dry_run_execution_result_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_formation_dry_run_execution_result_v1_invalid"

EXECUTION_MODULE_PATH_V1 = "weslr/answer_formation_dry_run_execution.py"
EXECUTION_TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_dry_run_execution_v1.py"
RESULT_ARTIFACT_PATH_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_RESULT_V1.md"
SOURCE_EXECUTION_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1.md"
SOURCE_EXECUTION_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_REVIEW_V1.md"
SOURCE_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_REVIEW_V1.md"
SOURCE_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_V1.md"
SOURCE_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_REVIEW_V1.md"
SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_REVIEW_V1.md"
SOURCE_REPORT_RUN_RESULT_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md"
NEXT_LANE_V1 = "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_V1"

ALLOWED_SYNTHETIC_EXECUTION_INPUTS_V1 = (
    "execution_label",
    "synthetic_task_type_label",
    "synthetic_inferred_need_label",
    "synthetic_uncertainty_label",
    "synthetic_response_obligation_label",
    "synthetic_domain_context_label",
    "synthetic_memory_relevance_label",
    "synthetic_continuity_relevance_label",
    "synthetic_evidence_requirement_label",
    "synthetic_provenance_requirement_label",
    "synthetic_governance_gate_label",
    "synthetic_capability_boundary_label",
    "synthetic_safety_boundary_label",
    "synthetic_legal_moral_domain_boundary_label",
    "gate_status_label",
    "gate_count",
    "candidate_type_label",
    "candidate_count_metadata",
    "candidate_rejection_reason_label",
    "selected_candidate_metadata_presence_boolean",
)

AGGREGATE_LABELS_V1 = (
    "metadata_only_dry_run_execution_result",
    "internal_only_dry_run_execution_result",
    "helper_based_dry_run_execution_result",
    "synthetic_input_only",
    "dry_run_helper_used",
    "dry_run_status_recorded",
    "dry_run_artifact_validated_before_rendering",
    "approved_result_artifact_written",
    "real_answer_formation_not_executed",
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
    "safe_markdown_eligible",
    "json_safe_eligible",
)

SAFETY_FLAGS_V1 = (
    "synthetic_metadata_only",
    "internal_only",
    "safe_markdown",
    "validation_backed",
    "no_raw_prompt_text",
    "no_raw_response_text",
    "no_private_content",
    "no_provider_output",
    "no_runtime_output",
    "no_answer_draft",
    "no_composed_final_answer",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_prompt_or_live_dialogue",
    "no_chat_responder_calls",
    "no_provider_search_advisor_calls",
    "no_dot_weslr_writes",
    "no_feature_flags",
    "no_judges_or_scores",
    "no_official_claims",
    "no_authority_grant",
    "weslr_chat_responder_py_untouched",
)

VALIDATION_LABELS_V1 = (
    "validation_pass_metadata_quality_evidence_only",
    "validation_pass_not_answer_correctness",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "validation_pass_not_runtime_authority",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "dry_run_execution_only",
    "helper_based",
    "synthetic_input_only",
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
    "execution_label",
    "execution_module_path",
    "execution_test_module_path",
    "result_artifact_path",
    "source_execution_design_doc",
    "source_execution_review_doc",
    "source_helpers_implementation_review_doc",
    "source_helpers_design_doc",
    "source_boundary_review_doc",
    "source_report_run_result_review_doc",
    "source_report_run_result_doc",
    "dry_run_helper_module_path",
    "dry_run_helper_test_module_path",
    "allowed_synthetic_execution_inputs",
    "forbidden_inputs_checked",
    "dry_run_status",
    "validation_status",
    "metadata_only_posture",
    "dry_run_helper_validation",
    "dry_run_helper_summary",
    "dry_run_helper_json_safe_metadata",
    "dry_run_helper_markdown_safe",
    "blocked",
    "blocked_reasons",
    "blocked_invalid_artifact_behavior",
    "aggregate_labels",
    "validation_labels",
    "safety_flags",
    "denied_authority_fields",
    "required_no_authority_labels",
    "next_lane",
    *DRY_RUN_DENIED_AUTHORITY_FIELDS_V1,
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

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "real user query:"),
    "private_content_detected": ("private content:", "protected private material"),
    "provider_output_detected": ("provider output:", "model output:", "search output:", "advisor output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output"),
    "final_answer_detected": ("final answer:", "final response text:"),
    "answer_draft_detected": ("answer draft:", "draft answer:", "composed reply:"),
    "official_claim_detected": ("official turing pass", "official iq", "official benchmark", "certification claim"),
    "judge_or_score_detected": ("official score:", "judge decision:", "score: 100"),
}

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | set(_TEXT_MARKERS) | {
    "dry_run_helper_module_path",
    "dry_run_helper_test_module_path",
    "dry_run_helper_validation",
    "dry_run_helper_summary",
    "dry_run_helper_json_safe_metadata",
    "dry_run_helper_markdown_safe",
    "source_execution_design_doc",
    "source_execution_review_doc",
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
    "dry_run_result_artifact_created",
    "official_answer_claim_made",
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
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    found[label] = True
    return found


def _unsafe_detection_labels(validation_or_detections: Mapping[str, Any]) -> list[str]:
    return [label for label in _TEXT_MARKERS if validation_or_detections.get(label) is True]


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        label = str(error).replace("`", "").replace("\n", " ")[:160]
        _append_unique(labels, label)
    return labels


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return deepcopy(value)
    return repr(value)


def _invalid_json_safe_wrapper_v1(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    safe_reasons = _safe_error_labels(_as_list(reason_labels))
    return {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "blocked": True,
        "unsafe_content_not_copied": True,
        "blocked_reasons": safe_reasons,
        "denied_authority_fields": {field: False for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(DRY_RUN_REQUIRED_NO_AUTHORITY_LABELS_V1),
        "safety_flags": list(SAFETY_FLAGS_V1),
        "next_lane": NEXT_LANE_V1,
    }


def _default_synthetic_metadata() -> dict[str, Any]:
    return {
        "synthetic_task_type_label": "answer_formation_dry_run_boundary_exercise",
        "synthetic_inferred_need_label": "metadata_only_result_artifact",
        "synthetic_uncertainty_label": "synthetic_fixture_only",
        "synthetic_response_obligation_label": "no_user_facing_answer",
        "synthetic_domain_context_label": "internal_governance_boundary",
        "synthetic_memory_relevance_label": "metadata_only",
        "synthetic_continuity_relevance_label": "context_alignment_lane",
        "synthetic_evidence_requirement_label": "validation_backed_labels_only",
        "synthetic_provenance_requirement_label": "source_paths_recorded",
        "synthetic_governance_gate_label": "authority_denied",
        "synthetic_capability_boundary_label": "helper_only_non_runtime",
        "synthetic_safety_boundary_label": "no_raw_content",
        "synthetic_legal_moral_domain_boundary_label": "no_official_claims",
        "gate_status_label": "present",
        "gate_count": 1,
        "candidate_type_label": "metadata_candidate_only",
        "candidate_count_metadata": 1,
        "candidate_rejection_reason_label": "not_final_answer",
        "selected_candidate_metadata_presence_boolean": False,
    }


def _synthetic_metadata_for_helper(execution_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _default_synthetic_metadata()
    if isinstance(execution_metadata, Mapping):
        for key, value in execution_metadata.items():
            if key == "execution_label":
                continue
            data[str(key)] = deepcopy(value)
    return data


def build_answer_formation_dry_run_execution_result_v1(
    synthetic_execution_metadata: Mapping[str, Any] | None = None,
    *,
    result_artifact_path: str = RESULT_ARTIFACT_PATH_V1,
) -> dict[str, Any]:
    """Build one metadata-only dry-run execution result in memory."""

    execution_label = "answer_formation_dry_run_execution_v1"
    if isinstance(synthetic_execution_metadata, Mapping) and "execution_label" in synthetic_execution_metadata:
        execution_label = str(synthetic_execution_metadata.get("execution_label"))

    dry_run_artifact = build_answer_formation_dry_run_artifact_v1(
        _synthetic_metadata_for_helper(synthetic_execution_metadata)
    )
    dry_run_validation = validate_answer_formation_dry_run_artifact_v1(dry_run_artifact)
    dry_run_summary = summarize_answer_formation_dry_run_artifact_v1(dry_run_artifact)
    dry_run_json_safe = to_answer_formation_dry_run_artifact_json_safe_v1(dry_run_artifact)
    dry_run_markdown = (
        render_answer_formation_dry_run_artifact_markdown_v1(dry_run_artifact)
        if dry_run_validation.get("safe_to_render") is True
        else ""
    )
    markdown_safe = bool(dry_run_validation.get("valid") is True and dry_run_validation.get("safe_to_render") is True and dry_run_markdown)

    result: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "dry_run_execution_only": True,
        "helper_based": True,
        "synthetic_input_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free_except_result_write": True,
        "qualitative_only": True,
        "validation_before_rendering": True,
        "safe_markdown_only": True,
        "json_safe_behavior_preserved": True,
        "execution_label": execution_label,
        "execution_module_path": EXECUTION_MODULE_PATH_V1,
        "execution_test_module_path": EXECUTION_TEST_MODULE_PATH_V1,
        "result_artifact_path": result_artifact_path,
        "source_execution_design_doc": SOURCE_EXECUTION_DESIGN_DOC_V1,
        "source_execution_review_doc": SOURCE_EXECUTION_REVIEW_DOC_V1,
        "source_helpers_implementation_review_doc": SOURCE_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_report_run_result_review_doc": SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1,
        "source_report_run_result_doc": SOURCE_REPORT_RUN_RESULT_DOC_V1,
        "dry_run_helper_module_path": DRY_RUN_HELPER_MODULE_PATH_V1,
        "dry_run_helper_test_module_path": DRY_RUN_TEST_MODULE_PATH_V1,
        "allowed_synthetic_execution_inputs": list(ALLOWED_SYNTHETIC_EXECUTION_INPUTS_V1),
        "forbidden_inputs_checked": list(DRY_RUN_FORBIDDEN_INPUTS_V1),
        "dry_run_status": "dry_run_helper_artifact_built_and_validated",
        "validation_status": "validation_pass_metadata_quality_evidence_only" if dry_run_validation.get("valid") is True else "blocked_invalid_artifact",
        "metadata_only_posture": "synthetic_metadata_only_internal_safe_markdown_no_authority",
        "dry_run_helper_validation": _json_safe(dry_run_validation),
        "dry_run_helper_summary": _json_safe(dry_run_summary),
        "dry_run_helper_json_safe_metadata": _json_safe(dry_run_json_safe),
        "dry_run_helper_markdown_safe": markdown_safe,
        "blocked": False,
        "blocked_reasons": [],
        "blocked_invalid_artifact_behavior": [
            "blocked_result_uses_safe_labels_only",
            "unsafe_values_not_copied",
            "denied_authority_fields_remain_false",
            "result_artifact_not_written_when_validation_fails",
        ],
        "aggregate_labels": list(AGGREGATE_LABELS_V1),
        "validation_labels": list(VALIDATION_LABELS_V1),
        "safety_flags": list(SAFETY_FLAGS_V1),
        "denied_authority_fields": {field: False for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(DRY_RUN_REQUIRED_NO_AUTHORITY_LABELS_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1:
        result[field] = False
    for reason in _derive_blocked_reasons(result):
        _append_unique(result["blocked_reasons"], reason)
    result["blocked"] = bool(result["blocked_reasons"])
    return result


def _derive_blocked_reasons(result: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if result.get("result_artifact_path") != RESULT_ARTIFACT_PATH_V1:
        reasons.append("result_artifact_path_not_approved")
    if result.get("dry_run_helper_markdown_safe") is not True:
        reasons.append("dry_run_helper_markdown_not_safe")
    helper_validation = result.get("dry_run_helper_validation")
    if not isinstance(helper_validation, Mapping) or helper_validation.get("valid") is not True:
        reasons.append("dry_run_helper_validation_failed")
    allowed = [str(item) for item in _as_list(result.get("allowed_synthetic_execution_inputs"))]
    if any(item not in ALLOWED_SYNTHETIC_EXECUTION_INPUTS_V1 for item in allowed):
        reasons.append("unknown_allowed_synthetic_execution_inputs")
    for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1:
        if result.get(field) is not False:
            reasons.append(f"authority_field_not_false:{field}")
    reasons.extend(_unsafe_detection_labels(_detect_unsafe_content(result)))
    return list(dict.fromkeys(reasons))


def validate_answer_formation_dry_run_execution_result_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one dry-run execution result without side effects."""

    errors: list[str] = []
    validation: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "dry_run_helper_validation_valid": False,
        "json_safe": False,
        "safe_to_render": False,
        "result_artifact_path_valid": False,
    }
    for label in _TEXT_MARKERS:
        validation[label] = False

    if not isinstance(result, Mapping):
        errors.append("artifact_not_mapping")
        return validation

    validation["artifact_type"] = result.get("artifact_type")
    if result.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_invalid")
    if result.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")
    for field in _REQUIRED_FIELDS:
        if field not in result:
            errors.append(f"missing_required_field:{field}")
    for field in _REQUIRED_TRUE_FIELDS:
        if result.get(field) is not True:
            errors.append(f"required_true_field_invalid:{field}")

    expected_paths = {
        "execution_module_path": EXECUTION_MODULE_PATH_V1,
        "execution_test_module_path": EXECUTION_TEST_MODULE_PATH_V1,
        "result_artifact_path": RESULT_ARTIFACT_PATH_V1,
        "source_execution_design_doc": SOURCE_EXECUTION_DESIGN_DOC_V1,
        "source_execution_review_doc": SOURCE_EXECUTION_REVIEW_DOC_V1,
        "source_helpers_implementation_review_doc": SOURCE_HELPERS_IMPLEMENTATION_REVIEW_DOC_V1,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_report_run_result_review_doc": SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1,
        "source_report_run_result_doc": SOURCE_REPORT_RUN_RESULT_DOC_V1,
        "dry_run_helper_module_path": DRY_RUN_HELPER_MODULE_PATH_V1,
        "dry_run_helper_test_module_path": DRY_RUN_TEST_MODULE_PATH_V1,
        "next_lane": NEXT_LANE_V1,
    }
    for key, expected in expected_paths.items():
        if result.get(key) != expected:
            errors.append(f"{key}_invalid")
    validation["result_artifact_path_valid"] = result.get("result_artifact_path") == RESULT_ARTIFACT_PATH_V1

    allowed = [str(item) for item in _as_list(result.get("allowed_synthetic_execution_inputs"))]
    if any(item not in ALLOWED_SYNTHETIC_EXECUTION_INPUTS_V1 for item in allowed):
        errors.append("unknown_allowed_synthetic_execution_inputs")
    if any(item not in allowed for item in ALLOWED_SYNTHETIC_EXECUTION_INPUTS_V1):
        errors.append("missing_allowed_synthetic_execution_inputs")
    forbidden_checked = [str(item) for item in _as_list(result.get("forbidden_inputs_checked"))]
    if any(item not in forbidden_checked for item in DRY_RUN_FORBIDDEN_INPUTS_V1):
        errors.append("missing_forbidden_input_checks")

    safety_ok = True
    denied = result.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        errors.append("denied_authority_fields_not_mapping")
        safety_ok = False
    for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1:
        if result.get(field) is not False:
            errors.append(f"authority_field_not_false:{field}")
            safety_ok = False
        if isinstance(denied, Mapping) and denied.get(field) is not False:
            errors.append(f"denied_authority_map_not_false:{field}")
            safety_ok = False
    validation["safety_booleans_valid"] = safety_ok

    helper_validation = result.get("dry_run_helper_validation")
    helper_valid = isinstance(helper_validation, Mapping) and helper_validation.get("valid") is True and helper_validation.get("safe_to_render") is True
    validation["dry_run_helper_validation_valid"] = helper_valid
    if not helper_valid:
        errors.append("dry_run_helper_validation_invalid")

    if result.get("dry_run_helper_markdown_safe") is not True:
        errors.append("dry_run_helper_markdown_not_safe")
    if not isinstance(result.get("dry_run_helper_json_safe_metadata"), Mapping):
        errors.append("dry_run_helper_json_safe_metadata_not_mapping")

    for label, detected in _detect_unsafe_content(result).items():
        validation[label] = detected
        if detected:
            errors.append(label)

    blocked_reasons = [str(item) for item in _as_list(result.get("blocked_reasons"))]
    if result.get("blocked") is True and not blocked_reasons:
        errors.append("blocked_without_reasons")
    if result.get("blocked") is False and blocked_reasons:
        errors.append("blocked_reasons_present_when_not_blocked")
    if result.get("blocked") not in (True, False):
        errors.append("blocked_not_boolean")

    try:
        json_safe = to_answer_formation_dry_run_execution_result_json_safe_v1(result)
        validation["json_safe"] = isinstance(json_safe, Mapping)
    except Exception:  # pragma: no cover - defensive only; message is not exposed.
        validation["json_safe"] = False
        errors.append("json_safe_conversion_failed")

    validation["safe_to_render"] = not any(bool(validation[label]) for label in _TEXT_MARKERS)
    validation["valid"] = not errors and result.get("blocked") is False
    validation["blocked"] = not validation["valid"]
    return validation


def summarize_answer_formation_dry_run_execution_result_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one execution result using safe labels, counts, and booleans."""

    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    helper_summary = result.get("dry_run_helper_summary") if isinstance(result, Mapping) else {}
    if not isinstance(helper_summary, Mapping):
        helper_summary = {}
    return {
        "artifact_type": str(result.get("artifact_type", INVALID_ARTIFACT_TYPE_V1)) if validation["valid"] else INVALID_ARTIFACT_TYPE_V1,
        "schema_version": str(result.get("schema_version", "")) if validation["valid"] else "",
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "metadata_only": bool(isinstance(result, Mapping) and result.get("metadata_only") is True),
        "internal_only": bool(isinstance(result, Mapping) and result.get("internal_only") is True),
        "dry_run_execution_only": bool(isinstance(result, Mapping) and result.get("dry_run_execution_only") is True),
        "helper_based": bool(isinstance(result, Mapping) and result.get("helper_based") is True),
        "synthetic_input_only": bool(isinstance(result, Mapping) and result.get("synthetic_input_only") is True),
        "all_authority_fields_false": bool(validation["safety_booleans_valid"]),
        "result_artifact_path": RESULT_ARTIFACT_PATH_V1,
        "dry_run_status": str(result.get("dry_run_status", "unknown_dry_run_status")) if isinstance(result, Mapping) else "unknown_dry_run_status",
        "validation_status": str(result.get("validation_status", "unknown_validation_status")) if isinstance(result, Mapping) else "unknown_validation_status",
        "candidate_count_total": int(helper_summary.get("candidate_count_total", 0)),
        "dry_run_helper_valid": bool(validation["dry_run_helper_validation_valid"]),
        "json_safe": bool(validation["json_safe"]),
        "visible_risk_count": len(_as_list(result.get("aggregate_labels"))) if isinstance(result, Mapping) else 0,
        "validation_error_labels": _safe_error_labels(validation["errors"]),
        "next_lane": NEXT_LANE_V1,
    }


def _safe_blocked_markdown_v1(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reason_labels = _safe_error_labels(_as_list(validation.get("errors")))
    for label in _unsafe_detection_labels(validation):
        _append_unique(reason_labels, label)
    if not reason_labels:
        reason_labels = ["invalid_or_blocked_dry_run_execution_result"]
    lines = [
        "# WESLR Answer Formation Dry-Run Result V1 — Blocked",
        "",
        "## Result Status",
        f"- valid: `{bool(validation.get('valid'))}`",
        "- blocked: `True`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- synthetic_metadata_only: `True`",
        "",
        "## Safe Blocked Reason Labels",
    ]
    lines.extend(f"- `{reason}`" for reason in reason_labels)
    lines.extend([
        "",
        "## Blocked / Invalid Artifact Behavior",
        "- `blocked_result_uses_safe_labels_only`",
        "- `unsafe_values_not_copied`",
        "- `denied_authority_fields_remain_false`",
        "- `result_artifact_not_written_when_validation_fails`",
        "",
        "## Safety Confirmation",
        "- `no_raw_prompt_text`",
        "- `no_raw_response_text`",
        "- `no_private_content`",
        "- `no_provider_output`",
        "- `no_runtime_output`",
        "- `no_answer_draft`",
        "- `no_composed_final_answer`",
        "- `no_final_answer_generation`",
        "- `no_runtime_wiring`",
        "- `no_authority_grant`",
        f"- next_lane: `{summary.get('next_lane', NEXT_LANE_V1)}`",
    ])
    return "\n".join(lines) + "\n"


def render_answer_formation_dry_run_execution_result_markdown_v1(result: Mapping[str, Any]) -> str:
    """Render validation-gated safe Markdown for one dry-run execution result."""

    validation = validate_answer_formation_dry_run_execution_result_v1(result)
    summary = summarize_answer_formation_dry_run_execution_result_v1(result)
    if validation["valid"] is not True or validation["safe_to_render"] is not True:
        return _safe_blocked_markdown_v1(validation, summary)

    lines = [
        "# WESLR Answer Formation Dry-Run Result V1",
        "",
        "Layer: `WESLR_CANON_ALIGNMENT` internal result artifact only",
        "",
        "## Execution Label",
        f"- execution_label: `{result.get('execution_label')}`",
        "",
        "## Result Status",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- dry_run_status: `{summary['dry_run_status']}`",
        f"- validation_status: `{summary['validation_status']}`",
        f"- metadata_only: `{summary['metadata_only']}`",
        f"- internal_only: `{summary['internal_only']}`",
        f"- dry_run_execution_only: `{summary['dry_run_execution_only']}`",
        f"- helper_based: `{summary['helper_based']}`",
        f"- synthetic_input_only: `{summary['synthetic_input_only']}`",
        f"- all_authority_fields_false: `{summary['all_authority_fields_false']}`",
        f"- result_artifact_path: `{summary['result_artifact_path']}`",
        f"- json_safe: `{summary['json_safe']}`",
        "",
        "## Source Paths",
        f"- source_execution_design_doc: `{result.get('source_execution_design_doc')}`",
        f"- source_execution_review_doc: `{result.get('source_execution_review_doc')}`",
        f"- source_helpers_implementation_review_doc: `{result.get('source_helpers_implementation_review_doc')}`",
        f"- source_helpers_design_doc: `{result.get('source_helpers_design_doc')}`",
        f"- source_boundary_review_doc: `{result.get('source_boundary_review_doc')}`",
        f"- source_report_run_result_review_doc: `{result.get('source_report_run_result_review_doc')}`",
        f"- source_report_run_result_doc: `{result.get('source_report_run_result_doc')}`",
        "",
        "## Helper Module Used",
        f"- dry_run_helper_module_path: `{result.get('dry_run_helper_module_path')}`",
        f"- dry_run_helper_test_module_path: `{result.get('dry_run_helper_test_module_path')}`",
        f"- execution_module_path: `{result.get('execution_module_path')}`",
        f"- execution_test_module_path: `{result.get('execution_test_module_path')}`",
        "",
        "## Metadata-Only Posture",
        f"- `{result.get('metadata_only_posture')}`",
        "",
        "## Blocked / Invalid Artifact Behavior",
    ]
    lines.extend(f"- `{label}`" for label in _as_list(result.get("blocked_invalid_artifact_behavior")))
    lines.extend(["", "## Safety Flags"])
    lines.extend(f"- `{label}`" for label in _as_list(result.get("safety_flags")))
    lines.extend(["", "## Validation Labels"])
    lines.extend(f"- `{label}`" for label in _as_list(result.get("validation_labels")))
    lines.extend(["", "## Aggregate Labels"])
    lines.extend(f"- `{label}`" for label in _as_list(result.get("aggregate_labels")))
    lines.extend(["", "## Denied Authority Fields"])
    lines.extend(f"- `{field}=false`" for field in DRY_RUN_DENIED_AUTHORITY_FIELDS_V1)
    lines.extend(["", "## Required No-Authority Labels"])
    lines.extend(f"- `{label}`" for label in _as_list(result.get("required_no_authority_labels")))
    lines.extend([
        "",
        "## No-Runtime / No-Provider / No-Final-Answer Boundary",
        "- `no_runtime_wiring`",
        "- `no_provider_search_advisor_calls`",
        "- `no_final_answer_generation`",
        "- `no_answer_draft`",
        "- `no_composed_final_answer`",
        "- `no_authority_grant`",
        "",
        "## Next Recommended Lane",
        f"- `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def to_answer_formation_dry_run_execution_result_json_safe_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe deep copy or safe invalid wrapper for one execution result."""

    detections = _detect_unsafe_content(result)
    detection_labels = _unsafe_detection_labels(detections)
    if detection_labels:
        return _invalid_json_safe_wrapper_v1(detection_labels)
    safe = _json_safe(result)
    if not isinstance(safe, dict):
        return _invalid_json_safe_wrapper_v1(["artifact_not_mapping"])
    return safe


def write_answer_formation_dry_run_result_artifact_v1(
    result: Mapping[str, Any] | None = None,
    *,
    result_artifact_path: str = RESULT_ARTIFACT_PATH_V1,
) -> dict[str, Any]:
    """Write exactly the approved dry-run result artifact from safe Markdown."""

    execution_result = dict(result) if isinstance(result, Mapping) else build_answer_formation_dry_run_execution_result_v1(result_artifact_path=result_artifact_path)
    if execution_result.get("result_artifact_path") != result_artifact_path:
        execution_result["result_artifact_path"] = result_artifact_path
    validation = validate_answer_formation_dry_run_execution_result_v1(execution_result)
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
    markdown = render_answer_formation_dry_run_execution_result_markdown_v1(execution_result)
    path = Path(result_artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown)
    return {
        "written": True,
        "path": result_artifact_path,
        "validation": _json_safe(validation),
        "artifact": to_answer_formation_dry_run_execution_result_json_safe_v1(execution_result),
    }


def run_answer_formation_dry_run_execution_v1() -> dict[str, Any]:
    """Run the approved metadata-only dry-run execution and write the result artifact."""

    result = build_answer_formation_dry_run_execution_result_v1()
    return write_answer_formation_dry_run_result_artifact_v1(result)


if __name__ == "__main__":
    output = run_answer_formation_dry_run_execution_v1()
    if output.get("written") is not True:
        raise SystemExit(1)
    print(output["path"])
