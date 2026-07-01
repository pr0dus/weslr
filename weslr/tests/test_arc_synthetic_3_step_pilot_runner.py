import pytest
from weslr.arc_synthetic_3_step_pilot_runner import run_3_step_pilot_diagnostic


def test_runner_consumes_20_tasks():
    report = run_3_step_pilot_diagnostic()
    assert len(report["task_reports"]) == 20, "Runner must produce 20 task reports"
    assert report["overall_metrics"]["represented_candidates"] == 8, "All 8 families should be represented"


def test_overall_metrics_counts():
    report = run_3_step_pilot_diagnostic()
    overall = report["overall_metrics"]
    # The static generator includes failure categories for every task, so all are "failed"
    assert overall["failed"] == 20
    assert overall["exact"] == 0
    assert overall["partial"] == 0
    assert overall["unsupported"] == 0


def test_leakage_flags_all_false():
    report = run_3_step_pilot_diagnostic()
    for tr in report["task_reports"]:
        for flag, val in tr["leakage_flags"].items():
            assert val is False, f"Leakage flag {flag} must be False"


def test_trace_summaries_structure():
    report = run_3_step_pilot_diagnostic()
    for tr in report["task_reports"]:
        ts = tr["trace_summaries"]
        assert set(ts.keys()) == {"step_1", "step_2", "step_3"}
        for v in ts.values():
            assert isinstance(v, str)

# End of test file
