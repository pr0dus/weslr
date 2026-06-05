#!/usr/bin/env python3
"""Focused tests for WESLR project start chat flow metadata v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.project_start_chat_flow_metadata import (  # noqa: E402
    FLOW_TYPE_V1,
    SCHEMA_VERSION_V1,
    build_initial_project_start_chat_flow_examples_v1,
    build_project_start_chat_flow_packet_v1,
    build_project_start_clarification_prompt_metadata_v1,
    build_project_start_status_phrase_metadata_v1,
    classify_project_start_intent_v1,
    summarize_project_start_chat_flow_packet_v1,
    to_project_start_chat_flow_json_safe_v1,
    validate_project_start_chat_flow_packet_v1,
)


class ProjectStartChatFlowMetadataV1Tests(unittest.TestCase):
    def _packet(self, **kwargs):
        base = {
            "requested_action": "Start a new project with Weslr",
            "owner_user_scope": "self",
            "tenant_account_scope": "self",
            "project_id": "project_alpha",
            "session_id": "session_alpha",
            "source_type": "synthetic",
            "source_ref": "test-source-1",
            "goal": "build a safe project intake packet",
            "scope": "bounded",
            "constraints": ["metadata only"],
            "success_criteria": "packet validates",
            "known_inputs": ["goal"],
            "desired_output": "metadata packet",
            "deadline_or_priority": "soon",
            "approval_needed": "yes",
            "privacy_sensitivity": "low",
            "tool_use_expectation": "metadata only",
        }
        base.update(kwargs)
        return build_project_start_chat_flow_packet_v1(**base)

    def test_01_classifies_new_project_start(self):
        result = classify_project_start_intent_v1(
            requested_action="Start a new project with Weslr",
            goal="build a safe project intake packet",
            desired_output="metadata packet",
            tool_use_expectation="metadata only",
        )
        self.assertEqual(result["intent_class"], "new_project_start")

    def test_02_classifies_continue_existing_project(self):
        result = classify_project_start_intent_v1(
            requested_action="Continue existing project project_alpha",
            project_id="project_alpha",
            goal="review the current project",
        )
        self.assertEqual(result["intent_class"], "continue_existing_project")

    def test_03_classifies_project_clarification(self):
        result = classify_project_start_intent_v1(
            requested_action="I need clarification about the project setup",
            goal="clarify the start request",
        )
        self.assertEqual(result["intent_class"], "project_clarification")

    def test_04_classifies_project_planning_request(self):
        result = classify_project_start_intent_v1(
            requested_action="Please plan the project steps and roadmap",
            goal="plan the work",
            scope="bounded",
            desired_output="roadmap",
        )
        self.assertEqual(result["intent_class"], "project_planning_request")

    def test_05_classifies_project_gap_review_request(self):
        result = classify_project_start_intent_v1(
            requested_action="Review gaps and blind spots in the project",
            goal="review gaps",
            scope="bounded",
        )
        self.assertEqual(result["intent_class"], "project_gap_review_request")

    def test_06_classifies_memory_update_proposal_request(self):
        result = classify_project_start_intent_v1(
            requested_action="Please remember this and update memory metadata",
            goal="remember this",
        )
        self.assertEqual(result["intent_class"], "memory_update_proposal_request")

    def test_07_classifies_tool_action_request(self):
        result = classify_project_start_intent_v1(
            requested_action="Run the tool and execute the action",
            tool_use_expectation="execute tool",
        )
        self.assertEqual(result["intent_class"], "tool_action_request")

    def test_08_unknown_or_ambiguous_intent_fails_closed_with_clarification(self):
        result = classify_project_start_intent_v1(requested_action="maybe something project-ish")
        self.assertEqual(result["intent_class"], "unknown_or_ambiguous")
        self.assertTrue(result["clarification_questions"])
        self.assertTrue(result["requires_user_confirmation"])

    def test_09_valid_packet_build(self):
        packet = self._packet()
        validation = validate_project_start_chat_flow_packet_v1(packet)
        self.assertTrue(validation["valid"])
        self.assertEqual(packet["schema_version"], SCHEMA_VERSION_V1)
        self.assertEqual(packet["flow_type"], FLOW_TYPE_V1)

    def test_10_json_safety(self):
        packet = self._packet()
        safe = to_project_start_chat_flow_json_safe_v1(packet)
        json.dumps(safe)
        self.assertIsInstance(safe, dict)

    def test_11_missing_owner_scope_source_like_fields_fail_closed(self):
        packet = build_project_start_chat_flow_packet_v1(requested_action="Start a new project")
        validation = validate_project_start_chat_flow_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_12_new_project_creates_candidate_only_not_real_project_mutation(self):
        packet = self._packet(project_id="")
        self.assertIn(packet["project_state_candidate"]["project_status"], {"proposed", "pending_approval"})
        self.assertEqual(packet["project_state_candidate"]["state_kind"], "project_context")
        self.assertIn("candidate", packet["project_state_candidate"]["source_type"])

    def test_13_continue_existing_project_requires_project_id_or_clarification(self):
        packet = build_project_start_chat_flow_packet_v1(
            requested_action="Continue existing project project_alpha",
            owner_user_scope="self",
            tenant_account_scope="self",
            project_id="",
            session_id="session_alpha",
            source_type="synthetic",
            source_ref="test-source-2",
            goal="review current project",
            scope="bounded",
            constraints=["metadata only"],
            success_criteria="gaps identified",
            known_inputs=["existing project"],
            desired_output="gap review packet",
            deadline_or_priority="medium",
            approval_needed="yes",
            privacy_sensitivity="low",
            tool_use_expectation="metadata only",
        )
        validation = validate_project_start_chat_flow_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertTrue(packet["clarification_questions"])

    def test_14_missing_fields_produce_clarification_questions(self):
        questions = build_project_start_clarification_prompt_metadata_v1(["goal", "desired_output"])
        self.assertIn("What is the goal?", questions)
        self.assertIn("What output do you want?", questions)

    def test_15_privacy_sensitive_project_requires_confirmation_before_deeper_analysis(self):
        result = classify_project_start_intent_v1(
            requested_action="Review gaps in a private project",
            goal="review gaps",
            privacy_sensitivity="high",
            scope="bounded",
        )
        self.assertTrue(result["requires_user_confirmation"])
        self.assertTrue(result["requires_operator_approval"])

    def test_16_memory_update_remains_proposal(self):
        packet = self._packet(requested_action="Please remember this", goal="remember this")
        self.assertEqual(packet["memory_state_candidates"][0]["status"], "proposed")
        self.assertTrue(packet["memory_state_candidates"][0]["pending_approval"])

    def test_17_project_state_remains_candidate_provisional_metadata(self):
        packet = self._packet()
        self.assertIn(packet["project_state_candidate"]["project_status"], {"proposed", "pending_approval"})
        self.assertIn(packet["project_state_candidate"]["project_phase"], {"intake", "clarification", "planning", "review"})

    def test_18_tool_action_becomes_contract_candidate_not_execution(self):
        packet = self._packet(requested_action="Run the tool and execute the action", tool_use_expectation="execute tool")
        self.assertTrue(packet["tool_lane_contract_candidates"])
        self.assertEqual(packet["tool_lane_contract_candidates"][0]["lane_id"], "draft_artifact_creation")

    def test_19_surface_gap_review_allowed_as_metadata_only(self):
        result = classify_project_start_intent_v1(
            requested_action="Review gaps and blind spots in the project",
            goal="review gaps",
            scope="bounded",
        )
        self.assertEqual(result["allowed_next_step"], "surface_gap_review_metadata")
        self.assertTrue(result["requires_user_confirmation"])

    def test_20_deeper_analysis_requires_explicit_approval(self):
        result = classify_project_start_intent_v1(
            requested_action="Review gaps and blind spots in the project",
            goal="review gaps",
            scope="bounded",
        )
        self.assertTrue(result["requires_operator_approval"])

    def test_21_user_visible_status_phrase_does_not_reveal_private_mechanism_names(self):
        phrase = build_project_start_status_phrase_metadata_v1(
            "project_gap_review_request",
            pending_approval=True,
            requires_user_confirmation=True,
            requires_operator_approval=True,
            blocked_reason="metadata only",
            missing_project_fields=["goal"],
        )
        self.assertNotIn("chat responder", phrase.lower())
        self.assertNotIn("runtime wiring", phrase.lower())
        self.assertNotIn("fake continuity", phrase.lower())

    def test_22_user_visible_phrase_does_not_contain_unknown_engine(self):
        packet = self._packet(requested_action="Review gaps in the project")
        self.assertNotIn("Unknown Engine", packet["user_visible_status_phrase"])

    def test_23_denied_authority_fields_remain_false_blocked(self):
        packet = self._packet()
        denied = packet["denied_authority"]
        self.assertTrue(denied)
        self.assertTrue(all(value is False for value in denied.values()))

    def test_24_no_hidden_memory(self):
        packet = self._packet()
        self.assertNotIn("hidden_memory", packet["user_visible_status_phrase"].lower())
        self.assertNotIn("hidden_memory", packet["operator_visible_summary"].lower())

    def test_25_no_fake_continuity(self):
        packet = self._packet()
        self.assertNotIn("fake continuity", json.dumps(packet).lower())

    def test_26_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "project_start_chat_flow_metadata.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_27_no_runtime_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "project_start_chat_flow_metadata.py").read_text(encoding="utf-8")
        for needle in ("chat_responder", "main.py", "dialogue", "chat_ui"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_28_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_29_examples_are_synthetic_only(self):
        examples = build_initial_project_start_chat_flow_examples_v1()
        self.assertTrue(examples)
        self.assertTrue(all(example["source_type"] == "synthetic" for example in examples))

    def test_30_summary_is_compact_and_json_safe(self):
        packet = self._packet()
        summary = summarize_project_start_chat_flow_packet_v1(packet)
        json.dumps(summary)
        self.assertIn("intent_class", summary)
        self.assertIn("flow_id", summary)
        self.assertLessEqual(len(summary), 16)

    def test_31_invalid_packet_fails_closed(self):
        packet = self._packet()
        packet.pop("schema_version")
        validation = validate_project_start_chat_flow_packet_v1(packet)
        self.assertFalse(validation["valid"])
        self.assertGreater(validation["violation_count"], 0)

    def test_32_validation_returns_metadata_not_normal_exceptions(self):
        validation = validate_project_start_chat_flow_packet_v1({"not": "a packet"})
        self.assertIsInstance(validation, dict)
        self.assertFalse(validation["valid"])
        self.assertIn("violations", validation)

    def test_33_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "project_start_chat_flow_metadata.py").read_text(encoding="utf-8")
        for needle in ("open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
