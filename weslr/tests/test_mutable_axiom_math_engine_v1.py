#!/usr/bin/env python3
"""Focused tests for MUTABLE_AXIOM_MATH_ENGINE helpers v1."""

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
from weslr.mutable_axiom_math_engine import (
    build_initial_mutable_axiom_math_examples_v1,
    build_mutable_axiom_math_packet_v1,
    summarize_mutable_axiom_math_packet_v1,
    to_mutable_axiom_math_json_safe_v1,
    validate_mutable_axiom_math_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "mutable_axiom_math_engine.py"
EXPECTED_FIELDS = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "mutable_axiom_map",
    "axiom_variant_candidates",
    "rule_perturbation_labels",
    "invariant_shift_labels",
    "contradiction_surface_notes",
    "degenerate_case_labels",
    "boundary_case_labels",
    "toy_model_shift_summaries",
    "proof_obstruction_map",
    "consistency_instability_candidates",
    "invalidated_axiom_variants",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_signal_vs_noise",
    "relationship_to_algorithm_emergence",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)


def _packet(**overrides):
    payload = {
        "input_category": "synthetic symbolic math terrain",
        "artifact_reference": "synthetic:mutable-axiom-math:artifact:test-001",
        "artifact_summary": "Synthetic axiom packet with variant maps, contradiction surfaces, proof obstructions, and boundary cases.",
        "mutable_axiom_map": {
            "base_axiom": "stable assumption frame",
            "variant_a": "weaken one constraint",
            "variant_b": "strengthen one rule",
        },
        "axiom_variant_candidates": ["variant-a", "variant-b"],
        "rule_perturbation_labels": ["perturb rule one", "perturb rule two"],
        "invariant_shift_labels": ["invariant shift hint", "stability shift hint"],
        "contradiction_surface_notes": ["contradiction surface note one", "contradiction surface note two"],
        "degenerate_case_labels": ["degenerate case one", "degenerate case two"],
        "boundary_case_labels": ["boundary case one", "boundary case two"],
        "toy_model_shift_summaries": ["toy-model shift summary one", "toy-model shift summary two"],
        "proof_obstruction_map": {
            "obstruction_a": "proof path blocked by variant change",
            "obstruction_b": "alternative obstruction pattern retained",
        },
        "consistency_instability_candidates": {
            "consistency_candidate": "bounded consistency pocket",
            "instability_candidate": "instability boundary under mutation",
        },
        "invalidated_axiom_variants": ["variant rejected by contradiction surface"],
        "next_probe_labels": ["vary one axiom", "compare obstruction map", "test nearby boundary case"],
        "relationship_to_raw_signal_cartographer": {
            "role": "axiom_mutation_after_raw_signal",
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
            "role": "axiom_mutation_after_interpretive_preservation",
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
            "role": "axiom_mutation_after_signal_noise_discrimination",
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
        "relationship_to_algorithm_emergence": {
            "role": "axiom_mutation_after_algorithm_emergence",
            "upstream_engine_name": "ALGORITHM_EMERGENCE_ENGINE",
            "preserves_candidate_algorithm_map": True,
            "preserves_operator_chain_candidates": True,
            "preserves_transformation_rule_candidates": True,
            "preserves_invariant_candidates": True,
            "preserves_invalidated_rule_history": True,
            "preserves_terrain_shift_context": True,
            "not_final_math_authority": True,
            "not_runtime_authority": True,
            "not_tool_authority": True,
            "not_provider_authority": True,
            "not_search_authority": True,
            "not_proof_authority": True,
            "not_public_claim_authority": True,
        },
        "relationship_to_cognitive_research_run": {
            "role": "reporting_safety_envelope_only",
            "envelope_only": True,
            "not_engine_kernel": True,
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
    return build_mutable_axiom_math_packet_v1(payload)


class TestMutableAxiomMathEngineV1:
    def test_01_valid_synthetic_packet_passes(self):
        packet = _packet()
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_02_all_required_fields_exist(self):
        packet = _packet()
        assert set(EXPECTED_FIELDS).issubset(packet.keys())

    def test_03_unknown_engine_fails(self):
        packet = _packet()
        packet["engine_name"] = "NOT_MUTABLE_AXIOM_MATH_ENGINE"
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_04_wrong_boundary_engine_fails(self):
        packet = _packet()
        packet["source_boundary_engine_name"] = "ALGORITHM_EMERGENCE_ENGINE"
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_05_missing_boundary_registry_entry_fails(self, monkeypatch):
        monkeypatch.setattr(
            "weslr.mutable_axiom_math_engine.build_cognitive_research_engine_boundary_registry_v1",
            lambda: {},
        )
        packet = _packet()
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize(
        "field,value",
        [
            ("artifact_summary", "raw private data should never appear"),
            ("input_category", "raw private text"),
            ("artifact_reference", "secret"),
        ],
    )
    def test_06_raw_private_data_fails(self, field, value):
        packet = _packet(**{field: value})
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_07_hidden_system_prompt_and_weslr_markers_fail(self):
        packet = _packet(artifact_summary="hidden system prompt with .weslr contents")
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_08_live_tool_and_provider_authority_content_fails(self):
        packet = _packet(artifact_summary="executable code-as-action with live tool instructions and provider authority")
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_09_benchmark_answer_keys_and_private_benchmark_data_fail(self):
        packet = _packet(artifact_summary="benchmark answer key with hidden benchmark data")
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_10_denied_authority_true_fails(self):
        denied = build_default_cognitive_research_denied_authority_v1()
        denied["runtime_authority"] = True
        packet = _packet(denied_authority=denied)
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("value", ["breakthrough", "solved", "public ready", "certification"])
    def test_11_public_claim_drift_fails(self, value):
        packet = _packet(public_claim_status=value)
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("value", ["official mathematical result", "open problem solution"])
    def test_12_official_math_or_open_problem_claims_fail(self, value):
        packet = _packet(artifact_summary=value)
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize(
        "value",
        [
            "theorem prover",
            "proof solver",
            "math tutor",
            "benchmark runner",
            "answer generator",
        ],
    )
    def test_13_flattening_markers_fail(self, value):
        packet = _packet(artifact_summary=f"generic {value} output")
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize(
        "field",
        [
            "axiom_variant_candidates",
            "rule_perturbation_labels",
            "invariant_shift_labels",
            "contradiction_surface_notes",
            "degenerate_case_labels",
            "boundary_case_labels",
            "toy_model_shift_summaries",
            "invalidated_axiom_variants",
            "next_probe_labels",
        ],
    )
    def test_14_erasure_of_terrain_metadata_fails(self, field):
        packet = _packet(**{field: []})
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False

    def test_15_mutable_axiom_map_and_proof_obstruction_map_are_preserved(self):
        packet = _packet(
            mutable_axiom_map={"base_axiom": "reference", "variant_a": "shift one rule", "variant_b": "shift another rule"},
            proof_obstruction_map={"obstruction_a": "blocked path", "obstruction_b": "alternate block"},
            consistency_instability_candidates={"consistency_candidate": "local pocket", "instability_candidate": "global break"},
        )
        assert packet["mutable_axiom_map"]["variant_b"] == "shift another rule"
        assert packet["proof_obstruction_map"]["obstruction_a"] == "blocked path"
        assert validate_mutable_axiom_math_packet_v1(packet)["valid"] is True

    def test_16_relationship_to_algorithm_emergence_is_preserved(self):
        packet = _packet(
            relationship_to_algorithm_emergence={
                "role": "axiom_mutation_after_algorithm_emergence",
                "upstream_engine_name": "ALGORITHM_EMERGENCE_ENGINE",
                "preserves_candidate_algorithm_map": True,
                "preserves_operator_chain_candidates": True,
                "preserves_transformation_rule_candidates": True,
                "preserves_invariant_candidates": True,
                "preserves_invalidated_rule_history": True,
                "preserves_terrain_shift_context": True,
                "not_final_math_authority": True,
                "not_runtime_authority": True,
                "not_tool_authority": True,
                "not_provider_authority": True,
                "not_search_authority": True,
                "not_proof_authority": True,
                "not_public_claim_authority": True,
            }
        )
        assert packet["relationship_to_algorithm_emergence"]["upstream_engine_name"] == "ALGORITHM_EMERGENCE_ENGINE"
        assert validate_mutable_axiom_math_packet_v1(packet)["valid"] is True

    def test_17_cognitive_research_run_remains_envelope_only(self):
        packet = _packet()
        assert packet["relationship_to_cognitive_research_run"]["envelope_only"] is True
        packet["relationship_to_cognitive_research_run"]["not_engine_kernel"] = False
        assert validate_mutable_axiom_math_packet_v1(packet)["valid"] is False

    def test_18_json_safe_conversion_works(self):
        packet = _packet()
        safe = to_mutable_axiom_math_json_safe_v1(packet)
        json.dumps(safe)
        assert isinstance(safe, dict)
        assert isinstance(safe["mutable_axiom_map"], dict)

    def test_19_summaries_are_bounded_and_safe(self):
        packet = _packet()
        summary = summarize_mutable_axiom_math_packet_v1(packet)
        assert len(summary) < 900
        assert "secret" not in summary.lower()
        assert "theorem prover" not in summary.lower()

    def test_20_examples_are_synthetic_and_non_private(self):
        examples = build_initial_mutable_axiom_math_examples_v1()
        assert len(examples) >= 3
        for example in examples:
            assert str(example["artifact_reference"]).startswith("synthetic:")
            blob = json.dumps(example).lower()
            assert "secret" not in blob
            assert "hidden prompt" not in blob
            assert ".weslr" not in blob

    def test_21_source_import_has_no_forbidden_imports(self):
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
        assert "entity_graph" not in source_lower
        assert "os.system" not in source_lower
        assert "open(" not in source_lower

    def test_22_registry_and_boundary_sanity(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        boundary = get_cognitive_research_engine_boundary_v1("MUTABLE_AXIOM_MATH_ENGINE")
        assert registry["MUTABLE_AXIOM_MATH_ENGINE"]["engine_family"] == "math"
        assert validate_cognitive_research_engine_boundary_v1(boundary)["valid"] is True

    def test_23_blank_mapping_and_missing_summary_fields_fail_closed(self):
        packet = _packet(mutable_axiom_map={}, proof_obstruction_map={}, consistency_instability_candidates={})
        validation = validate_mutable_axiom_math_packet_v1(packet)
        assert validation["valid"] is False
