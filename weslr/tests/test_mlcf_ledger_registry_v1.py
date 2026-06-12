from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_ledger_registry as registry
from weslr.mlcf_ledger_registry import (
    allowed_mlcf_ledger_ids_v1,
    build_initial_mlcf_ledger_registry_v1,
    build_mlcf_ledger_definition_v1,
    summarize_mlcf_ledger_registry_v1,
    to_mlcf_ledger_registry_json_safe_v1,
    validate_mlcf_ledger_definition_v1,
    validate_mlcf_ledger_registry_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

ALLOWED_NEW_FILES = {
    "weslr/mlcf_ledger_registry.py",
    "weslr/tests/test_mlcf_ledger_registry_v1.py",
}

CANONICAL_LEDGER_IDS = (
    "user_preference_ledger",
    "user_identity_context_ledger",
    "project_state_ledger",
    "idea_candidate_ledger",
    "decision_ledger",
    "evidence_ledger",
    "failed_idea_ledger",
    "calibration_outcome_ledger",
    "relationship_context_ledger",
    "behavior_candidate_ledger",
    "architecture_direction_ledger",
)


def _canonical_registry():
    return deepcopy(build_initial_mlcf_ledger_registry_v1())


def _canonical_definition(ledger_id: str):
    return deepcopy(build_mlcf_ledger_definition_v1({"ledger_id": ledger_id}))


def test_required_apis_exist():
    for name in [
        "allowed_mlcf_ledger_ids_v1",
        "build_mlcf_ledger_definition_v1",
        "build_initial_mlcf_ledger_registry_v1",
        "validate_mlcf_ledger_definition_v1",
        "validate_mlcf_ledger_registry_v1",
        "summarize_mlcf_ledger_registry_v1",
        "to_mlcf_ledger_registry_json_safe_v1",
    ]:
        assert hasattr(registry, name)
        assert callable(getattr(registry, name))


def test_allowed_ledger_ids_are_exact_and_stable():
    assert allowed_mlcf_ledger_ids_v1() == CANONICAL_LEDGER_IDS


@pytest.mark.parametrize("ledger_id", CANONICAL_LEDGER_IDS)
def test_canonical_ledger_definitions_validate(ledger_id):
    definition = _canonical_definition(ledger_id)
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"


def test_canonical_registry_validates_and_summarizes():
    registry_packet = _canonical_registry()
    validation = validate_mlcf_ledger_registry_v1(registry_packet)
    summary = summarize_mlcf_ledger_registry_v1(registry_packet)

    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"
    assert summary["ledger_count"] == len(CANONICAL_LEDGER_IDS)
    assert summary["ledger_ids"] == list(CANONICAL_LEDGER_IDS)
    assert summary["validation_posture"] == "valid"
    assert summary["registry_id"] == "mlcf_ledger_registry_v1"


def test_registry_summary_is_bounded_and_json_safe():
    registry_packet = _canonical_registry()
    summary = summarize_mlcf_ledger_registry_v1(registry_packet)
    assert len(summary["ledger_ids"]) <= 11
    assert json.dumps(summary, sort_keys=True)


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "ledger_id",
        "ledger_name",
        "ledger_purpose",
        "ledger_scope",
        "authority_requirement",
        "allowed_source_kinds",
        "allowed_record_kinds",
        "read_model_targets",
        "forbidden_operations",
        "privacy_boundary",
        "tombstone_policy",
        "rollback_policy",
        "cross_ledger_reference_policy",
        "retention_review_policy",
        "authority_status",
        "safe_metadata",
    ],
)
def test_missing_required_fields_fail_closed(field):
    definition = _canonical_definition("user_preference_ledger")
    definition.pop(field, None)
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("ledger_id", "not_a_ledger", "invalid_ledger_id"),
        ("schema_version", "wrong_version", "invalid_schema_version"),
        ("ledger_scope", "", "missing_ledger_scope"),
        ("authority_requirement", "", "missing_authority_requirement"),
        ("privacy_boundary", "", "missing_privacy_boundary"),
        ("tombstone_policy", "", "missing_tombstone_policy"),
        ("rollback_policy", "", "missing_rollback_policy"),
        ("cross_ledger_reference_policy", "", "missing_cross_ledger_reference_policy"),
        ("retention_review_policy", "", "missing_retention_review_policy"),
    ],
)
def test_invalid_and_missing_fields_fail_closed(field, value, expected_label):
    definition = _canonical_definition("user_preference_ledger")
    definition[field] = value
    validation = validate_mlcf_ledger_definition_v1(definition)
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
def test_unsafe_authority_flags_fail_closed(field):
    definition = _canonical_definition("evidence_ledger")
    definition["authority_status"][field] = True
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert f"unsafe_authority_flag:{field}" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "public_claim_authorized",
        "final_answer_authority",
        "proof_claim_authorized",
        "benchmark_claim_authorized",
        "agi_claim_authorized",
        "automatic_discovery_authorized",
        "source_ingestion_authorized",
        "runtime_authorized",
        "weslr_io_authorized",
        "weslr_read_authorized",
        "weslr_write_authorized",
        "weslr_persistence_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_pack_promotion_authorized",
    ],
)
def test_public_final_proof_discovery_agi_benchmark_and_mutation_authority_fail_closed(field):
    definition = _canonical_definition("architecture_direction_ledger")
    definition["authority_status"][field] = True
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert f"unsafe_authority_flag:{field}" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    ["ledger_purpose", "privacy_boundary", "authority_requirement", "tombstone_policy", "rollback_policy"],
)
def test_weslr_implication_and_hidden_markers_fail_closed(field):
    definition = _canonical_definition("project_state_ledger")
    definition[field] = "contains .weslr implication and hidden private protected markers"
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert any(
        label in validation["blocked_labels"]
        for label in ("unsafe_authority_text", "forbidden_hidden_private_protected_marker")
    )


