from __future__ import annotations

from types import SimpleNamespace

import weslr.arc_universal_family_runner_v1 as runner_module
from weslr.arc_family_discovery_engine_v1 import FamilyDiscoveryResult, FamilyHypothesis
from weslr.arc_synthetic_discovery_task_generator_v1 import (
    ADVERSARIAL_FAMILY_ORDER_V1,
    COMPOSITION_FAMILY_ORDER_V1,
    SINGLE_STEP_FAMILY_ORDER_V1,
    SUPPORTED_FAMILY_ORDER_V1,
    build_arc_synthetic_discovery_task_corpus_v1,
    build_arc_synthetic_discovery_task_v1,
    build_arc_synthetic_solver_packet_v1,
)


def _is_grid(grid: object) -> bool:
    if not isinstance(grid, list) or not grid:
        return False
    width = None
    for row in grid:
        if not isinstance(row, list) or not row:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for cell in row:
            if not isinstance(cell, int) or isinstance(cell, bool):
                return False
    return True


def test_deterministic_generation_and_seed_variation() -> None:
    first = build_arc_synthetic_discovery_task_corpus_v1(seed=2435, tasks_per_family=1, include_adversarial=True, include_compositions=True)
    second = build_arc_synthetic_discovery_task_corpus_v1(seed=2435, tasks_per_family=1, include_adversarial=True, include_compositions=True)
    third = build_arc_synthetic_discovery_task_corpus_v1(seed=2436, tasks_per_family=1, include_adversarial=True, include_compositions=True)
    assert first == second
    assert first != third


def test_required_families_present_and_schema_valid() -> None:
    corpus = build_arc_synthetic_discovery_task_corpus_v1(seed=7, tasks_per_family=1, include_adversarial=True, include_compositions=True)
    labels = {task["family_label"] for task in corpus}
    assert set(SINGLE_STEP_FAMILY_ORDER_V1).issubset(labels)
    assert set(COMPOSITION_FAMILY_ORDER_V1).issubset(labels)
    assert set(ADVERSARIAL_FAMILY_ORDER_V1).issubset(labels)
    assert set(SUPPORTED_FAMILY_ORDER_V1).issubset(labels)
    for task in corpus:
        assert {"task_id", "family_label", "primitive_chain", "train_pairs", "test_input", "expected_output", "difficulty", "variant", "seed", "metadata"} <= set(task)
        assert isinstance(task["task_id"], str)
        assert isinstance(task["family_label"], str)
        assert isinstance(task["primitive_chain"], list)
        assert isinstance(task["train_pairs"], list)
        assert isinstance(task["metadata"], dict)
        assert _is_grid(task["test_input"])
        assert _is_grid(task["expected_output"])
        for pair in task["train_pairs"]:
            assert _is_grid(pair["input"])
            assert _is_grid(pair["output"])
            assert len(pair["input"]) <= 6
            assert len(pair["input"][0]) <= 6
            assert len(pair["output"]) <= 6
            assert len(pair["output"][0]) <= 6


def test_solver_visible_packet_excludes_expected_output() -> None:
    task = build_arc_synthetic_discovery_task_v1("crop_foreground_bbox", seed=11)
    packet = build_arc_synthetic_solver_packet_v1(task)
    assert set(packet) == {"train_pairs", "test_input"}
    assert "expected_output" not in packet
    assert "expected_output" not in packet["train_pairs"][0]


def test_adversarial_tasks_are_labelled_correctly() -> None:
    corpus = build_arc_synthetic_discovery_task_corpus_v1(seed=21, tasks_per_family=1, include_adversarial=True, include_compositions=False)
    adversarial = [task for task in corpus if task["metadata"]["kind"] == "adversarial"]
    assert adversarial
    for task in adversarial:
        assert task["metadata"]["expected_behavior"] == "reject"
        assert task["family_label"] in set(ADVERSARIAL_FAMILY_ORDER_V1)


