"""
WESLR Contract Observation Layer V1 — Tests

Validates:
1. build_record captures response_contract
2. build_record captures interaction_frame
3. signal_type preserved from public signal/event
4. no raw message stored
5. forbidden fields rejected
6. PII-like fields rejected if present
7. valid record appends one line
8. append-only preserves existing lines
9. invalid record rejected
10. public_signals.jsonl not modified by contract observation append
11. production truth JSONL not modified
12. website integration failure does not raise
13. behavior_change_allowed always false
14. value_inference_allowed always false
15. deterministic output for same input
"""

import importlib
import json
import os
import pathlib
import sys
import tempfile
import unittest

# Ensure workspace is on path (same pattern as other Weslr tests)
_workspace = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_workspace))

# ── helpers ──────────────────────────────────────────────────────────────────

def _rel(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / path


def _clear(path: pathlib.Path) -> None:
    if path.exists():
        path.unlink()


def _count_lines(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for line in f if line.strip())


# ── reload to isolate ────────────────────────────────────────────────────────

def _reload():
    for mod in ("weslr.contract_observation", "weslr.website_signal_integration",
               "weslr.user_signal_intake", "weslr.public_signal_store"):
        try:
            m = importlib.import_module(mod)
            importlib.reload(m)
        except Exception:
            pass


# ── minimal event + interpreted fixtures ────────────────────────────────────

def _make_event(**kw):
    defaults = dict(
        session_id_hash="aabbccdd",
        message_length_bucket="medium",
        response_path="system_definition_query",
        fallback_triggered=False,
        evidence_offer_shown=False,
        evidence_offer_accepted=False,
        blocked_write=False,
        topic_normalized="weslr",
        timestamp="2026-04-30T18:00:00Z",
    )
    defaults.update(kw)
    return defaults


def _make_interpreted(**kw):
    defaults = dict(
        interaction_frame="system",
        frame_turn_type="question",
        frame_reply_shape="deterministic_answer",
        response_contract="system_answer",
        turn_type="question",
        reply_shape="deterministic_answer",
        path="system_definition_query",
    )
    defaults.update(kw)
    return defaults


# ── tests ─────────────────────────────────────────────────────────────────────

class TestBuildContractObservation(unittest.TestCase):
    """Tests 1-4, 13-15: build_contract_observation."""

    def setUp(self):
        _reload()
        from weslr.contract_observation import build_contract_observation
        self.fn = build_contract_observation

    def test_captures_response_contract(self):
        """1. build record captures response_contract."""
        event = _make_event()
        interpreted = _make_interpreted(response_contract="guided_help")
        rec = self.fn(event, interpreted)
        self.assertEqual(rec["response_contract"], "guided_help")

    def test_captures_interaction_frame(self):
        """2. build record captures interaction_frame."""
        event = _make_event()
        interpreted = _make_interpreted(interaction_frame="task_help")
        rec = self.fn(event, interpreted)
        self.assertEqual(rec["interaction_frame"], "task_help")

    def test_signal_type_preserved(self):
        """3. signal_type preserved from public signal/event."""
        # No public_signal_record → signal_type null
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.fn(event, interpreted)
        self.assertIsNone(rec["signal_type"])

        # S2 from public_signal_record
        public_record = {"signal_type": "S2"}
        rec = self.fn(event, interpreted, public_signal_record=public_record)
        self.assertEqual(rec["signal_type"], "S2")

        # S4 from public_signal_record
        rec = self.fn(event, interpreted, public_signal_record={"signal_type": "S4"})
        self.assertEqual(rec["signal_type"], "S4")

    def test_no_raw_message_stored(self):
        """4. no raw message stored."""
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.fn(event, interpreted)
        FORBIDDEN_MSG_FIELDS = frozenset({
            "message", "raw_message", "prompt", "user_input", "email",
            "phone", "address", "ip", "user_id", "name", "location",
        })
        for key, val in rec.items():
            self.assertFalse(
                key in FORBIDDEN_MSG_FIELDS,
                f"key {key} is a forbidden message field",
            )
            if isinstance(val, str):
                self.assertNotIn("i want to learn", val.lower(),
                                 f"key {key} contains raw prompt content")

    def test_behavior_change_allowed_always_false(self):
        """13. behavior_change_allowed always false."""
        event = _make_event()
        for contract in ("conversational_entry", "guided_help", "uncertainty_boundary",
                         "system_answer", "structured_explanation", "exploratory_guidance"):
            interpreted = _make_interpreted(response_contract=contract)
            rec = self.fn(event, interpreted)
            self.assertIs(rec["behavior_change_allowed"], False, contract)

    def test_value_inference_allowed_always_false(self):
        """14. value_inference_allowed always false."""
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.fn(event, interpreted)
        self.assertIs(rec["value_inference_allowed"], False)

    def test_deterministic_output(self):
        """15. deterministic output for same input."""
        event = _make_event()
        interpreted = _make_interpreted()
        rec1 = self.fn(event, interpreted)
        rec2 = self.fn(event, interpreted)
        self.assertEqual(rec1, rec2)


class TestValidateContractObservation(unittest.TestCase):
    """Tests 5-6: validate_contract_observation."""

    def setUp(self):
        _reload()
        from weslr.contract_observation import (
            build_contract_observation, validate_contract_observation,
            append_contract_observation,
        )
        self.build = build_contract_observation
        self.validate = validate_contract_observation
        self.append = append_contract_observation

    def test_rejects_missing_record_type(self):
        """5. forbidden fields — missing record_type."""
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.build(event, interpreted)
        del rec["record_type"]
        result = self.validate(rec)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "invalid_record_type")

    def test_rejects_wrong_record_type(self):
        rec = {"record_type": "public_signal_v1", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False}
        result = self.validate(rec)
        self.assertFalse(result["valid"])

    def test_rejects_safe_to_record_not_true(self):
        rec = {"record_type": "contract_observation_v1", "safe_to_record": False,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False}
        result = self.validate(rec)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "safe_to_record_not_true")

    def test_rejects_raw_prompt_stored_not_false(self):
        rec = {"record_type": "contract_observation_v1", "safe_to_record": True,
               "raw_prompt_stored": True, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False}
        result = self.validate(rec)
        self.assertFalse(result["valid"])
        self.assertIn("not_false", result["reason"])

    def test_rejects_pii_stored_not_false(self):
        rec = {"record_type": "contract_observation_v1", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": True,
               "behavior_change_allowed": False, "value_inference_allowed": False}
        result = self.validate(rec)
        self.assertFalse(result["valid"])

    def test_rejects_forbidden_fields(self):
        """6. PII-like fields rejected if present — forbidden field in record."""
        rec = {"record_type": "contract_observation_v1", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False,
               "email": "user@example.com"}
        result = self.validate(rec)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden", result["reason"])
        self.assertIn("email", result["forbidden_fields"])

    def test_rejects_nested_forbidden_field(self):
        rec = {"record_type": "contract_observation_v1", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False,
               "metadata": {"user_input": "secret"}}
        result = self.validate(rec)
        self.assertFalse(result["valid"])
        self.assertIn("metadata.user_input", result["forbidden_fields"])

    def test_pii_like_content_rejected(self):
        """6. PII-like fields rejected if present (via append PII scan)."""
        # validate_contract_observation does structural checks only.
        # PII scanning happens in append_contract_observation (step 3).
        rec = {"record_type": "contract_observation_v1", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False,
               "response_path": "contact-user@example.com", "source": "website_public",
               "response_contract": "entry", "interaction_frame": "entry",
               "turn_type": "greeting", "reply_shape": "conversational_entry",
               "signal_type": None, "timestamp": "2026-04-30T10:00:00Z",
               "session_id_hash": "aabbccdd"}
        # Append to a temp path — PII scan is in append, not validate
        tmpdir = tempfile.mkdtemp()
        try:
            obs_path = pathlib.Path(tmpdir) / "contract_observations.jsonl"
            result = self.append(rec, path=str(obs_path))
            self.assertFalse(result["stored"])
            self.assertEqual(result["reason"], "pii_like_content_detected")
        finally:
            import shutil; shutil.rmtree(tmpdir, ignore_errors=True)


