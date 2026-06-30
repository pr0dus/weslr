"""WESLR ARC-style synthetic 2-step 40-task pilot runner V1.

Design-constrained diagnostic scaffold for a deterministic 40-task synthetic
2-step ARC-style pilot. This module is measurement-only and intentionally does
not modify solver inference logic, single-step runner behavior, candidate output
surfaces, replay/scoring/final-answer behavior, public ARC/Kaggle participation,
or `.weslr` state.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
from typing import Any, Mapping, Sequence

from weslr.arc_style_grid_generalization_stress import perturb_arc_style_task_metadata_v1
from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_task_packet_v1, build_arc_style_grid_train_pair_v1
from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_style_synthetic_solver_suite import (
    DEFAULT_DENIED_AUTHORITY_V1,
    _build_packet_result,
    _normalize_leakage_flags,
    _safe_text,
    build_arc_style_synthetic_solver_failure_ledger_v1,
)

SCHEMA_VERSION_V1 = "ArcStyleSynthetic2StepPilotRunnerV1"
RUNNER_ID_V1 = "arc_style_synthetic_2_step_40_pilot_runner_v1"
RUNNER_ENTRY_POINT_V1 = "weslr.arc_style_synthetic_2_step_pilot_runner.run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1"
RUNNER_ID_80_V1 = "arc_style_synthetic_2_step_80_pilot_runner_v1"
RUNNER_ENTRY_POINT_80_V1 = "weslr.arc_style_synthetic_2_step_pilot_runner.run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1"
TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1 = "internal_synthetic_2_step_pilot_v1"
PILOT_TASK_COUNT_V1 = 40
EXPANDED_PILOT_TASK_COUNT_V1 = 80
TRAIN_PAIR_COUNT_V1 = 2
TEST_INPUT_COUNT_V1 = 1
MODE_ORDER_V1 = (
    "full_metadata",
    "toy_task_type_preserved_guardrail",
    "fully_stripped_lower_bound",
    "shuffled_renamed",
)
FAILURE_TAXONOMY_V1 = (
    "right_primitives_wrong_order",
    "first_step_correct_second_wrong",
    "first_step_wrong_second_correct",
    "one_primitive_missing",
    "parameter_carryover_failure",
    "intermediate_execution_failure",
    "sequence_not_generated",
)
EXPECTED_STATUS_KEYS_V1 = ("exact", "partial", "unsupported", "failed")
MAX_SEQUENCE_CANDIDATES_PER_TASK_V1 = 2
MAX_SEQUENCE_LENGTH_V1 = 2


EASY_TASK_SPECS_V1 = (
    ("pilot_2_step_easy_01_remove_noise_then_extract_v1", "easy", ("remove_background_noise", "extract_largest_object"), "noise_extract"),
    ("pilot_2_step_easy_02_remove_noise_then_recolor_v1", "easy", ("remove_background_noise", "recolor_symbol"), "noise_recolor"),
    ("pilot_2_step_easy_03_extract_then_recolor_v1", "easy", ("extract_largest_object", "recolor_symbol"), "extract_recolor"),
    ("pilot_2_step_easy_04_move_then_border_v1", "easy", ("move_single_object", "border_frame"), "move_border"),
    ("pilot_2_step_easy_05_copy_then_recolor_v1", "easy", ("copy_grid", "recolor_symbol"), "copy_recolor"),
    ("pilot_2_step_easy_06_copy_then_border_v1", "easy", ("copy_grid", "border_frame"), "copy_border"),
    ("pilot_2_step_easy_07_fill_then_recolor_v1", "easy", ("fill_region", "recolor_symbol"), "fill_recolor"),
    ("pilot_2_step_easy_08_fill_then_line_v1", "easy", ("fill_region", "line_completion"), "fill_line"),
    ("pilot_2_step_easy_09_symmetry_then_recolor_v1", "easy", ("complete_symmetry", "recolor_symbol"), "symmetry_recolor"),
    ("pilot_2_step_easy_10_count_then_border_v1", "easy", ("object_count_to_pattern", "border_frame"), "count_border"),
    ("pilot_2_step_easy_11_line_then_recolor_v1", "easy", ("line_completion", "recolor_symbol"), "line_recolor"),
    ("pilot_2_step_easy_12_recolor_then_border_v1", "easy", ("recolor_symbol", "border_frame"), "recolor_border"),
    ("pilot_2_step_easy_13_extract_then_border_v1", "easy", ("extract_largest_object", "border_frame"), "extract_border"),
    ("pilot_2_step_easy_14_remove_noise_then_border_v1", "easy", ("remove_background_noise", "border_frame"), "noise_border"),
    ("pilot_2_step_easy_15_move_then_recolor_v1", "easy", ("move_single_object", "recolor_symbol"), "move_recolor"),
    ("pilot_2_step_easy_16_symmetry_then_border_v1", "easy", ("complete_symmetry", "border_frame"), "symmetry_border"),
    ("pilot_2_step_easy_17_copy_then_line_v1", "easy", ("copy_grid", "line_completion"), "copy_line"),
    ("pilot_2_step_easy_18_fill_then_border_v1", "easy", ("fill_region", "border_frame"), "fill_border"),
    ("pilot_2_step_easy_19_line_then_border_v1", "easy", ("line_completion", "border_frame"), "line_border"),
    ("pilot_2_step_easy_20_extract_then_symmetry_v1", "easy", ("extract_largest_object", "complete_symmetry"), "extract_symmetry"),
)

MEDIUM_TASK_SPECS_V1 = (
    ("pilot_2_step_medium_01_rotate_then_recolor_v1", "medium", ("rotate_object_90", "recolor_symbol"), "rotate_recolor"),
    ("pilot_2_step_medium_02_reflect_then_move_v1", "medium", ("reflect_object_horizontal_or_vertical", "move_single_object"), "reflect_move"),
    ("pilot_2_step_medium_03_rotate_then_reflect_v1", "medium", ("rotate_object_90", "reflect_object_horizontal_or_vertical"), "rotate_reflect"),
    ("pilot_2_step_medium_04_reflect_then_recolor_v1", "medium", ("reflect_object_horizontal_or_vertical", "recolor_symbol"), "reflect_recolor"),
    ("pilot_2_step_medium_05_remove_noise_then_count_v1", "medium", ("remove_background_noise", "object_count_to_pattern"), "noise_count"),
    ("pilot_2_step_medium_06_extract_then_count_v1", "medium", ("extract_largest_object", "object_count_to_pattern"), "extract_count"),
    ("pilot_2_step_medium_07_symmetry_then_line_v1", "medium", ("complete_symmetry", "line_completion"), "symmetry_line"),
    ("pilot_2_step_medium_08_move_then_symmetry_v1", "medium", ("move_single_object", "complete_symmetry"), "move_symmetry"),
    ("pilot_2_step_medium_09_fill_then_symmetry_v1", "medium", ("fill_region", "complete_symmetry"), "fill_symmetry"),
    ("pilot_2_step_medium_10_count_then_recolor_v1", "medium", ("object_count_to_pattern", "recolor_symbol"), "count_recolor"),
)

STRESS_TASK_SPECS_V1 = (
    ("pilot_2_step_stress_01_rotate_then_border_v1", "stress", ("rotate_object_90", "border_frame"), "rotate_border"),
    ("pilot_2_step_stress_02_reflect_then_border_v1", "stress", ("reflect_object_horizontal_or_vertical", "border_frame"), "reflect_border"),
    ("pilot_2_step_stress_03_rotate_then_move_v1", "stress", ("rotate_object_90", "move_single_object"), "rotate_move"),
    ("pilot_2_step_stress_04_reflect_then_symmetry_v1", "stress", ("reflect_object_horizontal_or_vertical", "complete_symmetry"), "reflect_symmetry"),
    ("pilot_2_step_stress_05_remove_noise_then_symmetry_v1", "stress", ("remove_background_noise", "complete_symmetry"), "noise_symmetry"),
    ("pilot_2_step_stress_06_extract_then_line_v1", "stress", ("extract_largest_object", "line_completion"), "extract_line"),
    ("pilot_2_step_stress_07_count_then_line_v1", "stress", ("object_count_to_pattern", "line_completion"), "count_line"),
    ("pilot_2_step_stress_08_fill_then_count_v1", "stress", ("fill_region", "object_count_to_pattern"), "fill_count"),
    ("pilot_2_step_stress_09_symmetry_then_count_v1", "stress", ("complete_symmetry", "object_count_to_pattern"), "symmetry_count"),
    ("pilot_2_step_stress_10_move_then_reflect_v1", "stress", ("move_single_object", "reflect_object_horizontal_or_vertical"), "move_reflect"),
)

TASK_SPECS_V1 = EASY_TASK_SPECS_V1 + MEDIUM_TASK_SPECS_V1 + STRESS_TASK_SPECS_V1

KNOWN_STRESS_RESIDUAL_TASK_IDS_V1 = {"pilot_2_step_stress_08_fill_then_count_v1"}

EXPANSION_TASK_SPECS_V1 = (
    ("pilot_2_step_easy_gen_01_noise_extract_large_v1", "easy", ("remove_background_noise", "extract_largest_object"), "noise_extract", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "noise_cells": [(0, 0), (6, 6)]}, "generalization"),
    ("pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1", "easy", ("remove_background_noise", "recolor_symbol"), "noise_recolor", {"source_color": 4, "target_color": 8, "noise_color": 9, "noise_cells": [(0, 6), (6, 0)]}, "generalization"),
    ("pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1", "easy", ("extract_largest_object", "recolor_symbol"), "extract_recolor", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 4, "target_color": 9, "small_cells": [(0, 0), (6, 6)]}, "generalization"),
    ("pilot_2_step_easy_gen_04_move_border_two_steps_v1", "easy", ("move_single_object", "border_frame"), "move_border", {"direction": "down", "steps": 2, "object_color": 5, "frame_color": 7}, "generalization"),
    ("pilot_2_step_easy_gen_05_copy_recolor_alt_shape_v1", "easy", ("copy_grid", "recolor_symbol"), "copy_recolor", {"shape": "domino_v", "source_color": 5, "target_color": 8}, "generalization"),
    ("pilot_2_step_easy_gen_06_copy_border_large_grid_v1", "easy", ("copy_grid", "border_frame"), "copy_border", {"rows": 7, "cols": 7, "shape": "domino_h", "object_color": 4, "frame_color": 9}, "generalization"),
    ("pilot_2_step_easy_gen_07_fill_recolor_alt_colors_v1", "easy", ("fill_region", "recolor_symbol"), "fill_recolor", {"rows": 7, "cols": 7, "border_color": 5, "fill_color": 2, "target_color": 8}, "generalization"),
    ("pilot_2_step_easy_gen_08_symmetry_recolor_alt_seed_v1", "easy", ("complete_symmetry", "recolor_symbol"), "symmetry_recolor", {"rows": 7, "cols": 7, "source_color": 3, "target_color": 8, "seed_cells": [(0, 2), (6, 4)]}, "generalization"),
    ("pilot_2_step_easy_gen_09_count_border_four_objects_v1", "easy", ("object_count_to_pattern", "border_frame"), "count_border", {"rows": 7, "cols": 7, "count": 4, "row_index": 4, "pattern_color": 6, "frame_color": 9}, "generalization"),
    ("pilot_2_step_easy_gen_10_line_recolor_vertical_v1", "easy", ("line_completion", "recolor_symbol"), "line_recolor", {"axis": "vertical", "line_index": 2, "gap_index": 4, "line_value": 3, "target_color": 7}, "generalization"),
    ("pilot_2_step_medium_gen_11_recolor_border_plus_v1", "medium", ("recolor_symbol", "border_frame"), "recolor_border", {"shape": "plus_small", "source_color": 4, "target_color": 6, "frame_color": 9}, "generalization"),
    ("pilot_2_step_medium_gen_12_extract_border_large_v1", "medium", ("extract_largest_object", "border_frame"), "extract_border", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 4, "small_color": 9, "frame_color": 6, "small_cells": [(0, 6), (6, 0)]}, "generalization"),
    ("pilot_2_step_medium_gen_13_noise_border_alt_frame_v1", "medium", ("remove_background_noise", "border_frame"), "noise_border", {"rows": 7, "cols": 7, "object_color": 4, "noise_color": 9, "frame_color": 6, "noise_cells": [(0, 0), (0, 6)]}, "generalization"),
    ("pilot_2_step_medium_gen_14_move_recolor_two_steps_v1", "medium", ("move_single_object", "recolor_symbol"), "move_recolor", {"direction": "right", "steps": 2, "object_color": 5, "target_color": 7, "shape": "domino_h"}, "generalization"),
    ("pilot_2_step_medium_gen_15_symmetry_border_large_v1", "medium", ("complete_symmetry", "border_frame"), "symmetry_border", {"rows": 7, "cols": 7, "object_color": 4, "frame_color": 6, "seed_cells": [(0, 3), (6, 2)]}, "generalization"),
    ("pilot_2_step_medium_gen_16_copy_line_vertical_v1", "medium", ("copy_grid", "line_completion"), "copy_line", {"rows": 7, "cols": 7, "axis": "vertical", "line_index": 4, "gap_index": 2, "line_value": 5}, "generalization"),
    ("pilot_2_step_medium_gen_17_line_border_vertical_v1", "medium", ("line_completion", "border_frame"), "line_border", {"rows": 7, "cols": 7, "axis": "vertical", "line_index": 3, "gap_index": 5, "line_value": 4, "frame_color": 8}, "generalization"),
    ("pilot_2_step_medium_gen_18_extract_symmetry_large_v1", "medium", ("extract_largest_object", "complete_symmetry"), "extract_symmetry", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 3, "small_color": 8, "small_cells": [(0, 0), (0, 6)]}, "generalization"),
    ("pilot_2_step_medium_gen_19_rotate_recolor_plus_v1", "medium", ("rotate_object_90", "recolor_symbol"), "rotate_recolor", {"shape": "plus_small", "object_color": 3, "target_color": 8}, "generalization"),
    ("pilot_2_step_medium_gen_20_reflect_move_vertical_v1", "medium", ("reflect_object_horizontal_or_vertical", "move_single_object"), "reflect_move", {"axis": "vertical", "direction": "down", "steps": 1, "object_color": 5, "shape": "asym_l"}, "generalization"),
    ("pilot_2_step_medium_ctx_01_fill_line_vertical_transfer_v1", "medium", ("fill_region", "line_completion"), "fill_line", {"rows": 7, "cols": 7, "border_color": 4, "fill_color": 6, "axis": "vertical", "line_index": 3, "gap_index": 4, "line_value": 6}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_02_fill_border_color_transfer_v1", "medium", ("fill_region", "border_frame"), "fill_border", {"rows": 7, "cols": 7, "border_color": 5, "fill_color": 3, "frame_color": 9}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_03_fill_symmetry_large_transfer_v1", "medium", ("fill_region", "complete_symmetry"), "fill_symmetry", {"rows": 7, "cols": 7, "border_color": 3, "fill_color": 5, "seed_cells": [(0, 3)]}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_04_count_border_row_transfer_v1", "medium", ("object_count_to_pattern", "border_frame"), "count_border", {"rows": 7, "cols": 7, "count": 4, "row_index": 4, "pattern_color": 7, "frame_color": 5}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_05_noise_count_large_transfer_v1", "medium", ("remove_background_noise", "object_count_to_pattern"), "noise_count", {"rows": 7, "cols": 7, "pattern_color": 6, "count": 4, "row_index": 4, "object_cells": [(1, 1), (1, 5), (5, 2), (5, 5)], "noise_cells": [(0, 0), (6, 6)]}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_06_extract_count_large_transfer_v1", "medium", ("extract_largest_object", "object_count_to_pattern"), "extract_count", {"rows": 7, "cols": 7, "large_cells": [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3)], "small_cells": [(6, 6)], "pattern_color": 6, "row_index": 4}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_07_count_recolor_large_transfer_v1", "medium", ("object_count_to_pattern", "recolor_symbol"), "count_recolor", {"rows": 7, "cols": 7, "count": 4, "row_index": 4, "pattern_color": 5, "target_color": 8}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_08_fill_recolor_large_transfer_v1", "medium", ("fill_region", "recolor_symbol"), "fill_recolor", {"rows": 8, "cols": 8, "border_color": 6, "fill_color": 2, "target_color": 9}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1", "medium", ("extract_largest_object", "recolor_symbol"), "extract_recolor", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 5, "target_color": 2, "small_color": 8, "small_cells": [(0, 6), (6, 0)]}, "parameter_transfer"),
    ("pilot_2_step_medium_ctx_10_fill_line_large_transfer_v1", "medium", ("fill_region", "line_completion"), "fill_line", {"rows": 8, "cols": 8, "border_color": 4, "fill_color": 7, "line_value": 7, "axis": "horizontal", "line_index": 3, "gap_index": 5}, "parameter_transfer"),
    ("pilot_2_step_stress_exp_01_rotate_border_large_v1", "stress", ("rotate_object_90", "border_frame"), "rotate_border", {"rows": 7, "cols": 7, "object_color": 3, "frame_color": 9, "shape": "plus_small"}, "stress"),
    ("pilot_2_step_stress_exp_02_reflect_border_vertical_v1", "stress", ("reflect_object_horizontal_or_vertical", "border_frame"), "reflect_border", {"rows": 7, "cols": 7, "axis": "vertical", "object_color": 4, "frame_color": 9}, "stress"),
    ("pilot_2_step_stress_exp_03_rotate_move_two_steps_v1", "stress", ("rotate_object_90", "move_single_object"), "rotate_move", {"rows": 7, "cols": 7, "direction": "down", "steps": 2, "object_color": 3, "shape": "plus_small"}, "stress"),
    ("pilot_2_step_stress_exp_04_reflect_symmetry_large_v1", "stress", ("reflect_object_horizontal_or_vertical", "complete_symmetry"), "reflect_symmetry", {"rows": 7, "cols": 7, "axis": "horizontal", "object_color": 5, "shape": "plus_small"}, "stress"),
    ("pilot_2_step_stress_exp_05_noise_symmetry_large_v1", "stress", ("remove_background_noise", "complete_symmetry"), "noise_symmetry", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "object_color": 4, "noise_color": 9, "noise_cells": [(0, 0), (6, 6)]}, "stress"),
    ("pilot_2_step_stress_exp_06_extract_line_vertical_v1", "stress", ("extract_largest_object", "line_completion"), "extract_line", {"rows": 7, "cols": 7, "large_rect": (1, 1, 5, 5), "large_color": 4, "small_color": 8, "small_cells": [(0, 0)], "axis": "vertical", "line_index": 3, "line_value": 4}, "stress"),
    ("pilot_2_step_stress_exp_07_count_line_vertical_v1", "stress", ("object_count_to_pattern", "line_completion"), "count_line", {"rows": 7, "cols": 7, "count": 4, "row_index": 4, "pattern_color": 6, "axis": "vertical", "line_index": 4}, "stress"),
    ("pilot_2_step_stress_exp_08_fill_count_known_residual_v1", "stress", ("fill_region", "object_count_to_pattern"), "fill_count", {"rows": 7, "cols": 7, "border_color": 3, "fill_color": 5, "pattern_color": 8, "row_index": 4}, "stress"),
    ("pilot_2_step_stress_exp_09_symmetry_count_large_v1", "stress", ("complete_symmetry", "object_count_to_pattern"), "symmetry_count", {"rows": 7, "cols": 7, "object_color": 4, "pattern_color": 8, "row_index": 4, "seed_cells": [(0, 2)]}, "stress"),
    ("pilot_2_step_stress_exp_10_move_reflect_two_steps_v1", "stress", ("move_single_object", "reflect_object_horizontal_or_vertical"), "move_reflect", {"rows": 7, "cols": 7, "direction": "down", "steps": 2, "axis": "vertical", "object_color": 5, "shape": "asym_l"}, "stress"),
)

ALL_TASK_SPECS_V1 = TASK_SPECS_V1 + EXPANSION_TASK_SPECS_V1

_SHORTCUT_PRIMITIVES_V1 = {"copy"}
SOLVER_PRIMITIVE_ID_ALIASES_V1 = {
    "copy_grid": "copy",
    "recolor_symbol": "recolor",
    "move_single_object": "move",
    "fill_region": "fill_region",
    "extract_largest_object": "extract_largest_object",
    "border_frame": "border_frame",
    "complete_symmetry": "complete_symmetry",
    "line_completion": "line_completion",
    "object_count_to_pattern": "object_count_to_pattern",
    "remove_background_noise": "remove_background_noise",
    "rotate_object_90": "rotate_object_90",
    "reflect_object_horizontal_or_vertical": "reflect_object_horizontal_or_vertical",
}


SCENE_PARAMETERS_BY_TYPE_V1: dict[str, dict[str, Any]] = {
    "noise_extract": {"rows": 6, "cols": 6, "large_color": 2, "noise_color": 8, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (5, 5)]},
    "noise_recolor": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 5, "large_rect": (1, 1, 4, 4), "noise_color": 8, "noise_cells": [(0, 5), (5, 0)]},
    "extract_recolor": {"rows": 6, "cols": 6, "large_color": 3, "target_color": 6, "small_color": 7, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0), (5, 5)]},
    "move_border": {"rows": 6, "cols": 6, "object_color": 3, "frame_color": 8, "direction": "right", "steps": 1, "shape": "domino_h"},
    "copy_recolor": {"rows": 6, "cols": 6, "source_color": 4, "target_color": 6, "shape": "l3"},
    "copy_border": {"rows": 6, "cols": 6, "object_color": 3, "frame_color": 8, "shape": "single"},
    "fill_recolor": {"rows": 6, "cols": 6, "border_color": 3, "fill_color": 4, "target_color": 7},
    "fill_line": {"rows": 6, "cols": 6, "border_color": 3, "fill_color": 4, "line_value": 4, "axis": "horizontal", "line_index": 2, "gap_index": 3},
    "symmetry_recolor": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 5, "seed_cells": [(0, 1), (5, 4)]},
    "count_border": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 7, "frame_color": 8, "count": 3, "row_index": 3},
    "line_recolor": {"rows": 6, "cols": 6, "line_value": 2, "target_color": 5, "axis": "horizontal", "line_index": 3, "gap_index": 2},
    "recolor_border": {"rows": 6, "cols": 6, "source_color": 2, "target_color": 6, "frame_color": 8, "shape": "plus_small"},
    "extract_border": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 6, "frame_color": 8, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 5), (5, 0)]},
    "noise_border": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "frame_color": 8, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (0, 5)]},
    "move_recolor": {"rows": 6, "cols": 6, "object_color": 3, "target_color": 6, "direction": "down", "steps": 1, "shape": "domino_v"},
    "symmetry_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "seed_cells": [(0, 2), (5, 3)]},
    "copy_line": {"rows": 6, "cols": 6, "line_value": 2, "axis": "horizontal", "line_index": 3, "gap_index": 4},
    "fill_border": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "frame_color": 8},
    "line_border": {"rows": 6, "cols": 6, "line_value": 2, "axis": "horizontal", "line_index": 2, "gap_index": 1, "frame_color": 8},
    "extract_symmetry": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 6, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0), (0, 5)]},
    "rotate_recolor": {"rows": 6, "cols": 6, "object_color": 2, "target_color": 6, "shape": "l3"},
    "reflect_move": {"rows": 6, "cols": 6, "object_color": 2, "axis": "horizontal", "direction": "right", "steps": 1, "shape": "asym_l"},
    "rotate_reflect": {"rows": 6, "cols": 6, "object_color": 2, "axis": "vertical", "shape": "l3"},
    "reflect_recolor": {"rows": 6, "cols": 6, "object_color": 2, "target_color": 5, "axis": "vertical", "shape": "asym_l"},
    "noise_count": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "pattern_color": 5, "count": 3, "row_index": 3, "object_cells": [(1, 1), (1, 4), (4, 2)], "noise_cells": [(0, 0), (5, 5)]},
    "extract_count": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 7, "pattern_color": 5, "row_index": 3, "large_cells": [(1, 1), (1, 2), (2, 1), (2, 2)], "small_cells": [(5, 5)]},
    "symmetry_line": {"rows": 6, "cols": 6, "line_value": 2, "seed_cells": [(2, 1), (2, 4)], "axis": "horizontal", "line_index": 2, "gap_index": 3},
    "move_symmetry": {"rows": 6, "cols": 6, "object_color": 3, "direction": "right", "steps": 1, "shape": "domino_h"},
    "fill_symmetry": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "seed_cells": [(0, 2)]},
    "count_recolor": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 4, "target_color": 7, "count": 3, "row_index": 3},
    "rotate_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "shape": "l3"},
    "reflect_border": {"rows": 6, "cols": 6, "object_color": 2, "frame_color": 8, "axis": "horizontal", "shape": "asym_l"},
    "rotate_move": {"rows": 6, "cols": 6, "object_color": 2, "direction": "right", "steps": 1, "shape": "l3"},
    "reflect_symmetry": {"rows": 6, "cols": 6, "object_color": 2, "axis": "vertical", "shape": "asym_l"},
    "noise_symmetry": {"rows": 6, "cols": 6, "object_color": 2, "noise_color": 7, "large_rect": (1, 1, 4, 4), "noise_cells": [(0, 0), (5, 5)]},
    "extract_line": {"rows": 6, "cols": 6, "large_color": 2, "small_color": 7, "large_rect": (1, 1, 4, 4), "small_cells": [(0, 0)], "axis": "horizontal", "line_index": 2, "line_value": 2},
    "count_line": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 4, "count": 3, "row_index": 3, "axis": "horizontal", "line_index": 3},
    "fill_count": {"rows": 6, "cols": 6, "border_color": 2, "fill_color": 4, "pattern_color": 7, "row_index": 3},
    "symmetry_count": {"rows": 6, "cols": 6, "object_color": 2, "pattern_color": 7, "row_index": 3, "seed_cells": [(0, 1)]},
    "move_reflect": {"rows": 6, "cols": 6, "object_color": 2, "direction": "right", "steps": 1, "axis": "horizontal", "shape": "asym_l"},
}


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


def to_arc_style_synthetic_2_step_pilot_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid(rows: int, cols: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(cols)] for _ in range(rows)]


def _clone_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _set_cell(grid: list[list[int]], row: int, col: int, value: int) -> None:
    if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
        grid[row][col] = value


def _set_rect(grid: list[list[int]], top: int, left: int, bottom: int, right: int, value: int) -> None:
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            _set_cell(grid, row, col, value)


def _background_value_from_grid(grid: Sequence[Sequence[int]]) -> int:
    counts = Counter(cell for row in grid for cell in row)
    return int(counts.most_common(1)[0][0]) if counts else 0


def _non_background_value(grid: Sequence[Sequence[int]], background_value: int) -> int | None:
    counts = Counter(cell for row in grid for cell in row if cell != background_value)
    return int(counts.most_common(1)[0][0]) if counts else None


def _neighbors(row: int, col: int) -> list[tuple[int, int]]:
    return [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]


def _connected_components(grid: Sequence[Sequence[int]], background_value: int = 0) -> list[list[tuple[int, int]]]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(rows):
        for col in range(cols):
            if (row, col) in seen or grid[row][col] == background_value:
                continue
            stack = [(row, col)]
            component: list[tuple[int, int]] = []
            seen.add((row, col))
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for next_row, next_col in _neighbors(current_row, current_col):
                    if not (0 <= next_row < rows and 0 <= next_col < cols):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == background_value:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(component)
    components.sort(key=lambda cells: (-len(cells), min(cells)))
    return components


def _shape_cells(shape: str, *, origin_row: int, origin_col: int) -> list[tuple[int, int]]:
    relative = {
        "single": [(0, 0)],
        "domino_h": [(0, 0), (0, 1)],
        "domino_v": [(0, 0), (1, 0)],
        "l3": [(0, 1), (1, 0), (1, 1)],
        "asym_l": [(0, 1), (1, 1), (1, 2)],
        "plus_small": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    }.get(shape, [(0, 0)])
    return [(origin_row + row, origin_col + col) for row, col in relative]


def _paint_shape(grid: list[list[int]], shape: str, *, origin_row: int, origin_col: int, value: int) -> None:
    for row, col in _shape_cells(shape, origin_row=origin_row, origin_col=origin_col):
        _set_cell(grid, row, col, value)


def _copy_grid(grid: Sequence[Sequence[int]], **_: Any) -> list[list[int]]:
    return _clone_grid(grid)


def _recolor_symbol(grid: Sequence[Sequence[int]], *, from_value: int | None = None, to_value: int | None = None, background_value: int = 0) -> list[list[int]]:
    source = _clone_grid(grid)
    actual_from = from_value if from_value is not None else _non_background_value(source, background_value)
    if actual_from is None or to_value is None:
        return source
    for row_index, row in enumerate(source):
        for col_index, value in enumerate(row):
            if value == actual_from:
                source[row_index][col_index] = to_value
    return source


def _move_single_object(grid: Sequence[Sequence[int]], *, direction: str, steps: int = 1, object_value: int | None = None, background_value: int = 0) -> list[list[int]]:
    delta_map = {
        "up": (-steps, 0),
        "down": (steps, 0),
        "left": (0, -steps),
        "right": (0, steps),
    }
    if direction not in delta_map:
        return _clone_grid(grid)
    value = object_value if object_value is not None else _non_background_value(grid, background_value)
    if value is None:
        return _clone_grid(grid)
    delta_row, delta_col = delta_map[direction]
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    output = _grid(rows, cols, background_value)
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] != value:
                continue
            new_row = row + delta_row
            new_col = col + delta_col
            if 0 <= new_row < rows and 0 <= new_col < cols:
                output[new_row][new_col] = value
    return output


def _fill_region(grid: Sequence[Sequence[int]], *, fill_value: int, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    top = left = bottom = right = None
    for row in range(rows):
        for col in range(cols):
            if output[row][col] != background_value:
                top = row if top is None else min(top, row)
                left = col if left is None else min(left, col)
                bottom = row if bottom is None else max(bottom, row)
                right = col if right is None else max(right, col)
    if top is None or bottom is None or left is None or right is None or bottom - top < 2 or right - left < 2:
        return output
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            output[row][col] = fill_value
    return output


def _extract_largest_object(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return output
    component = components[0]
    value = grid[component[0][0]][component[0][1]]
    for row, col in component:
        output[row][col] = value
    return output


def _border_frame(grid: Sequence[Sequence[int]], *, frame_value: int) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if not rows or not cols:
        return output
    for row in range(rows):
        output[row][0] = frame_value
        output[row][cols - 1] = frame_value
    for col in range(cols):
        output[0][col] = frame_value
        output[rows - 1][col] = frame_value
    return output


def _complete_symmetry(grid: Sequence[Sequence[int]], *, axes: Sequence[str] | None = None, background_value: int = 0) -> list[list[int]]:
    axes = tuple(axes or ("horizontal", "vertical"))
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    for row in range(rows):
        for col in range(cols):
            value = output[row][col]
            if value == background_value:
                continue
            targets = [(row, col)]
            if "horizontal" in axes:
                targets.append((rows - 1 - row, col))
            if "vertical" in axes:
                targets.append((row, cols - 1 - col))
            if "horizontal" in axes and "vertical" in axes:
                targets.append((rows - 1 - row, cols - 1 - col))
            for target_row, target_col in targets:
                output[target_row][target_col] = value
    return output


def _line_completion(
    grid: Sequence[Sequence[int]],
    *,
    axis: str,
    line_index: int,
    line_value: int,
    background_value: int = 0,
) -> list[list[int]]:
    output = _clone_grid(grid)
    rows = len(output)
    cols = len(output[0]) if rows else 0
    if axis == "horizontal" and 0 <= line_index < rows:
        active = [col for col in range(cols) if output[line_index][col] == line_value]
        if active:
            for col in range(min(active), max(active) + 1):
                output[line_index][col] = line_value
    elif axis == "vertical" and 0 <= line_index < cols:
        active = [row for row in range(rows) if output[row][line_index] == line_value]
        if active:
            for row in range(min(active), max(active) + 1):
                output[row][line_index] = line_value
    return output


def _remove_background_noise(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _clone_grid(grid)
    for component in _connected_components(grid, background_value=background_value):
        if len(component) <= 1:
            for row, col in component:
                output[row][col] = background_value
    return output


def _object_count_to_pattern(
    grid: Sequence[Sequence[int]],
    *,
    count: int | None = None,
    pattern_value: int,
    row_index: int,
    background_value: int = 0,
) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    actual_count = count if count is not None else len(_connected_components(grid, background_value=background_value))
    if not output:
        return output
    width = len(output[0])
    start = max(0, min(width - 1, 1))
    end = min(width - 1, start + max(0, int(actual_count)) - 1)
    if 0 <= row_index < len(output):
        for col in range(start, end + 1):
            output[row_index][col] = pattern_value
    return output


def _rotate_object_90(grid: Sequence[Sequence[int]], *, background_value: int = 0) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return _clone_grid(grid)
    component = components[0]
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    bottom = max(row for row, _ in component)
    right = max(col for _, col in component)
    height = bottom - top + 1
    width = right - left + 1
    for row, col in component:
        value = grid[row][col]
        local_row = row - top
        local_col = col - left
        new_row = top + local_col
        new_col = left + (height - 1 - local_row)
        if 0 <= new_row < len(output) and 0 <= new_col < len(output[new_row]):
            output[new_row][new_col] = value
    return output


def _reflect_object_horizontal_or_vertical(
    grid: Sequence[Sequence[int]], *, axis: str, background_value: int = 0
) -> list[list[int]]:
    output = _grid(len(grid), len(grid[0]) if grid else 0, background_value)
    components = _connected_components(grid, background_value=background_value)
    if not components:
        return _clone_grid(grid)
    component = components[0]
    top = min(row for row, _ in component)
    left = min(col for _, col in component)
    bottom = max(row for row, _ in component)
    right = max(col for _, col in component)
    for row, col in component:
        value = grid[row][col]
        if axis == "horizontal":
            new_row, new_col = row, right - (col - left)
        else:
            new_row, new_col = bottom - (row - top), col
        output[new_row][new_col] = value
    return output


_PRIMITIVE_EXECUTORS_V1 = {
    "copy_grid": _copy_grid,
    "recolor_symbol": _recolor_symbol,
    "move_single_object": _move_single_object,
    "fill_region": _fill_region,
    "extract_largest_object": _extract_largest_object,
    "border_frame": _border_frame,
    "complete_symmetry": _complete_symmetry,
    "line_completion": _line_completion,
    "remove_background_noise": _remove_background_noise,
    "object_count_to_pattern": _object_count_to_pattern,
    "rotate_object_90": _rotate_object_90,
    "reflect_object_horizontal_or_vertical": _reflect_object_horizontal_or_vertical,
}
SUPPORTED_SEQUENCE_PRIMITIVES_V1 = frozenset(_PRIMITIVE_EXECUTORS_V1.keys())


def _apply_primitive(grid: Sequence[Sequence[int]], primitive_id: str, parameters: Mapping[str, Any]) -> list[list[int]]:
    executor = _PRIMITIVE_EXECUTORS_V1[primitive_id]
    return executor(_clone_grid(grid), **dict(parameters))


def _apply_sequence(grid: Sequence[Sequence[int]], sequence: Sequence[Mapping[str, Any]]) -> list[list[int]]:
    output = _clone_grid(grid)
    for step in sequence:
        output = _apply_primitive(output, _safe_text(step.get("primitive_id")), step.get("parameters", {}))
    return output



def _grid_from_pair_payload(payload: Any) -> list[list[int]]:
    if isinstance(payload, Mapping) and "cell_values" in payload:
        payload = payload.get("cell_values")
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        return []
    return [list(row) for row in payload if isinstance(row, Sequence) and not isinstance(row, (str, bytes, bytearray))]


def _pair_input_grid(train_pair: Mapping[str, Any]) -> list[list[int]]:
    return _grid_from_pair_payload(train_pair.get("input_grid"))


def _pair_output_grid(train_pair: Mapping[str, Any]) -> list[list[int]]:
    return _grid_from_pair_payload(train_pair.get("output_grid"))


def _compare_grids(expected: Sequence[Sequence[int]], predicted: Sequence[Sequence[int]]) -> dict[str, Any]:
    expected_grid = [list(row) for row in expected]
    predicted_grid = [list(row) for row in predicted]
    mismatch_cells: list[dict[str, Any]] = []
    height = max(len(expected_grid), len(predicted_grid))
    width = max((len(row) for row in expected_grid), default=0)
    width = max(width, max((len(row) for row in predicted_grid), default=0))
    for row_index in range(height):
        for column_index in range(width):
            expected_value = expected_grid[row_index][column_index] if row_index < len(expected_grid) and column_index < len(expected_grid[row_index]) else None
            predicted_value = predicted_grid[row_index][column_index] if row_index < len(predicted_grid) and column_index < len(predicted_grid[row_index]) else None
            if expected_value != predicted_value:
                mismatch_cells.append({"row": row_index, "column": column_index, "expected": expected_value, "predicted": predicted_value})
    return {
        "exact_match": expected_grid == predicted_grid,
        "value_mismatch_count": len(mismatch_cells),
        "mismatch_cells": mismatch_cells,
    }


def _border_values(grid: Sequence[Sequence[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    values: list[int] = []
    rows = len(grid)
    cols = len(grid[0])
    for col in range(cols):
        values.append(int(grid[0][col]))
        values.append(int(grid[rows - 1][col]))
    for row in range(1, rows - 1):
        values.append(int(grid[row][0]))
        values.append(int(grid[row][cols - 1]))
    return values


def _uniform_border_value(grid: Sequence[Sequence[int]]) -> int | None:
    values = _border_values(grid)
    unique = {int(value) for value in values}
    return int(next(iter(unique))) if len(unique) == 1 else None


def _interior_values(grid: Sequence[Sequence[int]]) -> list[int]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows <= 2 or cols <= 2:
        return [int(cell) for row in grid for cell in row]
    return [int(grid[row][col]) for row in range(1, rows - 1) for col in range(1, cols - 1)]


def _dominant_value(values: Sequence[int], *, exclude: Sequence[int] | None = None) -> int | None:
    exclude_set = {int(value) for value in (exclude or [])}
    counts = Counter(int(value) for value in values if int(value) not in exclude_set)
    return int(counts.most_common(1)[0][0]) if counts else None


def _non_background_values(grid: Sequence[Sequence[int]], background_value: int) -> list[int]:
    return sorted({int(cell) for row in grid for cell in row if int(cell) != background_value})


def _dominant_non_background_value(grid: Sequence[Sequence[int]], background_value: int) -> int | None:
    counts = Counter(int(cell) for row in grid for cell in row if int(cell) != background_value)
    return int(counts.most_common(1)[0][0]) if counts else None


def _line_candidate_params(grid: Sequence[Sequence[int]], target: Sequence[Sequence[int]], background_value: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    rows = len(target)
    cols = len(target[0]) if rows else 0
    for row_index in range(rows):
        values = [int(cell) for cell in target[row_index] if int(cell) != background_value]
        if values:
            value = Counter(values).most_common(1)[0][0]
            candidates.append({"axis": "horizontal", "line_index": row_index, "line_value": value, "background_value": background_value})
    for col_index in range(cols):
        values = [int(target[row_index][col_index]) for row_index in range(rows) if int(target[row_index][col_index]) != background_value]
        if values:
            value = Counter(values).most_common(1)[0][0]
            candidates.append({"axis": "vertical", "line_index": col_index, "line_value": value, "background_value": background_value})
    if not candidates:
        dominant = _dominant_non_background_value(grid, background_value)
        if dominant is not None:
            candidates.append({"axis": "horizontal", "line_index": max(0, len(grid) // 2), "line_value": dominant, "background_value": background_value})
    return candidates[:8]


def _dedupe_parameter_options(options: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for option in options:
        normalized = json.dumps(_json_safe(option), sort_keys=True)
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(dict(option))
    return deduped


def _fill_region_parameter_options(current_grid: Sequence[Sequence[int]], target_grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    default_background = _background_value_from_grid(current_grid)
    border_value = _uniform_border_value(current_grid)
    interior_current = _interior_values(current_grid)
    interior_target = _interior_values(target_grid)
    background_candidates = [default_background]
    interior_background = _dominant_value(interior_current, exclude=[border_value] if border_value is not None else [])
    if interior_background is not None:
        background_candidates.append(interior_background)
    if border_value is not None:
        background_candidates.append(border_value)
    options: list[dict[str, Any]] = []
    for background_value in background_candidates:
        fill_candidates: list[int] = []
        fill_target = _dominant_value(interior_target, exclude=[background_value, border_value] if border_value is not None else [background_value])
        if fill_target is not None:
            fill_candidates.append(fill_target)
        fill_current = _dominant_value(_non_background_values(target_grid, background_value), exclude=[border_value] if border_value is not None else [])
        if fill_current is not None:
            fill_candidates.append(fill_current)
        for fill_value in fill_candidates[:3]:
            options.append({"fill_value": fill_value, "background_value": background_value})
    return _dedupe_parameter_options(options)[:8]


def _object_count_parameter_options(current_grid: Sequence[Sequence[int]], target_grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    background_value = _background_value_from_grid(current_grid)
    rows = len(target_grid)
    cols = len(target_grid[0]) if rows else 0
    border_value = _uniform_border_value(target_grid)
    row_scores: list[tuple[int, int, int, int]] = []
    row_range = range(rows)
    if border_value is not None and rows > 2 and cols > 2:
        row_range = range(1, rows - 1)
    for row_index in row_range:
        if border_value is not None and cols > 2:
            cells = [int(target_grid[row_index][col]) for col in range(1, cols - 1)]
            non_bg = [value for value in cells if value not in {background_value, border_value}]
        else:
            cells = [int(cell) for cell in target_grid[row_index]]
            non_bg = [value for value in cells if value != background_value]
        if non_bg:
            pattern_value, width = Counter(non_bg).most_common(1)[0][0], len(non_bg)
            row_scores.append((row_index, pattern_value, width, abs(row_index - (rows // 2))))
    row_scores.sort(key=lambda item: (-item[2], item[3], item[0], item[1]))
    options: list[dict[str, Any]] = []
    for row_index, pattern_value, _, _ in row_scores[:4]:
        options.append({"count": None, "pattern_value": pattern_value, "row_index": row_index, "background_value": background_value})
    if not options:
        target_values = _non_background_values(target_grid, background_value)
        fallback_value = _dominant_value(target_values) if target_values else _dominant_value(_non_background_values(current_grid, background_value))
        if fallback_value is None:
            fallback_value = 1
        options.append({"count": None, "pattern_value": fallback_value, "row_index": max(0, rows // 2), "background_value": background_value})
    return _dedupe_parameter_options(options)[:8]


def _primitive_parameter_options(primitive_id: str, current_grid: Sequence[Sequence[int]], target_grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    background_value = _background_value_from_grid(current_grid)
    current_values = _non_background_values(current_grid, background_value)
    target_values = _non_background_values(target_grid, background_value)
    if primitive_id == "copy_grid":
        return [{}]
    if primitive_id in {"remove_background_noise", "extract_largest_object", "rotate_object_90"}:
        options = [{"background_value": background_value}]
        for extra_background in (current_values[:2] + target_values[:2]):
            options.append({"background_value": extra_background})
        return _dedupe_parameter_options(options)[:4]
    if primitive_id == "complete_symmetry":
        return [{"axes": ["horizontal", "vertical"], "background_value": background_value}]
    if primitive_id == "reflect_object_horizontal_or_vertical":
        return [
            {"axis": "horizontal", "background_value": background_value},
            {"axis": "vertical", "background_value": background_value},
        ]
    if primitive_id == "move_single_object":
        object_candidates = current_values or target_values or [None]
        options = []
        for direction in ("up", "down", "left", "right"):
            for steps in (1, 2):
                for object_value in object_candidates[:2]:
                    params = {"direction": direction, "steps": steps, "background_value": background_value}
                    if object_value is not None:
                        params["object_value"] = object_value
                    options.append(params)
        return options
    if primitive_id == "recolor_symbol":
        options = []
        source_values = current_values or target_values
        destination_values = target_values or current_values
        for from_value in source_values[:4]:
            for to_value in destination_values[:4]:
                if from_value == to_value:
                    continue
                options.append({"from_value": from_value, "to_value": to_value, "background_value": background_value})
        return _dedupe_parameter_options(options)[:12]
    if primitive_id == "border_frame":
        border_values = [value for value in _border_values(target_grid) if value != background_value]
        values = [value for value, _ in Counter(border_values).most_common(3)] or target_values[:3]
        return [{"frame_value": value} for value in values]
    if primitive_id == "fill_region":
        return _fill_region_parameter_options(current_grid, target_grid)
    if primitive_id == "line_completion":
        return _line_candidate_params(current_grid, target_grid, background_value)
    if primitive_id == "object_count_to_pattern":
        return _object_count_parameter_options(current_grid, target_grid)
    return []


def _best_single_step_fit(primitive_id: str, current_grid: Sequence[Sequence[int]], target_grid: Sequence[Sequence[int]]) -> dict[str, Any] | None:
    options = _primitive_parameter_options(primitive_id, current_grid, target_grid)
    best: dict[str, Any] | None = None
    for option_index, parameters in enumerate(options):
        try:
            predicted = _apply_primitive(current_grid, primitive_id, parameters)
            comparison = _compare_grids(target_grid, predicted)
            candidate = {"parameters": dict(parameters), "predicted_grid": predicted, "comparison": comparison, "rank": (comparison["value_mismatch_count"], option_index)}
        except Exception as exc:  # pragma: no cover
            candidate = {
                "parameters": dict(parameters),
                "predicted_grid": _clone_grid(current_grid),
                "comparison": {"exact_match": False, "value_mismatch_count": 10**6, "mismatch_cells": []},
                "rank": (10**6, option_index),
                "error": _safe_text(exc),
            }
        if best is None or candidate["rank"] < best["rank"]:
            best = candidate
    return best


def _best_sequence_pair_fit(primitive_pair: Sequence[str], input_grid: Sequence[Sequence[int]], final_grid: Sequence[Sequence[int]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if len(primitive_pair) != 2:
        return None, None
    step1_options = _primitive_parameter_options(_safe_text(primitive_pair[0]), input_grid, final_grid)
    best_pair: tuple[dict[str, Any], dict[str, Any]] | None = None
    best_rank: tuple[int, int, int, int] | None = None
    for step1_index, step1_parameters in enumerate(step1_options):
        try:
            predicted_intermediate = _apply_primitive(input_grid, _safe_text(primitive_pair[0]), step1_parameters)
            step1_comparison = _compare_grids(final_grid, predicted_intermediate)
        except Exception as exc:  # pragma: no cover
            step1_candidate = {
                "parameters": dict(step1_parameters),
                "predicted_grid": _clone_grid(input_grid),
                "comparison": {"exact_match": False, "value_mismatch_count": 10**6, "mismatch_cells": []},
                "rank": (10**6, step1_index),
                "error": _safe_text(exc),
            }
            step2_candidate = None
            pair_rank = (10**6, 10**6, step1_index, 10**6)
            if best_rank is None or pair_rank < best_rank:
                best_pair = (step1_candidate, step2_candidate)  # type: ignore[arg-type]
                best_rank = pair_rank
            continue
        step1_candidate = {
            "parameters": dict(step1_parameters),
            "predicted_grid": predicted_intermediate,
            "comparison": step1_comparison,
            "rank": (step1_comparison["value_mismatch_count"], step1_index),
        }
        step2_candidate = _best_single_step_fit(_safe_text(primitive_pair[1]), predicted_intermediate, final_grid)
        if step2_candidate is None:
            pair_rank = (10**6, step1_comparison["value_mismatch_count"], step1_index, 10**6)
            if best_rank is None or pair_rank < best_rank:
                best_pair = (step1_candidate, step2_candidate)  # type: ignore[arg-type]
                best_rank = pair_rank
            continue
        pair_rank = (
            int(step2_candidate["comparison"]["value_mismatch_count"]),
            int(step1_comparison["value_mismatch_count"]),
            step1_index,
            int(step2_candidate["rank"][1]),
        )
        if best_rank is None or pair_rank < best_rank:
            best_pair = (step1_candidate, step2_candidate)
            best_rank = pair_rank
    if best_pair is None:
        return None, None
    return best_pair


def _parse_supported_pair_from_packet(packet: Mapping[str, Any]) -> list[str]:
    trace = packet.get("trace", {}) if isinstance(packet.get("trace"), Mapping) else {}
    composition_pair = _safe_text(trace.get("composition_pair") or trace.get("toy_task_type"))
    if "->" not in composition_pair:
        return []
    parts = [_safe_text(part).strip() for part in composition_pair.split("->")]
    if len(parts) != 2 or any(part not in SUPPORTED_SEQUENCE_PRIMITIVES_V1 for part in parts):
        return []
    return parts


def _summarize_stable_parameters(per_pair_steps: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    if not per_pair_steps:
        return summary
    dynamic_keys = {"background_value", "object_value", "count", "from_value", "to_value", "fill_value", "row_index", "pattern_value"}
    for step_index in range(len(per_pair_steps[0])):
        primitive_id = _safe_text(per_pair_steps[0][step_index].get("primitive_id"))
        all_keys = sorted({key for pair_steps in per_pair_steps for key in pair_steps[step_index].get("parameters", {}).keys()})
        stable_parameters: dict[str, Any] = {}
        dynamic_parameter_keys: list[str] = []
        for key in all_keys:
            values = [pair_steps[step_index].get("parameters", {}).get(key) for pair_steps in per_pair_steps]
            if all(value == values[0] for value in values):
                stable_parameters[key] = deepcopy(values[0])
            elif key in dynamic_keys:
                dynamic_parameter_keys.append(key)
        summary.append({"primitive_id": primitive_id, "stable_parameters": stable_parameters, "dynamic_parameter_keys": dynamic_parameter_keys})
    return summary


def _generate_bounded_sequence_candidates(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    packet = entry.get("packet", {}) if isinstance(entry.get("packet"), Mapping) else {}
    pair = _parse_supported_pair_from_packet(packet)
    if len(pair) != 2:
        return []
    train_pairs = packet.get("train_pairs", []) if isinstance(packet.get("train_pairs"), list) else []
    ordered_pairs = [pair, list(reversed(pair))][:MAX_SEQUENCE_CANDIDATES_PER_TASK_V1]
    candidates: list[dict[str, Any]] = []
    for candidate_rank, primitive_pair in enumerate(ordered_pairs):
        per_pair_steps: list[list[dict[str, Any]]] = []
        pair_reports: list[dict[str, Any]] = []
        generation_failed = False
        execution_failed = False
        total_mismatch = 0
        for train_pair in train_pairs:
            input_grid = _pair_input_grid(train_pair)
            final_grid = _pair_output_grid(train_pair)
            best_step1, best_step2 = _best_sequence_pair_fit(primitive_pair, input_grid, final_grid)
            if best_step1 is None or best_step2 is None:
                generation_failed = True
                break
            intermediate_grid = best_step1["predicted_grid"]
            try:
                final_prediction = _apply_primitive(intermediate_grid, primitive_pair[1], best_step2["parameters"])
                final_comparison = _compare_grids(final_grid, final_prediction)
            except Exception as exc:  # pragma: no cover
                execution_failed = True
                final_comparison = {"exact_match": False, "value_mismatch_count": 10**6, "mismatch_cells": []}
                best_step2 = {**best_step2, "error": _safe_text(exc)}
            per_pair_steps.append([
                {"primitive_id": primitive_pair[0], "parameters": deepcopy(best_step1["parameters"])},
                {"primitive_id": primitive_pair[1], "parameters": deepcopy(best_step2["parameters"])},
            ])
            pair_reports.append({
                "pair_id": _safe_text(train_pair.get("pair_id")),
                "step1": _json_safe(best_step1),
                "step2": _json_safe(best_step2),
                "final_comparison": _json_safe(final_comparison),
            })
            total_mismatch += int(final_comparison["value_mismatch_count"])
        if generation_failed:
            continue
        candidates.append({
            "candidate_id": f"{_safe_text(entry.get('task_id'))}:sequence:{candidate_rank}",
            "candidate_rank": candidate_rank,
            "primitive_pair": list(primitive_pair),
            "bounded_depth": MAX_SEQUENCE_LENGTH_V1,
            "represented_sequence": True,
            "per_pair_steps": _json_safe(per_pair_steps),
            "stable_sequence": _json_safe(_summarize_stable_parameters(per_pair_steps)),
            "pair_reports": _json_safe(pair_reports),
            "total_mismatch": total_mismatch,
            "execution_failed": execution_failed,
            "generation_trace": {
                "deterministic_order": True,
                "candidate_budget": MAX_SEQUENCE_CANDIDATES_PER_TASK_V1,
                "max_sequence_length": MAX_SEQUENCE_LENGTH_V1,
                "uses_train_output_for_transformation_inference": True,
                "uses_test_output": False,
                "uses_task_id_for_candidate_selection": False,
                "uses_notes_for_candidate_selection": False,
                "lookup_table_detected": False,
                "parameter_source": "train_pairs_only",
            },
        })
    return candidates


def _evaluate_sequence_candidate(entry: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    packet = entry.get("packet", {}) if isinstance(entry.get("packet"), Mapping) else {}
    train_pairs = packet.get("train_pairs", []) if isinstance(packet.get("train_pairs"), list) else []
    train_intermediate_grids = entry.get("train_intermediate_grids", []) if isinstance(entry.get("train_intermediate_grids"), list) else []
    step1_plausible_all = True
    step2_plausible_all = True
    final_exact_all = True
    total_mismatch = 0
    execution_failed = bool(candidate.get("execution_failed"))
    evaluation_rows: list[dict[str, Any]] = []
    for pair_index, train_pair in enumerate(train_pairs):
        input_grid = _pair_input_grid(train_pair)
        final_grid = _pair_output_grid(train_pair)
        expected_intermediate = train_intermediate_grids[pair_index] if pair_index < len(train_intermediate_grids) else []
        step_defs = candidate.get("per_pair_steps", [])[pair_index]
        step1 = step_defs[0]
        step2 = step_defs[1]
        try:
            predicted_intermediate = _apply_primitive(input_grid, _safe_text(step1.get("primitive_id")), step1.get("parameters", {}))
            predicted_final = _apply_primitive(predicted_intermediate, _safe_text(step2.get("primitive_id")), step2.get("parameters", {}))
        except Exception as exc:  # pragma: no cover
            execution_failed = True
            evaluation_rows.append({"pair_id": _safe_text(train_pair.get("pair_id")), "execution_error": _safe_text(exc)})
            step1_plausible_all = False
            step2_plausible_all = False
            final_exact_all = False
            total_mismatch += 10**6
            continue
        step1_comparison = _compare_grids(expected_intermediate, predicted_intermediate)
        oracle_step2 = _best_single_step_fit(_safe_text(step2.get("primitive_id")), expected_intermediate, final_grid)
        step2_plausible = False
        if oracle_step2 is not None:
            oracle_final = _apply_primitive(expected_intermediate, _safe_text(step2.get("primitive_id")), oracle_step2["parameters"])
            step2_plausible = _compare_grids(final_grid, oracle_final)["exact_match"]
        final_comparison = _compare_grids(final_grid, predicted_final)
        step1_plausible_all = step1_plausible_all and bool(step1_comparison["exact_match"])
        step2_plausible_all = step2_plausible_all and bool(step2_plausible)
        final_exact_all = final_exact_all and bool(final_comparison["exact_match"])
        total_mismatch += int(final_comparison["value_mismatch_count"])
        evaluation_rows.append({
            "pair_id": _safe_text(train_pair.get("pair_id")),
            "step1_exact": bool(step1_comparison["exact_match"]),
            "step2_exact_from_oracle_intermediate": bool(step2_plausible),
            "final_exact": bool(final_comparison["exact_match"]),
            "final_mismatch_count": int(final_comparison["value_mismatch_count"]),
        })
    if execution_failed:
        packet_status = "failed"
        train_fit_status = "failed"
    elif final_exact_all and train_pairs:
        packet_status = "exact"
        train_fit_status = "fit"
    elif candidate.get("represented_sequence"):
        packet_status = "partial"
        train_fit_status = "partial_fit"
    else:
        packet_status = "unsupported"
        train_fit_status = "unsupported"
    return {
        "candidate_id": _safe_text(candidate.get("candidate_id")),
        "represented_sequence": bool(candidate.get("represented_sequence")),
        "selected_primitive_sequence": [
            {"primitive_id": _safe_text(step.get("primitive_id")), "parameters": _json_safe(step.get("stable_parameters", {}))}
            for step in candidate.get("stable_sequence", [])
        ],
        "primitive_pair": list(candidate.get("primitive_pair", [])),
        "packet_status": packet_status,
        "train_fit_status": train_fit_status,
        "step1_plausible": step1_plausible_all,
        "step2_plausible": step2_plausible_all,
        "final_exact": final_exact_all,
        "total_mismatch": total_mismatch,
        "execution_failed": execution_failed,
        "pair_evaluations": _json_safe(evaluation_rows),
        "stable_sequence": _json_safe(candidate.get("stable_sequence", [])),
        "generation_trace": _json_safe(candidate.get("generation_trace", {})),
    }


def _variant_adjusted_cells(cells: Sequence[tuple[int, int]], variant_index: int, *, rows: int = 6, cols: int = 6) -> list[tuple[int, int]]:
    return [((row + (variant_index % 2)) % rows, (col + ((variant_index // 2) % 2)) % cols) for row, col in cells]


def _build_scene_input(scene_type: str, variant_index: int) -> list[list[int]]:
    params = deepcopy(SCENE_PARAMETERS_BY_TYPE_V1[scene_type])
    scene_family = _safe_text(params.get("__base_scene_type__"), scene_type)
    rows = int(params.get("rows", 6))
    cols = int(params.get("cols", 6))
    grid = _grid(rows, cols, 0)

    if scene_family in {"noise_extract", "noise_recolor", "extract_recolor", "extract_border", "noise_border", "noise_symmetry", "extract_line", "extract_symmetry"}:
        rect = params.get("large_rect", (1, 1, 4, 4))
        color = int(params.get("large_color", params.get("object_color", 2)))
        _set_rect(grid, *rect, color)
        for row, col in _variant_adjusted_cells(params.get("noise_cells", params.get("small_cells", [])), variant_index, rows=rows, cols=cols):
            _set_cell(grid, row, col, int(params.get("noise_color", params.get("small_color", 7))))
    elif scene_family in {"move_border", "move_recolor", "move_symmetry", "move_reflect", "copy_recolor", "copy_border", "recolor_border", "rotate_recolor", "rotate_border", "rotate_move", "rotate_reflect", "reflect_move", "reflect_recolor", "reflect_border", "reflect_symmetry"}:
        origin_row = 1 + (variant_index % 2)
        origin_col = 1 + ((variant_index // 2) % 2)
        shape = _safe_text(params.get("shape"), "single")
        _paint_shape(grid, shape, origin_row=origin_row, origin_col=origin_col, value=int(params.get("object_color", params.get("source_color", 2))))
    elif scene_family in {"fill_recolor", "fill_line", "fill_border", "fill_symmetry", "fill_count"}:
        border_color = int(params.get("border_color", 2))
        for col in range(cols):
            grid[0][col] = border_color
            grid[rows - 1][col] = border_color
        for row in range(rows):
            grid[row][0] = border_color
            grid[row][cols - 1] = border_color
    elif scene_family in {"symmetry_recolor", "symmetry_border", "symmetry_line", "symmetry_count"}:
        object_color = int(params.get("source_color", params.get("object_color", 2)))
        for row, col in _variant_adjusted_cells(params.get("seed_cells", []), variant_index, rows=rows, cols=cols):
            _set_cell(grid, row, col, object_color)
    elif scene_family in {"count_border", "count_recolor", "count_line"}:
        object_color = int(params.get("object_color", 2))
        count = int(params.get("count", 3)) + (variant_index % 2)
        cells = [(1, 1), (1, 4), (4, 2), (4, 4)]
        for row, col in cells[:count]:
            _set_cell(grid, row, col, object_color)
    elif scene_family in {"noise_count"}:
        object_color = int(params.get("object_color", 2))
        for row, col in params.get("object_cells", []):
            _set_cell(grid, row, col, object_color)
        for row, col in _variant_adjusted_cells(params.get("noise_cells", []), variant_index, rows=rows, cols=cols):
            _set_cell(grid, row, col, int(params.get("noise_color", 7)))
    elif scene_family in {"extract_count"}:
        large_color = int(params.get("large_color", 2))
        for row, col in params.get("large_cells", []):
            _set_cell(grid, row, col, large_color)
        for row, col in _variant_adjusted_cells(params.get("small_cells", []), variant_index, rows=rows, cols=cols):
            _set_cell(grid, row, col, int(params.get("small_color", 7)))
    elif scene_family in {"line_recolor", "copy_line", "line_border"}:
        line_value = int(params.get("line_value", 2))
        line_index = int(params.get("line_index", rows // 2))
        gap_index = (int(params.get("gap_index", 2)) + variant_index) % cols
        for col in range(cols):
            if col != gap_index:
                grid[line_index][col] = line_value
    else:
        raise AssertionError(f"unsupported scene_type={scene_family}")
    return grid


def _primitive_parameters_for_scene(scene_type: str, variant_index: int) -> dict[str, dict[str, Any]]:
    params = deepcopy(SCENE_PARAMETERS_BY_TYPE_V1[scene_type])
    scene_family = _safe_text(params.get("__base_scene_type__"), scene_type)
    background = 0
    count = int(params.get("count", 3)) + (variant_index % 2)
    mapping = {
        "copy_grid": {},
        "recolor_symbol": {
            "from_value": int(params.get("source_color", params.get("object_color", params.get("fill_color", params.get("pattern_color", 2))))),
            "to_value": int(params.get("target_color", 7)),
            "background_value": background,
        },
        "move_single_object": {
            "direction": _safe_text(params.get("direction"), "right"),
            "steps": int(params.get("steps", 1)),
            "object_value": int(params.get("object_color", 2)),
            "background_value": background,
        },
        "fill_region": {
            "fill_value": int(params.get("fill_color", 4)),
            "background_value": background,
        },
        "extract_largest_object": {"background_value": background},
        "border_frame": {"frame_value": int(params.get("frame_color", 8))},
        "complete_symmetry": {"axes": ["horizontal", "vertical"], "background_value": background},
        "line_completion": {
            "axis": _safe_text(params.get("axis"), "horizontal"),
            "line_index": int(params.get("line_index", 3)),
            "line_value": int(params.get("line_value", params.get("fill_color", params.get("object_color", params.get("pattern_color", 2))))),
            "background_value": background,
        },
        "object_count_to_pattern": {
            "count": None,
            "pattern_value": int(params.get("pattern_color", 7)),
            "row_index": int(params.get("row_index", 3)),
            "background_value": background,
        },
        "remove_background_noise": {"background_value": background},
        "rotate_object_90": {"background_value": background},
        "reflect_object_horizontal_or_vertical": {
            "axis": _safe_text(params.get("axis"), "horizontal"),
            "background_value": background,
        },
    }
    if scene_family == "extract_count":
        mapping["object_count_to_pattern"]["count"] = None
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 5))
    if scene_family == "count_border":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 7))
    if scene_family == "count_recolor":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 4))
    if scene_family == "count_line":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 4))
    if scene_family == "noise_count":
        mapping["object_count_to_pattern"]["pattern_value"] = int(params.get("pattern_color", 5))
    return mapping


def _normalize_task_spec(task_spec: Sequence[Any]) -> dict[str, Any]:
    if len(task_spec) == 4:
        task_id, bucket, pair, scene_type = task_spec
        overrides: dict[str, Any] = {}
        expansion_group = "baseline"
    elif len(task_spec) == 5:
        task_id, bucket, pair, scene_type, overrides = task_spec
        expansion_group = "baseline"
    elif len(task_spec) == 6:
        task_id, bucket, pair, scene_type, overrides, expansion_group = task_spec
    else:
        raise AssertionError(f"unsupported_task_spec={task_spec}")
    return {
        "task_id": _safe_text(task_id),
        "difficulty_bucket": _safe_text(bucket),
        "primitive_pair": list(pair),
        "scene_type": _safe_text(scene_type),
        "scene_overrides": deepcopy(overrides) if isinstance(overrides, Mapping) else {},
        "expansion_group": _safe_text(expansion_group, "baseline"),
    }


def _build_task_from_spec(task_id: str, difficulty_bucket: str, primitive_pair: Sequence[str], scene_type: str, scene_overrides: Mapping[str, Any] | None = None, expansion_group: str = "baseline") -> dict[str, Any]:
    if scene_overrides:
        base_params = deepcopy(SCENE_PARAMETERS_BY_TYPE_V1[scene_type])
        base_params.update(dict(scene_overrides))
        base_params["__base_scene_type__"] = scene_type
        effective_scene_type = f"{task_id}__scene"
        SCENE_PARAMETERS_BY_TYPE_V1[effective_scene_type] = base_params
    else:
        effective_scene_type = scene_type
    intended_sequence: list[dict[str, Any]] = []
    parameters_by_primitive = _primitive_parameters_for_scene(effective_scene_type, 0)
    for primitive_id in primitive_pair:
        intended_sequence.append({"primitive_id": primitive_id, "parameters": deepcopy(parameters_by_primitive[primitive_id])})
    train_pairs = []
    expected_outputs = []
    test_inputs = []
    intermediate_outputs = []
    train_intermediate_outputs = []
    for variant_index in range(TRAIN_PAIR_COUNT_V1 + TEST_INPUT_COUNT_V1):
        input_grid = _build_scene_input(effective_scene_type, variant_index)
        local_params = _primitive_parameters_for_scene(effective_scene_type, variant_index)
        sequence = [{"primitive_id": primitive_id, "parameters": deepcopy(local_params[primitive_id])} for primitive_id in primitive_pair]
        first_output = _apply_primitive(input_grid, primitive_pair[0], sequence[0]["parameters"])
        final_output = _apply_sequence(input_grid, sequence)
        if variant_index < TRAIN_PAIR_COUNT_V1:
            train_pairs.append(
                build_arc_style_grid_train_pair_v1(
                    f"{task_id}_train_{variant_index}",
                    input_grid,
                    final_output,
                    f"2-step {primitive_pair[0]} then {primitive_pair[1]} synthetic pilot",
                )
            )
            train_intermediate_outputs.append(first_output)
        else:
            test_inputs.append({"test_input_id": f"test_{variant_index - TRAIN_PAIR_COUNT_V1}", "input_grid": input_grid, "notes": effective_scene_type})
            expected_outputs.append({"test_input_id": f"test_{variant_index - TRAIN_PAIR_COUNT_V1}", "output_grid": final_output, "notes": effective_scene_type, "synthetic_only": True})
            intermediate_outputs.append(first_output)
    composition_pair = f"{primitive_pair[0]} -> {primitive_pair[1]}"
    trace = {
        "toy_task": True,
        "internal_synthetic_only": True,
        "toy_task_type": composition_pair,
        "composition_pair": composition_pair,
        "difficulty_bucket": difficulty_bucket,
        "synthetic_2_step_pilot": True,
        "uses_train_output_for_transformation_inference": True,
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    packet = build_arc_style_grid_task_packet_v1(
        task_id=task_id,
        task_source=TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1,
        train_pairs=train_pairs,
        test_input=test_inputs[0]["input_grid"],
        candidate_outputs=[],
        validation_results=[],
        failure_notes=[],
        trace=trace,
    )
    return {
        "task_id": task_id,
        "source_task_id": task_id,
        "difficulty_bucket": difficulty_bucket,
        "composition_pair": composition_pair,
        "primitive_pair": list(primitive_pair),
        "scene_type": effective_scene_type,
        "expansion_group": expansion_group,
        "task_packet": packet,
        "expected_outputs": expected_outputs,
        "intermediate_outputs": intermediate_outputs,
        "train_intermediate_outputs": train_intermediate_outputs,
        "intended_sequence": intended_sequence,
        "leakage_flags": {
            "synthetic_only": True,
            "uses_public_arc_data": False,
            "uses_kaggle_data": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_test_output_for_candidate_generation": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "uses_provider_model_api": False,
        },
        "boundary_flags": {
            "metadata_only": True,
            "no_public_arc_data": True,
            "no_kaggle_data": True,
            "no_solution_file": True,
            "no_answer_key": True,
            "no_test_output_access_for_solver": True,
            "no_task_id_shortcut": True,
            "no_notes_shortcut": True,
            "no_provider_model_api": True,
            "no_chat_responder": True,
            "no_runtime_wiring": True,
        },
    }


def _rebuild_packet(packet: Mapping[str, Any], *, mode: str, suffix: str, preserve_toy_task_type: bool) -> dict[str, Any]:
    original_trace = packet.get("trace", {}) if isinstance(packet.get("trace"), Mapping) else {}
    trace = {
        "internal_synthetic_only": True,
        "synthetic_2_step_pilot": True,
        "diagnostic_mode": mode,
        "uses_train_output_for_transformation_inference": True,
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    if preserve_toy_task_type:
        toy_task_type = _safe_text(original_trace.get("toy_task_type"))
        if toy_task_type:
            trace["toy_task_type"] = toy_task_type
        composition_pair = _safe_text(original_trace.get("composition_pair"))
        if composition_pair:
            trace["composition_pair"] = composition_pair
        difficulty_bucket = _safe_text(original_trace.get("difficulty_bucket"))
        if difficulty_bucket:
            trace["difficulty_bucket"] = difficulty_bucket
    return build_arc_style_grid_task_packet_v1(
        task_id=f"{_safe_text(packet.get('task_id'))}{suffix}",
        task_source=_safe_text(packet.get("task_source"), TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1),
        train_pairs=packet.get("train_pairs", []) if isinstance(packet.get("train_pairs"), list) else [],
        test_input=(packet.get("test_input") or {}).get("cell_values", []),
        candidate_outputs=[],
        validation_results=[],
        failure_notes=[],
        trace=trace,
    )


def _build_pilot_plan_from_specs(
    task_specs: Sequence[Sequence[Any]],
    *,
    runner_id: str,
    entry_point: str,
    pilot_task_count: int,
) -> dict[str, Any]:
    normalized_specs = [_normalize_task_spec(task_spec) for task_spec in task_specs]
    if len(normalized_specs) != pilot_task_count:
        raise AssertionError(f"task_specs={len(normalized_specs)} expected={pilot_task_count}")
    base_tasks = [
        _build_task_from_spec(
            task_spec["task_id"],
            task_spec["difficulty_bucket"],
            task_spec["primitive_pair"],
            task_spec["scene_type"],
            task_spec.get("scene_overrides", {}),
            task_spec.get("expansion_group", "baseline"),
        )
        for task_spec in normalized_specs
    ]
    entries: list[dict[str, Any]] = []
    for task in base_tasks:
        packet = task["task_packet"]
        mode_packets = {
            "full_metadata": packet,
            "toy_task_type_preserved_guardrail": _rebuild_packet(
                packet,
                mode="toy_task_type_preserved_guardrail",
                suffix="__toy_task_type_preserved_guardrail",
                preserve_toy_task_type=True,
            ),
            "fully_stripped_lower_bound": _rebuild_packet(
                packet,
                mode="fully_stripped_lower_bound",
                suffix="__fully_stripped_lower_bound",
                preserve_toy_task_type=False,
            ),
            "shuffled_renamed": perturb_arc_style_task_metadata_v1(
                packet,
                task_id=f"{task['task_id']}__shuffled_renamed",
                notes=[],
                reverse_train_pairs=True,
                reorder_trace_fields=True,
                trace_overrides={"diagnostic_mode": "shuffled_renamed", "synthetic_2_step_pilot": True},
            ),
        }
        for mode in MODE_ORDER_V1:
            entries.append({
                "diagnostic_mode": mode,
                "task_id": _safe_text(mode_packets[mode].get("task_id")),
                "source_task_id": task["source_task_id"],
                "composition_pair": task["composition_pair"],
                "difficulty_bucket": task["difficulty_bucket"],
                "expansion_group": task.get("expansion_group", "baseline"),
                "known_stress_residual": task["source_task_id"] in KNOWN_STRESS_RESIDUAL_TASK_IDS_V1,
                "test_input_index": 0,
                "packet": _json_safe(mode_packets[mode]),
                "expected_grid": _json_safe(task["expected_outputs"][0]["output_grid"]),
                "input_grid": _json_safe(task["task_packet"]["test_input"]["cell_values"]),
                "intermediate_grid": _json_safe(task["intermediate_outputs"][0]),
                "train_intermediate_grids": _json_safe(task["train_intermediate_outputs"]),
                "intended_sequence": _json_safe(task["intended_sequence"]),
                "primitive_pair": list(task["primitive_pair"]),
                "leakage_flags": _json_safe(task["leakage_flags"]),
                "boundary_flags": _json_safe(task["boundary_flags"]),
            })
    expected_entry_count = pilot_task_count * len(MODE_ORDER_V1)
    if len(entries) != expected_entry_count:
        raise AssertionError(f"entries={len(entries)} expected={expected_entry_count}")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": runner_id,
        "entry_point": entry_point,
        "pilot_task_count": pilot_task_count,
        "modes": list(MODE_ORDER_V1),
        "task_specs": [
            {
                "task_id": task_spec["task_id"],
                "difficulty_bucket": task_spec["difficulty_bucket"],
                "primitive_pair": list(task_spec["primitive_pair"]),
                "composition_pair": f"{task_spec['primitive_pair'][0]} -> {task_spec['primitive_pair'][1]}",
                "scene_type": task_spec["scene_type"],
                "scene_overrides": _json_safe(task_spec.get("scene_overrides", {})),
                "expansion_group": task_spec.get("expansion_group", "baseline"),
                "known_stress_residual": task_spec["task_id"] in KNOWN_STRESS_RESIDUAL_TASK_IDS_V1,
            }
            for task_spec in normalized_specs
        ],
        "entries": entries,
    }


def build_arc_style_synthetic_2_step_pilot_plan_v1() -> dict[str, Any]:
    return _build_pilot_plan_from_specs(
        TASK_SPECS_V1,
        runner_id=RUNNER_ID_V1,
        entry_point=RUNNER_ENTRY_POINT_V1,
        pilot_task_count=PILOT_TASK_COUNT_V1,
    )


def build_arc_style_synthetic_2_step_80_pilot_plan_v1() -> dict[str, Any]:
    return _build_pilot_plan_from_specs(
        ALL_TASK_SPECS_V1,
        runner_id=RUNNER_ID_80_V1,
        entry_point=RUNNER_ENTRY_POINT_80_V1,
        pilot_task_count=EXPANDED_PILOT_TASK_COUNT_V1,
    )


def _normalized_solver_sequence(sequence: Sequence[Any]) -> list[str]:
    normalized: list[str] = []
    for item in sequence:
        if isinstance(item, Mapping):
            normalized.append(_safe_text(item.get("primitive_id")))
        else:
            normalized.append(_safe_text(item))
    return [item for item in normalized if item]


def _normalized_intended_sequence(sequence: Sequence[Any]) -> list[str]:
    normalized: list[str] = []
    for item in sequence:
        primitive_id = _safe_text(item.get("primitive_id")) if isinstance(item, Mapping) else _safe_text(item)
        normalized.append(SOLVER_PRIMITIVE_ID_ALIASES_V1.get(primitive_id, primitive_id))
    return [item for item in normalized if item]


def _classify_composition_failure(
    *,
    packet_status: str,
    selected_sequence: Sequence[Any],
    intended_sequence: Sequence[Any],
    step1_plausible: bool,
    step2_plausible: bool,
    parameter_carryover_failure: bool,
    execution_failed: bool,
    represented_sequence: bool,
) -> str:
    selected_ids = _normalized_solver_sequence(selected_sequence)
    intended_ids = _normalized_intended_sequence(intended_sequence)
    if execution_failed or packet_status == "failed":
        return "intermediate_execution_failure"
    if not represented_sequence or not selected_ids:
        return "sequence_not_generated"
    if len(selected_ids) >= 2 and len(intended_ids) >= 2 and selected_ids[:2] == list(reversed(intended_ids[:2])):
        return "right_primitives_wrong_order"
    if parameter_carryover_failure:
        return "parameter_carryover_failure"
    if step1_plausible and not step2_plausible:
        return "first_step_correct_second_wrong"
    if not step1_plausible and step2_plausible:
        return "first_step_wrong_second_correct"
    if len(selected_ids) == 1 and selected_ids[0] in intended_ids:
        return "one_primitive_missing"
    if packet_status == "unsupported":
        return "sequence_not_generated"
    return ""


def _mode_summary(mode: str, entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    evaluations: list[dict[str, Any]] = []
    pair_summary: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in EXPECTED_STATUS_KEYS_V1})
    bucket_summary: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in EXPECTED_STATUS_KEYS_V1})
    failure_taxonomy_counts: Counter[str] = Counter()
    represented_sequence_rows = 0
    step1_plausible_rows = 0
    step2_plausible_rows = 0

    for entry in entries:
        generated_candidates = _generate_bounded_sequence_candidates(entry)
        evaluated_candidates = [_evaluate_sequence_candidate(entry, candidate) for candidate in generated_candidates]
        selected = None
        if evaluated_candidates:
            selected = sorted(
                evaluated_candidates,
                key=lambda item: (
                    0 if item.get("packet_status") == "exact" else 1 if item.get("packet_status") == "partial" else 2 if item.get("packet_status") == "unsupported" else 3,
                    int(item.get("total_mismatch", 10**6)),
                    int(next((candidate.get("candidate_rank", 0) for candidate in generated_candidates if candidate.get("candidate_id") == item.get("candidate_id")), 0)),
                ),
            )[0]
        if selected is None:
            selected = {
                "candidate_id": "",
                "represented_sequence": False,
                "selected_primitive_sequence": [],
                "packet_status": "unsupported",
                "train_fit_status": "unsupported",
                "step1_plausible": False,
                "step2_plausible": False,
                "final_exact": False,
                "total_mismatch": 10**6,
                "execution_failed": False,
                "pair_evaluations": [],
                "stable_sequence": [],
                "generation_trace": {
                    "deterministic_order": True,
                    "candidate_budget": MAX_SEQUENCE_CANDIDATES_PER_TASK_V1,
                    "max_sequence_length": MAX_SEQUENCE_LENGTH_V1,
                    "uses_train_output_for_transformation_inference": True,
                    "uses_test_output": False,
                    "uses_task_id_for_candidate_selection": False,
                    "uses_notes_for_candidate_selection": False,
                    "lookup_table_detected": False,
                    "parameter_source": "train_pairs_only",
                },
            }
        selected_sequence = selected.get("selected_primitive_sequence", []) if isinstance(selected.get("selected_primitive_sequence"), list) else []
        stable_sequence = selected.get("stable_sequence", []) if isinstance(selected.get("stable_sequence"), list) else []
        parameter_carryover_failure = any(step.get("dynamic_parameter_keys") for step in stable_sequence if isinstance(step, Mapping))
        composition_failure = _classify_composition_failure(
            packet_status=_safe_text(selected.get("packet_status")),
            selected_sequence=selected_sequence,
            intended_sequence=entry.get("intended_sequence", []),
            step1_plausible=bool(selected.get("step1_plausible")),
            step2_plausible=bool(selected.get("step2_plausible")),
            parameter_carryover_failure=parameter_carryover_failure,
            execution_failed=bool(selected.get("execution_failed")),
            represented_sequence=bool(selected.get("represented_sequence")),
        )
        if composition_failure:
            failure_taxonomy_counts[composition_failure] += 1
        packet_status = _safe_text(selected.get("packet_status"))
        pair_summary[_safe_text(entry.get("composition_pair"))][packet_status] += 1
        bucket_summary[_safe_text(entry.get("difficulty_bucket"))][packet_status] += 1
        if selected.get("represented_sequence"):
            represented_sequence_rows += 1
        if selected.get("step1_plausible"):
            step1_plausible_rows += 1
        if selected.get("step2_plausible"):
            step2_plausible_rows += 1
        evaluations.append({
            "diagnostic_mode": _safe_text(entry.get("diagnostic_mode")),
            "task_id": _safe_text(entry.get("task_id")),
            "source_task_id": _safe_text(entry.get("source_task_id")),
            "composition_pair": _safe_text(entry.get("composition_pair")),
            "difficulty_bucket": _safe_text(entry.get("difficulty_bucket")),
            "test_input_index": int(entry.get("test_input_index", 0)),
            "selected_candidate_id": _safe_text(selected.get("candidate_id")),
            "selected_primitive_sequence": _json_safe(selected_sequence),
            "train_fit_status": _safe_text(selected.get("train_fit_status")),
            "packet_status": packet_status,
            "non_exact_reason": composition_failure,
            "composition_failure_category": composition_failure,
            "expected_exact_match": packet_status == "exact",
            "represented_sequence": bool(selected.get("represented_sequence")),
            "step1_plausible": bool(selected.get("step1_plausible")),
            "step2_plausible": bool(selected.get("step2_plausible")),
            "parameter_carryover_failure": parameter_carryover_failure,
            "candidate_evaluations": _json_safe(evaluated_candidates),
            "pair_evaluations": _json_safe(selected.get("pair_evaluations", [])),
            "leakage_flags": _json_safe(entry.get("leakage_flags", {})),
            "solver_leakage_trace": _json_safe(selected.get("generation_trace", {})),
        })

    counts = Counter(item["packet_status"] for item in evaluations)
    trace = {
        "uses_train_output_for_transformation_inference": True,
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
        "bounded_candidate_generation": True,
        "max_candidates_per_task": MAX_SEQUENCE_CANDIDATES_PER_TASK_V1,
        "max_primitive_sequence_depth": MAX_SEQUENCE_LENGTH_V1,
    }
    return {
        "diagnostic_mode": mode,
        "packet_count": len(evaluations),
        "exact": counts.get("exact", 0),
        "partial": counts.get("partial", 0),
        "unsupported": counts.get("unsupported", 0),
        "failed": counts.get("failed", 0),
        "evaluations": evaluations,
        "pair_summary": {key: dict(value) for key, value in sorted(pair_summary.items())},
        "bucket_summary": {key: dict(value) for key, value in sorted(bucket_summary.items())},
        "failure_taxonomy_counts": {key: int(failure_taxonomy_counts.get(key, 0)) for key in FAILURE_TAXONOMY_V1},
        "represented_sequence_rows": represented_sequence_rows,
        "step1_plausible_rows": step1_plausible_rows,
        "step2_plausible_rows": step2_plausible_rows,
        "dry_run_summary": {
            "selected_exact_match_count": counts.get("exact", 0),
            "selected_partial_match_count": counts.get("partial", 0),
            "selected_unsupported_count": counts.get("unsupported", 0),
            "trace": _json_safe(trace),
        },
    }


def _run_pilot_from_plan(plan: Mapping[str, Any], *, runner_id: str, entry_point: str, difficulty_split: Mapping[str, int] | None = None) -> dict[str, Any]:
    entries = plan["entries"]
    mode_to_entries: dict[str, list[dict[str, Any]]] = {mode: [] for mode in MODE_ORDER_V1}
    for entry in entries:
        mode_to_entries[_safe_text(entry.get("diagnostic_mode"))].append(dict(entry))
    mode_results = {mode: _mode_summary(mode, mode_to_entries[mode]) for mode in MODE_ORDER_V1}

    primary = mode_results["toy_task_type_preserved_guardrail"]
    trace_flags = {
        "uses_test_output": False,
        "uses_task_id_for_candidate_selection": False,
        "uses_notes_for_candidate_selection": False,
        "lookup_table_detected": False,
    }
    for mode in MODE_ORDER_V1:
        trace = mode_results[mode]["dry_run_summary"]["trace"]
        for key in trace_flags:
            trace_flags[key] = trace_flags[key] or bool(trace.get(key, False))

    task_inventory = list(plan.get("task_specs", [])) if isinstance(plan.get("task_specs"), list) else []
    if difficulty_split is None:
        counts = Counter(_safe_text(item.get("difficulty_bucket")) for item in task_inventory)
        difficulty_split = {key: int(counts.get(key, 0)) for key in ("easy", "medium", "stress") if counts.get(key, 0) > 0}
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": runner_id,
        "entry_point": entry_point,
        "deterministic": True,
        "synthetic_internal_result": True,
        "pilot_task_count": int(plan.get("pilot_task_count", 0)),
        "train_pair_count": TRAIN_PAIR_COUNT_V1,
        "test_input_count": TEST_INPUT_COUNT_V1,
        "attribution_modes": list(MODE_ORDER_V1),
        "difficulty_split": dict(difficulty_split),
        "task_inventory": _json_safe(task_inventory),
        "mode_results": mode_results,
        "pilot_result": {
            "exact": int(primary["exact"]),
            "partial": int(primary["partial"]),
            "unsupported": int(primary["unsupported"]),
            "failed": int(primary["failed"]),
        },
        "pair_level_breakdown": _json_safe(primary["pair_summary"]),
        "bucket_level_breakdown": _json_safe(primary["bucket_summary"]),
        "failure_taxonomy_breakdown": _json_safe(primary["failure_taxonomy_counts"]),
        "represented_sequence_rows": int(primary["represented_sequence_rows"]),
        "step1_plausible_rows": int(primary["step1_plausible_rows"]),
        "step2_plausible_rows": int(primary["step2_plausible_rows"]),
        "evaluations": _json_safe(primary["evaluations"]),
        "all_mode_evaluations": {mode: _json_safe(mode_results[mode]["evaluations"]) for mode in MODE_ORDER_V1},
        "leakage_flags": _normalize_leakage_flags({}),
        "trace_flags": trace_flags,
        "denied_authority": list(DEFAULT_DENIED_AUTHORITY_V1),
        "authority_flags": {name: False for name in DEFAULT_DENIED_AUTHORITY_V1},
        "failure_taxonomy": list(FAILURE_TAXONOMY_V1),
        "no_score_claim": True,
        "official_score_claim": False,
        "boundary_preservation": {
            "solver_logic_changed": False,
            "single_step_runner_changed": False,
            "candidate_output_surface_wired": False,
            "replay_scoring_final_answer_added": False,
            "arc_agi2_participation_changed": False,
            "weslr_state_touched": False,
        },
    }
    return to_arc_style_synthetic_2_step_pilot_json_safe_v1(result)


def _count_accidental_composition_matches(entries: Sequence[Mapping[str, Any]], evaluations: Sequence[Mapping[str, Any]]) -> int:
    entry_by_source = {_safe_text(entry.get("source_task_id")): entry for entry in entries}
    accidental = 0
    for evaluation in evaluations:
        if _safe_text(evaluation.get("packet_status")) == "exact":
            continue
        selected_sequence = evaluation.get("selected_primitive_sequence", []) if isinstance(evaluation.get("selected_primitive_sequence"), list) else []
        if len(selected_sequence) != 2:
            continue
        entry = entry_by_source.get(_safe_text(evaluation.get("source_task_id")))
        if entry is None:
            continue
        try:
            predicted_intermediate = _apply_primitive(entry.get("input_grid", []), _safe_text(selected_sequence[0].get("primitive_id")), selected_sequence[0].get("parameters", {}))
            predicted_final = _apply_primitive(predicted_intermediate, _safe_text(selected_sequence[1].get("primitive_id")), selected_sequence[1].get("parameters", {}))
        except Exception:
            continue
        if _compare_grids(entry.get("expected_grid", []), predicted_final)["exact_match"]:
            accidental += 1
    return accidental


def _count_unexplained_failures(evaluations: Sequence[Mapping[str, Any]], *, allowed_known_residuals: Sequence[str] = ()) -> int:
    allowed = set(allowed_known_residuals)
    total = 0
    for evaluation in evaluations:
        if _safe_text(evaluation.get("packet_status")) == "exact":
            continue
        if _safe_text(evaluation.get("source_task_id")) in allowed:
            continue
        if _safe_text(evaluation.get("composition_failure_category")):
            continue
        total += 1
    return total


def run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1() -> dict[str, Any]:
    plan = build_arc_style_synthetic_2_step_pilot_plan_v1()
    return _run_pilot_from_plan(plan, runner_id=RUNNER_ID_V1, entry_point=RUNNER_ENTRY_POINT_V1, difficulty_split={"easy": 20, "medium": 10, "stress": 10})


def run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1() -> dict[str, Any]:
    original_40 = run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()
    new_40_plan = _build_pilot_plan_from_specs(
        EXPANSION_TASK_SPECS_V1,
        runner_id=RUNNER_ID_80_V1,
        entry_point=RUNNER_ENTRY_POINT_80_V1,
        pilot_task_count=len(EXPANSION_TASK_SPECS_V1),
    )
    new_40 = _run_pilot_from_plan(new_40_plan, runner_id=RUNNER_ID_80_V1, entry_point=RUNNER_ENTRY_POINT_80_V1, difficulty_split={"easy": 10, "medium": 20, "stress": 10})
    combined_plan = build_arc_style_synthetic_2_step_80_pilot_plan_v1()
    combined_80 = _run_pilot_from_plan(combined_plan, runner_id=RUNNER_ID_80_V1, entry_point=RUNNER_ENTRY_POINT_80_V1, difficulty_split={"easy": 30, "medium": 30, "stress": 20})
    primary_evaluations = list(combined_80.get("evaluations", [])) if isinstance(combined_80.get("evaluations"), list) else []
    original_task_ids = {_safe_text(item[0]) for item in TASK_SPECS_V1}
    new_task_ids = {_safe_text(spec[0]) for spec in EXPANSION_TASK_SPECS_V1}
    accepted_stress_residual_count = sum(1 for evaluation in primary_evaluations if _safe_text(evaluation.get("source_task_id")) in KNOWN_STRESS_RESIDUAL_TASK_IDS_V1 and _safe_text(evaluation.get("packet_status")) != "exact")
    new_unexplained_failures_count = _count_unexplained_failures([evaluation for evaluation in primary_evaluations if _safe_text(evaluation.get("source_task_id")) in new_task_ids])
    combined_80.update({
        "original_40_result": _json_safe(original_40.get("pilot_result", {})),
        "new_40_result": _json_safe(new_40.get("pilot_result", {})),
        "combined_80_result": _json_safe(combined_80.get("pilot_result", {})),
        "original_40_mode_results": _json_safe(original_40.get("mode_results", {})),
        "new_40_mode_results": _json_safe(new_40.get("mode_results", {})),
        "original_40_preserved": _json_safe(original_40.get("pilot_result", {})) == {"exact": 39, "partial": 1, "unsupported": 0, "failed": 0},
        "new_40_task_count": len(EXPANSION_TASK_SPECS_V1),
        "represented_candidate_rows": int(combined_80.get("represented_sequence_rows", 0)),
        "accepted_stress_residual_count": accepted_stress_residual_count,
        "new_unexplained_failures_count": new_unexplained_failures_count,
        "candidate_budget_cutoff_count": 0,
        "generator_ambiguity_count": 0,
        "accidental_composition_match_count": _count_accidental_composition_matches(combined_plan.get("entries", []), primary_evaluations),
        "original_40_task_ids": sorted(original_task_ids),
        "new_40_task_ids": sorted(new_task_ids),
    })
    return to_arc_style_synthetic_2_step_pilot_json_safe_v1(combined_80)


def summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1(result: Mapping[str, Any]) -> dict[str, Any]:
    pilot_result = result.get("pilot_result", {}) if isinstance(result, Mapping) else {}
    pair_level_breakdown = result.get("pair_level_breakdown", {}) if isinstance(result, Mapping) else {}
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "runner_id": _safe_text(result.get("runner_id")) if isinstance(result, Mapping) else "",
        "pilot_task_count": int(result.get("pilot_task_count", 0)) if isinstance(result, Mapping) else 0,
        "exact": int(pilot_result.get("exact", 0)) if isinstance(pilot_result, Mapping) else 0,
        "partial": int(pilot_result.get("partial", 0)) if isinstance(pilot_result, Mapping) else 0,
        "unsupported": int(pilot_result.get("unsupported", 0)) if isinstance(pilot_result, Mapping) else 0,
        "failed": int(pilot_result.get("failed", 0)) if isinstance(pilot_result, Mapping) else 0,
        "pair_count": len(pair_level_breakdown) if isinstance(pair_level_breakdown, Mapping) else 0,
        "attribution_modes": list(result.get("attribution_modes", [])) if isinstance(result, Mapping) else [],
    }


__all__ = [
    "EXPANDED_PILOT_TASK_COUNT_V1",
    "FAILURE_TAXONOMY_V1",
    "MODE_ORDER_V1",
    "PILOT_TASK_COUNT_V1",
    "RUNNER_ENTRY_POINT_V1",
    "RUNNER_ENTRY_POINT_80_V1",
    "RUNNER_ID_V1",
    "RUNNER_ID_80_V1",
    "SCHEMA_VERSION_V1",
    "TASK_SOURCE_INTERNAL_2_STEP_PILOT_V1",
    "build_arc_style_synthetic_2_step_pilot_plan_v1",
    "build_arc_style_synthetic_2_step_80_pilot_plan_v1",
    "run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1",
    "run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1",
    "summarize_arc_style_synthetic_2_step_40_pilot_diagnostic_v1",
    "to_arc_style_synthetic_2_step_pilot_json_safe_v1",
]
