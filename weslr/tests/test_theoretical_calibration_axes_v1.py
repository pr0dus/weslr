from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.theoretical_calibration_axes as axes_module
from weslr.theoretical_calibration_axes import (
    allowed_theoretical_calibration_failure_modes_v1,
    allowed_theoretical_calibration_next_steps_v1,
    build_initial_theoretical_calibration_axes_examples_v1,
    build_theoretical_calibration_axes_set_v1,
    build_theoretical_calibration_axis_v1,
    summarize_theoretical_calibration_axes_set_v1,
    to_theoretical_calibration_axes_json_safe_v1,
    validate_theoretical_calibration_axes_set_v1,
    validate_theoretical_calibration_axis_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = Path(__file__).resolve().parents[1] / "theoretical_calibration_axes.py"
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

_REQUIRED_AXIS_IDS = (
    "reverse_calibration_backcasting",
    "adversarial_gan_calibration",
    "godel_incompleteness_calibration",
    "popper_falsification_calibration",
    "bayesian_calibration",
    "signal_detection_calibration",
    "cybernetic_control_calibration",
    "information_theory_compression_calibration",
    "causal_counterfactual_calibration",
    "game_theory_incentive_calibration",
    "evolutionary_calibration",
    "topological_structure_preserving_calibration",
    "nonlinear_escalation_schedule_calibration",
)


def _canonical_set():
    return deepcopy(build_initial_theoretical_calibration_axes_examples_v1())


def _canonical_axes_by_id():
    return {axis["axis_id"]: deepcopy(axis) for axis in _canonical_set()["axes"]}


def _base_axis(axis_id: str = "reverse_calibration_backcasting"):
    return deepcopy(_canonical_axes_by_id()[axis_id])


def test_required_apis_exist():
    names = [
        "allowed_theoretical_calibration_next_steps_v1",
        "allowed_theoretical_calibration_failure_modes_v1",
        "build_theoretical_calibration_axis_v1",
        "validate_theoretical_calibration_axis_v1",
        "build_theoretical_calibration_axes_set_v1",
        "validate_theoretical_calibration_axes_set_v1",
        "summarize_theoretical_calibration_axes_set_v1",
        "to_theoretical_calibration_axes_json_safe_v1",
        "build_initial_theoretical_calibration_axes_examples_v1",
    ]
    for name in names:
        assert hasattr(axes_module, name)
        assert callable(getattr(axes_module, name))


def test_allowed_labels_match_expected_constants():
    assert allowed_theoretical_calibration_next_steps_v1() == (
        "probe",
        "pressure_test",
        "calibrate",
        "watch",
        "archive",
        "operator_review",
        "blocked_by_safety",
        "needs_repair",
    )
    assert allowed_theoretical_calibration_failure_modes_v1() == (
        "calibrate_everything",
        "creative_but_unpressuretested_candidate",
        "fake_certainty_inside_incomplete_system",
        "unfalsifiable_direction",
        "confidence_does_not_move_or_moves_too_fast",
        "noise_as_signal_or_signal_as_noise",
        "endless_calibration_loop_or_overreaction",
        "pattern_without_explanatory_gain",
        "correlation_claimed_as_cause",
        "belief_distorted_by_strategy_or_incentives",
        "weak_candidates_never_evolve_or_never_die",
        "fake_analogy",
        "flat_timing_or_infinite_wait",
    )


def test_canonical_axis_set_builds():
    packet = _canonical_set()
    assert packet["axis_set_id"] == "theoretical_calibration_axes_set_v1"
    assert len(packet["axes"]) == 13
    assert {axis["axis_id"] for axis in packet["axes"]} == set(_REQUIRED_AXIS_IDS)


def test_canonical_axis_set_validates():
    validation = validate_theoretical_calibration_axes_set_v1(_canonical_set())
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"


def test_canonical_axis_set_summarizes():
    summary = summarize_theoretical_calibration_axes_set_v1(_canonical_set())
    assert summary["axis_count"] == 13
    assert summary["failure_mode_count"] == 13
    assert summary["validation_posture"] == "valid"
    assert set(summary["next_step_labels_used"]) <= set(allowed_theoretical_calibration_next_steps_v1())
    assert set(summary["combined_stack_prevention_themes"])


def test_canonical_axis_set_json_serializes_with_json_dumps():
    safe = to_theoretical_calibration_axes_json_safe_v1(_canonical_set())
    assert json.dumps(safe, sort_keys=True)


@pytest.mark.parametrize(
    "axis_id, expected_failure_mode",
    [
        ("reverse_calibration_backcasting", "calibrate_everything"),
        ("adversarial_gan_calibration", "creative_but_unpressuretested_candidate"),
        ("godel_incompleteness_calibration", "fake_certainty_inside_incomplete_system"),
        ("popper_falsification_calibration", "unfalsifiable_direction"),
        ("bayesian_calibration", "confidence_does_not_move_or_moves_too_fast"),
        ("signal_detection_calibration", "noise_as_signal_or_signal_as_noise"),
        ("cybernetic_control_calibration", "endless_calibration_loop_or_overreaction"),
        ("information_theory_compression_calibration", "pattern_without_explanatory_gain"),
        ("causal_counterfactual_calibration", "correlation_claimed_as_cause"),
        ("game_theory_incentive_calibration", "belief_distorted_by_strategy_or_incentives"),
        ("evolutionary_calibration", "weak_candidates_never_evolve_or_never_die"),
        ("topological_structure_preserving_calibration", "fake_analogy"),
        ("nonlinear_escalation_schedule_calibration", "flat_timing_or_infinite_wait"),
    ],
)
def test_axis_to_failure_mode_mapping(axis_id, expected_failure_mode):
    axis = _base_axis(axis_id)
    assert axis["calibrated_failure_mode"] == expected_failure_mode
    assert validate_theoretical_calibration_axis_v1(axis)["valid"] is True


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"axis_id": ""}, "missing_axis_id"),
        ({"theory_family": ""}, "missing_theory_family"),
        ({"calibrated_failure_mode": ""}, "missing_failure_mode"),
        ({"calibrated_failure_mode": "bogus"}, "unknown_failure_mode"),
        ({"calibration_question": ""}, "missing_calibration_question"),
        ({"next_step_effect": "not_allowed"}, "invalid_next_step_effect"),
        ({"forbidden_misuse": ""}, "missing_forbidden_misuse"),
    ],
)
def test_validation_fail_closed_required_fields(mutation, expected_label):
    axis = _base_axis()
    axis.update(mutation)
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"authority_status": {**_base_axis()["authority_status"], "runtime_authorized": True}}, "unsafe_authority_flag:runtime_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "source_ingestion_authorized": True}}, "unsafe_authority_flag:source_ingestion_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "public_claim_authorized": True}}, "unsafe_authority_flag:public_claim_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "final_answer_authority": True}}, "unsafe_authority_flag:final_answer_authority"),
        ({"authority_status": {**_base_axis()["authority_status"], "provider_model_call_authority": True}}, "unsafe_authority_flag:provider_model_call_authority"),
        ({"authority_status": {**_base_axis()["authority_status"], "tool_execution_authority": True}}, "unsafe_authority_flag:tool_execution_authority"),
        ({"authority_status": {**_base_axis()["authority_status"], "retrieval_tool_authority": True}}, "unsafe_authority_flag:retrieval_tool_authority"),
        ({"authority_status": {**_base_axis()["authority_status"], "web_authority": True}}, "unsafe_authority_flag:web_authority"),
        ({"authority_status": {**_base_axis()["authority_status"], "weslr_io_authorized": True}}, "unsafe_authority_flag:weslr_io_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "weslr_read_authorized": True}}, "unsafe_authority_flag:weslr_read_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "weslr_write_authorized": True}}, "unsafe_authority_flag:weslr_write_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "weslr_persistence_authorized": True}}, "unsafe_authority_flag:weslr_persistence_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "database_write_authorized": True}}, "unsafe_authority_flag:database_write_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "memory_mutation_authorized": True}}, "unsafe_authority_flag:memory_mutation_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "project_mutation_authorized": True}}, "unsafe_authority_flag:project_mutation_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "hidden_private_protected_authorized": True}}, "unsafe_authority_flag:hidden_private_protected_authorized"),
        ({"authority_status": {**_base_axis()["authority_status"], "boundary_notes": "discovery proof agi final answer public claim authorized"}}, "unsafe_authority_text"),
    ],
)
def test_validation_fail_closed_authority_flags(mutation, expected_label):
    axis = _base_axis()
    axis.update(mutation)
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"authority_status": {"status": "not_metadata_only"}}, "unsafe_authority_status"),
        ({"safe_metadata": {**_base_axis()["safe_metadata"], "no_public_claim_authority": False}}, "unsafe_safe_metadata_flag:no_public_claim_authority"),
        ({"safe_metadata": {**_base_axis()["safe_metadata"], "axis_family": "proof discovery final answer"}}, "unsafe_safe_metadata_text"),
        ({"example_application": "hidden prompt with secret api key"}, "forbidden_hidden_private_protected_marker"),
        ({"safe_metadata": {**_base_axis()["safe_metadata"], "nested": {"payload": {1, 2}}}}, "non_json_safe_output"),
    ],
)
def test_validation_fail_closed_metadata_and_json_safety(mutation, expected_label):
    axis = _base_axis()
    axis.update(mutation)
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "theory_family, example_application",
    [
        ("historical_scientific_theory_note", "Historical scientific calibration note: the signal was measured in a prior experiment."),
        ("neutral_calibration_family", "Scientific-historical note about how calibration got better over time."),
    ],
)
def test_neutral_theory_names_and_historical_scientific_wording_are_allowed(theory_family, example_application):
    axis = _base_axis()
    axis["theory_family"] = theory_family
    axis["example_application"] = example_application
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is False


