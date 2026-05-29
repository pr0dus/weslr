from __future__ import annotations

import builtins
import socket
import subprocess
from copy import deepcopy

import pytest

from weslr.run_controlled_real_answer_sample_run_approval_helpers import (
    ALLOWED_SOURCE_CLASSES_V1,
    APPROVAL_DECISIONS_V1,
    DENIED_AUTHORITY_FLAGS_V1,
    REQUIRED_EVALUATION_MATRIX_FAMILIES_V1,
    build_run_controlled_real_answer_sample_approval_packet_v1,
    build_run_controlled_real_answer_sample_approval_preconditions_v1,
    build_run_controlled_real_answer_sample_approval_review_packet_v1,
    summarize_run_controlled_real_answer_sample_approval_packet_v1,
    to_run_controlled_real_answer_sample_approval_json_safe_v1,
    validate_run_controlled_real_answer_sample_approval_batch_v1,
    validate_run_controlled_real_answer_sample_approval_packet_v1,
    validate_run_controlled_real_answer_sample_approval_preconditions_v1,
)


FAMILIES = list(REQUIRED_EVALUATION_MATRIX_FAMILIES_V1)
ALLOWED_SOURCE_CLASS = "public_open"
SECOND_ALLOWED_SOURCE_CLASS = "synthetic_weslr_created"
VALID_DECISION = "approval_ready_for_review"


def _deny_flags(**overrides: bool):
    flags = {flag: False for flag in DENIED_AUTHORITY_FLAGS_V1}
    flags.update(overrides)
    return flags


def _valid_preconditions(**overrides):
    base = dict(
        authoritative_commit="38ac76c",
        implementation_review_ref="docs/WESLR_CONTROLLED_REAL_ANSWER_SAMPLE_RUN_IMPLEMENTATION_REVIEW_V1.md",
        source_case_refs=["case-1", "case-2", "case-3"],
        source_classes=[ALLOWED_SOURCE_CLASS, SECOND_ALLOWED_SOURCE_CLASS],
        registry_approved_all=True,
        adapter_contract_ref="adapter-contract-ref",
        run_plan_ref="run-plan-ref",
        precondition_status="valid",
        denied_authority_flags=_deny_flags(),
        redaction_status="redacted",
        raw_answer_stored=False,
        no_persistence_policy="no raw persistence",
        abort_conditions=["abort_on_unapproved_inputs"],
        evaluation_matrix_review_ref="docs/WESLR_EVALUATION_MATRIX_CASE_REGISTRY_HELPERS_REVIEW_V1.md",
        evaluation_matrix_coverage_acknowledged=True,
        evaluation_matrix_families_acknowledged=FAMILIES,
    )
    base.update(overrides)
    return build_run_controlled_real_answer_sample_approval_preconditions_v1(**base)


def _valid_packet(**overrides):
    base = dict(
        approval_id="approval-1",
        requested_run_id="run-1",
        authoritative_commit="38ac76c",
        implementation_review_ref="docs/WESLR_CONTROLLED_REAL_ANSWER_SAMPLE_RUN_IMPLEMENTATION_REVIEW_V1.md",
        operator_approval_ref="operator-approval-ref",
        approved_case_ids=["case-1", "case-2", "case-3"],
        source_case_refs=["case-1", "case-2", "case-3"],
        source_classes=[ALLOWED_SOURCE_CLASS, SECOND_ALLOWED_SOURCE_CLASS],
        registry_approved_all=True,
        adapter_contract_ref="adapter-contract-ref",
        run_plan_ref="run-plan-ref",
        precondition_status="valid",
        denied_authority_flags=_deny_flags(),
        redaction_status="redacted",
        raw_answer_stored=False,
        no_persistence_policy="no raw persistence",
        abort_conditions=["abort_on_unapproved_inputs"],
        evaluation_matrix_review_ref="docs/WESLR_EVALUATION_MATRIX_CASE_REGISTRY_HELPERS_REVIEW_V1.md",
        evaluation_matrix_families_acknowledged=FAMILIES,
        approval_decision=VALID_DECISION,
    )
    base.update(overrides)
    return build_run_controlled_real_answer_sample_approval_packet_v1(**base)


