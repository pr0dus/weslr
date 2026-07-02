from __future__ import annotations

import json

from weslr.arc_synthetic_official_shape_mock_generator import (
    MOCK_BATCH_COUNT_V1,
    MOCK_BATCH_SEEDS_V1,
    MOCK_TASKS_PER_BATCH_V1,
    build_arc_synthetic_official_shape_mock_bundle_v1,
    summarize_arc_synthetic_official_shape_mock_bundle_v1,
    validate_arc_synthetic_official_shape_mock_bundle_v1,
)


def test_mock_bundle_is_deterministic_safe_and_seeded() -> None:
    first = build_arc_synthetic_official_shape_mock_bundle_v1()
    second = build_arc_synthetic_official_shape_mock_bundle_v1()
    validation = validate_arc_synthetic_official_shape_mock_bundle_v1(first)
    summary = summarize_arc_synthetic_official_shape_mock_bundle_v1(first)
    assert first == second
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert first["synthetic_only"] is True
    assert first["official_data_touched"] is False
    assert first["public_data_touched"] is False
    assert first["network_touched"] is False
    assert first["batch_count"] == MOCK_BATCH_COUNT_V1
    assert first["seeds"] == list(MOCK_BATCH_SEEDS_V1)
    assert first["task_count"] == MOCK_BATCH_COUNT_V1 * MOCK_TASKS_PER_BATCH_V1
    assert json.dumps(first, ensure_ascii=False)


def test_mock_bundle_keeps_hidden_outputs_out_of_solver_visible_tasks() -> None:
    bundle = build_arc_synthetic_official_shape_mock_bundle_v1()
    for batch in bundle["batches"]:
        assert batch["task_count"] == MOCK_TASKS_PER_BATCH_V1
        assert len(batch["family_ids"]) > 1
        for task in batch["solver_visible_tasks"]:
            assert "expected_outputs" not in task
            assert "reference_outputs" not in task
            assert task["trace"]["mock_official_shape"] is True
            assert task["trace"]["no_official_arc_data"] is True
            assert task["trace"]["no_public_arc_data"] is True
        for reference in batch["reference_tasks"]:
            assert reference["synthetic_only"] is True
            assert reference["hidden_only"] is True
            assert reference["expected_output_count"] == 1


def test_mock_family_manifest_tracks_batch_families() -> None:
    bundle = build_arc_synthetic_official_shape_mock_bundle_v1()
    family_manifest = bundle["family_manifest"]
    assert len(family_manifest) == MOCK_BATCH_COUNT_V1
    assert all(entry["task_count"] == MOCK_TASKS_PER_BATCH_V1 for entry in family_manifest)
    assert all(len(entry["family_ids"]) > 1 for entry in family_manifest)
    assert {entry["seed"] for entry in family_manifest} == set(MOCK_BATCH_SEEDS_V1)
