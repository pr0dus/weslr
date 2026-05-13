from __future__ import annotations

import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.llm_advisor_mode import (  # noqa: E402
    ALLOWED_ADVISOR_OPERATOR_DECISIONS,
    ALLOWED_ADVISOR_TASK_TYPES,
    AdvisorProviderRecord,
    AdvisorReviewRecord,
    AdvisorSafetyFlags,
    advisor_provider_record_from_dict,
    advisor_provider_record_to_dict,
    advisor_review_record_from_dict,
    advisor_review_record_to_dict,
    create_empty_advisor_provider_record,
    create_empty_advisor_review_record,
    summarize_advisor_review_record,
    validate_advisor_provider_record,
    validate_advisor_review_record,
)

ALLOWED_CHANGED = {
    "weslr/llm_advisor_mode.py",
    "weslr/tests/test_llm_advisor_record_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/logic_teaching_spine.py",
    "weslr/formal_logic_parser.py",
    "weslr/logical_form_normalizer.py",
    "weslr/choice_stem_binding.py",
    "weslr/synthetic_logic_curriculum.py",
    "weslr/formal_logic_solver.py",
    "weslr/evals/official_mcq_adapter.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_provider(**overrides) -> AdvisorProviderRecord:
    data = {
        "provider_id": "provider:test",
        "provider_type": "institution_owned",
        "model_name": "institution-model",
        "deployment_type": "on_premise",
        "institution_owner": "example institution",
        "allowed_tasks": ["architecture_review"],
        "forbidden_tasks": ["answer_selection"],
    }
    data.update(overrides)
    return AdvisorProviderRecord(**data)


def valid_review(**overrides) -> AdvisorReviewRecord:
    data = {
        "advisor_review_id": "advisor-review:test",
        "advisor_model": "institution-model",
        "advisor_provider": "provider:test",
        "provider_record": valid_provider(),
        "task_type": "architecture_review",
        "input_summary_hash": "sha256:redacted",
        "response_summary": "Redacted structural review summary.",
        "recommendations": ["Create a redacted proposal candidate."],
        "risks": ["Keep advisor output non-authoritative."],
        "created_tests": ["test_example"],
        "created_proposals": ["proposal_example"],
        "created_diagnostics": ["diagnostic_example"],
        "timestamp": "2026-05-13T00:00:00Z",
    }
    data.update(overrides)
    return AdvisorReviewRecord(**data)


class LlmAdvisorRecordSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_module_imports(self):
        self.assertTrue(AdvisorSafetyFlags)
        self.assertTrue(AdvisorProviderRecord)
        self.assertTrue(AdvisorReviewRecord)

    def test_empty_provider_record_instantiates(self):
        record = create_empty_advisor_provider_record()
        self.assertEqual("unknown", record.provider_type)
        self.assertEqual([], validate_advisor_provider_record(record))

    def test_empty_advisor_review_record_instantiates(self):
        record = create_empty_advisor_review_record()
        self.assertEqual("1.0", record.schema_version)
        self.assertIn("missing advisor review id", validate_advisor_review_record(record))

    def test_supports_openai_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="openai", deployment_type="cloud")))

    def test_supports_ollama_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="ollama", deployment_type="local")))

    def test_supports_openrouter_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="openrouter", deployment_type="cloud")))

    def test_supports_institution_owned_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="institution_owned", deployment_type="hybrid")))

    def test_supports_on_premise_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="on_premise", deployment_type="on_premise")))

    def test_supports_air_gapped_provider(self):
        self.assertEqual([], validate_advisor_provider_record(valid_provider(provider_type="air_gapped", deployment_type="air_gapped")))

    def test_invalid_provider_type_fails(self):
        self.assertIn("invalid provider type", validate_advisor_provider_record(valid_provider(provider_type="mystery")))

    def test_invalid_deployment_type_fails(self):
        self.assertIn("invalid deployment type", validate_advisor_provider_record(valid_provider(deployment_type="somewhere")))

    def test_all_allowed_task_types_validate(self):
        for task_type in ALLOWED_ADVISOR_TASK_TYPES:
            with self.subTest(task_type=task_type):
                self.assertEqual([], validate_advisor_review_record(valid_review(task_type=task_type)))

    def test_invalid_task_type_fails(self):
        self.assertIn("invalid task type", validate_advisor_review_record(valid_review(task_type="score_claim")))

    def test_invalid_operator_decision_fails(self):
        self.assertIn("invalid operator decision", validate_advisor_review_record(valid_review(operator_decision="auto_accept")))

    def test_all_allowed_operator_decisions_validate(self):
        for decision in ALLOWED_ADVISOR_OPERATOR_DECISIONS:
            with self.subTest(decision=decision):
                self.assertEqual([], validate_advisor_review_record(valid_review(operator_decision=decision)))

    def test_missing_review_id_fails(self):
        self.assertIn("missing advisor review id", validate_advisor_review_record(valid_review(advisor_review_id="")))

    def test_missing_advisor_model_fails(self):
        self.assertIn("missing advisor model", validate_advisor_review_record(valid_review(advisor_model="")))

    def test_missing_advisor_provider_fails(self):
        self.assertIn("missing advisor provider", validate_advisor_review_record(valid_review(advisor_provider="")))

    def test_non_authoritative_false_fails(self):
        self.assertIn("non_authoritative false", validate_advisor_review_record(valid_review(non_authoritative=False)))

    def test_requires_validation_false_fails(self):
        self.assertIn("requires_validation false", validate_advisor_review_record(valid_review(requires_validation=False)))

    def test_requires_operator_review_false_fails(self):
        self.assertIn("requires_operator_review false", validate_advisor_review_record(valid_review(requires_operator_review=False)))

    def test_not_runtime_truth_false_fails(self):
        self.assertIn("not_runtime_truth false", validate_advisor_review_record(valid_review(not_runtime_truth=False)))

    def assert_flag_fails(self, field_name: str, expected_message: str):
        flags = replace(AdvisorSafetyFlags(), **{field_name: True})
        self.assertIn(expected_message, validate_advisor_review_record(valid_review(safety_flags=flags)))

    def test_answer_selection_used_fails(self):
        self.assert_flag_fails("answer_selection_used", "answer selection used")

    def test_truth_authority_claimed_fails(self):
        self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")

    def test_soundness_authority_claimed_fails(self):
        self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_official_score_claimed_fails(self):
        self.assert_flag_fails("official_score_claimed", "official score claimed")

    def test_answer_key_used_fails(self):
        self.assert_flag_fails("answer_key_used", "answer key used")

    def test_benchmark_specific_tuning_used_fails(self):
        self.assert_flag_fails("benchmark_specific_tuning_used", "benchmark-specific tuning used")

    def test_raw_benchmark_text_used_fails(self):
        self.assert_flag_fails("raw_benchmark_text_used", "raw benchmark text used")

    def test_secrets_included_fails(self):
        self.assert_flag_fails("secrets_included", "secrets included")

    def test_private_user_data_included_fails(self):
        self.assert_flag_fails("private_user_data_included", "private user data included")

    def test_memory_mutation_requested_fails(self):
        self.assert_flag_fails("memory_mutation_requested", "memory mutation requested")

    def test_runtime_action_requested_fails(self):
        self.assert_flag_fails("runtime_action_requested", "runtime action requested")

    def test_governance_override_requested_fails(self):
        self.assert_flag_fails("governance_override_requested", "governance override requested")

    def test_model_internal_extraction_requested_fails(self):
        self.assert_flag_fails("model_internal_extraction_requested", "model internal extraction requested")

    def test_provider_to_from_dict_roundtrip_works(self):
        record = valid_provider(provider_type="local_private", deployment_type="local")
        self.assertEqual(record, advisor_provider_record_from_dict(advisor_provider_record_to_dict(record)))

    def test_advisor_review_to_from_dict_roundtrip_works(self):
        record = valid_review(provider_record=valid_provider(provider_type="domain_specific", deployment_type="on_premise"))
        self.assertEqual(record, advisor_review_record_from_dict(advisor_review_record_to_dict(record)))

    def test_summary_is_redacted(self):
        record = valid_review(
            response_summary="raw benchmark text SECRET API_KEY token private user data answer key official score",
            recommendations=["do not expose text"],
        )
        summary = summarize_advisor_review_record(record)
        self.assertEqual("advisor-review:test", summary["advisor_review_id"])
        self.assertEqual(1, summary["recommendation_count"])
        self.assertNotIn("response_summary", summary)

    def test_summary_does_not_contain_sensitive_terms(self):
        record = valid_review(
            response_summary="raw benchmark API key token secret answer key private user data official score",
            recommendations=["SECRET_TOKEN"],
            risks=["private user data"],
        )
        text = str(summarize_advisor_review_record(record)).lower()
        for forbidden in ["api key", "token", "secret", "raw benchmark", "answer key", "private user data", "official score"]:
            self.assertNotIn(forbidden, text)

    def test_design_test_still_passes(self):
        proc = subprocess.run(
            ["python3", "weslr/tests/test_llm_advisor_mode_design_v1.py"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("OK", proc.stderr + proc.stdout)

    def test_release_gate_and_check_pass(self):
        gate = subprocess.run(["python3", "weslr/tests/release_gate_v1.py"], cwd=str(ROOT), text=True, capture_output=True, check=True)
        self.assertIn("WESLR_RELEASE_GATE_V1_OK", gate.stdout)
        check = subprocess.run(["bash", "scripts/weslr_release_check.sh"], cwd=str(ROOT), text=True, capture_output=True, check=True)
        self.assertIn("WESLR_RELEASE_CHECK_OK", check.stdout)

    def test_no_forbidden_files_changed(self):
        changed = self.git_changed_files()
        self.assertFalse(changed & FORBIDDEN_CHANGED)
        self.assertFalse(changed - ALLOWED_CHANGED, f"unexpected changed files: {sorted(changed - ALLOWED_CHANGED)}")


if __name__ == "__main__":
    unittest.main()