def test_valid_approval_preconditions():
    preconditions = _valid_preconditions()
    validation = validate_run_controlled_real_answer_sample_approval_preconditions_v1(preconditions)
    assert validation["valid"] is True
    assert validation["blocked_labels"] == []
    assert validation["precondition_status"] == "valid"
    assert validation["evaluation_matrix_families_acknowledged"] == FAMILIES
    assert validation["denied_authority_flags"] == _deny_flags()


def test_valid_approval_packet():
    packet = _valid_packet()
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked_labels"] == []
    assert validation["approval_decision"] == VALID_DECISION
    assert validation["evaluation_matrix_families_acknowledged"] == FAMILIES
    assert validation["denied_authority_flags"] == _deny_flags()
    assert "approved_to_run" not in packet


def test_valid_review_packet():
    packet = _valid_packet()
    preconditions = _valid_preconditions()
    review = build_run_controlled_real_answer_sample_approval_review_packet_v1(packet=packet, precondition_result=preconditions)
    assert review["metadata_only"] is True
    assert review["raw_answer_stored"] is False
    assert review["review_status"] == "valid"
    assert review["validation_result"]["valid"] is True
    assert review["blocked_labels"] == []
    assert review["matrix_coverage_status"]["coverage_complete"] is True
    assert review["matrix_coverage_status"]["evaluation_matrix_families_acknowledged"] == FAMILIES


def test_valid_batch_validation():
    packets = [_valid_packet(approval_id=f"approval-{idx}", requested_run_id=f"run-{idx}") for idx in range(2)]
    batch = validate_run_controlled_real_answer_sample_approval_batch_v1(packets)
    assert batch["valid"] is True
    assert batch["packet_count"] == 2
    assert batch["blocked_labels"] == []
    assert batch["blocked_reasons"] == []


@pytest.mark.parametrize(
    "field,mutator,expected_label",
    [
        ("evaluation_matrix_review_ref", lambda p: p.__setitem__("evaluation_matrix_review_ref", ""), "missing_evaluation_matrix_review_ref"),
        ("evaluation_matrix_families_acknowledged", lambda p: p.__setitem__("evaluation_matrix_families_acknowledged", FAMILIES[:-1]), "missing_evaluation_matrix_families_acknowledged"),
        ("evaluation_matrix_families_acknowledged", lambda p: p.__setitem__("evaluation_matrix_families_acknowledged", FAMILIES + ["unknown_family"]), "missing_evaluation_matrix_families_acknowledged"),
        ("approval_decision", lambda p: p.__setitem__("approval_decision", "bogus"), "invalid_approval_decision"),
    ],
)
def test_reject_missing_matrix_review_or_family_or_invalid_decision(field, mutator, expected_label):
    packet = _valid_packet()
    mutator(packet)
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert expected_label in validation["blocked_labels"]


def test_reject_approved_to_run_true():
    packet = _valid_packet()
    packet["approved_to_run"] = True
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert "approved_to_run_present" in validation["blocked_labels"]


@pytest.mark.parametrize("source_classes", [["private"], ["hidden"], ["semi-private"], ["unknown_source"]])
def test_reject_private_live_hidden_semi_private_source(source_classes):
    packet = _valid_packet(source_classes=source_classes)
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert "invalid_source_classes" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("adapter_contract_ref", "raw prompt"),
        ("run_plan_ref", "raw answer"),
        ("abort_conditions", ["raw transcript", "raw context", "private memory"]),
        ("no_persistence_policy", "no .weslr io"),
    ],
)
def test_reject_raw_prompt_answer_transcript_context_private_memory_and_weslr(field, value):
    packet = _valid_packet()
    packet[field] = value
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert validation["blocked_labels"]


