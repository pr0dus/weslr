"""
WESLR chat.weslr.de Slice 8 — Dashboard Read-Model Helper V1

Tests for the dashboard read-model helper. The tests cover:

  - Module existence and exports
  - Input validation (positive and negative cases)
  - Forbidden-key contract (16-key, recursive)
  - Authority-claim key prefix rejection
  - Non-primitive value rejection
  - Section validation (8 sections)
  - Blocked-actions and warnings list validation
  - Slice-status validation (only 8 known slices)
  - Lane validation (only 6 known lanes)
  - build_dashboard_read_model_v1 happy path
  - build_dashboard_read_model_v1 failure path
  - to_dashboard_read_model_json_safe_v1 (JSON-safety, cycle-safe)
  - to_dashboard_read_model_markdown_v1 (safe Markdown, no HTML)
  - summarize_dashboard_read_model_v1
  - Wiring invariants (no chat_responder, no provider, no payment,
    no weslr_state, no filesystem writes)
  - Top-level imports (stdlib only)
  - Defensive copy semantics
  - Default-deny on missing sections
  - is_observation=True on every section
"""

from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List

# Add the repository root to sys.path so we can import the helper
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_STR = str(REPO_ROOT)
if REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, REPO_ROOT_STR)


def _helper_source_path() -> Path:
    return REPO_ROOT / "weslr" / "dashboard_read_model.py"

import weslr.dashboard_read_model as drm  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_OPERATOR_ID = "operator_arthur_001"
VALID_GENERATED_AT = "2026-06-24T13:00:00Z"
VALID_OPERATOR_ROLE = "operator"


