from __future__ import annotations

from dataclasses import asdict
import inspect
import sys

import pytest

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
from weslr.broad_topic_ontology import build_broad_topic_ontology_packet_v1
from weslr.privacy_sensitive_technology_boundary import build_privacy_sensitive_technology_boundary_v1
from weslr.project_brief_builder import (
    ProjectBrief,
    build_initial_project_brief_examples_v1,
    build_project_brief_from_research_plan_v1,
    build_project_brief_v1,
    summarize_project_brief_v1,
    to_project_brief_json_safe_v1,
    validate_project_brief_v1,
)
from weslr.research_conversation_planner import build_research_conversation_plan_v1


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


def _plan(intake):
    return build_research_conversation_plan_v1(domain_intake=intake)


def _boundary(intake, plan):
    return build_privacy_sensitive_technology_boundary_v1(domain_intake=intake, research_plan=plan)


def _brief(intake, with_boundary=False, project_title=None, ontology_packet=None):
    plan = _plan(intake)
    boundary = _boundary(intake, plan) if with_boundary else None
    return build_project_brief_v1(
        plan,
        boundary=boundary,
        ontology_packet=ontology_packet,
        domain_intake=intake,
        project_title=project_title,
    )


def test_module_imports_safely():
    import weslr.project_brief_builder as mod

    assert mod.HELPER_TYPE_V1 == "project_brief_builder_helper_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


@pytest.mark.parametrize(
    "intake_kwargs, expected_type, expected_stage, expected_next",
    [
        (
            dict(
                safe_topic_descriptor="WiFi/RF sensing for consent-based self-care in a household",
                prompt_labels=("wifi sensing", "self-care", "privacy", "consent"),
                owner_intent_labels=("research",),
                risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
                known_unknown_hints=("unfamiliar", "researchable"),
            ),
            "privacy_sensitive_research_brief",
            "needs_evidence_before_build",
            "evidence_map",
        ),
        (
            dict(
                safe_topic_descriptor="Metamaterials frontier research",
                prompt_labels=("metamaterials", "materials discovery", "frontier research", "experimental validation"),
                owner_intent_labels=("evaluate feasibility",),
                risk_hints=("high uncertainty",),
                known_unknown_hints=("frontier", "high uncertainty"),
            ),
            "materials_discovery_project_brief",
            "needs_evidence_before_build",
            "evidence_map",
        ),
        (
            dict(
                safe_topic_descriptor="AI agent architecture and governance",
                prompt_labels=("ai systems", "agentic systems", "cognitive architecture", "ai safety governance"),
                owner_intent_labels=("research",),
                risk_hints=("public-facing sensitivity", "safety critical"),
                known_unknown_hints=("adjacent",),
            ),
            "ai_system_project_brief",
            "architecture_ready",
            "architecture_plan",
        ),
        (
            dict(
                safe_topic_descriptor="Medical software regulated pathway",
                prompt_labels=("medicine health research", "software product", "clinical validation"),
                owner_intent_labels=("evaluate feasibility",),
                risk_hints=("medical sensitive", "regulated domain"),
                known_unknown_hints=("unfamiliar",),
            ),
            "medical_software_pathway_brief",
            "needs_evidence_before_build",
            "evidence_map",
        ),
        (
            dict(
                safe_topic_descriptor="Industrial automation troubleshooting for a control system",
                prompt_labels=("industrial automation", "troubleshooting", "PLC", "equipment"),
                owner_intent_labels=("troubleshooting",),
                risk_hints=("equipment safety",),
                known_unknown_hints=("adjacent",),
            ),
            "industrial_automation_project_brief",
            "prototype_planning",
            "architecture_plan",
        ),
        (
            dict(
                safe_topic_descriptor="Software product planning for an owner-facing feature",
                prompt_labels=("software product", "product strategy", "feature planning"),
                owner_intent_labels=("commercial product strategy",),
                risk_hints=("medium uncertainty",),
                known_unknown_hints=("known existing pack",),
            ),
            "software_product_brief",
            "architecture_ready",
            "architecture_plan",
        ),
        (
            dict(
                safe_topic_descriptor="Theory of mind conceptual research",
                prompt_labels=("theory of mind", "philosophy of mind", "cognitive science"),
                owner_intent_labels=("learn explain",),
                risk_hints=("high uncertainty",),
                known_unknown_hints=("high uncertainty",),
            ),
            "conceptual_research_brief",
            "concept_only",
            "clarifying_questions",
        ),
        (
            dict(
                safe_topic_descriptor="Unknown future topic",
                prompt_labels=("unknown", "novel"),
                owner_intent_labels=("unknown",),
                risk_hints=("high uncertainty",),
                known_unknown_hints=("high uncertainty",),
            ),
            "unknown_domain_project_brief",
            "concept_only",
            "clarifying_questions",
        ),
    ],
)
def test_domain_briefs_classify_correctly(intake_kwargs, expected_type, expected_stage, expected_next):
    intake = _intake(**intake_kwargs)
    brief = _brief(intake, with_boundary=(expected_type == "privacy_sensitive_research_brief"))
    assert brief.brief_type == expected_type
    assert brief.project_stage == expected_stage
    assert brief.recommended_next_artifact == expected_next


