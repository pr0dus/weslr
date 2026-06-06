from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_assembly_orchestration_packet import build_project_chat_assembly_packet_v1
from weslr.project_chat_runtime_shell_dry_run_consumer import (
    CONSUMER_DECISIONS_V1,
    CONSUMER_MODES_V1,
    CONSUMER_STATUSES_V1,
    RUNTIME_SHELL_READINESS_LABELS_V1,
    build_initial_project_chat_runtime_shell_dry_run_consumer_examples_v1,
    build_project_chat_runtime_shell_dry_run_consumer_packet_v1,
    summarize_project_chat_runtime_shell_dry_run_consumer_packet_v1,
    to_project_chat_runtime_shell_dry_run_consumer_json_safe_v1,
    validate_project_chat_runtime_shell_dry_run_consumer_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_runtime_shell_dry_run_consumer.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


def _base_assembly_packet(**overrides):
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
        "evidence_packet_metadata": [
            {
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
        ],
        "answer_plan_metadata": {
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
        },
        "final_answer_packet_metadata": {
            "controlled_answer_text_proposal": "Internal controlled answer candidate: evidence-grounded and bounded by citations.",
        },
    }
    packet.update(overrides)
    return build_project_chat_assembly_packet_v1(packet)



def test_allowed_modes_statuses_decisions_and_labels_match_constants():
    assert CONSUMER_MODES_V1
    assert CONSUMER_STATUSES_V1
    assert CONSUMER_DECISIONS_V1
    assert RUNTIME_SHELL_READINESS_LABELS_V1



def test_valid_assembly_packet_is_consumed_without_delivery():
    assembly_packet = _base_assembly_packet()
    packet = build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": assembly_packet})
    validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet)
    summary = summarize_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["consumer_status"] == "consumer_valid_metadata_only"
    assert validation["consumer_mode"] == "metadata_only_dry_run_consumer"
    assert validation["consumer_decision"] == "preserve_metadata_only"
    assert validation["assembly_validation"]["blocked"] is False
    assert validation["shell_validation"]["blocked"] is False
    assert validation["dry_run_validation"]["blocked"] is False
    assert validation["consumption_plan_validation"]["blocked"] is False
    assert validation["final_answer_validation"]["blocked"] is False
    assert validation["final_answer_packet_metadata"]["final_answer_status"] == "answer_ready"
    assert validation["blocked_state"]["live_chat_output_blocked"] is True
    assert validation["blocked_state"]["answer_delivery_blocked"] is True
    assert validation["blocked_state"]["retrieval_execution_blocked"] is True
    assert validation["blocked_state"]["persistence_blocked"] is True
    assert validation["blocked_state"]["provider_model_search_tool_authority_blocked"] is True
    assert validation["blocked_state"]["private_leak_blocked"] is True
    assert validation["blocked_state"]["public_ready_claim_blocked"] is True
    assert validation["blocked_state"]["cognitive_engine_authority_blocked"] is True
    assert "final_answer_packet_preserved" in validation["runtime_shell_readiness_labels"]
    assert "answer_delivery_blocked" in validation["runtime_shell_readiness_labels"]
    assert summary["summary_text"].startswith("consumer=metadata_only_dry_run_consumer")



def test_blocked_final_answer_metadata_blocks_and_preserves_packet():
    assembly_packet = _base_assembly_packet(
        final_answer_packet_metadata={
            "controlled_answer_text_proposal": "Unknown Engine and raw prompt must not appear.",
        }
    )
    packet = build_project_chat_runtime_shell_dry_run_consumer_packet_v1({"assembly_packet_metadata": assembly_packet})
    validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(packet)

    assert validation["blocked"] is True
    assert validation["final_answer_validation"]["blocked"] is True
    assert any(label.startswith("forbidden_phrase_") for label in validation["blocked_labels"])
    assert validation["final_answer_packet_metadata"]["controlled_answer_text_proposal"].startswith("Unknown Engine")


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
    assembly_packet = _base_assembly_packet()
    consumer_packet = build_project_chat_runtime_shell_dry_run_consumer_packet_v1(
        {
            "assembly_packet_metadata": assembly_packet,
            "denied_authority": {**{name: False for name in set(assembly_packet["denied_authority"])}, field: True},
        }
    )
    validation = validate_project_chat_runtime_shell_dry_run_consumer_packet_v1(consumer_packet)
    assert validation["denied_authority"][field] is True
    assert validation["blocked"] is True
    assert f"denied_authority_must_remain_false_{field}" in validation["blocked_labels"]



def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_runtime_shell_dry_run_consumer_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_runtime_shell_dry_run_consumer_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public readiness" not in encoded.lower()
    assert all(example["consumer_mode"] for example in examples)



def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_runtime_shell_dry_run_consumer_json_safe_v1(value)
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
