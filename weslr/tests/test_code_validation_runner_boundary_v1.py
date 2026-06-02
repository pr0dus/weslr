from __future__ import annotations

import ast
import inspect

import pytest

from weslr.code_validation_runner_boundary import (
    CodeValidationPacket,
    CodeValidationSummary,
    HELPER_TYPE_V1,
    VALIDATION_MODES_V1,
    VALIDATION_STATUSES_V1,
    VALIDATION_TARGET_TYPES_V1,
    build_code_validation_packet_v1,
    build_initial_code_validation_examples_v1,
    classify_validation_target_v1,
    evaluate_validation_result_v1,
    select_validation_modes_v1,
    summarize_code_validation_packet_v1,
    to_code_validation_json_safe_v1,
    validate_code_validation_packet_v1,
)


BASE_PACKET_KWARGS = dict(
    validation_packet_id="base_validation_packet_v1",
    target_id="base_target_v1",
    target_type="python_module",
    target_path_summary="weslr/example_module.py",
    candidate_source_ref="candidate_source_base_v1",
    artifact_provenance_ref="artifact_provenance_base_v1",
    file_manifest_ref="file_manifest_base_v1",
    validation_modes_requested=("syntax_only", "static_analysis"),
    validation_modes_completed=("syntax_only", "static_analysis"),
    validation_status="passed",
    validation_summary="base validation pass",
    test_result_refs=("test_result_base_v1",),
    failed_check_refs=(),
    warning_refs=(),
    protected_file_diff_status="clear",
    secret_risk_status="not_detected",
    network_policy_status="not_required",
    write_policy_status="not_required",
    rollback_required=False,
    patch_feedback_allowed=False,
    artifact_export_allowed=False,
    tool_execution_allowed=False,
    public_claim_allowed=False,
    owner_review_required=False,
    operator_review_required=False,
    recommended_next_check="review_validation_metadata",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_packet"},
)


FORBIDDEN_CALL_NAMES = {
    "open",
    "exec",
    "eval",
    "system",
    "popen",
    "run",
    "call",
    "check_call",
    "check_output",
    "communicate",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
}

FORBIDDEN_IMPORT_NAMES = {
    "subprocess",
    "os",
    "pathlib",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
}


def _example_by_name(name: str):
    for packet in build_initial_code_validation_examples_v1():
        payload = to_code_validation_json_safe_v1(packet)
        if payload["validation_packet_id"] == name or (payload.get("safe_metadata") or {}).get("example_name") == name:
            return packet
    raise AssertionError(f"missing example: {name}")


def test_module_exports_public_api_and_constants():
    assert HELPER_TYPE_V1 == "code_validation_runner_boundary_v1"
    assert VALIDATION_TARGET_TYPES_V1
    assert VALIDATION_MODES_V1
    assert VALIDATION_STATUSES_V1


def test_builds_packet_and_round_trips_summary():
    packet = build_code_validation_packet_v1(**BASE_PACKET_KWARGS)
    assert isinstance(packet, CodeValidationPacket)
    summary = summarize_code_validation_packet_v1(packet)
    assert isinstance(summary, CodeValidationSummary)
    assert summary.validation_packet_id == BASE_PACKET_KWARGS["validation_packet_id"]


def test_classifies_validation_target_from_path_only_when_needed():
    assert classify_validation_target_v1(target_path_summary="weslr/tests/test_example.py") == "python_test"
    assert classify_validation_target_v1(target_path_summary="docs/example.md") == "markdown_doc"
    assert classify_validation_target_v1(target_path_summary="site/index.html") == "html_css_js_static_site"
    assert classify_validation_target_v1(target_path_summary="scripts/run.sh") == "shell_script"
    assert classify_validation_target_v1(target_path_summary="unknown/thing.zzz") == "unknown_target"


def test_selects_validation_modes_by_target_type_and_metadata_only():
    modes = select_validation_modes_v1(target_type="python_test", target_path_summary="weslr/tests/test_example.py")
    assert "unit_tests" in modes
    assert "focused_tests" in modes
    assert "syntax_only" in modes


