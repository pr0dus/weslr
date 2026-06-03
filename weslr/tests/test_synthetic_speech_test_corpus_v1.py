from __future__ import annotations

import copy

import pytest

from weslr.synthetic_speech_test_corpus import (
    ALLOWED_SOURCE_CLASSES_V1,
    ALLOWED_VARIANT_FAMILIES_V1,
    BLOCKED_SOURCE_CLASSES_V1,
    FORBIDDEN_SOURCE_FLAG_NAMES_V1,
    PACKET_TYPE_V1,
    REQUIRED_FORBIDDEN_SOURCE_FLAG_NAMES_V1,
    build_synthetic_speech_corpus_packet_v1,
    render_synthetic_speech_corpus_markdown_v1,
    summarize_synthetic_speech_corpus_packet_v1,
    to_synthetic_speech_corpus_json_safe_v1,
    validate_synthetic_speech_corpus_packet_v1,
)


def _minimal_packet_kwargs(**overrides):
    payload = {
        "packet_id": "synthetic-speech-corpus-1",
        "source_refs": ["fixture:text-only-1"],
        "provenance_refs": ["prov:text-only-1"],
        "corpus_name": "Synthetic Speech Test Corpus V1",
        "corpus_scope": "internal metadata-only synthetic speech evaluation",
        "variant_family_refs": ["clear_command", "replay_scenario_metadata"],
        "scenario_refs": ["scenario:text-only-clear-1"],
        "allowed_source_class": "synthetic_weslr_created",
        "synthetic_only": True,
        "provenance_known": True,
        "review_required": True,
        "no_private_user_audio": True,
        "no_hidden_recording": True,
        "no_biometric_dataset": True,
        "no_public_benchmark_claim": True,
        "no_authority_granted": True,
        "no_public_claim": True,
        "safe_metadata": True,
    }
    payload.update(overrides)
    return payload


def _build_valid_packet(**overrides):
    return build_synthetic_speech_corpus_packet_v1(**_minimal_packet_kwargs(**overrides))


def test_valid_minimal_packet():
    packet = _build_valid_packet()

    assert packet["schema_version"] == PACKET_TYPE_V1
    assert packet["packet_id"] == "synthetic-speech-corpus-1"
    assert packet["synthetic_only"] is True
    assert packet["provenance_known"] is True
    assert packet["no_private_user_audio"] is True
    assert packet["no_hidden_recording"] is True
    assert packet["no_biometric_dataset"] is True
    assert packet["no_public_benchmark_claim"] is True
    assert packet["no_authority_granted"] is True
    assert packet["no_public_claim"] is True
    assert packet["safe_metadata"] is True
    assert set(packet["allowed_source_class"] for _ in [0]) <= ALLOWED_SOURCE_CLASSES_V1
    assert set(packet["variant_family_refs"]).issubset(ALLOWED_VARIANT_FAMILIES_V1)
    assert set(packet["forbidden_source_flags"]) == set(FORBIDDEN_SOURCE_FLAG_NAMES_V1)

    validation = validate_synthetic_speech_corpus_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["errors"] == []
    assert validation["blocked_labels"] == []


def test_valid_full_packet_with_optional_and_safe_extra_metadata():
    packet = _build_valid_packet(
        created_at="2026-06-03T09:38:00+02:00",
        created_by_ref="operator:occ",
        related_packet_refs=["packet:related-1"],
        related_design_refs=["design:related-1"],
        notes="internal metadata only",
        operator_note="safe note",
        custom_meta={"enabled": True, "levels": [1, 2, 3]},
        coverage_summary={"custom_summary_note": "safe extra"},
    )

    assert packet["created_at"] == "2026-06-03T09:38:00+02:00"
    assert packet["created_by_ref"] == "operator:occ"
    assert packet["related_packet_refs"] == ["packet:related-1"]
    assert packet["related_design_refs"] == ["design:related-1"]
    assert packet["notes"] == "internal metadata only"
    assert packet["operator_note"] == "safe note"
    assert packet["custom_meta"] == {"enabled": True, "levels": [1, 2, 3]}
    assert packet["coverage_summary"]["custom_summary_note"] == "safe extra"

    validation = validate_synthetic_speech_corpus_packet_v1(packet)
    assert validation["valid"] is True


