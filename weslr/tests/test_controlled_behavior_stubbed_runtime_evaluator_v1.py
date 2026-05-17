from __future__ import annotations

from pathlib import Path

import pytest

from weslr.controlled_behavior_prompt_set import build_default_controlled_behavior_prompt_set_v1
from weslr.controlled_behavior_stubbed_runtime_evaluator import (
    ALLOWED_STUB_SOURCES_V1,
    EVALUATOR_TYPE_V1,
    ACTIVE_OBSERVATION_MODE_V1,
    build_stubbed_runtime_metadata_v1,
    evaluate_controlled_prompt_with_stubbed_runtime_v1,
    evaluate_prompt_set_with_stubbed_runtime_v1,
    render_controlled_behavior_stubbed_runtime_markdown_v1,
    summarize_controlled_behavior_stubbed_runtime_result_v1,
    to_controlled_behavior_stubbed_runtime_json_safe_v1,
    validate_controlled_behavior_stubbed_runtime_result_v1,
    validate_stubbed_runtime_metadata_v1,
)

REPO_HEAD = "379db7459a8a9db1d8da5d185e1baf2686ddf048"
FORBIDDEN_OUTPUT_TERMS = (
    "raw_prompt",
    "response_text",
    "source_urls",
    "hidden_prompt",
    "answer_key",
    "protected_material",
)


def _prompt(prompt_id: str = "ordinary_task_behavior_001"):
    prompt_set = build_default_controlled_behavior_prompt_set_v1()
    return next(item for item in prompt_set["prompts"] if item["prompt_id"] == prompt_id)


def _result(**kwargs):
    return evaluate_prompt_set_with_stubbed_runtime_v1(repo_head=REPO_HEAD, timestamp_local="2026-05-17 13:09", **kwargs)


def test_stub_metadata_builder_shape_and_allowed_labels():
    for label in ["pass_property", "fail_property", "needs_review", "not_observed", "blocked_by_boundary"]:
        metadata = build_stubbed_runtime_metadata_v1(
            prompt_id="ordinary_task_behavior_001",
            family="ordinary_task_behavior",
            property_label=label,
            properties_observed=["bounded"],
            safe_summary="Short sanitized stub summary.",
        )
        assert metadata["runtime_mode"] == ACTIVE_OBSERVATION_MODE_V1
        assert metadata["prompt_executed"] is False
        assert metadata["chat_responder_called"] is False
        assert metadata["model_calls"] is False
        assert metadata["advisor_calls"] is False
        assert metadata["web_search"] is False
        assert metadata["property_label"] == label
        assert validate_stubbed_runtime_metadata_v1(metadata)["valid"] is True


def test_stub_metadata_validation_accepts_safe_sources():
    for source in ALLOWED_STUB_SOURCES_V1:
        metadata = build_stubbed_runtime_metadata_v1(
            prompt_id="ordinary_task_behavior_001",
            family="ordinary_task_behavior",
            property_label="needs_review",
            properties_observed=["bounded"],
            safe_summary="Short sanitized stub summary.",
            stub_source=source,
        )
        assert validate_stubbed_runtime_metadata_v1(metadata)["valid"] is True


