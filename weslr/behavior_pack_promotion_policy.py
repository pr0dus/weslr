"""Metadata-only behavior pack promotion policy v1.

This helper recommends whether a behavior pack is eligible for internal
promotion based on replay support, proof reports, owner review, and boundary
safety.

It is deterministic, import-safe, and fail-closed.

No live routing. No automatic promotion. No state writes. No model/provider
calls. No public readiness claims. No public ISS wording.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping, Sequence

from weslr.behavior_pack_registry import (
    BehaviorPack,
    BehaviorPackRegistry,
    build_initial_behavior_pack_registry_v1,
)
from weslr.friction_pattern_miner import build_initial_renderer_friction_patterns_v1
from weslr.friction_replay_suite_builder import build_initial_renderer_friction_replay_suites_v1
from weslr.friction_training_proof_report_run import build_initial_friction_training_proof_report_v1

POLICY_TYPE_V1 = "behavior_pack_promotion_policy_v1"
PACKET_TYPE_V1 = "behavior_pack_promotion_packet_v1"

ALLOWED_PROMOTION_ELIGIBILITY_V1 = {
    "eligible_internal_use_only",
    "eligible_for_owner_review",
    "needs_more_replay",
    "needs_proof_report",
    "candidate_only_not_ready",
    "blocked_boundary_risk",
    "blocked_public_claim_risk",
}

ALLOWED_RECOMMENDED_PROMOTION_STATUS_V1 = {
    "keep_candidate",
    "owner_review_required",
    "approved_for_internal_use",
    "promoted_internal_only",
    "blocked",
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

INJECTED_RISK_FLAG_FIELDS_V1 = {
    "agi_claimed",
    "consciousness_claimed",
    "sentience_claimed",
    "official_turing_claimed",
    "certification_claimed",
    "public_ready_claimed",
}

INITIAL_INTERNAL_LABEL_V1 = "WESLR V1.01 internal friction-trained improvement proof"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BehaviorPackPromotionDecision:
    decision_id: str
    pack_id: str
    pack_type: str
    current_status: str
    current_promotion_status: str
    promotion_eligibility: str
    recommended_promotion_status: str
    required_evidence: tuple[str, ...]
    evidence_present: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    risk_labels: tuple[str, ...]
    boundary_labels: tuple[str, ...]
    anti_hardcoding_evidence: tuple[str, ...]
    owner_review_required: bool
    safe_for_internal_use: bool
    safe_to_route_live: bool
    safe_to_apply_automatically: bool
    public_label_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    promotion_performed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BehaviorPackPromotionPacket:
    packet_id: str
    packet_type: str
    decision_count: int
    decisions: tuple[BehaviorPackPromotionDecision, ...]
    eligibility_counts: dict[str, int]
    recommended_status_counts: dict[str, int]
    safe_for_internal_use_count: int
    blocked_count: int
    public_label_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    promotion_performed: bool
    safe_metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Safe conversion helpers
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



def _dedupe_preserve(items: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return tuple(out)



def _normalize_strings(value: Any) -> tuple[str, ...]:
    return _dedupe_preserve(tuple(_safe_text(item) for item in _as_list(value)))



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
            blocked.extend(_collect_forbidden_keys(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_collect_forbidden_keys(item, f"{path}[{index}]") )
    return blocked



def _pack_lookup(registry: BehaviorPackRegistry) -> dict[str, BehaviorPack]:
    return {pack.pack_id: pack for pack in registry.packs}



def _initial_pack_requirements(pack: BehaviorPack) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], str, str, bool]:
    source_patterns = tuple(pack.source_pattern_ids)
    source_suites = tuple(pack.source_replay_suite_ids)
    source_proofs = tuple(pack.source_proof_report_ids)
    required = (
        "source_patterns_present",
        "source_replay_suites_present",
        "proof_report_present",
        "owner_review_required",
        "anti_hardcoding_coverage_present",
    )
    evidence_present = required
    missing = ()
    risks: list[str] = []
    boundary: list[str] = [
        "no_live_routing",
        "no_auto_apply",
        "no_public_label",
        "no_model_provider_use",
        "no_state_writes",
    ]
    if pack.public_label_allowed:
        risks.append("public_claim_risk")
    if pack.agi_claimed:
        risks.append("agi_risk")
    if pack.consciousness_claimed or pack.sentience_claimed:
        risks.append("consciousness_risk")
    if pack.official_turing_claimed or pack.certification_claimed:
        risks.append("official_turing_or_certification_risk")
    if pack.public_ready_claimed:
        risks.append("public_readiness_risk")
    if pack.runtime_authority:
        risks.append("runtime_authority_risk")
    if pack.writes_state:
        risks.append("state_write_risk")
    if pack.model_provider_used:
        risks.append("model_provider_risk")
    if pack.safe_to_route_live:
        risks.append("live_routing_risk")
    if pack.safe_to_apply_automatically:
        risks.append("auto_apply_risk")

    if not risks:
        risks.extend(("internal_only_low_risk", "public_claim_guarded"))

    anti = (
        "source_pattern_ids_known",
        "source_replay_suite_ids_known",
        "source_proof_report_ids_known",
        "boundary_checks_present",
        "public_claim_checks_present",
        "owner_review_gate_present",
    )
    eligibility = "eligible_internal_use_only"
    recommended = "approved_for_internal_use"
    safe_internal = True

    if pack.status == "candidate_only":
        eligibility = "candidate_only_not_ready"
        recommended = "keep_candidate"
        safe_internal = False
        risks = ["candidate_only_not_ready", "owner_review_required"]
    elif not source_suites or not source_patterns:
        eligibility = "needs_more_replay"
        recommended = "owner_review_required"
        safe_internal = False
    elif not source_proofs:
        eligibility = "needs_proof_report"
        recommended = "owner_review_required"
        safe_internal = False
    elif any(risk in {"public_claim_risk", "agi_risk", "consciousness_risk", "official_turing_or_certification_risk", "public_readiness_risk"} for risk in risks):
        eligibility = "blocked_public_claim_risk"
        recommended = "blocked"
        safe_internal = False
    elif any(risk in {"runtime_authority_risk", "state_write_risk", "model_provider_risk", "live_routing_risk", "auto_apply_risk"} for risk in risks):
        eligibility = "blocked_boundary_risk"
        recommended = "blocked"
        safe_internal = False
    elif pack.status not in {"replay_supported", "proof_reviewed_internal"}:
        eligibility = "eligible_for_owner_review"
        recommended = "owner_review_required"
        safe_internal = False

    if pack.status == "candidate_only":
        boundary.append("candidate_only_not_live_routable")
    else:
        boundary.append("replay_or_proof_supported")

    return source_patterns, source_suites, source_proofs, tuple(risks), tuple(boundary), tuple(anti), eligibility, recommended, safe_internal



def _build_decision_from_pack(pack: BehaviorPack, registry: BehaviorPackRegistry | None = None) -> BehaviorPackPromotionDecision:
    source_patterns, source_suites, source_proofs, risks, boundary, anti, eligibility, recommended, safe_internal = _initial_pack_requirements(pack)
    required = (
        "source_patterns_present",
        "source_replay_suites_present",
        "proof_report_present",
        "owner_review_required",
        "anti_hardcoding_coverage_present",
    )
    if pack.status == "candidate_only":
        required = (
            "source_patterns_present",
            "source_replay_suites_present",
            "proof_report_present",
            "owner_review_required",
            "candidate_only_gate",
        )
    evidence_present = required
    missing_evidence = ()
    if registry is not None:
        # Registry is only used as a verification anchor; no dynamic authority.
        if pack.pack_id not in _pack_lookup(registry):
            missing_evidence = ("pack_not_found_in_registry",)
            safe_internal = False
            recommended = "blocked"
            eligibility = "needs_more_replay"

    return BehaviorPackPromotionDecision(
        decision_id=f"behavior_pack_promotion__{pack.pack_id}",
        pack_id=pack.pack_id,
        pack_type=pack.pack_type,
        current_status=pack.status,
        current_promotion_status=pack.promotion_status,
        promotion_eligibility=eligibility,
        recommended_promotion_status=recommended,
        required_evidence=required,
        evidence_present=evidence_present,
        missing_evidence=missing_evidence,
        risk_labels=risks,
        boundary_labels=boundary,
        anti_hardcoding_evidence=anti,
        owner_review_required=True,
        safe_for_internal_use=safe_internal,
        safe_to_route_live=False,
        safe_to_apply_automatically=False,
        public_label_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        promotion_performed=False,
        safe_metadata={
            "source": "initial_behavior_pack_promotion_policy",
            "pack_name": pack.pack_name,
            "pack_scope": pack.scope,
            "internal_label": INITIAL_INTERNAL_LABEL_V1,
        },
    )



def _packet_counts(decisions: Sequence[BehaviorPackPromotionDecision]) -> tuple[dict[str, int], dict[str, int], int, int]:
    eligibility_counts = dict(sorted(Counter(decision.promotion_eligibility for decision in decisions).items()))
    recommended_status_counts = dict(sorted(Counter(decision.recommended_promotion_status for decision in decisions).items()))
    safe_count = sum(1 for decision in decisions if decision.safe_for_internal_use)
    blocked_count = sum(1 for decision in decisions if decision.recommended_promotion_status == "blocked")
    return eligibility_counts, recommended_status_counts, safe_count, blocked_count


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_behavior_pack_promotion_decision_v1(**kwargs: Any) -> BehaviorPackPromotionDecision:
    decision = BehaviorPackPromotionDecision(
        decision_id=_safe_text(kwargs.get("decision_id")),
        pack_id=_safe_text(kwargs.get("pack_id")),
        pack_type=_safe_text(kwargs.get("pack_type")),
        current_status=_safe_text(kwargs.get("current_status")),
        current_promotion_status=_safe_text(kwargs.get("current_promotion_status")),
        promotion_eligibility=_safe_text(kwargs.get("promotion_eligibility")),
        recommended_promotion_status=_safe_text(kwargs.get("recommended_promotion_status")),
        required_evidence=_normalize_strings(kwargs.get("required_evidence")),
        evidence_present=_normalize_strings(kwargs.get("evidence_present")),
        missing_evidence=_normalize_strings(kwargs.get("missing_evidence")),
        risk_labels=_normalize_strings(kwargs.get("risk_labels")),
        boundary_labels=_normalize_strings(kwargs.get("boundary_labels")),
        anti_hardcoding_evidence=_normalize_strings(kwargs.get("anti_hardcoding_evidence")),
        owner_review_required=bool(kwargs.get("owner_review_required", False)),
        safe_for_internal_use=bool(kwargs.get("safe_for_internal_use", False)),
        safe_to_route_live=bool(kwargs.get("safe_to_route_live", False)),
        safe_to_apply_automatically=bool(kwargs.get("safe_to_apply_automatically", False)),
        public_label_allowed=bool(kwargs.get("public_label_allowed", False)),
        iss_internal_reference_allowed=bool(kwargs.get("iss_internal_reference_allowed", False)),
        learning_claimed=bool(kwargs.get("learning_claimed", False)),
        runtime_authority=bool(kwargs.get("runtime_authority", False)),
        writes_state=bool(kwargs.get("writes_state", False)),
        model_provider_used=bool(kwargs.get("model_provider_used", False)),
        promotion_performed=bool(kwargs.get("promotion_performed", False)),
        safe_metadata=dict(kwargs.get("safe_metadata") or {}),
    )
    validate_behavior_pack_promotion_decision_v1(decision)
    return decision



def evaluate_behavior_pack_promotion_v1(pack: Any, registry: BehaviorPackRegistry | Mapping[str, Any] | None = None) -> BehaviorPackPromotionDecision:
    if not isinstance(pack, BehaviorPack):
        if not isinstance(pack, Mapping):
            raise ValidationError("pack_must_be_mapping_or_behavior_pack")
        from weslr.behavior_pack_registry import build_behavior_pack_v1

        pack = build_behavior_pack_v1(**pack)
    registry_obj = None
    if registry is not None:
        registry_obj = registry if isinstance(registry, BehaviorPackRegistry) else build_initial_behavior_pack_registry_v1() if not isinstance(registry, Mapping) else build_initial_behavior_pack_registry_v1() if registry.get("registry_id") == "weslr_behavior_pack_registry_v1" else build_initial_behavior_pack_registry_v1()
        if isinstance(registry, Mapping):
            registry_obj = build_initial_behavior_pack_registry_v1() if registry.get("registry_id") == "weslr_behavior_pack_registry_v1" else build_initial_behavior_pack_registry_v1()
    return _build_decision_from_pack(pack, registry_obj)



def evaluate_behavior_pack_registry_promotion_v1(registry: BehaviorPackRegistry | Mapping[str, Any] | None = None) -> BehaviorPackPromotionPacket:
    registry_obj = build_initial_behavior_pack_registry_v1() if registry is None else (registry if isinstance(registry, BehaviorPackRegistry) else build_initial_behavior_pack_registry_v1())
    decisions = tuple(_build_decision_from_pack(pack, registry_obj) for pack in registry_obj.packs)
    payload = _build_packet_payload(decisions)
    packet = _build_packet_from_mapping(payload)
    validate_behavior_pack_promotion_packet_v1(packet)
    return packet



def build_initial_behavior_pack_promotion_policy_v1() -> BehaviorPackPromotionPacket:
    return evaluate_behavior_pack_registry_promotion_v1(build_initial_behavior_pack_registry_v1())


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_behavior_pack_promotion_decision_v1(decision: Any) -> bool:
    if _collect_forbidden_keys(decision):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(decision, BehaviorPackPromotionDecision):
        normalized = decision
    elif isinstance(decision, Mapping):
        for field_name in INJECTED_RISK_FLAG_FIELDS_V1:
            if bool(decision.get(field_name, False)) is True:
                raise ValidationError(f"{field_name}_must_be_false")
        normalized = BehaviorPackPromotionDecision(
            decision_id=_safe_text(decision.get("decision_id")),
            pack_id=_safe_text(decision.get("pack_id")),
            pack_type=_safe_text(decision.get("pack_type")),
            current_status=_safe_text(decision.get("current_status")),
            current_promotion_status=_safe_text(decision.get("current_promotion_status")),
            promotion_eligibility=_safe_text(decision.get("promotion_eligibility")),
            recommended_promotion_status=_safe_text(decision.get("recommended_promotion_status")),
            required_evidence=_normalize_strings(decision.get("required_evidence")),
            evidence_present=_normalize_strings(decision.get("evidence_present")),
            missing_evidence=_normalize_strings(decision.get("missing_evidence")),
            risk_labels=_normalize_strings(decision.get("risk_labels")),
            boundary_labels=_normalize_strings(decision.get("boundary_labels")),
            anti_hardcoding_evidence=_normalize_strings(decision.get("anti_hardcoding_evidence")),
            owner_review_required=bool(decision.get("owner_review_required", False)),
            safe_for_internal_use=bool(decision.get("safe_for_internal_use", False)),
            safe_to_route_live=bool(decision.get("safe_to_route_live", False)),
            safe_to_apply_automatically=bool(decision.get("safe_to_apply_automatically", False)),
            public_label_allowed=bool(decision.get("public_label_allowed", False)),
            iss_internal_reference_allowed=bool(decision.get("iss_internal_reference_allowed", False)),
            learning_claimed=bool(decision.get("learning_claimed", False)),
            runtime_authority=bool(decision.get("runtime_authority", False)),
            writes_state=bool(decision.get("writes_state", False)),
            model_provider_used=bool(decision.get("model_provider_used", False)),
            promotion_performed=bool(decision.get("promotion_performed", False)),
            safe_metadata=dict(decision.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("decision_must_be_mapping_or_behavior_pack_promotion_decision")

    if not normalized.decision_id:
        raise ValidationError("decision_id_required")
    if not normalized.pack_id:
        raise ValidationError("pack_id_required")
    if not normalized.pack_type:
        raise ValidationError("pack_type_required")
    if not normalized.current_status:
        raise ValidationError("current_status_required")
    if not normalized.current_promotion_status:
        raise ValidationError("current_promotion_status_required")
    if not normalized.promotion_eligibility:
        raise ValidationError("promotion_eligibility_required")
    if normalized.promotion_eligibility not in ALLOWED_PROMOTION_ELIGIBILITY_V1:
        raise ValidationError("unknown_promotion_eligibility")
    if not normalized.recommended_promotion_status:
        raise ValidationError("recommended_promotion_status_required")
    if normalized.recommended_promotion_status not in ALLOWED_RECOMMENDED_PROMOTION_STATUS_V1:
        raise ValidationError("unknown_recommended_promotion_status")
    if not normalized.required_evidence:
        raise ValidationError("required_evidence_required")
    if not normalized.evidence_present:
        raise ValidationError("evidence_present_required")
    if not normalized.risk_labels:
        raise ValidationError("risk_labels_required")
    if not normalized.boundary_labels:
        raise ValidationError("boundary_labels_required")
    if not normalized.anti_hardcoding_evidence:
        raise ValidationError("anti_hardcoding_evidence_required")
    if normalized.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true")
    if normalized.safe_to_route_live is not False:
        raise ValidationError("safe_to_route_live_must_be_false")
    if normalized.safe_to_apply_automatically is not False:
        raise ValidationError("safe_to_apply_automatically_must_be_false")
    if normalized.public_label_allowed is not False:
        raise ValidationError("public_label_allowed_must_be_false")
    if normalized.iss_internal_reference_allowed is not True:
        raise ValidationError("iss_internal_reference_allowed_must_be_true")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.promotion_performed is not False:
        raise ValidationError("promotion_performed_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True



def _build_packet_payload(decisions: Sequence[BehaviorPackPromotionDecision]) -> dict[str, Any]:
    eligibility_counts, recommended_status_counts, safe_count, blocked_count = _packet_counts(decisions)
    return {
        "packet_id": "weslr_behavior_pack_promotion_packet_v1",
        "packet_type": PACKET_TYPE_V1,
        "decision_count": len(decisions),
        "decisions": tuple(decisions),
        "eligibility_counts": eligibility_counts,
        "recommended_status_counts": recommended_status_counts,
        "safe_for_internal_use_count": safe_count,
        "blocked_count": blocked_count,
        "public_label_allowed": False,
        "iss_internal_reference_allowed": True,
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "promotion_performed": False,
        "safe_metadata": {
            "source": "initial_behavior_pack_promotion_policy",
            "internal_label": INITIAL_INTERNAL_LABEL_V1,
        },
    }



def _build_packet_from_mapping(payload: Mapping[str, Any]) -> BehaviorPackPromotionPacket:
    decisions = tuple(
        decision if isinstance(decision, BehaviorPackPromotionDecision) else build_behavior_pack_promotion_decision_v1(**decision)
        for decision in _as_list(payload.get("decisions"))
    )
    return BehaviorPackPromotionPacket(
        packet_id=_safe_text(payload.get("packet_id")),
        packet_type=_safe_text(payload.get("packet_type")),
        decision_count=int(payload.get("decision_count", len(decisions))),
        decisions=decisions,
        eligibility_counts=dict(payload.get("eligibility_counts") or {}),
        recommended_status_counts=dict(payload.get("recommended_status_counts") or {}),
        safe_for_internal_use_count=int(payload.get("safe_for_internal_use_count", sum(1 for decision in decisions if decision.safe_for_internal_use))),
        blocked_count=int(payload.get("blocked_count", sum(1 for decision in decisions if decision.recommended_promotion_status == "blocked"))),
        public_label_allowed=bool(payload.get("public_label_allowed", False)),
        iss_internal_reference_allowed=bool(payload.get("iss_internal_reference_allowed", True)),
        learning_claimed=bool(payload.get("learning_claimed", False)),
        runtime_authority=bool(payload.get("runtime_authority", False)),
        writes_state=bool(payload.get("writes_state", False)),
        model_provider_used=bool(payload.get("model_provider_used", False)),
        promotion_performed=bool(payload.get("promotion_performed", False)),
        safe_metadata=dict(payload.get("safe_metadata") or {}),
    )



def validate_behavior_pack_promotion_packet_v1(packet: Any) -> bool:
    if _collect_forbidden_keys(packet):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(packet, BehaviorPackPromotionPacket):
        normalized = packet
    elif isinstance(packet, Mapping):
        normalized = _build_packet_from_mapping(packet)
    else:
        raise ValidationError("packet_must_be_mapping_or_behavior_pack_promotion_packet")

    if not normalized.packet_id:
        raise ValidationError("packet_id_required")
    if normalized.packet_type != PACKET_TYPE_V1:
        raise ValidationError("unknown_packet_type")
    if normalized.decision_count != len(normalized.decisions):
        raise ValidationError("decision_count_mismatch")
    if normalized.public_label_allowed is not False:
        raise ValidationError("public_label_allowed_must_be_false")
    if normalized.iss_internal_reference_allowed is not True:
        raise ValidationError("iss_internal_reference_allowed_must_be_true")
    if normalized.learning_claimed is not False:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority is not False:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state is not False:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used is not False:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.promotion_performed is not False:
        raise ValidationError("promotion_performed_must_be_false")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")

    decision_ids = [decision.decision_id for decision in normalized.decisions]
    if len(decision_ids) != len(set(decision_ids)):
        raise ValidationError("duplicate_decision_ids")
    for decision in normalized.decisions:
        validate_behavior_pack_promotion_decision_v1(decision)

    eligibility_counts, recommended_status_counts, safe_count, blocked_count = _packet_counts(normalized.decisions)
    if normalized.eligibility_counts != eligibility_counts:
        raise ValidationError("eligibility_count_mismatch")
    if normalized.recommended_status_counts != recommended_status_counts:
        raise ValidationError("recommended_status_count_mismatch")
    if normalized.safe_for_internal_use_count != safe_count:
        raise ValidationError("safe_for_internal_use_count_mismatch")
    if normalized.blocked_count != blocked_count:
        raise ValidationError("blocked_count_mismatch")
    return True


# ---------------------------------------------------------------------------
# Summary / export
# ---------------------------------------------------------------------------


def summarize_behavior_pack_promotion_packet_v1(packet: Any) -> dict[str, Any]:
    normalized = packet if isinstance(packet, BehaviorPackPromotionPacket) else _build_packet_from_mapping(packet)
    validate_behavior_pack_promotion_packet_v1(normalized)
    return {
        "packet_id": normalized.packet_id,
        "packet_type": normalized.packet_type,
        "decision_count": normalized.decision_count,
        "eligibility_counts": dict(normalized.eligibility_counts),
        "recommended_status_counts": dict(normalized.recommended_status_counts),
        "safe_for_internal_use_count": normalized.safe_for_internal_use_count,
        "blocked_count": normalized.blocked_count,
        "public_label_allowed": normalized.public_label_allowed,
        "iss_internal_reference_allowed": normalized.iss_internal_reference_allowed,
        "promotion_performed": normalized.promotion_performed,
    }



def to_behavior_pack_promotion_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


__all__ = [
    "BehaviorPackPromotionDecision",
    "BehaviorPackPromotionPacket",
    "ValidationError",
    "build_behavior_pack_promotion_decision_v1",
    "evaluate_behavior_pack_promotion_v1",
    "evaluate_behavior_pack_registry_promotion_v1",
    "build_initial_behavior_pack_promotion_policy_v1",
    "validate_behavior_pack_promotion_decision_v1",
    "validate_behavior_pack_promotion_packet_v1",
    "summarize_behavior_pack_promotion_packet_v1",
    "to_behavior_pack_promotion_json_safe_v1",
]
