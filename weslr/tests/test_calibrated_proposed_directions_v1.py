from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.calibrated_proposed_directions as proposed
from weslr.calibrated_proposed_directions import (
    allowed_calibrated_direction_statuses_v1,
    build_calibrated_proposed_direction_v1,
    build_initial_calibrated_proposed_direction_examples_v1,
    summarize_calibrated_proposed_direction_v1,
    to_calibrated_proposed_direction_json_safe_v1,
    validate_calibrated_proposed_direction_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = Path(__file__).resolve().parents[1] / "calibrated_proposed_directions.py"
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

CANONICAL_DIRECTION_ID = "pulsar_signal_followup_direction"


def _canonical_examples():
    return deepcopy(build_initial_calibrated_proposed_direction_examples_v1())


def _canonical_packet():
    examples = _canonical_examples()
    assert len(examples) >= 1
    packet = next(item for item in examples if item["direction_id"] == CANONICAL_DIRECTION_ID)
    return deepcopy(packet)


def test_required_apis_exist():
    names = [
        "allowed_calibrated_direction_statuses_v1",
        "build_calibrated_proposed_direction_v1",
        "validate_calibrated_proposed_direction_v1",
        "summarize_calibrated_proposed_direction_v1",
        "to_calibrated_proposed_direction_json_safe_v1",
        "build_initial_calibrated_proposed_direction_examples_v1",
    ]
    for name in names:
        assert hasattr(proposed, name)
        assert callable(getattr(proposed, name))


def test_allowed_statuses_are_exact():
    assert allowed_calibrated_direction_statuses_v1() == (
        "candidate_direction",
        "needs_probe",
        "needs_pressure_test",
        "needs_calibration",
        "needs_evidence",
        "watch",
        "archive",
        "operator_review_required",
        "blocked_by_safety",
        "needs_repair",
    )


def test_canonical_example_builds():
    examples = build_initial_calibrated_proposed_direction_examples_v1()
    assert len(examples) >= 1
    packet = next(item for item in examples if item["direction_id"] == CANONICAL_DIRECTION_ID)
    assert packet["direction_status"] == "needs_pressure_test"
    assert packet["expected_next_step"] == "pressure_test"
    assert packet["reverse_trace_reference"] == "pulsar_reverse_calibration_trace"
    assert "capability_suppression_boundary" in packet["calibration_axes_used"]


def test_canonical_example_validates_and_summarizes():
    packet = _canonical_packet()
    validation = validate_calibrated_proposed_direction_v1(packet)
    summary = summarize_calibrated_proposed_direction_v1(packet)

    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"
    assert summary["direction_id"] == CANONICAL_DIRECTION_ID
    assert summary["direction_status"] == "needs_pressure_test"
    assert summary["expected_next_step"] == "pressure_test"
    assert summary["promotion_blockers_count"] == 3
    assert summary["validation_posture"] == "valid"


def test_canonical_example_json_serializes_with_json_dumps():
    packet = _canonical_packet()
    safe = to_calibrated_proposed_direction_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)


def test_canonical_example_is_internal_candidate_only():
    packet = _canonical_packet()
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["valid"] is True
    assert packet["direction_status"] in allowed_calibrated_direction_statuses_v1()
    assert packet["authority_status"]["all_authority_flags_false"] is True
    assert packet["authority_status"]["status"] == "metadata_only"
    assert packet["safe_metadata"]["no_public_claim_authority"] is True
    assert packet["safe_metadata"]["no_final_answer_authority"] is True


def test_canonical_example_preserves_missing_evidence_and_disconfirming_signal():
    packet = _canonical_packet()
    assert packet["missing_evidence"]
    assert packet["disconfirming_signal"]
    assert any("confirmation" in item.lower() or "falsif" in item.lower() for item in packet["missing_evidence"])
    assert any("weaken" in item.lower() or "artifact" in item.lower() or "noise" in item.lower() for item in packet["disconfirming_signal"])


def test_canonical_example_preserves_promotion_blockers_and_risks():
    packet = _canonical_packet()
    assert packet["promotion_blockers"]
    assert "overclaim" in packet["risk_of_overclaim"].lower()
    assert "underexploration" in packet["risk_of_underexploration"].lower()
    assert packet["operator_review_need"]


