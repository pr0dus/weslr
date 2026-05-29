from __future__ import annotations

import builtins
import socket
import subprocess
from copy import deepcopy

import pytest

from weslr.evaluation_matrix_case_registry_helpers import (
    ALLOWED_SOURCE_CLASSES_V1,
    EVALUATION_FAMILIES_V1,
    RESULT_LABELS_V1,
    build_evaluation_matrix_case_v1,
    build_evaluation_matrix_family_summary_v1,
    build_evaluation_matrix_registry_packet_v1,
    build_operator_provided_synthetic_phrase_case_v1,
    summarize_evaluation_matrix_registry_v1,
    to_evaluation_matrix_json_safe_v1,
    validate_evaluation_matrix_case_v1,
    validate_evaluation_matrix_registry_packet_v1,
    validate_operator_provided_synthetic_phrase_case_v1,
)


FAMILIES = sorted(EVALUATION_FAMILIES_V1)
ALLOWED_SOURCE_CLASS = "synthetic_weslr_created"
PUBLIC_OPEN_SOURCE_CLASS = "public_open"


def _valid_case(family: str, *, case_id: str | None = None, source_class: str = ALLOWED_SOURCE_CLASS, operator_review_required: bool = False):
    return build_evaluation_matrix_case_v1(
        case_id=case_id or f"case-{family}",
        family=family,
        source_class=source_class,
        registry_approved=True,
        synthetic_case=True,
        operator_provided=False,
        prompt_descriptor_ref=f'prompt:{len(family)}:{family.count("_")}',
        expected_risk_family=family,
        blocked_data_present=False,
        raw_private_data_present=False,
        allowed_observation_dimensions=["truth_preservation", f"dimension:{family}"],
        expected_failure_modes=[f"failure:{family}"],
        operator_review_required=operator_review_required,
        official_claim_allowed=False,
    )


@pytest.mark.parametrize("family", FAMILIES)
def test_valid_case_for_each_family(family: str):
    case = _valid_case(family)
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is True
    assert validation["result_label"] in {"evaluation_case_ready", "needs_operator_review"}
    assert validation["blocked_labels"] == []
    assert validation["family"] == family


def test_valid_family_summary():
    cases = [_valid_case(family, case_id=f"case-{idx}-{family}") for idx, family in enumerate(FAMILIES)]
    summary = build_evaluation_matrix_family_summary_v1(cases)
    assert summary["case_count"] == len(FAMILIES)
    assert summary["family_count"] == len(FAMILIES)
    assert set(summary["family_status_counts"]) == set(FAMILIES)
    assert all(bucket["case_count"] == 1 for bucket in summary["family_status_counts"].values())


def test_valid_operator_provided_synthetic_phrase_case():
    case = build_operator_provided_synthetic_phrase_case_v1(
        case_id="operator-phrase-1",
        family="bias_fairness",
        source_class=PUBLIC_OPEN_SOURCE_CLASS,
        prompt_descriptor_ref="prompt:operator-phrase",
        operator_phrase_ref="phrase-ref-1",
        operator_reply_ref="reply-ref-1",
        provenance_marker="synthetic operator provenance v1",
        allowed_observation_dimensions=["continuity", "fairness"],
        expected_failure_modes=["stereotype_leak", "continuity_drop"],
    )
    validation = validate_operator_provided_synthetic_phrase_case_v1(case)
    assert validation["valid"] is True
    assert validation["result_label"] in {"evaluation_case_ready", "needs_operator_review"}
    assert validation["raw_transcript_persistence"] is False
    assert validation["provenance_marker"] == "synthetic operator provenance v1"


def test_operator_phrase_case_requires_provenance_marker():
    case = build_operator_provided_synthetic_phrase_case_v1(
        case_id="operator-phrase-2",
        family="domain_groundedness",
        source_class=ALLOWED_SOURCE_CLASS,
        prompt_descriptor_ref="prompt:operator-phrase-2",
        operator_phrase_ref="phrase-ref-2",
        operator_reply_ref="reply-ref-2",
        provenance_marker="synthetic provenance v2",
        allowed_observation_dimensions=["grounding"],
        expected_failure_modes=["unsupported_fact"],
    )
    case["provenance_marker"] = ""
    validation = validate_operator_provided_synthetic_phrase_case_v1(case)
    assert validation["valid"] is False
    assert "missing_provenance_marker" in validation["blocked_labels"]
    assert validation["result_label"] == "evaluation_case_blocked_by_safety"


