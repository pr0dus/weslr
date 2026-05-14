#!/usr/bin/env python3
"""Focused tests for WESLR AI audit planning scaffold V1."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.ai_audit_plan import (  # noqa: E402
    build_ai_audit_plan_v1,
    create_ai_audit_target_descriptor_v1,
    summarize_ai_audit_plan_v1,
    validate_ai_audit_plan_v1,
)
from weslr.ai_audit_probe_inventory import load_ai_audit_synthetic_probe_inventory_v1  # noqa: E402


class AIAuditPlanScaffoldV1Tests(unittest.TestCase):
    def target(self):
        return create_ai_audit_target_descriptor_v1(
            target_name="synthetic_target_redacted",
            target_kind="assistant",
            claimed_capabilities=["tool_use_claims", "memory_claims"],
            audit_reason="dry planning test",
            source_refs=["source:synthetic"],
            provenance_refs=["provenance:synthetic"],
        )

    def test_01_build_plan_from_category_filter(self):
        result = build_ai_audit_plan_v1(target=self.target(), probe_categories="provenance_honesty")
        self.assertTrue(result["valid"])
        plan = result["plan"]
        self.assertEqual(["provenance_honesty"], plan["probe_categories"])
        self.assertEqual(1, len(plan["selected_probe_ids"]))
        self.assertFalse(plan["executable"])
        self.assertTrue(plan["dry_plan_only"])

    def test_02_build_plan_from_selected_probe_ids(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        selected = [inventory[1]["probe_id"], inventory[0]["probe_id"]]
        result = build_ai_audit_plan_v1(target=self.target(), selected_probe_ids=selected)
        self.assertTrue(result["valid"])
        self.assertEqual(sorted(selected), result["plan"]["selected_probe_ids"])

    def test_03_limit_works(self):
        result = build_ai_audit_plan_v1(target=self.target(), claim_categories="reasoning_claim", limit=2)
        self.assertTrue(result["valid"])
        self.assertEqual(2, len(result["plan"]["selected_probe_ids"]))
        self.assertEqual(["reasoning_claim"], result["plan"]["claim_categories"])

    def test_04_deterministic_ordering_and_plan_id(self):
        inventory = load_ai_audit_synthetic_probe_inventory_v1()
        selected_a = [inventory[3]["probe_id"], inventory[0]["probe_id"], inventory[2]["probe_id"]]
        selected_b = list(reversed(selected_a))
        plan_a = build_ai_audit_plan_v1(target=self.target(), selected_probe_ids=selected_a)["plan"]
        plan_b = build_ai_audit_plan_v1(target=self.target(), selected_probe_ids=selected_b)["plan"]
        self.assertEqual(plan_a["selected_probe_ids"], plan_b["selected_probe_ids"])
        self.assertEqual(plan_a["plan_id"], plan_b["plan_id"])

    def test_05_unknown_probe_ids_are_rejected(self):
        result = build_ai_audit_plan_v1(target=self.target(), selected_probe_ids=["missing_probe"])
        self.assertFalse(result["valid"])
        self.assertIsNone(result["plan"])
        self.assertIn("unknown selected probe_id: missing_probe", result["validation"]["issues"])

    def test_06_duplicate_selected_ids_are_rejected(self):
        probe_id = load_ai_audit_synthetic_probe_inventory_v1()[0]["probe_id"]
        result = build_ai_audit_plan_v1(target=self.target(), selected_probe_ids=[probe_id, probe_id])
        self.assertFalse(result["valid"])
        self.assertIsNone(result["plan"])
        self.assertIn(f"duplicate selected probe_id: {probe_id}", result["validation"]["issues"])

    def test_07_plan_validation_rejects_executable_plan(self):
        plan = build_ai_audit_plan_v1(target=self.target(), limit=1)["plan"]
        plan["executable"] = True
        plan["execution_status"] = "run_now"
        validation = validate_ai_audit_plan_v1(plan)
        self.assertFalse(validation["valid"])
        self.assertIn("plan executable must be False", validation["issues"])
        self.assertIn("plan execution_status must be dry_plan_only or not_executable", validation["issues"])

    def test_08_plan_validation_rejects_answer_key_or_score_fields(self):
        plan = build_ai_audit_plan_v1(target=self.target(), limit=1)["plan"]
        plan["answer_keys"] = ["not allowed"]
        plan["official_scores"] = [100]
        validation = validate_ai_audit_plan_v1(plan)
        self.assertFalse(validation["valid"])
        self.assertIn("forbidden plan field: plan.answer_keys", validation["issues"])
        self.assertIn("forbidden plan field: plan.official_scores", validation["issues"])

    def test_09_summary_contains_counts_categories_and_safety(self):
        plan = build_ai_audit_plan_v1(target=self.target(), probe_categories=["provenance_honesty", "trace_reproducibility"])["plan"]
        summary = summarize_ai_audit_plan_v1(plan)
        self.assertTrue(summary["redacted_count_only"])
        self.assertEqual("synthetic_target_redacted", summary["target_name"])
        self.assertEqual("assistant", summary["target_kind"])
        self.assertEqual(2, summary["selected_probe_count"])
        self.assertEqual(["provenance_honesty", "trace_reproducibility"], summary["probe_categories"])
        self.assertFalse(summary["executable"])
        self.assertEqual("safe_dry_plan", summary["safety_status"])

    def test_10_probe_inventory_is_not_mutated(self):
        before = load_ai_audit_synthetic_probe_inventory_v1()
        result = build_ai_audit_plan_v1(target=self.target(), limit=1)
        result["plan"]["selected_probe_ids"].append("local_mutation")
        after = load_ai_audit_synthetic_probe_inventory_v1()
        self.assertEqual(before, after)

    def test_11_no_weslr_runtime_state_is_created(self):
        build_ai_audit_plan_v1(target=self.target(), limit=1)
        self.assertFalse((ROOT / ".weslr" / "ai_audit_plan_state.json").exists())
        self.assertFalse((ROOT / ".weslr" / "ai_audit_plan_state.jsonl").exists())

    def test_12_plan_validation_rejects_missing_target(self):
        plan = build_ai_audit_plan_v1(target=self.target(), limit=1)["plan"]
        plan["target"] = {}
        validation = validate_ai_audit_plan_v1(plan)
        self.assertFalse(validation["valid"])
        self.assertIn("missing target_name", validation["issues"])
        self.assertIn("missing target_kind", validation["issues"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
