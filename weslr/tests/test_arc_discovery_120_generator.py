"""Tests for ARC Synthetic Discovery 120 Generator.

Validates:
- Exactly 120 tasks generated
- 80 frozen BH80 tasks preserved
- 40 new tasks generated
- 110 scored / 10 candidate-probe
- All tasks have exactly 3 primitives
- color_invert tasks are scored
- Candidate probes are unscored
- Unpromoted candidates cannot be counted as solved
- No default [[1]] scenes
- Scene specs materialize successfully
- Gate thresholds correct
- BH80 unchanged
"""

from __future__ import annotations

import pytest

from weslr.arc_discovery_120_generator import (
    generate_discovery_120_tasks,
    get_scored_tasks,
    get_candidate_probe_tasks,
    get_scoring_summary,
    get_gate_definitions,
    check_no_default_ones,
    check_candidate_probe_separation,
    check_unpromoted_blocked,
    check_all_three_steps,
    anti_cheat_readiness,
    SCORED,
    CANDIDATE_PROBE,
    GATE_DEFINITIONS,
)
from weslr.arc_bh80_materializer import materialize_scene
from weslr.arc_synthetic_3_step_task_schema import generate_broad_hard_80_tasks


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def tasks120():
    return generate_discovery_120_tasks()


@pytest.fixture(scope="module")
def bh80_tasks():
    return generate_broad_hard_80_tasks()


# ---------------------------------------------------------------------------
# TestTotalCounts
# ---------------------------------------------------------------------------

class TestTotalCounts:
    def test_exactly_120_tasks(self, tasks120):
        assert len(tasks120) == 120

    def test_80_bh80_tasks(self, tasks120):
        bh80 = [t for t in tasks120 if t["task_id"].startswith("BH80_")]
        assert len(bh80) == 80

    def test_40_new_tasks(self, tasks120):
        new = [t for t in tasks120 if t["task_id"].startswith("T120_")]
        assert len(new) == 40

    def test_task_ids_sequential(self, tasks120):
        new_ids = [t["task_id"] for t in tasks120 if t["task_id"].startswith("T120_")]
        expected = [f"T120_{i:03d}" for i in range(81, 121)]
        assert new_ids == expected


# ---------------------------------------------------------------------------
# TestScoringLayers
# ---------------------------------------------------------------------------

