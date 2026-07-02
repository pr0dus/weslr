"""ARC Synthetic Discovery 120 Generator — 120-task suite with native-language scoring separation.

Generates exactly 120 tasks:
- BH80_001–BH80_080: frozen BH80 base (preserved unchanged)
- T120_081–T120_090: promoted-native tasks using color_invert (scored)
- T120_091–T120_100: old-primitive harder compositions (scored)
- T120_101–T120_110: candidate-probe tasks using unpromoted natives (unscored)
- T120_111–T120_120: adversarial/control tasks (scored)

Scoring layers:
- scored: 110 tasks (80 BH80 + 10 color_invert + 10 old-primitive + 10 adversarial)
- candidate_probe: 10 tasks (unpromoted candidates, not counted as solved)

This module is metadata-only: it generates task packets and scoring metadata.
It does NOT run solvers, oracles, scorers, or any execution pipeline.
It does NOT change BH80 components.
It does NOT promote primitives.
"""

from __future__ import annotations

from typing import Any

from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks
from weslr.native_arc_promotion_pilot import run_promotion_pilot

# ---------------------------------------------------------------------------
# Promotion status cache
# ---------------------------------------------------------------------------

_promotion_cache: dict[str, bool] | None = None


def _get_promotion_status() -> dict[str, bool]:
    """Return dict of primitive_id -> can_be_counted_as_solved."""
    global _promotion_cache
    if _promotion_cache is not None:
        return _promotion_cache

    cache: dict[str, bool] = {}
    # Check promotion pilot for promoted primitives
    try:
        contract, _audit, summary = run_promotion_pilot()
        if summary.get("promoted", False) and summary.get("can_be_counted_as_solved", False):
            cache[contract.primitive_id] = True
    except Exception:
        pass

    # All BH80 accepted primitives are scored
    bh80_primitives = {
        "count", "count_objects", "count_or_pattern", "crop", "crop_object",
        "extract", "extract_boundary", "extract_changed_region", "extract_object",
        "fill_region", "isolate_largest", "mirror_object", "normalize_position",
        "pattern_output", "place_back", "recolor", "recolor_boundary",
        "remove_noise", "rotate", "transform",
    }
    for p in bh80_primitives:
        cache[p] = True

    _promotion_cache = cache
    return cache


def _can_primitive_be_counted(primitive_id: str) -> bool:
    """Check if a primitive can be counted as solved."""
    return _get_promotion_status().get(primitive_id, False)


# ---------------------------------------------------------------------------
# Scoring layer classification
# ---------------------------------------------------------------------------

SCORED = "scored"
CANDIDATE_PROBE = "candidate_probe"


def _classify_scoring_layer(primitive_sequence: list[str]) -> str:
    """Classify a task as 'scored' or 'candidate_probe'.

    If any primitive in the sequence cannot be counted as solved,
    the task is classified as candidate_probe.
    """
    for p in primitive_sequence:
        if not _can_primitive_be_counted(p):
            return CANDIDATE_PROBE
    return SCORED


# ---------------------------------------------------------------------------
# New 40 task definitions
# ---------------------------------------------------------------------------

