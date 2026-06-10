from __future__ import annotations

from copy import deepcopy

import pytest

from weslr.cognitive_research_protocol import validate_cognitive_research_run_v1
from weslr.perspicuity_scorer import (
    build_initial_perspicuity_examples_v1,
    build_perspicuity_candidate_v1,
    build_perspicuity_dimension_score_v1,
    build_perspicuity_packet_v1,
    build_perspicuity_ranking_entry_v1,
    build_perspicuity_scorecard_v1,
    summarize_perspicuity_packet_v1,
    to_perspicuity_json_safe_v1,
    validate_perspicuity_packet_v1,
)


def _candidate(candidate_type: str = "source_signal", source_engine_name: str = "unknown_engine", **overrides):
    payload = {
        "candidate_type": candidate_type,
        "source_engine_name": source_engine_name,
        "source_run_id": f"run-{source_engine_name}-{candidate_type}",
        "candidate_summary": f"{source_engine_name} {candidate_type} candidate.",
        "candidate_scope": "metadata-only scope",
        "known_scope": "metadata-only scope",
        "failure_scope": "bounded failure scope",
        "uncertainty_factors": ["candidate remains provisional"],
        "invalidation_signals": ["not yet invalidated"],
        "public_claim_status": "internal_candidate_only",
    }
    payload.update(overrides)
    return build_perspicuity_candidate_v1(payload)


def _raw_candidate(candidate_type: str = "source_signal", source_engine_name: str = "unknown_engine", **overrides):
    payload = {
        "candidate_id": f"candidate-{source_engine_name}-{candidate_type}",
        "source_engine_name": source_engine_name,
        "source_run_id": f"run-{source_engine_name}-{candidate_type}",
        "candidate_type": candidate_type,
        "candidate_summary": f"{source_engine_name} {candidate_type} candidate.",
        "candidate_scope": "metadata-only scope",
        "known_scope": "metadata-only scope",
        "failure_scope": "bounded failure scope",
        "uncertainty_factors": ["candidate remains provisional"],
        "invalidation_signals": ["not yet invalidated"],
        "public_claim_status": "internal_candidate_only",
    }
    payload.update(overrides)
    return payload


def _packet(candidate_type: str = "source_signal", source_engine_name: str = "unknown_engine", **overrides):
    candidate = _candidate(candidate_type, source_engine_name, **overrides.pop("candidate_overrides", {}))
    payload = {
        "engine_name": "perspicuity_scorer",
        "engine_family": "candidate_ranking",
        "research_mode": overrides.pop("research_mode", "internal_exploration"),
        "input_artifact_ref": overrides.pop("input_artifact_ref", f"artifact:{source_engine_name}-{candidate_type}"),
        "input_artifact_type": "candidate",
        "input_summary": overrides.pop("input_summary", candidate["candidate_summary"]),
        "perspicuity_candidates": overrides.pop("perspicuity_candidates", [candidate]),
        "public_claim_status": overrides.pop("public_claim_status", candidate["public_claim_status"]),
        "public_gap_card_status": overrides.pop("public_gap_card_status", "public_export_blocked"),
        "llm_helper_role": "candidate_generator_only",
        "non_actionable_research_only": True,
        "simulation_before_real_world": True,
        "safe_metadata": {"safe": True, "metadata_only": True, "perspicuity_is_not_a_gate": True},
    }
    payload.update(overrides)
    return build_perspicuity_packet_v1(payload)


@pytest.mark.parametrize(
    "candidate_type, source_engine_name",
    [
        ("source_signal", "unknown_engine"),
        ("generated_source_signal", "raw_signal_cartographer"),
        ("operator_candidate", "nonlinear_inspiration_engine"),
        ("translation_candidate", "nonlinear_inspiration_engine"),
        ("structural_match_candidate", "raw_signal_cartographer"),
        ("pressure_result", "rule_pressure_engine"),
        ("dialectic_turn", "dialectic_generator_loop"),
        ("calibration_record", "forecast_calibration_bridge"),
    ],
)
def test_valid_candidate_types_pass(candidate_type, source_engine_name):
    packet = _packet(candidate_type=candidate_type, source_engine_name=source_engine_name)
    assert validate_perspicuity_packet_v1(packet)["blocked"] is False
    assert validate_cognitive_research_run_v1(packet)["blocked"] is False


