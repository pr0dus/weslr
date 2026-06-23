"""
WESLR chat.weslr.de Slice 2 — Runtime Wrapper Tests V1

Standalone tests for the runtime wrapper skeleton. Pure-Python, no I/O,
no protected-file imports, no provider/model calls.

Run:
  python3 -m unittest weslr.tests.test_runtime_wrapper_v1 -v
"""

from __future__ import annotations

import unittest

from weslr.runtime_wrapper import (
    WRAPPER_VERSION,
    SAFE_ACTIONS_V1,
    REASON_DENY_DEFAULT,
    REASON_DENY_UNKNOWN_ACTION,
    REASON_DENY_EMPTY_CAPABILITY_SET,
    REASON_DENY_PROTECTED_FILE,
    REASON_DENY_CHATRESPONDER,
    REASON_DENY_RESPOND_CHAT,
    REASON_DENY_PROVIDER_MODEL,
    REASON_DENY_INFRA,
    REASON_DENY_MEMORY,
    REASON_DENY_PROJECT,
    REASON_DENY_PUBLIC_CLAIM,
    REASON_DENY_RUNTIME_MODIFY,
    REASON_DENY_MALFORMED_PACKET,
    DECISION_AUTHORIZED,
    DECISION_DENIED,
    DECISION_FALLBACK,
    build_runtime_authorization_request_v1,
    validate_runtime_authorization_request_v1,
    authorize_runtime_action_v1,
    summarize_runtime_authorization_result_v1,
    to_runtime_wrapper_json_safe_v1,
)


def _good_packet(action="health_check_read", caps=None):
    """Build a minimal safe-action packet for tests."""
    if caps is None:
        caps = [action]
    return build_runtime_authorization_request_v1(
        action=action,
        identity_id="test-identity",
        session_id="test-session",
        capability_set=caps,
    )


class TestBuildPacket(unittest.TestCase):
    def test_version_present(self):
        p = _good_packet()
        self.assertEqual(p["wrapper_version"], WRAPPER_VERSION)

    def test_packet_carries_no_raw_content_flags(self):
        p = _good_packet()
        # Result flags always False; raw_content_retained is set on result, not packet.
        # The packet itself must not include any raw content. Only metadata.
        self.assertIn("denied_authority", p)
        for v in p["denied_authority"].values():
            self.assertIs(v, False)

    def test_capability_set_defaulted_to_list(self):
        p = _good_packet(caps=[])
        self.assertEqual(p["capability_set"], [])

    def test_source_context_defaulted_to_dict(self):
        p = _good_packet()
        self.assertEqual(p["source_context"], {})

    def test_requested_at_optional(self):
        p = build_runtime_authorization_request_v1(
            action="status_read",
            identity_id="x",
            session_id="y",
            capability_set=["status_read"],
        )
        self.assertEqual(p["requested_at"], "")


class TestValidatePacket(unittest.TestCase):
    def test_valid_packet(self):
        ok, errs = validate_runtime_authorization_request_v1(_good_packet())
        self.assertTrue(ok, msg=f"errors: {errs}")
        self.assertEqual(errs, [])

    def test_non_dict_rejected(self):
        ok, errs = validate_runtime_authorization_request_v1("not-a-dict")
        self.assertFalse(ok)
        self.assertIn("packet_not_dict", errs)

    def test_none_rejected(self):
        ok, errs = validate_runtime_authorization_request_v1(None)
        self.assertFalse(ok)
        self.assertIn("packet_not_dict", errs)

    def test_missing_field_rejected(self):
        p = _good_packet()
        del p["denied_authority"]
        ok, errs = validate_runtime_authorization_request_v1(p)
        self.assertFalse(ok)
        self.assertTrue(any("missing_field:denied_authority" == e for e in errs))

    def test_capability_set_must_be_list(self):
        p = _good_packet()
        p["capability_set"] = "not-a-list"
        ok, errs = validate_runtime_authorization_request_v1(p)
        self.assertFalse(ok)
        self.assertIn("capability_set_not_list", errs)


class TestAuthorizeDefaults(unittest.TestCase):
    def test_empty_packet_denied(self):
        result = authorize_runtime_action_v1({})
        self.assertFalse(result["authorized"])
        self.assertEqual(result["decision"], DECISION_DENIED)
        self.assertIn(REASON_DENY_MALFORMED_PACKET, result["reason_labels"])

    def test_non_dict_packet_denied(self):
        result = authorize_runtime_action_v1("not-a-dict")
        self.assertFalse(result["authorized"])
        self.assertEqual(result["decision"], DECISION_DENIED)
        self.assertIn(REASON_DENY_MALFORMED_PACKET, result["reason_labels"])

    def test_none_packet_denied(self):
        result = authorize_runtime_action_v1(None)
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_MALFORMED_PACKET, result["reason_labels"])


