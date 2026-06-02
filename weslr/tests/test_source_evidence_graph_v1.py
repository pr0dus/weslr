from __future__ import annotations

import inspect
import json
import sys

import pytest

import weslr.source_evidence_graph as mod


def _example(example_id: str):
    return next(item for item in mod.build_initial_source_evidence_graph_examples_v1() if item["evidence_graph_id"] == example_id)


def test_module_imports_safely() -> None:
    assert mod.HELPER_TYPE_V1 == "source_evidence_graph_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules



def test_module_does_not_reference_protected_runtime_files() -> None:
    source = inspect.getsource(mod)
    assert "chat_responder.py" not in source
    assert "weslr.chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source



def test_builds_deterministic_source_evidence_node() -> None:
    node_a = mod.build_source_evidence_node_v1(
        source_id="source_v1",
        source_type="signal_provenance",
        source_name="Source V1",
        source_scope="internal",
        source_reference="signal:v1",
    )
    node_b = mod.build_source_evidence_node_v1(
        source_id="source_v1",
        source_type="signal_provenance",
        source_name="Source V1",
        source_scope="internal",
        source_reference="signal:v1",
    )
    assert node_a == node_b
    assert node_a["node_type"] == "source_node"
    assert node_a["safe_metadata"] == {}



def test_builds_deterministic_claim_node() -> None:
    node_a = mod.build_claim_node_v1(
        claim_id="claim_v1",
        claim_text_summary="a bounded claim",
        claim_status="supported",
    )
    node_b = mod.build_claim_node_v1(
        claim_id="claim_v1",
        claim_text_summary="a bounded claim",
        claim_status="supported",
    )
    assert node_a == node_b
    assert node_a["node_type"] == "claim_node"
    assert node_a["claim_status"] == "supported"



def test_builds_deterministic_evidence_edge() -> None:
    edge_a = mod.build_evidence_edge_v1(
        edge_id="edge_v1",
        edge_type="supports",
        from_node_id="source_v1",
        to_node_id="claim_v1",
    )
    edge_b = mod.build_evidence_edge_v1(
        edge_id="edge_v1",
        edge_type="supports",
        from_node_id="source_v1",
        to_node_id="claim_v1",
    )
    assert edge_a == edge_b
    assert edge_a["edge_type"] == "supports"



def test_builds_deterministic_graph() -> None:
    source = mod.build_source_evidence_node_v1(
        source_id="graph_v1:source",
        source_type="signal_provenance",
        source_name="Graph Source",
        source_scope="internal",
        source_reference="signal:graph",
    )
    claim = mod.build_claim_node_v1(
        claim_id="graph_v1:claim",
        claim_text_summary="graph claim",
        claim_status="supported",
        supporting_sources=[source["source_id"]],
        citation_refs=[source["source_reference"]],
    )
    edge = mod.build_evidence_edge_v1(
        edge_id="graph_v1:edge",
        edge_type="supports",
        from_node_id=source["source_id"],
        to_node_id=claim["claim_id"],
    )
    graph_a = mod.build_source_evidence_graph_v1(
        evidence_graph_id="graph_v1",
        source_nodes=[source],
        claim_nodes=[claim],
        edges=[edge],
    )
    graph_b = mod.build_source_evidence_graph_v1(
        evidence_graph_id="graph_v1",
        source_nodes=[source],
        claim_nodes=[claim],
        edges=[edge],
    )
    assert graph_a == graph_b
    assert graph_a["safe_metadata"]["metadata_only"] is True



def test_validates_normal_graph() -> None:
    assert mod.validate_source_evidence_graph_v1(_example("fresh_source_supports_claim")) is True



def test_summarizes_graph() -> None:
    graph = _example("fresh_source_supports_claim")
    summary = mod.summarize_source_evidence_graph_v1(graph)
    assert summary["summary_type"] == mod.SUMMARY_TYPE_V1
    assert summary["evidence_graph_id"] == graph["evidence_graph_id"]
    assert summary["source_count"] == 1
    assert summary["claim_count"] == 1



def test_json_safe_export_works() -> None:
    graph = _example("fresh_source_supports_claim")
    safe = mod.to_source_evidence_graph_json_safe_v1(graph)
    json.dumps(safe)
    assert safe["evidence_graph_id"] == graph["evidence_graph_id"]



