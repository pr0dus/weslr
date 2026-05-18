from __future__ import annotations

import inspect
from pathlib import Path

from weslr import ranked_response_shadow_evaluation_report_run as run


def built_run():
    return run.build_ranked_response_shadow_evaluation_report_run_v1()


# 1
def test_in_memory_run_builds_successfully():
    result = built_run()
    assert result["schema_version"] == run.SCHEMA_VERSION_V1
    assert result["helper_name"] == run.HELPER_NAME_V1
    assert result["run_type"] == run.RUN_TYPE_V1


# 2
def test_scenario_count_is_20():
    assert built_run()["scenario_count"] == 20


# 3
def test_category_count_is_20():
    assert built_run()["category_count"] == 20


# 4
def test_passed_count_is_20():
    assert built_run()["passed_count"] == 20


# 5
def test_failed_count_is_0():
    assert built_run()["failed_count"] == 0


# 6
def test_blocked_count_is_0():
    assert built_run()["blocked_count"] == 0


# 7
def test_report_validation_is_valid():
    result = built_run()
    assert result["report_validation"]["valid"] is True


# 8
def test_run_validation_is_valid():
    result = built_run()
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is True
    assert validation["safe_to_write_artifact"] is True


# 9
def test_status_is_clean_with_minor_followup():
    result = built_run()
    assert result["run_status_label"] == "report_run_clean_with_minor_followup"
    assert run.derive_ranked_response_shadow_evaluation_report_run_status_v1(result) == "report_run_clean_with_minor_followup"


# 10
def test_minor_followups_include_renderer_next_lane_wording_drift():
    labels = {item["label"] for item in built_run()["minor_followups"]}
    assert "renderer_next_lane_wording_drift" in labels


# 11
def test_minor_followups_include_phrase_key_validator_limitation():
    labels = {item["label"] for item in built_run()["minor_followups"]}
    assert "validator_phrase_key_limitation" in labels


# 12
def test_readiness_labels_are_present():
    labels = set(built_run()["readiness_labels"])
    required = {
        "ranked_response_shadow_report_run_implemented",
        "metadata_only_report_run",
        "internal_shadow_evaluation_only",
        "runtime_integration_not_authorized",
        "raw_prompt_response_not_retained",
        "final_answer_not_generated",
        "official_evaluation_not_claimed",
        "minor_followup_carried_forward",
        "voice_downstream_not_current_priority",
    }
    assert required.issubset(labels)


# 13
def test_safety_flags_are_false_for_in_memory_build():
    result = built_run()
    for key in [
        "runtime_wired",
        "final_answer_generated",
        "raw_prompt_retained",
        "raw_response_retained",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "persistence_performed",
        "official_evaluation_claimed",
    ]:
        assert result[key] is False


# 14
def test_markdown_includes_internal_shadow_evaluation_caveat():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run())
    assert "internal shadow evaluation only" in text.lower()


# 15
def test_markdown_includes_runtime_integration_not_authorized():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run())
    assert "runtime_integration_not_authorized" in text
    assert "Runtime integration is not authorized" in text


# 16
def test_markdown_includes_no_official_claim_caveat():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run())
    assert "not an official benchmark" in text
    assert "official_evaluation_not_claimed" in text


# 17
def test_markdown_includes_minor_followup_caveats():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run())
    assert "renderer_next_lane_wording_drift" in text
    assert "validator_phrase_key_limitation" in text


# 18
def test_markdown_does_not_include_raw_prompt_key_or_secret_text():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run()).lower()
    assert "secret_prompt" not in text
    assert "raw_prompt:" not in text


# 19
def test_markdown_does_not_include_raw_response_key_or_secret_text():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run()).lower()
    assert "secret_response" not in text
    assert "raw_response:" not in text


# 20
def test_markdown_does_not_include_final_answer_text_key():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run()).lower()
    assert "final_answer_text" not in text


# 21
def test_markdown_does_not_include_hidden_prompt_or_answer_key():
    text = run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(built_run()).lower()
    assert "hidden_prompt" not in text
    assert "answer_key" not in text


# 22
def test_validator_rejects_raw_prompt_key():
    result = built_run()
    result["metadata"] = {"raw_prompt": "blocked"}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "forbidden_key:raw_prompt" in validation["reason_labels"]


# 23
def test_validator_rejects_final_answer_text():
    result = built_run()
    result["metadata"] = {"final_answer_text": "blocked"}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "forbidden_key:final_answer_text" in validation["reason_labels"]