class TestAuthorityFlagsDeny(unittest.TestCase):
    """Any authority flag set to True must deny."""

    def _packet_with_authority(self, flag):
        p = _good_packet()
        p["denied_authority"][flag] = True
        return p

    def test_protected_files_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_call_protected_files"))
        self.assertFalse(result["authorized"])
        self.assertEqual(result["decision"], DECISION_DENIED)
        self.assertIn(REASON_DENY_PROTECTED_FILE, result["reason_labels"])

    def test_chatresponder_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_execute_chatresponder"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_CHATRESPONDER, result["reason_labels"])

    def test_respond_chat_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_run_respond_chat"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_RESPOND_CHAT, result["reason_labels"])

    def test_provider_or_model_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_call_provider_or_model"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_PROVIDER_MODEL, result["reason_labels"])

    def test_modify_runtime_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_modify_runtime"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_RUNTIME_MODIFY, result["reason_labels"])

    def test_modify_project_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_modify_project"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_PROJECT, result["reason_labels"])

    def test_modify_memory_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_modify_memory"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_MEMORY, result["reason_labels"])

    def test_change_infra_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_change_infra"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_INFRA, result["reason_labels"])

    def test_create_public_claim_authority_denied(self):
        result = authorize_runtime_action_v1(self._packet_with_authority("can_create_public_claim"))
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_PUBLIC_CLAIM, result["reason_labels"])


class TestCapabilitySetRules(unittest.TestCase):
    def test_empty_capability_set_denied(self):
        p = _good_packet(action="health_check_read", caps=[])
        result = authorize_runtime_action_v1(p)
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_EMPTY_CAPABILITY_SET, result["reason_labels"])

    def test_action_not_in_capability_set_denied(self):
        p = _good_packet(action="health_check_read", caps=["status_read"])
        result = authorize_runtime_action_v1(p)
        self.assertFalse(result["authorized"])
        self.assertIn(REASON_DENY_EMPTY_CAPABILITY_SET, result["reason_labels"])


class TestUnknownActionFallback(unittest.TestCase):
    def test_unknown_action_returns_fallback(self):
        p = _good_packet(action="respond_chat", caps=["respond_chat"])
        result = authorize_runtime_action_v1(p)
        self.assertFalse(result["authorized"])
        self.assertEqual(result["decision"], DECISION_FALLBACK)
        self.assertIn(REASON_DENY_UNKNOWN_ACTION, result["reason_labels"])
        self.assertTrue(result["requires_operator_review"])

    def test_agi_action_returns_fallback(self):
        p = _good_packet(action="claim_agi_status", caps=["claim_agi_status"])
        result = authorize_runtime_action_v1(p)
        self.assertEqual(result["decision"], DECISION_FALLBACK)
        self.assertFalse(result["authorized"])

    def test_self_modify_returns_fallback(self):
        p = _good_packet(action="self_modify", caps=["self_modify"])
        result = authorize_runtime_action_v1(p)
        self.assertEqual(result["decision"], DECISION_FALLBACK)


class TestSafeActionsAuthorize(unittest.TestCase):
    def test_health_check_read_authorized(self):
        p = _good_packet(action="health_check_read", caps=["health_check_read"])
        result = authorize_runtime_action_v1(p)
        self.assertTrue(result["authorized"])
        self.assertEqual(result["decision"], DECISION_AUTHORIZED)
        self.assertEqual(result["reason_labels"], [])

    def test_status_read_authorized(self):
        p = _good_packet(action="status_read", caps=["status_read"])
        result = authorize_runtime_action_v1(p)
        self.assertTrue(result["authorized"])
        self.assertEqual(result["decision"], DECISION_AUTHORIZED)

    def test_operator_review_packet_read_authorized(self):
        p = _good_packet(
            action="operator_review_packet_read",
            caps=["operator_review_packet_read"],
        )
        result = authorize_runtime_action_v1(p)
        self.assertTrue(result["authorized"])
        self.assertEqual(result["decision"], DECISION_AUTHORIZED)

    def test_safe_actions_constant_matches(self):
        self.assertEqual(
            SAFE_ACTIONS_V1,
            frozenset({
                "health_check_read",
                "status_read",
                "operator_review_packet_read",
            }),
        )


