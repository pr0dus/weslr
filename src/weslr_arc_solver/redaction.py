"""WESLR ARC-AGI-2 redaction utilities.

Synthetic-only. No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


REDACTION_KEYS_V1 = (
    "expected_output",
    "solution",
    "public_solution",
    "answer_key",
    "notes",
)


def redact_forbidden_keys_v1(data: Any) -> Any:
    """Recursively remove forbidden keys from a data structure."""
    if isinstance(data, dict):
        return {
            k: redact_forbidden_keys_v1(v)
            for k, v in data.items()
            if k not in REDACTION_KEYS_V1
        }
    elif isinstance(data, list):
        return [redact_forbidden_keys_v1(item) for item in data]
    return deepcopy(data)
