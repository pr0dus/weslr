from __future__ import annotations

import builtins
import importlib
import socket
import subprocess
from pathlib import Path

import pytest

from weslr import mfcc_feature_quality_metadata as mfcc


def _safe_packet_kwargs(**overrides):
    payload = {
        "packet_id": "mfcc-quality-1",
        "source_type_classification": "synthetic_metadata",
        "dataset_provenance_class": "synthetic_metadata",
        "feature_family_metadata": ["mfcc", "delta", "delta_delta", "spectral_metadata", "chroma_metadata", "cymatics_display_metadata"],
        "quality_dimensions": {
            "completeness": "full",
            "stability": "stable",
            "frame_window_consistency": "consistent",
            "feature_availability": "complete",
            "noise_condition_label": "clean",
            "language_command_domain_label": "english_command_set",
            "synthetic_accent_noise_test_condition_label": "none_identifying",
            "command_set_coverage": "broad",
            "expected_vs_observed_recognition_metadata": "aligned",
            "error_category_label": "none",
            "confidence_calibration_metadata": "calibrated",
            "cymatics_display_usefulness_label": "useful",
            "cymatics_display_interpretability_label": "clear",
        },
        "cymatics_usefulness_metadata": {
            "visual_expressiveness": "clear",
            "diagnostic_usefulness": "high",
            "feature_gap_diagnosis": "strong",
            "noise_diagnosis": "helpful",
            "rhythm_diagnosis": "helpful",
            "emphasis_diagnosis": "helpful",
            "command_instability_diagnosis": "low",
            "interpretability_label": "clear",
            "no_real_time_wiring": True,
        },
        "recognition_quality_metadata": {
            "calibration": "stable",
            "false_accept_labels": [],
            "false_reject_labels": [],
            "command_ambiguity_labels": [],
            "noise_robustness_labels": ["good"],
            "multilingual_accent_condition_labels": ["neutral"],
            "quality_notes": "internal metadata only",
        },
    }
    payload.update(overrides)
    return payload


def _safe_packet(**overrides):
    return mfcc.build_mfcc_feature_quality_packet_v1(**_safe_packet_kwargs(**overrides))


def test_module_import_and_public_apis_exist():
    module = importlib.reload(mfcc)
    for name in [
        "build_mfcc_feature_quality_packet_v1",
        "validate_mfcc_feature_quality_packet_v1",
        "summarize_mfcc_feature_quality_packet_v1",
        "to_mfcc_feature_quality_json_safe_v1",
        "render_mfcc_feature_quality_markdown_v1",
        "build_initial_mfcc_feature_quality_examples_v1",
    ]:
        assert hasattr(module, name)
        assert callable(getattr(module, name))


def test_safe_example_packets_validate_and_are_internal_only():
    examples = mfcc.build_initial_mfcc_feature_quality_examples_v1()

    assert examples["helper_type"] == mfcc.HELPER_TYPE_V1
    assert examples["schema_version"] == mfcc.PACKET_SCHEMA_VERSION_V1
    assert examples["safe_examples"]
    assert examples["unsafe_examples"]

    for example in examples["safe_examples"]:
        packet = example["packet"]
        validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["internal_only"] is True
        assert packet["non_authoritative"] is True
        assert all(packet[name] is False for name in mfcc.DENIED_AUTHORITY_FIELDS_V1)
        assert packet["helper_type"] == mfcc.HELPER_TYPE_V1
        assert packet["schema_version"] == mfcc.PACKET_SCHEMA_VERSION_V1


def test_unsafe_examples_fail_closed():
    examples = mfcc.build_initial_mfcc_feature_quality_examples_v1()

    for example in examples["unsafe_examples"]:
        packet = example["packet"]
        validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)
        assert validation["valid"] is False
        assert validation["errors"]
        assert validation["blocked_reasons"]


def test_build_returns_valid_packet_and_denied_authorities_false():
    packet = mfcc.build_mfcc_feature_quality_packet_v1(**_safe_packet_kwargs())

    assert packet["helper_type"] == mfcc.HELPER_TYPE_V1
    assert packet["schema_version"] == mfcc.PACKET_SCHEMA_VERSION_V1
    assert packet["internal_only"] is True
    assert packet["non_authoritative"] is True
    assert set(packet["feature_family_metadata"]) == mfcc.SAFE_FEATURE_FAMILY_LABELS_V1
    assert all(packet[name] is False for name in mfcc.DENIED_AUTHORITY_FIELDS_V1)
    assert set(packet["denied_authority_fields"]) == mfcc.DENIED_AUTHORITY_FIELDS_V1


def test_build_rejects_unsafe_source_and_provenance_classes():
    with pytest.raises(ValueError):
        mfcc.build_mfcc_feature_quality_packet_v1(**_safe_packet_kwargs(source_type_classification="raw_audio"))
    with pytest.raises(ValueError):
        mfcc.build_mfcc_feature_quality_packet_v1(**_safe_packet_kwargs(dataset_provenance_class="private_audio"))


@pytest.mark.parametrize(
    "mutation",
    [
        {"quality_dimensions": {"notes": "http://example.com/sample.wav"}},
        {"quality_dimensions": {"raw_audio": True}},
        {"quality_dimensions": {"speaker_identity": "operator"}},
        {"recognition_quality_metadata": {"quality_notes": "public benchmark claim"}},
        {"cymatics_usefulness_metadata": {"visual_expressiveness": "clear", "notes": {"voice_verified": True}}},
    ],
)
def test_validation_rejects_forbidden_fields_and_nested_metadata(mutation):
    packet = _safe_packet()
    for key, value in mutation.items():
        if isinstance(packet.get(key), dict) and isinstance(value, dict):
            packet[key].update(value)
        else:
            packet[key] = value
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert validation["errors"]
    assert validation["blocked_reasons"]


