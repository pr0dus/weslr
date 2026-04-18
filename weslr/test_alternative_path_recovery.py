# test_alternative_path_recovery.py - WESLR v46: Alternative Path / Recovery Recommendation Layer Tests
# Focused tests for recovery recommendation layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.alternative_path_recovery import (
    BlockedPathType,
    BlockingReason,
    SaferAlternativeType,
    RecoveryConfidence,
    RecoveryStatus,
    BlockedPath,
    SaferAlternative,
    RecoveryRecommendation,
    ExplanationForRecovery,
    AlternativePathRecoveryEngine,
    integrate_with_constraint_invariant_layer,
    integrate_with_proof_gate,
    integrate_with_escalation,
    integrate_with_simulation,
    integrate_with_compromise_explanation,
)

# Import constraint_invariant for tests
from weslr.constraint_invariant import ViolationSeverity


class TestBlockedPathTypeEnum(TestCase):
    """Test blocked path type enum values."""
    
    def test_all_blocked_path_types_present(self):
        """All expected blocked path types are defined."""
        expected_types = [
            "blocked_by_constraint",
            "blocked_by_invariant",
            "blocked_by_proof_gate",
            "blocked_by_evidence",
            "blocked_by_capability",
            "blocked_by_authority",
            "blocked_by_timing",
            "blocked_by_rate_limit",
            "blocked_by_trust",
            "blocked_by_relationship",
        ]
        
        for blocked_type in expected_types:
            self.assertIn(blocked_type, [t.value for t in BlockedPathType])
    
    def test_blocked_path_types_are_strings(self):
        """All blocked path type values are strings."""
        for blocked_type in BlockedPathType:
            self.assertIsInstance(blocked_type.value, str)


class TestBlockingReasonEnum(TestCase):
    """Test blocking reason enum values."""
    
    def test_all_blocking_reasons_present(self):
        """All expected blocking reasons are defined."""
        expected_reasons = [
            "ethical_violation",
            "legal_violation",
            "security_violation",
            "privacy_violation",
            "trust_violation",
            "operational_violation",
            "insufficient_evidence",
            "failed_risk_assessment",
            "no_rollback",
            "low_confidence",
            "capability_prohibited",
            "capability_restricted",
            "no_authority",
            "rate_limit_exceeded",
            "not_allowed_at_time",
            "trust_too_low",
            "relationship_limited",
        ]
        
        for reason in expected_reasons:
            self.assertIn(reason, [r.value for r in BlockingReason])
    
    def test_blocking_reasons_are_strings(self):
        """All blocking reason values are strings."""
        for reason in BlockingReason:
            self.assertIsInstance(reason.value, str)


class TestSaferAlternativeTypeEnum(TestCase):
    """Test safer alternative type enum values."""
    
    def test_all_alternative_types_present(self):
        """All expected safer alternative types are defined."""
        expected_types = [
            "safer_alternative",
            "lower_scope",
            "delayed",
            "evidence_gathering",
            "escalation",
            "safer_delayed",
            "escalation_recommendation",
        ]
        
        for alt_type in expected_types:
            self.assertIn(alt_type, [t.value for t in SaferAlternativeType])
    
    def test_alternative_types_are_strings(self):
        """All safer alternative type values are strings."""
        for alt_type in SaferAlternativeType:
            self.assertIsInstance(alt_type.value, str)


class TestRecoveryConfidenceEnum(TestCase):
    """Test recovery confidence enum values."""
    
    def test_all_confidence_levels_present(self):
        """All expected confidence levels are defined."""
        expected_levels = [
            "low",
            "medium",
            "high",
            "very_high",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [l.value for l in RecoveryConfidence])
    
    def test_confidence_levels_are_strings(self):
        """All confidence level values are strings."""
        for level in RecoveryConfidence:
            self.assertIsInstance(level.value, str)


class TestRecoveryStatusEnum(TestCase):
    """Test recovery status enum values."""
    
    def test_all_recovery_statuses_present(self):
        """All expected recovery statuses are defined."""
        expected_statuses = [
            "generated",
            "reviewed",
            "used",
            "rejected",
            "implemented",
        ]
        
        for status in expected_statuses:
            self.assertIn(status, [s.value for s in RecoveryStatus])
    
    def test_recovery_statuses_are_strings(self):
        """All recovery status values are strings."""
        for status in RecoveryStatus:
            self.assertIsInstance(status.value, str)


