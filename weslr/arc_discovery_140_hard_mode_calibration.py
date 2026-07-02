"""ARC Synthetic Discovery 140 — Hard Mode Calibration Layer (V1).

This module is a separate calibration layer that stresses the current 140-base
assumptions without changing the clean 130/130 regression gate.

It is metadata-only: it builds hard-mode task packets and measures them with the
same oracle/solver comparison style used by the 140 semantic pilot.
It does NOT change BH80, promotion rules, solver behavior, oracle behavior,
scorer behavior, runtime/chat/UI/provider paths, or `.weslr`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from weslr.arc_discovery_140_semantic_pilot import (
    combined_oracle_pipeline,
    combined_solver_pipeline,
    run_140_semantic_pilot,
)
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_bh80_semantic_scorer import grids_equal

SCORING_LAYER = "hard_mode_scored"
HARD_MODE_TASK_COUNT = 30
HARD_MODE_GATES = {
    "clean": 30,
    "preferred": 27,
    "strong": 24,
    "minimal": 20,
    "total": 30,
}
HARD_MODE_AXES = (
    "object_ambiguity",
    "color_ambiguity",
    "connected_component_ambiguity",
    "distractor_density",
    "symmetry_trap",
    "largest_object_trap",
    "leftmost_topmost_trap",
    "same_color_multi_object_trap",
    "diagonal_adjacency_trap",
    "hole_topology_trap",
    "relation_swap_ambiguity",
    "order_sensitivity",
    "primitive_chain_deception",
    "output_dimension_change",
    "unseen_composition",
    "rival_grammar_ambiguity",
)


def _obj(object_id: str, kind: str, color: int, position: list[int], size: list[int]) -> dict:
    return {
        "object_id": object_id,
        "type": kind,
        "attributes": {
            "color": color,
            "position": position,
            "size": size,
        },
    }


def _rect(object_id: str, color: int, position: list[int], size: list[int]) -> dict:
    return _obj(object_id, "rectangle", color, position, size)


def _donut(object_id: str, color: int, position: list[int], size: list[int]) -> dict:
    return _obj(object_id, "donut", color, position, size)


def _cross(object_id: str, color: int, position: list[int], size: list[int]) -> dict:
    return _obj(object_id, "cross", color, position, size)


def _lshape(object_id: str, color: int, position: list[int], size: list[int]) -> dict:
    return _obj(object_id, "l_shape", color, position, size)


def _disconnected(object_id: str, color: int, position: list[int], size: list[int]) -> dict:
    return _obj(object_id, "disconnected", color, position, size)


def _scene(
    grid_size: list[int],
    initial_objects: list[dict],
    distractors: list[dict] | None = None,
    noise_pixels: int = 0,
    background: int = 0,
) -> dict:
    return {
        "grid_size": grid_size,
        "background": background,
        "initial_objects": initial_objects,
        "distractors": distractors or [],
        "noise_pixels": noise_pixels,
    }


def _make_task(
    task_id: str,
    primitive_sequence: list[str],
    scene_spec: dict,
    family_id: str,
    hard_mode_axes: list[str],
    not_bh80_duplicate: str,
    expected_failure_categories: list[str],
    hard_mode_note: str,
    scoring_layer: str = SCORING_LAYER,
) -> dict:
    task: dict[str, Any] = {
        "task_id": task_id,
        "family_id": family_id,
        "difficulty": "hard",
        "primitive_sequence": list(primitive_sequence),
        "scene_spec": scene_spec,
        "train_pair_count": 1,
        "test_input_count": 1,
        "hardness_axes": list(hard_mode_axes),
        "shortcut_defeated": "None",
        "expected_trace_requirements": {},
        "allowed_dynamic_parameters": [],
        "forbidden_shortcuts": [
            "expected_test_output",
            "task_id_shortcut",
            "generator_note_shortcut",
        ],
        "leakage_flags": {
            "arc_agi_participation_claim": False,
            "leaderboard_claim": False,
            "hidden_test_use": False,
            "public_claim": False,
            "final_answer_wiring": False,
            "weslr_persistence": False,
            "external_calls": False,
            "provider_model_calls": False,
            "runtime_chat_wiring": False,
        },
        "expected_failure_categories": list(expected_failure_categories),
        "scoring_layer": scoring_layer,
        "not_bh80_duplicate": not_bh80_duplicate,
        "anti_cheat_expectation": hard_mode_note,
        "hard_mode": True,
        "hard_mode_family": family_id,
        "hard_mode_note": hard_mode_note,
    }
    return task


HARD_MODE_TASK_SPECS = [
    # Supported / pressure-heavy tasks
    (
        "T140H_001",
        ["extract", "sel_leftmost", "recolor"],
        _scene([8, 8], [_rect("o1", 1, [1, 1], [2, 2]), _rect("o2", 1, [1, 4], [2, 2])], [_rect("d1", 6, [6, 6], [1, 1])]),
        "object_ambiguity",
        ["object_ambiguity", "same_color_multi_object_trap", "leftmost_topmost_trap"],
        "same-color multi-object selection pressure",
        ["identity_by_color", "selection_order_bias"],
    ),
    (
        "T140H_002",
        ["isolate_largest", "mask_complement", "normalize_position"],
        _scene([10, 10], [_donut("o1", 3, [1, 1], [6, 6]), _rect("o2", 5, [7, 7], [2, 2])], [_rect("d1", 8, [0, 8], [1, 2])]),
        "largest_object_trap",
        ["largest_object_trap", "hole_topology_trap"],
        "largest-object with hollow topology pressure",
        ["hollow_vs_solid", "largest_selection_bias"],
    ),
    (
        "T140H_003",
        ["mirror_object", "constr_draw_rect_around", "recolor_boundary"],
        _scene([10, 10], [_lshape("o1", 2, [2, 2], [3, 3]), _rect("o2", 4, [6, 6], [2, 2])], []),
        "symmetry_trap",
        ["symmetry_trap", "rival_grammar_ambiguity"],
        "mirror-vs-outline symmetry pressure",
        ["symmetry_confusion"],
    ),
    (
        "T140H_004",
        ["extract_boundary", "mask_complement", "count"],
        _scene([8, 8], [_disconnected("o1", 1, [1, 1], [4, 4]), _rect("o2", 7, [5, 5], [2, 2])], []),
        "connected_component_ambiguity",
        ["connected_component_ambiguity", "diagonal_adjacency_trap"],
        "diagonal and split-component pressure",
        ["cc_boundary_confusion"],
    ),
    (
        "T140H_005",
        ["topo_fill_holes", "recolor_boundary", "extract"],
        _scene([10, 10], [_donut("o1", 2, [1, 1], [6, 6]), _rect("o2", 5, [7, 7], [2, 2])], [_rect("d1", 8, [0, 0], [1, 1])]),
        "hole_topology_trap",
        ["hole_topology_trap", "object_ambiguity"],
        "hollow-object hole fill pressure",
        ["hole_detection_bias"],
    ),
    (
        "T140H_006",
        ["rel_swap_positions", "constr_draw_rect_around", "recolor"],
        _scene([12, 12], [_rect("o1", 4, [1, 1], [2, 2]), _rect("o2", 5, [6, 6], [2, 2])], [_rect("d1", 7, [3, 9], [1, 1])]),
        "relation_swap_ambiguity",
        ["relation_swap_ambiguity", "order_sensitivity"],
        "relative-placement swap pressure",
        ["relative_order_confusion"],
    ),
    (
        "T140H_007",
        ["constr_copy_to_pos", "normalize_position", "crop"],
        _scene([10, 10], [_rect("o1", 1, [2, 2], [3, 4]), _rect("o2", 6, [7, 1], [2, 2])], [_rect("d1", 8, [0, 8], [1, 1])]),
        "output_dimension_change",
        ["output_dimension_change", "unseen_composition"],
        "copy-and-reframe output-shape pressure",
        ["dimension_shift_confusion"],
    ),
    (
        "T140H_008",
        ["color_swap_1_2", "extract", "mask_complement"],
        _scene([8, 8], [_rect("o1", 1, [1, 1], [2, 2]), _rect("o2", 2, [1, 4], [2, 2]), _rect("o3", 1, [4, 2], [2, 2])], []),
        "same_color_multi_object_trap",
        ["same_color_multi_object_trap", "color_ambiguity"],
        "same-color multi-object pressure",
        ["color_identity_confusion"],
    ),
    (
        "T140H_009",
        ["remove_noise", "sel_leftmost", "recolor"],
        _scene([10, 10], [_rect("o1", 3, [2, 2], [2, 2]), _rect("o2", 3, [2, 6], [2, 2])], [_rect("d1", 9, [0, 0], [1, 1]), _rect("d2", 8, [9, 9], [1, 1])], noise_pixels=2),
        "distractor_density",
        ["distractor_density", "leftmost_topmost_trap"],
        "noise-heavy leftmost selection pressure",
        ["distractor_blindness"],
    ),
    (
        "T140H_010",
        ["color_invert", "mask_complement", "recolor"],
        _scene([10, 10], [_cross("o1", 2, [3, 3], [3, 3]), _rect("o2", 5, [0, 7], [2, 2])], []),
        "primitive_chain_deception",
        ["primitive_chain_deception", "rival_grammar_ambiguity"],
        "chain-deception with dual native transforms",
        ["chain_order_confusion"],
    ),
    (
        "T140H_011",
        ["sel_leftmost", "rotate", "recolor_boundary"],
        _scene([8, 8], [_rect("o1", 4, [1, 1], [2, 2]), _rect("o2", 4, [1, 4], [2, 2]), _rect("o3", 7, [4, 1], [2, 2])], []),
        "leftmost_topmost_trap",
        ["leftmost_topmost_trap", "same_color_multi_object_trap"],
        "row/column tie-break pressure",
        ["spatial_tiebreak_confusion"],
    ),
    (
        "T140H_012",
        ["normalize_position", "rel_swap_positions", "rotate"],
        _scene([12, 12], [_rect("o1", 2, [1, 1], [2, 2]), _rect("o2", 5, [7, 7], [2, 2])], [_rect("d1", 6, [11, 0], [1, 1])]),
        "order_sensitivity",
        ["order_sensitivity", "relation_swap_ambiguity"],
        "transform-order pressure",
        ["chain_reversal_bias"],
    ),
    (
        "T140H_013",
        ["fill_region", "topo_fill_holes", "normalize_position"],
        _scene([10, 10], [_donut("o1", 1, [1, 1], [6, 6]), _rect("o2", 4, [7, 7], [2, 2])], []),
        "hole_topology_trap",
        ["hole_topology_trap", "unseen_composition"],
        "fill-and-normalize hole topology pressure",
        ["interior_boundary_confusion"],
    ),
    (
        "T140H_014",
        ["mirror_object", "color_swap_1_2", "sel_leftmost"],
        _scene([10, 10], [_lshape("o1", 1, [2, 2], [3, 3]), _rect("o2", 2, [2, 6], [2, 2])], [_rect("d1", 7, [0, 9], [1, 1])]),
        "symmetry_trap",
        ["symmetry_trap", "color_ambiguity"],
        "mirror plus recolor ambiguity",
        ["symmetry_color_confusion"],
    ),
    (
        "T140H_015",
        ["remove_noise", "topo_fill_holes", "mask_complement"],
        _scene([12, 12], [_donut("o1", 3, [2, 2], [6, 6])], [_rect("d1", 8, [0, 0], [1, 1]), _rect("d2", 7, [11, 11], [1, 1])], noise_pixels=2),
        "distractor_density",
        ["distractor_density", "hole_topology_trap"],
        "noise plus topology pressure",
        ["noise_blindness"],
    ),
    (
        "T140H_016",
        ["rel_swap_positions", "extract_boundary", "normalize_position"],
        _scene([10, 10], [_disconnected("o1", 4, [1, 1], [4, 4]), _rect("o2", 5, [6, 1], [2, 2])], []),
        "connected_component_ambiguity",
        ["connected_component_ambiguity", "relation_swap_ambiguity"],
        "swap over split-component pressure",
        ["cc_swap_confusion"],
    ),
    (
        "T140H_017",
        ["isolate_largest", "constr_draw_rect_around", "count"],
        _scene([10, 10], [_donut("o1", 2, [1, 1], [6, 6]), _rect("o2", 2, [7, 7], [2, 2]), _rect("o3", 5, [0, 8], [1, 2])], []),
        "largest_object_trap",
        ["largest_object_trap", "same_color_multi_object_trap"],
        "largest-object plus duplicate-color pressure",
        ["largest_selection_confusion"],
    ),
    (
        "T140H_018",
        ["mask_complement", "color_invert", "extract"],
        _scene([8, 8], [_cross("o1", 2, [2, 2], [3, 3]), _rect("o2", 2, [4, 4], [2, 2])], []),
        "primitive_chain_deception",
        ["primitive_chain_deception", "rival_grammar_ambiguity"],
        "dual-complement visual trap",
        ["transform_order_confusion"],
    ),
    (
        "T140H_019",
        ["sel_leftmost", "constr_draw_rect_around", "normalize_position"],
        _scene([10, 10], [_rect("o1", 1, [1, 1], [2, 2]), _rect("o2", 1, [1, 5], [2, 2]), _rect("o3", 3, [6, 3], [2, 2])], []),
        "same_color_multi_object_trap",
        ["same_color_multi_object_trap", "leftmost_topmost_trap"],
        "same-color row/column ambiguity",
        ["identity_and_position_confusion"],
    ),
    (
        "T140H_020",
        ["cond_if_holes_fill", "extract_boundary", "place_back"],
        _scene([12, 12], [_donut("o1", 1, [2, 2], [6, 6]), _rect("o2", 5, [8, 8], [2, 2])], [_rect("d1", 7, [0, 10], [1, 1])]),
        "output_dimension_change",
        ["output_dimension_change", "hole_topology_trap"],
        "conditional hole-fill with reinsert pressure",
        ["dimension_reinsertion_confusion"],
    ),
    # Candidate / currently-unpromoted stress tasks
    (
        "T140H_021",
        ["geom_scale_2x", "recolor", "crop"],
        _scene([8, 8], [_rect("o1", 1, [1, 1], [2, 2]), _rect("o2", 4, [4, 4], [2, 2])], [_rect("d1", 7, [0, 6], [1, 2])]),
        "rival_grammar_ambiguity",
        ["output_dimension_change", "rival_grammar_ambiguity"],
        "geometry-scale candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_022",
        ["topo_merge_objects", "extract", "recolor"],
        _scene([10, 10], [_rect("o1", 2, [1, 1], [2, 2]), _rect("o2", 2, [1, 4], [2, 2]), _rect("o3", 5, [6, 6], [2, 2])], []),
        "connected_component_ambiguity",
        ["connected_component_ambiguity", "same_color_multi_object_trap"],
        "merge-object candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_023",
        ["constr_connect_line", "normalize_position", "count"],
        _scene([12, 12], [_rect("o1", 3, [1, 1], [2, 2]), _rect("o2", 4, [8, 8], [2, 2])], [_rect("d1", 6, [0, 10], [1, 1])]),
        "distractor_density",
        ["distractor_density", "connected_component_ambiguity"],
        "connect-line candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_024",
        ["constr_copy_to_pos", "rotate", "recolor"],
        _scene([10, 10], [_rect("o1", 1, [2, 2], [2, 2]), _rect("o2", 5, [6, 1], [3, 2])], [_rect("d1", 4, [8, 8], [1, 1])]),
        "output_dimension_change",
        ["output_dimension_change", "unseen_composition"],
        "copy-to-pos candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_025",
        ["pat_color_cycle", "extract", "mask_complement"],
        _scene([8, 8], [_rect("o1", 1, [1, 1], [4, 2]), _rect("o2", 2, [4, 1], [2, 4])], []),
        "rival_grammar_ambiguity",
        ["rival_grammar_ambiguity", "primitive_chain_deception"],
        "pattern-cycle candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_026",
        ["cond_if_edge_clip", "recolor_boundary", "place_back"],
        _scene([10, 10], [_rect("o1", 2, [0, 2], [3, 3]), _rect("o2", 6, [6, 6], [3, 3])], [_rect("d1", 7, [9, 0], [1, 1])]),
        "diagonal_adjacency_trap",
        ["diagonal_adjacency_trap", "output_dimension_change"],
        "edge-clip candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_027",
        ["topo_split_at_gap", "recolor", "count"],
        _scene([12, 12], [_rect("o1", 1, [2, 2], [2, 2]), _rect("o2", 1, [2, 5], [2, 2]), _rect("o3", 1, [2, 8], [2, 2])], []),
        "hole_topology_trap",
        ["hole_topology_trap", "connected_component_ambiguity"],
        "gap-identification candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_028",
        ["geom_scale_2x", "topo_merge_objects", "crop"],
        _scene([8, 8], [_donut("o1", 2, [1, 1], [4, 4]), _rect("o2", 5, [4, 4], [2, 2])], []),
        "rival_grammar_ambiguity",
        ["output_dimension_change", "connected_component_ambiguity"],
        "geometry + merge candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_029",
        ["constr_connect_line", "cond_if_edge_clip", "rotate"],
        _scene([10, 10], [_rect("o1", 4, [1, 1], [2, 2]), _rect("o2", 4, [1, 5], [2, 2]), _rect("o3", 7, [6, 6], [2, 2])], []),
        "connected_component_ambiguity",
        ["connected_component_ambiguity", "diagonal_adjacency_trap"],
        "line-then-clip candidate pressure",
        ["unsupported_primitives"],
    ),
    (
        "T140H_030",
        ["pat_color_cycle", "topo_split_at_gap", "normalize_position"],
        _scene([12, 12], [_cross("o1", 1, [2, 2], [3, 3]), _rect("o2", 4, [7, 7], [2, 2])], [_rect("d1", 8, [0, 11], [1, 1])]),
        "primitive_chain_deception",
        ["primitive_chain_deception", "rival_grammar_ambiguity"],
        "pattern-cycle plus gap split candidate pressure",
        ["unsupported_primitives"],
    ),
]


def generate_hard_mode_calibration_tasks() -> list[dict]:
    tasks = [
        _make_task(
            task_id=task_id,
            primitive_sequence=primitive_sequence,
            scene_spec=scene_spec,
            family_id=family_id,
            hard_mode_axes=axes,
            not_bh80_duplicate=note,
            expected_failure_categories=failures,
            hard_mode_note=note,
        )
        for (
            task_id,
            primitive_sequence,
            scene_spec,
            family_id,
            axes,
            note,
            failures,
        ) in HARD_MODE_TASK_SPECS
    ]
    assert len(tasks) == HARD_MODE_TASK_COUNT, f"Expected {HARD_MODE_TASK_COUNT} tasks, got {len(tasks)}"
    assert len({t["task_id"] for t in tasks}) == HARD_MODE_TASK_COUNT, "Duplicate task_id detected"
    return tasks


def get_hard_mode_tasks(tasks: list[dict]) -> list[dict]:
    return [t for t in tasks if t.get("hard_mode") is True]


def get_hard_mode_summary(tasks: list[dict]) -> dict:
    hard_mode_tasks = get_hard_mode_tasks(tasks)
    return {
        "total_tasks": len(tasks),
        "hard_mode_total": len(hard_mode_tasks),
        "hard_mode_scored_total": sum(1 for t in hard_mode_tasks if t.get("scoring_layer") == SCORING_LAYER),
        "candidate_probe_total": sum(1 for t in hard_mode_tasks if t.get("scoring_layer") != SCORING_LAYER),
        "family_counts": {
            family: sum(1 for t in hard_mode_tasks if t.get("family_id") == family)
            for family in sorted({t.get("family_id") for t in hard_mode_tasks})
        },
        "axis_counts": {
            axis: sum(1 for t in hard_mode_tasks if axis in t.get("hardness_axes", []))
            for axis in HARD_MODE_AXES
        },
        "hard_mode_denominator": len(hard_mode_tasks),
        "hard_mode_counted_as_solved": 0,
    }


def score_single_hard_mode_task(task: dict) -> dict:
    task_id = task["task_id"]
    scene_spec = task["scene_spec"]
    prims = task["primitive_sequence"]

    input_grid = materialize_scene(scene_spec, task_id)
    oracle_supported, oracle_grid, oracle_traces = combined_oracle_pipeline(prims, input_grid)
    solver_supported, solver_grid = combined_solver_pipeline(input_grid, prims)

    if not solver_supported:
        result = "unsupported"
    elif solver_grid is None:
        result = "failed"
    elif oracle_supported and grids_equal(solver_grid, oracle_grid):
        result = "semantic_exact"
    else:
        result = "failed"

    return {
        "task_id": task_id,
        "family_id": task.get("family_id"),
        "result": result,
        "solver_supported": solver_supported,
        "oracle_supported": oracle_supported,
        "grids_equal": grids_equal(solver_grid, oracle_grid) if (solver_supported and oracle_supported and solver_grid is not None) else False,
        "primitive_sequence": prims,
        "oracle_traces": oracle_traces,
        "hard_mode_axes": task.get("hardness_axes", []),
        "expected_failure_categories": task.get("expected_failure_categories", []),
    }


def run_hard_mode_semantic_pilot() -> dict:
    base_140 = run_140_semantic_pilot()
    tasks = generate_hard_mode_calibration_tasks()
    summary = get_hard_mode_summary(tasks)
    task_results = [score_single_hard_mode_task(task) for task in tasks]

    exact = sum(1 for r in task_results if r["result"] == "semantic_exact")
    failed = sum(1 for r in task_results if r["result"] == "failed")
    unsupported = sum(1 for r in task_results if r["result"] == "unsupported")
    structural_pass = sum(1 for r in task_results if r["result"] != "failed")

    failure_category_counts: dict[str, int] = {}
    for r in task_results:
        for category in r.get("expected_failure_categories", []):
            failure_category_counts[category] = failure_category_counts.get(category, 0) + 1

    hard_mode_exact_rate = round((exact / summary["hard_mode_denominator"] * 100) if summary["hard_mode_denominator"] else 0, 2)
    hard_mode_band = (
        "clean" if exact == summary["hard_mode_denominator"] else
        "strong" if exact >= HARD_MODE_GATES["strong"] else
        "preferred" if exact >= HARD_MODE_GATES["preferred"] else
        "minimal" if exact >= HARD_MODE_GATES["minimal"] else
        "weak"
    )

    return {
        "base_140_reference": {
            "scored_total": base_140["summary"]["scored_total"],
            "scored_exact": base_140["scored_aggregate"]["scored_exact"],
            "bh80_exact": base_140["bh80_subset"]["semantic_exact"],
            "previous_117_exact": base_140["previous_117_scored_base"]["semantic_exact"],
            "new_13_exact": base_140["new_13_scored_expansion"]["semantic_exact"],
            "candidate_probe_counted_as_solved": base_140["candidate_probe_diagnostics"]["candidate_probe_counted_as_solved"],
            "base_130_preserved": base_140["scored_aggregate"]["scored_exact"] == 130,
            "bh80_80_preserved": base_140["bh80_subset"]["semantic_exact"] == 80,
            "previous_117_preserved": base_140["previous_117_scored_base"]["semantic_exact"] == 117,
            "candidate_probes_counted_as_solved_zero": base_140["candidate_probe_diagnostics"]["candidate_probe_counted_as_solved"] == 0,
        },
        "hard_mode_summary": summary,
        "hard_mode_aggregate": {
            "hard_mode_total": summary["hard_mode_denominator"],
            "hard_mode_scored_total": summary["hard_mode_scored_total"],
            "hard_mode_exact": exact,
            "hard_mode_failed": failed,
            "hard_mode_unsupported": unsupported,
            "hard_mode_structural_pass": structural_pass,
            "hard_mode_exact_rate": hard_mode_exact_rate,
            "hard_mode_band": hard_mode_band,
        },
        "gate_results": {
            "hard_mode_clean": exact == HARD_MODE_GATES["clean"],
            "hard_mode_preferred": exact >= HARD_MODE_GATES["preferred"],
            "hard_mode_strong": exact >= HARD_MODE_GATES["strong"],
            "hard_mode_minimal": exact >= HARD_MODE_GATES["minimal"],
            "base_130_preserved": base_140["scored_aggregate"]["scored_exact"] == 130,
            "bh80_80_preserved": base_140["bh80_subset"]["semantic_exact"] == 80,
            "previous_117_preserved": base_140["previous_117_scored_base"]["semantic_exact"] == 117,
            "candidate_probes_counted_as_solved_zero": base_140["candidate_probe_diagnostics"]["candidate_probe_counted_as_solved"] == 0,
        },
        "failure_category_counts": failure_category_counts,
        "task_results": task_results,
        "task_count": len(tasks),
    }


if __name__ == "__main__":
    results = run_hard_mode_semantic_pilot()
    base = results["base_140_reference"]
    hard = results["hard_mode_aggregate"]
    gates = results["gate_results"]

    print("Running ARC Synthetic Discovery 140 Hard Mode Calibration Pilot...")
    print()
    print("BASE 140 REFERENCE")
    print(f"  scored_total:                 {base['scored_total']}")
    print(f"  scored_exact:                 {base['scored_exact']}")
    print(f"  bh80_exact:                   {base['bh80_exact']}")
    print(f"  previous_117_exact:           {base['previous_117_exact']}")
    print(f"  new_13_exact:                 {base['new_13_exact']}")
    print(f"  candidate_probe_solved:       {base['candidate_probe_counted_as_solved']}")
    print()
    print("HARD MODE")
    print(f"  hard_mode_total:              {hard['hard_mode_total']}")
    print(f"  hard_mode_scored_total:       {hard['hard_mode_scored_total']}")
    print(f"  hard_mode_exact:              {hard['hard_mode_exact']}")
    print(f"  hard_mode_failed:             {hard['hard_mode_failed']}")
    print(f"  hard_mode_unsupported:        {hard['hard_mode_unsupported']}")
    print(f"  hard_mode_structural_pass:    {hard['hard_mode_structural_pass']}")
    print(f"  hard_mode_exact_rate:         {hard['hard_mode_exact_rate']}%")
    print(f"  hard_mode_band:               {hard['hard_mode_band']}")
    print()
    print("GATES")
    for key, value in gates.items():
        print(f"  {key}: {value}")
    print()
    print("HARD MODE CALIBRATION COMPLETE")
