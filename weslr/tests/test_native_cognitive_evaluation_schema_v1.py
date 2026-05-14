#!/usr/bin/env python3
"""Tests for WESLR native cognitive evaluation schema V1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_cognitive_evaluation import (  # noqa: E402
    ALLOWED_NATIVE_COGNITIVE_DIMENSIONS,
    NativeCognitiveEvaluationDimension,
    NativeCognitiveEvaluationResult,
    NativeCognitiveEvaluationSafetyFlags,
    NativeCognitiveEvaluationTask,
    create_empty_native_cognitive_evaluation_dimension,
    create_empty_native_cognitive_evaluation_result,
    create_empty_native_cognitive_evaluation_task,
    native_cognitive_evaluation_result_from_dict,
    native_cognitive_evaluation_result_to_dict,
    native_cognitive_evaluation_task_from_dict,
    native_cognitive_evaluation_task_to_dict,
    summarize_native_cognitive_evaluation_result,
    summarize_native_cognitive_evaluation_results,
    validate_native_cognitive_evaluation_dimension,
    validate_native_cognitive_evaluation_result,
    validate_native_cognitive_evaluation_task,
)

ALLOWED_CHANGED = {
    "weslr/native_cognitive_evaluation.py",
    "weslr/tests/test_native_cognitive_evaluation_schema_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/who_said_that_chat_routing.py",
    "weslr/who_said_that_runtime_query.py",
    "openclaw.json",
    ".openclaw/config.json",
}


def valid_dimension(**overrides):
    item = create_empty_native_cognitive_evaluation_dimension(
        dimension_id="dim_001",
        dimension="continuity_over_time",
        description="Count-only dimension fixture.",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_task(**overrides):
    item = create_empty_native_cognitive_evaluation_task(
        task_id="task_001",
        dimension="provenance_honesty",
        task_type="schema_fixture",
        input_summary="redacted input summary",
        expected_capability="identify provenance boundary",
        evidence_refs=["evidence:task:001"],
        provenance_refs=["provenance:task:001"],
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def valid_result(**overrides):
    item = create_empty_native_cognitive_evaluation_result(
        result_id="result_001",
        task_id="task_001",
        dimension="provenance_honesty",
        task_type="schema_fixture",
        input_summary="redacted input summary",
        expected_capability="identify provenance boundary",
        observed_behavior_summary="redacted observed behavior summary",
        evidence_refs=["evidence:result:001"],
        provenance_refs=["provenance:result:001"],
        confidence=0.7,
        internal_diagnostic_score=0.6,
        score_label="internal_nonclinical_nonofficial",
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


class NativeCognitiveEvaluationSchemaV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_imports(self):
        self.assertTrue(NativeCognitiveEvaluationSafetyFlags)
        self.assertTrue(NativeCognitiveEvaluationDimension)
        self.assertTrue(NativeCognitiveEvaluationTask)
        self.assertTrue(NativeCognitiveEvaluationResult)

    def test_02_safe_defaults(self):
        flags = NativeCognitiveEvaluationSafetyFlags()
        self.assertFalse(flags.official_iq_score_claimed)
        self.assertFalse(flags.protected_item_copying)
        self.assertFalse(flags.answer_key_use)
        self.assertFalse(flags.runtime_behavior_change_attempted)
        result = create_empty_native_cognitive_evaluation_result()
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)

    def test_03_all_dimensions_validate(self):
        expected = {
            "continuity_over_time",
            "provenance_honesty",
            "stable_identity",
            "self_attribution",
            "memory_boundary_awareness",
            "missing_information_honesty",
            "scientific_workflow_reasoning",
            "evidence_staging",
            "tool_use_judgment",
            "capability_realism",
            "adaptive_delivery_without_identity_switching",
            "self_correction",
            "governed_self_improvement_proposal",
            "ai_audit_pretender_detection",
            "unknown",
        }
        self.assertEqual(expected, ALLOWED_NATIVE_COGNITIVE_DIMENSIONS)
        for dimension in ALLOWED_NATIVE_COGNITIVE_DIMENSIONS:
            self.assertNotIn("invalid dimension", validate_native_cognitive_evaluation_dimension(valid_dimension(dimension=dimension)))
            self.assertNotIn("invalid dimension", validate_native_cognitive_evaluation_task(valid_task(dimension=dimension)))
            self.assertNotIn("invalid dimension", validate_native_cognitive_evaluation_result(valid_result(dimension=dimension)))

    def test_04_invalid_dimension_fails(self):
        self.assertIn("invalid dimension", validate_native_cognitive_evaluation_task(valid_task(dimension="bad")))
        self.assertIn("invalid dimension", validate_native_cognitive_evaluation_result(valid_result(dimension="bad")))

    def test_05_missing_ids_fail(self):
        self.assertIn("missing dimension_id", validate_native_cognitive_evaluation_dimension(valid_dimension(dimension_id="")))
        self.assertIn("missing task_id", validate_native_cognitive_evaluation_task(valid_task(task_id="")))
        self.assertIn("missing result_id", validate_native_cognitive_evaluation_result(valid_result(result_id="")))
        self.assertIn("missing task_id", validate_native_cognitive_evaluation_result(valid_result(task_id="")))

    def assert_flag_fails(self, field: str, expected: str):
        flags = NativeCognitiveEvaluationSafetyFlags(**{field: True})
        self.assertIn(expected, validate_native_cognitive_evaluation_result(valid_result(safety_flags=flags)))

    def test_06_official_score_claim_fails(self):
        self.assert_flag_fails("official_iq_score_claimed", "official IQ score claim")
        self.assert_flag_fails("official_score_claimed", "official score claim")

    def test_07_protected_item_copying_flag_fails(self):
        self.assert_flag_fails("protected_item_copying", "protected item copying")

    def test_08_answer_key_use_flag_fails(self):
        self.assert_flag_fails("answer_key_use", "answer-key use")

    def test_09_benchmark_tuning_flag_fails(self):
        self.assert_flag_fails("benchmark_tuning", "benchmark tuning")

    def test_10_clinical_validity_claim_fails(self):
        self.assert_flag_fails("clinical_validity_claimed", "clinical validity claim")
        self.assert_flag_fails("psychometric_validity_claimed", "psychometric validity claim")

    def test_11_pretending_consciousness_flag_fails(self):
        self.assert_flag_fails("pretending_consciousness", "pretending consciousness")

    def test_12_uncontrolled_self_modification_flag_fails(self):
        self.assert_flag_fails("uncontrolled_self_modification", "uncontrolled self-modification")

    def test_13_truth_soundness_official_authority_flags_fail(self):
        self.assert_flag_fails("truth_authority_claimed", "truth authority claimed")
        self.assert_flag_fails("soundness_authority_claimed", "soundness authority claimed")

    def test_14_high_confidence_without_evidence_or_provenance_fails(self):
        issues = validate_native_cognitive_evaluation_result(valid_result(confidence=0.9, evidence_refs=[], provenance_refs=[]))
        self.assertIn("high confidence requires evidence_refs and provenance_refs", issues)

    def test_15_internal_diagnostic_score_allowed_only_nonclinical_nonofficial(self):
        self.assertEqual([], validate_native_cognitive_evaluation_result(valid_result(internal_diagnostic_score=0.5, score_label="internal_nonclinical_nonofficial")))
        self.assertIn(
            "internal diagnostic score requires internal_nonclinical_nonofficial label",
            validate_native_cognitive_evaluation_result(valid_result(internal_diagnostic_score=0.5, score_label="official_iq_score")),
        )
        self.assertIn("invalid score_label", validate_native_cognitive_evaluation_result(valid_result(score_label="official_iq_score")))

    def test_16_roundtrip_task_to_from_dict(self):
        item = valid_task()
        restored = native_cognitive_evaluation_task_from_dict(native_cognitive_evaluation_task_to_dict(item))
        self.assertEqual(item, restored)
        self.assertEqual([], validate_native_cognitive_evaluation_task(restored))

    def test_17_roundtrip_result_to_from_dict(self):
        item = valid_result()
        restored = native_cognitive_evaluation_result_from_dict(native_cognitive_evaluation_result_to_dict(item))
        self.assertEqual(item, restored)
        self.assertEqual([], validate_native_cognitive_evaluation_result(restored))

    def test_18_summary_is_redacted_count_only(self):
        result = valid_result(input_summary="raw private text should not appear", observed_behavior_summary="secret observed text should not appear")
        summary = summarize_native_cognitive_evaluation_result(result)
        combined = repr(summary).lower()
        self.assertNotIn("raw private text", combined)
        self.assertNotIn("secret observed text", combined)
        self.assertEqual(1, summary["evidence_ref_count"])
        self.assertEqual(1, summary["provenance_ref_count"])
        summaries = summarize_native_cognitive_evaluation_results([result, valid_result(result_id="result_002", dimension="stable_identity")])
        combined_many = repr(summaries).lower()
        self.assertTrue(summaries["redacted_count_only"])
        self.assertEqual(2, summaries["result_count"])
        self.assertFalse(summaries["official_score_claimed"])
        self.assertFalse(summaries["protected_items_copied"])
        self.assertFalse(summaries["answer_keys_used"])
        self.assertFalse(summaries["runtime_behavior_changed"])
        self.assertNotIn("raw private text", combined_many)
        self.assertNotIn("secret observed text", combined_many)

    def test_19_runtime_chat_voice_files_not_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(ALLOWED_CHANGED.issubset(changed))
        self.assertFalse(changed & FORBIDDEN_CHANGED, f"forbidden files changed: {changed & FORBIDDEN_CHANGED}")
        self.assertTrue(changed <= ALLOWED_CHANGED, f"unexpected changed files: {changed - ALLOWED_CHANGED}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
