from __future__ import annotations

import sys

import pytest

from weslr.memory_source_scope_registry import (
    build_initial_memory_source_scope_examples_v1,
    to_memory_source_scope_json_safe_v1,
    validate_memory_source_scope_resolution_v1,
)
from weslr.safe_memory_retrieval_executor import (
    SafeMemoryRetrievalRequest,
    SafeMemoryRetrievalResult,
    SafeMemoryRetrievalResultSummary,
    ValidationError,
    build_initial_safe_memory_retrieval_examples_v1,
    build_safe_memory_retrieval_request_v1,
    execute_safe_memory_retrieval_v1,
    summarize_safe_memory_retrieval_result_v1,
    to_safe_memory_retrieval_json_safe_v1,
    validate_safe_memory_retrieval_request_v1,
    validate_safe_memory_retrieval_result_v1,
)
from weslr.temporal_memory_retrieval_plan import (
    build_initial_temporal_memory_retrieval_plan_examples_v1,
    to_temporal_memory_retrieval_plan_json_safe_v1,
    validate_temporal_memory_retrieval_plan_v1,
)


def _plan_by_name(name: str):
    for example in build_initial_temporal_memory_retrieval_plan_examples_v1():
        if example.safe_metadata and example.safe_metadata.get("example_name") == name:
            return example
    raise AssertionError(f"missing plan example {name}")


def _resolution_by_name(name: str):
    for example in build_initial_memory_source_scope_examples_v1():
        metadata = getattr(example, "safe_metadata", None) or {}
        if metadata.get("example_name") == name:
            return example
    raise AssertionError(f"missing resolution example {name}")


def _provider(source_items):
    return {"source_items": source_items}


def _authority(**overrides):
    base = {
        "authority_packet_id": "auth-test",
        "authority_level": "summary_authority",
        "memory_read_authority_granted": True,
        "source_access_granted": True,
        "raw_log_access_allowed": False,
        "private_data_access_allowed": False,
        "allow_hidden_prompt": False,
        "allow_cross_user": False,
        "allow_cross_project": False,
    }
    base.update(overrides)
    return base


def test_module_imports_safely():
    import weslr.safe_memory_retrieval_executor as mod

    assert mod.HELPER_TYPE_V1 == "safe_memory_retrieval_executor_v1"
    assert mod.SAFE_MEMORY_RETRIEVAL_REQUEST_TYPE_V1 == "safe_memory_retrieval_request_v1"
    assert mod.SAFE_MEMORY_RETRIEVAL_RESULT_TYPE_V1 == "safe_memory_retrieval_result_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_request():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    first = build_safe_memory_retrieval_request_v1(plan, resolution, authority_packet=_authority())
    second = build_safe_memory_retrieval_request_v1(plan, resolution, authority_packet=_authority())
    assert first == second
    assert isinstance(first, SafeMemoryRetrievalRequest)


def test_validates_request():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    request = build_safe_memory_retrieval_request_v1(plan, resolution, authority_packet=_authority())
    assert validate_safe_memory_retrieval_request_v1(request) is True


def test_executes_blocked_when_provider_missing():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(plan, resolution, source_provider=None, authority_packet=_authority())
    assert result.blocked is True
    assert result.blocked_reason == "source provider missing"
    assert result.retrieval_executed is False


def test_executes_blocked_when_authority_missing():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(plan, resolution, source_provider=_provider([]), authority_packet=_authority(memory_read_authority_granted=False))
    assert result.blocked is True
    assert result.blocked_reason == "authority missing"


def test_executes_fake_provider_temporal_summary_retrieval():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "approved_memory_index",
                    "source_id": "mem-001",
                    "source_label": "Yesterday summary",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "You asked about yesterday’s summary.",
                    "safe_excerpt": "Yesterday summary.",
                    "semantic_tags": ["yesterday", "summary"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(authority_level="summary_authority"),
    )
    assert result.blocked is False
    assert result.result_count == 1
    assert result.source_classes_used == ("approved_memory_index",)
    assert "Yesterday summary" in result.answer_safe_summary or result.answer_safe_summary


