"""
WESLR chat.weslr.de Slice 4A — Audit Event Schema Helper Tests V1

Standalone tests for the audit event schema and in-memory store
helper. Pure-Python, no I/O, no protected-file imports, no
provider/model calls, no real persistence.

Run:
  python3 -m unittest weslr.tests.test_audit_log_v1 -v
"""

from __future__ import annotations

import unittest

from weslr.audit_log import (
    AUDIT_LOG_VERSION,
    ALLOWED_AUDIT_EVENT_CATEGORIES_V1,
    AUDIT_LOG_NEVER_INCLUDES_V1,
    REASON_OK,
    REASON_INVALID_MISSING_FIELDS,
    REASON_INVALID_BAD_CATEGORY,
    REASON_INVALID_NEVER_INCLUDES_KEY,
    REASON_INVALID_NOT_DICT,
    REASON_INVALID_STORE_NOT_LIST,
    FUTURE_LOG_STORAGE_PATH_METADATA,
    REQUIRED_AUDIT_EVENT_FIELDS_V1,
    build_audit_event_v1,
    validate_audit_event_v1,
    summarize_audit_event_v1,
    append_audit_event_to_in_memory_store_v1,
    list_audit_events_from_in_memory_store_v1,
    to_audit_log_json_safe_v1,
)


def _make_event(
    action_type="user_created",
    operator_ref="operator_alice",
    account_id="pilot_1",
    session_id="",
    before=None,
    after=None,
    reason_label="invite",
    summary="user invited",
    reason_labels=None,
):
    return build_audit_event_v1(
        audit_log_action_type=action_type,
        audit_log_operator_ref=operator_ref,
        audit_log_target_account_id=account_id,
        audit_log_target_session_id=session_id,
        audit_log_before_state=before,
        audit_log_after_state=after,
        audit_log_reason_label=reason_label,
        audit_log_summary=summary,
        reason_labels=reason_labels,
    )


class TestBuildEvent(unittest.TestCase):
    def test_version_present(self):
        e = _make_event()
        self.assertEqual(e["audit_log_version"], AUDIT_LOG_VERSION)

    def test_entry_id_auto_uuid(self):
        e = _make_event()
        self.assertEqual(len(e["audit_log_entry_id"]), 36)
        self.assertEqual(e["audit_log_entry_id"][8], "-")

    def test_raw_content_retained_always_false(self):
        e = _make_event()
        self.assertFalse(e["audit_log_raw_content_retained"])

    def test_never_includes_lists_forbidden_keys(self):
        e = _make_event()
        self.assertIsInstance(e["audit_log_never_includes"], list)
        for forbidden_key in AUDIT_LOG_NEVER_INCLUDES_V1:
            self.assertIn(forbidden_key, e["audit_log_never_includes"])

    def test_before_state_defaulted_to_dict(self):
        e = _make_event()
        self.assertEqual(e["audit_log_before_state"], {})

    def test_after_state_defaulted_to_dict(self):
        e = _make_event()
        self.assertEqual(e["audit_log_after_state"], {})

    def test_future_storage_path_metadata_present(self):
        e = _make_event()
        self.assertEqual(e["future_log_storage_path_metadata"], FUTURE_LOG_STORAGE_PATH_METADATA)
        self.assertEqual(e["future_log_storage_path_metadata"], "/home/pr0/weslr_state/logs/")

    def test_required_fields_present(self):
        e = _make_event()
        for key in REQUIRED_AUDIT_EVENT_FIELDS_V1:
            self.assertIn(key, e)

    def test_target_session_defaulted_to_empty(self):
        e = _make_event()
        self.assertEqual(e["audit_log_target_session_id"], "")

    def test_target_resource_defaulted_to_empty(self):
        e = _make_event()
        self.assertEqual(e["audit_log_target_resource"], "")

    def test_with_explicit_entry_id(self):
        e = build_audit_event_v1(
            audit_log_action_type="user_created",
            audit_log_operator_ref="op-1",
            audit_log_entry_id="explicit-id-1",
        )
        self.assertEqual(e["audit_log_entry_id"], "explicit-id-1")


