from __future__ import annotations

import ast
import builtins
import inspect
import sys
from pathlib import Path

import pytest

import weslr.inline_citation_claim_grounding_layer as mod


PROTECTED_MODULE_HINTS = (
    "weslr.chat_responder",
    "weslr.main",
    "dialogue",
    "chat_ui",
)


def _example(example_id: str):
    return next(
        item for item in mod.build_initial_claim_grounding_examples_v1()
        if item["claim_grounding_packet_id"] == example_id
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
    assert mod.HELPER_TYPE_V1 == "inline_citation_claim_grounding_layer_v1"
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

    packet = mod.build_claim_grounding_packet_v1(
        claim_grounding_packet_id="io_guard",
        answer_candidate_id="answer_guard",
        claim_nodes=["claim:io"],
        grounded_claims=["claim:io"],
        source_evidence_refs=["source:io"],
        citation_refs=["cite:io"],
        claim_grounding_status="grounded",
        citation_readiness="citation_ready",
        recommended_answer_action="answer_with_citations",
        public_claim_readiness=False,
    )
    assert packet["claim_grounding_packet_id"] == "io_guard"
    assert calls == []


def test_builds_deterministic_claim_grounding_packet() -> None:
    packet_a = mod.build_claim_grounding_packet_v1(
        claim_grounding_packet_id="pkt_1",
        answer_candidate_id="answer_1",
        claim_nodes=["claim:a"],
        source_evidence_refs=["source:1"],
        citation_refs=["cite:1"],
        grounded_claims=["claim:a"],
        claim_grounding_status="grounded",
        citation_readiness="citation_ready",
        recommended_answer_action="answer_with_citations",
        public_claim_readiness=False,
    )
    packet_b = mod.build_claim_grounding_packet_v1(
        claim_grounding_packet_id="pkt_1",
        answer_candidate_id="answer_1",
        claim_nodes=["claim:a"],
        source_evidence_refs=["source:1"],
        citation_refs=["cite:1"],
        grounded_claims=["claim:a"],
        claim_grounding_status="grounded",
        citation_readiness="citation_ready",
        recommended_answer_action="answer_with_citations",
        public_claim_readiness=False,
    )
    assert packet_a == packet_b
    assert packet_a["recommended_answer_action"] == "answer_with_citations"


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Use the source and cite it", "grounded"),
        ("This is stale but still usable", "stale_support"),
        ("These sources contradict each other", "contradicted"),
        ("This claim has no support", "unsupported"),
    ],
)
def test_evaluates_grounding_status(query: str, expected: str) -> None:
    packet = mod.build_claim_grounding_packet_v1(
        claim_grounding_packet_id=f"eval_{expected}",
        answer_candidate_id="answer_eval",
        claim_nodes=[query],
        claim_grounding_status=expected,
        citation_readiness="unknown_citation_status",
        recommended_answer_action="unknown_action",
    )
    assert mod.evaluate_claim_grounding_v1(packet) == expected


@pytest.mark.parametrize(
    "example_id,expected",
    [
        ("simple_grounded_claim_citation_ready", "citation_ready"),
        ("stale_source_requires_caveat", "citation_ready_with_caveat"),
        ("contradicted_claim_requires_disclosure", "citation_blocked_contradicted"),
        ("unsupported_claim_removed", "citation_blocked_unsupported"),
        ("access_restricted_source_blocks_public_citation", "citation_blocked_access"),
        ("poison_quarantined_source_blocks_citation", "citation_blocked_poison"),
        ("energy_recommendation_downgraded_due_stale_signal", "citation_ready_with_caveat"),
        ("llm_candidate_rejected_no_source_edge", "citation_blocked_unsupported"),
        ("public_website_claim_blocked_not_public_safe", "citation_blocked_access"),
        ("general_reasoning_answer_allowed_citation_not_required", "citation_not_required"),
    ],
)
def test_evaluates_citation_readiness(example_id: str, expected: str) -> None:
    assert mod.evaluate_citation_readiness_v1(_example(example_id)) == expected


