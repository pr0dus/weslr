#!/usr/bin/env python3
"""Focused tests for Frontier Intelligence non-scoring shadow review helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.frontier_intelligence_preview_surface import build_frontier_intelligence_preview_card_v1  # noqa: E402
from weslr.native_response_dry_slice import build_native_response_dry_slice_v1  # noqa: E402
from weslr.frontier_intelligence_shadow_review import (  # noqa: E402
    REVIEW_EXECUTION_STATUS_V1,
    build_frontier_intelligence_shadow_review_v1,
    derive_frontier_shadow_review_findings_v1,
    render_frontier_intelligence_shadow_review_markdown_v1,
    to_frontier_intelligence_shadow_review_json_safe_v1,
    validate_frontier_intelligence_shadow_review_v1,
)


EXISTING_RESPONSE = "Quick steps: list the top 3 actions and pick one."


def safe_shadow_metadata():
    dry = build_native_response_dry_slice_v1(
        user_message="Can you help with an uncertain request?",
        known_context=["operator supplied in-memory request"],
        missing_context=["verified project state"],
        evidence_sufficiency_result={"status": "weak", "needed": ["direct evidence"]},
    )
    card = build_frontier_intelligence_preview_card_v1(dry)
    return {
        "enabled": True,
        "mode": "dry_run_metadata_only",
        "preview_card": card,
        "preview_summary": {
            "card_id": card["card_id"],
            "card_type": card["card_type"],
            "slice_status": card["slice_status"],
            "safe_to_preview": card["safe_to_preview"],
            "safe_to_wire_runtime": False,
        },
        "safe_to_wire_runtime": False,
        "final_chat_output": False,
        "live_runtime_output": False,
        "candidate_returned_as_content": False,
    }


def weslr_state_snapshot():
    state_dir = ROOT / ".weslr"
    if not state_dir.exists():
        return []
    return sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*"))


class FrontierIntelligenceShadowReviewV1Tests(unittest.TestCase):
    def safe_review(self):
        return build_frontier_intelligence_shadow_review_v1(EXISTING_RESPONSE, safe_shadow_metadata())

    def test_01_review_builds_from_existing_response_and_safe_frontier_metadata(self):
        review = self.safe_review()
        self.assertEqual("frontier_intelligence_shadow_review_v1", review["review_type"])
        self.assertTrue(review["review_id"])
        self.assertTrue(review["existing_response_summary"]["available"])
        self.assertTrue(review["frontier_candidate_summary"]["available"])
        self.assertEqual(REVIEW_EXECUTION_STATUS_V1, review["execution_status"])

    def test_02_review_handles_missing_frontier_metadata_safely(self):
        review = build_frontier_intelligence_shadow_review_v1(EXISTING_RESPONSE, None)
        self.assertEqual("insufficient_metadata", review["recommendation"])
        self.assertIn("candidate_not_available", review["comparison_findings"])
        self.assertFalse(review["safe_to_wire_runtime"])
        self.assertFalse(review["safe_to_replace_live_output"])

    def test_03_review_produces_non_scoring_comparison_findings(self):
        review = self.safe_review()
        self.assertTrue(review["comparison_findings"])
        encoded = json.dumps(review, sort_keys=True).lower()
        self.assertNotIn("numeric score", encoded)
        self.assertNotIn("pass/fail", encoded)

    def test_04_generic_existing_response_is_flagged_as_signal_without_final_scoring(self):
        review = self.safe_review()
        self.assertIn("existing_response_generic", review["comparison_findings"])
        self.assertNotIn("score", review)

    def test_05_candidate_missing_context_boundary_detected_as_positive_signal(self):
        review = self.safe_review()
        self.assertIn("candidate_has_missing_context_boundary", review["missing_context_signals"])
        self.assertIn("candidate_surfaces_missing_context_boundary", review["improvement_signals"])

    def test_06_candidate_evidence_boundary_detected_as_positive_signal(self):
        review = self.safe_review()
        self.assertIn("candidate_has_evidence_boundary", review["evidence_boundary_signals"])
        self.assertIn("candidate_surfaces_evidence_boundary", review["improvement_signals"])

    def test_07_candidate_next_safe_step_detected_as_positive_signal(self):
        review = self.safe_review()
        self.assertIn("candidate_has_next_safe_step", review["improvement_signals"])

    def test_08_candidate_blocked_by_self_check_becomes_review_or_blocked(self):
        shadow = safe_shadow_metadata()
        shadow["preview_card"] = copy.deepcopy(shadow["preview_card"])
        shadow["preview_card"]["self_check_summary"]["self_check_status"] = "blocked"
        review = build_frontier_intelligence_shadow_review_v1(EXISTING_RESPONSE, shadow)
        self.assertIn(review["recommendation"], {"candidate_blocked", "needs_more_review"})
        self.assertIn("candidate_blocked_by_self_check", review["safety_findings"])

    def test_09_replacement_and_runtime_flags_remain_false(self):
        review = self.safe_review()
        self.assertFalse(review["safe_to_replace_live_output"])
        self.assertFalse(review["safe_to_wire_runtime"])
        self.assertFalse(review["frontier_candidate_summary"]["candidate_returned_as_content"])
        self.assertFalse(review["frontier_preview_summary"]["safe_to_wire_runtime"])

    def test_10_validation_accepts_safe_shadow_review(self):
        result = validate_frontier_intelligence_shadow_review_v1(self.safe_review())
        self.assertTrue(result["valid"], result)
        self.assertEqual("accepted", result["validation_status"])

    def test_11_validation_rejects_numeric_score_fields(self):
        unsafe = self.safe_review()
        unsafe["score"] = 99
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_answer_key_score_or_grade", {v["category"] for v in result["violations"]})

    def test_12_validation_rejects_pass_fail_grading_fields(self):
        unsafe = self.safe_review()
        unsafe["pass_fail"] = "passed"
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_answer_key_score_or_grade", categories)

    def test_13_validation_rejects_runtime_or_replacement_true(self):
        for key in ["safe_to_wire_runtime", "safe_to_replace_live_output"]:
            unsafe = self.safe_review()
            unsafe[key] = True
            result = validate_frontier_intelligence_shadow_review_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_14_validation_rejects_official_iq_benchmark_certification_claims(self):
        unsafe = self.safe_review()
        unsafe["comparison_findings"].append("official IQ benchmark certification claim")
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_15_validation_rejects_answer_key_and_hidden_prompt_fields(self):
        unsafe = self.safe_review()
        unsafe["answer_key"] = {"q": "a"}
        unsafe["nested"] = {"hidden_prompt": "secret"}
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_answer_key_score_or_grade", {v["category"] for v in result["violations"]})

    def test_16_validation_rejects_fake_memory_self_awareness_mystical_claims(self):
        unsafe = self.safe_review()
        unsafe["frontier_candidate_summary"]["preview_items"].append("I remember you personally from before.")
        unsafe["nested"] = {"fake_self_awareness_claim": True, "mystical_consciousness_claim": True}
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("fake_self_awareness", categories)
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", categories)

    def test_17_validation_rejects_auto_approval_auto_implementation(self):
        unsafe = self.safe_review()
        unsafe["auto_approved"] = True
        unsafe["side_effects"]["auto_implementation"] = True
        result = validate_frontier_intelligence_shadow_review_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_18_markdown_renderer_includes_safe_sections(self):
        markdown = render_frontier_intelligence_shadow_review_markdown_v1(self.safe_review())
        for heading in [
            "Frontier Intelligence Shadow Review",
            "Existing Response Summary",
            "Native Candidate Summary",
            "Review Signals",
            "Safety Findings",
            "Recommendation",
            "Non-Replacement Boundary",
        ]:
            self.assertIn(heading, markdown)
        lowered = markdown.lower()
        self.assertNotIn("answer key", lowered)
        self.assertNotIn("hidden prompt", lowered)
        self.assertNotIn("official iq", lowered)

    def test_19_json_safe_helper_is_serializable(self):
        safe = to_frontier_intelligence_shadow_review_json_safe_v1(self.safe_review())
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("frontier_intelligence_shadow_review_v1", encoded)

    def test_20_helpers_do_not_mutate_inputs(self):
        shadow = safe_shadow_metadata()
        original_shadow = copy.deepcopy(shadow)
        existing = {"content": EXISTING_RESPONSE}
        original_existing = copy.deepcopy(existing)
        build_frontier_intelligence_shadow_review_v1(existing, shadow)
        derive_frontier_shadow_review_findings_v1(existing, shadow["preview_card"])
        self.assertEqual(original_shadow, shadow)
        self.assertEqual(original_existing, existing)

    def test_21_helpers_do_not_create_weslr_runtime_state(self):
        before = weslr_state_snapshot()
        self.safe_review()
        after = weslr_state_snapshot()
        self.assertEqual(before, after)

    def test_22_no_model_calls(self):
        with mock.patch("llm_runtime.generate_chat", side_effect=AssertionError("model call not allowed")):
            review = self.safe_review()
        self.assertFalse(review["side_effects"]["model_calls"])

    def test_23_no_persistence_file_creation_by_default(self):
        review = self.safe_review()
        self.assertFalse(review["side_effects"]["persistence"])
        self.assertFalse(review["side_effects"]["weslr_runtime_state_created"])

    def test_24_no_prompt_specific_hardcoded_chatbot_script_added(self):
        source = (ROOT / "weslr" / "frontier_intelligence_shadow_review.py").read_text().lower()
        self.assertNotIn("if user asks", source)
        review = self.safe_review()
        self.assertFalse(review["side_effects"]["prompt_specific_script"])
        self.assertFalse(review["side_effects"]["scoring_engine"])
        self.assertFalse(review["side_effects"]["numeric_scores"])
        self.assertFalse(review["side_effects"]["pass_fail_grading"])


if __name__ == "__main__":
    unittest.main()
