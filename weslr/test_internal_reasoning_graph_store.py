"""Test suite for internal_reasoning_graph store - Test Doctrine v1

Test Doctrine version: 1.0.0 (2026-04-08)
"""

import os
import tempfile
import unittest
from pathlib import Path

from weslr.internal_reasoning_graph.models import NodeFactory, EdgeFactory, GovernanceStatus
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore, from_scenario


class TestInternalReasoningGraphStore(unittest.TestCase):
    """Test InternalReasoningGraphStore."""
    
    def setUp(self):
        """Set up test store in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_creation(self):
        """Test store creation and initialization."""
        self.assertTrue(self.store.nodes_dir.exists())
        self.assertTrue(self.store.edges_dir.exists())
        self.assertTrue(self.store.evidence_dir.exists())
        self.assertTrue(self.store.metadata_path.exists())
    
    def test_save_and_load_node(self):
        """Test saving and loading a node."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        
        self.store.save_node(node)
        loaded = self.store.load_node("sub_1", include_edges=True)
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, node.id)
        self.assertEqual(loaded.name, node.name)
    
    def test_save_and_load_edge(self):
        """Test saving and loading an edge."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        edge = EdgeFactory.create_depends_on(
            source_id="sub_1",
            target_id="dep_1",
            reason="Needs dependency",
            confidence=0.7,
        )
        
        self.store.save_edge(edge)
        loaded = self.store.load_edge("sub_1", "dep_1", "depends_on")
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.source_id, "sub_1")
        self.assertEqual(loaded.target_id, "dep_1")
    
    def test_save_node_with_validation(self):
        """Test saving a node with validation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        
        # Save node
        self.store.save_node(node)
        
        # Create validator
        validator = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Validation Gate",
            description="Validates nodes",
            gate_type="proposition",
            confidence=0.95,
        )
        self.store.save_node(validator)
        
        # Add validation edge
        edge = EdgeFactory.create_validated_by(
            source_id="sub_1",
            target_id="gate_1",
            validation_status="valid",
            reason="Passed validation",
            confidence=0.8,
        )
        self.store.save_edge(edge)
        
        # Reload and verify
        reloaded = self.store.load_node("sub_1", include_edges=True)
        self.assertEqual(len(reloaded.edges), 1)
        self.assertEqual(reloaded.edges[0].edge_type, "validated_by")
    
    def test_proposal_workflow(self):
        """Test proposal creation and workflow."""
        # Create proposal
        proposal = self.store.create_proposal(
            name="New Architecture",
            description="Proposed changes",
            proposed_by="model",
            confidence=0.6,
        )
        
        self.assertEqual(proposal.governance_status, GovernanceStatus.PENDING.value)
        
        # Get pending proposals
        proposals = self.store.get_pending_proposals()
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].id, proposal.id)
        
        # Approve proposal
        approved = self.store.approve_proposal(proposal.id, "operator")
        self.assertTrue(approved)
        
        reloaded = self.store.load_node(proposal.id, include_edges=True)
        self.assertEqual(reloaded.governance_status, GovernanceStatus.APPROVED.value)
    
    def test_reject_proposal(self):
        """Test proposal rejection."""
        proposal = self.store.create_proposal(
            name="Proposed Change",
            description="A change",
            proposed_by="model",
        )
        
        rejected = self.store.reject_proposal(
            proposal.id,
            "operator",
            reason="Not aligned with architecture"
        )
        self.assertTrue(rejected)
        
        reloaded = self.store.load_node(proposal.id, include_edges=True)
        self.assertEqual(reloaded.governance_status, GovernanceStatus.REJECTED.value)
        self.assertEqual(reloaded.metadata.get("rejection_reason"), "Not aligned with architecture")
    
    def test_apply_policy(self):
        """Test policy application."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        policy = NodeFactory.create_policy(
            id="pol_1",
            name="Acceptance Policy",
            description="Acceptance rules",
            enforcement_level="hard",
            applies_to=["sub_1"],
        )
        self.store.save_node(policy)
        
        # Apply policy to node
        edge = self.store.apply_policy(
            node_id="sub_1",
            policy_id="pol_1",
            enforcement_level="hard",
            reason="Policy applies",
            confidence=0.7,
        )
        
        self.assertIsNotNone(edge)
        self.assertEqual(edge.edge_type, "governed_by")
        self.assertEqual(edge.edge_subtype, "hard")
    
    def test_node_validation(self):
        """Test node validation workflow."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        validator = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Validation Gate",
            description="Validates nodes",
            gate_type="proposition",
            confidence=0.95,
        )
        self.store.save_node(validator)
        
        # Validate node
        edge = self.store.validate_node(
            node_id="sub_1",
            validator_id="gate_1",
            validation_status="valid",
            reason="Passed validation",
            confidence=0.8,
        )
        
        self.assertIsNotNone(edge)
        
        # Reload and verify
        reloaded = self.store.load_node("sub_1", include_edges=True)
        self.assertEqual(len(reloaded.edges), 1)
        self.assertEqual(reloaded.edges[0].edge_type, "validated_by")
    
    def test_statistics(self):
        """Test graph statistics."""
        # Create nodes
        for i in range(3):
            node = NodeFactory.create_subsystem(
                id=f"sub_{i}",
                name=f"System {i}",
                description=f"A system {i}",
            )
            self.store.save_node(node)
        
        # Create edges
        for i in range(3):
            edge = EdgeFactory.create_depends_on(
                source_id=f"sub_{i}",
                target_id=f"dep_{i}",
                reason=f"Needs dependency {i}",
                confidence=0.7,
            )
            self.store.save_edge(edge)
        
        stats = self.store.get_statistics()
        
        self.assertEqual(stats["node_count"], 3)
        self.assertEqual(stats["edge_count"], 3)
        self.assertIn("subsystem", stats["nodes_by_type"])
    
    def test_from_scenario(self):
        """Test from_scenario helper."""
        scenario = {
            "id": "test_node",
            "name": "Test Node",
            "description": "A test node",
            "subtype": "test",
        }
        
        node = from_scenario(scenario)
        
        self.assertEqual(node.id, "test_node")
        self.assertEqual(node.name, "Test Node")
        self.assertEqual(node.node_type, "subsystem")
    
    def test_delete_node(self):
        """Test node deletion."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        self.assertIsNotNone(self.store.load_node("sub_1", include_edges=True))
        
        self.store.delete_node("sub_1")
        
        self.assertIsNone(self.store.load_node("sub_1", include_edges=True))
    
    def test_delete_edge(self):
        """Test edge deletion."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        edge = EdgeFactory.create_depends_on(
            source_id="sub_1",
            target_id="dep_1",
            reason="Needs dependency",
            confidence=0.7,
        )
        self.store.save_edge(edge)
        
        self.assertIsNotNone(self.store.load_edge("sub_1", "dep_1", "depends_on"))
        
        self.store.delete_edge("sub_1", "dep_1", "depends_on")
        
        self.assertIsNone(self.store.load_edge("sub_1", "dep_1", "depends_on"))


