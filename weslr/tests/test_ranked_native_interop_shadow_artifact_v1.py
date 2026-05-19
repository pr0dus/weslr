from pathlib import Path

from weslr.ranked_native_interop_shadow_artifact import (
    build_ranked_native_interop_shadow_artifact_v1,
    render_ranked_native_interop_shadow_artifact_markdown_v1,
    summarize_ranked_native_interop_shadow_artifact_v1,
    to_ranked_native_interop_shadow_artifact_json_safe_v1,
    validate_ranked_native_interop_shadow_artifact_v1,
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


def assert_invalid(artifact, expected_fragment):
    result = validate_ranked_native_interop_shadow_artifact_v1(artifact)
    assert result["valid"] is False
    assert result["safe_to_render"] is False
    assert any(expected_fragment in reason for reason in result["reason_labels"])


def test_01_builder_returns_required_top_level_fields():
    artifact = safe_artifact()
    for field in [
        "schema_version",
        "helper_name",
        "artifact_type",
        "ranked_state_frame_summary",
        "selected_candidate_metadata",
        "rejected_candidate_labels",
        "ranking_label_summary",
        "final_answer_contract_metadata",
        "native_reasoning_frame_metadata",
        "native_draft_shape_metadata",
        "native_self_check_metadata",
        "native_assembly_metadata",
        "provenance_constraints",
        "evidence_constraints",
        "safety_boundary_labels",
        "interop_notes",
        "readiness_labels",
    ]:
        assert field in artifact


def test_02_builder_sets_all_required_false_safety_flags():
    artifact = safe_artifact()
    for flag in [
        "final_answer_generated",
        "runtime_wired",
        "raw_prompt_response_retained",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "dot_weslr_write_performed",
        "persistence_performed",
        "feature_flag_enabled",
        "official_evaluation_claimed",
    ]:
        assert artifact[flag] is False


def test_03_builder_includes_required_readiness_labels():
    labels = safe_artifact()["readiness_labels"]
    for label in [
        "ranked_native_interop_shadow_artifact_helpers_implemented",
        "metadata_only_artifact",
        "helper_only_not_runtime_wired",
        "runtime_integration_not_authorized",
        "final_answer_authority_not_granted",
        "raw_prompt_response_not_retained",
        "official_evaluation_not_claimed",
        "minor_followup_carried_forward",
        "voice_downstream_not_current_priority",
    ]:
        assert label in labels


def test_04_builder_preserves_minor_followups():
    assert safe_artifact()["minor_followups"] == [
        "renderer_next_lane_wording_drift",
        "validator_phrase_key_limitation",
    ]


def test_05_builder_accepts_ranked_metadata():
    artifact = safe_artifact(ranked_state_frame_summary={"state": "ranked_metadata"})
    assert artifact["ranked_state_frame_summary"] == {"state": "ranked_metadata"}


def test_06_builder_accepts_native_dry_slice_metadata():
    artifact = safe_artifact(native_reasoning_frame_metadata={"frame": "native_metadata"})
    assert artifact["native_reasoning_frame_metadata"] == {"frame": "native_metadata"}


def test_07_selected_candidate_metadata_is_metadata_not_live_response_text():
    artifact = safe_artifact(selected_candidate_metadata={"candidate_id": "c1", "metadata_only": True})
    assert "response_text" not in artifact["selected_candidate_metadata"]
    assert validate_ranked_native_interop_shadow_artifact_v1(artifact)["valid"] is True


def test_08_native_draft_preview_metadata_is_not_final_answer_prose():
    artifact = safe_artifact(native_draft_shape_metadata={"draft_shape": "bullets_without_prose"})
    assert "final_answer_text" not in artifact["native_draft_shape_metadata"]
    assert validate_ranked_native_interop_shadow_artifact_v1(artifact)["valid"] is True


def test_09_validator_accepts_safe_artifact():
    assert validate_ranked_native_interop_shadow_artifact_v1(safe_artifact()) == {
        "valid": True,
        "safe_to_render": True,
        "reason_labels": [],
    }


def test_10_validator_rejects_raw_prompt_key():
    artifact = safe_artifact()
    artifact["raw_prompt"] = "do not leak"
    assert_invalid(artifact, "forbidden_key")


def test_11_validator_rejects_raw_response_key():
    artifact = safe_artifact()
    artifact["raw_response"] = "do not leak"
    assert_invalid(artifact, "forbidden_key")


def test_12_validator_rejects_final_answer_text_key():
    artifact = safe_artifact()
    artifact["final_answer_text"] = "do not render"
    assert_invalid(artifact, "forbidden_key")


def test_13_validator_rejects_hidden_prompt():
    artifact = safe_artifact()
    artifact["hidden_prompt"] = "secret"
    assert_invalid(artifact, "forbidden_key")


def test_14_validator_rejects_answer_key():
    artifact = safe_artifact()
    artifact["answer_key"] = "secret"
    assert_invalid(artifact, "forbidden_key")


def test_15_validator_rejects_private_content_marker():
    artifact = safe_artifact()
    artifact["private_content"] = True
    assert_invalid(artifact, "forbidden_key")


def test_16_validator_rejects_provider_model_output_marker():
    artifact = safe_artifact()
    artifact["provider_output"] = "provider text"
    assert_invalid(artifact, "forbidden_key")
    artifact = safe_artifact()
    artifact["model_output"] = "model text"
    assert_invalid(artifact, "forbidden_key")


def test_17_validator_rejects_runtime_wired_true():
    assert_invalid(safe_artifact(runtime_wired=True), "runtime_wired")


def test_18_validator_rejects_final_answer_generated_true():
    assert_invalid(safe_artifact(final_answer_generated=True), "final_answer_generated")


def test_19_validator_rejects_model_search_advisor_call_markers_true():
    for flag in ["model_call_made", "search_call_made", "advisor_call_made"]:
        assert_invalid(safe_artifact(**{flag: True}), flag)


def test_20_validator_rejects_dot_weslr_write_marker_true():
    assert_invalid(safe_artifact(dot_weslr_write_performed=True), "dot_weslr_write_performed")


def test_21_validator_rejects_persistence_true():
    assert_invalid(safe_artifact(persistence_performed=True), "persistence_performed")


def test_22_validator_rejects_feature_flag_true():
    assert_invalid(safe_artifact(feature_flag_enabled=True), "feature_flag_enabled")


def test_23_validator_rejects_official_claim_markers():
    artifact = safe_artifact()
    artifact["interop_notes"].append("official benchmark claim")
    assert_invalid(artifact, "forbidden_claim_marker")


def test_24_validator_rejects_consciousness_sentience_markers():
    artifact = safe_artifact()
    artifact["conscious"] = True
    assert_invalid(artifact, "forbidden_key")
    artifact = safe_artifact()
    artifact["sentient"] = True
    assert_invalid(artifact, "forbidden_key")


def test_25_validator_rejects_occ_openclaw_as_weslr_markers():
    artifact = safe_artifact()
    artifact["occ_as_weslr"] = True
    assert_invalid(artifact, "forbidden_key")
    artifact = safe_artifact()
    artifact["openclaw_as_weslr"] = True
    assert_invalid(artifact, "forbidden_key")


def test_26_validator_rejects_numeric_official_scores():
    artifact = safe_artifact()
    artifact["official_score"] = 100
    assert_invalid(artifact, "forbidden_key")
    artifact = safe_artifact()
    artifact["metrics"] = {"iq_score": 180}
    assert_invalid(artifact, "forbidden_key")


def test_27_summary_returns_count_status_label_only():
    summary = summarize_ranked_native_interop_shadow_artifact_v1(safe_artifact())
    assert set(summary) == {
        "artifact_type",
        "valid",
        "safe_to_render",
        "ranked_metadata_present",
        "native_metadata_present",
        "rejected_label_count",
        "safety_boundary_label_count",
        "readiness_labels",
        "minor_followups",
        "safety_flags",
    }


def test_28_markdown_renderer_includes_artifact_status():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "Artifact Status" in markdown
    assert "ranked_native_interop_shadow_artifact_v1" in markdown


def test_29_markdown_renderer_includes_safety_confirmation():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "Safety Confirmation" in markdown
    assert "no runtime wiring" in markdown


def test_30_markdown_renderer_includes_minor_followups():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "renderer_next_lane_wording_drift" in markdown
    assert "validator_phrase_key_limitation" in markdown


def test_31_markdown_renderer_omits_raw_final_private_provider_content():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "SECRET_RAW_PROMPT" not in markdown
    assert "SECRET_RAW_RESPONSE" not in markdown
    assert "SECRET_PRIVATE_CONTENT" not in markdown
    assert "SECRET_PROVIDER_OUTPUT" not in markdown


def test_32_markdown_renderer_blocks_unsafe_artifact_without_leaking_content():
    artifact = safe_artifact(raw_prompt="SECRET_RAW_PROMPT")
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(artifact)
    assert "BLOCKED" in markdown
    assert "SECRET_RAW_PROMPT" not in markdown
    assert "forbidden_key" in markdown


def test_33_json_safe_helper_returns_safe_copy_for_valid_artifact():
    artifact = safe_artifact()
    copied = to_ranked_native_interop_shadow_artifact_json_safe_v1(artifact)
    assert copied == artifact
    assert copied is not artifact


def test_34_json_safe_helper_returns_invalid_wrapper_for_unsafe_artifact():
    wrapper = to_ranked_native_interop_shadow_artifact_json_safe_v1(safe_artifact(raw_response="SECRET"))
    assert wrapper["valid"] is False
    assert wrapper["safe_to_render"] is False
    assert "SECRET" not in str(wrapper)


def test_35_helpers_are_deterministic_for_same_input():
    first = safe_artifact()
    second = safe_artifact()
    assert first == second
    assert summarize_ranked_native_interop_shadow_artifact_v1(first) == summarize_ranked_native_interop_shadow_artifact_v1(second)
    assert render_ranked_native_interop_shadow_artifact_markdown_v1(first) == render_ranked_native_interop_shadow_artifact_markdown_v1(second)


def test_36_no_helper_writes_files(tmp_path, monkeypatch):
    before = set(tmp_path.iterdir())
    artifact = safe_artifact()
    validate_ranked_native_interop_shadow_artifact_v1(artifact)
    summarize_ranked_native_interop_shadow_artifact_v1(artifact)
    render_ranked_native_interop_shadow_artifact_markdown_v1(artifact)
    to_ranked_native_interop_shadow_artifact_json_safe_v1(artifact)
    after = set(tmp_path.iterdir())
    assert after == before


def test_37_no_network_subprocess_model_search_advisor_calls_static():
    source = Path("weslr/ranked_native_interop_shadow_artifact.py").read_text()
    for forbidden in ["requests", "urllib", "socket", "model_provider", "search_provider"]:
        assert forbidden not in source
    assert "subprocess_call_made" in source
    assert "advisor_call_made" in source


def test_38_no_chatresponder_respond_chat_generate_chat_calls_static():
    source = Path("weslr/ranked_native_interop_shadow_artifact.py").read_text()
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


def test_39_no_dot_weslr_write_path_references_except_marker_validation_names():
    source = Path("weslr/ranked_native_interop_shadow_artifact.py").read_text()
    assert "dot_weslr_write_performed" in source
    assert "open(" not in source
    assert "write_text" not in source


def test_40_no_official_claims_are_made():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    for phrase in ["official benchmark", "Turing-test pass", "IQ claim", "certification", "product-readiness"]:
        assert phrase.lower() not in markdown.lower()


def test_41_no_runtime_ready_declaration_is_rendered():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "runtime ready" not in markdown.lower()
    assert "runtime-ready" not in markdown.lower()


def test_42_module_importable_without_side_effects():
    import weslr.ranked_native_interop_shadow_artifact as module

    assert module.__all__


def test_43_validator_rejects_network_and_subprocess_true_flags():
    assert_invalid(safe_artifact(network_call_made=True), "network_call_made")
    assert_invalid(safe_artifact(subprocess_call_made=True), "subprocess_call_made")


def test_44_renderer_next_lane_is_review_not_runtime_wiring():
    markdown = render_ranked_native_interop_shadow_artifact_markdown_v1(safe_artifact())
    assert "REVIEW_RANKED_NATIVE_INTEROP_SHADOW_ARTIFACT_HELPERS_IMPLEMENTATION_V1" in markdown
    assert "wire runtime" not in markdown.lower()
