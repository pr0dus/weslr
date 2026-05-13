from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_log_lookup import (  # noqa: E402
    ALLOWED_LOOKUP_MODES,
    WhoSaidThatLogLookupPathPolicy,
    WhoSaidThatLogLookupRequest,
    WhoSaidThatLogLookupResult,
    WhoSaidThatLogLookupSafetyFlags,
    create_empty_who_said_that_log_lookup_path_policy,
    create_empty_who_said_that_log_lookup_request,
    create_empty_who_said_that_log_lookup_result,
    summarize_who_said_that_log_lookup_result,
    summarize_who_said_that_log_lookup_results,
    validate_who_said_that_log_lookup_path_policy,
    validate_who_said_that_log_lookup_request,
    validate_who_said_that_log_lookup_result,
    who_said_that_log_lookup_path_policy_from_dict,
    who_said_that_log_lookup_path_policy_to_dict,
    who_said_that_log_lookup_request_from_dict,
    who_said_that_log_lookup_request_to_dict,
    who_said_that_log_lookup_result_from_dict,
    who_said_that_log_lookup_result_to_dict,
)

ALLOWED_CHANGED_FILES = {
    "weslr/who_said_that_log_lookup.py",
    "weslr/tests/test_who_said_that_read_only_log_lookup_schema_v1.py",
    "weslr/tests/test_who_said_that_read_only_log_lookup_helpers_v1.py",
}


def policy(**overrides):
    return create_empty_who_said_that_log_lookup_path_policy(**overrides)


def request(**overrides):
    data = {"request_id": "req_a", "query_id": "query_a"}
    data.update(overrides)
    return create_empty_who_said_that_log_lookup_request(**data)


def result(**overrides):
    data = {"result_id": "res_a", "request_id": "req_a", "lookup_mode": "most_recent"}
    data.update(overrides)
    return create_empty_who_said_that_log_lookup_result(**data)


