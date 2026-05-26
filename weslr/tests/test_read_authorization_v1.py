import builtins
import importlib

import pytest

from weslr.read_authorization import (
    DENIED_AUTHORITY_FIELDS,
    authorize_scoped_read_v1,
    build_read_authorization_request_v1,
    render_read_authorization_markdown_v1,
    require_read_authorization_for_candidate_v1,
    summarize_read_authorization_v1,
    to_read_authorization_json_safe_v1,
    validate_read_authorization_request_v1,
)
from weslr.source_scope import build_source_scope_v1


def valid_source_scope(**overrides):
    data = dict(
        source_scope_id="scope_synthetic_read_001",
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
        authorization_id="read_auth_synthetic_001",
        source_scope=valid_source_scope(),
        requested_read_kind="memory",
        requested_use_context="candidate_metadata",
        requester_scope=requester_scope(),
        target_scope=target_scope(),
        public_browser_context=False,
        runtime_context_label="internal_metadata",
        privacy_label="user_private",
        retention_label="session",
        provenance_label="synthetic",
        currentness_label="current",
        policy_label="synthetic_metadata_only",
    )
    data.update(overrides)
    return build_read_authorization_request_v1(**data)


def decision_for(**overrides):
    return authorize_scoped_read_v1(valid_request(**overrides))


def test_import_safety():
    module = importlib.import_module("weslr.read_authorization")
    assert module.SCHEMA_VERSION == "weslr.read_authorization.v1"


def test_valid_metadata_only_authorization_request():
    request = valid_request()
    result = validate_read_authorization_request_v1(request)
    assert result["valid"] is True
    decision = authorize_scoped_read_v1(request)
    assert decision["decision"] == "allow_metadata_only"
    assert decision["denied_authority"] == {field: False for field in DENIED_AUTHORITY_FIELDS}


def test_valid_internal_shadow_allow_with_valid_source_scope():
    decision = decision_for(requested_use_context="shadow_validation", policy_label="internal_shadow")
    assert decision["decision"] == "allow_read_for_internal_shadow_use"
    assert "scoped_adapter_required" in decision["required_followup"]


def test_missing_source_scope_denied():
    decision = decision_for(source_scope=None)
    assert decision["decision"] == "deny_missing_source_scope"


def test_invalid_source_scope_denied():
    decision = decision_for(source_scope=valid_source_scope(tenant_id=None))
    assert decision["decision"] == "deny_invalid_source_scope"
    assert "missing_tenant_id" in decision["blocked_reason_labels"]


def test_missing_requester_scope_denied():
    decision = decision_for(requester_scope={})
    assert decision["decision"] == "deny_missing_requester_scope"


def test_missing_target_scope_denied():
    decision = decision_for(target_scope={})
    assert decision["decision"] == "deny_missing_target_scope"


def test_tenant_mismatch_denied():
    decision = decision_for(target_scope=target_scope(tenant_id="tenant_other"))
    assert decision["decision"] == "deny_cross_user_or_cross_tenant"
    assert "cross_tenant" in decision["blocked_reason_labels"]


def test_account_user_mismatch_denied():
    decision = decision_for(target_scope=target_scope(account_id="acct_other", user_id="user_other"))
    assert decision["decision"] == "deny_cross_user_or_cross_tenant"
    assert "cross_user" in decision["blocked_reason_labels"]


def test_session_conversation_mismatch_denied_where_required():
    session_decision = decision_for(target_scope=target_scope(session_id="sess_other"))
    assert session_decision["decision"] == "deny_scope_mismatch"
    assert "same_user_different_session" in session_decision["blocked_reason_labels"]
    conversation_decision = decision_for(target_scope=target_scope(conversation_id="conv_other"))
    assert conversation_decision["decision"] == "deny_scope_mismatch"
    assert "same_user_different_conversation" in conversation_decision["blocked_reason_labels"]


def test_guest_to_authenticated_read_denied():
    decision = decision_for(
        requester_scope=requester_scope(account_id=None, user_id=None, guest_id="guest_synthetic"),
        target_scope=target_scope(),
    )
    assert decision["decision"] == "deny_scope_mismatch"
    assert "guest_to_authenticated" in decision["blocked_reason_labels"]


def test_cross_user_memory_denied():
    decision = decision_for(requested_read_kind="memory", target_scope=target_scope(user_id="user_other"))
    assert decision["decision"] == "deny_cross_user_or_cross_tenant"


def test_cross_tenant_artifact_denied():
    artifact_scope = valid_source_scope(source_kind="artifact", artifact_id="artifact_synthetic", memory_scope_id=None)
    decision = decision_for(
        source_scope=artifact_scope,
        requested_read_kind="artifact",
        target_scope=target_scope(tenant_id="tenant_other"),
    )
    assert decision["decision"] == "deny_cross_user_or_cross_tenant"


def test_query_string_identity_denied():
    decision = decision_for(identity_source="query_string", query_string_user_id="user_synthetic")
    assert decision["decision"] == "deny_missing_policy"
    assert "query_string_user_id_not_identity_authority" in decision["blocked_reason_labels"]


