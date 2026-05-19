from pathlib import Path

import pytest

from weslr.ranked_native_interop_shadow_artifact_report_run import (
    AUTHORIZED_ARTIFACT_PATH,
    build_ranked_native_interop_shadow_artifact_report_run_v1,
    derive_ranked_native_interop_shadow_artifact_report_run_status_v1,
    render_ranked_native_interop_shadow_artifact_report_run_markdown_v1,
    validate_ranked_native_interop_shadow_artifact_report_run_v1,
    write_ranked_native_interop_shadow_artifact_report_run_artifact_v1,
)


def run_result(**overrides):
    result = build_ranked_native_interop_shadow_artifact_report_run_v1()
    result.update(overrides)
    return result


def assert_invalid(result, expected_fragment):
    validation = validate_ranked_native_interop_shadow_artifact_report_run_v1(result)
    assert validation["valid"] is False
    assert validation["safe_to_write_artifact"] is False
    assert any(expected_fragment in reason for reason in validation["reason_labels"])


REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "helper_name",
    "run_type",
    "artifact_type",
    "artifact_valid",
    "artifact_safe_to_render",
    "report_valid",
    "report_safe_to_render",
    "run_valid",
    "safe_to_write_artifact",
    "artifact_summary",
    "report",
    "markdown",
    "minor_followups",
    "run_status_label",
    "readiness_labels",
]

FALSE_SAFETY_FLAGS = [
    "runtime_wired",
    "final_answer_generated",
    "raw_prompt_response_retained",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "persistence_performed",
    "feature_flag_enabled",
    "official_evaluation_claimed",
]

REQUIRED_READINESS_LABELS = [
    "ranked_native_artifact_report_run_implemented",
    "metadata_only_report_run",
    "internal_shadow_evaluation_only",
    "helper_authority_boundaries_preserved",
    "runtime_integration_not_authorized",
    "final_answer_authority_not_granted",
    "raw_prompt_response_not_retained",
    "official_evaluation_not_claimed",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
]


def test_01_in_memory_run_builds_successfully():
    result = run_result()
    assert result["run_type"] == "ranked_native_interop_shadow_artifact_report_run_v1"
    assert result["run_valid"] is True


def test_02_run_result_has_required_top_level_fields():
    result = run_result()
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in result


def test_03_artifact_validation_is_valid():
    assert run_result()["artifact_valid"] is True


def test_04_artifact_safe_to_render_is_true():
    assert run_result()["artifact_safe_to_render"] is True


def test_05_report_validation_is_valid():
    assert run_result()["report_valid"] is True


def test_06_report_safe_to_render_is_true():
    assert run_result()["report_safe_to_render"] is True


def test_07_run_validation_is_valid():
    validation = validate_ranked_native_interop_shadow_artifact_report_run_v1(run_result())
    assert validation == {"valid": True, "safe_to_write_artifact": True, "reason_labels": []}


def test_08_status_is_clean_with_minor_followup():
    assert run_result()["run_status_label"] == "report_run_clean_with_minor_followup"


def test_09_status_helper_returns_clean_with_minor_followup():
    assert derive_ranked_native_interop_shadow_artifact_report_run_status_v1(run_result()) == "report_run_clean_with_minor_followup"


def test_10_readiness_labels_are_present():
    labels = run_result()["readiness_labels"]
    for label in REQUIRED_READINESS_LABELS:
        assert label in labels


def test_11_minor_followup_includes_renderer_next_lane_wording_drift():
    assert "renderer_next_lane_wording_drift" in run_result()["minor_followups"]


def test_12_minor_followup_includes_validator_phrase_key_limitation():
    assert "validator_phrase_key_limitation" in run_result()["minor_followups"]


@pytest.mark.parametrize("flag", FALSE_SAFETY_FLAGS)
def test_13_safety_flags_are_false(flag):
    assert run_result()[flag] is False


def test_14_synthetic_artifact_includes_ranked_metadata_presence():
    artifact = run_result()["synthetic_artifact_metadata"]
    assert artifact["ranked_state_frame_summary"]["present"] is True


def test_15_synthetic_artifact_includes_native_metadata_presence():
    artifact = run_result()["synthetic_artifact_metadata"]
    assert artifact["native_reasoning_frame_metadata"]["present"] is True


def test_16_selected_candidate_metadata_is_not_live_response_text():
    checks = run_result()["required_synthetic_metadata_checks"]
    artifact = run_result()["synthetic_artifact_metadata"]
    assert checks["selected_candidate_live_response_text"] is False
    assert artifact["selected_candidate_metadata"]["live_response_material"] is False