@pytest.mark.parametrize(
    "authority_text",
    [
        "discovery proof AGI final answer",
        "public claim authorized discovery proof",
        "benchmark score official intelligence",
    ],
)
def test_public_discovery_proof_agi_final_answer_wording_fails_in_authority_bearing_fields(authority_text):
    axis = _base_axis()
    axis["authority_status"]["boundary_notes"] = authority_text
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "field, marker",
    [
        ("example_application", "hidden prompt"),
        ("safe_internal_use", "private text"),
        ("forbidden_misuse", "secret"),
    ],
)
def test_hidden_private_protected_markers_fail(field, marker):
    axis = _base_axis()
    axis[field] = f"{marker} present in metadata"
    validation = validate_theoretical_calibration_axis_v1(axis)
    assert validation["blocked"] is True
    assert "forbidden_hidden_private_protected_marker" in validation["blocked_labels"]


def test_set_validation_fails_if_axis_count_or_failure_mode_count_is_wrong():
    packet = _canonical_set()
    packet["axes"] = packet["axes"][:-1]
    validation = validate_theoretical_calibration_axes_set_v1(packet)
    assert validation["blocked"] is True
    assert "wrong_axis_count" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"axis_set_id": ""}, "missing_axis_set_id"),
        ({"axis_set_id": "wrong"}, "invalid_axis_set_id"),
        ({"axes": "not a list"}, "missing_axes"),
    ],
)
def test_axes_set_validation_fail_closed_structure(mutation, expected_label):
    packet = _canonical_set()
    packet.update(mutation)
    validation = validate_theoretical_calibration_axes_set_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_axes_set_validation_detects_duplicate_and_missing_axes():
    packet = _canonical_set()
    packet["axes"][0]["axis_id"] = packet["axes"][1]["axis_id"]
    validation = validate_theoretical_calibration_axes_set_v1(packet)
    assert validation["blocked"] is True
    assert "duplicate_axis_ids" in validation["blocked_labels"]