class WhoSaidThatReadOnlyLogLookupSchemaV1Tests(unittest.TestCase):
    def test_01_module_imports(self):
        self.assertTrue(WhoSaidThatLogLookupSafetyFlags)
        self.assertTrue(WhoSaidThatLogLookupPathPolicy)
        self.assertTrue(WhoSaidThatLogLookupRequest)
        self.assertTrue(WhoSaidThatLogLookupResult)

    def test_02_path_policy_instantiates(self):
        self.assertEqual("jsonl", policy().storage_format)

    def test_03_request_instantiates(self):
        self.assertEqual("req_a", request().request_id)

    def test_04_result_instantiates(self):
        self.assertEqual("res_a", result().result_id)

    def test_05_safe_defaults(self):
        self.assertEqual([], validate_who_said_that_log_lookup_path_policy(policy()))
        self.assertEqual([], validate_who_said_that_log_lookup_request(request()))
        self.assertEqual([], validate_who_said_that_log_lookup_result(result()))

    def test_06_default_log_path(self):
        self.assertEqual(".weslr/voice_source_attribution.jsonl", policy().log_path)

    def test_07_storage_format_jsonl_validates(self):
        self.assertEqual([], validate_who_said_that_log_lookup_path_policy(policy(storage_format="jsonl")))

    def test_08_invalid_storage_format_fails(self):
        self.assertIn("invalid storage_format", validate_who_said_that_log_lookup_path_policy(policy(storage_format="sqlite")))

    def test_09_read_only_disabled_fails(self):
        self.assertIn("read_only_required disabled", validate_who_said_that_log_lookup_path_policy(policy(read_only_required=False)))

    def test_10_explicit_path_policy_disabled_fails(self):
        self.assertIn("explicit_path_policy_required disabled", validate_who_said_that_log_lookup_path_policy(policy(explicit_path_policy_required=False)))

    def test_11_redaction_disabled_fails(self):
        self.assertIn("redaction_required disabled", validate_who_said_that_log_lookup_path_policy(policy(redaction_required=False)))

    def test_12_raw_spoken_text_allowed_fails(self):
        self.assertIn("raw_spoken_text_allowed true", validate_who_said_that_log_lookup_path_policy(policy(raw_spoken_text_allowed=True)))

    def test_13_create_if_missing_allowed_fails(self):
        self.assertIn("create_if_missing_allowed true", validate_who_said_that_log_lookup_path_policy(policy(create_if_missing_allowed=True)))

    def test_14_writes_allowed_fails(self):
        self.assertIn("writes_allowed true", validate_who_said_that_log_lookup_path_policy(policy(writes_allowed=True)))

    def test_15_absolute_paths_allowed_fails(self):
        self.assertIn("absolute paths allowed", validate_who_said_that_log_lookup_path_policy(policy(allow_absolute_paths=True)))

    def test_16_path_traversal_allowed_fails(self):
        self.assertIn("path traversal allowed", validate_who_said_that_log_lookup_path_policy(policy(allow_path_traversal=True)))

    def test_17_external_storage_allowed_fails(self):
        self.assertIn("external storage allowed", validate_who_said_that_log_lookup_path_policy(policy(allow_external_storage=True)))

    def test_18_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required disabled", validate_who_said_that_log_lookup_path_policy(policy(operator_review_required=False)))

    def test_19_all_lookup_modes_validate(self):
        for mode in ALLOWED_LOOKUP_MODES:
            kwargs = {"lookup_mode": mode}
            if mode == "by_utterance_id":
                kwargs["requested_utterance_id"] = "utt_a"
            if mode == "by_trace_ref":
                kwargs["requested_trace_ref"] = "trace_a"
            if mode == "by_time_window":
                kwargs["time_window_start"] = "2026-05-13T20:00:00Z"
                kwargs["time_window_end"] = "2026-05-13T21:00:00Z"
            self.assertEqual([], validate_who_said_that_log_lookup_request(request(**kwargs)), mode)

    def test_20_invalid_lookup_mode_fails(self):
        self.assertIn("invalid lookup_mode", validate_who_said_that_log_lookup_request(request(lookup_mode="scan_everything")))

    def test_21_missing_request_id_fails(self):
        self.assertIn("missing request_id", validate_who_said_that_log_lookup_request(request(request_id="")))

    def test_22_by_utterance_id_without_utterance_id_fails(self):
        self.assertIn("by_utterance_id requires requested_utterance_id", validate_who_said_that_log_lookup_request(request(lookup_mode="by_utterance_id")))

    def test_23_by_trace_ref_without_trace_ref_fails(self):
        self.assertIn("by_trace_ref requires requested_trace_ref", validate_who_said_that_log_lookup_request(request(lookup_mode="by_trace_ref")))

    def test_24_by_time_window_without_start_end_fails(self):
        self.assertIn("by_time_window requires time_window_start and time_window_end", validate_who_said_that_log_lookup_request(request(lookup_mode="by_time_window")))

    def test_25_max_events_zero_fails(self):
        self.assertIn("max_events must be positive", validate_who_said_that_log_lookup_request(request(max_events=0)))

    def test_26_redacted_only_false_fails(self):
        self.assertIn("redacted_only false", validate_who_said_that_log_lookup_request(request(redacted_only=False)))

    def test_27_missing_result_id_fails(self):
        self.assertIn("missing result_id", validate_who_said_that_log_lookup_result(result(result_id="")))

    def test_28_missing_result_request_id_fails(self):
        self.assertIn("missing result request_id", validate_who_said_that_log_lookup_result(result(request_id="")))

    def test_29_result_not_read_only_fails(self):
        self.assertIn("result not read-only", validate_who_said_that_log_lookup_result(result(read_only=False)))

    def test_30_log_write_performed_fails(self):
        self.assertIn("log write performed", validate_who_said_that_log_lookup_result(result(log_write_performed=True)))

    def test_31_log_created_fails(self):
        self.assertIn("log created", validate_who_said_that_log_lookup_result(result(log_created=True)))

    def test_32_queue_write_performed_fails(self):
        self.assertIn("queue write performed", validate_who_said_that_log_lookup_result(result(queue_write_performed=True)))

    def test_33_runtime_change_performed_fails(self):
        self.assertIn("runtime change performed", validate_who_said_that_log_lookup_result(result(runtime_change_performed=True)))

    def test_34_external_model_call_performed_fails(self):
        self.assertIn("external model call performed", validate_who_said_that_log_lookup_result(result(external_model_call_performed=True)))

    def test_35_answer_selection_performed_fails(self):
        self.assertIn("answer selection performed", validate_who_said_that_log_lookup_result(result(answer_selection_performed=True)))

    def test_36_truth_claim_made_fails(self):
        self.assertIn("truth claim made", validate_who_said_that_log_lookup_result(result(truth_claim_made=True)))

    def test_37_official_score_claimed_fails(self):
        self.assertIn("official score claimed", validate_who_said_that_log_lookup_result(result(official_score_claimed=True)))

    def _assert_flag_fails(self, field_name: str, expected: str):
        flags = WhoSaidThatLogLookupSafetyFlags(**{field_name: True})
        self.assertIn(expected, validate_who_said_that_log_lookup_result(result(safety_flags=flags)))

    def test_38_log_write_safety_flag_fails(self):
        self._assert_flag_fails("log_write_attempted", "log write attempted")

    def test_39_log_creation_safety_flag_fails(self):
        self._assert_flag_fails("log_creation_attempted", "log creation attempted")

    def test_40_queue_write_safety_flag_fails(self):
        self._assert_flag_fails("queue_write_attempted", "queue write attempted")

    def test_41_registry_persistence_safety_flag_fails(self):
        self._assert_flag_fails("registry_persistence_attempted", "registry persistence attempted")

    def test_42_runtime_chat_voice_wiring_safety_flag_fails(self):
        self._assert_flag_fails("runtime_chat_voice_wiring_attempted", "runtime/chat/voice wiring attempted")

    def test_43_memory_mutation_safety_flag_fails(self):
        self._assert_flag_fails("memory_mutation_attempted", "memory mutation attempted")

    def test_44_external_model_call_safety_flag_fails(self):
        self._assert_flag_fails("external_model_call_attempted", "external model call attempted")

    def test_45_advisor_call_safety_flag_fails(self):
        self._assert_flag_fails("advisor_call_attempted", "advisor call attempted")

    def test_46_provenance_guessing_safety_flag_fails(self):
        self._assert_flag_fails("provenance_guessing_attempted", "provenance guessing attempted")

    def test_47_unsupported_self_ownership_safety_flag_fails(self):
        self._assert_flag_fails("unsupported_self_ownership_claimed", "unsupported self-ownership claimed")

    def test_48_hidden_llm_authority_safety_flag_fails(self):
        self._assert_flag_fails("hidden_llm_authority", "hidden LLM authority")

    def test_49_hidden_provider_involvement_safety_flag_fails(self):
        self._assert_flag_fails("hidden_model_provider_involvement", "hidden model/provider involvement")

    def test_50_self_improvement_activation_safety_flag_fails(self):
        self._assert_flag_fails("self_improvement_activation_attempted", "self-improvement activation attempted")

    def test_51_raw_sensitive_disclosure_safety_flag_fails(self):
        self._assert_flag_fails("raw_sensitive_content_disclosed", "raw sensitive content disclosed")

    def test_52_selected_snapshot_with_raw_spoken_text_fails(self):
        errors = validate_who_said_that_log_lookup_result(result(selected_event_snapshots=[{"raw_spoken_text": "hello"}]))
        self.assertTrue(any("raw spoken text" in error for error in errors))

    def test_53_selected_snapshot_with_secret_api_key_token_private_data_fails(self):
        snapshot = {"summary": "secret api key sk-test token private user data"}
        errors = validate_who_said_that_log_lookup_result(result(selected_event_snapshots=[snapshot]))
        self.assertTrue(any("secret" in error for error in errors))
        self.assertTrue(any("API key" in error for error in errors))
        self.assertTrue(any("token" in error for error in errors))
        self.assertTrue(any("private user data" in error for error in errors))

    def test_54_path_policy_to_from_dict_roundtrip(self):
        item = policy(storage_format="json")
        self.assertEqual(item, who_said_that_log_lookup_path_policy_from_dict(who_said_that_log_lookup_path_policy_to_dict(item)))

    def test_55_request_to_from_dict_roundtrip(self):
        item = request(lookup_mode="by_trace_ref", requested_trace_ref="trace_a")
        self.assertEqual(item, who_said_that_log_lookup_request_from_dict(who_said_that_log_lookup_request_to_dict(item)))

    def test_56_result_to_from_dict_roundtrip(self):
        item = result(redacted_event_summaries=["count-only"], selected_event_count=1)
        self.assertEqual(item, who_said_that_log_lookup_result_from_dict(who_said_that_log_lookup_result_to_dict(item)))

    def test_57_single_result_summary_is_redacted(self):
        summary = summarize_who_said_that_log_lookup_result(result(redacted_event_summaries=["safe summary"]))
        encoded = json.dumps(summary, sort_keys=True)
        self.assertNotIn("safe summary", encoded)
        self.assertEqual(1, summary["redacted_event_summary_count"])

    def test_58_multiple_result_summary_is_redacted_count_only(self):
        summary = summarize_who_said_that_log_lookup_results([result(records_found=2), result(result_id="res_b", records_found=3, missing_log=True)])
        encoded = json.dumps(summary, sort_keys=True)
        self.assertNotIn("res_a", encoded)
        self.assertNotIn("res_b", encoded)
        self.assertEqual(2, summary["result_count"])
        self.assertEqual(5, summary["records_found_total"])

    def test_59_summary_does_not_contain_sensitive_text(self):
        item = result(
            redacted_event_summaries=["secret api key token raw spoken text raw benchmark answer key private user data official score"],
            errors=["secret"],
            warnings=["token"],
        )
        summary = summarize_who_said_that_log_lookup_result(item)
        encoded = json.dumps(summary, sort_keys=True).lower()
        for needle in ["api key", "token", "secret", "raw spoken text", "raw benchmark", "answer key", "private user data"]:
            self.assertNotIn(needle, encoded)

    def test_60_design_test_still_passes(self):
        subprocess.run([sys.executable, "weslr/tests/test_who_said_that_read_only_log_lookup_design_v1.py"], cwd=ROOT, check=True)

    def test_61_parserless_resolver_helper_tests_still_pass(self):
        subprocess.run([sys.executable, "weslr/tests/test_who_said_that_parserless_resolver_helpers_v1.py"], cwd=ROOT, check=True)

    def test_62_voice_attribution_log_schema_tests_still_pass(self):
        subprocess.run([sys.executable, "weslr/tests/test_voice_source_attribution_log_schema_v1.py"], cwd=ROOT, check=True)

    def test_63_release_gate_check_pass(self):
        subprocess.run([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=ROOT, check=True)
        subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=ROOT, check=True)

    def test_64_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_65_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_66_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_67_no_implementation_files_changed_beyond_allowed_schema_module_test(self):
        result = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, text=True, capture_output=True)
        changed = set()
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            changed.add(path)
        self.assertFalse(changed - ALLOWED_CHANGED_FILES, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED_FILES)}")


if __name__ == "__main__":
    unittest.main()
