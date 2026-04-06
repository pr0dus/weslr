# test_simulation.py - WESLR v44: Simulation / Dry-Run Impact Layer Tests
# Focused tests for simulation layer.
# Additive only, transparent, reversible, non-manipulative, no repo drift.

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.simulation import (
    SimulationType,
    ImpactLevel,
    ConfidenceLevel,
    RollbackFeasibility,
    SimulationStatus,
    ImpactProjection,
    SimulationResult,
    DryRunSummary,
    SimulationEngine,
    integrate_with_governance_surface,
    integrate_with_proof_gate,
    integrate_with_multi_timescale_planning,
    integrate_with_outcome_feedback,
)


class TestSimulationTypeEnum(TestCase):
    """Test simulation type enum values."""
    
    def test_all_simulation_types_present(self):
        """All expected simulation types are defined."""
        expected_types = [
            "proposal_impact",
            "recommendation_implications",
            "action_consequences",
            "state_transition",
            "risk_exposure",
            "trust_dynamics",
        ]
        
        for sim_type in expected_types:
            self.assertIn(sim_type, [t.value for t in SimulationType])
    
    def test_simulation_types_are_strings(self):
        """All simulation type values are strings."""
        for sim_type in SimulationType:
            self.assertIsInstance(sim_type.value, str)


class TestImpactLevelEnum(TestCase):
    """Test impact level enum values."""
    
    def test_all_impact_levels_present(self):
        """All expected impact levels are defined."""
        expected_levels = [
            "none",
            "minimal",
            "moderate",
            "significant",
            "critical",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [l.value for l in ImpactLevel])
    
    def test_impact_levels_are_strings(self):
        """All impact level values are strings."""
        for level in ImpactLevel:
            self.assertIsInstance(level.value, str)


class TestConfidenceLevelEnum(TestCase):
    """Test confidence level enum values."""
    
    def test_all_confidence_levels_present(self):
        """All expected confidence levels are defined."""
        expected_levels = [
            "low",
            "medium",
            "high",
            "very_high",
        ]
        
        for level in expected_levels:
            self.assertIn(level, [l.value for l in ConfidenceLevel])
    
    def test_confidence_levels_are_strings(self):
        """All confidence level values are strings."""
        for level in ConfidenceLevel:
            self.assertIsInstance(level.value, str)


class TestRollbackFeasibilityEnum(TestCase):
    """Test rollback feasibility enum values."""
    
    def test_all_rollback_feasibilities_present(self):
        """All expected rollback feasibilities are defined."""
        expected_feasibilities = [
            "easy",
            "moderate",
            "difficult",
            "impossible",
        ]
        
        for feasibility in expected_feasibilities:
            self.assertIn(feasibility, [f.value for f in RollbackFeasibility])
    
    def test_rollback_feasibilities_are_strings(self):
        """All rollback feasibility values are strings."""
        for feasibility in RollbackFeasibility:
            self.assertIsInstance(feasibility.value, str)


class TestSimulationStatusEnum(TestCase):
    """Test simulation status enum values."""
    
    def test_all_simulation_statuses_present(self):
        """All expected simulation statuses are defined."""
        expected_statuses = [
            "pending",
            "running",
            "complete",
            "partial",
            "failed",
        ]
        
        for status in expected_statuses:
            self.assertIn(status, [s.value for s in SimulationStatus])
    
    def test_simulation_statuses_are_strings(self):
        """All simulation status values are strings."""
        for status in SimulationStatus:
            self.assertIsInstance(status.value, str)


