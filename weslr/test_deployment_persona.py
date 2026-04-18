# test_deployment_persona.py - WESLR v39: Role / Deployment Persona Layer Tests
# Focused tests for deployment persona layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.deployment_persona import (
    DeploymentRole,
    CommunicationPosture,
    EvidenceStrictness,
    CautionLevel,
    InitiativeLevel,
    ExplanationDensity,
    EscalationStyle,
    DegradedModeBehavior,
    DeploymentRoleProfile,
    DeploymentContext,
    RoleBehaviorAdaptation,
    get_deployment_role_registry,
    DeploymentPersonaEngine,
    integrate_with_adaptive_guidance,
    integrate_with_narrative,
    integrate_with_domain_ontology,
    integrate_with_trust_dynamics,
    integrate_with_intervention_timing,
)


class TestDeploymentRoleEnum(TestCase):
    """Test deployment role enum values."""
    
    def test_all_roles_present(self):
        """All expected roles are defined."""
        expected_roles = [
            "home_family",
            "education",
            "hospitals_medicine",
            "science_research",
            "industry",
            "aerospace_long_mission",
        ]
        
        for role in expected_roles:
            self.assertIn(role, [r.value for r in DeploymentRole])
    
    def test_roles_are_strings(self):
        """All role values are strings."""
        for role in DeploymentRole:
            self.assertIsInstance(role.value, str)
    
    def test_unique_role_values(self):
        """All role values are unique."""
        role_values = [r.value for r in DeploymentRole]
        self.assertEqual(len(role_values), len(set(role_values)))


class TestCommunicationPostureEnum(TestCase):
    """Test communication posture enum values."""
    
    def test_all_postures_present(self):
        """All expected postures are defined."""
        expected_postures = [
            "prescriptive",
            "advisory",
            "exploratory",
            "diagnostic",
            "supportive",
        ]
        
        for posture in expected_postures:
            self.assertIn(posture, [p.value for p in CommunicationPosture])


class TestEvidenceStrictnessEnum(TestCase):
    """Test evidence strictness enum values."""
    
    def test_all_strictness_levels_present(self):
        """All expected strictness levels are defined."""
        expected_levels = [
            "minimal",
            "moderate",
            "high",
            "maximum",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [s.value for s in EvidenceStrictness])
    
    def test_strictness_ordering(self):
        """Evidence strictness has logical ordering."""
        strictness_order = [
            EvidenceStrictness.MINIMAL.value,
            EvidenceStrictness.MODERATE.value,
            EvidenceStrictness.HIGH.value,
            EvidenceStrictness.MAXIMUM.value,
        ]
        
        # Verify all expected values are present
        for level in strictness_order:
            self.assertIn(level, [s.value for s in EvidenceStrictness])


class TestCautionLevelEnum(TestCase):
    """Test caution level enum values."""
    
    def test_all_caution_levels_present(self):
        """All expected caution levels are defined."""
        expected_levels = [
            "minimal",
            "normal",
            "elevated",
            "maximum",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [c.value for c in CautionLevel])


class TestInitiativeLevelEnum(TestCase):
    """Test initiative level enum values."""
    
    def test_all_initiative_levels_present(self):
        """All expected initiative levels are defined."""
        expected_levels = [
            "none",
            "low",
            "moderate",
            "high",
            "maximum",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [i.value for i in InitiativeLevel])


class TestExplanationDensityEnum(TestCase):
    """Test explanation density enum values."""
    
    def test_all_density_levels_present(self):
        """All expected density levels are defined."""
        expected_levels = [
            "minimal",
            "standard",
            "enhanced",
            "maximum",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [d.value for d in ExplanationDensity])


class TestEscalationStyleEnum(TestCase):
    """Test escalation style enum values."""
    
    def test_all_escalation_styles_present(self):
        """All expected escalation styles are defined."""
        expected_styles = [
            "direct",
            "gradual",
            "hesitant",
        ]
        
        for style in expected_styles:
            self.assertIn(style, [e.value for e in EscalationStyle])


class TestDegradedModeBehaviorEnum(TestCase):
    """Test degraded mode behavior enum values."""
    
    def test_all_degraded_modes_present(self):
        """All expected degraded modes are defined."""
        expected_modes = [
            "consultative",
            "fallback",
            "silent",
        ]
        
        for mode in expected_modes:
            self.assertIn(mode, [d.value for d in DegradedModeBehavior])


