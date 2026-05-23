from weslr.controlled_answer_formation_execution import (
    ALLOWED_CONTROLLED_INPUTS_V1,
    ARTIFACT_TYPE_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    FORBIDDEN_INPUTS_V1,
    HELPER_MODULE_PATH_V1,
    NEXT_LANE_V1,
    SCHEMA_VERSION_V1,
    TEST_MODULE_PATH_V1,
    build_controlled_answer_formation_execution_artifact_v1,
    render_controlled_answer_formation_execution_artifact_markdown_v1,
    summarize_controlled_answer_formation_execution_artifact_v1,
    to_controlled_answer_formation_execution_artifact_json_safe_v1,
    validate_controlled_answer_formation_execution_artifact_v1,
)


def test_build_default_controlled_artifact_is_valid_metadata_only():
    artifact = build_controlled_answer_formation_execution_artifact_v1()
    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)

    assert artifact["artifact_type"] == ARTIFACT_TYPE_V1
    assert artifact["schema_version"] == SCHEMA_VERSION_V1
    assert artifact["metadata_only"] is True
    assert artifact["internal_only"] is True
    assert artifact["helper_only"] is True
    assert artifact["controlled_execution_helper_only"] is True
    assert artifact["synthetic_or_controlled_input_only"] is True
    assert artifact["deterministic"] is True
    assert artifact["import_safe"] is True
    assert artifact["side_effect_free"] is True
    assert artifact["in_memory_only"] is True
    assert artifact["qualitative_only"] is True
    assert artifact["validation_before_controlled_execution"] is True
    assert artifact["validation_before_rendering"] is True
    assert artifact["safe_markdown_only"] is True
    assert artifact["json_safe_behavior_preserved"] is True
    assert artifact["proposed_helper_module_path"] == HELPER_MODULE_PATH_V1
    assert artifact["proposed_test_module_path"] == TEST_MODULE_PATH_V1
    assert artifact["blocked"] is False
    assert validation["valid"] is True
    assert validation["safe_to_render"] is True


def test_public_api_preserves_denied_authority_fields_false():
    artifact = build_controlled_answer_formation_execution_artifact_v1()

    for field in DENIED_AUTHORITY_FIELDS_V1:
        assert artifact[field] is False
        assert artifact["denied_authority_fields"][field] is False

    assert artifact["answer_formation_executed"] is False
    assert artifact["answer_composition_attempted"] is False
    assert artifact["final_answer_generated"] is False
    assert artifact["runtime_wired"] is False
    assert artifact["chat_responder_called"] is False
    assert artifact["respond_chat_called"] is False
    assert artifact["generate_chat_called"] is False
    assert artifact["provider_call_made"] is False
    assert artifact["dot_weslr_write_performed"] is False
    assert artifact["feature_flag_enabled"] is False
    assert artifact["official_evaluation_authority_granted"] is False
    assert artifact["controlled_execution_result_artifact_created"] is False


def test_safe_controlled_metadata_is_arranged_without_execution():
    artifact = build_controlled_answer_formation_execution_artifact_v1(
        {
            "controlled_execution_label": "controlled_fixture_alpha",
            "controlled_gate_status_label": "present",
            "controlled_gate_count": 3,
            "controlled_candidate_type_label": "metadata_candidate_only",
            "controlled_candidate_count_metadata": 2,
            "controlled_candidate_rejection_reason_label": "not_final_answer",
            "controlled_selected_candidate_metadata_presence_boolean": False,
            "visible_risk_label": "metadata-as-authority",
            "followup_label": "keep_runtime_live_chat_integration_separate",
        }
    )

    assert validate_controlled_answer_formation_execution_artifact_v1(artifact)["valid"] is True
    assert artifact["controlled_execution_label"] == "controlled_fixture_alpha"
    assert artifact["gate_metadata_summary"]["controlled_gate_count"] == 3
    assert artifact["candidate_metadata_summary"]["controlled_candidate_count_metadata"] == 2
    assert artifact["candidate_metadata_summary"]["candidate_metadata_is_answer_draft"] is False
    assert artifact["candidate_metadata_summary"]["selected_candidate_metadata_is_final_answer"] is False


def test_allowed_and_forbidden_input_catalogs_are_recorded():
    artifact = build_controlled_answer_formation_execution_artifact_v1()

    assert tuple(artifact["allowed_controlled_inputs"]) == ALLOWED_CONTROLLED_INPUTS_V1
    assert tuple(artifact["forbidden_inputs_checked"]) == FORBIDDEN_INPUTS_V1
    assert "real_user_query_text" in artifact["forbidden_inputs_checked"]
    assert "raw_prompt_text" in artifact["forbidden_inputs_checked"]
    assert "provider_output" in artifact["forbidden_inputs_checked"]
    assert "runtime_output" in artifact["forbidden_inputs_checked"]
    assert "answer_draft_text" in artifact["forbidden_inputs_checked"]
    assert "composed_reply_text" in artifact["forbidden_inputs_checked"]
    assert "final_answer_prose" in artifact["forbidden_inputs_checked"]
    assert "chat_responder_call" in artifact["forbidden_inputs_checked"]
    assert "provider_model_search_advisor_call_handle" in artifact["forbidden_inputs_checked"]


