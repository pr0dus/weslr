"""ARC official public-data approval manifest gate.

Deterministic, metadata-only, and fail-closed.
This gate validates that a future official public-data run has an owner-approved
manifest with the required provenance, offline, and no-contamination controls.

It does not load official ARC data, inspect source files, open bundles, call
web/tools/models/providers, or touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr.arc_official_contamination_boundary import (
    classify_data_class,
    classify_run_phase,
    summarize_boundary_status,
    validate_contamination_boundary_record,
)

SCHEMA_VERSION_V1 = "arc_official_public_data_approval_gate_v1"

ALLOWED_APPROVED_PHASES_V1 = (
    "phase_2_public_parse_scorer_validation",
    "phase_3_local_public_run",
    "phase_4_post_run_contamination_audit",
    "phase_5_competition_participation_design",
)

ALLOWED_OFFICIAL_DATA_CLASSES_V1 = (
    "public_official_arc",
)

_FORBIDDEN_SOURCE_TYPES_V1 = {
    "network",
    "browser_fetched",
    "web_fetched",
    "remote",
    "mutable_bundle",
    "synthetic_weslr",
    "hidden_private_arc",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _as_bool(value: Any) -> bool:
    return value is True


def _contains_forbidden_marker(value: Any) -> list[str]:
    issues: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            if key_text in {"expected_output", "hidden_answer", "latent_rule", "official_score", "competition_submission_authority"}:
                issues.append(key_text)
            issues.extend(_contains_forbidden_marker(nested))
    elif isinstance(value, list):
        for nested in value:
            issues.extend(_contains_forbidden_marker(nested))
    elif isinstance(value, tuple):
        for nested in value:
            issues.extend(_contains_forbidden_marker(nested))
    return issues


def validate_approval_manifest(manifest: Any) -> dict[str, Any]:
    data = _as_mapping(manifest)
    if not data:
        raise ValueError("Invalid approval manifest")

    owner_approved = _as_bool(data.get("owner_approved"))
    approval_reference = _text(data.get("approval_reference"))
    approved_phase = _text(data.get("approved_phase"))
    source_type = _text(data.get("source_type"))
    source_location = _text(data.get("source_location"))
    source_version_or_snapshot = _text(data.get("source_version_or_snapshot"))
    checksum = _text(data.get("checksum"))
    read_only_required = _as_bool(data.get("read_only_required"))
    approved_scope = _as_mapping(data.get("approved_scope"))
    official_data_class = _text(data.get("official_data_class"))
    claim_policy = _as_mapping(data.get("claim_policy"))
    offline_required = _as_bool(data.get("offline_required"))
    no_hidden_private_data = _as_bool(data.get("no_hidden_private_data"))
    no_network_fetch = _as_bool(data.get("no_network_fetch"))
    no_mutation_in_place = _as_bool(data.get("no_mutation_in_place"))

    issues: list[str] = []
    if not owner_approved:
        issues.append("owner_not_approved")
    if not approval_reference:
        issues.append("missing_approval_reference")
    if not source_location:
        issues.append("missing_source_location")
    if not source_version_or_snapshot:
        issues.append("missing_source_version_or_snapshot")
    if not checksum:
        issues.append("missing_checksum")
    if not read_only_required:
        issues.append("missing_read_only_requirement")
    if not offline_required:
        issues.append("missing_offline_requirement")
    if not no_network_fetch:
        issues.append("missing_no_network_fetch")
    if not no_mutation_in_place:
        issues.append("missing_no_mutation_in_place")
    if not no_hidden_private_data:
        issues.append("missing_no_hidden_private_data")
    if approved_phase not in ALLOWED_APPROVED_PHASES_V1:
        issues.append("unsupported_approved_phase")
    if source_type in _FORBIDDEN_SOURCE_TYPES_V1:
        issues.append("forbidden_source_type")
    if official_data_class not in ALLOWED_OFFICIAL_DATA_CLASSES_V1:
        issues.append("unsupported_official_data_class")
    if source_type in {"network", "browser_fetched", "web_fetched"}:
        issues.append("network_or_browser_fetched_source")
    if not isinstance(approved_scope, Mapping) or not approved_scope:
        issues.append("missing_approved_scope")

    claim_policy_issues = _validate_claim_policy(claim_policy, approved_phase)
    issues.extend(claim_policy_issues)

    boundary_record = {
        "data_class": official_data_class or "public_official_arc",
        "run_phase": approved_phase or "phase_0_synthetic_only",
        "official_data_touched": official_data_class == "public_official_arc",
        "hidden_private_data_touched": official_data_class == "hidden_private_arc",
        "internet_tool_model_calls_during_solving": False,
        "expected_output_leakage": False,
        "internal_task_language_leakage": False,
        "synthetic_official_score_mixing": bool(claim_policy.get("mix_synthetic_and_official_scores")),
        "dataset_provenance": {
            "source": source_type,
            "version": source_version_or_snapshot,
            "checksum": checksum,
        },
    }
    boundary_result = validate_contamination_boundary_record(boundary_record)
    if classify_data_class(boundary_result) != "public_official_arc":
        issues.append("contamination_boundary_classification_mismatch")
    if classify_run_phase(boundary_result) not in ALLOWED_APPROVED_PHASES_V1:
        issues.append("contamination_boundary_phase_mismatch")

    if issues:
        raise ValueError(f"Invalid approval manifest: {sorted(set(issues))}")

    summary = summarize_boundary_status({
        "official_run_proof": False,
        "local_public_run_proof": False,
        "official_percentage": 0,
        "official_data_touched": True,
        "hidden_private_data_touched": False,
        "synthetic_official_score_mixing": False,
        "data_class": official_data_class,
        "run_phase": approved_phase,
    })
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "owner_approved": True,
        "approval_reference": approval_reference,
        "approved_phase": approved_phase,
        "source_type": source_type,
        "source_location": source_location,
        "source_version_or_snapshot": source_version_or_snapshot,
        "checksum": checksum,
        "read_only_required": True,
        "approved_scope": deepcopy(approved_scope),
        "official_data_class": official_data_class,
        "claim_policy": deepcopy(claim_policy),
        "offline_required": True,
        "no_hidden_private_data": True,
        "no_network_fetch": True,
        "no_mutation_in_place": True,
        "contamination_boundary": boundary_result,
        "boundary_summary": summary,
        "official_percentage_claimable_text": summary["official_percentage_claimable_text"],
        "official_percentage_claimable_value": summary["official_percentage_claimable_value"],
    }


def _implies_official_percentage_claim(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if normalized in {"none", "none yet", "0", "0%", "zero", "no claim", "not claimable"}:
        return False
    return any(token in normalized for token in ("official", "claim", "%", "percent", "percentage"))


def _validate_claim_policy(claim_policy: Mapping[str, Any], approved_phase: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(claim_policy, Mapping) or not claim_policy:
        return ["missing_claim_policy"]

    allow_official_score_before_local_run = _as_bool(claim_policy.get("allow_official_score_before_local_run"))
    mix_synthetic_and_official_scores = _as_bool(claim_policy.get("mix_synthetic_and_official_scores"))
    competition_submission_authority = _as_bool(claim_policy.get("competition_submission_authority"))
    official_percentage_claimable = _text(claim_policy.get("official_percentage_claimable"))
    official_score_claimable = _as_bool(claim_policy.get("official_score_claimable"))

    if allow_official_score_before_local_run:
        issues.append("premature_official_score_claim_allowed")
    if mix_synthetic_and_official_scores:
        issues.append("synthetic_official_score_mixing_allowed")
    if competition_submission_authority:
        issues.append("competition_submission_authority_claimed")
    if official_score_claimable and approved_phase == "phase_2_public_parse_scorer_validation":
        issues.append("premature_official_score_claim")
    if official_score_claimable and mix_synthetic_and_official_scores:
        issues.append("official_and_synthetic_score_mixing")
    if _implies_official_percentage_claim(official_percentage_claimable) and approved_phase == "phase_2_public_parse_scorer_validation":
        issues.append("premature_official_percentage_claim")
    return issues


def validate_approval_manifest_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    if _as_bool(data.get("competition_submission_authority")):
        raise ValueError("Approval manifest cannot grant competition submission authority")
    if _as_bool(data.get("official_score_claimable")) and _text(data.get("approved_phase")) == "phase_2_public_parse_scorer_validation":
        raise ValueError("Premature official score claim")
    if _as_bool(data.get("mix_synthetic_and_official_scores")):
        raise ValueError("Synthetic and official scores may not be mixed")
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "ALLOWED_APPROVED_PHASES_V1",
    "ALLOWED_OFFICIAL_DATA_CLASSES_V1",
    "validate_approval_manifest",
    "validate_approval_manifest_claim",
]