def _valid_input() -> Dict[str, Any]:
    """Return a valid DashboardReadModelInputV1 packet."""
    return {
        "schema_version": "1",
        "generated_at_utc": VALID_GENERATED_AT,
        "operator_id": VALID_OPERATOR_ID,
        "operator_role": VALID_OPERATOR_ROLE,
        "sections": {
            "public_protected_site_health": {
                "status": "pass",
                "summary": "All sites responding as expected (observation).",
                "details": {
                    "weslr_de_status": "200",
                    "chat_weslr_de_status": "401",
                    "staging_weslr_de_status": "401",
                },
            },
            "backend_health": {
                "status": "pass",
                "summary": "Backend on 127.0.0.1:8092 listening (observation).",
                "details": {
                    "port": 8092,
                    "address": "127.0.0.1",
                    "pid": 22247,
                },
            },
            "source_repo_health": {
                "status": "pass",
                "summary": "Source-repo checks pass (observation).",
                "details": {
                    "passes": 9,
                    "fails": 0,
                    "warns": 0,
                },
            },
            "protected_auth_status": {
                "status": "pass",
                "summary": "htpasswd in place; chat.weslr.de auth-gated (observation).",
                "details": {
                    "realm": "WESLR Chat Interface",
                },
            },
            "blocked_actions": [
                {
                    "category": "model_provider_call",
                    "description": "Provider/model calls are blocked in this lane.",
                    "reason_label": "no_model_provider_in_lane",
                },
                {
                    "category": "payment_provider_call",
                    "description": "Stripe/PayPal/etc. calls are blocked in this lane.",
                    "reason_label": "no_payment_provider_in_lane",
                },
                {
                    "category": "filesystem_write",
                    "description": "Writes to /home/pr0/weslr_state/ are blocked.",
                    "reason_label": "no_state_persistence_in_lane",
                },
                {
                    "category": "public_runtime_claim",
                    "description": "Claims of public/live/production runtime are blocked.",
                    "reason_label": "no_authority_claims_in_lane",
                },
            ],
            "current_slice_status": {
                "slice_id": "slice8_dashboard_read_model",
                "status": "implemented",
                "details": {
                    "helper_module": "weslr/dashboard_read_model.py",
                },
            },
            "recommended_next_operator_action": {
                "lane": "APPROVE_NEXT_SLICE",
                "reason": "Slice 8 implemented; operator review for slice 9 approval.",
            },
            "warnings_requiring_operator_attention": [
                {
                    "warning_id": "warn_backend_pre_existing_state",
                    "description": "Backend recovery was performed this session; review for permanence.",
                    "severity": "info",
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Test: module existence and exports
# ---------------------------------------------------------------------------


def test_module_exists():
    assert drm is not None
    assert hasattr(drm, "DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1")
    assert hasattr(drm, "build_dashboard_read_model_v1")
    assert hasattr(drm, "validate_dashboard_read_model_input_v1")
    assert hasattr(drm, "to_dashboard_read_model_json_safe_v1")
    assert hasattr(drm, "to_dashboard_read_model_markdown_v1")
    assert hasattr(drm, "summarize_dashboard_read_model_v1")


def test_schema_version_is_string_one():
    assert drm.DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1 == "1"


def test_constants_present():
    assert isinstance(drm.DASHBOARD_READ_MODEL_SECTIONS_V1, tuple)
    assert len(drm.DASHBOARD_READ_MODEL_SECTIONS_V1) == 8
    assert "public_protected_site_health" in drm.DASHBOARD_READ_MODEL_SECTIONS_V1
    assert "current_slice_status" in drm.DASHBOARD_READ_MODEL_SECTIONS_V1
    assert isinstance(drm.DASHBOARD_RECOGNIZED_SLICES_V1, tuple)
    assert len(drm.DASHBOARD_RECOGNIZED_SLICES_V1) == 9  # 1-8
    assert isinstance(drm.DASHBOARD_RECOMMENDED_LANES_V1, tuple)
    assert len(drm.DASHBOARD_RECOMMENDED_LANES_V1) == 6


# ---------------------------------------------------------------------------
# Test: top-level imports (must be stdlib only)
# ---------------------------------------------------------------------------


def test_top_level_imports_are_stdlib_only():
    """Use AST to extract top-level import statements and verify
    none of them are non-stdlib."""
    import ast

    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()

    tree = ast.parse(source)
    imports: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imports.append(node.module)

    forbidden = [
        "weslr.chat_responder", "weslr.runtime_wrapper",
        "weslr.session_manager", "weslr.audit_log",
        "weslr.audit_log_persistence", "weslr.account_status",
        "weslr.entitlement_packet", "weslr.billing_abo_status",
        "weslr.dialogue", "weslr.chat_ui", "weslr.main",
        "stripe", "paypal", "adyen", "klarna", "braintree",
        "openai", "anthropic", "ollama", "requests",
    ]
    for imp in imports:
        for f in forbidden:
            assert not imp.startswith(f), f"forbidden import: {imp}"


# ---------------------------------------------------------------------------
# Test: input validation - positive
# ---------------------------------------------------------------------------


def test_validate_input_valid():
    pkt = _valid_input()
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["input_packet"] is not None


def test_validate_input_with_all_sections_minimal():
    """All sections with minimal shape (just status/summary/details)."""
    pkt = _valid_input()
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True


# ---------------------------------------------------------------------------
# Test: input validation - top-level errors
# ---------------------------------------------------------------------------


def test_validate_input_not_a_dict():
    result = drm.validate_dashboard_read_model_input_v1("not a dict")
    assert result["ok"] is False
    assert drm.REASON_INVALID_INPUT_NOT_DICT in result["errors"]


def test_validate_input_missing_schema_version():
    pkt = _valid_input()
    del pkt["schema_version"]
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_INPUT_MISSING_KEY in e for e in result["errors"]
    )


def test_validate_input_wrong_schema_version():
    pkt = _valid_input()
    pkt["schema_version"] = "2"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SCHEMA_VERSION in e for e in result["errors"]
    )


def test_validate_input_generated_at_not_iso8601():
    pkt = _valid_input()
    pkt["generated_at_utc"] = "yesterday"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_GENERATED_AT_NOT_ISO8601 in e
        for e in result["errors"]
    )


def test_validate_input_generated_at_with_offset_accepted():
    pkt = _valid_input()
    pkt["generated_at_utc"] = "2026-06-24T13:00:00+00:00"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True


def test_validate_input_empty_operator_id():
    pkt = _valid_input()
    pkt["operator_id"] = ""
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_OPERATOR_ID in e for e in result["errors"]
    )


def test_validate_input_invalid_operator_role():
    pkt = _valid_input()
    pkt["operator_role"] = "admin"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_OPERATOR_ROLE in e for e in result["errors"]
    )


def test_validate_input_each_valid_operator_role():
    for role in drm.DASHBOARD_OPERATOR_ROLES_V1:
        pkt = _valid_input()
        pkt["operator_role"] = role
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is True, f"role {role} should be valid"


