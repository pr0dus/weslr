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
from weslr.arc_agi2_public_local_score_checker import (
    run_arc_agi2_public_local_score_check_no_submission_v1,
)


SOLUTION_ZIP_FILES = {
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
            {"attempt_1": [[0, 0], [0, 0]], "attempt_2": [[0, 0], [0, 0]]}
        ]
    },
}


def _write_solution_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in SOLUTION_ZIP_FILES.items():
            zf.writestr(name, json.dumps(payload, ensure_ascii=False))


def _write_candidate_artifact(path: Path, *, task_payloads: dict[str, list[dict[str, object]]]) -> None:
    artifact = {
        "schema_version": "arc_agi2_public_challenge_solver_candidate_runner_v1",
        "dry_run_kind": "public_challenge_solver_candidate_dry_run_no_scoring",
        "source_path": str(path),
        "tasks": {
            task_id: {
                "challenge_file": "synthetic",
                "solver_visible_packets": packets,
                "test_input_packet_count": len(packets),
            }
            for task_id, packets in task_payloads.items()
        },
        "metadata": {"synthetic_only": True, "no_scoring": True, "no_submission": True},
    }
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")


def _candidate_packet(task_id: str, test_input_index: int, grid: list[list[int]]) -> dict[str, object]:
    return {
        "task_id": task_id,
        "test_input_index": test_input_index,
        "attempts": [
            {
                "attempt_id": f"{task_id}:{test_input_index}:cand_a:rank1",
                "source_candidate_id": f"{task_id}:{test_input_index}:cand_a",
                "grid": grid,
                "confidence_label": "unknown",
                "evidence_labels": ["synthetic"],
                "leakage_flags": {
                    "uses_test_output": False,
                    "uses_solution_file": False,
                    "uses_answer_key": False,
                    "uses_hidden_private_data": False,
                    "uses_task_id_shortcut": False,
                    "uses_notes_shortcut": False,
                    "lookup_table_detected": False,
                },
                "metadata": {"synthetic_only": True},
                "trace": {"synthetic_only": True},
                "validation_status": "unknown",
                "rank": 1,
            },
            {
                "attempt_id": f"{task_id}:{test_input_index}:cand_b:rank2",
                "source_candidate_id": f"{task_id}:{test_input_index}:cand_b",
                "grid": [[0, 0], [0, 0]],
                "confidence_label": "low",
                "evidence_labels": ["synthetic"],
                "leakage_flags": {
                    "uses_test_output": False,
                    "uses_solution_file": False,
                    "uses_answer_key": False,
                    "uses_hidden_private_data": False,
                    "uses_task_id_shortcut": False,
                    "uses_notes_shortcut": False,
                    "lookup_table_detected": False,
                },
                "metadata": {"synthetic_only": True},
                "trace": {"synthetic_only": True},
                "validation_status": "unknown",
                "rank": 2,
            },
        ],
        "duplicate_attempt_grid": False,
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": {"synthetic_only": True},
    }


def _base_manifest(source_path: Path, checksum: str, *, phase: str = "public_local_score_check_no_submission") -> dict[str, object]:
    return {
        "schema_version": "arc_agi2_public_data_approval_manifest_v1",
        "approval_id": "approval-local-score-001",
        "approved_by_owner": True,
        "approval_timestamp": "2026-07-04T17:47:00+02:00",
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
            "solution_json_read_for_scoring",
            "candidate_artifact_read",
            "exact_match_scoring",
            "json_structure_parse",
            "schema_validation",
            "redaction_audit",
            "leakage_audit",
        ],
        "forbidden_operations": [
            "unzip",
            "parse",
            "solver_run",
            "candidate_generation",
            "candidate_repair",
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
            "score_check_policy": "public solution files may be read only for local exact-match scoring with an unchanged frozen candidate artifact",
        },
    }


@pytest.fixture()
def score_source_zip(tmp_path: Path) -> Path:
    source = tmp_path / "arc-prize-2026-arc-agi-2.zip"
    _write_solution_zip(source)
    source.chmod(0o444)
    return source


@pytest.fixture()
def score_manifest(score_source_zip: Path) -> dict[str, object]:
    return _base_manifest(score_source_zip, hashlib.sha256(score_source_zip.read_bytes()).hexdigest())


@pytest.fixture()
def matching_candidate_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "candidate" / "solver_candidates_no_scoring.json"
    artifact.parent.mkdir(parents=True)
    _write_candidate_artifact(
        artifact,
        task_payloads={
            "task_train_1": [_candidate_packet("task_train_1", 0, [[1, 0], [0, 1]])],
            "task_eval_1": [_candidate_packet("task_eval_1", 0, [[2, 2], [2, 2]])],
        },
    )
    return artifact


