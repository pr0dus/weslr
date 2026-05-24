"""WESLR controlled user-facing output metadata helpers V1.

Helper-only, metadata-only, internal-only, deterministic, in-memory helpers for
controlled user-facing-output metadata artifacts. This module arranges safe
metadata labels only. It does not execute user-facing output, create reply text,
create live dialogue, generate final answers, create answer drafts, wire runtime
behavior, call chat/runtime/provider/search/advisor paths, read or write .weslr
state, enable feature flags, create judges or scores, make official claims, or
grant answer/user-facing-output/composition/runtime/official evaluation authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARTIFACT_TYPE_V1 = "controlled_user_facing_output_artifact_v1"
INVALID_ARTIFACT_TYPE_V1 = "controlled_user_facing_output_artifact_v1_invalid"
SCHEMA_VERSION_V1 = "controlled_user_facing_output_artifact_schema_v1"

SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_ARTIFACT_PATH_V1 = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_V1.md"
SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_REVIEW_PATH_V1 = "docs/WESLR_CONTROLLED_FINAL_ANSWER_GENERATION_RESULT_ARTIFACT_REVIEW_V1.md"
SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_DOC_V1 = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_V1.md"
SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_V1.md"
SOURCE_HELPERS_DOC_V1 = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_USER_FACING_OUTPUT_HELPERS_REVIEW_V1.md"
NEXT_LANE_V1 = "REVIEW_CONTROLLED_USER_FACING_OUTPUT_HELPERS_IMPLEMENTATION_V1"

ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1 = (
    "user_facing_output_metadata_label",
    "user_facing_output_policy_label",
    "output_arrangement_label",
    "source_metadata_label",
    "source_artifact_path_label",
    "source_review_path_label",
    "source_boundary_path_label",
    "validation_status_label",
    "blocked_status_boolean",
    "blocked_reason_label",
    "denied_authority_field_label",
    "no_output_policy_label",
    "no_reply_text_policy_label",
    "no_live_dialogue_policy_label",
    "no_runtime_policy_label",
    "no_chat_responder_policy_label",
    "no_provider_search_advisor_policy_label",
    "no_official_claim_policy_label",
    "safe_markdown_eligibility_label",
    "json_safe_eligibility_label",
    "visible_risk_label",
    "followup_label",
    "summary_label",
    "aggregate_label",
)

FORBIDDEN_INPUTS_CHECKED_V1 = (
    "raw_prompt_text",
    "raw_response_text",
    "real_user_content",
    "private_content",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "final_answer_prose",
    "answer_draft_text",
    "user_facing_reply_text",
    "live_dialogue_output",
    "sendable_message_text",
    "chat_responder_output",
    "respond_chat_output",
    "generate_chat_output",
    "dot_weslr_write_signal",
    "feature_flag_signal",
    "judges_scores",
    "official_claims",
    "authority_grants",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "answer_authority_granted",
    "user_facing_output_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "user_facing_output_executed",
    "user_facing_reply_created",
    "reply_text_created",
    "live_dialogue_output_created",
    "final_answer_generation_executed",
    "final_answer_generated",
    "final_answer_prose_created",
    "answer_draft_created",
    "answer_composition_executed",
    "answer_formation_executed",
    "runtime_wired",
    "chat_responder_called",
    "respond_chat_called",
    "generate_chat_called",
    "provider_call_made",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judges_created",
    "scores_created",
    "official_claim_made",
)

USER_FACING_OUTPUT_POLICY_LABELS_V1 = (
    "metadata_only_user_facing_output_arrangement",
    "internal_only_not_user_facing",
    "validation_before_rendering",
    "no_reply_text_policy",
    "no_live_dialogue_policy",
    "no_final_answer_generation_policy",
    "no_answer_draft_policy",
    "no_runtime_policy",
    "no_chat_responder_policy",
    "no_provider_search_advisor_policy",
    "no_official_claims_policy",
    "denied_authority_fields_must_remain_false",
)

OUTPUT_ARRANGEMENT_LABELS_V1 = (
    "source_paths_recorded",
    "safe_metadata_summarized",
    "blocked_inputs_reduced_to_safe_reason_labels",
    "safe_markdown_eligible_after_validation",
    "json_safe_eligible_after_validation",
)

NO_OUTPUT_POLICY_LABELS_V1 = (
    "no_user_facing_output_executed",
    "no_user_facing_reply_created",
    "no_reply_text_created",
    "no_live_dialogue_output_created",
    "no_final_answer_generated",
    "no_answer_draft_created",
)

VISIBLE_RISKS_V1 = (
    "helper-design-as-implementation-authority",
    "helper-metadata-as-user-facing-output-authority",
    "safe-metadata-as-reply-text",
    "safe-markdown-as-user-output",
    "validation-pass-as-answer-runtime-product-authority",
    "source-final-answer-artifact-as-answer-authority",
    "renderer-wording-drift",
    "reply-text-leak",
    "final-answer-prose-leak",
    "live-dialogue-output-leak",
    "runtime-wiring-drift",
    "provider-search-advisor-output-leak",
    "official-claim-or-scoring-drift",
)

FOLLOWUPS_V1 = (
    "review_controlled_user_facing_output_helpers_implementation_v1",
    "keep_user_facing_output_execution_separate",
    "keep_reply_text_creation_separate",
    "keep_final_answer_generation_separate",
    "keep_answer_drafts_separate",
    "keep_answer_composition_and_formation_separate",
    "keep_runtime_live_chat_integration_separate",
    "keep_official_evaluation_claims_separate",
)

_REQUIRED_TRUE_FIELDS = (
    "valid",
    "internal_only",
    "metadata_only",
    "helper_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "safe_markdown_eligible",
    "json_safe_eligible",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    "valid",
    "blocked",
    "validation_status",
    "internal_only",
    "metadata_only",
    "helper_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "source_controlled_final_answer_generation_artifact_path",
    "source_controlled_final_answer_generation_review_path",
    "source_user_facing_output_boundary_doc",
    "source_user_facing_output_boundary_review_doc",
    "allowed_metadata_input_labels",
    "forbidden_input_check_labels",
    "user_facing_output_policy_labels",
    "output_arrangement_labels",
    "source_metadata_summary",
    "user_facing_output_metadata_summary",
    "validation_summary",
    "blocked_reason_labels",
    "denied_authority_fields",
    "no_output_policy_labels",
    "safe_markdown_eligible",
    "json_safe_eligible",
    "visible_risks",
    "followups",
    "next_lane",
    *DENIED_AUTHORITY_FIELDS_V1,
)

_UNSAFE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "real_user",
    "private",
    "provider",
    "model_output",
    "search_output",
    "advisor",
    "runtime_output",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "final_answer",
    "answer_draft",
    "reply_text",
    "user_facing_reply",
    "live_dialogue",
    "sendable",
    "judge",
    "score",
    "benchmark",
    "iq",
    "turing",
    "certification",
    "product_readiness",
    "feature_flag",
    "authority_grant",
)

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "raw_prompt:", "raw_response:"),
    "real_user_content_detected": ("real user:", "user said:", "customer wrote:"),
    "private_content_detected": ("private content:", "confidential:", "secret:"),
    "provider_or_model_output_detected": ("provider output:", "model output:", "llm output:"),
    "search_or_advisor_output_detected": ("search output:", "advisor output:"),
    "runtime_output_detected": ("runtime output:", "chat responder output:"),
    "final_answer_detected": ("final answer:", "final response:", "final answer prose"),
    "answer_draft_detected": ("answer draft:", "draft answer:", "composed reply:"),
    "user_facing_reply_detected": ("user-facing reply:", "reply to user:", "send to user:"),
    "live_dialogue_detected": ("live dialogue:", "live chat output:"),
    "sendable_message_detected": ("sendable message:", "message to send:"),
    "chat_responder_signal_detected": ("chatresponder output:", "respond_chat output:", "generate_chat output:"),
    "dot_weslr_write_detected": (".weslr write:", "dot_weslr_write_performed=true"),
    "judge_or_score_detected": ("judge decision:", "official score:", "score: 100"),
    "official_claim_detected": ("official benchmark", "official iq", "passed the turing test", "certified product-ready", "product readiness"),
    "feature_flag_detected": ("enable feature flag", "feature_flag_enabled=true"),
    "authority_grant_detected": ("authority granted", "answer_authority_granted=true", "user_facing_output_authority_granted=true", "runtime_authority_granted=true"),
}

_SAFE_LABELS = set(ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1) | set(FORBIDDEN_INPUTS_CHECKED_V1) | set(DENIED_AUTHORITY_FIELDS_V1) | set(USER_FACING_OUTPUT_POLICY_LABELS_V1) | set(OUTPUT_ARRANGEMENT_LABELS_V1) | set(NO_OUTPUT_POLICY_LABELS_V1) | set(VISIBLE_RISKS_V1) | set(FOLLOWUPS_V1) | {
    ARTIFACT_TYPE_V1,
    INVALID_ARTIFACT_TYPE_V1,
    SCHEMA_VERSION_V1,
    SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_ARTIFACT_PATH_V1,
    SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_REVIEW_PATH_V1,
    SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_DOC_V1,
    SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_DOC_V1,
    SOURCE_HELPERS_DOC_V1,
    SOURCE_HELPERS_REVIEW_DOC_V1,
    NEXT_LANE_V1,
    "controlled_user_facing_output_metadata_v1",
    "controlled_user_facing_output_safe_metadata_only",
    "validation_pending_metadata_quality_only",
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "safe_markdown_after_validation",
    "json_safe_after_validation",
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
    elif isinstance(value, (list, tuple, set)):
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
        key_raw = path.rsplit(".", 1)[-1].split("[", 1)[0]
        key = key_raw.lower()
        if any(fragment in key for fragment in _UNSAFE_KEY_FRAGMENTS):
            if key_raw not in ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1 and key_raw not in _REQUIRED_FIELDS and key_raw not in DENIED_AUTHORITY_FIELDS_V1:
                if "draft" in key or "composed" in key:
                    found["answer_draft_detected"] = True
                elif "final_answer" in key:
                    found["final_answer_detected"] = True
                elif "reply" in key or "user_facing" in key:
                    found["user_facing_reply_detected"] = True
                elif "live_dialogue" in key:
                    found["live_dialogue_detected"] = True
                elif "sendable" in key:
                    found["sendable_message_detected"] = True
                elif "provider" in key or "model" in key:
                    found["provider_or_model_output_detected"] = True
                elif "search" in key or "advisor" in key:
                    found["search_or_advisor_output_detected"] = True
                elif "runtime" in key:
                    found["runtime_output_detected"] = True
                elif "chat_responder" in key or "respond_chat" in key or "generate_chat" in key:
                    found["chat_responder_signal_detected"] = True
                elif "private" in key:
                    found["private_content_detected"] = True
                elif "judge" in key or "score" in key:
                    found["judge_or_score_detected"] = True
                elif "feature_flag" in key:
                    found["feature_flag_detected"] = True
                elif "authority" in key:
                    found["authority_grant_detected"] = True
                else:
                    found["raw_content_detected"] = True
        if isinstance(item, str):
            if item in _SAFE_LABELS:
                continue
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    found[label] = True
    return found


def _unsafe_detection_labels(value: Mapping[str, Any]) -> list[str]:
    return [label for label in _TEXT_MARKERS if value.get(label) is True]


def _source_metadata_summary() -> dict[str, Any]:
    return {
        "source_controlled_final_answer_generation_artifact_path": SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_ARTIFACT_PATH_V1,
        "source_controlled_final_answer_generation_review_path": SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_REVIEW_PATH_V1,
        "source_user_facing_output_boundary_doc": SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_DOC_V1,
        "source_user_facing_output_boundary_review_doc": SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_DOC_V1,
        "source_helpers_doc": SOURCE_HELPERS_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
    }


def _summarize_safe_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"present": False, "mapping": False, "safe_label_keys": [], "key_count": 0}
    safe_keys = [str(key) for key in sorted(value.keys(), key=str) if str(key) in ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1]
    return {"present": True, "mapping": True, "safe_label_keys": safe_keys, "key_count": len(value)}


def _blocked_reason_labels_for_input(user_facing_output_metadata: Mapping[str, Any] | None) -> list[str]:
    if user_facing_output_metadata is None:
        return []
    if not isinstance(user_facing_output_metadata, Mapping):
        return ["user_facing_output_metadata_not_mapping"]
    reasons: list[str] = []
    for label in _unsafe_detection_labels(_detect_unsafe_content(user_facing_output_metadata)):
        _append_unique(reasons, label)
    for key, value in user_facing_output_metadata.items():
        key_s = str(key)
        if key_s in DENIED_AUTHORITY_FIELDS_V1:
            if value is not False:
                _append_unique(reasons, f"authority_field_not_false:{key_s}")
            continue
        if key_s not in ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1:
            _append_unique(reasons, f"unsupported_user_facing_output_metadata_input:{key_s}")
    return reasons


def _base_artifact() -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "validation_status": "validation_pending_metadata_quality_only",
        "internal_only": True,
        "metadata_only": True,
        "helper_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "source_controlled_final_answer_generation_artifact_path": SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_ARTIFACT_PATH_V1,
        "source_controlled_final_answer_generation_review_path": SOURCE_CONTROLLED_FINAL_ANSWER_GENERATION_REVIEW_PATH_V1,
        "source_user_facing_output_boundary_doc": SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_DOC_V1,
        "source_user_facing_output_boundary_review_doc": SOURCE_CONTROLLED_USER_FACING_OUTPUT_BOUNDARY_REVIEW_DOC_V1,
        "allowed_metadata_input_labels": list(ALLOWED_USER_FACING_OUTPUT_METADATA_INPUTS_V1),
        "forbidden_input_check_labels": list(FORBIDDEN_INPUTS_CHECKED_V1),
        "user_facing_output_policy_labels": list(USER_FACING_OUTPUT_POLICY_LABELS_V1),
        "output_arrangement_labels": list(OUTPUT_ARRANGEMENT_LABELS_V1),
        "source_metadata_summary": _source_metadata_summary(),
        "user_facing_output_metadata_summary": {"present": False, "mapping": False, "safe_label_keys": [], "key_count": 0},
        "validation_summary": {
            "validation_status_label": "validation_pending_metadata_quality_only",
            "validation_before_rendering": True,
            "unsafe_content_not_copied": True,
        },
        "blocked_reason_labels": [],
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "no_output_policy_labels": list(NO_OUTPUT_POLICY_LABELS_V1),
        "safe_markdown_eligible": True,
        "json_safe_eligible": True,
        "visible_risks": list(VISIBLE_RISKS_V1),
        "followups": list(FOLLOWUPS_V1),
        "next_lane": NEXT_LANE_V1,
    }
    for field in DENIED_AUTHORITY_FIELDS_V1:
        artifact[field] = False
    return artifact


def _safe_blocked_artifact(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    artifact = _base_artifact()
    artifact["artifact_type"] = INVALID_ARTIFACT_TYPE_V1
    artifact["valid"] = False
    artifact["blocked"] = True
    artifact["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
    artifact["safe_markdown_eligible"] = False
    artifact["json_safe_eligible"] = True
    artifact["source_metadata_summary"] = {"source_labels_present": True, "unsafe_content_not_copied": True}
    artifact["user_facing_output_metadata_summary"] = {"unsafe_content_not_copied": True, "safe_label_keys": []}
    artifact["validation_summary"] = {
        "validation_status_label": "blocked_invalid_or_unsafe_metadata_labels_only",
        "validation_before_rendering": True,
        "unsafe_content_not_copied": True,
    }
    artifact["blocked_reason_labels"] = _safe_error_labels(_as_list(reason_labels)) or ["invalid_or_unsafe_user_facing_output_metadata"]
    return artifact


def build_controlled_user_facing_output_artifact_v1(
    user_facing_output_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one safe in-memory controlled user-facing-output metadata artifact."""

    reasons = _blocked_reason_labels_for_input(user_facing_output_metadata)
    if reasons:
        return _safe_blocked_artifact(reasons)
    artifact = _base_artifact()
    artifact["validation_status"] = "validation_pass_metadata_quality_only"
    artifact["user_facing_output_metadata_summary"] = _summarize_safe_metadata(user_facing_output_metadata or {})
    artifact["validation_summary"] = {
        "validation_status_label": "validation_pass_metadata_quality_only",
        "validation_before_rendering": True,
        "unsafe_content_not_copied": True,
    }
    return artifact


