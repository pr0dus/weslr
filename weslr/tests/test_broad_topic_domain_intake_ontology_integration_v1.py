from __future__ import annotations

from dataclasses import asdict

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1, validate_broad_topic_domain_intake_v1


def _build(**overrides):
    base = {
        "safe_topic_descriptor": "Generic broad topic",
        "prompt_labels": ("research",),
        "owner_intent_labels": ("research",),
        "risk_hints": ("medium uncertainty",),
        "known_unknown_hints": ("unfamiliar",),
        "existing_behavior_pack_refs": (),
    }
    base.update(overrides)
    return build_broad_topic_domain_intake_v1(**base)


def test_intake_exposes_ontology_metadata_fields():
    intake = _build()
    payload = asdict(intake)
    for field in (
        "ontology_packet_id",
        "ontology_meta_domains",
        "ontology_domain_families",
        "ontology_subdomain_traits",
        "ontology_objects_of_study",
        "ontology_evidence_classes",
        "ontology_risk_classes",
        "ontology_sensitivity_classes",
        "ontology_response_route_family",
        "ontology_behavior_pack_candidate_labels",
    ):
        assert field in payload
    assert intake.ontology_packet_id.startswith("broad_topic_ontology_")
    assert validate_broad_topic_domain_intake_v1(intake) is True


def test_metamaterials_intake_is_ontology_enriched():
    intake = _build(
        safe_topic_descriptor="Metamaterials frontier research",
        prompt_labels=("metamaterials", "materials discovery", "frontier research", "experimental validation"),
        owner_intent_labels=("research",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("frontier", "high uncertainty"),
    )
    assert intake.domain_family == "materials_discovery"
    assert "materials_discovery" in intake.ontology_domain_families
    assert "metamaterials" in intake.ontology_domain_families
    assert "frontier_research" in intake.ontology_subdomain_traits
    assert "experimental_validation_needed" in intake.ontology_evidence_classes
    assert intake.public_claim_allowed is False


def test_theory_of_mind_intake_is_mind_consciousness_related():
    intake = _build(
        safe_topic_descriptor="Theory of mind conceptual research",
        prompt_labels=("theory of mind", "philosophy of mind", "cognitive science"),
        owner_intent_labels=("learn explain",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    assert intake.domain_family == "theory_of_mind"
    assert set(intake.ontology_meta_domains) >= {"mind_intelligence_consciousness", "formal_reasoning"}
    assert set(intake.ontology_domain_families) >= {"theory_of_mind", "philosophy_of_mind", "cognitive_science"}
    assert "conceptual_theory_path" == intake.ontology_response_route_family
    assert intake.public_claim_allowed is False


def test_ai_agent_architecture_intake_is_ai_cognitive_architecture_related():
    intake = _build(
        safe_topic_descriptor="AI agent architecture and governance",
        prompt_labels=("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
        owner_intent_labels=("research",),
        risk_hints=("public claim sensitive", "safety critical"),
        known_unknown_hints=("adjacent",),
    )
    assert intake.domain_family == "ai_systems"
    assert set(intake.ontology_domain_families) >= {"ai_systems", "agentic_systems", "cognitive_architecture", "ai_safety_governance"}
    assert intake.ontology_response_route_family == "research_conversation_plan"
    assert intake.public_claim_allowed is False
    assert intake.runtime_authority is False


def test_medical_software_intake_is_health_and_regulatory_sensitive():
    intake = _build(
        safe_topic_descriptor="Medical software regulated path",
        prompt_labels=("medicine health research", "software product", "clinical validation"),
        owner_intent_labels=("evaluate feasibility",),
        risk_hints=("medical sensitive", "regulated domain"),
        known_unknown_hints=("unfamiliar",),
    )
    assert intake.domain_family == "software_product"
    assert "medicine_health_research" in intake.ontology_domain_families
    assert intake.safety_sensitive is True
    assert intake.legal_sensitive is True
    assert intake.risk_level == "high"
    assert intake.recommended_next_stage in {"privacy_safety_legal_boundary_review", "evidence_mapping", "research_conversation_plan"}


def test_wifi_rf_sensing_preserves_privacy_boundary_path():
    intake = _build(
        safe_topic_descriptor="WiFi/RF sensing for self-care",
        prompt_labels=("wifi sensing", "rf sensing", "human sensing", "privacy", "consent", "self-care"),
        owner_intent_labels=("research",),
        risk_hints=("privacy sensitive", "medical adjacent", "lawful only"),
        known_unknown_hints=("unfamiliar", "researchable"),
    )
    assert intake.domain_family == "privacy_sensitive_technology"
    assert intake.privacy_sensitive is True
    assert intake.legal_sensitive is True
    assert intake.recommended_next_stage in {"research_conversation_plan", "privacy_safety_legal_boundary_review"}


def test_unknown_future_topic_stays_bounded():
    intake = _build(
        safe_topic_descriptor="Unknown future topic",
        prompt_labels=("unknown", "future topic"),
        owner_intent_labels=("unknown",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    assert intake.domain_family == "unknown_domain"
    assert intake.novelty_level == "high_uncertainty"
    assert intake.recommended_next_stage == "clarifying_question"
    assert intake.public_claim_allowed is False
    assert intake.runtime_authority is False
    assert intake.writes_state is False
    assert intake.model_provider_used is False
