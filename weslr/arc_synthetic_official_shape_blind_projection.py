"""Blind projection for synthetic ARC official-shape mock runs.

Solver-visible packets are anonymized and keep only grids plus generic format
metadata. Family and variant metadata stay scorer-side only.
"""

from __future__ import annotations

from copy import deepcopy
from random import Random
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_train_pair_v1
from weslr.arc_style_synthetic_task_generators import generate_arc_style_synthetic_task_suite_v1

SCHEMA_VERSION_V1 = "ArcSyntheticOfficialShapeBlindProjectionV1"
BLIND_BATCH_COUNT_V1 = 20
BLIND_TASKS_PER_BATCH_V1 = 12
BLIND_BATCH_SEEDS_V1 = tuple(1301 + (index * 37) for index in range(BLIND_BATCH_COUNT_V1))


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


def _sort_key(task: Mapping[str, Any]) -> tuple[Any, ...]:
    return (str(task.get("family_id", "")), int(task.get("variant_index", 0)), str(task.get("task_id", "")))


def _task_bank_v1() -> dict[str, list[dict[str, Any]]]:
    suite = generate_arc_style_synthetic_task_suite_v1()
    bank: dict[str, list[dict[str, Any]]] = {}
    for task in suite.get("tasks", []) if isinstance(suite.get("tasks"), list) else []:
        if not isinstance(task, Mapping) or len(task.get("test_inputs", [])) != 1:
            continue
        family_id = str(task.get("family_id", ""))
        if not family_id:
            continue
        bank.setdefault(family_id, []).append(dict(task))
    for tasks in bank.values():
        tasks.sort(key=_sort_key)
    return bank


def _train_pair_payload(pair: Mapping[str, Any], *, pair_index: int) -> dict[str, Any]:
    return build_arc_style_grid_train_pair_v1(
        f"p{pair_index}",
        pair.get("input_grid", []),
        pair.get("output_grid", []),
        "",
    )


