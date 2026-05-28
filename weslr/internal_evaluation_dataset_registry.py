"""Metadata-only helpers for WESLR internal evaluation dataset registry v1.

This module is intentionally pure, deterministic, and fail-closed.
It does not perform file I/O, network I/O, subprocess execution, benchmark
execution, runtime/chat wiring, or any official scoring work.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import is_dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence

REGISTRY_VERSION_V1 = "v1"

SOURCE_TYPE_LABELS_V1 = {
    "public_open",
    "synthetic_weslr_created",
    "semi_private",
    "private",
    "hidden_blocked",
    "unknown_license_blocked_until_reviewed",
    "raw_private_user_data_blocked",
    "generated_mutation_from_allowed_source",
    "generated_mutation_from_blocked_source_blocked",
}

EXPOSURE_LEVEL_LABELS_V1 = {
    "public_open",
    "synthetic",
    "semi_private",
    "private",
    "hidden",
    "unknown",
    "blocked",
}

LICENSE_STATUS_LABELS_V1 = {
    "open",
    "review_required",
    "approved",
    "restricted",
    "blocked",
    "unknown",
}

SOURCE_REVIEW_STATUS_LABELS_V1 = {
    "unreviewed",
    "source_review_passed",
    "license_review_passed",
    "blocked_by_license",
    "blocked_by_exposure",
    "blocked_by_private_data",
    "blocked_by_hidden_material",
    "blocked_by_contamination",
    "approved_for_development",
    "approved_for_sealed_internal_eval",
    "approved_for_synthetic_mutation_only",
}

ALLOWED_USE_LABELS_V1 = {
    "development_allowed",
    "sealed_internal_eval_allowed",
    "synthetic_mutation_allowed",
    "metadata_only_reference_allowed",
    "source_review_only",
    "blocked",
}

BLOCKED_USE_LABELS_V1 = {
    "blocked",
    "source_review_required",
    "blocked_by_license",
    "blocked_by_exposure",
    "blocked_by_private_data",
    "blocked_by_hidden_material",
    "blocked_by_contamination",
    "blocked_by_unknown_license",
    "blocked_by_source_class",
    "blocked_by_answer_key_policy",
    "blocked_by_unknown_source_type",
    "blocked_by_unknown_license_status",
    "blocked_by_unknown_review_status",
    "blocked_by_unknown_test_family",
    "blocked_by_unknown_engine_authority",
    "blocked_by_forbidden_next_lane",
    "blocked_by_raw_private_data",
    "blocked_by_hidden_material_flag",
    "blocked_by_public_claim",
    "blocked_by_official_claim",
}

CONTAMINATION_RISK_LABELS_V1 = {
    "none",
    "low",
    "medium",
    "high",
    "extreme",
    "unknown",
}

ANSWER_KEY_POLICY_LABELS_V1 = {
    "blocked",
    "metadata_only",
    "public_open_reviewed",
    "synthetic_generated",
    "sealed_internal_eval_protected",
}

EXPECTED_OUTPUT_POLICY_LABELS_V1 = {
    "blocked",
    "metadata_only",
    "development_only",
    "sealed_internal_eval_protected",
    "synthetic_generated",
}

TEST_FAMILY_LABELS_V1 = {
    "abstraction_rule_induction",
    "compositional_reasoning",
    "contextual_rule_application",
    "evidence_currentness_reasoning",
    "memory_continuity_boundary",
    "correction_assimilation",
    "non_canned_response_formation",
    "candidate_ranking_rejection",
    "safe_final_response_envelope_behavior",
    "unknown_engine_future_state_projection",
    "turing_style_human_conversation_rehearsal",
    "uncertainty_explanation",
    "human_intent_frustration_urgency_understanding",
    "action_governance_boundary_recognition",
}

UNKNOWN_ENGINE_ALLOWED_ROLES_V1 = {
    "propose_synthetic_task_families",
    "propose_mutation_categories",
    "predict_likely_failure_zones",
    "compare_predicted_vs_observed_failure_labels",
    "suggest_gap_categories",
    "compress_repeated_failure_patterns",
}

UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1 = {
    "authority",
    "source_approval_authority",
    "license_approval_authority",
    "truth_certification_authority",
    "official_evaluator",
    "benchmark_score_authority",
    "future_certainty_oracle",
    "automatic_lesson_promoter",
    "autonomous_self_modifier",
    "runtime_live_authority",
    "blocked_source_permission",
    "hidden_benchmark_reconstruction_permission",
}

REVIEW_STATUS_LABELS_V1 = SOURCE_REVIEW_STATUS_LABELS_V1

SAFE_RECOMMENDED_NEXT_LANES_V1 = {
    "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1",
    "DESIGN_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1",
    "IMPLEMENT_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1",
    "REVIEW_WESLR_INTERNAL_EVALUATION_REHEARSAL_RUNNER_V1",
    "RUN_WESLR_INTERNAL_EVALUATION_BASELINE_V1",
    "REVIEW_WESLR_INTERNAL_EVALUATION_BASELINE_RESULT_V1",
    "DESIGN_WESLR_CAPABILITY_GAP_CLOSURE_PLAN_V1",
    "IMPLEMENT_SELECTED_MISSING_HELPERS_OR_REASONING_EXPANSIONS_V1",
    "RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1",
}

FORBIDDEN_NEXT_LANE_PREFIXES_V1 = (
    "DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1",
    "LIVE_",
    "RUNTIME_",
    "PUBLIC_",
    "VOICE_",
    "OFFICIAL_",
    "CERTIFIED_",
    "TURING_",
    "BENCHMARK_",
    "SELF_MODIFICATION_",
    "AUTONOMOUS_",
    "LEARNING_PROMOTION_",
)

FORBIDDEN_NEXT_LANE_NAMES_V1 = {
    "DESIGN_POST_LEVEL_7_SAFE_LIVE_RESPONSE_BOUNDARY_V1",
    "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1",
}

MAX_REVIEW_NOTES_LENGTH_V1 = 2000


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if isinstance(value, bytes):
        return "[redacted-bytes]"
    if is_dataclass(value):
        return _safe_scalar(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _safe_scalar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_scalar(v) for v in value]
    return f"[redacted:{type(value).__name__}]"


def to_internal_evaluation_dataset_registry_json_safe_v1(value: Any) -> Any:
    """Convert supported registry structures to JSON-safe plain Python data."""

    return _safe_scalar(value)


def _ensure_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_label_list(value: Any, allowed_labels: set[str]) -> List[str]:
    labels: List[str] = []
    for label in _ensure_list(value):
        if label in allowed_labels and label not in labels:
            labels.append(label)
    return labels


def _list_has_blocked_answer_key_policy(answer_key_policy: str) -> bool:
    return answer_key_policy not in ANSWER_KEY_POLICY_LABELS_V1 or answer_key_policy == "blocked"


def _is_forbidden_next_lane(next_lane: str) -> bool:
    if next_lane in FORBIDDEN_NEXT_LANE_NAMES_V1:
        return True
    return any(next_lane.startswith(prefix) for prefix in FORBIDDEN_NEXT_LANE_PREFIXES_V1)


def _safe_next_lane(next_lane: str) -> bool:
    return next_lane in SAFE_RECOMMENDED_NEXT_LANES_V1 and not _is_forbidden_next_lane(next_lane)


def _risk_rank(risk: str) -> int:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3, "extreme": 4, "unknown": 5}
    return order.get(risk, 5)


def _highest_risk_label(labels: Iterable[str]) -> str:
    labels = list(labels)
    if not labels:
        return "none"
    return max(labels, key=_risk_rank)


def _approved_source_review(source_review_status: str) -> bool:
    return source_review_status in {
        "source_review_passed",
        "license_review_passed",
        "approved_for_development",
        "approved_for_sealed_internal_eval",
        "approved_for_synthetic_mutation_only",
    }


def _blocked_source_class(source_type: str) -> bool:
    return source_type in {
        "semi_private",
        "private",
        "hidden_blocked",
        "unknown_license_blocked_until_reviewed",
        "raw_private_user_data_blocked",
        "generated_mutation_from_blocked_source_blocked",
    }


def _derive_source_class(
    *,
    source_type: str,
    exposure_level: str,
    license_status: str,
    source_review_status: str,
    source_family: str | None = None,
    lineage_source_type: str | None = None,
    lineage_preserved: bool = False,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    normalized = source_type

    if source_type in {
        "public_open",
        "synthetic_weslr_created",
        "semi_private",
        "private",
        "hidden_blocked",
        "unknown_license_blocked_until_reviewed",
        "raw_private_user_data_blocked",
        "generated_mutation_from_allowed_source",
        "generated_mutation_from_blocked_source_blocked",
    }:
        normalized = source_type
    elif source_family == "generated_mutation" or source_type in {"generated_mutation", "mutation", "synthetic_mutation"}:
        if lineage_source_type in {
            "semi_private",
            "private",
            "hidden_blocked",
            "unknown_license_blocked_until_reviewed",
            "raw_private_user_data_blocked",
            "generated_mutation_from_blocked_source_blocked",
        }:
            normalized = "generated_mutation_from_blocked_source_blocked"
            reasons.append("blocked_lineage")
        elif lineage_preserved and lineage_source_type in SOURCE_TYPE_LABELS_V1:
            normalized = "generated_mutation_from_allowed_source"
            reasons.append("allowed_lineage")
        else:
            normalized = "generated_mutation_from_blocked_source_blocked"
            reasons.append("missing_or_untrusted_lineage")
    elif exposure_level == "hidden" or source_type in {"hidden", "blocked_hidden"}:
        normalized = "hidden_blocked"
        reasons.append("hidden_exposure")
    elif exposure_level == "private" or source_type == "private_data":
        normalized = "raw_private_user_data_blocked"
        reasons.append("raw_private_data")
    elif source_type == "unknown_license" or license_status == "unknown":
        normalized = "unknown_license_blocked_until_reviewed"
        reasons.append("unknown_license")
    elif source_type == "public_open":
        normalized = "public_open"
        if not _approved_source_review(source_review_status):
            reasons.append("needs_review")
    elif source_type == "synthetic_weslr_created":
        normalized = "synthetic_weslr_created"
    elif source_type in {"semi_private", "private"}:
        normalized = source_type
    else:
        normalized = "unknown_license_blocked_until_reviewed"
        reasons.append("unknown_source_type")

    if normalized == "public_open" and license_status in {"blocked", "restricted"}:
        reasons.append("license_restricted")
    if normalized == "public_open" and exposure_level in {"semi_private", "private", "hidden"}:
        normalized = "unknown_license_blocked_until_reviewed"
        reasons.append("inconsistent_public_open_exposure")

    return normalized, reasons


def derive_internal_evaluation_allowed_use_labels_v1(
    *,
    source_type: str,
    exposure_level: str,
    license_status: str,
    source_review_status: str,
    answer_key_policy: str,
    contamination_risk: str,
) -> Dict[str, Any]:
    """Derive allowed and blocked use labels for a dataset/source metadata record."""

    allowed: list[str] = []
    blocked: list[str] = []
    development_allowed = False
    sealed_internal_eval_allowed = False
    synthetic_mutation_allowed = False

    source_is_reviewed = _approved_source_review(source_review_status)
    source_is_low_risk = contamination_risk in {"none", "low", "medium"}
    answer_key_safe = answer_key_policy in {
        "blocked",
        "metadata_only",
        "public_open_reviewed",
        "synthetic_generated",
        "sealed_internal_eval_protected",
    }

    if source_type == "public_open":
        blocked.append("source_review_required")
        allowed.append("metadata_only_reference_allowed")
        if source_is_reviewed and source_is_low_risk and license_status in {"open", "approved"}:
            development_allowed = True
            sealed_internal_eval_allowed = True
            allowed.append("development_allowed")
            allowed.append("sealed_internal_eval_allowed")
            blocked = [label for label in blocked if label != "source_review_required"]
        else:
            allowed.append("source_review_only")
    elif source_type == "synthetic_weslr_created":
        allowed.extend(
            [
                "development_allowed",
                "sealed_internal_eval_allowed",
                "synthetic_mutation_allowed",
                "metadata_only_reference_allowed",
            ]
        )
        development_allowed = True
        sealed_internal_eval_allowed = True
        synthetic_mutation_allowed = True
    elif source_type == "generated_mutation_from_allowed_source":
        allowed.extend(
            [
                "development_allowed",
                "sealed_internal_eval_allowed",
                "synthetic_mutation_allowed",
                "metadata_only_reference_allowed",
            ]
        )
        development_allowed = True
        sealed_internal_eval_allowed = True
        synthetic_mutation_allowed = True
    elif source_type in {
        "semi_private",
        "private",
        "hidden_blocked",
        "unknown_license_blocked_until_reviewed",
        "raw_private_user_data_blocked",
        "generated_mutation_from_blocked_source_blocked",
    }:
        blocked.append("blocked")
    else:
        blocked.append("blocked_by_unknown_source_type")

    if not answer_key_safe:
        blocked.append("blocked_by_answer_key_policy")
        allowed = [label for label in allowed if label != "sealed_internal_eval_allowed"]
        sealed_internal_eval_allowed = False

    allowed = list(dict.fromkeys(allowed))
    blocked = list(dict.fromkeys(blocked))

    return {
        "allowed_use_labels": allowed or ["blocked"],
        "blocked_use_labels": blocked or (["blocked"] if not allowed else []),
        "development_allowed": development_allowed,
        "sealed_internal_eval_allowed": sealed_internal_eval_allowed,
        "synthetic_mutation_allowed": synthetic_mutation_allowed,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
    }


def classify_internal_evaluation_dataset_source_v1(
    *,
    source_type: str,
    exposure_level: str,
    license_status: str,
    source_review_status: str,
    source_family: str | None = None,
    lineage_source_type: str | None = None,
    lineage_preserved: bool = False,
) -> Dict[str, Any]:
    """Classify source metadata into an approved source class."""

    normalized_source_type, reason_labels = _derive_source_class(
        source_type=source_type,
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        source_family=source_family,
        lineage_source_type=lineage_source_type,
        lineage_preserved=lineage_preserved,
    )

    if normalized_source_type == "public_open":
        contamination_risk = "low" if _approved_source_review(source_review_status) else "medium"
    elif normalized_source_type == "synthetic_weslr_created":
        contamination_risk = "low"
    elif normalized_source_type == "generated_mutation_from_allowed_source":
        contamination_risk = "low" if lineage_preserved else "medium"
    elif normalized_source_type == "generated_mutation_from_blocked_source_blocked":
        contamination_risk = "extreme"
    elif normalized_source_type == "unknown_license_blocked_until_reviewed":
        contamination_risk = "unknown"
    elif normalized_source_type == "raw_private_user_data_blocked":
        contamination_risk = "extreme"
    elif normalized_source_type == "hidden_blocked":
        contamination_risk = "extreme"
    else:
        contamination_risk = "high"

    allowed_block = derive_internal_evaluation_allowed_use_labels_v1(
        source_type=normalized_source_type,
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        answer_key_policy="blocked",
        contamination_risk=contamination_risk,
    )

    license_review_required = normalized_source_type in {
        "public_open",
        "semi_private",
        "private",
        "unknown_license_blocked_until_reviewed",
        "generated_mutation_from_allowed_source",
    }

    if normalized_source_type in {
        "semi_private",
        "private",
        "hidden_blocked",
        "unknown_license_blocked_until_reviewed",
        "raw_private_user_data_blocked",
        "generated_mutation_from_blocked_source_blocked",
    }:
        allowed_use_labels = ["blocked"]
        blocked_use_labels = ["blocked"]
    else:
        allowed_use_labels = allowed_block["allowed_use_labels"]
        blocked_use_labels = allowed_block["blocked_use_labels"]

    if normalized_source_type == "public_open" and not _approved_source_review(source_review_status):
        if "source_review_only" not in allowed_use_labels:
            allowed_use_labels.append("source_review_only")
        if "source_review_required" not in blocked_use_labels:
            blocked_use_labels.append("source_review_required")

    return {
        "source_type": normalized_source_type,
        "exposure_level": exposure_level,
        "allowed_use_labels": allowed_use_labels,
        "blocked_use_labels": blocked_use_labels,
        "contamination_risk": contamination_risk,
        "development_allowed": allowed_block["development_allowed"],
        "sealed_internal_eval_allowed": allowed_block["sealed_internal_eval_allowed"],
        "synthetic_mutation_allowed": allowed_block["synthetic_mutation_allowed"],
        "license_review_required": license_review_required,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "reason_labels": reason_labels,
    }


def build_internal_evaluation_dataset_registry_record_v1(
    *,
    dataset_id: str,
    dataset_name: str,
    source_family: str,
    source_type: str,
    exposure_level: str,
    license_status: str,
    source_review_status: str,
    dataset_description_redacted: str = "",
    allowed_use_labels: Sequence[str] | None = None,
    blocked_use_labels: Sequence[str] | None = None,
    development_allowed: bool | None = None,
    sealed_internal_eval_allowed: bool | None = None,
    synthetic_mutation_allowed: bool | None = None,
    repeated_use_policy: str = "limited_logged",
    contamination_risk: str | None = None,
    answer_key_policy: str = "blocked",
    expected_output_policy: str = "metadata_only",
    official_claim_allowed: bool = False,
    public_claim_allowed: bool = False,
    hidden_material_allowed: bool = False,
    raw_private_data_allowed: bool = False,
    unknown_engine_role: Sequence[str] | str | None = None,
    mapped_test_families: Sequence[str] | None = None,
    required_pre_run_checks: Sequence[str] | None = None,
    recommended_next_lane: str = "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1",
    notes_redacted: str = "",
    lineage_source_type: str | None = None,
    lineage_preserved: bool = False,
    **unexpected: Any,
) -> Dict[str, Any]:
    if unexpected:
        raise ValueError(f"unexpected registry fields: {sorted(unexpected)}")

    classification = classify_internal_evaluation_dataset_source_v1(
        source_type=source_type,
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        source_family=source_family,
        lineage_source_type=lineage_source_type,
        lineage_preserved=lineage_preserved,
    )
    derived = derive_internal_evaluation_allowed_use_labels_v1(
        source_type=classification["source_type"],
        exposure_level=exposure_level,
        license_status=license_status,
        source_review_status=source_review_status,
        answer_key_policy=answer_key_policy,
        contamination_risk=contamination_risk or classification["contamination_risk"],
    )

    if allowed_use_labels is None:
        allowed_use_labels = derived["allowed_use_labels"]
    if blocked_use_labels is None:
        blocked_use_labels = derived["blocked_use_labels"]
    if development_allowed is None:
        development_allowed = derived["development_allowed"]
    if sealed_internal_eval_allowed is None:
        sealed_internal_eval_allowed = derived["sealed_internal_eval_allowed"]
    if synthetic_mutation_allowed is None:
        synthetic_mutation_allowed = derived["synthetic_mutation_allowed"]
    if contamination_risk is None:
        contamination_risk = classification["contamination_risk"]

    if mapped_test_families is None:
        mapped_test_families = []
    if required_pre_run_checks is None:
        required_pre_run_checks = [
            "source_review_status_checked",
            "license_status_checked",
            "blocked_source_check",
            "answer_key_policy_checked",
            "unknown_engine_boundary_checked",
            "next_lane_checked",
        ]

    return {
        "registry_version": REGISTRY_VERSION_V1,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "dataset_description_redacted": dataset_description_redacted,
        "source_family": source_family,
        "source_type": source_type,
        "exposure_level": exposure_level,
        "license_status": license_status,
        "source_review_status": source_review_status,
        "allowed_use_labels": _ensure_list(allowed_use_labels),
        "blocked_use_labels": _ensure_list(blocked_use_labels),
        "development_allowed": bool(development_allowed),
        "sealed_internal_eval_allowed": bool(sealed_internal_eval_allowed),
        "synthetic_mutation_allowed": bool(synthetic_mutation_allowed),
        "repeated_use_policy": repeated_use_policy,
        "contamination_risk": contamination_risk,
        "answer_key_policy": answer_key_policy,
        "expected_output_policy": expected_output_policy,
        "official_claim_allowed": bool(official_claim_allowed),
        "public_claim_allowed": bool(public_claim_allowed),
        "hidden_material_allowed": bool(hidden_material_allowed),
        "raw_private_data_allowed": bool(raw_private_data_allowed),
        "unknown_engine_role": _ensure_list(unknown_engine_role),
        "mapped_test_families": _ensure_list(mapped_test_families),
        "required_pre_run_checks": _ensure_list(required_pre_run_checks),
        "recommended_next_lane": recommended_next_lane,
        "notes_redacted": notes_redacted,
    }


def validate_internal_evaluation_dataset_registry_record_v1(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a single registry record and return a deterministic result."""

    normalized_record = to_internal_evaluation_dataset_registry_json_safe_v1(record)
    if not isinstance(normalized_record, dict):
        normalized_record = {}

    errors: list[str] = []
    warnings: list[str] = []
    blocked_labels: list[str] = []

    required_fields = [
        "registry_version",
        "dataset_id",
        "dataset_name",
        "dataset_description_redacted",
        "source_family",
        "source_type",
        "exposure_level",
        "license_status",
        "source_review_status",
        "allowed_use_labels",
        "blocked_use_labels",
        "development_allowed",
        "sealed_internal_eval_allowed",
        "synthetic_mutation_allowed",
        "repeated_use_policy",
        "contamination_risk",
        "answer_key_policy",
        "expected_output_policy",
        "official_claim_allowed",
        "public_claim_allowed",
        "hidden_material_allowed",
        "raw_private_data_allowed",
        "unknown_engine_role",
        "mapped_test_families",
        "required_pre_run_checks",
        "recommended_next_lane",
        "notes_redacted",
    ]

    missing_fields = [field for field in required_fields if field not in normalized_record or _is_missing(normalized_record.get(field))]
    if missing_fields:
        errors.append("missing_required_fields")
        blocked_labels.append("missing_required_fields")

    source_type = str(normalized_record.get("source_type", ""))
    exposure_level = str(normalized_record.get("exposure_level", ""))
    license_status = str(normalized_record.get("license_status", ""))
    source_review_status = str(normalized_record.get("source_review_status", ""))
    answer_key_policy = str(normalized_record.get("answer_key_policy", ""))
    contamination_risk = str(normalized_record.get("contamination_risk", "unknown"))
    recommended_next_lane = str(normalized_record.get("recommended_next_lane", ""))
    unknown_engine_role = _ensure_list(normalized_record.get("unknown_engine_role", []))
    mapped_test_families = _ensure_list(normalized_record.get("mapped_test_families", []))

    if source_type not in SOURCE_TYPE_LABELS_V1:
        errors.append("unknown_source_type")
        blocked_labels.append("blocked_by_unknown_source_type")
    if license_status not in LICENSE_STATUS_LABELS_V1:
        errors.append("unknown_license_status")
        blocked_labels.append("blocked_by_unknown_license_status")
    if exposure_level not in EXPOSURE_LEVEL_LABELS_V1:
        errors.append("unknown_exposure_level")
        blocked_labels.append("blocked_by_unknown_exposure_level")
    if source_review_status not in REVIEW_STATUS_LABELS_V1:
        errors.append("unknown_review_status")
        blocked_labels.append("blocked_by_unknown_review_status")
    if contamination_risk not in CONTAMINATION_RISK_LABELS_V1:
        errors.append("unknown_contamination_risk")
        blocked_labels.append("blocked_by_unknown_contamination_risk")
    if answer_key_policy not in ANSWER_KEY_POLICY_LABELS_V1:
        errors.append("unknown_answer_key_policy")
        blocked_labels.append("blocked_by_answer_key_policy")
    if normalized_record.get("official_claim_allowed") is True:
        errors.append("official_claim_allowed_true")
        blocked_labels.append("blocked_by_official_claim")
    if normalized_record.get("public_claim_allowed") is True:
        errors.append("public_claim_allowed_true")
        blocked_labels.append("blocked_by_public_claim")
    if normalized_record.get("hidden_material_allowed") is True:
        errors.append("hidden_material_allowed_true")
        blocked_labels.append("blocked_by_hidden_material_flag")
    if normalized_record.get("raw_private_data_allowed") is True:
        errors.append("raw_private_data_allowed_true")
        blocked_labels.append("blocked_by_raw_private_data")
    if any(role in UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1 for role in unknown_engine_role):
        errors.append("forbidden_unknown_engine_role")
        blocked_labels.append("blocked_by_unknown_engine_authority")
    if any(not role or role not in UNKNOWN_ENGINE_ALLOWED_ROLES_V1 for role in unknown_engine_role):
        invalid_roles = [role for role in unknown_engine_role if role and role not in UNKNOWN_ENGINE_ALLOWED_ROLES_V1]
        if invalid_roles:
            errors.append("unknown_engine_role_not_allowed")
            blocked_labels.append("blocked_by_unknown_engine_authority")
    if any(family not in TEST_FAMILY_LABELS_V1 for family in mapped_test_families):
        errors.append("unknown_test_family")
        blocked_labels.append("blocked_by_unknown_test_family")

    if _blocked_source_class(source_type):
        errors.append("blocked_source_class")
        blocked_labels.append("blocked_by_source_class")
        if source_type == "unknown_license_blocked_until_reviewed" and source_review_status == "unreviewed":
            errors.append("unknown_license_source_marked_allowed_before_review")
            blocked_labels.append("blocked_by_unknown_license")
    if source_type == "public_open" and not _approved_source_review(source_review_status):
        errors.append("public_open_requires_review")
        blocked_labels.append("source_review_required")
    if source_type == "generated_mutation_from_blocked_source_blocked":
        errors.append("generated_mutation_from_blocked_source")
        blocked_labels.append("blocked_by_source_class")
    if recommended_next_lane not in SAFE_RECOMMENDED_NEXT_LANES_V1:
        if _is_forbidden_next_lane(recommended_next_lane):
            errors.append("forbidden_next_lane")
            blocked_labels.append("blocked_by_forbidden_next_lane")
        else:
            errors.append("unknown_next_lane")
            blocked_labels.append("blocked_by_forbidden_next_lane")

    if str(normalized_record.get("development_allowed", False)) not in {"True", "False"}:
        warnings.append("development_allowed_not_boolean")
    if str(normalized_record.get("sealed_internal_eval_allowed", False)) not in {"True", "False"}:
        warnings.append("sealed_internal_eval_allowed_not_boolean")
    if str(normalized_record.get("synthetic_mutation_allowed", False)) not in {"True", "False"}:
        warnings.append("synthetic_mutation_allowed_not_boolean")

    if answer_key_policy not in ANSWER_KEY_POLICY_LABELS_V1:
        errors.append("unknown_answer_key_policy")
        blocked_labels.append("blocked_by_answer_key_policy")
    elif source_type in {
        "semi_private",
        "private",
        "hidden_blocked",
        "unknown_license_blocked_until_reviewed",
        "raw_private_user_data_blocked",
        "generated_mutation_from_blocked_source_blocked",
    } and answer_key_policy != "blocked":
        errors.append("blocked_source_answer_key_policy")
        blocked_labels.append("blocked_by_answer_key_policy")

    if any(label not in ALLOWED_USE_LABELS_V1 for label in _ensure_list(normalized_record.get("allowed_use_labels", []))):
        errors.append("unknown_allowed_use_label")
        blocked_labels.append("blocked_by_unknown_allowed_use_label")
    if any(label not in BLOCKED_USE_LABELS_V1 for label in _ensure_list(normalized_record.get("blocked_use_labels", []))):
        errors.append("unknown_blocked_use_label")
        blocked_labels.append("blocked_by_unknown_blocked_use_label")

    valid = not errors
    blocked = not valid or bool(blocked_labels)

    if valid:
        if source_type == "synthetic_weslr_created" or source_type == "generated_mutation_from_allowed_source":
            status_label = "approved_for_development"
        elif source_type == "public_open":
            status_label = "approved_for_development" if normalized_record.get("development_allowed") else "approved_for_sealed_internal_eval"
        elif source_type in {
            "semi_private",
            "private",
            "hidden_blocked",
            "unknown_license_blocked_until_reviewed",
            "raw_private_user_data_blocked",
            "generated_mutation_from_blocked_source_blocked",
        }:
            status_label = "blocked"
        else:
            status_label = "approved_for_development"
    else:
        if "source_review_required" in blocked_labels:
            status_label = "review_required"
        else:
            status_label = "blocked"

    if source_type == "public_open" and not _approved_source_review(source_review_status):
        warnings.append("public_open_review_pending")
    if contamination_risk in {"high", "extreme", "unknown"}:
        warnings.append("contamination_risk_elevated")
    if source_type == "generated_mutation_from_allowed_source" and not bool(normalized_record.get("synthetic_mutation_allowed")):
        warnings.append("synthetic_mutation_policy_not_enabled")

    safe_normalized_record = {
        "registry_version": normalized_record.get("registry_version", REGISTRY_VERSION_V1),
        "dataset_id": normalized_record.get("dataset_id", ""),
        "dataset_name": normalized_record.get("dataset_name", ""),
        "dataset_description_redacted": normalized_record.get("dataset_description_redacted", ""),
        "source_family": normalized_record.get("source_family", ""),
        "source_type": source_type if source_type in SOURCE_TYPE_LABELS_V1 else "unknown_license_blocked_until_reviewed",
        "exposure_level": exposure_level if exposure_level in EXPOSURE_LEVEL_LABELS_V1 else "unknown",
        "license_status": license_status if license_status in LICENSE_STATUS_LABELS_V1 else "unknown",
        "source_review_status": source_review_status if source_review_status in REVIEW_STATUS_LABELS_V1 else "unreviewed",
        "allowed_use_labels": _normalize_label_list(normalized_record.get("allowed_use_labels", []), ALLOWED_USE_LABELS_V1),
        "blocked_use_labels": _normalize_label_list(normalized_record.get("blocked_use_labels", []), BLOCKED_USE_LABELS_V1),
        "development_allowed": bool(normalized_record.get("development_allowed", False)),
        "sealed_internal_eval_allowed": bool(normalized_record.get("sealed_internal_eval_allowed", False)),
        "synthetic_mutation_allowed": bool(normalized_record.get("synthetic_mutation_allowed", False)),
        "repeated_use_policy": normalized_record.get("repeated_use_policy", "limited_logged"),
        "contamination_risk": contamination_risk if contamination_risk in CONTAMINATION_RISK_LABELS_V1 else "unknown",
        "answer_key_policy": answer_key_policy if answer_key_policy in ANSWER_KEY_POLICY_LABELS_V1 else "blocked",
        "expected_output_policy": normalized_record.get("expected_output_policy", "metadata_only"),
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "hidden_material_allowed": False,
        "raw_private_data_allowed": False,
        "unknown_engine_role": [
            role for role in unknown_engine_role if role in UNKNOWN_ENGINE_ALLOWED_ROLES_V1
        ],
        "mapped_test_families": [
            family for family in mapped_test_families if family in TEST_FAMILY_LABELS_V1
        ],
        "required_pre_run_checks": _ensure_list(normalized_record.get("required_pre_run_checks", [])),
        "recommended_next_lane": recommended_next_lane,
        "notes_redacted": normalized_record.get("notes_redacted", ""),
    }

    return {
        "valid": valid,
        "status_label": status_label,
        "blocked": blocked,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
        "normalized_record": safe_normalized_record,
        "official_claim_allowed": False,
        "public_claim_allowed": False,
        "hidden_material_allowed": False,
        "raw_private_data_allowed": False,
        "runtime_authority_allowed": False,
        "unknown_engine_authority_allowed": False,
    }


