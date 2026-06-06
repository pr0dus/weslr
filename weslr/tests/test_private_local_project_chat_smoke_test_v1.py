from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.private_local_project_chat_smoke_test import (
    ALLOWED_SMOKE_TEST_MODES_V1,
    SMOKE_TEST_MODE_V1,
    allowed_private_local_project_chat_smoke_test_modes_v1,
    build_initial_private_local_project_chat_smoke_test_examples_v1,
    build_private_local_project_chat_smoke_test_case_v1,
    run_private_local_project_chat_smoke_test_v1,
    summarize_private_local_project_chat_smoke_test_result_v1,
    to_private_local_project_chat_smoke_test_json_safe_v1,
    validate_private_local_project_chat_smoke_test_case_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "private_local_project_chat_smoke_test.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


@pytest.mark.parametrize("mode", ALLOWED_SMOKE_TEST_MODES_V1)
def test_allowed_mode_list_matches_constant(mode):
    assert allowed_private_local_project_chat_smoke_test_modes_v1() == ALLOWED_SMOKE_TEST_MODES_V1
    assert mode == SMOKE_TEST_MODE_V1


def test_valid_owner_only_smoke_test_runs_entrypoint_chain():
    payload = {
        "owner_approval_metadata_supplied": True,
        "owner_approval_metadata": {
            "owner_approval_required": True,
            "owner_approval_granted": True,
            "owner_approval_ref": "approval-001",
            "operator_visible_summary": "owner approval granted for private local smoke test only",
        },
    }
    result = run_private_local_project_chat_smoke_test_v1(payload)
    validation = validate_private_local_project_chat_smoke_test_case_v1(payload)
    summary = summarize_private_local_project_chat_smoke_test_result_v1(payload)

    assert result["blocked"] is False
    assert validation["blocked"] is False
    assert result["smoke_test_status"] == "private_local_smoke_test_valid_metadata_only"
    assert result["metadata_only_verified"] is True
    assert result["answer_delivery_verified"] is True
    assert result["public_mode_verified"] is True
    assert result["provider_model_search_tool_verified"] is True
    assert result["persistence_verified"] is True
    assert result["entrypoint_result_packet"]["blocked"] is False
    assert result["entrypoint_result_packet"]["entrypoint_status"] == "private_local_entrypoint_valid_metadata_only"
    assert result["entrypoint_result_packet"]["controlled_private_runtime_result"]["blocked"] is False
    assert result["runtime_boundary_validation"]["boundary_decision"]
    assert result["provenance_chain"]["step_count"] >= 4
    assert result["approval_state"]
    assert result["missing_evidence_state"]
    assert result["conflict_state"]
    assert "private_local_smoke_test_valid_metadata_only" in summary["summary_text"]


@pytest.mark.parametrize(
    "flag_name",
    [
        "public_user_facing_mode_requested",
        "answer_delivery_requested",
        "provider_model_search_tool_requested",
        "provider_call_requested",
        "search_call_requested",
        "tool_call_requested",
        "persistence_requested",
        "weslr_io_requested",
    ],
)
def test_forbidden_modes_block(flag_name):
    result = run_private_local_project_chat_smoke_test_v1({flag_name: True})
    assert result["blocked"] is True
    assert any(label.endswith("must_be_false") for label in result["blocked_labels"])


def test_owner_approval_absent_fails_closed():
    result = run_private_local_project_chat_smoke_test_v1({})
    assert result["blocked"] is True
    assert "missing_owner_approval_metadata" in result["blocked_labels"]


def test_examples_are_synthetic_and_non_private():
    examples = build_initial_private_local_project_chat_smoke_test_examples_v1()
    assert examples
    encoded = json.dumps(to_private_local_project_chat_smoke_test_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "public chat" not in encoded.lower()
    assert ".weslr" not in encoded.lower()


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_private_local_project_chat_smoke_test_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)


def test_source_does_not_import_protected_runtime_files():
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
