import builtins
import importlib

import pytest

from weslr.read_authorization import build_read_authorization_request_v1
from weslr.scoped_artifact_upload_registry import (
    ALLOWED_ACCESS_MODES,
    DEFAULT_DENIED_AUTHORITY,
    FORBIDDEN_ACCESS_MODES,
    SCHEMA_VERSION,
    authorize_scoped_artifact_upload_access_v1,
    build_scoped_artifact_upload_access_envelope_v1,
    build_scoped_artifact_upload_registry_entry_v1,
    render_scoped_artifact_upload_registry_markdown_v1,
    summarize_scoped_artifact_upload_registry_v1,
    to_scoped_artifact_upload_registry_json_safe_v1,
    validate_scoped_artifact_upload_access_envelope_v1,
    validate_scoped_artifact_upload_registry_entry_v1,
)
from weslr.source_scope import build_source_scope_v1


def valid_source_scope(**overrides):
    data = dict(
        source_scope_id="scope_registry_synthetic_001",
        tenant_id="tenant_synthetic",
        account_id="acct_synthetic",
        user_id="user_synthetic",
        session_id="sess_synthetic",
        conversation_id="conv_synthetic",
        workspace_id="workspace_synthetic",
        project_id="project_synthetic",
        artifact_id="artifact_synthetic",
        locale="en-US",
        language="en",
        source_kind="artifact",
        source_ref="opaque_artifact_ref_not_rendered",
        source_owner_kind="user",
        allowed_use_contexts=["candidate_metadata", "authority_checkpoint", "shadow_validation", "safe_assembly_shadow", "internal_review"],
        retention_label="session",
        privacy_label="user_private",
        currentness_label="current",
        provenance_label="synthetic",
    )
    data.update(overrides)
    return build_source_scope_v1(**data)


def same_scope(**overrides):
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


def valid_entry(**overrides):
    data = dict(
        registry_entry_id="registry_entry_synthetic_001",
        artifact_or_upload_kind="artifact",
        source_scope=valid_source_scope(),
        owner_scope=same_scope(),
        requester_scope=same_scope(),
        target_scope=same_scope(),
        requested_use_context="candidate_metadata",
        requested_content_mode="metadata_only_preview",
        access_mode="metadata_only_preview",
        privacy_label="user_private",
        retention_label="session",
        provenance_label="synthetic",
        currentness_label="current",
        policy_label="synthetic_metadata_only",
    )
    data.update(overrides)
    return build_scoped_artifact_upload_registry_entry_v1(**data)


def envelope_for(**overrides):
    return build_scoped_artifact_upload_access_envelope_v1(valid_entry(**overrides))


def assert_entry_blocked(entry, reason_fragment):
    result = validate_scoped_artifact_upload_registry_entry_v1(entry)
    assert result["valid"] is False
    assert any(reason_fragment in reason for reason in result["blocked_reasons"]), result["blocked_reasons"]
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["access_status"] == "blocked_no_access"
    return result


def test_import_safety():
    module = importlib.import_module("weslr.scoped_artifact_upload_registry")
    assert module.SCHEMA_VERSION == "weslr.scoped_artifact_upload_registry.v1"


def test_valid_metadata_only_preview_path():
    entry = valid_entry()
    validation = validate_scoped_artifact_upload_registry_entry_v1(entry)
    assert validation["valid"] is True
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["authorization_status"] == "allowed"
    assert decision["access_mode"] == "metadata_only_preview"
    assert decision["content_included"] is False
    envelope = build_scoped_artifact_upload_access_envelope_v1(entry, decision)
    assert validate_scoped_artifact_upload_access_envelope_v1(envelope)["valid"] is True


def test_valid_redacted_summary_candidate_path():
    entry = valid_entry(
        registry_entry_id="registry_entry_redacted_001",
        requested_use_context="shadow_validation",
        requested_content_mode="redacted_summary_candidate",
        access_mode="redacted_summary_candidate",
        policy_label="internal_shadow",
    )
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["authorization_status"] == "allowed"
    assert decision["central_authorization_decision"]["decision"] == "allow_read_for_internal_shadow_use"
    assert decision["content_included"] is False


def test_valid_provenance_summary_metadata_path():
    entry = valid_entry(
        registry_entry_id="registry_entry_provenance_001",
        artifact_or_upload_kind="provenance_summary",
        requested_content_mode="provenance_summary_metadata",
        access_mode="provenance_summary_metadata",
    )
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["authorization_status"] == "allowed"
    assert decision["access_mode"] == "provenance_summary_metadata"


