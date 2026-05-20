from __future__ import annotations

import copy
import inspect
from pathlib import Path

import pytest

from weslr.answer_authority_boundary import (
    ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1,
    ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1,
    ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1,
    ANSWER_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1,
    ANSWER_AUTHORITY_MINOR_RISKS_V1,
    ANSWER_AUTHORITY_READINESS_LABELS_V1,
    ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1,
    build_answer_authority_boundary_artifact_v1,
    render_answer_authority_boundary_artifact_markdown_v1,
    summarize_answer_authority_boundary_artifact_v1,
    to_answer_authority_boundary_artifact_json_safe_v1,
    validate_answer_authority_boundary_artifact_v1,
)
import weslr.answer_authority_boundary as boundary


def safe_artifact() -> dict:
    return build_answer_authority_boundary_artifact_v1(
        source_metadata_types=list(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        covered_dimensions=["scenario_coverage", "governance_boundary", "evidence_boundary"],
        covered_failure_modes=["authority_overreach", "runtime_overreach", "official_claim_overreach"],
        allowed_inferences=list(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1),
    )


def assert_blocked(artifact: dict, expected_key: str | None = None) -> dict:
    validation = validate_answer_authority_boundary_artifact_v1(artifact)
    assert validation["valid"] is False
    assert validation["blocked"] is True
    if expected_key:
        joined = "\n".join(validation["errors"])
        assert expected_key in joined or validation.get(expected_key) is True
    return validation


def test_module_imports_without_side_effects():
    assert boundary.ARTIFACT_TYPE_V1 == "answer_authority_boundary_artifact_v1"


@pytest.mark.parametrize("label", [
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
    assert label in ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1


@pytest.mark.parametrize("label", [
    "scenario_coverage_visible",
    "multi_turn_dimension_coverage_visible",
    "failure_taxonomy_visible",
    "governance_boundary_visible",
    "evidence_boundary_visible",
    "provenance_boundary_visible",
    "memory_boundary_visible",
    "uncertainty_honesty_expected",
    "non_cannedness_expected",
    "final_answer_authority_risk_visible",
    "runtime_authority_risk_visible",
    "occ_openclaw_identity_boundary_visible",
    "readiness_gap_visible",
])
def test_constants_include_allowed_inference_labels(label):
    assert label in ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1


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
])
def test_constants_include_forbidden_inference_labels(label):
    assert label in ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1


@pytest.mark.parametrize("label", [
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_authority",
    "candidate_metadata_not_answer_text",
    "evaluation_metadata_not_response_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "governance_review_required",
    "evidence_sufficiency_not_established",
    "official_claim_not_allowed",
    "runtime_wiring_requires_separate_approval",
    "final_answer_composition_requires_separate_design",
])
def test_constants_include_required_boundary_labels(label):
    assert label in ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1


@pytest.mark.parametrize("label", [
    "ready_for_runtime",
    "passed_turing_test",
    "officially_intelligent",
    "certified",
    "human_level",
    "conscious",
    "sentient",
    "production_ready",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
])
def test_constants_include_forbidden_label_drift(label):
    assert label in ANSWER_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1


@pytest.mark.parametrize("label", [
    "validator_phrase_key_limitation",
    "renderer_next_lane_wording_drift",
    "Turing-name overclaim risk",
    "future label non-scoring discipline",
    "metadata-overread risk",
    "boundary-label drift risk",
    "helper/report-as-judge risk",
    "helper/report-as-score risk",
])
def test_constants_include_minor_risks(label):
    assert label in ANSWER_AUTHORITY_MINOR_RISKS_V1


@pytest.mark.parametrize("label", [
    "answer_authority_boundary_helpers_implemented",
    "metadata_evidence_not_answer_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "internal_only_non_official",
    "qualitative_first",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
])
def test_constants_include_readiness_labels(label):
    assert label in ANSWER_AUTHORITY_READINESS_LABELS_V1


def test_artifact_builder_creates_required_fields():
    artifact = safe_artifact()
    for field in (
        "artifact_type", "source_metadata_types", "covered_dimensions", "covered_failure_modes",
        "authority_boundary_labels", "allowed_inferences", "forbidden_inferences",
        "governance_required", "evidence_sufficiency_status", "minor_risks",
        "readiness_labels", "schema_version", "metadata_only", "internal_only",
        "answer_authority_granted", "runtime_authority_granted", "final_answer_generated",
        "official_claim_allowed", "prompt_execution_allowed", "raw_content_allowed",
        "answer_composition_authorized", "judge_authority_granted", "scoring_authorized",
        "model_call_made", "search_call_made", "advisor_call_made",
        "dot_weslr_write_performed", "feature_flag_enabled",
    ):
        assert field in artifact


@pytest.mark.parametrize("flag", [
    "answer_authority_granted",
    "runtime_authority_granted",
    "final_answer_generated",
    "official_claim_allowed",
    "prompt_execution_allowed",
    "raw_content_allowed",
    "answer_composition_authorized",
    "judge_authority_granted",
    "scoring_authorized",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
])
def test_artifact_builder_sets_all_authority_runtime_prompt_final_flags_false(flag):
    assert safe_artifact()[flag] is False


def test_artifact_builder_includes_all_forbidden_inference_labels_by_default():
    artifact = build_answer_authority_boundary_artifact_v1(
        source_metadata_types=list(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        allowed_inferences=list(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1),
    )
    assert set(ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1).issubset(set(artifact["forbidden_inferences"]))


def test_artifact_builder_includes_required_boundary_labels_by_default():
    artifact = build_answer_authority_boundary_artifact_v1(
        source_metadata_types=list(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        allowed_inferences=list(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1),
    )
    assert set(ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1).issubset(set(artifact["authority_boundary_labels"]))


def test_validator_accepts_safe_artifact():
    validation = validate_answer_authority_boundary_artifact_v1(safe_artifact())
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["safety_booleans_valid"] is True


def test_validator_rejects_missing_required_field():
    artifact = safe_artifact()
    artifact.pop("artifact_type")
    assert_blocked(artifact, "missing_required_field:artifact_type")


def test_validator_rejects_unknown_source_metadata_type():
    artifact = safe_artifact()
    artifact["source_metadata_types"] = ["unknown_metadata"]
    validation = assert_blocked(artifact, "unknown_source_metadata_types")
    assert validation["unknown_source_metadata_types"] == ["unknown_metadata"]


def test_validator_rejects_unknown_allowed_inference():
    artifact = safe_artifact()
    artifact["allowed_inferences"] = ["scenario_coverage_visible", "unknown_allowed"]
    validation = assert_blocked(artifact, "unknown_allowed_inferences")
    assert validation["unknown_allowed_inferences"] == ["unknown_allowed"]


def test_validator_rejects_missing_forbidden_inference_label():
    artifact = safe_artifact()
    artifact["forbidden_inferences"] = list(ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1[:-1])
    validation = assert_blocked(artifact, "missing_forbidden_inferences")
    assert "final_answer_authorized" in validation["missing_forbidden_inferences"]


def test_validator_rejects_forbidden_inference_appearing_as_allowed():
    artifact = safe_artifact()
    artifact["allowed_inferences"] = ["scenario_coverage_visible", "final_answer_authorized"]
    validation = assert_blocked(artifact, "forbidden_as_allowed")
    assert "final_answer_authorized" in validation["forbidden_as_allowed"]


def test_validator_rejects_missing_required_boundary_label():
    artifact = safe_artifact()
    artifact["authority_boundary_labels"] = [
        label for label in ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1
        if label != "metadata_evidence_not_answer_authority"
    ]
    validation = assert_blocked(artifact, "missing_boundary_labels")
    assert "metadata_evidence_not_answer_authority" in validation["missing_boundary_labels"]


@pytest.mark.parametrize("flag, expected", [
    ("answer_authority_granted", "answer_authority_detected"),
    ("runtime_authority_granted", "runtime_authority_detected"),
    ("final_answer_generated", "final_answer_detected"),
    ("official_claim_allowed", "official_claim_detected"),
    ("prompt_execution_allowed", "prompt_execution_detected"),
    ("raw_content_allowed", "raw_content_detected"),
    ("answer_composition_authorized", "unsafe_true_or_missing_flag"),
    ("judge_authority_granted", "judge_or_score_detected"),
    ("scoring_authorized", "judge_or_score_detected"),
    ("model_call_made", "unsafe_true_or_missing_flag"),
    ("search_call_made", "unsafe_true_or_missing_flag"),
    ("advisor_call_made", "unsafe_true_or_missing_flag"),
    ("dot_weslr_write_performed", "unsafe_true_or_missing_flag"),
    ("feature_flag_enabled", "unsafe_true_or_missing_flag"),
])
def test_validator_rejects_unsafe_true_flags(flag, expected):
    artifact = safe_artifact()
    artifact[flag] = True
    assert_blocked(artifact, expected)


@pytest.mark.parametrize("key, value, expected", [
    ("raw_prompt", "synthetic raw prompt text", "raw_content_detected"),
    ("raw_response", "synthetic raw response text", "raw_content_detected"),
    ("final_answer_text", "synthetic final answer text", "final_answer_detected"),
    ("private_content", "private content: synthetic secret", "private_content_detected"),
    ("hidden_prompt", "hidden prompt: synthetic", "hidden_prompt_detected"),
    ("answer_key", "answer key: synthetic", "answer_key_detected"),
    ("provider_output", "provider output: synthetic", "provider_output_detected"),
    ("official_score", "official score: 100", "judge_or_score_detected"),
])
def test_validator_rejects_unsafe_keys_and_content_markers(key, value, expected):
    artifact = safe_artifact()
    artifact[key] = value
    assert_blocked(artifact, expected)


@pytest.mark.parametrize("marker, expected", [
    ("official turing pass", "official_claim_detected"),
    ("passed the turing test", "official_claim_detected"),
    ("official iq", "official_claim_detected"),
    ("iq score", "official_claim_detected"),
    ("certification claim", "official_claim_detected"),
    ("product readiness certified", "official_claim_detected"),
    ("weslr is conscious", "consciousness_claim_detected"),
    ("weslr is sentient", "consciousness_claim_detected"),
    ("occ is weslr", "identity_confusion_detected"),
    ("openclaw is weslr", "identity_confusion_detected"),
    ("execute prompt", "prompt_execution_detected"),
    ("live dialogue", "live_dialogue_detected"),
    ("model_call_made=true", "provider_call_detected"),
    ("search_call_made=true", "provider_call_detected"),
    ("advisor_call_made=true", "provider_call_detected"),
    (".weslr write", "dot_weslr_write_detected"),
    ("feature_flag_enabled=true", "feature_flag_detected"),
    ("scoring engine", "judge_or_score_detected"),
    ("judge authority", "judge_or_score_detected"),
])
def test_validator_rejects_forbidden_text_markers(marker, expected):
    artifact = safe_artifact()
    artifact["unsafe_note"] = marker
    assert_blocked(artifact, expected)


@pytest.mark.parametrize("label", ANSWER_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1)
def test_validator_rejects_forbidden_label_drift(label):
    artifact = safe_artifact()
    artifact["readiness_labels"] = list(ANSWER_AUTHORITY_READINESS_LABELS_V1) + [label]
    assert_blocked(artifact, "forbidden_label_drift")


def test_summary_includes_artifact_type_and_validity():
    summary = summarize_answer_authority_boundary_artifact_v1(safe_artifact())
    assert summary["artifact_type"] == "answer_authority_boundary_artifact_v1"
    assert summary["valid"] is True
    assert summary["blocked"] is False


def test_summary_includes_source_metadata_count():
    assert summarize_answer_authority_boundary_artifact_v1(safe_artifact())["source_metadata_type_count"] == len(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1)


def test_summary_includes_covered_dimension_count():
    assert summarize_answer_authority_boundary_artifact_v1(safe_artifact())["covered_dimension_count"] == 3


def test_summary_includes_covered_failure_mode_count():
    assert summarize_answer_authority_boundary_artifact_v1(safe_artifact())["covered_failure_mode_count"] == 3


def test_summary_includes_allowed_and_forbidden_inference_counts():
    summary = summarize_answer_authority_boundary_artifact_v1(safe_artifact())
    assert summary["allowed_inference_count"] == len(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1)
    assert summary["forbidden_inference_count"] == len(ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1)


def test_summary_includes_boundary_labels():
    summary = summarize_answer_authority_boundary_artifact_v1(safe_artifact())
    assert set(ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1).issubset(set(summary["authority_boundary_labels"]))


def test_summary_includes_governance_and_evidence_status():
    summary = summarize_answer_authority_boundary_artifact_v1(safe_artifact())
    assert summary["governance_required"] is True
    assert summary["evidence_sufficiency_status"] == "evidence_sufficiency_not_established"


def test_summary_includes_false_authority_flag_status():
    assert summarize_answer_authority_boundary_artifact_v1(safe_artifact())["all_authority_flags_false"] is True


def test_summary_includes_readiness_labels():
    assert "qualitative_first" in summarize_answer_authority_boundary_artifact_v1(safe_artifact())["readiness_labels"]


def test_summary_includes_minor_risks():
    assert "metadata-overread risk" in summarize_answer_authority_boundary_artifact_v1(safe_artifact())["minor_risks"]


def test_summary_excludes_raw_final_private_provider_content():
    summary_text = repr(summarize_answer_authority_boundary_artifact_v1(safe_artifact())).lower()
    assert "raw prompt:" not in summary_text
    assert "raw response:" not in summary_text
    assert "final answer:" not in summary_text
    assert "private content:" not in summary_text
    assert "provider output:" not in summary_text


def test_renderer_includes_artifact_status():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "## Artifact status" in rendered
    assert "answer_authority_boundary_artifact_v1" in rendered


def test_renderer_includes_validation_status():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "## Validation status" in rendered
    assert "valid: `True`" in rendered


def test_renderer_includes_source_metadata_count():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "source_metadata_type_count" in rendered


def test_renderer_includes_boundary_labels():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "metadata_evidence_not_answer_authority" in rendered


def test_renderer_includes_false_authority_flag_summary():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "False authority flag summary" in rendered
    assert "all_authority_flags_false: `True`" in rendered


def test_renderer_includes_minor_risks():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "metadata-overread risk" in rendered


def test_renderer_includes_safety_confirmation():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    assert "## Safety confirmation" in rendered
    assert "metadata evidence is not answer authority" in rendered


def test_renderer_blocks_invalid_artifact_without_leaking_offending_content():
    artifact = safe_artifact()
    artifact["raw_prompt"] = "raw prompt: DO_NOT_LEAK_SYNTHETIC"
    rendered = render_answer_authority_boundary_artifact_markdown_v1(artifact)
    assert "blocked_invalid_artifact" in rendered
    assert "DO_NOT_LEAK_SYNTHETIC" not in rendered
    assert "raw prompt: DO_NOT_LEAK" not in rendered


def test_renderer_omits_raw_final_private_provider_content():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact()).lower()
    assert "raw prompt:" not in rendered
    assert "raw response:" not in rendered
    assert "final answer:" not in rendered
    assert "private content:" not in rendered
    assert "provider output:" not in rendered
    assert "official score:" not in rendered


def test_json_safe_copy_returns_safe_copy_for_valid_artifact():
    artifact = safe_artifact()
    copied = to_answer_authority_boundary_artifact_json_safe_v1(artifact)
    assert copied == artifact
    assert copied is not artifact


def test_json_safe_copy_returns_invalid_wrapper_for_unsafe_artifact():
    artifact = safe_artifact()
    artifact["answer_authority_granted"] = True
    copied = to_answer_authority_boundary_artifact_json_safe_v1(artifact)
    assert copied["invalid_wrapper"] is True
    assert copied["valid"] is False
    assert "answer_authority_granted" not in repr(copied.get("reason_labels", []))


def test_helpers_are_deterministic_for_same_artifact():
    artifact = safe_artifact()
    assert build_answer_authority_boundary_artifact_v1(
        source_metadata_types=list(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1),
        covered_dimensions=["scenario_coverage", "governance_boundary", "evidence_boundary"],
        covered_failure_modes=["authority_overreach", "runtime_overreach", "official_claim_overreach"],
        allowed_inferences=list(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1),
    ) == artifact
    assert validate_answer_authority_boundary_artifact_v1(artifact) == validate_answer_authority_boundary_artifact_v1(copy.deepcopy(artifact))
    assert render_answer_authority_boundary_artifact_markdown_v1(artifact) == render_answer_authority_boundary_artifact_markdown_v1(copy.deepcopy(artifact))


def test_no_helper_writes_files(tmp_path):
    before = set(tmp_path.iterdir())
    artifact = safe_artifact()
    validate_answer_authority_boundary_artifact_v1(artifact)
    summarize_answer_authority_boundary_artifact_v1(artifact)
    render_answer_authority_boundary_artifact_markdown_v1(artifact)
    to_answer_authority_boundary_artifact_json_safe_v1(artifact)
    after = set(tmp_path.iterdir())
    assert before == after


def test_no_helper_calls_network_subprocess_model_search_advisor():
    source = Path(inspect.getsourcefile(boundary)).read_text()
    assert "import subprocess" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "model_call(" not in source
    assert "search_call(" not in source
    assert "advisor_call(" not in source


def test_no_chatresponder_respond_chat_generate_chat_calls():
    source = Path(inspect.getsourcefile(boundary)).read_text()
    assert "ChatResponder" not in source
    assert "respond_chat(" not in source
    assert "generate_chat(" not in source


def test_no_official_claims_are_made_by_valid_renderer():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact()).lower()
    assert "passed the turing test" not in rendered
    assert "official benchmark" not in rendered
    assert "certified product-ready" not in rendered
    assert "product readiness certified" not in rendered


def test_no_runtime_ready_declaration_is_rendered():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact()).lower()
    assert "ready_for_runtime" not in rendered
    assert "runtime-ready" not in rendered
    assert "production_ready" not in rendered