def test_unknown_target_fails_closed_in_classifier_and_validator():
    packet = build_code_validation_packet_v1(
        **{**BASE_PACKET_KWARGS, "target_type": "mystery_target", "validation_packet_id": "unknown_target_v1"}
    )
    assert packet.target_type == "unknown_target"
    with pytest.raises(ValueError, match="unknown_target_promoted_as_valid"):
        validate_code_validation_packet_v1(packet)


def test_unknown_validation_mode_fails_closed():
    packet = build_code_validation_packet_v1(
        **{
            **BASE_PACKET_KWARGS,
            "validation_packet_id": "unknown_mode_v1",
            "validation_modes_requested": ("mystery_mode",),
        }
    )
    with pytest.raises(ValueError, match="unknown_validation_mode_promoted_as_valid"):
        validate_code_validation_packet_v1(packet)


def test_unknown_status_fails_closed():
    packet = build_code_validation_packet_v1(
        **{**BASE_PACKET_KWARGS, "validation_packet_id": "unknown_status_v1", "validation_status": "mystery_status"}
    )
    with pytest.raises(ValueError, match="unknown_status_promoted_as_valid"):
        validate_code_validation_packet_v1(packet)


@pytest.mark.parametrize(
    "field_name",
    [
        "tool_execution_allowed",
        "public_claim_allowed",
        "proof_claim_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "learning_claimed",
    ],
)
def test_forbidden_true_flags_fail_validation(field_name: str):
    packet = build_code_validation_packet_v1(**BASE_PACKET_KWARGS)
    payload = to_code_validation_json_safe_v1(packet)
    payload[field_name] = True
    with pytest.raises(ValueError):
        validate_code_validation_packet_v1(payload)


def test_failed_validation_allows_patch_feedback_only():
    packet = evaluate_validation_result_v1(
        build_code_validation_packet_v1(
            **{**BASE_PACKET_KWARGS, "validation_packet_id": "failed_packet_v1", "validation_status": "failed", "validation_summary": "tests failed"}
        )
    )
    assert packet.patch_feedback_allowed is True
    assert packet.artifact_export_allowed is False
    assert validate_code_validation_packet_v1(packet) is True


def test_passed_validation_still_does_not_allow_public_claim():
    packet = evaluate_validation_result_v1(build_code_validation_packet_v1(**BASE_PACKET_KWARGS))
    assert packet.validation_status == "passed"
    assert packet.public_claim_allowed is False
    assert validate_code_validation_packet_v1(packet) is True


def test_missing_manifest_blocks_export():
    packet = evaluate_validation_result_v1(
        build_code_validation_packet_v1(
            **{**BASE_PACKET_KWARGS, "validation_packet_id": "missing_manifest_v1", "file_manifest_ref": ""}
        )
    )
    assert packet.validation_status == "blocked_missing_manifest"
    assert packet.artifact_export_allowed is False
    with pytest.raises(ValueError, match="missing_manifest_required"):
        validate_code_validation_packet_v1(packet)


def test_missing_provenance_blocks_export_and_promotion():
    packet = evaluate_validation_result_v1(
        build_code_validation_packet_v1(
            **{**BASE_PACKET_KWARGS, "validation_packet_id": "missing_provenance_v1", "artifact_provenance_ref": ""}
        )
    )
    assert packet.validation_status == "blocked_by_policy"
    assert packet.artifact_export_allowed is False
    with pytest.raises(ValueError, match="missing_provenance_required"):
        validate_code_validation_packet_v1(packet)


def test_secret_risk_blocks_export_when_allowed_flag_is_set():
    packet = evaluate_validation_result_v1(
        build_code_validation_packet_v1(
            **{
                **BASE_PACKET_KWARGS,
                "validation_packet_id": "secret_risk_v1",
                "secret_risk_status": "blocked",
                "owner_review_required": True,
                "operator_review_required": True,
            }
        )
    )
    assert packet.validation_status == "blocked_secret_risk"
    payload = to_code_validation_json_safe_v1(packet)
    payload["artifact_export_allowed"] = True
    with pytest.raises(ValueError, match="secret_risk_blocks_export"):
        validate_code_validation_packet_v1(payload)


