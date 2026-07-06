"""WESLR ARC-AGI-2 Kaggle submission format converter.

Converts WESLR submission packets to Kaggle-ready JSON format.

Kaggle format:
    {
        "task_id_1": [
            {"attempt_1": [[...], ...], "attempt_2": [[...], ...]},
            ...
        ],
        ...
    }

No WESLR metadata.
No extra keys.
No forbidden keys.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Mapping, Sequence

FORBIDDEN_KEYS_V1 = frozenset({
    "expected_output",
    "solution",
    "public_solution",
    "answer_key",
})

REQUIRED_ATTEMPT_KEYS_V1 = frozenset({"attempt_1", "attempt_2"})


def _validate_grid(grid: Any) -> list[list[int]]:
    """Validate and return a grid. Raises ValueError if invalid."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    width = None
    result: list[list[int]] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, list):
            raise ValueError(f"row[{row_index}] must be a list")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"row[{row_index}] has {len(row)} columns, expected {width}")
        int_row: list[int] = []
        for col_index, cell in enumerate(row):
            if not isinstance(cell, int) or isinstance(cell, bool):
                raise ValueError(f"grid[{row_index}][{col_index}] must be int")
            if cell < 0 or cell > 9:
                raise ValueError(f"grid[{row_index}][{col_index}] value {cell} out of range 0-9")
            int_row.append(cell)
        result.append(int_row)
    return result


def convert_weslr_to_kaggle_v1(weslr_packet: Any) -> dict[str, list[dict[str, list[list[int]]]]]:
    """Convert a WESLR submission packet to Kaggle-ready format.

    Args:
        weslr_packet: WESLR submission packet dict (from solve_challenges).

    Returns:
        Kaggle-format dict: task_id -> list of {attempt_1: grid, attempt_2: grid}.

    Raises:
        ValueError: If the packet is malformed or contains forbidden keys.
    """
    if not isinstance(weslr_packet, dict):
        raise ValueError("weslr_packet must be a dict")

    task_entries = weslr_packet.get("task_entries", weslr_packet.get("entries", []))
    if not isinstance(task_entries, list):
        raise ValueError("weslr_packet must contain task_entries or entries list")

    result: dict[str, list[dict[str, list[list[int]]]]] = {}

    for entry_index, entry in enumerate(task_entries):
        if not isinstance(entry, dict):
            raise ValueError(f"entry[{entry_index}] is not a dict")

        task_id = entry.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError(f"entry[{entry_index}] has invalid task_id: {task_id!r}")

        # Check for forbidden keys at entry level
        for key in FORBIDDEN_KEYS_V1:
            if key in entry:
                raise ValueError(f"entry[{entry_index}] ({task_id}): forbidden key '{key}'")

        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        if not isinstance(test_packets, list):
            raise ValueError(f"entry[{entry_index}] ({task_id}): test_input_packets is not a list")

        test_entries: list[dict[str, list[list[int]]]] = []

        for pkt_index, tp in enumerate(test_packets):
            if not isinstance(tp, dict):
                raise ValueError(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: not a dict")

            # Check for forbidden keys at packet level
            for key in FORBIDDEN_KEYS_V1:
                if key in tp:
                    raise ValueError(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: forbidden key '{key}'")

            attempts = tp.get("attempts", [])
            if not isinstance(attempts, list):
                raise ValueError(f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: attempts is not a list")

            if len(attempts) < 2:
                raise ValueError(
                    f"entry[{entry_index}] ({task_id}) packet[{pkt_index}]: "
                    f"expected at least 2 attempts, got {len(attempts)}"
                )

            test_entry: dict[str, list[list[int]]] = {}
            for rank, attempt in enumerate(attempts[:2], 1):
                attempt_key = f"attempt_{rank}"

                if not isinstance(attempt, dict):
                    raise ValueError(
                        f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] "
                        f"attempt[{rank - 1}]: not a dict"
                    )

                # Check for forbidden keys at attempt level
                for key in FORBIDDEN_KEYS_V1:
                    if key in attempt:
                        raise ValueError(
                            f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] "
                            f"attempt[{rank - 1}]: forbidden key '{key}'"
                        )

                grid = attempt.get("grid")
                if grid is None:
                    raise ValueError(
                        f"entry[{entry_index}] ({task_id}) packet[{pkt_index}] "
                        f"attempt[{rank - 1}]: missing 'grid'"
                    )

                test_entry[attempt_key] = _validate_grid(grid)

            test_entries.append(test_entry)

        result[task_id] = test_entries

    return result


def convert_weslr_to_kaggle_json_v1(weslr_packet: Any, **json_kwargs: Any) -> str:
    """Convert WESLR packet to Kaggle-format JSON string.

    Args:
        weslr_packet: WESLR submission packet dict.
        **json_kwargs: Additional kwargs for json.dumps (e.g., indent=2).

    Returns:
        Kaggle-format JSON string.
    """
    kaggle = convert_weslr_to_kaggle_v1(weslr_packet)
    return json.dumps(kaggle, **json_kwargs)


def validate_kaggle_submission_v1(kaggle_data: Any) -> dict[str, Any]:
    """Validate a Kaggle-format submission.

    Args:
        kaggle_data: Kaggle-format submission dict.

    Returns:
        {"valid": bool, "task_count": int, "test_input_count": int, "issues": [str, ...]}
    """
    issues: list[str] = []

    if not isinstance(kaggle_data, dict):
        return {"valid": False, "task_count": 0, "test_input_count": 0, "issues": ["not a dict"]}

    task_count = len(kaggle_data)
    test_input_count = 0

    for task_id, test_entries in kaggle_data.items():
        if not isinstance(test_entries, list):
            issues.append(f"task {task_id}: value is not a list")
            continue

        for entry_index, entry in enumerate(test_entries):
            if not isinstance(entry, dict):
                issues.append(f"task {task_id} entry[{entry_index}]: not a dict")
                continue

            test_input_count += 1

            # Check for extra keys
            entry_keys = set(entry.keys())
            if entry_keys != REQUIRED_ATTEMPT_KEYS_V1:
                extra = entry_keys - REQUIRED_ATTEMPT_KEYS_V1
                missing = REQUIRED_ATTEMPT_KEYS_V1 - entry_keys
                if extra:
                    issues.append(f"task {task_id} entry[{entry_index}]: extra keys {extra}")
                if missing:
                    issues.append(f"task {task_id} entry[{entry_index}]: missing keys {missing}")

            # Check for forbidden keys
            for key in FORBIDDEN_KEYS_V1:
                if key in entry:
                    issues.append(f"task {task_id} entry[{entry_index}]: forbidden key '{key}'")

            # Validate grids
            for attempt_key in ("attempt_1", "attempt_2"):
                grid = entry.get(attempt_key)
                if grid is None:
                    issues.append(f"task {task_id} entry[{entry_index}]: missing {attempt_key}")
                else:
                    try:
                        _validate_grid(grid)
                    except ValueError as e:
                        issues.append(f"task {task_id} entry[{entry_index}] {attempt_key}: {e}")

    # Check for absolute local paths
    packet_json = json.dumps(kaggle_data)
    if "/data/data/com.termux" in packet_json:
        issues.append("output contains /data/data/com.termux path")
    if "arc-agi2-public-source" in packet_json:
        issues.append("output contains arc-agi2-public-source path")

    return {
        "valid": len(issues) == 0,
        "task_count": task_count,
        "test_input_count": test_input_count,
        "issues": issues,
    }
