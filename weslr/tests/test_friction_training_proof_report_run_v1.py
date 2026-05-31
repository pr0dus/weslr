from __future__ import annotations

import ast
import importlib
import inspect
from functools import lru_cache
from pathlib import Path

import pytest

from weslr.friction_training_proof_report_run import (
    FrictionTrainingProofReport,
    ValidationError,
    build_friction_training_proof_report_v1,
    build_initial_friction_training_proof_report_v1,
    render_friction_training_proof_report_markdown_v1,
    summarize_friction_training_proof_report_v1,
    to_friction_training_proof_report_json_safe_v1,
    validate_friction_training_proof_report_v1,
)

MODULE_NAME = "weslr.friction_training_proof_report_run"
MODULE_PATH = Path(__file__).resolve().parents[1] / "friction_training_proof_report_run.py"

EXPECTED_CASE_IDS = [
    "what_is_weslr_identity_friction",
    "what_can_you_do_now_capability_friction",
    "unknown_word_blorvatek_friction",
    "upload_files_now_boundary_friction",
]
EXPECTED_ALLOWED_CLAIMS = [
    "internal_friction_trained_improvement_proof",
    "replay_proven_governed_improvement",
    "owner_approved_behavior_improvement",
    "metadata_only_proof_report",
]
EXPECTED_FORBIDDEN_CLAIMS = [
    "agi",
    "consciousness",
    "sentience",
    "official_turing_result",
    "certified_intelligence",
    "public_readiness",
    "autonomous_self_modification",
    "unbounded_learning",
]
PROHIBITED_MODULES = ["chat_responder", "main", "dialogue", "chat_ui"]


@lru_cache(maxsize=1)
def _module():
    return importlib.import_module(MODULE_NAME)


@lru_cache(maxsize=1)
def _base_report():
    return build_initial_friction_training_proof_report_v1()


@lru_cache(maxsize=1)
def _json_safe_report():
    return to_friction_training_proof_report_json_safe_v1(_base_report())


@lru_cache(maxsize=1)
def _imports_from_source(module) -> set[str]:
    tree = ast.parse(inspect.getsource(module))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def test_01_module_imports_safely() -> None:
    module = _module()
    assert hasattr(module, "build_friction_training_proof_report_v1")
    assert hasattr(module, "build_initial_friction_training_proof_report_v1")


def test_02_builds_deterministic_proof_report() -> None:
    one = _base_report()
    two = _base_report()
    assert one == two


def test_03_validates_normal_proof_report() -> None:
    assert validate_friction_training_proof_report_v1(_base_report()) is True


def test_04_json_safe_export_works() -> None:
    safe = _json_safe_report()
    assert safe["report_id"] == "WESLR-FR-TRAINING-PROOF-V1"
    assert isinstance(safe["allowed_claims"], list)


def test_05_summary_includes_final_judgment_and_internal_label() -> None:
    summary = summarize_friction_training_proof_report_v1(_base_report())
    assert summary["final_judgment"] == "v101_internal_friction_trained_improvement_proof_valid"
    assert summary["internal_label"] == "WESLR V1.01 internal friction-trained improvement proof"


def test_06_markdown_renderer_includes_internal_only_label() -> None:
    markdown = render_friction_training_proof_report_markdown_v1(_base_report())
    assert "WESLR V1.01 internal friction-trained improvement proof" in markdown


def test_07_report_includes_four_starter_friction_cases() -> None:
    report = _base_report()
    assert report.friction_case_summary["total_cases"] == 4
    assert report.friction_case_summary["case_ids"] == EXPECTED_CASE_IDS


def test_08_report_includes_4_of_4_post_realization_replay_pass_summary() -> None:
    report = _base_report()
    assert report.post_realization_replay_summary["passed_count"] == 4
    assert report.post_realization_replay_summary["case_count"] == 4


def test_09_report_includes_four_pattern_candidates() -> None:
    report = _base_report()
    assert report.pattern_summary["pattern_count"] == 4
    assert report.pattern_summary["confidence_counts"]["single_case_low"] == 4


