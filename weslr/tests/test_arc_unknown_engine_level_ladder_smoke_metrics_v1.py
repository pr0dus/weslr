import sys
import json

sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean')

from weslr.arc_style_synthetic_solver_suite import run_arc_style_synthetic_solver_suite_v1

def test_packet_exact_rate_computed_correctly():
    res = run_arc_style_synthetic_solver_suite_v1()
    top2 = res.get('top2_packet_count')
    exact = res.get('synthetic_exact_count')
    expected = exact / top2 if top2 else 0.0
    assert abs(res.get('packet_exact_rate') - expected) < 1e-9

def test_task_exact_rate_and_threshold():
    res = run_arc_style_synthetic_solver_suite_v1()
    attempted = res.get('attempted_task_count')
    exact_tasks = res.get('task_exact_count')
    expected_rate = exact_tasks / attempted if attempted else 0.0
    assert abs(res.get('task_exact_rate') - expected_rate) < 1e-9
    internal_pass = expected_rate >= 0.85
    assert res.get('internal_pass_85') == internal_pass
    assert res.get('level_hardening_allowed') == internal_pass

def test_boundary_flags_consistency():
    res = run_arc_style_synthetic_solver_suite_v1()
    assert res.get('synthetic_only') is True
    assert res.get('public_arc_used') is False
    assert res.get('kaggle_used') is False
    assert res.get('benchmark_claim_safe') is False