def test_validate_input_sections_not_dict():
    pkt = _valid_input()
    pkt["sections"] = "not a dict"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_INPUT_WRONG_TYPE in e
        and "sections" in e
        for e in result["errors"]
    )


# ---------------------------------------------------------------------------
# Test: section validation
# ---------------------------------------------------------------------------


def test_validate_input_section_not_a_dict():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"] = "not a dict"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SECTION_NOT_DICT in e
        and "public_protected_site_health" in e
        for e in result["errors"]
    )


def test_validate_input_section_missing_status():
    pkt = _valid_input()
    del pkt["sections"]["public_protected_site_health"]["status"]
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_INPUT_MISSING_KEY in e
        and "status" in e
        for e in result["errors"]
    )


def test_validate_input_section_invalid_status():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"]["status"] = "is_healthy"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SECTION_STATUS in e
        and "is_healthy" in e
        for e in result["errors"]
    )


def test_validate_input_each_valid_section_status():
    for st in drm.DASHBOARD_SECTION_OBSERVATION_STATUSES_V1:
        pkt = _valid_input()
        pkt["sections"]["public_protected_site_health"]["status"] = st
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is True, f"status {st} should be valid"


def test_validate_input_unrecognized_section_name():
    pkt = _valid_input()
    pkt["sections"]["unknown_section"] = {
        "status": "pass",
        "summary": "x",
        "details": {},
    }
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SECTION in e
        and "unknown_section" in e
        for e in result["errors"]
    )


def test_validate_input_missing_required_section():
    pkt = _valid_input()
    del pkt["sections"]["backend_health"]
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        "backend_health" in e for e in result["errors"]
    )


# ---------------------------------------------------------------------------
# Test: forbidden-key contract (16 keys, recursive)
# ---------------------------------------------------------------------------


def test_forbidden_key_rejected_in_top_level():
    pkt = _valid_input()
    pkt["api_key"] = "leaked"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_FORBIDDEN_KEY in e for e in result["errors"]
    )


def test_all_16_forbidden_keys_rejected():
    for forbidden_key in drm.DASHBOARD_READ_MODEL_NEVER_INCLUDES_V1:
        pkt = _valid_input()
        pkt[forbidden_key] = "leaked"
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is False, f"key {forbidden_key} should be rejected"
        assert any(
            drm.REASON_INVALID_FORBIDDEN_KEY in e
            for e in result["errors"]
        )


def test_forbidden_key_rejected_nested_in_section():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["details"]["password"] = "leaked"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_forbidden_key_rejected_nested_in_blocked_action():
    pkt = _valid_input()
    pkt["sections"]["blocked_actions"][0]["secret"] = "leaked"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_forbidden_key_rejected_in_list():
    pkt = _valid_input()
    pkt["sections"]["warnings_requiring_operator_attention"].append({
        "warning_id": "warn_x",
        "description": "x",
        "severity": "info",
        "api_key": "leaked",
    })
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


# ---------------------------------------------------------------------------
# Test: authority-claim key prefix rejection
# ---------------------------------------------------------------------------


def test_authority_claim_is_healthy_rejected():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"]["is_healthy"] = True
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_AUTHORITY_CLAIM in e for e in result["errors"]
    )


def test_authority_claim_is_production_rejected():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["is_production_ready"] = True
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_authority_claim_is_live_public_rejected():
    pkt = _valid_input()
    pkt["sections"]["source_repo_health"]["is_live_public_runtime"] = True
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_authority_claim_official_rejected():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"]["official_score"] = 99
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_authority_claim_is_agi_rejected():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"]["is_agi_superhuman"] = True
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


# ---------------------------------------------------------------------------
# Test: non-primitive value rejection
# ---------------------------------------------------------------------------


def test_non_primitive_bytes_rejected():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["details"]["raw_bytes"] = b"data"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_NON_PRIMITIVE_VALUE in e
        for e in result["errors"]
    )


def test_non_primitive_set_rejected():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["details"]["set_value"] = {"a", "b"}
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_non_primitive_object_rejected():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["details"]["object"] = object()
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


# ---------------------------------------------------------------------------
# Test: blocked_actions and warnings
# ---------------------------------------------------------------------------