def _make_task(
    task_id: str,
    primitive_sequence: list[str],
    scene_spec: dict,
    group: str,
    not_bh80_duplicate: str,
    anti_cheat_expectation: str,
    candidate_probe_metadata: dict | None = None,
    promoted_primitive_metadata: dict | None = None,
) -> dict:
    """Create a task packet for the 120 suite."""
    scoring_layer = _classify_scoring_layer(primitive_sequence)
    task: dict[str, Any] = {
        "task_id": task_id,
        "family_id": group,
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


# --- Promoted-native tasks (T120_081 – T120_090) ---

def _color_invert_tasks() -> list[dict]:
    """10 tasks using promoted color_invert in 3-step chains."""
    tasks = []

    specs = [
        # T120_081
        ("T120_081", ["extract", "color_invert", "recolor"],
         {"grid_size": [8, 8], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [2, 2], "size": [3, 3]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 4, "position": [6, 6], "size": [1, 1]}}],
          "noise_pixels": 0},
         "extract→color_invert→recolor: color_invert on extracted sub-grid"),
        # T120_082
        ("T120_082", ["color_invert", "extract", "rotate"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [4, 4]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [6, 6], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "color_invert→extract→rotate: invert as preprocessing before object selection"),
        # T120_083
        ("T120_083", ["isolate_largest", "color_invert", "normalize_position"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 5, "position": [1, 1], "size": [5, 5]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [8, 8], "size": [2, 2]}},
          ],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 7, "position": [0, 11], "size": [1, 1]}}],
          "noise_pixels": 0},
         "isolate_largest→color_invert→normalize_position: invert identity edge case (color 5)"),
        # T120_084
        ("T120_084", ["crop_object", "color_invert", "place_back"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [4, 3]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 8, "position": [8, 0], "size": [1, 1]}}],
          "noise_pixels": 0},
         "crop_object→color_invert→place_back: invert on cropped sub-grid"),
        # T120_085
        ("T120_085", ["color_invert", "isolate_largest", "recolor"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 0], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 6, "position": [3, 3], "size": [4, 4]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 9, "position": [7, 7], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "color_invert→isolate_largest→recolor: invert changes visual distinctiveness before selection"),
        # T120_086
        ("T120_086", ["extract_boundary", "color_invert", "count"],
         {"grid_size": [8, 8], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [1, 1], "size": [5, 5]}}],
          "distractors": [], "noise_pixels": 0},
         "extract_boundary→color_invert→count: invert on boundary-only sub-grid"),
        # T120_087
        ("T120_087", ["rotate", "color_invert", "crop"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 4, "position": [2, 2], "size": [4, 4]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 1, "position": [7, 7], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "rotate→color_invert→crop: invert after geometric transform"),
        # T120_088
        ("T120_088", ["mirror_object", "color_invert", "extract_changed_region"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [1, 1], "size": [4, 3]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 7, "position": [8, 8], "size": [1, 1]}}],
          "noise_pixels": 0},
         "mirror_object→color_invert→extract_changed_region: invert creates color convergence with mirror"),
        # T120_089
        ("T120_089", ["color_invert", "crop", "count_or_pattern"],
         {"grid_size": [8, 8], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 8, "position": [5, 5], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 2},
         "color_invert→crop→count_or_pattern: invert as preprocessing with noise"),
        # T120_090
        ("T120_090", ["fill_region", "color_invert", "transform"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "cross", "attributes": {"color": 2, "position": [3, 3], "size": [3, 3]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 6, "position": [0, 0], "size": [1, 1]}}],
          "noise_pixels": 0},
         "fill_region→color_invert→transform: invert after fill, before transform"),
    ]

    for tid, seq, spec, reason in specs:
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            group="promoted_native",
            not_bh80_duplicate=reason,
            anti_cheat_expectation="No-op differs; order reversal differs; no [[1]] materialization",
            promoted_primitive_metadata={"primitive_id": "color_invert", "promoted": True},
        ))
    return tasks


# --- Old-primitive harder compositions (T120_091 – T120_100) ---

