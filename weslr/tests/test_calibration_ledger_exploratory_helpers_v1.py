"""Tests for CALIBRATION_LEDGER exploratory metadata helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "calibration_ledger_exploratory_helpers.py"

PUBLIC_API = (
    "build_calibration_ledger_exploratory_case_v1",
    "validate_calibration_ledger_exploratory_case_v1",
    "summarize_calibration_ledger_exploratory_case_v1",
    "render_calibration_ledger_exploratory_case_markdown_v1",
    "to_calibration_ledger_exploratory_case_json_safe_v1",
)

CALIBRATION_FIELDS = (
    "calibration_case_id",
    "predicted_branch_label",
    "confidence_label",
    "uncertainty_label",
    "observed_outcome_label",
    "mismatch_label",
    "correction_label",
    "lesson_label",
    "calibration_status",
)

CALIBRATION_STATUSES = (
    "calibration_case_defined",
    "prediction_label_recorded",
    "outcome_label_recorded",
    "match_recorded",
    "mismatch_recorded",
    "correction_label_recorded",
    "lesson_label_recorded",
    "needs_external_review",
)

DENIED_AUTHORITY_FIELDS = (
    "runtime_authority",
    "chat_authority",
    "final_answer_authority",
    "proof_claim_authority",
    "open_problem_solved_claim_authority",
    "scientific_discovery_claim_authority",
    "official_benchmark_authority",
    "turing_test_claim_authority",
    "intelligence_certification_authority",
    "consciousness_claim_authority",
    "provider_call_authority",
    "search_call_authority",
    "persistence_authority",
    "scoring_authority",
    "judge_authority",
    "public_release_authority",
)


def _module():
    return importlib.import_module("weslr.calibration_ledger_exploratory_helpers")


def _case(**overrides):
    return _module().build_calibration_ledger_exploratory_case_v1(**overrides)


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


def test_import_safety_and_public_apis():
    before = set(sys.modules)
    mod = _module()
    for name in PUBLIC_API:
        assert callable(getattr(mod, name))
    newly_imported = set(sys.modules) - before
    assert "weslr.chat_responder" not in newly_imported

    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {"requests", "subprocess", "socket", "pathlib", "openai", "anthropic", "weslr.chat_responder"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name for alias in node.names}
            assert not (names & forbidden_imports)
            assert not ({name.split(".")[0] for name in names} & forbidden_imports)
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module not in forbidden_imports
            assert module.split(".")[0] not in forbidden_imports


def test_no_runtime_io_chatresponder_or_external_call_indicators_in_source():
    source = MODULE_PATH.read_text()
    forbidden = (
        "from weslr.chat_responder",
        "import weslr.chat_responder",
        "respond_chat(",
        "generate_chat(",
        "ChatResponder(",
        "requests.",
        "open(",
        ".weslr/",
        "provider_call_authority=True",
        "scoring_authority=True",
        "judge_authority=True",
    )
    for marker in forbidden:
        assert marker not in source


def test_valid_minimal_calibration_case_builds_and_validates():
    case = _case()
    validation = _module().validate_calibration_ledger_exploratory_case_v1(case)
    assert case["engine_name"] == "CALIBRATION_LEDGER"
    assert case["case_family"] == "calibration_ledger_exploratory_case"
    assert case["blocked"] is False
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert case["validation_status"] == "validation_pass_metadata_quality_only"


def test_one_family_only_behavior_blocks_other_engine_family():
    case = _case(engine_family="UNKNOWN_ENGINE")
    validation = _module().validate_calibration_ledger_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert "unsupported_engine_family" in validation["blocked_reason_labels"]


def test_metadata_maps_into_shared_exploratory_case_fields():
    case = _case(
        calibration_case_id="calibration_case_alpha",
        predicted_branch_label="branch_alpha",
        confidence_label="confidence_medium",
        uncertainty_label="uncertainty_high",
        observed_outcome_label="outcome_beta",
        mismatch_label="mismatch_detected",
        correction_label="correction_reduce_confidence",
        lesson_label="lesson_track_uncertainty",
        calibration_status="mismatch_recorded",
    )
    ledger = case["engine_specific_metadata"]["calibration_ledger"]
    assert case["case_id"] == "calibration_case_alpha"
    assert case["predictions_or_branch_labels"] == ["branch_alpha"]
    assert case["confidence"] == "confidence_medium"
    assert case["uncertainty"] == "uncertainty_high"
    assert case["reveal_or_outcome"] == "outcome_beta"
    assert case["counterexamples_or_invalidation_signals"] == ["mismatch_detected"]
    assert case["correction"] == "correction_reduce_confidence"
    assert case["compressed_lesson"] == "lesson_track_uncertainty"
    assert case["lifecycle_label"] == "invalidated"
    assert ledger["calibration_status"] == "mismatch_recorded"


def test_calibration_status_labels_supported_and_unsupported_blocks():
    for status in CALIBRATION_STATUSES:
        case = _case(calibration_status=status)
        validation = _module().validate_calibration_ledger_exploratory_case_v1(case)
        assert validation["valid"] is True, status
        assert case["engine_specific_metadata"]["calibration_ledger"]["calibration_status"] == status

    bad = _case(calibration_status="public_claim_ready")
    validation = _module().validate_calibration_ledger_exploratory_case_v1(bad)
    assert validation["valid"] is False
    assert "unsupported_calibration_status" in validation["blocked_reason_labels"]


def test_missing_calibration_metadata_blocks():
    case = _case()
    del case["engine_specific_metadata"]["calibration_ledger"]["lesson_label"]
    validation = _module().validate_calibration_ledger_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert "lesson_label" in validation["missing_calibration_metadata_fields"]
    assert "missing_calibration_metadata:lesson_label" in validation["blocked_reason_labels"]


def test_denied_authority_fields_present_and_false():
    case = _case()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(case["denied_authority_fields"])
    assert all(case["denied_authority_fields"][field] is False for field in DENIED_AUTHORITY_FIELDS)


def test_missing_and_true_authority_blocks():
    missing = _case()
    del missing["denied_authority_fields"]["runtime_authority"]
    validation = _module().validate_calibration_ledger_exploratory_case_v1(missing)
    assert validation["valid"] is False
    assert "missing_denied_authority_field:runtime_authority" in validation["denied_authority_violations"]

    true_case = _case()
    true_case["denied_authority_fields"]["provider_call_authority"] = True
    validation = _module().validate_calibration_ledger_exploratory_case_v1(true_case)
    assert validation["valid"] is False
    assert "denied_authority_field_not_false:provider_call_authority" in validation["denied_authority_violations"]


def test_unsafe_indicators_block_without_echoing_raw_content():
    unsafe_values = [
        "private content: do not store this",
        "hidden prompt: system message",
        "answer key: 42",
        "protected benchmark item: hidden",
        "provider output: raw response",
        ".weslr write attempted",
        "runtime activation instruction",
        "reply to user: hello",
        "score: 10",
        "proof claim: solved",
        "official benchmark passed",
    ]
    for value in unsafe_values:
        case = _case(predicted_branch_label=value)
        validation = _module().validate_calibration_ledger_exploratory_case_v1(case)
        assert validation["valid"] is False, value
        text = json.dumps(case, sort_keys=True)
        assert value not in text
        assert case["blocked"] is True


def test_safe_markdown_validates_first_and_is_not_final_or_user_facing_claim_text():
    case = _case()
    markdown = _module().render_calibration_ledger_exploratory_case_markdown_v1(case)
    lowered = markdown.lower()
    assert "weslr calibration_ledger exploratory helper v1" in lowered
    assert "safe_markdown_is_not_user_facing_output" in markdown
    forbidden = (
        "final answer:",
        "reply to user:",
        "sendable reply text:",
        "proof claim:",
        "open problem solution",
        "public release authorized",
    )
    for marker in forbidden:
        assert marker not in lowered


def test_blocked_markdown_preserves_reason_labels_without_unsafe_raw_content():
    raw = "hidden prompt: raw secret prompt"
    case = _case(predicted_branch_label=raw)
    markdown = _module().render_calibration_ledger_exploratory_case_markdown_v1(case)
    assert "blocked: `True`" in markdown
    assert "hidden_prompt_or_answer_key_indicator_blocked" in markdown
    assert raw not in markdown


def test_json_safe_conversion_for_valid_and_blocked_cases():
    valid = _case()
    valid_json = _module().to_calibration_ledger_exploratory_case_json_safe_v1(valid)
    json.dumps(valid_json, sort_keys=True)
    assert valid_json["engine_name"] == "CALIBRATION_LEDGER"
    assert valid_json["blocked"] is False

    blocked = _case(predicted_branch_label={"not": "a string"})
    blocked_json = _module().to_calibration_ledger_exploratory_case_json_safe_v1(blocked)
    json.dumps(blocked_json, sort_keys=True)
    assert blocked_json["blocked"] is True
    assert blocked_json["protocol_version"] == "calibration_ledger_exploratory_case_v1_invalid"
    assert blocked_json["denied_authority_fields"]["runtime_authority"] is False


def test_no_file_creation_no_dot_weslr_io_no_chatresponder_or_provider_calls(tmp_path, monkeypatch):
    before = {path.name for path in tmp_path.iterdir()}
    monkeypatch.chdir(tmp_path)
    before_modules = set(sys.modules)
    case = _case()
    after_modules = set(sys.modules)
    after = {path.name for path in tmp_path.iterdir()}
    assert before == after
    assert "weslr.chat_responder" not in (after_modules - before_modules)
    assert case["boundary_status"]["metadata_only"] is True
    all_strings = "\n".join(_flatten_strings(case)).lower()
    assert "provider output:" not in all_strings
    assert ".weslr write" not in all_strings


def test_summary_boundary_status_only():
    case = _case()
    summary = _module().summarize_calibration_ledger_exploratory_case_v1(case)
    assert summary["engine_name"] == "CALIBRATION_LEDGER"
    assert summary["calibration_status"] == "calibration_case_defined"
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["denied_authority_fields_false"] is True
    assert summary["calibration_metadata_fields_present_count"] == len(CALIBRATION_FIELDS)
    assert summary["next_lane"] == "REVIEW_CALIBRATION_LEDGER_EXPLORATORY_HELPERS_IMPLEMENTATION_V1"


def test_ast_has_no_forbidden_runtime_io_calls():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_calls = {"open", "exec", "eval", "compile", "respond_chat", "generate_chat", "ChatResponder"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in {"post", "request", "write_text", "read_text", "mkdir", "touch"}
