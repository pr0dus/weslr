from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.autonomous_debugging_dry_run_boundary import (
    ALLOWED_DEBUG_INPUT_CLASSES_V1,
    ALLOWED_DRY_RUN_ACTIONS_V1,
    ALLOWED_DRY_RUN_STATUSES_V1,
    ALLOWED_HYPOTHESIS_TYPES_V1,
    DebugDryRunPacket,
    DebugDryRunSummary,
    ValidationError,
    build_debug_dry_run_packet_v1,
    build_initial_debug_dry_run_examples_v1,
    classify_debug_input_v1,
    derive_debug_hypotheses_v1,
    select_debug_dry_run_actions_v1,
    summarize_debug_dry_run_packet_v1,
    to_debug_dry_run_json_safe_v1,
    validate_debug_dry_run_packet_v1,
)

BASE_PACKET_KWARGS = dict(
    debug_dry_run_packet_id="base_debug_v1",
    debug_input_class="test_failure_report",
    input_summary="Base unit test failure metadata.",
    validation_packet_ref="validation_packet_base_v1",
    patch_feedback_packet_ref="",
    tool_use_packet_ref="",
    artifact_provenance_ref="artifact_provenance_base_v1",
    file_manifest_ref="file_manifest_base_v1",
    hypotheses=("test_expectation_mismatch_hypothesis",),
    proposed_dry_run_actions=("inspect_metadata_only",),
    blocked_actions=(),
    dry_run_status="dry_run_not_started",
    diagnosis_summary="Base diagnosis summary.",
    expected_checks=("inspect_metadata_only",),
    expected_patch_feedback="Base patch feedback proposal.",
    protected_file_status="clear",
    secret_risk_status="clear",
    path_risk_status="clear",
    network_policy_status="clear",
    write_policy_status="clear",
    owner_review_required=False,
    operator_review_required=False,
    real_execution_allowed=False,
    tool_execution_allowed=False,
    patch_apply_allowed=False,
    commit_allowed=False,
    push_allowed=False,
    rollback_required=False,
    rollback_plan_ref="",
    validation_rerun_required=False,
    recommended_next_check="inspect_metadata_only",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_debug"},
)

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


def _packet(**overrides):
    payload = dict(BASE_PACKET_KWARGS)
    payload.update(overrides)
    return build_debug_dry_run_packet_v1(**payload)


def _payload(**overrides):
    payload = to_debug_dry_run_json_safe_v1(_packet())
    payload.update(overrides)
    return payload


def _example_by_id(packet_id: str):
    for item in build_initial_debug_dry_run_examples_v1():
        if item.debug_dry_run_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.autonomous_debugging_dry_run_boundary as mod

    assert mod.HELPER_TYPE_V1 == "autonomous_debugging_dry_run_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_classifies_known_and_unknown_debug_inputs():
    assert classify_debug_input_v1(debug_input_class="manifest_mismatch") == "manifest_mismatch"
    assert classify_debug_input_v1(debug_input_class="mystery") == "unknown_debug_input"
    assert classify_debug_input_v1(input_summary="ImportError: No module named x") == "runtime_error_summary"


def test_derives_hypotheses_from_packet_metadata():
    packet = _packet(input_summary="ImportError: No module named weslr_x", debug_input_class="runtime_error_summary")
    hypotheses = derive_debug_hypotheses_v1(packet)
    assert "import_error_hypothesis" in hypotheses
    assert "missing_dependency_hypothesis" in hypotheses
    assert all(h in ALLOWED_HYPOTHESIS_TYPES_V1 for h in hypotheses)


def test_selects_actions_for_tool_and_validation_paths():
    tool_packet = _packet(tool_use_packet_ref="tool_use_packet_v1")
    validation_packet = _packet(validation_packet_ref="validation_packet_v1")
    assert "defer_to_tool_executor_boundary" in select_debug_dry_run_actions_v1(tool_packet)
    assert "defer_to_validation_runner" in select_debug_dry_run_actions_v1(validation_packet)


def test_builds_deterministic_debug_packet():
    first = _packet()
    second = _packet()
    assert first == second
    assert isinstance(first, DebugDryRunPacket)
    assert first.real_execution_allowed is False
    assert first.tool_execution_allowed is False
    assert first.patch_apply_allowed is False


