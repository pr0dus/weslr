"""WESLR ARC-AGI-2 adapter — dummy bundle builder for testing.

Synthetic-only. No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_dummy_bundle_v1(
    task_id: str,
    train_pairs: Sequence[Mapping[str, Any]],
    test_inputs: Sequence[Any],
) -> dict[str, Any]:
    """Build a dummy bundle for testing the staging package structure."""
    return {
        "task_id": task_id,
        "train_pairs": list(train_pairs),
        "test_inputs": list(test_inputs),
        "synthetic_only": True,
    }
