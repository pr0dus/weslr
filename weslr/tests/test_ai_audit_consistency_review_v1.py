#!/usr/bin/env python3
"""Focused tests for WESLR AI audit consistency review helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_consistency_review import (  # noqa: E402
    build_ai_audit_consistency_review_result_v1,
    review_ai_audit_packet_report_consistency_v1,
    review_ai_audit_plan_finding_consistency_v1,
    review_ai_audit_review_card_consistency_v1,
    validate_ai_audit_consistency_review_result_v1,
)
from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_operator_review_surface import build_ai_audit_operator_review_card_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402


class AIAuditConsistencyReviewV1Tests(unittest.TestCase):
    def bundle(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_consistency_target", target_kind="assistant")
        plan = build_ai_audit_plan_v1(target=target, limit=2)["plan"]
        findings = [
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][0],
                target_name=plan["target"]["target_name"],
                finding_type="provenance_honesty",
                verdict="supported",
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
        packet_card = build_ai_audit_operator_review_card_v1(packet)
        report_card = build_ai_audit_operator_review_card_v1(report)
        return plan, findings, packet, report, packet_card, report_card

    def test_01_plan_findings_consistency_passes_for_matching_artifacts(self):
        plan, findings, *_ = self.bundle()
        review = review_ai_audit_plan_finding_consistency_v1(plan, findings)
        self.assertEqual([], review["issues"])
        self.assertEqual(2, review["covered_probe_count"])
        self.assertTrue(review["not_a_runner"])

    def test_02_plan_findings_consistency_detects_plan_id_mismatch(self):
        plan, findings, *_ = self.bundle()
        findings[0]["plan_id"] = "wrong_plan"
        review = review_ai_audit_plan_finding_consistency_v1(plan, findings)
        self.assertIn("plan_id_mismatch", {issue["issue_type"] for issue in review["issues"]})

    def test_03_plan_findings_consistency_detects_probe_id_not_in_plan(self):
        plan, findings, *_ = self.bundle()
        findings[0]["probe_id"] = "unknown_probe"
        review = review_ai_audit_plan_finding_consistency_v1(plan, findings)
        self.assertIn("unknown_or_unlinked_artifact", {issue["issue_type"] for issue in review["issues"]})

    def test_04_duplicate_finding_ids_are_detected(self):
        plan, findings, *_ = self.bundle()
        findings[1]["finding_id"] = findings[0]["finding_id"]
        review = review_ai_audit_plan_finding_consistency_v1(plan, findings)
        explanations = "\n".join(issue["explanation"] for issue in review["issues"])
        self.assertIn("Duplicate finding_id detected", explanations)

    def test_05_packet_report_consistency_passes_for_matching_artifacts(self):
        _, _, packet, report, *_ = self.bundle()
        review = review_ai_audit_packet_report_consistency_v1(packet, report)
        self.assertEqual([], review["issues"])
        self.assertTrue(review["no_model_calls"])

    def test_06_packet_report_consistency_detects_finding_count_mismatch(self):
        _, _, packet, report, *_ = self.bundle()
        report["total_findings"] = 99
        review = review_ai_audit_packet_report_consistency_v1(packet, report)
        self.assertIn("finding_count_mismatch", {issue["issue_type"] for issue in review["issues"]})

    def test_07_packet_report_consistency_detects_verdict_count_mismatch(self):
        _, _, packet, report, *_ = self.bundle()
        report["verdict_counts"] = {"supported": 99}
        review = review_ai_audit_packet_report_consistency_v1(packet, report)
        self.assertIn("verdict_count_mismatch", {issue["issue_type"] for issue in review["issues"]})

    def test_08_card_packet_consistency_detects_count_mismatch(self):
        _, _, packet, _, packet_card, _ = self.bundle()
        packet_card["total_findings"] = 99
        review = review_ai_audit_review_card_consistency_v1(packet_card, packet)
        self.assertIn("finding_count_mismatch", {issue["issue_type"] for issue in review["issues"]})

    def test_09_full_review_returns_consistent_when_artifacts_agree(self):
        plan, findings, packet, report, packet_card, _ = self.bundle()
        result = build_ai_audit_consistency_review_result_v1(plan=plan, findings=findings, packet=packet, report=report, cards=[packet_card])
        self.assertEqual("consistent", result["consistency_status"])
        self.assertEqual(0, result["total_issues"])

    def test_10_full_review_returns_inconsistent_when_artifacts_disagree(self):
        plan, findings, packet, report, packet_card, _ = self.bundle()
        report["total_findings"] = 99
        result = build_ai_audit_consistency_review_result_v1(plan=plan, findings=findings, packet=packet, report=report, cards=[packet_card])
        self.assertEqual("inconsistent", result["consistency_status"])
        self.assertGreater(result["total_issues"], 0)

    def test_11_validation_accepts_safe_consistency_review_result(self):
        plan, findings, packet, report, packet_card, _ = self.bundle()
        result = build_ai_audit_consistency_review_result_v1(plan=plan, findings=findings, packet=packet, report=report, cards=[packet_card])
        validation = validate_ai_audit_consistency_review_result_v1(result)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertEqual([], validation["issues"])

    def test_12_validation_rejects_injected_executable_or_runnable_marker(self):
        result = build_ai_audit_consistency_review_result_v1()
        result["executable"] = True
        result["runnable"] = True
        validation = validate_ai_audit_consistency_review_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden consistency true marker: consistency_review.executable", validation["issues"])
        self.assertIn("forbidden consistency true marker: consistency_review.runnable", validation["issues"])

    def test_13_validation_rejects_injected_score_or_official_score_fields(self):
        result = build_ai_audit_consistency_review_result_v1()
        result["score"] = 1
        result["official_score"] = 100
        validation = validate_ai_audit_consistency_review_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden consistency field: consistency_review.score", validation["issues"])
        self.assertIn("forbidden consistency field: consistency_review.official_score", validation["issues"])

    def test_14_validation_rejects_injected_answer_key_or_hidden_prompt_fields(self):
        result = build_ai_audit_consistency_review_result_v1()
        result["answer_key"] = "not allowed"
        result["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_consistency_review_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden consistency field: consistency_review.answer_key", validation["issues"])
        self.assertIn("forbidden consistency field: consistency_review.hidden_prompt", validation["issues"])

    def test_15_helpers_do_not_mutate_inputs(self):
        plan, findings, packet, report, packet_card, _ = self.bundle()
        plan_before = dict(plan)
        findings_before = [dict(item) for item in findings]
        packet_before = dict(packet)
        report_before = dict(report)
        card_before = dict(packet_card)
        result = build_ai_audit_consistency_review_result_v1(plan=plan, findings=findings, packet=packet, report=report, cards=[packet_card])
        result["total_issues"] = 99
        self.assertEqual(plan_before, plan)
        self.assertEqual(findings_before, findings)
        self.assertEqual(packet_before, packet)
        self.assertEqual(report_before, report)
        self.assertEqual(card_before, packet_card)

    def test_16_helpers_do_not_create_runtime_state_or_files(self):
        build_ai_audit_consistency_review_result_v1()
        self.assertFalse((ROOT / ".weslr" / "ai_audit_consistency_review.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_consistency_review.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_consistency_review.jsonl").exists())

    def test_17_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        build_ai_audit_consistency_review_result_v1()
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
