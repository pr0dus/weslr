from __future__ import annotations

import sys

import pytest

from weslr.memory_source_scope_registry import (
    MemorySourceScopeRecord,
    MemorySourceScopeRegistry,
    MemorySourceScopeResolution,
    ValidationError,
    build_initial_memory_source_scope_examples_v1,
    build_memory_source_scope_record_v1,
    build_memory_source_scope_registry_v1,
    resolve_memory_source_scope_v1,
    summarize_memory_source_scope_registry_v1,
    to_memory_source_scope_json_safe_v1,
    validate_memory_source_scope_record_v1,
    validate_memory_source_scope_registry_v1,
)
from weslr.temporal_memory_retrieval_plan import (
    build_temporal_memory_retrieval_plan_v1,
    validate_temporal_memory_retrieval_plan_v1,
)


def _example_by_name(name: str):
    for example in build_initial_memory_source_scope_examples_v1():
        metadata = getattr(example, "safe_metadata", None) or {}
        if metadata.get("example_name") == name:
            return example
    raise AssertionError(f"missing example {name}")


def _record_map(record: MemorySourceScopeRecord) -> dict:
    return to_memory_source_scope_json_safe_v1(record)


def _registry_map(registry: MemorySourceScopeRegistry) -> dict:
    return to_memory_source_scope_json_safe_v1(registry)


def _resolution_map(resolution: MemorySourceScopeResolution) -> dict:
    return to_memory_source_scope_json_safe_v1(resolution)


def test_module_imports_safely():
    import weslr.memory_source_scope_registry as mod

    assert mod.HELPER_TYPE_V1 == "memory_source_scope_registry_v1"
    assert mod.MEMORY_SOURCE_SCOPE_RECORD_TYPE_V1 == "memory_source_scope_record_v1"
    assert mod.MEMORY_SOURCE_SCOPE_REGISTRY_TYPE_V1 == "memory_source_scope_registry_v1"
    assert mod.SOURCE_RESOLUTION_TYPE_V1 == "memory_source_scope_resolution_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_source_scope_record():
    first = build_memory_source_scope_record_v1(
        "current_conversation",
        source_label="Current Conversation",
        description="Current conversation scope.",
        content_level="owner_visible_content",
        authority_required="no_authority",
        default_access_decision="allow_summary_only",
        raw_access_allowed=False,
        summary_access_allowed=True,
        metadata_access_allowed=True,
        safe_metadata={"example_name": "deterministic_record"},
    )
    second = build_memory_source_scope_record_v1(
        "current_conversation",
        source_label="Current Conversation",
        description="Current conversation scope.",
        content_level="owner_visible_content",
        authority_required="no_authority",
        default_access_decision="allow_summary_only",
        raw_access_allowed=False,
        summary_access_allowed=True,
        metadata_access_allowed=True,
        safe_metadata={"example_name": "deterministic_record"},
    )
    assert first == second


def test_builds_deterministic_registry():
    first = build_memory_source_scope_registry_v1()
    second = build_memory_source_scope_registry_v1()
    assert first == second


def test_validates_normal_record():
    record = _example_by_name("current_conversation_scope_record")
    assert validate_memory_source_scope_record_v1(record) is True


def test_validates_normal_registry():
    registry = build_memory_source_scope_registry_v1()
    assert validate_memory_source_scope_registry_v1(registry) is True


def test_json_safe_export_works():
    registry = build_memory_source_scope_registry_v1()
    exported = to_memory_source_scope_json_safe_v1(registry)
    assert isinstance(exported, dict)
    assert isinstance(exported["records"], list)
    assert isinstance(exported["records"][0], dict)
    assert exported["registry_type"] == "memory_source_scope_registry_v1"


def test_summary_includes_source_classes_and_access_decisions():
    summary = summarize_memory_source_scope_registry_v1(build_memory_source_scope_registry_v1())
    assert summary.summary_type == "memory_source_scope_registry_summary_v1"
    assert "current_conversation" in summary.source_classes
    assert "allow_summary_only" in summary.access_decisions
    assert "blocked_by_default" in summary.access_decisions


