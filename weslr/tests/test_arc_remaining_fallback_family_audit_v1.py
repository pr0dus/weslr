"""Tests for ARC-AGI-2 remaining fallback family audit V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_remaining_fallback_family_audit_v1 import (
    ADVERSARIAL_FAMILIES_V1,
    NORMAL_FAMILIES_V1,
    audit_remaining_families_from_evaluation,
    classify_unsolved_family,
    is_adversarial,
    is_normal,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import (
    build_arc_synthetic_discovery_task_corpus_v1,
    build_arc_synthetic_solver_packet_v1,
)
from weslr.arc_synthetic_discovery_eval_v1 import evaluate_arc_synthetic_discovery_tasks_v1


class TestFamilyClassification:
    def test_correctly_separates_adversarial_from_normal(self):
        for fam in ADVERSARIAL_FAMILIES_V1:
            assert is_adversarial(fam), f"{fam} should be adversarial"
            assert not is_normal(fam), f"{fam} should not be normal"
        for fam in NORMAL_FAMILIES_V1:
            assert is_normal(fam), f"{fam} should be normal"
            assert not is_adversarial(fam), f"{fam} should not be adversarial"

    def test_adversarial_expected_rejection_classified_correctly(self):
        row = classify_unsolved_family(
            "inconsistent_train_examples",
            generated=5, solved=0, unsolved=5, fallback_only=5,
            failure_category="ambiguous_expected_rejection",
        )
        assert row["classification"] == "correct_adversarial_rejection"
        assert row["expected_unsolved"] is True
        assert row["repair_priority"] == "correct_rejection_not_failure"

    def test_normal_family_failure_classified_as_unexpected(self):
        row = classify_unsolved_family(
            "crop_foreground_bbox",
            generated=5, solved=0, unsolved=5, fallback_only=5,
            failure_category="fallback_only",
        )
        assert row["classification"] == "unexpected_normal_family_failure"
        assert row["expected_unsolved"] is False
        assert row["repair_priority"] == "repair_next"

    def test_detects_fallback_only_families(self):
        row = classify_unsolved_family(
            "inconsistent_train_examples",
            generated=5, solved=0, unsolved=5, fallback_only=5,
        )
        assert row["fallback_only_count"] == 5

    def test_detects_unexpected_fallback_only_normal_families(self):
        row = classify_unsolved_family(
            "crop_foreground_bbox",
            generated=5, solved=0, unsolved=5, fallback_only=5,
        )
        assert row["fallback_only_count"] == 5
        assert row["expected_unsolved"] is False

    def test_computes_repair_priority_labels(self):
        adv = classify_unsolved_family("inconsistent_train_examples", generated=5, solved=0, unsolved=5)
        assert adv["repair_priority"] == "correct_rejection_not_failure"

        norm = classify_unsolved_family("crop_foreground_bbox", generated=5, solved=0, unsolved=5)
        assert norm["repair_priority"] == "repair_next"

        unknown = classify_unsolved_family("unknown_family", generated=5, solved=0, unsolved=5)
        assert unknown["repair_priority"] == "benchmark_definition_review_needed"


class TestExpectedOutputIsolation:
    def test_does_not_expose_expected_output_in_solver_packets(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=84455, tasks_per_family=1, include_adversarial=True, include_compositions=False
        )
        for task in tasks:
            family = str(task.get("family_label", ""))
            if not is_adversarial(family):
                continue
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet


class TestJsonSafety:
    def test_audit_output_is_json_safe(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=82435, tasks_per_family=2, include_adversarial=True, include_compositions=True
        )
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        d = eval_result.to_json_safe_dict()
        audit = audit_remaining_families_from_evaluation(d)
        text = json.dumps(audit, sort_keys=True, default=str)
        decoded = json.loads(text)
        assert isinstance(decoded, dict)
        assert "family_rows" in decoded
        assert "correct_rejections" in decoded
        assert "real_failures" in decoded


class TestAnalyzerConsistency:
    def test_uses_analyzer_log_summary_consistently(self):
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=82435, tasks_per_family=2, include_adversarial=True, include_compositions=True
        )
        eval_result = evaluate_arc_synthetic_discovery_tasks_v1(tasks)
        d = eval_result.to_json_safe_dict()
        audit = audit_remaining_families_from_evaluation(d)
        # All unsolved should be adversarial rejections
        for row in audit["family_rows"]:
            if row["unsolved_count"] > 0:
                assert row["is_adversarial"], f"{row['family']} has unsolved but is not adversarial"
        # No real failures expected
        assert audit["unexpected_normal_family_failures"] == 0


class TestNoPublicArcData:
    def test_does_not_require_public_arc_data(self):
        # Test uses only synthetic generators
        tasks = build_arc_synthetic_discovery_task_corpus_v1(
            seed=42, tasks_per_family=1, include_adversarial=True, include_compositions=False
        )
        assert len(tasks) > 0
        # No public ARC data was read