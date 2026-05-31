from __future__ import annotations

import ast
import importlib
import inspect

import pytest

from weslr.friction_case_capture import (
    ALLOWED_APPROVAL_STATUSES_V1,
    ALLOWED_CASE_TYPES_V1,
    ALLOWED_MISMATCH_LABELS_V1,
    ALLOWED_PROMOTION_STATUSES_V1,
    ALLOWED_PROPOSED_UPDATE_AREAS_V1,
    FrictionCaseCapturePacket,
    ValidationError,
    build_friction_case_capture_batch_v1,
    build_friction_case_capture_packet_v1,
    build_friction_case_v1,
    build_initial_renderer_friction_cases_v1,
    capture_friction_case_v1,
    summarize_friction_case_v1,
    summarize_friction_case_capture_packet_v1,
    summarize_friction_case_batch_v1,
    to_friction_case_json_safe_v1,
    validate_friction_case_capture_batch_v1,
    validate_friction_case_capture_packet_v1,
    validate_friction_case_v1,
)


def _base_case(**overrides):
    payload = {
        "case_id": "friction_case_1",
        "case_type": "missing_identity_directness",
        "safe_prompt_descriptor": "what is weslr identity friction",
        "prompt_labels": ["what is weslr", "identity"],
        "actual_render_mode": "clarifying_question",
        "actual_method_id": "clarifying_question_answer_v1",
        "actual_shape_id": "clarifying_question",
        "actual_case_id": "clarification_case",
        "actual_route_id": "clarification_route",
        "expected_render_mode": "direct_bounded",
        "expected_method_id": "verified_identity_status_answer_v1",
        "expected_shape_id": "direct_bounded_answer",
        "expected_case_id": "identity_self_description_case",
        "expected_route_id": "identity_status_route",
        "mismatch_labels": ["answer_shape_mismatch", "too_cautious"],
        "owner_correction": "Answer directly with bounded identity and status.",
        "proposed_update_area": ["response_method_selector", "no_model_bounded_renderer"],
        "replay_labels": ["what weslr", "what are you"],
        "approval_status": "captured_only",
        "promotion_status": "not_promoted",
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "safe_metadata": {"source": "unit_test"},
    }
    payload.update(overrides)
    return build_friction_case_v1(**payload)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.friction_case_capture")
    assert hasattr(module, "build_friction_case_v1")
    assert hasattr(module, "build_initial_renderer_friction_cases_v1")


def test_builds_deterministic_friction_case() -> None:
    case_one = _base_case()
    case_two = _base_case()
    assert case_one == case_two


def test_valid_friction_case_validates() -> None:
    case = _base_case()
    assert validate_friction_case_v1(case) is True


def test_json_safe_export_works() -> None:
    case = _base_case()
    safe = to_friction_case_json_safe_v1(case)
    assert safe["case_id"] == "friction_case_1"
    assert isinstance(safe["actual"], dict)
    assert isinstance(safe["expected"], dict)
    assert safe["safe_metadata"]["source"] == "unit_test"


def test_summary_includes_case_type_mismatch_labels_and_update_area() -> None:
    case = _base_case()
    summary = summarize_friction_case_v1(case)
    assert summary["case_type"] == "missing_identity_directness"
    assert "answer_shape_mismatch" in summary["mismatch_labels"]
    assert "response_method_selector" in summary["proposed_update_area"]


def test_initial_renderer_friction_cases_exist() -> None:
    cases = build_initial_renderer_friction_cases_v1()
    assert len(cases) == 4


def test_identity_friction_has_expected_direct_bounded_identity_route() -> None:
    case = next(item for item in build_initial_renderer_friction_cases_v1() if item.case_id == "what_is_weslr_identity_friction")
    assert case.actual.render_mode == "clarifying_question"
    assert case.expected.render_mode == "direct_bounded"
    assert case.expected.method_id == "verified_identity_status_answer_v1"
    assert case.expected.shape_id == "direct_bounded_answer"
    assert case.expected.case_id == "identity_self_description_case"
    assert case.expected.route_id == "identity_status_route"


def test_capability_friction_has_expected_capability_orientation_route() -> None:
    case = next(item for item in build_initial_renderer_friction_cases_v1() if item.case_id == "what_can_you_do_now_capability_friction")
    assert case.actual.render_mode == "clarifying_question"
    assert case.expected.render_mode == "direct_bounded"
    assert case.expected.method_id == "capability_orientation_answer_v1"
    assert case.expected.shape_id == "direct_bounded_answer"
    assert case.expected.case_id == "capability_orientation_case"
    assert case.expected.route_id == "capability_orientation_route"


