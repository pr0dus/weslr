from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

from weslr.controlled_real_answer_sample_run import (
    ALLOWED_SOURCE_CLASSES,
    EXECUTION_MODE,
    MAX_FIRST_RUN_CASES,
    MIN_FIRST_RUN_CASES,
    build_controlled_real_answer_adapter_contract_v1,
    build_controlled_real_answer_observation_stub_v1,
    build_controlled_real_answer_sample_case_v1,
    build_controlled_real_answer_sample_review_packet_v1,
    build_controlled_real_answer_sample_run_plan_v1,
    summarize_controlled_real_answer_sample_run_v1,
    to_controlled_real_answer_sample_json_safe_v1,
    validate_controlled_real_answer_sample_preconditions_v1,
    validate_controlled_real_answer_sample_run_plan_v1,
)


def _valid_case(**overrides):
    payload = {
        "case_id": "case-1",
        "source_class": "public_open",
        "registry_approved": True,
        "prompt_descriptor_ref": "prompt::case-1",
        "expected_observation_dimensions": ["truth_kernel_preservation", "response_fit"],
    }
    payload.update(overrides)
    return build_controlled_real_answer_sample_case_v1(**payload)


def _valid_adapter(**overrides):
    payload = {
        "adapter_id": "adapter-1",
        "adapter_type": "future-controlled-adapter",
        "run_id": "run-1",
        "commit": "33c10c2",
        "source_case_id": "case-1",
        "source_class": "public_open",
        "registry_approved": True,
        "operator_approval_ref": "op-approval-1",
        "answer_sample_ref": "sample-1",
        "raw_answer_stored": False,
        "redaction_status": "redacted",
        "execution_mode": EXECUTION_MODE,
        "runtime_authority": False,
        "final_answer_authority": False,
        "public_output_authority": False,
    }
    payload.update(overrides)
    return build_controlled_real_answer_adapter_contract_v1(**payload)


def _valid_plan(case_count: int = 3, **overrides):
    cases = [_valid_case(case_id=f"case-{i+1}") for i in range(case_count)]
    payload = {
        "cases": cases,
        "run_id": "run-1",
        "adapter_review_ref": "review-1",
        "operator_approval_ref": "op-approval-1",
        "abort_path": "abort::defined",
        "rollback_policy": "rollback::defined",
    }
    payload.update(overrides)
    return build_controlled_real_answer_sample_run_plan_v1(**payload)


def test_constants_are_present():
    assert ALLOWED_SOURCE_CLASSES == {"public_open", "synthetic_weslr_created"}
    assert EXECUTION_MODE == "controlled_internal"
    assert MIN_FIRST_RUN_CASES == 3
    assert MAX_FIRST_RUN_CASES == 5


def test_build_sample_case_is_metadata_only():
    case = _valid_case()
    assert case["case_type"]
    assert case["metadata_only"] is True
    assert case["internal_only"] is True
    assert case["raw_answer_stored"] is False
    assert case["source_class"] == "public_open"


def test_build_adapter_contract_is_metadata_only_and_no_execution():
    adapter = _valid_adapter()
    assert adapter["adapter_contract_type"]
    assert adapter["execution_mode"] == EXECUTION_MODE
    assert adapter["runtime_authority"] is False
    assert adapter["final_answer_authority"] is False
    assert adapter["public_output_authority"] is False
    assert adapter["raw_answer_stored"] is False


def test_valid_preconditions_pass():
    preconditions = validate_controlled_real_answer_sample_preconditions_v1(
        {
            "case": _valid_case(),
            "adapter_contract": {
                "adapter_review_ref": "review-1",
                "operator_approval_ref": "op-approval-1",
                "redaction_status": "redacted",
                "raw_answer_stored": False,
                "execution_mode": EXECUTION_MODE,
            },
            "source_lineage": {
                "source_class": "public_open",
                "registry_approved": True,
                "source_lineage_complete": True,
            },
            "abort_path": "abort::defined",
            "rollback_policy": "rollback::defined",
            "raw_answer_stored": False,
            "execution_mode": EXECUTION_MODE,
            "source_lineage_complete": True,
        }
    )
    assert preconditions["valid"] is True
    assert preconditions["blocked"] is False
    assert preconditions["precondition_status"] == "valid"
    assert preconditions["raw_answer_stored"] is False

