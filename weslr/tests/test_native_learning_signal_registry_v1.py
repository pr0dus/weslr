#!/usr/bin/env python3
"""Focused tests for WESLR native learning signal registry helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_learning_signal_registry import (  # noqa: E402
    REGISTRY_EXECUTION_STATUS_V1,
    SIGNAL_EXECUTION_STATUS_V1,
    build_native_learning_signal_registry_v1,
    create_native_learning_signal_v1,
    normalize_native_learning_signal_v1,
    render_native_learning_signal_registry_markdown_v1,
    summarize_native_learning_signal_registry_v1,
    to_native_learning_signal_registry_json_safe_v1,
    validate_native_learning_signal_registry_v1,
    validate_native_learning_signal_v1,
)


def weslr_state_snapshot():
    state_dir = ROOT / ".weslr"
    if not state_dir.exists():
        return []
    return sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*"))


class NativeLearningSignalRegistryV1Tests(unittest.TestCase):
    def safe_signal(self, **overrides):
        data = {
            "signal_family": "shadow_review_signal",
            "source_layer": "frontier_shadow_review",
            "source_ref": "review_123",
            "provenance_refs": ["operator_supplied_checkpoint", "shadow_review:review_123"],
            "recurrence_key": "generic_response_boundary",
            "confidence_label": "provisional",
            "suggested_investigation": "inspect recurring generic response pattern",
        }
        data.update(overrides)
        return create_native_learning_signal_v1(**data)

    def test_01_creates_valid_learning_signal(self):
        signal = self.safe_signal()
        self.assertEqual("native_learning_signal_v1", signal["signal_type"])
        self.assertTrue(signal["signal_id"])
        self.assertEqual("shadow_review_signal", signal["signal_family"])
        self.assertEqual(SIGNAL_EXECUTION_STATUS_V1, signal["execution_status"])
        self.assertTrue(validate_native_learning_signal_v1(signal)["valid"])

    def test_02_signal_is_marked_signal_only_not_truth_not_proposal_not_approval_not_implementation(self):
        status = self.safe_signal()["learning_status"]
        self.assertTrue(status["signal_only"])
        self.assertTrue(status["not_truth"])
        self.assertTrue(status["not_proposal"])
        self.assertTrue(status["not_approval"])
        self.assertTrue(status["not_implementation"])

    def test_03_normalizes_raw_shadow_review_signal_safely(self):
        raw = {
            "signal_family": "shadow_review_signal",
            "source_layer": "frontier_shadow_review",
            "source_ref": "review_abc",
            "provenance_refs": ["review_abc"],
            "suggested_investigation": "candidate surfaced missing context boundary",
        }
        normalized = normalize_native_learning_signal_v1(raw)
        self.assertEqual("shadow_review_signal", normalized["signal_family"])
        self.assertEqual("frontier_shadow_review", normalized["source_layer"])
        self.assertEqual(SIGNAL_EXECUTION_STATUS_V1, normalized["execution_status"])
        self.assertTrue(validate_native_learning_signal_v1(normalized)["valid"])

    def test_04_normalizes_self_check_issue_signal_safely(self):
        normalized = normalize_native_learning_signal_v1({
            "signal_family": "self_check_issue_signal",
            "source_layer": "native_response_self_check",
            "source_ref": "issue_1",
            "evidence_status": "requires_review_not_truth",
        })
        self.assertEqual("self_check_issue_signal", normalized["signal_family"])
        self.assertTrue(validate_native_learning_signal_v1(normalized)["valid"])

    def test_05_normalizes_drift_and_readiness_gap_signals_safely(self):
        drift = normalize_native_learning_signal_v1({"signal_family": "drift_signal", "source_layer": "audit", "source_ref": "drift_1"})
        gap = normalize_native_learning_signal_v1({"signal_family": "readiness_gap_signal", "source_layer": "release_gate", "source_ref": "gap_1"})
        self.assertEqual("drift_signal", drift["signal_family"])
        self.assertEqual("readiness_gap_signal", gap["signal_family"])
        self.assertTrue(validate_native_learning_signal_v1(drift)["valid"])
        self.assertTrue(validate_native_learning_signal_v1(gap)["valid"])

    def test_06_normalize_drops_raw_private_text_without_mutating_input(self):
        raw = {"signal_family": "user_correction_signal", "source_layer": "chat", "source_ref": "msg_1", "raw_private_text": "secret private payload"}
        original = copy.deepcopy(raw)
        normalized = normalize_native_learning_signal_v1(raw)
        self.assertEqual(original, raw)
        encoded = json.dumps(normalized, sort_keys=True)
        self.assertNotIn("secret private payload", encoded)
        self.assertNotIn("do not store", encoded)
        self.assertEqual("forbidden_fields_dropped", normalized["redaction_status"])

    def test_07_validation_rejects_raw_private_text(self):
        unsafe = self.safe_signal()
        unsafe["raw_private_text"] = "do not store"
        result = validate_native_learning_signal_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("raw_private_text", {v["category"] for v in result["violations"]})

    def test_08_drops_or_rejects_hidden_prompt(self):
        raw = {"signal_family": "self_check_issue_signal", "source_layer": "self_check", "source_ref": "x", "hidden_prompt": "system secret"}
        normalized = normalize_native_learning_signal_v1(raw)
        self.assertNotIn("system secret", json.dumps(normalized, sort_keys=True))
        unsafe = self.safe_signal()
        unsafe["hidden_prompt"] = "system secret"
        result = validate_native_learning_signal_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("hidden_prompt", {v["category"] for v in result["violations"]})

    def test_09_drops_or_rejects_answer_key(self):
        raw = {"signal_family": "evidence_boundary_signal", "source_layer": "review", "source_ref": "x", "answer_key": {"q": "a"}}
        normalized = normalize_native_learning_signal_v1(raw)
        self.assertNotIn('"q": "a"', json.dumps(normalized, sort_keys=True))
        unsafe = self.safe_signal()
        unsafe["answer_key"] = {"q": "a"}
        result = validate_native_learning_signal_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("answer_key_or_benchmark_answer", {v["category"] for v in result["violations"]})

    def test_10_drops_or_rejects_protected_item(self):
        raw = {"signal_family": "evidence_boundary_signal", "source_layer": "review", "source_ref": "x", "protected_item": "protected test item text"}
        normalized = normalize_native_learning_signal_v1(raw)
        self.assertNotIn("protected test item text", json.dumps(normalized, sort_keys=True))
        unsafe = self.safe_signal()
        unsafe["protected_item"] = "protected test item text"
        result = validate_native_learning_signal_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_material", {v["category"] for v in result["violations"]})

    def test_11_rejects_official_score_iq_score_certification_claim(self):
        for key in ["official_score", "iq_score", "certification_claim"]:
            unsafe = self.safe_signal()
            unsafe[key] = "unsafe claim"
            result = validate_native_learning_signal_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_12_rejects_model_weight_update_and_fine_tune_payload(self):
        for key in ["model_weight_update", "fine_tune_payload"]:
            unsafe = self.safe_signal()
            unsafe[key] = {"payload": "not allowed"}
            result = validate_native_learning_signal_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("model_training_or_fine_tuning", {v["category"] for v in result["violations"]})

    def test_13_rejects_auto_approval_and_auto_implementation(self):
        for key in ["auto_approval", "auto_implementation"]:
            unsafe = self.safe_signal()
            unsafe[key] = True
            result = validate_native_learning_signal_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_14_rejects_runtime_write_and_persistence_target(self):
        for key in ["runtime_write", "persistence_target"]:
            unsafe = self.safe_signal()
            unsafe[key] = True
            result = validate_native_learning_signal_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_15_builds_registry_from_multiple_safe_signals(self):
        registry = build_native_learning_signal_registry_v1([
            self.safe_signal(signal_id="sig_a"),
            self.safe_signal(signal_id="sig_b", signal_family="missing_context_signal", recurrence_key="missing_project_state"),
        ])
        self.assertEqual("native_learning_signal_registry_v1", registry["registry_type"])
        self.assertEqual(2, registry["total_signals"])
        self.assertEqual(2, registry["valid_signal_count"])
        self.assertEqual(REGISTRY_EXECUTION_STATUS_V1, registry["execution_status"])

    def test_16_groups_by_recurrence_key(self):
        registry = build_native_learning_signal_registry_v1([
            self.safe_signal(signal_id="sig_a", recurrence_key="same_gap"),
            self.safe_signal(signal_id="sig_b", signal_family="missing_context_signal", recurrence_key="same_gap"),
        ])
        self.assertEqual(["sig_a", "sig_b"], registry["groups_by_recurrence_key"]["same_gap"])

    def test_17_groups_by_signal_family_and_source_layer(self):
        registry = build_native_learning_signal_registry_v1([
            self.safe_signal(signal_id="sig_a", signal_family="shadow_review_signal", source_layer="shadow"),
            self.safe_signal(signal_id="sig_b", signal_family="drift_signal", source_layer="audit"),
        ])
        self.assertEqual(["sig_a"], registry["groups_by_signal_family"]["shadow_review_signal"])
        self.assertEqual(["sig_b"], registry["groups_by_source_layer"]["audit"])

    def test_18_detects_duplicate_signal_ids(self):
        registry = build_native_learning_signal_registry_v1([
            self.safe_signal(signal_id="dup"),
            self.safe_signal(signal_id="dup", signal_family="drift_signal"),
        ])
        self.assertEqual(["dup"], registry["duplicate_signal_ids"])
        validation = validate_native_learning_signal_registry_v1(registry)
        self.assertFalse(validation["valid"])
        self.assertIn("duplicate_signal_id", {v["category"] for v in validation["violations"]})

    def test_19_summary_is_count_only_and_redacted(self):
        registry = build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
        summary = summarize_native_learning_signal_registry_v1(registry)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertIn("total_signals", summary)
        self.assertNotIn("source_ref", encoded)
        self.assertNotIn("provenance_refs", encoded)
        self.assertNotIn("suggested_investigation", encoded)

    def test_20_json_safe_helper_is_serializable(self):
        registry = build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
        safe = to_native_learning_signal_registry_json_safe_v1(registry)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_learning_signal_registry_v1", encoded)

    def test_21_markdown_renderer_excludes_forbidden_payload_content(self):
        registry = build_native_learning_signal_registry_v1([
            {"signal_family": "user_correction_signal", "source_layer": "chat", "source_ref": "m1", "raw_private_text": "PRIVATE_SECRET", "hidden_prompt": "HIDDEN_SECRET", "answer_key": "ANSWER_SECRET"}
        ])
        markdown = render_native_learning_signal_registry_markdown_v1(registry)
        self.assertIn("Native Learning Signal Registry", markdown)
        self.assertIn("Signal Families", markdown)
        self.assertIn("Source Layers", markdown)
        self.assertIn("Recurrence Groups", markdown)
        self.assertIn("Safety Boundaries", markdown)
        self.assertIn("Non-Learning / Non-Truth Disclaimer", markdown)
        self.assertNotIn("PRIVATE_SECRET", markdown)
        self.assertNotIn("HIDDEN_SECRET", markdown)
        self.assertNotIn("ANSWER_SECRET", markdown)

    def test_22_helpers_do_not_mutate_inputs(self):
        raw = {"signal_family": "drift_signal", "source_layer": "audit", "source_ref": "drift", "provenance_refs": ["a"]}
        original = copy.deepcopy(raw)
        normalize_native_learning_signal_v1(raw)
        build_native_learning_signal_registry_v1([raw])
        self.assertEqual(original, raw)

    def test_23_helpers_do_not_create_weslr_runtime_state_or_files_by_default(self):
        before = weslr_state_snapshot()
        registry = build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
        render_native_learning_signal_registry_markdown_v1(registry)
        to_native_learning_signal_registry_json_safe_v1(registry)
        after = weslr_state_snapshot()
        self.assertEqual(before, after)

    def test_24_no_model_calls_are_made(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
            urlopen.assert_not_called()

    def test_25_no_scoring_or_pass_fail_grading_fields_are_allowed(self):
        for key in ["score", "numeric_score", "grade", "pass_fail", "passed", "failed"]:
            unsafe = self.safe_signal()
            unsafe[key] = 1
            result = validate_native_learning_signal_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("numeric_score_or_pass_fail_grading", {v["category"] for v in result["violations"]})

    def test_26_no_automatic_approval_or_implementation_in_registry(self):
        registry = build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
        unsafe = copy.deepcopy(registry)
        unsafe["auto_approval"] = True
        unsafe["signals"][0]["learning_status"]["not_implementation"] = False
        validation = validate_native_learning_signal_registry_v1(unsafe)
        categories = {v["category"] for v in validation["violations"]}
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden_field", categories)
        self.assertIn("learning_status_drift", categories)

    def test_27_learning_signals_are_not_truth_proposals_approvals_or_implementation(self):
        registry = build_native_learning_signal_registry_v1([self.safe_signal(signal_id="sig_a")])
        signal = registry["signals"][0]
        self.assertTrue(signal["learning_status"]["not_truth"])
        self.assertTrue(signal["learning_status"]["not_proposal"])
        self.assertTrue(signal["learning_status"]["not_approval"])
        self.assertTrue(signal["learning_status"]["not_implementation"])

    def test_28_rejects_fake_memory_fake_self_awareness_and_mystical_claims(self):
        unsafe = self.safe_signal()
        unsafe["suggested_investigation"] = "I remember you personally and this is a fake self-awareness claim with mystical consciousness"
        result = validate_native_learning_signal_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("fake_self_awareness", categories)
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", categories)


if __name__ == "__main__":
    unittest.main()
