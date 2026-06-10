from __future__ import annotations

from copy import deepcopy

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.suggestion_store_update_packet import (
    build_initial_suggestion_store_update_examples_v1,
    build_suggestion_store_candidate_ref_v1,
    build_suggestion_store_update_action_v1,
    build_suggestion_store_update_packet_v1,
    summarize_suggestion_store_update_packet_v1,
    to_suggestion_store_update_json_safe_v1,
    validate_suggestion_store_update_packet_v1,
)


def _candidate(candidate_status: str = "watch", source_engine_name: str = "perspicuity_scorer", **overrides):
    payload = {
        "candidate_id": f"candidate-{source_engine_name}-{candidate_status}",
        "source_engine_name": source_engine_name,
        "source_run_id": f"run-{source_engine_name}-{candidate_status}",
        "candidate_type": f"{source_engine_name}_candidate",
        "candidate_summary": f"{source_engine_name} {candidate_status} candidate.",
        "candidate_status": candidate_status,
        "candidate_scope": "metadata-only scope",
        "public_claim_status": "internal_candidate_only",
        "uncertainty_factors": ["candidate remains provisional"],
        "invalidation_signals": ["not yet invalidated"],
    }
    payload.update(overrides)
    return build_suggestion_store_candidate_ref_v1(payload)


def _raw_candidate(candidate_status: str = "watch", source_engine_name: str = "perspicuity_scorer", **overrides):
    payload = {
        "candidate_id": f"candidate-{source_engine_name}-{candidate_status}",
        "source_engine_name": source_engine_name,
        "source_run_id": f"run-{source_engine_name}-{candidate_status}",
        "candidate_type": f"{source_engine_name}_candidate",
        "candidate_summary": f"{source_engine_name} {candidate_status} candidate.",
        "candidate_status": candidate_status,
        "candidate_scope": "metadata-only scope",
        "public_claim_status": "internal_candidate_only",
        "uncertainty_factors": ["candidate remains provisional"],
        "invalidation_signals": ["not yet invalidated"],
    }
    payload.update(overrides)
    return payload


def _action(action_type: str = "update_status", candidate_id: str = "candidate-perspicuity_scorer-watch", **overrides):
    payload = {
        "update_action_id": f"update-{candidate_id}-{action_type}",
        "candidate_id": candidate_id,
        "action_type": action_type,
        "action_reason": f"Internal metadata-only {action_type} for candidate review.",
        "previous_status": "watch",
        "next_status": "watch",
        "linked_probe_ref": "",
        "linked_pressure_test_ref": "",
        "linked_calibration_record_ref": "",
        "linked_perspicuity_scorecard_ref": "",
        "operator_review_required": action_type != "no_op",
        "storage_write_authorized": False,
        "behavior_change_authorized": False,
        "public_claim_authorized": False,
    }
    payload.update(overrides)
    return build_suggestion_store_update_action_v1(payload)


def _raw_action(action_type: str = "update_status", candidate_id: str = "candidate-perspicuity_scorer-watch", **overrides):
    payload = {
        "update_action_id": f"update-{candidate_id}-{action_type}",
        "candidate_id": candidate_id,
        "action_type": action_type,
        "action_reason": f"Internal metadata-only {action_type} for candidate review.",
        "previous_status": "watch",
        "next_status": "watch",
        "linked_probe_ref": "",
        "linked_pressure_test_ref": "",
        "linked_calibration_record_ref": "",
        "linked_perspicuity_scorecard_ref": "",
        "operator_review_required": action_type != "no_op",
        "storage_write_authorized": False,
        "behavior_change_authorized": False,
        "public_claim_authorized": False,
    }
    payload.update(overrides)
    return payload


def _packet(
    action_type: str = "update_status",
    candidate_status: str = "watch",
    previous_status: str = "new",
    next_status: str = "watch",
    candidate_overrides: dict | None = None,
    action_overrides: dict | None = None,
    packet_overrides: dict | None = None,
):
    candidate = _candidate(candidate_status=candidate_status, **(candidate_overrides or {}))
    action_payload = {
        "candidate_id": candidate["candidate_id"],
        "action_type": action_type,
        "previous_status": previous_status,
        "next_status": next_status,
    }
    action_payload.update(action_overrides or {})
    action = _action(**action_payload)
    payload = {
        "source_run_id": candidate["source_run_id"],
        "research_mode": "synthetic_test",
        "input_artifact_ref": f"artifact:{candidate['candidate_id']}",
        "input_artifact_type": "suggestion-store-update",
        "input_summary": f"Suggestion-store update packet for {candidate['candidate_id']}.",
        "candidate_refs": [candidate],
        "update_actions": [action],
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "safe_metadata": {"safe": True, "metadata_only": True, "json_safe": True, "no_runtime_wiring": True},
    }
    payload.update(packet_overrides or {})
    return build_suggestion_store_update_packet_v1(payload)


