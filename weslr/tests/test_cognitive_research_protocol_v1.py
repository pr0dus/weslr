from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.cognitive_research_protocol as protocol
from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1,
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1,
    ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_GAP_CARD_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_generated_source_signal_metadata_v1,
    build_initial_cognitive_research_examples_v1,
    build_nonlinear_resonance_candidate_v1,
    build_perspicuity_score_metadata_v1,
    build_rule_pressure_test_metadata_v1,
    build_source_signal_metadata_v1,
    classify_cognitive_research_engine_family_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "cognitive_research_protocol.py"
REPO_ROOT = Path(__file__).resolve().parents[2]

ALLOWED_NEW_FILES = {
    "BUILD_STANDARD.md",
    "docs/PROJECT_BOUNDARIES_v1.md",
    "docs/WESLR_RECURSIVE_COGNITIVE_RESEARCH_PROTOCOL_AND_GENERATOR_LOOP_V1.md",
    "weslr/cognitive_research_protocol.py",
    "weslr/raw_signal_cartographer.py",
    "weslr/unintelligible_output_analyzer.py",
    "weslr/tests/test_cognitive_research_protocol_v1.py",
    "weslr/tests/test_raw_signal_cartographer_v1.py",
    "weslr/tests/test_entity_graph_import_guard_v1.py",
    "weslr/tests/release_gate_v1.py",
    "docs/WESLR_FORECAST_CALIBRATION_BRIDGE_REVIEW_V1.md",
    "entity_graph.py",
    "weslr/nonlinear_inspiration_resonance_engine.py",
    "weslr/tests/test_nonlinear_inspiration_resonance_engine_v1.py",
}

PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

BASE_PACKET = build_cognitive_research_run_v1(
    {
        "engine_name": "unknown_engine",
        "research_mode": "internal_exploration",
        "input_artifact_ref": "artifact:recursive-base-001",
        "input_artifact_type": "notes",
        "input_summary": "Metadata-only recursive research input.",
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "candidate_generator_only",
        "hypotheses": ["A hidden rule may explain the contradiction cloud."],
        "probes": ["observe -> predict -> reveal -> correct"],
        "compressed_lesson": "Unknowns should stay unknown until probes earn them.",
    }
)


def _packet(engine_name: str = "unknown_engine", engine_family: str | None = None, **overrides):
    payload = deepcopy(BASE_PACKET)
    payload.update(
        {
            "engine_name": engine_name,
            "engine_family": engine_family if engine_family is not None else classify_cognitive_research_engine_family_v1(engine_name) or "unknown_modeling",
        }
    )
    payload.update(overrides)
    return build_cognitive_research_run_v1(payload)


@pytest.mark.parametrize(
    "getter, expected",
    [
        (protocol.allowed_cognitive_research_engine_families_v1, ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1),
        (protocol.allowed_cognitive_research_engine_names_v1, ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1),
        (protocol.allowed_cognitive_research_research_modes_v1, ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1),
        (protocol.allowed_cognitive_research_public_claim_statuses_v1, ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1),
        (protocol.allowed_cognitive_research_llm_helper_roles_v1, ALLOWED_COGNITIVE_RESEARCH_LLM_HELPER_ROLES_V1),
    ],
)
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


@pytest.mark.parametrize(
    "engine_name, expected_family",
    [
        ("unknown_engine", "unknown_modeling"),
        ("raw_signal_cartographer", "raw_signal_analysis"),
        ("unintelligible_output_analyzer", "reasoning_integrity"),
        ("nonlinear_inspiration_engine", "discovery_generation"),
        ("resonance_engine", "discovery_generation"),
        ("algorithm_emergence_engine", "discovery_generation"),
        ("mutable_axiom_math_engine", "reasoning_integrity"),
        ("gap_cartographer", "frontier_gap_mapping"),
        ("dialectic_generator_loop", "recursive_generation"),
        ("rule_pressure_engine", "recursive_generation"),
        ("perspicuity_scorer", "reasoning_integrity"),
        ("live_weird_feed_adapter", "live_signal_ingestion"),
        ("public_gap_card_exporter", "public_export"),
    ],
)
def test_engine_family_classification_is_deterministic(engine_name, expected_family):
    assert classify_cognitive_research_engine_family_v1(engine_name) == expected_family
    assert classify_cognitive_research_engine_family_v1(engine_name) == expected_family