def _derive_validation_errors(artifact: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
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
    denied = artifact.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        errors.append("denied_authority_fields_not_mapping")
    for field in DENIED_AUTHORITY_FIELDS_V1:
        if artifact.get(field) is not False:
            errors.append(f"authority_field_not_false:{field}")
        if not isinstance(denied, Mapping) or denied.get(field) is not False:
            errors.append(f"denied_authority_field_not_false:{field}")
    if artifact.get("blocked") is not False:
        errors.append("artifact_blocked")
    for label in _unsafe_detection_labels(_detect_unsafe_content(artifact)):
        errors.append(f"unsafe_content_detected:{label}")
    return list(dict.fromkeys(errors))


def validate_controlled_user_facing_output_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one controlled user-facing-output metadata artifact."""

    if not isinstance(artifact, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "errors": ["artifact_not_mapping"],
            "safe_to_render": False,
            "authority_fields_false": False,
            "json_safe": False,
            "safe_markdown": False,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
        }
    errors = _derive_validation_errors(artifact)
    denied = artifact.get("denied_authority_fields")
    authority_fields_false = isinstance(denied, Mapping) and all(
        artifact.get(field) is False and denied.get(field) is False for field in DENIED_AUTHORITY_FIELDS_V1
    )
    valid = not errors
    return {
        "valid": valid,
        "blocked": not valid,
        "errors": errors,
        "artifact_type": artifact.get("artifact_type"),
        "metadata_only": artifact.get("metadata_only") is True,
        "internal_only": artifact.get("internal_only") is True,
        "helper_only": artifact.get("helper_only") is True,
        "non_runtime": artifact.get("non_runtime") is True,
        "non_user_facing": artifact.get("non_user_facing") is True,
        "authority_fields_false": authority_fields_false,
        "safe_to_render": valid and artifact.get("safe_markdown_eligible") is True,
        "json_safe": valid,
        "safe_markdown": valid,
        "validation_status": "validation_pass_metadata_quality_only" if valid else "blocked_invalid_or_unsafe_metadata_labels_only",
    }


def summarize_controlled_user_facing_output_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact safe summary for one user-facing-output metadata artifact."""

    validation = validate_controlled_user_facing_output_artifact_v1(artifact)
    return {
        "artifact_type": artifact.get("artifact_type") if isinstance(artifact, Mapping) else None,
        "schema_version": artifact.get("schema_version") if isinstance(artifact, Mapping) else None,
        "valid": validation.get("valid") is True,
        "blocked": validation.get("blocked") is True,
        "validation_status": validation.get("validation_status"),
        "metadata_only": bool(isinstance(artifact, Mapping) and artifact.get("metadata_only") is True),
        "internal_only": bool(isinstance(artifact, Mapping) and artifact.get("internal_only") is True),
        "helper_only": bool(isinstance(artifact, Mapping) and artifact.get("helper_only") is True),
        "non_runtime": bool(isinstance(artifact, Mapping) and artifact.get("non_runtime") is True),
        "non_user_facing": bool(isinstance(artifact, Mapping) and artifact.get("non_user_facing") is True),
        "blocked_reason_labels": _safe_error_labels(_as_list(artifact.get("blocked_reason_labels") if isinstance(artifact, Mapping) else [])),
        "source_metadata_summary": _json_safe(artifact.get("source_metadata_summary") if isinstance(artifact, Mapping) else {}),
        "user_facing_output_policy_labels": _json_safe(artifact.get("user_facing_output_policy_labels") if isinstance(artifact, Mapping) else []),
        "output_arrangement_labels": _json_safe(artifact.get("output_arrangement_labels") if isinstance(artifact, Mapping) else []),
        "denied_authority_fields_false": validation.get("authority_fields_false") is True,
        "visible_risks": _json_safe(artifact.get("visible_risks") if isinstance(artifact, Mapping) else []),
        "followups": _json_safe(artifact.get("followups") if isinstance(artifact, Mapping) else []),
        "next_lane": artifact.get("next_lane") if isinstance(artifact, Mapping) else NEXT_LANE_V1,
    }


def _blocked_markdown(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reasons = _safe_error_labels(_as_list(summary.get("blocked_reason_labels")) + _as_list(validation.get("errors")))
    lines = [
        "# WESLR Controlled User-Facing Output Helper Artifact V1",
        "",
        "- artifact_type: `controlled_user_facing_output_artifact_v1_invalid`",
        "- valid: `False`",
        "- blocked: `True`",
        "- unsafe_content_not_copied: `True`",
        "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
        "",
        "## Blocked Reason Labels",
    ]
    lines.extend(f"- `{reason}`" for reason in (reasons or ["invalid_or_unsafe_user_facing_output_metadata"]))
    lines.extend([
        "",
        "## Safety Boundary",
        "- `no_user_facing_output_executed`",
        "- `no_user_facing_reply_created`",
        "- `no_reply_text_created`",
        "- `no_live_dialogue_output_created`",
        "- `no_final_answer_generated`",
        "- `no_answer_draft_created`",
        "- `runtime_not_wired`",
        "- `provider_search_advisor_not_called`",
        "- `no_official_claim_made`",
        f"- next_lane: `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_controlled_user_facing_output_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown only after validation; invalid input renders labels only."""

    validation = validate_controlled_user_facing_output_artifact_v1(artifact)
    summary = summarize_controlled_user_facing_output_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _blocked_markdown(validation, summary)
    lines = [
        "# WESLR Controlled User-Facing Output Helper Artifact V1",
        "",
        "## Artifact Status",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- validation_status: `{summary['validation_status']}`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "- helper_only: `True`",
        "- non_runtime: `True`",
        "- non_user_facing: `True`",
        "",
        "## Source Metadata Summary",
    ]
    for key, value in summary["source_metadata_summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Output Policy Labels"])
    lines.extend(f"- `{label}`" for label in summary["user_facing_output_policy_labels"])
    lines.extend(["", "## Output Arrangement Labels"])
    lines.extend(f"- `{label}`" for label in summary["output_arrangement_labels"])
    lines.extend(["", "## No-Output Policies"])
    lines.extend(f"- `{label}`" for label in NO_OUTPUT_POLICY_LABELS_V1)
    lines.extend([
        "- `runtime_not_wired`",
        "- `provider_search_advisor_not_called`",
        "- `no_official_claim_made`",
    ])
    lines.extend(["", "## Denied Authority Fields"])
    lines.extend(f"- `{field}=false`" for field in DENIED_AUTHORITY_FIELDS_V1)
    lines.extend(["", "## Visible Risks"])
    lines.extend(f"- `{risk}`" for risk in summary["visible_risks"])
    lines.extend(["", "## Followups"])
    lines.extend(f"- `{followup}`" for followup in summary["followups"])
    lines.extend(["", "## Next Lane", f"- `{summary['next_lane']}`"])
    return "\n".join(lines) + "\n"


def to_controlled_user_facing_output_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe artifact metadata or a safe invalid wrapper."""

    validation = validate_controlled_user_facing_output_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _safe_blocked_artifact(_as_list(validation.get("errors")) or _as_list(artifact.get("blocked_reason_labels") if isinstance(artifact, Mapping) else []))
    return _json_safe(artifact)