@pytest.mark.parametrize(
    "dimension, score_label",
    [
        ("clarity", "high"),
        ("signal_density", "high"),
        ("novelty", "medium"),
        ("testability", "high"),
        ("pressure_worthiness", "high"),
        ("calibration_value", "medium"),
        ("cross_domain_resonance", "high"),
        ("compression_value", "medium"),
        ("risk_of_false_pattern", "low"),
        ("boundary_sensitivity", "medium"),
    ],
)
def test_dimension_score_builder_emits_required_fields(dimension, score_label):
    score = build_perspicuity_dimension_score_v1(
        {
            "dimension": dimension,
            "score_label": score_label,
            "reason": "metadata-only internal ranking rationale",
            "supporting_metadata_refs": ["candidate-1"],
            "uncertainty_note": "provisional",
        }
    )
    assert set(score) == {"dimension", "score_label", "reason", "supporting_metadata_refs", "uncertainty_note"}
    assert score["dimension"] == dimension
    assert score["score_label"] == score_label


def test_valid_dimension_scores_pass_for_all_required_dimensions():
    packet = _packet()
    dimensions = {item["dimension"] for item in packet["perspicuity_scorecard"]["dimension_scores"]}
    assert dimensions == {
        "clarity",
        "signal_density",
        "novelty",
        "testability",
        "pressure_worthiness",
        "calibration_value",
        "cross_domain_resonance",
        "compression_value",
        "risk_of_false_pattern",
        "boundary_sensitivity",
    }
    assert validate_perspicuity_packet_v1(packet)["blocked"] is False


def test_valid_scorecard_passes():
    candidate = _candidate("pressure_result", "rule_pressure_engine")
    scorecard = build_perspicuity_scorecard_v1({"candidate": candidate})
    assert scorecard["overall_priority"] in {
        "drop",
        "archive",
        "watch",
        "probe",
        "pressure_test",
        "calibrate",
        "promote_to_next_internal_step",
        "unknown",
    }
    assert scorecard["do_not_use_as_truth"] is True
    assert scorecard["public_claim_authorized"] is False
    assert scorecard["runtime_action_authorized"] is False
    assert scorecard["behavior_promotion_authorized"] is False


def test_valid_ranking_entry_passes():
    candidate = _candidate("dialectic_turn", "dialectic_generator_loop")
    scorecard = build_perspicuity_scorecard_v1({"candidate": candidate})
    entry = build_perspicuity_ranking_entry_v1({"candidate": candidate, "scorecard": scorecard})
    assert entry["rank_bucket"] in {"top", "high", "medium", "low", "blocked", "unknown"}
    assert entry["next_best_probe"]
    assert entry["next_best_pressure_test"]
    assert entry["blocked_reason"]
    assert validate_perspicuity_packet_v1(_packet())["blocked"] is False


def test_valid_packet_validates_as_cognitive_research_run_v1():
    packet = _packet(candidate_type="calibration_record", source_engine_name="forecast_calibration_bridge")
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "perspicuity_scorer"


def test_valid_packet_references_neighboring_engine_source_candidates():
    packet = build_perspicuity_packet_v1(
        {
            "engine_name": "perspicuity_scorer",
            "engine_family": "candidate_ranking",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:multi-candidate",
            "input_artifact_type": "candidate",
            "input_summary": "Multi-candidate packet.",
            "perspicuity_candidates": [
                _candidate("source_signal", "unknown_engine", candidate_summary="Unknown Engine candidate."),
                _candidate("operator_candidate", "nonlinear_inspiration_engine", candidate_summary="Nonlinear Inspiration candidate."),
                _candidate("pressure_result", "rule_pressure_engine", candidate_summary="Rule Pressure candidate."),
                _candidate("dialectic_turn", "dialectic_generator_loop", candidate_summary="Dialectic Generator Loop candidate."),
            ],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "safe_metadata": {"safe": True, "metadata_only": True, "perspicuity_is_not_a_gate": True},
        }
    )
    sources = [candidate["source_engine_name"] for candidate in packet["perspicuity_candidates"]]
    assert sources == [
        "unknown_engine",
        "nonlinear_inspiration_engine",
        "rule_pressure_engine",
        "dialectic_generator_loop",
    ]
    assert validate_perspicuity_packet_v1(packet)["blocked"] is False


