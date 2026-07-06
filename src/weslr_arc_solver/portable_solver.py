"""WESLR ARC-AGI-2 portable solver wrapper.

Wraps the real WESLR solver stack (universal family runner, capability
candidate aggregator, primitive registry, family discovery, compositional
executor, and all adapters) for use from a Kaggle-style staging package.

The portable solver does NOT copy the WESLR solver modules. Instead it:
1. Auto-detects the solver source directory (via WESLR_REPO_ROOT env var or
   sibling-directory lookup)
2. Supports both weslr/ and weslr_solver/ directory names
3. Adds the solver source to sys.path and aliases the module name if needed
4. Imports the real solver modules

Synthetic-only. No public ARC ingestion. No scoring claims. No Kaggle writes.
No internet. No provider calls. No model calls.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from copy import deepcopy
from typing import Any, Mapping, Sequence

# ── Solver source directory names ───────────────────────────────────────────

_SOLVER_DIR_NAMES: tuple[str, ...] = ("weslr", "weslr_solver")

# ── WESLR repo path resolution ──────────────────────────────────────────────

_WESLR_REPO_ROOT: str | None = None


def _find_solver_dir(root: str) -> str | None:
    """Check if root contains a solver source directory.

    Returns the full path to the solver directory (e.g., root/weslr/)
    or None if not found.
    """
    for name in _SOLVER_DIR_NAMES:
        candidate = os.path.join(root, name)
        if os.path.isdir(candidate):
            return candidate
    return None


def _resolve_weslr_repo_root() -> str:
    """Resolve the WESLR repo root directory.

    Resolution order:
    1. WESLR_REPO_ROOT environment variable
    2. Parent of this package's directory (sibling layout)
    3. Grandparent of this package's directory (nested layout)

    Supports both weslr/ and weslr_solver/ solver directory names.
    """
    env_path = os.environ.get("WESLR_REPO_ROOT")
    if env_path and _find_solver_dir(env_path):
        return os.path.abspath(env_path)

    # Sibling layout: src/ and solver dir are siblings
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(pkg_dir)
    candidate = os.path.dirname(src_dir)
    if _find_solver_dir(candidate):
        return candidate

    # Nested layout: src/weslr_arc_solver/ inside solver dir
    grandparent = os.path.dirname(candidate)
    if _find_solver_dir(grandparent):
        return grandparent

    checked = [
        f"WESLR_REPO_ROOT={os.environ.get('WESLR_REPO_ROOT', '(not set)')}",
        f"sibling of {pkg_dir}",
        f"grandparent of {pkg_dir}",
    ]
    raise RuntimeError(
        "Cannot find WESLR solver source directory. "
        f"Checked: {checked}. "
        "Set WESLR_REPO_ROOT environment variable to a directory containing "
        f"one of: {', '.join(_SOLVER_DIR_NAMES)}."
    )


def _ensure_weslr_imports() -> None:
    """Ensure the WESLR solver modules are importable.

    Adds the solver source directory to sys.path and aliases
    weslr_solver -> weslr if needed so that 'from weslr.xxx import ...'
    works regardless of the actual directory name.
    """
    global _WESLR_REPO_ROOT
    if _WESLR_REPO_ROOT is not None:
        return
    _WESLR_REPO_ROOT = _resolve_weslr_repo_root()

    solver_dir = _find_solver_dir(_WESLR_REPO_ROOT)
    if solver_dir is None:
        raise RuntimeError(
            f"No solver source directory found in {_WESLR_REPO_ROOT}. "
            f"Expected one of: {', '.join(_SOLVER_DIR_NAMES)}."
        )

    # Add the repo root to sys.path (needed for some cross-module references)
    if _WESLR_REPO_ROOT not in sys.path:
        sys.path.insert(0, _WESLR_REPO_ROOT)

    # Add the solver directory to sys.path
    if solver_dir not in sys.path:
        sys.path.insert(0, solver_dir)

    # If the solver directory is not named 'weslr', alias it so that
    # 'from weslr.xxx import ...' works.
    solver_dir_name = os.path.basename(solver_dir)
    if solver_dir_name != "weslr":
        try:
            mod = importlib.import_module(solver_dir_name)
            sys.modules["weslr"] = mod
        except ImportError:
            # If the module can't be imported directly (e.g., no __init__.py),
            # create a simple module alias
            import types
            alias = types.ModuleType("weslr")
            alias.__path__ = [solver_dir]
            alias.__file__ = os.path.join(solver_dir, "__init__.py")
            sys.modules["weslr"] = alias


# ── Lazy imports ─────────────────────────────────────────────────────────────

def _get_universal_runner():
    _ensure_weslr_imports()
    from weslr.arc_universal_family_runner_v1 import (
        run_universal_family_solver,
        UniversalRunnerResult,
        DEFAULT_TASK_ID_V1,
        FALLBACK_FAMILY_V1,
    )
    return run_universal_family_solver, UniversalRunnerResult, DEFAULT_TASK_ID_V1, FALLBACK_FAMILY_V1


def _get_submission_contract():
    _ensure_weslr_imports()
    from weslr.arc_agi2_submission_contract import (
        build_arc_agi2_submission_task_entry_v1,
        build_arc_agi2_submission_packet_v1,
        validate_arc_agi2_submission_packet_v1,
        summarize_arc_agi2_submission_packet_v1,
    )
    return (
        build_arc_agi2_submission_task_entry_v1,
        build_arc_agi2_submission_packet_v1,
        validate_arc_agi2_submission_packet_v1,
        summarize_arc_agi2_submission_packet_v1,
    )


def _get_aggregator():
    _ensure_weslr_imports()
    from weslr.arc_agi2_capability_candidate_aggregator_v1 import (
        build_arc_agi2_capability_candidate_top2_attempt_packet_v1,
    )
    return build_arc_agi2_capability_candidate_top2_attempt_packet_v1


# ── Public API ───────────────────────────────────────────────────────────────

def solve_task(
    task_id: str,
    train_pairs: Sequence[Mapping[str, Any]],
    test_inputs: Sequence[Any],
    enabled_families: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Solve a single ARC-AGI-2 task.

    Args:
        task_id: Unique task identifier.
        train_pairs: List of {"input_grid": ..., "output_grid": ...} dicts.
        test_inputs: List of test input grids.
        enabled_families: Optional list of family names to enable.
            Default: all known families.

    Returns:
        A submission task entry dict with exactly 2 attempts per test input.
        No expected_output, solution, or public_solution keys.
    """
    run_universal_family_solver, _, default_task_id, _ = _get_universal_runner()
    build_entry, _, _, _ = _get_submission_contract()

    test_input_packets = []
    for test_index, test_input in enumerate(test_inputs):
        result = run_universal_family_solver(
            train_pairs=train_pairs,
            test_input=test_input,
            enabled_families=enabled_families,
        )
        # UniversalRunnerResult has attempt_1 and attempt_2 as dataclass fields
        attempts_data = []
        if hasattr(result, "attempt_1") and result.attempt_1 is not None:
            attempts_data.append(result.attempt_1)
        if hasattr(result, "attempt_2") and result.attempt_2 is not None:
            attempts_data.append(result.attempt_2)
        packet = {
            "task_id": task_id,
            "test_input_index": test_index,
            "attempts": [
                {
                    "attempt_id": f"{task_id}_test{test_index}_rank{rank}",
                    "grid": deepcopy(attempt.output),
                    "source_candidate_id": attempt.source,
                    "rank": rank,
                    "confidence_label": "high" if attempt.confidence > 0.8 else "medium" if attempt.confidence > 0.5 else "low",
                    "evidence_labels": [attempt.family_name] if attempt.family_name else [],
                    "leakage_flags": {},
                    "metadata": {
                        "family_name": attempt.family_name,
                        "primitive_chain": list(attempt.primitive_chain),
                        "confidence": attempt.confidence,
                        "source": attempt.source,
                    },
                }
                for rank, attempt in enumerate(attempts_data[:2], 1)
            ],
            "metadata": {
                "synthetic_only": True,
                "kaggle_ready": False,
                "solver_version": "portable_solver_v1",
            },
        }
        test_input_packets.append(packet)

    entry = build_entry(
        task_id=task_id,
        test_input_packets=test_input_packets,
        metadata={"synthetic_only": True, "kaggle_ready": False},
    )
    return entry


