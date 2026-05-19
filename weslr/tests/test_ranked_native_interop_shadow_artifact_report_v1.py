from pathlib import Path

from weslr.ranked_native_interop_shadow_artifact import build_ranked_native_interop_shadow_artifact_v1
from weslr.ranked_native_interop_shadow_artifact_report import (
    build_ranked_native_artifact_report_tables_v1,
    build_ranked_native_interop_shadow_artifact_report_v1,
    derive_ranked_native_artifact_report_aggregate_labels_v1,
    render_ranked_native_interop_shadow_artifact_report_markdown_v1,
    to_ranked_native_interop_shadow_artifact_report_json_safe_v1,
    validate_ranked_native_interop_shadow_artifact_report_v1,
)


def safe_artifact(**overrides):
    artifact = build_ranked_native_interop_shadow_artifact_v1(
        ranked_state_frame_summary={"state_labels": ["grounded"]},
        selected_candidate_metadata={"candidate_id": "candidate_a", "selection_label": "metadata_only"},
        rejected_candidate_labels=["unsupported_claim"],
        ranking_label_summary={"top_label": "grounded_candidate_metadata"},
        final_answer_contract_metadata={"contract_label": "no_final_answer", "final_answer_generated": False},
        native_reasoning_frame_metadata={"frame_label": "goal_constraints_uncertainty"},
        native_draft_shape_metadata={"shape_label": "outline_metadata_only"},
        native_self_check_metadata={"check_labels": ["no_answer_approval"]},
        native_assembly_metadata={"assembly_label": "not_runtime_output"},
        provenance_constraints=["source_label_required"],
        evidence_constraints=["evidence_boundary_preserved"],
        safety_boundary_labels=["runtime_integration_not_authorized"],
        interop_notes=["metadata_relationship_only"],
        readiness_labels=["custom_safe_label"],
    )
    artifact.update(overrides)
    return artifact


def safe_report(**overrides):
    report = build_ranked_native_interop_shadow_artifact_report_v1(safe_artifact())
    report.update(overrides)
    return report


def assert_invalid_report(report, expected_fragment):
    validation = validate_ranked_native_interop_shadow_artifact_report_v1(report)
    assert validation["valid"] is False
    assert validation["safe_to_render"] is False
    assert any(expected_fragment in reason for reason in validation["reason_labels"])


def test_01_report_builder_creates_required_top_level_fields():
    report = safe_report()
    for field in [
        "schema_version",
        "helper_name",
        "report_type",
        "artifact_type",
        "artifact_valid",
        "safe_to_render",
        "validation",
        "artifact_identity",
        "ranked_metadata_summary",
        "native_metadata_summary",
        "constraint_summary",
        "safety_flag_summary",
        "readiness_labels",
        "minor_followups",
        "aggregate_labels",
        "gaps_risks",
    ]:
        assert field in report


def test_02_report_builder_consumes_metadata_only_artifact():
    report = build_ranked_native_interop_shadow_artifact_report_v1(safe_artifact())
    assert report["artifact_type"] == "ranked_native_interop_shadow_artifact_v1"
    assert report["artifact_valid"] is True


def test_03_report_builder_uses_artifact_validation_result():
    artifact = safe_artifact(raw_prompt="SECRET_RAW_PROMPT")
    report = build_ranked_native_interop_shadow_artifact_report_v1(artifact)
    assert report["artifact_valid"] is False
    assert any("forbidden_key" in reason for reason in report["validation"]["reason_labels"])
    assert "SECRET_RAW_PROMPT" not in str(report)


def test_04_report_builder_includes_ranked_metadata_summary():
    summary = safe_report()["ranked_metadata_summary"]
    assert "ranked_state_frame_summary" in summary
    assert summary["selected_candidate_metadata"]["presence"] == "present"


