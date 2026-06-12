from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_controlled_information_ingestion_candidate as bridge
from weslr.mlcf_controlled_information_ingestion_candidate import (
    allowed_mlcf_ingestion_input_kinds_v1,
    allowed_mlcf_ingestion_next_steps_v1,
    allowed_mlcf_ingestion_signal_families_v1,
    build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1,
    build_mlcf_controlled_information_ingestion_candidate_v1,
    summarize_mlcf_controlled_information_ingestion_candidate_v1,
    to_mlcf_controlled_information_ingestion_candidate_json_safe_v1,
    validate_mlcf_controlled_information_ingestion_candidate_v1,
)
from weslr.theoretical_calibration_axes import build_initial_theoretical_calibration_axes_examples_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

ALLOWED_NEW_FILES = {
    "weslr/mlcf_controlled_information_ingestion_candidate.py",
    "weslr/tests/test_mlcf_controlled_information_ingestion_candidate_v1.py",
    "weslr/tests/release_gate_v1.py",
}

CANONICAL_EXAMPLE_IDS = (
    "owner_architecture_observation_ingestion_candidate",
    "owner_repeating_signal_ingestion_candidate",
    "blocked_public_claim_ingestion_candidate",
)

IMPLEMENTED_AXIS_IDS = {axis["axis_id"] for axis in build_initial_theoretical_calibration_axes_examples_v1()["axes"]}


def _examples():
    return deepcopy(build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1())


def _example(example_id: str):
    packet = next(item for item in _examples() if item["candidate_id"] == example_id)
    return deepcopy(packet)


