"""Test suite for internal_reasoning_graph models - Test Doctrine v1

Test Doctrine version: 1.0.0 (2026-04-08)
"""

import unittest
import time
from dataclasses import asdict

from weslr.internal_reasoning_graph.models import (
    Node,
    Edge,
    Evidence,
    NodeSubtype,
    GovernanceStatus,
    ProposalStatus,
    ValidationStatus,
    EdgeType,
    ChangeType,
    ConflictType,
    NodeFactory,
    EdgeFactory,
    NodeValidator,
    EdgeValidator,
)


class TestNodeModel(unittest.TestCase):
    """Test Node data model."""
    
    def test_node_creation(self):
        """Test basic node creation."""
        node = NodeFactory.create_subsystem(
            id="test_subsystem",
            name="Test Subsystem",
            description="A test subsystem",
        )
        
        self.assertEqual(node.id, "test_subsystem")
        self.assertEqual(node.name, "Test Subsystem")
        self.assertEqual(node.description, "A test subsystem")
        self.assertEqual(node.node_type, "subsystem")
        self.assertEqual(node.status, "active")
        self.assertGreaterEqual(node.confidence, 0.5)
    
    def test_node_serialization(self):
        """Test node to_dict/from_dict serialization."""
        node = NodeFactory.create_subsystem(
            id="test_subsystem",
            name="Test Subsystem",
            description="A test subsystem",
        )
        
        data = node.to_dict()
        restored = Node.from_dict(data)
        
        self.assertEqual(node.id, restored.id)
        self.assertEqual(node.name, restored.name)
        self.assertEqual(node.description, restored.description)
        self.assertEqual(node.node_type, restored.node_type)
    
    def test_node_with_evidence(self):
        """Test node with evidence."""
        evidence = Evidence(
            source_id="test_source",
            source_type="test_type",
            content="Test evidence",
            confidence=0.8,
            timestamp=int(time.time()),
            category="source-backed",
        )
        
        node = NodeFactory.create_subsystem(
            id="test_subsystem",
            name="Test Subsystem",
            description="A test subsystem",
        )
        node.add_evidence(evidence)
        
        self.assertEqual(len(node.evidence), 1)
        self.assertGreater(node.confidence, 0.5)
    
    def test_node_with_edges(self):
        """Test node with edges."""
        edge = EdgeFactory.create_depends_on(
            source_id="test_subsystem",
            target_id="dependency",
            reason="Requires dependency",
            confidence=0.7,
        )
        
        node = NodeFactory.create_subsystem(
            id="test_subsystem",
            name="Test Subsystem",
            description="A test subsystem",
        )
        node.add_edge(edge)
        
        self.assertEqual(len(node.edges), 1)
        self.assertEqual(node.get_edge("dependency", "depends_on"), edge)
    
    def test_node_governance(self):
        """Test node governance status."""
        node = NodeFactory.create_subsystem(
            id="test_subsystem",
            name="Test Subsystem",
            description="A test subsystem",
        )
        
        node.mark_governance(GovernanceStatus.APPROVED.value, "operator")
        
        self.assertEqual(node.governance_status, GovernanceStatus.APPROVED.value)
        self.assertIsNotNone(node.governance_decided_at)
        self.assertEqual(node.governance_decided_by, "operator")


