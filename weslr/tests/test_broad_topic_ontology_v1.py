from __future__ import annotations

from dataclasses import asdict
import inspect
import sys

import pytest

from weslr.broad_topic_ontology import (
    BroadTopicOntologyPacket,
    ValidationError,
    build_broad_topic_ontology_packet_v1,
    build_initial_broad_topic_ontology_examples_v1,
    classify_broad_topic_ontology_v1,
    summarize_broad_topic_ontology_packet_v1,
    to_broad_topic_ontology_json_safe_v1,
    validate_broad_topic_ontology_packet_v1,
)


def _base_kwargs(**overrides):
    data = {
        "safe_topic_descriptor": "Generic broad topic",
        "prompt_labels": ("research",),
        "owner_intent_labels": ("research",),
        "risk_hints": ("medium uncertainty",),
        "evidence_hints": ("technical literature",),
        "known_unknown_hints": ("unfamiliar",),
        "existing_behavior_pack_refs": (),
    }
    data.update(overrides)
    return data


def _build(**overrides):
    return build_broad_topic_ontology_packet_v1(**_base_kwargs(**overrides))


def test_module_imports_safely():
    import weslr.broad_topic_ontology as mod

    assert mod.HELPER_TYPE_V1 == "broad_topic_ontology_helper_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


