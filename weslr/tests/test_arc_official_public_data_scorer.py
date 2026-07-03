from __future__ import annotations

import json

from weslr.arc_official_public_data_adapter import load_arc_official_public_dummy_no_data_bundle_v1
from weslr.arc_official_public_data_emitter import emit_arc_official_public_two_output_packet_v1
from weslr.arc_official_public_data_scorer import score_arc_official_public_top2_packet_v1


def test_scorer_uses_exact_equality_only() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    task = bundle["solver_visible_tasks"][0]
    reference = bundle["scorer_reference_tasks"][0]["reference_output"]
    emission = emit_arc_official_public_two_output_packet_v1(solver_visible_packet=task)
    score = score_arc_official_public_top2_packet_v1(top2_packet=emission["top2_packet"], reference_output=reference)
    assert score["valid"] is True
    assert score["task_score"] == 1
    assert score["solver_exact"] is True
    assert score["baseline_exact"] is False
    assert score["malformed_count"] == 0
    assert score["error_count"] == 0


def test_scorer_reports_zero_for_mismatch_without_leaking_reference_grid() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    task = bundle["solver_visible_tasks"][1]
    reference = bundle["scorer_reference_tasks"][1]["reference_output"]
    emission = emit_arc_official_public_two_output_packet_v1(solver_visible_packet=task)
    packet = dict(emission["top2_packet"])
    packet["attempts"] = [dict(packet["attempts"][0]), dict(packet["attempts"][1])]
    packet["attempts"][0]["grid"] = [[9]]
    packet["attempts"][1]["grid"] = [[8]]
    score = score_arc_official_public_top2_packet_v1(top2_packet=packet, reference_output=reference)
    assert score["valid"] is True
    assert score["task_score"] == 0
    assert score["solver_exact"] is False
    assert score["baseline_exact"] is False
    assert "reference_output" not in score
    assert "reference_grid" not in score
    assert "output_grid" not in json.dumps(score, ensure_ascii=False).lower()


def test_scorer_returns_metadata_safe_result_for_malformed_packet() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    reference = bundle["scorer_reference_tasks"][0]["reference_output"]
    score = score_arc_official_public_top2_packet_v1(top2_packet={"broken": True}, reference_output=reference)
    assert score["valid"] is False
    assert score["malformed_count"] == 1
    assert score["error_count"] == 1
    assert score["reference_shape"]["height"] > 0
