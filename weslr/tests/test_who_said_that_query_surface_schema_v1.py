from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.who_said_that_query_surface import (  # noqa: E402
    ALLOWED_CHANNELS,
    ALLOWED_INTENT_TYPES,
    ALLOWED_LOOKBACK_MODES,
    ALLOWED_OWNERSHIP_CATEGORIES,
    WhoSaidThatAnswer,
    WhoSaidThatQueryIntent,
    WhoSaidThatQuerySafetyFlags,
    create_empty_who_said_that_answer,
    create_empty_who_said_that_query_intent,
    summarize_who_said_that_answer,
    summarize_who_said_that_answers,
    validate_who_said_that_answer,
    validate_who_said_that_query_intent,
    who_said_that_answer_from_dict,
    who_said_that_answer_to_dict,
    who_said_that_query_intent_from_dict,
    who_said_that_query_intent_to_dict,
)

ALLOWED_CHANGED = {
    "weslr/who_said_that_query_surface.py",
    "weslr/tests/test_who_said_that_query_surface_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_source_attribution_log.py",
    "weslr/voice_source_attribution.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/output_provenance.py",
    "weslr/provenance_source_registry.py",
    "weslr/source_registry_review_queue_mapping.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_intent(**overrides):
    item = create_empty_who_said_that_query_intent(
        query_id="query_001",
        intent_type="who_said_that",
        query_text_hash="sha256:q",
        input_channel="chat",
        lookback_mode="most_recent",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_answer(**overrides):
    item = create_empty_who_said_that_answer(
        answer_id="answer_001",
        query_id="query_001",
        intent_type="who_said_that",
        attribution_found=True,
        ownership_category="operator_triggered",
        source_subsystem="operator_cli",
        source_module="weslr.operator_cli",
        generated_by="operator_cli",
        trigger="operator action",
        trigger_type="operator_action",
        authority_level="observed_event",
        truth_class="observed",
        confidence="medium",
        trace_ref_count=1,
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class WhoSaidThatQuerySurfaceSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(WhoSaidThatQuerySafetyFlags)
        self.assertTrue(WhoSaidThatQueryIntent)
        self.assertTrue(WhoSaidThatAnswer)

    def test_02_empty_query_intent_instantiates(self):
        self.assertEqual("1.0", WhoSaidThatQueryIntent().schema_version)

    def test_03_empty_answer_instantiates(self):
        self.assertEqual("1.0", WhoSaidThatAnswer().schema_version)

    def test_04_safe_defaults(self):
        intent = create_empty_who_said_that_query_intent()
        answer = create_empty_who_said_that_answer()
        self.assertFalse(intent.raw_query_stored)
        self.assertTrue(intent.operator_review_required)
        self.assertFalse(answer.attribution_found)
        self.assertEqual("unknown_unattributed", answer.ownership_category)
        self.assertTrue(answer.operator_review_required)

    def test_05_all_intent_types_validate(self):
        for value in ALLOWED_INTENT_TYPES:
            self.assertNotIn("invalid intent_type", validate_who_said_that_query_intent(valid_intent(intent_type=value)))

    def test_06_invalid_intent_type_fails(self):
        self.assertIn("invalid intent_type", validate_who_said_that_query_intent(valid_intent(intent_type="bad")))

    def test_07_all_input_channels_validate(self):
        for value in ALLOWED_CHANNELS:
            self.assertNotIn("invalid input_channel", validate_who_said_that_query_intent(valid_intent(input_channel=value)))

    def test_08_invalid_input_channel_fails(self):
        self.assertIn("invalid input_channel", validate_who_said_that_query_intent(valid_intent(input_channel="bad")))

    def test_09_all_lookback_modes_validate(self):
        for value in ALLOWED_LOOKBACK_MODES:
            item = valid_intent(lookback_mode=value)
            if value == "by_utterance_id":
                item.requested_utterance_id = "utt_001"
            self.assertNotIn("invalid lookback_mode", validate_who_said_that_query_intent(item))

    def test_10_invalid_lookback_mode_fails(self):
        self.assertIn("invalid lookback_mode", validate_who_said_that_query_intent(valid_intent(lookback_mode="bad")))

    def test_11_all_ownership_categories_validate(self):
        for value in ALLOWED_OWNERSHIP_CATEGORIES:
            item = valid_answer(ownership_category=value)
            if value == "unknown_unattributed":
                item.attribution_found = False
                item.source_module = ""
                item.generated_by = ""
            self.assertNotIn("invalid ownership_category", validate_who_said_that_answer(item))

    def test_12_invalid_ownership_category_fails(self):
        self.assertIn("invalid ownership_category", validate_who_said_that_answer(valid_answer(ownership_category="bad")))

    def test_13_missing_query_id_fails(self):
        self.assertIn("missing query_id", validate_who_said_that_query_intent(valid_intent(query_id="")))

    def test_14_raw_query_stored_fails_by_default(self):
        self.assertIn("raw_query_stored true", validate_who_said_that_query_intent(valid_intent(raw_query_stored=True)))

    def test_15_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required disabled", validate_who_said_that_query_intent(valid_intent(operator_review_required=False)))

    def test_16_by_utterance_id_without_utterance_id_fails(self):
        self.assertIn("by_utterance_id requires requested_utterance_id", validate_who_said_that_query_intent(valid_intent(lookback_mode="by_utterance_id", requested_utterance_id="")))

    def test_17_missing_answer_id_fails(self):
        self.assertIn("missing answer_id", validate_who_said_that_answer(valid_answer(answer_id="")))

    def test_18_missing_answer_query_id_fails(self):
        self.assertIn("missing query_id", validate_who_said_that_answer(valid_answer(query_id="")))

    def test_19_attribution_missing_with_ownership_not_unknown_fails(self):
        self.assertIn("attribution missing requires unknown_unattributed ownership", validate_who_said_that_answer(valid_answer(attribution_found=False, ownership_category="weslr_owned")))

    def test_20_attribution_missing_with_self_ownership_claim_fails(self):
        self.assertIn("attribution missing cannot claim source/generated_by/model/provider as fact", validate_who_said_that_answer(valid_answer(attribution_found=False, ownership_category="unknown_unattributed", generated_by="weslr")))

    def test_21_weslr_owned_without_attribution_and_trace_fails(self):
        self.assertIn("weslr_owned requires attribution_found and trace refs", validate_who_said_that_answer(valid_answer(ownership_category="weslr_owned", attribution_found=True, trace_ref_count=0)))

    def test_22_llm_assisted_answer_without_provider_fails(self):
        self.assertIn("llm_assisted requires model_provider", validate_who_said_that_answer(valid_answer(llm_assisted=True, model_provider="", model_name="model-a")))

    def test_23_llm_assisted_answer_without_model_name_fails(self):
        self.assertIn("llm_assisted requires model_name", validate_who_said_that_answer(valid_answer(llm_assisted=True, model_provider="provider-a", model_name="")))

    def test_24_system_fact_authority_for_llm_without_trace_fails(self):
        self.assertIn("system_fact authority requires trace refs for LLM-assisted answer", validate_who_said_that_answer(valid_answer(llm_assisted=True, model_provider="provider-a", model_name="model-a", authority_level="system_fact", trace_ref_count=0)))

    def test_25_verified_system_fact_truth_for_llm_without_trace_fails(self):
        self.assertIn("verified_system_fact truth requires trace refs for LLM-assisted answer", validate_who_said_that_answer(valid_answer(llm_assisted=True, model_provider="provider-a", model_name="model-a", truth_class="verified_system_fact", trace_ref_count=0)))

    def assert_flag_fails(self, field: str, expected: str):
        flags = WhoSaidThatQuerySafetyFlags(**{field: True})
        self.assertIn(expected, validate_who_said_that_answer(valid_answer(safety_flags=flags)))

    def test_26_provenance_guessing_flag_fails(self): self.assert_flag_fails("provenance_guessing_attempted", "provenance guessing attempted")
    def test_27_unsupported_self_ownership_flag_fails(self): self.assert_flag_fails("unsupported_self_ownership_claimed", "unsupported self-ownership claimed")
    def test_28_hidden_llm_authority_flag_fails(self): self.assert_flag_fails("hidden_llm_authority", "hidden LLM authority")
    def test_29_hidden_model_provider_involvement_flag_fails(self): self.assert_flag_fails("hidden_model_provider_involvement", "hidden model/provider involvement")
    def test_30_unattributed_output_treated_as_weslr_owned_flag_fails(self): self.assert_flag_fails("unattributed_output_treated_as_weslr_owned", "unattributed output treated as WESLR-owned")
    def test_31_raw_spoken_text_disclosed_flag_fails(self): self.assert_flag_fails("raw_spoken_text_disclosed", "raw spoken text disclosed")
    def test_32_memory_mutation_flag_fails(self): self.assert_flag_fails("memory_mutation_attempted", "memory mutation attempted")
    def test_33_queue_write_flag_fails(self): self.assert_flag_fails("queue_write_attempted", "queue write attempted")
    def test_34_log_read_flag_fails(self): self.assert_flag_fails("log_read_attempted", "log read attempted")
    def test_35_log_write_flag_fails(self): self.assert_flag_fails("log_write_attempted", "log write attempted")
    def test_36_runtime_voice_wiring_flag_fails(self): self.assert_flag_fails("runtime_voice_wiring_attempted", "runtime voice wiring attempted")
    def test_37_external_model_call_flag_fails(self): self.assert_flag_fails("external_model_call_attempted", "external model call attempted")
    def test_38_self_improvement_activation_flag_fails(self): self.assert_flag_fails("self_improvement_activation_attempted", "self-improvement activation attempted")
    def test_39_answer_selection_flag_fails(self): self.assert_flag_fails("answer_selection_attempted", "answer selection attempted")
    def test_40_truth_authority_flag_fails(self): self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")
    def test_41_soundness_authority_flag_fails(self): self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")
    def test_42_official_score_flag_fails(self): self.assert_flag_fails("official_score_claimed", "official score claimed")

    def test_43_query_intent_to_from_dict_roundtrip_works(self):
        item = valid_intent()
        self.assertEqual(item, who_said_that_query_intent_from_dict(who_said_that_query_intent_to_dict(item)))

    def test_44_answer_to_from_dict_roundtrip_works(self):
        item = valid_answer()
        self.assertEqual(item, who_said_that_answer_from_dict(who_said_that_answer_to_dict(item)))

    def test_45_single_answer_summary_is_redacted(self):
        summary = summarize_who_said_that_answer(valid_answer(answer_id="api key sk-abc123", redacted_answer_summary="raw spoken text answer key private user data password:=x"))
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "raw spoken text", "answer key", "private user data", "password"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_46_multiple_answer_summary_is_redacted_count_only(self):
        summary = summarize_who_said_that_answers([valid_answer(), valid_answer(answer_id="answer_002", ownership_category="unknown_unattributed", attribution_found=False, source_module="", generated_by="")])
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])

    def test_47_summary_does_not_contain_sensitive_raw_text(self):
        answer = valid_answer(answer_id="secret token bearer abc.def", redacted_answer_summary="raw spoken text raw benchmark text answer key official score private user data password:=x")
        rendered = json.dumps(summarize_who_said_that_answers([answer])) + json.dumps(summarize_who_said_that_answer(answer))
        rendered = rendered.lower()
        for forbidden in ["secret", "token", "bearer abc.def", "raw spoken text", "raw benchmark text", "answer key", "official score", "private user data", "password"]:
            self.assertNotIn(forbidden, rendered)

    def test_48_query_surface_design_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_who_said_that_query_surface_design_v1.py"], cwd=str(ROOT))

    def test_49_voice_attribution_logging_helper_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_logging_helpers_v1.py"], cwd=str(ROOT))

    def test_50_voice_attribution_log_schema_tests_still_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_log_schema_v1.py"], cwd=str(ROOT))

    def test_51_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))

    def test_52_no_voice_attribution_log_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_53_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_54_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_55_no_implementation_files_changed_beyond_allowed_schema_module_test(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
