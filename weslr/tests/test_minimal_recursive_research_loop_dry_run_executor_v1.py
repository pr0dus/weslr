from __future__ import annotations

from copy import deepcopy

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.dialectic_generator_loop import validate_dialectic_loop_packet_v1
from weslr.forecast_calibration_bridge import validate_forecast_calibration_record_v1
from weslr.minimal_recursive_research_loop_dry_run_executor import (
    ALLOWED_NEXT_INTERNAL_STEPS_V1,
    build_initial_minimal_recursive_loop_examples_v1,
    build_minimal_loop_input_signal_v1,
    run_minimal_recursive_research_loop_dry_run_v1,
    summarize_minimal_recursive_research_loop_result_v1,
    to_minimal_recursive_research_loop_json_safe_v1,
    validate_minimal_recursive_research_loop_result_v1,
)
from weslr.nonlinear_inspiration_resonance_engine import validate_nonlinear_inspiration_packet_v1
from weslr.perspicuity_scorer import validate_perspicuity_packet_v1
from weslr.raw_signal_cartographer import validate_raw_signal_cartography_packet_v1
from weslr.rule_pressure_engine import validate_rule_pressure_packet_v1
from weslr.suggestion_store_update_packet import validate_suggestion_store_update_packet_v1
from weslr.unintelligible_output_analyzer import validate_unintelligible_output_analysis_packet_v1
from weslr.unknown_engine_adapter import validate_unknown_engine_research_run_v1


STAGE_FIELDS = (
    "raw_signal_cartography",
    "unintelligible_output_analysis",
    "unknown_engine_run",
    "nonlinear_inspiration_run",
    "rule_pressure_run",
    "dialectic_generator_run",
    "perspicuity_score_run",
    "suggestion_store_update_packet",
    "calibration_bridge_record",
)

AUTH_FIELDS = (
    "runtime_action_authorized",
    "storage_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_promotion_authorized",
    "public_claim_authorized",
)


def _result(**overrides):
    signal = build_minimal_loop_input_signal_v1(
        {
            "signal_id": "signal:minimal-loop:test",
            "signal_summary": "Synthetic metadata-only signal with repeated boundary markers and a compact update proposal.",
        }
    )
    payload = {"input_signal": signal}
    payload.update(overrides)
    return run_minimal_recursive_research_loop_dry_run_v1(payload)


def test_minimal_recursive_loop_completes_and_validates_each_stage():
    result = _result()
    validation = validate_minimal_recursive_research_loop_result_v1(result)

    assert validation["valid"] is True
    assert result["recommended_next_internal_step"] in ALLOWED_NEXT_INTERNAL_STEPS_V1
    assert result["blocked_actions"] == []
    assert result["operator_review_required"] is True
    assert result["runtime_action_authorized"] is False
    assert result["storage_write_authorized"] is False
    assert result["memory_mutation_authorized"] is False
    assert result["project_mutation_authorized"] is False
    assert result["behavior_promotion_authorized"] is False
    assert result["public_claim_authorized"] is False

    assert validate_raw_signal_cartography_packet_v1(result["raw_signal_cartography"])["valid"] is True
    assert validate_unintelligible_output_analysis_packet_v1(result["unintelligible_output_analysis"])["valid"] is True
    assert validate_unknown_engine_research_run_v1(result["unknown_engine_run"])["valid"] is True
    assert validate_nonlinear_inspiration_packet_v1(result["nonlinear_inspiration_run"])["valid"] is True
    assert validate_rule_pressure_packet_v1(result["rule_pressure_run"])["valid"] is True
    assert validate_dialectic_loop_packet_v1(result["dialectic_generator_run"])["blocked"] is False
    assert validate_perspicuity_packet_v1(result["perspicuity_score_run"])["blocked"] is False
    assert validate_suggestion_store_update_packet_v1(result["suggestion_store_update_packet"])["blocked"] is False
    assert validate_forecast_calibration_record_v1(result["calibration_bridge_record"])["valid"] is True

    assert result["suggestion_store_update_packet"]["update_actions"][0]["action_type"] == "recommend_next_internal_step"
    assert result["calibration_bridge_record"]["calibration_result"] == "not_yet_calibrated"
    assert "private" not in result["final_loop_summary"].lower()
    assert len(result["final_loop_summary"]) <= 220
    assert summarize_minimal_recursive_research_loop_result_v1(result) == result["final_loop_summary"]


def test_examples_include_a_complete_synthetic_loop():
    examples = build_initial_minimal_recursive_loop_examples_v1()
    assert len(examples) >= 1
    assert any(validate_minimal_recursive_research_loop_result_v1(example)["valid"] for example in examples)


