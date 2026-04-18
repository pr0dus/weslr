# test_state_transition.py - WESLR v47: State Transition / Outcome Orchestration Layer Tests
# Focused tests for state transition orchestration layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.state_transition import (
    TransitionState,
    TransitionTrigger,
    TransitionConfidence,
    TransitionReason,
    StateTransition,
    AllowedTransition,
    RollbackTransition,
    TransitionExplanation,
    StateTransitionEngine,
    integrate_with_change_proposals,
    integrate_with_proof_gate,
    integrate_with_escalation,
    integrate_with_outcome_feedback,
    integrate_with_recovery_layer,
)


class TestTransitionStateEnum(TestCase):
    """Test transition state enum values."""
    
    def test_all_states_present(self):
        """All expected transition states are defined."""
        expected_states = [
            "draft",
            "pending",
            "active",
            "blocked",
            "deferred",
            "approved",
            "denied",
            "executed",
            "failed",
            "rolled_back",
            "cancelled",
            "recovered",
            "escalated",
            "calibrated",
            "feedback_received",
        ]
        
        for state in expected_states:
            self.assertIn(state, [s.value for s in TransitionState])
    
    def test_states_are_strings(self):
        """All state values are strings."""
        for state in TransitionState:
            self.assertIsInstance(state.value, str)


class TestTransitionTriggerEnum(TestCase):
    """Test transition trigger enum values."""
    
    def test_all_triggers_present(self):
        """All expected transition triggers are defined."""
        expected_triggers = [
            "created",
            "submitted",
            "review_started",
            "review_complete",
            "approved",
            "denied",
            "rejected",
            "executed",
            "execution_complete",
            "execution_failed",
            "blocked",
            "deferred",
            "cancelled",
            "rolled_back",
            "escalated",
            "recovered",
            "calibrated",
            "feedback_received",
            "timed_out",
        ]
        
        for trigger in expected_triggers:
            self.assertIn(trigger, [t.value for t in TransitionTrigger])
    
    def test_triggers_are_strings(self):
        """All trigger values are strings."""
        for trigger in TransitionTrigger:
            self.assertIsInstance(trigger.value, str)


class TestTransitionConfidenceEnum(TestCase):
    """Test transition confidence enum values."""
    
    def test_all_confidence_levels_present(self):
        """All expected confidence levels are defined."""
        expected_levels = [
            "low",
            "medium",
            "high",
            "very_high",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [l.value for l in TransitionConfidence])
    
    def test_confidence_levels_are_strings(self):
        """All confidence level values are strings."""
        for level in TransitionConfidence:
            self.assertIsInstance(level.value, str)