def test_axes_set_validation_detects_axis_failure_mode_mismatch():
    packet = _canonical_set()
    packet["axes"][0]["calibrated_failure_mode"] = "flat_timing_or_infinite_wait"
    validation = validate_theoretical_calibration_axes_set_v1(packet)
    assert validation["blocked"] is True
    assert "missing_required_failure_modes" in validation["blocked_labels"] or "unexpected_failure_modes" in validation["blocked_labels"]


def test_axes_set_validation_detects_non_json_safe_output():
    packet = _canonical_set()
    packet["axes"][0]["safe_metadata"]["callable"] = lambda: None
    validation = validate_theoretical_calibration_axes_set_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]


def test_helper_does_not_import_runtime_provider_tool_web_source_ingestion_modules():
    source = HELPER_PATH.read_text()
    forbidden = (
        "import weslr.runtime",
        "import weslr.provider",
        "import weslr.tool",
        "import weslr.web",
        "import weslr.source_ingestion",
        "from weslr import runtime",
        "from weslr import provider",
        "from weslr import tool",
        "from weslr import web",
        "from weslr import source_ingestion",
    )
    assert not any(marker in source for marker in forbidden)


def test_protected_files_remain_untouched():
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {
        line.split(maxsplit=1)[1]
        for line in completed.stdout.splitlines()
        if line.strip()
    }
    assert not changed.intersection(PROTECTED_FILES)
