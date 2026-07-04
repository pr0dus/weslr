"""ARC-AGI-2 real public local score check no-submission helper.

Metadata-only and fail-closed.
This module reads an existing frozen candidate artifact, scores it against
approved public solution files using exact grid equality only, and verifies the
candidate artifact hash remains unchanged before and after scoring.

It never imports or runs the solver, never generates candidates, never submits,
and never returns raw grids in summary objects.
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

from weslr.arc_agi2_public_challenge_solver_candidate_runner import (
    DEFAULT_ARTIFACT_FILENAME_V1 as DEFAULT_CANDIDATE_ARTIFACT_FILENAME_V1,
    DEFAULT_ARTIFACT_DIRNAME_V1 as DEFAULT_CANDIDATE_ARTIFACT_DIRNAME_V1,
    validate_frozen_solver_candidate_hashes_v1,
)
from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)
from weslr.arc_agi2_submission_contract import validate_arc_agi2_top2_attempt_packet_v1

SCHEMA_VERSION_V1 = "arc_agi2_public_local_score_checker_v1"
SOLUTION_FILES_V1 = (
    "arc-agi_evaluation_solutions.json",
    "arc-agi_training_solutions.json",
)
CHALLENGE_FILES_V1 = (
    "arc-agi_evaluation_challenges.json",
    "arc-agi_test_challenges.json",
    "arc-agi_training_challenges.json",
)
_FORBIDDEN_MARKERS_V1 = (
    "expected_output",
    "expected_outputs",
    "reference_output",
    "reference_outputs",
    "solution_grid",
    "latent_rule",
    "solver_hint",
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


def _artifact_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def _safe_json_load(text: str, *, label: str) -> Any:
    try:
        return json.loads(text)
    except Exception as exc:
        raise ValueError(f"invalid_json:{label}") from exc


def _grid_equal(a: Any, b: Any) -> bool:
    return a == b


def _is_grid(value: Any) -> bool:
    return isinstance(value, list) and value and all(isinstance(row, list) and row for row in value)


def _candidate_artifact_path(artifact_path: str | os.PathLike[str] | None) -> Path:
    if artifact_path is not None:
        return Path(artifact_path).expanduser().resolve()
    return Path("/data/data/com.termux/files/home/arc-agi2-public-source") / DEFAULT_CANDIDATE_ARTIFACT_DIRNAME_V1 / DEFAULT_CANDIDATE_ARTIFACT_FILENAME_V1


def _candidate_artifact_outside_repos(path: Path, repo_root: Path, staging_root: Path | None) -> bool:
    outside_repo = not _path_is_within(path, repo_root)
    outside_staging = True if staging_root is None else not _path_is_within(path, staging_root)
    return outside_repo and outside_staging


def _load_candidate_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("candidate_artifact_not_mapping")
    return dict(payload)


def _load_solution_mapping(zf: zipfile.ZipFile, member_name: str) -> dict[str, Any]:
    payload = _safe_json_load(zf.read(member_name).decode("utf-8"), label=member_name)
    if not isinstance(payload, Mapping):
        raise ValueError(f"solution_file_not_mapping:{member_name}")
    return dict(payload)


def _load_challenge_mapping(zf: zipfile.ZipFile, member_name: str) -> dict[str, Any]:
    payload = _safe_json_load(zf.read(member_name).decode("utf-8"), label=member_name)
    if not isinstance(payload, Mapping):
        raise ValueError(f"challenge_file_not_mapping:{member_name}")
    return dict(payload)


def _validate_redaction(payload: Mapping[str, Any]) -> dict[str, Any]:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    leakage = any(marker in serialized for marker in _FORBIDDEN_MARKERS_V1)
    return {"valid": not leakage, "contains_forbidden_markers": leakage}


def _extract_candidate_packets(candidate_artifact: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    tasks = candidate_artifact.get("tasks")
    if not isinstance(tasks, Mapping):
        raise ValueError("candidate_artifact_tasks_not_mapping")
    packets_by_task: dict[str, list[dict[str, Any]]] = {}
    for task_id, task_payload in tasks.items():
        if not isinstance(task_payload, Mapping):
            raise ValueError("candidate_task_payload_not_mapping")
        packets = task_payload.get("solver_visible_packets")
        if not isinstance(packets, list):
            raise ValueError("candidate_solver_visible_packets_not_list")
        packets_by_task[_text(task_id)] = [dict(packet) if isinstance(packet, Mapping) else packet for packet in packets]
    return packets_by_task


def _validate_candidate_packets(packets_by_task: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    result = {
        "valid": False,
        "task_count": len(packets_by_task),
        "packet_count": 0,
        "two_output_valid": False,
        "malformed_count": 0,
        "missing_count": 0,
        "reasons": [],
    }
    packet_count = 0
    malformed = 0
    two_output_valid = True
    for task_id, packets in packets_by_task.items():
        if not isinstance(packets, Sequence):
            malformed += 1
            two_output_valid = False
            continue
        packet_count += len(packets)
        for packet in packets:
            if not isinstance(packet, Mapping):
                malformed += 1
                two_output_valid = False
                continue
            validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
            if not validation["valid"]:
                malformed += 1
                two_output_valid = False
    result["packet_count"] = packet_count
    result["malformed_count"] = malformed
    result["two_output_valid"] = two_output_valid
    result["valid"] = two_output_valid
    return result


def _score_packet_against_solution_packet(packet: Mapping[str, Any], solution_grid: Any) -> dict[str, Any]:
    attempts = packet.get("attempts") if isinstance(packet.get("attempts"), list) else []
    if len(attempts) != 2:
        return {"malformed": True, "correct": False}
    solution_is_grid = _is_grid(solution_grid)
    if not solution_is_grid:
        return {"malformed": True, "correct": False}
    if any(not isinstance(attempt, Mapping) or not _is_grid(attempt.get("grid")) for attempt in attempts):
        return {"malformed": True, "correct": False}
    correct = any(_grid_equal(attempt.get("grid"), solution_grid) for attempt in attempts)
    return {"malformed": False, "correct": correct}


def _score_task_packets(candidate_packets: Sequence[Mapping[str, Any]], solution_grids: Sequence[Any]) -> dict[str, Any]:
    correct = 0
    incorrect = 0
    malformed = 0
    any_correct = False
    any_malformed = False
    any_valid_packet = False
    for packet in candidate_packets:
        if not isinstance(packet, Mapping):
            any_malformed = True
            continue
        packet_result = {"malformed": False, "correct": False}
        for solution_grid in solution_grids:
            packet_result = _score_packet_against_solution_packet(packet, solution_grid)
            if not packet_result["malformed"]:
                break
        if packet_result["malformed"]:
            any_malformed = True
        else:
            any_valid_packet = True
            if packet_result["correct"]:
                any_correct = True
    if any_malformed:
        malformed += 1
    if any_correct:
        correct += 1
    elif any_valid_packet:
        incorrect += 1
    return {"correct": correct, "incorrect": incorrect, "malformed": malformed}


def run_arc_agi2_public_local_score_check_no_submission_v1(
    manifest: Any,
    *,
    repo_root: str | os.PathLike[str],
    staging_root: str | os.PathLike[str] | None = None,
    artifact_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    meta = validate_arc_agi2_public_data_source_instance_metadata_v1(
        manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_local_score_check_no_submission",
    )
    repo_root_path = Path(repo_root).resolve()
    staging_root_path = Path(staging_root).resolve() if staging_root is not None else None
    source_path = Path(meta["source_path"])
    candidate_path = _candidate_artifact_path(artifact_path)
    if not candidate_path.exists():
        raise FileNotFoundError("local_public_score_check_failed_missing_frozen_candidate_artifact")
    if not _candidate_artifact_outside_repos(candidate_path, repo_root_path, staging_root_path):
        raise ValueError("candidate_artifact_must_be_outside_git_repos")
    if _git_tracked(candidate_path, repo_root_path):
        raise ValueError("candidate_artifact_git_tracked")

    candidate_hash_before = _artifact_hash(candidate_path)
    candidate_artifact = _load_candidate_artifact(candidate_path)
    packets_by_task = _extract_candidate_packets(candidate_artifact)
    candidate_validation = _validate_candidate_packets(packets_by_task)

    solution_summaries: dict[str, Any] = {}
    challenge_summaries: dict[str, Any] = {}
    total_tasks_scored = 0
    correct_count = 0
    incorrect_count = 0
    malformed_count = 0
    missing_count = 0

    with zipfile.ZipFile(source_path) as zf:
        for challenge_member in CHALLENGE_FILES_V1:
            if challenge_member in zf.namelist():
                challenge_payload = _load_challenge_mapping(zf, challenge_member)
                challenge_summaries[challenge_member] = {
                    "task_count": len(challenge_payload),
                    "file_name": challenge_member,
                }
        for solution_member in SOLUTION_FILES_V1:
            if solution_member not in zf.namelist():
                continue
            solution_payload = _load_solution_mapping(zf, solution_member)
            solution_summaries[solution_member] = {"task_count": len(solution_payload), "file_name": solution_member}
            for task_id, solutions in solution_payload.items():
                total_tasks_scored += 1
                candidate_packets = packets_by_task.get(_text(task_id))
                if not candidate_packets:
                    missing_count += 1
                    continue
                if not isinstance(solutions, list):
                    malformed_count += 1
                    continue
                score_result = _score_task_packets(candidate_packets, solutions)
                correct_count += score_result["correct"]
                incorrect_count += score_result["incorrect"]
                malformed_count += score_result["malformed"]

    candidate_hash_after = _artifact_hash(candidate_path)
    hash_guard_result = {
        "valid": candidate_hash_before == candidate_hash_after,
        "before": candidate_hash_before,
        "after": candidate_hash_after,
    }
    if not hash_guard_result["valid"]:
        raise RuntimeError("local_public_score_check_invalid_candidate_artifact_changed")

    redaction_result = _validate_redaction(
        {
            "challenge_summaries": challenge_summaries,
            "solution_summaries": solution_summaries,
            "candidate_validation": candidate_validation,
            "hash_guard_result": hash_guard_result,
        }
    )
    if not redaction_result["valid"]:
        raise ValueError("redaction_failed")

    exact_match_rate = 0.0 if total_tasks_scored == 0 else float(correct_count) / float(total_tasks_scored)
    result = {
        "valid": bool(meta["checksum_match"]) and redaction_result["valid"] and hash_guard_result["valid"],
        "schema_version": SCHEMA_VERSION_V1,
        "manifest": deepcopy(meta["manifest"]),
        "source_path": meta["source_path"],
        "checksum_match": bool(meta["checksum_match"]),
        "approved_phase": meta["approved_phase"],
        "candidate_artifact_path": str(candidate_path),
        "candidate_artifact_hash_before": candidate_hash_before,
        "candidate_artifact_hash_after": candidate_hash_after,
        "candidate_artifact_unchanged": candidate_hash_before == candidate_hash_after,
        "candidate_artifact_outside_repos": _candidate_artifact_outside_repos(candidate_path, repo_root_path, staging_root_path),
        "candidate_artifact_git_tracked": _git_tracked(candidate_path, repo_root_path),
        "solution_files_parsed": True,
        "solution_files_opened": True,
        "candidate_validation": candidate_validation,
        "challenge_summaries": challenge_summaries,
        "solution_summaries": solution_summaries,
        "total_tasks_scored": total_tasks_scored,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "malformed_candidate_count": malformed_count,
        "missing_candidate_count": missing_count,
        "exactly_two_output_valid": candidate_validation["two_output_valid"],
        "local_public_exact_match_rate_non_official": exact_match_rate,
        "hash_guard_result": hash_guard_result,
        "redaction_result": redaction_result,
        "leakage_audit": {
            "raw_grids_logged": False,
            "solution_reference_logged": False,
            "solution_reference_logged": False,
            "solver_run": False,
            "candidate_generation": False,
            "scoring": True,
            "submission": False,
        },
        "official_data_committed": False,
        "official_data_touched": True,
        "official_data_read": True,
        "official_solution_data_parsed": True,
        "official_challenge_data_parsed": True,
        "solver_run": False,
        "candidate_generation": False,
        "scoring": True,
        "kaggle_submission_made": False,
        "official_percentage": 0,
    }
    if not result["valid"]:
        raise ValueError("Invalid public local score check result")
    return result


__all__ = [
    "CHALLENGE_FILES_V1",
    "SCHEMA_VERSION_V1",
    "SOLUTION_FILES_V1",
    "run_arc_agi2_public_local_score_check_no_submission_v1",
]
