#!/usr/bin/env python3
"""Tests for WESLR AI audit synthetic probe inventory V1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_probe_inventory import (  # noqa: E402
    REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_CATEGORIES,
    REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_FIELDS,
    load_ai_audit_synthetic_probe_inventory_v1,
    summarize_ai_audit_synthetic_probe_inventory_v1,
    validate_ai_audit_synthetic_probe_inventory_v1,
)

ALLOWED_CHANGED = {
    "weslr/ai_audit_probe_inventory.py",
    "weslr/tests/test_ai_audit_probe_inventory_v1.py",
}
FORBIDDEN_CHANGED = {
    "weslr/voice_gateway.py",
    "weslr/ambient_voice_loop.py",
    "weslr/proactive_daemon.py",
    "weslr/proactive_suggestions.py",
    "weslr/pending_messages_queue.py",
    "weslr/capability_router.py",
    "weslr/capability_welcome_surface.py",
    "weslr/who_said_that_chat_routing.py",
    "weslr/who_said_that_runtime_query.py",
    "openclaw.json",
    ".openclaw/config.json",
}


class AIAuditProbeInventoryV1Tests(unittest.TestCase):
    def git_changed_files(self) -> set[str]:
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=str(ROOT), text=True).splitlines()
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=str(ROOT), text=True).splitlines()
        return set(changed + staged + untracked)

    def test_01_inventory_imports(self):
        self.assertTrue(load_ai_audit_synthetic_probe_inventory_v1)
        self.assertTrue(summarize_ai_audit_synthetic_probe_inventory_v1)
        self.assertTrue(validate_ai_audit_synthetic_probe_inventory_v1)

    def test_02_inventory_loads(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        self.assertIsInstance(inventory, list)
        self.assertTrue(all(isinstance(item, dict) for item in inventory))

    def test_03_at_least_12_probes_exist(self):
        self.assertGreaterEqual(len(load_ai_audit_synthetic_probe_inventory_v1()), 12)

    def test_04_all_required_probe_categories_represented(self):
        categories = {item["probe_category"] for item in load_ai_audit_synthetic_probe_inventory_v1()}
        self.assertTrue(REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_CATEGORIES.issubset(categories))

    def test_05_all_probe_ids_unique(self):
        ids = [item["probe_id"] for item in load_ai_audit_synthetic_probe_inventory_v1()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_06_all_required_fields_present(self):
        for item in load_ai_audit_synthetic_probe_inventory_v1():
            self.assertTrue(REQUIRED_AI_AUDIT_SYNTHETIC_PROBE_FIELDS.issubset(item.keys()))

    def test_07_all_probes_are_protected_item_free(self):
        self.assertTrue(all(item["protected_item_free"] is True for item in load_ai_audit_synthetic_probe_inventory_v1()))

    def test_08_all_probes_are_answer_key_free(self):
        self.assertTrue(all(item["answer_key_free"] is True for item in load_ai_audit_synthetic_probe_inventory_v1()))

    def test_09_no_official_score_claims(self):
        self.assertTrue(all(item["official_score_claimed"] is False for item in load_ai_audit_synthetic_probe_inventory_v1()))

    def test_10_no_benchmark_tuning(self):
        self.assertTrue(all(item["benchmark_tuning"] is False for item in load_ai_audit_synthetic_probe_inventory_v1()))

    def test_11_no_runtime_behavior_change(self):
        self.assertTrue(all(item["runtime_behavior_change"] is False for item in load_ai_audit_synthetic_probe_inventory_v1()))

    def test_12_validation_passes_default_inventory(self):
        self.assertEqual([], validate_ai_audit_synthetic_probe_inventory_v1())

    def test_13_summaries_are_redacted_count_only(self):
        summary = summarize_ai_audit_synthetic_probe_inventory_v1()
        self.assertTrue(summary["redacted_count_only"])
        self.assertEqual(16, summary["probe_count"])
        combined = repr(summary).lower()
        self.assertNotIn("safe_prompt_summary", combined)
        self.assertNotIn("probe_goal", combined)
        self.assertNotIn("target_claim_summary", combined)
        self.assertNotIn("failure_modes", combined)
        self.assertFalse(summary["protected_items_copied"])
        self.assertFalse(summary["answer_keys_used"])
        self.assertFalse(summary["official_score_claimed"])
        self.assertFalse(summary["benchmark_tuning_performed"])
        self.assertFalse(summary["runtime_behavior_changed"])

    def test_14_validation_catches_missing_ids(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["probe_id"] = ""
        self.assertIn("probe[0] missing probe_id", validate_ai_audit_synthetic_probe_inventory_v1(inventory))

    def test_15_validation_catches_unsafe_protected_item_flag(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["protected_item_free"] = False
        self.assertIn("probe[0] protected_item_free must be True", validate_ai_audit_synthetic_probe_inventory_v1(inventory))

    def test_16_validation_catches_answer_key_flag(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["answer_key_free"] = False
        self.assertIn("probe[0] answer_key_free must be True", validate_ai_audit_synthetic_probe_inventory_v1(inventory))

    def test_17_validation_catches_official_score_flag(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["official_score_claimed"] = True
        self.assertIn("probe[0] official_score_claimed must be False", validate_ai_audit_synthetic_probe_inventory_v1(inventory))

    def test_18_validation_catches_benchmark_tuning_flag(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["benchmark_tuning"] = True
        self.assertIn("probe[0] benchmark_tuning must be False", validate_ai_audit_synthetic_probe_inventory_v1(inventory))

    def test_19_no_runtime_chat_voice_files_changed(self):
        changed = self.git_changed_files()
        self.assertTrue(changed.issubset(ALLOWED_CHANGED), sorted(changed - ALLOWED_CHANGED))
        self.assertFalse(changed & FORBIDDEN_CHANGED, sorted(changed & FORBIDDEN_CHANGED))


if __name__ == "__main__":
    unittest.main(verbosity=2)
