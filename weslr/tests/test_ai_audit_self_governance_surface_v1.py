#!/usr/bin/env python3
"""Focused tests for WESLR AI audit self-governance surface helpers V1."""

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
from weslr.ai_audit_preflight_review import build_ai_audit_preflight_review_v1  # noqa: E402
from weslr.ai_audit_readiness_gap_advisor import build_ai_audit_readiness_gap_advisor_result_v1  # noqa: E402
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402
from weslr.ai_audit_self_governance_surface import (  # noqa: E402
    build_ai_audit_self_governance_card_v1,
    build_ai_audit_self_governance_overview_v1,
    render_ai_audit_self_governance_surface_markdown_v1,
    validate_ai_audit_self_governance_surface_v1,
)


class AIAuditSelfGovernanceSurfaceV1Tests(unittest.TestCase):
    def bundle(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_surface_target", target_kind="assistant")
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
        return readiness, preflight["consistency_result"], preflight["drift_result"], preflight

    def test_01_card_builds_from_safe_preflight_readiness_consistency_drift_results(self):
        readiness, consistency, drift, preflight = self.bundle()
        card = build_ai_audit_self_governance_card_v1(
            readiness_gap_advisor_result=readiness,
            consistency_review_result=consistency,
            drift_monitor_result=drift,
            preflight_review_result=preflight,
        )
        self.assertEqual("ai_audit_self_governance_card_v1", card["schema_version"])
        self.assertEqual("non_executing_surface_only", card["execution_status"])
        self.assertEqual(preflight["recommendation"], card["preflight_recommendation"])
        self.assertEqual(readiness["gap_count"], card["total_readiness_gaps"])
        self.assertEqual(consistency["total_issues"], card["total_consistency_issues"])
        self.assertEqual(drift["signal_count"], card["total_drift_signals"])

    def test_02_card_preserves_non_executing_authorization_boundaries(self):
        card = build_ai_audit_self_governance_card_v1()
        for marker in ("runner_not_authorized", "scoring_not_authorized", "external_testing_not_authorized", "runtime_wiring_not_authorized"):
            self.assertIn(marker, card["authorization_status"])
        self.assertFalse(card["safety_boundaries"]["runner_authorized"])
        self.assertFalse(card["safety_boundaries"]["persistence_authorized"])
        self.assertTrue(card["not_a_runner"])
        self.assertTrue(card["not_a_scoring_engine"])

    def test_03_overview_combines_cards_deterministically(self):
        safe_card = build_ai_audit_self_governance_card_v1()
        drift = build_ai_audit_drift_monitor_result_v1(texts=["create a runner and execute probes"])
        drift_card = build_ai_audit_self_governance_card_v1(drift_monitor_result=drift)
        overview_a = build_ai_audit_self_governance_overview_v1([drift_card, safe_card])
        overview_b = build_ai_audit_self_governance_overview_v1([safe_card, drift_card])
        self.assertEqual([card["card_id"] for card in overview_a["cards"]], [card["card_id"] for card in overview_b["cards"]])
        self.assertEqual(2, overview_a["total_cards"])
        self.assertEqual(drift_card["total_drift_signals"], overview_a["total_drift_signals"])

    def test_04_markdown_renderer_includes_safe_sections(self):
        card = build_ai_audit_self_governance_card_v1()
        markdown = render_ai_audit_self_governance_surface_markdown_v1(card)
        for section in (
            "# AI Audit Self-Governance Surface",
            "## Readiness",
            "## Consistency",
            "## Drift",
            "## Preflight",
            "## Safe Next Steps",
            "## Forbidden Next Steps",
            "## Boundaries",
        ):
            self.assertIn(section, markdown)

    def test_05_markdown_excludes_forbidden_sensitive_or_claim_language(self):
        card = build_ai_audit_self_governance_card_v1()
        card["safe_next_steps"].append("inspect_answer_key_hidden_prompt_official_score_certification")
        markdown = render_ai_audit_self_governance_surface_markdown_v1(card).lower()
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("hidden_prompt", markdown)
        self.assertNotIn("official_score", markdown)
        self.assertNotIn("certification", markdown)
        self.assertNotIn("protected_test_item", markdown)

    def test_06_validation_accepts_safe_surface(self):
        card = build_ai_audit_self_governance_card_v1()
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertTrue(validation["valid"], validation["issues"])

    def test_07_validation_rejects_executable_or_runnable_marker(self):
        card = build_ai_audit_self_governance_card_v1()
        card["executable"] = True
        card["runnable"] = True
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden surface true marker: surface.executable", validation["issues"])
        self.assertIn("forbidden surface true marker: surface.runnable", validation["issues"])

    def test_08_validation_rejects_score_or_official_score_fields(self):
        card = build_ai_audit_self_governance_card_v1()
        card["score"] = 1
        card["official_score"] = 100
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden surface field: surface.score", validation["issues"])
        self.assertIn("forbidden surface field: surface.official_score", validation["issues"])

    def test_09_validation_rejects_answer_key_or_hidden_prompt_fields(self):
        card = build_ai_audit_self_governance_card_v1()
        card["answer_key"] = "not allowed"
        card["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden surface field: surface.answer_key", validation["issues"])
        self.assertIn("forbidden surface field: surface.hidden_prompt", validation["issues"])

    def test_10_validation_rejects_auto_approval_or_truth_promotion(self):
        card = build_ai_audit_self_governance_card_v1()
        card["automatic_approval"] = True
        card["truth_promotion"] = True
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden surface true marker: surface.automatic_approval", validation["issues"])
        self.assertIn("forbidden surface true marker: surface.truth_promotion", validation["issues"])

    def test_11_validation_rejects_recommendation_implying_execution_scoring_external_probing(self):
        card = build_ai_audit_self_governance_card_v1()
        card["preflight_recommendation"] = "execute_probes_with_external_model_scoring"
        validation = validate_ai_audit_self_governance_surface_v1(card)
        self.assertFalse(validation["valid"])
        self.assertIn("surface recommendation must not imply execution/scoring/external probing", validation["issues"])

    def test_12_helpers_do_not_mutate_inputs(self):
        readiness, consistency, drift, preflight = self.bundle()
        readiness_before = dict(readiness)
        consistency_before = dict(consistency)
        drift_before = dict(drift)
        preflight_before = dict(preflight)
        card = build_ai_audit_self_governance_card_v1(
            readiness_gap_advisor_result=readiness,
            consistency_review_result=consistency,
            drift_monitor_result=drift,
            preflight_review_result=preflight,
        )
        card["preflight_recommendation"] = "mutated"
        self.assertEqual(readiness_before, readiness)
        self.assertEqual(consistency_before, consistency)
        self.assertEqual(drift_before, drift)
        self.assertEqual(preflight_before, preflight)

    def test_13_helpers_do_not_create_weslr_runtime_state(self):
        build_ai_audit_self_governance_card_v1()
        build_ai_audit_self_governance_overview_v1([build_ai_audit_self_governance_card_v1()])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_self_governance_surface.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_self_governance_surface.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_self_governance_surface.jsonl").exists())

    def test_14_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        card = build_ai_audit_self_governance_card_v1()
        build_ai_audit_self_governance_overview_v1([card])
        render_ai_audit_self_governance_surface_markdown_v1(card)
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
