"""
WESLR chat.weslr.de Slice 6 — Account Status Helper Tests V1

Standalone tests for the account-status state/transition helper.
Pure-Python, no I/O, no protected-file imports, no provider/model
calls, no network, no subprocess, no payment provider.

Run:
  python3 -m unittest weslr.tests.test_account_status_v1 -v
"""

from __future__ import annotations

import unittest

from weslr.account_status import (
    ACCOUNT_STATUS_HELPER_VERSION,
    VALID_ACCOUNT_STATUSES_V1,
    TERMINAL_STATUSES_V1,
    RESTRICTED_TERMINAL_LIKE_STATUSES_V1,
    ALLOWED_TRANSITIONS_V1,
    CHAT_ENABLED_STATUSES_V1,
    ACCOUNT_STATUS_NEVER_INCLUDES,
    REASON_OK,
    REASON_INVALID_NOT_DICT,
    REASON_INVALID_REQUEST_NOT_DICT,
    REASON_INVALID_BAD_STATUS,
    REASON_INVALID_BAD_TRANSITION,
    REASON_INVALID_BAD_VERSION,
    REASON_INVALID_EMPTY_ACCOUNT_ID,
    REASON_INVALID_SAME_STATUS,
    REASON_INVALID_TERMINAL_TRANSITION,
    REASON_INVALID_RESTRICTED_TRANSITION,
    REASON_INVALID_FORBIDDEN_KEY,
    build_account_status_record_v1,
    validate_account_status_record_v1,
    build_account_status_transition_request_v1,
    validate_account_status_transition_request_v1,
    apply_account_status_transition_v1,
    is_account_status_chat_enabled_v1,
    summarize_account_status_record_v1,
    to_account_status_json_safe_v1,
)


def _make_record(
    account_id="pilot_1",
    account_status="pilot_active",
    record_id="rec-1",
    status_updated_at="2026-06-23T20:00:00Z",
    status_updated_by="operator_alice",
    status_reason_label="invite",
    previous_account_status="",
    pii_visible_to_operator=False,
):
    return build_account_status_record_v1(
        account_id=account_id,
        account_status=account_status,
        account_status_record_id=record_id,
        status_updated_at=status_updated_at,
        status_updated_by=status_updated_by,
        status_reason_label=status_reason_label,
        previous_account_status=previous_account_status,
        account_status_pii_visible_to_operator=pii_visible_to_operator,
    )


def _make_request(
    account_id="pilot_1",
    from_status="pilot_active",
    to_status="pilot_paused",
    requested_by="operator_alice",
    reason_label="manual_pause",
    request_id="req-1",
    requested_at="2026-06-23T20:01:00Z",
    operator_approved=False,
):
    return build_account_status_transition_request_v1(
        account_id=account_id,
        from_status=from_status,
        to_status=to_status,
        transition_request_id=request_id,
        requested_at=requested_at,
        requested_by=requested_by,
        reason_label=reason_label,
        operator_approved=operator_approved,
    )


class TestBuildRecord(unittest.TestCase):
    def test_builds_valid_account_status_record(self):
        # Coverage item 1
        r = _make_record()
        self.assertEqual(r["account_status_helper_version"], ACCOUNT_STATUS_HELPER_VERSION)
        self.assertEqual(r["account_id"], "pilot_1")
        self.assertEqual(r["account_status"], "pilot_active")
        self.assertIn("previous_account_status", r)
        self.assertIn("status_updated_at", r)
        self.assertIn("status_updated_by", r)
        self.assertIn("status_reason_label", r)
        self.assertIn("status_transition_ref", r)
        self.assertIn("audit_log_ref", r)
        self.assertFalse(r["raw_content_retained"])
        self.assertIn("reason_labels", r)

    def test_record_id_auto_uuid(self):
        r = build_account_status_record_v1(account_id="x", account_status="invited")
        self.assertEqual(len(r["account_status_record_id"]), 36)

    def test_raw_content_retained_always_false(self):
        r = _make_record()
        self.assertFalse(r["raw_content_retained"])

    def test_required_record_fields_present(self):
        r = _make_record()
        for key in (
            "account_status_helper_version", "account_status_record_id",
            "account_status_version", "account_id", "account_status",
            "previous_account_status", "status_updated_at", "status_updated_by",
            "status_reason_label", "status_transition_ref", "audit_log_ref",
            "account_status_invited_at", "account_status_last_active_at",
            "account_status_pii_visible_to_operator",
            "account_status_red_zone_acknowledged_at",
            "reason_labels", "raw_content_retained",
        ):
            self.assertIn(key, r, msg=f"missing field: {key}")


