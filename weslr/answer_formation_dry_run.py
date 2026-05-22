"""WESLR answer formation dry-run helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
synthetic answer formation dry-run artifacts. These helpers do not execute a dry
run, create a result artifact, execute answer formation, compose answers,
generate final-answer prose, answer real user queries, call ChatResponder,
respond_chat(), generate_chat(), providers, search, advisors, wire runtime,
persist state, write files, enable feature flags, create judges or scores, make
official claims, or grant answer, composition, or runtime authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr.answer_formation import (
    ALLOWED_CANDIDATE_REJECTION_LABELS_V1 as SOURCE_ALLOWED_CANDIDATE_REJECTION_LABELS_V1,
    ALLOWED_GATE_STATUSES_V1 as SOURCE_ALLOWED_GATE_STATUSES_V1,
    summarize_answer_formation_artifact_v1,
    validate_answer_formation_artifact_v1,
)
from weslr.answer_formation_report import (
    summarize_answer_formation_report_v1,
    validate_answer_formation_report_v1,
)
from weslr.answer_formation_report_run import (
    RESULT_ARTIFACT_PATH_V1 as SOURCE_REPORT_RUN_RESULT_ARTIFACT_PATH_V1,
)

ARTIFACT_TYPE_V1 = "answer_formation_dry_run_artifact_v1"
SCHEMA_VERSION_V1 = "answer_formation_dry_run_artifact_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_formation_dry_run_artifact_v1_invalid"

HELPER_MODULE_PATH_V1 = "weslr/answer_formation_dry_run.py"
TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_dry_run_v1.py"
SOURCE_BOUNDARY_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_V1.md"
SOURCE_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_BOUNDARY_REVIEW_V1.md"
SOURCE_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_DRY_RUN_HELPERS_REVIEW_V1.md"
SOURCE_REPORT_RUN_RESULT_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_V1.md"
SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_REPORT_RUN_RESULT_REVIEW_V1.md"
SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1 = "weslr/answer_formation.py"
SOURCE_REPORT_HELPER_MODULE_PATH_V1 = "weslr/answer_formation_report.py"
SOURCE_REPORT_RUN_MODULE_PATH_V1 = "weslr/answer_formation_report_run.py"
NEXT_LANE_V1 = "REVIEW_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_V1"

ALLOWED_SYNTHETIC_METADATA_INPUTS_V1 = (
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
    "safe_source_path_label",
    "safe_artifact_type_label",
    "safe_schema_version_label",
    "safe_answer_formation_artifact_metadata",
    "safe_answer_formation_report_artifact_metadata",
    "safe_answer_formation_report_run_result_metadata",
    "safe_report_helper_validation_dictionary",
    "safe_report_helper_summary_dictionary",
    "validation_status_label",
    "blocked_status_boolean",
    "blocked_reason_label",
    "gate_status_label",
    "gate_count",
    "candidate_type_label",
    "candidate_count_metadata",
    "candidate_rejection_reason_label",
    "selected_candidate_metadata_presence_boolean",
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
    "dry_run_result_artifact_created",
    "official_answer_claim_made",
)

REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "dry_run_metadata_not_answer_text",
    "dry_run_artifact_not_final_answer",
    "candidate_metadata_not_answer_draft",
    "selected_candidate_metadata_not_final_answer",
    "validation_pass_not_answer_correctness",
    "validation_pass_not_answer_authority",
    "report_run_result_not_final_answer",
    "answer_formation_execution_requires_separate_approval",
    "answer_composition_requires_separate_approval",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "occ_openclaw_not_deployed_weslr",
)

AGGREGATE_LABELS_V1 = (
    "metadata_only_dry_run_artifact",
    "internal_only_dry_run_artifact",
    "helper_based_dry_run_artifact",
    "synthetic_metadata_only",
    "dry_run_not_executed",
    "dry_run_result_artifact_not_created",
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
    "safe_markdown_eligible",
    "json_safe_eligible",
)

VISIBLE_RISKS_V1 = (
    "metadata-overread",
    "dry-run-as-answer-formation",
    "dry-run-as-authority",
    "dry-run-result-as-final-answer",
    "report-run-result-as-final-answer",
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
    "review_answer_formation_dry_run_helpers_implementation_v1",
    "keep_dry_run_execution_separate",
    "keep_dry_run_result_artifact_separate",
    "keep_answer_formation_execution_separate",
    "keep_answer_composition_separate",
    "keep_final_answer_generation_separate",
    "keep_runtime_live_chat_integration_separate",
)

ABORT_CONDITIONS_V1 = (
    "repo_assertion_failure",
    "unexpected_scoped_tracked_changes",
    "chat_responder_edit_import_or_call",
    "unauthorized_source_or_test_edit",
    "real_user_answering_detected",
    "final_answer_prose_detected",
    "provider_search_advisor_call_detected",
    "prompt_execution_or_live_dialogue_detected",
    "runtime_wiring_detected",
    "dot_weslr_write_detected",
    "feature_flag_enablement_detected",
    "judge_or_score_detected",
    "official_claim_detected",
    "authority_grant_detected",
    "unsafe_content_leakage_detected",
    "validation_before_rendering_unavailable",
    "unsafe_markdown_detected",
    "unsafe_json_detected",
)

FUTURE_IMPLEMENTATION_SEQUENCE_V1 = (
    "REVIEW_ANSWER_FORMATION_DRY_RUN_HELPERS_IMPLEMENTATION_V1",
    "DESIGN_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1",
    "IMPLEMENT_ANSWER_FORMATION_DRY_RUN_EXECUTION_V1",
    "EXECUTE_ANSWER_FORMATION_DRY_RUN_RESULT_V1",
    "REVIEW_ANSWER_FORMATION_DRY_RUN_RESULT_V1",
)

SAFETY_CONFIRMATION_V1 = (
    "helper_only",
    "metadata_only",
    "internal_only",
    "dry_run_only",
    "synthetic_metadata_only",
    "no_dry_run_execution",
    "no_dry_run_result_artifact_created",
    "no_answer_formation_execution",
    "no_answer_composition",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_prompt_execution_or_live_dialogue",
    "no_chat_responder_calls",
    "no_respond_chat_calls",
    "no_generate_chat_calls",
    "no_provider_search_advisor_calls",
    "no_dot_weslr_writes",
    "no_feature_flags",
    "no_judges_or_scoring",
    "no_official_claims",
    "no_answer_authority_granted",
    "no_composition_authority_granted",
    "no_runtime_authority_granted",
    "weslr_chat_responder_py_untouched",
    "validation_before_rendering_required",
    "safe_markdown_required",
    "json_safe_required",
    "validation_pass_metadata_quality_evidence_only",
    "occ_openclaw_not_deployed_weslr",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "dry_run_only",
    "helper_based",
    "synthetic_metadata_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "import_safe",
    "side_effect_free",
    "in_memory_only",
    "qualitative_only",
    "validation_before_rendering",
    "safe_markdown_only",
    "json_safe_behavior_preserved",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    *_REQUIRED_TRUE_FIELDS,
    "future_helper_module_path",
    "future_test_module_path",
    "source_boundary_design_doc",
    "source_boundary_review_doc",
    "source_helpers_design_doc",
    "source_helpers_review_doc",
    "source_report_run_result_doc",
    "source_report_run_result_review_doc",
    "source_answer_formation_helper_module_path",
    "source_report_helper_module_path",
    "source_report_run_module_path",
    "allowed_synthetic_metadata_inputs",
    "forbidden_inputs_checked",
    "dry_run_flow_labels",
    "synthetic_metadata_summary",
    "candidate_metadata_summary",
    "gate_metadata_summary",
    "validation_summary",
    "blocked_status",
    "blocked_reason_labels",
    "required_no_authority_labels",
    "denied_authority_fields",
    "aggregate_labels",
    "visible_risks",
    "followups",
    "abort_conditions",
    "future_implementation_sequence",
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

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | set(DENIED_AUTHORITY_FIELDS_V1) | {
    "source_answer_formation_helper_module_path",
    "source_report_helper_module_path",
    "source_report_run_module_path",
    "source_report_run_result_doc",
    "source_report_run_result_review_doc",
    "dry_run_artifact_not_final_answer",
    "report_run_result_not_final_answer",
    "candidate_metadata_not_answer_draft",
    "selected_candidate_metadata_not_final_answer",
    "validation_pass_not_answer_correctness",
    "validation_pass_not_answer_authority",
    "answer_formation_execution_requires_separate_approval",
    "answer_composition_requires_separate_approval",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "final_answer_not_generated",
    "runtime_not_wired",
    "prompt_execution_not_allowed",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "official_claims_not_allowed",
    "chat_responder_not_called",
    "no_final_answer_generation",
    "no_runtime_wiring",
    "no_provider_search_advisor_calls",
    "no_dot_weslr_writes",
    "no_official_claims",
    "no_answer_authority_granted",
    "no_composition_authority_granted",
    "no_runtime_authority_granted",
    "no_dry_run_result_artifact_created",
    "validation_pass_metadata_quality_evidence_only",
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
_ALLOWED_KEYS_WITH_RISK_WORDS.update(_TEXT_MARKERS)
_ALLOWED_KEYS_WITH_RISK_WORDS.update({label for labels in _TEXT_MARKERS.values() for label in labels})


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
            elif "hidden" in key:
                found["hidden_prompt_detected"] = True
            elif "answer_key" in key:
                found["answer_key_detected"] = True
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
    labels = _safe_error_labels(list(reason_labels)) or ["invalid_or_unsafe_dry_run_artifact"]
    wrapper: dict[str, Any] = {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "valid": False,
        "blocked": True,
        "errors": labels,
        "unsafe_content_not_copied": True,
        "metadata_only": True,
        "internal_only": True,
        "dry_run_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "safe_label_only": True,
        "blocked_reason_labels": labels,
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "visible_risks": list(VISIBLE_RISKS_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for field in DENIED_AUTHORITY_FIELDS_V1:
        wrapper[field] = False
    return wrapper


def _safe_source_summaries(source_artifacts: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
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
        summary = summarize_answer_formation_artifact_v1(artifact)
        summaries.append({
            "artifact_type": str(summary.get("artifact_type", "unknown_artifact_type")),
            "valid": bool(summary.get("valid")),
            "blocked": bool(summary.get("blocked")),
            "metadata_only": bool(summary.get("metadata_only")),
            "internal_only": bool(summary.get("internal_only")),
            "gate_status_count": int(summary.get("gate_status_count", 0)),
            "candidate_count": int(summary.get("candidate_count", 0)),
            "rejection_label_count": int(summary.get("rejection_label_count", 0)),
            "validation_error_labels": [str(label) for label in _as_list(summary.get("validation_error_labels"))],
            "next_lane": str(summary.get("next_lane", "unknown_next_lane")),
        })
    return summaries


def _safe_report_summary(report_artifact: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(report_artifact, Mapping):
        return {
            "artifact_type": "not_supplied",
            "valid": False,
            "blocked": False,
            "validation_error_labels": [],
        }
    summary = summarize_answer_formation_report_v1(report_artifact)
    return {
        "artifact_type": str(summary.get("artifact_type", "unknown_artifact_type")),
        "valid": bool(summary.get("valid")),
        "blocked": bool(summary.get("blocked")),
        "source_artifact_count": int(summary.get("source_artifact_count", 0)),
        "valid_source_artifact_count": int(summary.get("valid_source_artifact_count", 0)),
        "candidate_count_total": int(summary.get("candidate_count_total", 0)),
        "validation_error_labels": [str(label) for label in _as_list(summary.get("validation_error_labels"))],
    }


def _summarize_synthetic_metadata(synthetic_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(synthetic_metadata, Mapping):
        return {
            "supplied": False,
            "input_key_count": 0,
            "allowed_input_key_count": 0,
            "unknown_input_key_labels": [],
            "unsafe_detection_labels": [],
        }
    keys = [str(key) for key in synthetic_metadata.keys()]
    unknown = [key for key in keys if key not in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1]
    detections = _unsafe_detection_labels(_detect_unsafe_content(synthetic_metadata))
    return {
        "supplied": True,
        "input_key_count": len(keys),
        "allowed_input_key_count": len([key for key in keys if key in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1]),
        "unknown_input_key_labels": sorted(unknown),
        "unsafe_detection_labels": detections,
    }


def _derive_gate_metadata_summary(source_artifacts: list[Mapping[str, Any]], synthetic_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    statuses: list[str] = []
    for artifact in source_artifacts:
        gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
        if isinstance(gates, Mapping):
            statuses.extend(str(status) for status in gates.values())
    synthetic_gate = synthetic_metadata.get("gate_status_label") if isinstance(synthetic_metadata, Mapping) else None
    if isinstance(synthetic_gate, str):
        statuses.append(synthetic_gate)
    counts: dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    return {
        "gate_status_counts": dict(sorted(counts.items())),
        "gate_status_total": len(statuses),
        "allowed_gate_statuses": list(SOURCE_ALLOWED_GATE_STATUSES_V1),
    }


def _derive_candidate_metadata_summary(source_artifacts: list[Mapping[str, Any]], synthetic_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    candidate_total = 0
    rejection_labels: list[str] = []
    selected_present = 0
    for artifact in source_artifacts:
        metadata = artifact.get("candidate_formation_metadata") if isinstance(artifact, Mapping) else None
        if isinstance(metadata, Mapping):
            count = metadata.get("candidate_count", 0)
            if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                candidate_total += count
            if metadata.get("selected_candidate_metadata_present") is True:
                selected_present += 1
        rejection = artifact.get("candidate_rejection_metadata") if isinstance(artifact, Mapping) else None
        if isinstance(rejection, Mapping):
            rejection_labels.extend(str(label) for label in _as_list(rejection.get("rejection_reason_labels")))
    if isinstance(synthetic_metadata, Mapping):
        synthetic_count = synthetic_metadata.get("candidate_count_metadata")
        if isinstance(synthetic_count, int) and not isinstance(synthetic_count, bool) and synthetic_count >= 0:
            candidate_total += synthetic_count
        if synthetic_metadata.get("selected_candidate_metadata_presence_boolean") is True:
            selected_present += 1
        for label in _as_list(synthetic_metadata.get("candidate_rejection_reason_label")):
            if label:
                rejection_labels.append(str(label))
    return {
        "candidate_count_total": candidate_total,
        "selected_candidate_metadata_present_count": selected_present,
        "rejection_label_count": len(rejection_labels),
        "rejection_labels": sorted(set(rejection_labels)),
        "allowed_rejection_labels": list(SOURCE_ALLOWED_CANDIDATE_REJECTION_LABELS_V1),
    }


def _derive_validation_summary(
    source_artifacts: list[Mapping[str, Any]],
    report_artifact: Mapping[str, Any] | None,
    synthetic_metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    error_labels: list[str] = []
    valid_sources = 0
    blocked_sources = 0
    for artifact in source_artifacts:
        validation = validate_answer_formation_artifact_v1(artifact) if isinstance(artifact, Mapping) else {"valid": False, "blocked": True, "errors": ["artifact_not_mapping"]}
        if validation.get("valid") is True:
            valid_sources += 1
        if validation.get("blocked") is True:
            blocked_sources += 1
        for label in _safe_error_labels(_as_list(validation.get("errors"))):
            _append_unique(error_labels, label)
        for label in _unsafe_detection_labels(validation):
            _append_unique(error_labels, label)
    report_validation = validate_answer_formation_report_v1(report_artifact) if isinstance(report_artifact, Mapping) else None
    if isinstance(report_validation, Mapping):
        for label in _safe_error_labels(_as_list(report_validation.get("errors"))):
            _append_unique(error_labels, f"report_{label}")
        for label in _unsafe_detection_labels(report_validation):
            _append_unique(error_labels, f"report_{label}")
    if isinstance(synthetic_metadata, Mapping):
        for label in _unsafe_detection_labels(_detect_unsafe_content(synthetic_metadata)):
            _append_unique(error_labels, label)
        for key in synthetic_metadata.keys():
            if str(key) not in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1:
                _append_unique(error_labels, "unknown_synthetic_metadata_input")
    return {
        "source_artifact_count": len(source_artifacts),
        "valid_source_artifact_count": valid_sources,
        "blocked_source_artifact_count": blocked_sources,
        "report_artifact_supplied": isinstance(report_artifact, Mapping),
        "report_artifact_valid": bool(isinstance(report_validation, Mapping) and report_validation.get("valid") is True),
        "validation_error_labels": error_labels,
        "validation_pass_means_metadata_quality_evidence_only": True,
    }


def _derive_blocked_reasons(artifact: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for label in _unsafe_detection_labels(_detect_unsafe_content(artifact)):
        _append_unique(reasons, label)
    validation_summary = artifact.get("validation_summary")
    if isinstance(validation_summary, Mapping):
        if validation_summary.get("blocked_source_artifact_count", 0):
            _append_unique(reasons, "blocked_source_artifacts_present")
        for label in _as_list(validation_summary.get("validation_error_labels")):
            _append_unique(reasons, str(label))
    synthetic_summary = artifact.get("synthetic_metadata_summary")
    if isinstance(synthetic_summary, Mapping):
        if synthetic_summary.get("unknown_input_key_labels"):
            _append_unique(reasons, "unknown_synthetic_metadata_inputs")
        for label in _as_list(synthetic_summary.get("unsafe_detection_labels")):
            _append_unique(reasons, str(label))
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            _append_unique(reasons, f"authority_field_not_false:{field}")
    return reasons


def build_answer_formation_dry_run_artifact_v1(
    synthetic_metadata: Mapping[str, Any] | None = None,
    source_artifacts: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...] | None = None,
    *,
    report_artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one in-memory metadata-only answer formation dry-run artifact."""

    safe_sources = [item for item in _as_list(source_artifacts) if isinstance(item, Mapping)]
    synthetic_summary = _summarize_synthetic_metadata(synthetic_metadata)
    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "dry_run_only": True,
        "helper_based": True,
        "synthetic_metadata_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free": True,
        "in_memory_only": True,
        "qualitative_only": True,
        "validation_before_rendering": True,
        "safe_markdown_only": True,
        "json_safe_behavior_preserved": True,
        "future_helper_module_path": HELPER_MODULE_PATH_V1,
        "future_test_module_path": TEST_MODULE_PATH_V1,
        "source_boundary_design_doc": SOURCE_BOUNDARY_DESIGN_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        "source_report_run_result_doc": SOURCE_REPORT_RUN_RESULT_DOC_V1,
        "source_report_run_result_review_doc": SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1,
        "source_report_run_result_artifact_path": SOURCE_REPORT_RUN_RESULT_ARTIFACT_PATH_V1,
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_report_helper_module_path": SOURCE_REPORT_HELPER_MODULE_PATH_V1,
        "source_report_run_module_path": SOURCE_REPORT_RUN_MODULE_PATH_V1,
        "allowed_synthetic_metadata_inputs": list(ALLOWED_SYNTHETIC_METADATA_INPUTS_V1),
        "forbidden_inputs_checked": list(FORBIDDEN_INPUTS_V1),
        "dry_run_flow_labels": [
            "explicit_synthetic_metadata_received",
            "runtime_handles_absent",
            "source_metadata_summarized",
            "synthetic_metadata_keys_checked",
            "authority_denials_preserved",
            "blocked_status_derived_from_safe_labels",
            "safe_markdown_renderable_after_validation",
            "json_safe_copy_available_after_validation",
            "no_result_artifact_created",
        ],
        "synthetic_metadata_summary": synthetic_summary,
        "source_artifact_summary": _safe_source_summaries(safe_sources),
        "report_artifact_summary": _safe_report_summary(report_artifact),
        "candidate_metadata_summary": _derive_candidate_metadata_summary(safe_sources, synthetic_metadata),
        "gate_metadata_summary": _derive_gate_metadata_summary(safe_sources, synthetic_metadata),
        "validation_summary": _derive_validation_summary(safe_sources, report_artifact, synthetic_metadata),
        "blocked_status": False,
        "blocked_reason_labels": [],
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "aggregate_labels": list(AGGREGATE_LABELS_V1),
        "visible_risks": list(VISIBLE_RISKS_V1),
        "followups": list(FOLLOWUPS_V1),
        "abort_conditions": list(ABORT_CONDITIONS_V1),
        "future_implementation_sequence": list(FUTURE_IMPLEMENTATION_SEQUENCE_V1),
        "safety_confirmation": list(SAFETY_CONFIRMATION_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for field in DENIED_AUTHORITY_FIELDS_V1:
        artifact[field] = False
    for reason in _derive_blocked_reasons(artifact):
        _append_unique(artifact["blocked_reason_labels"], reason)
    artifact["blocked_status"] = bool(artifact["blocked_reason_labels"])
    return artifact


def validate_answer_formation_dry_run_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one dry-run artifact without side effects."""

    errors: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "synthetic_metadata_valid": False,
        "json_safe": False,
        "safe_to_render": False,
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

    expected_paths = {
        "future_helper_module_path": HELPER_MODULE_PATH_V1,
        "future_test_module_path": TEST_MODULE_PATH_V1,
        "source_boundary_design_doc": SOURCE_BOUNDARY_DESIGN_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        "source_report_run_result_doc": SOURCE_REPORT_RUN_RESULT_DOC_V1,
        "source_report_run_result_review_doc": SOURCE_REPORT_RUN_RESULT_REVIEW_DOC_V1,
        "source_answer_formation_helper_module_path": SOURCE_ANSWER_FORMATION_HELPER_MODULE_PATH_V1,
        "source_report_helper_module_path": SOURCE_REPORT_HELPER_MODULE_PATH_V1,
        "source_report_run_module_path": SOURCE_REPORT_RUN_MODULE_PATH_V1,
        "next_lane": NEXT_LANE_V1,
    }
    for key, expected in expected_paths.items():
        if artifact.get(key) != expected:
            errors.append(f"{key}_invalid")

    allowed = [str(item) for item in _as_list(artifact.get("allowed_synthetic_metadata_inputs"))]
    if any(item not in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1 for item in allowed):
        errors.append("unknown_allowed_synthetic_metadata_inputs")
    if any(item not in allowed for item in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1):
        errors.append("missing_allowed_synthetic_metadata_inputs")
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

    synthetic_summary = artifact.get("synthetic_metadata_summary")
    synthetic_ok = isinstance(synthetic_summary, Mapping) and not synthetic_summary.get("unknown_input_key_labels") and not synthetic_summary.get("unsafe_detection_labels")
    result["synthetic_metadata_valid"] = synthetic_ok
    if not synthetic_ok:
        errors.append("synthetic_metadata_summary_invalid")

    validation_summary = artifact.get("validation_summary")
    if not isinstance(validation_summary, Mapping):
        errors.append("validation_summary_not_mapping")
    elif validation_summary.get("validation_error_labels"):
        errors.append("validation_summary_errors_present")

    for label in REQUIRED_NO_AUTHORITY_LABELS_V1:
        if label not in _as_list(artifact.get("required_no_authority_labels")):
            errors.append(f"missing_required_no_authority_label:{label}")
    for label in AGGREGATE_LABELS_V1:
        if label not in _as_list(artifact.get("aggregate_labels")):
            errors.append(f"missing_aggregate_label:{label}")
    unknown_aggregate = [label for label in _as_list(artifact.get("aggregate_labels")) if str(label) not in AGGREGATE_LABELS_V1]
    if unknown_aggregate:
        errors.append("unknown_aggregate_labels")

    for label, detected in _detect_unsafe_content(artifact).items():
        result[label] = detected
        if detected:
            errors.append(label)

    blocked_reasons = [str(item) for item in _as_list(artifact.get("blocked_reason_labels"))]
    if artifact.get("blocked_status") is True and not blocked_reasons:
        errors.append("blocked_without_reason")
    if artifact.get("blocked_status") is False and blocked_reasons:
        errors.append("blocked_reasons_present_but_not_blocked")

    result["blocked"] = bool(artifact.get("blocked_status") is True or errors)
    result["json_safe"] = not errors
    result["safe_to_render"] = not errors
    result["valid"] = not errors and artifact.get("blocked_status") is False
    return result


def summarize_answer_formation_dry_run_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a labels/counts/booleans-only summary for one dry-run artifact."""

    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    if not isinstance(artifact, Mapping):
        return {
            "artifact_type": "artifact_not_mapping",
            "valid": False,
            "blocked": True,
            "metadata_only": False,
            "internal_only": False,
            "dry_run_only": False,
            "all_authority_fields_false": False,
            "validation_error_labels": _safe_error_labels(_as_list(validation.get("errors"))),
            "next_lane": NEXT_LANE_V1,
        }
    validation_summary = artifact.get("validation_summary") if isinstance(artifact.get("validation_summary"), Mapping) else {}
    candidate_summary = artifact.get("candidate_metadata_summary") if isinstance(artifact.get("candidate_metadata_summary"), Mapping) else {}
    return {
        "artifact_type": str(artifact.get("artifact_type", "unknown_artifact_type")),
        "schema_version": str(artifact.get("schema_version", "unknown_schema_version")),
        "valid": bool(validation.get("valid")),
        "blocked": bool(validation.get("blocked")),
        "metadata_only": artifact.get("metadata_only") is True,
        "internal_only": artifact.get("internal_only") is True,
        "dry_run_only": artifact.get("dry_run_only") is True,
        "synthetic_metadata_only": artifact.get("synthetic_metadata_only") is True,
        "all_authority_fields_false": all(artifact.get(field) is False for field in DENIED_AUTHORITY_FIELDS_V1),
        "source_artifact_count": int(validation_summary.get("source_artifact_count", 0)),
        "valid_source_artifact_count": int(validation_summary.get("valid_source_artifact_count", 0)),
        "candidate_count_total": int(candidate_summary.get("candidate_count_total", 0)),
        "selected_candidate_metadata_present_count": int(candidate_summary.get("selected_candidate_metadata_present_count", 0)),
        "blocked_reason_labels": [str(label) for label in _as_list(artifact.get("blocked_reason_labels"))],
        "validation_error_labels": _safe_error_labels(_as_list(validation.get("errors"))),
        "aggregate_labels": [str(label) for label in _as_list(artifact.get("aggregate_labels"))],
        "next_lane": str(artifact.get("next_lane", NEXT_LANE_V1)),
    }


def render_answer_formation_dry_run_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown after validation, or a blocked safe template."""

    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    if validation.get("valid") is not True:
        reasons = _safe_error_labels(_as_list(validation.get("errors")))
        lines = [
            "# WESLR Answer Formation Dry-Run Artifact V1 — Blocked",
            "",
            "- artifact_type: `answer_formation_dry_run_artifact_v1_invalid`",
            "- valid: `False`",
            "- blocked: `True`",
            "- unsafe_content_not_copied: `True`",
            "",
            "## Safe Blocked Reason Labels",
        ]
        lines.extend(f"- `{reason}`" for reason in reasons)
        lines.extend([
            "",
            "## No-Authority Labels",
        ])
        lines.extend(f"- `{label}`" for label in REQUIRED_NO_AUTHORITY_LABELS_V1)
        lines.extend([
            "",
            "## Next Lane",
            f"- `{NEXT_LANE_V1}`",
        ])
        return "\n".join(lines) + "\n"

    summary = summarize_answer_formation_dry_run_artifact_v1(artifact)
    lines = [
        "# WESLR Answer Formation Dry-Run Artifact V1",
        "",
        "Layer: `WESLR_CANON_ALIGNMENT` helper artifact only",
        "",
        "## Artifact Status",
        f"- artifact_type: `{artifact.get('artifact_type')}`",
        f"- schema_version: `{artifact.get('schema_version')}`",
        f"- valid: `{validation.get('valid')}`",
        f"- blocked: `{artifact.get('blocked_status')}`",
        f"- metadata_only: `{artifact.get('metadata_only')}`",
        f"- internal_only: `{artifact.get('internal_only')}`",
        f"- dry_run_only: `{artifact.get('dry_run_only')}`",
        f"- synthetic_metadata_only: `{artifact.get('synthetic_metadata_only')}`",
        f"- helper_based: `{artifact.get('helper_based')}`",
        f"- all_authority_fields_false: `{summary.get('all_authority_fields_false')}`",
        "",
        "## Source Paths",
        f"- future_helper_module_path: `{artifact.get('future_helper_module_path')}`",
        f"- future_test_module_path: `{artifact.get('future_test_module_path')}`",
        f"- source_answer_formation_helper_module_path: `{artifact.get('source_answer_formation_helper_module_path')}`",
        f"- source_report_helper_module_path: `{artifact.get('source_report_helper_module_path')}`",
        f"- source_report_run_module_path: `{artifact.get('source_report_run_module_path')}`",
        f"- source_report_run_result_doc: `{artifact.get('source_report_run_result_doc')}`",
        "",
        "## Counts",
        f"- source_artifact_count: `{summary.get('source_artifact_count')}`",
        f"- valid_source_artifact_count: `{summary.get('valid_source_artifact_count')}`",
        f"- candidate_count_total: `{summary.get('candidate_count_total')}`",
        f"- selected_candidate_metadata_present_count: `{summary.get('selected_candidate_metadata_present_count')}`",
        "",
        "## Required No-Authority Labels",
    ]
    lines.extend(f"- `{label}`" for label in _as_list(artifact.get("required_no_authority_labels")))
    lines.extend(["", "## Aggregate Labels"])
    lines.extend(f"- `{label}`" for label in _as_list(artifact.get("aggregate_labels")))
    lines.extend(["", "## Denied Authority Fields"])
    lines.extend(f"- `{field}=false`" for field in DENIED_AUTHORITY_FIELDS_V1)
    lines.extend(["", "## Visible Risks"])
    lines.extend(f"- `{risk}`" for risk in _as_list(artifact.get("visible_risks")))
    lines.extend(["", "## Followups"])
    lines.extend(f"- `{followup}`" for followup in _as_list(artifact.get("followups")))
    lines.extend(["", "## Safety Confirmation"])
    lines.extend(f"- `{label}`" for label in _as_list(artifact.get("safety_confirmation")))
    lines.extend(["", "## Next Lane", f"- `{artifact.get('next_lane')}`"])
    return "\n".join(lines) + "\n"


def to_answer_formation_dry_run_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe copy or a safe invalid wrapper without unsafe values."""

    validation = validate_answer_formation_dry_run_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _invalid_json_safe_wrapper_v1(_as_list(validation.get("errors")))
    safe = _json_safe(artifact)
    if not isinstance(safe, dict):
        return _invalid_json_safe_wrapper_v1(["json_safe_conversion_failed"])
    return safe
