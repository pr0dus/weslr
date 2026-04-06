# test_constraint_invariant.py - WESLR v45: Constraint / Invariant Layer Tests
# Focused tests for constraint/invariant layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.constraint_invariant import (
    ConstraintType,
    InvariantType,
    ViolationSeverity,
    InvariantHoldBackCondition,
    ExplanationType,
    HardConstraint,
    ProtectedBaseline,
    TrustInvariant,
    InvariantViolation,
    ExplanationForBlock,
    ConstraintInvariantEngine,
    integrate_with_simulation,
    integrate_with_proof_gate,
    integrate_with_tension_resolution,
    integrate_with_goal_hierarchy,
    integrate_with_capability_boundary,
)


class TestConstraintTypeEnum(TestCase):
    """Test constraint type enum values."""
    
    def test_all_constraint_types_present(self):
        """All expected constraint types are defined."""
        expected_types = [
            "ethical",
            "legal",
            "security",
            "privacy",
            "trust",
            "operational",
            "reputation",
            "domain",
        ]
        
        for constraint_type in expected_types:
            self.assertIn(constraint_type, [t.value for t in ConstraintType])
    
    def test_constraint_types_are_strings(self):
        """All constraint type values are strings."""
        for constraint_type in ConstraintType:
            self.assertIsInstance(constraint_type.value, str)


class TestInvariantTypeEnum(TestCase):
    """Test invariant type enum values."""
    
    def test_all_invariant_types_present(self):
        """All expected invariant types are defined."""
        expected_types = [
            "logical",
            "causal",
            "temporal",
            "quantitative",
            "role",
        ]
        
        for invariant_type in expected_types:
            self.assertIn(invariant_type, [t.value for t in InvariantType])
    
    def test_invariant_types_are_strings(self):
        """All invariant type values are strings."""
        for invariant_type in InvariantType:
            self.assertIsInstance(invariant_type.value, str)


class TestViolationSeverityEnum(TestCase):
    """Test violation severity enum values."""
    
    def test_all_violation_severities_present(self):
        """All expected violation severities are defined."""
        expected_severities = [
            "low",
            "medium",
            "high",
            "critical",
        ]
        
        for severity in expected_severities:
            self.assertIn(severity, [s.value for s in ViolationSeverity])
    
    def test_violation_severities_are_strings(self):
        """All violation severity values are strings."""
        for severity in ViolationSeverity:
            self.assertIsInstance(severity.value, str)


class TestInvariantHoldBackConditionEnum(TestCase):
    """Test invariant hold-back condition enum values."""
    
    def test_all_hold_back_conditions_present(self):
        """All expected hold-back conditions are defined."""
        expected_conditions = [
            "always",
            "conditional",
            "gradual",
            "emergency_override",
        ]
        
        for condition in expected_conditions:
            self.assertIn(condition, [c.value for c in InvariantHoldBackCondition])
    
    def test_hold_back_conditions_are_strings(self):
        """All hold-back condition values are strings."""
        for condition in InvariantHoldBackCondition:
            self.assertIsInstance(condition.value, str)


class TestExplanationTypeEnum(TestCase):
    """Test explanation type enum values."""
    
    def test_all_explanation_types_present(self):
        """All expected explanation types are defined."""
        expected_types = [
            "description",
            "alternatives",
            "mitigations",
            "emergency",
        ]
        
        for explanation_type in expected_types:
            self.assertIn(explanation_type, [t.value for t in ExplanationType])
    
    def test_explanation_types_are_strings(self):
        """All explanation type values are strings."""
        for explanation_type in ExplanationType:
            self.assertIsInstance(explanation_type.value, str)


