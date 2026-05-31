from __future__ import annotations

from dataclasses import replace
import inspect
import sys

import pytest

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
from weslr.research_conversation_planner import (
    ResearchConversationPlan,
    build_initial_research_conversation_plan_examples_v1,
    build_research_conversation_plan_v1,
    plan_research_conversation_v1,
    summarize_research_conversation_plan_v1,
    to_research_conversation_plan_json_safe_v1,
    validate_research_conversation_plan_v1,
)


def _base_intake(**overrides):
    data = {
        "safe_topic_descriptor": "Generic technical research topic",
        "prompt_labels": ("technical research",),
        "owner_intent_labels": ("research",),
        "risk_hints": ("medium uncertainty",),
        "known_unknown_hints": ("unfamiliar",),
        "existing_behavior_pack_refs": (),
    }
    data.update(overrides)
    return build_broad_topic_domain_intake_v1(**data)


def _plan_from_intake(intake):
    return build_research_conversation_plan_v1(domain_intake=intake)


def test_module_imports_safely():
    import weslr.research_conversation_planner as mod

    assert mod.HELPER_TYPE_V1 == "research_conversation_planner_helper_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_research_plan():
    intake = _base_intake()
    plan1 = _plan_from_intake(intake)
    plan2 = _plan_from_intake(intake)
    assert plan1 == plan2


def test_wifi_rf_sensing_plan_classified():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy", "consent required"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
        known_unknown_hints=("unfamiliar", "researchable"),
    )
    plan = _plan_from_intake(intake)
    assert plan.domain_family == "privacy_sensitive_technology"
    assert plan.plan_type in {"risk_boundary_review", "map_research_questions"}
    assert plan.requires_boundary_review is True
    assert plan.requires_evidence_mapping is True
    assert plan.recommended_response_mode in {"refusal_boundary", "research_plan"}


def test_wifi_rf_requires_boundary_review_and_evidence_mapping():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = _plan_from_intake(intake)
    assert plan.requires_boundary_review is True
    assert plan.requires_evidence_mapping is True


def test_wifi_rf_asks_consent_lawfulness_question():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = _plan_from_intake(intake)
    questions = " ".join(plan.owner_questions)
    assert "consent" in questions
    assert "lawful" in questions or "lawfulness" in questions


def test_wifi_rf_blocks_covert_tracking_and_deployment_guidance():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = _plan_from_intake(intake)
    blob = " ".join(plan.safe_next_steps + plan.boundary_warnings + plan.prototype_phase_outline)
    assert "covert" not in blob
    assert "tracking" not in blob or plan.domain_family == "privacy_sensitive_technology"
    assert "deployment" not in blob or "research" in blob


def test_wifi_rf_blocks_prototype_details_unless_allowed_by_intake():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = _plan_from_intake(intake)
    assert plan.prototype_planning_allowed is False
    assert plan.prototype_phase_outline
    assert any("deferred" in item or "allowed" in item for item in plan.prototype_phase_outline)


def test_wifi_rf_lawful_consent_intake_may_allow_high_level_prototype_outline_only():
    intake = _base_intake(
        safe_topic_descriptor="WiFi/RF sensing for human presence with consent in a house",
        prompt_labels=("wifi sensing", "consent", "lawful only"),
        owner_intent_labels=("build prototype",),
        risk_hints=("consent required", "lawful"),
        known_unknown_hints=("unfamiliar",),
    )
    plan = _plan_from_intake(intake)
    assert plan.prototype_planning_allowed is True
    assert plan.prototype_phase_outline
    assert any("lawful" in item or "consent" in item for item in plan.safe_next_steps + plan.owner_questions)


@pytest.mark.parametrize(
    "safe_topic_descriptor, prompt_labels, owner_intent_labels, expected_family, expected_plan_type",
    [
        (
            "Industrial automation troubleshooting for a control system",
            ("industrial automation", "troubleshooting", "PLC", "equipment"),
            ("troubleshooting",),
            "industrial_automation",
            "troubleshooting_plan",
        ),
        (
            "Legal/privacy policy review for a new workflow",
            ("legal privacy", "policy review", "compliance"),
            ("safety legal privacy review",),
            "legal_privacy",
            "risk_boundary_review",
        ),
        (
            "Materials discovery feasibility planning",
            ("materials discovery", "feasibility", "research"),
            ("evaluate feasibility",),
            "materials_discovery",
            "feasibility_review",
        ),
        (
            "Energy system prototype planning",
            ("energy systems", "prototype", "battery", "power"),
            ("build prototype",),
            "energy_systems",
            "prototype_path_high_level",
        ),
        (
            "Software product planning for an owner-facing feature",
            ("software product", "product strategy", "feature planning"),
            ("commercial product strategy",),
            "software_product",
            "product_development_plan",
        ),
        (
            "Website public launch planning",
            ("website", "public launch", "landing page", "seo"),
            ("commercial product strategy",),
            "website_public_launch",
            "product_development_plan",
        ),
        (
            "Language and vocabulary discovery for a new term",
            ("language", "vocabulary", "definition"),
            ("learn explain",),
            "language_vocabulary",
            "explain_topic",
        ),
    ],
)
def test_domain_plans_classified(safe_topic_descriptor, prompt_labels, owner_intent_labels, expected_family, expected_plan_type):
    intake = _base_intake(
        safe_topic_descriptor=safe_topic_descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=("medium uncertainty",),
        known_unknown_hints=("known existing pack",),
    )
    plan = _plan_from_intake(intake)
    assert plan.domain_family == expected_family
    assert plan.plan_type == expected_plan_type


