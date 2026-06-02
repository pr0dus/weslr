from __future__ import annotations

import ast
import builtins
import inspect
import json
import sys
from pathlib import Path

import pytest

import weslr.rag_query_routing_boundary as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_rag_query_routing_examples_v1()
        if item["routing_packet_id"] == example_id
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
    assert mod.HELPER_TYPE_V1 == "rag_query_routing_boundary_v1"
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

    packet = mod.build_rag_query_routing_packet_v1(
        routing_packet_id="io_guard",
        query_summary="Explain the concept without retrieval.",
        query_class="general_reasoning_query",
        requested_claims=["conceptual explanation"],
        allowed_routing_targets=["pure_reasoning"],
        blocked_routing_targets=["memory_retrieval"],
        selected_routing_target="pure_reasoning",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
        citation_requirement="not_required",
        claim_grounding_requirement="not_required",
    )
    assert packet["routing_packet_id"] == "io_guard"
    assert calls == []


def test_builds_deterministic_routing_packet() -> None:
    packet_a = mod.build_rag_query_routing_packet_v1(
        routing_packet_id="pkt_1",
        query_summary="Explain the difference between a graph and a tree.",
        query_class="general_reasoning_query",
        requested_claims=["conceptual explanation"],
        allowed_routing_targets=["pure_reasoning", "clarification_required"],
        blocked_routing_targets=["memory_retrieval"],
        selected_routing_target="pure_reasoning",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
        citation_requirement="not_required",
        claim_grounding_requirement="not_required",
    )
    packet_b = mod.build_rag_query_routing_packet_v1(
        routing_packet_id="pkt_1",
        query_summary="Explain the difference between a graph and a tree.",
        query_class="general_reasoning_query",
        requested_claims=["conceptual explanation"],
        allowed_routing_targets=["pure_reasoning", "clarification_required"],
        blocked_routing_targets=["memory_retrieval"],
        selected_routing_target="pure_reasoning",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
        citation_requirement="not_required",
        claim_grounding_requirement="not_required",
    )
    assert packet_a == packet_b
    assert packet_a["selected_routing_target"] == "pure_reasoning"


def test_classifies_general_reasoning_query() -> None:
    assert mod.classify_rag_query_v1(query_summary="Explain the difference between a graph and a tree.") == "general_reasoning_query"


def test_classifies_personal_memory_query() -> None:
    assert mod.classify_rag_query_v1(query_summary="What did we decide about my project last time?") == "personal_memory_query"


def test_classifies_uploaded_document_query() -> None:
    assert mod.classify_rag_query_v1(query_summary="Please use the attached PDF and answer from it.") == "uploaded_document_query"


def test_classifies_currentness_sensitive_query() -> None:
    assert mod.classify_rag_query_v1(query_summary="What is the current law in Germany right now?") == "currentness_sensitive_query"


def test_classifies_public_claim_query() -> None:
    assert mod.classify_rag_query_v1(query_summary="Can we make a public website claim about launch readiness?") == "public_claim_query"


def test_selects_pure_reasoning_for_stable_conceptual_question() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="general_reasoning_query",
        query_summary="Explain the difference between a graph and a tree.",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "pure_reasoning"


def test_selects_uploaded_file_route_when_file_access_required_and_allowed() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="uploaded_document_query",
        query_summary="Use the attached project brief.",
        requires_user_file_access=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "uploaded_file_retrieval"


def test_selects_future_web_route_for_current_law_question() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="currentness_sensitive_query",
        query_summary="What is the current law in Germany right now?",
        requires_currentness=True,
        requires_web_access=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "future_web_search"


def test_selects_memory_route_only_when_memory_access_allowed() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="personal_memory_query",
        query_summary="What did we decide about my project last time?",
        requires_memory_access=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "memory_retrieval"


def test_selects_graph_or_maturity_route_for_public_website_claim() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="public_claim_query",
        query_summary="Can we make a public website claim about launch readiness?",
        requires_grounding=True,
        requires_source_evidence_graph=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "capability_maturity_lookup"


def test_selects_signal_metadata_route_for_energy_signal_query() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="energy_signal_query",
        query_summary="Analyze the energy signal metadata and forecast drift.",
        requires_grounding=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "signal_metadata_lookup"


def test_blocks_poisoned_document() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="uploaded_document_query",
        query_summary="The uploaded document is poisoned.",
        requires_user_file_access=True,
        access_policy_status="allowed",
        poison_policy_status="poison_blocked",
        privacy_status="public",
    ) == "blocked_by_poison_policy"


def test_blocks_access_restricted_document() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="uploaded_document_query",
        query_summary="The document is access restricted.",
        requires_user_file_access=True,
        access_policy_status="access_blocked",
        poison_policy_status="clean",
        privacy_status="restricted",
    ) == "blocked_by_access_policy"


