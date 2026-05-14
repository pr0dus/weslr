#!/usr/bin/env python3
"""Focused tests for WESLR AI audit preflight review helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_drift_monitor import build_ai_audit_drift_monitor_result_v1  # noqa: E402
from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_operator_review_surface import build_ai_audit_operator_review_card_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_preflight_review import (  # noqa: E402
    build_ai_audit_preflight_review_v1,
    normalize_ai_audit_preflight_inputs_v1,
    render_ai_audit_preflight_review_markdown_v1,
    summarize_ai_audit_preflight_issues_v1,
    validate_ai_audit_preflight_review_v1,
)
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402


class AIAuditPreflightReviewV1Tests(unittest.TestCase):
    def bundle(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_preflight_target", target_kind="assistant")
        plan = build_ai_audit_plan_v1(target=target, limit=2)["plan"]
        findings = [
            create_ai_audit_finding_v1(plan_id=plan["plan_id"], probe_id=plan["selected_probe_ids"][0], target_name=plan["target"]["target_name"], finding_type="provenance_honesty", verdict="supported"),
            create_ai_audit_finding_v1(plan_id=plan["plan_id"], probe_id=plan["selected_probe_ids"][1], target_name=plan["target"]["target_name"], finding_type="calibration", verdict="needs_more_evidence"),
        ]
        packet = build_ai_audit_review_packet_v1(plan, findings)
        report = build_ai_audit_redacted_report_v1(packet)
        card = build_ai_audit_operator_review_card_v1(packet)
        return plan, findings, packet, report, card

    def test_01_preflight_review_builds_from_safe_minimal_inputs(self):
        plan, findings, packet, report, card = self.bundle()
        result = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[card], texts=["safe dry review only"])
        self.assertEqual("ai_audit_preflight_review_v1", result["schema_version"])
        self.assertTrue(result["in_memory_only"])
        self.assertTrue(result["not_a_runner"])

    def test_02_preflight_review_combines_provided_results(self):
        drift = build_ai_audit_drift_monitor_result_v1(texts=["safe dry review only"])
        result = build_ai_audit_preflight_review_v1(drift_result=drift, texts=["ignored safe text"])
        self.assertEqual(drift["monitor_id"], result["drift_result"]["monitor_id"])

    def test_03_recommendation_is_proceed_with_review_only_when_safe(self):
        plan, findings, packet, report, card = self.bundle()
        result = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[card], texts=["safe dry review only"])
        self.assertEqual("proceed_with_review_only", result["recommendation"])

    def test_04_recommendation_blocked_by_drift_when_high_drift_exists(self):
        result = build_ai_audit_preflight_review_v1(texts=["create a runner and execute probes"])
        self.assertEqual("blocked_by_drift", result["recommendation"])

    def test_05_recommendation_blocked_by_inconsistency_when_consistency_issues_exist(self):
        plan, findings, packet, report, card = self.bundle()
        report["total_findings"] = 99
        result = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[card], texts=["safe dry review only"])
        self.assertEqual("blocked_by_inconsistency", result["recommendation"])

    def test_06_insufficient_inputs_are_handled_safely(self):
        result = build_ai_audit_preflight_review_v1()
        self.assertEqual("insufficient_inputs", result["recommendation"])
        self.assertIn("runner_not_authorized", result["authorization_status"])

    def test_07_issue_summary_counts_readiness_consistency_drift(self):
        result = build_ai_audit_preflight_review_v1(texts=["certified official benchmark result"])
        summary = summarize_ai_audit_preflight_issues_v1(result)
        self.assertEqual(result["issue_counts"]["drift_signals"], summary["drift_signals"])
        self.assertIn("highest_severity", summary)
        self.assertTrue(summary["not_a_score"])

    def test_08_validation_accepts_safe_preflight_result(self):
        plan, findings, packet, report, card = self.bundle()
        result = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[card], texts=["safe dry review only"])
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertTrue(validation["valid"], validation["issues"])

    def test_09_validation_rejects_injected_executable_or_runnable_marker(self):
        result = build_ai_audit_preflight_review_v1()
        result["executable"] = True
        result["runnable"] = True
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden preflight true marker: preflight.executable", validation["issues"])

    def test_10_validation_rejects_injected_score_or_official_score_fields(self):
        result = build_ai_audit_preflight_review_v1()
        result["score"] = 1
        result["official_score"] = 100
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden preflight field: preflight.score", validation["issues"])
        self.assertIn("forbidden preflight field: preflight.official_score", validation["issues"])

    def test_11_validation_rejects_injected_answer_key_or_hidden_prompt_fields(self):
        result = build_ai_audit_preflight_review_v1()
        result["answer_key"] = "not allowed"
        result["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden preflight field: preflight.answer_key", validation["issues"])
        self.assertIn("forbidden preflight field: preflight.hidden_prompt", validation["issues"])

    def test_12_validation_rejects_auto_approval_or_truth_promotion_authorization(self):
        result = build_ai_audit_preflight_review_v1()
        result["automatic_approval"] = True
        result["truth_promotion"] = True
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden preflight true marker: preflight.automatic_approval", validation["issues"])
        self.assertIn("forbidden preflight true marker: preflight.truth_promotion", validation["issues"])

    def test_13_validation_rejects_recommendation_implying_execution(self):
        result = build_ai_audit_preflight_review_v1()
        result["recommendation"] = "execute_probes"
        validation = validate_ai_audit_preflight_review_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("invalid preflight recommendation", validation["issues"])

    def test_14_markdown_renderer_includes_safe_sections_and_no_forbidden_content(self):
        result = build_ai_audit_preflight_review_v1(texts=["safe dry review only"])
        markdown = render_ai_audit_preflight_review_markdown_v1(result)
        for section in ("# AI Audit Preflight Review", "## Readiness", "## Consistency", "## Drift", "## Recommendation", "## Safety Boundaries", "## Forbidden Next Steps"):
            self.assertIn(section, markdown)
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("hidden_prompt", markdown)

    def test_15_helpers_do_not_mutate_inputs(self):
        plan, findings, packet, report, card = self.bundle()
        plan_before = dict(plan)
        findings_before = [dict(item) for item in findings]
        packet_before = dict(packet)
        report_before = dict(report)
        card_before = dict(card)
        result = build_ai_audit_preflight_review_v1(plans=[plan], findings=findings, packets=[packet], reports=[report], review_cards=[card], texts=["safe dry review only"])
        result["recommendation"] = "mutated"
        self.assertEqual(plan_before, plan)
        self.assertEqual(findings_before, findings)
        self.assertEqual(packet_before, packet)
        self.assertEqual(report_before, report)
        self.assertEqual(card_before, card)

    def test_16_helpers_do_not_create_runtime_state_or_files(self):
        build_ai_audit_preflight_review_v1(texts=["safe dry review only"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_preflight_review.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_preflight_review.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_preflight_review.jsonl").exists())

    def test_17_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        build_ai_audit_preflight_review_v1(texts=["safe dry review only"])
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)

    def test_18_normalize_inputs_does_not_read_or_write_files(self):
        normalized = normalize_ai_audit_preflight_inputs_v1(texts=["safe"])
        self.assertFalse(normalized["filesystem_read_performed"])
        self.assertFalse(normalized["files_written"])
        self.assertTrue(normalized["no_execution"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
