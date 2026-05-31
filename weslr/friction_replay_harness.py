"""Metadata-only friction replay harness v1.

This harness replays captured friction cases against the current protected
no-model stack and records whether the live metadata path matches the expected
route/method/shape/case/render mode.

It is pure, deterministic, import-safe, and fail-closed.

No model/provider calls. No runtime wiring. No state writes. No promotion.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.friction_case_capture import (
    FrictionCase,
    FrictionCaseObservation,
    ValidationError as FrictionCaseValidationError,
    build_initial_renderer_friction_cases_v1,
    to_friction_case_json_safe_v1,
)
from weslr.no_model_bounded_renderer import render_no_model_bounded_answer_v1, to_no_model_bounded_render_json_safe_v1

PACKET_TYPE_V1 = "friction_replay_harness_v1"
SUMMARY_TYPE_V1 = "friction_replay_summary_v1"

ALLOWED_MATCH_STATUSES_V1 = {
    "passes_expected",
    "fails_expected",
    "partially_matches_expected",
    "blocked_by_boundary",
    "replay_invalid",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
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
class FrictionReplayCaseResult:
    case_id: str
    case_type: str
    safe_prompt_descriptor: str
    observed_render_mode: str
    expected_render_mode: str
    observed_method_id: str
    expected_method_id: str
    observed_shape_id: str
    expected_shape_id: str
    observed_case_id: str
    expected_case_id: str
    observed_route_id: str
    expected_route_id: str
    match_status: str
    mismatch_labels: tuple[str, ...]
    new_mismatch_labels: tuple[str, ...]
    proposed_update_area: tuple[str, ...]
    replay_labels: tuple[str, ...]
    raw_prompt_stored: bool = False
    raw_answer_stored: bool = False
    blocked: bool = False
    needs_clarification: bool = False
    needs_evidence: bool = False
    needs_owner_approval: bool = False
    learning_claimed: bool = False
    runtime_authority: bool = False
    writes_state: bool = False
    model_provider_used: bool = False
    proposal_created: bool = False
    promotion_performed: bool = False
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FrictionReplaySummary:
    summary_type: str
    packet_type: str
    case_count: int
    passed_count: int
    failed_count: int
    partial_count: int
    blocked_count: int
    invalid_count: int
    result_case_ids: tuple[str, ...]
    match_status_counts: dict[str, int]
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    proposal_created: bool
    promotion_performed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FrictionReplayHarnessPacket:
    packet_type: str
    case_count: int
    passed_count: int
    failed_count: int
    partial_count: int
    blocked_count: int
    invalid_count: int
    results: tuple[FrictionReplayCaseResult, ...]
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    proposal_created: bool
    promotion_performed: bool
    safe_metadata: dict[str, Any] | None = None



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



def _coerce_case(value: Any) -> FrictionCase:
    if isinstance(value, FrictionCase):
        return value
    if isinstance(value, Mapping):
        actual = value.get("actual") or {}
        expected = value.get("expected") or {}
        if isinstance(actual, FrictionCaseObservation):
            actual_obs = actual
        else:
            actual_obs = FrictionCaseObservation(
                render_mode=_safe_text(actual.get("render_mode")),
                method_id=_safe_text(actual.get("method_id")),
                shape_id=_safe_text(actual.get("shape_id")),
                case_id=_safe_text(actual.get("case_id")),
                route_id=_safe_text(actual.get("route_id")),
            )
        if isinstance(expected, Mapping):
            expected_obs = FrictionCaseObservation(
                render_mode=_safe_text(expected.get("render_mode")),
                method_id=_safe_text(expected.get("method_id")),
                shape_id=_safe_text(expected.get("shape_id")),
                case_id=_safe_text(expected.get("case_id")),
                route_id=_safe_text(expected.get("route_id")),
            )
        else:
            expected_obs = expected
        safe_metadata = value.get("safe_metadata")
        if not isinstance(safe_metadata, Mapping):
            safe_metadata = {}
        return FrictionCase(
            case_id=_safe_text(value.get("case_id")),
            case_type=_safe_text(value.get("case_type")),
            safe_prompt_descriptor=_safe_text(value.get("safe_prompt_descriptor")),
            prompt_labels=_normalize_strings(value.get("prompt_labels")),
            actual=actual_obs,
            expected=expected_obs,
            mismatch_labels=_normalize_labels(value.get("mismatch_labels")),
            owner_correction=_safe_text(value.get("owner_correction")),
            proposed_update_area=_normalize_strings(value.get("proposed_update_area")),
            replay_labels=_normalize_strings(value.get("replay_labels")),
            approval_status=_safe_text(value.get("approval_status")),
            promotion_status=_safe_text(value.get("promotion_status")),
            learning_claimed=bool(value.get("learning_claimed", False)),
            runtime_authority=bool(value.get("runtime_authority", False)),
            writes_state=bool(value.get("writes_state", False)),
            model_provider_used=bool(value.get("model_provider_used", False)),
            safe_metadata=dict(safe_metadata),
        )
    raise ValidationError("friction_case_must_be_mapping_or_friction_case")



def _extract_observed_response(case: FrictionCase, observed_response: Any | None) -> dict[str, Any]:
    if observed_response is None:
        labels = list(case.replay_labels or case.prompt_labels or (case.safe_prompt_descriptor,))
        observed_response = to_no_model_bounded_render_json_safe_v1(
            render_no_model_bounded_answer_v1(labels, context_signals={"source": "friction_replay_harness_v1"})
        )
    if not isinstance(observed_response, Mapping):
        raise ValidationError("observed_response_must_be_mapping")
    if _collect_forbidden_keys(observed_response):
        raise ValidationError("forbidden_raw_fields_present")
    return dict(observed_response)



def _case_has_boundary_flags(observed: Mapping[str, Any]) -> bool:
    return any(
        bool(observed.get(field))
        for field in ("blocked", "needs_clarification", "needs_evidence", "needs_owner_approval")
    )



def _match_status_for_case(case: FrictionCase, observed: Mapping[str, Any]) -> str:
    if not observed:
        return "replay_invalid"
    if observed.get("model_provider_used") is True or observed.get("runtime_authority") is True or observed.get("writes_state") is True:
        return "replay_invalid"
    if _case_has_boundary_flags(observed) or bool(observed.get("blocked")):
        return "blocked_by_boundary"

    observed_fields = (
        _safe_text(observed.get("render_mode")),
        _safe_text(observed.get("selected_method_id")),
        _safe_text(observed.get("selected_shape_id")),
        _safe_text(observed.get("selected_case_id")),
        _safe_text(observed.get("selected_route_id")),
    )
    expected_fields = (
        case.expected.render_mode,
        case.expected.method_id,
        case.expected.shape_id,
        case.expected.case_id,
        case.expected.route_id,
    )
    matches = sum(1 for observed_value, expected_value in zip(observed_fields, expected_fields) if observed_value == expected_value)
    if matches == len(expected_fields):
        return "passes_expected"
    if matches >= 2:
        return "partially_matches_expected"
    return "fails_expected"



def build_friction_replay_case_result_v1(friction_case: Any, observed_response: Any | None = None) -> FrictionReplayCaseResult:
    case = _coerce_case(friction_case)
    observed = _extract_observed_response(case, observed_response)
    match_status = _match_status_for_case(case, observed)
    new_mismatch_labels = tuple(
        label
        for label in (
            "answer_shape_mismatch" if _safe_text(observed.get("render_mode")) != case.expected.render_mode else "",
            "wrong_case_priority" if _safe_text(observed.get("selected_case_id")) != case.expected.case_id else "",
            "wrong_boundary_policy" if bool(observed.get("blocked")) and case.case_type != "wrong_boundary_policy" else "",
            "missing_capability_orientation" if case.case_type == "missing_capability_orientation" and _safe_text(observed.get("render_mode")) != "direct_bounded" else "",
            "missing_identity_directness" if case.case_type == "missing_identity_directness" and _safe_text(observed.get("render_mode")) != "direct_bounded" else "",
            "unknown_friction_not_preferred" if case.case_type == "unknown_friction_not_preferred" and _safe_text(observed.get("render_mode")) != "unknown_friction" else "",
        )
        if label
    )
    return FrictionReplayCaseResult(
        case_id=case.case_id,
        case_type=case.case_type,
        safe_prompt_descriptor=case.safe_prompt_descriptor,
        observed_render_mode=_safe_text(observed.get("render_mode")),
        expected_render_mode=case.expected.render_mode,
        observed_method_id=_safe_text(observed.get("selected_method_id")),
        expected_method_id=case.expected.method_id,
        observed_shape_id=_safe_text(observed.get("selected_shape_id")),
        expected_shape_id=case.expected.shape_id,
        observed_case_id=_safe_text(observed.get("selected_case_id")),
        expected_case_id=case.expected.case_id,
        observed_route_id=_safe_text(observed.get("selected_route_id")),
        expected_route_id=case.expected.route_id,
        match_status=match_status,
        mismatch_labels=case.mismatch_labels,
        new_mismatch_labels=new_mismatch_labels,
        proposed_update_area=case.proposed_update_area,
        replay_labels=case.replay_labels,
        raw_prompt_stored=False,
        raw_answer_stored=False,
        blocked=bool(observed.get("blocked")),
        needs_clarification=bool(observed.get("needs_clarification")),
        needs_evidence=bool(observed.get("needs_evidence")),
        needs_owner_approval=bool(observed.get("needs_owner_approval")),
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=bool(observed.get("model_provider_used")),
        proposal_created=False,
        promotion_performed=False,
        safe_metadata={
            "case_safe_metadata": to_friction_case_json_safe_v1(case.safe_metadata),
            "observed_safe_metadata": to_friction_case_json_safe_v1(observed.get("safe_metadata") or {}),
        },
    )



def validate_friction_replay_case_result_v1(result: Any) -> bool:
    if isinstance(result, FrictionReplayCaseResult):
        normalized = result
    elif isinstance(result, Mapping):
        normalized = FrictionReplayCaseResult(
            case_id=_safe_text(result.get("case_id")),
            case_type=_safe_text(result.get("case_type")),
            safe_prompt_descriptor=_safe_text(result.get("safe_prompt_descriptor")),
            observed_render_mode=_safe_text(result.get("observed_render_mode")),
            expected_render_mode=_safe_text(result.get("expected_render_mode")),
            observed_method_id=_safe_text(result.get("observed_method_id")),
            expected_method_id=_safe_text(result.get("expected_method_id")),
            observed_shape_id=_safe_text(result.get("observed_shape_id")),
            expected_shape_id=_safe_text(result.get("expected_shape_id")),
            observed_case_id=_safe_text(result.get("observed_case_id")),
            expected_case_id=_safe_text(result.get("expected_case_id")),
            observed_route_id=_safe_text(result.get("observed_route_id")),
            expected_route_id=_safe_text(result.get("expected_route_id")),
            match_status=_safe_text(result.get("match_status")),
            mismatch_labels=_normalize_labels(result.get("mismatch_labels")),
            new_mismatch_labels=_normalize_labels(result.get("new_mismatch_labels")),
            proposed_update_area=_normalize_strings(result.get("proposed_update_area")),
            replay_labels=_normalize_strings(result.get("replay_labels")),
            raw_prompt_stored=bool(result.get("raw_prompt_stored", False)),
            raw_answer_stored=bool(result.get("raw_answer_stored", False)),
            blocked=bool(result.get("blocked", False)),
            needs_clarification=bool(result.get("needs_clarification", False)),
            needs_evidence=bool(result.get("needs_evidence", False)),
            needs_owner_approval=bool(result.get("needs_owner_approval", False)),
            learning_claimed=bool(result.get("learning_claimed", False)),
            runtime_authority=bool(result.get("runtime_authority", False)),
            writes_state=bool(result.get("writes_state", False)),
            model_provider_used=bool(result.get("model_provider_used", False)),
            proposal_created=bool(result.get("proposal_created", False)),
            promotion_performed=bool(result.get("promotion_performed", False)),
            safe_metadata=dict(result.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("result_must_be_mapping_or_replay_case_result")

    if not normalized.case_id:
        raise ValidationError("missing_case_id")
    if not normalized.case_type:
        raise ValidationError("missing_case_type")
    if not normalized.safe_prompt_descriptor:
        raise ValidationError("missing_safe_prompt_descriptor")
    if not normalized.observed_render_mode:
        raise ValidationError("missing_observed_render_mode")
    if not normalized.expected_render_mode:
        raise ValidationError("missing_expected_render_mode")
    if not normalized.observed_method_id:
        raise ValidationError("missing_observed_method_id")
    if not normalized.expected_method_id:
        raise ValidationError("missing_expected_method_id")
    if not normalized.observed_shape_id:
        raise ValidationError("missing_observed_shape_id")
    if not normalized.expected_shape_id:
        raise ValidationError("missing_expected_shape_id")
    if not normalized.observed_case_id:
        raise ValidationError("missing_observed_case_id")
    if not normalized.expected_case_id:
        raise ValidationError("missing_expected_case_id")
    if not normalized.observed_route_id:
        raise ValidationError("missing_observed_route_id")
    if not normalized.expected_route_id:
        raise ValidationError("missing_expected_route_id")
    if normalized.match_status not in ALLOWED_MATCH_STATUSES_V1:
        raise ValidationError("unknown_match_status")
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
    if normalized.raw_prompt_stored is not False:
        raise ValidationError("raw_prompt_stored_must_be_false")
    if normalized.raw_answer_stored is not False:
        raise ValidationError("raw_answer_stored_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_marker(normalized.safe_prompt_descriptor):
        raise ValidationError("unsafe_safe_prompt_descriptor")
    return True



def summarize_friction_replay_case_result_v1(result: Any) -> dict[str, Any]:
    validate_friction_replay_case_result_v1(result)
    normalized = result if isinstance(result, FrictionReplayCaseResult) else build_friction_replay_case_result_v1(result)
    return to_friction_replay_json_safe_v1(
        {
            "case_id": normalized.case_id,
            "case_type": normalized.case_type,
            "match_status": normalized.match_status,
            "observed_render_mode": normalized.observed_render_mode,
            "expected_render_mode": normalized.expected_render_mode,
            "observed_method_id": normalized.observed_method_id,
            "expected_method_id": normalized.expected_method_id,
            "observed_shape_id": normalized.observed_shape_id,
            "expected_shape_id": normalized.expected_shape_id,
            "observed_case_id": normalized.observed_case_id,
            "expected_case_id": normalized.expected_case_id,
            "observed_route_id": normalized.observed_route_id,
            "expected_route_id": normalized.expected_route_id,
            "mismatch_labels": list(normalized.mismatch_labels),
            "new_mismatch_labels": list(normalized.new_mismatch_labels),
            "proposed_update_area": list(normalized.proposed_update_area),
            "replay_labels": list(normalized.replay_labels),
        }
    )



def to_friction_replay_json_safe_v1(value: Any) -> Any:
    return _json_safe(deepcopy(value))



def _summary_from_results(results: Sequence[FrictionReplayCaseResult]) -> dict[str, Any]:
    counts = Counter(result.match_status for result in results)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "packet_type": PACKET_TYPE_V1,
        "case_count": len(results),
        "passed_count": counts.get("passes_expected", 0),
        "failed_count": counts.get("fails_expected", 0),
        "partial_count": counts.get("partially_matches_expected", 0),
        "blocked_count": counts.get("blocked_by_boundary", 0),
        "invalid_count": counts.get("replay_invalid", 0),
        "result_case_ids": [result.case_id for result in results],
        "match_status_counts": dict(sorted(counts.items())),
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "proposal_created": False,
        "promotion_performed": False,
    }



def build_friction_replay_harness_packet_v1(results: Sequence[Any], *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionReplayHarnessPacket:
    normalized_results = tuple(
        result if isinstance(result, FrictionReplayCaseResult) else build_friction_replay_case_result_v1(result)
        for result in results
    )
    summary = _summary_from_results(normalized_results)
    packet = FrictionReplayHarnessPacket(
        packet_type=PACKET_TYPE_V1,
        case_count=summary["case_count"],
        passed_count=summary["passed_count"],
        failed_count=summary["failed_count"],
        partial_count=summary["partial_count"],
        blocked_count=summary["blocked_count"],
        invalid_count=summary["invalid_count"],
        results=normalized_results,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        proposal_created=False,
        promotion_performed=False,
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_replay_packet_v1(packet)
    return packet



def run_friction_replay_v1(friction_cases: Sequence[Any] | None = None, observed_responses: Sequence[Any] | None = None) -> FrictionReplayHarnessPacket:
    cases = tuple(build_initial_renderer_friction_cases_v1() if friction_cases is None else friction_cases)
    results: list[FrictionReplayCaseResult] = []
    if observed_responses is not None and len(observed_responses) != len(cases):
        raise ValidationError("observed_response_count_mismatch")
    for index, case in enumerate(cases):
        response = None if observed_responses is None else observed_responses[index]
        try:
            result = build_friction_replay_case_result_v1(case, observed_response=response)
        except (ValidationError, FrictionCaseValidationError):
            case_obj = _coerce_case(case)
            result = FrictionReplayCaseResult(
                case_id=case_obj.case_id,
                case_type=case_obj.case_type,
                safe_prompt_descriptor=case_obj.safe_prompt_descriptor,
                observed_render_mode="",
                expected_render_mode=case_obj.expected.render_mode,
                observed_method_id="",
                expected_method_id=case_obj.expected.method_id,
                observed_shape_id="",
                expected_shape_id=case_obj.expected.shape_id,
                observed_case_id="",
                expected_case_id=case_obj.expected.case_id,
                observed_route_id="",
                expected_route_id=case_obj.expected.route_id,
                match_status="replay_invalid",
                mismatch_labels=case_obj.mismatch_labels,
                new_mismatch_labels=(),
                proposed_update_area=case_obj.proposed_update_area,
                replay_labels=case_obj.replay_labels,
                raw_prompt_stored=False,
                raw_answer_stored=False,
                blocked=False,
                needs_clarification=False,
                needs_evidence=False,
                needs_owner_approval=False,
                learning_claimed=False,
                runtime_authority=False,
                writes_state=False,
                model_provider_used=False,
                proposal_created=False,
                promotion_performed=False,
                safe_metadata={"replay_error": True},
            )
        results.append(result)
    return build_friction_replay_harness_packet_v1(results, safe_metadata={"case_source": "friction_case_capture_v1"})



def validate_friction_replay_packet_v1(packet: Any) -> bool:
    if isinstance(packet, FrictionReplayHarnessPacket):
        normalized = packet
    elif isinstance(packet, Mapping):
        results = tuple(
            result if isinstance(result, FrictionReplayCaseResult) else build_friction_replay_case_result_v1(result)
            for result in _as_list(packet.get("results"))
        )
        normalized = FrictionReplayHarnessPacket(
            packet_type=_safe_text(packet.get("packet_type")),
            case_count=int(packet.get("case_count", len(results))),
            passed_count=int(packet.get("passed_count", 0)),
            failed_count=int(packet.get("failed_count", 0)),
            partial_count=int(packet.get("partial_count", 0)),
            blocked_count=int(packet.get("blocked_count", 0)),
            invalid_count=int(packet.get("invalid_count", 0)),
            results=results,
            learning_claimed=bool(packet.get("learning_claimed", False)),
            runtime_authority=bool(packet.get("runtime_authority", False)),
            writes_state=bool(packet.get("writes_state", False)),
            model_provider_used=bool(packet.get("model_provider_used", False)),
            proposal_created=bool(packet.get("proposal_created", False)),
            promotion_performed=bool(packet.get("promotion_performed", False)),
            safe_metadata=dict(packet.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("packet_must_be_mapping_or_harness_packet")

    if normalized.packet_type != PACKET_TYPE_V1:
        raise ValidationError("unknown_packet_type")
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

    case_ids = [result.case_id for result in normalized.results]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationError("duplicate_result_case_id")
    for result in normalized.results:
        validate_friction_replay_case_result_v1(result)

    summary = _summary_from_results(normalized.results)
    if normalized.case_count != summary["case_count"]:
        raise ValidationError("case_count_mismatch")
    if normalized.passed_count != summary["passed_count"]:
        raise ValidationError("passed_count_mismatch")
    if normalized.failed_count != summary["failed_count"]:
        raise ValidationError("failed_count_mismatch")
    if normalized.partial_count != summary["partial_count"]:
        raise ValidationError("partial_count_mismatch")
    if normalized.blocked_count != summary["blocked_count"]:
        raise ValidationError("blocked_count_mismatch")
    if normalized.invalid_count != summary["invalid_count"]:
        raise ValidationError("invalid_count_mismatch")
    return True



def summarize_friction_replay_packet_v1(packet: Any) -> dict[str, Any]:
    validate_friction_replay_packet_v1(packet)
    normalized = packet if isinstance(packet, FrictionReplayHarnessPacket) else build_friction_replay_harness_packet_v1(packet["results"], safe_metadata=packet.get("safe_metadata"))
    return to_friction_replay_json_safe_v1(
        {
            "packet_type": normalized.packet_type,
            "case_count": normalized.case_count,
            "passed_count": normalized.passed_count,
            "failed_count": normalized.failed_count,
            "partial_count": normalized.partial_count,
            "blocked_count": normalized.blocked_count,
            "invalid_count": normalized.invalid_count,
            "match_status_counts": _summary_from_results(normalized.results)["match_status_counts"],
            "results": [summarize_friction_replay_case_result_v1(result) for result in normalized.results],
        }
    )



def build_initial_renderer_friction_replay_v1() -> FrictionReplayHarnessPacket:
    return run_friction_replay_v1(build_initial_renderer_friction_cases_v1())


__all__ = [
    "FrictionReplayCaseResult",
    "FrictionReplayHarnessPacket",
    "FrictionReplaySummary",
    "ValidationError",
    "build_friction_replay_case_result_v1",
    "build_friction_replay_harness_packet_v1",
    "build_initial_renderer_friction_replay_v1",
    "run_friction_replay_v1",
    "summarize_friction_replay_case_result_v1",
    "summarize_friction_replay_packet_v1",
    "to_friction_replay_json_safe_v1",
    "validate_friction_replay_case_result_v1",
    "validate_friction_replay_packet_v1",
]