class TestImpactProjection(TestCase):
    """Test ImpactProjection data class."""
    
    def test_projection_creation(self):
        """Projection creation works correctly."""
        projection = ImpactProjection(
            impact_id="impact_test_123",
            category=ImpactLevel.MODERATE.value,
            magnitude=0.6,
            scope=["subsystem_a", "subsystem_b"],
            expected_change={"risk": "increased", "trust": "decreased"},
            confidence=0.7,
        )
        
        self.assertEqual(projection.impact_id, "impact_test_123")
        self.assertEqual(projection.category, ImpactLevel.MODERATE.value)
        self.assertEqual(projection.magnitude, 0.6)
        self.assertEqual(len(projection.scope), 2)
        self.assertEqual(projection.confidence, 0.7)
    
    def test_to_dict(self):
        """Projection to_dict conversion works."""
        projection = ImpactProjection(
            impact_id="impact_test",
            category=ImpactLevel.MINIMAL.value,
            magnitude=0.2,
        )
        
        result = projection.to_dict()
        
        self.assertEqual(result["impact_id"], "impact_test")
        self.assertEqual(result["category"], ImpactLevel.MINIMAL.value)
        self.assertIn("created_at", result)
    
    def test_from_dict(self):
        """Projection from_dict reconstruction works."""
        original = ImpactProjection(
            impact_id="impact_test",
            category=ImpactLevel.MODERATE.value,
            magnitude=0.5,
            confidence=0.8,
        )
        
        data = original.to_dict()
        recreated = ImpactProjection.from_dict(data)
        
        self.assertEqual(recreated.impact_id, original.impact_id)
        self.assertEqual(recreated.category, original.category)
        self.assertEqual(recreated.magnitude, original.magnitude)


class TestSimulationResult(TestCase):
    """Test SimulationResult data class."""
    
    def test_simulation_creation(self):
        """Simulation creation works correctly."""
        simulation = SimulationResult(
            simulation_id="sim_test_123",
            simulation_type=SimulationType.PROPOSAL_IMPACT.value,
            action="execute",
            context="context_456",
            risk_delta=0.3,
            trust_delta=-0.2,
            escalation_probability=0.5,
        )
        
        self.assertEqual(simulation.simulation_id, "sim_test_123")
        self.assertEqual(simulation.simulation_type, SimulationType.PROPOSAL_IMPACT.value)
        self.assertEqual(simulation.action, "execute")
        self.assertEqual(simulation.context, "context_456")
        self.assertEqual(simulation.risk_delta, 0.3)
        self.assertEqual(simulation.trust_delta, -0.2)
        self.assertEqual(simulation.escalation_probability, 0.5)
    
    def test_simulation_with_explanation(self):
        """Simulation creation with explanation works."""
        simulation = SimulationResult(
            simulation_id="sim_test_789",
            simulation_type=SimulationType.RECOMMENDATION_IMPLICATIONS.value,
            action="recommend",
            explanation="This action increases risk by 30% but improves trust by 20%",
            assumptions=["User has sufficient privileges", "Network is stable"],
        )
        
        self.assertIsNotNone(simulation.explanation)
        self.assertEqual(len(simulation.assumptions), 2)
    
    def test_to_dict(self):
        """Simulation to_dict conversion works."""
        simulation = SimulationResult(
            simulation_id="sim_test",
            simulation_type=SimulationType.PROPOSAL_IMPACT.value,
            action="execute",
        )
        
        result = simulation.to_dict()
        
        self.assertEqual(result["simulation_id"], "sim_test")
        self.assertEqual(result["simulation_type"], SimulationType.PROPOSAL_IMPACT.value)
        self.assertIn("created_at", result)
        self.assertIn("status", result)
    
    def test_from_dict(self):
        """Simulation from_dict reconstruction works."""
        original = SimulationResult(
            simulation_id="sim_test",
            simulation_type=SimulationType.PROPOSAL_IMPACT.value,
            action="execute",
            risk_delta=0.4,
            confidence_level=ConfidenceLevel.HIGH.value,
        )
        
        data = original.to_dict()
        recreated = SimulationResult.from_dict(data)
        
        self.assertEqual(recreated.simulation_id, original.simulation_id)
        self.assertEqual(recreated.simulation_type, original.simulation_type)
        self.assertEqual(recreated.risk_delta, original.risk_delta)