@pytest.mark.parametrize(
    "key",
    [
        "runtime_wiring_authority",
        "chat_responder_authority",
        "final_answer_generation_authority",
        "public_claim_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
        "filesystem_authority",
        "network_authority",
        "subprocess_authority",
        "weslr_io_authority",
        "persistence_database_write_authority",
        "real_memory_mutation_authority",
        "real_project_mutation_authority",
        "behavior_pack_promotion_authority",
        "autonomous_self_modification_authority",
        "official_intelligence_claim_authority",
        "public_discovery_claim_authority",
    ],
)
def test_default_denied_authority_is_complete_and_false(key):
    denied = build_default_cognitive_research_denied_authority_v1()
    assert key in denied
    assert denied[key] is False


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("unknown_engine", "unknown_modeling"),
        ("raw_signal_cartographer", "raw_signal_analysis"),
        ("unintelligible_output_analyzer", "reasoning_integrity"),
        ("signal_vs_noise_engine", "raw_signal_analysis"),
        ("nonlinear_inspiration_engine", "discovery_generation"),
        ("resonance_engine", "discovery_generation"),
        ("algorithm_emergence_engine", "discovery_generation"),
        ("mutable_axiom_math_engine", "reasoning_integrity"),
        ("operator_forge_engine", "discovery_generation"),
        ("invariant_miner", "reasoning_integrity"),
        ("contradiction_furnace", "reasoning_integrity"),
        ("causal_trace_engine", "reasoning_integrity"),
        ("blindspot_engine", "frontier_gap_mapping"),
        ("calibration_ledger", "calibration_and_forecast"),
        ("forecast_error_ledger", "calibration_and_forecast"),
        ("gap_cartographer", "frontier_gap_mapping"),
        ("assumption_excavator", "frontier_gap_mapping"),
        ("probe_generator", "discovery_generation"),
        ("memory_trust_engine", "human_project_intelligence"),
        ("abstraction_ladder", "reasoning_integrity"),
        ("governance_boundary_engine", "governance_and_boundary"),
        ("intent_reconstruction_engine", "human_project_intelligence"),
        ("dialectic_generator_loop", "recursive_generation"),
        ("rule_pressure_engine", "recursive_generation"),
        ("perspicuity_scorer", "reasoning_integrity"),
        ("live_weird_feed_adapter", "live_signal_ingestion"),
        ("public_gap_card_exporter", "public_export"),
    ],
)
def test_valid_packets_for_required_engines(engine_name, engine_family):
    packet = _packet(
        engine_name=engine_name,
        engine_family=engine_family,
        llm_helper_role="candidate_generator_only",
        public_claim_status="internal_candidate_only",
        public_gap_card_status="public_export_blocked",
        non_actionable_research_only=True,
        simulation_before_real_world=True,
        safe_metadata={"safe": True, "metadata_only": True, "generator_loop": protocol.GENERATOR_LOOP_V1},
    )
    validation = validate_cognitive_research_run_v1(packet)
    summary = summarize_cognitive_research_run_v1(packet)

    assert validation["blocked"] is False
    assert validation["classification"] == engine_name
    assert summary["blocked"] is False
    assert summary["summary_text"].startswith("Cognitive research run:")