class TestHardConstraint(TestCase):
    """Test HardConstraint data model."""
    
    def test_hard_constraint_creation(self):
        """HardConstraint can be created and serialized."""
        constraint = HardConstraint(
            constraint_id="test_constraint_1",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Test ethical constraint",
            applies_to=["action_1", "action_2"],
        )
        
        self.assertEqual(constraint.constraint_id, "test_constraint_1")
        self.assertEqual(constraint.constraint_type, ConstraintType.ETHICAL.value)
        self.assertTrue(constraint.automatic_block)
        self.assertTrue(constraint.enabled)
        
        # Test serialization
        data = constraint.to_dict()
        self.assertEqual(data["constraint_id"], "test_constraint_1")
        self.assertEqual(data["constraint_type"], ConstraintType.ETHICAL.value)
        
        # Test deserialization
        constraint2 = HardConstraint.from_dict(data)
        self.assertEqual(constraint2.constraint_id, constraint.constraint_id)
    
    def test_hard_constraint_disabled(self):
        """HardConstraint can be disabled."""
        constraint = HardConstraint(
            constraint_id="test_constraint_2",
            constraint_type=ConstraintType.LEGAL.value,
            description="Test legal constraint",
            enabled=False,
        )
        self.assertFalse(constraint.enabled)


class TestProtectedBaseline(TestCase):
    """Test ProtectedBaseline data model."""
    
    def test_protected_baseline_creation(self):
        """ProtectedBaseline can be created and serialized."""
        baseline = ProtectedBaseline(
            baseline_id="test_baseline_1",
            baseline_type=InvariantType.QUANTITATIVE.value,
            description="Test trust baseline",
            min_threshold=0.0,
            max_threshold=1.0,
            target_value=0.8,
        )
        
        self.assertEqual(baseline.baseline_id, "test_baseline_1")
        self.assertEqual(baseline.min_threshold, 0.0)
        self.assertEqual(baseline.max_threshold, 1.0)
        self.assertEqual(baseline.target_value, 0.8)
        
        # Test serialization
        data = baseline.to_dict()
        self.assertEqual(data["baseline_id"], "test_baseline_1")
        
        # Test deserialization
        baseline2 = ProtectedBaseline.from_dict(data)
        self.assertEqual(baseline2.baseline_id, baseline.baseline_id)


class TestTrustInvariant(TestCase):
    """Test TrustInvariant data model."""
    
    def test_trust_invariant_creation(self):
        """TrustInvariant can be created and serialized."""
        invariant = TrustInvariant(
            invariant_id="test_invariant_1",
            invariant_type=InvariantType.CAUSAL.value,
            description="Test trust invariant",
            trust_type="relationship",
            criticality="high",
            hold_back_condition=InvariantHoldBackCondition.ALWAYS.value,
        )
        
        self.assertEqual(invariant.invariant_id, "test_invariant_1")
        self.assertEqual(invariant.trust_type, "relationship")
        self.assertEqual(invariant.criticality, "high")
        self.assertEqual(invariant.hold_back_condition, InvariantHoldBackCondition.ALWAYS.value)
        
        # Test serialization
        data = invariant.to_dict()
        self.assertEqual(data["invariant_id"], "test_invariant_1")


class TestInvariantViolation(TestCase):
    """Test InvariantViolation data model."""
    
    def test_violation_creation(self):
        """InvariantViolation can be created and serialized."""
        violation = InvariantViolation(
            violation_id="violation_1",
            violated_constraint_id="constraint_1",
            violated_constraint_type="HardConstraint",
            context="Test context",
            detected_severity=ViolationSeverity.HIGH.value,
            automatic_blocked=True,
        )
        
        self.assertEqual(violation.violation_id, "violation_1")
        self.assertEqual(violation.violated_constraint_type, "HardConstraint")
        self.assertTrue(violation.automatic_blocked)
        self.assertFalse(violation.resolved)
        
        # Test serialization
        data = violation.to_dict()
        self.assertEqual(data["violation_id"], "violation_1")
        
        # Test deserialization
        violation2 = InvariantViolation.from_dict(data)
        self.assertEqual(violation2.violation_id, violation.violation_id)


