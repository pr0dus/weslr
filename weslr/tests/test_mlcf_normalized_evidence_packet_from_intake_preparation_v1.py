from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_normalized_evidence_packet_from_intake_preparation as norm
from weslr.mlcf_evidence_intake_packet_from_metadata_summary import build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1
from weslr.mlcf_authorized_metadata_only_source_summary import build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1
from weslr.mlcf_source_locator_organization_review_packet import build_initial_mlcf_source_locator_organization_review_packet_examples_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _intake_examples():
    return deepcopy(build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1())


def _intake_packet(packet_id: str):
    for packet in _intake_examples():
        if packet["evidence_intake_packet_id"] == packet_id:
            return packet
    raise AssertionError(packet_id)


def _frontier_intake_packet():
    return _intake_packet("frontier_space_metadata_summary_to_evidence_intake_packet")


def _rf_intake_packet():
    return _intake_packet("rf_metadata_summary_operator_review_excluded_packet")


def _blocked_intake_packet():
    return _intake_packet("blocked_metadata_summary_to_evidence_intake_packet")


def _synthetic_github_intake_packet():
    packet = _frontier_intake_packet()
    record = deepcopy(packet["evidence_intake_preparation_records"][0])
    record.update(
        {
            "source_kind_hint": "github_repository_metadata",
            "evidence_preparation_role": "implementation_reference_preparation",
            "candidate_title": "GitHub implementation evidence summary candidate",
            "candidate_url_or_identifier": "https://github.com/example/repo",
            "candidate_domain": "github.com",
            "metadata_summary_text": "Metadata-only GitHub implementation evidence summary candidate.",
            "normalized_evidence_preparation_type": "implementation_reference_normalization_preparation",
            "metadata_only_claim_shape": "metadata-only claim shape; no claim or evidence output.",
            "source_content_required_notice": "Later content access would be required for full normalization; not available here.",
            "confidence_posture": "metadata_only_unverified",
        }
    )
    packet["evidence_intake_preparation_records"] = [record]
    packet["preparation_record_count"] = 1
    packet["excluded_summary_records"] = []
    packet["excluded_record_count"] = 0
    packet["blocked_records"] = []
    packet["blocked_record_count"] = 0
    packet["input_metadata_summary_count"] = 1
    packet["source_class_distribution"] = {"github_repository": 1}
    packet["authority_distribution"] = {"implementation_evidence": 1}
    packet["evidence_role_distribution"] = {"implementation_reference": 1}
    packet["intake_status"] = "evidence_intake_packet_prepared"
    packet["allowed_next_step"] = "prepare_normalized_evidence_packet"
    packet["evidence_intake_packet_id"] = "github_intake_to_normalized_evidence_preparation_packet"
    return packet


def _preparation_packet(packet_id: str):
    examples = norm.build_initial_mlcf_normalized_evidence_packet_from_intake_preparation_examples_v1()
    for packet in examples:
        if packet["normalized_evidence_packet_id"] == packet_id:
            return deepcopy(packet)
    raise AssertionError(packet_id)


def test_required_apis_exist():
    names = [
        "allowed_mlcf_normalized_evidence_packet_statuses_v1",
        "allowed_mlcf_normalized_evidence_packet_next_steps_v1",
        "allowed_mlcf_normalized_evidence_preparation_types_v1",
        "allowed_mlcf_normalized_evidence_confidence_postures_v1",
        "build_mlcf_normalized_evidence_packet_from_intake_preparation_v1",
        "build_mlcf_normalized_evidence_preparation_record_v1",
        "validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1",
        "summarize_mlcf_normalized_evidence_packet_from_intake_preparation_v1",
        "to_mlcf_normalized_evidence_packet_from_intake_preparation_json_safe_v1",
        "build_initial_mlcf_normalized_evidence_packet_from_intake_preparation_examples_v1",
    ]
    for name in names:
        assert hasattr(norm, name)
        assert callable(getattr(norm, name))


def test_allowed_enums_are_exact_and_stable():
    assert norm.allowed_mlcf_normalized_evidence_packet_statuses_v1() == (
        "normalized_evidence_preparation_packet_prepared",
        "excluded_needs_operator_review",
        "excluded_needs_repair",
        "excluded_blocked_by_safety",
        "blocked_by_safety",
    )
    assert norm.allowed_mlcf_normalized_evidence_packet_next_steps_v1() == (
        "operator_review",
        "prepare_provisional_candidate_evidence_packet",
        "repair_intake_preparation_records",
        "reject_normalized_evidence_packet",
        "blocked_by_safety",
    )
    assert norm.allowed_mlcf_normalized_evidence_preparation_types_v1() == (
        "definition_or_standard_normalization_preparation",
        "measurement_data_normalization_preparation",
        "prior_art_normalization_preparation",
        "implementation_reference_normalization_preparation",
        "replication_target_normalization_preparation",
        "domain_context_normalization_preparation",
        "constraint_source_normalization_preparation",
        "not_authoritative_context_normalization_preparation",
    )
    assert norm.allowed_mlcf_normalized_evidence_confidence_postures_v1() == (
        "metadata_only_unverified",
        "requires_source_content",
        "requires_operator_review",
        "blocked_by_safety",
    )


