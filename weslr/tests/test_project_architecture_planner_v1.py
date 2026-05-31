from __future__ import annotations

from dataclasses import asdict
import inspect
import sys

import pytest

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
from weslr.project_architecture_planner import (
    ArchitecturePlan,
    build_initial_project_architecture_examples_v1,
    build_project_architecture_from_brief_v1,
    build_project_architecture_plan_v1,
    summarize_project_architecture_plan_v1,
    to_project_architecture_json_safe_v1,
    validate_project_architecture_plan_v1,
)
from weslr.project_brief_builder import build_initial_project_brief_examples_v1, build_project_brief_v1
from weslr.privacy_sensitive_technology_boundary import build_privacy_sensitive_technology_boundary_v1
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



def _brief(intake, with_boundary=False, project_title=None):
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    boundary = build_privacy_sensitive_technology_boundary_v1(domain_intake=intake, research_plan=plan) if with_boundary else None
    return build_project_brief_v1(
        plan,
        boundary=boundary,
        domain_intake=intake,
        project_title=project_title,
    )



def _find_example(examples, architecture_type):
    for plan in examples:
        if plan.architecture_type == architecture_type:
            return plan
    raise AssertionError(f"missing example {architecture_type}")



def test_module_imports_safely():
    import weslr.project_architecture_planner as mod

    assert mod.HELPER_TYPE_V1 == "project_architecture_planner_helper_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


@pytest.mark.parametrize(
    "intake_kwargs, expected_type, expected_strategy, expected_next",
    [
        (
            dict(
                safe_topic_descriptor="WiFi/RF sensing for consent-based self-care in a household",
                prompt_labels=("wifi sensing", "self-care", "privacy", "consent"),
                owner_intent_labels=("research",),
                risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
                known_unknown_hints=("unfamiliar", "researchable"),
            ),
            "privacy_sensitive_assistive_architecture",
            "local_first",
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
            "materials_research_architecture",
            "cloud_optional_later",
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
            "ai_system_architecture",
            "cloud_optional_later",
            "validation_plan",
        ),
        (
            dict(
                safe_topic_descriptor="Medical software regulated pathway",
                prompt_labels=("medicine health research", "software product", "clinical validation"),
                owner_intent_labels=("evaluate feasibility",),
                risk_hints=("medical sensitive", "regulated domain"),
                known_unknown_hints=("unfamiliar",),
            ),
            "medical_software_pathway_architecture",
            "unknown_pending_requirements",
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
            "industrial_automation_architecture",
            "local_only",
            "validation_plan",
        ),
        (
            dict(
                safe_topic_descriptor="Software product planning for an owner-facing feature",
                prompt_labels=("software product", "product strategy", "feature planning"),
                owner_intent_labels=("commercial product strategy",),
                risk_hints=("medium uncertainty",),
                known_unknown_hints=("known existing pack",),
            ),
            "software_product_architecture",
            "cloud_optional_later",
            "stack_decision",
        ),
        (
            dict(
                safe_topic_descriptor="Theory of mind conceptual research",
                prompt_labels=("theory of mind", "philosophy of mind", "cognitive science"),
                owner_intent_labels=("learn explain",),
                risk_hints=("high uncertainty",),
                known_unknown_hints=("high uncertainty",),
            ),
            "conceptual_research_architecture",
            "local_only",
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
            "unknown_domain_architecture",
            "unknown_pending_requirements",
            "clarifying_questions",
        ),
    ],
)
def test_domain_architecture_types_and_strategies(intake_kwargs, expected_type, expected_strategy, expected_next):
    intake = _intake(**intake_kwargs)
    brief = _brief(intake, with_boundary=(expected_type == "privacy_sensitive_assistive_architecture"))
    plan = build_project_architecture_from_brief_v1(brief)
    assert plan.architecture_type == expected_type
    assert plan.local_cloud_strategy == expected_strategy
    assert plan.recommended_next_artifact == expected_next



def test_builds_deterministic_architecture_plan():
    brief = _brief(_intake())
    plan1 = build_project_architecture_plan_v1(brief)
    plan2 = build_project_architecture_plan_v1(brief)
    assert plan1 == plan2



