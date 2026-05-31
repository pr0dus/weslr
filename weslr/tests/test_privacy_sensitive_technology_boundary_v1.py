import sys
from dataclasses import replace

import pytest

from weslr.broad_topic_domain_intake import build_broad_topic_domain_intake_v1
from weslr.research_conversation_planner import build_research_conversation_plan_v1
from weslr.privacy_sensitive_technology_boundary import (
    PrivacySensitiveTechnologyBoundary,
    build_initial_privacy_sensitive_technology_boundary_examples_v1,
    build_privacy_sensitive_technology_boundary_v1,
    evaluate_privacy_sensitive_technology_boundary_v1,
    summarize_privacy_sensitive_technology_boundary_v1,
    to_privacy_sensitive_technology_boundary_json_safe_v1,
    validate_privacy_sensitive_technology_boundary_v1,
)


def _boundary(descriptor: str, *, prompt_labels=(), owner_intent_labels=(), risk_hints=(), known_unknown_hints=(), context_overrides=None):
    intake = build_broad_topic_domain_intake_v1(
        safe_topic_descriptor=descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=owner_intent_labels,
        risk_hints=risk_hints,
        known_unknown_hints=known_unknown_hints,
        existing_behavior_pack_refs=(),
    )
    plan = build_research_conversation_plan_v1(domain_intake=intake)
    return build_privacy_sensitive_technology_boundary_v1(
        domain_intake=intake,
        research_plan=plan,
        **(context_overrides or {}),
    )


def test_module_imports_safely():
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_builds_deterministic_boundary():
    boundary_a = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    boundary_b = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    assert boundary_a == boundary_b
    assert boundary_a.boundary_id == boundary_b.boundary_id


def test_wifi_rf_home_human_tracking_boundary():
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive", "consent required"),
        known_unknown_hints=("unfamiliar",),
    )
    assert boundary.boundary_decision in {"require_consent_and_lawfulness_context", "require_boundary_clarification", "allow_privacy_by_design_prototype_plan"}
    assert boundary.privacy_risk_level == "high"
    assert boundary.legal_risk_level == "high"
    assert boundary.abuse_risk_level == "high"
    assert boundary.person_tracking_sensitive is True
    assert boundary.home_monitoring_sensitive is True
    assert boundary.affected_person_consent_required is True
    assert boundary.covert_use_blocked is True
    assert boundary.deployment_guidance_allowed is False
    assert boundary.validation_required_before_reliance is True


def test_authenticated_responsible_context_is_positive_context():
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location", "consent required"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive", "consent required", "lawful only"),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "affected_person_consent_present": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
        },
    )
    assert boundary.authenticated_user_context is True
    assert boundary.terms_acceptance_context is True
    assert boundary.responsible_use_context is True
    assert boundary.consent_context_present is True
    assert boundary.lawfulness_context_present is True


@pytest.mark.parametrize(
    "descriptor,prompt_labels,overrides,expected_decision,expected_guidance",
    [
        (
            "WiFi/RF sensing for medication reminders and routine support",
            ("wifi sensing", "medication reminder", "routine support", "self care"),
            {"consent_context_present": True, "lawfulness_context_present": True, "affected_person_consent_present": True},
            {"allow_consent_based_assistive_research", "allow_privacy_by_design_prototype_plan"},
            {"privacy_by_design_plan", "assistive_product_design"},
        ),
        (
            "Breathing anomaly awareness with consent for home support",
            ("breathing", "anomaly awareness", "home support"),
            {"consent_context_present": True, "lawfulness_context_present": True, "affected_person_consent_present": True},
            {"allow_consent_based_assistive_research", "allow_privacy_by_design_prototype_plan"},
            {"privacy_by_design_plan", "assistive_product_design"},
        ),
    ],
)
def test_consent_based_self_care_allows_bounded_assistive_research(descriptor, prompt_labels, overrides, expected_decision, expected_guidance):
    boundary = _boundary(
        descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=("research",),
        risk_hints=("health support", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            **overrides,
        },
    )
    assert boundary.boundary_decision in expected_decision
    assert boundary.allowed_guidance_level in expected_guidance
    assert boundary.beneficial_use_detected is True
    assert boundary.assistive_health_support_intent is True
    assert boundary.covert_use_blocked is True
    assert boundary.local_processing_recommended is True
    assert boundary.data_minimization_required is True
    assert boundary.user_control_required is True
    assert boundary.medical_claim_boundary_required is True
    assert boundary.medical_diagnosis_claim_blocked is True
    assert boundary.treatment_recommendation_blocked is True