def test_public_open_text_only_fixture_is_accepted():
    packet = _build_valid_packet(
        packet_id="synthetic-speech-corpus-text-only-1",
        allowed_source_class="public_open_text_only",
        source_refs=["fixture:text-only-public-1"],
        provenance_refs=["prov:text-only-public-1"],
        variant_family_refs=["clear_command", "partial_command"],
        scenario_refs=["scenario:text-only-public-1"],
        corpus_name="Public open text-only fixture",
        corpus_scope="text-only synthetic speech test metadata",
    )

    validation = validate_synthetic_speech_corpus_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["allowed_source_class"] == "public_open_text_only"


def test_public_open_text_only_with_audio_like_content_is_rejected():
    with pytest.raises(ValueError):
        _build_valid_packet(
            allowed_source_class="public_open_text_only",
            notes="raw audio waveform",
        )


@pytest.mark.parametrize(
    "allowed_source_class",
    [
        "private_audio_blocked",
        "hidden_recording_blocked",
        "biometric_dataset_blocked",
        "poisoned_media_blocked",
        "unknown_source_blocked",
    ],
)
def test_blocked_source_classes_rejected(allowed_source_class):
    with pytest.raises(ValueError):
        _build_valid_packet(allowed_source_class=allowed_source_class)


@pytest.mark.parametrize(
    "variant_family_refs",
    [
        ["clear_command", "not-a-family"],
        ["unknown_variant", "bad_family"],
    ],
)
def test_invalid_variant_family_rejected(variant_family_refs):
    with pytest.raises(ValueError):
        _build_valid_packet(variant_family_refs=variant_family_refs)


@pytest.mark.parametrize(
    "field_name",
    [
        "source_refs",
        "provenance_refs",
        "variant_family_refs",
        "scenario_refs",
        "related_packet_refs",
        "related_design_refs",
    ],
)
def test_dict_inputs_are_rejected_by_builder(field_name):
    override = {field_name: {"a": "fixture:text-only-1"}}
    with pytest.raises(ValueError):
        _build_valid_packet(**override)


@pytest.mark.parametrize(
    "field_name",
    [
        "source_refs",
        "provenance_refs",
        "variant_family_refs",
        "scenario_refs",
        "related_packet_refs",
        "related_design_refs",
    ],
)
def test_dict_inputs_are_rejected_by_validation(field_name):
    packet = _build_valid_packet()
    packet[field_name] = {"a": "fixture:text-only-1"}
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any("real list" in error for error in validation["errors"])


@pytest.mark.parametrize(
    "flag_name",
    sorted(REQUIRED_FORBIDDEN_SOURCE_FLAG_NAMES_V1 | {"has_audio_generation", "has_speaker_verification"}),
)
def test_true_forbidden_source_flags_are_rejected(flag_name):
    with pytest.raises(ValueError):
        _build_valid_packet(forbidden_source_flags={flag_name: True})

    packet = _build_valid_packet()
    packet["forbidden_source_flags"][flag_name] = True
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(flag_name in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("raw_audio", "waveform-bytes"),
        ("audio_buffer", b"waveform-bytes"),
        ("speaker_verified", True),
        ("speaker_verification_claim", True),
        ("action_authority", True),
        ("public_benchmark_claim", True),
        ("model_provider_call", True),
        ("weslr_write", True),
        ("behavior_pack_promotion", True),
    ],
)
def test_forbidden_extra_fields_rejected(field_name, value):
    with pytest.raises(ValueError):
        _build_valid_packet(**{field_name: value})


