"""Synthetic ARC official-shape mock batch generator V1.

Deterministic, synthetic-only, offline batch construction for ARC-AGI-2-style
mock readiness runs. The generator keeps solver-visible inputs separate from
scorer-only hidden references and does not touch official/public ARC data.
"""

from __future__ import annotations

from copy import deepcopy
import json
from random import Random
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
)
from weslr.arc_style_synthetic_task_generators import generate_arc_style_synthetic_task_suite_v1

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeMockGeneratorV1"
MOCK_BATCH_SEEDS_V1 = (101, 202, 303)
MOCK_BATCH_COUNT_V1 = 3
MOCK_TASKS_PER_BATCH_V1 = 8


def _safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_safe(item) for item in value]
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if isinstance(value, set):
        return [_safe(item) for item in sorted(value, key=repr)]
    return str(value)


def _visible_train_pair(pair: Mapping[str, Any]) -> dict[str, Any]:
    return build_arc_style_grid_train_pair_v1(
        str(pair.get("pair_id", "")),
        pair.get("input_grid", []),
        pair.get("output_grid", []),
        str(pair.get("notes", "")),
    )


def _visible_task_packet(task: Mapping[str, Any]) -> dict[str, Any]:
    train_pairs = [_visible_train_pair(pair) for pair in task.get("train_pairs", []) if isinstance(pair, Mapping)]
    test_input = []
    test_inputs = task.get("test_inputs", []) if isinstance(task.get("test_inputs"), list) else []
    if test_inputs:
        test_input = deepcopy(test_inputs[0].get("input_grid", [])) if isinstance(test_inputs[0], Mapping) else []
    trace = {
        "toy_task": True,
        "internal_synthetic_only": True,
        "mock_official_shape": True,
        "batch_task_source": TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        "family_id": task.get("family_id"),
        "variant_index": task.get("variant_index"),
        "task_id": task.get("task_id"),
        "no_official_arc_data": True,
        "no_public_arc_data": True,
    }
    return build_arc_style_grid_task_packet_v1(
        task_id=str(task.get("task_id", "")),
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=train_pairs,
        test_input=test_input,
        candidate_outputs=[],
        validation_results=[],
        failure_notes=[],
        trace=trace,
    )


def _reference_record(task: Mapping[str, Any]) -> dict[str, Any]:
    expected_outputs = []
    validation_metadata = task.get("validation_metadata", {}) if isinstance(task.get("validation_metadata"), Mapping) else {}
    for output in validation_metadata.get("expected_outputs", []) if isinstance(validation_metadata.get("expected_outputs"), list) else []:
        if isinstance(output, Mapping):
            expected_outputs.append(_safe(output.get("output_grid", [])))
        else:
            expected_outputs.append(_safe(output))
    return {
        "task_id": str(task.get("task_id", "")),
        "family_id": str(task.get("family_id", "")),
        "variant_index": int(task.get("variant_index", 0)),
        "expected_outputs": expected_outputs,
        "expected_output_count": len(expected_outputs),
        "hidden_only": True,
        "synthetic_only": True,
    }


def _sort_key(task: Mapping[str, Any]) -> tuple[Any, ...]:
    return (str(task.get("family_id", "")), int(task.get("variant_index", 0)), str(task.get("task_id", "")))


def build_arc_synthetic_official_shape_mock_bundle_v1(
    *,
    seeds: Sequence[int] = MOCK_BATCH_SEEDS_V1,
) -> dict[str, Any]:
    suite = generate_arc_style_synthetic_task_suite_v1()
    one_input_tasks = [task for task in suite.get("tasks", []) if isinstance(task, Mapping) and len(task.get("test_inputs", [])) == 1]
    ordered_tasks = sorted(one_input_tasks, key=_sort_key)
    if len(ordered_tasks) < MOCK_BATCH_COUNT_V1 * MOCK_TASKS_PER_BATCH_V1:
        raise ValueError("not enough one-input synthetic tasks for the mock batches")

    batches: list[dict[str, Any]] = []
    family_manifest: list[dict[str, Any]] = []
    for batch_index, seed in enumerate(list(seeds)[:MOCK_BATCH_COUNT_V1]):
        start = batch_index * MOCK_TASKS_PER_BATCH_V1
        batch_tasks = ordered_tasks[start : start + MOCK_TASKS_PER_BATCH_V1]
        rng = Random(int(seed))
        batch_tasks = list(batch_tasks)
        rng.shuffle(batch_tasks)
        visible_tasks: list[dict[str, Any]] = []
        references: list[dict[str, Any]] = []
        batch_family_ids: list[str] = []
        for task in batch_tasks:
            visible_task = _visible_task_packet(task)
            visible_tasks.append(visible_task)
            references.append(_reference_record(task))
            family_id = str(task.get("family_id", ""))
            if family_id and family_id not in batch_family_ids:
                batch_family_ids.append(family_id)
        family_manifest.append(
            {
                "batch_index": batch_index,
                "seed": int(seed),
                "task_ids": [task.get("task_id") for task in batch_tasks],
                "family_ids": batch_family_ids,
                "task_count": len(batch_tasks),
            }
        )
        batches.append(
            {
                "batch_index": batch_index,
                "seed": int(seed),
                "task_count": len(batch_tasks),
                "family_ids": batch_family_ids,
                "solver_visible_tasks": visible_tasks,
                "reference_tasks": references,
                "synthetic_only": True,
                "official_data_touched": False,
                "public_data_touched": False,
                "network_touched": False,
            }
        )

    bundle = {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "seeds": [int(seed) for seed in list(seeds)[:MOCK_BATCH_COUNT_V1]],
        "batch_count": len(batches),
        "task_count": sum(batch["task_count"] for batch in batches),
        "family_manifest": family_manifest,
        "batches": batches,
    }
    json.dumps(_safe(bundle), ensure_ascii=False, allow_nan=False)
    return bundle


