from __future__ import annotations

import sys
from pathlib import Path

import pytest

from weslr.energy_signal_conflict_resolution_policy import (
    EnergySignalConflictDecision,
    EnergySignalConflictSummary,
    ValidationError,
    build_energy_signal_conflict_decision_v1,
    build_initial_energy_signal_conflict_examples_v1,
    classify_energy_signal_conflict_v1,
    resolve_energy_signal_conflict_v1,
    summarize_energy_signal_conflict_decision_v1,
    to_energy_signal_conflict_json_safe_v1,
    validate_energy_signal_conflict_decision_v1,
)
from weslr.signal_provenance_freshness_model import build_signal_provenance_record_v1


BASE_SIGNAL_A = dict(
    signal_provenance_id="signal_a_v1",
    signal_id="electricity_price_day_ahead_recent",
    signal_name="Electricity Price Day Ahead Recent",
    signal_class="electricity_price_provider",
    source_system="price_api",
    source_provider="market_operator",
    source_reference="day-ahead-a",
    source_url_or_entity_id="de-day-ahead",
    source_scope="market_zone",
    owner_authorized=False,
    operator_authorized=False,
    retrieval_method="api_poll",
    retrieval_timestamp="2026-06-01T20:00:00+02:00",
    reported_timestamp="2026-06-01T19:30:00+02:00",
    timezone="Europe/Berlin",
    region="de",
    country="DE",
    grid_zone="de-lu",
    market_zone="de-lu",
    unit="EUR/kWh",
    value_type="numeric",
    expected_update_cadence="hourly",
    poison_shield_status="clean",
    privacy_sensitivity="low",
    control_capable=False,
    forecasting_allowed=True,
    scenario_simulation_allowed=True,
    safe_metadata={"signal_value": 0.31},
)

BASE_SIGNAL_B = dict(
    signal_provenance_id="signal_b_v1",
    signal_id="carbon_intensity_grid_zone_recent",
    signal_name="Carbon Intensity Grid Zone Recent",
    signal_class="grid_carbon_provider",
    source_system="carbon_api",
    source_provider="grid_operator",
    source_reference="carbon-b",
    source_url_or_entity_id="grid-zone:de-lu",
    source_scope="grid_zone",
    owner_authorized=False,
    operator_authorized=False,
    retrieval_method="api_poll",
    retrieval_timestamp="2026-06-01T20:00:00+02:00",
    reported_timestamp="2026-06-01T19:20:00+02:00",
    timezone="Europe/Berlin",
    region="de",
    country="DE",
    grid_zone="de-lu",
    market_zone="de-lu",
    unit="gCO2/kWh",
    value_type="numeric",
    expected_update_cadence="hourly",
    poison_shield_status="clean",
    privacy_sensitivity="low",
    control_capable=False,
    forecasting_allowed=True,
    scenario_simulation_allowed=True,
    safe_metadata={"signal_value": 248},
)


def _record_a(**overrides):
    payload = dict(BASE_SIGNAL_A)
    payload.update(overrides)
    return build_signal_provenance_record_v1(**payload)


def _record_b(**overrides):
    payload = dict(BASE_SIGNAL_B)
    payload.update(overrides)
    return build_signal_provenance_record_v1(**payload)


def _decision(**overrides):
    payload = dict(
        conflict_decision_id="decision_v1",
        decision_subject="decision_subject",
        conflict_classes=["price_vs_carbon_conflict"],
        involved_signals=[_record_a(), _record_b()],
        optimization_goal="minimize_cost",
        safe_metadata={"example_name": "decision"},
    )
    payload.update(overrides)
    return build_energy_signal_conflict_decision_v1(**payload)


def test_module_imports_safely():
    import weslr.energy_signal_conflict_resolution_policy as mod

    assert mod.HELPER_TYPE_V1 == "energy_signal_conflict_resolution_policy_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_conflict_decision():
    first = _decision()
    second = _decision()

    assert first == second
    assert isinstance(first, EnergySignalConflictDecision)
    assert first.action_authority_granted is False
    assert first.automation_allowed is False
    assert first.device_control_allowed is False