class TestBlockedPath(TestCase):
    """Test BlockedPath data model."""
    
    def test_blocked_path_creation(self):
        """BlockedPath can be created and serialized."""
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            original_context={"key": "value"},
            blocked_path_type=BlockedPathType.BLOCKED_BY_CONSTRAINT.value,
            blocking_reason=BlockingReason.ETHICAL_VIOLATION.value,
        )
        
        self.assertEqual(blocked_path.blocked_path_id, "blocked_1")
        self.assertEqual(blocked_path.original_action, "test_action")
        self.assertEqual(blocked_path.blocking_reason, BlockingReason.ETHICAL_VIOLATION.value)
        
        # Test serialization
        data = blocked_path.to_dict()
        self.assertEqual(data["blocked_path_id"], "blocked_1")
        
        # Test deserialization
        blocked_path2 = BlockedPath.from_dict(data)
        self.assertEqual(blocked_path2.blocked_path_id, blocked_path.blocked_path_id)


class TestSaferAlternative(TestCase):
    """Test SaferAlternative data model."""
    
    def test_alternative_creation(self):
        """SaferAlternative can be created and serialized."""
        alternative = SaferAlternative(
            alternative_id="alt_1",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.EVIDENCE_GATHERING.value,
            alternative_description="Gather evidence first",
            expected_outcome={"confidence": "high"},
            confidence=RecoveryConfidence.HIGH.value,
        )
        
        self.assertEqual(alternative.alternative_id, "alt_1")
        self.assertEqual(alternative.alternative_type, SaferAlternativeType.EVIDENCE_GATHERING.value)
        self.assertEqual(alternative.confidence, RecoveryConfidence.HIGH.value)
        
        # Test serialization
        data = alternative.to_dict()
        self.assertEqual(data["alternative_id"], "alt_1")
        
        # Test deserialization
        alternative2 = SaferAlternative.from_dict(data)
        self.assertEqual(alternative2.alternative_id, alternative.alternative_id)
    
    def test_alternative_with_tradeoffs(self):
        """SaferAlternative can include tradeoffs and benefits."""
        alternative = SaferAlternative(
            alternative_id="alt_2",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.DELAYED.value,
            alternative_description="Delay for better conditions",
            expected_outcome={},
            confidence=RecoveryConfidence.MEDIUM.value,
            tradeoffs=["delay", "opportunity_cost"],
            benefits=["restored_trust", "higher_success_rate"],
        )
        
        self.assertEqual(len(alternative.tradeoffs), 2)
        self.assertEqual(len(alternative.benefits), 2)


class TestRecoveryRecommendation(TestCase):
    """Test RecoveryRecommendation data model."""
    
    def test_recovery_creation(self):
        """RecoveryRecommendation can be created and serialized."""
        recovery = RecoveryRecommendation(
            recovery_id="recovery_1",
            blocked_path_id="blocked_1",
            safer_alternatives=["alt_1", "alt_2"],
            preferred_alternative_id="alt_1",
            overall_confidence=RecoveryConfidence.MEDIUM.value,
            risk_reduction=0.5,
            implementation_steps=["step_1", "step_2"],
            required_human_review=True,
        )
        
        self.assertEqual(recovery.recovery_id, "recovery_1")
        self.assertEqual(len(recovery.safer_alternatives), 2)
        self.assertEqual(recovery.preferred_alternative_id, "alt_1")
        self.assertTrue(recovery.required_human_review)
        
        # Test serialization
        data = recovery.to_dict()
        self.assertEqual(data["recovery_id"], "recovery_1")
        
        # Test deserialization
        recovery2 = RecoveryRecommendation.from_dict(data)
        self.assertEqual(recovery2.recovery_id, recovery.recovery_id)


class TestExplanationForRecovery(TestCase):
    """Test ExplanationForRecovery data model."""
    
    def test_explanation_creation(self):
        """ExplanationForRecovery can be created and serialized."""
        explanation = ExplanationForRecovery(
            explanation_id="exp_1",
            recovery_id="recovery_1",
            explanation_type="recovery_recommendation",
            explanation_text="Action blocked, recovery recommended.",
            original_action="blocked_action",
            blocking_reason=BlockingReason.INSUFFICIENT_EVIDENCE.value,
            blocked_at="2026-04-06T19:26:00Z",
            recommended_alternative="alt_1",
            why_this_alternative="Best balance of safety and goals",
            why_other_alternatives_not_chosen=["alt_2 is less optimal"],
            confidence=0.7,
            risk_reduction_explanation="Risk reduced by 50%",
        )
        
        self.assertEqual(explanation.explanation_id, "exp_1")
        self.assertEqual(len(explanation.why_other_alternatives_not_chosen), 1)
        
        # Test serialization
        data = explanation.to_dict()
        self.assertEqual(data["explanation_id"], "exp_1")
        
        # Test deserialization
        explanation2 = ExplanationForRecovery.from_dict(data)
        self.assertEqual(explanation2.explanation_id, explanation.explanation_id)


