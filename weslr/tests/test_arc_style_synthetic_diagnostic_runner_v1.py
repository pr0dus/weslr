from __future__ import annotations

import json

from weslr.arc_style_synthetic_diagnostic_runner import (
    CANONICAL_PACKET_COUNT_V1,
    OPTIONAL_SHUFFLED_PACKET_COUNT_V1,
    RUNNER_ID_V1,
    build_arc_style_synthetic_diagnostic_plan_v1,
    run_arc_style_synthetic_120_diagnostic_runner_v1,
    summarize_arc_style_synthetic_120_diagnostic_runner_v1,
    to_arc_style_synthetic_diagnostic_runner_json_safe_v1,
)
from weslr.arc_style_synthetic_task_generators import REQUIRED_FAMILIES_V1


def test_diagnostic_plan_builds_canonical_120_and_optional_shuffled_entries() -> None:
    plan = build_arc_style_synthetic_diagnostic_plan_v1()
    assert plan["runner_id"] == RUNNER_ID_V1
    assert len(plan["canonical_entries"]) == CANONICAL_PACKET_COUNT_V1
    assert len(plan["optional_entries"]["shuffled_renamed"]) == OPTIONAL_SHUFFLED_PACKET_COUNT_V1


def test_diagnostic_runner_is_deterministic_and_json_safe() -> None:
    first = run_arc_style_synthetic_120_diagnostic_runner_v1()
    second = run_arc_style_synthetic_120_diagnostic_runner_v1()
    assert summarize_arc_style_synthetic_120_diagnostic_runner_v1(first) == summarize_arc_style_synthetic_120_diagnostic_runner_v1(second)
    assert to_arc_style_synthetic_diagnostic_runner_json_safe_v1(first) == to_arc_style_synthetic_diagnostic_runner_json_safe_v1(second)
    assert json.dumps(first, ensure_ascii=False)


def test_diagnostic_runner_covers_all_required_families_and_modes() -> None:
    result = run_arc_style_synthetic_120_diagnostic_runner_v1()
    assert result["canonical_packet_count"] == CANONICAL_PACKET_COUNT_V1
    assert result["canonical_modes"] == [
        "full_metadata",
        "toy_task_type_preserved_only",
        "fully_stripped_train_pairs_plus_test_input_only",
    ]
    assert result["optional_modes"] == ["shuffled_renamed"]
    assert set(result["canonical_family_summary"].keys()) == set(REQUIRED_FAMILIES_V1)
    assert result["canonical_exact"] == 109
    assert result["canonical_partial"] == 11
    assert result["canonical_unsupported"] == 0
    assert result["canonical_failed"] == 0
    assert result["canonical_mode_results"]["full_metadata"]["exact"] == 45
    assert result["canonical_mode_results"]["full_metadata"]["partial"] == 3
    assert result["canonical_mode_results"]["full_metadata"]["unsupported"] == 0
    assert result["canonical_mode_results"]["toy_task_type_preserved_only"]["exact"] == 35
    assert result["canonical_mode_results"]["toy_task_type_preserved_only"]["partial"] == 1
    assert result["canonical_mode_results"]["toy_task_type_preserved_only"]["unsupported"] == 0
    assert result["canonical_mode_results"]["fully_stripped_train_pairs_plus_test_input_only"]["exact"] == 29
    assert result["canonical_mode_results"]["fully_stripped_train_pairs_plus_test_input_only"]["partial"] == 7
    assert result["canonical_mode_results"]["fully_stripped_train_pairs_plus_test_input_only"]["unsupported"] == 0
    assert result["optional_mode_results"]["shuffled_renamed"]["exact"] == 35
    assert result["optional_mode_results"]["shuffled_renamed"]["partial"] == 1
    assert result["optional_mode_results"]["shuffled_renamed"]["unsupported"] == 0
    reflect_summary = result["canonical_family_summary"]["reflect_object_horizontal_or_vertical"]
    assert reflect_summary == {"exact": 7, "partial": 3, "unsupported": 0, "failed": 0}
    assert result["canonical_mode_results"]["full_metadata"]["family_summary"]["reflect_object_horizontal_or_vertical"] == {"exact": 4, "partial": 0, "unsupported": 0, "failed": 0}
    assert result["canonical_mode_results"]["toy_task_type_preserved_only"]["family_summary"]["reflect_object_horizontal_or_vertical"] == {"exact": 3, "partial": 0, "unsupported": 0, "failed": 0}
    assert result["canonical_mode_results"]["fully_stripped_train_pairs_plus_test_input_only"]["family_summary"]["reflect_object_horizontal_or_vertical"] == {"exact": 0, "partial": 3, "unsupported": 0, "failed": 0}
    assert result["canonical_family_summary"]["copy_grid"] == {"exact": 6, "partial": 4, "unsupported": 0, "failed": 0}
    assert result["canonical_family_summary"]["object_count_to_pattern"] == {"exact": 9, "partial": 1, "unsupported": 0, "failed": 0}
    assert result["canonical_family_summary"]["rotate_object_90"] == {"exact": 7, "partial": 3, "unsupported": 0, "failed": 0}
    assert result["leakage_flags"]["synthetic_only"] is True
    assert result["no_score_claim"] is True
    assert result["official_score_claim"] is False
    assert result["toy_task_type_dependency"]["dependency_still_present"] is True
    assert result["trace_flags"]["uses_test_output"] is False
    assert result["trace_flags"]["uses_task_id_for_candidate_selection"] is False
    assert result["trace_flags"]["uses_notes_for_candidate_selection"] is False
    assert result["trace_flags"]["lookup_table_detected"] is False
