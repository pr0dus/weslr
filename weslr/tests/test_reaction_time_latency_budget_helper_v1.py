from __future__ import annotations

import builtins
import importlib
import socket
import subprocess
from pathlib import Path

import pytest

from weslr import reaction_time_latency_budget_helper as rtlb


def _safe_packet_kwargs(**overrides):
    payload = {
        "case_id": "rtlb-case-1",
        "case_source_class": "synthetic_internal_prompt",
        "interaction_family": "acknowledgement",
        "target_latency_band": "tier_0_immediate_acknowledgement_100_200ms",
        "observed_latency_band": "tier_1_first_visible_reaction_under_250ms",
        "measurement_method": "synthetic_metadata_estimate",
        "latency_categories": [
            "perceived_reaction_time",
            "first_visible_acknowledgement",
        ],
        "latency_budget_tier": "tier_0_immediate_acknowledgement_100_200ms",
        "metadata_only": True,
        "raw_text_stored": False,
        "private_data_used": False,
        "audio_used": False,
        "runtime_path_used": False,
        "safety_preflight_present": True,
        "authority_boundary_preserved": True,
        "blocked_reason": [],
        "risk_notes": ["internal metadata only"],
        "latency_bottleneck_label": "safe acknowledgement path",
        "improvement_candidate_label": "faster staged acknowledgement",
        "denied_authority": {name: False for name in sorted(rtlb.DENIED_AUTHORITY_FIELDS_V1)},
        "internal_only": True,
        "non_authoritative": True,
        "validation_status": rtlb.PACKET_VALIDATION_STATUS_VALID_V1,
        "validation_errors": [],
    }
    payload.update(overrides)
    return payload


def _safe_packet(**overrides):
    return rtlb.build_reaction_time_latency_budget_packet_v1(**_safe_packet_kwargs(**overrides))


def test_module_import_and_public_apis_exist():
    module = importlib.reload(rtlb)
    for name in [
        "build_reaction_time_latency_budget_packet_v1",
        "validate_reaction_time_latency_budget_packet_v1",
        "summarize_reaction_time_latency_budget_packet_v1",
        "to_reaction_time_latency_budget_json_safe_v1",
        "render_reaction_time_latency_budget_markdown_v1",
        "build_initial_reaction_time_latency_budget_examples_v1",
    ]:
        assert hasattr(module, name)
        assert callable(getattr(module, name))


def test_safe_example_packets_validate_and_are_internal_only():
    examples = rtlb.build_initial_reaction_time_latency_budget_examples_v1()

    assert examples["schema"] == rtlb.PACKET_SCHEMA_V1
    assert examples["helper_type"] == rtlb.HELPER_TYPE_V1
    assert examples["safe_examples"]
    assert examples["unsafe_examples"]

    for example in examples["safe_examples"]:
        packet = example["packet"]
        validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["schema"] == rtlb.PACKET_SCHEMA_V1
        assert packet["metadata_only"] is True
        assert packet["internal_only"] is True
        assert packet["non_authoritative"] is True
        assert all(packet[name] is False for name in rtlb.DENIED_AUTHORITY_FIELDS_V1)
        assert set(packet["denied_authority"]) == rtlb.DENIED_AUTHORITY_FIELDS_V1
        assert all(packet["denied_authority"][name] is False for name in rtlb.DENIED_AUTHORITY_FIELDS_V1)


def test_unsafe_examples_fail_closed():
    examples = rtlb.build_initial_reaction_time_latency_budget_examples_v1()

    for example in examples["unsafe_examples"]:
        packet = example["packet"]
        validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)
        assert validation["valid"] is False
        assert validation["errors"]
        assert validation["blocked_reasons"]


def test_build_returns_valid_packet_and_denied_authorities_false():
    packet = _safe_packet()

    assert packet["schema"] == rtlb.PACKET_SCHEMA_V1
    assert packet["internal_only"] is True
    assert packet["non_authoritative"] is True
    assert packet["metadata_only"] is True
    assert packet["raw_text_stored"] is False
    assert packet["private_data_used"] is False
    assert packet["audio_used"] is False
    assert packet["runtime_path_used"] is False
    assert packet["safety_preflight_present"] is True
    assert packet["authority_boundary_preserved"] is True
    assert packet["validation_status"] == rtlb.PACKET_VALIDATION_STATUS_VALID_V1
    assert packet["validation_errors"] == []
    assert set(packet["latency_categories"]).issubset(rtlb.LATENCY_CATEGORY_LABELS_V1)
    assert packet["latency_budget_tier"] in rtlb.LATENCY_BUDGET_TIER_LABELS_V1
    assert packet["measurement_method"] in rtlb.MEASUREMENT_METHOD_LABELS_V1
    assert all(packet[name] is False for name in rtlb.DENIED_AUTHORITY_FIELDS_V1)
    assert set(packet["denied_authority"]) == rtlb.DENIED_AUTHORITY_FIELDS_V1