def test_builds_deterministic_project_brief():
    intake = _intake()
    brief1 = _brief(intake)
    brief2 = _brief(intake)
    assert brief1 == brief2


def test_builds_brief_from_research_plan_and_explicit_ontology_packet():
    intake = _intake(
        safe_topic_descriptor="WiFi/RF sensing for consent-based self-care in a household",
        prompt_labels=("wifi sensing", "self-care", "privacy", "consent"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
        known_unknown_hints=("unfamiliar", "researchable"),
    )
    plan = _plan(intake)
    boundary = _boundary(intake, plan)
    ontology = build_broad_topic_ontology_packet_v1(
        safe_topic_descriptor=intake.safe_topic_descriptor,
        prompt_labels=("wifi sensing", "self-care", "privacy", "consent"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("researchable",),
        existing_behavior_pack_refs=(),
    )
    brief = build_project_brief_from_research_plan_v1(
        research_plan=plan,
        boundary=boundary,
        ontology_packet=ontology,
        domain_intake=intake,
    )
    assert brief.source_plan_id == plan.plan_id
    assert brief.source_intake_id == intake.intake_id
    assert brief.source_ontology_id == ontology.ontology_id
    assert brief.source_boundary_id == boundary.boundary_id
    assert brief.brief_type == "privacy_sensitive_research_brief"
    assert validate_project_brief_v1(brief) is True


def test_validates_normal_project_brief():
    brief = _brief(_intake())
    assert validate_project_brief_v1(brief) is True


def test_json_safe_export_works():
    brief = _brief(_intake())
    exported = to_project_brief_json_safe_v1(brief)
    assert isinstance(exported, dict)
    assert isinstance(exported["goals"], list)
    assert isinstance(exported["privacy_requirements"], list)
    assert exported["brief_type"] == brief.brief_type


def test_summary_includes_brief_type_stage_and_next_artifact():
    brief = _brief(_intake())
    summary = summarize_project_brief_v1(brief)
    assert summary.brief_type == brief.brief_type
    assert summary.project_stage == brief.project_stage
    assert summary.recommended_next_artifact == brief.recommended_next_artifact
    assert summary.domain_family == brief.domain_family


def test_initial_examples_exist():
    examples = build_initial_project_brief_examples_v1()
    assert len(examples) >= 8


def _find_example(examples, brief_type):
    for brief in examples:
        if brief.brief_type == brief_type:
            return brief
    raise AssertionError(f"missing example {brief_type}")


def test_wifi_rf_self_care_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "privacy_sensitive_research_brief")
    assert "WiFi/RF" in brief.project_title or "WiFi" in brief.project_title


def test_wifi_rf_self_care_brief_is_privacy_sensitive_research_brief():
    brief = _find_example(build_initial_project_brief_examples_v1(), "privacy_sensitive_research_brief")
    assert brief.project_stage in {"research_planning", "needs_evidence_before_build"}
    assert brief.recommended_next_artifact in {"evidence_map", "architecture_plan"}


def test_wifi_rf_self_care_brief_includes_local_first_data_minimization_user_control_requirements():
    brief = _find_example(build_initial_project_brief_examples_v1(), "privacy_sensitive_research_brief")
    blob = " ".join(brief.privacy_requirements + brief.boundary_requirements)
    assert "local-first" in blob
    assert "data minimization" in blob
    assert "user control" in blob


def test_wifi_rf_self_care_brief_blocks_diagnosis_treatment_authority():
    brief = _find_example(build_initial_project_brief_examples_v1(), "privacy_sensitive_research_brief")
    assert "prescriptive health guidance" not in " ".join(brief.medical_claim_boundaries)
    payload = to_project_brief_json_safe_v1(brief)
    payload["medical_claim_boundaries"][0] = "diagnosis authority"
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


def test_metamaterials_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "materials_discovery_project_brief")
    assert "Metamaterials" in brief.project_title or "materials" in brief.project_title.lower()


def test_metamaterials_brief_includes_evidence_and_experimental_validation_requirements():
    brief = _find_example(build_initial_project_brief_examples_v1(), "materials_discovery_project_brief")
    blob = " ".join(brief.evidence_requirements + brief.validation_requirements)
    assert "technical literature" in blob
    assert "validation" in blob


def test_ai_agent_architecture_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "ai_system_project_brief")
    assert "AI" in brief.project_title


