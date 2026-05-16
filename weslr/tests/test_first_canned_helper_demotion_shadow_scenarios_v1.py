"""Focused tests for first canned helper demotion shadow scenarios V1."""

from pathlib import Path

import pytest

from weslr.first_canned_helper_demotion_shadow_scenarios import (
    ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1,
    FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1,
    build_first_canned_helper_demotion_shadow_scenario_v1,
    build_first_canned_helper_demotion_shadow_scenarios_v1,
    render_first_canned_helper_demotion_shadow_scenarios_markdown_v1,
    summarize_first_canned_helper_demotion_shadow_scenarios_v1,
    to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1,
    validate_first_canned_helper_demotion_shadow_scenario_v1,
    validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1,
)


def _render(obj):
    return repr(obj).lower()


def _assert_no_live_flags(obj):
    assert obj["safe_to_replace_live"] is False
    assert obj["runtime_wiring"] is False
    assert obj["live_runtime_output"] is False
    assert obj["model_calls"] is False
    assert obj["advisor_calls"] is False
    assert obj["web_search"] is False
    assert obj["solver_execution"] is False
    assert obj["answer_selection_arbitration"] is False
    assert obj["raw_text_stored"] is False


def test_default_scenario_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    assert bundle["bundle_type"] == "first_canned_helper_demotion_shadow_scenarios_bundle_v1"
    assert bundle["schema_version"] == "1.0"
    assert bundle["layer"] == "WESLR_RUNTIME_CHANGE_helper_test_source_only"
    assert bundle["live_weslr_behavior_changed"] is False
    assert bundle["scenario_count"] == 5
    assert bundle["valid_count"] == 5
    assert bundle["invalid_count"] == 0
    assert bundle["demotion_candidate_count"] == 5
    assert bundle["owner_approval_required_count"] == 5
    _assert_no_live_flags(bundle)
    assert bundle["validation"]["valid"] is True

    targets = {result["target_branch"] for result in bundle["scenario_results"]}
    assert targets == set(ALLOWED_FIRST_CANNED_HELPER_TARGET_BRANCHES_V1)
    for result in bundle["scenario_results"]:
        assert result["shadow_comparison_available"] is True
        assert result["requires_owner_approval"] is True
        _assert_no_live_flags(result)
        assert result["validation"]["valid"] is True


def test_each_target_branch_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()
    targets = {result["target_branch"] for result in bundle["scenario_results"]}

    assert "chat_responder_lunch_helper" in targets
    assert "chat_responder_workout_helper" in targets
    assert "chat_responder_plan_helper" in targets
    assert "chat_responder_email_helper" in targets
    assert "chat_responder_code_bug_helper" in targets


def test_scenario_results_use_existing_shadow_and_comparison_helpers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    for result in bundle["scenario_results"]:
        assert result["helper_sources_reused"]["unified_response_formation_shadow"] is True
        assert result["helper_sources_reused"]["canned_helper_shadow_comparison"] is True
        assert result["helper_sources_reused"]["meaning_reuse_native_dry_pipeline_indirect"] is True
        assert result["selected_shadow_candidate_family"]
        assert result["recommended_disposition"]
        assert result["comparison_available"] is True
        assert result["comparison_metadata"]["comparison_type"] == "canned_helper_shadow_comparison_v1"
        assert "validation" in result