class TestEdgeModel(unittest.TestCase):
    """Test Edge data model."""
    
    def test_edge_creation(self):
        """Test basic edge creation."""
        edge = EdgeFactory.create_depends_on(
            source_id="source",
            target_id="target",
            reason="Requires target",
            confidence=0.7,
        )
        
        self.assertEqual(edge.source_id, "source")
        self.assertEqual(edge.target_id, "target")
        self.assertEqual(edge.edge_type, EdgeType.DEPENDS_ON.value)
        self.assertEqual(edge.reason, "Requires target")
        self.assertGreaterEqual(edge.confidence, 0.7)
    
    def test_edge_serialization(self):
        """Test edge to_dict/from_dict serialization."""
        edge = EdgeFactory.create_depends_on(
            source_id="source",
            target_id="target",
            reason="Requires target",
            confidence=0.7,
        )
        
        data = edge.to_dict()
        restored = Edge.from_dict(data)
        
        self.assertEqual(edge.source_id, restored.source_id)
        self.assertEqual(edge.target_id, restored.target_id)
        self.assertEqual(edge.edge_type, restored.edge_type)
    
    def test_high_risk_edge_replacement(self):
        """Test high-risk replaces edge requires high confidence."""
        with self.assertRaises(ValueError):
            EdgeFactory.create_replaces(
                source_id="source",
                target_id="target",
                reason="Replaces target",
                confidence=0.5,  # Too low for replaces
            )
    
    def test_high_risk_edge_conflicts(self):
        """Test high-risk conflicts_with edge requires high confidence."""
        with self.assertRaises(ValueError):
            EdgeFactory.create_conflicts_with(
                source_id="source",
                target_id="target",
                conflict_type="contradiction",
                reason="Conflicts with target",
                confidence=0.5,  # Too low for conflicts_with
            )
    
    def test_proposes_change_to_edge(self):
        """Test proposes_change_to edge with change types."""
        edge = EdgeFactory.create_proposes_change_to(
            source_id="proposal",
            target_id="subsystem",
            change_type="modify",
            reason="Modifies subsystem",
            confidence=0.6,
        )
        
        self.assertEqual(edge.change_type, "modify")
        self.assertEqual(edge.edge_subtype, "modify")
    
    def test_conflicts_with_edge(self):
        """Test conflicts_with edge with conflict types."""
        edge = EdgeFactory.create_conflicts_with(
            source_id="source",
            target_id="target",
            conflict_type="contradiction",
            reason="Conflicts with target",
            confidence=0.8,
        )
        
        self.assertEqual(edge.conflict_type, "contradiction")
        self.assertEqual(edge.edge_subtype, "contradiction")


class TestEvidenceModel(unittest.TestCase):
    """Test Evidence data model."""
    
    def test_evidence_creation(self):
        """Test basic evidence creation."""
        evidence = Evidence(
            source_id="test_source",
            source_type="test_type",
            content="Test evidence",
            confidence=0.8,
            timestamp=int(time.time()),
            category="source-backed",
        )
        
        self.assertEqual(evidence.source_id, "test_source")
        self.assertEqual(evidence.confidence, 0.8)
        self.assertEqual(evidence.category, "source-backed")
    
    def test_evidence_serialization(self):
        """Test evidence to_dict/from_dict serialization."""
        evidence = Evidence(
            source_id="test_source",
            source_type="test_type",
            content="Test evidence",
            confidence=0.8,
            timestamp=int(time.time()),
            category="source-backed",
        )
        
        data = evidence.to_dict()
        restored = Evidence.from_dict(data)
        
        self.assertEqual(evidence.source_id, restored.source_id)
        self.assertEqual(evidence.confidence, restored.confidence)
    
    def test_evidence_expiration(self):
        """Test evidence expiration check."""
        evidence = Evidence(
            source_id="test_source",
            source_type="test_type",
            content="Test evidence",
            confidence=0.8,
            timestamp=int(time.time()) - (31 * 24 * 60 * 60),  # 31 days ago
            category="source-backed",
        )
        
        self.assertTrue(evidence.is_expired(max_age_seconds=2592000))  # 30 days


