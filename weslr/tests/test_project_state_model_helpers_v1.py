#!/usr/bin/env python3
"""Focused tests for WESLR project state model helpers v1."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.project_state_model_helpers import (  # noqa: E402
    allowed_project_state_phases_v1,
    allowed_project_state_scopes_v1,
    allowed_project_state_statuses_v1,
    build_initial_project_state_examples_v1,
    build_project_state_item_v1,
    build_project_state_packet_v1,
    classify_project_state_item_v1,
    summarize_project_state_packet_v1,
    to_project_state_json_safe_v1,
    validate_project_state_item_v1,
    validate_project_state_packet_v1,
)

DENIED_FIELDS = {
    "runtime_wiring_authority",
    "chat_responder_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_persistence_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "external_action_authority",
    "cross_user_leakage_authority",
    "hidden_project_state_authority",
    "hidden_personalization_authority",
    "public_product_readiness_authority",
}


class ProjectStateModelHelpersV1Tests(unittest.TestCase):
    def item_defaults(self, **overrides):
        visibility = overrides.get("visibility", "project_scoped")
        phase = overrides.get("project_phase", "intake")
        status = overrides.get("project_status")
        defaults = {
            "project_id": overrides.get("project_id", "project_alpha"),
            "item_id": overrides.get("item_id", f"project_alpha_{phase}"),
            "owner_user_scope": overrides.get("owner_user_scope", "operator"),
            "tenant_account_scope": overrides.get("tenant_account_scope", "self"),
            "session_id": overrides.get("session_id", "session_alpha"),
            "project_status": status,
            "project_phase": phase,
            "state_kind": overrides.get("state_kind", "project_state"),
            "title": overrides.get("title", "Project Alpha"),
            "summary": overrides.get("summary", "Synthetic project continuity metadata"),
            "goal": overrides.get("goal", "preserve continuity"),
            "open_questions": overrides.get("open_questions", ["What is the safe next step?"]),
            "constraints": overrides.get("constraints", ["No runtime wiring"]),
            "decisions": overrides.get("decisions", ["Use metadata-only helpers"]),
            "tasks": overrides.get("tasks", ["review project state"]),
            "blocked_items": overrides.get("blocked_items", []),
            "linked_memory_refs": overrides.get("linked_memory_refs", ["memory_ref_alpha"]),
            "linked_artifact_refs": overrides.get("linked_artifact_refs", ["artifact_ref_alpha"]),
            "linked_support_refs": overrides.get("linked_support_refs", ["support_ref_alpha"]),
            "source_type": overrides.get("source_type", "synthetic"),
            "source_ref": overrides.get("source_ref", "source_alpha"),
            "visibility": visibility,
            "correction_path": overrides.get("correction_path", "review_and_refresh"),
            "stale": overrides.get("stale", False),
            "contradicted": overrides.get("contradicted", False),
            "invalidated": overrides.get("invalidated", False),
            "pending_approval": overrides.get("pending_approval", False),
            "blocked_reason": overrides.get("blocked_reason", ""),
            "audit_note": overrides.get("audit_note", "synthetic metadata"),
            "created_marker": overrides.get("created_marker", "created_alpha"),
            "updated_marker": overrides.get("updated_marker", "updated_alpha"),
            "denied_authority": {field: False for field in DENIED_FIELDS},
        }
        defaults.update(overrides)
        if defaults["project_status"] is None:
            defaults["project_status"] = {
                "intake": "proposed",
                "clarification": "proposed",
                "planning": "provisional",
                "research": "provisional",
                "drafting": "active_metadata_only",
                "review": "pending_approval",
                "blocked": "blocked",
                "paused": "stale",
                "archived": "archived_deprecated",
            }.get(phase, "active_metadata_only")
        return build_project_state_item_v1(**defaults)

    def test_01_allowed_statuses_include_required_statuses(self):
        allowed = set(allowed_project_state_statuses_v1())
        expected = {
            "proposed",
            "provisional",
            "active_metadata_only",
            "pending_approval",
            "blocked",
            "stale",
            "contradicted",
            "invalidated",
            "archived_deprecated",
            "failed",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_02_allowed_phases_include_required_phases(self):
        allowed = set(allowed_project_state_phases_v1())
        expected = {
            "intake",
            "clarification",
            "planning",
            "research",
            "drafting",
            "review",
            "blocked",
            "paused",
            "archived",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_03_allowed_scopes_include_required_scopes(self):
        allowed = set(allowed_project_state_scopes_v1())
        expected = {
            "project_scoped",
            "user_scoped",
            "tenant_account_scoped",
            "operator_scoped",
        }
        self.assertTrue(expected.issubset(allowed))

    def test_04_builds_valid_item(self):
        item = self.item_defaults()
        result = validate_project_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])

    def test_05_builds_valid_packet(self):
        items = [
            self.item_defaults(item_id="project_alpha_project", visibility="project_scoped"),
            self.item_defaults(item_id="project_alpha_user", visibility="user_scoped", owner_user_scope="operator"),
            self.item_defaults(item_id="project_alpha_tenant", visibility="tenant_account_scoped", tenant_account_scope="self"),
            self.item_defaults(item_id="project_alpha_operator", visibility="operator_scoped", audit_note="operator trace metadata"),
        ]
        packet = build_project_state_packet_v1(
            packet_id="packet_alpha",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            items=items,
            limitations=["synthetic example"],
        )
        result = validate_project_state_packet_v1(packet)
        self.assertTrue(result["valid"], result["violations"])

    def test_06_item_and_packet_are_json_safe(self):
        item = self.item_defaults()
        packet = build_project_state_packet_v1(
            packet_id="packet_json",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            items=[item],
        )
        safe = to_project_state_json_safe_v1(packet)
        encoded = json.dumps(safe, sort_keys=True)
        self.assertIn("packet_json", encoded)
        self.assertIn("project_alpha", encoded)

    def test_07_validation_rejects_missing_required_fields(self):
        item = self.item_defaults()
        for field in ["project_id", "project_status", "project_phase", "source_ref", "source_type"]:
            item.pop(field, None)
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["violation_count"], 5)

    def test_08_unknown_status_fails_closed(self):
        item = self.item_defaults(project_status="impossible")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown status" in violation for violation in result["violations"]))

    def test_09_unknown_phase_fails_closed(self):
        item = self.item_defaults(project_phase="impossible")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown phase" in violation for violation in result["violations"]))

    def test_10_unknown_scope_fails_closed(self):
        item = self.item_defaults()
        item["visibility"] = "impossible"
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown scope" in violation for violation in result["violations"]))

    def test_11_project_scoped_item_requires_project_id(self):
        item = self.item_defaults()
        item["project_id"] = ""
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("project_id missing or blank" in violation for violation in result["violations"]))

    def test_12_user_scoped_item_requires_owner_user_scope(self):
        item = self.item_defaults(visibility="user_scoped", owner_user_scope="")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("user_scoped project state requires owner_user_scope" in violation for violation in result["violations"]))

    def test_13_tenant_scoped_item_requires_tenant_account_scope(self):
        item = self.item_defaults(visibility="tenant_account_scoped", tenant_account_scope="")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("tenant_account_scoped project state requires tenant_account_scope" in violation for violation in result["violations"]))

    def test_14_stale_state_is_surfaced(self):
        item = self.item_defaults(project_status="stale", stale=True)
        result = validate_project_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_project_state_item_v1(item)
        self.assertEqual("stale", classification["status"])
        self.assertEqual("review_required", classification["risk"])

    def test_15_contradicted_state_is_surfaced_and_not_active(self):
        item = self.item_defaults(project_status="contradicted", contradicted=True)
        result = validate_project_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_project_state_item_v1(item)
        self.assertEqual("contradicted", classification["status"])
        self.assertEqual("blocked", classification["risk"])

    def test_16_invalidated_state_is_surfaced_and_not_active(self):
        item = self.item_defaults(project_status="invalidated", invalidated=True)
        result = validate_project_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        classification = classify_project_state_item_v1(item)
        self.assertEqual("invalidated", classification["status"])
        self.assertEqual("blocked", classification["risk"])

    def test_17_pending_approvals_are_preserved(self):
        item = self.item_defaults(project_status="pending_approval", pending_approval=True, project_phase="review")
        packet = build_project_state_packet_v1(
            packet_id="packet_pending",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            items=[item],
        )
        summary = summarize_project_state_packet_v1(packet)
        self.assertEqual(1, summary["pending_count"])
        self.assertEqual(1, len(summary["pending_approvals"]))

    def test_18_blocked_item_requires_blocked_reason(self):
        item = self.item_defaults(project_status="blocked", project_phase="blocked", blocked_reason="")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("blocked project state requires blocked_reason" in violation for violation in result["violations"]))

    def test_19_linked_refs_do_not_grant_authority(self):
        item = self.item_defaults(
            linked_memory_refs=["memory_ref_alpha"],
            linked_artifact_refs=["artifact_ref_alpha"],
            linked_support_refs=["support_ref_alpha"],
        )
        result = validate_project_state_item_v1(item)
        self.assertTrue(result["valid"], result["violations"])
        self.assertTrue(item["linked_memory_refs"])
        self.assertTrue(item["linked_artifact_refs"])
        self.assertTrue(item["linked_support_refs"])

    def test_20_no_hidden_project_state(self):
        item = self.item_defaults()
        self.assertEqual("project_scoped", item["visibility"])
        self.assertNotIn("hidden_project_state", [k for k in item.keys() if k != "denied_authority"])

    def test_21_cross_user_leakage_fails_closed(self):
        item = self.item_defaults(project_id="shared_project_alpha")
        result = validate_project_state_item_v1(item)
        self.assertFalse(result["valid"])
        self.assertTrue(any("cross-user project state fails closed" in violation for violation in result["violations"]))

    def test_22_denied_authority_fields_remain_false_or_blocked(self):
        item = self.item_defaults()
        denied = item["denied_authority"]
        self.assertEqual(DENIED_FIELDS, set(denied))
        self.assertTrue(all(value is False for value in denied.values()))
        packet = build_project_state_packet_v1(
            packet_id="packet_denied",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            items=[item],
        )
        self.assertTrue(all(value is False for value in packet["denied_authority"].values()))

    def test_23_no_weslr_io(self):
        source = Path(ROOT / "weslr" / "project_state_model_helpers.py").read_text(encoding="utf-8")
        self.assertNotIn(".weslr", source)

    def test_24_no_runtime_or_protected_module_imports(self):
        source = Path(ROOT / "weslr" / "project_state_model_helpers.py").read_text(encoding="utf-8")
        for needle in ["chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)

    def test_25_no_protected_file_drift(self):
        protected = ["weslr/chat_responder.py", "weslr/main.py", "main.py", "dialogue.py", "chat_ui.py"]
        for rel in protected:
            with self.subTest(rel=rel):
                subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)

    def test_26_examples_are_synthetic_only(self):
        examples = build_initial_project_state_examples_v1()
        self.assertGreaterEqual(len(examples), 2)
        for example in examples:
            self.assertIn("project_summary", json.dumps(example, sort_keys=True))
            self.assertNotIn(".weslr", json.dumps(example, sort_keys=True))

    def test_27_summary_is_compact_and_json_safe(self):
        packet = build_project_state_packet_v1(
            packet_id="packet_summary",
            owner_user_scope="operator",
            tenant_account_scope="self",
            active_project_id="project_alpha",
            items=[self.item_defaults()],
        )
        summary = summarize_project_state_packet_v1(packet)
        encoded = json.dumps(summary, sort_keys=True)
        self.assertLess(len(encoded), 6000)
        self.assertIn("packet_summary", encoded)
        self.assertIn("item_count", summary)

    def test_28_invalid_packet_fails_closed(self):
        result = validate_project_state_packet_v1({"bad": "packet"})
        self.assertFalse(result["valid"])
        self.assertGreater(result["violation_count"], 0)

    def test_29_validation_returns_metadata_not_exceptions(self):
        item = self.item_defaults()
        item.pop("source_ref")
        result = validate_project_state_item_v1(item)
        self.assertIsInstance(result, dict)
        self.assertIn("violations", result)
        self.assertFalse(result["valid"])

    def test_30_helper_has_no_filesystem_network_subprocess_side_effects(self):
        source = Path(ROOT / "weslr" / "project_state_model_helpers.py").read_text(encoding="utf-8")
        for needle in ["open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"]:
            with self.subTest(needle=needle):
                self.assertNotIn(needle, source)


if __name__ == "__main__":
    unittest.main()