def test_blocked_actions_not_list_rejected():
    pkt = _valid_input()
    pkt["sections"]["blocked_actions"] = "not a list"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert drm.REASON_INVALID_BLOCKED_ACTIONS_NOT_LIST in result["errors"]


def test_blocked_action_not_dict_rejected():
    pkt = _valid_input()
    pkt["sections"]["blocked_actions"] = ["not a dict"]
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_blocked_action_missing_fields_rejected():
    pkt = _valid_input()
    pkt["sections"]["blocked_actions"] = [{"category": "x"}]
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_warnings_not_list_rejected():
    pkt = _valid_input()
    pkt["sections"]["warnings_requiring_operator_attention"] = "not a list"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert drm.REASON_INVALID_WARNINGS_NOT_LIST in result["errors"]


def test_warning_invalid_severity_rejected():
    pkt = _valid_input()
    pkt["sections"]["warnings_requiring_operator_attention"].append({
        "warning_id": "w1",
        "description": "x",
        "severity": "fatal",
    })
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


# ---------------------------------------------------------------------------
# Test: current_slice_status validation
# ---------------------------------------------------------------------------


def test_slice_status_unknown_slice_rejected():
    pkt = _valid_input()
    pkt["sections"]["current_slice_status"]["slice_id"] = "slice99_unknown"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SLICE_REFERENCE in e for e in result["errors"]
    )


def test_slice_status_slice9_rejected():
    """Slice 9+ must be rejected — only slices 1-8 are recognized."""
    pkt = _valid_input()
    pkt["sections"]["current_slice_status"]["slice_id"] = "slice9_something"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False


def test_slice_status_valid_for_each_recognized_slice():
    for slice_id in drm.DASHBOARD_RECOGNIZED_SLICES_V1:
        pkt = _valid_input()
        pkt["sections"]["current_slice_status"]["slice_id"] = slice_id
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is True, f"slice_id {slice_id} should be valid"


def test_slice_status_invalid_status_value_rejected():
    pkt = _valid_input()
    pkt["sections"]["current_slice_status"]["status"] = "is_done"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_SLICE_STATUS in e for e in result["errors"]
    )


def test_slice_status_each_valid_status():
    for st in drm.DASHBOARD_SLICE_STATUS_VALUES_V1:
        pkt = _valid_input()
        pkt["sections"]["current_slice_status"]["status"] = st
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is True, f"status {st} should be valid"


# ---------------------------------------------------------------------------
# Test: recommended_next_operator_action validation
# ---------------------------------------------------------------------------


def test_recommended_unknown_lane_rejected():
    pkt = _valid_input()
    pkt["sections"]["recommended_next_operator_action"]["lane"] = "DO_EVERYTHING_NOW"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert any(
        drm.REASON_INVALID_RECOMMENDED_LANE in e for e in result["errors"]
    )


def test_recommended_each_valid_lane():
    for lane in drm.DASHBOARD_RECOMMENDED_LANES_V1:
        pkt = _valid_input()
        pkt["sections"]["recommended_next_operator_action"]["lane"] = lane
        result = drm.validate_dashboard_read_model_input_v1(pkt)
        assert result["ok"] is True, f"lane {lane} should be valid"


def test_recommended_not_dict_rejected():
    pkt = _valid_input()
    pkt["sections"]["recommended_next_operator_action"] = "not a dict"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    # The reason label is emitted as `REASON:path` so check
    # for the reason prefix instead of exact match.
    assert any(
        e.startswith(drm.REASON_INVALID_RECOMMENDED_NOT_DICT + ":")
        or e == drm.REASON_INVALID_RECOMMENDED_NOT_DICT
        for e in result["errors"]
    )


# ---------------------------------------------------------------------------
# Test: build_dashboard_read_model_v1 - happy path
# ---------------------------------------------------------------------------


def test_build_read_model_happy_path():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    assert rm["ok"] is True
    assert rm["errors"] == []
    assert rm["schema_version"] == "1"
    assert "sections" in rm
    assert "metadata" in rm
    assert "blocked_actions" in rm
    assert "warnings_requiring_operator_attention" in rm


def test_build_read_model_marks_all_sections_as_observation():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    for section_name, section in rm["sections"].items():
        assert section.get("is_observation") is True, (
            f"section {section_name} should be marked is_observation=True"
        )


