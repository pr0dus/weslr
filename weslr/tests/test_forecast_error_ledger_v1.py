from __future__ import annotations

import sys
from pathlib import Path

import pytest

from weslr.forecast_error_ledger import (
    ForecastErrorLedger,
    ForecastErrorRecord,
    ForecastErrorRecordSummary,
    ForecastErrorLedgerSummary,
    ValidationError,
    build_forecast_error_ledger_v1,
    build_forecast_error_record_v1,
    build_initial_forecast_error_examples_v1,
    summarize_forecast_error_ledger_v1,
    summarize_forecast_error_record_v1,
    to_forecast_error_json_safe_v1,
    validate_forecast_error_ledger_v1,
    validate_forecast_error_record_v1,
)


BASE_RECORD_KWARGS = dict(
    forecast_error_record_id="base_forecast_error_v1",
    source_forecast_id="forecast_1",
    source_scenario_simulation_id="scenario_1",
    source_energy_intelligence_id="energy_intelligence_1",
    subject="base_forecast",
    domain="energy_home_forecast",
    forecast_horizon="2h",
    created_timestamp="2026-06-01T20:00:00+02:00",
    observation_timestamp="2026-06-01T22:00:00+02:00",
    expected_outcome="expected",
    observed_outcome="observed",
    outcome_match_status="matched",
    error_type="unknown_error",
    error_severity="none",
    confidence_before=0.7,
    confidence_after=0.8,
    assumptions_used=["fresh local signals"],
    signals_used=["battery_soc_home_assistant_fresh"],
    recommendation_taken="recommendation_only",
    owner_action_taken="none",
    resulting_effect="confirmed",
    corrective_lesson="keep this path",
    recommended_model_update="keep baseline",
    behavior_pack_candidate="",
    safe_metadata={"example_name": "base_forecast_error"},
)


BASE_LEDGER_KWARGS = dict(
    forecast_error_ledger_id="ledger_v1",
    ledger_version="v1",
)


def _record(**overrides):
    payload = dict(BASE_RECORD_KWARGS)
    payload.update(overrides)
    return build_forecast_error_record_v1(**payload)


def _record_payload(**overrides):
    payload = to_forecast_error_json_safe_v1(_record())
    payload.update(overrides)
    return payload


def _ledger(records=None, **overrides):
    payload = dict(BASE_LEDGER_KWARGS)
    payload.update(overrides)
    if records is None:
        records = build_initial_forecast_error_examples_v1()
    return build_forecast_error_ledger_v1(records=records, **payload)


def test_module_imports_safely():
    import weslr.forecast_error_ledger as mod

    assert mod.HELPER_TYPE_V1 == "forecast_error_ledger_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_forecast_error_record():
    first = _record()
    second = _record()

    assert first == second
    assert isinstance(first, ForecastErrorRecord)
    assert first.runtime_authority is False
    assert first.writes_state is False


def test_validates_normal_record():
    assert validate_forecast_error_record_v1(_record()) is True


def test_builds_deterministic_ledger():
    first = _ledger(records=[_record(), _record(forecast_error_record_id="base_forecast_error_v2")])
    second = _ledger(records=[_record(), _record(forecast_error_record_id="base_forecast_error_v2")])

    assert first == second
    assert isinstance(first, ForecastErrorLedger)
    assert first.record_count == 2


def test_validates_normal_ledger():
    ledger = _ledger(records=[_record(), _record(forecast_error_record_id="base_forecast_error_v2")])
    assert validate_forecast_error_ledger_v1(ledger) is True


def test_summarizes_record():
    summary = summarize_forecast_error_record_v1(_record())
    assert isinstance(summary, ForecastErrorRecordSummary)
    assert summary.forecast_error_record_id == "base_forecast_error_v1"
    assert summary.outcome_match_status == "matched"


