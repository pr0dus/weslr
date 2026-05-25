"""WESLR UNKNOWN ENGINE metadata helpers V1.

Helper-only, metadata-only, deterministic, in-memory UNKNOWN ENGINE helpers
backed by the shared CognitiveGymRun protocol. This module does not execute
UNKNOWN ENGINE, CognitiveGymRun, Cognitive Gym, runtime behavior, providers,
models, search, advisors, ChatResponder/respond_chat/generate_chat, .weslr IO,
feature flags, judges/scores, official claims, reply output, final-answer
prose, prediction output, future-certainty claims, open-problem solution
claims, result artifacts, or authority grants.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping

from weslr.cognitive_gym_run_protocol import (
    REQUIRED_COGNITIVE_GYM_RUN_FIELDS,
    REQUIRED_DENIED_AUTHORITY_FIELDS,
    SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS,
    build_cognitive_gym_run_v1,
    render_cognitive_gym_run_markdown_v1,
    summarize_cognitive_gym_run_v1,
    to_cognitive_gym_run_json_safe_v1,
    validate_cognitive_gym_run_v1,
)

UNKNOWN_ENGINE_NAME_V1 = "UNKNOWN_ENGINE"
UNKNOWN_ENGINE_VERSION_LABEL_V1 = "unknown_engine_helpers_metadata_v1"
UNKNOWN_ENGINE_DEFAULT_CHALLENGE_TRACK_V1 = "UNKNOWN / uncertainty"
UNKNOWN_ENGINE_NEXT_LANE_V1 = "REVIEW_UNKNOWN_ENGINE_HELPERS_IMPLEMENTATION_V1"

_UNKNOWN_ENGINE_METADATA_KEYS = (
    "missing_evidence_labels",
    "assumption_labels",
    "safe_next_observation_labels",
    "evidence_change_labels",
    "falsification_test_labels",
    "risk_boundary_labels",
    "limitation_labels",
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
    "user_facing",
    "sendable_reply",
    "actual_reply_body",
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
    "private_indicator_blocked": ("private content:", "confidential:", "secret:", "api key", "password:"),
    "runtime_output_indicator_blocked": ("runtime output:", "runtime trace:", "live runtime output:"),
    "user_facing_output_indicator_blocked": ("user-facing output:", "user facing output:", "user-facing answer:", "user facing answer:"),
    "reply_output_indicator_blocked": ("reply output:", "reply_output:", "sendable reply text:", "actual reply body:"),
    "preview_output_indicator_blocked": ("preview output:", "preview_output:", "reply preview:"),
    "final_answer_prose_indicator_blocked": ("final-answer prose", "final answer prose", "final answer:", "final_answer:"),
    "answer_draft_indicator_blocked": ("answer draft:", "answer_draft:", "draft answer:"),
    "chat_responder_indicator_blocked": ("chatresponder", "chat responder", "respond_chat", "generate_chat"),
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
    "dot_weslr_io_indicator_blocked": (".weslr read", ".weslr write", "dot_weslr_read", "dot_weslr_write"),
    "feature_flag_indicator_blocked": ("feature_flag_enabled=true", "enable feature flag"),
    "judges_scores_indicator_blocked": ("judge decision:", "official score:", "score: 100", "judges created"),
    "official_claim_indicator_blocked": (
        "official benchmark",
        "official iq",
        "passed the turing test",
        "certified product-ready",
        "product readiness",
    ),
    "open_problem_solution_claim_blocked": (
        "open-problem solution",
        "open problem solution",
        "erdős solved",
        "erdos solved",
        "millennium solved",
        "solved the open problem",
    ),
    "future_certainty_claim_blocked": ("future certainty", "guaranteed future", "certain future", "prophecy", "oracle"),
    "prediction_authority_blocked": ("prediction authority granted", "prediction_authority_granted=true"),
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


def _detect_unsafe_input(value: Any) -> list[str]:
    reasons: list[str] = []
    if not _is_json_safe(value):
        _append_unique(reasons, "non_json_safe_input_blocked")
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        allowed_keys = {
            *(field.lower() for field in REQUIRED_COGNITIVE_GYM_RUN_FIELDS),
            *(field.lower() for field in REQUIRED_DENIED_AUTHORITY_FIELDS),
            *(field.lower() for field in _UNKNOWN_ENGINE_METADATA_KEYS),
            "engine_specific_metadata",
            "unknown_engine_metadata",
            "uncertainty_map_labels",
            "metadata_only",
            "internal_only",
            "helper_only",
            "cognitive_gym_run_backed",
            "unknown_engine_metadata_only",
            "no_runtime_paths",
            "not_user_visible",
            "validation_before_rendering",
            "safe_markdown_internal_review_only",
            "json_safe_metadata_only",
            "no_prediction_grant",
            "no_future_grant",
            "no_open_problem_claim",
            "no_official_statement",
            "risk_boundary_labels",
            "limitation_labels",
        }
        if key not in allowed_keys:
            for fragment in _FORBIDDEN_KEY_FRAGMENTS:
                if fragment in key:
                    _append_unique(reasons, f"unsupported_indicator_blocked:{fragment}")
        if isinstance(item, str):
            lowered = item.lower()
            for label, markers in _TEXT_MARKERS.items():
                if any(marker in lowered for marker in markers):
                    _append_unique(reasons, label)
    return reasons


def _merge_metadata(metadata: Mapping[str, Any] | None, overrides: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if metadata is None:
        source: dict[str, Any] = {}
    elif isinstance(metadata, Mapping):
        source = dict(metadata)
    else:
        return {}, ["input_metadata_not_mapping"]
    source.update(dict(overrides))
    return source, []


def _boundary_status(risk_boundaries: Any = None, limitations: Any = None) -> dict[str, Any]:
    return {
        "metadata_only": True,
        "internal_only": True,
        "helper_only": True,
        "cognitive_gym_run_backed": True,
        "unknown_engine_metadata_only": True,
        "no_runtime_paths": True,
        "not_user_visible": True,
        "validation_before_rendering": True,
        "safe_markdown_internal_review_only": True,
        "json_safe_metadata_only": True,
        "no_prediction_grant": True,
        "no_future_grant": True,
        "no_open_problem_claim": True,
        "no_official_statement": True,
        "risk_boundary_labels": _safe_labels(risk_boundaries),
        "limitation_labels": _safe_labels(limitations),
    }


def _engine_specific_metadata(source: Mapping[str, Any]) -> dict[str, Any]:
    metadata = {
        "missing_evidence_labels": _safe_labels(source.get("missing_evidence")),
        "assumption_labels": _safe_labels(source.get("branch_assumptions")),
        "safe_next_observation_labels": _safe_labels(source.get("safe_next_observations")),
        "evidence_change_labels": _safe_labels(source.get("evidence_change_labels")),
        "falsification_test_labels": _safe_labels(source.get("falsification_tests")),
        "risk_boundary_labels": _safe_labels(source.get("risk_boundaries")),
        "limitation_labels": _safe_labels(source.get("limitations")),
    }
    if isinstance(source.get("uncertainty_map"), Mapping):
        metadata["uncertainty_map_labels"] = _json_safe(source["uncertainty_map"])
    elif source.get("uncertainty_map") is not None:
        metadata["uncertainty_map_labels"] = _safe_labels(source.get("uncertainty_map"))
    if isinstance(source.get("engine_specific_metadata"), Mapping):
        existing = source["engine_specific_metadata"].get("unknown_engine_metadata")
        if isinstance(existing, Mapping):
            for key in _UNKNOWN_ENGINE_METADATA_KEYS:
                if key in existing:
                    metadata[key] = _safe_labels(existing[key])
    return {"unknown_engine_metadata": metadata}


def _blocked_run(reason_labels: list[str]) -> dict[str, Any]:
    run = build_cognitive_gym_run_v1(
        engine_name=UNKNOWN_ENGINE_NAME_V1,
        engine_version_label=UNKNOWN_ENGINE_VERSION_LABEL_V1,
        challenge_track=UNKNOWN_ENGINE_DEFAULT_CHALLENGE_TRACK_V1,
        input_state="blocked_unknown_engine_metadata_only",
        boundary_status=_boundary_status(),
        blocked=True,
        blocked_reason_labels=_safe_labels(reason_labels),
        visible_risks=[
            "unknown-engine-helper-design-is-not-implementation-authority",
            "unknown-engine-helper-design-is-not-execution-authority",
            "cognitive-gym-run-metadata-is-not-prediction-authority",
            "branch-labels-are-not-future-certainty",
            "safe-markdown-is-not-user-facing-answer-text",
            "json-safe-metadata-is-not-reply-payload",
            "frontier-open-problem-language-is-not-solution-evidence",
        ],
        followups=["review_unknown_engine_helpers_implementation_v1"],
        next_lane=UNKNOWN_ENGINE_NEXT_LANE_V1,
        engine_specific_metadata={"unknown_engine_metadata": {key: [] for key in _UNKNOWN_ENGINE_METADATA_KEYS}},
    )
    run["blocked"] = True
    run["blocked_reason_labels"] = _safe_labels(reason_labels + run.get("blocked_reason_labels", []))
    run["validation_status"] = "blocked_invalid_or_unsafe_metadata_labels_only"
    return _json_safe(run)


def build_unknown_engine_run_v1(metadata: Mapping[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Build metadata-only UNKNOWN ENGINE CognitiveGymRun data.

    The builder maps UNKNOWN ENGINE labels into the shared CognitiveGymRun shape
    and never executes any engine, runtime, provider/model/search/advisor path,
    ChatResponder path, .weslr IO, output creation, or authority grant.
    """

    source, early_reasons = _merge_metadata(metadata, overrides)
    if early_reasons:
        return _blocked_run(early_reasons)

    unsafe_reasons = _detect_unsafe_input(source)
    if unsafe_reasons:
        return _blocked_run(unsafe_reasons)

    missing_evidence = _safe_labels(source.get("missing_evidence"))
    falsification_tests = _safe_labels(source.get("falsification_tests"))
    evidence_change_labels = _safe_labels(source.get("evidence_change_labels"))
    risk_boundaries = _safe_labels(source.get("risk_boundaries"))
    limitations = _safe_labels(source.get("limitations"))
    branch_likelihood_labels = _safe_labels(source.get("branch_likelihood_labels"))

    unknowns = _safe_labels(source.get("unknowns")) + [label for label in missing_evidence if label not in _safe_labels(source.get("unknowns"))]
    invalidation_signals = []
    for label in missing_evidence + falsification_tests + evidence_change_labels:
        _append_unique(invalidation_signals, label)

    uncertainty_parts = _safe_labels(source.get("uncertainty"))
    uncertainty_map = source.get("uncertainty_map")
    if isinstance(uncertainty_map, Mapping):
        uncertainty_parts.extend(f"{_safe_label(key)}={_safe_label(value)}" for key, value in uncertainty_map.items())
    else:
        uncertainty_parts.extend(_safe_labels(uncertainty_map))
    uncertainty_parts.extend(branch_likelihood_labels)
    uncertainty = "; ".join(uncertainty_parts) if uncertainty_parts else "unknown_engine_uncertainty_metadata_only"

    confidence = "; ".join(branch_likelihood_labels) if branch_likelihood_labels else "qualitative_confidence_not_scored_metadata_only"
    correction = "; ".join(evidence_change_labels) if evidence_change_labels else "no_correction_metadata_only"
    compressed_lesson = _safe_label(source.get("compressed_lesson", "unknown_engine_compressed_lesson_metadata_only"))

    visible_risks = [
        "unknown-engine-helper-metadata-as-execution-authority",
        "cognitive-gym-run-metadata-as-prediction-authority",
        "branch-labels-as-future-certainty",
        "safe-markdown-as-user-facing-answer-text",
        "json-safe-metadata-as-reply-payload",
        "frontier-open-problem-language-as-solution-evidence",
        "validation-pass-as-intelligence-product-runtime-official-evaluation-authority",
        "occ-openclaw-is-not-deployed-weslr",
    ]
    for label in risk_boundaries + limitations:
        _append_unique(visible_risks, label)

    run = build_cognitive_gym_run_v1(
        engine_name=UNKNOWN_ENGINE_NAME_V1,
        engine_version_label=UNKNOWN_ENGINE_VERSION_LABEL_V1,
        challenge_track=_safe_label(source.get("challenge_track", UNKNOWN_ENGINE_DEFAULT_CHALLENGE_TRACK_V1)),
        input_state=_safe_label(source.get("input_state", "unknown_engine_internal_metadata_input_state")),
        observations=_safe_labels(source.get("observations")),
        knowns=_safe_labels(source.get("knowns")),
        unknowns=unknowns,
        hypotheses=_safe_labels(source.get("branch_assumptions")) + _safe_labels(source.get("hypotheses")),
        predictions_or_branch_labels=_safe_labels(source.get("possible_future_branches")),
        confidence=confidence,
        uncertainty=uncertainty,
        invalidation_signals=invalidation_signals,
        reveal_or_outcome="not_revealed_metadata_only",
        correction=correction,
        compressed_lesson=compressed_lesson,
        boundary_status=_boundary_status(risk_boundaries, limitations),
        visible_risks=visible_risks,
        followups=_safe_labels(source.get("safe_next_observations")) or ["review_unknown_engine_helpers_implementation_v1"],
        next_lane=UNKNOWN_ENGINE_NEXT_LANE_V1,
        engine_specific_metadata=_engine_specific_metadata(source),
    )
    return _json_safe(run)


