from __future__ import annotations

from dataclasses import asdict, replace
import inspect
import sys

import pytest

from weslr.broad_topic_domain_intake import (
    BroadTopicDomainIntake,
    build_broad_topic_domain_intake_v1,
    build_initial_broad_topic_domain_intake_examples_v1,
    classify_broad_topic_domain_v1,
    summarize_broad_topic_domain_intake_v1,
    to_broad_topic_domain_intake_json_safe_v1,
    validate_broad_topic_domain_intake_v1,
)


def _base_kwargs(**overrides):
    data = {
        "safe_topic_descriptor": "Generic technical research topic",
        "prompt_labels": ("technical research",),
        "owner_intent_labels": ("research",),
        "risk_hints": ("medium uncertainty",),
        "known_unknown_hints": ("unfamiliar",),
        "existing_behavior_pack_refs": (),
    }
    data.update(overrides)
    return data


def _build(**overrides):
    return build_broad_topic_domain_intake_v1(**_base_kwargs(**overrides))


def test_module_imports_safely():
    import weslr.broad_topic_domain_intake as mod

    assert mod.HELPER_TYPE_V1 == "broad_topic_domain_intake_helper_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


@pytest.mark.parametrize(
    "kwargs, expected_family, expected_next_stage",
    [
        (
            {
                "safe_topic_descriptor": "WiFi/RF sensing for human presence and location in a house",
                "prompt_labels": ("wifi sensing", "human tracking", "privacy", "consent required"),
                "owner_intent_labels": ("research",),
                "risk_hints": ("high risk", "privacy-sensitive", "consent required", "lawful only"),
                "known_unknown_hints": ("unfamiliar", "researchable"),
            },
            "privacy_sensitive_technology",
            "research_conversation_plan",
        ),
        (
            {
                "safe_topic_descriptor": "Industrial automation troubleshooting for a control system",
                "prompt_labels": ("industrial automation", "troubleshooting", "PLC", "equipment"),
                "owner_intent_labels": ("troubleshooting",),
                "risk_hints": ("equipment safety",),
                "known_unknown_hints": ("adjacent",),
            },
            "industrial_automation",
            "direct_bounded_overview",
        ),
        (
            {
                "safe_topic_descriptor": "Legal/privacy policy review for a new workflow",
                "prompt_labels": ("legal privacy", "policy review", "compliance"),
                "owner_intent_labels": ("safety legal privacy review",),
                "risk_hints": ("legal", "privacy"),
                "known_unknown_hints": ("unfamiliar",),
            },
            "legal_privacy",
            "privacy_safety_legal_boundary_review",
        ),
        (
            {
                "safe_topic_descriptor": "Materials discovery feasibility planning",
                "prompt_labels": ("materials discovery", "feasibility", "research"),
                "owner_intent_labels": ("evaluate feasibility",),
                "risk_hints": ("high evidence need",),
                "known_unknown_hints": ("unfamiliar",),
            },
            "materials_discovery",
            "evidence_mapping",
        ),
        (
            {
                "safe_topic_descriptor": "Energy system prototype planning",
                "prompt_labels": ("energy systems", "prototype", "battery", "power"),
                "owner_intent_labels": ("build prototype",),
                "risk_hints": ("safety sensitive",),
                "known_unknown_hints": ("adjacent",),
            },
            "energy_systems",
            "prototype_path_high_level",
        ),
        (
            {
                "safe_topic_descriptor": "Software product planning for an owner-facing feature",
                "prompt_labels": ("software product", "product strategy", "feature planning"),
                "owner_intent_labels": ("commercial product strategy",),
                "risk_hints": ("medium uncertainty",),
                "known_unknown_hints": ("known existing pack",),
            },
            "software_product",
            "research_conversation_plan",
        ),
        (
            {
                "safe_topic_descriptor": "Website public launch planning",
                "prompt_labels": ("website", "public launch", "landing page", "seo"),
                "owner_intent_labels": ("build prototype",),
                "risk_hints": ("medium uncertainty",),
                "known_unknown_hints": ("adjacent",),
            },
            "website_public_launch",
            "prototype_path_high_level",
        ),
        (
            {
                "safe_topic_descriptor": "Language and vocabulary discovery for a new term",
                "prompt_labels": ("language", "vocabulary", "definition"),
                "owner_intent_labels": ("learn explain",),
                "risk_hints": ("low risk",),
                "known_unknown_hints": ("known existing pack",),
            },
            "language_vocabulary",
            "direct_bounded_overview",
        ),
        (
            {
                "safe_topic_descriptor": "Owner workflow planning for WESLR improvement",
                "prompt_labels": ("weslr", "behavior pack", "replay"),
                "owner_intent_labels": ("research",),
                "risk_hints": ("medium uncertainty",),
                "known_unknown_hints": ("known existing pack",),
                "existing_behavior_pack_refs": ("owner_workflow",),
            },
            "owner_workflow",
            "research_conversation_plan",
        ),
        (
            {
                "safe_topic_descriptor": "Unknown domain with unclear goal and no prior pack",
                "prompt_labels": ("unknown", "novel"),
                "owner_intent_labels": ("unknown",),
                "risk_hints": ("high uncertainty",),
                "known_unknown_hints": ("high uncertainty",),
            },
            "unknown_domain",
            "clarifying_question",
        ),
    ],
)
def test_domain_family_classification(kwargs, expected_family, expected_next_stage):
    intake = _build(**kwargs)
    assert intake.domain_family == expected_family
    assert intake.recommended_next_stage == expected_next_stage