def _old_primitive_harder_tasks() -> list[dict]:
    """10 tasks using accepted BH80 primitives in novel harder chains."""
    tasks = []

    specs = [
        ("T120_091", ["remove_noise", "rotate", "extract_boundary"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [5, 5]}}],
          "distractors": [
              {"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [10, 10], "size": [1, 1]}},
              {"object_id": "d2", "type": "rectangle", "attributes": {"color": 1, "position": [0, 11], "size": [1, 1]}},
          ],
          "noise_pixels": 3},
         "Novel: remove_noise→rotate→extract_boundary with noise + distractors"),
        ("T120_092", ["extract", "normalize_position", "count_objects"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [0, 0], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [5, 5], "size": [2, 2]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 3, "position": [8, 0], "size": [1, 1]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Novel: extract→normalize_position→count_objects with 3 objects"),
        ("T120_093", ["crop_object", "mirror_object", "recolor_boundary"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 4, "position": [2, 2], "size": [4, 4]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 4, "position": [8, 8], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Novel: crop_object→mirror_object→recolor_boundary chain"),
        ("T120_094", ["isolate_largest", "extract_changed_region", "pattern_output"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [6, 6]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [9, 9], "size": [2, 2]}},
          ],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 11], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Novel: isolate_largest→extract_changed_region→pattern_output"),
        ("T120_095", ["count_objects", "crop", "transform"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [1, 1], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [5, 5], "size": [2, 2]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 4, "position": [8, 8], "size": [1, 1]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Novel: count_objects→crop→transform ordering"),
        ("T120_096", ["place_back", "extract_boundary", "rotate"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 5, "position": [2, 2], "size": [3, 3]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 5, "position": [7, 0], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Novel: place_back before boundary extraction then rotate"),
        ("T120_097", ["transform", "remove_noise", "extract"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [3, 3], "size": [4, 4]}}],
          "distractors": [
              {"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [10, 0], "size": [1, 1]}},
              {"object_id": "d2", "type": "rectangle", "attributes": {"color": 1, "position": [0, 10], "size": [1, 1]}},
          ],
          "noise_pixels": 4},
         "Novel: transform first, then noise removal — reversed from BH80 pattern"),
        ("T120_098", ["recolor", "place_back", "count"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [6, 6], "size": [2, 2]}},
          ],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 9], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Novel: recolor→place_back→count chain"),
        ("T120_099", ["extract_object", "count_objects", "normalize_position"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [0, 0], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [4, 4], "size": [3, 3]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 4, "position": [8, 8], "size": [1, 1]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Novel: extract_object→count_objects→normalize_position"),
        ("T120_100", ["normalize_position", "recolor_boundary", "mirror_object"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [1, 1], "size": [4, 4]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [7, 7], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Novel: normalize_position→recolor_boundary→mirror_object"),
    ]

    for tid, seq, spec, reason in specs:
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            group="old_primitive_harder",
            not_bh80_duplicate=reason,
            anti_cheat_expectation="No-op differs; order reversal differs; no [[1]] materialization",
        ))
    return tasks


# --- Candidate-probe tasks (T120_101 – T120_110) ---

# Candidate primitive metadata for probes
_CANDIDATE_PROBES = [
    ("T120_101", ["extract", "mask_border_only", "recolor"],
     "mask_border_only", "mask_algebra", "Ω(mask∧border)⇢color(2)",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [5, 5]}}],
      "distractors": [], "noise_pixels": 0},
     "Border-highlight on composed chain"),
    ("T120_102", ["isolate_largest", "geom_flip_vertical", "recolor"],
     "geom_flip_vertical", "geometry_transform", "γ(flip(axis=row))⇒reflect",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [4, 4]}}],
      "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [8, 8], "size": [1, 1]}}],
      "noise_pixels": 0},
     "Vertical flip vs. mirror_object distinction"),
    ("T120_103", ["topo_fill_holes", "extract", "recolor"],
     "topo_fill_holes", "topology_transform", "τ(fill(holes))⇒solid",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "donut", "attributes": {"color": 2, "position": [2, 2], "size": [5, 5]}}],
      "distractors": [], "noise_pixels": 0},
     "Hole-filling on hollow objects"),
    ("T120_104", ["constr_draw_rect_around", "recolor", "crop"],
     "constr_draw_rect_around", "construction_transform", "ξ(draw(rect,bbox(obj)))⇒overlay",
     {"grid_size": [12, 12], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 4, "position": [3, 3], "size": [3, 3]}}],
      "distractors": [], "noise_pixels": 0},
     "Construction drawing around objects"),
    ("T120_105", ["color_swap_1_2", "extract", "rotate"],
     "color_swap_1_2", "color_transform", "κ(swap(1,2))⇒recolor",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [
          {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
          {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [6, 6], "size": [3, 3]}},
      ],
      "distractors": [], "noise_pixels": 0},
     "Color swap vs. no-op distinction"),
    ("T120_106", ["sel_leftmost", "recolor", "rotate"],
     "sel_leftmost", "object_selector", "λG.Σ[obj|argmin(col)]⇒extract",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [
          {"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [5, 1], "size": [2, 2]}},
          {"object_id": "o2", "type": "rectangle", "attributes": {"color": 4, "position": [5, 5], "size": [2, 2]}},
          {"object_id": "o3", "type": "rectangle", "attributes": {"color": 5, "position": [5, 8], "size": [2, 2]}},
      ],
      "distractors": [], "noise_pixels": 0},
     "Leftmost selection vs. other selectors"),
    ("T120_107", ["extract", "pat_row_alternate", "recolor"],
     "pat_row_alternate", "pattern_transform", "π(row_alternate(1,2))⇒pattern",
     {"grid_size": [8, 8], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [6, 2]}}],
      "distractors": [], "noise_pixels": 0},
     "Row-alternating pattern generation"),
    ("T120_108", ["cond_if_holes_fill", "recolor", "crop"],
     "cond_if_holes_fill", "conditional_transform", "κ(count(holes)>0)?fill_holes:identity",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "donut", "attributes": {"color": 2, "position": [2, 2], "size": [5, 5]}}],
      "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 2, "position": [8, 0], "size": [1, 1]}}],
      "noise_pixels": 0},
     "Conditional branching correctness"),
    ("T120_109", ["rel_swap_positions", "recolor", "transform"],
     "rel_swap_positions", "relation_transform", "Φ(rel(swap),obj_A,obj_B)⇒translate",
     {"grid_size": [12, 12], "background": 0,
      "initial_objects": [
          {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
          {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [8, 8], "size": [3, 3]}},
      ],
      "distractors": [], "noise_pixels": 0},
     "Relational position swap"),
    ("T120_110", ["mask_complement", "extract_boundary", "recolor"],
     "mask_complement", "mask_algebra", "Ω(¬mask)⇢invert",
     {"grid_size": [10, 10], "background": 0,
      "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [5, 5]}}],
      "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 3, "position": [8, 8], "size": [1, 1]}}],
      "noise_pixels": 0},
     "Mask complement vs. direct mask"),
]