def test_ai_agent_architecture_brief_includes_safety_governance_evaluation_requirements():
    brief = _find_example(build_initial_project_brief_examples_v1(), "ai_system_project_brief")
    blob = " ".join(brief.evidence_requirements + brief.boundary_requirements + brief.safety_requirements)
    assert "governance" in blob
    assert "evaluation" in blob
    assert "safety" in blob


def test_ai_agent_architecture_brief_does_not_claim_agi():
    brief = _find_example(build_initial_project_brief_examples_v1(), "ai_system_project_brief")
    blob = " ".join([brief.project_title, brief.project_purpose, brief.problem_statement, brief.goals[0]]).lower()
    assert "agi" not in blob


def test_medical_software_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "medical_software_pathway_brief")
    assert "Medical" in brief.project_title


def test_medical_software_brief_includes_clinical_regulatory_evidence_requirements():
    brief = _find_example(build_initial_project_brief_examples_v1(), "medical_software_pathway_brief")
    blob = " ".join(brief.evidence_requirements + brief.validation_requirements + brief.legal_requirements)
    assert "clinical" in blob
    assert "regulatory" in blob


def test_medical_software_brief_blocks_diagnosis_treatment_authority():
    brief = _find_example(build_initial_project_brief_examples_v1(), "medical_software_pathway_brief")
    payload = to_project_brief_json_safe_v1(brief)
    payload["medical_claim_boundaries"][0] = "treatment authority"
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


def test_industrial_automation_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "industrial_automation_project_brief")
    assert "Industrial" in brief.project_title


def test_software_product_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "software_product_brief")
    assert "software product" in brief.project_title.lower() or "Software" in brief.project_title


def test_theory_of_mind_conceptual_brief_exists():
    brief = _find_example(build_initial_project_brief_examples_v1(), "conceptual_research_brief")
    assert "Conceptual" in brief.project_title or "research" in brief.project_title.lower()


def test_theory_of_mind_brief_does_not_claim_consciousness_or_sentience():
    brief = _find_example(build_initial_project_brief_examples_v1(), "conceptual_research_brief")
    blob = " ".join([brief.project_title, brief.project_purpose, brief.problem_statement, *brief.goals]).lower()
    assert "consciousness" not in blob
    assert "sentience" not in blob


def test_unknown_domain_brief_uses_clarification_and_evidence_first():
    brief = _find_example(build_initial_project_brief_examples_v1(), "unknown_domain_project_brief")
    assert brief.project_stage == "concept_only"
    assert brief.recommended_next_artifact == "clarifying_questions"


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("public_claim_allowed", True),
        ("runtime_authority", True),
        ("writes_state", True),
        ("model_provider_used", True),
        ("learning_claimed", True),
        ("file_write_authority_granted", True),
    ],
)
def test_boolean_invariants_fail_validation(field_name, value):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload[field_name] = value
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


@pytest.mark.parametrize("field_name", ["raw_prompt", "raw_answer", "transcript"])
def test_raw_leak_fields_fail_validation(field_name):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload[field_name] = "leak"
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


@pytest.mark.parametrize(
    "field_name, value, error_fragment",
    [
        ("brief_type", "bad_brief_type", "unknown_brief_type"),
        ("project_stage", "bad_stage", "unknown_project_stage"),
        ("prototype_allowed_level", "bad_level", "unknown_prototype_allowed_level"),
        ("recommended_next_artifact", "bad_artifact", "unknown_recommended_next_artifact"),
    ],
)
def test_unknown_enum_values_fail_validation(field_name, value, error_fragment):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload[field_name] = value
    with pytest.raises(ValueError) as exc:
        validate_project_brief_v1(payload)
    assert error_fragment in str(exc.value)


def test_public_iss_wording_fails_validation():
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload["boundary_requirements"][0] = "public ISS wording"
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


@pytest.mark.parametrize(
    "marker",
    ["AGI claim", "consciousness claim", "sentience claim", "Turing claim", "certification claim"],
)
def test_agi_consciousness_turing_certification_claim_markers_fail_validation(marker):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload["project_purpose"] = marker
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


@pytest.mark.parametrize("marker", ["covert tracking", "unsafe deployment", "covert deployment"])
def test_unsafe_deployment_markers_fail_validation(marker):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload["constraints"][0] = marker
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


@pytest.mark.parametrize("marker", ["diagnosis authority", "treatment authority", "prescription authority"])
def test_diagnosis_treatment_authority_markers_fail_validation(marker):
    payload = to_project_brief_json_safe_v1(_brief(_intake()))
    payload["medical_claim_boundaries"][0] = marker
    with pytest.raises(ValueError):
        validate_project_brief_v1(payload)


def test_module_does_not_reference_protected_runtime_files():
    source = inspect.getsource(__import__("weslr.project_brief_builder", fromlist=["*"]))
    assert "chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source
