from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
)
from weslr.project_chat_assembly_orchestration_packet import (
    ASSEMBLY_MODES_V1,
    ASSEMBLY_STATUSES_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    allowed_project_chat_assembly_modes_v1,
    allowed_project_chat_assembly_statuses_v1,
    build_initial_project_chat_assembly_packet_examples_v1,
    build_project_chat_assembly_packet_v1,
    summarize_project_chat_assembly_packet_v1,
    to_project_chat_assembly_packet_json_safe_v1,
    validate_project_chat_assembly_packet_v1,
)
from weslr.project_chat_final_answer_generation import build_project_chat_final_answer_packet_v1
from weslr.project_chat_rag_evidence_retrieval import build_project_chat_evidence_packet_v1

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_assembly_orchestration_packet.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

FORBIDDEN_CASES = [
    "raw transcript",
    "raw prompt",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "provider output",
    "model output",
    "search output",
    "tool executed",
    "I executed",
    "I searched your private data",
    "I saved this project",
    "public readiness",
    "certified",
    "proof",
    "solved",
    "benchmark",
    "legal certainty",
    "medical certainty",
    "financial certainty",
    "professional certainty",
    "guaranteed",
    "cognitive engine",
]


def _base_answer_plan(**overrides):
    plan = {
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
    plan.update(overrides)
    return build_project_chat_answer_plan_v1(plan)


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
    }
    evidence.update(overrides)
    return build_project_chat_evidence_packet_v1(evidence)


def _base_packet(**overrides):
    answer_plan = _base_answer_plan()
    evidence = _base_evidence()
    packet = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "user_request_metadata": {
            "request_id": "request-001",
            "message_ref": "message-001",
            "message_status": "metadata only",
            "user_visible_status": "metadata only",
            "operator_visible_summary": "message intake metadata only",
            "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        },
        "project_context_metadata": {
            "project_state_refs": ["project-state-001"],
            "memory_state_refs": ["memory-state-001"],
            "continuity_state_refs": ["continuity-state-001"],
            "gap_analysis_refs": ["gap-001"],
            "approval_refs": ["approval-001"],
            "user_visible_status": "evidence grounded answer",
            "operator_visible_summary": "evidence grounded; metadata only",
        },
        "retrieval_need_metadata": {
            "retrieval_need_class": "project_metadata_retrieval_needed",
            "retrieval_status": "metadata only",
        },
        "evidence_packet_metadata": [evidence],
        "answer_plan_metadata": answer_plan,
        "final_answer_packet_metadata": {
            "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
        },
        "safe_metadata": {
            "assembly_summary": "metadata only assembly packet",
        },
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }
    packet.update(overrides)
    return packet


def test_allowed_modes_and_statuses_match_constants():
    assert allowed_project_chat_assembly_modes_v1() == ASSEMBLY_MODES_V1
    assert allowed_project_chat_assembly_statuses_v1() == ASSEMBLY_STATUSES_V1


def test_valid_metadata_only_assembly_packet_is_bounded():
    packet = build_project_chat_assembly_packet_v1(_base_packet())
    validation = validate_project_chat_assembly_packet_v1(packet)
    summary = summarize_project_chat_assembly_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["assembly_mode"] == "candidate_orchestration"
    assert validation["assembly_status"] == "assembly_valid_metadata_only"
    assert validation["answer_plan_validation"]["blocked"] is False
    assert validation["final_answer_validation"]["blocked"] is False
    assert validation["evidence_validations"][0]["blocked"] is False
    assert validation["blocked_state"]["live_chat_output_blocked"] is True
    assert validation["blocked_state"]["answer_delivery_blocked"] is True
    assert validation["provenance_chain"]["step_count"] == 4
    assert summary["summary_text"].startswith("assembly=candidate_orchestration")


def test_final_answer_requires_valid_evidence_and_answer_plan():
    packet = build_project_chat_assembly_packet_v1(
        _base_packet(
            evidence_packet_metadata=[],
            answer_plan_metadata=build_project_chat_answer_plan_v1(
                {
                    "project_id": "project-001",
                    "owner_user_scope": "owner-user",
                    "tenant_account_scope": "tenant-a",
                    "source_scope": "project_metadata_only",
                    "user_intent_class": "project-chat",
                    "answer_mode": "evidence_grounded_answer",
                    "allowed_answer_scope": "approved_evidence_packet",
                    "answer_status": "plan_valid_metadata_only",
                    "evidence_packet_refs": [],
                    "user_visible_status": "evidence grounded answer",
                    "operator_visible_summary": "evidence grounded; metadata only",
                    "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
                }
            ),
        )
    )
    validation = validate_project_chat_assembly_packet_v1(packet)

    assert validation["blocked"] is True
    assert "missing_evidence_packet_metadata" in validation["blocked_labels"]
    assert "invalid_answer_plan_metadata" in validation["blocked_labels"]
    assert "invalid_final_answer_packet_metadata" in validation["blocked_labels"]
    assert any(label == "final_answer_requires_valid_evidence_and_answer_plan" for label in validation["blocked_labels"])


def test_missing_project_context_metadata_blocks():
    packet = build_project_chat_assembly_packet_v1(_base_packet(project_context_metadata={}))
    validation = validate_project_chat_assembly_packet_v1(packet)

    assert validation["blocked"] is True
    assert "missing_project_context_metadata" in validation["blocked_labels"]


@pytest.mark.parametrize("phrase", FORBIDDEN_CASES)
def test_forbidden_leakage_phrases_block(phrase):
    packet = build_project_chat_assembly_packet_v1(
        _base_packet(
            user_request_metadata={
                "request_id": "request-003",
                "message_ref": "message-003",
                "message_status": "metadata only",
                "user_visible_status": phrase,
                "operator_visible_summary": "message intake metadata only",
            },
        )
    )
    validation = validate_project_chat_assembly_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("forbidden_phrase_") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field",
    [
        "provider_call_authority",
        "model_call_authority",
        "search_call_authority",
        "tool_execution_authority",
        "cognitive_engine_authority",
    ],
)
def test_denied_authority_fields_remain_false_and_block_when_true(field):
    packet = build_project_chat_assembly_packet_v1(
        _base_packet(
            denied_authority={**{name: False for name in DENIED_AUTHORITY_FIELDS_V1}, field: True},
        )
    )
    validation = validate_project_chat_assembly_packet_v1(packet)
    assert set(validation["denied_authority"]) == set(DENIED_AUTHORITY_FIELDS_V1)
    assert validation["denied_authority"][field] is True
    assert validation["blocked"] is True
    assert f"denied_authority_must_remain_false_{field}" in validation["blocked_labels"]


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_assembly_packet_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_assembly_packet_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public readiness" not in encoded.lower()
    assert "proof" not in encoded.lower()
    assert "solved" not in encoded.lower()
    assert all(example["user_request_metadata"]["project_id"] == "project-001" for example in examples)


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_assembly_packet_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)


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
