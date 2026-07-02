"""Tests for the ARC official-format toy adapter."""

from __future__ import annotations

import builtins
import json

import pytest

from weslr.arc_official_contamination_boundary import validate_contamination_boundary_record
from weslr.arc_official_format_toy_adapter import (
    export_solver_visible_toy_bundle,
    parse_toy_official_format_bundle,
    validate_toy_candidate_outputs,
    validate_toy_official_format_bundle,
    validate_toy_result_claim,
)


@pytest.fixture()
def toy_bundle():
    return {
        "task_id": "toy_arc_001",
        "train": [
            {
                "input": [[1, 1], [0, 0]],
                "output": [[1, 1], [1, 1]],
            }
        ],
        "test": [
            {
                "input": [[2, 2], [0, 0]],
                "expected_output": [[2, 2], [2, 2]],
                "candidate_output_slots": [None, None],
            }
        ],
        "bundle_provenance": {
            "source": "toy-fixture-bundle",
            "version": "toy-v1",
            "checksum": "toy-checksum-001",
        },
    }


class TestArcOfficialFormatToyAdapter:
    def test_valid_toy_official_format_task_parses(self, toy_bundle):
        parsed = parse_toy_official_format_bundle(json.dumps(toy_bundle))
        validated = validate_toy_official_format_bundle(parsed)
        assert validated["task_id"] == "toy_arc_001"
        assert validated["contamination_boundary"]["run_phase"] == "phase_1_toy_fixture_adapter"
        assert validated["contamination_boundary"]["data_class"] == "synthetic_weslr"

    def test_invalid_toy_task_is_rejected(self, toy_bundle):
        bad = dict(toy_bundle)
        bad["train"] = []
        with pytest.raises(ValueError):
            validate_toy_official_format_bundle(bad)

    @pytest.mark.parametrize(
        "field, value",
        [
            ("input", [[1, 1], [0]]),
            ("output", [[1, "x"], [1, 1]]),
        ],
    )
    def test_malformed_grid_is_rejected(self, toy_bundle, field, value):
        bad = json.loads(json.dumps(toy_bundle))
        bad["train"][0][field] = value
        with pytest.raises(ValueError):
            validate_toy_official_format_bundle(bad)

    def test_missing_train_or_test_is_rejected(self, toy_bundle):
        bad_train = dict(toy_bundle)
        bad_train.pop("train")
        with pytest.raises(ValueError):
            validate_toy_official_format_bundle(bad_train)

        bad_test = dict(toy_bundle)
        bad_test.pop("test")
        with pytest.raises(ValueError):
            validate_toy_official_format_bundle(bad_test)

    def test_solver_visible_export_strips_expected_test_output(self, toy_bundle):
        visible = export_solver_visible_toy_bundle(toy_bundle)
        assert "expected_output" not in json.dumps(visible, sort_keys=True)
        assert visible["test"][0]["candidate_output_slots"] == [None, None]
        assert set(visible) == {"task_id", "train", "test", "bundle_provenance", "schema_version"}

    def test_exactly_two_candidate_outputs_are_required(self, toy_bundle):
        grid_a = [[1, 1], [1, 1]]
        grid_b = [[0, 0], [0, 0]]
        validated = validate_toy_candidate_outputs(toy_bundle, [[grid_a, grid_b]])
        assert validated["candidate_outputs_validated"][0]["candidate_count"] == 2

    def test_one_output_rejected(self, toy_bundle):
        grid_a = [[1, 1], [1, 1]]
        with pytest.raises(ValueError):
            validate_toy_candidate_outputs(toy_bundle, [[grid_a]])

    def test_three_outputs_rejected(self, toy_bundle):
        grid_a = [[1, 1], [1, 1]]
        grid_b = [[0, 0], [0, 0]]
        grid_c = [[2, 2], [2, 2]]
        with pytest.raises(ValueError):
            validate_toy_candidate_outputs(toy_bundle, [[grid_a, grid_b, grid_c]])

    def test_hidden_private_data_class_rejected(self, toy_bundle):
        record = {
            "data_class": "hidden_private_arc",
            "run_phase": "phase_1_toy_fixture_adapter",
            "official_data_touched": False,
            "hidden_private_data_touched": True,
            "internet_tool_model_calls_during_solving": False,
            "expected_output_leakage": False,
            "internal_task_language_leakage": False,
            "synthetic_official_score_mixing": False,
        }
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    def test_official_data_class_rejected_in_toy_phase(self, toy_bundle):
        record = {
            "data_class": "public_official_arc",
            "run_phase": "phase_1_toy_fixture_adapter",
            "official_data_touched": True,
            "hidden_private_data_touched": False,
            "dataset_provenance": {"source": "official-arc", "version": "v1", "checksum": "abc123"},
            "internet_tool_model_calls_during_solving": False,
            "expected_output_leakage": False,
            "internal_task_language_leakage": False,
            "synthetic_official_score_mixing": False,
        }
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    def test_contamination_boundary_checker_passes_toy_phase(self, toy_bundle):
        validated = validate_toy_official_format_bundle(toy_bundle)
        assert validated["contamination_boundary"]["run_phase"] == "phase_1_toy_fixture_adapter"
        assert validated["contamination_boundary"]["official_data_touched"] is False

    def test_no_official_arc_data_files_are_touched(self, toy_bundle, monkeypatch):
        opened = []

        def fake_open(*args, **kwargs):
            opened.append(args[0] if args else None)
            raise AssertionError("No file IO should occur in toy adapter validation")

        monkeypatch.setattr(builtins, "open", fake_open)
        validate_toy_official_format_bundle(json.loads(json.dumps(toy_bundle)))
        assert opened == []

    def test_synthetic_scores_cannot_be_claimed_as_official(self):
        with pytest.raises(ValueError):
            validate_toy_result_claim(
                {
                    "claim_kind": "official_arc_performance",
                    "evidence_kind": "synthetic",
                    "synthetic_score": "130/130",
                }
            )