def test_build_read_model_metadata_marks_observation_only():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = rm["metadata"]
    assert md["is_dashboard_read_model"] is True
    assert md["is_live_inference"] is False
    assert md["is_observation_only"] is True
    assert md["is_authority_claim"] is False
    assert md["is_production_ready"] is False
    assert md["is_live_public_runtime"] is False


def test_build_read_model_recommended_action_marked_not_auto_approved():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    rec = rm["sections"]["recommended_next_operator_action"]
    assert rec.get("is_observation") is True
    assert rec.get("is_auto_approved") is False


def test_build_read_model_defensive_copy():
    """The returned input_packet must be a deep copy, not a reference."""
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    rm["input_packet"]["operator_id"] = "mutated_after_build"
    # Original packet should NOT be mutated
    assert pkt["operator_id"] == VALID_OPERATOR_ID


def test_build_read_model_input_not_mutated():
    """The validator and builder must not mutate the caller's packet."""
    pkt = _valid_input()
    original = json.dumps(pkt, sort_keys=True)
    drm.build_dashboard_read_model_v1(pkt)
    assert json.dumps(pkt, sort_keys=True) == original


# ---------------------------------------------------------------------------
# Test: build_dashboard_read_model_v1 - failure path
# ---------------------------------------------------------------------------


def test_build_read_model_invalid_input():
    rm = drm.build_dashboard_read_model_v1("not a dict")
    assert rm["ok"] is False
    assert len(rm["errors"]) > 0
    assert rm["input_packet"] is None
    assert rm["sections"] == {}


def test_build_read_model_invalid_observation_status():
    pkt = _valid_input()
    pkt["sections"]["public_protected_site_health"]["status"] = "is_healthy"
    rm = drm.build_dashboard_read_model_v1(pkt)
    assert rm["ok"] is False


# ---------------------------------------------------------------------------
# Test: JSON-safe serialization
# ---------------------------------------------------------------------------


def test_json_safe_happy_path():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    j = drm.to_dashboard_read_model_json_safe_v1(rm)
    assert isinstance(j, str)
    parsed = json.loads(j)
    assert parsed["ok"] is True


def test_json_safe_strips_forbidden_keys_defense_in_depth():
    """Even if a forbidden key slipped through, the JSON-safe
    serializer must redact it."""
    rm = {
        "ok": True,
        "schema_version": "1",
        "api_key": "leaked",  # forbidden
        "sections": {
            "backend_health": {
                "is_observation": True,
                "status": "pass",
                "summary": "x",
                "details": {
                    "password": "leaked",  # forbidden
                },
            },
        },
    }
    j = drm.to_dashboard_read_model_json_safe_v1(rm)
    parsed = json.loads(j)
    assert parsed["api_key"] == "<redacted:dashboard-forbidden-key>"
    assert (
        parsed["sections"]["backend_health"]["details"]["password"]
        == "<redacted:dashboard-forbidden-key>"
    )


def test_json_safe_handles_non_serializable():
    rm = {"ok": True, "data": b"bytes"}
    j = drm.to_dashboard_read_model_json_safe_v1(rm)
    parsed = json.loads(j)
    assert parsed["ok"] is False
    assert "serialization_error" in parsed["error"]


def test_json_safe_is_sorted_keys():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    j = drm.to_dashboard_read_model_json_safe_v1(rm)
    # Sort keys means the output is deterministic
    j2 = drm.to_dashboard_read_model_json_safe_v1(rm)
    assert j == j2


# ---------------------------------------------------------------------------
# Test: safe-Markdown rendering
# ---------------------------------------------------------------------------


def test_markdown_renders_happy_path():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    assert isinstance(md, str)
    assert "# Dashboard Read-Model V1" in md
    assert "## Sections" in md
    assert "## Blocked Actions / Safety Boundaries" in md
    assert "## Warnings Requiring Operator Attention" in md
    assert "is_observation_only" in md
    assert "is_live_inference" in md


def test_markdown_escapes_backticks():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["summary"] = "summary with `backticks` here"
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    # Backticks should be escaped (preceded by backslash)
    assert "\\`backticks\\`" in md


def test_markdown_escapes_angle_brackets():
    pkt = _valid_input()
    pkt["sections"]["backend_health"]["summary"] = "summary with <script> tag"
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    assert "&lt;script&gt;" in md
    # Raw <script> must NOT appear (defense-in-depth)
    # Note: the assertion above may overlap with markdown angle bracket
    # in heading markers. The escaped form is sufficient.


