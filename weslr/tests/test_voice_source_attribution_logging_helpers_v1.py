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
from weslr.voice_source_attribution_log import (  # noqa: E402
    VoiceAttributionLogEvent,
    create_attribution_query_requested_event,
    create_missing_attribution_event,
    create_post_speak_attribution_event,
    create_pre_speak_attribution_event,
    summarize_voice_attribution_log_events,
    validate_voice_attribution_log_event,
)


def valid_attribution(**overrides):
    item = create_empty_voice_source_attribution_record(
        utterance_id="utt_001",
        output_provenance_id="out_001",
        spoken_text_hash="sha256:abc123",
        source_subsystem="voice_gateway",
        source_module="weslr.voice_gateway",
        generated_by="voice_gateway",
        trigger="operator voice event",
        trigger_type="voice_event",
        input_channel="voice",
        output_channel="voice",
        voice_engine="configured_voice_surface",
        tts_engine="configured_tts_surface",
        stt_engine="configured_stt_surface",
        authority_level="voice_surface",
        truth_class="observed",
        confidence="medium",
        trace_refs=["trace_001"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class VoiceSourceAttributionLoggingHelpersV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(VoiceAttributionLogEvent)
        self.assertTrue(create_pre_speak_attribution_event)

    def test_02_pre_speak_event_created_from_valid_attribution_record(self):
        event = create_pre_speak_attribution_event(valid_attribution())
        self.assertEqual("pre_speak_attribution_draft", event.event_type)
        self.assertEqual("utt_001", event.utterance_id)

    def test_03_pre_speak_event_validates(self):
        self.assertEqual([], validate_voice_attribution_log_event(create_pre_speak_attribution_event(valid_attribution())))

    def test_04_post_speak_success_event_created(self):
        event = create_post_speak_attribution_event(valid_attribution(), speech_success=True)
        self.assertEqual("post_speak_attribution_confirmed", event.event_type)
        self.assertTrue(event.speech_success)

    def test_05_post_speak_failure_event_created(self):
        event = create_post_speak_attribution_event(valid_attribution(), speech_success=False)
        self.assertEqual("post_speak_attribution_failed", event.event_type)
        self.assertFalse(event.speech_success)

    def test_06_post_speak_event_requires_trace_refs_through_validation(self):
        event = create_post_speak_attribution_event(valid_attribution(), speech_success=True)
        event.trace_refs = []
        self.assertIn("post-speak event requires trace_refs", validate_voice_attribution_log_event(event))

    def test_07_missing_attribution_event_created(self):
        event = create_missing_attribution_event()
        self.assertEqual("missing_attribution_detected", event.event_type)

    def test_08_missing_attribution_event_uses_unknown_safe_source(self):
        event = create_missing_attribution_event(source_subsystem="bad")
        self.assertEqual("unknown", event.source_subsystem)

    def test_09_missing_attribution_event_does_not_claim_i_said_it(self):
        event = create_missing_attribution_event()
        rendered = json.dumps(event.attribution_record_snapshot).lower() + event.redacted_summary.lower()
        self.assertNotIn("i said it", rendered)
        self.assertFalse(event.attribution_record_snapshot["ownership_claim"])

    def test_10_attribution_query_requested_event_created(self):
        event = create_attribution_query_requested_event()
        self.assertEqual("attribution_query_requested", event.event_type)
        self.assertFalse(event.attribution_record_snapshot["lookup_performed"])
        self.assertFalse(event.attribution_record_snapshot["answer_provided"])

    def test_11_helper_rejects_invalid_attribution_record(self):
        with self.assertRaises(ValueError):
            create_pre_speak_attribution_event(valid_attribution(utterance_id=""))

    def test_12_helper_does_not_store_raw_spoken_text(self):
        event = create_pre_speak_attribution_event(valid_attribution())
        self.assertFalse(event.spoken_text_stored)
        self.assertNotIn("trigger", event.attribution_record_snapshot)

    def test_13_helper_preserves_spoken_text_hash_only(self):
        event = create_pre_speak_attribution_event(valid_attribution(spoken_text_hash="sha256:def456"))
        self.assertEqual("sha256:def456", event.spoken_text_hash)
        self.assertTrue(event.attribution_record_snapshot["spoken_text_hash"])

    def test_14_llm_assisted_event_carries_provider_model_safely(self):
        event = create_pre_speak_attribution_event(valid_attribution(llm_assisted=True, model_provider="provider-a", model_name="model-a"))
        self.assertTrue(event.llm_assisted)
        self.assertEqual("provider-a", event.model_provider)
        self.assertEqual("model-a", event.model_name)

    def test_15_event_with_llm_assistance_does_not_claim_system_fact_authority(self):
        event = create_pre_speak_attribution_event(valid_attribution(llm_assisted=True, model_provider="provider-a", model_name="model-a"))
        self.assertNotEqual("system_fact", event.authority_level)

    def test_16_event_with_llm_assistance_does_not_claim_verified_system_fact_truth(self):
        event = create_pre_speak_attribution_event(valid_attribution(llm_assisted=True, model_provider="provider-a", model_name="model-a"))
        self.assertNotEqual("verified_system_fact", event.truth_class)

    def test_17_event_has_no_log_write_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.log_write_attempted)

    def test_18_event_has_no_queue_write_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.queue_write_attempted)

    def test_19_event_has_no_registry_persistence_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.registry_persistence_attempted)

    def test_20_event_has_no_runtime_voice_wiring_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.runtime_voice_wiring_attempted)

    def test_21_event_has_no_external_model_call_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.external_model_call_attempted)

    def test_22_event_has_no_memory_mutation_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.memory_mutation_attempted)

    def test_23_event_has_no_self_improvement_activation_flag(self):
        self.assertFalse(create_pre_speak_attribution_event(valid_attribution()).safety_flags.self_improvement_activation_attempted)

    def test_24_summary_is_redacted_count_only(self):
        summary = summarize_voice_attribution_log_events([create_pre_speak_attribution_event(valid_attribution())])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertFalse(summary["log_writes_performed"])

    def test_25_summary_counts_event_types(self):
        summary = summarize_voice_attribution_log_events([create_pre_speak_attribution_event(valid_attribution())])
        self.assertEqual(1, summary["by_event_type"]["pre_speak_attribution_draft"])

    def test_26_summary_counts_missing_attribution_events(self):
        summary = summarize_voice_attribution_log_events([create_missing_attribution_event()])
        self.assertEqual(1, summary["missing_attribution_count"])

    def test_27_summary_counts_llm_assisted_events(self):
        event = create_pre_speak_attribution_event(valid_attribution(llm_assisted=True, model_provider="provider-a", model_name="model-a"))
        self.assertEqual(1, summarize_voice_attribution_log_events([event])["llm_assisted_count"])

    def test_28_summary_does_not_contain_sensitive_raw_text(self):
        event = create_attribution_query_requested_event(event_id="api key sk-abc123", utterance_id="secret token bearer abc.def")
        event.redacted_summary = "raw spoken text raw benchmark text answer key private user data password:=x"
        rendered = json.dumps(summarize_voice_attribution_log_events([event])).lower()
        for forbidden in ["sk-abc123", "token", "secret", "bearer abc.def", "raw spoken text", "raw benchmark text", "answer key", "private user data", "password"]:
            self.assertNotIn(forbidden, rendered)

    def test_29_no_attribution_log_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_30_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_31_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_32_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_log_schema_v1.py"], cwd=str(ROOT))

    def test_33_voice_attribution_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_schema_v1.py"], cwd=str(ROOT))

    def test_34_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))


if __name__ == "__main__":
    unittest.main()
