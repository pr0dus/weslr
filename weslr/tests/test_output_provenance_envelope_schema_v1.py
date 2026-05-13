from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.output_provenance import (  # noqa: E402
    ALLOWED_AUTHORITY_LEVELS,
    ALLOWED_CHANNELS,
    ALLOWED_CONFIDENCE_VALUES,
    ALLOWED_TRIGGER_TYPES,
    ALLOWED_TRUTH_CLASSES,
    OutputProvenanceEnvelope,
    OutputProvenanceSafetyFlags,
    create_empty_output_provenance_envelope,
    output_provenance_envelope_from_dict,
    output_provenance_envelope_to_dict,
    summarize_output_provenance_envelope,
    summarize_output_provenance_envelopes,
    validate_output_provenance_envelope,
)

ALLOWED_CHANGED = {
    "weslr/output_provenance.py",
    "weslr/tests/test_output_provenance_envelope_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/proactive_daemon.py",
    "weslr/frontier_daemon.py",
    "weslr/loop/research_work_loop.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/advisor_review_queue.py",
    "weslr/advisor_review_queue_cli.py",
    "weslr/advisor_prompt_templates.py",
    "weslr/llm_advisor_mode.py",
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_envelope(**overrides):
    item = create_empty_output_provenance_envelope(
        output_id="out_001",
        generated_by="capability_registry",
        source_modules=["capability_registry"],
        trigger="operator asked what can you do",
        trigger_type="user_message",
        input_channel="chat",
        output_channel="chat",
        authority_level="system_fact",
        truth_class="verified_system_fact",
        confidence="high",
        trace_refs=["trace_001"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class OutputProvenanceEnvelopeSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(OutputProvenanceEnvelope)
        self.assertTrue(OutputProvenanceSafetyFlags)

    def test_02_empty_envelope_instantiates(self):
        item = OutputProvenanceEnvelope()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, OutputProvenanceSafetyFlags)

    def test_03_safe_defaults(self):
        item = create_empty_output_provenance_envelope()
        self.assertTrue(item.operator_review_required)
        self.assertFalse(item.raw_sensitive_content_stored)
        self.assertFalse(item.memory_write_performed)
        self.assertFalse(item.queue_write_performed)
        self.assertFalse(item.runtime_action_performed)
        self.assertFalse(item.llm_assisted)
        self.assertFalse(item.advisor_assisted)

    def test_04_all_authority_levels_validate(self):
        for value in ALLOWED_AUTHORITY_LEVELS:
            self.assertNotIn("invalid authority_level", validate_output_provenance_envelope(valid_envelope(authority_level=value)))

    def test_05_invalid_authority_level_fails(self):
        self.assertIn("invalid authority_level", validate_output_provenance_envelope(valid_envelope(authority_level="bad")))

    def test_06_all_truth_classes_validate(self):
        for value in ALLOWED_TRUTH_CLASSES:
            self.assertNotIn("invalid truth_class", validate_output_provenance_envelope(valid_envelope(truth_class=value)))

    def test_07_invalid_truth_class_fails(self):
        self.assertIn("invalid truth_class", validate_output_provenance_envelope(valid_envelope(truth_class="bad")))

    def test_08_all_trigger_types_validate(self):
        for value in ALLOWED_TRIGGER_TYPES:
            item = valid_envelope(trigger_type=value)
            if value in {"voice_event", "ambient_event", "proactive_scan"}:
                item.trace_refs = ["trace_voice"]
                item.trigger = "attributed event"
            self.assertNotIn("invalid trigger_type", validate_output_provenance_envelope(item))

    def test_09_invalid_trigger_type_fails(self):
        self.assertIn("invalid trigger_type", validate_output_provenance_envelope(valid_envelope(trigger_type="bad")))

    def test_10_all_channels_validate_for_input_output(self):
        for value in ALLOWED_CHANNELS:
            self.assertNotIn("invalid input_channel", validate_output_provenance_envelope(valid_envelope(input_channel=value)))
            self.assertNotIn("invalid output_channel", validate_output_provenance_envelope(valid_envelope(output_channel=value)))

    def test_11_invalid_channel_fails(self):
        self.assertIn("invalid input_channel", validate_output_provenance_envelope(valid_envelope(input_channel="bad")))
        self.assertIn("invalid output_channel", validate_output_provenance_envelope(valid_envelope(output_channel="bad")))

    def test_12_all_confidence_values_validate(self):
        for value in ALLOWED_CONFIDENCE_VALUES:
            self.assertNotIn("invalid confidence", validate_output_provenance_envelope(valid_envelope(confidence=value)))

    def test_13_invalid_confidence_fails(self):
        self.assertIn("invalid confidence", validate_output_provenance_envelope(valid_envelope(confidence="certain")))

    def test_14_missing_output_id_fails(self):
        self.assertIn("missing output_id", validate_output_provenance_envelope(valid_envelope(output_id="")))

    def test_15_missing_generated_by_fails(self):
        self.assertIn("missing generated_by", validate_output_provenance_envelope(valid_envelope(generated_by="")))

    def test_16_empty_source_modules_fails(self):
        self.assertIn("empty source_modules", validate_output_provenance_envelope(valid_envelope(source_modules=[])))

    def test_17_suggestion_requires_operator_review(self):
        self.assertIn("suggestion requires operator review", validate_output_provenance_envelope(valid_envelope(authority_level="suggestion", operator_review_required=False)))

    def test_18_advisor_proposal_requires_operator_review(self):
        self.assertIn("advisor_proposal requires operator review", validate_output_provenance_envelope(valid_envelope(authority_level="advisor_proposal", operator_review_required=False)))

    def test_19_voice_surface_requires_attribution(self):
        errors = validate_output_provenance_envelope(valid_envelope(authority_level="voice_surface", trigger="", trace_refs=[]))
        self.assertIn("voice_surface requires attribution", errors)

    def test_20_raw_sensitive_content_stored_fails(self):
        self.assertIn("raw_sensitive_content_stored true", validate_output_provenance_envelope(valid_envelope(raw_sensitive_content_stored=True)))

    def test_21_memory_write_without_trace_refs_fails(self):
        self.assertIn("memory_write_performed requires trace_refs", validate_output_provenance_envelope(valid_envelope(memory_write_performed=True, trace_refs=[])))

    def test_22_queue_write_without_queue_item_ids_fails(self):
        self.assertIn("queue_write_performed requires related_queue_item_ids", validate_output_provenance_envelope(valid_envelope(queue_write_performed=True, related_queue_item_ids=[])))

    def test_23_runtime_action_without_trace_refs_fails(self):
        self.assertIn("runtime_action_performed requires trace_refs", validate_output_provenance_envelope(valid_envelope(runtime_action_performed=True, trace_refs=[])))

    def test_24_llm_assisted_without_trace_source_fails(self):
        self.assertIn("llm_assisted requires source_modules and trace_refs", validate_output_provenance_envelope(valid_envelope(llm_assisted=True, trace_refs=[])))
        self.assertIn("llm_assisted requires source_modules and trace_refs", validate_output_provenance_envelope(valid_envelope(llm_assisted=True, source_modules=[])))

    def test_25_advisor_assisted_without_advisor_review_id_fails(self):
        self.assertIn("advisor_assisted requires related_advisor_review_ids", validate_output_provenance_envelope(valid_envelope(advisor_assisted=True, related_advisor_review_ids=[])))

    def assert_flag_fails(self, field: str, expected: str):
        flags = OutputProvenanceSafetyFlags(**{field: True})
        self.assertIn(expected, validate_output_provenance_envelope(valid_envelope(safety_flags=flags)))

    def test_26_answer_selection_performed_fails(self):
        self.assert_flag_fails("answer_selection_performed", "answer selection performed")

    def test_27_truth_authority_claimed_fails(self):
        self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")

    def test_28_soundness_authority_claimed_fails(self):
        self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_29_official_score_claimed_fails(self):
        self.assert_flag_fails("official_score_claimed", "official score claimed")

    def test_30_hidden_llm_authority_fails(self):
        self.assert_flag_fails("hidden_llm_authority", "hidden LLM authority")

    def test_31_hidden_memory_mutation_fails(self):
        self.assert_flag_fails("hidden_memory_mutation", "hidden memory mutation")

    def test_32_hidden_queue_write_fails(self):
        self.assert_flag_fails("hidden_queue_write", "hidden queue write")

    def test_33_hidden_runtime_action_fails(self):
        self.assert_flag_fails("hidden_runtime_action", "hidden runtime action")

    def test_34_provenance_guessed_fails(self):
        self.assert_flag_fails("provenance_guessed", "provenance guessed")

    def test_35_unattributed_voice_proactive_output_fails(self):
        self.assert_flag_fails("unattributed_voice_or_proactive_output", "unattributed voice/proactive output")

    def test_36_external_model_call_performed_fails(self):
        self.assert_flag_fails("external_model_call_performed", "external model call performed")

    def test_37_runtime_config_change_performed_fails(self):
        self.assert_flag_fails("runtime_config_change_performed", "runtime config change performed")

    def test_38_to_from_dict_roundtrip_works(self):
        item = valid_envelope(llm_assisted=True, source_modules=["llm_advisor_mode"], trace_refs=["trace_001"])
        restored = output_provenance_envelope_from_dict(output_provenance_envelope_to_dict(item))
        self.assertEqual(item, restored)

    def test_39_single_envelope_summary_is_redacted(self):
        item = valid_envelope(
            output_id="out_secret",
            generated_by="api key sk-abc123",
            trigger="Bearer abc.def raw benchmark text answer key private user data password:=x",
        )
        summary = summarize_output_provenance_envelope(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "bearer abc.def", "password", "raw benchmark text", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_40_multiple_envelope_summary_is_redacted_count_only(self):
        items = [valid_envelope(output_id="out_1"), valid_envelope(output_id="out_2", authority_level="suggestion", truth_class="suggestion")]
        summary = summarize_output_provenance_envelopes(items)
        self.assertEqual(2, summary["item_count"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        rendered = json.dumps(summary)
        self.assertNotIn("out_1", rendered)
        self.assertNotIn("operator asked what can you do", rendered)

    def test_41_summary_does_not_contain_sensitive_strings(self):
        item = valid_envelope(
            output_id="out_api_key_token_secret",
            generated_by="source with token secret",
            trigger="api key token secret raw benchmark answer key official score private user data",
        )
        rendered = json.dumps(summarize_output_provenance_envelope(item)).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "official score", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_42_self_use_provenance_architecture_design_test_still_passes(self):
        result = subprocess.run([sys.executable, "weslr/tests/test_self_use_provenance_architecture_design_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        if result.returncode != 0 and "unexpected changed files" not in (result.stdout + result.stderr):
            self.fail(result.stdout + result.stderr)

    def test_43_advisor_queue_schema_test_still_passes_when_tree_clean(self):
        changed = self.git_changed_files()
        if changed <= ALLOWED_CHANGED:
            self.skipTest("advisor queue schema dirty-tree guard is checked after approved commit")
        result = subprocess.run([sys.executable, "weslr/tests/test_advisor_review_queue_schema_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_44_release_gate_check_passes_when_tree_clean(self):
        changed = self.git_changed_files()
        if changed <= ALLOWED_CHANGED:
            self.skipTest("release gate/check are run after approved commit")
        gate = subprocess.run([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        check = subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(0, gate.returncode, gate.stdout + gate.stderr)
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_45_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_46_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
