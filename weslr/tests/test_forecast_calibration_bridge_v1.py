from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.cognitive_research_protocol import build_cognitive_research_run_v1, build_default_cognitive_research_denied_authority_v1
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    build_forecast_calibration_record_v1,
    build_initial_forecast_calibration_examples_v1,
    summarize_forecast_calibration_record_v1,
    to_forecast_calibration_json_safe_v1,
    validate_forecast_calibration_record_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "forecast_calibration_bridge.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


def _research_run(engine_name: str, engine_family: str, **overrides):
    payload = {
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": "calibration_replay" if engine_name in {"forecast_error_ledger", "calibration_ledger"} else "internal_exploration",
        "input_artifact_ref": f"artifact:{engine_name}-001",
        "input_summary": f"Metadata-only source run for {engine_name}.",
        "predictions": ["A later probe will match the observed boundary."],
        "hypotheses": ["A narrow hidden rule governs the signal shift."],
        "probes": ["compare predicted and observed boundary signals"],
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "candidate_generator_only" if engine_name != "unintelligible_output_analyzer" else "translation_helper_only",
    }
    payload.update(overrides)
    return build_cognitive_research_run_v1(payload)


def _record(**overrides):
    base_run = _research_run("forecast_error_ledger", "calibration_and_forecast")
    payload = {
        "source_run": base_run,
        "record_id": "calibration-test-001",
        "prediction_id": "prediction-test-001",
        "prediction_statement": "A later probe will match the observed boundary.",
        "prediction_type": "probe_prediction",
        "prediction_scope": "metadata_only",
        "confidence_before": 0.61,
        "confidence_after": 0.61,
        "confidence_basis": "source run predictions and probes",
        "uncertainty_factors": ["probe timing uncertain"],
        "invalidation_signals": ["no observation yet"],
        "expected_outcome": "probe result to be observed",
        "observed_outcome": "",
        "outcome_status": "not_observed_yet",
        "calibration_result": "not_yet_calibrated",
        "error_type": "none",
        "safe_metadata": {
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
            "no_runtime_wiring": True,
            "no_provider_calls": True,
            "no_tool_execution": True,
            "no_persistence": True,
            "no_memory_mutation": True,
            "no_project_mutation": True,
            "no_public_claims": True,
            "no_final_answer": True,
        },
    }
    payload.update(overrides)
    return build_forecast_calibration_record_v1(payload)


