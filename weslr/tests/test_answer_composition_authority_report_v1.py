from __future__ import annotations

import copy
import inspect

import pytest

import weslr.answer_composition_authority_report as report_helpers
from weslr.answer_composition_authority import (
    ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1,
    build_answer_composition_authority_artifact_v1,
)
from weslr.answer_composition_authority_report import (
    ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_AGGREGATE_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_INPUT_TYPES_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_INPUT_TYPES_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1,
    ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1,
    build_answer_composition_authority_report_v1,
    derive_answer_composition_authority_report_aggregate_labels_v1,
    render_answer_composition_authority_report_markdown_v1,
    summarize_answer_composition_authority_report_v1,
    to_answer_composition_authority_report_json_safe_v1,
    validate_answer_composition_authority_report_v1,
)


def safe_artifact() -> dict:
    return build_answer_composition_authority_artifact_v1(
        source_metadata_types=list(ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        composition_review_dimensions=[
            "evidence_gate_visible",
            "governance_gate_visible",
            "final_answer_gate_visible",
        ],
        allowed_review_labels=list(ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1),
    )


def safe_report() -> dict:
    return build_answer_composition_authority_report_v1(source_artifacts=[safe_artifact()])


def assert_blocked(report: dict, expected_key: str | None = None) -> dict:
    validation = validate_answer_composition_authority_report_v1(report)
    assert validation["valid"] is False
    assert validation["blocked"] is True
    if expected_key:
        joined = "\n".join(validation["errors"])
        assert expected_key in joined or validation.get(expected_key) is True
    return validation


def test_module_imports_without_side_effects():
    assert report_helpers.REPORT_TYPE_V1 == "answer_composition_authority_report_v1"


@pytest.mark.parametrize("name", [
    "build_answer_composition_authority_report_v1",
    "validate_answer_composition_authority_report_v1",
    "summarize_answer_composition_authority_report_v1",
    "derive_answer_composition_authority_report_aggregate_labels_v1",
    "render_answer_composition_authority_report_markdown_v1",
    "to_answer_composition_authority_report_json_safe_v1",
])
def test_public_api_exists(name):
    assert callable(getattr(report_helpers, name))


@pytest.mark.parametrize("label", [
    "answer_composition_authority_artifact_v1",
    "answer_composition_authority_artifact_validation_output_v1",
    "answer_composition_authority_artifact_summary_v1",
    "answer_composition_authority_artifact_json_safe_v1",
    "answer_composition_authority_safe_review_label_v1",
    "answer_composition_authority_safe_gate_status_label_v1",
    "answer_composition_authority_safe_risk_followup_label_v1",
])
def test_constants_include_allowed_report_input_types(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_INPUT_TYPES_V1


@pytest.mark.parametrize("label", [
    "raw_prompt",
    "raw_response",
    "final_answer_prose",
    "final_response_text",
    "hidden_prompt",
    "answer_key",
    "private_content",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue_transcript",
    "official_score",
    "judge_decision",
    "scoring_result",
    "benchmark_pass_fail_claim",
    "turing_iq_certification_product_readiness_claim",
    "consciousness_sentience_claim",
    "dot_weslr_persistence_payload",
    "feature_flag_activation_payload",
    "chat_responder_runtime_output",
    "occ_openclaw_as_weslr_framing",
])
def test_constants_include_forbidden_report_input_types(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_INPUT_TYPES_V1


@pytest.mark.parametrize("gate,status", [
    ("evidence_gate", "not_established_or_not_present"),
    ("provenance_gate", "not_established_or_not_present"),
    ("governance_gate", "review_required_or_not_present"),
    ("memory_gate", "review_required_or_not_present"),
    ("domain_gate", "review_required_or_not_present"),
    ("uncertainty_gate", "required_or_not_present"),
    ("final_answer_gate", "generation_not_authorized"),
    ("runtime_gate", "runtime_wiring_requires_separate_approval"),
    ("prompt_execution_gate", "prompt_execution_not_authorized"),
    ("provider_gate", "provider_calls_not_authorized"),
    ("persistence_gate", "dot_weslr_writes_not_authorized"),
    ("official_claim_gate", "official_claim_not_allowed"),
    ("identity_gate", "occ_openclaw_not_weslr"),
])
def test_constants_include_required_gate_coverage(gate, status):
    assert ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1[gate] == status


@pytest.mark.parametrize("label", [
    "source_artifacts_present",
    "source_artifacts_validated",
    "gate_coverage_visible",
    "denied_paths_visible",
    "risks_carried_forward",
    "metadata_only_report",
    "internal_only_report",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
])
def test_constants_include_allowed_aggregate_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_AGGREGATE_LABELS_V1


@pytest.mark.parametrize("label", [
    "ready_for_runtime",
    "safe_to_wire_runtime",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_composition_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
    "passed_turing_test",
    "official_score",
    "certified",
    "production_ready",
    "product_ready",
    "conscious",
    "sentient",
])
def test_constants_include_forbidden_aggregate_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1


@pytest.mark.parametrize("risk", [
    "metadata-overread",
    "report-as-judge/score",
    "renderer wording drift",
    "artifact/report-as-authority",
    "OCC/WESLR identity confusion",
    "validation-pass-as-authority",
    "final-answer-prose leak",
])
def test_constants_include_visible_risks(risk):
    assert risk in ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1


def test_report_builder_creates_required_fields():
    report = safe_report()
    for field in (
        "report_type",
        "schema_version",
        "metadata_only",
        "internal_only",
        "report_scope",
        "source_artifact_type",
        "source_artifact_count",
        "source_artifact_summaries",
        "source_artifact_validation_statuses",
        "report_inputs",
        "allowed_report_input_types",
        "forbidden_report_input_types",
        "gate_coverage_summary",
        "denied_path_summary",
        "aggregate_labels",
        "visible_risks",
        "followups",
        "validation_status",
        "answer_composition_authorized",
        "final_answer_generated",
        "answer_authority_granted",
        "runtime_authority_granted",
        "prompt_execution_allowed",
        "live_dialogue_allowed",
        "raw_content_allowed",
        "official_claim_allowed",
        "model_call_made",
        "search_call_made",
        "advisor_call_made",
        "dot_weslr_write_performed",
        "feature_flag_enabled",
        "judge_authority_granted",
        "scoring_authorized",
    ):
        assert field in report


@pytest.mark.parametrize("flag", [
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
])
def test_report_builder_sets_all_authority_runtime_prompt_final_flags_false(flag):
    assert safe_report()[flag] is False


def test_report_builder_sets_metadata_flags_true():
    report = safe_report()
    assert report["metadata_only"] is True
    assert report["internal_only"] is True


def test_report_builder_summarizes_source_artifacts_without_raw_content():
    report = safe_report()
    assert report["source_artifact_count"] == 1
    assert report["source_artifact_validation_statuses"][0]["valid"] is True
    assert report["source_artifact_summaries"][0]["source_metadata_type_count"] == len(
        ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1
    )
    serialized = repr(report).lower()
    assert "raw prompt:" not in serialized
    assert "provider output:" not in serialized
    assert "final answer:" not in serialized


def test_validator_accepts_safe_report():
    validation = validate_answer_composition_authority_report_v1(safe_report())
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["safety_booleans_valid"] is True
    assert validation["gate_coverage_valid"] is True
    assert validation["denied_paths_valid"] is True
    assert validation["aggregate_labels_valid"] is True


@pytest.mark.parametrize("field", [
    "report_type",
    "schema_version",
    "metadata_only",
    "internal_only",
    "report_scope",
    "source_artifact_type",
    "source_artifact_count",
    "source_artifact_summaries",
    "source_artifact_validation_statuses",
    "report_inputs",
    "allowed_report_input_types",
    "forbidden_report_input_types",
    "gate_coverage_summary",
    "denied_path_summary",
    "aggregate_labels",
    "visible_risks",
    "validation_status",
    "answer_composition_authorized",
    "live_dialogue_allowed",
])
def test_validator_rejects_missing_required_field(field):
    report = safe_report()
    report.pop(field)
    assert_blocked(report, f"missing_required_field:{field}")


@pytest.mark.parametrize("flag", [
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
])
def test_validator_rejects_true_authority_fields(flag):
    report = safe_report()
    report[flag] = True
    assert_blocked(report, f"authority_flag_not_false:{flag}")


@pytest.mark.parametrize("flag", ["metadata_only", "internal_only"])
def test_validator_rejects_false_metadata_flags(flag):
    report = safe_report()
    report[flag] = False
    assert_blocked(report, f"metadata_flag_not_true:{flag}")


def test_validator_rejects_invalid_source_artifact_validation_status():
    bad_artifact = safe_artifact()
    bad_artifact["answer_composition_authorized"] = True
    report = build_answer_composition_authority_report_v1(source_artifacts=[bad_artifact])
    validation = assert_blocked(report, "source_artifact_validation_status_not_valid")
    assert validation["unsafe_source_artifacts"] == ["0"]


def test_validator_rejects_unknown_report_input():
    report = safe_report()
    report["report_inputs"] = ["unknown_input"]
    validation = assert_blocked(report, "unknown_report_inputs")
    assert validation["unknown_report_inputs"] == ["unknown_input"]


def test_validator_rejects_forbidden_report_input():
    report = safe_report()
    report["report_inputs"] = ["raw_prompt"]
    validation = assert_blocked(report, "forbidden_report_inputs")
    assert validation["forbidden_report_inputs"] == ["raw_prompt"]


def test_validator_rejects_missing_gate_coverage():
    report = safe_report()
    report["gate_coverage_summary"].pop("provider_gate")
    validation = assert_blocked(report, "missing_gate_coverage")
    assert "provider_gate" in validation["missing_gate_coverage"]


def test_validator_rejects_unsafe_gate_coverage():
    report = safe_report()
    report["gate_coverage_summary"]["runtime_gate"] = "runtime_authority_granted"
    validation = assert_blocked(report, "unsafe_gate_coverage")
    assert any("runtime_gate" in item for item in validation["unsafe_gate_coverage"])


def test_validator_rejects_missing_denied_path():
    report = safe_report()
    report["denied_path_summary"] = list(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1[:-1])
    validation = assert_blocked(report, "missing_denied_paths")
    assert "official_claims_not_allowed" in validation["missing_denied_paths"]


def test_validator_rejects_unknown_aggregate_label():
    report = safe_report()
    report["aggregate_labels"].append("unknown_label")
    validation = assert_blocked(report, "unknown_aggregate_labels")
    assert "unknown_label" in validation["unknown_aggregate_labels"]


@pytest.mark.parametrize("label", ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1)
def test_validator_rejects_forbidden_aggregate_labels(label):
    report = safe_report()
    report["aggregate_labels"] = [label]
    assert_blocked(report, "forbidden_aggregate_labels")


@pytest.mark.parametrize("key,value,expected", [
    ("raw_prompt_text", "what is your answer?", "unsafe_key_detected"),
    ("note", "raw prompt: unsafe", "raw_content_detected"),
    ("note", "raw response: unsafe", "raw_content_detected"),
    ("note", "private content: unsafe", "private_content_detected"),
    ("note", "hidden prompt: unsafe", "hidden_prompt_detected"),
    ("note", "answer key: unsafe", "answer_key_detected"),
    ("note", "provider output: unsafe", "provider_output_detected"),
    ("note", "model output: unsafe", "provider_output_detected"),
    ("note", "runtime output: unsafe", "runtime_output_detected"),
    ("note", "ChatResponder runtime output", "runtime_output_detected"),
    ("note", "final answer: unsafe", "final_answer_detected"),
    ("note", "final response text: unsafe", "final_answer_detected"),
    ("note", "official turing pass", "official_claim_detected"),
    ("note", "official iq", "official_claim_detected"),
    ("note", "official score: 100", "judge_or_score_detected"),
    ("note", "judge decision: unsafe", "judge_or_score_detected"),
    ("note", "scoring engine", "judge_or_score_detected"),
    ("note", "execute prompt", "prompt_execution_detected"),
    ("note", "live dialogue transcript", "live_dialogue_detected"),
    ("note", "call model", "provider_call_detected"),
    ("note", ".weslr write", "dot_weslr_write_detected"),
    ("note", "feature flag activation", "feature_flag_detected"),
    ("note", "answer authority granted", "answer_authority_detected"),
    ("note", "answer composition authorized", "composition_authority_detected"),
    ("note", "runtime authority granted", "runtime_authority_detected"),
    ("note", "benchmark pass/fail", "benchmark_claim_detected"),
    ("note", "WESLR is conscious", "consciousness_claim_detected"),
    ("note", "OCC is WESLR", "identity_confusion_detected"),
])
def test_validator_rejects_unsafe_content_markers(key, value, expected):
    report = safe_report()
    report[key] = value
    assert_blocked(report, expected)


def test_summary_contains_safe_counts_status_only():
    summary = summarize_answer_composition_authority_report_v1(safe_report())
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["source_artifact_count"] == 1
    assert summary["source_artifact_valid_count"] == 1
    assert summary["gate_coverage_valid"] is True
    assert summary["all_authority_flags_false"] is True
    assert "raw prompt" not in repr(summary).lower()
    assert "final answer:" not in repr(summary).lower()


def test_derive_aggregate_labels_are_safe_and_qualitative():
    labels = derive_answer_composition_authority_report_aggregate_labels_v1(safe_report())
    assert "source_artifacts_present" in labels
    assert "source_artifacts_validated" in labels
    assert "metadata_only_report" in labels
    assert "answer_composition_not_authorized" in labels
    for forbidden in ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1:
        assert forbidden not in labels


def test_renderer_output_contains_safe_internal_markdown_only():
    rendered = render_answer_composition_authority_report_markdown_v1(safe_report())
    assert rendered.startswith("# WESLR Answer Composition Authority Report V1")
    assert "metadata evidence is not answer text" in rendered
    assert "answer_composition_not_authorized" in rendered
    assert "final_answer_generation_not_authorized" in rendered
    forbidden = [
        "ready_for_runtime",
        "production_ready",
        "approved_for_live_answers",
        "final answer:",
        "raw prompt:",
        "provider output:",
        "official score:",
    ]
    for marker in forbidden:
        assert marker not in rendered.lower()


def test_invalid_renderer_blocks_without_leaking_unsafe_content():
    report = safe_report()
    secret = "raw prompt: DO NOT LEAK THIS"
    report["unsafe"] = secret
    rendered = render_answer_composition_authority_report_markdown_v1(report)
    assert "Blocked" in rendered
    assert "raw_content_detected" in rendered
    assert "DO NOT LEAK THIS" not in rendered
    assert secret not in rendered


def test_json_safe_returns_deep_copy_for_valid_report():
    report = safe_report()
    result = to_answer_composition_authority_report_json_safe_v1(report)
    assert result == report
    assert result is not report
    result["aggregate_labels"].append("mutated")
    assert "mutated" not in report["aggregate_labels"]


def test_json_safe_invalid_wrapper_does_not_silently_sanitize_into_valid_report():
    report = safe_report()
    report["unsafe"] = "provider output: DO NOT LEAK THIS"
    result = to_answer_composition_authority_report_json_safe_v1(report)
    assert result["report_type"] == "answer_composition_authority_report_v1_invalid"
    assert result["valid"] is False
    assert result["blocked"] is True
    assert result["invalid_wrapper"] is True
    assert result["safe_to_render"] is False
    assert "provider_output_detected" in result["errors"]
    assert "DO NOT LEAK THIS" not in repr(result)
    assert result["answer_composition_authorized"] is False
    assert result["answer_authority_granted"] is False
    assert result["final_answer_generated"] is False
    assert result["runtime_authority_granted"] is False


def test_determinism_across_repeated_calls():
    first = safe_report()
    second = safe_report()
    assert first == second
    assert validate_answer_composition_authority_report_v1(first) == validate_answer_composition_authority_report_v1(second)
    assert summarize_answer_composition_authority_report_v1(first) == summarize_answer_composition_authority_report_v1(second)
    assert render_answer_composition_authority_report_markdown_v1(first) == render_answer_composition_authority_report_markdown_v1(second)


def test_builder_accepts_tuple_and_set_inputs_deterministically():
    report = build_answer_composition_authority_report_v1(
        source_artifacts=(safe_artifact(),),
        report_inputs={"answer_composition_authority_artifact_v1"},
        followups={"b", "a"},
    )
    assert report["report_inputs"] == ["answer_composition_authority_artifact_v1"]
    assert report["followups"] == ["a", "b"]


def test_non_mapping_report_is_blocked():
    validation = validate_answer_composition_authority_report_v1(["not", "mapping"])  # type: ignore[arg-type]
    assert validation["valid"] is False
    assert "report_not_mapping" in validation["errors"]


def test_invalid_schema_and_report_type_are_blocked():
    report = safe_report()
    report["report_type"] = "wrong"
    report["schema_version"] = "wrong"
    validation = assert_blocked(report)
    assert "report_type_invalid" in validation["errors"]
    assert "schema_version_invalid" in validation["errors"]


def test_no_file_write_provider_subprocess_network_runtime_references_in_module_source():
    source = inspect.getsource(report_helpers)
    forbidden_tokens = [
        "ChatResponder",
        "respond_chat(",
        "generate_chat(",
        "subprocess",
        "requests",
        "urllib",
        "open(",
        "Path(",
        "write_text",
        "model_call(",
        "search_call(",
        "advisor_call(",
        "socket",
    ]
    for token in forbidden_tokens:
        assert token not in source


def test_helpers_do_not_write_files_or_dot_weslr(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected write or provider action")

    monkeypatch.setattr("builtins.open", fail)
    report = safe_report()
    assert validate_answer_composition_authority_report_v1(report)["valid"] is True
    assert summarize_answer_composition_authority_report_v1(report)["valid"] is True
    assert "metadata evidence is not answer text" in render_answer_composition_authority_report_markdown_v1(report)
    assert to_answer_composition_authority_report_json_safe_v1(report)["report_type"] == report_helpers.REPORT_TYPE_V1


def test_no_mutation_during_validation_summary_render_or_json_safe_invalid():
    report = safe_report()
    report["unsafe"] = "raw response: no leak"
    before = copy.deepcopy(report)
    validate_answer_composition_authority_report_v1(report)
    summarize_answer_composition_authority_report_v1(report)
    render_answer_composition_authority_report_markdown_v1(report)
    to_answer_composition_authority_report_json_safe_v1(report)
    assert report == before


def test_renderer_blocks_non_mapping_without_traceback():
    rendered = render_answer_composition_authority_report_markdown_v1(["bad"])  # type: ignore[arg-type]
    assert "Blocked" in rendered
    assert "report_not_mapping" in rendered


def test_json_safe_blocks_non_mapping_without_traceback():
    result = to_answer_composition_authority_report_json_safe_v1(["bad"])  # type: ignore[arg-type]
    assert result["valid"] is False
    assert result["blocked"] is True
    assert "report_not_mapping" in result["errors"]


def test_valid_report_contains_no_raw_prompt_response_private_provider_or_final_answer_content():
    report = safe_report()
    serialized = repr(report).lower()
    forbidden = [
        "raw prompt:",
        "raw response:",
        "private content:",
        "hidden prompt:",
        "answer key:",
        "provider output:",
        "official score:",
        "final answer:",
        "final response text:",
    ]
    for marker in forbidden:
        assert marker not in serialized


def test_next_lane_is_review_not_runtime():
    summary = summarize_answer_composition_authority_report_v1(safe_report())
    assert summary["next_lane_recommendation"] == "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_IMPLEMENTATION_V1"
    assert "RUNTIME" not in summary["next_lane_recommendation"]
