from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.mlcf_searxng_source_locator_adapter_boundary as adapter
from weslr.mlcf_searxng_source_locator_adapter_boundary import (
    allowed_mlcf_searxng_adapter_input_fields_v1,
    allowed_mlcf_searxng_adapter_result_statuses_v1,
    build_initial_mlcf_searxng_source_locator_adapter_examples_v1,
    build_mlcf_locator_record_from_searxng_result_v1,
    build_mlcf_searxng_source_locator_adapter_packet_v1,
    summarize_mlcf_searxng_source_locator_adapter_packet_v1,
    to_mlcf_searxng_source_locator_adapter_packet_json_safe_v1,
    validate_mlcf_searxng_source_locator_adapter_packet_v1,
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
    return deepcopy(build_initial_mlcf_searxng_source_locator_adapter_examples_v1())


def _example(packet_id: str):
    for item in _examples():
        if item["adapter_packet_id"] == packet_id:
            return item
    raise AssertionError(f"missing example {packet_id}")


def test_required_apis_exist():
    names = [
        "allowed_mlcf_searxng_adapter_input_fields_v1",
        "allowed_mlcf_searxng_adapter_result_statuses_v1",
        "build_mlcf_searxng_source_locator_adapter_packet_v1",
        "build_mlcf_locator_record_from_searxng_result_v1",
        "validate_mlcf_searxng_source_locator_adapter_packet_v1",
        "summarize_mlcf_searxng_source_locator_adapter_packet_v1",
        "to_mlcf_searxng_source_locator_adapter_packet_json_safe_v1",
        "build_initial_mlcf_searxng_source_locator_adapter_examples_v1",
    ]
    for name in names:
        assert hasattr(adapter, name)
        assert callable(getattr(adapter, name))


def test_allowed_enums_are_exact_and_stable():
    assert allowed_mlcf_searxng_adapter_input_fields_v1() == (
        "title",
        "url",
        "domain",
        "snippet",
        "engine",
        "published_date",
        "score",
        "source_class_hint",
        "query_family",
    )
    assert allowed_mlcf_searxng_adapter_result_statuses_v1() == ("accepted", "rejected", "blocked", "invalid")


def test_canonical_examples_build_and_validate():
    examples = _examples()
    assert {item["adapter_packet_id"] for item in examples} == {
        "searxng_rf_wifi_standard_result_packet",
        "searxng_rf_public_paper_result_packet",
        "searxng_wifi_sensing_github_result_packet",
        "searxng_private_hidden_result_blocked_packet",
    }
    for example in examples:
        validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(example)
        summary = summarize_mlcf_searxng_source_locator_adapter_packet_v1(example)
        assert validation["valid"] is True
        assert summary["adapter_packet_id"] == example["adapter_packet_id"]
        assert summary["validation_posture"] == "valid"
        assert summary["summary_text"]
        assert len(summary["summary_text"]) <= 220


def test_official_standard_mapping_result():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    record = packet["locator_records"][0]
    assert record["source_class"] == "official_standard"
    assert record["authority_level_guess"] == "official_primary"
    assert record["evidence_role_guess"] == "definition_or_standard"
    assert packet["allowed_next_step"] == "operator_review"


def test_public_paper_mapping_result():
    packet = _example("searxng_rf_public_paper_result_packet")
    record = packet["locator_records"][0]
    assert record["source_class"] == "public_research_paper"
    assert record["authority_level_guess"] == "public_primary"
    assert record["evidence_role_guess"] == "prior_art"


def test_github_mapping_result():
    packet = _example("searxng_wifi_sensing_github_result_packet")
    record = packet["locator_records"][0]
    assert record["source_class"] == "github_repository"
    assert record["authority_level_guess"] == "implementation_evidence"
    assert record["evidence_role_guess"] == "implementation_reference"
    assert "implementation evidence only" in record["relevance_reason"].lower()

    blocked = deepcopy(record)
    blocked["authority_level_guess"] = "official_primary"
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(
        {**packet, "locator_records": [blocked]}
    )
    assert validation["blocked"] is True
    assert any("github_locator_claims_official_science_authority" in label for label in validation["blocked_labels"])


def test_blocked_private_hidden_mapping_result():
    packet = _example("searxng_private_hidden_result_blocked_packet")
    record = packet["locator_records"][0]
    assert record["source_class"] == "blocked_sensitive_source"
    assert record["allowed_next_step"] == "blocked_by_safety"
    assert record["authority_level_guess"] == "blocked"


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("raw_content", "full body", "unsupported_input_fields"),
        ("full_text", "entire page", "unsupported_input_fields"),
        ("downloaded_content", "bytes", "unsupported_input_fields"),
    ],
)
def test_unsupported_raw_content_fields_fail_closed(field, value, expected_label):
    packet = build_mlcf_searxng_source_locator_adapter_packet_v1(
        adapter_packet_id="bad_raw_content_packet",
        science_direction_id="science",
        science_direction_summary="summary",
        query_used="query",
        query_family="family",
        searxng_results=[
            {
                "title": "Example",
                "url": "https://example.invalid",
                "domain": "example.invalid",
                "snippet": "snippet",
                "engine": "searxng",
                "published_date": "2024-01-01",
                "score": 0.1,
                "source_class_hint": "public_research_paper",
                "query_family": "family",
                field: value,
            }
        ],
    )
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["valid"] is True
    assert expected_label in json.dumps(packet["rejected_results"])
    assert packet["rejected_results"]
    assert not packet["locator_records"]
    assert packet["allowed_next_step"] == "blocked_by_safety"


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("snippet", "credential token cookie api key private hidden protected", "unsafe_hidden_private_protected_marker"),
        ("url", "https://example.invalid/private/hidden?token=abc", "unsafe_hidden_private_protected_marker"),
        ("title", "secret hidden protected result", "unsafe_hidden_private_protected_marker"),
    ],
)
def test_credential_token_cookie_api_key_markers_fail_closed(field, value, expected_label):
    packet = build_mlcf_searxng_source_locator_adapter_packet_v1(
        adapter_packet_id="bad_marker_packet",
        science_direction_id="science",
        science_direction_summary="summary",
        query_used="query",
        query_family="family",
        searxng_results=[
            {
                "title": "Example",
                "url": "https://example.invalid",
                "domain": "example.invalid",
                "snippet": "snippet",
                "engine": "searxng",
                "published_date": "2024-01-01",
                "score": 0.1,
                "source_class_hint": "public_research_paper",
                "query_family": "family",
                field: value,
            }
        ],
    )
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["locator_records"][0]["source_class"] == "blocked_sensitive_source"
    assert packet["allowed_next_step"] == "blocked_by_safety"


