#!/usr/bin/env python3
"""Focused tests for WESLR AI audit read-only status bundle helpers V1."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_status_bundle import (  # noqa: E402
    build_ai_audit_status_bundle_v1,
    render_ai_audit_status_bundle_markdown_v1,
    summarize_ai_audit_status_bundle_v1,
    to_ai_audit_status_bundle_json_safe_v1,
    validate_ai_audit_status_bundle_v1,
)


class AIAuditStatusBundleV1Tests(unittest.TestCase):
    def inputs(self):
        readiness = {
            "schema_version": "ai_audit_readiness_gap_advisor_result_v1",
            "gap_count": 2,
            "gap_records": [{"gap_id": "gap-1", "severity": "medium"}, {"gap_id": "gap-2", "severity": "low"}],
            "readiness_report": {"readiness_status": ["operator_review_needed"], "safe_next_steps": ["inspect_readiness_gaps_in_memory_only"]},
        }
        consistency = {
            "schema_version": "ai_audit_consistency_review_v1",
            "consistency_status": "issues_present",
            "total_issues": 1,
            "issues": [{"issue_id": "issue-1", "severity": "low"}],
        }
        drift = {
            "schema_version": "ai_audit_drift_monitor_v1",
            "signal_count": 3,
            "signals": [{"signal_id": "drift-1"}, {"signal_id": "drift-2"}, {"signal_id": "drift-3"}],
            "boundary_summary": {"drift_status": "drift_review_needed", "total_signals": 3},
        }
        preflight = {
            "schema_version": "ai_audit_preflight_review_v1",
            "preflight_id": "preflight-1",
            "recommendation": "review safe helper layer only",
            "forbidden_next_steps": ["call_external_models"],
        }
        card = {
            "schema_version": "ai_audit_self_governance_card_v1",
            "card_id": "card-1",
            "readiness_status": ["operator_review_needed"],
            "consistency_status": "issues_present",
            "drift_status": "drift_review_needed",
            "preflight_recommendation": "review safe helper layer only",
            "total_readiness_gaps": 2,
            "total_consistency_issues": 1,
            "total_drift_signals": 3,
            "forbidden_next_steps": ["add_scoring_engine"],
        }
        overview = {
            "schema_version": "ai_audit_self_governance_overview_v1",
            "overview_id": "overview-1",
            "total_readiness_gaps": 2,
            "total_consistency_issues": 1,
            "total_drift_signals": 3,
        }
        recommendation = {
            "schema_version": "ai_audit_safe_next_step_recommendation_result_v1",
            "recommendation_result_id": "rec-1",
            "top_recommendation": {
                "title": "package read only status bundle",
                "reason": "self governance status should be inspectable before any audit execution",
            },
        }
        dry_trace = {
            "schema_version": "ai_audit_dry_trace_v1",
            "trace_events": [
                {"trace_event_id": "evt-1", "source_layer": "readiness_gap_advisor"},
                {"trace_event_id": "evt-2", "source_layer": "safe_next_step_recommender"},
            ],
        }
        return readiness, consistency, drift, preflight, card, overview, recommendation, dry_trace

    def bundle(self):
        readiness, consistency, drift, preflight, card, overview, recommendation, dry_trace = self.inputs()
        return build_ai_audit_status_bundle_v1(
            readiness_gap_advisor_result=readiness,
            consistency_review_result=consistency,
            drift_monitor_result=drift,
            preflight_review_result=preflight,
            self_governance_surface_card=card,
            self_governance_surface_overview=overview,
            safe_next_step_recommendation_result=recommendation,
            dry_trace=dry_trace,
            canon_refs=["WESLR_AI_AUDIT_CANON_V1"],
        )

    def test_01_bundle_builds_from_safe_self_governance_recommendation_dry_trace_inputs(self):
        bundle = self.bundle()
        self.assertEqual("ai_audit_read_only_status_bundle_v1", bundle["schema_version"])
        self.assertEqual("ai_audit_read_only_status_bundle", bundle["bundle_type"])
        self.assertEqual(["operator_review_needed"], bundle["readiness_status"])
        self.assertEqual("issues_present", bundle["consistency_status"])
        self.assertEqual("drift_review_needed", bundle["drift_status"])
        self.assertEqual("package read only status bundle", bundle["top_safe_next_step"]["recommendation"])
        self.assertEqual(2, bundle["dry_trace_summary"]["total_trace_events"])

    def test_02_bundle_preserves_non_executing_authorization_boundaries(self):
        bundle = self.bundle()
        self.assertEqual("non_executing_status_bundle_only", bundle["execution_status"])
        self.assertTrue(bundle["authorization_status"]["runner_not_authorized"])
        self.assertTrue(bundle["authorization_status"]["scoring_not_authorized"])
        self.assertTrue(bundle["authorization_status"]["external_testing_not_authorized"])
        self.assertTrue(bundle["authorization_status"]["runtime_wiring_not_authorized"])
        self.assertTrue(bundle["authorization_status"]["persistence_not_authorized_by_default"])
        self.assertFalse(bundle["files_written"])
        self.assertFalse(bundle["weslr_runtime_state_created"])

    def test_03_bundle_includes_canon_references_safely(self):
        bundle = self.bundle()
        self.assertIn("WESLR_AI_AUDIT_CANON_V1", bundle["canon_refs"])
        self.assertGreaterEqual(len(bundle["canon_refs"]), 2)
        self.assertTrue(all(isinstance(ref, str) for ref in bundle["canon_refs"]))

    def test_04_summary_is_redacted_count_only(self):
        summary = summarize_ai_audit_status_bundle_v1(self.bundle())
        self.assertTrue(summary["redacted_count_only"])
        self.assertFalse(summary["raw_outputs_included"])
        self.assertEqual(2, summary["total_known_gaps"])
        self.assertEqual(1, summary["total_consistency_issues"])
        self.assertEqual(3, summary["total_drift_signals"])
        self.assertEqual(2, summary["total_trace_events"])
        self.assertTrue(summary["validation_status"]["valid"])

    def test_05_markdown_includes_safe_sections(self):
        markdown = render_ai_audit_status_bundle_markdown_v1(self.bundle())
        for section in (
            "# AI Audit Status Bundle",
            "## Readiness",
            "## Consistency",
            "## Drift",
            "## Preflight",
            "## Recommendation",
            "## Dry Trace Summary",
            "## Canon References",
            "## Safety Boundaries",
            "## Forbidden Next Steps",
            "## Non-Execution Disclaimer",
        ):
            self.assertIn(section, markdown)

    def test_06_markdown_excludes_forbidden_content(self):
        bundle = self.bundle()
        bundle["forbidden_next_steps"].append("inspect_answer_key_hidden_prompt_official_score_certification")
        markdown = render_ai_audit_status_bundle_markdown_v1(bundle).lower()
        self.assertNotIn("answer_key", markdown)
        self.assertNotIn("hidden_prompt", markdown)
        self.assertNotIn("official_score", markdown)
        self.assertNotIn("certification", markdown)
        self.assertNotIn("execute probes", markdown)
        self.assertNotIn("run probes", markdown)
        self.assertNotIn("scoring", markdown)

    def test_07_json_safe_export_is_serializable_and_redacted(self):
        exported = to_ai_audit_status_bundle_json_safe_v1(self.bundle())
        json.dumps(exported, sort_keys=True)
        self.assertTrue(exported["json_safe_export"])
        self.assertFalse(exported["files_written"])
        self.assertFalse(exported["report_persisted"])
        self.assertFalse(exported["raw_outputs_included"])
        self.assertTrue(exported["validation_status"]["valid"])

    def test_08_validation_accepts_safe_bundle(self):
        validation = validate_ai_audit_status_bundle_v1(self.bundle())
        self.assertTrue(validation["valid"], validation["issues"])

    def test_09_validation_rejects_executable_or_runnable_marker(self):
        bundle = self.bundle()
        bundle["executable"] = True
        bundle["runnable"] = True
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden status bundle true marker: bundle.executable", validation["issues"])
        self.assertIn("forbidden status bundle true marker: bundle.runnable", validation["issues"])

    def test_10_validation_rejects_score_or_official_score_fields(self):
        bundle = self.bundle()
        bundle["score"] = 1
        bundle["official_score"] = 100
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden status bundle field: bundle.score", validation["issues"])
        self.assertIn("forbidden status bundle field: bundle.official_score", validation["issues"])

    def test_11_validation_rejects_answer_key_or_hidden_prompt_fields(self):
        bundle = self.bundle()
        bundle["answer_key"] = "not allowed"
        bundle["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden status bundle field: bundle.answer_key", validation["issues"])
        self.assertIn("forbidden status bundle field: bundle.hidden_prompt", validation["issues"])

    def test_12_validation_rejects_auto_approval_truth_promotion_auto_implementation(self):
        bundle = self.bundle()
        bundle["automatic_approval"] = True
        bundle["truth_promotion"] = True
        bundle["automatic_implementation"] = True
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden status bundle true marker: bundle.automatic_approval", validation["issues"])
        self.assertIn("forbidden status bundle true marker: bundle.truth_promotion", validation["issues"])
        self.assertIn("forbidden status bundle true marker: bundle.automatic_implementation", validation["issues"])

    def test_13_validation_rejects_persistence_or_file_writing_authorization(self):
        bundle = self.bundle()
        bundle["persistence_authorized"] = True
        bundle["file_write_authorized"] = True
        bundle["files_written"] = True
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden status bundle true marker: bundle.persistence_authorized", validation["issues"])
        self.assertIn("forbidden status bundle field: bundle.file_write_authorized", validation["issues"])
        self.assertIn("files_written must be False", validation["issues"])

    def test_14_validation_rejects_recommendation_implying_runner_grading_external_probing_authorized(self):
        bundle = self.bundle()
        bundle["top_safe_next_step"]["recommendation"] = "authorize runner and external probing"
        validation = validate_ai_audit_status_bundle_v1(bundle)
        self.assertFalse(validation["valid"])
        self.assertIn("status bundle recommendation must not imply runner/scoring/external probing/persistence is authorized", validation["issues"])

    def test_15_helpers_do_not_mutate_inputs(self):
        inputs = self.inputs()
        before = deepcopy(inputs)
        build_ai_audit_status_bundle_v1(
            readiness_gap_advisor_result=inputs[0],
            consistency_review_result=inputs[1],
            drift_monitor_result=inputs[2],
            preflight_review_result=inputs[3],
            self_governance_surface_card=inputs[4],
            self_governance_surface_overview=inputs[5],
            safe_next_step_recommendation_result=inputs[6],
            dry_trace=inputs[7],
            canon_refs=["WESLR_AI_AUDIT_CANON_V1"],
        )
        self.assertEqual(before, inputs)

    def test_16_helpers_do_not_create_weslr_runtime_state(self):
        build_ai_audit_status_bundle_v1()
        self.assertFalse((ROOT / ".weslr" / "ai_audit_status_bundle.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_status_bundle.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_status_bundle.jsonl").exists())

    def test_17_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        bundle = build_ai_audit_status_bundle_v1()
        summarize_ai_audit_status_bundle_v1(bundle)
        render_ai_audit_status_bundle_markdown_v1(bundle)
        to_ai_audit_status_bundle_json_safe_v1(bundle)
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
