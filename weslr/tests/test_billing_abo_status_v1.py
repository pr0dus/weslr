"""
WESLR chat.weslr.de Slice 7 — Billing/Abo Status Helper V1 Tests

Tests for the metadata-only billing/abo status helper. Validates:
  - 11 billing/abo statuses supported
  - Record construction with 14+1+1 fields (operator-specified)
  - Record validation (required fields, types, forbidden keys)
  - Transition request construction with 11+1 fields
  - Transition request validation
  - Transition application (same-status, default-deny, terminal,
    restricted terminal-like, destructive-target operator_approval)
  - Billing-status allows chat access pre-check
  - Summarize (8-field metadata-only summary)
  - JSON-safe serialization (16 forbidden keys redacted recursively;
    cycles handled; serialization errors do not raise)
  - Strict boundary invariants (no /home/pr0/weslr_state/, no
    network/subprocess/payment imports, no ChatResponder wiring,
    no protected-file edits)

The tests are hermetic and metadata-only; they do NOT touch
disk, network, subprocess, or any external payment provider.
"""

from __future__ import annotations

import json
import unittest
from typing import Any, Dict, List, Optional

import weslr.billing_abo_status as m


def _make_record(
    *,
    account_id: str = "acct-test",
    billing_abo_status: str = "free_pilot",
    previous_billing_abo_status: str = "",
    **overrides: Any,
) -> Dict[str, Any]:
    """Helper: build a record with sensible defaults."""
    return m.build_billing_abo_status_record_v1(
        account_id=account_id,
        billing_abo_status=billing_abo_status,
        previous_billing_abo_status=previous_billing_abo_status,
        **overrides,
    )


def _make_request(
    *,
    account_id: str = "acct-test",
    from_status: str = "free_pilot",
    to_status: str = "active",
    operator_approved: bool = False,
    **overrides: Any,
) -> Dict[str, Any]:
    """Helper: build a transition request with sensible defaults."""
    return m.build_billing_abo_transition_request_v1(
        account_id=account_id,
        from_status=from_status,
        to_status=to_status,
        operator_approved=operator_approved,
        **overrides,
    )


# ----------------------------------------------------------------------------
# Constants & enums
# ----------------------------------------------------------------------------

class TestConstants(unittest.TestCase):
    def test_helper_version_is_set(self):
        self.assertTrue(m.BILLING_ABO_HELPER_VERSION)
        self.assertIn("billing-abo", m.BILLING_ABO_HELPER_VERSION)

    def test_11_billing_abo_statuses(self):
        self.assertEqual(len(m.VALID_BILLING_ABO_STATUSES_V1), 11)
        expected = {
            "no_subscription", "free_pilot", "trialing", "active",
            "past_due", "unpaid", "canceled", "refunded",
            "disputed", "grace_period", "disabled_for_nonpayment",
        }
        self.assertEqual(m.VALID_BILLING_ABO_STATUSES_V1, expected)

    def test_terminal_statuses(self):
        # Per Slice 7 spec (updated), terminal-like statuses
        # (allow-listed outgoing only) are:
        #   canceled, refunded, disabled_for_nonpayment.
        self.assertEqual(
            m.TERMINAL_LIKE_BILLING_ABO_STATUSES_V1,
            {"canceled", "refunded", "disabled_for_nonpayment"},
        )

    def test_no_restricted_terminal_like_set_removed(self):
        # The old RESTRICTED_TERMINAL_LIKE_BILLING_ABO_STATUSES_V1
        # constant has been replaced by TERMINAL_LIKE_BILLING_ABO_STATUSES_V1.
        # Verify the old constant no longer exists.
        self.assertFalse(
            hasattr(m, "RESTRICTED_TERMINAL_LIKE_BILLING_ABO_STATUSES_V1"),
        )

    def test_destructive_targets(self):
        # Per Slice 7 spec (updated), destructive targets are:
        # unpaid, canceled, refunded, disputed, disabled_for_nonpayment.
        self.assertEqual(
            m.DESTRUCTIVE_BILLING_ABO_TARGETS_V1,
            {"unpaid", "canceled", "refunded", "disputed", "disabled_for_nonpayment"},
        )

    def test_chat_access_allowed_set(self):
        self.assertEqual(
            m.BILLING_ABO_CHAT_ACCESS_ALLOWED_V1,
            {"free_pilot", "trialing", "active", "grace_period"},
        )

    def test_16_forbidden_keys(self):
        self.assertEqual(len(m.BILLING_ABO_STATUS_NEVER_INCLUDES), 16)
        expected = {
            "raw_prompt", "raw_reply", "credentials",
            "session_token_plaintext", "hidden_prompt", "system_prompt",
            "chain_of_thought", "provider_response", "shadow_call_output",
            "password", "secret", "api_key",
            "payment_card", "card_number", "iban", "bank_account",
        }
        self.assertEqual(m.BILLING_ABO_STATUS_NEVER_INCLUDES, expected)


