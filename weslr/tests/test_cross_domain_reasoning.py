"""Tests for Cross-Domain Reasoning / Transfer Layer (v25)

Tests cross_domain_reasoning.py data models, engine, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.cross_domain_reasoning import (
    TransferType,
    TransferSafety,
    ReasoningPattern,
    DomainTransferContext,
    CrossDomainReasoningEngine,
    integrate_with_domain_ontology,
    integrate_with_governance_view,
    integrate_with_narrative,
    integrate_with_proposal_realization,
)


class TestTransferModelModels(unittest.TestCase):
    """Test cross-domain reasoning data models."""

    def test_reasoning_pattern_creation(self):
        """Test creating a reasoning pattern."""
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="risk_assessment",
            reasoning_steps=["step1", "step2"],
            evidence_types=["user_feedback", "metrics"],
            transferability_score=0.8,
        )
        
        self.assertEqual(pattern.pattern_id, "pattern-001")
        self.assertEqual(pattern.domain, "home-assistant")
        self.assertEqual(pattern.pattern_type, "risk_assessment")
        self.assertEqual(len(pattern.reasoning_steps), 2)
        self.assertEqual(pattern.transferability_score, 0.8)

    def test_reasoning_pattern_forbidden_transfers(self):
        """Test forbidden transfers."""
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="finance",
            pattern_type="risk_assessment",
            confidence=0.9,  # High confidence to get SAFE instead of REQUIRES_REVIEW
            forbidden_transfers=["healthcare", "legal"],
        )
        
        self.assertEqual(pattern.is_transferable_to("finance"), TransferSafety.SAFE.value)
        self.assertEqual(pattern.is_transferable_to("healthcare"), TransferSafety.FORBIDDEN.value)
        self.assertEqual(pattern.is_transferable_to("legal"), TransferSafety.FORBIDDEN.value)

    def test_reasoning_pattern_record_transfer(self):
        """Test recording a transfer."""
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
            transfer_count=0,
        )
        
        pattern.record_transfer()
        self.assertEqual(pattern.transfer_count, 1)
        self.assertIsNotNone(pattern.last_used_at)

    def test_reasoning_pattern_serialization(self):
        """Test reasoning pattern to_dict/from_dict."""
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="risk_assessment",
            confidence=0.9,
        )
        
        pattern_dict = pattern.to_dict()
        pattern2 = ReasoningPattern.from_dict(pattern_dict)
        
        self.assertEqual(pattern.pattern_id, pattern2.pattern_id)
        self.assertEqual(pattern.domain, pattern2.domain)
        self.assertEqual(pattern.confidence, pattern2.confidence)

    def test_domain_transfer_context_creation(self):
        """Test creating a domain transfer context."""
        context = DomainTransferContext(
            pattern_id="pattern-001",
            originating_domain="home-assistant",
            target_domain="iot",
            transfer_type=TransferType.DIRECT.value,
            safety_classification=TransferSafety.SAFE.value,
            evidence_threshold=0.6,
        )
        
        self.assertEqual(context.pattern_id, "pattern-001")
        self.assertEqual(context.originating_domain, "home-assistant")
        self.assertEqual(context.target_domain, "iot")
        self.assertEqual(context.transfer_type, TransferType.DIRECT.value)
        self.assertTrue(context.is_allowed())
        self.assertFalse(context.rejected)

    def test_domain_transfer_context_rejection(self):
        """Test rejecting a transfer."""
        context = DomainTransferContext(
            pattern_id="pattern-001",
            originating_domain="home-assistant",
            target_domain="iot",
            transfer_type=TransferType.DIRECT.value,
            safety_classification=TransferSafety.SAFE.value,
            evidence_threshold=0.6,
        )
        
        self.assertTrue(context.is_allowed())
        
        context.set_approval(False, "Safety concern")
        self.assertFalse(context.is_allowed())
        self.assertTrue(context.rejected)
        self.assertEqual(context.rejection_reason, "Safety concern")

    def test_domain_transfer_context_approval(self):
        """Test approving a transfer."""
        context = DomainTransferContext(
            pattern_id="pattern-001",
            originating_domain="home-assistant",
            target_domain="iot",
            transfer_type=TransferType.DIRECT.value,
            safety_classification=TransferSafety.SAFE.value,
            evidence_threshold=0.6,
        )
        
        self.assertTrue(context.is_allowed())
        
        context.set_approval(True, "Approved after review")
        self.assertTrue(context.is_allowed())
        self.assertTrue(context.approved)
        self.assertEqual(context.approval_reason, "Approved after review")

    def test_domain_transfer_context_serialization(self):
        """Test domain transfer context to_dict/from_dict."""
        context = DomainTransferContext(
            pattern_id="pattern-001",
            originating_domain="home-assistant",
            target_domain="iot",
            transfer_type=TransferType.ADAPTED.value,
            safety_classification=TransferSafety.SAFE.value,
            evidence_threshold=0.6,
        )
        
        context_dict = context.to_dict()
        context2 = DomainTransferContext.from_dict(context_dict)
        
        self.assertEqual(context.pattern_id, context2.pattern_id)
        self.assertEqual(context.originating_domain, context2.originating_domain)
        self.assertEqual(context.target_domain, context2.target_domain)
        self.assertEqual(context.transfer_type, context2.transfer_type)


class TestCrossDomainReasoningEngine(unittest.TestCase):
    """Test cross-domain reasoning engine."""

    def test_register_pattern(self):
        """Test registering a pattern."""
        engine = CrossDomainReasoningEngine()
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
        )
        
        engine.register_pattern(pattern)
        self.assertEqual(engine.get_pattern("pattern-001"), pattern)

    def test_find_transferable_patterns(self):
        """Test finding transferable patterns."""
        engine = CrossDomainReasoningEngine()
        
        # Pattern with high confidence
        pattern1 = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
            confidence=0.9,
        )
        engine.register_pattern(pattern1)
        
        # Pattern with low confidence
        pattern2 = ReasoningPattern(
            pattern_id="pattern-002",
            domain="iot",
            pattern_type="forecast",
            confidence=0.5,
        )
        engine.register_pattern(pattern2)
        
        transferable = engine.find_transferable_patterns("iot")
        self.assertEqual(len(transferable), 2)  # Both patterns are transferable (no forbidden)

    def test_assess_transfer_safe(self):
        """Test assessing a safe transfer."""
        engine = CrossDomainReasoningEngine()
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
            confidence=0.9,
            originating_domain="home-assistant",
        )
        engine.register_pattern(pattern)
        
        context = engine.assess_transfer("pattern-001", "home-assistant", evidence_confidence=0.7)
        
        self.assertEqual(context.originating_domain, "home-assistant")
        self.assertEqual(context.target_domain, "home-assistant")
        self.assertEqual(context.transfer_type, TransferType.DIRECT.value)
        self.assertEqual(context.safety_classification, TransferSafety.SAFE.value)
        self.assertTrue(context.is_allowed())

    def test_assess_transfer_forbidden(self):
        """Test assessing a forbidden transfer."""
        engine = CrossDomainReasoningEngine()
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
            confidence=0.9,
            forbidden_transfers=["healthcare"],
        )
        engine.register_pattern(pattern)
        
        context = engine.assess_transfer("pattern-001", "healthcare", evidence_confidence=0.7)
        
        self.assertEqual(context.safety_classification, TransferSafety.FORBIDDEN.value)
        self.assertFalse(context.is_allowed())

    def test_assess_transfer_evidence_gap(self):
        """Test assessing transfer with evidence gap."""
        engine = CrossDomainReasoningEngine()
        pattern = ReasoningPattern(
            pattern_id="pattern-001",
            domain="home-assistant",
            pattern_type="forecast",
            confidence=0.9,
        )
        engine.register_pattern(pattern)
        
        context = engine.assess_transfer("pattern-001", "iot", evidence_confidence=0.4)
        
        self.assertEqual(context.safety_classification, TransferSafety.EVIDENCE_GAP.value)
        self.assertIn("Required", context.evidence_adjustment_reason or "")

    def test_assess_transfer_not_found(self):
        """Test assessing transfer for non-existent pattern."""
        engine = CrossDomainReasoningEngine()
        
        context = engine.assess_transfer("pattern-999", "iot", evidence_confidence=0.7)
        
        self.assertEqual(context.safety_classification, TransferSafety.FORBIDDEN.value)
        self.assertTrue(context.rejected)
        self.assertEqual(context.rejection_reason, "Pattern not found")


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for domain ontology, governance, narrative, and realization."""

    def test_integrate_with_domain_ontology_adds_metadata(self):
        """Test that integration adds transfer metadata to domain ontology."""
        ontology_dict = {
            "domain_id": "home",
            "name": "Home Assistant",
        }
        
        result = integrate_with_domain_ontology(ontology_dict)
        
        self.assertIn("transferable_patterns", result)
        self.assertIn("forbidden_transfers", result)
        self.assertIn("transfer_constraints", result)
        self.assertEqual(result["transferable_patterns"], [])
        self.assertEqual(result["forbidden_transfers"], [])

    def test_integrate_with_domain_ontology_preserves_existing(self):
        """Test that integration preserves existing transfer metadata."""
        ontology_dict = {
            "domain_id": "home",
            "transferable_patterns": ["pattern-001"],
        }
        
        result = integrate_with_domain_ontology(ontology_dict)
        
        self.assertEqual(result["transferable_patterns"], ["pattern-001"])

    def test_integrate_with_governance_view_adds_transfer_context(self):
        """Test that integration adds transfer context to governance."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("transfer_context", result)
        self.assertIn("transfer_safety", result)
        self.assertFalse(result["transfer_blocked"])
        self.assertEqual(result["transfer_blocked_reasons"], [])

    def test_integrate_with_governance_view_preserves_existing(self):
        """Test that integration preserves existing transfer context."""
        governance_dict = {
            "proposal_id": "prop-001",
            "transfer_blocked": True,
            "transfer_blocked_reasons": ["Safety constraint"],
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertTrue(result["transfer_blocked"])
        self.assertEqual(result["transfer_blocked_reasons"], ["Safety constraint"])

    def test_integrate_with_narrative_adds_transfer_hint(self):
        """Test that integration adds transfer hint to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("transfer_hint", result)
        self.assertIn("domain_transfer_safe", result)
        self.assertTrue(result["domain_transfer_safe"])

    def test_integrate_with_proposal_realization_adds_transfer_context(self):
        """Test that integration adds transfer context to proposal realization."""
        realization_dict = {
            "plan_id": "plan-001",
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertIn("transfer_context", result)
        self.assertIn("transfer_required_evidence", result)
        self.assertEqual(result["transfer_required_evidence"], 0.0)
        self.assertFalse(result["transfer_blocked"])

    def test_integrate_with_proposal_realization_preserves_existing(self):
        """Test that integration preserves existing transfer context."""
        realization_dict = {
            "plan_id": "plan-001",
            "transfer_required_evidence": 0.7,
            "transfer_blocked": True,
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertEqual(result["transfer_required_evidence"], 0.7)
        self.assertTrue(result["transfer_blocked"])


if __name__ == "__main__":
    unittest.main()
