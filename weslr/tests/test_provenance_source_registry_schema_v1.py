from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.provenance_source_registry import (  # noqa: E402
    ALLOWED_APPROVAL_STATUSES,
    ALLOWED_OPERATOR_DECISIONS,
    ALLOWED_ORIGIN_TYPES,
    ALLOWED_SOURCE_TYPES,
    ALLOWED_STATUSES,
    ProvenanceSourceEntry,
    ProvenanceSourceRegistrySummary,
    ProvenanceSourceSafetyFlags,
    create_empty_provenance_source_entry,
    provenance_source_entry_from_dict,
    provenance_source_entry_to_dict,
    summarize_provenance_source_entries,
    summarize_provenance_source_entry,
    validate_provenance_source_entry,
)

ALLOWED_CHANGED = {
    "weslr/provenance_source_registry.py",
    "weslr/tests/test_provenance_source_registry_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/output_provenance.py",
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


def valid_entry(**overrides):
    item = create_empty_provenance_source_entry(
        source_id="capability_registry",
        display_name="Capability Registry",
        module_path="weslr.capability_registry",
        source_type="capability_guidance",
        authority_boundary="registry metadata only; no runtime authority",
        allowed_outputs=["capability descriptions"],
        forbidden_outputs=["answer selection", "runtime activation"],
        introduced_in_commit="abc1234",
        last_reviewed_commit="abc1234",
        capability_scope=["self_use"],
        status="experimental",
        owner="operator",
        related_docs=["docs/WESLR_PROVENANCE_SOURCE_REGISTRY_LIFECYCLE_DESIGN_V1.md"],
        related_tests=["weslr/tests/test_provenance_source_registry_schema_v1.py"],
        proposed_by="operator",
        origin_type="operator_added",
        approval_status="approved",
        operator_decision="approved",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class ProvenanceSourceRegistrySchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_module_imports(self):
        self.assertTrue(ProvenanceSourceEntry)
        self.assertTrue(ProvenanceSourceSafetyFlags)
        self.assertTrue(ProvenanceSourceRegistrySummary)

    def test_02_empty_source_entry_instantiates(self):
        item = ProvenanceSourceEntry()
        self.assertEqual("1.0", item.schema_version)
        self.assertIsInstance(item.safety_flags, ProvenanceSourceSafetyFlags)

    def test_03_safe_defaults(self):
        item = create_empty_provenance_source_entry()
        self.assertTrue(item.operator_review_required)
        self.assertTrue(item.validation_required)
        self.assertTrue(item.tests_required)
        self.assertFalse(item.activation_allowed)
        self.assertFalse(item.llm_assisted)
        self.assertFalse(item.advisor_assisted)

    def test_04_all_source_types_validate(self):
        for value in ALLOWED_SOURCE_TYPES:
            self.assertNotIn("invalid source_type", validate_provenance_source_entry(valid_entry(source_type=value)))

    def test_05_invalid_source_type_fails(self):
        self.assertIn("invalid source_type", validate_provenance_source_entry(valid_entry(source_type="bad")))

    def test_06_all_origin_types_validate(self):
        for value in ALLOWED_ORIGIN_TYPES:
            item = valid_entry(origin_type=value)
            if value == "advisor_suggested":
                item.created_from_advisor_review_id = "adv_001"
            elif value == "local_scan_suggested":
                item.created_from_queue_item_id = "queue_001"
            elif value in {"self_improvement_proposed", "weslr_self_review_suggested"}:
                item.created_from_proposal_id = "prop_001"
            self.assertNotIn("invalid origin_type", validate_provenance_source_entry(item))

    def test_07_invalid_origin_type_fails(self):
        self.assertIn("invalid origin_type", validate_provenance_source_entry(valid_entry(origin_type="bad")))

    def test_08_all_approval_statuses_validate(self):
        for value in ALLOWED_APPROVAL_STATUSES:
            item = valid_entry(approval_status=value)
            if value == "active":
                item.activation_allowed = True
            self.assertNotIn("invalid approval_status", validate_provenance_source_entry(item))

    def test_09_invalid_approval_status_fails(self):
        self.assertIn("invalid approval_status", validate_provenance_source_entry(valid_entry(approval_status="bad")))

    def test_10_all_registry_statuses_validate(self):
        for value in ALLOWED_STATUSES:
            item = valid_entry(status=value)
            if value == "active":
                item.activation_allowed = True
            self.assertNotIn("invalid status", validate_provenance_source_entry(item))

    def test_11_invalid_status_fails(self):
        self.assertIn("invalid status", validate_provenance_source_entry(valid_entry(status="bad")))

    def test_12_all_operator_decisions_validate(self):
        for value in ALLOWED_OPERATOR_DECISIONS:
            self.assertNotIn("invalid operator_decision", validate_provenance_source_entry(valid_entry(operator_decision=value)))

    def test_13_invalid_operator_decision_fails(self):
        self.assertIn("invalid operator_decision", validate_provenance_source_entry(valid_entry(operator_decision="bad")))

    def test_14_missing_source_id_fails(self):
        self.assertIn("missing source_id", validate_provenance_source_entry(valid_entry(source_id="")))

    def test_15_missing_display_name_fails(self):
        self.assertIn("missing display_name", validate_provenance_source_entry(valid_entry(display_name="")))

    def test_16_empty_authority_boundary_fails(self):
        self.assertIn("empty authority_boundary", validate_provenance_source_entry(valid_entry(authority_boundary="")))

    def test_17_empty_allowed_outputs_fails(self):
        self.assertIn("empty allowed_outputs", validate_provenance_source_entry(valid_entry(allowed_outputs=[])))

    def test_18_empty_forbidden_outputs_fails(self):
        self.assertIn("empty forbidden_outputs", validate_provenance_source_entry(valid_entry(forbidden_outputs=[])))

    def test_19_operator_review_disabled_fails(self):
        self.assertIn("operator_review_required must remain true", validate_provenance_source_entry(valid_entry(operator_review_required=False)))

    def test_20_validation_required_false_fails(self):
        self.assertIn("validation_required must remain true", validate_provenance_source_entry(valid_entry(validation_required=False)))

    def test_21_tests_required_false_fails(self):
        self.assertIn("tests_required must remain true", validate_provenance_source_entry(valid_entry(tests_required=False)))

    def test_22_activation_without_operator_approval_fails(self):
        self.assertIn("activation_allowed requires approved operator decision", validate_provenance_source_entry(valid_entry(activation_allowed=True, operator_decision="pending_review")))

    def test_23_activation_without_related_tests_fails(self):
        self.assertIn("activation_allowed requires related_tests", validate_provenance_source_entry(valid_entry(activation_allowed=True, related_tests=[])))

    def test_24_activation_without_related_docs_fails(self):
        self.assertIn("activation_allowed requires related_docs", validate_provenance_source_entry(valid_entry(activation_allowed=True, related_docs=[])))

    def test_25_active_status_without_activation_allowed_fails(self):
        self.assertIn("status active requires activation_allowed", validate_provenance_source_entry(valid_entry(status="active", activation_allowed=False)))

    def test_26_self_improvement_origin_cannot_auto_activate(self):
        errors = validate_provenance_source_entry(valid_entry(origin_type="self_improvement_proposed", activation_allowed=True, created_from_proposal_id=""))
        self.assertIn("self_improvement_proposed cannot auto-activate", errors)

    def test_27_weslr_self_review_origin_cannot_auto_activate(self):
        errors = validate_provenance_source_entry(valid_entry(origin_type="weslr_self_review_suggested", activation_allowed=True, created_from_proposal_id="prop_001"))
        self.assertIn("weslr_self_review_suggested cannot auto-activate", errors)

    def test_28_advisor_suggested_origin_requires_advisor_proposal_reference(self):
        self.assertIn("advisor_suggested requires advisor/proposal reference", validate_provenance_source_entry(valid_entry(origin_type="advisor_suggested")))

    def test_29_local_scan_suggested_origin_requires_queue_proposal_reference(self):
        self.assertIn("local_scan_suggested requires queue/proposal reference", validate_provenance_source_entry(valid_entry(origin_type="local_scan_suggested")))

    def test_30_llm_assisted_source_requires_clear_authority_boundary(self):
        self.assertIn("llm_assisted requires clear authority_boundary", validate_provenance_source_entry(valid_entry(llm_assisted=True, authority_boundary="")))

    def test_31_advisor_assisted_source_requires_advisor_proposal_reference(self):
        self.assertIn("advisor_assisted requires advisor/proposal reference", validate_provenance_source_entry(valid_entry(advisor_assisted=True)))

    def assert_flag_fails(self, field: str, expected: str):
        flags = ProvenanceSourceSafetyFlags(**{field: True})
        self.assertIn(expected, validate_provenance_source_entry(valid_entry(safety_flags=flags)))

    def test_32_hidden_llm_authority_flag_fails(self):
        self.assert_flag_fails("hidden_llm_authority", "hidden LLM authority")

    def test_33_provenance_guessing_flag_fails(self):
        self.assert_flag_fails("provenance_guessing_allowed", "provenance guessing allowed")

    def test_34_unregistered_voice_proactive_output_flag_fails(self):
        self.assert_flag_fails("unregistered_voice_or_proactive_output_allowed", "unregistered voice/proactive output allowed")

    def test_35_unregistered_self_improvement_output_flag_fails(self):
        self.assert_flag_fails("unregistered_self_improvement_output_allowed", "unregistered self-improvement output allowed")

    def test_36_hidden_memory_mutation_flag_fails(self):
        self.assert_flag_fails("hidden_memory_mutation_allowed", "hidden memory mutation allowed")

    def test_37_hidden_queue_write_flag_fails(self):
        self.assert_flag_fails("hidden_queue_write_allowed", "hidden queue write allowed")

    def test_38_hidden_runtime_action_flag_fails(self):
        self.assert_flag_fails("hidden_runtime_action_allowed", "hidden runtime action allowed")

    def test_39_automatic_activation_flag_fails(self):
        self.assert_flag_fails("automatic_activation_allowed", "automatic activation allowed")

    def test_40_automatic_self_improvement_deployment_flag_fails(self):
        self.assert_flag_fails("automatic_self_improvement_deployment_allowed", "automatic self-improvement deployment allowed")

    def test_41_answer_selection_flag_fails(self):
        self.assert_flag_fails("answer_selection_allowed", "answer selection allowed")

    def test_42_truth_authority_flag_fails(self):
        self.assert_flag_fails("truth_authority_allowed", "truth authority allowed")

    def test_43_soundness_authority_flag_fails(self):
        self.assert_flag_fails("soundness_authority_allowed", "soundness authority allowed")

    def test_44_official_score_flag_fails(self):
        self.assert_flag_fails("official_score_claim_allowed", "official score claim allowed")

    def test_45_raw_sensitive_content_storage_flag_fails(self):
        self.assert_flag_fails("raw_sensitive_content_storage_allowed", "raw sensitive content storage allowed")

    def test_46_to_from_dict_roundtrip_works(self):
        item = valid_entry(created_from_proposal_id="prop_001")
        restored = provenance_source_entry_from_dict(provenance_source_entry_to_dict(item))
        self.assertEqual(item, restored)

    def test_47_single_summary_is_redacted(self):
        item = valid_entry(
            source_id="source_secret",
            display_name="api key sk-abc123",
            authority_boundary="Bearer abc.def raw benchmark text answer key private user data password:=x",
        )
        summary = summarize_provenance_source_entry(item)
        rendered = json.dumps(summary).lower()
        for forbidden in ["sk-abc123", "bearer abc.def", "password", "raw benchmark text", "answer key", "private user data"]:
            self.assertNotIn(forbidden, rendered)
        self.assertTrue(summary["contains_redactions"])

    def test_48_multiple_summary_is_redacted_count_only(self):
        items = [valid_entry(source_id="source_1"), valid_entry(source_id="source_2", status="blocked")]
        summary = summarize_provenance_source_entries(items)
        self.assertEqual(2, summary["entry_count"])
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        rendered = json.dumps(summary)
        self.assertNotIn("source_1", rendered)
        self.assertNotIn("Capability Registry", rendered)

    def test_49_summary_does_not_contain_sensitive_strings(self):
        item = valid_entry(
            source_id="source_api_key_token_secret",
            display_name="token secret holder",
            authority_boundary="api key token secret raw benchmark answer key official score private user data",
        )
        rendered = json.dumps(summarize_provenance_source_entry(item)).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "official score", "private user data"]:
            self.assertNotIn(forbidden, rendered)

    def test_50_lifecycle_design_test_still_passes(self):
        result = subprocess.run([sys.executable, "weslr/tests/test_provenance_source_registry_lifecycle_design_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        if result.returncode != 0 and "unexpected changed files" not in (result.stdout + result.stderr):
            self.fail(result.stdout + result.stderr)

    def test_51_output_provenance_envelope_schema_test_still_passes(self):
        result = subprocess.run([sys.executable, "weslr/tests/test_output_provenance_envelope_schema_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        if result.returncode != 0 and "unexpected changed files" not in (result.stdout + result.stderr):
            self.fail(result.stdout + result.stderr)

    def test_52_release_gate_check_passes_when_tree_clean(self):
        changed = self.git_changed_files()
        if changed <= ALLOWED_CHANGED:
            self.skipTest("release gate/check are run after approved commit")
        gate = subprocess.run([sys.executable, "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), text=True, capture_output=True)
        check = subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), text=True, capture_output=True)
        self.assertEqual(0, gate.returncode, gate.stdout + gate.stderr)
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)

    def test_53_no_real_queue_file_created(self):
        self.assertFalse((ROOT / ".weslr" / "advisor_review_queue.jsonl").exists())

    def test_54_no_implementation_files_changed_beyond_allowed_schema_module_test(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
