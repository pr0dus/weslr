"""Focused tests for plan helper demotion pre-live plan helpers V1."""

import copy

import pytest

from weslr.plan_helper_demotion_prelive_plan import (
    EXCLUDED_BRANCHES_V1,
    FEATURE_FLAG_V1,
    TARGET_BRANCH_V1,
    TARGET_FILE_V1,
    build_plan_helper_demotion_prelive_plan_v1,
    render_plan_helper_demotion_prelive_plan_markdown_v1,
    summarize_plan_helper_demotion_prelive_plan_v1,
    to_plan_helper_demotion_prelive_plan_json_safe_v1,
    validate_plan_helper_demotion_prelive_plan_v1,
)


def _render(obj):
    return repr(obj).lower()


def _assert_no_live_flags(plan):
    assert plan["implementation_allowed_now"] is False
    assert plan["chat_responder_edit_allowed_now"] is False
    assert plan["live_weslr_behavior_changed"] is False
    assert plan["safe_to_replace_live"] is False
    assert plan["runtime_wiring"] is False
    assert plan["live_runtime_output"] is False
    assert plan["model_calls"] is False
    assert plan["advisor_calls"] is False
    assert plan["web_search"] is False
    assert plan["solver_execution"] is False
    assert plan["answer_selection_arbitration"] is False
    assert plan["memory_writes"] is False
    assert plan["raw_text_stored"] is False
    assert plan["weslr_runtime_state_created"] is False


def test_prelive_plan_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()

    assert plan["plan_type"] == "plan_helper_demotion_prelive_plan_v1"
    assert plan["schema_version"] == "1.0"
    assert plan["target_branch"] == TARGET_BRANCH_V1
    assert plan["target_file"] == TARGET_FILE_V1
    assert plan["approx_line_range"] == "1787-1792"
    assert plan["legacy_surface"] == "chat_responder_topic_helper_ordinary"
    assert plan["selected_shadow_family"] == "ordinary_task_plan"
    assert plan["quality_label"] == "strongest_first_design_candidate"
    assert plan["validation"]["valid"] is True