def test_no_prompts_are_executable():
    artifact = safe_artifact()
    assert artifact["prompt_execution_allowed"] is False
    assert "prompt_execution_not_authorized" in artifact["authority_boundary_labels"]


def test_no_live_dialogue_is_created():
    assert "live_dialogue_authorized" in safe_artifact()["forbidden_inferences"]


def test_no_final_answers_are_generated():
    assert safe_artifact()["final_answer_generated"] is False


def test_no_answer_composition_is_authorized():
    assert safe_artifact()["answer_composition_authorized"] is False


def test_no_answer_authority_is_granted():
    assert safe_artifact()["answer_authority_granted"] is False


def test_no_dot_weslr_writes_occur():
    assert safe_artifact()["dot_weslr_write_performed"] is False


def test_minor_risks_remain_visible():
    artifact = safe_artifact()
    assert set(ANSWER_AUTHORITY_MINOR_RISKS_V1).issubset(set(artifact["minor_risks"]))
    assert "metadata-overread risk" in render_answer_authority_boundary_artifact_markdown_v1(artifact)


def test_forbidden_inference_labels_remain_visible_as_denied_paths():
    artifact = safe_artifact()
    assert "final_answer_authorized" in artifact["forbidden_inferences"]
    assert "prompt_execution_authorized" in artifact["forbidden_inferences"]


