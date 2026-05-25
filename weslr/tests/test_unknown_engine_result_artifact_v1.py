import importlib
import pathlib
import sys

from weslr.cognitive_gym_run_protocol import REQUIRED_DENIED_AUTHORITY_FIELDS
from weslr.unknown_engine import UNKNOWN_ENGINE_NAME_V1, build_unknown_engine_run_v1


MODULE_NAME = "weslr.unknown_engine_result_artifact"
ALLOWED_FIELDS = {
    "artifact_name",
    "artifact_schema_version",
    "source_engine_name",
    "source_helper_module",
    "source_protocol_name",
    "source_validation_status",
    "source_blocked",
    "source_blocked_reason_labels",
    "knowns_summary",
    "unknowns_summary",
    "uncertainty_summary",
    "possible_branch_label_summary",
    "missing_evidence_summary",
    "falsification_summary",
    "safe_next_observation_summary",
    "evidence_change_summary",
    "risk_boundary_summary",
    "compressed_lesson_summary",
    "denied_authority_summary",
    "visible_risks",
    "followups",
    "next_lane",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
}


def _module():
    return importlib.import_module(MODULE_NAME)


def _valid_source():
    return build_unknown_engine_run_v1(
        {
            "input_state": "internal uncertainty metadata only",
            "observations": ["observation label"],
            "knowns": ["known label"],
            "unknowns": ["unknown label"],
            "possible_future_branches": ["branch label only"],
            "branch_assumptions": ["assumption label"],
            "branch_likelihood_labels": ["qualitative likelihood only"],
            "uncertainty": "uncertainty label only",
            "missing_evidence": ["missing evidence label"],
            "falsification_tests": ["falsification label"],
            "safe_next_observations": ["safe next observation label"],
            "evidence_change_labels": ["evidence change label"],
            "risk_boundaries": ["risk boundary label"],
            "compressed_lesson": "compressed lesson label",
        }
    )


def _artifact(source=None):
    return _module().build_unknown_engine_result_artifact_v1(source or _valid_source())


def test_import_safety_and_public_api():
    before = set(sys.modules)
    module = importlib.import_module(MODULE_NAME)
    after = set(sys.modules)
    assert module.__all__ == (
        "build_unknown_engine_result_artifact_v1",
        "validate_unknown_engine_result_artifact_v1",
        "summarize_unknown_engine_result_artifact_v1",
        "render_unknown_engine_result_artifact_markdown_v1",
        "to_unknown_engine_result_artifact_json_safe_v1",
    )
    assert "weslr.chat_responder" not in after - before


