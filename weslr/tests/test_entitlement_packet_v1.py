"""
WESLR chat.weslr.de Slice 5 — Entitlement Packet Helper Tests V1

Standalone tests for the entitlement packet helper. Pure-Python,
no I/O, no protected-file imports, no provider/model calls, no
network, no subprocess, no payment provider.

Run:
  python3 -m unittest weslr.tests.test_entitlement_packet_v1 -v
"""

from __future__ import annotations

import unittest

from weslr.entitlement_packet import (
    ENTITLEMENT_PACKET_VERSION,
    ENTITLEMENT_NEVER_INCLUDES,
    REASON_OK,
    REASON_INVALID_NOT_DICT,
    REASON_INVALID_MISSING_FIELDS,
    REASON_INVALID_BAD_ACCOUNT_STATUS,
    REASON_INVALID_BAD_SUBSCRIPTION_STATUS,
    REASON_INVALID_CAPABILITIES_NOT_LIST,
    REASON_INVALID_CAPABILITIES_NOT_SUBSET,
    REASON_INVALID_FORBIDDEN_KEY,
    REASON_INVALID_EMPTY_ACCOUNT_ID,
    REASON_INVALID_QUOTA_NOT_INT,
    REASON_INVALID_BOOLEAN_NOT_BOOL,
    REASON_INVALID_BAD_VERSION,
    build_entitlement_packet_v1,
    validate_entitlement_packet_v1,
    compute_entitlement_packet_from_status_v1,
    is_action_allowed_by_entitlement_v1,
    summarize_entitlement_packet_v1,
    to_entitlement_packet_json_safe_v1,
)

# Import the runtime wrapper's safe actions to verify our
# strict-subset validation.
from weslr.runtime_wrapper import SAFE_ACTIONS_V1


def _make_packet(
    account_id="pilot_1",
    account_status="pilot_active",
    subscription_status="free_pilot",
    allowed_capabilities=None,
    chat_access_enabled=True,
    entitlement_id="ep-1",
    max_messages_per_day=100,
    max_sessions=1,
    operator_can_force_logout=False,
    operator_can_pause=False,
    operator_can_rotate_credentials=False,
    operator_can_revoke_capability=False,
    operator_can_extend_grace=False,
    entitlement_expiry="",
    entitlement_grace_period_end="",
    audit_log_ref="",
    file_upload_allowed=False,
    project_memory_allowed=False,
    marketplace_artifact_access_allowed=False,
    model_tool_access_allowed=False,
):
    if allowed_capabilities is None:
        # Default: a safe-action subset.
        allowed_capabilities = ["health_check_read", "status_read"]
    return build_entitlement_packet_v1(
        account_id=account_id,
        account_status=account_status,
        subscription_status=subscription_status,
        entitlement_id=entitlement_id,
        allowed_capabilities=allowed_capabilities,
        chat_access_enabled=chat_access_enabled,
        max_messages_per_day=max_messages_per_day,
        max_sessions=max_sessions,
        operator_can_force_logout=operator_can_force_logout,
        operator_can_pause=operator_can_pause,
        operator_can_rotate_credentials=operator_can_rotate_credentials,
        operator_can_revoke_capability=operator_can_revoke_capability,
        operator_can_extend_grace=operator_can_extend_grace,
        entitlement_expiry=entitlement_expiry,
        entitlement_grace_period_end=entitlement_grace_period_end,
        audit_log_ref=audit_log_ref,
        file_upload_allowed=file_upload_allowed,
        project_memory_allowed=project_memory_allowed,
        marketplace_artifact_access_allowed=marketplace_artifact_access_allowed,
        model_tool_access_allowed=model_tool_access_allowed,
    )


