#!/usr/bin/env python3
"""Focused tests for WESLR native response dry vertical slice helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_response_dry_slice import (  # noqa: E402
    build_native_response_dry_slice_v1,
    render_native_response_dry_slice_markdown_v1,
    summarize_native_response_dry_slice_v1,
    to_native_response_dry_slice_json_safe_v1,
    validate_native_response_dry_slice_v1,
)


class NativeResponseDrySliceV1Tests(unittest.TestCase):
    def safe_slice(self):
        return build_native_response_dry_slice_v1(
            user_message="Prepare a safe bounded answer.",
            known_context=["operator requested dry slice"],
            provenance_refs=["operator_supplied_context"],
        )

    def test_01_dry_slice_builds_full_chain_from_minimal_safe_inputs(self):
        result = self.safe_slice()
        self.assertEqual("native_response_dry_vertical_slice_v1", result["slice_type"])
        self.assertEqual("candidate_ready_for_preview", result["slice_status"])
        self.assertEqual("accepted", result["validation_status"]["validation_status"])

    def test_02_dry_slice_produces_frame_draft_self_check_candidate(self):
        result = self.safe_slice()
        for key in ["frame", "draft", "self_check", "candidate"]:
            self.assertIsInstance(result[key], dict)
            self.assertTrue(result[key])

    def test_03_ids_line_up_across_chain(self):
        result = self.safe_slice()
        frame = result["frame"]
        draft = result["draft"]
        self_check = result["self_check"]
        candidate = result["candidate"]
        self.assertEqual(frame["frame_id"], draft["source_frame_id"])
        self.assertEqual(frame["frame_id"], self_check["frame_id"])
        self.assertEqual(draft["draft_id"], self_check["draft_id"])
        self.assertEqual(frame["frame_id"], candidate["source_frame_id"])
        self.assertEqual(draft["draft_id"], candidate["source_draft_id"])
        self.assertEqual(self_check["self_check_id"], candidate["source_self_check_id"])

    def test_04_sufficient_context_produces_preview_ready_candidate(self):
        result = self.safe_slice()
        self.assertEqual("candidate_ready_for_preview", result["slice_status"])
        self.assertTrue(result["safe_to_preview"])
        self.assertTrue(result["candidate"]["safe_to_preview"])

    def test_05_missing_context_produces_insufficient_context_or_revision_path(self):
        result = build_native_response_dry_slice_v1(user_message="Answer?", missing_context=["subject"])
        self.assertIn(result["slice_status"], {"insufficient_context", "revision_required"})
        self.assertTrue(result["frame"]["missing_context"])

    def test_06_evidence_required_input_produces_evidence_required_path(self):
        result = build_native_response_dry_slice_v1(
            user_message="Prove this.",
            known_context=["hypothesis only"],
            evidence_sufficiency_result={"status": "weak", "needed": ["direct observation"]},
        )
        self.assertEqual("evidence_required", result["slice_status"])
        self.assertEqual("evidence_required", result["draft"]["response_mode"])

    def test_07_capability_boundary_blocks_overclaiming(self):
        result = build_native_response_dry_slice_v1(
            user_message="Run external calculation.",
            known_context=["calculation request"],
            capability_match={"requires_tool": True},
        )
        capability = " ".join(result["candidate"]["response_sections"]["capability"])
        self.assertIn("requires_tool", capability)
        self.assertNotIn("can execute", str(result).lower())

    def test_08_approval_required_does_not_imply_approval(self):
        result = build_native_response_dry_slice_v1(user_message="Change config.", approval_required=True)
        self.assertTrue(result["frame"]["approval_required"])
        self.assertFalse(result["side_effects"]["auto_approval"])
        self.assertNotIn("approved for execution", str(result).lower())

    def test_09_proposal_required_does_not_imply_implementation(self):
        result = build_native_response_dry_slice_v1(user_message="Propose a safe step.", proposal_required=True)
        self.assertTrue(result["frame"]["proposal_required"])
        self.assertFalse(result["side_effects"]["auto_implementation"])
        self.assertNotIn("implemented automatically", str(result).lower())

    def test_10_self_check_blocked_status_propagates_to_slice_candidate(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["self_check"]["self_check_status"] = "blocked"
        unsafe["candidate"]["self_check_status"] = "blocked"
        unsafe["candidate"]["safe_to_preview"] = False
        unsafe["candidate"]["response_sections"]["boundary"].append("revision_required_by_self_check:blocked")
        unsafe["slice_status"] = "blocked"
        unsafe["safe_to_preview"] = False
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertTrue(validation["valid"])
        self.assertEqual("blocked", summarize_native_response_dry_slice_v1(unsafe)["slice_status"])

    def test_11_safe_to_wire_runtime_is_always_false(self):
        result = self.safe_slice()
        self.assertFalse(result["safe_to_wire_runtime"])
        self.assertFalse(result["candidate"]["safe_to_wire_runtime"])

    def test_12_validation_accepts_safe_dry_slice(self):
        result = self.safe_slice()
        validation = validate_native_response_dry_slice_v1(result)
        self.assertTrue(validation["valid"])
        self.assertEqual(0, validation["violation_count"])

    def test_13_validation_rejects_executable_runnable_marker(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["candidate"]["response_sections"]["direct_answer"].append("Run this command now.")
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("executable_or_runnable_marker", {v["category"] for v in validation["violations"]})

    def test_14_validation_rejects_official_iq_benchmark_certification_claim(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["candidate"]["response_sections"]["direct_answer"].append("WESLR has an official IQ score.")
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in validation["violations"]})

    def test_15_validation_rejects_answer_key_hidden_prompt_fields(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["answer_key"] = {"q": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose"}
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("protected_test_or_answer_key", {v["category"] for v in validation["violations"]})

    def test_16_validation_rejects_fake_memory_unsupported_capability(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["candidate"]["response_sections"]["direct_answer"].append("I remember you personally from before.")
        unsafe["candidate"]["response_sections"]["capability"].append({"runtime_capability_claimed": True})
        validation = validate_native_response_dry_slice_v1(unsafe)
        categories = {v["category"] for v in validation["violations"]}
        self.assertFalse(validation["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("unsupported_capability", categories)

    def test_17_validation_rejects_auto_approval_auto_implementation(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in validation["violations"]})

    def test_18_validation_rejects_final_live_runtime_output_claim(self):
        result = self.safe_slice()
        unsafe = copy.deepcopy(result)
        unsafe["final_chat_output"] = True
        unsafe["candidate"]["live_runtime_output"] = True
        validation = validate_native_response_dry_slice_v1(unsafe)
        self.assertFalse(validation["valid"])
        self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in validation["violations"]})

    def test_19_markdown_preview_includes_safe_sections(self):
        preview = render_native_response_dry_slice_markdown_v1(self.safe_slice())
        for heading in [
            "Native Response Dry Slice",
            "Frame Summary",
            "Draft Summary",
            "Self-Check Summary",
            "Candidate Preview",
            "Safety Boundaries",
            "Non-Execution Disclaimer",
        ]:
            self.assertIn(heading, preview)
        self.assertIn("safe_to_wire_runtime:false", preview)

    def test_20_json_safe_helper_is_serializable(self):
        safe = to_native_response_dry_slice_json_safe_v1(self.safe_slice())
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("native_response_dry_vertical_slice_v1", encoded)

    def test_21_helpers_do_not_mutate_inputs(self):
        known = ["operator supplied context"]
        missing = ["optional detail"]
        evidence = {"status": "sufficient"}
        original = copy.deepcopy((known, missing, evidence))
        build_native_response_dry_slice_v1(user_message="Answer safely.", known_context=known, missing_context=missing, evidence_sufficiency_result=evidence)
        self.assertEqual(original, (known, missing, evidence))

    def test_22_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.safe_slice()
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_23_no_model_calls(self):
        result = self.safe_slice()
        self.assertFalse(result["side_effects"]["model_calls"])
        self.assertFalse(result["frame"]["side_effects"]["model_calls"])
        self.assertFalse(result["candidate"]["side_effects"]["model_calls"])

    def test_24_no_persistence_file_creation_by_default(self):
        result = self.safe_slice()
        self.assertFalse(result["side_effects"]["persistence"])
        self.assertFalse(result["side_effects"]["weslr_runtime_state_created"])
        self.assertFalse(result["candidate"]["side_effects"]["persistence"])

    def test_25_no_prompt_specific_hardcoded_chatbot_script_added(self):
        result = self.safe_slice()
        self.assertFalse(result["side_effects"]["prompt_specific_script"])
        self.assertNotIn("if user asks", str(result).lower())
        self.assertNotIn("elif", str(result).lower())


if __name__ == "__main__":
    unittest.main()
