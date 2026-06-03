from __future__ import annotations

import copy

import pytest

from weslr.speech_quality_packet import (
    ALLOWED_GAP_LABELS_V1,
    BLOCKER_FIELD_NAMES_V1,
    PACKET_TYPE_V1,
    QUALITY_BANDS_V1,
    QUALITY_BAND_FIELD_NAMES_V1,
    build_speech_quality_packet_v1,
    render_speech_quality_packet_markdown_v1,
    summarize_speech_quality_packet_v1,
    to_speech_quality_packet_json_safe_v1,
    validate_speech_quality_packet_v1,
)


def _minimal_packet_kwargs(**overrides):
    payload = {
        "packet_id": "speech-quality-packet-1",
        "schema_version": PACKET_TYPE_V1,
        "source_refs": ["source:synthetic-corpus-1"],
        "provenance_refs": ["prov:synthetic-corpus-1"],
        "corpus_ref": "corpus:synthetic-speech-v1",
        "command_set_ref": "commands:speech-quality-v1",
        "feature_pipeline_ref": "features:mfcc-delta-v1",
        "scenario_refs": ["scenario:clear-command-1"],
        "quality_scope": "speech quality metadata envelope",
        "gap_labels": [],
        "blocker_fields": {name: False for name in BLOCKER_FIELD_NAMES_V1},
        "synthetic_only": True,
        "review_required": False,
        "no_authority_granted": True,
        "no_public_claim": True,
        "safe_metadata": True,
    }
    payload["quality_band_fields"] = {name: "unknown" for name in QUALITY_BAND_FIELD_NAMES_V1}
    payload.update(overrides)
    return payload


def test_build_valid_minimal_packet():
    packet = build_speech_quality_packet_v1(**_minimal_packet_kwargs())

    assert packet["schema_version"] == PACKET_TYPE_V1
    assert packet["packet_id"] == "speech-quality-packet-1"
    assert packet["synthetic_only"] is True
    assert packet["no_authority_granted"] is True
    assert packet["no_public_claim"] is True
    assert packet["safe_metadata"] is True
    assert set(packet["quality_band_fields"]) == QUALITY_BAND_FIELD_NAMES_V1
    assert set(packet["blocker_fields"]) == BLOCKER_FIELD_NAMES_V1

    validation = validate_speech_quality_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["errors"] == []
    assert validation["blocked_labels"] == []


def test_build_valid_full_packet_with_optional_and_extra_metadata():
    packet = build_speech_quality_packet_v1(
        **_minimal_packet_kwargs(
            created_at="2026-06-03T09:37:00+02:00",
            created_by_ref="operator:occ",
            related_review_refs=["review:plan-1"],
            related_design_refs=["design:decomp-1"],
            notes="internal metadata only",
            custom_note="safe extra metadata",
            custom_tags=["alpha", "beta"],
        )
    )

    assert packet["created_at"] == "2026-06-03T09:37:00+02:00"
    assert packet["created_by_ref"] == "operator:occ"
    assert packet["related_review_refs"] == ["review:plan-1"]
    assert packet["related_design_refs"] == ["design:decomp-1"]
    assert packet["notes"] == "internal metadata only"
    assert packet["custom_note"] == "safe extra metadata"
    assert packet["custom_tags"] == ["alpha", "beta"]

    validation = validate_speech_quality_packet_v1(packet)
    assert validation["valid"] is True


def test_json_safe_copy_does_not_mutate_input():
    packet = build_speech_quality_packet_v1(
        **_minimal_packet_kwargs(
            custom_tags=["alpha", "beta"],
            custom_meta={"enabled": True, "levels": [1, 2, 3]},
        )
    )
    snapshot = copy.deepcopy(packet)

    json_safe = to_speech_quality_packet_json_safe_v1(packet)

    assert packet == snapshot
    assert json_safe == packet
    assert json_safe is not packet


def test_summary_does_not_imply_authority():
    packet = build_speech_quality_packet_v1(**_minimal_packet_kwargs())
    summary = summarize_speech_quality_packet_v1(packet)

    assert summary["valid"] is True
    assert summary["status"] == "valid"
    assert summary["no_authority_granted"] is True
    assert summary["no_public_claim"] is True
    assert summary["safe_metadata"] is True
    assert summary["review_required"] is False
    assert "authority" not in summary


def test_markdown_renderer_does_not_create_public_claim():
    packet = build_speech_quality_packet_v1(**_minimal_packet_kwargs())
    markdown = render_speech_quality_packet_markdown_v1(packet)

    assert "Status: VALID" in markdown
    assert "No Authority Granted: True" in markdown
    assert "No Public Claim: True" in markdown
    assert "benchmark claim" in markdown
    assert "Internal use only" in markdown
    assert "public claim" in markdown.lower()