def test_protected_file_requires_review():
    packet = build_code_validation_packet_v1(
        **{**BASE_PACKET_KWARGS, "validation_packet_id": "protected_file_review_v1", "protected_file_diff_status": "blocked"}
    )
    with pytest.raises(ValueError, match="owner_operator_review_required_for_risk"):
        validate_code_validation_packet_v1(packet)


def test_python_module_syntax_pass_example():
    packet = _example_by_name("python_module_syntax_pass_public_claim_blocked")
    payload = to_code_validation_json_safe_v1(packet)
    assert payload["validation_status"] == "passed"
    assert payload["public_claim_allowed"] is False


def test_python_tests_fail_and_patch_feedback_is_proposal_only():
    packet = _example_by_name("python_tests_fail_patch_feedback_only")
    payload = to_code_validation_json_safe_v1(packet)
    assert payload["validation_status"] == "failed"
    assert payload["patch_feedback_allowed"] is True
    assert payload["artifact_export_allowed"] is False


def test_protected_file_diff_blocks_promotion_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("protected_file_diff_blocks_promotion"))
    assert payload["validation_status"] == "blocked_protected_file"
    assert payload["owner_review_required"] is True
    assert payload["operator_review_required"] is True


def test_secret_api_key_risk_blocks_promotion_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("secret_api_key_risk_blocks_promotion"))
    assert payload["validation_status"] == "blocked_secret_risk"
    assert payload["owner_review_required"] is True
    assert payload["operator_review_required"] is True


def test_missing_manifest_blocks_export_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("missing_manifest_blocks_export"))
    assert payload["validation_status"] == "blocked_missing_manifest"
    assert payload["artifact_export_allowed"] is False


def test_markdown_doc_passes_policy_but_no_proof_claim_allowed_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("markdown_doc_pass_no_proof_claim"))
    assert payload["validation_status"] == "passed"
    assert payload["proof_claim_allowed"] is False


def test_static_site_passes_validation_but_deployment_remains_blocked_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("static_site_pass_deployment_blocked"))
    assert payload["validation_status"] == "passed"
    assert payload["artifact_export_allowed"] is True
    assert payload["public_claim_allowed"] is False


def test_shell_script_blocked_by_command_execution_policy_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("shell_script_blocked_by_policy"))
    assert payload["validation_status"] == "blocked_by_policy"
    assert payload["tool_execution_allowed"] is False


def test_network_requiring_validation_blocked_without_approval_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("network_requiring_validation_blocked_without_approval"))
    assert payload["owner_review_required"] is True
    assert payload["operator_review_required"] is True
    assert payload["validation_status"] == "passed"


def test_release_gate_passes_but_runtime_wiring_remains_blocked_example():
    payload = to_code_validation_json_safe_v1(_example_by_name("release_gate_pass_runtime_wiring_blocked"))
    assert payload["validation_status"] == "passed"
    assert payload["runtime_authority"] is False
    assert payload["writes_state"] is False


def test_json_safe_conversion_does_not_mutate_input():
    raw = {
        "packet": {
            "name": "alpha",
            "nested": [1, {"two": 2}],
            "flags": {"a", "b"},
        }
    }
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_code_validation_json_safe_v1(raw)
    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    packet = build_code_validation_packet_v1(
        **{
            **BASE_PACKET_KWARGS,
            "safe_metadata": {
                "example_name": "summary_redaction_v1",
                "raw_private_content": "should_not_escape",
                "secret_token": "should_not_escape",
                "hidden_prompt": "should_not_escape",
            },
        }
    )
    summary = summarize_code_validation_packet_v1(packet)
    text = str(summary).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_source_inspection_finds_no_subprocess_shell_or_file_io_calls():
    import weslr.code_validation_runner_boundary as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert not (imported & FORBIDDEN_IMPORT_NAMES)
        if isinstance(node, ast.ImportFrom):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert not (imported & FORBIDDEN_IMPORT_NAMES)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALL_NAMES