def test_validation_rejects_list_contained_unsafe_field():
    packet = _safe_packet()
    packet["recognition_quality_metadata"] = {
        "false_accept_labels": ["low", {"speaker_verified": True}],
        "false_reject_labels": [],
        "command_ambiguity_labels": [],
        "noise_robustness_labels": ["good"],
        "multilingual_accent_condition_labels": ["neutral"],
        "calibration": "stable",
    }
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert any("unsafe" in error.lower() or "forbidden" in error.lower() for error in validation["errors"])


def test_validation_rejects_dict_masquerading_as_list():
    packet = _safe_packet()
    packet["feature_family_metadata"] = {"0": "mfcc"}
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert any("real list" in error.lower() for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name",
    sorted(mfcc.DENIED_AUTHORITY_FIELDS_V1),
)
def test_denied_authority_fields_present_and_false(field_name):
    packet = mfcc.build_mfcc_feature_quality_packet_v1(**_safe_packet_kwargs())
    assert field_name in packet
    assert packet[field_name] is False
    assert packet["denied_authority_fields"][field_name] is False


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ({"runtime_authority": True}, "runtime_authority"),
        ({"microphone_authority": True}, "microphone_authority"),
        ({"voice_template_authority": True}, "voice_template_authority"),
        ({"benchmark_claim_authority": True}, "benchmark_claim_authority"),
        ({"public_accuracy_claim_authority": True}, "public_accuracy_claim_authority"),
    ],
)
def test_validation_rejects_true_denied_authority_fields(mutation, expected):
    packet = _safe_packet()
    packet.update(mutation)
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected in error for error in validation["errors"])


def test_validation_rejects_missing_denied_authority_field():
    packet = _safe_packet()
    del packet["runtime_authority"]
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert any("missing required fields" in error.lower() or "runtime_authority" in error.lower() for error in validation["errors"])


def test_validation_rejects_non_boolean_denied_authority_field():
    packet = _safe_packet()
    packet["runtime_authority"] = "false"
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)

    assert validation["valid"] is False
    assert any("top-level denied authority field" in error.lower() or "runtime_authority" in error.lower() for error in validation["errors"])


def test_json_safe_copy_does_not_sanitize_invalid_packet_into_validity():
    invalid_packet = _safe_packet()
    invalid_packet["quality_dimensions"] = {"notes": "http://example.com/sample.wav"}
    json_safe = mfcc.to_mfcc_feature_quality_json_safe_v1(invalid_packet)

    assert json_safe == invalid_packet
    assert json_safe is not invalid_packet
    assert mfcc.validate_mfcc_feature_quality_packet_v1(json_safe)["valid"] is False


def test_markdown_requires_validation():
    valid_packet = _safe_packet()
    assert "Status: VALID" in mfcc.render_mfcc_feature_quality_markdown_v1(valid_packet)

    invalid_packet = _safe_packet()
    invalid_packet["runtime_authority"] = True
    with pytest.raises(ValueError):
        mfcc.render_mfcc_feature_quality_markdown_v1(invalid_packet)


def test_summary_remains_internal_only():
    summary = mfcc.summarize_mfcc_feature_quality_packet_v1(_safe_packet())

    assert summary["valid"] is True
    assert summary["status"] == mfcc.PACKET_VALIDATION_STATUS_VALID_V1
    assert summary["internal_only"] is True
    assert summary["non_authoritative"] is True
    assert "authority" not in summary


def test_cymatics_labels_do_not_imply_cognition_or_authority():
    packet = _safe_packet()
    summary = mfcc.summarize_mfcc_feature_quality_packet_v1(packet)
    markdown = mfcc.render_mfcc_feature_quality_markdown_v1(packet)

    assert summary["valid"] is True
    assert packet["cymatics_usefulness_metadata"]["visual_expressiveness"] == "clear"
    assert "not proof of cognition or authority" in markdown.lower()


def test_recognition_quality_labels_do_not_imply_achieved_accuracy():
    packet = _safe_packet()
    summary = mfcc.summarize_mfcc_feature_quality_packet_v1(packet)

    assert summary["valid"] is True
    assert packet["recognition_quality_metadata"]["calibration"] == "stable"
    assert "accuracy" not in summary


def test_public_apis_do_not_use_io_or_subprocess(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("io path should not be touched")

    monkeypatch.setattr(builtins, "open", boom)
    monkeypatch.setattr(Path, "write_text", boom)
    monkeypatch.setattr(Path, "read_text", boom)
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(socket, "create_connection", boom, raising=False)
    monkeypatch.setattr(socket, "socket", boom)

    packet = _safe_packet()
    validation = mfcc.validate_mfcc_feature_quality_packet_v1(packet)
    summary = mfcc.summarize_mfcc_feature_quality_packet_v1(packet)
    json_safe = mfcc.to_mfcc_feature_quality_json_safe_v1(packet)
    markdown = mfcc.render_mfcc_feature_quality_markdown_v1(packet)

    assert validation["valid"] is True
    assert summary["valid"] is True
    assert json_safe == packet
    assert "Status: VALID" in markdown