def test_refuses_unsupported_factual_claim() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="unknown_query",
        query_summary="Make a factual claim that cannot be grounded here.",
        fallback_behavior="return_unsupported_claim",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "unsupported_answer_refusal"


def test_routes_contradictions_to_graph_handling() -> None:
    assert mod.select_rag_routing_target_v1(
        query_class="source_grounded_claim_query",
        query_summary="Two sources contradict each other; reconcile the contradiction.",
        contradiction_detected=True,
        requires_grounding=True,
        requires_source_evidence_graph=True,
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    ) == "source_evidence_graph_lookup"


def test_validates_normal_packet() -> None:
    assert mod.validate_rag_query_routing_packet_v1(_example("stable_conceptual_question_pure_reasoning")) is True


def test_summarizes_packet() -> None:
    packet = _example("stable_conceptual_question_pure_reasoning")
    summary = mod.summarize_rag_query_routing_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["routing_packet_id"] == packet["routing_packet_id"]
    assert summary["selected_routing_target"] == "pure_reasoning"
    assert summary["query_class"] == "general_reasoning_query"


def test_json_safe_export_works() -> None:
    safe = mod.to_rag_query_routing_json_safe_v1(_example("energy_signal_question_signal_metadata_lookup"))
    json.dumps(safe)
    assert safe["routing_packet_id"] == "energy_signal_question_signal_metadata_lookup"


