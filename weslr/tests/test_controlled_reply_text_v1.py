"""Tests for controlled reply text metadata helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "controlled_reply_text.py"
CHAT_RESPONDER_PATH = Path(__file__).resolve().parents[1] / "chat_responder.py"
USER_FACING_OUTPUT_HELPER_PATH = Path(__file__).resolve().parents[1] / "controlled_user_facing_output.py"

PUBLIC_API = (
    "build_controlled_reply_text_artifact_v1",
    "validate_controlled_reply_text_artifact_v1",
    "summarize_controlled_reply_text_artifact_v1",
    "render_controlled_reply_text_artifact_markdown_v1",
    "to_controlled_reply_text_artifact_json_safe_v1",
)

DENIED_AUTHORITY_FIELDS = (
    "answer_authority_granted",
    "reply_text_authority_granted",
    "user_facing_output_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "reply_text_executed",
    "sendable_reply_text_created",
    "actual_reply_body_created",
    "user_facing_output_executed",
    "user_facing_reply_created",
    "live_dialogue_output_created",
    "final_answer_generation_executed",
    "final_answer_generated",
    "final_answer_prose_created",
    "answer_draft_created",
    "answer_composition_executed",
    "answer_formation_executed",
    "runtime_wired",
    "chat_responder_called",
    "respond_chat_called",
    "generate_chat_called",
    "provider_call_made",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_read_performed",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judges_created",
    "scores_created",
    "official_claim_made",
)


def _module():
    return importlib.import_module("weslr.controlled_reply_text")


def _artifact():
    return _module().build_controlled_reply_text_artifact_v1(
        {
            "reply_text_metadata_label": "controlled_reply_text_metadata_v1",
            "reply_text_policy_label": "metadata_only_controlled_reply_text_arrangement",
            "output_arrangement_label": "source_paths_recorded",
        }
    )


def _flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _flatten_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten_strings(item)


def test_imports_are_safe_and_public_api_exists():
    mod = _module()
    for name in PUBLIC_API:
        assert callable(getattr(mod, name))


def test_valid_artifact_builds_with_required_safe_metadata():
    artifact = _artifact()
    expected = {
        "artifact_type",
        "schema_version",
        "valid",
        "blocked",
        "validation_status",
        "internal_only",
        "metadata_only",
        "helper_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "source_controlled_user_facing_output_artifact_path",
        "source_controlled_user_facing_output_review_path",
        "source_reply_text_boundary_doc",
        "source_reply_text_boundary_review_doc",
        "allowed_metadata_input_labels",
        "forbidden_input_check_labels",
        "reply_text_policy_labels",
        "output_arrangement_labels",
        "source_metadata_summary",
        "reply_text_metadata_summary",
        "validation_summary",
        "blocked_reason_labels",
        "denied_authority_fields",
        "no_output_policy_labels",
        "safe_markdown_eligible",
        "json_safe_eligible",
        "visible_risks",
        "followups",
        "next_lane",
    }
    assert expected <= set(artifact)
    assert artifact["artifact_type"] == "controlled_reply_text_artifact_v1"
    assert artifact["schema_version"] == "controlled_reply_text_artifact_schema_v1"
    assert artifact["valid"] is True
    assert artifact["blocked"] is False
    assert artifact["validation_status"] == "validation_pass_metadata_quality_only"
    assert artifact["internal_only"] is True
    assert artifact["metadata_only"] is True
    assert artifact["helper_only"] is True
    assert artifact["non_runtime"] is True
    assert artifact["non_user_facing"] is True
    assert artifact["deterministic"] is True
    assert artifact["next_lane"] == "REVIEW_CONTROLLED_REPLY_TEXT_HELPERS_IMPLEMENTATION_V1"


def test_validation_passes_only_for_safe_metadata():
    mod = _module()
    artifact = _artifact()
    validation = mod.validate_controlled_reply_text_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["safe_to_render"] is True
    assert validation["authority_fields_false"] is True

    unsafe = dict(artifact)
    unsafe["sendable_reply_text_created"] = True
    validation = mod.validate_controlled_reply_text_artifact_v1(unsafe)
    assert validation["valid"] is False
    assert "authority_field_not_false:sendable_reply_text_created" in validation["errors"]


def test_all_denied_authority_fields_exist_and_are_false():
    artifact = _artifact()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(artifact["denied_authority_fields"])
    for field in DENIED_AUTHORITY_FIELDS:
        assert artifact[field] is False
        assert artifact["denied_authority_fields"][field] is False


def test_blocked_invalid_input_does_not_copy_unsafe_values():
    mod = _module()
    unsafe_value = "Sendable reply text: send this private content to the real user"
    artifact = mod.build_controlled_reply_text_artifact_v1(
        {
            "raw_prompt_text": "Raw prompt: hidden prompt should not be copied",
            "real_user_content": "Real user: hello private content",
            "provider_output": "Provider output: unsafe",
            "runtime_output": "Runtime output: unsafe",
            "sendable_reply_text": unsafe_value,
        }
    )
    all_strings = list(_flatten_strings(artifact))
    assert artifact["valid"] is False
    assert artifact["blocked"] is True
    assert unsafe_value not in all_strings
    assert "Raw prompt: hidden prompt should not be copied" not in all_strings
    assert "Provider output: unsafe" not in all_strings
    assert any("sendable_reply_text_detected" in label for label in artifact["blocked_reason_labels"])
    assert artifact["validation_summary"]["unsafe_content_not_copied"] is True


def test_raw_prompt_response_user_private_provider_runtime_reply_final_answer_content_is_rejected():
    mod = _module()
    cases = [
        {"raw_response_text": "Raw response: unsafe"},
        {"private_content": "Private content: unsafe"},
        {"model_output": "Model output: unsafe"},
        {"search_output": "Search output: unsafe"},
        {"advisor_output": "Advisor output: unsafe"},
        {"final_answer_prose": "Final answer: unsafe"},
        {"answer_draft_text": "Answer draft: unsafe"},
        {"live_dialogue_output": "Live dialogue: unsafe"},
        {"sendable_message_text": "Sendable message: unsafe"},
    ]
    for case in cases:
        artifact = mod.build_controlled_reply_text_artifact_v1(case)
        assert artifact["blocked"] is True
        for unsafe in case.values():
            assert unsafe not in list(_flatten_strings(artifact))


def test_render_requires_valid_artifact():
    mod = _module()
    artifact = _artifact()
    artifact["reply_text_executed"] = True
    markdown = mod.render_controlled_reply_text_artifact_markdown_v1(artifact)
    assert "controlled_reply_text_artifact_v1_invalid" in markdown
    assert "authority_field_not_false:reply_text_executed" in markdown


def test_rendered_markdown_is_safe_internal_metadata_only():
    mod = _module()
    markdown = mod.render_controlled_reply_text_artifact_markdown_v1(_artifact())
    lowered = markdown.lower()
    assert "final answer:" not in lowered
    assert "answer draft:" not in lowered
    assert "reply-text reply:" not in lowered
    assert "reply to user:" not in lowered
    assert "send to user:" not in lowered
    assert "message to send:" not in lowered
    assert "no_reply_text_executed" in markdown
    assert "no_sendable_reply_text_created" in markdown
    assert "no_live_dialogue_output_created" in markdown


def test_json_safe_conversion_is_deterministic_and_contains_no_unsafe_objects():
    mod = _module()
    data1 = mod.to_controlled_reply_text_artifact_json_safe_v1(_artifact())
    data2 = mod.to_controlled_reply_text_artifact_json_safe_v1(_artifact())
    assert data1 == data2
    json.dumps(data1, sort_keys=True)
    assert data1["artifact_type"] == "controlled_reply_text_artifact_v1"
    assert data1["valid"] is True
    assert data1["denied_authority_fields"]["provider_call_made"] is False


def test_invalid_blocked_json_wrapper_contains_safe_labels_only_and_no_unsafe_value():
    mod = _module()
    unsafe = "Reply to user: copy me"
    artifact = mod.build_controlled_reply_text_artifact_v1({"sendable_reply_text": unsafe})
    wrapper = mod.to_controlled_reply_text_artifact_json_safe_v1(artifact)
    assert wrapper["artifact_type"] == "controlled_reply_text_artifact_v1_invalid"
    assert wrapper["blocked"] is True
    assert unsafe not in list(_flatten_strings(wrapper))
    assert wrapper["validation_summary"]["unsafe_content_not_copied"] is True


def test_no_chat_responder_respond_chat_generate_chat_imports_or_calls():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {"weslr.chat_responder", "chat_responder"}
    forbidden_calls = {"ChatResponder", "respond_chat", "generate_chat"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name not in forbidden_imports for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in forbidden_imports
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def test_no_provider_search_advisor_model_calls_or_runtime_wiring():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_calls = {
        "provider_call",
        "model_call",
        "search_call",
        "advisor_call",
        "wire_runtime",
        "runtime_wire",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
    artifact = _artifact()
    assert artifact["provider_call_made"] is False
    assert artifact["model_call_made"] is False
    assert artifact["search_call_made"] is False
    assert artifact["advisor_call_made"] is False
    assert artifact["runtime_wired"] is False


def test_no_dot_weslr_writes_or_writer_api_exists():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_calls = {"open", "write", "writelines", "write_text", "mkdir", "touch"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
    mod = _module()
    public_names = set(dir(mod))
    assert "write_controlled_reply_text_artifact_v1" not in public_names
    assert "save_controlled_reply_text_artifact_v1" not in public_names
    assert not any(name.startswith("write_") for name in public_names)


def test_no_authority_grants_judges_scores_or_official_claims():
    mod = _module()
    artifact = mod.build_controlled_reply_text_artifact_v1(
        {
            "official_score": "score: 100",
            "judge_decision": "judge decision: pass",
            "certification_claim": "certified product-ready",
            "authority_grant": "authority granted",
        }
    )
    assert artifact["blocked"] is True
    assert artifact["judges_created"] is False
    assert artifact["scores_created"] is False
    assert artifact["official_claim_made"] is False
    assert artifact["answer_authority_granted"] is False
    assert artifact["reply_text_authority_granted"] is False
    assert artifact["runtime_authority_granted"] is False


def test_source_helper_files_remain_separate_and_chat_responder_untouched():
    assert MODULE_PATH.name == "controlled_reply_text.py"
    assert USER_FACING_OUTPUT_HELPER_PATH.exists()
    assert USER_FACING_OUTPUT_HELPER_PATH != MODULE_PATH
    assert CHAT_RESPONDER_PATH.exists()
    assert "controlled_reply_text" not in CHAT_RESPONDER_PATH.read_text()
