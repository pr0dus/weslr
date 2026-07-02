"""Tests for the ARC official-format toy end-to-end harness."""

from __future__ import annotations

import json

import pytest

from weslr.arc_official_contamination_boundary import summarize_boundary_status
from weslr.arc_official_format_toy_adapter import export_solver_visible_toy_bundle
from weslr.arc_official_format_toy_harness import (
    run_toy_official_format_harness,
    validate_toy_end_to_end_harness_boundary_record,
    validate_toy_score_claim,
)
from weslr.arc_official_format_toy_scorer import score_toy_official_format_bundle


@pytest.fixture()
def toy_bundle_one_test():
    return {
        "task_id": "toy_harness_001",
        "train": [
            {
                "input": [[1, 1], [0, 0]],
                "output": [[1, 1], [1, 1]],
            }
        ],
        "test": [
            {
                "test_id": "toy_harness_test_1",
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


@pytest.fixture()
def toy_bundle_two_tests():
    return {
        "task_id": "toy_harness_002",
        "train": [
            {
                "input": [[1, 0], [1, 0]],
                "output": [[1, 1], [1, 1]],
            }
        ],
        "test": [
            {
                "test_id": "toy_harness_test_1",
                "input": [[2, 2], [0, 0]],
                "expected_output": [[2, 2], [2, 2]],
                "candidate_output_slots": [None, None],
            },
            {
                "test_id": "toy_harness_test_2",
                "input": [[3, 3], [0, 0]],
                "expected_output": [[3, 3], [3, 3]],
                "candidate_output_slots": [None, None],
            },
        ],
        "bundle_provenance": {
            "source": "toy-fixture-bundle",
            "version": "toy-v1",
            "checksum": "toy-checksum-002",
        },
    }


class TestArcOfficialFormatToyEndToEndHarness:
    def test_end_to_end_solved_when_candidate_1_matches(self, toy_bundle_one_test):
        seen = {}

        def provider(visible_bundle):
            seen["bundle"] = visible_bundle
            assert "expected_output" not in json.dumps(visible_bundle, sort_keys=True)
            return [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]]

        result = run_toy_official_format_harness(toy_bundle_one_test, provider)
        assert result["task_solved"] is True
        assert result["toy_only"] is True
        assert result["not_official_score"] is True
        assert result["score_result"]["per_test_scoring_metadata"][0]["candidate_1_matches"] is True
        assert result["aggregate_toy_percentage"] == 100.0
        assert "expected_output" not in json.dumps(seen["bundle"], sort_keys=True)
        assert score_toy_official_format_bundle(
            toy_bundle_one_test,
            result["emitted_submission"]["candidate_outputs"],
        )["task_solved"] is True

    def test_end_to_end_solved_when_candidate_2_matches(self, toy_bundle_one_test):
        result = run_toy_official_format_harness(
            toy_bundle_one_test,
            lambda visible_bundle: [[[[0, 0], [0, 0]], [[2, 2], [2, 2]]]],
        )
        assert result["task_solved"] is True
        assert result["score_result"]["per_test_scoring_metadata"][0]["candidate_2_matches"] is True

    def test_end_to_end_failed_when_neither_matches(self, toy_bundle_one_test):
        result = run_toy_official_format_harness(
            toy_bundle_one_test,
            lambda visible_bundle: [[[[0, 0], [0, 0]], [[1, 1], [1, 1]]]],
        )
        assert result["task_failed"] is True
        assert result["score_result"]["per_test_scoring_metadata"][0]["solved"] is False

    def test_malformed_toy_fixture_rejected(self, toy_bundle_one_test):
        bad = dict(toy_bundle_one_test)
        bad.pop("train")
        with pytest.raises(ValueError):
            run_toy_official_format_harness(bad, lambda visible_bundle: [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]])

    @pytest.mark.parametrize(
        "candidate_outputs",
        [
            [[[[1, 1], [1]]]],
            [[[[1, 1], [1, 1]], [[0, 0], [0, "x"]]]],
        ],
    )
    def test_malformed_candidate_rejected(self, toy_bundle_one_test, candidate_outputs):
        with pytest.raises(ValueError):
            run_toy_official_format_harness(toy_bundle_one_test, lambda visible_bundle: candidate_outputs)

    def test_one_candidate_rejected(self, toy_bundle_one_test):
        with pytest.raises(ValueError):
            run_toy_official_format_harness(
                toy_bundle_one_test,
                lambda visible_bundle: [[[[2, 2], [2, 2]]]],
            )

    def test_three_candidates_rejected(self, toy_bundle_one_test):
        with pytest.raises(ValueError):
            run_toy_official_format_harness(
                toy_bundle_one_test,
                lambda visible_bundle: [[[[2, 2], [2, 2]], [[0, 0], [0, 0]], [[1, 1], [1, 1]]]],
            )

    def test_expected_output_never_appears_in_solver_visible_candidate_provider_input(self, toy_bundle_one_test):
        seen = {}

        def provider(visible_bundle):
            seen["bundle"] = visible_bundle
            assert "expected_output" not in json.dumps(visible_bundle, sort_keys=True)
            return [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]]

        run_toy_official_format_harness(toy_bundle_one_test, provider)
        assert "expected_output" not in json.dumps(seen["bundle"], sort_keys=True)
        assert seen["bundle"] == export_solver_visible_toy_bundle(toy_bundle_one_test)

    def test_expected_output_leakage_in_emitted_answers_rejected(self, toy_bundle_one_test):
        with pytest.raises(ValueError):
            run_toy_official_format_harness(
                toy_bundle_one_test,
                {
                    "candidate_outputs": [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
                    "expected_output": [[2, 2], [2, 2]],
                },
            )

    def test_aggregate_toy_percentage_calculated_correctly(self, toy_bundle_two_tests):
        result = run_toy_official_format_harness(
            toy_bundle_two_tests,
            {
                "toy_harness_002": [
                    [[[2, 2], [2, 2]], [[0, 0], [0, 0]]],
                    [[[0, 0], [0, 0]], [[1, 1], [1, 1]]],
                ]
            },
        )
        assert result["aggregate_toy_percentage"] == 50.0
        assert result["score_result"]["aggregate_toy_percentage"] == 50.0
        assert result["per_task_scoring_metadata"][0]["solved"] is True
        assert result["per_task_scoring_metadata"][1]["solved"] is False

    def test_toy_only_and_not_official_score_markers_present(self, toy_bundle_one_test):
        result = run_toy_official_format_harness(
            toy_bundle_one_test,
            lambda visible_bundle: [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert result["toy_only"] is True
        assert result["not_official_score"] is True
        assert result["emitted_submission"]["toy_only"] is True
        assert result["emitted_submission"]["not_official_submission"] is True

    def test_official_data_class_rejected_in_toy_harness_phase(self):
        with pytest.raises(ValueError):
            validate_toy_end_to_end_harness_boundary_record(
                {
                    "data_class": "public_official_arc",
                    "run_phase": "phase_1_toy_fixture_adapter",
                    "official_data_touched": True,
                    "hidden_private_data_touched": False,
                    "dataset_provenance": {"source": "public-arc", "version": "v1", "checksum": "abc123"},
                    "internet_tool_model_calls_during_solving": False,
                    "expected_output_leakage": False,
                    "internal_task_language_leakage": False,
                    "synthetic_official_score_mixing": False,
                }
            )

    def test_hidden_private_data_rejected(self):
        with pytest.raises(ValueError):
            validate_toy_end_to_end_harness_boundary_record(
                {
                    "data_class": "hidden_private_arc",
                    "run_phase": "phase_1_toy_fixture_adapter",
                    "official_data_touched": False,
                    "hidden_private_data_touched": True,
                    "internet_tool_model_calls_during_solving": False,
                    "expected_output_leakage": False,
                    "internal_task_language_leakage": False,
                    "synthetic_official_score_mixing": False,
                }
            )

    def test_official_percentage_claimable_remains_none_zero(self, toy_bundle_one_test):
        result = run_toy_official_format_harness(
            toy_bundle_one_test,
            lambda visible_bundle: [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert result["official_percentage_claimable_text"] == "none yet"
        assert result["official_percentage_claimable_value"] == 0
        assert summarize_boundary_status(result["contamination_boundary"])["official_percentage_claimable_value"] == 0

    def test_no_official_arc_claim_can_be_produced_from_toy_harness_output(self, toy_bundle_one_test):
        result = run_toy_official_format_harness(
            toy_bundle_one_test,
            lambda visible_bundle: [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        with pytest.raises(ValueError):
            validate_toy_score_claim(
                {
                    "claim_kind": "official_arc_performance",
                    "official_arc_performance": True,
                    "aggregate_toy_percentage": result["aggregate_toy_percentage"],
                }
            )