class TestDeploymentRoleProfile(TestCase):
    """Test DeploymentRoleProfile data class."""
    
    def test_profile_creation(self):
        """Profile creation works correctly."""
        profile = DeploymentRoleProfile(
            role="test_role",
            name="Test Role",
            description="Test description",
            communication_posture=CommunicationPosture.ADVISORY.value,
            evidence_strictness=EvidenceStrictness.MODERATE.value,
            minimum_evidence_confidence=0.7,
            caution_level=CautionLevel.NORMAL.value,
            initiative_level=InitiativeLevel.MODERATE.value,
            explanation_density=ExplanationDensity.STANDARD.value,
            escalation_style=EscalationStyle.GRADUAL.value,
            degraded_mode_behavior=DegradedModeBehavior.CONSULTATIVE.value,
        )
        
        self.assertEqual(profile.role, "test_role")
        self.assertEqual(profile.name, "Test Role")
        self.assertEqual(profile.description, "Test description")
        self.assertEqual(profile.communication_posture, CommunicationPosture.ADVISORY.value)
        self.assertEqual(profile.evidence_strictness, EvidenceStrictness.MODERATE.value)
        self.assertEqual(profile.minimum_evidence_confidence, 0.7)
        self.assertEqual(profile.caution_level, CautionLevel.NORMAL.value)
        self.assertEqual(profile.initiative_level, InitiativeLevel.MODERATE.value)
        self.assertEqual(profile.explanation_density, ExplanationDensity.STANDARD.value)
        self.assertEqual(profile.escalation_style, EscalationStyle.GRADUAL.value)
        self.assertEqual(profile.degraded_mode_behavior, DegradedModeBehavior.CONSULTATIVE.value)
    
    def test_profile_to_dict(self):
        """Profile to_dict conversion works."""
        profile = DeploymentRoleProfile(
            role="test_role",
            name="Test Role",
            description="Test description",
        )
        
        result = profile.to_dict()
        
        self.assertEqual(result["role"], "test_role")
        self.assertEqual(result["name"], "Test Role")
        self.assertEqual(result["description"], "Test description")
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
    
    def test_profile_from_dict(self):
        """Profile from_dict reconstruction works."""
        profile = DeploymentRoleProfile(
            role="test_role",
            name="Test Role",
            description="Test description",
            minimum_evidence_confidence=0.7,
        )
        
        data = profile.to_dict()
        recreated = DeploymentRoleProfile.from_dict(data)
        
        self.assertEqual(recreated.role, profile.role)
        self.assertEqual(recreated.name, profile.name)
        self.assertEqual(recreated.description, profile.description)
        self.assertEqual(recreated.minimum_evidence_confidence, profile.minimum_evidence_confidence)
    
    def test_profile_update(self):
        """Profile update refreshes timestamp."""
        profile = DeploymentRoleProfile(
            role="test_role",
            name="Test Role",
            description="Test description",
            minimum_evidence_confidence=0.6,
        )
        
        original_timestamp = profile.updated_at
        updated_profile = profile.update(minimum_evidence_confidence=0.8)
        
        self.assertEqual(updated_profile.minimum_evidence_confidence, 0.8)
        self.assertEqual(updated_profile.role, profile.role)
        self.assertNotEqual(updated_profile.updated_at, original_timestamp)


