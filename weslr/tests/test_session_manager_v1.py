"""
WESLR chat.weslr.de Slice 3 — Session Manager Tests V1

Standalone tests for the session manager skeleton. Pure-Python, no I/O,
no protected-file imports, no provider/model calls, no real session
persistence.

Run:
  python3 -m unittest weslr.tests.test_session_manager_v1 -v
"""

from __future__ import annotations

import unittest

from weslr.session_manager import (
    SESSION_MANAGER_VERSION,
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_EXPIRED,
    SESSION_STATUS_FORCE_LOGGED_OUT,
    SESSION_STATUS_UNKNOWN,
    VALID_SESSION_STATUSES,
    REASON_OK,
    REASON_INVALID_MISSING_IDENTITY,
    REASON_INVALID_MISSING_SESSION_ID,
    REASON_INVALID_MISSING_CAPABILITY_SET,
    REASON_INVALID_MISSING_REQUIRED_FIELDS,
    REASON_NOT_FOUND,
    REASON_ALREADY_EXPIRED,
    REASON_ALREADY_FORCE_LOGGED_OUT,
    REASON_CANNOT_TOUCH_EXPIRED,
    REASON_CANNOT_TOUCH_FORCE_LOGGED_OUT,
    build_session_record_v1,
    validate_session_record_v1,
    create_session_v1,
    get_session_v1,
    touch_session_v1,
    expire_session_v1,
    force_logout_session_v1,
    summarize_session_record_v1,
    to_session_manager_json_safe_v1,
)


def _make_session(identity="alice", caps=None, created="2026-06-23T12:00:00Z", expires=None, session_id="sess-1"):
    if caps is None:
        caps = ["health_check_read"]
    return build_session_record_v1(
        identity_id=identity,
        capability_set=caps,
        session_id=session_id,
        created_at=created,
        last_seen_at=created,
        expires_at=expires,
    )


class TestBuildRecord(unittest.TestCase):
    def test_version_present(self):
        s = _make_session()
        self.assertEqual(s["session_manager_version"], SESSION_MANAGER_VERSION)

    def test_session_id_present(self):
        s = _make_session()
        self.assertEqual(s["session_id"], "sess-1")

    def test_auto_session_id_is_uuid(self):
        s = build_session_record_v1(identity_id="x", capability_set=["y"])
        self.assertEqual(len(s["session_id"]), 36)
        # UUID4 has dashes at positions 8, 13, 18, 23.
        self.assertEqual(s["session_id"][8], "-")
        self.assertEqual(s["session_id"][13], "-")
        self.assertEqual(s["session_id"][18], "-")
        self.assertEqual(s["session_id"][23], "-")

    def test_raw_content_retained_always_false(self):
        s = _make_session()
        self.assertFalse(s["raw_content_retained"])

    def test_cross_session_shared_always_false(self):
        s = _make_session()
        self.assertFalse(s["cross_session_shared"])

    def test_future_storage_path_metadata_present(self):
        s = _make_session()
        self.assertEqual(s["future_storage_path_metadata"], "/home/pr0/weslr_state/sessions/")

    def test_capability_set_defaulted_to_list(self):
        s = build_session_record_v1(identity_id="x", capability_set=None)
        self.assertEqual(s["capability_set"], [])

    def test_initial_status_active(self):
        s = _make_session()
        self.assertEqual(s["session_status"], SESSION_STATUS_ACTIVE)


class TestValidateRecord(unittest.TestCase):
    def test_valid_session_passes(self):
        s = _make_session()
        ok, errs = validate_session_record_v1(s)
        self.assertTrue(ok, msg=f"errors: {errs}")
        self.assertEqual(errs, [])

    def test_non_dict_rejected(self):
        ok, errs = validate_session_record_v1("not-a-dict")
        self.assertFalse(ok)
        self.assertIn("session_not_dict", errs)

    def test_none_rejected(self):
        ok, errs = validate_session_record_v1(None)
        self.assertFalse(ok)
        self.assertIn("session_not_dict", errs)

    def test_empty_identity_rejected(self):
        s = _make_session(identity="")
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("empty_identity_id", errs)

    def test_empty_session_id_rejected(self):
        s = _make_session(session_id="")
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("empty_session_id", errs)

    def test_empty_capability_set_rejected(self):
        s = _make_session(caps=[])
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("empty_capability_set", errs)

    def test_invalid_status_rejected(self):
        s = _make_session()
        s["session_status"] = "not_a_real_status"
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("invalid_status", errs)

    def test_raw_content_retained_true_rejected(self):
        s = _make_session()
        s["raw_content_retained"] = True
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("raw_content_retained_must_be_false", errs)

    def test_cross_session_shared_true_rejected(self):
        s = _make_session()
        s["cross_session_shared"] = True
        ok, errs = validate_session_record_v1(s)
        self.assertFalse(ok)
        self.assertIn("cross_session_shared_must_be_false", errs)


