from __future__ import annotations

import inspect
import json
import sys

import pytest

import weslr.energy_grid_signal_intelligence as mod


def _example(example_id: str):
    return next(item for item in mod.build_initial_energy_grid_signal_intelligence_examples_v1() if item.energy_intelligence_id == example_id)


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "energy_grid_signal_intelligence_v1"
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


def test_builds_deterministic_energy_grid_intelligence_request() -> None:
    request_a = mod.build_energy_grid_intelligence_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="home_energy",
        recommendation_mode="observe_only",
        owner_operator_mode="home_owner_mode",
        optimization_goals=["minimize_cost"],
    )
    request_b = mod.build_energy_grid_intelligence_request_v1(
        request_id="req_v1",
        subject="subject_v1",
        domain="home_energy",
        recommendation_mode="observe_only",
        owner_operator_mode="home_owner_mode",
        optimization_goals=["minimize_cost"],
    )
    assert request_a == request_b
    assert request_a.safe_metadata["metadata_only"] is True


def test_builds_deterministic_energy_grid_intelligence_packet() -> None:
    request = mod.build_energy_grid_intelligence_request_v1(
        request_id="pkt_v1",
        subject="pkt_subject",
        domain="home_energy",
    )
    packet_a = mod.build_energy_grid_intelligence_packet_v1(request)
    packet_b = mod.build_energy_grid_intelligence_packet_v1(request)
    assert packet_a == packet_b
    assert packet_a.recommendation_only is True
    assert packet_a.automation_allowed is False


def test_validates_normal_packet() -> None:
    packet = mod.build_energy_grid_intelligence_packet_v1(
        mod.build_energy_grid_intelligence_request_v1(
            request_id="valid_v1",
            subject="valid_subject",
            domain="home_energy",
            signal_records=[
                mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0].signal_provenance_summary and mod._signal(
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
    assert mod.validate_energy_grid_signal_intelligence_packet_v1(packet) is True


def test_summarizes_packet() -> None:
    packet = mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0]
    summary = mod.summarize_energy_grid_signal_intelligence_packet_v1(packet)
    assert summary.summary_type == mod.SUMMARY_TYPE_V1
    assert summary.energy_intelligence_id == packet.energy_intelligence_id
    assert summary.recommendation_only is True


def test_json_safe_export_works() -> None:
    packet = mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0]
    safe = mod.to_energy_grid_signal_intelligence_json_safe_v1(packet)
    json.dumps(safe)
    assert safe["energy_intelligence_id"] == packet.energy_intelligence_id


def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_energy_grid_signal_intelligence_examples_v1()
    ids = {item.energy_intelligence_id for item in examples}
    assert len(examples) == 10
    assert "pv_surplus_forecast_support_energy_intelligence" in ids
    assert "battery_reserve_recommendation_energy_intelligence" in ids
    assert "ev_charging_deadline_support_energy_intelligence" in ids
    assert "heat_pump_preheat_scenario_energy_intelligence" in ids
    assert "price_vs_carbon_conflict_owner_decision_energy_intelligence" in ids
    assert "country_import_export_macro_context_energy_intelligence" in ids
    assert "stale_home_assistant_signal_collect_more_data_energy_intelligence" in ids
    assert "missing_owner_priority_low_confidence_energy_intelligence" in ids
    assert "dashboard_recommendation_only_energy_intelligence" in ids
    assert "blocked_device_control_request_energy_intelligence" in ids


def test_pv_surplus_example_produces_forecast_and_scenario_input_not_control() -> None:
    packet = _example("pv_surplus_forecast_support_energy_intelligence")
    assert packet.forecast_inputs
    assert packet.scenario_inputs
    assert packet.device_control_allowed is False


def test_battery_reserve_example_preserves_recommendation_only_mode() -> None:
    packet = _example("battery_reserve_recommendation_energy_intelligence")
    assert packet.recommendation_only is True
    assert packet.recommendation_mode == "owner_decision_support"


def test_ev_deadline_example_surfaces_deadline_constraints() -> None:
    packet = _example("ev_charging_deadline_support_energy_intelligence")
    assert packet.deadline_constraints
    assert "departure_time" in packet.deadline_constraints or "departure_time" in packet.recommended_next_step or packet.recommendation_mode == "owner_decision_support"


def test_heat_pump_example_branches_comfort_cost_scenarios() -> None:
    packet = _example("heat_pump_preheat_scenario_energy_intelligence")
    assert packet.scenario_inputs
    assert packet.comfort_constraints
    assert packet.optimization_goals


def test_price_vs_carbon_example_exposes_conflict() -> None:
    packet = _example("price_vs_carbon_conflict_owner_decision_energy_intelligence")
    assert packet.conflict_summary["conflict_classes"]
    assert packet.conflict_summary["scenario_branch_required"] is True or packet.owner_priorities


def test_country_import_export_example_is_macro_context_only() -> None:
    packet = _example("country_import_export_macro_context_energy_intelligence")
    assert packet.grid_context_summary["context_kind"] == "macro_context"
    assert packet.location_scope == "macro_context"


def test_stale_ha_signal_example_collects_more_data() -> None:
    packet = _example("stale_home_assistant_signal_collect_more_data_energy_intelligence")
    assert packet.recommendation_mode == "collect_more_data"
    assert packet.missing_signals


def test_missing_owner_priority_lowers_confidence() -> None:
    packet = _example("missing_owner_priority_low_confidence_energy_intelligence")
    assert packet.confidence_label in {"low_confidence", "blocked_insufficient_evidence", "unknown_confidence"}


def test_dashboard_recommendation_does_not_create_dashboard() -> None:
    packet = _example("dashboard_recommendation_only_energy_intelligence")
    assert packet.recommendation_mode == "dashboard_recommendation"
    assert packet.recommendation_only is True


def test_blocked_device_control_request_blocks_control() -> None:
    packet = _example("blocked_device_control_request_energy_intelligence")
    assert packet.recommendation_mode == "blocked_control_request"
    assert packet.device_control_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_grants_automation(packet) -> None:
    assert packet.automation_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_grants_device_control(packet) -> None:
    assert packet.device_control_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_has_runtime_authority(packet) -> None:
    assert packet.runtime_authority is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_writes_state(packet) -> None:
    assert packet.writes_state is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_calls_model_provider(packet) -> None:
    assert packet.model_provider_used is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_allows_public_claim(packet) -> None:
    assert packet.public_claim_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_claims_energy_savings(packet) -> None:
    assert packet.energy_savings_claimed is False


@pytest.mark.parametrize("packet", mod.build_initial_energy_grid_signal_intelligence_examples_v1())
def test_no_initial_example_claims_prediction_certainty(packet) -> None:
    assert packet.prediction_certainty_claimed is False


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("domain", "unknown_space", "unknown_energy_signal_domain"),
    ("recommendation_mode", "totally_ready", "unknown_recommendation_mode"),
    ("owner_operator_mode", "unknown_operator", "unknown_owner_operator_mode"),
    ("confidence_label", "super_confident", "unknown_confidence"),
    ("uncertainty_label", "foggy", "unknown_uncertainty"),
])
def test_validation_fails_unknown_labels(field_name: str, field_value: str, expected_error: str) -> None:
    packet = mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0]
    payload = mod.to_energy_grid_signal_intelligence_json_safe_v1(packet)
    payload[field_name] = field_value
    mutated = mod.EnergyGridSignalIntelligencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_energy_grid_signal_intelligence_packet_v1(mutated)


