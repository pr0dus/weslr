import builtins
import importlib

import pytest

from weslr.cache_log_trace_scope import (
    ALLOWED_ACCESS_MODES,
    DEFAULT_DENIED_AUTHORITY,
    DENIED_AUTHORITY_FIELDS,
    FORBIDDEN_ACCESS_MODES,
    SURFACE_KINDS,
    authorize_cache_log_trace_access_v1,
    build_cache_log_trace_access_envelope_v1,
    build_cache_log_trace_scope_record_v1,
    render_cache_log_trace_scope_markdown_v1,
    to_cache_log_trace_scope_json_safe_v1,
    validate_cache_log_trace_access_envelope_v1,
    validate_cache_log_trace_scope_record_v1,
)
from weslr.read_authorization import authorize_scoped_read_v1, build_read_authorization_request_v1
from weslr.source_scope import build_source_scope_v1


def valid_scope_metadata(**overrides):
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


def valid_source_scope(**overrides):
    data = dict(
        source_scope_id="scope_cache_log_trace_synthetic_001",
        tenant_id="tenant_synthetic",
        account_id="acct_synthetic",
        user_id="user_synthetic",
        session_id="sess_synthetic",
        conversation_id="conv_synthetic",
        workspace_id="workspace_synthetic",
        project_id="project_synthetic",
        cache_scope_id="cache_scope_synthetic",
        locale="en-US",
        language="en",
        source_kind="cache",
        source_ref="opaque_cache_ref_not_rendered",
        source_owner_kind="user",
        allowed_use_contexts=["candidate_metadata", "authority_checkpoint", "shadow_validation"],
        retention_label="session",
        privacy_label="synthetic",
        currentness_label="current",
        provenance_label="synthetic",
    )
    data.update(overrides)
    return build_source_scope_v1(**data)


def valid_read_authorization(**overrides):
    source = overrides.pop("source_scope", valid_source_scope())
    request = build_read_authorization_request_v1(
        authorization_id="read_auth_cache_log_trace_synthetic_001",
        source_scope=source,
        requested_read_kind=overrides.pop("requested_read_kind", "cache"),
        requested_use_context=overrides.pop("requested_use_context", "candidate_metadata"),
        requester_scope=overrides.pop("requester_scope", valid_scope_metadata()),
        target_scope=overrides.pop("target_scope", valid_scope_metadata()),
        public_browser_context=overrides.pop("public_browser_context", False),
        runtime_context_label=overrides.pop("runtime_context_label", "internal_metadata"),
        privacy_label=overrides.pop("privacy_label", "synthetic"),
        retention_label=overrides.pop("retention_label", "session"),
        provenance_label=overrides.pop("provenance_label", "synthetic"),
        currentness_label=overrides.pop("currentness_label", "current"),
        policy_label=overrides.pop("policy_label", "synthetic_metadata_only"),
        **overrides,
    )
    return authorize_scoped_read_v1(request)


def valid_record(**overrides):
    source = overrides.pop("source_scope", valid_source_scope())
    requester = overrides.pop("requester_scope", valid_scope_metadata())
    target = overrides.pop("target_scope", valid_scope_metadata())
    owner = overrides.pop("owner_scope", valid_scope_metadata())
    read_auth = overrides.pop(
        "read_authorization",
        valid_read_authorization(source_scope=source, requester_scope=requester, target_scope=target),
    )
    data = dict(
        record_id="cache_log_trace_scope_synthetic_001",
        surface_kind="cache_entry",
        source_scope=source,
        owner_scope=owner,
        requester_scope=requester,
        target_scope=target,
        access_mode="metadata_only_preview",
        read_authorization=read_auth,
        retention_label="session",
        privacy_label="synthetic",
        provenance_label="synthetic",
        currentness_label="current",
        redaction_status="redacted_metadata_only",
        policy_label="synthetic_metadata_only",
        authorized_use_contexts=["candidate_metadata"],
    )
    data.update(overrides)
    return build_cache_log_trace_scope_record_v1(**data)


def assert_blocked(record, reason_fragment):
    result = validate_cache_log_trace_scope_record_v1(record)
    assert result["valid"] is False
    assert any(reason_fragment in reason for reason in result["blocked_reasons"])
    assert result["access_mode"] == "blocked_no_access"
    return result


def test_import_safety():
    module = importlib.import_module("weslr.cache_log_trace_scope")
    assert module.SCHEMA_VERSION == "weslr.cache_log_trace_scope.v1"


