from __future__ import annotations

import inspect

from weslr import ranked_response_shadow_evaluation_report as report
from weslr import ranked_response_shadow_evaluation_scenarios as scenarios


def corpus_result():
    return scenarios.run_ranked_response_shadow_scenario_corpus_v1()


def built_report():
    return report.build_ranked_response_shadow_evaluation_report_v1(corpus_result())


# 1
def test_report_builder_creates_required_metadata_fields():
    item = built_report()
    for key in [
        "schema_version",
        "helper_name",
        "report_type",
        "scenario_count",
        "category_count",
        "passed_count",
        "failed_count",
        "blocked_count",
        "category_rows",
        "selected_label_distribution",
        "rejection_label_distribution",
        "evidence_provenance_summary",
        "governance_summary",
        "final_answer_contract_summary",
        "safety_boundary_summary",
        "aggregate_labels",
        "readiness_labels",
        "validation",
    ]:
        assert key in item
    assert item["runtime_wired"] is False
    assert item["final_answer_generated"] is False
    assert item["raw_prompt_retained"] is False
    assert item["raw_response_retained"] is False
    assert item["model_call_made"] is False
    assert item["search_call_made"] is False
    assert item["advisor_call_made"] is False
    assert item["persistence_performed"] is False
    assert item["official_evaluation_claimed"] is False


# 2
def test_report_builder_consumes_corpus_result_metadata_only():
    item = built_report()
    text = repr(item).lower()
    assert "scenario_count" in item
    assert "candidate_prose" not in text
    assert "model_output" not in text
    assert "full_conversation" not in text


# 3
def test_category_rows_cover_all_20_scenarios():
    rows = report.build_ranked_response_shadow_category_rows_v1(corpus_result())
    assert len(rows) == 20
    assert {row["category"] for row in rows} == set(scenarios.REQUIRED_CATEGORIES_V1)


# 4
def test_category_rows_include_required_fields():
    required = {
        "category",
        "scenario_id",
        "scenario_name",
        "status",
        "selected_label",
        "rejected_count",
        "key_rejection_labels",
        "evidence_provenance_behavior",
        "governance_needed",
        "final_answer_generated",
        "notes",
    }
    for row in report.build_ranked_response_shadow_category_rows_v1(corpus_result()):
        assert required.issubset(row)


# 5
def test_selected_label_distribution_is_count_only():
    counts = report.summarize_selected_labels_v1(corpus_result())
    assert counts == {"reject": 1, "strong_fit": 19}
    assert all(isinstance(value, int) for value in counts.values())


# 6
def test_rejection_label_distribution_is_count_only():
    counts = report.summarize_rejection_labels_v1(corpus_result())
    assert "canned_template_like_candidate" in counts
    assert "required_evidence_not_satisfied" in counts
    assert all(isinstance(value, int) for value in counts.values())


# 7
def test_evidence_provenance_summary_includes_exercised_boundary_labels():
    summary = report.summarize_evidence_provenance_behavior_v1(corpus_result())
    assert "evidence_boundary_exercised" in summary["labels"]
    assert "provenance_boundary_exercised" in summary["labels"]
    assert summary["evidence_required_count"] >= 1
    assert summary["provenance_required_count"] >= 1


# 8
def test_governance_summary_includes_needs_governance_review_when_expected():
    summary = report.summarize_governance_behavior_v1(corpus_result())
    assert summary["governance_aggregate_label"] == "needs_governance_review"
    assert summary["governance_needed_count"] == 1


# 9
def test_expected_governance_escalation_is_not_failure():
    summary = report.summarize_governance_behavior_v1(corpus_result())
    assert summary["governance_expected_count"] == 1
    assert summary["governance_unexpected_count"] == 0
    assert summary["expected_governance_is_failure"] is False
    assert summary["governance_status"] == "expected_boundary_exercised"


# 10
def test_final_answer_contract_summary_confirms_no_final_answer_generated():
    summary = report.summarize_final_answer_contract_behavior_v1(corpus_result())
    assert summary["contract_metadata_present_count"] == 20
    assert summary["final_answer_generated_count"] == 0
    assert summary["final_answer_text_present_count"] == 0
    assert summary["final_answer_generated"] is False
    assert summary["final_answer_text_absent"] is True