class TestResultStructure(unittest.TestCase):
    def test_result_has_required_fields(self):
        p = _good_packet()
        result = authorize_runtime_action_v1(p)
        for key in (
            "wrapper_version",
            "authorized",
            "decision",
            "reason_labels",
            "safe_summary",
            "requires_operator_review",
            "denied_authority",
            "raw_content_retained",
            "protected_file_called",
            "respond_chat_called",
            "provider_or_model_called",
            "infra_changed",
            "memory_changed",
            "project_changed",
        ):
            self.assertIn(key, result)

    def test_result_never_retains_raw_content(self):
        p = _good_packet()
        result = authorize_runtime_action_v1(p)
        self.assertFalse(result["raw_content_retained"])
        self.assertFalse(result["protected_file_called"])
        self.assertFalse(result["respond_chat_called"])
        self.assertFalse(result["provider_or_model_called"])
        self.assertFalse(result["infra_changed"])
        self.assertFalse(result["memory_changed"])
        self.assertFalse(result["project_changed"])

    def test_red_zone_acknowledged_marks_operator_review(self):
        p = _good_packet()
        p["red_zone_acknowledged"] = True
        result = authorize_runtime_action_v1(p)
        self.assertTrue(result["authorized"])
        self.assertTrue(result["requires_operator_review"])

    def test_operator_token_marks_operator_review(self):
        p = _good_packet()
        p["operator_approval_token_present"] = True
        result = authorize_runtime_action_v1(p)
        self.assertTrue(result["authorized"])
        self.assertTrue(result["requires_operator_review"])


class TestSummaryAndSerialization(unittest.TestCase):
    def test_summary_for_authorized(self):
        p = _good_packet()
        result = authorize_runtime_action_v1(p)
        s = summarize_runtime_authorization_result_v1(result)
        self.assertIn("decision=authorized", s)
        self.assertIn("authorized=True", s)

    def test_summary_for_denied(self):
        result = authorize_runtime_action_v1({})
        s = summarize_runtime_authorization_result_v1(result)
        self.assertIn("decision=denied", s)

    def test_summary_for_fallback(self):
        p = _good_packet(action="unknown_action", caps=["unknown_action"])
        result = authorize_runtime_action_v1(p)
        s = summarize_runtime_authorization_result_v1(result)
        self.assertIn("decision=fallback", s)

    def test_summary_for_invalid_result(self):
        s = summarize_runtime_authorization_result_v1("not-a-dict")
        self.assertIn("invalid_result", s)

    def test_json_safe_for_dict(self):
        result = authorize_runtime_action_v1(_good_packet())
        s = to_runtime_wrapper_json_safe_v1(result)
        self.assertTrue(s.startswith("{"))
        self.assertIn('"authorized"', s)

    def test_json_safe_for_non_serializable(self):
        # Objects that JSON cannot serialize (no default support and
        # no obvious safe representation) must still produce a safe
        # JSON fallback string.
        class Bad:
            pass
        # Cyclic structure: dict references itself.
        cyclic = {}
        cyclic["self"] = cyclic
        s = to_runtime_wrapper_json_safe_v1(cyclic)
        self.assertTrue(s.startswith("{"))
        self.assertIn("serialization_error", s)


class TestWrapperIsPure(unittest.TestCase):
    """Static checks that the wrapper remains a pure-Python module with no I/O."""

    @staticmethod
    def _read_wrapper_source():
        import weslr.runtime_wrapper as rw
        with open(rw.__file__, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_no_subprocess_import(self):
        src = self._read_wrapper_source()
        self.assertNotIn("import subprocess", src)
        self.assertNotIn("from subprocess", src)

    def test_no_network_import(self):
        src = self._read_wrapper_source()
        for net in ("urllib", "requests", "httpx", "socket", "aiohttp"):
            self.assertNotIn(net, src, msg=f"unexpected network module: {net}")

    def test_no_import_of_chat_responder(self):
        # Check that there is no IMPORT statement pulling chat_responder in.
        # The wrapper's docstring may reference the term as part of its
        # negative-intent statement; we only forbid import statements.
        src = self._read_wrapper_source()
        for forbidden in (
            "import chat_responder",
            "from weslr.chat_responder",
            "from chat_responder",
            "import weslr.chat_responder",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")

    def test_no_import_of_protected_runtime_modules(self):
        src = self._read_wrapper_source()
        for forbidden in (
            "import dialogue",
            "from dialogue",
            "import weslr.dialogue",
            "from weslr.dialogue",
            "import chat_ui",
            "from chat_ui",
            "import weslr.chat_ui",
            "from weslr.chat_ui",
        ):
            self.assertNotIn(forbidden, src, msg=f"forbidden import: {forbidden}")

    def test_no_provider_or_model_import(self):
        src = self._read_wrapper_source()
        for term in ("openai", "anthropic", "ollama", "transformers", "torch"):
            self.assertNotIn(term, src, msg=f"unexpected provider module: {term}")


if __name__ == "__main__":
    unittest.main()