def test_unsafe_authority_flags_fail_closed():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["authority_status"]["searxng_call_authority"] = True
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_authority_flag:searxng_call_authority" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "authority_field",
    [
        "web_call_authority",
        "github_call_authority",
        "searxng_call_authority",
        "source_fetching_authority",
        "source_summary_authority",
    ],
)
def test_web_github_searxng_and_source_fetching_summary_authority_fail_closed(authority_field):
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "authority_field",
    [
        "source_ingestion_authorized",
        "raw_retention_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "discovery_claim_authorized",
        "proof_claim_authorized",
        "agi_claim_authorized",
        "benchmark_claim_authorized",
        "public_science_claim_authorized",
    ],
)
def test_ingestion_raw_retention_and_claim_authority_fail_closed(authority_field):
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["authority_status"][authority_field] = True
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "field, text, expected_label",
    [
        ("query_used", ".weslr implied", "unsafe_weslr_io_implication"),
        ("science_direction_summary", "database write implication", "unsafe_database_write_implication"),
        ("operator_review_need", "memory mutation implication", "unsafe_memory_project_mutation_implication"),
        ("blocked_conditions", ["behavior pack promotion implication"], "unsafe_behavior_pack_promotion_implication"),
        ("science_direction_summary", "public science discovery proof benchmark agi claim", "unsafe_claim_language"),
    ],
)
def test_weslr_database_memory_project_behavior_pack_and_claim_implications_fail_closed(field, text, expected_label):
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet[field] = text
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_cross_user_leakage_fails_closed():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["science_direction_summary"] = "cross-user leakage implication"
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_claim_language" in validation["blocked_labels"] or any("cross-user" in label for label in validation["blocked_labels"])


def test_hidden_private_protected_markers_fail_closed():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["science_direction_summary"] = "private hidden protected marker"
    validation = validate_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_hidden_private_protected_marker" in validation["blocked_labels"]


def test_json_safe_copy_preserves_locator_metadata_and_blocks_unsafe_structures():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["locator_records"][0]["authority_status"]["nested"] = {1, 2}
    packet["blocked_results"].append({"x": {"y": object()}})
    safe = to_mlcf_searxng_source_locator_adapter_packet_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)
    assert safe["locator_records"][0]["authority_status"]["nested"] == [1, 2]
    assert isinstance(safe["blocked_results"][-1]["x"]["y"], str)


def test_summaries_are_bounded_and_metadata_only():
    packet = _example("searxng_rf_wifi_standard_result_packet")
    packet["science_direction_summary"] = "x" * 500
    summary = summarize_mlcf_searxng_source_locator_adapter_packet_v1(packet)
    assert summary["validation_posture"] == "valid"
    assert len(summary["summary_text"]) <= 220


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
