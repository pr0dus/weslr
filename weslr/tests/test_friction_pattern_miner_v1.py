from __future__ import annotations

import ast
import inspect
import importlib
from pathlib import Path

import pytest

from weslr.friction_case_capture import build_initial_renderer_friction_cases_v1
from weslr.friction_replay_harness import build_initial_renderer_friction_replay_v1
from weslr.friction_update_proposal_bridge import build_initial_renderer_friction_update_proposals_v1
from weslr.friction_pattern_miner import (
    FrictionPatternCandidate,
    FrictionPatternPacket,
    ValidationError,
    build_friction_pattern_candidate_v1,
    build_friction_pattern_packet_v1,
    build_initial_renderer_friction_patterns_v1,
    mine_friction_patterns_v1,
    summarize_friction_pattern_packet_v1,
    to_friction_pattern_json_safe_v1,
    validate_friction_pattern_candidate_v1,
    validate_friction_pattern_packet_v1,
)

MODULE_NAME = "weslr.friction_pattern_miner"
MODULE_PATH = Path(__file__).resolve().parents[1] / "friction_pattern_miner.py"


def _module():
    return importlib.import_module(MODULE_NAME)


def _base_candidate(**overrides):
    payload = {
        "pattern_id": "identity_status_directness_pattern",
        "pattern_type": "identity_status_pattern",
        "source_case_ids": ["what_is_weslr_identity_friction"],
        "source_replay_statuses": ["passes_expected"],
        "shared_mismatch_labels": ["answer_shape_mismatch", "wrong_case_priority"],
        "shared_prompt_labels": ["what is weslr", "identity"],
        "shared_replay_labels": ["what is weslr", "identity"],
        "target_update_areas": ["response_method_selector", "cognition_case_registry"],
        "affected_method_ids": ["verified_identity_status_answer_v1", "clarifying_question_answer_v1"],
        "affected_shape_ids": ["direct_bounded_answer", "clarifying_question"],
        "affected_case_ids": ["identity_self_description_case", "clarification_case"],
        "affected_route_ids": ["identity_status_route", "clarification_route"],
        "generalized_failure_summary": "identity/self-description prompts were routed too cautiously into clarification.",
        "generalized_expected_behavior": "direct bounded identity/status response.",
        "proposal_eligibility": "eligible_for_owner_review",
        "minimum_replay_suite_requirements": ["original_friction_cases", "neighbor_prompts", "paraphrase_labels", "boundary_prompts"],
        "confidence_level": "proof_review_required",
        "owner_review_required": True,
        "safe_to_apply_automatically": False,
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "safe_metadata": {"source": "unit_test"},
    }
    payload.update(overrides)
    return build_friction_pattern_candidate_v1(**payload)


def _base_packet(**overrides):
    packet = build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1(), safe_metadata={"source": "unit_test"})
    payload = to_friction_pattern_json_safe_v1(packet)
    payload.update(overrides)
    return payload


def _initial_patterns_by_id():
    return {pattern.pattern_id: pattern for pattern in build_initial_renderer_friction_patterns_v1()}


def test_01_module_imports_safely() -> None:
    module = _module()
    assert hasattr(module, "build_friction_pattern_candidate_v1")
    assert hasattr(module, "build_initial_renderer_friction_patterns_v1")


def test_02_builds_deterministic_pattern_candidate() -> None:
    one = _base_candidate()
    two = _base_candidate()
    assert one == two


def test_03_validates_normal_pattern_candidate() -> None:
    candidate = _base_candidate()
    assert validate_friction_pattern_candidate_v1(candidate) is True


def test_04_validates_normal_pattern_packet() -> None:
    packet = build_friction_pattern_packet_v1([_base_candidate(), _base_candidate(pattern_id="capability_orientation_directness_pattern", pattern_type="capability_orientation_pattern", source_case_ids=["what_can_you_do_now_capability_friction"], shared_mismatch_labels=["missing_capability_orientation", "wrong_case_priority"], shared_prompt_labels=["what can you do", "capability"], shared_replay_labels=["what can you do", "capability"], target_update_areas=["response_method_selector", "cognition_case_registry"], affected_method_ids=["capability_orientation_answer_v1", "clarifying_question_answer_v1"], affected_case_ids=["capability_orientation_case", "clarification_case"], affected_route_ids=["capability_orientation_route", "clarification_route"], generalized_failure_summary="capability/current-ability prompts were routed too cautiously into clarification.", generalized_expected_behavior="capability orientation response.", proposal_eligibility="eligible_for_replay_suite", confidence_level="single_case_low")])
    assert isinstance(packet, FrictionPatternPacket)
    assert validate_friction_pattern_packet_v1(packet) is True


def test_05_json_safe_export_works() -> None:
    candidate = _base_candidate()
    safe = to_friction_pattern_json_safe_v1(candidate)
    assert safe["pattern_id"] == "identity_status_directness_pattern"
    assert isinstance(safe["source_case_ids"], list)


def test_06_summary_includes_pattern_counts_and_confidence_counts() -> None:
    packet = build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1())
    summary = summarize_friction_pattern_packet_v1(packet)
    assert summary["pattern_count"] == 4
    assert summary["pattern_type_counts"]["identity_status_pattern"] == 1
    assert summary["confidence_counts"]


def test_07_initial_renderer_patterns_exist() -> None:
    patterns = build_initial_renderer_friction_patterns_v1()
    assert len(patterns) == 4


def test_08_identity_pattern_exists() -> None:
    patterns = _initial_patterns_by_id()
    assert "identity_status_directness_pattern" in patterns


def test_09_capability_pattern_exists() -> None:
    patterns = _initial_patterns_by_id()
    assert "capability_orientation_directness_pattern" in patterns


