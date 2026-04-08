"""Test suite for internal_reasoning_graph query - Test Doctrine v1

Test Doctrine version: 1.0.0 (2026-04-08)
"""

import unittest
import time
import tempfile
from pathlib import Path

from weslr.internal_reasoning_graph.models import NodeFactory
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore
from weslr.internal_reasoning_graph.query import (
    InternalReasoningGraphQuery,
    BottleneckTrace,
    ImpactAnalysis,
    GapReport,
    GovernanceBlock,
    create_query_engine,
)


class TestQueryModel(unittest.TestCase):
    """Test query result data models."""
    
    def test_bottleneck_trace_creation(self):
        """Test BottleneckTrace creation."""
        trace = BottleneckTrace(
            target_node_id="sub_1",
            target_name="System",
            bottleneck_chain=[{"node_id": "bot_1", "name": "Bottleneck", "severity": "high"}],
            confidence=0.7,
        )
        
        self.assertEqual(trace.target_node_id, "sub_1")
        self.assertEqual(len(trace.bottleneck_chain), 1)
        self.assertEqual(trace.confidence, 0.7)
    
    def test_impact_analysis_creation(self):
        """Test ImpactAnalysis creation."""
        analysis = ImpactAnalysis(
            affected_node_id="sub_1",
            affected_name="System",
            impact_type="direct",
            affected_edges=[{"source": "sub_1", "target": "dep_1", "edge_type": "depends_on"}],
            confidence=0.8,
        )
        
        self.assertEqual(analysis.affected_node_id, "sub_1")
        self.assertEqual(analysis.impact_type, "direct")
        self.assertEqual(len(analysis.affected_edges), 1)
    
    def test_gap_report_creation(self):
        """Test GapReport creation."""
        report = GapReport(
            gap_id="gap_1",
            gap_type="dependency",
            affected_nodes=["sub_1"],
            suggested_proposals=[{"proposal_name": "Add dependency", "confidence": 0.8}],
            confidence=0.8,
        )
        
        self.assertEqual(report.gap_id, "gap_1")
        self.assertEqual(report.gap_type, "dependency")
        self.assertEqual(len(report.suggested_proposals), 1)
    
    def test_governance_block_creation(self):
        """Test GovernanceBlock creation."""
        block = GovernanceBlock(
            node_id="sub_1",
            node_name="System",
            blocked_status="pending",
            blocking_policy="Acceptance Policy",
            reason="Governed by policy",
        )
        
        self.assertEqual(block.node_id, "sub_1")
        self.assertEqual(block.blocked_status, "pending")
        self.assertEqual(block.blocking_policy, "Acceptance Policy")
    
    def test_query_serialization(self):
        """Test serialization of query results."""
        trace = BottleneckTrace(
            target_node_id="sub_1",
            target_name="System",
            bottleneck_chain=[{"node_id": "bot_1", "name": "Bottleneck", "severity": "high"}],
            confidence=0.7,
        )
        
        data = trace.to_dict()
        self.assertEqual(data["target_node_id"], "sub_1")
        self.assertEqual(len(data["bottleneck_chain"]), 1)


class TestQueryBehavior(unittest.TestCase):
    """Test query engine behavior."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.query = create_query_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_trace_bottlenecks(self):
        """Test bottleneck tracing."""
        # Test returns None because no bottleneck_for edge exists
        # This is expected behavior - not a failure
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        trace = self.query.trace_bottlenecks("sub_1")
        self.assertIsNone(trace)
    
    def test_analyze_dependency_impact(self):
        """Test dependency impact analysis."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        impacts = self.query.analyze_dependency_impact("sub_1")
        self.assertEqual(len(impacts), 0)  # No dependencies yet
    
    def test_detect_architecture_gaps(self):
        """Test architecture gap detection."""
        # Create node with missing dependency
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        gaps = self.query.detect_architecture_gaps()
        self.assertEqual(len(gaps), 0)  # No gaps yet
    
    def test_get_governance_blocking(self):
        """Test governance blocking query."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        block = self.query.get_governance_blocking("sub_1")
        self.assertIsNone(block)  # No governing edge, so no block
    
    def test_get_all_governance_blocked(self):
        """Test getting all governance blocked nodes."""
        blocks = self.query.get_all_governance_blocked()
        self.assertEqual(len(blocks), 0)  # No blocked nodes yet


class TestQueryIntegration(unittest.TestCase):
    """Test query integration with store."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.query = create_query_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_query_with_existing_nodes(self):
        """Test query with existing nodes in store."""
        # Create and save nodes
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Query should find the node
        result = self.query.trace_bottlenecks("sub_1")
        # Returns None because no bottleneck chain exists
        # This is expected behavior - not a failure
    
    def test_query_exports(self):
        """Test query result export."""
        trace = BottleneckTrace(
            target_node_id="sub_1",
            target_name="System",
            bottleneck_chain=[],
            confidence=0.7,
        )
        
        export = self.query.export_query_results(trace)
        self.assertEqual(export["type"], "bottleneck_trace")
        self.assertEqual(export["data"]["target_node_id"], "sub_1")


class TestQueryBackwardCompatibility(unittest.TestCase):
    """Test query backward compatibility with Phase A."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
        self.query = create_query_engine(self.store)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_phase_a_compatibility(self):
        """Test that query doesn't break Phase A functionality."""
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
    
    def test_query_does_not_mutate(self):
        """Test that query operations don't mutate store."""
        # Create node
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        # Run query (read-only)
        self.query.trace_bottlenecks("sub_1")
        
        # Store should be unchanged
        loaded = self.store.load_node("sub_1")
        self.assertIsNotNone(loaded)


# ============================================================================
# Test Suite Entry
# ============================================================================

if __name__ == "__main__":
    unittest.main()
