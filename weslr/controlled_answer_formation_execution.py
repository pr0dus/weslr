"""WESLR controlled answer formation execution helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
controlled answer formation execution artifacts. These helpers arrange explicitly
supplied controlled/synthetic metadata only. They do not execute controlled
answer formation, execute real answer formation, compose answers, generate
final-answer prose, answer user queries, execute prompts, create live dialogue,
call ChatResponder/respond_chat/generate_chat, call providers/models/search/
advisors, wire runtime behavior, write .weslr state, enable feature flags,
create judges or scores, make official claims, create an execution result
artifact, or grant answer, composition, runtime, or official evaluation
authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARTIFACT_TYPE_V1 = "controlled_answer_formation_execution_artifact_v1"
SCHEMA_VERSION_V1 = "controlled_answer_formation_execution_artifact_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "controlled_answer_formation_execution_artifact_v1_invalid"

HELPER_MODULE_PATH_V1 = "weslr/controlled_answer_formation_execution.py"
TEST_MODULE_PATH_V1 = "weslr/tests/test_controlled_answer_formation_execution_v1.py"
SOURCE_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_REVIEW_V1.md"
SOURCE_BOUNDARY_DESIGN_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_V1.md"
SOURCE_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_BOUNDARY_REVIEW_V1.md"
SOURCE_DRY_RUN_RESULT_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_RESULT_V1.md"
SOURCE_DRY_RUN_RESULT_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_EXECUTION_RESULT_REVIEW_V1.md"
SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1 = "weslr/answer_formation.py"
SOURCE_DRY_RUN_HELPER_MODULE_PATH_V1 = "weslr/answer_formation_dry_run.py"
SOURCE_DRY_RUN_EXECUTION_MODULE_PATH_V1 = "weslr/answer_formation_dry_run_execution.py"
SOURCE_REPORT_HELPER_MODULE_PATH_V1 = "weslr/answer_formation_report.py"
SOURCE_REPORT_RUN_MODULE_PATH_V1 = "weslr/answer_formation_report_run.py"
NEXT_LANE_V1 = "REVIEW_CONTROLLED_ANSWER_FORMATION_EXECUTION_HELPERS_IMPLEMENTATION_V1"

ALLOWED_CONTROLLED_INPUTS_V1 = (
    "controlled_execution_label",
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
    "controlled_gate_status_label",
    "controlled_gate_count",
    "controlled_candidate_type_label",
    "controlled_candidate_count_metadata",
    "controlled_candidate_rejection_reason_label",
    "controlled_selected_candidate_metadata_presence_boolean",
    "safe_answer_formation_artifact_metadata",
    "safe_answer_formation_dry_run_artifact_metadata",
    "safe_answer_formation_report_artifact_metadata",
    "safe_answer_formation_report_run_result_metadata",
    "safe_dry_run_execution_result_metadata",
    "source_helper_path_label",
    "source_review_path_label",
    "source_result_path_label",
    "validation_status_label",
    "blocked_status_boolean",
    "blocked_reason_label",
    "denied_authority_field_label",
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
    "answer_authority_grant",
    "composition_authority_grant",
    "runtime_authority_grant",
    "official_evaluation_authority_grant",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "answer_formation_authorized",
    "answer_formation_executed",
    "answer_composition_attempted",
    "answer_composition_authorized",
    "final_answer_generated",
    "final_answer_selected",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "prompt_execution_allowed",
    "prompt_execution_performed",
    "live_dialogue_allowed",
    "live_dialogue_performed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "provider_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
    "official_score_claimed",
    "chat_responder_called",
    "respond_chat_called",
    "generate_chat_called",
    "chat_responder_modified",
    "runtime_wired",
    "user_facing_output_created",
    "official_answer_claim_made",
    "controlled_execution_result_artifact_created",
)

AGGREGATE_LABELS_V1 = (
    "metadata_only_controlled_execution_helper_artifact",
    "internal_only_controlled_execution_helper_artifact",
    "helper_only_controlled_execution_metadata",
    "synthetic_or_controlled_input_only",
    "controlled_execution_not_performed",
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
    "execution_result_artifact_not_created",
    "safe_markdown_eligible_after_validation",
    "json_safe_eligible_after_validation",
)

VISIBLE_RISKS_V1 = (
    "dry-run-result-as-controlled-execution-authority",
    "controlled-execution-helper-as-answer-formation-execution",
    "controlled-execution-as-answer-composition",
    "controlled-execution-as-final-answer-generation",
    "controlled-execution-as-runtime-wiring",
    "validation-pass-as-answer-authority",
    "metadata-as-authority",
    "helper-existence-as-authority",
    "result-artifact-as-runtime-readiness",
    "candidate-metadata-as-answer-draft",
    "selected-candidate-metadata-as-final-answer",
    "aggregate-label-as-readiness",
    "state-frame-as-runtime-authority",
    "final-answer-prose leak",
    "OCC/WESLR identity confusion",
    "implementation-as-runtime-authority",
    "future-lane-compression-risk",
)

FOLLOWUPS_V1 = (
    "review_controlled_answer_formation_execution_helpers_implementation_v1",
    "keep_controlled_execution_result_artifact_separate",
    "keep_answer_formation_execution_separate",
    "keep_answer_composition_separate",
    "keep_final_answer_generation_separate",
    "keep_runtime_live_chat_integration_separate",
    "keep_official_evaluation_claims_separate",
)

REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "controlled_helper_metadata_not_answer_text",
    "controlled_execution_helper_artifact_not_final_answer",
    "candidate_metadata_not_answer_draft",
    "selected_candidate_metadata_not_final_answer",
    "validation_pass_not_answer_correctness",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "validation_pass_not_runtime_authority",
    "dry_run_result_not_controlled_execution_authority",
    "controlled_execution_result_artifact_requires_separate_approval",
    "answer_formation_execution_requires_separate_approval",
    "answer_composition_requires_separate_approval",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "official_evaluation_requires_separate_approval",
    "occ_openclaw_not_deployed_weslr",
)

SAFETY_CONFIRMATION_V1 = (
    "helper_only",
    "metadata_controlled",
    "synthetic_control_input_only",
    "deterministic",
    "import_safe",
    "side_effect_free",
    "in_memory_only",
    "internal_only",
    "qualitative_only",
    "validation_before_rendering_required",
    "safe_markdown_only",
    "json_safe",
    "blocked_artifact_aware",
    "no_authority_preserving",
    "no_controlled_execution_performed",
    "no_answer_formation_execution",
    "no_answer_composition",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_prompt_or_live_dialogue",
    "no_chat_responder_calls",
    "no_provider_search_advisor_calls",
    "no_dot_weslr_writes",
    "no_feature_flags",
    "no_judges_or_scores",
    "no_official_claims",
    "no_execution_result_artifact_created",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "helper_only",
    "controlled_execution_helper_only",
    "synthetic_or_controlled_input_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "import_safe",
    "side_effect_free",
    "in_memory_only",
    "qualitative_only",
    "validation_before_controlled_execution",
    "validation_before_rendering",
    "safe_markdown_only",
    "json_safe_behavior_preserved",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    *_REQUIRED_TRUE_FIELDS,
    "source_helpers_design_doc",
    "source_helpers_review_doc",
    "source_boundary_design_doc",
    "source_boundary_review_doc",
    "source_dry_run_result_doc",
    "source_dry_run_result_review_doc",
    "source_helper_module_paths",
    "proposed_helper_module_path",
    "proposed_test_module_path",
    "allowed_controlled_inputs",
    "forbidden_inputs_checked",
    "controlled_execution_label",
    "metadata_only_posture",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "gate_metadata_summary",
    "candidate_metadata_summary",
    "source_metadata_summary",
    "denied_authority_fields",
    "aggregate_labels",
    "required_no_authority_labels",
    "visible_risks",
    "followups",
    "safety_confirmation",
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
    "final_answer",
    "final_response",
    "answer_draft",
    "composed_reply",
    "official_benchmark",
    "official_turing",
    "official_iq",
    "certification",
    "product_readiness",
    "consciousness_sentience",
    "official_score",
    "judge_decision",
    "scoring_result",
    "dot_weslr_state",
    "feature_flag_activation",
    "runtime_wiring",
    "chat_responder_call",
    "respond_chat_call",
    "generate_chat_call",
    "provider_model_search_advisor_call",
    "prompt_execution",
    "authority_grant",
)

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "real user query:", "raw_prompt:", "raw_response:"),
    "private_content_detected": ("private content:", "protected private material"),
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
        "certification claim",
    ),
    "judge_or_score_detected": ("official score:", "score: 100", "judge decision:", "judge_authority_granted=true"),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
    "provider_call_detected": ("model_call_made=true", "search_call_made=true", "advisor_call_made=true", "provider_call_made=true"),
    "dot_weslr_write_detected": ("write .weslr", ".weslr write", "dot_weslr_write_performed=true"),
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag"),
    "answer_authority_detected": ("answer authority granted", "answer_authority_granted=true", "approved for live answers"),
    "composition_authority_detected": ("composition authority granted", "answer_composition_authorized=true"),
    "runtime_authority_detected": ("runtime authority granted", "runtime_authority_granted=true"),
    "official_evaluation_authority_detected": ("official evaluation authority granted", "official_evaluation_authority_granted=true"),
    "consciousness_claim_detected": ("weslr is conscious", "weslr is sentient", "consciousness proven", "sentience proven"),
    "identity_confusion_detected": ("occ is weslr", "openclaw is weslr", "occ/openclaw is weslr"),
}

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | set(DENIED_AUTHORITY_FIELDS_V1) | set(ALLOWED_CONTROLLED_INPUTS_V1) | {
    "source_answer_formation_helper_module_path",
    "source_dry_run_helper_module_path",
    "source_dry_run_execution_module_path",
    "source_report_helper_module_path",
    "source_report_run_module_path",
    "source_dry_run_result_doc",
    "source_dry_run_result_review_doc",
    "dry_run_result_not_controlled_execution_authority",
    "controlled_execution_result_artifact_requires_separate_approval",
    "controlled_execution_not_performed",
    "execution_result_artifact_not_created",
    "controlled_execution_helper_artifact_not_final_answer",
    "candidate_metadata_not_answer_draft",
    "selected_candidate_metadata_not_final_answer",
    "validation_pass_not_answer_authority",
    "metadata-as-authority",
    "helper-existence-as-authority",
    "result-artifact-as-runtime-readiness",
    "final-answer-prose leak",
    "candidate_metadata_is_answer_draft",
    "selected_candidate_metadata_is_final_answer",
}
_ALLOWED_KEYS_WITH_RISK_WORDS.update(_TEXT_MARKERS)
_ALLOWED_KEYS_WITH_RISK_WORDS.update({marker for markers in _TEXT_MARKERS.values() for marker in markers})

_SAFE_STRING_LABELS = (
    set(ALLOWED_CONTROLLED_INPUTS_V1)
    | set(FORBIDDEN_INPUTS_V1)
    | set(DENIED_AUTHORITY_FIELDS_V1)
    | set(AGGREGATE_LABELS_V1)
    | set(VISIBLE_RISKS_V1)
    | set(FOLLOWUPS_V1)
    | set(REQUIRED_NO_AUTHORITY_LABELS_V1)
    | set(SAFETY_CONFIRMATION_V1)
    | {
        ARTIFACT_TYPE_V1,
        SCHEMA_VERSION_V1,
        INVALID_ARTIFACT_TYPE_V1,
        HELPER_MODULE_PATH_V1,
        TEST_MODULE_PATH_V1,
        SOURCE_HELPERS_DESIGN_DOC_V1,
        SOURCE_HELPERS_REVIEW_DOC_V1,
        SOURCE_BOUNDARY_DESIGN_DOC_V1,
        SOURCE_BOUNDARY_REVIEW_DOC_V1,
        SOURCE_DRY_RUN_RESULT_DOC_V1,
        SOURCE_DRY_RUN_RESULT_REVIEW_DOC_V1,
        SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        SOURCE_DRY_RUN_HELPER_MODULE_PATH_V1,
        SOURCE_DRY_RUN_EXECUTION_MODULE_PATH_V1,
        SOURCE_REPORT_HELPER_MODULE_PATH_V1,
        SOURCE_REPORT_RUN_MODULE_PATH_V1,
        NEXT_LANE_V1,
        "controlled_synthetic_metadata_only_internal_safe_markdown_no_authority",
        "controlled_answer_formation_execution_helper_metadata_v1",
        "controlled_answer_formation_execution_boundary_exercise",
        "metadata_only_controlled_execution_artifact",
        "validation_pending_metadata_quality_evidence_only",
        "validation_pass_metadata_quality_evidence_only",
        "blocked_invalid_or_unsafe_metadata_labels_only",
        "metadata_candidate_only",
        "not_final_answer",
        "no_user_facing_answer",
        "authority_denied",
        "helper_only_non_runtime",
        "no_raw_content",
        "no_official_claims",
        "present",
        "internal_governance_boundary",
        "metadata_only",
        "context_alignment_lane",
        "validation_backed_labels_only",
        "source_paths_recorded",
        "synthetic_fixture_only",
        "json_safe_eligible_after_validation",
        "safe_markdown_eligible_after_validation",
    }
)


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


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        label = str(error).replace("`", "").replace("\n", " ")[:160]
        _append_unique(labels, label)
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
            elif "hidden" in key:
                found["hidden_prompt_detected"] = True
            elif "answer_key" in key:
                found["answer_key_detected"] = True
            elif "judge" in key or "score" in key:
                found["judge_or_score_detected"] = True
            elif "prompt" in key:
                found["prompt_execution_detected"] = True
            elif "feature_flag" in key:
                found["feature_flag_detected"] = True
            elif "authority" in key:
                found["answer_authority_detected"] = True
            else:
                found["raw_content_detected"] = True
        if isinstance(item, str):
            if item in _SAFE_STRING_LABELS:
                continue
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    found[label] = True
    return found


def _unsafe_detection_labels(validation_or_detections: Mapping[str, Any]) -> list[str]:
    return [label for label in _TEXT_MARKERS if validation_or_detections.get(label) is True]


def _default_controlled_metadata() -> dict[str, Any]:
    return {
        "controlled_execution_label": "controlled_answer_formation_execution_helper_metadata_v1",
        "synthetic_task_type_label": "controlled_answer_formation_execution_boundary_exercise",
        "synthetic_inferred_need_label": "metadata_only_controlled_execution_artifact",
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
        "controlled_gate_status_label": "present",
        "controlled_gate_count": 1,
        "controlled_candidate_type_label": "metadata_candidate_only",
        "controlled_candidate_count_metadata": 1,
        "controlled_candidate_rejection_reason_label": "not_final_answer",
        "controlled_selected_candidate_metadata_presence_boolean": False,
        "validation_status_label": "validation_pass_metadata_quality_evidence_only",
        "blocked_status_boolean": False,
        "no_authority_boolean": True,
        "json_safe_eligibility_label": "json_safe_eligible_after_validation",
        "markdown_safe_eligibility_label": "safe_markdown_eligible_after_validation",
        "next_lane_label": NEXT_LANE_V1,
    }


def _source_metadata_summary() -> dict[str, Any]:
    return {
        "source_boundary_design_doc": SOURCE_BOUNDARY_DESIGN_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_dry_run_result_doc": SOURCE_DRY_RUN_RESULT_DOC_V1,
        "source_dry_run_result_review_doc": SOURCE_DRY_RUN_RESULT_REVIEW_DOC_V1,
        "source_helper_module_paths": [
            SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
            SOURCE_DRY_RUN_HELPER_MODULE_PATH_V1,
            SOURCE_DRY_RUN_EXECUTION_MODULE_PATH_V1,
            SOURCE_REPORT_HELPER_MODULE_PATH_V1,
            SOURCE_REPORT_RUN_MODULE_PATH_V1,
        ],
        "proposed_helper_module_path": HELPER_MODULE_PATH_V1,
        "proposed_test_module_path": TEST_MODULE_PATH_V1,
    }


def _summarize_safe_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"present": False, "mapping": False, "key_count": 0, "safe_label_keys": []}
    safe_keys = [str(key) for key in sorted(value.keys(), key=str) if str(key) in ALLOWED_CONTROLLED_INPUTS_V1 or str(key) in DENIED_AUTHORITY_FIELDS_V1]
    return {
        "present": True,
        "mapping": True,
        "key_count": len(value),
        "safe_label_keys": safe_keys,
        "contains_authority_fields": any(str(key) in DENIED_AUTHORITY_FIELDS_V1 for key in value),
    }


def _controlled_metadata_from_input(controlled_metadata: Mapping[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    data = _default_controlled_metadata()
    reasons: list[str] = []
    if controlled_metadata is None:
        return data, reasons
    if not isinstance(controlled_metadata, Mapping):
        return data, ["controlled_metadata_not_mapping"]
    detections = _detect_unsafe_content(controlled_metadata)
    reasons.extend(_unsafe_detection_labels(detections))
    for key, value in controlled_metadata.items():
        key_s = str(key)
        if key_s not in ALLOWED_CONTROLLED_INPUTS_V1 and key_s not in DENIED_AUTHORITY_FIELDS_V1:
            _append_unique(reasons, f"unsupported_controlled_input:{key_s}")
            continue
        if key_s in DENIED_AUTHORITY_FIELDS_V1:
            if value is not False:
                _append_unique(reasons, f"authority_field_not_false:{key_s}")
            continue
        if key_s == "controlled_execution_label":
            data[key_s] = str(value)[:120]
        elif key_s.endswith("_count") or key_s.endswith("_count_metadata"):
            data[key_s] = value if isinstance(value, int) and value >= 0 else 0
            if not isinstance(value, int) or value < 0:
                _append_unique(reasons, f"invalid_count_metadata:{key_s}")
        elif key_s.endswith("_boolean") or key_s == "blocked_status_boolean" or key_s == "no_authority_boolean":
            data[key_s] = bool(value)
        elif isinstance(value, Mapping):
            data[key_s] = _summarize_safe_mapping(value)
        elif isinstance(value, (list, tuple, set)):
            data[key_s] = [str(item)[:120] for item in list(value)[:20] if isinstance(item, (str, int, bool))]
        elif isinstance(value, (str, int, bool)) or value is None:
            data[key_s] = value if not isinstance(value, str) else value[:160]
        else:
            data[key_s] = repr(value)[:160]
            _append_unique(reasons, f"unsupported_value_type:{key_s}")
    return data, list(dict.fromkeys(reasons))


def _derive_gate_metadata_summary(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "controlled_gate_status_label": metadata.get("controlled_gate_status_label", "present"),
        "controlled_gate_count": metadata.get("controlled_gate_count", 1),
        "governance_gate_label": metadata.get("synthetic_governance_gate_label", "authority_denied"),
        "capability_boundary_label": metadata.get("synthetic_capability_boundary_label", "helper_only_non_runtime"),
        "safety_boundary_label": metadata.get("synthetic_safety_boundary_label", "no_raw_content"),
    }


def _derive_candidate_metadata_summary(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "controlled_candidate_type_label": metadata.get("controlled_candidate_type_label", "metadata_candidate_only"),
        "controlled_candidate_count_metadata": metadata.get("controlled_candidate_count_metadata", 1),
        "controlled_candidate_rejection_reason_label": metadata.get("controlled_candidate_rejection_reason_label", "not_final_answer"),
        "controlled_selected_candidate_metadata_presence_boolean": bool(metadata.get("controlled_selected_candidate_metadata_presence_boolean", False)),
        "candidate_metadata_is_answer_draft": False,
        "selected_candidate_metadata_is_final_answer": False,
    }


def _invalid_json_safe_wrapper_v1(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    safe_reasons = _safe_error_labels(_as_list(reason_labels)) or ["invalid_or_unsafe_controlled_execution_artifact"]
    return {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "blocked": True,
        "unsafe_content_not_copied": True,
        "blocked_reason_labels": safe_reasons,
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "safety_confirmation": list(SAFETY_CONFIRMATION_V1),
        "next_lane": NEXT_LANE_V1,
    }


def build_controlled_answer_formation_execution_artifact_v1(
    controlled_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one in-memory controlled execution helper artifact from safe metadata."""

    safe_metadata, input_block_reasons = _controlled_metadata_from_input(controlled_metadata)
    source_summary = _source_metadata_summary()
    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "helper_only": True,
        "controlled_execution_helper_only": True,
        "synthetic_or_controlled_input_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free": True,
        "in_memory_only": True,
        "qualitative_only": True,
        "validation_before_controlled_execution": True,
        "validation_before_rendering": True,
        "safe_markdown_only": True,
        "json_safe_behavior_preserved": True,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        **source_summary,
        "allowed_controlled_inputs": list(ALLOWED_CONTROLLED_INPUTS_V1),
        "forbidden_inputs_checked": list(FORBIDDEN_INPUTS_V1),
        "controlled_execution_label": safe_metadata.get("controlled_execution_label"),
        "metadata_only_posture": "controlled_synthetic_metadata_only_internal_safe_markdown_no_authority",
        "validation_status": "validation_pending_metadata_quality_evidence_only",
        "blocked": False,
        "blocked_reason_labels": [],
        "controlled_metadata_summary": _summarize_safe_mapping(safe_metadata),
        "gate_metadata_summary": _derive_gate_metadata_summary(safe_metadata),
        "candidate_metadata_summary": _derive_candidate_metadata_summary(safe_metadata),
        "source_metadata_summary": source_summary,
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "aggregate_labels": list(AGGREGATE_LABELS_V1),
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "visible_risks": list(VISIBLE_RISKS_V1),
        "followups": list(FOLLOWUPS_V1),
        "safety_confirmation": list(SAFETY_CONFIRMATION_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for field in DENIED_AUTHORITY_FIELDS_V1:
        artifact[field] = False
    for reason in input_block_reasons:
        _append_unique(artifact["blocked_reason_labels"], reason)
    for reason in _derive_blocked_reasons(artifact):
        _append_unique(artifact["blocked_reason_labels"], reason)
    artifact["blocked"] = bool(artifact["blocked_reason_labels"])
    artifact["validation_status"] = (
        "blocked_invalid_or_unsafe_metadata_labels_only"
        if artifact["blocked"]
        else "validation_pass_metadata_quality_evidence_only"
    )
    return artifact


def _derive_blocked_reasons(artifact: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        reasons.append("artifact_type_mismatch")
    for field in _REQUIRED_TRUE_FIELDS:
        if artifact.get(field) is not True:
            reasons.append(f"required_true_field_not_true:{field}")
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            reasons.append(f"authority_field_not_false:{field}")
        denied = artifact.get("denied_authority_fields")
        if not isinstance(denied, Mapping) or denied.get(field) is not False:
            reasons.append(f"denied_authority_field_not_false:{field}")
    allowed = [str(item) for item in _as_list(artifact.get("allowed_controlled_inputs"))]
    if any(item not in ALLOWED_CONTROLLED_INPUTS_V1 for item in allowed):
        reasons.append("unknown_allowed_controlled_inputs")
    reasons.extend(_unsafe_detection_labels(_detect_unsafe_content(artifact)))
    return list(dict.fromkeys(reasons))


def validate_controlled_answer_formation_execution_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one controlled execution helper artifact without side effects."""

    errors: list[str] = []
    validation: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "artifact_type": None,
        "metadata_only": False,
        "internal_only": False,
        "helper_only": False,
        "controlled_execution_helper_only": False,
        "synthetic_or_controlled_input_only": False,
        "safety_booleans_valid": False,
        "authority_fields_false": False,
        "safe_markdown": False,
        "safe_to_render": False,
        "json_safe": False,
        "validation_status": "validation_failed",
    }
    if not isinstance(artifact, Mapping):
        errors.append("artifact_not_mapping")
        return validation

    validation["artifact_type"] = artifact.get("artifact_type")
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_mismatch")
    if artifact.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_mismatch")
    for field in _REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"missing_required_field:{field}")
    for field in _REQUIRED_TRUE_FIELDS:
        if artifact.get(field) is not True:
            errors.append(f"required_true_field_not_true:{field}")
    validation["metadata_only"] = artifact.get("metadata_only") is True
    validation["internal_only"] = artifact.get("internal_only") is True
    validation["helper_only"] = artifact.get("helper_only") is True
    validation["controlled_execution_helper_only"] = artifact.get("controlled_execution_helper_only") is True
    validation["synthetic_or_controlled_input_only"] = artifact.get("synthetic_or_controlled_input_only") is True
    validation["safety_booleans_valid"] = all(artifact.get(field) is True for field in _REQUIRED_TRUE_FIELDS)

    authority_ok = True
    denied = artifact.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        authority_ok = False
        errors.append("denied_authority_fields_not_mapping")
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            authority_ok = False
            errors.append(f"authority_field_not_false:{field}")
        if not isinstance(denied, Mapping) or denied.get(field) is not False:
            authority_ok = False
            errors.append(f"denied_authority_field_not_false:{field}")
    validation["authority_fields_false"] = authority_ok

    blocked_reasons = [str(item) for item in _as_list(artifact.get("blocked_reason_labels"))]
    derived_reasons = _derive_blocked_reasons(artifact)
    for reason in derived_reasons:
        if reason not in blocked_reasons:
            errors.append(f"missing_blocked_reason:{reason}")
    if artifact.get("blocked") is not bool(blocked_reasons):
        errors.append("blocked_flag_does_not_match_reasons")

    for label in _unsafe_detection_labels(_detect_unsafe_content(artifact)):
        if label not in blocked_reasons:
            errors.append(f"unsafe_content_detected:{label}")

    validation["safe_markdown"] = artifact.get("safe_markdown_only") is True and not any(
        str(error).startswith("unsafe_content_detected") for error in errors
    )
    validation["safe_to_render"] = not errors and artifact.get("validation_before_rendering") is True
    validation["json_safe"] = not errors
    validation["blocked"] = bool(errors or artifact.get("blocked") is True)
    validation["valid"] = not errors and artifact.get("blocked") is False
    validation["validation_status"] = (
        "validation_pass_metadata_quality_evidence_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only"
    )
    return validation


def summarize_controlled_answer_formation_execution_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact safe metadata summary for one artifact."""

    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)
    return {
        "artifact_type": artifact.get("artifact_type") if isinstance(artifact, Mapping) else None,
        "schema_version": artifact.get("schema_version") if isinstance(artifact, Mapping) else None,
        "valid": validation.get("valid") is True,
        "blocked": validation.get("blocked") is True,
        "validation_status": validation.get("validation_status"),
        "metadata_only": bool(isinstance(artifact, Mapping) and artifact.get("metadata_only") is True),
        "internal_only": bool(isinstance(artifact, Mapping) and artifact.get("internal_only") is True),
        "helper_only": bool(isinstance(artifact, Mapping) and artifact.get("helper_only") is True),
        "controlled_execution_helper_only": bool(isinstance(artifact, Mapping) and artifact.get("controlled_execution_helper_only") is True),
        "controlled_execution_label": artifact.get("controlled_execution_label") if isinstance(artifact, Mapping) else None,
        "blocked_reason_labels": _safe_error_labels(_as_list(artifact.get("blocked_reason_labels") if isinstance(artifact, Mapping) else [])),
        "gate_metadata_summary": _json_safe(artifact.get("gate_metadata_summary") if isinstance(artifact, Mapping) else {}),
        "candidate_metadata_summary": _json_safe(artifact.get("candidate_metadata_summary") if isinstance(artifact, Mapping) else {}),
        "source_metadata_summary": _json_safe(artifact.get("source_metadata_summary") if isinstance(artifact, Mapping) else {}),
        "denied_authority_fields_false": validation.get("authority_fields_false") is True,
        "aggregate_labels": _json_safe(artifact.get("aggregate_labels") if isinstance(artifact, Mapping) else []),
        "visible_risks": _json_safe(artifact.get("visible_risks") if isinstance(artifact, Mapping) else []),
        "followups": _json_safe(artifact.get("followups") if isinstance(artifact, Mapping) else []),
        "next_lane": artifact.get("next_lane") if isinstance(artifact, Mapping) else NEXT_LANE_V1,
    }


def _safe_blocked_markdown_v1(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reasons = _safe_error_labels(_as_list(summary.get("blocked_reason_labels")) + _as_list(validation.get("errors")))
    lines = [
        "# WESLR Controlled Answer Formation Execution Helper Artifact V1",
        "",
        "- artifact_type: `controlled_answer_formation_execution_artifact_v1_invalid`",
        "- valid: `False`",
        "- blocked: `True`",
        "- unsafe_content_not_copied: `True`",
        "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
        "",
        "## Blocked Reason Labels",
    ]
    lines.extend(f"- `{reason}`" for reason in (reasons or ["invalid_or_unsafe_controlled_execution_artifact"]))
    lines.extend([
        "",
        "## Safety Boundary",
        "- `no_controlled_execution_performed`",
        "- `no_answer_formation_execution`",
        "- `no_answer_composition`",
        "- `no_final_answer_generation`",
        "- `no_runtime_wiring`",
        "- `no_provider_search_advisor_calls`",
        "- `no_execution_result_artifact_created`",
        f"- next_lane: `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_controlled_answer_formation_execution_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown after validation; invalid artifacts render safe labels only."""

    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)
    summary = summarize_controlled_answer_formation_execution_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _safe_blocked_markdown_v1(validation, summary)

    lines = [
        "# WESLR Controlled Answer Formation Execution Helper Artifact V1",
        "",
        "## Artifact Status",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- validation_status: `{summary['validation_status']}`",
        f"- controlled_execution_label: `{summary['controlled_execution_label']}`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- helper_only: `True`",
        "- controlled_execution_helper_only: `True`",
        "- synthetic_or_controlled_input_only: `True`",
        "",
        "## Source Paths",
    ]
    for key, value in summary["source_metadata_summary"].items():
        if isinstance(value, list):
            lines.append(f"- {key}:")
            lines.extend(f"  - `{item}`" for item in value)
        else:
            lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Gate Metadata Summary"])
    for key, value in summary["gate_metadata_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Candidate Metadata Summary"])
    for key, value in summary["candidate_metadata_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Denied Authority Fields"])
    lines.extend(f"- `{field}=false`" for field in DENIED_AUTHORITY_FIELDS_V1)
    lines.extend(["", "## Visible Risks"])
    lines.extend(f"- `{risk}`" for risk in summary["visible_risks"])
    lines.extend(["", "## Followups"])
    lines.extend(f"- `{followup}`" for followup in summary["followups"])
    lines.extend(["", "## Safety Boundary"])
    lines.extend(f"- `{label}`" for label in SAFETY_CONFIRMATION_V1)
    lines.extend(["", "## Next Lane", f"- `{summary['next_lane']}`"])
    return "\n".join(lines) + "\n"


def to_controlled_answer_formation_execution_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe metadata or a safe invalid wrapper without unsafe values."""

    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _invalid_json_safe_wrapper_v1(_as_list(validation.get("errors")) or _as_list(validation.get("blocked_reason_labels")))
    return _json_safe(artifact)
