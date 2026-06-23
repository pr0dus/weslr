"""
WESLR chat.weslr.de Slice 4B — Audit Log Persistence Helper Tests V1

Standalone tests for the JSONL persistence helper. Uses
tempfile.TemporaryDirectory for all file I/O — no real production
write paths are ever touched. Pure-Python, no network, no
subprocess, no protected-file imports, no provider/model calls.

Run:
  python3 -m unittest weslr.tests.test_audit_log_persistence_v1 -v
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import weslr.audit_log as al
import weslr.audit_log_persistence as alp
from weslr.audit_log_persistence import (
    FUTURE_PRODUCTION_LOG_STORAGE_PATH,
    DEFAULT_MAX_READ_LIMIT,
    build_audit_log_persistence_request_v1,
    validate_audit_log_persistence_request_v1,
    append_audit_event_jsonl_v1,
    read_audit_events_jsonl_v1,
    summarize_audit_log_persistence_request_v1,
    to_audit_log_persistence_json_safe_v1,
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
    entry_id="e-1",
    recorded_at="2026-06-23T20:00:00Z",
    raw_content_retained=False,
    never_includes=None,
    reason_labels=None,
):
    return al.build_audit_event_v1(
        audit_log_action_type=action_type,
        audit_log_operator_ref=operator_ref,
        audit_log_target_account_id=account_id,
        audit_log_target_session_id=session_id,
        audit_log_before_state=before,
        audit_log_after_state=after,
        audit_log_reason_label=reason_label,
        audit_log_summary=summary,
        audit_log_entry_id=entry_id,
        audit_log_recorded_at=recorded_at,
    )


class TestBuildRequest(unittest.TestCase):
    def test_version_present(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        self.assertEqual(r["persistence_version"], "weslr-audit-log-persistence-v1")

    def test_request_id_auto_uuid(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        self.assertEqual(len(r["request_id"]), 36)

    def test_path_propagated(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/foo.jsonl")
        self.assertEqual(r["log_file_path"], "/tmp/foo.jsonl")

    def test_operator_ref_propagated(self):
        r = build_audit_log_persistence_request_v1(
            log_file_path="/tmp/x.jsonl", operator_ref="op-1"
        )
        self.assertEqual(r["operator_ref"], "op-1")

    def test_future_production_path_metadata_present(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        self.assertEqual(r["future_production_storage_path_metadata"], FUTURE_PRODUCTION_LOG_STORAGE_PATH)


class TestValidateRequest(unittest.TestCase):
    def test_valid_request_passes(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertTrue(ok, msg=f"errors: {errs}")
        self.assertEqual(errs, [])

    def test_non_dict_rejected(self):
        ok, errs = validate_audit_log_persistence_request_v1("not-a-dict")
        self.assertFalse(ok)
        # Non-dict always returns a single-element error list with the
        # not-dict label, before any path-specific check runs.
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0], al.REASON_INVALID_NOT_DICT)

    def test_empty_path_rejected(self):
        r = build_audit_log_persistence_request_v1(log_file_path="")
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("path_not_provided" in e for e in errs))

    def test_none_path_rejected(self):
        r = build_audit_log_persistence_request_v1(log_file_path="")
        r["log_file_path"] = None
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("path_not_provided" in e for e in errs))

    def test_production_path_rejected(self):
        r = build_audit_log_persistence_request_v1(log_file_path=FUTURE_PRODUCTION_LOG_STORAGE_PATH)
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("path_forbidden_production" in e for e in errs))

    def test_null_byte_path_rejected(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x\x00.jsonl")
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("null_byte" in e for e in errs))

    def test_missing_field_rejected(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        del r["log_file_path"]
        ok, errs = validate_audit_log_persistence_request_v1(r)
        self.assertFalse(ok)
        self.assertTrue(any("missing_required_fields:log_file_path" in e for e in errs))


class TestAppendAndRead(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _path(self, name="audit.jsonl"):
        return os.path.join(self.tmpdir, name)

    def _req(self, name="audit.jsonl"):
        return build_audit_log_persistence_request_v1(log_file_path=self._path(name))

    def test_append_creates_file_and_writes_one_line(self):
        e = _make_event(entry_id="e-1")
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertTrue(result["ok"], msg=result)
        p = self._path()
        self.assertTrue(os.path.exists(p))
        with open(p, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["audit_log_entry_id"], "e-1")

    def test_append_appends_in_order(self):
        for i in range(3):
            e = _make_event(entry_id=f"e-{i}")
            result = append_audit_event_jsonl_v1(self._req(), e)
            self.assertTrue(result["ok"], msg=result)
        with open(self._path(), "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(len(lines), 3)
        ids = [json.loads(l)["audit_log_entry_id"] for l in lines]
        self.assertEqual(ids, ["e-0", "e-1", "e-2"])

    def test_append_rejects_event_with_top_level_forbidden_key(self):
        e = _make_event()
        e["raw_prompt"] = "SENSITIVE"
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("never_includes_key" in e2 for e2 in result["reason_labels"]))
        self.assertFalse(os.path.exists(self._path()))

    def test_append_rejects_event_with_nested_forbidden_key_in_before_state(self):
        e = _make_event(before={"raw_prompt": "SENSITIVE"})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("never_includes_key" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_event_with_nested_forbidden_key_in_after_state(self):
        e = _make_event(after={"api_key": "SECRET"})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("never_includes_key" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_event_with_password(self):
        e = _make_event(before={"password": "NESTED"})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("password" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_event_with_secret(self):
        e = _make_event(after={"secret": "NESTED"})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("secret" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_event_with_api_key(self):
        e = _make_event(before={"api_key": "NESTED"})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("api_key" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_event_with_forbidden_key_in_list(self):
        e = _make_event(before={"events": [{"name": "x", "chain_of_thought": "TRACE"}]})
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("chain_of_thought" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_unknown_action_type(self):
        e = _make_event(action_type="not_a_real_category")
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertFalse(os.path.exists(self._path()))

    def test_append_rejects_event_version_mismatch(self):
        e = _make_event()
        e["audit_log_version"] = "weslr-audit-log-v999"
        result = append_audit_event_jsonl_v1(self._req(), e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("version_mismatch" in e2 for e2 in result["reason_labels"]))

    def test_append_rejects_invalid_request(self):
        bad = {"some": "junk"}  # missing required fields
        e = _make_event()
        result = append_audit_event_jsonl_v1(bad, e)
        self.assertFalse(result["ok"])

    def test_append_refuses_production_path_even_with_valid_event(self):
        e = _make_event()
        bad_req = build_audit_log_persistence_request_v1(
            log_file_path=FUTURE_PRODUCTION_LOG_STORAGE_PATH
        )
        result = append_audit_event_jsonl_v1(bad_req, e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("path_forbidden_production" in e2 for e2 in result["reason_labels"]))

    def test_append_refuses_when_parent_directory_does_not_exist(self):
        e = _make_event()
        bad_req = build_audit_log_persistence_request_v1(
            log_file_path=os.path.join(self.tmpdir, "no_such_dir", "audit.jsonl")
        )
        result = append_audit_event_jsonl_v1(bad_req, e)
        self.assertFalse(result["ok"])
        self.assertTrue(any("parent_directory" in e2 for e2 in result["reason_labels"]))

    def test_read_returns_zero_for_missing_file(self):
        result = read_audit_events_jsonl_v1(self._req())
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["events"], [])

    def test_read_all_when_no_filters(self):
        for i in range(3):
            e = _make_event(entry_id=f"e-{i}")
            append_audit_event_jsonl_v1(self._req(), e)
        result = read_audit_events_jsonl_v1(self._req())
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 3)

    def test_read_filter_by_account_id(self):
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="a", entry_id="e1"))
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="b", entry_id="e2"))
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="a", entry_id="e3"))
        result = read_audit_events_jsonl_v1(self._req(), account_id="a")
        self.assertEqual(result["count"], 2)
        for ev in result["events"]:
            self.assertEqual(ev["audit_log_target_account_id"], "a")

    def test_read_filter_by_session_id(self):
        append_audit_event_jsonl_v1(self._req(), _make_event(session_id="s1", entry_id="e1"))
        append_audit_event_jsonl_v1(self._req(), _make_event(session_id="s2", entry_id="e2"))
        append_audit_event_jsonl_v1(self._req(), _make_event(session_id="s1", entry_id="e3"))
        result = read_audit_events_jsonl_v1(self._req(), session_id="s1")
        self.assertEqual(result["count"], 2)

    def test_read_filter_by_action_type(self):
        append_audit_event_jsonl_v1(self._req(), _make_event(action_type="user_created", entry_id="e1"))
        append_audit_event_jsonl_v1(self._req(), _make_event(action_type="session_created", entry_id="e2"))
        append_audit_event_jsonl_v1(self._req(), _make_event(action_type="user_created", entry_id="e3"))
        result = read_audit_events_jsonl_v1(self._req(), action_type="user_created")
        self.assertEqual(result["count"], 2)
        for ev in result["events"]:
            self.assertEqual(ev["audit_log_action_type"], "user_created")

    def test_read_combined_filters(self):
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="a", action_type="user_created", entry_id="e1"))
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="a", action_type="session_created", entry_id="e2"))
        append_audit_event_jsonl_v1(self._req(), _make_event(account_id="b", action_type="user_created", entry_id="e3"))
        result = read_audit_events_jsonl_v1(
            self._req(), account_id="a", action_type="user_created"
        )
        self.assertEqual(result["count"], 1)

    def test_read_with_limit(self):
        for i in range(5):
            append_audit_event_jsonl_v1(self._req(), _make_event(entry_id=f"e-{i}"))
        result = read_audit_events_jsonl_v1(self._req(), limit=2)
        self.assertEqual(result["count"], 2)

    def test_read_rejects_limit_too_large(self):
        result = read_audit_events_jsonl_v1(self._req(), limit=DEFAULT_MAX_READ_LIMIT + 1)
        self.assertFalse(result["ok"])
        self.assertTrue(any("limit_too_large" in e2 for e2 in result["reason_labels"]))

    def test_read_rejects_negative_limit(self):
        result = read_audit_events_jsonl_v1(self._req(), limit=-1)
        self.assertFalse(result["ok"])

    def test_read_refuses_production_path(self):
        bad_req = build_audit_log_persistence_request_v1(
            log_file_path=FUTURE_PRODUCTION_LOG_STORAGE_PATH
        )
        result = read_audit_events_jsonl_v1(bad_req)
        self.assertFalse(result["ok"])
        self.assertTrue(any("path_forbidden_production" in e2 for e2 in result["reason_labels"]))

    def test_read_skips_malformed_lines(self):
        # Write a valid event, then a malformed line, then another valid event.
        append_audit_event_jsonl_v1(self._req(), _make_event(entry_id="e-1"))
        with open(self._path(), "a", encoding="utf-8") as fh:
            fh.write("not valid json\n")
        append_audit_event_jsonl_v1(self._req(), _make_event(entry_id="e-2"))
        result = read_audit_events_jsonl_v1(self._req())
        # Malformed line is skipped; only 2 valid events remain.
        self.assertEqual(result["count"], 2)
        ids = [ev["audit_log_entry_id"] for ev in result["events"]]
        self.assertEqual(ids, ["e-1", "e-2"])


class TestSummaryAndSerialization(unittest.TestCase):
    def test_summary_for_valid_request(self):
        r = build_audit_log_persistence_request_v1(
            log_file_path="/tmp/foo.jsonl", operator_ref="op-1"
        )
        s = summarize_audit_log_persistence_request_v1(r)
        self.assertIn("op-1", s)
        self.assertIn("/tmp/foo.jsonl", s)

    def test_summary_for_invalid_request(self):
        s = summarize_audit_log_persistence_request_v1("not-a-dict")
        self.assertIn("invalid_persistence_request", s)

    def test_json_safe_for_request(self):
        r = build_audit_log_persistence_request_v1(log_file_path="/tmp/x.jsonl")
        s = to_audit_log_persistence_json_safe_v1(r)
        self.assertTrue(s.startswith("{"))
        self.assertIn('"persistence_version": "weslr-audit-log-persistence-v1"', s)

    def test_json_safe_strips_forbidden_keys_in_event(self):
        e = {
            "audit_log_entry_id": "x",
            "audit_log_version": al.AUDIT_LOG_VERSION,
            "raw_prompt": "SENSITIVE_PROMPT",
            "raw_reply": "SENSITIVE_REPLY",
            "credentials": "SENSITIVE_CRED",
            "password": "PWD",
            "secret": "SEC",
            "api_key": "KEY",
            "hidden_prompt": "HIDDEN",
            "shadow_call_output": "TRACE",
            "chain_of_thought": "COT",
            "system_prompt": "SYS",
            "provider_response": "PROV",
            "session_token_plaintext": "TOK",
            "audit_log_action_type": "user_created",
            "audit_log_operator_ref": "op-1",
        }
        s = to_audit_log_persistence_json_safe_v1(e)
        for forbidden in ("SENSITIVE_PROMPT", "SENSITIVE_REPLY", "SENSITIVE_CRED",
                          "PWD", "SEC", "KEY", "HIDDEN", "TRACE", "COT",
                          "SYS", "PROV", "TOK"):
            self.assertNotIn(forbidden, s, msg=f"forbidden key leaked: {forbidden}")
        for key in ("raw_prompt", "raw_reply", "credentials", "password", "secret",
                    "api_key", "hidden_prompt", "shadow_call_output",
                    "chain_of_thought", "system_prompt", "provider_response",
                    "session_token_plaintext"):
            self.assertNotIn(f'"{key}"', s, msg=f"forbidden key name leaked: {key}")

    def test_json_safe_for_cyclic(self):
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_audit_log_persistence_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertTrue("<cyclic>" in s or "serialization_error" in s)


class TestImportSurface(unittest.TestCase):
    """Verify the persistence module imports only what was promised."""

    def test_imports_only_from_weslr_audit_log(self):
        import weslr.audit_log_persistence as alp
        import inspect
        src = inspect.getsource(alp)
        # Module-level imports must be limited to safe targets.
        # The only allowed cross-module dependency is weslr.audit_log.
        self.assertIn("from weslr.audit_log import", src)
        # Disallowed cross-module imports.
        for forbidden in (
            "from weslr.chat_responder",
            "from weslr.dialogue",
            "from weslr.chat_ui",
            "from weslr.runtime_wrapper",
            "from weslr.session_manager",
            "import openai",
            "import anthropic",
            "import ollama",
            "import transformers",
            "import torch",
            "import urllib",
            "import requests",
            "import httpx",
            "import socket",
            "import aiohttp",
            "import subprocess",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")


class TestPurityOfPersistenceModule(unittest.TestCase):
    """The persistence module does not import protected runtime modules
    or provider/model/network/subprocess modules."""

    @staticmethod
    def _read_source():
        import weslr.audit_log_persistence as alp
        with open(alp.__file__, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_no_subprocess_import(self):
        src = self._read_source()
        # subprocess is allowed in the `import os` sense; this is a static
        # check that we don't use the `subprocess` module.
        self.assertNotIn("import subprocess", src)
        self.assertNotIn("from subprocess", src)

    def test_no_provider_or_model_import(self):
        src = self._read_source()
        for term in ("openai", "anthropic", "ollama", "transformers", "torch"):
            self.assertNotIn(term, src, msg=f"unexpected provider module: {term}")

    def test_no_network_import(self):
        src = self._read_source()
        for net in ("urllib", "requests", "httpx", "socket", "aiohttp"):
            self.assertNotIn(net, src, msg=f"unexpected network module: {net}")

    def test_no_protected_runtime_import(self):
        src = self._read_source()
        for forbidden in (
            "import weslr.chat_responder",
            "from weslr.chat_responder",
            "import weslr.dialogue",
            "from weslr.dialogue",
            "import weslr.chat_ui",
            "from weslr.chat_ui",
            "import weslr.runtime_wrapper",
            "from weslr.runtime_wrapper",
            "import weslr.session_manager",
            "from weslr.session_manager",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")


class TestNoProductionWrite(unittest.TestCase):
    """The persistence module must NOT write to the production future-storage path."""

    def test_module_uses_future_path_only_as_constant_metadata(self):
        import weslr.audit_log_persistence as alp
        import inspect
        src = inspect.getsource(alp)
        # The future production path is a constant assignment.
        self.assertIn("FUTURE_PRODUCTION_LOG_STORAGE_PATH", src)
        # The path appears at least once (the constant) and at most a
        # handful of times (constant + check + log message).
        count = src.count("/home/pr0/weslr_state/")
        self.assertLessEqual(count, 5, msg=f"too many refs: {count}")

    def test_no_real_writes_outside_caller_controlled_path(self):
        # Build a request with a path that does NOT match the
        # production future-storage path; append should succeed in
        # the caller's tempdir; the future-storage path must remain
        # absent.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "audit.jsonl")
            req = build_audit_log_persistence_request_v1(log_file_path=path)
            e = _make_event(entry_id="e-1")
            result = append_audit_event_jsonl_v1(req, e)
            self.assertTrue(result["ok"], msg=result)
            self.assertTrue(os.path.exists(path))
        # The production path must never have been written.
        self.assertFalse(
            os.path.exists("/home/pr0/weslr_state/logs/"),
            msg="production future-storage path must not exist",
        )


if __name__ == "__main__":
    unittest.main()