def test_initial_examples_exist():
    assert len(build_initial_memory_source_scope_examples_v1()) >= 15


@pytest.mark.parametrize(
    "name",
    [
        "current_conversation_scope_record",
        "prior_conversation_summary_scope_record",
        "project_memory_scope_record",
        "repo_commit_metadata_scope_record",
        "lane_report_metadata_scope_record",
        "uploaded_file_reference_scope_record",
        "approved_memory_index_scope_record",
        "runtime_session_log_scope_record",
        "weslr_state_scope_record",
        "unknown_source_scope_record",
        "yesterday_temporal_source_resolution",
        "earlier_chat_source_resolution",
        "before_file_manifest_source_resolution",
        "runtime_log_blocked_resolution",
        "weslr_state_blocked_resolution",
    ],
)
def test_named_initial_examples_exist(name):
    example = _example_by_name(name)
    assert example.safe_metadata["example_name"] == name


def test_current_conversation_allows_summary_metadata_only():
    record = _example_by_name("current_conversation_scope_record")
    assert record.content_level == "owner_visible_content"
    assert record.default_access_decision == "allow_summary_only"
    assert record.raw_access_allowed is False
    assert record.cross_user_allowed is False


def test_prior_conversation_summary_allows_summary_only():
    record = _example_by_name("prior_conversation_summary_scope_record")
    assert record.content_level == "summary_only"
    assert record.default_access_decision == "allow_summary_only"
    assert record.raw_access_allowed is False


def test_project_memory_is_scoped_and_not_cross_project_by_default():
    record = _example_by_name("project_memory_scope_record")
    assert record.cross_project_allowed is False
    assert record.default_access_decision == "allow_summary_only"


def test_repo_commit_metadata_is_metadata_only():
    record = _example_by_name("repo_commit_metadata_scope_record")
    assert record.content_level == "metadata_only"
    assert record.default_access_decision == "allow_metadata_only"


def test_lane_report_metadata_supports_event_anchors():
    record = _example_by_name("lane_report_metadata_scope_record")
    assert record.event_anchor_supported is True
    assert record.commit_anchor_supported is True


def test_uploaded_file_reference_requires_source_authority():
    record = _example_by_name("uploaded_file_reference_scope_record")
    assert record.default_access_decision == "requires_owner_authority"
    assert record.authority_required == "owner_content_authority"


def test_approved_memory_index_is_summary_only():
    record = _example_by_name("approved_memory_index_scope_record")
    assert record.content_level == "summary_only"
    assert record.default_access_decision == "allow_summary_only"


def test_runtime_session_log_is_blocked_or_authority_required():
    record = _example_by_name("runtime_session_log_scope_record")
    assert record.default_access_decision == "blocked_by_default"
    assert record.authority_required == "operator_runtime_authority"


def test_weslr_state_is_blocked_by_default():
    record = _example_by_name("weslr_state_scope_record")
    assert record.default_access_decision == "blocked_by_default"
    assert record.content_level == "private_state"


def test_unknown_source_is_blocked_or_clarification():
    record = _example_by_name("unknown_source_scope_record")
    assert record.default_access_decision == "unknown_blocked"
    assert record.content_level == "unknown_content"


def test_temporal_first_resolution_prefers_approved_memory_prior_summaries_project_memory():
    resolution = _example_by_name("yesterday_temporal_source_resolution")
    assert resolution.selected_source_priority[:3] == (
        "approved_memory_index",
        "prior_conversation_summary",
        "project_memory",
    )
    assert "approved_memory_index" in resolution.allowed_sources


def test_session_order_resolution_prefers_current_conversation():
    resolution = _example_by_name("earlier_chat_source_resolution")
    assert resolution.selected_source_priority[0] == "current_conversation"
    assert "current_conversation" in resolution.allowed_sources


def test_event_anchor_resolution_prefers_lane_report_and_commit_metadata():
    resolution = _example_by_name("before_file_manifest_source_resolution")
    assert resolution.selected_source_priority[:2] == (
        "lane_report_metadata",
        "repo_commit_metadata",
    )