def test_wifi_sensing_requires_boundary_review_and_evidence_mapping():
    intake = _build(
        safe_topic_descriptor="WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human tracking", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    assert intake.domain_family == "privacy_sensitive_technology"
    assert intake.boundary_review_required is True
    assert intake.evidence_mapping_required is True
    assert intake.risk_level == "high"
    assert intake.privacy_sensitive is True
    assert intake.legal_sensitive is True
    assert intake.prototype_planning_allowed is False


def test_wifi_sensing_with_consent_can_allow_high_level_prototype_planning_but_still_needs_boundary_review():
    intake = _build(
        safe_topic_descriptor="WiFi/RF sensing for human presence with consent in a house",
        prompt_labels=("wifi sensing", "consent", "lawful only"),
        owner_intent_labels=("build prototype",),
        risk_hints=("consent required", "lawful"),
        known_unknown_hints=("unfamiliar",),
    )
    assert intake.domain_family == "privacy_sensitive_technology"
    assert intake.boundary_review_required is True
    assert intake.prototype_planning_allowed is True
    assert intake.recommended_next_stage in {"research_conversation_plan", "privacy_safety_legal_boundary_review"}


@pytest.mark.parametrize(
    "safe_topic_descriptor, prompt_labels, owner_intent_labels, expected_family, expected_safety, expected_next_stage",
    [
        (
            "Industrial automation troubleshooting for a control system",
            ("industrial automation", "troubleshooting", "PLC", "equipment"),
            ("troubleshooting",),
            "industrial_automation",
            True,
            "direct_bounded_overview",
        ),
        (
            "Legal/privacy policy review for a new workflow",
            ("legal privacy", "policy review", "compliance"),
            ("safety legal privacy review",),
            "legal_privacy",
            False,
            "privacy_safety_legal_boundary_review",
        ),
        (
            "Materials discovery feasibility planning",
            ("materials discovery", "feasibility", "research"),
            ("evaluate feasibility",),
            "materials_discovery",
            False,
            "evidence_mapping",
        ),
        (
            "Energy system prototype planning",
            ("energy systems", "prototype", "battery", "power"),
            ("build prototype",),
            "energy_systems",
            True,
            "prototype_path_high_level",
        ),
        (
            "Robotics prototype planning",
            ("robotics", "robot", "actuator"),
            ("build prototype",),
            "robotics",
            True,
            "prototype_path_high_level",
        ),
        (
            "Software product planning for an owner-facing feature",
            ("software product", "product strategy", "feature planning"),
            ("commercial product strategy",),
            "software_product",
            False,
            "research_conversation_plan",
        ),
        (
            "Website public launch planning",
            ("website", "public launch", "landing page", "seo"),
            ("build prototype",),
            "website_public_launch",
            False,
            "prototype_path_high_level",
        ),
        (
            "Language and vocabulary discovery for a new term",
            ("language", "vocabulary", "definition"),
            ("learn explain",),
            "language_vocabulary",
            False,
            "direct_bounded_overview",
        ),
        (
            "Owner workflow planning for WESLR improvement",
            ("weslr", "behavior pack", "replay"),
            ("research",),
            "owner_workflow",
            False,
            "research_conversation_plan",
        ),
    ],
)
def test_domain_examples_and_boundaries(safe_topic_descriptor, prompt_labels, owner_intent_labels, expected_family, expected_safety, expected_next_stage):
    intake = _build(
        safe_topic_descriptor=safe_topic_descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=("medium uncertainty",),
        known_unknown_hints=("known existing pack",),
    )
    assert intake.domain_family == expected_family
    assert intake.safety_sensitive is expected_safety
    assert intake.recommended_next_stage == expected_next_stage


def test_unknown_domain_high_uncertainty():
    intake = _build(
        safe_topic_descriptor="Unknown domain with unclear goal and no prior pack",
        prompt_labels=("unknown", "novel"),
        owner_intent_labels=("unknown",),
        risk_hints=("high uncertainty",),
        known_unknown_hints=("high uncertainty",),
    )
    assert intake.domain_family == "unknown_domain"
    assert intake.novelty_level == "high_uncertainty"
    assert intake.recommended_next_stage == "clarifying_question"
    assert intake.evidence_need_level == "must_collect_before_claims"


def test_validates_normal_intake():
    intake = _build()
    assert validate_broad_topic_domain_intake_v1(intake) is True


def test_json_safe_export_works():
    intake = _build()
    exported = to_broad_topic_domain_intake_json_safe_v1(intake)
    assert isinstance(exported, dict)
    assert isinstance(exported["risk_labels"], list)
    assert isinstance(exported["candidate_behavior_pack_labels"], list)
    assert exported["safe_topic_descriptor"] == intake.safe_topic_descriptor


def test_summary_includes_core_fields():
    summary = summarize_broad_topic_domain_intake_v1(_build())
    assert summary.domain_family == "technical_research"
    assert summary.novelty_level == "unfamiliar_but_researchable"
    assert summary.risk_level == "medium"
    assert summary.recommended_next_stage == "research_conversation_plan"


def test_initial_examples_exist_and_stay_internal():
    examples = build_initial_broad_topic_domain_intake_examples_v1()
    assert len(examples) >= 8
    for example in examples:
        assert example.public_claim_allowed is False
        assert example.learning_claimed is False
        assert example.runtime_authority is False
        assert example.writes_state is False
        assert example.model_provider_used is False
        assert example.iss_internal_reference_allowed is True


def test_initial_examples_cover_required_seed_domains():
    examples = build_initial_broad_topic_domain_intake_examples_v1()
    families = {example.domain_family for example in examples}
    assert {
        "privacy_sensitive_technology",
        "industrial_automation",
        "materials_discovery",
        "legal_privacy",
        "energy_systems",
        "software_product",
        "language_vocabulary",
        "unknown_domain",
    }.issubset(families)


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
    intake = replace(_build(), **{field_name: value})
    with pytest.raises(ValueError):
        validate_broad_topic_domain_intake_v1(intake)


@pytest.mark.parametrize("field_name", ["raw_prompt", "raw_answer", "transcript"])
def test_raw_leak_fields_fail_validation(field_name):
    payload = to_broad_topic_domain_intake_json_safe_v1(_build())
    payload[field_name] = "leak"
    with pytest.raises(ValueError):
        validate_broad_topic_domain_intake_v1(payload)


@pytest.mark.parametrize(
    "field_name, value, error_fragment",
    [
        ("domain_family", "bad_domain", "unknown_domain_family"),
        ("novelty_level", "bad_novelty", "unknown_novelty_level"),
        ("owner_intent", "bad_intent", "unknown_owner_intent"),
        ("evidence_need_level", "bad_need", "unknown_evidence_need_level"),
        ("risk_level", "bad_risk", "unknown_risk_level"),
        ("recommended_next_stage", "bad_stage", "unknown_recommended_next_stage"),
    ],
)
def test_unknown_enum_values_fail_validation(field_name, value, error_fragment):
    payload = to_broad_topic_domain_intake_json_safe_v1(_build())
    payload[field_name] = value
    with pytest.raises(ValueError) as exc:
        validate_broad_topic_domain_intake_v1(payload)
    assert error_fragment in str(exc.value)


@pytest.mark.parametrize(
    "descriptor",
    [
        "public ISS wording",
        "AGI claim",
        "consciousness claim",
        "sentience claim",
        "Turing claim",
        "certification claim",
    ],
)
def test_public_iss_and_claim_markers_fail_validation(descriptor):
    payload = to_broad_topic_domain_intake_json_safe_v1(_build())
    payload["safe_topic_descriptor"] = descriptor
    with pytest.raises(ValueError):
        validate_broad_topic_domain_intake_v1(payload)


def test_module_does_not_reference_protected_runtime_files():
    source = inspect.getsource(__import__("weslr.broad_topic_domain_intake", fromlist=["*"]))
    assert "chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue.py" not in source
    assert "chat_ui.py" not in source
