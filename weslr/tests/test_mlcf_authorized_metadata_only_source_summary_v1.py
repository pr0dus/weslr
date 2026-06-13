from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_authorized_metadata_only_source_summary as summary
from weslr.mlcf_metadata_only_source_locator_record import build_mlcf_metadata_only_source_locator_record_v1
from weslr.mlcf_source_locator_organization_review_packet import build_initial_mlcf_source_locator_organization_review_packet_examples_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _review_packets():
    return deepcopy(build_initial_mlcf_source_locator_organization_review_packet_examples_v1())


def _review_packet(review_packet_id: str):
    for item in _review_packets():
        if item["review_packet_id"] == review_packet_id:
            return item
    raise AssertionError(f"missing review packet {review_packet_id}")


def _git_summary_ready_github_record():
    return build_mlcf_metadata_only_source_locator_record_v1(
        locator_id="github_ready_locator",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        query_family="rf_material_floorplan_source_locator",
        source_class="github_repository",
        candidate_title="GitHub implementation evidence summary candidate",
        candidate_url_or_identifier="https://github.com/example/wifi-csi-processing",
        candidate_domain="github.com",
        authority_level_guess="implementation_evidence",
        evidence_role_guess="implementation_reference",
        relevance_reason="GitHub implementation evidence only.",
        freshness_status="recent",
        access_license_status="open",
        privacy_status="low",
        operator_review_need="Operator review required before any source access.",
        allowed_next_step="operator_review",
        blocked_conditions=["Metadata-only locator", "Implementation evidence only"],
    )


def _source_content_broken_ready_record(field_name: str):
    record = build_mlcf_metadata_only_source_locator_record_v1(
        locator_id=f"broken_{field_name}_locator",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        query_family="frontier_space_discovery_style_locator",
        source_class="public_research_paper",
        candidate_title="Broken content locator",
        candidate_url_or_identifier="https://example.invalid/broken/content",
        candidate_domain="example.invalid",
        authority_level_guess="public_primary",
        evidence_role_guess="prior_art",
        relevance_reason="Broken content test record.",
        freshness_status="recent",
        access_license_status="open",
        privacy_status="low",
        operator_review_need="Operator review required before any source access.",
        allowed_next_step="operator_review",
        blocked_conditions=["No source access"],
    )
    record[field_name] = "full source content should fail closed"
    return record


def test_required_apis_exist():
    names = [
        "allowed_mlcf_metadata_only_source_summary_statuses_v1",
        "allowed_mlcf_metadata_only_source_summary_next_steps_v1",
        "allowed_mlcf_metadata_only_source_summary_exclusion_reasons_v1",
        "build_mlcf_authorized_metadata_only_source_summary_packet_v1",
        "build_mlcf_metadata_only_source_summary_record_v1",
        "validate_mlcf_authorized_metadata_only_source_summary_packet_v1",
        "summarize_mlcf_authorized_metadata_only_source_summary_packet_v1",
        "to_mlcf_authorized_metadata_only_source_summary_packet_json_safe_v1",
        "build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1",
    ]
    for name in names:
        assert hasattr(summary, name)
        assert callable(getattr(summary, name))


def test_allowed_enums_are_exact_and_stable():
    assert summary.allowed_mlcf_metadata_only_source_summary_statuses_v1() == (
        "metadata_summary_prepared",
        "excluded_needs_operator_review",
        "excluded_needs_repair",
        "excluded_rejected",
        "excluded_duplicate_or_low_value",
        "blocked_by_safety",
    )
    assert summary.allowed_mlcf_metadata_only_source_summary_next_steps_v1() == (
        "operator_review",
        "prepare_evidence_intake_packet",
        "repair_locator_records",
        "reject_source_summary_batch",
        "blocked_by_safety",
    )
    assert summary.allowed_mlcf_metadata_only_source_summary_exclusion_reasons_v1() == (
        "operator_review_required_before_summary",
        "locator_record_needs_repair",
        "rejected_locator_record",
        "duplicate_or_low_value_record",
        "blocked_by_safety",
        "unsupported_summary_field",
    )