def test_05_report_builder_includes_native_metadata_summary():
    summary = safe_report()["native_metadata_summary"]
    assert "native_reasoning_frame_metadata" in summary
    assert summary["native_assembly_metadata"]["presence"] == "present"


def test_06_report_builder_includes_constraint_summary():
    summary = safe_report()["constraint_summary"]
    assert summary["provenance_constraints"]["count"] == 1
    assert "runtime_integration_not_authorized" in summary["safety_boundary_labels"]["labels"]


def test_07_report_builder_includes_safety_flag_summary():
    report = safe_report()
    assert report["safety_flag_summary"]["runtime_wired"] is False
    assert report["model_call_made"] is False


def test_08_report_builder_preserves_readiness_labels():
    labels = safe_report()["readiness_labels"]
    for label in [
        "ranked_native_artifact_report_helpers_implemented",
        "metadata_only_report_surface",
        "helper_authority_boundaries_preserved",
        "runtime_integration_not_authorized",
        "final_answer_authority_not_granted",
        "raw_prompt_response_not_retained",
        "official_evaluation_not_claimed",
        "minor_followup_carried_forward",
        "voice_downstream_not_current_priority",
        "custom_safe_label",
    ]:
        assert label in labels


def test_09_report_builder_preserves_minor_followups():
    assert safe_report()["minor_followups"] == [
        "renderer_next_lane_wording_drift",
        "validator_phrase_key_limitation",
    ]


def test_10_aggregate_labels_include_runtime_integration_not_authorized():
    assert "runtime_integration_not_authorized" in safe_report()["aggregate_labels"]


def test_11_aggregate_labels_include_final_answer_authority_not_granted():
    assert "final_answer_authority_not_granted" in safe_report()["aggregate_labels"]


def test_12_valid_artifact_gets_artifact_valid():
    assert "artifact_valid" in safe_report()["aggregate_labels"]


def test_13_invalid_artifact_gets_artifact_invalid_blocked():
    report = build_ranked_native_interop_shadow_artifact_report_v1(safe_artifact(runtime_wired=True))
    assert "artifact_invalid_blocked" in report["aggregate_labels"]


def test_14_table_helper_returns_artifact_field_presence_table():
    tables = build_ranked_native_artifact_report_tables_v1(safe_report())
    assert "artifact_field_presence" in tables
    assert any(row["field"] == "artifact_type" for row in tables["artifact_field_presence"])


def test_15_table_helper_returns_safety_flag_table():
    tables = build_ranked_native_artifact_report_tables_v1(safe_report())
    assert "safety_flags" in tables
    assert any(row["safety_flag"] == "runtime_wired" for row in tables["safety_flags"])


def test_16_table_helper_returns_ranked_native_metadata_table():
    tables = build_ranked_native_artifact_report_tables_v1(safe_report())
    assert "ranked_native_metadata" in tables
    assert any(row["side"] == "ranked" for row in tables["ranked_native_metadata"])
    assert any(row["side"] == "native" for row in tables["ranked_native_metadata"])


def test_17_table_helper_returns_constraint_label_table():
    tables = build_ranked_native_artifact_report_tables_v1(safe_report())
    assert "constraint_labels" in tables
    assert any(row.get("constraint_category") == "safety_boundary_labels" for row in tables["constraint_labels"])


def test_18_table_helper_returns_validator_reason_label_table():
    tables = build_ranked_native_artifact_report_tables_v1(safe_report())
    assert "validator_reason_labels" in tables
    assert tables["validator_reason_labels"][0]["reason_label"] == "none"


def test_19_validator_accepts_safe_report():
    assert validate_ranked_native_interop_shadow_artifact_report_v1(safe_report()) == {
        "valid": True,
        "safe_to_render": True,
        "reason_labels": [],
    }


def test_20_validator_rejects_raw_prompt_text_key():
    report = safe_report(raw_prompt_text="SECRET_RAW_PROMPT")
    assert_invalid_report(report, "forbidden_key")


