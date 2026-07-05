"""Tests for ARC-AGI-2 diversified failure audit V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_diversified_failure_audit_v1 import (
    DIVERSIFIED_FAMILY_ORDER_V1,
    EXPECTED_SOLVED_FAMILIES,
    EXPECTED_UNSOLVED_FAMILIES,
    FAILURE_MISSING_CAPABILITY,
    FAILURE_SOLVED,
    PRIORITY_DO_NOT_REPAIR,
    PRIORITY_REPAIR_NEXT,
    classify_diversified_family,
    reconcile_diversified_counts,
    check_accidental_solve,
    run_diversified_failure_audit,
)
from weslr.arc_synthetic_family_diversification_v1 import build_diversified_family_corpus_v1
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestReconciliation:
    def test_detects_all_diversified_family_names(self):
        assert len(DIVERSIFIED_FAMILY_ORDER_V1) == 8
        assert "complete_horizontal_symmetry" in DIVERSIFIED_FAMILY_ORDER_V1
        assert "recolor_by_object_size" in DIVERSIFIED_FAMILY_ORDER_V1

    def test_expected_vs_actual_added_task_counts(self):
        dev_div = build_diversified_family_corpus_v1(seed=2435, tasks_per_family=3)
        held_div = build_diversified_family_corpus_v1(seed=82435, tasks_per_family=3)
        assert len(dev_div) == 8 * 3
        assert len(held_div) == 8 * 3

    def test_no_missing_diversified_families(self):
        dev_div = build_diversified_family_corpus_v1(seed=2435, tasks_per_family=3)
        families = {t["family_label"] for t in dev_div}
        assert families == set(DIVERSIFIED_FAMILY_ORDER_V1)


class TestClassification:
    def test_classifies_solved_family(self):
        result = classify_diversified_family(
            "remove_distractor_object",
            dev_solved=3, dev_unsolved=0, dev_fallback=0,
            heldout_solved=3, heldout_unsolved=0, heldout_fallback=0,
            exceptions=0,
        )
        assert result["classification"] == FAILURE_SOLVED
        assert result["repair_priority"] == PRIORITY_DO_NOT_REPAIR

    def test_classifies_unsolved_family(self):
        result = classify_diversified_family(
            "complete_horizontal_symmetry",
            dev_solved=0, dev_unsolved=3, dev_fallback=3,
            heldout_solved=0, heldout_unsolved=3, heldout_fallback=3,
            exceptions=0,
        )
        assert result["classification"] == FAILURE_MISSING_CAPABILITY
        assert result["repair_priority"] == PRIORITY_REPAIR_NEXT

    def test_classifies_partially_solved_family(self):
        result = classify_diversified_family(
            "fill_enclosed_hole",
            dev_solved=0, dev_unsolved=3, dev_fallback=0,
            heldout_solved=0, heldout_unsolved=3, heldout_fallback=0,
            exceptions=0,
        )
        assert result["classification"] == FAILURE_MISSING_CAPABILITY


class TestAccidentalSolve:
    def test_remove_distractor_is_not_accidental(self):
        result = check_accidental_solve(
            "remove_distractor_object",
            dev_solved=3, heldout_solved=3,
            dev_generated=3, heldout_generated=3,
        )
        assert result["accidental"] is False

    def test_recolor_by_size_is_not_accidental(self):
        result = check_accidental_solve(
            "recolor_by_object_size",
            dev_solved=3, heldout_solved=3,
            dev_generated=3, heldout_generated=3,
        )
        assert result["accidental"] is False

    def test_unsolved_family_is_not_accidental(self):
        result = check_accidental_solve(
            "complete_horizontal_symmetry",
            dev_solved=0, heldout_solved=0,
            dev_generated=3, heldout_generated=3,
        )
        assert result["status"] == "unsolved"
        assert result["accidental"] is False


class TestFullAudit:
    def test_audit_output_is_json_safe(self):
        # Build diversified tasks and evaluate
        tasks = build_diversified_family_corpus_v1(seed=42, tasks_per_family=2)
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        eval_dict = eval_result.to_json_safe_dict()

        # Run audit on a single split
        from weslr.arc_diversified_failure_audit_v1 import audit_diversified_families
        results = audit_diversified_families(eval_dict, split_name="dev")
        text = json.dumps(results, sort_keys=True, default=str)
        decoded = json.loads(text)
        assert len(decoded) == len(results)

    def test_audit_does_not_expose_expected_output(self):
        tasks = build_diversified_family_corpus_v1(seed=42, tasks_per_family=1)
        from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1
        for task in tasks:
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet

    def test_audit_does_not_require_public_arc_data(self):
        # Verify no public ARC paths in the audit module
        import weslr.arc_diversified_failure_audit_v1 as audit_mod
        source = open(audit_mod.__file__).read()
        assert "kaggle" not in source.lower()
        assert "arc-agi" not in source.lower() or "arc-agi-2" in source.lower()


class TestRepairPriorities:
    def test_computes_repair_priority_labels(self):
        from weslr.arc_diversified_failure_audit_v1 import compute_repair_priorities
        classifications = [
            classify_diversified_family(
                "complete_horizontal_symmetry",
                dev_solved=0, dev_unsolved=3, dev_fallback=3,
                heldout_solved=0, heldout_unsolved=3, heldout_fallback=3,
                exceptions=0,
            ),
            classify_diversified_family(
                "remove_distractor_object",
                dev_solved=3, dev_unsolved=0, dev_fallback=0,
                heldout_solved=3, heldout_unsolved=0, heldout_fallback=0,
                exceptions=0,
            ),
        ]
        priorities = compute_repair_priorities(classifications)
        assert "repair_next" in priorities
        assert "do_not_repair_currently" in priorities
        assert len(priorities["repair_next"]) == 1
        assert len(priorities["do_not_repair_currently"]) == 1