@pytest.mark.parametrize(
    "mutation, expected_error",
    [
        ({"packet_id": ""}, "packet_id"),
        ({"schema_version": "wrong"}, "schema_version"),
        ({"source_refs": "ref1, ref2"}, "source_refs"),
        ({"provenance_refs": "ref1, ref2"}, "provenance_refs"),
        ({"corpus_ref": ""}, "corpus_ref"),
        ({"command_set_ref": ""}, "command_set_ref"),
        ({"feature_pipeline_ref": ""}, "feature_pipeline_ref"),
        ({"blocker_fields": {**{name: False for name in BLOCKER_FIELD_NAMES_V1}, "has_raw_audio": True}}, "true blocker field"),
        ({"blocker_fields": {**{name: False for name in BLOCKER_FIELD_NAMES_V1}, "has_public_accuracy_claim": True}}, "true blocker field"),
        ({"quality_band_fields": {**{name: "unknown" for name in QUALITY_BAND_FIELD_NAMES_V1}, "unexpected_band": "low"}}, "unknown metric band field"),
        ({"quality_band_fields": {name: "super_high" for name in QUALITY_BAND_FIELD_NAMES_V1}}, "unsafe metric band"),
        ({"gap_labels": ["unknown_label"]}, "unsafe gap label"),
        ({"synthetic_only": False}, "synthetic_only"),
        ({"no_authority_granted": False}, "no_authority_granted"),
        ({"no_public_claim": False}, "no_public_claim"),
        ({"safe_metadata": False}, "safe_metadata"),
    ],
)
def test_validation_rejects_core_schema_and_safety_errors(mutation, expected_error):
    packet = _minimal_packet_kwargs(**mutation)
    result = validate_speech_quality_packet_v1(packet)

    assert result["valid"] is False
    assert any(expected_error in error for error in result["errors"])


@pytest.mark.parametrize(
    "mutation",
    [
        {"raw_audio": "waveform-bytes"},
        {"audio_buffers": [1, 2, 3]},
        {"microphone_handle": "device"},
        {"runtime_voice_event": "evt-1"},
        {"private_user_audio": "secret"},
        {"hidden_recording": True},
        {"biometric_identity_claim": True},
        {"speaker_verification_claim": True},
        {"action_authority": True},
        {"public_accuracy_claim": True},
        {"model_provider_call": True},
        {"weslr_write": True},
        {"behavior_pack_promotion": True},
        {"notes": "public benchmark result"},
        {"custom_meta": {"public": "benchmark"}},
    ],
)
def test_validation_rejects_forbidden_field_classes_and_markers(mutation):
    packet = _minimal_packet_kwargs(**mutation)
    result = validate_speech_quality_packet_v1(packet)

    assert result["valid"] is False
    assert any(
        "forbidden" in error or "unsafe extra metadata field" in error or "true blocker field" in error
        for error in result["errors"]
    )


def test_build_rejects_empty_source_refs():
    kwargs = _minimal_packet_kwargs(source_refs=[])

    with pytest.raises(ValueError):
        build_speech_quality_packet_v1(**kwargs)


def test_build_rejects_empty_provenance_refs():
    kwargs = _minimal_packet_kwargs(provenance_refs=[])

    with pytest.raises(ValueError):
        build_speech_quality_packet_v1(**kwargs)


def test_build_normalizes_duplicate_scenario_refs():
    kwargs = _minimal_packet_kwargs(scenario_refs=["scenario:1", "scenario:1"])
    packet = build_speech_quality_packet_v1(**kwargs)

    assert packet["scenario_refs"] == ["scenario:1"]


def test_build_fills_default_quality_band_fields():
    kwargs = _minimal_packet_kwargs(quality_band_fields=None)
    kwargs["quality_band_fields"] = None
    packet = build_speech_quality_packet_v1(**kwargs)

    assert packet["quality_band_fields"] == {name: "unknown" for name in sorted(QUALITY_BAND_FIELD_NAMES_V1)}


def test_build_fills_default_blocker_fields():
    kwargs = _minimal_packet_kwargs(blocker_fields=None)
    kwargs["blocker_fields"] = None
    packet = build_speech_quality_packet_v1(**kwargs)

    assert packet["blocker_fields"] == {name: False for name in sorted(BLOCKER_FIELD_NAMES_V1)}


def test_unknown_but_safe_metadata_field_behavior():
    packet = build_speech_quality_packet_v1(
        **_minimal_packet_kwargs(
            operator_note="safe extra note",
            owner_tags=["alpha", "beta"],
        )
    )
    validation = validate_speech_quality_packet_v1(packet)

    assert validation["valid"] is True
    assert packet["operator_note"] == "safe extra note"
    assert packet["owner_tags"] == ["alpha", "beta"]


def test_validation_rejects_missing_required_field():
    packet = _minimal_packet_kwargs()
    del packet["packet_id"]
    result = validate_speech_quality_packet_v1(packet)

    assert result["valid"] is False
    assert any("missing required fields" in error for error in result["errors"])


def test_validation_rejects_wrong_schema_version():
    packet = _minimal_packet_kwargs(schema_version="not-the-schema")
    result = validate_speech_quality_packet_v1(packet)

    assert result["valid"] is False
    assert any("schema_version" in error for error in result["errors"])


def test_validation_rejects_comma_delimited_ref_strings():
    packet = _minimal_packet_kwargs(source_refs="ref1, ref2")
    result = validate_speech_quality_packet_v1(packet)

    assert result["valid"] is False
    assert any("source_refs" in error for error in result["errors"])
