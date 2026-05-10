"""Internal Reasoning Graph Query Engine

v94b Phase B — Reasoning Queries

Query Layer:
  - Bottleneck Tracing: Find chains of bottlenecks from subsystem to root cause
  - Dependency Impact Analysis: Trace downstream effects of node changes
  - Proposal Impact Analysis: Trace affected nodes from proposals
  - Architecture Gap Detection: Identify missing capabilities, unmet dependencies
  - Governance Blocking Queries: Find nodes blocked by policy/governance status

Constraints:
  - Read-only queries only (no silent mutation)
  - Governance-aware (check governance status before reporting)
  - Proposal-aware (include pending proposals in impact analysis)
  - Evidence-backed (include confidence scores, evidence sources)
  - No integration hooks yet (pure query layer)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .models import Node, Edge, NodeFactory, GovernanceStatus
from .store import InternalReasoningGraphStore


# ============================================================================
# QUERY RESULT DATACLASSES
# ============================================================================


@dataclass
class BottleneckTrace:
    """Trace of bottlenecks from target to root cause."""
    target_node_id: str
    target_name: str
    bottleneck_chain: List[Dict[str, Any]]  # [(node_id, name, severity), ...]
    evidence: List[Any] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_node_id": self.target_node_id,
            "target_name": self.target_name,
            "bottleneck_chain": self.bottleneck_chain,
            "evidence": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.evidence],
            "confidence": self.confidence,
        }


@dataclass
class ImpactAnalysis:
    """Impact analysis for a node change."""
    affected_node_id: str
    affected_name: str
    impact_type: str  # "direct", "indirect", "propagation"
    affected_edges: List[Dict[str, Any]]  # [(source, target, edge_type), ...]
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "affected_node_id": self.affected_node_id,
            "affected_name": self.affected_name,
            "impact_type": self.impact_type,
            "affected_edges": self.affected_edges,
            "confidence": self.confidence,
        }


@dataclass
class GapReport:
    """Architecture gap detection report."""
    gap_id: str
    gap_type: str  # "capability", "dependency", "policy"
    affected_nodes: List[str]
    suggested_proposals: List[Dict[str, Any]]  # Structured candidate proposals
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type,
            "affected_nodes": self.affected_nodes,
            "suggested_proposals": self.suggested_proposals,
            "confidence": self.confidence,
        }


@dataclass
class GovernanceBlock:
    """Governance blocking status for a node."""
    node_id: str
    node_name: str
    blocked_status: str  # "proposed", "rejected", "pending"
    blocking_policy: Optional[str] = None
    reason: Optional[str] = None
    blocking_edges: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "blocked_status": self.blocked_status,
            "blocking_policy": self.blocking_policy,
            "reason": self.reason,
            "blocking_edges": self.blocking_edges,
        }


# ============================================================================
# QUERY ENGINE
# ============================================================================


class InternalReasoningGraphQuery:
    """Query engine for internal reasoning graph.
    
    Provides read-only queries over the graph with governance awareness.
    All queries are explanatory only — no mutation allowed.
    """
    
    def __init__(self, store: InternalReasoningGraphStore):
        """Initialize query engine with store."""
        self.store = store
    
    # --------------------------------------------------------------------------
    # BOTTLENECK TRACING
    # --------------------------------------------------------------------------
    
    def trace_bottlenecks(self, node_id: str, max_depth: int = 10) -> Optional[BottleneckTrace]:
        """Trace bottleneck chain from target to root cause.
        
        Follows bottleneck_for edges to find root cause bottlenecks.
        Returns None if node has no bottleneck chain.
        """
        # Load node with edges
        node = self.store.load_node(node_id, include_edges=True)
        if not node:
            return None
        
        # Find bottleneck_for edges
        bottleneck_edges = [
            e for e in node.edges
            if e.edge_type == "bottleneck_for"
        ]
        
        if not bottleneck_edges:
            return None
        
        # Build bottleneck chain
        bottleneck_chain = []
        current_depth = 0
        visited = {node_id}
        
        while bottleneck_edges and current_depth < max_depth:
            # Get bottleneck nodes from edges
            for edge in bottleneck_edges:
                bottleneck_node = self.store.load_node(edge.target_id, include_edges=True)
                if bottleneck_node and bottleneck_node.node_type == "bottleneck":
                    if bottleneck_node.id not in visited:
                        visited.add(bottleneck_node.id)
                        bottleneck_chain.append({
                            "node_id": bottleneck_node.id,
                            "name": bottleneck_node.name,
                            "severity": bottleneck_node.metadata.get("severity", "unknown"),
                        })
                        
                        # Find more bottleneck_for edges from this bottleneck
                        for next_edge in bottleneck_node.edges:
                            if next_edge.edge_type == "bottleneck_for":
                                next_bottleneck = self.store.load_node(
                                    next_edge.target_id, include_edges=True
                                )
                                if next_bottleneck and next_bottleneck.node_type == "bottleneck":
                                    if next_bottleneck.id not in visited:
                                        visited.add(next_bottleneck.id)
                                        bottleneck_chain.append({
                                            "node_id": next_bottleneck.id,
                                            "name": next_bottleneck.name,
                                            "severity": next_bottleneck.metadata.get("severity", "unknown"),
                                        })
            
            current_depth += 1
            bottleneck_edges = []
        
        # Calculate confidence based on chain length and evidence
        confidence = min(1.0, 0.5 + (len(bottleneck_chain) * 0.1))
        
        return BottleneckTrace(
            target_node_id=node_id,
            target_name=node.name,
            bottleneck_chain=bottleneck_chain,
            confidence=confidence,
        )
    
    # --------------------------------------------------------------------------
    # DEPENDENCY IMPACT ANALYSIS
    # --------------------------------------------------------------------------
    
    def analyze_dependency_impact(self, node_id: str) -> List[ImpactAnalysis]:
        """Analyze downstream impact of node changes."""
        node = self.store.load_node(node_id, include_edges=True)
        if not node:
            return []
        
        # Find depends_on edges where this node is source
        dependency_edges = [
            e for e in node.edges
            if e.edge_type == "depends_on"
        ]
        
        impacts = []
        for edge in dependency_edges:
            dependent_node = self.store.load_node(edge.target_id, include_edges=True)
            if dependent_node:
                impacts.append(ImpactAnalysis(
                    affected_node_id=dependent_node.id,
                    affected_name=dependent_node.name,
                    impact_type="direct",
                    affected_edges=[{
                        "source": node_id,
                        "target": edge.target_id,
                        "edge_type": edge.edge_type,
                    }],
                    confidence=edge.confidence,
                ))
        
        return impacts
    
    # --------------------------------------------------------------------------
    # PROPOSAL IMPACT ANALYSIS
    # --------------------------------------------------------------------------
    
    def analyze_proposal_impact(self, proposal_id: str) -> List[ImpactAnalysis]:
        """Analyze impact of a proposal on affected nodes."""
        proposal = self.store.load_node(proposal_id, include_edges=True)
        if not proposal:
            return []
        
        # Find proposes_change_to edges
        proposal_edges = [
            e for e in proposal.edges
            if e.edge_type == "proposes_change_to"
        ]
        
        impacts = []
        for edge in proposal_edges:
            affected_node = self.store.load_node(edge.target_id, include_edges=True)
            if affected_node:
                impacts.append(ImpactAnalysis(
                    affected_node_id=affected_node.id,
                    affected_name=affected_node.name,
                    impact_type="propagation",
                    affected_edges=[{
                        "source": proposal_id,
                        "target": edge.target_id,
                        "edge_type": edge.edge_type,
                        "change_type": edge.change_type,
                    }],
                    confidence=edge.confidence,
                ))
        
        return impacts
    
    # --------------------------------------------------------------------------
    # ARCHITECTURE GAP DETECTION
    # --------------------------------------------------------------------------
    
    def detect_architecture_gaps(self) -> List[GapReport]:
        """Detect architecture gaps: missing capabilities, unmet dependencies, explicit enrichment gaps."""
        gaps = []
        gap_id = 0
        
        # Get all nodes
        all_nodes = self.store.list_nodes()
        all_nodes_dict = {n.id: n for n in all_nodes}

        # Include explicit enrichment gap records already stored in the graph
        for node in all_nodes:
            metadata = node.metadata or {}
            if node.node_type == "bottleneck" and metadata.get("record_kind") == "enrichment_gap":
                gap_id += 1
                affected_nodes = metadata.get("affected_node_ids") or []
                target_substrate_node_id = metadata.get("graph_links", {}).get("target_substrate_node_id")
                if target_substrate_node_id and target_substrate_node_id not in affected_nodes:
                    affected_nodes = affected_nodes + [target_substrate_node_id]
                gaps.append(GapReport(
                    gap_id=node.id,
                    gap_type=metadata.get("category", "capability"),
                    affected_nodes=affected_nodes,
                    suggested_proposals=[{
                        "proposal_name": metadata.get("proposed_enrichment", f"Address enrichment gap: {node.name}"),
                        "proposal_description": metadata.get("legibility_summary", node.description),
                        "confidence": node.confidence,
                        "source_eval": metadata.get("source_eval"),
                        "before_score": metadata.get("before_score"),
                        "after_score": metadata.get("after_score"),
                        "failure_mode": metadata.get("failure_mode"),
                        "target_substrate": metadata.get("target_substrate"),
                    }],
                    confidence=node.confidence,
                ))
        
        # Check for nodes with unmet dependencies
        for node in all_nodes:
            if node.node_type in ["subsystem", "capability"]:
                # Check for depends_on edges to missing nodes
                for edge in node.edges:
                    if edge.edge_type == "depends_on":
                        if edge.target_id not in all_nodes_dict:
                            gap_id += 1
                            gaps.append(GapReport(
                                gap_id=f"gap_{gap_id}",
                                gap_type="dependency",
                                affected_nodes=[node.id],
                                suggested_proposals=[{
                                    "proposal_name": f"Add missing dependency: {edge.target_id}",
                                    "proposal_description": f"Add dependency node for {edge.target_id}",
                                    "confidence": edge.confidence,
                                }],
                                confidence=edge.confidence,
                            ))
        
        # Check for capability gaps (nodes without required subtypes)
        for node in all_nodes:
            if node.node_type == "capability":
                required_subtype = node.metadata.get("required_subtype")
                if required_subtype and node.node_subtype != required_subtype:
                    gap_id += 1
                    gaps.append(GapReport(
                        gap_id=f"gap_{gap_id}",
                        gap_type="capability",
                        affected_nodes=[node.id],
                        suggested_proposals=[{
                            "proposal_name": f"Update capability: {node.name}",
                            "proposal_description": f"Update node_subtype to {required_subtype}",
                            "confidence": 0.8,
                        }],
                        confidence=0.8,
                    ))
        
        return gaps
    
    # --------------------------------------------------------------------------
    # GOVERNANCE BLOCKING QUERIES
    # --------------------------------------------------------------------------
    
    def get_enrichment_gap_records(self) -> List[GapReport]:
        """Return explicit enrichment gap records as read-only gap reports."""
        explicit_gap_ids = {node.id for node in self.store.get_enrichment_gap_records()}
        return [
            gap for gap in self.detect_architecture_gaps()
            if gap.gap_id in explicit_gap_ids
        ]

    def get_enrichment_records(self) -> List[Node]:
        """Return explicit enrichment proposal records."""
        return self.store.get_enrichment_records()

    def get_governance_blocking(self, node_id: str) -> Optional[GovernanceBlock]:
        """Get governance blocking status for a node.
        
        Returns blocking information but does NOT alter proposal/governance state.
        """
        node = self.store.load_node(node_id, include_edges=True)
        if not node:
            return None
        
        # Find governing edges (only return block if there's an actual policy)
        governing_edges = [
            e for e in node.edges
            if e.edge_type == "governed_by"
        ]
        
        if not governing_edges:
            return None
        
        # Only return block if node has governance status
        if node.governance_status not in [GovernanceStatus.PENDING.value, GovernanceStatus.REJECTED.value]:
            return None
        
        blocking_policy = None
        reason = None
        policy_node = self.store.load_node(governing_edges[0].target_id)
        if policy_node:
            blocking_policy = policy_node.name
            reason = f"Governed by {policy_node.name}"
        
        return GovernanceBlock(
            node_id=node_id,
            node_name=node.name,
            blocked_status=node.governance_status,
            blocking_policy=blocking_policy,
            reason=reason,
            blocking_edges=[e.to_dict() for e in governing_edges],
        )
    
    def get_all_governance_blocked(self) -> List[GovernanceBlock]:
        """Get all nodes with governance blocking status."""
        blocked = []
        
        for node in self.store.list_nodes():
            block = self.get_governance_blocking(node.id)
            if block:
                blocked.append(block)
        
        return blocked
    
    # --------------------------------------------------------------------------
    # UTILITY METHODS
    # --------------------------------------------------------------------------
    
    def export_query_results(self, results: Any) -> Dict[str, Any]:
        """Export query results as JSON for operator review.
        
        This is read-only export only — no mutation.
        """
        if isinstance(results, BottleneckTrace):
            return {"type": "bottleneck_trace", "data": results.to_dict()}
        elif isinstance(results, ImpactAnalysis):
            return {"type": "impact_analysis", "data": results.to_dict()}
        elif isinstance(results, GapReport):
            return {"type": "gap_report", "data": results.to_dict()}
        elif isinstance(results, GovernanceBlock):
            return {"type": "governance_block", "data": results.to_dict()}
        elif isinstance(results, list):
            if results and isinstance(results[0], BottleneckTrace):
                return {"type": "bottleneck_traces", "data": [r.to_dict() for r in results]}
            elif results and isinstance(results[0], ImpactAnalysis):
                return {"type": "impact_analyses", "data": [r.to_dict() for r in results]}
            elif results and isinstance(results[0], GapReport):
                return {"type": "gap_reports", "data": [r.to_dict() for r in results]}
            elif results and isinstance(results[0], GovernanceBlock):
                return {"type": "governance_blocks", "data": [r.to_dict() for r in results]}
        
        return {"type": "unknown", "data": str(results)}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_query_engine(store: InternalReasoningGraphStore) -> InternalReasoningGraphQuery:
    """Create a new query engine with the given store."""
    return InternalReasoningGraphQuery(store)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "InternalReasoningGraphQuery",
    "BottleneckTrace",
    "ImpactAnalysis",
    "GapReport",
    "GovernanceBlock",
    "create_query_engine",
]
