from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_chat_routing import (  # noqa: E402
    ALLOWED_ATTRIBUTION_INTENTS,
    ALLOWED_CONFIDENCE_VALUES,
    ALLOWED_INPUT_CHANNELS,
    ALLOWED_PHRASE_FAMILIES,
    WhoSaidThatChatRoutingDecision,
    WhoSaidThatChatRoutingRequest,
    WhoSaidThatChatRoutingSafetyFlags,
    create_empty_who_said_that_chat_routing_decision,
    create_empty_who_said_that_chat_routing_request,
    create_empty_who_said_that_chat_routing_safety_flags,
    summarize_who_said_that_chat_routing_safety,
    validate_who_said_that_chat_routing_decision,
    validate_who_said_that_chat_routing_request,
    who_said_that_chat_routing_decision_from_dict,
    who_said_that_chat_routing_decision_to_dict,
    who_said_that_chat_routing_request_from_dict,
    who_said_that_chat_routing_request_to_dict,
    who_said_that_chat_routing_safety_flags_from_dict,
    who_said_that_chat_routing_safety_flags_to_dict,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_chat_routing.py",
    "weslr/tests/test_who_said_that_chat_routing_schema_v1.py",
}
FORBIDDEN_CHANGED_FILES = {
    "weslr/chat_responder.py",
    "weslr/runtime_chat.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/tts.py",
    "weslr/stt.py",
    "weslr/pending_messages_queue.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/voice_source_attribution_log.py",
    "weslr/voice_source_attribution.py",
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def valid_request(**overrides):
    data = {
        "request_id": "chat_req_001",
        "input_channel": "chat",
        "raw_text_stored": False,
        "message_text_hash": "sha256:msg",
        "detected_attribution_intent": "who_said_that",
        "matched_phrase_family": "who_said_that",
        "confidence": "high",
        "operator_review_required": True,
    }
    data.update(overrides)
    return create_empty_who_said_that_chat_routing_request(**data)


def valid_decision(**overrides):
    data = {
        "decision_id": "chat_decision_001",
        "request_id": "chat_req_001",
        "input_channel": "chat",
        "detected_attribution_intent": "who_said_that",
        "matched_phrase_family": "who_said_that",
        "confidence": "high",
        "should_route": True,
        "runtime_query_request_id": "runtime_req_001",
        "operator_review_required": True,
    }
    data.update(overrides)
    return create_empty_who_said_that_chat_routing_decision(**data)


class WhoSaidThatChatRoutingSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_schema_imports(self):
        self.assertTrue(WhoSaidThatChatRoutingSafetyFlags)
        self.assertTrue(WhoSaidThatChatRoutingRequest)
        self.assertTrue(WhoSaidThatChatRoutingDecision)

    def test_02_safe_defaults(self):
        flags = create_empty_who_said_that_chat_routing_safety_flags()
        request = create_empty_who_said_that_chat_routing_request()
        decision = create_empty_who_said_that_chat_routing_decision()
        self.assertFalse(flags.routing_attempted)
        self.assertFalse(request.raw_text_stored)
        self.assertFalse(decision.routing_performed)
        self.assertFalse(decision.log_write_performed)
        self.assertFalse(decision.queue_write_performed)

    def test_03_valid_request_passes(self):
        self.assertEqual([], validate_who_said_that_chat_routing_request(valid_request()))

    def test_04_valid_decision_passes(self):
        self.assertEqual([], validate_who_said_that_chat_routing_decision(valid_decision()))

    def test_05_missing_ids_fail(self):
        self.assertIn("missing request_id", validate_who_said_that_chat_routing_request(valid_request(request_id="")))
        self.assertIn("missing decision_id", validate_who_said_that_chat_routing_decision(valid_decision(decision_id="")))
        self.assertIn("missing request_id", validate_who_said_that_chat_routing_decision(valid_decision(request_id="")))

    def test_06_raw_text_storage_fails(self):
        self.assertIn("raw_text_stored true", validate_who_said_that_chat_routing_request(valid_request(raw_text_stored=True)))

    def test_07_invalid_channel_fails(self):
        self.assertIn("invalid input_channel", validate_who_said_that_chat_routing_request(valid_request(input_channel="voice")))
        self.assertIn("invalid input_channel", validate_who_said_that_chat_routing_decision(valid_decision(input_channel="voice")))

    def test_08_invalid_intent_fails(self):
        self.assertIn("invalid detected_attribution_intent", validate_who_said_that_chat_routing_request(valid_request(detected_attribution_intent="guess_owner")))
        self.assertIn("invalid detected_attribution_intent", validate_who_said_that_chat_routing_decision(valid_decision(detected_attribution_intent="guess_owner")))

    def test_09_invalid_phrase_family_fails(self):
        self.assertIn("invalid matched_phrase_family", validate_who_said_that_chat_routing_request(valid_request(matched_phrase_family="freeform_parser")))
        self.assertIn("invalid matched_phrase_family", validate_who_said_that_chat_routing_decision(valid_decision(matched_phrase_family="freeform_parser")))

    def test_10_invalid_confidence_fails(self):
        self.assertIn("invalid confidence", validate_who_said_that_chat_routing_request(valid_request(confidence="certain")))
        self.assertIn("invalid confidence", validate_who_said_that_chat_routing_decision(valid_decision(confidence="certain")))

    def test_11_allowed_enums_pass(self):
        for channel in ALLOWED_INPUT_CHANNELS:
            self.assertNotIn("invalid input_channel", validate_who_said_that_chat_routing_request(valid_request(input_channel=channel)))
        for intent in ALLOWED_ATTRIBUTION_INTENTS:
            self.assertNotIn("invalid detected_attribution_intent", validate_who_said_that_chat_routing_request(valid_request(detected_attribution_intent=intent)))
        for family in ALLOWED_PHRASE_FAMILIES:
            self.assertNotIn("invalid matched_phrase_family", validate_who_said_that_chat_routing_request(valid_request(matched_phrase_family=family)))
        for confidence in ALLOWED_CONFIDENCE_VALUES:
            self.assertNotIn("invalid confidence", validate_who_said_that_chat_routing_request(valid_request(confidence=confidence)))

    def test_12_unsafe_side_effects_fail(self):
        unsafe_fields = {
            "routing_performed": "routing performed",
            "log_read_performed": "log read performed",
            "log_write_performed": "log write performed",
            "queue_write_performed": "queue write performed",
            "memory_mutation_performed": "memory mutation performed",
            "model_advisor_call_performed": "model/advisor call performed",
            "answer_selection_performed": "answer selection performed",
            "truth_soundness_score_claimed": "truth/soundness/score claim made",
        }
        for field_name, expected in unsafe_fields.items():
            self.assertIn(expected, validate_who_said_that_chat_routing_decision(valid_decision(**{field_name: True})))

    def test_13_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required disabled", validate_who_said_that_chat_routing_request(valid_request(operator_review_required=False)))
        self.assertIn("operator_review_required disabled", validate_who_said_that_chat_routing_decision(valid_decision(operator_review_required=False)))

    def test_14_unsafe_flags_fail(self):
        flag_expectations = {
            "routing_attempted": "routing attempted",
            "chat_responder_modified": "chat responder modified",
            "runtime_integration_attempted": "runtime integration attempted",
            "voice_wiring_attempted": "voice wiring attempted",
            "log_read_attempted": "log read attempted",
            "log_write_attempted": "log write attempted",
            "queue_write_attempted": "queue write attempted",
            "memory_mutation_attempted": "memory mutation attempted",
            "model_call_attempted": "model call attempted",
            "advisor_call_attempted": "advisor call attempted",
            "answer_selection_attempted": "answer selection attempted",
            "truth_authority_claimed": "truth authority claimed",
            "soundness_authority_claimed": "soundness authority claimed",
            "score_authority_claimed": "score authority claimed",
            "official_score_claimed": "official score claimed",
            "raw_text_storage_attempted": "raw text storage attempted",
            "provenance_guessing_attempted": "provenance guessing attempted",
            "unsupported_self_ownership_claimed": "unsupported self-ownership claimed",
            "hidden_llm_authority": "hidden LLM authority",
        }
        for field_name, expected in flag_expectations.items():
            flags = WhoSaidThatChatRoutingSafetyFlags(**{field_name: True})
            self.assertIn(expected, validate_who_said_that_chat_routing_request(valid_request(safety_flags=flags)))
            self.assertIn(expected, validate_who_said_that_chat_routing_decision(valid_decision(safety_flags=flags)))

    def test_15_request_roundtrip_to_from_dict(self):
        item = valid_request(message_text_hash="sha256:abc")
        self.assertEqual(item, who_said_that_chat_routing_request_from_dict(who_said_that_chat_routing_request_to_dict(item)))

    def test_16_decision_roundtrip_to_from_dict(self):
        item = valid_decision(runtime_query_request_id="runtime_req_002")
        self.assertEqual(item, who_said_that_chat_routing_decision_from_dict(who_said_that_chat_routing_decision_to_dict(item)))

    def test_17_flags_roundtrip_to_from_dict(self):
        item = WhoSaidThatChatRoutingSafetyFlags(hidden_llm_authority=True)
        self.assertEqual(item, who_said_that_chat_routing_safety_flags_from_dict(who_said_that_chat_routing_safety_flags_to_dict(item)))

    def test_18_safety_summary_has_no_side_effects(self):
        summary = summarize_who_said_that_chat_routing_safety()
        self.assertFalse(any(summary.values()))

    def test_19_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_20_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
