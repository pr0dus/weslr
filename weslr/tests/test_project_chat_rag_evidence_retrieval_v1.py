from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_rag_evidence_retrieval import (
    APPROVAL_STATUSES_V1,
    CONFIDENCE_LABELS_V1,
    CONSENT_STATUSES_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    FRESHNESS_LABELS_V1,
    HELPER_TYPE_V1,
    PRIVACY_LABELS_V1,
    QUERY_CLASSES_V1,
    QUERY_REDACTION_STATUSES_V1,
    RELEVANCE_LABELS_V1,
    RETRIEVAL_ADAPTERS_V1,
    RETRIEVAL_NEEDS_V1,
    SCHEMA_VERSION_V1,
    SOURCE_CLASSES_V1,
    SOURCE_TYPES_V1,
    SOURCE_TYPES_V1 as RAG_SOURCE_TYPES_V1,
    VERIFICATION_STATUSES_V1,
    allowed_project_chat_rag_adapters_v1,
    allowed_project_chat_rag_query_classes_v1,
    allowed_project_chat_rag_retrieval_needs_v1,
    allowed_project_chat_rag_source_classes_v1,
    build_initial_project_chat_rag_evidence_examples_v1,
    build_project_chat_evidence_packet_v1,
    build_project_chat_rag_request_packet_v1,
    classify_project_chat_retrieval_need_v1,
    summarize_project_chat_evidence_packet_v1,
    to_project_chat_rag_evidence_json_safe_v1,
    validate_project_chat_evidence_packet_v1,
    validate_project_chat_rag_request_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_rag_evidence_retrieval.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

FORBIDDEN_LEAKAGE_CASES = [
    "Unknown Engine",
    ".weslr",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "hidden system",
    "raw private",
    "raw secret",
    "secret",
    "tool executed",
    "I executed",
    "I searched",
    "I saved",
    "I found the truth",
    "the web confirms",
    "SearXNG proves",
    "proof",
    "proven",
    "solved",
    "certified",
    "public readiness",
    "final answer",
]


def _base_request(**overrides):
    request = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "source_class": "project_metadata",
        "retrieval_need_class": "project_metadata_retrieval_needed",
        "query_class": "direct_project_query",
        "retrieval_adapter": "ProjectStateMetadataAdapter",
        "query_text": "project metadata only",
        "privacy_sensitivity": "low",
        "external_query_allowed": False,
        "redaction_required": False,
        "approval_status": "not_required",
        "consent_status": "not_required",
        "query_redaction_status": "not_required",
        "freshness_label": "fresh_current",
        "relevance_label": "high_relevance",
        "confidence_label": "high_confidence",
        "verification_status": "metadata_only",
        "privacy_label": "public",
        "evidence_summary": "metadata only",
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }
    request.update(overrides)
    return request


def _base_evidence(**overrides):
    evidence = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "retrieval_request_id": "request-001",
        "retrieval_need_class": "project_metadata_retrieval_needed",
        "retrieval_adapter": "ProjectStateMetadataAdapter",
        "source_type": "project_metadata",
        "source_ref": "project-metadata-001",
        "source_title": "project metadata only",
        "source_timestamp": "2026-06-06T13:00:00Z",
        "retrieved_at_marker": "metadata_only",
        "freshness_label": "fresh_current",
        "relevance_label": "high_relevance",
        "confidence_label": "high_confidence",
        "verification_status": "metadata_only",
        "privacy_label": "public",
        "privacy_sensitivity": "low",
        "query_redaction_status": "not_required",
        "evidence_summary": "evidence packet metadata only",
        "limitations": ["metadata only"],
        "conflict_flags": [],
        "missing_evidence_flags": [],
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }
    evidence.update(overrides)
    return evidence


@pytest.mark.parametrize(
    "getter,expected",
    [
        (allowed_project_chat_rag_retrieval_needs_v1, RETRIEVAL_NEEDS_V1),
        (allowed_project_chat_rag_query_classes_v1, QUERY_CLASSES_V1),
        (allowed_project_chat_rag_source_classes_v1, SOURCE_CLASSES_V1),
        (allowed_project_chat_rag_adapters_v1, RETRIEVAL_ADAPTERS_V1),
    ],
)
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