def test_all_initial_examples_exist() -> None:
    examples = mod.build_initial_source_evidence_graph_examples_v1()
    ids = {item["evidence_graph_id"] for item in examples}
    assert len(examples) == 10
    assert "fresh_source_supports_claim" in ids
    assert "stale_source_supports_claim_with_warning" in ids
    assert "two_sources_contradict_same_claim" in ids
    assert "poisoned_source_quarantined_cannot_support_claim" in ids
    assert "access_restricted_document_blocked_for_public_answer" in ids
    assert "artifact_provenance_supports_generated_artifact_claim" in ids
    assert "signal_freshness_supports_energy_forecast_claim" in ids
    assert "forecast_error_invalidates_prior_assumption" in ids
    assert "naie_rejects_llm_candidate_missing_source_edge" in ids
    assert "public_claim_blocked_not_public_safe" in ids



def test_fresh_source_supports_claim() -> None:
    graph = _example("fresh_source_supports_claim")
    assert graph["claim_grounding_status"] == "grounded"
    assert graph["citation_readiness"] == "ready"
    assert graph["rag_readiness"] == "ready"



def test_stale_support_produces_stale_warning_status() -> None:
    graph = _example("stale_source_supports_claim_with_warning")
    assert graph["stale_sources"]
    assert graph["claim_nodes"][0]["claim_status"] == "stale_support"
    assert graph["claim_grounding_status"] == "partially_grounded"



def test_contradiction_summary_detects_contradicting_sources() -> None:
    graph = _example("two_sources_contradict_same_claim")
    assert graph["contradiction_summary"]["contradiction_count"] == 1
    assert graph["claim_nodes"][0]["claim_status"] == "contradicted"
    assert graph["claim_grounding_status"] == "partially_grounded"



def test_poisoned_source_cannot_support_public_claim() -> None:
    graph = _example("poisoned_source_quarantined_cannot_support_claim")
    assert graph["poison_quarantined_sources"]
    assert graph["public_claim_readiness"] == "blocked"
    assert graph["claim_nodes"][0]["claim_status"] == "poison_quarantined"



def test_access_restricted_source_blocks_public_answer_use() -> None:
    graph = _example("access_restricted_document_blocked_for_public_answer")
    assert graph["access_restricted_sources"]
    assert graph["public_claim_readiness"] == "blocked"
    assert graph["claim_nodes"][0]["claim_status"] == "access_restricted"



def test_artifact_provenance_supports_generated_artifact_claim() -> None:
    graph = _example("artifact_provenance_supports_generated_artifact_claim")
    assert graph["artifact_nodes"]
    assert graph["claim_nodes"][0]["claim_status"] == "supported"
    assert graph["claim_grounding_status"] == "grounded"



def test_signal_freshness_supports_energy_forecast_claim() -> None:
    graph = _example("signal_freshness_supports_energy_forecast_claim")
    assert graph["forecast_nodes"]
    assert graph["claim_nodes"][0]["claim_status"] == "supported"
    assert graph["rag_readiness"] == "ready"



def test_forecast_error_invalidates_prior_assumption() -> None:
    graph = _example("forecast_error_invalidates_prior_assumption")
    assert any(edge["edge_type"] == "invalidates" for edge in graph["edges"])
    assert graph["claim_nodes"][0]["claim_status"] == "contradicted"



def test_naie_missing_source_edge_causes_candidate_rejection_metadata() -> None:
    graph = _example("naie_rejects_llm_candidate_missing_source_edge")
    assert graph["inference_nodes"]
    assert graph["candidate_answer_nodes"]
    assert graph["candidate_answer_nodes"][0]["candidate_status"] == "candidate_rejected"
    assert graph["missing_sources"] == ["source_edge:llm_candidate"]



def test_public_claim_blocked_when_maturity_not_public_safe() -> None:
    graph = _example("public_claim_blocked_not_public_safe")
    assert graph["public_claim_nodes"]
    assert graph["public_claim_readiness"] == "blocked"
    assert graph["claim_nodes"][0]["claim_status"] == "unsupported"


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_grants_runtime_authority(graph) -> None:
    assert graph["runtime_authority"] is False


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_writes_state(graph) -> None:
    assert graph["writes_state"] is False


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_uses_model_provider(graph) -> None:
    assert graph["model_provider_used"] is False


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_allows_public_claim(graph) -> None:
    assert graph["public_claim_allowed"] is False


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_allows_proof_claim(graph) -> None:
    assert graph["proof_claim_allowed"] is False


