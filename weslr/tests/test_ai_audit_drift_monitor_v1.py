#!/usr/bin/env python3
"""Focused tests for WESLR AI audit drift monitor helpers V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_drift_monitor import (  # noqa: E402
    build_ai_audit_drift_monitor_result_v1,
    scan_ai_audit_file_snapshot_for_drift_v1,
    scan_ai_audit_text_for_drift_v1,
    summarize_ai_audit_drift_boundaries_v1,
    validate_ai_audit_drift_monitor_result_v1,
)


class AIAuditDriftMonitorV1Tests(unittest.TestCase):
    def signal_types(self, text):
        return {signal["signal_type"] for signal in scan_ai_audit_text_for_drift_v1(text, source_ref="test")}

    def test_01_text_scan_detects_runner_drift(self):
        self.assertIn("runner_drift", self.signal_types("Create a runner to execute probes with live probing."))

    def test_02_text_scan_detects_scoring_drift(self):
        types = self.signal_types("Add a scoring engine with automated grading and an official score.")
        self.assertIn("scoring_drift", types)

    def test_03_text_scan_detects_certification_and_official_benchmark_drift(self):
        types = self.signal_types("Publish certified official benchmark result language.")
        self.assertIn("certification_claim_drift", types)
        self.assertIn("official_benchmark_claim_drift", types)

    def test_04_text_scan_detects_answer_key_and_hidden_prompt_drift(self):
        types = self.signal_types("Use an answer_key and hidden_prompt for the audit.")
        self.assertIn("answer_key_drift", types)
        self.assertIn("hidden_prompt_drift", types)

    def test_05_text_scan_detects_auto_approval_and_truth_promotion_drift(self):
        types = self.signal_types("Automatically approve results and promote to truth.")
        self.assertIn("auto_approval_drift", types)
        self.assertIn("truth_promotion_drift", types)

    def test_06_safe_ai_audit_canon_text_produces_no_high_severity_drift(self):
        text = "AI audit findings are evidence containers, not final truth. Plans are dry preparation artifacts, not executable workflows."
        signals = scan_ai_audit_text_for_drift_v1(text, source_ref="safe_canon")
        self.assertFalse([signal for signal in signals if signal["severity"] == "high"])

    def test_07_file_snapshot_scan_groups_signals_by_path(self):
        result = scan_ai_audit_file_snapshot_for_drift_v1([
            {"path": "a.md", "content": "create probe runner"},
            {"path": "b.md", "content": "safe dry review only"},
        ])
        self.assertIn("a.md", result["signals_by_source_ref"])
        self.assertIn("b.md", result["signals_by_source_ref"])
        self.assertGreater(len(result["signals_by_source_ref"]["a.md"]), 0)
        self.assertEqual([], result["signals_by_source_ref"]["b.md"])
        self.assertFalse(result["filesystem_walk_performed"])

    def test_08_summary_counts_signal_types_and_severity(self):
        signals = scan_ai_audit_text_for_drift_v1("runner and scoring engine and certified", source_ref="summary")
        summary = summarize_ai_audit_drift_boundaries_v1(signals)
        self.assertEqual(len(signals), summary["total_signals"])
        self.assertIn("runner_drift", summary["counts_by_signal_type"])
        self.assertIn("high", summary["counts_by_severity"])
        self.assertEqual("high", summary["highest_severity"])

    def test_09_full_drift_monitor_result_combines_signals_and_summary(self):
        result = build_ai_audit_drift_monitor_result_v1(
            texts=[{"source_ref": "inline", "text": "auto approve audit findings"}],
            file_snapshots=[{"path": "audit.md", "content": "write to .weslr"}],
        )
        self.assertEqual("ai_audit_drift_monitor_result_v1", result["schema_version"])
        self.assertGreaterEqual(result["signal_count"], 2)
        self.assertEqual(result["signal_count"], result["boundary_summary"]["total_signals"])
        self.assertTrue(result["in_memory_only"])

    def test_10_validation_accepts_safe_drift_result(self):
        result = build_ai_audit_drift_monitor_result_v1(texts=["safe dry review only"])
        validation = validate_ai_audit_drift_monitor_result_v1(result)
        self.assertTrue(validation["valid"], validation["issues"])
        self.assertEqual([], validation["issues"])

    def test_11_validation_rejects_injected_executable_or_runnable_marker(self):
        result = build_ai_audit_drift_monitor_result_v1()
        result["executable"] = True
        result["runnable"] = True
        validation = validate_ai_audit_drift_monitor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden drift monitor true marker: drift_monitor.executable", validation["issues"])
        self.assertIn("forbidden drift monitor true marker: drift_monitor.runnable", validation["issues"])

    def test_12_validation_rejects_injected_score_or_official_score_fields(self):
        result = build_ai_audit_drift_monitor_result_v1()
        result["score"] = 1
        result["official_score"] = 100
        validation = validate_ai_audit_drift_monitor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden drift monitor field: drift_monitor.score", validation["issues"])
        self.assertIn("forbidden drift monitor field: drift_monitor.official_score", validation["issues"])

    def test_13_validation_rejects_injected_answer_key_or_hidden_prompt_fields(self):
        result = build_ai_audit_drift_monitor_result_v1()
        result["answer_key"] = "not allowed"
        result["hidden_prompt"] = "not allowed"
        validation = validate_ai_audit_drift_monitor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden drift monitor field: drift_monitor.answer_key", validation["issues"])
        self.assertIn("forbidden drift monitor field: drift_monitor.hidden_prompt", validation["issues"])

    def test_14_validation_rejects_auto_approval_or_truth_promotion_authorization(self):
        result = build_ai_audit_drift_monitor_result_v1()
        result["automatic_approval"] = True
        result["truth_promotion"] = True
        validation = validate_ai_audit_drift_monitor_result_v1(result)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden drift monitor true marker: drift_monitor.automatic_approval", validation["issues"])
        self.assertIn("forbidden drift monitor true marker: drift_monitor.truth_promotion", validation["issues"])

    def test_15_helpers_do_not_mutate_inputs(self):
        snapshots = [{"path": "a.md", "content": "create runner"}]
        texts = [{"source_ref": "inline", "text": "official score"}]
        snapshots_before = [dict(item) for item in snapshots]
        texts_before = [dict(item) for item in texts]
        result = build_ai_audit_drift_monitor_result_v1(file_snapshots=snapshots, texts=texts)
        result["signal_count"] = -1
        self.assertEqual(snapshots_before, snapshots)
        self.assertEqual(texts_before, texts)

    def test_16_helpers_do_not_create_runtime_state_or_files(self):
        build_ai_audit_drift_monitor_result_v1(texts=["safe dry review only"])
        self.assertFalse((ROOT / ".weslr" / "ai_audit_drift_monitor.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_drift_monitor.md").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_drift_monitor.jsonl").exists())

    def test_17_no_persistence_file_creation_by_default(self):
        before = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        build_ai_audit_drift_monitor_result_v1(texts=["safe dry review only"])
        after = set((ROOT / ".weslr").glob("*") if (ROOT / ".weslr").exists() else [])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
