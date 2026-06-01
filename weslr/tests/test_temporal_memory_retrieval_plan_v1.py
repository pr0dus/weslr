from __future__ import annotations

import sys

import pytest

from weslr.temporal_memory_retrieval_plan import (
    TemporalMemoryRetrievalPlan,
    ValidationError,
    build_initial_temporal_memory_retrieval_plan_examples_v1,
    build_temporal_memory_retrieval_plan_from_anchor_v1,
    build_temporal_memory_retrieval_plan_v1,
    summarize_temporal_memory_retrieval_plan_v1,
    to_temporal_memory_retrieval_plan_json_safe_v1,
    validate_temporal_memory_retrieval_plan_v1,
)
from weslr.time_anchor_resolver import build_time_anchor_packet_v1


def _example_by_name(name: str) -> TemporalMemoryRetrievalPlan:
    for example in build_initial_temporal_memory_retrieval_plan_examples_v1():
        if example.safe_metadata and example.safe_metadata.get("example_name") == name:
            return example
    raise AssertionError(f"missing example {name}")


def _plan_map(plan: TemporalMemoryRetrievalPlan) -> dict:
    return to_temporal_memory_retrieval_plan_json_safe_v1(plan)


def test_module_imports_safely():
    import weslr.temporal_memory_retrieval_plan as mod

    assert mod.HELPER_TYPE_V1 == "temporal_memory_retrieval_plan_v1"
    assert mod.TEMPORAL_MEMORY_RETRIEVAL_PLAN_TYPE_V1 == "temporal_memory_retrieval_plan_v1"
    assert mod.SUMMARY_TYPE_V1 == "temporal_memory_retrieval_plan_summary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_retrieval_plan():
    first = build_temporal_memory_retrieval_plan_v1(
        "yesterday",
        reference_time="2026-06-01T12:00:00",
        timezone="Europe/Berlin",
        available_sources=("approved_memory_index", "prior_conversation_summary", "project_memory"),
    )
    second = build_temporal_memory_retrieval_plan_v1(
        "yesterday",
        reference_time="2026-06-01T12:00:00",
        timezone="Europe/Berlin",
        available_sources=("approved_memory_index", "prior_conversation_summary", "project_memory"),
    )
    assert first == second


def test_builds_plan_from_time_anchor_packet():
    anchor = build_time_anchor_packet_v1(
        "yesterday",
        reference_time="2026-06-01T12:00:00",
        timezone="Europe/Berlin",
        safe_metadata={"example_name": "time_anchor_for_retrieval_plan"},
    )
    plan = build_temporal_memory_retrieval_plan_from_anchor_v1(
        anchor,
        available_sources=("approved_memory_index", "prior_conversation_summary"),
    )
    assert plan.source_time_anchor_id == anchor.time_anchor_id
    assert plan.original_phrase == anchor.original_phrase
    assert plan.anchor_type == anchor.anchor_type
    assert validate_temporal_memory_retrieval_plan_v1(plan) is True


def test_validates_normal_plan():
    plan = _example_by_name("yesterday_temporal_first_plan")
    assert validate_temporal_memory_retrieval_plan_v1(plan) is True


def test_json_safe_export_works():
    plan = _example_by_name("yesterday_wifi_hybrid_plan")
    exported = to_temporal_memory_retrieval_plan_json_safe_v1(plan)
    assert isinstance(exported, dict)
    assert exported["retrieval_mode"] == plan.retrieval_mode
    assert isinstance(exported["candidate_source_classes"], list)
    assert exported["source_scope"] == plan.source_scope


def test_summary_includes_retrieval_mode_source_confidence():
    plan = _example_by_name("earlier_in_chat_session_plan")
    summary = summarize_temporal_memory_retrieval_plan_v1(plan)
    assert summary.summary_type == "temporal_memory_retrieval_plan_summary_v1"
    assert summary.retrieval_mode == plan.retrieval_mode
    assert summary.source_scope == plan.source_scope
    assert summary.expected_confidence == plan.expected_confidence


def test_initial_examples_exist():
    examples = build_initial_temporal_memory_retrieval_plan_examples_v1()
    assert len(examples) >= 8