class TestValidateRecord(unittest.TestCase):
    def test_valid_record_passes(self):
        r = _make_record()
        ok, errs = validate_account_status_record_v1(r)
        self.assertTrue(ok, msg=f"errors: {errs}")

    def test_validates_required_record_fields(self):
        # Coverage item 2
        r = _make_record()
        del r["account_id"]
        ok, errs = validate_account_status_record_v1(r)
        self.assertFalse(ok)

    def test_rejects_non_dict_record(self):
        # Coverage item 3
        ok, errs = validate_account_status_record_v1("not-a-dict")
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_NOT_DICT, errs)

    def test_rejects_missing_account_id(self):
        # Coverage item 4
        r = _make_record()
        del r["account_id"]
        ok, errs = validate_account_status_record_v1(r)
        self.assertFalse(ok)

    def test_rejects_unknown_account_status(self):
        # Coverage item 5
        r = _make_record(account_status="not_a_real_status")
        ok, errs = validate_account_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_STATUS in e for e in errs))

    def test_rejects_raw_content_retained_true(self):
        # Coverage item 6
        r = _make_record()
        r["raw_content_retained"] = True
        ok, errs = validate_account_status_record_v1(r)
        self.assertFalse(ok)
        self.assertIn("raw_content_retained_must_be_false", errs)

    def test_invalid_version_rejected(self):
        r = _make_record()
        r["account_status_version"] = "weslr-account-status-helper-v999"
        ok, errs = validate_account_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_VERSION in e for e in errs))


class TestBuildRequest(unittest.TestCase):
    def test_builds_transition_request(self):
        # Coverage item 7
        r = _make_request()
        self.assertIn("transition_request_id", r)
        self.assertEqual(r["account_id"], "pilot_1")
        self.assertEqual(r["from_status"], "pilot_active")
        self.assertEqual(r["to_status"], "pilot_paused")
        self.assertIn("requested_by", r)
        self.assertIn("requested_at", r)
        self.assertIn("reason_label", r)
        self.assertIn("operator_approved", r)
        self.assertIn("audit_log_ref", r)
        self.assertFalse(r["raw_content_retained"])

    def test_request_id_auto_uuid(self):
        r = build_account_status_transition_request_v1(
            account_id="x", from_status="invited", to_status="pilot_active",
        )
        self.assertEqual(len(r["transition_request_id"]), 36)


class TestValidateRequest(unittest.TestCase):
    def test_validates_transition_request_fields(self):
        # Coverage item 8
        ok, errs = validate_account_status_transition_request_v1(_make_request())
        self.assertTrue(ok, msg=f"errors: {errs}")

    def test_rejects_non_dict_request(self):
        ok, errs = validate_account_status_transition_request_v1("not-a-dict")
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_REQUEST_NOT_DICT, errs)

    def test_rejects_empty_account_id(self):
        r = _make_request(account_id="")
        ok, errs = validate_account_status_transition_request_v1(r)
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_EMPTY_ACCOUNT_ID, errs)

    def test_invalid_from_status_rejected(self):
        r = _make_request(from_status="not_a_real_status")
        ok, errs = validate_account_status_transition_request_v1(r)
        self.assertFalse(ok)

    def test_invalid_to_status_rejected(self):
        r = _make_request(to_status="not_a_real_status")
        ok, errs = validate_account_status_transition_request_v1(r)
        self.assertFalse(ok)


