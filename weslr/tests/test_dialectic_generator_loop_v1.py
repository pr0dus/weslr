from __future__ import annotations

from copy import deepcopy

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.dialectic_generator_loop import (
    build_dialectic_loop_packet_v1,
    build_dialectic_seed_candidate_v1,
    build_dialectic_turn_v1,
    build_generated_counter_signal_v1,
    build_generated_probe_signal_v1,
    build_initial_dialectic_loop_examples_v1,
    summarize_dialectic_loop_packet_v1,
    to_dialectic_loop_json_safe_v1,
    validate_dialectic_loop_packet_v1,
    validate_generated_probe_signal_v1,
)


def _packet(**overrides):
    base = {
        "engine_name": "dialectic_generator_loop",
        "research_mode": "internal_exploration",
        "input_artifact_ref": "artifact:dialectic-loop-001",
        "input_artifact_type": "dialectic-loop-bundle",
        "input_summary": "Metadata-only dialectic candidate loop.",
        "source_engine_name": "unknown_engine",
        "source_run_id": "run-dialectic-001",
        "seed_type": "hidden_rule_candidate",
        "seed_summary": "Hidden-rule candidate with bounded scope.",
        "candidate_claim_or_operator": "candidate rule",
        "known_scope": "bounded metadata-only scope",
        "failure_scope": "narrow failure scope",
        "uncertainty_factors": ["scope may shift under pressure"],
        "invalidation_signals": ["no invalidation observed yet"],
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "candidate_generator_only",
    }
    base.update(overrides)
    return build_dialectic_loop_packet_v1(base)


def _first_seed(packet):
    return packet["dialectic_seed_candidates"][0]


def _first_generated_signal(packet):
    return packet["generated_source_signals"][0]


def _first_counter_signal(packet):
    return packet["generated_counter_signals"][0]


def _first_turn(packet):
    return packet["dialectic_turns"][0]


def _assert_valid(packet):
    validation = validate_dialectic_loop_packet_v1(packet)
    assert validation["blocked"] is False
    assert protocol.validate_cognitive_research_run_v1(packet)["blocked"] is False
    return validation


def _assert_blocked(packet, fragment):
    validation = validate_dialectic_loop_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(fragment in label for label in validation["blocked_labels"])
    return validation


@pytest.mark.parametrize(
    "seed_type, source_engine_name, candidate_claim_or_operator, expected_fragment",
    [
        ("hidden_rule_candidate", "unknown_engine", "candidate rule", "hidden_rule"),
        ("operator_candidate", "nonlinear_inspiration_engine", "bridge operator", "operator"),
        ("translation_candidate", "unintelligible_output_analyzer", "candidate translation layer", "translation"),
        ("structural_match_candidate", "raw_signal_cartographer", "shared structure", "structural"),
    ],
)
def test_valid_seed_candidates_pass(seed_type, source_engine_name, candidate_claim_or_operator, expected_fragment):
    packet = _packet(
        seed_type=seed_type,
        source_engine_name=source_engine_name,
        candidate_claim_or_operator=candidate_claim_or_operator,
        seed_summary=f"{seed_type} summary",
        known_scope="bounded scope",
        failure_scope="failure scope",
    )
    validation = _assert_valid(packet)
    assert expected_fragment in packet["dialectic_seed_candidates"][0]["seed_type"]
    assert validation["engine_name"] == "dialectic_generator_loop"


@pytest.mark.parametrize(
    "seed_type, counter_signal_type",
    [
        ("hidden_rule_candidate", "counterexample"),
        ("structural_match_candidate", "boundary_case"),
        ("translation_candidate", "contradiction"),
        ("motif_candidate", "noise_variant"),
    ],
)
def test_valid_counter_signals_pass(seed_type, counter_signal_type):
    packet = _packet(seed_type=seed_type, seed_summary=f"{seed_type} summary")
    packet["generated_counter_signals"] = [
        build_generated_counter_signal_v1(
            {
                "seed": _first_seed(packet),
                "counter_signal_type": counter_signal_type,
                "counter_signal_summary": f"{counter_signal_type} counter signal",
                "what_it_challenges": "candidate rule",
                "expected_breakage": "hidden_assumption_failure",
                "target_uncertainty": "bounded uncertainty",
                "safe_to_reingest_as_metadata": True,
                "public_claim_status": "internal_candidate_only",
            }
        )
    ]
    _assert_valid(packet)
    assert packet["generated_counter_signals"][0]["counter_signal_type"] == counter_signal_type