def test_10_report_includes_four_replay_suites() -> None:
    report = _base_report()
    assert report.replay_suite_summary["suite_count"] == 4


def test_11_report_includes_31_replay_suite_cases() -> None:
    report = _base_report()
    assert report.replay_suite_summary["suite_case_count"] == 31


def test_12_report_includes_anti_hardcoding_summary() -> None:
    report = _base_report()
    assert report.anti_hardcoding_summary["neighbor_prompts_included"] is True
    assert report.anti_hardcoding_summary["boundary_prompts_included"] is True
    assert report.anti_hardcoding_summary["unrelated_controls_included"] is True
    assert report.anti_hardcoding_summary["exact_prompt_only_patch_not_supported"] is True


def test_13_report_includes_boundary_regression_summary() -> None:
    report = _base_report()
    assert report.boundary_regression_summary["agi_overclaim_blocked"] is True
    assert report.boundary_regression_summary["consciousness_overclaim_blocked"] is True
    assert report.boundary_regression_summary["official_turing_claim_blocked"] is True
    assert report.boundary_regression_summary["certification_claim_blocked"] is True
    assert report.boundary_regression_summary["public_readiness_bounded"] is True


def test_14_report_includes_protected_file_summary() -> None:
    report = _base_report()
    assert report.protected_file_summary["selector_renderer_files_untouched"] is True
    assert "weslr/chat_responder.py" in report.protected_file_summary["untouched_files"]
    assert "weslr/main.py" in report.protected_file_summary["untouched_files"]


def test_15_allowed_claims_are_bounded() -> None:
    report = _base_report()
    assert list(report.allowed_claims) == EXPECTED_ALLOWED_CLAIMS


def test_16_forbidden_claims_include_required_bans() -> None:
    report = _base_report()
    assert list(report.forbidden_claims) == EXPECTED_FORBIDDEN_CLAIMS


@pytest.mark.parametrize(
    "field_name",
    [
        "agi_claimed",
        "consciousness_claimed",
        "official_turing_claimed",
        "certification_claimed",
        "public_ready_claimed",
        "autonomous_self_modification_claimed",
    ],
)
def test_17_22_claim_booleans_true_fail_validation(field_name) -> None:
    payload = _json_safe_report()
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_training_proof_report_v1(payload)


@pytest.mark.parametrize("field_name", ["runtime_authority", "writes_state", "model_provider_used"])
def test_23_25_governance_booleans_true_fail_validation(field_name) -> None:
    payload = _json_safe_report()
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_training_proof_report_v1(payload)


@pytest.mark.parametrize(
    "field_name",
    ["raw_prompt", "raw_answer", "transcript"],
)
def test_26_28_raw_fields_fail_validation(field_name) -> None:
    payload = _json_safe_report()
    payload[field_name] = "secret"
    with pytest.raises(ValidationError):
        validate_friction_training_proof_report_v1(payload)


def test_29_unknown_final_judgment_fails_validation() -> None:
    payload = _json_safe_report()
    payload["final_judgment"] = "unknown_final_judgment"
    with pytest.raises(ValidationError):
        validate_friction_training_proof_report_v1(payload)


def test_30_markdown_does_not_contain_public_marketing_overclaim() -> None:
    markdown = render_friction_training_proof_report_markdown_v1(_base_report()).lower()
    assert "public-ready launch" not in markdown
    assert "certified intelligence claim" not in markdown
    assert "marketing proof" not in markdown


@pytest.mark.parametrize("module_name", ["chat_responder", "main"])
def test_31_32_module_does_not_import_prohibited_core_modules(module_name) -> None:
    module = _module()
    imports = _imports_from_source(module)
    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)


@pytest.mark.parametrize("module_name", ["dialogue", "chat_ui"])
def test_33_34_module_does_not_import_prohibited_ui_modules(module_name) -> None:
    module = _module()
    imports = _imports_from_source(module)
    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