@pytest.mark.parametrize(
    "field_name,mutated_value,expected_error",
    [
        ("synthetic_only", False, "synthetic_only must be true"),
        ("provenance_known", False, "provenance_known must be true"),
        ("no_private_user_audio", False, "no_private_user_audio must be true"),
        ("no_hidden_recording", False, "no_hidden_recording must be true"),
        ("no_biometric_dataset", False, "no_biometric_dataset must be true"),
        ("no_public_benchmark_claim", False, "no_public_benchmark_claim must be true"),
        ("no_authority_granted", False, "no_authority_granted must be true"),
        ("no_public_claim", False, "no_public_claim must be true"),
        ("safe_metadata", False, "safe_metadata must be true"),
    ],
)
def test_required_boolean_safety_fields_reject_false(field_name, mutated_value, expected_error):
    packet = _build_valid_packet()
    packet[field_name] = mutated_value
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_error in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name,mutated_value,expected_error",
    [
        ("source_refs", "ref1, ref2", "source_refs must be a real list of safe strings"),
        ("provenance_refs", "ref1, ref2", "provenance_refs must be a real list of safe strings"),
        ("variant_family_refs", ["clear_command", "not_real"], "unknown unsafe variant family"),
        ("scenario_refs", "scenario1", "scenario_refs must be a real list of safe strings"),
    ],
)
def test_list_and_variant_validation(field_name, mutated_value, expected_error):
    packet = _build_valid_packet()
    packet[field_name] = mutated_value
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_error in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name,mutated_value,expected_error",
    [
        ("packet_id", "", "packet_id must be a non-empty stable string"),
        ("schema_version", "wrong", "schema_version must equal synthetic_speech_corpus_packet_v1"),
        ("corpus_name", "", "corpus_name must be a non-empty safe string"),
        ("corpus_scope", "", "corpus_scope must be a non-empty safe string"),
        ("allowed_source_class", "totally_unknown", "unknown unsafe source class"),
    ],
)
def test_scalar_validation(field_name, mutated_value, expected_error):
    packet = _build_valid_packet()
    packet[field_name] = mutated_value
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_error in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name",
    [
        "has_private_user_audio",
        "has_hidden_recording",
        "has_raw_audio",
        "has_biometric_dataset",
        "has_unapproved_proprietary_dataset",
        "has_poisoned_external_media",
        "has_social_media_audio",
        "has_public_benchmark_claim",
        "has_speaker_verification_claim",
        "has_action_authority",
        "has_model_provider_call",
        "has_weslr_write",
        "has_behavior_pack_promotion",
        "has_audio_generation",
        "has_speaker_verification",
    ],
)
def test_forbidden_flag_map_true_values_are_rejected(field_name):
    with pytest.raises(ValueError):
        _build_valid_packet(forbidden_source_flags={field_name: True})

    packet = _build_valid_packet()
    packet["forbidden_source_flags"][field_name] = True
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(field_name in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("coverage_summary", "not-a-mapping", "coverage_summary must be a mapping"),
        ("coverage_summary", {"source_ref_count": 99}, "missing coverage summary fields"),
    ],
)
def test_coverage_summary_validation(field_name, value, expected_error):
    packet = _build_valid_packet()
    packet[field_name] = value
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_error in error for error in validation["errors"])


@pytest.mark.parametrize(
    "mutation, expected_error",
    [
        ({"source_refs": ["fixture:text-only-1", "raw audio"]}, "source_refs contains forbidden content"),
        ({"provenance_refs": ["prov:text-only-1", "public benchmark"]}, "provenance_refs contains forbidden content"),
        ({"scenario_refs": ["scenario:text-only-1", "voice recording"]}, "scenario_refs contains forbidden content"),
        ({"notes": "public accuracy claim"}, "notes contains forbidden content"),
    ],
)
def test_forbidden_content_markers_are_rejected(mutation, expected_error):
    packet = _build_valid_packet()
    packet.update(mutation)
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is False
    assert any(expected_error in error for error in validation["errors"])