class TestBuildPacket(unittest.TestCase):
    def test_version_present(self):
        p = _make_packet()
        self.assertEqual(p["entitlement_version"], ENTITLEMENT_PACKET_VERSION)

    def test_packet_id_auto_uuid(self):
        p = build_entitlement_packet_v1(
            account_id="x", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertEqual(len(p["entitlement_id"]), 36)

    def test_raw_content_retained_always_false(self):
        p = _make_packet()
        self.assertFalse(p["raw_content_retained"])

    def test_required_fields_present(self):
        p = _make_packet()
        for key in (
            "entitlement_version", "entitlement_id", "account_id",
            "account_status", "subscription_status", "entitlement_computed_at",
            "entitlement_computed_by", "allowed_capabilities",
            "max_messages_per_day", "max_sessions",
            "file_upload_allowed", "project_memory_allowed",
            "marketplace_artifact_access_allowed", "model_tool_access_allowed",
            "chat_access_enabled", "operator_override_flags",
            "entitlement_expiry", "entitlement_grace_period_end",
            "audit_log_ref", "raw_content_retained",
        ):
            self.assertIn(key, p)

    def test_default_capability_set_from_pilot_active(self):
        # Use build_entitlement_packet_v1 directly so the default mapping
        # is exercised (the _make_packet helper passes explicit capabilities).
        p = build_entitlement_packet_v1(
            account_id="pilot_1", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertIn("health_check_read", p["allowed_capabilities"])
        self.assertIn("status_read", p["allowed_capabilities"])

    def test_default_capability_set_from_manual_paid(self):
        # Default mapping for manual_paid/active should include the full
        # read-only set (3 safe actions).
        p = build_entitlement_packet_v1(
            account_id="manual_1", account_status="manual_paid", subscription_status="active",
        )
        self.assertIn("operator_review_packet_read", p["allowed_capabilities"])

    def test_default_capability_set_for_banned_is_empty(self):
        # Banned: no capabilities by default.
        p = build_entitlement_packet_v1(
            account_id="x", account_status="banned", subscription_status="active",
        )
        self.assertEqual(p["allowed_capabilities"], [])

    def test_explicit_capabilities_override_default(self):
        p = _make_packet(
            account_status="banned",
            allowed_capabilities=["status_read"],
        )
        self.assertEqual(p["allowed_capabilities"], ["status_read"])


class TestValidatePacket(unittest.TestCase):
    def test_valid_packet_passes(self):
        p = _make_packet()
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertTrue(ok, msg=f"errors: {errs}")
        self.assertEqual(errs, [])

    def test_rejects_non_dict_packet(self):
        # Coverage item 3: rejects non-dict packet
        for non_dict in (None, "not-a-dict", 42, [1, 2, 3], (1, 2)):
            ok, errs = validate_entitlement_packet_v1(non_dict)
            self.assertFalse(ok, msg=f"{non_dict!r} should be rejected")
            self.assertIn(REASON_INVALID_NOT_DICT, errs)

    def test_rejects_missing_entitlement_id(self):
        # Coverage item 4: rejects missing entitlement_id
        p = _make_packet()
        del p["entitlement_id"]
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any("missing_required_fields:entitlement_id" in e for e in errs))

    def test_rejects_missing_account_id(self):
        # Coverage item 5: rejects missing account_id
        p = _make_packet()
        del p["account_id"]
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any("missing_required_fields:account_id" in e for e in errs))

    def test_rejects_missing_account_id_in_compute(self):
        # Coverage item 5: rejects empty account_id in compute
        result = compute_entitlement_packet_from_status_v1(
            account_id="", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_EMPTY_ACCOUNT_ID, result["reason_labels"])

    def test_rejects_missing_field_required(self):
        # Coverage item 2: validates required fields (already covered
        # by test_each_required_field_independently_checked; this is the
        # explicit "validates required fields" test for the coverage list).
        p = _make_packet()
        for required_key in (
            "entitlement_version", "entitlement_id", "account_id",
            "account_status", "subscription_status", "entitlement_computed_at",
            "entitlement_computed_by", "allowed_capabilities",
            "max_messages_per_day", "max_sessions",
            "file_upload_allowed", "project_memory_allowed",
            "marketplace_artifact_access_allowed", "model_tool_access_allowed",
            "chat_access_enabled", "operator_override_flags",
            "entitlement_expiry", "entitlement_grace_period_end",
            "audit_log_ref", "raw_content_retained",
        ):
            p_test = _make_packet()
            del p_test[required_key]
            ok, errs = validate_entitlement_packet_v1(p_test)
            self.assertFalse(ok, msg=f"field {required_key} should be required")

    def test_invalid_account_status_rejected(self):
        # Coverage item 6: rejects unknown account status
        p = _make_packet(account_status="not_a_real_status")
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_ACCOUNT_STATUS in e for e in errs))

    def test_invalid_subscription_status_rejected(self):
        # Coverage item 7: rejects unknown subscription status
        p = _make_packet(subscription_status="not_a_real_subscription")
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_SUBSCRIPTION_STATUS in e for e in errs))

    def test_invalid_version_rejected(self):
        p = _make_packet()
        p["entitlement_version"] = "weslr-entitlement-packet-v999"
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_VERSION in e for e in errs))

    def test_capabilities_not_list_rejected(self):
        p = _make_packet()
        p["allowed_capabilities"] = "not-a-list"
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_CAPABILITIES_NOT_LIST, errs)

    def test_capabilities_not_subset_of_safe_actions_rejected(self):
        # Coverage item 9: rejects capability outside SAFE_ACTIONS_V1
        p = _make_packet(allowed_capabilities=["health_check_read", "fake_capability"])
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_CAPABILITIES_NOT_SUBSET in e for e in errs))

    def test_capability_not_string_rejected(self):
        p = _make_packet()
        p["allowed_capabilities"] = ["health_check_read", 42]
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any("capability_not_string" in e for e in errs))

    def test_negative_max_messages_per_day_rejected(self):
        # Coverage item 10: rejects negative max_messages_per_day
        p = _make_packet(max_messages_per_day=-1)
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_QUOTA_NOT_INT in e for e in errs))

    def test_negative_max_sessions_rejected(self):
        # Coverage item 11: rejects negative max_sessions
        p = _make_packet(max_sessions=-1)
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_QUOTA_NOT_INT in e for e in errs))

    def test_boolean_not_bool_rejected(self):
        # Coverage item 12: rejects non-bool feature flags
        for bool_key in (
            "file_upload_allowed", "project_memory_allowed",
            "marketplace_artifact_access_allowed", "model_tool_access_allowed",
            "chat_access_enabled", "raw_content_retained",
        ):
            p = _make_packet()
            p[bool_key] = "not-a-bool"
            ok, errs = validate_entitlement_packet_v1(p)
            self.assertFalse(ok, msg=f"{bool_key} should be bool")
            self.assertTrue(any(REASON_INVALID_BOOLEAN_NOT_BOOL in e for e in errs))

    def test_invalid_operator_override_flags_rejected(self):
        # Coverage item 13: rejects invalid operator_override_flags
        p = _make_packet()
        p["operator_override_flags"] = "not-a-dict"
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertIn("operator_override_flags_not_dict", errs)

    def test_raw_content_retained_true_rejected(self):
        # Coverage item 8: rejects raw_content_retained=True
        p = _make_packet()
        p["raw_content_retained"] = True
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertFalse(ok)
        self.assertIn("raw_content_retained_must_be_false", errs)

    def test_default_deny_if_capabilities_empty(self):
        # Coverage item 14: default-deny if allowed_capabilities is empty
        p = _make_packet(allowed_capabilities=[])
        # The packet itself is still valid; the deny happens at action time.
        ok, errs = validate_entitlement_packet_v1(p)
        self.assertTrue(ok, msg=f"empty caps packet is structurally valid: {errs}")
        # But no action is allowed.
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertFalse(result["allowed"])

    def test_pilot_active_allows_health_check_read(self):
        # Coverage item 15
        result = compute_entitlement_packet_from_status_v1(
            account_id="pilot_x", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertTrue(result["ok"])
        r = is_action_allowed_by_entitlement_v1(result["packet"], "health_check_read")
        self.assertTrue(r["allowed"])

    def test_pilot_active_allows_status_read(self):
        # Coverage item 16
        result = compute_entitlement_packet_from_status_v1(
            account_id="pilot_x", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertTrue(result["ok"])
        r = is_action_allowed_by_entitlement_v1(result["packet"], "status_read")
        self.assertTrue(r["allowed"])

    def test_pilot_active_denies_operator_review_packet_read(self):
        # Coverage item 17
        result = compute_entitlement_packet_from_status_v1(
            account_id="pilot_x", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertTrue(result["ok"])
        r = is_action_allowed_by_entitlement_v1(result["packet"], "operator_review_packet_read")
        self.assertFalse(r["allowed"])

    def test_manual_paid_active_gets_all_safe_read_capabilities(self):
        # Coverage item 18
        result = compute_entitlement_packet_from_status_v1(
            account_id="manual_x", account_status="manual_paid", subscription_status="active",
        )
        self.assertTrue(result["ok"])
        caps = result["packet"]["allowed_capabilities"]
        self.assertIn("health_check_read", caps)
        self.assertIn("status_read", caps)
        self.assertIn("operator_review_packet_read", caps)
        r_h = is_action_allowed_by_entitlement_v1(result["packet"], "health_check_read")
        r_s = is_action_allowed_by_entitlement_v1(result["packet"], "status_read")
        r_o = is_action_allowed_by_entitlement_v1(result["packet"], "operator_review_packet_read")
        self.assertTrue(r_h["allowed"])
        self.assertTrue(r_s["allowed"])
        self.assertTrue(r_o["allowed"])

    def test_manual_unpaid_grace_gets_status_read_only(self):
        # Coverage item 19
        result = compute_entitlement_packet_from_status_v1(
            account_id="manual_x", account_status="manual_unpaid", subscription_status="grace_period",
        )
        self.assertTrue(result["ok"])
        caps = result["packet"]["allowed_capabilities"]
        self.assertEqual(caps, ["status_read"])

    def test_banned_gets_no_capabilities(self):
        # Coverage item 20
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="banned", subscription_status="active",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["packet"]["allowed_capabilities"], [])
        self.assertFalse(result["packet"]["chat_access_enabled"])

    def test_deleted_or_revoked_gets_no_capabilities(self):
        # Coverage item 21
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="deleted_or_revoked", subscription_status="active",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["packet"]["allowed_capabilities"], [])
        self.assertFalse(result["packet"]["chat_access_enabled"])

    def test_pilot_paused_gets_no_capabilities(self):
        # Coverage item 22
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_paused", subscription_status="free_pilot",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["packet"]["allowed_capabilities"], [])
        self.assertFalse(result["packet"]["chat_access_enabled"])

    def test_pilot_expired_grace_gets_status_read_only(self):
        # Coverage item 23
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_expired", subscription_status="grace_period",
        )
        self.assertTrue(result["ok"])
        caps = result["packet"]["allowed_capabilities"]
        self.assertEqual(caps, ["status_read"])

    def test_subscription_disabled_for_nonpayment_disables_access(self):
        # Coverage item 24
        # Pair an active-account status with disabled_for_nonpayment
        # subscription — chat should be disabled.
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="manual_paid", subscription_status="disabled_for_nonpayment",
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["packet"]["chat_access_enabled"])
        # And no action is allowed.
        r = is_action_allowed_by_entitlement_v1(result["packet"], "status_read")
        self.assertFalse(r["allowed"])

    def test_computes_entitlement_from_account_subscription_status(self):
        # Coverage item 25: computes entitlement from account/subscription status
        result = compute_entitlement_packet_from_status_v1(
            account_id="manual_y", account_status="manual_paid", subscription_status="active",
        )
        self.assertTrue(result["ok"])
        p = result["packet"]
        self.assertEqual(p["account_id"], "manual_y")
        self.assertEqual(p["account_status"], "manual_paid")
        self.assertEqual(p["subscription_status"], "active")
        self.assertIn("operator_review_packet_read", p["allowed_capabilities"])

    def test_summary_contains_no_raw_private_payment_keys(self):
        # Coverage item 26: summary contains no raw/private/payment keys
        p = _make_packet()
        # Add a bunch of forbidden keys; the summary must not leak them.
        p["raw_prompt"] = "SENSITIVE_PROMPT"
        p["password"] = "SENSITIVE_PW"
        p["api_key"] = "SENSITIVE_KEY"
        p["payment_card"] = "4111111111111111"
        p["card_number"] = "4111111111111111"
        p["iban"] = "DE89370400440532013000"
        p["bank_account"] = "DE89370400440532013000"
        s = summarize_entitlement_packet_v1(p)
        forbidden = [
            "SENSITIVE_PROMPT", "SENSITIVE_PW", "SENSITIVE_KEY",
            "4111111111111111", "DE89370400440532013000",
            "raw_prompt", "password", "api_key",
            "payment_card", "card_number", "iban", "bank_account",
        ]
        for f in forbidden:
            self.assertNotIn(f, s, msg=f"summary leaked forbidden key: {f}")

    def test_json_safe_strips_payment_keys(self):
        # Verify the 4 new payment-related forbidden keys are stripped.
        p = _make_packet()
        p["payment_card"] = "4111111111111111"
        p["card_number"] = "4111111111111111"
        p["iban"] = "DE89370400440532013000"
        p["bank_account"] = "DE89370400440532013000"
        s = to_entitlement_packet_json_safe_v1(p)
        for leaked in ("4111111111111111", "DE89370400440532013000",
                       "payment_card", "card_number", "iban", "bank_account"):
            self.assertNotIn(leaked, s, msg=f"forbidden payment key leaked: {leaked}")