def test_boundary_labels_are_qualitative_only():
    labels = safe_artifact()["authority_boundary_labels"]
    assert all("score" not in label for label in labels)
    assert all("passed" not in label for label in labels)


def test_readiness_labels_are_qualitative_only():
    labels = safe_artifact()["readiness_labels"]
    assert all("score" not in label for label in labels)
    assert all("passed" not in label for label in labels)
    assert all("certified" not in label for label in labels)


def test_next_lane_recommendation_avoids_runtime_wiring_and_answer_composition():
    rendered = render_answer_authority_boundary_artifact_markdown_v1(safe_artifact())
    next_lane = rendered.split("## Next lane recommendation", 1)[1]
    assert "RUNTIME" not in next_lane
    assert "ANSWER_COMPOSITION" not in next_lane
    assert "AUTHORITY" not in next_lane.replace("METADATA_BOUNDARY", "")


def test_validation_result_exposes_required_output_fields():
    validation = validate_answer_authority_boundary_artifact_v1(safe_artifact())
    for key in (
        "valid", "blocked", "errors", "warnings", "artifact_type", "safety_booleans_valid",
        "unknown_source_metadata_types", "unknown_allowed_inferences", "missing_forbidden_inferences",
        "forbidden_as_allowed", "missing_boundary_labels", "raw_content_detected",
        "final_answer_detected", "answer_authority_detected", "runtime_authority_detected",
        "prompt_execution_detected", "official_claim_detected", "judge_or_score_detected",
    ):
        assert key in validation