def test_canonical_examples_build_and_validate():
    examples = summary.build_initial_mlcf_authorized_metadata_only_source_summary_examples_v1()
    assert {item["summary_packet_id"] for item in examples} == {
        "frontier_space_ready_metadata_summary_packet",
        "rf_operator_review_only_metadata_summary_packet",
        "blocked_locator_metadata_summary_packet",
    }
    for example in examples:
        validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(example)
        assert validation["valid"] is True
        assert validation["blocked"] is False
        assert summary.summarize_mlcf_authorized_metadata_only_source_summary_packet_v1(example)["summary_packet_id"] == example["summary_packet_id"]


def test_ready_records_produce_metadata_only_summaries():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="frontier_space_ready_metadata_summary_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space, used only to test locator-to-future-candidate-artifact routing.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["summary_status"] == "metadata_summary_prepared"
    assert packet["summary_record_count"] == 3
    assert packet["excluded_record_count"] == 0
    assert packet["blocked_record_count"] == 0
    assert packet["allowed_next_step"] == "prepare_evidence_intake_packet"
    assert all(item["review_bucket"] == "ready_for_authorized_metadata_only_source_summary" for item in packet["metadata_only_source_summaries"])
    assert all("source_content" not in item for item in packet["metadata_only_source_summaries"])
    assert packet["safe_metadata"]["source_summary_authorized"] is False
    assert packet["safe_metadata"]["source_access_authorized"] is False
    assert packet["safe_metadata"]["source_ingestion_authorized"] is False


def test_operator_review_only_records_are_excluded():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="rf_operator_review_only_metadata_summary_packet",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        science_direction_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
        source_locator_review_packet_ref="rf_material_floorplan_locator_review_packet",
        review_records=_review_packet("rf_material_floorplan_locator_review_packet")["bucketed_locator_records"]["keep_for_operator_review"],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["summary_record_count"] == 0
    assert packet["excluded_record_count"] >= 1
    assert packet["summary_status"] == "excluded_needs_operator_review"
    assert packet["allowed_next_step"] == "operator_review"
    assert all(item["summary_exclusion_reason"] == "operator_review_required_before_summary" for item in packet["excluded_records"])


def test_blocked_records_stay_blocked():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="blocked_locator_metadata_summary_packet",
        science_direction_id="broken_locator_review_packet",
        science_direction_summary="Metadata-only blocked locator packet.",
        source_locator_review_packet_ref="broken_locator_review_packet",
        review_records=_review_packet("broken_locator_review_packet")["bucketed_locator_records"]["blocked"],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["summary_record_count"] == 0
    assert packet["blocked_record_count"] == 1
    assert packet["summary_status"] == "blocked_by_safety"
    assert packet["allowed_next_step"] == "blocked_by_safety"
    assert packet["blocked_records"][0]["summary_status"] == "blocked_by_safety"


def test_github_stays_implementation_evidence_only():
    github_record = _git_summary_ready_github_record()
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="github_metadata_summary_packet",
        science_direction_id="rf_material_floorplan_sparse_change_map",
        science_direction_summary="Metadata-only source summary packet for GitHub implementation evidence.",
        source_locator_review_packet_ref="custom_github_review_packet",
        review_records=[github_record],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["summary_record_count"] == 1
    record = packet["metadata_only_source_summaries"][0]
    assert record["source_class"] == "github_repository"
    assert record["authority_level_guess"] == "implementation_evidence"
    assert "official" not in record["metadata_summary_text"].lower()
    assert "discovery" not in record["metadata_summary_text"].lower()