def test_valid_scorecard_recommends_pressure_testing_without_authorizing_execution():
    packet = _packet(candidate_type="operator_candidate", source_engine_name="nonlinear_inspiration_engine")
    scorecard = packet["perspicuity_scorecard"]
    assert scorecard["recommended_next_action"]
    assert scorecard["public_claim_authorized"] is False
    assert scorecard["runtime_action_authorized"] is False
    assert scorecard["behavior_promotion_authorized"] is False


def test_valid_scorecard_recommends_calibration_without_authorizing_truth_or_public_claim():
    packet = _packet(candidate_type="calibration_record", source_engine_name="forecast_calibration_bridge")
    scorecard = packet["perspicuity_scorecard"]
    assert scorecard["overall_priority"] in {"calibrate", "pressure_test", "promote_to_next_internal_step", "watch", "probe", "archive", "drop", "unknown"}
    assert scorecard["do_not_use_as_truth"] is True
    assert scorecard["public_claim_authorized"] is False


def test_json_safe_copy_strips_unsafe_raw_fields():
    packet = _packet()
    packet["raw_private_text"] = "secret"
    packet["nested"] = {"hidden_prompt": "abc", "safe": "ok"}
    safe = to_perspicuity_json_safe_v1(packet)
    assert "raw_private_text" not in safe
    assert "nested" in safe
    assert "hidden_prompt" not in safe["nested"]
    assert safe["nested"]["safe"] == "ok"


