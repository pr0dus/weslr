from __future__ import annotations

import ast
import importlib
import inspect

import pytest

from weslr.friction_case_capture import build_initial_renderer_friction_cases_v1
from weslr.friction_replay_harness import build_initial_renderer_friction_replay_v1
from weslr.friction_update_proposal_bridge import (
    FrictionUpdateProposalPacket,
    ValidationError,
    build_friction_update_proposal_packet_v1,
    build_friction_update_proposal_v1,
    build_friction_update_proposals_from_replay_v1,
    build_initial_renderer_friction_update_proposals_v1,
    summarize_friction_update_proposal_packet_v1,
    summarize_friction_update_proposal_v1,
    to_friction_update_proposal_json_safe_v1,
    validate_friction_update_proposal_packet_v1,
    validate_friction_update_proposal_v1,
)


def _base_proposal(**overrides):
    payload = {
        "proposal_id": "selector_priority_update__what_is_weslr_identity_friction",
        "source_case_id": "what_is_weslr_identity_friction",
        "source_replay_status": "fails_expected",
        "proposal_type": "selector_priority_update",
        "target_update_area": ["response_method_selector", "cognition_case_registry"],
        "problem_summary": "Identity turns are falling into generic clarification.",
        "expected_behavior_summary": "Prefer direct bounded identity/status routing.",
        "proposed_rule_change": "Prioritize identity self-description over clarification.",
        "affected_method_ids": ["verified_identity_status_answer_v1", "clarifying_question_answer_v1"],
        "affected_shape_ids": ["direct_bounded_answer", "clarifying_question"],
        "affected_case_ids": ["identity_self_description_case", "clarification_needed_case"],
        "affected_route_ids": ["identity_status_route", "clarification_route"],
        "replay_labels": ["what weslr", "what are you", "identity", "status"],
        "regression_labels": [
            "what are you",
            "are you an llm",
            "are you agi",
            "what can you do",
            "can I upload files",
            "can I pay now",
            "marketplace active",
            "unknown term",
            "new word",
            "needs evidence",
            "unsafe request",
            "memory question",
        ],
        "risk_labels": ["overfit_to_single_phrase", "generic_clarification_regression", "route_priority_drift"],
        "approval_status": "proposal_created",
        "promotion_status": "not_promoted",
        "owner_review_required": True,
        "safe_to_apply_automatically": False,
        "learning_claimed": False,
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "safe_metadata": {"source": "unit_test"},
    }
    payload.update(overrides)
    return build_friction_update_proposal_v1(**payload)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.friction_update_proposal_bridge")
    assert hasattr(module, "build_friction_update_proposal_v1")
    assert hasattr(module, "build_initial_renderer_friction_update_proposals_v1")


def test_builds_deterministic_proposal() -> None:
    proposal_one = _base_proposal()
    proposal_two = _base_proposal()
    assert proposal_one == proposal_two


def test_valid_proposal_validates() -> None:
    proposal = _base_proposal()
    assert validate_friction_update_proposal_v1(proposal) is True


def test_valid_proposal_packet_validates() -> None:
    proposals = build_initial_renderer_friction_update_proposals_v1()
    packet = build_friction_update_proposal_packet_v1(proposals)
    assert isinstance(packet, FrictionUpdateProposalPacket)
    assert validate_friction_update_proposal_packet_v1(packet) is True


def test_json_safe_export_works() -> None:
    proposal = _base_proposal()
    safe = to_friction_update_proposal_json_safe_v1(proposal)
    assert safe["proposal_id"] == "selector_priority_update__what_is_weslr_identity_friction"
    assert isinstance(safe["target_update_area"], list)


def test_summary_includes_counts_and_target_areas() -> None:
    packet = build_friction_update_proposal_packet_v1(build_initial_renderer_friction_update_proposals_v1())
    summary = summarize_friction_update_proposal_packet_v1(packet)
    assert summary["proposal_count"] == 4
    assert summary["proposal_type_counts"]["selector_priority_update"] >= 1
    assert summary["target_update_area_counts"]["response_method_selector"] >= 3


def test_initial_four_proposals_exist() -> None:
    proposals = build_initial_renderer_friction_update_proposals_v1()
    assert len(proposals) == 4
    assert {proposal.source_case_id for proposal in proposals} == {
        "what_is_weslr_identity_friction",
        "what_can_you_do_now_capability_friction",
        "unknown_word_blorvatek_friction",
        "upload_files_now_boundary_friction",
    }