@pytest.mark.parametrize(
    "engine_name, engine_family",
    [
        ("unknown_engine", "raw_signal_analysis"),
        ("raw_signal_cartographer", "discovery_generation"),
        ("mutable_axiom_math_engine", "public_export"),
        ("gap_cartographer", "unknown_modeling"),
    ],
)
def test_engine_family_mismatch_fails(engine_name, engine_family):
    packet = _packet(engine_name=engine_name, engine_family=engine_family)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "engine_family_mismatch" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": None},
        {"denied_authority": {}},
    ],
)
def test_missing_denied_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("missing_denied_authority") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "llm_authority": True}},
    ],
)
def test_llm_treated_as_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "denied_authority_granted_llm_authority" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "summary_text",
    [
        "breakthrough proof solution certified public-ready",
        "official certification solved breakthrough",
    ],
)
def test_public_breakthrough_claim_fails(summary_text):
    packet = _packet(public_claim_status="public_export_blocked", input_summary=summary_text)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "public_claim_language" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "runtime_wiring_authority": True}},
        {"boundary_status": {**protocol._default_boundary_status(), "runtime_wiring_authority": True}},
    ],
)
def test_runtime_wiring_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "provider_model_call_authority": True}},
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "provider_authority": True}},
    ],
)
def test_provider_model_call_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "summary_text",
    [
        "raw private data hidden system prompt",
        "private mechanism text with raw project data",
    ],
)
def test_raw_private_text_fails(summary_text):
    packet = _packet(input_summary=summary_text)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "raw_private_or_hidden_text" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "mutation",
    [
        {"denied_authority": {**build_default_cognitive_research_denied_authority_v1(), "final_answer_generation_authority": True}},
    ],
)
def test_final_answer_authority_fails(mutation):
    packet = _packet()
    packet.update(mutation)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "denied_authority_granted_final_answer_generation_authority" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "source_signal",
    [
        {"signal_origin": "live_weird_feed_metadata_only", "source_ref": "feed:future", "summary": "live weird feed metadata only", "trust_level": "reviewed", "poison_risk": "low", "injection_risk": "low", "raw_content_ref_only": True},
        {"signal_origin": "live_weird_feed_metadata_only", "source_ref": "feed:future", "summary": "live weird feed metadata only", "raw_content_ref_only": False, "trust_level": "reviewed", "poison_risk": "low", "injection_risk": "low"},
    ],
)
def test_live_feed_without_trust_poison_injection_metadata_fails(source_signal):
    packet = _packet(engine_name="live_weird_feed_adapter", engine_family="live_signal_ingestion", source_signal=build_source_signal_metadata_v1(source_signal))
    packet["source_signal"].pop("trust_level", None)
    packet["source_signal"].pop("poison_risk", None)
    packet["source_signal"].pop("injection_risk", None)
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("live_feed_trust_poison_injection_gap", "live_feed_must_be_ref_only", "missing_source_signal_trust_level"))