class TestStoreValidation(unittest.TestCase):
    """Test store validation rules."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cannot_save_invalid_node(self):
        """Test cannot save node without id."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        node.id = ""  # Invalid
        
        with self.assertRaises(ValueError):
            self.store.save_node(node)
    
    def test_cannot_save_invalid_edge(self):
        """Test cannot save edge without source."""
        edge = EdgeFactory.create_depends_on(
            source_id="source",
            target_id="target",
            reason="Needs target",
            confidence=0.7,
        )
        edge.source_id = ""  # Invalid
        
        with self.assertRaises(ValueError):
            self.store.save_edge(edge)
    
    def test_cannot_save_invalid_proposal(self):
        """Test cannot save proposal without proposed_by."""
        node = NodeFactory.create_proposal(
            id="prop_1",
            name="Proposal",
            description="A proposal",
            proposed_by="model",
        )
        node.metadata = {}  # Remove proposed_by
        
        with self.assertRaises(ValueError):
            self.store.save_node(node)
    
    def test_cannot_save_invalid_trust_gate(self):
        """Test cannot save trust gate with low confidence."""
        node = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Gate",
            description="A gate",
            gate_type="proposition",
            confidence=0.95,
        )
        node.confidence = 0.8  # Too low
        
        with self.assertRaises(ValueError):
            self.store.save_node(node)
    
    def test_cannot_save_high_risk_edge_with_low_confidence(self):
        """Test cannot save high-risk edge with low confidence."""
        with self.assertRaises(ValueError) as ctx:
            EdgeFactory.create_replaces(
                source_id="source",
                target_id="target",
                reason="Replaces target",
                confidence=0.5,  # Too low
            )
        self.assertIn("confidence", str(ctx.exception))


