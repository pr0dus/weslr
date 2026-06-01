from __future__ import annotations

import inspect
import json
import sys

import pytest

import weslr.scenario_simulation_engine as mod


def _example(example_id: str):
    return next(item for item in mod.build_initial_scenario_simulation_examples_v1() if item.scenario_simulation_id == example_id)


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "scenario_simulation_engine_v1"
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


def test_builds_deterministic_scenario_simulation_request() -> None:
    request_a = mod.build_scenario_simulation_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="weslr_project_scenario",
        assumptions=["a"],
        known_constraints=["b"],
    )
    request_b = mod.build_scenario_simulation_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="weslr_project_scenario",
        assumptions=["a"],
        known_constraints=["b"],
    )
    assert request_a == request_b
    assert request_a.safe_metadata["metadata_only"] is True


def test_builds_deterministic_scenario_simulation_packet() -> None:
    request = mod.build_scenario_simulation_request_v1(
        request_id="pkt_v1",
        subject="pkt_subject",
        domain="weslr_project_scenario",
    )
    packet_a = mod.build_scenario_simulation_packet_v1(request)
    packet_b = mod.build_scenario_simulation_packet_v1(request)
    assert packet_a == packet_b
    assert packet_a.recommendation_only is True
    assert packet_a.action_authority_granted is False


def test_validates_normal_simulation_packet() -> None:
    packet = mod.build_scenario_simulation_packet_v1(
        mod.build_scenario_simulation_request_v1(
            request_id="valid_v1",
            subject="valid_subject",
            domain="energy_home_scenario",
            forecast_packets=[mod.build_initial_future_state_forecast_examples_v1()[1]],
        )
    )
    assert mod.validate_scenario_simulation_packet_v1(packet) is True


def test_summarizes_simulation_packet() -> None:
    packet = mod.build_initial_scenario_simulation_examples_v1()[0]
    summary = mod.summarize_scenario_simulation_packet_v1(packet)
    assert summary.summary_type == mod.SUMMARY_TYPE_V1
    assert summary.scenario_simulation_id == packet.scenario_simulation_id
    assert summary.branch_count == packet.branch_count


def test_json_safe_export_works() -> None:
    packet = mod.build_initial_scenario_simulation_examples_v1()[0]
    safe = mod.to_scenario_simulation_json_safe_v1(packet)
    json.dumps(safe)
    assert safe["scenario_simulation_id"] == packet.scenario_simulation_id


def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_scenario_simulation_examples_v1()
    ids = {item.scenario_simulation_id for item in examples}
    assert len(examples) == 10
    assert "energy_price_vs_carbon_three_branches_scenario" in ids
    assert "pv_surplus_sunny_vs_cloudy_branches_scenario" in ids
    assert "battery_reserve_wait_and_observe_stale_soc_scenario" in ids
    assert "ev_deadline_first_branch_missing_departure_time_scenario" in ids
    assert "heat_pump_comfort_first_vs_cost_branch_scenario" in ids
    assert "artifact_build_validation_runner_missing_blocked_branch_scenario" in ids
    assert "public_pilot_claim_lifecycle_missing_blocked_branch_scenario" in ids
    assert "wifi_rf_privacy_boundary_missing_blocked_branch_scenario" in ids
    assert "tri_engine_runtime_later_orchestration_branch_scenario" in ids
    assert "implementation_wave_continue_future_forecast_to_scenario_scenario" in ids


def test_price_vs_carbon_scenario_creates_multiple_branches() -> None:
    packet = _example("energy_price_vs_carbon_three_branches_scenario")
    assert packet.branch_count >= 3
    assert {b["branch_label"] for b in packet.scenario_branches} >= {"baseline_branch", "cost_optimized_branch", "carbon_optimized_branch"}


def test_pv_weather_uncertainty_creates_sunny_cloudy_branches() -> None:
    packet = _example("pv_surplus_sunny_vs_cloudy_branches_scenario")
    assert packet.branch_count >= 2
    labels = {b["branch_label"] for b in packet.scenario_branches}
    assert labels >= {"optimistic_branch", "conservative_branch"}


def test_stale_soc_creates_wait_observe_or_blocked_branch() -> None:
    packet = _example("battery_reserve_wait_and_observe_stale_soc_scenario")
    labels = {b["branch_label"] for b in packet.scenario_branches}
    assert "wait_and_observe_branch" in labels or "blocked_branch" in labels
    assert packet.scenario_status in {"blocked_stale_signal", "blocked_missing_input", "branching_required"}