class TestComputePacket(unittest.TestCase):
    def test_compute_pilot_active_yields_health_and_status(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="pilot_1", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertTrue(result["ok"], msg=result)
        p = result["packet"]
        self.assertIn("health_check_read", p["allowed_capabilities"])
        self.assertIn("status_read", p["allowed_capabilities"])
        # Pilot users do NOT get operator_review_packet_read by default.
        self.assertNotIn("operator_review_packet_read", p["allowed_capabilities"])

    def test_compute_manual_paid_yields_full_read_only_set(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="manual_1", account_status="manual_paid", subscription_status="active",
        )
        self.assertTrue(result["ok"], msg=result)
        p = result["packet"]
        self.assertIn("health_check_read", p["allowed_capabilities"])
        self.assertIn("status_read", p["allowed_capabilities"])
        self.assertIn("operator_review_packet_read", p["allowed_capabilities"])

    def test_compute_banned_yields_empty_capabilities(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="banned", subscription_status="active",
        )
        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(result["packet"]["allowed_capabilities"], [])

    def test_compute_banned_yields_chat_disabled(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="banned", subscription_status="active",
        )
        self.assertFalse(result["packet"]["chat_access_enabled"])

    def test_compute_pilot_expired_grace_yields_only_status(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_expired", subscription_status="grace_period",
        )
        self.assertTrue(result["ok"], msg=result)
        caps = result["packet"]["allowed_capabilities"]
        self.assertIn("status_read", caps)
        self.assertNotIn("health_check_read", caps)
        self.assertNotIn("operator_review_packet_read", caps)

    def test_compute_operator_role_yields_full_set(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="op_alice", account_status="operator", subscription_status="active",
        )
        self.assertTrue(result["ok"], msg=result)
        p = result["packet"]
        self.assertEqual(set(p["allowed_capabilities"]),
                         {"health_check_read", "status_read", "operator_review_packet_read"})
        # Operator role gets higher quota defaults.
        self.assertEqual(p["max_messages_per_day"], 1000)
        self.assertEqual(p["max_sessions"], 5)

    def test_compute_rejects_empty_account_id(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="", account_status="pilot_active", subscription_status="free_pilot",
        )
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_EMPTY_ACCOUNT_ID, result["reason_labels"])

    def test_compute_rejects_invalid_account_status(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="not_a_real_status", subscription_status="free_pilot",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any(REASON_INVALID_BAD_ACCOUNT_STATUS in e for e in result["reason_labels"]))

    def test_compute_rejects_invalid_subscription_status(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_active", subscription_status="not_real",
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any(REASON_INVALID_BAD_SUBSCRIPTION_STATUS in e for e in result["reason_labels"]))

    def test_compute_rejects_override_capabilities_not_list(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_active", subscription_status="free_pilot",
            allow_override_capabilities="not-a-list",
        )
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_CAPABILITIES_NOT_LIST, result["reason_labels"])

    def test_compute_rejects_override_capabilities_not_subset(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_active", subscription_status="free_pilot",
            allow_override_capabilities=["fake_capability"],
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any(REASON_INVALID_CAPABILITIES_NOT_SUBSET in e for e in result["reason_labels"]))

    def test_compute_accepts_valid_override_capabilities(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="banned", subscription_status="active",
            allow_override_capabilities=["status_read"],  # override the empty default
        )
        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(result["packet"]["allowed_capabilities"], ["status_read"])

    def test_compute_overrides_apply_to_quotas(self):
        result = compute_entitlement_packet_from_status_v1(
            account_id="x", account_status="pilot_active", subscription_status="free_pilot",
            max_messages_per_day=500,
            max_sessions=3,
        )
        self.assertEqual(result["packet"]["max_messages_per_day"], 500)
        self.assertEqual(result["packet"]["max_sessions"], 3)


