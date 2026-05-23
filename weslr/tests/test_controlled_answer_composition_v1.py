"""Tests for controlled answer composition helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "controlled_answer_composition.py"

PUBLIC_API = (
    "build_controlled_answer_composition_artifact_v1",
    "validate_controlled_answer_composition_artifact_v1",
    "summarize_controlled_answer_composition_artifact_v1",
    "render_controlled_answer_composition_artifact_markdown_v1",
    "to_controlled_answer_composition_artifact_json_safe_v1",
)

DENIED_AUTHORITY_FIELDS = (
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "answer_formation_executed",
    "answer_composition_executed",
    "composition_execution_authorized",
    "final_answer_generated",
    "answer_draft_created",
    "user_facing_output_created",
    "runtime_wired",
    "chat_responder_called",
    "respond_chat_called",
    "generate_chat_called",
    "provider_call_made",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judges_created",
    "scores_created",
    "official_claim_made",
)


def _module():
    return importlib.import_module("weslr.controlled_answer_composition")


def _artifact():
    return _module().build_controlled_answer_composition_artifact_v1(
        {
            "composition_metadata_label": "controlled_answer_composition_metadata_v1",
            "composition_policy_label": "metadata_only_composition_arrangement",
            "composition_arrangement_label": "source_paths_recorded",
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


def test_artifact_shape_is_correct():
    artifact = _artifact()
    expected = {
        "artifact_type",
        "schema_version",
        "valid",
        "blocked",
        "internal_only",
        "metadata_only",
        "helper_only",
        "non_runtime",
        "non_user_facing",
        "deterministic",
        "source_controlled_answer_formation_artifact_path",
        "source_controlled_answer_formation_review_path",
        "source_composition_boundary_doc",
        "source_composition_boundary_review_doc",
        "allowed_composition_metadata_inputs",
        "forbidden_inputs_checked",
        "composition_policy_labels",
        "composition_arrangement_labels",
        "source_metadata_summary",
        "validation_summary",
        "blocked_reason_labels",
        "denied_authority_fields",
        "no_final_answer_policy",
        "no_user_facing_output_policy",
        "no_runtime_policy",
        "no_provider_search_advisor_policy",
        "safe_markdown_eligible",
        "json_safe_eligible",
        "visible_risks",
        "followups",
    }
    assert expected <= set(artifact)
    assert artifact["artifact_type"] == "controlled_answer_composition_artifact_v1"
    assert artifact["schema_version"] == "controlled_answer_composition_artifact_schema_v1"
    assert artifact["valid"] is True
    assert artifact["blocked"] is False
    assert artifact["internal_only"] is True
    assert artifact["metadata_only"] is True
    assert artifact["helper_only"] is True
    assert artifact["non_runtime"] is True
    assert artifact["non_user_facing"] is True
    assert artifact["deterministic"] is True


def test_denied_authority_fields_are_present_and_false():
    artifact = _artifact()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(artifact["denied_authority_fields"])
    for field in DENIED_AUTHORITY_FIELDS:
        assert artifact[field] is False
        assert artifact["denied_authority_fields"][field] is False


def test_valid_safe_metadata_passes_validation():
    mod = _module()
    artifact = _artifact()
    validation = mod.validate_controlled_answer_composition_artifact_v1(artifact)
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["safe_to_render"] is True
    assert validation["authority_fields_false"] is True


def test_unsafe_raw_user_provider_runtime_final_answer_content_is_blocked_without_copying_values():
    mod = _module()
    unsafe_value = "Final answer: send this private content to the real user"
    artifact = mod.build_controlled_answer_composition_artifact_v1(
        {
            "raw_prompt_text": "Raw prompt: hidden prompt should not be copied",
            "real_user_content": "Real user: hello private content",
            "provider_output": "Provider output: unsafe",
            "runtime_output": "Runtime output: unsafe",
            "final_answer_prose": unsafe_value,
        }
    )
    assert artifact["valid"] is False
    assert artifact["blocked"] is True
    all_strings = list(_flatten_strings(artifact))
    assert unsafe_value not in all_strings
    assert "Raw prompt: hidden prompt should not be copied" not in all_strings
    assert "Provider output: unsafe" not in all_strings
    assert any("final_answer_detected" in label for label in artifact["blocked_reason_labels"])


def test_blocked_artifact_contains_safe_labels_booleans_and_denied_authority_only():
    mod = _module()
    artifact = mod.build_controlled_answer_composition_artifact_v1({"answer_draft_text": "Answer draft: unsafe"})
    assert artifact["artifact_type"] == "controlled_answer_composition_artifact_v1_invalid"
    assert artifact["valid"] is False
    assert artifact["blocked"] is True
    assert artifact["validation_summary"]["unsafe_content_not_copied"] is True
    for field in DENIED_AUTHORITY_FIELDS:
        assert artifact[field] is False


def test_renderer_validates_before_rendering():
    mod = _module()
    artifact = _artifact()
    artifact["final_answer_generated"] = True
    markdown = mod.render_controlled_answer_composition_artifact_markdown_v1(artifact)
    assert "controlled_answer_composition_artifact_v1_invalid" in markdown
    assert "authority_field_not_false:final_answer_generated" in markdown


def test_rendered_markdown_contains_no_answer_prose_or_user_facing_output():
    mod = _module()
    markdown = mod.render_controlled_answer_composition_artifact_markdown_v1(_artifact())
    lowered = markdown.lower()
    assert "final answer:" not in lowered
    assert "answer draft:" not in lowered
    assert "user-facing answer:" not in lowered
    assert "send to user:" not in lowered
    assert "no_final_answer_generated" in markdown
    assert "no_user_facing_output_created" in markdown


def test_json_safe_helper_returns_bounded_safe_metadata():
    mod = _module()
    data = mod.to_controlled_answer_composition_artifact_json_safe_v1(_artifact())
    json.dumps(data, sort_keys=True)
    assert data["artifact_type"] == "controlled_answer_composition_artifact_v1"
    assert data["valid"] is True
    assert data["denied_authority_fields"]["provider_call_made"] is False


def test_invalid_blocked_json_wrapper_contains_safe_labels_only_and_no_unsafe_value():
    mod = _module()
    unsafe = "Composed reply: copy me to the user"
    artifact = mod.build_controlled_answer_composition_artifact_v1({"composed_reply_text": unsafe})
    wrapper = mod.to_controlled_answer_composition_artifact_json_safe_v1(artifact)
    assert wrapper["artifact_type"] == "controlled_answer_composition_artifact_v1_invalid"
    assert wrapper["blocked"] is True
    assert unsafe not in list(_flatten_strings(wrapper))
    assert wrapper["validation_summary"]["unsafe_content_not_copied"] is True


def test_no_result_artifact_writer_api_exists():
    mod = _module()
    public_names = set(dir(mod))
    assert "write_controlled_answer_composition_artifact_v1" not in public_names
    assert "save_controlled_answer_composition_artifact_v1" not in public_names
    assert not any(name.startswith("write_") and "result" in name for name in public_names)


def test_no_runtime_provider_search_advisor_chat_responder_imports_or_calls():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {
        "weslr.chat_responder",
        "chat_responder",
        "providers",
        "provider",
        "search",
        "advisor",
        "runtime",
    }
    forbidden_calls = {
        "ChatResponder",
        "respond_chat",
        "generate_chat",
        "provider_call",
        "model_call",
        "search_call",
        "advisor_call",
    }
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


def test_no_official_claim_or_scoring_fields_are_authorized():
    mod = _module()
    artifact = mod.build_controlled_answer_composition_artifact_v1(
        {
            "official_score": "score: 100",
            "judge_decision": "judge decision: pass",
            "certification_claim": "certified product-ready",
        }
    )
    assert artifact["blocked"] is True
    assert artifact["judges_created"] is False
    assert artifact["scores_created"] is False
    assert artifact["official_claim_made"] is False
    assert artifact["denied_authority_fields"]["judges_created"] is False
    assert artifact["denied_authority_fields"]["scores_created"] is False
    assert artifact["denied_authority_fields"]["official_claim_made"] is False