def test_valid_project_metadata_request():
    request = build_project_chat_rag_request_packet_v1(_base_request())
    validation = validate_project_chat_rag_request_packet_v1(request)
    classification = classify_project_chat_retrieval_need_v1(request)

    assert request["schema_version"] == SCHEMA_VERSION_V1
    assert request["helper_type"] == HELPER_TYPE_V1
    assert validation["blocked"] is False
    assert validation["retrieval_need_class"] == "project_metadata_retrieval_needed"
    assert classification["classification"] == "project_metadata_retrieval_needed"


def test_valid_memory_continuity_request():
    request = build_project_chat_rag_request_packet_v1(
        _base_request(
            source_class="memory_metadata",
            retrieval_need_class="memory_continuity_retrieval_needed",
            query_class="source_specific_query",
            retrieval_adapter="MemoryStateMetadataAdapter",
            privacy_sensitivity="project_private",
            privacy_label="project_private",
            consent_status="provided",
        )
    )
    validation = validate_project_chat_rag_request_packet_v1(request)
    assert validation["blocked"] is False
    assert validation["classification"] == "memory_continuity_retrieval_needed"


def test_valid_local_index_request():
    request = build_project_chat_rag_request_packet_v1(
        _base_request(
            source_class="local_project_index",
            retrieval_need_class="local_index_retrieval_needed",
            query_class="source_specific_query",
            retrieval_adapter="LocalProjectIndexAdapter",
            privacy_sensitivity="project_private",
            privacy_label="project_private",
            consent_status="provided",
        )
    )
    validation = validate_project_chat_rag_request_packet_v1(request)
    assert validation["blocked"] is False
    assert validation["classification"] == "local_index_retrieval_needed"


def test_valid_external_search_request_with_approval_and_redaction():
    request = build_project_chat_rag_request_packet_v1(
        _base_request(
            source_class="external_web_search",
            retrieval_need_class="external_web_search_needed",
            query_class="general_web_query",
            retrieval_adapter="SearXNGExternalSearchAdapter",
            query_text="general web search metadata only",
            redacted_query_text="general web search metadata only",
            privacy_sensitivity="public",
            privacy_label="public",
            external_query_allowed=True,
            redaction_required=False,
            approval_status="approved",
            consent_status="not_required",
            query_redaction_status="applied",
            freshness_sensitive=False,
            source_url="https://example.invalid/search",
            source_title="general web search metadata only",
        )
    )
    validation = validate_project_chat_rag_request_packet_v1(request)
    assert validation["blocked"] is False
    assert validation["classification"] == "external_web_search_needed"
    assert validation["needs_redaction"] is False


def test_external_search_without_permission_blocks():
    validation = validate_project_chat_rag_request_packet_v1(
        _base_request(
            source_class="external_web_search",
            retrieval_need_class="external_web_search_needed",
            query_class="general_web_query",
            retrieval_adapter="SearXNGExternalSearchAdapter",
            privacy_sensitivity="public",
            privacy_label="public",
            external_query_allowed=False,
            approval_status="not_required",
            query_redaction_status="required",
            source_url="https://example.invalid/search",
        )
    )
    assert validation["blocked"] is True
    assert "missing_external_query_permission" in validation["blocked_labels"]
    assert "missing_user_approval_for_external_search" in validation["blocked_labels"]


@pytest.mark.parametrize("field", ["direct_to_answer_requested", "final_answer_requested", "live_retrieval_requested", "provider_search_requested", "tool_execution_requested"])
def test_direct_answer_and_execution_requests_block(field):
    validation = validate_project_chat_rag_request_packet_v1(_base_request(**{field: True}))
    assert validation["blocked"] is True
    assert field in validation["blocked_labels"]


@pytest.mark.parametrize("phrase", FORBIDDEN_LEAKAGE_CASES)
def test_private_raw_secret_and_public_readiness_leakage_blocks(phrase):
    validation = validate_project_chat_rag_request_packet_v1(
        _base_request(query_text=f"safe prefix {phrase.upper()} safe suffix")
    )
    assert validation["blocked"] is True
    assert any("forbidden_phrase" in label for label in validation["blocked_labels"])


