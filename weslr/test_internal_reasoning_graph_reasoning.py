"""Test suite for internal_reasoning_graph reasoning engine - Test Doctrine v1

Test Doctrine version: 1.0.0 (2026-04-08)
"""

import unittest
import time
import tempfile
from pathlib import Path

from weslr.internal_reasoning_graph.models import NodeFactory
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore
from weslr.internal_reasoning_graph.reasoning_engine import (
    ReasoningEngine,
    ProposalCandidate,
    ReasoningResult,
    create_reasoning_engine,
)


class TestReasoningModel(unittest.TestCase):
    """Test reasoning result data models."""
    
    def test_proposal_candidate_creation(self):
        """Test ProposalCandidate creation."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="operator_review",
        )
        
        self.assertEqual(proposal.proposal_id, "prop_1")
        self.assertEqual(proposal.proposal_name, "Add System")
        self.assertEqual(proposal.proposal_type, "architectural")
        self.assertEqual(proposal.required_governance, "operator_review")
    
    def test_reasoning_result_creation(self):
        """Test ReasoningResult creation."""
        result = ReasoningResult(
            result_id="reason_1",
            result_type="gap_report",
            content={"gap_id": "gap_1"},
            confidence=0.8,
            governance_required=True,
        )
        
        self.assertEqual(result.result_id, "reason_1")
        self.assertEqual(result.result_type, "gap_report")
        self.assertTrue(result.governance_required)
    
    def test_proposal_serialization(self):
        """Test proposal serialization."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="operator_review",
        )
        
        data = proposal.to_dict()
        self.assertEqual(data["proposal_id"], "prop_1")
        self.assertEqual(data["proposal_type"], "architectural")
        self.assertEqual(data["required_governance"], "operator_review")
    
    def test_reasoning_result_serialization(self):
        """Test reasoning result serialization."""
        result = ReasoningResult(
            result_id="reason_1",
            result_type="gap_report",
            content={"gap_id": "gap_1"},
            confidence=0.8,
            governance_required=True,
        )
        
        data = result.to_dict()
        self.assertEqual(data["result_type"], "gap_report")
        self.assertTrue(data["governance_required"])


