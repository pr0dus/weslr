from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

from weslr.real_answer_quality_observation_helpers import (
    ALLOWED_SOURCE_CLASSES_V1,
    BOUNDARY_TYPE_V1,
    BLOCKED_LABELS_V1,
    HUMAN_PERCEIVED_AI_SIGNALS_V1,
    OBSERVATION_DIMENSIONS_V1,
    RESULT_LABELS_V1,
    SUMMARY_TYPE_V1,
    SOURCE_LINEAGE_TYPE_V1,
    OBSERVATION_RECORD_TYPE_V1,
    REVIEW_PACKET_TYPE_V1,
    build_real_answer_quality_observation_record_v1,
    build_real_answer_quality_review_packet_v1,
    build_real_answer_quality_source_lineage_v1,
    classify_real_answer_quality_observation_v1,
    summarize_real_answer_quality_observations_v1,
    to_real_answer_quality_observation_json_safe_v1,
    validate_real_answer_quality_batch_v1,
    validate_real_answer_quality_observation_record_v1,
)


def _valid_source_lineage(**overrides):
    payload = {
        "source_case_id": "case-1",
        "run_id": "run-1",
        "source_class": "public_open",
        "registry_approved": True,
        "adapter_ref": "adapter-v1",
        "commit": "2f08106",
        "redaction_status": "redacted",
    }
    payload.update(overrides)
    return build_real_answer_quality_source_lineage_v1(**payload)


def _valid_record(**overrides):
    payload = {
        "observation_id": "obs-1",
        "run_id": "run-1",
        "source_case_id": "case-1",
        "answer_sample_ref": "sample-1",
        "raw_answer_stored": False,
        "redaction_status": "redacted",
        "truth_kernel_id": "truth::1",
        "human_situation_frame_id": "situation::1",
        "answer_shape_id": "shape::1",
        "fit_result_label": "answer_quality_fit",
        "mismatch_families": [],
        "quality_dimensions": ["truth_kernel_preservation", "response_fit"],
        "blocked_labels": [],
        "reviewer_notes_metadata_only": "",
        "recommended_existing_surface": "response_fit_engine_helpers",
        "operator_review_required": True,
        "source_lineage": _valid_source_lineage(),
        "human_perceived_ai_signals": ["generic_response"],
    }
    payload.update(overrides)
    return build_real_answer_quality_observation_record_v1(**payload)


def test_constant_coverage_is_present():
    assert SOURCE_LINEAGE_TYPE_V1
    assert OBSERVATION_RECORD_TYPE_V1
    assert REVIEW_PACKET_TYPE_V1
    assert SUMMARY_TYPE_V1
    assert ALLOWED_SOURCE_CLASSES_V1 == {"public_open", "synthetic_weslr_created"}
    assert "answer_quality_fit" in RESULT_LABELS_V1
    assert "truth_kernel_preservation" in OBSERVATION_DIMENSIONS_V1
    assert "generic_response" in HUMAN_PERCEIVED_AI_SIGNALS_V1
    assert "raw_answer_provided" in BLOCKED_LABELS_V1


def test_builders_create_expected_metadata():
    lineage = _valid_source_lineage()
    record = _valid_record(source_lineage=lineage)

    assert lineage["source_lineage_type"] == SOURCE_LINEAGE_TYPE_V1
    assert record["observation_record_type"] == OBSERVATION_RECORD_TYPE_V1
    assert record["raw_answer_stored"] is False
    assert record["source_lineage"]["source_class"] == "public_open"
    assert record["source_lineage"]["registry_approved"] is True


def test_validation_accepts_valid_record_and_classification_is_fit():
    record = _valid_record()
    validation = validate_real_answer_quality_observation_record_v1(record)
    classification = classify_real_answer_quality_observation_v1(record)

    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["fit_result_label"] == "answer_quality_fit"
    assert classification["classification_label"] == "answer_quality_fit"
    assert classification["fit_result_label"] == "answer_quality_fit"


def test_review_packet_is_metadata_only_and_operator_reviewable():
    record = _valid_record()
    validation = validate_real_answer_quality_observation_record_v1(record)
    classification = classify_real_answer_quality_observation_v1(record)
    packet = build_real_answer_quality_review_packet_v1(record, validation, classification)

    assert packet["review_packet_type"] == REVIEW_PACKET_TYPE_V1
    assert packet["operator_review_required"] is True
    assert packet["metadata_only"] is True
    assert packet["internal_only"] is True
    assert packet["raw_answer_stored"] is False
    assert packet["fit_result_label"] in RESULT_LABELS_V1
    assert set(packet["quality_dimensions"]).issubset(OBSERVATION_DIMENSIONS_V1)
    assert set(packet["human_perceived_ai_signals"]).issubset(HUMAN_PERCEIVED_AI_SIGNALS_V1)


def test_validation_blocks_raw_answer_prompt_transcript_and_context():
    record = _valid_record(
        answer_sample_ref="raw-answer",
        reviewer_notes_metadata_only="raw prompt raw transcript raw context",
        raw_answer_text="secret answer",
        raw_prompt="secret prompt",
        raw_response_text="secret response",
        raw_transcript="secret transcript",
        raw_context="secret context",
    )
    validation = validate_real_answer_quality_observation_record_v1(record)

    assert validation["blocked"] is True
    assert "raw_answer_provided" in validation["blocked_labels"]
    assert "raw_prompt_provided" in validation["blocked_labels"]
    assert "raw_response_text_provided" in validation["blocked_labels"]
    assert "raw_transcript_provided" in validation["blocked_labels"]
    assert "raw_context_provided" in validation["blocked_labels"]


