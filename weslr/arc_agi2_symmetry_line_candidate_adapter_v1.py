"""ARC-AGI-2 symmetry completion and line extension capability V1.

Synthetic-only solver capability for:
- complete_horizontal_symmetry
- complete_vertical_symmetry
- extend_line_to_boundary

No public ARC data, no scoring, no submission.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_top2_attempt_packet_v1,
    build_arc_agi2_submission_packet_v1,
    build_arc_agi2_submission_task_entry_v1,
)

ADAPTER_NAME_V1 = "arc_symmetry_line_completion_v1"
SCHEMA_VERSION_V1 = "ArcSymmetryLineCompletionV1"


def _grid(rows: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(map(int, row)) for row in rows]


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _grids_equal(a: Any, b: Any) -> bool:
    if not isinstance(a, list) or not isinstance(b, list):
        return False
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if not isinstance(ra, list) or not isinstance(rb, list):
            return False
        if len(ra) != len(rb):
            return False
        for ca, cb in zip(ra, rb):
            if int(ca) != int(cb):
                return False
    return True


def _pair_input(pair: Mapping[str, Any]) -> list[list[int]]:
    raw = pair.get("input", [])
    return _grid(raw)


def _pair_output(pair: Mapping[str, Any]) -> list[list[int]]:
    raw = pair.get("output", [])
    return _grid(raw)


def _hflip(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _vflip(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return list(reversed(grid))


def _non_background_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    """Return (r, c, color) for all non-zero cells."""
    cells: list[tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != 0:
                cells.append((r, c, int(cell)))
    return cells


def _is_horizontal_line(grid: Sequence[Sequence[int]]) -> bool:
    """Check if non-zero cells form a single horizontal line segment."""
    cells = _non_background_cells(grid)
    if not cells:
        return False
    rows = set(c[0] for c in cells)
    if len(rows) != 1:
        return False
    cols = sorted(c[1] for c in cells)
    # Check contiguous
    for i in range(1, len(cols)):
        if cols[i] - cols[i - 1] != 1:
            return False
    # Check same color
    colors = set(c[2] for c in cells)
    return len(colors) == 1


def _is_vertical_line(grid: Sequence[Sequence[int]]) -> bool:
    """Check if non-zero cells form a single vertical line segment."""
    cells = _non_background_cells(grid)
    if not cells:
        return False
    cols = set(c[1] for c in cells)
    if len(cols) != 1:
        return False
    rows = sorted(c[0] for c in cells)
    for i in range(1, len(rows)):
        if rows[i] - rows[i - 1] != 1:
            return False
    colors = set(c[2] for c in cells)
    return len(colors) == 1


# --- Symmetry completion ---

def _infer_horizontal_symmetry(train_pairs: Sequence[Mapping[str, Any]]) -> str | None:
    """Infer horizontal symmetry direction from train pairs.
    Returns 'left_to_right' if train output is left half + mirror of right half.
    Returns 'right_to_left' if train output is right half + mirror of left half.
    Returns None if ambiguous.
    """
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)
        if len(train_in) != len(train_out):
            continue
        h = len(train_in)
        w = len(train_in[0])
        if w < 2:
            continue
        mid = w // 2
        # Check left_to_right: left half of output matches left half of input,
        # right half of output is mirror of left half
        left_in = [row[:mid] for row in train_in]
        left_out = [row[:mid] for row in train_out]
        right_out = [row[mid:] for row in train_out]
        if _grids_equal(left_in, left_out) and _grids_equal(_hflip(left_in), right_out):
            return "left_to_right"
        # Check right_to_left: right half of output matches right half of input,
        # left half of output is mirror of right half
        right_in = [row[mid:] for row in train_in]
        if _grids_equal(right_in, right_out) and _grids_equal(_hflip(right_in), left_out):
            return "right_to_left"
    return None


def _infer_vertical_symmetry(train_pairs: Sequence[Mapping[str, Any]]) -> str | None:
    """Infer vertical symmetry direction from train pairs."""
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)
        if len(train_in) != len(train_out):
            continue
        h = len(train_in)
        if h < 2:
            continue
        mid = h // 2
        top_in = train_in[:mid]
        top_out = train_out[:mid]
        bottom_out = train_out[mid:]
        if _grids_equal(top_in, top_out) and _grids_equal(_vflip(top_in), bottom_out):
            return "top_to_bottom"
        bottom_in = train_in[mid:]
        if _grids_equal(bottom_in, bottom_out) and _grids_equal(_vflip(bottom_in), top_out):
            return "bottom_to_top"
    return None


def _complete_horizontal_symmetry(
    test_input: Sequence[Sequence[int]],
    direction: str,
) -> list[list[int]] | None:
    """Complete horizontal symmetry on test input."""
    h = len(test_input)
    w = len(test_input[0])
    if w < 2:
        return None
    mid = w // 2
    output = [list(row) for row in test_input]
    if direction == "left_to_right":
        for r in range(h):
            for c in range(mid):
                mirror_c = w - 1 - c
                if output[r][mirror_c] == 0:
                    output[r][mirror_c] = output[r][c]
    elif direction == "right_to_left":
        for r in range(h):
            for c in range(mid, w):
                mirror_c = w - 1 - c
                if output[r][mirror_c] == 0:
                    output[r][mirror_c] = output[r][c]
    else:
        return None
    return output


def _complete_vertical_symmetry(
    test_input: Sequence[Sequence[int]],
    direction: str,
) -> list[list[int]] | None:
    """Complete vertical symmetry on test input."""
    h = len(test_input)
    if h < 2:
        return None
    mid = h // 2
    output = [list(row) for row in test_input]
    if direction == "top_to_bottom":
        for r in range(mid):
            mirror_r = h - 1 - r
            for c in range(len(output[0])):
                if output[mirror_r][c] == 0:
                    output[mirror_r][c] = output[r][c]
    elif direction == "bottom_to_top":
        for r in range(mid, h):
            mirror_r = h - 1 - r
            for c in range(len(output[0])):
                if output[mirror_r][c] == 0:
                    output[mirror_r][c] = output[r][c]
    else:
        return None
    return output


# --- Line extension ---

def _infer_line_extension(train_pairs: Sequence[Mapping[str, Any]]) -> str | None:
    """Infer line extension direction from train pairs.
    Returns 'horizontal' or 'vertical' or None.
    """
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)
        if _is_horizontal_line(train_in) and _is_horizontal_line(train_out):
            # Check that output extends to full width
            h = len(train_out)
            w = len(train_out[0])
            cells_out = _non_background_cells(train_out)
            if len(cells_out) == w:
                return "horizontal"
        if _is_vertical_line(train_in) and _is_vertical_line(train_out):
            h = len(train_out)
            cells_out = _non_background_cells(train_out)
            if len(cells_out) == h:
                return "vertical"
    return None


def _extend_horizontal_line(
    test_input: Sequence[Sequence[int]],
) -> list[list[int]] | None:
    """Extend horizontal line to full width."""
    cells = _non_background_cells(test_input)
    if not cells:
        return None
    rows = set(c[0] for c in cells)
    if len(rows) != 1:
        return None
    row_idx = list(rows)[0]
    color = cells[0][2]
    w = len(test_input[0])
    output = [list(row) for row in test_input]
    for c in range(w):
        output[row_idx][c] = color
    return output


def _extend_vertical_line(
    test_input: Sequence[Sequence[int]],
) -> list[list[int]] | None:
    """Extend vertical line to full height."""
    cells = _non_background_cells(test_input)
    if not cells:
        return None
    cols = set(c[1] for c in cells)
    if len(cols) != 1:
        return None
    col_idx = list(cols)[0]
    color = cells[0][2]
    h = len(test_input)
    output = [list(row) for row in test_input]
    for r in range(h):
        output[r][col_idx] = color
    return output


# --- Main solver ---

def solve_symmetry_line_task(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
) -> list[dict[str, Any]]:
    """Solve a symmetry or line extension task. Returns candidates."""
    test_grid = _grid(test_input)
    candidates: list[dict[str, Any]] = []

    # Try horizontal symmetry
    h_dir = _infer_horizontal_symmetry(train_pairs)
    if h_dir is not None:
        result = _complete_horizontal_symmetry(test_grid, h_dir)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "complete_horizontal_symmetry",
                "confidence": 0.9,
                "metadata": {"direction": h_dir, "source": ADAPTER_NAME_V1},
            })

    # Try vertical symmetry
    v_dir = _infer_vertical_symmetry(train_pairs)
    if v_dir is not None:
        result = _complete_vertical_symmetry(test_grid, v_dir)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "complete_vertical_symmetry",
                "confidence": 0.9,
                "metadata": {"direction": v_dir, "source": ADAPTER_NAME_V1},
            })

    # Try line extension — try both orientations regardless of train inference
    # The train may show one orientation but the test may have the other
    if _is_horizontal_line(test_grid):
        result = _extend_horizontal_line(test_grid)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "extend_line_to_boundary",
                "confidence": 0.9,
                "metadata": {"direction": "horizontal", "source": ADAPTER_NAME_V1},
            })
    if _is_vertical_line(test_grid):
        result = _extend_vertical_line(test_grid)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "extend_line_to_boundary",
                "confidence": 0.9,
                "metadata": {"direction": "vertical", "source": ADAPTER_NAME_V1},
            })

    return candidates


def _candidate_packets_for_top2(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
    symmetry_candidates: list[dict[str, Any]],
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Build top-2 candidate packets from symmetry/line candidates."""
    candidate_packets: list[dict[str, Any]] = []
    used_fallback = False

    for candidate in symmetry_candidates[:2]:
        family = _safe_text(candidate.get("family", "symmetry_line"))
        output = deepcopy(candidate["grid"])
        metadata = {
            "adapter_name": ADAPTER_NAME_V1,
            "schema_version": SCHEMA_VERSION_V1,
            "task_id": task_id,
            "test_input_index": test_input_index,
            "source_family": family,
            "direction": candidate.get("metadata", {}).get("direction", ""),
            "synthetic_only": True,
            "source_kind": "symmetry_line_solver",
            "trace_labels": ["symmetry_line", family, "synthetic_only"],
        }
        candidate_packets.append({
            "candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_kind": "symmetry_line_solver",
            "synthetic_only": True,
            "grid": output,
            "confidence_label": "high",
            "evidence_labels": ["symmetry_line", family, "synthetic_only"],
            "leakage_flags": {
                "uses_test_output": False,
                "uses_solution_file": False,
                "uses_answer_key": False,
                "uses_hidden_private_data": False,
                "uses_task_id_shortcut": False,
                "uses_notes_shortcut": False,
                "lookup_table_detected": False,
            },
            "metadata": metadata,
        })

    # Ensure at least 2 candidate packets for top2 contract
    if len(candidate_packets) == 1 and fallback_candidate_packets:
        for fb in fallback_candidate_packets:
            candidate_packets.append(dict(fb))
            break
        used_fallback = True
    elif len(candidate_packets) == 1:
        # Duplicate the single candidate as fallback
        dup = dict(candidate_packets[0])
        dup["metadata"] = dict(dup.get("metadata", {}))
        dup["metadata"]["source_family"] = "fallback"
        candidate_packets.append(dup)
        used_fallback = True

    if not candidate_packets and fallback_candidate_packets:
        for fb in fallback_candidate_packets:
            candidate_packets.append(dict(fb))
        used_fallback = True

    return candidate_packets, used_fallback