@pytest.mark.parametrize("example_id", [
    "simple_grounded_claim_citation_ready",
    "stale_source_requires_caveat",
    "contradicted_claim_requires_disclosure",
    "unsupported_claim_removed",
    "access_restricted_source_blocks_public_citation",
    "poison_quarantined_source_blocks_citation",
    "energy_recommendation_downgraded_due_stale_signal",
    "llm_candidate_rejected_no_source_edge",
    "public_website_claim_blocked_not_public_safe",
    "general_reasoning_answer_allowed_citation_not_required",
])
def test_validates_normal_packet(example_id: str) -> None:
    assert mod.validate_claim_grounding_packet_v1(_example(example_id)) is True


def test_summarizes_packet() -> None:
    packet = _example("simple_grounded_claim_citation_ready")
    summary = mod.summarize_claim_grounding_packet_v1(packet)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["claim_grounding_packet_id"] == packet["claim_grounding_packet_id"]
    assert summary["claim_grounding_status"] == "grounded"
    assert summary["citation_readiness"] == "citation_ready"
    assert summary["recommended_answer_action"] == "answer_with_citations"


def test_json_safe_export_works() -> None:
    value = {"b": {"nested": {1, 2}}, "a": ("x", "y")}
    safe = mod.to_claim_grounding_json_safe_v1(value)
    assert safe == {"a": ["x", "y"], "b": {"nested": [1, 2]}}


def test_all_initial_examples_exist() -> None:
    example_ids = {item["claim_grounding_packet_id"] for item in mod.build_initial_claim_grounding_examples_v1()}
    assert example_ids == {
        "simple_grounded_claim_citation_ready",
        "stale_source_requires_caveat",
        "contradicted_claim_requires_disclosure",
        "unsupported_claim_removed",
        "access_restricted_source_blocks_public_citation",
        "poison_quarantined_source_blocks_citation",
        "energy_recommendation_downgraded_due_stale_signal",
        "llm_candidate_rejected_no_source_edge",
        "public_website_claim_blocked_not_public_safe",
        "general_reasoning_answer_allowed_citation_not_required",
    }


def test_no_initial_example_grants_runtime_authority() -> None:
    assert all(not item["runtime_authority"] for item in mod.build_initial_claim_grounding_examples_v1())


def test_no_initial_example_writes_state() -> None:
    assert all(not item["writes_state"] for item in mod.build_initial_claim_grounding_examples_v1())


def test_no_initial_example_calls_model_provider() -> None:
    assert all(not item["model_provider_used"] for item in mod.build_initial_claim_grounding_examples_v1())


def test_no_initial_example_allows_public_claim_authority() -> None:
    assert all(not item["public_claim_allowed"] for item in mod.build_initial_claim_grounding_examples_v1())


def test_no_initial_example_allows_proof_claim() -> None:
    assert all(not item["proof_claim_allowed"] for item in mod.build_initial_claim_grounding_examples_v1())


def test_no_initial_example_claims_learning() -> None:
    assert all(not item["learning_claimed"] for item in mod.build_initial_claim_grounding_examples_v1())


