import builtins
import importlib

import pytest

from weslr.read_authorization import build_read_authorization_request_v1
from weslr.scoped_memory_context_read_adapter import (
    ALLOWED_READ_MODES,
    DEFAULT_DENIED_AUTHORITY,
    FORBIDDEN_READ_MODES,
    SCHEMA_VERSION,
    authorize_scoped_memory_context_read_request_v1,
    build_scoped_memory_context_read_envelope_v1,
    build_scoped_memory_context_read_request_v1,
    render_scoped_memory_context_read_adapter_markdown_v1,
    summarize_scoped_memory_context_read_adapter_v1,
    to_scoped_memory_context_read_adapter_json_safe_v1,
    validate_scoped_memory_context_read_envelope_v1,
    validate_scoped_memory_context_read_request_v1,
)
from weslr.source_scope import build_source_scope_v1


def valid_source_scope(**overrides):
    data = dict(
        source_scope_id="scope_adapter_synthetic_001",
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
        source_ref="opaque_memory_ref_not_rendered",
        source_owner_kind="user",
        allowed_use_contexts=["candidate_metadata", "authority_checkpoint", "shadow_validation", "safe_assembly_shadow", "internal_review"],
        retention_label="session",
        privacy_label="user_private",
        currentness_label="current",
        provenance_label="synthetic",
    )
    data.update(overrides)
    return build_source_scope_v1(**data)


def requester_scope(**overrides):
    data = dict(
        tenant_id="tenant_synthetic",
        account_id="acct_synthetic",
        user_id="user_synthetic",
        guest_id=None,
        session_id="sess_synthetic",
        conversation_id="conv_synthetic",
        workspace_id="workspace_synthetic",
        project_id="project_synthetic",
    )
    data.update(overrides)
    return data


def target_scope(**overrides):
    return requester_scope(**overrides)


def valid_request(**overrides):
    data = dict(
        request_id="adapter_req_synthetic_001",
        read_kind="memory",
        source_scope=valid_source_scope(),
        requester_scope=requester_scope(),
        target_scope=target_scope(),
        requested_use_context="candidate_metadata",
        requested_content_mode="metadata_only_preview",
        read_mode="metadata_only_preview",
        privacy_label="user_private",
        retention_label="session",
        provenance_label="synthetic",
        currentness_label="current",
        policy_label="synthetic_metadata_only",
    )
    data.update(overrides)
    return build_scoped_memory_context_read_request_v1(**data)


def envelope_for(**overrides):
    return build_scoped_memory_context_read_envelope_v1(valid_request(**overrides))


def assert_request_blocked(request, reason_fragment):
    result = validate_scoped_memory_context_read_request_v1(request)
    assert result["valid"] is False
    assert any(reason_fragment in reason for reason in result["blocked_reasons"])
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["read_status"] == "blocked_no_read"
    return result


def test_import_safety():
    module = importlib.import_module("weslr.scoped_memory_context_read_adapter")
    assert module.SCHEMA_VERSION == "weslr.scoped_memory_context_read_adapter.v1"


def test_valid_metadata_only_preview_path():
    request = valid_request()
    validation = validate_scoped_memory_context_read_request_v1(request)
    assert validation["valid"] is True
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "allowed"
    assert decision["read_mode"] == "metadata_only_preview"
    assert decision["content_included"] is False
    envelope = build_scoped_memory_context_read_envelope_v1(request, decision)
    assert validate_scoped_memory_context_read_envelope_v1(envelope)["valid"] is True


def test_valid_redacted_summary_candidate_path_requires_internal_shadow_authorization():
    request = valid_request(
        request_id="adapter_req_redacted_001",
        requested_use_context="shadow_validation",
        requested_content_mode="redacted_summary_candidate",
        read_mode="redacted_summary_candidate",
        policy_label="internal_shadow",
    )
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "allowed"
    assert decision["central_authorization_decision"]["decision"] == "allow_read_for_internal_shadow_use"
    assert decision["content_included"] is False


