#!/usr/bin/env python3
"""Focused tests for the Nonlinear Inspiration / Resonance engine V1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import weslr.cognitive_research_protocol as protocol
from weslr.forecast_calibration_bridge import build_forecast_calibration_packet_from_research_run_v1, validate_forecast_calibration_record_v1
from weslr.nonlinear_inspiration_resonance_engine import (
    ALLOWED_DOMAIN_DISTANCE_V1,
    ALLOWED_GAP_TYPES_V1,
    ALLOWED_OPERATOR_STATUS_V1,
    ALLOWED_SCORE_LABELS_V1,
    ENGINE_FAMILY_V1,
    ENGINE_NAME_V1,
    _build_safe_boundary_status_v1,
    build_initial_nonlinear_inspiration_examples_v1,
    build_intelligibility_bridge_v1,
    build_nonlinear_inspiration_packet_v1,
    build_resonance_domain_candidate_v1,
    build_resonance_source_gap_v1,
    build_structural_match_v1,
    build_transferred_operator_candidate_v1,
    summarize_nonlinear_inspiration_packet_v1,
    to_nonlinear_inspiration_json_safe_v1,
    validate_nonlinear_inspiration_packet_v1,
)

PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

HELPER_PATH = ROOT / "weslr" / "nonlinear_inspiration_resonance_engine.py"


def _packet(**overrides):
    payload = {
        "engine_name": ENGINE_NAME_V1,
        "research_mode": "internal_exploration",
        "input_artifact_ref": "artifact:nonlinear-inspiration-001",
        "input_artifact_type": "gap-card",
        "input_summary": "Hidden-rule resonance candidate with a toy bridge.",
        "public_claim_status": "not_public_claim",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "resonance_suggestion_helper_only",
        "denied_authority": protocol.build_default_cognitive_research_denied_authority_v1(),
        "safe_metadata": {
            "safe": True,
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
            "no_runtime_wiring": True,
            "no_provider_calls": True,
            "no_tool_execution": True,
            "no_persistence": True,
            "no_memory_mutation": True,
            "no_project_mutation": True,
            "no_behavior_pack_promotion": True,
            "no_final_answer": True,
            "no_public_claims": True,
            "no_weslr_io": True,
            "no_network": True,
            "no_subprocess": True,
        },
    }
    payload.update(overrides)
    packet = build_nonlinear_inspiration_packet_v1(payload)
    for key in (
        "input_summary",
        "resonance_source_gaps",
        "resonance_domain_candidates",
        "structural_matches",
        "transferred_operator_candidates",
        "intelligibility_bridges",
        "safe_metadata",
        "public_claim_status",
        "public_gap_card_status",
    ):
        if key in payload:
            packet[key] = deepcopy(payload[key])
    packet["research_mode"] = payload.get("research_mode", "internal_exploration")
    if payload.get("denied_authority") is None and "denied_authority" in payload:
        packet["denied_authority"] = None
    else:
        denied_keys = getattr(protocol, "_DENIED_AUTHORITY_KEYS_V1", ())
        packet["denied_authority"] = {str(key): False for key in denied_keys}
    packet["boundary_status"] = _build_safe_boundary_status_v1()
    packet["calibration_record"] = build_forecast_calibration_packet_from_research_run_v1(
        packet,
        uncertainty_factors=["boundary risk remains unconfirmed"],
        invalidation_signals=["a later probe may break the transfer"],
        compressed_lesson="Distant resonance is useful only when it becomes a bounded, testable bridge.",
        future_adjustment="tighten the analogy before widening the transfer",
    )
    return packet


def _flatten(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _flatten(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten(item)


class TestNonlinearInspirationResonanceEngineV1:
    def test_01_import_safety_and_public_api(self):
        import weslr.nonlinear_inspiration_resonance_engine as mod

        assert mod.ENGINE_NAME_V1 == ENGINE_NAME_V1
        assert mod.ENGINE_FAMILY_V1 == ENGINE_FAMILY_V1
        for name in (
            "build_resonance_source_gap_v1",
            "build_resonance_domain_candidate_v1",
            "build_structural_match_v1",
            "build_transferred_operator_candidate_v1",
            "build_intelligibility_bridge_v1",
            "build_nonlinear_inspiration_packet_v1",
            "validate_nonlinear_inspiration_packet_v1",
            "summarize_nonlinear_inspiration_packet_v1",
            "to_nonlinear_inspiration_json_safe_v1",
            "build_initial_nonlinear_inspiration_examples_v1",
        ):
            assert callable(getattr(mod, name))

    def test_02_module_has_no_forbidden_runtime_imports(self):
        source = HELPER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "socket", "urllib", "openai", "anthropic", "http.client", "subprocess"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden)
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden
        assert "respond_chat(" not in source
        assert "generate_chat(" not in source
        assert ".weslr/" not in source

    @pytest.mark.parametrize(
        "gap_type",
        ["hidden_rule_gap", "operator_gap", "scale_transition_gap", "translation_gap"],
    )
    def test_03_valid_gap_packets_pass(self, gap_type):
        packet = _packet(
            gap_type=gap_type,
            gap_summary=f"A {gap_type} appears in a bounded resonance problem.",
            failure_shape="The boundary changes before the operator is named.",
        )
        validation = validate_nonlinear_inspiration_packet_v1(packet)
        protocol_validation = protocol.validate_cognitive_research_run_v1(packet)
        assert validation["valid"] is True
        assert protocol_validation["blocked"] is False
        assert protocol_validation["classification"] == ENGINE_NAME_V1
        assert packet["resonance_source_gaps"][0]["gap_type"] == gap_type

    def test_04_valid_far_domain_candidate_passes(self):
        domain = build_resonance_domain_candidate_v1(
            {
                "domain_id": "domain:far-001",
                "domain_label": "topology",
                "domain_distance": "very_far",
                "why_relevant": "It shares a transfer shape without the same surface form.",
                "surface_difference": "The surface language is very different.",
                "deep_structure_candidate": "The same boundary-shape relation may survive.",
                "risk_of_false_analogy": "The analogy may fail if the hidden state does not transfer.",
            }
        )
        assert domain["domain_distance"] == "very_far"
        assert json.dumps(domain, sort_keys=True)
        assert set(domain) >= {"domain_id", "domain_label", "domain_distance", "why_relevant"}

    def test_05_valid_structural_match_passes(self):
        match = build_structural_match_v1(
            {
                "source_gap_id": "gap:001",
                "resonance_domain": "domain:far-001",
                "shared_structure": "Both cases preserve a boundary-shape relation.",
                "shared_operator_shape": "A local transformation stays stable.",
                "shared_boundary_shape": "A boundary shift precedes explicit naming.",
                "shared_failure_mode": "The mapping breaks when the hidden state stops transferring.",
                "invariant_candidate": "The boundary-shape relation may be invariant.",
                "where_mapping_breaks": "It breaks when the hidden state is no longer transferable.",
                "match_confidence": "high",
                "match_uncertainty": "medium",
            }
        )
        assert match["match_confidence"] == "high"
        assert match["match_uncertainty"] == "medium"
        assert json.dumps(match, sort_keys=True)

    def test_06_valid_transferred_operator_candidate_passes(self):
        operator = build_transferred_operator_candidate_v1(
            {
                "operator_label": "transfer-the-boundary",
                "source_domain": "topology",
                "target_gap": "gap:001",
                "input_type": "gap metadata",
                "output_type": "bridge metadata",
                "transformation_logic": "Translate a boundary relation into a toy operator.",
                "what_it_might_explain": "Why the same boundary shape reappears.",
                "where_it_probably_fails": "When the hidden state stops transferring.",
                "toy_application_summary": "A toy case shows the transfer in two steps.",
                "probe_to_test_usefulness": "Check the operator on a smaller boundary shift.",
                "operator_status": "probe_ready",
            }
        )
        assert operator["operator_status"] == "probe_ready"
        assert operator["where_it_probably_fails"]
        assert json.dumps(operator, sort_keys=True)

    def test_07_valid_intelligibility_bridge_passes(self):
        bridge = build_intelligibility_bridge_v1(
            {
                "plain_language_bridge": "A simple bridge from hidden structure to a toy example.",
                "formal_sketch": "Sketch the relation in a compact operator form.",
                "toy_example_summary": "A toy example shows one boundary shift and one operator transfer.",
                "minimal_sequence": ["observe", "map", "transfer", "probe"],
                "new_notation_needed": False,
                "unmapped_terms": ["boundary-shape relation"],
                "failure_boundary": "The bridge fails when the hidden structure cannot transfer.",
                "next_probe": "Try the same mapping on a smaller toy example.",
                "intelligibility_score": "medium",
                "testability_score": "high",
                "novelty_score": "medium",
            }
        )
        assert bridge["toy_example_summary"]
        assert bridge["failure_boundary"]
        assert bridge["intelligibility_score"] in ALLOWED_SCORE_LABELS_V1
        assert json.dumps(bridge, sort_keys=True)

    def test_08_valid_default_packet_passes_protocol_validation(self):
        packet = _packet()
        validation = validate_nonlinear_inspiration_packet_v1(packet)
        protocol_validation = protocol.validate_cognitive_research_run_v1(packet)
        assert validation["valid"] is True
        assert protocol_validation["blocked"] is False
        assert protocol_validation["classification"] == ENGINE_NAME_V1
        assert packet["engine_family"] == ENGINE_FAMILY_V1

    def test_09_calibration_bridge_compatibility_passes(self):
        packet = _packet()
        record = packet["calibration_record"]
        assert validate_forecast_calibration_record_v1(record)["valid"] is True
        assert record["source_engine_name"] == ENGINE_NAME_V1

    def test_10_json_safe_copy_strips_unsafe_raw_fields(self):
        unsafe = deepcopy(_packet())
        unsafe["raw_prompt_text"] = "raw private text hidden system prompt"
        unsafe["hidden_prompt"] = "developer prompt leakage"
        unsafe["resonance_source_gaps"][0]["private_blob"] = "secret payload"
        safe = to_nonlinear_inspiration_json_safe_v1(unsafe)
        assert "raw_prompt_text" not in safe
        assert "hidden_prompt" not in safe
        assert "private_blob" not in json.dumps(safe, sort_keys=True)
        flattened = "\n".join(_flatten(safe)).lower()
        assert "raw private text" not in flattened
        assert "hidden prompt" not in flattened
        json.dumps(safe, sort_keys=True)

    def test_11_summary_is_concise_and_private_safe(self):
        summary = summarize_nonlinear_inspiration_packet_v1(_packet())
        assert len(summary["summary_text"]) <= 360
        assert "secret" not in summary["summary_text"].lower()
        assert "hidden prompt" not in summary["summary_text"].lower()

    def test_12_examples_cover_required_gap_types(self):
        examples = build_initial_nonlinear_inspiration_examples_v1()
        gap_types = {example["resonance_source_gaps"][0]["gap_type"] for example in examples}
        assert len(examples) >= 4
        assert gap_types.issuperset({"hidden_rule_gap", "scale_transition_gap", "translation_gap", "signal_noise_gap"})

    @pytest.mark.parametrize(
        "mutator,expected",
        [
            (lambda packet: packet["resonance_source_gaps"][0].__delitem__("source_gap_id"), "missing_source_gap_id"),
            (lambda packet: packet["resonance_source_gaps"][0].__setitem__("gap_summary", ""), "missing_source_gap_summary"),
            (lambda packet: packet["resonance_source_gaps"][0].__setitem__("gap_type", ""), "invalid_gap_type"),
            (lambda packet: packet["resonance_source_gaps"][0].__delitem__("uncertainty_factors"), "missing_uncertainty_factors"),
            (lambda packet: packet["resonance_source_gaps"][0].__delitem__("invalidation_signals"), "missing_invalidation_signals"),
            (lambda packet: packet["structural_matches"][0].__setitem__("shared_structure", ""), "missing_structural_match_explanation"),
            (lambda packet: packet["transferred_operator_candidates"][0].__setitem__("where_it_probably_fails", ""), "missing_failure_boundary"),
            (lambda packet: packet["transferred_operator_candidates"][0].__setitem__("operator_status", "proven"), "operator_candidate_marked_proven_or_true"),
            (lambda packet: packet["intelligibility_bridges"][0].__setitem__("toy_example_summary", ""), "missing_toy_example_summary"),
            (lambda packet: packet["intelligibility_bridges"][0].__setitem__("failure_boundary", ""), "missing_failure_boundary"),
            (lambda packet: packet["intelligibility_bridges"][0].__setitem__("novelty_score", "extreme"), "invalid_score_label"),
            (lambda packet: packet.__setitem__("public_claim_status", "public_safe_summary_required"), "public_export_marked_safe"),
        ],
    )
    def test_13_negative_validation_rules_fail_closed(self, mutator, expected):
        packet = _packet()
        if expected == "":
            pytest.skip("placeholder")
        mutator(packet)
        validation = validate_nonlinear_inspiration_packet_v1(packet)
        assert validation["valid"] is False
        labels = " ".join(validation["violations"])
        assert expected in labels

    @pytest.mark.parametrize(
        "payload,expected",
        [
            ({"input_summary": "AGI consciousness breakthrough proof claim"}, "forbidden_text_marker"),
            ({"input_summary": "final answer authority should be blocked"}, "forbidden_text_marker"),
            ({"input_summary": "llm authority should be blocked"}, "forbidden_text_marker"),
            ({"input_summary": "tool authority provider authority runtime authority persistence database write"}, "protocol:runtime_provider_tool_persistence_implication"),
            ({"input_summary": " .weslr private artifact reference and internal details "}, "protocol:dot_weslr_implication"),
            ({"input_summary": "live ingestion from github rss lab notebook and network feed"}, "protocol:live_ingestion_network_implication"),
            ({"input_summary": "memory mutation authority"}, "protocol:memory_mutation_authority"),
            ({"input_summary": "project mutation authority"}, "protocol:project_mutation_authority"),
            ({"input_summary": "behavior pack promotion implication"}, "protocol:behavior_pack_promotion_implication"),
            ({"denied_authority": None}, "protocol:missing_denied_authority"),
            ({"safe_metadata": {"safe": False, "metadata_only": True}}, "protocol:unsafe_safe_metadata"),
            ({"resonance_source_gaps": [{"source_gap_id": "gap:1", "source_engine_name": "nonlinear_inspiration_engine", "source_run_id": "run:1", "gap_summary": "raw private text hidden system prompt", "gap_type": "hidden_rule_gap", "failure_shape": "shape", "missing_structure_suspected": True, "known_scope": "scope", "failure_scope": "scope", "uncertainty_factors": ["u"], "invalidation_signals": ["i"], "public_claim_status": "not_public_claim"}]}, "protocol:raw_private_or_hidden_text"),
            ({"intelligibility_bridges": [{"bridge_id": "bridge:1", "plain_language_bridge": "hidden prompt", "formal_sketch": "sketch", "toy_example_summary": "toy", "minimal_sequence": ["a"], "new_notation_needed": False, "unmapped_terms": [], "failure_boundary": "fail", "next_probe": "probe", "intelligibility_score": "medium", "testability_score": "medium", "novelty_score": "medium"}]}, "protocol:raw_private_or_hidden_text"),
        ],
    )
    def test_14_forbidden_text_and_authority_implications_fail(self, payload, expected):
        packet = _packet(**payload)
        validation = validate_nonlinear_inspiration_packet_v1(packet)
        assert validation["valid"] is False
        labels = " ".join(validation["violations"])
        assert expected in labels

    def test_15_protected_files_unchanged(self):
        for rel in PROTECTED_FILES:
            subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)