def test_unknown_domain_plan_uses_clarification_or_evidence_path():
    intake = _base_intake(
        safe_topic_descriptor="Unknown domain with unclear goal and no prior pack",
        prompt_labels=("unknown", "novel"),
        owner_intent_labels=("unknown",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    plan = _plan_from_intake(intake)
    assert plan.domain_family == "unknown_domain"
    assert plan.plan_type in {"clarifying_intake_plan", "evidence_collection_plan"}
    assert plan.recommended_response_mode in {"clarifying_question", "evidence_request"}


def test_validates_normal_plan():
    plan = _plan_from_intake(_base_intake())
    assert validate_research_conversation_plan_v1(plan) is True


def test_json_safe_export_works():
    plan = _plan_from_intake(_base_intake())
    exported = to_research_conversation_plan_json_safe_v1(plan)
    assert isinstance(exported, dict)
    assert isinstance(exported["knowns"], list)
    assert isinstance(exported["owner_questions"], list)
    assert exported["plan_type"] == plan.plan_type


def test_summary_includes_core_requirements():
    summary = summarize_research_conversation_plan_v1(_plan_from_intake(_base_intake()))
    assert summary.plan_type in {"map_research_questions", "clarifying_intake_plan", "feasibility_review", "product_development_plan", "explain_topic", "behavior_pack_seed_plan", "evidence_collection_plan", "risk_boundary_review", "troubleshooting_plan", "prototype_path_high_level"}
    assert summary.domain_family == "technical_research"
    assert isinstance(summary.requires_boundary_review, bool)
    assert isinstance(summary.requires_evidence_mapping, bool)


def test_initial_examples_exist():
    examples = build_initial_research_conversation_plan_examples_v1()
    assert len(examples) >= 8


def test_no_initial_example_allows_public_claim():
    for plan in build_initial_research_conversation_plan_examples_v1():
        assert plan.public_claim_allowed is False


def test_no_initial_example_claims_learning():
    for plan in build_initial_research_conversation_plan_examples_v1():
        assert plan.learning_claimed is False


def test_no_initial_example_has_runtime_authority():
    for plan in build_initial_research_conversation_plan_examples_v1():
        assert plan.runtime_authority is False


def test_no_initial_example_writes_state():
    for plan in build_initial_research_conversation_plan_examples_v1():
        assert plan.writes_state is False


def test_no_initial_example_uses_model_provider():
    for plan in build_initial_research_conversation_plan_examples_v1():
        assert plan.model_provider_used is False


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
    plan = replace(_plan_from_intake(_base_intake()), **{field_name: value})
    with pytest.raises(ValueError):
        validate_research_conversation_plan_v1(plan)


@pytest.mark.parametrize("field_name", ["raw_prompt", "raw_answer", "transcript"])
def test_raw_leak_fields_fail_validation(field_name):
    payload = to_research_conversation_plan_json_safe_v1(_plan_from_intake(_base_intake()))
    payload[field_name] = "leak"
    with pytest.raises(ValueError):
        validate_research_conversation_plan_v1(payload)


@pytest.mark.parametrize(
    "field_name, value, error_fragment",
    [
        ("plan_type", "bad_plan_type", "unknown_plan_type"),
        ("recommended_response_mode", "bad_mode", "unknown_recommended_response_mode"),
        ("domain_family", "bad_domain", "unknown_domain_family"),
        ("novelty_level", "bad_novelty", "unknown_novelty_level"),
        ("owner_intent", "bad_intent", "unknown_owner_intent"),
    ],
)
def test_unknown_enum_values_fail_validation(field_name, value, error_fragment):
    payload = to_research_conversation_plan_json_safe_v1(_plan_from_intake(_base_intake()))
    payload[field_name] = value
    with pytest.raises(ValueError) as exc:
        validate_research_conversation_plan_v1(payload)
    assert error_fragment in str(exc.value)


def test_public_iss_and_claim_markers_fail_validation():
    payload = to_research_conversation_plan_json_safe_v1(_plan_from_intake(_base_intake()))
    payload["boundary_warnings"][0] = "public ISS wording"
    with pytest.raises(ValueError):
        validate_research_conversation_plan_v1(payload)


@pytest.mark.parametrize(
    "marker",
    ["AGI claim", "consciousness claim", "sentience claim", "Turing claim", "certification claim"],
)
def test_claim_markers_fail_validation(marker):
    payload = to_research_conversation_plan_json_safe_v1(_plan_from_intake(_base_intake()))
    payload["owner_questions"][0] = marker
    with pytest.raises(ValueError):
        validate_research_conversation_plan_v1(payload)


@pytest.mark.parametrize("marker", ["covert tracking", "unsafe deployment", "covert deployment"])
def test_unsafe_markers_fail_validation(marker):
    payload = to_research_conversation_plan_json_safe_v1(_plan_from_intake(_base_intake()))
    payload["safe_next_steps"][0] = marker
    with pytest.raises(ValueError):
        validate_research_conversation_plan_v1(payload)


def test_module_does_not_reference_protected_runtime_files():
    source = inspect.getsource(__import__("weslr.research_conversation_planner", fromlist=["*"]))
    assert "chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source
