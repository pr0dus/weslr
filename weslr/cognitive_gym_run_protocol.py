"""WESLR CognitiveGymRun metadata protocol helpers V1.

Helper-only, metadata-only, deterministic, in-memory protocol helpers for
future Cognitive Gym engine reports. This module defines and validates one
shared report shape. It does not implement or execute Cognitive Gym engines,
UNKNOWN ENGINE, runtime behavior, provider/model/search/advisor calls,
ChatResponder/respond_chat/generate_chat paths, .weslr IO, judges/scores,
official claims, reply output, final answers, answer drafts, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any, Mapping

COGNITIVE_GYM_RUN_PROTOCOL_NAME = "cognitive_gym_run_v1"
COGNITIVE_GYM_RUN_SCHEMA_VERSION = "cognitive_gym_run_schema_v1"
INVALID_COGNITIVE_GYM_RUN_PROTOCOL_NAME = "cognitive_gym_run_v1_invalid"
NEXT_LANE_V1 = "REVIEW_COGNITIVE_GYM_RUN_PROTOCOL_HELPERS_IMPLEMENTATION_V1"

SUPPORTED_COGNITIVE_GYM_ENGINE_NAMES = (
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
)

SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS = (
    "UNKNOWN / uncertainty",
    "ERDŐS / open mathematical structure",
    "COUNTEREXAMPLE / falsification",
    "CALIBRATION / prediction vs outcome",
    "CONTRADICTION / conflict handling",
    "GOVERNANCE / allowed vs possible",
    "MATERIALS / scientific discovery",
    "CONVERSATION / human understanding",
)

REQUIRED_DENIED_AUTHORITY_FIELDS = (
    "cognitive_gym_authority_granted",
    "cognitive_gym_run_authority_granted",
    "unknown_engine_authority_granted",
    "prediction_authority_granted",
    "future_certainty_authority_granted",
    "challenge_solution_authority_granted",
    "open_problem_solution_claim_authorized",
    "answer_authority_granted",
    "preview_authority_granted",
    "reply_output_authority_granted",
    "reply_text_authority_granted",
    "user_facing_output_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "turing_test_authority_granted",
    "real_conversation_sandbox_authority_granted",
    "cognitive_gym_executed",
    "cognitive_gym_run_executed",
    "unknown_engine_executed",
    "prediction_output_created",
    "future_certainty_claim_created",
    "challenge_solution_claim_created",
    "reply_preview_executed",
    "preview_output_created",
    "reply_output_created",
    "reply_text_executed",
    "sendable_reply_text_created",
    "actual_reply_body_created",
    "user_facing_output_executed",
    "user_facing_reply_created",
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
    "dot_weslr_read_performed",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judges_created",
    "scores_created",
    "official_claim_made",
)

REQUIRED_COGNITIVE_GYM_RUN_FIELDS = (
    "protocol_name",
    "schema_version",
    "engine_name",
    "engine_version_label",
    "challenge_track",
    "input_state",
    "observations",
    "knowns",
    "unknowns",
    "hypotheses",
    "predictions_or_branch_labels",
    "confidence",
    "uncertainty",
    "invalidation_signals",
    "reveal_or_outcome",
    "correction",
    "compressed_lesson",
    "boundary_status",
    "denied_authority_fields",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
    "next_lane",
)

_LIST_FIELDS = (
    "observations",
    "knowns",
    "unknowns",
    "hypotheses",
    "predictions_or_branch_labels",
    "invalidation_signals",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
)

_FORBIDDEN_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "private",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue_output",
    "user_facing_response_body",
    "sendable_reply_text",
    "sendable_message",
    "actual_reply_body",
    "final_answer_prose",
    "answer_draft",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "dot_weslr",
    "feature_flag",
    "judge",
    "score",
    "official_claim",
    "benchmark_claim",
    "iq_claim",
    "turing_claim",
    "certification_claim",
    "product_readiness_claim",
    "open_problem_solution",
    "future_certainty",
    "prediction_authority",
    "answer_authority",
    "runtime_authority",
    "official_evaluation_authority",
)

_TEXT_MARKERS = {
    "raw_prompt_text_detected": ("raw prompt:", "raw_prompt:", "system prompt:", "developer prompt:"),
    "raw_response_text_detected": ("raw response:", "raw_response:", "assistant raw:"),
    "private_content_detected": ("private content:", "confidential:", "secret:", "api key", "password:"),
    "provider_output_detected": ("provider output:", "provider response:"),
    "model_output_detected": ("model output:", "llm output:"),
    "search_output_detected": ("search output:", "search result:"),
    "advisor_output_detected": ("advisor output:", "advisor response:"),
    "runtime_output_detected": ("runtime output:", "runtime trace:", "live runtime output:"),
    "live_dialogue_output_detected": ("live dialogue:", "live chat output:"),
    "user_facing_response_body_detected": ("user-facing response body:", "reply to user:", "send to user:"),
    "sendable_reply_text_detected": ("sendable reply text:", "message to send:", "sendable message:"),
    "actual_reply_body_detected": ("actual reply body:",),
    "final_answer_prose_detected": ("final answer:", "final-answer prose", "final response:"),
    "answer_draft_text_detected": ("answer draft:", "draft answer:", "composed reply:"),
    "chat_responder_signal_detected": ("chatresponder", "chat responder", "respond_chat", "generate_chat"),
    "dot_weslr_io_signal_detected": (".weslr read", ".weslr write", "dot_weslr_read_performed=true", "dot_weslr_write_performed=true"),
    "feature_flag_signal_detected": ("feature_flag_enabled=true", "enable feature flag"),
    "judges_or_scores_detected": ("judge decision:", "official score:", "score: 100", "judges created"),
    "official_claim_detected": ("official benchmark", "official iq", "passed the turing test", "certified product-ready", "product readiness"),
    "open_problem_solution_claim_detected": ("open-problem solution", "erdős solved", "erdos solved", "solved the open problem"),
    "future_certainty_claim_detected": ("future certainty", "guaranteed future", "certain future", "prophecy", "oracle"),
    "prediction_authority_grant_detected": ("prediction authority granted", "prediction_authority_granted=true"),
    "answer_authority_grant_detected": ("answer authority granted", "answer_authority_granted=true"),
    "runtime_authority_grant_detected": ("runtime authority granted", "runtime_authority_granted=true"),
    "official_evaluation_authority_grant_detected": ("official evaluation authority granted", "official_evaluation_authority_granted=true"),
}

_SAFE_LITERAL_STRINGS = {
    COGNITIVE_GYM_RUN_PROTOCOL_NAME,
    COGNITIVE_GYM_RUN_SCHEMA_VERSION,
    INVALID_COGNITIVE_GYM_RUN_PROTOCOL_NAME,
    NEXT_LANE_V1,
    "validation_pending_metadata_quality_only",
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "metadata_only_no_runtime_no_output_no_authority",
    "none_metadata_only",
    "not_revealed_metadata_only",
    "no_correction_metadata_only",
    "no_compressed_lesson_metadata_only",
    "engine_specific_metadata",
    "json_safe_after_validation",
    "safe_markdown_after_validation",
    *_LIST_FIELDS,
    *REQUIRED_COGNITIVE_GYM_RUN_FIELDS,
    *SUPPORTED_COGNITIVE_GYM_ENGINE_NAMES,
    *SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS,
    *REQUIRED_DENIED_AUTHORITY_FIELDS,
}

_SAFE_NEXT_LANE_RE = re.compile(r"^[A-Z0-9_]{3,120}_V1$")


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


def _safe_labels(values: Any) -> list[str]:
    labels: list[str] = []
    for value in _as_list(values):
        _append_unique(labels, _safe_label(value))
    return labels


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


def _detect_unsafe_content(value: Any) -> list[str]:
    reasons: list[str] = []
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        key_allowed = key in {field.lower() for field in REQUIRED_COGNITIVE_GYM_RUN_FIELDS} or key in {field.lower() for field in REQUIRED_DENIED_AUTHORITY_FIELDS}
        if not key_allowed:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    _append_unique(reasons, f"unsafe_key_detected:{fragment}")
        if isinstance(item, str):
            if item in _SAFE_LITERAL_STRINGS:
                continue
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
    return reasons


def _default_boundary_status() -> dict[str, bool]:
    return {
        "metadata_only": True,
        "internal_only": True,
        "helper_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "safe_markdown_internal_review_only": True,
        "json_safe_metadata_only": True,
        "shared_protocol_first": True,
        "individual_engines_second": True,
        "runtime_integration_later_only_if_separately_authorized": True,
    }


def _base_run() -> dict[str, Any]:
    return {
        "protocol_name": COGNITIVE_GYM_RUN_PROTOCOL_NAME,
        "schema_version": COGNITIVE_GYM_RUN_SCHEMA_VERSION,
        "engine_name": "UNKNOWN_ENGINE",
        "engine_version_label": "engine_not_implemented_metadata_protocol_v1",
        "challenge_track": "UNKNOWN / uncertainty",
        "input_state": "metadata_only_input_state",
        "observations": [],
        "knowns": [],
        "unknowns": [],
        "hypotheses": [],
        "predictions_or_branch_labels": [],
        "confidence": "not_scored_metadata_only",
        "uncertainty": "uncertainty_metadata_only",
        "invalidation_signals": [],
        "reveal_or_outcome": "not_revealed_metadata_only",
        "correction": "no_correction_metadata_only",
        "compressed_lesson": "no_compressed_lesson_metadata_only",
        "boundary_status": _default_boundary_status(),
        "denied_authority_fields": {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS},
        "validation_status": "validation_pending_metadata_quality_only",
        "blocked": False,
        "blocked_reason_labels": [],
        "visible_risks": [
            "shared-protocol-as-engine-authority",
            "metadata-as-execution-authority",
            "branch-labels-as-prediction-authority",
            "safe-markdown-as-user-output",
            "validation-pass-as-runtime-product-official-authority",
            "engine-specific-metadata-as-private-report-shape",
        ],
        "followups": [
            "review_cognitive_gym_run_protocol_helpers_implementation_v1",
            "keep_individual_engine_implementation_separate",
            "keep_unknown_engine_implementation_separate",
            "keep_runtime_integration_separate",
            "keep_official_evaluation_claims_separate",
        ],
        "next_lane": NEXT_LANE_V1,
    }


def _merge_input(metadata: Mapping[str, Any] | None, overrides: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if metadata is None:
        source: dict[str, Any] = {}
    elif isinstance(metadata, Mapping):
        source = dict(metadata)
    else:
        return {}, ["input_metadata_not_mapping"]
    source.update(dict(overrides))
    return source, []


def build_cognitive_gym_run_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Build one metadata-only CognitiveGymRun protocol object.

    The builder only arranges in-memory metadata. It never executes an engine,
    calls runtime/provider/model/search/advisor paths, reads or writes .weslr,
    creates reply/final-answer output, or grants authority.
    """

    source, early_reasons = _merge_input(metadata, overrides)
    run = _base_run()
    if early_reasons:
        run["blocked"] = True
        run["blocked_reason_labels"] = early_reasons
        run["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        return run

    input_reasons = _detect_unsafe_content(source)
    if not _is_json_safe(source):
        _append_unique(input_reasons, "non_json_safe_input_detected")

    for field in REQUIRED_COGNITIVE_GYM_RUN_FIELDS:
        if field in source and field != "denied_authority_fields":
            run[field] = _json_safe(source[field])

    if isinstance(source.get("denied_authority_fields"), Mapping):
        denied = {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS}
        for key, value in source["denied_authority_fields"].items():
            denied[str(key)] = _json_safe(value)
        run["denied_authority_fields"] = denied

    if "engine_specific_metadata" in source:
        if _is_json_safe(source["engine_specific_metadata"]):
            run["engine_specific_metadata"] = _json_safe(source["engine_specific_metadata"])
        else:
            _append_unique(input_reasons, "engine_specific_metadata_not_json_safe")

    if input_reasons:
        run["blocked"] = True
        run["blocked_reason_labels"] = _safe_labels(input_reasons)

    validation = validate_cognitive_gym_run_v1(run)
    run["blocked"] = validation["blocked"]
    run["blocked_reason_labels"] = _safe_labels(run.get("blocked_reason_labels", []) + validation.get("blocked_reason_labels", []))
    run["validation_status"] = "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(run)


def validate_cognitive_gym_run_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate CognitiveGymRun metadata and return validation metadata only."""

    if not isinstance(run, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_reason_labels": ["run_not_mapping"],
            "missing_required_fields": list(REQUIRED_COGNITIVE_GYM_RUN_FIELDS),
            "invalid_fields": ["run"],
            "unsupported_engine_name": None,
            "unsupported_challenge_track": None,
            "denied_authority_violations": [],
            "json_safe": False,
            "safe_to_render_markdown": False,
        }

    blocked_reason_labels: list[str] = []
    invalid_fields: list[str] = []
    missing_required_fields = [field for field in REQUIRED_COGNITIVE_GYM_RUN_FIELDS if field not in run]
    for field in missing_required_fields:
        _append_unique(blocked_reason_labels, f"missing_required_field:{field}")

    if run.get("protocol_name") != COGNITIVE_GYM_RUN_PROTOCOL_NAME:
        invalid_fields.append("protocol_name")
        _append_unique(blocked_reason_labels, "protocol_name_mismatch")
    if run.get("schema_version") != COGNITIVE_GYM_RUN_SCHEMA_VERSION:
        invalid_fields.append("schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")

    unsupported_engine_name = None
    if run.get("engine_name") not in SUPPORTED_COGNITIVE_GYM_ENGINE_NAMES:
        unsupported_engine_name = run.get("engine_name")
        invalid_fields.append("engine_name")
        _append_unique(blocked_reason_labels, "unsupported_engine_name")

    unsupported_challenge_track = None
    if run.get("challenge_track") not in SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS:
        unsupported_challenge_track = run.get("challenge_track")
        invalid_fields.append("challenge_track")
        _append_unique(blocked_reason_labels, "unsupported_challenge_track")

    denied = run.get("denied_authority_fields")
    denied_authority_violations: list[str] = []
    if not isinstance(denied, Mapping):
        invalid_fields.append("denied_authority_fields")
        _append_unique(blocked_reason_labels, "denied_authority_fields_not_mapping")
        denied = {}
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
        if field not in denied:
            denied_authority_violations.append(f"missing_denied_authority_field:{field}")
        elif denied.get(field) is not False:
            denied_authority_violations.append(f"denied_authority_field_not_false:{field}")
    for field in denied_authority_violations:
        _append_unique(blocked_reason_labels, field)

    if not isinstance(run.get("blocked"), bool):
        invalid_fields.append("blocked")
        _append_unique(blocked_reason_labels, "blocked_not_boolean")
    for field in ("blocked_reason_labels", "visible_risks", "followups"):
        if not isinstance(run.get(field), list):
            invalid_fields.append(field)
            _append_unique(blocked_reason_labels, f"{field}_not_list")
    for field in _LIST_FIELDS:
        if field in run and not isinstance(run.get(field), list):
            invalid_fields.append(field)
            _append_unique(blocked_reason_labels, f"{field}_not_list")

    next_lane = run.get("next_lane")
    if not isinstance(next_lane, str) or not _SAFE_NEXT_LANE_RE.fullmatch(next_lane):
        invalid_fields.append("next_lane")
        _append_unique(blocked_reason_labels, "next_lane_not_safe_label")

    json_safe = _is_json_safe(run)
    if not json_safe:
        _append_unique(blocked_reason_labels, "non_json_safe_value_detected")

    for label in _detect_unsafe_content(run):
        _append_unique(blocked_reason_labels, label)

    if run.get("blocked") is True:
        for label in _safe_labels(run.get("blocked_reason_labels", [])):
            _append_unique(blocked_reason_labels, label)

    valid = not blocked_reason_labels and not invalid_fields and not missing_required_fields and json_safe
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(blocked_reason_labels),
        "missing_required_fields": missing_required_fields,
        "invalid_fields": _safe_labels(invalid_fields),
        "unsupported_engine_name": unsupported_engine_name,
        "unsupported_challenge_track": unsupported_challenge_track,
        "denied_authority_violations": _safe_labels(denied_authority_violations),
        "json_safe": json_safe,
        "safe_to_render_markdown": valid,
    }


def summarize_cognitive_gym_run_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact safe summary for one CognitiveGymRun metadata object."""

    validation = validate_cognitive_gym_run_v1(run)
    if not isinstance(run, Mapping):
        run = {}
    return {
        "protocol_name": run.get("protocol_name"),
        "schema_version": run.get("schema_version"),
        "engine_name": run.get("engine_name"),
        "engine_version_label": run.get("engine_version_label"),
        "challenge_track": run.get("challenge_track"),
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "validation_status": "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only",
        "blocked_reason_labels": validation["blocked_reason_labels"],
        "boundary_status": _json_safe(run.get("boundary_status", {})),
        "denied_authority_fields_false": isinstance(run.get("denied_authority_fields"), Mapping) and not validation["denied_authority_violations"],
        "visible_risks": _json_safe(run.get("visible_risks", [])),
        "followups": _json_safe(run.get("followups", [])),
        "next_lane": run.get("next_lane", NEXT_LANE_V1),
    }


def _blocked_markdown(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reasons = _safe_labels(validation.get("blocked_reason_labels") or summary.get("blocked_reason_labels") or ["invalid_or_unsafe_cognitive_gym_run_metadata"])
    lines = [
        "# WESLR CognitiveGymRun Protocol Helper V1",
        "",
        f"- protocol_name: `{INVALID_COGNITIVE_GYM_RUN_PROTOCOL_NAME}`",
        "- valid: `False`",
        "- blocked: `True`",
        "- unsafe_content_not_rendered: `True`",
        "- validation_status: `blocked_invalid_or_unsafe_metadata_labels_only`",
        "",
        "## Blocked Reason Labels",
    ]
    lines.extend(f"- `{reason}`" for reason in reasons)
    lines.extend([
        "",
        "## Safety Boundary",
        "- `metadata_only_no_runtime_no_output_no_authority`",
        "- `no_cognitive_gym_execution`",
        "- `no_unknown_engine_execution`",
        "- `no_prediction_output_created`",
        "- `no_future_certainty_claim_created`",
        "- `no_open_problem_solution_claim_created`",
        "- `no_reply_or_user_facing_output_created`",
        "- `no_final_answer_or_answer_draft_created`",
        "- `chat_responder_not_called`",
        "- `provider_model_search_advisor_not_called`",
        "- `dot_weslr_io_not_performed`",
        "- `no_judges_scores_or_official_claims`",
        f"- next_lane: `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_cognitive_gym_run_markdown_v1(run: Mapping[str, Any]) -> str:
    """Render safe internal Markdown for validated CognitiveGymRun metadata only."""

    validation = validate_cognitive_gym_run_v1(run)
    summary = summarize_cognitive_gym_run_v1(run)
    if validation["valid"] is not True:
        return _blocked_markdown(validation, summary)

    lines = [
        "# WESLR CognitiveGymRun Protocol Helper V1",
        "",
        "## Protocol Status",
        f"- protocol_name: `{summary['protocol_name']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- engine_name: `{summary['engine_name']}`",
        f"- engine_version_label: `{summary['engine_version_label']}`",
        f"- challenge_track: `{summary['challenge_track']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- validation_status: `{summary['validation_status']}`",
        "",
        "## Boundary Status",
    ]
    for key, value in summary["boundary_status"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Denied Authority Fields",
    ])
    lines.extend(f"- `{field}=false`" for field in REQUIRED_DENIED_AUTHORITY_FIELDS)
    lines.extend([
        "",
        "## Internal Review Safety Notes",
        "- `safe_markdown_internal_review_material_only`",
        "- `safe_markdown_is_not_user_facing_output`",
        "- `safe_markdown_is_not_reply_payload`",
        "- `safe_markdown_is_not_final_answer_prose`",
        "- `validation_pass_is_metadata_quality_only`",
        "- `shared_protocol_first_individual_engines_second`",
        "",
        "## Visible Risks",
    ])
    lines.extend(f"- `{risk}`" for risk in summary["visible_risks"])
    lines.extend(["", "## Followups"])
    lines.extend(f"- `{followup}`" for followup in summary["followups"])
    lines.extend(["", "## Next Lane", f"- `{summary['next_lane']}`"])
    return "\n".join(lines) + "\n"


def to_cognitive_gym_run_json_safe_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe CognitiveGymRun data or a safe blocked wrapper."""

    validation = validate_cognitive_gym_run_v1(run)
    if validation["valid"] is not True:
        wrapper = _base_run()
        wrapper["protocol_name"] = INVALID_COGNITIVE_GYM_RUN_PROTOCOL_NAME
        wrapper["blocked"] = True
        wrapper["blocked_reason_labels"] = validation["blocked_reason_labels"] or ["invalid_or_unsafe_cognitive_gym_run_metadata"]
        wrapper["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        return _json_safe(wrapper)
    return _json_safe(run)