class TestStoreGovernance(unittest.TestCase):
    """Test store governance functionality."""
    
    def setUp(self):
        """Set up test store."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = InternalReasoningGraphStore(
            graph_dir=Path(self.temp_dir) / "internal_reasoning_graph"
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_governed_node(self):
        """Test node with governance policy."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        policy = NodeFactory.create_policy(
            id="pol_1",
            name="Acceptance Policy",
            description="Acceptance rules",
            enforcement_level="hard",
            applies_to=["sub_1"],
        )
        self.store.save_node(policy)
        
        # Apply policy
        edge = EdgeFactory.create_governed_by(
            source_id="sub_1",
            target_id="pol_1",
            enforcement_level="hard",
            reason="Policy applies",
            confidence=0.7,
        )
        self.store.save_edge(edge)
        
        # Reload and verify
        reloaded = self.store.load_node("sub_1", include_edges=True)
        self.assertEqual(len(reloaded.edges), 1)
        self.assertEqual(reloaded.edges[0].edge_subtype, "hard")
    
    def test_validated_node(self):
        """Test node with validation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        self.store.save_node(node)
        
        validator = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Validation Gate",
            description="Validates nodes",
            gate_type="proposition",
            confidence=0.95,
        )
        self.store.save_node(validator)
        
        # Validate node
        edge = EdgeFactory.create_validated_by(
            source_id="sub_1",
            target_id="gate_1",
            validation_status="valid",
            reason="Passed validation",
            confidence=0.8,
        )
        self.store.save_edge(edge)
        
        # Reload and verify
        reloaded = self.store.load_node("sub_1", include_edges=True)
        self.assertEqual(len(reloaded.edges), 1)
        self.assertEqual(reloaded.edges[0].edge_subtype, "valid")
    
    def test_conflicting_proposals(self):
        """Test proposal conflict detection."""
        # Create proposal 1
        prop1 = self.store.create_proposal(
            name="Change A",
            description="Change A",
            proposed_by="model",
            confidence=0.6,
        )
        
        # Create proposal 2
        prop2 = self.store.create_proposal(
            name="Change B",
            description="Change B",
            proposed_by="model",
            confidence=0.6,
        )
        
        # Both propose changes to same subsystem
        edge1 = EdgeFactory.create_proposes_change_to(
            source_id=prop1.id,
            target_id="sub_1",
            change_type="modify",
            reason="Modify sub_1",
            confidence=0.6,
        )
        prop1.add_edge(edge1)
        self.store.save_node(prop1)
        
        edge2 = EdgeFactory.create_proposes_change_to(
            source_id=prop2.id,
            target_id="sub_1",
            change_type="remove",
            reason="Remove sub_1",
            confidence=0.6,
        )
        prop2.add_edge(edge2)
        self.store.save_node(prop2)
        
        # Reload and verify
        reloaded1 = self.store.load_node(prop1.id)
        reloaded2 = self.store.load_node(prop2.id)
        
        self.assertEqual(len(reloaded1.edges), 1)
        self.assertEqual(len(reloaded2.edges), 1)


# ============================================================================
# Test Suite Entry
# ============================================================================

if __name__ == "__main__":
    unittest.main()