class TestIsActionAllowed(unittest.TestCase):
    def test_action_in_capabilities_allowed(self):
        p = _make_packet(allowed_capabilities=["health_check_read", "status_read"])
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertTrue(result["ok"])
        self.assertTrue(result["allowed"])
        self.assertIn(REASON_OK, result["reason_labels"])

    def test_action_not_in_capabilities_denied(self):
        p = _make_packet(allowed_capabilities=["status_read"])
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertFalse(result["allowed"])
        self.assertTrue(any("denied_capability_not_in_packet" in e for e in result["reason_labels"]))

    def test_chat_disabled_denies_all(self):
        p = _make_packet(
            allowed_capabilities=["health_check_read", "status_read"],
            chat_access_enabled=False,
        )
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertFalse(result["allowed"])
        self.assertTrue(any("denied_chat_access_disabled" in e for e in result["reason_labels"]))

    def test_empty_capabilities_denies_all(self):
        p = _make_packet(allowed_capabilities=[])
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertFalse(result["allowed"])

    def test_action_not_in_safe_actions_denied(self):
        # Defensively: if a packet somehow contains a capability that
        # is NOT in the runtime wrapper's SAFE_ACTIONS_V1, the action
        # is denied even if the packet claims it (defense in depth).
        p = _make_packet(allowed_capabilities=["not_a_real_action"])
        result = is_action_allowed_by_entitlement_v1(p, "not_a_real_action")
        self.assertFalse(result["allowed"])

    def test_non_dict_packet_denied(self):
        result = is_action_allowed_by_entitlement_v1("not-a-dict", "health_check_read")
        self.assertFalse(result["allowed"])
        self.assertIn(REASON_INVALID_NOT_DICT, result["reason_labels"])

    def test_invalid_action_type_rejected(self):
        p = _make_packet()
        result = is_action_allowed_by_entitlement_v1(p, "")
        self.assertFalse(result["allowed"])
        result = is_action_allowed_by_entitlement_v1(p, None)
        self.assertFalse(result["allowed"])
        result = is_action_allowed_by_entitlement_v1(p, 42)
        self.assertFalse(result["allowed"])

    def test_invalid_packet_denied(self):
        # Packet missing required field should not allow any action.
        p = _make_packet()
        del p["account_id"]
        result = is_action_allowed_by_entitlement_v1(p, "health_check_read")
        self.assertFalse(result["allowed"])


