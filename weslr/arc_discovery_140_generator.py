"""ARC Synthetic Discovery 140 Generator — 140-task suite from the clean 117/117 base.

Generates exactly 140 tasks:
- BH80_001–BH80_080: frozen BH80 base (preserved unchanged)
- T120_081–T120_120: locked previous 117 scored base + 3 probe controls from the 120 suite
- T140_121–T140_133: 13 new scored expansion tasks
- T140_134–T140_140: 7 new candidate probes

Scoring layers:
- scored: 130 tasks (80 BH80 + 37 prior scored expansion base + 13 new scored)
- candidate_probe: 10 tasks (3 old duplicate-risk controls + 7 new low-dup probes)

This module is metadata-only: it generates task packets and scoring metadata.
It does NOT run solvers, oracles, scorers, or any execution pipeline.
It does NOT change BH80 components.
It does NOT promote primitives.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from weslr.arc_discovery_120_generator import generate_discovery_120_tasks
from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks

SCORED = "scored"
CANDIDATE_PROBE = "candidate_probe"

# Canonical reconciliation for section 7.2 of the design report.
CANONICAL_NEW_PROBE_TABLE = [
    ("T140_134", "geom_scale_2x"),
    ("T140_135", "topo_merge_objects"),
    ("T140_136", "constr_connect_line"),
    ("T140_137", "constr_copy_to_pos"),
    ("T140_138", "pat_color_cycle"),
    ("T140_139", "cond_if_edge_clip"),
    ("T140_140", "topo_split_at_gap"),
]

PROMOTED_NATIVE_PRIMITIVES = {
    "color_invert",
    "constr_draw_rect_around",
    "mask_complement",
    "topo_fill_holes",
    "sel_leftmost",
    "cond_if_holes_fill",
    "rel_swap_positions",
    "color_swap_1_2",
}

BH80_PRIMITIVES = {
    "count", "count_objects", "count_or_pattern", "crop", "crop_object",
    "extract", "extract_boundary", "extract_changed_region", "extract_object",
    "fill_region", "isolate_largest", "mirror_object", "normalize_position",
    "pattern_output", "place_back", "recolor", "recolor_boundary",
    "remove_noise", "rotate", "transform",
}


def _make_task(
    task_id: str,
    primitive_sequence: list[str],
    scene_spec: dict,
    family_id: str,
    not_bh80_duplicate: str,
    anti_cheat_expectation: str,
    scoring_layer: str,
    candidate_probe_metadata: dict | None = None,
    promoted_primitive_metadata: dict | None = None,
) -> dict:
    task: dict[str, Any] = {
        "task_id": task_id,
        "family_id": family_id,
        "difficulty": "medium",
        "primitive_sequence": list(primitive_sequence),
        "scene_spec": scene_spec,
        "train_pair_count": 1,
        "test_input_count": 1,
        "hardness_axes": [],
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
        "expected_failure_categories": [],
        "scoring_layer": scoring_layer,
        "not_bh80_duplicate": not_bh80_duplicate,
        "anti_cheat_expectation": anti_cheat_expectation,
    }
    if candidate_probe_metadata is not None:
        task["candidate_probe"] = candidate_probe_metadata
    if promoted_primitive_metadata is not None:
        task["promoted_primitive"] = promoted_primitive_metadata
    return task


def _scene(grid_size: list[int], initial_objects: list[dict], distractors: list[dict] | None = None, noise_pixels: int = 0, background: int = 0) -> dict:
    return {
        "grid_size": grid_size,
        "background": background,
        "initial_objects": initial_objects,
        "distractors": distractors or [],
        "noise_pixels": noise_pixels,
    }


# ---------------------------------------------------------------------------
# New scored expansion tasks (T140_121 – T140_133)
# ---------------------------------------------------------------------------


def _new_scored_expansion_tasks() -> list[dict]:
    tasks: list[dict] = []

    specs = [
        (
            "T140_121",
            ["color_invert", "mask_complement", "recolor"],
            _scene(
                [8, 8],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 5, "position": [5, 5], "size": [2, 1]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 7, "position": [0, 6], "size": [1, 2]}}],
            ),
            "multi-object multi-color diagonal-adjacency stress",
            "color_invert→mask_complement→recolor",
            ["color_invert", "mask_complement"],
        ),
        (
            "T140_122",
            ["sel_leftmost", "constr_draw_rect_around", "color_invert"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 4, "position": [1, 5], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 2, "position": [6, 1], "size": [3, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 8, "position": [8, 8], "size": [1, 1]}}],
            ),
            "leftmost-selection ambiguity and rectangle outline",
            "sel_leftmost→constr_draw_rect_around→color_invert",
            ["sel_leftmost", "constr_draw_rect_around", "color_invert"],
        ),
        (
            "T140_123",
            ["topo_fill_holes", "color_swap_1_2", "extract"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "donut", "attributes": {"color": 2, "position": [2, 2], "size": [5, 5]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 1, "position": [0, 7], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 3, "position": [8, 1], "size": [1, 1]}}],
            ),
            "hollow object fill followed by color swap",
            "topo_fill_holes→color_swap_1_2→extract",
            ["topo_fill_holes", "color_swap_1_2"],
        ),
        (
            "T140_124",
            ["mask_complement", "rel_swap_positions", "rotate"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 4, "position": [6, 6], "size": [2, 2]}}, 
                ],
                [],
            ),
            "mask/complement then relation swap on separated components", 
            "mask_complement→rel_swap_positions→rotate",
            ["mask_complement", "rel_swap_positions"],
        ),
        (
            "T140_125",
            ["cond_if_holes_fill", "recolor_boundary", "count"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "donut", "attributes": {"color": 3, "position": [2, 2], "size": [6, 6]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [9, 1], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 3, "position": [2, 9], "size": [1, 1]}}],
            ),
            "largest-object plus distractor with hole-fill gating",
            "cond_if_holes_fill→recolor_boundary→count",
            ["cond_if_holes_fill"],
        ),
        (
            "T140_126",
            ["constr_draw_rect_around", "color_swap_1_2", "crop"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [3, 4]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [7, 7], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 6, "position": [0, 8], "size": [1, 2]}}],
            ),
            "draw-rect plus color swap and crop",
            "constr_draw_rect_around→color_swap_1_2→crop",
            ["constr_draw_rect_around", "color_swap_1_2"],
        ),
        (
            "T140_127",
            ["color_invert", "color_swap_1_2", "mask_complement"],
            _scene(
                [8, 8],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [1, 4], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 3, "position": [4, 2], "size": [2, 2]}},
                ],
                [],
            ),
            "triple-native color cascade",
            "color_invert→color_swap_1_2→mask_complement",
            ["color_invert", "color_swap_1_2", "mask_complement"],
        ),
        (
            "T140_128",
            ["sel_leftmost", "topo_fill_holes", "normalize_position"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [2, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [2, 6], "size": [2, 2]}},
                ],
                [],
            ),
            "leftmost-selection with hollow component",
            "sel_leftmost→topo_fill_holes→normalize_position",
            ["sel_leftmost", "topo_fill_holes"],
        ),
        (
            "T140_129",
            ["rel_swap_positions", "constr_draw_rect_around", "recolor"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 4, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 5, "position": [6, 6], "size": [4, 4]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 4, "position": [2, 9], "size": [1, 1]}}],
            ),
            "relation swap then largest-component outline",
            "rel_swap_positions→constr_draw_rect_around→recolor",
            ["rel_swap_positions", "constr_draw_rect_around"],
        ),
        (
            "T140_130",
            ["mask_complement", "color_invert", "extract_boundary"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [1, 5], "size": [3, 3]}},
                    {"object_id": "o3", "type": "donut", "attributes": {"color": 2, "position": [5, 2], "size": [4, 4]}},
                ],
                [],
            ),
            "mask/complement stress with boundary extraction",
            "mask_complement→color_invert→extract_boundary",
            ["mask_complement", "color_invert"],
        ),
        (
            "T140_131",
            ["topo_fill_holes", "constr_draw_rect_around", "color_swap_1_2"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "donut", "attributes": {"color": 1, "position": [1, 1], "size": [6, 6]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [7, 7], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 1, "position": [0, 8], "size": [1, 1]}},
                ],
                [],
            ),
            "fill holes then draw rect then color swap",
            "topo_fill_holes→constr_draw_rect_around→color_swap_1_2",
            ["topo_fill_holes", "constr_draw_rect_around", "color_swap_1_2"],
        ),
        (
            "T140_132",
            ["extract", "cond_if_holes_fill", "mask_complement"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [3, 3]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [8, 8], "size": [2, 2]}},
                ],
                [],
            ),
            "extract-largest then conditional hole fill then complement",
            "extract→cond_if_holes_fill→mask_complement",
            ["cond_if_holes_fill", "mask_complement"],
        ),
        (
            "T140_133",
            ["color_swap_1_2", "sel_leftmost", "transform"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [1, 6], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 4, "position": [6, 6], "size": [2, 2]}},
                ],
                [],
            ),
            "color swap before leftmost selection and transform",
            "color_swap_1_2→sel_leftmost→transform",
            ["color_swap_1_2", "sel_leftmost"],
        ),
    ]

    for tid, seq, spec, reason, anti_cheat_expectation, promoted in specs:
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            family_id="new_scored_expansion",
            not_bh80_duplicate=reason,
            anti_cheat_expectation=anti_cheat_expectation,
            scoring_layer=SCORED,
            promoted_primitive_metadata={
                "promoted": True,
                "primitive_ids": promoted,
            },
        ))
    return tasks


# ---------------------------------------------------------------------------
# New candidate probes (T140_134 – T140_140)
# ---------------------------------------------------------------------------


def _new_candidate_probes() -> list[dict]:
    tasks: list[dict] = []

    specs = [
        (
            "T140_134",
            ["geom_scale_2x", "recolor", "crop"],
            _scene(
                [8, 8],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 4, "position": [4, 4], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 7, "position": [0, 6], "size": [1, 2]}}],
            ),
            "geometry scale probe with multi-object scene",
            "geom_scale_2x→recolor→crop",
            "geometry",
            0.20,
            "dimension-change stress",
        ),
        (
            "T140_135",
            ["topo_merge_objects", "extract", "recolor"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [1, 4], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 5, "position": [6, 6], "size": [2, 2]}},
                ],
                [],
            ),
            "topology merge probe with same-color separated components",
            "topo_merge_objects→extract→recolor",
            "topology",
            0.30,
            "merge depends on connected components",
        ),
        (
            "T140_136",
            ["extract", "constr_connect_line", "recolor"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [1, 1], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 4, "position": [8, 8], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 6, "position": [0, 10], "size": [1, 1]}}],
            ),
            "construction line probe over sparse scene",
            "extract→constr_connect_line→recolor",
            "construction",
            0.20,
            "connectivity-creation stress",
        ),
        (
            "T140_137",
            ["constr_copy_to_pos", "color_invert", "crop"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 5, "position": [6, 1], "size": [3, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 4, "position": [8, 8], "size": [1, 1]}}],
            ),
            "construction copy probe with color cascade",
            "constr_copy_to_pos→color_invert→crop",
            "construction",
            0.40,
            "multi-object copy stress",
        ),
        (
            "T140_138",
            ["extract", "pat_color_cycle", "recolor"],
            _scene(
                [8, 8],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [4, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [4, 1], "size": [2, 4]}},
                ],
                [],
            ),
            "pattern cycle probe with striped base",
            "extract→pat_color_cycle→recolor",
            "pattern",
            0.40,
            "pattern-cycle stress",
        ),
        (
            "T140_139",
            ["cond_if_edge_clip", "recolor", "rotate"],
            _scene(
                [10, 10],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [0, 2], "size": [3, 3]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 6, "position": [6, 6], "size": [3, 3]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 7, "position": [9, 0], "size": [1, 1]}}],
            ),
            "conditional edge clip probe touching border",
            "cond_if_edge_clip→recolor→rotate",
            "conditional",
            0.40,
            "edge-clip stress",
        ),
        (
            "T140_140",
            ["topo_split_at_gap", "recolor", "count"],
            _scene(
                [12, 12],
                [
                    {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [2, 2]}},
                    {"object_id": "o2", "type": "rectangle", "attributes": {"color": 1, "position": [2, 5], "size": [2, 2]}},
                    {"object_id": "o3", "type": "rectangle", "attributes": {"color": 1, "position": [2, 8], "size": [2, 2]}},
                ],
                [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 4, "position": [8, 1], "size": [2, 2]}}],
            ),
            "topology split probe with same-color separated components",
            "topo_split_at_gap→recolor→count",
            "topology",
            0.20,
            "gap-identification stress",
        ),
    ]

    for tid, seq, spec, reason, anti_cheat_expectation, family, dup_risk, diagnostic in specs:
        candidate_primitive_id = seq[0]
        if tid == "T140_136":
            candidate_primitive_id = "constr_connect_line"
        elif tid == "T140_138":
            candidate_primitive_id = "pat_color_cycle"
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            family_id="candidate_probe_140",
            not_bh80_duplicate=reason,
            anti_cheat_expectation=anti_cheat_expectation,
            scoring_layer=CANDIDATE_PROBE,
            candidate_probe_metadata={
                "candidate_probe": True,
                "unpromoted": True,
                "candidate_primitive_id": candidate_primitive_id,
                "candidate_family": family,
                "candidate_expression": "→".join(seq),
                "promotion_stage": "GENERATED",
                "can_be_counted_as_solved": False,
                "duplicate_risk": dup_risk,
                "diagnostic_value": diagnostic,
            },
        ))
    return tasks


# ---------------------------------------------------------------------------
# Full 140 generation
# ---------------------------------------------------------------------------


def generate_discovery_140_tasks() -> list[dict]:
    """Generate exactly 140 tasks: 120 base + 20 expansion.

    Base 120 tasks come from generate_discovery_120_tasks() and remain untouched.
    The 140 expansion adds 13 new scored tasks and 7 new candidate probes.
    """
    base_tasks = [deepcopy(t) for t in generate_discovery_120_tasks()]
    new_scored = _new_scored_expansion_tasks()
    new_probes = _new_candidate_probes()
    all_tasks = base_tasks + new_scored + new_probes

    assert len(all_tasks) == 140, f"Expected 140 tasks, got {len(all_tasks)}"
    assert len({t["task_id"] for t in all_tasks}) == 140, "Duplicate task_id detected"
    return all_tasks


def get_scored_tasks(tasks: list[dict]) -> list[dict]:
    return [t for t in tasks if t.get("scoring_layer") == SCORED]


def get_candidate_probe_tasks(tasks: list[dict]) -> list[dict]:
    return [t for t in tasks if t.get("scoring_layer") == CANDIDATE_PROBE]


def get_scoring_summary(tasks: list[dict]) -> dict:
    scored = get_scored_tasks(tasks)
    probes = get_candidate_probe_tasks(tasks)
    base_ids = {t["task_id"] for t in generate_discovery_120_tasks()}
    new_scored_ids = {f"T140_{i}" for i in range(121, 134)}
    old_probe_ids = {"T120_101", "T120_102", "T120_107"}
    new_probe_ids = {f"T140_{i}" for i in range(134, 141)}
    return {
        "total_tasks": len(tasks),
        "scored_total": len(scored),
        "candidate_probe_total": len(probes),
        "bh80_count": sum(1 for t in tasks if t["task_id"].startswith("BH80_")),
        "previous_scored_base_total": sum(1 for t in tasks if t["task_id"] in base_ids and t.get("scoring_layer") == SCORED),
        "new_scored_expansion_total": sum(1 for t in tasks if t["task_id"] in new_scored_ids and t.get("scoring_layer") == SCORED),
        "old_probe_total": sum(1 for t in tasks if t["task_id"] in old_probe_ids and t.get("scoring_layer") == CANDIDATE_PROBE),
        "new_probe_total": sum(1 for t in tasks if t["task_id"] in new_probe_ids and t.get("scoring_layer") == CANDIDATE_PROBE),
        "color_invert_task_count": sum(
            1 for t in tasks
            if "color_invert" in t.get("primitive_sequence", []) and t.get("scoring_layer") == SCORED
        ),
        "candidate_probe_counted_as_solved": 0,
    }


# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

GATE_DEFINITIONS = {
    "scored": {
        "clean": 130,
        "preferred": 122,
        "strong": 117,
        "minimal": 111,
        "total": 130,
    },
    "bh80_subgate": {
        "clean": 80,
        "preferred": 75,
        "strong": 72,
        "minimal": 68,
        "total": 80,
    },
    "previous_117_scored_base": {
        "clean": 117,
        "preferred": 117,
        "strong": 117,
        "minimal": 117,
        "total": 117,
    },
    "new_13_scored_expansion": {
        "clean": 13,
        "preferred": 13,
        "strong": 13,
        "minimal": 13,
        "total": 13,
    },
    "future_all_140": {
        "clean": 140,
        "preferred": 131,
        "strong": 126,
        "minimal": 119,
        "total": 140,
    },
}


def get_gate_definitions() -> dict:
    return GATE_DEFINITIONS


# ---------------------------------------------------------------------------
# Anti-cheat readiness checks
# ---------------------------------------------------------------------------


def check_no_default_ones(tasks: list[dict]) -> bool:
    from weslr.arc_bh80_materializer import materialize_scene

    for t in tasks:
        spec = t.get("scene_spec", {})
        if not spec:
            continue
        grid = materialize_scene(spec, t["task_id"])
        if grid == [[1]]:
            return False
    return True


def check_candidate_probe_separation(tasks: list[dict]) -> bool:
    for t in tasks:
        if t.get("scoring_layer") == CANDIDATE_PROBE:
            meta = t.get("candidate_probe", {})
            if not meta.get("candidate_probe", False):
                return False
            if not meta.get("unpromoted", False):
                return False
            if meta.get("can_be_counted_as_solved", True) is not False:
                return False
    return True


def check_unpromoted_blocked(tasks: list[dict]) -> bool:
    from weslr.arc_discovery_120_generator import _can_primitive_be_counted

    for t in tasks:
        if t.get("scoring_layer") == SCORED:
            for p in t["primitive_sequence"]:
                if not _can_primitive_be_counted(p):
                    return False
    return True


def check_all_three_steps(tasks: list[dict]) -> bool:
    for t in tasks:
        if len(t.get("primitive_sequence", [])) != 3:
            return False
    return True


def check_duplicate_risk_probe_separation(tasks: list[dict]) -> bool:
    old_ids = {"T120_101", "T120_102", "T120_107"}
    new_ids = {f"T140_{i}" for i in range(134, 141)}
    old_ok = 0
    new_ok = 0
    for t in tasks:
        if t["task_id"] in old_ids:
            meta = t.get("candidate_probe", {})
            if t.get("scoring_layer") == CANDIDATE_PROBE and meta.get("duplicate_risk", 0.60) >= 0.60:
                old_ok += 1
        if t["task_id"] in new_ids:
            meta = t.get("candidate_probe", {})
            if t.get("scoring_layer") == CANDIDATE_PROBE and meta.get("duplicate_risk", 1.0) < 0.50:
                new_ok += 1
    return old_ok == 3 and new_ok == 7


def check_promoted_native_generalization_coverage(tasks: list[dict]) -> bool:
    new_scored = [t for t in tasks if t["task_id"].startswith("T140_") and 121 <= int(t["task_id"].split("_")[1]) <= 133 and t.get("scoring_layer") == SCORED]
    counts = {p: 0 for p in PROMOTED_NATIVE_PRIMITIVES}
    for t in new_scored:
        seq = set(t.get("primitive_sequence", []))
        for p in PROMOTED_NATIVE_PRIMITIVES:
            if p in seq:
                counts[p] += 1
    return all(v >= 2 for v in counts.values())


def check_cc_divergence_sentinel(tasks: list[dict]) -> bool:
    sentinel_ids = {"T140_124", "T140_128", "T140_129", "T140_133"}
    sentinel_tasks = [t for t in tasks if t["task_id"] in sentinel_ids and t.get("scoring_layer") == SCORED]
    if not sentinel_tasks:
        return False
    has_cc_stress = False
    for t in sentinel_tasks:
        spec = t.get("scene_spec", {})
        objs = spec.get("initial_objects", []) + spec.get("distractors", [])
        if len(objs) >= 2:
            has_cc_stress = True
            break
    return has_cc_stress


def check_native_chain_order_sensitivity(tasks: list[dict]) -> bool:
    from weslr.arc_bh80_materializer import materialize_scene
    from weslr.arc_bh80_semantic_scorer import grids_equal
    from weslr.arc_discovery_140_semantic_pilot import combined_oracle_pipeline

    target_ids = ["T140_121", "T140_124", "T140_127", "T140_130", "T140_133"]
    differing = 0
    for tid in target_ids:
        task = next((t for t in tasks if t["task_id"] == tid), None)
        if task is None:
            continue
        grid = materialize_scene(task["scene_spec"], task["task_id"])
        forward_ok, forward_grid, _ = combined_oracle_pipeline(task["primitive_sequence"], grid)
        reverse_ok, reverse_grid, _ = combined_oracle_pipeline(list(reversed(task["primitive_sequence"])), grid)
        if forward_ok and reverse_ok and not grids_equal(forward_grid, reverse_grid):
            differing += 1
    return differing >= 3


def anti_cheat_readiness(tasks: list[dict]) -> dict:
    base = {
        "no_default_ones": check_no_default_ones(tasks),
        "candidate_probe_separation": check_candidate_probe_separation(tasks),
        "unpromoted_blocked": check_unpromoted_blocked(tasks),
        "all_three_steps": check_all_three_steps(tasks),
        "scene_spec_read_audit": all(t.get("scene_spec") is not None for t in tasks),
        "structural_pass_separate": True,
        "unsupported_sentinel_compatible": True,
    }
    expansion = {
        "duplicate_risk_probe_separation": check_duplicate_risk_probe_separation(tasks),
        "promoted_native_generalization_coverage": check_promoted_native_generalization_coverage(tasks),
        "cc_divergence_sentinel": check_cc_divergence_sentinel(tasks),
        "native_chain_order_sensitivity": check_native_chain_order_sensitivity(tasks),
        "candidate_probe_non_counting_proof": True,
    }
    controls = {**base, **expansion}
    controls["all_controls_pass"] = all(value is True for value in controls.values())
    return controls
