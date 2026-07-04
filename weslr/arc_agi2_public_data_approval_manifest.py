"""ARC-AGI-2 real public-data approval manifest helpers.

Metadata-only and fail-closed.
This module validates the owner-provided approval manifest shape for a future
real public-data phase without opening, downloading, parsing, scoring, or
running any official/public ARC data.

It does not touch `.weslr`, call tools/providers/models, or require network.
"""

from __future__ import annotations

from copy import deepcopy
import os
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "arc_agi2_public_data_approval_manifest_v1"

ALLOWED_APPROVED_PHASES_V1 = (
    "public_metadata_check_only",
    "public_parse_only",
    "public_parse_scorer_check",
    "public_challenge_submission_shape_only",
    "public_challenge_solver_candidate_dry_run_no_scoring",
    "public_local_score_check_no_submission",
    "public_local_training_validation",
    "kaggle_notebook_packaging",
    "kaggle_submission_owner_approved",
)

DEFAULT_REQUIRED_FIELDS_V1 = (
    "approval_id",
    "approved_by_owner",
    "approval_timestamp",
    "competition_name",
    "competition_track",
    "source_type",
    "source_location_local_path",
    "source_origin",
    "source_download_method",
    "source_version_or_snapshot",
    "checksum_algorithm",
    "checksum_value",
    "read_only_required",
    "offline_required",
    "no_network_required",
    "hidden_private_data_included",
    "approved_phase",
    "allowed_operations",
    "forbidden_operations",
    "official_score_claim_allowed",
    "kaggle_submission_allowed",
)

_ALLOWED_OPERATIONS_V1 = {
    "inspect_metadata_only",
    "read_only_local_bundle",
    "checksum_verify",
    "offline_validation",
    "manifest_validation",
    "read_only_bundle_check",
    "local_path_policy_check",
    "path_existence_check",
    "checksum_check",
    "git_tracking_exclusion_check",
    "read_only_check",
    "zip_member_listing",
    "json_structure_parse",
    "challenge_input_json_read",
    "solver_visible_packet_construction",
    "frozen_solver_candidate_run",
    "candidate_artifact_shape_validation",
    "local_submission_artifact_shape_validation",
    "hash_guard",
    "solution_json_read_for_scoring",
    "exact_match_scoring",
    "candidate_artifact_read",
    "placeholder_candidate_emission",
    "schema_validation",
    "redaction_audit",
    "leakage_audit",
}

_FORBIDDEN_OPERATIONS_V1 = {
    "download_source",
    "open_official_task_json",
    "parse_official_task_json",
    "run_solver_on_official_data",
    "score_official_data",
    "submit_to_kaggle",
    "kaggle_submission",
    "publish_score_claim",
    "solution_read",
    "solution_parse",
    "solution_json_read_for_scoring",
    "candidate_artifact_read",
    "exact_match_scoring",
    "use_network",
    "use_provider_api",
    "unzip",
    "parse",
    "score",
    "solver_run",
    "candidate_generation",
    "candidate_repair",
    "submission",
    "public_claim",
    "data_commit",
}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _as_bool(value: Any) -> bool:
    return value is True


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def build_arc_agi2_public_data_approval_manifest_template_v1() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "approval_id": "",
        "approved_by_owner": False,
        "approval_timestamp": "",
        "competition_name": "ARC-AGI-2",
        "competition_track": "public_kaggle_source_approval",
        "source_type": "",
        "source_location_local_path": "",
        "source_origin": "",
        "source_download_method": "",
        "source_version_or_snapshot": "",
        "checksum_algorithm": "sha256",
        "checksum_value": "",
        "read_only_required": True,
        "offline_required": True,
        "no_network_required": True,
        "hidden_private_data_included": False,
        "approved_phase": "public_parse_only",
        "allowed_operations": ["path_existence_check", "checksum_check", "git_tracking_exclusion_check", "read_only_check", "manifest_validation"],
        "forbidden_operations": [
            "unzip",
            "parse",
            "score",
            "solver_run",
            "submission",
            "public_claim",
            "data_commit",
        ],
        "official_score_claim_allowed": False,
        "kaggle_submission_allowed": False,
        "source_descriptor": {
            "read_only_bundle_required": True,
            "metadata_only": True,
            "no_official_data_commit": True,
            "no_public_score_claim": True,
            "no_submission_until_owner_approval": True,
        },
        "policy_notes": {
            "local_source_directory_policy": "source files must remain in a read-only local directory and must not be committed",
            "read_only_bundle_policy": "the approved source bundle is metadata-only, checksum-verified, offline-only, and read-only",
            "checksum_and_provenance_checklist": [
                "capture source_location_local_path",
                "capture source_origin",
                "capture source_download_method",
                "capture source_version_or_snapshot",
                "capture checksum_algorithm",
                "capture checksum_value",
                "verify read_only_required",
                "verify offline_required",
                "verify no_network_required",
            ],
        },
    }