def test_canonical_example_references_calibration_axes_and_reverse_trace():
    packet = _canonical_packet()
    assert packet["reverse_trace_reference"] == "pulsar_reverse_calibration_trace"
    assert packet["calibration_axes_used"] == [
        "reverse_calibration_backcasting",
        "signal_detection_calibration",
        "popper_falsification_calibration",
        "bayesian_calibration",
        "capability_suppression_boundary",
    ]


@pytest.mark.parametrize(
    "field",
    [
        "direction_id",
        "source_signal_summary",
        "proposed_direction_summary",
        "calibration_axes_used",
        "reverse_trace_reference",
        "expected_next_step",
        "direction_status",
        "disconfirming_signal",
        "forbidden_interpretations",
    ],
)
def test_fail_closed_on_missing_required_fields(field):
    packet = _canonical_packet()
    packet.pop(field, None)
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("direction_id", "", "missing_direction_id"),
        ("source_signal_summary", "", "missing_source_signal_summary"),
        ("proposed_direction_summary", "", "missing_proposed_direction_summary"),
        ("calibration_axes_used", [], "missing_calibration_axes_used"),
        ("reverse_trace_reference", "", "missing_reverse_trace_reference"),
        ("expected_next_step", "", "missing_expected_next_step"),
        ("direction_status", "", "missing_direction_status"),
        ("direction_status", "not_a_status", "invalid_direction_status"),
        ("disconfirming_signal", [], "missing_disconfirming_signal"),
        ("forbidden_interpretations", [], "missing_forbidden_interpretations"),
    ],
)
def test_fail_closed_on_required_fields_and_status_enums(field, value, expected_label):
    packet = _canonical_packet()
    packet[field] = value
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "runtime_authorized",
        "source_ingestion_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "provider_authority",
        "model_authority",
        "tool_execution_authority",
        "retrieval_tool_authority",
        "web_authority",
        "weslr_io_authorized",
        "weslr_read_authorized",
        "weslr_write_authorized",
        "weslr_persistence_authorized",
        "database_write_authority",
        "database_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "hidden_private_protected_authorized",
        "public_science_claim_authorized",
        "proof_claim_authorized",
        "benchmark_claim_authorized",
        "agi_claim_authorized",
        "automatic_discovery_authorized",
    ],
)
def test_fail_closed_on_unsafe_authority_flags(field):
    packet = _canonical_packet()
    packet["authority_status"][field] = True
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert f"unsafe_authority_flag:{field}" in validation["blocked_labels"] or f"unsafe_{field}" in validation["blocked_labels"]


def test_fail_closed_on_public_authority_language_in_authority_fields():
    packet = _canonical_packet()
    packet["authority_status"]["boundary_notes"] = "discovery proof AGI final answer public claim authorized"
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("unsafe_authority_text", "unsafe_safe_metadata_text"))


def test_fail_closed_on_source_ingestion_authorization_and_runtime_authorization():
    packet = _canonical_packet()
    packet["authority_status"]["source_ingestion_authorized"] = True
    packet["authority_status"]["runtime_authorized"] = True
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag:source_ingestion_authorized" in validation["blocked_labels"]
    assert "unsafe_authority_flag:runtime_authorized" in validation["blocked_labels"]


def test_fail_closed_on_hidden_private_protected_markers():
    packet = _canonical_packet()
    packet["source_signal_summary"] = "hidden prompt with private text and api key"
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert "forbidden_hidden_private_protected_marker" in validation["blocked_labels"]


def test_fail_closed_on_non_json_safe_output():
    packet = _canonical_packet()
    packet["safe_metadata"]["callable"] = lambda: None
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]
    assert json.dumps(to_calibrated_proposed_direction_json_safe_v1(packet), sort_keys=True)


def test_neutral_historical_scientific_wording_is_allowed_as_metadata():
    packet = _canonical_packet()
    packet["source_signal_summary"] = "Historical scientific note: this repeated signal is metadata only."
    packet["proposed_direction_summary"] = "Scientific-historical wording is allowed here as internal metadata."
    validation = validate_calibrated_proposed_direction_v1(packet)
    assert validation["valid"] is True


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
