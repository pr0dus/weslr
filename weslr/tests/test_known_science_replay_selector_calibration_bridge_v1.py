from __future__ import annotations

import json
from copy import deepcopy

import pytest

import weslr.known_science_replay_helpers as ksr
import weslr.known_science_replay_selector_calibration_bridge as bridge

BASE_CASES_V1 = {case["case_id"]: case for case in ksr.build_initial_known_science_replay_examples_v1()}
PULSAR_CASE_V1 = deepcopy(BASE_CASES_V1["pulsar_discovery_replay"])


def _phase(case_id: str, phase_name: str):
    for phase in BASE_CASES_V1[case_id]["replay_phases"]:
        if phase["phase_name"] == phase_name:
            return deepcopy(phase)
    raise AssertionError(f"missing phase: {case_id}:{phase_name}")


def _payload(case_id: str, phase_name: str, **overrides):
    case = deepcopy(BASE_CASES_V1[case_id])
    phase = _phase(case_id, phase_name)
    payload = {
        "bridge_id": f"{case_id}:{phase['phase_id']}:bridge",
        "replay_case": case,
        "replay_phase": phase,
        "source_replay_case_id": case["case_id"],
        "source_known_outcome": case["known_outcome"],
        "source_case_domain": case["domain"],
        "replay_phase_id": phase["phase_id"],
        "replay_phase_summary": phase.get("historical_signal_summary") or phase.get("safe_interpretation"),
        "expected_internal_next_step": phase.get("expected_internal_next_step") or phase.get("expected_selector_outcome"),
        "selector_input_metadata": {
            "bridge_family": "known_science_replay_selector_calibration",
            "case_title": case["case_title"],
            "phase_name": phase.get("phase_name"),
            "phase_order": phase.get("phase_order"),
        },
        "selector_selected_next_step": phase.get("expected_internal_next_step") or phase.get("expected_selector_outcome"),
        "selector_selection_reason": "matches the expected internal next step",
        "forbidden_interpretations": phase.get("forbidden_interpretations") or case.get("forbidden_interpretations", []),
        "authority_status": bridge._default_authority_status(),
        "safe_metadata": bridge._default_safe_metadata(),
    }
    payload.update(overrides)
    return payload


def _packet(case_id: str, phase_name: str, **overrides):
    return bridge.build_known_science_replay_selector_bridge_packet_v1(_payload(case_id, phase_name, **overrides))


def test_public_apis_exist() -> None:
    for name in (
        "build_known_science_replay_selector_bridge_input_v1",
        "build_known_science_replay_selector_bridge_packet_v1",
        "compare_known_science_replay_selector_step_v1",
        "validate_known_science_replay_selector_bridge_packet_v1",
        "summarize_known_science_replay_selector_bridge_packet_v1",
        "to_known_science_replay_selector_bridge_json_safe_v1",
        "build_initial_known_science_replay_selector_bridge_examples_v1",
    ):
        assert hasattr(bridge, name)


def test_initial_examples_build_and_validate() -> None:
    examples = bridge.build_initial_known_science_replay_selector_bridge_examples_v1()
    assert len(examples) == 9
    assert {example["source_replay_case_id"] for example in examples} == {
        "pulsar_discovery_replay",
        "continental_drift_replay",
        "penicillin_contamination_replay",
        "cosmic_microwave_background_replay",
        "helicobacter_pylori_ulcer_replay",
    }

    unsafe_example = next(example for example in examples if example["replay_phase_id"].endswith(":unsafe_public_claim_attempt"))
    assert unsafe_example["alignment_status"] == "blocked_by_safety"
    assert unsafe_example["mismatch_type"] == "none"

    for example in examples:
        validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(example)
        assert validation["valid"]
        assert json.dumps(bridge.to_known_science_replay_selector_bridge_json_safe_v1(example))


def test_exact_match_aligns() -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert validation["valid"]
    assert packet["alignment_status"] == "aligned"
    assert packet["mismatch_type"] == "none"