def test_21_validator_rejects_raw_response_text_key():
    report = safe_report(raw_response_text="SECRET_RAW_RESPONSE")
    assert_invalid_report(report, "forbidden_key")


def test_22_validator_rejects_final_answer_text_key():
    report = safe_report(final_answer_text="SECRET_FINAL")
    assert_invalid_report(report, "forbidden_key")


def test_23_validator_rejects_private_content():
    report = safe_report(private_content="SECRET_PRIVATE")
    assert_invalid_report(report, "forbidden_key")


def test_24_validator_rejects_hidden_prompt():
    report = safe_report(hidden_prompt="SECRET_HIDDEN")
    assert_invalid_report(report, "forbidden_key")


def test_25_validator_rejects_answer_key():
    report = safe_report(answer_key="SECRET_ANSWER_KEY")
    assert_invalid_report(report, "forbidden_key")


def test_26_validator_rejects_provider_model_output():
    assert_invalid_report(safe_report(provider_output="SECRET_PROVIDER"), "forbidden_key")
    assert_invalid_report(safe_report(model_output="SECRET_MODEL"), "forbidden_key")


def test_27_validator_rejects_official_scores():
    assert_invalid_report(safe_report(official_score=100), "forbidden_key")
    assert_invalid_report(safe_report(metrics={"iq_score": 180}), "forbidden_key")


def test_28_validator_rejects_runtime_authority_markers():
    report = safe_report(notes=["runtime output treated as authority"])
    assert_invalid_report(report, "forbidden_value_marker")


def test_29_validator_rejects_runtime_wired_true():
    assert_invalid_report(safe_report(runtime_wired=True), "runtime_wired")


def test_30_validator_rejects_final_answer_generated_true():
    assert_invalid_report(safe_report(final_answer_generated=True), "final_answer_generated")


def test_31_validator_rejects_model_search_advisor_call_markers_true():
    for flag in ["model_call_made", "search_call_made", "advisor_call_made"]:
        assert_invalid_report(safe_report(**{flag: True}), flag)


def test_32_validator_rejects_dot_weslr_write_marker_true():
    assert_invalid_report(safe_report(dot_weslr_write_performed=True), "dot_weslr_write_performed")


def test_33_validator_rejects_persistence_true():
    assert_invalid_report(safe_report(persistence_performed=True), "persistence_performed")


def test_34_validator_rejects_feature_flag_true():
    assert_invalid_report(safe_report(feature_flag_enabled=True), "feature_flag_enabled")


def test_35_validator_rejects_official_evaluation_claim_true():
    assert_invalid_report(safe_report(official_evaluation_claimed=True), "official_evaluation_claimed")


def test_36_validator_rejects_consciousness_sentience_markers():
    assert_invalid_report(safe_report(conscious=True), "forbidden_key")
    assert_invalid_report(safe_report(sentient=True), "forbidden_key")


def test_37_validator_rejects_occ_openclaw_as_weslr_markers():
    assert_invalid_report(safe_report(occ_as_weslr=True), "forbidden_key")
    assert_invalid_report(safe_report(openclaw_as_weslr=True), "forbidden_key")


def test_38_markdown_renderer_includes_report_status():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    assert "Report Status" in markdown
    assert "ranked_native_interop_shadow_artifact_report_v1" in markdown


def test_39_markdown_renderer_includes_safety_confirmation():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    assert "Safety Confirmation" in markdown
    assert "no runtime wiring" in markdown


def test_40_markdown_renderer_includes_minor_followups():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    assert "renderer_next_lane_wording_drift" in markdown
    assert "validator_phrase_key_limitation" in markdown


def test_41_markdown_renderer_includes_metadata_only_tables_or_summaries():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    assert "Metadata-only Table Summaries" in markdown
    assert "safety_flag_rows" in markdown


