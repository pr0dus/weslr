from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.voice_source_attribution import (  # noqa: E402
    ALLOWED_AUTHORITY_LEVELS,
    ALLOWED_CHANNELS,
    ALLOWED_CONFIDENCE_VALUES,
    ALLOWED_SOURCE_SUBSYSTEMS,
    ALLOWED_TRIGGER_TYPES,
    ALLOWED_TRUTH_CLASSES,
    VoiceSourceAttributionRecord,
    VoiceSourceAttributionSafetyFlags,
    create_empty_voice_source_attribution_record,
    summarize_voice_source_attribution_record,
    summarize_voice_source_attribution_records,
    validate_voice_source_attribution_record,
    voice_source_attribution_record_from_dict,
    voice_source_attribution_record_to_dict,
)

ALLOWED_CHANGED = {
    "weslr/voice_source_attribution.py",
    "weslr/tests/test_voice_source_attribution_schema_v1.py",
}
FORBIDDEN_CHANGED = {
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
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


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


class VoiceSourceAttributionSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(VoiceSourceAttributionRecord)
        self.assertTrue(VoiceSourceAttributionSafetyFlags)

    def test_02_empty_attribution_record_instantiates(self):
        item = VoiceSourceAttributionRecord()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, VoiceSourceAttributionSafetyFlags)

    def test_03_safe_defaults(self):
        item = create_empty_voice_source_attribution_record()
        self.assertEqual("unknown", item.source_subsystem)
        self.assertEqual("voice", item.output_channel)
        self.assertTrue(item.operator_review_required)
        self.assertFalse(item.spoken_text_stored)
        self.assertFalse(item.llm_assisted)
        self.assertFalse(item.advisor_assisted)
        self.assertFalse(item.ambient_loop_involved)
        self.assertFalse(item.proactive_suggestion_involved)

    def test_04_all_source_subsystems_validate(self):
        for value in ALLOWED_SOURCE_SUBSYSTEMS:
            self.assertNotIn("invalid source_subsystem", validate_voice_source_attribution_record(valid_record(source_subsystem=value)))

    def test_05_invalid_source_subsystem_fails(self):
        self.assertIn("invalid source_subsystem", validate_voice_source_attribution_record(valid_record(source_subsystem="bad")))

    def test_06_all_trigger_types_validate(self):
        for value in ALLOWED_TRIGGER_TYPES:
            self.assertNotIn("invalid trigger_type", validate_voice_source_attribution_record(valid_record(trigger_type=value)))

    def test_07_invalid_trigger_type_fails(self):
        self.assertIn("invalid trigger_type", validate_voice_source_attribution_record(valid_record(trigger_type="bad")))

    def test_08_all_channels_validate(self):
        for value in ALLOWED_CHANNELS:
            self.assertNotIn("invalid input_channel", validate_voice_source_attribution_record(valid_record(input_channel=value)))
            self.assertNotIn("invalid output_channel", validate_voice_source_attribution_record(valid_record(output_channel=value)))

    def test_09_invalid_channel_fails(self):
        self.assertIn("invalid input_channel", validate_voice_source_attribution_record(valid_record(input_channel="bad")))
        self.assertIn("invalid output_channel", validate_voice_source_attribution_record(valid_record(output_channel="bad")))

    def test_10_all_authority_levels_validate(self):
        for value in ALLOWED_AUTHORITY_LEVELS:
            item = valid_record(authority_level=value)
            if value == "system_fact":
                item.llm_assisted = False
            self.assertNotIn("invalid authority_level", validate_voice_source_attribution_record(item))

    def test_11_invalid_authority_level_fails(self):
        self.assertIn("invalid authority_level", validate_voice_source_attribution_record(valid_record(authority_level="bad")))

    def test_12_all_truth_classes_validate(self):
        for value in ALLOWED_TRUTH_CLASSES:
            self.assertNotIn("invalid truth_class", validate_voice_source_attribution_record(valid_record(truth_class=value)))

    def test_13_invalid_truth_class_fails(self):
        self.assertIn("invalid truth_class", validate_voice_source_attribution_record(valid_record(truth_class="bad")))

    def test_14_all_confidence_values_validate(self):
        for value in ALLOWED_CONFIDENCE_VALUES:
            self.assertNotIn("invalid confidence", validate_voice_source_attribution_record(valid_record(confidence=value)))

    def test_15_invalid_confidence_fails(self):
        self.assertIn("invalid confidence", validate_voice_source_attribution_record(valid_record(confidence="certain")))

    def test_16_missing_utterance_id_fails(self):
        self.assertIn("missing utterance_id", validate_voice_source_attribution_record(valid_record(utterance_id="")))

    def test_17_missing_output_provenance_id_fails(self):
        self.assertIn("missing output_provenance_id", validate_voice_source_attribution_record(valid_record(output_provenance_id="")))

    def test_18_missing_source_module_fails(self):
        self.assertIn("missing source_module", validate_voice_source_attribution_record(valid_record(source_module="")))

    def test_19_missing_generated_by_fails(self):
        self.assertIn("missing generated_by", validate_voice_source_attribution_record(valid_record(generated_by="")))

    def test_20_ambient_record_without_trigger_fails(self):
        errors = validate_voice_source_attribution_record(valid_record(source_subsystem="ambient_voice_loop", ambient_loop_involved=True, trigger=""))
        self.assertIn("missing trigger for ambient/proactive voice record", errors)

    def test_21_proactive_record_without_trigger_fails(self):
        errors = validate_voice_source_attribution_record(valid_record(source_subsystem="proactive_suggestions", proactive_suggestion_involved=True, trigger=""))
        self.assertIn("missing trigger for ambient/proactive voice record", errors)

    def test_22_spoken_text_stored_true_fails_by_default(self):
        self.assertIn("spoken_text_stored true", validate_voice_source_attribution_record(valid_record(spoken_text_stored=True)))

    def test_23_llm_assisted_record_without_provider_fails(self):
        errors = validate_voice_source_attribution_record(valid_record(llm_assisted=True, model_provider="", model_name="model-a"))
        self.assertIn("llm_assisted requires model_provider", errors)

    def test_24_llm_assisted_record_without_model_name_fails(self):
        errors = validate_voice_source_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name=""))
        self.assertIn("llm_assisted requires model_name", errors)

    def test_25_advisor_assisted_record_without_advisor_review_id_fails(self):
        errors = validate_voice_source_attribution_record(valid_record(advisor_assisted=True, related_advisor_review_ids=[]))
        self.assertIn("advisor_assisted requires related_advisor_review_ids", errors)

    def test_26_operator_review_disabled_fails_for_llm_assisted_record(self):
        errors = validate_voice_source_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a", operator_review_required=False))
        self.assertIn("operator_review_required must remain true for unknown/assisted/ambient/proactive records", errors)

    def test_27_operator_review_disabled_fails_for_unknown_source_record(self):
        errors = validate_voice_source_attribution_record(valid_record(source_subsystem="unknown", operator_review_required=False))
        self.assertIn("operator_review_required must remain true for unknown/assisted/ambient/proactive records", errors)

    def test_28_system_fact_authority_fails_for_unverified_llm_assisted_voice(self):
        errors = validate_voice_source_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a", authority_level="system_fact", trace_refs=["trace_001"]))
        self.assertIn("system_fact authority requires verified trace for LLM-assisted voice", errors)

    def test_29_verified_system_fact_truth_fails_for_unverified_llm_assisted_voice(self):
        errors = validate_voice_source_attribution_record(valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a", truth_class="verified_system_fact", trace_refs=["trace_001"]))
        self.assertIn("verified_system_fact truth requires verified trace for LLM-assisted voice", errors)

    def test_30_missing_trace_refs_fails(self):
        self.assertIn("empty trace_refs", validate_voice_source_attribution_record(valid_record(trace_refs=[])))

    def assert_flag_fails(self, field: str, expected: str):
        flags = VoiceSourceAttributionSafetyFlags(**{field: True})
        self.assertIn(expected, validate_voice_source_attribution_record(valid_record(safety_flags=flags)))

    def test_31_provenance_guessing_safety_flag_fails(self):
        self.assert_flag_fails("provenance_guessing_attempted", "provenance guessing attempted")

    def test_32_hidden_llm_authority_flag_fails(self):
        self.assert_flag_fails("hidden_llm_authority", "hidden LLM authority")

    def test_33_hidden_model_provider_involvement_flag_fails(self):
        self.assert_flag_fails("hidden_model_provider_involvement", "hidden model/provider involvement")

    def test_34_unattributed_voice_proactive_output_flag_fails(self):
        self.assert_flag_fails("unattributed_voice_or_proactive_output", "unattributed voice/proactive output")

    def test_35_raw_sensitive_spoken_text_storage_flag_fails(self):
        self.assert_flag_fails("raw_sensitive_spoken_text_stored", "raw sensitive spoken text stored")

    def test_36_memory_mutation_from_attribution_flag_fails(self):
        self.assert_flag_fails("memory_mutation_from_attribution", "memory mutation from attribution")

    def test_37_runtime_voice_wiring_flag_fails(self):
        self.assert_flag_fails("runtime_voice_wiring_attempted", "runtime voice wiring attempted")

    def test_38_queue_write_flag_fails(self):
        self.assert_flag_fails("queue_write_attempted", "queue write attempted")

    def test_39_registry_persistence_flag_fails(self):
        self.assert_flag_fails("registry_persistence_attempted", "registry persistence attempted")

    def test_40_external_model_call_flag_fails(self):
        self.assert_flag_fails("external_model_call_attempted", "external model call attempted")

    def test_41_self_improvement_activation_flag_fails(self):
        self.assert_flag_fails("self_improvement_activation_attempted", "self-improvement activation attempted")

    def test_42_answer_selection_flag_fails(self):
        self.assert_flag_fails("answer_selection_attempted", "answer selection attempted")

    def test_43_truth_authority_flag_fails(self):
        self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")

    def test_44_soundness_authority_flag_fails(self):
        self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_45_official_score_flag_fails(self):
        self.assert_flag_fails("official_score_claimed", "official score claimed")

    def test_46_to_from_dict_roundtrip_works(self):
        item = valid_record(llm_assisted=True, model_provider="provider-a", model_name="model-a")
        restored = voice_source_attribution_record_from_dict(voice_source_attribution_record_to_dict(item))
        self.assertEqual(item, restored)

    def test_47_single_summary_is_redacted(self):
        item = valid_record(
            utterance_id="utt_secret",
            source_module="api key sk-abc123",
            generated_by="Bearer abc.def",
            trigger="password:=x raw benchmark text answer key private user data",
        )
        summary = summarize_voice_source_attribution_record(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "bearer abc.def", "password", "raw benchmark text", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])
        self.assertNotIn("trigger", summary)

    def test_48_multiple_summary_is_redacted_count_only(self):
        items = [
            valid_record(utterance_id="utt_1"),
            valid_record(utterance_id="utt_2", source_subsystem="proactive_suggestions", proactive_suggestion_involved=True, trigger="scan result"),
        ]
        summary = summarize_voice_source_attribution_records(items)
        rendered = json.dumps(summary).lower()
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertNotIn("utt_1", rendered)
        self.assertNotIn("scan result", rendered)

    def test_49_summary_does_not_contain_sensitive_raw_text(self):
        item = valid_record(
            utterance_id="utt_api_key_token_secret",
            source_module="secret token bearer abc.def",
            generated_by="private user data",
            trigger="raw benchmark text answer key official score password:=x",
        )
        single = json.dumps(summarize_voice_source_attribution_record(item)).lower()
        multiple = json.dumps(summarize_voice_source_attribution_records([item])).lower()
        for rendered in [single, multiple]:
            for forbidden in ["api_key", "token", "secret", "bearer abc.def", "raw benchmark text", "answer key", "official score", "password", "private user data"]:
                self.assertNotIn(forbidden, rendered)

    def test_50_design_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_design_v1.py"], cwd=str(ROOT))

    def test_51_output_provenance_envelope_schema_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_output_provenance_envelope_schema_v1.py"], cwd=str(ROOT))

    def test_52_provenance_source_registry_schema_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_provenance_source_registry_schema_v1.py"], cwd=str(ROOT))

    def test_53_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))

    def test_54_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_55_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_56_no_implementation_files_changed_beyond_allowed_schema_module_test(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
