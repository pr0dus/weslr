from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

from weslr import rf_field_discovery_schema_helpers as mod

EXPECTED_BUILDERS = [
    mod.build_rf_discovery_environment_candidate_v1,
    mod.build_rf_discovery_anchor_candidate_v1,
    mod.build_rf_discovery_signal_observation_candidate_v1,
    mod.build_rf_discovery_baseline_candidate_v1,
    mod.build_rf_discovery_pattern_candidate_v1,
    mod.build_rf_discovery_strange_signal_candidate_v1,
    mod.build_rf_discovery_calibration_experiment_candidate_v1,
    mod.build_rf_discovery_visualization_frame_candidate_v1,
    mod.build_rf_discovery_decision_outcome_candidate_v1,
    mod.build_rf_discovery_value_assessment_candidate_v1,
]

PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


@pytest.mark.parametrize("builder", EXPECTED_BUILDERS)
def test_builders_return_valid_packets(builder):
    packet = builder()
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)
    assert packet["schema_version"] == mod.SCHEMA_VERSION_V1
    assert packet["raw_signal_included"] is False
    assert packet["live_sensing_performed"] is False
    assert packet["router_access_performed"] is False
    assert packet["packet_capture_performed"] is False
    assert packet["csi_collection_performed"] is False
    assert packet["runtime_wiring_performed"] is False


@pytest.mark.parametrize("field_name", [
    "packet_type",
    "schema_version",
    "missing_fields",
    "confidence",
    "notes",
    "raw_signal_included",
    "live_sensing_performed",
    "router_access_performed",
    "packet_capture_performed",
    "csi_collection_performed",
    "runtime_wiring_performed",
])
def test_missing_required_fields_fail_closed(field_name):
    packet = mod.build_rf_discovery_environment_candidate_v1()
    packet.pop(field_name)
    assert mod.validate_rf_discovery_candidate_packet_v1(packet) is False


@pytest.mark.parametrize("field_name", [
    "raw_signal_included",
    "live_sensing_performed",
    "router_access_performed",
    "packet_capture_performed",
    "csi_collection_performed",
    "runtime_wiring_performed",
])
def test_forbidden_live_flags_fail_closed(field_name):
    packet = mod.build_rf_discovery_environment_candidate_v1()
    packet[field_name] = True
    assert mod.validate_rf_discovery_candidate_packet_v1(packet) is False


def test_unknown_packet_type_fails_closed():
    packet = mod.build_rf_discovery_environment_candidate_v1()
    packet["packet_type"] = "unknown_type"
    assert mod.validate_rf_discovery_candidate_packet_v1(packet) is False


def test_csi_fields_can_be_absent():
    packet = mod.build_rf_discovery_signal_observation_candidate_v1()
    packet.pop("csi_amplitude", None)
    packet.pop("csi_phase", None)
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


def test_missing_fields_are_preserved():
    packet = mod.build_rf_discovery_environment_candidate_v1(missing_fields=["exact_geometry", "material_details"])
    assert packet["missing_fields"] == ["exact_geometry", "material_details"]
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


@pytest.mark.parametrize("builder", EXPECTED_BUILDERS)
def test_confidence_is_present_and_bounded(builder):
    packet = builder(confidence=0.75)
    assert 0.0 <= packet["confidence"] <= 1.0
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


@pytest.mark.parametrize("builder", [
    mod.build_rf_discovery_signal_observation_candidate_v1,
    mod.build_rf_discovery_pattern_candidate_v1,
    mod.build_rf_discovery_strange_signal_candidate_v1,
    mod.build_rf_discovery_calibration_experiment_candidate_v1,
])
def test_alternatives_or_hypotheses_are_preserved(builder):
    packet = builder()
    text = repr(packet).lower()
    if packet["packet_type"] == "rf_discovery_calibration_experiment_candidate":
        assert "hypotheses" in text
    else:
        assert any(token in text for token in ("alternatives", "hypotheses", "possible_causes", "candidate_grammar"))


