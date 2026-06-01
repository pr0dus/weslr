from __future__ import annotations

import inspect
import json
import sys

import pytest

import weslr.neurosymbolic_algorithmic_inference_engine as mod


def _example(example_id: str):
    return next(item for item in mod.build_initial_neurosymbolic_inference_examples_v1() if item.inference_packet_id == example_id)


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "neurosymbolic_algorithmic_inference_engine_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_module_does_not_reference_protected_runtime_files() -> None:
    source = inspect.getsource(mod)
    assert "chat_responder.py" not in source
    assert "weslr.chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source


def test_builds_deterministic_inference_packet() -> None:
    packet_a = mod.build_inference_packet_v1(
        request_id="req_v1",
        subject="subject_v1",
        inference_mode="constraint_check",
        assumptions=["a"],
        missing_inputs=["b"],
    )
    packet_b = mod.build_inference_packet_v1(
        request_id="req_v1",
        subject="subject_v1",
        inference_mode="constraint_check",
        assumptions=["a"],
        missing_inputs=["b"],
    )
    assert packet_a == packet_b
    assert packet_a.safe_metadata["metadata_only"] is True


def test_validates_normal_inference_packet() -> None:
    packet = mod.build_inference_packet_v1(
        request_id="valid_v1",
        subject="valid_subject",
        inference_mode="source_evidence_linking",
        source_provenance_refs=["source:one"],
        assumptions=["safe metadata only"],
    )
    assert mod.validate_inference_packet_v1(packet) is True


def test_apply_inference_constraints_preserves_hard_and_soft_distinction() -> None:
    packet = mod.build_inference_packet_v1(
        request_id="constraints_v1",
        subject="constraints_subject",
        inference_mode="dependency_resolution",
        missing_inputs=["owner_priority"],
        confidence_label="unknown_confidence",
        authority_boundary="unknown_authority_boundary",
    )
    constrained = mod.apply_inference_constraints_v1(packet)
    kinds = {item["constraint_kind"] for item in constrained.constraints_checked}
    assert "hard" in kinds
    assert "soft" in kinds
    assert any(item["constraint_status"] == "branch_required" for item in constrained.constraints_checked)


def test_derives_candidates_without_authority() -> None:
    packet = _example("unknown_engine_finding_to_missing_bridge_lane")
    candidates = mod.derive_inference_candidates_v1(packet)
    assert candidates
    assert all(candidate["action_authority_granted"] is False for candidate in candidates)
    assert all(candidate["runtime_authority"] is False for candidate in candidates)


def test_rejects_unsupported_candidates_with_reasons() -> None:
    packet = _example("public_claim_rejected_not_public_safe")
    rejected = mod.reject_unsupported_candidates_v1(packet)
    assert rejected
    assert any("not public safe" in item["reason"] for item in rejected)


def test_summarizes_packet() -> None:
    packet = _example("energy_recommendation_blocked_stale_battery_soc")
    summary = mod.summarize_inference_packet_v1(packet)
    assert summary.summary_type == mod.SUMMARY_TYPE_V1
    assert summary.inference_packet_id == packet.inference_packet_id
    assert summary.recommendation_only is True


def test_json_safe_export_works() -> None:
    packet = _example("forecast_error_wrong_grid_zone_trace")
    safe = mod.to_neurosymbolic_inference_json_safe_v1(packet)
    json.dumps(safe)
    assert safe["inference_packet_id"] == packet.inference_packet_id


def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_neurosymbolic_inference_examples_v1()
    ids = {item.inference_packet_id for item in examples}
    assert len(examples) == 10
    assert "energy_recommendation_blocked_stale_battery_soc" in ids
    assert "price_vs_carbon_owner_priority_missing_branch" in ids
    assert "forecast_error_wrong_grid_zone_trace" in ids
    assert "artifact_generation_blocked_missing_validation_runner" in ids
    assert "public_claim_rejected_not_public_safe" in ids
    assert "memory_answer_blocked_missing_source_scope" in ids
    assert "llm_candidate_rejected_no_provenance" in ids
    assert "unknown_engine_finding_to_missing_bridge_lane" in ids
    assert "scenario_branch_from_unresolved_conflict" in ids
    assert "repeated_forecast_errors_behavior_pack_proposal_only" in ids


