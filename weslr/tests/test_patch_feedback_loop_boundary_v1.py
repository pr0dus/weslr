from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.patch_feedback_loop_boundary import (
    ALLOWED_FAILURE_CLASSES_V1,
    ALLOWED_PROPOSAL_STATUSES_V1,
    ALLOWED_PROPOSAL_TYPES_V1,
    PatchFeedbackPacket,
    PatchFeedbackSummary,
    ValidationError,
    build_initial_patch_feedback_examples_v1,
    build_patch_feedback_packet_v1,
    classify_patch_failure_v1,
    evaluate_patch_retry_budget_v1,
    select_patch_proposal_v1,
    summarize_patch_feedback_packet_v1,
    to_patch_feedback_json_safe_v1,
    validate_patch_feedback_packet_v1,
)


BASE_PACKET_KWARGS = dict(
    patch_feedback_packet_id="base_patch_feedback_v1",
    validation_packet_ref="validation_packet_base_v1",
    candidate_source_ref="candidate_source_base_v1",
    artifact_provenance_ref="artifact_provenance_base_v1",
    file_manifest_ref="file_manifest_base_v1",
    failure_class="unit_test_failure",
    failed_check_refs=("unit_test_failure_v1",),
    warning_refs=(),
    proposal_type="source_fix_proposal",
    proposal_status="proposal_created",
    proposal_summary="base patch feedback proposal",
    affected_path_summaries=("weslr/example_module.py",),
    protected_file_status="clear",
    secret_risk_status="not_detected",
    network_policy_status="not_required",
    write_policy_status="not_required",
    provenance_status="present",
    retry_count=0,
    max_retries=3,
    retry_allowed=False,
    repeated_failure_detected=False,
    rollback_required=False,
    rollback_plan_ref="rollback_plan_base_v1",
    owner_review_required=False,
    operator_review_required=False,
    patch_apply_allowed=False,
    commit_allowed=False,
    push_allowed=False,
    validation_rerun_required=True,
    artifact_export_allowed=False,
    tool_execution_allowed=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    recommended_next_check="review_patch_feedback_metadata",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_patch_feedback"},
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


def _packet(**overrides):
    payload = dict(BASE_PACKET_KWARGS)
    payload.update(overrides)
    return build_patch_feedback_packet_v1(**payload)


def _packet_payload(**overrides):
    payload = to_patch_feedback_json_safe_v1(_packet())
    payload.update(overrides)
    return payload


def _example_by_id(packet_id: str):
    for item in build_initial_patch_feedback_examples_v1():
        if item.patch_feedback_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.patch_feedback_loop_boundary as mod

    assert mod.HELPER_TYPE_V1 == "patch_feedback_loop_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_classifies_known_and_unknown_patch_failures():
    assert classify_patch_failure_v1(failure_class="unit_test_failure") == "unit_test_failure"
    assert classify_patch_failure_v1(failure_class="mystery_failure") == "unknown_validation_failure"


def test_builds_deterministic_patch_feedback_packet():
    first = _packet()
    second = _packet()

    assert first == second
    assert isinstance(first, PatchFeedbackPacket)
    assert first.patch_apply_allowed is False
    assert first.commit_allowed is False
    assert first.push_allowed is False


def test_selects_patch_proposal_for_syntax_and_unit_test_failures():
    syntax = select_patch_proposal_v1(
        PatchFeedbackPacket(
            **{
                **BASE_PACKET_KWARGS,
                "failure_class": "syntax_failure",
                "proposal_type": "unknown_patch_proposal",
                "proposal_status": "not_attempted",
            }
        )
    )
    unit = select_patch_proposal_v1(
        PatchFeedbackPacket(
            **{
                **BASE_PACKET_KWARGS,
                "failure_class": "unit_test_failure",
                "proposal_type": "unknown_patch_proposal",
                "proposal_status": "not_attempted",
            }
        )
    )

    assert syntax.proposal_type == "metadata_fix_proposal"
    assert unit.proposal_type == "source_fix_proposal"


def test_evaluates_retry_budget_for_available_and_exhausted_paths():
    available = evaluate_patch_retry_budget_v1(_packet(retry_count=0, max_retries=2))
    exhausted = evaluate_patch_retry_budget_v1(_packet(retry_count=1, max_retries=1))

    assert available.retry_allowed is True
    assert available.proposal_status == "retry_budget_available"
    assert exhausted.retry_allowed is False
    assert exhausted.proposal_status == "retry_budget_exhausted"


def test_evaluates_repeated_failure_into_rollback_and_review():
    repeated = evaluate_patch_retry_budget_v1(_packet(retry_count=2, max_retries=5, repeated_failure_detected=False))

    assert repeated.retry_allowed is False
    assert repeated.repeated_failure_detected is True
    assert repeated.rollback_required is True
    assert repeated.proposal_status == "rollback_required"


def test_validates_normal_packet():
    assert validate_patch_feedback_packet_v1(_packet()) is True


def test_summarizes_packet():
    summary = summarize_patch_feedback_packet_v1(_packet())
    assert isinstance(summary, PatchFeedbackSummary)
    assert summary.patch_feedback_packet_id == "base_patch_feedback_v1"
    assert summary.proposal_type == "source_fix_proposal"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {
        "packet": {
            "name": "alpha",
            "nested": [1, {"two": 2}],
            "flags": {"a", "b"},
        }
    }
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_patch_feedback_json_safe_v1(raw)

    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_patch_feedback_packet_v1(_packet())
    text = str(summary).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_all_initial_examples_exist():
    ids = {item.patch_feedback_packet_id for item in build_initial_patch_feedback_examples_v1()}
    assert ids == {
        "unit_test_failure_source_fix_v1",
        "syntax_failure_metadata_fix_v1",
        "protected_file_diff_blocked_v1",
        "secret_risk_blocked_v1",
        "retry_budget_exhausted_v1",
        "repeated_failure_rollback_v1",
        "missing_manifest_fix_v1",
        "release_gate_rerun_v1",
        "patch_proposal_no_commit_push_v1",
        "passed_rerun_no_public_claim_v1",
        "network_policy_block_v1",
        "write_policy_block_v1",
        "poisoned_external_suggestion_blocked_v1",
        "protected_runtime_path_review_v1",
        "no_patch_needed_passed_cleanly_v1",
    }


@pytest.mark.parametrize(
    "packet_id, expected_status",
    [
        ("unit_test_failure_source_fix_v1", True),
        ("syntax_failure_metadata_fix_v1", True),
        ("protected_file_diff_blocked_v1", True),
        ("secret_risk_blocked_v1", True),
        ("retry_budget_exhausted_v1", True),
        ("repeated_failure_rollback_v1", True),
        ("missing_manifest_fix_v1", True),
        ("release_gate_rerun_v1", True),
        ("patch_proposal_no_commit_push_v1", True),
        ("passed_rerun_no_public_claim_v1", True),
        ("network_policy_block_v1", True),
        ("write_policy_block_v1", True),
        ("poisoned_external_suggestion_blocked_v1", True),
        ("protected_runtime_path_review_v1", True),
        ("no_patch_needed_passed_cleanly_v1", True),
    ],
)
def test_initial_examples_validate_as_expected(packet_id: str, expected_status: bool):
    packet = _example_by_id(packet_id)
    assert validate_patch_feedback_packet_v1(packet) is expected_status


def test_initial_examples_cover_required_outcomes():
    assert _example_by_id("unit_test_failure_source_fix_v1").proposal_type == "source_fix_proposal"
    assert _example_by_id("syntax_failure_metadata_fix_v1").proposal_type == "metadata_fix_proposal"
    assert _example_by_id("protected_file_diff_blocked_v1").proposal_status == "blocked_protected_file"
    assert _example_by_id("secret_risk_blocked_v1").proposal_status == "blocked_secret_risk"
    assert _example_by_id("retry_budget_exhausted_v1").proposal_status == "retry_budget_exhausted"
    assert _example_by_id("repeated_failure_rollback_v1").rollback_required is True
    assert _example_by_id("missing_manifest_fix_v1").proposal_type == "manifest_fix_proposal"
    assert _example_by_id("release_gate_rerun_v1").validation_rerun_required is True
    assert _example_by_id("patch_proposal_no_commit_push_v1").commit_allowed is False
    assert _example_by_id("passed_rerun_no_public_claim_v1").public_claim_allowed is False
    assert _example_by_id("network_policy_block_v1").proposal_status == "blocked_network_policy"
    assert _example_by_id("write_policy_block_v1").proposal_status == "blocked_write_policy"
    assert _example_by_id("poisoned_external_suggestion_blocked_v1").proposal_status == "blocked_secret_risk"
    assert _example_by_id("protected_runtime_path_review_v1").owner_review_required is True
    assert _example_by_id("no_patch_needed_passed_cleanly_v1").proposal_type == "no_patch_needed"


@pytest.mark.parametrize(
    "field_name",
    [
        "patch_apply_allowed",
        "commit_allowed",
        "push_allowed",
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
    payload = _packet_payload(**{field_name: True})
    with pytest.raises(ValidationError):
        validate_patch_feedback_packet_v1(payload)


def test_unknown_failure_class_fails_closed():
    with pytest.raises(ValidationError, match="unknown_failure_class_promoted_as_valid"):
        validate_patch_feedback_packet_v1(
            _packet_payload(
                failure_class="mystery_failure",
                failed_check_refs=(),
                warning_refs=(),
                affected_path_summaries=(),
            )
        )


def test_unknown_proposal_type_fails_closed():
    with pytest.raises(ValidationError, match="unknown_proposal_type_promoted_as_valid"):
        validate_patch_feedback_packet_v1(_packet_payload(proposal_type="unknown_patch_proposal"))


def test_unknown_status_fails_closed():
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_patch_feedback_packet_v1(_packet_payload(proposal_status="unknown_status"))


def test_secret_risk_blocks_promotion():
    with pytest.raises(ValidationError, match="secret_risk_blocks_promotion"):
        validate_patch_feedback_packet_v1(
            _packet_payload(
                secret_risk_status="blocked",
                proposal_type="source_fix_proposal",
            )
        )


def test_protected_file_requires_review():
    with pytest.raises(ValidationError, match="protected_file_requires_owner_operator_review"):
        validate_patch_feedback_packet_v1(
            _packet_payload(
                protected_file_status="blocked",
                owner_review_required=False,
                operator_review_required=False,
            )
        )


def test_retry_budget_exhaustion_and_repeated_failure_are_distinct():
    exhausted = evaluate_patch_retry_budget_v1(_packet(retry_count=1, max_retries=1))
    repeated = evaluate_patch_retry_budget_v1(_packet(retry_count=2, max_retries=5, repeated_failure_detected=False))

    assert exhausted.proposal_status == "retry_budget_exhausted"
    assert repeated.proposal_status == "rollback_required"


def test_rollback_required_without_rollback_plan_fails():
    with pytest.raises(ValidationError, match="rollback_required_without_plan"):
        validate_patch_feedback_packet_v1(_packet(rollback_required=True, rollback_plan_ref=""))


def test_missing_provenance_blocks_promotion():
    with pytest.raises(ValidationError, match="missing_provenance_blocks_promotion"):
        validate_patch_feedback_packet_v1(
            _packet_payload(
                provenance_status="missing",
                artifact_provenance_ref="",
                owner_review_required=True,
                operator_review_required=True,
                proposal_type="source_fix_proposal",
            )
        )


def test_validation_rerun_required_where_future_patch_application_would_be_needed():
    packet = _packet(failure_class="unit_test_failure")
    assert packet.validation_rerun_required is True
    assert packet.proposal_type == "source_fix_proposal"


def test_no_patch_needed_stays_no_patch_and_no_rerun():
    packet = _example_by_id("no_patch_needed_passed_cleanly_v1")
    assert packet.proposal_type == "no_patch_needed"
    assert packet.validation_rerun_required is False
    assert packet.retry_allowed is False


def test_source_inspection_finds_no_subprocess_shell_or_file_io_calls():
    import weslr.patch_feedback_loop_boundary as mod

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
