#!/usr/bin/env python3
"""Focused tests for RAW_SIGNAL_CARTOGRAPHER helpers v1."""

from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

from weslr.cognitive_research_engine_boundaries import (
    build_cognitive_research_engine_boundary_registry_v1,
    get_cognitive_research_engine_boundary_v1,
    validate_cognitive_research_engine_boundary_v1,
)
from weslr.cognitive_research_protocol import build_default_cognitive_research_denied_authority_v1
from weslr.raw_signal_cartographer import (
    build_initial_raw_signal_cartography_examples_v1,
    build_raw_signal_cartography_packet_v1,
    summarize_raw_signal_cartography_packet_v1,
    to_raw_signal_cartography_json_safe_v1,
    validate_raw_signal_cartography_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "raw_signal_cartographer.py"
EXPECTED_FIELDS = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "terrain_primitives",
    "motif_candidates",
    "weak_signal_labels",
    "stable_region_labels",
    "unstable_region_labels",
    "noise_region_labels",
    "boundary_region_labels",
    "candidate_grammar_labels",
    "operator_transformation_labels",
    "uncertainty_map",
    "probe_suggestions",
    "invalidation_notes",
    "compression_summary",
    "next_experiment_labels",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)


def _packet(**overrides):
    payload = {
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:raw-signal-cartography:artifact:test-001",
        "artifact_summary": "Synthetic terrain packet preserving motifs, weak signals, and invalidation notes.",
        "terrain_primitives": ["glyphs", "fragments", "clusters", "edges"],
        "motif_candidates": ["repeat cluster"],
        "weak_signal_labels": ["weak motif"],
        "stable_region_labels": ["stable zone"],
        "unstable_region_labels": ["unstable zone"],
        "noise_region_labels": ["noise cluster"],
        "boundary_region_labels": ["transition band"],
        "candidate_grammar_labels": ["segment", "cluster", "probe"],
        "operator_transformation_labels": ["compress", "trace", "label"],
        "uncertainty_map": {"terrain": "unknown", "confidence": "bounded"},
        "probe_suggestions": ["perturb one axis", "compare local change"],
        "invalidation_notes": ["flattening rejected"],
        "compression_summary": "Bounded terrain metadata with preserved uncertainty and invalidation history.",
        "next_experiment_labels": ["probe boundary shift"],
        "safe_metadata": {"metadata_only": True, "json_safe": True, "non_public": True},
        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
        "public_claim_status": "blocked_internal_only",
    }
    payload.update(overrides)
    return build_raw_signal_cartography_packet_v1(payload)