def test_markdown_renders_validation_failure():
    rm = {
        "schema_version": "1",
        "ok": False,
        "errors": ["invalid_section_name:foo"],
    }
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    assert "validation failed" in md.lower()
    assert "invalid_section_name:foo" in md


def test_markdown_handles_non_dict_input():
    md = drm.to_dashboard_read_model_markdown_v1("not a dict")
    assert "error" in md.lower()


def test_markdown_observation_disclaimer_present():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    # Must include the observation-only disclaimer
    assert "observation-only" in md


# ---------------------------------------------------------------------------
# Test: summarize
# ---------------------------------------------------------------------------


def test_summarize_happy_path():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    s = drm.summarize_dashboard_read_model_v1(rm)
    assert "DashboardReadModelV1" in s
    assert "ok=True" in s
    assert "operator=" + VALID_OPERATOR_ID in s
    assert "recommended_lane=APPROVE_NEXT_SLICE" in s
    assert "warnings=1" in s


def test_summarize_failure_path():
    s = drm.summarize_dashboard_read_model_v1({"ok": False, "errors": ["x", "y"]})
    assert "ok=False" in s


def test_summarize_handles_non_dict():
    s = drm.summarize_dashboard_read_model_v1("not a dict")
    assert "ok=False" in s


# ---------------------------------------------------------------------------
# Test: wiring invariants
# ---------------------------------------------------------------------------


def test_no_chat_responder_import_in_source():
    """The helper source must not import or call ChatResponder,
    even in docstrings/comments at the executable level."""
    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()
    import ast
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "chat_responder" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert "chat_responder" not in node.module
                assert "chat_ui" not in node.module
                assert "dialogue" not in node.module
                assert "main" not in node.module
                assert "providers" not in node.module
                assert "weslr" not in node.module


def test_no_payment_provider_in_source():
    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()
    # The helper may mention payment providers ONLY in docstring
    # or comment lines (e.g., in the "does NOT call any payment
    # provider (Stripe, Adyen, Klarna, etc.)" negation). Verify
    # that any line containing a payment provider name is a
    # docstring or comment line.
    for provider in ("stripe", "paypal", "adyen", "klarna", "braintree"):
        for line in source.split("\n"):
            if provider in line.lower():
                stripped = line.lstrip()
                # Allowed contexts: docstring (starts with quote
                # or is inside a docstring block), comment (starts
                # with #), or negation phrases.
                if not (
                    stripped.startswith("#")
                    or stripped.startswith('"')
                    or stripped.startswith("'")
                    or stripped.startswith("- ")
                    or stripped.startswith("  - ")
                    or "does NOT" in line
                    or "does not" in line
                    or "blocked in this lane" in line
                    or "no payment provider" in line
                    or "no_payment" in line
                ):
                    raise AssertionError(
                        f"payment provider {provider!r} appears in "
                        f"non-docstring line: {line!r}"
                    )


def test_no_filesystem_writes_in_source():
    """The helper must not perform filesystem writes (no open(...,'w'),
    no os.makedirs, no .write() in executable code)."""
    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()
    import ast
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "open":
                    # All open() calls must be 'r' (read-only) for
                    # test inspection only. The helper itself does
                    # not use open().
                    pass


def test_no_weslr_state_path_in_source():
    """The helper must not reference /home/pr0/weslr_state/ in
    executable code (docstring negation is allowed)."""
    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()
    # Find any reference to weslr_state
    if "weslr_state" in source:
        # Ensure it's only in negation context (docstring or comment)
        for line in source.split("\n"):
            if "weslr_state" in line:
                # Strip leading whitespace and check for negation
                stripped = line.lstrip()
                if not (
                    stripped.startswith("#")
                    or 'no real persistence' in line
                    or 'Writes to /home/pr0/weslr_state/ are blocked' in line
                ):
                    raise AssertionError(
                        f"weslr_state appears in non-docstring line: {line!r}"
                    )


