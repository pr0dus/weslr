from __future__ import annotations

import ast
import builtins
import inspect
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.self_rag_evidence_loop_boundary as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_self_rag_loop_examples_v1()
        if item["self_rag_loop_packet_id"] == example_id
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
    assert mod.HELPER_TYPE_V1 == "self_rag_evidence_loop_boundary_v1"
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

    packet = mod.build_self_rag_loop_packet_v1(
        self_rag_loop_packet_id="io_guard",
        query_summary="Explain the concept without retrieval.",
        initial_query_class="general_reasoning_query",
        initial_routing_target="source_evidence_graph_lookup",
        loop_stage="gap_detection",
        loop_iteration_count=0,
        max_iterations=2,
        visited_routing_targets=["source_evidence_graph_lookup"],
        evidence_candidates=[],
        grounding_status="more_evidence_needed",
        citation_readiness="more_evidence_needed",
        context_budget_status="within_budget",
        reroute_recommended=False,
        reroute_target="no_reroute_stop",
        stop_reason="more evidence needed",
        fallback_behavior="ask_clarifying_question",
        recommended_answer_action="ask_clarifying_question",
        recommended_next_check="ask the user for the missing source or scope",
    )
    assert packet["self_rag_loop_packet_id"] == "io_guard"
    assert calls == []


def test_builds_deterministic_self_rag_loop_packet() -> None:
    packet_a = mod.build_self_rag_loop_packet_v1(
        self_rag_loop_packet_id="pkt_1",
        query_summary="Explain the difference between supported and unsupported evidence.",
        initial_query_class="general_reasoning_query",
        initial_routing_target="source_evidence_graph_lookup",
        loop_stage="gap_detection",
        loop_iteration_count=0,
        max_iterations=2,
        visited_routing_targets=["source_evidence_graph_lookup"],
        evidence_candidates=[
            {
                "evidence_ref": "evidence:1",
                "candidate_status": "accepted",
                "source_type": "source_graph",
                "access_status": "access_allowed",
                "privacy_status": "public",
                "poison_status": "clean",
                "freshness_status": "current",
                "summary": "grounded evidence",
                "citation_required": False,
                "public_safe": True,
            }
        ],
        accepted_evidence_refs=["evidence:1"],
        grounding_status="evidence_sufficient",
        citation_readiness="evidence_sufficient",
        context_budget_status="within_budget",
        reroute_recommended=False,
        reroute_target="no_reroute_stop",
        stop_reason="sufficient evidence",
        fallback_behavior="use_existing_graph_only",
        recommended_answer_action="use_existing_graph_only",
        recommended_next_check="no additional evidence check needed",
        safe_metadata={"example_name": "deterministic_packet"},
    )
    packet_b = mod.build_self_rag_loop_packet_v1(
        self_rag_loop_packet_id="pkt_1",
        query_summary="Explain the difference between supported and unsupported evidence.",
        initial_query_class="general_reasoning_query",
        initial_routing_target="source_evidence_graph_lookup",
        loop_stage="gap_detection",
        loop_iteration_count=0,
        max_iterations=2,
        visited_routing_targets=["source_evidence_graph_lookup"],
        evidence_candidates=[
            {
                "evidence_ref": "evidence:1",
                "candidate_status": "accepted",
                "source_type": "source_graph",
                "access_status": "access_allowed",
                "privacy_status": "public",
                "poison_status": "clean",
                "freshness_status": "current",
                "summary": "grounded evidence",
                "citation_required": False,
                "public_safe": True,
            }
        ],
        accepted_evidence_refs=["evidence:1"],
        grounding_status="evidence_sufficient",
        citation_readiness="evidence_sufficient",
        context_budget_status="within_budget",
        reroute_recommended=False,
        reroute_target="no_reroute_stop",
        stop_reason="sufficient evidence",
        fallback_behavior="use_existing_graph_only",
        recommended_answer_action="use_existing_graph_only",
        recommended_next_check="no additional evidence check needed",
        safe_metadata={"example_name": "deterministic_packet"},
    )
    assert packet_a == packet_b
    assert packet_a["initial_routing_target"] == "source_evidence_graph_lookup"


def test_evaluates_evidence_sufficient_first_pass() -> None:
    packet = _example("evidence_sufficient_first_pass")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_sufficient"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"


def test_selects_reroute_for_missing_citation_source() -> None:
    packet = _example("missing_citation_source_triggers_one_reroute")
    assert mod.select_self_rag_reroute_v1(packet) == "source_evidence_graph_lookup"
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_missing"


