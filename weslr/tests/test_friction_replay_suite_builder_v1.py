from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

from weslr.friction_pattern_miner import build_initial_renderer_friction_patterns_v1
from weslr.friction_replay_suite_builder import (
    FrictionReplaySuite,
    FrictionReplaySuiteCase,
    FrictionReplaySuitePacket,
    ValidationError,
    build_friction_replay_suite_case_v1,
    build_friction_replay_suite_packet_v1,
    build_friction_replay_suite_v1,
    build_initial_renderer_friction_replay_suites_v1,
    build_replay_suite_from_pattern_v1,
    build_replay_suites_from_pattern_packet_v1,
    summarize_friction_replay_suite_packet_v1,
    to_friction_replay_suite_json_safe_v1,
    validate_friction_replay_suite_case_v1,
    validate_friction_replay_suite_packet_v1,
    validate_friction_replay_suite_v1,
)

MODULE_NAME = "weslr.friction_replay_suite_builder"
MODULE_PATH = Path(__file__).resolve().parents[1] / "friction_replay_suite_builder.py"


def _module():
    return importlib.import_module(MODULE_NAME)


def _base_case(**overrides):
    payload = {
        "suite_case_id": "identity_status_directness_replay_suite__original_friction__what_is_weslr_identity_friction",
        "source_pattern_id": "identity_status_directness_pattern",
        "case_kind": "original_friction",
        "safe_prompt_descriptor": "what is weslr identity friction",
        "prompt_labels": ["what is weslr", "identity", "status"],
        "expected_render_mode": "direct_bounded",
        "expected_method_id": "verified_identity_status_answer_v1",
        "expected_shape_id": "direct_bounded_answer",
        "expected_case_id": "identity_self_description_case",
        "expected_route_id": "identity_status_route",
        "expected_boundary_behavior": "direct identity/status without AGI or consciousness overclaim.",
        "risk_labels": ["overclaim_risk", "identity_directness_drift"],
        "regression_labels": ["clarification_drift", "overclaim_drift"],
        "raw_prompt_stored": False,
        "raw_answer_stored": False,
        "safe_metadata": {"source": "unit_test"},
    }
    payload.update(overrides)
    return build_friction_replay_suite_case_v1(**payload)


def _identity_suite():
    return next(item for item in build_initial_renderer_friction_replay_suites_v1() if item.source_pattern_id == "identity_status_directness_pattern")


def _capability_suite():
    return next(item for item in build_initial_renderer_friction_replay_suites_v1() if item.source_pattern_id == "capability_orientation_directness_pattern")


def _unknown_suite():
    return next(item for item in build_initial_renderer_friction_replay_suites_v1() if item.source_pattern_id == "unknown_term_friction_preference_pattern")


def _inactive_suite():
    return next(item for item in build_initial_renderer_friction_replay_suites_v1() if item.source_pattern_id == "inactive_capability_boundary_pattern")


def test_01_module_imports_safely() -> None:
    module = _module()
    assert hasattr(module, "build_friction_replay_suite_v1")
    assert hasattr(module, "build_initial_renderer_friction_replay_suites_v1")


def test_02_builds_deterministic_suite_case() -> None:
    case_one = _base_case()
    case_two = _base_case()
    assert case_one == case_two


def test_03_builds_deterministic_suite() -> None:
    pattern = build_initial_renderer_friction_patterns_v1()[0]
    suite_one = build_replay_suite_from_pattern_v1(pattern)
    suite_two = build_replay_suite_from_pattern_v1(pattern)
    assert suite_one == suite_two


def test_04_validates_normal_suite_case() -> None:
    assert validate_friction_replay_suite_case_v1(_base_case()) is True


def test_05_validates_normal_suite() -> None:
    suite = build_replay_suite_from_pattern_v1(build_initial_renderer_friction_patterns_v1()[0])
    assert validate_friction_replay_suite_v1(suite) is True


def test_06_validates_normal_suite_packet() -> None:
    packet = build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1())
    assert isinstance(packet, FrictionReplaySuitePacket)
    assert validate_friction_replay_suite_packet_v1(packet) is True


def test_07_json_safe_export_works() -> None:
    case = _base_case()
    safe = to_friction_replay_suite_json_safe_v1(case)
    assert safe["suite_case_id"] == case.suite_case_id
    assert isinstance(safe["prompt_labels"], list)


def test_08_summary_includes_suite_counts_and_case_kind_counts() -> None:
    packet = build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1())
    summary = summarize_friction_replay_suite_packet_v1(packet)
    assert summary["suite_count"] == 4
    assert summary["case_kind_counts"]["original_friction"] == 4
    assert summary["case_kind_counts"]["neighbor_prompt"] >= 12


def test_09_initial_renderer_suites_exist() -> None:
    suites = build_initial_renderer_friction_replay_suites_v1()
    assert len(suites) == 4


def test_10_identity_suite_exists() -> None:
    suite = _identity_suite()
    assert suite.source_pattern_id == "identity_status_directness_pattern"


def test_11_capability_suite_exists() -> None:
    suite = _capability_suite()
    assert suite.source_pattern_id == "capability_orientation_directness_pattern"


def test_12_unknown_term_suite_exists() -> None:
    suite = _unknown_suite()
    assert suite.source_pattern_id == "unknown_term_friction_preference_pattern"


def test_13_inactive_capability_boundary_suite_exists() -> None:
    suite = _inactive_suite()
    assert suite.source_pattern_id == "inactive_capability_boundary_pattern"


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_14_each_initial_suite_has_original_friction_case(suite) -> None:
    assert any(case.case_kind == "original_friction" for case in suite.suite_cases)


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_15_each_initial_suite_has_neighbor_or_paraphrase_case(suite) -> None:
    assert any(case.case_kind in {"neighbor_prompt", "paraphrase_label"} for case in suite.suite_cases)


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_16_each_initial_suite_has_boundary_regression_or_overclaim_case(suite) -> None:
    assert any(case.case_kind in {"boundary_prompt", "regression_prompt", "overclaim_prompt", "unrelated_control"} for case in suite.suite_cases)


