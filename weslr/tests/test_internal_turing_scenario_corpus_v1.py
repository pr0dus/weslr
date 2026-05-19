from __future__ import annotations

from copy import deepcopy
import inspect
import json

import pytest

from weslr import internal_turing_scenario_corpus as corpus_mod


def _corpus():
    return corpus_mod.build_internal_turing_scenario_corpus_v1()


def _safe_record():
    return corpus_mod.build_internal_turing_scenario_record_v1(
        scenario_id="safe_record_v1",
        category="simple_ordinary_request",
        dimension_targets=["human-understanding fit"],
        synthetic_user_turn_summary="Synthetic metadata summary only.",
        context_constraints=["metadata-only"],
        allowed_evidence=["safe metadata"],
        memory_boundary="summary-only",
        expected_response_properties=["bounded helpfulness"],
        failure_modes=["missed_intent"],
        forbidden_claims=["no official claims"],
        safety_boundaries=["no runtime wiring"],
    )


def test_module_imports_without_side_effects():
    assert corpus_mod.SCHEMA_VERSION_V1 == "internal_turing_scenario_corpus_v1"


def test_constants_include_26_categories():
    assert len(corpus_mod.INTERNAL_TURING_SCENARIO_CATEGORIES_V1) == 26


def test_constants_include_19_readiness_dimensions():
    assert len(corpus_mod.INTERNAL_TURING_READINESS_DIMENSIONS_V1) == 19


def test_constants_include_minor_followups():
    assert set(corpus_mod.INTERNAL_TURING_MINOR_FOLLOWUPS_V1) == {
        "renderer_next_lane_wording_drift",
        "validator_phrase_key_limitation",
    }


def test_corpus_builder_returns_26_records():
    assert len(_corpus()) == 26


def test_corpus_contains_all_required_categories():
    categories = {record["category"] for record in _corpus()}
    assert categories == set(corpus_mod.INTERNAL_TURING_SCENARIO_CATEGORIES_V1)


def test_scenario_ids_are_unique():
    ids = [record["scenario_id"] for record in _corpus()]
    assert len(ids) == len(set(ids))


def test_record_builder_creates_required_fields():
    record = _safe_record()
    for field in (
        "scenario_id",
        "category",
        "dimension_targets",
        "synthetic_user_turn_summary",
        "context_constraints",
        "allowed_evidence",
        "memory_boundary",
        "expected_response_properties",
        "failure_modes",
        "governance_expected",
        "forbidden_claims",
        "safety_boundaries",
        "schema_version",
        "metadata_only",
        "internal_only",
    ):
        assert field in record


@pytest.mark.parametrize(
    "field",
    [
        "raw_content_allowed",
        "final_answer_required",
        "runtime_execution_allowed",
        "official_score_allowed",
        "official_evaluation_claimed",
        "prompt_execution_authorized",
        "final_answer_generated",
        "runtime_wired",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "dot_weslr_write_performed",
        "feature_flag_enabled",
    ],
)
def test_record_builder_sets_required_false_booleans(field):
    assert _safe_record()[field] is False


@pytest.mark.parametrize("record", _corpus())
def test_each_corpus_record_has_dimension_targets(record):
    assert record["dimension_targets"]


@pytest.mark.parametrize("record", _corpus())
def test_each_corpus_record_has_expected_response_properties(record):
    assert record["expected_response_properties"]


@pytest.mark.parametrize("record", _corpus())
def test_each_corpus_record_has_failure_modes(record):
    assert record["failure_modes"]


def test_record_validator_accepts_safe_record():
    result = corpus_mod.validate_internal_turing_scenario_record_v1(_safe_record())
    assert result["valid"] is True
    assert result["blocked"] is False


def test_corpus_validator_accepts_full_corpus():
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(_corpus())
    assert result["valid"] is True
    assert result["all_categories_present"] is True


def _invalid_record(**updates):
    record = _safe_record()
    record.update(updates)
    return record


def test_validator_rejects_unknown_category():
    result = corpus_mod.validate_internal_turing_scenario_record_v1(_invalid_record(category="unknown"))
    assert not result["valid"]
    assert "unknown_category" in result["errors"]


def test_validator_rejects_missing_required_field():
    record = _safe_record()
    del record["scenario_id"]
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]
    assert "missing_required_field:scenario_id" in result["errors"]


def test_validator_rejects_duplicate_scenario_ids_in_corpus():
    corpus = _corpus()
    corpus[1]["scenario_id"] = corpus[0]["scenario_id"]
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(corpus)
    assert not result["valid"]
    assert result["duplicate_scenario_ids"]


@pytest.mark.parametrize(
    "field",
    ["raw_content_allowed", "final_answer_required", "runtime_execution_allowed", "official_score_allowed"],
)
def test_validator_rejects_unsafe_booleans_true(field):
    result = corpus_mod.validate_internal_turing_scenario_record_v1(_invalid_record(**{field: True}))
    assert not result["valid"]
    assert result["safety_booleans_valid"] is False