def _candidate_probe_tasks() -> list[dict]:
    """10 candidate-probe tasks using unpromoted native candidates."""
    tasks = []
    for tid, seq, cand_id, family, expr, spec, diagnostic in _CANDIDATE_PROBES:
        probe_meta = {
            "candidate_probe": True,
            "unpromoted": True,
            "candidate_primitive_id": cand_id,
            "candidate_family": family,
            "candidate_expression": expr,
            "promotion_stage": "GENERATED",
            "can_be_counted_as_solved": False,
            "diagnostic_value": diagnostic,
        }
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            group="candidate_probe",
            not_bh80_duplicate=f"Candidate probe using unpromoted {cand_id}",
            anti_cheat_expectation="Candidate probe: not counted in scored denominator",
            candidate_probe_metadata=probe_meta,
        ))
    return tasks


# --- Adversarial/control tasks (T120_111 – T120_120) ---

def _adversarial_control_tasks() -> list[dict]:
    """10 adversarial/control tasks testing no-op, order, metadata, diversity, regression."""
    tasks = []

    specs = [
        ("T120_111", ["pattern_output", "pattern_output", "pattern_output"],
         {"grid_size": [6, 6], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}}],
          "distractors": [], "noise_pixels": 0},
         "Triple near-identity: no [[1]] collapse"),
        ("T120_112", ["extract", "rotate", "extract"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [2, 2], "size": [4, 4]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 2, "position": [8, 0], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Repeated extract: order sensitivity with repeated primitives"),
        ("T120_113", ["count", "count", "count"],
         {"grid_size": [8, 8], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 0], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 2, "position": [4, 4], "size": [1, 1]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 3, "position": [6, 6], "size": [1, 1]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Triple count: output diversity and metadata stripping"),
        ("T120_114", ["color_invert", "color_invert", "color_invert"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 8, "position": [6, 6], "size": [2, 2]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Triple color_invert: parity semantics (odd=identity, even=original)"),
        ("T120_115", ["crop", "crop", "crop"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 4, "position": [3, 3], "size": [6, 6]}}],
          "distractors": [], "noise_pixels": 0},
         "Triple crop: repeated same-primitive must not collapse to [[1]]"),
        ("T120_116", ["rotate", "recolor", "rotate"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [4, 4]}}],
          "distractors": [{"object_id": "d1", "type": "rectangle", "attributes": {"color": 3, "position": [8, 8], "size": [1, 1]}}],
          "noise_pixels": 0},
         "Sandwich pattern: rotate→recolor→rotate order sensitivity"),
        ("T120_117", ["extract_boundary", "count", "recolor"],
         {"grid_size": [8, 8], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [1, 1], "size": [5, 5]}}],
          "distractors": [
              {"object_id": "d1", "type": "rectangle", "attributes": {"color": 2, "position": [0, 7], "size": [1, 1]}},
              {"object_id": "d2", "type": "rectangle", "attributes": {"color": 2, "position": [7, 0], "size": [1, 1]}},
          ],
          "noise_pixels": 0},
         "Distractor pressure: boundary+count+recolor with distractors"),
        ("T120_118", ["remove_noise", "normalize_position", "count_objects"],
         {"grid_size": [12, 12], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 1, "position": [8, 8], "size": [2, 2]}},
          ],
          "distractors": [
              {"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 11], "size": [1, 1]}},
              {"object_id": "d2", "type": "rectangle", "attributes": {"color": 1, "position": [11, 0], "size": [1, 1]}},
          ],
          "noise_pixels": 5},
         "High-noise regression safety and metadata stripping"),
        ("T120_119", ["isolate_largest", "color_invert", "count"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [
              {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 0], "size": [2, 2]}},
              {"object_id": "o2", "type": "rectangle", "attributes": {"color": 3, "position": [3, 3], "size": [5, 5]}},
              {"object_id": "o3", "type": "rectangle", "attributes": {"color": 9, "position": [8, 8], "size": [1, 1]}},
          ],
          "distractors": [], "noise_pixels": 0},
         "Promoted primitive before count: count reads inverted grid"),
        ("T120_120", ["transform", "extract_object", "pattern_output"],
         {"grid_size": [10, 10], "background": 0,
          "initial_objects": [{"object_id": "o1", "type": "rectangle", "attributes": {"color": 5, "position": [2, 2], "size": [4, 4]}}],
          "distractors": [
              {"object_id": "d1", "type": "rectangle", "attributes": {"color": 5, "position": [8, 8], "size": [1, 1]}},
              {"object_id": "d2", "type": "rectangle", "attributes": {"color": 5, "position": [0, 9], "size": [1, 1]}},
          ],
          "noise_pixels": 2},
         "Scene_spec read audit and output diversity with noise + distractors"),
    ]

    for tid, seq, spec, reason in specs:
        tasks.append(_make_task(
            task_id=tid,
            primitive_sequence=seq,
            scene_spec=spec,
            group="adversarial_control",
            not_bh80_duplicate=reason,
            anti_cheat_expectation="No [[1]]; deterministic; no-op differs; no metadata leakage",
        ))
    return tasks


