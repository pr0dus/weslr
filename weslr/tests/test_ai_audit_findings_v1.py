#!/usr/bin/env python3
"""Focused tests for WESLR AI audit finding helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import (  # noqa: E402
    build_ai_audit_finding_collection_v1,
    create_ai_audit_finding_v1,
    summarize_ai_audit_findings_v1,
    validate_ai_audit_finding_v1,
)
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402


class AIAuditFindingsV1Tests(unittest.TestCase):
    def plan(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_target_redacted", target_kind="assistant")
        return build_ai_audit_plan_v1(target=target, limit=2)["plan"]

    def finding(self, **overrides):
        plan = overrides.pop("plan", self.plan())
        data = dict(
            plan_id=plan["plan_id"],
            probe_id=plan["selected_probe_ids"][0],
            target_name=plan["target"]["target_name"],
            finding_type="provenance_honesty",
            verdict="supported",
            evidence_refs=["evidence:manual:001"],
            reviewer_notes="redacted manual note",
            source="manual_review_only",
        )
        data.update(overrides)
        return create_ai_audit_finding_v1(**data)

    def test_01_create_valid_finding(self):
        finding = self.finding()
        self.assertTrue(finding["finding_id"].startswith("weslr_ai_audit_finding_v1_"))
        self.assertEqual("manual_review_only", finding["source"])
        self.assertFalse(finding["executable"])
        self.assertFalse(finding["scoring_engine"])

    def test_02_validation_accepts_valid_manual_dry_finding(self):
        plan = self.plan()
        finding = self.finding(plan=plan)
        result = validate_ai_audit_finding_v1(finding, plan=plan)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["issues"])
        self.assertFalse(result["official_score_claimed"])

    def test_03_validation_rejects_missing_required_fields(self):
        finding = self.finding()
        finding["finding_id"] = ""
        finding["probe_id"] = ""
        result = validate_ai_audit_finding_v1(finding)
        self.assertFalse(result["valid"])
        self.assertIn("missing finding_id", result["issues"])
        self.assertIn("missing probe_id", result["issues"])

    def test_04_validation_rejects_unknown_verdict(self):
        finding = self.finding(verdict="officially_correct")
        result = validate_ai_audit_finding_v1(finding)
        self.assertFalse(result["valid"])
        self.assertIn("invalid verdict", result["issues"])

    def test_05_validation_rejects_executable_marker(self):
        finding = self.finding()
        finding["executable"] = True
        finding["safety_flags"]["executable_marker"] = True
        result = validate_ai_audit_finding_v1(finding)
        self.assertFalse(result["valid"])
        self.assertIn("finding executable must be False", result["issues"])
        self.assertIn("executable marker", result["issues"])

    def test_06_validation_rejects_answer_key_or_official_score_fields(self):
        finding = self.finding()
        finding["answer_key"] = "not allowed"
        finding["official_score"] = 100
        result = validate_ai_audit_finding_v1(finding)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden finding field: finding.answer_key", result["issues"])
        self.assertIn("forbidden finding field: finding.official_score", result["issues"])

    def test_07_validation_rejects_plan_probe_mismatch(self):
        plan = self.plan()
        finding = self.finding(plan=plan)
        finding["plan_id"] = "wrong_plan"
        finding["probe_id"] = "wrong_probe"
        result = validate_ai_audit_finding_v1(finding, plan=plan)
        self.assertFalse(result["valid"])
        self.assertIn("finding plan_id does not match plan", result["issues"])
        self.assertIn("finding probe_id not present in plan", result["issues"])

    def test_08_summary_counts_verdicts_and_finding_types(self):
        findings = [self.finding(verdict="supported"), self.finding(verdict="unsupported", finding_type="calibration")]
        summary = summarize_ai_audit_findings_v1(findings, validate=True)
        self.assertEqual(2, summary["finding_count"])
        self.assertEqual(1, summary["verdict_counts"]["supported"])
        self.assertEqual(1, summary["verdict_counts"]["unsupported"])
        self.assertEqual(1, summary["finding_type_counts"]["calibration"])
        self.assertEqual("safe_findings", summary["safety_status"])

    def test_09_summary_is_redacted_and_omits_reviewer_notes(self):
        finding = self.finding(reviewer_notes="sensitive reviewer note should not appear")
        summary = summarize_ai_audit_findings_v1([finding])
        self.assertTrue(summary["redacted_count_only"])
        self.assertNotIn("sensitive reviewer note", repr(summary).lower())
        self.assertNotIn("reviewer_notes", repr(summary))

    def test_10_collection_rejects_duplicate_finding_ids(self):
        first = self.finding()
        second = dict(first)
        collection = build_ai_audit_finding_collection_v1([first, second])
        self.assertFalse(collection["validation"]["valid"])
        self.assertEqual([first["finding_id"]], collection["duplicate_finding_ids"])
        self.assertIn(f"duplicate finding_id: {first['finding_id']}", collection["validation"]["issues"])

    def test_11_collection_is_in_memory_and_creates_no_runtime_state(self):
        collection = build_ai_audit_finding_collection_v1([self.finding()])
        self.assertTrue(collection["in_memory_only"])
        self.assertFalse(collection["execution_allowed"])
        self.assertFalse(collection["scoring_engine"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_findings.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_findings.jsonl").exists())

    def test_12_collection_does_not_mutate_input_findings(self):
        finding = self.finding()
        original = dict(finding)
        collection = build_ai_audit_finding_collection_v1([finding])
        collection["findings"][0]["finding_id"] = "mutated"
        self.assertEqual(original, finding)


if __name__ == "__main__":
    unittest.main(verbosity=2)
