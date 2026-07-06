"""WESLR ARC-AGI-2 Kaggle Format Converter Tests V1.

Tests for the Kaggle submission format converter.
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

import pytest

from weslr_arc_solver.kaggle_format import (
    convert_weslr_to_kaggle_v1,
    convert_weslr_to_kaggle_json_v1,
    validate_kaggle_submission_v1,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def valid_weslr_packet():
    """A valid WESLR submission packet."""
    return {
        "contract_name": "arc_agi2_submission_contract_v1",
        "contract_version": "v1",
        "synthetic_only": True,
        "kaggle_ready": False,
        "denied_authority": ["runtime", "persistence", "tool_execution"],
        "task_entries": [
            {
                "task_id": "task_001",
                "test_input_packets": [
                    {
                        "task_id": "task_001",
                        "test_input_index": 0,
                        "attempts": [
                            {
                                "attempt_id": "task_001_test0_rank1",
                                "grid": [[1, 0], [0, 1]],
                                "source_candidate_id": "c1",
                                "rank": 1,
                                "confidence_label": "high",
                                "evidence_labels": ["color_role"],
                                "leakage_flags": {},
                                "metadata": {"family": "color_role"},
                            },
                            {
                                "attempt_id": "task_001_test0_rank2",
                                "grid": [[0, 1], [1, 0]],
                                "source_candidate_id": "c2",
                                "rank": 2,
                                "confidence_label": "medium",
                                "evidence_labels": ["fallback"],
                                "leakage_flags": {},
                                "metadata": {"family": "fallback"},
                            },
                        ],
                    }
                ],
                "leakage_flags": {},
                "metadata": {"synthetic_only": True},
            }
        ],
        "leakage_flags": {},
        "metadata": {"synthetic_only": True, "kaggle_ready": False},
    }


@pytest.fixture
def multi_test_weslr_packet():
    """A WESLR packet with multiple test inputs per task."""
    return {
        "task_entries": [
            {
                "task_id": "multi_test_task",
                "test_input_packets": [
                    {
                        "task_id": "multi_test_task",
                        "test_input_index": 0,
                        "attempts": [
                            {"grid": [[1]], "rank": 1},
                            {"grid": [[2]], "rank": 2},
                        ],
                    },
                    {
                        "task_id": "multi_test_task",
                        "test_input_index": 1,
                        "attempts": [
                            {"grid": [[3]], "rank": 1},
                            {"grid": [[4]], "rank": 2},
                        ],
                    },
                ],
            }
        ],
    }


@pytest.fixture
def expected_kaggle_single():
    """Expected Kaggle output for single-test task."""
    return {
        "task_001": [
            {
                "attempt_1": [[1, 0], [0, 1]],
                "attempt_2": [[0, 1], [1, 0]],
            }
        ]
    }


# ── Test 1: Basic conversion ─────────────────────────────────────────────────

def test_basic_conversion(valid_weslr_packet, expected_kaggle_single):
    """Verify basic conversion strips metadata and keeps grids."""
    result = convert_weslr_to_kaggle_v1(valid_weslr_packet)
    assert result == expected_kaggle_single
    # Verify no metadata keys
    result_json = json.dumps(result)
    assert "kaggle_ready" not in result_json
    assert "synthetic_only" not in result_json
    assert "contract_name" not in result_json
    assert "metadata" not in result_json
    assert "leakage_flags" not in result_json


# ── Test 2: Multiple test inputs ─────────────────────────────────────────────

def test_multiple_test_inputs(multi_test_weslr_packet):
    """Verify converter handles multiple test inputs."""
    result = convert_weslr_to_kaggle_v1(multi_test_weslr_packet)
    assert "multi_test_task" in result
    assert len(result["multi_test_task"]) == 2
    assert result["multi_test_task"][0]["attempt_1"] == [[1]]
    assert result["multi_test_task"][0]["attempt_2"] == [[2]]
    assert result["multi_test_task"][1]["attempt_1"] == [[3]]
    assert result["multi_test_task"][1]["attempt_2"] == [[4]]


# ── Test 3: JSON output ───────────────────────────────────────────────────────

def test_json_output(valid_weslr_packet):
    """Verify JSON output is valid and clean."""
    json_str = convert_weslr_to_kaggle_json_v1(valid_weslr_packet, indent=2)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert "task_001" in parsed
    # Verify no metadata in JSON string
    assert "kaggle_ready" not in json_str
    assert "synthetic_only" not in json_str
    assert "contract_name" not in json_str


# ── Test 4: Validation passes on valid output ───────────────────────────────

def test_validation_passes(valid_weslr_packet):
    """Verify validation passes on valid Kaggle output."""
    kaggle = convert_weslr_to_kaggle_v1(valid_weslr_packet)
    result = validate_kaggle_submission_v1(kaggle)
    assert result["valid"], f"Validation failed: {result.get('issues', [])}"
    assert result["task_count"] == 1
    assert result["test_input_count"] == 1


# ── Test 5: Validation catches missing attempts ─────────────────────────────

def test_validation_catches_missing_attempts():
    """Verify validation catches missing attempt keys."""
    bad = {
        "task_001": [
            {"attempt_1": [[0]]}  # Missing attempt_2
        ]
    }
    result = validate_kaggle_submission_v1(bad)
    assert not result["valid"]
    assert any("missing" in issue for issue in result["issues"])


# ── Test 6: Validation catches extra keys ────────────────────────────────────

def test_validation_catches_extra_keys():
    """Verify validation catches extra keys in entries."""
    bad = {
        "task_001": [
            {
                "attempt_1": [[0]],
                "attempt_2": [[1]],
                "extra_key": "bad",
            }
        ]
    }
    result = validate_kaggle_submission_v1(bad)
    assert not result["valid"]
    assert any("extra" in issue for issue in result["issues"])


# ── Test 7: Validation catches forbidden keys ────────────────────────────────

def test_validation_catches_forbidden_keys():
    """Verify validation catches forbidden keys."""
    bad = {
        "task_001": [
            {
                "attempt_1": [[0]],
                "attempt_2": [[1]],
                "expected_output": [[0]],
            }
        ]
    }
    result = validate_kaggle_submission_v1(bad)
    assert not result["valid"]
    assert any("forbidden" in issue for issue in result["issues"])


# ── Test 8: Validation catches invalid grid cells ────────────────────────────

def test_validation_catches_invalid_cells():
    """Verify validation catches invalid cell values."""
    bad = {
        "task_001": [
            {
                "attempt_1": [[10]],  # 10 is out of range
                "attempt_2": [[0]],
            }
        ]
    }
    result = validate_kaggle_submission_v1(bad)
    assert not result["valid"]
    assert any("out of range" in issue for issue in result["issues"])


# ── Test 9: Converter rejects forbidden keys in WESLR packet ─────────────────

def test_converter_rejects_forbidden_keys():
    """Verify converter raises ValueError on forbidden keys."""
    bad_packet = {
        "task_entries": [
            {
                "task_id": "bad",
                "test_input_packets": [
                    {
                        "attempts": [
                            {"grid": [[0]], "expected_output": [[0]]},
                            {"grid": [[1]]},
                        ],
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValueError, match="forbidden"):
        convert_weslr_to_kaggle_v1(bad_packet)


# ── Test 10: Converter rejects malformed WESLR packets ──────────────────────

def test_converter_rejects_malformed():
    """Verify converter raises ValueError on malformed packets."""
    with pytest.raises(ValueError):
        convert_weslr_to_kaggle_v1("not a dict")
    with pytest.raises(ValueError):
        convert_weslr_to_kaggle_v1({"task_entries": "not a list"})


# ── Test 11: Converter handles entries key (not task_entries) ────────────────

def test_converter_handles_entries_key():
    """Verify converter handles 'entries' key as alternative to 'task_entries'."""
    packet = {
        "entries": [
            {
                "task_id": "test",
                "packets": [
                    {
                        "attempts": [
                            {"grid": [[1]]},
                            {"grid": [[2]]},
                        ],
                    }
                ],
            }
        ]
    }
    result = convert_weslr_to_kaggle_v1(packet)
    assert "test" in result
    assert result["test"][0]["attempt_1"] == [[1]]


# ── Test 12: Deterministic conversion ────────────────────────────────────────

def test_deterministic_conversion(valid_weslr_packet):
    """Verify conversion is deterministic."""
    r1 = convert_weslr_to_kaggle_v1(valid_weslr_packet)
    r2 = convert_weslr_to_kaggle_v1(valid_weslr_packet)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


# ── Test 13: No metadata in output ───────────────────────────────────────────

def test_no_metadata_in_output(valid_weslr_packet):
    """Verify no WESLR metadata remains in output."""
    result = convert_weslr_to_kaggle_v1(valid_weslr_packet)
    result_json = json.dumps(result)
    metadata_patterns = [
        "kaggle_ready",
        "synthetic_only",
        "contract_name",
        "contract_version",
        "denied_authority",
        "leakage_flags",
        "metadata",
        "schema_version",
        "source_candidate_id",
        "confidence_label",
        "evidence_labels",
        "attempt_id",
    ]
    for pattern in metadata_patterns:
        assert pattern not in result_json, f"Output contains metadata: {pattern}"


# ── Test 14: Sample submission shape compatibility ───────────────────────────

def test_sample_submission_shape():
    """Verify output matches sample submission shape."""
    # Create a WESLR packet that mimics the sample submission structure
    packet = {
        "task_entries": [
            {
                "task_id": "00576224",
                "test_input_packets": [
                    {
                        "attempts": [
                            {"grid": [[1, 0], [0, 1]]},
                            {"grid": [[0, 1], [1, 0]]},
                        ],
                    }
                ],
            }
        ]
    }
    result = convert_weslr_to_kaggle_v1(packet)
    # Sample format: dict of task_id -> list of {attempt_1, attempt_2}
    assert isinstance(result, dict)
    assert "00576224" in result
    assert isinstance(result["00576224"], list)
    assert len(result["00576224"]) == 1
    entry = result["00576224"][0]
    assert isinstance(entry, dict)
    assert set(entry.keys()) == {"attempt_1", "attempt_2"}
    assert isinstance(entry["attempt_1"], list)
    assert isinstance(entry["attempt_2"], list)


# ── Test 15: Multiple tasks ─────────────────────────────────────────────────

def test_multiple_tasks():
    """Verify converter handles multiple tasks."""
    packet = {
        "task_entries": [
            {
                "task_id": "task_a",
                "test_input_packets": [
                    {
                        "attempts": [
                            {"grid": [[1]]},
                            {"grid": [[2]]},
                        ],
                    }
                ],
            },
            {
                "task_id": "task_b",
                "test_input_packets": [
                    {
                        "attempts": [
                            {"grid": [[3]]},
                            {"grid": [[4]]},
                        ],
                    }
                ],
            },
        ]
    }
    result = convert_weslr_to_kaggle_v1(packet)
    assert len(result) == 2
    assert "task_a" in result
    assert "task_b" in result
