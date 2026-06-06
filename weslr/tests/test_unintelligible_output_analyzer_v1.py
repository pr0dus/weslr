#!/usr/bin/env python3
"""Focused tests for UNINTELLIGIBLE_OUTPUT_ANALYZER helpers v1."""

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
from weslr.unintelligible_output_analyzer import (
    build_initial_unintelligible_output_analysis_examples_v1,
    build_unintelligible_output_analysis_packet_v1,
    summarize_unintelligible_output_analysis_packet_v1,
    to_unintelligible_output_analysis_json_safe_v1,
    validate_unintelligible_output_analysis_packet_v1,
)

ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = ROOT / "weslr" / "unintelligible_output_analyzer.py"
EXPECTED_FIELDS = (
    "schema_version",
    "engine_name",
    "source_boundary_engine_name",
    "input_category",
    "artifact_reference",
    "artifact_summary",
    "candidate_translation_layers",
    "unmapped_token_metadata",
    "competing_interpretation_map",
    "ambiguity_map",
    "semantic_fracture_labels",
    "syntax_like_structure_labels",
    "required_new_notation_notes",
    "confidence_uncertainty_map",
    "translation_probes",
    "meaning_preservation_probes",
    "invalidated_interpretations",
    "next_interpretation_experiments",
    "relationship_to_raw_signal_cartographer",
    "relationship_to_cognitive_research_run",
    "safe_metadata",
    "denied_authority",
    "public_claim_status",
)


