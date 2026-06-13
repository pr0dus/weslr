from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_source_locator_organization_review_packet as review
from weslr.mlcf_metadata_only_source_locator_record import build_mlcf_metadata_only_source_locator_record_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _examples():
    return deepcopy(review.build_initial_mlcf_source_locator_organization_review_packet_examples_v1())


def _example(review_packet_id: str):
    for item in _examples():
        if item["review_packet_id"] == review_packet_id:
            return item
    raise AssertionError(f"missing example {review_packet_id}")


def _valid_ready_record(source_class: str = "official_standard"):
    return build_mlcf_metadata_only_source_locator_record_v1(
        locator_id=f"{source_class}_ready_locator",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        query_family="rf_material_floorplan_source_locator",
        source_class=source_class,
        candidate_title="Ready locator record",
        candidate_url_or_identifier="https://example.invalid/ready/locator",
        candidate_domain="example.invalid",
        authority_level_guess="official_primary" if source_class != "github_repository" else "implementation_evidence",
        evidence_role_guess="definition_or_standard" if source_class == "official_standard" else "implementation_reference",
        relevance_reason=(
            "Metadata-only official locator ready for authorized summary."
            if source_class != "github_repository"
            else "GitHub implementation evidence only."
        ),
        freshness_status="current",
        access_license_status="open",
        privacy_status="low",
        operator_review_need="Operator review required before any source access.",
        allowed_next_step="operator_review",
        blocked_conditions=["No source access", "No ingestion"],
    )


def test_required_apis_exist():
    names = [
        "allowed_mlcf_locator_review_bucket_ids_v1",
        "allowed_mlcf_locator_review_packet_next_steps_v1",
        "allowed_mlcf_locator_review_decision_reasons_v1",
        "classify_mlcf_locator_record_for_review_v1",
        "build_mlcf_source_locator_organization_review_packet_v1",
        "validate_mlcf_source_locator_organization_review_packet_v1",
        "summarize_mlcf_source_locator_organization_review_packet_v1",
        "to_mlcf_source_locator_organization_review_packet_json_safe_v1",
        "build_initial_mlcf_source_locator_organization_review_packet_examples_v1",
    ]
    for name in names:
        assert hasattr(review, name)
        assert callable(getattr(review, name))


def test_allowed_enums_are_exact_and_stable():
    assert review.allowed_mlcf_locator_review_bucket_ids_v1() == (
        "keep_for_operator_review",
        "ready_for_authorized_metadata_only_source_summary",
        "needs_repair",
        "reject",
        "blocked",
        "duplicate_or_low_value",
    )
    assert review.allowed_mlcf_locator_review_packet_next_steps_v1() == (
        "operator_review",
        "prepare_authorized_metadata_only_source_summary",
        "repair_locator_records",
        "reject_locator_batch",
        "blocked_by_safety",
    )
    assert review.allowed_mlcf_locator_review_decision_reasons_v1() == (
        "keep_for_operator_review",
        "ready_for_authorized_metadata_only_source_summary",
        "needs_repair_missing_or_invalid_metadata",
        "reject_locator",
        "blocked_private_hidden_or_protected_source",
        "duplicate_or_low_value",
        "unsafe_authority_or_claim_language",
    )


def test_canonical_examples_build():
    examples = _examples()
    assert {item["review_packet_id"] for item in examples} == {
        "rf_material_floorplan_locator_review_packet",
        "frontier_space_fixture_locator_review_packet",
        "broken_locator_review_packet",
    }


def test_canonical_examples_validate_and_summarize():
    for example in _examples():
        validation = review.validate_mlcf_source_locator_organization_review_packet_v1(example)
        summary = review.summarize_mlcf_source_locator_organization_review_packet_v1(example)
        assert summary["review_packet_id"] == example["review_packet_id"]
        assert summary["science_direction_id"] == example["science_direction_id"]
        assert len(summary["summary_text"]) <= 220
        if example["review_packet_id"] == "broken_locator_review_packet":
            assert validation["blocked"] is True
        else:
            assert validation["valid"] is True


def test_rf_packet_organizes_correctly():
    packet = _example("rf_material_floorplan_locator_review_packet")
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["blocked_locator_count"] == 1
    assert packet["bucket_counts"]["blocked"] == 1
    assert packet["bucket_counts"]["keep_for_operator_review"] >= 1
    assert packet["bucketed_locator_records"]["blocked"][0]["source_class"] == "blocked_private_or_hidden_source"
    assert any(r["source_class"] == "github_repository" for r in packet["bucketed_locator_records"]["keep_for_operator_review"])


