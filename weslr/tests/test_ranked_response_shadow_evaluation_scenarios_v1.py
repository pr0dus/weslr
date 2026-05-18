from __future__ import annotations

import inspect

from weslr import ranked_response_shadow_evaluation_scenarios as scenarios


def corpus():
    return scenarios.build_ranked_response_shadow_scenario_corpus_v1()


def by_category(category: str) -> dict:
    return next(item for item in corpus() if item["category"] == category)


def run_category(category: str) -> dict:
    return scenarios.run_ranked_response_shadow_scenario_v1(by_category(category))


# 1
def test_corpus_contains_all_20_required_categories():
    categories = {item["category"] for item in corpus()}
    assert set(scenarios.REQUIRED_CATEGORIES_V1).issubset(categories)
    assert len(categories) == 20


# 2
def test_scenario_ids_are_unique():
    ids = [item["scenario_id"] for item in corpus()]
    assert len(ids) == len(set(ids))


# 3
def test_each_scenario_validates():
    for item in corpus():
        validation = scenarios.validate_ranked_response_shadow_scenario_v1(item)
        assert validation["valid"], (item["scenario_id"], validation["reason_labels"])


# 4
def test_corpus_validates():
    validation = scenarios.validate_ranked_response_shadow_scenario_corpus_v1(corpus())
    assert validation["valid"], validation["reason_labels"]


# 5
def test_corpus_runner_returns_at_least_20_scenarios():
    result = scenarios.run_ranked_response_shadow_scenario_corpus_v1()
    assert result["scenario_count"] >= 20
    assert result["category_count"] == 20


# 6
def test_corpus_runner_passes_all_scenarios():
    result = scenarios.run_ranked_response_shadow_scenario_corpus_v1()
    assert result["failed_count"] == 0
    assert result["passed_count"] == result["scenario_count"]
    assert result["validation_status"] == "pass"


# 7
def test_scenario_runner_produces_no_final_answer():
    result = run_category("context_variation")
    assert result["final_answer_generated"] is False
    assert result["final_answer_text_present"] is False


# 8
def test_scenario_runner_retains_no_raw_prompt_response():
    result = run_category("evidence_variation")
    assert result["raw_prompt_retained"] is False
    assert result["raw_response_retained"] is False


# 9
def test_scenario_runner_makes_no_model_search_advisor_calls():
    result = run_category("unauthorized_model_search_advisor_requirement")
    assert result["model_call_made"] is False
    assert result["search_call_made"] is False
    assert result["advisor_call_made"] is False


# 10
def test_scenario_runner_performs_no_persistence():
    result = run_category("memory_relevance_boundary")
    assert result["persistence_performed"] is False


# 11
def test_context_variation_scenario_selects_expected_label():
    result = run_category("context_variation")
    assert result["selected_label"] == by_category("context_variation")["expected_selected_label"] == "strong_fit"


# 12
def test_evidence_variation_enforces_evidence_expectation():
    result = run_category("evidence_variation")
    assert "required_evidence_not_satisfied" in result["observed_rejection_labels"]
    assert result["expected_rejections_ok"] is True


# 13
def test_domain_variation_changes_domain_context_metadata():
    item = by_category("domain_variation")
    assert item["state_frame_input"]["domain_context"]["domain"] == "hospital"
    result = run_category("domain_variation")
    assert "domain_or_legal_moral_boundary_violation" in result["observed_rejection_labels"]


# 14
def test_memory_relevance_boundary_rejects_unprovenanced_stale_memory():
    result = run_category("memory_relevance_boundary")
    assert "required_provenance_not_satisfied" in result["observed_rejection_labels"]


# 15
def test_continuity_boundary_downgrades_stale_continuity():
    result = run_category("continuity_boundary")
    assert result["selected_label"] == "strong_fit"
    assert "required_provenance_not_satisfied" in result["observed_rejection_labels"]


