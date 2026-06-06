#!/usr/bin/env python3
"""Focused tests for ALGORITHM_EMERGENCE_ENGINE helpers v1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from weslr.cognitive_research_engine_boundaries import (
    build_cognitive_research_engine_boundary_registry_v1,
    get_cognitive_research_engine_boundary_v1,
    validate_cognitive_research_engine_boundary_v1,
)
from weslr.cognitive_research_protocol import build_default_cognitive_research_denied_authority_v1
from weslr.algorithm_emergence_engine import (
    build_algorithm_emergence_packet_v1,
    build_initial_algorithm_emergence_examples_v1,
    summarize_algorithm_emergence_packet_v1,
    to_algorithm_emergence_json_safe_v1,
    validate_algorithm_emergence_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "algorithm_emergence_engine.py"
EXPECTED_FIELDS = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "candidate_algorithm_map",
    "operator_chain_candidates",
    "transformation_rule_candidates",
    "state_transition_hints",
    "invariant_candidates",
    "recursion_self_similarity_labels",
    "algorithm_likeness_confidence_map",
    "invalidated_rule_candidates",
    "undecidable_process_regions",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_signal_vs_noise",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)


def _packet(**overrides):
    payload = {
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:algorithm-emergence:artifact:test-001",
        "artifact_summary": "Synthetic process-like fragment with operator chains, invariants, and undecidable regions.",
        "candidate_algorithm_map": {
            "candidate_a": "rule-like chain with repeated state transitions",
            "candidate_b": "structured path with invariant preservation",
        },
        "operator_chain_candidates": ["chain-a", "chain-b"],
        "transformation_rule_candidates": ["rule-a", "rule-b"],
        "state_transition_hints": ["transition hint one", "transition hint two"],
        "invariant_candidates": ["invariant candidate one", "invariant candidate two"],
        "recursion_self_similarity_labels": ["self-similarity hint", "recursion hint"],
        "algorithm_likeness_confidence_map": {"likeness": "bounded", "confidence": "mixed", "uncertainty": "tracked"},
        "invalidated_rule_candidates": ["rule candidate rejected"],
        "undecidable_process_regions": ["undecidable process band"],
        "next_probe_labels": ["vary one step", "compare operator-chain persistence"],
        "relationship_to_raw_signal_cartographer": {
            "role": "algorithm_inference_after_raw_signal",
            "upstream_engine_name": "RAW_SIGNAL_CARTOGRAPHER",
            "preserves_unknown_tokens": True,
            "preserves_competing_layers": True,
            "not_final_meaning_authority": True,
            "not_runtime_authority": True,
            "not_tool_authority": True,
            "not_provider_authority": True,
            "not_search_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "relationship_to_unintelligible_output_analyzer": {
            "role": "algorithm_inference_after_interpretation_preservation",
            "upstream_engine_name": "UNINTELLIGIBLE_OUTPUT_ANALYZER",
            "preserves_competing_interpretations": True,
            "preserves_weak_structure": True,
            "not_final_meaning_authority": True,
            "not_runtime_authority": True,
            "not_tool_authority": True,
            "not_provider_authority": True,
            "not_search_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "relationship_to_signal_vs_noise": {
            "role": "algorithm_inference_after_signal_noise_discrimination",
            "upstream_engine_name": "SIGNAL_VS_NOISE_ENGINE",
            "preserves_signal_noise_classification": True,
            "preserves_weak_signal_candidates": True,
            "preserves_pseudo_randomness_labels": True,
            "preserves_artifact_effect_labels": True,
            "preserves_undecidable_regions": True,
            "not_final_algorithm_authority": True,
            "not_runtime_authority": True,
            "not_tool_authority": True,
            "not_provider_authority": True,
            "not_search_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "safe_metadata": {
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
        },
        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
        "public_claim_status": "blocked_internal_only",
    }
    payload.update(overrides)
    return build_algorithm_emergence_packet_v1(payload)


class TestAlgorithmEmergenceEngineV1:
    def test_01_valid_synthetic_packet_passes(self):
        packet = _packet()
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_02_all_required_fields_exist(self):
        packet = _packet()
        assert set(EXPECTED_FIELDS).issubset(packet.keys())

    def test_03_unknown_engine_fails(self):
        packet = _packet()
        packet["engine_name"] = "NOT_ALGORITHM_EMERGENCE_ENGINE"
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_04_wrong_engine_fails(self):
        packet = _packet()
        packet["source_boundary_engine_name"] = "RAW_SIGNAL_CARTOGRAPHER"
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_05_missing_boundary_registry_entry_fails(self, monkeypatch):
        monkeypatch.setattr(
            "weslr.algorithm_emergence_engine.build_cognitive_research_engine_boundary_registry_v1",
            lambda: {},
        )
        packet = _packet()
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("field,value", [("artifact_summary", "raw private data should never appear"), ("input_category", "raw private data")])
    def test_06_raw_private_data_fails(self, field, value):
        packet = _packet(**{field: value})
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_07_secret_markers_fail(self):
        packet = _packet(artifact_summary="this contains a secret token=abc")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_08_hidden_system_prompt_markers_fail(self):
        packet = _packet(artifact_summary="hidden system prompt content")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_09_weslr_content_fails(self):
        packet = _packet(artifact_summary="contains .weslr contents")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_10_executable_and_live_tool_instructions_fail(self):
        packet = _packet(artifact_summary="please run this executable code-as-action and live tool instructions")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_11_provider_output_authority_claim_fails(self):
        packet = _packet(artifact_summary="provider/model output claimed as authority")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_12_dangerous_procedural_content_fails(self):
        packet = _packet(artifact_summary="dangerous procedural instructions with step-by-step exploit chain")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_13_massive_raw_artifact_pasted_instead_of_reference_fails(self):
        packet = _packet(artifact_reference="artifact:\n" + ("x" * 1200), artifact_summary="bounded summary")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_14_denied_authority_true_fails(self):
        denied = build_default_cognitive_research_denied_authority_v1()
        denied["runtime_authority"] = True
        packet = _packet(denied_authority=denied)
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_15_public_claim_drift_fails(self):
        packet = _packet(public_claim_status="breakthrough")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_16_confirmed_algorithm_discovery_fails(self):
        packet = _packet(artifact_summary="confirmed algorithm discovery and solved algorithm")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_17_programming_assistant_flattening_fails(self):
        packet = _packet(artifact_summary="generic programming assistant summary with no operator chain detail")
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is False

    def test_18_operator_chains_are_preserved(self):
        packet = _packet(operator_chain_candidates=["chain-a", "chain-b", "chain-c"])
        assert packet["operator_chain_candidates"][-1] == "chain-c"
        assert validate_algorithm_emergence_packet_v1(packet)["valid"] is True

    def test_19_invariants_are_preserved(self):
        packet = _packet(invariant_candidates=["invariant candidate one", "invariant candidate two"])
        assert packet["invariant_candidates"][0] == "invariant candidate one"
        assert validate_algorithm_emergence_packet_v1(packet)["valid"] is True

    def test_20_recursion_hints_are_preserved(self):
        packet = _packet(recursion_self_similarity_labels=["self-similarity hint", "recursion hint", "recursive trace"])
        assert packet["recursion_self_similarity_labels"][-1] == "recursive trace"
        assert validate_algorithm_emergence_packet_v1(packet)["valid"] is True

    def test_21_invalidated_rules_are_preserved(self):
        packet = _packet(invalidated_rule_candidates=["rule candidate rejected", "operator chain rejected"])
        assert packet["invalidated_rule_candidates"][-1] == "operator chain rejected"
        assert validate_algorithm_emergence_packet_v1(packet)["valid"] is True

    def test_22_undecidable_regions_are_preserved(self):
        packet = _packet(undecidable_process_regions=["undecidable process band", "undecidable loop"])
        assert packet["undecidable_process_regions"][-1] == "undecidable loop"
        assert validate_algorithm_emergence_packet_v1(packet)["valid"] is True

    def test_23_confidence_map_is_allowed(self):
        packet = _packet(algorithm_likeness_confidence_map={"likeness": "low", "confidence": "mixed", "uncertainty": {"region": "tracked"}})
        validation = validate_algorithm_emergence_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["algorithm_likeness_confidence_map"]["likeness"] == "low"

    def test_24_json_safe_conversion_works(self):
        packet = _packet()
        safe = to_algorithm_emergence_json_safe_v1(packet)
        json.dumps(safe)
        assert isinstance(safe, dict)
        assert isinstance(safe["operator_chain_candidates"], list)

    def test_25_summaries_are_bounded_and_safe(self):
        packet = _packet()
        summary = summarize_algorithm_emergence_packet_v1(packet)
        assert len(summary) < 900
        assert "secret" not in summary.lower()
        assert "generic pattern summary" not in summary.lower()

    def test_26_examples_are_synthetic_and_non_private(self):
        examples = build_initial_algorithm_emergence_examples_v1()
        assert len(examples) >= 3
        for example in examples:
            assert str(example["artifact_reference"]).startswith("synthetic:")
            blob = json.dumps(example).lower()
            assert "secret" not in blob
            assert "hidden prompt" not in blob
            assert ".weslr" not in blob

    def test_27_helper_source_has_no_forbidden_imports(self):
        source = HELPER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        lowered = " ".join(imports).lower()
        for forbidden in ("subprocess", "socket", "urllib", "requests", "asyncio", "http.client"):
            assert forbidden not in lowered
        source_lower = source.lower()
        assert "os.system" not in source_lower
        assert "open(" not in source_lower
