#!/usr/bin/env python3
"""Focused tests for WESLR AI audit safe next-step recommender helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_operator_review_surface import build_ai_audit_operator_review_card_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_preflight_review import build_ai_audit_preflight_review_v1  # noqa: E402
from weslr.ai_audit_readiness_gap_advisor import build_ai_audit_readiness_gap_advisor_result_v1  # noqa: E402
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402
from weslr.ai_audit_safe_next_step_recommender import (  # noqa: E402
    build_ai_audit_safe_next_step_candidates_v1,
    build_ai_audit_safe_next_step_recommendation_result_v1,
    rank_ai_audit_safe_next_step_candidates_v1,
    render_ai_audit_safe_next_step_recommendations_markdown_v1,
    validate_ai_audit_safe_next_step_recommendation_result_v1,
)
from weslr.ai_audit_self_governance_surface import build_ai_audit_self_governance_card_v1  # noqa: E402


class AIAuditSafeNextStepRecommenderV1Tests(unittest.TestCase):
    def bundle(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_recommender_target", target_kind="assistant")
        plan = build_ai_audit_plan_v1(target=target, limit=2)["plan"]
        findings = [
            create_ai_audit_finding_v1(plan_id=plan["plan_id"], probe_id=plan["selected_probe_ids"][0], target_name=plan["target"]["target_name"], finding_type="provenance_honesty", verdict="supported"),
            create_ai_audit_finding_v1(plan_id=plan["plan_id"], probe_id=plan["selected_probe_ids"][1], target_name=plan["target"]["target_name"], finding_type="calibration", verdict="needs_more_evidence"),
        ]
        packet = build_ai_audit_review_packet_v1(plan, findings)
        report = build_ai_audit_redacted_report_v1(packet)
        review_card = build_ai_audit_operator_review_card_v1(packet)
        readiness = build_ai_audit_readiness_gap_advisor_result_v1(plans=[plan], findings=findings, packets=[packet], reports=[report])
        preflight = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[review_card], texts=["safe dry review only"])
        governance_card = build_ai_audit_self_governance_card_v1(
            readiness_gap_advisor_result=readiness,
            consistency_review_result=preflight["consistency_result"],
            drift_monitor_result=preflight["drift_result"],
            preflight_review_result=preflight,
        )
        return readiness, preflight, governance_card

    def test_01_candidates_build_from_safe_self_governance_preflight_inputs(self):
        readiness, preflight, governance_card = self.bundle()
        candidates = build_ai_audit_safe_next_step_candidates_v1(
            self_governance_card=governance_card,
            preflight_review_result=preflight,
            readiness_gap_advisor_result=readiness,
        )
        self.assertTrue(candidates)
        self.assertTrue(all(candidate["implementation_status"] == "recommendation_only" for candidate in candidates))
        self.assertTrue(all(candidate["requires_operator_approval"] for candidate in candidates))

    def test_02_top_recommendation_prefers_safe_non_executing_next_step(self):
        readiness, preflight, governance_card = self.bundle()
        result = build_ai_audit_safe_next_step_recommendation_result_v1(
            self_governance_card=governance_card,
            preflight_review_result=preflight,
            readiness_gap_advisor_result=readiness,
        )
        self.assertEqual("safe_non_executing", result["top_recommendation"]["safety_level"])
        self.assertNotEqual("blocked", result["top_recommendation"]["safety_level"])

    def test_03_blocked_runner_grading_external_testing_candidates_remain_blocked(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        blocked_phase_types = {candidate["phase_type"] for candidate in result["blocked_recommendations"]}
        self.assertIn("blocked_runner", blocked_phase_types)
        self.assertIn("blocked_scoring", blocked_phase_types)
        self.assertIn("blocked_external_testing", blocked_phase_types)
        self.assertTrue(all(candidate["safety_level"] == "blocked" for candidate in result["blocked_recommendations"]))

    def test_04_ranking_is_deterministic(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        reversed_ranked = rank_ai_audit_safe_next_step_candidates_v1(list(reversed(result["ranked_recommendations"])))
        self.assertEqual([c["recommendation_id"] for c in result["ranked_recommendations"]], [c["recommendation_id"] for c in reversed_ranked])

    def test_05_recommendation_result_marks_all_risky_actions_not_authorized(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        for marker in ("runner_not_authorized", "scoring_not_authorized", "external_testing_not_authorized", "runtime_wiring_not_authorized"):
            self.assertIn(marker, result["authorization_status"])
        for key in ("runner_authorized", "scoring_authorized", "external_testing_authorized", "runtime_wiring_authorized", "automatic_implementation_authorized"):
            self.assertFalse(result["safety_boundaries"][key])

    def test_06_recommended_does_not_imply_approved(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        self.assertTrue(result["recommended_does_not_mean_approved"])
        self.assertTrue(result["not_implementation"])
        self.assertIn("not approved", result["explanation"])

    def test_07_validation_accepts_safe_recommendation_result(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertTrue(validation["valid"], validation["issues"])

    def test_08_validation_rejects_executable_or_runnable_marker(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["executable"] = True
        result["runnable"] = True
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden recommendation true marker: result.executable", validation["issues"])
        self.assertIn("forbidden recommendation true marker: result.runnable", validation["issues"])

    def test_09_validation_rejects_score_or_official_score_fields(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["score"] = 1
        result["official_score"] = 100
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden recommendation field: result.score", validation["issues"])
        self.assertIn("forbidden recommendation field: result.official_score", validation["issues"])

    def test_10_validation_rejects_answer_key_or_hidden_prompt_fields(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["answer_key"] = "not allowed"
        result["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden recommendation field: result.answer_key", validation["issues"])
        self.assertIn("forbidden recommendation field: result.hidden_prompt", validation["issues"])

    def test_11_validation_rejects_auto_approval_truth_promotion_auto_implementation(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["automatic_approval"] = True
        result["truth_promotion"] = True
        result["automatic_implementation"] = True
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden recommendation true marker: result.automatic_approval", validation["issues"])
        self.assertIn("forbidden recommendation true marker: result.truth_promotion", validation["issues"])
        self.assertIn("forbidden recommendation true marker: result.automatic_implementation", validation["issues"])

    def test_12_validation_rejects_recommendation_implying_runner_grading_external_probing_authorized(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["ranked_recommendations"][0]["title"] = "Authorize runner and external probing"
        result["ranked_recommendations"][0]["safety_level"] = "safe_non_executing"
        validation = validate_ai_audit_safe_next_step_recommendation_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("recommendation must not imply runner/scoring/external probing is authorized", validation["issues"])

    def test_13_markdown_renderer_includes_safe_sections_and_no_forbidden_content(self):
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        result["safe_next_steps"].append("inspect_answer_key_hidden_prompt_official_score_certification")
        markdown = render_ai_audit_safe_next_step_recommendations_markdown_v1(result).lower()
        for section in (
            "# ai audit safe next-step recommendations",
            "## top recommendation",
            "## why",
            "## safe next steps",
            "## blocked / forbidden steps",
            "## authorization boundaries",
        ):
            self.assertIn(section, markdown)
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("hidden_prompt", markdown)
        self.assertNotIn("official_score", markdown)
        self.assertNotIn("certification", markdown)

    def test_14_helpers_do_not_mutate_inputs(self):
        readiness, preflight, governance_card = self.bundle()
        readiness_before = dict(readiness)
        preflight_before = dict(preflight)
        governance_card_before = dict(governance_card)
        result = build_ai_audit_safe_next_step_recommendation_result_v1(
            self_governance_card=governance_card,
            preflight_review_result=preflight,
            readiness_gap_advisor_result=readiness,
        )
        result["explanation"] = "mutated"
        self.assertEqual(readiness_before, readiness)
        self.assertEqual(preflight_before, preflight)
        self.assertEqual(governance_card_before, governance_card)

    def test_15_helpers_do_not_create_weslr_runtime_state(self):
        build_ai_audit_safe_next_step_recommendation_result_v1()
        self.assertFalse((ROOT / ".weslr" / "ai_audit_safe_next_step_recommendations.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_safe_next_step_recommendations.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_safe_next_step_recommendations.jsonl").exists())

    def test_16_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        result = build_ai_audit_safe_next_step_recommendation_result_v1()
        render_ai_audit_safe_next_step_recommendations_markdown_v1(result)
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
