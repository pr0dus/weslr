from __future__ import annotations

import json

from weslr.arc_synthetic_official_shape_blind_runner import (
    run_arc_synthetic_official_shape_blind_readiness_v1,
    summarize_arc_synthetic_official_shape_blind_readiness_v1,
)


FORBIDDEN_TOKENS = (
    "family_id",
    "variant_id",
    "toy_task_type",
    "primitive",
    "reflect",
    "rotate",
    "transform_label",
    "expected_output",
    "source_task_id",
)


def test_blind_readiness_run_beats_baseline_and_keeps_labels_hidden() -> None:
    result = run_arc_synthetic_official_shape_blind_readiness_v1()
    summary = summarize_arc_synthetic_official_shape_blind_readiness_v1(result)

    assert result["synthetic_only"] is True
    assert result["official_data_touched"] is False
    assert result["public_data_touched"] is False
    assert result["network_touched"] is False
    assert result["batch_count"] == 20
    assert result["task_count"] == 240
    assert result["blind_readiness_signal"] is True
    assert result["compatibility_readiness_signal"] is True
    assert result["readiness_verdict"] == "blind_mock_ready_for_public_parse_scorer_design"
    assert result["exact_two_output_compliance"] is True
    assert result["audit"]["expected_output_visible_to_solver"] is False
    assert result["audit"]["expected_output_leakage"] is False
    assert result["audit"]["scorer_reference_visible_to_solver"] is False
    assert result["audit"]["toy_task_type_visible_to_solver"] is False
    assert result["audit"]["family_id_visible_to_solver"] is False
    assert result["audit"]["variant_id_visible_to_solver"] is False
    assert result["audit"]["semantic_task_id_visible_to_solver"] is False
    assert result["audit"]["family_metadata_used_after_prediction_only"] is True

    assert summary["valid"] is True
    assert summary["solver_exact_count"] == 240
    assert summary["baseline_exact_count"] == 20
    assert summary["malformed_count"] == 0
    assert summary["timeout_count"] == 0
    assert summary["error_count"] == 0
    assert summary["compatibility_solver_exact_count"] > summary["compatibility_baseline_exact_count"]
    assert summary["compatibility_solver_exact_count"] == 200
    assert summary["compatibility_baseline_exact_count"] == 20

    blind_batches = result["blind_batch_results"]
    assert len(blind_batches) == 20
    assert all(batch["task_count"] == 12 for batch in blind_batches)
    assert all(batch["exact_two_output_compliance"] is True for batch in blind_batches)
    assert len({batch["seed"] for batch in blind_batches}) == 20

    family_scores = summary["family_scores"]
    reflect = family_scores["reflect_object_horizontal_or_vertical"]
    rotate = family_scores["rotate_object_90"]
    assert reflect["solver_exact"] == 20
    assert rotate["solver_exact"] == 20
    assert reflect["baseline_exact"] == 0
    assert rotate["baseline_exact"] == 0

    for batch in blind_batches:
        for task in batch["task_results"]:
            visible_packet = task["visible_packet"]
            top2_packet = task["top2_packet"]
            assert len(top2_packet["attempts"]) == 2
            assert visible_packet["task_id"].startswith("blind_")
            assert "family_id" not in visible_packet
            assert "variant_index" not in visible_packet
            assert "expected_output" not in visible_packet
            serialized_visible = json.dumps(visible_packet, ensure_ascii=False).lower()
            serialized_top2 = json.dumps(top2_packet, ensure_ascii=False).lower()
            assert all(token not in serialized_visible for token in FORBIDDEN_TOKENS)
            assert all(token not in serialized_top2 for token in FORBIDDEN_TOKENS)
            assert task["solver_exact"] is True
            assert task["baseline_exact"] in {False, True}
            assert task["malformed_count"] == 0
            assert task["timeout_count"] == 0
            assert task["error_count"] == 0


def test_blind_readiness_is_deterministic_across_invocations() -> None:
    first = run_arc_synthetic_official_shape_blind_readiness_v1()
    second = run_arc_synthetic_official_shape_blind_readiness_v1()
    assert first["readiness_verdict"] == second["readiness_verdict"]
    assert first["blind_overall_summary"]["task_score"] == second["blind_overall_summary"]["task_score"]
    assert first["blind_overall_summary"]["solver_exact_count"] == second["blind_overall_summary"]["solver_exact_count"]
    assert first["blind_overall_summary"]["baseline_exact_count"] == second["blind_overall_summary"]["baseline_exact_count"]