# 16
def test_candidate_rejection_rejects_unsafe_unsupported_overclaiming():
    result = run_category("candidate_rejection")
    labels = set(result["observed_rejection_labels"])
    assert {"unsafe_candidate", "required_evidence_not_satisfied", "overclaim_or_capability_overreach"}.issubset(labels)


# 17
def test_non_cannedness_demotion_rejects_canned_candidate():
    result = run_category("non_cannedness_demotion")
    assert "canned_template_like_candidate" in result["observed_rejection_labels"]
    assert result["selected_candidate_id"] == "state_grounded"


# 18
def test_unauthorized_external_help_rejects_model_search_advisor_required_candidates():
    result = run_category("unauthorized_model_search_advisor_requirement")
    labels = set(result["observed_rejection_labels"])
    assert {
        "unauthorized_model_call_required",
        "unauthorized_search_call_required",
        "unauthorized_advisor_call_required",
    }.issubset(labels)


# 19
def test_provenance_requirement_requires_provenance_behavior():
    result = run_category("provenance_requirement")
    assert "required_provenance_not_satisfied" in result["observed_rejection_labels"]


# 20
def test_legal_moral_capability_rejects_boundary_violation():
    result = run_category("legal_moral_capability_boundary")
    labels = set(result["observed_rejection_labels"])
    assert "overclaim_or_capability_overreach" in labels
    assert "legal_or_moral_boundary_violation" in labels


# 21
def test_uncertainty_honesty_prefers_uncertainty_preserving_candidate():
    result = run_category("uncertainty_honesty")
    assert result["selected_candidate_id"] == "uncertainty_preserving"
    assert "overclaim_or_capability_overreach" in result["observed_rejection_labels"]


# 22
def test_actionability_proportionality_selects_bounded_useful_candidate():
    result = run_category("actionability_proportionality")
    assert result["selected_candidate_id"] == "bounded_useful"


# 23
def test_human_understanding_selects_context_fit_candidate():
    item = by_category("human_understanding_fit")
    assert item["state_frame_input"]["relationship_context"]["stress_level"] == "high"
    result = run_category("human_understanding_fit")
    assert result["selected_candidate_id"] == "human_fit"


# 24
def test_governance_escalation_marks_governance_needed():
    result = run_category("governance_escalation")
    assert result["selected_candidate_id"] is None
    assert result["selected_label"] == "reject"
    assert "governance_required" in result["observed_rejection_labels"]


# 25
def test_final_answer_contract_builds_metadata_but_no_final_answer():
    result = run_category("final_answer_contract_metadata")
    contract = result["final_answer_contract_metadata"]
    assert contract["artifact_type"] == "final_answer_contract_metadata_v1"
    assert contract["final_answer_generated"] is False
    assert contract["final_answer_text_present"] is False


# 26
def test_raw_content_safety_rejects_forbidden_fields():
    bad = dict(by_category("raw_content_safety"), raw_prompt="synthetic forbidden placeholder")
    validation = scenarios.validate_ranked_response_shadow_scenario_v1(bad)
    assert validation["valid"] is False
    assert "forbidden_key:raw_prompt" in validation["reason_labels"]


# 27
def test_official_claim_boundary_rejects_official_claim_markers():
    bad = dict(by_category("official_claim_boundary"), claim="passed Turing with official IQ score")
    validation = scenarios.validate_ranked_response_shadow_scenario_v1(bad)
    assert validation["valid"] is False
    assert "official_claim_marker_present" in validation["reason_labels"]


# 28
def test_occ_openclaw_separation_rejects_occ_as_weslr_marker():
    bad = dict(by_category("occ_openclaw_separation"), claim="OCC is WESLR")
    validation = scenarios.validate_ranked_response_shadow_scenario_v1(bad)
    assert validation["valid"] is False
    assert "occ_as_weslr_marker_present" in validation["reason_labels"]


