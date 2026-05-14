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
    create_chat_integration_fallthrough_result,
    simulate_who_said_that_chat_integration_from_metadata,
    summarize_chat_integration_result,
    summarize_chat_integration_results,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_chat_routing.py",
    "weslr/tests/test_who_said_that_chat_routing_integration_helpers_v1.py",
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


def simulate(**overrides):
    data = {
        "integration_result_id": "integration_001",
        "request_id": "chat_req_001",
        "input_channel": "chat",
        "message_text_hash": "sha256:msg",
        "transient_phrase": "who said that?",
        "confidence": "high",
        "runtime_query_request_id": "runtime_req_001",
    }
    data.update(overrides)
    return simulate_who_said_that_chat_integration_from_metadata(**data)


class WhoSaidThatChatRoutingIntegrationHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_imports(self):
        self.assertTrue(simulate_who_said_that_chat_integration_from_metadata)
        self.assertTrue(create_chat_integration_fallthrough_result)
        self.assertTrue(summarize_chat_integration_result)
        self.assertTrue(summarize_chat_integration_results)

    def test_02_clear_who_said_that_routes(self):
        result = simulate(transient_phrase="who said that?")
        self.assertTrue(result["who_said_that_path_selected"])
        self.assertFalse(result["fallthrough_to_normal_chat"])
        self.assertEqual("who_said_that_path", result["integration_path"])
        self.assertEqual("who_said_that", result["matched_phrase_family"])

    def test_03_clear_llm_involved_routes(self):
        result = simulate(transient_phrase="was an LLM involved?", runtime_query_request_id="runtime_req_llm")
        self.assertTrue(result["who_said_that_path_selected"])
        self.assertEqual("was_llm_involved", result["matched_phrase_family"])
        self.assertEqual("was_llm_involved", result["detected_attribution_intent"])

    def test_04_unclear_message_falls_through(self):
        result = simulate(transient_phrase="please continue the task", confidence="unknown", runtime_query_request_id="runtime_req_unused")
        self.assertFalse(result["who_said_that_path_selected"])
        self.assertTrue(result["fallthrough_to_normal_chat"])
        self.assertEqual("normal_chat_fallthrough", result["integration_path"])

    def test_05_low_confidence_falls_through(self):
        result = simulate(transient_phrase="who said that?", confidence="low", runtime_query_request_id="runtime_req_unused")
        self.assertFalse(result["who_said_that_path_selected"])
        self.assertTrue(result["fallthrough_to_normal_chat"])

    def test_06_fallthrough_has_no_side_effects(self):
        result = create_chat_integration_fallthrough_result("fallthrough_001", "chat_req_001")
        self.assertTrue(result["fallthrough_to_normal_chat"])
        self.assertFalse(result["routing_performed"])
        self.assertFalse(result["runtime_integration_performed"])
        self.assertFalse(result["chat_responder_modified"])
        self.assertFalse(result["runtime_output_created"])
        self.assertFalse(result["log_read_performed"])
        self.assertFalse(result["log_write_performed"])
        self.assertFalse(result["queue_write_performed"])
        self.assertFalse(result["memory_mutation_performed"])
        self.assertFalse(result["model_call_performed"])

    def test_07_routed_result_has_no_runtime_integration_performed(self):
        self.assertFalse(simulate()["runtime_integration_performed"])
        self.assertFalse(simulate()["routing_performed"])
        self.assertFalse(simulate()["chat_responder_modified"])
        self.assertFalse(simulate()["runtime_output_created"])

    def test_08_routed_result_has_no_log_read_write(self):
        result = simulate()
        self.assertFalse(result["log_read_performed"])
        self.assertFalse(result["log_write_performed"])

    def test_09_routed_result_has_no_queue_write(self):
        self.assertFalse(simulate()["queue_write_performed"])

    def test_10_routed_result_has_no_model_call(self):
        result = simulate()
        self.assertFalse(result["model_call_performed"])
        self.assertFalse(result["advisor_call_performed"])

    def test_11_raw_text_is_not_stored(self):
        result = simulate(transient_phrase="who said that?")
        rendered = json.dumps(result).lower()
        self.assertNotIn("who said that", rendered)
        self.assertFalse(result["chat_routing_request"]["raw_text_stored"])
        with self.assertRaises(ValueError):
            simulate(raw_text="who said that?")

    def test_12_summaries_are_redacted_count_only(self):
        routed = simulate(integration_result_id="secret-integration-token", runtime_query_request_id="secret-runtime-token")
        fallthrough = simulate(integration_result_id="fallthrough_secret", transient_phrase="not attribution", confidence="unknown")
        one = summarize_chat_integration_result(routed)
        many = summarize_chat_integration_results([routed, fallthrough])
        rendered = json.dumps({"one": one, "many": many}, sort_keys=True).lower()
        self.assertNotIn("secret-integration-token", rendered)
        self.assertNotIn("secret-runtime-token", rendered)
        self.assertEqual("redacted_count_only", one["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["result_count"])
        self.assertEqual(1, many["route_count"])
        self.assertEqual(1, many["fallthrough_count"])

    def test_13_summary_side_effect_flags_false(self):
        summary = summarize_chat_integration_results([simulate()])
        self.assertFalse(summary["routing_performed"])
        self.assertFalse(summary["runtime_integration_performed"])
        self.assertFalse(summary["chat_responder_modified"])
        self.assertFalse(summary["runtime_outputs_created"])
        self.assertFalse(summary["log_reads_performed"])
        self.assertFalse(summary["log_writes_performed"])
        self.assertFalse(summary["queue_writes_performed"])
        self.assertFalse(summary["memory_mutations_performed"])
        self.assertFalse(summary["model_calls_performed"])
        self.assertFalse(summary["voice_wiring_performed"])

    def test_14_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_15_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
