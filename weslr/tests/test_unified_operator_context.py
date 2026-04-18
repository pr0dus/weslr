"""Tests for Unified Operator Context Surface (v31)

Tests unified_operator_context.py data models, manager, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.unified_operator_context import (
    ReliabilityMode,
    ContextSurfaceStatus,
    OperatorContextSummary,
    UnifiedOperatorContextManager,
    integrate_with_governance_view,
    integrate_with_operator_review,
    integrate_with_narrative,
    integrate_with_adaptive_guidance,
    integrate_with_longitudinal_patterns,
)


class TestOperatorContextModels(unittest.TestCase):
    """Test operator context data models."""

    def test_operator_context_summary_creation(self):
        """Test creating an operator context summary."""
        summary = OperatorContextSummary(
            surface_id="surface-001",
        )
        
        self.assertEqual(summary.surface_id, "surface-001")
        self.assertEqual(summary.status, ContextSurfaceStatus.ACTIVE.value)
        self.assertEqual(summary.reliability_mode, ReliabilityMode.NORMAL.value)

    def test_operator_context_summary_status_display(self):
        """Test status display method."""
        summary = OperatorContextSummary(
            surface_id="surface-001",
            status=ContextSurfaceStatus.PAUSED.value,
            reliability_mode=ReliabilityMode.STRICT.value,
        )
        
        display = summary.get_status_display()
        self.assertIn("PAUSED", display)
        self.assertIn("strict", display.lower())

    def test_operator_context_summary_get_state_overview(self):
        """Test state overview method."""
        summary = OperatorContextSummary(
            surface_id="surface-001",
            continuity_summary={"status": "active"},
            pattern_summary={"pattern_count": 5},
            household_summary={"household_count": 2},
            governance_summary={"scorecard_count": 1},
            evidence_summary={"evidence_count": 10},
            guidance_posture={"confidence": 0.8},
        )
        
        overview = summary.get_state_overview()
        
        self.assertEqual(overview["continuity"], "active")
        self.assertEqual(overview["patterns"], 5)
        self.assertEqual(overview["household"], 2)
        self.assertEqual(overview["governance"], 1)
        self.assertEqual(overview["evidence"], 10)
        self.assertEqual(overview["guidance_confidence"], 0.8)

    def test_operator_context_summary_serialization(self):
        """Test operator context summary to_dict/from_dict."""
        summary = OperatorContextSummary(
            surface_id="surface-001",
            operator_id="operator-001",
            session_id="session-001",
        )
        
        summary_dict = summary.to_dict()
        summary2 = OperatorContextSummary.from_dict(summary_dict)
        
        self.assertEqual(summary.surface_id, summary2.surface_id)
        self.assertEqual(summary.operator_id, summary2.operator_id)


class TestUnifiedOperatorContextManager(unittest.TestCase):
    """Test unified operator context manager."""

    def setUp(self):
        """Set up test manager."""
        self.manager = UnifiedOperatorContextManager()

    def test_create_surface(self):
        """Test creating a new operator context surface."""
        surface = self.manager.create_surface("surface-001", "operator-001", "session-001")
        
        self.assertIsNotNone(surface)
        self.assertEqual(surface.surface_id, "surface-001")
        self.assertEqual(surface.operator_id, "operator-001")
        self.assertEqual(surface.session_id, "session-001")

    def test_update_continuity(self):
        """Test updating continuity summary."""
        self.manager.create_surface("surface-001")
        
        continuity = {"status": "active", "confidence": 0.8}
        self.manager.update_continuity("surface-001", continuity)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.continuity_summary, continuity)

    def test_update_personalization(self):
        """Test updating personalization summary."""
        self.manager.create_surface("surface-001")
        
        personalization = {"profile_id": "profile-001", "communication_style": "detailed"}
        self.manager.update_personalization("surface-001", personalization)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.personalization_summary, personalization)

    def test_update_patterns(self):
        """Test updating pattern summary."""
        self.manager.create_surface("surface-001")
        
        patterns = {"pattern_count": 5, "last_pattern": "routine"}
        self.manager.update_patterns("surface-001", patterns)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.pattern_summary, patterns)

    def test_update_household(self):
        """Test updating household summary."""
        self.manager.create_surface("surface-001")
        
        household = {"household_count": 2, "household_id": "household-001"}
        self.manager.update_household("surface-001", household)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.household_summary, household)

    def test_update_domain(self):
        """Test updating domain summary."""
        self.manager.create_surface("surface-001")
        
        domain = {"domain_id": "domain-001", "current_task": "testing"}
        self.manager.update_domain("surface-001", domain)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.domain_summary, domain)

    def test_update_governance(self):
        """Test updating governance summary."""
        self.manager.create_surface("surface-001")
        
        governance = {"scorecard_count": 1, "last_decision": "execute"}
        self.manager.update_governance("surface-001", governance)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.governance_summary, governance)

    def test_set_reliability_mode(self):
        """Test setting reliability mode."""
        self.manager.create_surface("surface-001")
        
        self.assertTrue(self.manager.set_reliability_mode("surface-001", ReliabilityMode.STRICT.value))
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.reliability_mode, ReliabilityMode.STRICT.value)

    def test_update_evidence(self):
        """Test updating evidence summary."""
        self.manager.create_surface("surface-001")
        
        evidence = {"evidence_count": 10, "last_evidence": "evidence-001"}
        self.manager.update_evidence("surface-001", evidence)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.evidence_summary, evidence)

    def test_update_guidance_posture(self):
        """Test updating guidance posture."""
        self.manager.create_surface("surface-001")
        
        posture = {"confidence": 0.8, "posture": "active"}
        self.manager.update_guidance_posture("surface-001", posture)
        
        surface = self.manager.get_surface()
        self.assertEqual(surface.guidance_posture, posture)

    def test_pause_and_resume_surface(self):
        """Test pausing and resuming surface."""
        self.manager.create_surface("surface-001")
        
        self.assertTrue(self.manager.pause_surface("surface-001"))
        surface = self.manager.get_surface()
        self.assertEqual(surface.status, ContextSurfaceStatus.PAUSED.value)
        
        self.assertTrue(self.manager.resume_surface("surface-001"))
        self.assertEqual(surface.status, ContextSurfaceStatus.ACTIVE.value)

    def test_get_state_overview(self):
        """Test getting state overview."""
        self.manager.create_surface("surface-001")
        self.manager.update_continuity("surface-001", {"status": "active"})
        self.manager.update_patterns("surface-001", {"pattern_count": 5})
        self.manager.update_governance("surface-001", {"scorecard_count": 2})
        self.manager.set_reliability_mode("surface-001", ReliabilityMode.STRICT.value)
        
        overview = self.manager.get_state_overview()
        
        self.assertEqual(overview["status"], "active")
        self.assertEqual(overview["reliability_mode"], "strict")
        self.assertEqual(overview["patterns"], 5)
        self.assertEqual(overview["governance"], 2)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_surface("surface-001")
        self.manager.update_continuity("surface-001", {"status": "active"})
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["surface_count"], 1)
        self.assertIn("current_surface", manager_dict)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for governance, operator review, narrative, guidance, and patterns."""

    def test_integrate_with_governance_view_adds_operator_context(self):
        """Test that integration adds operator context to governance view."""
        governance_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("operator_context_available", result)
        self.assertIn("operator_context_status", result)
        self.assertFalse(result["operator_context_available"])

    def test_integrate_with_operator_review_adds_operator_context(self):
        """Test that integration adds operator context to operator review."""
        review_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertIn("operator_context_summary", result)
        self.assertEqual(result["reliability_mode"], ReliabilityMode.NORMAL.value)

    def test_integrate_with_narrative_adds_operator_context(self):
        """Test that integration adds operator context to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("operator_context_available", result)
        self.assertIn("operator_session_id", result)

    def test_integrate_with_adaptive_guidance_adds_operator_context(self):
        """Test that integration adds operator context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("operator_context_available", result)
        self.assertIn("current_reliability_mode", result)
        self.assertEqual(result["current_reliability_mode"], ReliabilityMode.NORMAL.value)

    def test_integrate_with_longitudinal_patterns_adds_operator_context(self):
        """Test that integration adds operator context to longitudinal patterns."""
        patterns_dict = {
            "pattern_id": "pattern-001",
        }
        
        result = integrate_with_longitudinal_patterns(patterns_dict)
        
        self.assertIn("operator_context", result)
        self.assertIn("session_id", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing operator context."""
        governance_dict = {
            "proposal_id": "proposal-001",
            "operator_context_available": True,
            "operator_context_status": "active",
            "reliability_mode": ReliabilityMode.STRICT.value,
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertTrue(result["operator_context_available"])
        self.assertEqual(result["operator_context_status"], "active")


if __name__ == "__main__":
    unittest.main()
