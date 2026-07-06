"""WESLR ARC-AGI-2 public data gate.

Synthetic-only. Blocks public ARC data access.
No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

import os
from typing import Any


PUBLIC_DATA_PATTERNS_V1 = (
    "arc-agi2",
    "arc-prize",
    "kaggle/input",
    "public_source",
)


def is_public_data_path_v1(path: str) -> bool:
    """Check if a path looks like a public ARC data path."""
    normalized = os.path.normpath(path).lower()
    for pattern in PUBLIC_DATA_PATTERNS_V1:
        if pattern.lower() in normalized:
            return True
    return False


def gate_public_data_access_v1(path: str) -> None:
    """Raise RuntimeError if the path looks like public ARC data."""
    if is_public_data_path_v1(path):
        raise RuntimeError(
            f"Public data access blocked: {path}. "
            "This package is synthetic-only."
        )