def test_no_live_replacement_flags(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    _assert_no_live_flags(bundle)
    for result in bundle["scenario_results"]:
        _assert_no_live_flags(result)


@pytest.mark.parametrize("target", [
    "chat_responder_wife_partner_helper",
    "chat_responder_low_focus_fallback",
    "chat_responder_vague_fallback",
    "chat_responder_identity_self_surface",
    "chat_responder_model_path",
    "evidence_bridge_guardrail_or_fallback",
    "deterministic_handler_write_capable_surface",
    "staging_arbiter_raw_message_log_surface",
    "deterministic_handler_status_surface",
    "unknown_target_branch",
])
def test_out_of_scope_branch_rejection(target, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    scenario = dict(FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1[0])
    scenario["target_branch"] = target

    with pytest.raises(ValueError):
        build_first_canned_helper_demotion_shadow_scenario_v1(scenario)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1([scenario])
    assert bundle["valid_count"] == 0
    assert bundle["invalid_count"] == 1
    assert bundle["validation"]["valid"] is False


def test_no_raw_prompt_leakage_in_summary_or_markdown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    private_phrase = "private-zebra-candle-728391"
    scenario = dict(FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1[0])
    scenario["safe_prompt"] = f"Help me plan this {private_phrase}."

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1([scenario])
    summary = summarize_first_canned_helper_demotion_shadow_scenarios_v1(bundle)
    markdown = render_first_canned_helper_demotion_shadow_scenarios_markdown_v1(bundle)
    rendered_public = _render({"summary": summary, "markdown": markdown})

    assert private_phrase not in rendered_public
    assert "help me plan this" not in rendered_public
    assert "hidden prompt" not in rendered_public
    assert "answer key" not in rendered_public
    assert "protected material" not in rendered_public

    result_rendered = _render(bundle["scenario_results"][0])
    assert private_phrase not in result_rendered
    assert bundle["scenario_results"][0]["validation"]["valid"] is True


def test_expected_dispositions_and_no_auto_owner_approval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    for result in bundle["scenario_results"]:
        assert result["recommended_disposition"] in {"demote_after_shadow_validation", "shadow_compare_more"}
        assert result["safe_to_replace_live"] is False
        assert result["requires_owner_approval"] is True
        assert result["demotion_candidate"] is True


def test_summary_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()
    summary = summarize_first_canned_helper_demotion_shadow_scenarios_v1(bundle)
    rendered = _render(summary)

    assert summary["summary_type"] == "first_canned_helper_demotion_shadow_scenarios_summary_v1"
    assert summary["scenario_count"] == 5
    assert summary["safe_to_replace_live"] is False
    assert "help me" not in rendered
    assert "legacy full answer" not in rendered
    assert "hidden prompt" not in rendered
    assert "answer key" not in rendered
    assert "protected material" not in rendered


def test_markdown_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()
    markdown = render_first_canned_helper_demotion_shadow_scenarios_markdown_v1(bundle)
    rendered = markdown.lower()

    assert "scenario_count:5" in rendered
    assert "safe_to_replace_live:false" in rendered
    assert "runtime_wiring:false" in rendered
    assert "help me" not in rendered
    assert "legacy full answer" not in rendered
    assert "hidden prompt" not in rendered
    assert "answer key" not in rendered
    assert "protected material" not in rendered


def test_json_safe_copy_is_not_sanitizer_and_validator_catches_raw_text():
    original = {"nested": {"items": [1]}, "raw_text": "private"}
    copied = to_first_canned_helper_demotion_shadow_scenarios_json_safe_v1(original)

    copied["nested"]["items"].append(2)

    assert original["nested"]["items"] == [1]
    assert copied["raw_text"] == "private"
    result = validate_first_canned_helper_demotion_shadow_scenario_v1({
        "scenario_result_type": "first_canned_helper_demotion_shadow_scenario_v1",
        "slice_type": "first_canned_helper_demotion_shadow_slice_v1",
        "target_branch": "chat_responder_lunch_helper",
        "legacy_surface": "chat_responder_topic_helper_ordinary",
        "safe_to_replace_live": False,
        "requires_owner_approval": True,
        "runtime_wiring": False,
        "live_runtime_output": False,
        "model_calls": False,
        "advisor_calls": False,
        "web_search": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "raw_text_stored": False,
        **copied,
    })
    assert result["valid"] is False


def test_bundle_validation_detects_drift(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()
    assert validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(bundle)["valid"] is True

    added = dict(bundle)
    added["scenario_results"] = list(bundle["scenario_results"]) + [
        {**bundle["scenario_results"][0], "target_branch": "chat_responder_wife_partner_helper"}
    ]
    added["scenario_count"] = 6
    added_result = validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(added)
    assert added_result["valid"] is False

    live = dict(bundle)
    live["runtime_wiring"] = True
    assert validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(live)["valid"] is False

    missing_owner = dict(bundle)
    missing_results = [dict(result) for result in bundle["scenario_results"]]
    missing_results[0]["requires_owner_approval"] = False
    missing_owner["scenario_results"] = missing_results
    missing_owner["owner_approval_required_count"] = 4
    assert validate_first_canned_helper_demotion_shadow_scenarios_bundle_v1(missing_owner)["valid"] is False


def test_no_side_effects_runtime_edits_or_persistence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    assert bundle["model_calls"] is False
    assert bundle["advisor_calls"] is False
    assert bundle["web_search"] is False
    assert bundle["solver_execution"] is False
    assert bundle["answer_selection_arbitration"] is False
    assert not (tmp_path / ".weslr").exists()
    assert Path("weslr/chat_responder.py").exists() is False
    assert bundle["live_weslr_behavior_changed"] is False
