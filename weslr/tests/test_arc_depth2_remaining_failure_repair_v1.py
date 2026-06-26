from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from weslr.arc_controlled_improvement_evidence import (
    build_arc_controlled_improvement_evidence_chain_v1,
    build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1,
    summarize_arc_controlled_improvement_evidence_v1,
    validate_arc_controlled_improvement_evidence_chain_v1,
    validate_arc_controlled_improvement_evidence_packet_v1,
)
from weslr.arc_style_depth2_compositional_program_search import (
    run_arc_style_depth2_compositional_program_search_v1,
    summarize_arc_style_depth2_compositional_program_search_result_v1,
    to_arc_style_depth2_compositional_program_search_json_safe_v1,
    validate_arc_style_depth2_compositional_program_search_result_v1,
)
from weslr.arc_style_heldout_compositional_baseline import run_arc_style_heldout_compositional_baseline_v1


@lru_cache(maxsize=2)
def _search_result() -> dict[str, Any]:
    return run_arc_style_depth2_compositional_program_search_v1(seed=20260625)


@lru_cache(maxsize=2)
def _baseline_result() -> dict[str, Any]:
    return run_arc_style_heldout_compositional_baseline_v1(seed=20260625)


def test_repair_lane_measurement_is_stable_and_depth2_only() -> None:
    first = _search_result()
    second = run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    assert to_arc_style_depth2_compositional_program_search_json_safe_v1(first) == to_arc_style_depth2_compositional_program_search_json_safe_v1(second)
    assert json.dumps(to_arc_style_depth2_compositional_program_search_json_safe_v1(first), ensure_ascii=False)
    assert first["depth"] == 2
    assert first["search_type"] == "arc_style_depth2_compositional_program_search_v1"
    assert validate_arc_style_depth2_compositional_program_search_result_v1(first)["valid"] is True
    assert summarize_arc_style_depth2_compositional_program_search_result_v1(first)["valid"] is True
    assert first["heldout_baseline_before"]["exact_count"] == 1
    assert first["heldout_baseline_before"]["partial_count"] == 2
    assert first["heldout_baseline_before"]["unsupported_count"] == 11
    assert first["heldout_search_after"]["exact_count"] == 10
    assert first["heldout_search_after"]["partial_count"] == 2
    assert first["heldout_search_after"]["unsupported_count"] == 2
    assert first["comparison_report"]["exact_improvement"] == 9
    assert first["comparison_report"]["unsupported_reduction"] == 9
    assert first["comparison_report"]["known_family_baseline_before"] == first["comparison_report"]["known_family_baseline_after"]
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_exact_count"] == 41
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_partial_count"] == 3
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_unsupported_count"] == 4


def test_repair_lane_per_recipe_outcomes_and_remaining_gap_causes() -> None:
    result = _search_result()
    by_recipe = {(row["recipe_family_id"], row["variant_index"]): row for row in result["heldout_task_results"]}

    assert by_recipe[("move_then_border", 0)]["heldout_fit_status"] == "fit"
    assert by_recipe[("move_then_border", 1)]["heldout_fit_status"] == "fit"

    assert by_recipe[("remove_noise_then_complete_line", 0)]["heldout_fit_status"] == "fit"
    assert by_recipe[("remove_noise_then_complete_line", 1)]["heldout_fit_status"] == "fit"

    assert by_recipe[("fill_region_then_extract_object", 0)]["heldout_fit_status"] == "partial_fit"
    assert by_recipe[("fill_region_then_extract_object", 1)]["heldout_fit_status"] == "partial_fit"
    assert "wrong color" in by_recipe[("fill_region_then_extract_object", 0)]["mismatch_categories"]
    assert "wrong reflection/rotation orientation" in by_recipe[("fill_region_then_extract_object", 0)]["mismatch_categories"]

    assert by_recipe[("count_object_then_emit_pattern", 0)]["heldout_fit_status"] == "fit"
    assert by_recipe[("count_object_then_emit_pattern", 1)]["heldout_fit_status"] == "fit"

    assert by_recipe[("rotate_then_recolor", 0)]["heldout_fit_status"] == "unsupported"
    assert by_recipe[("rotate_then_recolor", 1)]["heldout_fit_status"] == "unsupported"
    assert "output-size mismatch" in by_recipe[("rotate_then_recolor", 0)]["mismatch_categories"]

    for task_result in result["heldout_task_results"]:
        assert task_result["search_trace"]["heldout_evaluation_delay"] is True
        assert task_result["selected_top2_program_packet_validation"]["valid"] is True
        assert task_result["solver_visible_expected_outputs_absent"] is True
        assert task_result["evaluation_outputs_separated"] is True


def test_controlled_improvement_evidence_reflects_repaired_measurement_and_rejects_unsafe_claims() -> None:
    packet = build_arc_controlled_improvement_evidence_fixture_depth2_compositional_search_v1()
    summary = summarize_arc_controlled_improvement_evidence_v1(packet)
    chain = build_arc_controlled_improvement_evidence_chain_v1()
    assert validate_arc_controlled_improvement_evidence_packet_v1(packet)["valid"] is True
    assert summary["exact_delta"] == 9
    assert summary["unsupported_delta"] == -9
    assert chain["summary"]["heldout_exact_gain"] == 9
    assert validate_arc_controlled_improvement_evidence_chain_v1(chain)["valid"] is True

    mutated = json.loads(json.dumps(packet))
    mutated["non_claim_flags"]["public_score_claimed"] = True
    assert validate_arc_controlled_improvement_evidence_packet_v1(mutated)["valid"] is False

    baseline = _baseline_result()
    assert baseline["known_family_baseline_summary"]["synthetic_exact_count"] == 41
    assert baseline["known_family_baseline_summary"]["synthetic_partial_count"] == 3
    assert baseline["known_family_baseline_summary"]["synthetic_unsupported_count"] == 4
