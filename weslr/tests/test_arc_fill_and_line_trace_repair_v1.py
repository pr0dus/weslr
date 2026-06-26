from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from weslr.arc_style_depth2_compositional_program_search import (
    run_arc_style_depth2_compositional_program_search_v1,
    summarize_arc_style_depth2_compositional_program_search_result_v1,
    to_arc_style_depth2_compositional_program_search_json_safe_v1,
    validate_arc_style_depth2_compositional_program_search_result_v1,
)


@lru_cache(maxsize=2)
def _search_result() -> dict[str, Any]:
    return run_arc_style_depth2_compositional_program_search_v1(seed=20260625)


def test_fill_and_line_repair_metrics_are_stable_and_json_safe() -> None:
    first = _search_result()
    second = run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    assert to_arc_style_depth2_compositional_program_search_json_safe_v1(first) == to_arc_style_depth2_compositional_program_search_json_safe_v1(second)
    assert json.dumps(to_arc_style_depth2_compositional_program_search_json_safe_v1(first), ensure_ascii=False)
    assert validate_arc_style_depth2_compositional_program_search_result_v1(first)["valid"] is True
    assert summarize_arc_style_depth2_compositional_program_search_result_v1(first)["valid"] is True
    assert first["heldout_search_after"]["exact_count"] == 12
    assert first["heldout_search_after"]["partial_count"] == 2
    assert first["heldout_search_after"]["unsupported_count"] == 0
    assert first["comparison_report"]["exact_improvement"] == 11
    assert first["comparison_report"]["known_family_baseline_before"]["synthetic_exact_count"] == 41


def test_line_completion_repair_improves_while_fill_region_stays_safe_closed() -> None:
    result = _search_result()
    by_recipe = {(row["recipe_family_id"], row["variant_index"]): row for row in result["heldout_task_results"]}

    assert by_recipe[("remove_noise_then_complete_line", 0)]["heldout_fit_status"] == "fit"
    assert by_recipe[("remove_noise_then_complete_line", 1)]["heldout_fit_status"] == "fit"
    assert by_recipe[("remove_noise_then_complete_line", 0)]["mismatch_categories"] == []
    assert by_recipe[("remove_noise_then_complete_line", 1)]["mismatch_categories"] == []

    assert by_recipe[("fill_region_then_extract_object", 0)]["heldout_fit_status"] == "partial_fit"
    assert by_recipe[("fill_region_then_extract_object", 1)]["heldout_fit_status"] == "partial_fit"
    assert "wrong color" in by_recipe[("fill_region_then_extract_object", 0)]["mismatch_categories"]
    assert "wrong color" in by_recipe[("fill_region_then_extract_object", 1)]["mismatch_categories"]
    assert result["heldout_search_after"]["partial_count"] == 2
    assert result["heldout_search_after"]["unsupported_count"] == 0