class TestNodeFactory(unittest.TestCase):
    """Test NodeFactory."""
    
    def test_create_subsystem(self):
        """Test subsystem creation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
            version="v1.0",
            confidence=0.6,
        )
        
        self.assertEqual(node.node_type, "subsystem")
        self.assertEqual(node.version, "v1.0")
    
    def test_create_capability(self):
        """Test capability creation."""
        node = NodeFactory.create_capability(
            id="cap_1",
            name="Detection Capability",
            description="Detects anomalies",
            node_subtype="detection",
            confidence=0.7,
        )
        
        self.assertEqual(node.node_type, "capability")
        self.assertEqual(node.node_subtype, "detection")
    
    def test_create_bottleneck(self):
        """Test bottleneck creation."""
        node = NodeFactory.create_bottleneck(
            id="bot_1",
            name="Detection Bottleneck",
            description="No autonomous detection",
            severity="critical",
            confidence=0.8,
        )
        
        self.assertEqual(node.node_type, "bottleneck")
        self.assertEqual(node.metadata["severity"], "critical")
    
    def test_create_policy(self):
        """Test policy creation."""
        node = NodeFactory.create_policy(
            id="pol_1",
            name="Acceptance Policy",
            description="Acceptance rules",
            enforcement_level="hard",
            applies_to=["sub_1"],
            confidence=0.85,
        )
        
        self.assertEqual(node.node_type, "policy")
        self.assertEqual(node.metadata["enforcement_level"], "hard")
    
    def test_create_proposal(self):
        """Test proposal creation."""
        node = NodeFactory.create_proposal(
            id="prop_1",
            name="New Architecture",
            description="Proposed changes",
            proposed_by="model",
            confidence=0.5,
        )
        
        self.assertEqual(node.node_type, "proposal")
        self.assertEqual(node.governance_status, GovernanceStatus.PENDING.value)
    
    def test_create_trust_gate(self):
        """Test trust gate creation."""
        node = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Modification Gate",
            description="Requires approval",
            gate_type="modification",
            confidence=0.95,
        )
        
        self.assertEqual(node.node_type, "trust_gate")
        self.assertEqual(node.metadata["gate_type"], "modification")
        self.assertGreaterEqual(node.confidence, 0.9)


class TestEdgeFactory(unittest.TestCase):
    """Test EdgeFactory."""
    
    def test_create_depends_on(self):
        """Test depends_on edge creation."""
        edge = EdgeFactory.create_depends_on(
            source_id="source",
            target_id="target",
            reason="Needs target",
            confidence=0.7,
        )
        
        self.assertEqual(edge.edge_type, EdgeType.DEPENDS_ON.value)
    
    def test_create_bottleneck_for(self):
        """Test bottleneck_for edge creation."""
        edge = EdgeFactory.create_bottleneck_for(
            source_id="bot_1",
            target_id="sub_1",
            severity="high",
            reason="Blocks sub_1",
            confidence=0.7,
        )
        
        self.assertEqual(edge.edge_type, EdgeType.BOTTLENECK_FOR.value)
        self.assertEqual(edge.edge_subtype, "high")
    
    def test_create_governed_by(self):
        """Test governed_by edge creation."""
        edge = EdgeFactory.create_governed_by(
            source_id="sub_1",
            target_id="pol_1",
            enforcement_level="hard",
            reason="Policy applies",
            confidence=0.7,
        )
        
        self.assertEqual(edge.edge_type, EdgeType.GOVERNED_BY.value)
        self.assertEqual(edge.edge_subtype, "hard")
    
    def test_create_proposes_change_to(self):
        """Test proposes_change_to edge creation."""
        edge = EdgeFactory.create_proposes_change_to(
            source_id="prop_1",
            target_id="sub_1",
            change_type="modify",
            reason="Modify sub_1",
            confidence=0.6,
        )
        
        self.assertEqual(edge.edge_type, EdgeType.PROPOSES_CHANGE_TO.value)
        self.assertEqual(edge.change_type, "modify")


class TestNodeValidator(unittest.TestCase):
    """Test NodeValidator."""
    
    def test_valid_node(self):
        """Test valid node passes validation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        
        valid, reason = NodeValidator.validate_node(node)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid")
    
    def test_invalid_node_missing_id(self):
        """Test node without id fails validation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        node.id = ""
        
        valid, reason = NodeValidator.validate_node(node)
        self.assertFalse(valid)
        self.assertIn("id", reason)
    
    def test_invalid_node_type(self):
        """Test node with invalid type fails validation."""
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        node.node_type = "invalid_type"
        
        valid, reason = NodeValidator.validate_node(node)
        self.assertFalse(valid)
        self.assertIn("node_type", reason)
    
    def test_valid_proposal(self):
        """Test valid proposal passes validation."""
        node = NodeFactory.create_proposal(
            id="prop_1",
            name="Proposal",
            description="A proposal",
            proposed_by="model",
        )
        
        valid, reason = NodeValidator.validate_proposal(node)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid")
    
    def test_valid_trust_gate(self):
        """Test valid trust gate passes validation."""
        node = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Gate",
            description="A gate",
            gate_type="proposition",
            confidence=0.95,
        )
        
        valid, reason = NodeValidator.validate_trust_gate(node)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid")
    
    def test_trust_gate_low_confidence(self):
        """Test trust gate with low confidence fails factory validation."""
        with self.assertRaises(ValueError) as ctx:
            NodeFactory.create_trust_gate(
                id="gate_1",
                name="Gate",
                description="A gate",
                gate_type="proposition",
                confidence=0.8,
            )
        self.assertIn("confidence", str(ctx.exception))


class TestEdgeValidator(unittest.TestCase):
    """Test EdgeValidator."""
    
    def test_valid_edge(self):
        """Test valid edge passes validation."""
        edge = EdgeFactory.create_depends_on(
            source_id="source",
            target_id="target",
            reason="Needs target",
            confidence=0.7,
        )
        
        valid, reason = EdgeValidator.validate_edge(edge)
        self.assertTrue(valid)
        self.assertEqual(reason, "Valid")
    
    def test_invalid_edge_high_risk_low_confidence(self):
        """Test high-risk edge with low confidence fails factory validation."""
        with self.assertRaises(ValueError) as ctx:
            EdgeFactory.create_replaces(
                source_id="source",
                target_id="target",
                reason="Replaces target",
                confidence=0.5,  # Too low
            )
        self.assertIn("confidence", str(ctx.exception))
    
    def test_invalid_edge_subtype(self):
        """Test edge with invalid subtype fails validation."""
        edge = EdgeFactory.create_bottleneck_for(
            source_id="bot_1",
            target_id="sub_1",
            severity="invalid_severity",  # Invalid
            reason="Blocks sub_1",
            confidence=0.7,
        )
        
        valid, reason = EdgeValidator.validate_edge_subtype(edge)
        self.assertFalse(valid)
        self.assertIn("subtype", reason)


class TestModelIntegration(unittest.TestCase):
    """Test model integration and workflows."""
    
    def test_proposal_workflow(self):
        """Test complete proposal workflow."""
        # Create proposal
        proposal = NodeFactory.create_proposal(
            id="prop_1",
            name="New Architecture",
            description="Proposed changes",
            proposed_by="model",
            confidence=0.6,
        )
        
        # Create policy
        policy = NodeFactory.create_policy(
            id="pol_1",
            name="Acceptance Policy",
            description="Acceptance rules",
            enforcement_level="hard",
            applies_to=["prop_1"],
        )
        
        # Create governed_by edge
        edge = EdgeFactory.create_governed_by(
            source_id="prop_1",
            target_id="pol_1",
            enforcement_level="hard",
            reason="Policy applies",
            confidence=0.7,
        )
        
        proposal.add_edge(edge)
        
        self.assertEqual(len(proposal.edges), 1)
        self.assertEqual(proposal.governance_status, GovernanceStatus.PENDING.value)
    
    def test_validation_workflow(self):
        """Test complete validation workflow."""
        # Create node to validate
        node = NodeFactory.create_subsystem(
            id="sub_1",
            name="System",
            description="A system",
        )
        
        # Create validator
        validator = NodeFactory.create_trust_gate(
            id="gate_1",
            name="Validation Gate",
            description="Validates nodes",
            gate_type="proposition",
            confidence=0.95,
        )
        
        # Create validated_by edge
        edge = EdgeFactory.create_validated_by(
            source_id="sub_1",
            target_id="gate_1",
            validation_status="valid",
            reason="Passed validation",
            confidence=0.8,
        )
        
        node.add_edge(edge)
        
        self.assertEqual(len(node.edges), 1)
        self.assertEqual(node.governance_status, GovernanceStatus.PENDING.value)


# ============================================================================
# Test Suite Entry
# ============================================================================

if __name__ == "__main__":
    unittest.main()
