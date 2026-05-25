"""WESLR CALIBRATION_LEDGER exploratory metadata helpers V1.

Helper-only, metadata-only, deterministic, in-memory adapters from bounded
CALIBRATION_LEDGER labels into the reviewed shared Cognitive Gym exploratory
case shape. This module does not implement runtime behavior, chat/user-facing
output, engine execution, scoring, judging, provider/model/search/advisor calls,
.weslr IO, final answers, proof/open-problem/scientific/official claims, or
authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any, Mapping

from weslr.cognitive_gym_exploratory_case import (
    REQUIRED_DENIED_AUTHORITY_FIELDS_V1,
    build_cognitive_gym_exploratory_case_v1,
    render_cognitive_gym_exploratory_case_markdown_v1,
    summarize_cognitive_gym_exploratory_case_v1,
    to_cognitive_gym_exploratory_case_json_safe_v1,
    validate_cognitive_gym_exploratory_case_v1,
)

CALIBRATION_LEDGER_ENGINE_FAMILY_V1 = "CALIBRATION_LEDGER"
CALIBRATION_LEDGER_CASE_FAMILY_V1 = "calibration_ledger_exploratory_case"
CALIBRATION_LEDGER_NEXT_LANE_V1 = "REVIEW_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_IMPLEMENTATION_V1"
INVALID_CALIBRATION_LEDGER_PROTOCOL_VERSION_V1 = "calibration_ledger_exploratory_case_v1_invalid"

REQUIRED_CALIBRATION_METADATA_FIELDS_V1 = (
    "calibration_case_id",
    "predicted_branch_label",
    "confidence_label",
    "uncertainty_label",
    "observed_outcome_label",
    "mismatch_label",
    "correction_label",
    "lesson_label",
    "calibration_status",
)

SUPPORTED_CALIBRATION_STATUS_LABELS_V1 = (
    "calibration_case_defined",
    "prediction_label_recorded",
    "outcome_label_recorded",
    "match_recorded",
    "mismatch_recorded",
    "correction_label_recorded",
    "lesson_label_recorded",
    "needs_external_review",
    "blocked_by_boundary",
)

_STATUS_TO_LIFECYCLE_V1 = {
    "calibration_case_defined": "case_defined",
    "prediction_label_recorded": "exploratory_candidate",
    "outcome_label_recorded": "partial_structure_found",
    "match_recorded": "correction_recorded",
    "mismatch_recorded": "invalidated",
    "correction_label_recorded": "correction_recorded",
    "lesson_label_recorded": "correction_recorded",
    "needs_external_review": "needs_external_review",
    "blocked_by_boundary": "blocked_by_boundary",
}

_TEXT_MARKERS_V1 = {
    "raw_private_content_indicator_blocked": (
        "raw private content:",
        "private content:",
        "personal sensitive data:",
        "confidential:",
        "secret:",
        "api key",
        "password:",
    ),
    "hidden_prompt_or_answer_key_indicator_blocked": (
        "hidden prompt:",
        "system prompt:",
        "developer prompt:",
        "raw prompt:",
        "answer key:",
        "hidden answer key",
    ),
    "protected_benchmark_indicator_blocked": ("protected benchmark", "benchmark item:", "private eval item"),
    "provider_model_search_advisor_output_indicator_blocked": (
        "provider output:",
        "provider response:",
        "model output:",
        "llm output:",
        "search output:",
        "advisor output:",
    ),
    "dot_weslr_io_indicator_blocked": (".weslr read", ".weslr write", "dot_weslr_read", "dot_weslr_write"),
    "runtime_chat_output_indicator_blocked": (
        "runtime output:",
        "runtime trace:",
        "runtime activation",
        "wire runtime",
        "chat_responder",
        "respond_chat",
        "generate_chat",
    ),
    "final_answer_reply_user_facing_output_indicator_blocked": (
        "final answer:",
        "reply to user:",
        "send to user:",
        "user-facing answer:",
        "sendable reply text:",
        "actual reply body:",
    ),
    "scoring_judging_execution_indicator_blocked": (
        "score:",
        "official score:",
        "judge decision:",
        "execute challenge",
        "engine execution",
    ),
    "proof_open_problem_scientific_official_claim_indicator_blocked": (
        "proof claim:",
        "we proved",
        "weslr solved",
        "open-problem solution",
        "open problem solution",
        "scientific discovery claim",
        "official benchmark",
        "passed the turing test",
        "intelligence certification",
        "consciousness claim",
        "product readiness",
    ),
}

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_private",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "protected_benchmark",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "dot_weslr",
    ".weslr",
    "runtime_output",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "user_facing",
    "reply_output",
    "final_answer",
    "score",
    "judge",
    "proof_claim",
    "open_problem_solution",
    "scientific_discovery",
    "official_benchmark",
    "authority_grant",
)

_SAFE_LABEL_RE_V1 = re.compile(r"^[A-Za-z0-9_./:;=,() \-]{1,220}$")


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _safe_label(value: Any) -> str:
    return str(value).replace("`", "").replace("\n", " ")[:220]


def _safe_labels(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    labels: list[str] = []
    for item in items:
        _append_unique(labels, _safe_label(item))
    return labels


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, bool)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
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


def _detect_unsafe_metadata(value: Any) -> list[str]:
    reasons: list[str] = []
    allowed_keys = {
        *(field.lower() for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1),
        "metadata_only",
        "internal_only",
        "helper_only",
        "non_runtime",
        "non_user_facing",
        "safe_markdown_internal_review_only",
        "json_safe_metadata_only",
        "validation_before_rendering",
        "blocked_metadata_behavior",
        "claim_ladder_preserved",
        "external_validation_required_for_claims",
    }
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if key not in allowed_keys:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1:
                if fragment in key:
                    _append_unique(reasons, f"unsafe_key_detected:{fragment}")
        if isinstance(item, str):
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS_V1.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
    return reasons


def _default_calibration_metadata() -> dict[str, str]:
    return {
        "calibration_case_id": "calibration_case_metadata_v1",
        "predicted_branch_label": "predicted_branch_label_metadata_only",
        "confidence_label": "confidence_label_metadata_only",
        "uncertainty_label": "uncertainty_label_metadata_only",
        "observed_outcome_label": "observed_outcome_label_metadata_only",
        "mismatch_label": "mismatch_label_metadata_only",
        "correction_label": "correction_label_metadata_only",
        "lesson_label": "lesson_label_metadata_only",
        "calibration_status": "calibration_case_defined",
    }


def _merge_metadata(metadata: Mapping[str, Any] | None, overrides: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if metadata is None:
        source: dict[str, Any] = {}
    elif isinstance(metadata, Mapping):
        source = dict(metadata)
    else:
        return {}, ["input_metadata_not_mapping"]
    source.update(dict(overrides))
    return source, []


def _blocked_case(reason_labels: list[str]) -> dict[str, Any]:
    calibration = _default_calibration_metadata()
    calibration["calibration_status"] = "blocked_by_boundary"
    case = build_cognitive_gym_exploratory_case_v1(
        case_id=calibration["calibration_case_id"],
        case_family=CALIBRATION_LEDGER_CASE_FAMILY_V1,
        engine_name=CALIBRATION_LEDGER_ENGINE_FAMILY_V1,
        domain="calibration_ledger_metadata_only",
        lifecycle_label="blocked_by_boundary",
        problem_statement_metadata="calibration_problem_metadata_only",
        input_state="calibration_input_metadata_only",
        observations=["calibration_metadata_blocked_labels_only"],
        counterexamples_or_invalidation_signals=_safe_labels(reason_labels),
        predictions_or_branch_labels=[calibration["predicted_branch_label"]],
        confidence=calibration["confidence_label"],
        uncertainty=calibration["uncertainty_label"],
        reveal_or_outcome=calibration["observed_outcome_label"],
        correction=calibration["correction_label"],
        compressed_lesson=calibration["lesson_label"],
        blocked=True,
        blocked_reason_labels=_safe_labels(reason_labels),
        validation_status="blocked_invalid_or_unsafe_metadata_labels_only",
        next_allowed_steps=["review_calibration_ledger_exploratory_helpers_implementation_v1"],
        next_lane=CALIBRATION_LEDGER_NEXT_LANE_V1,
    )
    case["engine_specific_metadata"] = {"calibration_ledger": _json_safe(calibration)}
    case["blocked"] = True
    case["blocked_reason_labels"] = _safe_labels(reason_labels)
    case["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(case)


def build_calibration_ledger_exploratory_case_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Build one CALIBRATION_LEDGER metadata-only exploratory case."""

    source, early_reasons = _merge_metadata(metadata, overrides)
    reasons = list(early_reasons)
    calibration = _default_calibration_metadata()

    if source.get("engine_family", CALIBRATION_LEDGER_ENGINE_FAMILY_V1) != CALIBRATION_LEDGER_ENGINE_FAMILY_V1:
        _append_unique(reasons, "unsupported_engine_family")
    if source.get("engine_name", CALIBRATION_LEDGER_ENGINE_FAMILY_V1) != CALIBRATION_LEDGER_ENGINE_FAMILY_V1:
        _append_unique(reasons, "unsupported_engine_family")

    for field in REQUIRED_CALIBRATION_METADATA_FIELDS_V1:
        if field in source:
            calibration[field] = _json_safe(source[field])

    for field in REQUIRED_CALIBRATION_METADATA_FIELDS_V1:
        value = calibration.get(field)
        if not isinstance(value, str) or not value or not _SAFE_LABEL_RE_V1.fullmatch(value):
            _append_unique(reasons, f"missing_or_unsafe_calibration_metadata:{field}")

    if calibration.get("calibration_status") not in SUPPORTED_CALIBRATION_STATUS_LABELS_V1:
        _append_unique(reasons, "unsupported_calibration_status")

    if not _is_json_safe(source) or not _is_json_safe(calibration):
        _append_unique(reasons, "non_json_safe_value_detected")
    for label in _detect_unsafe_metadata(source):
        _append_unique(reasons, label)

    if reasons:
        return _blocked_case(reasons)

    lifecycle_label = _STATUS_TO_LIFECYCLE_V1[calibration["calibration_status"]]
    case = build_cognitive_gym_exploratory_case_v1(
        case_id=calibration["calibration_case_id"],
        case_family=CALIBRATION_LEDGER_CASE_FAMILY_V1,
        engine_name=CALIBRATION_LEDGER_ENGINE_FAMILY_V1,
        domain="calibration_ledger_metadata_only",
        lifecycle_label=lifecycle_label,
        problem_statement_metadata="calibration_problem_metadata_only",
        input_state="calibration_input_metadata_only",
        observations=["calibration_metadata_mapped_to_shared_exploratory_case_shape"],
        hypotheses=[],
        candidate_structures=[],
        attempted_approaches=[],
        failed_paths=[],
        counterexamples_or_invalidation_signals=[calibration["mismatch_label"]],
        predictions_or_branch_labels=[calibration["predicted_branch_label"]],
        confidence=calibration["confidence_label"],
        uncertainty=calibration["uncertainty_label"],
        reveal_or_outcome=calibration["observed_outcome_label"],
        correction=calibration["correction_label"],
        compressed_lesson=calibration["lesson_label"],
        review_requirements=["external_validation_required_before_public_final_or_official_claims"],
        next_allowed_steps=["review_calibration_ledger_exploratory_helpers_implementation_v1"],
        safe_summary="calibration_ledger_safe_internal_summary_metadata_only",
        next_lane=CALIBRATION_LEDGER_NEXT_LANE_V1,
    )
    case["engine_specific_metadata"] = {"calibration_ledger": _json_safe(calibration)}
    validation = validate_calibration_ledger_exploratory_case_v1(case)
    case["blocked"] = validation["blocked"]
    case["blocked_reason_labels"] = validation["blocked_reason_labels"]
    case["validation_status"] = "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(case)


