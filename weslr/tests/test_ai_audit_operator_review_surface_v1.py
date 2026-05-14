#!/usr/bin/env python3
"""Focused tests for WESLR AI audit operator review surface helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_operator_review_surface import (  # noqa: E402
    build_ai_audit_operator_review_card_v1,
    build_ai_audit_operator_review_list_v1,
    filter_ai_audit_operator_review_cards_v1,
    render_ai_audit_operator_review_surface_markdown_v1,
    validate_ai_audit_operator_review_card_v1,
)
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1, set_ai_audit_review_packet_decision_v1  # noqa: E402


class AIAuditOperatorReviewSurfaceV1Tests(unittest.TestCase):
    def packet(self, target_name="synthetic_target_redacted", decision="none"):
        target = create_ai_audit_target_descriptor_v1(target_name=target_name, target_kind="assistant")
        plan = build_ai_audit_plan_v1(target=target, limit=2)["plan"]
        findings = [
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][0],
                target_name=plan["target"]["target_name"],
                finding_type="provenance_honesty",
                verdict="supported",
                reviewer_notes="sensitive reviewer note should not appear",
            ),
            create_ai_audit_finding_v1(
                plan_id=plan["plan_id"],
                probe_id=plan["selected_probe_ids"][1],
                target_name=plan["target"]["target_name"],
                finding_type="calibration",
                verdict="needs_more_evidence",
                reviewer_notes="another sensitive note",
            ),
        ]
        packet = build_ai_audit_review_packet_v1(plan, findings)
        if decision != "none":
            packet = set_ai_audit_review_packet_decision_v1(packet, decision)
        return packet

    def test_01_build_card_from_safe_review_packet(self):
        card = build_ai_audit_operator_review_card_v1(self.packet())
        self.assertTrue(card["card_id"].startswith("weslr_ai_audit_review_card_v1_"))
        self.assertEqual("review_packet", card["source_type"])
        self.assertEqual(2, card["total_probes"])
        self.assertEqual(2, card["total_findings"])
        self.assertFalse(card["executable"])

    def test_02_build_card_from_safe_redacted_report(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        card = build_ai_audit_operator_review_card_v1(report)
        self.assertEqual("redacted_report", card["source_type"])
        self.assertEqual(report["report_id"], card["report_id"])
        self.assertEqual(2, card["total_findings"])

    def test_03_review_list_is_deterministic(self):
        items = [self.packet("target_b"), self.packet("target_a")]
        first = build_ai_audit_operator_review_list_v1(items)
        second = build_ai_audit_operator_review_list_v1(list(reversed(items)))
        self.assertEqual([c["card_id"] for c in first["cards"]], [c["card_id"] for c in second["cards"]])
        self.assertEqual(["target_a", "target_b"], [c["target_name"] for c in first["cards"]])

    def test_04_filtering_by_operator_status_works(self):
        cards = build_ai_audit_operator_review_list_v1([self.packet(decision="needs_more_evidence"), self.packet("target_pending")])["cards"]
        reviewed = filter_ai_audit_operator_review_cards_v1(cards, operator_review_status="reviewed")
        self.assertEqual(1, len(reviewed))
        self.assertEqual("needs_more_evidence", reviewed[0]["operator_decision"])

    def test_05_filtering_by_validation_and_safety_status_works(self):
        cards = build_ai_audit_operator_review_list_v1([self.packet()])["cards"]
        selected = filter_ai_audit_operator_review_cards_v1(cards, validation_status="valid", safety_status="safe_review_packet", min_findings=2)
        self.assertEqual(1, len(selected))

    def test_06_markdown_render_includes_safe_overview_sections(self):
        review_list = build_ai_audit_operator_review_list_v1([self.packet()])
        markdown = render_ai_audit_operator_review_surface_markdown_v1(review_list)
        for section in ("# AI Audit Operator Review Surface", "## Summary", "## Cards", "## Safety Boundaries", "## Non-execution Disclaimer"):
            self.assertIn(section, markdown)

    def test_07_markdown_render_does_not_expose_reviewer_notes(self):
        markdown = render_ai_audit_operator_review_surface_markdown_v1(build_ai_audit_operator_review_list_v1([self.packet()]))
        self.assertNotIn("sensitive reviewer note", markdown.lower())
        self.assertNotIn("reviewer_notes", markdown)

    def test_08_validation_accepts_safe_cards(self):
        card = build_ai_audit_operator_review_card_v1(self.packet())
        result = validate_ai_audit_operator_review_card_v1(card)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["issues"])

    def test_09_validation_rejects_executable_marker(self):
        card = build_ai_audit_operator_review_card_v1(self.packet())
        card["executable"] = True
        card["execution_status"] = "run_now"
        result = validate_ai_audit_operator_review_card_v1(card)
        self.assertFalse(result["valid"])
        self.assertIn("card executable must be False", result["issues"])
        self.assertIn("card execution_status must be dry_review_only or not_executable", result["issues"])

    def test_10_validation_rejects_answer_key_or_official_score_fields(self):
        card = build_ai_audit_operator_review_card_v1(self.packet())
        card["answer_key"] = "not allowed"
        card["official_score"] = 100
        result = validate_ai_audit_operator_review_card_v1(card)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden review card field: card.answer_key", result["issues"])
        self.assertIn("forbidden review card field: card.official_score", result["issues"])

    def test_11_validation_rejects_certification_or_official_benchmark_claim_fields(self):
        card = build_ai_audit_operator_review_card_v1(self.packet())
        card["certification"] = "certified"
        card["official_benchmark_result"] = "passed"
        result = validate_ai_audit_operator_review_card_v1(card)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden review card field: card.certification", result["issues"])
        self.assertIn("forbidden review card field: card.official_benchmark_result", result["issues"])

    def test_12_helpers_do_not_mutate_inputs(self):
        packet = self.packet()
        report = build_ai_audit_redacted_report_v1(packet)
        packet_before = dict(packet)
        report_before = dict(report)
        card = build_ai_audit_operator_review_card_v1(packet)
        review_list = build_ai_audit_operator_review_list_v1([report, card])
        review_list["cards"][0]["card_id"] = "mutated"
        self.assertEqual(packet_before, packet)
        self.assertEqual(report_before, report)

    def test_13_helpers_do_not_create_runtime_state_or_files(self):
        review_list = build_ai_audit_operator_review_list_v1([self.packet()])
        render_ai_audit_operator_review_surface_markdown_v1(review_list)
        self.assertTrue(review_list["in_memory_only"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_operator_review_surface.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_operator_review_surface.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_operator_review_surface.jsonl").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
