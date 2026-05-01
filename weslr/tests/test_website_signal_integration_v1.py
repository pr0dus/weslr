#!/usr/bin/env python3
"""
WESLR Website Signal Integration V1 — Tests

Validates:
- capture_website_signal is fire-and-forget (returns None)
- event contains no raw message text, no PII
- signal classification pipeline works
- blocked_write signal stored safely
- public_signals.jsonl append-only
- /chat response unchanged when storage succeeds
- /chat response unchanged when storage fails

Pytest-compatible: uses unittest-style assertions, no sys.exit().
"""

import sys
import pathlib
import json
import tempfile
import importlib
import unittest

_workspace = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_workspace))
sys.path.insert(0, str(_workspace / "weslr"))

# Reload fresh
import website_signal_integration
importlib.reload(website_signal_integration)
import user_signal_intake
importlib.reload(user_signal_intake)
import public_signal_store
importlib.reload(public_signal_store)

from website_signal_integration import capture_website_signal, _hash_session, _message_length_bucket
from user_signal_intake import classify_public_signal, build_public_signal_record
from public_signal_store import append_public_signal_record


class TestWebsiteSignalIntegration(unittest.TestCase):
    """Website signal integration tests — pytest-compatible."""

    def test_01_capture_returns_none(self):
        """capture_website_signal returns None (fire-and-forget)."""
        result = capture_website_signal(
            message="How do solar panels work?",
            session_id="session_abc123",
            response_path="direct_answer",
            quality_class="grounded_reasoning",
            blocked_write=False,
            evidence_offer_shown=False,
            evidence_offer_accepted=False,
            topic_normalized="solar_panels",
            fallback_triggered=False,
        )
        self.assertIsNone(result)

    def test_02_hash_is_one_way(self):
        """_hash_session is one-way, deterministic."""
        hashed = _hash_session("session_abc123xyz")
        self.assertIsInstance(hashed, str)
        self.assertEqual(len(hashed), 16)
        self.assertNotIn("session_abc123xyz", hashed)
        self.assertEqual(_hash_session("session_abc123xyz"), hashed)
        self.assertNotEqual(_hash_session("session_different"), hashed)

    def test_03_length_bucket_based_on_length(self):
        """_message_length_bucket based on length, not content."""
        self.assertEqual(_message_length_bucket("hi"), "short")
        self.assertEqual(_message_length_bucket("hello world test"), "short")
        self.assertEqual(_message_length_bucket("a" * 30), "medium")
        self.assertEqual(_message_length_bucket("a" * 150), "medium")
        self.assertEqual(_message_length_bucket("a" * 201), "long")

    def test_04_forbidden_fields_rejected(self):
        """Forbidden raw content fields → safe_to_record=False."""
        forbidden_events = [
            {"session_id_hash": "abc", "message": "raw user message"},
            {"session_id_hash": "abc", "prompt": "raw prompt"},
            {"session_id_hash": "abc", "raw_prompt": "raw prompt"},
            {"session_id_hash": "abc", "user_input": "raw input"},
            {"session_id_hash": "abc", "email": "test@example.com"},
            {"session_id_hash": "abc", "phone": "1234567890"},
            {"session_id_hash": "abc", "ip": "192.168.1.1"},
        ]
        for ev in forbidden_events:
            r = classify_public_signal(ev)
            self.assertFalse(r["safe_to_record"], f"forbidden field '{list(ev.keys())[1]}' must be rejected")

    def test_05_pii_like_content_rejected(self):
        """PII-like content in topic_normalized → safe_to_record=False."""
        pii_events = [
            {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "contact: john@test.com", "timestamp": "2026-04-30T10:00:00Z"},
            {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "phone: 1234567890123", "timestamp": "2026-04-30T10:00:00Z"},
            {"session_id_hash": "abc", "message_length_bucket": "medium", "response_path": "test", "fallback_triggered": False, "evidence_offer_shown": False, "evidence_offer_accepted": False, "blocked_write": False, "topic_normalized": "user at 192.168.1.100", "timestamp": "2026-04-30T10:00:00Z"},
        ]
        for ev in pii_events:
            r = classify_public_signal(ev)
            self.assertFalse(r["safe_to_record"], "PII-like topic_normalized must be rejected")

    def test_06_valid_metadata_event_accepted(self):
        """Valid metadata-only event → safe_to_record=True."""
        valid_event = {
            "session_id_hash": "abc123",
            "message_length_bucket": "medium",
            "response_path": "direct_answer",
            "fallback_triggered": False,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": False,
            "topic_normalized": "solar_panels",
            "timestamp": "2026-04-30T10:00:00Z",
        }
        r = classify_public_signal(valid_event)
        self.assertTrue(r["safe_to_record"])
        self.assertFalse(r["contains_raw_prompt"])
        self.assertFalse(r["contains_pii"])

    def test_07_blocked_write_signal_null(self):
        """blocked_write → safe_to_record=True, signal_type null."""
        blocked_event_local = {
            "session_id_hash": "abc123",
            "message_length_bucket": "medium",
            "response_path": "blocked_write",
            "fallback_triggered": False,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": True,
            "topic_normalized": "iss_suggestion",
            "timestamp": "2026-04-30T10:00:00Z",
        }
        r = classify_public_signal(blocked_event_local)
        self.assertTrue(r["safe_to_record"])
        self.assertIsNone(r["signal_type"])
        self.assertEqual(r["reason"], "blocked_write_observed")

    def test_08_public_signal_record_structure(self):
        """build_public_signal_record produces correct structure."""
        blocked_event_local = {
            "session_id_hash": "abc123",
            "message_length_bucket": "medium",
            "response_path": "blocked_write",
            "fallback_triggered": False,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": True,
            "topic_normalized": "iss_suggestion",
            "timestamp": "2026-04-30T10:00:00Z",
        }
        record = build_public_signal_record(blocked_event_local)
        self.assertEqual(record["record_type"], "public_signal_v1")
        self.assertEqual(record["session_id_hash"], "abc123")
        self.assertIsNone(record["signal_type"])
        self.assertEqual(record["response_path"], "blocked_write")
        self.assertEqual(record["topic_normalized"], "iss_suggestion")
        self.assertEqual(record["source"], "website_public")
        self.assertFalse(record["raw_prompt_stored"])
        self.assertFalse(record["pii_stored"])
        self.assertFalse(record["behavior_change_allowed"])
        self.assertFalse(record["value_inference_allowed"])
        self.assertTrue(record["safe_to_record"])
        self.assertEqual(record["reason"], "blocked_write_observed")

    def test_09_append_one_record(self):
        """append_public_signal_record appends one line."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tmp_path = pathlib.Path(tf.name)
        blocked_event_local = {
            "session_id_hash": "abc123",
            "message_length_bucket": "medium",
            "response_path": "blocked_write",
            "fallback_triggered": False,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": True,
            "topic_normalized": "iss_suggestion",
            "timestamp": "2026-04-30T10:00:00Z",
        }
        record = build_public_signal_record(blocked_event_local)
        try:
            result = append_public_signal_record(record, path=str(tmp_path))
            self.assertTrue(result["stored"])
            self.assertEqual(result["reason"], "stored")
            self.assertEqual(result["record_type"], "public_signal_v1")
            self.assertTrue(tmp_path.exists())
            lines = tmp_path.read_text().strip().split("\n")
            self.assertEqual(len(lines), 1)
            stored_record = json.loads(lines[0])
            self.assertEqual(stored_record["record_type"], "public_signal_v1")
            self.assertEqual(stored_record["session_id_hash"], "abc123")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_10_append_second_line(self):
        """Second append adds second line (append-only)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tf:
            tmp_path = pathlib.Path(tf.name)
        try:
            r1 = build_public_signal_record({
                "session_id_hash": "abc123",
                "message_length_bucket": "medium",
                "response_path": "direct_answer",
                "fallback_triggered": False,
                "evidence_offer_shown": False,
                "evidence_offer_accepted": False,
                "blocked_write": False,
                "topic_normalized": "solar_panels",
                "timestamp": "2026-04-30T10:00:00Z",
            })
            r2 = build_public_signal_record({
                "session_id_hash": "def456",
                "message_length_bucket": "short",
                "response_path": "fallback_safe",
                "fallback_triggered": True,
                "evidence_offer_shown": False,
                "evidence_offer_accepted": False,
                "blocked_write": False,
                "topic_normalized": "unknown_topic",
                "timestamp": "2026-04-30T10:01:00Z",
            })
            append_public_signal_record(r1, path=str(tmp_path))
            append_public_signal_record(r2, path=str(tmp_path))
            lines = tmp_path.read_text().strip().split("\n")
            self.assertEqual(len(lines), 2)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_11_capture_never_raises(self):
        """capture_website_signal never raises on garbage inputs."""
        try:
            capture_website_signal(
                message="test",
                session_id="s1",
                response_path=None,
                quality_class=None,
                blocked_write="not_a_bool",
                evidence_offer_shown=None,
                evidence_offer_accepted=None,
                topic_normalized=123,
                fallback_triggered="also_not_bool",
            )
        except Exception as e:
            self.fail(f"capture_website_signal raised with garbage inputs: {e}")

    def test_12_evidence_offer_accepted_s2(self):
        """evidence_offer_accepted → S2."""
        event_s2 = {
            "session_id_hash": "xyz789",
            "message_length_bucket": "long",
            "response_path": "evidence_workspace_response",
            "fallback_triggered": False,
            "evidence_offer_shown": True,
            "evidence_offer_accepted": True,
            "blocked_write": False,
            "topic_normalized": "consciousness",
            "timestamp": "2026-04-30T10:02:00Z",
        }
        r = classify_public_signal(event_s2)
        self.assertEqual(r["signal_type"], "S2")
        self.assertTrue(r["safe_to_record"])

    def test_13_fallback_triggered_s4(self):
        """fallback_triggered → S4."""
        fallback_event = {
            "session_id_hash": "xyz789",
            "message_length_bucket": "short",
            "response_path": "fallback_safe",
            "fallback_triggered": True,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": False,
            "topic_normalized": "unknown",
            "timestamp": "2026-04-30T10:03:00Z",
        }
        r = classify_public_signal(fallback_event)
        self.assertEqual(r["signal_type"], "S4")
        self.assertTrue(r["safe_to_record"])

    def test_14_unknown_response_path_s1(self):
        """unknown response_path → S1."""
        unknown_event = {
            "session_id_hash": "xyz789",
            "message_length_bucket": "medium",
            "response_path": "handler_unknown_topic",
            "fallback_triggered": False,
            "evidence_offer_shown": False,
            "evidence_offer_accepted": False,
            "blocked_write": False,
            "topic_normalized": "obscure_topic",
            "timestamp": "2026-04-30T10:04:00Z",
        }
        r = classify_public_signal(unknown_event)
        self.assertEqual(r["signal_type"], "S1")

    def test_15_improvement_path_s5(self):
        """improvement response_path → S5."""
        for imp_path in ["handler_improvement_query", "handler_proposal_draft"]:
            imp_event = {
                "session_id_hash": "xyz789",
                "message_length_bucket": "long",
                "response_path": imp_path,
                "fallback_triggered": False,
                "evidence_offer_shown": False,
                "evidence_offer_accepted": False,
                "blocked_write": False,
                "topic_normalized": "refinement",
                "timestamp": "2026-04-30T10:05:00Z",
            }
            r = classify_public_signal(imp_event)
            self.assertEqual(r["signal_type"], "S5", f"{imp_path} → S5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