class TestDryRunSummary(TestCase):
    """Test DryRunSummary data class."""
    
    def test_summary_creation(self):
        """Summary creation works correctly."""
        summary = DryRunSummary(
            summary_id="summary_test_123",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
            aggregate_risk_delta=0.5,
            aggregate_trust_delta=-0.3,
            aggregate_escalation_probability=0.6,
        )
        
        self.assertEqual(summary.summary_id, "summary_test_123")
        self.assertEqual(summary.affected_object_id, "proposal_456")
        self.assertEqual(summary.affected_object_type, "proposal")
        self.assertEqual(summary.aggregate_risk_delta, 0.5)
        self.assertEqual(summary.aggregate_trust_delta, -0.3)
        self.assertEqual(summary.aggregate_escalation_probability, 0.6)
    
    def test_to_dict(self):
        """Summary to_dict conversion works."""
        summary = DryRunSummary(
            summary_id="summary_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
        )
        
        result = summary.to_dict()
        
        self.assertEqual(result["summary_id"], "summary_test")
        self.assertEqual(result["affected_object_id"], "proposal_456")
        self.assertEqual(result["simulation_count"], 0)
        self.assertIn("simulations", result)
    
    def test_from_dict(self):
        """Summary from_dict reconstruction works."""
        original = DryRunSummary(
            summary_id="summary_test",
            affected_object_id="proposal_456",
            affected_object_type="proposal",
            aggregate_risk_delta=0.4,
        )
        
        data = original.to_dict()
        recreated = DryRunSummary.from_dict(data)
        
        self.assertEqual(recreated.summary_id, original.summary_id)
        self.assertEqual(recreated.affected_object_id, original.affected_object_id)


class TestSimulationEngine(TestCase):
    """Test SimulationEngine class."""
    
    def test_engine_initialization(self):
        """Engine initialization works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            self.assertEqual(len(engine.simulations), 0)
            self.assertEqual(len(engine.dry_runs), 0)
    
    def test_create_simulation(self):
        """Engine create_simulation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            simulation = engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
                context="context_123",
            )
            
            self.assertIsNotNone(simulation)
            self.assertEqual(simulation.simulation_id, "sim_test")
            self.assertEqual(simulation.action, "execute")
    
    def test_run_simulation(self):
        """Engine run_simulation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            
            simulation = engine.run_simulation(
                simulation_id="sim_test",
                expected_impact=[{"category": "moderate", "magnitude": 0.5}],
                risk_delta=0.3,
                trust_delta=-0.2,
                escalation_probability=0.5,
                explanation="This action has moderate risk",
                assumptions=["System is healthy"],
            )
            
            self.assertEqual(simulation.status, SimulationStatus.COMPLETE.value)
            self.assertEqual(len(simulation.expected_impact), 1)
    
    def test_get_simulation(self):
        """Engine get_simulation works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            simulation = engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            retrieved = engine.get_simulation("sim_test")
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.simulation_id, simulation.simulation_id)
    
    def test_create_dry_run_summary(self):
        """Engine create_dry_run_summary works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            engine.create_simulation(
                simulation_id="sim_1",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.create_simulation(
                simulation_id="sim_2",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            
            # Run both simulations
            engine.run_simulation(
                simulation_id="sim_1",
                risk_delta=0.3,
                trust_delta=-0.2,
                escalation_probability=0.5,
            )
            engine.run_simulation(
                simulation_id="sim_2",
                risk_delta=0.2,
                trust_delta=-0.1,
                escalation_probability=0.4,
            )
            
            summary = engine.create_dry_run_summary(
                summary_id="summary_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                simulations=["sim_1", "sim_2"],
            )
            
            self.assertIsNotNone(summary)
            self.assertEqual(len(summary.simulations), 2)
            self.assertAlmostEqual(summary.aggregate_risk_delta, 0.5, places=1)
    
    def test_get_dry_run(self):
        """Engine get_dry_run works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.run_simulation(
                simulation_id="sim_test",
                risk_delta=0.3,
            )
            
            summary = engine.create_dry_run_summary(
                summary_id="summary_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                simulations=["sim_test"],
            )
            
            retrieved = engine.get_dry_run("summary_test")
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.summary_id, summary.summary_id)
    
    def test_to_dict(self):
        """Engine to_dict conversion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.create_dry_run_summary(
                summary_id="summary_test",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                simulations=[],
            )
            
            result = engine.to_dict()
            
            self.assertEqual(result["simulation_count"], 1)
            self.assertEqual(result["dry_run_count"], 1)
            self.assertIn("simulations", result)
            self.assertIn("dry_runs", result)


class TestIntegrationHooks(TestCase):
    """Test integration hook functions."""
    
    def test_integrate_with_governance_surface(self):
        """integrate_with_governance_surface adds dry-run context."""
        governance_dict = {"governance_id": "test_governance"}
        
        result = integrate_with_governance_surface(governance_dict)
        
        self.assertIn("dry_run_context", result)
        self.assertIsNone(result["dry_run_context"])
    
    def test_integrate_with_governance_surface_with_engine(self):
        """integrate_with_governance_surface works with simulation engine."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            affected_id = "integration_object"
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.run_simulation(
                simulation_id="sim_test",
                risk_delta=0.3,
                trust_delta=-0.2,
                escalation_probability=0.5,
            )
            
            # Create dry-run with consistent naming
            summary = engine.create_dry_run_summary(
                summary_id=f"dry_run_{affected_id}",
                affected_object_id=affected_id,
                affected_object_type="proposal",
                simulations=["sim_test"],
            )
            
            governance_dict = {"governance_id": "test_governance"}
            
            result = integrate_with_governance_surface(
                governance_dict,
                simulation_engine=engine,
                affected_object_id=affected_id,
            )
            
            self.assertIn("dry_run_context", result)
            self.assertIsNotNone(result["dry_run_context"])
    
    def test_integrate_with_proof_gate(self):
        """integrate_with_proof_gate adds dry-run context."""
        proof_dict = {"proof_type": "validation"}
        
        result = integrate_with_proof_gate(proof_dict)
        
        self.assertIn("dry_run_context", result)
        self.assertIsNone(result["dry_run_context"])
    
    def test_integrate_with_multi_timescale_planning(self):
        """integrate_with_multi_timescale_planning adds dry-run context."""
        planning_dict = {"planning_id": "test_planning"}
        
        result = integrate_with_multi_timescale_planning(planning_dict)
        
        self.assertIn("dry_run_context", result)
        self.assertIsNone(result["dry_run_context"])
    
    def test_integrate_with_outcome_feedback(self):
        """integrate_with_outcome_feedback adds dry-run context."""
        feedback_dict = {"feedback_id": "test_feedback"}
        
        result = integrate_with_outcome_feedback(feedback_dict)
        
        self.assertIn("dry_run_context", result)
        self.assertIsNone(result["dry_run_context"])


