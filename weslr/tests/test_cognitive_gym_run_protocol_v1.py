"""Tests for CognitiveGymRun metadata protocol helpers V1."""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "cognitive_gym_run_protocol.py"

PUBLIC_API = (
    "build_cognitive_gym_run_v1",
    "validate_cognitive_gym_run_v1",
    "summarize_cognitive_gym_run_v1",
    "render_cognitive_gym_run_markdown_v1",
    "to_cognitive_gym_run_json_safe_v1",
)

SUPPORTED_ENGINE_NAMES = (
    "UNKNOWN_ENGINE",
    "CALIBRATION_LEDGER",
    "CONTRADICTION_FURNACE",
    "GOVERNANCE_BOUNDARY_ENGINE",
    "COUNTERFACTUAL_ENGINE",
    "BLINDSPOT_ENGINE",
    "INVARIANT_MINER",
    "INTENT_RECONSTRUCTION_ENGINE",
    "MEMORY_TRUST_ENGINE",
    "CAUSAL_TRACE_ENGINE",
    "FAILURE_MODE_SIMULATOR",
    "ABSTRACTION_LADDER",
    "SIGNAL_VS_NOISE_ENGINE",
)

SUPPORTED_CHALLENGE_TRACKS = (
    "UNKNOWN / uncertainty",
    "ERDŐS / open mathematical structure",
    "COUNTEREXAMPLE / falsification",
    "CALIBRATION / prediction vs outcome",
    "CONTRADICTION / conflict handling",
    "GOVERNANCE / allowed vs possible",
    "MATERIALS / scientific discovery",
    "CONVERSATION / human understanding",
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


def _module():
    return importlib.import_module("weslr.cognitive_gym_run_protocol")


def _run(**overrides):
    return _module().build_cognitive_gym_run_v1(**overrides)


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


def test_import_safety_and_public_api_exists():
    mod = _module()
    for name in PUBLIC_API:
        assert callable(getattr(mod, name))


def test_build_minimal_valid_cognitive_gym_run():
    run = _run()
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert run["protocol_name"] == "cognitive_gym_run_v1"
    assert run["schema_version"] == "cognitive_gym_run_schema_v1"
    assert run["engine_name"] == "UNKNOWN_ENGINE"
    assert run["challenge_track"] == "UNKNOWN / uncertainty"
    assert run["blocked"] is False
    assert run["validation_status"] == "validation_pass_metadata_quality_only"
    assert validation["valid"] is True
    assert validation["blocked"] is False


def test_required_fields_present():
    run = _run()
    assert set(REQUIRED_FIELDS) <= set(run)


def test_all_denied_authority_fields_present_and_false():
    run = _run()
    assert set(DENIED_AUTHORITY_FIELDS) <= set(run["denied_authority_fields"])
    for field in DENIED_AUTHORITY_FIELDS:
        assert run["denied_authority_fields"][field] is False


def test_all_supported_engine_names_accepted():
    for engine_name in SUPPORTED_ENGINE_NAMES:
        run = _run(engine_name=engine_name)
        validation = _module().validate_cognitive_gym_run_v1(run)
        assert validation["valid"] is True
        assert run["engine_name"] == engine_name


def test_all_challenge_tracks_accepted():
    for challenge_track in SUPPORTED_CHALLENGE_TRACKS:
        run = _run(challenge_track=challenge_track)
        validation = _module().validate_cognitive_gym_run_v1(run)
        assert validation["valid"] is True
        assert run["challenge_track"] == challenge_track


def test_unsupported_engine_name_blocks():
    run = _run(engine_name="DISCONNECTED_PRIVATE_ENGINE")
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert validation["blocked"] is True
    assert validation["unsupported_engine_name"] == "DISCONNECTED_PRIVATE_ENGINE"
    assert "unsupported_engine_name" in validation["blocked_reason_labels"]


def test_unsupported_challenge_track_blocks():
    run = _run(challenge_track="UNAUTHORIZED / track")
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert validation["unsupported_challenge_track"] == "UNAUTHORIZED / track"
    assert "unsupported_challenge_track" in validation["blocked_reason_labels"]


def test_missing_required_field_blocks():
    run = _run()
    del run["knowns"]
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert "knowns" in validation["missing_required_fields"]
    assert "missing_required_field:knowns" in validation["blocked_reason_labels"]


def test_missing_denied_authority_field_blocks():
    run = _run()
    del run["denied_authority_fields"]["runtime_authority_granted"]
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert "missing_denied_authority_field:runtime_authority_granted" in validation["denied_authority_violations"]


def test_non_false_denied_authority_field_blocks():
    run = _run(denied_authority_fields={"provider_call_made": True})
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert "denied_authority_field_not_false:provider_call_made" in validation["denied_authority_violations"]


def test_json_safe_conversion_works():
    data1 = _module().to_cognitive_gym_run_json_safe_v1(_run())
    data2 = _module().to_cognitive_gym_run_json_safe_v1(_run())
    assert data1 == data2
    json.dumps(data1, sort_keys=True)
    assert data1["protocol_name"] == "cognitive_gym_run_v1"
    assert data1["denied_authority_fields"]["official_claim_made"] is False


def test_non_json_safe_values_block_or_are_safely_marked():
    unsafe = object()
    run = _module().build_cognitive_gym_run_v1(engine_specific_metadata={"unsafe": unsafe})
    validation = _module().validate_cognitive_gym_run_v1(run)
    assert validation["valid"] is False
    assert run["blocked"] is True
    assert "engine_specific_metadata_not_json_safe" in run["blocked_reason_labels"]
    assert unsafe not in list(_flatten_strings(run))


def test_safe_markdown_rendering_from_valid_metadata():
    markdown = _module().render_cognitive_gym_run_markdown_v1(_run())
    assert "WESLR CognitiveGymRun Protocol Helper V1" in markdown
    assert "cognitive_gym_run_v1" in markdown
    assert "Denied Authority Fields" in markdown
    assert "provider_call_made=false" in markdown
    assert "safe_markdown_internal_review_material_only" in markdown


def test_safe_markdown_does_not_create_user_facing_answer_or_output():
    markdown = _module().render_cognitive_gym_run_markdown_v1(_run())
    lowered = markdown.lower()
    forbidden = (
        "reply to user:",
        "send to user:",
        "message to send:",
        "final answer:",
        "answer draft:",
        "actual reply body:",
        "user-facing response body:",
        "provider output:",
        "model output:",
        "official score:",
    )
    for marker in forbidden:
        assert marker not in lowered


def test_raw_prompt_response_private_output_indicators_block():
    cases = [
        {"raw_prompt_text": "Raw prompt: do not copy"},
        {"raw_response_text": "Raw response: do not copy"},
        {"private_content": "Private content: do not copy"},
        {"sendable_reply_text": "Reply to user: do not copy"},
        {"final_answer_prose": "Final answer: do not copy"},
        {"answer_draft_text": "Answer draft: do not copy"},
        {"actual_reply_body": "Actual reply body: do not copy"},
    ]
    for case in cases:
        unsafe_value = next(iter(case.values()))
        run = _module().build_cognitive_gym_run_v1(case)
        validation = _module().validate_cognitive_gym_run_v1(run)
        assert validation["valid"] is False
        assert run["blocked"] is True
        assert unsafe_value not in list(_flatten_strings(run))


def test_runtime_provider_feature_judges_scores_official_claim_indicators_block():
    cases = [
        {"chat_responder_output": "ChatResponder output: unsafe"},
        {"respond_chat_output": "respond_chat output: unsafe"},
        {"generate_chat_output": "generate_chat output: unsafe"},
        {"provider_output": "Provider output: unsafe"},
        {"model_output": "Model output: unsafe"},
        {"search_output": "Search output: unsafe"},
        {"advisor_output": "Advisor output: unsafe"},
        {"dot_weslr_write_signal": ".weslr write unsafe"},
        {"feature_flag_signal": "feature_flag_enabled=true"},
        {"judges_scores": "Official score: 100"},
        {"official_claims": "Passed the Turing test"},
    ]
    for case in cases:
        run = _module().build_cognitive_gym_run_v1(case)
        assert run["blocked"] is True
        assert _module().validate_cognitive_gym_run_v1(run)["valid"] is False


def test_open_problem_solution_claim_blocks():
    run = _module().build_cognitive_gym_run_v1({"open_problem_solution_claim": "Erdős solved"})
    assert run["blocked"] is True
    assert any("open_problem_solution" in label for label in run["blocked_reason_labels"])


def test_future_certainty_and_prediction_authority_claims_block():
    cases = [
        {"future_certainty_claim": "Guaranteed future outcome"},
        {"prediction_authority_claim": "prediction_authority_granted=true"},
    ]
    for case in cases:
        run = _module().build_cognitive_gym_run_v1(case)
        assert run["blocked"] is True
        assert _module().validate_cognitive_gym_run_v1(run)["valid"] is False


def test_engine_specific_metadata_stays_inside_protocol_and_does_not_fork_shape():
    run = _run(engine_specific_metadata={"safe_engine_label": "engine_specific_metadata", "branch_count": 2})
    assert run["protocol_name"] == "cognitive_gym_run_v1"
    assert run["engine_specific_metadata"] == {"safe_engine_label": "engine_specific_metadata", "branch_count": 2}
    assert "private_report_shape" not in run
    assert _module().validate_cognitive_gym_run_v1(run)["valid"] is True


def test_no_runtime_side_effect_imports_calls_or_io():
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {
        "weslr.chat_responder",
        "chat_responder",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "openai",
    }
    forbidden_calls = {
        "ChatResponder",
        "respond_chat",
        "generate_chat",
        "open",
        "Path",
        "requests",
        "httpx",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name not in forbidden_imports for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in forbidden_imports
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in {"read_text", "write_text", "open", "request", "post"}


def test_no_dot_weslr_io_and_no_chat_responder_import_call_strings_in_runtime_code():
    source = MODULE_PATH.read_text()
    assert "from weslr.chat_responder" not in source
    assert "import weslr.chat_responder" not in source
    assert "import chat_responder" not in source
    assert "open(" not in source
    assert "read_text(" not in source
    assert "write_text(" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"ChatResponder", "respond_chat", "generate_chat"}
            if isinstance(func, ast.Attribute):
                assert func.attr not in {"respond_chat", "generate_chat"}
