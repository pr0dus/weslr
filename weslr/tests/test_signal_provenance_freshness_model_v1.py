from __future__ import annotations

import sys
from pathlib import Path

import pytest

from weslr.signal_provenance_freshness_model import (
    SignalProvenanceRecord,
    SignalProvenanceSummary,
    ValidationError,
    build_initial_signal_provenance_examples_v1,
    build_signal_provenance_record_v1,
    detect_signal_conflict_v1,
    evaluate_signal_freshness_v1,
    evaluate_signal_quality_v1,
    summarize_signal_provenance_record_v1,
    to_signal_provenance_json_safe_v1,
    validate_signal_provenance_record_v1,
)


BASE_RECORD_KWARGS = dict(
    signal_provenance_id="base_signal_v1",
    signal_id="base_signal",
    signal_name="Base Signal",
    signal_class="home_assistant_entity",
    source_system="home_assistant",
    source_provider="local_entity",
    source_reference="sensor.base_signal",
    source_url_or_entity_id="sensor.base_signal",
    source_scope="local_home",
    owner_authorized=True,
    operator_authorized=True,
    retrieval_method="entity_read",
    retrieval_timestamp="2026-06-01T20:00:00+02:00",
    reported_timestamp="2026-06-01T19:59:00+02:00",
    timezone="Europe/Berlin",
    region="de-by",
    country="DE",
    grid_zone="de-lu",
    market_zone="de-lu",
    unit="%",
    value_type="numeric",
    expected_update_cadence="minutes",
    poison_shield_status="clean",
    privacy_sensitivity="low",
    control_capable=True,
    forecasting_allowed=True,
    scenario_simulation_allowed=True,
    safe_metadata={"signal_value": 50},
)


def _record(**overrides):
    payload = dict(BASE_RECORD_KWARGS)
    payload.update(overrides)
    return build_signal_provenance_record_v1(**payload)


def _payload(**overrides):
    payload = to_signal_provenance_json_safe_v1(_record())
    payload.update(overrides)
    return payload


def test_module_imports_safely():
    import weslr.signal_provenance_freshness_model as mod

    assert mod.HELPER_TYPE_V1 == "signal_provenance_freshness_model_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_signal_provenance_record():
    first = _record()
    second = _record()

    assert first == second
    assert isinstance(first, SignalProvenanceRecord)
    assert first.memory_write_allowed is False
    assert first.action_authority_granted is False


@pytest.mark.parametrize(
    "reported_timestamp,expected,cadence",
    [
        ("2026-06-01T19:59:30+02:00", "fresh", "minutes"),
        ("2026-06-01T12:00:00+02:00", "stale", "hourly"),
        ("2026-05-31T18:00:00+02:00", "expired", "hourly"),
        ("", "missing_timestamp", "minutes"),
        ("2026-06-01T21:00:00+02:00", "future_timestamp", "minutes"),
    ],
)
def test_evaluates_freshness_cases(reported_timestamp, expected, cadence):
    freshness = evaluate_signal_freshness_v1(_record(reported_timestamp=reported_timestamp, expected_update_cadence=cadence))
    assert freshness == expected


def test_evaluates_high_quality_signal():
    record = _record(reported_timestamp="2026-06-01T19:59:30+02:00")
    assert evaluate_signal_quality_v1(record) == "high_quality"


def test_evaluates_poison_risk_signal():
    record = build_initial_signal_provenance_examples_v1()[7]
    assert record.signal_id == "poison_risk_external_document_signal"
    assert evaluate_signal_quality_v1(record) == "poison_risk"


def test_detects_no_conflict():
    assert detect_signal_conflict_v1([_record()]) == "no_conflict"


def test_detects_value_conflict():
    a = _record(signal_id="value_conflict", safe_metadata={"signal_value": 10})
    b = _record(signal_id="value_conflict", safe_metadata={"signal_value": 90})
    assert detect_signal_conflict_v1([a, b]) == "value_conflict"


def test_detects_timestamp_conflict():
    a = _record(signal_id="timestamp_conflict", reported_timestamp="2026-06-01T19:59:30+02:00")
    b = _record(signal_id="timestamp_conflict", reported_timestamp="2026-06-01T19:30:00+02:00")
    assert detect_signal_conflict_v1([a, b]) == "timestamp_conflict"


def test_detects_unit_conflict():
    a = _record(signal_id="unit_conflict", unit="%")
    b = _record(signal_id="unit_conflict", unit="kWh")
    assert detect_signal_conflict_v1([a, b]) == "unit_conflict"


def test_detects_region_conflict():
    a = _record(signal_id="region_conflict", region="de-by", country="DE", grid_zone="de-lu")
    b = _record(signal_id="region_conflict", region="de-nw", country="DE", grid_zone="de-nw")
    assert detect_signal_conflict_v1([a, b]) == "region_conflict"


