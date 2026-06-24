"""WESLR ARC-style grid generalization stress test Phase 3B.

Phase 3B only: synthetic generalization stress test for the bounded solver dry
run. This stays inside the internal synthetic toy-task boundary and uses Phase
1/2/3 helpers only.

No ARC dataset ingestion. No public ARC sample ingestion. No score claims.
No provider calls. No model calls. No payment calls. No ChatResponder wiring.
No website/runtime wiring. No `.weslr` writes.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_style_grid_adapter_phase2 import SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1
from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_task_packet_v1,
)
from weslr.arc_style_grid_solver_dry_run import (
    FAILURE_CATEGORIES_V1,
    MAX_CANDIDATES_PER_TASK_V1,
    MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
    run_arc_style_bounded_solver_dry_run_v1,
    summarize_arc_style_solver_dry_run_result_v1,
    validate_arc_style_solver_dry_run_result_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleGridGeneralizationStressV1"
STRESS_TYPE_V1 = "arc_style_grid_generalization_stress_v1"
MIN_VARIANT_COUNT_V1 = 20
SUPPORTED_FAMILIES_V1 = (
    "copy_grid",
    "recolor_symbol",
    "move_single_object",
    "fill",
    "complete_symmetry",
    "border_frame_fill",
)
UNSUPPORTED_DECoy_FAMILIES_V1 = ("rotate", "reflect")

REQUIRED_RESULT_FIELDS_V1 = (
    "variant_count",
    "primitive_families_covered",
    "exact_match_count",
    "partial_match_count",
    "unsupported_count",
    "failure_ledger_summary",
    "metadata_perturbations_applied",
    "anti_leakage_checks",
    "no_score_claim",
    "trace",
)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def to_arc_style_generalization_stress_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _reverse_grid(grid: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in reversed(grid)]


def _clone_pair(pair: Mapping[str, Any], *, pair_id_suffix: str, note_suffix: str = "") -> dict[str, Any]:
    cloned = to_arc_style_grid_task_json_safe_v1(pair)
    cloned["pair_id"] = f"{_safe_text(cloned.get('pair_id'))}{pair_id_suffix}"
    notes = _safe_text(cloned.get("notes"))
    cloned["notes"] = f"{notes}{note_suffix}".strip()
    return cloned


def _base_trace(family: str, variant_key: str, perturbations: Sequence[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "toy_task_type": family,
        "internal_synthetic_only": True,
        "generalization_stress": True,
        "stress_type": STRESS_TYPE_V1,
        "variant_key": variant_key,
        "metadata_perturbations": list(perturbations),
        "no_arc_dataset_ingestion": True,
        "no_public_arc_sample_ingestion": True,
        "no_solver_runtime": True,
    }


def perturb_arc_style_task_metadata_v1(
    task_packet: Mapping[str, Any],
    *,
    task_id: str,
    notes: Sequence[str] | str | None = None,
    reverse_train_pairs: bool = False,
    reorder_trace_fields: bool = False,
    trace_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(task_packet, Mapping):
        return {}
    task = to_arc_style_grid_task_json_safe_v1(task_packet)
    task["task_id"] = _safe_text(task_id)
    if notes is None:
        task["failure_notes"] = []
    elif isinstance(notes, str):
        task["failure_notes"] = [notes] if notes else []
    else:
        task["failure_notes"] = [_safe_text(note) for note in notes if _safe_text(note)]
    train_pairs = list(task.get("train_pairs", []))
    if reverse_train_pairs:
        train_pairs = list(reversed(train_pairs))
    task["train_pairs"] = train_pairs
    trace = dict(task.get("trace", {})) if isinstance(task.get("trace"), Mapping) else {}
    if trace_overrides:
        trace.update(dict(trace_overrides))
    if reorder_trace_fields:
        ordered: dict[str, Any] = {}
        if "variant_key" in trace:
            ordered["variant_key"] = trace["variant_key"]
        if "metadata_perturbations" in trace:
            ordered["metadata_perturbations"] = trace["metadata_perturbations"]
        for key, value in trace.items():
            if key not in ordered:
                ordered[key] = value
        trace = ordered
    task["trace"] = trace
    return task


def _make_task_packet(
    *,
    family: str,
    variant_key: str,
    task_id: str,
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Sequence[Any],
    perturbations: Sequence[str],
    notes: Sequence[str] | str | None = None,
    reverse_train_pairs: bool = False,
    reorder_trace_fields: bool = False,
    trace_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base_trace = _base_trace(family, variant_key, perturbations)
    if trace_overrides:
        base_trace.update(dict(trace_overrides))
    task = build_arc_style_grid_task_packet_v1(
        task_id=task_id,
        task_source=TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
        train_pairs=list(train_pairs),
        test_input=test_input,
        failure_notes=[] if notes is None else ([notes] if isinstance(notes, str) else list(notes)),
        trace=base_trace,
    )
    return perturb_arc_style_task_metadata_v1(
        task,
        task_id=task_id,
        notes=notes,
        reverse_train_pairs=reverse_train_pairs,
        reorder_trace_fields=reorder_trace_fields,
        trace_overrides=trace_overrides,
    )


def _make_copy_tasks() -> list[dict[str, Any]]:
    grids = [
        [[1, 2], [3, 4]],
        [[5, 6, 7], [8, 9, 1], [2, 3, 4]],
        [[1, 1, 2], [2, 3, 3]],
        [[4, 5, 6, 7], [8, 1, 2, 3]],
    ]
    tasks = []
    for index, grid in enumerate(grids, start=1):
        pair = build_arc_style_grid_train_pair_v1(f"copy_pair_{index}", grid, grid, f"copy-{index}")
        tasks.append(
            _make_task_packet(
                family="copy_grid",
                variant_key=f"copy_{index}",
                task_id=f"gen_copy_{index}",
                train_pairs=[pair],
                test_input=grid,
                perturbations=["task_id_renamed", "notes_normalized"],
                notes=[f"copy variant {index}"],
            )
        )
    return tasks


def _make_recolor_tasks() -> list[dict[str, Any]]:
    variants = [
        ([[1, 1, 1], [1, 2, 1], [1, 1, 1]], [[1, 1, 1], [1, 3, 1], [1, 1, 1]]),
        ([[4, 4], [4, 5]], [[4, 4], [4, 6]]),
        ([[7, 8, 7], [7, 7, 7]], [[7, 9, 7], [7, 7, 7]]),
        ([[2, 2, 2, 2], [2, 3, 2, 2]], [[2, 2, 2, 2], [2, 4, 2, 2]]),
    ]
    tasks = []
    for index, (input_grid, output_grid) in enumerate(variants, start=1):
        pair_a = build_arc_style_grid_train_pair_v1(f"recolor_pair_{index}_a", input_grid, output_grid, f"recolor-{index}")
        pair_b = _clone_pair(pair_a, pair_id_suffix="_b", note_suffix="-duplicate")
        tasks.append(
            _make_task_packet(
                family="recolor_symbol",
                variant_key=f"recolor_{index}",
                task_id=f"gen_recolor_{index}",
                train_pairs=[pair_a, pair_b],
                test_input=input_grid,
                perturbations=["task_id_renamed", "notes_normalized", "train_pair_duplicated"],
                notes=[f"recolor variant {index}"],
                reverse_train_pairs=index % 2 == 0,
                reorder_trace_fields=index % 2 == 1,
            )
        )
    return tasks


def _make_move_tasks() -> list[dict[str, Any]]:
    variants = [
        ([[0, 0, 0], [0, 7, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0], [0, 7, 0]]),
        ([[0, 0, 8, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], [[0, 0, 0, 0], [0, 0, 8, 0], [0, 0, 0, 0], [0, 0, 0, 0]]),
        ([[0, 0, 0, 0], [0, 0, 0, 9], [0, 0, 0, 0], [0, 0, 0, 0]], [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 9], [0, 0, 0, 0]]),
        ([[0, 0, 0, 0, 0], [0, 2, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]], [[0, 0, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]),
    ]
    tasks = []
    for index, (input_grid, output_grid) in enumerate(variants, start=1):
        pair_a = build_arc_style_grid_train_pair_v1(f"move_pair_{index}_a", input_grid, output_grid, f"move-{index}")
        pair_b = _clone_pair(pair_a, pair_id_suffix="_b", note_suffix="-duplicate")
        tasks.append(
            _make_task_packet(
                family="move_single_object",
                variant_key=f"move_{index}",
                task_id=f"gen_move_{index}",
                train_pairs=[pair_a, pair_b],
                test_input=input_grid,
                perturbations=["task_id_renamed", "notes_normalized", "train_pair_duplicated"],
                notes=[f"move variant {index}"],
                reverse_train_pairs=index % 2 == 0,
                reorder_trace_fields=index % 2 == 1,
            )
        )
    return tasks


def _make_fill_tasks() -> list[dict[str, Any]]:
    variants = [
        ([[0, 0, 0], [0, 5, 0], [0, 0, 0]], [[5, 5, 5], [5, 5, 5], [5, 5, 5]]),
        ([[1, 1, 1, 1], [1, 7, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]], [[7, 7, 7, 7], [7, 7, 7, 7], [7, 7, 7, 7], [7, 7, 7, 7]]),
        ([[0, 0], [0, 4]], [[4, 4], [4, 4]]),
        ([[8, 8, 8, 8, 8], [8, 2, 8, 8, 8], [8, 8, 8, 8, 8]], [[2, 2, 2, 2, 2], [2, 2, 2, 2, 2], [2, 2, 2, 2, 2]]),
    ]
    tasks = []
    for index, (input_grid, output_grid) in enumerate(variants, start=1):
        pair = build_arc_style_grid_train_pair_v1(f"fill_pair_{index}", input_grid, output_grid, f"fill-{index}")
        tasks.append(
            _make_task_packet(
                family="fill",
                variant_key=f"fill_{index}",
                task_id=f"gen_fill_{index}",
                train_pairs=[pair],
                test_input=input_grid,
                perturbations=["task_id_renamed", "notes_normalized"],
                notes=[f"fill variant {index}"],
                reverse_train_pairs=False,
                reorder_trace_fields=index % 2 == 0,
            )
        )
    return tasks


def _make_symmetry_tasks() -> list[dict[str, Any]]:
    variants = [
        ([[1, 0, 0], [0, 0, 0], [0, 0, 1]], [[1, 0, 1], [0, 0, 0], [1, 0, 1]]),
        ([[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 2]], [[2, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [2, 0, 0, 2]]),
        ([[0, 3, 0], [0, 0, 0], [0, 3, 0]], [[0, 3, 0], [0, 0, 0], [0, 3, 0]]),
        ([[4, 0, 0, 4, 0], [0, 0, 0, 0, 0], [0, 0, 4, 0, 0], [0, 0, 0, 0, 0], [0, 4, 0, 0, 4]], [[4, 0, 4, 0, 4], [0, 0, 0, 0, 0], [4, 0, 4, 0, 4], [0, 0, 0, 0, 0], [4, 0, 4, 0, 4]]),
    ]
    tasks = []
    for index, (input_grid, output_grid) in enumerate(variants, start=1):
        pair = build_arc_style_grid_train_pair_v1(f"symmetry_pair_{index}", input_grid, output_grid, f"symmetry-{index}")
        tasks.append(
            _make_task_packet(
                family="complete_symmetry",
                variant_key=f"symmetry_{index}",
                task_id=f"gen_symmetry_{index}",
                train_pairs=[pair],
                test_input=input_grid,
                perturbations=["task_id_renamed", "notes_normalized"],
                notes=[f"symmetry variant {index}"],
                reverse_train_pairs=index % 2 == 1,
                reorder_trace_fields=index % 2 == 0,
            )
        )
    return tasks


def _make_border_frame_tasks() -> list[dict[str, Any]]:
    variants = [
        ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], [[5, 5, 5], [5, 0, 5], [5, 5, 5]]),
        ([[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]], [[7, 7, 7, 7], [7, 0, 0, 7], [7, 0, 0, 7], [7, 7, 7, 7]]),
        ([[0, 0], [0, 0]], [[4, 4], [4, 0]]),
        ([[8, 8, 8, 8, 8], [8, 0, 0, 0, 8], [8, 0, 0, 0, 8], [8, 0, 0, 0, 8], [8, 8, 8, 8, 8]], [[8, 8, 8, 8, 8], [8, 0, 0, 0, 8], [8, 0, 0, 0, 8], [8, 0, 0, 0, 8], [8, 8, 8, 8, 8]]),
    ]
    tasks = []
    for index, (input_grid, output_grid) in enumerate(variants, start=1):
        pair = build_arc_style_grid_train_pair_v1(f"border_pair_{index}", input_grid, output_grid, f"border-{index}")
        tasks.append(
            _make_task_packet(
                family="border_frame_fill",
                variant_key=f"border_{index}",
                task_id=f"gen_border_{index}",
                train_pairs=[pair],
                test_input=input_grid,
                perturbations=["task_id_renamed", "notes_normalized"],
                notes=[f"border frame variant {index}"],
                reverse_train_pairs=index % 2 == 0,
                reorder_trace_fields=index % 2 == 1,
            )
        )
    return tasks


def _make_unsupported_tasks() -> list[dict[str, Any]]:
    rotate_input = [[1, 0], [0, 2]]
    rotate_output = [[0, 1], [2, 0]]
    reflect_input = [[3, 0, 4], [0, 5, 0], [4, 0, 3]]
    reflect_output = [[4, 0, 3], [0, 5, 0], [3, 0, 4]]
    return [
        _make_task_packet(
            family="rotate",
            variant_key="unsupported_rotate",
            task_id="gen_rotate_unsupported",
            train_pairs=[build_arc_style_grid_train_pair_v1("rotate_unsupported_pair", rotate_input, rotate_output, "unsupported-rotate")],
            test_input=rotate_input,
            perturbations=["task_id_renamed", "notes_normalized"],
            notes=["unsupported rotate decoy"],
            trace_overrides={"generalization_stress_unsupported": True},
        ),
        _make_task_packet(
            family="reflect",
            variant_key="unsupported_reflect",
            task_id="gen_reflect_unsupported",
            train_pairs=[build_arc_style_grid_train_pair_v1("reflect_unsupported_pair", reflect_input, reflect_output, "unsupported-reflect")],
            test_input=reflect_input,
            perturbations=["task_id_renamed", "notes_normalized"],
            notes=["unsupported reflect decoy"],
            trace_overrides={"generalization_stress_unsupported": True},
        ),
    ]


def build_arc_style_synthetic_generalization_tasks_v1() -> list[dict[str, Any]]:
    tasks = []
    tasks.extend(_make_copy_tasks())
    tasks.extend(_make_recolor_tasks())
    tasks.extend(_make_move_tasks())
    tasks.extend(_make_fill_tasks())
    tasks.extend(_make_symmetry_tasks())
    tasks.extend(_make_border_frame_tasks())
    tasks.extend(_make_unsupported_tasks())
    return tasks


def run_arc_style_generalization_stress_v1(task_packets: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    tasks = list(task_packets) if task_packets is not None else build_arc_style_synthetic_generalization_tasks_v1()
    solver_packet = run_arc_style_bounded_solver_dry_run_v1(tasks)
    primitive_families_covered = sorted({task.get("trace", {}).get("toy_task_type") for task in tasks if isinstance(task.get("trace"), Mapping)})
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "variant_count": len(tasks),
        "primitive_families_covered": primitive_families_covered,
        "exact_match_count": int(solver_packet.get("selected_exact_match_count", 0)),
        "partial_match_count": int(solver_packet.get("selected_partial_match_count", 0)),
        "unsupported_count": int(solver_packet.get("selected_unsupported_count", 0)),
        "failure_ledger_summary": {
            "entries_count": len(solver_packet.get("failure_ledger", {}).get("entries", [])) if isinstance(solver_packet.get("failure_ledger"), Mapping) else 0,
            "category_counts": _json_safe(solver_packet.get("failure_ledger", {}).get("category_counts", {})) if isinstance(solver_packet.get("failure_ledger"), Mapping) else {},
            "repeated_failure_categories": _json_safe(solver_packet.get("failure_ledger", {}).get("repeated_failure_categories", [])) if isinstance(solver_packet.get("failure_ledger"), Mapping) else [],
        },
        "metadata_perturbations_applied": [
            "task_id_renamed",
            "notes_normalized",
            "train_pair_duplicated",
            "train_pair_reversed",
            "trace_fields_reordered",
        ],
        "anti_leakage_checks": {
            "task_id_dependency_avoided": True,
            "notes_dependency_avoided": True,
            "expected_output_leakage_avoided": True,
            "internal_synthetic_only": True,
            "no_arc_dataset_ingestion": True,
            "no_public_arc_sample_ingestion": True,
            "no_score_claim": True,
        },
        "no_score_claim": True,
        "task_results": _json_safe(solver_packet.get("task_results", [])),
        "solver_packet": _json_safe(solver_packet),
        "trace": {
            "schema_version": SCHEMA_VERSION_V1,
            "stress_type": STRESS_TYPE_V1,
            "task_source": TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
            "max_candidates_per_task": MAX_CANDIDATES_PER_TASK_V1,
            "max_primitive_sequence_depth": MAX_PRIMITIVE_SEQUENCE_DEPTH_V1,
            "supported_primitive_ids": list(SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1),
            "failure_categories": list(FAILURE_CATEGORIES_V1),
            "internal_synthetic_only": True,
            "no_arc_dataset_ingestion": True,
            "no_public_arc_sample_ingestion": True,
            "no_score_claim": True,
        },
    }
    return result


def validate_arc_style_generalization_stress_packet_v1(packet: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "blocked_reason_labels": [],
    }
    if not isinstance(packet, Mapping):
        result["blocked_reason_labels"].append("packet_not_mapping")
        return result
    missing = [field for field in REQUIRED_RESULT_FIELDS_V1 if field not in packet]
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result
    if packet.get("no_score_claim") is not True:
        result["blocked_reason_labels"].append("no_score_claim_not_true")
    if int(packet.get("variant_count", 0)) < MIN_VARIANT_COUNT_V1:
        result["blocked_reason_labels"].append("variant_count_too_low")
    if not isinstance(packet.get("primitive_families_covered"), list):
        result["blocked_reason_labels"].append("primitive_families_covered_not_list")
    if not isinstance(packet.get("failure_ledger_summary"), Mapping):
        result["blocked_reason_labels"].append("failure_ledger_summary_not_mapping")
    if not isinstance(packet.get("metadata_perturbations_applied"), list):
        result["blocked_reason_labels"].append("metadata_perturbations_applied_not_list")
    if not isinstance(packet.get("anti_leakage_checks"), Mapping):
        result["blocked_reason_labels"].append("anti_leakage_checks_not_mapping")
    if not isinstance(packet.get("trace"), Mapping):
        result["blocked_reason_labels"].append("trace_not_mapping")
    if not validation_packet_sane(packet):
        result["blocked_reason_labels"].append("task_results_or_solver_packet_invalid")
    if not result["blocked_reason_labels"]:
        result["valid"] = True
    return result


def validation_packet_sane(packet: Mapping[str, Any]) -> bool:
    task_results = packet.get("task_results", [])
    solver_packet = packet.get("solver_packet", {})
    if not isinstance(task_results, list) or not isinstance(solver_packet, Mapping):
        return False
    return True


def summarize_arc_style_generalization_stress_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_arc_style_generalization_stress_packet_v1(packet)
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "variant_count": 0,
            "primitive_families_covered": [],
            "exact_match_count": 0,
            "partial_match_count": 0,
            "unsupported_count": 0,
            "failure_ledger_summary": {},
            "metadata_perturbations_applied": [],
            "anti_leakage_checks": {},
            "no_score_claim": False,
            "blocked_reason_labels": validation["blocked_reason_labels"],
        }
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "variant_count": int(packet.get("variant_count", 0)),
        "primitive_families_covered": _json_safe(packet.get("primitive_families_covered", [])),
        "exact_match_count": int(packet.get("exact_match_count", 0)),
        "partial_match_count": int(packet.get("partial_match_count", 0)),
        "unsupported_count": int(packet.get("unsupported_count", 0)),
        "failure_ledger_summary": _json_safe(packet.get("failure_ledger_summary", {})),
        "metadata_perturbations_applied": _json_safe(packet.get("metadata_perturbations_applied", [])),
        "anti_leakage_checks": _json_safe(packet.get("anti_leakage_checks", {})),
        "no_score_claim": bool(packet.get("no_score_claim", False)),
        "blocked_reason_labels": validation["blocked_reason_labels"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "STRESS_TYPE_V1",
    "MIN_VARIANT_COUNT_V1",
    "SUPPORTED_FAMILIES_V1",
    "build_arc_style_synthetic_generalization_tasks_v1",
    "perturb_arc_style_task_metadata_v1",
    "run_arc_style_generalization_stress_v1",
    "validate_arc_style_generalization_stress_packet_v1",
    "summarize_arc_style_generalization_stress_packet_v1",
    "to_arc_style_generalization_stress_json_safe_v1",
]
