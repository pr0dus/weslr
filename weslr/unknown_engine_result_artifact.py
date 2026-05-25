"""WESLR UNKNOWN ENGINE result artifact metadata helpers V1.

Helper-only, metadata-only, deterministic, in-memory helpers for internal
UNKNOWN ENGINE result artifact metadata. This module does not execute UNKNOWN
ENGINE, CognitiveGymRun, Cognitive Gym, runtime behavior, providers, models,
search, advisors, ChatResponder/respond_chat/generate_chat, .weslr IO, feature
flags, judges/scores, official claims, prediction output, reply output,
preview output, final-answer prose, answer drafts, user-facing output, result
artifact file creation, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

from weslr.cognitive_gym_run_protocol import REQUIRED_DENIED_AUTHORITY_FIELDS
from weslr.unknown_engine import (
    UNKNOWN_ENGINE_NAME_V1,
    summarize_unknown_engine_run_v1,
    to_unknown_engine_run_json_safe_v1,
    validate_unknown_engine_run_v1,
)

ARTIFACT_NAME_V1 = "unknown_engine_result_artifact_v1"
ARTIFACT_SCHEMA_VERSION_V1 = "unknown_engine_result_artifact_schema_v1"
SOURCE_HELPER_MODULE_V1 = "weslr/unknown_engine.py"
RESULT_ARTIFACT_HELPER_MODULE_V1 = "weslr/unknown_engine_result_artifact.py"
NEXT_LANE_V1 = "REVIEW_UNKNOWN_ENGINE_RESULT_ARTIFACT_HELPERS_IMPLEMENTATION_V1"

_ALLOWED_ARTIFACT_FIELDS = (
    "artifact_name",
    "artifact_schema_version",
    "source_engine_name",
    "source_helper_module",
    "source_protocol_name",
    "source_validation_status",
    "source_blocked",
    "source_blocked_reason_labels",
    "knowns_summary",
    "unknowns_summary",
    "uncertainty_summary",
    "possible_branch_label_summary",
    "missing_evidence_summary",
    "falsification_summary",
    "safe_next_observation_summary",
    "evidence_change_summary",
    "risk_boundary_summary",
    "compressed_lesson_summary",
    "denied_authority_summary",
    "visible_risks",
    "followups",
    "next_lane",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
)

_LIST_ARTIFACT_FIELDS = (
    "source_blocked_reason_labels",
    "knowns_summary",
    "unknowns_summary",
    "possible_branch_label_summary",
    "missing_evidence_summary",
    "falsification_summary",
    "safe_next_observation_summary",
    "evidence_change_summary",
    "risk_boundary_summary",
    "visible_risks",
    "followups",
    "blocked_reason_labels",
)

_FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "private",
    "provider",
    "model",
    "search",
    "advisor",
    "runtime",
    "live_dialogue",
    "reply_output",
    "preview_output",
    "sendable_reply",
    "actual_reply_body",
    "user_facing",
    "final_answer",
    "answer_draft",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "dot_weslr",
    ".weslr",
    "feature_flag",
    "judge",
    "score",
    "official_claim",
    "benchmark",
    "iq_claim",
    "turing",
    "certification",
    "product_readiness",
    "open_problem_solution",
    "future_certainty",
    "prediction_authority",
    "authority_granted",
)

_TEXT_MARKERS = {
    "raw_prompt_indicator_blocked": ("raw prompt:", "raw_prompt:", "system prompt:", "developer prompt:"),
    "raw_response_indicator_blocked": ("raw response:", "raw_response:", "assistant raw:"),
    "private_content_indicator_blocked": ("private content:", "confidential:", "secret:", "api key", "password:"),
    "runtime_output_indicator_blocked": ("runtime output:", "runtime trace:", "live runtime output:"),
    "reply_output_indicator_blocked": ("reply output:", "reply_output:", "sendable reply text:", "actual reply body:"),
    "preview_output_indicator_blocked": ("preview output:", "preview_output:", "reply preview:"),
    "user_facing_output_indicator_blocked": ("user-facing output:", "user facing output:", "user-facing answer:"),
    "final_answer_prose_indicator_blocked": ("final-answer prose", "final answer prose", "final answer:", "final_answer:"),
    "answer_draft_indicator_blocked": ("answer draft:", "answer_draft:", "draft answer:"),
    "prediction_output_indicator_blocked": ("prediction output:", "prediction_output:"),
    "future_certainty_claim_blocked": ("future certainty", "guaranteed future", "certain future", "prophecy", "oracle"),
    "open_problem_solution_claim_blocked": ("open-problem solution", "open problem solution", "erdős solved", "erdos solved", "millennium solved", "solved the open problem"),
    "provider_model_search_advisor_indicator_blocked": (
        "provider output:",
        "provider response:",
        "model output:",
        "llm output:",
        "search output:",
        "search result:",
        "advisor output:",
        "advisor response:",
    ),
    "chat_responder_indicator_blocked": ("chatresponder", "chat responder", "respond_chat", "generate_chat"),
    "dot_weslr_io_indicator_blocked": (".weslr read", ".weslr write", "dot_weslr_read", "dot_weslr_write"),
    "feature_flag_indicator_blocked": ("feature_flag_enabled=true", "enable feature flag"),
    "judges_scores_indicator_blocked": ("judge decision:", "official score:", "score: 100", "judges created"),
    "official_claim_indicator_blocked": ("official benchmark", "official iq", "passed the turing test", "certified product-ready", "product readiness"),
    "authority_grant_indicator_blocked": ("authority granted", "authority_granted=true"),
}

_ALLOWED_INTERNAL_STRINGS = {
    ARTIFACT_NAME_V1,
    ARTIFACT_SCHEMA_VERSION_V1,
    SOURCE_HELPER_MODULE_V1,
    RESULT_ARTIFACT_HELPER_MODULE_V1,
    NEXT_LANE_V1,
    UNKNOWN_ENGINE_NAME_V1,
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "metadata_only_no_runtime_no_output_no_authority",
    "no_correction_metadata_only",
    "not_revealed_metadata_only",
    "unknown_engine_compressed_lesson_metadata_only",
    "unknown_engine_uncertainty_metadata_only",
    "qualitative_confidence_not_scored_metadata_only",
    *_ALLOWED_ARTIFACT_FIELDS,
    *REQUIRED_DENIED_AUTHORITY_FIELDS,
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


def _safe_label(value: Any) -> str:
    return str(value).replace("`", "").replace("\n", " ")[:180]


def _safe_labels(value: Any) -> list[str]:
    labels: list[str] = []
    for item in _as_list(value):
        _append_unique(labels, _safe_label(item))
    return labels


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    return False


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "non_json_safe_float_replaced"
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return "non_json_safe_value_replaced"


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


def _is_safe_denied_authority_path(path: str, value: Any) -> bool:
    parts = path.split(".")
    return (
        len(parts) >= 2
        and parts[-2] in {"denied_authority_summary", "denied_authority_fields"}
        and parts[-1] in REQUIRED_DENIED_AUTHORITY_FIELDS
        and value is False
    )


def _detect_unsafe_content(value: Any) -> list[str]:
    reasons: list[str] = []
    if not _is_json_safe(value):
        _append_unique(reasons, "non_json_safe_input_blocked")
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if _is_safe_denied_authority_path(path, item):
            continue
        if path.startswith("boundary_status.") and isinstance(item, (bool, list)):
            continue
        if key not in {*(field.lower() for field in _ALLOWED_ARTIFACT_FIELDS), *(field.lower() for field in REQUIRED_DENIED_AUTHORITY_FIELDS)}:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    _append_unique(reasons, f"unsupported_indicator_blocked:{fragment}")
        if isinstance(item, str):
            lowered = item.lower()
            if item in _ALLOWED_INTERNAL_STRINGS or item in REQUIRED_DENIED_AUTHORITY_FIELDS:
                continue
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
    return reasons


def _source_unknown_engine_metadata(source: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = source.get("engine_specific_metadata")
    if isinstance(metadata, Mapping):
        unknown_engine = metadata.get("unknown_engine_metadata")
        if isinstance(unknown_engine, Mapping):
            return unknown_engine
    return {}


def _denied_authority_summary(source: Mapping[str, Any]) -> dict[str, bool]:
    return {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS}


def _source_denied_violations(source: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    denied = source.get("denied_authority_fields")
    if not isinstance(denied, Mapping):
        return ["denied_authority_fields_not_mapping"]
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            _append_unique(reasons, f"missing_denied_authority_field:{field}")
        elif denied.get(field) is not False:
            _append_unique(reasons, f"denied_authority_field_not_false:{field}")
    return reasons


def _artifact_validation_status(blocked: bool) -> str:
    return "blocked_invalid_or_unsafe_metadata_labels_only" if blocked else "validation_pass_metadata_quality_only"


def _blocked_artifact(source: Mapping[str, Any] | None, reason_labels: list[str]) -> dict[str, Any]:
    safe_source = source if isinstance(source, Mapping) else {}
    reasons = _safe_labels(reason_labels or ["invalid_unknown_engine_result_artifact_source"])
    return _json_safe(
        {
            "artifact_name": ARTIFACT_NAME_V1,
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION_V1,
            "source_engine_name": safe_source.get("engine_name", UNKNOWN_ENGINE_NAME_V1),
            "source_helper_module": SOURCE_HELPER_MODULE_V1,
            "source_protocol_name": safe_source.get("protocol_name"),
            "source_validation_status": safe_source.get("validation_status", "blocked_invalid_or_unsafe_metadata_labels_only"),
            "source_blocked": True,
            "source_blocked_reason_labels": _safe_labels(safe_source.get("blocked_reason_labels", []) + reasons),
            "knowns_summary": _safe_labels(safe_source.get("knowns")),
            "unknowns_summary": _safe_labels(safe_source.get("unknowns")),
            "uncertainty_summary": _safe_label(safe_source.get("uncertainty", "unknown_engine_uncertainty_metadata_only")),
            "possible_branch_label_summary": _safe_labels(safe_source.get("predictions_or_branch_labels")),
            "missing_evidence_summary": _safe_labels(_source_unknown_engine_metadata(safe_source).get("missing_evidence_labels")),
            "falsification_summary": _safe_labels(_source_unknown_engine_metadata(safe_source).get("falsification_test_labels")),
            "safe_next_observation_summary": _safe_labels(_source_unknown_engine_metadata(safe_source).get("safe_next_observation_labels")),
            "evidence_change_summary": _safe_labels(_source_unknown_engine_metadata(safe_source).get("evidence_change_labels")),
            "risk_boundary_summary": _safe_labels(_source_unknown_engine_metadata(safe_source).get("risk_boundary_labels")),
            "compressed_lesson_summary": _safe_label(safe_source.get("compressed_lesson", "unknown_engine_compressed_lesson_metadata_only")),
            "denied_authority_summary": _denied_authority_summary(safe_source),
            "visible_risks": [
                "helper-design-is-not-helper-implementation",
                "artifact-helper-is-not-artifact-creation",
                "artifact-metadata-is-not-engine-execution",
                "artifact-metadata-is-not-prediction-authority",
                "branch-labels-are-not-future-certainty",
                "safe-markdown-is-not-user-facing-answer-text",
                "json-safe-metadata-is-not-reply-payload",
                "result-artifact-is-not-official-evaluation-evidence",
                "validation-pass-is-not-intelligence-product-runtime-evidence",
                "frontier-open-problem-metadata-is-not-solution-evidence",
                "occ-openclaw-is-not-deployed-weslr",
            ],
            "followups": _safe_labels(safe_source.get("followups")) or ["review_unknown_engine_result_artifact_helpers_implementation_v1"],
            "next_lane": NEXT_LANE_V1,
            "validation_status": "blocked_invalid_or_unsafe_metadata_labels_only",
            "blocked": True,
            "blocked_reason_labels": reasons,
        }
    )


def build_unknown_engine_result_artifact_v1(source_metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Build in-memory UNKNOWN ENGINE result artifact metadata only.

    The builder validates source UNKNOWN ENGINE CognitiveGymRun metadata first,
    preserves blocked source metadata as blocked artifact metadata, writes no
    files, executes no engines/runtime paths, creates no reply/final-answer/user
    output, and grants no authority.
    """

    if not isinstance(source_metadata, Mapping):
        return _blocked_artifact(None, ["source_metadata_not_mapping"])

    source = to_unknown_engine_run_json_safe_v1(source_metadata)
    source_validation = validate_unknown_engine_run_v1(source_metadata)
    unsafe_reasons = _detect_unsafe_content(source_metadata)
    denied_reasons = _source_denied_violations(source_metadata)
    reasons = _safe_labels(
        source_validation.get("blocked_reason_labels", [])
        + source_validation.get("denied_authority_violations", [])
        + denied_reasons
        + unsafe_reasons
    )

    if source.get("engine_name") != UNKNOWN_ENGINE_NAME_V1:
        _append_unique(reasons, "source_engine_name_not_unknown_engine")

    source_blocked = bool(source.get("blocked")) or bool(source_validation.get("blocked")) or bool(reasons)
    unknown_engine_metadata = _source_unknown_engine_metadata(source)

    artifact = {
        "artifact_name": ARTIFACT_NAME_V1,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION_V1,
        "source_engine_name": source.get("engine_name"),
        "source_helper_module": SOURCE_HELPER_MODULE_V1,
        "source_protocol_name": source.get("protocol_name"),
        "source_validation_status": source.get("validation_status", _artifact_validation_status(source_blocked)),
        "source_blocked": bool(source.get("blocked")) or bool(source_validation.get("blocked")),
        "source_blocked_reason_labels": _safe_labels(source.get("blocked_reason_labels", []) + source_validation.get("blocked_reason_labels", [])),
        "knowns_summary": _safe_labels(source.get("knowns")),
        "unknowns_summary": _safe_labels(source.get("unknowns")),
        "uncertainty_summary": _safe_label(source.get("uncertainty", "unknown_engine_uncertainty_metadata_only")),
        "possible_branch_label_summary": _safe_labels(source.get("predictions_or_branch_labels")),
        "missing_evidence_summary": _safe_labels(unknown_engine_metadata.get("missing_evidence_labels")),
        "falsification_summary": _safe_labels(unknown_engine_metadata.get("falsification_test_labels")),
        "safe_next_observation_summary": _safe_labels(unknown_engine_metadata.get("safe_next_observation_labels")),
        "evidence_change_summary": _safe_labels(unknown_engine_metadata.get("evidence_change_labels")),
        "risk_boundary_summary": _safe_labels(unknown_engine_metadata.get("risk_boundary_labels")),
        "compressed_lesson_summary": _safe_label(source.get("compressed_lesson", "unknown_engine_compressed_lesson_metadata_only")),
        "denied_authority_summary": _denied_authority_summary(source),
        "visible_risks": _safe_labels(
            source.get("visible_risks", [])
            + [
                "helper-design-is-not-helper-implementation",
                "artifact-helper-is-not-artifact-creation",
                "artifact-metadata-is-not-engine-execution",
                "artifact-metadata-is-not-prediction-authority",
                "branch-labels-are-not-future-certainty",
                "safe-markdown-is-not-user-facing-answer-text",
                "json-safe-metadata-is-not-reply-payload",
                "result-artifact-is-not-official-evaluation-evidence",
                "validation-pass-is-not-intelligence-product-runtime-evidence",
                "frontier-open-problem-metadata-is-not-solution-evidence",
                "occ-openclaw-is-not-deployed-weslr",
            ]
        ),
        "followups": _safe_labels(source.get("followups")) or ["review_unknown_engine_result_artifact_helpers_implementation_v1"],
        "next_lane": NEXT_LANE_V1,
        "validation_status": _artifact_validation_status(source_blocked),
        "blocked": source_blocked,
        "blocked_reason_labels": reasons,
    }

    artifact_reasons = _detect_unsafe_content(artifact)
    for reason in artifact_reasons:
        _append_unique(artifact["blocked_reason_labels"], reason)
    if artifact["blocked_reason_labels"]:
        artifact["blocked"] = True
        artifact["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(artifact)


def validate_unknown_engine_result_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate UNKNOWN ENGINE result artifact metadata without side effects."""

    if not isinstance(artifact, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_reason_labels": ["artifact_not_mapping"],
            "missing_required_fields": list(_ALLOWED_ARTIFACT_FIELDS),
            "invalid_fields": ["artifact"],
            "json_safe": False,
            "safe_to_render_markdown": False,
            "denied_authority_violations": [],
        }

    blocked_reason_labels: list[str] = []
    invalid_fields: list[str] = []
    missing_required_fields = [field for field in _ALLOWED_ARTIFACT_FIELDS if field not in artifact]
    for field in missing_required_fields:
        _append_unique(blocked_reason_labels, f"missing_required_field:{field}")

    extra_fields = [field for field in artifact if field not in _ALLOWED_ARTIFACT_FIELDS]
    for field in extra_fields:
        _append_unique(invalid_fields, field)
        _append_unique(blocked_reason_labels, f"unsupported_artifact_field:{field}")

    if artifact.get("artifact_name") != ARTIFACT_NAME_V1:
        _append_unique(invalid_fields, "artifact_name")
        _append_unique(blocked_reason_labels, "artifact_name_mismatch")
    if artifact.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION_V1:
        _append_unique(invalid_fields, "artifact_schema_version")
        _append_unique(blocked_reason_labels, "artifact_schema_version_mismatch")
    if artifact.get("source_engine_name") != UNKNOWN_ENGINE_NAME_V1:
        _append_unique(invalid_fields, "source_engine_name")
        _append_unique(blocked_reason_labels, "source_engine_name_not_unknown_engine")
    if artifact.get("source_helper_module") != SOURCE_HELPER_MODULE_V1:
        _append_unique(invalid_fields, "source_helper_module")
        _append_unique(blocked_reason_labels, "source_helper_module_mismatch")
    if artifact.get("next_lane") != NEXT_LANE_V1:
        _append_unique(invalid_fields, "next_lane")
        _append_unique(blocked_reason_labels, "next_lane_mismatch")

    if not isinstance(artifact.get("source_blocked"), bool):
        _append_unique(invalid_fields, "source_blocked")
        _append_unique(blocked_reason_labels, "source_blocked_not_boolean")
    if not isinstance(artifact.get("blocked"), bool):
        _append_unique(invalid_fields, "blocked")
        _append_unique(blocked_reason_labels, "blocked_not_boolean")

    for field in _LIST_ARTIFACT_FIELDS:
        if field in artifact and not isinstance(artifact.get(field), list):
            _append_unique(invalid_fields, field)
            _append_unique(blocked_reason_labels, f"{field}_not_list")

    if "uncertainty_summary" in artifact and not isinstance(artifact.get("uncertainty_summary"), str):
        _append_unique(invalid_fields, "uncertainty_summary")
        _append_unique(blocked_reason_labels, "uncertainty_summary_not_string")
    if "compressed_lesson_summary" in artifact and not isinstance(artifact.get("compressed_lesson_summary"), str):
        _append_unique(invalid_fields, "compressed_lesson_summary")
        _append_unique(blocked_reason_labels, "compressed_lesson_summary_not_string")

    denied = artifact.get("denied_authority_summary")
    denied_authority_violations: list[str] = []
    if not isinstance(denied, Mapping):
        _append_unique(invalid_fields, "denied_authority_summary")
        _append_unique(blocked_reason_labels, "denied_authority_summary_not_mapping")
        denied = {}
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            _append_unique(denied_authority_violations, f"missing_denied_authority_field:{field}")
        elif denied.get(field) is not False:
            _append_unique(denied_authority_violations, f"denied_authority_field_not_false:{field}")
    for reason in denied_authority_violations:
        _append_unique(blocked_reason_labels, reason)

    json_safe = _is_json_safe(artifact)
    if not json_safe:
        _append_unique(blocked_reason_labels, "non_json_safe_artifact_detected")

    for reason in _detect_unsafe_content(artifact):
        _append_unique(blocked_reason_labels, reason)

    if artifact.get("blocked") is True:
        for reason in _safe_labels(artifact.get("blocked_reason_labels", [])):
            _append_unique(blocked_reason_labels, reason)

    valid = not blocked_reason_labels and not invalid_fields and not missing_required_fields and json_safe
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(blocked_reason_labels),
        "missing_required_fields": missing_required_fields,
        "invalid_fields": _safe_labels(invalid_fields),
        "json_safe": json_safe,
        "safe_to_render_markdown": valid,
        "denied_authority_violations": _safe_labels(denied_authority_violations),
    }


def summarize_unknown_engine_result_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact JSON-safe internal summary metadata."""

    validation = validate_unknown_engine_result_artifact_v1(artifact)
    if not isinstance(artifact, Mapping):
        artifact = {}
    return _json_safe(
        {
            "artifact_name": artifact.get("artifact_name"),
            "artifact_schema_version": artifact.get("artifact_schema_version"),
            "source_engine_name": artifact.get("source_engine_name"),
            "source_protocol_name": artifact.get("source_protocol_name"),
            "source_validation_status": artifact.get("source_validation_status"),
            "source_blocked": artifact.get("source_blocked"),
            "valid": validation["valid"],
            "blocked": validation["blocked"],
            "validation_status": "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only",
            "blocked_reason_labels": validation["blocked_reason_labels"],
            "denied_authority_fields_false": not validation["denied_authority_violations"],
            "visible_risks": _json_safe(artifact.get("visible_risks", [])),
            "followups": _json_safe(artifact.get("followups", [])),
            "next_lane": artifact.get("next_lane", NEXT_LANE_V1),
        }
    )


def render_unknown_engine_result_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for validated artifact metadata only."""

    validation = validate_unknown_engine_result_artifact_v1(artifact)
    if validation["valid"] is not True:
        reasons = validation["blocked_reason_labels"] or ["invalid_unknown_engine_result_artifact_metadata"]
        lines = [
            "# WESLR UNKNOWN ENGINE Result Artifact Helper V1",
            "",
            "- artifact_name: `unknown_engine_result_artifact_v1`",
            "- valid: `False`",
            "- blocked: `True`",
            "- unsafe_content_not_rendered: `True`",
            "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
            "",
            "## Blocked Reason Labels",
        ]
        lines.extend(f"- `{reason}`" for reason in _safe_labels(reasons))
        lines.extend(
            [
                "",
                "## Safety Boundary",
                "- `internal_review_material_only`",
                "- `metadata_only_no_runtime_no_output_no_authority`",
                "- `no_unknown_engine_execution`",
                "- `no_cognitive_gym_run_execution`",
                "- `no_cognitive_gym_execution`",
                "- `no_prediction_output_created`",
                "- `no_future_certainty_claim_created`",
                "- `no_open_problem_solution_claim_created`",
                "- `no_reply_preview_final_answer_or_user_facing_output_created`",
                "- `chat_responder_not_called`",
                "- `provider_model_search_advisor_not_called`",
                "- `dot_weslr_io_not_performed`",
                "- `no_judges_scores_or_official_claims`",
                f"- next_lane: `{NEXT_LANE_V1}`",
            ]
        )
        return "\n".join(lines) + "\n"

    lines = [
        "# WESLR UNKNOWN ENGINE Result Artifact Helper V1",
        "",
        "## Artifact Status",
        f"- artifact_name: `{artifact['artifact_name']}`",
        f"- artifact_schema_version: `{artifact['artifact_schema_version']}`",
        f"- source_engine_name: `{artifact['source_engine_name']}`",
        f"- source_protocol_name: `{artifact['source_protocol_name']}`",
        f"- source_validation_status: `{artifact['source_validation_status']}`",
        f"- source_blocked: `{artifact['source_blocked']}`",
        f"- valid: `{validation['valid']}`",
        f"- blocked: `{validation['blocked']}`",
        f"- validation_status: `validation_pass_metadata_quality_only`",
        "",
        "## Metadata Summaries",
        f"- knowns_summary: `{artifact['knowns_summary']}`",
        f"- unknowns_summary: `{artifact['unknowns_summary']}`",
        f"- uncertainty_summary: `{artifact['uncertainty_summary']}`",
        f"- possible_branch_label_summary: `{artifact['possible_branch_label_summary']}`",
        f"- missing_evidence_summary: `{artifact['missing_evidence_summary']}`",
        f"- falsification_summary: `{artifact['falsification_summary']}`",
        f"- safe_next_observation_summary: `{artifact['safe_next_observation_summary']}`",
        f"- evidence_change_summary: `{artifact['evidence_change_summary']}`",
        f"- risk_boundary_summary: `{artifact['risk_boundary_summary']}`",
        f"- compressed_lesson_summary: `{artifact['compressed_lesson_summary']}`",
        "",
        "## Denied Authority Summary",
    ]
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        lines.append(f"- {field}: `{artifact['denied_authority_summary'][field]}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- `internal_review_material_only`",
            "- `metadata_only_no_runtime_no_output_no_authority`",
            "- `not_reply_output`",
            "- `not_preview_output`",
            "- `not_final_answer_prose`",
            "- `not_user_facing_output`",
            "- `not_sendable_reply_text`",
            "- `not_actual_reply_body`",
            "- `not_official_claim`",
            "- `not_open_problem_solution_claim`",
            "- `not_prediction_output`",
            "- `no_authority_grant`",
            f"- next_lane: `{artifact['next_lane']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def to_unknown_engine_result_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe UNKNOWN ENGINE artifact metadata."""

    validation = validate_unknown_engine_result_artifact_v1(artifact)
    if validation["valid"] is not True:
        return _blocked_artifact(artifact if isinstance(artifact, Mapping) else {}, validation["blocked_reason_labels"])
    safe = _json_safe(artifact)
    safe["denied_authority_summary"] = {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS}
    return safe


__all__ = (
    "build_unknown_engine_result_artifact_v1",
    "validate_unknown_engine_result_artifact_v1",
    "summarize_unknown_engine_result_artifact_v1",
    "render_unknown_engine_result_artifact_markdown_v1",
    "to_unknown_engine_result_artifact_json_safe_v1",
)
