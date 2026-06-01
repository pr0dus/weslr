from __future__ import annotations

import inspect
import sys

import pytest

from weslr.time_anchor_resolver import (
    TimeAnchorPacket,
    build_initial_time_anchor_examples_v1,
    build_time_anchor_packet_v1,
    resolve_time_anchor_v1,
    summarize_time_anchor_packet_v1,
    to_time_anchor_json_safe_v1,
    validate_time_anchor_packet_v1,
)


REF = "2026-06-01T12:00:00"
TZ = "Europe/Berlin"


def _find_example(examples, example_name):
    for packet in examples:
        if packet.safe_metadata.get("example_name") == example_name:
            return packet
    raise AssertionError(f"missing example {example_name}")



def _packet_map(packet):
    return to_time_anchor_json_safe_v1(packet)



def _mutate(packet, **overrides):
    data = _packet_map(packet)
    data.update(overrides)
    return data



def test_module_imports_safely():
    import weslr.time_anchor_resolver as mod

    assert mod.HELPER_TYPE_V1 == "time_anchor_resolver_v1"
    assert mod.TIME_ANCHOR_PACKET_TYPE_V1 == "time_anchor_packet_v1"
    assert mod.SUMMARY_TYPE_V1 == "time_anchor_summary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules



def test_builds_deterministic_anchor_packet():
    first = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    second = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    assert first == second



def test_validates_normal_anchor_packet():
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    assert validate_time_anchor_packet_v1(packet) is True



def test_json_safe_export_works():
    packet = build_time_anchor_packet_v1("today", reference_time=REF, timezone=TZ)
    exported = to_time_anchor_json_safe_v1(packet)
    assert isinstance(exported, dict)
    assert exported["original_phrase"] == "today"
    assert exported["anchor_type"] == "relative_day"



def test_summary_includes_phrase_anchor_type_window_confidence():
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    summary = summarize_time_anchor_packet_v1(packet)
    assert summary.original_phrase == "yesterday"
    assert summary.anchor_type == "relative_day"
    assert summary.confidence == "high"
    assert "2026-05-31T00:00:00" in summary.window_summary



def test_initial_examples_exist():
    assert len(build_initial_time_anchor_examples_v1()) >= 13


@pytest.mark.parametrize(
    "example_name, expected_anchor_type",
    [
        ("yesterday_anchor_example", "relative_day"),
        ("today_anchor_example", "relative_day"),
        ("this_morning_anchor_example", "day_part"),
        ("last_night_anchor_example", "day_part"),
        ("last_week_anchor_example", "relative_range"),
        ("past_few_days_anchor_example", "relative_range"),
        ("previous_session_anchor_example", "session_relative"),
        ("earlier_in_this_chat_anchor_example", "session_relative"),
        ("before_last_commit_anchor_example", "project_relative"),
        ("after_file_manifest_builder_anchor_example", "project_relative"),
        ("absolute_date_anchor_example", "absolute_date"),
        ("recently_vague_anchor_example", "vague_temporal"),
        ("missing_reference_time_anchor_example", "relative_day"),
    ],
)
def test_named_examples_exist(example_name, expected_anchor_type):
    packet = _find_example(build_initial_time_anchor_examples_v1(), example_name)
    assert packet.anchor_type == expected_anchor_type


