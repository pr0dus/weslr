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
# 40‑task Batch‑5 primitive stress expansion generator
# ---------------------------------------------------------------------------

def generate_40_task_expansion() -> List[Dict[str, Any]]:
    """Generate the full 40‑task set for the Batch‑5 stress expansion.

    Returns a list containing the 20 baseline tasks (as produced by
    ``generate_3_step_pilot_tasks``) followed by 20 newly designed tasks (T21‑T40).
    Each new task stresses the three primitives ``extract_boundary``, ``mirror_object``
    and ``crop`` in various orders and edge‑case configurations.
    """
    # Preserve the baseline tasks
    tasks: List[Dict[str, Any]] = generate_3_step_pilot_tasks()

    # Specification of the 20 new tasks (mirroring the design report)
    new_tasks_spec = [
        {"task_id": "T21", "family_id": "A", "difficulty": "easy",
         "primitive_sequence": ["extract_boundary", "mirror_object", "crop"],
         "edge_case": "centered single object, simple shape"},
        {"task_id": "T22", "family_id": "A", "difficulty": "easy",
         "primitive_sequence": ["extract_boundary", "crop", "mirror_object"],
         "edge_case": "centered object, square bbox"},
        {"task_id": "T23", "family_id": "B", "difficulty": "medium",
         "primitive_sequence": ["mirror_object", "extract_boundary", "crop"],
         "edge_case": "asymmetric shape requiring correct mirroring"},
        {"task_id": "T24", "family_id": "B", "difficulty": "medium",
         "primitive_sequence": ["mirror_object", "crop", "extract_boundary"],
         "edge_case": "multi‑object scene, mirror creates overlap"},
        {"task_id": "T25", "family_id": "A", "difficulty": "medium",
         "primitive_sequence": ["crop", "extract_boundary", "mirror_object"],
         "edge_case": "object near image edge, bbox clipping"},
        {"task_id": "T26", "family_id": "A", "difficulty": "medium",
         "primitive_sequence": ["crop", "mirror_object", "extract_boundary"],
         "edge_case": "object touches multiple edges"},
        {"task_id": "T27", "family_id": "B", "difficulty": "hard",
         "primitive_sequence": ["extract_boundary", "mirror_object", "crop"],
         "edge_case": "non‑centered object, off‑center bbox"},
        {"task_id": "T28", "family_id": "B", "difficulty": "hard",
         "primitive_sequence": ["extract_boundary", "crop", "mirror_object"],
         "edge_case": "multi‑object with overlapping bboxes"},
        {"task_id": "T29", "family_id": "A", "difficulty": "hard",
         "primitive_sequence": ["mirror_object", "extract_boundary", "crop"],
         "edge_case": "asymmetric shape with distractor colors"},
        {"task_id": "T30", "family_id": "A", "difficulty": "hard",
         "primitive_sequence": ["mirror_object", "crop", "extract_boundary"],
         "edge_case": "scene with distractor colors and background noise"},
        {"task_id": "T31", "family_id": "B", "difficulty": "easy",
         "primitive_sequence": ["crop", "extract_boundary", "mirror_object"],
         "edge_case": "simple L‑shaped object, clear bbox"},
        {"task_id": "T32", "family_id": "B", "difficulty": "easy",
         "primitive_sequence": ["crop", "mirror_object", "extract_boundary"],
         "edge_case": "single vertical rectangle, mirror test"},
        {"task_id": "T33", "family_id": "A", "difficulty": "medium",
         "primitive_sequence": ["extract_boundary", "mirror_object", "crop"],
         "edge_case": "object with hole (donut) – bbox must ignore hole"},
        {"task_id": "T34", "family_id": "A", "difficulty": "medium",
         "primitive_sequence": ["extract_boundary", "crop", "mirror_object"],
         "edge_case": "object rotated 45°, bbox must be tight"},
        {"task_id": "T35", "family_id": "B", "difficulty": "medium",
         "primitive_sequence": ["mirror_object", "extract_boundary", "crop"],
         "edge_case": "two objects, one mirrored, one not"},
        {"task_id": "T36", "family_id": "B", "difficulty": "medium",
         "primitive_sequence": ["mirror_object", "crop", "extract_boundary"],
         "edge_case": "overlapping objects, mirror changes ordering"},
        {"task_id": "T37", "family_id": "A", "difficulty": "hard",
         "primitive_sequence": ["crop", "extract_boundary", "mirror_object"],
         "edge_case": "object spanning whole canvas, crop must keep size"},
        {"task_id": "T38", "family_id": "A", "difficulty": "hard",
         "primitive_sequence": ["crop", "mirror_object", "extract_boundary"],
         "edge_case": "very small object, precision of bbox critical"},
        {"task_id": "T39", "family_id": "B", "difficulty": "hard",
         "primitive_sequence": ["extract_boundary", "mirror_object", "crop"],
         "edge_case": "asymmetric multi‑color object, mirror must preserve colors"},
        {"task_id": "T40", "family_id": "B", "difficulty": "hard",
         "primitive_sequence": ["extract_boundary", "crop", "mirror_object"],
         "edge_case": "object clipped at canvas boundary, bbox must be clipped correctly"},
    ]

    for spec in new_tasks_spec:
        task = {
            "task_id": spec["task_id"],
            "family_id": spec["family_id"],
            "difficulty": spec["difficulty"],
            "primitive_sequence": spec["primitive_sequence"].copy(),
            "scene_spec": _make_scene_spec(spec["task_id"], 1),
            "train_pair_count": 1,
            "test_input_count": 1,
            "expected_trace_requirements": TRACE_REQUIREMENTS_TEMPLATE.copy(),
            "allowed_dynamic_parameters": [],
            "forbidden_shortcuts": FORBIDDEN_SHORTCUTS.copy(),
            "leakage_flags": LEAKAGE_FLAGS_TEMPLATE.copy(),
            "expected_failure_categories": [],
            "edge_case_flags": {"description": spec["edge_case"]},
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

# ---------------------------------------------------------------------------
# Broad‑Hard‑80 generator (deterministic, no randomness)
# ---------------------------------------------------------------------------

# Core primitive boundary
_BH80_ALLOWED_CORE = {
    "extract", "extract_largest_object", "isolate_largest", "extract_boundary",
    "crop", "mirror_object", "rotate", "recolor", "normalize_position",
    "place_back", "count_objects", "pattern_output", "transform",
}

# Approved aliases that map to dispatch wrappers or adapters
_BH80_ALLOWED_ALIASES = {
    "remove_noise", "extract_object", "crop_object", "recolor_boundary",
    "count", "count_or_pattern", "extract_changed_region", "fill_region",
}

_BH80_ALL_ALLOWED = _BH80_ALLOWED_CORE | _BH80_ALLOWED_ALIASES

# Deterministic task specifications extracted from the accepted Broad‑Hard‑80 design.
_BROAD_HARD_80_SPECS: List[Dict[str, Any]] = [
    {"task_id": "BH80_001", "family_id": "F001", "difficulty": "medium", "primitive_sequence": ["extract", "rotate", "recolor"], "hardness_axes": [1, 5], "shortcut_defeated": "Order‑independence"},
    {"task_id": "BH80_002", "family_id": "F001", "difficulty": "hard", "primitive_sequence": ["extract", "rotate", "recolor"], "hardness_axes": [1, 3, 5, 7], "shortcut_defeated": "Largest‑object shortcut"},
    {"task_id": "BH80_003", "family_id": "F002", "difficulty": "medium", "primitive_sequence": ["remove_noise", "extract_object", "recolor"], "hardness_axes": [1, 3], "shortcut_defeated": "Noise‑ignore shortcut"},
    {"task_id": "BH80_004", "family_id": "F002", "difficulty": "hard", "primitive_sequence": ["remove_noise", "extract_object", "recolor"], "hardness_axes": [1, 2, 3, 7], "shortcut_defeated": "First‑object shortcut"},
    {"task_id": "BH80_005", "family_id": "F003", "difficulty": "hard", "primitive_sequence": ["fill_region", "count_objects", "pattern_output"], "hardness_axes": [2, 4, 5, 8], "shortcut_defeated": "Count‑only shortcut"},
    {"task_id": "BH80_006", "family_id": "F003", "difficulty": "hard", "primitive_sequence": ["fill_region", "count_objects", "pattern_output"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Simple‑fill shortcut"},
    {"task_id": "BH80_007", "family_id": "F004", "difficulty": "medium", "primitive_sequence": ["crop_object", "transform", "place_back"], "hardness_axes": [1, 5], "shortcut_defeated": "Bbox‑invariance shortcut"},
    {"task_id": "BH80_008", "family_id": "F004", "difficulty": "hard", "primitive_sequence": ["crop_object", "transform", "place_back"], "hardness_axes": [1, 4, 5, 9], "shortcut_defeated": "Identity‑invariance shortcut"},
    {"task_id": "BH80_009", "family_id": "F005", "difficulty": "medium", "primitive_sequence": ["extract_boundary", "recolor_boundary", "count"], "hardness_axes": [1, 4], "shortcut_defeated": "Interior‑count shortcut"},
    {"task_id": "BH80_010", "family_id": "F005", "difficulty": "hard", "primitive_sequence": ["extract_boundary", "recolor_boundary", "count"], "hardness_axes": [2, 3, 4, 7], "shortcut_defeated": "Single‑boundary shortcut"},
    {"task_id": "BH80_011", "family_id": "F006", "difficulty": "medium", "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"], "hardness_axes": [1, 2], "shortcut_defeated": "First‑component shortcut"},
    {"task_id": "BH80_012", "family_id": "F006", "difficulty": "hard", "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"], "hardness_axes": [1, 2, 3, 5, 8], "shortcut_defeated": "Size‑tie shortcut"},
    {"task_id": "BH80_013", "family_id": "F007", "difficulty": "medium", "primitive_sequence": ["mirror_object", "extract_changed_region", "recolor"], "hardness_axes": [1, 5], "shortcut_defeated": "Symmetry shortcut"},
    {"task_id": "BH80_014", "family_id": "F007", "difficulty": "hard", "primitive_sequence": ["mirror_object", "extract_changed_region", "recolor"], "hardness_axes": [1, 3, 5, 7, 9], "shortcut_defeated": "Mirror‑invariance shortcut"},
    {"task_id": "BH80_015", "family_id": "F008", "difficulty": "medium", "primitive_sequence": ["crop", "rotate", "count_or_pattern"], "hardness_axes": [1, 5], "shortcut_defeated": "Pre‑crop shortcut"},
    {"task_id": "BH80_016", "family_id": "F008", "difficulty": "hard", "primitive_sequence": ["crop", "rotate", "count_or_pattern"], "hardness_axes": [1, 4, 5, 6, 9], "shortcut_defeated": "Count‑first shortcut"},
    {"task_id": "BH80_017", "family_id": "F003", "difficulty": "adversarial", "primitive_sequence": ["fill_region", "count_objects", "pattern_output"], "hardness_axes": [2, 3, 4, 5, 6, 8, 9], "shortcut_defeated": "Fill‑all shortcut"},
    {"task_id": "BH80_018", "family_id": "F006", "difficulty": "adversarial", "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"], "hardness_axes": [1, 2, 3, 4, 5, 6, 8], "shortcut_defeated": "Largest‑first shortcut"},
    {"task_id": "BH80_019", "family_id": "BH‑A", "difficulty": "medium", "primitive_sequence": ["extract_boundary", "mirror_object", "crop"], "hardness_axes": [1, 5], "shortcut_defeated": "Order‑independence"},
    {"task_id": "BH80_020", "family_id": "BH‑A", "difficulty": "medium", "primitive_sequence": ["mirror_object", "extract_boundary", "crop"], "hardness_axes": [1, 5, 7], "shortcut_defeated": "Post‑mirror‑boundary shortcut"},
    {"task_id": "BH80_021", "family_id": "BH‑A", "difficulty": "hard", "primitive_sequence": ["extract_boundary", "crop", "mirror_object"], "hardness_axes": [1, 4, 5, 7], "shortcut_defeated": "Bbox‑stable shortcut"},
    {"task_id": "BH80_022", "family_id": "BH‑A", "difficulty": "hard", "primitive_sequence": ["crop", "extract_boundary", "mirror_object"], "hardness_axes": [1, 4, 5, 9], "shortcut_defeated": "Boundary‑invariance shortcut"},
    {"task_id": "BH80_023", "family_id": "BH‑A", "difficulty": "adversarial", "primitive_sequence": ["extract_boundary", "mirror_object", "crop"], "hardness_axes": [1, 2, 3, 5, 6, 7, 8], "shortcut_defeated": "Largest‑object shortcut"},
    {"task_id": "BH80_024", "family_id": "BH‑A", "difficulty": "hard", "primitive_sequence": ["mirror_object", "crop", "extract_boundary"], "hardness_axes": [1, 4, 5, 7, 8], "shortcut_defeated": "Mirror‑then‑crop shortcut"},
    {"task_id": "BH80_025", "family_id": "BH‑A", "difficulty": "adversarial", "primitive_sequence": ["crop", "mirror_object", "extract_boundary"], "hardness_axes": [1, 3, 4, 5, 6, 7, 9], "shortcut_defeated": "Crop‑equals‑extract shortcut"},
    {"task_id": "BH80_026", "family_id": "BH‑A", "difficulty": "adversarial", "primitive_sequence": ["extract_boundary", "crop", "mirror_object"], "hardness_axes": [1, 2, 3, 4, 5, 6, 8], "shortcut_defeated": "Boundary‑equals‑extract shortcut"},
    {"task_id": "BH80_027", "family_id": "BH‑A", "difficulty": "hard", "primitive_sequence": ["mirror_object", "crop", "extract_boundary"], "hardness_axes": [1, 4, 5, 7, 9], "shortcut_defeated": "Mirror‑invariance shortcut"},
    {"task_id": "BH80_028", "family_id": "BH‑A", "difficulty": "hard", "primitive_sequence": ["crop", "extract_boundary", "mirror_object"], "hardness_axes": [1, 3, 5, 7, 8], "shortcut_defeated": "First‑crop shortcut"},
    {"task_id": "BH80_029", "family_id": "BH‑B", "difficulty": "medium", "primitive_sequence": ["isolate_largest", "rotate", "normalize_position"], "hardness_axes": [1, 5], "shortcut_defeated": "Order‑independence"},
    {"task_id": "BH80_030", "family_id": "BH‑B", "difficulty": "medium", "primitive_sequence": ["rotate", "isolate_largest", "normalize_position"], "hardness_axes": [1, 2, 5], "shortcut_defeated": "Pre‑rotate shortcut"},
    {"task_id": "BH80_031", "family_id": "BH‑B", "difficulty": "hard", "primitive_sequence": ["isolate_largest", "normalize_position", "rotate"], "hardness_axes": [1, 2, 4, 5], "shortcut_defeated": "First‑object shortcut"},
    {"task_id": "BH80_032", "family_id": "BH‑B", "difficulty": "hard", "primitive_sequence": ["normalize_position", "isolate_largest", "rotate"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Position‑invariance shortcut"},
    {"task_id": "BH80_033", "family_id": "BH‑B", "difficulty": "hard", "primitive_sequence": ["rotate", "normalize_position", "isolate_largest"], "hardness_axes": [1, 3, 4, 5, 7], "shortcut_defeated": "Rotation‑invariance shortcut"},
    {"task_id": "BH80_034", "family_id": "BH‑B", "difficulty": "adversarial", "primitive_sequence": ["isolate_largest", "rotate", "normalize_position"], "hardness_axes": [1, 2, 3, 5, 6, 8, 9], "shortcut_defeated": "Largest‑first shortcut"},
    {"task_id": "BH80_035", "family_id": "BH‑B", "difficulty": "adversarial", "primitive_sequence": ["normalize_position", "rotate", "isolate_largest"], "hardness_axes": [1, 2, 3, 4, 5, 6, 8], "shortcut_defeated": "Normalize‑noop shortcut"},
    {"task_id": "BH80_036", "family_id": "BH‑B", "difficulty": "adversarial", "primitive_sequence": ["rotate", "isolate_largest", "normalize_position"], "hardness_axes": [1, 2, 3, 4, 5, 6, 9], "shortcut_defeated": "Rotate‑identity shortcut"},
    {"task_id": "BH80_037", "family_id": "BH‑B", "difficulty": "hard", "primitive_sequence": ["isolate_largest", "normalize_position", "rotate"], "hardness_axes": [1, 2, 4, 5, 9], "shortcut_defeated": "Size‑only shortcut"},
    {"task_id": "BH80_038", "family_id": "BH‑B", "difficulty": "hard", "primitive_sequence": ["normalize_position", "isolate_largest", "rotate"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Normalize‑then‑select shortcut"},
    {"task_id": "BH80_039", "family_id": "BH‑C", "difficulty": "medium", "primitive_sequence": ["extract", "rotate", "recolor"], "hardness_axes": [1, 3], "shortcut_defeated": "Single‑object shortcut"},
    {"task_id": "BH80_040", "family_id": "BH‑C", "difficulty": "medium", "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"], "hardness_axes": [1, 2], "shortcut_defeated": "Largest‑first shortcut"},
    {"task_id": "BH80_041", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["extract_boundary", "recolor_boundary", "count"], "hardness_axes": [1, 3, 4, 7], "shortcut_defeated": "Interior‑only shortcut"},
    {"task_id": "BH80_042", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["crop_object", "transform", "place_back"], "hardness_axes": [1, 4, 5, 9], "shortcut_defeated": "Solid‑shape shortcut"},
    {"task_id": "BH80_043", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["fill_region", "count_objects", "pattern_output"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Fixed‑canvas shortcut"},
    {"task_id": "BH80_044", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["extract", "rotate", "recolor"], "hardness_axes": [1, 3, 5, 7, 9], "shortcut_defeated": "Colour‑map shortcut"},
    {"task_id": "BH80_045", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["remove_noise", "extract_object", "recolor"], "hardness_axes": [1, 2, 3, 5, 8], "shortcut_defeated": "Single‑extract shortcut"},
    {"task_id": "BH80_046", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["crop", "rotate", "count_or_pattern"], "hardness_axes": [1, 3, 4, 5, 7], "shortcut_defeated": "Count‑first shortcut"},
    {"task_id": "BH80_047", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["isolate_largest", "normalize_position", "recolor"], "hardness_axes": [1, 2, 3, 5, 8], "shortcut_defeated": "Largest‑only shortcut"},
    {"task_id": "BH80_048", "family_id": "BH‑C", "difficulty": "adversarial", "primitive_sequence": ["mirror_object", "extract_changed_region", "recolor"], "hardness_axes": [1, 3, 4, 5, 6, 7, 9], "shortcut_defeated": "Connected‑shape shortcut"},
    {"task_id": "BH80_049", "family_id": "BH‑C", "difficulty": "adversarial", "primitive_sequence": ["extract_boundary", "mirror_object", "crop"], "hardness_axes": [1, 3, 4, 5, 6, 7, 9], "shortcut_defeated": "Boundary‑all shortcut"},
    {"task_id": "BH80_050", "family_id": "BH‑C", "difficulty": "adversarial", "primitive_sequence": ["fill_region", "count_objects", "pattern_output"], "hardness_axes": [2, 3, 4, 5, 6, 8, 9], "shortcut_defeated": "Fill‑count‑all shortcut"},
    {"task_id": "BH80_051", "family_id": "BH‑C", "difficulty": "adversarial", "primitive_sequence": ["extract", "rotate", "recolor"], "hardness_axes": [1, 2, 3, 5, 6, 7, 9], "shortcut_defeated": "First‑object shortcut"},
    {"task_id": "BH80_052", "family_id": "BH‑C", "difficulty": "hard", "primitive_sequence": ["crop_object", "transform", "place_back"], "hardness_axes": [1, 3, 4, 5, 7], "shortcut_defeated": "Position‑invariance shortcut"},
    {"task_id": "BH80_053", "family_id": "BH‑D", "difficulty": "hard", "primitive_sequence": ["normalize_position", "isolate_largest", "recolor"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Order‑independence shortcut"},
    {"task_id": "BH80_054", "family_id": "BH‑D", "difficulty": "hard", "primitive_sequence": ["recolor", "extract", "rotate"], "hardness_axes": [1, 3, 5, 7, 9], "shortcut_defeated": "Order‑independence shortcut"},
    {"task_id": "BH80_055", "family_id": "BH‑D", "difficulty": "medium", "primitive_sequence": ["recolor", "isolate_largest", "normalize_position"], "hardness_axes": [1, 5], "shortcut_defeated": "Order‑independence"},
    {"task_id": "BH80_056", "family_id": "BH‑D", "difficulty": "medium", "primitive_sequence": ["rotate", "extract", "recolor"], "hardness_axes": [1, 5], "shortcut_defeated": "Extract‑first shortcut"},
    {"task_id": "BH80_057", "family_id": "BH‑D", "difficulty": "hard", "primitive_sequence": ["count_objects", "pattern_output", "fill_region"], "hardness_axes": [1, 2, 4, 5, 8], "shortcut_defeated": "Fill‑first shortcut"},
    {"task_id": "BH80_058", "family_id": "BH‑D", "difficulty": "medium", "primitive_sequence": ["place_back", "crop_object", "transform"], "hardness_axes": [1, 4, 5], "shortcut_defeated": "Crop‑first shortcut"},
    {"task_id": "BH80_059", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["extract", "count_objects", "transform"], "hardness_axes": [1, 4, 5, 8, 10], "shortcut_defeated": "Extract‑only shortcut"},
    {"task_id": "BH80_060", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["extract", "count_objects", "transform"], "hardness_axes": [1, 2, 3, 5, 8, 10], "shortcut_defeated": "Count‑ignore shortcut"},
    {"task_id": "BH80_061", "family_id": "BH‑E", "difficulty": "adversarial", "primitive_sequence": ["extract", "count_objects", "transform"], "hardness_axes": [1, 2, 3, 4, 5, 6, 10], "shortcut_defeated": "Extract‑ignore shortcut"},
    {"task_id": "BH80_062", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["count_objects", "extract", "transform"], "hardness_axes": [1, 4, 5, 8, 9, 10], "shortcut_defeated": "Count‑then‑extract shortcut"},
    {"task_id": "BH80_063", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["extract", "count_objects", "transform"], "hardness_axes": [1, 3, 4, 5, 7, 10], "shortcut_defeated": "Edge‑free shortcut"},
    {"task_id": "BH80_064", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["transform", "extract", "count_objects"], "hardness_axes": [1, 2, 4, 5, 8, 10], "shortcut_defeated": "Extract‑first shortcut"},
    {"task_id": "BH80_065", "family_id": "BH‑E", "difficulty": "hard", "primitive_sequence": ["count_objects", "transform", "extract"], "hardness_axes": [1, 2, 4, 5, 8, 10], "shortcut_defeated": "Count‑final shortcut"},
    {"task_id": "BH80_066", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["normalize_position", "mirror_object", "place_back"], "hardness_axes": [1, 4, 5, 7, 8, 10], "shortcut_defeated": "Normalize‑noop shortcut"},
    {"task_id": "BH80_067", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["mirror_object", "normalize_position", "place_back"], "hardness_axes": [1, 2, 4, 5, 8, 10], "shortcut_defeated": "Mirror‑invariance shortcut"},
    {"task_id": "BH80_068", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["normalize_position", "mirror_object", "place_back"], "hardness_axes": [1, 2, 3, 4, 5, 10], "shortcut_defeated": "Position‑invariance shortcut"},
    {"task_id": "BH80_069", "family_id": "BH‑F", "difficulty": "adversarial", "primitive_sequence": ["normalize_position", "mirror_object", "place_back"], "hardness_axes": [1, 2, 3, 4, 5, 6, 10], "shortcut_defeated": "Normalize‑identity shortcut"},
    {"task_id": "BH80_070", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["mirror_object", "place_back", "normalize_position"], "hardness_axes": [1, 4, 5, 8, 9, 10], "shortcut_defeated": "Place‑last shortcut"},
    {"task_id": "BH80_071", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["place_back", "normalize_position", "mirror_object"], "hardness_axes": [1, 2, 4, 5, 8, 10], "shortcut_defeated": "Place‑first shortcut"},
    {"task_id": "BH80_072", "family_id": "BH‑F", "difficulty": "hard", "primitive_sequence": ["mirror_object", "normalize_position", "place_back"], "hardness_axes": [1, 2, 4, 5, 9, 10], "shortcut_defeated": "Mirror‑flip‑only shortcut"},
    {"task_id": "BH80_073", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["crop", "count_objects", "recolor"], "hardness_axes": [1, 4, 5, 8, 10], "shortcut_defeated": "Crop‑noop shortcut"},
    {"task_id": "BH80_074", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["count_objects", "crop", "recolor"], "hardness_axes": [1, 3, 4, 5, 8, 10], "shortcut_defeated": "Crop‑first shortcut"},
    {"task_id": "BH80_075", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["crop", "recolor", "count_objects"], "hardness_axes": [1, 2, 4, 5, 9, 10], "shortcut_defeated": "Count‑first shortcut"},
    {"task_id": "BH80_076", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["recolor", "crop", "count_objects"], "hardness_axes": [1, 3, 4, 5, 7, 10], "shortcut_defeated": "Recolor‑last shortcut"},
    {"task_id": "BH80_077", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["crop", "count_objects", "recolor"], "hardness_axes": [1, 2, 3, 4, 5, 10], "shortcut_defeated": "Crop‑noop shortcut"},
    {"task_id": "BH80_078", "family_id": "BH‑G", "difficulty": "adversarial", "primitive_sequence": ["crop", "count_objects", "recolor"], "hardness_axes": [1, 2, 3, 4, 5, 6, 10], "shortcut_defeated": "Crop‑all shortcut"},
    {"task_id": "BH80_079", "family_id": "BH‑G", "difficulty": "hard", "primitive_sequence": ["count_objects", "recolor", "crop"], "hardness_axes": [1, 2, 4, 5, 8, 10], "shortcut_defeated": "Count‑last shortcut"},
    {"task_id": "BH80_080", "family_id": "BH‑G", "difficulty": "adversarial", "primitive_sequence": ["crop", "count_objects", "recolor"], "hardness_axes": [1, 2, 3, 4, 5, 6, 9], "shortcut_defeated": "Crop‑extract‑all shortcut"},
]


def generate_broad_hard_80_tasks() -> List[Dict[str, Any]]:
    """Generate the deterministic 80‑task Broad‑Hard‑80 packet.

    Returns a list of 80 task dictionaries with IDs ``BH80_001`` through
    ``BH80_080``. No randomness is used. All primitives are from the
    allowed boundary or approved aliases. All leakage flags are false.
    """
    tasks: List[Dict[str, Any]] = []
    for spec in _BROAD_HARD_80_SPECS:
        # Validate primitives at construction time
        for p in spec["primitive_sequence"]:
            if p not in _BH80_ALL_ALLOWED:
                raise ValueError(f"{spec['task_id']}: disallowed primitive '{p}'")
        task = {
            "task_id": spec["task_id"],
            "family_id": spec["family_id"],
            "difficulty": spec["difficulty"],
            "primitive_sequence": spec["primitive_sequence"].copy(),
            "scene_spec": _make_scene_spec(spec["task_id"], 1),
            "train_pair_count": 1,
            "test_input_count": 1,
            "hardness_axes": spec["hardness_axes"].copy(),
            "shortcut_defeated": spec["shortcut_defeated"],
            "expected_trace_requirements": TRACE_REQUIREMENTS_TEMPLATE.copy(),
            "allowed_dynamic_parameters": [],
            "forbidden_shortcuts": FORBIDDEN_SHORTCUTS.copy(),
            "leakage_flags": LEAKAGE_FLAGS_TEMPLATE.copy(),
            "expected_failure_categories": EXPECTED_FAILURE_CATEGORIES.copy(),
        }
        tasks.append(task)
    return tasks


# End of module