@pytest.mark.parametrize(
    "access_mode",
    [
        "metadata_only_preview",
        "redacted_diagnostic_summary",
        "aggregate_count_summary",
        "provenance_summary_metadata",
    ],
)
def test_valid_allowed_access_modes(access_mode):
    record = valid_record(access_mode=access_mode)
    validation = validate_cache_log_trace_scope_record_v1(record)
    assert validation["valid"] is True
    assert validation["access_mode"] == access_mode
    decision = authorize_cache_log_trace_access_v1(record)
    assert decision["decision"] == "allow_metadata_only"


def test_blocked_no_access_path_is_metadata_only():
    record = valid_record(access_mode="blocked_no_access", read_authorization=None)
    validation = validate_cache_log_trace_scope_record_v1(record)
    assert validation["valid"] is True
    assert validation["validation_status"] == "blocked_no_access"
    decision = authorize_cache_log_trace_access_v1(record)
    assert decision["decision"] == "blocked_no_access"


@pytest.mark.parametrize("surface_kind", sorted(SURFACE_KINDS))
def test_all_surface_kinds_accepted_as_metadata(surface_kind):
    record = valid_record(surface_kind=surface_kind)
    assert validate_cache_log_trace_scope_record_v1(record)["valid"] is True


def test_source_scope_validation_integration_blocks_invalid_source_scope():
    record = valid_record(source_scope=valid_source_scope(tenant_id=None))
    assert_blocked(record, "source_scope:missing_tenant_id")


def test_read_authorization_integration_blocks_denied_policy():
    record = valid_record(policy_label="unknown")
    decision = authorize_cache_log_trace_access_v1(record)
    assert decision["decision"] == "blocked_no_access"
    assert "missing_or_unknown_policy_label" in decision["blocked_reasons"]


def test_missing_source_scope_blocked():
    assert_blocked(valid_record(source_scope=None), "missing_source_scope")


@pytest.mark.parametrize("scope_name", ["owner_scope", "requester_scope", "target_scope"])
def test_missing_owner_requester_target_scope_blocked(scope_name):
    assert_blocked(valid_record(**{scope_name: {}}), f"missing_{scope_name}")


def test_missing_authorization_blocked_for_non_blocked_access():
    assert_blocked(valid_record(read_authorization=None), "missing_read_authorization")


def test_denied_authorization_blocked():
    denied = valid_read_authorization(policy_label="unknown")
    assert denied["decision"] != "allow_metadata_only"
    assert_blocked(valid_record(read_authorization=denied), "read_authorization_denied")


@pytest.mark.parametrize(
    "target_overrides,reason",
    [
        ({"tenant_id": "tenant_other"}, "cross_tenant"),
        ({"account_id": "acct_other", "user_id": "user_other"}, "cross_user"),
        ({"session_id": "sess_other"}, "same_user_different_session"),
    ],
)
def test_cross_user_cross_tenant_session_risk_blocked(target_overrides, reason):
    assert_blocked(valid_record(target_scope=valid_scope_metadata(**target_overrides)), reason)


def test_public_browser_private_trace_conflict_blocked():
    source = valid_source_scope(source_owner_kind="operator_local", privacy_label="operator_private")
    record = valid_record(
        surface_kind="trace",
        source_scope=source,
        public_browser_context=True,
        privacy_label="operator_private",
    )
    assert_blocked(record, "public_browser_context")


@pytest.mark.parametrize(
    "field",
    ["raw_log_text", "raw_trace_payload", "raw_cache_value", "runtime_transcript_dump"],
)
def test_raw_log_trace_cache_or_transcript_request_blocked(field):
    record = valid_record(**{field: "synthetic raw payload forbidden"})
    assert_blocked(record, f"raw_content_field_present:{field}")


@pytest.mark.parametrize("access_mode", sorted(FORBIDDEN_ACCESS_MODES))
def test_each_forbidden_access_mode_blocked(access_mode):
    assert_blocked(valid_record(access_mode=access_mode), f"forbidden_access_mode:{access_mode}")


def test_dot_weslr_marker_blocked():
    assert_blocked(valid_record(runtime_context_label=".weslr"), "global_dot_weslr")


