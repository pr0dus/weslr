#!/usr/bin/env python3
"""Focused tests for WESLR native response assembly helpers V1."""

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
from weslr.native_response_self_check import build_native_response_self_check_result_v1  # noqa: E402
from weslr.native_response_assembly import (  # noqa: E402
    assemble_native_response_candidate_v1,
    derive_native_response_sections_v1,
    render_native_response_candidate_preview_v1,
    to_native_response_candidate_json_safe_v1,
    validate_native_response_candidate_v1,
)


class NativeResponseAssemblyV1Tests(unittest.TestCase):
    def safe_chain(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Prepare a safe bounded answer.",
            known_context=["operator requested helper-only assembly"],
            provenance_refs=["operator_supplied_context"],
        )
        draft = build_native_response_draft_v1(frame)
        self_check = build_native_response_self_check_result_v1(frame, draft)
        return frame, draft, self_check

    def candidate_for(self, frame=None, draft=None, self_check=None):
        if frame is None or draft is None or self_check is None:
            frame, draft, self_check = self.safe_chain()
        return assemble_native_response_candidate_v1(frame, draft, self_check)

    def test_01_assembles_candidate_from_aligned_safe_frame_draft_self_check(self):
        frame, draft, self_check = self.safe_chain()
        candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
        self.assertEqual("native_response_candidate_v1", candidate["candidate_type"])
        self.assertEqual(frame["frame_id"], candidate["source_frame_id"])
        self.assertEqual(draft["draft_id"], candidate["source_draft_id"])
        self.assertEqual(self_check["self_check_id"], candidate["source_self_check_id"])
        self.assertEqual("accepted", candidate["validation_status"]["validation_status"])

    def test_02_derives_missing_context_section_when_draft_mode_requires_clarification(self):
        frame = build_native_reasoning_frame_v1(user_message="Answer?", missing_context=["question subject"])
        draft = build_native_response_draft_v1(frame)
        self_check = build_native_response_self_check_result_v1(frame, draft)
        sections = derive_native_response_sections_v1(frame, draft, self_check)
        self.assertTrue(sections["missing_context"])
        self.assertIn(draft["response_mode"], {"insufficient_context", "clarify"})

    def test_03_derives_evidence_section_when_evidence_is_required(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Prove this.",
            known_context=["hypothesis only"],
            evidence_sufficiency_result={"status": "weak", "needed": ["direct observation"]},
        )
        draft = build_native_response_draft_v1(frame)
        self_check = build_native_response_self_check_result_v1(frame, draft)
        sections = derive_native_response_sections_v1(frame, draft, self_check)
        self.assertTrue(sections["evidence"])
        self.assertEqual("evidence_required", draft["response_mode"])

    def test_04_derives_capability_boundary_section_without_overclaiming(self):
        frame = build_native_reasoning_frame_v1(
            user_message="Run the external calculation.",
            capability_match={"requires_tool": True},
            known_context=["calculation request"],
        )
        draft = build_native_response_draft_v1(frame)
        self_check = build_native_response_self_check_result_v1(frame, draft)
        candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
        capability = " ".join(candidate["response_sections"]["capability"])
        self.assertIn("requires_tool", capability)
        self.assertNotIn("can execute", str(candidate).lower())

    def test_05_derives_approval_proposal_section_without_approval_or_implementation(self):
        frame = build_native_reasoning_frame_v1(user_message="Propose a config change.", approval_required=True, proposal_required=True)
        draft = build_native_response_draft_v1(frame)
        self_check = build_native_response_self_check_result_v1(frame, draft)
        candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
        notes = " ".join(candidate["response_sections"]["proposal_or_approval"]).lower()
        self.assertIn("approval", notes)
        self.assertIn("proposal", notes)
        self.assertFalse(candidate["side_effects"]["auto_approval"])
        self.assertFalse(candidate["side_effects"]["auto_implementation"])

    def test_06_candidate_marks_safe_to_wire_runtime_false(self):
        self.assertFalse(self.candidate_for()["safe_to_wire_runtime"])

    def test_07_candidate_is_not_final_or_live_runtime_output(self):
        candidate = self.candidate_for()
        self.assertFalse(candidate["final_chat_output"])
        self.assertFalse(candidate["live_runtime_output"])
        self.assertEqual("non_executing_response_candidate_only", candidate["execution_status"])

    def test_08_candidate_reflects_self_check_blocked_revision_required_status(self):
        frame, draft, _ = self.safe_chain()
        unsafe = copy.deepcopy(draft)
        unsafe["answer_outline"].append({"summary": "official benchmark score"})
        self_check = build_native_response_self_check_result_v1(frame, unsafe)
        candidate = assemble_native_response_candidate_v1(frame, unsafe, self_check)
        self.assertEqual("blocked", candidate["self_check_status"])
        self.assertFalse(candidate["safe_to_preview"])
        self.assertIn("revision_required", " ".join(candidate["response_sections"]["boundary"]))

    def test_09_validation_accepts_safe_candidate(self):
        frame, draft, self_check = self.safe_chain()
        candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
        validation = validate_native_response_candidate_v1(candidate, frame=frame, draft=draft, self_check=self_check)
        self.assertTrue(validation["valid"])
        self.assertEqual(0, validation["violation_count"])

    def test_10_validation_rejects_fake_memory_claim(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["response_sections"]["direct_answer"].append("I remember you personally from before.")
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", {v["category"] for v in result["violations"]})

    def test_11_validation_rejects_unsupported_capability_claim(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["response_sections"]["capability"].append({"runtime_capability_claimed": True})
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("unsupported_capability", {v["category"] for v in result["violations"]})

    def test_12_validation_rejects_official_iq_benchmark_certification_claim(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["response_sections"]["direct_answer"].append("WESLR has an official IQ score.")
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_13_validation_rejects_answer_key_and_hidden_prompt_fields(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["answer_key"] = {"q": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose"}
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_or_answer_key", {v["category"] for v in result["violations"]})

    def test_14_validation_rejects_auto_approval_and_auto_implementation(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_15_validation_rejects_mystical_consciousness_claim(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["response_sections"]["direct_answer"].append({"mystical_consciousness_claim": True})
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", {v["category"] for v in result["violations"]})

    def test_16_validation_rejects_safe_to_wire_runtime_true(self):
        candidate = self.candidate_for()
        unsafe = copy.deepcopy(candidate)
        unsafe["safe_to_wire_runtime"] = True
        result = validate_native_response_candidate_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_17_validation_detects_source_id_mismatch(self):
        frame, draft, self_check = self.safe_chain()
        candidate = assemble_native_response_candidate_v1(frame, draft, self_check)
        other = build_native_reasoning_frame_v1(user_message="Different", known_context=["x"])
        result = validate_native_response_candidate_v1(candidate, frame=other, draft=draft, self_check=self_check)
        self.assertFalse(result["valid"])
        self.assertIn("source_id_mismatch", {v["category"] for v in result["violations"]})

    def test_18_preview_renderer_includes_safe_sections(self):
        preview = render_native_response_candidate_preview_v1(self.candidate_for())
        for heading in [
            "Native Response Candidate",
            "Mode",
            "Drafted Response Sections",
            "Boundaries",
            "Missing Context",
            "Evidence",
            "Capability",
            "Uncertainty",
            "Next Safe Step",
            "Self-Check Status",
            "Non-Execution Disclaimer",
        ]:
            self.assertIn(heading, preview)
        self.assertIn("safe_to_wire_runtime:false", preview)

    def test_19_json_safe_helper_is_serializable(self):
        safe = to_native_response_candidate_json_safe_v1(self.candidate_for())
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_response_candidate_v1", encoded)

    def test_20_helpers_do_not_mutate_inputs(self):
        frame, draft, self_check = self.safe_chain()
        original = copy.deepcopy((frame, draft, self_check))
        assemble_native_response_candidate_v1(frame, draft, self_check)
        derive_native_response_sections_v1(frame, draft, self_check)
        self.assertEqual(original, (frame, draft, self_check))

    def test_21_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.candidate_for()
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_22_no_model_calls(self):
        candidate = self.candidate_for()
        self.assertFalse(candidate["side_effects"]["model_calls"])

    def test_23_no_persistence_file_creation_by_default(self):
        candidate = self.candidate_for()
        self.assertFalse(candidate["side_effects"]["persistence"])
        self.assertFalse(candidate["side_effects"]["weslr_runtime_state_created"])

    def test_24_no_prompt_specific_hardcoded_chatbot_script_added(self):
        candidate = self.candidate_for()
        self.assertFalse(candidate["side_effects"]["prompt_specific_script"])
        self.assertNotIn("if user asks", str(candidate).lower())
        self.assertNotIn("elif", str(candidate).lower())


if __name__ == "__main__":
    unittest.main()
