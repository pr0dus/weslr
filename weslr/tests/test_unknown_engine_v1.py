"""Tests for UNKNOWN ENGINE metadata helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "unknown_engine.py"

PUBLIC_API = (
    "build_unknown_engine_run_v1",
    "validate_unknown_engine_run_v1",
    "summarize_unknown_engine_run_v1",
    "render_unknown_engine_run_markdown_v1",
    "to_unknown_engine_run_json_safe_v1",
)

REQUIRED_FIELDS = (
    "protocol_name",
    "schema_version",
    "engine_name",
    "engine_version_label",
    "challenge_track",
    "input_state",
    "observations",
    "knowns",
    "unknowns",
    "hypotheses",
    "predictions_or_branch_labels",
    "confidence",
    "uncertainty",
    "invalidation_signals",
    "reveal_or_outcome",
    "correction",
    "compressed_lesson",
    "boundary_status",
    "denied_authority_fields",
    "validation_status",
    "blocked",
    "blocked_reason_labels",
    "visible_risks",
    "followups",
    "next_lane",
)

DENIED_AUTHORITY_FIELDS = (
    "cognitive_gym_authority_granted",
    "cognitive_gym_run_authority_granted",
    "unknown_engine_authority_granted",
    "prediction_authority_granted",
    "future_certainty_authority_granted",
    "challenge_solution_authority_granted",
    "open_problem_solution_claim_authorized",
    "answer_authority_granted",
    "preview_authority_granted",
    "reply_output_authority_granted",
    "reply_text_authority_granted",
    "user_facing_output_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "official_evaluation_authority_granted",
    "turing_test_authority_granted",
    "real_conversation_sandbox_authority_granted",
    "cognitive_gym_executed",
    "cognitive_gym_run_executed",
    "unknown_engine_executed",
    "prediction_output_created",
    "future_certainty_claim_created",
    "challenge_solution_claim_created",
    "reply_preview_executed",
    "preview_output_created",
    "reply_output_created",
    "reply_text_executed",
    "sendable_reply_text_created",
    "actual_reply_body_created",
    "user_facing_output_executed",
    "user_facing_reply_created",
    "live_dialogue_output_created",
    "final_answer_generation_executed",
    "final_answer_generated",
    "final_answer_prose_created",
    "answer_draft_created",
    "answer_composition_executed",
    "answer_formation_executed",
    "runtime_wired",
    "chat_responder_called",
    "respond_chat_called",
    "generate_chat_called",
    "provider_call_made",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_read_performed",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judges_created",
    "scores_created",
    "official_claim_made",
)


def _module():
    return importlib.import_module("weslr.unknown_engine")


def _sample_run(**overrides):
    kwargs = {
        "knowns": ["repo_head_known"],
        "unknowns": ["review_result_unknown"],
        "missing_evidence": ["external_verification_missing"],
        "uncertainty_map": {"branch_a": "qualitative_low"},
        "possible_future_branches": ["implementation_review_next"],
        "branch_assumptions": ["helper_metadata_stays_internal"],
        "branch_likelihood_labels": ["qualitative_possible_not_prediction"],
        "falsification_tests": ["denied_authority_field_non_false"],
        "safe_next_observations": ["inspect_validation_metadata"],
        "evidence_change_labels": ["new_runtime_signal_blocks"],
        "risk_boundaries": ["metadata_misread_as_output"],
        "limitations": ["no_runtime_execution"],
        "compressed_lesson": "unknown_engine_metadata_only",
    }
    kwargs.update(overrides)
    return _module().build_unknown_engine_run_v1(**kwargs)


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


def test_import_safety_public_api_and_no_side_effect_paths():
    mod = _module()
    for name in PUBLIC_API:
        assert callable(getattr(mod, name))
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {"requests", "subprocess", "socket", "pathlib", "openai", "anthropic"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden_imports)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports


def test_no_runtime_or_external_call_indicators_in_source():
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
        "provider_call_made=True",
        "judges_created=True",
    )
    for marker in forbidden:
        assert marker not in source


def test_valid_unknown_engine_cognitive_gym_run_build_defaults():
    run = _sample_run()
    validation = _module().validate_unknown_engine_run_v1(run)
    assert validation["valid"] is True
    assert run["protocol_name"] == "cognitive_gym_run_v1"
    assert run["engine_name"] == "UNKNOWN_ENGINE"
    assert run["challenge_track"] == "UNKNOWN / uncertainty"
    assert set(REQUIRED_FIELDS) <= set(run)


def test_denied_authority_fields_present_and_false():
    run = _sample_run()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(run["denied_authority_fields"])
    assert all(run["denied_authority_fields"][field] is False for field in DENIED_AUTHORITY_FIELDS)


def test_validation_reuses_cognitive_gym_validation_for_required_fields():
    run = _sample_run()
    del run["knowns"]
    validation = _module().validate_unknown_engine_run_v1(run)
    assert validation["valid"] is False
    assert "knowns" in validation["missing_required_fields"]
    assert "missing_required_field:knowns" in validation["blocked_reason_labels"]


def test_unknown_engine_mapping_and_containment():
    run = _sample_run()
    metadata = run["engine_specific_metadata"]["unknown_engine_metadata"]
    assert run["knowns"] == ["repo_head_known"]
    assert "review_result_unknown" in run["unknowns"]
    assert "external_verification_missing" in run["unknowns"]
    assert "branch_a=qualitative_low" in run["uncertainty"]
    assert run["predictions_or_branch_labels"] == ["implementation_review_next"]
    assert "helper_metadata_stays_internal" in run["hypotheses"]
    assert "qualitative_possible_not_prediction" in run["confidence"]
    assert "qualitative_possible_not_prediction" in run["uncertainty"]
    assert "denied_authority_field_non_false" in run["invalidation_signals"]
    assert "inspect_validation_metadata" in run["followups"]
    assert "new_runtime_signal_blocks" in run["invalidation_signals"]
    assert "new_runtime_signal_blocks" in run["correction"]
    assert "metadata_misread_as_output" in run["visible_risks"]
    assert "no_runtime_execution" in run["visible_risks"]
    assert run["compressed_lesson"] == "unknown_engine_metadata_only"
    assert metadata["missing_evidence_labels"] == ["external_verification_missing"]
    assert metadata["assumption_labels"] == ["helper_metadata_stays_internal"]
    assert metadata["safe_next_observation_labels"] == ["inspect_validation_metadata"]
    assert metadata["evidence_change_labels"] == ["new_runtime_signal_blocks"]
    assert metadata["falsification_test_labels"] == ["denied_authority_field_non_false"]
    assert metadata["risk_boundary_labels"] == ["metadata_misread_as_output"]
    assert metadata["limitation_labels"] == ["no_runtime_execution"]


def test_safe_markdown_is_internal_and_not_user_facing_output():
    markdown = _module().render_unknown_engine_run_markdown_v1(_sample_run())
    assert "WESLR UNKNOWN ENGINE Helper V1" in markdown
    assert "not_user_facing_answer_text" in markdown
    assert "not_reply_payload" in markdown
    assert "not_final_answer_prose" in markdown
    assert "sendable reply text:" not in markdown.lower()
    assert "final answer:" not in markdown.lower()


def test_json_safe_conversion_preserves_shape_and_containment():
    data = _module().to_unknown_engine_run_json_safe_v1(_sample_run())
    json.dumps(data, sort_keys=True)
    assert data["engine_name"] == "UNKNOWN_ENGINE"
    assert "unknown_engine_metadata" in data["engine_specific_metadata"]
    assert all(data["denied_authority_fields"][field] is False for field in DENIED_AUTHORITY_FIELDS)


def test_summary_reports_containment_and_denied_authority():
    summary = _module().summarize_unknown_engine_run_v1(_sample_run())
    assert summary["unknown_engine_valid"] is True
    assert summary["engine_specific_metadata_contained"] is True
    assert summary["denied_authority_fields_false"] is True


def test_unsupported_raw_private_runtime_output_indicators_block_without_leak():
    run = _module().build_unknown_engine_run_v1(raw_prompt_text="raw prompt: hidden", private_blob="secret: x")
    assert run["blocked"] is True
    assert any("raw_prompt" in label or "private" in label for label in run["blocked_reason_labels"])
    safe = _module().to_unknown_engine_run_json_safe_v1(run)
    flattened = "\n".join(_flatten_strings(safe)).lower()
    assert "secret: x" not in flattened
    assert "raw prompt: hidden" not in flattened


def test_prediction_future_certainty_and_open_problem_solution_claims_block():
    run = _module().build_unknown_engine_run_v1(
        possible_future_branches=["prediction authority granted"],
        evidence_change_labels=["guaranteed future"],
        limitations=["Erdos solved"],
    )
    assert run["blocked"] is True
    labels = " ".join(run["blocked_reason_labels"])
    assert "prediction" in labels
    assert "future_certainty" in labels
    assert "open_problem_solution" in labels


def test_chatresponder_provider_dot_weslr_feature_flag_judges_scores_official_indicators_block():
    cases = [
        {"chat_responder_signal": "respond_chat"},
        {"provider_output": "provider output: text"},
        {"model_output": "model output: text"},
        {"search_output": "search result: text"},
        {"advisor_output": "advisor response: text"},
        {"dot_weslr_read": ".weslr read"},
        {"feature_flag_enabled": "feature_flag_enabled=true"},
        {"judge_score": "official score: 100"},
        {"official_claim": "passed the Turing test"},
    ]
    for kwargs in cases:
        run = _module().build_unknown_engine_run_v1(**kwargs)
        assert run["blocked"] is True


def test_wrong_engine_name_or_authority_grant_blocks():
    run = _sample_run()
    run["engine_name"] = "CALIBRATION_LEDGER"
    assert _module().validate_unknown_engine_run_v1(run)["valid"] is False
    run = _sample_run()
    run["denied_authority_fields"]["unknown_engine_authority_granted"] = True
    validation = _module().validate_unknown_engine_run_v1(run)
    assert validation["valid"] is False
    assert "denied_authority_field_not_false:unknown_engine_authority_granted" in validation["denied_authority_violations"]


def test_no_result_artifact_runtime_wiring_or_external_io_calls_in_ast():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_calls = {"open", "exec", "eval", "compile", "respond_chat", "generate_chat", "ChatResponder"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            assert name not in forbidden_calls
    run = _sample_run()
    assert run["denied_authority_fields"]["runtime_wired"] is False
    assert run["denied_authority_fields"]["chat_responder_called"] is False
    assert run["denied_authority_fields"]["provider_call_made"] is False
    assert run["denied_authority_fields"]["dot_weslr_read_performed"] is False
    assert run["denied_authority_fields"]["dot_weslr_write_performed"] is False
    assert run["denied_authority_fields"]["scores_created"] is False
