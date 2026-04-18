"""Internal Reasoning Graph Store

Persistence layer for internal reasoning graph:
- Saves/loads nodes and edges
- Manages validation, governance hooks
- Handles proposal workflow
- Provides save/load/merge operations

Storage structure:
  nodes/          - Node files (id.json)
  edges/          - Edge files (source-target-type.json)
  metadata.json   - Graph metadata
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    Node,
    Edge,
    Evidence,
    NodeValidator,
    EdgeValidator,
    GovernanceStatus,
    ProposalStatus,
    ValidationStatus,
    NodeFactory,
    EdgeFactory,
)


# Base directory for internal reasoning graph storage
BASE_DIR = Path(__file__).resolve().parent
GRAPH_DIR = BASE_DIR / "internal_reasoning_graph"
NODES_DIR = GRAPH_DIR / "nodes"
EDGES_DIR = GRAPH_DIR / "edges"
EVIDENCE_DIR = GRAPH_DIR / "evidence"

DEFAULT_GRAPH_PATH = GRAPH_DIR / "metadata.json"


class InternalReasoningGraphStore:
    """Persistence layer for internal reasoning graph.
    
    Manages:
    - Node storage and retrieval
    - Edge storage and retrieval
    - Validation workflow
    - Governance hooks
    - Proposal tracking
    """
    
    def __init__(self, graph_dir: Path = None):
        """Initialize store with optional custom directory."""
        self.graph_dir = graph_dir or GRAPH_DIR
        self.nodes_dir = self.graph_dir / "nodes"
        self.edges_dir = self.graph_dir / "edges"
        self.evidence_dir = self.graph_dir / "evidence"
        
        self.metadata_path = self.graph_dir / "metadata.json"
        self.proposal_path = self.graph_dir / "proposals.json"
        
        # Create directories
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        self.edges_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Load metadata (creates file if missing)
        self._metadata = self._load_metadata()
        # Create metadata file if it doesn't exist
        if not self.metadata_path.exists():
            self._save_metadata()
        
        # In-memory cache
        self._node_cache: Dict[str, Node] = {}
        self._edge_cache: Dict[str, Edge] = {}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load or initialize graph metadata."""
        if self.metadata_path.exists():
            try:
                return json.loads(self.metadata_path.read_text())
            except Exception:
                pass
        return {
            "version": "1.0",
            "created_at": int(time.time()),
            "last_updated": int(time.time()),
            "node_count": 0,
            "edge_count": 0,
        }
    
    def _save_metadata(self) -> None:
        """Save graph metadata."""
        self.metadata_path.write_text(json.dumps(self._metadata, indent=2))
    
    def save(self) -> None:
        """Save all nodes and edges to disk."""
        # Save nodes
        for node_id, node in self._node_cache.items():
            path = self.nodes_dir / f"{node_id}.json"
            path.write_text(json.dumps(node.to_dict(), indent=2))
        
        # Save edges
        for edge_key, edge in self._edge_cache.items():
            path = self.edges_dir / f"{edge_key}.json"
            path.write_text(json.dumps(edge.to_dict(), indent=2))
        
        # Update metadata
        self._metadata["last_updated"] = int(time.time())
        self._metadata["node_count"] = len(self._node_cache)
        self._metadata["edge_count"] = len(self._edge_cache)
        self._save_metadata()
    
    def load(self) -> None:
        """Load nodes and edges from disk."""
        # Load nodes
        for path in self.nodes_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                node = Node.from_dict(data)
                self._node_cache[node.id] = node
            except Exception:
                pass
        
        # Load edges
        for path in self.edges_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                edge = Edge.from_dict(data)
                edge_key = f"{edge.source_id}-{edge.target_id}-{edge.edge_type}"
                self._edge_cache[edge_key] = edge
            except Exception:
                pass
        
        # Load metadata
        self._metadata = self._load_metadata()
    
    def save_node(self, node: Node) -> None:
        """Save a single node with validation."""
        # Validate node
        valid, reason = NodeValidator.validate_node(node)
        if not valid:
            raise ValueError(f"Invalid node: {reason}")
        
        valid, reason = NodeValidator.validate_node_subtype(node)
        if not valid:
            raise ValueError(f"Invalid node subtype: {reason}")
        
        # Special validation for proposals
        if node.node_type == "proposal":
            valid, reason = NodeValidator.validate_proposal(node)
            if not valid:
                raise ValueError(f"Invalid proposal: {reason}")
        
        # Special validation for trust gates
        if node.node_type == "trust_gate":
            valid, reason = NodeValidator.validate_trust_gate(node)
            if not valid:
                raise ValueError(f"Invalid trust gate: {reason}")
        
        path = self.nodes_dir / f"{node.id}.json"
        path.write_text(json.dumps(node.to_dict(), indent=2))
        self._node_cache[node.id] = node
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def load_node(self, node_id: str, include_edges: bool = False) -> Optional[Node]:
        """Load a single node by ID.
        
        Args:
            node_id: Node ID to load
            include_edges: If True, also load and attach edges for this node
        """
        path = self.nodes_dir / f"{node_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            node = Node.from_dict(data)
            if include_edges:
                # Load edges where this node is source or target
                for edge_file in self.edges_dir.glob(f"{node_id}-*.json"):
                    try:
                        edge_data = json.loads(edge_file.read_text())
                        edge = Edge.from_dict(edge_data)
                        node.add_edge(edge)
                    except Exception:
                        pass
                for edge_file in self.edges_dir.glob(f"*-{node_id}-*.json"):
                    try:
                        edge_data = json.loads(edge_file.read_text())
                        edge = Edge.from_dict(edge_data)
                        node.add_edge(edge)
                    except Exception:
                        pass
            return node
        return self._node_cache.get(node_id)
    
    def save_edge(self, edge: Edge) -> None:
        """Save a single edge with validation."""
        # Validate edge
        valid, reason = EdgeValidator.validate_edge(edge)
        if not valid:
            raise ValueError(f"Invalid edge: {reason}")
        
        valid, reason = EdgeValidator.validate_edge_subtype(edge)
        if not valid:
            raise ValueError(f"Invalid edge subtype: {reason}")
        
        # High-risk edge check
        valid, reason = EdgeValidator.validate_high_risk_edge(edge)
        if not valid:
            raise ValueError(f"Invalid high-risk edge: {reason}")
        
        edge_key = f"{edge.source_id}-{edge.target_id}-{edge.edge_type}"
        path = self.edges_dir / f"{edge_key}.json"
        path.write_text(json.dumps(edge.to_dict(), indent=2))
        self._edge_cache[edge_key] = edge
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def load_edge(self, source_id: str, target_id: str, edge_type: str) -> Optional[Edge]:
        """Load a single edge by source, target, and type."""
        edge_key = f"{source_id}-{target_id}-{edge_type}"
        path = self.edges_dir / f"{edge_key}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return Edge.from_dict(data)
        return self._edge_cache.get(edge_key)
    
    def list_nodes(self) -> List[Node]:
        """List all nodes."""
        self.load()
        return list(self._node_cache.values())
    
    def list_edges(self) -> List[Edge]:
        """List all edges."""
        self.load()
        return list(self._edge_cache.values())
    
    def delete_node(self, node_id: str) -> None:
        """Delete a node by ID."""
        path = self.nodes_dir / f"{node_id}.json"
        if path.exists():
            path.unlink()
        if node_id in self._node_cache:
            del self._node_cache[node_id]
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def delete_edge(self, source_id: str, target_id: str, edge_type: str) -> None:
        """Delete an edge by source, target, and type."""
        edge_key = f"{source_id}-{target_id}-{edge_type}"
        path = self.edges_dir / f"{edge_key}.json"
        if path.exists():
            path.unlink()
        if edge_key in self._edge_cache:
            del self._edge_cache[edge_key]
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def get_node_count(self) -> int:
        """Get number of nodes."""
        return len(self._node_cache)
    
    def get_edge_count(self) -> int:
        """Get number of edges."""
        return len(self._edge_cache)
    
    def is_stale_node(self, node: Node, max_age_seconds: int = 604800) -> bool:
        """Check if node is stale."""
        return time.time() - node.updated_at > max_age_seconds
    
    # Proposal workflow methods
    
    def create_proposal(
        self,
        name: str,
        description: str,
        proposed_by: str,
        confidence: float = 0.5,
        required_governance: str = "operator_review",
    ) -> Node:
        """Create a new proposal node."""
        proposal = NodeFactory.create_proposal(
            id=f"prop_{int(time.time())}",
            name=name,
            description=description,
            proposed_by=proposed_by,
            confidence=confidence,
            required_governance=required_governance,
        )
        self.save_node(proposal)
        return proposal
    
    def get_proposals(self, status: Optional[str] = None) -> List[Node]:
        """Get proposals, optionally filtered by status."""
        proposals = []
        for node in self._node_cache.values():
            if node.node_type == "proposal":
                if status is None or node.governance_status == status:
                    proposals.append(node)
        return proposals
    
    def get_pending_proposals(self) -> List[Node]:
        """Get all pending proposals requiring governance."""
        return self.get_proposals(status=GovernanceStatus.PENDING.value)
    
    def approve_proposal(self, proposal_id: str, approved_by: Optional[str] = None) -> bool:
        """Approve a proposal (requires governance)."""
        proposal = self.load_node(proposal_id)
        if not proposal or proposal.node_type != "proposal":
            return False
        
        proposal.mark_governance(GovernanceStatus.APPROVED.value, approved_by)
        proposal.status = "proposed"
        proposal.metadata["governance_status"] = "approved"
        self.save_node(proposal)
        return True
    
    def reject_proposal(self, proposal_id: str, rejected_by: Optional[str] = None, reason: str = "") -> bool:
        """Reject a proposal (requires governance)."""
        proposal = self.load_node(proposal_id)
        if not proposal or proposal.node_type != "proposal":
            return False
        
        proposal.mark_governance(GovernanceStatus.REJECTED.value, rejected_by)
        proposal.status = "rejected"
        proposal.metadata["governance_status"] = "rejected"
        if reason:
            proposal.metadata["rejection_reason"] = reason
        self.save_node(proposal)
        return True
    
    # Governance methods
    
    def apply_policy(
        self,
        node_id: str,
        policy_id: str,
        enforcement_level: str,
        reason: str,
        confidence: float = 0.7,
    ) -> Optional[Edge]:
        """Apply a policy to a node via governed_by edge."""
        node = self.load_node(node_id)
        if not node:
            return None
        
        policy = self.load_node(policy_id)
        if not policy or policy.node_type != "policy":
            return None
        
        edge = EdgeFactory.create_governed_by(
            source_id=node_id,
            target_id=policy_id,
            enforcement_level=enforcement_level,
            reason=reason,
            confidence=confidence,
        )
        self.save_edge(edge)
        return edge
    
    def validate_node(
        self,
        node_id: str,
        validator_id: str,
        validation_status: str,
        reason: str,
        confidence: float = 0.6,
    ) -> Optional[Edge]:
        """Add validation for a node."""
        node = self.load_node(node_id)
        if not node:
            return None
        
        validator = self.load_node(validator_id)
        if not validator or validator.node_type not in ["capability", "trust_gate"]:
            return None
        
        edge = EdgeFactory.create_validated_by(
            source_id=node_id,
            target_id=validator_id,
            validation_status=validation_status,
            reason=reason,
            confidence=confidence,
        )
        self.save_edge(edge)
        return edge
    
    # Utility methods
    
    def find_node_by_name(self, name: str) -> Optional[Node]:
        """Find a node by name."""
        for node in self._node_cache.values():
            if node.name == name:
                return node
        return None
    
    def find_nodes_by_type(self, node_type: str) -> List[Node]:
        """Find nodes by type."""
        return [node for node in self._node_cache.values() if node.node_type == node_type]
    
    def find_edges_for_node(self, node_id: str) -> List[Edge]:
        """Find all edges for a node (as source or target)."""
        edges = []
        for edge in self._edge_cache.values():
            if edge.source_id == node_id or edge.target_id == node_id:
                edges.append(edge)
        return edges
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "node_count": len(self._node_cache),
            "edge_count": len(self._edge_cache),
            "nodes_by_type": {
                node_type: len([n for n in self._node_cache.values() if n.node_type == node_type])
                for node_type in ["subsystem", "capability", "bottleneck", "policy", "workflow", 
                                 "dependency", "proposal", "research_finding", "trust_gate"]
            },
            "last_updated": self._metadata.get("last_updated", 0),
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_internal_reasoning_store(graph_dir: Path = None) -> InternalReasoningGraphStore:
    """Create a new internal reasoning graph store."""
    return InternalReasoningGraphStore(graph_dir=graph_dir)


def from_scenario(scenario: Dict[str, Any]) -> Node:
    """Create a node from a scenario dict (for testing).
    
    This is purely additive — no migration required.
    """
    return NodeFactory.create_subsystem(
        id=scenario.get("id", "test_node"),
        name=scenario.get("name", "Test Node"),
        description=scenario.get("description", "A test node"),
        node_subtype=scenario.get("subtype"),
        confidence=scenario.get("confidence", 0.5),
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "InternalReasoningGraphStore",
    "create_internal_reasoning_store",
    "from_scenario",
]
