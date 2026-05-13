from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.voice_source_attribution_log import (  # noqa: E402
    ALLOWED_AUTHORITY_LEVELS,
    ALLOWED_EVENT_TYPES,
    ALLOWED_SOURCE_SUBSYSTEMS,
    ALLOWED_TRUTH_CLASSES,
    VoiceAttributionLogEvent,
    VoiceAttributionLogPathPolicy,
    VoiceAttributionLogSafetyFlags,
    create_empty_voice_attribution_log_event,
    create_empty_voice_attribution_log_path_policy,
    summarize_voice_attribution_log_event,
    summarize_voice_attribution_log_path_policy,
    validate_voice_attribution_log_event,
    validate_voice_attribution_log_path_policy,
    voice_attribution_log_event_from_dict,
    voice_attribution_log_event_to_dict,
    voice_attribution_log_path_policy_from_dict,
    voice_attribution_log_path_policy_to_dict,
)

ALLOWED_CHANGED = {
    "weslr/voice_source_attribution_log.py",
    "weslr/tests/test_voice_source_attribution_log_schema_v1.py",
}
FORBIDDEN_CHANGED = {
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
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_event(**overrides):
    item = create_empty_voice_attribution_log_event(
        event_id="evt_001",
        event_type="pre_speak_attribution_draft",
        utterance_id="utt_001",
        attribution_record_snapshot={"schema_version": "1.0", "utterance_id": "utt_001"},
        output_provenance_id="out_001",
        source_subsystem="voice_gateway",
        spoken_text_hash="sha256:abc123",
        tts_engine="configured_tts_surface",
        stt_engine="configured_stt_surface",
        authority_level="voice_surface",
        truth_class="observed",
        redacted_summary="redacted attribution summary",
        trace_refs=["trace_001"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class VoiceSourceAttributionLogSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(VoiceAttributionLogSafetyFlags)
        self.assertTrue(VoiceAttributionLogPathPolicy)
        self.assertTrue(VoiceAttributionLogEvent)

    def test_02_path_policy_instantiates(self):
        item = VoiceAttributionLogPathPolicy()
        self.assertEqual("1.0", item.schema_version)

    def test_03_log_event_instantiates(self):
        item = VoiceAttributionLogEvent()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, VoiceAttributionLogSafetyFlags)

    def test_04_safe_path_policy_defaults(self):
        item = create_empty_voice_attribution_log_path_policy()
        self.assertTrue(item.append_only_required)
        self.assertTrue(item.redaction_required)
        self.assertFalse(item.raw_spoken_text_allowed)
        self.assertTrue(item.operator_review_required)
        self.assertFalse(item.allow_absolute_paths)
        self.assertFalse(item.allow_path_traversal)
        self.assertFalse(item.allow_external_storage)

    def test_05_default_path(self):
        self.assertEqual(".weslr/voice_source_attribution.jsonl", create_empty_voice_attribution_log_path_policy().log_path)

    def test_06_storage_format_jsonl_validates(self):
        self.assertNotIn("invalid storage_format", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(storage_format="jsonl")))

    def test_07_invalid_storage_format_fails(self):
        self.assertIn("invalid storage_format", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(storage_format="sqlite")))

    def test_08_append_only_disabled_fails(self):
        self.assertIn("append_only_required disabled", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(append_only_required=False)))

    def test_09_redaction_disabled_fails(self):
        self.assertIn("redaction_required disabled", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(redaction_required=False)))

    def test_10_raw_spoken_text_allowed_fails(self):
        self.assertIn("raw_spoken_text_allowed true", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(raw_spoken_text_allowed=True)))

    def test_11_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required disabled", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(operator_review_required=False)))

    def test_12_absolute_paths_allowed_fails(self):
        self.assertIn("absolute paths allowed", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(allow_absolute_paths=True)))

    def test_13_path_traversal_allowed_fails(self):
        self.assertIn("path traversal allowed", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(allow_path_traversal=True)))

    def test_14_external_storage_allowed_fails(self):
        self.assertIn("external storage allowed", validate_voice_attribution_log_path_policy(create_empty_voice_attribution_log_path_policy(allow_external_storage=True)))

    def test_15_all_event_types_validate(self):
        for value in ALLOWED_EVENT_TYPES:
            item = valid_event(event_type=value)
            if value == "attribution_query_requested":
                item.utterance_id = ""
            self.assertNotIn("invalid event_type", validate_voice_attribution_log_event(item))

    def test_16_invalid_event_type_fails(self):
        self.assertIn("invalid event_type", validate_voice_attribution_log_event(valid_event(event_type="bad")))

    def test_17_all_source_subsystems_validate(self):
        for value in ALLOWED_SOURCE_SUBSYSTEMS:
            self.assertNotIn("invalid source_subsystem", validate_voice_attribution_log_event(valid_event(source_subsystem=value)))

    def test_18_invalid_source_subsystem_fails(self):
        self.assertIn("invalid source_subsystem", validate_voice_attribution_log_event(valid_event(source_subsystem="bad")))

    def test_19_all_authority_levels_validate(self):
        for value in ALLOWED_AUTHORITY_LEVELS:
            self.assertNotIn("invalid authority_level", validate_voice_attribution_log_event(valid_event(authority_level=value)))

    def test_20_invalid_authority_level_fails(self):
        self.assertIn("invalid authority_level", validate_voice_attribution_log_event(valid_event(authority_level="bad")))

    def test_21_all_truth_classes_validate(self):
        for value in ALLOWED_TRUTH_CLASSES:
            self.assertNotIn("invalid truth_class", validate_voice_attribution_log_event(valid_event(truth_class=value)))

    def test_22_invalid_truth_class_fails(self):
        self.assertIn("invalid truth_class", validate_voice_attribution_log_event(valid_event(truth_class="bad")))

    def test_23_missing_event_id_fails(self):
        self.assertIn("missing event_id", validate_voice_attribution_log_event(valid_event(event_id="")))

    def test_24_missing_utterance_id_fails_for_pre_speak_event(self):
        self.assertIn("missing utterance_id", validate_voice_attribution_log_event(valid_event(event_type="pre_speak_attribution_draft", utterance_id="")))

    def test_25_spoken_text_stored_true_fails(self):
        self.assertIn("spoken_text_stored true", validate_voice_attribution_log_event(valid_event(spoken_text_stored=True)))

    def test_26_llm_assisted_event_without_provider_fails(self):
        self.assertIn("llm_assisted requires model_provider", validate_voice_attribution_log_event(valid_event(llm_assisted=True, model_provider="", model_name="model-a")))

    def test_27_llm_assisted_event_without_model_name_fails(self):
        self.assertIn("llm_assisted requires model_name", validate_voice_attribution_log_event(valid_event(llm_assisted=True, model_provider="provider-a", model_name="")))

    def test_28_llm_assisted_system_fact_without_trace_refs_fails(self):
        errors = validate_voice_attribution_log_event(valid_event(llm_assisted=True, model_provider="provider-a", model_name="model-a", authority_level="system_fact", trace_refs=[]))
        self.assertIn("system_fact authority requires trace_refs for LLM-assisted voice", errors)

    def test_29_confirmed_speech_event_without_trace_refs_fails(self):
        self.assertIn("post-speak event requires trace_refs", validate_voice_attribution_log_event(valid_event(event_type="post_speak_attribution_confirmed", trace_refs=[])))

    def test_30_failed_speech_event_without_trace_refs_fails(self):
        self.assertIn("post-speak event requires trace_refs", validate_voice_attribution_log_event(valid_event(event_type="post_speak_attribution_failed", trace_refs=[])))

    def assert_flag_fails(self, field: str, expected: str):
        flags = VoiceAttributionLogSafetyFlags(**{field: True})
        self.assertIn(expected, validate_voice_attribution_log_event(valid_event(safety_flags=flags)))

    def test_31_log_write_attempted_flag_fails(self):
        self.assert_flag_fails("log_write_attempted", "log write attempted")

    def test_32_raw_spoken_text_stored_flag_fails(self):
        self.assert_flag_fails("raw_spoken_text_stored", "raw spoken text stored")

    def test_33_provenance_guessing_flag_fails(self):
        self.assert_flag_fails("provenance_guessing_attempted", "provenance guessing attempted")

    def test_34_hidden_llm_authority_flag_fails(self):
        self.assert_flag_fails("hidden_llm_authority", "hidden LLM authority")

    def test_35_hidden_model_provider_involvement_flag_fails(self):
        self.assert_flag_fails("hidden_model_provider_involvement", "hidden model/provider involvement")

    def test_36_memory_mutation_flag_fails(self):
        self.assert_flag_fails("memory_mutation_attempted", "memory mutation attempted")

    def test_37_queue_write_flag_fails(self):
        self.assert_flag_fails("queue_write_attempted", "queue write attempted")

    def test_38_registry_persistence_flag_fails(self):
        self.assert_flag_fails("registry_persistence_attempted", "registry persistence attempted")

    def test_39_runtime_voice_wiring_flag_fails(self):
        self.assert_flag_fails("runtime_voice_wiring_attempted", "runtime voice wiring attempted")

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

    def test_46_path_policy_to_from_dict_roundtrip_works(self):
        item = create_empty_voice_attribution_log_path_policy(retention_policy="operator_defined")
        self.assertEqual(item, voice_attribution_log_path_policy_from_dict(voice_attribution_log_path_policy_to_dict(item)))

    def test_47_event_to_from_dict_roundtrip_works(self):
        item = valid_event(llm_assisted=True, model_provider="provider-a", model_name="model-a")
        self.assertEqual(item, voice_attribution_log_event_from_dict(voice_attribution_log_event_to_dict(item)))

    def test_48_path_policy_summary_is_redacted(self):
        item = create_empty_voice_attribution_log_path_policy(retention_policy="secret token bearer abc.def password:=x")
        summary = summarize_voice_attribution_log_path_policy(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["secret", "token", "bearer abc.def", "password"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_49_event_summary_is_redacted(self):
        item = valid_event(redacted_summary="api key sk-abc123 raw spoken text answer key private user data")
        summary = summarize_voice_attribution_log_event(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "raw spoken text", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_50_summaries_do_not_contain_sensitive_raw_text(self):
        policy = create_empty_voice_attribution_log_path_policy(institution_storage_policy="secret token bearer abc.def private user data")
        event = valid_event(
            redacted_summary="raw spoken text raw benchmark text answer key official score password:=x",
            attribution_record_snapshot={"transcript": "spoken text: hello", "api_key": "sk-abc123"},
        )
        rendered = (json.dumps(summarize_voice_attribution_log_path_policy(policy)) + json.dumps(summarize_voice_attribution_log_event(event))).lower()
        for forbidden in ["sk-abc123", "token", "secret", "bearer abc.def", "raw spoken text", "raw benchmark text", "answer key", "official score", "password", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_51_logging_design_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_logging_design_v1.py"], cwd=str(ROOT))

    def test_52_voice_attribution_schema_test_still_passes(self):
        subprocess.check_call([sys.executable, "weslr/tests/test_voice_source_attribution_schema_v1.py"], cwd=str(ROOT))

    def test_53_release_gate_check_pass(self):
        subprocess.check_call([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT))
        subprocess.check_call(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT))

    def test_54_no_attribution_log_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "voice_source_attribution.jsonl").exists())

    def test_55_no_persistent_registry_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.json").exists())
        self.assertFalse((ROOT / ".weslr" / "provenance_source_registry.jsonl").exists())

    def test_56_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_57_no_implementation_files_changed_beyond_allowed_schema_module_test(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
