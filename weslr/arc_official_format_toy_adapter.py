"""Toy ARC official-format adapter for local evaluation shape checks.

Deterministic, metadata-only, and fail-closed.
This adapter only accepts synthetic/toy fixtures and exists to validate the
shape of an ARC-style JSON task bundle before any official-format adapter or
local-public run is implemented.

It does not load official ARC data, score answers, run solvers, call tools,
call models, call the web, or touch `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_official_contamination_boundary import (
    classify_run_phase,
    validate_contamination_boundary_record,
)

SCHEMA_VERSION_V1 = "arc_official_format_toy_adapter_v1"
TOY_DATA_CLASS_V1 = "synthetic_weslr"
TOY_RUN_PHASE_V1 = "phase_1_toy_fixture_adapter"

_ALLOWED_PUBLIC_TASK_KEYS_V1 = (
    "task_id",
    "train",
    "test",
)

_ALLOWED_PUBLIC_TEST_KEYS_V1 = (
    "input",
    "candidate_output_slots",
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _is_valid_grid(grid: Any) -> bool:
    if not isinstance(grid, list) or not grid:
        return False
    row_lengths = []
    for row in grid:
        if not isinstance(row, list) or not row:
            return False
        row_lengths.append(len(row))
        for cell in row:
            if not isinstance(cell, (int, bool)):
                return False
    return len(set(row_lengths)) == 1


def _validate_grid(grid: Any, field_name: str) -> None:
    if not _is_valid_grid(grid):
        raise ValueError(f"Invalid grid for {field_name}")


def _validate_train_example(example: Any, index: int) -> dict[str, Any]:
    data = _as_mapping(example)
    if "input" not in data or "output" not in data:
        raise ValueError(f"Missing train section at index {index}")
    _validate_grid(data.get("input"), f"train[{index}].input")
    _validate_grid(data.get("output"), f"train[{index}].output")
    return {
        "input": deepcopy(data.get("input")),
        "output": deepcopy(data.get("output")),
    }


def _validate_test_example(example: Any, index: int) -> dict[str, Any]:
    data = _as_mapping(example)
    if "input" not in data:
        raise ValueError(f"Missing test input at index {index}")
    _validate_grid(data.get("input"), f"test[{index}].input")
    if "expected_output" in data:
        _validate_grid(data.get("expected_output"), f"test[{index}].expected_output")
    slots = data.get("candidate_output_slots")
    if slots is None:
        slots = [None, None]
    slots_list = _as_list(slots)
    if len(slots_list) != 2:
        raise ValueError("Each test input must have exactly two candidate output slots")
    return {
        "input": deepcopy(data.get("input")),
        "candidate_output_slots": [None, None],
    }


def parse_toy_official_format_bundle(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception as exc:
            raise ValueError("Invalid JSON bundle") from exc
    bundle = _as_mapping(payload)
    if not bundle:
        raise ValueError("Invalid toy bundle")
    return deepcopy(bundle)


def validate_toy_official_format_bundle(bundle: Any) -> dict[str, Any]:
    data = _as_mapping(bundle)
    if not data:
        raise ValueError("Invalid toy bundle")
    task_id = _text(data.get("task_id"))
    if not task_id:
        raise ValueError("Missing task_id")
    train = data.get("train")
    test = data.get("test")
    if not isinstance(train, list) or not train:
        raise ValueError("Missing train section")
    if not isinstance(test, list) or not test:
        raise ValueError("Missing test section")

    validated_train = [_validate_train_example(example, index) for index, example in enumerate(train)]
    validated_test = [_validate_test_example(example, index) for index, example in enumerate(test)]

    provenance = _as_mapping(data.get("bundle_provenance"))
    source = _text(provenance.get("source"))
    version = _text(provenance.get("version"))
    checksum = _text(provenance.get("checksum"))
    if not source or not version or not checksum:
        raise ValueError("Missing toy fixture bundle provenance/checksum")

    boundary_record = {
        "data_class": TOY_DATA_CLASS_V1,
        "run_phase": TOY_RUN_PHASE_V1,
        "toy_fixture": True,
        "official_data_touched": False,
        "hidden_private_data_touched": False,
        "internet_tool_model_calls_during_solving": False,
        "expected_output_leakage": False,
        "internal_task_language_leakage": False,
        "synthetic_official_score_mixing": False,
        "dataset_provenance": deepcopy(provenance),
    }
    boundary_result = validate_contamination_boundary_record(boundary_record)
    if boundary_result["run_phase"] != TOY_RUN_PHASE_V1:
        raise ValueError("Toy fixture adapter must validate against phase_1_toy_fixture_adapter")

    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id,
        "train": validated_train,
        "test": validated_test,
        "bundle_provenance": deepcopy(provenance),
        "contamination_boundary": boundary_result,
    }


def export_solver_visible_toy_bundle(bundle: Any) -> dict[str, Any]:
    data = validate_toy_official_format_bundle(bundle)
    visible_tests = []
    for test in data["test"]:
        visible_tests.append({
            "input": deepcopy(test["input"]),
            "candidate_output_slots": [None, None],
        })
    return {
        "task_id": data["task_id"],
        "train": deepcopy(data["train"]),
        "test": visible_tests,
        "bundle_provenance": deepcopy(data["bundle_provenance"]),
        "schema_version": SCHEMA_VERSION_V1,
    }


def validate_toy_candidate_outputs(bundle: Any, candidate_outputs: Any) -> dict[str, Any]:
    data = validate_toy_official_format_bundle(bundle)
    outputs = candidate_outputs if isinstance(candidate_outputs, list) else []
    if len(outputs) != len(data["test"]):
        raise ValueError("Candidate outputs must match number of test inputs")
    per_test: list[dict[str, Any]] = []
    for index, candidates in enumerate(outputs):
        if not isinstance(candidates, list):
            raise ValueError("Each test input must have exactly two candidate outputs")
        if len(candidates) != 2:
            raise ValueError("Each test input must have exactly two candidate outputs")
        _validate_grid(candidates[0], f"candidate_outputs[{index}][0]")
        _validate_grid(candidates[1], f"candidate_outputs[{index}][1]")
        per_test.append({"test_index": index, "candidate_count": 2, "valid": True})
    return {
        "valid": True,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": data["task_id"],
        "candidate_outputs_validated": per_test,
        "contamination_boundary": data["contamination_boundary"],
    }


def validate_toy_result_claim(claim: Any) -> dict[str, Any]:
    data = _as_mapping(claim)
    if _text(data.get("claim_kind")) in {"official_local_percentage", "official_arc_performance"}:
        raise ValueError("Synthetic toy results cannot be claimed as official ARC performance")
    return {"valid": True, "schema_version": SCHEMA_VERSION_V1}


__all__ = [
    "SCHEMA_VERSION_V1",
    "TOY_DATA_CLASS_V1",
    "TOY_RUN_PHASE_V1",
    "parse_toy_official_format_bundle",
    "validate_toy_official_format_bundle",
    "export_solver_visible_toy_bundle",
    "validate_toy_candidate_outputs",
    "validate_toy_result_claim",
]
