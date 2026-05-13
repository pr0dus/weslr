from __future__ import annotations

import json
import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.voice_source_attribution import create_empty_voice_source_attribution_record  # noqa: E402
from weslr.voice_source_attribution_log import create_pre_speak_attribution_event  # noqa: E402
from weslr.who_said_that_query_surface import (  # noqa: E402
    create_answer_from_voice_attribution_record,
    create_answer_from_voice_log_event,
    create_empty_who_said_that_answer,
    create_missing_attribution_answer,
    create_who_said_that_query_intent_from_text_metadata,
    derive_ownership_category_from_records,
    summarize_who_said_that_query_diagnostics,
    validate_who_said_that_answer,
    validate_who_said_that_query_intent,
)


def valid_record(**overrides):
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
        tts_engine="tts_surface",
        stt_engine="stt_surface",
        authority_level="voice_surface",
        truth_class="observed",
        confidence="medium",
        trace_refs=["trace_001"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class WhoSaidThatQuerySurfaceHelpersV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(create_who_said_that_query_intent_from_text_metadata)
        self.assertTrue(create_answer_from_voice_attribution_record)

    def test_02_create_query_intent_from_explicit_metadata(self):
        item = create_who_said_that_query_intent_from_text_metadata("q1", "who_said_that", "sha256:q", "chat")
        self.assertEqual("q1", item.query_id)
        self.assertEqual("who_said_that", item.intent_type)

    def test_03_query_intent_does_not_store_raw_query_text(self):
        self.assertFalse(create_who_said_that_query_intent_from_text_metadata("q1").raw_query_stored)

    def test_04_query_intent_validates(self):
        self.assertEqual([], validate_who_said_that_query_intent(create_who_said_that_query_intent_from_text_metadata("q1")))

    def test_05_missing_attribution_answer_validates(self):
        self.assertEqual([], validate_who_said_that_answer(create_missing_attribution_answer("a1", "q1")))

    def test_06_missing_attribution_answer_has_unknown_unattributed(self):
        self.assertEqual("unknown_unattributed", create_missing_attribution_answer("a1", "q1").ownership_category)

    def test_07_missing_attribution_answer_does_not_claim_i_said_it(self):
        rendered = json.dumps(asdict(create_missing_attribution_answer("a1", "q1"))).lower()
        self.assertNotIn("i said it", rendered)

    def test_08_missing_attribution_answer_requires_operator_review(self):
        self.assertTrue(create_missing_attribution_answer("a1", "q1").operator_review_required)

    def test_09_answer_from_valid_voice_attribution_record_validates(self):
        answer = create_answer_from_voice_attribution_record(valid_record(), "a1", "q1")
        self.assertEqual([], validate_who_said_that_answer(answer))

    def test_10_answer_preserves_source_subsystem(self):
        self.assertEqual("voice_gateway", create_answer_from_voice_attribution_record(valid_record(), "a1", "q1").source_subsystem)

    def test_11_answer_preserves_trigger(self):
        self.assertEqual("operator voice event", create_answer_from_voice_attribution_record(valid_record(), "a1", "q1").trigger)

    def test_12_answer_preserves_authority_truth_confidence(self):
        answer = create_answer_from_voice_attribution_record(valid_record(), "a1", "q1")
        self.assertEqual(("voice_surface", "observed", "medium"), (answer.authority_level, answer.truth_class, answer.confidence))

    def test_13_llm_assisted_record_includes_provider_model(self):
        answer = create_answer_from_voice_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a"), "a1", "q1")
        self.assertEqual(("provider-a", "model-a"), (answer.model_provider, answer.model_name))

    def test_14_llm_assisted_answer_does_not_claim_system_fact(self):
        answer = create_answer_from_voice_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a", authority_level="voice_surface"), "a1", "q1")
        self.assertNotEqual("system_fact", answer.authority_level)

    def test_15_llm_assisted_ownership_safe(self):
        answer = create_answer_from_voice_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a"), "a1", "q1")
        self.assertIn(answer.ownership_category, {"weslr_surface_llm_assisted", "unknown_unattributed"})

    def test_16_advisor_assisted_answer_ownership(self):
        answer = create_answer_from_voice_attribution_record(valid_record(advisor_assisted=True, related_advisor_review_ids=["adv1"]), "a1", "q1")
        self.assertEqual("advisor_assisted", answer.ownership_category)

    def test_17_external_model_source_maps(self):
        self.assertEqual("external_model_surface", derive_ownership_category_from_records("external_model", attribution_found=True))

    def test_18_operator_triggered_source_maps(self):
        self.assertEqual("operator_triggered", derive_ownership_category_from_records("operator_cli", generated_by="operator_cli", attribution_found=True))

    def test_19_unknown_source_maps_unknown(self):
        self.assertEqual("unknown_unattributed", derive_ownership_category_from_records("unknown", attribution_found=True))

    def test_20_answer_from_log_event_works(self):
        event = create_pre_speak_attribution_event(valid_record())
        answer = create_answer_from_voice_log_event(event, "a1", "q1")
        self.assertTrue(answer.attribution_found)

    def test_21_incomplete_log_event_creates_partial_or_missing(self):
        event = create_pre_speak_attribution_event(valid_record())
        event.attribution_record_snapshot = {}
        answer = create_answer_from_voice_log_event(event, "a1", "q1")
        self.assertTrue(answer.attribution_partial or not answer.attribution_found)

    def test_22_derive_ownership_category_is_conservative(self):
        self.assertEqual("unknown_unattributed", derive_ownership_category_from_records("bad", attribution_found=True))

    def test_23_helper_rejects_invalid_attribution_record(self):
        with self.assertRaises(ValueError):
            create_answer_from_voice_attribution_record(valid_record(utterance_id=""), "a1", "q1")

    def test_24_helper_does_not_read_logs(self):
        self.assertFalse(summarize_who_said_that_query_diagnostics([])["log_reads_performed"])

    def test_25_helper_does_not_write_logs(self):
        self.assertFalse(summarize_who_said_that_query_diagnostics([])["log_writes_performed"])

    def test_26_helper_does_not_write_queues(self):
        self.assertFalse(summarize_who_said_that_query_diagnostics([])["queue_writes_performed"])

    def test_27_helper_does_not_call_models(self):
        self.assertFalse(summarize_who_said_that_query_diagnostics([])["external_model_calls_performed"])

    def test_28_helper_does_not_mutate_runtime_config(self):
        self.assertFalse(summarize_who_said_that_query_diagnostics([])["runtime_changes_performed"])

    def test_29_diagnostics_summary_redacted_count_only(self):
        summary = summarize_who_said_that_query_diagnostics([create_missing_attribution_answer("a1", "q1")])
        self.assertEqual("redacted_count_only", summary["summary_mode"])

    def test_30_diagnostics_counts_missing_partial_found(self):
        answers = [create_missing_attribution_answer("a1", "q1"), create_answer_from_voice_attribution_record(valid_record(), "a2", "q1")]
        summary = summarize_who_said_that_query_diagnostics(answers)
        self.assertEqual(1, summary["attribution_missing_count"])
        self.assertEqual(1, summary["attribution_found_count"])

    def test_31_diagnostics_counts_llm_advisor_assisted(self):
        answers = [
            create_answer_from_voice_attribution_record(valid_record(llm_assisted=True, model_provider="p", model_name="m"), "a1", "q1"),
            create_answer_from_voice_attribution_record(valid_record(advisor_assisted=True, related_advisor_review_ids=["adv"]), "a2", "q1"),
        ]
        summary = summarize_who_said_that_query_diagnostics(answers)
        self.assertEqual(1, summary["llm_assisted_count"])
        self.assertEqual(1, summary["advisor_assisted_count"])

    def test_32_diagnostics_summary_no_sensitive_text(self):
        answer = create_empty_who_said_that_answer(answer_id="secret token bearer abc.def", query_id="q1", missing_attribution_reason="raw spoken text raw benchmark text answer key private user data password:=x")
        rendered = json.dumps(summarize_who_said_that_query_diagnostics([answer])).lower()
        for forbidden in ["secret", "token", "bearer abc.def", "raw spoken text", "raw benchmark text", "answer key", "private user data", "password"]:
            self.assertNotIn(forbidden, rendered)

    def test_33_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_34_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_35_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_36_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_query_surface_schema_v1.py"], cwd=str(ROOT))

    def test_37_voice_attribution_logging_helper_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_logging_helpers_v1.py"], cwd=str(ROOT))

    def test_38_voice_attribution_log_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_log_schema_v1.py"], cwd=str(ROOT))

    def test_39_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))


if __name__ == "__main__":
    unittest.main()
