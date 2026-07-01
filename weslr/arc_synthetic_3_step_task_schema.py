"""ARC Synthetic 3‑Step Task Schema and Diagnostic Packet Generator

Provides a static schema for the 3‑step ARC synthetic pilot and a generator that
produces the 20 diagnostic task packets. No execution of primitives occurs
and no external calls are made.
"""

from __future__ import annotations

from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Core families – defined in the pilot design (8 families)
# ---------------------------------------------------------------------------
CORE_FAMILIES: List[Dict[str, Any]] = [
    {
        "family_id": "F001",
        "primitive_sequence": ["extract", "rotate", "recolor"],
        "difficulty": "medium",
        "allowed_dynamic_parameters": ["rotation_angle", "colour_map"],
    },
    {
        "family_id": "F002",
        "primitive_sequence": ["remove_noise", "extract_object", "recolor"],
        "difficulty": "easy",
        "allowed_dynamic_parameters": ["noise_level", "colour_map"],
    },
    {
        "family_id": "F003",
        "primitive_sequence": ["fill_region", "count_objects", "pattern_output"],
        "difficulty": "hard",
        "allowed_dynamic_parameters": ["region_shape", "pattern_type"],
    },
    {
        "family_id": "F004",
        "primitive_sequence": ["crop_object", "transform", "place_back"],
        "difficulty": "medium",
        "allowed_dynamic_parameters": ["crop_box", "transform_params"],
    },
    {
        "family_id": "F005",
        "primitive_sequence": ["extract_boundary", "recolor_boundary", "count"],
        "difficulty": "easy",
        "allowed_dynamic_parameters": ["boundary_style", "colour_map"],
    },
    {
        "family_id": "F006",
        "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"],
        "difficulty": "medium",
        "allowed_dynamic_parameters": ["normalisation_method", "colour_map"],
    },
    {
        "family_id": "F007",
        "primitive_sequence": ["mirror_object", "extract_changed_region", "recolor"],
        "difficulty": "medium",
        "allowed_dynamic_parameters": ["mirror_axis", "change_threshold", "colour_map"],
    },
    {
        "family_id": "F008",
        "primitive_sequence": ["crop", "rotate", "count_or_pattern"],
        "difficulty": "easy",
        "allowed_dynamic_parameters": ["crop_box", "angle", "pattern_type"],
    },
]

# ---------------------------------------------------------------------------
# Fixed helper constants – must stay false/true as required by the pilot
# ---------------------------------------------------------------------------
FORBIDDEN_SHORTCUTS = ["expected_test_output", "task_id_shortcut", "generator_note_shortcut"]

LEAKAGE_FLAGS_TEMPLATE: Dict[str, bool] = {
    "arc_agi_participation_claim": False,
    "leaderboard_claim": False,
    "hidden_test_use": False,
    "public_claim": False,
    "final_answer_wiring": False,
    "weslr_persistence": False,
    "external_calls": False,
    "provider_model_calls": False,
    "runtime_chat_wiring": False,
}

TRACE_REQUIREMENTS_TEMPLATE: Dict[str, bool] = {
    "step_1_exports": True,
    "step_2_imports": True,
    "step_2_exports": True,
    "step_3_imports": True,
    "carried_parameters_by_edge": True,
    "dropped_parameters_by_edge": True,
    "parameter_origin_by_step": True,
    "intermediate_grid_1_summary": True,
    "intermediate_grid_2_summary": True,
    "failure_step": True,
    "failure_reason": True,
    "sequence_visibility_reason": True,
}

EXPECTED_FAILURE_CATEGORIES = [
    "rotation_out_of_bounds",
    "object_missing",
    "count_mismatch",
    "alignment_error",
    "parameter_drift",
]

# ---------------------------------------------------------------------------
# Minimal static scene specification (placeholder only)
# ---------------------------------------------------------------------------
def _make_scene_spec(family_id: str, variant_index: int) -> Dict[str, Any]:
    return {
        "grid_size": [10, 10],
        "initial_objects": [
            {
                "object_id": f"obj_{family_id}_{variant_index}",
                "type": "generic",
                "attributes": {"color": "red", "position": [0, 0]},
            }
        ],
    }

# ---------------------------------------------------------------------------
# Diagnostic‑only generator for the 20‑task pilot
# ---------------------------------------------------------------------------
def generate_3_step_pilot_tasks() -> List[Dict[str, Any]]:
    """Create the 20 diagnostic task dictionaries.

    The first four families provide three variants each, the remaining four families
    provide two variants each (4 × 3 + 4 × 2 = 20).
    """
    tasks: List[Dict[str, Any]] = []
    for idx, family in enumerate(CORE_FAMILIES):
        variant_count = 3 if idx < 4 else 2
        for v in range(variant_count):
            task_id = f"{family['family_id']}_{v + 1}"
            task = {
                "task_id": task_id,
                "family_id": family["family_id"],
                "difficulty": family["difficulty"],
                "primitive_sequence": family["primitive_sequence"].copy(),
                "scene_spec": _make_scene_spec(family["family_id"], v + 1),
                "train_pair_count": 1,
                "test_input_count": 1,
                "expected_trace_requirements": TRACE_REQUIREMENTS_TEMPLATE.copy(),
                "allowed_dynamic_parameters": family["allowed_dynamic_parameters"].copy(),
                "forbidden_shortcuts": FORBIDDEN_SHORTCUTS.copy(),
                "leakage_flags": LEAKAGE_FLAGS_TEMPLATE.copy(),
                "expected_failure_categories": EXPECTED_FAILURE_CATEGORIES.copy(),
            }
            tasks.append(task)
    return tasks

# ---------------------------------------------------------------------------
# Shallow validator used by the unit test suite
# ---------------------------------------------------------------------------
def validate_task_schema(task: Dict[str, Any]) -> None:
    required_keys = {
        "task_id",
        "family_id",
        "difficulty",
        "primitive_sequence",
        "scene_spec",
        "train_pair_count",
        "test_input_count",
        "expected_trace_requirements",
        "allowed_dynamic_parameters",
        "forbidden_shortcuts",
        "leakage_flags",
        "expected_failure_categories",
    }
    missing = required_keys - set(task.keys())
    if missing:
        raise ValueError(f"Task missing required keys: {missing}")
    if len(task["primitive_sequence"]) != 3:
        raise ValueError("primitive_sequence must contain exactly three primitives")
    for flag, val in LEAKAGE_FLAGS_TEMPLATE.items():
        if task["leakage_flags"].get(flag) is not False:
            raise ValueError(f"Leakage flag {flag} must be False")
    for req, val in TRACE_REQUIREMENTS_TEMPLATE.items():
        if task["expected_trace_requirements"].get(req) is not True:
            raise ValueError(f"Trace requirement {req} must be True")

# End of module