def test_strange_signal_packet_preserves_unmatched_features_and_next_probe():
    packet = mod.build_rf_discovery_strange_signal_candidate_v1(
        unmatched_features=["spike cluster", "uncertain cadence"],
        next_probe="repeat under traffic-only and movement-only conditions",
    )
    assert packet["unmatched_features"] == ["spike cluster", "uncertain cadence"]
    assert packet["next_probe"] == "repeat under traffic-only and movement-only conditions"
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


def test_calibration_packet_preserves_prediction_and_correction():
    packet = mod.build_rf_discovery_calibration_experiment_candidate_v1(
        prediction_before_label="movement may create a weak repeatable disturbance",
        correction="update threshold and uncertainty handling",
    )
    assert "prediction_before_label" in packet
    assert "correction" in packet
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


def test_visualization_packet_uses_estimated_field_language():
    packet = mod.build_rf_discovery_visualization_frame_candidate_v1()
    text = " ".join(map(str, [packet.get("stable_field_estimate"), packet.get("disturbed_field_estimate"), packet.get("unknown_field_estimate"), packet.get("explanation_panel")])).lower()
    assert "estimated" in text or "estimate" in text
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


def test_value_assessment_does_not_activate_marketplace_release():
    packet = mod.build_rf_discovery_value_assessment_candidate_v1()
    assert packet["marketplace_potential"] == "future_only"
    assert packet["synthetic_demo_possible"] is True
    assert packet["private_data_dependency"] is False
    assert mod.validate_rf_discovery_candidate_packet_v1(packet)


def test_synthetic_examples_contain_no_private_data():
    examples = mod.build_rf_discovery_synthetic_examples_v1()
    assert examples["synthetic_only"] is True
    blob = repr(examples).lower()
    for token in ("private home", "occupancy history", "real router", "rf log", "packet capture"):
        assert token not in blob
    assert all(mod.validate_rf_discovery_candidate_packet_v1(packet) for packet in examples["examples"])


def test_json_safe_conversion_works():
    value = {"a": {1, 2}, "b": ("x", object()), "c": Path("/tmp/demo")}
    safe = mod.to_rf_discovery_json_safe_v1(value)
    assert isinstance(safe, dict)
    assert isinstance(safe["a"], list)
    assert isinstance(safe["b"], list)
    assert isinstance(safe["c"], str)


def test_summarize_returns_json_safe_summary():
    packet = mod.build_rf_discovery_environment_candidate_v1()
    summary = mod.summarize_rf_discovery_candidate_packet_v1(packet)
    assert summary["valid"] is True
    assert summary["packet_type"] == "rf_discovery_environment_candidate"
    assert summary["raw_signal_included"] is False


def test_no_network_or_runtime_wiring_functions_exist():
    function_names = {name for name, obj in inspect.getmembers(mod, inspect.isfunction)}
    expected_public = {
        "build_rf_discovery_anchor_candidate_v1",
        "build_rf_discovery_baseline_candidate_v1",
        "build_rf_discovery_calibration_experiment_candidate_v1",
        "build_rf_discovery_decision_outcome_candidate_v1",
        "build_rf_discovery_environment_candidate_v1",
        "build_rf_discovery_pattern_candidate_v1",
        "build_rf_discovery_signal_observation_candidate_v1",
        "build_rf_discovery_strange_signal_candidate_v1",
        "build_rf_discovery_synthetic_examples_v1",
        "build_rf_discovery_value_assessment_candidate_v1",
        "build_rf_discovery_visualization_frame_candidate_v1",
        "summarize_rf_discovery_candidate_packet_v1",
        "to_rf_discovery_json_safe_v1",
        "validate_rf_discovery_candidate_packet_v1",
    }
    assert expected_public.issubset(function_names)
    forbidden_public = [name for name in function_names if any(token in name.lower() for token in ("router", "repeater", "home", "packet_capture", "csi", "network", "scan"))]
    assert forbidden_public == []


def test_protected_runtime_files_untouched():
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", *PROTECTED_FILES],
        cwd=repo_root,
        check=False,
    )
    assert result.returncode == 0
