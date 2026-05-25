"""WESLR Cognitive Gym exploratory case metadata helpers V1.

Helper-only, metadata-only, deterministic, in-memory helpers for shared
Cognitive Gym exploratory case records. This module does not implement engines,
engine-specific helpers, challenge execution, runtime behavior, providers,
models, search, advisors, ChatResponder/respond_chat/generate_chat, .weslr IO,
scoring, judging, official claims, reply output, final answers, proof claims,
open-problem solution claims, scientific discovery claims, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
import re
from typing import Any, Mapping

COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1 = "cognitive_gym_exploratory_case_v1"
COGNITIVE_GYM_EXPLORATORY_CASE_SCHEMA_VERSION_V1 = "cognitive_gym_exploratory_case_schema_v1"
INVALID_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1 = "cognitive_gym_exploratory_case_v1_invalid"
NEXT_LANE_V1 = "REVIEW_COGNITIVE_GYM_EXPLORATORY_CASE_HELPERS_IMPLEMENTATION_V1"

SUPPORTED_LIFECYCLE_LABELS_V1 = (
    "case_defined",
    "intake_validated",
    "exploratory_not_started",
    "exploratory_candidate",
    "partial_structure_found",
    "failed_attempt_recorded",
    "invalidated",
    "correction_recorded",
    "needs_external_review",
    "externally_validated",
    "claim_forbidden_without_validation",
    "blocked_by_boundary",
)

REQUIRED_DENIED_AUTHORITY_FIELDS_V1 = (
    "runtime_authority",
    "chat_authority",
    "final_answer_authority",
    "proof_claim_authority",
    "open_problem_solved_claim_authority",
    "scientific_discovery_claim_authority",
    "official_benchmark_authority",
    "turing_test_claim_authority",
    "intelligence_certification_authority",
    "consciousness_claim_authority",
    "provider_call_authority",
    "search_call_authority",
    "persistence_authority",
    "scoring_authority",
    "judge_authority",
    "public_release_authority",
)

REQUIRED_CASE_FIELDS_V1 = (
    "protocol_version",
    "schema_version",
    "case_id",
    "case_family",
    "engine_name",
    "domain",
    "lifecycle_label",
    "problem_statement_metadata",
    "input_state",
    "assumptions",
    "constraints",
    "observations",
    "hypotheses",
    "candidate_structures",
    "attempted_approaches",
    "failed_paths",
    "counterexamples_or_invalidation_signals",
    "predictions_or_branch_labels",
    "confidence",
    "uncertainty",
    "reveal_or_outcome",
    "correction",
    "compressed_lesson",
    "boundary_status",
    "denied_authority_fields",
    "validation_status",
    "review_requirements",
    "next_allowed_steps",
    "blocked",
    "blocked_reason_labels",
    "safe_summary",
    "next_lane",
)

_LIST_FIELDS_V1 = (
    "assumptions",
    "constraints",
    "observations",
    "hypotheses",
    "candidate_structures",
    "attempted_approaches",
    "failed_paths",
    "counterexamples_or_invalidation_signals",
    "predictions_or_branch_labels",
    "review_requirements",
    "next_allowed_steps",
    "blocked_reason_labels",
)

_FORBIDDEN_KEY_FRAGMENTS = (
    "raw_private",
    "private_content",
    "personal_sensitive",
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
    "runtime_activation",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "user_facing",
    "reply_output",
    "sendable_reply",
    "actual_reply_body",
    "final_answer",
    "proof_claim",
    "open_problem_solution",
    "scientific_discovery",
    "official_benchmark",
    "turing_test",
    "intelligence_certification",
    "consciousness_claim",
    "score",
    "judge",
    "authority_grant",
    "public_release",
)

_TEXT_MARKERS = {
    "raw_private_content_indicator_blocked": (
        "raw private content:",
        "private content:",
        "personal sensitive data:",
        "confidential:",
        "secret:",
        "api key",
        "password:",
    ),
    "hidden_prompt_indicator_blocked": ("hidden prompt:", "system prompt:", "developer prompt:", "raw prompt:"),
    "answer_key_indicator_blocked": ("answer key:", "hidden answer key", "correct answer key"),
    "protected_benchmark_indicator_blocked": ("protected benchmark", "benchmark item:", "private eval item"),
    "provider_model_search_advisor_output_indicator_blocked": (
        "provider output:",
        "provider response:",
        "model output:",
        "llm output:",
        "search output:",
        "search result:",
        "advisor output:",
        "advisor response:",
    ),
    "dot_weslr_io_indicator_blocked": (".weslr read", ".weslr write", "dot_weslr_read", "dot_weslr_write"),
    "runtime_output_indicator_blocked": ("runtime output:", "runtime trace:", "runtime activation", "wire runtime"),
    "final_answer_user_facing_reply_output_indicator_blocked": (
        "final answer:",
        "final-answer prose",
        "reply to user:",
        "send to user:",
        "user-facing answer:",
        "sendable reply text:",
        "actual reply body:",
    ),
    "proof_open_problem_scientific_claim_indicator_blocked": (
        "proof claim:",
        "we proved",
        "weslr solved",
        "open-problem solution",
        "open problem solution",
        "scientific discovery claim",
        "new scientific discovery",
    ),
    "official_claim_indicator_blocked": (
        "official benchmark",
        "passed the turing test",
        "intelligence certification",
        "certified intelligent",
        "consciousness claim",
        "official readiness",
    ),
    "scoring_judging_indicator_blocked": ("score:", "official score:", "judge decision:", "judges created"),
    "authority_grant_indicator_blocked": ("authority granted", "_authority=true", "public release authorized"),
}

_SAFE_LITERAL_STRINGS = {
    COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1,
    COGNITIVE_GYM_EXPLORATORY_CASE_SCHEMA_VERSION_V1,
    INVALID_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1,
    NEXT_LANE_V1,
    "validation_pending_metadata_quality_only",
    "validation_pass_metadata_quality_only",
    "blocked_invalid_or_unsafe_metadata_labels_only",
    "metadata_only_no_runtime_no_output_no_authority",
    "problem_metadata_only",
    "input_metadata_only",
    "not_scored_metadata_only",
    "uncertainty_metadata_required",
    "not_revealed_metadata_only",
    "no_correction_metadata_only",
    "no_compressed_lesson_metadata_only",
    "safe_internal_summary_metadata_only",
    *SUPPORTED_LIFECYCLE_LABELS_V1,
    *REQUIRED_DENIED_AUTHORITY_FIELDS_V1,
    *REQUIRED_CASE_FIELDS_V1,
}

_SAFE_NEXT_LANE_RE = re.compile(r"^[A-Z0-9_]{3,140}_V1$")
_SAFE_LABEL_RE = re.compile(r"^[A-Za-z0-9_./:;=,() \-]{0,240}$")


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
    return str(value).replace("`", "").replace("\n", " ")[:220]


def _safe_labels(value: Any) -> list[str]:
    labels: list[str] = []
    for item in _as_list(value):
        _append_unique(labels, _safe_label(item))
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
    allowed_keys = {
        *(field.lower() for field in REQUIRED_CASE_FIELDS_V1),
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
        "validation_before_rendering": True,
        "blocked_metadata_behavior": True,
        "claim_ladder_preserved": True,
        "external_validation_required_for_claims": True,
    }


def _base_case() -> dict[str, Any]:
    return {
        "protocol_version": COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1,
        "schema_version": COGNITIVE_GYM_EXPLORATORY_CASE_SCHEMA_VERSION_V1,
        "case_id": "exploratory_case_metadata_v1",
        "case_family": "shared_cognitive_gym_exploratory_case",
        "engine_name": "SHARED_COGNITIVE_GYM_EXPLORATORY_CASE",
        "domain": "general_exploratory_problem_work",
        "lifecycle_label": "case_defined",
        "problem_statement_metadata": "problem_metadata_only",
        "input_state": "input_metadata_only",
        "assumptions": [],
        "constraints": [],
        "observations": [],
        "hypotheses": [],
        "candidate_structures": [],
        "attempted_approaches": [],
        "failed_paths": [],
        "counterexamples_or_invalidation_signals": [],
        "predictions_or_branch_labels": [],
        "confidence": "not_scored_metadata_only",
        "uncertainty": "uncertainty_metadata_required",
        "reveal_or_outcome": "not_revealed_metadata_only",
        "correction": "no_correction_metadata_only",
        "compressed_lesson": "no_compressed_lesson_metadata_only",
        "boundary_status": _default_boundary_status(),
        "denied_authority_fields": {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1},
        "validation_status": "validation_pending_metadata_quality_only",
        "review_requirements": ["external_validation_required_before_public_final_or_official_claims"],
        "next_allowed_steps": ["review_cognitive_gym_exploratory_case_helpers_implementation_v1"],
        "blocked": False,
        "blocked_reason_labels": [],
        "safe_summary": "safe_internal_summary_metadata_only",
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


def build_cognitive_gym_exploratory_case_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Build one shared metadata-only Cognitive Gym exploratory case record."""

    source, early_reasons = _merge_input(metadata, overrides)
    case = _base_case()
    if early_reasons:
        case["blocked"] = True
        case["blocked_reason_labels"] = early_reasons
        case["lifecycle_label"] = "blocked_by_boundary"
        case["boundary_status"] = "blocked_by_boundary"
        case["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        return case

    input_reasons = _detect_unsafe_content(source)
    if not _is_json_safe(source):
        _append_unique(input_reasons, "non_json_safe_input_detected")

    for field in REQUIRED_CASE_FIELDS_V1:
        if field in source and field != "denied_authority_fields":
            case[field] = _json_safe(source[field])

    for field in _LIST_FIELDS_V1:
        if field in case:
            case[field] = _json_safe(_as_list(case[field]))

    if isinstance(source.get("denied_authority_fields"), Mapping):
        denied = {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1}
        for key, value in source["denied_authority_fields"].items():
            denied[str(key)] = _json_safe(value)
        case["denied_authority_fields"] = denied

    if input_reasons:
        case["blocked"] = True
        case["blocked_reason_labels"] = _safe_labels(input_reasons)
        case["lifecycle_label"] = "blocked_by_boundary"

    validation = validate_cognitive_gym_exploratory_case_v1(case)
    case["blocked"] = validation["blocked"]
    case["blocked_reason_labels"] = _safe_labels(case.get("blocked_reason_labels", []) + validation.get("blocked_reason_labels", []))
    if validation["valid"]:
        case["validation_status"] = "validation_pass_metadata_quality_only"
    else:
        case["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        if case.get("boundary_status") != "blocked_by_boundary":
            case["boundary_status"] = _json_safe(case.get("boundary_status", _default_boundary_status()))
    return _json_safe(case)


def validate_cognitive_gym_exploratory_case_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Validate shared exploratory case metadata and return validation metadata only."""

    if not isinstance(case, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "blocked_reason_labels": ["case_not_mapping"],
            "missing_required_fields": list(REQUIRED_CASE_FIELDS_V1),
            "invalid_fields": ["case"],
            "unsupported_lifecycle_label": None,
            "denied_authority_violations": [],
            "json_safe": False,
            "safe_to_render_markdown": False,
        }

    blocked_reason_labels: list[str] = []
    invalid_fields: list[str] = []
    missing_required_fields = [field for field in REQUIRED_CASE_FIELDS_V1 if field not in case]
    for field in missing_required_fields:
        _append_unique(blocked_reason_labels, f"missing_required_field:{field}")

    if case.get("protocol_version") != COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1:
        invalid_fields.append("protocol_version")
        _append_unique(blocked_reason_labels, "protocol_version_mismatch")
    if case.get("schema_version") != COGNITIVE_GYM_EXPLORATORY_CASE_SCHEMA_VERSION_V1:
        invalid_fields.append("schema_version")
        _append_unique(blocked_reason_labels, "schema_version_mismatch")

    unsupported_lifecycle_label = None
    if case.get("lifecycle_label") not in SUPPORTED_LIFECYCLE_LABELS_V1:
        unsupported_lifecycle_label = case.get("lifecycle_label")
        invalid_fields.append("lifecycle_label")
        _append_unique(blocked_reason_labels, "unsupported_lifecycle_label")

    if not case.get("boundary_status"):
        invalid_fields.append("boundary_status")
        _append_unique(blocked_reason_labels, "missing_boundary_status")
    if not case.get("validation_status"):
        invalid_fields.append("validation_status")
        _append_unique(blocked_reason_labels, "missing_validation_status")
    if not case.get("uncertainty"):
        invalid_fields.append("uncertainty")
        _append_unique(blocked_reason_labels, "missing_uncertainty")

    denied = case.get("denied_authority_fields")
    denied_authority_violations: list[str] = []
    if not isinstance(denied, Mapping):
        invalid_fields.append("denied_authority_fields")
        _append_unique(blocked_reason_labels, "denied_authority_fields_not_mapping")
        denied = {}
    for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1:
        if field not in denied:
            denied_authority_violations.append(f"missing_denied_authority_field:{field}")
        elif denied.get(field) is not False:
            denied_authority_violations.append(f"denied_authority_field_not_false:{field}")
    for field in denied_authority_violations:
        _append_unique(blocked_reason_labels, field)

    if not isinstance(case.get("blocked"), bool):
        invalid_fields.append("blocked")
        _append_unique(blocked_reason_labels, "blocked_not_boolean")
    for field in _LIST_FIELDS_V1:
        if field in case and not isinstance(case.get(field), list):
            invalid_fields.append(field)
            _append_unique(blocked_reason_labels, f"{field}_not_list")

    next_lane = case.get("next_lane")
    if not isinstance(next_lane, str) or not _SAFE_NEXT_LANE_RE.fullmatch(next_lane):
        invalid_fields.append("next_lane")
        _append_unique(blocked_reason_labels, "next_lane_not_safe_label")

    for field in ("case_id", "case_family", "engine_name", "domain"):
        value = case.get(field)
        if not isinstance(value, str) or not value or not _SAFE_LABEL_RE.fullmatch(value):
            invalid_fields.append(field)
            _append_unique(blocked_reason_labels, f"{field}_not_safe_label")

    json_safe = _is_json_safe(case)
    if not json_safe:
        _append_unique(blocked_reason_labels, "non_json_safe_value_detected")

    for label in _detect_unsafe_content(case):
        _append_unique(blocked_reason_labels, label)

    if case.get("blocked") is True:
        for label in _safe_labels(case.get("blocked_reason_labels", [])):
            _append_unique(blocked_reason_labels, label)

    valid = not blocked_reason_labels and not invalid_fields and not missing_required_fields and json_safe
    return {
        "valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(blocked_reason_labels),
        "missing_required_fields": missing_required_fields,
        "invalid_fields": _safe_labels(invalid_fields),
        "unsupported_lifecycle_label": unsupported_lifecycle_label,
        "denied_authority_violations": _safe_labels(denied_authority_violations),
        "json_safe": json_safe,
        "safe_to_render_markdown": valid,
    }


def summarize_cognitive_gym_exploratory_case_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact safe summary for one exploratory case metadata object."""

    validation = validate_cognitive_gym_exploratory_case_v1(case)
    if not isinstance(case, Mapping):
        case = {}
    return {
        "protocol_version": case.get("protocol_version"),
        "schema_version": case.get("schema_version"),
        "case_id": case.get("case_id"),
        "case_family": case.get("case_family"),
        "engine_name": case.get("engine_name"),
        "domain": case.get("domain"),
        "lifecycle_label": case.get("lifecycle_label"),
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "validation_status": "validation_pass_metadata_quality_only" if validation["valid"] else "blocked_invalid_or_unsafe_metadata_labels_only",
        "blocked_reason_labels": validation["blocked_reason_labels"],
        "boundary_status": _json_safe(case.get("boundary_status", {})),
        "denied_authority_fields_false": isinstance(case.get("denied_authority_fields"), Mapping) and not validation["denied_authority_violations"],
        "counts": {
            "assumptions": len(case.get("assumptions", [])) if isinstance(case.get("assumptions"), list) else 0,
            "constraints": len(case.get("constraints", [])) if isinstance(case.get("constraints"), list) else 0,
            "observations": len(case.get("observations", [])) if isinstance(case.get("observations"), list) else 0,
            "hypotheses": len(case.get("hypotheses", [])) if isinstance(case.get("hypotheses"), list) else 0,
            "candidate_structures": len(case.get("candidate_structures", [])) if isinstance(case.get("candidate_structures"), list) else 0,
            "attempted_approaches": len(case.get("attempted_approaches", [])) if isinstance(case.get("attempted_approaches"), list) else 0,
            "failed_paths": len(case.get("failed_paths", [])) if isinstance(case.get("failed_paths"), list) else 0,
            "invalidation_signals": len(case.get("counterexamples_or_invalidation_signals", [])) if isinstance(case.get("counterexamples_or_invalidation_signals"), list) else 0,
        },
        "review_requirements_count": len(case.get("review_requirements", [])) if isinstance(case.get("review_requirements"), list) else 0,
        "next_allowed_steps_count": len(case.get("next_allowed_steps", [])) if isinstance(case.get("next_allowed_steps"), list) else 0,
        "next_lane": case.get("next_lane", NEXT_LANE_V1),
    }


def _blocked_markdown(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reasons = _safe_labels(validation.get("blocked_reason_labels") or summary.get("blocked_reason_labels") or ["invalid_or_unsafe_exploratory_case_metadata"])
    lines = [
        "# WESLR Cognitive Gym Exploratory Case Helper V1",
        "",
        f"- protocol_version: `{INVALID_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1}`",
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
        "- `no_engine_or_engine_specific_helper_implementation`",
        "- `no_challenge_execution`",
        "- `no_scoring_or_judging`",
        "- `no_final_answer_or_user_facing_reply_output`",
        "- `no_proof_open_problem_scientific_or_official_claims`",
        "- `chat_responder_not_called`",
        "- `provider_model_search_advisor_not_called`",
        "- `dot_weslr_io_not_performed`",
        f"- next_lane: `{NEXT_LANE_V1}`",
    ])
    return "\n".join(lines) + "\n"


def render_cognitive_gym_exploratory_case_markdown_v1(case: Mapping[str, Any]) -> str:
    """Render safe internal Markdown only after validation."""

    validation = validate_cognitive_gym_exploratory_case_v1(case)
    summary = summarize_cognitive_gym_exploratory_case_v1(case)
    if validation["valid"] is not True:
        return _blocked_markdown(validation, summary)

    lines = [
        "# WESLR Cognitive Gym Exploratory Case Helper V1",
        "",
        "## Case Status",
        f"- protocol_version: `{summary['protocol_version']}`",
        f"- schema_version: `{summary['schema_version']}`",
        f"- case_id: `{summary['case_id']}`",
        f"- case_family: `{summary['case_family']}`",
        f"- engine_name: `{summary['engine_name']}`",
        f"- domain: `{summary['domain']}`",
        f"- lifecycle_label: `{summary['lifecycle_label']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- validation_status: `{summary['validation_status']}`",
        "",
        "## Boundary Status",
    ]
    boundary_status = summary["boundary_status"]
    if isinstance(boundary_status, Mapping):
        for key, value in boundary_status.items():
            lines.append(f"- {key}: `{value}`")
    else:
        lines.append(f"- boundary_status: `{_safe_label(boundary_status)}`")
    lines.extend(["", "## Counts"])
    for key, value in summary["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Denied Authority Fields",
    ])
    lines.extend(f"- `{field}=false`" for field in REQUIRED_DENIED_AUTHORITY_FIELDS_V1)
    lines.extend([
        "",
        "## Internal Review Safety Notes",
        "- `hypotheses_are_internal_exploratory_metadata_only`",
        "- `candidate_structures_are_internal_exploratory_metadata_only`",
        "- `safe_markdown_is_not_user_facing_output`",
        "- `safe_markdown_is_not_reply_payload`",
        "- `safe_markdown_is_not_final_answer_prose`",
        "- `validation_pass_is_metadata_quality_only`",
        "- `external_validation_required_before_public_final_or_official_claims`",
        "- `engine_specific_helpers_must_wait_for_reviewed_shared_helper_implementation`",
        "",
        "## Next Lane",
        f"- `{summary['next_lane']}`",
    ])
    return "\n".join(lines) + "\n"


def to_cognitive_gym_exploratory_case_json_safe_v1(case: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe case data or a safe blocked wrapper."""

    validation = validate_cognitive_gym_exploratory_case_v1(case)
    if validation["valid"] is not True:
        wrapper = _base_case()
        wrapper["protocol_version"] = INVALID_COGNITIVE_GYM_EXPLORATORY_CASE_PROTOCOL_VERSION_V1
        wrapper["lifecycle_label"] = "blocked_by_boundary"
        wrapper["boundary_status"] = "blocked_by_boundary"
        wrapper["blocked"] = True
        wrapper["blocked_reason_labels"] = validation["blocked_reason_labels"] or ["invalid_or_unsafe_exploratory_case_metadata"]
        wrapper["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
        return _json_safe(wrapper)
    return _json_safe(case)