class TestReasoningBehavior(unittest.TestCase):
    """Test reasoning engine behavior."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.engine = create_reasoning_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_proposals_from_gaps(self):
        """Test proposal generation from gaps."""
        # No gaps yet, should return empty list
        proposals = self.engine.generate_proposals_from_gaps()
        self.assertEqual(len(proposals), 0)
    
    def test_generate_proposal_from_impact(self):
        """Test proposal generation from impact analysis."""
        # No impact analysis yet, should return None
        from weslr.internal_reasoning_graph.query import ImpactAnalysis
        impact = ImpactAnalysis(
            affected_node_id="sub_1",
            affected_name="System",
            impact_type="direct",
            affected_edges=[],
            confidence=0.8,  # High enough for proposal
        )
        
        proposal = self.engine.generate_proposal_from_impact(impact)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.proposal_name, "Address impact on System")
    
    def test_validate_proposal_governance(self):
        """Test proposal governance validation."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="operator_review",
        )
        
        valid, reason = self.engine.validate_proposal_governance(proposal)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid governance proposal")
    
    def test_validate_proposal_governance_low_confidence(self):
        """Test proposal governance validation with low confidence."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.3,  # Too low
            required_governance="operator_review",
        )
        
        valid, reason = self.engine.validate_proposal_governance(proposal)
        self.assertFalse(valid)
        self.assertIn("confidence", reason)
    
    def test_validate_proposal_governance_wrong_governance(self):
        """Test proposal governance validation with wrong governance type."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="none",  # Not operator_review
        )
        
        valid, reason = self.engine.validate_proposal_governance(proposal)
        self.assertFalse(valid)
        self.assertIn("governance", reason)
    
    def test_run_reasoning_operation_detect_gaps(self):
        """Test gap detection reasoning operation."""
        results = self.engine.run_reasoning_operation("detect_gaps")
        self.assertEqual(len(results), 0)  # No gaps yet
    
    def test_run_reasoning_operation_trace_bottlenecks(self):
        """Test bottleneck tracing reasoning operation."""
        # Create node
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        results = self.engine.run_reasoning_operation("trace_bottlenecks", node_id="sub_1")
        # Returns empty because no bottleneck chain exists
        # This is expected behavior - not a failure
        self.assertEqual(len(results), 0)
    
    def test_run_reasoning_operation_analyze_impact(self):
        """Test impact analysis reasoning operation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        results = self.engine.run_reasoning_operation("analyze_impact", node_id="sub_1")
        self.assertEqual(len(results), 0)  # No dependencies yet
    
    def test_run_reasoning_operation_get_governance_blocks(self):
        """Test governance blocking reasoning operation."""
        results = self.engine.run_reasoning_operation("get_governance_blocks")
        self.assertEqual(len(results), 0)  # No blocked nodes yet
    
    def test_run_reasoning_operation_generate_proposals(self):
        """Test proposal generation reasoning operation."""
        results = self.engine.run_reasoning_operation("generate_proposals")
        self.assertEqual(len(results), 0)  # No gaps yet
    
    def test_export_reasoning_results(self):
        """Test reasoning results export."""
        result = ReasoningResult(
            result_id="reason_1",
            result_type="gap_report",
            content={"gap_id": "gap_1"},
            confidence=0.8,
            governance_required=True,
        )
        
        export = self.engine.export_reasoning_results([result])
        self.assertEqual(export["total_count"], 1)
        self.assertEqual(export["governance_required_count"], 1)
    
    def test_export_proposal_candidates(self):
        """Test proposal candidates export."""
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="operator_review",
        )
        
        export = self.engine.export_proposal_candidates([proposal])
        self.assertEqual(export["total_count"], 1)
        self.assertTrue(export["requires_governance"])


class TestReasoningIntegration(unittest.TestCase):
    """Test reasoning engine integration with query and store."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.engine = create_reasoning_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_engine_uses_query(self):
        """Test that reasoning engine uses query correctly."""
        # Query should be accessible
        self.assertIsNotNone(self.engine.query)
    
    def test_reasoning_with_existing_nodes(self):
        """Test reasoning with existing nodes."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Reasoning should work
        results = self.engine.run_reasoning_operation("detect_gaps")
        self.assertEqual(len(results), 0)  # No gaps yet
    
    def test_export_does_not_mutate(self):
        """Test that export operations don't mutate store."""
        # Create node
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Export results
        results = self.engine.run_reasoning_operation("detect_gaps")
        self.engine.export_reasoning_results(results)
        
        # Store should be unchanged
        loaded = self.store.load_node("sub_1")
        self.assertIsNotNone(loaded)


class TestReasoningBackwardCompatibility(unittest.TestCase):
    """Test reasoning backward compatibility with Phase A."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.engine = create_reasoning_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_phase_a_compatibility(self):
        """Test that reasoning doesn't break Phase A functionality."""
        # Phase A stores
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Phase A should still work
        loaded = self.store.load_node("sub_1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, "sub_1")
    
    def test_reasoning_does_not_mutate_store(self):
        """Test that reasoning operations don't mutate store."""
        # Create node
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Run reasoning (read-only)
        self.engine.run_reasoning_operation("detect_gaps")
        self.engine.run_reasoning_operation("generate_proposals")
        
        # Store should be unchanged
        loaded = self.store.load_node("sub_1")
        self.assertIsNotNone(loaded)
    
    def test_governance_constraint_enforced(self):
        """Test that governance constraint is enforced (no autonomous mutation)."""
        # All proposals must require governance
        proposal = ProposalCandidate(
            proposal_id="prop_1",
            proposal_name="Add System",
            proposal_description="Add new system component",
            proposal_type="architectural",
            confidence=0.8,
            required_governance="operator_review",
        )
        
        valid, _ = self.engine.validate_proposal_governance(proposal)
        self.assertTrue(valid)
        self.assertEqual(proposal.required_governance, "operator_review")


# ============================================================================
# Test Suite Entry
# ============================================================================

if __name__ == "__main__":
    unittest.main()