def test_multiple_expected_safe_steps_align() -> None:
    packet = bridge.build_known_science_replay_selector_bridge_packet_v1(
        {
            "bridge_id": "multi-step-bridge",
            "source_replay_case_id": "pulsar_discovery_replay",
            "source_known_outcome": PULSAR_CASE_V1["known_outcome"],
            "source_case_domain": PULSAR_CASE_V1["domain"],
            "replay_phase_id": PULSAR_CASE_V1["replay_phases"][0]["phase_id"],
            "replay_phase_summary": PULSAR_CASE_V1["replay_phases"][0]["historical_signal_summary"],
            "expected_internal_next_steps": ["probe", "pressure_test"],
            "selector_input_metadata": {"bridge_family": "known_science_replay_selector_calibration"},
            "selector_selected_next_step": "pressure_test",
            "selector_selection_reason": "one of the safe expected steps",
            "forbidden_interpretations": ["discovery", "proof"],
            "authority_status": bridge._default_authority_status(),
            "safe_metadata": bridge._default_safe_metadata(),
        }
    )

    assert packet["alignment_status"] == "aligned"
    assert packet["mismatch_type"] == "none"
    assert bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)["valid"]


@pytest.mark.parametrize(
    ("phase_name", "selected", "expected_status", "expected_mismatch"),
    [
        ("initial_strange_signal", "calibrate", "mismatch", "premature_calibration"),
        ("initial_strange_signal", "archive", "mismatch", "premature_archive"),
        ("repeated_precise_signal", "calibrate", "mismatch", "missed_pressure_test"),
        ("ordinary_explanations_weakened", "watch", "partially_aligned", "over_cautious"),
        ("ordinary_explanations_weakened", "probe", "mismatch", "over_cautious"),
    ],
)
def test_alignment_and_mismatch_logic(phase_name, selected, expected_status, expected_mismatch) -> None:
    packet = _packet("pulsar_discovery_replay", phase_name, selector_selected_next_step=selected)

    assert packet["alignment_status"] == expected_status
    assert packet["mismatch_type"] == expected_mismatch
    assert bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)["valid"]


@pytest.mark.parametrize(
    "metadata_value",
    [
        {"case_title": "historical discovery replay"},
        {"case_title": "pulsar discovery replay"},
    ],
)
def test_neutral_selector_input_metadata_with_discovery_validates(metadata_value) -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["selector_input_metadata"] = metadata_value

    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert validation["valid"]
    assert json.dumps(bridge.to_known_science_replay_selector_bridge_json_safe_v1(packet))


def test_forbidden_interpretations_with_discovery_claim_remain_a_warning_boundary() -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["forbidden_interpretations"] = ["discovery claim"]

    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert validation["valid"]


@pytest.mark.parametrize(
    ("bad_text", "expected_label"),
    [
        ("WESLR discovered pulsars", "forbidden_claim_language"),
        ("proof of discovery", "forbidden_claim_language"),
        ("validated scientific result", "forbidden_claim_language"),
    ],
)
def test_validation_fail_closed_on_live_claim_language(bad_text, expected_label) -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["selector_selection_reason"] = bad_text
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


def test_unsafe_public_claim_attempt_blocks_safely() -> None:
    packet = _packet("pulsar_discovery_replay", "unsafe_public_claim_attempt", selector_selected_next_step="blocked")

    assert packet["alignment_status"] == "blocked_by_safety"
    assert packet["mismatch_type"] == "none"
    assert bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)["valid"]