def test_validation_blocks_dot_weslr_private_memory_live_chat_and_hidden_sources():
    record = _valid_record(
        answer_sample_ref=".weslr/private-memory",
        source_lineage=_valid_source_lineage(source_class="private", registry_approved=False, adapter_ref=".weslr/private-memory"),
        live_user_content_requested=True,
        provider_model_output_requested=True,
        final_answer_authority_requested=True,
        public_live_authority_requested=True,
        voice_authority_requested=True,
        runtime_authority_requested=True,
        official_claim_requested=True,
    )
    validation = validate_real_answer_quality_observation_record_v1(record)

    assert validation["blocked"] is True
    assert "unknown_source_class" in validation["blocked_labels"]
    assert "registry_not_approved" in validation["blocked_labels"]
    assert "raw_answer_provided" in validation["blocked_labels"]
    assert "live_user_content_requested" in validation["blocked_labels"] or "raw_private_content_requested" in validation["blocked_labels"]
    assert "provider_model_output_requested" in validation["blocked_labels"]
    assert "final_answer_authority_requested" in validation["blocked_labels"]
    assert "public_live_authority_requested" in validation["blocked_labels"]
    assert "runtime_authority_requested" in validation["blocked_labels"]
    assert "official_claim_requested" in validation["blocked_labels"]


def test_validation_blocks_official_claims_and_unknown_labels():
    record = _valid_record(
        source_lineage=_valid_source_lineage(source_class="synthetic_weslr_created"),
        fit_result_label="unknown_fit_label",
        quality_dimensions=["truth_kernel_preservation", "unknown_dimension"],
        mismatch_families=["unknown_mismatch"],
        human_perceived_ai_signals=["generic_response", "unknown_signal"],
        blocked_labels=["unknown_blocked_label"],
    )
    validation = validate_real_answer_quality_observation_record_v1(record)

    assert validation["blocked"] is True
    assert "unknown_fit_result_label" in validation["blocked_labels"]
    assert "unknown_dimension" in validation["blocked_labels"]
    assert "unknown_mismatch_family" in validation["blocked_labels"]
    assert "unknown_signal_label" in validation["blocked_labels"]
    assert "unknown_blocked_label" in validation["blocked_labels"]


def test_batch_validation_counts_and_blocked_reasons():
    valid = _valid_record(observation_id="obs-valid")
    privacy_blocked = _valid_record(observation_id="obs-privacy", raw_prompt="secret prompt")
    runtime_blocked = _valid_record(observation_id="obs-runtime", runtime_authority_requested=True)

    batch = validate_real_answer_quality_batch_v1([valid, privacy_blocked, runtime_blocked])

    assert batch["total_records"] == 3
    assert batch["valid_records"] == 1
    assert batch["blocked_records"] == 2
    assert batch["record_status_counts"]["valid"] == 1
    assert batch["record_status_counts"]["blocked"] == 2
    assert batch["blocked_reason_counts"]["raw_prompt_provided"] == 1
    assert batch["blocked_reason_counts"]["runtime_authority_requested"] == 1


def test_summary_is_counts_and_status_only():
    valid = _valid_record(observation_id="obs-valid")
    blocked = _valid_record(observation_id="obs-block", raw_context="secret context")
    summary = summarize_real_answer_quality_observations_v1([valid, blocked])

    assert summary["summary_type"] == SUMMARY_TYPE_V1
    assert summary["total_records"] == 2
    assert summary["valid_records"] == 1
    assert summary["blocked_records"] == 1
    assert isinstance(summary["classification_counts"], dict)
    assert isinstance(summary["record_status_counts"], dict)
    assert summary["raw_answer_stored"] is False


def test_json_safe_conversion_is_deterministic_and_redacts_sensitive_values():
    class Dummy:
        def __init__(self):
            self.raw_prompt = "should be redacted"
            self.nested = {"private_memory": "hidden"}

    value = {"z": 2, "a": Dummy(), "list": [3, {"prompt": "also redacted"}]}
    safe_a = to_real_answer_quality_observation_json_safe_v1(value)
    safe_b = to_real_answer_quality_observation_json_safe_v1(value)

    assert safe_a == safe_b
    assert safe_a["a"]["raw_prompt"] == "[redacted:raw_prompt]"
    assert safe_a["a"]["nested"]["private_memory"] == "[redacted:private_memory]"
    assert safe_a["list"][1]["prompt"] == "[redacted:prompt]"


def test_no_file_network_subprocess_provider_or_dot_weslr_behavior(monkeypatch):
    monkeypatch.setattr(builtins, "open", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("open called")))
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess called")))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess called")))
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("socket called")))

    record = _valid_record()
    assert validate_real_answer_quality_observation_record_v1(record)["valid"] is True
    assert classify_real_answer_quality_observation_v1(record)["classification_label"] == "answer_quality_fit"


def test_source_text_does_not_reference_runtime_wiring():
    source = Path("weslr/real_answer_quality_observation_helpers.py").read_text()
    assert "ChatResponder" not in source
    assert "respond_chat" not in source
    assert "generate_chat" not in source
    assert "main.py" not in source
