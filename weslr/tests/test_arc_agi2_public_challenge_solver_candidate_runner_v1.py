from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_approval_manifest_v1,
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)
from weslr.arc_agi2_public_challenge_solver_candidate_runner import (
    collect_frozen_solver_candidate_hashes_v1,
    run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1,
    validate_frozen_solver_candidate_hashes_v1,
)


FILES = {
    "arc-agi_training_challenges.json": {
        "task_train_1": {
            "train": [{"input": [[1, 0], [0, 1]], "output": [[1, 0], [0, 1]]}],
            "test": [{"input": [[1, 1], [0, 0]]}],
        }
    },
    "arc-agi_training_solutions.json": {"task_train_1": [[[1, 0], [0, 1]]]},
    "arc-agi_evaluation_challenges.json": {
        "task_eval_1": {
            "train": [{"input": [[2, 2], [2, 2]], "output": [[2, 2], [2, 2]]}],
            "test": [{"input": [[2, 0], [0, 2]]}],
        }
    },
    "arc-agi_evaluation_solutions.json": {"task_eval_1": [[[2, 2], [2, 2]]]},
    "arc-agi_test_challenges.json": {
        "task_test_1": {
            "train": [{"input": [[3, 0], [0, 3]], "output": [[3, 0], [0, 3]]}],
            "test": [
                {"input": [[3, 3], [3, 0]]},
                {"input": [[4, 4], [4, 0]]},
            ],
        }
    },
    "sample_submission.json": {
        "task_test_1": [
            {"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]},
            {"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]},
        ]
    },
}


def _write_shape_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in FILES.items():
            zf.writestr(name, json.dumps(payload, ensure_ascii=False))


def _base_manifest(source_path: Path, checksum: str, *, phase: str = "public_challenge_solver_candidate_dry_run_no_scoring") -> dict[str, object]:
    return {
        "schema_version": "arc_agi2_public_data_approval_manifest_v1",
        "approval_id": "approval-solver-dry-run-001",
        "approved_by_owner": True,
        "approval_timestamp": "2026-07-04T17:26:00+02:00",
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
            "solver_visible_packet_construction",
            "frozen_solver_candidate_run",
            "candidate_artifact_shape_validation",
            "local_submission_artifact_shape_validation",
            "hash_guard",
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
            "challenge_shape_policy": "challenge/input files may be parsed structurally for placeholder submission-shape validation only; solution files must not be opened",
            "solver_candidate_policy": "challenge/input files may be parsed structurally for frozen solver-candidate no-score validation only; solution files must not be opened",
        },
    }


@pytest.fixture()
def shape_source_zip(tmp_path: Path) -> Path:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_shape_zip(source)
    source.chmod(0o444)
    return source


@pytest.fixture()
def solver_manifest(shape_source_zip: Path) -> dict[str, object]:
    return _base_manifest(shape_source_zip, hashlib.sha256(shape_source_zip.read_bytes()).hexdigest())


def test_manifest_accepts_solver_candidate_dry_run_and_rejects_scoring_and_submission(shape_source_zip: Path) -> None:
    repo_root = shape_source_zip.parent / "repo"
    staging_root = shape_source_zip.parent / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = validate_arc_agi2_public_data_source_instance_metadata_v1(
        _base_manifest(shape_source_zip, hashlib.sha256(shape_source_zip.read_bytes()).hexdigest()),
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_challenge_solver_candidate_dry_run_no_scoring",
    )
    assert result["valid"] is True

    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1(
            {
                **_base_manifest(shape_source_zip, hashlib.sha256(shape_source_zip.read_bytes()).hexdigest()),
                "official_score_claim_allowed": True,
            }
        )
    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1(
            {
                **_base_manifest(shape_source_zip, hashlib.sha256(shape_source_zip.read_bytes()).hexdigest()),
                "kaggle_submission_allowed": True,
            }
        )


def test_solution_files_are_not_opened_by_solver_candidate_runner(solver_manifest: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    opened: list[str] = []
    original_open = zipfile.ZipFile.open

    def tracking_open(self, name, *args, **kwargs):
        opened.append(str(name))
        return original_open(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", tracking_open)
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    assert result["solution_files_opened"] is False
    assert all(not name.endswith("solutions.json") for name in opened)
    assert any(name.endswith("challenges.json") for name in opened)


def test_solver_visible_packets_contain_no_expected_outputs(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    assert result["solver_visible_packet_summary"]["solution_values_visible"] is False
    blob = json.dumps(result).lower()
    assert "expected_output" not in blob
    assert "reference_output" not in blob


def test_candidate_artifact_has_exactly_two_outputs_per_test_input(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    artifact = json.loads(Path(result["candidate_artifact_path"]).read_text(encoding="utf-8"))
    packets = artifact["tasks"]["task_test_1"]["solver_visible_packets"]
    assert len(packets) == 2
    for packet in packets:
        assert len(packet["attempts"]) == 2
        assert set(packet.keys()) >= {"task_id", "test_input_index", "attempts"}


def test_artifact_contains_no_scorer_references(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    artifact_text = Path(result["candidate_artifact_path"]).read_text(encoding="utf-8").lower()
    assert "scorer" not in artifact_text
    assert "reference_output" not in artifact_text


def test_artifact_path_outside_git_repos(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    staging_root = tmp_path / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    artifact_path = Path(result["candidate_artifact_path"])
    assert result["candidate_artifact_meta"]["outside_repos"] is True
    assert result["candidate_artifact_meta"]["git_tracked"] is False
    assert str(artifact_path).startswith(str(tmp_path))


def test_result_summary_contains_no_raw_grids(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
        solver_manifest,
        repo_root=repo_root,
        artifact_root=tmp_path / "solver_artifact",
    )
    blob = json.dumps(result).lower()
    assert "[[" not in blob
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "scorer" not in blob


def test_exception_messages_do_not_leak_grids(solver_manifest: dict[str, object], tmp_path: Path) -> None:
    bad_source = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_source, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "arc-agi_test_challenges.json",
            json.dumps({"task_test_1": {"train": [{"input": [[1]], "output": [[1, 2], [3]]}], "test": [{"input": [[1, 2]]}]}}),
        )
        zf.writestr("arc-agi_training_challenges.json", json.dumps({"task_train_1": {"train": [{"input": [[1]], "output": [[1]]}], "test": [{"input": [[1]]}]}}))
        zf.writestr("arc-agi_evaluation_challenges.json", json.dumps({"task_eval_1": {"train": [{"input": [[1]], "output": [[1]]}], "test": [{"input": [[1]]}]}}))
        zf.writestr("arc-agi_training_solutions.json", json.dumps({"task_train_1": [[[1]]]}))
        zf.writestr("arc-agi_evaluation_solutions.json", json.dumps({"task_eval_1": [[[1]]]}))
        zf.writestr("sample_submission.json", json.dumps({"task_test_1": [{"attempt_1": [[0]], "attempt_2": [[0]]}]}))
    bad_source.chmod(0o444)
    bad_manifest = _base_manifest(bad_source, hashlib.sha256(bad_source.read_bytes()).hexdigest())
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(ValueError) as exc:
        run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1(
            bad_manifest,
            repo_root=repo_root,
            artifact_root=tmp_path / "solver_artifact",
        )
    assert "[[" not in str(exc.value)
    assert "expected_output" not in str(exc.value).lower()
    assert "reference_output" not in str(exc.value).lower()
    assert "scorer" not in str(exc.value).lower()


def test_solver_hash_guard_detects_modified_file(tmp_path: Path) -> None:
    file_path = tmp_path / "solver_component.py"
    file_path.write_text("alpha", encoding="utf-8")
    before = collect_frozen_solver_candidate_hashes_v1([file_path])
    file_path.write_text("beta", encoding="utf-8")
    after = collect_frozen_solver_candidate_hashes_v1([file_path])
    result = validate_frozen_solver_candidate_hashes_v1(before, after)
    assert result["valid"] is False
    assert str(file_path.resolve()) in result["changed_paths"]
