#!/usr/bin/env python3
"""Focused tests for WESLR Frontier Intelligence preview surface helpers V1."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.native_response_dry_slice import build_native_response_dry_slice_v1  # noqa: E402
from weslr.frontier_intelligence_preview_surface import (  # noqa: E402
    build_frontier_intelligence_preview_card_v1,
    build_frontier_intelligence_preview_overview_v1,
    render_frontier_intelligence_preview_markdown_v1,
    to_frontier_intelligence_preview_json_safe_v1,
    validate_frontier_intelligence_preview_surface_v1,
)


class FrontierIntelligencePreviewSurfaceV1Tests(unittest.TestCase):
    def safe_slice(self):
        return build_native_response_dry_slice_v1(
            user_message="Prepare a safe bounded answer.",
            known_context=["operator requested preview surface"],
            provenance_refs=["operator_supplied_context"],
        )

    def safe_card(self):
        return build_frontier_intelligence_preview_card_v1(self.safe_slice())

    def test_01_preview_card_builds_from_safe_dry_slice(self):
        dry = self.safe_slice()
        card = build_frontier_intelligence_preview_card_v1(dry)
        self.assertEqual("frontier_intelligence_preview_card_v1", card["card_type"])
        self.assertEqual(dry["slice_id"], card["source_slice_id"])
        self.assertEqual("accepted", card["validation_status"]["validation_status"])

    def test_02_preview_card_includes_frame_draft_self_check_candidate_summaries(self):
        card = self.safe_card()
        for key in ["frame_summary", "draft_summary", "self_check_summary", "candidate_summary"]:
            self.assertIsInstance(card[key], dict)
            self.assertTrue(card[key])

    def test_03_preview_card_preserves_safe_to_wire_runtime_false(self):
        self.assertFalse(self.safe_card()["safe_to_wire_runtime"])

    def test_04_preview_overview_combines_multiple_cards_deterministically(self):
        one = self.safe_card()
        two = build_frontier_intelligence_preview_card_v1(build_native_response_dry_slice_v1(user_message="Need detail?", missing_context=["subject"]))
        overview_a = build_frontier_intelligence_preview_overview_v1([two, one])
        overview_b = build_frontier_intelligence_preview_overview_v1([one, two])
        self.assertEqual(2, overview_a["total_cards"])
        self.assertEqual(overview_a["card_ids"], overview_b["card_ids"])
        self.assertEqual(overview_a["status_counts"], overview_b["status_counts"])

    def test_05_blocked_revision_required_dry_slice_is_reflected_safely(self):
        dry = self.safe_slice()
        blocked = copy.deepcopy(dry)
        blocked["slice_status"] = "blocked"
        blocked["safe_to_preview"] = False
        blocked["self_check"]["self_check_status"] = "blocked"
        blocked["candidate"]["self_check_status"] = "blocked"
        blocked["candidate"]["safe_to_preview"] = False
        card = build_frontier_intelligence_preview_card_v1(blocked)
        self.assertEqual("blocked", card["slice_status"])
        self.assertFalse(card["safe_to_preview"])

    def test_06_missing_context_is_shown_without_fabricating_memory(self):
        dry = build_native_response_dry_slice_v1(user_message="Do you remember me?", missing_context=["verified memory record"])
        card = build_frontier_intelligence_preview_card_v1(dry)
        self.assertTrue(card["missing_context_summary"])
        self.assertNotIn("I remember you personally", str(card))

    def test_07_evidence_required_status_is_shown_without_overclaiming(self):
        dry = build_native_response_dry_slice_v1(
            user_message="Prove it.",
            known_context=["hypothesis only"],
            evidence_sufficiency_result={"status": "weak", "needed": ["direct observation"]},
        )
        card = build_frontier_intelligence_preview_card_v1(dry)
        self.assertEqual("evidence_required", card["slice_status"])
        self.assertTrue(card["evidence_summary"])
        self.assertNotIn("proven", str(card).lower())

    def test_08_capability_boundary_is_shown_without_unsupported_capability_claims(self):
        dry = build_native_response_dry_slice_v1(
            user_message="Run external calculation.",
            known_context=["calculation request"],
            capability_match={"requires_tool": True},
        )
        card = build_frontier_intelligence_preview_card_v1(dry)
        self.assertIn("requires_tool", " ".join(card["capability_boundary_summary"]))
        self.assertNotIn("can execute", str(card).lower())

    def test_09_markdown_renderer_includes_safe_sections(self):
        markdown = render_frontier_intelligence_preview_markdown_v1(self.safe_card())
        for heading in ["Frontier Intelligence Preview", "Understanding", "Known Context", "Missing Context", "Evidence", "Capability Boundary", "Candidate Preview", "Self-Check Status", "Next Safe Step", "Non-Runtime Boundary"]:
            self.assertIn(heading, markdown)

    def test_10_markdown_renderer_omits_hidden_answer_official_runtime_claims(self):
        markdown = render_frontier_intelligence_preview_markdown_v1(self.safe_card()).lower()
        self.assertNotIn("hidden prompt", markdown)
        self.assertNotIn("answer key", markdown)
        self.assertNotIn("official iq", markdown)
        self.assertNotIn("runtime-wired", markdown)
        self.assertNotIn("final live output", markdown)

    def test_11_json_safe_helper_is_serializable(self):
        safe = to_frontier_intelligence_preview_json_safe_v1(self.safe_card())
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("frontier_intelligence_preview_card_v1", encoded)

    def test_12_validation_accepts_safe_preview_card_and_overview(self):
        card = self.safe_card()
        overview = build_frontier_intelligence_preview_overview_v1([card])
        self.assertTrue(validate_frontier_intelligence_preview_surface_v1(card)["valid"])
        self.assertTrue(validate_frontier_intelligence_preview_surface_v1(overview)["valid"])

    def test_13_validation_rejects_safe_to_wire_runtime_true(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["safe_to_wire_runtime"] = True
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_14_validation_rejects_final_live_output_claim(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["final_chat_output"] = True
        unsafe["candidate_summary"]["live_runtime_output"] = True
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("runtime_or_persistence_authorization_drift", {v["category"] for v in result["violations"]})

    def test_15_validation_rejects_official_iq_benchmark_certification_claim(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["candidate_preview_summary"].append("WESLR has an official IQ score.")
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("official_iq_benchmark_or_certification", {v["category"] for v in result["violations"]})

    def test_16_validation_rejects_fake_memory_fake_self_awareness_mystical_claim(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["candidate_preview_summary"].append("I remember you personally from before.")
        unsafe["frame_summary"]["fake_self_awareness_claim"] = True
        unsafe["candidate_summary"]["mystical_consciousness_claim"] = True
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("fake_memory", categories)
        self.assertIn("fake_self_awareness", categories)
        self.assertIn("mystical_consciousness_or_official_test_pass_claim", categories)

    def test_17_validation_rejects_auto_approval_auto_implementation(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["auto_approved"] = True
        unsafe["auto_implemented"] = True
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        self.assertFalse(result["valid"])
        self.assertIn("auto_approval_or_auto_implementation", {v["category"] for v in result["violations"]})

    def test_18_validation_rejects_answer_key_hidden_prompt_score_and_model_call(self):
        unsafe = copy.deepcopy(self.safe_card())
        unsafe["answer_key"] = {"q": "a"}
        unsafe["nested"] = {"hidden_prompt": "do not expose", "official_score": 1, "model_call": True}
        result = validate_frontier_intelligence_preview_surface_v1(unsafe)
        categories = {v["category"] for v in result["violations"]}
        self.assertFalse(result["valid"])
        self.assertIn("protected_test_answer_key_or_score", categories)
        self.assertIn("model_call_claim", categories)

    def test_19_helpers_do_not_mutate_inputs(self):
        dry = self.safe_slice()
        original = copy.deepcopy(dry)
        build_frontier_intelligence_preview_card_v1(dry)
        build_frontier_intelligence_preview_overview_v1([dry])
        self.assertEqual(original, dry)

    def test_20_helpers_do_not_create_weslr_runtime_state(self):
        state_dir = ROOT / ".weslr"
        before = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.safe_card()
        after = sorted(p.relative_to(state_dir).as_posix() for p in state_dir.rglob("*")) if state_dir.exists() else []
        self.assertEqual(before, after)

    def test_21_no_model_calls(self):
        card = self.safe_card()
        self.assertFalse(card["side_effects"]["model_calls"])

    def test_22_no_persistence_file_creation_by_default(self):
        card = self.safe_card()
        self.assertFalse(card["side_effects"]["persistence"])
        self.assertFalse(card["side_effects"]["weslr_runtime_state_created"])

    def test_23_no_prompt_specific_hardcoded_chatbot_script_added(self):
        card = self.safe_card()
        self.assertFalse(card["side_effects"]["prompt_specific_script"])
        self.assertNotIn("if user asks", str(card).lower())
        self.assertNotIn("elif", str(card).lower())


if __name__ == "__main__":
    unittest.main()
