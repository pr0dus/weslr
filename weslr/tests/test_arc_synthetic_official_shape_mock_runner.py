from __future__ import annotations

from weslr.arc_synthetic_official_shape_mock_runner import (
    run_arc_synthetic_official_shape_mock_readiness_v1,
    summarize_arc_synthetic_official_shape_mock_readiness_v1,
)


def test_mock_readiness_run_beats_trivial_baseline_and_stays_clean() -> None:
    result = run_arc_synthetic_official_shape_mock_readiness_v1()
    summary = summarize_arc_synthetic_official_shape_mock_readiness_v1(result)
    assert result["synthetic_only"] is True
    assert result["official_data_touched"] is False
    assert result["public_data_touched"] is False
    assert result["network_touched"] is False
    assert result["bundle_validation"]["valid"] is True
    assert result["readiness_signal"] is True
    assert result["readiness_verdict"] == "mock_ready_for_public_parse_scorer_design"
    assert summary["valid"] is True
    assert summary["solver_exact_count"] > summary["baseline_exact_count"]
    assert summary["malformed_count"] == 0
    assert summary["timeout_count"] == 0
    assert summary["error_count"] == 0
    assert summary["batch_count"] == 3
    assert summary["task_count"] == 24
    assert summary["batch_score_variance"] >= 0.0
    assert result["audit"]["expected_output_leakage"] is False
    assert result["audit"]["internet_used"] is False
    assert result["audit"]["provider_used"] is False
    assert result["audit"]["retrieval_used"] is False
    assert result["audit"]["tool_calls_used"] is False
    assert all(batch["exact_two_output_compliance"] for batch in result["batch_results"])
    assert all(batch["malformed_count"] == 0 for batch in result["batch_results"])
    assert all(batch["timeout_count"] == 0 for batch in result["batch_results"])
    assert all(batch["error_count"] == 0 for batch in result["batch_results"])
    assert len({batch["seed"] for batch in result["batch_results"]}) == 3
    assert len({tuple(batch["family_ids"]) for batch in result["batch_results"]}) == 3


def test_mock_readiness_run_is_deterministic_across_invocations() -> None:
    first = run_arc_synthetic_official_shape_mock_readiness_v1()
    second = run_arc_synthetic_official_shape_mock_readiness_v1()
    assert first["readiness_verdict"] == second["readiness_verdict"]
    assert first["overall_summary"]["task_score"] == second["overall_summary"]["task_score"]
    assert first["overall_summary"]["solver_exact_count"] == second["overall_summary"]["solver_exact_count"]
    assert first["overall_summary"]["baseline_exact_count"] == second["overall_summary"]["baseline_exact_count"]