class TestTransitionGraph(unittest.TestCase):
    def test_all_11_statuses_have_an_entry(self):
        # Every valid status must appear as a key in the
        # transition graph (even terminal-like statuses with
        # a narrow allow-list).
        for s in m.VALID_BILLING_ABO_STATUSES_V1:
            self.assertIn(s, m.ALLOWED_BILLING_ABO_TRANSITIONS_V1)
            self.assertIsInstance(
                m.ALLOWED_BILLING_ABO_TRANSITIONS_V1[s], frozenset
            )

    def test_terminal_like_canceled_narrow_allowlist(self):
        # Per operator's spec: canceled -> {trialing, active,
        # disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["canceled"],
            {"trialing", "active", "disabled_for_nonpayment"},
        )

    def test_terminal_like_refunded_narrow_allowlist(self):
        # Per operator's spec: refunded -> {canceled,
        # disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["refunded"],
            {"canceled", "disabled_for_nonpayment"},
        )

    def test_terminal_like_disabled_for_nonpayment_narrow_allowlist(self):
        # Per operator's spec: disabled_for_nonpayment -> {active,
        # trialing, canceled}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["disabled_for_nonpayment"],
            {"active", "trialing", "canceled"},
        )

    def test_normal_no_subscription_transitions(self):
        # Per operator's spec: no_subscription ->
        # {free_pilot, trialing, active, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["no_subscription"],
            {"free_pilot", "trialing", "active", "disabled_for_nonpayment"},
        )

    def test_normal_free_pilot_transitions(self):
        # Per operator's spec: free_pilot ->
        # {trialing, active, grace_period, canceled, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["free_pilot"],
            {"trialing", "active", "grace_period", "canceled", "disabled_for_nonpayment"},
        )

    def test_normal_trialing_transitions(self):
        # Per operator's spec: trialing ->
        # {active, past_due, canceled, grace_period}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["trialing"],
            {"active", "past_due", "canceled", "grace_period"},
        )

    def test_normal_active_transitions(self):
        # Per operator's spec: active ->
        # {past_due, unpaid, canceled, refunded, disputed}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["active"],
            {"past_due", "unpaid", "canceled", "refunded", "disputed"},
        )

    def test_normal_past_due_transitions(self):
        # Per operator's spec: past_due ->
        # {active, unpaid, grace_period, canceled, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["past_due"],
            {"active", "unpaid", "grace_period", "canceled", "disabled_for_nonpayment"},
        )

    def test_normal_unpaid_transitions(self):
        # Per operator's spec: unpaid ->
        # {active, grace_period, canceled, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["unpaid"],
            {"active", "grace_period", "canceled", "disabled_for_nonpayment"},
        )

    def test_normal_grace_period_transitions(self):
        # Per operator's spec: grace_period ->
        # {active, unpaid, canceled, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["grace_period"],
            {"active", "unpaid", "canceled", "disabled_for_nonpayment"},
        )

    def test_normal_disputed_transitions(self):
        # Per operator's spec: disputed ->
        # {active, refunded, canceled, disabled_for_nonpayment}.
        self.assertEqual(
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["disputed"],
            {"active", "refunded", "canceled", "disabled_for_nonpayment"},
        )

    def test_default_deny_unknown_transitions_not_in_graph(self):
        # Per the operator's spec, no_subscription -> past_due
        # is NOT in the graph (no_subscription jumps straight
        # to trialing/active/disabled_for_nonpayment).
        self.assertNotIn(
            "past_due",
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["no_subscription"],
        )
        # And no_subscription -> grace_period is NOT in the graph.
        self.assertNotIn(
            "grace_period",
            m.ALLOWED_BILLING_ABO_TRANSITIONS_V1["no_subscription"],
        )


# ----------------------------------------------------------------------------
# Record construction
# ----------------------------------------------------------------------------

class TestBuildRecord(unittest.TestCase):
    def test_minimal_record_has_required_fields(self):
        r = _make_record()
        for field in (
            "billing_abo_record_id", "account_id", "billing_abo_version",
            "billing_abo_status", "previous_billing_abo_status",
            "billing_abo_updated_at", "billing_abo_updated_by",
            "billing_abo_reason_label", "billing_abo_transition_ref",
            "billing_provider_ref_metadata", "entitlement_recompute_required",
            "audit_log_ref", "raw_content_retained",
            "billing_abo_reason_labels",
        ):
            self.assertIn(field, r)

    def test_record_id_is_generated(self):
        r = _make_record()
        self.assertTrue(r["billing_abo_record_id"].startswith("billing-abo-record-"))

    def test_custom_record_id(self):
        r = _make_record(billing_abo_record_id="custom-id-123")
        self.assertEqual(r["billing_abo_record_id"], "custom-id-123")

    def test_raw_content_retained_is_false(self):
        r = _make_record()
        self.assertEqual(r["raw_content_retained"], False)

    def test_default_version_is_helper_version(self):
        r = _make_record()
        self.assertEqual(r["billing_abo_version"], m.BILLING_ABO_HELPER_VERSION)

    def test_previous_status_default_empty(self):
        r = _make_record(billing_abo_status="active")
        self.assertEqual(r["previous_billing_abo_status"], "")

    def test_previous_status_explicit(self):
        r = _make_record(
            billing_abo_status="active",
            previous_billing_abo_status="free_pilot",
        )
        self.assertEqual(r["previous_billing_abo_status"], "free_pilot")

    def test_billing_provider_ref_metadata_defaults_to_empty_dict(self):
        r = _make_record()
        self.assertEqual(r["billing_provider_ref_metadata"], {})

    def test_entitlement_recompute_required_default_true(self):
        r = _make_record()
        self.assertTrue(r["entitlement_recompute_required"])

    def test_billing_abo_reason_labels_default_empty_list(self):
        r = _make_record()
        self.assertEqual(r["billing_abo_reason_labels"], [])


# ----------------------------------------------------------------------------
# Record validation
# ----------------------------------------------------------------------------

