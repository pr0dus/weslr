"""Tests for the ARC official-data contamination boundary checker."""

from __future__ import annotations

import pytest

from weslr.arc_official_contamination_boundary import (
    DATA_CLASSES_V1,
    RUN_PHASES_V1,
    classify_data_class,
    classify_run_phase,
    summarize_boundary_status,
    validate_contamination_boundary_record,
    validate_logging_policy,
    validate_official_data_provenance,
    validate_result_claim,
)


@pytest.fixture()
def synthetic_record():
    return {
        "data_class": "synthetic_weslr",
        "run_phase": "phase_0_synthetic_only",
        "official_data_touched": False,
        "hidden_private_data_touched": False,
        "internet_tool_model_calls_during_solving": False,
        "expected_output_leakage": False,
        "internal_task_language_leakage": False,
        "synthetic_official_score_mixing": False,
        "toy_fixture": False,
        "claim": {
            "claim_kind": "synthetic_score",
            "evidence_kind": "synthetic",
            "synthetic_score": "130/130",
            "official_run_proof": False,
            "local_public_run_proof": False,
            "official_arc_performance": False,
        },
        "log": {
            "task_id": "ARC_T3_diagnostic",
            "status": "solved",
            "timing_ms": 12,
            "score_metadata": {"score": 1.0},
        },
    }


