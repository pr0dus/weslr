"""ARC-AGI-2 hole filling and row/column extraction candidate adapter V1.

Integrates hole/row-column capability into the aggregator pipeline.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from weslr.arc_hole_row_column_v1 import (
    ADAPTER_NAME_V1,
    SCHEMA_VERSION_V1,
    build_arc_agi2_hole_row_column_top2_attempt_packet_v1,
    solve_hole_row_column_task,
)

__all__ = [
    "ADAPTER_NAME_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_hole_row_column_top2_attempt_packet_v1",
    "solve_hole_row_column_task",
]