@pytest.mark.parametrize(
    "field, value, expected_flag",
    [
        ("raw_prompt", "raw prompt: do the thing", "raw_content_detected"),
        ("raw_response", "raw response: unsafe", "raw_content_detected"),
        ("final_answer_text", "final answer: unsafe", "final_answer_detected"),
        ("private_content", "private content: unsafe", "raw_content_detected"),
        ("hidden_prompt", "hidden prompt: unsafe", "raw_content_detected"),
        ("answer_key", "answer key: unsafe", "raw_content_detected"),
        ("provider_output", "provider output: unsafe", "raw_content_detected"),
        ("official_score", "official score: 100", "official_claim_detected"),
        ("runtime_output", "runtime output: unsafe", "runtime_authority_detected"),
    ],
)
def test_validator_rejects_unsafe_keys_and_content(field, value, expected_flag):
    record = _safe_record()
    record[field] = value
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]
    assert result[expected_flag] is True


@pytest.mark.parametrize(
    "text",
    [
        "raw prompt: unsafe",
        "raw response: unsafe",
        "final answer: unsafe",
        "private content: unsafe",
        "hidden prompt: unsafe",
        "answer key: unsafe",
        "provider output: unsafe",
        "model output: unsafe",
    ],
)
def test_validator_rejects_unsafe_text_markers(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]


@pytest.mark.parametrize(
    "text",
    [
        "official Turing pass",
        "passed the Turing test",
        "IQ certification",
        "certified product-ready",
        "official benchmark",
    ],
)
def test_validator_rejects_official_turing_iq_certification_product_claims(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]
    assert result["official_claim_detected"] is True


@pytest.mark.parametrize("text", ["WESLR is conscious", "WESLR is sentient", "sentience proven"])
def test_validator_rejects_consciousness_sentience_claims(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]
    assert result["official_claim_detected"] is True


@pytest.mark.parametrize("text", ["OCC is WESLR", "OpenClaw is WESLR", "OCC/OpenClaw as WESLR"])
def test_validator_rejects_occ_openclaw_as_weslr_framing(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]


@pytest.mark.parametrize("text", ["execute prompt", "prompt execution", "run this prompt"])
def test_validator_rejects_prompt_execution_markers(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]


@pytest.mark.parametrize(
    "text",
    ["model_call_made=true", "search_call_made=true", "advisor_call_made=true"],
)
def test_validator_rejects_model_search_advisor_call_markers(text):
    record = _safe_record()
    record["synthetic_user_turn_summary"] = text
    result = corpus_mod.validate_internal_turing_scenario_record_v1(record)
    assert not result["valid"]


def test_validator_rejects_dot_weslr_write_marker():
    result = corpus_mod.validate_internal_turing_scenario_record_v1(
        _invalid_record(synthetic_user_turn_summary="write .weslr")
    )
    assert not result["valid"]


def test_validator_rejects_feature_flag_marker():
    result = corpus_mod.validate_internal_turing_scenario_record_v1(
        _invalid_record(synthetic_user_turn_summary="feature_flag_enabled=true")
    )
    assert not result["valid"]


def test_summary_includes_scenario_and_category_counts():
    summary = corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    assert summary["scenario_count"] == 26
    assert summary["category_count"] == 26


def test_summary_includes_dimension_coverage():
    summary = corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    assert "human-understanding fit" in summary["dimension_coverage"]


def test_summary_includes_failure_mode_coverage():
    summary = corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    assert "missed_intent" in summary["failure_mode_coverage"]


def test_summary_includes_governance_expected_count():
    summary = corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    assert summary["governance_expected_count"] >= 1


def test_summary_includes_minor_followups():
    summary = corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    assert "renderer_next_lane_wording_drift" in summary["minor_followups"]
    assert "validator_phrase_key_limitation" in summary["minor_followups"]


def test_summary_excludes_raw_prompts_final_answers_private_provider_content():
    summary_text = json.dumps(corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus()))
    forbidden = ["raw prompt:", "final answer:", "private content:", "provider output:"]
    assert all(item not in summary_text.lower() for item in forbidden)


def test_renderer_includes_corpus_status():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "Status: metadata_only_corpus_valid" in rendered


def test_renderer_includes_validation_status():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "Validation valid: True" in rendered


def test_renderer_includes_category_coverage():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "## Category Coverage" in rendered
    assert "simple_ordinary_request" in rendered


def test_renderer_includes_minor_followups():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "renderer_next_lane_wording_drift" in rendered


def test_renderer_includes_safety_confirmation():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "## Safety Confirmation" in rendered
    assert "no prompt execution" in rendered


def test_renderer_blocks_invalid_corpus_without_leaking_offending_content():
    corpus = _corpus()
    corpus[0]["raw_prompt"] = "raw prompt: DO NOT LEAK UNIQUE_OFFENDING_CONTENT"
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(corpus)
    assert "blocked_invalid_metadata" in rendered
    assert "UNIQUE_OFFENDING_CONTENT" not in rendered


