from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_chat_routing import (  # noqa: E402
    WhoSaidThatChatRoutingSafetyFlags,
    classify_who_said_that_phrase_family,
    create_chat_routing_decision_from_request,
    create_chat_routing_request_from_metadata,
    summarize_chat_routing_decision,
    summarize_chat_routing_decisions,
    validate_who_said_that_chat_routing_decision,
    validate_who_said_that_chat_routing_request,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_chat_routing.py",
    "weslr/tests/test_who_said_that_chat_routing_helpers_v1.py",
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


def request(**overrides):
    data = {
        "request_id": "chat_req_001",
        "input_channel": "chat",
        "message_text_hash": "sha256:msg",
        "matched_phrase_family": "who_said_that",
        "detected_attribution_intent": "who_said_that",
        "confidence": "high",
    }
    data.update(overrides)
    return create_chat_routing_request_from_metadata(**data)


class WhoSaidThatChatRoutingHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_imports(self):
        self.assertTrue(create_chat_routing_request_from_metadata)
        self.assertTrue(classify_who_said_that_phrase_family)
        self.assertTrue(create_chat_routing_decision_from_request)
        self.assertTrue(summarize_chat_routing_decision)
        self.assertTrue(summarize_chat_routing_decisions)

    def test_02_valid_metadata_creates_request(self):
        item = request()
        self.assertEqual("chat_req_001", item.request_id)
        self.assertEqual("chat", item.input_channel)
        self.assertEqual("sha256:msg", item.message_text_hash)
        self.assertEqual("who_said_that", item.detected_attribution_intent)
        self.assertEqual([], validate_who_said_that_chat_routing_request(item))

    def test_03_raw_text_is_not_stored(self):
        item = request()
        self.assertFalse(item.raw_text_stored)
        self.assertFalse(hasattr(item, "raw_text"))
        self.assertFalse(hasattr(item, "message_text"))
        with self.assertRaises(ValueError):
            create_chat_routing_request_from_metadata(request_id="raw", input_channel="chat", message_text_hash="sha256:x", raw_text="who said that?")

    def test_04_phrase_family_detection_who_said_that(self):
        self.assertEqual("who_said_that", classify_who_said_that_phrase_family("who said that?"))

    def test_05_phrase_family_detection_llm(self):
        self.assertEqual("was_llm_involved", classify_who_said_that_phrase_family("was an LLM involved?"))

    def test_06_phrase_family_detection_what_generated(self):
        self.assertEqual("what_generated_that", classify_who_said_that_phrase_family("what generated that?"))

    def test_07_supported_phrase_families(self):
        examples = {
            "what triggered that?": "what_triggered_that",
            "why did you say that?": "why_did_you_say_that",
            "was that WESLR?": "was_that_weslr_owned",
            "show last voice attribution": "show_last_voice_attribution",
        }
        for text, expected in examples.items():
            self.assertEqual(expected, classify_who_said_that_phrase_family(text))

    def test_08_unclear_text_returns_unknown_no_route(self):
        family = classify_who_said_that_phrase_family("please continue the task")
        item = request(matched_phrase_family=family, detected_attribution_intent="unknown", confidence="unknown")
        decision = create_chat_routing_decision_from_request(item, "decision_unknown")
        self.assertEqual("unknown", family)
        self.assertFalse(decision.should_route)
        self.assertEqual("", decision.runtime_query_request_id)

    def test_09_clear_attribution_intent_creates_route_decision(self):
        item = request()
        decision = create_chat_routing_decision_from_request(item, "decision_route", runtime_query_request_id="runtime_req_001")
        self.assertTrue(decision.should_route)
        self.assertEqual("runtime_req_001", decision.runtime_query_request_id)
        self.assertEqual([], validate_who_said_that_chat_routing_decision(decision))

    def test_10_route_decision_does_not_perform_routing(self):
        decision = create_chat_routing_decision_from_request(request(), "decision_no_route_performed", runtime_query_request_id="runtime_req_001")
        self.assertFalse(decision.routing_performed)
        self.assertFalse(decision.log_read_performed)
        self.assertFalse(decision.log_write_performed)
        self.assertFalse(decision.queue_write_performed)
        self.assertFalse(decision.memory_mutation_performed)
        self.assertFalse(decision.model_advisor_call_performed)
        self.assertFalse(decision.answer_selection_performed)
        self.assertFalse(decision.truth_soundness_score_claimed)

    def test_11_unsafe_side_effect_flags_remain_false(self):
        decision = create_chat_routing_decision_from_request(request(), "decision_safe", runtime_query_request_id="runtime_req_001")
        summary = summarize_chat_routing_decision(decision)
        self.assertFalse(summary["routing_performed"])
        self.assertFalse(summary["log_read_performed"])
        self.assertFalse(summary["log_write_performed"])
        self.assertFalse(summary["queue_write_performed"])
        self.assertFalse(summary["memory_mutation_performed"])
        self.assertFalse(summary["model_advisor_call_performed"])
        self.assertFalse(summary["answer_selection_performed"])
        self.assertFalse(summary["truth_soundness_score_claimed"])

    def test_12_invalid_metadata_fails_safely(self):
        with self.assertRaises(ValueError):
            request(input_channel="voice")
        with self.assertRaises(ValueError):
            request(matched_phrase_family="freeform")
        with self.assertRaises(ValueError):
            request(confidence="certain")
        with self.assertRaises(ValueError):
            request(safety_flags=WhoSaidThatChatRoutingSafetyFlags(log_read_attempted=True))

    def test_13_summaries_are_redacted_count_only(self):
        routed = create_chat_routing_decision_from_request(request(), "secret-decision-token", runtime_query_request_id="secret-runtime-token")
        unknown_request = request(request_id="chat_req_002", matched_phrase_family="unknown", detected_attribution_intent="unknown", confidence="unknown")
        unknown = create_chat_routing_decision_from_request(unknown_request, "decision_unknown")
        one = summarize_chat_routing_decision(routed)
        many = summarize_chat_routing_decisions([routed, unknown])
        rendered = json.dumps({"one": one, "many": many}, sort_keys=True).lower()
        self.assertNotIn("secret-decision-token", rendered)
        self.assertNotIn("secret-runtime-token", rendered)
        self.assertEqual("redacted_count_only", one["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["decision_count"])
        self.assertEqual(1, many["route_count"])
        self.assertEqual(1, many["no_route_count"])

    def test_14_no_side_effects_in_aggregate_summary(self):
        summary = summarize_chat_routing_decisions([create_chat_routing_decision_from_request(request(), "decision_route")])
        self.assertFalse(summary["routing_performed"])
        self.assertFalse(summary["log_reads_performed"])
        self.assertFalse(summary["log_writes_performed"])
        self.assertFalse(summary["queue_writes_performed"])
        self.assertFalse(summary["memory_mutations_performed"])
        self.assertFalse(summary["model_advisor_calls_performed"])
        self.assertFalse(summary["answer_selection_performed"])
        self.assertFalse(summary["truth_soundness_score_claimed"])

    def test_15_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_16_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