def test_summary_is_concise_and_private_text_safe():
    packet = _packet()
    summary = summarize_perspicuity_packet_v1(packet)
    assert len(summary["summary_text"]) <= 320
    assert "secret" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_examples_include_expected_engine_candidates():
    examples = build_initial_perspicuity_examples_v1()
    assert len(examples) == 4
    sources = [example["perspicuity_candidates"][0]["source_engine_name"] for example in examples]
    assert sources == ["unknown_engine", "nonlinear_inspiration_engine", "rule_pressure_engine", "dialectic_generator_loop"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"perspicuity_candidates": [_raw_candidate(candidate_id="", candidate_type="source_signal", source_engine_name="unknown_engine", source_run_id="run-1", candidate_summary="ok", candidate_scope="s", known_scope="s", failure_scope="s", uncertainty_factors=["x"], invalidation_signals=["y"], public_claim_status="internal_candidate_only")]}, "missing_candidate_id"),
        ({"perspicuity_candidates": [_raw_candidate(candidate_type="source_signal", source_engine_name="unknown_engine", source_run_id="run-1", candidate_summary="", candidate_scope="s", known_scope="s", failure_scope="s", uncertainty_factors=["x"], invalidation_signals=["y"], public_claim_status="internal_candidate_only")]}, "missing_candidate_summary"),
        ({"perspicuity_candidates": [_raw_candidate(candidate_type="source_signal", source_engine_name="unknown_engine", source_run_id="run-1", candidate_summary="ok", candidate_scope="s", known_scope="s", failure_scope="s", uncertainty_factors=[], invalidation_signals=["y"], public_claim_status="internal_candidate_only")]}, "missing_uncertainty_factors"),
        ({"perspicuity_candidates": [_raw_candidate(candidate_type="source_signal", source_engine_name="unknown_engine", source_run_id="run-1", candidate_summary="ok", candidate_scope="s", known_scope="s", failure_scope="s", uncertainty_factors=["x"], invalidation_signals=[], public_claim_status="internal_candidate_only")]}, "missing_invalidation_signals"),
        ({"perspicuity_candidates": [_raw_candidate(candidate_type="source_signal", source_engine_name="unknown_engine", source_run_id="run-1", candidate_summary="ok", candidate_scope="s", known_scope="s", failure_scope="s", uncertainty_factors=["x"], invalidation_signals=["y"], public_claim_status="public_safe_summary_required")]}, "invalid_public_claim_status"),
    ],
)
def test_candidate_validation_fail_closed(mutation, expected_label):
    packet = _packet()
    packet.update(mutation)
    validation = validate_perspicuity_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "dimension_scores": [{"dimension": "invalid", "score_label": "high", "reason": "x", "supporting_metadata_refs": ["a"], "uncertainty_note": "y"}]}}, "invalid_score_dimension_0"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "dimension_scores": [{"dimension": "clarity", "score_label": "wrong", "reason": "x", "supporting_metadata_refs": ["a"], "uncertainty_note": "y"}]}}, "invalid_score_label_0"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "dimension_scores": [{"dimension": "clarity", "score_label": "high", "reason": "", "supporting_metadata_refs": ["a"], "uncertainty_note": "y"}]}}, "dimension_score_missing_reason_0"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "dimension_scores": []}}, "scorecard_without_dimension_scores"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "public_claim_authorized": True}}, "scorecard_authorizes_public_claim"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "runtime_action_authorized": True}}, "scorecard_authorizes_runtime_action"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "behavior_promotion_authorized": True}}, "scorecard_authorizes_behavior_promotion"),
        ({"perspicuity_scorecard": {**_packet()["perspicuity_scorecard"], "do_not_use_as_truth": False}}, "scorecard_treated_as_truth"),
    ],
)
def test_scorecard_validation_fail_closed(mutation, expected_label):
    packet = _packet()
    packet.update(mutation)
    validation = validate_perspicuity_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"perspicuity_ranking_entries": [{**_packet()["perspicuity_ranking_entries"][0], "next_best_probe": ""}]}, "ranking_entry_missing_next_probe"),
        ({"perspicuity_ranking_entries": [{**_packet()["perspicuity_ranking_entries"][0], "next_best_pressure_test": ""}]}, "ranking_entry_missing_next_pressure_test"),
        ({"perspicuity_ranking_entries": [{**_packet()["perspicuity_ranking_entries"][0], "calibration_prediction": None}]}, "ranking_entry_missing_calibration_prediction"),
        ({"perspicuity_ranking_entries": [{**_packet()["perspicuity_ranking_entries"][0], "blocked_reason": ""}]}, "ranking_entry_missing_blocked_reason"),
        ({"perspicuity_ranking_entries": [{**_packet()["perspicuity_ranking_entries"][0], "rank_reason": "proof of truth"}]}, "ranking_entry_marked_truth_or_proof"),
    ],
)
def test_ranking_entry_validation_fail_closed(mutation, expected_label):
    packet = _packet()
    packet.update(mutation)
    validation = validate_perspicuity_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_labels",
    [
        ("compressed_lesson", "public breakthrough proof", ("public_claim_language", "forbidden_packet_text")),
        ("compressed_lesson", "AGI consciousness sentience", ("forbidden_packet_text",)),
        ("compressed_lesson", "final-answer authority", ("forbidden_packet_text",)),
        ("compressed_lesson", "LLM authority claim", ("llm_as_authority", "forbidden_packet_text")),
        ("compressed_lesson", "safety gate replacement", ("forbidden_packet_text",)),
        ("compressed_lesson", "runtime provider tool persistence", ("forbidden_packet_text",)),
        ("compressed_lesson", ".weslr IO", ("forbidden_packet_text",)),
        ("compressed_lesson", "live ingestion network", ("forbidden_packet_text",)),
        ("compressed_lesson", "memory mutation authority", ("forbidden_packet_text",)),
        ("compressed_lesson", "project mutation authority", ("forbidden_packet_text",)),
        ("compressed_lesson", "behavior-pack promotion", ("forbidden_packet_text",)),
        ("safe_metadata", {}, ("unsafe_safe_metadata",)),
        ("denied_authority", None, ("missing_denied_authority",)),
        ("raw_private_text", "secret", ("raw_private_or_hidden_text",)),
        ("hidden_prompt", "secret prompt", ("raw_private_or_hidden_text",)),
    ],
)
def test_packet_validation_fail_closed(field, value, expected_labels):
    packet = _packet()
    packet[field] = value
    validation = validate_perspicuity_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in expected_labels)


def test_packet_rejects_public_claim_marked_safe():
    packet = _packet()
    packet["public_claim_status"] = "public_safe_summary_required"
    validation = validate_perspicuity_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_public_claim_status" in validation["blocked_labels"]