def _selected_internal_task_records_v1(*, seeds: Sequence[int] = BLIND_BATCH_SEEDS_V1) -> dict[str, Any]:
    bank = _task_bank_v1()
    family_ids = sorted(bank)
    if len(family_ids) != BLIND_TASKS_PER_BATCH_V1:
        raise ValueError("expected exactly 12 synthetic families for the blind mock")
    batches: list[dict[str, Any]] = []
    family_manifest: list[dict[str, Any]] = []
    for batch_index, seed in enumerate(list(seeds)[:BLIND_BATCH_COUNT_V1]):
        rng = Random(int(seed))
        selected: list[dict[str, Any]] = []
        for family_index, family_id in enumerate(family_ids):
            family_tasks = bank[family_id]
            task = family_tasks[(batch_index + family_index) % len(family_tasks)]
            validation_metadata = task.get("validation_metadata", {}) if isinstance(task.get("validation_metadata"), Mapping) else {}
            expected_outputs = validation_metadata.get("expected_outputs", []) if isinstance(validation_metadata.get("expected_outputs"), list) else []
            train_pairs = [_train_pair_payload(pair, pair_index=pair_index) for pair_index, pair in enumerate(task.get("train_pairs", []) if isinstance(task.get("train_pairs"), list) else [])]
            selected.append(
                {
                    "source_task_id": str(task.get("task_id", "")),
                    "family_id": family_id,
                    "variant_index": int(task.get("variant_index", 0)),
                    "task_index": family_index,
                    "task_seed": int(seed),
                    "task_id_labeled": f"{task.get('task_id', '')}__compat_{batch_index:02d}_{family_index:02d}",
                    "task_id_blind": f"blind_{batch_index:02d}_{family_index:02d}",
                    "train_pairs": _safe(train_pairs),
                    "test_input": _safe(task.get("test_inputs", [{}])[0].get("input_grid", [])),
                    "expected_output": _safe(expected_outputs[0].get("output_grid", []) if expected_outputs else []),
                    "expected_output_count": len(expected_outputs),
                }
            )
        rng.shuffle(selected)
        batches.append(
            {
                "batch_index": batch_index,
                "seed": int(seed),
                "task_count": len(selected),
                "family_ids": [item["family_id"] for item in selected],
                "selected_tasks": selected,
            }
        )
        family_manifest.append(
            {
                "batch_index": batch_index,
                "seed": int(seed),
                "task_ids": [item["task_id_blind"] for item in selected],
                "family_ids": [item["family_id"] for item in selected],
                "task_count": len(selected),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "synthetic_only": True,
        "official_data_touched": False,
        "public_data_touched": False,
        "network_touched": False,
        "seeds": [int(seed) for seed in list(seeds)[:BLIND_BATCH_COUNT_V1]],
        "batch_count": len(batches),
        "task_count": sum(batch["task_count"] for batch in batches),
        "family_manifest": family_manifest,
        "batches": batches,
    }


def project_blind_task_packet_v1(selected_task: Mapping[str, Any], *, batch_index: int, batch_seed: int, batch_task_index: int) -> dict[str, Any]:
    return {
        "task_id": str(selected_task.get("task_id_blind", f"blind_{batch_index:02d}_{batch_task_index:02d}")),
        "train_pairs": [
            {
                "pair_id": f"p{index}",
                "input_grid": deepcopy(pair.get("input_grid", [])),
                "output_grid": deepcopy(pair.get("output_grid", [])),
            }
            for index, pair in enumerate(selected_task.get("train_pairs", []) if isinstance(selected_task.get("train_pairs"), list) else [])
        ],
        "test_input": deepcopy(selected_task.get("test_input", [])),
        "grid_format": {"format_id": "grid_v1", "json_safe": True},
        "palette": {"palette_ids": [], "json_safe": True},
    }


def project_labeled_task_packet_v1(selected_task: Mapping[str, Any], *, batch_index: int, batch_seed: int, batch_task_index: int) -> dict[str, Any]:
    train_pairs = [
        build_arc_style_grid_train_pair_v1(f"p{index}", pair.get("input_grid", []), pair.get("output_grid", []), "")
        for index, pair in enumerate(selected_task.get("train_pairs", []) if isinstance(selected_task.get("train_pairs"), list) else [])
    ]
    return {
        "task_id": str(selected_task.get("task_id_labeled", f"{selected_task.get('source_task_id', 'task')}_{batch_index:02d}_{batch_task_index:02d}")),
        "task_source": "synthetic_blind_compatibility",
        "train_pairs": train_pairs,
        "test_input": deepcopy(selected_task.get("test_input", [])),
        "grid_format": {"format_id": "grid_v1", "json_safe": True},
        "palette": {"palette_ids": [], "json_safe": True},
        "object_candidates": [],
        "transformation_candidates": [],
        "constraint_candidates": [],
        "candidate_outputs": [],
        "validation_results": [],
        "failure_notes": [],
        "trace": {
            "toy_task": True,
            "internal_synthetic_only": True,
            "compatibility_mode": True,
            "family_id": selected_task.get("family_id"),
            "variant_index": selected_task.get("variant_index"),
            "source_task_id": selected_task.get("source_task_id"),
        },
        "allowed_output_count": 2,
        "compatibility_projection": True,
        "batch_index": batch_index,
        "batch_seed": batch_seed,
        "batch_task_index": batch_task_index,
    }


def build_arc_synthetic_official_shape_blind_projection_bundle_v1(*, seeds: Sequence[int] = BLIND_BATCH_SEEDS_V1) -> dict[str, Any]:
    selected = _selected_internal_task_records_v1(seeds=seeds)
    return selected


def validate_arc_synthetic_official_shape_blind_task_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "blocked_reason_labels": [],
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    for key in ("task_id", "train_pairs", "test_input", "grid_format", "palette"):
        if key not in packet:
            result["blocked_reason_labels"].append(f"missing:{key}")
    if result["blocked_reason_labels"]:
        return result
    serialized = str(packet).lower()
    forbidden = ("family", "variant", "rotate", "reflect", "primitive", "label", "toy_task_type", "source_task_id")
    if any(term in str(packet.get("task_id", "")).lower() for term in forbidden):
        result["blocked_reason_labels"].append("semantic_task_id_visible_to_solver")
    if any(term in serialized for term in forbidden):
        result["blocked_reason_labels"].append("semantic_metadata_visible_to_solver")
    result["valid"] = not result["blocked_reason_labels"]
    return result


__all__ = [
    "BLIND_BATCH_COUNT_V1",
    "BLIND_BATCH_SEEDS_V1",
    "BLIND_TASKS_PER_BATCH_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_synthetic_official_shape_blind_projection_bundle_v1",
    "project_blind_task_packet_v1",
    "project_labeled_task_packet_v1",
    "validate_arc_synthetic_official_shape_blind_task_packet_v1",
]
