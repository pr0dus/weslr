from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_runtime_query import (  # noqa: E402
    WhoSaidThatRuntimeQueryResult,
    WhoSaidThatRuntimeQuerySafetyFlags,
    create_missing_runtime_query_result,
    create_runtime_query_request_from_metadata,
    create_runtime_query_result_from_answer,
    summarize_runtime_query_result,
    summarize_runtime_query_results,
    validate_who_said_that_runtime_query_request,
    validate_who_said_that_runtime_query_result,
)
from weslr.who_said_that_query_surface import create_empty_who_said_that_answer  # noqa: E402

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_runtime_query.py",
    "weslr/tests/test_who_said_that_runtime_query_helpers_v1.py",
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
        "request_id": "runtime_req_001",
        "input_channel": "chat",
        "query_text_hash": "sha256:who-said-that",
        "detected_intent_type": "who_said_that",
        "lookup_mode": "most_recent",
    }
    data.update(overrides)
    return create_runtime_query_request_from_metadata(**data)


def answer(**overrides):
    data = {
        "answer_id": "answer_001",
        "query_id": "query_001",
        "intent_type": "who_said_that",
        "attribution_found": True,
        "ownership_category": "operator_triggered",
        "source_subsystem": "operator_cli",
        "trigger_type": "operator_action",
        "authority_level": "observed_event",
        "truth_class": "observed",
        "confidence": "medium",
        "trace_ref_count": 1,
        "operator_review_required": True,
    }
    data.update(overrides)
    return create_empty_who_said_that_answer(**data)


class WhoSaidThatRuntimeQueryHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_imports(self):
        self.assertTrue(create_runtime_query_request_from_metadata)
        self.assertTrue(create_runtime_query_result_from_answer)
        self.assertTrue(create_missing_runtime_query_result)
        self.assertTrue(summarize_runtime_query_result)
        self.assertTrue(summarize_runtime_query_results)

    def test_02_valid_metadata_creates_request(self):
        item = request()
        self.assertEqual("runtime_req_001", item.request_id)
        self.assertEqual("chat", item.input_channel)
        self.assertEqual("sha256:who-said-that", item.query_text_hash)
        self.assertEqual("who_said_that", item.detected_intent_type)
        self.assertEqual([], validate_who_said_that_runtime_query_request(item))

    def test_03_raw_text_is_not_stored(self):
        item = request()
        self.assertFalse(item.raw_text_stored)
        self.assertFalse(hasattr(item, "raw_text"))
        with self.assertRaises(ValueError):
            create_runtime_query_request_from_metadata(request_id="req_raw", input_channel="chat", query_text_hash="sha256:x", raw_text="who said that?")

    def test_04_missing_attribution_creates_safe_result(self):
        result = create_missing_runtime_query_result(request(), "result_missing")
        self.assertEqual("", result.attribution_answer_id)
        self.assertFalse(result.routing_allowed)
        self.assertTrue(result.operator_review_required)
        self.assertEqual([], validate_who_said_that_runtime_query_result(result))
        self.assertFalse(result.runtime_integration_performed)
        self.assertFalse(result.log_read_performed)
        self.assertFalse(result.log_write_performed)
        self.assertFalse(result.queue_write_performed)
        self.assertFalse(result.memory_mutation_performed)
        self.assertFalse(result.model_advisor_call_performed)

    def test_05_result_from_answer_preserves_attribution_answer_id(self):
        result = create_runtime_query_result_from_answer(request(), answer(answer_id="answer_preserved"), "result_001")
        self.assertEqual("answer_preserved", result.attribution_answer_id)
        self.assertEqual("runtime_req_001", result.request_id)
        self.assertEqual([], validate_who_said_that_runtime_query_result(result))

    def test_06_result_from_answer_accepts_dict_answer(self):
        result = create_runtime_query_result_from_answer(request(), {"answer_id": "answer_dict", "operator_review_required": True}, "result_dict")
        self.assertEqual("answer_dict", result.attribution_answer_id)

    def test_07_invalid_metadata_fails_safely(self):
        with self.assertRaises(ValueError):
            request(input_channel="runtime_socket")
        with self.assertRaises(ValueError):
            request(detected_intent_type="guess_owner")
        with self.assertRaises(ValueError):
            request(lookup_mode="scan_all_logs")
        with self.assertRaises(ValueError):
            request(lookup_mode="by_utterance_id")

    def test_08_unsafe_flags_fail_safely(self):
        with self.assertRaises(ValueError):
            request(safety_flags=WhoSaidThatRuntimeQuerySafetyFlags(log_read_attempted=True))
        with self.assertRaises(ValueError):
            create_missing_runtime_query_result(request(), "result_bad", safety_flags=WhoSaidThatRuntimeQuerySafetyFlags(queue_write_attempted=True))

    def test_09_summaries_are_redacted_count_only(self):
        one = create_runtime_query_result_from_answer(request(), answer(answer_id="secret-answer-id-token"), "result_secret")
        missing = create_missing_runtime_query_result(request(request_id="runtime_req_002"), "result_missing")
        summary = summarize_runtime_query_result(one)
        many = summarize_runtime_query_results([one, missing])
        rendered = json.dumps({"summary": summary, "many": many}, sort_keys=True).lower()
        self.assertNotIn("secret-answer-id-token", rendered)
        self.assertNotIn("result_secret", rendered)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["result_count"])
        self.assertEqual(1, many["with_answer_count"])
        self.assertEqual(1, many["missing_answer_count"])

    def test_10_no_side_effects_in_summaries(self):
        summary = summarize_runtime_query_results([create_missing_runtime_query_result(request(), "result_missing")])
        self.assertFalse(summary["runtime_integration_performed"])
        self.assertFalse(summary["log_reads_performed"])
        self.assertFalse(summary["log_writes_performed"])
        self.assertFalse(summary["queue_writes_performed"])
        self.assertFalse(summary["memory_mutations_performed"])
        self.assertFalse(summary["model_advisor_calls_performed"])
        self.assertFalse(summary["answer_selection_performed"])
        self.assertFalse(summary["truth_soundness_score_claimed"])

    def test_11_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_12_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