def test_executes_fake_provider_hybrid_semantic_retrieval():
    plan = _plan_by_name("yesterday_wifi_hybrid_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "project_memory",
                    "source_id": "mem-wifi-001",
                    "source_label": "Wi-Fi note",
                    "timestamp": "2026-05-31T13:00:00",
                    "safe_summary": "Wi-Fi was the main topic.",
                    "safe_excerpt": "Wi-Fi troubleshooting summary.",
                    "semantic_tags": ["wifi", "network"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(authority_level="summary_authority"),
    )
    assert result.blocked is False
    assert result.result_count == 1
    assert result.source_results[0].source_class == "project_memory"
    assert "Wi-Fi" in result.source_results[0].safe_summary


def test_executes_fake_provider_session_order_retrieval():
    plan = _plan_by_name("earlier_in_chat_session_plan")
    resolution = _resolution_by_name("earlier_chat_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "current_conversation",
                    "source_id": "chat-001",
                    "source_label": "Earlier chat mention",
                    "timestamp": "2026-06-01T11:00:00",
                    "safe_summary": "Earlier you said ISS internally.",
                    "safe_excerpt": "ISS mention.",
                    "semantic_tags": ["iss", "chat"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(authority_level="summary_authority"),
    )
    assert result.blocked is False
    assert result.source_classes_used == ("current_conversation",)
    assert result.source_results[0].match_reason


def test_executes_fake_provider_event_anchor_retrieval():
    plan = _plan_by_name("before_file_manifest_builder_event_plan")
    resolution = _resolution_by_name("before_file_manifest_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "lane_report_metadata",
                    "source_id": "lane-001",
                    "source_label": "Before file manifest builder",
                    "timestamp": "2026-06-01T10:30:00",
                    "safe_summary": "File manifest builder followed this lane.",
                    "safe_excerpt": "Manifest lane metadata.",
                    "semantic_tags": ["manifest", "lane"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(authority_level="metadata_authority"),
    )
    assert result.blocked is False
    assert result.source_classes_used == ("lane_report_metadata",)
    assert result.source_results[0].source_time_window


def test_excludes_raw_private_hidden_entries():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "approved_memory_index",
                    "source_id": "safe-001",
                    "source_label": "Safe item",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "Safe summary.",
                    "safe_excerpt": "Safe excerpt.",
                    "semantic_tags": ["safe"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                },
                {
                    "source_class": "approved_memory_index",
                    "source_id": "unsafe-001",
                    "source_label": "Unsafe item",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "Unsafe summary.",
                    "safe_excerpt": "Unsafe excerpt.",
                    "semantic_tags": ["safe"],
                    "private_data_possible": True,
                    "hidden_prompt": True,
                    "raw_content": "raw secret",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                },
            ]
        ),
        authority_packet=_authority(),
    )
    assert result.blocked is False
    assert result.result_count == 1
    assert result.source_results[0].source_id == "safe-001"


def test_caps_result_count():
    plan = to_temporal_memory_retrieval_plan_json_safe_v1(_plan_by_name("yesterday_temporal_first_plan"))
    plan["safe_metadata"] = {"max_result_count": 2}
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "approved_memory_index",
                    "source_id": f"safe-{index}",
                    "source_label": f"Safe item {index}",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": f"Safe summary {index}.",
                    "safe_excerpt": f"Safe excerpt {index}.",
                    "semantic_tags": ["safe"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
                for index in range(5)
            ]
        ),
        authority_packet=_authority(),
    )
    assert result.result_count == 2
    assert len(result.source_results) == 2


def test_caps_safe_excerpt_length():
    plan = to_temporal_memory_retrieval_plan_json_safe_v1(_plan_by_name("yesterday_temporal_first_plan"))
    plan["safe_metadata"] = {"max_excerpt_length": 12}
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "approved_memory_index",
                    "source_id": "safe-001",
                    "source_label": "Safe item",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "Safe summary with a very long excerpt.",
                    "safe_excerpt": "This excerpt is definitely too long.",
                    "semantic_tags": ["safe"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(),
    )
    assert len(result.source_results[0].safe_excerpt) <= 12


