#!/usr/bin/env python3
"""Focused tests for WESLR AI audit synthetic probe helper utilities V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_probe_inventory import (  # noqa: E402
    build_ai_audit_synthetic_probe_set_v1,
    filter_ai_audit_synthetic_probes_v1,
    find_duplicate_ai_audit_probe_ids_v1,
    load_ai_audit_synthetic_probe_inventory_v1,
    summarize_ai_audit_synthetic_probe_metadata_v1,
    validate_ai_audit_synthetic_probe_selection_v1,
)


class AIAuditProbeHelpersV1Tests(unittest.TestCase):
    def test_01_category_filtering_is_deterministic_and_copied(self):
        selected = filter_ai_audit_synthetic_probes_v1(probe_categories="provenance_honesty")
        self.assertEqual(1, len(selected))
        self.assertEqual("provenance_honesty", selected[0]["probe_category"])
        selected[0]["probe_id"] = "mutated"
        canonical = filter_ai_audit_synthetic_probes_v1(probe_categories="provenance_honesty")
        self.assertNotEqual("mutated", canonical[0]["probe_id"])

    def test_02_claim_category_filtering_works(self):
        selected = filter_ai_audit_synthetic_probes_v1(claim_categories="reasoning_claim")
        self.assertGreaterEqual(len(selected), 1)
        self.assertTrue(all(probe["claim_category"] == "reasoning_claim" for probe in selected))
        ids = [probe["probe_id"] for probe in selected]
        self.assertEqual(sorted(ids), ids)

    def test_03_combined_filters_work(self):
        selected = filter_ai_audit_synthetic_probes_v1(
            probe_categories=["trace_reproducibility", "provenance_honesty"],
            claim_categories="provenance_claim",
        )
        self.assertEqual(2, len(selected))
        self.assertEqual(sorted(probe["probe_id"] for probe in selected), [probe["probe_id"] for probe in selected])

    def test_04_summary_counts_match_inventory_and_are_deterministic(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        summary_a = summarize_ai_audit_synthetic_probe_metadata_v1()
        summary_b = summarize_ai_audit_synthetic_probe_metadata_v1()
        self.assertEqual(summary_a, summary_b)
        self.assertEqual(len(inventory), summary_a["probe_count"])
        self.assertEqual(16, summary_a["probe_category_count"])
        self.assertTrue(summary_a["all_required_fields_complete"])
        self.assertEqual([], summary_a["duplicate_probe_ids"])

    def test_05_duplicate_detection_works_on_local_synthetic_data(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        duplicate = dict(inventory[0])
        inventory.append(duplicate)
        self.assertEqual([duplicate["probe_id"]], find_duplicate_ai_audit_probe_ids_v1(inventory))
        summary = summarize_ai_audit_synthetic_probe_metadata_v1(inventory)
        self.assertEqual([duplicate["probe_id"]], summary["duplicate_probe_ids"])

    def test_06_safe_selection_validation_accepts_safe_probes(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        selected_ids = [inventory[0]["probe_id"], inventory[1]["probe_id"]]
        result = validate_ai_audit_synthetic_probe_selection_v1(selected_ids)
        self.assertTrue(result["valid"])
        self.assertEqual([], result["issues"])
        self.assertEqual(2, result["selected_count"])
        self.assertFalse(result["official_score_claimed"])

    def test_07_safe_selection_validation_rejects_unknown_ids(self):
        result = validate_ai_audit_synthetic_probe_selection_v1(["unknown_probe_id"])
        self.assertFalse(result["valid"])
        self.assertIn("unknown selected probe_id: unknown_probe_id", result["issues"])
        self.assertEqual(["unknown_probe_id"], result["unknown_probe_ids"])

    def test_08_safe_selection_validation_rejects_duplicate_selected_ids(self):
        probe_id = load_ai_audit_synthetic_probe_inventory_v1()[0]["probe_id"]
        result = validate_ai_audit_synthetic_probe_selection_v1([probe_id, probe_id])
        self.assertFalse(result["valid"])
        self.assertIn(f"duplicate selected probe_id: {probe_id}", result["issues"])
        self.assertEqual([probe_id], result["duplicate_probe_ids"])

    def test_09_safe_selection_validation_rejects_unsafe_local_inventory(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        inventory[0]["protected_item_free"] = False
        result = validate_ai_audit_synthetic_probe_selection_v1([inventory[0]["probe_id"]], inventory=inventory)
        self.assertFalse(result["valid"])
        self.assertEqual([inventory[0]["probe_id"]], result["unsafe_probe_ids"])
        self.assertEqual([inventory[0]["probe_id"]], result["protected_item_probe_ids"])
        self.assertTrue(result["protected_items_copied"])
        self.assertFalse(result["answer_keys_used"])
        self.assertFalse(result["official_score_claimed"])

    def test_10_small_probe_set_respects_limit_and_filters(self):
        probe_set = build_ai_audit_synthetic_probe_set_v1(limit=2, claim_categories="reasoning_claim")
        self.assertEqual(2, probe_set["probe_count"])
        self.assertFalse(probe_set["execution_allowed"])
        self.assertFalse(probe_set["runner_created"])
        self.assertTrue(probe_set["validation"]["valid"])
        self.assertTrue(all(probe["claim_category"] == "reasoning_claim" for probe in probe_set["probes"]))

    def test_11_references_only_probe_set_omits_probe_bodies(self):
        probe_set = build_ai_audit_synthetic_probe_set_v1(limit=1, references_only=True)
        self.assertEqual(1, probe_set["probe_count"])
        self.assertEqual(1, len(probe_set["probe_ids"]))
        self.assertEqual([], probe_set["probes"])
        self.assertTrue(probe_set["redacted_count_only"])

    def test_12_canonical_inventory_not_mutated_by_probe_set_helpers(self):
        before = load_ai_audit_synthetic_probe_inventory_v1()
        probe_set = build_ai_audit_synthetic_probe_set_v1(limit=1)
        probe_set["probes"][0]["probe_id"] = "mutated"
        after = load_ai_audit_synthetic_probe_inventory_v1()
        self.assertEqual(before, after)

    def test_13_negative_limit_is_rejected_without_execution(self):
        with self.assertRaises(ValueError):
            build_ai_audit_synthetic_probe_set_v1(limit=-1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
