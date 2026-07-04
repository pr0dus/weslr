"""ARC-AGI-2 real public-data parse-only validator.

Metadata-only, checksum-first, and fail-closed.
This module performs parse-only structural validation for an approved public
ARC-AGI-2 source bundle without scoring, candidate generation, solver runs, or
submission behavior.

It never returns raw grids or expected outputs in result objects.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from weslr.arc_agi2_public_data_approval_manifest import (
    validate_arc_agi2_public_data_source_instance_metadata_v1,
)

SCHEMA_VERSION_V1 = "arc_agi2_public_data_parse_only_validator_v1"
EXPECTED_ZIP_MEMBERS_V1 = (
    "arc-agi_evaluation_challenges.json",
    "arc-agi_evaluation_solutions.json",
    "arc-agi_test_challenges.json",
    "arc-agi_training_challenges.json",
    "arc-agi_training_solutions.json",
    "sample_submission.json",
)
_CHALLENGE_FILES_V1 = {
    "arc-agi_evaluation_challenges.json": "evaluation",
    "arc-agi_test_challenges.json": "test",
    "arc-agi_training_challenges.json": "training",
}
_SOLUTION_FILES_V1 = {
    "arc-agi_evaluation_solutions.json": "evaluation",
    "arc-agi_training_solutions.json": "training",
}
_LEAKAGE_NEEDLES_V1 = (
    "expected_output",
    "expected_outputs",
    "reference_output",
    "reference_outputs",
    "hidden_answer",
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


def _ensure_int_grid(grid: Any) -> dict[str, Any]:
    result = {"valid": False, "rows": 0, "cols": 0, "reasons": []}
    if not isinstance(grid, list) or not grid:
        result["reasons"].append("grid_not_nonempty_list")
        return result
    width = None
    for row in grid:
        if not isinstance(row, list) or not row:
            result["reasons"].append("row_not_nonempty_list")
            return result
        if width is None:
            width = len(row)
        elif len(row) != width:
            result["reasons"].append("grid_not_rectangular")
            return result
        for cell in row:
            if not isinstance(cell, int):
                result["reasons"].append("non_integer_cell")
                return result
    result["valid"] = True
    result["rows"] = len(grid)
    result["cols"] = width or 0
    return result


def _safe_json_load(zf: zipfile.ZipFile, member_name: str) -> Any:
    return json.loads(zf.read(member_name).decode("utf-8"))


def _anonymize_task_id(task_id: str) -> str:
    return hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:16]


def _validate_task_collection(name: str, payload: Any, *, expect_output: bool, expect_test_output: bool = False) -> dict[str, Any]:
    result = {
        "file_name": name,
        "schema_valid": False,
        "grid_valid": False,
        "task_count": 0,
        "anonymized_task_ids": [],
        "reasons": [],
    }
    if not isinstance(payload, Mapping):
        result["reasons"].append("top_level_not_mapping")
        return result

    task_ids = list(payload.keys())
    result["task_count"] = len(task_ids)
    result["anonymized_task_ids"] = [_anonymize_task_id(str(task_id)) for task_id in task_ids]
    if not task_ids:
        result["reasons"].append("empty_task_collection")
        return result

    grid_ok = True
    for task_id, task in payload.items():
        if not isinstance(task, Mapping):
            result["reasons"].append("task_not_mapping")
            grid_ok = False
            continue
        train = task.get("train")
        test = task.get("test")
        if not isinstance(train, list) or not train:
            result["reasons"].append("train_missing_or_invalid")
            grid_ok = False
        if not isinstance(test, list) or not test:
            result["reasons"].append("test_missing_or_invalid")
            grid_ok = False
        for train_pair in train if isinstance(train, list) else []:
            if not isinstance(train_pair, Mapping):
                result["reasons"].append("train_pair_not_mapping")
                grid_ok = False
                continue
            if set(train_pair.keys()) != {"input", "output"}:
                result["reasons"].append("train_pair_schema_invalid")
            input_grid = _ensure_int_grid(train_pair.get("input"))
            output_grid = _ensure_int_grid(train_pair.get("output")) if expect_output else {"valid": True}
            grid_ok = grid_ok and input_grid["valid"] and output_grid["valid"]
        for test_pair in test if isinstance(test, list) else []:
            if not isinstance(test_pair, Mapping):
                result["reasons"].append("test_pair_not_mapping")
                grid_ok = False
                continue
            allowed_keys = {"input"} if not expect_test_output else {"input", "output"}
            if not set(test_pair.keys()).issubset(allowed_keys):
                result["reasons"].append("test_pair_schema_invalid")
            input_grid = _ensure_int_grid(test_pair.get("input"))
            grid_ok = grid_ok and input_grid["valid"]
            if expect_test_output and "output" in test_pair:
                grid_ok = grid_ok and _ensure_int_grid(test_pair.get("output"))["valid"]
            if not expect_test_output and "output" in test_pair:
                result["reasons"].append("unexpected_test_output_present")
    result["schema_valid"] = not result["reasons"]
    result["grid_valid"] = grid_ok and result["schema_valid"]
    return result


def _validate_solution_mapping(name: str, payload: Any) -> dict[str, Any]:
    result = {
        "file_name": name,
        "schema_valid": False,
        "grid_valid": False,
        "task_count": 0,
        "reasons": [],
    }
    if not isinstance(payload, Mapping):
        result["reasons"].append("top_level_not_mapping")
        return result
    task_ids = list(payload.keys())
    result["task_count"] = len(task_ids)
    if not task_ids:
        result["reasons"].append("empty_task_collection")
        return result
    grid_ok = True
    for task_id, solutions in payload.items():
        if not isinstance(solutions, list) or not solutions:
            result["reasons"].append("solutions_missing_or_invalid")
            grid_ok = False
            continue
        for solution in solutions:
            if not isinstance(solution, list):
                result["reasons"].append("solution_not_grid")
                grid_ok = False
                continue
            grid_check = _ensure_int_grid(solution)
            grid_ok = grid_ok and grid_check["valid"]
    result["schema_valid"] = not result["reasons"]
    result["grid_valid"] = grid_ok
    return result


def _validate_sample_submission(name: str, payload: Any, expected_task_ids: set[str]) -> dict[str, Any]:
    result = {
        "file_name": name,
        "schema_valid": False,
        "grid_valid": False,
        "linkage_valid": False,
        "task_count": 0,
        "pack_count": 0,
        "reasons": [],
    }
    if not isinstance(payload, Mapping):
        result["reasons"].append("top_level_not_mapping")
        return result
    task_ids = set(payload.keys())
    result["task_count"] = len(task_ids)
    if task_ids != expected_task_ids:
        result["reasons"].append("task_id_mismatch")
    grid_ok = True
    pack_count = 0
    for task_id, attempts in payload.items():
        if not isinstance(attempts, list) or not attempts:
            result["reasons"].append("attempt_list_invalid")
            grid_ok = False
            continue
        pack_count += len(attempts)
        for attempt_pack in attempts:
            if not isinstance(attempt_pack, Mapping):
                result["reasons"].append("attempt_pack_not_mapping")
                grid_ok = False
                continue
            if set(attempt_pack.keys()) != {"attempt_1", "attempt_2"}:
                result["reasons"].append("attempt_pack_schema_invalid")
            for attempt_key in ("attempt_1", "attempt_2"):
                attempt_grid = attempt_pack.get(attempt_key)
                if not _ensure_int_grid(attempt_grid)["valid"]:
                    result["reasons"].append(f"{attempt_key}_invalid")
                    grid_ok = False
    result["pack_count"] = pack_count
    result["schema_valid"] = not result["reasons"]
    result["grid_valid"] = grid_ok
    result["linkage_valid"] = result["schema_valid"] and task_ids == expected_task_ids
    return result


def _validate_redaction(payload: Mapping[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False).lower()
    leakage = any(needle in text for needle in _LEAKAGE_NEEDLES_V1)
    return {"valid": not leakage, "contains_forbidden_markers": leakage}


def run_arc_agi2_public_data_parse_only_validation_v1(
    manifest: Any,
    *,
    repo_root: str | Path,
    staging_root: str | Path | None = None,
) -> dict[str, Any]:
    meta = validate_arc_agi2_public_data_source_instance_metadata_v1(
        manifest,
        repo_root=repo_root,
        staging_root=staging_root,
        required_phase="public_parse_only",
    )
    source_path = Path(meta["source_path"])
    zip_summary: dict[str, Any] = {
        "zip_members": [],
        "json_file_names": [],
        "file_summaries": {},
    }
    with zipfile.ZipFile(source_path) as zf:
        members = zf.namelist()
        zip_summary["zip_members"] = list(members)
        zip_summary["json_file_names"] = [name for name in members if name.endswith(".json")]
        missing = [name for name in EXPECTED_ZIP_MEMBERS_V1 if name not in members]
        extra = [name for name in members if name not in EXPECTED_ZIP_MEMBERS_V1]
        if missing:
            raise ValueError(f"missing_zip_members:{missing}")
        if extra:
            raise ValueError(f"unexpected_zip_members:{extra}")

        challenge_payloads: dict[str, Any] = {}
        for file_name, split_name in _CHALLENGE_FILES_V1.items():
            payload = _safe_json_load(zf, file_name)
            challenge_payloads[split_name] = payload
            zip_summary["file_summaries"][file_name] = _validate_task_collection(file_name, payload, expect_output=(split_name != "test"))

        solution_payloads: dict[str, Any] = {}
        for file_name, split_name in _SOLUTION_FILES_V1.items():
            payload = _safe_json_load(zf, file_name)
            solution_payloads[split_name] = payload
            zip_summary["file_summaries"][file_name] = _validate_solution_mapping(file_name, payload)

        sample_submission = _safe_json_load(zf, "sample_submission.json")
        zip_summary["file_summaries"]["sample_submission.json"] = _validate_sample_submission(
            "sample_submission.json",
            sample_submission,
            expected_task_ids=set(challenge_payloads.get("test", {}).keys()),
        )

    schema_valid = all(summary.get("schema_valid", False) for summary in zip_summary["file_summaries"].values())
    grid_valid = all(summary.get("grid_valid", False) for summary in zip_summary["file_summaries"].values())
    linkage_valid = (
        zip_summary["file_summaries"]["arc-agi_training_challenges.json"]["task_count"]
        == zip_summary["file_summaries"]["arc-agi_training_solutions.json"]["task_count"]
        and zip_summary["file_summaries"]["arc-agi_evaluation_challenges.json"]["task_count"]
        == zip_summary["file_summaries"]["arc-agi_evaluation_solutions.json"]["task_count"]
        and zip_summary["file_summaries"]["sample_submission.json"]["task_count"]
        == zip_summary["file_summaries"]["arc-agi_test_challenges.json"]["task_count"]
    )
    redaction_result = _validate_redaction({
        "zip_members": zip_summary["zip_members"],
        "json_file_names": zip_summary["json_file_names"],
        "file_summaries": zip_summary["file_summaries"],
    })
    leakage_audit = {
        "raw_grids_logged": False,
        "solver_visible_answer_logged": False,
        "solver_run": False,
        "scoring": False,
        "candidate_generation": False,
        "submission": False,
    }
    result = {
        "valid": bool(meta["checksum_match"]) and schema_valid and grid_valid and linkage_valid and redaction_result["valid"],
        "schema_version": SCHEMA_VERSION_V1,
        "manifest": deepcopy(meta["manifest"]),
        "source_path": meta["source_path"],
        "checksum_match": bool(meta["checksum_match"]),
        "approved_phase": meta["approved_phase"],
        "zip_members": zip_summary["zip_members"],
        "json_file_names": zip_summary["json_file_names"],
        "file_summaries": zip_summary["file_summaries"],
        "schema_valid": schema_valid,
        "grid_valid": grid_valid,
        "solution_linkage_valid": linkage_valid,
        "redaction_result": redaction_result,
        "leakage_audit": leakage_audit,
        "official_data_committed": False,
        "official_data_touched": True,
        "official_data_read": True,
        "official_data_parsed": True,
        "solver_run": False,
        "scoring": False,
        "candidate_generation": False,
        "kaggle_submission_made": False,
        "official_percentage": 0,
    }
    if not result["valid"]:
        raise ValueError("Invalid public data parse-only validation result")
    return result


__all__ = [
    "EXPECTED_ZIP_MEMBERS_V1",
    "SCHEMA_VERSION_V1",
    "run_arc_agi2_public_data_parse_only_validation_v1",
]
