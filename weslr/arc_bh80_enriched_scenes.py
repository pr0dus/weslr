"""Enriched scene specs for all 80 BH80 tasks.

Each spec is deterministic, non-trivial, and matches the task's hardness axes:
- Axis 3 (distractor pressure): includes distractor objects
- Axis 7 (edge/boundary pressure): objects near/touching canvas edges
- Axis 8 (multi-object relational): multiple objects
- Axis 9 (shape identity pressure): non-rectangle shapes (donut, l_shape, cross, disconnected)
"""

from __future__ import annotations
from typing import Any

def _spec(grid_h: int, grid_w: int, objects: list[dict], distractors: list[dict] | None = None, noise: int = 0) -> dict:
    return {
        "grid_size": [grid_w, grid_h],
        "background": 0,
        "initial_objects": objects,
        "distractors": distractors or [],
        "noise_pixels": noise,
    }

def _obj(oid: str, shape: str, color: int, row: int, col: int, h: int = 2, w: int = 2) -> dict:
    return {"object_id": oid, "type": shape, "attributes": {"color": color, "position": [row, col], "size": [h, w]}}

def get_enriched_scene_spec(task_id: str) -> dict:
    return _ALL_ENRICHED_SPECS.get(task_id, _spec(10, 10, [_obj("default", "rectangle", 1, 3, 3, 3, 3)]))