def test_blocked_no_source_plan_remains_blocked():
    resolution = _example_by_name("runtime_log_blocked_resolution")
    assert resolution.safe_result_format == "blocked_authority_required"
    assert resolution.allowed_sources == tuple()
    assert resolution.blocked_sources


def test_blocked_no_authority_plan_remains_authority_required():
    resolution = _example_by_name("weslr_state_blocked_resolution")
    assert resolution.effective_access_decision == "requires_owner_authority"
    assert resolution.authority_missing is True


@pytest.mark.parametrize(
    "field_name",
    [
        "memory_read_authority_granted",
        "source_access_granted",
        "raw_access_allowed",
        "private_data_access_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_no_initial_example_grants_restricted_authority(field_name):
    for example in build_initial_memory_source_scope_examples_v1():
        if hasattr(example, field_name):
            assert getattr(example, field_name) is False


@pytest.mark.parametrize(
    "field_name, bad_value, expected_error",
    [
        ("source_class", "mystery_source", "unknown_source_class"),
        ("content_level", "mystery_content", "unknown_content_level"),
        ("default_access_decision", "mystery_decision", "unknown_access_decision"),
        ("authority_required", "mystery_authority", "unknown_authority_level"),
        ("safe_result_format", "mystery_format", "unknown_safe_result_format"),
    ],
)
def test_validation_rejects_unknown_enumerations(field_name, bad_value, expected_error):
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record[field_name] = bad_value
    with pytest.raises(ValidationError, match=expected_error):
        validate_memory_source_scope_record_v1(record)


def test_validation_rejects_cross_user_true():
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record["cross_user_allowed"] = True
    with pytest.raises(ValidationError, match="cross_user_allowed_must_be_false"):
        validate_memory_source_scope_record_v1(record)


def test_validation_rejects_raw_access_true_for_default_record():
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record["raw_access_allowed"] = True
    with pytest.raises(ValidationError, match="raw_access_allowed_must_be_false"):
        validate_memory_source_scope_record_v1(record)


def test_validation_rejects_private_data_access_true():
    resolution = _resolution_map(_example_by_name("yesterday_temporal_source_resolution"))
    resolution["private_data_access_allowed"] = True
    from weslr.memory_source_scope_registry import validate_memory_source_scope_resolution_v1
    with pytest.raises(ValidationError, match="private_data_access_allowed_must_be_false"):
        validate_memory_source_scope_resolution_v1(resolution)


@pytest.mark.parametrize(
    "field_name",
    [
        "memory_read_authority_granted",
        "source_access_granted",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_validation_rejects_resolution_restricted_authority_true(field_name):
    resolution = _resolution_map(_example_by_name("yesterday_temporal_source_resolution"))
    resolution[field_name] = True
    from weslr.memory_source_scope_registry import validate_memory_source_scope_resolution_v1
    with pytest.raises(ValidationError):
        validate_memory_source_scope_resolution_v1(resolution)


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
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record[field_name] = bad_value
    with pytest.raises(ValidationError):
        validate_memory_source_scope_record_v1(record)


def test_validation_rejects_public_iss_and_claim_markers():
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record["safe_metadata"] = {"notes": "public ISS wording and AGI claim"}
    with pytest.raises(ValidationError):
        validate_memory_source_scope_record_v1(record)


def test_non_blocked_record_with_no_accessibility_fails_validation():
    record = _record_map(_example_by_name("current_conversation_scope_record"))
    record["default_access_decision"] = "mystery_decision"
    with pytest.raises(ValidationError, match="unknown_access_decision"):
        validate_memory_source_scope_record_v1(record)


def test_module_does_not_import_or_call_protected_files():
    import weslr.memory_source_scope_registry as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "build_memory_source_scope_registry_v1")


def test_resolution_record_and_registry_examples_have_safe_metadata_names():
    for name in [
        "yesterday_temporal_source_resolution",
        "earlier_chat_source_resolution",
        "before_file_manifest_source_resolution",
        "runtime_log_blocked_resolution",
        "weslr_state_blocked_resolution",
    ]:
        example = _example_by_name(name)
        assert example.safe_metadata["example_name"] == name
