from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_approval_manifest_v1,
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)
from weslr.arc_agi2_public_challenge_solver_candidate_runner import (
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1,
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1,
    TARGET_PUBLIC_SCOREABLE_V1,
    _validate_candidate_artifact,
    run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1,
)


def _grid(seed: int) -> list[list[int]]:
    return [[seed % 10, (seed + 1) % 10], [(seed + 2) % 10, (seed + 3) % 10]]


def _write_runner_zip(path: Path) -> None:
    payloads = {
        "arc-agi_training_challenges.json": {
            "train_a": {
                "train": [{"input": _grid(1), "output": _grid(2)}],
                "test": [{"input": _grid(3)}, {"input": _grid(4)}],
            },
            "train_b": {
                "train": [{"input": _grid(5), "output": _grid(6)}],
                "test": [{"input": _grid(7)}],
            },
        },
        "arc-agi_training_solutions.json": {
            "train_a": [_grid(2)],
            "train_b": [_grid(6)],
        },
        "arc-agi_evaluation_challenges.json": {
            "eval_a": {
                "train": [{"input": _grid(8), "output": _grid(9)}],
                "test": [{"input": _grid(10)}, {"input": _grid(11)}],
            }
        },
        "arc-agi_evaluation_solutions.json": {
            "eval_a": [_grid(9)],
        },
        "arc-agi_test_challenges.json": {
            "test_a": {
                "train": [{"input": _grid(12), "output": _grid(13)}],
                "test": [{"input": _grid(14)}],
            },
            "test_b": {
                "train": [{"input": _grid(15), "output": _grid(16)}],
                "test": [{"input": _grid(17)}, {"input": _grid(18)}],
            },
        },
        "sample_submission.json": {
            "test_a": [{"attempt_1": _grid(0), "attempt_2": _grid(0)}],
            "test_b": [
                {"attempt_1": _grid(0), "attempt_2": _grid(0)},
                {"attempt_1": _grid(0), "attempt_2": _grid(0)},
            ],
        },
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in payloads.items():
            zf.writestr(name, json.dumps(payload, ensure_ascii=False))


def _base_manifest(source_path: Path, checksum: str, *, phase: str = "public_challenge_solver_candidate_dry_run_no_scoring") -> dict[str, object]:
    return {
        "schema_version": "arc_agi2_public_data_approval_manifest_v1",
        "approval_id": "approval-runner-001",
        "approved_by_owner": True,
        "approval_timestamp": "2026-07-04T18:12:00+02:00",
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
        "approved_phase": phase,
        "allowed_operations": [
            "path_existence_check",
            "checksum_check",
            "git_tracking_exclusion_check",
            "read_only_check",
            "manifest_validation",
            "challenge_input_json_read",
            "placeholder_candidate_emission",
            "local_submission_artifact_shape_validation",
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
            "solution_parse",
            "solution_read",
            "kaggle_submission",
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
            "challenge_shape_policy": "challenge/input files may be parsed structurally only; solution files must not be opened during candidate generation",
        },
    }


@pytest.fixture()
def runner_source_zip(tmp_path: Path) -> Path:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_runner_zip(source)
    source.chmod(0o444)
    return source


@pytest.fixture()
def runner_manifest(runner_source_zip: Path) -> dict[str, object]:
    checksum = hashlib.sha256(runner_source_zip.read_bytes()).hexdigest()
    return _base_manifest(runner_source_zip, checksum)


@pytest.mark.parametrize(
    "target_mode,expected_task_count,expected_test_input_count,expected_files,expected_key_mode",
    [
        (TARGET_PUBLIC_SCOREABLE_V1, 3, 5, ["arc-agi_training_challenges.json", "arc-agi_evaluation_challenges.json"], "raw_task_id"),
        (TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1, 2, 3, ["arc-agi_test_challenges.json"], "raw_task_id"),
        (
            TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1,
            5,
            8,
            ["arc-agi_training_challenges.json", "arc-agi_evaluation_challenges.json", "arc-agi_test_challenges.json"],
            "namespaced_by_challenge_file",
        ),
    ],
)
def test_runner_supports_dynamic_target_modes_and_counts(
    runner_manifest: dict[str, object],
    runner_source_zip: Path,
    tmp_path: Path,
    target_mode: str,
    expected_task_count: int,
    expected_test_input_count: int,
    expected_files: list[str],
    expected_key_mode: str,
) -> None:
    repo_root = tmp_path / "repo"
    staging_root = tmp_path / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        runner_manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        artifact_root=tmp_path / "artifacts",
        target_mode=target_mode,
    )
    assert result["task_count"] == expected_task_count
    assert result["test_input_count"] == expected_test_input_count
    assert result["challenge_files_used"] == expected_files
    assert result["artifact_task_key_mode"] == expected_key_mode
    assert result["solution_files_opened"] is False
    assert result["artifact_validation"]["valid"] is True
    assert result["artifact_validation"]["two_output_valid"] is True
    assert result["artifact_validation"]["task_count"] == expected_task_count
    assert result["artifact_validation"]["test_input_packet_count"] == expected_test_input_count



