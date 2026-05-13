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
    create_who_said_that_query_intent_from_text_metadata,
    resolve_who_said_that_from_provided_records,
    select_candidate_attribution_record,
    summarize_who_said_that_resolver_diagnostics,
    validate_who_said_that_answer,
)


def intent(**overrides):
    data = {
        "query_id": "q_resolver",
        "intent_type": "who_said_that",
        "query_text_hash": "trace_a",
        "input_channel": "chat",
        "lookback_mode": "most_recent",
    }
    data.update(overrides)
    return create_who_said_that_query_intent_from_text_metadata(**data)


def record(**overrides):
    data = {
        "utterance_id": "utt_a",
        "output_provenance_id": "out_a",
        "spoken_text_hash": "sha256:a",
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
        "created_at": "2026-05-13T20:00:00+00:00",
        "trace_refs": ["trace_a"],
    }
    data.update(overrides)
    return create_empty_voice_source_attribution_record(**data)


class WhoSaidThatParserlessResolverHelpersV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(resolve_who_said_that_from_provided_records)
        self.assertTrue(select_candidate_attribution_record)

    def test_02_resolver_accepts_valid_query_intent(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[])
        self.assertEqual("q_resolver", answer.query_id)

    def test_03_resolver_uses_provided_in_memory_attribution_record(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record()])
        self.assertTrue(answer.attribution_found)
        self.assertEqual("voice_gateway", answer.source_subsystem)

    def test_04_resolver_uses_provided_in_memory_log_event(self):
        event = create_pre_speak_attribution_event(record())
        answer = resolve_who_said_that_from_provided_records(intent(), log_events=[event])
        self.assertTrue(answer.attribution_found)
        self.assertEqual("voice_gateway", answer.source_subsystem)

    def test_05_most_recent_chooses_latest_created_at_when_available(self):
        old = record(utterance_id="old", created_at="2026-05-13T19:00:00+00:00", trace_refs=["old_trace"])
        new = record(utterance_id="new", created_at="2026-05-13T21:00:00+00:00", trace_refs=["new_trace"])
        selected = select_candidate_attribution_record(intent(), attribution_records=[new, old])
        self.assertEqual("new", selected["candidate"].utterance_id)

    def test_06_most_recent_falls_back_to_last_provided_when_dates_absent(self):
        first = record(utterance_id="first", created_at="", trace_refs=["trace_first"])
        second = record(utterance_id="second", created_at="", trace_refs=["trace_second"])
        selected = select_candidate_attribution_record(intent(), attribution_records=[first, second])
        self.assertEqual("second", selected["candidate"].utterance_id)

    def test_07_by_utterance_id_finds_matching_record(self):
        query = intent(lookback_mode="by_utterance_id", requested_utterance_id="target")
        answer = resolve_who_said_that_from_provided_records(query, attribution_records=[record(utterance_id="other"), record(utterance_id="target")])
        self.assertTrue(answer.attribution_found)
        self.assertEqual("voice_gateway", answer.generated_by)

    def test_08_by_utterance_id_missing_returns_missing_attribution_answer(self):
        query = intent(lookback_mode="by_utterance_id", requested_utterance_id="missing")
        answer = resolve_who_said_that_from_provided_records(query, attribution_records=[record(utterance_id="other")])
        self.assertFalse(answer.attribution_found)
        self.assertEqual("unknown_unattributed", answer.ownership_category)

    def test_09_by_trace_ref_finds_matching_record_event(self):
        query = intent(lookback_mode="by_trace_ref", query_text_hash="trace_target")
        answer = resolve_who_said_that_from_provided_records(query, attribution_records=[record(trace_refs=["trace_target"])])
        self.assertTrue(answer.attribution_found)

    def test_10_by_trace_ref_missing_returns_missing_attribution_answer(self):
        query = intent(lookback_mode="by_trace_ref", query_text_hash="trace_missing")
        answer = resolve_who_said_that_from_provided_records(query, attribution_records=[record(trace_refs=["trace_other"])])
        self.assertFalse(answer.attribution_found)

    def test_11_ambiguous_match_does_not_guess(self):
        query = intent(lookback_mode="by_trace_ref", query_text_hash="same_trace")
        selected = select_candidate_attribution_record(query, attribution_records=[record(utterance_id="a", trace_refs=["same_trace"]), record(utterance_id="b", trace_refs=["same_trace"])])
        answer = resolve_who_said_that_from_provided_records(query, attribution_records=[record(utterance_id="a", trace_refs=["same_trace"]), record(utterance_id="b", trace_refs=["same_trace"])])
        self.assertTrue(selected["ambiguous"])
        self.assertFalse(answer.attribution_found)

    def test_12_invalid_query_intent_fails_safely(self):
        bad = asdict(intent())
        bad["lookback_mode"] = "scan_disk_logs"
        answer = resolve_who_said_that_from_provided_records(bad, attribution_records=[record()])
        self.assertFalse(answer.attribution_found)
        self.assertEqual("unknown_unattributed", answer.ownership_category)

    def test_13_invalid_provided_record_fails_safely(self):
        bad = asdict(record())
        bad["utterance_id"] = ""
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[bad])
        self.assertFalse(answer.attribution_found)

    def test_14_no_provided_records_returns_missing_attribution_answer(self):
        answer = resolve_who_said_that_from_provided_records(intent())
        self.assertFalse(answer.attribution_found)

    def test_15_missing_attribution_answer_validates(self):
        answer = resolve_who_said_that_from_provided_records(intent())
        self.assertEqual([], validate_who_said_that_answer(answer))

    def test_16_matched_attribution_answer_validates(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record()])
        self.assertEqual([], validate_who_said_that_answer(answer))

    def test_17_llm_assisted_record_returns_safe_answer(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(llm_assisted=True, model_provider="provider-a", model_name="model-a")])
        self.assertTrue(answer.llm_assisted)
        self.assertEqual("weslr_surface_llm_assisted", answer.ownership_category)

    def test_18_advisor_assisted_record_returns_advisor_answer(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(advisor_assisted=True, related_advisor_review_ids=["adv1"])])
        self.assertTrue(answer.advisor_assisted)
        self.assertEqual("advisor_assisted", answer.ownership_category)

    def test_19_external_model_source_returns_external_model_surface_category(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(source_subsystem="external_model", generated_by="external_model")])
        self.assertEqual("external_model_surface", answer.ownership_category)

    def test_20_unknown_source_returns_unknown_unattributed(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(source_subsystem="unknown", source_module="", generated_by="", trace_refs=[])])
        self.assertFalse(answer.attribution_found)
        self.assertEqual("unknown_unattributed", answer.ownership_category)

    def test_21_resolver_does_not_claim_i_said_it_without_support(self):
        rendered = json.dumps(asdict(resolve_who_said_that_from_provided_records(intent()))).lower()
        self.assertNotIn("i said it", rendered)

    def test_22_resolver_does_not_claim_weslr_ownership_without_attribution_and_trace_refs(self):
        answer = resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(trace_refs=[])])
        self.assertNotEqual("weslr_owned", answer.ownership_category)

    def test_23_resolver_does_not_read_logs(self):
        self.assertFalse(summarize_who_said_that_resolver_diagnostics()["log_reads_performed"])

    def test_24_resolver_does_not_write_logs(self):
        self.assertFalse(summarize_who_said_that_resolver_diagnostics()["log_writes_performed"])

    def test_25_resolver_does_not_write_queues(self):
        self.assertFalse(summarize_who_said_that_resolver_diagnostics()["queue_writes_performed"])

    def test_26_resolver_does_not_call_models(self):
        self.assertFalse(summarize_who_said_that_resolver_diagnostics()["external_model_calls_performed"])

    def test_27_resolver_does_not_mutate_runtime_config(self):
        self.assertFalse(summarize_who_said_that_resolver_diagnostics()["runtime_changes_performed"])

    def test_28_diagnostics_summary_is_redacted_count_only(self):
        self.assertEqual("redacted_count_only", summarize_who_said_that_resolver_diagnostics()["summary_mode"])

    def test_29_diagnostics_summary_counts_matched_missing_partial_ambiguous(self):
        query = intent(lookback_mode="by_trace_ref", query_text_hash="same_trace")
        selected_match = select_candidate_attribution_record(intent(), attribution_records=[record()])
        selected_ambiguous = select_candidate_attribution_record(query, attribution_records=[record(utterance_id="a", trace_refs=["same_trace"]), record(utterance_id="b", trace_refs=["same_trace"])])
        answers = [resolve_who_said_that_from_provided_records(intent(), attribution_records=[record()]), resolve_who_said_that_from_provided_records(intent())]
        summary = summarize_who_said_that_resolver_diagnostics(answers=answers, selections=[selected_match, selected_ambiguous], provided_record_count=3)
        self.assertEqual(1, summary["matched_count"])
        self.assertEqual(1, summary["missing_count"])
        self.assertGreaterEqual(summary["partial_count"], 1)
        self.assertEqual(1, summary["ambiguous_count"])

    def test_30_diagnostics_summary_counts_llm_advisor_assisted_answers(self):
        answers = [
            resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(llm_assisted=True, model_provider="p", model_name="m")]),
            resolve_who_said_that_from_provided_records(intent(), attribution_records=[record(advisor_assisted=True, related_advisor_review_ids=["adv"])])
        ]
        summary = summarize_who_said_that_resolver_diagnostics(answers=answers)
        self.assertEqual(1, summary["llm_assisted_count"])
        self.assertEqual(1, summary["advisor_assisted_count"])

    def test_31_diagnostics_summary_does_not_contain_sensitive_text(self):
        answer = resolve_who_said_that_from_provided_records(intent())
        summary = summarize_who_said_that_resolver_diagnostics(answers=[answer], selections=[{"matched": False, "ambiguous": False, "partial": False, "candidate": None, "note": "api key token secret raw spoken text raw benchmark answer key private user data"}])
        rendered = json.dumps(summary).lower()
        for forbidden in ["api key", "token", "secret", "raw spoken text", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_32_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_33_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_34_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_35_who_said_that_helper_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_query_surface_helpers_v1.py"], cwd=str(ROOT))

    def test_36_who_said_that_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_query_surface_schema_v1.py"], cwd=str(ROOT))

    def test_37_voice_attribution_logging_helper_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_logging_helpers_v1.py"], cwd=str(ROOT))

    def test_38_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))


if __name__ == "__main__":
    unittest.main()