def test_canonical_examples_build_and_validate():
    examples = norm.build_initial_mlcf_normalized_evidence_packet_from_intake_preparation_examples_v1()
    assert {item["normalized_evidence_packet_id"] for item in examples} == {
        "frontier_space_intake_to_normalized_evidence_preparation_packet",
        "rf_excluded_intake_to_normalized_evidence_preparation_packet",
        "blocked_intake_to_normalized_evidence_preparation_packet",
    }
    for example in examples:
        validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert norm.summarize_mlcf_normalized_evidence_packet_from_intake_preparation_v1(example)["normalized_evidence_packet_id"] == example["normalized_evidence_packet_id"]


def test_frontier_space_intake_to_normalized_evidence_preparation_result():
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 3
    assert packet["excluded_record_count"] == 0
    assert packet["blocked_record_count"] == 0
    assert packet["normalized_evidence_preparation_status"] == "normalized_evidence_preparation_packet_prepared"
    assert packet["allowed_next_step"] == "prepare_provisional_candidate_evidence_packet"
    assert [r["normalized_evidence_preparation_type"] for r in packet["normalized_evidence_preparation_records"]] == [
        "domain_context_normalization_preparation",
        "prior_art_normalization_preparation",
        "measurement_data_normalization_preparation",
    ]


def test_rf_excluded_intake_to_normalized_evidence_preparation_result():
    packet = _preparation_packet("rf_excluded_intake_to_normalized_evidence_preparation_packet")
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 0
    assert packet["excluded_record_count"] == 3
    assert packet["blocked_record_count"] == 0
    assert packet["normalized_evidence_preparation_status"] == "excluded_needs_operator_review"
    assert packet["allowed_next_step"] == "operator_review"
    assert all(item["normalized_evidence_packet_status"] == "excluded_needs_operator_review" for item in packet["excluded_intake_records"])


def test_blocked_intake_to_normalized_evidence_preparation_result():
    packet = _preparation_packet("blocked_intake_to_normalized_evidence_preparation_packet")
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 0
    assert packet["excluded_record_count"] == 0
    assert packet["blocked_record_count"] == 1
    assert packet["normalized_evidence_preparation_status"] == "blocked_by_safety"
    assert packet["allowed_next_step"] == "blocked_by_safety"
    assert packet["blocked_records"][0]["normalized_evidence_packet_status"] == "blocked_by_safety"


def test_github_stays_implementation_reference_only():
    packet = _synthetic_github_intake_packet()
    prep = norm.build_mlcf_normalized_evidence_preparation_record_v1(packet["evidence_intake_preparation_records"][0])
    assert prep["source_kind_hint"] == "github_repository_metadata"
    assert prep["normalized_evidence_preparation_type"] == "implementation_reference_normalization_preparation"
    assert "official science" not in prep["not_normalized_evidence_notice"].lower()