@pytest.mark.parametrize(
    "name, expected_mode",
    [
        ("yesterday_temporal_first_plan", "temporal_first"),
        ("yesterday_wifi_hybrid_plan", "hybrid_temporal_semantic"),
        ("earlier_in_chat_session_plan", "session_order_retrieval"),
        ("before_file_manifest_builder_event_plan", "event_anchor_retrieval"),
        ("recently_vague_clarification_plan", "clarification_required"),
        ("last_week_public_wording_hybrid_plan", "hybrid_temporal_semantic"),
        ("blocked_no_source_plan", "blocked_no_source"),
        ("blocked_no_authority_plan", "blocked_no_authority"),
    ],
)
def test_named_examples_have_expected_modes(name, expected_mode):
    plan = _example_by_name(name)
    assert plan.retrieval_mode == expected_mode


@pytest.mark.parametrize(
    "field_name",
    [
        "memory_read_authority_granted",
        "source_access_granted",
        "raw_log_access_allowed",
        "private_data_access_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_no_initial_example_grants_restricted_authority(field_name):
    for example in build_initial_temporal_memory_retrieval_plan_examples_v1():
        assert getattr(example, field_name) is False


@pytest.mark.parametrize(
    "field_name, bad_value, expected_error",
    [
        ("retrieval_mode", "mystery_mode", "unknown_retrieval_mode"),
        ("candidate_source_classes", ("mystery_source",), "unknown_source_class"),
        ("source_priority", ("mystery_source",), "unknown_source_class"),
        ("expected_confidence", "certain", "unknown_expected_confidence"),
        ("ranking_strategy", "mystery_strategy", "unknown_ranking_strategy"),
        ("recommended_next_step", "mystery_step", "unknown_next_step"),
    ],
)
def test_validation_rejects_unknown_enumerations(field_name, bad_value, expected_error):
    plan = _plan_map(_example_by_name("yesterday_temporal_first_plan"))
    plan[field_name] = bad_value
    with pytest.raises(ValidationError, match=expected_error):
        validate_temporal_memory_retrieval_plan_v1(plan)


@pytest.mark.parametrize(
    "field_name",
    [
        "memory_read_authority_granted",
        "source_access_granted",
        "raw_log_access_allowed",
        "private_data_access_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_validation_rejects_restricted_authority_true(field_name):
    plan = _plan_map(_example_by_name("yesterday_temporal_first_plan"))
    plan[field_name] = True
    with pytest.raises(ValidationError):
        validate_temporal_memory_retrieval_plan_v1(plan)


@pytest.mark.parametrize(
    "field_name, bad_value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript", "secret transcript"),
        ("hidden_prompt", "secret hidden prompt"),
        ("private_data", "secret private data"),
    ],
)
def test_validation_rejects_raw_or_private_fields(field_name, bad_value):
    plan = _plan_map(_example_by_name("yesterday_temporal_first_plan"))
    plan[field_name] = bad_value
    with pytest.raises(ValidationError):
        validate_temporal_memory_retrieval_plan_v1(plan)


@pytest.mark.parametrize(
    "bad_text",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "sentience claim",
        "Turing test claim",
        "certification claim",
    ],
)
def test_validation_rejects_public_iss_and_claim_markers(bad_text):
    plan = _plan_map(_example_by_name("yesterday_temporal_first_plan"))
    plan["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError):
        validate_temporal_memory_retrieval_plan_v1(plan)


def test_non_blocked_plan_without_source_classes_fails_validation():
    plan = _plan_map(_example_by_name("yesterday_temporal_first_plan"))
    plan["candidate_source_classes"] = []
    plan["source_priority"] = []
    with pytest.raises(ValidationError, match="non_blocked_plan_requires_source_classes"):
        validate_temporal_memory_retrieval_plan_v1(plan)


def test_blocked_plan_with_high_confidence_fails_validation():
    plan = _plan_map(_example_by_name("blocked_no_source_plan"))
    plan["expected_confidence"] = "high"
    with pytest.raises(ValidationError, match="blocked_plan_must_be_blocked_confidence"):
        validate_temporal_memory_retrieval_plan_v1(plan)


def test_vague_temporal_high_confidence_without_clarification_fails_validation():
    plan = _plan_map(_example_by_name("recently_vague_clarification_plan"))
    plan["expected_confidence"] = "high"
    plan["needs_clarification"] = False
    with pytest.raises(ValidationError, match="vague_plan_cannot_be_high_confidence"):
        validate_temporal_memory_retrieval_plan_v1(plan)


def test_yesterday_plan_is_temporal_first():
    assert _example_by_name("yesterday_temporal_first_plan").retrieval_mode == "temporal_first"


def test_yesterday_wifi_plan_is_hybrid_temporal_semantic():
    plan = _example_by_name("yesterday_wifi_hybrid_plan")
    assert plan.retrieval_mode == "hybrid_temporal_semantic"
    assert plan.semantic_query_present is True
    assert plan.retrieval_mode == "hybrid_temporal_semantic"


def test_earlier_in_chat_plan_is_session_order_retrieval():
    plan = _example_by_name("earlier_in_chat_session_plan")
    assert plan.retrieval_mode == "session_order_retrieval"
    assert plan.ranking_strategy == "session_order_nearest"


def test_before_file_manifest_builder_plan_is_event_anchor_retrieval():
    plan = _example_by_name("before_file_manifest_builder_event_plan")
    assert plan.retrieval_mode == "event_anchor_retrieval"
    assert plan.ranking_strategy in {"event_anchor_before_after", "commit_order_before_after"}


def test_recently_plan_asks_clarification_or_low_confidence():
    plan = _example_by_name("recently_vague_clarification_plan")
    assert plan.retrieval_mode == "clarification_required"
    assert plan.needs_clarification is True
    assert plan.expected_confidence in {"low", "unresolved"}


def test_blocked_no_source_plan_is_blocked():
    plan = _example_by_name("blocked_no_source_plan")
    assert plan.retrieval_mode == "blocked_no_source"
    assert plan.expected_confidence == "blocked"
    assert plan.recommended_next_step == "blocked_wait_for_source"


def test_blocked_no_authority_plan_is_blocked():
    plan = _example_by_name("blocked_no_authority_plan")
    assert plan.retrieval_mode == "blocked_no_authority"
    assert plan.expected_confidence == "blocked"
    assert plan.recommended_next_step in {"request_memory_authority", "request_source_authority"}


@pytest.mark.parametrize(
    "example_name",
    [
        "yesterday_temporal_first_plan",
        "yesterday_wifi_hybrid_plan",
        "earlier_in_chat_session_plan",
        "before_file_manifest_builder_event_plan",
        "recently_vague_clarification_plan",
        "last_week_public_wording_hybrid_plan",
        "blocked_no_source_plan",
        "blocked_no_authority_plan",
    ],
)
def test_example_safe_metadata_contains_name(example_name):
    plan = _example_by_name(example_name)
    assert plan.safe_metadata["example_name"] == example_name


@pytest.mark.parametrize(
    "example_name",
    [
        "yesterday_temporal_first_plan",
        "yesterday_wifi_hybrid_plan",
        "earlier_in_chat_session_plan",
        "before_file_manifest_builder_event_plan",
        "recently_vague_clarification_plan",
        "last_week_public_wording_hybrid_plan",
        "blocked_no_source_plan",
        "blocked_no_authority_plan",
    ],
)
def test_example_source_scope_is_safe(example_name):
    plan = _example_by_name(example_name)
    assert plan.source_scope in {
        "current_conversation",
        "prior_conversation_summary",
        "project_memory",
        "repo_commit_metadata",
        "lane_report_metadata",
        "uploaded_file_reference",
        "approved_memory_index",
        "runtime_session_log",
        ".weslr_state",
        "unknown_source",
    }


@pytest.mark.parametrize(
    "example_name",
    [
        "yesterday_temporal_first_plan",
        "yesterday_wifi_hybrid_plan",
        "earlier_in_chat_session_plan",
        "before_file_manifest_builder_event_plan",
        "recently_vague_clarification_plan",
        "last_week_public_wording_hybrid_plan",
        "blocked_no_source_plan",
        "blocked_no_authority_plan",
    ],
)
def test_example_has_safe_constraints_and_boundaries(example_name):
    plan = _example_by_name(example_name)
    assert "no raw private dump" in plan.result_constraints
    assert "do not fabricate memory" in plan.answer_boundary