def validate_calibration_ledger_exploratory_case_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one CALIBRATION_LEDGER exploratory case metadata object."""

    shared_validation = validate_cognitive_gym_exploratory_case_v1(case)
    reasons = _safe_labels(shared_validation.get("blocked_reason_labels", []))
    invalid_fields = _safe_labels(shared_validation.get("invalid_fields", []))
    missing_fields: list[str] = []

    if not isinstance(case, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_reason_labels": _safe_labels(reasons + ["case_not_mapping"]),
            "missing_calibration_metadata_fields": list(REQUIRED_CALIBRATION_METADATA_FIELDS_V1),
            "invalid_fields": _safe_labels(invalid_fields + ["case"]),
            "unsupported_calibration_status": None,
            "denied_authority_violations": _safe_labels(shared_validation.get("denied_authority_violations", [])),
            "json_safe": False,
            "safe_to_render_markdown": False,
        }

    if case.get("engine_name") != CALIBRATION_LEDGER_ENGINE_FAMILY_V1:
        _append_unique(reasons, "unsupported_engine_family")
        _append_unique(invalid_fields, "engine_name")
    if case.get("case_family") != CALIBRATION_LEDGER_CASE_FAMILY_V1:
        _append_unique(reasons, "unsupported_case_family")
        _append_unique(invalid_fields, "case_family")

    engine_specific = case.get("engine_specific_metadata")
    calibration = engine_specific.get("calibration_ledger") if isinstance(engine_specific, Mapping) else None
    if not isinstance(calibration, Mapping):
        _append_unique(reasons, "missing_calibration_ledger_metadata")
        calibration = {}

    for field in REQUIRED_CALIBRATION_METADATA_FIELDS_V1:
        value = calibration.get(field)
        if field not in calibration:
            missing_fields.append(field)
            _append_unique(reasons, f"missing_calibration_metadata:{field}")
        elif not isinstance(value, str) or not value or not _SAFE_LABEL_RE_V1.fullmatch(value):
            _append_unique(reasons, f"missing_or_unsafe_calibration_metadata:{field}")
            _append_unique(invalid_fields, field)

    unsupported_calibration_status = None
    if calibration.get("calibration_status") not in SUPPORTED_CALIBRATION_STATUS_LABELS_V1:
        unsupported_calibration_status = calibration.get("calibration_status")
        _append_unique(reasons, "unsupported_calibration_status")
        _append_unique(invalid_fields, "calibration_status")

    if not _is_json_safe(case):
        _append_unique(reasons, "non_json_safe_value_detected")
    for label in _detect_unsafe_metadata(case):
        _append_unique(reasons, label)

    denied = case.get("denied_authority_fields")
    denied_violations: list[str] = []
    if not isinstance(denied, Mapping):
        _append_unique(denied_violations, "denied_authority_fields_not_mapping")
    else:
        for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1:
            if field not in denied:
                _append_unique(denied_violations, f"missing_denied_authority_field:{field}")
            elif denied.get(field) is not False:
                _append_unique(denied_violations, f"denied_authority_field_not_false:{field}")
    for field in denied_violations:
        _append_unique(reasons, field)

    valid = not reasons and not invalid_fields and not missing_fields and _is_json_safe(case)
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(reasons),
        "missing_calibration_metadata_fields": _safe_labels(missing_fields),
        "invalid_fields": _safe_labels(invalid_fields),
        "unsupported_calibration_status": unsupported_calibration_status,
        "denied_authority_violations": _safe_labels(denied_violations),
        "json_safe": _is_json_safe(case),
        "safe_to_render_markdown": valid,
    }


def summarize_calibration_ledger_exploratory_case_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return compact boundary/status metadata for one CALIBRATION_LEDGER case."""

    validation = validate_calibration_ledger_exploratory_case_v1(case)
    shared_summary = summarize_cognitive_gym_exploratory_case_v1(case) if isinstance(case, Mapping) else {}
    calibration = {}
    if isinstance(case, Mapping):
        engine_specific = case.get("engine_specific_metadata")
        if isinstance(engine_specific, Mapping) and isinstance(engine_specific.get("calibration_ledger"), Mapping):
            calibration = dict(engine_specific["calibration_ledger"])
    return _json_safe({
        "case_id": case.get("case_id") if isinstance(case, Mapping) else None,
        "case_family": case.get("case_family") if isinstance(case, Mapping) else None,
        "engine_name": case.get("engine_name") if isinstance(case, Mapping) else None,
        "calibration_status": calibration.get("calibration_status"),
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "validation_status": "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only",
        "blocked_reason_labels": validation["blocked_reason_labels"],
        "boundary_status": shared_summary.get("boundary_status", {}),
        "denied_authority_fields_false": not validation["denied_authority_violations"],
        "calibration_metadata_fields_present_count": len(REQUIRED_CALIBRATION_METADATA_FIELDS_V1) - len(validation["missing_calibration_metadata_fields"]),
        "shared_counts": shared_summary.get("counts", {}),
        "next_lane": CALIBRATION_LEDGER_NEXT_LANE_V1,
    })