def test_unknown_word_friction_has_expected_unknown_route() -> None:
    case = next(item for item in build_initial_renderer_friction_cases_v1() if item.case_id == "unknown_word_blorvatek_friction")
    assert case.actual.render_mode == "clarifying_question"
    assert case.expected.render_mode == "unknown_friction"
    assert case.expected.method_id == "unknown_engine_branch_friction_answer_v1"
    assert case.expected.shape_id == "unknown_friction_branch_answer"
    assert case.expected.case_id == "unknown_word_or_phrase_case"
    assert case.expected.route_id == "unknown_word_phrase_route"


def test_boundary_friction_has_expected_capability_boundary_route() -> None:
    case = next(item for item in build_initial_renderer_friction_cases_v1() if item.case_id == "upload_files_now_boundary_friction")
    assert case.actual.render_mode == "clarifying_question"
    assert case.expected.render_mode == "direct_bounded"
    assert case.expected.method_id == "capability_orientation_answer_v1"
    assert case.expected.shape_id == "direct_bounded_answer"
    assert case.expected.case_id == "capability_orientation_case"
    assert case.expected.route_id == "capability_orientation_route"


@pytest.mark.parametrize("case", build_initial_renderer_friction_cases_v1())
def test_initial_cases_do_not_claim_learning(case) -> None:
    assert case.learning_claimed is False


@pytest.mark.parametrize("case", build_initial_renderer_friction_cases_v1())
def test_initial_cases_are_not_promoted(case) -> None:
    assert case.promotion_status == "not_promoted"


@pytest.mark.parametrize("case", build_initial_renderer_friction_cases_v1())
def test_initial_cases_have_no_runtime_authority(case) -> None:
    assert case.runtime_authority is False


@pytest.mark.parametrize("case", build_initial_renderer_friction_cases_v1())
def test_initial_cases_do_not_write_state(case) -> None:
    assert case.writes_state is False


@pytest.mark.parametrize("case", build_initial_renderer_friction_cases_v1())
def test_initial_cases_do_not_use_model_provider(case) -> None:
    assert case.model_provider_used is False


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("raw_transcript", "secret transcript"),
    ],
)
def test_raw_fields_fail_validation(field_name, value) -> None:
    payload = to_friction_case_json_safe_v1(_base_case())
    payload[field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_case_v1(payload)


@pytest.mark.parametrize("field_name", ["learning_claimed", "runtime_authority", "writes_state", "model_provider_used"])
def test_forbidden_boolean_drift_fails_validation(field_name) -> None:
    payload = to_friction_case_json_safe_v1(_base_case())
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_case_v1(payload)


@pytest.mark.parametrize("field_name, value", [("mismatch_labels", ["unknown_label"]), ("proposed_update_area", ["unknown_area"]), ("approval_status", "unknown_status"), ("promotion_status", "unknown_promotion")])
def test_unknown_enums_fail_validation(field_name, value) -> None:
    payload = to_friction_case_json_safe_v1(_base_case())
    payload[field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_case_v1(payload)


def test_capture_packet_build_and_validate() -> None:
    case = _base_case()
    packet = build_friction_case_capture_packet_v1(case)
    assert isinstance(packet, FrictionCaseCapturePacket)
    assert validate_friction_case_capture_packet_v1(packet) is True
    safe = summarize_friction_case_capture_packet_v1(packet)
    assert safe["case_id"] == "friction_case_1"
    assert safe["case_type"] == "missing_identity_directness"


def test_batch_helper_detects_duplicate_case_ids() -> None:
    case_one = _base_case(case_id="dup_case")
    case_two = _base_case(case_id="dup_case", safe_metadata={"source": "dup"})
    with pytest.raises(ValidationError):
        build_friction_case_capture_batch_v1([case_one, case_two])


def test_batch_summary_counts_case_types_mismatches_and_updates() -> None:
    cases = build_initial_renderer_friction_cases_v1()
    summary = summarize_friction_case_batch_v1(cases)
    assert summary["total_cases"] == 4
    assert summary["case_type_counts"]["missing_identity_directness"] == 1
    assert summary["mismatch_label_counts"]["wrong_case_priority"] >= 2
    assert summary["proposed_update_area_counts"]["response_method_selector"] >= 3


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_module_source_does_not_import_prohibited_modules(module_name) -> None:
    import weslr.friction_case_capture as module

    tree = ast.parse(inspect.getsource(module))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