def test_builds_architecture_from_project_brief():
    brief = _brief(
        _intake(
            safe_topic_descriptor="WiFi/RF sensing for consent-based self-care in a household",
            prompt_labels=("wifi sensing", "self-care", "privacy", "consent"),
            owner_intent_labels=("research",),
            risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
            known_unknown_hints=("unfamiliar", "researchable"),
        ),
        with_boundary=True,
    )
    plan = build_project_architecture_from_brief_v1(brief)
    assert plan.source_brief_id == brief.brief_id
    assert plan.project_title == brief.project_title
    assert plan.domain_family == brief.domain_family
    assert plan.architecture_type == "privacy_sensitive_assistive_architecture"
    assert validate_project_architecture_plan_v1(plan) is True



def test_validates_normal_project_architecture_plan():
    plan = build_project_architecture_plan_v1(_brief(_intake()))
    assert validate_project_architecture_plan_v1(plan) is True



def test_json_safe_export_works():
    plan = build_project_architecture_plan_v1(_brief(_intake()))
    exported = to_project_architecture_json_safe_v1(plan)
    assert isinstance(exported, dict)
    assert isinstance(exported["architecture_goals"], list)
    assert exported["architecture_type"] == plan.architecture_type



def test_summary_includes_architecture_type_selected_architecture_and_next_artifact():
    plan = build_project_architecture_plan_v1(_brief(_intake()))
    summary = summarize_project_architecture_plan_v1(plan)
    assert summary.architecture_type == plan.architecture_type
    assert summary.selected_architecture == plan.selected_architecture
    assert summary.recommended_next_artifact == plan.recommended_next_artifact
    assert summary.domain_family == plan.domain_family



def test_initial_examples_exist():
    examples = build_initial_project_architecture_examples_v1()
    assert len(examples) >= 8



def test_wifi_rf_self_care_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    assert "local-first" in plan.selected_architecture or "assistive" in plan.selected_architecture



def test_wifi_rf_self_care_architecture_is_privacy_sensitive_assistive_architecture():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    assert plan.local_cloud_strategy == "local_first"
    assert plan.recommended_next_artifact == "evidence_map"



def test_wifi_rf_self_care_uses_local_first_strategy():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    assert plan.local_cloud_strategy == "local_first"



def test_wifi_rf_self_care_includes_privacy_audit_user_control_controls():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    blob = " ".join(plan.privacy_controls + plan.safety_controls + plan.interface_surfaces)
    assert "audit" in blob
    assert "user control" in blob
    assert "consent" in blob



def test_wifi_rf_self_care_blocks_covert_tracking():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    assert "no covert tracking" in " ".join(plan.privacy_controls)
    payload = to_project_architecture_json_safe_v1(plan)
    payload["privacy_controls"][0] = "covert tracking implementation"
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)



def test_wifi_rf_self_care_blocks_diagnosis_treatment_authority():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "privacy_sensitive_assistive_architecture")
    payload = to_project_architecture_json_safe_v1(plan)
    payload["medical_claim_controls"][0] = "diagnosis authority"
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)



def test_metamaterials_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "materials_research_architecture")
    assert "materials" in plan.selected_architecture.lower() or "metamaterial" in plan.selected_architecture.lower()



def test_metamaterials_architecture_includes_evidence_validation_uncertainty_handling():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "materials_research_architecture")
    blob = " ".join(plan.architecture_goals + plan.validation_points + plan.failure_modes)
    assert "validation" in blob
    assert "uncertainty" in blob
    assert "evidence" in blob



def test_ai_agent_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "ai_system_architecture")
    assert "AI" in plan.selected_architecture or "ai" in plan.selected_architecture.lower()



def test_ai_agent_architecture_includes_governance_evaluation_safety_components():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "ai_system_architecture")
    blob = " ".join(plan.architecture_goals + plan.component_map + plan.safety_controls)
    assert "governance" in blob
    assert "evaluation" in blob
    assert "safety" in blob



def test_ai_agent_architecture_does_not_claim_agi():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "ai_system_architecture")
    blob = " ".join([plan.selected_architecture, *plan.architecture_goals]).lower()
    assert "agi" not in blob



def test_medical_software_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "medical_software_pathway_architecture")
    assert "medical" in plan.selected_architecture.lower()



def test_medical_software_architecture_includes_clinical_regulatory_safety_validation():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "medical_software_pathway_architecture")
    blob = " ".join(plan.medical_claim_controls + plan.validation_points + plan.safety_controls)
    assert "clinical" in blob
    assert "regulatory" in blob
    assert "safety" in blob