def test_identity_friction_proposal_targets_selector_and_case_priority() -> None:
    proposal = next(item for item in build_initial_renderer_friction_update_proposals_v1() if item.source_case_id == "what_is_weslr_identity_friction")
    assert proposal.proposal_type in {"selector_priority_update", "case_priority_update"}
    assert "response_method_selector" in proposal.target_update_area
    assert "cognition_case_registry" in proposal.target_update_area


def test_capability_friction_proposal_targets_capability_orientation() -> None:
    proposal = next(item for item in build_initial_renderer_friction_update_proposals_v1() if item.source_case_id == "what_can_you_do_now_capability_friction")
    assert proposal.proposal_type == "case_priority_update"
    assert "response_method_selector" in proposal.target_update_area
    assert "cognition_case_registry" in proposal.target_update_area
    assert "capability_orientation_answer_v1" in proposal.affected_method_ids


def test_unknown_word_proposal_targets_unknown_friction_routing() -> None:
    proposal = next(item for item in build_initial_renderer_friction_update_proposals_v1() if item.source_case_id == "unknown_word_blorvatek_friction")
    assert proposal.proposal_type == "unknown_friction_routing_update"
    assert "unknown_prompt_friction_router" in proposal.target_update_area
    assert "response_method_selector" in proposal.target_update_area


def test_upload_boundary_proposal_targets_capability_boundary_behavior() -> None:
    proposal = next(item for item in build_initial_renderer_friction_update_proposals_v1() if item.source_case_id == "upload_files_now_boundary_friction")
    assert proposal.proposal_type == "boundary_policy_update"
    assert "response_method_selector" in proposal.target_update_area
    assert "no_model_bounded_renderer" in proposal.target_update_area


@pytest.mark.parametrize("proposal", build_initial_renderer_friction_update_proposals_v1())
def test_no_proposal_claims_learning(proposal) -> None:
    assert proposal.learning_claimed is False


@pytest.mark.parametrize("proposal", build_initial_renderer_friction_update_proposals_v1())
def test_no_proposal_is_auto_applied(proposal) -> None:
    assert proposal.safe_to_apply_automatically is False


@pytest.mark.parametrize("proposal", build_initial_renderer_friction_update_proposals_v1())
def test_all_proposals_require_owner_review(proposal) -> None:
    assert proposal.owner_review_required is True


@pytest.mark.parametrize("proposal", build_initial_renderer_friction_update_proposals_v1())
def test_no_proposal_is_promoted(proposal) -> None:
    assert proposal.promotion_status == "not_promoted"


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("raw_prompt", "secret prompt"),
        ("raw_answer", "secret answer"),
        ("transcript_text", "secret transcript"),
    ],
)
def test_raw_fields_fail_validation(field_name, value) -> None:
    payload = to_friction_update_proposal_json_safe_v1(_base_proposal())
    payload[field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_update_proposal_v1(payload)


@pytest.mark.parametrize("field_name", ["learning_claimed", "safe_to_apply_automatically", "runtime_authority", "writes_state", "model_provider_used"])
def test_boolean_drift_fails_validation(field_name) -> None:
    payload = to_friction_update_proposal_json_safe_v1(_base_proposal())
    payload[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_update_proposal_v1(payload)


@pytest.mark.parametrize("field_name, value", [("proposal_type", "unknown_type"), ("target_update_area", ["unknown_area"]), ("approval_status", "unknown_status"), ("promotion_status", "unknown_promotion")])
def test_unknown_enums_fail_validation(field_name, value) -> None:
    payload = to_friction_update_proposal_json_safe_v1(_base_proposal())
    payload[field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_update_proposal_v1(payload)


def test_duplicate_proposal_ids_fail_packet_validation() -> None:
    packet = to_friction_update_proposal_json_safe_v1(build_friction_update_proposal_packet_v1(build_initial_renderer_friction_update_proposals_v1()))
    packet["proposals"][1]["proposal_id"] = packet["proposals"][0]["proposal_id"]
    with pytest.raises(ValidationError):
        validate_friction_update_proposal_packet_v1(packet)


def test_proposal_from_replay_packet_preserves_replay_status() -> None:
    replay_packet = build_initial_renderer_friction_replay_v1()
    proposals = build_friction_update_proposals_from_replay_v1(replay_packet)
    replay_status_by_case = {result.case_id: result.match_status for result in replay_packet.results}
    for proposal in proposals:
        assert proposal.source_replay_status == replay_status_by_case[proposal.source_case_id]


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_module_source_does_not_import_prohibited_modules(module_name) -> None:
    import weslr.friction_update_proposal_bridge as module

    tree = ast.parse(inspect.getsource(module))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