def solve_challenges(
    challenges: Mapping[str, Any],
    enabled_families: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Solve a challenge dict with multiple tasks.

    Args:
        challenges: Dict mapping task_id -> {"train": [...], "test": [...]}.
            Each train entry: {"input": grid, "output": grid}.
            Each test entry: {"input": grid}.
        enabled_families: Optional list of family names to enable.

    Returns:
        A full submission packet with metadata.
        Sets synthetic_only=True, kaggle_ready=False.
    """
    build_entry, build_packet, validate_packet, _ = _get_submission_contract()

    task_entries = []
    for task_id, task_data in challenges.items():
        train_pairs = []
        for pair in task_data.get("train", []):
            train_pairs.append({
                "input_grid": deepcopy(pair.get("input", pair.get("input_grid", []))),
                "output_grid": deepcopy(pair.get("output", pair.get("output_grid", []))),
            })
        test_inputs = []
        for test_entry in task_data.get("test", []):
            test_inputs.append(deepcopy(test_entry.get("input", test_entry.get("input_grid", []))))

        entry = solve_task(
            task_id=str(task_id),
            train_pairs=train_pairs,
            test_inputs=test_inputs,
            enabled_families=enabled_families,
        )
        task_entries.append(entry)

    packet = build_packet(
        task_entries=task_entries,
        metadata={
            "synthetic_only": True,
            "kaggle_ready": False,
            "solver_version": "portable_solver_v1",
        },
    )
    return packet


def validate_submission_packet(packet: Any) -> dict[str, Any]:
    """Validate a submission packet structure.

    Checks:
    - Valid JSON structure
    - Exactly 2 attempts per test input
    - All grids are valid (list of list of int 0-9)
    - No expected_output/solution/public_solution keys
    - No absolute local paths

    Returns:
        {"valid": bool, "task_count": int, "test_input_count": int,
         "issues": [str, ...]}
    """
    issues: list[str] = []

    if not isinstance(packet, dict):
        return {"valid": False, "task_count": 0, "test_input_count": 0, "issues": ["packet is not a dict"]}

    task_entries = packet.get("task_entries", packet.get("entries", []))
    if not isinstance(task_entries, list):
        return {"valid": False, "task_count": 0, "test_input_count": 0, "issues": ["task_entries is not a list"]}

    task_count = len(task_entries)
    test_input_count = 0

    forbidden_keys = {"expected_output", "solution", "public_solution"}

    for entry_index, entry in enumerate(task_entries):
        if not isinstance(entry, dict):
            issues.append(f"entry[{entry_index}] is not a dict")
            continue

        # Check for forbidden keys at entry level
        for key in forbidden_keys:
            if key in entry:
                issues.append(f"entry[{entry_index}] contains forbidden key: {key}")

        test_packets = entry.get("test_input_packets", entry.get("packets", []))
        if not isinstance(test_packets, list):
            issues.append(f"entry[{entry_index}].test_input_packets is not a list")
            continue

        for packet_index, tp in enumerate(test_packets):
            if not isinstance(tp, dict):
                issues.append(f"entry[{entry_index}].test_input_packets[{packet_index}] is not a dict")
                continue

            test_input_count += 1

            # Check for forbidden keys at packet level
            for key in forbidden_keys:
                if key in tp:
                    issues.append(f"entry[{entry_index}].test_input_packets[{packet_index}] contains forbidden key: {key}")

            attempts = tp.get("attempts", [])
            if not isinstance(attempts, list):
                issues.append(f"entry[{entry_index}].test_input_packets[{packet_index}].attempts is not a list")
                continue

            if len(attempts) != 2:
                issues.append(
                    f"entry[{entry_index}].test_input_packets[{packet_index}]: "
                    f"expected 2 attempts, got {len(attempts)}"
                )

            for attempt_index, attempt in enumerate(attempts):
                if not isinstance(attempt, dict):
                    issues.append(
                        f"entry[{entry_index}].test_input_packets[{packet_index}]."
                        f"attempts[{attempt_index}] is not a dict"
                    )
                    continue

                # Check for forbidden keys at attempt level
                for key in forbidden_keys:
                    if key in attempt:
                        issues.append(
                            f"entry[{entry_index}].test_input_packets[{packet_index}]."
                            f"attempts[{attempt_index}] contains forbidden key: {key}"
                        )

                grid = attempt.get("grid", [])
                if not isinstance(grid, list) or not grid:
                    issues.append(
                        f"entry[{entry_index}].test_input_packets[{packet_index}]."
                        f"attempts[{attempt_index}].grid is not a valid grid"
                    )
                    continue

                for row_index, row in enumerate(grid):
                    if not isinstance(row, list):
                        issues.append(
                            f"entry[{entry_index}].test_input_packets[{packet_index}]."
                            f"attempts[{attempt_index}].grid[{row_index}] is not a list"
                        )
                        continue
                    for col_index, cell in enumerate(row):
                        if not isinstance(cell, int) or cell < 0 or cell > 9:
                            issues.append(
                                f"entry[{entry_index}].test_input_packets[{packet_index}]."
                                f"attempts[{attempt_index}].grid[{row_index}][{col_index}]: "
                                f"invalid cell value {cell}"
                            )

    # Check for absolute local paths in JSON string
    packet_json = json.dumps(packet)
    if "/data/data/com.termux" in packet_json:
        issues.append("packet JSON contains /data/data/com.termux path")
    if "arc-agi2-public-source" in packet_json:
        issues.append("packet JSON contains arc-agi2-public-source path")

    return {
        "valid": len(issues) == 0,
        "task_count": task_count,
        "test_input_count": test_input_count,
        "issues": issues,
    }
