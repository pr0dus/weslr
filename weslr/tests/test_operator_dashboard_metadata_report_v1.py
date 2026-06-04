#!/usr/bin/env python3
"""Focused tests for WESLR operator dashboard metadata report helpers V1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.operator_dashboard_metadata_report import (  # noqa: E402
    build_initial_operator_dashboard_metadata_examples_v1,
    build_operator_dashboard_metadata_packet_v1,
    classify_operator_dashboard_item_v1,
    summarize_operator_dashboard_metadata_packet_v1,
    to_operator_dashboard_metadata_json_safe_v1,
    validate_operator_dashboard_metadata_packet_v1,
)


DENIED_FIELDS = {
    "ui_implementation_authority",
    "backend_api_authority",
    "runtime_wiring_authority",
    "live_dashboard_authority",
    "operator_control_execution_authority",
    "tool_execution_authority",
    "storage_database_authority",
    "memory_mutation_authority",
    "project_state_mutation_authority",
    "cross_user_browsing_authority",
    "raw_private_data_dump_authority",
    "public_product_readiness_authority",
    "behavior_pack_promotion_authority",
}


class OperatorDashboardMetadataReportV1Tests(unittest.TestCase):
    def base_packet(self, **overrides):
        defaults = {
            "report_id": "report_alpha",
            "owner_operator_scope": "operator",
            "tenant_account_scope": "self",
            "source_scope": "synthetic",
            "overview": [{"owner_user_scope": "operator", "source_provenance": "synthetic"}],
            "approvals_queue": [
                {
                    "approval_id": "approval_001",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "lane_id": "draft_artifact_creation",
                    "action_class": "draft_artifact_creation",
                    "requested_action": "Draft a note",
                    "risk_level": "low_internal",
                    "required_approval_type": "none",
                    "approval_status": "not_required_internal_only",
                    "source_provenance": "synthetic",
                    "user_visible_summary": "Draft only",
                }
            ],
            "blocked_actions": [
                {
                    "blocked_reason": "external export blocked",
                    "boundary_triggered": "no external export",
                    "lane_id": "public_publishing",
                    "action_class": "public_publishing",
                    "affected_item": "report_alpha",
                    "user_visible_blocked_phrase": "blocked from public export",
                    "source_provenance": "synthetic",
                }
            ],
            "project_state": [
                {
                    "project_id": "project_alpha",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "project_status": "active",
                    "project_phase": "planning",
                    "source_provenance": "synthetic",
                    "stale": False,
                    "contradicted": False,
                    "invalidated": False,
                }
            ],
            "memory_state": [
                {
                    "memory_id": "memory_alpha",
                    "scope": "self",
                    "status": "provisional",
                    "type": "note",
                    "source_provenance": "synthetic",
                    "stale": False,
                    "contradicted": False,
                    "invalidated": False,
                }
            ],
            "first_tool_lane_contracts": [
                {
                    "lane_id": "safe_internal_report_generation",
                    "action_class": "safe_internal_report_generation",
                    "approval_status": "not_required_internal_only",
                    "execution_status": "planned_metadata_only",
                    "risk_level": "low_internal",
                    "blocked_reason": "",
                    "denied_authority": {field: False for field in DENIED_FIELDS},
                    "operator_visibility": True,
                    "user_visible_status_phrase": "internal report only",
                    "source_provenance": "synthetic",
                    "external_action_requested": False,
                    "destructive_action_requested": False,
                    "third_party_action_requested": False,
                    "runtime_activation_requested": False,
                    "public_export_requested": False,
                }
            ],
            "support_escalation": [
                {
                    "support_escalation_id": "support_alpha",
                    "reason": "user question",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "status": "open",
                    "last_safe_step": "collect evidence",
                    "source_provenance": "synthetic",
                    "personal_data_inclusion_flag": False,
                }
            ],
            "audit_trail": [
                {
                    "initiator": "system",
                    "marker": "audit_001",
                    "scope": "self",
                    "reason": "metadata example",
                    "source_provenance": "synthetic",
                    "old_state_summary": "draft",
                    "new_state_summary": "draft",
                    "related_artifact_or_contract": "report_alpha",
                }
            ],
            "rollback_deprecation": [
                {
                    "rollback_availability": "available",
                    "rollback_target": "report_alpha",
                    "deprecation_status": "active",
                    "source_provenance": "synthetic",
                    "last_safe_state": "initial",
                }
            ],
            "validation_release_status": [
                {
                    "latest_validation_status": "valid",
                    "release_gate_status": "passed",
                    "release_check_status": "passed",
                    "protected_file_status": "unchanged",
                    "allowed_file_scope": "docs-only",
                    "source_provenance": "synthetic",
                }
            ],
            "incident_risk_flags": [
                {"flag": "repeated_failure", "scope": "self", "source_provenance": "synthetic"}
            ],
            "lane_expansion_candidates": [
                {"candidate_id": "lane_001", "summary": "future scope", "source_provenance": "synthetic"}
            ],
            "operator_notes": ["synthetic example"],
            "limitations": ["synthetic only"],
            "governed_metadata_only": False,
        }
        defaults.update(overrides)
        packet = build_operator_dashboard_metadata_packet_v1(**defaults)
        return packet

    def test_01_packet_shape_and_all_required_sections(self):
        packet = self.base_packet()
        self.assertEqual("operator_dashboard_metadata_report_v1", packet["schema_version"])
        self.assertEqual("operator_dashboard_metadata_report_v1", packet["report_type"])
        self.assertIn("sections", packet)
        self.assertEqual(
            {
                "overview",
                "approvals_queue",
                "blocked_actions",
                "project_state",
                "memory_state",
                "first_tool_lane_contracts",
                "support_escalation",
                "audit_trail",
                "rollback_deprecation",
                "validation_release_status",
                "incident_risk_flags",
                "lane_expansion_candidates",
            },
            set(packet["sections"]),
        )

    def test_02_packet_is_json_safe(self):
        packet = self.base_packet()
        safe = to_operator_dashboard_metadata_json_safe_v1(packet)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("report_alpha", encoded)

    def test_03_validation_rejects_missing_owner_scope_status_source_like_fields(self):
        packet = self.base_packet()
        packet["sections"]["approvals_queue"][0].pop("source_provenance")
        packet["sections"]["project_state"][0].pop("owner_user_scope")
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["violation_count"], 2)

    def test_04_overview_counts_are_computed_from_supplied_metadata(self):
        packet = self.base_packet()
        counts = packet["counts"]
        self.assertEqual(1, counts["approvals_queue"])
        self.assertEqual(1, counts["blocked_actions"])
        self.assertEqual(1, counts["project_state"])
        self.assertEqual(1, counts["memory_state"])
        self.assertEqual(1, counts["first_tool_lane_contracts"])
        self.assertEqual(1, counts["support_escalation"])
        self.assertEqual(1, counts["audit_trail"])
        self.assertEqual(1, counts["rollback_deprecation"])
        self.assertEqual(1, counts["validation_release_status"])
        self.assertEqual(1, counts["incident_risk_flags"])
        self.assertEqual(1, counts["lane_expansion_candidates"])

    def test_05_approval_queue_entries_require_approval_status_and_scope(self):
        packet = self.base_packet()
        entry = packet["sections"]["approvals_queue"][0]
        self.assertTrue(entry["approval_status"])
        self.assertTrue(entry["owner_user_scope"])
        self.assertTrue(entry["tenant_account_scope"])

    def test_06_blocked_actions_require_blocked_reason_and_boundary(self):
        packet = self.base_packet()
        entry = packet["sections"]["blocked_actions"][0]
        self.assertTrue(entry["blocked_reason"])
        self.assertTrue(entry["boundary_triggered"])

    def test_07_project_state_entries_expose_status_and_stale_contradicted_flags(self):
        packet = self.base_packet()
        entry = packet["sections"]["project_state"][0]
        self.assertTrue(entry["project_status"])
        self.assertTrue(entry["project_phase"])
        self.assertIn("stale", entry)
        self.assertIn("contradicted", entry)

    def test_08_memory_state_entries_expose_status_and_stale_contradicted_invalidated_flags(self):
        packet = self.base_packet()
        entry = packet["sections"]["memory_state"][0]
        self.assertTrue(entry["status"])
        self.assertTrue(entry["type"])
        self.assertIn("stale", entry)
        self.assertIn("contradicted", entry)
        self.assertIn("invalidated", entry)

    def test_09_first_tool_lane_contracts_expose_denied_authority_status(self):
        packet = self.base_packet()
        entry = packet["sections"]["first_tool_lane_contracts"][0]
        self.assertTrue(entry["operator_visibility"])
        self.assertTrue(entry["denied_authority"])
        self.assertTrue(all(value is False for value in entry["denied_authority"].values()))

    def test_10_support_escalation_entries_expose_status_owner_last_safe_step(self):
        packet = self.base_packet()
        entry = packet["sections"]["support_escalation"][0]
        self.assertTrue(entry["status"])
        self.assertTrue(entry["owner_user_scope"])
        self.assertTrue(entry["last_safe_step"])

    def test_11_personal_data_support_escalation_requires_approval_metadata(self):
        packet = self.base_packet(
            support_escalation=[
                {
                    "support_escalation_id": "support_personal",
                    "reason": "needs personal data",
                    "owner_user_scope": "self",
                    "tenant_account_scope": "self",
                    "status": "open",
                    "last_safe_step": "ask for approval",
                    "source_provenance": "synthetic",
                    "personal_data_inclusion_flag": True,
                }
            ]
        )
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertTrue(any("personal data" in item.lower() for item in result["violations"]))

    def test_12_audit_entries_require_initiator_marker_scope_reason(self):
        packet = self.base_packet()
        entry = packet["sections"]["audit_trail"][0]
        self.assertTrue(entry["initiator"])
        self.assertTrue(entry["marker"])
        self.assertTrue(entry["scope"])
        self.assertTrue(entry["reason"])

    def test_13_rollback_deprecation_entries_show_availability_or_deprecation_status(self):
        packet = self.base_packet()
        entry = packet["sections"]["rollback_deprecation"][0]
        self.assertTrue(entry.get("rollback_availability") or entry.get("deprecation_status"))

    def test_14_validation_release_status_includes_gate_check_protected_file_status(self):
        packet = self.base_packet()
        self.assertTrue(packet["protected_file_status"])
        self.assertTrue(packet["release_gate_status"])
        self.assertTrue(packet["release_check_status"])

    def test_15_incident_risk_flags_include_required_risk_categories(self):
        packet = self.base_packet(
            incident_risk_flags=[
                {"flag": "external_action_request", "scope": "self", "source_provenance": "synthetic"},
                {"flag": "destructive_action_request", "scope": "self", "source_provenance": "synthetic"},
                {"flag": "runtime_activation_request", "scope": "self", "source_provenance": "synthetic"},
                {"flag": "hidden_memory_project_mutation_request", "scope": "self", "source_provenance": "synthetic"},
                {"flag": "cross_user_leakage_risk", "scope": "shared", "source_provenance": "synthetic"},
            ]
        )
        flags = packet["risk_flags"]
        for flag in [
            "external_action_request",
            "destructive_action_request",
            "runtime_activation_request",
            "hidden_memory_project_mutation_request",
            "cross_user_leakage_risk",
        ]:
            with self.subTest(flag=flag):
                self.assertIn(flag, flags)

    def test_16_raw_private_data_is_blocked_or_redacted_by_default(self):
        packet = self.base_packet(raw_private_data={"secret": "value"})
        self.assertTrue(packet["raw_private_data_redacted"])
        encoded = json.dumps(to_operator_dashboard_metadata_json_safe_v1(packet), sort_keys=True)
        self.assertNotIn("secret", encoded)

    def test_17_cross_user_global_view_fails_closed_unless_governed_metadata_only(self):
        packet = self.base_packet(owner_operator_scope="shared", tenant_account_scope="system", source_scope="cross-user")
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        governed = self.base_packet(owner_operator_scope="shared", tenant_account_scope="system", source_scope="cross-user", governed_metadata_only=True)
        governed_result = validate_operator_dashboard_metadata_packet_v1(governed)
        self.assertTrue(governed_result["valid"])

    def test_18_dashboard_controls_are_not_executable(self):
        packet = self.base_packet()

        def walk(value):
            if callable(value):
                return True
            if isinstance(value, dict):
                return any(walk(item) for item in value.values())
            if isinstance(value, list):
                return any(walk(item) for item in value)
            return False

        self.assertFalse(walk(packet))

    def test_19_denied_authority_fields_remain_false_or_blocked(self):
        packet = self.base_packet()
        entry = packet["sections"]["first_tool_lane_contracts"][0]["denied_authority"]
        self.assertEqual(DENIED_FIELDS, set(entry))
        self.assertTrue(all(value is False for value in entry.values()))

    def test_20_unknown_dashboard_section_fails_closed(self):
        packet = self.base_packet()
        packet["sections"]["mystery"] = []
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown sections" in violation for violation in result["violations"]))

    def test_21_missing_blocked_reason_fails_validation(self):
        packet = self.base_packet()
        packet["sections"]["blocked_actions"][0].pop("blocked_reason")
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertTrue(any("blocked_reason" in violation for violation in result["violations"]))

    def test_22_missing_approval_status_fails_validation(self):
        packet = self.base_packet()
        packet["sections"]["approvals_queue"][0].pop("approval_status")
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertFalse(result["valid"])
        self.assertTrue(any("approval_status" in violation for violation in result["violations"]))

    def test_23_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "operator_dashboard_metadata_report.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_24_no_runtime_or_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "operator_dashboard_metadata_report.py").read_text(encoding="utf-8")
        for needle in ["chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_25_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_26_examples_are_synthetic_only(self):
        examples = build_initial_operator_dashboard_metadata_examples_v1()
        self.assertGreaterEqual(len(examples), 2)
        for item in examples:
            self.assertIn("sections", item)
            self.assertNotIn(".weslr", json.dumps(item, sort_keys=True))

    def test_27_summary_is_compact_and_json_safe(self):
        packet = self.base_packet()
        summary = summarize_operator_dashboard_metadata_packet_v1(packet)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertLess(len(encoded), 4000)
        self.assertIn("report_alpha", encoded)
        self.assertIn("counts", summary)

    def test_28_invalid_packet_fails_closed(self):
        result = validate_operator_dashboard_metadata_packet_v1({"bad": "packet"})
        self.assertFalse(result["valid"])
        self.assertGreater(result["violation_count"], 0)

    def test_29_validation_returns_metadata_not_exceptions(self):
        packet = self.base_packet()
        packet["sections"]["approvals_queue"][0].pop("source_provenance")
        result = validate_operator_dashboard_metadata_packet_v1(packet)
        self.assertIsInstance(result, dict)
        self.assertIn("violations", result)
        self.assertFalse(result["valid"])

    def test_30_report_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "operator_dashboard_metadata_report.py").read_text(encoding="utf-8")
        for needle in ["open(", "subprocess", "requests", "socket", "chat_responder", "main.py", "dialogue", "chat_ui", ".weslr"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