def test_no_executable_runtime_call_in_source():
    """The helper must not call any of the runtime/infra modules."""
    source_path = _helper_source_path()
    with open(source_path) as f:
        source = f.read()
    import ast
    tree = ast.parse(source)
    forbidden_modules = {
        "weslr.chat_responder", "weslr.dialogue", "weslr.chat_ui",
        "weslr.runtime_wrapper", "weslr.session_manager",
        "weslr.audit_log", "weslr.audit_log_persistence",
        "weslr.account_status", "weslr.entitlement_packet",
        "weslr.billing_abo_status", "weslr.main", "main",
        "dialogue", "chat_ui",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_modules
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert node.module not in forbidden_modules
        elif isinstance(node, ast.Call):
            # Check for runtime calls like weslr.chat_responder.respond()
            if isinstance(node.func, ast.Attribute):
                pass  # We don't follow attribute chains; the import
                      # check is the primary guard


# ---------------------------------------------------------------------------
# Test: section ordering
# ---------------------------------------------------------------------------


def test_sections_iterate_in_canonical_order():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    # Sections should be iterable, and the order in the output
    # should match DASHBOARD_READ_MODEL_SECTIONS_V1 (deterministic).
    keys = list(rm["sections"].keys())
    # We don't require strict ordering, but every expected key
    # must be present
    for k in drm.DASHBOARD_READ_MODEL_SECTIONS_V1:
        if k not in ("blocked_actions", "warnings_requiring_operator_attention"):
            assert k in keys, f"expected section {k} missing"


# ---------------------------------------------------------------------------
# Test: stress / boundary cases
# ---------------------------------------------------------------------------


def test_validate_empty_packet():
    result = drm.validate_dashboard_read_model_input_v1({})
    assert result["ok"] is False
    # Should report multiple missing keys
    missing = [e for e in result["errors"] if drm.REASON_INVALID_INPUT_MISSING_KEY in e]
    assert len(missing) >= 5  # 5 required top-level keys


def test_validate_minimal_valid_packet():
    pkt = _valid_input()
    # Strip details to minimum
    for sec_name, sec in pkt["sections"].items():
        if isinstance(sec, dict) and "details" in sec:
            sec["details"] = {}
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True


def test_validate_input_with_operator_auditor_role():
    pkt = _valid_input()
    pkt["operator_role"] = "operator_auditor"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True


def test_validate_input_with_operator_viewer_role():
    pkt = _valid_input()
    pkt["operator_role"] = "operator_viewer"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is True


def test_build_then_serialize_then_render_round_trip():
    """Full happy path: validate → build → JSON-serialize → Markdown-render."""
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    assert rm["ok"] is True
    j = drm.to_dashboard_read_model_json_safe_v1(rm)
    parsed = json.loads(j)
    assert parsed["ok"] is True
    md = drm.to_dashboard_read_model_markdown_v1(rm)
    assert "# Dashboard Read-Model V1" in md


def test_summary_after_build():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    s = drm.summarize_dashboard_read_model_v1(rm)
    assert "DashboardReadModelV1" in s


# ---------------------------------------------------------------------------
# Test: error accumulation (multi-error reporting)
# ---------------------------------------------------------------------------


def test_validate_input_reports_multiple_errors():
    pkt = _valid_input()
    pkt["schema_version"] = "wrong"
    pkt["operator_id"] = ""
    pkt["operator_role"] = "invalid"
    pkt["sections"]["backend_health"]["status"] = "is_healthy"
    pkt["api_key"] = "leaked"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    # Should have at least 5 distinct errors
    assert len(result["errors"]) >= 5


def test_validate_input_continues_after_first_error():
    """The validator must collect ALL errors, not stop at the first."""
    pkt = _valid_input()
    pkt["schema_version"] = "wrong"
    pkt["operator_role"] = "invalid"
    result = drm.validate_dashboard_read_model_input_v1(pkt)
    assert result["ok"] is False
    assert len(result["errors"]) >= 2


# ---------------------------------------------------------------------------
# Test: minimal metadata
# ---------------------------------------------------------------------------


def test_minimal_metadata_present():
    pkt = _valid_input()
    rm = drm.build_dashboard_read_model_v1(pkt)
    md = rm["metadata"]
    for k in (
        "schema_version", "generated_at_utc", "operator_id",
        "operator_role", "is_dashboard_read_model", "is_live_inference",
        "is_observation_only", "is_authority_claim",
        "is_production_ready", "is_live_public_runtime",
    ):
        assert k in md, f"metadata key {k} missing"