class TestScoringLayers:
    def test_110_scored(self, tasks120):
        scored = get_scored_tasks(tasks120)
        assert len(scored) == 114

    def test_10_candidate_probes(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        assert len(probes) == 6

    def test_bh80_all_scored(self, tasks120):
        bh80 = [t for t in tasks120 if t["task_id"].startswith("BH80_")]
        for t in bh80:
            assert t["scoring_layer"] == SCORED

    def test_candidate_probes_are_remaining_unpromoted(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        probe_ids = [t["task_id"] for t in probes]
        expected = ["T120_101", "T120_102", "T120_105", "T120_107", "T120_108", "T120_109"]
        assert probe_ids == expected

    def test_scoring_summary(self, tasks120):
        summary = get_scoring_summary(tasks120)
        assert summary["total_tasks"] == 120
        assert summary["scored_total"] == 114
        assert summary["candidate_probe_total"] == 6
        assert summary["bh80_count"] == 80
        assert summary["new_task_count"] == 40


# ---------------------------------------------------------------------------
# TestThreeStepSequences
# ---------------------------------------------------------------------------

class TestThreeStepSequences:
    def test_all_tasks_3_primitives(self, tasks120):
        assert check_all_three_steps(tasks120)

    def test_bh80_sequences_unchanged(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["primitive_sequence"] == bh80_tasks[i]["primitive_sequence"]


# ---------------------------------------------------------------------------
# TestColorInvertTasks
# ---------------------------------------------------------------------------

class TestColorInvertTasks:
    def test_color_invert_tasks_scored(self, tasks120):
        ci_tasks = [t for t in tasks120 if "color_invert" in t["primitive_sequence"]]
        assert len(ci_tasks) == 12  # 10 promoted-native + T120_114 + T120_119
        for t in ci_tasks:
            assert t["scoring_layer"] == SCORED, f"{t['task_id']} should be scored"

    def test_color_invert_in_t120_081_to_090(self, tasks120):
        for i in range(81, 91):
            tid = f"T120_{i:03d}"
            t = next(task for task in tasks120 if task["task_id"] == tid)
            assert "color_invert" in t["primitive_sequence"], f"{tid} should use color_invert"
            assert t["scoring_layer"] == SCORED

    def test_color_invert_has_promoted_metadata(self, tasks120):
        for t in tasks120:
            if "color_invert" in t["primitive_sequence"] and t["task_id"].startswith("T120_08"):
                meta = t.get("promoted_primitive", {})
                assert meta.get("primitive_id") == "color_invert"
                assert meta.get("promoted") is True


# ---------------------------------------------------------------------------
# TestCandidateProbes
# ---------------------------------------------------------------------------

class TestCandidateProbes:
    def test_probes_unscored(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        for t in probes:
            assert t["scoring_layer"] == CANDIDATE_PROBE

    def test_probes_have_candidate_metadata(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        for t in probes:
            meta = t.get("candidate_probe", {})
            assert meta.get("candidate_probe") is True
            assert meta.get("unpromoted") is True
            assert meta.get("can_be_counted_as_solved") is False

    def test_probes_have_candidate_primitive_id(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        for t in probes:
            meta = t.get("candidate_probe", {})
            assert "candidate_primitive_id" in meta
            assert meta["candidate_primitive_id"]  # non-empty

    def test_probes_have_promotion_stage_generated(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        for t in probes:
            meta = t.get("candidate_probe", {})
            assert meta.get("promotion_stage") == "GENERATED"

    def test_probe_ids_are_remaining_unpromoted(self, tasks120):
        probes = get_candidate_probe_tasks(tasks120)
        ids = [t["task_id"] for t in probes]
        expected = ["T120_101", "T120_102", "T120_105", "T120_107", "T120_108", "T120_109"]
        assert ids == expected


# ---------------------------------------------------------------------------
# TestUnpromotedBlocking
# ---------------------------------------------------------------------------

class TestUnpromotedBlocking:
    def test_no_scored_task_has_unpromoted_primitive(self, tasks120):
        assert check_unpromoted_blocked(tasks120)

    def test_candidate_probe_tasks_contain_unpromoted(self, tasks120):
        # At least one primitive in each probe task should not be in the promoted set
        from weslr.arc_discovery_120_generator import _can_primitive_be_counted
        probes = get_candidate_probe_tasks(tasks120)
        for t in probes:
            has_unpromoted = any(
                not _can_primitive_be_counted(p)
                for p in t["primitive_sequence"]
            )
            assert has_unpromoted, f"{t['task_id']} should contain at least one unpromoted primitive"


# ---------------------------------------------------------------------------
# TestSceneSpecs
# ---------------------------------------------------------------------------

class TestSceneSpecs:
    def test_no_default_ones(self, tasks120):
        assert check_no_default_ones(tasks120)

    def test_all_new_tasks_have_scene_spec(self, tasks120):
        new = [t for t in tasks120 if t["task_id"].startswith("T120_")]
        for t in new:
            assert t.get("scene_spec") is not None
            assert isinstance(t["scene_spec"], dict)
            assert "grid_size" in t["scene_spec"]
            assert "initial_objects" in t["scene_spec"]

    def test_scene_specs_materialize(self, tasks120):
        new = [t for t in tasks120 if t["task_id"].startswith("T120_")]
        for t in new:
            grid = materialize_scene(t["scene_spec"], t["task_id"])
            assert isinstance(grid, list)
            assert len(grid) > 0
            assert all(isinstance(row, list) for row in grid)
            assert all(isinstance(v, int) for row in grid for v in row)

    def test_varied_grid_sizes(self, tasks120):
        new = [t for t in tasks120 if t["task_id"].startswith("T120_")]
        sizes = set()
        for t in new:
            gs = t["scene_spec"]["grid_size"]
            sizes.add((gs[0], gs[1]))
        assert len(sizes) >= 3, f"Only {len(sizes)} distinct grid sizes, expected ≥ 3"

    def test_color_diversity_in_color_invert_tasks(self, tasks120):
        ci_tasks = [t for t in tasks120 if "color_invert" in t["primitive_sequence"]]
        colors = set()
        for t in ci_tasks:
            for obj in t["scene_spec"].get("initial_objects", []):
                colors.add(obj["attributes"]["color"])
            for d in t["scene_spec"].get("distractors", []):
                colors.add(d["attributes"]["color"])
        assert len(colors) >= 4, f"Only {len(colors)} distinct colors in color_invert tasks, expected ≥ 4"


# ---------------------------------------------------------------------------
# TestGateDefinitions
# ---------------------------------------------------------------------------

class TestGateDefinitions:
    def test_gate_definitions_exist(self):
        gates = get_gate_definitions()
        assert "scored" in gates
        assert "bh80_subgate" in gates
        assert "future_all_120" in gates

    def test_scored_gates(self):
        gates = get_gate_definitions()
        scored = gates["scored"]
        assert scored["clean"] == 114
        assert scored["preferred"] == 107
        assert scored["strong"] == 103
        assert scored["minimal"] == 97
        assert scored["total"] == 114

    def test_bh80_subgate(self):
        gates = get_gate_definitions()
        bh80 = gates["bh80_subgate"]
        assert bh80["clean"] == 80
        assert bh80["preferred"] == 75
        assert bh80["strong"] == 72
        assert bh80["minimal"] == 68
        assert bh80["total"] == 80

    def test_future_all_120_gates(self):
        gates = get_gate_definitions()
        future = gates["future_all_120"]
        assert future["clean"] == 120
        assert future["preferred"] == 112
        assert future["strong"] == 108
        assert future["minimal"] == 102
        assert future["total"] == 120


# ---------------------------------------------------------------------------
# TestBH80Preservation
# ---------------------------------------------------------------------------

class TestBH80Preservation:
    def test_bh80_task_ids_preserved(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["task_id"] == bh80_tasks[i]["task_id"]

    def test_bh80_family_ids_preserved(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["family_id"] == bh80_tasks[i]["family_id"]

    def test_bh80_primitive_sequences_preserved(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["primitive_sequence"] == bh80_tasks[i]["primitive_sequence"]

    def test_bh80_difficulty_preserved(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["difficulty"] == bh80_tasks[i]["difficulty"]

    def test_bh80_scene_specs_preserved(self, tasks120, bh80_tasks):
        for i in range(80):
            assert tasks120[i]["scene_spec"] == bh80_tasks[i]["scene_spec"]


# ---------------------------------------------------------------------------
# TestAntiCheatReadiness
# ---------------------------------------------------------------------------

class TestAntiCheatReadiness:
    def test_no_default_ones(self, tasks120):
        assert check_no_default_ones(tasks120)

    def test_candidate_probe_separation(self, tasks120):
        assert check_candidate_probe_separation(tasks120)

    def test_unpromoted_blocked(self, tasks120):
        assert check_unpromoted_blocked(tasks120)

    def test_all_three_steps(self, tasks120):
        assert check_all_three_steps(tasks120)

    def test_scene_spec_read_audit(self, tasks120):
        checks = anti_cheat_readiness(tasks120)
        assert checks["scene_spec_read_audit"] is True

    def test_full_readiness(self, tasks120):
        checks = anti_cheat_readiness(tasks120)
        for check_name, result in checks.items():
            assert result is True, f"Anti-cheat check '{check_name}' failed"


# ---------------------------------------------------------------------------
# TestGroupDistribution
# ---------------------------------------------------------------------------

class TestGroupDistribution:
    def test_promoted_native_group_count(self, tasks120):
        pn = [t for t in tasks120 if t.get("family_id") == "promoted_native"]
        assert len(pn) == 10

    def test_old_primitive_harder_group_count(self, tasks120):
        oph = [t for t in tasks120 if t.get("family_id") == "old_primitive_harder"]
        assert len(oph) == 10

    def test_candidate_probe_group_count(self, tasks120):
        cp = [t for t in tasks120 if t.get("family_id") == "candidate_probe"]
        assert len(cp) == 10

    def test_adversarial_control_group_count(self, tasks120):
        ac = [t for t in tasks120 if t.get("family_id") == "adversarial_control"]
        assert len(ac) == 10