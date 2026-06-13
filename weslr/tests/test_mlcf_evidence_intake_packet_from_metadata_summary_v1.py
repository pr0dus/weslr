from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_evidence_intake_packet_from_metadata_summary as intake
from weslr.mlcf_authorized_metadata_only_source_summary import (
    build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1,
    build_mlcf_authorized_metadata_only_source_summary_packet_v1,
)
from weslr.mlcf_metadata_only_source_locator_record import build_mlcf_metadata_only_source_locator_record_v1
from weslr.mlcf_source_locator_organization_review_packet import build_initial_mlcf_source_locator_organization_review_packet_examples_v1

from weslr.mlcf_evidence_intake_packet_from_metadata_summary import build_mlcf_evidence_intake_preparation_record_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _source_summary_examples():
    return deepcopy(build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1())


def _summary_packet(packet_id: str):
    for packet in _source_summary_examples():
        if packet["summary_packet_id"] == packet_id:
            return packet
    raise AssertionError(f"missing source-summary packet {packet_id}")


def _review_packets():
    return deepcopy(build_initial_mlcf_source_locator_organization_review_packet_examples_v1())


def _rf_operator_review_only_source_summary_packet():
    rf_review = next(p for p in _review_packets() if p["review_packet_id"] == "rf_material_floorplan_locator_review_packet")
    return build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="rf_operator_review_only_metadata_summary_packet",
        science_direction_id=rf_review["science_direction_id"],
        science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
        source_locator_review_packet_ref=rf_review["review_packet_id"],
        review_records=rf_review["bucketed_locator_records"]["keep_for_operator_review"],
        metadata_summary_scope="ready_records_only",
    )


def _blocked_only_source_summary_packet():
    frontier_review = next(p for p in _review_packets() if p["review_packet_id"] == "frontier_space_fixture_locator_review_packet")
    return build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="blocked_locator_metadata_summary_packet",
        science_direction_id=frontier_review["science_direction_id"],
        science_direction_summary="Metadata-only blocked locator packet.",
        source_locator_review_packet_ref=frontier_review["review_packet_id"],
        review_records=frontier_review["bucketed_locator_records"]["blocked"],
        metadata_summary_scope="ready_records_only",
    )


def _frontier_ready_source_summary_packet():
    return _summary_packet("frontier_space_ready_metadata_summary_packet")


def _frontier_ready_input_packet_with_blocked_and_excluded():
    packet = _frontier_ready_source_summary_packet()
    frontier_review = next(p for p in _review_packets() if p["review_packet_id"] == "frontier_space_fixture_locator_review_packet")
    packet["excluded_records"] = deepcopy(frontier_review["bucketed_locator_records"]["keep_for_operator_review"])
    packet["blocked_records"] = deepcopy(frontier_review["bucketed_locator_records"]["blocked"])
    packet["summary_record_count"] = len(packet["metadata_only_source_summaries"])
    packet["excluded_record_count"] = len(packet["excluded_records"])
    packet["blocked_record_count"] = len(packet["blocked_records"])
    packet["input_metadata_summary_count"] = packet["summary_record_count"] + packet["excluded_record_count"] + packet["blocked_record_count"]
    return packet


def _synthetic_github_ready_summary_packet():
    frontier = _frontier_ready_source_summary_packet()
    github_record = deepcopy(frontier["metadata_only_source_summaries"][0])
    github_record.update(
        {
            "metadata_summary_id": "github_ready_metadata_summary",
            "source_class": "github_repository",
            "authority_level_guess": "implementation_evidence",
            "evidence_role_guess": "implementation_reference",
            "candidate_title": "GitHub implementation evidence summary candidate",
            "candidate_url_or_identifier": "https://github.com/example/repo",
            "candidate_domain": "github.com",
            "metadata_summary_text": "Metadata-only GitHub implementation evidence summary candidate.",
            "summary_status": "metadata_summary_prepared",
        }
    )
    frontier["metadata_only_source_summaries"] = [github_record]
    frontier["summary_record_count"] = 1
    frontier["excluded_records"] = []
    frontier["excluded_record_count"] = 0
    frontier["blocked_records"] = []
    frontier["blocked_record_count"] = 0
    frontier["input_metadata_summary_count"] = 1
    frontier["source_class_distribution"] = {"github_repository": 1}
    frontier["authority_distribution"] = {"implementation_evidence": 1}
    frontier["evidence_role_distribution"] = {"implementation_reference": 1}
    frontier["intake_status"] = "evidence_intake_packet_prepared"
    frontier["allowed_next_step"] = "prepare_normalized_evidence_packet"
    frontier["evidence_intake_packet_id"] = "github_metadata_summary_to_evidence_intake_packet"
    frontier["source_summary_packet_ref"] = "synthetic_github_summary_packet"
    return frontier