def test_runner_does_not_open_solution_files(runner_manifest: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    opened: list[str] = []
    original_read = zipfile.ZipFile.read

    def tracking_read(self, name, *args, **kwargs):
        opened.append(str(name))
        return original_read(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", tracking_read)
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        runner_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "artifacts",
        target_mode=TARGET_PUBLIC_SCOREABLE_V1,
    )
    assert result["solution_files_opened"] is False
    assert all(not name.endswith("solutions.json") for name in opened)
    assert any(name.endswith("challenges.json") for name in opened)



def test_complete_coverage_required_by_artifact_validator() -> None:
    artifact = {
        "tasks": {
            "a": {"solver_visible_packets": [{"attempt_1": [[0]], "attempt_2": [[0]]}]},
        }
    }
    result = _validate_candidate_artifact(artifact, expected_task_count=2, expected_test_input_count=2)
    assert result["valid"] is False
    assert result["schema_valid"] is False
    assert result["task_count"] == 1
    assert result["test_input_packet_count"] == 1



def test_exactly_two_output_validation_required(monkeypatch: pytest.MonkeyPatch, runner_manifest: dict[str, object], tmp_path: Path) -> None:
    import weslr.arc_agi2_public_challenge_solver_candidate_runner as runner

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def malformed_top2(*args, **kwargs):
        return {
            "task_id": kwargs.get("task_id", "x"),
            "test_input_index": kwargs.get("test_input_index", 0),
            "candidate_packets": [{"grid": [[0]], "metadata": {}}],
            "metadata": {},
        }

    monkeypatch.setattr(runner, "build_arc_agi2_top2_attempt_packet_v1", malformed_top2)
    with pytest.raises(ValueError):
        runner.run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
            runner_manifest,
            repo_root=repo_root,
            artifact_root=tmp_path / "artifacts",
            target_mode=TARGET_PUBLIC_SCOREABLE_V1,
        )



def test_solver_hash_guard_detects_modified_file(runner_manifest: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import weslr.arc_agi2_public_challenge_solver_candidate_runner as runner

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    state = {"calls": 0}
    original = runner.collect_frozen_solver_candidate_hashes_v1

    def mutating_collect(paths=None):
        state["calls"] += 1
        result = original(paths)
        if state["calls"] == 2 and result:
            key = next(iter(result))
            result[key] = result[key][::-1]
        return result

    monkeypatch.setattr(runner, "collect_frozen_solver_candidate_hashes_v1", mutating_collect)
    with pytest.raises(RuntimeError, match="elastic_public_challenge_coverage_repair_invalid_solver_changed"):
        runner.run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
            runner_manifest,
            repo_root=repo_root,
            artifact_root=tmp_path / "artifacts",
            target_mode=TARGET_PUBLIC_SCOREABLE_V1,
        )



def test_result_summary_contains_no_raw_grids(runner_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        runner_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "artifacts",
        target_mode=TARGET_PUBLIC_SCOREABLE_V1,
    )
    blob = json.dumps(result).lower()
    assert "[[" not in blob
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "solution_grid" not in blob



def test_manifest_accepts_target_phase_and_rejects_scoring_and_submission(runner_source_zip: Path) -> None:
    manifest = _base_manifest(runner_source_zip, hashlib.sha256(runner_source_zip.read_bytes()).hexdigest())
    repo_root = runner_source_zip.parent / "repo"
    staging_root = runner_source_zip.parent / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = validate_arc_agi2_public_data_source_instance_metadata_v1(
        manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_challenge_solver_candidate_dry_run_no_scoring",
    )
    assert result["valid"] is True
    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1({**manifest, "official_score_claim_allowed": True})
    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1({**manifest, "kaggle_submission_allowed": True})