def test_no_live_behavior_allowed_now(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()

    _assert_no_live_flags(plan)


def test_owner_approval_feature_flag_fallback_rollback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()

    assert plan["owner_approval_required_before_implementation"] is True
    assert plan["feature_flag"] == FEATURE_FLAG_V1
    assert plan["feature_flag_default"] is False
    assert plan["fallback_required"] is True
    assert plan["rollback_required"] is True
    assert plan["owner_approval_gate"]
    assert plan["rollback_plan"]


def test_scope_excludes_other_branches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()
    target_scope = plan["target_scope"]

    assert target_scope["target_branch"] == TARGET_BRANCH_V1
    assert target_scope["one_branch_only"] is True
    assert target_scope["non_plan_branches_unchanged"] is True
    assert target_scope["guardrails_unchanged"] is True
    assert target_scope["evidence_search_paths_unchanged"] is True
    assert target_scope["memory_write_paths_unchanged"] is True
    assert TARGET_BRANCH_V1 not in plan["excluded_branches"]
    assert "chat_responder_lunch_helper" in plan["excluded_branches"]
    assert "chat_responder_workout_helper" in plan["excluded_branches"]
    assert "chat_responder_email_helper" in plan["excluded_branches"]
    assert "chat_responder_code_bug_helper" in plan["excluded_branches"]
    assert "deterministic_write_capable_handlers" in plan["excluded_branches"]
    assert "deterministic_external_search_handlers" in plan["excluded_branches"]
    assert "status_command_surfaces" in plan["excluded_branches"]


@pytest.mark.parametrize("branch", list(EXCLUDED_BRANCHES_V1)[:10])
def test_validation_rejects_excluded_target_branch(branch, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted["target_branch"] = branch
    drifted["target_scope"]["target_branch"] = branch

    validation = validate_plan_helper_demotion_prelive_plan_v1(drifted)

    assert validation["valid"] is False


def test_future_diff_plan_safe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()
    diff_plan = plan["future_diff_plan"]
    rendered = _render(diff_plan)

    assert diff_plan
    assert TARGET_BRANCH_V1 in rendered
    assert "one_branch_only" in rendered
    assert "implementation_allowed_now': false" in rendered or '"implementation_allowed_now": false' in rendered
    assert "broad runtime replacement" not in rendered
    assert "chat_responder_lunch_helper" not in rendered
    assert "chat_responder_workout_helper" not in rendered
    assert "chat_responder_email_helper" not in rendered
    assert "chat_responder_code_bug_helper" not in rendered


def test_future_tests_required(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()
    tests = "\n".join(plan["future_tests_required"]).lower()

    assert "plan branch only" in tests
    assert "non-plan lunch helper unchanged" in tests
    assert "non-plan workout helper unchanged" in tests
    assert "non-plan email helper unchanged" in tests
    assert "non-plan code bug helper unchanged" in tests
    assert "guardrail" in tests
    assert "no model advisor search calls" in tests
    assert "no memory writes" in tests
    assert "no .weslr state creation" in tests
    assert "no raw private text storage" in tests
    assert "fallback" in tests
    assert "rollback" in tests
    assert "release gate" in tests
    assert "release check" in tests


@pytest.mark.parametrize("field", [
    "implementation_allowed_now",
    "chat_responder_edit_allowed_now",
    "live_weslr_behavior_changed",
    "safe_to_replace_live",
    "runtime_wiring",
    "live_runtime_output",
    "model_calls",
    "advisor_calls",
    "web_search",
    "memory_writes",
    "raw_text_stored",
    "weslr_runtime_state_created",
])
def test_validation_rejects_live_drift(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted[field] = True

    validation = validate_plan_helper_demotion_prelive_plan_v1(drifted)

    assert validation["valid"] is False


@pytest.mark.parametrize("field", ["feature_flag_default"])
def test_validation_rejects_enabled_default(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted[field] = True

    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


@pytest.mark.parametrize("field", ["fallback_required", "rollback_required", "owner_approval_required_before_implementation"])
def test_validation_rejects_missing_required_true_flags(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted[field] = False

    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


@pytest.mark.parametrize("field", ["final_answer", "response_text", "raw_prompt", "safe_prompt", "raw_text", "normalized_text", "tokens"])
def test_validation_rejects_forbidden_fields(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted[field] = "do not expose this"

    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_validation_rejects_respond_chat_marker_and_live_ready_wording(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()

    marker = copy.deepcopy(plan)
    marker["unsafe_note"] = "call ChatResponder.respond_chat("
    assert validate_plan_helper_demotion_prelive_plan_v1(marker)["valid"] is False

    live_ready = copy.deepcopy(plan)
    live_ready["unsafe_note"] = "this is live-ready now"
    assert validate_plan_helper_demotion_prelive_plan_v1(live_ready)["valid"] is False


def test_validation_warns_for_missing_plan_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    drifted = copy.deepcopy(plan)
    drifted["future_diff_plan"] = []
    drifted["future_tests_required"] = []
    drifted["rollback_plan"] = []
    drifted["smoke_tests"] = []
    drifted["owner_approval_gate"] = []

    validation = validate_plan_helper_demotion_prelive_plan_v1(drifted)
    warning_categories = {warning["category"] for warning in validation["warnings"]}

    assert validation["valid"] is True
    assert "future_diff_plan_missing" in warning_categories
    assert "future_tests_missing" in warning_categories
    assert "rollback_plan_missing" in warning_categories
    assert "smoke_tests_missing" in warning_categories
    assert "owner_approval_gate_missing" in warning_categories


def test_no_raw_prompt_or_final_answer_text_in_default_plan(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plan = build_plan_helper_demotion_prelive_plan_v1()
    rendered = _render(plan)

    assert "raw_prompt" not in rendered
    assert "safe_prompt" not in rendered
    assert "final_answer" not in rendered
    assert "response_text" not in rendered
    assert "private-zebra-candle" not in rendered
    assert "https://" not in rendered


def test_summary_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    summary = summarize_plan_helper_demotion_prelive_plan_v1(plan)
    rendered = _render(summary)

    assert summary["summary_type"] == "plan_helper_demotion_prelive_plan_summary_v1"
    assert summary["target_branch"] == TARGET_BRANCH_V1
    assert summary["target_file"] == TARGET_FILE_V1
    assert summary["future_diff_step_count"] == len(plan["future_diff_plan"])
    assert summary["future_test_count"] == len(plan["future_tests_required"])
    assert summary["excluded_branch_count"] == len(plan["excluded_branches"])
    assert "raw_prompt" not in rendered
    assert "final_answer" not in rendered
    assert "response_text" not in rendered
    assert "private-zebra-candle" not in rendered


def test_markdown_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    markdown = render_plan_helper_demotion_prelive_plan_markdown_v1(plan)
    rendered = markdown.lower()

    assert "# plan helper demotion pre-live plan v1" in rendered
    assert TARGET_BRANCH_V1 in markdown
    assert "future_diff_step_count" in rendered
    assert "raw_prompt" not in rendered
    assert "final_answer" not in rendered
    assert "response_text" not in rendered
    assert "private-zebra-candle" not in rendered
    assert "hidden prompt" not in rendered
    assert "answer key" not in rendered


def test_json_safe_copy_is_not_sanitizer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    obj = {"raw_text": "private-zebra-candle-12345"}
    copied = to_plan_helper_demotion_prelive_plan_json_safe_v1(obj)

    assert copied == obj
    assert copied is not obj
    assert validate_plan_helper_demotion_prelive_plan_v1(copied)["valid"] is False


def test_validation_rejects_private_like_url_and_claim_markers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()

    url = copy.deepcopy(plan)
    url["unsafe_note"] = "see https://example.invalid/source"
    assert validate_plan_helper_demotion_prelive_plan_v1(url)["valid"] is False

    token = copy.deepcopy(plan)
    token["unsafe_note"] = "private-zebra-candle-12345"
    assert validate_plan_helper_demotion_prelive_plan_v1(token)["valid"] is False

    claim = copy.deepcopy(plan)
    claim["unsafe_note"] = "I have a soul"
    assert validate_plan_helper_demotion_prelive_plan_v1(claim)["valid"] is False