def test_17_native_draft_metadata_is_not_final_answer_prose():
    artifact = run_result()["synthetic_artifact_metadata"]
    assert artifact["native_draft_shape_metadata"]["draft_is_final_answer"] is False
    assert "final_answer_text" not in artifact["native_draft_shape_metadata"]


def test_18_native_self_check_is_not_answer_approval():
    artifact = run_result()["synthetic_artifact_metadata"]
    assert artifact["native_self_check_metadata"]["answer_approval"] is False


def test_19_native_assembly_is_not_runtime_output():
    artifact = run_result()["synthetic_artifact_metadata"]
    assert artifact["native_assembly_metadata"]["runtime_material"] is False


def test_20_markdown_includes_internal_shadow_evaluation_caveat():
    assert "internal shadow evaluation only" in run_result()["markdown"]


def test_21_markdown_includes_runtime_integration_not_authorized():
    assert "runtime integration not authorized" in run_result()["markdown"]


def test_22_markdown_includes_final_answer_authority_not_granted():
    assert "final-answer authority not granted" in run_result()["markdown"]


def test_23_markdown_includes_no_official_claim_caveat():
    markdown = run_result()["markdown"]
    assert "not official benchmark/Turing/IQ/certification/product-readiness" in markdown


def test_24_markdown_includes_minor_followups():
    markdown = run_result()["markdown"]
    assert "renderer_next_lane_wording_drift" in markdown
    assert "validator_phrase_key_limitation" in markdown


def test_25_markdown_does_not_include_raw_prompt_text():
    assert "raw prompt text" not in run_result()["markdown"].lower()


def test_26_markdown_does_not_include_raw_response_text():
    assert "raw response text" not in run_result()["markdown"].lower()


def test_27_markdown_does_not_include_final_answer_text():
    assert "final answer text" not in run_result()["markdown"].lower()


def test_28_markdown_does_not_include_hidden_prompt():
    assert "hidden prompt" not in run_result()["markdown"].lower()


def test_29_markdown_does_not_include_answer_key():
    assert "answer key" not in run_result()["markdown"].lower()


def test_30_validator_rejects_raw_prompt_key():
    result = run_result(raw_prompt="do not retain")
    assert_invalid(result, "forbidden_key")


def test_31_validator_rejects_raw_response_key():
    result = run_result(raw_response="do not retain")
    assert_invalid(result, "forbidden_key")


def test_32_validator_rejects_final_answer_text():
    result = run_result(final_answer_text="do not render")
    assert_invalid(result, "forbidden_key")


def test_33_validator_rejects_hidden_prompt():
    result = run_result(hidden_prompt="secret")
    assert_invalid(result, "forbidden_key")


def test_34_validator_rejects_answer_key():
    result = run_result(answer_key="secret")
    assert_invalid(result, "forbidden_key")


@pytest.mark.parametrize("flag", ["model_call_made", "search_call_made", "advisor_call_made"])
def test_35_validator_rejects_model_search_advisor_markers_true(flag):
    result = run_result(**{flag: True})
    assert_invalid(result, "forbidden_true_flag")


def test_36_validator_rejects_runtime_wired_true():
    assert_invalid(run_result(runtime_wired=True), "forbidden_true_flag:runtime_wired")


def test_37_validator_rejects_final_answer_generated_true():
    assert_invalid(run_result(final_answer_generated=True), "forbidden_true_flag:final_answer_generated")


def test_38_validator_rejects_dot_weslr_write_marker_true():
    assert_invalid(run_result(dot_weslr_write_performed=True), "forbidden_true_flag:dot_weslr_write_performed")


def test_39_validator_rejects_persistence_true_for_in_memory_run():
    assert_invalid(run_result(persistence_performed=True), "forbidden_true_flag:persistence_performed")


def test_40_validator_rejects_feature_flag_true():
    assert_invalid(run_result(feature_flag_enabled=True), "forbidden_true_flag:feature_flag_enabled")


def test_41_validator_rejects_official_claim_marker_true():
    assert_invalid(run_result(official_evaluation_claimed=True), "forbidden_true_flag:official_evaluation_claimed")


def test_42_validator_rejects_official_claim_value_markers():
    result = run_result(extra_label="official benchmark")
    assert_invalid(result, "forbidden_value_marker:official_benchmark")


