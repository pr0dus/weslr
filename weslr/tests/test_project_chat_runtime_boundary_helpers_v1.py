from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_runtime_boundary_helpers import (
    BOUNDARY_DECISIONS_V1,
    BOUNDARY_MODES_V1,
    BOUNDARY_READINESS_LABELS_V1,
    BOUNDARY_STATUSES_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    allowed_project_chat_runtime_boundary_decisions_v1,
    allowed_project_chat_runtime_boundary_modes_v1,
    allowed_project_chat_runtime_boundary_readiness_labels_v1,
    allowed_project_chat_runtime_boundary_statuses_v1,
    build_initial_project_chat_runtime_boundary_examples_v1,
    build_project_chat_runtime_boundary_packet_v1,
    classify_project_chat_runtime_boundary_decision_v1,
    summarize_project_chat_runtime_boundary_packet_v1,
    to_project_chat_runtime_boundary_json_safe_v1,
    validate_project_chat_runtime_boundary_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_runtime_boundary_helpers.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

FORBIDDEN_USER_VISIBLE_STATUS_CASES = [
    "Unknown Engine",
    "Unknown Engine",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "internal mechanism",
    "tool executed",
    "I executed",
    "I searched your private data",
    "I saved this project",
    "I remember this",
    "SearXNG proves",
    "the web confirms",
    "truth authority",
    "final answer authority",
    "runtime authority",
    "mutation authority",
    "memory authority",
    "tool execution authority",
    "storage authority",
    "public readiness",
    "certified intelligence",
    "autonomous self-improvement",
]


def test_allowed_modes_statuses_decisions_and_labels_match_constants():
    assert allowed_project_chat_runtime_boundary_modes_v1() == BOUNDARY_MODES_V1
    assert allowed_project_chat_runtime_boundary_statuses_v1() == BOUNDARY_STATUSES_V1
    assert allowed_project_chat_runtime_boundary_decisions_v1() == BOUNDARY_DECISIONS_V1
    assert allowed_project_chat_runtime_boundary_readiness_labels_v1() == BOUNDARY_READINESS_LABELS_V1


def test_valid_runtime_boundary_packet_preserves_metadata_and_blocks_runtime_wiring():
    packet = build_project_chat_runtime_boundary_packet_v1({})
    validation = validate_project_chat_runtime_boundary_packet_v1(packet)
    summary = summarize_project_chat_runtime_boundary_packet_v1(packet)
    classification = classify_project_chat_runtime_boundary_decision_v1(packet)

    assert validation["blocked"] is False
    assert validation["boundary_status"] == "owner_approval_required"
    assert validation["boundary_decision"] == "require_owner_approval_before_runtime_wiring"
    assert classification["classification"] == "owner_approval_required"
    assert validation["future_owner_approval_required"] is True
    assert validation["runtime_wiring_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["live_chat_output_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["answer_delivery_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["retrieval_execution_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["model_provider_search_tool_calls_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["persistence_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["ui_nova_behavior_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["public_user_facing_behavior_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["private_raw_secret_hidden_system_leakage_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["public_ready_claim_blocked"] is True
    assert validation["boundary_packet"]["blocked_state"]["cognitive_engine_authority_blocked"] is True
    assert "consumer_packet_preserved" in validation["runtime_boundary_readiness_labels"]
    assert "future_owner_approval_required" in validation["runtime_boundary_readiness_labels"]
    assert validation["dry_run_consumer_packet_metadata"]["consumer_mode"] == "metadata_only_dry_run_consumer"
    assert validation["safe_metadata"]["boundary_summary"].startswith("require_owner_approval_before_runtime_wiring")
    assert summary["summary_text"].startswith("boundary=require_owner_approval_before_runtime_wiring")


@pytest.mark.parametrize("phrase", FORBIDDEN_USER_VISIBLE_STATUS_CASES)
def test_forbidden_visible_phrases_fail_closed(phrase):
    packet = build_project_chat_runtime_boundary_packet_v1(
        {
            "user_visible_status": phrase,
            "operator_visible_summary": "boundary metadata only",
        }
    )
    validation = validate_project_chat_runtime_boundary_packet_v1(packet)

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
    packet = build_project_chat_runtime_boundary_packet_v1(
        {"denied_authority": {**{name: False for name in DENIED_AUTHORITY_FIELDS_V1}, field: True}}
    )
    validation = validate_project_chat_runtime_boundary_packet_v1(packet)

    assert validation["blocked"] is True
    assert validation["denied_authority"][field] is True
    assert f"denied_authority_must_remain_false_{field}" in validation["blocked_labels"]


def test_blocked_boundary_packet_can_be_generated_without_runtime_wiring():
    packet = build_project_chat_runtime_boundary_packet_v1(
        {
            "boundary_status": "blocked",
            "boundary_decision": "block_before_runtime",
            "user_visible_status": "This runtime boundary is blocked.",
            "operator_visible_summary": "Blocked boundary metadata only.",
        }
    )
    validation = validate_project_chat_runtime_boundary_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["boundary_status"] == "blocked"
    assert validation["boundary_decision"] == "block_before_runtime"


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_runtime_boundary_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_runtime_boundary_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public readiness" not in encoded.lower()
    assert all(example["boundary_id"] for example in examples)


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_runtime_boundary_json_safe_v1(value)
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
