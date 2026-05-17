"""Test routing validator safe preflight integration V1.

Validates that prompt_set_routing_validator.py is the first safety gate before
any callable construction or shadow execution.

No ChatResponder/respond_chat/generate_chat import or call in this test file.
No raw prompt/response text retention.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import pytest

from weslr.controlled_behavior_prompt_set import build_default_controlled_behavior_prompt_set_v1
from weslr.real_chatresponder_shadow_call_helpers import (
    build_real_chatresponder_shadow_call_blocker_contract_v1,
    build_real_chatresponder_shadow_call_config_v1,
    build_real_chatresponder_shadow_call_observation_v1,
    evaluate_prompt_with_real_chatresponder_shadow_call_v1,
    preflight_for_real_chatresponder_shadow_call_v1,
    routing_validator_preflight_v1,
)


# ---------------------------------------------------------------------------
# Local helpers (mirroring test_real_chatresponder_shadow_call_helpers_v1.py)
# ---------------------------------------------------------------------------

def _authorized_config(prompt_id="ordinary_task_behavior_001", **overrides):
    cfg = build_real_chatresponder_shadow_call_config_v1(
        real_call_authorized=True,
        allow_injected_callable=True,
        selected_prompt_ids=[prompt_id],
    )
    cfg.update(overrides)
    return cfg


def _contract(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior"):
    return build_real_chatresponder_shadow_call_blocker_contract_v1(prompt_id=prompt_id, family=family)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_callable():
    def _call(data):
        return {
            "property_label": "pass_property",
            "safe_summary": "Mock safe response.",
            "chatresponder_called": False,
        }
    return _call


def _get_prompt_item(prompt_id: str):
    prompt_set = build_default_controlled_behavior_prompt_set_v1()
    for item in prompt_set.get("prompts", []):
        if item.get("prompt_id") == prompt_id:
            return item
    raise ValueError(f"Prompt not found: {prompt_id}")


# ---------------------------------------------------------------------------
# Routing validator preflight shape
# ---------------------------------------------------------------------------

class TestRoutingValidatorPreflightShape:
    """routing_validator_preflight_v1 returns correct metadata shape."""

    def test_returns_safe_metadata_fields(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_001")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_type"] == "weslr_routing_validator_preflight_v1"
        assert "prompt_id" in result
        assert "family" in result
        assert "route_class" in result
        assert "alignment_status" in result
        assert "safe_to_call" in result
        assert "requires_mock" in result
        assert "mock_authorized" in result
        assert "blocked_by_boundary" in result
        assert "reason_labels" in result
        assert "matched_terms" in result
        assert result["routing_validator_applied"] is True
        assert result["raw_text_retained"] is False
        assert result["model_calls"] is False
        assert result["search_calls"] is False
        assert result["advisor_calls"] is False
        assert result["writes"] is False

    def test_no_raw_private_keys(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_001")
        result = routing_validator_preflight_v1(item)
        # Check exact keys, not substrings — raw_prompt_stored is fine, raw_prompt is not
        forbidden_exact = {"raw_text", "raw_prompt", "response_text", "final_answer", "full_conversation", "prompt_text"}
        result_keys = set(result.keys())
        found = forbidden_exact & result_keys
        assert not found, f"Forbidden exact keys found in preflight result: {found}"

        # Also ensure no forbidden key appears as a standalone substring in any key
        for key in result_keys:
            for forbidden in forbidden_exact:
                # raw_prompt_stored is allowed; raw_prompt alone is not
                if key == forbidden:
                    assert False, f"Forbidden exact key found: {key}"

    def test_keyword_prompt_allowed_without_mock(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_001")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_allowed"] is True
        assert result["route_class"] == "safe_keyword_branch"
        assert result["safe_to_call"] is True
        assert result["requires_mock"] is False
        assert result["blocked_by_boundary"] is False

    def test_planning_prompt_allowed_without_mock(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_002")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_allowed"] is True
        assert result["route_class"] == "safe_limited_ordinary_task"
        assert result["safe_to_call"] is True
        assert result["requires_mock"] is False


# ---------------------------------------------------------------------------
# Known failure case: ordinary_task_behavior_003
# ---------------------------------------------------------------------------

class TestOrdinaryTaskBehavior003:
    """The canonical misaligned prompt must be blocked without mock, allowed with mock."""

    def test_blocked_without_mock(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_003")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": False})
        assert result["preflight_allowed"] is False
        assert result["route_class"] == "forbidden_model_path"
        assert result["alignment_status"] == "mismatch"
        assert result["safe_to_call"] is False
        assert result["requires_mock"] is False
        assert result["blocked_by_boundary"] is True
        # Reason labels include mismatch + unsafe + model_path from validator
        assert "routing_validator_mismatch" in result["reason_labels"]
        assert "model_path_blocked" in result["reason_labels"]

    def test_allowed_with_mock_active(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_003")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": True})
        assert result["preflight_allowed"] is True
        assert result["route_class"] == "requires_generate_chat_mock"
        assert result["alignment_status"] == "aligned"
        assert result["safe_to_call"] is True
        assert result["requires_mock"] is True
        assert result["mock_authorized"] is True
        assert result["blocked_by_boundary"] is False

    def test_blocked_before_callable_construction_without_mock(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_003")
        observation = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
            item,
            config=_authorized_config("ordinary_task_behavior_003"),
            blocker_contract=_contract("ordinary_task_behavior_003", "ordinary_task_behavior"),
        )
        assert observation["preflight_allowed"] is False
        assert observation["blocked_by_boundary"] is True
        assert observation["call_attempted"] is False
        assert observation["chatresponder_called"] is False

    def test_allowed_with_mock_active_callable_constructed(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_003")
        cfg = _authorized_config("ordinary_task_behavior_003")
        cfg["generate_chat_mock_active"] = True
        observation = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
            item,
            shadow_callable=_mock_callable(),
            config=cfg,
            blocker_contract=_contract("ordinary_task_behavior_003", "ordinary_task_behavior"),
        )
        assert observation["preflight_allowed"] is True
        assert observation["call_attempted"] is True
        assert observation["chatresponder_called"] is False  # mock callable returns False
        assert observation["blocked_by_boundary"] is False


# ---------------------------------------------------------------------------
# Blocked families
# ---------------------------------------------------------------------------

class TestBlockedFamilies:
    """Blocked families remain blocked regardless of mock state."""

    def test_memory_honesty_blocked_without_mock(self) -> None:
        item = _get_prompt_item("memory_honesty_001")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": False})
        assert result["preflight_allowed"] is False
        assert result["blocked_by_boundary"] is True
        assert "unsupported_family_blocked" in result["reason_labels"]

    def test_memory_honesty_blocked_with_mock(self) -> None:
        item = _get_prompt_item("memory_honesty_001")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": True})
        assert result["preflight_allowed"] is False
        assert result["blocked_by_boundary"] is True
        assert "unsupported_family_blocked" in result["reason_labels"]

    def test_guardrail_preservation_blocked(self) -> None:
        item = _get_prompt_item("guardrail_preservation_001")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_allowed"] is False
        assert result["blocked_by_boundary"] is True

    def test_self_identity_blocked(self) -> None:
        item = _get_prompt_item("self_identity_boundaries_001")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_allowed"] is False
        assert result["blocked_by_boundary"] is True


# ---------------------------------------------------------------------------
# Search / currentness blocking
# ---------------------------------------------------------------------------

class TestSearchAndCurrentness:
    """Search/currentness prompts must be blocked."""

    def test_currentness_prompt_blocked(self) -> None:
        # evidence_source_boundaries_001 implies currentness/source
        item = _get_prompt_item("evidence_source_boundaries_001")
        result = routing_validator_preflight_v1(item)
        assert result["preflight_allowed"] is False
        assert result["route_class"] == "forbidden_search_or_advisor_path"
        assert "search_path_blocked" in result["reason_labels"]


# ---------------------------------------------------------------------------
# Metadata mismatch blocking
# ---------------------------------------------------------------------------

class TestMetadataMismatch:
    """Prompts with metadata/routing mismatch must be blocked without mock."""

    def test_non_canned_cognition_002_blocked(self) -> None:
        item = _get_prompt_item("non_canned_cognition_002")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": False})
        assert result["preflight_allowed"] is False
        assert result["alignment_status"] == "mismatch"
        assert "routing_validator_mismatch" in result["reason_labels"]
        assert "model_path_blocked" in result["reason_labels"]

    def test_conduct_alignment_blocked(self) -> None:
        item = _get_prompt_item("conduct_alignment_001")
        result = routing_validator_preflight_v1(item, config={"generate_chat_mock_active": False})
        assert result["preflight_allowed"] is False
        assert result["alignment_status"] == "mismatch"


# ---------------------------------------------------------------------------
# Safety: no ChatResponder import/call in test file
# ---------------------------------------------------------------------------

class TestNoChatResponderImport:
    """This test file must never import or call ChatResponder."""

    def test_no_chatresponder_import_in_source(self) -> None:
        import weslr.tests.test_routing_validator_safe_preflight_integration_v1 as mod
        import ast
        source_path = Path(mod.__file__)
        with open(source_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(source_path))
        forbidden = {"chat_responder", "respond_chat", "ChatResponder"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(part in forbidden for part in alias.name.split(".")):
                        assert False, f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[-1]
                if module in forbidden:
                    assert False, f"Forbidden import from: {node.module}"
                for alias in node.names:
                    if alias.name in forbidden:
                        assert False, f"Forbidden import: {alias.name}"

    def test_no_generate_chat_call(self) -> None:
        import weslr.tests.test_routing_validator_safe_preflight_integration_v1 as mod
        import ast
        source_path = Path(mod.__file__)
        with open(source_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "generate_chat":
                    assert False, "Forbidden generate_chat call found"

    def test_no_raw_private_keys_in_observation(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_001")
        observation = evaluate_prompt_with_real_chatresponder_shadow_call_v1(
            item,
            shadow_callable=_mock_callable(),
            config=_authorized_config("ordinary_task_behavior_001"),
            blocker_contract=_contract("ordinary_task_behavior_001", "ordinary_task_behavior"),
        )
        # Only check exact top-level keys; raw_prompt_stored / raw_prompt_available are allowed fields
        forbidden_exact = {"raw_text", "raw_prompt", "response_text", "final_answer", "full_conversation"}
        found = forbidden_exact & set(observation.keys())
        assert not found, f"Forbidden exact keys found in observation: {found}"


# ---------------------------------------------------------------------------
# Existing preflight still works alongside routing validator
# ---------------------------------------------------------------------------

class TestExistingPreflightCompatibility:
    """Existing preflight should still work when routing validator passes."""

    def test_existing_preflight_passes_after_routing_validator(self) -> None:
        item = _get_prompt_item("ordinary_task_behavior_001")
        # First, routing validator must pass
        rv = routing_validator_preflight_v1(item)
        assert rv["preflight_allowed"] is True
        # Then existing preflight should also pass
        preflight = preflight_for_real_chatresponder_shadow_call_v1(
            item,
            config=_authorized_config("ordinary_task_behavior_001"),
            blocker_contract=_contract("ordinary_task_behavior_001", "ordinary_task_behavior"),
        )
        assert preflight["preflight_allowed"] is True
        assert preflight["side_effects"]["chatresponder_called"] is False

    def test_existing_preflight_blocked_family_after_rv_pass(self) -> None:
        # memory_honesty: RV blocks it, so existing preflight never reached in evaluate_...
        item = _get_prompt_item("memory_honesty_001")
        rv = routing_validator_preflight_v1(item)
        assert rv["preflight_allowed"] is False
        # If we bypass RV and call existing preflight directly, it also blocks
        preflight = preflight_for_real_chatresponder_shadow_call_v1(
            item,
            config=_authorized_config("memory_honesty_001"),
            blocker_contract=_contract("memory_honesty_001", "memory_honesty"),
        )
        assert preflight["preflight_allowed"] is False
        assert "memory_namespace_required" in preflight["reason_labels"]
