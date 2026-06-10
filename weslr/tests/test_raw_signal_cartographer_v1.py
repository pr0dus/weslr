from __future__ import annotations

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
from weslr.raw_signal_cartographer import (
    ENGINE_FAMILY_V1,
    ENGINE_NAME_V1,
    build_initial_raw_signal_cartography_examples_v1,
    build_raw_signal_cartography_packet_v1,
    summarize_raw_signal_cartography_packet_v1,
    to_raw_signal_cartography_json_safe_v1,
    validate_raw_signal_cartography_packet_v1,
)

PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


def _packet(**overrides):
    base = {
        "input_artifact_ref": "artifact:raw-signal-001",
        "input_summary": "αβ :: αβ :: ??? repeated boundary tokens with operator-like arrows -> -> and compressed motifs.",
        "research_mode": "internal_exploration",
        "public_claim_status": "internal_candidate_only",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "candidate_generator_only",
    }
    base.update(overrides)
    return build_raw_signal_cartography_packet_v1(base)


def test_allowed_engine_identity_is_fixed():
    packet = _packet()
    assert packet["engine_name"] == ENGINE_NAME_V1
    assert packet["engine_family"] == ENGINE_FAMILY_V1
    assert packet["public_claim_status"] == "internal_candidate_only"
    assert packet["public_gap_card_status"] == "public_export_blocked"


def test_valid_symbolic_stream_summary_passes():
    packet = _packet()
    validation = validate_raw_signal_cartography_packet_v1(packet)
    summary = summarize_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["classification"]["cartography_state"] == "mapped"
    assert summary["summary_text"].startswith("Raw signal cartography:")


