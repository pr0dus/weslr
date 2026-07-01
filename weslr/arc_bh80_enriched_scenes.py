"""Enriched scene specs for representative BH80 tasks.

These specs provide real grids with objects, distractors, holes, and edge contact
so the materializer can produce non-trivial input grids for semantic scoring.
"""

from __future__ import annotations

from typing import Any


def get_enriched_scene_spec(task_id: str) -> dict:
    """Return an enriched scene_spec for a representative BH80 task.

    For tasks not yet enriched, returns a basic-but-non-trivial spec
    with a single 3x3 object on a 10x10 grid.
    """
    specs = {
        # Known-family anchors with real scenes
        "BH80_001": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_001", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [3, 3]}},
            ],
        },
        "BH80_002": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_002", "type": "rectangle", "attributes": {"color": 1, "position": [0, 0], "size": [3, 3]}},
                {"object_id": "obj_002_d", "type": "rectangle", "attributes": {"color": 1, "position": [6, 6], "size": [2, 2]}},
            ],
            "distractors": [
                {"object_id": "dist_002", "type": "rectangle", "attributes": {"color": 1, "position": [5, 5], "size": [1, 1]}},
            ],
        },
        "BH80_005": {
            "grid_size": [8, 8], "background": 0,
            "initial_objects": [
                {"object_id": "obj_005", "type": "cross", "attributes": {"color": 2, "position": [3, 3]}},
            ],
        },
        "BH80_006": {
            "grid_size": [8, 8], "background": 0,
            "initial_objects": [
                {"object_id": "obj_006", "type": "donut", "attributes": {"color": 3, "position": [2, 2], "size": [4, 4]}},
            ],
        },
        "BH80_012": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_012a", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 3]}},
                {"object_id": "obj_012b", "type": "rectangle", "attributes": {"color": 2, "position": [5, 5], "size": [3, 3]}},
            ],
            "distractors": [
                {"object_id": "dist_012", "type": "rectangle", "attributes": {"color": 1, "position": [7, 1], "size": [2, 2]}},
            ],
        },
        # Hybrid tasks
        "BH80_023": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_023", "type": "l_shape", "attributes": {"color": 1, "position": [0, 0]}},
                {"object_id": "obj_023b", "type": "rectangle", "attributes": {"color": 1, "position": [5, 5], "size": [2, 2]}},
            ],
        },
        "BH80_025": {
            "grid_size": [8, 8], "background": 0,
            "initial_objects": [
                {"object_id": "obj_025", "type": "rectangle", "attributes": {"color": 2, "position": [0, 0], "size": [3, 3]}},
            ],
            "distractors": [
                {"object_id": "dist_025", "type": "rectangle", "attributes": {"color": 2, "position": [4, 4], "size": [1, 1]}},
            ],
        },
        # Mutation tasks
        "BH80_048": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_048", "type": "disconnected", "attributes": {"color": 1, "position": [2, 1], "size": [3, 5]}},
            ],
        },
        "BH80_050": {
            "grid_size": [12, 12], "background": 0,
            "initial_objects": [
                {"object_id": "obj_050", "type": "donut", "attributes": {"color": 2, "position": [3, 3], "size": [5, 5]}},
            ],
            "distractors": [
                {"object_id": "dist_050a", "type": "rectangle", "attributes": {"color": 2, "position": [0, 0], "size": [1, 1]}},
                {"object_id": "dist_050b", "type": "rectangle", "attributes": {"color": 2, "position": [10, 10], "size": [1, 1]}},
            ],
        },
        # Unknown-family candidates
        "BH80_061": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_061a", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [3, 2]}},
                {"object_id": "obj_061b", "type": "rectangle", "attributes": {"color": 1, "position": [6, 6], "size": [2, 3]}},
            ],
        },
        "BH80_069": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_069a", "type": "cross", "attributes": {"color": 1, "position": [1, 1]}},
                {"object_id": "obj_069b", "type": "cross", "attributes": {"color": 2, "position": [5, 5]}},
            ],
            "distractors": [
                {"object_id": "dist_069", "type": "rectangle", "attributes": {"color": 1, "position": [8, 1], "size": [1, 1]}},
            ],
        },
        "BH80_080": {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [
                {"object_id": "obj_080", "type": "rectangle", "attributes": {"color": 3, "position": [2, 2], "size": [4, 4]}},
            ],
            "distractors": [
                {"object_id": "dist_080a", "type": "rectangle", "attributes": {"color": 3, "position": [7, 0], "size": [1, 1]}},
                {"object_id": "dist_080b", "type": "rectangle", "attributes": {"color": 3, "position": [0, 8], "size": [1, 1]}},
            ],
        },
    }
    return specs.get(task_id, {
        "grid_size": [10, 10], "background": 0,
        "initial_objects": [
            {"object_id": f"obj_{task_id}", "type": "rectangle", "attributes": {"color": 1, "position": [3, 3], "size": [3, 3]}},
        ],
    })