@pytest.mark.parametrize("graph", mod.build_initial_source_evidence_graph_examples_v1())
def test_no_initial_example_claims_autonomous_learning(graph) -> None:
    assert graph["learning_claimed"] is False


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("source_nodes", [{"node_type": "mystery_node"}], "unknown_node_type"),
])
def test_validation_fails_unknown_node_type(field_name: str, field_value, expected_error: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph[field_name] = field_value
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("edges", [{"edge_id": "bad", "edge_type": "mystery_edge", "from_node_id": "a", "to_node_id": "b"}], "unknown_edge_type"),
])
def test_validation_fails_unknown_edge_type(field_name: str, field_value, expected_error: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph[field_name] = field_value
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("field_name, field_value, expected_error", [
    ("claim_nodes", [{"node_type": "claim_node", "node_id": "x", "claim_id": "x", "claim_text_summary": "x", "claim_type": "factual_claim", "claim_scope": "internal", "claim_status": "mystery_status", "supporting_sources": [], "contradicting_sources": [], "citation_refs": [], "freshness_required": True, "public_claim_sensitive": False, "requires_owner_approval": False, "unsupported_reason": "", "safe_metadata": {}}], "unknown_claim_status"),
])
def test_validation_fails_unknown_claim_status(field_name: str, field_value, expected_error: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph[field_name] = field_value
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("field_name, expected_error", [
    ("public_claim_allowed", "public_claim_allowed_true"),
    ("proof_claim_allowed", "proof_claim_allowed_true"),
    ("runtime_authority", "runtime_authority_true"),
    ("writes_state", "writes_state_true"),
    ("model_provider_used", "model_provider_used_true"),
    ("learning_claimed", "learning_claimed_true"),
])
def test_validation_fails_forbidden_graph_authority_flags(field_name: str, expected_error: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph[field_name] = True
    with pytest.raises(mod.ValidationError, match=expected_error):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("bad_payload", [
    {"safe_metadata": {"hidden_prompt": "x"}},
    {"safe_metadata": {"raw_private": "x"}},
    {"safe_metadata": {"secret": "x"}},
    {"safe_metadata": {"token": "x"}},
    {"safe_metadata": {"api_key": "x"}},
    {"safe_metadata": {"credential": "x"}},
    {"safe_metadata": {"password": "x"}},
])
def test_validation_fails_hidden_prompt_raw_private_secret_and_key_fields(bad_payload: dict[str, dict[str, str]]) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph["safe_metadata"] = {**graph["safe_metadata"], **bad_payload["safe_metadata"]}
    with pytest.raises(mod.ValidationError, match="hidden_prompt_or_raw_private_field"):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("marker", ["AGI", "consciousness", "sentience", "Turing", "certification"])
def test_validation_fails_agi_consciousness_turing_certification_marker(marker: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph["safe_metadata"] = {**graph["safe_metadata"], "claim": marker}
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("claim", ["hallucination elimination", "hallucination-free", "no hallucinations"])
def test_validation_fails_hallucination_elimination_claim(claim: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph["safe_metadata"] = {**graph["safe_metadata"], "claim": claim}
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_source_evidence_graph_v1(graph)


@pytest.mark.parametrize("claim", ["public readiness claim", "proof certainty", "truth certainty"])
def test_validation_fails_public_readiness_and_proof_truth_certainty_claims(claim: str) -> None:
    graph = mod.to_source_evidence_graph_json_safe_v1(_example("fresh_source_supports_claim"))
    graph["safe_metadata"] = {**graph["safe_metadata"], "claim": claim}
    with pytest.raises(mod.ValidationError, match="claim_marker_blocked"):
        mod.validate_source_evidence_graph_v1(graph)



def test_validation_fails_poisoned_source_supports_public_claim() -> None:
    source = mod.build_source_evidence_node_v1(
        source_id="poison_support_public:source",
        source_type="retrieved_content",
        source_name="Poisoned source",
        source_scope="internal",
        source_reference="retrieved:poison",
        poison_shield_status="quarantined",
    )
    claim = mod.build_claim_node_v1(
        claim_id="poison_support_public:claim",
        claim_text_summary="public claim",
        claim_status="supported",
        claim_scope="public",
        public_claim_sensitive=True,
        node_type=mod.NODE_TYPE_PUBLIC_CLAIM_V1,
    )
    graph = mod.build_source_evidence_graph_v1(
        evidence_graph_id="poison_support_public",
        source_nodes=[source],
        claim_nodes=[claim],
        public_claim_nodes=[claim],
        edges=[
            mod.build_evidence_edge_v1(
                edge_id="poison_support_public:edge",
                edge_type="supports",
                from_node_id=source["source_id"],
                to_node_id=claim["claim_id"],
            )
        ],
    )
    with pytest.raises(mod.ValidationError, match="poisoned_source_supports_public_claim"):
        mod.validate_source_evidence_graph_v1(graph)