def test_stale_support_reroutes_then_caveats_when_unavailable() -> None:
    packet = _example("stale_support_reroute_then_caveat_when_unavailable")
    assert mod.select_self_rag_reroute_v1(packet) == "future_web_search"
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_stale"
    assert packet["fallback_behavior"] == "answer_with_caveat"


def test_contradictory_evidence_preserved_no_forced_winner() -> None:
    packet = _example("contradictory_evidence_preserved_no_forced_winner")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_contradicted"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"
    assert "contradiction" in packet["stop_reason"]


def test_access_blocked_source_stops_loop() -> None:
    packet = _example("access_blocked_source_stops_loop")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_access_blocked"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"


def test_poison_blocked_source_stops_loop() -> None:
    packet = _example("poison_blocked_source_stops_loop")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "evidence_poison_blocked"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"


def test_public_claim_unsupported_after_max_iterations_refused() -> None:
    packet = _example("public_claim_unsupported_after_max_iterations_refused")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "refuse_unsupported"
    assert packet["fallback_behavior"] == "refuse_public_claim"


def test_currentness_sensitive_query_deferred_no_current_source() -> None:
    packet = _example("currentness_sensitive_query_deferred_no_current_source")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "defer_until_retrieval_available"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"


def test_context_budget_exceeded_recommends_compression_or_defer() -> None:
    packet = _example("context_budget_exceeded_compression_recommended")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "more_evidence_needed"
    assert "compress" in packet["recommended_next_check"] or "defer" in packet["recommended_next_check"]


def test_repeated_failed_reroute_path_stops_loop() -> None:
    packet = _example("repeated_failed_reroute_path_stops_loop")
    assert mod.evaluate_self_rag_evidence_state_v1(packet) == "more_evidence_needed"
    assert mod.select_self_rag_reroute_v1(packet) == "no_reroute_stop"


def test_normal_packet_validates_summarizes_and_exports_json_safe() -> None:
    packet = _example("evidence_sufficient_first_pass")
    assert mod.validate_self_rag_loop_packet_v1(packet) is True

    summary = mod.summarize_self_rag_loop_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["self_rag_loop_packet_id"] == "evidence_sufficient_first_pass"
    assert summary["evidence_candidate_count"] == 1
    assert json.dumps(mod.to_self_rag_loop_json_safe_v1(summary))


def test_all_initial_examples_exist_and_have_no_authority_flags() -> None:
    examples = mod.build_initial_self_rag_loop_examples_v1()
    names = {item["self_rag_loop_packet_id"] for item in examples}

    assert len(examples) == 10
    assert {
        "evidence_sufficient_first_pass",
        "missing_citation_source_triggers_one_reroute",
        "stale_support_reroute_then_caveat_when_unavailable",
        "contradictory_evidence_preserved_no_forced_winner",
        "access_blocked_source_stops_loop",
        "poison_blocked_source_stops_loop",
        "public_claim_unsupported_after_max_iterations_refused",
        "currentness_sensitive_query_deferred_no_current_source",
        "context_budget_exceeded_compression_recommended",
        "repeated_failed_reroute_path_stops_loop",
    } == names

    for item in examples:
        assert item["runtime_authority"] is False
        assert item["writes_state"] is False
        assert item["model_provider_used"] is False
        assert item["public_claim_allowed"] is False
        assert item["proof_claim_allowed"] is False
        assert item["learning_claimed"] is False


