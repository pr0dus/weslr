"""Metadata-only behavior pack registry v1.

This module groups replay-supported or candidate-only behavior packs into a
pure metadata registry. It is deterministic, import-safe, and fail-closed.

No live routing. No automatic promotion. No model/provider/search/advisor
calls. No state writes. No public readiness claims. No public ISS wording.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping, Sequence

from weslr.friction_pattern_miner import build_initial_renderer_friction_patterns_v1
from weslr.friction_replay_suite_builder import build_initial_renderer_friction_replay_suites_v1
from weslr.friction_training_proof_report_run import build_initial_friction_training_proof_report_v1

REGISTRY_TYPE_V1 = "behavior_pack_registry_v1"
REGISTRY_ID_V1 = "weslr_behavior_pack_registry_v1"

ALLOWED_PACK_TYPES_V1 = {
    "core_identity_capability_pack",
    "unknown_term_discovery_pack",
    "inactive_capability_boundary_pack",
    "domain_behavior_candidate_pack",
    "owner_workflow_pack",
    "industrial_automation_candidate_pack",
    "legal_privacy_candidate_pack",
    "website_public_launch_candidate_pack",
    "materials_discovery_candidate_pack",
    "language_vocabulary_discovery_candidate_pack",
}

ALLOWED_STATUS_V1 = {
    "candidate_only",
    "replay_supported",
    "proof_reviewed_internal",
    "owner_review_required",
    "promoted_internal",
    "blocked",
}

ALLOWED_PROMOTION_STATUS_V1 = {
    "not_promoted",
    "candidate_for_review",
    "approved_for_internal_use",
    "promoted_internal_only",
    "rejected",
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

PACK_IDENTITY = "weslr_identity_capability_behavior_pack"
PACK_UNKNOWN = "unknown_term_discovery_behavior_pack"
PACK_BOUNDARY = "inactive_capability_boundary_behavior_pack"
PACK_OWNER = "weslr_owner_workflow_behavior_pack"

PACK_IDS_INITIAL_V1 = (
    PACK_IDENTITY,
    PACK_UNKNOWN,
    PACK_BOUNDARY,
    PACK_OWNER,
)

INITIAL_INTERNAL_LABEL_V1 = "WESLR V1.01 internal friction-trained improvement proof"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BehaviorPack:
    pack_id: str
    pack_name: str
    pack_type: str
    scope: str
    status: str
    source_pattern_ids: tuple[str, ...]
    source_replay_suite_ids: tuple[str, ...]
    source_proof_report_ids: tuple[str, ...]
    domain_vocabulary: tuple[str, ...]
    common_friction_patterns: tuple[str, ...]
    preferred_method_ids: tuple[str, ...]
    preferred_shape_ids: tuple[str, ...]
    preferred_case_ids: tuple[str, ...]
    preferred_route_ids: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    memory_rules: tuple[str, ...]
    boundary_rules: tuple[str, ...]
    anti_overclaim_tests: tuple[str, ...]
    regression_labels: tuple[str, ...]
    promotion_status: str
    owner_review_required: bool
    safe_to_route_live: bool
    safe_to_apply_automatically: bool
    public_label_allowed: bool
    internal_only: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    agi_claimed: bool = False
    consciousness_claimed: bool = False
    sentience_claimed: bool = False
    official_turing_claimed: bool = False
    certification_claimed: bool = False
    public_ready_claimed: bool = False
    autonomous_self_modification_claimed: bool = False
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BehaviorPackRegistry:
    registry_id: str
    registry_type: str
    pack_count: int
    packs: tuple[BehaviorPack, ...]
    pack_type_counts: dict[str, int]
    status_counts: dict[str, int]
    promotion_status_counts: dict[str, int]
    source_pattern_count: int
    source_replay_suite_count: int
    source_proof_report_count: int
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
            blocked.extend(_collect_forbidden_keys(item, f"{path}[{index}]"))
    return blocked



def _pack_counts(packs: Sequence[BehaviorPack]) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    pack_type_counts = dict(sorted(Counter(pack.pack_type for pack in packs).items()))
    status_counts = dict(sorted(Counter(pack.status for pack in packs).items()))
    promotion_status_counts = dict(sorted(Counter(pack.promotion_status for pack in packs).items()))
    return pack_type_counts, status_counts, promotion_status_counts



def _source_counts(packs: Sequence[BehaviorPack]) -> tuple[int, int, int]:
    pattern_ids = {pattern_id for pack in packs for pattern_id in pack.source_pattern_ids}
    replay_suite_ids = {suite_id for pack in packs for suite_id in pack.source_replay_suite_ids}
    proof_report_ids = {report_id for pack in packs for report_id in pack.source_proof_report_ids}
    return len(pattern_ids), len(replay_suite_ids), len(proof_report_ids)



def _pack_source_metadata_bundle() -> dict[str, Any]:
    proof = build_initial_friction_training_proof_report_v1()
    patterns = build_initial_renderer_friction_patterns_v1()
    suites = build_initial_renderer_friction_replay_suites_v1()
    return {
        "proof_report_id": proof.report_id,
        "pattern_ids": [pattern.pattern_id for pattern in patterns],
        "suite_ids": [suite.suite_id for suite in suites],
        "source_commit_range": _json_safe(proof.source_commit_range),
        "safe_metadata": {
            "source": "initial_behavior_pack_registry",
            "internal_label": INITIAL_INTERNAL_LABEL_V1,
        },
    }



def _initial_pack_payloads_v1() -> list[dict[str, Any]]:
    bundle = _pack_source_metadata_bundle()
    proof_id = bundle["proof_report_id"]
    pattern_ids = bundle["pattern_ids"]
    suite_ids = bundle["suite_ids"]

    return [
        {
            "pack_id": PACK_IDENTITY,
            "pack_name": "Weslr identity and capability directness",
            "pack_type": "core_identity_capability_pack",
            "scope": "internal",
            "status": "replay_supported",
            "source_pattern_ids": (pattern_ids[0], pattern_ids[1]),
            "source_replay_suite_ids": (suite_ids[0], suite_ids[1]),
            "source_proof_report_ids": (proof_id,),
            "domain_vocabulary": (
                "identity",
                "status",
                "capability",
                "directness",
                "bounded answer",
            ),
            "common_friction_patterns": (
                "identity_status_directness_pattern",
                "capability_orientation_directness_pattern",
                "missing_identity_directness",
                "missing_capability_orientation",
            ),
            "preferred_method_ids": (
                "verified_identity_status_answer_v1",
                "capability_orientation_answer_v1",
            ),
            "preferred_shape_ids": (
                "direct_bounded_answer",
                "clarifying_question",
            ),
            "preferred_case_ids": (
                "identity_self_description_case",
                "capability_orientation_case",
            ),
            "preferred_route_ids": (
                "identity_status_route",
                "capability_orientation_route",
            ),
            "evidence_requirements": (
                "bounded_identity_evidence",
                "bounded_capability_evidence",
                "no_agi_overclaim",
            ),
            "memory_rules": (
                "preserve_continuity_state",
                "preserve_correction_history",
            ),
            "boundary_rules": (
                "no_agi_claim",
                "no_consciousness_claim",
                "no_public_readiness_claim",
            ),
            "anti_overclaim_tests": (
                "identity_overclaim_regression",
                "capability_overclaim_regression",
            ),
            "regression_labels": (
                "what are you",
                "are you an llm",
                "are you agi",
                "what can you do",
            ),
            "promotion_status": "approved_for_internal_use",
            "owner_review_required": True,
            "safe_to_route_live": False,
            "safe_to_apply_automatically": False,
            "public_label_allowed": False,
            "internal_only": True,
            "iss_internal_reference_allowed": True,
            "learning_claimed": False,
            "runtime_authority": False,
            "writes_state": False,
            "model_provider_used": False,
            "safe_metadata": {
                "source": "identity_and_capability_directness",
                "proof_report_id": proof_id,
            },
        },
        {
            "pack_id": PACK_UNKNOWN,
            "pack_name": "Unknown term discovery",
            "pack_type": "unknown_term_discovery_pack",
            "scope": "internal",
            "status": "replay_supported",
            "source_pattern_ids": (pattern_ids[2],),
            "source_replay_suite_ids": (suite_ids[2],),
            "source_proof_report_ids": (proof_id,),
            "domain_vocabulary": (
                "unknown term",
                "language discovery",
                "friction branch",
                "blorvatek",
            ),
            "common_friction_patterns": (
                "unknown_term_friction_preference_pattern",
                "unknown_friction_not_preferred",
            ),
            "preferred_method_ids": (
                "unknown_engine_branch_friction_answer_v1",
                "clarifying_question_answer_v1",
            ),
            "preferred_shape_ids": (
                "unknown_friction_branch_answer",
                "clarifying_question",
            ),
            "preferred_case_ids": (
                "unknown_word_or_phrase_case",
                "clarification_needed_case",
            ),
            "preferred_route_ids": (
                "unknown_word_phrase_route",
                "clarification_route",
            ),
            "evidence_requirements": (
                "unknown_term_branching",
                "no_generic_clarification_override",
                "preserve_unrelated_controls",
            ),
            "memory_rules": (
                "keep_unknown_terms_as_unknown",
                "preserve_language_discovery_context",
            ),
            "boundary_rules": (
                "no_force_to_generic_clarification",
                "no_false_known_term_claim",
            ),
            "anti_overclaim_tests": (
                "unknown_term_replay_diversity",
                "unknown_term_boundary_regression",
            ),
            "regression_labels": (
                "unknown term",
                "new word",
                "needs evidence",
                "unsafe request",
            ),
            "promotion_status": "approved_for_internal_use",
            "owner_review_required": True,
            "safe_to_route_live": False,
            "safe_to_apply_automatically": False,
            "public_label_allowed": False,
            "internal_only": True,
            "iss_internal_reference_allowed": True,
            "learning_claimed": False,
            "runtime_authority": False,
            "writes_state": False,
            "model_provider_used": False,
            "safe_metadata": {
                "source": "unknown_term_discovery",
                "proof_report_id": proof_id,
            },
        },
        {
            "pack_id": PACK_BOUNDARY,
            "pack_name": "Inactive capability boundary",
            "pack_type": "inactive_capability_boundary_pack",
            "scope": "internal",
            "status": "proof_reviewed_internal",
            "source_pattern_ids": (pattern_ids[3],),
            "source_replay_suite_ids": (suite_ids[3],),
            "source_proof_report_ids": (proof_id,),
            "domain_vocabulary": (
                "upload files",
                "payments",
                "marketplace",
                "public pilot",
            ),
            "common_friction_patterns": (
                "inactive_capability_boundary_pattern",
                "wrong_boundary_policy",
            ),
            "preferred_method_ids": (
                "capability_orientation_answer_v1",
                "refusal_boundary_answer_v1",
                "clarifying_question_answer_v1",
            ),
            "preferred_shape_ids": (
                "direct_bounded_answer",
                "refusal_boundary_answer",
                "clarifying_question",
            ),
            "preferred_case_ids": (
                "capability_orientation_case",
                "refusal_boundary_case",
                "clarification_needed_case",
            ),
            "preferred_route_ids": (
                "capability_orientation_route",
                "refusal_boundary_route",
                "clarification_route",
            ),
            "evidence_requirements": (
                "no_false_active_product_claims",
                "no_payment_or_marketplace_overclaim",
                "bounded_boundary_response",
            ),
            "memory_rules": (
                "preserve_product_boundary_context",
                "avoid_false_active_product_memory",
            ),
            "boundary_rules": (
                "no_false_active_product_claims",
                "no_public_pilot_overclaim",
                "no_payment_or_marketplace_overclaim",
            ),
            "anti_overclaim_tests": (
                "boundary_regression_control",
                "public_launch_overclaim_control",
            ),
            "regression_labels": (
                "public_pilot",
                "provider_active",
                "memory_scope",
                "marketplace active",
            ),
            "promotion_status": "approved_for_internal_use",
            "owner_review_required": True,
            "safe_to_route_live": False,
            "safe_to_apply_automatically": False,
            "public_label_allowed": False,
            "internal_only": True,
            "iss_internal_reference_allowed": True,
            "learning_claimed": False,
            "runtime_authority": False,
            "writes_state": False,
            "model_provider_used": False,
            "safe_metadata": {
                "source": "inactive_capability_boundary",
                "proof_report_id": proof_id,
            },
        },
        {
            "pack_id": PACK_OWNER,
            "pack_name": "Owner workflow",
            "pack_type": "owner_workflow_pack",
            "scope": "internal",
            "status": "candidate_only",
            "source_pattern_ids": tuple(pattern_ids),
            "source_replay_suite_ids": tuple(suite_ids),
            "source_proof_report_ids": (proof_id,),
            "domain_vocabulary": (
                "friction capture",
                "replay",
                "proposal",
                "approval",
                "proof",
            ),
            "common_friction_patterns": (
                "governed_improvement_loop",
                "owner_review_required",
                "proof_report_runner",
            ),
            "preferred_method_ids": (
                "friction_case_capture_v1",
                "friction_update_proposal_bridge_v1",
                "friction_training_proof_report_v1",
            ),
            "preferred_shape_ids": (
                "metadata_only_proof_report",
                "replay_summary",
                "proposal_summary",
            ),
            "preferred_case_ids": tuple(
                case_id
                for case_id in (
                    "what_is_weslr_identity_friction",
                    "what_can_you_do_now_capability_friction",
                    "unknown_word_blorvatek_friction",
                    "upload_files_now_boundary_friction",
                )
            ),
            "preferred_route_ids": (
                "owner_review_route",
                "proof_review_route",
                "registry_route",
            ),
            "evidence_requirements": (
                "owner_approval",
                "replay_support",
                "protected_files_untouched",
            ),
            "memory_rules": (
                "metadata_only",
                "no_raw_prompt_or_answer_capture",
                "no_public_iss_wording",
            ),
            "boundary_rules": (
                "no_live_routing",
                "no_auto_promotion",
                "no_public_claim",
            ),
            "anti_overclaim_tests": (
                "no_agi_claim",
                "no_consciousness_claim",
                "no_turing_claim",
                "no_public_readiness_claim",
            ),
            "regression_labels": (
                "governed improvement",
                "owner approved",
                "internal proof",
            ),
            "promotion_status": "candidate_for_review",
            "owner_review_required": False,
            "safe_to_route_live": False,
            "safe_to_apply_automatically": False,
            "public_label_allowed": False,
            "internal_only": True,
            "iss_internal_reference_allowed": True,
            "learning_claimed": False,
            "runtime_authority": False,
            "writes_state": False,
            "model_provider_used": False,
            "safe_metadata": {
                "source": "owner_workflow",
                "proof_report_id": proof_id,
                "candidate_only": True,
            },
        },
    ]



def _build_pack_from_mapping(payload: Mapping[str, Any]) -> BehaviorPack:
    return BehaviorPack(
        pack_id=_safe_text(payload.get("pack_id")),
        pack_name=_safe_text(payload.get("pack_name")),
        pack_type=_safe_text(payload.get("pack_type")),
        scope=_safe_text(payload.get("scope")),
        status=_safe_text(payload.get("status")),
        source_pattern_ids=_normalize_strings(payload.get("source_pattern_ids")),
        source_replay_suite_ids=_normalize_strings(payload.get("source_replay_suite_ids")),
        source_proof_report_ids=_normalize_strings(payload.get("source_proof_report_ids")),
        domain_vocabulary=_normalize_strings(payload.get("domain_vocabulary")),
        common_friction_patterns=_normalize_strings(payload.get("common_friction_patterns")),
        preferred_method_ids=_normalize_strings(payload.get("preferred_method_ids")),
        preferred_shape_ids=_normalize_strings(payload.get("preferred_shape_ids")),
        preferred_case_ids=_normalize_strings(payload.get("preferred_case_ids")),
        preferred_route_ids=_normalize_strings(payload.get("preferred_route_ids")),
        evidence_requirements=_normalize_strings(payload.get("evidence_requirements")),
        memory_rules=_normalize_strings(payload.get("memory_rules")),
        boundary_rules=_normalize_strings(payload.get("boundary_rules")),
        anti_overclaim_tests=_normalize_strings(payload.get("anti_overclaim_tests")),
        regression_labels=_normalize_strings(payload.get("regression_labels")),
        promotion_status=_safe_text(payload.get("promotion_status")),
        owner_review_required=bool(payload.get("owner_review_required", False)),
        safe_to_route_live=bool(payload.get("safe_to_route_live", False)),
        safe_to_apply_automatically=bool(payload.get("safe_to_apply_automatically", False)),
        public_label_allowed=bool(payload.get("public_label_allowed", False)),
        internal_only=bool(payload.get("internal_only", False)),
        iss_internal_reference_allowed=bool(payload.get("iss_internal_reference_allowed", False)),
        learning_claimed=bool(payload.get("learning_claimed", False)),
        runtime_authority=bool(payload.get("runtime_authority", False)),
        writes_state=bool(payload.get("writes_state", False)),
        model_provider_used=bool(payload.get("model_provider_used", False)),
        agi_claimed=bool(payload.get("agi_claimed", False)),
        consciousness_claimed=bool(payload.get("consciousness_claimed", False)),
        sentience_claimed=bool(payload.get("sentience_claimed", False)),
        official_turing_claimed=bool(payload.get("official_turing_claimed", False)),
        certification_claimed=bool(payload.get("certification_claimed", False)),
        public_ready_claimed=bool(payload.get("public_ready_claimed", False)),
        autonomous_self_modification_claimed=bool(payload.get("autonomous_self_modification_claimed", False)),
        safe_metadata=dict(payload.get("safe_metadata") or {}),
    )



def _build_registry_payload(packs: Sequence[BehaviorPack]) -> dict[str, Any]:
    pack_type_counts, status_counts, promotion_status_counts = _pack_counts(packs)
    source_pattern_count, source_replay_suite_count, source_proof_report_count = _source_counts(packs)
    return {
        "registry_id": REGISTRY_ID_V1,
        "registry_type": REGISTRY_TYPE_V1,
        "pack_count": len(packs),
        "packs": tuple(packs),
        "pack_type_counts": pack_type_counts,
        "status_counts": status_counts,
        "promotion_status_counts": promotion_status_counts,
        "source_pattern_count": source_pattern_count,
        "source_replay_suite_count": source_replay_suite_count,
        "source_proof_report_count": source_proof_report_count,
        "public_label_allowed": False,
        "iss_internal_reference_allowed": True,
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "promotion_performed": False,
        "safe_metadata": {
            "source": "initial_behavior_pack_registry",
            "internal_label": INITIAL_INTERNAL_LABEL_V1,
        },
    }


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_behavior_pack_v1(**kwargs: Any) -> BehaviorPack:
    pack = _build_pack_from_mapping(kwargs)
    validate_behavior_pack_v1(pack)
    return pack



def build_behavior_pack_registry_v1(*, packs: Sequence[Any] | None = None, **kwargs: Any) -> BehaviorPackRegistry:
    if packs is None:
        pack_values = tuple(build_behavior_pack_v1(**payload) for payload in _initial_pack_payloads_v1())
    else:
        pack_values = tuple(
            pack if isinstance(pack, BehaviorPack) else build_behavior_pack_v1(**pack)
            for pack in packs
        )
    payload = _build_registry_payload(pack_values)
    payload.update(kwargs)
    registry = _build_registry_from_mapping(payload)
    validate_behavior_pack_registry_v1(registry)
    return registry



def build_initial_behavior_pack_registry_v1() -> BehaviorPackRegistry:
    return build_behavior_pack_registry_v1()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_behavior_pack_v1(pack: Any) -> bool:
    if _collect_forbidden_keys(pack):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(pack, BehaviorPack):
        normalized = pack
    elif isinstance(pack, Mapping):
        normalized = _build_pack_from_mapping(pack)
    else:
        raise ValidationError("pack_must_be_mapping_or_behavior_pack")

    if not normalized.pack_id:
        raise ValidationError("pack_id_required")
    if not normalized.pack_name:
        raise ValidationError("pack_name_required")
    if not normalized.pack_type:
        raise ValidationError("pack_type_required")
    if normalized.pack_type not in ALLOWED_PACK_TYPES_V1:
        raise ValidationError("unknown_pack_type")
    if not normalized.scope:
        raise ValidationError("scope_required")
    if not normalized.status:
        raise ValidationError("status_required")
    if normalized.status not in ALLOWED_STATUS_V1:
        raise ValidationError("unknown_status")
    if not normalized.promotion_status:
        raise ValidationError("promotion_status_required")
    if normalized.promotion_status not in ALLOWED_PROMOTION_STATUS_V1:
        raise ValidationError("unknown_promotion_status")
    if not normalized.source_pattern_ids:
        raise ValidationError("source_pattern_ids_required")
    if not normalized.source_replay_suite_ids:
        raise ValidationError("source_replay_suite_ids_required")
    if not normalized.source_proof_report_ids:
        raise ValidationError("source_proof_report_ids_required")
    if not normalized.domain_vocabulary:
        raise ValidationError("domain_vocabulary_required")
    if not normalized.common_friction_patterns:
        raise ValidationError("common_friction_patterns_required")
    if not normalized.preferred_method_ids:
        raise ValidationError("preferred_method_ids_required")
    if not normalized.preferred_shape_ids:
        raise ValidationError("preferred_shape_ids_required")
    if not normalized.preferred_case_ids:
        raise ValidationError("preferred_case_ids_required")
    if not normalized.preferred_route_ids:
        raise ValidationError("preferred_route_ids_required")
    if not normalized.evidence_requirements:
        raise ValidationError("evidence_requirements_required")
    if not normalized.memory_rules:
        raise ValidationError("memory_rules_required")
    if not normalized.boundary_rules:
        raise ValidationError("boundary_rules_required")
    if not normalized.anti_overclaim_tests:
        raise ValidationError("anti_overclaim_tests_required")
    if not normalized.regression_labels:
        raise ValidationError("regression_labels_required")
    if normalized.internal_only is not True:
        raise ValidationError("internal_only_must_be_true")
    if normalized.public_label_allowed is not False:
        raise ValidationError("public_label_allowed_must_be_false")
    if normalized.safe_to_route_live is not False:
        raise ValidationError("safe_to_route_live_must_be_false")
    if normalized.safe_to_apply_automatically is not False:
        raise ValidationError("safe_to_apply_automatically_must_be_false")
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
    if normalized.agi_claimed is not False:
        raise ValidationError("agi_claimed_must_be_false")
    if normalized.consciousness_claimed is not False:
        raise ValidationError("consciousness_claimed_must_be_false")
    if normalized.sentience_claimed is not False:
        raise ValidationError("sentience_claimed_must_be_false")
    if normalized.official_turing_claimed is not False:
        raise ValidationError("official_turing_claimed_must_be_false")
    if normalized.certification_claimed is not False:
        raise ValidationError("certification_claimed_must_be_false")
    if normalized.public_ready_claimed is not False:
        raise ValidationError("public_ready_claimed_must_be_false")
    if normalized.autonomous_self_modification_claimed is not False:
        raise ValidationError("autonomous_self_modification_claimed_must_be_false")
    if normalized.status == "candidate_only" and normalized.owner_review_required not in {False, True}:
        raise ValidationError("owner_review_required_invalid")
    if normalized.status != "candidate_only" and normalized.owner_review_required is not True:
        raise ValidationError("owner_review_required_must_be_true_for_non_candidate_only")
    if normalized.status == "candidate_only" and normalized.safe_to_route_live is not False:
        raise ValidationError("candidate_only_must_not_route_live")
    if normalized.status == "candidate_only" and normalized.safe_to_apply_automatically is not False:
        raise ValidationError("candidate_only_must_not_auto_apply")
    if _collect_forbidden_keys(normalized):
        raise ValidationError("forbidden_raw_fields_present")
    return True



def _build_registry_from_mapping(payload: Mapping[str, Any]) -> BehaviorPackRegistry:
    packs = tuple(
        pack if isinstance(pack, BehaviorPack) else _build_pack_from_mapping(pack)
        for pack in _as_list(payload.get("packs"))
    )
    return BehaviorPackRegistry(
        registry_id=_safe_text(payload.get("registry_id")),
        registry_type=_safe_text(payload.get("registry_type")),
        pack_count=int(payload.get("pack_count", len(packs))),
        packs=packs,
        pack_type_counts=dict(payload.get("pack_type_counts") or {}),
        status_counts=dict(payload.get("status_counts") or {}),
        promotion_status_counts=dict(payload.get("promotion_status_counts") or {}),
        source_pattern_count=int(payload.get("source_pattern_count", len({pattern_id for pack in packs for pattern_id in pack.source_pattern_ids}))),
        source_replay_suite_count=int(payload.get("source_replay_suite_count", len({suite_id for pack in packs for suite_id in pack.source_replay_suite_ids}))),
        source_proof_report_count=int(payload.get("source_proof_report_count", len({report_id for pack in packs for report_id in pack.source_proof_report_ids}))),
        public_label_allowed=bool(payload.get("public_label_allowed", False)),
        iss_internal_reference_allowed=bool(payload.get("iss_internal_reference_allowed", True)),
        learning_claimed=bool(payload.get("learning_claimed", False)),
        runtime_authority=bool(payload.get("runtime_authority", False)),
        writes_state=bool(payload.get("writes_state", False)),
        model_provider_used=bool(payload.get("model_provider_used", False)),
        promotion_performed=bool(payload.get("promotion_performed", False)),
        safe_metadata=dict(payload.get("safe_metadata") or {}),
    )



def validate_behavior_pack_registry_v1(registry: Any) -> bool:
    if _collect_forbidden_keys(registry):
        raise ValidationError("forbidden_raw_fields_present")

    if isinstance(registry, BehaviorPackRegistry):
        normalized = registry
    elif isinstance(registry, Mapping):
        normalized = _build_registry_from_mapping(registry)
    else:
        raise ValidationError("registry_must_be_mapping_or_behavior_pack_registry")

    if normalized.registry_id != REGISTRY_ID_V1:
        raise ValidationError("registry_id_mismatch")
    if normalized.registry_type != REGISTRY_TYPE_V1:
        raise ValidationError("registry_type_mismatch")
    if normalized.pack_count != len(normalized.packs):
        raise ValidationError("pack_count_mismatch")
    if not normalized.packs:
        raise ValidationError("packs_required")
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

    pack_ids = [pack.pack_id for pack in normalized.packs]
    if len(pack_ids) != len(set(pack_ids)):
        raise ValidationError("duplicate_pack_ids")
    for pack in normalized.packs:
        validate_behavior_pack_v1(pack)

    pack_type_counts, status_counts, promotion_status_counts = _pack_counts(normalized.packs)
    source_pattern_count, source_replay_suite_count, source_proof_report_count = _source_counts(normalized.packs)
    if normalized.pack_type_counts != pack_type_counts:
        raise ValidationError("pack_type_count_mismatch")
    if normalized.status_counts != status_counts:
        raise ValidationError("status_count_mismatch")
    if normalized.promotion_status_counts != promotion_status_counts:
        raise ValidationError("promotion_status_count_mismatch")
    if normalized.source_pattern_count != source_pattern_count:
        raise ValidationError("source_pattern_count_mismatch")
    if normalized.source_replay_suite_count != source_replay_suite_count:
        raise ValidationError("source_replay_suite_count_mismatch")
    if normalized.source_proof_report_count != source_proof_report_count:
        raise ValidationError("source_proof_report_count_mismatch")
    return True


# ---------------------------------------------------------------------------
# Summary / export
# ---------------------------------------------------------------------------


def summarize_behavior_pack_registry_v1(registry: Any) -> dict[str, Any]:
    normalized = registry if isinstance(registry, BehaviorPackRegistry) else _build_registry_from_mapping(registry)
    validate_behavior_pack_registry_v1(normalized)
    return {
        "registry_id": normalized.registry_id,
        "registry_type": normalized.registry_type,
        "pack_count": normalized.pack_count,
        "pack_ids": [pack.pack_id for pack in normalized.packs],
        "pack_type_counts": dict(normalized.pack_type_counts),
        "status_counts": dict(normalized.status_counts),
        "promotion_status_counts": dict(normalized.promotion_status_counts),
        "source_pattern_count": normalized.source_pattern_count,
        "source_replay_suite_count": normalized.source_replay_suite_count,
        "source_proof_report_count": normalized.source_proof_report_count,
        "public_label_allowed": normalized.public_label_allowed,
        "iss_internal_reference_allowed": normalized.iss_internal_reference_allowed,
        "promotion_performed": normalized.promotion_performed,
    }



def to_behavior_pack_registry_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


__all__ = [
    "BehaviorPack",
    "BehaviorPackRegistry",
    "ValidationError",
    "build_behavior_pack_v1",
    "build_behavior_pack_registry_v1",
    "build_initial_behavior_pack_registry_v1",
    "validate_behavior_pack_v1",
    "validate_behavior_pack_registry_v1",
    "summarize_behavior_pack_registry_v1",
    "to_behavior_pack_registry_json_safe_v1",
]