def validate_arc_synthetic_official_shape_mock_bundle_v1(bundle: Any) -> dict[str, Any]:
    result = {"valid": False, "blocked_reason_labels": []}
    if not isinstance(bundle, Mapping):
        result["blocked_reason_labels"].append("bundle_not_mapping")
        return result
    if bundle.get("synthetic_only") is not True:
        result["blocked_reason_labels"].append("synthetic_only_not_true")
    if bundle.get("official_data_touched") is not False:
        result["blocked_reason_labels"].append("official_data_touched_not_false")
    if bundle.get("public_data_touched") is not False:
        result["blocked_reason_labels"].append("public_data_touched_not_false")
    if bundle.get("network_touched") is not False:
        result["blocked_reason_labels"].append("network_touched_not_false")
    if bundle.get("batch_count") != MOCK_BATCH_COUNT_V1:
        result["blocked_reason_labels"].append("batch_count_mismatch")
    if not isinstance(bundle.get("batches"), list) or len(bundle.get("batches", [])) != MOCK_BATCH_COUNT_V1:
        result["blocked_reason_labels"].append("batch_list_mismatch")
    if not isinstance(bundle.get("seeds"), list) or len(bundle.get("seeds", [])) != MOCK_BATCH_COUNT_V1:
        result["blocked_reason_labels"].append("seed_list_mismatch")
    if not isinstance(bundle.get("family_manifest"), list) or len(bundle.get("family_manifest", [])) != MOCK_BATCH_COUNT_V1:
        result["blocked_reason_labels"].append("family_manifest_mismatch")
    for batch in bundle.get("batches", []) if isinstance(bundle.get("batches"), list) else []:
        if not isinstance(batch, Mapping):
            result["blocked_reason_labels"].append("batch_not_mapping")
            continue
        if batch.get("task_count") != MOCK_TASKS_PER_BATCH_V1:
            result["blocked_reason_labels"].append("batch_task_count_mismatch")
        if len(batch.get("solver_visible_tasks", [])) != MOCK_TASKS_PER_BATCH_V1:
            result["blocked_reason_labels"].append("visible_task_count_mismatch")
        if len(batch.get("reference_tasks", [])) != MOCK_TASKS_PER_BATCH_V1:
            result["blocked_reason_labels"].append("reference_task_count_mismatch")
        for task in batch.get("solver_visible_tasks", []) if isinstance(batch.get("solver_visible_tasks"), list) else []:
            if not isinstance(task, Mapping):
                result["blocked_reason_labels"].append("visible_task_not_mapping")
                continue
            if "expected_outputs" in task or "reference_outputs" in task:
                result["blocked_reason_labels"].append("expected_output_leakage")
    result["valid"] = not result["blocked_reason_labels"]
    return result


def summarize_arc_synthetic_official_shape_mock_bundle_v1(bundle: Any) -> dict[str, Any]:
    validation = validate_arc_synthetic_official_shape_mock_bundle_v1(bundle)
    if not isinstance(bundle, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "batch_count": 0,
            "task_count": 0,
            "family_manifest": [],
            "seed_list": [],
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    families = []
    for batch in bundle.get("family_manifest", []) if isinstance(bundle.get("family_manifest"), list) else []:
        if isinstance(batch, Mapping):
            families.extend([family for family in batch.get("family_ids", []) if family not in families])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": validation["valid"],
        "batch_count": int(bundle.get("batch_count", 0)),
        "task_count": int(bundle.get("task_count", 0)),
        "family_manifest": _safe(bundle.get("family_manifest", [])),
        "seed_list": _safe(bundle.get("seeds", [])),
        "family_ids": families,
        "blocked_reason_labels": validation["blocked_reason_labels"],
        "synthetic_only": bool(bundle.get("synthetic_only", False)),
        "official_data_touched": bool(bundle.get("official_data_touched", True)),
        "public_data_touched": bool(bundle.get("public_data_touched", True)),
        "network_touched": bool(bundle.get("network_touched", True)),
    }


__all__ = [
    "MOCK_BATCH_COUNT_V1",
    "MOCK_BATCH_SEEDS_V1",
    "MOCK_TASKS_PER_BATCH_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_synthetic_official_shape_mock_bundle_v1",
    "summarize_arc_synthetic_official_shape_mock_bundle_v1",
    "validate_arc_synthetic_official_shape_mock_bundle_v1",
]
