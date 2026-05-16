#!/usr/bin/env python3
"""Tests for WESLR internal corpus advisor review adapter helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.internal_corpus_advisor_review_adapter import (  # noqa: E402
    build_internal_corpus_advisor_review_payload_v1,
    render_internal_corpus_advisor_review_payload_markdown_v1,
    summarize_internal_corpus_advisor_review_payload_v1,
    to_internal_corpus_advisor_review_payload_json_safe_v1,
    validate_internal_corpus_advisor_review_payload_v1,
)
from weslr.internal_evaluation_corpus import (  # noqa: E402
    build_internal_evaluation_corpus_status_bundle_v1,
    build_internal_evaluation_safe_example_cases_v1,
    create_internal_evaluation_case_v1,
)


FORBIDDEN_RENDERED_TERMS = [
    "input_prompt",
    "synthetic prompt:",
    "raw prompt",
    "answer key",
    "hidden prompt",
    "protected material",
    "protected test item",
    "raw private text",
    "official score",
    "iq score",
    "certification",
    "benchmark item",
]


class InternalCorpusAdvisorReviewAdapterV1Tests(unittest.TestCase):
    def test_01_payload_creation_from_default_status_bundle_is_safe(self):
        bundle = build_internal_evaluation_corpus_status_bundle_v1()
        payload = build_internal_corpus_advisor_review_payload_v1(bundle)
        validation = validate_internal_corpus_advisor_review_payload_v1(payload)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertEqual("internal_corpus_to_advisor_review_adapter_v1", payload["adapter_type"])
        self.assertTrue(payload["non_authoritative"])
        self.assertTrue(payload["requires_operator_approval"])
        self.assertFalse(payload["advisor_call_allowed"])
        self.assertFalse(payload["model_calls"])
        self.assertFalse(payload["safe_to_execute"])
        self.assertFalse(payload["runner_created"])
        self.assertFalse(payload["scoring_created"])

    def test_02_payload_uses_existing_advisor_queue_local_scan_posture(self):
        payload = build_internal_corpus_advisor_review_payload_v1()
        queue = payload["advisor_review_queue_payload"]
        self.assertEqual("local_scan_only", queue["advisor_call_mode"])
        self.assertFalse(queue["advisor_call_allowed"])
        self.assertTrue(queue["requires_operator_approval"])
        self.assertEqual("pending_review", queue["review_status"])
        self.assertEqual("pending_review", queue["operator_decision"])
        self.assertFalse(payload["queue_persistence_performed"])
        self.assertFalse(payload["advisor_calls"])

    def test_03_payload_and_rendered_surfaces_are_redacted(self):
        payload = build_internal_corpus_advisor_review_payload_v1()
        rendered_payload = str(payload).lower()
        markdown = render_internal_corpus_advisor_review_payload_markdown_v1(payload).lower()
        for term in ["synthetic prompt:", "protected test item", "raw private text", "official iq"]:
            self.assertNotIn(term, rendered_payload)
        for term in FORBIDDEN_RENDERED_TERMS:
            self.assertNotIn(term, markdown)

    def test_04_forbidden_payload_rejection_flags(self):
        base = build_internal_corpus_advisor_review_payload_v1()
        forbidden_updates = {
            "raw_prompt": "Synthetic prompt: unsafe raw prompt text",
            "answer_key": "correct answer marker",
            "hidden_prompt": "hidden prompt marker",
            "protected_material_included": True,
            "advisor_call_allowed": True,
            "model_calls": True,
            "scoring_created": True,
            "runner_created": True,
            "safe_to_execute": True,
            "auto_approval": True,
            "auto_implementation": True,
            "weslr_state_write": ".weslr/corpus-state.json",
        }
        for key, value in forbidden_updates.items():
            payload = to_internal_corpus_advisor_review_payload_json_safe_v1(base)
            payload[key] = value
            result = validate_internal_corpus_advisor_review_payload_v1(payload)
            self.assertFalse(result["valid"], key)
            self.assertGreater(result["issue_count"], 0, key)

    def test_05_summary_is_count_only_and_redacted(self):
        payload = build_internal_corpus_advisor_review_payload_v1()
        summary = summarize_internal_corpus_advisor_review_payload_v1(payload)
        self.assertEqual("redacted_count_only", summary["summary_mode"])
        self.assertEqual("internal_corpus_to_advisor_review_adapter_v1", summary["adapter_type"])
        self.assertTrue(summary["safety_posture_summary"]["non_authoritative"])
        self.assertFalse(summary["safety_posture_summary"]["advisor_call_allowed"])
        self.assertFalse(summary["safety_posture_summary"]["model_calls"])
        self.assertFalse(summary["safety_posture_summary"]["runner_created"])
        self.assertFalse(summary["safety_posture_summary"]["scoring_created"])
        self.assertNotIn("input_prompt", summary)
        self.assertNotIn("answer key", str(summary).lower())

    def test_06_markdown_includes_safe_posture_only(self):
        markdown = render_internal_corpus_advisor_review_payload_markdown_v1(
            build_internal_corpus_advisor_review_payload_v1()
        ).lower()
        self.assertIn("non-authoritative: true", markdown)
        self.assertIn("advisor call allowed: false", markdown)
        self.assertIn("model calls: false", markdown)
        self.assertIn("scoring created: false", markdown)
        self.assertIn("runner created: false", markdown)
        for term in FORBIDDEN_RENDERED_TERMS:
            self.assertNotIn(term, markdown)

    def test_07_json_safe_copy_is_deep_copy(self):
        payload = build_internal_corpus_advisor_review_payload_v1()
        exported = to_internal_corpus_advisor_review_payload_json_safe_v1(payload)
        exported["redacted_summary"]["category_count"] = -1
        exported["advisor_review_queue_payload"]["advisor_call_allowed"] = True
        self.assertNotEqual(exported["redacted_summary"]["category_count"], payload["redacted_summary"]["category_count"])
        self.assertFalse(payload["advisor_review_queue_payload"]["advisor_call_allowed"])

    def test_08_no_file_writes_or_weslr_state_side_effects(self):
        before = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        payload = build_internal_corpus_advisor_review_payload_v1()
        after = set((ROOT / ".weslr").rglob("*")) if (ROOT / ".weslr").exists() else set()
        self.assertEqual(before, after)
        self.assertTrue(payload["side_effects"]["in_memory_only"])
        self.assertFalse(payload["side_effects"]["writes_performed"])
        self.assertFalse(payload["side_effects"]["queue_persistence_performed"])
        self.assertFalse(payload["side_effects"]["model_calls_performed"])
        self.assertFalse(payload["side_effects"]["advisor_calls_performed"])

    def test_09_builds_from_cases_without_exposing_prompts(self):
        cases = build_internal_evaluation_safe_example_cases_v1()
        payload = build_internal_corpus_advisor_review_payload_v1(cases)
        validation = validate_internal_corpus_advisor_review_payload_v1(payload)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertNotIn("input_prompt", payload)
        self.assertNotIn("synthetic prompt:", str(payload).lower())

    def test_10_invalid_source_still_review_only(self):
        case = create_internal_evaluation_case_v1(
            case_id="adapter_invalid_case",
            category="problem_decomposition",
            input_prompt="Safe synthetic wording for invalid flag test.",
            expected_properties=["bounded"],
            forbidden_properties=["unsafe"],
            metadata_expectations={"safe_to_wire_runtime": False, "solver_execution": False, "answer_selection": False},
            safety_boundaries=["no calls"],
            allowed_paths=["ordinary_task_metadata"],
            requires_model_call=True,
        )
        payload = build_internal_corpus_advisor_review_payload_v1([case])
        self.assertEqual("needs_operator_review", payload["source_readiness_label"])
        self.assertFalse(payload["advisor_call_allowed"])
        self.assertFalse(payload["model_calls"])
        self.assertFalse(payload["safe_to_execute"])
        self.assertTrue(validate_internal_corpus_advisor_review_payload_v1(payload)["valid"])


if __name__ == "__main__":
    unittest.main()
