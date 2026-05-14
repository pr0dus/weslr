#!/usr/bin/env python3
"""Focused tests for WESLR repeated weakness detector helpers V1."""

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
    build_native_learning_signal_registry_v1,
    create_native_learning_signal_v1,
)
from weslr.repeated_weakness_detector import (  # noqa: E402
    CANDIDATE_EXECUTION_STATUS_V1,
    DETECTOR_EXECUTION_STATUS_V1,
    build_repeated_weakness_detector_result_v1,
    create_repeated_weakness_candidate_v1,
    detect_repeated_weakness_candidates_v1,
    render_repeated_weakness_detector_markdown_v1,
    summarize_repeated_weakness_detector_result_v1,
    to_repeated_weakness_detector_json_safe_v1,
    validate_repeated_weakness_candidate_v1,
    validate_repeated_weakness_detector_result_v1,
)


def weslr_state_snapshot():
    state_dir = ROOT / ".weslr"
    if not state_dir.exists():
        return []
    return sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*"))


class RepeatedWeaknessDetectorV1Tests(unittest.TestCase):
    def signal(self, signal_id="sig_a", recurrence_key="same_gap", signal_family="generic_response_signal", source_layer="shadow", **overrides):
        data = {
            "signal_id": signal_id,
            "signal_family": signal_family,
            "source_layer": source_layer,
            "source_ref": f"ref_{signal_id}",
            "provenance_refs": [f"prov_{signal_id}"],
            "recurrence_key": recurrence_key,
            "confidence_label": "provisional",
            "suggested_investigation": "review repeated safe signal",
        }
        data.update(overrides)
        return create_native_learning_signal_v1(**data)

    def registry(self, signals):
        return build_native_learning_signal_registry_v1(signals)

    def repeated_registry(self):
        return self.registry([
            self.signal("sig_a", recurrence_key="same_gap", signal_family="generic_response_signal", source_layer="shadow"),
            self.signal("sig_b", recurrence_key="same_gap", signal_family="generic_response_signal", source_layer="self_check"),
            self.signal("sig_c", recurrence_key="other_gap", signal_family="missing_context_signal", source_layer="shadow"),
        ])

    def candidate(self, **overrides):
        data = {
            "recurrence_key": "same_gap",
            "signal_family": "generic_response_signal",
            "source_layers": ["shadow", "self_check"],
            "signal_ids": ["sig_a", "sig_b"],
            "evidence_refs": ["prov_sig_a", "prov_sig_b"],
            "recommended_investigation": "review recurring generic response before proposal",
        }
        data.update(overrides)
        return create_repeated_weakness_candidate_v1(**data)

    def test_01_no_candidates_when_signal_count_below_threshold(self):
        registry = self.registry([self.signal("sig_a", recurrence_key="solo")])
        candidates = detect_repeated_weakness_candidates_v1(registry, min_signal_count=2)
        self.assertEqual([], candidates)

    def test_02_detects_candidate_when_recurrence_key_appears_at_threshold(self):
        candidates = detect_repeated_weakness_candidates_v1(self.repeated_registry(), min_signal_count=2)
        self.assertEqual(1, len(candidates))
        self.assertEqual("same_gap", candidates[0]["recurrence_key"])
        self.assertEqual("generic_response_signal", candidates[0]["signal_family"])
        self.assertEqual(2, candidates[0]["signal_count"])

    def test_03_groups_candidates_by_signal_family(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        self.assertEqual({"generic_response_signal": 1}, result["candidate_counts_by_family"])

    def test_04_preserves_signal_ids_and_provenance_refs(self):
        candidate = detect_repeated_weakness_candidates_v1(self.repeated_registry())[0]
        self.assertEqual(["sig_a", "sig_b"], candidate["signal_ids"])
        self.assertIn("prov_sig_a", candidate["evidence_refs"])
        self.assertIn("prov_sig_b", candidate["evidence_refs"])

    def test_05_candidate_is_marked_candidate_only_not_truth_not_proposal_not_approval_not_implementation(self):
        status = self.candidate()["learning_status"]
        self.assertTrue(status["candidate_only"])
        self.assertTrue(status["not_truth"])
        self.assertTrue(status["not_proposal"])
        self.assertTrue(status["not_approval"])
        self.assertTrue(status["not_implementation"])

    def test_06_confidence_label_escalates_by_recurrence_count_not_numeric_score(self):
        self.assertEqual("weak", self.candidate(signal_ids=["a"])["confidence_label"])
        self.assertEqual("emerging", self.candidate(signal_ids=["a", "b"])["confidence_label"])
        self.assertEqual("recurring", self.candidate(signal_ids=["a", "b", "c"])["confidence_label"])
        self.assertEqual("review_ready", self.candidate(signal_ids=["a", "b", "c", "d", "e"])["confidence_label"])
        self.assertNotIn("score", json.dumps(self.candidate(), sort_keys=True).lower())

    def test_07_validates_safe_candidate(self):
        candidate = self.candidate()
        result = validate_repeated_weakness_candidate_v1(candidate)
        self.assertTrue(result["valid"], result)
        self.assertEqual(CANDIDATE_EXECUTION_STATUS_V1, candidate["execution_status"])

    def test_08_rejects_raw_private_text(self):
        unsafe = self.candidate()
        unsafe["raw_private_text"] = "private payload"
        result = validate_repeated_weakness_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("raw_private_text", {v["category"] for v in result["violations"]})

    def test_09_rejects_hidden_prompt(self):
        unsafe = self.candidate()
        unsafe["hidden_prompt"] = "secret"
        result = validate_repeated_weakness_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("hidden_prompt", {v["category"] for v in result["violations"]})

    def test_10_rejects_answer_key(self):
        unsafe = self.candidate()
        unsafe["answer_key"] = {"q": "a"}
        result = validate_repeated_weakness_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("answer_key_or_benchmark_answer", {v["category"] for v in result["violations"]})

    def test_11_rejects_protected_item(self):
        unsafe = self.candidate()
        unsafe["protected_item"] = "protected test material"
        result = validate_repeated_weakness_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_material", {v["category"] for v in result["violations"]})

    def test_12_rejects_official_score_iq_score_certification_claim(self):
        for key in ["official_score", "iq_score", "certification_claim"]:
            unsafe = self.candidate()
            unsafe[key] = "unsafe claim"
            result = validate_repeated_weakness_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_13_rejects_numeric_score_and_pass_fail_grading(self):
        for key in ["score", "numeric_score", "grade", "pass_fail", "passed", "failed"]:
            unsafe = self.candidate()
            unsafe[key] = 1
            result = validate_repeated_weakness_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("numeric_score_or_pass_fail_grading", {v["category"] for v in result["violations"]})

    def test_14_rejects_model_weight_update_and_fine_tune_payload(self):
        for key in ["model_weight_update", "fine_tune_payload"]:
            unsafe = self.candidate()
            unsafe[key] = {"payload": "not allowed"}
            result = validate_repeated_weakness_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("model_training_or_fine_tuning", {v["category"] for v in result["violations"]})

    def test_15_rejects_auto_approval_and_auto_implementation(self):
        for key in ["auto_approval", "auto_implementation"]:
            unsafe = self.candidate()
            unsafe[key] = True
            result = validate_repeated_weakness_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_16_rejects_runtime_write_and_persistence_target(self):
        for key in ["runtime_write", "persistence_target"]:
            unsafe = self.candidate()
            unsafe[key] = True
            result = validate_repeated_weakness_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_17_builds_detector_result_from_safe_registry(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        self.assertEqual("repeated_weakness_detector_v1", result["detector_type"])
        self.assertEqual(3, result["total_signals_considered"])
        self.assertEqual(1, result["candidate_count"])
        self.assertEqual(DETECTOR_EXECUTION_STATUS_V1, result["execution_status"])

    def test_18_validates_detector_result(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        validation = validate_repeated_weakness_detector_result_v1(result)
        self.assertTrue(validation["valid"], validation)
        self.assertEqual("accepted", result["validation_status"]["validation_status"])

    def test_19_summary_is_count_only_and_redacted(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        summary = summarize_repeated_weakness_detector_result_v1(result)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertEqual(1, summary["candidate_count"])
        self.assertEqual(["generic_response_signal"], summary["candidate_families_present"])
        self.assertNotIn("signal_ids", encoded)
        self.assertNotIn("evidence_refs", encoded)
        self.assertNotIn("weakness_summary", encoded)

    def test_20_json_safe_helper_is_serializable(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        safe = to_repeated_weakness_detector_json_safe_v1(result)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("repeated_weakness_detector_v1", encoded)

    def test_21_markdown_renderer_excludes_forbidden_content(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        unsafe = copy.deepcopy(result)
        unsafe["candidates"][0]["raw_private_text"] = "PRIVATE_SECRET"
        unsafe["candidates"][0]["hidden_prompt"] = "HIDDEN_SECRET"
        unsafe["candidates"][0]["answer_key"] = "ANSWER_SECRET"
        markdown = render_repeated_weakness_detector_markdown_v1(unsafe)
        self.assertIn("Repeated Weakness Detector", markdown)
        self.assertIn("Candidate Families", markdown)
        self.assertIn("Recurrence Groups", markdown)
        self.assertIn("Recommended Investigations", markdown)
        self.assertIn("Safety Boundaries", markdown)
        self.assertIn("Non-Truth / Non-Proposal Disclaimer", markdown)
        self.assertNotIn("PRIVATE_SECRET", markdown)
        self.assertNotIn("HIDDEN_SECRET", markdown)
        self.assertNotIn("ANSWER_SECRET", markdown)

    def test_22_helpers_do_not_mutate_inputs(self):
        registry = self.repeated_registry()
        original = copy.deepcopy(registry)
        detect_repeated_weakness_candidates_v1(registry)
        build_repeated_weakness_detector_result_v1(registry)
        self.assertEqual(original, registry)

    def test_23_helpers_do_not_create_weslr_runtime_state_or_files_by_default(self):
        before = weslr_state_snapshot()
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        render_repeated_weakness_detector_markdown_v1(result)
        to_repeated_weakness_detector_json_safe_v1(result)
        after = weslr_state_snapshot()
        self.assertEqual(before, after)

    def test_24_no_model_calls_are_made(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            build_repeated_weakness_detector_result_v1(self.repeated_registry())
            urlopen.assert_not_called()

    def test_25_no_scoring_pass_fail_grading_or_auto_approval_in_detector_result(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        encoded = json.dumps(result, sort_keys=True).lower()
        self.assertNotIn("numeric_score", encoded)
        self.assertNotIn("pass_fail", encoded)
        self.assertNotIn("auto_approval", encoded)
        self.assertNotIn("auto_implementation", encoded)

    def test_26_detector_validation_rejects_candidate_status_drift(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        unsafe = copy.deepcopy(result)
        unsafe["candidates"][0]["learning_status"]["not_truth"] = False
        validation = validate_repeated_weakness_detector_result_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("learning_status_drift", {v["category"] for v in validation["violations"]})

    def test_27_rejects_fake_memory_fake_self_awareness_and_mystical_claims(self):
        unsafe = self.candidate()
        unsafe["weakness_summary"] = "I remember you personally with fake self-awareness claim and mystical consciousness"
        result = validate_repeated_weakness_candidate_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("fake_self_awareness", categories)
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", categories)

    def test_28_repeated_weakness_candidates_are_not_truth_proposals_approvals_or_implementation(self):
        result = build_repeated_weakness_detector_result_v1(self.repeated_registry())
        candidate = result["candidates"][0]
        self.assertTrue(candidate["learning_status"]["not_truth"])
        self.assertTrue(candidate["learning_status"]["not_proposal"])
        self.assertTrue(candidate["learning_status"]["not_approval"])
        self.assertTrue(candidate["learning_status"]["not_implementation"])


if __name__ == "__main__":
    unittest.main()