def validate_unknown_engine_run_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Validate UNKNOWN ENGINE CognitiveGymRun metadata without raising."""

    base = validate_cognitive_gym_run_v1(run)
    blocked_reason_labels = _safe_labels(base.get("blocked_reason_labels", []))
    invalid_fields = _safe_labels(base.get("invalid_fields", []))
    if not isinstance(run, Mapping):
        return {**base, "unknown_engine_valid": False}

    if run.get("engine_name") != UNKNOWN_ENGINE_NAME_V1:
        _append_unique(invalid_fields, "engine_name")
        _append_unique(blocked_reason_labels, "unknown_engine_engine_name_required")
    if run.get("challenge_track") not in SUPPORTED_COGNITIVE_GYM_CHALLENGE_TRACKS:
        _append_unique(invalid_fields, "challenge_track")
        _append_unique(blocked_reason_labels, "unknown_engine_challenge_track_unsupported")

    denied = run.get("denied_authority_fields")
    denied_authority_violations = _safe_labels(base.get("denied_authority_violations", []))
    if isinstance(denied, Mapping):
        for field in REQUIRED_DENIED_AUTHORITY_FIELDS:
            if denied.get(field) is not False:
                _append_unique(denied_authority_violations, f"denied_authority_field_not_false:{field}")

    engine_specific = run.get("engine_specific_metadata")
    contained = isinstance(engine_specific, Mapping) and isinstance(engine_specific.get("unknown_engine_metadata"), Mapping)
    if not contained:
        _append_unique(invalid_fields, "engine_specific_metadata")
        _append_unique(blocked_reason_labels, "unknown_engine_metadata_not_contained")

    unsafe_reasons = _detect_unsafe_input(run)
    for reason in unsafe_reasons:
        _append_unique(blocked_reason_labels, reason)

    valid = bool(base.get("valid")) and not blocked_reason_labels and not invalid_fields and not denied_authority_violations and contained
    return {
        **base,
        "valid": valid,
        "unknown_engine_valid": valid,
        "blocked": not valid,
        "blocked_reason_labels": _safe_labels(blocked_reason_labels),
        "invalid_fields": _safe_labels(invalid_fields),
        "denied_authority_violations": _safe_labels(denied_authority_violations),
        "engine_specific_metadata_contained": contained,
        "safe_to_render_markdown": valid,
    }


def summarize_unknown_engine_run_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact JSON-safe UNKNOWN ENGINE metadata summary."""

    validation = validate_unknown_engine_run_v1(run)
    summary = summarize_cognitive_gym_run_v1(run if isinstance(run, Mapping) else {})
    return _json_safe(
        {
            **summary,
            "unknown_engine_valid": validation["unknown_engine_valid"],
            "blocked": validation["blocked"],
            "blocked_reason_labels": validation["blocked_reason_labels"],
            "engine_specific_metadata_contained": validation["engine_specific_metadata_contained"],
            "denied_authority_fields_false": not validation["denied_authority_violations"],
        }
    )