@pytest.mark.parametrize(
    "field_name,audio_value",
    [
        ("source_refs", ["fixture:text-only-public-1", "https://example.com/clip.mp3"]),
        ("provenance_refs", ["prov:text-only-public-1", "file:///tmp/clip.wav"]),
        ("scenario_refs", ["scenario:text-only-public-1", "audio/sample.opus"]),
        ("related_packet_refs", ["packet:related-1", "voice/clip.m4a"]),
        ("related_design_refs", ["design:related-1", "https://example.com/media.flac?download=1"]),
        ("related_design_refs", ["design:related-1", "sound/room.ogg"]),
    ],
)
def test_public_open_text_only_rejects_audio_like_refs(field_name, audio_value):
    with pytest.raises(ValueError):
        _build_valid_packet(
            allowed_source_class="public_open_text_only",
            **{field_name: audio_value},
        )


@pytest.mark.parametrize(
    "field_name,audio_value",
    [
        ("notes", "voice_sample"),
        ("notes", "raw_audio"),
        ("notes", "microphone"),
        ("notes", "https://example.com/clip.opus"),
    ],
)
def test_public_open_text_only_rejects_audio_like_notes(field_name, audio_value):
    with pytest.raises(ValueError):
        _build_valid_packet(
            allowed_source_class="public_open_text_only",
            **{field_name: audio_value},
        )


@pytest.mark.parametrize(
    "field_name,audio_value",
    [
        ("custom_meta", {"nested": {"uri": "https://example.com/clip.webm"}}),
        ("operator_note", {"nested": ["sound/room.wav"]}),
    ],
)
def test_public_open_text_only_rejects_audio_like_nested_extra_metadata(field_name, audio_value):
    with pytest.raises(ValueError):
        _build_valid_packet(
            allowed_source_class="public_open_text_only",
            **{field_name: audio_value},
        )


def test_json_safe_copy_does_not_mutate_input():
    packet = _build_valid_packet(
        operator_note="safe note",
        custom_meta={"enabled": True, "levels": [1, 2, 3]},
    )
    snapshot = copy.deepcopy(packet)

    json_safe = to_synthetic_speech_corpus_json_safe_v1(packet)

    assert packet == snapshot
    assert json_safe == packet
    assert json_safe is not packet


def test_summary_does_not_imply_authority_or_benchmark():
    packet = _build_valid_packet()
    summary = summarize_synthetic_speech_corpus_packet_v1(packet)

    assert summary["valid"] is True
    assert summary["status"] == "valid"
    assert summary["no_authority_granted"] is True
    assert summary["no_public_claim"] is True
    assert summary["safe_metadata"] is True
    assert "authority" not in summary
    assert "benchmark" not in summary


def test_markdown_renderer_does_not_create_public_accuracy_claim():
    packet = _build_valid_packet()
    markdown = render_synthetic_speech_corpus_markdown_v1(packet)

    assert "Status: VALID" in markdown
    assert "Allowed Source Class: synthetic_weslr_created" in markdown
    assert "No Authority Granted: True" in markdown
    assert "No Public Claim: True" in markdown
    assert "public accuracy" not in markdown.lower()
    assert "Internal use only" in markdown


def test_safe_unknown_metadata_is_accepted_when_json_safe_and_non_authority_bearing():
    packet = _build_valid_packet(
        operator_note="safe note",
        owner_tags=["alpha", "beta"],
        custom_meta={"enabled": True, "levels": [1, 2, 3]},
    )
    validation = validate_synthetic_speech_corpus_packet_v1(packet)

    assert validation["valid"] is True
    assert packet["operator_note"] == "safe note"
    assert packet["owner_tags"] == ["alpha", "beta"]
    assert packet["custom_meta"] == {"enabled": True, "levels": [1, 2, 3]}
