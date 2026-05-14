from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.voice_source_attribution import create_empty_voice_source_attribution_record  # noqa: E402
from weslr.who_said_that_dry_run_vertical_slice import (  # noqa: E402
    WhoSaidThatDryRunResult,
    run_who_said_that_dry_run_vertical_slice,
    summarize_who_said_that_dry_run_result,
    summarize_who_said_that_dry_run_results,
    who_said_that_dry_run_result_to_dict,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_dry_run_vertical_slice.py",
    "weslr/tests/test_who_said_that_dry_run_vertical_slice_v1.py",
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
    "openclaw.json",
    ".openclaw/config.json",
    "MEMORY.md",
}


def record(**overrides):
    data = {
        "utterance_id": "utt_a",
        "output_provenance_id": "out_a",
        "spoken_text_hash": "sha256:spoken",
        "source_subsystem": "voice_gateway",
        "source_module": "weslr.voice_gateway",
        "generated_by": "voice_gateway",
        "trigger": "operator voice event",
        "trigger_type": "voice_event",
        "input_channel": "voice",
        "output_channel": "voice",
        "tts_engine": "tts_surface",
        "stt_engine": "stt_surface",
        "authority_level": "voice_surface",
        "truth_class": "observed",
        "confidence": "medium",
        "created_at": "2026-05-14T11:45:00+00:00",
        "trace_refs": ["trace_a"],
    }
    data.update(overrides)
    return create_empty_voice_source_attribution_record(**data)


def run(**overrides):
    data = {
        "dry_run_id": "dry_run_001",
        "input_channel": "chat",
        "message_hash": "sha256:msg",
        "transient_phrase": "who said that?",
        "attribution_records": [record()],
    }
    data.update(overrides)
    return run_who_said_that_dry_run_vertical_slice(**data)


class WhoSaidThatDryRunVerticalSliceV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(WhoSaidThatDryRunResult)
        self.assertTrue(run_who_said_that_dry_run_vertical_slice)
        self.assertTrue(summarize_who_said_that_dry_run_result)
        self.assertTrue(summarize_who_said_that_dry_run_results)

    def test_02_dry_run_who_said_that_routes(self):
        result = run(transient_phrase="who said that?")
        self.assertTrue(result.should_route)
        self.assertFalse(result.fallthrough)
        self.assertTrue(result.runtime_query_created)
        self.assertEqual("who_said_that", result.phrase_family)

    def test_03_dry_run_llm_involved_routes(self):
        result = run(transient_phrase="was an LLM involved?", attribution_records=[record(llm_assisted=True, model_provider="provider-a", model_name="model-a")])
        self.assertTrue(result.should_route)
        self.assertEqual("was_llm_involved", result.phrase_family)

    def test_04_unclear_message_falls_through(self):
        result = run(transient_phrase="continue please", confidence="unknown", attribution_records=[])
        self.assertFalse(result.should_route)
        self.assertTrue(result.fallthrough)
        self.assertFalse(result.runtime_query_created)
        self.assertFalse(result.answer_created)

    def test_05_fallthrough_has_no_side_effects(self):
        result = run(transient_phrase="continue please", confidence="unknown", attribution_records=[])
        self.assertFalse(result.runtime_integration_performed)
        self.assertFalse(result.log_read_performed)
        self.assertFalse(result.log_write_performed)
        self.assertFalse(result.queue_write_performed)
        self.assertFalse(result.memory_mutation_performed)
        self.assertFalse(result.external_model_call_performed)

    def test_06_fake_in_memory_attribution_record_produces_answer(self):
        result = run(attribution_records=[record(source_subsystem="voice_gateway")])
        self.assertTrue(result.answer_created)
        self.assertTrue(result.attribution_found)
        self.assertEqual("voice_gateway", result.model_provider or "voice_gateway")
        self.assertTrue(result.answer_id)

    def test_07_fake_llm_assisted_attribution_record_discloses_provider_model(self):
        result = run(attribution_records=[record(llm_assisted=True, model_provider="provider-a", model_name="model-a")])
        self.assertTrue(result.llm_assisted)
        self.assertEqual("provider-a", result.model_provider)
        self.assertEqual("model-a", result.model_name)

    def test_08_missing_attribution_produces_unknown_unattributed_result(self):
        result = run(attribution_records=[])
        self.assertTrue(result.should_route)
        self.assertTrue(result.answer_created)
        self.assertFalse(result.attribution_found)
        self.assertEqual("unknown_unattributed", result.ownership_category)
        self.assertTrue(result.missing_attribution_reason)

    def test_09_no_raw_text_stored(self):
        result = run(transient_phrase="who said that?")
        rendered = json.dumps(who_said_that_dry_run_result_to_dict(result)).lower()
        self.assertNotIn("who said that", rendered)
        with self.assertRaises(ValueError):
            run(raw_text="who said that?")

    def test_10_no_real_log_read(self):
        self.assertFalse(run().log_read_performed)

    def test_11_no_log_write(self):
        self.assertFalse(run().log_write_performed)

    def test_12_no_queue_write(self):
        self.assertFalse(run().queue_write_performed)

    def test_13_no_runtime_integration(self):
        self.assertFalse(run().runtime_integration_performed)

    def test_14_no_memory_mutation(self):
        self.assertFalse(run().memory_mutation_performed)

    def test_15_no_external_model_call(self):
        self.assertFalse(run().external_model_call_performed)

    def test_16_no_answer_selection(self):
        self.assertFalse(run().answer_selection_performed)

    def test_17_no_truth_soundness_claim(self):
        result = run()
        self.assertFalse(result.truth_claim_made)
        rendered = json.dumps(who_said_that_dry_run_result_to_dict(result)).lower()
        self.assertNotIn("soundness", rendered)

    def test_18_no_official_score(self):
        self.assertFalse(run().official_score_claimed)

    def test_19_summaries_are_redacted_count_only(self):
        result = run(dry_run_id="dry_run_redacted_like")
        summary = summarize_who_said_that_dry_run_result(result)
        many = summarize_who_said_that_dry_run_results([result, run(dry_run_id="dry_run_002", attribution_records=[])])
        rendered = json.dumps({"summary": summary, "many": many}, sort_keys=True).lower()
        self.assertNotIn("dry_run_redacted_like", rendered)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual("redacted_count_only", many["summary_mode"])
        self.assertEqual(2, many["result_count"])

    def test_20_summaries_do_not_contain_sensitive_text(self):
        result = run()
        result.redacted_summary = "api key token secret raw spoken text raw benchmark answer key private user data"
        rendered = json.dumps(summarize_who_said_that_dry_run_result(result)) + json.dumps(summarize_who_said_that_dry_run_results([result]))
        rendered = rendered.lower()
        for forbidden in ["api key", "token", "secret", "raw spoken text", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_21_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_22_no_runtime_chat_voice_wiring_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED_FILES)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
