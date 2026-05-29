from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

from weslr.response_fit_engine_helpers import (
    ANSWER_SHAPE_TYPE_V1,
    BOUNDARY_TYPE_V1,
    CHECK_LABELS_V1,
    DENIED_AUTHORITY_FLAGS_V1,
    FIT_CONFIDENCE_LABELS_V1,
    FIT_LABELS_V1,
    HUMAN_SITUATION_FRAME_TYPE_V1,
    HUMAN_SITUATION_SIGNALS_V1,
    MISMATCH_FAMILIES_V1,
    RESULT_PACKET_TYPE_V1,
    SUMMARY_TYPE_V1,
    TRUTH_KERNEL_TYPE_V1,
    build_response_fit_answer_shape_v1,
    build_response_fit_human_situation_frame_v1,
    build_response_fit_result_packet_v1,
    build_response_fit_truth_kernel_v1,
    detect_response_fit_mismatch_v1,
    summarize_response_fit_cases_v1,
    to_response_fit_json_safe_v1,
    validate_response_fit_case_v1,
)


def _valid_truth_kernel():
    return build_response_fit_truth_kernel_v1(
        {
            "fact_labels": ["stable_facts", "truth_preserved"],
            "uncertainty_labels": ["uncertainty_honesty"],
            "evidence_boundary_labels": ["evidence_depth_boundary"],
            "safety_boundary_labels": ["safety_boundary"],
            "governance_boundary_labels": ["governance_boundary"],
        }
    )


def _valid_situation_frame(**overrides):
    payload = {
        "role_context": "operator",
        "domain_context": "industrial automation",
        "expertise_level": "expert",
        "urgency_level": "normal",
        "risk_level": "medium",
        "emotional_pressure": "calm",
        "decision_burden": "moderate",
        "desired_detail_level": "medium",
        "evidence_need": "medium",
        "language_style": "plain",
        "continuity_state": "ongoing",
        "correction_history": "none",
        "trust_state": "neutral",
        "safety_boundary_need": "present",
        "industry_context": "factory",
    }
    payload.update(overrides)
    return build_response_fit_human_situation_frame_v1(payload)


def _valid_answer_shape(**overrides):
    payload = {
        "length": "medium",
        "tone": "direct",
        "structure": "bullets",
        "jargon": "plain",
        "evidence_depth": "medium",
        "warning_position": "early",
        "directness": "direct",
        "next_action": "next_step",
    }
    payload.update(overrides)
    return build_response_fit_answer_shape_v1(payload)


def _valid_case(**overrides):
    case = {
        "case_id": "fit-case-1",
        "truth_kernel": _valid_truth_kernel(),
        "human_situation_frame": _valid_situation_frame(),
        "answer_shape": _valid_answer_shape(),
        "fit_label": "fit_aligned",
        "fit_confidence_label": "high_confidence",
    }
    case.update(overrides)
    return case


def test_builders_create_expected_metadata():
    truth = _valid_truth_kernel()
    situation = _valid_situation_frame()
    shape = _valid_answer_shape()

    assert truth["truth_kernel_type"] == TRUTH_KERNEL_TYPE_V1
    assert situation["human_situation_frame_type"] == HUMAN_SITUATION_FRAME_TYPE_V1
    assert shape["answer_shape_type"] == ANSWER_SHAPE_TYPE_V1
    assert truth["raw_content_stored"] is False
    assert situation["raw_content_stored"] is False
    assert shape["raw_content_stored"] is False
    assert truth["truth_kernel_id"]
    assert situation["human_situation_frame_id"]
    assert shape["answer_shape_id"]


def test_same_truth_can_map_to_different_answer_shapes_without_changing_truth():
    truth = _valid_truth_kernel()
    situation = _valid_situation_frame(desired_detail_level="high", evidence_need="high")
    answer_a = _valid_answer_shape(length="short", tone="direct", next_action="act_now")
    answer_b = _valid_answer_shape(length="long", tone="warm", next_action="explain_more")

    case_a = _valid_case(truth_kernel=truth, human_situation_frame=situation, answer_shape=answer_a)
    case_b = _valid_case(truth_kernel=truth, human_situation_frame=situation, answer_shape=answer_b)

    validation_a = validate_response_fit_case_v1(case_a)
    validation_b = validate_response_fit_case_v1(case_b)

    assert validation_a["truth_kernel_id"] == validation_b["truth_kernel_id"]
    assert validation_a["truth_kernel"]["fact_labels"] == validation_b["truth_kernel"]["fact_labels"]
    assert validation_a["answer_shape"]["length"] != validation_b["answer_shape"]["length"]