def test_valid_continuity_anchor_metadata_path():
    entry = valid_entry(
        registry_entry_id="registry_entry_anchor_001",
        requested_content_mode="continuity_anchor_metadata",
        access_mode="continuity_anchor_metadata",
    )
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["authorization_status"] == "allowed"
    assert decision["access_mode"] == "continuity_anchor_metadata"


def test_blocked_no_access_path():
    entry = valid_entry(
        registry_entry_id="registry_entry_blocked_001",
        requested_content_mode="blocked_no_access",
        access_mode="blocked_no_access",
    )
    assert validate_scoped_artifact_upload_registry_entry_v1(entry)["valid"] is True
    decision = authorize_scoped_artifact_upload_access_v1(entry)
    assert decision["authorization_status"] == "blocked"
    assert decision["access_status"] == "blocked_no_access"
    envelope = build_scoped_artifact_upload_access_envelope_v1(entry, decision)
    assert envelope["access_mode"] == "blocked_no_access"
    assert envelope["content_included"] is False


def test_source_scope_validation_integration():
    validation = validate_scoped_artifact_upload_registry_entry_v1(valid_entry())
    assert validation["source_scope_summary"]["source_scope_id"] == "scope_registry_synthetic_001"


def test_read_authorization_integration():
    decision = authorize_scoped_artifact_upload_access_v1(valid_entry())
    assert decision["central_authorization_decision"]["decision"] == "allow_metadata_only"


def test_missing_invalid_source_scope_blocked():
    assert_entry_blocked(valid_entry(source_scope=None), "missing_source_scope")
    assert_entry_blocked(valid_entry(source_scope=valid_source_scope(tenant_id=None)), "source_scope:missing_tenant_id")


def test_missing_owner_requester_target_scope_blocked():
    assert_entry_blocked(valid_entry(owner_scope=None), "missing_owner_scope")
    assert_entry_blocked(valid_entry(requester_scope=None), "missing_requester_scope")
    assert_entry_blocked(valid_entry(target_scope=None), "missing_target_scope")


def test_missing_denied_authorization_blocked():
    missing = valid_entry()
    missing.pop("authorization_request")
    assert_entry_blocked(missing, "missing_read_authorization")

    denied_auth = build_read_authorization_request_v1(
        authorization_id="auth_denied_synthetic",
        source_scope=valid_source_scope(),
        requested_read_kind="artifact",
        requested_use_context="final_answer",
        requester_scope=same_scope(),
        target_scope=same_scope(),
        privacy_label="user_private",
        retention_label="session",
        provenance_label="synthetic",
        currentness_label="current",
        policy_label="synthetic_metadata_only",
    )
    decision = authorize_scoped_artifact_upload_access_v1(valid_entry(authorization_request=denied_auth))
    assert decision["authorization_status"] == "blocked"
    assert decision["access_status"] == "blocked_no_access"


def test_ownership_and_requester_target_mismatch_blocked():
    assert_entry_blocked(valid_entry(owner_scope=same_scope(user_id="owner_other")), "ownership_mismatch")
    assert_entry_blocked(valid_entry(target_scope=same_scope(session_id="sess_other")), "same_user_different_session")


def test_cross_user_cross_tenant_blocked():
    assert_entry_blocked(valid_entry(target_scope=same_scope(user_id="user_other")), "cross_user")
    assert_entry_blocked(valid_entry(target_scope=same_scope(tenant_id="tenant_other")), "cross_tenant")


def test_guest_anonymous_authenticated_mismatch_blocked():
    assert_entry_blocked(valid_entry(requester_scope=same_scope(account_id=None, user_id=None, guest_id="guest_synthetic")), "guest_to_authenticated")
    assert_entry_blocked(valid_entry(target_scope=same_scope(account_id=None, user_id=None, guest_id="guest_synthetic")), "authenticated_to_guest")


def test_public_browser_private_artifact_conflict_blocked():
    entry = valid_entry(public_browser_context=True, privacy_label="operator_private")
    assert_entry_blocked(entry, "public_browser")


def test_raw_artifact_upload_content_request_blocked():
    assert_entry_blocked(valid_entry(privacy_label="raw_private"), "raw_artifact_or_upload_content_requested")
    assert_entry_blocked(valid_entry(requested_content_mode="raw_upload_content"), "forbidden_access_mode:raw_upload_content")


@pytest.mark.parametrize("mode", sorted(FORBIDDEN_ACCESS_MODES))
def test_each_forbidden_access_mode_blocked(mode):
    entry = valid_entry(access_mode=mode, requested_content_mode=mode)
    assert_entry_blocked(entry, f"forbidden_access_mode:{mode}")


def test_dot_weslr_marker_blocked():
    assert_entry_blocked(valid_entry(runtime_context_label=".weslr"), "dot_weslr_marker")


