"""Tests for Domain Ontology / Domain Overlay Layer (v21)

Tests domain_ontology.py data models, registry, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.domain_ontology import (
    DomainType,
    DomainRiskSensitivity,
    DomainRecommendationStyle,
    DomainProfile,
    DomainContext,
    DomainOverlay,
    get_domain_profile_registry,
    create_domain_profile,
    create_domain_context,
    create_domain_overlay,
    integrate_with_evidence_claim,
    integrate_with_change_proposal,
    integrate_with_governance_view,
)


class TestDomainOntology(unittest.TestCase):
    """Test domain ontology data models and factory functions."""

    def test_domain_type_enum(self):
        """Test DomainType enum values."""
        self.assertEqual(DomainType.HOME_FAMILY.value, "home_family")
        self.assertEqual(DomainType.EDUCATION.value, "education")
        self.assertEqual(DomainType.HOSPITALS_MEDICINE.value, "hospitals_medicine")
        self.assertEqual(DomainType.SCIENCE_RESEARCH.value, "science_research")
        self.assertEqual(DomainType.INDUSTRY.value, "industry")
        self.assertEqual(DomainType.AEROSPACE_LONG_MISSION.value, "aerospace_long_mission")
        self.assertEqual(DomainType.OTHER.value, "other")

    def test_domain_risk_sensitivity_enum(self):
        """Test DomainRiskSensitivity enum values."""
        self.assertEqual(DomainRiskSensitivity.LOW.value, "low")
        self.assertEqual(DomainRiskSensitivity.MEDIUM.value, "medium")
        self.assertEqual(DomainRiskSensitivity.HIGH.value, "high")

    def test_domain_recommendation_style_enum(self):
        """Test DomainRecommendationStyle enum values."""
        self.assertEqual(DomainRecommendationStyle.advisory.value, "advisory")
        self.assertEqual(DomainRecommendationStyle.PREScriptive.value, "prescriptive")
        self.assertEqual(DomainRecommendationStyle.exploratory.value, "exploratory")
        self.assertEqual(DomainRecommendationStyle.diagnostic.value, "diagnostic")

    def test_create_domain_profile_defaults(self):
        """Test creating a domain profile with defaults."""
        profile = create_domain_profile(
            domain_type=DomainType.HOME_FAMILY.value,
            name="Home & Family",
            description="Residential environments.",
        )
        
        self.assertIsNotNone(profile.domain_type)
        self.assertEqual(profile.name, "Home & Family")
        self.assertEqual(profile.description, "Residential environments.")
        self.assertEqual(profile.minimum_evidence_confidence, 0.7)
        self.assertEqual(profile.risk_sensitivity, DomainRiskSensitivity.MEDIUM.value)
        self.assertEqual(profile.trust_weighting, 1.0)
        self.assertEqual(profile.recommendation_style, DomainRecommendationStyle.advisory.value)
        self.assertEqual(profile.max_execution_latency_ms, 10000)
        self.assertEqual(profile.requires_online, False)
        self.assertEqual(profile.offline_fallback_allowed, True)
        self.assertIsNotNone(profile.created_at)

    def test_create_domain_profile_custom(self):
        """Test creating a domain profile with custom values."""
        profile = create_domain_profile(
            domain_type=DomainType.HOSPITALS_MEDICINE.value,
            name="Hospitals",
            description="Clinical care.",
            minimum_evidence_confidence=0.9,
            risk_sensitivity=DomainRiskSensitivity.LOW.value,
            requires_online=True,
            offline_fallback_allowed=False,
        )
        
        self.assertEqual(profile.minimum_evidence_confidence, 0.9)
        self.assertEqual(profile.risk_sensitivity, DomainRiskSensitivity.LOW.value)
        self.assertEqual(profile.requires_online, True)
        self.assertEqual(profile.offline_fallback_allowed, False)

    def test_domain_profile_to_dict_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        profile = create_domain_profile(
            domain_type=DomainType.EDUCATION.value,
            name="Education",
            description="Academic environments.",
        )
        profile_dict = profile.to_dict()
        profile2 = DomainProfile.from_dict(profile_dict)
        
        self.assertEqual(profile.domain_type, profile2.domain_type)
        self.assertEqual(profile.name, profile2.name)

    def test_domain_profile_update(self):
        """Test updating a domain profile."""
        profile = create_domain_profile(
            domain_type=DomainType.INDUSTRY.value,
            name="Industry",
            description="Manufacturing.",
        )
        
        profile.update(minimum_evidence_confidence=0.8, max_execution_latency_ms=500)
        
        self.assertEqual(profile.minimum_evidence_confidence, 0.8)
        self.assertEqual(profile.max_execution_latency_ms, 500)

    def test_create_domain_context(self):
        """Test creating a domain context."""
        context = create_domain_context(
            domain_type=DomainType.HOME_FAMILY.value,
            domain_profile_id="profile-001",
            application_scope=["safety", "education"],
            author="operator-001",
        )
        
        self.assertIsNotNone(context.context_id)
        self.assertEqual(context.domain_type, DomainType.HOME_FAMILY.value)
        self.assertEqual(context.domain_profile_id, "profile-001")
        self.assertEqual(context.application_scope, ["safety", "education"])
        self.assertEqual(context.author, "operator-001")
        self.assertIsNone(context.evidence_confidence_override)
        self.assertIsNone(context.risk_override)

    def test_domain_context_to_dict(self):
        """Test domain context serialization."""
        context = create_domain_context(
            domain_type=DomainType.AEROSPACE_LONG_MISSION.value,
            evidence_confidence_override=0.95,
        )
        
        context_dict = context.to_dict()
        self.assertEqual(context_dict["domain_type"], DomainType.AEROSPACE_LONG_MISSION.value)
        self.assertEqual(context_dict["evidence_confidence_override"], 0.95)
        self.assertIsNone(context_dict["risk_override"])

    def test_create_domain_overlay(self):
        """Test creating a domain overlay."""
        overlay = create_domain_overlay(
            domain_type=DomainType.SCIENCE_RESEARCH.value,
            target_component="proposal_review",
            rules={"min_evidence": 2, "reviewer_count": 3},
            enabled=True,
            priority=50,
        )
        
        self.assertIsNotNone(overlay.overlay_id)
        self.assertEqual(overlay.domain_type, DomainType.SCIENCE_RESEARCH.value)
        self.assertEqual(overlay.target_component, "proposal_review")
        self.assertEqual(overlay.rules, {"min_evidence": 2, "reviewer_count": 3})
        self.assertTrue(overlay.enabled)
        self.assertEqual(overlay.priority, 50)

    def test_domain_overlay_to_dict(self):
        """Test domain overlay serialization."""
        overlay = create_domain_overlay(
            domain_type=DomainType.HOSPITALS_MEDICINE.value,
            target_component="evidence_assessment",
        )
        
        overlay_dict = overlay.to_dict()
        self.assertEqual(overlay_dict["domain_type"], DomainType.HOSPITALS_MEDICINE.value)
        self.assertEqual(overlay_dict["target_component"], "evidence_assessment")
        self.assertEqual(overlay_dict["rules"], {})

    def test_get_domain_profile_registry(self):
        """Test domain profile registry includes all standard domains."""
        registry = get_domain_profile_registry()
        
        self.assertIn(DomainType.HOME_FAMILY.value, registry)
        self.assertIn(DomainType.EDUCATION.value, registry)
        self.assertIn(DomainType.HOSPITALS_MEDICINE.value, registry)
        self.assertIn(DomainType.SCIENCE_RESEARCH.value, registry)
        self.assertIn(DomainType.INDUSTRY.value, registry)
        self.assertIn(DomainType.AEROSPACE_LONG_MISSION.value, registry)
        # Registry has 6 profiles (OTHER is not included as a predefined domain)
        self.assertEqual(len(registry), 6)

    def test_domain_profile_registry_values(self):
        """Test domain profile registry has correct values."""
        registry = get_domain_profile_registry()
        
        home_profile = registry[DomainType.HOME_FAMILY.value]
        self.assertEqual(home_profile.minimum_evidence_confidence, 0.6)
        self.assertEqual(home_profile.risk_sensitivity, DomainRiskSensitivity.LOW.value)
        self.assertFalse(home_profile.requires_online)
        self.assertTrue(home_profile.offline_fallback_allowed)
        
        hospital_profile = registry[DomainType.HOSPITALS_MEDICINE.value]
        self.assertEqual(hospital_profile.minimum_evidence_confidence, 0.9)
        self.assertEqual(hospital_profile.requires_online, True)
        self.assertFalse(hospital_profile.offline_fallback_allowed)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for evidence, proposals, and governance views."""

    def test_integrate_with_evidence_claim_adds_domain_fields(self):
        """Test that integration adds domain context to evidence claim."""
        claim_dict = {
            "claim_id": "claim-001",
            "text": "Test evidence",
        }
        
        result = integrate_with_evidence_claim(claim_dict)
        
        self.assertIn("domain_tags", result)
        self.assertIn("domain_profile_id", result)
        self.assertEqual(result["domain_tags"], [])
        self.assertIsNone(result["domain_profile_id"])

    def test_integrate_with_evidence_claim_preserves_existing(self):
        """Test that integration preserves existing domain fields."""
        claim_dict = {
            "claim_id": "claim-001",
            "text": "Test evidence",
            "domain_tags": ["hospital"],
            "domain_profile_id": "profile-001",
        }
        
        result = integrate_with_evidence_claim(claim_dict)
        
        self.assertEqual(result["domain_tags"], ["hospital"])
        self.assertEqual(result["domain_profile_id"], "profile-001")

    def test_integrate_with_change_proposal_adds_domain_fields(self):
        """Test that integration adds domain context to change proposal."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertIn("domain_context", result)
        self.assertIn("domain_tag", result)
        self.assertIsNone(result["domain_context"])
        self.assertIsNone(result["domain_tag"])

    def test_integrate_with_change_proposal_preserves_existing(self):
        """Test that integration preserves existing domain fields."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "domain_tag": "hospital",
            "domain_context": {"domain_type": "hospitals_medicine"},
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertEqual(result["domain_tag"], "hospital")
        self.assertEqual(result["domain_context"]["domain_type"], "hospitals_medicine")

    def test_integrate_with_governance_view_adds_domain_fields(self):
        """Test that integration adds domain context to governance view."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("domain_tag", result)
        self.assertIn("domain_profile_id", result)
        self.assertIn("domain_risk_override", result)
        self.assertIsNone(result["domain_tag"])
        self.assertIsNone(result["domain_profile_id"])
        self.assertIsNone(result["domain_risk_override"])


if __name__ == "__main__":
    unittest.main()
