from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import weslr.authorized_ingestion_boundary as boundary
from weslr.authorized_ingestion_boundary import (
    build_authorized_ingestion_boundary_packet_v1,
    build_initial_authorized_ingestion_boundary_examples_v1,
    summarize_authorized_ingestion_boundary_packet_v1,
    to_authorized_ingestion_boundary_json_safe_v1,
    validate_authorized_ingestion_boundary_packet_v1,
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
    "weslr/authorized_ingestion_boundary.py",
    "weslr/tests/test_authorized_ingestion_boundary_v1.py",
    "weslr/tests/release_gate_v1.py",
    "weslr/tests/test_cognitive_research_protocol_v1.py",
}


def _base_packet(**overrides):
    packet = build_authorized_ingestion_boundary_packet_v1(
        {
            "ingestion_boundary_id": "test_boundary",
            "requested_source_kind": "owner_supplied_document",
            "requested_access_mode": "owner_supplied_summary",
            "authorization_state": "operator_supplied_summary_only",
            "source_scope": "metadata-only source scope for testing",
            "owner_or_operator_request_status": "operator approved metadata-only handling",
            "privacy_sensitivity": "low",
            "safety_sensitivity": "low",
            "cross_user_or_tenant_risk": "low",
            "raw_content_handling": "summary_only",
            "retention_policy": "no raw retention",
            "allowed_output_form": "metadata_only",
            "evidence_intake_link_allowed": False,
            "operator_review_required": True,
            "blocked_reason": "metadata-only boundary",
            "required_redactions": [],
            "forbidden_interpretations": list(boundary._CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
            "authority_status": boundary._build_default_authority_status(),
            "safe_metadata": {
                **boundary._build_default_safe_metadata(),
                "ingestion_authorized": False,
                "evidence_intake_link_allowed": False,
                "raw_retention_allowed": False,
                "public_claim_allowed": False,
                "final_answer_authority": False,
                "discovery_preservation": True,
            },
            "search_direction_allowed": True,
            "search_direction_blocked_reason": "",
            "ingestion_authorized": False,
            "raw_retention_allowed": False,
            "public_claim_allowed": False,
            "final_answer_authority": False,
            "discovery_domains_preserved": list(boundary.allowed_discovery_domains_v1()),
        },
        **overrides,
    )
    return packet


@pytest.mark.parametrize(
    "getter, expected",
    [
        (boundary.allowed_ingestion_authorization_states_v1, boundary.allowed_ingestion_authorization_states_v1()),
        (boundary.allowed_source_access_modes_v1, boundary.allowed_source_access_modes_v1()),
        (boundary.allowed_raw_content_handling_states_v1, boundary.allowed_raw_content_handling_states_v1()),
        (boundary.allowed_ingestion_output_forms_v1, boundary.allowed_ingestion_output_forms_v1()),
        (boundary.allowed_discovery_domains_v1, boundary.allowed_discovery_domains_v1()),
    ],
)
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


def test_canonical_examples_validate_and_summarize():
    examples = build_initial_authorized_ingestion_boundary_examples_v1()
    assert [example["ingestion_boundary_id"] for example in examples] == [
        "owner_summary_metadata_only_boundary",
        "broad_search_direction_not_ingestion_boundary",
    ]
    for example in examples:
        validation = validate_authorized_ingestion_boundary_packet_v1(example)
        summary = summarize_authorized_ingestion_boundary_packet_v1(example)
        assert validation["blocked"] is False
        assert validation["valid"] is True
        assert summary["validation_posture"] == "valid"
        assert summary["blocked_reason"]
        assert summary["discovery_domains_count"] == len(boundary.allowed_discovery_domains_v1())


def test_broad_search_direction_remains_independent_of_ingestion_authority():
    packet = _base_packet(search_direction_allowed=False, ingestion_authorized=False)
    validation = validate_authorized_ingestion_boundary_packet_v1(packet)
    assert validation["blocked"] is False

    broad_packet = _base_packet(
        ingestion_boundary_id="broad_search_direction",
        source_scope="broad interdisciplinary speculative early-stage direction",
        blocked_reason="broad search direction remains allowed",
        search_direction_allowed=True,
        ingestion_authorized=False,
    )
    broad_validation = validate_authorized_ingestion_boundary_packet_v1(broad_packet)
    assert broad_validation["blocked"] is False


def test_unsafe_authority_retention_claim_and_evidence_conversion_fail_closed():
    cases = [
        _base_packet(ingestion_authorized=True, authorization_state="not_authorized"),
        _base_packet(raw_retention_allowed=True),
        _base_packet(public_claim_allowed=True),
        _base_packet(final_answer_authority=True),
        _base_packet(evidence_intake_link_allowed=True, ingestion_authorized=False),
        _base_packet(authority_status={**boundary._build_default_authority_status(), "tool_execution_authority": True}),
    ]
    for packet in cases:
        validation = validate_authorized_ingestion_boundary_packet_v1(packet)
        assert validation["blocked"] is True


def test_json_safe_copy_and_summary_are_bounded():
    packet = _base_packet()
    safe = to_authorized_ingestion_boundary_json_safe_v1({"items": {1, 2}, "packet": packet, "custom": object()})
    assert json.dumps(safe, sort_keys=True)

    summary = summarize_authorized_ingestion_boundary_packet_v1(packet)
    assert len(summary["blocked_reason"]) <= 200
    assert summary["validation_posture"] == "valid"


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