def test_required_apis_exist():
    for name in [
        "allowed_mlcf_ingestion_input_kinds_v1",
        "allowed_mlcf_ingestion_next_steps_v1",
        "allowed_mlcf_ingestion_signal_families_v1",
        "build_mlcf_controlled_information_ingestion_candidate_v1",
        "validate_mlcf_controlled_information_ingestion_candidate_v1",
        "summarize_mlcf_controlled_information_ingestion_candidate_v1",
        "to_mlcf_controlled_information_ingestion_candidate_json_safe_v1",
        "build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1",
    ]:
        assert hasattr(bridge, name)
        assert callable(getattr(bridge, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_mlcf_ingestion_input_kinds_v1() == (
        "owner_supplied_observation_summary",
        "owner_supplied_document_summary",
        "internal_project_artifact_summary",
        "known_science_replay_summary",
        "architecture_direction_summary",
        "idea_candidate_summary",
        "blocked_or_unknown_source_summary",
    )
    assert allowed_mlcf_ingestion_next_steps_v1() == (
        "probe",
        "pressure_test",
        "calibrate",
        "watch",
        "archive",
        "operator_review",
        "blocked_by_safety",
        "needs_repair",
    )
    assert allowed_mlcf_ingestion_signal_families_v1() == (
        "weak_signal",
        "repeating_signal",
        "contradictory_signal",
        "cross_domain_resonance_signal",
        "architecture_direction_signal",
        "idea_candidate_signal",
        "evidence_candidate_signal",
        "calibration_needed_signal",
        "blocked_public_claim_signal",
        "archive_low_value_signal",
        "unknown_signal",
    )


def test_canonical_examples_build_validate_and_summarize():
    examples = build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1()
    assert [example["candidate_id"] for example in examples] == list(CANONICAL_EXAMPLE_IDS)

    for example in examples:
        validation = validate_mlcf_controlled_information_ingestion_candidate_v1(example)
        summary = summarize_mlcf_controlled_information_ingestion_candidate_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert summary["validation_posture"] == "valid"
        assert summary["candidate_id"] == example["candidate_id"]
        assert json.dumps(summary, sort_keys=True)
        assert example["authorized_ingestion_boundary_validation"]["valid"] is True
        assert example["evidence_intake_validation"]["valid"] is True
        assert example["calibrated_proposed_direction_validation"]["valid"] is True
        assert example["ledger_registry_summary"]["validation_posture"] == "valid"
        assert example["raw_content_retained"] is False
        assert example["authority_status"]["all_authority_flags_false"] is True
        assert example["authority_status"]["status"] == "metadata_only"
        assert example["safe_metadata"]["no_raw_content_retention"] is True
        assert set(example["calibration_axes_to_apply"]).issubset(IMPLEMENTED_AXIS_IDS)


def test_canonical_example_ledger_recommendations_are_exact():
    examples = {item["candidate_id"]: item for item in build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1()}
    assert examples["owner_architecture_observation_ingestion_candidate"]["recommended_ledger_id"] == "architecture_direction_ledger"
    assert examples["owner_architecture_observation_ingestion_candidate"]["signal_family"] == "architecture_direction_signal"
    assert examples["owner_architecture_observation_ingestion_candidate"]["next_safe_step"] == "pressure_test"

    assert examples["owner_repeating_signal_ingestion_candidate"]["recommended_ledger_id"] == "evidence_ledger"
    assert examples["owner_repeating_signal_ingestion_candidate"]["signal_family"] == "repeating_signal"
    assert examples["owner_repeating_signal_ingestion_candidate"]["next_safe_step"] == "pressure_test"
    assert examples["owner_repeating_signal_ingestion_candidate"]["calibration_axes_to_apply"] == [
        "signal_detection_calibration",
        "bayesian_calibration",
        "reverse_calibration_backcasting",
    ]

    assert examples["blocked_public_claim_ingestion_candidate"]["recommended_ledger_id"] == "failed_idea_ledger"
    assert examples["blocked_public_claim_ingestion_candidate"]["signal_family"] == "blocked_public_claim_signal"
    assert examples["blocked_public_claim_ingestion_candidate"]["next_safe_step"] == "blocked_by_safety"


def test_canonical_example_json_safe_copy_is_dumpable():
    example = _example("owner_architecture_observation_ingestion_candidate")
    safe = to_mlcf_controlled_information_ingestion_candidate_json_safe_v1(example)
    assert json.dumps(safe, sort_keys=True)


def test_canonical_example_next_steps_are_supported():
    for example in _examples():
        assert example["next_safe_step"] in allowed_mlcf_ingestion_next_steps_v1()
        assert example["calibrated_proposed_direction_packet"]["expected_next_step"] == example["next_safe_step"]


@pytest.mark.parametrize("field,value,label", [
    ("input_kind", "not_allowed", "invalid_input_kind"),
    ("signal_family", "not_allowed", "invalid_signal_family"),
    ("next_safe_step", "not_allowed", "invalid_next_safe_step"),
    ("recommended_ledger_id", "not_a_ledger", "invalid_recommended_ledger_id"),
])
def test_invalid_enums_fail_closed(field, value, label):
    packet = _example("owner_repeating_signal_ingestion_candidate")
    packet[field] = value
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "candidate_id",
        "input_kind",
        "input_scope",
        "input_summary",
        "source_access_status",
        "authorized_ingestion_boundary_packet",
        "authorized_ingestion_boundary_validation",
        "evidence_intake_packet",
        "evidence_intake_validation",
        "recommended_ledger_id",
        "recommended_ledger_reason",
        "ledger_registry_summary",
        "signal_family",
        "confidence_posture",
        "calibration_axes_to_apply",
        "calibration_reason",
        "calibrated_proposed_direction_packet",
        "calibrated_proposed_direction_validation",
        "next_safe_step",
        "missing_evidence",
        "disconfirming_signal",
        "promotion_blockers",
        "forbidden_interpretations",
        "authority_status",
        "safe_metadata",
    ],
)
def test_missing_required_fields_fail_closed(field):
    packet = _example("owner_architecture_observation_ingestion_candidate")
    packet.pop(field, None)
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