@pytest.mark.parametrize(
    "packet,match",
    [
        ({**_example("simple_grounded_claim_citation_ready"), "claim_grounding_status": "mystery"}, "unknown_claim_grounding_status"),
        ({**_example("simple_grounded_claim_citation_ready"), "citation_readiness": "mystery"}, "unknown_citation_readiness"),
        ({**_example("simple_grounded_claim_citation_ready"), "recommended_answer_action": "mystery"}, "unknown_recommended_answer_action"),
        ({**_example("unsupported_claim_removed"), "citation_readiness": "citation_ready", "source_evidence_refs": ["source:1"], "citation_refs": ["cite:1"]}, "citation_ready_cannot_have_unsupported_claims"),
        ({**_example("access_restricted_source_blocks_public_citation"), "citation_readiness": "citation_ready", "source_evidence_refs": ["source:2"], "citation_refs": ["cite:2"]}, "citation_ready_cannot_use_access_restricted_source"),
        ({**_example("poison_quarantined_source_blocks_citation"), "citation_readiness": "citation_ready", "source_evidence_refs": ["source:3"], "citation_refs": ["cite:3"]}, "citation_ready_cannot_use_poison_quarantined_source"),
        ({**_example("simple_grounded_claim_citation_ready"), "public_claim_readiness": True}, "public_claim_readiness_requires_public_claim_allowed"),
        ({**_example("simple_grounded_claim_citation_ready"), "recommended_answer_action": "answer_with_citations", "source_evidence_refs": []}, "answer_with_citations_requires_source_evidence_refs"),
        ({**_example("contradicted_claim_requires_disclosure"), "recommended_answer_action": "answer_with_caveats"}, "contradicted_claim_requires_disclosure"),
        ({**_example("stale_source_requires_caveat"), "recommended_answer_action": "answer_with_citations"}, "stale_support_requires_caveat_or_downgrade"),
        ({**_example("simple_grounded_claim_citation_ready"), "runtime_authority": True}, "runtime_authority_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "writes_state": True}, "writes_state_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "model_provider_used": True}, "model_provider_used_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "public_claim_allowed": True}, "public_claim_allowed_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "proof_claim_allowed": True}, "proof_claim_allowed_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "learning_claimed": True}, "learning_claimed_must_be_false"),
        ({**_example("simple_grounded_claim_citation_ready"), "hidden_prompt": "x"}, "forbidden_field_present:hidden_prompt"),
        ({**_example("simple_grounded_claim_citation_ready"), "raw_private": "x"}, "forbidden_field_present:raw_private"),
        ({**_example("simple_grounded_claim_citation_ready"), "secret_token": "x"}, "forbidden_field_present:secret_token"),
        ({**_example("simple_grounded_claim_citation_ready"), "requested_claims": ["hallucination elimination"]}, "forbidden_claim_phrase_present"),
        ({**_example("simple_grounded_claim_citation_ready"), "requested_claims": ["public readiness"]}, "forbidden_claim_phrase_present"),
        ({**_example("simple_grounded_claim_citation_ready"), "requested_claims": ["proof certainty"]}, "forbidden_claim_phrase_present"),
    ],
)
def test_validation_fails_specific_cases(packet: dict[str, object], match: str) -> None:
    with pytest.raises(mod.ValidationError, match=match):
        mod.validate_claim_grounding_packet_v1(packet)


def test_validation_fails_when_public_claim_readiness_true_but_public_claim_not_allowed() -> None:
    packet = {
        **_example("simple_grounded_claim_citation_ready"),
        "public_claim_readiness": True,
        "public_claim_allowed": False,
    }
    with pytest.raises(mod.ValidationError, match="public_claim_readiness_requires_public_claim_allowed"):
        mod.validate_claim_grounding_packet_v1(packet)


def test_module_does_not_import_or_call_protected_runtime_files(monkeypatch: pytest.MonkeyPatch) -> None:
    blocked_calls: list[str] = []

    def _sentinel(*args, **kwargs):
        blocked_calls.append("hit")
        raise AssertionError("protected runtime file access not allowed")

    monkeypatch.setattr(builtins, "open", _sentinel)
    monkeypatch.setattr(Path, "read_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "write_text", _sentinel, raising=False)
    monkeypatch.setattr(Path, "open", _sentinel, raising=False)

    packet = mod.build_claim_grounding_packet_v1(
        claim_grounding_packet_id="protected_guard",
        answer_candidate_id="answer_guard",
        claim_nodes=["claim:guard"],
        grounded_claims=["claim:guard"],
        source_evidence_refs=["source:guard"],
        citation_refs=["cite:guard"],
        claim_grounding_status="grounded",
        citation_readiness="citation_ready",
        recommended_answer_action="answer_with_citations",
        public_claim_readiness=False,
    )
    assert packet["claim_grounding_packet_id"] == "protected_guard"
    assert blocked_calls == []