def test_valid_continuity_anchor_metadata_path():
    request = valid_request(
        request_id="adapter_req_anchor_001",
        read_kind="continuity_anchor",
        requested_content_mode="continuity_anchor_metadata",
        read_mode="continuity_anchor_metadata",
    )
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "allowed"
    assert decision["read_mode"] == "continuity_anchor_metadata"


def test_valid_evidence_summary_metadata_path():
    request = valid_request(
        request_id="adapter_req_evidence_001",
        read_kind="evidence_summary",
        requested_content_mode="evidence_summary_metadata",
        read_mode="evidence_summary_metadata",
    )
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "allowed"
    assert decision["read_mode"] == "evidence_summary_metadata"


def test_blocked_no_read_path():
    request = valid_request(
        request_id="adapter_req_blocked_001",
        requested_content_mode="blocked_no_read",
        read_mode="blocked_no_read",
    )
    assert validate_scoped_memory_context_read_request_v1(request)["valid"] is True
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "blocked"
    assert decision["read_status"] == "blocked_no_read"
    envelope = build_scoped_memory_context_read_envelope_v1(request, decision)
    assert envelope["read_mode"] == "blocked_no_read"
    assert envelope["content_included"] is False


def test_source_scope_validation_integration():
    request = valid_request()
    validation = validate_scoped_memory_context_read_request_v1(request)
    assert validation["source_scope_summary"]["source_scope_id"] == "scope_adapter_synthetic_001"


def test_read_authorization_integration():
    decision = authorize_scoped_memory_context_read_request_v1(valid_request())
    assert decision["central_authorization_decision"]["decision"] == "allow_metadata_only"


def test_missing_source_scope_blocked():
    assert_request_blocked(valid_request(source_scope=None), "missing_source_scope")


def test_invalid_source_scope_blocked():
    assert_request_blocked(valid_request(source_scope=valid_source_scope(tenant_id=None)), "source_scope:missing_tenant_id")


def test_missing_read_authorization_blocked():
    request = valid_request()
    request.pop("authorization_request")
    assert_request_blocked(request, "missing_read_authorization")


def test_denied_read_authorization_blocked():
    denied_auth = build_read_authorization_request_v1(
        authorization_id="auth_denied_synthetic",
        source_scope=valid_source_scope(),
        requested_read_kind="memory",
        requested_use_context="final_answer",
        requester_scope=requester_scope(),
        target_scope=target_scope(),
        privacy_label="user_private",
        retention_label="session",
        provenance_label="synthetic",
        currentness_label="current",
        policy_label="synthetic_metadata_only",
    )
    request = valid_request(authorization_request=denied_auth)
    decision = authorize_scoped_memory_context_read_request_v1(request)
    assert decision["authorization_status"] == "blocked"
    assert decision["read_status"] == "blocked_no_read"


def test_requester_target_mismatch_blocked():
    assert_request_blocked(valid_request(target_scope=target_scope(session_id="sess_other")), "same_user_different_session")


def test_cross_user_cross_tenant_blocked():
    assert_request_blocked(valid_request(target_scope=target_scope(user_id="user_other")), "cross_user")
    assert_request_blocked(valid_request(target_scope=target_scope(tenant_id="tenant_other")), "cross_tenant")


def test_guest_authenticated_mismatch_blocked():
    request = valid_request(requester_scope=requester_scope(account_id=None, user_id=None, guest_id="guest_synthetic"))
    assert_request_blocked(request, "guest_to_authenticated")


def test_public_browser_private_state_conflict_blocked():
    request = valid_request(public_browser_context=True, privacy_label="operator_private")
    assert_request_blocked(request, "public_browser")


def test_raw_private_content_request_blocked():
    request = valid_request(privacy_label="raw_private")
    assert_request_blocked(request, "raw_private_content_requested")


@pytest.mark.parametrize("mode", sorted(FORBIDDEN_READ_MODES))
def test_each_forbidden_read_mode_blocked(mode):
    request = valid_request(read_mode=mode, requested_content_mode=mode)
    assert_request_blocked(request, f"forbidden_read_mode:{mode}")


def test_dot_weslr_marker_blocked():
    request = valid_request(runtime_context_label=".weslr")
    assert_request_blocked(request, "dot_weslr_marker")