def test_runner_smoke_tasks_solve_for_supported_families(monkeypatch) -> None:
    smoke_cases = [
        "crop_foreground_bbox",
        "recolor_foreground",
        "rotate_object_90",
        "tile_grid",
        "count_objects_to_line",
    ]
    for family in smoke_cases:
        task = build_arc_synthetic_discovery_task_v1(family, seed=99, variant="smoke")
        result = runner_module.run_universal_family_solver(task["train_pairs"], task["test_input"])
        assert result.exact_two_output is True
        assert result.attempt_1.output == task["expected_output"] or result.attempt_2.output == task["expected_output"]

    composition_task = build_arc_synthetic_discovery_task_v1("crop_then_recolor", seed=99, variant="smoke")
    family_result = FamilyDiscoveryResult(
        accepted_families=(FamilyHypothesis(family_name="crop_then_recolor", primitive_chain=("crop_foreground_bbox", "recolor_global"), status="accepted", confidence=0.95, reason="manual", parameters={}, train_fit=True, rejection_reason=None, source_primitive_hints=("crop_foreground_bbox", "recolor_global"), trace={"manual": True}),),
        rejected_families=(),
        uncertain_families=(),
        family_count=1,
        accepted_count=1,
        rejected_count=0,
        uncertain_count=0,
        trace={"synthetic_only": True},
    )
    monkeypatch.setattr(runner_module, "discover_families_for_task", lambda *args, **kwargs: family_result)
    result = runner_module.run_universal_family_solver(composition_task["train_pairs"], composition_task["test_input"])
    assert result.exact_two_output is True
    assert result.attempt_1.output == composition_task["expected_output"] or result.attempt_2.output == composition_task["expected_output"]


def test_adversarial_ambiguous_multiple_rules_has_non_identity_expected_output() -> None:
    for vi in range(5):
        variant = f"v{vi}"
        task = build_arc_synthetic_discovery_task_v1("ambiguous_multiple_rules", seed=82435, variant=variant)
        assert task["expected_output"] != task["test_input"], (
            f"ambiguous_multiple_rules {variant} has identity expected output"
        )
        assert task["metadata"]["expected_behavior"] == "reject"
        assert task["metadata"]["kind"] == "adversarial"


def test_adversarial_unsupported_primitive_chain_has_non_identity_expected_output() -> None:
    for vi in range(5):
        variant = f"v{vi}"
        task = build_arc_synthetic_discovery_task_v1("unsupported_primitive_chain", seed=82435, variant=variant)
        assert task["expected_output"] != task["test_input"], (
            f"unsupported_primitive_chain {variant} has identity expected output"
        )
        assert task["metadata"]["expected_behavior"] == "reject"
        assert task["metadata"]["kind"] == "adversarial"


def test_adversarial_ambiguous_multiple_rules_not_solved_by_runner() -> None:
    for vi in range(5):
        variant = f"v{vi}"
        task = build_arc_synthetic_discovery_task_v1("ambiguous_multiple_rules", seed=82435, variant=variant)
        result = runner_module.run_universal_family_solver(task["train_pairs"], task["test_input"])
        a1 = getattr(result.attempt_1, "output", None)
        a2 = getattr(result.attempt_2, "output", None)
        assert a1 != task["expected_output"], f"ambiguous_multiple_rules {variant} solved by attempt_1"
        assert a2 != task["expected_output"], f"ambiguous_multiple_rules {variant} solved by attempt_2"


def test_adversarial_unsupported_primitive_chain_not_solved_by_runner() -> None:
    for vi in range(5):
        variant = f"v{vi}"
        task = build_arc_synthetic_discovery_task_v1("unsupported_primitive_chain", seed=82435, variant=variant)
        result = runner_module.run_universal_family_solver(task["train_pairs"], task["test_input"])
        a1 = getattr(result.attempt_1, "output", None)
        a2 = getattr(result.attempt_2, "output", None)
        assert a1 != task["expected_output"], f"unsupported_primitive_chain {variant} solved by attempt_1"
        assert a2 != task["expected_output"], f"unsupported_primitive_chain {variant} solved by attempt_2"


def test_adversarial_repaired_families_remain_deterministic() -> None:
    for family in ("ambiguous_multiple_rules", "unsupported_primitive_chain"):
        t1 = build_arc_synthetic_discovery_task_v1(family, seed=42, variant="v0")
        t2 = build_arc_synthetic_discovery_task_v1(family, seed=42, variant="v0")
        assert t1 == t2, f"{family} not deterministic for seed=42"
        t3 = build_arc_synthetic_discovery_task_v1(family, seed=43, variant="v0")
        assert t3 != t1, f"{family} same for different seeds"