class TestDeploymentContext(TestCase):
    """Test DeploymentContext data class."""
    
    def test_context_creation(self):
        """Context creation works correctly."""
        context = DeploymentContext(
            context_id="test-context-123",
            role=DeploymentRole.EDUCATION.value,
            evidence_confidence_override=0.75,
            caution_override=CautionLevel.ELEVATED.value,
        )
        
        self.assertEqual(context.context_id, "test-context-123")
        self.assertEqual(context.role, DeploymentRole.EDUCATION.value)
        self.assertEqual(context.evidence_confidence_override, 0.75)
        self.assertEqual(context.caution_override, CautionLevel.ELEVATED.value)
        self.assertEqual(context.application_scope, [])
    
    def test_context_with_application_scope(self):
        """Context creation with application scope works."""
        context = DeploymentContext(
            context_id="test-context-456",
            role=DeploymentRole.INDUSTRY.value,
            application_scope=["process_control", "maintenance"],
        )
        
        self.assertEqual(len(context.application_scope), 2)
        self.assertIn("process_control", context.application_scope)
        self.assertIn("maintenance", context.application_scope)
    
    def test_context_to_dict(self):
        """Context to_dict conversion works."""
        context = DeploymentContext(
            context_id="test-context-789",
            role=DeploymentRole.HOME_FAMILY.value,
            evidence_confidence_override=0.6,
        )
        
        result = context.to_dict()
        
        self.assertEqual(result["context_id"], "test-context-789")
        self.assertEqual(result["role"], DeploymentRole.HOME_FAMILY.value)
        self.assertEqual(result["evidence_confidence_override"], 0.6)
        self.assertIn("created_at", result)
    
    def test_context_from_dict(self):
        """Context from_dict reconstruction works."""
        context = DeploymentContext(
            context_id="test-context-abc",
            role=DeploymentRole.SCIENCE_RESEARCH.value,
            application_scope=["data_analysis"],
        )
        
        data = context.to_dict()
        recreated = DeploymentContext.from_dict(data)
        
        self.assertEqual(recreated.context_id, context.context_id)
        self.assertEqual(recreated.role, context.role)
        self.assertEqual(recreated.application_scope, context.application_scope)


class TestRoleBehaviorAdaptation(TestCase):
    """Test RoleBehaviorAdaptation data class."""
    
    def test_adaptation_creation(self):
        """Adaptation creation works correctly."""
        adaptation = RoleBehaviorAdaptation(
            role=DeploymentRole.HOSPITALS_MEDICINE.value,
            effective_communication_posture=CommunicationPosture.DIAGNOSTIC.value,
            effective_evidence_strictness=EvidenceStrictness.MAXIMUM.value,
            effective_caution_level=CautionLevel.MAXIMUM.value,
            effective_initiative_level=InitiativeLevel.NONE.value,
            effective_explanation_density=ExplanationDensity.MAXIMUM.value,
            effective_escalation_style=EscalationStyle.DIRECT.value,
            effective_degraded_mode_behavior=DegradedModeBehavior.SILENT.value,
            minimum_evidence_confidence=0.9,
            max_single_step_confidence=0.85,
            max_suggestions_per_session=3,
            can_be_proactive=False,
            requires_explanation=True,
            min_explanation_length=100,
            escalation_delay_ms=3000,
        )
        
        self.assertEqual(adaptation.role, DeploymentRole.HOSPITALS_MEDICINE.value)
        self.assertEqual(adaptation.effective_caution_level, CautionLevel.MAXIMUM.value)
        self.assertEqual(adaptation.minimum_evidence_confidence, 0.9)
        self.assertFalse(adaptation.can_be_proactive)
        self.assertTrue(adaptation.requires_explanation)
    
    def test_adaptation_to_dict(self):
        """Adaptation to_dict conversion works."""
        adaptation = RoleBehaviorAdaptation(
            role=DeploymentRole.INDUSTRY.value,
            effective_communication_posture=CommunicationPosture.PRESCRIPTIVE.value,
            effective_evidence_strictness=EvidenceStrictness.HIGH.value,
            effective_caution_level=CautionLevel.NORMAL.value,
            effective_initiative_level=InitiativeLevel.MODERATE.value,
            effective_explanation_density=ExplanationDensity.STANDARD.value,
            effective_escalation_style=EscalationStyle.GRADUAL.value,
            effective_degraded_mode_behavior=DegradedModeBehavior.FALLBACK.value,
            minimum_evidence_confidence=0.7,
            max_single_step_confidence=0.85,
            max_suggestions_per_session=5,
            can_be_proactive=True,
            requires_explanation=False,
            min_explanation_length=50,
            escalation_delay_ms=1000,
        )
        
        result = adaptation.to_dict()
        
        self.assertEqual(result["role"], DeploymentRole.INDUSTRY.value)
        self.assertEqual(result["minimum_evidence_confidence"], 0.7)
        self.assertTrue(result["can_be_proactive"])
        self.assertEqual(result["max_suggestions_per_session"], 5)
        self.assertIn("computed_at", result)
        self.assertEqual(result["computed_by"], "deployment_persona_layer_v39")