class TestStateTransition(TestCase):
    """Test StateTransition data model."""
    
    def test_transition_creation(self):
        """StateTransition can be created and serialized."""
        transition = StateTransition(
            transition_id="transition_1",
            object_type="change_proposal",
            object_id="proposal_1",
            previous_state=TransitionState.DRAFT.value,
            new_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        
        self.assertEqual(transition.transition_id, "transition_1")
        self.assertEqual(transition.previous_state, TransitionState.DRAFT.value)
        self.assertEqual(transition.new_state, TransitionState.PENDING.value)
        
        # Test serialization
        data = transition.to_dict()
        self.assertEqual(data["transition_id"], "transition_1")
        
        # Test deserialization
        transition2 = StateTransition.from_dict(data)
        self.assertEqual(transition2.transition_id, transition.transition_id)
    
    def test_transition_with_context(self):
        """StateTransition can include context."""
        transition = StateTransition(
            transition_id="transition_2",
            object_type="change_proposal",
            object_id="proposal_2",
            previous_state=TransitionState.PENDING.value,
            new_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
            actor="operator",
            context={"reason": "business_justification", "risk_level": "low"},
            confidence=TransitionConfidence.HIGH.value,
        )
        
        self.assertEqual(transition.actor, "operator")
        self.assertEqual(len(transition.context), 2)
        self.assertEqual(transition.confidence, TransitionConfidence.HIGH.value)


class TestAllowedTransition(TestCase):
    """Test AllowedTransition data model."""
    
    def test_allowed_transition_creation(self):
        """AllowedTransition can be created and serialized."""
        allowed = AllowedTransition(
            allowed_id="allowed_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
            requires_approval=False,
        )
        
        self.assertEqual(allowed.allowed_id, "allowed_1")
        self.assertEqual(allowed.from_state, TransitionState.DRAFT.value)
        self.assertEqual(allowed.to_state, TransitionState.PENDING.value)
        self.assertFalse(allowed.requires_approval)
        
        # Test serialization
        data = allowed.to_dict()
        self.assertEqual(data["allowed_id"], "allowed_1")
        
        # Test deserialization
        allowed2 = AllowedTransition.from_dict(data)
        self.assertEqual(allowed2.allowed_id, allowed.allowed_id)
    
    def test_allowed_transition_with_conditions(self):
        """AllowedTransition can include conditions."""
        allowed = AllowedTransition(
            allowed_id="allowed_2",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
            required_conditions=["risk_assessment_complete", "legal_review_passed"],
            optional_conditions=["stakeholder_consulted"],
            min_confidence=TransitionConfidence.MEDIUM.value,
            max_retries=3,
            requires_approval=True,
        )
        
        self.assertEqual(len(allowed.required_conditions), 2)
        self.assertEqual(len(allowed.optional_conditions), 1)
        self.assertEqual(allowed.max_retries, 3)


class TestRollbackTransition(TestCase):
    """Test RollbackTransition data model."""
    
    def test_rollback_creation(self):
        """RollbackTransition can be created and serialized."""
        rollback = RollbackTransition(
            rollback_id="rollback_1",
            transition_id="transition_1",
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.PENDING.value,
            rollback_reason="execution_failed_safety_check",
        )
        
        self.assertEqual(rollback.rollback_id, "rollback_1")
        self.assertEqual(rollback.transition_id, "transition_1")
        self.assertEqual(rollback.original_state, TransitionState.EXECUTED.value)
        self.assertEqual(rollback.rollback_to_state, TransitionState.PENDING.value)
        
        # Test serialization
        data = rollback.to_dict()
        self.assertEqual(data["rollback_id"], "rollback_1")
        
        # Test deserialization
        rollback2 = RollbackTransition.from_dict(data)
        self.assertEqual(rollback2.rollback_id, rollback.rollback_id)
    
    def test_rollback_with_steps(self):
        """RollbackTransition can include rollback steps."""
        rollback = RollbackTransition(
            rollback_id="rollback_2",
            transition_id="transition_2",
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.APPROVED.value,
            rollback_reason="rollback_required",
            rollback_steps=["revert_database_changes", "restore_backup", "notify_stakeholders"],
            completed=True,
        )
        
        self.assertEqual(len(rollback.rollback_steps), 3)
        self.assertTrue(rollback.completed)


class TestTransitionExplanation(TestCase):
    """Test TransitionExplanation data model."""
    
    def test_explanation_creation(self):
        """TransitionExplanation can be created and serialized."""
        explanation = TransitionExplanation(
            explanation_id="exp_1",
            transition_id="transition_1",
            object_type="change_proposal",
            object_id="proposal_1",
            explanation_type="state_transition",
            explanation_text="Transitioned from draft to pending.",
            previous_state=TransitionState.DRAFT.value,
            new_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
            why_transition="Trigger submitted caused transition.",
            why_not_other_transitions=["cancelled not applicable"],
            confidence=0.7,
            confidence_reasoning="Transition follows defined allowed transitions.",
        )
        
        self.assertEqual(explanation.explanation_id, "exp_1")
        self.assertEqual(len(explanation.why_not_other_transitions), 1)
        
        # Test serialization
        data = explanation.to_dict()
        self.assertEqual(data["explanation_id"], "exp_1")
        
        # Test deserialization
        explanation2 = TransitionExplanation.from_dict(data)
        self.assertEqual(explanation2.explanation_id, explanation.explanation_id)


class TestStateTransitionEngine(TestCase):
    """Test StateTransitionEngine."""
    
    def setUp(self):
        """Set up test engine with in-memory storage."""
        self.engine = StateTransitionEngine(in_memory=True)
    
    def tearDown(self):
        """Clean up (no-op for in-memory storage)."""
        pass
    
    def test_record_transition(self):
        """Record transition works."""
        transition = StateTransition(
            transition_id="transition_1",
            object_type="change_proposal",
            object_id="proposal_1",
            previous_state=TransitionState.DRAFT.value,
            new_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        
        self.engine.record_transition(transition)
        retrieved = self.engine.get_transition("transition_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.new_state, TransitionState.PENDING.value)
    
    def test_add_allowed_transition(self):
        """Add allowed transition works."""
        allowed = AllowedTransition(
            allowed_id="allowed_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        
        self.engine.add_allowed_transition(allowed)
        retrieved = self.engine.get_allowed_transition(
            TransitionState.DRAFT.value,
            TransitionState.PENDING.value,
        )
        self.assertIsNotNone(retrieved)
    
    def test_is_transition_allowed(self):
        """is_transition_allowed returns True for valid transitions."""
        # Default transitions include draft->pending
        self.assertTrue(
            self.engine.is_transition_allowed(
                TransitionState.DRAFT.value,
                TransitionState.PENDING.value,
                TransitionTrigger.SUBMITTED.value,
            )
        )
    
    def test_is_transition_not_allowed(self):
        """is_transition_allowed returns False for invalid transitions."""
        # Draft->approved is not a direct allowed transition
        self.assertFalse(
            self.engine.is_transition_allowed(
                TransitionState.DRAFT.value,
                TransitionState.APPROVED.value,
                TransitionTrigger.APPROVED.value,
            )
        )
    
    def test_record_rollback(self):
        """Record rollback works."""
        rollback = RollbackTransition(
            rollback_id="rollback_1",
            transition_id="transition_1",
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.PENDING.value,
            rollback_reason="execution_failed",
        )
        
        self.engine.record_rollback(rollback)
        retrieved = self.engine.get_rollback("rollback_1")
        self.assertIsNotNone(retrieved)
    
    def test_create_explanation(self):
        """Create explanation works."""
        explanation = TransitionExplanation(
            explanation_id="exp_1",
            transition_id="transition_1",
            object_type="change_proposal",
            object_id="proposal_1",
            explanation_type="state_transition",
            explanation_text="Explanation text",
            previous_state=TransitionState.DRAFT.value,
            new_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
            why_transition="Test transition explanation.",
            why_not_other_transitions=["other not applicable"],
        )
        
        self.engine.create_explanation(explanation)
        retrieved = self.engine.get_explanation("exp_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.explanation_text, "Explanation text")
    
    def test_generate_transition(self):
        """generate_transition creates valid transitions."""
        transition = self.engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        
        self.assertIsNotNone(transition)
        self.assertEqual(transition.previous_state, TransitionState.DRAFT.value)
        self.assertEqual(transition.new_state, TransitionState.PENDING.value)
    
    def test_generate_transition_not_allowed(self):
        """generate_transition returns None for disallowed transitions."""
        transition = self.engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.APPROVED.value,  # Not directly allowed
            trigger=TransitionTrigger.APPROVED.value,
        )
        
        self.assertIsNone(transition)
    
    def test_generate_rollback(self):
        """generate_rollback creates valid rollbacks."""
        # First create a transition
        transition = self.engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_1",
            from_state=TransitionState.APPROVED.value,
            to_state=TransitionState.EXECUTED.value,
            trigger=TransitionTrigger.EXECUTED.value,
        )
        
        rollback = self.engine.generate_rollback(
            transition_id=transition.transition_id,
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.APPROVED.value,
            rollback_reason="execution_failed",
        )
        
        self.assertIsNotNone(rollback)
        self.assertEqual(rollback.original_state, TransitionState.EXECUTED.value)
    
    def test_to_dict(self):
        """to_dict returns expected structure."""
        # Create a fresh engine for this test
        engine = StateTransitionEngine(in_memory=True)
        
        # Create some transitions (only using allowed transitions)
        t1 = engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        self.assertIsNotNone(t1, "First transition should be created")
        
        t2 = engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_2",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.DENIED.value,
            trigger=TransitionTrigger.DENIED.value,
        )
        self.assertIsNotNone(t2, "Second transition should be created")
        
        result = engine.to_dict()
        self.assertEqual(result["transition_count"], 2, f"Expected 2 transitions, got {result['transition_count']}. Created: {t1 and t2}")
        self.assertEqual(result["allowed_transition_count"], 7)  # Default allowed transitions
        self.assertEqual(result["rollback_count"], 0)


class TestIntegrationHooks(TestCase):
    """Test integration hooks with StateTransitionEngine."""
    
    def test_integrate_with_change_proposals(self):
        """integrate_with_change_proposals adds transition context."""
        engine = StateTransitionEngine()
        
        proposal_dict = {"existing_field": "value"}
        result = integrate_with_change_proposals(
            proposal_dict,
            engine,
            proposal_id="proposal_1",
            from_state=TransitionState.DRAFT.value,
            to_state=TransitionState.PENDING.value,
            trigger=TransitionTrigger.SUBMITTED.value,
        )
        
        self.assertIn("transition_context", result)
        self.assertIsNotNone(result["transition_context"])
        self.assertEqual(result["transition_context"]["transition_generated"], True)
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds transition context."""
        engine = StateTransitionEngine()
        
        proof_dict = {"existing_field": "value"}
        result = integrate_with_proof_gate(
            proof_dict,
            engine,
            proof_id="proof_1",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
        )
        
        self.assertIn("transition_context", result)
        self.assertIsNotNone(result["transition_context"])
        self.assertEqual(result["transition_context"]["transition_generated"], True)
    
    def test_integrate_with_escalation(self):
        """integrate_with_escalation adds transition context."""
        engine = StateTransitionEngine()
        
        escalation_dict = {"existing_field": "value"}
        result = integrate_with_escalation(
            escalation_dict,
            engine,
            escalation_id="escalation_1",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
        )
        
        self.assertIn("transition_context", result)
        self.assertIsNotNone(result["transition_context"])
        self.assertEqual(result["transition_context"]["transition_generated"], True)
    
    def test_integrate_with_outcome_feedback(self):
        """integrate_with_outcome_feedback adds transition context."""
        engine = StateTransitionEngine()
        
        feedback_dict = {"existing_field": "value"}
        result = integrate_with_outcome_feedback(
            feedback_dict,
            engine,
            feedback_id="feedback_1",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
        )
        
        self.assertIn("transition_context", result)
        self.assertIsNotNone(result["transition_context"])
        self.assertEqual(result["transition_context"]["transition_generated"], True)
    
    def test_integrate_with_recovery_layer(self):
        """integrate_with_recovery_layer adds transition context."""
        engine = StateTransitionEngine()
        
        recovery_dict = {"existing_field": "value"}
        result = integrate_with_recovery_layer(
            recovery_dict,
            engine,
            recovery_id="recovery_1",
            from_state=TransitionState.PENDING.value,
            to_state=TransitionState.APPROVED.value,
            trigger=TransitionTrigger.APPROVED.value,
        )
        
        self.assertIn("transition_context", result)
        self.assertIsNotNone(result["transition_context"])
        self.assertEqual(result["transition_context"]["transition_generated"], True)


class TestRollbackBehavior(TestCase):
    """Test rollback transition behavior."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = StateTransitionEngine()
    
    def test_rollback_records_all_needed_data(self):
        """Rollback records all needed data for audit."""
        transition = self.engine.generate_transition(
            object_type="change_proposal",
            object_id="proposal_1",
            from_state=TransitionState.APPROVED.value,
            to_state=TransitionState.EXECUTED.value,
            trigger=TransitionTrigger.EXECUTED.value,
        )
        
        rollback = self.engine.generate_rollback(
            transition_id=transition.transition_id,
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.APPROVED.value,
            rollback_reason="execution_failed",
        )
        
        self.assertIsNotNone(rollback)
        self.assertEqual(rollback.transition_id, transition.transition_id)
        self.assertTrue(rollback.completed)
    
    def test_rollback_with_failure(self):
        """Rollback can record failure state."""
        rollback = RollbackTransition(
            rollback_id="rollback_1",
            transition_id="transition_1",
            original_state=TransitionState.EXECUTED.value,
            rollback_to_state=TransitionState.APPROVED.value,
            rollback_reason="execution_failed",
            completed=False,
            failed_at="2026-04-06T19:45:00Z",
            failure_reason="Database lock timeout",
        )
        
        self.assertFalse(rollback.completed)
        self.assertIsNotNone(rollback.failed_at)
        self.assertIsNotNone(rollback.failure_reason)
