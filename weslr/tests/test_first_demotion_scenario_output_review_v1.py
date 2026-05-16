"""Focused tests for first demotion scenario output review helpers V1."""

import pytest

from weslr.first_canned_helper_demotion_shadow_scenarios import (
    build_first_canned_helper_demotion_shadow_scenarios_v1,
)
from weslr.first_demotion_scenario_output_review import (
    ALLOWED_READINESS_LABELS_V1,
    ALLOWED_TARGET_BRANCHES_V1,
    CANDIDATE_RANK_ORDER_V1,
    build_first_demotion_scenario_output_reviews_v1,
    render_first_demotion_scenario_output_reviews_markdown_v1,
    summarize_first_demotion_scenario_output_reviews_v1,
    to_first_demotion_scenario_output_review_json_safe_v1,
    validate_first_demotion_scenario_output_review_v1,
    validate_first_demotion_scenario_output_reviews_bundle_v1,
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


def _by_target(bundle):
    return {review["target_branch"]: review for review in bundle["scenario_reviews"]}


def test_default_output_review_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    bundle = build_first_demotion_scenario_output_reviews_v1()

    assert bundle["review_bundle_type"] == "first_demotion_scenario_output_reviews_bundle_v1"
    assert bundle["schema_version"] == "1.0"
    assert bundle["scenario_review_count"] == 5
    assert bundle["recommended_first_design_candidate"] == "chat_responder_plan_helper"
    assert bundle["candidate_rank_order"] == CANDIDATE_RANK_ORDER_V1
    _assert_no_live_flags(bundle)
    assert bundle["requires_owner_approval"] is True
    assert bundle["validation"]["valid"] is True

    targets = {review["target_branch"] for review in bundle["scenario_reviews"]}
    assert targets == set(ALLOWED_TARGET_BRANCHES_V1)
    assert bundle["shadow_review_ready_count"] >= 1
    assert bundle["needs_more_shadow_detail_count"] >= 1
    for review in bundle["scenario_reviews"]:
        _assert_no_live_flags(review)
        assert review["validation"]["valid"] is True


def test_accepts_existing_scenario_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    scenario_bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()
    review_bundle = build_first_demotion_scenario_output_reviews_v1(scenario_bundle)

    assert review_bundle["scenario_review_count"] == 5
    assert review_bundle["validation"]["valid"] is True


def test_per_branch_quality_labels(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reviews = _by_target(build_first_demotion_scenario_output_reviews_v1())

    assert reviews["chat_responder_plan_helper"]["branch_quality_label"] == "strongest_first_design_candidate"
    assert reviews["chat_responder_email_helper"]["branch_quality_label"] == "strong_but_private_text_sensitive"
    assert reviews["chat_responder_lunch_helper"]["branch_quality_label"] == "moderate_low_risk_context_needed"
    assert reviews["chat_responder_workout_helper"]["branch_quality_label"] == "moderate_health_context_needed"
    assert reviews["chat_responder_code_bug_helper"]["branch_quality_label"] == "weak_debug_specificity_needed"

    assert "clarification_match" in reviews["chat_responder_email_helper"]["quality_signals"]
    assert "preference_context_boundary_needed" in reviews["chat_responder_lunch_helper"]["boundary_labels"]
    assert "health_context_boundary_needed" in reviews["chat_responder_workout_helper"]["boundary_labels"]
    assert "debug_context_boundary_needed" in reviews["chat_responder_code_bug_helper"]["boundary_labels"]


def test_readiness_labels_are_non_live(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = build_first_demotion_scenario_output_reviews_v1()

    for review in bundle["scenario_reviews"]:
        readiness = review["branch_readiness_label"]
        assert readiness in ALLOWED_READINESS_LABELS_V1
        assert readiness != "live_ready"
        assert "live" not in readiness
        assert review["safe_to_replace_live"] is False


def test_boundary_labels(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reviews = _by_target(build_first_demotion_scenario_output_reviews_v1())
    required = {
        "owner_approval_required",
        "no_live_replacement",
        "no_model_call",
        "no_web_search",
        "no_solver_execution",
        "no_answer_arbitration",
        "no_advisor_call",
    }

    for review in reviews.values():
        labels = set(review["boundary_labels"])
        assert required.issubset(labels)

    assert "private_text_boundary_needed" in reviews["chat_responder_email_helper"]["boundary_labels"]
    assert "health_context_boundary_needed" in reviews["chat_responder_workout_helper"]["boundary_labels"]
    assert "preference_context_boundary_needed" in reviews["chat_responder_lunch_helper"]["boundary_labels"]
    assert "debug_context_boundary_needed" in reviews["chat_responder_code_bug_helper"]["boundary_labels"]


@pytest.mark.parametrize("field", [
    "safe_to_replace_live",
    "runtime_wiring",
    "live_runtime_output",
    "model_calls",
    "advisor_calls",
    "web_search",
    "solver_execution",
    "answer_selection_arbitration",
])
def test_validation_rejects_live_drift_flags(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    review = build_first_demotion_scenario_output_reviews_v1()["scenario_reviews"][0]
    drifted = dict(review)
    drifted[field] = True

    validation = validate_first_demotion_scenario_output_review_v1(drifted)

    assert validation["valid"] is False


@pytest.mark.parametrize("field", ["final_answer", "response_text", "raw_prompt", "safe_prompt"])
def test_validation_rejects_forbidden_text_fields(field, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    review = build_first_demotion_scenario_output_reviews_v1()["scenario_reviews"][0]
    drifted = dict(review)
    drifted[field] = "do not expose this"

    validation = validate_first_demotion_scenario_output_review_v1(drifted)

    assert validation["valid"] is False


def test_validation_rejects_respond_chat_marker_and_live_ready_label(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    review = build_first_demotion_scenario_output_reviews_v1()["scenario_reviews"][0]

    marker = dict(review)
    marker["recommended_next_action"] = "call ChatResponder.respond_chat(" 
    assert validate_first_demotion_scenario_output_review_v1(marker)["valid"] is False

    live_ready = dict(review)
    live_ready["branch_readiness_label"] = "live_ready"
    assert validate_first_demotion_scenario_output_review_v1(live_ready)["valid"] is False


def test_bundle_validation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = build_first_demotion_scenario_output_reviews_v1()

    assert validate_first_demotion_scenario_output_reviews_bundle_v1(bundle)["valid"] is True

    drifted = dict(bundle)
    drifted["candidate_rank_order"] = ["unknown_branch"]
    assert validate_first_demotion_scenario_output_reviews_bundle_v1(drifted)["valid"] is False

    plan_second = dict(bundle)
    plan_second["candidate_rank_order"] = [
        "chat_responder_email_helper",
        "chat_responder_plan_helper",
        "chat_responder_lunch_helper",
        "chat_responder_workout_helper",
        "chat_responder_code_bug_helper",
    ]
    warning_categories = {w["category"] for w in validate_first_demotion_scenario_output_reviews_bundle_v1(plan_second)["warnings"]}
    assert "plan_not_ranked_first" in warning_categories

    code_strong = dict(bundle)
    reviews = [dict(review) for review in bundle["scenario_reviews"]]
    for review in reviews:
        if review["target_branch"] == "chat_responder_code_bug_helper":
            review["branch_quality_label"] = "strongest_first_design_candidate"
    code_strong["scenario_reviews"] = reviews
    warning_categories = {w["category"] for w in validate_first_demotion_scenario_output_reviews_bundle_v1(code_strong)["warnings"]}
    assert "code_bug_marked_strongest" in warning_categories


def test_summary_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = build_first_demotion_scenario_output_reviews_v1()
    summary = summarize_first_demotion_scenario_output_reviews_v1(bundle)
    rendered = _render(summary)

    assert summary["summary_type"] == "first_demotion_scenario_output_reviews_summary_v1"
    assert summary["scenario_review_count"] == 5
    assert summary["safe_to_replace_live"] is False
    assert "help me" not in rendered
    assert "final answer" not in rendered
    assert "private-zebra-candle" not in rendered
    assert "hidden prompt" not in rendered
    assert "answer key" not in rendered


def test_markdown_safety(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = build_first_demotion_scenario_output_reviews_v1()
    markdown = render_first_demotion_scenario_output_reviews_markdown_v1(bundle)
    rendered = markdown.lower()

    assert "scenario_review_count:5" in rendered
    assert "safe_to_replace_live:false" in rendered
    assert "runtime_wiring:false" in rendered
    assert "help me" not in rendered
    assert "final answer" not in rendered
    assert "private-zebra-candle" not in rendered
    assert "hidden prompt" not in rendered
    assert "answer key" not in rendered


def test_json_safe_copy_is_not_sanitizer_and_validator_catches_raw_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    copied = to_first_demotion_scenario_output_review_json_safe_v1({"nested": {"items": [1]}, "raw_text": "private"})
    copied["nested"]["items"].append(2)

    assert copied["raw_text"] == "private"
    review = build_first_demotion_scenario_output_reviews_v1()["scenario_reviews"][0]
    drifted = dict(review)
    drifted.update(copied)

    assert validate_first_demotion_scenario_output_review_v1(drifted)["valid"] is False


def test_existing_scenario_harness_still_passes_in_process(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = build_first_canned_helper_demotion_shadow_scenarios_v1()

    assert bundle["scenario_count"] == 5
    assert bundle["validation"]["valid"] is True
    assert all(result["validation"]["valid"] is True for result in bundle["scenario_results"])