def _preparation_packet(packet_id: str):
    if packet_id == "frontier_space_metadata_summary_to_evidence_intake_packet":
        source_packet = _frontier_ready_input_packet_with_blocked_and_excluded()
    elif packet_id == "rf_metadata_summary_operator_review_excluded_packet":
        source_packet = _rf_operator_review_only_source_summary_packet()
    elif packet_id == "blocked_metadata_summary_to_evidence_intake_packet":
        source_packet = _blocked_only_source_summary_packet()
    else:
        raise AssertionError(packet_id)
    examples = intake.build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1()
    for packet in examples:
        if packet["evidence_intake_packet_id"] == packet_id:
            return deepcopy(packet)
    raise AssertionError(f"missing intake packet {packet_id}")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_evidence_intake_packet_statuses_v1",
        "allowed_mlcf_evidence_intake_packet_next_steps_v1",
        "allowed_mlcf_evidence_intake_source_kinds_v1",
        "allowed_mlcf_evidence_intake_preparation_roles_v1",
        "build_mlcf_evidence_intake_packet_from_metadata_summary_v1",
        "build_mlcf_evidence_intake_preparation_record_v1",
        "validate_mlcf_evidence_intake_packet_from_metadata_summary_v1",
        "summarize_mlcf_evidence_intake_packet_from_metadata_summary_v1",
        "to_mlcf_evidence_intake_packet_from_metadata_summary_json_safe_v1",
        "build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1",
    ]
    for name in names:
        assert hasattr(intake, name)
        assert callable(getattr(intake, name))


def test_allowed_enums_are_exact_and_stable():
    assert intake.allowed_mlcf_evidence_intake_packet_statuses_v1() == (
        "evidence_intake_packet_prepared",
        "excluded_needs_operator_review",
        "excluded_needs_repair",
        "excluded_blocked_by_safety",
        "blocked_by_safety",
    )
    assert intake.allowed_mlcf_evidence_intake_packet_next_steps_v1() == (
        "operator_review",
        "prepare_normalized_evidence_packet",
        "repair_metadata_summary_records",
        "reject_evidence_intake_packet",
        "blocked_by_safety",
    )
    assert intake.allowed_mlcf_evidence_intake_source_kinds_v1() == (
        "official_standard_metadata",
        "official_government_or_agency_metadata",
        "official_vendor_documentation_metadata",
        "public_research_paper_metadata",
        "public_dataset_metadata",
        "github_repository_metadata",
        "public_lab_or_university_artifact_metadata",
        "public_benchmark_or_test_suite_metadata",
        "blocked_source_metadata",
        "unknown_source_metadata",
    )
    assert intake.allowed_mlcf_evidence_intake_preparation_roles_v1() == (
        "definition_or_standard_preparation",
        "measurement_data_preparation",
        "prior_art_preparation",
        "implementation_reference_preparation",
        "replication_target_preparation",
        "counterexample_source_preparation",
        "domain_context_preparation",
        "constraint_source_preparation",
        "not_authoritative_context_preparation",
    )


def test_canonical_examples_build_and_validate():
    examples = intake.build_initial_mlcf_evidence_intake_packet_from_metadata_summary_examples_v1()
    assert {item["evidence_intake_packet_id"] for item in examples} == {
        "frontier_space_metadata_summary_to_evidence_intake_packet",
        "rf_metadata_summary_operator_review_excluded_packet",
        "blocked_metadata_summary_to_evidence_intake_packet",
    }
    for example in examples:
        validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert intake.summarize_mlcf_evidence_intake_packet_from_metadata_summary_v1(example)["evidence_intake_packet_id"] == example["evidence_intake_packet_id"]


def test_frontier_space_metadata_summary_intake_result():
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 3
    assert packet["excluded_record_count"] == 0
    assert packet["blocked_record_count"] == 0
    assert packet["intake_status"] == "evidence_intake_packet_prepared"
    assert packet["allowed_next_step"] == "prepare_normalized_evidence_packet"
    assert all(item["source_kind_hint"].endswith("_metadata") for item in packet["evidence_intake_preparation_records"])
    assert all(item["not_evidence_notice"] for item in packet["evidence_intake_preparation_records"])
    assert all(item["source_summary_status"] == "metadata_summary_prepared" for item in packet["evidence_intake_preparation_records"])


def test_rf_excluded_record_result():
    packet = _preparation_packet("rf_metadata_summary_operator_review_excluded_packet")
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 0
    assert packet["excluded_record_count"] == 3
    assert packet["blocked_record_count"] == 0
    assert packet["intake_status"] == "excluded_needs_operator_review"
    assert packet["allowed_next_step"] == "operator_review"
    assert all(item["summary_status"] == "excluded_needs_operator_review" for item in packet["excluded_summary_records"])


def test_blocked_record_result():
    packet = _preparation_packet("blocked_metadata_summary_to_evidence_intake_packet")
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["valid"] is True
    assert packet["preparation_record_count"] == 0
    assert packet["blocked_record_count"] == 1
    assert packet["intake_status"] == "blocked_by_safety"
    assert packet["allowed_next_step"] == "blocked_by_safety"
    assert packet["blocked_records"][0]["summary_status"] == "blocked_by_safety"


