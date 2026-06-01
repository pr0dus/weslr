from __future__ import annotations

import inspect
import json
import sys

import pytest

import weslr.future_state_forecasting_engine as mod


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "future_state_forecasting_engine_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_module_does_not_reference_protected_runtime_files() -> None:
    source = inspect.getsource(mod)
    assert "chat_responder.py" not in source
    assert "weslr.chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source


def test_builds_deterministic_forecast_request() -> None:
    request_a = mod.build_future_state_forecast_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="weslr_project_forecast",
        forecast_horizon="immediate",
        assumptions=["a", "b"],
        known_constraints=["c"],
        missing_inputs=[],
    )
    request_b = mod.build_future_state_forecast_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="weslr_project_forecast",
        forecast_horizon="immediate",
        assumptions=["a", "b"],
        known_constraints=["c"],
        missing_inputs=[],
    )
    assert request_a == request_b
    assert request_a.safe_metadata["metadata_only"] is True


def test_builds_deterministic_forecast_packet() -> None:
    request = mod.build_future_state_forecast_request_v1(
        request_id="pkt_v1",
        subject="pkt_subject",
        domain="weslr_project_forecast",
        forecast_horizon="immediate",
    )
    packet_a = mod.build_future_state_forecast_packet_v1(request)
    packet_b = mod.build_future_state_forecast_packet_v1(request)
    assert packet_a == packet_b
    assert packet_a.recommendation_only is True
    assert packet_a.action_authority_granted is False


def test_validates_normal_forecast_packet() -> None:
    packet = mod.build_future_state_forecast_packet_v1(
        mod.build_future_state_forecast_request_v1(
            request_id="valid_v1",
            subject="valid_subject",
            domain="energy_home_forecast",
            forecast_horizon="short_term",
            signal_records=[
                mod.build_signal_provenance_record_v1(
                    signal_provenance_id="sig_valid_v1",
                    signal_id="sig_valid",
                    signal_name="Valid Signal",
                    signal_class="home_assistant_entity",
                    source_system="home_assistant",
                    source_provider="local_entity",
                    source_reference="sensor.valid",
                    source_url_or_entity_id="sensor.valid",
                )
            ],
        )
    )
    assert mod.validate_future_state_forecast_packet_v1(packet) is True


def test_summarizes_forecast_packet() -> None:
    packet = mod.build_initial_future_state_forecast_examples_v1()[0]
    summary = mod.summarize_future_state_forecast_packet_v1(packet)
    assert summary.summary_type == mod.SUMMARY_TYPE_V1
    assert summary.forecast_id == packet.forecast_id
    assert summary.recommendation_only is True


def test_json_safe_export_works() -> None:
    packet = mod.build_initial_future_state_forecast_examples_v1()[0]
    safe = mod.to_future_state_forecast_json_safe_v1(packet)
    json.dumps(safe)
    assert safe["forecast_id"] == packet.forecast_id


def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_future_state_forecast_examples_v1()
    ids = {item.forecast_id for item in examples}
    assert len(examples) == 10
    assert "next_lane_forecast_capability_registry_to_implementation_wave_forecast" in ids
    assert "energy_evening_grid_import_risk_with_fresh_signals_forecast" in ids
    assert "pv_surplus_likelihood_with_weather_uncertainty_forecast" in ids
    assert "battery_reserve_depletion_risk_with_stale_soc_blocked_forecast" in ids
    assert "ev_deadline_risk_missing_departure_time_forecast" in ids
    assert "price_vs_carbon_conflict_requires_scenario_branch_forecast" in ids
    assert "artifact_build_forecast_missing_validation_runner_forecast" in ids
    assert "public_pilot_forecast_blocked_claim_lifecycle_missing_forecast" in ids
    assert "wifi_rf_research_forecast_blocked_privacy_boundary_missing_forecast" in ids
    assert "tri_engine_orchestration_forecast_preserved_for_runtime_later_forecast" in ids


def test_energy_fresh_signal_forecast_is_ready_or_uncertain() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "energy_evening_grid_import_risk_with_fresh_signals_forecast")
    assert packet.forecast_status in {"forecast_ready", "forecast_ready_with_uncertainty"}


def test_stale_signal_forecast_is_blocked_or_low_confidence() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "battery_reserve_depletion_risk_with_stale_soc_blocked_forecast")
    assert packet.forecast_status == "blocked_stale_signal" or packet.confidence_label == "low_confidence"


def test_conflicting_signal_forecast_requires_scenario_branch() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "price_vs_carbon_conflict_requires_scenario_branch_forecast")
    assert packet.forecast_status == "scenario_branch_required"


def test_missing_input_forecast_records_missing_inputs() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "ev_deadline_risk_missing_departure_time_forecast")
    assert packet.missing_inputs == ["departure_time"]
    assert packet.forecast_status == "blocked_missing_signal"


def test_public_pilot_forecast_is_blocked_by_missing_claim_lifecycle() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "public_pilot_forecast_blocked_claim_lifecycle_missing_forecast")
    assert packet.forecast_status in {"blocked_missing_signal", "blocked_authority_boundary"}


def test_artifact_build_forecast_records_missing_validation_runner() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "artifact_build_forecast_missing_validation_runner_forecast")
    assert "validation_runner" in packet.missing_inputs