def test_raw_content_retention_source_ingestion_and_public_authority_fail_closed():
    packet = _example("owner_repeating_signal_ingestion_candidate")
    packet["raw_content_retained"] = True
    packet["authority_status"]["source_ingestion_authorized"] = True
    packet["authority_status"]["public_claim_authorized"] = True
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_raw_content_retained" in validation["blocked_labels"]
    assert "unsafe_authority_flag:source_ingestion_authorized" in validation["blocked_labels"]
    assert "unsafe_authority_flag:public_claim_authorized" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "final_answer_authority",
        "provider_model_call_authority",
        "tool_execution_authority",
        "retrieval_tool_authority",
        "web_authority",
        "weslr_io_authorized",
        "weslr_read_authorized",
        "weslr_write_authorized",
        "weslr_persistence_authorized",
        "database_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_pack_promotion_authorized",
        "public_science_claim_authorized",
        "proof_claim_authorized",
        "benchmark_claim_authorized",
        "agi_claim_authorized",
        "automatic_discovery_authorized",
        "cross_user_leakage_authorized",
        "hidden_private_protected_authorized",
    ],
)
def test_authority_flags_fail_closed(field):
    packet = _example("owner_repeating_signal_ingestion_candidate")
    packet["authority_status"][field] = True
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert f"unsafe_authority_flag:{field}" in validation["blocked_labels"]


def test_provider_tool_web_retrieval_and_weslr_implication_fail_closed():
    packet = _example("owner_architecture_observation_ingestion_candidate")
    packet["authority_status"]["boundary_notes"] = "provider/model/tool/web/retrieval and .weslr implication"
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("unsafe_authority_text", "forbidden_hidden_private_protected_marker"))


def test_hidden_private_protected_markers_fail_closed():
    packet = _example("owner_architecture_observation_ingestion_candidate")
    packet["input_summary"] = "hidden prompt with private text and api key"
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert "forbidden_hidden_private_protected_marker" in validation["blocked_labels"]


def test_memory_project_and_behavior_promotion_fail_closed():
    packet = _example("owner_repeating_signal_ingestion_candidate")
    packet["authority_status"]["memory_mutation_authorized"] = True
    packet["authority_status"]["project_mutation_authorized"] = True
    packet["authority_status"]["behavior_pack_promotion_authorized"] = True
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag:memory_mutation_authorized" in validation["blocked_labels"]
    assert "unsafe_authority_flag:project_mutation_authorized" in validation["blocked_labels"]
    assert "unsafe_authority_flag:behavior_pack_promotion_authorized" in validation["blocked_labels"]


def test_non_json_safe_output_fails_closed():
    packet = _example("owner_repeating_signal_ingestion_candidate")
    packet["safe_metadata"]["callable"] = lambda: None
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutator,label",
    [
        (lambda p: p.__setitem__("authorized_ingestion_boundary_packet", "bad"), "invalid_authorized_ingestion_boundary_packet_type"),
        (lambda p: p.__setitem__("evidence_intake_packet", "bad"), "invalid_evidence_intake_packet_type"),
        (lambda p: p.__setitem__("calibrated_proposed_direction_packet", "bad"), "invalid_calibrated_proposed_direction_packet_type"),
    ],
)
def test_malformed_subpackets_fail_closed(mutator, label):
    packet = _example("owner_architecture_observation_ingestion_candidate")
    mutator(packet)
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert label in validation["blocked_labels"]


def test_blocked_or_mismatched_subpacket_validation_fails_closed():
    packet = _example("owner_architecture_observation_ingestion_candidate")
    packet["evidence_intake_validation"] = {"valid": False, "blocked": True}
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(packet)
    assert validation["blocked"] is True
    assert "mismatched_evidence_intake_validation" in validation["blocked_labels"]


def test_calibration_axes_are_implemented_axes_only():
    for example in _examples():
        assert set(example["calibration_axes_to_apply"]).issubset(IMPLEMENTED_AXIS_IDS)


def test_protected_file_drift_absent():
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
    assert changed.issubset(ALLOWED_NEW_FILES)