# 29
def test_voice_downstream_confirms_no_voice_tts_behavior():
    result = run_category("voice_downstream_boundary")
    assert result["final_answer_generated"] is False
    assert "overclaim_or_capability_overreach" in result["observed_rejection_labels"]
    assert "voice_tts" in by_category("voice_downstream_boundary")["forbidden_side_effects"]


# 30
def test_native_helper_overlap_is_metadata_only_relationship():
    item = by_category("native_helper_overlap")
    assert item["state_frame_input"]["task_type"] == "ranked_selection_review"
    result = run_category("native_helper_overlap")
    assert result["selected_candidate_id"] == "ranked_state_candidate"


# 31
def test_summary_helper_returns_count_status_only():
    result = scenarios.run_ranked_response_shadow_scenario_corpus_v1()
    summary = scenarios.summarize_ranked_response_shadow_scenario_corpus_v1(result)
    assert set(summary) == {
        "artifact_type",
        "scenario_count",
        "category_count",
        "passed_count",
        "failed_count",
        "validation_status",
        "readiness_labels",
        "raw_content_included",
        "runtime_wired",
        "final_answer_generated",
        "raw_prompt_retained",
        "raw_response_retained",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "persistence_performed",
    }
    assert summary["raw_content_included"] is False


# 32
def test_markdown_renderer_omits_raw_final_private_content():
    result = scenarios.run_ranked_response_shadow_scenario_corpus_v1()
    markdown = scenarios.render_ranked_response_shadow_scenario_corpus_markdown_v1(result).lower()
    assert "synthetic forbidden placeholder" not in markdown
    assert "private user content" not in markdown
    assert "final answer text" not in markdown
    assert "hidden prompt" not in markdown
    assert "answer key" not in markdown


# 33
def test_deterministic_output_for_same_corpus():
    first = scenarios.run_ranked_response_shadow_scenario_corpus_v1(corpus())
    second = scenarios.run_ranked_response_shadow_scenario_corpus_v1(corpus())
    assert first == second


# 34
def test_module_contains_no_file_write_calls():
    source = inspect.getsource(scenarios)
    assert "open(" not in source
    assert ".write(" not in source
    assert "Path(" not in source


# 35
def test_module_contains_no_network_or_subprocess_imports_or_calls():
    source = inspect.getsource(scenarios)
    forbidden = ["import subprocess", "from subprocess", "import socket", "import requests", "urllib", "http.client"]
    assert not any(item in source for item in forbidden)


# 36
def test_module_contains_no_chat_or_generation_calls():
    source = inspect.getsource(scenarios)
    assert "chat_responder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


# 37
def test_readiness_labels_are_present():
    result = scenarios.run_ranked_response_shadow_scenario_corpus_v1()
    assert set(scenarios.READINESS_LABELS_V1).issubset(set(result["readiness_labels"]))
    for item in corpus():
        assert set(scenarios.READINESS_LABELS_V1).issubset(set(item["readiness_labels"]))


# 38
def test_validator_rejects_true_side_effect_flags():
    bad = dict(by_category("context_variation"), model_call_made=True, persistence_performed=True)
    validation = scenarios.validate_ranked_response_shadow_scenario_v1(bad)
    assert "model_call_made_true" in validation["reason_labels"]
    assert "persistence_performed_true" in validation["reason_labels"]


# 39
def test_corpus_validation_rejects_missing_category():
    partial = [item for item in corpus() if item["category"] != "context_variation"]
    validation = scenarios.validate_ranked_response_shadow_scenario_corpus_v1(partial)
    assert validation["valid"] is False
    assert "missing_category:context_variation" in validation["reason_labels"]


# 40
def test_corpus_validation_rejects_duplicate_ids():
    items = corpus()
    duplicate = dict(items[0], category="context_variation")
    items.append(duplicate)
    validation = scenarios.validate_ranked_response_shadow_scenario_corpus_v1(items)
    assert validation["valid"] is False
    assert "scenario_ids_not_unique" in validation["reason_labels"]