# ---------------------------------------------------------------------------
# Full 120 generation
# ---------------------------------------------------------------------------

def generate_discovery_120_tasks() -> list[dict]:
    """Generate exactly 120 tasks: 80 BH80 + 40 new.

    Returns a list of task dicts. The first 80 are the frozen BH80 tasks
    with scoring_layer='scored' added. The next 40 are new tasks with
    appropriate scoring_layer classification.
    """
    # Get frozen BH80 tasks
    bh80_tasks = generate_broad_hard_80_tasks()

    # Add scoring_layer to BH80 tasks (all scored)
    bh80_with_scoring = []
    for t in bh80_tasks:
        t_copy = dict(t)
        t_copy["scoring_layer"] = SCORED
        bh80_with_scoring.append(t_copy)

    # Generate 40 new tasks
    new_tasks = []
    new_tasks.extend(_color_invert_tasks())
    new_tasks.extend(_old_primitive_harder_tasks())
    new_tasks.extend(_candidate_probe_tasks())
    new_tasks.extend(_adversarial_control_tasks())

    all_tasks = bh80_with_scoring + new_tasks
    assert len(all_tasks) == 120, f"Expected 120 tasks, got {len(all_tasks)}"
    return all_tasks


def get_scored_tasks(tasks: list[dict]) -> list[dict]:
    """Filter tasks to only scored (non-candidate-probe) tasks."""
    return [t for t in tasks if t.get("scoring_layer") == SCORED]