def test_valid_unintelligible_operator_sequence_summary_passes():
    packet = _packet(
        input_artifact_ref="artifact:raw-signal-002",
        input_summary="-> fold -> translate -> invert -> map -> compress; noisy but structured operator sequence.",
        research_mode="synthetic_test",
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["operator_like_transformations"]
    assert packet["segment_candidates"]


def test_valid_massive_artifact_reference_passes_without_raw_content():
    packet = _packet(
        input_artifact_ref="artifact:" + ("A" * 5000),
        input_summary="bounded summary only; no raw artifact stored.",
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert len(packet["input_artifact_ref"]) > 100
    assert packet["raw_artifact_included"] is False


def test_valid_noisy_artifact_with_motif_candidates_passes():
    packet = _packet(
        input_artifact_ref="artifact:raw-signal-003",
        input_summary="noise noise motif motif symbol symbol with delimiter :: :: and uncertain tail.",
        research_mode="synthetic_test",
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["motif_clusters"]
    assert packet["recurring_symbol_candidates"]


def test_valid_random_control_noise_hypothesis_passes():
    packet = _packet(
        input_artifact_ref="artifact:raw-signal-004",
        input_summary="random control: noise dominates while the structure is intentionally weak.",
        research_mode="synthetic_test",
        noise_hypotheses=[{"hypothesis_id": "noise-h1", "claim": "noise dominates", "evidence": ["random control"], "confidence": 58.0}],
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["noise_hypotheses"]


def test_valid_candidate_grammar_metadata_passes():
    packet = _packet(
        input_artifact_ref="artifact:raw-signal-005",
        input_summary="segment cluster compress map probe.",
        candidate_grammar={
            "grammar_id": "grammar-example",
            "terminals": ["segment", "cluster", "compress", "map", "probe"],
            "nonterminals": ["RUN", "REGION"],
            "rules": [{"lhs": "RUN", "rhs": ["REGION", "MOTIF", "PROBE"]}],
            "notes": "example grammar metadata",
        },
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["candidate_grammar"]["grammar_id"] == "grammar-example"


def test_valid_next_probes_and_rule_pressure_candidates_pass():
    packet = _packet(
        input_artifact_ref="artifact:raw-signal-006",
        input_summary="stable core; unstable tail; compare and falsify the boundary assumption.",
        next_probes=[{"probe_id": "probe-1", "probe": "compare the first and last regions", "purpose": "boundary test"}],
        rule_pressure_tests=[{"test_id": "pressure-1", "target_rule_or_operator": "segment map", "pressure_type": "counterexample", "mutated_input_summary": "swap delimiters", "expected_behavior": "structure survives", "observed_behavior": "pending", "result": "pending", "failure_mode": "none", "scope_update": "metadata_only"}],
    )
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["next_probes"]
    assert packet["rule_pressure_tests"]


def test_json_safe_copy_removes_unsafe_raw_fields():
    unsafe = deepcopy(_packet())
    unsafe["raw_artifact"] = "super secret raw artifact"
    unsafe["hidden_prompt"] = "system prompt leakage"
    safe = to_raw_signal_cartography_json_safe_v1(unsafe)
    assert "raw_artifact" not in safe
    assert "hidden_prompt" not in safe
    json.dumps(safe, sort_keys=True)


def test_summary_is_concise_and_does_not_expose_raw_private_text():
    packet = _packet(input_summary="raw private text with hidden system prompt")
    summary = summarize_raw_signal_cartography_packet_v1(packet)
    assert len(summary["summary_text"]) <= 320
    assert "raw private" not in summary["summary_text"].lower()
    assert "hidden prompt" not in summary["summary_text"].lower()


def test_packet_is_cognitive_research_run_compatible():
    packet = _packet()
    protocol_validation = protocol.validate_cognitive_research_run_v1(packet)
    assert protocol_validation["blocked"] is False
    assert protocol_validation["classification"] == ENGINE_NAME_V1


@pytest.mark.parametrize(
    "summary_text",
    [
        "raw private text hidden system prompt",
        "private mechanism text with raw private data",
    ],
)
def test_raw_private_text_fails(summary_text):
    packet = _packet(input_summary=summary_text)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert any("raw_private" in label or "hidden" in label for label in validation["violations"])


@pytest.mark.parametrize(
    "payload",
    [
        {"raw_artifact": "X" * 6000},
        {"input_summary": "X" * 1600},
    ],
)
def test_full_massive_artifact_inline_fails(payload):
    packet = _packet(**payload)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert any(label in validation["violations"] for label in ("full_massive_artifact_included_inline", "inline_summary_too_large"))


@pytest.mark.parametrize(
    "payload",
    [
        {"input_summary": "breakthrough proof solution certified public-ready"},
        {"input_summary": "official certification solved breakthrough"},
    ],
)
def test_public_breakthrough_claim_fails(payload):
    packet = _packet(**payload)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert any("public_claim" in label for label in validation["violations"])


@pytest.mark.parametrize(
    "authority_key",
    [
        "final_answer_generation_authority",
        "llm_authority",
        "runtime_wiring_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
        "persistence_database_write_authority",
        "tool_authority",
        "provider_authority",
    ],
)
def test_authority_claims_fail_closed(authority_key):
    denied = protocol.build_default_cognitive_research_denied_authority_v1()
    denied[authority_key] = True
    packet = _packet(denied_authority=denied)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False


@pytest.mark.parametrize(
    "summary_text",
    [
        ".weslr private artifact reference and internal details",
        "live ingestion from github rss lab notebook and network feed",
    ],
)
def test_runtime_provider_tool_persistence_dot_weslr_or_live_ingestion_implication_fails(summary_text):
    packet = _packet(input_summary=summary_text)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert any("ingestion" in label or "network" in label or "weslr" in label for label in validation["violations"])


def test_missing_artifact_ref_fails():
    packet = _packet(input_artifact_ref="")
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert "missing_safe_artifact_reference" in validation["violations"]


def test_missing_denied_authority_fails():
    packet = _packet(denied_authority=None)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert "missing_denied_authority" in validation["violations"]


@pytest.mark.parametrize(
    "metadata",
    [
        {"safe": False, "metadata_only": True},
        {"safe": True, "metadata_only": False},
        {"safe": True, "metadata_only": True, "perspicuity_is_gate": True},
    ],
)
def test_safe_metadata_and_perspicuity_gate_fail_closed(metadata):
    packet = _packet(safe_metadata=metadata)
    validation = validate_raw_signal_cartography_packet_v1(packet)
    assert validation["valid"] is False
    assert any("safe_metadata" in label or "perspicuity" in label for label in validation["violations"])


def test_initial_examples_cover_supported_surface():
    examples = build_initial_raw_signal_cartography_examples_v1()
    assert examples
    assert all(example["engine_name"] == ENGINE_NAME_V1 for example in examples)
    assert all(example["engine_family"] == ENGINE_FAMILY_V1 for example in examples)
    assert all(example["public_claim_status"] == "internal_candidate_only" for example in examples)
    assert all(example["public_gap_card_status"] == "public_export_blocked" for example in examples)


def test_protected_files_unchanged():
    for rel in PROTECTED_FILES:
        subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], check=True)