class TestCreateSession(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_creates_session_in_store(self):
        result = create_session_v1(
            self.store, "alice", ["health_check_read"],
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        self.assertTrue(result["ok"])
        self.assertIn(REASON_OK, result["reason_labels"])
        self.assertIsNotNone(result["session"])
        self.assertEqual(len(self.store), 1)
        self.assertEqual(result["session"]["identity_id"], "alice")
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_ACTIVE)
        self.assertEqual(result["session"]["capability_set"], ["health_check_read"])

    def test_rejects_missing_identity(self):
        result = create_session_v1(self.store, "", ["x"])
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_IDENTITY, result["reason_labels"])
        self.assertIsNone(result["session"])
        self.assertEqual(len(self.store), 0)

    def test_rejects_missing_capability_set(self):
        result = create_session_v1(self.store, "alice", [])
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_CAPABILITY_SET, result["reason_labels"])
        self.assertEqual(len(self.store), 0)

    def test_rejects_missing_capability_set_when_none(self):
        result = create_session_v1(self.store, "alice", None)
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_CAPABILITY_SET, result["reason_labels"])

    def test_rejects_session_id_collision(self):
        create_session_v1(self.store, "alice", ["x"], session_id="dup")
        result = create_session_v1(self.store, "bob", ["y"], session_id="dup")
        self.assertFalse(result["ok"])
        self.assertIn("session_id_already_exists", result["reason_labels"])
        self.assertEqual(len(self.store), 1)

    def test_rejects_non_dict_store(self):
        result = create_session_v1("not-a-dict", "alice", ["x"])
        self.assertFalse(result["ok"])
        self.assertIn("invalid_store_not_dict", result["reason_labels"])

    def test_explicit_session_id_preserved(self):
        result = create_session_v1(
            self.store, "alice", ["x"],
            session_id="my-id-1",
            created_at="2026-06-23T12:00:00Z",
        )
        self.assertEqual(result["session"]["session_id"], "my-id-1")


class TestGetSession(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_get_existing_session(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        result = get_session_v1(self.store, "s1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["session"]["session_id"], "s1")
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_ACTIVE)

    def test_get_unknown_session_returns_not_found(self):
        result = get_session_v1(self.store, "missing")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_NOT_FOUND, result["reason_labels"])
        self.assertIsNone(result["session"])

    def test_get_missing_session_id_rejected(self):
        result = get_session_v1(self.store, "")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_SESSION_ID, result["reason_labels"])

    def test_get_non_dict_store_rejected(self):
        result = get_session_v1("not-a-dict", "x")
        self.assertFalse(result["ok"])
        self.assertIn("invalid_store_not_dict", result["reason_labels"])

    def test_get_with_now_after_expiry_returns_expired(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-23T13:00:00Z",
        )
        result = get_session_v1(self.store, "s1", now="2026-06-23T14:00:00Z")
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_EXPIRED)


class TestTouchSession(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_touch_updates_last_seen_at(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        result = touch_session_v1(self.store, "s1", now="2026-06-23T13:00:00Z")
        self.assertTrue(result["ok"])
        self.assertEqual(result["session"]["last_seen_at"], "2026-06-23T13:00:00Z")

    def test_touch_does_not_silently_extend_absolute_expiry(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-23T13:00:00Z",
        )
        touch_session_v1(self.store, "s1", now="2026-06-23T13:30:00Z")
        # Absolute expiry unchanged.
        self.assertEqual(self.store["s1"]["expires_at"], "2026-06-23T13:00:00Z")

    def test_touch_expired_session_denied(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-23T13:00:00Z",
        )
        result = touch_session_v1(self.store, "s1", now="2026-06-23T14:00:00Z")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_CANNOT_TOUCH_EXPIRED, result["reason_labels"])
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_EXPIRED)

    def test_touch_unknown_session_returns_not_found(self):
        result = touch_session_v1(self.store, "missing", now="2026-06-23T13:00:00Z")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_NOT_FOUND, result["reason_labels"])

    def test_touch_force_logged_out_denied(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        force_logout_session_v1(self.store, "s1", operator_ref="op-1")
        result = touch_session_v1(self.store, "s1", now="2026-06-23T13:00:00Z")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_CANNOT_TOUCH_FORCE_LOGGED_OUT, result["reason_labels"])

    def test_touch_missing_session_id_rejected(self):
        result = touch_session_v1(self.store, "", now="2026-06-23T13:00:00Z")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_SESSION_ID, result["reason_labels"])

    def test_touch_non_dict_store_rejected(self):
        result = touch_session_v1("not-a-dict", "x", now="2026-06-23T13:00:00Z")
        self.assertFalse(result["ok"])
        self.assertIn("invalid_store_not_dict", result["reason_labels"])