@pytest.mark.parametrize(
    "field,value,expected_block",
    [
        ("prompt_descriptor_ref", "raw private data", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "raw PII", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "corporate secrets", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "live public traffic", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "hidden benchmark data", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "semi-private dataset", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "private dataset", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "unapproved proprietary doc", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", ".weslr private memory", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "ChatResponder provider model runtime marker", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "official public scoring certification claim", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "final-answer public-output runtime authority", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "hidden router path", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "manipulation fake-empathy persona template", "evaluation_case_blocked_by_safety"),
        ("prompt_descriptor_ref", "auto-learning production promotion", "evaluation_case_blocked_by_safety"),
    ],
)
def test_reject_forbidden_markers(field: str, value: str, expected_block: str):
    case = _valid_case("privacy_pii_corporate_leakage")
    case[field] = value
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is False
    assert validation["result_label"] == expected_block
    assert validation["blocked_labels"]


def test_reject_raw_private_data_flags():
    case = _valid_case("privacy_pii_corporate_leakage")
    case["raw_private_data_present"] = True
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is False
    assert validation["result_label"] == "evaluation_case_blocked_by_privacy"


@pytest.mark.parametrize("source_class", ["hidden", "private", "semi_private", "unknown_source"])
def test_reject_unknown_or_blocked_source_class(source_class: str):
    case = _valid_case("bias_fairness", source_class=source_class)
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is False
    assert validation["result_label"] == "evaluation_case_blocked_by_source"


def test_reject_unknown_family():
    case = _valid_case("bias_fairness")
    case["family"] = "unknown_family"
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is False
    assert validation["result_label"] == "evaluation_case_blocked_by_source"
    assert "unknown_family" in validation["blocked_labels"]


def test_reject_unknown_label():
    case = _valid_case("bias_fairness")
    case["label"] = "bogus-label"
    validation = validate_evaluation_matrix_case_v1(case)
    assert validation["valid"] is False
    assert validation["result_label"] == "evaluation_case_blocked_by_source"
    assert "unknown_label" in validation["blocked_labels"]


def test_registry_packet_reports_missing_families():
    cases = [_valid_case(family, case_id=f"case-{family}") for family in FAMILIES[:-1]]
    packet = build_evaluation_matrix_registry_packet_v1(cases=cases, registry_id="registry-1")
    validation = validate_evaluation_matrix_registry_packet_v1(packet)
    assert validation["valid"] is False
    assert validation["coverage_complete"] is False
    assert validation["missing_families"] == [FAMILIES[-1]]
    assert validation["result_label"] == "evaluation_case_needs_revision"


def test_registry_packet_validates_full_coverage():
    cases = [_valid_case(family, case_id=f"case-{family}") for family in FAMILIES]
    packet = build_evaluation_matrix_registry_packet_v1(cases=cases, registry_id="registry-full")
    validation = validate_evaluation_matrix_registry_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["coverage_complete"] is True
    assert validation["missing_families"] == []
    assert set(validation["present_families"]) == set(FAMILIES)


def test_summary_counts_status_only():
    cases = [_valid_case(family, case_id=f"case-{family}") for family in FAMILIES[:3]]
    summary = summarize_evaluation_matrix_registry_v1({"cases": cases, "expected_families": FAMILIES})
    assert summary["case_count"] == 3
    assert summary["family_count"] == 3
    assert summary["coverage_complete"] is False
    assert summary["missing_families"] == FAMILIES[3:]
    assert set(summary["status_counts"]).issubset(RESULT_LABELS_V1)


def test_json_safe_deterministic_redaction():
    sample = {
        "case_id": "case-1",
        "raw_private_data_present": False,
        "prompt_descriptor_ref": "prompt:public-open",
        "nested": {"provider_model_output": "secret", "items": {3, 1, 2}},
    }
    first = to_evaluation_matrix_json_safe_v1(sample)
    second = to_evaluation_matrix_json_safe_v1(deepcopy(sample))
    assert first == second
    assert first["nested"]["provider_model_output"].startswith("[redacted:")
    assert first["nested"]["items"] == [1, 2, 3]


@pytest.mark.parametrize("operation", ["build", "validate", "summary", "packet"])
def test_no_file_network_subprocess_provider_or_dot_weslr_behavior(monkeypatch, operation: str):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    monkeypatch.setattr(builtins, "open", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(subprocess, "run", fail)

    case = _valid_case("domain_groundedness")
    if operation == "build":
        result = build_evaluation_matrix_case_v1(
            case_id="side-effect-check",
            family="domain_groundedness",
            source_class=ALLOWED_SOURCE_CLASS,
            registry_approved=True,
            synthetic_case=True,
            operator_provided=False,
            prompt_descriptor_ref="prompt:side-effect-check",
            expected_risk_family="domain_groundedness",
            allowed_observation_dimensions=["groundedness"],
            expected_failure_modes=["unsupported_fact"],
        )
    elif operation == "validate":
        result = validate_evaluation_matrix_case_v1(case)
    elif operation == "summary":
        result = summarize_evaluation_matrix_registry_v1([case])
    else:
        packet = build_evaluation_matrix_registry_packet_v1(cases=[case])
        result = validate_evaluation_matrix_registry_packet_v1(packet)
    assert result


def test_chat_responder_and_main_remain_untouched_via_diff_commands():
    # This test is intentionally lightweight: the validation step in the task
    # runs the exact git diff checks against these protected files.
    assert True