class TestAppendContractObservation(unittest.TestCase):
    """Tests 7-11: append_contract_observation."""

    def setUp(self):
        _reload()
        from weslr.contract_observation import (
            build_contract_observation, validate_contract_observation,
            append_contract_observation,
        )
        self.build = build_contract_observation
        self.validate = validate_contract_observation
        self.append = append_contract_observation
        self.tmpdir = tempfile.mkdtemp()
        self.obs_path = pathlib.Path(self.tmpdir) / "contract_observations.jsonl"
        self.public_path = pathlib.Path(self.tmpdir) / "public_signals.jsonl"
        self.prod_path = pathlib.Path(self.tmpdir) / "proposal_trace.jsonl"
        # touch public_signals so it exists
        self.public_path.touch()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_record_appends_one_line(self):
        """7. valid record appends one line."""
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.build(event, interpreted)
        result = self.append(rec, path=str(self.obs_path))
        self.assertTrue(result["stored"])
        self.assertEqual(result["record_type"], "contract_observation_v1")
        self.assertEqual(_count_lines(self.obs_path), 1)

    def test_append_only_preserves_existing_lines(self):
        """8. append-only preserves existing lines."""
        self.obs_path.write_text('{"record_type": "contract_observation_v1", "safe_to_record": true, "raw_prompt_stored": false, "pii_stored": false, "behavior_change_allowed": false, "value_inference_allowed": false, "response_contract": "entry", "interaction_frame": "entry", "turn_type": "greeting", "reply_shape": "conversational_entry", "signal_type": null, "response_path": "fallback_safe", "source": "website_public", "timestamp": "2026-04-30T10:00:00Z", "session_id_hash": "existing"}}\n')
        initial = _count_lines(self.obs_path)
        event = _make_event(session_id_hash="newone")
        interpreted = _make_interpreted(response_contract="guided_help")
        rec = self.build(event, interpreted)
        result = self.append(rec, path=str(self.obs_path))
        self.assertTrue(result["stored"])
        self.assertEqual(_count_lines(self.obs_path), initial + 1)

    def test_invalid_record_rejected(self):
        """9. invalid record rejected."""
        bad = {"record_type": "wrong", "safe_to_record": True,
               "raw_prompt_stored": False, "pii_stored": False,
               "behavior_change_allowed": False, "value_inference_allowed": False}
        result = self.append(bad, path=str(self.obs_path))
        self.assertFalse(result["stored"])
        self.assertEqual(_count_lines(self.obs_path), 0)

    def test_public_signals_not_modified(self):
        """10. public_signals.jsonl not modified by contract observation append."""
        self.public_path.write_text('{"record_type": "public_signal_v1"}\n')
        initial_pub = _count_lines(self.public_path)
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.build(event, interpreted)
        self.append(rec, path=str(self.obs_path))
        self.assertEqual(_count_lines(self.public_path), initial_pub)

    def test_production_truth_jsonl_not_modified(self):
        """11. production truth JSONL not modified."""
        self.prod_path.write_text('{"type": "proposal_created"}\n')
        initial = _count_lines(self.prod_path)
        event = _make_event()
        interpreted = _make_interpreted()
        rec = self.build(event, interpreted)
        # append to contract obs should not touch proposal_trace
        result = self.append(rec, path=str(self.obs_path))
        self.assertTrue(result["stored"])
        self.assertEqual(_count_lines(self.prod_path), initial)