def test_generated_source_signal_without_parent_fails():
    packet = _packet(
        engine_name="dialectic_generator_loop",
        engine_family="recursive_generation",
        generated_source_signals=[
            build_generated_source_signal_metadata_v1(
                {
                    "generated_signal_id": "generated-001",
                    "generation_reason": "loop mutation",
                    "mutation_type": "dialectic_rewrite",
                    "expected_pressure": "counterexample",
                    "target_uncertainty": "bounded",
                    "generated_signal_summary": "mutated source signal",
                    "raw_generated_content_included": False,
                    "safe_to_reingest": True,
                }
            )
        ],
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "generated_source_signal_0_missing_parent_reference" in validation["blocked_labels"]


def test_rule_pressure_promoting_candidate_without_calibration_scope_update_fails():
    packet = _packet(
        engine_name="rule_pressure_engine",
        engine_family="recursive_generation",
        rule_pressure_tests=[
            build_rule_pressure_test_metadata_v1(
                {
                    "target_rule_or_operator": "candidate rule",
                    "pressure_type": "counterexample",
                    "mutated_input_summary": "mutated input",
                    "expected_behavior": "stay bounded",
                    "observed_behavior": "promoted",
                    "result": "promoted",
                    "failure_mode": "none",
                    "scope_update": "",
                }
            )
        ],
        calibration_record={},
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("rule_pressure_promoted_without") for label in validation["blocked_labels"])


def test_perspicuity_score_used_as_safety_gate_fails():
    packet = _packet(
        engine_name="perspicuity_scorer",
        engine_family="reasoning_integrity",
        perspicuity_score=build_perspicuity_score_metadata_v1({"score": 70, "clarity": 70, "signal_density": 70, "novelty": 65, "gap_pressure": 60, "verification_potential": 70, "recurrence": 55, "cross_domain_resonance": 50, "reason": "gate it", "used_as_gate": True}),
        safe_metadata={"safe": True, "metadata_only": True, "perspicuity_is_not_a_gate": False, "use_perspicuity_as_gate": True},
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is True
    assert "perspicuity_used_as_gate" in validation["blocked_labels"]


def test_safe_internal_radical_hypothesis_passes_when_public_claim_blocked():
    packet = _packet(
        engine_name="unknown_engine",
        engine_family="unknown_modeling",
        research_mode="internal_exploration",
        public_claim_status="internal_candidate_only",
        llm_helper_role="candidate_generator_only",
        hypotheses=["A strange contradiction cloud may encode a new operator family."],
        probes=["interpret the contradiction cloud"],
        non_actionable_research_only=True,
        safety_boundary={"scope": "metadata_only", "non_actionable": True},
    )
    validation = validate_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False


def test_massive_artifact_ref_passes_without_raw_storage():
    massive_ref = "artifact:" + ("A" * 5000)
    packet = _packet(
        engine_name="raw_signal_cartographer",
        engine_family="raw_signal_analysis",
        input_artifact_ref=massive_ref,
        input_summary="Metadata-only summary for a large artifact reference.",
        source_scope="metadata_only",
    )
    validation = validate_cognitive_research_run_v1(packet)
    summary = summarize_cognitive_research_run_v1(packet)
    assert validation["blocked"] is False
    assert len(summary["summary_text"]) <= 320
    assert "artifact:" in summary["summary_text"]


@pytest.mark.parametrize(
    "packet_builder",
    [
        lambda: _packet(),
        lambda: _packet(engine_name="raw_signal_cartographer", engine_family="raw_signal_analysis"),
    ],
)
def test_json_safe_copy_works(packet_builder):
    value = to_cognitive_research_json_safe_v1({"items": {1, 2}, "tuple": ("a", "b"), "custom": object()})
    assert value["items"] in ([1, 2], [2, 1])
    json.dumps(value, sort_keys=True)
    packet = packet_builder()
    safe = to_cognitive_research_json_safe_v1(packet)
    json.dumps(safe, sort_keys=True)


def test_summary_is_safe_and_bounded():
    packet = _packet(input_summary="raw private text with hidden system prompt")
    summary = summarize_cognitive_research_run_v1(packet)
    assert summary["summary_text"].startswith("Blocked cognitive research run:") or summary["summary_text"].startswith("Cognitive research run:")
    assert len(summary["summary_text"]) <= 320
    assert "raw private" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_examples_include_all_supported_families_and_names():
    examples = build_initial_cognitive_research_examples_v1()
    families = {example["engine_family"] for example in examples}
    names = {example["engine_name"] for example in examples}
    assert families == set(ALLOWED_COGNITIVE_RESEARCH_ENGINE_FAMILIES_V1)
    assert names == set(ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1)
    assert all(example["public_claim_status"] in set(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1) for example in examples)
    assert all(example["public_gap_card_status"] in set(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_GAP_CARD_STATUSES_V1) for example in examples)


def test_nested_metadata_builders_are_json_safe():
    signal = build_source_signal_metadata_v1({"signal_origin": "metadata_only", "source_ref": "artifact:signal-001", "summary": "structured signal"})
    generated = build_generated_source_signal_metadata_v1({"parent_suggestion_id": "suggestion-001", "generated_signal_summary": "generated"})
    pressure = build_rule_pressure_test_metadata_v1({"target_rule_or_operator": "rule", "pressure_type": "edge_case"})
    resonance = build_nonlinear_resonance_candidate_v1({"source_gap": "gap", "resonance_domain": "domain"})
    perspicuity = build_perspicuity_score_metadata_v1({"score": 42, "clarity": 42, "signal_density": 43, "novelty": 44, "gap_pressure": 41, "verification_potential": 45, "recurrence": 39, "cross_domain_resonance": 40})

    json.dumps(signal, sort_keys=True)
    json.dumps(generated, sort_keys=True)
    json.dumps(pressure, sort_keys=True)
    json.dumps(resonance, sort_keys=True)
    json.dumps(perspicuity, sort_keys=True)


def test_protected_file_drift_absent():
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {
        line.split(maxsplit=1)[1]
        for line in completed.stdout.splitlines()
        if line.strip()
    }
    assert changed.issubset(ALLOWED_NEW_FILES)
    assert not changed.intersection(PROTECTED_FILES)