def test_17_identity_suite_contains_agi_conscious_turing_boundary_labels() -> None:
    suite = _identity_suite()
    labels = " ".join(" ".join(case.prompt_labels) for case in suite.suite_cases).lower()
    assert "agi" in labels
    assert "conscious" in labels
    assert "turing" in labels


def test_18_capability_suite_contains_public_pilot_provider_memory_boundary_labels() -> None:
    suite = _capability_suite()
    labels = " ".join(" ".join(case.prompt_labels) for case in suite.suite_cases).lower()
    assert "public pilot" in labels
    assert "provider" in labels
    assert "memory" in labels


def test_19_unknown_suite_contains_unrelated_controls() -> None:
    suite = _unknown_suite()
    kinds = {case.case_kind for case in suite.suite_cases}
    assert "unrelated_control" in kinds


def test_20_inactive_capability_suite_contains_upload_payment_marketplace_register_labels() -> None:
    suite = _inactive_suite()
    labels = " ".join(" ".join(case.prompt_labels) for case in suite.suite_cases).lower()
    assert "upload" in labels
    assert "pay" in labels
    assert "marketplace" in labels
    assert "register" in labels


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_21_no_suite_claims_learning(suite) -> None:
    assert suite.learning_claimed is False


def test_22_no_suite_creates_proposal() -> None:
    packet = build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1())
    assert packet.proposal_created is False


def test_23_no_suite_performs_promotion() -> None:
    packet = build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1())
    assert packet.promotion_performed is False


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_24_no_suite_has_runtime_authority(suite) -> None:
    assert suite.runtime_authority is False


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_25_no_suite_writes_state(suite) -> None:
    assert suite.writes_state is False


@pytest.mark.parametrize("suite", build_initial_renderer_friction_replay_suites_v1())
def test_26_no_suite_uses_model_provider(suite) -> None:
    assert suite.model_provider_used is False


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("raw_transcript", "secret transcript"),
    ],
)
def test_27_raw_prompt_field_fails_validation(field_name, value) -> None:
    payload = to_friction_replay_suite_json_safe_v1(_base_case())
    payload[field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_case_v1(payload)


@pytest.mark.parametrize("field_name", ["raw_prompt_stored", "raw_answer_stored"])
def test_28_raw_answer_field_fails_validation(field_name) -> None:
    payload = to_friction_replay_suite_json_safe_v1(_base_case())
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_case_v1(payload)


@pytest.mark.parametrize("field_name", ["transcript", "transcript_text"])
def test_29_transcript_field_fails_validation(field_name) -> None:
    payload = to_friction_replay_suite_json_safe_v1(_base_case())
    payload[field_name] = "secret transcript"
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_case_v1(payload)


def test_30_unknown_case_kind_fails_validation() -> None:
    payload = to_friction_replay_suite_json_safe_v1(_base_case())
    payload["case_kind"] = "unknown_case_kind"
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_case_v1(payload)


def test_31_duplicate_suite_ids_fail_packet_validation() -> None:
    packet = to_friction_replay_suite_json_safe_v1(build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1()))
    packet["suites"][1]["suite_id"] = packet["suites"][0]["suite_id"]
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_packet_v1(packet)


def test_32_duplicate_suite_case_ids_fail_packet_validation() -> None:
    packet = to_friction_replay_suite_json_safe_v1(build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1()))
    packet["suites"][0]["suite_cases"][1]["suite_case_id"] = packet["suites"][0]["suite_cases"][0]["suite_case_id"]
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_packet_v1(packet)


def test_33_count_mismatch_fails_validation() -> None:
    packet = to_friction_replay_suite_json_safe_v1(build_friction_replay_suite_packet_v1(build_initial_renderer_friction_replay_suites_v1()))
    packet["suite_count"] += 1
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_packet_v1(packet)


def test_34_missing_original_friction_case_fails_validation() -> None:
    suite = to_friction_replay_suite_json_safe_v1(_identity_suite())
    suite["suite_cases"] = [case for case in suite["suite_cases"] if case["case_kind"] != "original_friction"]
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_v1(suite)


def test_35_missing_neighbor_paraphrase_case_fails_validation() -> None:
    suite = to_friction_replay_suite_json_safe_v1(_identity_suite())
    suite["suite_cases"] = [case for case in suite["suite_cases"] if case["case_kind"] == "original_friction" or case["case_kind"] in {"boundary_prompt", "overclaim_prompt"}]
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_v1(suite)


def test_36_missing_boundary_regression_overclaim_case_fails_validation() -> None:
    suite = to_friction_replay_suite_json_safe_v1(_identity_suite())
    suite["suite_cases"] = [case for case in suite["suite_cases"] if case["case_kind"] in {"original_friction", "neighbor_prompt"}]
    with pytest.raises(ValidationError):
        validate_friction_replay_suite_v1(suite)


def test_37_build_from_initial_pattern_packet_is_deterministic() -> None:
    pattern_packet = build_initial_renderer_friction_patterns_v1()
    one = build_replay_suites_from_pattern_packet_v1(pattern_packet)
    two = build_replay_suites_from_pattern_packet_v1(pattern_packet)
    assert one == two


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_38_to_41_module_does_not_import_or_call_prohibited_modules(module_name: str) -> None:
    module = _module()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                called_names.add(func.attr)
    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
    assert module_name not in called_names
