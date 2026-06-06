from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.private_local_project_chat_entrypoint import (
    ALLOWED_OWNER_MODES_V1,
    ENTRYPOINT_MODE_V1,
    allowed_private_local_project_chat_entrypoint_modes_v1,
    build_initial_private_local_project_chat_entrypoint_examples_v1,
    build_private_local_project_chat_entrypoint_request_v1,
    run_private_local_project_chat_entrypoint_dry_run_v1,
    summarize_private_local_project_chat_entrypoint_result_v1,
    to_private_local_project_chat_entrypoint_json_safe_v1,
    validate_private_local_project_chat_entrypoint_request_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "private_local_project_chat_entrypoint.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


@pytest.mark.parametrize("mode", ALLOWED_OWNER_MODES_V1)
def test_allowed_mode_list_matches_constant(mode):
    assert allowed_private_local_project_chat_entrypoint_modes_v1() == ALLOWED_OWNER_MODES_V1
    assert mode == ENTRYPOINT_MODE_V1


def test_valid_owner_only_request_runs_controlled_runtime_chain():
    result = run_private_local_project_chat_entrypoint_dry_run_v1({})
    validation = validate_private_local_project_chat_entrypoint_request_v1({})
    summary = summarize_private_local_project_chat_entrypoint_result_v1({})

    assert result["blocked"] is False
    assert validation["blocked"] is False
    assert result["entrypoint_status"] == "private_local_entrypoint_valid_metadata_only"
    assert result["controlled_private_runtime_result"]["blocked"] is False
    assert result["controlled_private_runtime_result"]["controlled_private_runtime_status"] == "controlled_private_runtime_valid_metadata_only"
    assert result["owner_approval_metadata"]["owner_approval_granted"] is True
    assert result["runtime_boundary_validation"]["boundary_decision"]
    assert result["provenance_chain"]["step_count"] >= 4
    assert result["approval_state"]
    assert result["missing_evidence_state"]
    assert result["conflict_state"]
    assert "private_local_entrypoint_valid_metadata_only" in summary["summary_text"]


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
    result = run_private_local_project_chat_entrypoint_dry_run_v1({flag_name: True})
    assert result["blocked"] is True
    assert any(label.endswith("must_be_false") for label in result["blocked_labels"])


def test_owner_approval_required_blocks_when_missing_or_false():
    result = run_private_local_project_chat_entrypoint_dry_run_v1(
        {"owner_approval_metadata": {"owner_approval_required": True, "owner_approval_granted": False}}
    )
    assert result["blocked"] is True
    assert any("owner_approval" in label for label in result["blocked_labels"])


def test_examples_are_synthetic_and_json_safe():
    examples = build_initial_private_local_project_chat_entrypoint_examples_v1()
    assert examples
    encoded = json.dumps(to_private_local_project_chat_entrypoint_json_safe_v1(examples), sort_keys=True)
    assert "public chat" not in encoded.lower()
    assert ".weslr" not in encoded.lower()


def test_json_safe_helper_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_private_local_project_chat_entrypoint_json_safe_v1(value)
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
