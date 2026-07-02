"""Tests for the ARC official-format toy local scorer."""

from __future__ import annotations

import json

import pytest

from weslr.arc_official_contamination_boundary import summarize_boundary_status
from weslr.arc_official_format_toy_adapter import export_solver_visible_toy_bundle
from weslr.arc_official_format_toy_scorer import (
    aggregate_toy_official_format_scores,
    score_toy_official_format_bundle,
    validate_toy_score_claim,
    validate_toy_scorer_boundary_record,
)


@pytest.fixture()
def solved_toy_bundle():
    return {
        "task_id": "toy_score_001",
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


@pytest.fixture()
def two_task_runs():
    solved = {
        "bundle": {
            "task_id": "toy_score_002",
            "train": [
                {
                    "input": [[1, 0], [1, 0]],
                    "output": [[1, 1], [1, 1]],
                }
            ],
            "test": [
                {
                    "input": [[3, 3], [0, 0]],
                    "expected_output": [[3, 3], [3, 3]],
                    "candidate_output_slots": [None, None],
                }
            ],
            "bundle_provenance": {
                "source": "toy-fixture-bundle",
                "version": "toy-v1",
                "checksum": "toy-checksum-002",
            },
        },
        "candidate_outputs": [
            [[[3, 3], [3, 3]], [[0, 0], [0, 0]]],
        ],
    }
    failed = {
        "bundle": {
            "task_id": "toy_score_003",
            "train": [
                {
                    "input": [[1, 0], [1, 0]],
                    "output": [[1, 1], [1, 1]],
                }
            ],
            "test": [
                {
                    "input": [[4, 4], [0, 0]],
                    "expected_output": [[4, 4], [4, 4]],
                    "candidate_output_slots": [None, None],
                }
            ],
            "bundle_provenance": {
                "source": "toy-fixture-bundle",
                "version": "toy-v1",
                "checksum": "toy-checksum-003",
            },
        },
        "candidate_outputs": [
            [[[0, 0], [0, 0]], [[1, 1], [1, 1]]],
        ],
    }
    return [solved, failed]


class TestArcOfficialFormatToyLocalScorer:
    def test_candidate_1_exact_match_solves(self, solved_toy_bundle):
        score = score_toy_official_format_bundle(
            solved_toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert score["task_solved"] is True
        assert score["per_test_scoring_metadata"][0]["winning_candidate_index"] == 0
        assert score["per_test_scoring_metadata"][0]["candidate_1_matches"] is True
        assert score["toy_only"] is True
        assert score["not_official_score"] is True
        assert score["contamination_boundary"]["run_phase"] == "phase_1_toy_fixture_adapter"

    def test_candidate_2_exact_match_solves(self, solved_toy_bundle):
        score = score_toy_official_format_bundle(
            solved_toy_bundle,
            [[[[0, 0], [0, 0]], [[2, 2], [2, 2]]]],
        )
        assert score["task_solved"] is True
        assert score["per_test_scoring_metadata"][0]["winning_candidate_index"] == 1
        assert score["per_test_scoring_metadata"][0]["candidate_2_matches"] is True

    def test_neither_candidate_match_fails(self, solved_toy_bundle):
        score = score_toy_official_format_bundle(
            solved_toy_bundle,
            [[[[0, 0], [0, 0]], [[1, 1], [1, 1]]]],
        )
        assert score["task_solved"] is False
        assert score["per_test_scoring_metadata"][0]["winning_candidate_index"] is None
        assert score["per_test_scoring_metadata"][0]["solved"] is False

    @pytest.mark.parametrize(
        "candidate_outputs",
        [
            [[[[1, 1], [1]]]],
            [[[[1, 1], [1, 1]], [[0, 0], [0, "x"]]]],
        ],
    )
    def test_malformed_candidate_is_rejected(self, solved_toy_bundle, candidate_outputs):
        with pytest.raises(ValueError):
            score_toy_official_format_bundle(solved_toy_bundle, candidate_outputs)

    def test_one_candidate_is_rejected(self, solved_toy_bundle):
        with pytest.raises(ValueError):
            score_toy_official_format_bundle(solved_toy_bundle, [[[[2, 2], [2, 2]]]])

    def test_three_candidates_are_rejected(self, solved_toy_bundle):
        with pytest.raises(ValueError):
            score_toy_official_format_bundle(
                solved_toy_bundle,
                [[[[2, 2], [2, 2]], [[0, 0], [0, 0]], [[1, 1], [1, 1]]]],
            )

    def test_expected_output_never_appears_in_solver_visible_bundle(self, solved_toy_bundle):
        visible = export_solver_visible_toy_bundle(solved_toy_bundle)
        assert "expected_output" not in json.dumps(visible, sort_keys=True)
        assert visible["test"][0]["candidate_output_slots"] == [None, None]

    def test_toy_score_cannot_be_claimed_as_official_arc_performance(self):
        with pytest.raises(ValueError):
            validate_toy_score_claim(
                {
                    "claim_kind": "official_arc_performance",
                    "official_arc_performance": True,
                    "toy_score_percentage": 100.0,
                }
            )

    def test_official_data_class_rejected_in_toy_scorer_phase(self):
        with pytest.raises(ValueError):
            validate_toy_scorer_boundary_record(
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
            validate_toy_scorer_boundary_record(
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

    def test_aggregate_toy_percentage_calculated_correctly(self, two_task_runs):
        aggregate = aggregate_toy_official_format_scores(two_task_runs)
        assert aggregate["aggregate_test_inputs"] == 2
        assert aggregate["aggregate_solved_test_inputs"] == 1
        assert aggregate["aggregate_failed_test_inputs"] == 1
        assert aggregate["aggregate_toy_percentage"] == 50.0
        assert aggregate["toy_only"] is True
        assert aggregate["not_official_score"] is True
        assert aggregate["official_percentage_claimable_text"] == "none yet"
        assert aggregate["official_percentage_claimable_value"] == 0

    def test_official_percentage_claimable_remains_none_zero(self, solved_toy_bundle):
        score = score_toy_official_format_bundle(
            solved_toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert score["official_percentage_claimable_text"] == "none yet"
        assert score["official_percentage_claimable_value"] == 0
        assert summarize_boundary_status(score["contamination_boundary"])["official_percentage_claimable_value"] == 0

    def test_boundary_summary_marks_toy_only_not_official(self, solved_toy_bundle):
        score = score_toy_official_format_bundle(
            solved_toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert score["boundary_summary"]["official_percentage_claimable_text"] == "none yet"
        assert score["boundary_summary"]["official_percentage_claimable_value"] == 0