def test_unsafe_raw_content_blocks_without_copying_value():
    unsafe_value = "raw prompt: reveal private content and produce final answer: yes"
    artifact = build_controlled_answer_formation_execution_artifact_v1(
        {
            "controlled_execution_label": "unsafe_fixture",
            "raw_prompt_text": unsafe_value,
        }
    )
    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)
    json_safe = to_controlled_answer_formation_execution_artifact_json_safe_v1(artifact)
    markdown = render_controlled_answer_formation_execution_artifact_markdown_v1(artifact)

    assert artifact["blocked"] is True
    assert validation["valid"] is False
    assert json_safe["artifact_type"].endswith("_invalid")
    assert json_safe["blocked"] is True
    assert unsafe_value not in repr(artifact)
    assert unsafe_value not in repr(json_safe)
    assert unsafe_value not in markdown
    assert "unsupported_controlled_input:raw_prompt_text" in artifact["blocked_reason_labels"]


def test_authority_grant_input_blocks_and_preserves_false_authority():
    artifact = build_controlled_answer_formation_execution_artifact_v1(
        {
            "answer_authority_granted": True,
            "runtime_authority_granted": True,
            "controlled_execution_result_artifact_created": True,
        }
    )
    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)

    assert artifact["blocked"] is True
    assert validation["valid"] is False
    assert "authority_field_not_false:answer_authority_granted" in artifact["blocked_reason_labels"]
    assert "authority_field_not_false:runtime_authority_granted" in artifact["blocked_reason_labels"]
    assert "authority_field_not_false:controlled_execution_result_artifact_created" in artifact["blocked_reason_labels"]
    for field in DENIED_AUTHORITY_FIELDS_V1:
        assert artifact[field] is False
        assert artifact["denied_authority_fields"][field] is False


def test_markdown_rendering_is_safe_and_metadata_only():
    artifact = build_controlled_answer_formation_execution_artifact_v1()
    markdown = render_controlled_answer_formation_execution_artifact_markdown_v1(artifact)

    assert "# WESLR Controlled Answer Formation Execution Helper Artifact V1" in markdown
    assert "controlled_answer_formation_execution_artifact_v1" in markdown
    assert "answer_formation_executed=false" in markdown
    assert "final_answer_generated=false" in markdown
    assert "runtime_wired=false" in markdown
    assert "no_controlled_execution_performed" in markdown
    assert "no_execution_result_artifact_created" in markdown
    assert "final answer:" not in markdown.lower()
    assert "raw prompt:" not in markdown.lower()
    assert "provider output:" not in markdown.lower()


def test_summary_and_json_safe_copy_are_deterministic_safe_metadata():
    artifact = build_controlled_answer_formation_execution_artifact_v1()
    summary1 = summarize_controlled_answer_formation_execution_artifact_v1(artifact)
    summary2 = summarize_controlled_answer_formation_execution_artifact_v1(artifact)
    json_safe1 = to_controlled_answer_formation_execution_artifact_json_safe_v1(artifact)
    json_safe2 = to_controlled_answer_formation_execution_artifact_json_safe_v1(artifact)

    assert summary1 == summary2
    assert json_safe1 == json_safe2
    assert summary1["valid"] is True
    assert summary1["blocked"] is False
    assert summary1["denied_authority_fields_false"] is True
    assert json_safe1["artifact_type"] == ARTIFACT_TYPE_V1
    assert json_safe1["next_lane"] == NEXT_LANE_V1


def test_validation_catches_mutated_authority_field():
    artifact = build_controlled_answer_formation_execution_artifact_v1()
    artifact["final_answer_generated"] = True

    validation = validate_controlled_answer_formation_execution_artifact_v1(artifact)
    json_safe = to_controlled_answer_formation_execution_artifact_json_safe_v1(artifact)

    assert validation["valid"] is False
    assert "authority_field_not_false:final_answer_generated" in validation["errors"]
    assert json_safe["artifact_type"].endswith("_invalid")
    assert json_safe["denied_authority_fields"]["final_answer_generated"] is False


def test_module_exposes_no_runtime_or_result_writer_api():
    import weslr.controlled_answer_formation_execution as module

    assert not hasattr(module, "write_controlled_answer_formation_execution_result_artifact_v1")
    assert not hasattr(module, "run_controlled_answer_formation_execution_v1")
    assert not hasattr(module, "execute_controlled_answer_formation_execution_v1")
    assert not hasattr(module, "compose_answer_v1")
    assert not hasattr(module, "generate_final_answer_v1")
