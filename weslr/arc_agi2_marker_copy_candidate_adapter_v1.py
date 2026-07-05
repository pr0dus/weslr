"""ARC-AGI-2 marker-copy candidate adapter V1.

Integrates marker-copy capability into the aggregator pipeline.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from weslr.arc_marker_copy_v1 import (
    ADAPTER_NAME_V1,
    SCHEMA_VERSION_V1,
    build_arc_agi2_marker_copy_top2_attempt_packet_v1,
    solve_marker_copy_task,
)

__all__ = [
    "ADAPTER_NAME_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_agi2_marker_copy_top2_attempt_packet_v1",
    "solve_marker_copy_task",
]