def test_frontier_space_fixture_packet_organizes_without_discovery_claims():
    packet = _example("frontier_space_fixture_locator_review_packet")
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["bucket_counts"]["blocked"] == 1
    assert packet["bucketed_locator_records"]["blocked"][0]["source_class"] == "blocked_private_or_hidden_source"
    assert "unsafe_claim_language" not in validation["blocked_labels"]


def test_duplicate_and_ready_bucket_routing():
    ready_record = _valid_ready_record("official_standard")
    duplicate_record = deepcopy(ready_record)
    packet = review.build_mlcf_source_locator_organization_review_packet_v1(
        review_packet_id="duplicate_ready_packet",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        science_direction_summary="Metadata-only organization packet for ready and duplicate records.",
        source_packet_origin="validated_metadata_only_source_locator_records",
        locator_records=[ready_record, duplicate_record],
    )
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["bucket_counts"]["ready_for_authorized_metadata_only_source_summary"] == 1
    assert packet["bucket_counts"]["duplicate_or_low_value"] == 1
    assert packet["allowed_next_step"] == "prepare_authorized_metadata_only_source_summary"
    assert packet["safe_metadata"]["source_summary_authorized"] is False


def test_github_remains_implementation_evidence_only():
    github_record = _valid_ready_record("github_repository")
    packet = review.build_mlcf_source_locator_organization_review_packet_v1(
        review_packet_id="github_ready_packet",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        science_direction_summary="Metadata-only organization packet for implementation evidence.",
        source_packet_origin="validated_metadata_only_source_locator_records",
        locator_records=[github_record],
    )
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["bucket_counts"]["ready_for_authorized_metadata_only_source_summary"] == 1
    assert packet["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"][0]["source_class"] == "github_repository"
    assert "implementation" in packet["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"][0]["relevance_reason"].lower()


def test_broken_records_go_to_needs_repair_or_blocked():
    packet = _example("broken_locator_review_packet")
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["blocked"] is True
    assert packet["bucket_counts"]["needs_repair"] >= 1
    assert packet["blocked_locator_count"] >= 1
    assert validation["blocked_labels"]


def test_unsafe_authority_flags_fail_closed():
    packet = _example("rf_material_floorplan_locator_review_packet")
    packet["authority_status"]["source_ingestion_authorized"] = True
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag:source_ingestion_authorized" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, marker, expected_label",
    [
        ("science_direction_summary", "WESLR discovered a candidate object", "unsafe_claim_language"),
        ("organization_notes", ".weslr writes are not allowed", "unsafe_weslr_io_implication"),
        ("organization_notes", "database write implication", "unsafe_database_write_implication"),
        ("organization_notes", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("organization_notes", "behavior pack promotion implication", "unsafe_behavior_pack_promotion_implication"),
    ],
)
def test_unsafe_claim_and_implication_language_fail_closed(field, marker, expected_label):
    packet = _example("frontier_space_fixture_locator_review_packet")
    packet[field] = marker
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_non_json_safe_output_fails_closed_and_safe_copy_preserves_metadata():
    packet = _example("rf_material_floorplan_locator_review_packet")
    packet["bucketed_locator_records"]["keep_for_operator_review"][0]["blocked_conditions"] = {"unsafe", "set"}
    validation = review.validate_mlcf_source_locator_organization_review_packet_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]

    safe_packet = review.to_mlcf_source_locator_organization_review_packet_json_safe_v1(packet)
    assert safe_packet["bucketed_locator_records"]["keep_for_operator_review"][0]["blocked_conditions"] == ["unsafe", "set"] or safe_packet["bucketed_locator_records"]["keep_for_operator_review"][0]["blocked_conditions"] == ["set", "unsafe"]


def test_summary_is_bounded_and_metadata_only():
    packet = _example("frontier_space_fixture_locator_review_packet")
    summary = review.summarize_mlcf_source_locator_organization_review_packet_v1(packet)
    assert summary["validation_posture"] == "valid"
    assert len(summary["summary_text"]) <= 220
    assert "raw" not in summary["summary_text"].lower()


def test_protected_files_unchanged():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""