class TestValidateEvent(unittest.TestCase):
    def test_valid_event_passes(self):
        e = _make_event()
        ok, errs = validate_audit_event_v1(e)
        self.assertTrue(ok, msg=f"errors: {errs}")
        self.assertEqual(errs, [])

    def test_non_dict_rejected(self):
        ok, errs = validate_audit_event_v1("not-a-dict")
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_NOT_DICT, errs)

    def test_none_rejected(self):
        ok, errs = validate_audit_event_v1(None)
        self.assertFalse(ok)
        self.assertIn(REASON_INVALID_NOT_DICT, errs)

    def test_missing_field_rejected(self):
        e = _make_event()
        del e["audit_log_action_type"]
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertTrue(any("audit_log_action_type" in err for err in errs))
        self.assertTrue(any(REASON_INVALID_MISSING_FIELDS in err for err in errs))

    def test_invalid_category_rejected(self):
        e = _make_event(action_type="not_a_real_category")
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertTrue(any(REASON_INVALID_BAD_CATEGORY in err for err in errs))

    def test_raw_content_retained_true_rejected(self):
        e = _make_event()
        e["audit_log_raw_content_retained"] = True
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertIn("raw_content_retained_must_be_false", errs)

    def test_forbidden_key_in_event_rejected(self):
        # If the event tries to carry a forbidden key (e.g., raw_prompt),
        # validation must reject it as an audit_log_never_includes violation.
        e = _make_event()
        e["raw_prompt"] = "SENSITIVE"
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertTrue(any(
            REASON_INVALID_NEVER_INCLUDES_KEY in err and "raw_prompt" in err
            for err in errs
        ))

    def test_forbidden_key_nested_in_before_state_rejected(self):
        # Operator test 7: rejects forbidden key nested inside before_state
        e = _make_event()
        e["audit_log_before_state"] = {"raw_prompt": "SENSITIVE_NESTED"}
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertTrue(any(
            REASON_INVALID_NEVER_INCLUDES_KEY in err and "raw_prompt" in err
            for err in errs
        ))

    def test_forbidden_key_nested_in_after_state_rejected(self):
        # Operator test 8: rejects forbidden key nested inside after_state
        e = _make_event()
        e["audit_log_after_state"] = {"raw_reply": "SENSITIVE_NESTED"}
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertTrue(any(
            REASON_INVALID_NEVER_INCLUDES_KEY in err and "raw_reply" in err
            for err in errs
        ))

    def test_password_secret_api_key_rejected_top_level(self):
        # Operator test 9: rejects password/secret/api_key fields
        for forbidden_key in ("password", "secret", "api_key"):
            e = _make_event()
            e[forbidden_key] = "SENSITIVE"
            ok, errs = validate_audit_event_v1(e)
            self.assertFalse(ok, msg=f"{forbidden_key} should be rejected")
            self.assertTrue(any(
                REASON_INVALID_NEVER_INCLUDES_KEY in err and forbidden_key in err
                for err in errs
            ), msg=f"errors for {forbidden_key}: {errs}")

    def test_password_secret_api_key_rejected_nested(self):
        # Operator test 9 nested: rejects password/secret/api_key in nested dicts
        for forbidden_key in ("password", "secret", "api_key"):
            e = _make_event()
            e["audit_log_before_state"] = {forbidden_key: "SENSITIVE_NESTED"}
            ok, errs = validate_audit_event_v1(e)
            self.assertFalse(ok, msg=f"{forbidden_key} nested should be rejected")
            self.assertTrue(any(
                REASON_INVALID_NEVER_INCLUDES_KEY in err and forbidden_key in err
                for err in errs
            ), msg=f"errors for nested {forbidden_key}: {errs}")

    def test_never_includes_as_list_required(self):
        e = _make_event()
        e["audit_log_never_includes"] = "not-a-list"
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertIn("never_includes_must_be_list", errs)

    def test_before_state_must_be_dict(self):
        e = _make_event()
        e["audit_log_before_state"] = "not-a-dict"
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertIn("audit_log_before_state_not_dict", errs)

    def test_after_state_must_be_dict(self):
        e = _make_event()
        e["audit_log_after_state"] = "not-a-dict"
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertIn("audit_log_after_state_not_dict", errs)

    def test_reason_labels_must_be_list(self):
        e = _make_event()
        e["reason_labels"] = "not-a-list"
        ok, errs = validate_audit_event_v1(e)
        self.assertFalse(ok)
        self.assertIn("reason_labels_not_list", errs)

    def test_all_required_fields_checked(self):
        # Verify each required field is independently checked.
        for missing_key in REQUIRED_AUDIT_EVENT_FIELDS_V1:
            e = _make_event()
            del e[missing_key]
            ok, errs = validate_audit_event_v1(e)
            self.assertFalse(ok, msg=f"field {missing_key} should be required")
            self.assertTrue(any(missing_key in err for err in errs),
                            msg=f"errors for missing {missing_key}: {errs}")