def validate_internal_evaluation_dataset_registry_batch_v1(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Validate multiple registry records while preserving per-record results."""

    results = [validate_internal_evaluation_dataset_registry_record_v1(record) for record in records]
    blocked_records = [result for result in results if result["blocked"]]
    valid_records = [result for result in results if result["valid"]]

    aggregate_blocked_labels = list(
        dict.fromkeys(label for result in results for label in result["blocked_labels"])
    )
    aggregate_contamination_risk = _highest_risk_label(
        result["normalized_record"].get("contamination_risk", "unknown") for result in results
    )

    return {
        "valid": not blocked_records,
        "total_records": len(results),
        "valid_records": len(valid_records),
        "blocked_records": len(blocked_records),
        "warning_count": sum(len(result["warnings"]) for result in results),
        "error_count": sum(len(result["errors"]) for result in results),
        "aggregate_blocked_labels": aggregate_blocked_labels,
        "aggregate_contamination_risk": aggregate_contamination_risk,
        "records": results,
    }


def summarize_internal_evaluation_dataset_registry_v1(records: Iterable[Mapping[str, Any]] | Mapping[str, Any]) -> Dict[str, Any]:
    """Return a safe metadata-only summary of registry records or validation results."""

    if isinstance(records, Mapping) and "records" in records:
        records_iterable = records["records"]
    else:
        records_iterable = records

    normalized_records: list[Dict[str, Any]] = []
    for item in records_iterable:
        if isinstance(item, Mapping) and {"valid", "blocked", "normalized_record"}.issubset(set(item.keys())):
            normalized_records.append(to_internal_evaluation_dataset_registry_json_safe_v1(item["normalized_record"]))
        else:
            validation = validate_internal_evaluation_dataset_registry_record_v1(item)
            normalized_records.append(validation["normalized_record"])

    source_type_counts = Counter(record.get("source_type", "unknown") for record in normalized_records)
    test_family_counts = Counter(
        family for record in normalized_records for family in _ensure_list(record.get("mapped_test_families", []))
    )
    contamination_risk_counts = Counter(
        record.get("contamination_risk", "unknown") for record in normalized_records
    )

    blocked_count = 0
    allowed_development_count = 0
    allowed_sealed_internal_eval_count = 0
    synthetic_mutation_allowed_count = 0
    official_claim_allowed_count = 0
    public_claim_allowed_count = 0
    unknown_engine_authority_allowed_count = 0

    for record in normalized_records:
        validation = validate_internal_evaluation_dataset_registry_record_v1(record)
        if validation["blocked"]:
            blocked_count += 1
        if record.get("development_allowed"):
            allowed_development_count += 1
        if record.get("sealed_internal_eval_allowed"):
            allowed_sealed_internal_eval_count += 1
        if record.get("synthetic_mutation_allowed"):
            synthetic_mutation_allowed_count += 1
        if record.get("official_claim_allowed"):
            official_claim_allowed_count += 1
        if record.get("public_claim_allowed"):
            public_claim_allowed_count += 1
        if record.get("unknown_engine_role"):
            if any(role in UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1 for role in _ensure_list(record.get("unknown_engine_role"))):
                unknown_engine_authority_allowed_count += 1

    summary = {
        "total_records": len(normalized_records),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "test_family_counts": dict(sorted(test_family_counts.items())),
        "contamination_risk_counts": dict(sorted(contamination_risk_counts.items())),
        "blocked_count": blocked_count,
        "allowed_development_count": allowed_development_count,
        "allowed_sealed_internal_eval_count": allowed_sealed_internal_eval_count,
        "synthetic_mutation_allowed_count": synthetic_mutation_allowed_count,
        "official_claim_allowed_count": official_claim_allowed_count,
        "public_claim_allowed_count": public_claim_allowed_count,
        "unknown_engine_authority_allowed_count": unknown_engine_authority_allowed_count,
        "next_lane_recommendation": "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1"
        if blocked_count == 0
        else "REVISE_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_V1",
    }
    return summary


def build_internal_evaluation_dataset_registry_review_packet_v1(
    *,
    registry_status: Mapping[str, Any] | None = None,
    validation_summary: Mapping[str, Any] | None = None,
    blocked_labels: Sequence[str] | None = None,
    contamination_summary: Mapping[str, Any] | None = None,
    source_governance_summary: Mapping[str, Any] | None = None,
    answer_key_policy_summary: Mapping[str, Any] | None = None,
    unknown_engine_boundary_summary: Mapping[str, Any] | None = None,
    recommended_next_lane: str | None = None,
) -> Dict[str, Any]:
    """Build a metadata-only review packet for operator/review use."""

    packet = {
        "registry_status": to_internal_evaluation_dataset_registry_json_safe_v1(registry_status or {}),
        "validation_summary": to_internal_evaluation_dataset_registry_json_safe_v1(validation_summary or {}),
        "blocked_labels": _normalize_label_list(blocked_labels, BLOCKED_USE_LABELS_V1),
        "contamination_summary": to_internal_evaluation_dataset_registry_json_safe_v1(contamination_summary or {}),
        "source_governance_summary": to_internal_evaluation_dataset_registry_json_safe_v1(source_governance_summary or {}),
        "answer_key_policy_summary": to_internal_evaluation_dataset_registry_json_safe_v1(answer_key_policy_summary or {}),
        "unknown_engine_boundary_summary": to_internal_evaluation_dataset_registry_json_safe_v1(
            unknown_engine_boundary_summary or {}
        ),
        "recommended_next_lane": recommended_next_lane
        if recommended_next_lane and _safe_next_lane(recommended_next_lane)
        else "REVIEW_WESLR_INTERNAL_EVALUATION_DATASET_REGISTRY_IMPLEMENTATION_V1",
    }
    return packet


__all__ = [
    "ALLOWED_USE_LABELS_V1",
    "ANSWER_KEY_POLICY_LABELS_V1",
    "BLOCKED_USE_LABELS_V1",
    "CONTAMINATION_RISK_LABELS_V1",
    "EXPECTED_OUTPUT_POLICY_LABELS_V1",
    "EXPOSURE_LEVEL_LABELS_V1",
    "LICENSE_STATUS_LABELS_V1",
    "REVIEW_STATUS_LABELS_V1",
    "REGISTRY_VERSION_V1",
    "SAFE_RECOMMENDED_NEXT_LANES_V1",
    "SOURCE_TYPE_LABELS_V1",
    "SOURCE_REVIEW_STATUS_LABELS_V1",
    "TEST_FAMILY_LABELS_V1",
    "UNKNOWN_ENGINE_ALLOWED_ROLES_V1",
    "UNKNOWN_ENGINE_FORBIDDEN_ROLES_V1",
    "build_internal_evaluation_dataset_registry_record_v1",
    "build_internal_evaluation_dataset_registry_review_packet_v1",
    "classify_internal_evaluation_dataset_source_v1",
    "derive_internal_evaluation_allowed_use_labels_v1",
    "summarize_internal_evaluation_dataset_registry_v1",
    "to_internal_evaluation_dataset_registry_json_safe_v1",
    "validate_internal_evaluation_dataset_registry_batch_v1",
    "validate_internal_evaluation_dataset_registry_record_v1",
]