def test_stale_battery_soc_example_blocks_energy_recommendation() -> None:
    packet = _example("energy_recommendation_blocked_stale_battery_soc")
    assert packet.authority_boundary == "blocked_by_missing_input"
    assert packet.missing_inputs == ["fresh_battery_soc"]
    assert "battery_soc" in packet.recommended_next_check


def test_price_vs_carbon_example_branches_when_owner_priority_missing() -> None:
    packet = _example("price_vs_carbon_owner_priority_missing_branch")
    assert packet.authority_boundary == "branch_required"
    assert any(item["candidate_status"] == "branch_required" for item in packet.derived_candidates)


def test_wrong_grid_zone_example_traces_forecast_error_assumption() -> None:
    packet = _example("forecast_error_wrong_grid_zone_trace")
    assert packet.forecast_error_refs == ["forecast_error:wrong_grid_zone_trace"]
    assert any("grid zone" in note.lower() for note in packet.uncertainty_notes)


def test_artifact_generation_example_blocks_on_validation_runner_missing() -> None:
    packet = _example("artifact_generation_blocked_missing_validation_runner")
    assert packet.authority_boundary == "blocked_by_missing_input"
    assert packet.missing_inputs == ["validation_runner"]


def test_public_claim_example_rejects_not_public_safe_claim() -> None:
    packet = _example("public_claim_rejected_not_public_safe")
    assert packet.authority_boundary == "blocked_by_public_claim_boundary"
    assert any(item["candidate_status"] == "candidate_rejected" for item in packet.rejected_candidates)


def test_memory_example_blocks_missing_source_scope() -> None:
    packet = _example("memory_answer_blocked_missing_source_scope")
    assert packet.authority_boundary == "blocked_by_privacy_boundary"
    assert packet.memory_refs == ["memory:scope:missing"]


def test_llm_candidate_example_rejects_no_provenance_authority_claim() -> None:
    packet = _example("llm_candidate_rejected_no_provenance")
    assert packet.authority_boundary == "blocked_by_authority_boundary"
    assert any("provenance" in item["reason"].lower() for item in packet.rejected_candidates)


def test_unknown_engine_finding_becomes_missing_bridge_lane_not_runtime_instruction() -> None:
    packet = _example("unknown_engine_finding_to_missing_bridge_lane")
    assert packet.inference_mode == "unknown_inference_mode"
    assert packet.runtime_authority is False
    assert packet.recommended_next_check.lower().startswith("design the missing bridge lane")
    assert any(item["candidate_label"] == "missing_bridge_lane" for item in packet.derived_candidates)


def test_scenario_branch_from_unresolved_conflict_creates_scenario_branch() -> None:
    packet = _example("scenario_branch_from_unresolved_conflict")
    assert packet.authority_boundary == "branch_required"
    assert any(item["candidate_status"] == "branch_required" for item in packet.derived_candidates)


def test_repeated_forecast_errors_create_behavior_pack_proposal_only() -> None:
    packet = _example("repeated_forecast_errors_behavior_pack_proposal_only")
    assert packet.authority_boundary == "candidate_only"
    assert any(item["candidate_label"] == "behavior_pack_proposal" for item in packet.derived_candidates)
    assert packet.learning_claimed is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_grants_action_authority(packet) -> None:
    assert packet.action_authority_granted is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_has_runtime_authority(packet) -> None:
    assert packet.runtime_authority is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_writes_state(packet) -> None:
    assert packet.writes_state is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_calls_model_provider(packet) -> None:
    assert packet.model_provider_used is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_allows_public_claim(packet) -> None:
    assert packet.public_claim_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_allows_proof_claim(packet) -> None:
    assert packet.proof_claim_allowed is False