class TestAlternativePathRecoveryEngine(TestCase):
    """Test AlternativePathRecoveryEngine."""
    
    def setUp(self):
        """Set up test engine with temp storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = AlternativePathRecoveryEngine(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_record_blocked_path(self):
        """Record blocked path works."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_CONSTRAINT.value,
            blocking_reason=BlockingReason.ETHICAL_VIOLATION.value,
            severity=ViolationSeverity.HIGH.value,
        )
        
        self.engine.record_blocked_path(blocked_path)
        retrieved = self.engine.get_blocked_path("blocked_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.original_action, "test_action")
    
    def test_add_alternative(self):
        """Add alternative works."""
        alternative = SaferAlternative(
            alternative_id="alt_1",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.EVIDENCE_GATHERING.value,
            alternative_description="Gather evidence",
        )
        
        self.engine.add_alternative(alternative)
        retrieved = self.engine.get_alternative("alt_1")
        self.assertIsNotNone(retrieved)
    
    def test_get_all_alternatives_enabled(self):
        """Get all alternatives filters by enabled."""
        enabled = SaferAlternative(
            alternative_id="alt_enabled",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.DELAYED.value,
            alternative_description="Enabled",
            enabled=True,
        )
        disabled = SaferAlternative(
            alternative_id="alt_disabled",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.ESCALATION.value,
            alternative_description="Disabled",
            enabled=False,
        )
        
        self.engine.add_alternative(enabled)
        self.engine.add_alternative(disabled)
        
        all_alts = self.engine.get_all_alternatives()
        self.assertEqual(len(all_alts), 1)
        self.assertEqual(all_alts[0].alternative_id, "alt_enabled")
    
    def test_create_recovery(self):
        """Create recovery works."""
        recovery = RecoveryRecommendation(
            recovery_id="recovery_1",
            blocked_path_id="blocked_1",
            safer_alternatives=["alt_1"],
            preferred_alternative_id="alt_1",
        )
        
        self.engine.create_recovery(recovery)
        retrieved = self.engine.get_recovery("recovery_1")
        self.assertIsNotNone(retrieved)
    
    def test_create_explanation(self):
        """Create explanation works."""
        explanation = ExplanationForRecovery(
            explanation_id="exp_1",
            recovery_id="recovery_1",
            explanation_type="recovery_recommendation",
            explanation_text="Explanation text",
            original_action="blocked_action",
            blocking_reason=BlockingReason.INSUFFICIENT_EVIDENCE.value,
            blocked_at="2026-04-06T19:26:00Z",
        )
        
        self.engine.create_explanation(explanation)
        retrieved = self.engine.get_explanation("exp_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.explanation_text, "Explanation text")
    
    def test_to_dict(self):
        """to_dict returns expected structure."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_CONSTRAINT.value,
            blocking_reason=BlockingReason.ETHICAL_VIOLATION.value,
            severity=ViolationSeverity.HIGH.value,
        )
        self.engine.record_blocked_path(blocked_path)
        
        alternative = SaferAlternative(
            alternative_id="alt_1",
            blocked_path_id="blocked_1",
            alternative_type=SaferAlternativeType.DELAYED.value,
            alternative_description="Delay",
        )
        self.engine.add_alternative(alternative)
        
        recovery = RecoveryRecommendation(
            recovery_id="recovery_1",
            blocked_path_id="blocked_1",
            safer_alternatives=["alt_1"],
            preferred_alternative_id="alt_1",
        )
        self.engine.create_recovery(recovery)
        
        result = self.engine.to_dict()
        self.assertEqual(result["blocked_path_count"], 1)
        self.assertEqual(result["alternative_count"], 1)
        self.assertEqual(result["recovery_count"], 1)
    
    def test_generate_recovery_recommendation_evidence_gathering(self):
        """generate_recovery_recommendation generates evidence-gathering alternative."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_PROOF_GATE.value,
            blocking_reason=BlockingReason.INSUFFICIENT_EVIDENCE.value,
            severity=ViolationSeverity.HIGH.value,
        )
        
        recovery = self.engine.generate_recovery_recommendation(blocked_path)
        self.assertIsNotNone(recovery)
        self.assertIsNotNone(recovery.preferred_alternative_id)
        
        # Verify evidence-gathering alternative was created
        alternative = self.engine.get_alternative(recovery.preferred_alternative_id)
        self.assertIsNotNone(alternative)
        self.assertEqual(alternative.alternative_type, SaferAlternativeType.EVIDENCE_GATHERING.value)
    
    def test_generate_recovery_recommendation_escalation(self):
        """generate_recovery_recommendation generates escalation when capability blocked."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_CAPABILITY.value,
            blocking_reason=BlockingReason.CAPABILITY_PROHIBITED.value,
            severity=ViolationSeverity.HIGH.value,
        )
        
        recovery = self.engine.generate_recovery_recommendation(blocked_path)
        self.assertIsNotNone(recovery)
        
        # Verify escalation alternative was created
        alternative = self.engine.get_alternative(recovery.preferred_alternative_id)
        self.assertIsNotNone(alternative)
        self.assertEqual(alternative.alternative_type, SaferAlternativeType.ESCALATION.value)
    
    def test_generate_recovery_recommendation_delayed(self):
        """generate_recovery_recommendation generates delayed alternative for trust issues."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_TRUST.value,
            blocking_reason=BlockingReason.TRUST_TOO_LOW.value,
            severity=ViolationSeverity.HIGH.value,
        )
        
        recovery = self.engine.generate_recovery_recommendation(blocked_path)
        self.assertIsNotNone(recovery)
        
        # Verify delayed alternative was created
        alternative = self.engine.get_alternative(recovery.preferred_alternative_id)
        self.assertIsNotNone(alternative)
        self.assertEqual(alternative.alternative_type, SaferAlternativeType.DELAYED.value)
    
    def test_generate_recovery_recommendation_lower_scope(self):
        """generate_recovery_recommendation generates lower-scope alternative as fallback."""
        from weslr.constraint_invariant import ViolationSeverity
        
        blocked_path = BlockedPath(
            blocked_path_id="blocked_1",
            original_action="test_action",
            blocked_path_type=BlockedPathType.BLOCKED_BY_INVARIANT.value,
            blocking_reason=BlockingReason.OPERATIONAL_VIOLATION.value,
            severity=ViolationSeverity.HIGH.value,
        )
        
        recovery = self.engine.generate_recovery_recommendation(blocked_path)
        self.assertIsNotNone(recovery)
        
        # Verify lower-scope alternative was created
        alternative = self.engine.get_alternative(recovery.preferred_alternative_id)
        self.assertIsNotNone(alternative)
        self.assertEqual(alternative.alternative_type, SaferAlternativeType.LOWER_SCOPE.value)


