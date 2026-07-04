from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from weslr.arc_agi2_public_data_parse_only_validator import run_arc_agi2_public_data_parse_only_validation_v1


FILES = {
    "arc-agi_training_challenges.json": {
        "task_train_1": {
            "train": [{"input": [[1, 0], [0, 1]], "output": [[1, 0], [0, 1]]}],
            "test": [{"input": [[1, 1], [0, 0]]}],
        }
    },
    "arc-agi_training_solutions.json": {
        "task_train_1": [[[1, 0], [0, 1]]]
    },
    "arc-agi_evaluation_challenges.json": {
        "task_eval_1": {
            "train": [{"input": [[2, 2], [2, 2]], "output": [[2, 2], [2, 2]]}],
            "test": [{"input": [[2, 0], [0, 2]]}],
        }
    },
    "arc-agi_evaluation_solutions.json": {
        "task_eval_1": [[[2, 2], [2, 2]]]
    },
    "arc-agi_test_challenges.json": {
        "task_test_1": {
            "train": [{"input": [[3, 0], [0, 3]], "output": [[3, 0], [0, 3]]}],
            "test": [{"input": [[3, 3], [3, 0]]}],
        }
    },
    "sample_submission.json": {
        "task_test_1": [
            {
                "attempt_1": [[3, 0], [0, 3]],
                "attempt_2": [[0, 3], [3, 0]],
            }
        ]
    },
}


def _write_synthetic_parse_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in FILES.items():
            zf.writestr(name, json.dumps(payload, ensure_ascii=False))


def _base_manifest(source_path: Path, checksum: str, approved_phase: str = "public_parse_only") -> dict[str, object]:
    return {
        "schema_version": "arc_agi2_public_data_approval_manifest_v1",
        "approval_id": "approval-parse-only-001",
        "approved_by_owner": True,
        "approval_timestamp": "2026-07-04T16:44:00+02:00",
        "competition_name": "ARC-AGI-2",
        "competition_track": "public_kaggle_source_approval",
        "source_type": "public ARC-AGI-2 Kaggle competition source bundle",
        "source_location_local_path": str(source_path),
        "source_origin": "Kaggle ARC Prize 2026 ARC-AGI-2 competition Data tab",
        "source_download_method": "manual owner download from Kaggle Data tab",
        "source_version_or_snapshot": source_path.name,
        "checksum_algorithm": "sha256",
        "checksum_value": checksum,
        "read_only_required": True,
        "offline_required": True,
        "no_network_required": True,
        "hidden_private_data_included": False,
        "approved_phase": approved_phase,
        "allowed_operations": [
            "path_existence_check",
            "checksum_check",
            "git_tracking_exclusion_check",
            "read_only_check",
            "manifest_validation",
            "zip_member_listing",
            "json_structure_parse",
            "schema_validation",
            "redaction_audit",
            "leakage_audit",
        ],
        "forbidden_operations": [
            "unzip",
            "parse",
            "score",
            "solver_run",
            "candidate_generation",
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
            "local_source_directory_policy": "source files must remain outside git repos, read-only, checksum-verified, and must not be committed",
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
                "verify source outside repo",
                "verify source not git-tracked",
            ],
        },
    }


def test_parse_only_validator_passes_on_synthetic_zip(tmp_path: Path) -> None:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_synthetic_parse_zip(source)
    source.chmod(0o444)
    manifest = _base_manifest(source, hashlib.sha256(source.read_bytes()).hexdigest())
    repo_root = tmp_path / "repo"
    staging_root = tmp_path / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = run_arc_agi2_public_data_parse_only_validation_v1(manifest, repo_root=repo_root, staging_root=staging_root)
    assert result["valid"] is True
    assert result["checksum_match"] is True
    assert result["approved_phase"] == "public_parse_only"
    assert result["official_data_read"] is True
    assert result["official_data_parsed"] is True
    assert result["solver_run"] is False
    assert result["scoring"] is False
    assert result["candidate_generation"] is False
    assert result["kaggle_submission_made"] is False
    assert result["redaction_result"]["valid"] is True
    assert result["leakage_audit"]["raw_grids_logged"] is False
    assert result["leakage_audit"]["solver_visible_answer_logged"] is False
    assert all(len(name) > 0 for name in result["json_file_names"])
    blob = json.dumps(result).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob


def test_manifest_phase_must_be_public_parse_only(tmp_path: Path) -> None:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_synthetic_parse_zip(source)
    source.chmod(0o444)
    manifest = _base_manifest(source, hashlib.sha256(source.read_bytes()).hexdigest(), approved_phase="public_metadata_check_only")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(ValueError):
        run_arc_agi2_public_data_parse_only_validation_v1(manifest, repo_root=repo_root)


def test_checksum_mismatch_fails(tmp_path: Path) -> None:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_synthetic_parse_zip(source)
    source.chmod(0o444)
    manifest = _base_manifest(source, "0" * 64)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(ValueError):
        run_arc_agi2_public_data_parse_only_validation_v1(manifest, repo_root=repo_root)


def test_source_inside_git_repo_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    source = repo_root / "arc-prize-2026-arc-agi-2.zip"
    _write_synthetic_parse_zip(source)
    source.chmod(0o444)
    subprocess.run(["git", "add", "arc-prize-2026-arc-agi-2.zip"], cwd=repo_root, check=True)
    manifest = _base_manifest(source, hashlib.sha256(source.read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        run_arc_agi2_public_data_parse_only_validation_v1(manifest, repo_root=repo_root)


def test_exception_messages_do_not_leak_grids(tmp_path: Path) -> None:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "arc-agi_training_challenges.json",
            json.dumps({"task_train_1": {"train": [{"input": [[1]], "output": [[1, 2], [3]]}], "test": [{"input": [[1]]}]}}),
        )
        zf.writestr("arc-agi_training_solutions.json", json.dumps({"task_train_1": [[[1]]]}))
        zf.writestr(
            "arc-agi_evaluation_challenges.json",
            json.dumps({"task_eval_1": {"train": [{"input": [[2]], "output": [[2]]}], "test": [{"input": [[2]]}]}}),
        )
        zf.writestr("arc-agi_evaluation_solutions.json", json.dumps({"task_eval_1": [[[2]]]}))
        zf.writestr(
            "arc-agi_test_challenges.json",
            json.dumps({"task_test_1": {"train": [{"input": [[3]], "output": [[3]]}], "test": [{"input": [[3]]}]}}),
        )
        zf.writestr("sample_submission.json", json.dumps({"task_test_1": [{"attempt_1": [[3]], "attempt_2": [[3]]}]}))
    source.chmod(0o444)
    manifest = _base_manifest(source, hashlib.sha256(source.read_bytes()).hexdigest())
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(ValueError) as exc:
        run_arc_agi2_public_data_parse_only_validation_v1(manifest, repo_root=repo_root)
    assert "[[" not in str(exc.value)
    assert "expected_output" not in str(exc.value).lower()
    assert "reference_output" not in str(exc.value).lower()