def test_global_dot_weslr_denied():
    decision = decision_for(runtime_context_label=".weslr")
    assert decision["decision"] == "deny_missing_policy"
    assert "global_dot_weslr_invalid_for_authorization" in decision["blocked_reason_labels"]


def test_tl_default_denied():
    decision = decision_for(runtime_context_label="tl_default")
    assert decision["decision"] == "deny_missing_policy"
    assert "tl_default_invalid_shared_user_scope" in decision["blocked_reason_labels"]


def test_process_global_default_timeline_inference_denied():
    decision = decision_for(scope_inference="process_global")
    assert decision["decision"] == "deny_missing_policy"
    assert "process_global_or_default_timeline_inference_rejected" in decision["blocked_reason_labels"]


def test_private_operator_local_state_denied_in_public_browser_context():
    source = valid_source_scope(source_owner_kind="operator_local", privacy_label="operator_private")
    decision = decision_for(
        source_scope=source,
        public_browser_context=True,
        requested_use_context="candidate_metadata",
        privacy_label="operator_private",
    )
    assert decision["decision"] in {"deny_invalid_source_scope", "deny_public_browser_context"}


def test_raw_private_content_denied_for_anonymous_aggregate():
    source = valid_source_scope(
        source_owner_kind="anonymized_aggregate",
        privacy_label="raw_private",
        cross_user=False,
        contains_raw_private_material=False,
    )
    decision = decision_for(source_scope=source, privacy_label="raw_private")
    assert decision["decision"] == "deny_private_or_raw_content"


def test_unknown_policy_denied():
    decision = decision_for(policy_label="unknown")
    assert decision["decision"] == "deny_missing_policy"


@pytest.mark.parametrize(
    "use_context,expected",
    [
        ("final_answer", "deny_final_answer_or_user_output"),
        ("runtime_chat", "deny_runtime_authority"),
        ("provider_call", "deny_provider_or_external_call"),
    ],
)
def test_final_answer_runtime_provider_authority_denied(use_context, expected):
    decision = decision_for(requested_use_context=use_context)
    assert decision["decision"] == expected


def test_dot_weslr_authority_denied():
    decision = decision_for(denied_authority={"permits_dot_weslr_public_state": True})
    assert decision["decision"] == "deny_runtime_authority"
    assert "denied_authority_true:permits_dot_weslr_public_state" in decision["blocked_reason_labels"]


def test_missing_or_true_denied_authority_fields_denied():
    request = valid_request()
    request["denied_authority"].pop("permits_database_reads")
    missing = authorize_scoped_read_v1(request)
    assert missing["decision"] == "deny_runtime_authority"

    true_decision = decision_for(denied_authority={"permits_provider_calls": True})
    assert true_decision["decision"] == "deny_runtime_authority"
    assert "denied_authority_true:permits_provider_calls" in true_decision["blocked_reason_labels"]


def test_json_safe_export():
    decision = decision_for()
    exported = to_read_authorization_json_safe_v1(decision)
    assert exported["schema_version"] == "weslr.read_authorization.v1"
    assert exported["decision"] == "allow_metadata_only"
    with pytest.raises(ValueError):
        to_read_authorization_json_safe_v1({"bad_set": {"not", "json"}})


def test_safe_metadata_only_markdown_rendering():
    decision = decision_for()
    markdown = render_read_authorization_markdown_v1(decision)
    assert "# Read Authorization Metadata V1" in markdown
    assert "metadata_only" in markdown
    assert "grants_runtime_authority" in markdown
    assert "opaque_memory_ref_not_rendered" not in markdown


def test_candidate_requirement_rejects_missing_authorization():
    result = require_read_authorization_for_candidate_v1({"candidate_id": "candidate_synthetic"})
    assert result["valid"] is False
    assert "missing_read_authorization" in result["blocked_reasons"]


def test_candidate_requirement_rejects_denied_authorization():
    denied = decision_for(target_scope=target_scope(user_id="user_other"))
    result = require_read_authorization_for_candidate_v1(
        {"candidate_id": "candidate_synthetic", "read_authorization": denied}
    )
    assert result["valid"] is False
    assert "read_authorization_not_allowed" in result["blocked_reasons"]


def test_candidate_requirement_accepts_valid_metadata_only_authorization():
    allowed = decision_for()
    result = require_read_authorization_for_candidate_v1(
        {"candidate_id": "candidate_synthetic", "read_authorization": allowed}
    )
    assert result["valid"] is True
    assert result["authorization_summary"]["authorization_id"] == "read_auth_synthetic_001"


def test_summary_is_metadata_only():
    summary = summarize_read_authorization_v1(decision_for())
    assert summary["authorization_id"] == "read_auth_synthetic_001"
    assert "source_scope" not in summary


def test_no_filesystem_network_provider_database_runtime_dot_weslr_calls(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("filesystem access is not allowed")

    monkeypatch.setattr(builtins, "open", fail_open)
    request = valid_request()
    decision = authorize_scoped_read_v1(request)
    assert decision["decision"] == "allow_metadata_only"
    assert validate_read_authorization_request_v1(request)["valid"] is True
    assert require_read_authorization_for_candidate_v1({"read_authorization": decision})["valid"] is True
    assert "Read Authorization Metadata" in render_read_authorization_markdown_v1(decision)