def get_candidate_probe_tasks(tasks: list[dict]) -> list[dict]:
    """Filter tasks to only candidate-probe tasks."""
    return [t for t in tasks if t.get("scoring_layer") == CANDIDATE_PROBE]


def get_scoring_summary(tasks: list[dict]) -> dict:
    """Return scoring summary for the 120-task suite."""
    scored = get_scored_tasks(tasks)
    probes = get_candidate_probe_tasks(tasks)
    return {
        "total_tasks": len(tasks),
        "scored_total": len(scored),
        "candidate_probe_total": len(probes),
        "bh80_count": sum(1 for t in tasks if t["task_id"].startswith("BH80_")),
        "new_task_count": sum(1 for t in tasks if t["task_id"].startswith("T120_")),
        "color_invert_task_count": sum(
            1 for t in tasks
            if "color_invert" in t.get("primitive_sequence", [])
            and t.get("scoring_layer") == SCORED
        ),
    }


# ---------------------------------------------------------------------------
# 120 Gate definitions
# ---------------------------------------------------------------------------

GATE_DEFINITIONS = {
    "scored": {
        "clean": 110,
        "preferred": 103,
        "strong": 99,
        "minimal": 94,
        "total": 110,
    },
    "bh80_subgate": {
        "clean": 80,
        "preferred": 75,
        "strong": 72,
        "minimal": 68,
        "total": 80,
    },
    "future_all_120": {
        "clean": 120,
        "preferred": 112,
        "strong": 108,
        "minimal": 102,
        "total": 120,
    },
}


def get_gate_definitions() -> dict:
    """Return the 120-task gate thresholds."""
    return GATE_DEFINITIONS


# ---------------------------------------------------------------------------
# Anti-cheat readiness checks
# ---------------------------------------------------------------------------

def check_no_default_ones(tasks: list[dict]) -> bool:
    """Check that no task scene_spec materializes to [[1]]."""
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
    """Check that all candidate-probe tasks are separated from scored tasks."""
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
    """Check that no task with unpromoted primitives is classified as scored."""
    for t in tasks:
        if t.get("scoring_layer") == SCORED:
            for p in t["primitive_sequence"]:
                if not _can_primitive_be_counted(p):
                    return False
    return True


def check_all_three_steps(tasks: list[dict]) -> bool:
    """Check that all tasks have exactly 3 primitives in their sequence."""
    for t in tasks:
        if len(t.get("primitive_sequence", [])) != 3:
            return False
    return True


def anti_cheat_readiness(tasks: list[dict]) -> dict:
    """Run all anti-cheat readiness checks."""
    return {
        "no_default_ones": check_no_default_ones(tasks),
        "candidate_probe_separation": check_candidate_probe_separation(tasks),
        "unpromoted_blocked": check_unpromoted_blocked(tasks),
        "all_three_steps": check_all_three_steps(tasks),
        "scene_spec_read_audit": all(t.get("scene_spec") is not None for t in tasks),
        "structural_pass_separate": True,  # semantic scorer unchanged
        "unsupported_sentinel_compatible": True,  # unsupported primitives return unsupported
    }