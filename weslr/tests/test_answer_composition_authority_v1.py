from __future__ import annotations

import copy
import inspect

import pytest

import weslr.answer_composition_authority as composition
from weslr.answer_composition_authority import (
    ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1,
    ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1,
    ANSWER_COMPOSITION_AUTHORITY_MINOR_RISKS_V1,
    ANSWER_COMPOSITION_AUTHORITY_READINESS_LABELS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1,
    ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1,
    build_answer_composition_authority_artifact_v1,
    render_answer_composition_authority_artifact_markdown_v1,
    summarize_answer_composition_authority_artifact_v1,
    to_answer_composition_authority_artifact_json_safe_v1,
    validate_answer_composition_authority_artifact_v1,
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


def assert_blocked(artifact: dict, expected_key: str | None = None) -> dict:
    validation = validate_answer_composition_authority_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation["blocked"] is True
    if expected_key:
        joined = "\n".join(validation["errors"])
        assert expected_key in joined or validation.get(expected_key) is True
    return validation


def test_module_imports_without_side_effects():
    assert composition.ARTIFACT_TYPE_V1 == "answer_composition_authority_artifact_v1"


@pytest.mark.parametrize("name", [
    "build_answer_composition_authority_artifact_v1",
    "validate_answer_composition_authority_artifact_v1",
    "summarize_answer_composition_authority_artifact_v1",
    "render_answer_composition_authority_artifact_markdown_v1",
    "to_answer_composition_authority_artifact_json_safe_v1",
])
def test_public_api_exists(name):
    assert callable(getattr(composition, name))


@pytest.mark.parametrize("label", [
    "answer_authority_boundary_artifact_metadata",
    "answer_composition_authority_boundary_design_metadata",
    "internal_turing_scenario_corpus_metadata",
    "internal_turing_multi_turn_protocol_metadata",
    "ranked_response_shadow_report_run_metadata",
    "ranked_native_interop_report_run_metadata",
    "behavior_evaluation_report_metadata",
    "internal_evaluation_corpus_metadata",
    "cognition_target_model_design_metadata",
    "ranked_state_grounded_response_formation_design_metadata",
])
def test_constants_include_approved_source_metadata_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1


@pytest.mark.parametrize("label", [
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_text",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_authority",
    "composition_gate_status_visible",
    "evidence_gate_visible",
    "provenance_gate_visible",
    "governance_gate_visible",
    "memory_gate_visible",
    "domain_gate_visible",
    "uncertainty_gate_visible",
    "raw_content_gate_visible",
    "provider_gate_visible",
    "persistence_gate_visible",
    "official_claim_gate_visible",
    "occ_openclaw_identity_boundary_visible",
    "denied_paths_visible",
    "visible_risks_carried_forward",
])
def test_constants_include_allowed_review_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1


@pytest.mark.parametrize("label", [
    "final_response_text_authorized",
    "live_answer_composition_authorized",
    "runtime_route_activation_authorized",
    "chat_responder_edit_authorized",
    "prompt_execution_authorized",
    "live_dialogue_authorized",
    "model_search_advisor_calls_authorized",
    "dot_weslr_write_authorized",
    "feature_flag_authorized",
    "scoring_authorized",
    "judge_authority_granted",
    "benchmark_claim_authorized",
    "official_claim_authorized",
    "deployment_readiness_authorized",
    "product_readiness_authorized",
    "final_answer_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
    "answer_composition_authorized",
])
def test_constants_include_forbidden_inference_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1


@pytest.mark.parametrize("label", [
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_text",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_authority",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "live_dialogue_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claim_not_allowed",
    "runtime_wiring_requires_separate_approval",
    "final_answer_composition_requires_separate_design",
    "occ_openclaw_not_weslr",
])
def test_constants_include_required_no_authority_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1


@pytest.mark.parametrize("gate,status", [
    ("evidence_gate", "evidence_sufficiency_not_established"),
    ("provenance_gate", "provenance_sufficiency_not_established"),
    ("governance_gate", "governance_review_required"),
    ("memory_gate", "memory_boundary_review_required"),
    ("domain_gate", "domain_constraints_review_required"),
    ("uncertainty_gate", "uncertainty_honesty_required"),
    ("final_answer_gate", "final_answer_generation_not_authorized"),
    ("runtime_gate", "runtime_wiring_requires_separate_approval"),
    ("prompt_execution_gate", "prompt_execution_not_authorized"),
    ("provider_gate", "provider_calls_not_authorized"),
    ("persistence_gate", "dot_weslr_writes_not_authorized"),
    ("official_claim_gate", "official_claim_not_allowed"),
    ("identity_gate", "occ_openclaw_not_weslr"),
])
def test_constants_include_required_gate_statuses(gate, status):
    assert ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1[gate] == status


@pytest.mark.parametrize("label", [
    "ready_for_runtime",
    "safe_to_wire_runtime",
    "safe_to_replace_live_output",
    "passed_turing_test",
    "officially_intelligent",
    "certified",
    "human_level",
    "conscious",
    "sentient",
    "production_ready",
    "product_ready",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
    "answer_composition_authorized",
])
def test_constants_include_forbidden_label_drift(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1


@pytest.mark.parametrize("label", [
    "metadata-overread risk",
    "report-as-judge/score risk",
    "renderer wording drift",
    "artifact-as-authority risk",
    "OCC/WESLR identity confusion risk",
    "validation-pass-as-authority risk",
    "final-answer-prose leak risk",
])
def test_constants_include_minor_risks(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_MINOR_RISKS_V1


@pytest.mark.parametrize("label", [
    "answer_composition_authority_helpers_implemented",
    "helper_only",
    "metadata_only",
    "qualitative_only",
    "internal_only_non_official",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "minor_followup_carried_forward",
])
def test_constants_include_readiness_labels(label):
    assert label in ANSWER_COMPOSITION_AUTHORITY_READINESS_LABELS_V1


def test_artifact_builder_creates_required_fields():
    artifact = safe_artifact()
    for field in (
        "artifact_type",
        "schema_version",
        "metadata_only",
        "internal_only",
        "source_metadata_types",
        "composition_review_dimensions",
        "composition_gate_statuses",
        "allowed_review_labels",
        "forbidden_inference_labels",
        "required_no_authority_labels",
        "minor_risks",
        "readiness_labels",
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
        assert field in artifact


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
def test_artifact_builder_sets_all_authority_runtime_prompt_final_flags_false(flag):
    assert safe_artifact()[flag] is False


def test_artifact_builder_sets_metadata_flags_true():
    artifact = safe_artifact()
    assert artifact["metadata_only"] is True
    assert artifact["internal_only"] is True


def test_artifact_builder_includes_required_no_authority_labels_by_default():
    artifact = safe_artifact()
    assert set(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1).issubset(set(artifact["required_no_authority_labels"]))


def test_artifact_builder_includes_forbidden_inference_labels_by_default():
    artifact = safe_artifact()
    assert set(ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1).issubset(set(artifact["forbidden_inference_labels"]))


def test_validator_accepts_safe_artifact():
    validation = validate_answer_composition_authority_artifact_v1(safe_artifact())
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["safety_booleans_valid"] is True
    assert validation["gate_statuses_valid"] is True


@pytest.mark.parametrize("field", [
    "artifact_type",
    "schema_version",
    "metadata_only",
    "internal_only",
    "source_metadata_types",
    "composition_review_dimensions",
    "composition_gate_statuses",
    "allowed_review_labels",
    "forbidden_inference_labels",
    "required_no_authority_labels",
    "minor_risks",
    "readiness_labels",
    "answer_composition_authorized",
    "live_dialogue_allowed",
])
def test_validator_rejects_missing_required_field(field):
    artifact = safe_artifact()
    artifact.pop(field)
    assert_blocked(artifact, f"missing_required_field:{field}")


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
    artifact = safe_artifact()
    artifact[flag] = True
    assert_blocked(artifact, f"authority_flag_not_false:{flag}")


@pytest.mark.parametrize("flag", ["metadata_only", "internal_only"])
def test_validator_rejects_false_metadata_flags(flag):
    artifact = safe_artifact()
    artifact[flag] = False
    assert_blocked(artifact, f"metadata_flag_not_true:{flag}")


def test_validator_rejects_unknown_source_metadata_label():
    artifact = safe_artifact()
    artifact["source_metadata_types"] = ["unknown_metadata"]
    validation = assert_blocked(artifact, "unknown_source_metadata_types")
    assert validation["unknown_source_metadata_types"] == ["unknown_metadata"]


def test_validator_rejects_unknown_allowed_review_label():
    artifact = safe_artifact()
    artifact["allowed_review_labels"] = ["metadata_evidence_useful_for_review", "unknown_allowed"]
    validation = assert_blocked(artifact, "unknown_allowed_review_labels")
    assert validation["unknown_allowed_review_labels"] == ["unknown_allowed"]


def test_validator_rejects_missing_required_no_authority_label():
    artifact = safe_artifact()
    artifact["required_no_authority_labels"] = list(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1[:-1])
    validation = assert_blocked(artifact, "missing_no_authority_labels")
    assert "occ_openclaw_not_weslr" in validation["missing_no_authority_labels"]


def test_validator_rejects_missing_forbidden_inference_label():
    artifact = safe_artifact()
    artifact["forbidden_inference_labels"] = list(ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1[:-1])
    validation = assert_blocked(artifact, "missing_forbidden_inference_labels")
    assert "answer_composition_authorized" in validation["missing_forbidden_inference_labels"]


def test_validator_rejects_forbidden_label_as_allowed_review_label():
    artifact = safe_artifact()
    artifact["allowed_review_labels"] = ["metadata_evidence_useful_for_review", "answer_composition_authorized"]
    assert_blocked(artifact, "forbidden_inference_label_used_as_allowed_review_label")


def test_validator_rejects_missing_gate_status():
    artifact = safe_artifact()
    artifact["composition_gate_statuses"].pop("provider_gate")
    validation = assert_blocked(artifact, "missing_gate_statuses")
    assert "provider_gate" in validation["missing_gate_statuses"]


def test_validator_rejects_unsafe_gate_status():
    artifact = safe_artifact()
    artifact["composition_gate_statuses"]["runtime_gate"] = "runtime_authority_granted"
    validation = assert_blocked(artifact, "unsafe_gate_statuses")
    assert any("runtime_gate" in item for item in validation["unsafe_gate_statuses"])


@pytest.mark.parametrize("key,value,expected", [
    ("raw_prompt_text", "what is your answer?", "unsafe_key_detected"),
    ("note", "raw prompt: unsafe", "raw_content_detected"),
    ("note", "raw response: unsafe", "raw_content_detected"),
    ("note", "private content: unsafe", "private_content_detected"),
    ("note", "hidden prompt: unsafe", "hidden_prompt_detected"),
    ("note", "answer key: unsafe", "answer_key_detected"),
    ("note", "provider output: unsafe", "provider_output_detected"),
    ("note", "model output: unsafe", "provider_output_detected"),
    ("note", "final answer: unsafe", "final_answer_detected"),
    ("note", "final answer prose", "final_answer_detected"),
    ("note", "official turing pass", "official_claim_detected"),
    ("note", "passed the turing test", "official_claim_detected"),
    ("note", "official score: 100", "judge_or_score_detected"),
    ("note", "scoring engine", "judge_or_score_detected"),
    ("note", "execute prompt", "prompt_execution_detected"),
    ("note", "live dialogue", "live_dialogue_detected"),
    ("note", "call model", "provider_call_detected"),
    ("note", ".weslr write", "dot_weslr_write_detected"),
    ("note", "enable feature flag", "feature_flag_detected"),
    ("note", "answer authority granted", "answer_authority_detected"),
    ("note", "answer composition authorized", "composition_authority_detected"),
    ("note", "runtime authority granted", "runtime_authority_detected"),
    ("note", "WESLR is conscious", "consciousness_claim_detected"),
    ("note", "OCC is WESLR", "identity_confusion_detected"),
])
def test_validator_rejects_unsafe_content_markers(key, value, expected):
    artifact = safe_artifact()
    artifact[key] = value
    assert_blocked(artifact, expected)


@pytest.mark.parametrize("label", ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1)
def test_validator_rejects_forbidden_label_drift(label):
    artifact = safe_artifact()
    artifact["drift"] = label
    assert_blocked(artifact, "forbidden_label_drift")


def test_summary_contains_safe_counts_status_only():
    summary = summarize_answer_composition_authority_artifact_v1(safe_artifact())
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["source_metadata_type_count"] == len(ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1)
    assert summary["gate_statuses_valid"] is True
    assert summary["all_authority_flags_false"] is True
    assert "raw prompt" not in repr(summary).lower()
    assert "final answer:" not in repr(summary).lower()


def test_renderer_output_contains_safe_internal_markdown_only():
    rendered = render_answer_composition_authority_artifact_markdown_v1(safe_artifact())
    assert rendered.startswith("# WESLR Answer Composition Authority Artifact V1")
    assert "metadata evidence is not answer text" in rendered
    assert "answer composition: `not_authorized`" in rendered
    assert "final answer generation: `not_authorized`" in rendered
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
    artifact = safe_artifact()
    secret = "raw prompt: DO NOT LEAK THIS"
    artifact["unsafe"] = secret
    rendered = render_answer_composition_authority_artifact_markdown_v1(artifact)
    assert "Blocked" in rendered
    assert "raw_content_detected" in rendered
    assert "DO NOT LEAK THIS" not in rendered
    assert secret not in rendered


def test_json_safe_returns_deep_copy_for_valid_artifact():
    artifact = safe_artifact()
    result = to_answer_composition_authority_artifact_json_safe_v1(artifact)
    assert result == artifact
    assert result is not artifact
    result["source_metadata_types"].append("mutated")
    assert "mutated" not in artifact["source_metadata_types"]


def test_json_safe_invalid_wrapper_does_not_silently_sanitize_into_valid_artifact():
    artifact = safe_artifact()
    artifact["unsafe"] = "provider output: DO NOT LEAK THIS"
    result = to_answer_composition_authority_artifact_json_safe_v1(artifact)
    assert result["artifact_type"] == "answer_composition_authority_artifact_v1_invalid"
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
    first = safe_artifact()
    second = safe_artifact()
    assert first == second
    assert validate_answer_composition_authority_artifact_v1(first) == validate_answer_composition_authority_artifact_v1(second)
    assert summarize_answer_composition_authority_artifact_v1(first) == summarize_answer_composition_authority_artifact_v1(second)
    assert render_answer_composition_authority_artifact_markdown_v1(first) == render_answer_composition_authority_artifact_markdown_v1(second)


def test_builder_accepts_tuple_and_set_inputs_deterministically():
    artifact = build_answer_composition_authority_artifact_v1(
        source_metadata_types=("behavior_evaluation_report_metadata",),
        composition_review_dimensions={"b", "a"},
        allowed_review_labels=("metadata_evidence_useful_for_review",),
    )
    assert artifact["source_metadata_types"] == ["behavior_evaluation_report_metadata"]
    assert artifact["composition_review_dimensions"] == ["a", "b"]


def test_non_mapping_artifact_is_blocked():
    validation = validate_answer_composition_authority_artifact_v1(["not", "mapping"])  # type: ignore[arg-type]
    assert validation["valid"] is False
    assert "artifact_not_mapping" in validation["errors"]


def test_invalid_schema_and_artifact_type_are_blocked():
    artifact = safe_artifact()
    artifact["artifact_type"] = "wrong"
    artifact["schema_version"] = "wrong"
    validation = assert_blocked(artifact)
    assert "artifact_type_invalid" in validation["errors"]
    assert "schema_version_invalid" in validation["errors"]


def test_no_file_write_provider_subprocess_network_runtime_references_in_module_source():
    source = inspect.getsource(composition)
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
    artifact = safe_artifact()
    assert validate_answer_composition_authority_artifact_v1(artifact)["valid"] is True
    assert summarize_answer_composition_authority_artifact_v1(artifact)["valid"] is True
    assert "metadata evidence is not answer text" in render_answer_composition_authority_artifact_markdown_v1(artifact)
    assert to_answer_composition_authority_artifact_json_safe_v1(artifact)["artifact_type"] == composition.ARTIFACT_TYPE_V1


def test_no_mutation_during_validation_summary_render_or_json_safe_invalid():
    artifact = safe_artifact()
    artifact["unsafe"] = "raw response: no leak"
    before = copy.deepcopy(artifact)
    validate_answer_composition_authority_artifact_v1(artifact)
    summarize_answer_composition_authority_artifact_v1(artifact)
    render_answer_composition_authority_artifact_markdown_v1(artifact)
    to_answer_composition_authority_artifact_json_safe_v1(artifact)
    assert artifact == before


def test_renderer_blocks_non_mapping_without_traceback():
    rendered = render_answer_composition_authority_artifact_markdown_v1(["bad"])  # type: ignore[arg-type]
    assert "Blocked" in rendered
    assert "artifact_not_mapping" in rendered


def test_json_safe_blocks_non_mapping_without_traceback():
    result = to_answer_composition_authority_artifact_json_safe_v1(["bad"])  # type: ignore[arg-type]
    assert result["valid"] is False
    assert result["blocked"] is True
    assert "artifact_not_mapping" in result["errors"]


def test_valid_artifact_contains_no_raw_prompt_response_private_provider_or_final_answer_text_fields():
    artifact = safe_artifact()
    serialized = repr(artifact).lower()
    forbidden = [
        "raw_prompt_text",
        "raw_response_text",
        "private_content",
        "hidden_prompt",
        "answer_key",
        "provider_output",
        "official_score",
        "final_answer_text",
        "final_answer_prose",
    ]
    for marker in forbidden:
        assert marker not in serialized


def test_next_lane_is_review_not_runtime():
    summary = summarize_answer_composition_authority_artifact_v1(safe_artifact())
    assert summary["next_lane_recommendation"] == "REVIEW_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_V1"
    assert "RUNTIME" not in summary["next_lane_recommendation"]