@pytest.mark.parametrize("packet", mod.build_initial_neurosymbolic_inference_examples_v1())
def test_no_initial_example_claims_autonomous_learning(packet) -> None:
    assert packet.learning_claimed is False


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("inference_mode", "totally_unknown_mode", "unknown_inference_mode"),
])
def test_validation_fails_unknown_inference_mode(field_name: str, field_value: str, expected_error: str) -> None:
    packet = mod.build_initial_neurosymbolic_inference_examples_v1()[0]
    payload = mod.to_neurosymbolic_inference_json_safe_v1(packet)
    payload[field_name] = field_value
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("confidence_label", "super_confident", "unknown_confidence_label"),
])
def test_validation_fails_unknown_confidence_label(field_name: str, field_value: str, expected_error: str) -> None:
    packet = mod.build_initial_neurosymbolic_inference_examples_v1()[0]
    payload = mod.to_neurosymbolic_inference_json_safe_v1(packet)
    payload[field_name] = field_value
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("authority_boundary", "totally_unknown_boundary", "unknown_authority_boundary"),
])
def test_validation_fails_unknown_authority_boundary(field_name: str, field_value: str, expected_error: str) -> None:
    packet = mod.build_initial_neurosymbolic_inference_examples_v1()[0]
    payload = mod.to_neurosymbolic_inference_json_safe_v1(packet)
    payload[field_name] = field_value
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("field_name, expected_error", [
    ("action_authority_granted", "action_authority_granted_true"),
    ("runtime_authority", "runtime_authority_true"),
    ("writes_state", "writes_state_true"),
    ("model_provider_used", "model_provider_used_true"),
    ("public_claim_allowed", "public_claim_allowed_true"),
    ("proof_claim_allowed", "proof_claim_allowed_true"),
    ("learning_claimed", "learning_claimed_true"),
])
def test_validation_fails_forbidden_authority_flags(field_name: str, expected_error: str) -> None:
    packet = mod.build_initial_neurosymbolic_inference_examples_v1()[0]
    payload = mod.to_neurosymbolic_inference_json_safe_v1(packet)
    payload[field_name] = True
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("bad_payload", [
    {"safe_metadata": {"hidden_prompt": "x"}},
    {"safe_metadata": {"raw_private": "x"}},
    {"safe_metadata": {"secret": "x"}},
    {"safe_metadata": {"token": "x"}},
    {"safe_metadata": {"api_key": "x"}},
    {"safe_metadata": {"credential": "x"}},
    {"safe_metadata": {"password": "x"}},
])
def test_validation_fails_hidden_prompt_raw_private_secret_and_key_fields(bad_payload: dict[str, dict[str, str]]) -> None:
    payload = mod.to_neurosymbolic_inference_json_safe_v1(mod.build_initial_neurosymbolic_inference_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], **bad_payload["safe_metadata"]}
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match="hidden_prompt_or_raw_private_field"):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("marker", ["AGI", "consciousness", "sentience", "Turing", "certification"])
def test_validation_fails_agi_consciousness_turing_certification_marker(marker: str) -> None:
    payload = mod.to_neurosymbolic_inference_json_safe_v1(mod.build_initial_neurosymbolic_inference_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": marker}
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_inference_packet_v1(mutated)


@pytest.mark.parametrize("claim", ["public readiness", "proof certainty", "truth certainty", "autonomous learning"])
def test_validation_fails_proof_truth_certainty_and_autonomous_learning_claims(claim: str) -> None:
    payload = mod.to_neurosymbolic_inference_json_safe_v1(mod.build_initial_neurosymbolic_inference_examples_v1()[0])
    payload["safe_metadata"] = {**payload["safe_metadata"], "claim": claim}
    mutated = mod.NeurosymbolicInferencePacket(**payload)
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_inference_packet_v1(mutated)