def build_arc_agi2_symmetry_line_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_symmetry_line_task",
    test_input_index: Any = 0,
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a top-2 attempt packet for symmetry/line completion."""
    task_id_text = str(task_id)
    test_input_index_int = int(test_input_index)
    test_grid = _grid(test_input)

    symmetry_candidates = solve_symmetry_line_task(train_pairs, test_grid)
    candidate_packets, used_fallback = _candidate_packets_for_top2(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        test_input=test_grid,
        symmetry_candidates=symmetry_candidates,
        fallback_candidate_packets=fallback_candidate_packets,
    )

    packet_metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id_text,
        "test_input_index": test_input_index_int,
        "candidate_count": len(symmetry_candidates),
        "used_fallback": used_fallback,
        "synthetic_only": True,
        "trace_labels": ["symmetry_line", "top2_attempts", "synthetic_only"],
    }
    if isinstance(metadata, Mapping):
        packet_metadata.update(dict(metadata))

    return build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        candidate_packets=candidate_packets,
        metadata=packet_metadata,
    )


def build_arc_agi2_symmetry_line_submission_v1(
    task_packets: Sequence[Mapping[str, Any]],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a submission packet for symmetry/line tasks."""
    task_entries = []
    for packet in task_packets:
        task_entries.append(
            build_arc_agi2_submission_task_entry_v1(
                task_id=str(packet.get("task_id", "")),
                test_input_packets=[packet],
                metadata={"adapter_name": ADAPTER_NAME_V1, "synthetic_only": True},
            )
        )
    return build_arc_agi2_submission_packet_v1(
        task_entries=task_entries,
        metadata={"adapter_name": ADAPTER_NAME_V1, "synthetic_only": True, **(dict(metadata or {}))},
    )


__all__ = [
    "ADAPTER_NAME_V1",
    "SCHEMA_VERSION_V1",
    "solve_symmetry_line_task",
    "build_arc_agi2_symmetry_line_top2_attempt_packet_v1",
    "build_arc_agi2_symmetry_line_submission_v1",
]