def test_frontier_fixture_remains_non_claim_metadata_routing():
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    assert all("discovery" not in item["not_normalized_evidence_notice"].lower() for item in packet["normalized_evidence_preparation_records"])
    assert all("proof" not in item["not_normalized_evidence_notice"].lower() for item in packet["normalized_evidence_preparation_records"])
    assert all("public science" not in item["not_normalized_evidence_notice"].lower() for item in packet["normalized_evidence_preparation_records"])


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("source_content", "full text", "preparation_record_contains_source_content"),
        ("full_text", "full text", "preparation_record_contains_source_content"),
        ("raw_page_content", "raw content", "preparation_record_contains_source_content"),
        ("quote", "quoted content", "preparation_record_contains_source_content"),
        ("excerpt", "excerpt content", "preparation_record_contains_source_content"),
        ("evidence_claim", "claim", "preparation_record_contains_source_content"),
        ("normalized_evidence", "normalized", "preparation_record_contains_source_content"),
        ("trusted_evidence", "trusted", "preparation_record_contains_source_content"),
        ("accepted_evidence", "accepted", "preparation_record_contains_source_content"),
        ("accepted_candidate", "accepted", "preparation_record_contains_source_content"),
        ("proposal_payload", "proposal", "preparation_record_contains_source_content"),
    ],
)
def test_source_content_boundary(field, value, expected_label):
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    packet["normalized_evidence_preparation_records"][0][field] = value
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("source_access_authorized", True, "unsafe_authority_flag:source_access_authorized"),
        ("source_fetching_authority", True, "unsafe_authority_flag:source_fetching_authority"),
        ("source_summary_authority", True, "unsafe_authority_flag:source_summary_authority"),
        ("source_content_ingestion_authorized", True, "unsafe_authority_flag:source_content_ingestion_authorized"),
        ("evidence_claim_authorized", True, "unsafe_authority_flag:evidence_claim_authorized"),
        ("normalized_evidence_authorized", True, "unsafe_authority_flag:normalized_evidence_authorized"),
        ("trusted_evidence_authorized", True, "unsafe_authority_flag:trusted_evidence_authorized"),
        ("accepted_evidence_authorized", True, "unsafe_authority_flag:accepted_evidence_authorized"),
        ("candidate_graph_membership_authorized", True, "unsafe_authority_flag:candidate_graph_membership_authorized"),
        ("proposal_payload_authorized", True, "unsafe_authority_flag:proposal_payload_authorized"),
        ("proposal_submission_authorized", True, "unsafe_authority_flag:proposal_submission_authorized"),
        ("proposal_application_authorized", True, "unsafe_authority_flag:proposal_application_authorized"),
    ],
)
def test_unsafe_authority_flags_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    packet["authority_status"][field] = value
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("metadata_summary_text", "WESLR discovered a result", "unsafe_claim_language"),
        ("metadata_summary_text", "confirmed discovery", "unsafe_claim_language"),
        ("metadata_summary_text", "proved", "unsafe_claim_language"),
        ("metadata_summary_text", "public science result", "unsafe_claim_language"),
        ("metadata_summary_text", "benchmark-winning", "unsafe_claim_language"),
        ("metadata_summary_text", "AGI consciousness", "unsafe_claim_language"),
        ("science_direction_summary", "WESLR discovered a result", "unsafe_claim_language"),
        ("metadata_only_claim_shape", "proposal application", "unsafe_claim_language"),
    ],
)
def test_unsafe_claim_language_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    packet["normalized_evidence_preparation_records"][0][field] = value
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("normalization_scope", ".weslr scope", "unsafe_weslr_io_implication"),
        ("normalization_scope", "database write implication", "unsafe_database_write_implication"),
        ("normalization_scope", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("normalization_scope", "behavior pack promotion", "unsafe_behavior_pack_promotion_implication"),
    ],
)
def test_weslr_database_memory_project_mutation_implications_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    packet[field] = value
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_json_safe_copy_preserves_metadata_only_intake_packets_and_blocks_unsafe_structures():
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    packet["normalized_evidence_preparation_records"][0]["blocked_conditions"] = {"set", "values"}
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    safe_packet = norm.to_mlcf_normalized_evidence_packet_from_intake_preparation_json_safe_v1(packet)
    assert isinstance(safe_packet["normalized_evidence_preparation_records"][0]["blocked_conditions"], list)
    assert json.dumps(safe_packet, sort_keys=True)


def test_summaries_are_bounded_and_metadata_only():
    packet = _preparation_packet("frontier_space_intake_to_normalized_evidence_preparation_packet")
    prep = packet["normalized_evidence_preparation_records"][0]
    assert len(prep["not_normalized_evidence_notice"]) <= 220
    assert len(prep["not_trusted_evidence_notice"]) <= 220
    assert len(prep["not_accepted_evidence_notice"]) <= 220
    assert len(prep["source_content_required_notice"]) <= 240


def test_blocked_record_not_converted_into_preparation_record():
    packet = _preparation_packet("blocked_intake_to_normalized_evidence_preparation_packet")
    bad = norm.build_mlcf_normalized_evidence_preparation_record_v1(packet["blocked_records"][0])
    bad["summary_status"] = "blocked_by_safety"
    packet["normalized_evidence_preparation_records"] = [bad]
    packet["preparation_record_count"] = 1
    packet["input_intake_record_count"] = 2
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert "blocked_record_not_blocked" in validation["blocked_labels"]


def test_operator_review_only_record_not_converted_into_preparation_record():
    packet = _preparation_packet("rf_excluded_intake_to_normalized_evidence_preparation_packet")
    bad = norm.build_mlcf_normalized_evidence_preparation_record_v1(packet["excluded_intake_records"][0])
    bad["summary_status"] = "excluded_needs_operator_review"
    packet["normalized_evidence_preparation_records"] = [bad]
    packet["preparation_record_count"] = 1
    packet["input_intake_record_count"] = 1 + packet["excluded_record_count"]
    validation = norm.validate_mlcf_normalized_evidence_packet_from_intake_preparation_v1(packet)
    assert validation["blocked"] is True
    assert "preparation_record_bad_summary_status" in validation["blocked_labels"]


def test_git_status_protected_files_unchanged():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