def test_github_stays_implementation_evidence_only():
    packet = _synthetic_github_ready_summary_packet()
    prep = intake.build_mlcf_evidence_intake_preparation_record_v1(packet["metadata_only_source_summaries"][0])
    assert prep["source_kind_hint"] == "github_repository_metadata"
    assert prep["evidence_preparation_role"] == "implementation_reference_preparation"
    assert "official science" not in prep["not_evidence_notice"].lower()
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(
        intake.build_mlcf_evidence_intake_packet_from_metadata_summary_v1(metadata_summary_packet=packet)
    )
    assert validation["valid"] is True


def test_frontier_fixture_remains_non_claim_metadata_routing():
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    assert all("discovery" not in item["not_evidence_notice"].lower() for item in packet["evidence_intake_preparation_records"])
    assert all("proof" not in item["not_evidence_notice"].lower() for item in packet["evidence_intake_preparation_records"])
    assert all("public science" not in item["not_evidence_notice"].lower() for item in packet["evidence_intake_preparation_records"])


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
        ("accepted_candidate", "accepted", "preparation_record_contains_source_content"),
        ("proposal_payload", "proposal", "preparation_record_contains_source_content"),
    ],
)
def test_source_content_boundary(field, value, expected_label):
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    packet["evidence_intake_preparation_records"][0][field] = value
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
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
        ("candidate_graph_membership_authorized", True, "unsafe_authority_flag:candidate_graph_membership_authorized"),
        ("proposal_submission_authorized", True, "unsafe_authority_flag:proposal_submission_authorized"),
        ("proposal_application_authorized", True, "unsafe_authority_flag:proposal_application_authorized"),
    ],
)
def test_unsafe_authority_flags_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    packet["authority_status"][field] = value
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
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
        ("normalization_plan", "proposal application", "unsafe_claim_language"),
    ],
)
def test_unsafe_claim_language_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    packet["evidence_intake_preparation_records"][0][field] = value
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("intake_scope", ".weslr scope", "unsafe_weslr_io_implication"),
        ("intake_scope", "database write implication", "unsafe_database_write_implication"),
        ("intake_scope", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("intake_scope", "behavior pack promotion", "unsafe_behavior_pack_promotion_implication"),
    ],
)
def test_weslr_database_memory_project_mutation_implications_fail_closed(field, value, expected_label):
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    packet[field] = value
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_json_safe_copy_preserves_metadata_only_intake_packets_and_blocks_unsafe_structures():
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    packet["evidence_intake_preparation_records"][0]["blocked_conditions"] = {"set", "values"}
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"] or "preparation_record_contains_source_content" not in validation["blocked_labels"]
    safe_packet = intake.to_mlcf_evidence_intake_packet_from_metadata_summary_json_safe_v1(packet)
    assert isinstance(safe_packet["evidence_intake_preparation_records"][0]["blocked_conditions"], list)
    assert json.dumps(safe_packet, sort_keys=True)


def test_summaries_are_bounded_and_metadata_only():
    packet = _preparation_packet("frontier_space_metadata_summary_to_evidence_intake_packet")
    prep = packet["evidence_intake_preparation_records"][0]
    assert len(prep["not_evidence_notice"]) <= 240
    assert len(prep["limitations"]) <= 240
    assert len(prep["provenance_stub"]) <= 240
    assert "raw" not in prep["not_evidence_notice"].lower()


def test_blocked_record_not_converted_into_preparation_record():
    packet = _preparation_packet("blocked_metadata_summary_to_evidence_intake_packet")
    bad = build_mlcf_evidence_intake_preparation_record_v1(packet["blocked_records"][0])
    bad["source_summary_status"] = "blocked_by_safety"
    packet["evidence_intake_preparation_records"] = [bad]
    packet["preparation_record_count"] = 1
    packet["input_metadata_summary_count"] = 2
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["blocked"] is True
    assert "preparation_record_not_from_ready_summary" in validation["blocked_labels"]


def test_operator_review_only_record_not_converted_into_preparation_record():
    packet = _preparation_packet("rf_metadata_summary_operator_review_excluded_packet")
    bad = build_mlcf_evidence_intake_preparation_record_v1(packet["excluded_summary_records"][0])
    bad["source_summary_status"] = packet["excluded_summary_records"][0]["summary_status"]
    packet["evidence_intake_preparation_records"] = [bad]
    packet["preparation_record_count"] = 1
    packet["input_metadata_summary_count"] = 1 + packet["excluded_record_count"]
    validation = intake.validate_mlcf_evidence_intake_packet_from_metadata_summary_v1(packet)
    assert validation["blocked"] is True
    assert "preparation_record_not_from_ready_summary" in validation["blocked_labels"]


def test_git_status_protected_files_unchanged():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