class TestOfficialDataContaminationBoundary:
    def test_data_classes_and_run_phases_are_modeled(self):
        assert DATA_CLASSES_V1 == (
            "synthetic_weslr",
            "public_official_arc",
            "hidden_private_arc",
            "user_provided_example",
            "generated_hard_mode",
            "report_log_metadata",
        )
        assert RUN_PHASES_V1 == (
            "phase_0_synthetic_only",
            "phase_1_toy_fixture_adapter",
            "phase_2_public_parse_scorer_validation",
            "phase_3_local_public_run",
            "phase_4_post_run_audit",
            "phase_5_competition_participation_design",
        )

    def test_synthetic_only_record_passes(self, synthetic_record):
        validated = validate_contamination_boundary_record(synthetic_record)
        assert validated["valid"] is True
        assert classify_data_class(synthetic_record) == "synthetic_weslr"
        assert classify_run_phase(synthetic_record) == "phase_0_synthetic_only"
        assert summarize_boundary_status(synthetic_record)["official_percentage_claimable_text"] == "none yet"
        assert summarize_boundary_status(synthetic_record)["official_percentage_claimable_value"] == 0

    def test_toy_fixture_adapter_phase_passes(self):
        record = {
            "data_class": "synthetic_weslr",
            "run_phase": "phase_1_toy_fixture_adapter",
            "toy_fixture": True,
            "official_data_touched": False,
            "hidden_private_data_touched": False,
            "internet_tool_model_calls_during_solving": False,
            "expected_output_leakage": False,
            "internal_task_language_leakage": False,
            "synthetic_official_score_mixing": False,
        }
        validated = validate_contamination_boundary_record(record)
        assert validated["run_phase"] == "phase_1_toy_fixture_adapter"

    @pytest.mark.parametrize(
        "field, value",
        [
            ("data_class", "hidden_private_arc"),
            ("hidden_private_data_touched", True),
        ],
    )
    def test_hidden_private_arc_is_always_rejected(self, synthetic_record, field, value):
        record = dict(synthetic_record)
        record[field] = value
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    @pytest.mark.parametrize("phase", ["phase_0_synthetic_only", "phase_1_toy_fixture_adapter"])
    def test_official_data_before_approved_phase_is_rejected(self, synthetic_record, phase):
        record = dict(synthetic_record)
        record.update(
            {
                "data_class": "public_official_arc",
                "run_phase": phase,
                "official_data_touched": True,
                "dataset_provenance": {"source": "public-arc", "version": "v1", "checksum": "abc123"},
            }
        )
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    @pytest.mark.parametrize("phase", ["phase_2_public_parse_scorer_validation", "phase_3_local_public_run"])
    def test_official_future_phase_requires_provenance_and_passes(self, synthetic_record, phase):
        record = dict(synthetic_record)
        record.update(
            {
                "data_class": "public_official_arc",
                "run_phase": phase,
                "official_data_touched": True,
                "dataset_provenance": {"source": "public-arc", "version": "v1", "checksum": "abc123"},
                "official_run_proof": phase == "phase_3_local_public_run",
                "local_public_run_proof": phase == "phase_3_local_public_run",
            }
        )
        validated = validate_contamination_boundary_record(record)
        assert validated["official_data_touched"] is True
        assert validated["official_data_provenance"]["has_checksum"] is True

    def test_missing_provenance_or_checksum_is_rejected_for_official_data(self, synthetic_record):
        for provenance in [
            {},
            {"source": "public-arc", "version": "v1"},
            {"source": "public-arc", "checksum": "abc123"},
            {"version": "v1", "checksum": "abc123"},
        ]:
            record = dict(synthetic_record)
            record.update(
                {
                    "data_class": "public_official_arc",
                    "run_phase": "phase_2_public_parse_scorer_validation",
                    "official_data_touched": True,
                    "dataset_provenance": provenance,
                }
            )
            with pytest.raises(ValueError):
                validate_contamination_boundary_record(record)

    def test_synthetic_scores_cannot_be_claimed_as_official_performance(self):
        claim = {
            "claim_kind": "official_arc_performance",
            "evidence_kind": "synthetic",
            "synthetic_score": "130/130",
            "official_run_proof": False,
            "local_public_run_proof": False,
            "official_arc_performance": True,
        }
        with pytest.raises(ValueError):
            validate_result_claim(claim)

    def test_local_public_percentage_cannot_be_claimed_without_official_run(self):
        claim = {
            "claim_kind": "official_local_percentage",
            "evidence_kind": "official",
            "official_percentage": 42,
            "official_run_proof": False,
            "local_public_run_proof": False,
        }
        with pytest.raises(ValueError):
            validate_result_claim(claim)

    def test_expected_output_and_internal_task_language_leaks_are_rejected(self):
        record = {
            "data_class": "report_log_metadata",
            "run_phase": "phase_4_post_run_audit",
            "official_data_touched": True,
            "hidden_private_data_touched": False,
            "dataset_provenance": {"source": "public-arc", "version": "v1", "checksum": "abc123"},
            "expected_output_leakage": True,
            "internal_task_language_leakage": True,
        }
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    def test_internet_tool_model_calls_during_solving_are_rejected(self):
        record = {
            "data_class": "synthetic_weslr",
            "run_phase": "phase_0_synthetic_only",
            "internet_tool_model_calls_during_solving": True,
            "official_data_touched": False,
            "hidden_private_data_touched": False,
            "expected_output_leakage": False,
            "internal_task_language_leakage": False,
            "synthetic_official_score_mixing": False,
        }
        with pytest.raises(ValueError):
            validate_contamination_boundary_record(record)

    def test_logging_policy_rejects_answers_and_internal_language(self):
        bad_log = {
            "task_id": "ARC_T3_diagnostic",
            "status": "solved",
            "timing_ms": 12,
            "expected_output": [1, 2, 3],
        }
        with pytest.raises(ValueError):
            validate_logging_policy(bad_log)

        also_bad_log = {
            "task_id": "ARC_T3_diagnostic",
            "status": "solved",
            "timing_ms": 12,
            "internal_task_language": {"latent_rule": "hidden"},
        }
        with pytest.raises(ValueError):
            validate_logging_policy(also_bad_log)

    def test_summary_reports_none_yet_without_official_run_proof(self, synthetic_record):
        summary = summarize_boundary_status(synthetic_record)
        assert summary["official_percentage_claimable_text"] == "none yet"
        assert summary["official_percentage_claimable_value"] == 0
        assert summary["official_run_proof_present"] is False

    def test_solver_changes_after_official_run_must_be_labelled(self):
        claim = {
            "claim_kind": "official_local_percentage",
            "evidence_kind": "official",
            "official_percentage": 12,
            "official_run_proof": True,
            "local_public_run_proof": True,
            "solver_changed_after_official_run": True,
            "iteration_labelled": False,
        }
        with pytest.raises(ValueError):
            validate_result_claim(claim)