@pytest.mark.parametrize("field_name, expected_error", [
    ("automation_allowed", "automation_allowed_true"),
    ("device_control_allowed", "device_control_allowed_true"),
    ("runtime_authority", "runtime_authority_true"),
    ("writes_state", "writes_state_true"),
    ("public_claim_allowed", "public_claim_allowed_true"),
    ("energy_savings_claimed", "energy_savings_claimed_true"),
    ("prediction_certainty_claimed", "prediction_certainty_claimed_true"),
    ("learning_claimed", "learning_claimed_true"),
])
def test_validation_fails_forbidden_authority_flags(field_name: str, expected_error: str) -> None:
    packet = mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0]
    payload = mod.to_energy_grid_signal_intelligence_json_safe_v1(packet)
    payload[field_name] = True
    mutated = mod.EnergyGridSignalIntelligencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_energy_grid_signal_intelligence_packet_v1(mutated)


@pytest.mark.parametrize("bad_payload", [
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
    {"safe_metadata": {"claim": "safety guarantee"}},
    {"safe_metadata": {"claim": "carbon optimization correctness guarantee"}},
    {"safe_metadata": {"claim": "energy savings guarantee"}},
])
def test_validation_fails_hidden_prompt_raw_private_secret_and_claim_markers(bad_payload: dict[str, dict[str, str]]) -> None:
    payload = mod.to_energy_grid_signal_intelligence_json_safe_v1(mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], **bad_payload["safe_metadata"]}
    mutated = mod.EnergyGridSignalIntelligencePacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_energy_grid_signal_intelligence_packet_v1(mutated)


@pytest.mark.parametrize("marker", ["AGI", "consciousness", "sentience", "Turing", "certification"])
def test_validation_fails_agi_consciousness_turing_certification_marker(marker: str) -> None:
    payload = mod.to_energy_grid_signal_intelligence_json_safe_v1(mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": marker}
    mutated = mod.EnergyGridSignalIntelligencePacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_energy_grid_signal_intelligence_packet_v1(mutated)


@pytest.mark.parametrize("claim", ["public readiness", "safety guarantee", "carbon optimization correctness guarantee", "energy savings guarantee"])
def test_validation_fails_claim_guarantees(claim: str) -> None:
    payload = mod.to_energy_grid_signal_intelligence_json_safe_v1(mod.build_initial_energy_grid_signal_intelligence_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": claim}
    mutated = mod.EnergyGridSignalIntelligencePacket(**payload)
    with pytest.raises(mod.ValidationError):
        mod.validate_energy_grid_signal_intelligence_packet_v1(mutated)