def test_detects_source_disagreement():
    a = _record(signal_id="source_disagreement", source_system="home_assistant", source_provider="local_entity")
    b = _record(signal_id="source_disagreement", source_system="inverter_api", source_provider="battery_vendor")
    assert detect_signal_conflict_v1([a, b]) == "source_disagreement"


def test_json_safe_export_works():
    payload = to_signal_provenance_json_safe_v1(_record())
    assert isinstance(payload, dict)
    assert payload["signal_id"] == "base_signal"
    assert payload["safe_metadata"]["signal_value"] == 50


def test_summary_includes_signal_id_freshness_quality_conflict():
    summary = summarize_signal_provenance_record_v1(_record())

    assert isinstance(summary, SignalProvenanceSummary)
    assert summary.signal_id == "base_signal"
    assert summary.freshness_status == "fresh"
    assert summary.quality_status == "high_quality"
    assert summary.conflict_status == "no_conflict"


def test_all_initial_examples_exist():
    ids = {item.signal_id for item in build_initial_signal_provenance_examples_v1()}
    assert ids == {
        "battery_soc_home_assistant_fresh",
        "electricity_price_day_ahead_recent",
        "carbon_intensity_grid_zone_recent",
        "import_export_country_macro_context",
        "weather_forecast_location_scoped",
        "pv_forecast_weather_conflict",
        "battery_soc_source_conflict",
        "poison_risk_external_document_signal",
        "missing_timestamp_signal",
        "future_timestamp_signal",
    }


def test_no_initial_example_writes_memory():
    for record in build_initial_signal_provenance_examples_v1():
        assert record.memory_write_allowed is False


def test_no_initial_example_grants_action_authority():
    for record in build_initial_signal_provenance_examples_v1():
        assert record.action_authority_granted is False


def test_validation_fails_unknown_freshness():
    with pytest.raises(ValidationError, match="unknown_freshness"):
        validate_signal_provenance_record_v1(_payload(freshness_status="mystery_freshness"))


def test_validation_fails_unknown_quality():
    with pytest.raises(ValidationError, match="unknown_quality"):
        validate_signal_provenance_record_v1(_payload(quality_status="mystery_quality"))


def test_validation_fails_unknown_source_class():
    with pytest.raises(ValidationError, match="unknown_source_class"):
        validate_signal_provenance_record_v1(_payload(signal_class="mystery_source"))


def test_validation_fails_unknown_conflict():
    with pytest.raises(ValidationError, match="unknown_conflict"):
        validate_signal_provenance_record_v1(_payload(conflict_status="mystery_conflict"))


def test_validation_fails_memory_write_allowed_true():
    with pytest.raises(ValidationError, match="memory_write_allowed_must_be_false"):
        validate_signal_provenance_record_v1(_payload(memory_write_allowed=True))


def test_validation_fails_action_authority_granted_true():
    with pytest.raises(ValidationError, match="action_authority_granted_must_be_false"):
        validate_signal_provenance_record_v1(_payload(action_authority_granted=True))


def test_validation_fails_hidden_prompt_raw_private_or_secret_fields():
    payload = _payload()
    payload["hidden_prompt"] = "secret hidden prompt"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_signal_provenance_record_v1(payload)

    payload = _payload()
    payload["raw_private_data"] = "secret raw private data"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_signal_provenance_record_v1(payload)

    payload = _payload()
    payload["secret_token"] = "tok_123"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_signal_provenance_record_v1(payload)


def test_validation_fails_agi_consciousness_turing_certification_marker():
    payload = _payload(safe_metadata={"notes": "AGI consciousness sentience Turing certification"})
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_signal_provenance_record_v1(payload)


def test_validation_fails_public_readiness_claim():
    payload = _payload(safe_metadata={"notes": "public readiness claim"})
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_signal_provenance_record_v1(payload)


def test_module_does_not_import_or_call_chat_responder():
    source = Path(__file__).resolve().parents[1] / "signal_provenance_freshness_model.py"
    text = source.read_text()
    assert "chat_responder" not in text
    assert "weslr.chat_responder" not in sys.modules


def test_module_does_not_import_or_call_main():
    source = Path(__file__).resolve().parents[1] / "signal_provenance_freshness_model.py"
    text = source.read_text()
    assert "main.py" not in text
    assert "weslr.main" not in sys.modules


def test_module_does_not_import_or_call_dialogue():
    source = Path(__file__).resolve().parents[1] / "signal_provenance_freshness_model.py"
    text = source.read_text()
    assert "dialogue" not in text
    assert "dialogue" not in sys.modules


def test_module_does_not_import_or_call_chat_ui():
    source = Path(__file__).resolve().parents[1] / "signal_provenance_freshness_model.py"
    text = source.read_text()
    assert "chat_ui" not in text
    assert "chat_ui" not in sys.modules