class TestStrictSubsetMapping(unittest.TestCase):
    """Verify all capability mappings stay within SAFE_ACTIONS_V1."""

    def test_all_status_pairs_map_to_strict_subset_of_safe_actions(self):
        # Iterate over all combinations of (account_status, subscription_status)
        # and check that the resulting capability set is a subset of SAFE_ACTIONS_V1.
        all_statuses = [
            "invited", "pilot_free", "pilot_active", "pilot_paused", "pilot_expired",
            "manual_paid", "manual_unpaid", "manual_disabled",
            "banned", "deletion_requested", "deleted_or_revoked", "operator",
        ]
        all_subscriptions = [
            "no_subscription", "free_pilot", "trialing", "active", "past_due",
            "unpaid", "canceled", "refunded", "disputed", "grace_period",
            "disabled_for_nonpayment",
        ]
        for acc in all_statuses:
            for sub in all_subscriptions:
                result = compute_entitlement_packet_from_status_v1(
                    account_id="x", account_status=acc, subscription_status=sub,
                )
                self.assertTrue(result["ok"], msg=f"{acc}/{sub} compute failed: {result}")
                caps = result["packet"]["allowed_capabilities"]
                for c in caps:
                    self.assertIn(c, SAFE_ACTIONS_V1,
                                  msg=f"capability {c!r} for {acc}/{sub} not in SAFE_ACTIONS_V1")