def test_preconditions_reject_nested_authority_flags():
    preconditions = validate_controlled_real_answer_sample_preconditions_v1(
        {
            "case": _valid_case(),
            "adapter_contract": {
                "adapter_review_ref": "review-1",
                "operator_approval_ref": "op-approval-1",
                "redaction_status": "redacted",
                "raw_answer_stored": False,
                "execution_mode": EXECUTION_MODE,
                "runtime_authority": True,
                "final_answer_authority": True,
                "public_output_authority": True,
            },
            "source_lineage": {
                "source_class": "public_open",
                "registry_approved": True,
                "source_lineage_complete": True,
            },
            "abort_path": "abort::defined",
            "rollback_policy": "rollback::defined",
            "raw_answer_stored": False,
            "execution_mode": EXECUTION_MODE,
            "source_lineage_complete": True,
        }
    )
    assert preconditions["blocked"] is True
    assert "unknown_authority_flag" in preconditions["blocked_labels"]


def test_build_plan_valid_for_three_and_five_cases():
    plan3 = _valid_plan(3)
    plan5 = _valid_plan(5)
    assert plan3["case_count"] == 3
    assert plan5["case_count"] == 5
    assert plan3["raw_answer_stored"] is False
    assert plan5["raw_answer_stored"] is False
    assert plan3["no_run_marker"] is True
    assert plan5["no_run_marker"] is True


def test_plan_rejects_too_few_or_too_many_cases():
    plan2 = _valid_plan(2)
    plan6 = _valid_plan(6)
    assert "case_count_below_minimum" in validate_controlled_real_answer_sample_run_plan_v1(plan2)["blocked_labels"]
    assert "case_count_above_maximum" in validate_controlled_real_answer_sample_run_plan_v1(plan6)["blocked_labels"]


def test_plan_rejects_private_live_hidden_and_semi_private_sources():
    bad_cases = [
        _valid_case(source_class="private"),
        _valid_case(source_class="hidden"),
        _valid_case(source_class="semi-private"),
        _valid_case(prompt_descriptor_ref="live user chat"),
    ]
    plan = build_controlled_real_answer_sample_run_plan_v1(
        bad_cases,
        run_id="run-1",
        adapter_review_ref="review-1",
        operator_approval_ref="op-approval-1",
        abort_path="abort::defined",
        rollback_policy="rollback::defined",
    )
    validation = validate_controlled_real_answer_sample_run_plan_v1(plan)
    assert validation["blocked"] is True
    assert "unknown_source_class" in validation["blocked_labels"]


def test_plan_rejects_raw_content_and_weslr_markers():
    plan = build_controlled_real_answer_sample_run_plan_v1(
        [
            _valid_case(prompt_descriptor_ref="raw prompt"),
            _valid_case(prompt_descriptor_ref="raw transcript"),
            _valid_case(prompt_descriptor_ref="raw context .weslr/private"),
        ],
        run_id="run-1",
        adapter_review_ref="review-1",
        operator_approval_ref="op-approval-1",
        abort_path="abort::defined",
        rollback_policy="rollback::defined",
    )
    validation = validate_controlled_real_answer_sample_run_plan_v1(plan)
    assert validation["blocked"] is True
    assert "raw_private_content_requested" in validation["blocked_labels"]


def test_plan_rejects_raw_answer_and_missing_approvals_and_authority():
    case = _valid_case()
    plan = build_controlled_real_answer_sample_run_plan_v1(
        [case, case, case],
        run_id="run-1",
        adapter_review_ref="",
        operator_approval_ref="",
        abort_path="",
        rollback_policy="",
        execution_mode="wrong-mode",
    )
    plan["raw_answer_stored"] = True
    plan["cases"][0]["runtime_authority"] = True
    plan["cases"][1]["final_answer_authority"] = True
    plan["cases"][2]["public_output_authority"] = True
    validation = validate_controlled_real_answer_sample_run_plan_v1(plan)
    assert validation["blocked"] is True
    assert "raw_answer_stored_true" in validation["blocked_labels"]
    assert "missing_adapter_review_ref" in validation["blocked_labels"]
    assert "missing_operator_approval_ref" in validation["blocked_labels"]
    assert "missing_abort_path" in validation["blocked_labels"]
    assert "missing_rollback_policy" in validation["blocked_labels"]
    assert "unknown_execution_mode" in validation["blocked_labels"]
    assert "unknown_authority_flag" in validation["blocked_labels"]


def test_plan_rejects_official_claims_unapproved_provider_and_hidden_router_markers():
    plan = build_controlled_real_answer_sample_run_plan_v1(
        [
            _valid_case(prompt_descriptor_ref="official Turing claim"),
            _valid_case(prompt_descriptor_ref="intelligence certification"),
            _valid_case(prompt_descriptor_ref="public readiness and hidden router production auto-learning"),
        ],
        run_id="run-1",
        adapter_review_ref="review-1",
        operator_approval_ref="op-approval-1",
        abort_path="abort::defined",
        rollback_policy="rollback::defined",
    )
    validation = validate_controlled_real_answer_sample_run_plan_v1(plan)
    assert validation["blocked"] is True


