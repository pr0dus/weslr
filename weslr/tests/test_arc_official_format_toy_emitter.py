"""Tests for the ARC official-format toy two-output emitter."""

from __future__ import annotations

import json

import pytest

from weslr.arc_official_contamination_boundary import summarize_boundary_status
from weslr.arc_official_format_toy_emitter import (
    emit_toy_official_format_submission,
    validate_toy_official_format_submission,
    validate_toy_emitter_boundary_record,
    validate_toy_score_claim,
)
from weslr.arc_official_format_toy_scorer import score_toy_official_format_bundle


@pytest.fixture()
def toy_bundle():
    return {
        "task_id": "toy_emit_001",
        "train": [
            {
                "input": [[1, 1], [0, 0]],
                "output": [[1, 1], [1, 1]],
            }
        ],
        "test": [
            {
                "test_id": "toy_emit_test_1",
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


class TestArcOfficialFormatToyEmitter:
    def test_exactly_two_candidates_accepted(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert submission["toy_only"] is True
        assert submission["not_official_submission"] is True
        assert submission["task_id"] == "toy_emit_001"
        assert submission["tests"][0]["candidate_count"] == 2
        assert submission["tests"][0]["test_id"] == "toy_emit_test_1"
        assert submission["tests"][0]["candidate_outputs"][0] == [[2, 2], [2, 2]]
        assert submission["tests"][0]["candidate_outputs"][1] == [[0, 0], [0, 0]]

    def test_one_candidate_rejected(self, toy_bundle):
        with pytest.raises(ValueError):
            emit_toy_official_format_submission(toy_bundle, [[[[2, 2], [2, 2]]]])

    def test_three_candidates_rejected(self, toy_bundle):
        with pytest.raises(ValueError):
            emit_toy_official_format_submission(
                toy_bundle,
                [[[[2, 2], [2, 2]], [[0, 0], [0, 0]], [[1, 1], [1, 1]]]],
            )

    @pytest.mark.parametrize(
        "candidate_outputs",
        [
            [[[[1, 1], [1]]]],
            [[[[1, 1], [1, 1]], [[0, 0], [0, "x"]]]],
        ],
    )
    def test_malformed_grid_rejected(self, toy_bundle, candidate_outputs):
        with pytest.raises(ValueError):
            emit_toy_official_format_submission(toy_bundle, candidate_outputs)

    def test_expected_output_leakage_rejected(self, toy_bundle):
        malicious = {
            "task_id": "toy_emit_001",
            "toy_only": True,
            "not_official_submission": True,
            "tests": [
                {
                    "test_id": "toy_emit_test_1",
                    "candidate_outputs": [[[2, 2], [2, 2]], [[0, 0], [0, 0]]],
                    "expected_output": [[2, 2], [2, 2]],
                }
            ],
            "candidate_outputs": [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        }
        with pytest.raises(ValueError):
            validate_toy_official_format_submission(malicious)

    def test_task_and_test_ids_are_preserved(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert submission["task"]["task_id"] == "toy_emit_001"
        assert submission["tests"][0]["test_id"] == "toy_emit_test_1"

    def test_toy_only_and_not_official_submission_markers_present(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert submission["toy_only"] is True
        assert submission["not_official_submission"] is True

    def test_output_can_be_scored_by_toy_scorer_candidate_1(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        score = score_toy_official_format_bundle(toy_bundle, submission["candidate_outputs"])
        assert score["task_solved"] is True
        assert score["per_test_scoring_metadata"][0]["candidate_1_matches"] is True
        assert score["per_test_scoring_metadata"][0]["winning_candidate_index"] == 0

    def test_output_can_be_scored_by_toy_scorer_candidate_2(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[0, 0], [0, 0]], [[2, 2], [2, 2]]]],
        )
        score = score_toy_official_format_bundle(toy_bundle, submission["candidate_outputs"])
        assert score["task_solved"] is True
        assert score["per_test_scoring_metadata"][0]["candidate_2_matches"] is True
        assert score["per_test_scoring_metadata"][0]["winning_candidate_index"] == 1

    def test_official_data_class_rejected_in_toy_emitter_phase(self):
        with pytest.raises(ValueError):
            validate_toy_emitter_boundary_record(
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
            validate_toy_emitter_boundary_record(
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

    def test_official_percentage_claimable_remains_none_zero(self, toy_bundle):
        submission = emit_toy_official_format_submission(
            toy_bundle,
            [[[[2, 2], [2, 2]], [[0, 0], [0, 0]]]],
        )
        assert submission["official_percentage_claimable_text"] == "none yet"
        assert submission["official_percentage_claimable_value"] == 0
        assert summarize_boundary_status(submission["contamination_boundary"])["official_percentage_claimable_value"] == 0

    def test_synthetic_as_official_claim_rejected(self):
        with pytest.raises(ValueError):
            validate_toy_score_claim(
                {
                    "claim_kind": "official_arc_performance",
                    "official_arc_performance": True,
                }
            )