def test_42_markdown_renderer_blocks_unsafe_report_without_leaking_offending_content():
    report = safe_report(raw_prompt_text="SECRET_RAW_PROMPT")
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(report)
    assert "BLOCKED" in markdown
    assert "SECRET_RAW_PROMPT" not in markdown
    assert "forbidden_key" in markdown


def test_43_markdown_renderer_omits_raw_final_private_provider_content():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    for secret in ["SECRET_RAW", "SECRET_FINAL", "SECRET_PRIVATE", "SECRET_PROVIDER"]:
        assert secret not in markdown


def test_44_json_safe_helper_returns_safe_copy_for_valid_report():
    report = safe_report()
    copied = to_ranked_native_interop_shadow_artifact_report_json_safe_v1(report)
    assert copied == report
    assert copied is not report


def test_45_json_safe_helper_returns_invalid_wrapper_for_unsafe_report():
    wrapper = to_ranked_native_interop_shadow_artifact_report_json_safe_v1(safe_report(raw_response_text="SECRET"))
    assert wrapper["valid"] is False
    assert wrapper["safe_to_render"] is False
    assert "SECRET" not in str(wrapper)


def test_46_helpers_are_deterministic_for_same_input():
    artifact = safe_artifact()
    first = build_ranked_native_interop_shadow_artifact_report_v1(artifact)
    second = build_ranked_native_interop_shadow_artifact_report_v1(artifact)
    assert first == second
    assert build_ranked_native_artifact_report_tables_v1(first) == build_ranked_native_artifact_report_tables_v1(second)
    assert render_ranked_native_interop_shadow_artifact_report_markdown_v1(first) == render_ranked_native_interop_shadow_artifact_report_markdown_v1(second)


def test_47_no_helper_writes_files(tmp_path):
    before = set(tmp_path.iterdir())
    report = safe_report()
    validate_ranked_native_interop_shadow_artifact_report_v1(report)
    build_ranked_native_artifact_report_tables_v1(report)
    render_ranked_native_interop_shadow_artifact_report_markdown_v1(report)
    to_ranked_native_interop_shadow_artifact_report_json_safe_v1(report)
    after = set(tmp_path.iterdir())
    assert after == before


def test_48_no_network_subprocess_model_search_advisor_calls_static():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report.py").read_text()
    for forbidden in ["requests", "urllib", "socket", "import subprocess", "model_provider", "search_provider", "advisor_provider"]:
        assert forbidden not in source


def test_49_no_chat_responder_respond_chat_generate_chat_calls_static():
    source = Path("weslr/ranked_native_interop_shadow_artifact_report.py").read_text()
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


def test_50_no_official_claims_are_made():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    for phrase in ["official benchmark", "Turing-test pass", "IQ claim", "certification", "product-readiness"]:
        assert phrase.lower() not in markdown.lower()


def test_51_no_runtime_ready_declaration_is_rendered():
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(safe_report())
    assert "runtime ready" not in markdown.lower()
    assert "runtime-ready" not in markdown.lower()


def test_52_module_is_importable_without_side_effects():
    import weslr.ranked_native_interop_shadow_artifact_report as module

    assert module.__all__


def test_53_derive_aggregate_labels_is_qualitative_only():
    labels = derive_ranked_native_artifact_report_aggregate_labels_v1(safe_report())
    assert "metadata_only_report_surface" in labels
    assert not any(isinstance(label, (int, float)) for label in labels)


def test_54_invalid_artifact_report_can_be_safely_rendered_as_blocked_artifact_state():
    report = build_ranked_native_interop_shadow_artifact_report_v1(safe_artifact(raw_response="SECRET_RAW_RESPONSE"))
    validation = validate_ranked_native_interop_shadow_artifact_report_v1(report)
    assert validation["valid"] is True
    markdown = render_ranked_native_interop_shadow_artifact_report_markdown_v1(report)
    assert "artifact_invalid_blocked" in markdown
    assert "SECRET_RAW_RESPONSE" not in markdown