def test_summarizes_ledger_with_counts():
    ledger = _ledger(records=[_record(), _record(forecast_error_record_id="base_forecast_error_v2", domain="grid_signal_forecast")])
    summary = summarize_forecast_error_ledger_v1(ledger)
    assert isinstance(summary, ForecastErrorLedgerSummary)
    assert summary.record_count == 2
    assert summary.domain_counts["energy_home_forecast"] == 1
    assert summary.domain_counts["grid_signal_forecast"] == 1


def test_detects_repeated_stale_signal_pattern():
    stale_a = _record(
        forecast_error_record_id="stale_1",
        source_forecast_id="stale_forecast_1",
        subject="stale_forecast",
        outcome_match_status="missed",
        error_type="stale_signal",
        stale_signals=["weather_forecast_location_scoped"],
    )
    stale_b = _record(
        forecast_error_record_id="stale_2",
        source_forecast_id="stale_forecast_2",
        subject="stale_forecast",
        outcome_match_status="missed",
        error_type="stale_signal",
        stale_signals=["weather_forecast_location_scoped"],
    )
    ledger = _ledger(records=[stale_a, stale_b])
    summary = summarize_forecast_error_ledger_v1(ledger)
    assert any("stale_signal" in item for item in summary.repeated_error_patterns)


def test_detects_repeated_missing_signal_pattern():
    missing_a = _record(
        forecast_error_record_id="missing_1",
        source_forecast_id="missing_forecast_1",
        subject="missing_forecast",
        outcome_match_status="missed",
        error_type="missing_signal",
        missing_signals=["battery_soc_source"],
    )
    missing_b = _record(
        forecast_error_record_id="missing_2",
        source_forecast_id="missing_forecast_2",
        subject="missing_forecast",
        outcome_match_status="missed",
        error_type="missing_signal",
        missing_signals=["battery_soc_source"],
    )
    ledger = _ledger(records=[missing_a, missing_b])
    summary = summarize_forecast_error_ledger_v1(ledger)
    assert any("missing_signal" in item for item in summary.repeated_error_patterns)


def test_includes_behavior_pack_candidates_as_proposal_only():
    ledger = _ledger(records=build_initial_forecast_error_examples_v1())
    summary = summarize_forecast_error_ledger_v1(ledger)
    assert summary.behavior_pack_candidates
    assert ledger.runtime_authority is False
    assert ledger.writes_state is False
    assert ledger.public_claim_allowed is False
    assert ledger.learning_claimed is False


def test_json_safe_export_works():
    payload = to_forecast_error_json_safe_v1(_record())
    assert isinstance(payload, dict)
    assert payload["forecast_error_record_id"] == "base_forecast_error_v1"


def test_all_initial_examples_exist():
    ids = {item.forecast_error_record_id for item in build_initial_forecast_error_examples_v1()}
    assert ids == {
        "pv_surplus_missed_stale_weather_v1",
        "battery_reserve_wrong_soc_source_v1",
        "heat_pump_preheat_wrong_missing_comfort_priority_v1",
        "ev_charging_wrong_departure_changed_v1",
        "carbon_recommendation_wrong_grid_zone_unresolved_v1",
        "price_recommendation_partially_matched_comfort_priority_v1",
        "import_export_macro_signal_overweighted_v1",
        "good_forecast_matched_fresh_local_signals_v1",
        "next_lane_forecast_wrong_hidden_dependency_v1",
        "public_readiness_forecast_correctly_blocked_v1",
    }


def test_no_initial_example_has_runtime_authority():
    for item in build_initial_forecast_error_examples_v1():
        assert item.runtime_authority is False


def test_no_initial_example_writes_state():
    for item in build_initial_forecast_error_examples_v1():
        assert item.writes_state is False


def test_no_initial_example_allows_public_claim():
    for item in build_initial_forecast_error_examples_v1():
        assert item.public_claim_allowed is False


def test_no_initial_example_claims_autonomous_learning():
    for item in build_initial_forecast_error_examples_v1():
        assert item.learning_claimed is False