class TestRawSignalCartographerV1:
    def test_01_valid_synthetic_packet_passes(self):
        packet = _packet()
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_02_all_required_fields_exist(self):
        packet = _packet()
        assert set(EXPECTED_FIELDS).issubset(packet.keys())

    def test_03_unknown_engine_fails(self):
        packet = _packet()
        packet["engine_name"] = "NOT_RAW_SIGNAL_CARTOGRAPHER"
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_04_wrong_engine_fails(self):
        packet = _packet()
        packet["source_boundary_engine_name"] = "UNINTELLIGIBLE_OUTPUT_ANALYZER"
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_05_missing_boundary_registry_entry_fails(self, monkeypatch):
        monkeypatch.setattr(
            "weslr.raw_signal_cartographer.build_cognitive_research_engine_boundary_registry_v1",
            lambda: {},
        )
        packet = _packet()
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("field,value", [("artifact_summary", "raw private data should never appear"), ("input_category", "raw private data")])
    def test_06_raw_private_data_fails(self, field, value):
        packet = _packet(**{field: value})
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_07_secret_markers_fail(self):
        packet = _packet(artifact_summary="this contains a secret token=abc")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_08_hidden_system_prompt_markers_fail(self):
        packet = _packet(artifact_summary="hidden system prompt content")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_09_weslr_content_fails(self):
        packet = _packet(artifact_summary="contains .weslr contents")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_10_executable_and_live_tool_instructions_fail(self):
        packet = _packet(artifact_summary="please run this executable code-as-action and live tool instructions")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_11_provider_output_authority_claim_fails(self):
        packet = _packet(artifact_summary="provider/model output claimed as authority")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_12_dangerous_procedural_content_fails(self):
        packet = _packet(artifact_summary="dangerous procedural instructions with step-by-step exploit chain")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_13_massive_raw_artifact_pasted_instead_of_reference_fails(self):
        packet = _packet(artifact_reference="artifact:\n" + ("x" * 1200), artifact_summary="bounded summary")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_14_denied_authority_true_fails(self):
        denied = build_default_cognitive_research_denied_authority_v1()
        denied["runtime_authority"] = True
        packet = _packet(denied_authority=denied)
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_15_public_claim_drift_fails(self):
        packet = _packet(public_claim_status="breakthrough")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_16_generic_summary_flattening_fails(self):
        packet = _packet(artifact_summary="generic summary of all terrain", compression_summary="generic assistant summary")
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is False

    def test_17_terrain_primitives_are_preserved(self):
        packet = _packet(terrain_primitives=["glyphs", "gaps", "clusters", "edges"])
        assert packet["terrain_primitives"] == ["glyphs", "gaps", "clusters", "edges"]
        assert validate_raw_signal_cartography_packet_v1(packet)["valid"] is True

    def test_18_motif_candidates_are_preserved(self):
        packet = _packet(motif_candidates=["repeat cluster", "boundary tension"])
        assert packet["motif_candidates"] == ["repeat cluster", "boundary tension"]
        assert validate_raw_signal_cartography_packet_v1(packet)["valid"] is True

    def test_19_unknown_terrain_and_uncertainty_map_are_allowed(self):
        packet = _packet(uncertainty_map={"terrain": "unknown", "novel": "yes", "nested": {"a": 1}})
        validation = validate_raw_signal_cartography_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["uncertainty_map"]["terrain"] == "unknown"

    def test_20_invalidation_notes_are_preserved(self):
        packet = _packet(invalidation_notes=["flattening rejected", "candidate invalidated for loss of texture"])
        assert packet["invalidation_notes"][-1] == "candidate invalidated for loss of texture"
        assert validate_raw_signal_cartography_packet_v1(packet)["valid"] is True

    def test_21_json_safe_conversion_works(self):
        packet = _packet()
        safe = to_raw_signal_cartography_json_safe_v1(packet)
        json.dumps(safe)
        assert isinstance(safe, dict)
        assert isinstance(safe["terrain_primitives"], list)

    def test_22_summaries_are_bounded_and_safe(self):
        packet = _packet()
        summary = summarize_raw_signal_cartography_packet_v1(packet)
        assert len(summary) < 900
        assert "secret" not in summary.lower()
        assert "provider/model output" not in summary.lower()

    def test_23_examples_are_synthetic_and_non_private(self):
        examples = build_initial_raw_signal_cartography_examples_v1()
        assert len(examples) >= 3
        for example in examples:
            assert str(example["artifact_reference"]).startswith("synthetic:")
            blob = json.dumps(example).lower()
            assert "secret" not in blob
            assert "hidden prompt" not in blob
            assert ".weslr" not in blob

    def test_24_helper_source_has_no_forbidden_imports(self):
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

    def test_25_boundary_helper_and_protocol_integration_still_pass(self):
        registry = build_cognitive_research_engine_boundary_registry_v1()
        boundary = get_cognitive_research_engine_boundary_v1("RAW_SIGNAL_CARTOGRAPHER")
        assert validate_cognitive_research_engine_boundary_v1(boundary)["valid"] is True
        assert "RAW_SIGNAL_CARTOGRAPHER" in registry
        packet = _packet()
        assert validate_raw_signal_cartography_packet_v1(packet)["valid"] is True

