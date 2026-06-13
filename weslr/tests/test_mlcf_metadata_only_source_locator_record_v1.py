from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_metadata_only_source_locator_record as locator
from weslr.mlcf_metadata_only_source_locator_record import (
    allowed_mlcf_locator_access_license_statuses_v1,
    allowed_mlcf_locator_authority_levels_v1,
    allowed_mlcf_locator_evidence_roles_v1,
    allowed_mlcf_locator_freshness_statuses_v1,
    allowed_mlcf_locator_next_steps_v1,
    allowed_mlcf_locator_privacy_statuses_v1,
    allowed_mlcf_locator_source_classes_v1,
    build_initial_mlcf_metadata_only_source_locator_record_examples_v1,
    build_mlcf_metadata_only_source_locator_record_v1,
    summarize_mlcf_metadata_only_source_locator_record_v1,
    to_mlcf_metadata_only_source_locator_record_json_safe_v1,
    validate_mlcf_metadata_only_source_locator_record_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _examples():
    return deepcopy(build_initial_mlcf_metadata_only_source_locator_record_examples_v1())


def _example(locator_id: str):
    for item in _examples():
        if item["locator_id"] == locator_id:
            return item
    raise AssertionError(f"missing example {locator_id}")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_locator_source_classes_v1",
        "allowed_mlcf_locator_authority_levels_v1",
        "allowed_mlcf_locator_evidence_roles_v1",
        "allowed_mlcf_locator_freshness_statuses_v1",
        "allowed_mlcf_locator_access_license_statuses_v1",
        "allowed_mlcf_locator_privacy_statuses_v1",
        "allowed_mlcf_locator_next_steps_v1",
        "build_mlcf_metadata_only_source_locator_record_v1",
        "validate_mlcf_metadata_only_source_locator_record_v1",
        "summarize_mlcf_metadata_only_source_locator_record_v1",
        "to_mlcf_metadata_only_source_locator_record_json_safe_v1",
        "build_initial_mlcf_metadata_only_source_locator_record_examples_v1",
    ]
    for name in names:
        assert hasattr(locator, name)
        assert callable(getattr(locator, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_mlcf_locator_source_classes_v1() == (
        "official_standard",
        "official_government_or_agency_data",
        "official_vendor_documentation",
        "public_research_paper",
        "public_dataset",
        "github_repository",
        "public_lab_or_university_artifact",
        "public_benchmark_or_test_suite",
        "blocked_private_or_hidden_source",
    )
    assert allowed_mlcf_locator_authority_levels_v1() == (
        "official_primary",
        "public_primary",
        "public_secondary",
        "implementation_evidence",
        "community_signal",
        "owner_context",
        "internal_context",
        "unknown_authority",
        "blocked",
    )
    assert allowed_mlcf_locator_evidence_roles_v1() == (
        "definition_or_standard",
        "measurement_data",
        "implementation_reference",
        "prior_art",
        "candidate_signal",
        "counterexample_source",
        "replication_target",
        "constraint_source",
        "domain_context",
        "safety_boundary_context",
        "not_authoritative_context",
    )
    assert allowed_mlcf_locator_freshness_statuses_v1() == ("current", "recent", "stale", "unknown")
    assert allowed_mlcf_locator_access_license_statuses_v1() == ("open", "permissioned", "restricted", "blocked", "unknown")
    assert allowed_mlcf_locator_privacy_statuses_v1() == ("low", "medium", "high", "unknown")
    assert allowed_mlcf_locator_next_steps_v1() == (
        "operator_review",
        "prepare_metadata_only_source_summary",
        "reject_locator",
        "needs_repair",
        "blocked_by_safety",
    )


def test_canonical_examples_build():
    examples = _examples()
    assert {item["locator_id"] for item in examples} == {
        "rf_wifi_standard_locator_record",
        "rf_sensing_public_paper_locator_record",
        "wifi_sensing_github_repo_locator_record",
        "blocked_private_hidden_locator_record",
    }


def test_canonical_examples_validate_and_summarize():
    for example in _examples():
        validation = validate_mlcf_metadata_only_source_locator_record_v1(example)
        summary = summarize_mlcf_metadata_only_source_locator_record_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert validation["validation_posture"] == "valid"
        assert summary["locator_id"] == example["locator_id"]
        assert summary["source_class"] == example["source_class"]
        assert summary["validation_posture"] == "valid"
        assert summary["summary_text"]
        assert len(summary["summary_text"]) <= 200


def test_official_standard_locator_validates():
    packet = _example("rf_wifi_standard_locator_record")
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["valid"] is True
    assert packet["source_class"] == "official_standard"
    assert packet["authority_level_guess"] == "official_primary"
    assert packet["evidence_role_guess"] == "definition_or_standard"


def test_public_paper_locator_validates():
    packet = _example("rf_sensing_public_paper_locator_record")
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["valid"] is True
    assert packet["source_class"] == "public_research_paper"
    assert packet["authority_level_guess"] == "public_primary"
    assert packet["evidence_role_guess"] == "prior_art"


def test_github_locator_validates_but_cannot_claim_official_science_authority():
    packet = _example("wifi_sensing_github_repo_locator_record")
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["valid"] is True
    assert packet["source_class"] == "github_repository"
    assert packet["authority_level_guess"] == "implementation_evidence"

    blocked = build_mlcf_metadata_only_source_locator_record_v1(
        deepcopy(packet),
        authority_level_guess="official_primary",
    )
    blocked_validation = validate_mlcf_metadata_only_source_locator_record_v1(blocked)
    assert blocked_validation["blocked"] is True
    assert any(
        label in blocked_validation["blocked_labels"]
        for label in ("invalid_authority_level", "github_locator_claims_official_science_authority")
    )


def test_private_hidden_locator_blocks_safely():
    packet = _example("blocked_private_hidden_locator_record")
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["valid"] is True
    assert packet["source_class"] == "blocked_private_or_hidden_source"
    assert packet["authority_level_guess"] == "blocked"
    assert packet["access_license_status"] == "blocked"
    assert packet["privacy_status"] == "high"
    assert any("private" in item.lower() or "hidden" in item.lower() or "protected" in item.lower() for item in packet["blocked_conditions"])


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("source_class", "not_real", "invalid_source_class"),
        ("authority_level_guess", "not_real", "invalid_authority_level"),
        ("evidence_role_guess", "not_real", "invalid_evidence_role"),
        ("freshness_status", "not_real", "invalid_freshness_status"),
        ("access_license_status", "not_real", "invalid_access_license_status"),
        ("privacy_status", "not_real", "invalid_privacy_status"),
        ("allowed_next_step", "not_real", "invalid_allowed_next_step"),
    ],
)
def test_invalid_enum_values_fail_closed(field, value, expected_label):
    packet = _example("rf_wifi_standard_locator_record")
    packet[field] = value
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "locator_id",
        "science_direction_id",
        "query_family",
        "candidate_title",
        "candidate_url_or_identifier",
        "candidate_domain",
        "relevance_reason",
        "operator_review_need",
    ],
)
def test_missing_required_fields_fail_closed(field):
    packet = _example("rf_wifi_standard_locator_record")
    packet[field] = ""
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