def test_10_unknown_term_pattern_exists() -> None:
    patterns = _initial_patterns_by_id()
    assert "unknown_term_friction_preference_pattern" in patterns


def test_11_inactive_capability_boundary_pattern_exists() -> None:
    patterns = _initial_patterns_by_id()
    assert "inactive_capability_boundary_pattern" in patterns


def test_12_one_case_patterns_are_not_overstated_as_high_confidence_proof() -> None:
    for pattern in build_initial_renderer_friction_patterns_v1():
        assert len(pattern.source_case_ids) == 1
        assert pattern.confidence_level in {"single_case_low", "proof_review_required"}
        assert pattern.confidence_level != "proposal_supported_high"


def test_13_proposal_eligible_patterns_require_owner_review() -> None:
    for pattern in build_initial_renderer_friction_patterns_v1():
        if pattern.proposal_eligibility not in {"capture_only", "needs_more_cases", "not_eligible_boundary_risk"}:
            assert pattern.owner_review_required is True


def test_14_no_pattern_claims_learning() -> None:
    for pattern in build_initial_renderer_friction_patterns_v1():
        assert pattern.learning_claimed is False


def test_15_no_pattern_is_auto_applied() -> None:
    for pattern in build_initial_renderer_friction_patterns_v1():
        assert pattern.safe_to_apply_automatically is False


def test_16_no_proposal_is_created() -> None:
    packet = build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1())
    assert packet.proposal_created is False


def test_17_no_promotion_is_performed() -> None:
    packet = build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1())
    assert packet.promotion_performed is False


def test_18_runtime_authority_true_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["runtime_authority"] = True
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_19_writes_state_true_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["writes_state"] = True
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_20_model_provider_used_true_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["model_provider_used"] = True
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_21_learning_claimed_true_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["learning_claimed"] = True
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_22_safe_to_apply_automatically_true_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["safe_to_apply_automatically"] = True
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_23_proposal_created_true_fails_validation() -> None:
    packet = _base_packet(proposal_created=True)
    with pytest.raises(ValidationError):
        validate_friction_pattern_packet_v1(packet)


def test_24_promotion_performed_true_fails_validation() -> None:
    packet = _base_packet(promotion_performed=True)
    with pytest.raises(ValidationError):
        validate_friction_pattern_packet_v1(packet)


def test_25_raw_prompt_field_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["raw_prompt"] = "secret prompt"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_26_raw_answer_field_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["raw_answer"] = "secret answer"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_27_transcript_field_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["transcript"] = "secret transcript"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_28_unknown_pattern_type_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["pattern_type"] = "unknown_pattern_type"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_29_unknown_confidence_level_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["confidence_level"] = "unknown_confidence"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_30_unknown_proposal_eligibility_fails_validation() -> None:
    candidate = to_friction_pattern_json_safe_v1(_base_candidate())
    candidate["proposal_eligibility"] = "unknown_eligibility"
    with pytest.raises(ValidationError):
        validate_friction_pattern_candidate_v1(candidate)


def test_31_duplicate_pattern_ids_fail_packet_validation() -> None:
    packet = to_friction_pattern_json_safe_v1(build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1()))
    packet["patterns"][1]["pattern_id"] = packet["patterns"][0]["pattern_id"]
    with pytest.raises(ValidationError):
        validate_friction_pattern_packet_v1(packet)


def test_32_packet_count_mismatch_fails_validation() -> None:
    packet = to_friction_pattern_json_safe_v1(build_friction_pattern_packet_v1(build_initial_renderer_friction_patterns_v1()))
    packet["pattern_count"] += 1
    with pytest.raises(ValidationError):
        validate_friction_pattern_packet_v1(packet)


def test_33_mining_from_initial_friction_cases_is_deterministic() -> None:
    cases = build_initial_renderer_friction_cases_v1()
    replay_packet = build_initial_renderer_friction_replay_v1()
    proposal_packet = build_initial_renderer_friction_update_proposals_v1()
    one = mine_friction_patterns_v1(cases, replay_packet, proposal_packet)
    two = mine_friction_patterns_v1(cases, replay_packet, proposal_packet)
    assert one == two


def test_34_mining_from_replay_packet_preserves_replay_statuses() -> None:
    cases = build_initial_renderer_friction_cases_v1()
    replay_packet = build_initial_renderer_friction_replay_v1()
    patterns = mine_friction_patterns_v1(cases, replay_packet=replay_packet)
    assert all(pattern.source_replay_statuses == ("passes_expected",) for pattern in patterns)


def test_35_mining_from_proposal_packet_preserves_target_update_areas() -> None:
    cases = build_initial_renderer_friction_cases_v1()
    proposal_packet = build_initial_renderer_friction_update_proposals_v1()
    patterns = mine_friction_patterns_v1(cases, proposal_packet=proposal_packet)
    target_map = {pattern.pattern_id: pattern.target_update_areas for pattern in patterns}
    assert target_map["identity_status_directness_pattern"] == ("response_method_selector", "cognition_case_registry", "no_model_bounded_renderer")
    assert target_map["capability_orientation_directness_pattern"] == ("response_method_selector", "cognition_case_registry")
    assert target_map["unknown_term_friction_preference_pattern"] == ("unknown_prompt_friction_router", "response_method_selector")
    assert target_map["inactive_capability_boundary_pattern"] == ("response_method_selector", "no_model_bounded_renderer")


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_36_to_39_module_source_does_not_import_or_call_prohibited_modules(module_name: str) -> None:
    module = _module()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imports: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                called_names.add(func.attr)
    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
    assert module_name not in called_names