class TestDeploymentRoleRegistry(TestCase):
    """Test get_deployment_role_registry function."""
    
    def test_registry_contains_all_roles(self):
        """Registry contains all predefined roles."""
        registry = get_deployment_role_registry()
        
        expected_roles = [
            DeploymentRole.HOME_FAMILY.value,
            DeploymentRole.EDUCATION.value,
            DeploymentRole.HOSPITALS_MEDICINE.value,
            DeploymentRole.SCIENCE_RESEARCH.value,
            DeploymentRole.INDUSTRY.value,
            DeploymentRole.AEROSPACE_LONG_MISSION.value,
        ]
        
        for role in expected_roles:
            self.assertIn(role, registry)
    
    def test_registry_profiles_have_expected_properties(self):
        """Registry profiles have expected properties."""
        registry = get_deployment_role_registry()
        
        # Test hospital/medicine profile
        hospital_profile = registry[DeploymentRole.HOSPITALS_MEDICINE.value]
        self.assertEqual(hospital_profile.minimum_evidence_confidence, 0.9)
        self.assertEqual(hospital_profile.caution_level, CautionLevel.MAXIMUM.value)
        self.assertEqual(hospital_profile.initiative_level, InitiativeLevel.NONE.value)
        self.assertTrue(hospital_profile.requires_online)
        self.assertFalse(hospital_profile.offline_fallback_allowed)
        
        # Test aerospace profile
        aerospace_profile = registry[DeploymentRole.AEROSPACE_LONG_MISSION.value]
        self.assertEqual(aerospace_profile.minimum_evidence_confidence, 0.85)
        self.assertEqual(aerospace_profile.caution_level, CautionLevel.MAXIMUM.value)
        self.assertFalse(aerospace_profile.offline_fallback_allowed)
        
        # Test home family profile
        home_profile = registry[DeploymentRole.HOME_FAMILY.value]
        self.assertEqual(home_profile.minimum_evidence_confidence, 0.6)
        self.assertEqual(home_profile.caution_level, CautionLevel.ELEVATED.value)
        self.assertFalse(home_profile.requires_online)
    
    def test_registry_profiles_have_expected_postures(self):
        """Registry profiles have expected communication postures."""
        registry = get_deployment_role_registry()
        
        # Hospitals should use diagnostic
        hospital_profile = registry[DeploymentRole.HOSPITALS_MEDICINE.value]
        self.assertEqual(hospital_profile.communication_posture, CommunicationPosture.DIAGNOSTIC.value)
        
        # Education should use exploratory
        education_profile = registry[DeploymentRole.EDUCATION.value]
        self.assertEqual(education_profile.communication_posture, CommunicationPosture.EXPLORATORY.value)
        
        # Home should use supportive
        home_profile = registry[DeploymentRole.HOME_FAMILY.value]
        self.assertEqual(home_profile.communication_posture, CommunicationPosture.SUPPORTIVE.value)