class TestExplanationForBlock(TestCase):
    """Test ExplanationForBlock data model."""
    
    def test_explanation_creation(self):
        """ExplanationForBlock can be created and serialized."""
        explanation = ExplanationForBlock(
            explanation_id="explanation_1",
            blocked_action="test_action",
            violated_invariant_id="invariant_1",
            explanation_type=ExplanationType.DESCRIPTION.value,
            explanation_text="Action was blocked due to constraint violation.",
            alternatives=["alternative_1", "alternative_2"],
        )
        
        self.assertEqual(explanation.explanation_id, "explanation_1")
        self.assertEqual(explanation.blocked_action, "test_action")
        self.assertEqual(len(explanation.alternatives), 2)
        
        # Test serialization
        data = explanation.to_dict()
        self.assertEqual(data["explanation_id"], "explanation_1")
        
        # Test deserialization
        explanation2 = ExplanationForBlock.from_dict(data)
        self.assertEqual(explanation2.explanation_id, explanation.explanation_id)


class TestConstraintInvariantEngine(TestCase):
    """Test ConstraintInvariantEngine."""
    
    def setUp(self):
        """Set up test engine with temp storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = ConstraintInvariantEngine(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_add_constraint(self):
        """Add constraint works."""
        constraint = HardConstraint(
            constraint_id="constraint_1",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Test constraint",
        )
        
        self.engine.add_constraint(constraint)
        retrieved = self.engine.get_constraint("constraint_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.description, "Test constraint")
    
    def test_add_baseline(self):
        """Add baseline works."""
        baseline = ProtectedBaseline(
            baseline_id="baseline_1",
            baseline_type=InvariantType.QUANTITATIVE.value,
            description="Test baseline",
        )
        
        self.engine.add_baseline(baseline)
        retrieved = self.engine.get_baseline("baseline_1")
        self.assertIsNotNone(retrieved)
    
    def test_add_invariant(self):
        """Add invariant works."""
        invariant = TrustInvariant(
            invariant_id="invariant_1",
            invariant_type=InvariantType.CAUSAL.value,
            description="Test invariant",
        )
        
        self.engine.add_invariant(invariant)
        retrieved = self.engine.get_invariant("invariant_1")
        self.assertIsNotNone(retrieved)
    
    def test_get_all_constraints_enabled(self):
        """Get all constraints filters by enabled."""
        constraint_enabled = HardConstraint(
            constraint_id="constraint_enabled",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Enabled constraint",
            enabled=True,
        )
        constraint_disabled = HardConstraint(
            constraint_id="constraint_disabled",
            constraint_type=ConstraintType.LEGAL.value,
            description="Disabled constraint",
            enabled=False,
        )
        
        self.engine.add_constraint(constraint_enabled)
        self.engine.add_constraint(constraint_disabled)
        
        all_constraints = self.engine.get_all_constraints()
        self.assertEqual(len(all_constraints), 1)
        self.assertEqual(all_constraints[0].constraint_id, "constraint_enabled")
    
    def test_get_all_baselines_enabled(self):
        """Get all baselines filters by enabled."""
        baseline_enabled = ProtectedBaseline(
            baseline_id="baseline_enabled",
            baseline_type=InvariantType.QUANTITATIVE.value,
            description="Enabled baseline",
            enabled=True,
        )
        baseline_disabled = ProtectedBaseline(
            baseline_id="baseline_disabled",
            baseline_type=InvariantType.CAUSAL.value,
            description="Disabled baseline",
            enabled=False,
        )
        
        self.engine.add_baseline(baseline_enabled)
        self.engine.add_baseline(baseline_disabled)
        
        all_baselines = self.engine.get_all_baselines()
        self.assertEqual(len(all_baselines), 1)
        self.assertEqual(all_baselines[0].baseline_id, "baseline_enabled")
    
    def test_get_all_invariants_enabled(self):
        """Get all invariants filters by enabled."""
        invariant_enabled = TrustInvariant(
            invariant_id="invariant_enabled",
            invariant_type=InvariantType.CAUSAL.value,
            description="Enabled invariant",
            enabled=True,
        )
        invariant_disabled = TrustInvariant(
            invariant_id="invariant_disabled",
            invariant_type=InvariantType.QUANTITATIVE.value,
            description="Disabled invariant",
            enabled=False,
        )
        
        self.engine.add_invariant(invariant_enabled)
        self.engine.add_invariant(invariant_disabled)
        
        all_invariants = self.engine.get_all_invariants()
        self.assertEqual(len(all_invariants), 1)
        self.assertEqual(all_invariants[0].invariant_id, "invariant_enabled")
    
    def test_to_dict(self):
        """to_dict returns expected structure."""
        self.engine.add_constraint(HardConstraint(
            constraint_id="c1",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Constraint",
        ))
        self.engine.add_baseline(ProtectedBaseline(
            baseline_id="b1",
            baseline_type=InvariantType.QUANTITATIVE.value,
            description="Baseline",
        ))
        self.engine.add_invariant(TrustInvariant(
            invariant_id="i1",
            invariant_type=InvariantType.CAUSAL.value,
            description="Invariant",
        ))
        
        result = self.engine.to_dict()
        self.assertEqual(result["constraint_count"], 1)
        self.assertEqual(result["baseline_count"], 1)
        self.assertEqual(result["invariant_count"], 1)
    
    def test_record_and_resolve_violation(self):
        """Record and resolve violation works."""
        violation = InvariantViolation(
            violation_id="v1",
            violated_constraint_id="c1",
            violated_constraint_type="HardConstraint",
            timestamp="2026-04-06T19:17:00Z",
            context="Test context",
        )
        
        self.engine.record_violation(violation)
        retrieved = self.engine.get_violation("v1")
        self.assertIsNotNone(retrieved)
        
        # Resolve
        result = self.engine.resolve_violation("v1", "Fixed by operator")
        self.assertTrue(result)
        retrieved = self.engine.get_violation("v1")
        self.assertTrue(retrieved.resolved)
        self.assertEqual(retrieved.resolution_notes, "Fixed by operator")
    
    def test_create_block_explanation(self):
        """Create block explanation works."""
        explanation = ExplanationForBlock(
            explanation_id="exp1",
            blocked_action="test_action",
            violated_invariant_id="inv1",
            explanation_type=ExplanationType.DESCRIPTION.value,
            explanation_text="Action blocked due to constraint.",
        )
        
        self.engine.create_block_explanation(explanation)
        retrieved = self.engine.get_block_explanation("exp1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.explanation_text, "Action blocked due to constraint.")


class TestConstraintViolationDetection(TestCase):
    """Test violation detection in ConstraintInvariantEngine."""
    
    def setUp(self):
        """Set up test engine."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = ConstraintInvariantEngine(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_check_violation_with_constraint(self):
        """check_violation detects constraint violations."""
        constraint = HardConstraint(
            constraint_id="prohibited_action",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Prohibited action",
            applies_to=["prohibited_action"],
            automatic_block=True,
        )
        self.engine.add_constraint(constraint)
        
        # Action that matches constraint applies_to
        violation = self.engine.check_violation("prohibited_action", {"description": "test"})
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violated_constraint_id, "prohibited_action")
        self.assertTrue(violation.automatic_blocked)
    
    def test_check_violation_with_baseline(self):
        """check_violation detects baseline violations."""
        baseline = ProtectedBaseline(
            baseline_id="trust_baseline",
            baseline_type=InvariantType.QUANTITATIVE.value,
            description="Trust baseline",
            min_threshold=0.5,
            automatic_block=True,
        )
        self.engine.add_baseline(baseline)
        
        # Context below min_threshold
        violation = self.engine.check_violation(
            "test_action",
            {"description": "test", "value": 0.3}
        )
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violated_constraint_id, "trust_baseline")
    
    def test_check_violation_no_violation(self):
        """check_violation returns None when no violation."""
        constraint = HardConstraint(
            constraint_id="other_constraint",
            constraint_type=ConstraintType.LEGAL.value,
            description="Other constraint",
            applies_to=["other_action"],
        )
        self.engine.add_constraint(constraint)
        
        # Action that doesn't match
        violation = self.engine.check_violation("test_action", {"description": "test"})
        self.assertIsNone(violation)


