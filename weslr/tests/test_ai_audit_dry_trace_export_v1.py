#!/usr/bin/env python3
"""Focused tests for WESLR AI audit dry trace export helpers V1."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_dry_trace_export import (  # noqa: E402
    build_ai_audit_dry_trace_v1,
    render_ai_audit_dry_trace_markdown_v1,
    summarize_ai_audit_dry_trace_v1,
    to_ai_audit_dry_trace_json_safe_v1,
    validate_ai_audit_dry_trace_v1,
)
from weslr.ai_audit_findings import create_ai_audit_finding_v1  # noqa: E402
from weslr.ai_audit_operator_review_surface import build_ai_audit_operator_review_card_v1  # noqa: E402
from weslr.ai_audit_plan import build_ai_audit_plan_v1, create_ai_audit_target_descriptor_v1  # noqa: E402
from weslr.ai_audit_preflight_review import build_ai_audit_preflight_review_v1  # noqa: E402
from weslr.ai_audit_readiness_gap_advisor import build_ai_audit_readiness_gap_advisor_result_v1  # noqa: E402
from weslr.ai_audit_report import build_ai_audit_redacted_report_v1  # noqa: E402
from weslr.ai_audit_review_packet import build_ai_audit_review_packet_v1  # noqa: E402
from weslr.ai_audit_safe_next_step_recommender import build_ai_audit_safe_next_step_recommendation_result_v1  # noqa: E402
from weslr.ai_audit_self_governance_surface import build_ai_audit_self_governance_card_v1  # noqa: E402


class AIAuditDryTraceExportV1Tests(unittest.TestCase):
    def bundle(self):
        target = create_ai_audit_target_descriptor_v1(target_name="synthetic_trace_target", target_kind="assistant")
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
        surface = build_ai_audit_self_governance_card_v1(
            readiness_gap_advisor_result=readiness,
            consistency_review_result=preflight["consistency_result"],
            drift_monitor_result=preflight["drift_result"],
            preflight_review_result=preflight,
        )
        recommendation = build_ai_audit_safe_next_step_recommendation_result_v1(
            self_governance_card=surface,
            preflight_review_result=preflight,
            readiness_gap_advisor_result=readiness,
        )
        return readiness, preflight, surface, recommendation

    def test_01_trace_builds_from_safe_self_governance_preflight_recommendation_inputs(self):
        readiness, preflight, surface, recommendation = self.bundle()
        trace = build_ai_audit_dry_trace_v1(
            readiness_gap_advisor_result=readiness,
            preflight_review_result=preflight,
            self_governance_card_or_overview=surface,
            safe_next_step_recommendation_result=recommendation,
        )
        self.assertEqual("ai_audit_dry_trace_v1", trace["schema_version"])
        self.assertEqual("non_executing_dry_trace_only", trace["execution_status"])
        self.assertGreaterEqual(len(trace["trace_events"]), 6)

    def test_02_trace_events_are_redacted_and_non_executing(self):
        readiness, preflight, surface, recommendation = self.bundle()
        trace = build_ai_audit_dry_trace_v1(readiness_gap_advisor_result=readiness, preflight_review_result=preflight, self_governance_card_or_overview=surface, safe_next_step_recommendation_result=recommendation)
        for event in trace["trace_events"]:
            self.assertEqual("redacted", event["redaction_status"])
            self.assertEqual("non_executing_trace_event_only", event["execution_status"])
            self.assertTrue(event["not_a_runner"])
            self.assertTrue(event["no_model_calls"])

    def test_03_summary_contains_expected_source_layers_and_final_recommendation(self):
        readiness, preflight, surface, recommendation = self.bundle()
        trace = build_ai_audit_dry_trace_v1(readiness_gap_advisor_result=readiness, preflight_review_result=preflight, self_governance_card_or_overview=surface, safe_next_step_recommendation_result=recommendation)
        summary = summarize_ai_audit_dry_trace_v1(trace)
        for layer in ("readiness_gap_advisor", "consistency_review", "drift_monitor", "preflight_review", "self_governance_surface", "safe_next_step_recommender"):
            self.assertIn(layer, summary["source_layers_present"])
        self.assertIn("safe_next_step", summary["final_recommendation"])
        self.assertTrue(summary["validation_status"]["valid"])

    def test_04_markdown_includes_safe_sections(self):
        trace = build_ai_audit_dry_trace_v1()
        markdown = render_ai_audit_dry_trace_markdown_v1(trace)
        for section in ("# AI Audit Dry Trace", "## Inputs Considered", "## Readiness", "## Consistency", "## Drift", "## Preflight", "## Self-Governance Surface", "## Safe Next-Step Recommendation", "## Safety Boundaries", "## Forbidden Next Steps", "## Non-Execution Disclaimer"):
            self.assertIn(section, markdown)

    def test_05_markdown_excludes_forbidden_content(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["forbidden_next_steps"].append("inspect_answer_key_hidden_prompt_official_score_certification")
        markdown = render_ai_audit_dry_trace_markdown_v1(trace).lower()
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("hidden_prompt", markdown)
        self.assertNotIn("official_score", markdown)
        self.assertNotIn("certification", markdown)
        self.assertNotIn("execute probes", markdown)
        self.assertNotIn("run probes", markdown)

    def test_06_json_safe_export_is_serializable_and_redacted(self):
        trace = build_ai_audit_dry_trace_v1()
        exported = to_ai_audit_dry_trace_json_safe_v1(trace)
        json.dumps(exported, sort_keys=True)
        self.assertTrue(exported["json_safe_export"])
        self.assertFalse(exported["files_written"])
        self.assertTrue(all(event["redaction_status"] == "redacted" for event in exported["trace_events"]))

    def test_07_validation_accepts_safe_trace(self):
        trace = build_ai_audit_dry_trace_v1()
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertTrue(validation["valid"], validation["issues"])

    def test_08_validation_rejects_executable_or_runnable_marker(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["executable"] = True
        trace["runnable"] = True
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden dry trace true marker: trace.executable", validation["issues"])
        self.assertIn("forbidden dry trace true marker: trace.runnable", validation["issues"])

    def test_09_validation_rejects_score_or_official_score_fields(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["score"] = 1
        trace["official_score"] = 100
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden dry trace field: trace.score", validation["issues"])
        self.assertIn("forbidden dry trace field: trace.official_score", validation["issues"])

    def test_10_validation_rejects_answer_key_or_hidden_prompt_fields(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["answer_key"] = "not allowed"
        trace["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden dry trace field: trace.answer_key", validation["issues"])
        self.assertIn("forbidden dry trace field: trace.hidden_prompt", validation["issues"])

    def test_11_validation_rejects_auto_approval_truth_promotion_auto_implementation(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["automatic_approval"] = True
        trace["truth_promotion"] = True
        trace["automatic_implementation"] = True
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden dry trace true marker: trace.automatic_approval", validation["issues"])
        self.assertIn("forbidden dry trace true marker: trace.truth_promotion", validation["issues"])
        self.assertIn("forbidden dry trace true marker: trace.automatic_implementation", validation["issues"])

    def test_12_validation_rejects_recommendation_implying_runner_grading_external_probing_authorized(self):
        trace = build_ai_audit_dry_trace_v1()
        trace["final_recommendation_summary"]["safe_next_step"] = "authorize runner and external probing"
        validation = validate_ai_audit_dry_trace_v1(trace)
        self.assertFalse(validation["valid"])
        self.assertIn("dry trace recommendation must not imply runner/scoring/external probing is authorized", validation["issues"])

    def test_13_helpers_do_not_mutate_inputs(self):
        readiness, preflight, surface, recommendation = self.bundle()
        readiness_before = dict(readiness)
        preflight_before = dict(preflight)
        surface_before = dict(surface)
        recommendation_before = dict(recommendation)
        trace = build_ai_audit_dry_trace_v1(readiness_gap_advisor_result=readiness, preflight_review_result=preflight, self_governance_card_or_overview=surface, safe_next_step_recommendation_result=recommendation)
        trace["final_recommendation_summary"]["safe_next_step"] = "mutated"
        self.assertEqual(readiness_before, readiness)
        self.assertEqual(preflight_before, preflight)
        self.assertEqual(surface_before, surface)
        self.assertEqual(recommendation_before, recommendation)

    def test_14_helpers_do_not_create_weslr_runtime_state(self):
        build_ai_audit_dry_trace_v1()
        self.assertFalse((ROOT / ".weslr" / "ai_audit_dry_trace.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_dry_trace.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_dry_trace.jsonl").exists())

    def test_15_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        trace = build_ai_audit_dry_trace_v1()
        summarize_ai_audit_dry_trace_v1(trace)
        render_ai_audit_dry_trace_markdown_v1(trace)
        to_ai_audit_dry_trace_json_safe_v1(trace)
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
