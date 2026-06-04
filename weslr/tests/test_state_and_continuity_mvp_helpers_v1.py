#!/usr/bin/env python3
"""Focused tests for WESLR state and continuity MVP helpers v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.state_and_continuity_mvp_helpers import (  # noqa: E402
    allowed_state_continuity_categories_v1,
    allowed_state_continuity_scopes_v1,
    allowed_state_continuity_statuses_v1,
    build_initial_state_continuity_examples_v1,
    build_state_continuity_item_v1,
    build_state_continuity_packet_v1,
    classify_state_continuity_item_v1,
    summarize_state_continuity_packet_v1,
    to_state_continuity_json_safe_v1,
    validate_state_continuity_item_v1,
    validate_state_continuity_packet_v1,
)

DENIED_FIELDS = {
    "runtime_wiring_authority",
    "chat_responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "memory_persistence_authority",
    "project_state_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_personalization_authority",
    "behavior_update_authority",
    "public_product_readiness_authority",
    "consciousness_or_aliveness_claim_authority",
}


class StateAndContinuityMVPHelpersV1Tests(unittest.TestCase):
    def item_defaults(self, **overrides):
        category = overrides.get("category", "user_state")
        scope = overrides.get("scope", "user_scoped")
        status = overrides.get("status")
        defaults = {
            "item_id": f"item_{category}",
            "category": category,
            "scope": scope,
            "owner_user_scope": "operator",
            "tenant_account_scope": "self",
            "project_id": "project_alpha" if scope == "project_scoped" else "",
            "session_id": "session_alpha" if scope == "session_only" else "",
            "status": status,
            "source_type": "synthetic",
            "source_ref": "source_alpha",
            "evidence_count": 1,
            "confidence_level": "medium",
            "visibility": "user_visible" if category != "operator_visible_state" else "operator_visible",
            "update_authority": "operator_review_required" if scope in {"system_wide_candidate", "system_wide_approved"} else "metadata_only",
            "correction_path": "review_and_refresh",
            "user_visible_summary": f"{category} summary",
            "operator_visible_summary": f"{category} summary",
            "stale": False,
            "contradicted": False,
            "invalidated": False,
            "pending_approval": False,
            "blocked_reason": "",
            "audit_note": "synthetic review metadata" if category in {"operator_visible_state", "learning_candidate_pattern_state", "escalation_support_state"} else "synthetic metadata",
            "created_marker": "created_alpha",
            "updated_marker": "updated_alpha",
            "denied_authority": {field: False for field in DENIED_FIELDS},
            "governed_metadata_only": scope in {"system_wide_candidate", "system_wide_approved"},
        }
        defaults.update(overrides)
        if defaults["status"] is None:
            defaults["status"] = {
                "user_state": "confirmed",
                "session_state": "active_metadata_only",
                "project_state": "active_metadata_only",
                "memory_state": "provisional",
                "task_checklist_state": "pending_approval",
                "action_tool_state": "pending_approval",
                "evidence_source_state": "confirmed",
                "uncertainty_state": "proposed",
                "boundary_safety_state": "active_metadata_only",
                "learning_candidate_pattern_state": "proposed",
                "escalation_support_state": "pending_approval",
                "operator_visible_state": "active_metadata_only",
            }.get(category, "absent")
        if "scope" not in overrides:
            if category == "session_state":
                defaults["scope"] = "session_only"
            elif category == "project_state":
                defaults["scope"] = "project_scoped"
            elif category in {"task_checklist_state", "action_tool_state", "evidence_source_state", "escalation_support_state"}:
                defaults["scope"] = "project_scoped"
            elif category in {"user_state", "memory_state"}:
                defaults["scope"] = "user_scoped"
            elif category in {"uncertainty_state", "boundary_safety_state"}:
                defaults["scope"] = "session_only"
            elif category == "learning_candidate_pattern_state":
                defaults["scope"] = "system_wide_candidate" if overrides.get("governed_metadata_only", True) else "project_scoped"
            elif category == "operator_visible_state":
                defaults["scope"] = "operator_scoped"
        if category == "session_state":
            defaults["session_id"] = defaults.get("session_id") or "session_alpha"
        if category == "project_state":
            defaults["project_id"] = defaults.get("project_id") or "project_alpha"
        if category == "uncertainty_state":
            defaults["session_id"] = defaults.get("session_id") or "session_alpha"
        if category == "boundary_safety_state":
            defaults["session_id"] = defaults.get("session_id") or "session_alpha"
        if category == "learning_candidate_pattern_state":
            defaults["governed_metadata_only"] = True
            defaults["update_authority"] = "operator_review_required"
            defaults["audit_note"] = "operator review metadata for candidate pattern"
        if category == "operator_visible_state":
            defaults["visibility"] = "operator_visible"
            defaults["update_authority"] = "operator_review_required"
            defaults["audit_note"] = "operator trace metadata"
        if defaults.get("scope") == "project_scoped" and not defaults.get("project_id"):
            defaults["project_id"] = "project_alpha"
        if defaults.get("scope") == "session_only" and not defaults.get("session_id"):
            defaults["session_id"] = "session_alpha"
        return build_state_continuity_item_v1(**defaults)

    def test_01_allowed_categories_include_all_required_categories(self):
        allowed = set(allowed_state_continuity_categories_v1())
        expected = {
            "user_state",
            "session_state",
            "project_state",
            "memory_state",
            "task_checklist_state",
            "action_tool_state",
            "evidence_source_state",
            "uncertainty_state",
            "boundary_safety_state",
            "learning_candidate_pattern_state",
            "escalation_support_state",
            "operator_visible_state",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_02_allowed_scopes_include_all_required_scopes(self):
        allowed = set(allowed_state_continuity_scopes_v1())
        expected = {
            "session_only",
            "project_scoped",
            "user_scoped",
            "tenant_account_scoped",
            "operator_scoped",
            "system_wide_candidate",
            "system_wide_approved",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_03_allowed_statuses_include_memory_status_model(self):
        allowed = set(allowed_state_continuity_statuses_v1())
        expected = {
            "absent",
            "proposed",
            "provisional",
            "confirmed",
            "stale",
            "contradicted",
            "invalidated",
            "archived_deprecated",
            "blocked",
            "pending_approval",
            "failed",
            "active_metadata_only",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_04_builds_valid_item_for_each_required_category(self):
        for category in allowed_state_continuity_categories_v1():
            with self.subTest(category=category):
                item = self.item_defaults(category=category)
                result = validate_state_continuity_item_v1(item)
                self.assertTrue(result["valid"], result["violations"])

    def test_05_builds_valid_packet_with_all_sections_items(self):
        items = [self.item_defaults(category=category) for category in allowed_state_continuity_categories_v1()]
        packet = build_state_continuity_packet_v1(
            packet_id="packet_alpha",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=items,
            limitations=["synthetic example"],
        )
        result = validate_state_continuity_packet_v1(packet)
        self.assertTrue(result["valid"], result["violations"])

    def test_06_item_and_packet_are_json_safe(self):
        item = self.item_defaults(category="project_state")
        packet = build_state_continuity_packet_v1(
            packet_id="packet_json",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        safe = to_state_continuity_json_safe_v1(packet)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("packet_json", encoded)
        self.assertIn("project_state", encoded)

    def test_07_validation_rejects_missing_owner_scope_status_source_like_fields(self):
        item = self.item_defaults(category="project_state")
        item.pop("owner_user_scope")
        item.pop("status")
        item.pop("source_ref")
        item.pop("source_type")
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["violation_count"], 4)

    def test_08_unknown_category_fails_closed(self):
        item = self.item_defaults(category="unknown_state")
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown category" in violation for violation in result["violations"]))

    def test_09_unknown_scope_fails_closed(self):
        item = self.item_defaults(scope="unknown_scope")
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown scope" in violation for violation in result["violations"]))

    def test_10_unknown_status_fails_closed(self):
        item = self.item_defaults(status="impossible")
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown status" in violation for violation in result["violations"]))

    def test_11_session_only_cannot_silently_become_global_system_state(self):
        item = self.item_defaults(category="session_state")
        item["project_id"] = "project_alpha"
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("session_only state must not silently become project scoped" in v for v in result["violations"]))

    def test_12_project_scoped_state_requires_project_id(self):
        item = self.item_defaults(category="project_state")
        item["project_id"] = ""
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("project_scoped state requires project_id" in v for v in result["violations"]))

    def test_13_user_scoped_state_requires_owner_user_scope(self):
        item = self.item_defaults(category="user_state")
        item["owner_user_scope"] = ""
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("user_scoped state requires owner_user_scope" in v for v in result["violations"]))

    def test_14_tenant_scoped_state_requires_tenant_account_scope(self):
        item = self.item_defaults(category="project_state", scope="tenant_account_scoped")
        item["tenant_account_scope"] = ""
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("tenant_account_scoped state requires tenant_account_scope" in v for v in result["violations"]))

    def test_15_system_wide_candidate_and_approved_requires_operator_review_metadata(self):
        item = self.item_defaults(category="learning_candidate_pattern_state", scope="system_wide_candidate")
        item["governed_metadata_only"] = False
        item["update_authority"] = "metadata_only"
        item["audit_note"] = ""
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("system-wide state requires governed_metadata_only=true" in v for v in result["violations"]))
        self.assertTrue(any("operator review metadata" in v for v in result["violations"]))

    def test_16_cross_user_global_view_fails_closed_unless_governed_metadata_only(self):
        item = self.item_defaults(category="user_state")
        item["owner_user_scope"] = "shared"
        item["tenant_account_scope"] = "system"
        item["scope"] = "system_wide_candidate"
        item["governed_metadata_only"] = False
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        governed = self.item_defaults(category="user_state")
        governed["owner_user_scope"] = "shared"
        governed["tenant_account_scope"] = "system"
        governed["scope"] = "system_wide_candidate"
        governed["governed_metadata_only"] = True
        governed["update_authority"] = "operator_review_required"
        governed["audit_note"] = "operator review metadata"
        governed_result = validate_state_continuity_item_v1(governed)
        self.assertTrue(governed_result["valid"], governed_result["violations"])

    def test_17_raw_private_data_is_blocked_or_redacted_by_default(self):
        item = build_state_continuity_item_v1(
            item_id="item_private",
            category="memory_state",
            scope="user_scoped",
            owner_user_scope="operator",
            tenant_account_scope="self",
            status="provisional",
            source_type="synthetic",
            source_ref="memory_private",
            user_visible_summary="memory continuity metadata",
            operator_visible_summary="memory continuity metadata",
            raw_private_content={"secret": "value"},
        )
        encoded = json.dumps(to_state_continuity_json_safe_v1(item), sort_keys=True)
        self.assertNotIn("secret", encoded)
        self.assertTrue(item["raw_private_data_redacted"])

    def test_18_stale_state_is_surfaced_in_summary(self):
        stale_item = self.item_defaults(category="memory_state")
        stale_item["status"] = "stale"
        stale_item["stale"] = True
        packet = build_state_continuity_packet_v1(
            packet_id="packet_stale",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[stale_item],
        )
        summary = summarize_state_continuity_packet_v1(packet)
        self.assertGreater(summary["stale_items_count"], 0)

    def test_19_contradicted_state_is_surfaced_and_not_active(self):
        item = self.item_defaults(category="memory_state")
        item["status"] = "active_metadata_only"
        item["contradicted"] = True
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("contradicted state cannot be active" in v for v in result["violations"]))

    def test_20_invalidated_state_is_surfaced_and_not_active(self):
        item = self.item_defaults(category="memory_state")
        item["status"] = "active_metadata_only"
        item["invalidated"] = True
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("invalidated state cannot be active" in v for v in result["violations"]))

    def test_21_pending_approvals_are_preserved_in_packet_summary(self):
        item = self.item_defaults(category="action_tool_state")
        item["status"] = "pending_approval"
        item["pending_approval"] = True
        packet = build_state_continuity_packet_v1(
            packet_id="packet_pending",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        summary = summarize_state_continuity_packet_v1(packet)
        self.assertEqual(1, summary["pending_approvals_count"])

    def test_22_action_tool_state_does_not_imply_permission(self):
        item = self.item_defaults(category="action_tool_state")
        item["update_authority"] = "metadata_only"
        result = validate_state_continuity_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        denied = item["denied_authority"]
        self.assertTrue(all(value is False for value in denied.values()))

    def test_23_boundary_safety_state_has_blocked_reason_when_blocked(self):
        item = self.item_defaults(category="boundary_safety_state")
        item["status"] = "blocked"
        item["blocked_reason"] = ""
        result = validate_state_continuity_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("blocked state requires blocked_reason" in v for v in result["violations"]))

    def test_24_candidate_learning_pattern_remains_candidate_not_rule(self):
        item = self.item_defaults(category="learning_candidate_pattern_state")
        self.assertEqual("learning_candidate_pattern_state", item["category"])
        self.assertEqual("proposed", item["status"])
        classification = classify_state_continuity_item_v1(item)
        self.assertEqual("learning_candidate_pattern_state", classification["category"])
        self.assertEqual("proposed", classification["status"])

    def test_25_support_escalation_is_visible_not_hidden(self):
        item = self.item_defaults(category="escalation_support_state")
        packet = build_state_continuity_packet_v1(
            packet_id="packet_support",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        summary = summarize_state_continuity_packet_v1(packet)
        self.assertEqual(1, summary["item_count"])
        self.assertTrue(packet["operator_visible_items"] or packet["items"])

    def test_26_operator_visible_state_has_audit_trace_metadata(self):
        item = self.item_defaults(category="operator_visible_state")
        result = validate_state_continuity_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        self.assertTrue(item["audit_note"])
        self.assertEqual("operator_visible", item["visibility"])

    def test_27_denied_authority_fields_remain_false_or_blocked(self):
        item = self.item_defaults(category="operator_visible_state")
        denied = item["denied_authority"]
        self.assertEqual(DENIED_FIELDS, set(denied))
        self.assertTrue(all(value is False for value in denied.values()))
        packet = build_state_continuity_packet_v1(
            packet_id="packet_denied",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        self.assertTrue(all(value is False for value in packet["denied_authority"].values()))

    def test_28_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "state_and_continuity_mvp_helpers.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_29_no_runtime_or_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "state_and_continuity_mvp_helpers.py").read_text(encoding="utf-8")
        for needle in ["chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_30_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_31_examples_are_synthetic_only(self):
        examples = build_initial_state_continuity_examples_v1()
        self.assertGreaterEqual(len(examples), 2)
        for item in examples:
            self.assertIn("items", item)
            self.assertNotIn(".weslr", json.dumps(item, sort_keys=True))

    def test_32_summary_is_compact_and_json_safe(self):
        packet = build_state_continuity_packet_v1(
            packet_id="packet_summary",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[self.item_defaults(category="project_state")],
        )
        summary = summarize_state_continuity_packet_v1(packet)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertLess(len(encoded), 5000)
        self.assertIn("packet_summary", encoded)
        self.assertIn("item_count", summary)

    def test_33_invalid_packet_fails_closed(self):
        result = validate_state_continuity_packet_v1({"bad": "packet"})
        self.assertFalse(result["valid"])
        self.assertGreater(result["violation_count"], 0)

    def test_34_validation_returns_metadata_not_exceptions(self):
        item = self.item_defaults(category="project_state")
        item.pop("source_ref")
        result = validate_state_continuity_item_v1(item)
        self.assertIsInstance(result, dict)
        self.assertIn("violations", result)
        self.assertFalse(result["valid"])

    def test_35_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "state_and_continuity_mvp_helpers.py").read_text(encoding="utf-8")
        for needle in ["open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