class TestDeploymentPersonaEngine(TestCase):
    """Test DeploymentPersonaEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization loads profiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            self.assertGreater(len(engine.role_profiles), 0)
            self.assertEqual(len(engine.active_contexts), 0)
    
    def test_create_role_profile(self):
        """Engine create_role_profile works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            profile = engine.create_role_profile(
                role="custom_role",
                name="Custom Role",
                description="Custom description",
                communication_posture=CommunicationPosture.ADVISORY.value,
                minimum_evidence_confidence=0.65,
            )
            
            self.assertEqual(engine.role_profiles["custom_role"], profile)
            self.assertEqual(profile.role, "custom_role")
    
    def test_get_role_profile(self):
        """Engine get_role_profile works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            profile = engine.get_role_profile(DeploymentRole.EDUCATION.value)
            self.assertIsNotNone(profile)
            self.assertEqual(profile.role, DeploymentRole.EDUCATION.value)
    
    def test_set_active_context(self):
        """Engine set_active_context works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            context = engine.set_active_context(
                context_id="test-context",
                role=DeploymentRole.HOSPITALS_MEDICINE.value,
                evidence_confidence_override=0.95,
            )
            
            loaded = engine.get_active_context("test-context")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.role, DeploymentRole.HOSPITALS_MEDICINE.value)
            self.assertEqual(loaded.evidence_confidence_override, 0.95)
    
    def test_get_default_context(self):
        """Engine get_default_context creates default if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            # Clear contexts first
            engine.active_contexts = {}
            
            context = engine.get_default_context()
            
            self.assertIsNotNone(context)
            self.assertEqual(context.role, DeploymentRole.HOME_FAMILY.value)
    
    def test_compute_behavior_adaptation(self):
        """Engine compute_behavior_adaptation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            # Set up context
            engine.set_active_context(
                context_id="adaptation-test",
                role=DeploymentRole.HOSPITALS_MEDICINE.value,
            )
            
            adaptation = engine.compute_behavior_adaptation("adaptation-test")
            
            self.assertEqual(adaptation.role, DeploymentRole.HOSPITALS_MEDICINE.value)
            self.assertEqual(adaptation.effective_evidence_strictness, EvidenceStrictness.MAXIMUM.value)
            self.assertEqual(adaptation.effective_caution_level, CautionLevel.MAXIMUM.value)
            self.assertEqual(adaptation.minimum_evidence_confidence, 0.9)
            self.assertFalse(adaptation.can_be_proactive)
            self.assertEqual(adaptation.effective_initiative_level, InitiativeLevel.NONE.value)
    
    def test_compute_behavior_adaptation_with_overrides(self):
        """Engine compute_behavior_adaptation respects overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            # Set up context with overrides
            engine.set_active_context(
                context_id="override-test",
                role=DeploymentRole.HOME_FAMILY.value,
                evidence_confidence_override=0.8,
                caution_override=CautionLevel.ELEVATED.value,
                initiative_override=InitiativeLevel.HIGH.value,
            )
            
            adaptation = engine.compute_behavior_adaptation("override-test")
            
            self.assertEqual(adaptation.role, DeploymentRole.HOME_FAMILY.value)
            self.assertEqual(adaptation.minimum_evidence_confidence, 0.8)
            self.assertEqual(adaptation.effective_caution_level, CautionLevel.ELEVATED.value)
            self.assertEqual(adaptation.effective_initiative_level, InitiativeLevel.HIGH.value)
            self.assertTrue(adaptation.can_be_proactive)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            engine.set_active_context(
                context_id="dict-test",
                role=DeploymentRole.INDUSTRY.value,
            )
            
            result = engine.to_dict()
            
            self.assertGreater(result["role_profile_count"], 0)
            self.assertEqual(result["active_context_count"], 1)
            self.assertIn("role_profiles", result)
            self.assertIn("active_contexts", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_adaptive_guidance(self):
        """integrate_with_adaptive_guidance adds role context."""
        guidance_dict = {
            "recommendation_strength": "strong",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("deployment_role_context", result)
        self.assertIsNone(result["deployment_role_context"])
    
    def test_integrate_with_adaptive_guidance_with_role_engine(self):
        """integrate_with_adaptive_guidance works with role engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            engine.set_active_context(
                context_id="integration-test",
                role=DeploymentRole.SCIENCE_RESEARCH.value,
            )
            
            guidance_dict = {
                "recommendation_strength": "moderate",
            }
            
            result = integrate_with_adaptive_guidance(
                guidance_dict,
                role_engine=engine,
                context_id="integration-test",
            )
            
            self.assertIn("deployment_role_context", result)
            self.assertIsNotNone(result["deployment_role_context"])
            self.assertEqual(result["deployment_role_context"]["role"], DeploymentRole.SCIENCE_RESEARCH.value)
            self.assertEqual(result["deployment_role_context"]["effective_evidence_strictness"], EvidenceStrictness.HIGH.value)
    
    def test_integrate_with_narrative(self):
        """integrate_with_narrative adds role context."""
        narrative_dict = {
            "title": "Test Narrative",
            "domain": "test",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("deployment_role_context", result)
        self.assertIsNone(result["deployment_role_context"])
    
    def test_integrate_with_narrative_with_role_engine(self):
        """integrate_with_narrative works with role engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            engine.set_active_context(
                context_id="narrative-test",
                role=DeploymentRole.EDUCATION.value,
            )
            
            narrative_dict = {
                "title": "Test Narrative",
                "domain": "test",
            }
            
            result = integrate_with_narrative(
                narrative_dict,
                role_engine=engine,
                context_id="narrative-test",
            )
            
            self.assertIn("deployment_role_context", result)
            self.assertIsNotNone(result["deployment_role_context"])
            self.assertEqual(result["deployment_role_context"]["role"], DeploymentRole.EDUCATION.value)
    
    def test_integrate_with_domain_ontology(self):
        """integrate_with_domain_ontology adds role context."""
        domain_dict = {
            "domain_type": "home_family",
        }
        
        result = integrate_with_domain_ontology(domain_dict)
        
        self.assertIn("deployment_role_context", result)
        self.assertIsNone(result["deployment_role_context"])
    
    def test_integrate_with_trust_dynamics(self):
        """integrate_with_trust_dynamics adds role context."""
        trust_dict = {
            "relationship_id": "test-relationship",
        }
        
        result = integrate_with_trust_dynamics(trust_dict)
        
        self.assertIn("deployment_role_context", result)
        self.assertIsNone(result["deployment_role_context"])
    
    def test_integrate_with_intervention_timing(self):
        """integrate_with_intervention_timing adds role context."""
        timing_dict = {
            "intervention_id": "test-intervention",
        }
        
        result = integrate_with_intervention_timing(timing_dict)
        
        self.assertIn("deployment_role_context", result)
        self.assertIsNone(result["deployment_role_context"])


class TestRoleBasedOutputAdaptation(TestCase):
    """Test role-based output adaptation scenarios."""
    
    def test_hospital_role_strict_evidence(self):
        """Hospital role requires maximum evidence strictness."""
        registry = get_deployment_role_registry()
        profile = registry[DeploymentRole.HOSPITALS_MEDICINE.value]
        
        self.assertEqual(profile.evidence_strictness, EvidenceStrictness.MAXIMUM.value)
        self.assertEqual(profile.minimum_evidence_confidence, 0.9)
    
    def test_education_role_exploratory(self):
        """Education role uses exploratory communication."""
        registry = get_deployment_role_registry()
        profile = registry[DeploymentRole.EDUCATION.value]
        
        self.assertEqual(profile.communication_posture, CommunicationPosture.EXPLORATORY.value)
        self.assertEqual(profile.explanation_density, ExplanationDensity.ENHANCED.value)
    
    def test_aerospace_role_autonomous(self):
        """Aerospace role requires autonomy (no offline fallback)."""
        registry = get_deployment_role_registry()
        profile = registry[DeploymentRole.AEROSPACE_LONG_MISSION.value]
        
        self.assertFalse(profile.offline_fallback_allowed)
        self.assertEqual(profile.degraded_mode_behavior, DegradedModeBehavior.FALLBACK.value)
    
    def test_industry_role_prescriptive(self):
        """Industry role uses prescriptive communication."""
        registry = get_deployment_role_registry()
        profile = registry[DeploymentRole.INDUSTRY.value]
        
        self.assertEqual(profile.communication_posture, CommunicationPosture.PRESCRIPTIVE.value)
        self.assertEqual(profile.initiative_level, InitiativeLevel.MODERATE.value)
    
    def test_home_role_supportive(self):
        """Home family role uses supportive communication."""
        registry = get_deployment_role_registry()
        profile = registry[DeploymentRole.HOME_FAMILY.value]
        
        self.assertEqual(profile.communication_posture, CommunicationPosture.SUPPORTIVE.value)
        self.assertEqual(profile.caution_level, CautionLevel.ELEVATED.value)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_role_context(self):
        """Existing code works when role context not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Integration hooks should work without role engine
            guidance_result = integrate_with_adaptive_guidance({"test": "data"})
            self.assertEqual(guidance_result["test"], "data")
            
            narrative_result = integrate_with_narrative({"test": "data"})
            self.assertEqual(narrative_result["test"], "data")
            
            domain_result = integrate_with_domain_ontology({"test": "data"})
            self.assertEqual(domain_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without active context (uses defaults)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            # No context set - should use defaults
            adaptation = engine.compute_behavior_adaptation("nonexistent")
            
            self.assertIsNotNone(adaptation)
            self.assertEqual(adaptation.role, DeploymentRole.HOME_FAMILY.value)
    
    def test_missing_profile_fallback(self):
        """Engine handles missing profile gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            
            # Clear profiles
            original_profiles = engine.role_profiles.copy()
            engine.role_profiles = {}
            
            adaptation = engine.compute_behavior_adaptation("test")
            
            # Should fall back to default role profile
            self.assertIsNotNone(adaptation)
            self.assertEqual(adaptation.role, DeploymentRole.HOME_FAMILY.value)
            
            # Restore
            engine.role_profiles = original_profiles


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_role_profile_serialization(self):
        """Role profile serialization round-trip works."""
        original = DeploymentRoleProfile(
            role="test_role",
            name="Test",
            description="Description",
            minimum_evidence_confidence=0.7,
        )
        
        data = original.to_dict()
        recreated = DeploymentRoleProfile.from_dict(data)
        
        self.assertEqual(original.role, recreated.role)
        self.assertEqual(original.name, recreated.name)
        self.assertEqual(original.description, recreated.description)
        self.assertEqual(original.minimum_evidence_confidence, recreated.minimum_evidence_confidence)
    
    def test_context_serialization(self):
        """Context serialization round-trip works."""
        original = DeploymentContext(
            context_id="serial-test",
            role=DeploymentRole.HOSPITALS_MEDICINE.value,
            application_scope=["clinical", "diagnostic"],
        )
        
        data = original.to_dict()
        recreated = DeploymentContext.from_dict(data)
        
        self.assertEqual(original.context_id, recreated.context_id)
        self.assertEqual(original.role, recreated.role)
        self.assertEqual(original.application_scope, recreated.application_scope)
    
    def test_adaptation_serialization(self):
        """Adaptation serialization round-trip works."""
        original = RoleBehaviorAdaptation(
            role=DeploymentRole.EDUCATION.value,
            effective_communication_posture=CommunicationPosture.EXPLORATORY.value,
            effective_evidence_strictness=EvidenceStrictness.MODERATE.value,
            effective_caution_level=CautionLevel.NORMAL.value,
            effective_initiative_level=InitiativeLevel.MODERATE.value,
            effective_explanation_density=ExplanationDensity.ENHANCED.value,
            effective_escalation_style=EscalationStyle.GRADUAL.value,
            effective_degraded_mode_behavior=DegradedModeBehavior.CONSULTATIVE.value,
            minimum_evidence_confidence=0.65,
            max_single_step_confidence=0.85,
            max_suggestions_per_session=10,
            can_be_proactive=True,
            requires_explanation=True,
            min_explanation_length=100,
            escalation_delay_ms=2000,
        )
        
        data = original.to_dict()
        recreated = RoleBehaviorAdaptation.from_dict(data)
        
        self.assertEqual(original.role, recreated.role)
        self.assertEqual(original.minimum_evidence_confidence, recreated.minimum_evidence_confidence)
        self.assertEqual(original.max_suggestions_per_session, recreated.max_suggestions_per_session)


class TestIntegrationWithExistingLayers(TestCase):
    """Test integration with existing WESLR layers."""
    
    def test_integration_with_domain_ontology(self):
        """Integration with domain ontology works."""
        # This test verifies that the integration hook signature is compatible
        # with how domain_ontology.py uses similar integration patterns
        
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            engine.set_active_context(
                context_id="domain-test",
                role=DeploymentRole.INDUSTRY.value,
            )
            
            # Simulate domain ontology usage pattern
            domain_dict = {
                "domain_type": DeploymentRole.INDUSTRY.value,
                "minimum_evidence_confidence": 0.7,
            }
            
            # Apply integration
            result = integrate_with_domain_ontology(
                domain_dict,
                role_engine=engine,
                context_id="domain-test",
            )
            
            self.assertIn("deployment_role_context", result)
            self.assertIsNotNone(result["deployment_role_context"])
    
    def test_integration_with_trust_dynamics(self):
        """Integration with trust dynamics works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = DeploymentPersonaEngine(storage_path=tmpdir)
            engine.set_active_context(
                context_id="trust-test",
                role=DeploymentRole.HOSPITALS_MEDICINE.value,
            )
            
            trust_dict = {
                "relationship_id": "hospital-relationship",
                "trust_score": 0.5,
            }
            
            result = integrate_with_trust_dynamics(
                trust_dict,
                role_engine=engine,
                context_id="trust-test",
            )
            
            self.assertIn("deployment_role_context", result)
            self.assertIsNotNone(result["deployment_role_context"])


if __name__ == "__main__":
    import unittest
    unittest.main()