def test_classifies_price_vs_carbon_conflict():
    assert classify_energy_signal_conflict_v1([_record_a(), _record_b()]) == "price_vs_carbon_conflict"


def test_classifies_pv_forecast_vs_weather_conflict():
    pv = build_signal_provenance_record_v1(
        signal_provenance_id="pv_v1",
        signal_id="pv_forecast_signal",
        signal_name="PV Forecast Signal",
        signal_class="weather_provider",
        source_system="forecast_service",
        source_provider="forecast_service",
        source_reference="pv-forecast",
        source_url_or_entity_id="forecast:pv",
        source_scope="location_scoped",
        owner_authorized=False,
        operator_authorized=False,
        retrieval_method="synthetic_in_memory",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:40:00+02:00",
        timezone="Europe/Berlin",
        region="de-by",
        country="DE",
        grid_zone="de-lu",
        market_zone="de-lu",
        unit="kWh",
        value_type="numeric",
        expected_update_cadence="hourly",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": 14},
    )
    weather = build_signal_provenance_record_v1(
        signal_provenance_id="weather_v1",
        signal_id="weather_forecast_signal",
        signal_name="Weather Forecast Signal",
        signal_class="weather_provider",
        source_system="weather_api",
        source_provider="weather_service",
        source_reference="weather-1",
        source_url_or_entity_id="location:berlin",
        source_scope="location_scoped",
        owner_authorized=False,
        operator_authorized=False,
        retrieval_method="api_poll",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:35:00+02:00",
        timezone="Europe/Berlin",
        region="de-by",
        country="DE",
        grid_zone="de-lu",
        market_zone="de-lu",
        unit="°C",
        value_type="numeric",
        expected_update_cadence="hourly",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": 18.5},
    )
    assert classify_energy_signal_conflict_v1([pv, weather]) == "pv_forecast_vs_weather_conflict"


def test_classifies_battery_soc_source_conflict():
    a = build_signal_provenance_record_v1(
        signal_provenance_id="soc_a_v1",
        signal_id="battery_soc_signal",
        signal_name="Battery SOC Signal",
        signal_class="home_assistant_entity",
        source_system="home_assistant",
        source_provider="local_entity",
        source_reference="sensor.battery_soc",
        source_url_or_entity_id="sensor.battery_soc",
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
        safe_metadata={"signal_value": 20},
    )
    b = build_signal_provenance_record_v1(
        signal_provenance_id="soc_b_v1",
        signal_id="battery_soc_signal",
        signal_name="Battery SOC Signal",
        signal_class="inverter_or_battery_api",
        source_system="inverter_api",
        source_provider="battery_vendor",
        source_reference="battery.soc",
        source_url_or_entity_id="device:inverter",
        source_scope="local_home",
        owner_authorized=True,
        operator_authorized=True,
        retrieval_method="api_poll",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:58:30+02:00",
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
        safe_metadata={"signal_value": 80},
    )
    assert classify_energy_signal_conflict_v1([a, b]) == "battery_soc_source_conflict"


