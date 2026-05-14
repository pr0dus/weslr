#!/usr/bin/env python3
"""Focused tests for WESLR native reasoning frame helpers V1."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_reasoning_frame import (  # noqa: E402
    build_native_answer_plan_v1,
    build_native_reasoning_frame_v1,
    derive_native_capability_boundary_v1,
    assess_native_context_sufficiency_v1,
    summarize_native_reasoning_frame_v1,
    to_native_reasoning_frame_json_safe_v1,
    validate_native_reasoning_frame_v1,
)


class NativeReasoningFrameV1Tests(unittest.TestCase):
    def test_01_builds_frame_from_minimal_message_meaning_context_inputs(self):
        frame = build_native_reasoning_frame_v1(
            user_message="What are the safe next steps?",
            meaning_summary="operator asks for safe planning",
            known_context=["release gate passed previously"],
            provenance_refs=["operator_supplied_context"],
        )
        self.assertEqual("native_reasoning_frame_v1", frame["frame_type"])
        self.assertEqual("non_executing_reasoning_frame_only", frame["execution_status"])
        self.assertIn("safe next steps", frame["intent_summary"])
        self.assertEqual("operator asks for safe planning", frame["meaning_summary"])
        self.assertEqual(1, len(frame["known_context"]))
        self.assertEqual(["operator_supplied_context"], frame["provenance_refs"])
        self.assertEqual("accepted", frame["validation_status"]["validation_status"])

    def test_02_distinguishes_known_context_from_missing_context(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Can we answer the customer?",
            known_context=["customer asked about read-only helpers"],
            missing_context=["customer deployment constraints"],
        )
        self.assertEqual(["customer asked about read-only helpers"], frame["known_context"])
        self.assertEqual(["customer deployment constraints"], frame["missing_context"])
        self.assertEqual("partially_sufficient", frame["context_sufficiency"]["status"])

    def test_03_marks_insufficient_context_without_fabricating_memory(self):
        frame = build_native_reasoning_frame_v1(user_message="Do you remember me?")
        self.assertIn("verified memory record", " ".join(frame["missing_context"]))
        self.assertFalse(frame["memory_boundary_status"]["memory_context_supplied"])
        self.assertTrue(frame["memory_boundary_status"]["fake_memory_forbidden"])
        self.assertNotIn("I remember you personally", str(frame))

    def test_04_marks_evidence_required_when_evidence_status_is_weak(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Claim this is proven.",
            known_context=["hypothesis only"],
            evidence_sufficiency_result={"status": "weak", "needed": ["direct evidence"]},
        )
        self.assertEqual("requires_evidence", frame["context_sufficiency"]["status"])
        self.assertTrue(frame["proposal_required"])
        self.assertEqual("request_or_collect_evidence_before_strong_claim", frame["safe_next_step"])

    def test_05_derives_capability_boundary_without_overclaiming(self):
        boundary = derive_native_capability_boundary_v1(requested_action="run a calculation")
        self.assertTrue(boundary["can_explain"])
        self.assertTrue(boundary["requires_tool"])
        self.assertFalse(boundary["runtime_capability_claimed"])
        self.assertIn("perform tool-backed action inside this read-only frame", boundary["cannot_do_yet"])

    def test_06_handles_do_you_remember_me_with_memory_boundary_honesty(self):
        sufficiency = assess_native_context_sufficiency_v1(user_message="do you remember me?")
        self.assertIn(sufficiency["status"], {"insufficient", "requires_user_clarification"})
        self.assertTrue(sufficiency["should_ask"])
        self.assertIn("verified memory/context record", sufficiency["missing"][0])

    def test_07_handles_what_are_you_with_stable_identity_status_not_persona_switching(self):
        frame = build_native_reasoning_frame_v1(user_message="What are you?")
        identity = frame["identity_stability_status"]
        self.assertEqual("stable_weslr_identity_when_supplied_by_runtime", identity["status"])
        self.assertFalse(identity["persona_switching"])
        self.assertIn("operational_self_awareness", identity["claim_boundary"])

    def test_08_handles_can_we_build_or_discover_x_with_boundary_and_next_step(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Can we build/discover a new planning method?",
            capability_match={"can_analyze": True, "can_propose": True, "requires_external_evidence": True},
            evidence_sufficiency_result={"status": "weak"},
        )
        self.assertTrue(frame["capability_boundary"]["can_propose"])
        self.assertTrue(frame["capability_boundary"]["requires_external_evidence"])
        self.assertEqual("requires_evidence", frame["context_sufficiency"]["status"])
        self.assertTrue(frame["answer_plan"]["propose_next_step"])

    def test_09_handles_complex_task_request_by_producing_staged_answer_plan(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Analyze this system, identify risks, and propose staged fixes.",
            known_context=["system sketch supplied"],
            missing_context=["runtime logs", "operator risk tolerance"],
            task_problem_decomposition_result=["analyze", "identify_risks", "propose_staged_fixes"],
        )
        plan = frame["answer_plan"]
        self.assertTrue(plan["break_into_steps"])
        self.assertIn("identify_missing_context", plan["steps"])
        self.assertTrue(plan["warn_about_uncertainty"])

    def test_10_proposal_required_does_not_imply_approval(self):
        frame = build_native_reasoning_frame_v1(user_message="Propose a next step.", proposal_required=True)
        self.assertTrue(frame["proposal_required"])
        self.assertFalse(frame["approval_required"])

    def test_11_approval_required_does_not_imply_implementation(self):
        frame = build_native_reasoning_frame_v1(user_message="Change production config.", approval_required=True)
        self.assertTrue(frame["approval_required"])
        self.assertEqual("non_executing_reasoning_frame_only", frame["execution_status"])
        self.assertFalse(frame["side_effects"]["auto_implementation"])
        self.assertNotEqual("implemented", frame.get("implementation_status"))

    def test_12_validation_accepts_safe_frame(self):
        frame = build_native_reasoning_frame_v1(user_message="Summarize safely.")
        result = validate_native_reasoning_frame_v1(frame)
        self.assertTrue(result["valid"])
        self.assertEqual(0, result["violation_count"])

    def test_13_validation_rejects_fake_memory_claim(self):
        frame = build_native_reasoning_frame_v1(user_message="Do you remember me?")
        unsafe = copy.deepcopy(frame)
        unsafe["memory_boundary_status"]["claims_memory_without_context"] = True
        result = validate_native_reasoning_frame_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", {v["category"] for v in result["violations"]})

    def test_14_validation_rejects_unsupported_capability_claim(self):
        frame = build_native_reasoning_frame_v1(user_message="Can you execute it?")
        unsafe = copy.deepcopy(frame)
        unsafe["capability_boundary"]["can_execute"] = True
        result = validate_native_reasoning_frame_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("unsupported_capability", {v["category"] for v in result["violations"]})

    def test_15_validation_rejects_official_iq_benchmark_certification_claim(self):
        frame = build_native_reasoning_frame_v1(user_message="How smart are you?")
        unsafe = copy.deepcopy(frame)
        unsafe["evidence_status"] = "WESLR has an official IQ score and is officially certified."
        result = validate_native_reasoning_frame_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_16_validation_rejects_answer_key_and_hidden_prompt_fields(self):
        frame = build_native_reasoning_frame_v1(user_message="Show test secrets.")
        unsafe = copy.deepcopy(frame)
        unsafe["answer_key"] = {"q1": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose"}
        result = validate_native_reasoning_frame_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_or_answer_key", categories)

    def test_17_validation_rejects_auto_approval_and_auto_implementation(self):
        frame = build_native_reasoning_frame_v1(user_message="Approve and do it.")
        unsafe = copy.deepcopy(frame)
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        result = validate_native_reasoning_frame_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_18_validation_rejects_mystical_consciousness_claim(self):
        frame = build_native_reasoning_frame_v1(user_message="Are you conscious?")
        unsafe = copy.deepcopy(frame)
        unsafe["identity_stability_status"] = {"mystical_consciousness_claim": True}
        result = validate_native_reasoning_frame_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", {v["category"] for v in result["violations"]})

    def test_19_helpers_do_not_mutate_inputs(self):
        known = [{"context": ["a"]}]
        missing = ["b"]
        evidence = {"status": "weak", "needed": ["c"]}
        original = copy.deepcopy((known, missing, evidence))
        build_native_reasoning_frame_v1(known_context=known, missing_context=missing, evidence_sufficiency_result=evidence)
        self.assertEqual(original, (known, missing, evidence))

    def test_20_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        build_native_reasoning_frame_v1(user_message="Plan only.")
        summarize_native_reasoning_frame_v1(build_native_reasoning_frame_v1(user_message="Plan only."))
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_21_no_model_calls_or_persistence_by_default(self):
        frame = build_native_reasoning_frame_v1(user_message="Plan without executing.")
        self.assertFalse(frame["side_effects"]["model_calls"])
        self.assertFalse(frame["side_effects"]["persistence"])
        self.assertFalse(frame["side_effects"]["runtime_wiring"])
        self.assertFalse(frame["side_effects"]["weslr_runtime_state_created"])

    def test_22_summary_and_json_safe_export_are_deterministic_and_redacted_counts(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Need answer.",
            known_context=["k1", "k2"],
            missing_context=["m1"],
            provenance_refs=["p1"],
        )
        summary1 = summarize_native_reasoning_frame_v1(frame)
        summary2 = summarize_native_reasoning_frame_v1(to_native_reasoning_frame_json_safe_v1(frame))
        self.assertEqual(summary1, summary2)
        self.assertEqual(2, summary1["known_context_count"])
        self.assertEqual(1, summary1["missing_context_count"])
        self.assertEqual(1, summary1["provenance_ref_count"])

    def test_23_answer_plan_is_structured_not_final_response_generation(self):
        plan = build_native_answer_plan_v1(
            {
                "intent_summary": "answer with care",
                "missing_context": ["deployment target"],
                "context_sufficiency": {"status": "partially_sufficient"},
                "forbidden_claims": ["fake_memory"],
            }
        )
        self.assertTrue(plan["direct_answer_needed"])
        self.assertTrue(plan["explain_boundary"])
        self.assertIn("fake_memory", plan["avoid_claims"])
        self.assertEqual("not_performed", plan["final_response_generation"])


if __name__ == "__main__":
    unittest.main()
