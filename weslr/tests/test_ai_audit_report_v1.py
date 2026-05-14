#!/usr/bin/env python3
"""Focused tests for WESLR AI audit redacted report helpers V1."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_report import (  # noqa: E402
    build_ai_audit_redacted_report_v1,
    render_ai_audit_redacted_report_markdown_v1,
    to_ai_audit_redacted_report_json_safe_v1,
    validate_ai_audit_redacted_report_v1,
)
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402


class AIAuditReportV1Tests(unittest.TestCase):
    def packet(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_target_redacted", target_kind="assistant")
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
        return build_ai_audit_review_packet_v1(plan, findings)

    def test_01_build_redacted_report_from_valid_packet(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        self.assertTrue(report["report_id"].startswith("weslr_ai_audit_redacted_report_v1_"))
        self.assertEqual(2, report["total_selected_probes"])
        self.assertEqual(2, report["total_findings"])
        self.assertTrue(report["disclaimer"]["non_official"])
        self.assertFalse(report["executable"])

    def test_02_markdown_rendering_includes_expected_safe_sections(self):
        markdown = render_ai_audit_redacted_report_markdown_v1(build_ai_audit_redacted_report_v1(self.packet()))
        for section in (
            "# AI Audit Review Report",
            "## Target",
            "## Scope",
            "## Findings Summary",
            "## Safety / Boundary Notes",
            "## Operator Review Status",
            "## Disclaimer",
        ):
            self.assertIn(section, markdown)

    def test_03_markdown_rendering_does_not_expose_reviewer_notes(self):
        markdown = render_ai_audit_redacted_report_markdown_v1(build_ai_audit_redacted_report_v1(self.packet()))
        self.assertNotIn("sensitive reviewer note", markdown.lower())
        self.assertNotIn("reviewer_notes", markdown)

    def test_04_markdown_rendering_avoids_answer_keys_and_official_scores(self):
        markdown = render_ai_audit_redacted_report_markdown_v1(build_ai_audit_redacted_report_v1(self.packet()))
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("official_score", markdown)
        self.assertNotIn("official score", markdown.lower())

    def test_05_validation_accepts_safe_report(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        result = validate_ai_audit_redacted_report_v1(report)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["issues"])

    def test_06_validation_rejects_executable_marker(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        report["executable"] = True
        result = validate_ai_audit_redacted_report_v1(report)
        self.assertFalse(result["valid"])
        self.assertIn("report executable must be False", result["issues"])

    def test_07_validation_rejects_answer_key_or_official_score_fields(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        report["answer_key"] = "not allowed"
        report["official_score"] = 100
        result = validate_ai_audit_redacted_report_v1(report)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden report field: report.answer_key", result["issues"])
        self.assertIn("forbidden report field: report.official_score", result["issues"])

    def test_08_validation_rejects_certification_or_official_benchmark_fields(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        report["certification"] = "certified"
        report["official_benchmark_result"] = "passed"
        result = validate_ai_audit_redacted_report_v1(report)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden report field: report.certification", result["issues"])
        self.assertIn("forbidden report field: report.official_benchmark_result", result["issues"])

    def test_09_json_safe_helper_returns_serializable_dict(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        report["answer_key"] = "remove me"
        safe = to_ai_audit_redacted_report_json_safe_v1(report)
        self.assertNotIn("answer_key", safe)
        json.dumps(safe, sort_keys=True)

    def test_10_helpers_do_not_mutate_input_packet(self):
        packet = self.packet()
        before = dict(packet)
        report = build_ai_audit_redacted_report_v1(packet)
        report["packet_id"] = "mutated"
        self.assertEqual(before, packet)

    def test_11_helpers_do_not_create_runtime_state_or_files(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        render_ai_audit_redacted_report_markdown_v1(report)
        self.assertFalse(report["report_persistence"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_report.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_report.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_report.jsonl").exists())

    def test_12_validation_rejects_raw_reviewer_notes_if_injected(self):
        report = build_ai_audit_redacted_report_v1(self.packet())
        report["reviewer_notes"] = "raw notes are not allowed"
        result = validate_ai_audit_redacted_report_v1(report)
        self.assertFalse(result["valid"])
        self.assertIn("forbidden report field: report.reviewer_notes", result["issues"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