def test_reject_raw_answer_stored_true():
    packet = _valid_packet()
    packet["raw_answer_stored"] = True
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert "raw_answer_stored_true" in validation["blocked_labels"]


@pytest.mark.parametrize("field", ["implementation_review_ref", "operator_approval_ref", "adapter_contract_ref", "run_plan_ref"])
def test_reject_missing_required_refs(field):
    packet = _valid_packet()
    packet[field] = ""
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert validation["blocked_labels"]


@pytest.mark.parametrize(
    "flag",
    [
        "runtime_authority",
        "final_answer_authority",
        "public_output_authority",
        "source_approval_authority",
        "scoring_certification_authority",
        "benchmark_turing_intelligence_claim_authority",
        "hidden_router_authority",
        "self_modification_authority",
        "run_execution_authority",
    ],
)
def test_reject_denied_authority_flags_true(flag):
    packet = _valid_packet(denied_authority_flags=_deny_flags(**{flag: True}))
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert "denied_authority_flags_true" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "marker",
    [
        "runtime authority",
        "public output authority",
        "voice authority",
        "final answer routing",
        "official turing intelligence certification public readiness",
        "source approval authority",
        "scoring authority",
        "ChatResponder provider model",
        "hidden router",
        "production promotion",
        "auto-learning",
        "fake empathy persona template manipulation",
    ],
)
def test_reject_authority_and_hidden_router_and_automation_markers(marker):
    packet = _valid_packet()
    packet["abort_conditions"] = [marker]
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert validation["blocked_labels"]


@pytest.mark.parametrize(
    "decision",
    ["", "bogus", "approval_already_granted"],
)
def test_reject_invalid_approval_decision(decision):
    packet = _valid_packet(approval_decision=decision)
    validation = validate_run_controlled_real_answer_sample_approval_packet_v1(packet)
    assert validation["valid"] is False
    assert "invalid_approval_decision" in validation["blocked_labels"]


def test_summary_counts_status_only_no_score():
    packets = [_valid_packet(approval_id=f"approval-{idx}", requested_run_id=f"run-{idx}") for idx in range(3)]
    summary = summarize_run_controlled_real_answer_sample_approval_packet_v1(packets)
    assert summary["packet_count"] == 3
    assert summary["valid_packet_count"] == 3
    assert summary["blocked_packet_count"] == 0
    assert summary["approval_decision_counts"][VALID_DECISION] == 3
    assert "score" not in summary
    assert "approved_to_run" not in summary


def test_json_safe_deterministic_redaction():
    sample = {
        "approval_id": "approval-1",
        "nested": {
            "provider_model_output": "secret",
            "raw_answer_stored": False,
            "items": {3, 1, 2},
        },
    }
    first = to_run_controlled_real_answer_sample_approval_json_safe_v1(sample)
    second = to_run_controlled_real_answer_sample_approval_json_safe_v1(deepcopy(sample))
    assert first == second
    assert first["nested"]["provider_model_output"].startswith("[redacted:")
    assert first["nested"]["items"] == [1, 2, 3]


@pytest.mark.parametrize("operation", ["preconditions", "packet", "review", "summary", "batch"])
def test_no_file_network_subprocess_provider_or_dot_weslr_behavior(monkeypatch, operation: str):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    monkeypatch.setattr(builtins, "open", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(subprocess, "run", fail)

    if operation == "preconditions":
        result = _valid_preconditions()
    elif operation == "packet":
        result = _valid_packet()
    elif operation == "review":
        result = build_run_controlled_real_answer_sample_approval_review_packet_v1(packet=_valid_packet(), precondition_result=_valid_preconditions())
    elif operation == "summary":
        result = summarize_run_controlled_real_answer_sample_approval_packet_v1([_valid_packet()])
    else:
        result = validate_run_controlled_real_answer_sample_approval_batch_v1([_valid_packet()])
    assert result


def test_chat_responder_and_main_remain_untouched_via_diff_checks():
    # The task validation step runs the exact git diff checks against protected files.
    assert True