def test_classifies_grid_import_export_scope_conflict():
    local = build_signal_provenance_record_v1(
        signal_provenance_id="local_flow_v1",
        signal_id="local_import_export_flow_signal",
        signal_name="Local Import Export Flow Signal",
        signal_class="import_export_flow_provider",
        source_system="home_energy_meter",
        source_provider="local_meter",
        source_reference="meter-home-flow",
        source_url_or_entity_id="meter:home-flow",
        source_scope="local_home",
        owner_authorized=True,
        operator_authorized=True,
        retrieval_method="entity_read",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:58:50+02:00",
        timezone="Europe/Berlin",
        region="de-by",
        country="DE",
        grid_zone="de-lu",
        market_zone="de-lu",
        unit="kW",
        value_type="numeric",
        expected_update_cadence="minutes",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": 1.5},
    )
    country = build_signal_provenance_record_v1(
        signal_provenance_id="country_flow_v1",
        signal_id="import_export_country_macro_context",
        signal_name="Import Export Country Macro Context",
        signal_class="import_export_flow_provider",
        source_system="grid_context_api",
        source_provider="national_operator",
        source_reference="de-import-export",
        source_url_or_entity_id="country:de",
        source_scope="country_macro",
        owner_authorized=False,
        operator_authorized=False,
        retrieval_method="api_poll",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:55:00+02:00",
        timezone="Europe/Berlin",
        region="de",
        country="DE",
        grid_zone="de",
        market_zone="de",
        unit="kW",
        value_type="numeric",
        expected_update_cadence="hourly",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": -420},
    )
    assert classify_energy_signal_conflict_v1([local, country]) == "grid_import_export_scope_conflict"


def test_classifies_region_grid_zone_conflict():
    a = _record_a(region="de-by", grid_zone="de-lu", market_zone="de-lu", unit="EUR/kWh")
    b = _record_b(region="de-nw", grid_zone="de-nw", market_zone="de-nw", unit="EUR/kWh", signal_id="electricity_price_day_ahead_recent_2")
    assert classify_energy_signal_conflict_v1([a, b]) == "region_or_grid_zone_conflict"


def test_resolves_stale_signal_with_wait_no_action():
    stale = _record_a(signal_id="stale_price_signal", reported_timestamp="2026-06-01T10:00:00+02:00")
    decision = resolve_energy_signal_conflict_v1([stale], decision_subject="stale_signal_no_action_recommendation", optimization_goal="safety_first")
    assert decision.recommended_resolution_strategy == "wait_for_fresh_signal"
    assert decision.safe_recommendation_mode == "recommendation_only"
    assert decision.action_authority_granted is False


def test_resolves_owner_priority_with_owner_priority_strategy():
    decision = resolve_energy_signal_conflict_v1(
        [_record_a(), _record_b()],
        decision_subject="owner_priority_case",
        optimization_goal="minimize_cost",
        owner_priority=True,
    )
    assert decision.recommended_resolution_strategy == "prefer_owner_manual_priority"


def test_resolves_safety_constraint_with_safety_first_strategy():
    comfort = build_signal_provenance_record_v1(
        signal_provenance_id="comfort_v1",
        signal_id="heat_pump_comfort_signal",
        signal_name="Heat Pump Comfort Signal",
        signal_class="heat_pump_api",
        source_system="heat_pump_api",
        source_provider="heat_pump_vendor",
        source_reference="heat-pump-1",
        source_url_or_entity_id="device:heat-pump",
        source_scope="local_home",
        owner_authorized=True,
        operator_authorized=True,
        retrieval_method="api_poll",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:59:00+02:00",
        timezone="Europe/Berlin",
        region="de-by",
        country="DE",
        grid_zone="de-lu",
        market_zone="de-lu",
        unit="°C",
        value_type="numeric",
        expected_update_cadence="hourly",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=True,
        safe_metadata={"signal_value": 21.0},
    )
    decision = resolve_energy_signal_conflict_v1(
        [comfort, _record_a()],
        decision_subject="heat_pump_comfort_vs_price_conflict",
        optimization_goal="maintain_comfort",
        safety_constraints=["comfort_band"],
    )
    assert decision.recommended_resolution_strategy == "prefer_safety_constraint"


def test_sets_scenario_branch_required_for_tradeoff_conflicts():
    decision = resolve_energy_signal_conflict_v1([_record_a(), _record_b()], decision_subject="tradeoff", optimization_goal="minimize_cost")
    assert decision.scenario_branch_required is True


def test_never_silently_averages_conflicts():
    decision = resolve_energy_signal_conflict_v1([_record_a(), _record_b()], decision_subject="no_average", optimization_goal="minimize_cost")
    assert decision.unresolved_conflicts
    assert decision.recommended_resolution_strategy in {"branch_scenarios", "prefer_owner_manual_priority", "preserve_conflict"}