def test_medical_software_architecture_blocks_diagnosis_treatment_authority():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "medical_software_pathway_architecture")
    payload = to_project_architecture_json_safe_v1(plan)
    payload["medical_claim_controls"][0] = "treatment authority"
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)



def test_industrial_automation_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "industrial_automation_architecture")
    assert "industrial" in plan.selected_architecture.lower()



def test_industrial_automation_architecture_includes_safety_config_normalization_reporting():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "industrial_automation_architecture")
    blob = " ".join(plan.component_map + plan.safety_controls + plan.validation_points)
    assert "config" in blob
    assert "safety" in blob
    assert "report" in blob



def test_software_product_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "software_product_architecture")
    assert "product" in plan.selected_architecture.lower()



def test_software_product_architecture_includes_user_flow_interface_storage_acceptance_criteria():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "software_product_architecture")
    blob = " ".join(plan.component_map + plan.interface_surfaces + plan.storage_strategy + plan.validation_points)
    assert "user flow" in blob
    assert "interface" in blob
    assert "storage" in blob
    assert "acceptance" in blob



def test_theory_of_mind_conceptual_architecture_exists():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "conceptual_research_architecture")
    assert "conceptual" in plan.selected_architecture.lower()



def test_theory_of_mind_architecture_includes_definition_claim_evidence_uncertainty_maps():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "conceptual_research_architecture")
    blob = " ".join(plan.component_map + plan.validation_points + plan.failure_modes)
    assert "definition" in blob
    assert "claim" in blob
    assert "evidence" in blob
    assert "uncertainty" in blob



def test_theory_of_mind_architecture_does_not_claim_consciousness_or_sentience():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "conceptual_research_architecture")
    blob = " ".join([plan.selected_architecture, *plan.architecture_goals]).lower()
    assert "consciousness" not in blob
    assert "sentience" not in blob



def test_unknown_domain_architecture_uses_clarification_and_evidence_first():
    plan = _find_example(build_initial_project_architecture_examples_v1(), "unknown_domain_architecture")
    assert plan.selected_architecture.startswith("clarification-first")
    assert plan.recommended_next_artifact == "clarifying_questions"


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
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake())))
    payload[field_name] = value
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)


@pytest.mark.parametrize("field_name", ["raw_prompt", "raw_answer", "transcript"])
def test_raw_leak_fields_fail_validation(field_name):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake())))
    payload[field_name] = "leak"
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)


@pytest.mark.parametrize(
    "field_name, value, error_fragment",
    [
        ("architecture_type", "bad_architecture_type", "unknown_architecture_type"),
        ("local_cloud_strategy", "bad_strategy", "unknown_local_cloud_strategy"),
        ("prototype_allowed_level", "bad_level", "unknown_prototype_allowed_level"),
        ("recommended_next_artifact", "bad_artifact", "unknown_recommended_next_artifact"),
    ],
)
def test_unknown_enum_values_fail_validation(field_name, value, error_fragment):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake())))
    payload[field_name] = value
    with pytest.raises(ValueError) as excinfo:
        validate_project_architecture_plan_v1(payload)
    assert error_fragment in str(excinfo.value)


@pytest.mark.parametrize("marker", ["public ISS wording", "official AGI certification claim", "turing test certification"])
def test_public_iss_and_claim_markers_fail_validation(marker):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake())))
    payload["selected_architecture"] = marker
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)


@pytest.mark.parametrize("marker", ["deployment before review", "unsafe deployment", "covert rollout"])
def test_unsafe_deployment_marker_fails_validation(marker):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake())))
    payload["safety_controls"][0] = marker
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)


@pytest.mark.parametrize("marker", ["covert tracking implementation", "tracking pipeline", "hidden tracking"])
def test_covert_tracking_marker_fails_validation(marker):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake(), with_boundary=True)))
    payload["privacy_controls"][0] = marker
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)


@pytest.mark.parametrize("marker", ["diagnosis authority", "treatment authority", "prescription authority"])
def test_diagnosis_treatment_authority_marker_fails_validation(marker):
    payload = to_project_architecture_json_safe_v1(build_project_architecture_plan_v1(_brief(_intake(), with_boundary=True)))
    payload["medical_claim_controls"][0] = marker
    with pytest.raises(ValueError):
        validate_project_architecture_plan_v1(payload)



def test_module_does_not_reference_protected_runtime_files():
    source = inspect.getsource(__import__("weslr.project_architecture_planner", fromlist=["*"]))
    assert "chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source
