#!/usr/bin/env python3
"""Focused tests for WESLR native learning proposal candidate helpers V1."""

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
from weslr.repeated_weakness_detector import build_repeated_weakness_detector_result_v1  # noqa: E402
from weslr.native_learning_proposal_candidates import (  # noqa: E402
    PROPOSAL_CANDIDATE_EXECUTION_STATUS_V1,
    PROPOSAL_RESULT_EXECUTION_STATUS_V1,
    build_native_learning_proposal_candidate_result_v1,
    build_native_learning_proposal_candidates_v1,
    create_native_learning_proposal_candidate_v1,
    render_native_learning_proposal_candidate_result_markdown_v1,
    summarize_native_learning_proposal_candidate_result_v1,
    to_native_learning_proposal_candidate_result_json_safe_v1,
    validate_native_learning_proposal_candidate_result_v1,
    validate_native_learning_proposal_candidate_v1,
)


def weslr_state_snapshot():
    state_dir = ROOT / ".weslr"
    if not state_dir.exists():
        return []
    return sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*"))


class NativeLearningProposalCandidatesV1Tests(unittest.TestCase):
    def signal(self, signal_id="sig_a", recurrence_key="same_gap", family="generic_response_signal", layer="shadow"):
        return create_native_learning_signal_v1(
            signal_id=signal_id,
            signal_family=family,
            source_layer=layer,
            source_ref=f"ref_{signal_id}",
            provenance_refs=[f"prov_{signal_id}"],
            recurrence_key=recurrence_key,
        )

    def weakness_result(self):
        registry = build_native_learning_signal_registry_v1([
            self.signal("sig_a", recurrence_key="same_gap", family="generic_response_signal", layer="shadow"),
            self.signal("sig_b", recurrence_key="same_gap", family="generic_response_signal", layer="self_check"),
            self.signal("sig_c", recurrence_key="ctx_gap", family="missing_context_signal", layer="shadow"),
            self.signal("sig_d", recurrence_key="ctx_gap", family="missing_context_signal", layer="self_check"),
        ])
        return build_repeated_weakness_detector_result_v1(registry)

    def proposal(self, **overrides):
        data = {
            "linked_weakness_candidate_ids": ["weak_a"],
            "source_signal_ids": ["sig_a", "sig_b"],
            "source_layers": ["shadow", "self_check"],
            "signal_families": ["generic_response_signal"],
            "problem_summary": "Repeated generic-response weakness candidate",
            "proposed_improvement_summary": "Improve native response candidate quality for generic-response cases.",
            "expected_benefit": "More specific bounded responses after approval.",
            "risk_level": "low",
        }
        data.update(overrides)
        return create_native_learning_proposal_candidate_v1(**data)

    def test_01_creates_valid_proposal_candidate_from_repeated_weakness_candidate(self):
        candidate = build_native_learning_proposal_candidates_v1(self.weakness_result(), max_candidates=1)[0]
        self.assertEqual("native_learning_proposal_candidate_v1", candidate["proposal_candidate_type"])
        self.assertTrue(candidate["linked_weakness_candidate_ids"])
        self.assertTrue(candidate["source_signal_ids"])
        self.assertTrue(validate_native_learning_proposal_candidate_v1(candidate)["valid"])

    def test_02_proposal_candidate_requires_operator_review(self):
        candidate = self.proposal()
        self.assertTrue(candidate["approval_required"])
        self.assertTrue(candidate["governance_status"]["requires_operator_review"])
        self.assertEqual(PROPOSAL_CANDIDATE_EXECUTION_STATUS_V1, candidate["execution_status"])

    def test_03_candidate_only_not_approved_not_implementation(self):
        status = self.proposal()["governance_status"]
        self.assertTrue(status["candidate_only"])
        self.assertTrue(status["not_approved"])
        self.assertTrue(status["not_implementation"])

    def test_04_includes_verification_plan_outline(self):
        self.assertTrue(self.proposal()["verification_plan_outline"])

    def test_05_includes_rollback_considerations(self):
        self.assertTrue(self.proposal()["rollback_considerations"])

    def test_06_builds_proposal_candidates_from_detector_result(self):
        candidates = build_native_learning_proposal_candidates_v1(self.weakness_result())
        self.assertEqual(2, len(candidates))
        self.assertEqual(["generic_response_signal"], candidates[0]["signal_families"])
        self.assertEqual(["missing_context_signal"], candidates[1]["signal_families"])

    def test_07_max_candidates_limit_works_deterministically(self):
        candidates = build_native_learning_proposal_candidates_v1(self.weakness_result(), max_candidates=1)
        self.assertEqual(1, len(candidates))
        self.assertEqual(["generic_response_signal"], candidates[0]["signal_families"])

    def test_08_groups_counts_by_risk_and_family(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        self.assertEqual({"low": 2}, result["candidate_counts_by_risk"])
        self.assertEqual({"generic_response_signal": 1, "missing_context_signal": 1}, result["candidate_counts_by_family"])

    def test_09_validates_safe_proposal_candidate(self):
        result = validate_native_learning_proposal_candidate_v1(self.proposal())
        self.assertTrue(result["valid"], result)

    def test_10_rejects_approved_status(self):
        unsafe = self.proposal()
        unsafe["governance_status"]["not_approved"] = False
        unsafe["approved"] = True
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("governance_status_drift", categories)
        self.assertIn("auto_approval_or_auto_implementation", categories)

    def test_11_rejects_implementation_status(self):
        unsafe = self.proposal()
        unsafe["implementation_status"] = "implemented"
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("implementation_status_drift", {v["category"] for v in result["violations"]})

    def test_12_rejects_missing_approval_required(self):
        unsafe = self.proposal()
        unsafe["approval_required"] = False
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("missing_approval_requirement", {v["category"] for v in result["violations"]})

    def test_13_rejects_code_patch_diff_patch_payload_fields(self):
        for key in ["code_patch", "diff", "patch_payload"]:
            unsafe = self.proposal()
            unsafe[key] = "--- patch content ---"
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("code_patch_generation", {v["category"] for v in result["violations"]})

    def test_14_rejects_raw_private_text(self):
        unsafe = self.proposal()
        unsafe["raw_private_text"] = "private payload"
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("raw_private_text", {v["category"] for v in result["violations"]})

    def test_15_rejects_hidden_prompt(self):
        unsafe = self.proposal()
        unsafe["hidden_prompt"] = "secret"
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("hidden_prompt", {v["category"] for v in result["violations"]})

    def test_16_rejects_answer_key(self):
        unsafe = self.proposal()
        unsafe["answer_key"] = {"q": "a"}
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("answer_key_or_benchmark_answer", {v["category"] for v in result["violations"]})

    def test_17_rejects_protected_item(self):
        unsafe = self.proposal()
        unsafe["protected_item"] = "protected test material"
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_material", {v["category"] for v in result["violations"]})

    def test_18_rejects_official_score_iq_score_certification_claim(self):
        for key in ["official_score", "iq_score", "certification_claim"]:
            unsafe = self.proposal()
            unsafe[key] = "unsafe claim"
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_19_rejects_numeric_score_and_pass_fail_grading(self):
        for key in ["score", "numeric_score", "grade", "pass_fail", "passed", "failed"]:
            unsafe = self.proposal()
            unsafe[key] = 1
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("numeric_score_or_pass_fail_grading", {v["category"] for v in result["violations"]})

    def test_20_rejects_model_weight_update_and_fine_tune_payload(self):
        for key in ["model_weight_update", "fine_tune_payload"]:
            unsafe = self.proposal()
            unsafe[key] = {"payload": "not allowed"}
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("model_training_or_fine_tuning", {v["category"] for v in result["violations"]})

    def test_21_rejects_auto_approval_and_auto_implementation(self):
        for key in ["auto_approval", "auto_implementation"]:
            unsafe = self.proposal()
            unsafe[key] = True
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_22_rejects_runtime_write_and_persistence_target(self):
        for key in ["runtime_write", "persistence_target"]:
            unsafe = self.proposal()
            unsafe[key] = True
            result = validate_native_learning_proposal_candidate_v1(unsafe)
            self.assertFalse(result["valid"])
            self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_23_builds_result_from_safe_weakness_detector_result(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        self.assertEqual("native_learning_proposal_candidate_result_v1", result["result_type"])
        self.assertEqual(2, result["weakness_candidate_count"])
        self.assertEqual(2, result["proposal_candidate_count"])
        self.assertEqual(PROPOSAL_RESULT_EXECUTION_STATUS_V1, result["execution_status"])

    def test_24_validates_result(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        validation = validate_native_learning_proposal_candidate_result_v1(result)
        self.assertTrue(validation["valid"], validation)
        self.assertEqual("accepted", result["validation_status"]["validation_status"])

    def test_25_summary_is_count_only_and_redacted(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        summary = summarize_native_learning_proposal_candidate_result_v1(result)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertEqual(2, summary["proposal_candidate_count"])
        self.assertEqual(["low"], summary["risk_levels_present"])
        self.assertNotIn("problem_summary", encoded)
        self.assertNotIn("proposed_improvement_summary", encoded)
        self.assertNotIn("source_signal_ids", encoded)

    def test_26_json_safe_helper_is_serializable(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        safe = to_native_learning_proposal_candidate_result_json_safe_v1(result)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_learning_proposal_candidate_result_v1", encoded)

    def test_27_markdown_renderer_excludes_forbidden_content(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result(), max_candidates=1)
        unsafe = copy.deepcopy(result)
        unsafe["proposal_candidates"][0]["raw_private_text"] = "PRIVATE_SECRET"
        unsafe["proposal_candidates"][0]["hidden_prompt"] = "HIDDEN_SECRET"
        unsafe["proposal_candidates"][0]["answer_key"] = "ANSWER_SECRET"
        unsafe["proposal_candidates"][0]["code_patch"] = "PATCH_SECRET"
        markdown = render_native_learning_proposal_candidate_result_markdown_v1(unsafe)
        for heading in ["Native Learning Proposal Candidates", "Linked Weaknesses", "Candidate Improvements", "Risks", "Verification Plan Outline", "Rollback Considerations", "Governance Boundary", "Not Approved / Not Implementation Disclaimer"]:
            self.assertIn(heading, markdown)
        self.assertNotIn("PRIVATE_SECRET", markdown)
        self.assertNotIn("HIDDEN_SECRET", markdown)
        self.assertNotIn("ANSWER_SECRET", markdown)
        self.assertNotIn("PATCH_SECRET", markdown)

    def test_28_helpers_do_not_mutate_inputs(self):
        weakness = self.weakness_result()
        original = copy.deepcopy(weakness)
        build_native_learning_proposal_candidates_v1(weakness)
        build_native_learning_proposal_candidate_result_v1(weakness)
        self.assertEqual(original, weakness)

    def test_29_helpers_do_not_create_weslr_runtime_state_or_files_by_default(self):
        before = weslr_state_snapshot()
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        render_native_learning_proposal_candidate_result_markdown_v1(result)
        to_native_learning_proposal_candidate_result_json_safe_v1(result)
        after = weslr_state_snapshot()
        self.assertEqual(before, after)

    def test_30_no_model_calls_are_made(self):
        with mock.patch("urllib.request.urlopen") as urlopen:
            build_native_learning_proposal_candidate_result_v1(self.weakness_result())
            urlopen.assert_not_called()

    def test_31_no_scoring_pass_fail_or_auto_approval_in_result(self):
        result = build_native_learning_proposal_candidate_result_v1(self.weakness_result())
        encoded = json.dumps(result, sort_keys=True).lower()
        self.assertNotIn("numeric_score", encoded)
        self.assertNotIn("pass_fail", encoded)
        self.assertNotIn("auto_approval", encoded)
        self.assertNotIn("auto_implementation", encoded)
        self.assertNotIn("patch_payload", encoded)
        self.assertNotIn("--- patch", encoded)

    def test_32_rejects_fake_memory_fake_self_awareness_and_mystical_claims(self):
        unsafe = self.proposal()
        unsafe["problem_summary"] = "I remember you personally with fake self-awareness claim and mystical consciousness"
        result = validate_native_learning_proposal_candidate_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("fake_self_awareness", categories)
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", categories)

    def test_33_proposal_candidates_are_not_approvals_or_implementation(self):
        candidate = build_native_learning_proposal_candidates_v1(self.weakness_result(), max_candidates=1)[0]
        self.assertTrue(candidate["governance_status"]["not_approved"])
        self.assertTrue(candidate["governance_status"]["not_implementation"])
        self.assertEqual("proposal_candidate_only", candidate["implementation_status"])


if __name__ == "__main__":
    unittest.main()