def test_no_side_effect_files_created_by_build(tmp_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    forbidden = [
        root / "docs" / "WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md",
        root / "weslr" / "unknown_engine_result_artifact_output.json",
    ]
    before = {path: path.exists() for path in forbidden}
    _artifact()
    after = {path: path.exists() for path in forbidden}
    assert after == before


def test_valid_artifact_metadata_from_valid_unknown_engine_run():
    source = _valid_source()
    artifact = _artifact(source)
    validation = _module().validate_unknown_engine_result_artifact_v1(artifact)
    assert validation["valid"] is True
    assert artifact["blocked"] is False
    assert artifact["source_engine_name"] == UNKNOWN_ENGINE_NAME_V1
    assert artifact["source_validation_status"] == source["validation_status"]
    assert artifact["source_blocked"] is False


def test_blocked_artifact_metadata_from_blocked_source():
    blocked_source = build_unknown_engine_run_v1({"knowns": ["raw prompt: blocked"]})
    assert blocked_source["blocked"] is True
    artifact = _artifact(blocked_source)
    assert artifact["blocked"] is True
    assert artifact["source_blocked"] is True
    assert "raw_prompt_indicator_blocked" in artifact["source_blocked_reason_labels"]
    assert "raw_prompt_indicator_blocked" in artifact["blocked_reason_labels"]


def test_artifact_shape_contains_only_allowed_fields():
    artifact = _artifact()
    assert set(artifact) == ALLOWED_FIELDS


def test_summary_fields_are_preserved():
    artifact = _artifact()
    assert artifact["knowns_summary"] == ["known label"]
    assert "unknown label" in artifact["unknowns_summary"]
    assert artifact["uncertainty_summary"]
    assert artifact["possible_branch_label_summary"] == ["branch label only"]
    assert artifact["missing_evidence_summary"] == ["missing evidence label"]
    assert artifact["falsification_summary"] == ["falsification label"]
    assert artifact["safe_next_observation_summary"] == ["safe next observation label"]
    assert artifact["evidence_change_summary"] == ["evidence change label"]
    assert artifact["risk_boundary_summary"] == ["risk boundary label"]
    assert artifact["compressed_lesson_summary"] == "compressed lesson label"


def test_denied_authority_summary_fields_remain_false():
    artifact = _artifact()
    assert set(REQUIRED_DENIED_AUTHORITY_FIELDS) <= set(artifact["denied_authority_summary"])
    assert all(artifact["denied_authority_summary"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_missing_denied_authority_fields_block():
    source = _valid_source()
    del source["denied_authority_fields"]["runtime_wired"]
    artifact = _artifact(source)
    assert artifact["blocked"] is True
    assert any("missing_denied_authority_field:runtime_wired" == reason for reason in artifact["blocked_reason_labels"])


def test_true_denied_authority_fields_block():
    source = _valid_source()
    source["denied_authority_fields"]["provider_call_made"] = True
    artifact = _artifact(source)
    assert artifact["blocked"] is True
    assert "denied_authority_field_not_false:provider_call_made" in artifact["blocked_reason_labels"]


def test_raw_prompt_and_response_indicators_block():
    for text, expected in [
        ("raw prompt: unsafe", "raw_prompt_indicator_blocked"),
        ("raw response: unsafe", "raw_response_indicator_blocked"),
    ]:
        source = _valid_source()
        source["knowns"] = [text]
        artifact = _artifact(source)
        assert artifact["blocked"] is True
        assert expected in artifact["blocked_reason_labels"]


def test_private_content_indicators_block():
    source = _valid_source()
    source["knowns"] = ["private content: unsafe"]
    artifact = _artifact(source)
    assert artifact["blocked"] is True
    assert "private_content_indicator_blocked" in artifact["blocked_reason_labels"]


def test_runtime_reply_preview_final_answer_and_draft_indicators_block():
    cases = [
        ("runtime output: unsafe", "runtime_output_indicator_blocked"),
        ("reply output: unsafe", "reply_output_indicator_blocked"),
        ("preview output: unsafe", "preview_output_indicator_blocked"),
        ("final-answer prose", "final_answer_prose_indicator_blocked"),
        ("answer draft: unsafe", "answer_draft_indicator_blocked"),
    ]
    for text, expected in cases:
        source = _valid_source()
        source["unknowns"] = [text]
        artifact = _artifact(source)
        assert artifact["blocked"] is True
        assert expected in artifact["blocked_reason_labels"]


def test_prediction_future_certainty_and_open_problem_indicators_block():
    cases = [
        ("prediction output: unsafe", "prediction_output_indicator_blocked"),
        ("future certainty", "future_certainty_claim_blocked"),
        ("open-problem solution", "open_problem_solution_claim_blocked"),
    ]
    for text, expected in cases:
        source = _valid_source()
        source["hypotheses"] = [text]
        artifact = _artifact(source)
        assert artifact["blocked"] is True
        assert expected in artifact["blocked_reason_labels"]


def test_provider_model_search_advisor_indicators_block():
    for text in ["provider output: unsafe", "model output: unsafe", "search output: unsafe", "advisor output: unsafe"]:
        source = _valid_source()
        source["knowns"] = [text]
        artifact = _artifact(source)
        assert artifact["blocked"] is True
        assert "provider_model_search_advisor_indicator_blocked" in artifact["blocked_reason_labels"]


def test_chatresponder_dot_weslr_feature_judges_official_indicators_block():
    cases = [
        ("ChatResponder", "chat_responder_indicator_blocked"),
        (".weslr read", "dot_weslr_io_indicator_blocked"),
        ("feature_flag_enabled=true", "feature_flag_indicator_blocked"),
        ("judge decision:", "judges_scores_indicator_blocked"),
        ("official benchmark", "official_claim_indicator_blocked"),
    ]
    for text, expected in cases:
        source = _valid_source()
        source["knowns"] = [text]
        artifact = _artifact(source)
        assert artifact["blocked"] is True
        assert expected in artifact["blocked_reason_labels"]


def test_safe_markdown_internal_only_and_not_output():
    markdown = _module().render_unknown_engine_result_artifact_markdown_v1(_artifact())
    lowered = markdown.lower()
    assert "internal_review_material_only" in markdown
    assert "metadata_only_no_runtime_no_output_no_authority" in markdown
    assert "not_reply_output" in markdown
    assert "not_preview_output" in markdown
    assert "not_final_answer_prose" in markdown
    assert "not_user_facing_output" in markdown
    assert "not_sendable_reply_text" in markdown
    assert "not_actual_reply_body" in markdown
    assert "not_official_claim" in markdown
    assert "not_open_problem_solution_claim" in markdown
    assert "not_prediction_output" in markdown
    assert "no_authority_grant" in markdown
    assert "send this to user" not in lowered


def test_blocked_markdown_preserves_block_labels_without_raw_content():
    artifact = _artifact(build_unknown_engine_run_v1({"knowns": ["raw prompt: unsafe secret"]}))
    markdown = _module().render_unknown_engine_result_artifact_markdown_v1(artifact)
    assert "raw_prompt_indicator_blocked" in markdown
    assert "raw prompt: unsafe secret" not in markdown
    assert "unsafe_content_not_rendered" in markdown


def test_json_safe_conversion_works_and_preserves_shape():
    artifact = _artifact()
    safe = _module().to_unknown_engine_result_artifact_json_safe_v1(artifact)
    assert set(safe) == ALLOWED_FIELDS
    assert safe["blocked"] is False
    assert safe["blocked_reason_labels"] == []
    assert safe["source_validation_status"] == artifact["source_validation_status"]
    assert all(safe["denied_authority_summary"][field] is False for field in REQUIRED_DENIED_AUTHORITY_FIELDS)


def test_summary_is_metadata_only():
    summary = _module().summarize_unknown_engine_result_artifact_v1(_artifact())
    assert summary["source_engine_name"] == UNKNOWN_ENGINE_NAME_V1
    assert summary["blocked"] is False
    assert summary["denied_authority_fields_false"] is True


def test_no_runtime_provider_search_advisor_model_or_chatresponder_imports_or_calls():
    module_path = pathlib.Path(__file__).resolve().parents[1] / "unknown_engine_result_artifact.py"
    text = module_path.read_text()
    forbidden = [
        "from weslr.chat_responder",
        "import weslr.chat_responder",
        "respond_chat(",
        "generate_chat(",
        "provider_call(",
        "model_call(",
        "search_call(",
        "advisor_call(",
        "open('.weslr",
        'open(".weslr',
    ]
    assert not any(fragment in text for fragment in forbidden)


def test_no_actual_result_artifact_file_created():
    root = pathlib.Path(__file__).resolve().parents[2]
    forbidden = root / "docs" / "WESLR_UNKNOWN_ENGINE_RESULT_ARTIFACT_V1.md"
    before = forbidden.exists()
    _artifact()
    after = forbidden.exists()
    assert after == before