def test_sensitive_query_without_redaction_blocks():
    validation = validate_project_chat_rag_request_packet_v1(
        _base_request(
            privacy_sensitivity="sensitive",
            privacy_label="sensitive",
            redaction_required=True,
            query_redaction_status="required",
            query_text="private project details",
            redacted_query_text="",
        )
    )
    assert validation["blocked"] is True
    assert "missing_query_redaction_metadata" in validation["blocked_labels"]
    assert "sensitive_query_requires_redacted_metadata" in validation["blocked_labels"]


def test_source_class_mismatch_blocks():
    validation = validate_project_chat_rag_request_packet_v1(
        _base_request(
            source_class="external_web_search",
            retrieval_need_class="memory_continuity_retrieval_needed",
            query_class="source_specific_query",
            retrieval_adapter="SearXNGExternalSearchAdapter",
            privacy_sensitivity="public",
            privacy_label="public",
        )
    )
    assert validation["blocked"] is True
    assert "source_class_mismatch_for_external_search" in validation["blocked_labels"]


def test_evidence_packet_preserves_provenance_and_stays_metadata_only():
    evidence = build_project_chat_evidence_packet_v1(_base_evidence())
    validation = validate_project_chat_evidence_packet_v1(evidence)
    summary = summarize_project_chat_evidence_packet_v1(evidence)

    assert validation["blocked"] is False
    assert validation["classification"] == "evidence_packet_metadata_only"
    assert evidence["source_ref"] == "project-metadata-001"
    assert evidence["source_title"] == "project metadata only"
    assert "proof" not in summary["summary_text"].lower()
    assert "solved" not in summary["summary_text"].lower()


def test_external_evidence_packet_requires_source_url():
    validation = validate_project_chat_evidence_packet_v1(
        _base_evidence(source_type="searxng_search_result", source_url="")
    )
    assert validation["blocked"] is True
    assert "missing_source_url_for_external_evidence" in validation["blocked_labels"]


def test_internal_evidence_packet_requires_source_ref():
    validation = validate_project_chat_evidence_packet_v1(
        _base_evidence(source_type="approved_project_artifact", source_ref="")
    )
    assert validation["blocked"] is True
    assert "missing_source_ref_for_internal_evidence" in validation["blocked_labels"]


def test_evidence_conflict_and_missing_flags_are_preserved():
    evidence = build_project_chat_evidence_packet_v1(
        _base_evidence(
            conflict_flags=["conflicts_with_project_state"],
            missing_evidence_flags=["missing_external_verification"],
            freshness_label="possibly_stale",
        )
    )
    validation = validate_project_chat_evidence_packet_v1(evidence)
    assert validation["blocked"] is False
    assert validation["conflict_flags"] == ["conflicts_with_project_state"]
    assert validation["missing_evidence_flags"] == ["missing_external_verification"]
    assert validation["classification"] in {"evidence_packet_conflict_review_required", "evidence_packet_stale_or_recent"}


def test_summary_is_metadata_only_and_json_safe():
    evidence = build_project_chat_evidence_packet_v1(_base_evidence())
    summary = summarize_project_chat_evidence_packet_v1(evidence)
    encoded = json.dumps(to_project_chat_rag_evidence_json_safe_v1(summary), sort_keys=True)

    assert "public readiness" not in encoded.lower()
    assert "final answer" not in encoded.lower()
    assert "unknown engine" not in encoded.lower()


def test_invalid_packets_fail_closed():
    request_validation = validate_project_chat_rag_request_packet_v1({"retrieval_need_class": "unknown"})
    evidence_validation = validate_project_chat_evidence_packet_v1({"source_type": "unknown"})

    assert request_validation["blocked"] is True
    assert evidence_validation["blocked"] is True
    assert request_validation["validation_notes"]
    assert evidence_validation["validation_notes"]


def test_json_safe_normalization_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_rag_evidence_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_rag_evidence_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_rag_evidence_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "final answer" not in encoded.lower()
    assert "public readiness" not in encoded.lower()
    assert all(example["project_id"] == "project-001" for example in examples)


def test_no_runtime_or_protected_module_imports_in_source():
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden = [
        "open(",
        "subprocess",
        "requests",
        "socket",
        ".weslr",
        "chat_responder",
        "main.py",
        "dialogue",
        "chat_ui",
    ]
    assert all(token not in source for token in forbidden)
