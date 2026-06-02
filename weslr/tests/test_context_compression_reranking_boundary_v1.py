from __future__ import annotations

import ast
import builtins
import inspect
import json
import sys
from pathlib import Path

import pytest

import weslr.context_compression_reranking_boundary as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_context_compression_examples_v1()
        if item["context_packet_id"] == example_id
    )


def _imported_module_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "context_compression_reranking_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules

    imported = _imported_module_names(inspect.getsource(mod))
    for hint in PROTECTED_MODULE_HINTS:
        assert hint not in imported


def test_module_does_not_read_write_or_touch_weslr(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _blocked(*args, **kwargs):
        calls.append("io")
        raise AssertionError("file I/O not allowed")

    monkeypatch.setattr(builtins, "open", _blocked)
    monkeypatch.setattr(Path, "read_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "write_text", _blocked, raising=False)
    monkeypatch.setattr(Path, "open", _blocked, raising=False)

    packet = mod.build_context_compression_packet_v1(
        context_packet_id="io_guard",
        query_summary="guard",
        context_units=[
            {
                "context_unit_id": "u1",
                "context_unit_type": "claim_context",
                "summary": "safe",
                "public_safe": True,
            }
        ],
        context_budget_status="within_budget",
    )
    assert packet["context_packet_id"] == "io_guard"
    assert calls == []


def test_builds_deterministic_context_compression_packet() -> None:
    packet_a = mod.build_context_compression_packet_v1(
        context_packet_id="pkt_1",
        query_summary="Rank safe evidence",
        context_units=[
            {
                "context_unit_id": "u1",
                "context_unit_type": "claim_context",
                "summary": "claim",
                "claim_relevance": "high",
                "access_status": "access_allowed",
                "public_safe": True,
            }
        ],
        compression_mode="metadata_only",
        reranking_mode="claim_relevance_first",
        context_budget_status="within_budget",
    )
    packet_b = mod.build_context_compression_packet_v1(
        context_packet_id="pkt_1",
        query_summary="Rank safe evidence",
        context_units=[
            {
                "context_unit_id": "u1",
                "context_unit_type": "claim_context",
                "summary": "claim",
                "claim_relevance": "high",
                "access_status": "access_allowed",
                "public_safe": True,
            }
        ],
        compression_mode="metadata_only",
        reranking_mode="claim_relevance_first",
        context_budget_status="within_budget",
    )
    assert packet_a == packet_b


def test_selects_context_units() -> None:
    packet = _example("energy_signal_ranked_by_freshness_and_deadline")
    selected = mod.select_context_units_v1(packet)
    assert [unit["context_unit_id"] for unit in selected] == ["signal:8a", "signal:8b"]


def test_compresses_context_units_metadata_only() -> None:
    packet = _example("private_project_memory_summary_only")
    compressed = mod.compress_context_units_v1(packet)
    assert compressed[0]["context_unit_id"] == "memory:6"
    assert "raw_content" not in compressed[0]
    assert compressed[0]["summary"] == "private project memory summary"


def test_ranks_context_units_metadata_only() -> None:
    packet = _example("energy_signal_ranked_by_freshness_and_deadline")
    ranked = mod.rank_context_units_v1(packet)
    assert [unit["context_unit_id"] for unit in ranked] == ["signal:8a", "signal:8b"]


def test_validates_normal_packet() -> None:
    assert mod.validate_context_compression_packet_v1(_example("fresh_supported_claim_selected_citation_preserved")) is True


def test_summarizes_packet() -> None:
    packet = _example("fresh_supported_claim_selected_citation_preserved")
    summary = mod.summarize_context_compression_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["context_packet_id"] == packet["context_packet_id"]
    assert summary["compression_mode"] == "citation_preserving_summary"
    assert summary["reranking_mode"] == "claim_relevance_first"


def test_json_safe_export_works() -> None:
    value = {"b": {"nested": {1, 2}}, "a": ("x", "y")}
    safe = mod.to_context_compression_json_safe_v1(value)
    json.dumps(safe)
    assert safe == {"a": ["x", "y"], "b": {"nested": [1, 2]}}


def test_all_initial_examples_exist() -> None:
    ids = {item["context_packet_id"] for item in mod.build_initial_context_compression_examples_v1()}
    assert ids == {
        "fresh_supported_claim_selected_citation_preserved",
        "stale_source_compressed_with_freshness_caveat",
        "contradictory_sources_both_retained",
        "access_restricted_source_dropped_from_public_context",
        "poison_quarantined_source_blocked_from_context",
        "private_project_memory_summary_only",
        "api_key_context_blocked_not_summarized",
        "energy_signal_ranked_by_freshness_and_deadline",
        "public_claim_context_blocked_not_public_safe",
        "long_context_budget_exceeded_ask_clarification",
    }


def test_no_initial_example_grants_runtime_authority() -> None:
    assert all(not item["runtime_authority"] for item in mod.build_initial_context_compression_examples_v1())


def test_no_initial_example_writes_state() -> None:
    assert all(not item["writes_state"] for item in mod.build_initial_context_compression_examples_v1())


def test_no_initial_example_calls_model_provider() -> None:
    assert all(not item["model_provider_used"] for item in mod.build_initial_context_compression_examples_v1())


def test_no_initial_example_allows_public_claim_authority() -> None:
    assert all(not item["public_claim_allowed"] for item in mod.build_initial_context_compression_examples_v1())


def test_no_initial_example_allows_proof_claim() -> None:
    assert all(not item["proof_claim_allowed"] for item in mod.build_initial_context_compression_examples_v1())


def test_no_initial_example_claims_learning() -> None:
    assert all(not item["learning_claimed"] for item in mod.build_initial_context_compression_examples_v1())


@pytest.mark.parametrize(
    "packet,match",
    [
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "context_units": [{"context_unit_id": "u", "context_unit_type": "mystery_context"}]}, "unknown_context_unit_type"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "compression_mode": "mystery"}, "unknown_compression_mode"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "reranking_mode": "mystery"}, "unknown_reranking_mode"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "context_budget_status": "mystery"}, "unknown_context_budget_status"),
        ({**_example("contradictory_sources_both_retained"), "contradictions_preserved": False}, "contradictions_not_preserved"),
        ({**_example("access_restricted_source_dropped_from_public_context"), "access_restrictions_preserved": False}, "access_restrictions_not_preserved"),
        ({**_example("poison_quarantined_source_blocked_from_context"), "poison_flags_preserved": False, "safe_metadata": {"public_context": False}}, "poison_flags_not_preserved"),
        ({**_example("stale_source_compressed_with_freshness_caveat"), "freshness_refs_preserved": False}, "freshness_caveats_not_preserved"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "citation_refs_preserved": False}, "citation_refs_not_preserved_when_required"),
        ({**_example("access_restricted_source_dropped_from_public_context"), "safe_metadata": {"public_context": True}, "selected_context_units": [{"context_unit_id": "source:4b", "context_unit_type": "source_summary_context", "summary": "restricted source", "access_status": "access_restricted", "public_safe": False}]}, "selected_private_or_access_restricted_context_not_public_safe"),
        ({**_example("api_key_context_blocked_not_summarized"), "selected_context_units": [{"context_unit_id": "chunk:7", "context_unit_type": "chunk_summary_context", "api_key": "sk-test-123"}]}, "forbidden_field_present:api_key"),
        ({**_example("long_context_budget_exceeded_ask_clarification"), "recommended_next_check": "none"}, "over_budget_requires_defer_or_clarification"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "runtime_authority": True}, "runtime_authority_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "writes_state": True}, "writes_state_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "model_provider_used": True}, "model_provider_used_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "public_claim_allowed": True}, "public_claim_allowed_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "proof_claim_allowed": True}, "proof_claim_allowed_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "learning_claimed": True}, "learning_claimed_must_be_false"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "hidden_prompt": "x"}, "forbidden_field_present:hidden_prompt"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "raw_private": "x"}, "forbidden_field_present:raw_private"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "secret_token": "x"}, "forbidden_field_present:secret_token"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "query_summary": "hallucination elimination"}, "forbidden_claim_phrase_present"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "query_summary": "public readiness"}, "forbidden_claim_phrase_present"),
        ({**_example("fresh_supported_claim_selected_citation_preserved"), "query_summary": "proof certainty"}, "forbidden_claim_phrase_present"),
    ],
)
def test_validation_fails_specific_cases(packet: dict[str, object], match: str) -> None:
    with pytest.raises(mod.ValidationError, match=match):
        mod.validate_context_compression_packet_v1(packet)


