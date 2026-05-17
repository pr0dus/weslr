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

    assert validation["valid"] is False
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

def test_approval_marker_schema_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()

    assert plan["required_owner_approval_marker"] == "APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1"
    assert plan["required_live_task_name"] == "IMPLEMENT_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1"
    assert plan["live_task_must_declare"] == "WESLR_RUNTIME_CHANGE live behavior"
    assert plan["metadata_is_owner_approval"] is False
    assert plan["owner_approval_granted"] is False

    for field, value in [
        ("metadata_is_owner_approval", True),
        ("owner_approval_granted", True),
        ("required_owner_approval_marker", "WRONG"),
        ("required_live_task_name", "WRONG"),
        ("live_task_must_declare", "WRONG"),
    ]:
        drifted = copy.deepcopy(plan)
        drifted[field] = value
        assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_owner_approval_gate_completeness_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    gate = "\n".join(plan["owner_approval_gate"]).lower()

    for clause in [
        "approve_weslr_plan_helper_live_demotion_slice_v1",
        "implement_weslr_plan_helper_live_demotion_slice_v1",
        "no unrelated files changed",
        "no model calls",
        "no advisor calls",
        "no web search calls",
        "no memory writes",
        "no .weslr runtime state",
        "no raw private text storage",
        "no solver execution",
        "no answer-selection arbitration",
        "release gate required",
        "release check required",
    ]:
        assert clause in gate

    drifted = copy.deepcopy(plan)
    drifted["owner_approval_gate"] = [item for item in drifted["owner_approval_gate"] if "no unrelated files" not in item]
    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_rollback_command_completeness_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    rollback = "\n".join(plan["rollback_plan"]).lower()

    for clause in [
        "git rev-parse head",
        "git diff --stat",
        "git diff",
        "disable weslr_enable_plan_helper_demotion_v1",
        "git revert <live-slice-commit>",
        "python -m pytest -q weslr/tests/test_plan_helper_live_demotion_slice_v1.py",
        "python3 weslr/tests/release_gate_v1.py",
        "bash scripts/weslr_release_check.sh",
    ]:
        assert clause in rollback

    drifted = copy.deepcopy(plan)
    drifted["rollback_plan"] = [item for item in drifted["rollback_plan"] if "git diff --stat" not in item]
    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_future_diff_boundaries_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    diff_text = _render(plan["future_diff_plan"])

    assert "weslr/chat_responder.py" in diff_text
    assert "chat_responder_plan_helper" in diff_text
    assert "1787-1792" in diff_text
    assert "weslr/tests/test_plan_helper_live_demotion_slice_v1.py" in diff_text
    assert "no_main_py" in diff_text
    assert "no_staging_server" in diff_text
    assert "no_voice_ui_persistence_files" in diff_text
    assert "chat_responder_lunch_helper" not in diff_text
    assert "main.py" not in diff_text
    assert "deploy/staging" not in diff_text

    drifted = copy.deepcopy(plan)
    drifted["future_diff_plan"].append({"label": "broad router", "target": "all chat_responder branches"})
    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False

    drifted = copy.deepcopy(plan)
    drifted["future_diff_plan"].append({"label": "non_plan_branch", "target": "chat_responder_lunch_helper"})
    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_future_tests_required_strengthened_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    tests = "\n".join(plan["future_tests_required"]).lower()

    for clause in [
        "feature flag default false",
        "exact plan trigger only",
        "no broad route replacement",
        "no unrelated files changed",
        "no solver execution",
        "no answer selection arbitration",
        "fallback path used if formation fails",
        "old canned behavior still available by direct fallback assertion",
    ]:
        assert clause in tests

    drifted = copy.deepcopy(plan)
    drifted["future_tests_required"] = [item for item in drifted["future_tests_required"] if "exact plan trigger only" not in item]
    assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_implementation_approval_packet_and_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    packet = plan["implementation_approval_packet"]

    assert packet["approval_status"] == "not_requested"
    assert packet["owner_approval_granted"] is False
    assert packet["metadata_is_approval"] is False
    assert packet["approved_target_branch"] == TARGET_BRANCH_V1
    assert packet["approved_target_file"] == TARGET_FILE_V1
    assert packet["approved_scope"] == "one_branch_only"

    for field, value in [
        ("approval_status", "approved"),
        ("owner_approval_granted", True),
        ("metadata_is_approval", True),
        ("approved_target_branch", "chat_responder_lunch_helper"),
        ("approved_target_file", "main.py"),
        ("approved_scope", "all_branches"),
    ]:
        drifted = copy.deepcopy(plan)
        drifted["implementation_approval_packet"][field] = value
        assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False


def test_summary_markdown_refined_approval_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    summary = summarize_plan_helper_demotion_prelive_plan_v1(plan)
    markdown = render_plan_helper_demotion_prelive_plan_markdown_v1(plan).lower()

    assert summary["owner_approval_granted"] is False
    assert summary["metadata_is_owner_approval"] is False
    assert summary["required_owner_approval_marker_present"] is True
    assert summary["rollback_command_count"] == len(plan["rollback_plan"])
    assert summary["exact_diff_boundary_present"] is True
    assert "owner_approval_granted: false" in markdown
    assert "metadata_is_owner_approval: false" in markdown
    assert "required_owner_approval_marker_present: true" in markdown
    assert "rollback_command_count" in markdown
    assert "exact_diff_boundary_present: true" in markdown
    assert "raw_prompt" not in markdown
    assert "final_answer" not in markdown
    assert "response_text" not in markdown
    assert "https://" not in markdown


def test_validation_rejects_solver_and_arbitration_drift(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plan = build_plan_helper_demotion_prelive_plan_v1()
    for field in ["solver_execution", "answer_selection_arbitration"]:
        drifted = copy.deepcopy(plan)
        drifted[field] = True
        assert validate_plan_helper_demotion_prelive_plan_v1(drifted)["valid"] is False
