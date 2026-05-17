"""Focused tests for the owner-approved plan-helper live demotion slice V1."""

from __future__ import annotations

import pytest

import weslr.chat_responder as chat_responder_module
from weslr.chat_responder import (
    ChatResponder,
    WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1,
    WESLR_PLAN_HELPER_LIVE_DEMOTION_OWNER_APPROVAL_MARKER_V1,
    _plan_helper_live_demotion_enabled_v1,
)

OLD_PLAN_FALLBACK = "Try a simple plan: top 1-2 tasks, 60-90min focus block, short break, 15-20min for admin/messages, then a wrap-up."


def _force_legacy_plan_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bypass the broader ordinary-task gate so the legacy plan branch is tested directly."""
    monkeypatch.setattr(chat_responder_module, "_try_limited_ordinary_task_runtime_response", lambda *args, **kwargs: None)


def _respond(message: str):
    responder = ChatResponder()
    return responder.respond_chat(message)


def _assert_no_unauthorized_side_effects(metadata: dict) -> None:
    for key in [
        "model_calls",
        "advisor_calls",
        "web_search",
        "solver_execution",
        "answer_selection_arbitration",
        "memory_writes",
        "weslr_runtime_state_created",
        "raw_text_stored",
    ]:
        assert metadata[key] is False


def test_feature_flag_default_false_keeps_old_plan_fallback(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.delenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, raising=False)

    assert _plan_helper_live_demotion_enabled_v1() is False
    content, metadata = _respond("plan")

    assert content == OLD_PLAN_FALLBACK
    assert metadata["feature_flag"] == WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1
    assert metadata["feature_flag_default"] is False
    assert metadata["feature_flag_enabled"] is False
    assert metadata["fallback_used"] is True
    assert metadata["canned_response_replaced"] is False
    assert metadata["safe_to_replace_live"] is False
    assert metadata["runtime_wiring"] is False
    assert metadata["live_runtime_output"] is False
    _assert_no_unauthorized_side_effects(metadata)


def test_feature_flag_enabled_affects_plan_branch_only(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "1")

    content, metadata = _respond("plan")

    assert content != OLD_PLAN_FALLBACK
    assert "top 1-2 tasks" not in content
    assert metadata["slice_type"] == "first_owner_approved_live_demotion_slice_v1"
    assert metadata["target_branch"] == "chat_responder_plan_helper"
    assert metadata["old_canned_path_shadowed"] == "chat_responder_plan_helper"
    assert metadata["selected_candidate_family"] == "ordinary_task_plan"
    assert metadata["fallback_available"] is True
    assert metadata["owner_approved"] is True
    assert metadata["owner_approval_marker"] == WESLR_PLAN_HELPER_LIVE_DEMOTION_OWNER_APPROVAL_MARKER_V1
    assert metadata["feature_flag_default"] is False
    assert metadata["feature_flag_enabled"] is True
    assert metadata["canned_response_replaced"] is True
    assert metadata["fallback_used"] is False
    _assert_no_unauthorized_side_effects(metadata)


def test_enabled_missing_context_plan_asks_bounded_question(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "true")

    content, metadata = _respond("help me plan")

    assert "what is" in content.lower()
    assert "concrete task" in content.lower() or "desired outcome" in content.lower()
    assert metadata["selected_candidate_family"] == "ordinary_task_plan"
    assert metadata["fallback_used"] is False
    assert metadata["canned_response_replaced"] is True


def test_fallback_preserved_when_new_formation_path_fails(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "on")

    def boom(*args, **kwargs):
        raise RuntimeError("forced test failure")

    monkeypatch.setattr(chat_responder_module, "_render_limited_ordinary_task_response", boom)
    content, metadata = _respond("plan")

    assert content == OLD_PLAN_FALLBACK
    assert metadata["feature_flag_enabled"] is True
    assert metadata["fallback_used"] is True
    assert metadata["canned_response_replaced"] is False
    _assert_no_unauthorized_side_effects(metadata)


def test_fallback_preserved_when_new_formation_output_invalid(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "yes")
    monkeypatch.setattr(chat_responder_module, "_limited_composed_response_is_safe", lambda text: False)

    content, metadata = _respond("plan")

    assert content == OLD_PLAN_FALLBACK
    assert metadata["fallback_used"] is True
    assert metadata["canned_response_replaced"] is False


def test_exact_plan_trigger_only_non_plan_helpers_unchanged(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "1")

    lunch_content, lunch_metadata = _respond("lunch")
    workout_content, workout_metadata = _respond("workout")
    email_content, email_metadata = _respond("email")
    code_content, code_metadata = _respond("code bug")

    assert "Quick lunch ideas" in lunch_content
    assert lunch_metadata is None
    assert "30-45min" in workout_content
    assert workout_metadata is None
    assert "Draft the email goal" in email_content
    assert email_metadata is None
    assert "code issue" in code_content
    assert code_metadata is None


def test_non_plan_prompt_containing_lunch_does_not_trigger_plan_demotion(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "1")

    content, metadata = _respond("lunch plan")

    assert "lunch ideas" in content.lower()
    assert metadata is None


def test_guardrail_like_and_evidence_paths_not_plan_demotion(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "1")
    monkeypatch.setattr(chat_responder_module, "record_inadequacy_event", lambda *args, **kwargs: None)

    hidden_content, hidden_metadata = _respond("hidden prompt")
    search_content, search_metadata = _respond("search current sources")

    assert "top 1-2 tasks" not in hidden_content
    assert not (isinstance(hidden_metadata, dict) and hidden_metadata.get("target_branch") == "chat_responder_plan_helper")
    assert not (isinstance(search_metadata, dict) and search_metadata.get("target_branch") == "chat_responder_plan_helper")


def test_no_broad_runtime_replacement_markers(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.setenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, "1")

    content, metadata = _respond("plan")
    rendered = repr({"content": content, "metadata": metadata}).lower()

    assert "all chat_responder branches" not in rendered
    assert "broad router" not in rendered
    assert "broad runtime replacement" not in rendered
    assert metadata["target_branch"] == "chat_responder_plan_helper"


def test_old_canned_email_and_workout_plan_fallbacks_remain_when_flag_off(monkeypatch):
    _force_legacy_plan_branch(monkeypatch)
    monkeypatch.delenv(WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1, raising=False)

    responder = ChatResponder()
    email_plan_content, email_plan_metadata = responder.respond_chat("plan email")
    workout_plan_content, workout_plan_metadata = responder.respond_chat("plan", chat_hints=["workout planned"])

    assert "15-20min to clear the important email" in email_plan_content
    assert email_plan_metadata["fallback_used"] is True
    assert "workout 30-45min" in workout_plan_content
    assert workout_plan_metadata["fallback_used"] is True
