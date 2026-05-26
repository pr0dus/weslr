import builtins
import importlib

import pytest

from weslr.source_scope import (
    DENIED_AUTHORITY_FIELDS,
    build_source_scope_v1,
    render_source_scope_markdown_v1,
    require_source_scope_for_candidate_v1,
    summarize_source_scope_v1,
    to_source_scope_json_safe_v1,
    validate_source_scope_v1,
)


def valid_user_scope(**overrides):
    data = dict(
        source_scope_id="scope_synthetic_user_001",
        tenant_id="tenant_synthetic",
        account_id="acct_synthetic",
        user_id="user_synthetic",
        session_id="sess_synthetic",
        conversation_id="conv_synthetic",
        workspace_id="workspace_synthetic",
        project_id="project_synthetic",
        memory_scope_id="memory_synthetic",
        locale="en-US",
        language="en",
        source_kind="memory",
        source_ref="opaque_memory_ref",
        source_owner_kind="user",
        allowed_use_contexts=["candidate_metadata", "authority_checkpoint", "shadow_validation"],
        retention_label="session",
        privacy_label="user_private",
        currentness_label="current",
        provenance_label="synthetic",
    )
    data.update(overrides)
    return build_source_scope_v1(**data)


def valid_guest_scope(**overrides):
    data = dict(
        source_scope_id="scope_synthetic_guest_001",
        tenant_id="tenant_guest_synthetic",
        guest_id="guest_synthetic",
        session_id="sess_guest_synthetic",
        conversation_id="conv_guest_synthetic",
        locale="en-US",
        language="en",
        source_kind="synthetic_fixture",
        source_ref="opaque_guest_ref",
        source_owner_kind="guest",
        allowed_use_contexts=["candidate_metadata", "shadow_validation"],
        retention_label="ephemeral",
        privacy_label="synthetic",
        currentness_label="synthetic",
        provenance_label="synthetic",
    )
    data.update(overrides)
    return build_source_scope_v1(**data)


def assert_blocked(scope, reason_fragment):
    result = validate_source_scope_v1(scope)
    assert result["valid"] is False
    assert any(reason_fragment in reason for reason in result["blocked_reasons"])
    return result


def test_import_safety():
    module = importlib.import_module("weslr.source_scope")
    assert module.SCHEMA_VERSION == "weslr.source_scope.v1"


def test_valid_user_scoped_source_scope():
    result = validate_source_scope_v1(valid_user_scope())
    assert result["valid"] is True
    assert result["validation_status"] == "valid"
    assert result["denied_authority"] == {field: False for field in DENIED_AUTHORITY_FIELDS}


def test_valid_guest_scoped_source_scope_if_guest_id_provided():
    result = validate_source_scope_v1(valid_guest_scope())
    assert result["valid"] is True
    assert result["guest_id"] == "guest_synthetic"


def test_rejects_missing_tenant_id():
    assert_blocked(valid_user_scope(tenant_id=None), "missing_tenant_id")


def test_rejects_missing_session_id_and_conversation_id_where_required():
    result = validate_source_scope_v1(valid_user_scope(session_id=None, conversation_id=None))
    assert result["valid"] is False
    assert "missing_session_id" in result["blocked_reasons"]
    assert "missing_conversation_id" in result["blocked_reasons"]


def test_rejects_missing_account_user_or_guest_identity():
    assert_blocked(valid_user_scope(account_id=None, user_id=None), "missing_account_user_or_guest_identity")


def test_rejects_query_string_only_identity():
    result = validate_source_scope_v1(
        valid_user_scope(identity_source="query_string", query_string_user_id="user_synthetic")
    )
    assert result["valid"] is False
    assert "unsafe_identity_source" in result["blocked_reasons"]
    assert "query_string_user_id_not_identity_authority" in result["blocked_reasons"]


def test_rejects_global_dot_weslr():
    assert_blocked(valid_user_scope(source_ref=".weslr"), "global_dot_weslr_invalid_for_public_scope")


def test_rejects_tl_default():
    assert_blocked(valid_user_scope(memory_scope_id="tl_default"), "tl_default_invalid_shared_user_scope")


def test_rejects_process_global_inference():
    assert_blocked(valid_user_scope(scope_inference="process_global"), "process_global_or_implicit_scope_inference_rejected")