@pytest.mark.parametrize(
    "move_type",
    ["attack", "mutate", "control"],
)
def test_valid_turns_pass(move_type):
    packet = _packet()
    packet["dialectic_turns"] = [
        build_dialectic_turn_v1(
            {
                "seed": _first_seed(packet),
                "turn_index": 0,
                "move_type": move_type,
                "move_summary": f"{move_type} the candidate in metadata only.",
                "generated_source_signal_ref": _first_generated_signal(packet)["generated_signal_id"],
                "pressure_test_ref": packet["rule_pressure_tests"][0]["pressure_test_id"],
                "calibration_record_ref": packet["calibration_record"]["record_id"],
                "compressed_lesson": f"{move_type} keeps the loop bounded.",
                "next_turn_recommendation": "control next.",
            }
        )
    ]
    _assert_valid(packet)
    assert packet["dialectic_turns"][0]["move_type"] == move_type


def test_valid_generated_probe_passes():
    packet = _packet(seed_type="operator_candidate", source_engine_name="nonlinear_inspiration_engine", candidate_claim_or_operator="bridge operator")
    probe = build_generated_probe_signal_v1(
        {
            "seed": _first_seed(packet),
            "research_mode": "calibration_replay",
            "probe_goal": "Probe whether the bridge operator survives pressure.",
            "probe_summary": "Calibration-ready probe for the bridge operator.",
            "expected_observation": "bounded bridge behavior",
            "falsification_condition": "if the bridge fails a control case",
            "next_best_observation": "compare with a control case",
        }
    )
    validation = validate_generated_probe_signal_v1(probe)
    assert validation["valid"] is True
    assert probe["calibration_prediction"]["prediction_type"] == "probe_prediction"
    assert probe["calibration_prediction"]["outcome_status"] == "not_observed_yet"


def test_full_packet_validates_as_cognitive_research_run():
    packet = _packet()
    validation = _assert_valid(packet)
    assert packet["engine_name"] == "dialectic_generator_loop"
    assert packet["engine_family"] == "recursive_generation"
    assert validation["research_mode"] == "internal_exploration"


def test_generated_source_signal_metadata_is_protocol_compatible():
    packet = _packet()
    signal = _first_generated_signal(packet)
    assert signal["generated_signal_id"]
    assert signal["parent_suggestion_id"] == _first_seed(packet)["seed_id"]
    assert signal["safe_to_reingest"] is True
    assert signal["raw_generated_content_included"] is False
    assert validate_dialectic_loop_packet_v1(packet)["blocked"] is False


def test_pressure_ready_metadata_is_rule_pressure_shape_compatible():
    packet = _packet(seed_type="hidden_rule_candidate", candidate_claim_or_operator="candidate rule")
    test = packet["rule_pressure_tests"][0]
    assert test["pressure_test_id"]
    assert test["pressure_type"] == "counterexample_search"
    assert test["safe_to_run_as_metadata"] is True
    assert test["calibration_prediction"]["prediction_type"] == "rule_pressure_prediction"
    assert test["calibration_prediction"]["outcome_status"] == "not_observed_yet"


def test_calibration_prediction_and_probe_metadata_are_bridge_compatible():
    packet = _packet()
    probe = build_generated_probe_signal_v1(
        {
            "seed": _first_seed(packet),
            "research_mode": "calibration_replay",
            "probe_goal": "Probe whether the hidden-rule candidate survives pressure.",
            "probe_summary": "Calibration-ready probe for the hidden-rule candidate.",
            "expected_observation": "bounded metadata-only behavior",
            "falsification_condition": "if a control case fails",
            "next_best_observation": "compare with a control case",
        }
    )
    assert probe["calibration_prediction"]["prediction_type"] == "probe_prediction"
    assert packet["calibration_record"]["prediction_type"] == "probe_prediction"
    assert packet["calibration_record"]["outcome_status"] == "not_observed_yet"


def test_json_safe_copy_strips_unsafe_raw_fields():
    packet = _packet()
    packet["raw_prompt"] = "secret prompt"
    packet["generated_source_signals"][0]["raw_response"] = "secret response"
    packet["dialectic_turns"][0]["hidden_prompt"] = "hidden"
    safe = to_dialectic_loop_json_safe_v1(packet)

    def _keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield key
                yield from _keys(item)
        elif isinstance(value, list):
            for item in value:
                yield from _keys(item)

    keys = list(_keys(safe))
    assert "raw_prompt" not in keys
    assert "raw_response" not in keys
    assert "hidden_prompt" not in keys


def test_summary_is_concise_and_private_safe():
    packet = _packet()
    summary = summarize_dialectic_loop_packet_v1(packet)
    assert len(summary["summary_text"]) <= 320
    assert "secret" not in summary["summary_text"].lower()
    assert "raw prompt" not in summary["summary_text"].lower()


