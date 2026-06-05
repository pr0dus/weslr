#!/usr/bin/env python3
"""Focused tests for WESLR memory state model helpers v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.memory_state_model_helpers import (  # noqa: E402
    allowed_memory_state_scopes_v1,
    allowed_memory_state_statuses_v1,
    allowed_memory_state_types_v1,
    build_initial_memory_state_examples_v1,
    build_memory_state_item_v1,
    build_memory_state_packet_v1,
    classify_memory_state_item_v1,
    summarize_memory_state_packet_v1,
    to_memory_state_json_safe_v1,
    validate_memory_state_item_v1,
    validate_memory_state_packet_v1,
)

DENIED_FIELDS = {
    "runtime_wiring_authority",
    "chat_responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "memory_persistence_authority",
    "memory_mutation_authority",
    "project_state_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_memory_authority",
    "hidden_personalization_authority",
    "perfect_memory_claim_authority",
    "behavior_update_authority",
    "public_product_readiness_authority",
}


class MemoryStateModelHelpersV1Tests(unittest.TestCase):
    def item_defaults(self, **overrides):
        scope = overrides.get("scope", "project_scoped")
        memory_type = overrides.get("memory_type", "project_context")
        status = overrides.get("status")
        defaults = {
            "memory_id": overrides.get("memory_id", f"memory_alpha_{memory_type}"),
            "memory_type": memory_type,
            "scope": scope,
            "owner_user_scope": overrides.get("owner_user_scope", "operator"),
            "tenant_account_scope": overrides.get("tenant_account_scope", "self"),
            "project_id": overrides.get("project_id", "project_alpha"),
            "session_id": overrides.get("session_id", "session_alpha"),
            "status": status,
            "source_type": overrides.get("source_type", "synthetic"),
            "source_ref": overrides.get("source_ref", "source_alpha"),
            "evidence_count": overrides.get("evidence_count", 2),
            "confidence_level": overrides.get("confidence_level", "medium"),
            "visibility": overrides.get("visibility", scope),
            "correction_path": overrides.get("correction_path", "review_or_refresh"),
            "export_relevance": overrides.get("export_relevance", False),
            "deletion_relevance": overrides.get("deletion_relevance", False),
            "revocation_relevance": overrides.get("revocation_relevance", False),
            "stale": overrides.get("stale", False),
            "contradicted": overrides.get("contradicted", False),
            "invalidated": overrides.get("invalidated", False),
            "pending_approval": overrides.get("pending_approval", False),
            "blocked_reason": overrides.get("blocked_reason", ""),
            "user_visible_summary": overrides.get("user_visible_summary", "Synthetic memory continuity note"),
            "operator_visible_summary": overrides.get("operator_visible_summary", "Synthetic operator review note"),
            "audit_note": overrides.get("audit_note", "synthetic memory state metadata"),
            "created_marker": overrides.get("created_marker", "created_alpha"),
            "updated_marker": overrides.get("updated_marker", "updated_alpha"),
            "denied_authority": {field: False for field in DENIED_FIELDS},
        }
        defaults.update(overrides)
        if defaults["status"] is None:
            defaults["status"] = {
                "candidate_learning_pattern": "proposed",
                "blocked_memory": "blocked",
                "system_wide_candidate": "proposed",
                "system_wide_approved": "confirmed",
            }.get(scope, "confirmed")
        return build_memory_state_item_v1(**defaults)

    def test_01_allowed_statuses_include_required_statuses(self):
        allowed = set(allowed_memory_state_statuses_v1())
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
        }
        self.assertTrue(expected.issubset(allowed))

    def test_02_allowed_types_include_required_types(self):
        allowed = set(allowed_memory_state_types_v1())
        expected = {
            "preference",
            "project_context",
            "user_correction",
            "constraint",
            "decision",
            "artifact_reference",
            "support_context",
            "operator_note",
            "candidate_learning_pattern",
            "blocked_memory",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_03_allowed_scopes_include_required_scopes(self):
        allowed = set(allowed_memory_state_scopes_v1())
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

    def test_04_builds_valid_item(self):
        item = self.item_defaults()
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_05_builds_valid_packet(self):
        items = [
            self.item_defaults(memory_id="memory_alpha_project", scope="project_scoped"),
            self.item_defaults(memory_id="memory_alpha_user", memory_type="preference", scope="user_scoped", owner_user_scope="operator"),
            self.item_defaults(memory_id="memory_alpha_session", scope="session_only", project_id="", tenant_account_scope="", visibility="session_only", session_id="session_alpha"),
            self.item_defaults(memory_id="memory_alpha_system", scope="system_wide_approved", status="confirmed", operator_visible_summary="operator review metadata", audit_note="operator review metadata", project_id="project_alpha"),
        ]
        packet = build_memory_state_packet_v1(
            packet_id="packet_alpha",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=items,
            limitations=["synthetic example"],
        )
        result = validate_memory_state_packet_v1(packet)
        self.assertTrue(result["valid"], result["violations"])

    def test_06_item_and_packet_are_json_safe(self):
        item = self.item_defaults()
        packet = build_memory_state_packet_v1(
            packet_id="packet_json",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        safe = to_memory_state_json_safe_v1(packet)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("packet_json", encoded)
        self.assertIn("memory_alpha_project_context", encoded)

    def test_07_validation_rejects_missing_required_fields(self):
        item = self.item_defaults()
        for field in ["memory_id", "status", "scope", "source_ref", "source_type"]:
            item.pop(field, None)
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["violation_count"], 5)

    def test_08_unknown_status_fails_closed(self):
        item = self.item_defaults(status="impossible")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown status" in violation for violation in result["violations"]))

    def test_09_unknown_type_fails_closed(self):
        item = self.item_defaults(memory_type="impossible")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown memory type" in violation for violation in result["violations"]))

    def test_10_unknown_scope_fails_closed(self):
        item = self.item_defaults(scope="impossible")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown scope" in violation for violation in result["violations"]))

    def test_11_session_only_cannot_silently_become_global_or_project_memory(self):
        item = self.item_defaults(scope="session_only", project_id="project_alpha", tenant_account_scope="self")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("session_only memory cannot silently become project-scoped" in violation for violation in result["violations"]))

    def test_12_project_scoped_memory_requires_project_id(self):
        item = self.item_defaults(scope="project_scoped", project_id="")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("project_scoped memory requires project_id" in violation for violation in result["violations"]))

    def test_13_user_scoped_memory_requires_owner_user_scope(self):
        item = self.item_defaults(scope="user_scoped", owner_user_scope="")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("owner_user_scope missing or blank" in violation for violation in result["violations"]))

    def test_14_tenant_account_scoped_memory_requires_tenant_account_scope(self):
        item = self.item_defaults(scope="tenant_account_scoped", tenant_account_scope="")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("tenant_account_scoped memory requires tenant_account_scope" in violation for violation in result["violations"]))

    def test_15_system_wide_candidate_requires_operator_review_metadata(self):
        item = self.item_defaults(scope="system_wide_candidate", status="proposed", operator_visible_summary="", audit_note="")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("system-wide memory requires operator review metadata" in violation for violation in result["violations"]))

    def test_16_system_wide_approved_requires_operator_review_metadata(self):
        item = self.item_defaults(scope="system_wide_approved", status="confirmed", operator_visible_summary="operator review metadata", audit_note="operator review metadata")
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_17_cross_user_global_memory_fails_closed_unless_governed_metadata_only(self):
        item = self.item_defaults(memory_id="global_shared_memory_alpha", scope="user_scoped")
        result = validate_memory_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("cross-user/global memory fails closed" in violation for violation in result["violations"]))

    def test_18_raw_private_data_is_blocked_or_redacted_by_default(self):
        item = self.item_defaults(source_ref="operator@example.com", user_visible_summary="private details", operator_visible_summary="private details")
        self.assertEqual("redacted_content", item["source_ref"])
        self.assertEqual("redacted_content", item["user_visible_summary"])
        self.assertEqual("redacted_content", item["operator_visible_summary"])
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_19_proposed_or_provisional_memory_is_not_confirmed(self):
        proposed = self.item_defaults(memory_id="memory_proposed", status="proposed")
        provisional = self.item_defaults(memory_id="memory_provisional", status="provisional")
        self.assertEqual("review_required", classify_memory_state_item_v1(proposed)["risk"])
        self.assertEqual("review_required", classify_memory_state_item_v1(provisional)["risk"])
        self.assertEqual("proposed", classify_memory_state_item_v1(proposed)["status"])
        self.assertEqual("provisional", classify_memory_state_item_v1(provisional)["status"])

    def test_20_stale_memory_is_surfaced(self):
        item = self.item_defaults(memory_id="memory_stale", status="stale", stale=True)
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_memory_state_item_v1(item)
        self.assertEqual("stale", classification["status"])
        self.assertEqual("review_required", classification["risk"])

    def test_21_contradicted_memory_is_surfaced_and_not_active(self):
        item = self.item_defaults(memory_id="memory_contradicted", status="contradicted", contradicted=True)
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_memory_state_item_v1(item)
        self.assertEqual("contradicted", classification["status"])
        self.assertEqual("blocked", classification["risk"])

    def test_22_invalidated_memory_is_surfaced_and_not_active(self):
        item = self.item_defaults(memory_id="memory_invalidated", status="invalidated", invalidated=True)
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_memory_state_item_v1(item)
        self.assertEqual("invalidated", classification["status"])
        self.assertEqual("blocked", classification["risk"])

    def test_23_pending_approvals_are_preserved(self):
        item = self.item_defaults(memory_id="memory_pending", status="pending_approval", pending_approval=True)
        packet = build_memory_state_packet_v1(
            packet_id="packet_pending",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        summary = summarize_memory_state_packet_v1(packet)
        self.assertEqual(1, summary["pending_count"])
        self.assertEqual(1, len(summary["pending_approvals"]))

    def test_24_candidate_learning_patterns_remain_candidates_not_rules(self):
        item = self.item_defaults(memory_id="memory_candidate", memory_type="candidate_learning_pattern", scope="system_wide_candidate", status="pending_approval", pending_approval=True, operator_visible_summary="operator review metadata", audit_note="operator review metadata")
        packet = build_memory_state_packet_v1(
            packet_id="packet_candidate",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        summary = summarize_memory_state_packet_v1(packet)
        self.assertEqual(1, summary["candidate_learning_pattern_count"])
        self.assertEqual(1, len(packet["candidate_learning_patterns"]))

    def test_25_export_deletion_revocation_relevance_is_metadata_only(self):
        item = self.item_defaults(memory_id="memory_relevance", export_relevance=True, deletion_relevance=True, revocation_relevance=True)
        packet = build_memory_state_packet_v1(
            packet_id="packet_relevance",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        self.assertEqual([item], packet["export_relevant_items"])
        self.assertEqual([item], packet["deletion_relevant_items"])
        self.assertEqual([item], packet["revocation_relevant_items"])

    def test_26_no_hidden_memory(self):
        item = self.item_defaults()
        self.assertNotIn("hidden_memory", [key for key in item.keys() if key != "denied_authority"])

    def test_27_no_fake_continuity(self):
        item = self.item_defaults(scope="session_only", project_id="", tenant_account_scope="", visibility="session_only")
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_28_no_silent_personalization(self):
        item = self.item_defaults(scope="user_scoped", owner_user_scope="operator")
        result = validate_memory_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_29_denied_authority_fields_remain_false_or_blocked(self):
        item = self.item_defaults()
        denied = item["denied_authority"]
        self.assertEqual(DENIED_FIELDS, set(denied))
        self.assertTrue(all(value is False for value in denied.values()))
        packet = build_memory_state_packet_v1(
            packet_id="packet_denied",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[item],
        )
        self.assertTrue(all(value is False for value in packet["denied_authority"].values()))

    def test_30_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "memory_state_model_helpers.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_31_no_runtime_or_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "memory_state_model_helpers.py").read_text(encoding="utf-8")
        for needle in ["chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_32_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_33_examples_are_synthetic_only(self):
        examples = build_initial_memory_state_examples_v1()
        self.assertGreaterEqual(len(examples), 2)
        for example in examples:
            encoded = json.dumps(example, sort_keys=True)
            self.assertIn("synthetic", encoded)
            self.assertNotIn(".weslr", encoded)

    def test_34_summary_is_compact_and_json_safe(self):
        packet = build_memory_state_packet_v1(
            packet_id="packet_summary",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            active_session_id="session_alpha",
            items=[self.item_defaults()],
        )
        summary = summarize_memory_state_packet_v1(packet)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertLess(len(encoded), 6000)
        self.assertIn("packet_summary", encoded)
        self.assertIn("item_count", summary)

    def test_35_invalid_packet_fails_closed(self):
        result = validate_memory_state_packet_v1({"bad": "packet"})
        self.assertFalse(result["valid"])
        self.assertGreater(result["violation_count"], 0)

    def test_36_validation_returns_metadata_not_exceptions(self):
        item = self.item_defaults()
        item.pop("source_ref")
        result = validate_memory_state_item_v1(item)
        self.assertIsInstance(result, dict)
        self.assertIn("violations", result)
        self.assertFalse(result["valid"])

    def test_37_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "memory_state_model_helpers.py").read_text(encoding="utf-8")
        for needle in ["open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
