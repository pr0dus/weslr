"""WESLR ARC-AGI-2 schema constants.

Synthetic-only. No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

SCHEMA_VERSION_V1 = "WeslrArcSolverStagingV1"
CONTRACT_NAME_V1 = "weslr_arc_solver_staging_v1"
CONTRACT_VERSION_V1 = "v1"

# Grid constraints
MAX_GRID_WIDTH_V1 = 30
MAX_GRID_HEIGHT_V1 = 30
ALLOWED_CELL_VALUES_V1 = tuple(range(10))

# Submission constraints
MAX_ATTEMPTS_PER_TEST_V1 = 2
MAX_TASKS_PER_SUBMISSION_V1 = 1000

# Family names
FAMILY_NAMES_V1 = (
    "object_bbox",
    "shape_geometry",
    "color_role",
    "resize_tile",
    "count_quantity",
    "symmetry_line",
    "hole_row_column",
    "marker_copy",
    "fallback",
)
