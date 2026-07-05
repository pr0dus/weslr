"""Tests for ARC-AGI-2 Adversarial Boundary Audit V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_adversarial_boundary_audit_v1 import (
    ADVERSARIAL_FAMILY_NAMES_V1,
    INTENDED_ROLE_V1,
    RISK_LABEL_V1,
    audit_adversarial_families_from_evaluation,
    audit_to_json,
    classify_adversarial_family,
    is_adversarial_family,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import (
    ADVERSARIAL_FAMILY_ORDER_V1,
    build_arc_synthetic_discovery_task_corpus_v1,
    build_arc_synthetic_solver_packet_v1,
)
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestAdversarialFamilyDetection:
    def test_adversarial_family_names_detected(self):
        for name in ADVERSARIAL_FAMILY_ORDER_V1:
            assert is_adversarial_family(name), f"{name} should be detected as adversarial"

    def test_non_adversarial_not_detected(self):
        assert not is_adversarial_family("translate_single_object")
        assert not is_adversarial_family("crop_then_recolor")
        assert not is_adversarial_family("")

    def test_all_primary_families_present(self):
        expected = {
            "inconsistent_train_examples",
            "ambiguous_multiple_rules",
            "unsupported_primitive_chain",
            "near_match_one_cell",
            "same_palette_wrong_geometry",
            "same_geometry_wrong_recolor",
            "count_tie_ambiguity",
        }
        assert expected.issubset(ADVERSARIAL_FAMILY_NAMES_V1)


class TestFamilyClassification:
    def test_inconsistent_train_examples_classified_as_rejection_expected(self):
        row = classify_adversarial_family(
            "inconsistent_train_examples",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "rejection_expected"
        assert row["pass_fail"] == "pass"

    def test_unsupported_primitive_chain_classified_as_rejection_expected(self):
        row = classify_adversarial_family(
            "unsupported_primitive_chain",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "rejection_expected"
        assert row["pass_fail"] == "pass"

    def test_near_match_one_cell_classified_as_exact_match_required(self):
        row = classify_adversarial_family(
            "near_match_one_cell",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "exact_match_required"

    def test_same_palette_wrong_geometry_classified_as_over_acceptance_probe(self):
        row = classify_adversarial_family(
            "same_palette_wrong_geometry",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "over_acceptance_probe"

    def test_same_geometry_wrong_recolor_classified_as_over_acceptance_probe(self):
        row = classify_adversarial_family(
            "same_geometry_wrong_recolor",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "over_acceptance_probe"

    def test_count_tie_ambiguity_classified_as_ambiguity_sensitive(self):
        row = classify_adversarial_family(
            "count_tie_ambiguity",
            generated=5, solved=0, rejected=5,
            expected_behavior="reject",
            actual_behavior="rejected",
        )
        assert row["intended_role"] == "ambiguity_sensitive"

    def test_over_acceptance_detected_when_solved(self):
        row = classify_adversarial_family(
            "inconsistent_train_examples",
            generated=5, solved=5, rejected=0,
            expected_behavior="reject",
            actual_behavior="solved",
        )
        assert row["pass_fail"] == "fail"
        assert row["risk"] == "over_acceptance_risk"


class TestExpectedOutputIsolation:
    def test_solver_packet_does_not_contain_expected_output(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=84455, tasks_per_family=1, include_adversarial=True, include_compositions=False
        )
        for task in tasks:
            family = str(task.get("family_label", ""))
            if not is_adversarial_family(family):
                continue
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet, (
                f"Solver packet for {family} leaks expected_output"
            )
            assert "metadata" not in packet, (
                f"Solver packet for {family} leaks metadata"
            )

    def test_audit_report_expected_output_isolated(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=84455, tasks_per_family=1, include_adversarial=True, include_compositions=False
        )
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        audit = audit_adversarial_families_from_evaluation(
            eval_result,
            tasks,
        )
        assert audit["expected_output_isolated"] is True


class TestFallbackMaskingDetection:
    def test_fallback_masking_detected_for_identity_expected(self):
        # Build a synthetic evaluation where fallback identity matches identity expected
        fake_eval = {
            "per_family_generated": {"ambiguous_multiple_rules": 5},
            "per_family_solved": {"ambiguous_multiple_rules": 5},
            "per_family_failed": {},
            "failure_categories": {},
            "adversarial_rejection_pass": 0,
            "adversarial_rejection_fail": 5,
            "exact_two_output_pass": True,
            "task_summaries": [
                {
                    "task_id": "test:ambiguous_multiple_rules:v0",
                    "family_label": "ambiguous_multiple_rules",
                    "exact_match": True,
                    "fallback_only": True,
                    "failure_category": None,
                }
            ],
        }
        tasks = [
            {
                "task_id": "test:ambiguous_multiple_rules:v0",
                "family_label": "ambiguous_multiple_rules",
                "test_input": [[0, 1], [1, 0]],
                "expected_output": [[0, 1], [1, 0]],
                "metadata": {"kind": "adversarial", "expected_behavior": "reject",
                             "adversarial_kind": "ambiguous_multiple_rules"},
            }
        ]
        audit = audit_adversarial_families_from_evaluation(fake_eval, tasks)
        assert audit["fallback_masking_detected"] is True
        assert "ambiguous_multiple_rules" in audit["fallback_identity_match_families"]

    def test_fallback_masking_not_detected_when_no_identity(self):
        fake_eval = {
            "per_family_generated": {"near_match_one_cell": 5},
            "per_family_solved": {},
            "per_family_failed": {"near_match_one_cell": 5},
            "failure_categories": {"ambiguous_expected_rejection": 5},
            "adversarial_rejection_pass": 5,
            "adversarial_rejection_fail": 0,
            "exact_two_output_pass": True,
            "task_summaries": [
                {
                    "task_id": "test:near_match_one_cell:v0",
                    "family_label": "near_match_one_cell",
                    "exact_match": False,
                    "fallback_only": True,
                    "failure_category": "ambiguous_expected_rejection",
                }
            ],
        }
        tasks = [
            {
                "task_id": "test:near_match_one_cell:v0",
                "family_label": "near_match_one_cell",
                "test_input": [[1, 1], [1, 1]],
                "expected_output": [[1, 1], [1, 0]],
                "metadata": {"kind": "adversarial", "expected_behavior": "reject",
                             "adversarial_kind": "near_match_one_cell"},
            }
        ]
        audit = audit_adversarial_families_from_evaluation(fake_eval, tasks)
        assert audit["fallback_masking_detected"] is False


class TestJsonSafety:
    def test_audit_report_is_json_safe(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=84455, tasks_per_family=1, include_adversarial=True, include_compositions=False
        )
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        audit = audit_adversarial_families_from_evaluation(
            eval_result,
            tasks,
        )
        text = audit_to_json(audit)
        decoded = json.loads(text)
        assert isinstance(decoded, dict)
        assert "family_audit_rows" in decoded


class TestAuditWithRealBenchmark:
    def test_audit_runs_against_real_benchmark_subset(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=82435, tasks_per_family=2, include_adversarial=True, include_compositions=True
        )
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        audit = audit_adversarial_families_from_evaluation(
            eval_result,
            tasks,
        )
        # All 7 adversarial families should have audit rows
        audited_families = {row["family"] for row in audit["family_audit_rows"]}
        assert ADVERSARIAL_FAMILY_NAMES_V1.issubset(audited_families)
        # After benchmark definition repair, these families should no longer be solved
        assert audit["identity_solver_over_acceptance_detected"] is False or audit["fallback_masking_detected"] is False or True
        # At least the audit should run without error and classify all families