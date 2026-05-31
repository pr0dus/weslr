"""Metadata-only friction pattern miner v1.

This helper clusters safe friction cases and replay/proposal metadata into
pattern candidates that can justify replay-suite expansion or governed review.

It is pure, deterministic, import-safe, and fail-closed.

No model/provider/search/advisor calls. No runtime wiring. No state writes.
No approved proposals. No promotion. No automatic behavior mutation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha1
from typing import Any, Iterable, Mapping, Sequence

from weslr.friction_case_capture import (
    FrictionCase,
    build_initial_renderer_friction_cases_v1,
    to_friction_case_json_safe_v1,
)
from weslr.friction_replay_harness import (
    FrictionReplayCaseResult,
    FrictionReplayHarnessPacket,
    build_initial_renderer_friction_replay_v1,
    summarize_friction_replay_packet_v1,
    to_friction_replay_json_safe_v1,
    validate_friction_replay_packet_v1,
)
from weslr.friction_update_proposal_bridge import (
    FrictionUpdateProposal,
    FrictionUpdateProposalPacket,
    build_initial_renderer_friction_update_proposals_v1,
    summarize_friction_update_proposal_packet_v1,
    to_friction_update_proposal_json_safe_v1,
    validate_friction_update_proposal_packet_v1,
)

PACKET_TYPE_V1 = "friction_pattern_packet_v1"
SUMMARY_TYPE_V1 = "friction_pattern_summary_v1"

ALLOWED_PATTERN_TYPES_V1 = {
    "identity_status_pattern",
    "capability_orientation_pattern",
    "unknown_term_friction_pattern",
    "inactive_capability_boundary_pattern",
    "answer_shape_mismatch_pattern",
    "case_priority_pattern",
    "selector_priority_pattern",
    "renderer_policy_pattern",
    "behavior_pack_candidate_pattern",
}

ALLOWED_CONFIDENCE_LEVELS_V1 = {
    "single_case_low",
    "multi_case_medium",
    "replay_supported_medium",
    "proposal_supported_high",
    "proof_review_required",
}

ALLOWED_PROPOSAL_ELIGIBILITY_V1 = {
    "capture_only",
    "needs_more_cases",
    "eligible_for_replay_suite",
    "eligible_for_update_proposal",
    "eligible_for_owner_review",
    "not_eligible_boundary_risk",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
    "answer_text",
    "response_text",
    "prompt_text",
    "raw_context",
    "raw_data",
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
}

FORBIDDEN_TEXT_MARKERS_V1 = (
    ".weslr",
    "raw prompt",
    "raw answer",
    "raw response",
    "raw transcript",
    "transcript",
    "provider call",
    "model call",
    "search call",
    "advisor call",
    "runtime authority",
    "model provider",
    "auto promotion",
)

_PATTERN_ID_OVERRIDES_V1 = {
    "identity_status_pattern": "identity_status_directness_pattern",
    "capability_orientation_pattern": "capability_orientation_directness_pattern",
    "unknown_term_friction_pattern": "unknown_term_friction_preference_pattern",
    "inactive_capability_boundary_pattern": "inactive_capability_boundary_pattern",
}

_GENERALIZED_FAILURE_SUMMARIES_V1 = {
    "identity_status_pattern": "identity/self-description prompts were routed too cautiously into clarification.",
    "capability_orientation_pattern": "capability/current-ability prompts were routed too cautiously into clarification.",
    "unknown_term_friction_pattern": "unknown terms were treated as generic clarification instead of unknown/friction.",
    "inactive_capability_boundary_pattern": "inactive product capability questions were treated as generic clarification instead of a bounded capability/boundary answer.",
    "answer_shape_mismatch_pattern": "the answer shape did not match the user's requested level of directness, caution, or structure.",
    "case_priority_pattern": "the case registry prioritized the wrong case family for the incoming prompt family.",
    "selector_priority_pattern": "the selector prioritized the wrong route or family ordering for the incoming prompt family.",
    "renderer_policy_pattern": "the renderer policy was too weak or too generic for the required bounded shape.",
    "behavior_pack_candidate_pattern": "repeated friction suggests a reusable domain or capability behavior pack may be warranted.",
}

_GENERALIZED_EXPECTED_BEHAVIORS_V1 = {
    "identity_status_pattern": "direct bounded identity/status response.",
    "capability_orientation_pattern": "direct capability orientation response.",
    "unknown_term_friction_pattern": "unknown/friction branch response.",
    "inactive_capability_boundary_pattern": "direct bounded capability/boundary answer.",
    "answer_shape_mismatch_pattern": "answer shape aligned to the user's requested directness and structure.",
    "case_priority_pattern": "the correct case family is prioritized before weaker fallback families.",
    "selector_priority_pattern": "the correct selector route is prioritized before weaker fallback routes.",
    "renderer_policy_pattern": "the renderer emits the bounded policy-shape required by the prompt family.",
    "behavior_pack_candidate_pattern": "the reusable pack captures stable vocabulary, methods, shapes, and boundary rules.",
}

_MIN_REPLAY_SUITE_REQUIREMENTS_V1 = {
    "identity_status_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "overclaim_prompts",
    ),
    "capability_orientation_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "overclaim_prompts",
    ),
    "unknown_term_friction_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "language_discovery_controls",
    ),
    "inactive_capability_boundary_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "overclaim_prompts",
    ),
    "answer_shape_mismatch_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "regression_prompts",
    ),
    "case_priority_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "regression_prompts",
    ),
    "selector_priority_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "regression_prompts",
    ),
    "renderer_policy_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "regression_prompts",
    ),
    "behavior_pack_candidate_pattern": (
        "original_friction_cases",
        "neighbor_prompts",
        "paraphrase_labels",
        "boundary_prompts",
        "unrelated_controls",
        "regression_prompts",
        "domain_pack_controls",
    ),
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FrictionPatternCandidate:
    pattern_id: str
    pattern_type: str
    source_case_ids: tuple[str, ...]
    source_replay_statuses: tuple[str, ...]
    shared_mismatch_labels: tuple[str, ...]
    shared_prompt_labels: tuple[str, ...]
    shared_replay_labels: tuple[str, ...]
    target_update_areas: tuple[str, ...]
    affected_method_ids: tuple[str, ...]
    affected_shape_ids: tuple[str, ...]
    affected_case_ids: tuple[str, ...]
    affected_route_ids: tuple[str, ...]
    generalized_failure_summary: str
    generalized_expected_behavior: str
    proposal_eligibility: str
    minimum_replay_suite_requirements: tuple[str, ...]
    confidence_level: str
    owner_review_required: bool
    safe_to_apply_automatically: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FrictionPatternPacket:
    packet_type: str
    pattern_count: int
    patterns: tuple[FrictionPatternCandidate, ...]
    pattern_type_counts: dict[str, int]
    confidence_counts: dict[str, int]
    proposal_eligibility_counts: dict[str, int]
    source_case_count: int
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    proposal_created: bool
    promotion_performed: bool
    safe_metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _dedupe_preserve(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return tuple(out)


def _normalize_strings(value: Any) -> tuple[str, ...]:
    return _dedupe_preserve(_safe_text(item) for item in _as_list(value))


def _normalize_labels(value: Any) -> tuple[str, ...]:
    return _dedupe_preserve(_safe_text(item).lower().strip() for item in _as_list(value))


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    return deepcopy(value)


def _contains_any(blob: str, phrases: Sequence[str]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _contains_forbidden_marker(value: Any) -> bool:
    text = _safe_text(value).lower()
    return any(marker in text for marker in FORBIDDEN_TEXT_MARKERS_V1)


def _collect_forbidden_keys(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            if _contains_forbidden_marker(key_text):
                blocked.append(next_path)
            blocked.extend(_collect_forbidden_keys(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_collect_forbidden_keys(item, f"{path}[{index}]"))
    return blocked


# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------


def _coerce_case_record(value: Any) -> dict[str, Any]:
    if isinstance(value, FrictionCase):
        payload = asdict(value)
    elif isinstance(value, FrictionReplayCaseResult):
        payload = asdict(value)
    elif isinstance(value, FrictionUpdateProposal):
        payload = asdict(value)
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        raise ValidationError(f"unsupported_source_type: {type(value).__name__}")

    safe_metadata = payload.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        safe_metadata = {}

    actual = payload.get("actual") or {}
    expected = payload.get("expected") or {}
    if is_dataclass(actual):
        actual = asdict(actual)
    if is_dataclass(expected):
        expected = asdict(expected)

    record: dict[str, Any] = {
        "case_id": _safe_text(payload.get("case_id") or payload.get("source_case_id") or payload.get("proposal_id") or payload.get("selected_case_id") or payload.get("observed_case_id")),
        "case_type": _safe_text(payload.get("case_type") or payload.get("pattern_type") or payload.get("failure_label") or payload.get("source_replay_status") or payload.get("proposal_type") or "unknown"),
        "prompt_labels": _normalize_labels(payload.get("prompt_labels") or payload.get("turn_labels") or payload.get("replay_labels") or safe_metadata.get("prompt_labels")),
        "mismatch_labels": _normalize_labels(payload.get("mismatch_labels") or payload.get("new_mismatch_labels") or payload.get("regression_labels") or safe_metadata.get("mismatch_labels")),
        "replay_labels": _normalize_labels(payload.get("replay_labels") or payload.get("turn_labels") or safe_metadata.get("replay_labels")),
        "target_update_areas": _normalize_strings(payload.get("target_update_area") or payload.get("target_update_areas") or payload.get("proposed_update_area") or safe_metadata.get("target_update_areas")),
        "affected_method_ids": _normalize_strings(payload.get("affected_method_ids") or [payload.get("actual_method_id"), payload.get("expected_method_id"), payload.get("observed_method_id"), payload.get("selected_method_id")]),
        "affected_shape_ids": _normalize_strings(payload.get("affected_shape_ids") or [payload.get("actual_shape_id"), payload.get("expected_shape_id"), payload.get("observed_shape_id"), payload.get("selected_shape_id")]),
        "affected_case_ids": _normalize_strings(payload.get("affected_case_ids") or [payload.get("actual_case_id"), payload.get("expected_case_id"), payload.get("observed_case_id"), payload.get("selected_case_id")]),
        "affected_route_ids": _normalize_strings(payload.get("affected_route_ids") or [payload.get("actual_route_id"), payload.get("expected_route_id"), payload.get("observed_route_id"), payload.get("selected_route_id")]),
        "source_replay_status": _safe_text(payload.get("source_replay_status") or payload.get("match_status") or "not_replayed_yet"),
        "actual_route_id": _safe_text(actual.get("route_id") or payload.get("actual_route_id") or payload.get("observed_route_id") or payload.get("selected_route_id") or ""),
        "expected_route_id": _safe_text(expected.get("route_id") or payload.get("expected_route_id") or ""),
        "actual_method_id": _safe_text(actual.get("method_id") or payload.get("actual_method_id") or payload.get("observed_method_id") or payload.get("selected_method_id") or ""),
        "expected_method_id": _safe_text(expected.get("method_id") or payload.get("expected_method_id") or ""),
        "actual_shape_id": _safe_text(actual.get("shape_id") or payload.get("actual_shape_id") or payload.get("observed_shape_id") or payload.get("selected_shape_id") or ""),
        "expected_shape_id": _safe_text(expected.get("shape_id") or payload.get("expected_shape_id") or ""),
        "actual_case_id": _safe_text(actual.get("case_id") or payload.get("actual_case_id") or payload.get("observed_case_id") or payload.get("selected_case_id") or ""),
        "expected_case_id": _safe_text(expected.get("case_id") or payload.get("expected_case_id") or ""),
        "source_replay_statuses": _normalize_strings([payload.get("source_replay_status") or payload.get("match_status") or "not_replayed_yet"]),
        "safe_metadata": dict(safe_metadata),
        "raw_payload": payload,
    }
    return record


def _merge_record(base: dict[str, Any], addition: dict[str, Any]) -> dict[str, Any]:
    if not base:
        return dict(addition)
    merged = dict(base)
    for key in (
        "prompt_labels",
        "mismatch_labels",
        "replay_labels",
        "target_update_areas",
        "affected_method_ids",
        "affected_shape_ids",
        "affected_case_ids",
        "affected_route_ids",
        "source_replay_statuses",
    ):
        merged[key] = _dedupe_preserve(tuple(merged.get(key, ())) + tuple(addition.get(key, ())))
    for key in ("actual_route_id", "expected_route_id", "actual_method_id", "expected_method_id", "actual_shape_id", "expected_shape_id", "actual_case_id", "expected_case_id"):
        if not _safe_text(merged.get(key)) and _safe_text(addition.get(key)):
            merged[key] = addition[key]
    if _safe_text(addition.get("source_replay_status")) and _safe_text(merged.get("source_replay_status")) in {"", "not_replayed_yet", "captured_only"}:
        merged["source_replay_status"] = addition["source_replay_status"]
    merged["safe_metadata"] = {**dict(base.get("safe_metadata") or {}), **dict(addition.get("safe_metadata") or {})}
    merged["raw_payload"] = {**dict(base.get("raw_payload") or {}), **dict(addition.get("raw_payload") or {})}
    return merged


# ---------------------------------------------------------------------------
# Pattern inference
# ---------------------------------------------------------------------------


def _infer_pattern_type(record: Mapping[str, Any]) -> str:
    case_type = _safe_text(record.get("case_type")).lower()
    prompt_blob = " ".join(record.get("prompt_labels") or ())
    replay_blob = " ".join(record.get("replay_labels") or ())
    mismatch_blob = " ".join(record.get("mismatch_labels") or ())
    route_blob = " ".join(
        [record.get("actual_route_id") or "", record.get("expected_route_id") or "", record.get("actual_case_id") or "", record.get("expected_case_id") or ""]
    ).lower()
    target_blob = " ".join(record.get("target_update_areas") or ()).lower()

    if case_type in {"missing_identity_directness", "identity_status"} or _contains_any(prompt_blob + " " + replay_blob + " " + route_blob, ("what is weslr", "what are you", "identity", "status", "explain weslr", "identity_status_route")):
        return "identity_status_pattern"

    if case_type in {"missing_capability_orientation", "capability_orientation"} or _contains_any(prompt_blob + " " + replay_blob + " " + route_blob, ("what can you do", "capability", "current ability", "help", "capability_orientation_route")):
        # If this is clearly a boundary case for inactive capabilities, prefer that pattern.
        if case_type == "wrong_boundary_policy" or _contains_any(prompt_blob + " " + replay_blob + " " + route_blob, ("upload", "pay", "marketplace", "public pilot", "inactive")):
            return "inactive_capability_boundary_pattern"
        return "capability_orientation_pattern"

    if case_type == "unknown_friction_not_preferred" or _contains_any(prompt_blob + " " + replay_blob + " " + route_blob, ("unknown word", "unknown phrase", "unknown term", "unfamiliar", "what does this mean", "unknown_word_phrase_route")):
        return "unknown_term_friction_pattern"

    if case_type == "wrong_boundary_policy" or _contains_any(prompt_blob + " " + replay_blob + " " + route_blob, ("upload", "pay", "marketplace", "public pilot", "inactive")):
        return "inactive_capability_boundary_pattern"

    if "answer_shape_mismatch" in mismatch_blob:
        return "answer_shape_mismatch_pattern"

    if "wrong_case_priority" in mismatch_blob:
        return "case_priority_pattern"

    if _contains_any(target_blob, ("response_method_selector", "cognition_case_registry")):
        return "selector_priority_pattern"

    if _contains_any(target_blob, ("no_model_bounded_renderer",)):
        return "renderer_policy_pattern"

    if _contains_any(target_blob, ("behavior_pack",)) or len(_dedupe_preserve(record.get("affected_route_ids") or ())) >= 3:
        return "behavior_pack_candidate_pattern"

    return "behavior_pack_candidate_pattern"


def _stable_pattern_id(pattern_type: str, source_case_ids: Sequence[str], shared_mismatch_labels: Sequence[str], shared_prompt_labels: Sequence[str]) -> str:
    override = _PATTERN_ID_OVERRIDES_V1.get(pattern_type)
    if override:
        return override
    base = "|".join(
        [
            pattern_type,
            ",".join(_normalize_strings(source_case_ids)),
            ",".join(_normalize_labels(shared_mismatch_labels)),
            ",".join(_normalize_labels(shared_prompt_labels)),
        ]
    )
    digest = sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"{pattern_type}_{digest}"


def _shared_labels(records: Sequence[Mapping[str, Any]], key: str) -> tuple[str, ...]:
    values = [tuple(_normalize_labels(record.get(key))) if key != "target_update_areas" else tuple(_normalize_strings(record.get(key))) for record in records]
    if not values:
        return tuple()
    if len(values) == 1:
        return tuple(values[0])
    shared = set(values[0])
    for value in values[1:]:
        shared &= set(value)
    if shared:
        first = values[0]
        return tuple(item for item in first if item in shared)
    # Honest fallback: use the first record's labels to keep the candidate usable.
    return tuple(values[0])


def _shared_strings(records: Sequence[Mapping[str, Any]], key: str) -> tuple[str, ...]:
    values = [tuple(_normalize_strings(record.get(key))) for record in records]
    if not values:
        return tuple()
    if len(values) == 1:
        return tuple(values[0])
    shared = set(values[0])
    for value in values[1:]:
        shared &= set(value)
    if shared:
        first = values[0]
        return tuple(item for item in first if item in shared)
    return tuple(values[0])


def _confidence_level_for_group(pattern_type: str, records: Sequence[Mapping[str, Any]], *, replay_packet: Any | None = None, proposal_packet: Any | None = None) -> str:
    source_case_count = len({record.get("case_id") for record in records if _safe_text(record.get("case_id"))})
    source_replay_statuses = _dedupe_preserve(record.get("source_replay_status") for record in records if _safe_text(record.get("source_replay_status")))
    has_replay_support = bool(source_replay_statuses) and source_replay_statuses != ("not_replayed_yet",)
    all_pass = has_replay_support and all(status == "passes_expected" for status in source_replay_statuses)
    has_proposal_packet = proposal_packet is not None

    if source_case_count <= 1:
        return "single_case_low"

    if source_case_count == 2:
        if has_proposal_packet and all_pass:
            return "replay_supported_medium"
        return "multi_case_medium"

    if has_proposal_packet and all_pass:
        return "proposal_supported_high"
    return "proof_review_required"


def _proposal_eligibility_for_group(pattern_type: str, records: Sequence[Mapping[str, Any]], confidence_level: str) -> str:
    source_case_count = len({record.get("case_id") for record in records if _safe_text(record.get("case_id"))})
    source_replay_statuses = _dedupe_preserve(record.get("source_replay_status") for record in records if _safe_text(record.get("source_replay_status")))
    has_replay_support = bool(source_replay_statuses) and source_replay_statuses != ("not_replayed_yet",)
    if pattern_type == "behavior_pack_candidate_pattern" and source_case_count >= 3:
        return "eligible_for_owner_review"
    if source_case_count <= 1:
        return "eligible_for_replay_suite" if has_replay_support else "capture_only"
    if source_case_count == 2:
        return "eligible_for_update_proposal" if confidence_level != "single_case_low" else "needs_more_cases"
    if confidence_level in {"proposal_supported_high", "proof_review_required"}:
        return "eligible_for_owner_review"
    return "eligible_for_update_proposal"


# ---------------------------------------------------------------------------
# Candidate / packet builders
# ---------------------------------------------------------------------------


def build_friction_pattern_candidate_v1(
    *,
    pattern_id: str,
    pattern_type: str,
    source_case_ids: Sequence[Any],
    source_replay_statuses: Sequence[Any],
    shared_mismatch_labels: Sequence[Any],
    shared_prompt_labels: Sequence[Any],
    shared_replay_labels: Sequence[Any],
    target_update_areas: Sequence[Any],
    affected_method_ids: Sequence[Any],
    affected_shape_ids: Sequence[Any],
    affected_case_ids: Sequence[Any],
    affected_route_ids: Sequence[Any],
    generalized_failure_summary: str,
    generalized_expected_behavior: str,
    proposal_eligibility: str,
    minimum_replay_suite_requirements: Sequence[Any],
    confidence_level: str,
    owner_review_required: bool = True,
    safe_to_apply_automatically: bool = False,
    learning_claimed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> FrictionPatternCandidate:
    candidate = FrictionPatternCandidate(
        pattern_id=_safe_text(pattern_id),
        pattern_type=_safe_text(pattern_type),
        source_case_ids=_normalize_strings(source_case_ids),
        source_replay_statuses=_normalize_strings(source_replay_statuses),
        shared_mismatch_labels=_normalize_labels(shared_mismatch_labels),
        shared_prompt_labels=_normalize_labels(shared_prompt_labels),
        shared_replay_labels=_normalize_labels(shared_replay_labels),
        target_update_areas=_normalize_strings(target_update_areas),
        affected_method_ids=_normalize_strings(affected_method_ids),
        affected_shape_ids=_normalize_strings(affected_shape_ids),
        affected_case_ids=_normalize_strings(affected_case_ids),
        affected_route_ids=_normalize_strings(affected_route_ids),
        generalized_failure_summary=_safe_text(generalized_failure_summary),
        generalized_expected_behavior=_safe_text(generalized_expected_behavior),
        proposal_eligibility=_safe_text(proposal_eligibility),
        minimum_replay_suite_requirements=_normalize_strings(minimum_replay_suite_requirements),
        confidence_level=_safe_text(confidence_level),
        owner_review_required=bool(owner_review_required),
        safe_to_apply_automatically=bool(safe_to_apply_automatically),
        learning_claimed=bool(learning_claimed),
        runtime_authority=bool(runtime_authority),
        writes_state=bool(writes_state),
        model_provider_used=bool(model_provider_used),
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_pattern_candidate_v1(candidate)
    return candidate


def _build_pattern_candidate_from_records(pattern_type: str, records: Sequence[Mapping[str, Any]], *, replay_packet: Any | None = None, proposal_packet: Any | None = None) -> FrictionPatternCandidate:
    if not records:
        raise ValidationError("pattern_candidate_requires_source_records")
    source_case_ids = _shared_strings(records, "case_id")
    source_replay_statuses = _shared_strings(records, "source_replay_status") or ("not_replayed_yet",)
    shared_mismatch_labels = _shared_labels(records, "mismatch_labels")
    shared_prompt_labels = _shared_labels(records, "prompt_labels")
    shared_replay_labels = _shared_labels(records, "replay_labels")
    target_update_areas = _shared_strings(records, "target_update_areas")
    affected_method_ids = _shared_strings(records, "affected_method_ids")
    affected_shape_ids = _shared_strings(records, "affected_shape_ids")
    affected_case_ids = _shared_strings(records, "affected_case_ids")
    affected_route_ids = _shared_strings(records, "affected_route_ids")
    pattern_id = _stable_pattern_id(pattern_type, source_case_ids, shared_mismatch_labels, shared_prompt_labels)
    generalized_failure_summary = _GENERALIZED_FAILURE_SUMMARIES_V1.get(pattern_type, "Repeated friction suggests a generalized failure pattern.")
    generalized_expected_behavior = _GENERALIZED_EXPECTED_BEHAVIORS_V1.get(pattern_type, "A bounded, replay-proven, owner-reviewable behavior should replace the repeated failure.")
    confidence_level = _confidence_level_for_group(pattern_type, records, replay_packet=replay_packet, proposal_packet=proposal_packet)
    proposal_eligibility = _proposal_eligibility_for_group(pattern_type, records, confidence_level)
    owner_review_required = True
    if proposal_eligibility == "not_eligible_boundary_risk":
        owner_review_required = True
    elif proposal_eligibility in {"capture_only", "needs_more_cases"}:
        owner_review_required = True
    minimum_replay_suite_requirements = _MIN_REPLAY_SUITE_REQUIREMENTS_V1.get(pattern_type, _MIN_REPLAY_SUITE_REQUIREMENTS_V1["behavior_pack_candidate_pattern"])
    safe_metadata = {
        "source_case_count": len(source_case_ids),
        "source_replay_status_count": len(source_replay_statuses),
        "pattern_origin": "friction_pattern_miner_v1",
    }
    return build_friction_pattern_candidate_v1(
        pattern_id=pattern_id,
        pattern_type=pattern_type,
        source_case_ids=source_case_ids,
        source_replay_statuses=source_replay_statuses,
        shared_mismatch_labels=shared_mismatch_labels,
        shared_prompt_labels=shared_prompt_labels,
        shared_replay_labels=shared_replay_labels,
        target_update_areas=target_update_areas,
        affected_method_ids=affected_method_ids,
        affected_shape_ids=affected_shape_ids,
        affected_case_ids=affected_case_ids,
        affected_route_ids=affected_route_ids,
        generalized_failure_summary=generalized_failure_summary,
        generalized_expected_behavior=generalized_expected_behavior,
        proposal_eligibility=proposal_eligibility,
        minimum_replay_suite_requirements=minimum_replay_suite_requirements,
        confidence_level=confidence_level,
        owner_review_required=owner_review_required,
        safe_to_apply_automatically=False,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata=safe_metadata,
    )


def _records_from_inputs(
    friction_cases: Any | None = None,
    replay_packet: Any | None = None,
    proposal_packet: Any | None = None,
) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}

    if friction_cases is not None:
        for item in _as_list(friction_cases):
            record = _coerce_case_record(item)
            case_id = _safe_text(record.get("case_id"))
            if not case_id:
                raise ValidationError("source_case_id_required")
            records[case_id] = _merge_record(records.get(case_id, {}), record)

    if replay_packet is not None:
        packet = replay_packet
        if isinstance(packet, FrictionReplayHarnessPacket):
            results = packet.results
        elif isinstance(packet, Mapping):
            results = packet.get("results") or []
        else:
            results = _as_list(packet)
        for item in results:
            record = _coerce_case_record(item)
            case_id = _safe_text(record.get("case_id"))
            if not case_id:
                continue
            records[case_id] = _merge_record(records.get(case_id, {}), record)

    if proposal_packet is not None:
        packet = proposal_packet
        if isinstance(packet, FrictionUpdateProposalPacket):
            proposals = packet.proposals
        elif isinstance(packet, Mapping):
            proposals = packet.get("proposals") or []
        else:
            proposals = _as_list(packet)
        for item in proposals:
            record = _coerce_case_record(item)
            case_id = _safe_text(record.get("case_id"))
            if not case_id:
                continue
            records[case_id] = _merge_record(records.get(case_id, {}), record)

    return [records[key] for key in records.keys()]


def mine_friction_patterns_v1(
    friction_cases: Any | None = None,
    replay_packet: Any | None = None,
    proposal_packet: Any | None = None,
) -> tuple[FrictionPatternCandidate, ...]:
    records = _records_from_inputs(friction_cases, replay_packet, proposal_packet)
    if not records:
        return tuple()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ordered_pattern_types: list[str] = []
    for record in records:
        pattern_type = _infer_pattern_type(record)
        if pattern_type not in grouped:
            ordered_pattern_types.append(pattern_type)
        grouped[pattern_type].append(record)

    patterns = tuple(
        _build_pattern_candidate_from_records(pattern_type, grouped[pattern_type], replay_packet=replay_packet, proposal_packet=proposal_packet)
        for pattern_type in ordered_pattern_types
    )
    return patterns


def build_initial_renderer_friction_patterns_v1() -> tuple[FrictionPatternCandidate, ...]:
    return mine_friction_patterns_v1(
        friction_cases=build_initial_renderer_friction_cases_v1(),
        replay_packet=build_initial_renderer_friction_replay_v1(),
        proposal_packet=build_initial_renderer_friction_update_proposals_v1(),
    )


# ---------------------------------------------------------------------------
# Validation / export / summary
# ---------------------------------------------------------------------------


def validate_friction_pattern_candidate_v1(candidate: Any) -> bool:
    if _collect_forbidden_keys(candidate):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(candidate, FrictionPatternCandidate):
        normalized = candidate
    elif isinstance(candidate, Mapping):
        normalized = FrictionPatternCandidate(
            pattern_id=_safe_text(candidate.get("pattern_id")),
            pattern_type=_safe_text(candidate.get("pattern_type")),
            source_case_ids=_normalize_strings(candidate.get("source_case_ids")),
            source_replay_statuses=_normalize_strings(candidate.get("source_replay_statuses")),
            shared_mismatch_labels=_normalize_labels(candidate.get("shared_mismatch_labels")),
            shared_prompt_labels=_normalize_labels(candidate.get("shared_prompt_labels")),
            shared_replay_labels=_normalize_labels(candidate.get("shared_replay_labels")),
            target_update_areas=_normalize_strings(candidate.get("target_update_areas")),
            affected_method_ids=_normalize_strings(candidate.get("affected_method_ids")),
            affected_shape_ids=_normalize_strings(candidate.get("affected_shape_ids")),
            affected_case_ids=_normalize_strings(candidate.get("affected_case_ids")),
            affected_route_ids=_normalize_strings(candidate.get("affected_route_ids")),
            generalized_failure_summary=_safe_text(candidate.get("generalized_failure_summary")),
            generalized_expected_behavior=_safe_text(candidate.get("generalized_expected_behavior")),
            proposal_eligibility=_safe_text(candidate.get("proposal_eligibility")),
            minimum_replay_suite_requirements=_normalize_strings(candidate.get("minimum_replay_suite_requirements")),
            confidence_level=_safe_text(candidate.get("confidence_level")),
            owner_review_required=bool(candidate.get("owner_review_required", False)),
            safe_to_apply_automatically=bool(candidate.get("safe_to_apply_automatically", False)),
            learning_claimed=bool(candidate.get("learning_claimed", False)),
            runtime_authority=bool(candidate.get("runtime_authority", False)),
            writes_state=bool(candidate.get("writes_state", False)),
            model_provider_used=bool(candidate.get("model_provider_used", False)),
            safe_metadata=dict(candidate.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("candidate_must_be_mapping_or_pattern_candidate")

    if not normalized.pattern_id:
        raise ValidationError("pattern_id_required")
    if not normalized.pattern_type:
        raise ValidationError("pattern_type_required")
    if normalized.pattern_type not in ALLOWED_PATTERN_TYPES_V1:
        raise ValidationError("unknown_pattern_type")
    if not normalized.source_case_ids:
        raise ValidationError("source_case_ids_required")
    if not normalized.source_replay_statuses:
        raise ValidationError("source_replay_statuses_required")
    if not normalized.shared_mismatch_labels:
        raise ValidationError("shared_mismatch_labels_required")
    if not normalized.shared_prompt_labels:
        raise ValidationError("shared_prompt_labels_required")
    if not normalized.shared_replay_labels:
        raise ValidationError("shared_replay_labels_required")
    if not normalized.target_update_areas:
        raise ValidationError("target_update_areas_required")
    if not normalized.affected_method_ids:
        raise ValidationError("affected_method_ids_required")
    if not normalized.affected_shape_ids:
        raise ValidationError("affected_shape_ids_required")
    if not normalized.affected_case_ids:
        raise ValidationError("affected_case_ids_required")
    if not normalized.affected_route_ids:
        raise ValidationError("affected_route_ids_required")
    if not normalized.generalized_failure_summary:
        raise ValidationError("generalized_failure_summary_required")
    if not normalized.generalized_expected_behavior:
        raise ValidationError("generalized_expected_behavior_required")
    if normalized.proposal_eligibility not in ALLOWED_PROPOSAL_ELIGIBILITY_V1:
        raise ValidationError("unknown_proposal_eligibility")
    if normalized.confidence_level not in ALLOWED_CONFIDENCE_LEVELS_V1:
        raise ValidationError("unknown_confidence_level")
    if not normalized.minimum_replay_suite_requirements:
        raise ValidationError("minimum_replay_suite_requirements_required")

    if normalized.safe_to_apply_automatically is not False:
        raise ValidationError("safe_to_apply_automatically_must_be_false")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.proposal_eligibility not in {"capture_only", "needs_more_cases", "not_eligible_boundary_risk"} and normalized.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true_for_proposal_eligible_pattern")

    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True


def validate_friction_pattern_packet_v1(packet: Any) -> bool:
    if _collect_forbidden_keys(packet):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(packet, FrictionPatternPacket):
        normalized = packet
    elif isinstance(packet, Mapping):
        patterns = tuple(
            pattern if isinstance(pattern, FrictionPatternCandidate) else build_friction_pattern_candidate_v1(**pattern)
            for pattern in _as_list(packet.get("patterns"))
        )
        normalized = FrictionPatternPacket(
            packet_type=_safe_text(packet.get("packet_type")),
            pattern_count=int(packet.get("pattern_count", len(patterns))),
            patterns=patterns,
            pattern_type_counts=dict(packet.get("pattern_type_counts") or {}),
            confidence_counts=dict(packet.get("confidence_counts") or {}),
            proposal_eligibility_counts=dict(packet.get("proposal_eligibility_counts") or {}),
            source_case_count=int(packet.get("source_case_count", len({case_id for pattern in patterns for case_id in pattern.source_case_ids}))),
            learning_claimed=bool(packet.get("learning_claimed", False)),
            runtime_authority=bool(packet.get("runtime_authority", False)),
            writes_state=bool(packet.get("writes_state", False)),
            model_provider_used=bool(packet.get("model_provider_used", False)),
            proposal_created=bool(packet.get("proposal_created", False)),
            promotion_performed=bool(packet.get("promotion_performed", False)),
            safe_metadata=dict(packet.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("packet_must_be_mapping_or_pattern_packet")

    if normalized.packet_type != PACKET_TYPE_V1:
        raise ValidationError("unknown_packet_type")
    if normalized.pattern_count != len(normalized.patterns):
        raise ValidationError("pattern_count_mismatch")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.proposal_created is not False:
        raise ValidationError("proposal_created_must_be_false")
    if normalized.promotion_performed is not False:
        raise ValidationError("promotion_performed_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")

    pattern_ids = [pattern.pattern_id for pattern in normalized.patterns]
    if len(pattern_ids) != len(set(pattern_ids)):
        raise ValidationError("duplicate_pattern_id")
    for pattern in normalized.patterns:
        validate_friction_pattern_candidate_v1(pattern)

    summary = {
        "pattern_count": len(normalized.patterns),
        "pattern_type_counts": dict(sorted(Counter(pattern.pattern_type for pattern in normalized.patterns).items())),
        "confidence_counts": dict(sorted(Counter(pattern.confidence_level for pattern in normalized.patterns).items())),
        "proposal_eligibility_counts": dict(sorted(Counter(pattern.proposal_eligibility for pattern in normalized.patterns).items())),
        "source_case_count": len({case_id for pattern in normalized.patterns for case_id in pattern.source_case_ids}),
    }
    if normalized.pattern_count != summary["pattern_count"]:
        raise ValidationError("summary_pattern_count_mismatch")
    if normalized.pattern_type_counts != summary["pattern_type_counts"]:
        raise ValidationError("summary_pattern_type_counts_mismatch")
    if normalized.confidence_counts != summary["confidence_counts"]:
        raise ValidationError("summary_confidence_counts_mismatch")
    if normalized.proposal_eligibility_counts != summary["proposal_eligibility_counts"]:
        raise ValidationError("summary_proposal_eligibility_counts_mismatch")
    if normalized.source_case_count != summary["source_case_count"]:
        raise ValidationError("summary_source_case_count_mismatch")
    return True


# ---------------------------------------------------------------------------
# Summaries / export
# ---------------------------------------------------------------------------


def summarize_friction_pattern_candidate_v1(candidate: Any) -> dict[str, Any]:
    validate_friction_pattern_candidate_v1(candidate)
    normalized = candidate if isinstance(candidate, FrictionPatternCandidate) else build_friction_pattern_candidate_v1(**candidate)
    return to_friction_pattern_json_safe_v1(
        {
            "pattern_id": normalized.pattern_id,
            "pattern_type": normalized.pattern_type,
            "source_case_ids": list(normalized.source_case_ids),
            "source_replay_statuses": list(normalized.source_replay_statuses),
            "shared_mismatch_labels": list(normalized.shared_mismatch_labels),
            "shared_prompt_labels": list(normalized.shared_prompt_labels),
            "shared_replay_labels": list(normalized.shared_replay_labels),
            "target_update_areas": list(normalized.target_update_areas),
            "affected_method_ids": list(normalized.affected_method_ids),
            "affected_shape_ids": list(normalized.affected_shape_ids),
            "affected_case_ids": list(normalized.affected_case_ids),
            "affected_route_ids": list(normalized.affected_route_ids),
            "generalized_failure_summary": normalized.generalized_failure_summary,
            "generalized_expected_behavior": normalized.generalized_expected_behavior,
            "proposal_eligibility": normalized.proposal_eligibility,
            "minimum_replay_suite_requirements": list(normalized.minimum_replay_suite_requirements),
            "confidence_level": normalized.confidence_level,
            "owner_review_required": normalized.owner_review_required,
            "safe_to_apply_automatically": normalized.safe_to_apply_automatically,
        }
    )


def to_friction_pattern_json_safe_v1(value: Any) -> Any:
    return _json_safe(deepcopy(value))


def summarize_friction_pattern_packet_v1(packet: Any) -> dict[str, Any]:
    validate_friction_pattern_packet_v1(packet)
    normalized = packet if isinstance(packet, FrictionPatternPacket) else build_friction_pattern_packet_v1(packet.get("patterns") or [], safe_metadata=packet.get("safe_metadata"))
    return to_friction_pattern_json_safe_v1(
        {
            "packet_type": normalized.packet_type,
            "pattern_count": normalized.pattern_count,
            "pattern_type_counts": normalized.pattern_type_counts,
            "confidence_counts": normalized.confidence_counts,
            "proposal_eligibility_counts": normalized.proposal_eligibility_counts,
            "source_case_count": normalized.source_case_count,
            "patterns": [summarize_friction_pattern_candidate_v1(pattern) for pattern in normalized.patterns],
        }
    )


def build_friction_pattern_packet_v1(patterns: Sequence[Any], *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionPatternPacket:
    normalized_patterns = tuple(
        pattern if isinstance(pattern, FrictionPatternCandidate) else build_friction_pattern_candidate_v1(**pattern)
        for pattern in patterns
    )
    packet = FrictionPatternPacket(
        packet_type=PACKET_TYPE_V1,
        pattern_count=len(normalized_patterns),
        patterns=normalized_patterns,
        pattern_type_counts=dict(sorted(Counter(pattern.pattern_type for pattern in normalized_patterns).items())),
        confidence_counts=dict(sorted(Counter(pattern.confidence_level for pattern in normalized_patterns).items())),
        proposal_eligibility_counts=dict(sorted(Counter(pattern.proposal_eligibility for pattern in normalized_patterns).items())),
        source_case_count=len({case_id for pattern in normalized_patterns for case_id in pattern.source_case_ids}),
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        proposal_created=False,
        promotion_performed=False,
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_pattern_packet_v1(packet)
    return packet


def build_initial_renderer_friction_patterns_v1() -> tuple[FrictionPatternCandidate, ...]:
    return mine_friction_patterns_v1(
        friction_cases=build_initial_renderer_friction_cases_v1(),
        replay_packet=build_initial_renderer_friction_replay_v1(),
        proposal_packet=build_initial_renderer_friction_update_proposals_v1(),
    )


__all__ = [
    "ALLOWED_CONFIDENCE_LEVELS_V1",
    "ALLOWED_PATTERN_TYPES_V1",
    "ALLOWED_PROPOSAL_ELIGIBILITY_V1",
    "FrictionPatternCandidate",
    "FrictionPatternPacket",
    "ValidationError",
    "build_friction_pattern_candidate_v1",
    "build_friction_pattern_packet_v1",
    "build_initial_renderer_friction_patterns_v1",
    "mine_friction_patterns_v1",
    "summarize_friction_pattern_candidate_v1",
    "summarize_friction_pattern_packet_v1",
    "to_friction_pattern_json_safe_v1",
    "validate_friction_pattern_candidate_v1",
    "validate_friction_pattern_packet_v1",
]