# 24
def test_validator_rejects_model_search_advisor_call_markers_true():
    result = built_run()
    result["model_call_made"] = True
    result["search_call_made"] = True
    result["advisor_call_made"] = True
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    labels = set(validation["reason_labels"])
    assert {"model_call_made_true", "search_call_made_true", "advisor_call_made_true"}.issubset(labels)


# 25
def test_validator_rejects_runtime_wired_true():
    result = built_run()
    result["runtime_wired"] = True
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "runtime_wired_true" in validation["reason_labels"]


# 26
def test_validator_rejects_official_claim_markers():
    result = built_run()
    result["metadata"] = {"claim": "official benchmark"}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "official_claim_marker_present" in validation["reason_labels"]


# 27
def test_validator_rejects_consciousness_and_occ_as_weslr_markers():
    result = built_run()
    result["metadata"] = {"claim": "WESLR is sentient; OCC is WESLR"}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    labels = set(validation["reason_labels"])
    assert "consciousness_or_sentience_marker_present" in labels
    assert "occ_as_weslr_marker_present" in labels


# 28
def test_write_helper_writes_only_exact_authorized_docs_path():
    path = Path(run.AUTHORIZED_ARTIFACT_PATH_V1)
    before = path.read_text(encoding="utf-8") if path.exists() else None
    metadata = run.write_ranked_response_shadow_evaluation_report_run_artifact_v1()
    assert metadata["artifact_written"] is True
    assert metadata["artifact_path"] == run.AUTHORIZED_ARTIFACT_PATH_V1
    assert path.exists()
    assert path.read_text(encoding="utf-8")
    if before is not None:
        assert path.read_text(encoding="utf-8") == before


# 29
def test_write_helper_rejects_alternate_paths():
    metadata = run.write_ranked_response_shadow_evaluation_report_run_artifact_v1("docs/not_allowed.md")
    assert metadata["artifact_written"] is False
    assert metadata["safe_to_write_artifact"] is False
    assert "unauthorized_artifact_path" in metadata["reason_labels"]
    assert not Path("docs/not_allowed.md").exists()


# 30
def test_artifact_file_content_is_metadata_only_and_safe():
    run.write_ranked_response_shadow_evaluation_report_run_artifact_v1()
    text = Path(run.AUTHORIZED_ARTIFACT_PATH_V1).read_text(encoding="utf-8").lower()
    assert "internal_shadow_evaluation_only" in text
    assert "runtime_integration_not_authorized" in text
    assert "official_evaluation_not_claimed" in text
    assert "secret_prompt" not in text
    assert "secret_response" not in text
    assert "final_answer_text" not in text
    assert "hidden_prompt" not in text
    assert "answer_key" not in text


# 31
def test_no_dot_weslr_write_in_source():
    source = inspect.getsource(run)
    assert ".weslr" not in source.replace("write .weslr state", "")


# 32
def test_no_chatresponder_respond_chat_generate_chat_calls_in_source():
    source = inspect.getsource(run)
    assert "ChatResponder(" not in source
    assert "respond_chat(" not in source
    assert "generate_chat(" not in source


# 33
def test_no_model_search_advisor_calls_in_source():
    source = inspect.getsource(run)
    forbidden = ["model_call(", "search_call(", "advisor_call("]
    for token in forbidden:
        assert token not in source


# 34
def test_no_network_subprocess_calls_in_source():
    source = inspect.getsource(run)
    forbidden = ["import subprocess", "from subprocess", "import socket", "import requests", "urllib", "http.client"]
    for token in forbidden:
        assert token not in source


# 35
def test_no_feature_flag_enablement_in_source():
    source = inspect.getsource(run)
    assert "os.environ" not in source
    assert "feature_flag_enabled = True" not in source
    assert "feature_flags_enabled = True" not in source


# 36
def test_deterministic_output_for_same_run():
    first = built_run()
    second = built_run()
    assert first == second
    assert run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(first) == run.render_ranked_response_shadow_evaluation_report_run_markdown_v1(second)


# 37
def test_report_contains_existing_report_helper_aggregate_labels():
    result = built_run()
    assert "aggregate_labels" in result["report"]
    assert "runtime_integration_not_authorized" in result["report"]["aggregate_labels"]


# 38
def test_validation_rejects_scenario_validation_failure():
    result = built_run()
    result["scenario_validation"] = {"valid": False, "reason_labels": ["forced"]}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "scenario_validation_failed" in validation["reason_labels"]


# 39
def test_validation_rejects_report_validation_failure():
    result = built_run()
    result["report_validation"] = {"valid": False, "reason_labels": ["forced"]}
    validation = run.validate_ranked_response_shadow_evaluation_report_run_v1(result)
    assert validation["valid"] is False
    assert "report_validation_failed" in validation["reason_labels"]