def test_renderer_omits_raw_final_private_provider_content_for_valid_corpus():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus()).lower()
    assert "raw prompt:" not in rendered
    assert "final answer:" not in rendered
    assert "private content:" not in rendered
    assert "provider output:" not in rendered


def test_json_safe_copy_returns_safe_copy_for_valid_corpus():
    corpus = _corpus()
    safe = corpus_mod.to_internal_turing_scenario_corpus_json_safe_v1(corpus)
    assert safe == corpus
    assert safe is not corpus


def test_json_safe_copy_returns_invalid_wrapper_for_unsafe_corpus():
    corpus = _corpus()
    corpus[0]["official_score"] = "official score: 100"
    safe = corpus_mod.to_internal_turing_scenario_corpus_json_safe_v1(corpus)
    assert safe["valid"] is False
    assert safe["blocked"] is True


def test_helpers_are_deterministic_for_same_corpus():
    assert _corpus() == _corpus()
    assert corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus()) == corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())


def test_no_helper_writes_files(tmp_path, monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("open should not be called")

    monkeypatch.setattr("builtins.open", fail_open)
    corpus_mod.build_internal_turing_scenario_corpus_v1()
    corpus_mod.validate_internal_turing_scenario_corpus_v1(_corpus())
    corpus_mod.summarize_internal_turing_scenario_corpus_v1(_corpus())
    corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())


def test_no_helper_calls_network_subprocess_model_search_advisor():
    source = inspect.getsource(corpus_mod)
    forbidden = ["subprocess", "requests", "urllib", "socket", "ChatResponder", "respond_chat", "generate_chat"]
    assert all(item not in source for item in forbidden)


def test_no_chatresponder_respond_chat_generate_chat_calls():
    source = inspect.getsource(corpus_mod)
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source


def test_no_official_claims_are_made_by_renderer():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus()).lower()
    assert "passed the turing test" not in rendered
    assert "certified" not in rendered


def test_no_runtime_ready_declaration_is_rendered():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus()).lower()
    assert "runtime ready" not in rendered
    assert "runtime-ready" not in rendered


def test_no_prompts_are_executable():
    for record in _corpus():
        assert record["prompt_execution_authorized"] is False
        assert "execute prompt" not in record["synthetic_user_turn_summary"].lower()


def test_no_final_answers_are_generated():
    for record in _corpus():
        assert record["final_answer_generated"] is False
        assert record["final_answer_required"] is False


def test_no_dot_weslr_writes_occur():
    for record in _corpus():
        assert record["dot_weslr_write_performed"] is False


def test_minor_followups_remain_visible():
    rendered = corpus_mod.render_internal_turing_scenario_corpus_markdown_v1(_corpus())
    assert "renderer_next_lane_wording_drift" in rendered
    assert "validator_phrase_key_limitation" in rendered


def test_corpus_validator_rejects_missing_category():
    corpus = [record for record in _corpus() if record["category"] != "anti_gaming_boundary"]
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(corpus)
    assert not result["valid"]
    assert "anti_gaming_boundary" in result["missing_categories"]


def test_corpus_validator_requires_expected_properties():
    corpus = _corpus()
    corpus[0]["expected_response_properties"] = []
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(corpus)
    assert not result["valid"]


def test_corpus_validator_requires_failure_modes():
    corpus = _corpus()
    corpus[0]["failure_modes"] = []
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(corpus)
    assert not result["valid"]


def test_corpus_validator_requires_dimension_targets():
    corpus = _corpus()
    corpus[0]["dimension_targets"] = []
    result = corpus_mod.validate_internal_turing_scenario_corpus_v1(corpus)
    assert not result["valid"]


def test_readiness_labels_required_values_present():
    labels = set(corpus_mod.INTERNAL_TURING_READINESS_LABELS_V1)
    assert "internal_turing_scenario_corpus_helpers_implemented" in labels
    assert "voice_downstream_not_current_priority" in labels


def test_all_labels_are_qualitative():
    assert all("score" not in label for label in corpus_mod.INTERNAL_TURING_QUALITATIVE_LABELS_V1)
    assert all("pass" not in label for label in corpus_mod.INTERNAL_TURING_QUALITATIVE_LABELS_V1)


def test_json_safe_invalid_wrapper_does_not_silently_sanitize():
    corpus = _corpus()
    corpus[0]["raw_prompt"] = "raw prompt: unsafe"
    result = corpus_mod.to_internal_turing_scenario_corpus_json_safe_v1(corpus)
    assert isinstance(result, dict)
    assert result["valid"] is False
    assert "raw_content_detected" in result["reason_labels"]


def test_valid_corpus_is_json_serializable():
    json.dumps(corpus_mod.to_internal_turing_scenario_corpus_json_safe_v1(_corpus()))