@pytest.mark.parametrize("field", STAGE_FIELDS)
def test_missing_stage_fields_fail_closed(field):
    result = _result()
    result.pop(field)
    validation = validate_minimal_recursive_research_loop_result_v1(result)
    assert validation["valid"] is False
    assert any(field in label for label in validation["blocked_labels"])


@pytest.mark.parametrize("field", AUTH_FIELDS)
def test_authority_flags_fail_closed(field):
    result = _result()
    result[field] = True
    validation = validate_minimal_recursive_research_loop_result_v1(result)
    assert validation["valid"] is False
    assert any("unsafe_" in label for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("final_loop_summary",), "public breakthrough claim"),
        (("final_loop_summary",), "final-answer authority"),
        (("input_signal", "signal_summary"), "hidden prompt secret"),
        (("input_signal", "signal_summary"), ".weslr live ingestion"),
        (("raw_signal_cartography", "input_summary"), "provider call"),
        (("unintelligible_output_analysis", "artifact_summary"), "tool execution"),
    ],
)
def test_forbidden_text_fail_closed(path, value):
    result = _result()
    target = result
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    validation = validate_minimal_recursive_research_loop_result_v1(result)
    assert validation["valid"] is False
    assert any("forbidden" in label or "invalid" in label for label in validation["blocked_labels"])


def test_json_safe_copy_redacts_forbidden_text():
    result = _result()
    result["raw_signal_cartography"]["artifact_summary"] = "hidden prompt secret private text"
    result["suggestion_store_update_packet"]["update_actions"][0]["action_reason"] = "provider call and tool execution"

    safe = to_minimal_recursive_research_loop_json_safe_v1(result)

    assert safe["raw_signal_cartography"]["artifact_summary"] == "[redacted]"
    assert safe["suggestion_store_update_packet"]["update_actions"][0]["action_reason"] == "[redacted]"
    assert result["raw_signal_cartography"]["artifact_summary"] != "[redacted]"


def test_minimal_loop_input_signal_is_metadata_only():
    signal = build_minimal_loop_input_signal_v1()
    assert signal["raw_content_included"] is False
    assert signal["raw_content_ref_only"] is True
    assert signal["safe_metadata"]["metadata_only"] is True
    assert signal["denied_authority"]["status"] == "metadata_only"


def test_result_fields_are_json_safe_and_private_safe():
    result = _result()
    safe = to_minimal_recursive_research_loop_json_safe_v1(result)

    assert safe["schema_version"]
    assert safe["loop_run_id"].startswith("loop:")
    assert safe["safe_metadata"]["no_runtime_wiring"] is True
    assert safe["safe_metadata"]["no_public_claim"] is True
    assert safe["blocked_actions"] == []
    assert safe["recommended_next_internal_step"] in ALLOWED_NEXT_INTERNAL_STEPS_V1


def test_stage_results_remain_compatible_with_existing_module_validators():
    result = _result()
    assert validate_raw_signal_cartography_packet_v1(result["raw_signal_cartography"])["valid"] is True
    assert validate_unintelligible_output_analysis_packet_v1(result["unintelligible_output_analysis"])["valid"] is True
    assert validate_unknown_engine_research_run_v1(result["unknown_engine_run"])["valid"] is True
    assert validate_nonlinear_inspiration_packet_v1(result["nonlinear_inspiration_run"])["valid"] is True
    assert validate_rule_pressure_packet_v1(result["rule_pressure_run"])["valid"] is True
    assert validate_dialectic_loop_packet_v1(result["dialectic_generator_run"])["blocked"] is False
    assert validate_perspicuity_packet_v1(result["perspicuity_score_run"])["blocked"] is False
    assert validate_suggestion_store_update_packet_v1(result["suggestion_store_update_packet"])["blocked"] is False
    assert validate_forecast_calibration_record_v1(result["calibration_bridge_record"])["valid"] is True


def test_suggestion_store_update_stays_proposal_only_and_calibration_stays_metadata_only():
    result = _result()
    suggestion = result["suggestion_store_update_packet"]
    calibration = result["calibration_bridge_record"]

    assert suggestion["operator_review_required"] is True
    assert suggestion["storage_write_authorized"] is False
    assert suggestion["memory_mutation_authorized"] is False
    assert suggestion["project_mutation_authorized"] is False
    assert suggestion["behavior_promotion_authorized"] is False
    assert calibration["calibration_result"] == "not_yet_calibrated"
    assert calibration["outcome_status"] == "not_observed_yet"