# 11
def test_aggregate_labels_include_runtime_integration_not_authorized():
    assert "runtime_integration_not_authorized" in built_report()["aggregate_labels"]


# 12
def test_clean_corpus_derives_clean_or_minor_gap_label():
    labels = set(built_report()["aggregate_labels"])
    assert labels & {"shadow_report_clean", "shadow_report_clean_with_minor_gaps"}


# 13
def test_report_validator_accepts_safe_report():
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(built_report())
    assert validation == {"valid": True, "safe_to_render": True, "reason_labels": []}


# 14
def test_validator_rejects_raw_prompt_keys():
    item = built_report()
    item["notes"] = {"raw_prompt": "synthetic blocked"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert validation["valid"] is False
    assert "forbidden_key:raw_prompt" in validation["reason_labels"]


# 15
def test_validator_rejects_raw_response_keys():
    item = built_report()
    item["notes"] = {"raw_response": "synthetic blocked"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "forbidden_key:raw_response" in validation["reason_labels"]


# 16
def test_validator_rejects_final_answer_text():
    item = built_report()
    item["notes"] = {"final_answer_text": "synthetic blocked"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "forbidden_key:final_answer_text" in validation["reason_labels"]


# 17
def test_validator_rejects_hidden_prompt():
    item = built_report()
    item["notes"] = {"hidden_prompt": "synthetic blocked"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "forbidden_key:hidden_prompt" in validation["reason_labels"]


# 18
def test_validator_rejects_answer_key():
    item = built_report()
    item["notes"] = {"answer_key": "synthetic blocked"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "forbidden_key:answer_key" in validation["reason_labels"]


# 19
def test_validator_rejects_private_content_markers():
    item = built_report()
    item["notes"] = {"label": "private user content"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "private_content_marker_present" in validation["reason_labels"]


# 20
def test_validator_rejects_official_claim_markers():
    item = built_report()
    item["notes"] = {"claim": "passed Turing with official IQ score"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "official_claim_marker_present" in validation["reason_labels"]


# 21
def test_validator_rejects_consciousness_sentience_markers():
    item = built_report()
    item["notes"] = {"claim": "WESLR is conscious"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "consciousness_or_sentience_marker_present" in validation["reason_labels"]


# 22
def test_validator_rejects_occ_as_weslr_markers():
    item = built_report()
    item["notes"] = {"claim": "OCC is WESLR"}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "occ_as_weslr_marker_present" in validation["reason_labels"]


# 23
def test_validator_rejects_runtime_wired_true():
    item = built_report()
    item["runtime_wired"] = True
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "runtime_wired_true" in validation["reason_labels"]


# 24
def test_validator_rejects_model_search_advisor_call_made_true():
    item = built_report()
    item["model_call_made"] = True
    item["search_call_made"] = True
    item["advisor_call_made"] = True
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    labels = set(validation["reason_labels"])
    assert {"model_call_made_true", "search_call_made_true", "advisor_call_made_true"}.issubset(labels)


# 25
def test_validator_rejects_persistence_true():
    item = built_report()
    item["persistence_performed"] = True
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "persistence_performed_true" in validation["reason_labels"]


# 26
def test_validator_rejects_feature_flag_enabled_true():
    item = built_report()
    item["feature_flag_enabled"] = True
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "feature_flag_enabled_true" in validation["reason_labels"]


# 27
def test_validator_rejects_numeric_official_scoring():
    item = built_report()
    item["notes"] = {"numeric_score": 99}
    validation = report.validate_ranked_response_shadow_evaluation_report_v1(item)
    assert "numeric_official_scoring_present" in validation["reason_labels"]


# 28
def test_markdown_renderer_includes_category_table():
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(built_report())
    assert "## Category result table" in markdown
    assert "| category | scenario_id | status | selected_label |" in markdown


# 29
def test_markdown_renderer_includes_governance_summary():
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(built_report())
    assert "## Governance-needed summary" in markdown
    assert "needs_governance_review" in markdown


# 30
def test_markdown_renderer_includes_external_help_side_effect_distinction():
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(built_report())
    assert "candidate-level model/search/advisor requirements are negative-test metadata only" in markdown
    assert "actual model/search/advisor side-effect flags must remain `False`" in markdown


# 31
def test_markdown_renderer_omits_raw_content_values():
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(built_report()).lower()
    for forbidden_value in ["secret_prompt_leak", "secret_response_leak", "secret_final_leak", "secret_private_leak"]:
        assert forbidden_value not in markdown


# 32
def test_markdown_renderer_blocks_unsafe_report_without_leaking_offending_content():
    item = built_report()
    item["notes"] = {"raw_prompt": "SECRET_PROMPT_LEAK"}
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(item)
    assert "BLOCKED VALIDATION SUMMARY" in markdown
    assert "SECRET_PROMPT_LEAK" not in markdown
    assert "forbidden_key:raw_prompt" in markdown


# 33
def test_json_safe_helper_rejects_invalid_report_explicitly():
    item = built_report()
    item["notes"] = {"raw_response": "SECRET_RESPONSE_LEAK"}
    copied = report.to_ranked_response_shadow_evaluation_report_json_safe_v1(item)
    assert copied["valid"] is False
    assert copied["safe_to_render"] is False
    assert "forbidden_key:raw_response" in copied["reason_labels"]
    assert "SECRET_RESPONSE_LEAK" not in repr(copied)


# 34
def test_report_output_is_deterministic():
    first = built_report()
    second = built_report()
    assert first == second
    assert report.render_ranked_response_shadow_evaluation_report_markdown_v1(first) == report.render_ranked_response_shadow_evaluation_report_markdown_v1(second)


# 35
def test_helper_contains_no_file_write_calls():
    source = inspect.getsource(report)
    assert "open(" not in source
    assert ".write(" not in source
    assert "Path(" not in source


# 36
def test_helper_contains_no_network_subprocess_model_search_advisor_calls():
    source = inspect.getsource(report)
    forbidden = ["import subprocess", "from subprocess", "import socket", "import requests", "urllib", "http.client", "model_call(", "search_call(", "advisor_call("]
    assert not any(item in source for item in forbidden)


# 37
def test_helper_contains_no_chatresponder_respond_chat_generate_chat_calls():
    source = inspect.getsource(report)
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


# 38
def test_readiness_labels_are_present():
    item = built_report()
    for label in report.READINESS_LABELS_V1:
        assert label in item["readiness_labels"]


# 39
def test_report_remains_non_official_and_non_runtime():
    item = built_report()
    assert item["official_evaluation_claimed"] is False
    assert item["runtime_wired"] is False
    assert "runtime_integration_not_authorized" in item["aggregate_labels"]


# 40
def test_native_helper_overlap_is_only_metadata_boundary_if_present():
    item = built_report()
    rows = [row for row in item["category_rows"] if row["category"] == "native_helper_overlap"]
    assert len(rows) == 1
    assert rows[0]["notes"] == "native_helper_overlap_metadata_only"
    assert item["native_helper_overlap_policy"] == "metadata_only_not_final_answer_authority"


# 41
def test_report_records_external_help_negative_metadata_without_side_effects():
    item = built_report()
    row = next(row for row in item["category_rows"] if row["category"] == "unauthorized_model_search_advisor_requirement")
    assert row["notes"] == "external_help_negative_metadata_only"
    assert item["external_help_distinction"]["candidate_level_requirements_are_negative_metadata"] is True
    assert item["external_help_distinction"]["model_call_made"] is False
    assert item["external_help_distinction"]["search_call_made"] is False
    assert item["external_help_distinction"]["advisor_call_made"] is False


# 42
def test_blocked_report_does_not_render_category_rows():
    item = built_report()
    item["runtime_wired"] = True
    markdown = report.render_ranked_response_shadow_evaluation_report_markdown_v1(item)
    assert "BLOCKED VALIDATION SUMMARY" in markdown
    assert "## Category result table" not in markdown