def test_checker_refuses_to_run_if_candidate_artifact_missing(score_manifest: dict[str, object], tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(FileNotFoundError):
        run_arc_agi2_public_local_score_check_no_submission_v1(
            score_manifest,
            repo_root=repo_root,
            artifact_path=tmp_path / "missing" / "solver_candidates_no_scoring.json",
        )


def test_checker_exact_match_scoring_works_on_dummy_fixtures(score_manifest: dict[str, object], matching_candidate_artifact: Path, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    staging_root = tmp_path / "staging"
    repo_root.mkdir()
    staging_root.mkdir()
    result = run_arc_agi2_public_local_score_check_no_submission_v1(
        score_manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        artifact_path=matching_candidate_artifact,
    )
    assert result["valid"] is True
    assert result["total_tasks_scored"] == 2
    assert result["correct_count"] == 2
    assert result["incorrect_count"] == 0
    assert result["malformed_candidate_count"] == 0
    assert result["missing_candidate_count"] == 0
    assert result["exactly_two_output_valid"] is True


def test_checker_hashes_artifact_before_and_after_scoring(score_manifest: dict[str, object], matching_candidate_artifact: Path, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_local_score_check_no_submission_v1(
        score_manifest,
        repo_root=repo_root,
        artifact_path=matching_candidate_artifact,
    )
    assert result["candidate_artifact_hash_before"] == result["candidate_artifact_hash_after"]
    assert result["candidate_artifact_unchanged"] is True


def test_checker_detects_modified_artifact(score_manifest: dict[str, object], matching_candidate_artifact: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import weslr.arc_agi2_public_local_score_checker as checker

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    state = {"calls": 0}
    original = checker._artifact_hash

    def mutating_hash(path: Path) -> str:
        state["calls"] += 1
        if state["calls"] == 2:
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return original(path)

    monkeypatch.setattr(checker, "_artifact_hash", mutating_hash)
    with pytest.raises(RuntimeError):
        checker.run_arc_agi2_public_local_score_check_no_submission_v1(
            score_manifest,
            repo_root=repo_root,
            artifact_path=matching_candidate_artifact,
        )


def test_checker_does_not_import_or_call_solver(score_manifest: dict[str, object], matching_candidate_artifact: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    bad_names = ["weslr.arc_style_grid_solver_dry_run", "weslr.arc_primitive_sequence_grid_reconstruction"]
    for name in bad_names:
        sys.modules.pop(name, None)

    original_import = __import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in bad_names:
            raise AssertionError(f"unexpected import:{name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", guarded_import)
    result = run_arc_agi2_public_local_score_check_no_submission_v1(
        score_manifest,
        repo_root=repo_root,
        artifact_path=matching_candidate_artifact,
    )
    assert result["solver_run"] is False
    assert result["candidate_generation"] is False


def test_checker_returns_no_raw_grids(score_manifest: dict[str, object], matching_candidate_artifact: Path, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    result = run_arc_agi2_public_local_score_check_no_submission_v1(
        score_manifest,
        repo_root=repo_root,
        artifact_path=matching_candidate_artifact,
    )
    blob = json.dumps(result).lower()
    assert "[[" not in blob
    assert "expected_output" not in blob
    assert "reference_output" not in blob
    assert "solution_grid" not in blob


def test_exception_messages_do_not_leak_grids(score_manifest: dict[str, object], tmp_path: Path) -> None:
    bad_source = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_source, "w", compression=zipfile.ZIP_DEFLATED) as zf:
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
        zf.writestr("sample_submission.json", json.dumps({"task_test_1": [{"attempt_1": [[0]], "attempt_2": [[0]]}]}))
    bad_source.chmod(0o444)
    bad_manifest = _base_manifest(bad_source, hashlib.sha256(bad_source.read_bytes()).hexdigest(), phase="bad_phase")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    bad_artifact = tmp_path / "candidate" / "solver_candidates_no_scoring.json"
    bad_artifact.parent.mkdir(parents=True)
    _write_candidate_artifact(
        bad_artifact,
        task_payloads={"task_train_1": ["not a packet"]},
    )
    with pytest.raises(ValueError) as exc:
        run_arc_agi2_public_local_score_check_no_submission_v1(
            bad_manifest,
            repo_root=repo_root,
            artifact_path=bad_artifact,
        )
    assert "[[" not in str(exc.value)
    assert "expected_output" not in str(exc.value).lower()
    assert "reference_output" not in str(exc.value).lower()
    assert "solution_grid" not in str(exc.value).lower()


def test_manifest_phase_rejects_submission_and_official_score_claims(score_source_zip: Path) -> None:
    manifest = _base_manifest(score_source_zip, hashlib.sha256(score_source_zip.read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1({**manifest, "official_score_claim_allowed": True})
    with pytest.raises(ValueError):
        validate_arc_agi2_public_data_approval_manifest_v1({**manifest, "kaggle_submission_allowed": True})
