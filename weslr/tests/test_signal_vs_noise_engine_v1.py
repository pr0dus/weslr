#!/usr/bin/env python3
"""Focused tests for SIGNAL_VS_NOISE_ENGINE helpers v1."""

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
from weslr.signal_vs_noise_engine import (
    build_initial_signal_vs_noise_examples_v1,
    build_signal_vs_noise_packet_v1,
    summarize_signal_vs_noise_packet_v1,
    to_signal_vs_noise_json_safe_v1,
    validate_signal_vs_noise_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "signal_vs_noise_engine.py"
EXPECTED_FIELDS = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "signal_noise_classification_map",
    "weak_signal_candidates",
    "pseudo_randomness_labels",
    "emerging_grammar_labels",
    "stable_signal_labels",
    "unstable_signal_labels",
    "artifact_effect_labels",
    "undecidable_region_labels",
    "confidence_uncertainty_map",
    "invalidation_notes",
    "next_probe_labels",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_unintelligible_output_analyzer",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)


def _packet(**overrides):
    payload = {
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:signal-vs-noise:artifact:test-001",
        "artifact_summary": "Synthetic signal/noise packet preserving weak structure and undecidable regions.",
        "signal_noise_classification_map": {
            "signal_candidates": ["candidate signal region"],
            "noise_candidates": ["candidate noise region"],
            "weak_signal_candidates": ["weak signal candidate"],
            "pseudo_randomness_labels": ["pseudo-randomness hint"],
            "artifact_effect_labels": ["artifact-effect candidate"],
            "undecidable_region_labels": ["undecidable band"],
        },
        "weak_signal_candidates": ["weak motif survives perturbation"],
        "pseudo_randomness_labels": ["pseudo-random cluster"],
        "emerging_grammar_labels": ["candidate grammar seed"],
        "stable_signal_labels": ["stable local signal"],
        "unstable_signal_labels": ["unstable local signal"],
        "artifact_effect_labels": ["artifact-effect signature"],
        "undecidable_region_labels": ["undecidable boundary band"],
        "confidence_uncertainty_map": {"signal": "bounded", "noise": "bounded", "artifact": "tracked", "undecidable": "tracked"},
        "invalidation_notes": ["binary-only flattening rejected"],
        "next_probe_labels": ["perturb candidate region", "compare persistence under one-axis shift"],
        "relationship_to_raw_signal_cartographer": {
            "role": "classification_pressure_after_raw_signal",
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
            "role": "classification_pressure_after_interpretation_preservation",
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
        "safe_metadata": {
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
        },
        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
        "public_claim_status": "blocked_internal_only",
    }
    payload.update(overrides)
    return build_signal_vs_noise_packet_v1(payload)


class TestSignalVsNoiseEngineV1:
    def test_01_valid_synthetic_packet_passes(self):
        packet = _packet()
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_02_all_required_fields_exist(self):
        packet = _packet()
        assert set(EXPECTED_FIELDS).issubset(packet.keys())

    def test_03_unknown_engine_fails(self):
        packet = _packet()
        packet["engine_name"] = "NOT_SIGNAL_VS_NOISE_ENGINE"
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_04_wrong_engine_fails(self):
        packet = _packet()
        packet["source_boundary_engine_name"] = "RAW_SIGNAL_CARTOGRAPHER"
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_05_missing_boundary_registry_entry_fails(self, monkeypatch):
        monkeypatch.setattr(
            "weslr.signal_vs_noise_engine.build_cognitive_research_engine_boundary_registry_v1",
            lambda: {},
        )
        packet = _packet()
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("field,value", [("artifact_summary", "raw private data should never appear"), ("input_category", "raw private data")])
    def test_06_raw_private_data_fails(self, field, value):
        packet = _packet(**{field: value})
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_07_secret_markers_fail(self):
        packet = _packet(artifact_summary="this contains a secret token=abc")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_08_hidden_system_prompt_markers_fail(self):
        packet = _packet(artifact_summary="hidden system prompt content")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_09_weslr_content_fails(self):
        packet = _packet(artifact_summary="contains .weslr contents")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_10_executable_and_live_tool_instructions_fail(self):
        packet = _packet(artifact_summary="please run this executable code-as-action and live tool instructions")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_11_provider_output_authority_claim_fails(self):
        packet = _packet(artifact_summary="provider/model output claimed as authority")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_12_dangerous_procedural_content_fails(self):
        packet = _packet(artifact_summary="dangerous procedural instructions with step-by-step exploit chain")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_13_massive_raw_artifact_pasted_instead_of_reference_fails(self):
        packet = _packet(artifact_reference="artifact:\n" + ("x" * 1200), artifact_summary="bounded summary")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_14_denied_authority_true_fails(self):
        denied = build_default_cognitive_research_denied_authority_v1()
        denied["runtime_authority"] = True
        packet = _packet(denied_authority=denied)
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_15_public_claim_drift_fails(self):
        packet = _packet(public_claim_status="breakthrough")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_16_binary_only_flattening_fails(self):
        packet = _packet(
            signal_noise_classification_map={
                "signal_candidates": ["signal only"],
                "noise_candidates": ["noise only"],
                "weak_signal_candidates": ["binary only"],
                "pseudo_randomness_labels": ["pseudo-random"],
                "artifact_effect_labels": ["artifact-effect"],
                "undecidable_region_labels": ["undecidable"],
            }
        )
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_17_generic_cleanup_flattening_fails(self):
        packet = _packet(artifact_summary="generic cleanup assistant should simplify to noise deletion")
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is False

    def test_18_weak_signals_are_preserved(self):
        packet = _packet(weak_signal_candidates=["weak motif survives perturbation", "cluster persistence hint"])
        assert packet["weak_signal_candidates"][0].startswith("weak motif")
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_19_pseudo_randomness_labels_are_preserved(self):
        packet = _packet(pseudo_randomness_labels=["pseudo-random cluster", "random-looking local texture"])
        assert packet["pseudo_randomness_labels"][-1] == "random-looking local texture"
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_20_emerging_grammar_labels_are_preserved(self):
        packet = _packet(emerging_grammar_labels=["candidate grammar seed", "local rule hint"])
        assert packet["emerging_grammar_labels"][1] == "local rule hint"
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_21_artifact_effect_labels_are_preserved(self):
        packet = _packet(artifact_effect_labels=["artifact-effect signature", "measurement artifact signature"])
        assert packet["artifact_effect_labels"][-1] == "measurement artifact signature"
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_22_undecidable_regions_are_preserved(self):
        packet = _packet(undecidable_region_labels=["undecidable boundary band", "still undecidable"])
        assert packet["undecidable_region_labels"][-1] == "still undecidable"
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_23_confidence_uncertainty_map_is_allowed(self):
        packet = _packet(confidence_uncertainty_map={"signal": "low", "noise": "high", "artifact": "tracked", "undecidable": {"region": "held open"}})
        validation = validate_signal_vs_noise_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["confidence_uncertainty_map"]["signal"] == "low"

    def test_24_invalidation_notes_are_preserved(self):
        packet = _packet(invalidation_notes=["candidate rejected", "binary-only flattening rejected"])
        assert packet["invalidation_notes"][-1] == "binary-only flattening rejected"
        assert validate_signal_vs_noise_packet_v1(packet)["valid"] is True

    def test_25_json_safe_conversion_works(self):
        packet = _packet()
        safe = to_signal_vs_noise_json_safe_v1(packet)
        json.dumps(safe)
        assert isinstance(safe, dict)
        assert isinstance(safe["weak_signal_candidates"], list)

    def test_26_summaries_are_bounded_and_safe(self):
        packet = _packet()
        summary = summarize_signal_vs_noise_packet_v1(packet)
        assert len(summary) < 900
        assert "secret" not in summary.lower()
        assert "generic cleanup" not in summary.lower()

    def test_27_examples_are_synthetic_and_non_private(self):
        examples = build_initial_signal_vs_noise_examples_v1()
        assert len(examples) >= 3
        for example in examples:
            assert str(example["artifact_reference"]).startswith("synthetic:")
            blob = json.dumps(example).lower()
            assert "secret" not in blob
            assert "hidden prompt" not in blob
            assert ".weslr" not in blob

    def test_28_helper_source_has_no_forbidden_imports(self):
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