def _blocked_markdown(validation: Mapping[str, Any]) -> str:
    reasons = _safe_labels(validation.get("blocked_reason_labels") or ["invalid_or_unsafe_calibration_ledger_metadata"])
    lines = [
        "# WESLR CALIBRATION_LEDGER Exploratory Helper V1",
        "",
        f"- protocol_version: `{INVALID_CALIBRATION_LEDGER_PROTOCOL_VERSION_V1}`",
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
        "- `calibration_ledger_metadata_only_no_runtime_no_output_no_authority`",
        "- `one_family_only_calibration_ledger`",
        "- `no_engine_execution`",
        "- `no_scoring_or_judging`",
        "- `no_final_answer_or_user_facing_reply_output`",
        "- `no_proof_open_problem_scientific_or_official_claims`",
        "- `chat_responder_not_called`",
        "- `provider_model_search_advisor_not_called`",
        "- `dot_weslr_io_not_performed`",
        f"- next_lane: `{CALIBRATION_LEDGER_NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_calibration_ledger_exploratory_case_markdown_v1(case: Mapping[str, Any]) -> str:
    """Render safe internal CALIBRATION_LEDGER Markdown only after validation."""

    validation = validate_calibration_ledger_exploratory_case_v1(case)
    if validation["valid"] is not True:
        return _blocked_markdown(validation)

    summary = summarize_calibration_ledger_exploratory_case_v1(case)
    shared_markdown = render_cognitive_gym_exploratory_case_markdown_v1(case)
    lines = [
        "# WESLR CALIBRATION_LEDGER Exploratory Helper V1",
        "",
        "## Calibration Status",
        f"- case_id: `{summary['case_id']}`",
        f"- case_family: `{summary['case_family']}`",
        f"- engine_name: `{summary['engine_name']}`",
        f"- calibration_status: `{summary['calibration_status']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- validation_status: `{summary['validation_status']}`",
        f"- calibration_metadata_fields_present_count: `{summary['calibration_metadata_fields_present_count']}`",
        "",
        "## Safety Notes",
        "- `safe_markdown_is_internal_metadata_only`",
        "- `safe_markdown_is_not_user_facing_output`",
        "- `safe_markdown_is_not_reply_payload`",
        "- `safe_markdown_is_not_final_answer_prose`",
        "- `calibration_labels_are_not_scores_or_judge_decisions`",
        "- `external_validation_required_before_public_final_or_official_claims`",
        "",
        "## Shared Exploratory Case Summary",
    ]
    for line in shared_markdown.splitlines():
        if line.startswith("# "):
            continue
        if line.strip():
            lines.append(line)
    return "\n".join(lines) + "\n"


def to_calibration_ledger_exploratory_case_json_safe_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe CALIBRATION_LEDGER metadata or safe blocked wrapper."""

    validation = validate_calibration_ledger_exploratory_case_v1(case)
    if validation["valid"] is True:
        return to_cognitive_gym_exploratory_case_json_safe_v1(case)
    wrapper = _blocked_case(validation["blocked_reason_labels"] or ["invalid_or_unsafe_calibration_ledger_metadata"])
    wrapper["protocol_version"] = INVALID_CALIBRATION_LEDGER_PROTOCOL_VERSION_V1
    wrapper["blocked"] = True
    wrapper["blocked_reason_labels"] = _safe_labels(validation["blocked_reason_labels"] or ["invalid_or_unsafe_calibration_ledger_metadata"])
    wrapper["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(wrapper)