def test_tri_engine_orchestration_forecast_preserves_later_runtime_boundary() -> None:
    packet = next(item for item in mod.build_initial_future_state_forecast_examples_v1() if item.forecast_id == "tri_engine_orchestration_forecast_preserved_for_runtime_later_forecast")
    assert packet.runtime_authority is False
    assert packet.recommended_next_lane == "IMPLEMENT_WESLR_FUTURE_STATE_FORECASTING_ENGINE_V1"


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_grants_action_authority(packet) -> None:
    assert packet.action_authority_granted is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_allows_automation(packet) -> None:
    assert packet.automation_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_allows_device_control(packet) -> None:
    assert packet.device_control_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_has_runtime_authority(packet) -> None:
    assert packet.runtime_authority is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_writes_state(packet) -> None:
    assert packet.writes_state is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_claims_prediction_certainty(packet) -> None:
    assert packet.prediction_certainty_claimed is False


@pytest.mark.parametrize("packet", mod.build_initial_future_state_forecast_examples_v1())
def test_no_initial_example_claims_autonomous_learning(packet) -> None:
    assert packet.learning_claimed is False


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_error"),
    [
        ("domain", "unknown_space", "unknown_domain"),
        ("forecast_horizon", "epic", "unknown_horizon"),
        ("confidence_label", "super_confident", "unknown_confidence"),
        ("uncertainty_label", "foggy", "unknown_uncertainty"),
        ("forecast_status", "totally_ready", "unknown_status"),
    ],
)
def test_validation_fails_unknown_labels(field_name: str, field_value: str, expected_error: str) -> None:
    packet = mod.build_initial_future_state_forecast_examples_v1()[0]
    mutated = mod.FutureStateForecastPacket(**{**mod.to_future_state_forecast_json_safe_v1(packet), field_name: field_value})
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_future_state_forecast_packet_v1(mutated)


@pytest.mark.parametrize(
    ("field_name", "expected_error"),
    [
        ("action_authority_granted", "action_authority_granted_true"),
        ("automation_allowed", "automation_allowed_true"),
        ("device_control_allowed", "device_control_allowed_true"),
        ("runtime_authority", "runtime_authority_true"),
        ("writes_state", "writes_state_true"),
        ("model_provider_used", "model_provider_used_true"),
        ("public_claim_allowed", "public_claim_allowed_true"),
        ("prediction_certainty_claimed", "prediction_certainty_claimed_true"),
        ("learning_claimed", "learning_claimed_true"),
    ],
)
def test_validation_fails_forbidden_authority_flags(field_name: str, expected_error: str) -> None:
    packet = mod.build_initial_future_state_forecast_examples_v1()[0]
    payload = mod.to_future_state_forecast_json_safe_v1(packet)
    payload[field_name] = True
    mutated = mod.FutureStateForecastPacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_future_state_forecast_packet_v1(mutated)


@pytest.mark.parametrize(
    "bad_payload",
    [
        {"safe_metadata": {"hidden_prompt": "x"}},
        {"safe_metadata": {"raw_private": "x"}},
        {"safe_metadata": {"secret": "x"}},
        {"safe_metadata": {"token": "x"}},
        {"safe_metadata": {"api_key": "x"}},
        {"safe_metadata": {"credential": "x"}},
        {"safe_metadata": {"password": "x"}},
        {"safe_metadata": {"claim": "AGI"}},
        {"safe_metadata": {"claim": "consciousness"}},
        {"safe_metadata": {"claim": "sentience"}},
        {"safe_metadata": {"claim": "Turing"}},
        {"safe_metadata": {"claim": "certification"}},
        {"safe_metadata": {"claim": "public readiness"}},
        {"safe_metadata": {"claim": "energy savings guarantee"}},
        {"safe_metadata": {"claim": "autonomous learning"}},
        {"safe_metadata": {"claim": "prediction certainty"}},
    ],
)
def test_validation_fails_hidden_prompt_raw_private_secret_and_claim_markers(bad_payload: dict[str, dict[str, str]]) -> None:
    payload = mod.to_future_state_forecast_json_safe_v1(mod.build_initial_future_state_forecast_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], **bad_payload["safe_metadata"]}
    mutated = mod.FutureStateForecastPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_future_state_forecast_packet_v1(mutated)


@pytest.mark.parametrize("marker", ["AGI", "consciousness", "sentience", "Turing", "certification"])
def test_validation_fails_agi_consciousness_turing_certification_marker(marker: str) -> None:
    payload = mod.to_future_state_forecast_json_safe_v1(mod.build_initial_future_state_forecast_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": marker}
    mutated = mod.FutureStateForecastPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_future_state_forecast_packet_v1(mutated)


@pytest.mark.parametrize("claim", ["public readiness", "energy savings guarantee", "autonomous learning"])
def test_validation_fails_public_readiness_and_energy_savings_and_autonomous_learning_claims(claim: str) -> None:
    payload = mod.to_future_state_forecast_json_safe_v1(mod.build_initial_future_state_forecast_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": claim}
    mutated = mod.FutureStateForecastPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_future_state_forecast_packet_v1(mutated)
