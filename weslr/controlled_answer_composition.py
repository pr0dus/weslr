"""WESLR controlled answer composition helpers V1.

Helper-only, metadata-only, internal-only, deterministic, in-memory helpers for
controlled answer composition metadata artifacts. This module arranges safe
metadata labels only. It does not execute answer formation or answer
composition, generate final-answer prose, create answer drafts, create
user-facing output, wire runtime behavior, call chat/runtime/provider/search/
advisor paths, write files or .weslr state, enable feature flags, create judges
or scores, make official claims, or grant answer/composition/runtime/official
evaluation authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARTIFACT_TYPE_V1 = "controlled_answer_composition_artifact_v1"
INVALID_ARTIFACT_TYPE_V1 = "controlled_answer_composition_artifact_v1_invalid"
SCHEMA_VERSION_V1 = "controlled_answer_composition_artifact_schema_v1"

SOURCE_CONTROLLED_ANSWER_FORMATION_ARTIFACT_PATH_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_V1.md"
SOURCE_CONTROLLED_ANSWER_FORMATION_REVIEW_PATH_V1 = "docs/WESLR_CONTROLLED_ANSWER_FORMATION_EXECUTION_RESULT_ARTIFACT_REVIEW_V1.md"
SOURCE_COMPOSITION_BOUNDARY_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_V1.md"
SOURCE_COMPOSITION_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_BOUNDARY_REVIEW_V1.md"
SOURCE_HELPERS_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_HELPERS_REVIEW_V1.md"
NEXT_LANE_V1 = "REVIEW_CONTROLLED_ANSWER_COMPOSITION_HELPERS_IMPLEMENTATION_V1"

ALLOWED_COMPOSITION_METADATA_INPUTS_V1 = (
    "composition_metadata_label",
    "composition_policy_label",
    "composition_arrangement_label",
    "source_metadata_label",
    "source_artifact_path_label",
    "source_review_path_label",
    "source_boundary_path_label",
    "validation_status_label",
    "blocked_status_boolean",
    "blocked_reason_label",
    "denied_authority_field_label",
    "no_final_answer_policy_label",
    "no_user_facing_output_policy_label",
    "no_runtime_policy_label",
    "no_provider_search_advisor_policy_label",
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
    "provider_model_search_advisor_output",
    "runtime_output",
    "chat_responder_handles_or_output",
    "answer_drafts",
    "composed_replies",
    "final_answer_prose",
    "user_facing_answer_text",
    "judges_scores",
    "benchmark_iq_turing_certification_product_readiness_claims",
    "feature_flag_payloads",
    "authority_grants",
)

DENIED_AUTHORITY_FIELDS_V1 = (
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "answer_formation_executed",
    "answer_composition_executed",
    "composition_execution_authorized",
    "final_answer_generated",
    "answer_draft_created",
    "user_facing_output_created",
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

COMPOSITION_POLICY_LABELS_V1 = (
    "metadata_only_composition_arrangement",
    "internal_only_not_user_facing",
    "validation_before_rendering",
    "no_final_answer_policy",
    "no_user_facing_output_policy",
    "no_runtime_policy",
    "no_provider_search_advisor_policy",
    "denied_authority_fields_must_remain_false",
)

COMPOSITION_ARRANGEMENT_LABELS_V1 = (
    "source_paths_recorded",
    "safe_metadata_summarized",
    "blocked_inputs_reduced_to_safe_reason_labels",
    "safe_markdown_eligible_after_validation",
    "json_safe_eligible_after_validation",
)

VISIBLE_RISKS_V1 = (
    "composition-helper-as-composition-execution",
    "composition-metadata-as-answer-draft",
    "source-artifact-as-answer-authority",
    "validation-pass-as-composition-authority",
    "renderer-wording-drift",
    "final-answer-prose-leak",
    "user-facing-output-leak",
    "runtime-wiring-drift",
    "provider-search-advisor-output-leak",
    "official-claim-or-scoring-drift",
)

FOLLOWUPS_V1 = (
    "review_controlled_answer_composition_helpers_implementation_v1",
    "keep_composition_execution_separate",
    "keep_final_answer_generation_separate",
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
    "internal_only",
    "metadata_only",
    "helper_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "source_controlled_answer_formation_artifact_path",
    "source_controlled_answer_formation_review_path",
    "source_composition_boundary_doc",
    "source_composition_boundary_review_doc",
    "allowed_composition_metadata_inputs",
    "forbidden_inputs_checked",
    "composition_policy_labels",
    "composition_arrangement_labels",
    "source_metadata_summary",
    "validation_summary",
    "blocked_reason_labels",
    "denied_authority_fields",
    "no_final_answer_policy",
    "no_user_facing_output_policy",
    "no_runtime_policy",
    "no_provider_search_advisor_policy",
    "safe_markdown_eligible",
    "json_safe_eligible",
    "visible_risks",
    "followups",
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
    "answer_draft",
    "composed_reply",
    "final_answer",
    "user_facing",
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
    "answer_draft_detected": ("answer draft:", "draft answer:", "composed reply:"),
    "final_answer_detected": ("final answer:", "final response:", "final answer prose"),
    "user_facing_output_detected": ("user-facing answer:", "send to user:", "reply to user:"),
    "judge_or_score_detected": ("judge decision:", "official score:", "score: 100"),
    "official_claim_detected": ("official benchmark", "official iq", "passed the turing test", "certified product-ready", "product readiness"),
    "feature_flag_detected": ("enable feature flag", "feature_flag_enabled=true"),
    "authority_grant_detected": ("authority granted", "answer_authority_granted=true", "composition_authority_granted=true", "runtime_authority_granted=true"),
}

_SAFE_LABELS = set(ALLOWED_COMPOSITION_METADATA_INPUTS_V1) | set(FORBIDDEN_INPUTS_CHECKED_V1) | set(DENIED_AUTHORITY_FIELDS_V1) | set(COMPOSITION_POLICY_LABELS_V1) | set(COMPOSITION_ARRANGEMENT_LABELS_V1) | set(VISIBLE_RISKS_V1) | set(FOLLOWUPS_V1) | {
    ARTIFACT_TYPE_V1,
    INVALID_ARTIFACT_TYPE_V1,
    SCHEMA_VERSION_V1,
    SOURCE_CONTROLLED_ANSWER_FORMATION_ARTIFACT_PATH_V1,
    SOURCE_CONTROLLED_ANSWER_FORMATION_REVIEW_PATH_V1,
    SOURCE_COMPOSITION_BOUNDARY_DOC_V1,
    SOURCE_COMPOSITION_BOUNDARY_REVIEW_DOC_V1,
    SOURCE_HELPERS_DOC_V1,
    SOURCE_HELPERS_REVIEW_DOC_V1,
    NEXT_LANE_V1,
    "controlled_answer_composition_metadata_v1",
    "controlled_answer_composition_safe_metadata_only",
    "validation_pending_metadata_quality_only",
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "no_final_answer_generated",
    "no_user_facing_output_created",
    "runtime_not_wired",
    "provider_search_advisor_not_called",
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
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if any(fragment in key for fragment in _UNSAFE_KEY_FRAGMENTS):
            if key not in _REQUIRED_FIELDS and key not in DENIED_AUTHORITY_FIELDS_V1:
                if "draft" in key or "composed" in key:
                    found["answer_draft_detected"] = True
                elif "final_answer" in key:
                    found["final_answer_detected"] = True
                elif "user_facing" in key:
                    found["user_facing_output_detected"] = True
                elif "provider" in key or "model" in key:
                    found["provider_or_model_output_detected"] = True
                elif "search" in key or "advisor" in key:
                    found["search_or_advisor_output_detected"] = True
                elif "runtime" in key or "chat_responder" in key:
                    found["runtime_output_detected"] = True
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
        "source_controlled_answer_formation_artifact_path": SOURCE_CONTROLLED_ANSWER_FORMATION_ARTIFACT_PATH_V1,
        "source_controlled_answer_formation_review_path": SOURCE_CONTROLLED_ANSWER_FORMATION_REVIEW_PATH_V1,
        "source_composition_boundary_doc": SOURCE_COMPOSITION_BOUNDARY_DOC_V1,
        "source_composition_boundary_review_doc": SOURCE_COMPOSITION_BOUNDARY_REVIEW_DOC_V1,
        "source_helpers_doc": SOURCE_HELPERS_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
    }


def _summarize_safe_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"present": False, "mapping": False, "safe_label_keys": [], "key_count": 0}
    safe_keys = [str(key) for key in sorted(value.keys(), key=str) if str(key) in ALLOWED_COMPOSITION_METADATA_INPUTS_V1]
    return {"present": True, "mapping": True, "safe_label_keys": safe_keys, "key_count": len(value)}


def _blocked_reason_labels_for_input(composition_metadata: Mapping[str, Any] | None) -> list[str]:
    if composition_metadata is None:
        return []
    if not isinstance(composition_metadata, Mapping):
        return ["composition_metadata_not_mapping"]
    reasons: list[str] = []
    for label in _unsafe_detection_labels(_detect_unsafe_content(composition_metadata)):
        _append_unique(reasons, label)
    for key, value in composition_metadata.items():
        key_s = str(key)
        if key_s in DENIED_AUTHORITY_FIELDS_V1:
            if value is not False:
                _append_unique(reasons, f"authority_field_not_false:{key_s}")
            continue
        if key_s not in ALLOWED_COMPOSITION_METADATA_INPUTS_V1:
            _append_unique(reasons, f"unsupported_composition_metadata_input:{key_s}")
    return reasons


def _base_artifact() -> dict[str, Any]:
    source_summary = _source_metadata_summary()
    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "valid": True,
        "blocked": False,
        "internal_only": True,
        "metadata_only": True,
        "helper_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "source_controlled_answer_formation_artifact_path": SOURCE_CONTROLLED_ANSWER_FORMATION_ARTIFACT_PATH_V1,
        "source_controlled_answer_formation_review_path": SOURCE_CONTROLLED_ANSWER_FORMATION_REVIEW_PATH_V1,
        "source_composition_boundary_doc": SOURCE_COMPOSITION_BOUNDARY_DOC_V1,
        "source_composition_boundary_review_doc": SOURCE_COMPOSITION_BOUNDARY_REVIEW_DOC_V1,
        "allowed_composition_metadata_inputs": list(ALLOWED_COMPOSITION_METADATA_INPUTS_V1),
        "forbidden_inputs_checked": list(FORBIDDEN_INPUTS_CHECKED_V1),
        "composition_policy_labels": list(COMPOSITION_POLICY_LABELS_V1),
        "composition_arrangement_labels": list(COMPOSITION_ARRANGEMENT_LABELS_V1),
        "source_metadata_summary": source_summary,
        "validation_summary": {
            "validation_status_label": "validation_pending_metadata_quality_only",
            "validation_before_rendering": True,
            "unsafe_content_not_copied": True,
        },
        "blocked_reason_labels": [],
        "denied_authority_fields": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        "no_final_answer_policy": "no_final_answer_generated",
        "no_user_facing_output_policy": "no_user_facing_output_created",
        "no_runtime_policy": "runtime_not_wired",
        "no_provider_search_advisor_policy": "provider_search_advisor_not_called",
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
    artifact["safe_markdown_eligible"] = False
    artifact["json_safe_eligible"] = True
    artifact["source_metadata_summary"] = {"source_labels_present": True, "unsafe_content_not_copied": True}
    artifact["validation_summary"] = {
        "validation_status_label": "blocked_invalid_or_unsafe_metadata_labels_only",
        "validation_before_rendering": True,
        "unsafe_content_not_copied": True,
    }
    artifact["blocked_reason_labels"] = _safe_error_labels(_as_list(reason_labels)) or ["invalid_or_unsafe_composition_metadata"]
    return artifact


def build_controlled_answer_composition_artifact_v1(
    composition_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one safe in-memory controlled answer composition metadata artifact."""

    reasons = _blocked_reason_labels_for_input(composition_metadata)
    if reasons:
        return _safe_blocked_artifact(reasons)
    artifact = _base_artifact()
    artifact["composition_metadata_summary"] = _summarize_safe_metadata(composition_metadata or {})
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