class TestAppendAndList(unittest.TestCase):
    def setUp(self):
        self.store: list = []

    def test_append_valid_event(self):
        e = _make_event()
        result = append_audit_event_to_in_memory_store_v1(self.store, e)
        self.assertTrue(result["ok"])
        self.assertIn(REASON_OK, result["reason_labels"])
        self.assertEqual(len(self.store), 1)
        self.assertEqual(self.store[0]["audit_log_entry_id"], e["audit_log_entry_id"])

    def test_append_rejects_invalid_event(self):
        bad = {"some": "junk"}  # missing required fields
        result = append_audit_event_to_in_memory_store_v1(self.store, bad)
        self.assertFalse(result["ok"])
        self.assertEqual(len(self.store), 0)

    def test_append_rejects_non_list_store(self):
        e = _make_event()
        result = append_audit_event_to_in_memory_store_v1("not-a-list", e)
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_STORE_NOT_LIST, result["reason_labels"])

    def test_append_rejects_event_with_forbidden_key(self):
        e = _make_event()
        e["raw_reply"] = "SENSITIVE_REPLY"
        result = append_audit_event_to_in_memory_store_v1(self.store, e)
        self.assertFalse(result["ok"])
        self.assertEqual(len(self.store), 0)

    def test_append_does_not_mutate_event_after_storage(self):
        e = _make_event()
        result = append_audit_event_to_in_memory_store_v1(self.store, e)
        self.assertTrue(result["ok"])
        # Mutate the original event; the stored copy must not change.
        e["audit_log_operator_ref"] = "MUTATED"
        self.assertNotEqual(self.store[0]["audit_log_operator_ref"], "MUTATED")

    def test_list_all_when_no_filters(self):
        for i in range(3):
            e = _make_event(action_type="user_created")
            append_audit_event_to_in_memory_store_v1(self.store, e)
        result = list_audit_events_from_in_memory_store_v1(self.store)
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 3)
        self.assertEqual(len(result["events"]), 3)

    def test_list_filter_by_account_id(self):
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="a"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="b"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="a"))
        result = list_audit_events_from_in_memory_store_v1(self.store, account_id="a")
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 2)
        for ev in result["events"]:
            self.assertEqual(ev["audit_log_target_account_id"], "a")

    def test_list_filter_by_session_id(self):
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(session_id="s1"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(session_id="s2"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(session_id="s1"))
        result = list_audit_events_from_in_memory_store_v1(self.store, session_id="s1")
        self.assertEqual(result["count"], 2)

    def test_list_filter_by_action_type(self):
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(action_type="user_created"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(action_type="session_created"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(action_type="user_created"))
        result = list_audit_events_from_in_memory_store_v1(self.store, action_type="user_created")
        self.assertEqual(result["count"], 2)
        for ev in result["events"]:
            self.assertEqual(ev["audit_log_action_type"], "user_created")

    def test_list_combined_filters(self):
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="a", action_type="user_created"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="a", action_type="session_created"))
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="b", action_type="user_created"))
        result = list_audit_events_from_in_memory_store_v1(
            self.store, account_id="a", action_type="user_created"
        )
        self.assertEqual(result["count"], 1)

    def test_list_rejects_non_list_store(self):
        result = list_audit_events_from_in_memory_store_v1("not-a-list")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_STORE_NOT_LIST, result["reason_labels"])

    def test_list_no_matches_returns_zero(self):
        append_audit_event_to_in_memory_store_v1(self.store, _make_event(account_id="a"))
        result = list_audit_events_from_in_memory_store_v1(self.store, account_id="zzz")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["events"], [])


class TestSummaryAndSerialization(unittest.TestCase):
    def setUp(self):
        self.store: list = []

    def test_summary_for_valid_event(self):
        e = _make_event(
            action_type="user_created",
            operator_ref="op-1",
            account_id="pilot_1",
            reason_label="invite",
        )
        s = summarize_audit_event_v1(e)
        self.assertIn("action=user_created", s)
        self.assertIn("operator=op-1", s)
        self.assertIn("account=pilot_1", s)
        self.assertIn("reason=invite", s)

    def test_summary_for_invalid_event(self):
        s = summarize_audit_event_v1("not-a-dict")
        self.assertIn("invalid_audit_event", s)

    def test_json_safe_for_event(self):
        e = _make_event()
        s = to_audit_log_json_safe_v1(e)
        self.assertTrue(s.startswith("{"))
        self.assertIn('"audit_log_version": "weslr-audit-log-v1"', s)

    def test_json_safe_strips_private_keys(self):
        e = _make_event()
        e_with_private = {
            "audit_log_entry_id": "x",
            "audit_log_version": AUDIT_LOG_VERSION,
            "raw_prompt": "SENSITIVE_PROMPT",
            "raw_reply": "SENSITIVE_REPLY",
            "credentials": "SENSITIVE_CRED",
            "password": "SENSITIVE_PW",
            "hidden_prompt": "SENSITIVE_HIDDEN",
            "audit_log_action_type": "user_created",
            "audit_log_operator_ref": "op-1",
        }
        s = to_audit_log_json_safe_v1(e_with_private)
        for forbidden in ("SENSITIVE_PROMPT", "SENSITIVE_REPLY", "SENSITIVE_CRED",
                          "SENSITIVE_PW", "SENSITIVE_HIDDEN"):
            self.assertNotIn(forbidden, s, msg=f"forbidden key leaked: {forbidden}")
        for key in ("raw_prompt", "raw_reply", "credentials", "password", "hidden_prompt"):
            self.assertNotIn(f'"{key}"', s, msg=f"forbidden key name leaked: {key}")

    def test_json_safe_for_cyclic_dict(self):
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_audit_log_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertNotIn("SENSITIVE", s)
        self.assertTrue("<cyclic>" in s or "serialization_error" in s,
                        msg=f"unexpected output: {s}")

    def test_json_safe_for_non_serializable_object(self):
        # Cyclic dict must produce a safe fallback string.
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_audit_log_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertNotIn("SENSITIVE", s)
        self.assertTrue("<cyclic>" in s or "serialization_error" in s,
                        msg=f"unexpected output: {s}")