class TestSummaryAndSerialization(unittest.TestCase):
    def test_summary_for_valid_packet(self):
        p = _make_packet(
            account_id="pilot_42",
            account_status="pilot_active",
            subscription_status="free_pilot",
        )
        s = summarize_entitlement_packet_v1(p)
        self.assertIn("pilot_42", s)
        self.assertIn("pilot_active", s)
        self.assertIn("free_pilot", s)
        self.assertIn("chat_enabled=True", s)

    def test_summary_for_invalid_packet(self):
        s = summarize_entitlement_packet_v1("not-a-dict")
        self.assertIn("invalid_entitlement_packet", s)

    def test_json_safe_for_packet(self):
        p = _make_packet()
        s = to_entitlement_packet_json_safe_v1(p)
        self.assertTrue(s.startswith("{"))
        self.assertIn(f'"entitlement_version": "{ENTITLEMENT_PACKET_VERSION}"', s)
        self.assertIn('"account_id": "pilot_1"', s)

    def test_json_safe_strips_forbidden_keys(self):
        p = _make_packet()
        # Add forbidden keys at various depths.
        p["raw_prompt"] = "SENSITIVE_PROMPT"
        p["operator_override_flags"]["password"] = "SENSITIVE_PASSWORD"
        p["allowed_capabilities"].append({"chain_of_thought": "TRACE"})
        s = to_entitlement_packet_json_safe_v1(p)
        for forbidden in ("SENSITIVE_PROMPT", "SENSITIVE_PASSWORD", "TRACE"):
            self.assertNotIn(forbidden, s, msg=f"forbidden key leaked: {forbidden}")
        for key in ("raw_prompt", "password", "chain_of_thought"):
            self.assertNotIn(f'"{key}"', s, msg=f"forbidden key name leaked: {key}")

    def test_json_safe_for_cyclic(self):
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_entitlement_packet_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertTrue("<cyclic>" in s or "serialization_error" in s)

    def test_summary_does_not_contain_forbidden_keys(self):
        p = _make_packet()
        s = summarize_entitlement_packet_v1(p)
        for forbidden in ENTITLEMENT_NEVER_INCLUDES:
            self.assertNotIn(forbidden, s, msg=f"summary leaked forbidden key: {forbidden}")