@pytest.mark.parametrize("flag", ["prompt_executed", "chat_responder_called", "model_calls", "advisor_calls", "web_search", "memory_writes", "raw_text_stored"])
def test_stub_metadata_validation_rejects_unsafe_flags(flag):
    metadata = build_stubbed_runtime_metadata_v1(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior", safe_summary="Short summary.")
    metadata[flag] = True
    validation = validate_stubbed_runtime_metadata_v1(metadata)
    assert validation["valid"] is False
    assert any(flag in error for error in validation["errors"])


@pytest.mark.parametrize("field,value", [("property_label", "score_99"), ("stub_source", "external_model_output"), ("family", "unknown_family")])
def test_stub_metadata_validation_rejects_invalid_label_source_family(field, value):
    metadata = build_stubbed_runtime_metadata_v1(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior", safe_summary="Short summary.")
    metadata[field] = value
    assert validate_stubbed_runtime_metadata_v1(metadata)["valid"] is False


@pytest.mark.parametrize("forbidden_key", ["raw_text", "raw_prompt", "response_text", "final_answer", "full_conversation", "source_urls", "hidden_prompt", "answer_key", "protected_material"])
def test_stub_metadata_validation_rejects_forbidden_raw_private_keys(forbidden_key):
    metadata = build_stubbed_runtime_metadata_v1(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior", safe_summary="Short summary.")
    metadata["unsafe"] = {forbidden_key: "synthetic unsafe"}
    validation = validate_stubbed_runtime_metadata_v1(metadata)
    assert validation["valid"] is False
    assert any(forbidden_key in error for error in validation["errors"])


@pytest.mark.parametrize("phrase", ["passed Turing test", "official benchmark", "certified intelligent", "IQ score", "human level", "conscious", "sentient", "soul", "alive"])
def test_stub_metadata_validation_rejects_forbidden_claim_text(phrase):
    metadata = build_stubbed_runtime_metadata_v1(prompt_id="ordinary_task_behavior_001", family="ordinary_task_behavior", safe_summary=phrase)
    validation = validate_stubbed_runtime_metadata_v1(metadata)
    assert validation["valid"] is False
    assert any(phrase.lower() in error for error in validation["errors"])


def test_single_prompt_evaluator_accepts_prompt_and_safe_stub_metadata():
    prompt = _prompt()
    stub = build_stubbed_runtime_metadata_v1(
        prompt_id=prompt["prompt_id"],
        family=prompt["family"],
        property_label="pass_property",
        properties_observed=["bounded", "useful"],
        safe_summary="Bounded synthetic stub observation.",
    )
    result = evaluate_controlled_prompt_with_stubbed_runtime_v1(prompt, stub_response_metadata=stub)
    assert result["validation"]["valid"] is True
    assert result["prompt_executed"] is False
    assert result["chat_responder_called"] is False
    assert result["property_label"] == "pass_property"


def test_single_prompt_evaluator_rejects_prompt_id_or_family_mismatch():
    prompt = _prompt()
    stub = build_stubbed_runtime_metadata_v1(prompt_id="wrong", family=prompt["family"], safe_summary="Short summary.")
    result = evaluate_controlled_prompt_with_stubbed_runtime_v1(prompt, stub_response_metadata=stub)
    assert result["validation"]["valid"] is False
    assert any("prompt_id mismatch" in error for error in result["validation"]["errors"])

    stub = build_stubbed_runtime_metadata_v1(prompt_id=prompt["prompt_id"], family="conduct_alignment", safe_summary="Short summary.")
    result = evaluate_controlled_prompt_with_stubbed_runtime_v1(prompt, stub_response_metadata=stub)
    assert result["validation"]["valid"] is False
    assert any("family mismatch" in error for error in result["validation"]["errors"])


def test_single_prompt_evaluator_missing_stub_returns_not_observed_safely():
    result = evaluate_controlled_prompt_with_stubbed_runtime_v1(_prompt())
    assert result["validation"]["valid"] is True
    assert result["observed"] is False
    assert result["property_label"] == "not_observed"
    assert result["prompt_executed"] is False


def test_batch_evaluator_default_safe_shape_report_valid_and_no_persistence():
    before = {p.relative_to(Path.cwd()) for p in Path.cwd().rglob(".weslr*")}
    result = _result()
    after = {p.relative_to(Path.cwd()) for p in Path.cwd().rglob(".weslr*")}
    assert after == before
    assert result["evaluator_type"] == EVALUATOR_TYPE_V1
    assert result["observation_mode"] == ACTIVE_OBSERVATION_MODE_V1
    assert result["prompt_execution"] is False
    assert result["chat_responder_calls"] is False
    assert result["model_calls"] is False
    assert result["advisor_calls"] is False
    assert result["web_search"] is False
    assert result["report"]["report_type"] == "weslr_behavior_evaluation_report_v1"
    assert result["validation"]["valid"] is True


def test_batch_evaluator_with_safe_stubs_observes_prompts_and_derives_labels():
    stubs = {
        "ordinary_task_behavior_001": build_stubbed_runtime_metadata_v1(
            prompt_id="ordinary_task_behavior_001",
            family="ordinary_task_behavior",
            property_label="pass_property",
            properties_observed=["bounded", "useful"],
            safe_summary="Bounded ordinary stub observation.",
        ),
        "conduct_alignment_001": build_stubbed_runtime_metadata_v1(
            prompt_id="conduct_alignment_001",
            family="conduct_alignment",
            property_label="pass_property",
            properties_observed=["transparent_uncertainty"],
            safe_summary="Constraint-following stub observation.",
        ),
        "live_slice_behavior_001": build_stubbed_runtime_metadata_v1(
            prompt_id="live_slice_behavior_001",
            family="live_slice_behavior",
            property_label="pass_property",
            properties_observed=["plan_slice_metadata_when_enabled"],
            safe_summary="Plan slice boundary metadata stub observed.",
        ),
    }
    result = _result(stub_metadata_by_prompt_id=stubs)
    summary = summarize_controlled_behavior_stubbed_runtime_result_v1(result)
    assert result["validation"]["valid"] is True
    assert result["family_results"]["ordinary_task_behavior"]["label"] == "pass_property"
    assert result["family_results"]["conduct_alignment"]["label"] == "pass_property"
    assert result["report"]["readiness_label"] == "bounded_task_readiness"
    assert summary["observed_prompt_count"] > 0


def test_unknown_stub_prompt_id_invalid():
    result = _result(stub_metadata_by_prompt_id={"unknown_prompt": build_stubbed_runtime_metadata_v1(prompt_id="unknown_prompt", family="ordinary_task_behavior", safe_summary="Short summary.")})
    assert result["validation"]["valid"] is False
    assert any("unknown stub prompt_id" in error for error in result["validation"]["errors"])


@pytest.mark.parametrize(
    "flag",
    [
        "prompt_execution",
        "chat_responder_calls",
        "model_calls",
        "advisor_calls",
        "web_search",
        "numeric_scores_used",
        "official_benchmark_claim",
        "turing_test_claim",
        "iq_claim",
        "certification_claim",
        "raw_private_text_included",
        "weslr_runtime_state_created",
    ],
)
def test_result_validation_rejects_unsafe_flags(flag):
    result = _result()
    result[flag] = True
    validation = validate_controlled_behavior_stubbed_runtime_result_v1(result)
    assert validation["valid"] is False
    assert any(flag in error for error in validation["errors"])


def test_json_safe_copy_is_not_sanitizer():
    result = _result()
    result["unsafe"] = {"raw_text": "synthetic unsafe"}
    copied = to_controlled_behavior_stubbed_runtime_json_safe_v1(result)
    assert copied["unsafe"]["raw_text"] == "synthetic unsafe"
    validation = validate_controlled_behavior_stubbed_runtime_result_v1(copied)
    assert validation["valid"] is False
    assert any("raw_text" in error for error in validation["errors"])


def test_summary_safety_labels_counts_status_only():
    result = _result()
    result["unsafe"] = {
        "raw_prompt": "synthetic",
        "response_text": "synthetic",
        "source_urls": ["https://example.invalid"],
        "hidden_prompt": "synthetic",
        "answer_key": "synthetic",
        "protected_material": "synthetic",
    }
    summary = summarize_controlled_behavior_stubbed_runtime_result_v1(result)
    text = repr(summary).lower()
    assert summary["prompt_count"] == 29
    assert summary["family_count"] == 9
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in text
    assert "://" not in text


def test_markdown_safety_sections_and_no_unsafe_content():
    markdown = render_controlled_behavior_stubbed_runtime_markdown_v1(_result())
    for section in [
        "SECTION 1 — STATUS",
        "SECTION 2 — STUBBED RUNTIME BOUNDARIES",
        "SECTION 3 — FAMILY RESULTS",
        "SECTION 4 — READINESS LABEL",
        "SECTION 5 — SAFETY / CLAIM BOUNDARIES",
        "SECTION 6 — VALIDATION SUMMARY",
        "SECTION 7 — RECOMMENDED NEXT STEP",
    ]:
        assert section in markdown
    lowered = markdown.lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        assert term not in lowered
    assert "://" not in lowered
    assert "official benchmark" not in lowered
    assert "passed turing test" not in lowered
    assert "certified" not in lowered
    assert "iq score" not in lowered
    assert "conscious" not in lowered
    assert "sentient" not in lowered


def test_no_side_effect_files_or_live_calls_created():
    before = {p.relative_to(Path.cwd()) for p in Path.cwd().rglob(".weslr*")}
    result = _result()
    validate_controlled_behavior_stubbed_runtime_result_v1(result)
    summarize_controlled_behavior_stubbed_runtime_result_v1(result)
    render_controlled_behavior_stubbed_runtime_markdown_v1(result)
    to_controlled_behavior_stubbed_runtime_json_safe_v1(result)
    after = {p.relative_to(Path.cwd()) for p in Path.cwd().rglob(".weslr*")}
    assert after == before
    assert result["chat_responder_calls"] is False
    assert result["model_calls"] is False
    assert result["advisor_calls"] is False
    assert result["web_search"] is False