def test_validation_blocks_raw_prompt_response_transcript_context_and_private_memory():
    case = _valid_case(
        raw_prompt="secret prompt",
        raw_response_text="secret response",
        raw_transcript="secret transcript",
        raw_context="secret context",
        private_memory="private memory",
    )
    validation = validate_response_fit_case_v1(case)

    assert validation["blocked"] is True
    assert "raw_prompt_provided" in validation["blocked_labels"]
    assert "raw_response_text_provided" in validation["blocked_labels"]
    assert "raw_transcript_provided" in validation["blocked_labels"]
    assert "raw_context_provided" in validation["blocked_labels"]
    assert "private_memory_requested" in validation["blocked_labels"]


def test_validation_blocks_dot_weslr_private_memory_and_public_authority():
    case = _valid_case(
        dot_weslr_requested=True,
        private_memory_requested=True,
        final_answer_authority=True,
        public_live_authority=True,
        voice_authority=True,
        runtime_authority=True,
        official_claim_authority=True,
    )
    validation = validate_response_fit_case_v1(case)

    assert validation["blocked"] is True
    assert "raw_private_content_requested" in validation["blocked_labels"]
    assert "public_live_authority_requested" in validation["blocked_labels"]
    assert "runtime_authority_requested" in validation["blocked_labels"]
    assert "final_answer_authority_requested" in validation["blocked_labels"]
    assert "official_claim_requested" in validation["blocked_labels"]


def test_validation_blocks_stereotype_manipulation_fake_empathy_and_templates():
    case = _valid_case(
        stereotype_assumption_requested=True,
        manipulation_logic_requested=True,
        fake_empathy_requested=True,
        template_engine_requested=True,
        role_personality_template_requested=True,
        human_imitation_requested=True,
    )
    validation = validate_response_fit_case_v1(case)

    assert validation["blocked"] is True
    assert "stereotype_assumption_requested" in validation["blocked_labels"]
    assert "manipulation_logic_requested" in validation["blocked_labels"]
    assert "fake_empathy_requested" in validation["blocked_labels"]
    assert "template_engine_requested" in validation["blocked_labels"]
    assert "human_imitation_requested" in validation["blocked_labels"]


def test_validation_blocks_unknown_signal_and_mismatch_and_check_labels():
    case = _valid_case(
        human_situation_frame=_valid_situation_frame(human_situation_signal_labels=["role_context", "unknown_signal"]),
        mismatch_families=["too_generic", "unknown_mismatch"],
        check_labels=["anti_stereotype_check", "unknown_check"],
        fit_label="unknown_fit_label",
        fit_confidence_label="unknown_confidence",
    )
    validation = validate_response_fit_case_v1(case)

    assert validation["blocked"] is True
    assert "unknown_signal_label" in validation["blocked_labels"]
    assert "unknown_mismatch_family" in validation["blocked_labels"]
    assert "unknown_check_label" in validation["blocked_labels"]
    assert "unknown_fit_label" in validation["blocked_labels"]
    assert "unknown_fit_confidence_label" in validation["blocked_labels"]


def test_industry_adaptation_metadata_allowed_without_templates():
    situation = _valid_situation_frame(industry_context="factory operator", role_context="factory operator")
    case = _valid_case(human_situation_frame=situation)
    validation = validate_response_fit_case_v1(case)

    assert validation["blocked"] is False
    assert validation["human_situation_frame"]["industry_context"] == "factory operator"
    assert "template_engine_requested" not in validation["blocked_labels"]


