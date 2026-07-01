"""Tests for the Broad‑Hard‑80 generator."""

import copy
import pytest
from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks

ALLOWED_PRIMITIVES = {
    "extract", "extract_largest_object", "isolate_largest", "extract_boundary",
    "crop", "mirror_object", "rotate", "recolor", "normalize_position",
    "place_back", "count_objects", "pattern_output", "transform",
}

ALLOWED_ALIASES = {
    "remove_noise", "extract_object", "crop_object", "recolor_boundary",
    "count", "count_or_pattern", "extract_changed_region", "fill_region",
}

ALL_ALLOWED = ALLOWED_PRIMITIVES | ALLOWED_ALIASES


@pytest.fixture(scope="module")
def tasks():
    return generate_broad_hard_80_tasks()


def _axes_for_difficulty(difficulty):
    if difficulty == "medium":
        return range(2, 4)
    if difficulty == "hard":
        return range(4, 7)
    if difficulty == "adversarial":
        return range(7, 11)
    return range(0, 0)


class TestBroadHard80Structure:
    def test_exactly_80_tasks(self, tasks):
        assert len(tasks) == 80

    def test_ids_bh80_001_to_080(self, tasks):
        ids = [t["task_id"] for t in tasks]
        expected = {f"BH80_{i:03d}" for i in range(1, 81)}
        assert set(ids) == expected
        assert len(ids) == len(set(ids))  # no duplicates

    def test_ids_in_order(self, tasks):
        ids = [t["task_id"] for t in tasks]
        assert ids == sorted(ids)

    def test_every_task_has_3_primitives(self, tasks):
        for t in tasks:
            assert len(t["primitive_sequence"]) == 3, f"{t['task_id']} has {len(t['primitive_sequence'])} primitives"

    def test_all_primitives_allowed(self, tasks):
        for t in tasks:
            for p in t["primitive_sequence"]:
                assert p in ALL_ALLOWED, f"{t['task_id']} uses disallowed primitive: {p}"


class TestBroadHard80Allocation:
    def test_known_family_anchors(self, tasks):
        known = [t for t in tasks if t["family_id"].startswith("F00")]
        assert 15 <= len(known) <= 20

    def test_hybrid_tasks(self, tasks):
        hybrid = [t for t in tasks if t["family_id"] in ("BH‑A", "BH‑B")]
        assert len(hybrid) == 20

    def test_mutation_tasks(self, tasks):
        mutation = [t for t in tasks if t["family_id"] in ("BH‑C", "BH‑D")]
        assert len(mutation) == 20

    def test_unknown_family_candidates(self, tasks):
        unknown = [t for t in tasks if t["family_id"] in ("BH‑E", "BH‑F", "BH‑G")]
        assert 20 <= len(unknown) <= 25


class TestBroadHard80Difficulty:
    def test_difficulty_distribution(self, tasks):
        from collections import Counter
        dc = Counter(t["difficulty"] for t in tasks)
        assert dc.get("easy", 0) == 0
        assert dc.get("medium", 0) == 16
        assert dc.get("hard", 0) == 48
        assert dc.get("adversarial", 0) == 16

    def test_hardness_axes_match_difficulty(self, tasks):
        for t in tasks:
            n = len(t["hardness_axes"])
            diff = t["difficulty"]
            assert n in _axes_for_difficulty(diff), (
                f"{t['task_id']}: {diff} with {n} axes"
            )

    def test_adversarial_has_axis_6(self, tasks):
        for t in tasks:
            if t["difficulty"] == "adversarial":
                assert 6 in t["hardness_axes"], f"{t['task_id']} adversarial missing axis 6"


class TestBroadHard80Families:
    def test_15_family_ids(self, tasks):
        families = {t["family_id"] for t in tasks}
        assert len(families) == 15

    def test_family_ids_are_expected(self, tasks):
        families = {t["family_id"] for t in tasks}
        expected = {f"F00{i}" for i in range(1, 9)} | {"BH‑A", "BH‑B", "BH‑C", "BH‑D", "BH‑E", "BH‑F", "BH‑G"}
        assert families == expected


class TestBroadHard80Content:
    def test_every_task_has_hardness_axes(self, tasks):
        for t in tasks:
            assert "hardness_axes" in t
            assert isinstance(t["hardness_axes"], list)
            assert len(t["hardness_axes"]) >= 2

    def test_every_task_has_shortcut_defeated(self, tasks):
        for t in tasks:
            assert "shortcut_defeated" in t
            assert len(t["shortcut_defeated"]) > 3

    def test_every_task_has_scene_spec(self, tasks):
        for t in tasks:
            assert "scene_spec" in t
            assert "grid_size" in t["scene_spec"]
            assert "initial_objects" in t["scene_spec"]

    def test_leakage_flags_all_false(self, tasks):
        for t in tasks:
            for flag, val in t["leakage_flags"].items():
                assert val is False, f"{t['task_id']} leakage flag {flag} = {val}"

    def test_no_expected_output_leakage(self, tasks):
        for t in tasks:
            assert "expected_test_output" in t["forbidden_shortcuts"]
            assert "expected_test_output" not in t.get("scene_spec", {})


class TestBroadHard80Determinism:
    def test_deterministic_output(self, tasks):
        tasks2 = generate_broad_hard_80_tasks()
        # Deep compare
        assert copy.deepcopy(tasks) == copy.deepcopy(tasks2)

    def test_output_stable_across_calls(self):
        t1 = generate_broad_hard_80_tasks()
        t2 = generate_broad_hard_80_tasks()
        t3 = generate_broad_hard_80_tasks()
        ids1 = [t["task_id"] for t in t1]
        ids2 = [t["task_id"] for t in t2]
        ids3 = [t["task_id"] for t in t3]
        assert ids1 == ids2 == ids3