@pytest.mark.parametrize(
    "source_kind,field",
    [
        ("artifact", "artifact_id"),
        ("upload", "upload_id"),
        ("cache", "cache_scope_id"),
        ("trace", "trace_scope_id"),
    ],
)
def test_rejects_unscoped_artifact_upload_cache_trace(source_kind, field):
    kwargs = {"source_kind": source_kind, field: None}
    result = validate_source_scope_v1(valid_user_scope(**kwargs))
    assert result["valid"] is False
    assert f"unscoped_{source_kind}" in result["blocked_reasons"]


def test_rejects_cross_user_mixing():
    result = validate_source_scope_v1(
        valid_user_scope(cross_user=True, contains_raw_private_material=True)
    )
    assert result["valid"] is False
    assert "unsafe_cross_user_source_mixing" in result["blocked_reasons"]


def test_rejects_missing_denied_authority_fields():
    scope = valid_user_scope()
    scope["denied_authority"].pop("permits_provider_calls")
    result = validate_source_scope_v1(scope)
    assert result["valid"] is False
    assert "missing_denied_authority:permits_provider_calls" in result["blocked_reasons"]


def test_rejects_true_denied_authority_fields():
    scope = valid_user_scope(denied_authority={"permits_final_answer_generation": True})
    result = validate_source_scope_v1(scope)
    assert result["valid"] is False
    assert "denied_authority_true:permits_final_answer_generation" in result["blocked_reasons"]


def test_rejects_non_json_safe_values():
    scope = valid_user_scope()
    scope["bad_set"] = {"not", "json"}
    result = validate_source_scope_v1(scope)
    assert result["valid"] is False
    assert "non_json_safe_value" in result["blocked_reasons"]
    with pytest.raises(ValueError):
        to_source_scope_json_safe_v1(scope)


def test_json_safe_export():
    exported = to_source_scope_json_safe_v1(valid_user_scope())
    assert exported["schema_version"] == "weslr.source_scope.v1"
    assert exported["source_ref"] == "opaque_memory_ref"


def test_markdown_rendering_is_safe_and_metadata_only():
    markdown = render_source_scope_markdown_v1(validate_source_scope_v1(valid_user_scope()))
    assert "# Source Scope Metadata V1" in markdown
    assert "metadata_only" in markdown
    assert "grants_runtime_authority" in markdown
    assert "opaque_memory_ref" not in markdown


def test_summary_is_metadata_only():
    summary = summarize_source_scope_v1(validate_source_scope_v1(valid_user_scope()))
    assert summary["source_scope_id"] == "scope_synthetic_user_001"
    assert "source_ref" not in summary


def test_candidate_requirement_rejects_missing_source_scope():
    result = require_source_scope_for_candidate_v1(
        {"referenced_source_kinds": ["memory"], "candidate_id": "candidate_synthetic"}
    )
    assert result["valid"] is False
    assert "candidate_references_stateful_source_without_scope" in result["blocked_reasons"]
    assert "missing_source_scope" in result["blocked_reasons"]


def test_candidate_requirement_accepts_valid_source_scope():
    result = require_source_scope_for_candidate_v1(
        {
            "candidate_id": "candidate_synthetic",
            "referenced_source_kinds": ["memory"],
            "source_scope": valid_user_scope(),
        }
    )
    assert result["valid"] is True
    assert result["source_scope_summary"]["source_scope_id"] == "scope_synthetic_user_001"


def test_candidate_requirement_rejects_forbidden_authority_implication():
    result = require_source_scope_for_candidate_v1(
        {
            "candidate_id": "candidate_synthetic",
            "source_scope": valid_user_scope(),
            "permits_provider_calls": True,
        }
    )
    assert result["valid"] is False
    assert "candidate_implies_forbidden_authority:permits_provider_calls" in result["blocked_reasons"]


def test_no_filesystem_network_provider_database_runtime_calls(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed")

    monkeypatch.setattr(builtins, "open", fail_open)
    scope = valid_user_scope()
    assert validate_source_scope_v1(scope)["valid"] is True
    assert require_source_scope_for_candidate_v1({"source_scope": scope})["valid"] is True
    assert "Source Scope Metadata" in render_source_scope_markdown_v1(scope)