def test_missing_blocked_conditions_fail_closed():
    packet = _example("rf_wifi_standard_locator_record")
    packet["blocked_conditions"] = []
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert "missing_blocked_conditions" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "authority_field",
    [
        "source_ingestion_authorized",
        "raw_retention_authorized",
        "web_call_authority",
        "github_call_authority",
        "source_fetching_authorized",
        "source_summary_authorized",
        "source_access_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "discovery_claim_authorized",
        "proof_claim_authorized",
        "agi_claim_authorized",
        "benchmark_claim_authorized",
        "public_science_claim_authorized",
        "behavior_pack_promotion_authorized",
        "database_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "cross_user_leakage_authorized",
        "hidden_private_protected_authorized",
    ],
)
def test_unsafe_authority_flags_fail_closed(authority_field):
    packet = _example("rf_wifi_standard_locator_record")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert any(authority_field in label for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "authority_field",
    [
        "source_ingestion_authorized",
        "raw_retention_authorized",
        "web_call_authority",
        "github_call_authority",
        "source_fetching_authorized",
        "source_summary_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "discovery_claim_authorized",
        "proof_claim_authorized",
        "agi_claim_authorized",
        "benchmark_claim_authorized",
        "public_science_claim_authorized",
    ],
)
def test_ingestion_web_github_summary_and_claim_authority_fail_closed(authority_field):
    packet = _example("rf_wifi_standard_locator_record")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert any(authority_field in label for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field, text, expected_label",
    [
        ("candidate_title", ".weslr access implied", "unsafe_weslr_io_implication"),
        ("relevance_reason", "database write implication", "unsafe_database_write_implication"),
        ("operator_review_need", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("relevance_reason", "behavior pack promotion implication", "unsafe_behavior_pack_promotion_implication"),
        ("relevance_reason", "public science discovery proof benchmark agi claim", "unsafe_claim_language"),
    ],
)
def test_weslr_database_memory_project_and_claim_implications_fail_closed(field, text, expected_label):
    packet = _example("rf_wifi_standard_locator_record")
    packet[field] = text
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_cross_user_leakage_fails_closed():
    packet = _example("rf_wifi_standard_locator_record")
    packet["relevance_reason"] = "cross-user leakage implication"
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_claim_language" in validation["blocked_labels"] or any(
        "cross-user" in label for label in validation["blocked_labels"]
    )


def test_hidden_private_protected_markers_fail_closed():
    packet = _example("rf_wifi_standard_locator_record")
    packet["candidate_title"] = "private hidden protected source locator"
    validation = validate_mlcf_metadata_only_source_locator_record_v1(packet)
    assert validation["blocked"] is True
    assert any("unsafe_hidden_private_protected_marker" in label for label in validation["blocked_labels"])


def test_json_safe_copy_preserves_allowed_metadata_and_blocks_unsafe_structures():
    packet = _example("rf_wifi_standard_locator_record")
    packet["authority_status"]["nested"] = {"extra": {1, 2}}
    packet["authority_status"]["custom_object"] = object()
    safe = to_mlcf_metadata_only_source_locator_record_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)
    assert safe["authority_status"]["nested"]["extra"] == [1, 2]
    assert isinstance(safe["authority_status"]["custom_object"], str)


def test_summaries_are_bounded_and_metadata_only():
    packet = _example("rf_wifi_standard_locator_record")
    packet["relevance_reason"] = "x" * 500
    summary = summarize_mlcf_metadata_only_source_locator_record_v1(packet)
    assert summary["validation_posture"] == "valid"
    assert len(summary["summary_text"]) <= 200
    assert summary["locator_id"] == packet["locator_id"]


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
