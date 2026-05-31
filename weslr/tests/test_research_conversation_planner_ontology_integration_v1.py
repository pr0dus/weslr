from __future__ import annotations

from dataclasses import asdict
import sys

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
from weslr.research_conversation_planner import build_research_conversation_plan_v1, validate_research_conversation_plan_v1


def _intake(**overrides):
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


def test_planner_imports_safely():
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_planner_exposes_ontology_metadata_fields():
    plan = build_research_conversation_plan_v1(domain_intake=_intake())
    payload = asdict(plan)
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
    assert plan.ontology_packet_id.startswith("broad_topic_ontology_")
    assert validate_research_conversation_plan_v1(plan) is True


def test_metamaterials_plan_is_feasibility_or_research_evidence_oriented():
    intake = _intake(
        safe_topic_descriptor="Metamaterials frontier research",
        prompt_labels=("metamaterials", "materials discovery", "frontier research", "experimental validation"),
        owner_intent_labels=("evaluate feasibility",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("frontier", "high uncertainty"),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "materials_discovery"
    assert plan.plan_type in {"map_research_questions", "feasibility_review"}
    assert plan.recommended_response_mode in {"research_plan", "evidence_request"}
    blob = " ".join(plan.evidence_needed + plan.safe_next_steps + plan.boundary_warnings)
    assert "technical literature" in blob
    assert "experimental" in blob
    assert plan.public_claim_allowed is False


def test_theory_of_mind_plan_stays_conceptual_without_claim_markers():
    intake = _intake(
        safe_topic_descriptor="Theory of mind conceptual research",
        prompt_labels=("theory of mind", "philosophy of mind", "cognitive science"),
        owner_intent_labels=("learn explain",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "theory_of_mind"
    assert plan.plan_type == "explain_topic"
    assert plan.recommended_response_mode == "direct_bounded_overview"
    blob = " ".join(plan.safe_next_steps + plan.boundary_warnings + plan.owner_questions + plan.evidence_needed).lower()
    assert "consciousness claim" not in blob
    assert "sentience claim" not in blob
    assert "theory of mind" in blob


def test_ai_agent_architecture_plan_is_governed_and_safety_research_oriented():
    intake = _intake(
        safe_topic_descriptor="AI agent architecture and governance",
        prompt_labels=("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
        owner_intent_labels=("research",),
        risk_hints=("public-facing sensitivity", "safety critical"),
        known_unknown_hints=("adjacent",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "ai_systems"
    assert plan.plan_type in {"map_research_questions", "feasibility_review"}
    assert plan.recommended_response_mode == "research_plan"
    assert plan.requires_boundary_review is True
    assert plan.public_claim_allowed is False
    assert "governance" in " ".join(plan.safe_next_steps + plan.boundary_warnings).lower()


def test_medical_software_plan_requires_boundary_review_and_clinical_evidence():
    intake = _intake(
        safe_topic_descriptor="Medical software regulated path",
        prompt_labels=("medicine health research", "software product", "clinical validation"),
        owner_intent_labels=("evaluate feasibility",),
        risk_hints=("medical sensitive", "regulated domain"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "software_product"
    assert plan.plan_type == "risk_boundary_review"
    assert plan.recommended_response_mode == "evidence_request"
    blob = " ".join(plan.evidence_needed + plan.safe_next_steps + plan.boundary_warnings).lower()
    assert "clinical" in blob
    assert "regulatory" in blob
    assert plan.runtime_authority is False


def test_wifi_rf_sensing_plan_keeps_privacy_boundary_and_beneficial_assistive_path():
    intake = _intake(
        safe_topic_descriptor="WiFi/RF sensing for consent-based research in a home setting",
        prompt_labels=("wifi sensing", "research only", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("consent required", "lawful only"),
        known_unknown_hints=("researchable",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "privacy_sensitive_technology"
    assert plan.plan_type in {"map_research_questions", "risk_boundary_review"}
    assert plan.requires_boundary_review is True
    assert plan.requires_evidence_mapping is True
    assert plan.recommended_response_mode == "research_plan"
    assert "consent" in " ".join(plan.safe_next_steps + plan.owner_questions).lower()


def test_unknown_future_topic_stays_high_uncertainty_and_asks_clarification():
    intake = _intake(
        safe_topic_descriptor="Unknown future topic",
        prompt_labels=("unknown", "novel"),
        owner_intent_labels=("unknown",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.domain_family == "unknown_domain"
    assert plan.plan_type in {"clarifying_intake_plan", "evidence_collection_plan"}
    assert plan.recommended_response_mode in {"clarifying_question", "evidence_request"}
    assert any("clarification" in item or "unknown" in item for item in plan.safe_next_steps + plan.owner_questions + plan.friction_capture_triggers)


def test_ontology_behavior_pack_candidate_labels_are_preserved():
    intake = _intake(
        safe_topic_descriptor="Owner workflow planning for WESLR improvement",
        prompt_labels=("weslr", "behavior pack", "replay"),
        owner_intent_labels=("research",),
        risk_hints=("medium uncertainty",),
        known_unknown_hints=("known existing pack",),
        existing_behavior_pack_refs=("owner_workflow",),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    assert plan.ontology_behavior_pack_candidate_labels
    assert isinstance(plan.ontology_behavior_pack_candidate_labels, tuple)
    assert validate_research_conversation_plan_v1(plan) is True


def test_forbidden_markers_remain_blocked():
    plan = build_research_conversation_plan_v1(domain_intake=_intake())
    payload = asdict(plan)
    payload["safe_next_steps"][0] = "public ISS wording"
    try:
        validate_research_conversation_plan_v1(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("expected validation failure")

    payload = asdict(plan)
    payload["owner_questions"][0] = "AGI claim"
    try:
        validate_research_conversation_plan_v1(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("expected validation failure")
