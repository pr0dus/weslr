from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
)
from weslr.project_chat_final_answer_generation import (
    ANSWER_SURFACES_V1,
    ANSWER_VISIBILITIES_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    FINAL_ANSWER_MODES_V1,
    FINAL_ANSWER_STATUSES_V1,
    allowed_project_chat_final_answer_modes_v1,
    allowed_project_chat_final_answer_statuses_v1,
    allowed_project_chat_final_answer_surfaces_v1,
    allowed_project_chat_final_answer_visibilities_v1,
    build_initial_project_chat_final_answer_examples_v1,
    build_project_chat_final_answer_packet_v1,
    build_project_chat_final_answer_request_packet_v1,
    summarize_project_chat_final_answer_packet_v1,
    to_project_chat_final_answer_json_safe_v1,
    validate_project_chat_final_answer_packet_v1,
    validate_project_chat_final_answer_request_packet_v1,
)
from weslr.project_chat_rag_evidence_retrieval import (
    DENIED_AUTHORITY_FIELDS_V1 as RAG_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_evidence_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_final_answer_generation.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

FORBIDDEN_USER_VISIBLE_CASES = [
    "Unknown Engine",
    ".weslr",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "tool executed",
    "I executed",
    "I searched your private data",
    "I saved this project",
    "I remember this",
    "SearXNG proves",
    "the web confirms",
    "final answer authority",
    "public readiness",
    "proof",
    "proven",
    "solved",
    "certified",
    "benchmark",
    "legal certainty",
    "medical certainty",
    "financial certainty",
    "professional certainty",
    "guaranteed",
    "CognitiveResearchRunV1",
    "cognitive engine",
]


def _base_answer_plan():
    return build_project_chat_answer_plan_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "answer_mode": "evidence_grounded_answer",
            "allowed_answer_scope": "approved_evidence_packet",
            "answer_status": "plan_valid_metadata_only",
            "evidence_packet_refs": ["evidence-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        }
    )


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
        "source_timestamp": "2026-06-06T14:00:00Z",
        "retrieved_at_marker": "metadata_only",
        "freshness_label": "fresh_current",
        "relevance_label": "high_relevance",
        "confidence_label": "high_confidence",
        "verification_status": "metadata_only",
        "privacy_label": "public",
        "privacy_sensitivity": "low",
        "query_redaction_status": "not_required",
        "evidence_summary": "evidence packet metadata only",
        "denied_authority": {field: False for field in RAG_DENIED_AUTHORITY_FIELDS_V1},
    }
    evidence.update(overrides)
    return build_project_chat_evidence_packet_v1(evidence)