def test_43_validator_rejects_occ_openclaw_as_weslr_markers():
    assert_invalid(run_result(occ_as_weslr=True), "forbidden_key")
    assert_invalid(run_result(openclaw_as_weslr=True), "forbidden_key")


def test_44_validator_rejects_network_subprocess_markers_true():
    assert_invalid(run_result(network_call_made=True), "forbidden_true_flag:network_call_made")
    assert_invalid(run_result(subprocess_call_made=True), "forbidden_true_flag:subprocess_call_made")


def test_45_write_helper_writes_only_exact_authorized_docs_path():
    meta = write_ranked_native_interop_shadow_artifact_report_run_artifact_v1()
    assert meta["artifact_written"] is True
    assert meta["artifact_path"] == AUTHORIZED_ARTIFACT_PATH
    assert Path(AUTHORIZED_ARTIFACT_PATH).exists()


def test_46_write_helper_rejects_alternate_paths(tmp_path):
    target = tmp_path / "unauthorized.md"
    meta = write_ranked_native_interop_shadow_artifact_report_run_artifact_v1(str(target))
    assert meta["artifact_written"] is False
    assert meta["reason_labels"] == ["unauthorized_artifact_path"]
    assert not target.exists()


def test_47_artifact_file_content_is_metadata_only_and_safe():
    write_ranked_native_interop_shadow_artifact_report_run_artifact_v1()
    content = Path(AUTHORIZED_ARTIFACT_PATH).read_text(encoding="utf-8")
    assert "metadata-only internal shadow evaluation" in content
    assert "FINAL ANSWER:" not in content
    assert "provider output" not in content.lower()
    assert "hidden prompt" not in content.lower()
    assert "answer key" not in content.lower()


def test_48_no_dot_weslr_write():
    meta = write_ranked_native_interop_shadow_artifact_report_run_artifact_v1()
    assert meta["dot_weslr_write_performed"] is False


def test_49_no_chatresponder_respond_chat_generate_chat_calls():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report_run.py").read_text(encoding="utf-8")
    assert "ChatResponder(" not in source
    assert "respond_chat(" not in source
    assert "generate_chat(" not in source
    assert "weslr.chat_responder" not in source


def test_50_no_model_search_advisor_calls():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report_run.py").read_text(encoding="utf-8")
    assert "model_call(" not in source
    assert "search_call(" not in source
    assert "advisor_call(" not in source
    assert "requests." not in source


def test_51_no_network_subprocess_calls():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report_run.py").read_text(encoding="utf-8")
    assert "import socket" not in source
    assert "import urllib" not in source
    assert "import subprocess" not in source
    assert "os.system" not in source


def test_52_no_feature_flag_enablement():
    assert run_result()["feature_flag_enabled"] is False


def test_53_deterministic_output_for_same_run():
    first = run_result()
    second = run_result()
    assert first == second


def test_54_no_official_claims_are_made():
    result = run_result()
    assert result["official_evaluation_claimed"] is False
    assert "official_evaluation_not_claimed" in result["readiness_labels"]


def test_55_no_runtime_ready_declaration_is_rendered():
    assert "runtime ready" not in run_result()["markdown"].lower()
    assert "runtime-ready" not in run_result()["markdown"].lower()


def test_56_module_imports_without_side_effect_writer_call_in_source():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report_run.py").read_text(encoding="utf-8")
    assert "write_ranked_native_interop_shadow_artifact_report_run_artifact_v1()" not in source.split("def write_ranked_native_interop_shadow_artifact_report_run_artifact_v1", 1)[0]


def test_57_blocked_renderer_omits_offending_content():
    result = run_result(raw_prompt="VERY_SECRET_RAW_PROMPT")
    markdown = render_ranked_native_interop_shadow_artifact_report_run_markdown_v1(result)
    assert "BLOCKED" in markdown
    assert "VERY_SECRET_RAW_PROMPT" not in markdown


def test_58_status_blocks_failed_artifact_validation():
    result = run_result(artifact_valid=False)
    assert derive_ranked_native_interop_shadow_artifact_report_run_status_v1(result) == "report_run_blocked"


def test_59_status_blocks_failed_report_validation():
    result = run_result(report_valid=False)
    assert derive_ranked_native_interop_shadow_artifact_report_run_status_v1(result) == "report_run_blocked"


def test_60_status_blocks_dirty_safety_flag():
    result = run_result(model_call_made=True)
    assert derive_ranked_native_interop_shadow_artifact_report_run_status_v1(result) == "report_run_blocked"
