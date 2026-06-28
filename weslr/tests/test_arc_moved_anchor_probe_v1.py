import sys
sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')
from weslr.arc_moved_anchor_probe import run_moved_anchor_frontier_probe_v1


def test_returns_dict():
    res = run_moved_anchor_frontier_probe_v1()
    assert isinstance(res, dict)


def test_mode_flag():
    res = run_moved_anchor_frontier_probe_v1()
    assert res.get('mode') == 'moved_anchor_probe_v1'


def test_boundary_flags():
    res = run_moved_anchor_frontier_probe_v1()
    assert res.get('synthetic_only') is True
    assert res.get('public_arc_used') is False
    assert res.get('kaggle_used') is False
    assert res.get('benchmark_claim_safe') is False
    assert res.get('solver_behavior_changed') is False
    assert res.get('solver_primitives_added') is False


def test_families_present():
    res = run_moved_anchor_frontier_probe_v1()
    families = {case['family_id'] for case in res['probe_cases']}
    expected = {
        'anchor_translated_target_preserved',
        'anchor_moved_distractor_at_old_coord',
        'anchor_role_preserved_color_changed',
        'anchor_role_preserved_shape_changed',
        'multiple_anchors_one_valid',
        'anchor_moved_near_boundary',
        'anchor_moved_offset_constant',
        'anchor_absent_ambiguous',
    }
    assert expected.issubset(families)
    assert len(families) == 8


def test_tier_mapping_present():
    res = run_moved_anchor_frontier_probe_v1()
    assert set(res['difficulty_tiers_present']) == {0,1,2,3,4,5}


def test_moved_anchor_metrics_present():
    res = run_moved_anchor_frontier_probe_v1()
    for field in [
        'moved_anchor_failure_count', 'moved_anchor_failure_rate',
        'old_anchor_coordinate_bait_count', 'old_anchor_coordinate_bait_rate',
        'anchor_role_preservation_success_count', 'anchor_role_preservation_success_rate',
        'ambiguous_anchor_safe_failure_count', 'ambiguous_anchor_safe_failure_rate',
    ]:
        assert field in res, f"Missing field: {field}"


def test_moved_anchor_metric_formulas():
    res = run_moved_anchor_frontier_probe_v1()
    attempted = res['attempted_task_count']
    # Verify rates are calculated correctly
    assert abs(res['moved_anchor_failure_rate'] - (res['moved_anchor_failure_count'] / attempted)) < 1e-9
    assert abs(res['old_anchor_coordinate_bait_rate'] - (res['old_anchor_coordinate_bait_count'] / attempted)) < 1e-9
    assert abs(res['anchor_role_preservation_success_rate'] - (res['anchor_role_preservation_success_count'] / attempted)) < 1e-9
    assert abs(res['ambiguous_anchor_safe_failure_rate'] - (res['ambiguous_anchor_safe_failure_count'] / attempted)) < 1e-9


def test_frontier_fields_present():
    res = run_moved_anchor_frontier_probe_v1()
    for field in [
        'hardest_exact_tier', 'hardest_partial_tier', 'first_stable_failure_frontier',
        'remaining_partial_families', 'remaining_blocker_families', 'remaining_unsupported_families',
        'first_stable_moved_anchor_frontier', 'hardest_moved_anchor_tier',
    ]:
        assert field in res


def test_relation_first_metadata_present():
    res = run_moved_anchor_frontier_probe_v1()
    assert 'coordinate_form_example' in res
    assert 'relational_form_example' in res
    assert 'relation_first_poc_candidate' in res
    assert 'rewrite_outcome_options' in res
    assert isinstance(res['rewrite_outcome_options'], list)


def test_baseline_reference_separate():
    res = run_moved_anchor_frontier_probe_v1()
    baseline = res['baseline_reference']
    assert baseline['task_exact_rate'] == 0.8611111111111112
    assert baseline['generated_level_count'] == 12


def test_coordinate_reference_present_flag():
    res = run_moved_anchor_frontier_probe_v1()
    assert res.get('coordinate_probe_reference_present') is True


def test_existing_coordinate_overfit_tests_pass():
    from weslr.arc_coordinate_overfit_probe import run_coordinate_overfit_trap_frontier_probe_v1
    res = run_coordinate_overfit_trap_frontier_probe_v1()
    assert res['mode'] == 'coordinate_overfit_probe_v1'


def test_existing_difficulty_probe_tests_pass():
    from weslr.arc_unknown_engine_level_ladder_difficulty_probe import run_arc_unknown_engine_level_ladder_difficulty_probe_v1
    res = run_arc_unknown_engine_level_ladder_difficulty_probe_v1()
    assert res['mode'] == 'difficulty_probe_v1'


def test_existing_smoke_metrics_tests_pass():
    from weslr.tests.test_arc_unknown_engine_level_ladder_smoke_metrics_v1 import (
        test_smoke_output_contains_required_metric_fields,
        test_smoke_output_contains_frontier_placeholder_fields,
        test_current_run_formulae_use_correct_denominators,
        test_threshold_basis_positive_fixture_uses_task_rate_not_packet_rate,
        test_threshold_basis_negative_fixture_blocks_packet_pass_task_fail_case,
        test_packet_pass_task_fail_fixture_cannot_unlock_hardening,
        test_boundary_flags_consistency,
        test_current_run_sanity_and_threshold_policy_surface,
    )
    test_smoke_output_contains_required_metric_fields()
    test_smoke_output_contains_frontier_placeholder_fields()
    test_current_run_formulae_use_correct_denominators()
    test_threshold_basis_positive_fixture_uses_task_rate_not_packet_rate()
    test_threshold_basis_negative_fixture_blocks_packet_pass_task_fail_case()
    test_packet_pass_task_fail_fixture_cannot_unlock_hardening()
    test_boundary_flags_consistency()
    test_current_run_sanity_and_threshold_policy_surface()


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__]))