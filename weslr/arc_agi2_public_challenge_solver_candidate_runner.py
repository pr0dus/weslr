"""ARC-AGI-2 real public challenge solver-candidate no-score dry run runner.

Metadata-only and fail-closed.
This module reads approved public challenge/input JSON, constructs solver-visible
packets without expected outputs, runs a frozen local candidate path, and writes
an out-of-repo candidate artifact for structure validation only.

It never opens public solution files, never scores, never submits, and never
returns raw grids in summary objects.
"""

from __future__ import annotations

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
CHALLENGE_FILES_V1 = (
    "arc-agi_evaluation_challenges.json",
    "arc-agi_test_challenges.json",
    "arc-agi_training_challenges.json",
)
DEFAULT_ARTIFACT_DIRNAME_V1 = "solver_candidate_dry_run_v1"
DEFAULT_ARTIFACT_FILENAME_V1 = "solver_candidates_no_scoring.json"
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


def _make_candidate(candidate_id: str, grid: Sequence[Any], *, rank: int, input_index: int, task_id: str) -> dict[str, Any]:
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
            "source_kind": "public_challenge_solver_candidate_dry_run_no_scoring",
            "task_id": _text(task_id),
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


def _build_top2_packet(task_id: str, test_input_index: int, input_grid: Any) -> dict[str, Any]:
    candidate_grids = _build_candidate_grids(input_grid)
    candidate_a = _make_candidate(f"{task_id}:{test_input_index}:cand_a", candidate_grids[0], rank=1, input_index=test_input_index, task_id=task_id)
    candidate_b = _make_candidate(f"{task_id}:{test_input_index}:cand_b", candidate_grids[1], rank=2, input_index=test_input_index, task_id=task_id)
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


def _artifact_path(repo_root: Path, staging_root: Path | None, artifact_root: str | os.PathLike[str] | None) -> Path:
    if artifact_root is not None:
        return Path(artifact_root).expanduser().resolve() / DEFAULT_ARTIFACT_FILENAME_V1
    return Path("/data/data/com.termux/files/home/arc-agi2-public-source") / DEFAULT_ARTIFACT_DIRNAME_V1 / DEFAULT_ARTIFACT_FILENAME_V1


def _artifact_outside_repos(path: Path, repo_root: Path, staging_root: Path | None) -> bool:
    outside_repo = not _path_is_within(path, repo_root)
    outside_staging = True if staging_root is None else not _path_is_within(path, staging_root)
    return outside_repo and outside_staging


def _validate_candidate_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "valid": False,
        "schema_valid": False,
        "task_count": 0,
        "test_input_packet_count": 0,
        "two_output_valid": False,
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
    for task_id, task_payload in tasks.items():
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


def run_arc_agi2_public_challenge_solver_candidate_dry_run_no_scoring_v1(
    manifest: Any,
    *,
    repo_root: str | os.PathLike[str],
    staging_root: str | os.PathLike[str] | None = None,
    artifact_root: str | os.PathLike[str] | None = None,
    hash_paths: Sequence[str | os.PathLike[str]] | None = None,
) -> dict[str, Any]:
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
    artifact_path = _artifact_path(repo_root_path, staging_root_path, artifact_root)

    challenge_summaries: dict[str, Any] = {}
    solver_visible_packets: dict[str, list[dict[str, Any]]] = {}
    candidate_artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V1,
        "dry_run_kind": "public_challenge_solver_candidate_dry_run_no_scoring",
        "source_path": str(source_path),
        "tasks": {},
        "metadata": {
            "synthetic_only": True,
            "no_scoring": True,
            "no_submission": True,
            "no_solution_data": True,
            "frozen_solver_candidate_paths": list(hash_snapshot_before.keys()),
        },
    }
    solution_files_opened = False
    challenge_files_parsed = True
    with zipfile.ZipFile(source_path) as zf:
        member_names = set(zf.namelist())
        for forbidden_member in ("arc-agi_evaluation_solutions.json", "arc-agi_training_solutions.json"):
            if forbidden_member in member_names:
                pass
        for challenge_member in CHALLENGE_FILES_V1:
            if challenge_member not in member_names:
                raise ValueError(f"missing_challenge_member:{challenge_member}")
            payload = _safe_json_load(zf.read(challenge_member).decode("utf-8"), label=challenge_member)
            summary = _validate_challenge_payload(challenge_member, payload)
            challenge_summaries[challenge_member] = summary
            if not summary["schema_valid"]:
                raise ValueError(f"invalid_challenge_schema:{challenge_member}")
            if challenge_member == "arc-agi_test_challenges.json":
                for task_id, task in payload.items():
                    if not isinstance(task, Mapping):
                        continue
                    packets: list[dict[str, Any]] = []
                    for test_input_index, test_pair in enumerate(task.get("test", [])):
                        if not isinstance(test_pair, Mapping):
                            continue
                        packet = _build_top2_packet(task_id, test_input_index, test_pair.get("input"))
                        packets.append(packet)
                    solver_visible_packets[_text(task_id)] = packets
                    candidate_artifact["tasks"][_text(task_id)] = {
                        "challenge_file": challenge_member,
                        "solver_visible_packets": packets,
                        "test_input_packet_count": len(packets),
                    }

    artifact_validation = _validate_candidate_artifact(candidate_artifact)
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
        }
    )
    if not redaction_result["valid"]:
        raise ValueError("redaction_failed")

    hash_snapshot_after = collect_frozen_solver_candidate_hashes_v1(hash_paths)
    hash_guard_result = validate_frozen_solver_candidate_hashes_v1(hash_snapshot_before, hash_snapshot_after)
    if not hash_guard_result["valid"]:
        raise RuntimeError("real_public_solver_candidate_dry_run_invalid_solver_changed")

    task_count = sum(summary["task_count"] for summary in challenge_summaries.values())
    test_input_count = challenge_summaries["arc-agi_test_challenges.json"]["test_input_count"]
    result = {
        "valid": bool(meta["checksum_match"]) and artifact_validation["valid"] and redaction_result["valid"] and hash_guard_result["valid"],
        "schema_version": SCHEMA_VERSION_V1,
        "manifest": deepcopy(meta["manifest"]),
        "source_path": meta["source_path"],
        "checksum_match": bool(meta["checksum_match"]),
        "approved_phase": meta["approved_phase"],
        "challenge_files_used": list(CHALLENGE_FILES_V1),
        "challenge_summaries": challenge_summaries,
        "solution_files_opened": solution_files_opened,
        "challenge_files_parsed": challenge_files_parsed,
        "task_count": task_count,
        "test_input_count": test_input_count,
        "candidate_artifact_path": artifact_meta["path"],
        "candidate_artifact_meta": artifact_meta,
        "artifact_validation": artifact_validation,
        "solver_visible_packet_summary": {
            "task_count": len(solver_visible_packets),
            "test_input_packet_count": sum(len(packets) for packets in solver_visible_packets.values()),
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
            "solver_run": True,
            "candidate_generation": True,
            "scoring": False,
            "submission": False,
        },
        "official_data_committed": False,
        "official_data_touched": True,
        "official_data_read": True,
        "official_challenge_data_parsed": True,
        "official_solution_data_parsed": False,
        "solver_run": True,
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
    "DEFAULT_ARTIFACT_FILENAME_V1",
    "FROZEN_SOLVER_CANDIDATE_PATHS_V1",
    "SCHEMA_VERSION_V1",
    "collect_frozen_solver_candidate_hashes_v1",
    "run_arc_agi2_public_challenge_solver_candidate_dry_run_no_scoring_v1",
    "validate_frozen_solver_candidate_hashes_v1",
]