@pytest.mark.parametrize(
    "kwargs, expected_meta_domains, expected_domain_families, expected_traits, expected_objects, expected_evidence, expected_route",
    [
        (
            {
                "safe_topic_descriptor": "Metamaterials frontier research",
                "prompt_labels": ("metamaterials", "materials discovery", "frontier research", "experimental validation"),
                "owner_intent_labels": ("research",),
                "evidence_hints": ("technical literature", "experimental validation"),
                "known_unknown_hints": ("frontier", "high uncertainty"),
            },
            {"physical_sciences", "technical_engineering"},
            {"metamaterials", "materials_discovery"},
            {"frontier_research", "experimental_validation_needed", "high_uncertainty", "prototype_possible"},
            {"materials", "signals_waves"},
            {"technical_literature_needed", "experimental_validation_needed"},
            {"research_conversation_plan", "evidence_mapping"},
        ),
        (
            {
                "safe_topic_descriptor": "WiFi/RF sensing for self-care",
                "prompt_labels": ("wifi sensing", "rf sensing", "human sensing", "privacy", "consent", "self-care"),
                "owner_intent_labels": ("research",),
                "risk_hints": ("privacy sensitive", "medical adjacent", "lawful only"),
                "evidence_hints": ("technical literature", "legal/privacy", "safety validation"),
                "known_unknown_hints": ("unfamiliar", "researchable"),
            },
            {"technical_engineering", "life_health", "society_law_governance"},
            {"privacy_sensitive_technology"},
            {"human_subject_involved", "privacy_sensitive", "beneficial_assistive_use", "medical_claim_adjacent", "physical_world_deployment"},
            {"signals_waves", "human_mind", "living_systems"},
            {"technical_literature_needed", "legal_regulatory_sources_needed", "safety_validation_needed"},
            {"privacy_safety_legal_boundary_review"},
        ),
        (
            {
                "safe_topic_descriptor": "Theory of mind conceptual research",
                "prompt_labels": ("theory of mind", "philosophy of mind", "cognitive science"),
                "owner_intent_labels": ("learn explain",),
                "evidence_hints": ("conceptual definition", "technical literature"),
                "known_unknown_hints": ("high uncertainty",),
            },
            {"mind_intelligence_consciousness", "formal_reasoning"},
            {"theory_of_mind", "philosophy_of_mind", "cognitive_science"},
            {"theoretical_concept", "multi_domain", "high_uncertainty", "conceptual_modeling", "formal_reasoning_required"},
            {"human_mind", "machine_intelligence"},
            {"conceptual_definition", "technical_literature_needed"},
            {"conceptual_theory_path"},
        ),
        (
            {
                "safe_topic_descriptor": "AI agent architecture and governance",
                "prompt_labels": ("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
                "owner_intent_labels": ("research",),
                "risk_hints": ("public claim sensitive", "safety critical"),
                "evidence_hints": ("technical literature", "safety validation"),
                "known_unknown_hints": ("adjacent",),
            },
            {"mind_intelligence_consciousness", "technical_engineering"},
            {"ai_systems", "agentic_systems", "cognitive_architecture", "ai_safety_governance"},
            {"emerging_technology", "system_architecture", "safety_critical", "public_claim_sensitive"},
            {"machine_intelligence", "software_system"},
            {"technical_literature_needed", "safety_validation_needed"},
            {"research_conversation_plan"},
        ),
        (
            {
                "safe_topic_descriptor": "Medical software regulated path",
                "prompt_labels": ("medicine health research", "software product", "clinical validation"),
                "owner_intent_labels": ("evaluate feasibility",),
                "risk_hints": ("medical sensitive", "regulated domain"),
                "evidence_hints": ("clinical validation", "legal/regulatory", "safety validation"),
                "known_unknown_hints": ("unfamiliar",),
            },
            {"life_health", "technical_engineering", "society_law_governance"},
            {"medicine_health_research", "software_product"},
            {"medical_claim_adjacent", "regulated_domain", "safety_critical"},
            {"living_systems", "software_system", "business_process"},
            {"clinical_validation_needed", "legal_regulatory_sources_needed", "safety_validation_needed"},
            {"privacy_safety_legal_boundary_review", "evidence_mapping"},
        ),
    ],
)
def test_core_classifications(kwargs, expected_meta_domains, expected_domain_families, expected_traits, expected_objects, expected_evidence, expected_route):
    packet = _build(**kwargs)
    assert set(packet.meta_domains) >= expected_meta_domains
    assert set(packet.domain_families) >= expected_domain_families
    assert set(packet.subdomain_traits) >= expected_traits
    assert set(packet.objects_of_study) >= expected_objects
    assert set(packet.evidence_classes) >= expected_evidence
    assert packet.response_route_family in expected_route
    assert packet.public_claim_allowed is False
    assert packet.runtime_authority is False
    assert packet.writes_state is False
    assert packet.model_provider_used is False
    assert packet.learning_claimed is False


def test_philosophy_of_mind_classification():
    packet = _build(
        safe_topic_descriptor="Philosophy of mind",
        prompt_labels=("philosophy of mind", "formal reasoning"),
        owner_intent_labels=("learn explain",),
        evidence_hints=("conceptual definition",),
        known_unknown_hints=("known existing pack",),
    )
    assert set(packet.meta_domains) >= {"mind_intelligence_consciousness", "formal_reasoning"}
    assert "philosophy_of_mind" in packet.domain_families
    assert "conceptual_definition" in packet.evidence_classes
    assert packet.response_route_family == "conceptual_theory_path"
    assert packet.public_claim_allowed is False


def test_industrial_automation_classification():
    packet = _build(
        safe_topic_descriptor="Industrial automation control system",
        prompt_labels=("industrial automation", "PLC", "control system", "equipment"),
        owner_intent_labels=("troubleshooting",),
        risk_hints=("safety critical",),
        evidence_hints=("technical literature", "safety validation"),
        known_unknown_hints=("adjacent",),
    )
    assert "industrial_automation" in packet.domain_families
    assert "technical_engineering" in packet.meta_domains
    assert "safety_critical" in packet.subdomain_traits
    assert packet.safety_sensitive is True


def test_energy_storage_system_classification():
    packet = _build(
        safe_topic_descriptor="Energy storage system planning",
        prompt_labels=("energy systems", "battery", "storage", "power"),
        owner_intent_labels=("build prototype",),
        risk_hints=("safety critical",),
        evidence_hints=("technical literature", "safety validation"),
        known_unknown_hints=("adjacent",),
    )
    assert "energy_systems" in packet.domain_families
    assert set(packet.meta_domains) >= {"environment_energy", "technical_engineering"}
    assert packet.response_route_family in {"research_conversation_plan", "evidence_mapping", "prototype_path_high_level"}


def test_legal_privacy_policy_classification():
    packet = _build(
        safe_topic_descriptor="Legal/privacy policy review",
        prompt_labels=("legal privacy", "policy governance", "compliance"),
        owner_intent_labels=("safety legal privacy review",),
        risk_hints=("legal regulatory sensitive", "privacy sensitive"),
        evidence_hints=("legal/regulatory",),
        known_unknown_hints=("unfamiliar",),
    )
    assert set(packet.meta_domains) >= {"society_law_governance"}
    assert set(packet.domain_families) >= {"legal_privacy", "policy_governance"}
    assert packet.response_route_family == "privacy_safety_legal_boundary_review"


def test_language_vocabulary_discovery_classification():
    packet = _build(
        safe_topic_descriptor="Language vocabulary discovery",
        prompt_labels=("language vocabulary", "meaning", "definition"),
        owner_intent_labels=("learn explain",),
        evidence_hints=("conceptual definition",),
        known_unknown_hints=("known existing pack",),
    )
    assert "language_vocabulary" in packet.domain_families
    assert "language_communication" in packet.meta_domains
    assert packet.response_route_family == "direct_bounded_overview"


def test_software_product_planning_classification():
    packet = _build(
        safe_topic_descriptor="Software product planning",
        prompt_labels=("software product", "product strategy", "feature planning"),
        owner_intent_labels=("commercial product strategy",),
        risk_hints=("public claim sensitive",),
        evidence_hints=("market validation", "user context"),
        known_unknown_hints=("adjacent",),
    )
    assert "software_product" in packet.domain_families
    assert set(packet.meta_domains) >= {"product_business", "technical_engineering"}
    assert "market_validation_needed" in packet.evidence_classes
    assert packet.response_route_family == "research_conversation_plan"


def test_unknown_future_topic_classification():
    packet = _build(
        safe_topic_descriptor="Unknown future topic",
        prompt_labels=("unknown", "future topic"),
        owner_intent_labels=("unknown",),
        risk_hints=("high uncertainty",),
        evidence_hints=("unknown evidence"),
        known_unknown_hints=("high uncertainty",),
    )
    assert packet.meta_domains == ["unknown_open_domain"]
    assert packet.domain_families == ["unknown_domain"]
    assert packet.novelty_level == "high_uncertainty"
    assert packet.evidence_classes == ["unknown_evidence_needed"]
    assert packet.response_route_family == "clarifying_question"


def test_deterministic_packet_building():
    packet_one = _build(
        safe_topic_descriptor="Deterministic topic",
        prompt_labels=("ai systems", "agentic systems"),
        owner_intent_labels=("research",),
        risk_hints=("public claim sensitive",),
        evidence_hints=("technical literature",),
        known_unknown_hints=("adjacent",),
    )
    packet_two = _build(
        safe_topic_descriptor="Deterministic topic",
        prompt_labels=("ai systems", "agentic systems"),
        owner_intent_labels=("research",),
        risk_hints=("public claim sensitive",),
        evidence_hints=("technical literature",),
        known_unknown_hints=("adjacent",),
    )
    assert asdict(packet_one) == asdict(packet_two)


def test_json_safe_export_works():
    packet = _build()
    exported = to_broad_topic_ontology_json_safe_v1(packet)
    assert isinstance(exported, dict)
    assert isinstance(exported["meta_domains"], list)
    assert isinstance(exported["safe_metadata"], dict)
    assert exported["public_claim_allowed"] is False


def test_summary_includes_key_axes():
    summary = summarize_broad_topic_ontology_packet_v1(_build())
    assert summary.summary_type == "broad_topic_ontology_summary_v1"
    assert summary.meta_domains
    assert summary.domain_families
    assert summary.evidence_classes
    assert summary.risk_classes
    assert summary.response_route_family


def test_initial_examples_exist_and_are_safe():
    examples = build_initial_broad_topic_ontology_examples_v1()
    assert len(examples) >= 12
    for name in (
        "metamaterials_frontier_research_ontology",
        "wifi_rf_self_care_sensing_ontology",
        "theory_of_mind_conceptual_ontology",
        "ai_agent_architecture_ontology",
        "medical_software_regulated_path_ontology",
        "philosophy_of_mind_ontology",
        "industrial_automation_control_ontology",
        "energy_storage_system_ontology",
        "legal_privacy_policy_ontology",
        "language_vocabulary_discovery_ontology",
        "software_product_planning_ontology",
        "unknown_future_topic_ontology",
    ):
        assert name in examples
        packet = examples[name]
        assert packet.public_claim_allowed is False
        assert packet.learning_claimed is False
        assert packet.runtime_authority is False
        assert packet.writes_state is False
        assert packet.model_provider_used is False
        assert validate_broad_topic_ontology_packet_v1(packet) is True


def test_validation_accepts_normal_packet():
    assert validate_broad_topic_ontology_packet_v1(_build()) is True


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("public_claim_allowed", True),
        ("runtime_authority", True),
        ("writes_state", True),
        ("model_provider_used", True),
        ("learning_claimed", True),
    ],
)
def test_boolean_invariants_fail_validation(field_name, value):
    packet = asdict(_build())
    packet[field_name] = value
    with pytest.raises(ValidationError):
        validate_broad_topic_ontology_packet_v1(packet)


