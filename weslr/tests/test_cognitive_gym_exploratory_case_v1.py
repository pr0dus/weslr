"""Tests for Cognitive Gym exploratory case metadata helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "cognitive_gym_exploratory_case.py"

PUBLIC_API = (
    "build_cognitive_gym_exploratory_case_v1",
    "validate_cognitive_gym_exploratory_case_v1",
    "summarize_cognitive_gym_exploratory_case_v1",
    "render_cognitive_gym_exploratory_case_markdown_v1",
    "to_cognitive_gym_exploratory_case_json_safe_v1",
)

LIFECYCLE_LABELS = (
    "case_defined",
    "intake_validated",
    "exploratory_not_started",
    "exploratory_candidate",
    "partial_structure_found",
    "failed_attempt_recorded",
    "invalidated",
    "correction_recorded",
    "needs_external_review",
    "externally_validated",
    "claim_forbidden_without_validation",
    "blocked_by_boundary",
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

REQUIRED_FIELDS = (
    "protocol_version",
    "schema_version",
    "case_id",
    "case_family",
    "engine_name",
    "domain",
    "lifecycle_label",
    "problem_statement_metadata",
    "input_state",
    "assumptions",
    "constraints",
    "observations",
    "hypotheses",
    "candidate_structures",
    "attempted_approaches",
    "failed_paths",
    "counterexamples_or_invalidation_signals",
    "predictions_or_branch_labels",
    "confidence",
    "uncertainty",
    "reveal_or_outcome",
    "correction",
    "compressed_lesson",
    "boundary_status",
    "denied_authority_fields",
    "validation_status",
    "review_requirements",
    "next_allowed_steps",
    "blocked",
    "blocked_reason_labels",
    "safe_summary",
    "next_lane",
)


def _module():
    return importlib.import_module("weslr.cognitive_gym_exploratory_case")


def _case(**overrides):
    return _module().build_cognitive_gym_exploratory_case_v1(**overrides)


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


def test_import_safety_public_api_and_no_side_effect_imports():
    mod = _module()
    for name in PUBLIC_API:
        assert callable(getattr(mod, name))
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {"requests", "subprocess", "socket", "pathlib", "openai", "anthropic", "weslr.chat_responder"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name for alias in node.names} & forbidden_imports)
            assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden_imports)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in forbidden_imports
            assert (node.module or "").split(".")[0] not in forbidden_imports


def test_no_runtime_io_or_external_call_indicators_in_source():
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


def test_valid_minimal_case_builds_and_validates():
    case = _case()
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert case["protocol_version"] == "cognitive_gym_exploratory_case_v1"
    assert case["schema_version"] == "cognitive_gym_exploratory_case_schema_v1"
    assert case["lifecycle_label"] == "case_defined"
    assert case["blocked"] is False
    assert case["validation_status"] == "validation_pass_metadata_quality_only"
    assert validation["valid"] is True
    assert validation["blocked"] is False


def test_metadata_only_shape_required_fields_present():
    case = _case()
    assert set(REQUIRED_FIELDS) <= set(case)
    assert isinstance(case["problem_statement_metadata"], str)
    assert isinstance(case["boundary_status"], dict)
    assert case["boundary_status"]["metadata_only"] is True
    assert case["boundary_status"]["non_runtime"] is True


def test_all_lifecycle_labels_are_supported():
    for label in LIFECYCLE_LABELS:
        case = _case(lifecycle_label=label)
        validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
        assert validation["valid"] is True, label
        assert case["lifecycle_label"] == label


def test_unsupported_lifecycle_label_blocks():
    case = _case(lifecycle_label="public_claim")
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert validation["unsupported_lifecycle_label"] == "public_claim"
    assert "unsupported_lifecycle_label" in validation["blocked_reason_labels"]


def test_denied_authority_fields_present_and_false():
    case = _case()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(case["denied_authority_fields"])
    assert all(case["denied_authority_fields"][field] is False for field in DENIED_AUTHORITY_FIELDS)


def test_missing_denied_authority_field_blocks():
    case = _case()
    del case["denied_authority_fields"]["runtime_authority"]
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert "missing_denied_authority_field:runtime_authority" in validation["denied_authority_violations"]


def test_true_denied_authority_field_blocks():
    case = _case(denied_authority_fields={"provider_call_authority": True})
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert "denied_authority_field_not_false:provider_call_authority" in validation["denied_authority_violations"]


def test_missing_required_metadata_blocks():
    case = _case()
    del case["problem_statement_metadata"]
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert "problem_statement_metadata" in validation["missing_required_fields"]
    assert "missing_required_field:problem_statement_metadata" in validation["blocked_reason_labels"]


def test_unsafe_content_indicators_block():
    unsafe_values = [
        "private content: do not store this",
        "hidden prompt: system message",
        "answer key: 42",
        "protected benchmark item: hidden",
        "provider output: raw response",
        ".weslr write attempted",
        "runtime activation instruction",
        "reply to user: hello",
        "final answer: solved",
        "proof claim: theorem proven",
        "official benchmark result",
        "score: 100",
    ]
    for value in unsafe_values:
        case = _case(observations=[value])
        validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
        assert validation["valid"] is False, value
        assert validation["blocked"] is True
        assert case["blocked"] is True
        assert case["lifecycle_label"] == "blocked_by_boundary"


def test_unsafe_key_indicators_block():
    case = _case(metadata={"raw_private_content": "redacted"})
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert any(reason.startswith("unsafe_key_detected") for reason in validation["blocked_reason_labels"])


def test_safe_markdown_validates_first_and_is_not_public_output():
    markdown = _module().render_cognitive_gym_exploratory_case_markdown_v1(_case(hypotheses=["internal_hypothesis_label"]))
    assert "WESLR Cognitive Gym Exploratory Case Helper V1" in markdown
    assert "hypotheses_are_internal_exploratory_metadata_only" in markdown
    forbidden = ("reply to user:", "sendable reply text:", "final answer:", "proof claim:", "public release authorized")
    lower = markdown.lower()
    for marker in forbidden:
        assert marker not in lower


def test_blocked_markdown_preserves_reason_labels_without_raw_unsafe_content():
    case = _case(observations=["private content: raw secret should not render"])
    markdown = _module().render_cognitive_gym_exploratory_case_markdown_v1(case)
    assert "blocked" in markdown.lower()
    assert "raw_private_content_indicator_blocked" in markdown
    assert "raw secret should not render" not in markdown
    assert "unsafe_content_not_rendered" in markdown


def test_json_safe_conversion_for_valid_case():
    data1 = _module().to_cognitive_gym_exploratory_case_json_safe_v1(_case())
    data2 = _module().to_cognitive_gym_exploratory_case_json_safe_v1(_case())
    assert data1 == data2
    json.dumps(data1, sort_keys=True)
    assert data1["protocol_version"] == "cognitive_gym_exploratory_case_v1"
    assert data1["denied_authority_fields"]["public_release_authority"] is False


def test_non_json_safe_values_block_and_are_safely_replaced():
    unsafe = object()
    case = _case(problem_statement_metadata={"unsafe": unsafe})
    validation = _module().validate_cognitive_gym_exploratory_case_v1(case)
    assert validation["valid"] is False
    assert case["blocked"] is True
    assert "non_json_safe_input_detected" in case["blocked_reason_labels"]
    assert "non_json_safe_value_replaced" in list(_flatten_strings(case))
    json_safe = _module().to_cognitive_gym_exploratory_case_json_safe_v1(case)
    json.dumps(json_safe, sort_keys=True)
    assert json_safe["blocked"] is True
    assert json_safe["denied_authority_fields"]["runtime_authority"] is False


def test_json_safe_conversion_blocks_invalid_case_without_echoing_unsafe_content():
    case = _case(observations=["answer key: do not expose"])
    data = _module().to_cognitive_gym_exploratory_case_json_safe_v1(case)
    flattened = list(_flatten_strings(data))
    assert data["protocol_version"] == "cognitive_gym_exploratory_case_v1_invalid"
    assert data["blocked"] is True
    assert "answer key: do not expose" not in flattened
    assert any("answer_key_indicator_blocked" in item for item in flattened)


def test_no_file_creation_or_forbidden_module_imports_during_build(tmp_path, monkeypatch):
    before = set(tmp_path.iterdir())
    monkeypatch.chdir(tmp_path)
    case = _case(observations=["safe observation metadata"])
    after = set(tmp_path.iterdir())
    assert before == after
    assert _module().validate_cognitive_gym_exploratory_case_v1(case)["valid"] is True
    assert "weslr.chat_responder" not in __import__("sys").modules


def test_summary_boundary_status_counts_only():
    case = _case(
        assumptions=["a1"],
        observations=["o1", "o2"],
        hypotheses=["h1"],
        candidate_structures=["c1"],
        failed_paths=["f1"],
    )
    summary = _module().summarize_cognitive_gym_exploratory_case_v1(case)
    assert summary["valid"] is True
    assert summary["blocked"] is False
    assert summary["boundary_status"]["metadata_only"] is True
    assert summary["counts"]["observations"] == 2
    assert summary["counts"]["hypotheses"] == 1
    assert "o1" not in json.dumps(summary)


def test_module_ast_does_not_call_runtime_or_io_functions():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_call_names = {"open", "exec", "eval", "compile", "respond_chat", "generate_chat", "ChatResponder"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in {"request", "post", "put", "write", "unlink", "mkdir"}