def test_validation_fails_when_public_context_contains_private_or_restricted_evidence() -> None:
    packet = {
        **_example("access_restricted_source_dropped_from_public_context"),
        "safe_metadata": {"public_context": True},
        "selected_context_units": [
            {"context_unit_id": "source:4b", "context_unit_type": "source_summary_context", "summary": "restricted source", "access_status": "access_restricted", "public_safe": False},
        ],
    }
    with pytest.raises(mod.ValidationError, match="selected_private_or_access_restricted_context_not_public_safe"):
        mod.validate_context_compression_packet_v1(packet)


def test_module_does_not_import_or_call_protected_runtime_files(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_calls: list[str] = []

    def _sentinel(*args, **kwargs):
        blocked_calls.append("hit")
        raise AssertionError("protected runtime file access not allowed")

    monkeypatch.setattr(builtins, "open", _sentinel)
    monkeypatch.setattr(Path, "read_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "write_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "open", _sentinel, raising=False)

    packet = mod.build_context_compression_packet_v1(
        context_packet_id="protected_guard",
        query_summary="guard",
        context_units=[
            {
                "context_unit_id": "u1",
                "context_unit_type": "claim_context",
                "summary": "safe",
                "public_safe": True,
            }
        ],
        context_budget_status="within_budget",
    )
    assert packet["context_packet_id"] == "protected_guard"
    assert blocked_calls == []