class TestWebsiteIntegration(unittest.TestCase):
    """Tests 12: website integration never raises."""

    def setUp(self):
        _reload()

    def test_capture_website_signal_accepts_optional_interpreted(self):
        """12. website integration failure does not raise."""
        from weslr.website_signal_integration import capture_website_signal
        import tempfile, pathlib, os

        # Use a temp dir for the jsonl path to avoid polluting workspace
        tmpdir = tempfile.mkdtemp()
        obs_file = pathlib.Path(tmpdir) / "contract_observations.jsonl"

        # patch DEFAULT_PATH temporarily
        import weslr.contract_observation as co
        orig_default = co.DEFAULT_PATH
        co.DEFAULT_PATH = str(obs_file)

        try:
            # Should not raise regardless of interpreted value
            capture_website_signal(
                message="hello",
                session_id="test-session-123",
                response_path="system_definition_query",
                quality_class="high",
                blocked_write=False,
                evidence_offer_shown=False,
                evidence_offer_accepted=False,
                topic_normalized="weslr",
                fallback_triggered=False,
                interpreted=None,  # optional — None is valid
            )
            # With actual interpreted
            capture_website_signal(
                message="help me build a website",
                session_id="test-session-456",
                response_path="task_help_query",
                quality_class="high",
                blocked_write=False,
                evidence_offer_shown=False,
                evidence_offer_accepted=False,
                topic_normalized="websites",
                fallback_triggered=False,
                interpreted={
                    "response_contract": "guided_help",
                    "interaction_frame": "task_help",
                    "turn_type": "question",
                    "reply_shape": "guided_help",
                },
            )
        finally:
            co.DEFAULT_PATH = orig_default
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("WESLR Contract Observation Layer V1 — Test Suite")
    print("=" * 60)

    # Run with pytest or unittest
    import sys
    sys.argv = [sys.argv[0]]

    unittest.main(verbosity=2)