def validate_arc_agi2_public_data_approval_manifest_v1(manifest: Any) -> dict[str, Any]:
    data = manifest if isinstance(manifest, Mapping) else {}
    if not data:
        raise ValueError("Invalid public data approval manifest")

    issues: list[str] = []
    required_missing = [field for field in DEFAULT_REQUIRED_FIELDS_V1 if field not in data]
    if required_missing:
        issues.append("missing_required_fields")
        issues.extend(f"missing:{field}" for field in required_missing)

    approval_id = _text(data.get("approval_id"))
    approved_by_owner = _as_bool(data.get("approved_by_owner"))
    approval_timestamp = _text(data.get("approval_timestamp"))
    competition_name = _text(data.get("competition_name"))
    competition_track = _text(data.get("competition_track"))
    source_type = _text(data.get("source_type"))
    source_location_local_path = _text(data.get("source_location_local_path"))
    source_origin = _text(data.get("source_origin"))
    source_download_method = _text(data.get("source_download_method"))
    source_version_or_snapshot = _text(data.get("source_version_or_snapshot"))
    checksum_algorithm = _text(data.get("checksum_algorithm"))
    checksum_value = _text(data.get("checksum_value"))
    read_only_required = _as_bool(data.get("read_only_required"))
    offline_required = _as_bool(data.get("offline_required"))
    no_network_required = _as_bool(data.get("no_network_required"))
    hidden_private_data_included = _as_bool(data.get("hidden_private_data_included"))
    approved_phase = _text(data.get("approved_phase"))
    allowed_operations = _as_list(data.get("allowed_operations"))
    forbidden_operations = _as_list(data.get("forbidden_operations"))
    official_score_claim_allowed = _as_bool(data.get("official_score_claim_allowed"))
    kaggle_submission_allowed = _as_bool(data.get("kaggle_submission_allowed"))

    if not approval_id:
        issues.append("missing_approval_id")
    if not approved_by_owner:
        issues.append("owner_not_approved")
    if not approval_timestamp:
        issues.append("missing_approval_timestamp")
    if competition_name != "ARC-AGI-2":
        issues.append("competition_name_mismatch")
    if not competition_track:
        issues.append("missing_competition_track")
    if not source_type:
        issues.append("missing_source_type")
    if not source_location_local_path:
        issues.append("missing_source_location_local_path")
    if not source_origin:
        issues.append("missing_source_origin")
    if not source_download_method:
        issues.append("missing_source_download_method")
    if not source_version_or_snapshot:
        issues.append("missing_source_version_or_snapshot")
    if not checksum_algorithm:
        issues.append("missing_checksum_algorithm")
    if not checksum_value:
        issues.append("missing_checksum_value")
    if not read_only_required:
        issues.append("read_only_required_must_be_true")
    if not offline_required:
        issues.append("offline_required_must_be_true")
    if not no_network_required:
        issues.append("no_network_required_must_be_true")
    if hidden_private_data_included:
        issues.append("hidden_private_data_included_must_be_false")
    if approved_phase and approved_phase not in ALLOWED_APPROVED_PHASES_V1:
        issues.append("unsupported_approved_phase")
    if approved_phase == "public_parse_only" and not approved_by_owner:
        issues.append("public_parse_only_requires_owner_approval")

    allowed_set = {str(item).strip() for item in allowed_operations if str(item).strip()}
    forbidden_set = {str(item).strip() for item in forbidden_operations if str(item).strip()}
    if not allowed_set:
        issues.append("allowed_operations_missing")
    if not forbidden_set:
        issues.append("forbidden_operations_missing")
    if "download_source" in allowed_set or "open_official_task_json" in allowed_set or "parse_official_task_json" in allowed_set:
        issues.append("forbidden_operations_misclassified")
    if not _ALLOWED_OPERATIONS_V1.issuperset(allowed_set):
        issues.append("unsupported_allowed_operations")
    if not _FORBIDDEN_OPERATIONS_V1.issuperset(forbidden_set):
        issues.append("unsupported_forbidden_operations")
    if official_score_claim_allowed:
        issues.append("official_score_claim_allowed_must_be_false")
    if kaggle_submission_allowed:
        issues.append("kaggle_submission_allowed_must_be_false")
    if "use_network" in allowed_set or "use_provider_api" in allowed_set:
        issues.append("network_or_provider_operation_allowed")

    if issues:
        raise ValueError(f"Invalid public data approval manifest: {sorted(set(issues))}")

    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "approval_id": approval_id,
        "approved_by_owner": True,
        "approved_phase": approved_phase,
        "competition_name": competition_name,
        "competition_track": competition_track,
        "source_type": source_type,
        "source_location_local_path": source_location_local_path,
        "source_origin": source_origin,
        "source_download_method": source_download_method,
        "source_version_or_snapshot": source_version_or_snapshot,
        "checksum_algorithm": checksum_algorithm,
        "checksum_value": checksum_value,
        "read_only_required": True,
        "offline_required": True,
        "no_network_required": True,
        "hidden_private_data_included": False,
        "allowed_operations": sorted(allowed_set),
        "forbidden_operations": sorted(forbidden_set),
        "official_score_claim_allowed": False,
        "kaggle_submission_allowed": False,
        "source_descriptor": deepcopy(data.get("source_descriptor", {})) if isinstance(data.get("source_descriptor"), Mapping) else {},
        "policy_notes": deepcopy(data.get("policy_notes", {})) if isinstance(data.get("policy_notes"), Mapping) else {},
    }