class TestForecastCalibrationBridgeV1:
    def test_01_module_imports_safely(self):
        import weslr.forecast_calibration_bridge as mod

        assert mod.HELPER_TYPE_V1 == "weslr_forecast_calibration_bridge_v1"
        assert "weslr.chat_responder" not in __import__("sys").modules
        assert "weslr.main" not in __import__("sys").modules
        assert "dialogue" not in __import__("sys").modules
        assert "chat_ui" not in __import__("sys").modules

    def test_02_default_record_contains_required_fields(self):
        record = _record()
        required = {
            "schema_version",
            "record_id",
            "source_run_id",
            "source_engine_name",
            "source_engine_family",
            "prediction_id",
            "prediction_statement",
            "prediction_type",
            "prediction_scope",
            "confidence_before",
            "confidence_basis",
            "uncertainty_factors",
            "invalidation_signals",
            "expected_outcome",
            "observed_outcome",
            "outcome_status",
            "calibration_result",
            "error_type",
            "assumptions_used",
            "assumptions_failed",
            "missing_signals",
            "conflicting_signals",
            "correction",
            "compressed_lesson",
            "confidence_after",
            "future_adjustment",
            "behavior_change_authorized",
            "memory_mutation_authorized",
            "project_mutation_authorized",
            "public_claim_authorized",
            "denied_authority",
            "safe_metadata",
        }
        assert required.issubset(record.keys())

    def test_03_valid_not_yet_observed_record_passes(self):
        record = _record()
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_04_valid_matched_record_passes(self):
        record = _record(
            record_id="calibration-matched-001",
            prediction_id="prediction-matched-001",
            observed_outcome="boundary matched the prediction",
            outcome_status="matched",
            calibration_result="well_calibrated",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_05_valid_failed_record_passes(self):
        record = _record(
            record_id="calibration-failed-001",
            prediction_id="prediction-failed-001",
            confidence_before=0.83,
            confidence_after=0.44,
            observed_outcome="boundary contradicted the prediction",
            outcome_status="failed",
            calibration_result="wrong_model",
            error_type="wrong_assumption",
            correction="The boundary hypothesis was too narrow.",
            compressed_lesson="Widen the boundary model next time.",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_06_valid_partially_matched_record_passes(self):
        record = _record(
            record_id="calibration-partial-001",
            prediction_id="prediction-partial-001",
            prediction_statement="The probe will narrow the boundary but not fully settle it.",
            prediction_type="gap_prediction",
            observed_outcome="partial narrowing observed",
            outcome_status="partially_matched",
            calibration_result="ambiguous",
            error_type="scope_mismatch",
            correction="Only part of the gap was resolved.",
            compressed_lesson="Separate narrowing from closure.",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_07_valid_inconclusive_record_passes(self):
        record = _record(
            record_id="calibration-inconclusive-001",
            prediction_id="prediction-inconclusive-001",
            observed_outcome="no decisive outcome",
            outcome_status="inconclusive",
            calibration_result="ambiguous",
            error_type="none",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_08_valid_overconfident_correction_passes(self):
        record = _record(
            record_id="calibration-overconfident-001",
            prediction_id="prediction-overconfident-001",
            confidence_before=0.92,
            confidence_after=0.64,
            observed_outcome="precision was lower than expected",
            outcome_status="failed",
            calibration_result="overconfident",
            error_type="ignored_uncertainty",
            correction="Initial confidence overreached the evidence.",
            compressed_lesson="Treat thin evidence as tentative.",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_09_valid_underconfident_correction_passes(self):
        record = _record(
            record_id="calibration-underconfident-001",
            prediction_id="prediction-underconfident-001",
            confidence_before=0.22,
            confidence_after=0.56,
            observed_outcome="stronger-than-expected confirmation",
            outcome_status="matched",
            calibration_result="underconfident",
            error_type="missing_context",
            correction="The evidence supported a stronger reading.",
            compressed_lesson="Raise confidence when repeated probes converge.",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_10_valid_missing_signal_correction_passes(self):
        record = _record(
            record_id="calibration-missing-signal-001",
            prediction_id="prediction-missing-signal-001",
            observed_outcome="missing signal prevented full confirmation",
            outcome_status="blocked",
            calibration_result="missing_signal",
            error_type="missing_context",
            missing_signals=["signal window"],
            correction="Do not treat incomplete signal sets as complete.",
            compressed_lesson="Require the missing signal before closing the loop.",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_11_translation_prediction_from_uoa_passes(self):
        record = _record(
            source_run=_research_run("unintelligible_output_analyzer", "reasoning_integrity", predictions=["The translation layer will remain partially bounded."]),
            source_engine_name="unintelligible_output_analyzer",
            source_engine_family="reasoning_integrity",
            record_id="calibration-uoa-001",
            prediction_id="prediction-uoa-001",
            prediction_statement="The translation layer will remain partially bounded.",
            prediction_type="translation_prediction",
            observed_outcome="translation stayed partially bounded",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="translation_overreach",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_12_motif_probe_prediction_from_rsc_passes(self):
        record = _record(
            source_run=_research_run("raw_signal_cartographer", "raw_signal_analysis", predictions=["Repeated motif cluster will remain stable across probes."], probes=["probe the repeated motif cluster"]),
            source_engine_name="raw_signal_cartographer",
            source_engine_family="raw_signal_analysis",
            record_id="calibration-rsc-001",
            prediction_id="prediction-rsc-001",
            prediction_statement="Repeated motif cluster will remain stable across probes.",
            prediction_type="motif_prediction",
            observed_outcome="stability confirmed within metadata bounds",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="none",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_13_packet_from_cognitive_research_run_example_passes(self):
        example_run = protocol.build_initial_cognitive_research_examples_v1()[0]
        packet = build_forecast_calibration_packet_from_research_run_v1(example_run)
        assert validate_forecast_calibration_record_v1(packet)["valid"] is True
        assert packet["source_run_id"]

    def test_14_json_safe_copy_strips_unsafe_raw_fields(self):
        unsafe = deepcopy(_record())
        unsafe["raw_private_text"] = "super secret raw artifact"
        unsafe["hidden_prompt"] = "system prompt leakage"
        safe = to_forecast_calibration_json_safe_v1(unsafe)
        assert "raw_private_text" not in safe
        assert "hidden_prompt" not in safe
        json.dumps(safe, sort_keys=True)

    def test_15_summary_is_concise_and_private_text_safe(self):
        summary = summarize_forecast_calibration_record_v1(_record())
        assert len(summary["summary_text"]) <= 320
        assert "secret" not in summary["summary_text"].lower()
        assert "hidden prompt" not in summary["summary_text"].lower()

    def test_16_forecast_error_ledger_source_run_passes(self):
        record = _record(
            source_run=_research_run("forecast_error_ledger", "calibration_and_forecast"),
            source_engine_name="forecast_error_ledger",
            source_engine_family="calibration_and_forecast",
            record_id="calibration-fed-001",
            prediction_id="prediction-fed-001",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    def test_17_calibration_ledger_source_run_passes(self):
        record = _record(
            source_run=_research_run("calibration_ledger", "calibration_and_forecast"),
            source_engine_name="calibration_ledger",
            source_engine_family="calibration_and_forecast",
            record_id="calibration-ledger-001",
            prediction_id="prediction-ledger-001",
        )
        assert validate_forecast_calibration_record_v1(record)["valid"] is True

    @pytest.mark.parametrize(
        "mutation,expected",
        [
            ({"source_run_id": ""}, "missing_source_run_id"),
            ({"prediction_statement": ""}, "missing_prediction_statement"),
            ({"confidence_before": 1.4}, "unsafe_confidence_before"),
            ({"confidence_before": -0.1}, "unsafe_confidence_before"),
        ],
    )
    def test_18_missing_or_unsafe_core_fields_fail(self, mutation, expected):
        record = _record()
        record.update(mutation)
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert expected in validation["violations"]

    def test_19_matched_without_observed_outcome_fails(self):
        record = _record(outcome_status="matched", observed_outcome="", calibration_result="well_calibrated")
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert "missing_observed_outcome" in validation["violations"]

    def test_20_calibration_result_before_observation_fails(self):
        record = _record()
        record["outcome_status"] = "not_observed_yet"
        record["calibration_result"] = "well_calibrated"
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert "calibration_result_before_observation" in validation["violations"]

    def test_21_confidence_after_change_without_correction_fails(self):
        record = _record(confidence_after=0.41, correction="", compressed_lesson="")
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert "confidence_after_changed_without_correction" in validation["violations"]

    @pytest.mark.parametrize(
        "authority_key",
        [
            "behavior_change_authorized",
            "memory_mutation_authorized",
            "project_mutation_authorized",
            "public_claim_authorized",
        ],
    )
    def test_22_authority_flags_fail_closed(self, authority_key):
        record = _record(**{authority_key: True})
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert any(authority_key in violation for violation in validation["violations"])

    @pytest.mark.parametrize(
        "payload",
        [
            {"prediction_statement": ".weslr private artifact reference and internal details"},
            {"prediction_statement": "live ingestion from github rss lab notebook and network feed"},
            {"safe_metadata": {"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True, "notes": "breakthrough proof solved"}},
        ],
    )
    def test_23_runtime_provider_tool_persistence_or_public_implications_fail(self, payload):
        record = _record(**payload)
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert any("forbidden" in violation or "public" in violation for violation in validation["violations"])

    @pytest.mark.parametrize(
        "payload",
        [
            {"prediction_statement": "raw private text hidden system prompt"},
            {"prediction_statement": "private mechanism text with raw private data"},
        ],
    )
    def test_24_raw_private_or_hidden_prompt_text_fails(self, payload):
        record = _record(**payload)
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert any("forbidden_text_marker" in violation for violation in validation["violations"])

    @pytest.mark.parametrize(
        "payload",
        [
            {"prediction_statement": "breakthrough proof solution certified public-ready"},
            {"prediction_statement": "official certification solved breakthrough"},
        ],
    )
    def test_25_public_breakthrough_claim_fails(self, payload):
        record = _record(**payload)
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert any("forbidden_text_marker" in violation for violation in validation["violations"])

    def test_26_behavior_pack_promotion_implication_fails(self):
        record = _record(correction="promote this behavior pack immediately")
        validation = validate_forecast_calibration_record_v1(record)
        assert validation["valid"] is False
        assert "behavior_pack_promotion_implication" in validation["violations"]