def test_medication_routine_reminder_blocks_treatment_authority():
    boundary = _boundary(
        "Medication routine reminder with user-configured safety support",
        prompt_labels=("medication reminder", "routine", "support"),
        owner_intent_labels=("learn explain",),
        risk_hints=("health support", "wellness"),
        known_unknown_hints=("known existing pack",),
        context_overrides={
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "affected_person_consent_present": True,
        },
    )
    assert boundary.medical_claim_boundary_required is True
    assert boundary.medical_diagnosis_claim_blocked is True
    assert boundary.treatment_recommendation_blocked is True
    assert boundary.validation_required_before_reliance is True


def test_breathing_anomaly_awareness_blocks_diagnosis_claim():
    boundary = _boundary(
        "Breathing anomaly awareness with consent for home support",
        prompt_labels=("breathing", "anomaly awareness", "home support"),
        owner_intent_labels=("research",),
        risk_hints=("health support",),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "affected_person_consent_present": True,
        },
    )
    assert boundary.medical_claim_boundary_required is True
    assert boundary.medical_diagnosis_claim_blocked is True
    assert boundary.treatment_recommendation_blocked is True


def test_emergency_escalation_requires_explicit_permission():
    boundary = _boundary(
        "Emergency escalation design with explicit permission and override controls",
        prompt_labels=("emergency escalation", "override", "permission"),
        owner_intent_labels=("research",),
        risk_hints=("safety critical",),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "emergency_escalation_requires_explicit_permission": True,
        },
    )
    assert boundary.emergency_escalation_requires_explicit_permission is True
    assert any("permission" in item for item in boundary.required_owner_questions)
    assert any("permission" in item for item in boundary.allowed_next_steps)


def test_consent_based_research_may_allow_high_level_prototype_only():
    boundary = _boundary(
        "WiFi/RF sensing for consent-based research in a home setting",
        prompt_labels=("wifi sensing", "research only", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("consent required", "lawful only"),
        known_unknown_hints=("researchable",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
        },
    )
    assert boundary.boundary_decision in {"allow_high_level_prototype_only", "allow_privacy_by_design_prototype_plan", "allow_consent_based_assistive_research"}
    assert boundary.allowed_guidance_level in {"high_level_prototype_only", "privacy_by_design_plan", "assistive_product_design"}
    assert boundary.deployment_guidance_allowed is False


@pytest.mark.parametrize(
    "descriptor,prompt_labels,risk_hints,expected_risk,expected_decision",
    [
        (
            "Workplace monitoring boundary review for a lawful employee-safety program",
            ("workplace", "employee safety", "monitoring"),
            ("workplace context", "privacy-sensitive"),
            {"high", "blocked"},
            {"require_affected_person_consent_context", "require_consent_and_lawfulness_context", "allow_privacy_by_design_prototype_plan"},
        ),
        (
            "Minor-sensitive sensing boundary review",
            ("minors", "vulnerable people", "home safety"),
            ("high risk", "minor context"),
            {"high", "blocked"},
            {"require_affected_person_consent_context", "require_consent_and_lawfulness_context", "allow_privacy_by_design_prototype_plan", "blocked_sensitive_use"},
        ),
        (
            "Biometric identity inference boundary review",
            ("biometric", "identity", "face", "voice"),
            ("high privacy risk", "legal review required"),
            {"high", "blocked"},
            {"require_consent_and_lawfulness_context", "require_boundary_clarification", "allow_privacy_by_design_prototype_plan", "blocked_sensitive_use"},
        ),
    ],
)
def test_sensitive_contexts_are_high_risk(descriptor, prompt_labels, risk_hints, expected_risk, expected_decision):
    boundary = _boundary(
        descriptor,
        prompt_labels=prompt_labels,
        owner_intent_labels=("safety legal privacy review",),
        risk_hints=risk_hints,
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
        },
    )
    assert boundary.privacy_risk_level in expected_risk
    assert boundary.legal_risk_level in {"high", "blocked"}
    assert boundary.abuse_risk_level in {"high", "blocked"}
    assert boundary.boundary_decision in expected_decision
    assert boundary.deployment_guidance_allowed is False
    assert boundary.covert_use_blocked is True