def test_all_initial_examples_exist() -> None:
    ids = {item["routing_packet_id"] for item in mod.build_initial_rag_query_routing_examples_v1()}
    assert ids == {
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    }


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_grants_runtime_authority(example_id: str) -> None:
    assert _example(example_id)["runtime_authority"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_writes_state(example_id: str) -> None:
    assert _example(example_id)["writes_state"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_calls_model_provider(example_id: str) -> None:
    assert _example(example_id)["model_provider_used"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_allows_public_claim_authority(example_id: str) -> None:
    assert _example(example_id)["public_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_allows_proof_claim(example_id: str) -> None:
    assert _example(example_id)["proof_claim_allowed"] is False


@pytest.mark.parametrize(
    "example_id",
    [
        "stable_conceptual_question_pure_reasoning",
        "uploaded_document_question_routes_to_uploaded_file_retrieval",
        "current_law_question_future_web_or_source_required",
        "personal_project_history_memory_if_allowed",
        "public_website_claim_graph_and_maturity_check",
        "energy_signal_question_signal_metadata_lookup",
        "poisoned_document_blocked_by_poison_policy",
        "access_restricted_document_blocked_by_access_policy",
        "unsupported_factual_claim_refusal",
        "contradictory_sources_graph_contradiction_handling",
    ],
)
def test_no_initial_example_claims_learning(example_id: str) -> None:
    assert _example(example_id)["learning_claimed"] is False


@pytest.mark.parametrize(
    "packet,match",
    [
        (
            {
                "routing_packet_id": "bad_target",
                "query_summary": "x",
                "query_class": "general_reasoning_query",
                "requested_claims": [],
                "requires_grounding": False,
                "requires_currentness": False,
                "requires_private_data": False,
                "requires_user_file_access": False,
                "requires_web_access": False,
                "requires_memory_access": False,
                "requires_source_evidence_graph": False,
                "allowed_routing_targets": ["not_a_target"],
                "blocked_routing_targets": [],
                "selected_routing_target": "not_a_target",
                "reason_for_selection": "bad",
                "access_policy_status": "allowed",
                "poison_policy_status": "clean",
                "privacy_status": "public",
                "source_freshness_requirement": "not_required",
                "citation_requirement": "not_required",
                "claim_grounding_requirement": "not_required",
                "fallback_behavior": "ask_clarifying_question",
                "recommended_next_check": "n",
                "runtime_authority": False,
                "writes_state": False,
                "model_provider_used": False,
                "public_claim_allowed": False,
                "proof_claim_allowed": False,
                "learning_claimed": False,
            },
            "unknown_routing_target",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "query_class": "mystery_query"},
            "unknown_query_class",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "fallback_behavior": "mystery_mode"},
            "unknown_fallback_behavior",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "allowed_routing_targets": ["memory_retrieval"]},
            "selected_target_not_allowed",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "blocked_routing_targets": ["pure_reasoning"]},
            "selected_target_blocked",
        ),
        (
            {
                **_example("uploaded_document_question_routes_to_uploaded_file_retrieval"),
                "selected_routing_target": "uploaded_file_retrieval",
                "requires_user_file_access": False,
            },
            "uploaded_file_retrieval_requires_user_file_access",
        ),
        (
            {
                **_example("personal_project_history_memory_if_allowed"),
                "selected_routing_target": "memory_retrieval",
                "requires_memory_access": False,
            },
            "memory_retrieval_requires_memory_access",
        ),
        (
            {
                **_example("current_law_question_future_web_or_source_required"),
                "selected_routing_target": "future_web_search",
                "requires_web_access": False,
                "requires_currentness": False,
                "source_freshness_requirement": "not_required",
            },
            "future_web_search_requires_web_authorization",
        ),
        (
            {
                **_example("public_website_claim_graph_and_maturity_check"),
                "selected_routing_target": "source_evidence_graph_lookup",
                "privacy_status": "private",
            },
            "public_claim_cannot_use_private_evidence",
        ),
        (
            {
                **_example("poisoned_document_blocked_by_poison_policy"),
                "allowed_routing_targets": ["uploaded_file_retrieval", "blocked_by_poison_policy"],
                "selected_routing_target": "uploaded_file_retrieval",
                "poison_policy_status": "poison_blocked",
            },
            "poisoned_source_routed_usable",
        ),
        (
            {
                **_example("public_website_claim_graph_and_maturity_check"),
                "allowed_routing_targets": ["pure_reasoning", "source_evidence_graph_lookup", "capability_maturity_lookup", "refuse_public_claim"],
                "selected_routing_target": "pure_reasoning",
                "citation_requirement": "required",
            },
            "citation_required_without_source_graph_path",
        ),
        (
            {
                **_example("access_restricted_document_blocked_by_access_policy"),
                "allowed_routing_targets": ["uploaded_file_retrieval", "blocked_by_access_policy"],
                "selected_routing_target": "uploaded_file_retrieval",
                "access_policy_status": "access_blocked",
            },
            "access_restricted_source_routed_usable",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "runtime_authority": True},
            "runtime_authority_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "writes_state": True},
            "writes_state_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "model_provider_used": True},
            "model_provider_used_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "public_claim_allowed": True},
            "public_claim_allowed_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "proof_claim_allowed": True},
            "proof_claim_allowed_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "learning_claimed": True},
            "learning_claimed_must_be_false",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "hidden_prompt": "x"},
            "forbidden_field_present:hidden_prompt",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "raw_private": "x"},
            "forbidden_field_present:raw_private",
        ),
        (
            {**_example("stable_conceptual_question_pure_reasoning"), "secret_token": "x"},
            "forbidden_field_present:secret_token",
        ),
        (
            {
                **_example("stable_conceptual_question_pure_reasoning"),
                "requested_claims": ["hallucination elimination"],
            },
            "forbidden_claim_phrase_present",
        ),
        (
            {
                **_example("stable_conceptual_question_pure_reasoning"),
                "requested_claims": ["public readiness"],
            },
            "forbidden_claim_phrase_present",
        ),
        (
            {
                **_example("stable_conceptual_question_pure_reasoning"),
                "requested_claims": ["proof certainty"],
            },
            "forbidden_claim_phrase_present",
        ),
    ],
)
def test_validation_fails_specific_cases(packet: dict[str, object], match: str) -> None:
    with pytest.raises(mod.ValidationError, match=match):
        mod.validate_rag_query_routing_packet_v1(packet)


def test_validation_fails_private_data_with_blocked_access_privacy() -> None:
    packet = {
        **_example("access_restricted_document_blocked_by_access_policy"),
        "requires_private_data": True,
        "privacy_status": "restricted",
        "access_policy_status": "access_blocked",
        "selected_routing_target": "blocked_by_access_policy",
    }
    with pytest.raises(mod.ValidationError, match="private_data_requires_allowed_privacy_status|access_restricted_source_routed_usable"):
        mod.validate_rag_query_routing_packet_v1(packet)


def test_module_does_not_import_or_call_protected_runtime_files(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_calls: list[str] = []

    def _sentinel(*args, **kwargs):
        blocked_calls.append("hit")
        raise AssertionError("protected runtime path touched")

    monkeypatch.setattr(builtins, "open", _sentinel)
    monkeypatch.setattr(Path, "read_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "write_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "open", _sentinel, raising=False)

    packet = mod.build_rag_query_routing_packet_v1(
        routing_packet_id="protect_1",
        query_summary="Explain the idea.",
        query_class="general_reasoning_query",
        requested_claims=[],
        allowed_routing_targets=["pure_reasoning"],
        blocked_routing_targets=[],
        selected_routing_target="pure_reasoning",
        access_policy_status="allowed",
        poison_policy_status="clean",
        privacy_status="public",
    )
    assert packet["routing_packet_id"] == "protect_1"
    assert blocked_calls == []