def test_no_initial_example_uses_action_authority():
    for item in build_initial_forecast_error_examples_v1():
        assert item.action_authority_used is False


def test_validation_fails_unknown_outcome_status():
    with pytest.raises(ValidationError, match="unknown_outcome_match_status"):
        validate_forecast_error_record_v1(_record(outcome_match_status="mystery"))


def test_validation_fails_unknown_error_type():
    with pytest.raises(ValidationError, match="unknown_error_type"):
        validate_forecast_error_record_v1(_record(error_type="mystery_error"))


def test_validation_fails_unknown_severity():
    with pytest.raises(ValidationError, match="unknown_severity"):
        validate_forecast_error_record_v1(_record(error_severity="mystery_severity"))


def test_validation_fails_unknown_domain():
    with pytest.raises(ValidationError, match="unknown_domain"):
        validate_forecast_error_record_v1(_record(domain="mystery_domain"))


def test_validation_fails_runtime_authority_true():
    with pytest.raises(ValidationError, match="runtime_authority_must_be_false"):
        validate_forecast_error_record_v1(_record(runtime_authority=True))


def test_validation_fails_writes_state_true():
    with pytest.raises(ValidationError, match="writes_state_must_be_false"):
        validate_forecast_error_record_v1(_record(writes_state=True))


def test_validation_fails_public_claim_allowed_true():
    with pytest.raises(ValidationError, match="public_claim_allowed_must_be_false"):
        validate_forecast_error_record_v1(_record(public_claim_allowed=True))


def test_validation_fails_learning_claimed_true():
    with pytest.raises(ValidationError, match="learning_claimed_must_be_false"):
        validate_forecast_error_record_v1(_record(learning_claimed=True))


def test_validation_fails_action_authority_used_true():
    with pytest.raises(ValidationError, match="action_authority_used_must_be_false"):
        validate_forecast_error_record_v1(_record(action_authority_used=True))


def test_validation_fails_autonomous_learning_claim():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_forecast_error_record_v1(_record(safe_metadata={"notes": "autonomous learning claim"}))


def test_validation_fails_prediction_certainty_claim():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_forecast_error_record_v1(_record(safe_metadata={"notes": "prediction certainty claim"}))


def test_validation_fails_energy_savings_guarantee():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_forecast_error_record_v1(_record(safe_metadata={"notes": "energy savings guarantee"}))


def test_validation_fails_hidden_prompt_raw_private_or_secret_fields():
    payload = _record_payload()
    payload["hidden_prompt"] = "secret hidden prompt"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_forecast_error_record_v1(payload)

    payload = _record_payload()
    payload["raw_private_data"] = "secret raw private data"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_forecast_error_record_v1(payload)

    payload = _record_payload()
    payload["secret_token"] = "tok_123"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_forecast_error_record_v1(payload)


def test_validation_fails_agi_consciousness_turing_certification_marker():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_forecast_error_record_v1(_record(safe_metadata={"notes": "AGI consciousness sentience Turing certification"}))


def test_module_does_not_import_or_call_chat_responder():
    source = Path(__file__).resolve().parents[1] / "forecast_error_ledger.py"
    text = source.read_text()
    assert "chat_responder" not in text
    assert "weslr.chat_responder" not in sys.modules


def test_module_does_not_import_or_call_main():
    source = Path(__file__).resolve().parents[1] / "forecast_error_ledger.py"
    text = source.read_text()
    assert "main.py" not in text
    assert "weslr.main" not in sys.modules


def test_module_does_not_import_or_call_dialogue():
    source = Path(__file__).resolve().parents[1] / "forecast_error_ledger.py"
    text = source.read_text()
    assert "dialogue" not in text
    assert "dialogue" not in sys.modules


def test_module_does_not_import_or_call_chat_ui():
    source = Path(__file__).resolve().parents[1] / "forecast_error_ledger.py"
    text = source.read_text()
    assert "chat_ui" not in text
    assert "chat_ui" not in sys.modules
