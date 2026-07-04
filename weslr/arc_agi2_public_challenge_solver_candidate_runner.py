"""ARC-AGI-2 public challenge solver-candidate dry runs.

Metadata-only and fail-closed.
This module reads approved public challenge/input JSON, constructs solver-visible
packets without expected outputs, and writes an out-of-repo candidate artifact
for structural validation only.

It never opens public solution files, never scores, never submits, and never
returns raw grids in summary objects.

Target modes:
- public_scoreable
- kaggle_test_submission_shape
- all_public_challenges_no_score
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)
from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_primitive_sequence_grid_reconstruction import apply_primitive_sequence_to_grid_v1

SCHEMA_VERSION_V1 = "arc_agi2_public_challenge_solver_candidate_runner_v1"
TARGET_PUBLIC_SCOREABLE_V1 = "public_scoreable"
TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1 = "kaggle_test_submission_shape"
TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1 = "all_public_challenges_no_score"
TARGET_MODE_ALIASES_V1 = {
    "public_challenge_solver_candidate_dry_run_no_scoring": TARGET_PUBLIC_SCOREABLE_V1,
    "public_challenge_solver_candidate_dry_run_no_score": TARGET_PUBLIC_SCOREABLE_V1,
}
TARGET_MODE_TO_CHALLENGE_FILES_V1 = {
    TARGET_PUBLIC_SCOREABLE_V1: (
        "arc-agi_training_challenges.json",
        "arc-agi_evaluation_challenges.json",
    ),
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1: (
        "arc-agi_test_challenges.json",
    ),
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1: (
        "arc-agi_training_challenges.json",
        "arc-agi_evaluation_challenges.json",
        "arc-agi_test_challenges.json",
    ),
}
TARGET_MODE_TO_ARTIFACT_FILENAME_V1 = {
    TARGET_PUBLIC_SCOREABLE_V1: "public_scoreable_candidates_no_submission.json",
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1: "kaggle_test_candidates_no_submission.json",
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1: "all_public_challenges_candidates_no_score.json",
}
TARGET_MODE_TO_SELECTION_LABEL_V1 = {
    TARGET_PUBLIC_SCOREABLE_V1: "post_exposure_local_public_scoreable_only",
    TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1: "kaggle_test_submission_shape_only",
    TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1: "all_public_challenges_no_score_only",
}
DEFAULT_ARTIFACT_DIRNAME_V1 = "solver_candidate_dry_run_v1"
DEFAULT_ARTIFACT_FILENAME_V1 = "solver_candidates_no_scoring.json"
DEFAULT_ARTIFACT_DIRNAME_V2 = "solver_candidate_dry_run_v2"
FROZEN_SOLVER_CANDIDATE_PATHS_V1 = (
    Path(__file__).resolve(),
    Path(__file__).resolve().with_name("arc_agi2_submission_contract.py"),
    Path(__file__).resolve().with_name("arc_primitive_sequence_grid_reconstruction.py"),
    Path(__file__).resolve().with_name("arc_style_grid_solver_dry_run.py"),
)
_FORBIDDEN_MARKERS_V1 = (
    "expected_output",
    "expected_outputs",
    "reference_output",
    "reference_outputs",
    "solver_hint",
    "latent_rule",
    "answer_key",
)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except Exception:
        return False


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


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def collect_frozen_solver_candidate_hashes_v1(paths: Sequence[str | os.PathLike[str]] | None = None) -> dict[str, str]:
    selected_paths = [Path(p).resolve() for p in (paths or FROZEN_SOLVER_CANDIDATE_PATHS_V1)]
    return {str(path): _hash_file(path) for path in selected_paths if path.exists()}


def validate_frozen_solver_candidate_hashes_v1(
    before: Mapping[str, str],
    after: Mapping[str, str],
) -> dict[str, Any]:
    before_map = {str(key): _text(value) for key, value in before.items()}
    after_map = {str(key): _text(value) for key, value in after.items()}
    changed = sorted(key for key in before_map if before_map.get(key) != after_map.get(key))
    missing = sorted(key for key in before_map if key not in after_map)
    extra = sorted(key for key in after_map if key not in before_map)
    return {
        "valid": not changed and not missing and not extra,
        "changed_paths": changed,
        "missing_paths": missing,
        "extra_paths": extra,
        "before": before_map,
        "after": after_map,
    }


def _safe_json_load(text: str, *, label: str) -> Any:
    try:
        return json.loads(text)
    except Exception as exc:
        raise ValueError(f"invalid_json:{label}") from exc


def _grid_dimensions(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("invalid_grid_shape")
    width: int | None = None
    for row in grid:
        if not isinstance(row, list) or not row:
            raise ValueError("invalid_grid_row_shape")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("non_rectangular_grid")
        for cell in row:
            if not isinstance(cell, int):
                raise ValueError("non_integer_grid_cell")
    return len(grid), width or 0


def _zero_grid(rows: int, cols: int) -> list[list[int]]:
    if rows <= 0 or cols <= 0:
        raise ValueError("invalid_placeholder_dimensions")
    return [[0 for _ in range(cols)] for _ in range(rows)]


def _anonymize_task_id(task_id: str) -> str:
    return hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:16]


def _normalize_target_mode(target_mode: str | None) -> str:
    mode = _text(target_mode, TARGET_PUBLIC_SCOREABLE_V1)
    mode = TARGET_MODE_ALIASES_V1.get(mode, mode)
    if mode not in TARGET_MODE_TO_CHALLENGE_FILES_V1:
        raise ValueError(f"unsupported_target_mode:{mode}")
    return mode


def _artifact_filename_for_target(target_mode: str) -> str:
    return TARGET_MODE_TO_ARTIFACT_FILENAME_V1[target_mode]


def _artifact_path(
    repo_root: Path,
    staging_root: Path | None,
    artifact_root: str | os.PathLike[str] | None,
    *,
    target_mode: str,
) -> Path:
    filename = _artifact_filename_for_target(target_mode)
    if artifact_root is not None:
        return Path(artifact_root).expanduser().resolve() / filename
    return Path("/data/data/com.termux/files/home/arc-agi2-public-source") / DEFAULT_ARTIFACT_DIRNAME_V2 / filename


def _artifact_outside_repos(path: Path, repo_root: Path, staging_root: Path | None) -> bool:
    outside_repo = not _path_is_within(path, repo_root)
    outside_staging = True if staging_root is None else not _path_is_within(path, staging_root)
    return outside_repo and outside_staging


def _validate_challenge_payload(name: str, payload: Any) -> dict[str, Any]:
    result = {
        "file_name": name,
        "schema_valid": False,
        "task_count": 0,
        "test_input_count": 0,
        "test_input_count_per_task": [],
        "anonymized_task_ids": [],
        "reasons": [],
    }
    if not isinstance(payload, Mapping):
        result["reasons"].append("top_level_not_mapping")
        return result

    task_ids = list(payload.keys())
    result["task_count"] = len(task_ids)
    result["anonymized_task_ids"] = [_anonymize_task_id(str(task_id)) for task_id in task_ids]
    total_test_inputs = 0
    counts: list[int] = []
    for task_id, task in payload.items():
        if not isinstance(task, Mapping):
            result["reasons"].append("task_not_mapping")
            continue
        train = task.get("train")
        test = task.get("test")
        if not isinstance(train, list) or not train:
            result["reasons"].append("train_missing_or_invalid")
        if not isinstance(test, list) or not test:
            result["reasons"].append("test_missing_or_invalid")
            continue
        counts.append(len(test))
        total_test_inputs += len(test)
        for train_pair in train if isinstance(train, list) else []:
            if not isinstance(train_pair, Mapping):
                result["reasons"].append("train_pair_not_mapping")
                continue
            if set(train_pair.keys()) != {"input", "output"}:
                result["reasons"].append("train_pair_schema_invalid")
            _grid_dimensions(train_pair.get("input"))
            _grid_dimensions(train_pair.get("output"))
        for test_pair in test:
            if not isinstance(test_pair, Mapping):
                result["reasons"].append("test_pair_not_mapping")
                continue
            if set(test_pair.keys()) != {"input"}:
                result["reasons"].append("test_pair_schema_invalid")
            _grid_dimensions(test_pair.get("input"))
    result["test_input_count"] = total_test_inputs
    result["test_input_count_per_task"] = counts
    result["schema_valid"] = not result["reasons"]
    return result


def _solver_visible_packet(task_id: str, challenge_file: str, test_input_index: int, input_grid: Any) -> dict[str, Any]:
    rows, cols = _grid_dimensions(input_grid)
    return {
        "task_id": _text(task_id),
        "challenge_file": _text(challenge_file),
        "test_input_index": int(test_input_index),
        "input_grid": deepcopy(input_grid),
        "input_grid_metadata": {
            "rows": rows,
            "cols": cols,
            "cell_count": rows * cols,
            "rectangular": True,
        },
        "metadata": {
            "dry_run_kind": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "no_solution_values": True,
            "no_solution_data": True,
            "no_scoring": True,
            "no_submission": True,
        },
    }


def _build_candidate_grids(input_grid: Any) -> list[list[list[int]]]:
    rows, cols = _grid_dimensions(input_grid)
    copy_result = apply_primitive_sequence_to_grid_v1(input_grid, [{"primitive_id": "copy", "parameters": {}}])
    copied_grid = copy_result.get("reconstructed_grid") if isinstance(copy_result, Mapping) else None
    grid_a = copied_grid if isinstance(copied_grid, list) else _zero_grid(rows, cols)
    grid_b = _zero_grid(rows, cols)
    return [deepcopy(grid_a), deepcopy(grid_b)]


def _make_candidate(candidate_id: str, grid: Sequence[Any], *, rank: int, input_index: int, task_id: str, challenge_file: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "source_candidate_id": candidate_id,
        "grid": deepcopy(list(grid)),
        "confidence_label": "unknown" if rank == 1 else "low",
        "evidence_labels": ["shape_only", "format_only", "no_solution_data"],
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": {
            "synthetic_only": True,
            "no_scoring": True,
            "no_submission": True,
            "source_kind": TARGET_PUBLIC_SCOREABLE_V1,
            "task_id": _text(task_id),
            "challenge_file": _text(challenge_file),
            "test_input_index": int(input_index),
            "candidate_rank": int(rank),
        },
        "trace": {
            "synthetic_only": True,
            "stage": "frozen_local_candidate_path",
            "candidate_rank": int(rank),
            "test_input_index": int(input_index),
        },
        "validation_status": "unknown",
    }


def _build_top2_packet(task_id: str, challenge_file: str, test_input_index: int, input_grid: Any) -> dict[str, Any]:
    candidate_grids = _build_candidate_grids(input_grid)
    candidate_a = _make_candidate(
        f"{challenge_file}:{task_id}:{test_input_index}:cand_a",
        candidate_grids[0],
        rank=1,
        input_index=test_input_index,
        task_id=task_id,
        challenge_file=challenge_file,
    )
    candidate_b = _make_candidate(
        f"{challenge_file}:{task_id}:{test_input_index}:cand_b",
        candidate_grids[1],
        rank=2,
        input_index=test_input_index,
        task_id=task_id,
        challenge_file=challenge_file,
    )
    return build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id,
        test_input_index=test_input_index,
        candidate_packets=[candidate_a, candidate_b],
        metadata={
            "dry_run_kind": SCHEMA_VERSION_V1,
            "synthetic_only": True,
            "no_scoring": True,
            "no_submission": True,
        },
    )


def _validate_candidate_artifact(
    artifact: Mapping[str, Any],
    *,
    expected_task_count: int,
    expected_test_input_count: int,
) -> dict[str, Any]:
    result = {
        "valid": False,
        "schema_valid": False,
        "task_count": 0,
        "test_input_packet_count": 0,
        "two_output_valid": False,
        "expected_task_count": expected_task_count,
        "expected_test_input_count": expected_test_input_count,
        "reasons": [],
    }
    if not isinstance(artifact, Mapping):
        result["reasons"].append("artifact_not_mapping")
        return result
    tasks = artifact.get("tasks")
    if not isinstance(tasks, Mapping):
        result["reasons"].append("tasks_not_mapping")
        return result
    result["task_count"] = len(tasks)
    packet_count = 0
    two_output_valid = True
    if len(tasks) != expected_task_count:
        result["reasons"].append("task_count_mismatch")
    for task_key, task_payload in tasks.items():
        if not isinstance(task_payload, Mapping):
            result["reasons"].append("task_payload_not_mapping")
            two_output_valid = False
            continue
        packets = task_payload.get("solver_visible_packets")
        if not isinstance(packets, list):
            result["reasons"].append("solver_visible_packets_not_list")
            two_output_valid = False
            continue
        packet_count += len(packets)
        for packet in packets:
            if not isinstance(packet, Mapping):
                result["reasons"].append("packet_not_mapping")
                two_output_valid = False
                continue
            validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
            if not validation["valid"]:
                result["reasons"].append(f"top2_invalid:{validation.get('task_id')}:{validation.get('test_input_index')}")
                two_output_valid = False
    result["test_input_packet_count"] = packet_count
    if packet_count != expected_test_input_count:
        result["reasons"].append("test_input_count_mismatch")
    result["two_output_valid"] = two_output_valid
    result["schema_valid"] = not result["reasons"]
    result["valid"] = result["schema_valid"] and two_output_valid
    return result


def _validate_redaction(payload: Mapping[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    leakage = any(marker in serialized for marker in _FORBIDDEN_MARKERS_V1)
    return {
        "valid": not leakage,
        "contains_forbidden_markers": leakage,
    }


def _load_sample_submission_alignment(
    zf: zipfile.ZipFile,
    *,
    candidate_task_ids: Sequence[str],
) -> dict[str, Any]:
    member_name = "sample_submission.json"
    if member_name not in zf.namelist():
        return {
            "available": False,
            "valid": None,
            "candidate_task_count": len(candidate_task_ids),
            "sample_submission_key_count": 0,
            "missing_keys": 0,
            "extra_keys": 0,
        }
    payload = _safe_json_load(zf.read(member_name).decode("utf-8"), label=member_name)
    if not isinstance(payload, Mapping):
        raise ValueError("sample_submission_not_mapping")
    candidate_set = {str(task_id) for task_id in candidate_task_ids}
    sample_set = {str(task_id) for task_id in payload.keys()}
    return {
        "available": True,
        "valid": candidate_set == sample_set,
        "candidate_task_count": len(candidate_set),
        "sample_submission_key_count": len(sample_set),
        "missing_keys": len(sample_set - candidate_set),
        "extra_keys": len(candidate_set - sample_set),
    }


def run_arc_agi2_public_challenge_solver_candidate_dry_run_no_scoring_v1(
    manifest: Any,
    *,
    repo_root: str | os.PathLike[str],
    staging_root: str | os.PathLike[str] | None = None,
    artifact_root: str | os.PathLike[str] | None = None,
    target_mode: str | None = None,
    hash_paths: Sequence[str | os.PathLike[str]] | None = None,
) -> dict[str, Any]:
    target_mode = _normalize_target_mode(target_mode)
    hash_paths = tuple(hash_paths or FROZEN_SOLVER_CANDIDATE_PATHS_V1)
    hash_snapshot_before = collect_frozen_solver_candidate_hashes_v1(hash_paths)
    meta = validate_arc_agi2_public_data_source_instance_metadata_v1(
        manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_challenge_solver_candidate_dry_run_no_scoring",
    )

    repo_root_path = Path(repo_root).resolve()
    staging_root_path = Path(staging_root).resolve() if staging_root is not None else None
    source_path = Path(meta["source_path"])
    artifact_path = _artifact_path(repo_root_path, staging_root_path, artifact_root, target_mode=target_mode)

    selected_challenge_files = TARGET_MODE_TO_CHALLENGE_FILES_V1[target_mode]
    challenge_summaries: dict[str, Any] = {}
    candidate_artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V1,
        "dry_run_kind": target_mode,
        "target_mode": target_mode,
        "source_path": str(source_path),
        "tasks": {},
        "metadata": {
            "synthetic_only": True,
            "no_scoring": True,
            "no_submission": True,
            "no_solution_data": True,
            "selected_target_mode": target_mode,
            "selection_label": TARGET_MODE_TO_SELECTION_LABEL_V1[target_mode],
            "frozen_solver_candidate_paths": list(hash_snapshot_before.keys()),
        },
    }
    solution_files_opened = False
    challenge_files_parsed = True
    sample_submission_alignment = {
        "available": False,
        "valid": None,
        "candidate_task_count": 0,
        "sample_submission_key_count": 0,
        "missing_keys": 0,
        "extra_keys": 0,
    }
    task_key_mode = "raw_task_id"
    if target_mode == TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1:
        task_key_mode = "namespaced_by_challenge_file"

    with zipfile.ZipFile(source_path) as zf:
        member_names = set(zf.namelist())
        for challenge_member in selected_challenge_files:
            if challenge_member not in member_names:
                raise ValueError(f"missing_selected_challenge_member:{challenge_member}")
            payload = _safe_json_load(zf.read(challenge_member).decode("utf-8"), label=challenge_member)
            summary = _validate_challenge_payload(challenge_member, payload)
            challenge_summaries[challenge_member] = summary
            if not summary["schema_valid"]:
                raise ValueError(f"invalid_challenge_schema:{challenge_member}")
            for task_id, task in payload.items():
                if not isinstance(task, Mapping):
                    continue
                packets: list[dict[str, Any]] = []
                test_inputs = task.get("test", [])
                for test_input_index, test_pair in enumerate(test_inputs if isinstance(test_inputs, list) else []):
                    if not isinstance(test_pair, Mapping):
                        continue
                    packet = _build_top2_packet(str(task_id), challenge_member, test_input_index, test_pair.get("input"))
                    packets.append(packet)
                artifact_task_key = str(task_id)
                if task_key_mode == "namespaced_by_challenge_file":
                    artifact_task_key = f"{challenge_member}::{task_id}"
                candidate_artifact["tasks"][artifact_task_key] = {
                    "challenge_file": challenge_member,
                    "source_task_id": str(task_id),
                    "solver_visible_packets": packets,
                    "test_input_packet_count": len(packets),
                }
        if target_mode == TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1:
            sample_submission_alignment = _load_sample_submission_alignment(
                zf,
                candidate_task_ids=[str(task_id) for task_id in candidate_artifact["tasks"].keys()],
            )
            if sample_submission_alignment["available"] and not sample_submission_alignment["valid"]:
                raise ValueError("sample_submission_key_alignment_failed")

    expected_task_count = sum(summary["task_count"] for summary in challenge_summaries.values())
    expected_test_input_count = sum(summary["test_input_count"] for summary in challenge_summaries.values())
    artifact_validation = _validate_candidate_artifact(
        candidate_artifact,
        expected_task_count=expected_task_count,
        expected_test_input_count=expected_test_input_count,
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(candidate_artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    artifact_meta = {
        "path": str(artifact_path),
        "outside_repos": _artifact_outside_repos(artifact_path, repo_root_path, staging_root_path),
        "git_tracked": _git_tracked(artifact_path, repo_root_path),
        "exists": artifact_path.exists(),
    }
    if not artifact_meta["outside_repos"] or artifact_meta["git_tracked"]:
        raise ValueError("candidate_artifact_outside_git_required")

    redaction_result = _validate_redaction(
        {
            "challenge_summaries": challenge_summaries,
            "artifact_meta": artifact_meta,
            "artifact_validation": artifact_validation,
            "sample_submission_alignment": sample_submission_alignment,
        }
    )
    if not redaction_result["valid"]:
        raise ValueError("redaction_failed")

    hash_snapshot_after = collect_frozen_solver_candidate_hashes_v1(hash_paths)
    hash_guard_result = validate_frozen_solver_candidate_hashes_v1(hash_snapshot_before, hash_snapshot_after)
    if not hash_guard_result["valid"]:
        raise RuntimeError("elastic_public_challenge_coverage_repair_invalid_solver_changed")

    task_count = expected_task_count
    test_input_count = expected_test_input_count
    result = {
        "valid": bool(meta["checksum_match"]) and artifact_validation["valid"] and redaction_result["valid"] and hash_guard_result["valid"],
        "schema_version": SCHEMA_VERSION_V1,
        "manifest": deepcopy(meta["manifest"]),
        "source_path": meta["source_path"],
        "checksum_match": bool(meta["checksum_match"]),
        "approved_phase": meta["approved_phase"],
        "target_mode": target_mode,
        "challenge_files_used": list(selected_challenge_files),
        "challenge_summaries": challenge_summaries,
        "solution_files_opened": solution_files_opened,
        "challenge_files_parsed": challenge_files_parsed,
        "task_count": task_count,
        "test_input_count": test_input_count,
        "artifact_task_key_mode": task_key_mode,
        "sample_submission_alignment": sample_submission_alignment,
        "candidate_artifact_path": artifact_meta["path"],
        "candidate_artifact_meta": artifact_meta,
        "artifact_validation": artifact_validation,
        "solver_visible_packet_summary": {
            "task_count": len(candidate_artifact["tasks"]),
            "test_input_packet_count": sum(len(task["solver_visible_packets"]) for task in candidate_artifact["tasks"].values()),
            "solution_values_visible": False,
            "solution_data_visible": False,
        },
        "hash_guard_result": hash_guard_result,
        "hash_snapshot_before": hash_snapshot_before,
        "hash_snapshot_after": hash_snapshot_after,
        "redaction_result": redaction_result,
        "leakage_audit": {
            "raw_grids_logged": False,
            "solution_values_logged": False,
            "reference_leakage_logged": False,
            "solution_files_opened": False,
            "solver_run": False,
            "candidate_generation": True,
            "scoring": False,
            "submission": False,
        },
        "official_data_committed": False,
        "official_data_touched": True,
        "official_data_read": True,
        "official_challenge_data_parsed": True,
        "official_solution_data_parsed": False,
        "solver_run": False,
        "candidate_generation": True,
        "scoring": False,
        "kaggle_submission_made": False,
        "official_percentage": 0,
    }
    if not result["valid"]:
        raise ValueError("Invalid public challenge solver-candidate dry run result")
    return result


run_arc_agi2_public_challenge_solver_candidate_dry_run_no_score_v1 = run_arc_agi2_public_challenge_solver_candidate_dry_run_no_scoring_v1


__all__ = [
    "CHALLENGE_FILES_V1",
    "DEFAULT_ARTIFACT_DIRNAME_V1",
    "DEFAULT_ARTIFACT_DIRNAME_V2",
    "DEFAULT_ARTIFACT_FILENAME_V1",
    "FROZEN_SOLVER_CANDIDATE_PATHS_V1",
    "SCHEMA_VERSION_V1",
    "TARGET_ALL_PUBLIC_CHALLENGES_NO_SCORE_V1",
    "TARGET_KAGGLE_TEST_SUBMISSION_SHAPE_V1",
    "TARGET_PUBLIC_SCOREABLE_V1",
    "collect_frozen_solver_candidate_hashes_v1",
    "run_arc_agi2_public_challenge_solver_candidate_dry_run_no_scoring_v1",
    "validate_frozen_solver_candidate_hashes_v1",
]