def _raw_packet(**overrides):
    packet = deepcopy(_packet())
    packet.update(overrides)
    return packet


def _assert_valid(packet):
    validation = validate_suggestion_store_update_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "suggestion_store_update_packet"
    assert protocol.validate_cognitive_research_run_v1(packet)["blocked"] is False
    return validation


@pytest.mark.parametrize(
    "action_type, candidate_status, previous_status, next_status, action_overrides",
    [
        ("add_candidate", "new", "unknown", "new", {}),
        ("update_status", "watch", "new", "watch", {}),
        ("update_status", "probe", "watch", "probe", {}),
        ("update_status", "pressure_test", "probe", "pressure_test", {}),
        ("link_calibration_record", "calibrate", "calibrate", "calibrate", {"linked_calibration_record_ref": "calibration:forecast-001"}),
        ("link_perspicuity_scorecard", "watch", "watch", "watch", {"linked_perspicuity_scorecard_ref": "scorecard:perspicuity-001"}),
        ("archive_candidate", "archive", "watch", "archive", {}),
        ("block_candidate", "blocked", "probe", "blocked", {}),
        ("recommend_next_internal_step", "promote_to_next_internal_step", "watch", "promote_to_next_internal_step", {}),
        ("no_op", "watch", "unknown", "unknown", {"operator_review_required": False}),
    ],
)
def test_positive_update_actions_pass(action_type, candidate_status, previous_status, next_status, action_overrides):
    packet = _packet(
        action_type=action_type,
        candidate_status=candidate_status,
        previous_status=previous_status,
        next_status=next_status,
        action_overrides=action_overrides,
    )
    validation = _assert_valid(packet)
    assert validation["engine_name"] == "suggestion_store_update_packet"
    assert packet["candidate_refs"][0]["candidate_status"] == candidate_status
    assert packet["update_actions"][0]["action_type"] == action_type


def test_valid_packet_references_perspicuity_scorecard_without_trusting_it_as_truth():
    packet = _packet(
        action_type="link_perspicuity_scorecard",
        candidate_status="watch",
        previous_status="watch",
        next_status="watch",
        action_overrides={"linked_perspicuity_scorecard_ref": "scorecard:perspicuity-001"},
    )
    validation = _assert_valid(packet)
    assert packet["update_actions"][0]["linked_perspicuity_scorecard_ref"] == "scorecard:perspicuity-001"
    assert packet["public_claim_authorized"] is False
    assert packet["operator_review_required"] is True
    assert validation["packet"]["safe_metadata"]["no_runtime_wiring"] is True


def test_valid_packet_references_rule_pressure_test_without_executing_it():
    packet = _packet(
        action_type="link_pressure_test",
        candidate_status="pressure_test",
        previous_status="pressure_test",
        next_status="pressure_test",
        action_overrides={"linked_pressure_test_ref": "pressure:rule-pressure-001"},
    )
    _assert_valid(packet)
    assert packet["update_actions"][0]["linked_pressure_test_ref"] == "pressure:rule-pressure-001"
    assert packet["storage_write_authorized"] is False
    assert packet["behavior_change_authorized"] is False


def test_valid_packet_references_calibration_record_without_mutating_confidence_globally():
    packet = _packet(
        action_type="link_calibration_record",
        candidate_status="calibrate",
        previous_status="calibrate",
        next_status="calibrate",
        action_overrides={"linked_calibration_record_ref": "calibration:forecast-001"},
    )
    _assert_valid(packet)
    assert packet["update_actions"][0]["linked_calibration_record_ref"] == "calibration:forecast-001"
    assert packet["memory_mutation_authorized"] is False
    assert packet["project_mutation_authorized"] is False


def test_valid_packet_validates_as_metadata_only_and_protocol_compatible():
    packet = _packet()
    validation = validate_suggestion_store_update_packet_v1(packet)
    assert validation["blocked"] is False
    assert protocol.validate_cognitive_research_run_v1(packet)["blocked"] is False
    assert validation["classification"] == "suggestion_store_update_packet"
    assert packet["engine_family"] == "candidate_store_update"