class TestAllowedCategories(unittest.TestCase):
    def test_all_16_categories_present(self):
        expected = {
            "user_created", "user_status_changed", "entitlement_changed",
            "session_created", "session_touched", "session_expired",
            "session_force_logged_out", "billing_status_changed",
            "grace_period_started", "access_disabled", "operator_action",
            "support_escalation", "deletion_requested", "deletion_completed",
            "runtime_authorization_denied", "runtime_authorization_allowed",
        }
        self.assertEqual(ALLOWED_AUDIT_EVENT_CATEGORIES_V1, frozenset(expected))

    def test_each_category_accepted_by_validation(self):
        for cat in ALLOWED_AUDIT_EVENT_CATEGORIES_V1:
            e = _make_event(action_type=cat)
            ok, errs = validate_audit_event_v1(e)
            self.assertTrue(ok, msg=f"category {cat} rejected: {errs}")


class TestAuditLogIsPure(unittest.TestCase):
    """Static checks that the audit log module is pure-Python with no I/O."""

    @staticmethod
    def _read_source():
        import weslr.audit_log as al
        with open(al.__file__, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_no_subprocess_import(self):
        src = self._read_source()
        self.assertNotIn("import subprocess", src)
        self.assertNotIn("from subprocess", src)

    def test_no_network_import(self):
        src = self._read_source()
        for net in ("urllib", "requests", "httpx", "socket", "aiohttp"):
            self.assertNotIn(net, src, msg=f"unexpected network module: {net}")

    def test_no_import_of_protected_runtime_modules(self):
        src = self._read_source()
        for forbidden in (
            "import weslr.chat_responder",
            "from weslr.chat_responder",
            "import weslr.dialogue",
            "from weslr.dialogue",
            "import weslr.chat_ui",
            "from weslr.chat_ui",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")

    def test_no_provider_or_model_import(self):
        src = self._read_source()
        for term in ("openai", "anthropic", "ollama", "transformers", "torch"):
            self.assertNotIn(term, src, msg=f"unexpected provider module: {term}")

    def test_no_filesystem_write_call(self):
        src = self._read_source()
        # Disallow direct file write/open patterns. JSON serialization
        # of the metadata-only future storage path is allowed.
        for forbidden in (".write(", "os.system", "shutil.", "pathlib.Path"):
            self.assertNotIn(forbidden, src, msg=f"forbidden op: {forbidden}")
        # open() calls are forbidden except for reading the source file in tests.
        # The module source itself should not call open().
        open_calls = sum(1 for line in src.splitlines() if "open(" in line and "open(" in line)
        self.assertEqual(open_calls, 0, msg=f"unexpected open() calls: {open_calls}")

    def test_no_call_to_weslr_state_writes(self):
        # The path may appear only as the metadata constant.
        src = self._read_source()
        count = src.count("/home/pr0/weslr_state/")
        self.assertLessEqual(count, 2, msg=f"unexpected writes-state path occurrences: {count}")


class TestForbiddenContract(unittest.TestCase):
    """The forbidden-keys contract is a hard guarantee."""

    def test_forbidden_keys_count_is_12(self):
        self.assertEqual(len(AUDIT_LOG_NEVER_INCLUDES_V1), 12)

    def test_all_required_forbidden_keys_present(self):
        required = {
            "raw_prompt", "raw_reply", "credentials",
            "session_token_plaintext", "hidden_prompt", "system_prompt",
            "chain_of_thought", "provider_response", "shadow_call_output",
            "password", "secret", "api_key",
        }
        self.assertTrue(required.issubset(AUDIT_LOG_NEVER_INCLUDES_V1))

    def test_summary_never_includes_private_keys(self):
        e = _make_event()
        s = summarize_audit_event_v1(e)
        for forbidden in AUDIT_LOG_NEVER_INCLUDES_V1:
            self.assertNotIn(forbidden, s, msg=f"summary leaked forbidden key: {forbidden}")


if __name__ == "__main__":
    unittest.main()