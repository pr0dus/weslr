"""Tests for ARC-AGI-2 synthetic family diversification V1."""

from __future__ import annotations

import json

import pytest

from weslr.arc_synthetic_family_diversification_v1 import (
    DIVERSIFIED_FAMILY_ORDER_V1,
    build_diversified_family_corpus_v1,
    build_diversified_family_task_v1,
)
from weslr.arc_synthetic_discovery_task_generator_v1 import build_arc_synthetic_solver_packet_v1


class TestFamilyGeneration:
    def test_each_family_generates_valid_task(self):
        for family in DIVERSIFIED_FAMILY_ORDER_V1:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            assert task["family_label"] == family
            assert len(task["train_pairs"]) >= 1
            assert len(task["test_input"]) > 0
            assert len(task["expected_output"]) > 0
            assert task["metadata"]["expected_behavior"] == "solve"
            assert task["metadata"]["kind"] == "single_step"

    def test_each_family_is_nontrivial(self):
        for family in DIVERSIFIED_FAMILY_ORDER_V1:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            # Expected output should differ from test input (non-trivial)
            assert task["expected_output"] != task["test_input"], (
                f"{family} has identity expected output"
            )

    def test_same_seed_produces_same_corpus(self):
        c1 = build_diversified_family_corpus_v1(seed=42, tasks_per_family=2)
        c2 = build_diversified_family_corpus_v1(seed=42, tasks_per_family=2)
        assert json.dumps(c1, sort_keys=True) == json.dumps(c2, sort_keys=True)

    def test_different_seed_changes_task_identity(self):
        c1 = build_diversified_family_corpus_v1(seed=42, tasks_per_family=1)
        c2 = build_diversified_family_corpus_v1(seed=43, tasks_per_family=1)
        ids1 = {t["task_id"] for t in c1}
        ids2 = {t["task_id"] for t in c2}
        assert ids1.isdisjoint(ids2)

    def test_corpus_has_correct_family_count(self):
        corpus = build_diversified_family_corpus_v1(seed=42, tasks_per_family=3)
        families = {t["family_label"] for t in corpus}
        assert families == set(DIVERSIFIED_FAMILY_ORDER_V1)
        assert len(corpus) == len(DIVERSIFIED_FAMILY_ORDER_V1) * 3


class TestExpectedOutputIsolation:
    def test_expected_output_not_in_solver_packet(self):
        for family in DIVERSIFIED_FAMILY_ORDER_V1:
            task = build_diversified_family_task_v1(family, seed=42, variant="v0")
            packet = build_arc_synthetic_solver_packet_v1(task)
            assert "expected_output" not in packet, (
                f"{family} leaks expected_output in solver packet"
            )


class TestDeterminism:
    def test_dev_heldout_task_ids_disjoint(self):
        dev = build_diversified_family_corpus_v1(seed=2435, tasks_per_family=3)
        held = build_diversified_family_corpus_v1(seed=82435, tasks_per_family=3)
        dev_ids = {t["task_id"] for t in dev}
        held_ids = {t["task_id"] for t in held}
        assert dev_ids.isdisjoint(held_ids), "Dev and heldout task IDs overlap"


class TestJsonSafety:
    def test_tasks_are_json_safe(self):
        corpus = build_diversified_family_corpus_v1(seed=42, tasks_per_family=2)
        text = json.dumps(corpus, sort_keys=True, default=str)
        decoded = json.loads(text)
        assert len(decoded) == len(corpus)


class TestNoPublicArcPaths:
    def test_no_public_arc_paths(self):
        corpus = build_diversified_family_corpus_v1(seed=42, tasks_per_family=1)
        text = json.dumps(corpus, sort_keys=True, default=str)
        assert "kaggle" not in text.lower()
        assert "arc-agi" not in text.lower()
        assert "public" not in text.lower() or "public_solution" not in text