class TestIsPure(unittest.TestCase):
    """The entitlement packet helper does not import protected runtime
    modules or provider/model/network/subprocess modules."""

    @staticmethod
    def _read_source():
        import weslr.entitlement_packet as ep
        with open(ep.__file__, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_imports_only_from_runtime_wrapper_safe_actions(self):
        import weslr.entitlement_packet as ep
        import inspect
        src = inspect.getsource(ep)
        # The only allowed cross-module import is from runtime_wrapper
        # for SAFE_ACTIONS_V1 (used to validate strict subset).
        # All other cross-module imports are forbidden.
        self.assertIn("from weslr.runtime_wrapper import SAFE_ACTIONS_V1", src)
        for forbidden in (
            "import weslr.chat_responder",
            "from weslr.chat_responder",
            "import weslr.dialogue",
            "from weslr.dialogue",
            "import weslr.chat_ui",
            "from weslr.chat_ui",
            "import weslr.session_manager",
            "from weslr.session_manager",
            "import weslr.audit_log_persistence",
            "from weslr.audit_log_persistence",
            "import weslr.audit_log",
            "from weslr.audit_log",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")

    def test_no_subprocess_import(self):
        src = self._read_source()
        self.assertNotIn("import subprocess", src)
        self.assertNotIn("from subprocess", src)

    def test_no_network_import(self):
        src = self._read_source()
        for net in ("urllib", "requests", "httpx", "socket", "aiohttp"):
            self.assertNotIn(net, src, msg=f"unexpected network module: {net}")

    def test_no_provider_or_model_import(self):
        src = self._read_source()
        for term in ("openai", "anthropic", "ollama", "transformers", "torch"):
            self.assertNotIn(term, src, msg=f"unexpected provider module: {term}")

    def test_no_payment_provider_import(self):
        src = self._read_source()
        for term in ("stripe", "paypal", "braintree", "square", "adyen"):
            self.assertNotIn(term, src, msg=f"unexpected payment module: {term}")

    def test_no_filesystem_write_call(self):
        src = self._read_source()
        for forbidden in (".write(", "os.system", "shutil.", "pathlib.Path"):
            self.assertNotIn(forbidden, src, msg=f"forbidden op: {forbidden}")
        open_calls = sum(1 for line in src.splitlines() if "open(" in line)
        self.assertEqual(open_calls, 0, msg=f"unexpected open() calls: {open_calls}")

    def test_no_weslr_state_writes(self):
        src = self._read_source()
        # The helper must NEVER write to the production future-storage path.
        self.assertNotIn("/home/pr0/weslr_state/", src)


if __name__ == "__main__":
    unittest.main()