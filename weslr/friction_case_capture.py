"""Metadata-only friction case capture helpers v1.

This module captures weak or wrong WESLR answer-route metadata as replayable
friction cases. It is pure, deterministic, import-safe, and fail-closed.

It does not write state, does not call providers/models/search/advisors, does
not wire runtime/chat, does not store raw prompts/answers/transcripts by
default, and does not create proposals or promotions.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.answer_method_catalog import build_answer_method_catalog_v1
from weslr.answer_shape_catalog import build_answer_shape_catalog_v1
from weslr.cognition_case_registry import build_cognition_case_registry_v1

HELPER_TYPE_V1 = "weslr_friction_case_capture_v1"
CASE_TYPE_V1 = "friction_case_v1"
CAPTURE_PACKET_TYPE_V1 = "friction_case_capture_packet_v1"
SUMMARY_TYPE_V1 = "friction_case_summary_v1"

ALLOWED_CASE_TYPES_V1 = {
    "answer_shape_mismatch",
    "wrong_case_priority",
    "unknown_friction_not_preferred",
    "wrong_boundary_policy",
    "too_cautious",
    "too_generic",
    "missing_capability_orientation",
    "missing_identity_directness",
    "missing_evidence_policy",
    "memory_honesty_gap",
    "continuity_gap",
    "correction_repair_gap",
    "relationship_feedback_gap",
    "language_discovery_gap",
}

ALLOWED_PROPOSED_UPDATE_AREAS_V1 = {
    "method_catalog",
    "shape_catalog",
    "cognition_case_registry",
    "response_method_selector",
    "unknown_prompt_friction_router",
    "candidate_response_formation",
    "response_fit_self_check",
    "no_model_bounded_renderer",
    "behavior_pack",
    "governance_proposal_bridge",
}

ALLOWED_APPROVAL_STATUSES_V1 = {
    "captured_only",
    "owner_review_required",
    "approved_for_replay",
    "approved_for_proposal",
    "rejected",
}

ALLOWED_PROMOTION_STATUSES_V1 = {
    "not_promoted",
    "replay_ready",
    "proposal_ready",
    "promoted_after_approval",
}

ALLOWED_RENDER_MODES_V1 = {
    "clarifying_question",
    "direct_bounded",
    "unknown_friction",
    "refusal_boundary",
}

ALLOWED_MISMATCH_LABELS_V1 = {
    "answer_shape_mismatch",
    "wrong_case_priority",
    "unknown_friction_not_preferred",
    "wrong_boundary_policy",
    "too_cautious",
    "too_generic",
    "missing_capability_orientation",
    "missing_identity_directness",
    "missing_evidence_policy",
    "memory_honesty_gap",
    "continuity_gap",
    "correction_repair_gap",
    "relationship_feedback_gap",
    "language_discovery_gap",
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


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FrictionCaseExpectation:
    render_mode: str
    method_id: str
    shape_id: str
    case_id: str
    route_id: str


@dataclass(frozen=True, slots=True)
class FrictionCaseObservation:
    render_mode: str
    method_id: str
    shape_id: str
    case_id: str
    route_id: str


@dataclass(frozen=True, slots=True)
class FrictionCase:
    case_id: str
    case_type: str
    safe_prompt_descriptor: str
    prompt_labels: tuple[str, ...]
    actual: FrictionCaseObservation
    expected: FrictionCaseExpectation
    mismatch_labels: tuple[str, ...]
    owner_correction: str
    proposed_update_area: tuple[str, ...]
    replay_labels: tuple[str, ...]
    approval_status: str
    promotion_status: str
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FrictionCaseSummary:
    summary_type: str
    case_id: str
    case_type: str
    prompt_labels: tuple[str, ...]
    mismatch_labels: tuple[str, ...]
    proposed_update_area: tuple[str, ...]
    approval_status: str
    promotion_status: str
    replay_labels: tuple[str, ...]
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FrictionCaseCapturePacket:
    packet_type: str
    case: FrictionCase
    summary: FrictionCaseSummary
    validation: dict[str, Any]
    safe_metadata: dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    writes_state: bool = False


@dataclass(frozen=True, slots=True)
class FrictionCaseCaptureBatch:
    packet_type: str
    cases: tuple[FrictionCase, ...]
    summary: dict[str, Any]
    validation: dict[str, Any]
    safe_metadata: dict[str, Any]
    runtime_authority: bool = False
    model_provider_used: bool = False
    writes_state: bool = False


_ALLOWED_METHOD_IDS_V1 = {method.method_id for method in build_answer_method_catalog_v1().methods}
_ALLOWED_SHAPE_IDS_V1 = {shape.shape_id for shape in build_answer_shape_catalog_v1().shapes}
_ALLOWED_ROUTE_IDS_V1 = {
    "clarification_route",
    "identity_status_route",
    "capability_orientation_route",
    "unknown_word_phrase_route",
    "refusal_boundary_route",
}


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
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


def _as_bool(value: Any) -> bool:
    return bool(value is True or value == 1 or str(value).strip().lower() in {"true", "yes", "1", "on"})


def _normalize_labels(value: Any) -> tuple[str, ...]:
    labels: list[str] = []
    for item in _as_list(value):
        label = _safe_text(item).lower().strip()
        if label:
            labels.append(label)
    return _dedupe_preserve(labels)


def _normalize_strings(value: Any) -> tuple[str, ...]:
    return _dedupe_preserve(_safe_text(item) for item in _as_list(value))


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
    return value


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


def _coerce_observation(value: Any) -> FrictionCaseObservation:
    if isinstance(value, FrictionCaseObservation):
        return value
    if isinstance(value, Mapping):
        return FrictionCaseObservation(
            render_mode=_safe_text(value.get("render_mode")),
            method_id=_safe_text(value.get("method_id")),
            shape_id=_safe_text(value.get("shape_id")),
            case_id=_safe_text(value.get("case_id")),
            route_id=_safe_text(value.get("route_id")),
        )
    raise ValidationError("actual_or_expected_must_be_mapping_or_friction_case_observation")


def _coerce_expectation(value: Any) -> FrictionCaseExpectation:
    if isinstance(value, FrictionCaseExpectation):
        return value
    if isinstance(value, Mapping):
        return FrictionCaseExpectation(
            render_mode=_safe_text(value.get("render_mode")),
            method_id=_safe_text(value.get("method_id")),
            shape_id=_safe_text(value.get("shape_id")),
            case_id=_safe_text(value.get("case_id")),
            route_id=_safe_text(value.get("route_id")),
        )
    raise ValidationError("actual_or_expected_must_be_mapping_or_friction_case_expectation")


def _coerce_case(value: Any) -> FrictionCase:
    if isinstance(value, FrictionCase):
        return value
    if isinstance(value, Mapping):
        actual = _coerce_observation(value.get("actual"))
        expected = _coerce_expectation(value.get("expected"))
        safe_metadata = value.get("safe_metadata")
        if not isinstance(safe_metadata, Mapping):
            safe_metadata = {}
        return FrictionCase(
            case_id=_safe_text(value.get("case_id")),
            case_type=_safe_text(value.get("case_type")),
            safe_prompt_descriptor=_safe_text(value.get("safe_prompt_descriptor")),
            prompt_labels=_normalize_strings(value.get("prompt_labels")),
            actual=actual,
            expected=expected,
            mismatch_labels=_normalize_labels(value.get("mismatch_labels")),
            owner_correction=_safe_text(value.get("owner_correction")),
            proposed_update_area=_normalize_strings(value.get("proposed_update_area")),
            replay_labels=_normalize_strings(value.get("replay_labels")),
            approval_status=_safe_text(value.get("approval_status")),
            promotion_status=_safe_text(value.get("promotion_status")),
            learning_claimed=_as_bool(value.get("learning_claimed")),
            runtime_authority=_as_bool(value.get("runtime_authority")),
            writes_state=_as_bool(value.get("writes_state")),
            model_provider_used=_as_bool(value.get("model_provider_used")),
            safe_metadata=dict(safe_metadata),
        )
    raise ValidationError("friction_case_must_be_mapping_or_friction_case")


def _validate_case_core(case: FrictionCase) -> None:
    if not case.case_id:
        raise ValidationError("missing_case_id")
    if case.case_type not in ALLOWED_CASE_TYPES_V1:
        raise ValidationError("unknown_case_type")
    if not case.safe_prompt_descriptor:
        raise ValidationError("missing_safe_prompt_descriptor")
    if not case.prompt_labels:
        raise ValidationError("missing_prompt_labels")
    if case.actual.render_mode not in ALLOWED_RENDER_MODES_V1:
        raise ValidationError("unknown_actual_render_mode")
    if case.expected.render_mode not in ALLOWED_RENDER_MODES_V1:
        raise ValidationError("unknown_expected_render_mode")
    if not case.actual.method_id:
        raise ValidationError("missing_actual_method_id")
    if not case.expected.method_id:
        raise ValidationError("missing_expected_method_id")
    if not case.actual.shape_id:
        raise ValidationError("missing_actual_shape_id")
    if not case.expected.shape_id:
        raise ValidationError("missing_expected_shape_id")
    if not case.actual.case_id:
        raise ValidationError("missing_actual_case_id")
    if not case.expected.case_id:
        raise ValidationError("missing_expected_case_id")
    if not case.actual.route_id:
        raise ValidationError("missing_actual_route_id")
    if not case.expected.route_id:
        raise ValidationError("missing_expected_route_id")
    if _contains_forbidden_marker(case.actual.method_id):
        raise ValidationError("unsafe_actual_method_id")
    if _contains_forbidden_marker(case.expected.method_id):
        raise ValidationError("unsafe_expected_method_id")
    if _contains_forbidden_marker(case.actual.shape_id):
        raise ValidationError("unsafe_actual_shape_id")
    if _contains_forbidden_marker(case.expected.shape_id):
        raise ValidationError("unsafe_expected_shape_id")
    if _contains_forbidden_marker(case.actual.case_id):
        raise ValidationError("unsafe_actual_case_id")
    if _contains_forbidden_marker(case.expected.case_id):
        raise ValidationError("unsafe_expected_case_id")
    if _contains_forbidden_marker(case.actual.route_id):
        raise ValidationError("unsafe_actual_route_id")
    if _contains_forbidden_marker(case.expected.route_id):
        raise ValidationError("unsafe_expected_route_id")
    if not case.mismatch_labels:
        raise ValidationError("missing_mismatch_labels")
    unknown_mismatch = [label for label in case.mismatch_labels if label not in ALLOWED_MISMATCH_LABELS_V1]
    if unknown_mismatch:
        raise ValidationError("unknown_mismatch_label")
    if not case.owner_correction:
        raise ValidationError("missing_owner_correction")
    if not case.proposed_update_area:
        raise ValidationError("missing_proposed_update_area")
    unknown_update_area = [area for area in case.proposed_update_area if area not in ALLOWED_PROPOSED_UPDATE_AREAS_V1]
    if unknown_update_area:
        raise ValidationError("unknown_proposed_update_area")
    if not case.replay_labels:
        raise ValidationError("missing_replay_labels")
    if case.approval_status not in ALLOWED_APPROVAL_STATUSES_V1:
        raise ValidationError("unknown_approval_status")
    if case.promotion_status not in ALLOWED_PROMOTION_STATUSES_V1:
        raise ValidationError("unknown_promotion_status")
    if case.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if case.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if case.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if case.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if _collect_forbidden_keys(case):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_marker(case.safe_prompt_descriptor):
        raise ValidationError("unsafe_prompt_descriptor")
    if _contains_forbidden_marker(case.owner_correction):
        raise ValidationError("unsafe_owner_correction")
    if _contains_forbidden_marker(case.safe_metadata):
        raise ValidationError("unsafe_safe_metadata")


def validate_friction_case_v1(case: Any) -> bool:
    """Validate a friction case or raise ValidationError."""

    if _collect_forbidden_keys(case):
        raise ValidationError("forbidden_raw_fields_present")
    normalized = _coerce_case(case)
    _validate_case_core(normalized)
    return True


def build_friction_case_v1(
    *,
    case_id: str,
    case_type: str,
    safe_prompt_descriptor: str,
    prompt_labels: Sequence[str] | str,
    actual_render_mode: str,
    actual_method_id: str,
    actual_shape_id: str,
    actual_case_id: str,
    actual_route_id: str,
    expected_render_mode: str,
    expected_method_id: str,
    expected_shape_id: str,
    expected_case_id: str,
    expected_route_id: str,
    mismatch_labels: Sequence[str] | str,
    owner_correction: str,
    proposed_update_area: Sequence[str] | str,
    replay_labels: Sequence[str] | str,
    approval_status: str,
    promotion_status: str,
    learning_claimed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> FrictionCase:
    case = FrictionCase(
        case_id=_safe_text(case_id),
        case_type=_safe_text(case_type),
        safe_prompt_descriptor=_safe_text(safe_prompt_descriptor),
        prompt_labels=_normalize_strings(prompt_labels),
        actual=FrictionCaseObservation(
            render_mode=_safe_text(actual_render_mode),
            method_id=_safe_text(actual_method_id),
            shape_id=_safe_text(actual_shape_id),
            case_id=_safe_text(actual_case_id),
            route_id=_safe_text(actual_route_id),
        ),
        expected=FrictionCaseExpectation(
            render_mode=_safe_text(expected_render_mode),
            method_id=_safe_text(expected_method_id),
            shape_id=_safe_text(expected_shape_id),
            case_id=_safe_text(expected_case_id),
            route_id=_safe_text(expected_route_id),
        ),
        mismatch_labels=_normalize_labels(mismatch_labels),
        owner_correction=_safe_text(owner_correction),
        proposed_update_area=_normalize_strings(proposed_update_area),
        replay_labels=_normalize_strings(replay_labels),
        approval_status=_safe_text(approval_status),
        promotion_status=_safe_text(promotion_status),
        learning_claimed=_as_bool(learning_claimed),
        runtime_authority=_as_bool(runtime_authority),
        writes_state=_as_bool(writes_state),
        model_provider_used=_as_bool(model_provider_used),
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_case_v1(case)
    return case


def summarize_friction_case_v1(case: Any) -> dict[str, Any]:
    normalized = _coerce_case(case)
    validate_friction_case_v1(normalized)
    summary = FrictionCaseSummary(
        summary_type=SUMMARY_TYPE_V1,
        case_id=normalized.case_id,
        case_type=normalized.case_type,
        prompt_labels=normalized.prompt_labels,
        mismatch_labels=normalized.mismatch_labels,
        proposed_update_area=normalized.proposed_update_area,
        approval_status=normalized.approval_status,
        promotion_status=normalized.promotion_status,
        replay_labels=normalized.replay_labels,
        learning_claimed=normalized.learning_claimed,
        runtime_authority=normalized.runtime_authority,
        writes_state=normalized.writes_state,
        model_provider_used=normalized.model_provider_used,
        safe_metadata=normalized.safe_metadata,
    )
    return to_friction_case_json_safe_v1(summary)


def to_friction_case_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(deepcopy(value))
    return safe


def build_friction_case_capture_packet_v1(case: Any, *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionCaseCapturePacket:
    normalized = _coerce_case(case)
    validation = {
        "valid": False,
        "blocked": False,
        "blocked_labels": [],
    }
    validate_friction_case_v1(normalized)
    validation = {
        "valid": True,
        "blocked": False,
        "blocked_labels": [],
    }
    packet = FrictionCaseCapturePacket(
        packet_type=CAPTURE_PACKET_TYPE_V1,
        case=normalized,
        summary=FrictionCaseSummary(
            summary_type=SUMMARY_TYPE_V1,
            case_id=normalized.case_id,
            case_type=normalized.case_type,
            prompt_labels=normalized.prompt_labels,
            mismatch_labels=normalized.mismatch_labels,
            proposed_update_area=normalized.proposed_update_area,
            approval_status=normalized.approval_status,
            promotion_status=normalized.promotion_status,
            replay_labels=normalized.replay_labels,
            learning_claimed=normalized.learning_claimed,
            runtime_authority=normalized.runtime_authority,
            writes_state=normalized.writes_state,
            model_provider_used=normalized.model_provider_used,
            safe_metadata=normalized.safe_metadata,
        ),
        validation=validation,
        safe_metadata=dict(safe_metadata or {}),
    )
    return packet


def capture_friction_case_v1(case: Any, *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionCaseCapturePacket:
    packet = build_friction_case_capture_packet_v1(case, safe_metadata=safe_metadata)
    validate_friction_case_capture_packet_v1(packet)
    return packet


def validate_friction_case_capture_packet_v1(packet: Any) -> bool:
    if isinstance(packet, FrictionCaseCapturePacket):
        normalized = packet
    elif isinstance(packet, Mapping):
        case = _coerce_case(packet.get("case"))
        summary = packet.get("summary")
        if isinstance(summary, FrictionCaseSummary):
            normalized_summary = summary
        elif isinstance(summary, Mapping):
            normalized_summary = FrictionCaseSummary(
                summary_type=_safe_text(summary.get("summary_type")),
                case_id=_safe_text(summary.get("case_id")),
                case_type=_safe_text(summary.get("case_type")),
                prompt_labels=_normalize_strings(summary.get("prompt_labels")),
                mismatch_labels=_normalize_labels(summary.get("mismatch_labels")),
                proposed_update_area=_normalize_strings(summary.get("proposed_update_area")),
                approval_status=_safe_text(summary.get("approval_status")),
                promotion_status=_safe_text(summary.get("promotion_status")),
                replay_labels=_normalize_strings(summary.get("replay_labels")),
                learning_claimed=_as_bool(summary.get("learning_claimed")),
                runtime_authority=_as_bool(summary.get("runtime_authority")),
                writes_state=_as_bool(summary.get("writes_state")),
                model_provider_used=_as_bool(summary.get("model_provider_used")),
                safe_metadata=dict(summary.get("safe_metadata") or {}),
            )
        else:
            raise ValidationError("missing_or_invalid_summary")
        normalized = FrictionCaseCapturePacket(
            packet_type=_safe_text(packet.get("packet_type")),
            case=case,
            summary=normalized_summary,
            validation=dict(packet.get("validation") or {}),
            safe_metadata=dict(packet.get("safe_metadata") or {}),
            runtime_authority=_as_bool(packet.get("runtime_authority")),
            model_provider_used=_as_bool(packet.get("model_provider_used")),
            writes_state=_as_bool(packet.get("writes_state")),
        )
    else:
        raise ValidationError("packet_must_be_mapping_or_capture_packet")

    if normalized.packet_type != CAPTURE_PACKET_TYPE_V1:
        raise ValidationError("unknown_packet_type")
    validate_friction_case_v1(normalized.case)
    if normalized.summary.case_id != normalized.case.case_id:
        raise ValidationError("summary_case_id_mismatch")
    if normalized.summary.case_type != normalized.case.case_type:
        raise ValidationError("summary_case_type_mismatch")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True


def summarize_friction_case_capture_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, (FrictionCaseCapturePacket, Mapping)):
        raise ValidationError("packet_must_be_mapping_or_capture_packet")
    validate_friction_case_capture_packet_v1(packet)
    normalized = packet if isinstance(packet, FrictionCaseCapturePacket) else build_friction_case_capture_packet_v1(packet["case"], safe_metadata=packet.get("safe_metadata"))
    return to_friction_case_json_safe_v1(
        {
            "packet_type": CAPTURE_PACKET_TYPE_V1,
            "case_id": normalized.case.case_id,
            "case_type": normalized.case.case_type,
            "mismatch_labels": list(normalized.case.mismatch_labels),
            "proposed_update_area": list(normalized.case.proposed_update_area),
            "approval_status": normalized.case.approval_status,
            "promotion_status": normalized.case.promotion_status,
            "replay_labels": list(normalized.case.replay_labels),
            "validation": normalized.validation,
        }
    )


def build_friction_case_capture_batch_v1(cases: Sequence[Any], *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionCaseCaptureBatch:
    normalized_cases = tuple(_coerce_case(case) for case in cases)
    summary = summarize_friction_case_batch_v1(normalized_cases)
    batch = FrictionCaseCaptureBatch(
        packet_type=CAPTURE_PACKET_TYPE_V1,
        cases=normalized_cases,
        summary=summary,
        validation={"valid": True, "blocked": False, "blocked_labels": []},
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_case_capture_batch_v1(batch)
    return batch


def validate_friction_case_capture_batch_v1(batch: Any) -> bool:
    if isinstance(batch, FrictionCaseCaptureBatch):
        normalized = batch
    elif isinstance(batch, Mapping):
        cases = tuple(_coerce_case(case) for case in _as_list(batch.get("cases")))
        normalized = FrictionCaseCaptureBatch(
            packet_type=_safe_text(batch.get("packet_type")),
            cases=cases,
            summary=dict(batch.get("summary") or {}),
            validation=dict(batch.get("validation") or {}),
            safe_metadata=dict(batch.get("safe_metadata") or {}),
            runtime_authority=_as_bool(batch.get("runtime_authority")),
            model_provider_used=_as_bool(batch.get("model_provider_used")),
            writes_state=_as_bool(batch.get("writes_state")),
        )
    else:
        raise ValidationError("batch_must_be_mapping_or_capture_batch")

    if normalized.packet_type != CAPTURE_PACKET_TYPE_V1:
        raise ValidationError("unknown_packet_type")
    case_ids = [case.case_id for case in normalized.cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationError("duplicate_case_id")
    for case in normalized.cases:
        validate_friction_case_v1(case)
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True


def summarize_friction_case_batch_v1(cases: Sequence[Any]) -> dict[str, Any]:
    normalized_cases = tuple(_coerce_case(case) for case in cases)
    case_type_counts = Counter(case.case_type for case in normalized_cases)
    mismatch_counts = Counter(label for case in normalized_cases for label in case.mismatch_labels)
    proposed_update_counts = Counter(area for case in normalized_cases for area in case.proposed_update_area)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "total_cases": len(normalized_cases),
        "case_type_counts": dict(sorted(case_type_counts.items())),
        "mismatch_label_counts": dict(sorted(mismatch_counts.items())),
        "proposed_update_area_counts": dict(sorted(proposed_update_counts.items())),
        "case_ids": [case.case_id for case in normalized_cases],
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
    }


def build_initial_renderer_friction_cases_v1() -> tuple[FrictionCase, ...]:
    return (
        build_friction_case_v1(
            case_id="what_is_weslr_identity_friction",
            case_type="missing_identity_directness",
            safe_prompt_descriptor="what is weslr identity friction",
            prompt_labels=("what is weslr", "what are you", "identity", "status"),
            actual_render_mode="clarifying_question",
            actual_method_id="clarifying_question_answer_v1",
            actual_shape_id="clarifying_question",
            actual_case_id="clarification_case",
            actual_route_id="clarification_route",
            expected_render_mode="direct_bounded",
            expected_method_id="verified_identity_status_answer_v1",
            expected_shape_id="direct_bounded_answer",
            expected_case_id="identity_self_description_case",
            expected_route_id="identity_status_route",
            mismatch_labels=("answer_shape_mismatch", "too_cautious", "wrong_case_priority"),
            owner_correction="Answer directly with bounded identity and status instead of asking for clarification.",
            proposed_update_area=("response_method_selector", "cognition_case_registry", "no_model_bounded_renderer"),
            replay_labels=("what weslr", "what are you", "identity", "status"),
            approval_status="captured_only",
            promotion_status="not_promoted",
            learning_claimed=False,
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            safe_metadata={"source": "ocw_local_server_test", "case_family": "identity"},
        ),
        build_friction_case_v1(
            case_id="what_can_you_do_now_capability_friction",
            case_type="missing_capability_orientation",
            safe_prompt_descriptor="what can you do now capability friction",
            prompt_labels=("what can you do", "capability", "now", "help"),
            actual_render_mode="clarifying_question",
            actual_method_id="clarifying_question_answer_v1",
            actual_shape_id="clarifying_question",
            actual_case_id="clarification_case",
            actual_route_id="clarification_route",
            expected_render_mode="direct_bounded",
            expected_method_id="capability_orientation_answer_v1",
            expected_shape_id="direct_bounded_answer",
            expected_case_id="capability_orientation_case",
            expected_route_id="capability_orientation_route",
            mismatch_labels=("missing_capability_orientation", "wrong_case_priority"),
            owner_correction="Orient capability directly instead of falling back to clarification.",
            proposed_update_area=("response_method_selector", "cognition_case_registry"),
            replay_labels=("what can you do", "capability", "now", "help"),
            approval_status="captured_only",
            promotion_status="not_promoted",
            learning_claimed=False,
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            safe_metadata={"source": "ocw_local_server_test", "case_family": "capability"},
        ),
        build_friction_case_v1(
            case_id="unknown_word_blorvatek_friction",
            case_type="unknown_friction_not_preferred",
            safe_prompt_descriptor="unknown word blorvatek friction",
            prompt_labels=("unknown term", "blorvatek", "unknown word", "language discovery"),
            actual_render_mode="clarifying_question",
            actual_method_id="clarifying_question_answer_v1",
            actual_shape_id="clarifying_question",
            actual_case_id="clarification_case",
            actual_route_id="clarification_route",
            expected_render_mode="unknown_friction",
            expected_method_id="unknown_engine_branch_friction_answer_v1",
            expected_shape_id="unknown_friction_branch_answer",
            expected_case_id="unknown_word_or_phrase_case",
            expected_route_id="unknown_word_phrase_route",
            mismatch_labels=("unknown_friction_not_preferred", "wrong_case_priority"),
            owner_correction="Route unknown words into the unknown/friction branch rather than generic clarification.",
            proposed_update_area=("unknown_prompt_friction_router", "response_method_selector"),
            replay_labels=("unknown term", "blorvatek", "unknown word", "language discovery"),
            approval_status="captured_only",
            promotion_status="not_promoted",
            learning_claimed=False,
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            safe_metadata={"source": "ocw_local_server_test", "case_family": "unknown_friction"},
        ),
        build_friction_case_v1(
            case_id="upload_files_now_boundary_friction",
            case_type="wrong_boundary_policy",
            safe_prompt_descriptor="upload files now boundary friction",
            prompt_labels=("can upload files now", "not public pilot", "capability boundary"),
            actual_render_mode="clarifying_question",
            actual_method_id="clarifying_question_answer_v1",
            actual_shape_id="clarifying_question",
            actual_case_id="clarification_case",
            actual_route_id="clarification_route",
            expected_render_mode="direct_bounded",
            expected_method_id="capability_orientation_answer_v1",
            expected_shape_id="direct_bounded_answer",
            expected_case_id="capability_orientation_case",
            expected_route_id="capability_orientation_route",
            mismatch_labels=("wrong_boundary_policy", "missing_capability_orientation"),
            owner_correction="State the upload-files capability boundary directly instead of asking a clarifying question.",
            proposed_update_area=("response_method_selector", "no_model_bounded_renderer"),
            replay_labels=("can upload files now", "not public pilot", "capability boundary"),
            approval_status="captured_only",
            promotion_status="not_promoted",
            learning_claimed=False,
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            safe_metadata={"source": "ocw_local_server_test", "case_family": "boundary"},
        ),
    )


__all__ = [
    "ALLOWED_APPROVAL_STATUSES_V1",
    "ALLOWED_CASE_TYPES_V1",
    "ALLOWED_MISMATCH_LABELS_V1",
    "ALLOWED_PROMOTION_STATUSES_V1",
    "ALLOWED_PROPOSED_UPDATE_AREAS_V1",
    "ALLOWED_RENDER_MODES_V1",
    "CASE_TYPE_V1",
    "CAPTURE_PACKET_TYPE_V1",
    "FrictionCase",
    "FrictionCaseCaptureBatch",
    "FrictionCaseCapturePacket",
    "FrictionCaseExpectation",
    "FrictionCaseObservation",
    "FrictionCaseSummary",
    "ValidationError",
    "build_friction_case_capture_batch_v1",
    "build_friction_case_capture_packet_v1",
    "build_friction_case_v1",
    "build_initial_renderer_friction_cases_v1",
    "capture_friction_case_v1",
    "summarize_friction_case_batch_v1",
    "summarize_friction_case_capture_packet_v1",
    "summarize_friction_case_v1",
    "to_friction_case_json_safe_v1",
    "validate_friction_case_capture_batch_v1",
    "validate_friction_case_capture_packet_v1",
    "validate_friction_case_v1",
]