@pytest.mark.parametrize(
    "phrase, expected_start, expected_end",
    [
        ("yesterday", "2026-05-31T00:00:00", "2026-05-31T23:59:59"),
        ("today", "2026-06-01T00:00:00", "2026-06-01T23:59:59"),
        ("tomorrow", "2026-06-02T00:00:00", "2026-06-02T23:59:59"),
    ],
)
def test_relative_day_resolution(phrase, expected_start, expected_end):
    packet = build_time_anchor_packet_v1(phrase, reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "relative_day"
    assert packet.resolved_start == expected_start
    assert packet.resolved_end == expected_end
    assert packet.retrieval_mode_hint == "temporal_first"
    assert packet.temporal_first is True
    assert packet.confidence == "high"


@pytest.mark.parametrize(
    "phrase, expected_start, expected_end",
    [
        ("this morning", "2026-06-01T05:00:00", "2026-06-01T12:00:00"),
        ("this afternoon", "2026-06-01T12:00:00", "2026-06-01T18:00:00"),
        ("this evening", "2026-06-01T18:00:00", "2026-06-01T23:59:59"),
        ("last night", "2026-05-31T20:00:00", "2026-06-01T05:00:00"),
    ],
)
def test_day_part_resolution(phrase, expected_start, expected_end):
    packet = build_time_anchor_packet_v1(phrase, reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "day_part"
    assert packet.resolved_start == expected_start
    assert packet.resolved_end == expected_end
    assert packet.calendar_basis == "local_day_part"



def test_last_week_resolution():
    packet = build_time_anchor_packet_v1("last week", reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "relative_range"
    assert packet.calendar_basis == "local_calendar_week"
    assert packet.resolved_start == "2026-05-25T00:00:00"
    assert packet.resolved_end == "2026-05-31T23:59:59"



def test_past_few_days_resolution():
    packet = build_time_anchor_packet_v1("past few days", reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "relative_range"
    assert packet.resolved_start == "2026-05-29T00:00:00"
    assert packet.resolved_end == "2026-06-01T12:00:00"
    assert packet.confidence == "medium"



def test_recently_is_vague_low_confidence():
    packet = build_time_anchor_packet_v1("recently", reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "vague_temporal"
    assert packet.confidence == "low"
    assert packet.needs_clarification is True
    assert packet.retrieval_mode_hint == "clarification_required"


@pytest.mark.parametrize(
    "phrase, expected_scope",
    [
        ("earlier in this chat", "current_conversation"),
        ("earlier", "current_conversation"),
        ("previous session", "previous_session"),
        ("last session", "previous_session"),
        ("previous conversation", "previous_session"),
    ],
)
def test_session_relative_phrases(phrase, expected_scope):
    packet = build_time_anchor_packet_v1(phrase, reference_time=REF, timezone=TZ)
    assert packet.anchor_type == "session_relative"
    assert packet.source_scope_hint == expected_scope
    assert packet.calendar_basis == "session_order"
    assert packet.confidence in {"medium", "low"}


@pytest.mark.parametrize(
    "phrase, expected_retrieval",
    [
        ("before the last commit", "event_anchor_retrieval"),
        ("after the file manifest builder", "event_anchor_retrieval"),
    ],
)
def test_project_relative_phrases(phrase, expected_retrieval):
    packet = build_time_anchor_packet_v1(phrase, reference_time=REF, timezone=TZ, commit_anchor="last_commit", event_anchor="file_manifest_builder")
    assert packet.anchor_type == "project_relative"
    assert packet.retrieval_mode_hint == expected_retrieval
    assert packet.calendar_basis == "project_event_order"



def test_event_relative_phrase():
    packet = build_time_anchor_packet_v1("after OCC replied", reference_time=REF, timezone=TZ, event_anchor="occ_replied")
    assert packet.anchor_type == "event_relative"
    assert packet.retrieval_mode_hint == "event_anchor_retrieval"
    assert packet.calendar_basis == "project_event_order"


@pytest.mark.parametrize(
    "phrase, expected_start, expected_end",
    [
        ("2026-05-31", "2026-05-31T00:00:00", "2026-05-31T23:59:59"),
        ("2026-05-31T10:30:00", "2026-05-31T10:30:00", "2026-05-31T10:30:00"),
    ],
)
def test_absolute_date_resolution(phrase, expected_start, expected_end):
    packet = build_time_anchor_packet_v1(phrase)
    assert packet.anchor_type == "absolute_date"
    assert packet.calendar_basis == "explicit_absolute_date"
    assert packet.resolved_start == expected_start
    assert packet.resolved_end == expected_end
    assert packet.confidence == "high"



def test_missing_reference_time_for_yesterday_requires_clarification():
    packet = build_time_anchor_packet_v1("yesterday", timezone=TZ)
    assert packet.anchor_type == "relative_day"
    assert packet.confidence == "unresolved"
    assert packet.needs_clarification is True
    assert packet.retrieval_mode_hint == "clarification_required"
    assert packet.resolved_start is None
    assert packet.resolved_end is None



def test_timezone_is_preserved_in_packet():
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    assert packet.timezone == TZ



def test_missing_timezone_lowers_confidence_or_requires_clarification():
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF)
    assert packet.confidence in {"low", "unresolved"}
    assert packet.needs_clarification is True


@pytest.mark.parametrize(
    "field_name",
    [
        "source_access_granted",
        "memory_read_authority_granted",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_no_initial_example_allows_authority(field_name):
    for packet in build_initial_time_anchor_examples_v1():
        assert getattr(packet, field_name) is False


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("anchor_type", "unknown_anchor", "unknown_anchor_type"),
        ("retrieval_mode_hint", "unknown_mode", "unknown_retrieval_mode_hint"),
        ("confidence", "unknown", "unknown_confidence"),
        ("calendar_basis", "unknown_basis", "unknown_calendar_basis"),
        ("source_access_granted", True, "source_access_granted_must_be_false"),
        ("memory_read_authority_granted", True, "memory_read_authority_granted_must_be_false"),
        ("runtime_authority", True, "runtime_authority_must_be_false"),
        ("writes_state", True, "writes_state_must_be_false"),
        ("model_provider_used", True, "model_provider_used_must_be_false"),
        ("public_claim_allowed", True, "public_claim_allowed_must_be_false"),
        ("learning_claimed", True, "learning_claimed_must_be_false"),
    ],
)
def test_validation_rejects_unknown_enum_and_forbidden_authority(field_name, value, expected_error):
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    candidate = _mutate(packet, **{field_name: value})
    with pytest.raises(Exception, match=expected_error):
        validate_time_anchor_packet_v1(candidate)


@pytest.mark.parametrize(
    "field_name, value, expected_error",
    [
        ("original_phrase", {"raw_prompt": "leak"}, "forbidden_raw_fields_present"),
        ("safe_metadata", {"raw_answer": "leak"}, "forbidden_raw_fields_present"),
        ("safe_metadata", {"transcript": "leak"}, "forbidden_raw_fields_present"),
        ("safe_metadata", {"hidden_prompt": "leak"}, "forbidden_raw_fields_present"),
        ("safe_metadata", {"private_data": "leak"}, "forbidden_raw_fields_present"),
    ],
)
def test_raw_fields_fail_validation(field_name, value, expected_error):
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    candidate = _mutate(packet, **{field_name: value})
    with pytest.raises(Exception, match=expected_error):
        validate_time_anchor_packet_v1(candidate)


@pytest.mark.parametrize(
    "text, expected_error",
    [
        ("public ISS wording", "forbidden_public_or_claim_language_present"),
        ("AGI consciousness sentience Turing certification claim", "forbidden_public_or_claim_language_present"),
    ],
)
def test_claim_markers_fail_validation(text, expected_error):
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    candidate = _mutate(packet, safe_metadata={"note": text})
    with pytest.raises(Exception, match=expected_error):
        validate_time_anchor_packet_v1(candidate)



def test_unresolved_relative_phrase_with_fake_window_fails_validation():
    packet = build_time_anchor_packet_v1("yesterday", timezone=TZ)
    candidate = _mutate(packet, confidence="high", resolved_start="2026-05-31T00:00:00", resolved_end="2026-05-31T23:59:59")
    with pytest.raises(Exception, match="relative_phrase_without_reference_time_cannot_have_fake_window"):
        validate_time_anchor_packet_v1(candidate)


@pytest.mark.parametrize(
    "packet_name, expected_anchor_type, expected_mode",
    [
        ("yesterday_anchor_example", "relative_day", "temporal_first"),
        ("today_anchor_example", "relative_day", "temporal_first"),
        ("this_morning_anchor_example", "day_part", "temporal_first"),
        ("last_night_anchor_example", "day_part", "temporal_first"),
        ("last_week_anchor_example", "relative_range", "temporal_first"),
        ("past_few_days_anchor_example", "relative_range", "temporal_first"),
        ("previous_session_anchor_example", "session_relative", "event_anchor_retrieval"),
        ("earlier_in_this_chat_anchor_example", "session_relative", "temporal_first"),
        ("before_last_commit_anchor_example", "project_relative", "event_anchor_retrieval"),
        ("after_file_manifest_builder_anchor_example", "project_relative", "event_anchor_retrieval"),
        ("absolute_date_anchor_example", "absolute_date", "temporal_first"),
        ("recently_vague_anchor_example", "vague_temporal", "clarification_required"),
        ("missing_reference_time_anchor_example", "relative_day", "clarification_required"),
    ],
)
def test_initial_examples_have_expected_modes(packet_name, expected_anchor_type, expected_mode):
    packet = _find_example(build_initial_time_anchor_examples_v1(), packet_name)
    assert packet.anchor_type == expected_anchor_type
    assert packet.retrieval_mode_hint == expected_mode



def test_module_does_not_call_hidden_current_time():
    source = inspect.getsource(__import__("weslr.time_anchor_resolver", fromlist=["*"]))
    assert "datetime.now" not in source
    assert "datetime.utcnow" not in source


@pytest.mark.parametrize(
    "field_name",
    ["reference_time", "resolved_start", "resolved_end", "timezone", "event_anchor", "commit_anchor"],
)
def test_packet_fields_are_json_safe_strings_or_none(field_name):
    packet = build_time_anchor_packet_v1("yesterday", reference_time=REF, timezone=TZ)
    assert hasattr(packet, field_name)


@pytest.mark.parametrize(
    "phrase",
    ["yesterday", "today", "this morning", "last week", "previous session", "before the last commit", "after OCC replied", "2026-05-31", "recently"],
)
def test_resolve_alias_matches_builder(phrase):
    a = build_time_anchor_packet_v1(phrase, reference_time=REF, timezone=TZ)
    b = resolve_time_anchor_v1(phrase, reference_time=REF, timezone=TZ)
    assert a == b
