#!/usr/bin/env python3
"""Focused tests for WESLR AI audit readiness gap advisor helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_readiness_gap_advisor import (  # noqa: E402
    build_ai_audit_next_proposal_candidates_v1,
    build_ai_audit_readiness_gap_advisor_result_v1,
    detect_ai_audit_readiness_gaps_v1,
    advise_ai_audit_readiness_v1,
    summarize_ai_audit_coverage_v1,
    validate_ai_audit_readiness_gap_advisor_result_v1,
)
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402


class AIAuditReadinessGapAdvisorV1Tests(unittest.TestCase):
    def plan(self, limit=2):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_target_advisor", target_kind="assistant")
        return build_ai_audit_plan_v1(target=target, limit=limit)["plan"]

    def packet_bundle(self):
        plan = self.plan(limit=2)
        findings = [
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][0],
                target_name=plan["target"]["target_name"],
                finding_type="provenance_honesty",
                verdict="supported",
                reviewer_notes="local note should remain internal",
            ),
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][1],
                target_name=plan["target"]["target_name"],
                finding_type="calibration",
                verdict="needs_more_evidence",
            ),
        ]
        packet = build_ai_audit_review_packet_v1(plan, findings)
        report = build_ai_audit_redacted_report_v1(packet)
        return plan, findings, packet, report

    def tiny_inventory(self):
        return [
            {
                "probe_id": "tiny_probe_001",
                "probe_category": "provenance_honesty",
                "claim_category": "provenance_claim",
                "target_claim_summary": "Synthetic claim.",
                "probe_goal": "Synthetic goal.",
                "safe_prompt_summary": "Synthetic prompt summary.",
                "expected_evidence_type": "Synthetic evidence.",
                "failure_modes": ["synthetic failure"],
                "operator_review_required": True,
                "protected_item_free": True,
                "answer_key_free": True,
                "official_score_claimed": False,
                "benchmark_tuning": False,
                "runtime_behavior_change": False,
            }
        ]

    def test_01_coverage_summary_includes_inventory_categories(self):
        summary = summarize_ai_audit_coverage_v1()
        self.assertEqual("ai_audit_coverage_summary_v1", summary["schema_version"])
        self.assertGreaterEqual(summary["total_probes"], 12)
        self.assertIn("provenance_honesty", summary["categories_covered"])
        self.assertIn("provenance_claim", summary["claim_categories_covered"])
        self.assertTrue(summary["redacted_count_only"])
        self.assertTrue(summary["no_execution"])

    def test_02_coverage_summary_is_count_only_and_deterministic(self):
        first = summarize_ai_audit_coverage_v1()
        second = summarize_ai_audit_coverage_v1()
        self.assertEqual(first, second)
        self.assertIn("category_count", first)
        self.assertIn("claim_category_count", first)
        self.assertNotIn("model_output", first)
        self.assertNotIn("answer_key", first)

    def test_03_gap_detector_identifies_missing_category_and_claim_coverage(self):
        gaps = detect_ai_audit_readiness_gaps_v1(
            inventory=self.tiny_inventory(),
            expected_probe_categories={"provenance_honesty", "calibration_quality"},
            expected_claim_categories={"provenance_claim", "calibration_claim"},
        )
        gap_types = {gap["gap_type"] for gap in gaps}
        self.assertIn("category_missing", gap_types)
        self.assertIn("claim_category_missing", gap_types)

    def test_04_gap_records_are_non_executing(self):
        gaps = detect_ai_audit_readiness_gaps_v1(inventory=self.tiny_inventory(), expected_probe_categories={"missing_category"})
        self.assertTrue(gaps)
        for gap in gaps:
            self.assertEqual("non_executing_gap_only", gap["execution_status"])
            self.assertFalse(gap["automatic_fix"])
            self.assertFalse(gap["truth_promotion"])
            self.assertFalse(gap["runtime_behavior_change"])

    def test_05_readiness_advisor_marks_foundation_and_review_ready_where_appropriate(self):
        plan, findings, packet, report = self.packet_bundle()
        coverage = summarize_ai_audit_coverage_v1(plans=[plan], findings=findings, packets=[packet], reports=[report])
        gaps = detect_ai_audit_readiness_gaps_v1(plans=[plan], findings=findings, packets=[packet], reports=[report])
        readiness = advise_ai_audit_readiness_v1(coverage_summary=coverage, gaps=gaps)
        self.assertIn("foundation_ready", readiness["readiness_status"])
        self.assertIn("planning_ready", readiness["readiness_status"])
        self.assertIn("review_ready", readiness["readiness_status"])

    def test_06_readiness_advisor_marks_runner_scoring_external_testing_not_authorized(self):
        readiness = advise_ai_audit_readiness_v1(coverage_summary=summarize_ai_audit_coverage_v1(), gaps=[])
        self.assertIn("execution_not_authorized", readiness["readiness_status"])
        self.assertIn("scoring_not_authorized", readiness["readiness_status"])
        self.assertIn("external_testing_not_authorized", readiness["readiness_status"])
        self.assertIn("create_probe_runner", readiness["forbidden_next_steps"])

    def test_07_proposal_candidates_are_proposal_only_and_require_approval(self):
        gaps = detect_ai_audit_readiness_gaps_v1(inventory=self.tiny_inventory(), expected_probe_categories={"missing_category"})
        readiness = advise_ai_audit_readiness_v1(coverage_summary=summarize_ai_audit_coverage_v1(inventory=self.tiny_inventory()), gaps=gaps)
        proposals = build_ai_audit_next_proposal_candidates_v1(gaps, readiness)
        self.assertTrue(proposals)
        for proposal in proposals:
            self.assertEqual("proposal_only", proposal["implementation_status"])
            self.assertTrue(proposal["requires_operator_approval"])
            self.assertFalse(proposal["automatic_approval"])

    def test_08_full_advisor_result_combines_summary_gaps_readiness_proposals(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        self.assertEqual("ai_audit_readiness_gap_advisor_result_v1", result["schema_version"])
        self.assertIn("coverage_summary", result)
        self.assertIn("gap_records", result)
        self.assertIn("readiness_report", result)
        self.assertIn("proposal_candidates", result)
        self.assertTrue(result["in_memory_only"])
        self.assertTrue(result["not_a_runner"])

    def test_09_validation_accepts_safe_advisor_result(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertEqual([], validation["issues"])

    def test_10_validation_rejects_injected_executable_or_runnable_marker(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        result["executable"] = True
        result["runnable"] = True
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden advisor true marker: advisor_result.executable", validation["issues"])
        self.assertIn("forbidden advisor true marker: advisor_result.runnable", validation["issues"])

    def test_11_validation_rejects_injected_score_or_official_score_fields(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        result["score"] = 1
        result["official_score"] = 100
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden advisor field: advisor_result.score", validation["issues"])
        self.assertIn("forbidden advisor field: advisor_result.official_score", validation["issues"])

    def test_12_validation_rejects_injected_answer_key_or_hidden_prompt_fields(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        result["answer_key"] = "not allowed"
        result["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden advisor field: advisor_result.answer_key", validation["issues"])
        self.assertIn("forbidden advisor field: advisor_result.hidden_prompt", validation["issues"])

    def test_13_validation_rejects_proposal_candidates_without_approval(self):
        result = build_ai_audit_readiness_gap_advisor_result_v1()
        result["proposal_candidates"][0]["requires_operator_approval"] = False
        validation = validate_ai_audit_readiness_gap_advisor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("proposal must require operator approval", "\n".join(validation["issues"]))

    def test_14_helpers_do_not_mutate_inputs(self):
        plan, findings, packet, report = self.packet_bundle()
        plan_before = dict(plan)
        findings_before = [dict(item) for item in findings]
        packet_before = dict(packet)
        report_before = dict(report)
        result = build_ai_audit_readiness_gap_advisor_result_v1(plans=[plan], findings=findings, packets=[packet], reports=[report])
        result["coverage_summary"]["total_probes"] = -1
        self.assertEqual(plan_before, plan)
        self.assertEqual(findings_before, findings)
        self.assertEqual(packet_before, packet)
        self.assertEqual(report_before, report)

    def test_15_helpers_do_not_create_runtime_state_or_files(self):
        build_ai_audit_readiness_gap_advisor_result_v1()
        self.assertFalse((ROOT / ".weslr" / "ai_audit_readiness_gap_advisor.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_readiness_gap_advisor.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_readiness_gap_advisor.jsonl").exists())

    def test_16_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        build_ai_audit_readiness_gap_advisor_result_v1()
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