@pytest.mark.parametrize("marker", ["global", "tl_default", "process_global", "default_timeline"])
def test_global_tl_default_process_global_default_timeline_marker_blocked(marker):
    record = valid_record(runtime_context_label=marker)
    result = validate_cache_log_trace_scope_record_v1(record)
    assert result["valid"] is False


def test_query_string_identity_blocked():
    assert_blocked(valid_record(identity_source="query_string", query_string_user_id="user_synthetic"), "query_string_identity")


def test_truth_authority_misuse_blocked():
    assert_blocked(valid_record(requested_as_truth=True), "cache_log_trace_not_truth_authority")


def test_stale_untrusted_diagnostic_as_truth_blocked():
    assert_blocked(
        valid_record(requested_as_truth=True, currentness_label="stale", provenance_label="untrusted"),
        "stale_or_untrusted_diagnostic_requested_as_truth",
    )


@pytest.mark.parametrize("marker", ["final_answer", "runtime_chat", "provider_call", "search_call"])
def test_final_answer_runtime_chat_provider_search_authority_marker_blocked(marker):
    assert_blocked(valid_record(requested_use_context=marker), "final_runtime_provider_search_authority_rejected")


def test_denied_authority_missing_or_true_blocked():
    missing = valid_record()
    missing["denied_authority"].pop("permits_raw_log_text")
    assert_blocked(missing, "missing_denied_authority:permits_raw_log_text")

    true_record = valid_record(denied_authority={"permits_provider_calls": True})
    assert_blocked(true_record, "denied_authority_true:permits_provider_calls")


def test_non_json_safe_metadata_blocked_and_export_raises():
    record = valid_record()
    record["bad_set"] = {"not", "json"}
    result = validate_cache_log_trace_scope_record_v1(record)
    assert result["valid"] is False
    assert "non_json_safe_metadata" in result["blocked_reasons"]
    with pytest.raises(ValueError):
        to_cache_log_trace_scope_json_safe_v1(record)


def test_envelope_defaults_content_flags_false():
    envelope = build_cache_log_trace_access_envelope_v1(valid_record())
    assert envelope["content_included"] is False
    assert envelope["raw_trace_included"] is False
    assert envelope["raw_log_included"] is False
    assert envelope["raw_cache_value_included"] is False
    assert envelope["raw_transcript_included"] is False
    assert validate_cache_log_trace_access_envelope_v1(envelope)["valid"] is True


def test_no_raw_log_trace_cache_transcript_content_included():
    envelope = build_cache_log_trace_access_envelope_v1(valid_record())
    rendered = repr(envelope)
    assert "synthetic raw payload forbidden" not in rendered
    assert "raw_log_text" not in envelope
    assert "raw_trace_payload" not in envelope
    assert "raw_cache_value" not in envelope
    assert "runtime_transcript_dump" not in envelope


def test_json_safe_export():
    exported = to_cache_log_trace_scope_json_safe_v1(valid_record())
    assert exported["schema_version"] == "weslr.cache_log_trace_scope.v1"
    assert exported["denied_authority"] == DEFAULT_DENIED_AUTHORITY


def test_internal_metadata_only_markdown_renderer():
    markdown = render_cache_log_trace_scope_markdown_v1(validate_cache_log_trace_scope_record_v1(valid_record()))
    assert "# Cache Log Trace Scope Metadata V1" in markdown
    assert "metadata_only" in markdown
    assert "raw_log_included`: `false" in markdown
    assert "opaque_cache_ref_not_rendered" not in markdown


def test_no_filesystem_network_provider_database_auth_runtime_dot_weslr_behavior(monkeypatch):
    def fail_open(*args, **kwargs):
        raise AssertionError("filesystem reads are forbidden")

    monkeypatch.setattr(builtins, "open", fail_open)
    record = valid_record()
    validation = validate_cache_log_trace_scope_record_v1(record)
    envelope = build_cache_log_trace_access_envelope_v1(record)
    assert validation["valid"] is True
    assert envelope["access_decision"]["decision"] == "allow_metadata_only"
    rendered = repr(envelope).lower()
    assert ".weslr" not in rendered


def test_allowed_and_forbidden_mode_sets_are_disjoint():
    assert ALLOWED_ACCESS_MODES.isdisjoint(FORBIDDEN_ACCESS_MODES)
    assert "blocked_no_access" in ALLOWED_ACCESS_MODES
    assert set(DENIED_AUTHORITY_FIELDS) == set(DEFAULT_DENIED_AUTHORITY)