@pytest.mark.parametrize("marker", ["global_memory", "tl_default", "process_global", "default_timeline"])
def test_global_tl_default_process_global_default_timeline_marker_blocked(marker):
    request = valid_request(scope_inference=marker)
    assert_request_blocked(request, "marker")


def test_query_string_identity_blocked():
    request = valid_request(identity_source="query_string", query_string_user_id="user_synthetic")
    assert_request_blocked(request, "query_string_identity_marker")


def test_stale_untrusted_source_as_truth_blocked():
    assert_request_blocked(valid_request(currentness_label="stale"), "stale_or_unknown_source_requested_as_truth")
    assert_request_blocked(valid_request(provenance_label="inferred"), "untrusted_source_requested_as_truth")


@pytest.mark.parametrize("use_context", ["final_answer", "runtime_chat", "chat_runtime", "provider_call", "search_call"])
def test_final_answer_runtime_chat_provider_search_authority_marker_blocked(use_context):
    request = valid_request(requested_use_context=use_context)
    assert_request_blocked(request, "authority_marker")


def test_denied_authority_missing_true_blocked():
    missing = valid_request()
    missing["denied_authority"].pop("permits_provider_calls")
    assert_request_blocked(missing, "missing_denied_authority:permits_provider_calls")

    true_field = valid_request(denied_authority={"permits_final_answer_generation": True})
    assert_request_blocked(true_field, "denied_authority_true:permits_final_answer_generation")


def test_non_json_safe_metadata_blocked():
    request = valid_request()
    request["bad_set"] = {"not", "json"}
    result = validate_scoped_memory_context_read_request_v1(request)
    assert result["valid"] is False
    assert "non_json_safe_metadata" in result["blocked_reasons"]
    with pytest.raises(ValueError):
        to_scoped_memory_context_read_adapter_json_safe_v1(request)


def test_envelope_defaults_content_included_false():
    envelope = envelope_for()
    assert envelope["content_included"] is False
    assert envelope["redaction_status"] == "content_excluded_metadata_only"


def test_no_raw_memory_context_text_included():
    request = valid_request(raw_memory_text="secret synthetic raw text")
    result = validate_scoped_memory_context_read_request_v1(request)
    assert result["valid"] is False
    envelope = envelope_for()
    summary = summarize_scoped_memory_context_read_adapter_v1(envelope)
    markdown = render_scoped_memory_context_read_adapter_markdown_v1(envelope)
    assert "secret synthetic raw text" not in str(summary)
    assert "secret synthetic raw text" not in markdown
    assert "opaque_memory_ref_not_rendered" not in markdown


def test_json_safe_export():
    exported = to_scoped_memory_context_read_adapter_json_safe_v1(envelope_for())
    assert exported["schema_version"] == SCHEMA_VERSION
    assert exported["content_included"] is False


def test_internal_metadata_only_markdown_renderer():
    markdown = render_scoped_memory_context_read_adapter_markdown_v1(envelope_for())
    assert "# Scoped Memory Context Read Adapter Metadata V1" in markdown
    assert "metadata_only" in markdown
    assert "content_included`: `false" in markdown
    assert "permits_final_answer_generation" in markdown
    assert "opaque_memory_ref_not_rendered" not in markdown


def test_no_filesystem_network_provider_database_auth_runtime_dot_weslr_behavior(monkeypatch):
    def blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is forbidden")

    monkeypatch.setattr(builtins, "open", blocked_open)
    request = valid_request()
    envelope = build_scoped_memory_context_read_envelope_v1(request)
    assert envelope["content_included"] is False
    assert validate_scoped_memory_context_read_envelope_v1(envelope)["valid"] is True


def test_allowed_read_mode_set_is_exact():
    assert ALLOWED_READ_MODES == {
        "metadata_only_preview",
        "redacted_summary_candidate",
        "continuity_anchor_metadata",
        "evidence_summary_metadata",
        "blocked_no_read",
    }
    assert DEFAULT_DENIED_AUTHORITY["permits_context_reads_without_authorization"] is False