class TestIntegrationHooks(TestCase):
    """Test integration hooks with AlternativePathRecoveryEngine."""
    
    def test_integrate_with_constraint_invariant_layer(self):
        """integrate_with_constraint_invariant_layer adds recovery context."""
        engine = AlternativePathRecoveryEngine()
        
        constraint_dict = {"existing_field": "value"}
        result = integrate_with_constraint_invariant_layer(
            constraint_dict,
            engine,
            blocked_action="test_action",
            blocking_rule_id="constraint_1",
        )
        
        self.assertIn("recovery_context", result)
        self.assertIsNotNone(result["recovery_context"])
        self.assertEqual(result["recovery_context"]["path_blocked"], True)
        self.assertEqual(result["recovery_context"]["recovery_generated"], True)
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds recovery context."""
        engine = AlternativePathRecoveryEngine()
        
        proof_dict = {"existing_field": "value"}
        result = integrate_with_proof_gate(
            proof_dict,
            engine,
            blocked_action="test_action",
            blocking_reason=BlockingReason.INSUFFICIENT_EVIDENCE.value,
        )
        
        self.assertIn("recovery_context", result)
        self.assertIsNotNone(result["recovery_context"])
        self.assertEqual(result["recovery_context"]["path_blocked"], True)
    
    def test_integrate_with_escalation(self):
        """integrate_with_escalation adds recovery context."""
        engine = AlternativePathRecoveryEngine()
        
        escalation_dict = {"existing_field": "value"}
        result = integrate_with_escalation(
            escalation_dict,
            engine,
            blocked_action="test_action",
            trigger=BlockingReason.CAPABILITY_PROHIBITED.value,
        )
        
        self.assertIn("recovery_context", result)
        self.assertIsNotNone(result["recovery_context"])
        self.assertEqual(result["recovery_context"]["path_blocked"], True)
    
    def test_integrate_with_simulation(self):
        """integrate_with_simulation adds recovery context."""
        engine = AlternativePathRecoveryEngine()
        
        simulation_dict = {"existing_field": "value"}
        result = integrate_with_simulation(
            simulation_dict,
            engine,
            blocked_action="test_action",
            blocking_context={"reason": BlockingReason.INSUFFICIENT_EVIDENCE.value},
        )
        
        self.assertIn("recovery_context", result)
        self.assertIsNotNone(result["recovery_context"])
        self.assertEqual(result["recovery_context"]["path_blocked"], True)
        self.assertEqual(result["recovery_context"]["recovery_generated"], True)
    
    def test_integrate_with_compromise_explanation(self):
        """integrate_with_compromise_explanation adds recovery context."""
        engine = AlternativePathRecoveryEngine()
        
        compromise_dict = {"existing_field": "value"}
        result = integrate_with_compromise_explanation(
            compromise_dict,
            engine,
            blocked_action="test_action",
            blocking_reason=BlockingReason.TRUST_TOO_LOW.value,
        )
        
        self.assertIn("recovery_context", result)
        self.assertIsNotNone(result["recovery_context"])
        self.assertEqual(result["recovery_context"]["path_blocked"], True)