_ALL_ENRICHED_SPECS: dict[str, dict] = {
    # === Known-family anchors (18 tasks) ===
    "BH80_001": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3)]),
    "BH80_002": _spec(10, 10, [_obj("o1", "rectangle", 1, 0, 0, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 2, 2)], [_obj("d1", "rectangle", 1, 5, 5, 1, 1)]),
    "BH80_003": _spec(8, 8, [_obj("o1", "rectangle", 1, 2, 2, 3, 3)], [_obj("d1", "rectangle", 1, 5, 5, 1, 1)], noise=3),
    "BH80_004": _spec(8, 8, [_obj("o1", "rectangle", 1, 0, 0, 2, 2), _obj("o2", "rectangle", 2, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 0, 5, 1, 1)]),
    "BH80_005": _spec(8, 8, [_obj("o1", "cross", 2, 3, 3)]),
    "BH80_006": _spec(8, 8, [_obj("o1", "donut", 3, 2, 2, 4, 4)]),
    "BH80_007": _spec(10, 10, [_obj("o1", "rectangle", 1, 3, 3, 3, 3)]),
    "BH80_008": _spec(10, 10, [_obj("o1", "donut", 2, 3, 3, 3, 3)]),
    "BH80_009": _spec(8, 8, [_obj("o1", "rectangle", 1, 1, 1, 4, 4)]),
    "BH80_010": _spec(8, 8, [_obj("o1", "rectangle", 1, 0, 0, 3, 3), _obj("o2", "rectangle", 1, 4, 4, 3, 3)], [_obj("d1", "rectangle", 1, 3, 0, 1, 1)]),
    "BH80_011": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),
    "BH80_012": _spec(10, 10, [_obj("o1a", "rectangle", 1, 1, 1, 3, 3), _obj("o1b", "rectangle", 2, 5, 5, 3, 3)], [_obj("d1", "rectangle", 1, 7, 1, 2, 2)]),
    "BH80_013": _spec(10, 10, [_obj("o1", "l_shape", 1, 2, 2)]),
    "BH80_014": _spec(10, 10, [_obj("o1", "l_shape", 2, 0, 0)], [_obj("d1", "rectangle", 2, 5, 5, 1, 1)]),
    "BH80_015": _spec(8, 8, [_obj("o1", "rectangle", 1, 1, 1, 3, 3)]),
    "BH80_016": _spec(8, 8, [_obj("o1", "cross", 3, 0, 0)]),
    "BH80_017": _spec(12, 12, [_obj("o1", "donut", 2, 3, 3, 5, 5)], [_obj("d1", "rectangle", 2, 0, 0, 1, 1), _obj("d2", "rectangle", 2, 10, 10, 1, 1)]),
    "BH80_018": _spec(10, 10, [_obj("o1a", "rectangle", 1, 1, 1, 3, 3), _obj("o1b", "rectangle", 1, 5, 5, 3, 3)], [_obj("d1", "rectangle", 1, 8, 1, 1, 1), _obj("d2", "rectangle", 1, 1, 8, 1, 1)]),

    # === Hybrid BH-A (10 tasks) ===
    "BH80_019": _spec(10, 10, [_obj("o1", "rectangle", 1, 3, 3, 3, 3)]),
    "BH80_020": _spec(10, 10, [_obj("o1", "rectangle", 1, 0, 0, 3, 3)]),
    "BH80_021": _spec(10, 10, [_obj("o1", "rectangle", 2, 2, 2, 4, 4)]),
    "BH80_022": _spec(10, 10, [_obj("o1", "donut", 1, 3, 3, 3, 3)]),
    "BH80_023": _spec(10, 10, [_obj("o1", "l_shape", 1, 0, 0), _obj("o2", "rectangle", 1, 5, 5, 2, 2)]),
    "BH80_024": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 2, 2)]),
    "BH80_025": _spec(8, 8, [_obj("o1", "rectangle", 2, 0, 0, 3, 3)], [_obj("d1", "rectangle", 2, 4, 4, 1, 1)]),
    "BH80_026": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 3, 3), _obj("o3", "rectangle", 1, 7, 1, 1, 1)]),
    "BH80_027": _spec(10, 10, [_obj("o1", "l_shape", 2, 0, 0)]),
    "BH80_028": _spec(10, 10, [_obj("o1", "rectangle", 1, 0, 0, 2, 2), _obj("o2", "rectangle", 1, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 7, 0, 1, 1)]),

    # === Hybrid BH-B (10 tasks) ===
    "BH80_029": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3)]),
    "BH80_030": _spec(10, 10, [_obj("o1", "rectangle", 1, 3, 3, 3, 3), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),
    "BH80_031": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 3, 3)]),
    "BH80_032": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 1, 6, 0, 2, 2)]),
    "BH80_033": _spec(10, 10, [_obj("o1", "rectangle", 2, 0, 0, 3, 3), _obj("o2", "rectangle", 2, 5, 5, 2, 2)], [_obj("d1", "rectangle", 2, 7, 7, 1, 1)]),
    "BH80_034": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 3, 3), _obj("o3", "rectangle", 1, 8, 1, 1, 1)], [_obj("d1", "rectangle", 1, 1, 8, 1, 1)]),
    "BH80_035": _spec(10, 10, [_obj("o1a", "rectangle", 1, 1, 1, 3, 3), _obj("o1b", "rectangle", 1, 6, 6, 3, 3)], [_obj("d1", "rectangle", 1, 3, 7, 1, 1), _obj("d2", "rectangle", 1, 7, 3, 1, 1)]),
    "BH80_036": _spec(10, 10, [_obj("o1", "cross", 1, 1, 1), _obj("o2", "cross", 2, 5, 5)], [_obj("d1", "rectangle", 1, 8, 1, 1, 1)]),
    "BH80_037": _spec(10, 10, [_obj("o1", "donut", 1, 2, 2, 3, 3)]),
    "BH80_038": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 2, 6, 0, 2, 2)]),

    # === Mutation BH-C (14 tasks) ===
    "BH80_039": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 2, 2), _obj("o2", "rectangle", 1, 5, 5, 2, 2), _obj("o3", "rectangle", 1, 7, 1, 1, 1)]),
    "BH80_040": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 2, 5, 5, 2, 2)]),
    "BH80_041": _spec(8, 8, [_obj("o1", "rectangle", 1, 0, 0, 3, 3)]),
    "BH80_042": _spec(10, 10, [_obj("o1", "donut", 2, 3, 3, 3, 3)]),
    "BH80_043": _spec(12, 12, [_obj("o1", "cross", 1, 4, 4), _obj("o2", "rectangle", 2, 1, 1, 2, 2)]),
    "BH80_044": _spec(10, 10, [_obj("o1", "l_shape", 1, 0, 0), _obj("o2", "l_shape", 2, 5, 5)]),
    "BH80_045": _spec(8, 8, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 1, 1, 1)], noise=5),
    "BH80_046": _spec(8, 8, [_obj("o1", "rectangle", 1, 0, 0, 3, 3)]),
    "BH80_047": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 2, 2), _obj("o2", "rectangle", 1, 4, 4, 2, 2), _obj("o3", "rectangle", 2, 7, 7, 2, 2)]),
    "BH80_048": _spec(10, 10, [_obj("o1", "disconnected", 1, 2, 1, 3, 5)]),
    "BH80_049": _spec(10, 10, [_obj("o1", "donut", 1, 0, 0, 4, 4)]),
    "BH80_050": _spec(12, 12, [_obj("o1", "donut", 2, 3, 3, 5, 5)], [_obj("d1", "rectangle", 2, 0, 0, 1, 1), _obj("d2", "rectangle", 2, 10, 10, 1, 1)]),
    "BH80_051": _spec(10, 10, [_obj("o1", "l_shape", 1, 0, 0), _obj("o2", "l_shape", 2, 5, 5)], [_obj("d1", "rectangle", 1, 7, 7, 1, 1)]),
    "BH80_052": _spec(10, 10, [_obj("o1", "rectangle", 2, 0, 0, 3, 3)]),

    # === Mutation BH-D (6 tasks) ===
    "BH80_053": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 2, 2)]),
    "BH80_054": _spec(10, 10, [_obj("o1", "l_shape", 2, 0, 0)]),
    "BH80_055": _spec(10, 10, [_obj("o1", "rectangle", 1, 3, 3, 3, 3)]),
    "BH80_056": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3)]),
    "BH80_057": _spec(8, 8, [_obj("o1", "cross", 1, 2, 2), _obj("o2", "rectangle", 2, 5, 0, 2, 2)]),
    "BH80_058": _spec(10, 10, [_obj("o1", "rectangle", 1, 3, 3, 3, 3)]),

    # === Unknown-family BH-E (7 tasks) ===
    "BH80_059": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 2), _obj("o2", "rectangle", 1, 6, 6, 2, 3)]),
    "BH80_060": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 7, 7, 1, 1)]),
    "BH80_061": _spec(10, 10, [_obj("o1a", "rectangle", 1, 1, 1, 3, 2), _obj("o1b", "rectangle", 1, 6, 6, 2, 3)]),
    "BH80_062": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),
    "BH80_063": _spec(10, 10, [_obj("o1", "rectangle", 1, 0, 0, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 2, 2)]),
    "BH80_064": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 6, 0, 2, 2)]),
    "BH80_065": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 3, 3)]),

    # === Unknown-family BH-F (7 tasks) ===
    "BH80_066": _spec(10, 10, [_obj("o1", "rectangle", 1, 0, 0, 3, 3), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),
    "BH80_067": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 2, 5, 5, 2, 2)]),
    "BH80_068": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 7, 7, 1, 1)]),
    "BH80_069": _spec(10, 10, [_obj("o1", "cross", 1, 1, 1), _obj("o2", "cross", 2, 5, 5)], [_obj("d1", "rectangle", 1, 8, 1, 1, 1)]),
    "BH80_070": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "donut", 2, 6, 6, 3, 3)]),
    "BH80_071": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 2, 2)]),
    "BH80_072": _spec(10, 10, [_obj("o1", "l_shape", 1, 2, 2), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),

    # === Unknown-family BH-G (8 tasks) ===
    "BH80_073": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 2, 6, 6, 2, 2)]),
    "BH80_074": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 7, 7, 1, 1)]),
    "BH80_075": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 2, 6, 0, 2, 2)]),
    "BH80_076": _spec(10, 10, [_obj("o1", "rectangle", 3, 0, 0, 3, 3)], [_obj("d1", "rectangle", 3, 5, 5, 1, 1)]),
    "BH80_077": _spec(10, 10, [_obj("o1", "rectangle", 1, 1, 1, 3, 3), _obj("o2", "rectangle", 1, 5, 5, 2, 2)], [_obj("d1", "rectangle", 1, 7, 7, 1, 1)]),
    "BH80_078": _spec(10, 10, [_obj("o1", "rectangle", 3, 2, 2, 4, 4)], [_obj("d1", "rectangle", 3, 7, 0, 1, 1), _obj("d2", "rectangle", 3, 0, 8, 1, 1)]),
    "BH80_079": _spec(10, 10, [_obj("o1", "rectangle", 1, 2, 2, 3, 3), _obj("o2", "rectangle", 1, 6, 6, 2, 2)]),
    "BH80_080": _spec(10, 10, [_obj("o1", "rectangle", 3, 2, 2, 4, 4)], [_obj("d1", "rectangle", 3, 7, 0, 1, 1), _obj("d2", "rectangle", 3, 0, 8, 1, 1)]),
}