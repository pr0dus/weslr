import sys

sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')

from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1
from weslr.arc_unknown_engine_level_ladder_difficulty_probe import (
    run_arc_unknown_engine_level_ladder_difficulty_probe_v1,
)


EXPECTED_FRONTIER_FIELDS = {
    'hardest_exact_tier',
    'hardest_partial_tier',
    'first_stable_failure_frontier',
    'remaining_partial_families',
    'remaining_blocker_families',
    'remaining_unsupported_families',
    'next_recommended_pressure_family',
}


def _run_probe():
    return run_arc_unknown_engine_level_ladder_difficulty_probe_v1()


def test_probe_mode_is_separate_and_baseline_is_preserved():
    baseline_before = run_arc_style_synthetic_solver_suite_v1()
    probe = _run_probe()
    baseline_after = run_arc_style_synthetic_solver_suite_v1()

    assert probe.get('mode') == 'difficulty_probe_v1'
    assert probe.get('baseline_mode_unchanged') is True
    assert probe.get('generator_behavior_changed_for_baseline') is False
    assert probe.get('baseline_reference', {}).get('generated_level_count') == 12
    assert probe.get('baseline_reference', {}).get('task_exact_rate') == 0.8611111111111112
    assert baseline_before.get('task_exact_rate') == baseline_after.get('task_exact_rate') == 0.8611111111111112
    assert baseline_before.get('generated_level_count') == baseline_after.get('generated_level_count') == 12


def test_probe_boundary_and_solver_freeze_flags_are_fail_closed():
    probe = _run_probe()
    assert probe.get('synthetic_only') is True
    assert probe.get('public_arc_used') is False
    assert probe.get('kaggle_used') is False
    assert probe.get('benchmark_claim_safe') is False
    assert probe.get('solver_behavior_changed') is False
    assert probe.get('solver_primitives_added') is False


def test_difficulty_tiers_and_axes_are_present():
    probe = _run_probe()
    assert probe.get('difficulty_tiers_present') == [0, 1, 2, 3, 4, 5]
    axes = probe.get('difficulty_axes_present')
    assert isinstance(axes, list)
    assert len(axes) == 15
    assert 'multi_step_transformation' in axes
    assert 'ambiguous_rival_grammar' in axes
    assert len(probe.get('executable_axes', [])) >= 1
    assert len(probe.get('placeholder_axes', [])) >= 1


def test_task_metrics_are_primary_and_packet_metrics_are_diagnostic():
    probe = _run_probe()
    assert probe.get('threshold_basis') == 'task_exact_rate'
    assert probe.get('task_exact_count') == 4
    assert probe.get('attempted_task_count') == 8
    assert probe.get('task_exact_rate') == 0.5
    assert probe.get('internal_pass_85') is False
    assert probe.get('level_hardening_allowed') is False
    assert probe.get('packet_exact_count') == 9
    assert probe.get('packet_exact_rate') == 0.5625
    assert probe.get('difficulty_interpretation') == 'meaningful_stress_exposure_with_frontier_signal'


def test_frontier_fields_and_harder_cases_are_present():
    probe = _run_probe()
    missing = EXPECTED_FRONTIER_FIELDS - set(probe.keys())
    assert not missing
    assert probe.get('hardest_exact_tier') == 3
    assert probe.get('hardest_partial_tier') == 3
    frontier = probe.get('first_stable_failure_frontier')
    assert isinstance(frontier, dict)
    assert frontier.get('tier_index') == 3
    assert probe.get('next_recommended_pressure_family') == 'coordinate_overfit_trap'
    assert any(case.get('tier_index', 0) >= 2 for case in probe.get('probe_cases', []))


def test_existing_baseline_smoke_surface_still_passes_current_expectations():
    baseline = run_arc_style_synthetic_solver_suite_v1()
    assert baseline.get('generated_level_count') == 12
    assert baseline.get('task_exact_rate') == 0.8611111111111112
    assert baseline.get('packet_exact_rate') == 0.8541666666666666
    assert baseline.get('threshold_basis') == 'task_exact_rate'