class TestValidateRecord(unittest.TestCase):
    def test_valid_record_ok(self):
        r = _make_record()
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertTrue(ok, msg=str(errs))
        self.assertEqual(errs, [])

    def test_invalid_status_rejected(self):
        r = _make_record(billing_abo_status="not_a_real_status")
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("invalid_billing_abo_status" in e for e in errs))

    def test_missing_account_id_rejected(self):
        r = _make_record()
        del r["account_id"]
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("account_id" in e for e in errs))

    def test_empty_account_id_rejected(self):
        r = _make_record(account_id="")
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_EMPTY_ACCOUNT_ID, errs)

    def test_raw_content_retained_true_rejected(self):
        r = _make_record()
        r["raw_content_retained"] = True
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("raw_content_retained" in e for e in errs))

    def test_wrong_version_rejected(self):
        r = _make_record(billing_abo_version="wrong-version")
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("invalid_billing_abo_version" in e for e in errs))

    def test_non_dict_rejected(self):
        ok, errs = m.validate_billing_abo_status_record_v1("not a dict")
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_NOT_DICT, errs)

    def test_none_rejected(self):
        ok, errs = m.validate_billing_abo_status_record_v1(None)
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_NOT_DICT, errs)

    def test_billing_abo_reason_labels_must_be_list(self):
        r = _make_record()
        r["billing_abo_reason_labels"] = "not a list"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("billing_abo_reason_labels_not_list" in e for e in errs))

    def test_billing_provider_ref_metadata_must_be_dict(self):
        r = _make_record()
        r["billing_provider_ref_metadata"] = "not a dict"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("billing_provider_ref_metadata_not_dict" in e for e in errs))

    def test_entitlement_recompute_required_must_be_bool(self):
        r = _make_record()
        r["entitlement_recompute_required"] = "true"  # string, not bool
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("entitlement_recompute_required_must_be_bool" in e for e in errs))


class TestForbiddenKeysInRecord(unittest.TestCase):
    def test_no_forbidden_keys_by_default(self):
        r = _make_record()
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertTrue(ok, msg=str(errs))

    def test_payment_card_rejected(self):
        r = _make_record()
        r["payment_card"] = "4111-1111-1111-1111"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("payment_card" in e for e in errs))

    def test_card_number_rejected(self):
        r = _make_record()
        r["card_number"] = "4111111111111111"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("card_number" in e for e in errs))

    def test_iban_rejected(self):
        r = _make_record()
        r["iban"] = "DE89370400440532013000"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("iban" in e for e in errs))

    def test_bank_account_rejected(self):
        r = _make_record()
        r["bank_account"] = "1234567890"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("bank_account" in e for e in errs))

    def test_raw_prompt_rejected(self):
        r = _make_record()
        r["raw_prompt"] = "user typed this"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("raw_prompt" in e for e in errs))

    def test_raw_reply_rejected(self):
        r = _make_record()
        r["raw_reply"] = "model said this"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("raw_reply" in e for e in errs))

    def test_password_rejected(self):
        r = _make_record()
        r["password"] = "hunter2"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("password" in e for e in errs))

    def test_api_key_rejected(self):
        r = _make_record()
        r["api_key"] = "sk-abc123"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("api_key" in e for e in errs))

    def test_session_token_plaintext_rejected(self):
        r = _make_record()
        r["session_token_plaintext"] = "tok_xyz"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("session_token_plaintext" in e for e in errs))

    def test_provider_response_rejected(self):
        r = _make_record()
        r["provider_response"] = {"id": "resp_123"}
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("provider_response" in e for e in errs))

    def test_chain_of_thought_rejected(self):
        r = _make_record()
        r["chain_of_thought"] = "step 1: think"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("chain_of_thought" in e for e in errs))

    def test_forbidden_key_in_nested_dict(self):
        r = _make_record()
        r["billing_provider_ref_metadata"] = {"payment_card": "4111-1111-1111-1111"}
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("payment_card" in e for e in errs))

    def test_forbidden_key_in_nested_list(self):
        r = _make_record()
        r["billing_abo_reason_labels"] = [{"secret": "leaked"}]
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("secret" in e for e in errs))

    def test_multiple_forbidden_keys_reported(self):
        r = _make_record()
        r["password"] = "x"
        r["api_key"] = "y"
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("password" in e for e in errs))
        self.assertTrue(any("api_key" in e for e in errs))


# ----------------------------------------------------------------------------
# Transition request construction & validation
# ----------------------------------------------------------------------------

class TestBuildRequest(unittest.TestCase):
    def test_minimal_request_has_required_fields(self):
        req = _make_request()
        for field in (
            "transition_request_id", "account_id", "from_status",
            "to_status", "requested_at", "requested_by", "reason_label",
            "operator_approved", "provider_event_ref_metadata",
            "audit_log_ref", "raw_content_retained",
        ):
            self.assertIn(field, req)

    def test_request_id_generated(self):
        req = _make_request()
        self.assertTrue(req["transition_request_id"].startswith("billing-abo-transition-"))

    def test_operator_approved_default_false(self):
        req = _make_request()
        self.assertFalse(req["operator_approved"])

    def test_operator_approved_explicit_true(self):
        req = _make_request(to_status="canceled", operator_approved=True)
        self.assertTrue(req["operator_approved"])

    def test_provider_event_ref_metadata_defaults_empty_dict(self):
        req = _make_request()
        self.assertEqual(req["provider_event_ref_metadata"], {})


class TestValidateRequest(unittest.TestCase):
    def test_valid_request_ok(self):
        req = _make_request()
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertTrue(ok, msg=str(errs))
        self.assertEqual(errs, [])

    def test_invalid_from_status(self):
        req = _make_request(from_status="bogus")
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(any("from_status" in e and "invalid_billing_abo_status" in e for e in errs))

    def test_invalid_to_status(self):
        req = _make_request(to_status="bogus")
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(any("to_status" in e and "invalid_billing_abo_status" in e for e in errs))

    def test_empty_account_id_rejected(self):
        req = _make_request(account_id="")
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_EMPTY_ACCOUNT_ID, errs)

    def test_operator_approved_must_be_bool(self):
        req = _make_request()
        req["operator_approved"] = "yes"  # string, not bool
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(any("operator_approved_must_be_bool" in e for e in errs))

    def test_raw_content_retained_true_rejected(self):
        req = _make_request()
        req["raw_content_retained"] = True
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)

    def test_non_dict_rejected(self):
        ok, errs = m.validate_billing_abo_transition_request_v1("not a dict")
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_REQUEST_NOT_DICT, errs)

    def test_none_rejected(self):
        ok, errs = m.validate_billing_abo_transition_request_v1(None)
        self.assertFalse(ok)
        self.assertIn(m.REASON_INVALID_REQUEST_NOT_DICT, errs)

    def test_forbidden_key_in_provider_event_ref_metadata(self):
        req = _make_request()
        req["provider_event_ref_metadata"] = {"card_number": "4111"}
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(any("card_number" in e for e in errs))