def _base_request(**overrides):
    answer_plan = _base_answer_plan()
    evidence = _base_evidence()
    request = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "answer_plan_metadata": answer_plan,
        "evidence_packet_metadata": [evidence],
        "project_context_metadata": {
            "project_state_refs": ["project-state-001"],
            "memory_state_refs": ["memory-state-001"],
            "continuity_state_refs": ["continuity-state-001"],
            "gap_analysis_refs": ["gap-001"],
            "tool_lane_candidate_refs": ["tool-lane-001"],
            "approval_refs": ["approval-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
            "limitations": ["metadata only"],
            "uncertainty_flags": [],
            "stale_state_flags": [],
            "contradiction_flags": [],
            "missing_evidence_flags": [],
        },
        "answer_surface": "internal_controlled",
        "answer_visibility": "internal_controlled",
        "final_answer_mode": "evidence_grounded_answer",
        "answer_status": "answer_ready",
        "retrieval_required": False,
        "retrieval_completed": True,
        "external_search_required": False,
        "external_search_approved": False,
        "external_search_redacted": False,
        "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }
    request.update(overrides)
    return request


@pytest.mark.parametrize(
    "getter,expected",
    [
        (allowed_project_chat_final_answer_surfaces_v1, ANSWER_SURFACES_V1),
        (allowed_project_chat_final_answer_visibilities_v1, ANSWER_VISIBILITIES_V1),
        (allowed_project_chat_final_answer_statuses_v1, FINAL_ANSWER_STATUSES_V1),
        (allowed_project_chat_final_answer_modes_v1, FINAL_ANSWER_MODES_V1),
    ],
)
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


def test_valid_internal_controlled_final_answer_request():
    request = build_project_chat_final_answer_request_packet_v1(_base_request())
    validation = validate_project_chat_final_answer_request_packet_v1(request)

    assert validation["blocked"] is False
    assert validation["answer_status"] == "answer_ready"
    assert validation["answer_surface"] == "internal_controlled"
    assert validation["answer_visibility"] == "internal_controlled"
    assert validation["answer_text_bounded"] is True
    assert validation["answer_plan_validation"]["blocked"] is False
    assert validation["evidence_validations"][0]["blocked"] is False


def test_valid_uncertain_request_preserves_flags_and_remains_bounded():
    request = build_project_chat_final_answer_request_packet_v1(
        _base_request(
            answer_plan_metadata=build_project_chat_answer_plan_v1(
                {
                    "project_id": "project-001",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "user_intent_class": "project-chat",
                    "answer_mode": "uncertain_or_missing_evidence_answer",
                    "allowed_answer_scope": "approved_evidence_packet",
                    "answer_status": "plan_valid_metadata_only",
                    "evidence_packet_refs": ["evidence-001"],
                    "missing_evidence_flags": ["missing_project_context"],
                    "user_visible_status": "evidence incomplete",
                    "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
                }
            ),
            project_context_metadata={
                "missing_evidence_flags": ["missing_project_context"],
                "user_visible_status": "evidence incomplete",
                "operator_visible_summary": "evidence incomplete; metadata only",
            },
            final_answer_mode="uncertain_or_missing_evidence_answer",
            controlled_answer_text_proposal="Internal controlled answer candidate: evidence is incomplete or uncertain.",
        )
    )
    validation = validate_project_chat_final_answer_request_packet_v1(request)
    assert validation["blocked"] is False
    assert validation["answer_status"] == "uncertain"
    assert validation["missing_evidence_flags"] == ["missing_project_context"]
    assert "incomplete" in validation["controlled_answer_text"].lower()


def test_raw_prompt_alone_or_user_facing_text_is_blocked():
    validation = validate_project_chat_final_answer_request_packet_v1(
        _base_request(
            evidence_packet_metadata=[],
            answer_plan_metadata={"answer_mode": "evidence_grounded_answer"},
            project_context_metadata={},
            answer_text_proposal="Raw prompt alone should not become an answer",
        )
    )
    assert validation["blocked"] is True
    assert "missing_evidence_packet_metadata" in validation["blocked_labels"]


def test_retrieval_required_but_not_completed_blocks():
    validation = validate_project_chat_final_answer_request_packet_v1(
        _base_request(retrieval_required=True, retrieval_completed=False)
    )
    assert validation["blocked"] is True
    assert "retrieval_required_but_not_completed" in validation["blocked_labels"]


def test_external_search_required_without_approval_or_redaction_blocks():
    evidence = _base_evidence(
        source_type="searxng_search_result",
        source_url="https://example.invalid/search",
        retrieval_need_class="external_web_search_needed",
        retrieval_adapter="SearXNGExternalSearchAdapter",
        privacy_sensitivity="sensitive",
        privacy_label="sensitive",
        query_redaction_status="required",
    )
    request = build_project_chat_final_answer_request_packet_v1(
        _base_request(
            evidence_packet_metadata=[evidence],
            external_search_required=True,
            external_search_approved=False,
            external_search_redacted=False,
        )
    )
    validation = validate_project_chat_final_answer_request_packet_v1(request)
    assert validation["blocked"] is True
    assert "external_search_required_but_not_approved" in validation["blocked_labels"]
    assert "external_search_required_but_not_redacted" in validation["blocked_labels"]


@pytest.mark.parametrize("phrase", FORBIDDEN_USER_VISIBLE_CASES)
def test_forbidden_public_readiness_and_uncertain_certainty_phrases_block(phrase):
    validation = validate_project_chat_final_answer_request_packet_v1(
        _base_request(controlled_answer_text_proposal=f"safe prefix {phrase.upper()} safe suffix")
    )
    assert validation["blocked"] is True
    assert any("forbidden_phrase" in label for label in validation["blocked_labels"])


def test_final_answer_packet_preserves_citations_and_summary_is_metadata_only():
    packet = build_project_chat_final_answer_packet_v1(_base_request())
    validation = validate_project_chat_final_answer_packet_v1(packet)
    summary = summarize_project_chat_final_answer_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["final_answer_status"] == "answer_ready"
    assert validation["citations"]
    assert packet["final_answer_packet_id"].startswith("project-chat-final-answer-")
    assert "proof" not in summary["summary_text"].lower()
    assert "solved" not in summary["summary_text"].lower()
    assert "certified" not in summary["summary_text"].lower()


def test_missing_or_invalid_nested_answer_plan_and_evidence_blocks():
    request = build_project_chat_final_answer_request_packet_v1(
        {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "answer_plan_metadata": {"answer_mode": "unknown"},
            "evidence_packet_metadata": [{"source_type": "unknown"}],
            "project_context_metadata": {},
            "answer_surface": "internal_controlled",
            "answer_visibility": "internal_controlled",
            "final_answer_mode": "evidence_grounded_answer",
            "answer_status": "answer_ready",
            "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    validation = validate_project_chat_final_answer_request_packet_v1(request)
    assert validation["blocked"] is True
    assert validation["answer_plan_validation"]["blocked"] is True
    assert any(validation_item["blocked"] for validation_item in validation["evidence_validations"])


def test_denied_authority_fields_remain_false():
    validation = validate_project_chat_final_answer_request_packet_v1(_base_request())
    assert set(validation["denied_authority"]) == set(DENIED_AUTHORITY_FIELDS_V1)
    assert all(value is False for value in validation["denied_authority"].values())


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


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_final_answer_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_final_answer_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public readiness" not in encoded.lower()
    assert "final answer" not in encoded.lower()
    assert all(example["project_id"] == "project-001" for example in examples)


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_final_answer_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)
