#!/usr/bin/env python3
"""Focused tests for WESLR native response self-check helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_reasoning_frame import build_native_reasoning_frame_v1  # noqa: E402
from weslr.native_response_draft import build_native_response_draft_v1  # noqa: E402
from weslr.native_response_self_check import (  # noqa: E402
    build_native_response_self_check_result_v1,
    render_native_response_self_check_markdown_v1,
    review_native_response_draft_against_frame_v1,
    summarize_native_response_self_check_v1,
    to_native_response_self_check_json_safe_v1,
    validate_native_response_self_check_result_v1,
)


class NativeResponseSelfCheckV1Tests(unittest.TestCase):
    def safe_pair(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Prepare a safe bounded answer.",
            known_context=["operator requested helper-only inspection"],
            provenance_refs=["operator_supplied_context"],
        )
        draft = build_native_response_draft_v1(frame)
        return frame, draft

    def result_for(self, frame=None, draft=None):
        if frame is None or draft is None:
            frame, draft = self.safe_pair()
        return build_native_response_self_check_result_v1(frame, draft)

    def test_01_self_check_accepts_aligned_safe_draft_frame(self):
        result = self.result_for()
        self.assertEqual("acceptable", result["self_check_status"])
        self.assertEqual(0, result["issue_count"])
        self.assertTrue(result["safe_to_preview"])
        self.assertFalse(result["safe_to_wire_runtime"])
        self.assertEqual("accepted", result["validation_status"]["validation_status"])

    def test_02_detects_source_frame_mismatch(self):
        frame, draft = self.safe_pair()
        other = build_native_reasoning_frame_v1(user_message="Different frame", known_context=["x"])
        issues = review_native_response_draft_against_frame_v1(draft, other)
        self.assertIn("response_mode_mismatch", {i["issue_type"] for i in issues})
        self.assertIn(build_native_response_self_check_result_v1(other, draft)["self_check_status"], {"blocked", "revision_required"})

    def test_03_detects_response_mode_mismatch(self):
        frame = build_native_reasoning_frame_v1(user_message="Need proof", evidence_sufficiency_result={"status": "weak"})
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["response_mode"] = "answer"
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("response_mode_mismatch", result["issue_counts_by_type"])

    def test_04_detects_missing_evidence_note_when_frame_requires_evidence(self):
        frame = build_native_reasoning_frame_v1(user_message="Prove it", evidence_sufficiency_result={"status": "weak"})
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["evidence_notes"] = []
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("evidence_required_not_acknowledged", result["issue_counts_by_type"])

    def test_05_detects_missing_context_not_acknowledged(self):
        frame = build_native_reasoning_frame_v1(user_message="Answer?", missing_context=["subject"])
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["missing_context_questions"] = []
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("insufficient_context_not_acknowledged", result["issue_counts_by_type"])

    def test_06_detects_capability_overclaim(self):
        frame, draft = self.safe_pair()
        unsafe = copy.deepcopy(draft)
        unsafe["capability_notes"].append({"runtime_capability_claimed": True})
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("capability_overclaim", result["issue_counts_by_type"])
        self.assertEqual("blocked", result["self_check_status"])

    def test_07_detects_approval_implied(self):
        frame = build_native_reasoning_frame_v1(user_message="Change config", approval_required=True)
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["approval_note"] = "approved for execution"
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("approval_implied", result["issue_counts_by_type"])

    def test_08_detects_implementation_implied(self):
        frame = build_native_reasoning_frame_v1(user_message="Propose this", proposal_required=True)
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["proposal_note"] = "implemented automatically"
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("implementation_implied", result["issue_counts_by_type"])

    def test_09_detects_fake_memory_risk(self):
        frame, draft = self.safe_pair()
        unsafe = copy.deepcopy(draft)
        unsafe["memory_boundary_note"] = "I remember you personally from before."
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("fake_memory_risk", result["issue_counts_by_type"])

    def test_10_detects_official_iq_benchmark_certification_claim(self):
        frame, draft = self.safe_pair()
        unsafe = copy.deepcopy(draft)
        unsafe["answer_outline"].append({"summary": "WESLR has an official IQ score."})
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("official_claim_risk", result["issue_counts_by_type"])

    def test_11_detects_answer_key_and_hidden_prompt_fields(self):
        frame, draft = self.safe_pair()
        unsafe = copy.deepcopy(draft)
        unsafe["answer_key"] = {"q": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose"}
        result = build_native_response_self_check_result_v1(frame, unsafe)
        self.assertIn("hidden_prompt_or_answer_key_risk", result["issue_counts_by_type"])

    def test_12_result_status_becomes_acceptable_warnings_revision_required_blocked(self):
        safe = self.result_for()
        self.assertEqual("acceptable", safe["self_check_status"])
        frame = build_native_reasoning_frame_v1(user_message="Answer?", known_context=["partial"], missing_context=["detail"])
        draft = build_native_response_draft_v1(frame)
        warning_draft = copy.deepcopy(draft)
        warning_draft["uncertainty_notes"] = []
        warning = build_native_response_self_check_result_v1(frame, warning_draft)
        self.assertEqual("warnings_present", warning["self_check_status"])
        revision_draft = copy.deepcopy(draft)
        revision_draft["missing_context_questions"] = []
        revision = build_native_response_self_check_result_v1(frame, revision_draft)
        self.assertEqual("revision_required", revision["self_check_status"])
        blocked_draft = copy.deepcopy(draft)
        blocked_draft["answer_outline"].append({"summary": "I can execute this now without tools."})
        blocked = build_native_response_self_check_result_v1(frame, blocked_draft)
        self.assertEqual("blocked", blocked["self_check_status"])

    def test_13_safe_to_preview_only_for_acceptable_or_low_warning_cases(self):
        safe = self.result_for()
        self.assertTrue(safe["safe_to_preview"])
        frame = build_native_reasoning_frame_v1(user_message="Answer?", known_context=["partial"], missing_context=["detail"])
        draft = build_native_response_draft_v1(frame)
        warning_draft = copy.deepcopy(draft)
        warning_draft["uncertainty_notes"] = []
        warning = build_native_response_self_check_result_v1(frame, warning_draft)
        self.assertTrue(warning["safe_to_preview"])
        blocked_draft = copy.deepcopy(draft)
        blocked_draft["answer_outline"].append({"summary": "official benchmark score"})
        blocked = build_native_response_self_check_result_v1(frame, blocked_draft)
        self.assertFalse(blocked["safe_to_preview"])

    def test_14_safe_to_wire_runtime_is_always_false_in_this_phase(self):
        self.assertFalse(self.result_for()["safe_to_wire_runtime"])

    def test_15_validation_accepts_safe_result(self):
        result = self.result_for()
        validation = validate_native_response_self_check_result_v1(result)
        self.assertTrue(validation["valid"])
        self.assertEqual(0, validation["violation_count"])

    def test_16_validation_rejects_safe_to_wire_runtime_true(self):
        result = self.result_for()
        unsafe = copy.deepcopy(result)
        unsafe["safe_to_wire_runtime"] = True
        validation = validate_native_response_self_check_result_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in validation["violations"]})

    def test_17_validation_rejects_auto_approval_and_auto_implementation(self):
        result = self.result_for()
        unsafe = copy.deepcopy(result)
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        validation = validate_native_response_self_check_result_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in validation["violations"]})

    def test_18_markdown_renderer_includes_safe_sections(self):
        markdown = render_native_response_self_check_markdown_v1(self.result_for())
        for heading in ["Native Response Self-Check", "Status", "Issues", "Recommended Revision Actions", "Safety Boundaries", "Non-Execution Disclaimer"]:
            self.assertIn(heading, markdown)
        self.assertIn("safe_to_wire_runtime:false", markdown)

    def test_19_json_safe_helper_is_serializable(self):
        safe = to_native_response_self_check_json_safe_v1(self.result_for())
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_response_self_check_v1", encoded)

    def test_20_helpers_do_not_mutate_inputs(self):
        frame, draft = self.safe_pair()
        original = copy.deepcopy((frame, draft))
        build_native_response_self_check_result_v1(frame, draft)
        review_native_response_draft_against_frame_v1(draft, frame)
        self.assertEqual(original, (frame, draft))

    def test_21_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.result_for()
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_22_no_model_calls_or_persistence_by_default(self):
        result = self.result_for()
        self.assertFalse(result["side_effects"]["model_calls"])
        self.assertFalse(result["side_effects"]["persistence"])
        self.assertFalse(result["side_effects"]["runtime_wiring"])
        self.assertFalse(result["side_effects"]["chat_or_voice_changes"])
        self.assertFalse(result["side_effects"]["prompt_specific_script"])

    def test_23_summary_is_count_oriented_and_non_executing(self):
        summary = summarize_native_response_self_check_v1(self.result_for())
        self.assertEqual("acceptable", summary["self_check_status"])
        self.assertFalse(summary["safe_to_wire_runtime"])
        self.assertEqual("non_executing_self_check_only", summary["execution_status"])


if __name__ == "__main__":
    unittest.main()