def test_json_safe_copy_strips_unsafe_raw_fields():
    packet = _packet()
    packet["raw_private_text"] = "secret"
    packet["candidate_refs"][0]["hidden_prompt"] = "hidden"
    packet["update_actions"][0]["raw_response"] = "response"
    safe = to_suggestion_store_update_json_safe_v1(packet)
    assert "raw_private_text" not in safe
    assert "hidden_prompt" not in safe["candidate_refs"][0]
    assert "raw_response" not in safe["update_actions"][0]


def test_summary_is_concise_and_private_text_safe():
    packet = _packet()
    summary = summarize_suggestion_store_update_packet_v1(packet)
    assert len(summary["summary_text"]) <= 320
    assert "secret" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_examples_include_required_named_examples():
    examples = build_initial_suggestion_store_update_examples_v1()
    assert len(examples) == 4
    sources = [example["candidate_refs"][0]["source_engine_name"] for example in examples]
    assert sources == [
        "perspicuity_scorer",
        "rule_pressure_engine",
        "dialectic_generator_loop",
        "forecast_calibration_bridge",
    ]


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        (lambda p: p.__setitem__("packet_id", ""), "missing_packet_id"),
        (lambda p: p["candidate_refs"][0].__setitem__("candidate_id", ""), "missing_candidate_id"),
        (lambda p: p.__setitem__("source_run_id", ""), "missing_source_run_id"),
        (lambda p: p["candidate_refs"][0].__setitem__("candidate_summary", ""), "missing_candidate_summary"),
        (lambda p: p["candidate_refs"][0].__setitem__("uncertainty_factors", []), "missing_uncertainty_factors"),
        (lambda p: p["candidate_refs"][0].__setitem__("invalidation_signals", []), "missing_invalidation_signals"),
        (lambda p: p["candidate_refs"][0].__setitem__("candidate_status", "future_state"), "invalid_candidate_status"),
        (lambda p: p["candidate_refs"][0].__setitem__("public_claim_status", "public_safe_summary_required"), "candidate_marked_public_or_export_safe"),
        (lambda p: p["update_actions"][0].__setitem__("action_type", "future_action"), "invalid_action_type"),
        (lambda p: p["update_actions"][0].__setitem__("action_reason", ""), "missing_action_reason"),
        (lambda p: p["update_actions"][0].update({"action_type": "update_status", "previous_status": "", "next_status": ""}), "status_update_without_previous_or_next_status"),
        (lambda p: p["update_actions"][0].update({"action_type": "link_probe", "linked_probe_ref": ""}), "missing_linked_probe_ref"),
        (lambda p: p.__setitem__("storage_write_authorized", True), "storage_write_authorized"),
        (lambda p: p.__setitem__("memory_mutation_authorized", True), "memory_mutation_authorized"),
        (lambda p: p.__setitem__("project_mutation_authorized", True), "project_mutation_authorized"),
        (lambda p: p.__setitem__("behavior_change_authorized", True), "behavior_change_authorized"),
        (lambda p: p.__setitem__("behavior_promotion_authorized", True), "behavior_promotion_authorized"),
        (lambda p: p.__setitem__("public_claim_authorized", True), "public_claim_authorized"),
        (lambda p: p.__setitem__("compressed_lesson", "commit to store"), "update_packet_treated_as_persistence_or_write"),
        (lambda p: p.__setitem__("compressed_lesson", "public breakthrough claim"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "AGI intelligence claim"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "final answer authority"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "LLM authority"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "safety gate replacement"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "runtime provider tool persistence"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", ".weslr"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("compressed_lesson", "live ingestion network"), "forbidden_update_packet_text"),
        (lambda p: p.__setitem__("denied_authority", None), "missing_denied_authority"),
        (lambda p: p.__setitem__("safe_metadata", {"safe": False}), "unsafe_safe_metadata"),
        (lambda p: p["candidate_refs"][0].__setitem__("candidate_summary", "raw private text"), "forbidden_candidate_text"),
        (lambda p: p["update_actions"][0].__setitem__("action_reason", "hidden prompt secret"), "forbidden_update_action_text"),
    ],
)
def test_negative_mutations_fail_closed(mutation, expected_label):
    packet = _raw_packet()
    mutation(packet)
    validation = validate_suggestion_store_update_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(expected_label == label or expected_label in label for label in validation["blocked_labels"])
