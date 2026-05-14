#!/usr/bin/env python3
"""Focused tests for WESLR AI audit review packet helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_review_packet import (  # noqa: E402
    build_ai_audit_review_packet_v1,
    set_ai_audit_review_packet_decision_v1,
    summarize_ai_audit_review_packet_v1,
    validate_ai_audit_review_packet_v1,
)


class AIAuditReviewPacketV1Tests(unittest.TestCase):
    def plan(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_target_redacted", target_kind="assistant")
        return build_ai_audit_plan_v1(target=target, limit=2)["plan"]

    def findings(self, plan=None):
        plan = plan or self.plan()
        return [
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][0],
                target_name=plan["target"]["target_name"],
                finding_type="provenance_honesty",
                verdict="supported",
                reviewer_notes="redacted reviewer note one",
            ),
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][1],
                target_name=plan["target"]["target_name"],
                finding_type="calibration",
                verdict="needs_more_evidence",
                reviewer_notes="redacted reviewer note two",
            ),
        ]

    def test_01_build_review_packet_from_plan_and_findings(self):
        plan = self.plan()
        packet = build_ai_audit_review_packet_v1(plan, self.findings(plan))
        self.assertTrue(packet["packet_id"].startswith("weslr_ai_audit_review_packet_v1_"))
        self.assertEqual(plan["plan_id"], packet["plan_id"])
        self.assertEqual(2, packet["selected_probe_count"])
        self.assertEqual(2, packet["finding_count"])
        self.assertFalse(packet["executable"])
        self.assertFalse(packet["scoring_engine"])

    def test_02_validation_accepts_safe_dry_review_packet(self):
        plan = self.plan()
        findings = self.findings(plan)
        packet = build_ai_audit_review_packet_v1(plan, findings)
        result = validate_ai_audit_review_packet_v1(packet, plan=plan, findings=findings)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["issues"])

    def test_03_validation_rejects_executable_marker(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        packet["executable"] = True
        packet["execution_status"] = "run_now"
        result = validate_ai_audit_review_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertIn("packet executable must be False", result["issues"])
        self.assertIn("packet execution_status must be dry_review_only or not_executable", result["issues"])

    def test_04_validation_rejects_answer_key_or_official_score_fields(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        packet["answer_key"] = "not allowed"
        packet["official_score"] = 100
        result = validate_ai_audit_review_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden review packet field: packet.answer_key", result["issues"])
        self.assertIn("forbidden review packet field: packet.official_score", result["issues"])

    def test_05_validation_rejects_certification_or_official_benchmark_claims(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        packet["certification"] = "certified"
        packet["official_benchmark_result"] = "passed"
        result = validate_ai_audit_review_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden review packet field: packet.certification", result["issues"])
        self.assertIn("forbidden review packet field: packet.official_benchmark_result", result["issues"])

    def test_06_validation_rejects_findings_from_wrong_plan_id(self):
        plan = self.plan()
        findings = self.findings(plan)
        findings[0]["plan_id"] = "wrong_plan"
        packet = build_ai_audit_review_packet_v1(plan, findings)
        result = validate_ai_audit_review_packet_v1(packet, plan=plan, findings=findings)
        self.assertFalse(result["valid"])
        self.assertTrue(any("finding plan_id mismatch" in issue for issue in result["issues"]))

    def test_07_summary_is_redacted_and_omits_reviewer_notes(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        summary = summarize_ai_audit_review_packet_v1(packet)
        self.assertTrue(summary["redacted_count_only"])
        self.assertNotIn("reviewer note", repr(summary).lower())
        self.assertNotIn("reviewer_notes", repr(summary))
        self.assertEqual(2, summary["finding_count"])
        self.assertEqual("safe_review_packet", summary["safety_status"])

    def test_08_decision_helper_accepts_allowed_decisions(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        updated = set_ai_audit_review_packet_decision_v1(packet, "needs_more_evidence", notes="operator placeholder")
        self.assertEqual("needs_more_evidence", updated["operator_decision"])
        self.assertEqual("reviewed", updated["operator_review_status"])
        self.assertEqual("none", packet["operator_decision"])
        self.assertTrue(updated["validation_status"]["valid"])

    def test_09_decision_helper_rejects_unknown_decision(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        with self.assertRaises(ValueError):
            set_ai_audit_review_packet_decision_v1(packet, "promote_to_truth")

    def test_10_packet_remains_in_memory_and_creates_no_runtime_state(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        self.assertTrue(packet["in_memory_only"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_review_packet.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_review_packet.jsonl").exists())

    def test_11_inputs_are_not_mutated(self):
        plan = self.plan()
        findings = self.findings(plan)
        plan_before = dict(plan)
        findings_before = [dict(finding) for finding in findings]
        packet = build_ai_audit_review_packet_v1(plan, findings)
        packet["plan_id"] = "mutated"
        packet["finding_summary"]["finding_count"] = 0
        self.assertEqual(plan_before, plan)
        self.assertEqual(findings_before, findings)

    def test_12_operator_decision_fields_are_placeholders_only(self):
        packet = build_ai_audit_review_packet_v1(self.plan(), self.findings())
        updated = set_ai_audit_review_packet_decision_v1(packet, "accepted_as_observation")
        self.assertFalse(updated["scoring_engine"])
        self.assertFalse(updated["automated_grading"])
        self.assertFalse(updated["answer_evaluation"])
        self.assertTrue(updated["non_official"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