def render_unknown_engine_run_markdown_v1(run: Mapping[str, Any]) -> str:
    """Render bounded internal Markdown only after UNKNOWN ENGINE validation."""

    validation = validate_unknown_engine_run_v1(run)
    if validation["valid"] is not True:
        safe = _blocked_run(validation["blocked_reason_labels"] or ["invalid_unknown_engine_metadata"])
        return render_cognitive_gym_run_markdown_v1(safe).replace(
            "WESLR CognitiveGymRun Protocol Helper V1", "WESLR UNKNOWN ENGINE Helper V1"
        )

    markdown = render_cognitive_gym_run_markdown_v1(run).replace(
        "WESLR CognitiveGymRun Protocol Helper V1", "WESLR UNKNOWN ENGINE Helper V1"
    )
    extra = [
        "",
        "## UNKNOWN ENGINE Boundary Summary",
        "- `metadata_only_unknown_engine_helpers`",
        "- `cognitive_gym_run_backed`",
        "- `not_user_facing_answer_text`",
        "- `not_reply_payload`",
        "- `not_final_answer_prose`",
        "- `no_prediction_authority`",
        "- `no_future_certainty_claim`",
        "- `no_open_problem_solution_claim`",
        "- `no_official_claim`",
    ]
    return markdown.rstrip() + "\n" + "\n".join(extra) + "\n"


def to_unknown_engine_run_json_safe_v1(run: Mapping[str, Any]) -> dict[str, Any]:
    """Return deterministic JSON-safe UNKNOWN ENGINE CognitiveGymRun metadata."""

    validation = validate_unknown_engine_run_v1(run)
    if validation["valid"] is not True:
        safe = _blocked_run(validation["blocked_reason_labels"] or ["invalid_unknown_engine_metadata"])
        return to_cognitive_gym_run_json_safe_v1(safe)
    safe = to_cognitive_gym_run_json_safe_v1(run)
    if isinstance(safe.get("denied_authority_fields"), Mapping):
        safe["denied_authority_fields"] = {field: False for field in REQUIRED_DENIED_AUTHORITY_FIELDS}
    return _json_safe(safe)


__all__ = (
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "summarize_unknown_engine_run_v1",
    "render_unknown_engine_run_markdown_v1",
    "to_unknown_engine_run_json_safe_v1",
)