def _packet(**overrides):
    payload = {
        "input_category": "synthetic symbolic stream",
        "artifact_reference": "synthetic:unintelligible-output-analysis:artifact:test-001",
        "artifact_summary": "Synthetic layered fragment with unknown tokens and competing readings.",
        "candidate_translation_layers": ["layer-a", "layer-b"],
        "unmapped_token_metadata": [
            {"token": "??", "status": "unmapped", "note": "unknown token preserved"},
            {"token": "<fracture>", "status": "preserved", "note": "friction retained"},
        ],
        "competing_interpretation_map": {
            "reading_a": "candidate layer A preserves one translation path",
            "reading_b": "candidate layer B preserves a rival translation path",
        },
        "ambiguity_map": {"meaning": "open", "confidence": "bounded", "translation": "plural"},
        "semantic_fracture_labels": ["translation fracture", "meaning split"],
        "syntax_like_structure_labels": ["parse-like run", "phrase-like cluster"],
        "required_new_notation_notes": ["keep alternative notation for repeated unknown tokens"],
        "confidence_uncertainty_map": {"interpretation": "low", "translation": "mixed", "fracture": "tracked"},
        "translation_probes": ["propose layer A", "compare layer B"],
        "meaning_preservation_probes": ["retain token order", "preserve unknown symbols"],
        "invalidated_interpretations": ["plural readings retained"],
        "next_interpretation_experiments": ["try a new notation", "compare contradiction surface"],
        "relationship_to_raw_signal_cartographer": {
            "role": "interpretation_refinement_after_raw_signal",
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
        "safe_metadata": {
            "metadata_only": True,
            "json_safe": True,
            "non_public": True,
        },
        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
        "public_claim_status": "blocked_internal_only",
    }
    payload.update(overrides)
    return build_unintelligible_output_analysis_packet_v1(payload)


class TestUnintelligibleOutputAnalyzerV1:
    def test_01_valid_synthetic_packet_passes(self):
        packet = _packet()
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is True
        assert validation["violation_count"] == 0

    def test_02_all_required_fields_exist(self):
        packet = _packet()
        assert set(EXPECTED_FIELDS).issubset(packet.keys())

    def test_03_unknown_engine_fails(self):
        packet = _packet()
        packet["engine_name"] = "NOT_UNINTELLIGIBLE_OUTPUT_ANALYZER"
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_04_wrong_engine_fails(self):
        packet = _packet()
        packet["source_boundary_engine_name"] = "RAW_SIGNAL_CARTOGRAPHER"
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_05_missing_boundary_registry_entry_fails(self, monkeypatch):
        monkeypatch.setattr(
            "weslr.unintelligible_output_analyzer.build_cognitive_research_engine_boundary_registry_v1",
            lambda: {},
        )
        packet = _packet()
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    @pytest.mark.parametrize("field,value", [("artifact_summary", "raw private data should never appear"), ("input_category", "raw private data")])
    def test_06_raw_private_data_fails(self, field, value):
        packet = _packet(**{field: value})
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_07_secret_markers_fail(self):
        packet = _packet(artifact_summary="this contains a secret token=abc")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_08_hidden_system_prompt_markers_fail(self):
        packet = _packet(artifact_summary="hidden system prompt content")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_09_weslr_content_fails(self):
        packet = _packet(artifact_summary="contains .weslr contents")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_10_executable_and_live_tool_instructions_fail(self):
        packet = _packet(artifact_summary="please run this executable code-as-action and live tool instructions")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_11_provider_output_authority_claim_fails(self):
        packet = _packet(artifact_summary="provider/model output claimed as authority")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_12_dangerous_procedural_content_fails(self):
        packet = _packet(artifact_summary="dangerous procedural instructions with step-by-step exploit chain")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_13_massive_raw_artifact_pasted_instead_of_reference_fails(self):
        packet = _packet(artifact_reference="artifact:\n" + ("x" * 1200), artifact_summary="bounded summary")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_14_denied_authority_true_fails(self):
        denied = build_default_cognitive_research_denied_authority_v1()
        denied["runtime_authority"] = True
        packet = _packet(denied_authority=denied)
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_15_public_claim_drift_fails(self):
        packet = _packet(public_claim_status="breakthrough")
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_16_single_final_meaning_flattening_fails(self):
        packet = _packet(
            competing_interpretation_map={"reading_a": "final meaning"},
            invalidated_interpretations=["single final meaning rejected"],
        )
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is False

    def test_17_unknown_tokens_and_unmapped_metadata_are_preserved(self):
        packet = _packet(
            unmapped_token_metadata=[
                {"token": "??", "status": "unmapped"},
                {"token": "<gap>", "status": "preserved"},
            ]
        )
        assert packet["unmapped_token_metadata"][0]["token"] == "??"
        assert packet["unmapped_token_metadata"][1]["token"] == "<gap>"
        assert validate_unintelligible_output_analysis_packet_v1(packet)["valid"] is True

    def test_18_competing_interpretations_are_preserved(self):
        packet = _packet()
        assert set(packet["competing_interpretation_map"].keys()) == {"reading_a", "reading_b"}
        assert validate_unintelligible_output_analysis_packet_v1(packet)["valid"] is True

    def test_19_ambiguity_map_is_allowed(self):
        packet = _packet(ambiguity_map={"meaning": "open", "confidence": "bounded", "nested": {"a": 1}})
        validation = validate_unintelligible_output_analysis_packet_v1(packet)
        assert validation["valid"] is True
        assert packet["ambiguity_map"]["meaning"] == "open"

    def test_20_semantic_fracture_labels_are_preserved(self):
        packet = _packet(semantic_fracture_labels=["translation fracture", "meaning split", "notation crack"])
        assert packet["semantic_fracture_labels"][-1] == "notation crack"
        assert validate_unintelligible_output_analysis_packet_v1(packet)["valid"] is True

    def test_21_required_new_notation_notes_are_preserved(self):
        packet = _packet(required_new_notation_notes=["keep notation A", "keep notation B"])
        assert packet["required_new_notation_notes"][0] == "keep notation A"
        assert validate_unintelligible_output_analysis_packet_v1(packet)["valid"] is True

    def test_22_invalidated_interpretations_are_preserved(self):
        packet = _packet(invalidated_interpretations=["plural readings retained", "flattening rejected"])
        assert packet["invalidated_interpretations"][-1] == "flattening rejected"
        assert validate_unintelligible_output_analysis_packet_v1(packet)["valid"] is True

    def test_23_json_safe_conversion_works(self):
        packet = _packet()
        safe = to_unintelligible_output_analysis_json_safe_v1(packet)
        json.dumps(safe)
        assert isinstance(safe, dict)
        assert isinstance(safe["candidate_translation_layers"], list)

    def test_24_summaries_are_bounded_and_safe(self):
        packet = _packet()
        summary = summarize_unintelligible_output_analysis_packet_v1(packet)
        assert len(summary) < 900
        assert "secret" not in summary.lower()
        assert "generic summary" not in summary.lower()

    def test_25_examples_are_synthetic_and_non_private(self):
        examples = build_initial_unintelligible_output_analysis_examples_v1()
        assert len(examples) >= 3
        for example in examples:
            assert str(example["artifact_reference"]).startswith("synthetic:")
            blob = json.dumps(example).lower()
            assert "secret" not in blob
            assert "hidden prompt" not in blob
            assert ".weslr" not in blob

    def test_26_helper_source_has_no_forbidden_imports(self):
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