class TestApplyTransitionAllowed(unittest.TestCase):
    """Coverage item 9: accepts listed valid transitions."""

    def _apply(self, from_status, to_status, operator_approved=False):
        record = _make_record(account_status=from_status)
        request = _make_request(
            from_status=from_status, to_status=to_status,
            operator_approved=operator_approved,
        )
        return apply_account_status_transition_v1(record, request)

    def test_invited_to_pilot_free(self):
        self.assertTrue(self._apply("invited", "pilot_free")["ok"])

    def test_invited_to_pilot_active(self):
        self.assertTrue(self._apply("invited", "pilot_active")["ok"])

    def test_invited_to_manual_paid(self):
        self.assertTrue(self._apply("invited", "manual_paid")["ok"])

    def test_invited_to_manual_disabled_without_operator_approval(self):
        # manual_disabled IS destructive per operator's rule
        # but is NOT a transition INTO manual_disabled — wait, it IS.
        # So it requires operator_approved=True.
        result = self._apply("invited", "manual_disabled", operator_approved=False)
        self.assertFalse(result["ok"])

    def test_invited_to_manual_disabled_with_operator_approval(self):
        result = self._apply("invited", "manual_disabled", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_invited_to_deleted_or_revoked_with_operator_approval(self):
        result = self._apply("invited", "deleted_or_revoked", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_pilot_free_to_pilot_active(self):
        self.assertTrue(self._apply("pilot_free", "pilot_active")["ok"])

    def test_pilot_free_to_pilot_paused(self):
        self.assertTrue(self._apply("pilot_free", "pilot_paused")["ok"])

    def test_pilot_free_to_pilot_expired(self):
        self.assertTrue(self._apply("pilot_free", "pilot_expired")["ok"])

    def test_pilot_free_to_manual_paid(self):
        self.assertTrue(self._apply("pilot_free", "manual_paid")["ok"])

    def test_pilot_free_to_manual_unpaid(self):
        self.assertTrue(self._apply("pilot_free", "manual_unpaid")["ok"])

    def test_pilot_free_to_banned_with_operator_approval(self):
        # banned is destructive; requires operator_approved
        result = self._apply("pilot_free", "banned", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_pilot_active_to_pilot_paused(self):
        self.assertTrue(self._apply("pilot_active", "pilot_paused")["ok"])

    def test_pilot_active_to_pilot_expired(self):
        self.assertTrue(self._apply("pilot_active", "pilot_expired")["ok"])

    def test_pilot_active_to_manual_disabled_with_operator_approval(self):
        result = self._apply("pilot_active", "manual_disabled", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_pilot_active_to_banned_with_operator_approval(self):
        result = self._apply("pilot_active", "banned", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_pilot_paused_to_pilot_active(self):
        self.assertTrue(self._apply("pilot_paused", "pilot_active")["ok"])

    def test_pilot_paused_to_pilot_expired(self):
        self.assertTrue(self._apply("pilot_paused", "pilot_expired")["ok"])

    def test_pilot_paused_to_manual_disabled_with_operator_approval(self):
        result = self._apply("pilot_paused", "manual_disabled", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_pilot_expired_to_pilot_active(self):
        self.assertTrue(self._apply("pilot_expired", "pilot_active")["ok"])

    def test_pilot_expired_to_manual_paid(self):
        self.assertTrue(self._apply("pilot_expired", "manual_paid")["ok"])

    def test_manual_paid_to_manual_unpaid(self):
        self.assertTrue(self._apply("manual_paid", "manual_unpaid")["ok"])

    def test_manual_unpaid_to_manual_paid(self):
        self.assertTrue(self._apply("manual_unpaid", "manual_paid")["ok"])

    def test_manual_paid_to_manual_disabled_with_operator_approval(self):
        result = self._apply("manual_paid", "manual_disabled", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_manual_paid_to_banned_with_operator_approval(self):
        result = self._apply("manual_paid", "banned", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_manual_unpaid_to_banned_with_operator_approval(self):
        result = self._apply("manual_unpaid", "banned", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_banned_to_deletion_requested_with_operator_approval(self):
        result = self._apply("banned", "deletion_requested", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_banned_to_deleted_or_revoked_with_operator_approval(self):
        result = self._apply("banned", "deleted_or_revoked", operator_approved=True)
        self.assertTrue(result["ok"])

    def test_deletion_requested_to_deleted_or_revoked_with_operator_approval(self):
        result = self._apply("deletion_requested", "deleted_or_revoked", operator_approved=True)
        self.assertTrue(result["ok"])


class TestApplyTransitionDenied(unittest.TestCase):
    """Coverage item 10: rejects invalid transitions."""

    def _apply(self, from_status, to_status, operator_approved=False):
        record = _make_record(account_status=from_status)
        request = _make_request(
            from_status=from_status, to_status=to_status,
            operator_approved=operator_approved,
        )
        return apply_account_status_transition_v1(record, request)

    def test_unknown_transition_rejected(self):
        result = self._apply("invited", "pilot_paused")
        self.assertFalse(result["ok"])
        self.assertTrue(any(REASON_INVALID_BAD_TRANSITION in e for e in result["reason_labels"]))

    def test_same_status_rejected(self):
        result = self._apply("pilot_active", "pilot_active")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_SAME_STATUS, result["reason_labels"])

    def test_terminal_deleted_or_revoked_cannot_transition(self):
        # Coverage item 11
        result = self._apply("deleted_or_revoked", "pilot_active", operator_approved=True)
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_TERMINAL_TRANSITION, result["reason_labels"])

    def test_banned_only_transitions_to_deletion_states(self):
        # Coverage item 12
        result = self._apply("banned", "pilot_active", operator_approved=True)
        self.assertFalse(result["ok"])
        # Could be bad_transition or restricted — both should be in the
        # negative path
        self.assertTrue(any(
            REASON_INVALID_BAD_TRANSITION in e
            or REASON_INVALID_RESTRICTED_TRANSITION in e
            for e in result["reason_labels"]
        ))

    def test_banned_to_manual_paid_rejected(self):
        result = self._apply("banned", "manual_paid", operator_approved=True)
        self.assertFalse(result["ok"])

    def test_deletion_requested_only_transitions_to_deleted(self):
        # Coverage item 13
        result = self._apply("deletion_requested", "pilot_active", operator_approved=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any(
            REASON_INVALID_BAD_TRANSITION in e
            or REASON_INVALID_RESTRICTED_TRANSITION in e
            for e in result["reason_labels"]
        ))

    def test_destructive_transition_requires_operator_approval(self):
        # Coverage item 14
        # banned is a destructive target; without operator_approved, deny
        result = self._apply("pilot_active", "banned", operator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("destructive_transition_requires_operator_approval", result["reason_labels"])

    def test_destructive_transition_to_deletion_requested_without_approval(self):
        result = self._apply("pilot_active", "deletion_requested", operator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("destructive_transition_requires_operator_approval", result["reason_labels"])

    def test_destructive_transition_to_deleted_or_revoked_without_approval(self):
        result = self._apply("banned", "deleted_or_revoked", operator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("destructive_transition_requires_operator_approval", result["reason_labels"])

    def test_destructive_transition_to_manual_disabled_without_approval(self):
        result = self._apply("manual_paid", "manual_disabled", operator_approved=False)
        self.assertFalse(result["ok"])
        self.assertIn("destructive_transition_requires_operator_approval", result["reason_labels"])


class TestApplyTransitionValidation(unittest.TestCase):
    """Coverage item 15: apply transition updates status and previous status."""

    def test_new_record_carries_updated_status_and_previous(self):
        record = _make_record(account_status="pilot_active")
        request = _make_request(
            from_status="pilot_active", to_status="pilot_paused",
            operator_approved=False,
        )
        result = apply_account_status_transition_v1(record, request)
        self.assertTrue(result["ok"])
        new = result["new_record"]
        self.assertIsNotNone(new)
        self.assertEqual(new["account_status"], "pilot_paused")
        self.assertEqual(new["previous_account_status"], "pilot_active")
        # Original record NOT mutated (defensive copy)
        self.assertEqual(record["account_status"], "pilot_active")
        self.assertEqual(record["previous_account_status"], "")

    def test_new_record_carries_transition_metadata(self):
        record = _make_record(account_status="pilot_active")
        request = _make_request(
            from_status="pilot_active", to_status="pilot_paused",
            requested_by="operator_bob",
            reason_label="policy_violation",
        )
        result = apply_account_status_transition_v1(record, request)
        self.assertTrue(result["ok"])
        new = result["new_record"]
        self.assertEqual(new["status_updated_by"], "operator_bob")
        self.assertEqual(new["status_reason_label"], "policy_violation")
        self.assertIn("policy_violation", new["reason_labels"])

    def test_rejects_account_id_mismatch(self):
        # Coverage item "rejects account_id mismatch"
        record = _make_record(account_id="alice")
        request = _make_request(
            account_id="bob", from_status="pilot_active", to_status="pilot_paused",
        )
        result = apply_account_status_transition_v1(record, request)
        self.assertFalse(result["ok"])
        self.assertIn("account_id_mismatch", result["reason_labels"])

    def test_suggested_audit_metadata_returned_on_success(self):
        # Coverage item: apply transition returns suggested audit metadata but
        # performs no audit write.
        record = _make_record(account_status="pilot_active")
        request = _make_request(from_status="pilot_active", to_status="pilot_paused")
        result = apply_account_status_transition_v1(record, request)
        self.assertTrue(result["ok"])
        audit = result["suggested_audit_metadata"]
        self.assertIsNotNone(audit)
        self.assertEqual(audit["audit_action_type"], "user_status_changed")
        self.assertEqual(audit["audit_target_account_id"], "pilot_1")
        self.assertEqual(audit["audit_before_state"]["account_status"], "pilot_active")
        self.assertEqual(audit["audit_after_state"]["account_status"], "pilot_paused")

    def test_no_audit_file_written(self):
        # The helper does NOT write to any audit log. The audit_log
        # persistence helper (Slice 4B) is a separate module; this
        # helper only RETURNS suggested metadata.
        record = _make_record(account_status="pilot_active")
        request = _make_request(from_status="pilot_active", to_status="pilot_paused")
        apply_account_status_transition_v1(record, request)
        # Verify no audit files were created.
        import os
        for forbidden in ("/home/pr0/weslr_state/", "/tmp/weslr_audit"):
            self.assertFalse(os.path.exists(forbidden))


class TestIsChatEnabled(unittest.TestCase):
    """Coverage items 16, 17: chat enabled/disabled behavior."""

    def test_chat_enabled_for_usable_active_statuses(self):
        # Coverage item 16: chat enabled only for usable active statuses
        for status in ("pilot_free", "pilot_active", "manual_paid", "manual_unpaid"):
            r = _make_record(account_status=status)
            result = is_account_status_chat_enabled_v1(r)
            self.assertTrue(result["ok"], msg=status)
            self.assertTrue(result["chat_enabled"], msg=f"{status} should be chat_enabled")

    def test_chat_disabled_for_paused(self):
        # Coverage item 17
        r = _make_record(account_status="pilot_paused")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_expired(self):
        r = _make_record(account_status="pilot_expired")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_unpaid(self):
        # manual_unpaid has its own chat logic in Slice 5;
        # at the account-status level, manual_unpaid is in CHAT_ENABLED
        # (the entitlement packet handles subscription-level gating).
        # However, per the operator's strict spec, chat is disabled for
        # 'unpaid' (manual_unpaid). Verify accordingly.
        r = _make_record(account_status="manual_unpaid")
        result = is_account_status_chat_enabled_v1(r)
        # Per the strict operator spec, unpaid should be chat-disabled.
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_disabled(self):
        r = _make_record(account_status="manual_disabled")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_banned(self):
        r = _make_record(account_status="banned")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_deletion_requested(self):
        r = _make_record(account_status="deletion_requested")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_deleted_or_revoked(self):
        r = _make_record(account_status="deleted_or_revoked")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_chat_disabled_for_invited(self):
        r = _make_record(account_status="invited")
        result = is_account_status_chat_enabled_v1(r)
        self.assertFalse(result["chat_enabled"])

    def test_non_dict_query_denied(self):
        result = is_account_status_chat_enabled_v1("not-a-dict")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_NOT_DICT, result["reason_labels"])


class TestSummaryAndSerialization(unittest.TestCase):
    """Coverage items 18-20: summary + JSON-safe + cycle handling."""

    def test_summary_contains_no_raw_private_payment_keys(self):
        # Coverage item 18
        r = _make_record(
            account_id="pilot_42", account_status="pilot_active",
            status_updated_by="operator_alice",
        )
        # Inject forbidden keys
        r["raw_prompt"] = "SENSITIVE_PROMPT"
        r["password"] = "PWD"
        r["payment_card"] = "4111111111111111"
        s = summarize_account_status_record_v1(r)
        for forbidden in ("SENSITIVE_PROMPT", "PWD", "4111111111111111",
                          "raw_prompt", "password", "payment_card"):
            self.assertNotIn(forbidden, s, msg=f"summary leaked: {forbidden}")

    def test_json_safe_redacts_all_16_forbidden_keys(self):
        # Coverage item 19
        r = _make_record()
        # Inject all 16 forbidden keys at various depths.
        r["raw_prompt"] = "SENSITIVE_PROMPT"
        r["raw_reply"] = "SENSITIVE_REPLY"
        r["credentials"] = "SENSITIVE_CRED"
        r["session_token_plaintext"] = "SENSITIVE_TOK"
        r["hidden_prompt"] = "SENSITIVE_HIDDEN"
        r["system_prompt"] = "SENSITIVE_SYS"
        r["chain_of_thought"] = "TRACE"
        r["provider_response"] = "PROV"
        r["shadow_call_output"] = "SHADOW"
        r["password"] = "PWD"
        r["secret"] = "SEC"
        r["api_key"] = "KEY"
        r["payment_card"] = "4111111111111111"
        r["card_number"] = "4111111111111111"
        r["iban"] = "DE89370400440532013000"
        r["bank_account"] = "DE89370400440532013000"
        r["reason_labels"].append({"api_key": "NESTED"})
        s = to_account_status_json_safe_v1(r)
        for forbidden in ("SENSITIVE_PROMPT", "SENSITIVE_REPLY", "SENSITIVE_CRED",
                          "SENSITIVE_TOK", "SENSITIVE_HIDDEN", "SENSITIVE_SYS",
                          "TRACE", "PROV", "SHADOW", "PWD", "SEC", "KEY",
                          "4111111111111111", "DE89370400440532013000", "NESTED"):
            self.assertNotIn(forbidden, s, msg=f"forbidden value leaked: {forbidden}")
        for key in ("raw_prompt", "raw_reply", "credentials",
                    "session_token_plaintext", "hidden_prompt", "system_prompt",
                    "chain_of_thought", "provider_response", "shadow_call_output",
                    "password", "secret", "api_key",
                    "payment_card", "card_number", "iban", "bank_account"):
            self.assertNotIn(f'"{key}"', s, msg=f"forbidden key name leaked: {key}")

    def test_cycle_handling_in_json_safe(self):
        # Coverage item 20
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_account_status_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertTrue("<cyclic>" in s or "serialization_error" in s)

    def test_summary_for_valid_record(self):
        r = _make_record(account_id="pilot_42", account_status="pilot_active")
        s = summarize_account_status_record_v1(r)
        self.assertIn("pilot_42", s)
        self.assertIn("pilot_active", s)

    def test_summary_for_invalid_record(self):
        s = summarize_account_status_record_v1("not-a-dict")
        self.assertIn("invalid_account_status_record", s)


class TestTransitionGraphConsistency(unittest.TestCase):
    """Verify the transition graph is internally consistent."""

    def test_terminal_statuses_have_no_outgoing_transitions(self):
        for status in TERMINAL_STATUSES_V1:
            self.assertEqual(ALLOWED_TRANSITIONS_V1[status], frozenset())

    def test_all_statuses_have_an_entry_in_the_graph(self):
        for status in VALID_ACCOUNT_STATUSES_V1:
            self.assertIn(status, ALLOWED_TRANSITIONS_V1)

    def test_all_outgoing_targets_are_valid_statuses(self):
        for from_status, targets in ALLOWED_TRANSITIONS_V1.items():
            for to_status in targets:
                self.assertIn(to_status, VALID_ACCOUNT_STATUSES_V1)

    def test_no_self_transitions_in_graph(self):
        for from_status, targets in ALLOWED_TRANSITIONS_V1.items():
            self.assertNotIn(from_status, targets)

    def test_banned_has_only_deletion_targets(self):
        for to_status in ALLOWED_TRANSITIONS_V1["banned"]:
            self.assertIn(to_status, {"deletion_requested", "deleted_or_revoked"})

    def test_deletion_requested_has_only_deleted_target(self):
        for to_status in ALLOWED_TRANSITIONS_V1["deletion_requested"]:
            self.assertEqual(to_status, "deleted_or_revoked")

    def test_deleted_or_revoked_is_in_terminal_set(self):
        self.assertIn("deleted_or_revoked", TERMINAL_STATUSES_V1)

    def test_banned_and_deletion_requested_are_in_restricted_set(self):
        self.assertIn("banned", RESTRICTED_TERMINAL_LIKE_STATUSES_V1)
        self.assertIn("deletion_requested", RESTRICTED_TERMINAL_LIKE_STATUSES_V1)


class TestIsPure(unittest.TestCase):
    """The account status helper does not import protected runtime
    modules or provider/model/network/subprocess modules."""

    @staticmethod
    def _read_source():
        import weslr.account_status as ac
        with open(ac.__file__, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_module_imports_only_safe_stdlib_plus_entitlement_constants(self):
        # Coverage item 21
        import weslr.account_status as ac
        import inspect
        src = inspect.getsource(ac)
        # The only allowed cross-module import is from entitlement_packet.
        self.assertIn("from weslr.entitlement_packet import _VALID_ACCOUNT_STATUSES", src)
        for forbidden in (
            "import weslr.chat_responder", "from weslr.chat_responder",
            "import weslr.dialogue", "from weslr.dialogue",
            "import weslr.chat_ui", "from weslr.chat_ui",
            "import weslr.runtime_wrapper", "from weslr.runtime_wrapper",
            "import weslr.session_manager", "from weslr.session_manager",
            "import weslr.audit_log", "from weslr.audit_log",
            "import weslr.audit_log_persistence", "from weslr.audit_log_persistence",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")

    def test_no_provider_model_network_subprocess_payment_imports(self):
        # Coverage item 22
        src = self._read_source()
        for forbidden in ("openai", "anthropic", "ollama", "transformers", "torch",
                           "urllib", "requests", "httpx", "import socket", "import aiohttp",
                           "import subprocess", "stripe", "paypal", "braintree", "square", "adyen"):
            self.assertNotIn(forbidden, src, msg=f"forbidden: {forbidden}")

    def test_no_protected_runtime_imports(self):
        # Coverage item 23
        src = self._read_source()
        for forbidden in ("chat_responder", "dialogue", "chat_ui", "session_manager",
                          "audit_log", "audit_log_persistence", "runtime_wrapper"):
            import_count = src.count(f"import weslr.{forbidden}") + src.count(f"from weslr.{forbidden}")
            self.assertEqual(import_count, 0, msg=f"unexpected import: weslr.{forbidden}")

    def test_no_filesystem_write_path(self):
        # Coverage item 24
        src = self._read_source()
        for forbidden in (".write(", "os.system", "shutil.", "pathlib.Path"):
            self.assertNotIn(forbidden, src, msg=f"forbidden op: {forbidden}")
        open_calls = sum(1 for line in src.splitlines() if "open(" in line)
        self.assertEqual(open_calls, 0, msg=f"unexpected open() calls: {open_calls}")

    def test_no_weslr_state_path(self):
        # Coverage item 25
        src = self._read_source()
        self.assertNotIn("/home/pr0/weslr_state/", src)


if __name__ == "__main__":
    unittest.main()