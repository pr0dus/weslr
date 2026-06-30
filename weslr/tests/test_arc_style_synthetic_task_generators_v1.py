from __future__ import annotations

import json

from weslr.arc_agi2_submission_contract import (
    build_arc_agi2_top2_attempt_packet_v1,
    validate_arc_agi2_top2_attempt_packet_v1,
)
from weslr.arc_style_grid_schema_helpers import (
    build_arc_style_grid_metadata_v1,
    validate_arc_style_grid_task_packet_v1,
)
from weslr.arc_style_grid_adapter_phase2 import (
    build_arc_style_grid_candidate_result_v1,
    validate_arc_style_train_pair_with_candidate_v1,
)
from weslr.arc_style_synthetic_solver_suite import _supported_primitive_grid
from weslr.arc_style_synthetic_task_generators import (
    REQUIRED_FAMILIES_V1,
    build_arc_style_synthetic_generator_spec_v1,
    build_initial_arc_style_synthetic_generator_specs_v1,
    generate_arc_style_synthetic_task_family_v1,
    generate_arc_style_synthetic_task_suite_v1,
    summarize_arc_style_synthetic_task_suite_v1,
    to_arc_style_synthetic_task_suite_json_safe_v1,
    validate_arc_style_synthetic_generator_spec_v1,
    validate_arc_style_synthetic_task_family_v1,
    validate_arc_style_synthetic_task_suite_v1,
)


def test_initial_specs_cover_all_families_and_three_variants_each() -> None:
    specs = build_initial_arc_style_synthetic_generator_specs_v1()
    assert len(specs) == 36
    families = [spec["family_id"] for spec in specs]
    assert set(families) == set(REQUIRED_FAMILIES_V1)
    for family_id in REQUIRED_FAMILIES_V1:
        assert families.count(family_id) == 3
    assert all(validate_arc_style_synthetic_generator_spec_v1(spec)["valid"] for spec in specs)


def test_invalid_generator_specs_are_rejected() -> None:
    bad_family = build_arc_style_synthetic_generator_spec_v1(
        family_id="not_a_family",
        variant_index=0,
        task_id="bad",
        train_pair_count=0,
        test_input_count=0,
        difficulty_label="",
        transformation_labels=[],
        generation_parameters={},
        leakage_flags={"synthetic_only": False},
    )
    validation = validate_arc_style_synthetic_generator_spec_v1(bad_family)
    assert validation["valid"] is False
    assert "family_id_not_supported" in validation["blocked_reason_labels"]
    assert "train_pair_count_invalid" in validation["blocked_reason_labels"]
    assert "test_input_count_invalid" in validation["blocked_reason_labels"]


def test_suite_generation_validation_and_summary_pass() -> None:
    suite = generate_arc_style_synthetic_task_suite_v1()
    validation = validate_arc_style_synthetic_task_suite_v1(suite)
    summary = summarize_arc_style_synthetic_task_suite_v1(suite)
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert summary["family_count"] == 12
    assert summary["task_count"] == 36
    assert summary["top2_contract_compatibility_checked"] is True
    assert summary["leakage_clean"] is True
    assert set(summary["families"]) == set(REQUIRED_FAMILIES_V1)
    assert len(summary["difficulty_labels"]) == 3
    assert "synthetic_only" not in suite
    assert "expected_outputs" not in suite
    assert suite["top2_contract_compatibility_checked"] is True
    assert json.dumps(to_arc_style_synthetic_task_suite_json_safe_v1(suite), ensure_ascii=False)


def test_every_task_family_validates_and_keeps_expected_outputs_in_validation_metadata_only() -> None:
    suite = generate_arc_style_synthetic_task_suite_v1()
    for task in suite["tasks"]:
        task_validation = validate_arc_style_synthetic_task_family_v1(task)
        assert task_validation["valid"] is True
        assert task["leakage_flags"]["synthetic_only"] is True
        assert all(not task["leakage_flags"][name] for name in task["leakage_flags"] if name != "synthetic_only")
        assert "expected_outputs" not in task
        assert task["validation_metadata"]["synthetic_only"] is True
        assert len(task["validation_metadata"]["expected_outputs"]) == len(task["test_inputs"])
        assert task["generator_metadata"]["top2_contract_compatibility_checked"] is True
        for packet in task["generator_metadata"]["arc_style_task_packets"]:
            packet_validation = validate_arc_style_grid_task_packet_v1(packet)
            assert packet_validation["valid"] is True
            assert packet["test_input"]["invalid_cells"] == []
        for train_pair in task["train_pairs"]:
            assert build_arc_style_grid_metadata_v1(train_pair["input_grid"])["invalid_cells"] == []
            assert build_arc_style_grid_metadata_v1(train_pair["output_grid"])["invalid_cells"] == []
        for test_input in task["test_inputs"]:
            assert build_arc_style_grid_metadata_v1(test_input["input_grid"])["invalid_cells"] == []
        for expected_output in task["validation_metadata"]["expected_outputs"]:
            assert expected_output["synthetic_only"] is True
            assert build_arc_style_grid_metadata_v1(expected_output["output_grid"])["invalid_cells"] == []


