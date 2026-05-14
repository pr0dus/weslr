from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_runtime_query import (  # noqa: E402
    ALLOWED_INPUT_CHANNELS,
    ALLOWED_INTENT_TYPES,
    ALLOWED_LOOKUP_MODES,
    WhoSaidThatRuntimeQueryRequest,
    WhoSaidThatRuntimeQueryResult,
    WhoSaidThatRuntimeQuerySafetyFlags,
    create_empty_who_said_that_runtime_query_request,
    create_empty_who_said_that_runtime_query_result,
    create_empty_who_said_that_runtime_query_safety_flags,
    summarize_who_said_that_runtime_query_safety,
    validate_who_said_that_runtime_query_request,
    validate_who_said_that_runtime_query_result,
    who_said_that_runtime_query_request_from_dict,
    who_said_that_runtime_query_request_to_dict,
    who_said_that_runtime_query_result_from_dict,
    who_said_that_runtime_query_result_to_dict,
    who_said_that_runtime_query_safety_flags_from_dict,
    who_said_that_runtime_query_safety_flags_to_dict,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_runtime_query.py",
    "weslr/tests/test_who_said_that_runtime_query_schema_v1.py",
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
        "request_id": "runtime_req_001",
        "input_channel": "chat",
        "raw_text_stored": False,
        "query_text_hash": "sha256:query",
        "detected_intent_type": "who_said_that",
        "lookup_mode": "most_recent",
        "routing_allowed": False,
        "operator_review_required": True,
    }
    data.update(overrides)
    return create_empty_who_said_that_runtime_query_request(**data)


def valid_result(**overrides):
    data = {
        "result_id": "runtime_result_001",
        "request_id": "runtime_req_001",
        "attribution_answer_id": "answer_001",
        "input_channel": "chat",
        "detected_intent_type": "who_said_that",
        "lookup_mode": "most_recent",
        "routing_allowed": False,
        "operator_review_required": True,
    }
    data.update(overrides)
    return create_empty_who_said_that_runtime_query_result(**data)


class WhoSaidThatRuntimeQuerySchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_schema_imports(self):
        self.assertTrue(WhoSaidThatRuntimeQuerySafetyFlags)
        self.assertTrue(WhoSaidThatRuntimeQueryRequest)
        self.assertTrue(WhoSaidThatRuntimeQueryResult)

    def test_02_safe_defaults(self):
        flags = create_empty_who_said_that_runtime_query_safety_flags()
        request = create_empty_who_said_that_runtime_query_request()
        result = create_empty_who_said_that_runtime_query_result()
        self.assertFalse(flags.runtime_integration_attempted)
        self.assertFalse(request.raw_text_stored)
        self.assertFalse(request.routing_allowed)
        self.assertFalse(result.runtime_integration_performed)
        self.assertFalse(result.log_write_performed)
        self.assertFalse(result.queue_write_performed)

    def test_03_valid_request_passes(self):
        self.assertEqual([], validate_who_said_that_runtime_query_request(valid_request()))

    def test_04_valid_result_passes(self):
        self.assertEqual([], validate_who_said_that_runtime_query_result(valid_result()))

    def test_05_missing_request_id_fails(self):
        self.assertIn("missing request_id", validate_who_said_that_runtime_query_request(valid_request(request_id="")))
        self.assertIn("missing request_id", validate_who_said_that_runtime_query_result(valid_result(request_id="")))

    def test_06_missing_result_id_fails(self):
        self.assertIn("missing result_id", validate_who_said_that_runtime_query_result(valid_result(result_id="")))

    def test_07_raw_text_storage_fails(self):
        self.assertIn("raw_text_stored true", validate_who_said_that_runtime_query_request(valid_request(raw_text_stored=True)))

    def test_08_invalid_input_channel_fails(self):
        self.assertIn("invalid input_channel", validate_who_said_that_runtime_query_request(valid_request(input_channel="websocket")))
        self.assertIn("invalid input_channel", validate_who_said_that_runtime_query_result(valid_result(input_channel="websocket")))

    def test_09_invalid_intent_fails(self):
        self.assertIn("invalid detected_intent_type", validate_who_said_that_runtime_query_request(valid_request(detected_intent_type="parse_everything")))
        self.assertIn("invalid detected_intent_type", validate_who_said_that_runtime_query_result(valid_result(detected_intent_type="parse_everything")))

    def test_10_invalid_lookup_mode_fails(self):
        self.assertIn("invalid lookup_mode", validate_who_said_that_runtime_query_request(valid_request(lookup_mode="scan_logs")))
        self.assertIn("invalid lookup_mode", validate_who_said_that_runtime_query_result(valid_result(lookup_mode="scan_logs")))

    def test_11_allowed_enums_pass(self):
        for channel in ALLOWED_INPUT_CHANNELS:
            self.assertNotIn("invalid input_channel", validate_who_said_that_runtime_query_request(valid_request(input_channel=channel)))
        for intent in ALLOWED_INTENT_TYPES:
            self.assertNotIn("invalid detected_intent_type", validate_who_said_that_runtime_query_request(valid_request(detected_intent_type=intent)))
        for mode in ALLOWED_LOOKUP_MODES:
            kwargs = {"lookup_mode": mode}
            if mode == "by_utterance_id":
                kwargs["requested_utterance_id"] = "utt_001"
            if mode == "by_trace_ref":
                kwargs["requested_trace_ref"] = "trace_001"
            self.assertNotIn("invalid lookup_mode", validate_who_said_that_runtime_query_request(valid_request(**kwargs)))

    def test_12_lookup_modes_require_identifiers(self):
        self.assertIn("by_utterance_id requires requested_utterance_id", validate_who_said_that_runtime_query_request(valid_request(lookup_mode="by_utterance_id")))
        self.assertIn("by_trace_ref requires requested_trace_ref", validate_who_said_that_runtime_query_request(valid_request(lookup_mode="by_trace_ref")))

    def test_13_unsafe_side_effects_fail(self):
        unsafe_result_fields = {
            "runtime_integration_performed": "runtime integration performed",
            "log_read_performed": "log read performed",
            "log_write_performed": "log write performed",
            "queue_write_performed": "queue write performed",
            "memory_mutation_performed": "memory mutation performed",
            "model_advisor_call_performed": "model/advisor call performed",
            "answer_selection_performed": "answer selection performed",
            "truth_soundness_score_claimed": "truth/soundness/score claim made",
        }
        for field_name, expected in unsafe_result_fields.items():
            self.assertIn(expected, validate_who_said_that_runtime_query_result(valid_result(**{field_name: True})))

    def test_14_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required disabled", validate_who_said_that_runtime_query_request(valid_request(operator_review_required=False)))
        self.assertIn("operator_review_required disabled", validate_who_said_that_runtime_query_result(valid_result(operator_review_required=False)))

    def test_15_unsafe_flags_fail(self):
        flag_expectations = {
            "runtime_integration_attempted": "runtime integration attempted",
            "chat_wiring_attempted": "chat wiring attempted",
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
            flags = WhoSaidThatRuntimeQuerySafetyFlags(**{field_name: True})
            self.assertIn(expected, validate_who_said_that_runtime_query_request(valid_request(safety_flags=flags)))
            self.assertIn(expected, validate_who_said_that_runtime_query_result(valid_result(safety_flags=flags)))

    def test_16_request_roundtrip_to_from_dict(self):
        item = valid_request(lookup_mode="by_trace_ref", requested_trace_ref="trace_001")
        self.assertEqual(item, who_said_that_runtime_query_request_from_dict(who_said_that_runtime_query_request_to_dict(item)))

    def test_17_result_roundtrip_to_from_dict(self):
        item = valid_result(attribution_answer_id="answer_002")
        self.assertEqual(item, who_said_that_runtime_query_result_from_dict(who_said_that_runtime_query_result_to_dict(item)))

    def test_18_flags_roundtrip_to_from_dict(self):
        item = WhoSaidThatRuntimeQuerySafetyFlags(hidden_llm_authority=True)
        self.assertEqual(item, who_said_that_runtime_query_safety_flags_from_dict(who_said_that_runtime_query_safety_flags_to_dict(item)))

    def test_19_safety_summary_has_no_side_effects(self):
        summary = summarize_who_said_that_runtime_query_safety()
        self.assertFalse(any(summary.values()))

    def test_20_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_21_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