def test_summarizes_packet():
    summary = summarize_debug_dry_run_packet_v1(_packet())
    assert isinstance(summary, DebugDryRunSummary)
    assert summary.debug_dry_run_packet_id == "base_debug_v1"
    assert summary.debug_input_class == "test_failure_report"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_debug_dry_run_json_safe_v1(raw)

    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    text = str(summarize_debug_dry_run_packet_v1(_packet())).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_all_initial_examples_exist():
    ids = {item.debug_dry_run_packet_id for item in build_initial_debug_dry_run_examples_v1()}
    assert ids == {
        "unit_test_failure_dry_run_v1",
        "import_error_dependency_check_v1",
        "manifest_mismatch_review_v1",
        "protected_file_owner_operator_review_v1",
        "secret_risk_blocks_escalation_v1",
        "release_gate_failure_rerun_v1",
        "patch_feedback_proposal_only_v1",
        "tool_deferred_to_executor_v1",
        "repeated_failure_rollback_review_v1",
        "network_dependent_debug_blocked_v1",
        "user_reported_bug_hypothesis_only_v1",
        "validation_pass_not_correctness_v1",
        "dry_run_cannot_commit_or_push_v1",
        "dry_run_cannot_write_weslr_v1",
        "poisoned_external_suggestion_blocked_v1",
    }


@pytest.mark.parametrize(
    "packet_id, expected_valid",
    [
        ("unit_test_failure_dry_run_v1", True),
        ("import_error_dependency_check_v1", True),
        ("manifest_mismatch_review_v1", True),
        ("protected_file_owner_operator_review_v1", True),
        ("secret_risk_blocks_escalation_v1", True),
        ("release_gate_failure_rerun_v1", True),
        ("patch_feedback_proposal_only_v1", True),
        ("tool_deferred_to_executor_v1", True),
        ("repeated_failure_rollback_review_v1", True),
        ("network_dependent_debug_blocked_v1", True),
        ("user_reported_bug_hypothesis_only_v1", True),
        ("validation_pass_not_correctness_v1", True),
        ("dry_run_cannot_commit_or_push_v1", True),
        ("dry_run_cannot_write_weslr_v1", True),
        ("poisoned_external_suggestion_blocked_v1", True),
    ],
)
def test_initial_examples_validate_as_expected(packet_id: str, expected_valid: bool):
    packet = _example_by_id(packet_id)
    assert validate_debug_dry_run_packet_v1(packet) is expected_valid


def test_unknown_debug_input_fails_closed():
    with pytest.raises(ValidationError, match="unknown_debug_input_promoted_as_valid"):
        validate_debug_dry_run_packet_v1(_payload(debug_input_class="mystery"))


def test_unknown_status_action_and_hypothesis_fail_closed():
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_debug_dry_run_packet_v1(_payload(dry_run_status="mystery_status"))
    with pytest.raises(ValidationError, match="unknown_dry_run_action_promoted_as_valid"):
        validate_debug_dry_run_packet_v1(_payload(proposed_dry_run_actions=("mystery_action",)))
    with pytest.raises(ValidationError, match="unknown_hypothesis_promoted_as_valid"):
        validate_debug_dry_run_packet_v1(_payload(hypotheses=("mystery_hypothesis",)))


@pytest.mark.parametrize(
    "field_name",
    [
        "real_execution_allowed",
        "tool_execution_allowed",
        "patch_apply_allowed",
        "commit_allowed",
        "push_allowed",
        "writes_state",
        "runtime_authority",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ],
)
def test_forbidden_true_flags_fail_validation(field_name: str):
    payload = _packet(**{field_name: True})
    with pytest.raises(ValidationError):
        validate_debug_dry_run_packet_v1(payload)


def test_missing_validation_packet_defers():
    packet = _packet(validation_packet_ref="", dry_run_status="dry_run_blocked_missing_validation")
    assert validate_debug_dry_run_packet_v1(packet)


def test_patch_feedback_path_remains_proposal_only():
    packet = _packet(debug_input_class="patch_feedback_packet", patch_feedback_packet_ref="patch_feedback_packet_x")
    assert "propose_patch_feedback" in select_debug_dry_run_actions_v1(packet)


def test_tool_required_step_defers_to_executor_boundary():
    packet = _packet(tool_use_packet_ref="tool_use_packet_x")
    assert "defer_to_tool_executor_boundary" in select_debug_dry_run_actions_v1(packet)


def test_secret_path_and_protected_file_risks_block_or_require_review():
    secret_packet = _packet(secret_risk_status="blocked")
    protected_packet = _packet(protected_file_status="blocked", owner_review_required=True, operator_review_required=True)
    assert validate_debug_dry_run_packet_v1(secret_packet)
    assert validate_debug_dry_run_packet_v1(protected_packet)


def test_repeated_unresolved_failure_triggers_review():
    packet = _packet(rollback_required=True, rollback_plan_ref="rollback_plan_v1")
    actions = select_debug_dry_run_actions_v1(packet)
    assert "propose_rollback_review" in actions


def test_no_subprocess_shell_or_file_io_exists_in_helper_source():
    import weslr.autonomous_debugging_dry_run_boundary as mod

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