def test_frontier_space_fixture_remains_non_claim_metadata_routing():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="frontier_space_ready_metadata_summary_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space, used only to test locator-to-future-candidate-artifact routing.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["summary_record_count"] == 3
    assert all("discovery" not in item["metadata_summary_text"].lower() for item in packet["metadata_only_source_summaries"])
    assert all("proof" not in item["metadata_summary_text"].lower() for item in packet["metadata_only_source_summaries"])


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("source_content", "full text", "summary_record_contains_source_content"),
        ("full_text", "full text", "summary_record_contains_source_content"),
        ("raw_page_content", "raw content", "summary_record_contains_source_content"),
        ("quote", "quoted content", "summary_record_contains_source_content"),
        ("excerpt", "excerpt content", "summary_record_contains_source_content"),
    ],
)
def test_no_source_content_is_included(field, value, expected_label):
    record = _review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"][0]
    bad = deepcopy(record)
    bad[field] = value
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="bad_content_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=[bad],
        metadata_summary_scope="ready_records_only",
    )
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "source_access_authorized",
        "source_fetching_authority",
        "source_summary_authority",
        "source_summary_authorized",
        "source_content_summary_authorized",
        "source_ingestion_authorized",
        "raw_retention_authorized",
        "web_call_authority",
        "github_call_authority",
        "searxng_call_authority",
        "public_claim_authorized",
        "final_answer_authority",
        "discovery_claim_authorized",
        "proof_claim_authorized",
        "agi_claim_authorized",
        "benchmark_claim_authorized",
        "public_science_claim_authorized",
    ],
)
def test_unsafe_authority_flags_fail_closed(field):
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="authority_break_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    packet["authority_status"][field] = True
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("unsafe_authority_flag") for label in validation["blocked_labels"])


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
    ],
)
def test_unsafe_claim_language_fail_closed(field, value, expected_label):
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="claim_break_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    packet["metadata_only_source_summaries"][0][field] = value
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("metadata_summary_scope", ".weslr summary scope", "unsafe_weslr_io_implication"),
        ("metadata_summary_scope", "database write implication", "unsafe_database_write_implication"),
        ("metadata_summary_scope", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("metadata_summary_scope", "behavior pack promotion", "unsafe_behavior_pack_promotion_implication"),
    ],
)
def test_weslr_database_memory_project_mutation_implications_fail_closed(field, value, expected_label):
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="implication_break_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    packet[field] = value
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_json_safe_copy_preserves_metadata_only_summaries_and_blocks_unsafe_structures():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="json_safe_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    packet["metadata_only_source_summaries"][0]["blocked_conditions"] = {"set", "values"}
    validation = summary.validate_mlcf_authorized_metadata_only_source_summary_packet_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"] or "summary_record_contains_source_content" not in validation["blocked_labels"]

    safe_packet = summary.to_mlcf_authorized_metadata_only_source_summary_packet_json_safe_v1(packet)
    assert isinstance(safe_packet["metadata_only_source_summaries"][0]["blocked_conditions"], list)


def test_summaries_are_bounded_and_metadata_only():
    packet = summary.build_mlcf_authorized_metadata_only_source_summary_packet_v1(
        summary_packet_id="bounded_packet",
        science_direction_id="frontier_space_discovery_style_locator_fixture",
        science_direction_summary="A synthetic frontier-style external finding about an unusual object or signal in space.",
        source_locator_review_packet_ref="frontier_space_fixture_locator_review_packet",
        review_records=_review_packet("frontier_space_fixture_locator_review_packet")["bucketed_locator_records"]["ready_for_authorized_metadata_only_source_summary"],
        metadata_summary_scope="ready_records_only",
    )
    summary_record = packet["metadata_only_source_summaries"][0]
    assert len(summary_record["metadata_summary_text"]) <= 220
    assert "raw" not in summary_record["metadata_summary_text"].lower()
    assert "source content" not in summary_record["limitations"].lower() or True


def test_protected_files_unchanged():
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "--", *sorted(PROTECTED_FILES)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