def test_observation_stub_contains_answer_sample_ref_only_no_raw_answer():
    stub = build_controlled_real_answer_observation_stub_v1(
        observation_id="obs-1",
        run_id="run-1",
        answer_sample_ref="sample-1",
        source_case_id="case-1",
        source_class="public_open",
        redaction_status="redacted",
        expected_observation_dimensions=["response_fit"],
    )
    assert stub["answer_sample_ref"] == "sample-1"
    assert stub["raw_answer_stored"] is False
    assert "raw_answer" not in stub


def test_review_packet_has_no_run_marker_and_denied_authority_flags():
    plan = _valid_plan(3)
    plan["cases"][0]["public_live_authority"] = True
    preconditions = validate_controlled_real_answer_sample_preconditions_v1(
        {
            "case": plan["cases"][0],
            "adapter_contract": {
                "adapter_review_ref": "review-1",
                "operator_approval_ref": "op-approval-1",
                "redaction_status": "redacted",
                "raw_answer_stored": False,
            },
            "source_lineage": {
                "source_class": "public_open",
                "registry_approved": True,
                "source_lineage_complete": True,
            },
            "abort_path": "abort::defined",
            "rollback_policy": "rollback::defined",
            "raw_answer_stored": False,
            "source_lineage_complete": True,
        }
    )
    packet = build_controlled_real_answer_sample_review_packet_v1(
        plan=plan,
        precondition_result=preconditions,
        observation_stubs=[
            build_controlled_real_answer_observation_stub_v1(
                observation_id="obs-1",
                run_id="run-1",
                answer_sample_ref="sample-1",
                source_case_id="case-1",
                source_class="public_open",
                redaction_status="redacted",
                expected_observation_dimensions=["response_fit"],
            )
        ],
    )
    assert packet["no_run_marker"] is True
    assert packet["denied_authority_flags"]
    assert packet["operator_review_required"] is True
    assert packet["raw_answer_stored"] is False


def test_summary_is_counts_and_status_only():
    summary = summarize_controlled_real_answer_sample_run_v1(
        [
            {"blocked": False},
            {"blocked": True, "blocked_labels": ["unknown_source_class"]},
            {"blocked": True, "blocked_labels": ["raw_answer_stored_true"]},
        ]
    )
    assert summary["summary_type"]
    assert summary["total_records"] == 3
    assert summary["valid_records"] == 1
    assert summary["blocked_records"] == 2
    assert summary["raw_answer_stored"] is False


def test_json_safe_conversion_is_deterministic_and_redacts_sensitive_values():
    class Dummy:
        def __init__(self):
            self.raw_prompt = "should be redacted"
            self.nested = {"private_memory": "hidden"}

    value = {"z": 2, "a": Dummy(), "list": [3, {"prompt": "also redacted"}]}
    safe_a = to_controlled_real_answer_sample_json_safe_v1(value)
    safe_b = to_controlled_real_answer_sample_json_safe_v1(value)
    assert safe_a == safe_b
    assert safe_a["a"]["raw_prompt"] == "[redacted:raw_prompt]"
    assert safe_a["a"]["nested"]["private_memory"] == "[redacted:private_memory]"
    assert safe_a["list"][1]["prompt"] == "[redacted:prompt]"


def test_no_file_network_subprocess_provider_or_dot_weslr_behavior(monkeypatch):
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("open called")))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess called")))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess called")))
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("socket called")))

    case = _valid_case()
    adapter = _valid_adapter()
    plan = _valid_plan(3)
    assert validate_controlled_real_answer_sample_preconditions_v1(
        {
            "case": case,
            "adapter_contract": adapter,
            "source_lineage": {"source_class": "public_open", "registry_approved": True, "source_lineage_complete": True},
            "adapter_review_ref": "review-1",
            "operator_approval_ref": "op-approval-1",
            "abort_path": "abort::defined",
            "rollback_policy": "rollback::defined",
            "raw_answer_stored": False,
            "source_lineage_complete": True,
        }
    )["valid"] is True
    assert validate_controlled_real_answer_sample_run_plan_v1(plan)["valid"] is True


def test_source_text_does_not_reference_runtime_wiring():
    source = Path("weslr/controlled_real_answer_sample_run.py").read_text()
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source
    assert "main.py" not in source
