import sys

sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')

from weslr.arc_style_synthetic_solver_suite import (
    compute_arc_unknown_engine_smoke_metrics_policy_v1,
    run_arc_style_synthetic_solver_suite_v1,
)


EXPECTED_METRIC_FIELDS = {
    'generated_level_count',
    'attempted_task_count',
    'task_exact_count',
    'task_partial_count',
    'task_unsupported_count',
    'task_failed_count',
    'task_exact_rate',
    'task_partial_rate',
    'task_unsupported_rate',
    'top2_packet_count',
    'packet_exact_rate',
    'packet_partial_rate',
    'packet_unsupported_rate',
    'internal_threshold',
    'threshold_basis',
    'internal_pass_85',
    'level_hardening_allowed',
    'level_hardening_reason',
    'synthetic_only',
    'public_arc_used',
    'kaggle_used',
    'benchmark_claim_safe',
}

EXPECTED_FRONTIER_FIELDS = {
    'hardest_exact_tier',
    'hardest_partial_tier',
    'first_stable_failure_frontier',
    'remaining_partial_families',
    'remaining_blocker_families',
    'remaining_unsupported_families',
    'next_recommended_pressure_family',
}


def _run():
    return run_arc_style_synthetic_solver_suite_v1()


def test_smoke_output_contains_required_metric_fields():
    res = _run()
    missing = EXPECTED_METRIC_FIELDS - set(res.keys())
    assert not missing


def test_smoke_output_contains_frontier_placeholder_fields():
    res = _run()
    missing = EXPECTED_FRONTIER_FIELDS - set(res.keys())
    assert not missing


def test_current_run_formulae_use_correct_denominators():
    res = _run()
    attempted = res.get('attempted_task_count')
    top2 = res.get('top2_packet_count')
    assert attempted > 0
    assert top2 > 0
    assert abs(res.get('task_exact_rate') - (res.get('task_exact_count') / attempted)) < 1e-9
    assert abs(res.get('task_partial_rate') - (res.get('task_partial_count') / attempted)) < 1e-9
    assert abs(res.get('task_unsupported_rate') - (res.get('task_unsupported_count') / attempted)) < 1e-9
    assert abs(res.get('packet_exact_rate') - (res.get('synthetic_exact_count') / top2)) < 1e-9
    assert abs(res.get('packet_partial_rate') - (res.get('synthetic_partial_count') / top2)) < 1e-9
    assert abs(res.get('packet_unsupported_rate') - (res.get('synthetic_unsupported_count') / top2)) < 1e-9


def test_threshold_basis_positive_fixture_uses_task_rate_not_packet_rate():
    fixture = compute_arc_unknown_engine_smoke_metrics_policy_v1(
        generated_level_count=12,
        attempted_task_count=20,
        task_exact_count=17,
        task_partial_count=1,
        task_unsupported_count=2,
        task_failed_count=0,
        top2_packet_count=40,
        synthetic_exact_count=30,
        synthetic_partial_count=4,
        synthetic_unsupported_count=6,
    )
    assert fixture.get('task_exact_rate') >= 0.85
    assert fixture.get('packet_exact_rate') < 0.85
    assert fixture.get('internal_pass_85') is True
    assert fixture.get('level_hardening_allowed') is True
    assert fixture.get('level_hardening_reason') == 'task_exact_rate_meets_internal_threshold'


def test_threshold_basis_negative_fixture_blocks_packet_pass_task_fail_case():
    fixture = compute_arc_unknown_engine_smoke_metrics_policy_v1(
        generated_level_count=12,
        attempted_task_count=20,
        task_exact_count=16,
        task_partial_count=2,
        task_unsupported_count=2,
        task_failed_count=0,
        top2_packet_count=20,
        synthetic_exact_count=18,
        synthetic_partial_count=1,
        synthetic_unsupported_count=1,
    )
    assert fixture.get('packet_exact_rate') >= 0.85
    assert fixture.get('task_exact_rate') < 0.85
    assert fixture.get('internal_pass_85') is False
    assert fixture.get('level_hardening_allowed') is False
    assert fixture.get('level_hardening_reason') == 'task_exact_rate_below_internal_threshold'


def test_packet_pass_task_fail_fixture_cannot_unlock_hardening():
    fixture = compute_arc_unknown_engine_smoke_metrics_policy_v1(
        generated_level_count=8,
        attempted_task_count=10,
        task_exact_count=8,
        task_partial_count=1,
        task_unsupported_count=1,
        task_failed_count=0,
        top2_packet_count=10,
        synthetic_exact_count=9,
        synthetic_partial_count=1,
        synthetic_unsupported_count=0,
    )
    assert fixture.get('packet_exact_rate') >= 0.85
    assert fixture.get('task_exact_rate') < 0.85
    assert fixture.get('level_hardening_allowed') is False
    assert fixture.get('internal_pass_85') is False


def test_boundary_flags_consistency():
    res = _run()
    assert res.get('synthetic_only') is True
    assert res.get('public_arc_used') is False
    assert res.get('kaggle_used') is False
    assert res.get('benchmark_claim_safe') is False


def test_current_run_sanity_and_threshold_policy_surface():
    res = _run()
    assert res.get('generated_level_count') == 12
    assert res.get('threshold_basis') == 'task_exact_rate'
    assert res.get('internal_threshold') == 0.85
    assert res.get('attempted_task_count') > 0
    assert res.get('top2_packet_count') >= res.get('attempted_task_count')
    assert res.get('public_arc_used') is False
    assert res.get('kaggle_used') is False
    assert res.get('synthetic_only') is True
    assert 'public' not in (res.get('level_hardening_reason') or '')
