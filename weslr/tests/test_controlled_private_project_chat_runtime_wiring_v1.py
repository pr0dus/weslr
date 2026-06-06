from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.controlled_private_project_chat_runtime_wiring import (
    ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1,
    PRIVATE_RUNTIME_MODES_V1,
    allowed_controlled_private_project_chat_runtime_boundary_decisions_v1,
    allowed_controlled_private_project_chat_runtime_modes_v1,
    build_initial_controlled_private_project_chat_runtime_examples_v1,
    build_controlled_private_project_chat_runtime_request_v1,
    run_controlled_private_project_chat_runtime_dry_run_v1,
    summarize_controlled_private_project_chat_runtime_result_v1,
    to_controlled_private_project_chat_runtime_json_safe_v1,
    validate_controlled_private_project_chat_runtime_request_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "controlled_private_project_chat_runtime_wiring.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


@pytest.mark.parametrize("mode", PRIVATE_RUNTIME_MODES_V1)
def test_allowed_modes_and_boundary_decisions_match_constants(mode):
    assert allowed_controlled_private_project_chat_runtime_modes_v1() == PRIVATE_RUNTIME_MODES_V1
    assert allowed_controlled_private_project_chat_runtime_boundary_decisions_v1() == ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1


def test_valid_private_local_request_runs_closed_helper_chain():
    result = run_controlled_private_project_chat_runtime_dry_run_v1({})
    validation = validate_controlled_private_project_chat_runtime_request_v1({})
    summary = summarize_controlled_private_project_chat_runtime_result_v1({})

    assert result["blocked"] is False
    assert validation["blocked"] is False
    assert result["controlled_private_runtime_status"] == "controlled_private_runtime_valid_metadata_only"
    assert result["owner_approval_metadata"]["owner_approval_granted"] is True
    assert result["runtime_boundary_validation"]["boundary_decision"] in ALLOWED_RUNTIME_BOUNDARY_DECISIONS_V1
    assert result["runtime_boundary_validation"]["blocked"] is False
    assert result["dry_run_consumer_validation"]["blocked"] is False
    assert result["assembly_validation"]["blocked"] is False
    assert result["final_answer_validation"]["blocked"] is False
    assert result["blocked_state"]["answer_delivery_blocked"] is True
    assert result["blocked_state"]["retrieval_execution_blocked"] is True
    assert result["blocked_state"]["provider_model_search_tool_authority_blocked"] is True
    assert result["blocked_state"]["persistence_blocked"] is True
    assert result["blocked_state"]["weslr_io_blocked"] is True
    assert result["blocked_state"]["ui_nova_behavior_blocked"] is True
    assert result["blocked_state"]["public_user_facing_behavior_blocked"] is True
    assert result["blocked_state"]["private_raw_secret_hidden_system_leakage_blocked"] is True
    assert result["blocked_state"]["public_ready_claim_blocked"] is True
    assert result["blocked_state"]["cognitive_engine_authority_blocked"] is True
    assert result["provenance_chain"]["step_count"] >= 4
    assert "controlled_private_runtime_valid_metadata_only" in summary["summary_text"]


@pytest.mark.parametrize(
    "flag_name",
    [
        "answer_delivery_requested",
        "public_user_facing_mode_requested",
        "provider_model_search_tool_requested",
        "persistence_requested",
        "weslr_io_requested",
    ],
)
def test_forbidden_runtime_requests_block(flag_name):
    result = run_controlled_private_project_chat_runtime_dry_run_v1({flag_name: True})
    assert result["blocked"] is True
    assert any(label.endswith("must_be_false") for label in result["blocked_labels"])


def test_retrieval_requested_without_preapproved_metadata_blocks():
    result = run_controlled_private_project_chat_runtime_dry_run_v1({"retrieval_requested": True})
    assert result["blocked"] is True
    assert "retrieval_requested_without_preapproved_metadata" in result["blocked_labels"]


def test_invalid_boundary_or_final_answer_input_blocks():
    result = run_controlled_private_project_chat_runtime_dry_run_v1(
        {
            "assembly_packet_metadata": {
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
                    "controlled_answer_text_proposal": "Unknown Engine and raw prompt must not appear.",
                },
            }
        }
    )
    assert result["blocked"] is True
    assert result["assembly_validation"]["blocked"] is True
    assert result["final_answer_validation"]["blocked"] is True


def test_examples_are_synthetic_only():
    examples = build_initial_controlled_private_project_chat_runtime_examples_v1()
    assert examples
    encoded = json.dumps(to_controlled_private_project_chat_runtime_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public readiness" not in encoded.lower()


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_controlled_private_project_chat_runtime_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)


def test_no_runtime_or_protected_module_imports_in_source():
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden = [
        "open(",
        "subprocess",
        "requests",
        "socket",
        "from weslr.chat_responder",
        "import chat_responder",
        "from weslr.main",
        "import main",
        "from dialogue",
        "import dialogue",
        "from chat_ui",
        "import chat_ui",
    ]
    assert all(token not in source for token in forbidden)