def test_unknown_case_or_phase_is_not_applicable() -> None:
    comparison = bridge.compare_known_science_replay_selector_step_v1(
        {
            "bridge_id": "unknown-case-bridge",
            "source_replay_case_id": "unknown_case",
            "source_known_outcome": "unknown outcome",
            "source_case_domain": "unknown domain",
            "replay_phase_id": "unknown_phase",
            "replay_phase_summary": "unknown phase",
            "expected_internal_next_step": "probe",
            "selector_input_metadata": {"bridge_family": "known_science_replay_selector_calibration"},
            "selector_selected_next_step": "probe",
            "selector_selection_reason": "unknown case comparison",
            "forbidden_interpretations": ["discovery"],
            "authority_status": bridge._default_authority_status(),
            "safe_metadata": bridge._default_safe_metadata(),
        }
    )

    assert comparison["alignment_status"] == "not_applicable"
    assert comparison["mismatch_type"] == "unknown_case"


def test_summarize_and_json_safe_export() -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    summary = bridge.summarize_known_science_replay_selector_bridge_packet_v1(packet)

    assert summary["alignment_status"] == "aligned"
    assert "Known-science replay selector bridge" in summary["summary_text"]
    assert json.dumps(bridge.to_known_science_replay_selector_bridge_json_safe_v1(packet))


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("bridge_id", "", "missing_bridge_id"),
        ("source_replay_case_id", "", "missing_replay_case_id"),
        ("expected_internal_next_step", "", "missing_expected_internal_next_step"),
        ("selector_selected_next_step", "", "missing_selector_selected_next_step"),
        ("alignment_notes", [], "missing_alignment_notes"),
        ("alignment_status", "not-a-status", "invalid_alignment_status"),
        ("mismatch_type", "not-a-mismatch", "invalid_mismatch_type"),
    ],
)
def test_validation_fail_closed_on_required_fields_and_enums(field, value, expected_label) -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet[field] = value
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("field", "value", "expected_label"),
    [
        ("runtime_action_authorized", True, "unsafe_runtime_action_authorized"),
        ("storage_write_authorized", True, "unsafe_storage_write_authorized"),
        ("memory_mutation_authorized", True, "unsafe_memory_mutation_authorized"),
        ("project_mutation_authorized", True, "unsafe_project_mutation_authorized"),
        ("behavior_promotion_authorized", True, "unsafe_behavior_promotion_authorized"),
        ("public_claim_authorized", True, "unsafe_public_claim_authorized"),
        ("final_answer_authority", True, "unsafe_final_answer_authority"),
        ("provider_model_call_authority", True, "unsafe_provider_model_call_authority"),
        ("tool_execution_authority", True, "unsafe_tool_execution_authority"),
        ("retrieval_tool_authority", True, "unsafe_retrieval_tool_authority"),
    ],
)
def test_validation_fail_closed_on_unsafe_authority(field, value, expected_label) -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["authority_status"][field] = value
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    ("bad_text", "expected_label"),
    [
        ("discovery proof breakthrough scientific result", "forbidden_claim_language"),
        ("hidden prompt secret", "forbidden_private_text"),
        ("provider call tool execution retrieval call runtime", "forbidden_runtime_or_tool_language"),
        (".weslr protected private text", "forbidden_private_text"),
        ("final answer authority", "forbidden_claim_language"),
    ],
)
def test_validation_fail_closed_on_forbidden_language(bad_text, expected_label) -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["selector_selection_reason"] = bad_text
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert not validation["valid"]
    assert expected_label in validation["blocked_labels"]


def test_validation_fail_closed_on_non_json_safe_nested_value_and_json_safe_helper_recovers() -> None:
    packet = _packet("pulsar_discovery_replay", "initial_strange_signal", selector_selected_next_step="probe")
    packet["selector_input_metadata"] = {"unsafe": {1, 2}}
    validation = bridge.validate_known_science_replay_selector_bridge_packet_v1(packet)

    assert not validation["valid"]
    assert "non_json_safe_result_structure" in validation["blocked_labels"]

    safe = bridge.to_known_science_replay_selector_bridge_json_safe_v1(packet)
    assert json.dumps(safe)
    assert safe["selector_input_metadata"]["unsafe"] == [1, 2]
