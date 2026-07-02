from __future__ import annotations

from copy import deepcopy

from weslr.arc_agi2_submission_contract import build_arc_agi2_top2_attempt_packet_v1, validate_arc_agi2_top2_attempt_packet_v1
from weslr.arc_synthetic_official_shape_mock_generator import build_arc_synthetic_official_shape_mock_bundle_v1
from weslr.arc_synthetic_official_shape_mock_scorer import (
    score_arc_synthetic_official_shape_mock_top2_packet_v1,
    summarize_arc_synthetic_official_shape_mock_scores_v1,
)


def _top2_packet_for_first_task():
    bundle = build_arc_synthetic_official_shape_mock_bundle_v1()
    batch = bundle["batches"][0]
    task = batch["solver_visible_tasks"][0]
    reference = batch["reference_tasks"][0]
    ref_grid = reference["expected_outputs"][0]
    solver_candidate = {
        "candidate_id": f"{task['task_id']}:solver:0",
        "grid": deepcopy(ref_grid),
        "source_candidate_id": f"{task['task_id']}:solver:0",
        "rank": 1,
        "confidence_label": "high",
        "evidence_labels": ["train_fit"],
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": {"candidate_role": "solver", "synthetic_only": True},
    }
    baseline_candidate = {
        "candidate_id": f"{task['task_id']}:baseline_copy:0",
        "grid": deepcopy(task["test_input"]),
        "source_candidate_id": f"{task['task_id']}:baseline_copy:0",
        "rank": 2,
        "confidence_label": "low",
        "evidence_labels": ["copy_input"],
        "leakage_flags": {
            "uses_test_output": False,
            "uses_solution_file": False,
            "uses_answer_key": False,
            "uses_hidden_private_data": False,
            "uses_task_id_shortcut": False,
            "uses_notes_shortcut": False,
            "lookup_table_detected": False,
        },
        "metadata": {"candidate_role": "baseline", "synthetic_only": True},
    }
    packet = build_arc_agi2_top2_attempt_packet_v1(
        task_id=task["task_id"],
        test_input_index=0,
        candidate_packets=[solver_candidate, baseline_candidate],
        metadata={"synthetic_only": True},
    )
    return packet, ref_grid, batch["family_ids"][0]


def test_mock_scorer_exact_match_and_validation_pass() -> None:
    packet, ref_grid, family_id = _top2_packet_for_first_task()
    validation = validate_arc_agi2_top2_attempt_packet_v1(packet)
    score = score_arc_synthetic_official_shape_mock_top2_packet_v1(top2_packet=packet, reference_output=ref_grid)
    assert validation["valid"] is True
    assert score["valid"] is True
    assert score["task_score"] == 1
    assert score["solver_exact"] is True
    assert score["baseline_exact"] is False
    assert score["malformed_count"] == 0
    assert score["timeout_count"] == 0
    assert score["error_count"] == 0
    assert score["reference_shape"]["height"] > 0
    assert family_id


def test_mock_scorer_is_exact_match_only() -> None:
    packet, ref_grid, _ = _top2_packet_for_first_task()
    packet["attempts"][0]["grid"] = deepcopy(ref_grid)
    packet["attempts"][1]["grid"] = deepcopy(ref_grid)
    packet["attempts"][0]["grid"][0][0] = 9 if ref_grid[0][0] != 9 else 8
    packet["attempts"][1]["grid"][0][0] = 9 if ref_grid[0][0] != 9 else 8
    score = score_arc_synthetic_official_shape_mock_top2_packet_v1(top2_packet=packet, reference_output=ref_grid)
    assert score["task_score"] == 0
    assert score["solver_exact"] is False
    assert score["baseline_exact"] is False


def test_mock_scorer_rejects_malformed_top2_packets() -> None:
    packet, ref_grid, _ = _top2_packet_for_first_task()
    packet["attempts"] = packet["attempts"][:1]
    malformed = score_arc_synthetic_official_shape_mock_top2_packet_v1(top2_packet=packet, reference_output=ref_grid)
    summary = summarize_arc_synthetic_official_shape_mock_scores_v1([malformed])
    assert malformed["valid"] is False
    assert malformed["malformed_count"] == 1
    assert summary["malformed_count"] == 1
    assert summary["valid"] is False