@pytest.mark.parametrize(
    "field",
    ["ledger_purpose", "privacy_boundary", "cross_ledger_reference_policy", "retention_review_policy"],
)
def test_text_marker_leakage_and_scope_markers_fail_closed(field):
    definition = _canonical_definition("idea_candidate_ledger")
    definition[field] = "public discovery proof agi benchmark final answer runtime authorization"
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("unsafe_authority_text", "forbidden_hidden_private_protected_marker"))


def test_non_json_safe_objects_are_redacted_or_blocked_according_to_policy():
    definition = _canonical_definition("behavior_candidate_ledger")
    definition["safe_metadata"]["callable"] = lambda: None
    validation = validate_mlcf_ledger_definition_v1(definition)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]

    safe_copy = to_mlcf_ledger_registry_json_safe_v1({"definition": definition, "custom": object()})
    assert json.dumps(safe_copy, sort_keys=True)
    assert safe_copy["definition"]["safe_metadata"]["callable"].startswith("[redacted:")


def test_duplicate_ledger_ids_fail_closed():
    registry_packet = _canonical_registry()
    registry_packet["ledger_definitions"][1]["ledger_id"] = registry_packet["ledger_definitions"][0]["ledger_id"]
    validation = validate_mlcf_ledger_registry_v1(registry_packet)
    assert validation["blocked"] is True
    assert any(label.startswith("duplicate_ledger_id:") for label in validation["blocked_labels"])


def test_missing_required_fields_in_registry_fail_closed():
    registry_packet = _canonical_registry()
    registry_packet.pop("safe_metadata", None)
    validation = validate_mlcf_ledger_registry_v1(registry_packet)
    assert validation["blocked"] is True
    assert "missing_safe_metadata" in validation["blocked_labels"]


def test_registry_rejects_invalid_ledger_order_and_invalid_ids():
    registry_packet = _canonical_registry()
    registry_packet["ledger_definitions"].reverse()
    validation = validate_mlcf_ledger_registry_v1(registry_packet)
    assert validation["blocked"] is True
    assert "invalid_ledger_id_order" in validation["blocked_labels"]


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