def test_examples_include_required_loops():
    examples = build_initial_dialectic_loop_examples_v1()
    assert len(examples) >= 4
    assert examples[0]["dialectic_seed_candidates"][0]["seed_type"] == "hidden_rule_candidate"
    assert examples[1]["dialectic_seed_candidates"][0]["source_engine_name"] == "nonlinear_inspiration_engine"
    assert examples[2]["dialectic_seed_candidates"][0]["source_engine_name"] == "unintelligible_output_analyzer"
    assert examples[3]["dialectic_seed_candidates"][0]["source_engine_name"] == "raw_signal_cartographer"


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("seed_id", ""), "missing_seed_id"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("seed_summary", ""), "missing_seed_summary"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("candidate_claim_or_operator", ""), "missing_candidate_claim_or_operator"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("uncertainty_factors", []), "missing_uncertainty_factors"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("invalidation_signals", []), "missing_invalidation_signals"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("public_claim_status", "public_safe_summary_required"), "seed_marked_public_export_safe"),
        (lambda p: p["generated_counter_signals"].__setitem__(0, {**p["generated_counter_signals"][0], "what_it_challenges": ""}), "missing_counter_signal_challenge_target"),
        (lambda p: p["generated_counter_signals"].__setitem__(0, {**p["generated_counter_signals"][0], "counter_signal_summary": "proof claim"}), "generated_counter_signal_marked_truth_proof_or_discovery"),
        (lambda p: p["generated_counter_signals"].__setitem__(0, {**p["generated_counter_signals"][0], "target_uncertainty": "", "safe_to_reingest_as_metadata": True}), "generated_counter_signal_safe_to_reingest_without_target_uncertainty"),
        (lambda p: p["dialectic_turns"].__setitem__(0, {**p["dialectic_turns"][0], "move_type": ""}), "missing_move_type"),
        (lambda p: p["dialectic_turns"].__setitem__(0, {**p["dialectic_turns"][0], "compressed_lesson": ""}), "missing_compressed_lesson"),
        (lambda p: p["dialectic_turns"].__setitem__(0, {**p["dialectic_turns"][0], "move_summary": "autonomous loop execution"}), "dialectic_turn_implies_autonomous_loop_execution"),
        (lambda p: p.__setitem__("public_claim_status", "public_breakthrough_claim"), "invalid_public_claim_status"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("seed_summary", "AGI consciousness breakthrough"), "forbidden_seed_text"),
        (lambda p: p["boundary_status"].__setitem__("final_answer_generation_authority", True), "boundary_status_grants_final_answer_generation_authority"),
        (lambda p: p["boundary_status"].__setitem__("llm_authority", True), "boundary_status_grants_llm_authority"),
        (lambda p: p["boundary_status"].__setitem__("runtime_authority", True), "boundary_status_grants_runtime_authority"),
        (lambda p: p["boundary_status"].__setitem__("tool_authority", True), "boundary_status_grants_tool_authority"),
        (lambda p: p["boundary_status"].__setitem__("provider_authority", True), "boundary_status_grants_provider_authority"),
        (lambda p: p["boundary_status"].__setitem__("persistence_authority", True), "boundary_status_grants_persistence_authority"),
        (lambda p: p["boundary_status"].__setitem__("behavior_change_authority", True), "boundary_status_grants_behavior_change_authority"),
        (lambda p: p["boundary_status"].__setitem__("behavior_pack_promotion_authority", True), "boundary_status_grants_behavior_pack_promotion_authority"),
        (lambda p: p.__setitem__("denied_authority", {}), "unsafe_or_missing_denied_authority"),
        (lambda p: p.__setitem__("safe_metadata", {}), "unsafe_or_missing_safe_metadata"),
        (lambda p: p["dialectic_seed_candidates"][0].__setitem__("seed_summary", "raw private text: secret"), "forbidden_seed_text"),
        (lambda p: p["dialectic_turns"].__setitem__(0, {**p["dialectic_turns"][0], "move_summary": "hidden prompt and password"}), "forbidden_turn_text"),
    ],
)
def test_negative_fail_closed_cases(mutator, expected_fragment):
    packet = _packet()
    mutator(packet)
    _assert_blocked(packet, expected_fragment)


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (lambda probe: probe.__setitem__("falsification_condition", ""), "missing_falsification_condition"),
        (lambda probe: probe.__setitem__("calibration_prediction", None), "missing_calibration_prediction"),
    ],
)
def test_negative_probe_helper_fail_closed_cases(mutator, expected_fragment):
    packet = _packet(seed_type="operator_candidate", source_engine_name="nonlinear_inspiration_engine", candidate_claim_or_operator="bridge operator")
    probe = build_generated_probe_signal_v1(
        {
            "seed": _first_seed(packet),
            "research_mode": "calibration_replay",
            "probe_goal": "Probe whether the bridge operator survives pressure.",
            "probe_summary": "Calibration-ready probe for the bridge operator.",
            "expected_observation": "bounded bridge behavior",
            "falsification_condition": "if the bridge fails a control case",
            "next_best_observation": "compare with a control case",
        }
    )
    mutator(probe)
    validation = validate_generated_probe_signal_v1(probe)
    assert validation["valid"] is False
    assert any(expected_fragment in item for item in validation["violations"])