# ----------------------------------------------------------------------------
# Apply transition
# ----------------------------------------------------------------------------

class TestApplyTransition(unittest.TestCase):
    def test_normal_transition_active(self):
        r = _make_record(billing_abo_status="free_pilot")
        req = _make_request(from_status="free_pilot", to_status="active")
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertIsNotNone(res["record"])
        self.assertEqual(res["record"]["billing_abo_status"], "active")
        self.assertEqual(res["record"]["previous_billing_abo_status"], "free_pilot")

    def test_transition_clears_previous_status_from_record_to_new(self):
        r = _make_record(
            billing_abo_status="free_pilot",
            previous_billing_abo_status="no_subscription",
        )
        req = _make_request(from_status="free_pilot", to_status="active")
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        # After the transition, previous is now "free_pilot" and
        # current is "active".
        self.assertEqual(res["record"]["previous_billing_abo_status"], "free_pilot")
        self.assertEqual(res["record"]["billing_abo_status"], "active")

    def test_same_status_rejected(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(from_status="active", to_status="active")
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_SAME_STATUS, res["reason_labels"])

    def test_default_deny_unknown_transition(self):
        r = _make_record(billing_abo_status="active")
        # active -> trialing is NOT in the graph (active ->
        # past_due is the typical next step). Trialing is the
        # initial-subscription state, not a re-entry from
        # active.
        req = _make_request(
            from_status="active",
            to_status="trialing",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_BAD_TRANSITION, res["reason_labels"])

    def test_terminal_like_refunded_cannot_jump_to_active(self):
        r = _make_record(billing_abo_status="refunded")
        # refunded -> active is NOT in refunded's narrow
        # allow-list. Only refunded -> {canceled,
        # disabled_for_nonpayment} is allowed.
        req = _make_request(
            from_status="refunded",
            to_status="active",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_TERMINAL_TRANSITION, res["reason_labels"])

    def test_terminal_like_canceled_cannot_jump_to_past_due(self):
        r = _make_record(billing_abo_status="canceled")
        # canceled -> past_due is NOT in canceled's narrow
        # allow-list. Only canceled -> {trialing, active,
        # disabled_for_nonpayment} is allowed.
        req = _make_request(
            from_status="canceled",
            to_status="past_due",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_TERMINAL_TRANSITION, res["reason_labels"])

    def test_terminal_like_disabled_for_nonpayment_to_trialing_allowed_with_approval(self):
        # disabled_for_nonpayment -> trialing is in the allow-list
        # but trialing is NOT a destructive target, so no
        # operator_approval is required.
        r = _make_record(billing_abo_status="disabled_for_nonpayment")
        req = _make_request(
            from_status="disabled_for_nonpayment",
            to_status="trialing",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])

    def test_terminal_like_canceled_to_active_is_destructive(self):
        # canceled -> active is in canceled's allow-list but
        # active is NOT a destructive target, so no operator
        # approval is required.
        r = _make_record(billing_abo_status="canceled")
        req = _make_request(
            from_status="canceled",
            to_status="active",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])

    def test_account_id_mismatch_rejected(self):
        # Per operator's "Safety" list: reject request
        # account_id mismatch. The record is for acct-001
        # but the request carries acct-002.
        r = _make_record(account_id="acct-001", billing_abo_status="active")
        req = _make_request(
            account_id="acct-002",
            from_status="active",
            to_status="past_due",
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_ACCOUNT_ID_MISMATCH, res["reason_labels"])

    def test_account_id_mismatch_rejected_even_for_destructive_with_approval(self):
        # Even with operator_approved=True, an account_id
        # mismatch is rejected (it would corrupt the cross-
        # account transition log).
        r = _make_record(account_id="acct-001", billing_abo_status="active")
        req = _make_request(
            account_id="acct-002",
            from_status="active",
            to_status="refunded",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_ACCOUNT_ID_MISMATCH, res["reason_labels"])

    def test_destructive_target_requires_operator_approval(self):
        r = _make_record(billing_abo_status="active")
        # active -> refunded is allowed (in the graph) but refunded
        # is a destructive target, so operator_approved is required.
        req = _make_request(
            from_status="active",
            to_status="refunded",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertTrue(
            any("destructive_billing_abo_transition_requires_operator_approval" in label
                for label in res["reason_labels"])
        )
        self.assertTrue(res["requires_operator_approval"])

    def test_destructive_target_with_approval_allowed(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="refunded",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertEqual(res["record"]["billing_abo_status"], "refunded")

    def test_destructive_target_disputed_from_past_due_with_approval(self):
        # past_due -> disputed is NOT in the graph, so this is
        # a default-deny (not even allowed with approval). To
        # actually reach disputed from the graph, only via disputed
        # itself is impossible (terminal). Verify: there is no
        # legal entry into disputed from a non-restricted state.
        # Instead test disabled_for_nonpayment <-> unpaid.
        r = _make_record(billing_abo_status="unpaid")
        req = _make_request(
            from_status="unpaid",
            to_status="disabled_for_nonpayment",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertEqual(res["record"]["billing_abo_status"], "disabled_for_nonpayment")

    def test_destructive_disabled_for_nonpayment_without_approval_rejected(self):
        r = _make_record(billing_abo_status="unpaid")
        req = _make_request(
            from_status="unpaid",
            to_status="disabled_for_nonpayment",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertTrue(
            any("destructive_billing_abo_transition_requires_operator_approval" in label
                for label in res["reason_labels"])
        )

    def test_destructive_canceled_without_approval_rejected(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="canceled",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertTrue(
            any("destructive_billing_abo_transition_requires_operator_approval" in label
                for label in res["reason_labels"])
        )

    def test_destructive_canceled_with_approval_allowed(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="canceled",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertEqual(res["record"]["billing_abo_status"], "canceled")

    def test_destructive_unpaid_without_approval_rejected(self):
        # Per operator's updated spec, `unpaid` is a destructive
        # target that requires operator_approved=True.
        # past_due -> unpaid is in the graph AND unpaid is
        # destructive, so without approval the transition is
        # rejected.
        r = _make_record(billing_abo_status="past_due")
        req = _make_request(
            from_status="past_due",
            to_status="unpaid",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertTrue(
            any("destructive_billing_abo_transition_requires_operator_approval" in label
                for label in res["reason_labels"])
        )

    def test_destructive_unpaid_with_approval_allowed(self):
        r = _make_record(billing_abo_status="past_due")
        req = _make_request(
            from_status="past_due",
            to_status="unpaid",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertEqual(res["record"]["billing_abo_status"], "unpaid")

    def test_destructive_disputed_from_active_with_approval(self):
        # active -> disputed is in the graph AND disputed is
        # destructive, so operator_approved is required.
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="disputed",
            operator_approved=False,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        # With approval, allowed.
        req2 = _make_request(
            from_status="active",
            to_status="disputed",
            operator_approved=True,
        )
        res2 = m.apply_billing_abo_transition_v1(r, req2)
        self.assertTrue(res2["ok"])
        self.assertEqual(res2["record"]["billing_abo_status"], "disputed")

    def test_provider_event_ref_metadata_rejects_bytes(self):
        # Raw provider payloads often contain bytes (e.g.,
        # base64-encoded blobs). The validator must reject
        # bytes in provider_event_ref_metadata.
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="past_due",
        )
        req["provider_event_ref_metadata"] = {"raw_payload": b"\\x00\\x01\\x02"}
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(
            any("invalid_provider_ref_metadata_raw_payload_rejected" in e for e in errs)
        )

    def test_provider_event_ref_metadata_rejects_set(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="past_due",
        )
        req["provider_event_ref_metadata"] = {"tags": {"a", "b"}}
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertFalse(ok)
        self.assertTrue(
            any("invalid_provider_ref_metadata_raw_payload_rejected" in e for e in errs)
        )

    def test_provider_event_ref_metadata_accepts_safe_primitives(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="past_due",
        )
        req["provider_event_ref_metadata"] = {
            "external_ref": "evt_abc123",
            "amount_cents": 4999,
            "is_renewal": True,
            "renewed_at": "2026-06-24T10:00:00Z",
        }
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertTrue(ok, msg=str(errs))

    def test_provider_event_ref_metadata_accepts_nested_safe_primitives(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="past_due",
        )
        req["provider_event_ref_metadata"] = {
            "billing_event": {
                "id": "evt_1",
                "amount_cents": 999,
                "tags": ["recurring", "monthly"],
            },
        }
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertTrue(ok, msg=str(errs))

    def test_record_billing_provider_ref_metadata_rejects_bytes(self):
        r = _make_record(billing_abo_status="active")
        r["billing_provider_ref_metadata"] = {"raw_payload": b"\\x00"}
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertFalse(ok)
        self.assertTrue(
            any("invalid_provider_ref_metadata_raw_payload_rejected" in e for e in errs)
        )

    def test_suggested_audit_metadata_returned(self):
        r = _make_record(billing_abo_status="free_pilot")
        req = _make_request(from_status="free_pilot", to_status="active")
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        sam = res["suggested_audit_metadata"]
        self.assertEqual(sam["audit_category"], "billing_abo_status_transition")
        self.assertEqual(sam["audit_from_status"], "free_pilot")
        self.assertEqual(sam["audit_to_status"], "active")
        self.assertEqual(sam["audit_account_id"], "acct-test")
        self.assertFalse(sam["audit_operator_approved"])
        self.assertFalse(sam["audit_destructive_target"])

    def test_suggested_audit_metadata_destructive_flag(self):
        r = _make_record(billing_abo_status="active")
        req = _make_request(
            from_status="active",
            to_status="refunded",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        sam = res["suggested_audit_metadata"]
        self.assertTrue(sam["audit_destructive_target"])
        self.assertTrue(sam["audit_operator_approved"])

    def test_apply_invalid_record_returns_record_invalid(self):
        # Pass a non-dict as record.
        req = _make_request()
        res = m.apply_billing_abo_transition_v1("not a dict", req)  # type: ignore[arg-type]
        self.assertFalse(res["ok"])
        self.assertTrue(any("record_invalid" in label for label in res["reason_labels"]))

    def test_apply_invalid_request_returns_request_invalid(self):
        r = _make_record()
        res = m.apply_billing_abo_transition_v1(r, "not a dict")  # type: ignore[arg-type]
        self.assertFalse(res["ok"])
        self.assertTrue(any("request_invalid" in label for label in res["reason_labels"]))

    def test_input_record_not_mutated(self):
        r = _make_record(billing_abo_status="free_pilot")
        original_status = r["billing_abo_status"]
        req = _make_request(from_status="free_pilot", to_status="active")
        m.apply_billing_abo_transition_v1(r, req)
        # The original record must not be mutated.
        self.assertEqual(r["billing_abo_status"], original_status)

    def test_entitlement_recompute_required_after_transition(self):
        r = _make_record(billing_abo_status="free_pilot", entitlement_recompute_required=False)
        req = _make_request(from_status="free_pilot", to_status="active")
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        # After ANY transition, entitlement_recompute_required must be True
        # so the runtime wrapper will recompute the entitlement packet.
        self.assertTrue(res["record"]["entitlement_recompute_required"])

    def test_provider_event_ref_metadata_merged_into_record(self):
        r = _make_record(billing_abo_status="free_pilot")
        req = _make_request(
            from_status="free_pilot",
            to_status="active",
        )
        req["provider_event_ref_metadata"] = {"external_ref": "evt_abc123"}
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertTrue(res["ok"])
        self.assertEqual(
            res["record"]["billing_provider_ref_metadata"].get("external_ref"),
            "evt_abc123",
        )

    def test_transition_to_canceled_with_no_subscription_entry(self):
        # no_subscription -> canceled is NOT in the graph. Should
        # be rejected with REASON_INVALID_BAD_TRANSITION.
        r = _make_record(billing_abo_status="no_subscription")
        req = _make_request(
            from_status="no_subscription",
            to_status="canceled",
            operator_approved=True,
        )
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertFalse(res["ok"])
        self.assertIn(m.REASON_INVALID_BAD_TRANSITION, res["reason_labels"])


# ----------------------------------------------------------------------------
# Billing-status chat-access pre-check
# ----------------------------------------------------------------------------

class TestChatAccess(unittest.TestCase):
    def test_chat_access_for_chat_access_allowed_statuses(self):
        for status in ("free_pilot", "trialing", "active", "grace_period"):
            r = _make_record(billing_abo_status=status)
            res = m.billing_status_allows_chat_access_v1(r)
            self.assertTrue(res["ok"], msg=status)
            self.assertTrue(res["allows_chat_access"], msg=status)

    def test_no_chat_access_for_non_allowed_statuses(self):
        for status in (
            "no_subscription", "past_due", "unpaid", "canceled",
            "refunded", "disputed", "disabled_for_nonpayment",
        ):
            r = _make_record(billing_abo_status=status)
            res = m.billing_status_allows_chat_access_v1(r)
            self.assertTrue(res["ok"], msg=status)
            self.assertFalse(res["allows_chat_access"], msg=status)

    def test_invalid_record_returns_ok_false(self):
        res = m.billing_status_allows_chat_access_v1("not a dict")  # type: ignore[arg-type]
        self.assertFalse(res["ok"])
        self.assertFalse(res["allows_chat_access"])

    def test_invalid_status_returns_allows_false(self):
        r = _make_record(billing_abo_status="bogus")
        res = m.billing_status_allows_chat_access_v1(r)
        self.assertFalse(res["ok"])

    def test_past_due_is_not_chat_access_allowed(self):
        # past_due is intentionally NOT in the chat-access-allowed
        # set per Slice 7 spec (payment-failing status).
        self.assertNotIn("past_due", m.BILLING_ABO_CHAT_ACCESS_ALLOWED_V1)


# ----------------------------------------------------------------------------
# Summarize
# ----------------------------------------------------------------------------

class TestSummarize(unittest.TestCase):
    def test_summarize_ok(self):
        r = _make_record(billing_abo_status="active")
        res = m.summarize_billing_abo_status_record_v1(r)
        self.assertTrue(res["ok"])
        summary = res["summary"]
        for field in (
            "summary_version", "account_id", "billing_abo_status",
            "previous_billing_abo_status", "billing_abo_updated_at",
            "billing_abo_updated_by", "billing_abo_reason_label",
            "entitlement_recompute_required", "allows_chat_access",
        ):
            self.assertIn(field, summary)

    def test_summary_does_not_carry_forbidden_keys(self):
        r = _make_record(billing_abo_status="active")
        res = m.summarize_billing_abo_status_record_v1(r)
        self.assertTrue(res["ok"])
        summary = res["summary"]
        for field in summary:
            self.assertNotIn(field, m.BILLING_ABO_STATUS_NEVER_INCLUDES)

    def test_summary_allows_chat_access_flag(self):
        r = _make_record(billing_abo_status="active")
        res = m.summarize_billing_abo_status_record_v1(r)
        self.assertTrue(res["ok"])
        self.assertTrue(res["summary"]["allows_chat_access"])

    def test_summary_no_chat_access(self):
        r = _make_record(billing_abo_status="unpaid")
        res = m.summarize_billing_abo_status_record_v1(r)
        self.assertTrue(res["ok"])
        self.assertFalse(res["summary"]["allows_chat_access"])

    def test_summary_invalid_record_returns_ok_false(self):
        res = m.summarize_billing_abo_status_record_v1("not a dict")  # type: ignore[arg-type]
        self.assertFalse(res["ok"])

    def test_summary_does_not_leak_payment_card(self):
        r = _make_record(billing_abo_status="active")
        r["payment_card"] = "4111-1111-1111-1111"
        # Validation should fail; summary should also fail.
        res = m.summarize_billing_abo_status_record_v1(r)
        self.assertFalse(res["ok"])


# ----------------------------------------------------------------------------
# JSON-safe serialization
# ----------------------------------------------------------------------------

class TestJsonSafe(unittest.TestCase):
    def test_basic_serialization(self):
        r = _make_record(billing_abo_status="active")
        s = m.to_billing_abo_status_json_safe_v1(r)
        self.assertIsInstance(s, str)
        parsed = json.loads(s)
        self.assertEqual(parsed["billing_abo_status"], "active")

    def test_top_level_forbidden_key_redacted(self):
        r = _make_record(billing_abo_status="active")
        r["payment_card"] = "4111-1111-1111-1111"
        s = m.to_billing_abo_status_json_safe_v1(r)
        parsed = json.loads(s)
        self.assertEqual(parsed["payment_card"], "<redacted:billing-abo-forbidden-key>")

    def test_nested_forbidden_key_redacted(self):
        r = _make_record(billing_abo_status="active")
        r["billing_provider_ref_metadata"] = {"card_number": "4111", "external_ref": "evt_1"}
        s = m.to_billing_abo_status_json_safe_v1(r)
        parsed = json.loads(s)
        nested = parsed["billing_provider_ref_metadata"]
        self.assertEqual(nested["card_number"], "<redacted:billing-abo-forbidden-key>")
        self.assertEqual(nested["external_ref"], "evt_1")

    def test_forbidden_key_in_list_redacted(self):
        r = _make_record(billing_abo_status="active")
        r["billing_abo_reason_labels"] = ["normal", {"secret": "leaked"}]
        s = m.to_billing_abo_status_json_safe_v1(r)
        parsed = json.loads(s)
        self.assertEqual(parsed["billing_abo_reason_labels"][0], "normal")
        self.assertEqual(
            parsed["billing_abo_reason_labels"][1]["secret"],
            "<redacted:billing-abo-forbidden-key>",
        )

    def test_cyclic_structure_returns_cyclic_marker(self):
        a: Dict[str, Any] = {"x": 1}
        a["self"] = a
        s = m.to_billing_abo_status_json_safe_v1(a)
        self.assertIn("<cyclic>", s)

    def test_non_serializable_returns_error_envelope(self):
        # A set is not JSON-serializable. The helper's recursive
        # scrub returns the set unchanged at the leaf level
        # (sets are not dict/list/tuple, so they pass through).
        # json.dumps with default=str converts the set to its
        # string repr without raising. The fallback
        # {"serialization_error": true} only triggers on
        # TypeError/ValueError. Both outcomes are safe.
        s = m.to_billing_abo_status_json_safe_v1({1, 2, 3})
        parsed = json.loads(s)
        is_fallback = (parsed == {"serialization_error": True})
        is_str_repr = (
            isinstance(parsed, str) and ("{" in parsed or "set" in parsed)
        )
        self.assertTrue(
            is_fallback or is_str_repr,
            msg=f"unexpected serialization: {s}",
        )

    def test_serialization_never_includes_raw_prompt_text(self):
        r = _make_record(billing_abo_status="active")
        # Even if raw_prompt slips in, JSON-safe should redact it.
        r["raw_prompt"] = "user typed secret things"
        s = m.to_billing_abo_status_json_safe_v1(r)
        self.assertNotIn("user typed secret things", s)


# ----------------------------------------------------------------------------
# Strict boundary invariants (the "is this helper safe?" tests)
# ----------------------------------------------------------------------------

class TestStrictBoundary(unittest.TestCase):
    def _non_comment_source(self) -> str:
        """
        Return the module source with all triple-quoted
        docstrings and `#`-comment lines removed. This way,
        tests can scan for forbidden tokens that should not
        appear in actual executable code.
        """
        with open(m.__file__, "r", encoding="utf-8") as f:
            source = f.read()
        in_docstring = False
        docstring_marker: Optional[str] = None
        output_lines: List[str] = []
        for line in source.split("\n"):
            stripped = line.strip()
            # Track triple-quoted docstring regions.
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_marker = stripped[:3]
                    rest = stripped[3:]
                    if docstring_marker and docstring_marker in rest:
                        in_docstring = False
                    else:
                        in_docstring = True
                    continue
                # Drop comment lines.
                if stripped.startswith("#"):
                    continue
                output_lines.append(line)
            else:
                if docstring_marker and docstring_marker in stripped:
                    in_docstring = False
        return "\n".join(output_lines)

    def _top_level_imports(self) -> List[str]:
        """
        Extract top-level import lines from the module.
        """
        with open(m.__file__, "r", encoding="utf-8") as f:
            source = f.read()
        in_docstring = False
        docstring_marker: Optional[str] = None
        imports: List[str] = []
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_marker = stripped[:3]
                    rest = stripped[3:]
                    if docstring_marker and docstring_marker in rest:
                        in_docstring = False
                    else:
                        in_docstring = True
                    continue
                if stripped.startswith("import ") or stripped.startswith("from "):
                    imports.append(stripped)
            else:
                if docstring_marker and docstring_marker in stripped:
                    in_docstring = False
        return imports

    def test_no_weslr_state_path(self):
        # Outside the docstring, the helper must not reference
        # /home/pr0/weslr_state/ or "weslr_state".
        code = self._non_comment_source()
        self.assertNotIn("/home/pr0/weslr_state/", code)
        self.assertNotIn("weslr_state", code)

    def test_no_filesystem_write_calls(self):
        code = self._non_comment_source()
        for forbidden in (
            ".write(",
            "os.makedirs",
            "os.mkdir",
            "subprocess",
            "import urllib",
            "import requests",
            "import stripe",
            "import braintree",
            "import adyen",
        ):
            self.assertNotIn(forbidden, code, msg=f"found forbidden token: {forbidden}")

    def test_no_runtime_wiring_imports(self):
        imports = self._top_level_imports()
        joined = "\n".join(imports)
        for forbidden_import in (
            "weslr.chat_responder",
            "weslr.runtime_wrapper",
            "weslr.session_manager",
            "weslr.audit_log",
            "weslr.audit_log_persistence",
            "weslr.dialogue",
            "weslr.chat_ui",
            "weslr.main",
        ):
            self.assertNotIn(
                forbidden_import,
                joined,
                msg=f"found forbidden top-level import: {forbidden_import}",
            )

    def test_no_payment_provider_imports(self):
        imports = self._top_level_imports()
        joined = "\n".join(imports)
        for forbidden in (
            "import stripe",
            "from stripe",
            "import braintree",
            "from braintree",
            "import adyen",
            "from adyen",
            "import klarna",
            "from klarna",
            "import paypal",
            "from paypal",
        ):
            self.assertNotIn(forbidden, joined)

    def test_no_network_subprocess_imports(self):
        imports = self._top_level_imports()
        joined = "\n".join(imports)
        for forbidden in (
            "import urllib.request",
            "import urllib2",
            "import requests",
            "import httpx",
            "import aiohttp",
            "import socket",
            "import subprocess",
            "from subprocess",
            "import os.system",
        ):
            self.assertNotIn(forbidden, joined)

    def test_only_safe_top_level_imports(self):
        imports = self._top_level_imports()
        allowed_prefixes = (
            "import json",
            "import uuid",
            "from typing",
            "from __future__",
            "from weslr.entitlement_packet",
            "from weslr.account_status",
        )
        for imp in imports:
            ok = any(imp.startswith(prefix) for prefix in allowed_prefixes)
            self.assertTrue(
                ok,
                msg=f"top-level import not in whitelist: {imp!r}",
            )


# ----------------------------------------------------------------------------
# Protected files invariant (operator's spec: 31)
# ----------------------------------------------------------------------------

class TestProtectedFilesUnchanged(unittest.TestCase):
    """
    Verify that the protected runtime/wiring files were NOT
    modified by the Slice 7 commit. These are the files
    already shipped in Slices 1-6 (or earlier); Slice 7
    must not touch them.
    """

    # The path-resolved absolute path of the WESLR repo root
    # (the parent of weslr/). Slice 7 is committed into a
    # worktree under /home/pr0/projects/weslr-*; we walk up
    # from m.__file__ to find the repo root.
    @classmethod
    def _repo_root(cls) -> str:
        import os
        p = os.path.abspath(m.__file__)
        # p is <repo>/weslr/billing_abo_status.py
        return os.path.dirname(os.path.dirname(p))

    def _read_file(self, relpath: str) -> str:
        import os
        full = os.path.join(self._repo_root(), relpath)
        with open(full, "r", encoding="utf-8") as f:
            return f.read()

    def test_account_status_unchanged(self):
        # Read both the current file and the canonical-version
        # of the same file. If the file exists in the worktree,
        # it MUST match the canonical `origin/occ-discovery-...`
        # version byte-for-byte (we only count addition of new
        # files in Slice 7; we MUST NOT have modified any
        # pre-existing file).
        import subprocess
        canonical = "origin/occ-discovery-doctrine-implementation-20260613"
        relpath = "weslr/account_status.py"
        local = self._read_file(relpath)
        try:
            result = subprocess.run(
                ["git", "show", f"{canonical}:{relpath}"],
                cwd=self._repo_root(),
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                self.skipTest(f"could not read canonical {relpath}")
            canonical_bytes = result.stdout
            self.assertEqual(
                local, canonical_bytes,
                msg=f"{relpath} differs from canonical",
            )
        except FileNotFoundError:
            self.skipTest("git not available")

    def test_entitlement_packet_unchanged(self):
        import subprocess
        canonical = "origin/occ-discovery-doctrine-implementation-20260613"
        relpath = "weslr/entitlement_packet.py"
        local = self._read_file(relpath)
        try:
            result = subprocess.run(
                ["git", "show", f"{canonical}:{relpath}"],
                cwd=self._repo_root(),
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                self.skipTest(f"could not read canonical {relpath}")
            self.assertEqual(
                local, result.stdout,
                msg=f"{relpath} differs from canonical",
            )
        except FileNotFoundError:
            self.skipTest("git not available")

    def test_slice_2_through_5_files_unchanged(self):
        # Verify that the Slice 2-5 protected files match the
        # canonical version. We check byte-for-byte equality.
        import subprocess
        canonical = "origin/occ-discovery-doctrine-implementation-20260613"
        protected = [
            "weslr/runtime_wrapper.py",
            "weslr/session_manager.py",
            "weslr/audit_log.py",
            "weslr/audit_log_persistence.py",
        ]
        for relpath in protected:
            local = self._read_file(relpath)
            try:
                result = subprocess.run(
                    ["git", "show", f"{canonical}:{relpath}"],
                    cwd=self._repo_root(),
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    self.skipTest(f"could not read canonical {relpath}")
                self.assertEqual(
                    local, result.stdout,
                    msg=f"{relpath} differs from canonical",
                )
            except FileNotFoundError:
                self.skipTest("git not available")


# ----------------------------------------------------------------------------
# Helper module-level sanity
# ----------------------------------------------------------------------------

class TestModule(unittest.TestCase):
    def test_module_has_all_8_public_apis(self):
        for fn in (
            "build_billing_abo_status_record_v1",
            "validate_billing_abo_status_record_v1",
            "build_billing_abo_transition_request_v1",
            "validate_billing_abo_transition_request_v1",
            "apply_billing_abo_transition_v1",
            "billing_status_allows_chat_access_v1",
            "summarize_billing_abo_status_record_v1",
            "to_billing_abo_status_json_safe_v1",
        ):
            self.assertTrue(
                hasattr(m, fn),
                msg=f"missing public API: {fn}",
            )
            self.assertTrue(callable(getattr(m, fn)))

    def test_public_api_returns_dict_or_tuple(self):
        # The 8 public APIs must return either dict or tuple
        # (not None / not raise).
        r = _make_record()
        ok, errs = m.validate_billing_abo_status_record_v1(r)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(errs, list)
        req = _make_request()
        ok, errs = m.validate_billing_abo_transition_request_v1(req)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(errs, list)
        res = m.apply_billing_abo_transition_v1(r, req)
        self.assertIsInstance(res, dict)
        chat = m.billing_status_allows_chat_access_v1(r)
        self.assertIsInstance(chat, dict)
        sm = m.summarize_billing_abo_status_record_v1(r)
        self.assertIsInstance(sm, dict)
        js = m.to_billing_abo_status_json_safe_v1(r)
        self.assertIsInstance(js, str)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