def validate_controlled_answer_composition_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one controlled answer composition metadata artifact."""

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


def summarize_controlled_answer_composition_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact safe summary for one composition metadata artifact."""

    validation = validate_controlled_answer_composition_artifact_v1(artifact)
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
        "composition_policy_labels": _json_safe(artifact.get("composition_policy_labels") if isinstance(artifact, Mapping) else []),
        "composition_arrangement_labels": _json_safe(artifact.get("composition_arrangement_labels") if isinstance(artifact, Mapping) else []),
        "denied_authority_fields_false": validation.get("authority_fields_false") is True,
        "visible_risks": _json_safe(artifact.get("visible_risks") if isinstance(artifact, Mapping) else []),
        "followups": _json_safe(artifact.get("followups") if isinstance(artifact, Mapping) else []),
        "next_lane": artifact.get("next_lane") if isinstance(artifact, Mapping) else NEXT_LANE_V1,
    }


def _blocked_markdown(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reasons = _safe_error_labels(_as_list(summary.get("blocked_reason_labels")) + _as_list(validation.get("errors")))
    lines = [
        "# WESLR Controlled Answer Composition Helper Artifact V1",
        "",
        "- artifact_type: `controlled_answer_composition_artifact_v1_invalid`",
        "- valid: `False`",
        "- blocked: `True`",
        "- unsafe_content_not_copied: `True`",
        "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
        "",
        "## Blocked Reason Labels",
    ]
    lines.extend(f"- `{reason}`" for reason in (reasons or ["invalid_or_unsafe_composition_metadata"]))
    lines.extend([
        "",
        "## Safety Boundary",
        "- `no_answer_composition_executed`",
        "- `no_final_answer_generated`",
        "- `no_answer_draft_created`",
        "- `no_user_facing_output_created`",
        "- `runtime_not_wired`",
        "- `provider_search_advisor_not_called`",
        "- `no_official_claim_made`",
        f"- next_lane: `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_controlled_answer_composition_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown only after validation; invalid input renders labels only."""

    validation = validate_controlled_answer_composition_artifact_v1(artifact)
    summary = summarize_controlled_answer_composition_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _blocked_markdown(validation, summary)
    lines = [
        "# WESLR Controlled Answer Composition Helper Artifact V1",
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
    lines.extend(["", "## Composition Policy Labels"])
    lines.extend(f"- `{label}`" for label in summary["composition_policy_labels"])
    lines.extend(["", "## Composition Arrangement Labels"])
    lines.extend(f"- `{label}`" for label in summary["composition_arrangement_labels"])
    lines.extend(["", "## No-Output Policies"])
    lines.extend([
        "- `no_final_answer_generated`",
        "- `no_user_facing_output_created`",
        "- `runtime_not_wired`",
        "- `provider_search_advisor_not_called`",
    ])
    lines.extend(["", "## Denied Authority Fields"])
    lines.extend(f"- `{field}=false`" for field in DENIED_AUTHORITY_FIELDS_V1)
    lines.extend(["", "## Visible Risks"])
    lines.extend(f"- `{risk}`" for risk in summary["visible_risks"])
    lines.extend(["", "## Followups"])
    lines.extend(f"- `{followup}`" for followup in summary["followups"])
    lines.extend(["", "## Next Lane", f"- `{summary['next_lane']}`"])
    return "\n".join(lines) + "\n"


def to_controlled_answer_composition_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return JSON-safe artifact metadata or a safe invalid wrapper."""

    validation = validate_controlled_answer_composition_artifact_v1(artifact)
    if validation.get("valid") is not True:
        return _safe_blocked_artifact(_as_list(validation.get("errors")) or _as_list(artifact.get("blocked_reason_labels") if isinstance(artifact, Mapping) else []))
    return _json_safe(artifact)