@pytest.mark.parametrize("marker", ["global_artifact_registry", "tl_default", "process_global", "default_timeline"])
def test_global_tl_default_process_global_default_timeline_marker_blocked(marker):
    assert_entry_blocked(valid_entry(scope_inference=marker), "marker")


def test_query_string_identity_blocked():
    assert_entry_blocked(valid_entry(identity_source="query_string", query_string_user_id="user_synthetic"), "query_string_identity_marker")


def test_stale_untrusted_artifact_as_truth_blocked():
    assert_entry_blocked(valid_entry(currentness_label="stale"), "stale_or_unknown_source_requested_as_truth")
    assert_entry_blocked(valid_entry(provenance_label="inferred"), "untrusted_source_requested_as_truth")


@pytest.mark.parametrize("use_context", ["final_answer", "runtime_chat", "chat_runtime", "provider_call", "search_call"])
def test_final_answer_runtime_chat_provider_search_authority_marker_blocked(use_context):
    assert_entry_blocked(valid_entry(requested_use_context=use_context), "authority_marker")


def test_denied_authority_missing_true_blocked():
    missing = valid_entry()
    missing["denied_authority"].pop("permits_provider_calls")
    assert_entry_blocked(missing, "missing_denied_authority:permits_provider_calls")

    true_field = valid_entry(denied_authority={"permits_final_answer_generation": True})
    assert_entry_blocked(true_field, "denied_authority_true:permits_final_answer_generation")


def test_non_json_safe_metadata_blocked():
    entry = valid_entry()
    entry["bad_set"] = {"not", "json"}
    result = validate_scoped_artifact_upload_registry_entry_v1(entry)
    assert result["valid"] is False
    assert "non_json_safe_metadata" in result["blocked_reasons"]
    with pytest.raises(ValueError):
        to_scoped_artifact_upload_registry_json_safe_v1(entry)


def test_access_envelope_defaults_content_included_false():
    envelope = envelope_for()
    assert envelope["content_included"] is False
    assert envelope["redaction_status"] == "content_excluded_metadata_only"


def test_no_raw_artifact_upload_content_included():
    entry = valid_entry(raw_artifact_content="secret synthetic raw text")
    result = validate_scoped_artifact_upload_registry_entry_v1(entry)
    assert result["valid"] is False
    envelope = envelope_for()
    summary = summarize_scoped_artifact_upload_registry_v1(envelope)
    markdown = render_scoped_artifact_upload_registry_markdown_v1(envelope)
    assert "secret synthetic raw text" not in str(summary)
    assert "secret synthetic raw text" not in markdown
    assert "opaque_artifact_ref_not_rendered" not in markdown


def test_json_safe_export():
    exported = to_scoped_artifact_upload_registry_json_safe_v1(envelope_for())
    assert exported["schema_version"] == SCHEMA_VERSION
    assert exported["content_included"] is False


def test_internal_metadata_only_markdown_renderer():
    markdown = render_scoped_artifact_upload_registry_markdown_v1(envelope_for())
    assert "# Scoped Artifact Upload Registry Metadata V1" in markdown
    assert "metadata_only" in markdown
    assert "content_included`: `false" in markdown
    assert "permits_final_answer_generation" in markdown
    assert "opaque_artifact_ref_not_rendered" not in markdown


def test_no_filesystem_network_provider_database_auth_runtime_dot_weslr_behavior(monkeypatch):
    def blocked_open(*args, **kwargs):
        raise AssertionError("filesystem access is forbidden")

    monkeypatch.setattr(builtins, "open", blocked_open)
    envelope = build_scoped_artifact_upload_access_envelope_v1(valid_entry())
    assert envelope["content_included"] is False
    assert validate_scoped_artifact_upload_access_envelope_v1(envelope)["valid"] is True


def test_allowed_access_mode_set_and_denied_authority_are_exact():
    assert ALLOWED_ACCESS_MODES == {
        "metadata_only_preview",
        "redacted_summary_candidate",
        "provenance_summary_metadata",
        "continuity_anchor_metadata",
        "blocked_no_access",
    }
    assert DEFAULT_DENIED_AUTHORITY == {
        "grants_runtime_authority": False,
        "permits_public_browser_runtime": False,
        "permits_provider_calls": False,
        "permits_dot_weslr_public_state": False,
        "permits_final_answer_generation": False,
        "permits_unscoped_artifact_reads": False,
        "permits_cross_user_artifact_access": False,
        "permits_raw_artifact_content": False,
        "permits_raw_upload_content": False,
        "permits_database_reads": False,
        "permits_authentication_decisions": False,
        "permits_upload_ingestion": False,
        "permits_filesystem_scanning": False,
    }