class TestIntegrationHooks(TestCase):
    """Test integration hooks with ConstraintInvariantEngine."""
    
    def test_integrate_with_simulation(self):
        """integrate_with_simulation adds constraint context."""
        import tempfile
        
        from weslr.constraint_invariant import ConstraintInvariantEngine, integrate_with_simulation
        
        temp_dir = tempfile.mkdtemp()
        engine = ConstraintInvariantEngine(storage_path=temp_dir)
        engine.add_constraint(HardConstraint(
            constraint_id="test_constraint",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Test",
        ))
        
        sim_dict = {"existing_field": "value"}
        result = integrate_with_simulation(sim_dict, engine, "test_action")
        
        self.assertIn("constraint_context", result)
        self.assertIsNotNone(result["constraint_context"])
        self.assertEqual(result["constraint_context"]["constraints_active"], True)
        self.assertEqual(result["constraint_context"]["constraint_count"], 1)
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds constraint context."""
        from weslr.constraint_invariant import ConstraintInvariantEngine, integrate_with_proof_gate
        
        engine = ConstraintInvariantEngine()
        
        proof_dict = {"existing_field": "value"}
        result = integrate_with_proof_gate(proof_dict, engine, "test_action", {})
        
        self.assertIn("constraint_context", result)
        self.assertIsNotNone(result["constraint_context"])
        self.assertEqual(result["constraint_context"]["violation_detected"], False)
    
    def test_integrate_with_tension_resolution(self):
        """integrate_with_tension_resolution adds constraint context."""
        from weslr.constraint_invariant import ConstraintInvariantEngine, integrate_with_tension_resolution
        
        engine = ConstraintInvariantEngine()
        
        tension_dict = {"existing_field": "value"}
        result = integrate_with_tension_resolution(tension_dict, engine, "test_action")
        
        self.assertIn("constraint_context", result)
        self.assertIsNotNone(result["constraint_context"])
        self.assertEqual(result["constraint_context"]["constraints_override"], False)
    
    def test_integrate_with_goal_hierarchy(self):
        """integrate_with_goal_hierarchy adds constraint context."""
        from weslr.constraint_invariant import ConstraintInvariantEngine, integrate_with_goal_hierarchy
        
        engine = ConstraintInvariantEngine()
        
        goal_dict = {"existing_field": "value"}
        result = integrate_with_goal_hierarchy(goal_dict, engine, "goal_1")
        
        self.assertIn("constraint_context", result)
        self.assertIsNotNone(result["constraint_context"])
        self.assertEqual(result["constraint_context"]["goal_compliant"], True)
    
    def test_integrate_with_capability_boundary(self):
        """integrate_with_capability_boundary adds constraint context."""
        import tempfile
        
        from weslr.constraint_invariant import ConstraintInvariantEngine, integrate_with_capability_boundary
        
        temp_dir = tempfile.mkdtemp()
        engine = ConstraintInvariantEngine(storage_path=temp_dir)
        engine.add_constraint(HardConstraint(
            constraint_id="c1",
            constraint_type=ConstraintType.ETHICAL.value,
            description="Test",
        ))
        
        capability_dict = {"existing_field": "value"}
        result = integrate_with_capability_boundary(capability_dict, engine, "actuate")
        
        self.assertIn("constraint_context", result)
        self.assertIsNotNone(result["constraint_context"])
        self.assertEqual(result["constraint_context"]["constraint_count"], 1)