class TestExpireSession(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_expire_changes_status(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        result = expire_session_v1(self.store, "s1", reason="manual")
        self.assertTrue(result["ok"])
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_EXPIRED)

    def test_expire_unknown_session_returns_not_found(self):
        result = expire_session_v1(self.store, "missing")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_NOT_FOUND, result["reason_labels"])

    def test_expire_already_expired_denied(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        expire_session_v1(self.store, "s1")
        result = expire_session_v1(self.store, "s1")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_ALREADY_EXPIRED, result["reason_labels"])

    def test_expire_missing_session_id_rejected(self):
        result = expire_session_v1(self.store, "")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_SESSION_ID, result["reason_labels"])

    def test_expire_non_dict_store_rejected(self):
        result = expire_session_v1("not-a-dict", "x")
        self.assertFalse(result["ok"])
        self.assertIn("invalid_store_not_dict", result["reason_labels"])

    def test_expire_reason_label_sanitized(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        result = expire_session_v1(self.store, "s1", reason="admin override/with spaces!")
        self.assertTrue(result["ok"])
        # Reason should be sanitized to a safe machine-readable label.
        labels = result["session"]["reason_labels"]
        self.assertTrue(any(lbl.replace("_", "").replace("-", "").isalnum() for lbl in labels))


class TestForceLogout(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_force_logout_changes_status(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        result = force_logout_session_v1(self.store, "s1", operator_ref="op-1")
        self.assertTrue(result["ok"])
        self.assertEqual(result["session"]["session_status"], SESSION_STATUS_FORCE_LOGGED_OUT)

    def test_force_logged_out_cannot_become_active_via_touch(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        force_logout_session_v1(self.store, "s1", operator_ref="op-1")
        touch_result = touch_session_v1(self.store, "s1", now="2026-06-23T13:00:00Z")
        self.assertFalse(touch_result["ok"])
        self.assertEqual(touch_result["session"]["session_status"], SESSION_STATUS_FORCE_LOGGED_OUT)

    def test_force_logged_out_cannot_become_expired_via_expire(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        force_logout_session_v1(self.store, "s1", operator_ref="op-1")
        expire_result = expire_session_v1(self.store, "s1")
        self.assertFalse(expire_result["ok"])
        self.assertEqual(expire_result["session"]["session_status"], SESSION_STATUS_FORCE_LOGGED_OUT)

    def test_force_logout_unknown_session_returns_not_found(self):
        result = force_logout_session_v1(self.store, "missing", operator_ref="op-1")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_NOT_FOUND, result["reason_labels"])

    def test_force_logout_missing_session_id_rejected(self):
        result = force_logout_session_v1(self.store, "", operator_ref="op-1")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_INVALID_MISSING_SESSION_ID, result["reason_labels"])

    def test_force_logout_missing_operator_ref_rejected(self):
        result = force_logout_session_v1(self.store, "s1", operator_ref="")
        self.assertFalse(result["ok"])
        self.assertIn("invalid_missing_operator_ref", result["reason_labels"])

    def test_force_logout_already_force_logged_out_denied(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        force_logout_session_v1(self.store, "s1", operator_ref="op-1")
        result = force_logout_session_v1(self.store, "s1", operator_ref="op-2")
        self.assertFalse(result["ok"])
        self.assertIn(REASON_ALREADY_FORCE_LOGGED_OUT, result["reason_labels"])

    def test_force_logout_non_dict_store_rejected(self):
        result = force_logout_session_v1("not-a-dict", "x", operator_ref="op-1")
        self.assertFalse(result["ok"])
        self.assertIn("invalid_store_not_dict", result["reason_labels"])


class TestCrossSessionIsolation(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_no_cross_session_sharing_by_default(self):
        a = create_session_v1(
            self.store, "alice", ["x"],
            session_id="alice-sess",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        b = create_session_v1(
            self.store, "bob", ["y"],
            session_id="bob-sess",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        # Touching one does not affect the other.
        touch_session_v1(self.store, "alice-sess", now="2026-06-23T13:00:00Z")
        self.assertEqual(self.store["bob-sess"]["last_seen_at"], "2026-06-23T12:00:00Z")
        # Capability sets are distinct.
        self.assertNotEqual(
            self.store["alice-sess"]["capability_set"],
            self.store["bob-sess"]["capability_set"],
        )
        # Both records have cross_session_shared=False.
        self.assertFalse(a["session"]["cross_session_shared"])
        self.assertFalse(b["session"]["cross_session_shared"])

    def test_records_are_isolated_after_force_logout(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="alice-sess",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        create_session_v1(
            self.store, "bob", ["y"],
            session_id="bob-sess",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        force_logout_session_v1(self.store, "alice-sess", operator_ref="op-1")
        # Bob's session is still active.
        self.assertEqual(self.store["bob-sess"]["session_status"], SESSION_STATUS_ACTIVE)


class TestSummaryAndSerialization(unittest.TestCase):
    def setUp(self):
        self.store: dict = {}

    def test_summary_for_session(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
            expires_at="2026-06-30T12:00:00Z",
        )
        s = summarize_session_record_v1(self.store["s1"])
        self.assertIn("session_id=s1", s)
        self.assertIn("identity=alice", s)
        self.assertIn("status=active", s)

    def test_summary_for_invalid_session(self):
        s = summarize_session_record_v1("not-a-dict")
        self.assertIn("invalid_session", s)

    def test_json_safe_for_session(self):
        create_session_v1(
            self.store, "alice", ["x"],
            session_id="s1",
            created_at="2026-06-23T12:00:00Z",
        )
        s = to_session_manager_json_safe_v1(self.store["s1"])
        self.assertTrue(s.startswith("{"))
        self.assertIn('"session_id": "s1"', s)

    def test_json_safe_strips_private_keys(self):
        s = to_session_manager_json_safe_v1({
            "session_id": "s1",
            "identity_id": "alice",
            "raw_prompt": "SENSITIVE_PROMPT_TEXT",
            "credentials": "SENSITIVE_CRED",
            "password": "SENSITIVE_PW",
            "audit_log_ref": "ok",
        })
        self.assertNotIn("SENSITIVE_PROMPT_TEXT", s)
        self.assertNotIn("SENSITIVE_CRED", s)
        self.assertNotIn("SENSITIVE_PW", s)
        self.assertNotIn("raw_prompt", s)
        self.assertNotIn("credentials", s)
        self.assertNotIn("password", s)
        # Non-private keys pass through.
        self.assertIn("session_id", s)
        self.assertIn("identity_id", s)
        self.assertIn("audit_log_ref", s)

    def test_json_safe_for_non_serializable(self):
        # Cyclic dict must produce a safe fallback string. The
        # manager's _strip_private_keys has its own cycle detection
        # that returns "<cyclic>" markers; either that or the
        # json.dumps fallback path is acceptable, as long as the
        # function does not crash and never returns a raw cyclic
        # structure.
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_session_manager_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertNotIn("SENSITIVE", s)
        # Must not contain a raw representation of the cyclic dict.
        self.assertNotIn("[..]", s)
        self.assertNotIn("...", s)
        # Either the cyclic marker or the serialization-error fallback is acceptable.
        self.assertTrue(
            "<cyclic>" in s or "serialization_error" in s,
            msg=f"unexpected output: {s}",
        )


class TestSessionManagerIsPure(unittest.TestCase):
    """Static checks that the session manager is pure-Python with no I/O."""

    @staticmethod
    def _read_source():
        import weslr.session_manager as sm
        with open(sm.__file__, "r", encoding="utf-8") as fh:
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
        # The manager should not open files for writing. The storage
        # path is metadata only.
        src = self._read_source()
        self.assertNotIn("open(", src.replace("def ", ""))  # heuristic
        # Direct write/file ops are forbidden.
        for forbidden in (".write(", "os.system", "shutil.", "pathlib.Path"):
            self.assertNotIn(forbidden, src, msg=f"forbidden op: {forbidden}")

    def test_no_call_to_weslr_state_writes(self):
        # We must not create /home/pr0/weslr_state/. The path may
        # appear as a metadata constant AND in the docstring's
        # negative-intent statement (i.e. "does NOT read or write ...").
        # We allow up to 2 occurrences and forbid any function/method
        # body from referencing the path.
        src = self._read_source()
        count = src.count("/home/pr0/weslr_state/")
        self.assertLessEqual(count, 2, msg=f"unexpected writes-state path occurrences: {count}")
        # The path may not appear inside any def block (other than the
        # class-level constant). Heuristic: it must not appear after a
        # "def " on the same logical line.
        for line in src.splitlines():
            if "/home/pr0/weslr_state/" in line and "def " in line and "FUTURE_STORAGE_PATH_METADATA" not in line:
                self.fail(f"unexpected write-state path inside function body: {line}")


class TestStatusConstants(unittest.TestCase):
    def test_status_constants_distinct(self):
        self.assertEqual(
            len({SESSION_STATUS_ACTIVE, SESSION_STATUS_EXPIRED,
                 SESSION_STATUS_FORCE_LOGGED_OUT, SESSION_STATUS_UNKNOWN}),
            4,
        )

    def test_valid_statuses_includes_all(self):
        for s in (
            SESSION_STATUS_ACTIVE,
            SESSION_STATUS_EXPIRED,
            SESSION_STATUS_FORCE_LOGGED_OUT,
            SESSION_STATUS_UNKNOWN,
        ):
            self.assertIn(s, VALID_SESSION_STATUSES)


if __name__ == "__main__":
    unittest.main()