@pytest.mark.parametrize(
    ("mutation_label", "mutate"),
    [
        ("unknown_loop_stage", lambda p: p.__setitem__("loop_stage", "unknown_stage")),
        ("unknown_loop_outcome", lambda p: p.__setitem__("grounding_status", "unknown_outcome_value")),
        ("unknown_fallback_behavior", lambda p: p.__setitem__("fallback_behavior", "unknown_behavior")),
        ("unknown_reroute_target", lambda p: p.__setitem__("reroute_target", "unknown_target")),
        ("iteration_count_greater_than_max", lambda p: (p.__setitem__("loop_iteration_count", 3), p.__setitem__("max_iterations", 2))),
        ("reroute_recommended_when_max_reached", lambda p: (p.__setitem__("loop_iteration_count", 2), p.__setitem__("max_iterations", 2), p.__setitem__("reroute_recommended", True), p.__setitem__("reroute_target", "same_route_once"))),
        ("repeated_failed_route_loop", lambda p: (p.__setitem__("loop_iteration_count", 1), p.__setitem__("max_iterations", 2), p.__setitem__("reroute_recommended", True), p.__setitem__("reroute_target", "source_evidence_graph_lookup"), p.__setitem__("visited_routing_targets", ["source_evidence_graph_lookup", "source_evidence_graph_lookup"]))),
        ("accepted_access_blocked_evidence", lambda p: (p.__setitem__("accepted_evidence_refs", ["evidence:block"]), p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "evidence_ref": "evidence:block", "candidate_status": "access_blocked", "access_status": "access_restricted"}))),
        ("accepted_poison_blocked_evidence", lambda p: (p.__setitem__("accepted_evidence_refs", ["evidence:block"]), p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "evidence_ref": "evidence:block", "candidate_status": "poison_blocked", "poison_status": "poisoned"}))),
        ("accepted_privacy_blocked_evidence", lambda p: (p.__setitem__("accepted_evidence_refs", ["evidence:block"]), p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "evidence_ref": "evidence:block", "candidate_status": "privacy_blocked", "privacy_status": "private"}))),
        ("public_claim_from_private_evidence", lambda p: (p["safe_metadata"].__setitem__("public_claim_requested", True), p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "privacy_status": "private", "access_status": "access_restricted"}))),
        ("hidden_unresolved_contradiction", lambda p: (p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "candidate_status": "contradicted", "contradiction_present": True}), p.__setitem__("grounding_status", "evidence_sufficient"))),
        ("stale_evidence_treated_current", lambda p: (p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "freshness_status": "stale", "candidate_status": "stale"}), p.__setitem__("grounding_status", "evidence_sufficient"), p.__setitem__("recommended_answer_action", "use_existing_graph_only"), p.__setitem__("stop_reason", "sufficient evidence"))),
        ("citation_required_without_refs", lambda p: (p["safe_metadata"].__setitem__("citation_required", True), p.__setitem__("accepted_evidence_refs", []), p["evidence_candidates"].__setitem__(0, {**p["evidence_candidates"][0], "citation_required": True}))),
        ("over_budget_without_compression_defer_or_clarification", lambda p: (p.__setitem__("context_budget_status", "over_budget"), p.__setitem__("recommended_answer_action", "use_existing_graph_only"), p.__setitem__("recommended_next_check", "none"))),
        ("runtime_authority_true", lambda p: p.__setitem__("runtime_authority", True)),
        ("writes_state_true", lambda p: p.__setitem__("writes_state", True)),
        ("model_provider_used_true", lambda p: p.__setitem__("model_provider_used", True)),
        ("public_claim_allowed_true", lambda p: p.__setitem__("public_claim_allowed", True)),
        ("proof_claim_allowed_true", lambda p: p.__setitem__("proof_claim_allowed", True)),
        ("learning_claimed_true", lambda p: p.__setitem__("learning_claimed", True)),
        ("forbidden_hidden_prompt_field", lambda p: p.__setitem__("hidden_prompt", "x")),
        ("forbidden_raw_private_field", lambda p: p.__setitem__("raw_private", "x")),
        ("forbidden_secret_field", lambda p: p.__setitem__("secret_token", "x")),
        ("forbidden_token_field", lambda p: p.__setitem__("token", "x")),
        ("forbidden_key_field", lambda p: p.__setitem__("api_key", "x")),
        ("forbidden_claim_phrase_marker", lambda p: p.__setitem__("query_summary", "hallucination elimination public readiness proof certainty")),
    ],
)
def test_validation_failures_cover_boundary_rules(mutation_label, mutate) -> None:
    packet = deepcopy(_example("evidence_sufficient_first_pass"))
    mutate(packet)
    with pytest.raises(mod.ValidationError):
        mod.validate_self_rag_loop_packet_v1(packet)


def test_module_does_not_import_or_call_protected_runtime_files(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_calls: list[str] = []

    def _sentinel(*args, **kwargs):
        blocked_calls.append("hit")
        raise AssertionError("protected runtime path touched")

    monkeypatch.setattr(builtins, "open", _sentinel)
    monkeypatch.setattr(Path, "read_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "write_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "open", _sentinel, raising=False)

    packet = mod.build_self_rag_loop_packet_v1(
        self_rag_loop_packet_id="protect_1",
        query_summary="Simple metadata-only loop state.",
        initial_query_class="general_reasoning_query",
        initial_routing_target="source_evidence_graph_lookup",
        loop_stage="gap_detection",
        loop_iteration_count=0,
        max_iterations=2,
        visited_routing_targets=[],
        evidence_candidates=[],
        grounding_status="more_evidence_needed",
        citation_readiness="more_evidence_needed",
        context_budget_status="within_budget",
        reroute_recommended=False,
        reroute_target="no_reroute_stop",
        stop_reason="more evidence needed",
        fallback_behavior="ask_clarifying_question",
        recommended_answer_action="ask_clarifying_question",
        recommended_next_check="ask the user for the missing source or scope",
    )
    assert packet["self_rag_loop_packet_id"] == "protect_1"
    assert blocked_calls == []