@pytest.mark.parametrize(
    "mutation",
    [
        {"case_source_class": "private_user_chat"},
        {"case_source_class": "voiceprint"},
        {"measurement_method": "provider_log_analysis"},
        {"measurement_method": "live_runtime_instrumentation"},
    ],
)
def test_builder_rejects_unsafe_source_or_measurement_method(mutation):
    with pytest.raises(ValueError):
        rtlb.build_reaction_time_latency_budget_packet_v1(**_safe_packet_kwargs(**mutation))


@pytest.mark.parametrize(
    "mutation, expected_fragment",
    [
        ({"latency_categories": [{"private_user_chat": True}]}, "latency_categories must contain only safe strings"),
        ({"blocked_reason": [{"public_claim": "fast"}]}, "blocked_reason must contain only safe strings"),
        ({"risk_notes": [{"provider_log": True}]}, "risk_notes must contain only safe strings"),
    ],
)
def test_validation_rejects_nested_unsafe_metadata(mutation, expected_fragment):
    packet = _safe_packet()
    for key, value in mutation.items():
        packet[key] = value
    validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_fragment.lower() in error.lower() for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name",
    ["latency_categories", "blocked_reason", "risk_notes", "validation_errors"],
)
def test_validation_rejects_dict_masquerading_as_list(field_name):
    packet = _safe_packet()
    packet[field_name] = {"0": "mfcc"}
    validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)

    assert validation["valid"] is False
    assert any("real list" in error.lower() for error in validation["errors"])


@pytest.mark.parametrize(
    "mutation, expected_fragment",
    [
        ({"runtime_authority": True}, "runtime_authority"),
        ({"behavior_pack_promotion_authority": True}, "behavior_pack_promotion_authority"),
        ({"benchmark_claim_authority": "false"}, "benchmark_claim_authority"),
    ],
)
def test_validation_rejects_true_missing_or_non_boolean_denied_authority_fields(mutation, expected_fragment):
    packet = _safe_packet()
    if "runtime_authority" in mutation:
        del packet["denied_authority"]["runtime_authority"]
    packet.update(mutation)
    validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_fragment.lower() in error.lower() for error in validation["errors"])


@pytest.mark.parametrize(
    "mutation",
    [
        {"latency_categories": ["public_claim_dashboard"]},
        {"latency_budget_tier": "tier_9_not_real"},
        {"target_latency_band": "tier_9_not_real"},
        {"observed_latency_band": "tier_9_not_real"},
    ],
)
def test_validation_rejects_unsafe_labels(mutation):
    packet = _safe_packet()
    packet.update(mutation)
    validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)

    assert validation["valid"] is False
    assert validation["errors"]


def test_json_safe_copy_does_not_launder_invalid_packet_into_validity():
    invalid_packet = _safe_packet()
    invalid_packet["case_source_class"] = "private_user_chat"
    invalid_packet["validation_status"] = rtlb.PACKET_VALIDATION_STATUS_INVALID_V1
    invalid_packet["validation_errors"] = ["private_user_chat is forbidden"]
    json_safe = rtlb.to_reaction_time_latency_budget_json_safe_v1(invalid_packet)

    assert json_safe is not invalid_packet
    assert json_safe["validation_status"] == rtlb.PACKET_VALIDATION_STATUS_INVALID_V1
    assert rtlb.validate_reaction_time_latency_budget_packet_v1(json_safe)["valid"] is False


def test_markdown_requires_validation_and_summary_remains_internal_only():
    packet = _safe_packet()
    summary = rtlb.summarize_reaction_time_latency_budget_packet_v1(packet)
    markdown = rtlb.render_reaction_time_latency_budget_markdown_v1(packet)

    assert summary["valid"] is True
    assert summary["status"] == rtlb.PACKET_VALIDATION_STATUS_VALID_V1
    assert summary["internal_only"] is True
    assert summary["non_authoritative"] is True
    assert summary["authority_boundary_preserved"] is True
    assert "performance" not in summary
    assert "benchmark" not in summary
    assert "Status: VALID" in markdown
    assert "Internal use only" in markdown
    assert "No runtime measurement" in markdown

    invalid_packet = _safe_packet()
    invalid_packet["runtime_authority"] = True
    with pytest.raises(ValueError):
        rtlb.render_reaction_time_latency_budget_markdown_v1(invalid_packet)


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
    validation = rtlb.validate_reaction_time_latency_budget_packet_v1(packet)
    summary = rtlb.summarize_reaction_time_latency_budget_packet_v1(packet)
    json_safe = rtlb.to_reaction_time_latency_budget_json_safe_v1(packet)
    markdown = rtlb.render_reaction_time_latency_budget_markdown_v1(packet)

    assert validation["valid"] is True
    assert summary["valid"] is True
    assert json_safe == packet
    assert "Status: VALID" in markdown