def test_mismatch_detection_returns_metadata_only():
    case = _valid_case(
        human_situation_frame=_valid_situation_frame(
            desired_detail_level="high",
            urgency_level="urgent",
            risk_level="safety_critical",
            emotional_pressure="stressed",
            evidence_need="high",
            language_style="plain",
            continuity_state="ongoing",
            correction_history="recent_correction",
        ),
        answer_shape=_valid_answer_shape(
            length="short",
            tone="generic",
            structure="standalone",
            jargon="technical",
            evidence_depth="low",
            warning_position="late",
            directness="soft",
            next_action="none",
        ),
    )
    mismatch = detect_response_fit_mismatch_v1(case)

    assert mismatch["helper_type"].startswith("weslr_response_fit_engine_helpers")
    assert mismatch["boundary_type"] == BOUNDARY_TYPE_V1
    assert isinstance(mismatch["mismatch_families"], list)
    assert "too_simple" in mismatch["mismatch_families"]
    assert "too_generic" in mismatch["mismatch_families"]
    assert "wrong_urgency" in mismatch["mismatch_families"]
    assert "wrong_risk_posture" in mismatch["mismatch_families"]
    assert "missed_emotional_pressure" in mismatch["mismatch_families"]
    assert "ignored_correction" in mismatch["mismatch_families"]
    assert "evidence_depth_mismatch" in mismatch["mismatch_families"]
    assert "human_perceived_ai_tone" in mismatch["mismatch_families"]


def test_result_packet_is_metadata_only_and_operator_reviewable():
    case = _valid_case(
        human_situation_frame=_valid_situation_frame(
            desired_detail_level="high",
            urgency_level="urgent",
            risk_level="safety_critical",
            emotional_pressure="stressed",
            evidence_need="high",
            correction_history="recent_correction",
        ),
        answer_shape=_valid_answer_shape(
            length="short",
            tone="generic",
            structure="standalone",
            jargon="technical",
            evidence_depth="low",
            warning_position="late",
            directness="soft",
            next_action="none",
        ),
    )
    validation = validate_response_fit_case_v1(case)
    mismatch = detect_response_fit_mismatch_v1(case)
    packet = build_response_fit_result_packet_v1(case, validation, mismatch)

    assert packet["packet_type"] == RESULT_PACKET_TYPE_V1
    assert packet["operator_review_required"] is True
    assert packet["raw_content_stored"] is False
    assert packet["metadata_only"] is True
    assert packet["internal_only"] is True
    assert packet["fit_label"] in FIT_LABELS_V1
    assert set(packet["checks"]).issubset(CHECK_LABELS_V1)
    assert isinstance(packet["mismatch_families"], list)
    assert isinstance(packet["denied_authority_flags"], list)


def test_summary_is_counts_and_status_only():
    case_ok = _valid_case()
    validation_ok = validate_response_fit_case_v1(case_ok)
    mismatch_ok = detect_response_fit_mismatch_v1(case_ok)
    packet_ok = build_response_fit_result_packet_v1(case_ok, validation_ok, mismatch_ok)

    case_blocked = _valid_case(raw_prompt="secret")
    validation_blocked = validate_response_fit_case_v1(case_blocked)
    mismatch_blocked = detect_response_fit_mismatch_v1(case_blocked)
    packet_blocked = build_response_fit_result_packet_v1(case_blocked, validation_blocked, mismatch_blocked)

    summary = summarize_response_fit_cases_v1([packet_ok, packet_blocked])

    assert summary["summary_type"] == SUMMARY_TYPE_V1
    assert summary["total_records"] == 2
    assert summary["valid_records"] == 1
    assert summary["blocked_records"] == 1
    assert isinstance(summary["fit_label_counts"], dict)
    assert isinstance(summary["case_status_counts"], dict)
    assert summary["raw_content_stored"] is False


def test_json_safe_conversion_is_deterministic_and_redacts_sensitive_values():
    class Dummy:
        def __init__(self):
            self.raw_prompt = "should be redacted"
            self.nested = {"private_memory": "hidden"}

    value = {"z": 2, "a": Dummy(), "list": [3, {"prompt": "also redacted"}]}
    safe_a = to_response_fit_json_safe_v1(value)
    safe_b = to_response_fit_json_safe_v1(value)

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
    assert validate_response_fit_case_v1(case)["valid"] is True
    assert detect_response_fit_mismatch_v1(case)["fit_label"] == "fit_aligned"


def test_source_text_does_not_reference_runtime_wiring():
    source = Path("weslr/response_fit_engine_helpers.py").read_text()
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source
    assert "main.py" not in source