def test_generic_non_person_sensor_research_may_allow_bounded_research():
    boundary = _boundary(
        "Generic sensor research for a lab prototype",
        prompt_labels=("sensor research", "lab prototype"),
        owner_intent_labels=("research",),
        risk_hints=("low risk",),
        known_unknown_hints=("known existing pack",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
        },
    )
    assert boundary.boundary_decision == "allow_bounded_research"
    assert boundary.person_tracking_sensitive is False
    assert boundary.allowed_guidance_level in {"conceptual_only", "research_questions_only"}


def test_validates_normal_boundary():
    boundary = _boundary(
        "WiFi/RF sensing for consent-based research in a home setting",
        prompt_labels=("wifi sensing", "research only", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("consent required", "lawful only"),
        known_unknown_hints=("researchable",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
        },
    )
    assert validate_privacy_sensitive_technology_boundary_v1(boundary) is True


def test_json_safe_export_works():
    boundary = _boundary(
        "WiFi/RF sensing for consent-based research in a home setting",
        prompt_labels=("wifi sensing", "research only", "privacy"),
        owner_intent_labels=("research",),
        risk_hints=("consent required", "lawful only"),
        known_unknown_hints=("researchable",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
        },
    )
    safe = to_privacy_sensitive_technology_boundary_json_safe_v1(boundary)
    assert isinstance(safe, dict)
    assert safe["boundary_id"] == boundary.boundary_id


def test_summary_includes_decision_risk_guidance_and_beneficial_use_flag():
    boundary = _boundary(
        "WiFi/RF sensing for medication reminders and routine support",
        prompt_labels=("wifi sensing", "medication reminder", "routine support", "self care"),
        owner_intent_labels=("research",),
        risk_hints=("health support", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "affected_person_consent_present": True,
        },
    )
    summary = summarize_privacy_sensitive_technology_boundary_v1(boundary)
    assert summary.boundary_decision == boundary.boundary_decision
    assert summary.privacy_risk_level == boundary.privacy_risk_level
    assert summary.allowed_guidance_level == boundary.allowed_guidance_level
    assert summary.beneficial_use_detected is True


def test_initial_examples_exist():
    examples = build_initial_privacy_sensitive_technology_boundary_examples_v1()
    assert len(examples) >= 10
    for example in examples:
        assert validate_privacy_sensitive_technology_boundary_v1(example) is True


@pytest.mark.parametrize("field", ["public_claim_allowed", "learning_claimed", "runtime_authority", "writes_state", "model_provider_used"])
def test_no_initial_example_has_forbidden_authority(field):
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert getattr(example, field) is False


def test_no_initial_example_allows_public_claim():
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert example.public_claim_allowed is False


def test_no_initial_example_claims_learning():
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert example.learning_claimed is False


def test_no_initial_example_has_runtime_authority():
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert example.runtime_authority is False


def test_no_initial_example_writes_state():
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert example.writes_state is False


def test_no_initial_example_uses_model_provider():
    for example in build_initial_privacy_sensitive_technology_boundary_examples_v1():
        assert example.model_provider_used is False


@pytest.mark.parametrize(
    "patch,expected_error",
    [
        ({"public_claim_allowed": True}, "public_claim_allowed_must_be_false"),
        ({"runtime_authority": True}, "runtime_authority_must_be_false"),
        ({"writes_state": True}, "writes_state_must_be_false"),
        ({"model_provider_used": True}, "model_provider_used_must_be_false"),
        ({"learning_claimed": True}, "learning_claimed_must_be_false"),
        ({"boundary_decision": "unknown"}, "unknown_boundary_decision"),
        ({"allowed_guidance_level": "unknown"}, "unknown_allowed_guidance_level"),
        ({"privacy_risk_level": "unknown"}, "unknown_privacy_risk_level"),
        ({"recommended_response_mode": "unknown"}, "unknown_recommended_response_mode"),
    ],
)
def test_unknown_values_fail_validation(patch, expected_error):
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    mutated = replace(boundary, **patch)
    with pytest.raises(ValueError, match=expected_error):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


@pytest.mark.parametrize("extra_field", ["raw_prompt", "raw_answer", "transcript"])
def test_raw_fields_fail_validation(extra_field):
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    payload = to_privacy_sensitive_technology_boundary_json_safe_v1(boundary)
    payload[extra_field] = "secret"
    with pytest.raises(ValueError, match="forbidden_raw_fields_present"):
        validate_privacy_sensitive_technology_boundary_v1(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"technology_area": "AGI claim"},
        {"technology_area": "consciousness claim"},
        {"technology_area": "sentience claim"},
        {"technology_area": "Turing claim"},
        {"technology_area": "certification claim"},
        {"technology_area": "public ISS wording"},
    ],
)
def test_public_iss_and_claim_markers_fail_validation(payload):
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    mutated = replace(boundary, **payload)
    with pytest.raises(ValueError, match="forbidden_public_or_claim_language_present"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


@pytest.mark.parametrize(
    "payload",
    [
        {"technology_area": "covert tracking"},
        {"technology_area": "unsafe deployment"},
        {"required_owner_questions": ("covert tracking",)},
        {"forbidden_guidance": ("covert deployment",)},
    ],
)
def test_unsafe_markers_fail_validation(payload):
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    mutated = replace(boundary, **payload)
    with pytest.raises(ValueError, match="unsafe_marker_present"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_deployment_guidance_allowed_true_for_high_risk_person_tracking_fails_validation():
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    mutated = replace(boundary, deployment_guidance_allowed=True)
    with pytest.raises(ValueError, match="deployment_guidance_allowed_for_high_risk_person_tracking"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_covert_use_blocked_false_for_sensitive_use_fails_validation():
    boundary = _boundary(
        "WiFi/RF sensing for human presence and location in a house",
        prompt_labels=("wifi sensing", "human presence", "location"),
        owner_intent_labels=("research",),
        risk_hints=("high risk", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
    )
    mutated = replace(boundary, covert_use_blocked=False)
    with pytest.raises(ValueError, match="covert_use_blocked_required_for_sensitive_use"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_medical_diagnosis_allowed_in_health_support_context_fails_validation():
    boundary = _boundary(
        "WiFi/RF sensing for medication reminders and routine support",
        prompt_labels=("wifi sensing", "medication reminder", "routine support", "self care"),
        owner_intent_labels=("research",),
        risk_hints=("health support", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "affected_person_consent_present": True,
        },
    )
    mutated = replace(boundary, medical_diagnosis_claim_blocked=False)
    with pytest.raises(ValueError, match="medical_claim_boundaries_required"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_treatment_recommendation_allowed_in_health_support_context_fails_validation():
    boundary = _boundary(
        "WiFi/RF sensing for medication reminders and routine support",
        prompt_labels=("wifi sensing", "medication reminder", "routine support", "self care"),
        owner_intent_labels=("research",),
        risk_hints=("health support", "privacy-sensitive"),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "authenticated_user_context": True,
            "terms_acceptance_context": True,
            "responsible_use_context": True,
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "affected_person_consent_present": True,
        },
    )
    mutated = replace(boundary, treatment_recommendation_blocked=False)
    with pytest.raises(ValueError, match="medical_claim_boundaries_required"):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_emergency_escalation_without_explicit_permission_requirement_fails_validation():
    boundary = _boundary(
        "Emergency escalation design with explicit permission and override controls",
        prompt_labels=("emergency escalation", "override", "permission"),
        owner_intent_labels=("research",),
        risk_hints=("safety critical",),
        known_unknown_hints=("unfamiliar",),
        context_overrides={
            "consent_context_present": True,
            "lawfulness_context_present": True,
            "emergency_escalation_requires_explicit_permission": True,
        },
    )
    mutated = replace(boundary, emergency_escalation_requires_explicit_permission=False)
    # The presence of an emergency context must preserve the explicit-permission gate.
    with pytest.raises(ValueError):
        validate_privacy_sensitive_technology_boundary_v1(mutated)


def test_module_does_not_import_or_call_protected_modules():
    source = open("weslr/privacy_sensitive_technology_boundary.py", "r", encoding="utf-8").read()
    assert "chat_responder" not in source
    assert "weslr.main" not in source
    assert "dialogue" not in source
    assert "chat_ui" not in source
