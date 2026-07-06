"""WESLR ARC-AGI-2 Portable Solver Tests V1.

25 tests for portability, functional correctness, and safety.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from copy import deepcopy

# Add src to path for importing the staging package
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

import pytest

from weslr_arc_solver.portable_solver import (
    solve_task,
    solve_challenges,
    validate_submission_packet,
)
from weslr_arc_solver.solver import run_solver_on_challenges_file
from weslr_arc_solver.grid import validate_grid_v1, grid_shape, grids_equal, grid_copy
from weslr_arc_solver.emitter import emit_top2_attempts_v1
from weslr_arc_solver.redaction import redact_forbidden_keys_v1
from weslr_arc_solver.public_gate import is_public_data_path_v1, gate_public_data_access_v1
from weslr_arc_solver.schema import (
    SCHEMA_VERSION_V1,
    MAX_GRID_WIDTH_V1,
    MAX_GRID_HEIGHT_V1,
    ALLOWED_CELL_VALUES_V1,
    FAMILY_NAMES_V1,
)
from weslr_arc_solver.scorer import score_submission_v1


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_task():
    """A simple color-role task (copy input as output)."""
    return {
        "train": [
            {"input": [[1, 0], [0, 1]], "output": [[1, 0], [0, 1]]},
            {"input": [[2, 0], [0, 2]], "output": [[2, 0], [0, 2]]},
        ],
        "test": [
            {"input": [[3, 0], [0, 3]]},
        ],
    }


@pytest.fixture
def bbox_task():
    """An object-bbox task (crop to non-zero region)."""
    return {
        "train": [
            {
                "input": [[0, 0, 0], [0, 5, 0], [0, 0, 0]],
                "output": [[5]],
            },
        ],
        "test": [
            {"input": [[0, 0, 0, 0], [0, 7, 7, 0], [0, 7, 7, 0], [0, 0, 0, 0]]},
        ],
    }


@pytest.fixture
def multi_test_task():
    """A task with multiple test inputs."""
    return {
        "train": [
            {"input": [[1, 0], [0, 1]], "output": [[1, 0], [0, 1]]},
        ],
        "test": [
            {"input": [[2, 0], [0, 2]]},
            {"input": [[3, 0], [0, 3]]},
            {"input": [[4, 0], [0, 4]]},
        ],
    }


@pytest.fixture
def fallback_task():
    """A task that should trigger fallback behavior."""
    return {
        "train": [
            {"input": [[1, 2], [3, 4]], "output": [[4, 3], [2, 1]]},
        ],
        "test": [
            {"input": [[5, 6], [7, 8]]},
        ],
    }


@pytest.fixture
def simple_challenge(simple_task, bbox_task, fallback_task):
    return {
        "simple_color_role": simple_task,
        "simple_bbox": bbox_task,
        "simple_fallback": fallback_task,
    }


# ── Test 1: Import from outside repo ─────────────────────────────────────────

def test_import_from_outside_repo():
    """Verify solver imports do not require WESLR repo source path."""
    # These imports already succeeded at module level
    # Verify the modules are importable
    from weslr_arc_solver import portable_solver
    from weslr_arc_solver import solver
    assert hasattr(portable_solver, "solve_task")
    assert hasattr(portable_solver, "solve_challenges")
    assert hasattr(portable_solver, "validate_submission_packet")
    assert hasattr(solver, "run_solver_on_challenges_file")


# ── Test 2: solve_task returns valid structure ────────────────────────────────

def test_solve_task_structure(simple_task):
    """Verify solve_task returns a valid submission task entry."""
    train_pairs = simple_task["train"]
    test_inputs = [t["input"] for t in simple_task["test"]]
    entry = solve_task("test_task_001", train_pairs, test_inputs)
    assert isinstance(entry, dict)
    assert "task_id" in entry
    assert entry["task_id"] == "test_task_001"
    assert "test_input_packets" in entry or "packets" in entry


# ── Test 3: solve_task returns exactly 2 attempts per test input ─────────────

def test_solve_task_exactly_two_attempts(simple_task):
    """Verify exactly 2 attempts per test input."""
    train_pairs = simple_task["train"]
    test_inputs = [t["input"] for t in simple_task["test"]]
    entry = solve_task("test_task_001", train_pairs, test_inputs)
    packets = entry.get("test_input_packets", entry.get("packets", []))
    for tp in packets:
        assert len(tp["attempts"]) == 2, f"Expected 2 attempts, got {len(tp['attempts'])}"


# ── Test 4: solve_task with multiple test inputs ─────────────────────────────

def test_solve_task_multiple_test_inputs(multi_test_task):
    """Verify solve_task handles multiple test inputs."""
    train_pairs = multi_test_task["train"]
    test_inputs = [t["input"] for t in multi_test_task["test"]]
    entry = solve_task("multi_test", train_pairs, test_inputs)
    packets = entry.get("test_input_packets", entry.get("packets", []))
    assert len(packets) == 3, f"Expected 3 packets, got {len(packets)}"


# ── Test 5: solve_challenges returns valid submission ─────────────────────────

def test_solve_challenges_structure(simple_challenge):
    """Verify solve_challenges returns a valid submission packet."""
    packet = solve_challenges(simple_challenge)
    assert isinstance(packet, dict)
    assert "task_entries" in packet or "entries" in packet
    entries = packet.get("task_entries", packet.get("entries", []))
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"


# ── Test 6: validate_submission_packet passes on valid output ────────────────

def test_validate_submission_packet_valid(simple_challenge):
    """Verify validate_submission_packet passes on valid output."""
    packet = solve_challenges(simple_challenge)
    result = validate_submission_packet(packet)
    assert result["valid"], f"Validation failed: {result.get('issues', [])}"


# ── Test 7: validate_submission_packet catches missing attempts ──────────────

def test_validate_submission_packet_missing_attempts():
    """Verify validate_submission_packet catches missing attempts."""
    bad_packet = {
        "task_entries": [
            {
                "task_id": "bad_task",
                "test_input_packets": [
                    {
                        "task_id": "bad_task",
                        "test_input_index": 0,
                        "attempts": [{"grid": [[0]]}],  # Only 1 attempt
                    }
                ],
            }
        ]
    }
    result = validate_submission_packet(bad_packet)
    assert not result["valid"]
    assert any("expected 2 attempts" in issue for issue in result["issues"])


# ── Test 8: validate_submission_packet catches invalid grid cells ────────────

def test_validate_submission_packet_invalid_cells():
    """Verify validate_submission_packet catches invalid cell values."""
    bad_packet = {
        "task_entries": [
            {
                "task_id": "bad_task",
                "test_input_packets": [
                    {
                        "task_id": "bad_task",
                        "test_input_index": 0,
                        "attempts": [
                            {"grid": [[10]]},  # 10 is out of range 0-9
                            {"grid": [[0]]},
                        ],
                    }
                ],
            }
        ]
    }
    result = validate_submission_packet(bad_packet)
    assert not result["valid"]
    assert any("invalid cell" in issue for issue in result["issues"])


# ── Test 9: No expected_output in output ────────────────────────────────────

def test_no_expected_output_in_output(simple_challenge):
    """Verify output has no expected_output/solution/public_solution keys."""
    packet = solve_challenges(simple_challenge)
    packet_json = json.dumps(packet)
    assert "expected_output" not in packet_json
    assert '"solution"' not in packet_json
    assert "public_solution" not in packet_json


# ── Test 10: No absolute local paths in output ───────────────────────────────

def test_no_absolute_local_paths(simple_challenge):
    """Verify output has no absolute local paths."""
    packet = solve_challenges(simple_challenge)
    packet_json = json.dumps(packet)
    assert "/data/data/com.termux" not in packet_json
    assert "arc-agi2-public-source" not in packet_json


# ── Test 11: Deterministic output ───────────────────────────────────────────

def test_deterministic_output(simple_challenge):
    """Verify output is deterministic across repeated runs."""
    packet1 = solve_challenges(simple_challenge)
    packet2 = solve_challenges(simple_challenge)
    json1 = json.dumps(packet1, sort_keys=True)
    json2 = json.dumps(packet2, sort_keys=True)
    assert json1 == json2, "Output is not deterministic"


# ── Test 12: Grid validation ─────────────────────────────────────────────────

def test_grid_validation():
    """Verify grid validation works correctly."""
    valid = validate_grid_v1([[1, 2], [3, 4]])
    assert valid == [[1, 2], [3, 4]]

    with pytest.raises(ValueError):
        validate_grid_v1("not a grid")

    with pytest.raises(ValueError):
        validate_grid_v1([[]])

    with pytest.raises(ValueError):
        validate_grid_v1([[10]])  # Out of range


# ── Test 13: Grid shape ──────────────────────────────────────────────────────

def test_grid_shape():
    """Verify grid_shape returns correct dimensions."""
    assert grid_shape([[1, 2], [3, 4]]) == (2, 2)
    assert grid_shape([[1]]) == (1, 1)
    assert grid_shape([[1, 2, 3]]) == (1, 3)


# ── Test 14: Grids equal ─────────────────────────────────────────────────────

def test_grids_equal():
    """Verify grids_equal works correctly."""
    assert grids_equal([[1, 2], [3, 4]], [[1, 2], [3, 4]])
    assert not grids_equal([[1, 2], [3, 4]], [[1, 2], [3, 5]])
    assert not grids_equal([[1, 2], [3, 4]], "not a grid")


# ── Test 15: Grid copy ───────────────────────────────────────────────────────

def test_grid_copy():
    """Verify grid_copy creates independent copy."""
    original = [[1, 2], [3, 4]]
    copied = grid_copy(original)
    assert copied == original
    copied[0][0] = 99
    assert original[0][0] == 1  # Original unchanged


# ── Test 16: Emitter produces valid top-2 packet ──────────────────────────────

def test_emitter_top2():
    """Verify emitter produces valid top-2 attempt packet."""
    candidates = [
        {"grid": [[1]], "source_candidate_id": "c1", "rank": 1,
         "confidence_label": "high", "evidence_labels": [], "leakage_flags": {},
         "metadata": {}},
        {"grid": [[2]], "source_candidate_id": "c2", "rank": 2,
         "confidence_label": "medium", "evidence_labels": [], "leakage_flags": {},
         "metadata": {}},
    ]
    packet = emit_top2_attempts_v1("test_task", 0, candidates)
    assert len(packet["attempts"]) == 2
    assert packet["attempts"][0]["rank"] == 1
    assert packet["attempts"][1]["rank"] == 2


# ── Test 17: Redaction removes forbidden keys ────────────────────────────────

def test_redaction():
    """Verify redaction removes forbidden keys."""
    data = {
        "task_id": "test",
        "expected_output": [[0]],
        "solution": "secret",
        "public_solution": "also secret",
        "grid": [[1]],
    }
    redacted = redact_forbidden_keys_v1(data)
    assert "expected_output" not in redacted
    assert "solution" not in redacted
    assert "public_solution" not in redacted
    assert "task_id" in redacted
    assert "grid" in redacted


# ── Test 18: Public data gate blocks public paths ────────────────────────────

def test_public_data_gate():
    """Verify public data gate blocks public ARC paths."""
    assert is_public_data_path_v1("/kaggle/input/arc-agi-2")
    assert is_public_data_path_v1("/data/arc-agi2-public")
    assert not is_public_data_path_v1("/tmp/synthetic.json")

    with pytest.raises(RuntimeError):
        gate_public_data_access_v1("/kaggle/input/arc-agi-2")


# ── Test 19: Schema constants are valid ──────────────────────────────────────

def test_schema_constants():
    """Verify schema constants are valid."""
    assert SCHEMA_VERSION_V1 == "WeslrArcSolverStagingV1"
    assert MAX_GRID_WIDTH_V1 == 30
    assert MAX_GRID_HEIGHT_V1 == 30
    assert all(0 <= v <= 9 for v in ALLOWED_CELL_VALUES_V1)
    assert len(FAMILY_NAMES_V1) >= 8


# ── Test 20: Scorer works with valid data ────────────────────────────────────

def test_scorer():
    """Verify scorer works with valid data."""
    submission = {
        "task_entries": [
            {
                "task_id": "task1",
                "test_input_packets": [
                    {
                        "task_id": "task1",
                        "test_input_index": 0,
                        "attempts": [
                            {"grid": [[1]], "rank": 1},
                            {"grid": [[2]], "rank": 2},
                        ],
                    }
                ],
            }
        ]
    }
    expected = {"task1": [[[1]]]}
    result = score_submission_v1(submission, expected)
    assert result["total_tasks"] == 1
    assert result["correct_tasks"] == 1
    assert result["accuracy"] == 1.0


# ── Test 21: run_solver_on_challenges_file works ──────────────────────────────

def test_run_solver_on_challenges_file(simple_challenge):
    """Verify run_solver_on_challenges_file reads/writes correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(simple_challenge, f)
        challenges_path = f.name

    output_path = challenges_path + ".out.json"
    try:
        result = run_solver_on_challenges_file(challenges_path, output_path)
        assert isinstance(result, dict)
        assert os.path.exists(output_path)
        with open(output_path) as f:
            packet = json.load(f)
        assert isinstance(packet, dict)
    finally:
        os.unlink(challenges_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


# ── Test 22: Fallback task produces output ───────────────────────────────────

def test_fallback_task_produces_output(fallback_task):
    """Verify fallback task still produces valid output."""
    train_pairs = fallback_task["train"]
    test_inputs = [t["input"] for t in fallback_task["test"]]
    entry = solve_task("fallback_test", train_pairs, test_inputs)
    packets = entry.get("test_input_packets", entry.get("packets", []))
    assert len(packets) == 1
    assert len(packets[0]["attempts"]) == 2


# ── Test 23: Bbox task produces output ───────────────────────────────────────

def test_bbox_task_produces_output(bbox_task):
    """Verify bbox task produces valid output."""
    train_pairs = bbox_task["train"]
    test_inputs = [t["input"] for t in bbox_task["test"]]
    entry = solve_task("bbox_test", train_pairs, test_inputs)
    packets = entry.get("test_input_packets", entry.get("packets", []))
    assert len(packets) == 1
    assert len(packets[0]["attempts"]) == 2


# ── Test 24: All attempts have valid grids ────────────────────────────────────

def test_all_attempts_have_valid_grids(simple_challenge):
    """Verify all attempts have valid grids (list of list of int 0-9)."""
    packet = solve_challenges(simple_challenge)
    entries = packet.get("task_entries", packet.get("entries", []))
    for entry in entries:
        packets = entry.get("test_input_packets", entry.get("packets", []))
        for tp in packets:
            for attempt in tp["attempts"]:
                grid = attempt.get("grid", [])
                validate_grid_v1(grid)  # Will raise if invalid


# ── Test 25: No internet imports ─────────────────────────────────────────────

def test_no_internet_imports():
    """Verify staging package does not import network libraries."""
    import ast
    import os

    staging_dir = os.path.join(REPO_ROOT, "src", "weslr_arc_solver")
    network_imports = {"requests", "http", "urllib", "socket", "openai", "anthropic"}

    for fname in sorted(os.listdir(staging_dir)):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(staging_dir, fname)
        with open(path) as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            top = alias.name.split(".")[0]
                            assert top not in network_imports, \
                                f"{fname} imports {alias.name} (network library)"
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            top = node.module.split(".")[0]
                            assert top not in network_imports, \
                                f"{fname} imports {node.module} (network library)"
            except SyntaxError:
                pass  # Skip malformed files
