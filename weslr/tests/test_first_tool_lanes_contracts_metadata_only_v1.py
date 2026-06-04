#!/usr/bin/env python3
"""Focused tests for WESLR first tool lanes metadata-only contract helpers V1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.first_tool_lanes_contracts import (  # noqa: E402
    APPROVED_FIRST_TOOL_LANES_V1,
    BLOCKED_FIRST_TOOL_LANES_V1,
    ALL_FIRST_TOOL_LANES_V1,
    build_first_tool_lane_contract_v1,
    build_initial_first_tool_lane_contract_examples_v1,
    classify_first_tool_lane_v1,
    evaluate_first_tool_lane_approval_v1,
    summarize_first_tool_lane_contract_v1,
    to_first_tool_lane_contract_json_safe_v1,
    validate_first_tool_lane_contract_v1,
)


class FirstToolLanesContractsMetadataOnlyV1Tests(unittest.TestCase):
    def contract_for(self, lane_id: str, requested_action: str | None = None, **kwargs):
        action = requested_action or lane_id.replace("_", " ")
        return build_first_tool_lane_contract_v1(
            lane_id,
            lane_id=lane_id,
            requested_action=action,
            project_id=kwargs.pop("project_id", "project_alpha"),
            memory_reference_ids=kwargs.pop("memory_reference_ids", [f"mem_{lane_id}_001"]),
            owner_user_scope=kwargs.pop("owner_user_scope", "self"),
            tenant_account_scope=kwargs.pop("tenant_account_scope", "self"),
            **kwargs,
        )

    def test_01_contract_shape_for_all_five_approved_lanes(self):
        required = {
            "schema_version",
            "lane_id",
            "lane_label",
            "action_class",
            "project_id",
            "memory_reference_ids",
            "owner_user_scope",
            "tenant_account_scope",
            "requested_action",
            "risk_level",
            "approval_status",
            "execution_status",
            "failure_count",
            "rollback_deprecation_status",
            "blocked_reason",
            "audit_note",
            "created_marker",
            "updated_marker",
            "operator_visibility",
            "user_visible_status_phrase",
            "external_action_requested",
            "destructive_action_requested",
            "third_party_action_requested",
            "runtime_activation_requested",
            "public_export_requested",
            "requires_user_confirmation",
            "requires_operator_approval",
            "requires_separate_review",
            "allowed_now",
            "denied_authority",
        }
        for lane_id in APPROVED_FIRST_TOOL_LANES_V1:
            with self.subTest(lane_id=lane_id):
                contract = self.contract_for(lane_id)
                self.assertTrue(required.issubset(contract))
                self.assertEqual(lane_id, contract["lane_id"])
                self.assertTrue(contract["operator_visibility"])

    def test_02_contract_is_json_safe(self):
        contract = self.contract_for("draft_artifact_creation")
        safe = to_first_tool_lane_contract_json_safe_v1(contract)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("draft_artifact_creation", encoded)

    def test_03_validation_rejects_missing_owner_scope_status_source_like_fields(self):
        contract = self.contract_for("project_plan_checklist")
        for field in ["owner_user_scope", "tenant_account_scope", "project_id", "approval_status", "execution_status"]:
            with self.subTest(field=field):
                broken = dict(contract)
                broken.pop(field, None)
                result = validate_first_tool_lane_contract_v1(broken)
                self.assertFalse(result["valid"])
                self.assertGreater(result["violation_count"], 0)

    def test_04_draft_lane_distinguishes_draft_from_sent_exported(self):
        contract = self.contract_for("draft_artifact_creation", requested_action="Draft a note, not send it")
        self.assertEqual("draft_artifact_creation", contract["lane_id"])
        self.assertIn("draft", contract["user_visible_status_phrase"].lower())
        self.assertIn("not send", contract["user_visible_status_phrase"].lower())
        self.assertEqual("not_required_internal_only", contract["approval_status"])

    def test_05_draft_lane_blocks_sending_publishing_external_sharing(self):
        contract = self.contract_for("draft_artifact_creation", requested_action="Send and publish externally")
        self.assertFalse(contract["allowed_now"])
        self.assertEqual("separate_review_required", contract["approval_status"])
        self.assertTrue(contract["external_action_requested"])
        self.assertTrue(contract["public_export_requested"])
        self.assertIn("blocked", contract["user_visible_status_phrase"].lower())

    def test_06_project_plan_lane_distinguishes_planning_from_execution(self):
        contract = self.contract_for("project_plan_checklist", requested_action="Create a project plan")
        self.assertEqual("planned_metadata_only", contract["execution_status"])
        self.assertEqual("this is a plan, not an executed action.", contract["user_visible_status_phrase"].lower())

    def test_07_project_plan_lane_blocks_execution_without_later_approval(self):
        contract = self.contract_for("project_plan_checklist", requested_action="Execute the plan now")
        self.assertFalse(contract["allowed_now"])
        self.assertEqual("separate_review_required", contract["approval_status"])
        self.assertEqual("blocked", contract["execution_status"])
        self.assertIn("blocked", contract["blocked_reason"].lower())

    def test_08_memory_update_proposal_stays_proposal_provisional_unless_confirmed(self):
        contract = self.contract_for("scoped_memory_project_update_proposal", requested_action="Propose a project memory update")
        self.assertEqual("proposed_metadata_only", contract["execution_status"])
        self.assertEqual("user_confirmation_required", contract["approval_status"])
        self.assertTrue(contract["requires_user_confirmation"])
        self.assertIn("memory", contract["user_visible_status_phrase"].lower())

    def test_09_memory_update_proposal_blocks_silent_global_and_cross_user_memory(self):
        contract = self.contract_for(
            "scoped_memory_project_update_proposal",
            requested_action="Propose shared cross-user memory update",
            owner_user_scope="shared",
            tenant_account_scope="system",
        )
        self.assertEqual("operator_approval_required", contract["approval_status"])
        self.assertFalse(contract["allowed_now"] is False and contract["approval_status"] != "operator_approval_required")
        self.assertTrue(contract["requires_operator_approval"])

    def test_10_internal_report_generation_is_internal_only_by_default(self):
        contract = self.contract_for("safe_internal_report_generation", requested_action="Generate an internal report")
        self.assertEqual("not_required_internal_only", contract["approval_status"])
        self.assertTrue(contract["allowed_now"])
        self.assertIn("internal report", contract["user_visible_status_phrase"].lower())

    def test_11_internal_report_generation_blocks_export_public_use_without_approval(self):
        contract = self.contract_for("safe_internal_report_generation", requested_action="Export the report publicly")
        self.assertFalse(contract["allowed_now"])
        self.assertEqual("separate_review_required", contract["approval_status"])
        self.assertEqual("blocked", contract["execution_status"])
        self.assertTrue(contract["public_export_requested"])

    def test_12_support_record_blocks_hidden_escalation_and_silent_third_party_contact(self):
        contract = self.contract_for("support_escalation_record", requested_action="Record a support escalation")
        self.assertTrue(contract["operator_visibility"])
        self.assertEqual("user_confirmation_required", contract["approval_status"])
        self.assertFalse(contract["third_party_action_requested"])
        blocked = self.contract_for("support_escalation_record", requested_action="Silently contact a third party")
        self.assertFalse(blocked["allowed_now"])
        self.assertEqual("blocked", blocked["approval_status"])
        self.assertTrue(blocked["third_party_action_requested"])

    def test_13_personal_data_inclusion_requires_user_approval_metadata(self):
        contract = self.contract_for("support_escalation_record", requested_action="Record personal data for support")
        self.assertIn(contract["approval_status"], {"user_confirmation_required", "operator_approval_required"})
        self.assertTrue(contract["requires_user_confirmation"] or contract["requires_operator_approval"])

    def test_14_external_sending_posting_lane_is_blocked_deferred(self):
        contract = self.contract_for("external_sending_posting", requested_action="Send the message")
        self.assertEqual("blocked", contract["approval_status"])
        self.assertFalse(contract["allowed_now"])
        self.assertEqual("blocked", contract["execution_status"])

    def test_15_destructive_action_lane_is_blocked(self):
        contract = self.contract_for("destructive_action", requested_action="Delete the record")
        self.assertEqual("blocked", contract["approval_status"])
        self.assertFalse(contract["allowed_now"])
        self.assertIn("destructive", contract["blocked_reason"].lower())

    def test_16_third_party_integration_lane_is_blocked(self):
        contract = self.contract_for("broad_third_party_integration", requested_action="Integrate with an external system")
        self.assertEqual("blocked", contract["approval_status"])
        self.assertFalse(contract["allowed_now"])
        self.assertTrue(contract["third_party_action_requested"])

    def test_17_runtime_chat_wiring_lane_is_blocked(self):
        contract = self.contract_for("runtime_chat_wiring", requested_action="Wire runtime chat behavior")
        self.assertEqual("blocked", contract["approval_status"])
        self.assertFalse(contract["allowed_now"])
        self.assertTrue(contract["runtime_activation_requested"])

    def test_18_public_product_readiness_lane_is_blocked(self):
        contract = self.contract_for("public_product_readiness", requested_action="Declare public product readiness")
        self.assertEqual("blocked", contract["approval_status"])
        self.assertFalse(contract["allowed_now"])
        self.assertTrue(contract["public_export_requested"])

    def test_19_approval_is_scoped_and_not_permanent_permission(self):
        internal = self.contract_for("scoped_memory_project_update_proposal", requested_action="Propose a scoped memory update")
        shared = self.contract_for(
            "scoped_memory_project_update_proposal",
            requested_action="Propose a shared memory update",
            owner_user_scope="shared",
            tenant_account_scope="system",
        )
        self.assertEqual("user_confirmation_required", internal["approval_status"])
        self.assertEqual("operator_approval_required", shared["approval_status"])
        self.assertNotEqual(internal["approval_status"], shared["approval_status"])

    def test_20_blocked_contracts_always_include_blocked_reason(self):
        for lane_id in BLOCKED_FIRST_TOOL_LANES_V1:
            with self.subTest(lane_id=lane_id):
                contract = self.contract_for(lane_id)
                self.assertEqual("blocked", contract["approval_status"])
                self.assertTrue(contract["blocked_reason"])

    def test_21_failure_metadata_does_not_claim_success(self):
        contract = self.contract_for("draft_artifact_creation", failure_count=2)
        self.assertEqual(2, contract["failure_count"])
        self.assertEqual("failed_metadata_only", contract["execution_status"])
        self.assertIn("failed", contract["user_visible_status_phrase"].lower())
        self.assertNotIn("succeeded", contract["user_visible_status_phrase"].lower())

    def test_22_operator_visibility_flag_is_present(self):
        contract = self.contract_for("project_plan_checklist")
        self.assertTrue(contract["operator_visibility"])

    def test_23_user_visible_status_phrase_is_present(self):
        for lane_id in APPROVED_FIRST_TOOL_LANES_V1:
            with self.subTest(lane_id=lane_id):
                contract = self.contract_for(lane_id)
                self.assertTrue(contract["user_visible_status_phrase"])

    def test_24_denied_authority_fields_remain_false(self):
        contract = self.contract_for("support_escalation_record")
        denied = contract["denied_authority"]
        self.assertIsInstance(denied, dict)
        for field in [
            "runtime_wiring_authority",
            "tool_execution_authority",
            "external_sending_authority",
            "public_publishing_authority",
            "destructive_action_authority",
            "third_party_account_authority",
            "storage_database_authority",
            "memory_mutation_authority",
            "project_state_mutation_authority",
            "behavior_pack_promotion_authority",
            "public_product_readiness_authority",
        ]:
            self.assertFalse(contract[field])
            self.assertFalse(denied[field])

    def test_25_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "first_tool_lanes_contracts.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_26_no_runtime_or_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "first_tool_lanes_contracts.py").read_text(encoding="utf-8")
        for needle in ["open(", "subprocess", "requests", "socket", "chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_27_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_28_examples_are_synthetic_only(self):
        examples = build_initial_first_tool_lane_contract_examples_v1()
        self.assertGreaterEqual(len(examples), 7)
        for item in examples:
            self.assertIn(item["lane_id"], ALL_FIRST_TOOL_LANES_V1)
            self.assertNotIn(".weslr", json.dumps(item, sort_keys=True))

    def test_29_summary_is_compact_and_json_safe(self):
        contract = self.contract_for("safe_internal_report_generation")
        summary = summarize_first_tool_lane_contract_v1(contract)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertLess(len(encoded), 2500)
        self.assertIn("safe_internal_report_generation", encoded)
        self.assertIn("validation_status", summary)

    def test_30_invalid_unknown_lane_fails_closed(self):
        contract = build_first_tool_lane_contract_v1(
            "unknown lane action",
            lane_id="unknown_lane",
            project_id="project_alpha",
            memory_reference_ids=["mem_unknown_001"],
            owner_user_scope="self",
            tenant_account_scope="self",
            requested_action="Unknown lane action",
        )
        validation = validate_first_tool_lane_contract_v1(contract)
        evaluation = evaluate_first_tool_lane_approval_v1(contract)
        self.assertFalse(validation["valid"])
        self.assertEqual("blocked", contract["approval_status"])
        self.assertEqual("blocked", evaluation["decision"])
        self.assertTrue(contract["blocked_reason"])


if __name__ == "__main__":
    unittest.main()