def test_local_household_signal_distinguished_from_macro_import_export_signal():
    local = build_signal_provenance_record_v1(
        signal_provenance_id="local_flow_v2",
        signal_id="local_import_export_flow_signal",
        signal_name="Local Import Export Flow Signal",
        signal_class="import_export_flow_provider",
        source_system="home_energy_meter",
        source_provider="local_meter",
        source_reference="meter-home-flow",
        source_url_or_entity_id="meter:home-flow",
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
        unit="kW",
        value_type="numeric",
        expected_update_cadence="minutes",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": 1.2},
    )
    macro = build_signal_provenance_record_v1(
        signal_provenance_id="macro_flow_v2",
        signal_id="import_export_country_macro_context",
        signal_name="Import Export Country Macro Context",
        signal_class="import_export_flow_provider",
        source_system="grid_context_api",
        source_provider="national_operator",
        source_reference="de-import-export",
        source_url_or_entity_id="country:de",
        source_scope="country_macro",
        owner_authorized=False,
        operator_authorized=False,
        retrieval_method="api_poll",
        retrieval_timestamp="2026-06-01T20:00:00+02:00",
        reported_timestamp="2026-06-01T19:59:30+02:00",
        timezone="Europe/Berlin",
        region="de",
        country="DE",
        grid_zone="de",
        market_zone="de",
        unit="kW",
        value_type="numeric",
        expected_update_cadence="hourly",
        poison_shield_status="clean",
        privacy_sensitivity="low",
        control_capable=False,
        safe_metadata={"signal_value": -420},
    )
    assert classify_energy_signal_conflict_v1([local, macro]) == "grid_import_export_scope_conflict"
    assert local.source_scope == "local_home"
    assert macro.source_scope == "country_macro"


def test_control_capable_signal_does_not_grant_control_authority():
    record = _record_a(control_capable=True)
    assert record.control_capable is True
    assert record.action_authority_granted is False
    assert record.memory_write_allowed is False


def test_json_safe_export_works():
    payload = to_energy_signal_conflict_json_safe_v1(_decision())
    assert isinstance(payload, dict)
    assert payload["decision_subject"] == "decision_subject"
    assert payload["conflict_classes"] == ["price_vs_carbon_conflict"]


def test_summary_includes_conflict_classes_strategy_confidence_adjustment():
    summary = summarize_energy_signal_conflict_decision_v1(_decision())
    assert isinstance(summary, EnergySignalConflictSummary)
    assert summary.conflict_classes == ["price_vs_carbon_conflict"]
    assert summary.recommended_resolution_strategy in {"preserve_conflict", "branch_scenarios", "prefer_owner_manual_priority"}
    assert isinstance(summary.confidence_adjustment, float)


def test_all_initial_examples_exist():
    names = {item.decision_subject for item in build_initial_energy_signal_conflict_examples_v1()}
    assert names == {
        "price_low_carbon_high_conflict",
        "price_high_pv_surplus_likely_conflict",
        "pv_forecast_weather_cloud_conflict",
        "battery_soc_source_mismatch_conflict",
        "country_import_export_vs_household_flow_conflict",
        "heat_pump_comfort_vs_price_conflict",
        "ev_departure_deadline_vs_carbon_window_conflict",
        "occupancy_signal_privacy_limited_conflict",
        "control_capable_entity_read_only_conflict",
        "stale_signal_no_action_recommendation",
    }


def test_no_initial_example_grants_action_authority():
    for item in build_initial_energy_signal_conflict_examples_v1():
        assert item.action_authority_granted is False


def test_no_initial_example_allows_automation():
    for item in build_initial_energy_signal_conflict_examples_v1():
        assert item.automation_allowed is False


def test_no_initial_example_allows_device_control():
    for item in build_initial_energy_signal_conflict_examples_v1():
        assert item.device_control_allowed is False


