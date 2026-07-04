"""ARC-AGI-2 real public challenge submission-shape dry run runner.

Metadata-only and fail-closed.
This module reads approved public challenge/input JSON, builds placeholder
submission-shape artifacts, and validates exactly-two-output structure without
opening public solution files, scoring, solver execution, or Kaggle submission.

It never returns raw grids in summary objects.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)

SCHEMA_VERSION_V1 = "arc_agi2_public_challenge_submission_shape_runner_v1"
CHALLENGE_FILES_V1 = (
    "arc-agi_evaluation_challenges.json",
    "arc-agi_test_challenges.json",
    "arc-agi_training_challenges.json",
)
DEFAULT_ARTIFACT_DIRNAME_V1 = "submission_shape_dry_run_v1"
DEFAULT_ARTIFACT_FILENAME_V1 = "submission_shape_only.json"
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


def _safe_json_load(text: str, *, label: str) -> Any:
    try:
        return json.loads(text)
    except Exception as exc:
        raise ValueError(f"invalid_json:{label}") from exc


def _anonymize_task_id(task_id: str) -> str:
    return hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:16]


def _artifact_is_outside_repos(path: Path, repo_root: Path, staging_root: Path | None) -> bool:
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


def _build_placeholder_artifact(
    *,
    task_id: str,
    test_inputs: list[Any],
) -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    for test_input in test_inputs:
        rows, cols = _grid_dimensions(test_input)
        zero = _zero_grid(rows, cols)
        packs.append({"attempt_1": deepcopy(zero), "attempt_2": deepcopy(zero)})
    return packs


def _validate_artifact_structure(artifact: Mapping[str, Any], expected_task_specs: Mapping[str, int]) -> dict[str, Any]:
    result = {
        "valid": False,
        "schema_valid": False,
        "task_count": 0,
        "pack_count": 0,
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
    if set(tasks.keys()) != set(expected_task_specs.keys()):
        result["reasons"].append("task_id_mismatch")
    pack_count = 0
    two_output_valid = True
    for task_id, packs in tasks.items():
        expected_pack_count = int(expected_task_specs.get(task_id, -1))
        if not isinstance(packs, list):
            result["reasons"].append("task_packs_not_list")
            two_output_valid = False
            continue
        if expected_pack_count != len(packs):
            result["reasons"].append("pack_count_mismatch")
        pack_count += len(packs)
        for pack in packs:
            if not isinstance(pack, Mapping):
                result["reasons"].append("pack_not_mapping")
                two_output_valid = False
                continue
            if set(pack.keys()) != {"attempt_1", "attempt_2"}:
                result["reasons"].append("pack_schema_invalid")
                two_output_valid = False
            for attempt_key in ("attempt_1", "attempt_2"):
                try:
                    _grid_dimensions(pack.get(attempt_key))
                except ValueError:
                    result["reasons"].append(f"{attempt_key}_invalid")
                    two_output_valid = False
    result["pack_count"] = pack_count
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


def _artifact_path(repo_root: Path, staging_root: Path | None, artifact_root: str | os.PathLike[str] | None) -> Path:
    if artifact_root is not None:
        return Path(artifact_root).expanduser().resolve() / DEFAULT_ARTIFACT_FILENAME_V1
    return Path("/data/data/com.termux/files/home/arc-agi2-public-source") / DEFAULT_ARTIFACT_DIRNAME_V1 / DEFAULT_ARTIFACT_FILENAME_V1


def run_arc_agi2_public_challenge_submission_shape_dry_run_v1(
    manifest: Any,
    *,
    repo_root: str | os.PathLike[str],
    staging_root: str | os.PathLike[str] | None = None,
    artifact_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    meta = validate_arc_agi2_public_data_source_instance_metadata_v1(
        manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_challenge_submission_shape_only",
    )
    repo_root_path = Path(repo_root).resolve()
    staging_root_path = Path(staging_root).resolve() if staging_root is not None else None
    source_path = Path(meta["source_path"])
    artifact_path = _artifact_path(repo_root_path, staging_root_path, artifact_root)

    import zipfile

    challenge_summaries: dict[str, Any] = {}
    placeholder_artifact: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V1,
        "placeholder_candidates_only": True,
        "source_path": str(source_path),
        "tasks": {},
    }
    solution_files_opened = False
    challenge_files_parsed = True
    expected_task_specs: dict[str, int] = {}
    with zipfile.ZipFile(source_path) as zf:
        member_names = set(zf.namelist())
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
                    if isinstance(task, Mapping):
                        test_inputs = [item.get("input") for item in task.get("test", []) if isinstance(item, Mapping)]
                        placeholder_artifact["tasks"][task_id] = _build_placeholder_artifact(task_id=task_id, test_inputs=test_inputs)
                        expected_task_specs[task_id] = len(task.get("test", []))

    artifact_validation = _validate_artifact_structure(placeholder_artifact, expected_task_specs)

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(placeholder_artifact, ensure_ascii=False, indent=2), encoding="utf-8")

    artifact_meta = {
        "path": str(artifact_path),
        "outside_repos": _artifact_is_outside_repos(artifact_path, repo_root_path, staging_root_path),
        "git_tracked": _git_tracked(artifact_path, repo_root_path),
        "exists": artifact_path.exists(),
    }

    redaction_result = _validate_redaction(
        {
            "challenge_summaries": challenge_summaries,
            "artifact_meta": artifact_meta,
            "artifact_validation": artifact_validation,
        }
    )
    if not redaction_result["valid"]:
        raise ValueError("redaction_failed")

    task_count = sum(summary["task_count"] for summary in challenge_summaries.values())
    test_input_count = challenge_summaries["arc-agi_test_challenges.json"]["test_input_count"]
    result = {
        "valid": bool(meta["checksum_match"]) and artifact_validation["valid"] and redaction_result["valid"],
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
        "placeholder_candidates_emitted": True,
        "placeholder_artifact_path": artifact_meta["path"],
        "artifact_meta": artifact_meta,
        "artifact_validation": artifact_validation,
        "redaction_result": redaction_result,
        "leakage_audit": {
            "raw_grids_logged": False,
            "solver_visible_output_logged": False,
            "solution_files_opened": False,
            "solver_run": False,
            "scoring": False,
            "candidate_generation": False,
            "submission": False,
        },
        "official_data_committed": False,
        "official_data_touched": True,
        "official_data_read": True,
        "official_challenge_data_parsed": True,
        "official_solution_data_parsed": False,
        "solver_run": False,
        "scoring": False,
        "candidate_generation": False,
        "kaggle_submission_made": False,
        "official_percentage": 0,
    }
    if not result["valid"]:
        raise ValueError("Invalid public challenge submission-shape dry run result")
    return result


__all__ = [
    "CHALLENGE_FILES_V1",
    "DEFAULT_ARTIFACT_DIRNAME_V1",
    "DEFAULT_ARTIFACT_FILENAME_V1",
    "SCHEMA_VERSION_V1",
    "run_arc_agi2_public_challenge_submission_shape_dry_run_v1",
]
