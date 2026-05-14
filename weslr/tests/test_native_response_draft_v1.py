#!/usr/bin/env python3
"""Focused tests for WESLR native response draft helpers V1."""

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
from weslr.native_response_draft import (  # noqa: E402
    build_native_response_draft_v1,
    derive_native_response_mode_v1,
    render_native_response_draft_preview_v1,
    to_native_response_draft_json_safe_v1,
    validate_native_response_draft_v1,
)


class NativeResponseDraftV1Tests(unittest.TestCase):
    def safe_frame(self):
        return build_native_reasoning_frame_v1(
            user_message="Explain the safe answer shape.",
            meaning_summary="safe response planning",
            known_context=["operator requested helper-only draft"],
            provenance_refs=["operator_supplied_context"],
        )

    def test_01_builds_draft_from_safe_native_reasoning_frame(self):
        frame = self.safe_frame()
        draft = build_native_response_draft_v1(frame)
        self.assertEqual("native_response_draft_v1", draft["draft_type"])
        self.assertEqual(frame["frame_id"], draft["source_frame_id"])
        self.assertEqual("non_executing_response_draft_only", draft["execution_status"])
        self.assertEqual("accepted", draft["validation_status"]["validation_status"])
        self.assertFalse(draft["final_chat_output"])

    def test_02_derives_answer_mode_when_context_and_evidence_sufficient(self):
        frame = self.safe_frame()
        self.assertEqual("answer", derive_native_response_mode_v1(frame))
        draft = build_native_response_draft_v1(frame)
        self.assertEqual("answer", draft["response_mode"])

    def test_03_derives_insufficient_context_or_clarify_mode_when_missing_context_exists(self):
        frame = build_native_reasoning_frame_v1(user_message="Can you answer this?", missing_context=["question subject"])
        mode = derive_native_response_mode_v1(frame)
        self.assertIn(mode, {"insufficient_context", "clarify"})
        draft = build_native_response_draft_v1(frame)
        self.assertTrue(draft["missing_context_questions"])

    def test_04_derives_evidence_required_mode_when_frame_requires_evidence(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Claim this is proven.",
            known_context=["hypothesis only"],
            evidence_sufficiency_result={"status": "weak", "needed": ["direct observation"]},
        )
        self.assertEqual("evidence_required", derive_native_response_mode_v1(frame))
        draft = build_native_response_draft_v1(frame)
        self.assertEqual("evidence_required", draft["response_mode"])
        self.assertTrue(draft["evidence_notes"])

    def test_05_derives_explain_boundary_mode_when_capability_boundary_blocks_overclaiming(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Run the external calculation.",
            capability_match={"requires_tool": True},
            known_context=["calculation request"],
        )
        self.assertEqual("explain_boundary", derive_native_response_mode_v1(frame))
        draft = build_native_response_draft_v1(frame)
        self.assertIn("requires_tool:True", draft["capability_notes"])

    def test_06_approval_required_produces_approval_note_but_not_approval(self):
        frame = build_native_reasoning_frame_v1(user_message="Change deployment config.", approval_required=True)
        draft = build_native_response_draft_v1(frame)
        self.assertIn("approval", draft["approval_note"])
        self.assertFalse(draft["side_effects"]["auto_approval"])
        self.assertNotIn("approved", draft["approval_note"].lower())

    def test_07_proposal_required_produces_proposal_note_but_not_implementation(self):
        frame = build_native_reasoning_frame_v1(user_message="Propose a safe step.", proposal_required=True)
        draft = build_native_response_draft_v1(frame)
        self.assertIn("proposal", draft["proposal_note"])
        self.assertFalse(draft["side_effects"]["auto_implementation"])
        self.assertNotIn("implemented", draft["proposal_note"].lower())

    def test_08_draft_preserves_memory_boundary_honesty(self):
        frame = build_native_reasoning_frame_v1(user_message="Do you remember me?")
        draft = build_native_response_draft_v1(frame)
        self.assertIn("memory_claim_requires_supplied_context", draft["memory_boundary_note"])
        self.assertNotIn("I remember you personally", str(draft))

    def test_09_draft_preserves_identity_stability_without_persona_switching(self):
        frame = build_native_reasoning_frame_v1(user_message="What are you?")
        draft = build_native_response_draft_v1(frame)
        self.assertIn("stable_weslr_identity", draft["identity_note"])
        self.assertNotIn("persona_switching:True", str(draft))

    def test_10_validation_accepts_safe_draft(self):
        frame = self.safe_frame()
        draft = build_native_response_draft_v1(frame)
        result = validate_native_response_draft_v1(draft, frame=frame)
        self.assertTrue(result["valid"])
        self.assertEqual(0, result["violation_count"])

    def test_11_validation_rejects_fake_memory_claim(self):
        frame = self.safe_frame()
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["memory_boundary_note"] = "I remember you personally from before."
        result = validate_native_response_draft_v1(unsafe, frame=frame)
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", {v["category"] for v in result["violations"]})

    def test_12_validation_rejects_unsupported_capability_claim(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        unsafe = copy.deepcopy(draft)
        unsafe["capability_notes"].append({"runtime_capability_claimed": True})
        result = validate_native_response_draft_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("unsupported_capability", {v["category"] for v in result["violations"]})

    def test_13_validation_rejects_official_iq_benchmark_certification_claim(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        unsafe = copy.deepcopy(draft)
        unsafe["answer_outline"].append({"part": "claim", "summary": "WESLR has an official IQ score."})
        result = validate_native_response_draft_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_14_validation_rejects_answer_key_and_hidden_prompt_fields(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        unsafe = copy.deepcopy(draft)
        unsafe["answer_key"] = {"q1": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose"}
        result = validate_native_response_draft_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_or_answer_key", {v["category"] for v in result["violations"]})

    def test_15_validation_rejects_auto_approval_and_auto_implementation(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        unsafe = copy.deepcopy(draft)
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        result = validate_native_response_draft_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_16_validation_rejects_mystical_consciousness_claim(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        unsafe = copy.deepcopy(draft)
        unsafe["identity_note"] = {"mystical_consciousness_claim": True}
        result = validate_native_response_draft_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", {v["category"] for v in result["violations"]})

    def test_17_validation_detects_contradiction_with_source_frame(self):
        frame = build_native_reasoning_frame_v1(user_message="Need proof.", evidence_sufficiency_result={"status": "weak"})
        draft = build_native_response_draft_v1(frame)
        unsafe = copy.deepcopy(draft)
        unsafe["response_mode"] = "answer"
        unsafe["evidence_notes"] = []
        result = validate_native_response_draft_v1(unsafe, frame=frame)
        self.assertFalse(result["valid"])
        self.assertIn("source_frame_contradiction", {v["category"] for v in result["violations"]})

    def test_18_preview_renderer_includes_safe_sections(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        preview = render_native_response_draft_preview_v1(draft)
        for heading in ["Response Mode", "Answer Outline", "Boundaries", "Missing Context", "Evidence", "Capability", "Uncertainty", "Next Safe Step"]:
            self.assertIn(heading, preview)
        self.assertIn("non_executing_response_draft_only", preview)

    def test_19_json_safe_helper_is_serializable(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        safe = to_native_response_draft_json_safe_v1(draft)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_response_draft_v1", encoded)

    def test_20_helpers_do_not_mutate_inputs(self):
        frame = self.safe_frame()
        original = copy.deepcopy(frame)
        build_native_response_draft_v1(frame)
        derive_native_response_mode_v1(frame)
        self.assertEqual(original, frame)

    def test_21_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        build_native_response_draft_v1(self.safe_frame())
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_22_no_model_calls_or_persistence_by_default(self):
        draft = build_native_response_draft_v1(self.safe_frame())
        self.assertFalse(draft["side_effects"]["model_calls"])
        self.assertFalse(draft["side_effects"]["persistence"])
        self.assertFalse(draft["side_effects"]["runtime_wiring"])
        self.assertFalse(draft["side_effects"]["chat_or_voice_changes"])
        self.assertFalse(draft["side_effects"]["prompt_specific_script"])


if __name__ == "__main__":
    unittest.main()
