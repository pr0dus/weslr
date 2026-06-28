import sys
import json
sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')
from weslr.arc_coordinate_overfit_probe import run_coordinate_overfit_trap_frontier_probe_v1


def test_returns_pure_dict():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    assert isinstance(res, dict)


def test_mode_flag():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    assert res.get('mode') == 'coordinate_overfit_probe_v1'


def test_boundary_flags():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    assert res.get('synthetic_only') is True
    assert res.get('public_arc_used') is False
    assert res.get('kaggle_used') is False
    assert res.get('benchmark_claim_safe') is False
    assert res.get('solver_behavior_changed') is False
    assert res.get('solver_primitives_added') is False


def test_families_and_tiers_present():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    families = {case['family_id'] for case in res['probe_cases']}
    expected = {'shifted_same_relation', 'moved_anchor', 'translated_pair',
                'same_shape_diff_coord', 'coordinate_bait_distractor', 'relative_adjacency_preserve'}
    assert expected.issubset(families)
    assert set(res['difficulty_tiers_present']) == {0,1,2,3,4,5}


def test_coordinate_metrics_present_and_correct():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    attempted = res['attempted_task_count']
    # Suspected count should be sum of families marked as such
    suspected = sum(1 for c in res['probe_cases'] if c['coordinate_overfit_suspected'])
    assert res['coordinate_overfit_suspected_count'] == suspected
    assert abs(res['coordinate_overfit_suspected_rate'] - (suspected/attempted)) < 1e-9
    bait = sum(1 for c in res['probe_cases'] if c['coordinate_bait_failure'])
    assert res['coordinate_bait_failure_count'] == bait
    assert abs(res['coordinate_bait_failure_rate'] - (bait/attempted)) < 1e-9
    rel = sum(1 for c in res['probe_cases'] if c['relation_preservation_success'])
    assert res['relation_preservation_success_count'] == rel
    assert abs(res['relation_preservation_success_rate'] - (rel/attempted)) < 1e-9


def test_frontier_fields_present():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    for field in ['hardest_exact_tier', 'hardest_partial_tier', 'first_stable_failure_frontier',
                  'remaining_partial_families', 'remaining_blocker_families', 'remaining_unsupported_families',
                  'next_recommended_pressure_family']:
        assert field in res


def test_baseline_reference_separate():
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    baseline = res['baseline_reference']
    # baseline task exact rate must match the original smoke V2 baseline (0.861111...)
    assert baseline['task_exact_rate'] == 0.8611111111111112
    # Changing the probe must not affect baseline values
    assert baseline['generated_level_count'] == 12


def test_existing_difficulty_probe_still_passes():
    from weslr.arc_unknown_engine_level_ladder_difficulty_probe import run_arc_unknown_engine_level_ladder_difficulty_probe_v1
    res = run_arc_unknown_engine_level_ladder_difficulty_probe_v1()
    assert res['mode'] == 'difficulty_probe_v1'


def test_existing_smoke_metrics_still_pass():
    from weslr.tests.test_arc_unknown_engine_level_ladder_smoke_metrics_v1 import (
        test_smoke_output_contains_required_metric_fields,
        test_smoke_output_contains_frontier_placeholder_fields,
        test_current_run_formulae_use_correct_denominators,
        test_threshold_basis_positive_fixture,
        test_threshold_basis_negative_fixture,
        test_packet_pass_task_fail_fixture,
        test_boundary_flags_consistency,
        test_current_run_sanity_and_threshold_policy_surface,
    )
    # Run the imported test functions directly; they assert internally.
    test_smoke_output_contains_required_metric_fields()
    test_smoke_output_contains_frontier_placeholder_fields()
    test_current_run_formulae_use_correct_denominators()
    test_threshold_basis_positive_fixture()
    test_threshold_basis_negative_fixture()
    test_packet_pass_task_fail_fixture()
    test_boundary_flags_consistency()
    test_current_run_sanity_and_threshold_policy_surface()

if __name__ == '__main__':
    # Run all tests when executed directly
    import pytest
    sys.exit(pytest.main([__file__]))
