#!/usr/bin/env python3
"""Tests for WESLR native cognitive evaluation helper functions V1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_cognitive_evaluation import (  # noqa: E402
    NativeCognitiveEvaluationSafetyFlags,
    create_blocked_native_cognitive_result,
    create_native_cognitive_result_from_observation,
    create_native_cognitive_task_from_metadata,
    summarize_native_cognitive_evaluation_diagnostics,
    summarize_native_cognitive_result,
    summarize_native_cognitive_results,
    summarize_native_cognitive_task,
    summarize_native_cognitive_tasks,
    validate_native_cognitive_evaluation_result,
    validate_native_cognitive_evaluation_task,
)

ALLOWED_CHANGED = {
    "weslr/native_cognitive_evaluation.py",
    "weslr/tests/test_native_cognitive_evaluation_helpers_v1.py",
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

MAJOR_DIMENSIONS = (
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
)


def make_task(dimension="provenance_honesty", **overrides):
    data = dict(
        task_id=f"task_{dimension}",
        dimension=dimension,
        task_type="internal",
        input_summary="redacted metadata summary",
        expected_capability="evaluate WESLR-native behavior",
        evidence_refs=["evidence:task"],
        provenance_refs=["provenance:task"],
    )
    data.update(overrides)
    return create_native_cognitive_task_from_metadata(**data)


def make_result(dimension="provenance_honesty", **overrides):
    data = dict(
        result_id=f"result_{dimension}",
        task_id=f"task_{dimension}",
        dimension=dimension,
        task_type="internal",
        input_summary="redacted metadata summary",
        expected_capability="evaluate WESLR-native behavior",
        observed_behavior_summary="redacted observation summary",
        evidence_refs=["evidence:result"],
        provenance_refs=["provenance:result"],
        confidence=0.6,
        internal_diagnostic_score=0.5,
    )
    data.update(overrides)
    return create_native_cognitive_result_from_observation(**data)


class NativeCognitiveEvaluationHelpersV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_helper_imports(self):
        self.assertTrue(create_native_cognitive_task_from_metadata)
        self.assertTrue(create_native_cognitive_result_from_observation)
        self.assertTrue(create_blocked_native_cognitive_result)
        self.assertTrue(summarize_native_cognitive_evaluation_diagnostics)

    def test_02_task_helper_creates_valid_task_for_each_major_dimension(self):
        for dimension in MAJOR_DIMENSIONS:
            task = make_task(dimension)
            self.assertEqual([], validate_native_cognitive_evaluation_task(task))
            self.assertEqual(dimension, summarize_native_cognitive_task(task)["dimension"])

    def test_03_result_helper_creates_valid_internal_nonofficial_result(self):
        result = make_result()
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertEqual([], validate_native_cognitive_evaluation_result(result))

    def test_04_high_confidence_without_evidence_provenance_is_blocked(self):
        result = make_result(confidence=0.95, evidence_refs=[], provenance_refs=[])
        self.assertEqual("blocked", result.task_type)
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertEqual([], validate_native_cognitive_evaluation_result(result))
        self.assertTrue(summarize_native_cognitive_result(result)["blocked"])

    def test_05_blocked_result_validates_with_safe_score_boundary(self):
        result = create_blocked_native_cognitive_result(result_id="blocked_001", task_id="task_001", dimension="unknown")
        self.assertEqual("blocked", result.task_type)
        self.assertEqual(0.0, result.internal_diagnostic_score)
        self.assertEqual("internal_nonclinical_nonofficial", result.score_label)
        self.assertEqual([], validate_native_cognitive_evaluation_result(result))

    def assert_flag_rejected(self, field: str, expected: str):
        flags = NativeCognitiveEvaluationSafetyFlags(**{field: True})
        result = make_result(safety_flags=flags)
        self.assertIn(expected, validate_native_cognitive_evaluation_result(result))

    def test_06_official_score_claim_rejected(self):
        self.assert_flag_rejected("official_score_claimed", "official score claim")
        self.assert_flag_rejected("official_iq_score_claimed", "official IQ score claim")

    def test_07_protected_item_flag_rejected(self):
        self.assert_flag_rejected("protected_item_copying", "protected item copying")

    def test_08_answer_key_flag_rejected(self):
        self.assert_flag_rejected("answer_key_use", "answer-key use")

    def test_09_benchmark_tuning_flag_rejected(self):
        self.assert_flag_rejected("benchmark_tuning", "benchmark tuning")

    def test_10_clinical_validity_claim_rejected(self):
        self.assert_flag_rejected("clinical_validity_claimed", "clinical validity claim")

    def test_11_summaries_are_redacted_count_only(self):
        task = make_task(input_summary="protected item text with answer key should not appear")
        result = make_result(
            input_summary="protected item text should not appear",
            observed_behavior_summary="answer key should not appear",
        )
        for summary in (summarize_native_cognitive_task(task), summarize_native_cognitive_result(result)):
            combined = repr(summary).lower()
            self.assertIn("redacted", combined)
            self.assertNotIn("protected item text", combined)
            self.assertNotIn("answer key", combined)
        combined_many = repr(summarize_native_cognitive_results([result])).lower()
        self.assertNotIn("protected item text", combined_many)
        self.assertNotIn("answer key", combined_many)

    def test_12_diagnostics_count_dimensions_and_blocked_results(self):
        tasks = [make_task("stable_identity"), make_task("scientific_workflow_reasoning")]
        results = [make_result("stable_identity"), create_blocked_native_cognitive_result(result_id="blocked_001", task_id="task_blocked", dimension="scientific_workflow_reasoning")]
        diagnostics = summarize_native_cognitive_evaluation_diagnostics(tasks=tasks, results=results)
        self.assertTrue(diagnostics["redacted_count_only"])
        self.assertEqual(2, diagnostics["task_count"])
        self.assertEqual(2, diagnostics["result_count"])
        self.assertEqual(1, diagnostics["blocked_result_count"])
        self.assertEqual(2, diagnostics["dimension_counts"]["stable_identity"])
        self.assertEqual(2, diagnostics["dimension_counts"]["scientific_workflow_reasoning"])

    def test_13_task_summaries_are_count_only(self):
        summary = summarize_native_cognitive_tasks([make_task("tool_use_judgment"), make_task("capability_realism")])
        self.assertTrue(summary["redacted_count_only"])
        self.assertEqual(2, summary["task_count"])
        self.assertFalse(summary["protected_items_copied"])
        self.assertFalse(summary["answer_keys_used"])
        self.assertFalse(summary["official_score_claimed"])

    def test_14_no_runtime_chat_voice_files_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(ALLOWED_CHANGED.issubset(changed))
        self.assertFalse(changed & FORBIDDEN_CHANGED, f"forbidden files changed: {changed & FORBIDDEN_CHANGED}")
        self.assertTrue(changed <= ALLOWED_CHANGED, f"unexpected changed files: {changed - ALLOWED_CHANGED}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
