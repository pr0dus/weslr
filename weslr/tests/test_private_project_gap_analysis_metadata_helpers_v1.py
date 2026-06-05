#!/usr/bin/env python3
"""Focused tests for WESLR private project gap analysis metadata helpers v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.private_project_gap_analysis_metadata_helpers import (  # noqa: E402
    allowed_project_gap_analysis_levels_v1,
    allowed_project_gap_approval_statuses_v1,
    allowed_project_gap_categories_v1,
    allowed_project_gap_consent_statuses_v1,
    build_initial_project_gap_analysis_examples_v1,
    build_project_gap_analysis_packet_v1,
    classify_project_gap_analysis_packet_v1,
    summarize_project_gap_analysis_packet_v1,
    to_project_gap_analysis_json_safe_v1,
    validate_project_gap_analysis_packet_v1,
)


class PrivateProjectGapAnalysisMetadataHelpersV1Tests(unittest.TestCase):
    def _surface_packet(self, **kwargs):
        base = {
            "project_id": "project_alpha",
            "owner_user_scope": "self",
            "tenant_account_scope": "self",
            "source_scope": "project_scoped",
            "analysis_level": "surface_gap_review",
            "consent_status": "not_required_for_surface",
            "approval_status": "not_required",
            "privacy_sensitivity": "low",
            "input_metadata_refs": ["synthetic:project_start:alpha"],
            "missing_fields": ["goal", "scope", "constraints"],
            "weak_evidence_items": ["goal inferred from note"],
            "blocked_items": ["tool action candidate only"],
            "safe_next_steps": ["ask clarifying questions"],
        }
        base.update(kwargs)
        return build_project_gap_analysis_packet_v1(**base)

    def _deeper_packet(self, **kwargs):
        base = {
            "project_id": "project_beta",
            "owner_user_scope": "self",
            "tenant_account_scope": "self",
            "source_scope": "project_scoped",
            "analysis_level": "deeper_gap_analysis",
            "consent_status": "granted",
            "approval_status": "user_confirmed",
            "privacy_sensitivity": "low",
            "input_metadata_refs": ["synthetic:project_state:beta", "synthetic:memory_state:beta"],
            "missing_fields": ["success_criteria", "deadline_or_priority"],
            "contradictions": ["scope is both fixed and expanding"],
            "weak_evidence_items": ["success criteria not grounded yet"],
            "safe_next_steps": ["clarify success criteria", "collect evidence"],
            "requires_user_confirmation": True,
            "deeper_analysis_available": True,
        }
        base.update(kwargs)
        return build_project_gap_analysis_packet_v1(**base)

    def _operator_packet(self, **kwargs):
        base = {
            "project_id": "project_gamma",
            "owner_user_scope": "self",
            "tenant_account_scope": "system",
            "source_scope": "system_wide_candidate",
            "analysis_level": "operator_review_required",
            "consent_status": "required",
            "approval_status": "operator_review_required",
            "privacy_sensitivity": "high",
            "input_metadata_refs": ["synthetic:operator_dashboard:gamma"],
            "blocked_items": ["cross-user data boundary"],
            "risk_flags": ["cross_user_scope", "privacy_sensitive"],
            "requires_operator_review": True,
            "deeper_analysis_available": False,
            "safe_next_steps": ["await operator review"],
        }
        base.update(kwargs)
        return build_project_gap_analysis_packet_v1(**base)

    def test_01_allowed_analysis_levels(self):
        self.assertEqual(
            allowed_project_gap_analysis_levels_v1(),
            ("surface_gap_review", "deeper_gap_analysis", "operator_review_required"),
        )

    def test_02_allowed_gap_categories(self):
        categories = allowed_project_gap_categories_v1()
        self.assertIn("missing_goal", categories)
        self.assertIn("rollout_gap", categories)
        self.assertEqual(len(categories), 20)

    def test_03_allowed_consent_and_approval_statuses(self):
        self.assertIn("granted", allowed_project_gap_consent_statuses_v1())
        self.assertIn("operator_review_required", allowed_project_gap_approval_statuses_v1())

    def test_04_valid_surface_packet(self):
        packet = self._surface_packet()
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertTrue(validation["valid"])
        self.assertEqual(packet["analysis_level"], "surface_gap_review")
        self.assertFalse(packet["requires_operator_review"])

    def test_05_valid_deeper_packet_with_approval(self):
        packet = self._deeper_packet()
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertTrue(validation["valid"])
        self.assertEqual(packet["approval_status"], "user_confirmed")
        self.assertTrue(packet["requires_user_confirmation"])

    def test_06_operator_review_required_packet(self):
        packet = self._operator_packet()
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertTrue(validation["valid"])
        self.assertEqual(packet["analysis_level"], "operator_review_required")
        self.assertTrue(packet["requires_operator_review"])

    def test_07_json_safety(self):
        packet = self._surface_packet()
        safe = to_project_gap_analysis_json_safe_v1(packet)
        json.dumps(safe)
        self.assertIsInstance(safe, dict)

    def test_08_missing_owner_scope_source_like_metadata_fails_closed(self):
        packet = build_project_gap_analysis_packet_v1(project_id="project_alpha")
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_09_unknown_analysis_level_fails_closed(self):
        packet = self._surface_packet()
        packet["analysis_level"] = "not_a_level"
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_10_unknown_gap_category_fails_closed(self):
        packet = self._surface_packet()
        packet["gap_categories"] = ["missing_goal", "not_a_gap"]
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_11_surface_review_does_not_pretend_certainty(self):
        packet = self._surface_packet()
        self.assertIn("likely gaps", packet["user_visible_summary"].lower())
        self.assertNotIn("certainty", packet["user_visible_summary"].lower())

    def test_12_surface_review_does_not_require_private_mechanism_disclosure(self):
        packet = self._surface_packet()
        self.assertNotIn("secret reasoning", packet["user_visible_summary"].lower())
        self.assertNotIn("hidden prompt", packet["user_visible_summary"].lower())

    def test_13_deeper_analysis_requires_explicit_user_approval(self):
        packet = self._deeper_packet(approval_status="pending_user_confirmation", consent_status="required", requires_user_confirmation=True)
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertTrue(validation["valid"])
        self.assertTrue(packet["requires_user_confirmation"])
        self.assertEqual(packet["approval_status"], "pending_user_confirmation")

    def test_14_privacy_sensitive_deeper_analysis_requires_confirmation(self):
        packet = self._deeper_packet(privacy_sensitivity="high", approval_status="pending_user_confirmation", consent_status="required")
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertTrue(packet["requires_user_confirmation"])
        self.assertTrue(validation["valid"])

    def test_15_cross_user_system_wide_analysis_requires_operator_review(self):
        packet = self._operator_packet()
        self.assertTrue(packet["requires_operator_review"])
        self.assertFalse(packet["deeper_analysis_available"])

    def test_16_operator_review_required_does_not_proceed_as_normal_user_visible_analysis(self):
        packet = self._operator_packet()
        self.assertIn("operator review", packet["user_visible_summary"].lower())
        self.assertNotIn("likely gaps", packet["user_visible_summary"].lower())

    def test_17_missing_evidence_is_not_invented(self):
        packet = self._surface_packet(weak_evidence_items=["missing evidence: not yet grounded"])
        self.assertIn("missing evidence", json.dumps(packet).lower())

    def test_18_contradictions_are_surfaces(self):
        packet = self._deeper_packet()
        self.assertIn("contradiction", json.dumps(packet).lower())

    def test_19_stale_context_is_surfaces(self):
        packet = self._surface_packet(risk_flags=["stale_context_detected"], gap_categories=["stale_context"])
        self.assertIn("stale_context", packet["gap_categories"])

    def test_20_tool_action_boundary_remains_approval_gated_candidate_only(self):
        packet = self._surface_packet(blocked_items=["tool action boundary candidate"], risk_flags=["approval_required_for_tool_action"])
        self.assertIn("tool_action_boundary", packet["gap_categories"])

    def test_21_external_action_boundary_remains_approval_gated_candidate_only(self):
        packet = self._surface_packet(blocked_items=["external action boundary candidate"], risk_flags=["approval_required_for_external_action"])
        self.assertIn("external_action_boundary", packet["gap_categories"])

    def test_22_user_visible_summary_is_mechanism_neutral(self):
        packet = self._surface_packet()
        self.assertNotIn("secret reasoning", packet["user_visible_summary"].lower())
        self.assertNotIn("hidden prompt", packet["user_visible_summary"].lower())

    def test_23_user_visible_summary_contains_no_unknown_engine(self):
        packet = self._surface_packet()
        self.assertNotIn("unknown engine", packet["user_visible_summary"].lower())

    def test_24_user_visible_summary_contains_no_private_mechanism_names(self):
        packet = self._surface_packet()
        self.assertNotIn("private mechanism", packet["user_visible_summary"].lower())

    def test_25_findings_include_limitations(self):
        packet = self._surface_packet()
        self.assertTrue(packet["limitations"])

    def test_26_denied_authority_fields_remain_false_blocked(self):
        packet = self._surface_packet()
        denied = packet["denied_authority"]
        self.assertTrue(denied)
        self.assertTrue(all(value is False for value in denied.values()))

    def test_27_no_project_mutation(self):
        packet = self._surface_packet()
        self.assertNotIn("project_state_mutation_authority", packet["operator_visible_summary"].lower())
        self.assertTrue(packet["denied_authority"]["project_state_mutation_authority"] is False)

    def test_28_no_memory_mutation(self):
        packet = self._surface_packet()
        self.assertTrue(packet["denied_authority"]["memory_mutation_authority"] is False)

    def test_29_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "private_project_gap_analysis_metadata_helpers.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_30_no_runtime_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "private_project_gap_analysis_metadata_helpers.py").read_text(encoding="utf-8")
        for needle in ("chat_responder", "main.py", "dialogue", "chat_ui"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_31_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_32_examples_are_synthetic_only(self):
        examples = build_initial_project_gap_analysis_examples_v1()
        self.assertTrue(examples)
        self.assertTrue(all(any(str(ref).startswith("synthetic:") for ref in example["input_metadata_refs"]) for example in examples))

    def test_33_summary_is_compact_and_json_safe(self):
        packet = self._surface_packet()
        summary = summarize_project_gap_analysis_packet_v1(packet)
        json.dumps(summary)
        self.assertIn("analysis_id", summary)
        self.assertLessEqual(len(summary), 14)

    def test_34_invalid_packet_fails_closed(self):
        packet = self._surface_packet()
        packet.pop("schema_version")
        validation = validate_project_gap_analysis_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_35_validation_returns_metadata_not_normal_exceptions(self):
        validation = validate_project_gap_analysis_packet_v1({"not": "a packet"})
        self.assertIsInstance(validation, dict)
        self.assertFalse(validation["valid"])
        self.assertIn("violations", validation)

    def test_36_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "private_project_gap_analysis_metadata_helpers.py").read_text(encoding="utf-8")
        for needle in ("open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