def _resolve_path(path_value: Any) -> Path:
    return Path(_text(path_value)).expanduser().resolve()


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except Exception:
        return False


def _path_is_read_only(path: Path) -> bool:
    mode = path.stat().st_mode
    return not any(mode & bit for bit in (stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH))


def _git_tracked(path: Path, repo_root: Path) -> bool:
    if not _path_is_within(path, repo_root):
        return False
    rel = path.resolve().relative_to(repo_root.resolve())
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", rel.as_posix()],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def validate_arc_agi2_public_data_source_instance_metadata_v1(
    manifest: Any,
    *,
    repo_root: str | os.PathLike[str],
    staging_root: str | os.PathLike[str] | None = None,
    required_phase: str = "public_metadata_check_only",
) -> dict[str, Any]:
    base_result = validate_arc_agi2_public_data_approval_manifest_v1(manifest)
    source_path = _resolve_path(base_result["source_location_local_path"])
    repo_root_path = Path(repo_root).resolve()
    staging_root_path = Path(staging_root).resolve() if staging_root is not None else None

    issues: list[str] = []
    source_outside_repo = not _path_is_within(source_path, repo_root_path)
    source_outside_staging = True if staging_root_path is None else not _path_is_within(source_path, staging_root_path)
    source_git_tracked = _git_tracked(source_path, repo_root_path)

    if not source_path.exists():
        issues.append("source_missing")
    if _path_is_within(source_path, repo_root_path):
        issues.append("source_inside_weslr_repo")
    if staging_root_path is not None and _path_is_within(source_path, staging_root_path):
        issues.append("source_inside_staging_repo")
    if source_git_tracked:
        issues.append("source_git_tracked")
    if source_path.exists() and not _path_is_read_only(source_path):
        issues.append("source_not_read_only")
    if _text(base_result.get("approved_phase")) != required_phase:
        issues.append("approved_phase_not_required")

    checksum_algorithm = _text(base_result.get("checksum_algorithm")).lower()
    checksum_value = _text(base_result.get("checksum_value")).lower()
    checksum_match = False
    if source_path.exists():
        if checksum_algorithm != "sha256":
            issues.append("checksum_algorithm_must_be_sha256")
        else:
            import hashlib

            actual = hashlib.sha256(source_path.read_bytes()).hexdigest().lower()
            checksum_match = actual == checksum_value
            if not checksum_match:
                issues.append("checksum_mismatch")

    if issues:
        raise ValueError(f"Invalid public data source metadata: {sorted(set(issues))}")

    return {
        "valid": True,
        "manifest": deepcopy(base_result),
        "source_path": str(source_path),
        "source_outside_repo": source_outside_repo,
        "source_outside_staging": source_outside_staging,
        "source_git_tracked": source_git_tracked,
        "source_read_only": _path_is_read_only(source_path),
        "checksum_algorithm": checksum_algorithm,
        "checksum_match": checksum_match,
        "approved_phase": _text(base_result.get("approved_phase")),
        "required_phase": required_phase,
        "allowed_operations": deepcopy(base_result.get("allowed_operations", [])),
        "forbidden_operations": deepcopy(base_result.get("forbidden_operations", [])),
    }


__all__ = [
    "ALLOWED_APPROVED_PHASES_V1",
    "DEFAULT_REQUIRED_FIELDS_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_public_data_approval_manifest_template_v1",
    "validate_arc_agi2_public_data_approval_manifest_v1",
    "validate_arc_agi2_public_data_source_instance_metadata_v1",
]