class TestSimulationFlow(TestCase):
    """Test complete simulation flow."""
    
    def test_complete_simulation_flow(self):
        """Complete simulation flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            # Create simulation
            simulation = engine.create_simulation(
                simulation_id="sim_proposal_456",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
                context="context_456",
            )
            
            # Run simulation
            simulation = engine.run_simulation(
                simulation_id="sim_proposal_456",
                expected_impact=[{"category": "moderate", "magnitude": 0.5}],
                risk_delta=0.3,
                trust_delta=-0.2,
                escalation_probability=0.5,
                explanation="This action has moderate risk but improves efficiency",
                assumptions=["System is healthy", "User has sufficient privileges"],
            )
            
            self.assertEqual(simulation.status, SimulationStatus.COMPLETE.value)
            self.assertEqual(simulation.escalation_probability, 0.5)
    
    def test_complete_dry_run_flow(self):
        """Complete dry-run flow works end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            # Create and run simulation
            engine.create_simulation(
                simulation_id="sim_proposal_456",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.run_simulation(
                simulation_id="sim_proposal_456",
                risk_delta=0.3,
                trust_delta=-0.2,
                escalation_probability=0.5,
            )
            
            # Create dry-run summary
            summary = engine.create_dry_run_summary(
                summary_id="summary_proposal_456",
                affected_object_id="proposal_456",
                affected_object_type="proposal",
                simulations=["sim_proposal_456"],
            )
            
            self.assertIsNotNone(summary)
            self.assertEqual(summary.aggregate_risk_delta, 0.3)


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility with existing code."""
    
    def test_existing_code_works_without_dry_run_context(self):
        """Existing code works when dry-run context not provided."""
        # Integration hooks should work without simulation engine
        governance_result = integrate_with_governance_surface({"test": "data"})
        self.assertEqual(governance_result["test"], "data")
        
        proof_result = integrate_with_proof_gate({"test": "data"})
        self.assertEqual(proof_result["test"], "data")
        
        planning_result = integrate_with_multi_timescale_planning({"test": "data"})
        self.assertEqual(planning_result["test"], "data")
        
        feedback_result = integrate_with_outcome_feedback({"test": "data"})
        self.assertEqual(feedback_result["test"], "data")
    
    def test_engine_without_context(self):
        """Engine works without context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            # Create simulation without context
            simulation = engine.create_simulation(
                simulation_id="no_context_sim",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            
            self.assertIsNotNone(simulation)
            self.assertIsNone(simulation.context)
    
    def test_simulation_without_optional_fields(self):
        """Simulation creation works without optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            simulation = engine.create_simulation(
                simulation_id="minimal_sim",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            
            self.assertIsNotNone(simulation)
            self.assertIsNone(simulation.explanation)
            self.assertEqual(len(simulation.assumptions), 0)


class TestSerialization(TestCase):
    """Test serialization and deserialization."""
    
    def test_projection_serialization(self):
        """Projection serialization round-trip works."""
        original = ImpactProjection(
            impact_id="serial_test",
            category=ImpactLevel.MODERATE.value,
            magnitude=0.5,
            confidence=0.8,
        )
        
        data = original.to_dict()
        recreated = ImpactProjection.from_dict(data)
        
        self.assertEqual(original.impact_id, recreated.impact_id)
        self.assertEqual(original.category, recreated.category)
        self.assertEqual(original.magnitude, recreated.magnitude)
    
    def test_simulation_serialization(self):
        """Simulation serialization round-trip works."""
        original = SimulationResult(
            simulation_id="serial_test",
            simulation_type=SimulationType.PROPOSAL_IMPACT.value,
            action="execute",
            risk_delta=0.3,
            confidence_level=ConfidenceLevel.HIGH.value,
        )
        
        data = original.to_dict()
        recreated = SimulationResult.from_dict(data)
        
        self.assertEqual(original.simulation_id, recreated.simulation_id)
        self.assertEqual(original.simulation_type, recreated.simulation_type)
        self.assertEqual(original.risk_delta, recreated.risk_delta)
    
    def test_summary_serialization(self):
        """Summary serialization round-trip works."""
        original = DryRunSummary(
            summary_id="serial_test",
            affected_object_id="object_1",
            affected_object_type="proposal",
            aggregate_risk_delta=0.4,
        )
        
        data = original.to_dict()
        recreated = DryRunSummary.from_dict(data)
        
        self.assertEqual(original.summary_id, recreated.summary_id)
        self.assertEqual(original.affected_object_id, recreated.affected_object_id)


class TestIntegrationWithExistingLayers(TestCase):
    """Test integration with existing WESLR layers."""
    
    def test_integration_with_governance_surface(self):
        """Integration with governance surface works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            affected_id = "governance_object"
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.run_simulation(
                simulation_id="sim_test",
                risk_delta=0.3,
            )
            
            # Create dry-run with consistent naming
            engine.create_dry_run_summary(
                summary_id=f"dry_run_{affected_id}",
                affected_object_id=affected_id,
                affected_object_type="proposal",
                simulations=["sim_test"],
            )
            
            governance_dict = {
                "governance_id": "governance_test",
                "object_id": "governance_object",
            }
            
            result = integrate_with_governance_surface(
                governance_dict,
                simulation_engine=engine,
                affected_object_id=affected_id,
            )
            
            self.assertIn("dry_run_context", result)
            self.assertIsNotNone(result["dry_run_context"])
    
    def test_integration_with_proof_gate(self):
        """Integration with proof gate works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = SimulationEngine(storage_path=tmpdir)
            
            engine.create_simulation(
                simulation_id="sim_test",
                simulation_type=SimulationType.PROPOSAL_IMPACT.value,
                action="execute",
            )
            engine.run_simulation(
                simulation_id="sim_test",
                risk_delta=0.3,
                escalation_probability=0.5,
            )
            
            proof_dict = {
                "proof_id": "proof_test",
                "simulation_id": "sim_test",
            }
            
            result = integrate_with_proof_gate(
                proof_dict,
                simulation_engine=engine,
                simulation_id="sim_test",
            )
            
            self.assertIn("dry_run_context", result)
            self.assertIsNotNone(result["dry_run_context"])


if __name__ == "__main__":
    import unittest
    unittest.main()