def test_validation_fails_unknown_conflict_class():
    with pytest.raises(ValidationError, match="unknown_conflict_class"):
        validate_energy_signal_conflict_decision_v1(_decision(conflict_classes=["mystery_conflict"]))


def test_validation_fails_unknown_resolution_strategy():
    with pytest.raises(ValidationError, match="unknown_resolution_strategy"):
        validate_energy_signal_conflict_decision_v1(_decision(recommended_resolution_strategy="mystery_strategy"))


def test_validation_fails_unknown_optimization_goal():
    with pytest.raises(ValidationError, match="unknown_optimization_goal"):
        validate_energy_signal_conflict_decision_v1(_decision(optimization_goal="mystery_goal"))


def test_validation_fails_action_authority_granted_true():
    with pytest.raises(ValidationError, match="action_authority_granted_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(action_authority_granted=True))


def test_validation_fails_automation_allowed_true():
    with pytest.raises(ValidationError, match="automation_allowed_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(automation_allowed=True))


def test_validation_fails_device_control_allowed_true():
    with pytest.raises(ValidationError, match="device_control_allowed_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(device_control_allowed=True))


def test_validation_fails_runtime_authority_true():
    with pytest.raises(ValidationError, match="runtime_authority_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(runtime_authority=True))


def test_validation_fails_writes_state_true():
    with pytest.raises(ValidationError, match="writes_state_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(writes_state=True))


def test_validation_fails_public_or_learning_claim():
    with pytest.raises(ValidationError, match="public_claim_allowed_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(public_claim_allowed=True))
    with pytest.raises(ValidationError, match="learning_claimed_must_be_false"):
        validate_energy_signal_conflict_decision_v1(_decision(learning_claimed=True))


def test_validation_fails_hidden_prompt_raw_private_or_secret_fields():
    payload = to_energy_signal_conflict_json_safe_v1(_decision())
    payload["hidden_prompt"] = "secret hidden prompt"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_energy_signal_conflict_decision_v1(payload)

    payload = to_energy_signal_conflict_json_safe_v1(_decision())
    payload["raw_private_data"] = "secret raw private data"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_energy_signal_conflict_decision_v1(payload)

    payload = to_energy_signal_conflict_json_safe_v1(_decision())
    payload["secret_token"] = "tok_123"
    with pytest.raises(ValidationError, match="forbidden_field_detected"):
        validate_energy_signal_conflict_decision_v1(payload)


def test_validation_fails_agi_consciousness_turing_certification_marker():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_energy_signal_conflict_decision_v1(_decision(safe_metadata={"notes": "AGI consciousness sentience Turing certification"}))


def test_validation_fails_energy_savings_guarantee():
    with pytest.raises(ValidationError, match="forbidden_claim_marker_detected"):
        validate_energy_signal_conflict_decision_v1(_decision(safe_metadata={"notes": "energy savings guarantee"}))


def test_module_does_not_import_or_call_chat_responder():
    source = Path(__file__).resolve().parents[1] / "energy_signal_conflict_resolution_policy.py"
    text = source.read_text()
    assert "chat_responder" not in text
    assert "weslr.chat_responder" not in sys.modules


def test_module_does_not_import_or_call_main():
    source = Path(__file__).resolve().parents[1] / "energy_signal_conflict_resolution_policy.py"
    text = source.read_text()
    assert "main.py" not in text
    assert "weslr.main" not in sys.modules


def test_module_does_not_import_or_call_dialogue():
    source = Path(__file__).resolve().parents[1] / "energy_signal_conflict_resolution_policy.py"
    text = source.read_text()
    assert "dialogue" not in text
    assert "dialogue" not in sys.modules


def test_module_does_not_import_or_call_chat_ui():
    source = Path(__file__).resolve().parents[1] / "energy_signal_conflict_resolution_policy.py"
    text = source.read_text()
    assert "chat_ui" not in text
    assert "chat_ui" not in sys.modules