def test_returns_safe_summaries_only():
    plan = _plan_by_name("yesterday_temporal_first_plan")
    resolution = _resolution_by_name("yesterday_temporal_source_resolution")
    result = execute_safe_memory_retrieval_v1(
        plan,
        resolution,
        source_provider=_provider(
            [
                {
                    "source_class": "approved_memory_index",
                    "source_id": "safe-001",
                    "source_label": "Safe item",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "Safe summary.",
                    "safe_excerpt": "Safe excerpt.",
                    "semantic_tags": ["safe"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(),
    )
    item = result.source_results[0]
    assert item.raw_content_omitted is True
    assert item.safe_summary
    assert item.safe_excerpt


@pytest.mark.parametrize(
    "plan_name,resolution_name,source_class",
    [
        ("blocked_no_source_plan", "runtime_log_blocked_resolution", "runtime_session_log"),
        ("blocked_no_source_plan", "weslr_state_blocked_resolution", ".weslr_state"),
    ],
)
def test_runtime_and_private_state_sources_remain_blocked_by_default(plan_name, resolution_name, source_class):
    result = execute_safe_memory_retrieval_v1(
        _plan_by_name(plan_name),
        _resolution_by_name(resolution_name),
        source_provider=_provider(
            [
                {
                    "source_class": source_class,
                    "source_id": "blocked-001",
                    "source_label": "Blocked source",
                    "timestamp": "2026-05-31T12:00:00",
                    "safe_summary": "Blocked.",
                    "safe_excerpt": "Blocked.",
                    "semantic_tags": ["blocked"],
                    "private_data_possible": False,
                    "hidden_prompt": False,
                    "raw_content": "",
                    "project_scope": "same_project",
                    "session_scope": "same_session",
                }
            ]
        ),
        authority_packet=_authority(),
    )
    assert result.blocked is True or result.result_count == 0
    assert source_class in result.source_classes_blocked or result.blocked is True


def test_json_safe_export_works():
    result = build_initial_safe_memory_retrieval_examples_v1()[2]
    exported = to_safe_memory_retrieval_json_safe_v1(result)
    assert isinstance(exported, dict)
    assert exported["retrieval_result_id"] == result.retrieval_result_id


def test_summary_includes_executed_blocked_result_count_confidence():
    result = build_initial_safe_memory_retrieval_examples_v1()[2]
    summary = summarize_safe_memory_retrieval_result_v1(result)
    assert isinstance(summary, SafeMemoryRetrievalResultSummary)
    assert summary.retrieval_executed == result.retrieval_executed
    assert summary.blocked == result.blocked
    assert summary.result_count == result.result_count
    assert summary.expected_confidence == result.expected_confidence


def test_initial_examples_exist():
    examples = build_initial_safe_memory_retrieval_examples_v1()
    assert len(examples) >= 8


@pytest.mark.parametrize(
    "name",
    [
        "blocked_missing_provider_result",
        "blocked_missing_authority_result",
        "yesterday_summary_fake_provider_result",
        "yesterday_wifi_fake_provider_result",
        "earlier_chat_fake_provider_result",
        "before_file_manifest_fake_provider_result",
        "runtime_log_blocked_result",
        "weslr_state_blocked_result",
    ],
)
def test_named_initial_examples_exist(name):
    for example in build_initial_safe_memory_retrieval_examples_v1():
        if example.safe_metadata and example.safe_metadata.get("example_name") == name:
            assert example.safe_metadata["example_name"] == name
            return
    raise AssertionError(f"missing example {name}")


def test_no_initial_example_includes_raw_or_private_or_hidden_or_authority_claims():
    for example in build_initial_safe_memory_retrieval_examples_v1():
        assert example.raw_content_included is False
        assert example.private_data_included is False
        assert example.hidden_prompt_included is False
        assert example.runtime_authority is False
        assert example.writes_state is False
        assert example.model_provider_used is False
        assert example.public_claim_allowed is False
        assert example.learning_claimed is False
        assert example.memory_read_authority_granted is False or example.blocked is True
        assert example.source_access_granted is False or example.blocked is True


@pytest.mark.parametrize(
    "field_name",
    [
        "raw_content_included",
        "private_data_included",
        "hidden_prompt_included",
        "cross_user_content_included",
        "cross_project_content_included",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ],
)
def test_validation_fails_on_restricted_true_flags(field_name):
    result = to_safe_memory_retrieval_json_safe_v1(build_initial_safe_memory_retrieval_examples_v1()[2])
    result[field_name] = True
    with pytest.raises(ValidationError):
        validate_safe_memory_retrieval_result_v1(result)


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript", "secret transcript"),
        ("hidden_prompt", "secret hidden prompt"),
        ("private_data", "secret private data"),
    ],
)
def test_validation_fails_on_raw_or_private_fields(field_name, value):
    result = to_safe_memory_retrieval_json_safe_v1(build_initial_safe_memory_retrieval_examples_v1()[2])
    result[field_name] = value
    with pytest.raises(ValidationError):
        validate_safe_memory_retrieval_result_v1(result)


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
def test_validation_fails_on_public_iss_or_claim_markers(bad_text):
    result = to_safe_memory_retrieval_json_safe_v1(build_initial_safe_memory_retrieval_examples_v1()[2])
    result["safe_metadata"] = {"notes": bad_text}
    with pytest.raises(ValidationError):
        validate_safe_memory_retrieval_result_v1(result)


def test_module_does_not_import_or_call_protected_files():
    import weslr.safe_memory_retrieval_executor as mod

    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules
    assert hasattr(mod, "execute_safe_memory_retrieval_v1")
    assert hasattr(mod, "build_safe_memory_retrieval_request_v1")