@pytest.mark.parametrize(
    "field_name",
    ["raw_prompt", "raw_answer", "transcript", "raw_response_text"],
)
def test_forbidden_raw_fields_fail_validation(field_name):
    packet = asdict(_build())
    packet[field_name] = "sensitive payload"
    with pytest.raises(ValidationError):
        validate_broad_topic_ontology_packet_v1(packet)


@pytest.mark.parametrize(
    "field_name, bad_value",
    [
        ("meta_domains", ["bad_meta_domain"]),
        ("domain_families", ["bad_domain_family"]),
        ("subdomain_traits", ["bad_trait"]),
        ("objects_of_study", ["bad_object"]),
        ("evidence_classes", ["bad_evidence"]),
        ("risk_classes", ["bad_risk"]),
        ("sensitivity_classes", ["bad_sensitivity"]),
        ("response_route_family", "bad_route"),
        ("novelty_level", "bad_novelty"),
    ],
)
def test_unknown_enum_values_fail_validation(field_name, bad_value):
    packet = asdict(_build())
    packet[field_name] = bad_value
    with pytest.raises(ValidationError):
        validate_broad_topic_ontology_packet_v1(packet)


@pytest.mark.parametrize(
    "marker",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "Turing test claim",
        "certification claim",
    ],
)
def test_public_claim_markers_fail_validation(marker):
    packet = asdict(_build())
    packet["safe_metadata"] = {"note": marker}
    with pytest.raises(ValidationError):
        validate_broad_topic_ontology_packet_v1(packet)


def test_module_does_not_import_or_call_protected_runtime_files():
    import weslr.broad_topic_ontology as mod

    source = inspect.getsource(mod)
    for forbidden in ("chat_responder", "weslr.main", "dialogue", "chat_ui"):
        assert forbidden not in source


def test_classify_function_matches_build_function():
    packet_one = classify_broad_topic_ontology_v1(**_base_kwargs())
    packet_two = build_broad_topic_ontology_packet_v1(**_base_kwargs())
    assert asdict(packet_one) == asdict(packet_two)