def test_missing_ev_departure_time_records_missing_input() -> None:
    packet = _example("ev_deadline_first_branch_missing_departure_time_scenario")
    assert "departure_time" in packet.missing_inputs


def test_artifact_build_scenario_blocks_on_validation_runner_missing() -> None:
    packet = _example("artifact_build_validation_runner_missing_blocked_branch_scenario")
    assert "validation_runner" in packet.missing_inputs
    assert "blocked_branch" in {b["branch_label"] for b in packet.scenario_branches}


def test_public_pilot_scenario_blocks_on_claim_lifecycle_missing() -> None:
    packet = _example("public_pilot_claim_lifecycle_missing_blocked_branch_scenario")
    assert packet.domain == "product_market_scenario"
    assert "blocked_branch" in {b["branch_label"] for b in packet.scenario_branches}


def test_wifi_rf_scenario_blocks_on_privacy_boundary_missing() -> None:
    packet = _example("wifi_rf_privacy_boundary_missing_blocked_branch_scenario")
    assert packet.domain == "wifi_rf_sensing_scenario"
    assert "blocked_branch" in {b["branch_label"] for b in packet.scenario_branches}


def test_tri_engine_scenario_preserves_orchestration_for_later_runtime() -> None:
    packet = _example("tri_engine_runtime_later_orchestration_branch_scenario")
    assert packet.recommended_next_lane == "DESIGN_WESLR_TRI_ENGINE_ORCHESTRATION_BOUNDARY_V1"
    assert packet.runtime_authority is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_grants_action_authority(packet) -> None:
    assert packet.action_authority_granted is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_allows_automation(packet) -> None:
    assert packet.automation_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_allows_device_control(packet) -> None:
    assert packet.device_control_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_has_runtime_authority(packet) -> None:
    assert packet.runtime_authority is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_writes_state(packet) -> None:
    assert packet.writes_state is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_claims_prediction_certainty(packet) -> None:
    assert packet.prediction_certainty_claimed is False


@pytest.mark.parametrize("packet", mod.build_initial_scenario_simulation_examples_v1())
def test_no_initial_example_claims_autonomous_learning(packet) -> None:
    assert packet.learning_claimed is False


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_error"),
    [
        ("domain", "unknown_space", "unknown_domain"),
        ("scenario_status", "totally_ready", "unknown_status"),
        ("scenario_branches", [{"branch_label": "nope", "reversibility": "reversible"}], "unknown_branch_label"),
        ("scenario_branches", [{"branch_label": "baseline_branch", "reversibility": "wild"}], "unknown_reversibility"),
    ],
)
def test_validation_fails_unknown_scenario_labels(field_name: str, field_value, expected_error: str) -> None:
    packet = mod.build_initial_scenario_simulation_examples_v1()[0]
    payload = mod.to_scenario_simulation_json_safe_v1(packet)
    payload[field_name] = field_value
    mutated = mod.ScenarioSimulationPacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_scenario_simulation_packet_v1(mutated)


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
    packet = mod.build_initial_scenario_simulation_examples_v1()[0]
    payload = mod.to_scenario_simulation_json_safe_v1(packet)
    payload[field_name] = True
    mutated = mod.ScenarioSimulationPacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_scenario_simulation_packet_v1(mutated)


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
    payload = mod.to_scenario_simulation_json_safe_v1(mod.build_initial_scenario_simulation_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], **bad_payload["safe_metadata"]}
    mutated = mod.ScenarioSimulationPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_scenario_simulation_packet_v1(mutated)


@pytest.mark.parametrize("marker", ["AGI", "consciousness", "sentience", "Turing", "certification"])
def test_validation_fails_agi_consciousness_turing_certification_marker(marker: str) -> None:
    payload = mod.to_scenario_simulation_json_safe_v1(mod.build_initial_scenario_simulation_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": marker}
    mutated = mod.ScenarioSimulationPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_scenario_simulation_packet_v1(mutated)


@pytest.mark.parametrize("claim", ["public readiness", "energy savings guarantee", "autonomous learning"])
def test_validation_fails_public_readiness_and_energy_savings_and_autonomous_learning_claims(claim: str) -> None:
    payload = mod.to_scenario_simulation_json_safe_v1(mod.build_initial_scenario_simulation_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": claim}
    mutated = mod.ScenarioSimulationPacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_scenario_simulation_packet_v1(mutated)