def test_multiple_test_input_variants_exist() -> None:
    suite = generate_arc_style_synthetic_task_suite_v1()
    assert any(len(task["test_inputs"]) > 1 for task in suite["tasks"])


def test_deterministic_generation_is_stable() -> None:
    first = generate_arc_style_synthetic_task_suite_v1()
    second = generate_arc_style_synthetic_task_suite_v1()
    assert to_arc_style_synthetic_task_suite_json_safe_v1(first) == to_arc_style_synthetic_task_suite_json_safe_v1(second)


def test_top2_contract_compatibility_path_works() -> None:
    task = generate_arc_style_synthetic_task_suite_v1()["tasks"][0]
    expected_output = task["validation_metadata"]["expected_outputs"][0]["output_grid"]
    distractor = [row[:] for row in expected_output]
    distractor[0][0] = 9 if distractor[0][0] != 9 else 8
    packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task["task_id"],
        test_input_index=0,
        candidate_packets=[
            {
                "candidate_id": "candidate_expected",
                "grid": expected_output,
                "confidence_label": "high",
                "evidence_labels": ["synthetic_expected_output"],
                "leakage_flags": {"synthetic_only": True},
                "metadata": {"synthetic_only": True},
            },
            {
                "candidate_id": "candidate_distractor",
                "grid": distractor,
                "confidence_label": "medium",
                "evidence_labels": ["synthetic_distractor"],
                "leakage_flags": {"synthetic_only": True},
                "metadata": {"synthetic_only": True},
            },
        ],
    )
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    assert validation["valid"] is True
    assert len(packet["attempts"]) == 2


def test_suite_summary_reports_expected_shape_counts() -> None:
    suite = generate_arc_style_synthetic_task_suite_v1()
    summary = summarize_arc_style_synthetic_task_suite_v1(suite)
    assert summary["family_count"] == 12
    assert summary["task_count"] == 36
    assert summary["train_pair_count"] >= 72
    assert summary["test_input_count"] >= 48
    assert summary["top2_contract_compatibility_checked"] is True


def test_copy_grid_variant_2_generator_breaks_rotate_equivalence_but_preserves_copy() -> None:
    suite = generate_arc_style_synthetic_task_suite_v1()
    task = next(task for task in suite["tasks"] if task["task_id"] == "synthetic_copy_grid_variant_2_v1")
    train_pairs = task["train_pairs"]
    expected_outputs = task["validation_metadata"]["expected_outputs"]
    copy_candidate = build_arc_style_grid_candidate_result_v1(
        "copy",
        candidate_type="copy_candidate",
        primitive_sequence=[{"primitive_id": "copy", "parameters": {}}],
        train_fit_status="unknown",
        confidence_metadata={},
        calibration_metadata={},
    )
    rotate_candidate = build_arc_style_grid_candidate_result_v1(
        "rotate_object_90",
        candidate_type="rotate_object_90_candidate",
        primitive_sequence=[{"primitive_id": "rotate_object_90", "parameters": {"object_value": 2, "background_value": 0}}],
        train_fit_status="unknown",
        confidence_metadata={},
        calibration_metadata={},
    )
    copy_fit = sum(1 for pair in train_pairs if validate_arc_style_train_pair_with_candidate_v1(pair, copy_candidate)["exact_match"])
    rotate_fit = sum(1 for pair in train_pairs if validate_arc_style_train_pair_with_candidate_v1(pair, rotate_candidate)["exact_match"])
    assert copy_fit == 3
    assert rotate_fit < 3
    for test_input, expected in zip(task["test_inputs"], expected_outputs):
        copy_pred = _supported_primitive_grid({"primitive_id": "copy", "primitive_sequence": [{"primitive_id": "copy", "parameters": {}}]}, test_input["input_grid"])
        assert copy_pred == expected["output_grid"]

