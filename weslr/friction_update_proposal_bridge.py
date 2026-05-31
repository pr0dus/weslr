"""Metadata-only friction update proposal bridge v1.

This bridge turns captured/replayed friction metadata into governed update
proposal records. It is pure, deterministic, import-safe, and fail-closed.

No selector updates. No renderer updates. No promotion. No auto-apply.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.friction_case_capture import build_initial_renderer_friction_cases_v1, to_friction_case_json_safe_v1
from weslr.friction_replay_harness import (
    FrictionReplayCaseResult,
    FrictionReplayHarnessPacket,
    build_initial_renderer_friction_replay_v1,
    summarize_friction_replay_packet_v1,
    to_friction_replay_json_safe_v1,
    validate_friction_replay_packet_v1,
)

PACKET_TYPE_V1 = "friction_update_proposal_bridge_v1"
SUMMARY_TYPE_V1 = "friction_update_proposal_summary_v1"

ALLOWED_PROPOSAL_TYPES_V1 = {
    "selector_priority_update",
    "case_priority_update",
    "unknown_friction_routing_update",
    "renderer_policy_update",
    "boundary_policy_update",
    "behavior_pack_candidate",
    "replay_test_expansion",
}

ALLOWED_TARGET_UPDATE_AREAS_V1 = {
    "response_method_selector",
    "cognition_case_registry",
    "unknown_prompt_friction_router",
    "no_model_bounded_renderer",
    "friction_replay_harness",
    "behavior_pack_registry",
    "governance_proposal_bridge",
}

ALLOWED_APPROVAL_STATUSES_V1 = {
    "proposal_created",
    "owner_review_required",
    "approved_for_implementation",
    "rejected",
}

ALLOWED_PROMOTION_STATUSES_V1 = {
    "not_promoted",
    "implementation_ready",
    "implemented_pending_replay",
    "promoted_after_replay",
}

ALLOWED_SOURCE_REPLAY_STATUSES_V1 = {
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
    "apply automatically",
)


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FrictionUpdateProposal:
    proposal_id: str
    source_case_id: str
    source_replay_status: str
    proposal_type: str
    target_update_area: tuple[str, ...]
    problem_summary: str
    expected_behavior_summary: str
    proposed_rule_change: str
    affected_method_ids: tuple[str, ...]
    affected_shape_ids: tuple[str, ...]
    affected_case_ids: tuple[str, ...]
    affected_route_ids: tuple[str, ...]
    replay_labels: tuple[str, ...]
    regression_labels: tuple[str, ...]
    risk_labels: tuple[str, ...]
    approval_status: str
    promotion_status: str
    owner_review_required: bool
    safe_to_apply_automatically: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FrictionUpdateProposalSummary:
    summary_type: str
    packet_type: str
    proposal_count: int
    proposal_type_counts: dict[str, int]
    target_update_area_counts: dict[str, int]
    approval_status_counts: dict[str, int]
    promotion_status_counts: dict[str, int]
    source_replay_status_counts: dict[str, int]
    source_case_ids: tuple[str, ...]
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_to_apply_automatically: bool
    owner_review_required: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FrictionUpdateProposalPacket:
    packet_type: str
    proposal_count: int
    proposals: tuple[FrictionUpdateProposal, ...]
    summary: FrictionUpdateProposalSummary
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_to_apply_automatically: bool
    owner_review_required: bool
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



def _coerce_replay_results(replay_packet: Any | None) -> tuple[FrictionReplayCaseResult, ...]:
    if replay_packet is None:
        replay_packet = build_initial_renderer_friction_replay_v1()
    validate_friction_replay_packet_v1(replay_packet)
    if isinstance(replay_packet, FrictionReplayHarnessPacket):
        return replay_packet.results
    results = replay_packet.get("results") if isinstance(replay_packet, Mapping) else None
    if results is None:
        raise ValidationError("missing_replay_results")
    out: list[FrictionReplayCaseResult] = []
    for result in _as_list(results):
        if isinstance(result, FrictionReplayCaseResult):
            out.append(result)
        elif isinstance(result, Mapping):
            out.append(
                FrictionReplayCaseResult(
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
            )
        else:
            raise ValidationError("replay_result_must_be_mapping_or_result")
    return tuple(out)



def _target_for_case(case_id: str) -> tuple[str, ...]:
    if case_id == "what_is_weslr_identity_friction":
        return ("response_method_selector", "cognition_case_registry")
    if case_id == "what_can_you_do_now_capability_friction":
        return ("response_method_selector", "cognition_case_registry")
    if case_id == "unknown_word_blorvatek_friction":
        return ("unknown_prompt_friction_router", "response_method_selector")
    if case_id == "upload_files_now_boundary_friction":
        return ("response_method_selector", "no_model_bounded_renderer")
    return ("governance_proposal_bridge",)



def _proposal_type_for_case(case_id: str) -> str:
    if case_id == "what_is_weslr_identity_friction":
        return "selector_priority_update"
    if case_id == "what_can_you_do_now_capability_friction":
        return "case_priority_update"
    if case_id == "unknown_word_blorvatek_friction":
        return "unknown_friction_routing_update"
    if case_id == "upload_files_now_boundary_friction":
        return "boundary_policy_update"
    return "replay_test_expansion"



def _proposal_rule_for_case(case_id: str) -> tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if case_id == "what_is_weslr_identity_friction":
        return (
            "WESLR identity/self-description signals should avoid generic clarification when direct bounded identity is available.",
            "Prefer verified_identity_status_answer_v1 with direct_bounded_answer and identity_self_description_case over clarification.",
            ("verified_identity_status_answer_v1", "clarifying_question_answer_v1"),
            ("direct_bounded_answer", "clarifying_question"),
            ("identity_self_description_case", "clarification_needed_case"),
            ("identity_status_route", "clarification_route"),
        )
    if case_id == "what_can_you_do_now_capability_friction":
        return (
            "Capability/current-ability signals should prefer direct bounded capability orientation over generic clarification.",
            "Prefer capability_orientation_answer_v1 with direct_bounded_answer and capability_orientation_case.",
            ("capability_orientation_answer_v1", "clarifying_question_answer_v1"),
            ("direct_bounded_answer", "clarifying_question"),
            ("capability_orientation_case", "clarification_needed_case"),
            ("capability_orientation_route", "clarification_route"),
        )
    if case_id == "unknown_word_blorvatek_friction":
        return (
            "Unknown term / unknown word signals should route into the unknown/friction branch rather than generic clarification.",
            "Prefer unknown_engine_branch_friction_answer_v1 with unknown_friction_branch_answer and unknown_word_or_phrase_case.",
            ("unknown_engine_branch_friction_answer_v1", "clarifying_question_answer_v1"),
            ("unknown_friction_branch_answer", "clarifying_question"),
            ("unknown_word_or_phrase_case", "clarification_needed_case"),
            ("unknown_word_phrase_route", "clarification_route"),
        )
    if case_id == "upload_files_now_boundary_friction":
        return (
            "Capability boundary questions about inactive upload/payment/marketplace actions should not be answered as open clarification.",
            "Prefer capability orientation or refusal/boundary handling with direct bounded or refusal boundary shapes.",
            ("capability_orientation_answer_v1", "refusal_boundary_answer_v1", "clarifying_question_answer_v1"),
            ("direct_bounded_answer", "refusal_boundary_answer", "clarifying_question"),
            ("capability_orientation_case", "refusal_boundary_case", "clarification_needed_case"),
            ("capability_orientation_route", "refusal_boundary_route", "clarification_route"),
        )
    return (
        "Replay-derived friction case should be turned into a governed proposal candidate.",
        "Use the replay observation to propose a bounded governed update.",
        (),
        (),
        (),
        (),
    )



def _default_regression_labels(case_id: str) -> tuple[str, ...]:
    labels = (
        "what are you",
        "are you an llm",
        "are you agi",
        "what can you do",
        "can I upload files",
        "can I pay now",
        "marketplace active",
        "unknown term",
        "new word",
        "needs evidence",
        "unsafe request",
        "memory question",
    )
    if case_id == "what_is_weslr_identity_friction":
        return labels
    if case_id == "what_can_you_do_now_capability_friction":
        return labels
    if case_id == "unknown_word_blorvatek_friction":
        return labels
    if case_id == "upload_files_now_boundary_friction":
        return labels
    return labels



def build_friction_update_proposal_v1(
    *,
    proposal_id: str,
    source_case_id: str,
    source_replay_status: str,
    proposal_type: str,
    target_update_area: Sequence[str] | str,
    problem_summary: str,
    expected_behavior_summary: str,
    proposed_rule_change: str,
    affected_method_ids: Sequence[str] | str,
    affected_shape_ids: Sequence[str] | str,
    affected_case_ids: Sequence[str] | str,
    affected_route_ids: Sequence[str] | str,
    replay_labels: Sequence[str] | str,
    regression_labels: Sequence[str] | str,
    risk_labels: Sequence[str] | str,
    approval_status: str,
    promotion_status: str,
    owner_review_required: bool = True,
    safe_to_apply_automatically: bool = False,
    learning_claimed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    safe_metadata: Mapping[str, Any] | None = None,
) -> FrictionUpdateProposal:
    proposal = FrictionUpdateProposal(
        proposal_id=_safe_text(proposal_id),
        source_case_id=_safe_text(source_case_id),
        source_replay_status=_safe_text(source_replay_status),
        proposal_type=_safe_text(proposal_type),
        target_update_area=_normalize_strings(target_update_area),
        problem_summary=_safe_text(problem_summary),
        expected_behavior_summary=_safe_text(expected_behavior_summary),
        proposed_rule_change=_safe_text(proposed_rule_change),
        affected_method_ids=_normalize_strings(affected_method_ids),
        affected_shape_ids=_normalize_strings(affected_shape_ids),
        affected_case_ids=_normalize_strings(affected_case_ids),
        affected_route_ids=_normalize_strings(affected_route_ids),
        replay_labels=_normalize_strings(replay_labels),
        regression_labels=_normalize_labels(regression_labels),
        risk_labels=_normalize_labels(risk_labels),
        approval_status=_safe_text(approval_status),
        promotion_status=_safe_text(promotion_status),
        owner_review_required=bool(owner_review_required),
        safe_to_apply_automatically=bool(safe_to_apply_automatically),
        learning_claimed=bool(learning_claimed),
        runtime_authority=bool(runtime_authority),
        writes_state=bool(writes_state),
        model_provider_used=bool(model_provider_used),
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_update_proposal_v1(proposal)
    return proposal



def _proposal_for_replay_result(result: FrictionReplayCaseResult) -> FrictionUpdateProposal:
    problem_summary, expected_behavior_summary, affected_method_ids, affected_shape_ids, affected_case_ids, affected_route_ids = _proposal_rule_for_case(result.case_id)
    proposal_type = _proposal_type_for_case(result.case_id)
    target_update_area = _target_for_case(result.case_id)
    risk_labels = (
        "overfit_to_single_phrase",
        "generic_clarification_regression",
        "route_priority_drift",
    )
    if result.case_id == "unknown_word_blorvatek_friction":
        risk_labels = (
            "overfit_to_specific_unknown_token",
            "generic_clarification_regression",
            "route_priority_drift",
        )
    if result.case_id == "upload_files_now_boundary_friction":
        risk_labels = (
            "boundary_underreach",
            "capability_boundary_regression",
            "generic_clarification_regression",
        )
    return build_friction_update_proposal_v1(
        proposal_id=f"{proposal_type}__{result.case_id}",
        source_case_id=result.case_id,
        source_replay_status=result.match_status,
        proposal_type=proposal_type,
        target_update_area=target_update_area,
        problem_summary=problem_summary,
        expected_behavior_summary=expected_behavior_summary,
        proposed_rule_change=expected_behavior_summary,
        affected_method_ids=affected_method_ids,
        affected_shape_ids=affected_shape_ids,
        affected_case_ids=affected_case_ids,
        affected_route_ids=affected_route_ids,
        replay_labels=result.replay_labels,
        regression_labels=_default_regression_labels(result.case_id),
        risk_labels=risk_labels,
        approval_status="proposal_created",
        promotion_status="not_promoted",
        owner_review_required=True,
        safe_to_apply_automatically=False,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={
            "source_replay_status": result.match_status,
            "source_case_type": result.case_type,
            "source_safe_prompt_descriptor": result.safe_prompt_descriptor,
        },
    )



def build_friction_update_proposals_from_replay_v1(replay_packet: Any | None = None) -> tuple[FrictionUpdateProposal, ...]:
    results = _coerce_replay_results(replay_packet)
    proposals = tuple(_proposal_for_replay_result(result) for result in results)
    return proposals



def build_initial_renderer_friction_update_proposals_v1() -> tuple[FrictionUpdateProposal, ...]:
    return build_friction_update_proposals_from_replay_v1(build_initial_renderer_friction_replay_v1())



def validate_friction_update_proposal_v1(proposal: Any) -> bool:
    if _collect_forbidden_keys(proposal):
        raise ValidationError("forbidden_raw_fields_present")
    if isinstance(proposal, FrictionUpdateProposal):
        normalized = proposal
    elif isinstance(proposal, Mapping):
        normalized = FrictionUpdateProposal(
            proposal_id=_safe_text(proposal.get("proposal_id")),
            source_case_id=_safe_text(proposal.get("source_case_id")),
            source_replay_status=_safe_text(proposal.get("source_replay_status")),
            proposal_type=_safe_text(proposal.get("proposal_type")),
            target_update_area=_normalize_strings(proposal.get("target_update_area")),
            problem_summary=_safe_text(proposal.get("problem_summary")),
            expected_behavior_summary=_safe_text(proposal.get("expected_behavior_summary")),
            proposed_rule_change=_safe_text(proposal.get("proposed_rule_change")),
            affected_method_ids=_normalize_strings(proposal.get("affected_method_ids")),
            affected_shape_ids=_normalize_strings(proposal.get("affected_shape_ids")),
            affected_case_ids=_normalize_strings(proposal.get("affected_case_ids")),
            affected_route_ids=_normalize_strings(proposal.get("affected_route_ids")),
            replay_labels=_normalize_strings(proposal.get("replay_labels")),
            regression_labels=_normalize_labels(proposal.get("regression_labels")),
            risk_labels=_normalize_labels(proposal.get("risk_labels")),
            approval_status=_safe_text(proposal.get("approval_status")),
            promotion_status=_safe_text(proposal.get("promotion_status")),
            owner_review_required=bool(proposal.get("owner_review_required", False)),
            safe_to_apply_automatically=bool(proposal.get("safe_to_apply_automatically", False)),
            learning_claimed=bool(proposal.get("learning_claimed", False)),
            runtime_authority=bool(proposal.get("runtime_authority", False)),
            writes_state=bool(proposal.get("writes_state", False)),
            model_provider_used=bool(proposal.get("model_provider_used", False)),
            safe_metadata=dict(proposal.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("proposal_must_be_mapping_or_proposal")

    if not normalized.proposal_id:
        raise ValidationError("missing_proposal_id")
    if not normalized.source_case_id:
        raise ValidationError("missing_source_case_id")
    if normalized.source_replay_status not in ALLOWED_SOURCE_REPLAY_STATUSES_V1:
        raise ValidationError("unknown_source_replay_status")
    if normalized.proposal_type not in ALLOWED_PROPOSAL_TYPES_V1:
        raise ValidationError("unknown_proposal_type")
    if not normalized.target_update_area:
        raise ValidationError("missing_target_update_area")
    unknown_targets = [item for item in normalized.target_update_area if item not in ALLOWED_TARGET_UPDATE_AREAS_V1]
    if unknown_targets:
        raise ValidationError("unknown_target_update_area")
    if not normalized.problem_summary:
        raise ValidationError("missing_problem_summary")
    if not normalized.expected_behavior_summary:
        raise ValidationError("missing_expected_behavior_summary")
    if not normalized.proposed_rule_change:
        raise ValidationError("missing_proposed_rule_change")
    if not normalized.affected_method_ids:
        raise ValidationError("missing_affected_method_ids")
    if not normalized.affected_shape_ids:
        raise ValidationError("missing_affected_shape_ids")
    if not normalized.affected_case_ids:
        raise ValidationError("missing_affected_case_ids")
    if not normalized.affected_route_ids:
        raise ValidationError("missing_affected_route_ids")
    if not normalized.replay_labels:
        raise ValidationError("missing_replay_labels")
    if not normalized.regression_labels:
        raise ValidationError("missing_regression_labels")
    if not normalized.risk_labels:
        raise ValidationError("missing_risk_labels")
    if normalized.approval_status not in ALLOWED_APPROVAL_STATUSES_V1:
        raise ValidationError("unknown_approval_status")
    if normalized.promotion_status not in ALLOWED_PROMOTION_STATUSES_V1:
        raise ValidationError("unknown_promotion_status")
    if normalized.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true")
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
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_marker(normalized.proposal_id):
        raise ValidationError("unsafe_proposal_id")
    if _contains_forbidden_marker(normalized.problem_summary):
        raise ValidationError("unsafe_problem_summary")
    if _contains_forbidden_marker(normalized.expected_behavior_summary):
        raise ValidationError("unsafe_expected_behavior_summary")
    if _contains_forbidden_marker(normalized.proposed_rule_change):
        raise ValidationError("unsafe_proposed_rule_change")
    if _contains_forbidden_marker(normalized.safe_metadata):
        raise ValidationError("unsafe_safe_metadata")
    return True



def summarize_friction_update_proposal_v1(proposal: Any) -> dict[str, Any]:
    validate_friction_update_proposal_v1(proposal)
    normalized = proposal if isinstance(proposal, FrictionUpdateProposal) else build_friction_update_proposal_v1(**proposal)
    return to_friction_update_proposal_json_safe_v1(
        {
            "proposal_id": normalized.proposal_id,
            "source_case_id": normalized.source_case_id,
            "source_replay_status": normalized.source_replay_status,
            "proposal_type": normalized.proposal_type,
            "target_update_area": list(normalized.target_update_area),
            "approval_status": normalized.approval_status,
            "promotion_status": normalized.promotion_status,
            "owner_review_required": normalized.owner_review_required,
            "safe_to_apply_automatically": normalized.safe_to_apply_automatically,
            "regression_labels": list(normalized.regression_labels),
            "risk_labels": list(normalized.risk_labels),
        }
    )



def to_friction_update_proposal_json_safe_v1(value: Any) -> Any:
    return _json_safe(deepcopy(value))



def build_friction_update_proposal_packet_v1(proposals: Sequence[Any], *, safe_metadata: Mapping[str, Any] | None = None) -> FrictionUpdateProposalPacket:
    normalized_proposals = tuple(
        proposal if isinstance(proposal, FrictionUpdateProposal) else build_friction_update_proposal_v1(**proposal)
        for proposal in proposals
    )
    packet = FrictionUpdateProposalPacket(
        packet_type=PACKET_TYPE_V1,
        proposal_count=len(normalized_proposals),
        proposals=normalized_proposals,
        summary=FrictionUpdateProposalSummary(
            summary_type=SUMMARY_TYPE_V1,
            packet_type=PACKET_TYPE_V1,
            proposal_count=len(normalized_proposals),
            proposal_type_counts=dict(sorted(Counter(p.proposal_type for p in normalized_proposals).items())),
            target_update_area_counts=dict(sorted(Counter(area for p in normalized_proposals for area in p.target_update_area).items())),
            approval_status_counts=dict(sorted(Counter(p.approval_status for p in normalized_proposals).items())),
            promotion_status_counts=dict(sorted(Counter(p.promotion_status for p in normalized_proposals).items())),
            source_replay_status_counts=dict(sorted(Counter(p.source_replay_status for p in normalized_proposals).items())),
            source_case_ids=tuple(p.source_case_id for p in normalized_proposals),
            learning_claimed=False,
            runtime_authority=False,
            writes_state=False,
            model_provider_used=False,
            safe_to_apply_automatically=False,
            owner_review_required=True,
            safe_metadata=dict(safe_metadata or {}),
        ),
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_to_apply_automatically=False,
        owner_review_required=True,
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_friction_update_proposal_packet_v1(packet)
    return packet



def validate_friction_update_proposal_packet_v1(packet: Any) -> bool:
    if _collect_forbidden_keys(packet):
        raise ValidationError("forbidden_raw_fields_present")
    if isinstance(packet, FrictionUpdateProposalPacket):
        normalized = packet
    elif isinstance(packet, Mapping):
        proposals = tuple(
            proposal if isinstance(proposal, FrictionUpdateProposal) else build_friction_update_proposal_v1(**proposal)
            for proposal in _as_list(packet.get("proposals"))
        )
        summary = packet.get("summary")
        if isinstance(summary, FrictionUpdateProposalSummary):
            normalized_summary = summary
        elif isinstance(summary, Mapping):
            normalized_summary = FrictionUpdateProposalSummary(
                summary_type=_safe_text(summary.get("summary_type")),
                packet_type=_safe_text(summary.get("packet_type")),
                proposal_count=int(summary.get("proposal_count", len(proposals))),
                proposal_type_counts=dict(summary.get("proposal_type_counts") or {}),
                target_update_area_counts=dict(summary.get("target_update_area_counts") or {}),
                approval_status_counts=dict(summary.get("approval_status_counts") or {}),
                promotion_status_counts=dict(summary.get("promotion_status_counts") or {}),
                source_replay_status_counts=dict(summary.get("source_replay_status_counts") or {}),
                source_case_ids=tuple(_normalize_strings(summary.get("source_case_ids"))),
                learning_claimed=bool(summary.get("learning_claimed", False)),
                runtime_authority=bool(summary.get("runtime_authority", False)),
                writes_state=bool(summary.get("writes_state", False)),
                model_provider_used=bool(summary.get("model_provider_used", False)),
                safe_to_apply_automatically=bool(summary.get("safe_to_apply_automatically", False)),
                owner_review_required=bool(summary.get("owner_review_required", False)),
                safe_metadata=dict(summary.get("safe_metadata") or {}),
            )
        else:
            raise ValidationError("missing_or_invalid_summary")
        normalized = FrictionUpdateProposalPacket(
            packet_type=_safe_text(packet.get("packet_type")),
            proposal_count=int(packet.get("proposal_count", len(proposals))),
            proposals=proposals,
            summary=normalized_summary,
            learning_claimed=bool(packet.get("learning_claimed", False)),
            runtime_authority=bool(packet.get("runtime_authority", False)),
            writes_state=bool(packet.get("writes_state", False)),
            model_provider_used=bool(packet.get("model_provider_used", False)),
            safe_to_apply_automatically=bool(packet.get("safe_to_apply_automatically", False)),
            owner_review_required=bool(packet.get("owner_review_required", False)),
            safe_metadata=dict(packet.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("packet_must_be_mapping_or_proposal_packet")

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
    if normalized.safe_to_apply_automatically is not False:
        raise ValidationError("safe_to_apply_automatically_must_be_false")
    if normalized.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")

    if normalized.proposal_count != len(normalized.proposals):
        raise ValidationError("proposal_count_mismatch")
    proposal_ids = [proposal.proposal_id for proposal in normalized.proposals]
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValidationError("duplicate_proposal_id")
    for proposal in normalized.proposals:
        validate_friction_update_proposal_v1(proposal)

    summary = {
        "proposal_count": len(normalized.proposals),
        "proposal_type_counts": dict(sorted(Counter(p.proposal_type for p in normalized.proposals).items())),
        "target_update_area_counts": dict(sorted(Counter(area for p in normalized.proposals for area in p.target_update_area).items())),
        "approval_status_counts": dict(sorted(Counter(p.approval_status for p in normalized.proposals).items())),
        "promotion_status_counts": dict(sorted(Counter(p.promotion_status for p in normalized.proposals).items())),
        "source_replay_status_counts": dict(sorted(Counter(p.source_replay_status for p in normalized.proposals).items())),
        "source_case_ids": tuple(p.source_case_id for p in normalized.proposals),
    }
    if normalized.summary.proposal_count != summary["proposal_count"]:
        raise ValidationError("summary_proposal_count_mismatch")
    if normalized.summary.proposal_type_counts != summary["proposal_type_counts"]:
        raise ValidationError("summary_proposal_type_counts_mismatch")
    if normalized.summary.target_update_area_counts != summary["target_update_area_counts"]:
        raise ValidationError("summary_target_update_area_counts_mismatch")
    if normalized.summary.approval_status_counts != summary["approval_status_counts"]:
        raise ValidationError("summary_approval_status_counts_mismatch")
    if normalized.summary.promotion_status_counts != summary["promotion_status_counts"]:
        raise ValidationError("summary_promotion_status_counts_mismatch")
    if normalized.summary.source_replay_status_counts != summary["source_replay_status_counts"]:
        raise ValidationError("summary_source_replay_status_counts_mismatch")
    if normalized.summary.source_case_ids != summary["source_case_ids"]:
        raise ValidationError("summary_source_case_ids_mismatch")
    if normalized.summary.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.summary.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.summary.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.summary.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.summary.safe_to_apply_automatically is not False:
        raise ValidationError("safe_to_apply_automatically_must_be_false")
    if normalized.summary.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true")
    return True



def summarize_friction_update_proposal_packet_v1(packet: Any) -> dict[str, Any]:
    validate_friction_update_proposal_packet_v1(packet)
    normalized = packet if isinstance(packet, FrictionUpdateProposalPacket) else build_friction_update_proposal_packet_v1(packet.get("proposals") or [], safe_metadata=packet.get("safe_metadata"))
    return to_friction_update_proposal_json_safe_v1(
        {
            "packet_type": normalized.packet_type,
            "proposal_count": normalized.proposal_count,
            "proposal_type_counts": normalized.summary.proposal_type_counts,
            "target_update_area_counts": normalized.summary.target_update_area_counts,
            "approval_status_counts": normalized.summary.approval_status_counts,
            "promotion_status_counts": normalized.summary.promotion_status_counts,
            "source_replay_status_counts": normalized.summary.source_replay_status_counts,
            "source_case_ids": list(normalized.summary.source_case_ids),
            "proposals": [summarize_friction_update_proposal_v1(proposal) for proposal in normalized.proposals],
        }
    )



def build_friction_update_proposals_from_replay_v1(replay_packet: Any | None = None) -> tuple[FrictionUpdateProposal, ...]:
    results = _coerce_replay_results(replay_packet)
    return tuple(_proposal_for_replay_result(result) for result in results)



def build_initial_renderer_friction_update_proposals_v1() -> tuple[FrictionUpdateProposal, ...]:
    return build_friction_update_proposals_from_replay_v1(build_initial_renderer_friction_replay_v1())


__all__ = [
    "ALLOWED_APPROVAL_STATUSES_V1",
    "ALLOWED_PROMOTION_STATUSES_V1",
    "ALLOWED_PROPOSAL_TYPES_V1",
    "ALLOWED_TARGET_UPDATE_AREAS_V1",
    "FrictionUpdateProposal",
    "FrictionUpdateProposalPacket",
    "FrictionUpdateProposalSummary",
    "ValidationError",
    "build_friction_update_proposal_packet_v1",
    "build_friction_update_proposal_v1",
    "build_friction_update_proposals_from_replay_v1",
    "build_initial_renderer_friction_update_proposals_v1",
    "summarize_friction_update_proposal_packet_v1",
    "summarize_friction_update_proposal_v1",
    "to_friction_update_proposal_json_safe_v1",
    "validate_friction_update_proposal_packet_v1",
    "validate_friction_update_proposal_v1",
]
