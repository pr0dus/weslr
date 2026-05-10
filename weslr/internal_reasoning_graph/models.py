"""Internal Reasoning Graph Models

Core data structures for the internal reasoning graph:
- Node: Architecture node (subsystem, capability, bottleneck, policy, workflow, dependency, proposal, research_finding, trust_gate)
- Edge: Typed relationship between nodes
- Governance: Governance status and rules
- Proposal: Architecture change proposal
- Validation: Node validation state

All classes support serialization to/from dict for persistence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class NodeSubtype(str, Enum):
    """Subtypes for node types."""
    # Subsystem subtypes
    SUBSYSTEM = "subsystem"
    
    # Capability subtypes
    DETECTION = "detection"
    NORMALIZATION = "normalization"
    SYNTHESIS = "synthesis"
    ANALYSIS = "analysis"
    SYNTHESIS_PROPOSAL = "synthesis_proposal"
    GOVERNANCE = "governance"
    COMMUNICATION = "communication"
    
    # Bottleneck subtypes
    DETECTION_BOTTLENECK = "detection"
    ANALYSIS_BOTTLENECK = "analysis"
    
    # Policy subtypes
    ACCEPTANCE_POLICY = "acceptance"
    VALIDATION_POLICY = "validation"
    GOVERNANCE_POLICY = "governance"
    
    # Workflow subtypes
    PROPOSAL_WORKFLOW = "proposal"
    VALIDATION_WORKFLOW = "validation"
    
    # Trust gate subtypes
    PROPOSITION_GATE = "proposition"
    MODIFICATION_GATE = "modification"
    PROPOSAL_GATE = "proposal"
    ASSIMILATION_GATE = "assimilation"


class GovernanceStatus(str, Enum):
    """Governance status for proposals and nodes."""
    PENDING = "pending"           # Awaiting governance decision
    APPROVED = "approved"         # Governance approved
    REJECTED = "rejected"         # Governance rejected
    SNOOZED = "snoozed"           # Deferred temporarily
    ARCHIVED = "archived"         # No longer active


class ProposalStatus(str, Enum):
    """Proposal status."""
    PENDING = "pending"           # Created, awaiting review
    REVIEWING = "reviewing"       # Currently being reviewed
    APPROVED = "approved"         # Governance approved
    REJECTED = "rejected"         # Governance rejected
    MERGED = "merged"             # Applied to architecture


class ValidationStatus(str, Enum):
    """Validation status."""
    PENDING = "pending"           # Awaiting validation
    VALID = "valid"               # Passed validation
    INVALID = "invalid"           # Failed validation
    EXPIRED = "expired"           # Validation expired


class EdgeType(str, Enum):
    """Edge types for architecture relationships."""
    # Dependencies
    DEPENDS_ON = "depends_on"
    
    # Relationships
    STRENGTHENS = "strengthens"
    REPLACES = "replaces"
    
    # Bottlenecks
    BOTTLENECK_FOR = "bottleneck_for"
    
    # Governance
    GOVERNED_BY = "governed_by"
    
    # Proposals
    PROPOSES_CHANGE_TO = "proposes_change_to"
    
    # Validation
    VALIDATED_BY = "validated_by"
    
    # Conflicts
    CONFLICTS_WITH = "conflicts_with"


class ChangeType(str, Enum):
    """Types of architectural changes."""
    ADD = "add"
    MODIFY = "modify"
    REMOVE = "remove"
    REPLACE = "replace"


class ConflictType(str, Enum):
    """Types of conflicts between nodes."""
    CONTRADICTION = "contradiction"
    REDUNDANCY = "redundancy"
    INCOMPATIBILITY = "incompatibility"


# ============================================================================
# BASE CLASSES
# ============================================================================


@dataclass
class Evidence:
    """Evidence supporting a node or edge.
    
    Same structure as concept_graph.models.Evidence for compatibility.
    """
    source_id: str
    source_type: str
    content: str
    confidence: float
    timestamp: int
    category: str  # EvidenceCategory.value
    traceable: bool = True
    reason: Optional[str] = None
    source_file: Optional[str] = None
    source_message_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "category": self.category,
            "traceable": self.traceable,
            "reason": self.reason,
            "source_file": self.source_file,
            "source_message_id": self.source_message_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Evidence:
        return cls(
            source_id=data["source_id"],
            source_type=data["source_type"],
            content=data["content"],
            confidence=data["confidence"],
            timestamp=data["timestamp"],
            category=data["category"],
            traceable=data.get("traceable", True),
            reason=data.get("reason"),
            source_file=data.get("source_file"),
            source_message_id=data.get("source_message_id"),
        )
    
    def is_expired(self, max_age_seconds: int = 2592000) -> bool:
        """Check if evidence is expired (default: 30 days)."""
        return time.time() - self.timestamp > max_age_seconds


@dataclass
class Edge:
    """A typed edge between nodes.
    
    Same structure as concept_graph.models.Link for compatibility,
    but with irk-specific metadata.
    """
    source_id: str
    target_id: str
    edge_type: str  # EdgeType.value
    confidence: float
    reason: str
    evidence: List[Evidence]
    created_at: int
    updated_at: int
    is_stale: bool = False
    
    # Edge-specific metadata
    edge_subtype: Optional[str] = None  # e.g., "hard", "soft", "advisory"
    change_type: Optional[str] = None   # e.g., "add", "modify" (for proposes_change_to)
    conflict_type: Optional[str] = None  # e.g., "contradiction" (for conflicts_with)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "confidence": self.confidence,
            "reason": self.reason,
            "evidence": [e.to_dict() for e in self.evidence],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_stale": self.is_stale,
            "edge_subtype": self.edge_subtype,
            "change_type": self.change_type,
            "conflict_type": self.conflict_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Edge:
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=data["edge_type"],
            confidence=data["confidence"],
            reason=data["reason"],
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            is_stale=data.get("is_stale", False),
            edge_subtype=data.get("edge_subtype"),
            change_type=data.get("change_type"),
            conflict_type=data.get("conflict_type"),
        )


@dataclass
class Node:
    """Represents an architecture node in the graph.
    
    Nodes can be:
    - subsystem (general subsystem)
    - capability (specific capability)
    - bottleneck (identified bottleneck)
    - policy (governance policy)
    - workflow (workflow definition)
    - dependency (dependency requirement)
    - proposal (change proposal)
    - research_finding (research finding)
    - trust_gate (governance gate)
    
    All nodes support typed metadata for subtype-specific behavior.
    """
    id: str
    name: str
    description: str
    node_type: str  # e.g., "subsystem", "capability", "bottleneck"
    
    # Basic metadata
    status: str = "active"  # active, deprecated, proposed, rejected
    confidence: float = 0.5
    created_at: int = field(default_factory=lambda: int(time.time()))
    updated_at: int = field(default_factory=lambda: int(int(time.time())))
    
    # Typed metadata
    node_subtype: Optional[str] = None  # e.g., "detection", "validation", "hard"
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Edges and evidence
    edges: List[Edge] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    
    # Governance metadata
    governance_status: str = GovernanceStatus.PENDING.value
    governance_decided_at: Optional[int] = None
    governance_decided_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "node_type": self.node_type,
            "node_subtype": self.node_subtype,
            "status": self.status,
            "version": self.version,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "edges": [e.to_dict() for e in self.edges],
            "evidence": [e.to_dict() for e in self.evidence],
            "governance_status": self.governance_status,
            "governance_decided_at": self.governance_decided_at,
            "governance_decided_by": self.governance_decided_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Node:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            node_type=data["node_type"],
            node_subtype=data.get("node_subtype"),
            status=data.get("status", "active"),
            version=data.get("version"),
            confidence=data.get("confidence", 0.5),
            created_at=data.get("created_at", int(time.time())),
            updated_at=data.get("updated_at", int(time.time())),
            metadata=data.get("metadata", {}),
            edges=[Edge.from_dict(e) for e in data.get("edges", [])],
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            governance_status=data.get("governance_status", GovernanceStatus.PENDING.value),
            governance_decided_at=data.get("governance_decided_at"),
            governance_decided_by=data.get("governance_decided_by"),
        )
    
    def get_edge(self, target_id: str, edge_type: str) -> Optional[Edge]:
        """Get edge to target with specific type."""
        for edge in self.edges:
            if edge.target_id == target_id and edge.edge_type == edge_type:
                return edge
        return None
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to this node."""
        self.edges.append(edge)
        self.updated_at = int(time.time())
    
    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to this node."""
        self.evidence.append(evidence)
        self.updated_at = int(time.time())
        self.confidence = min(1.0, self.confidence * 0.8 + evidence.confidence * 0.2)
    
    def mark_governance(self, status: str, decided_by: Optional[str] = None) -> None:
        """Mark governance status for this node."""
        self.governance_status = status
        self.governance_decided_at = int(time.time())
        self.governance_decided_by = decided_by
        self.updated_at = self.governance_decided_at
    
    def is_stale(self, max_age_seconds: int = 604800) -> bool:
        """Check if node is stale (default: 7 days)."""
        return time.time() - self.updated_at > max_age_seconds


# ============================================================================
# NODE FACTORY METHODS
# ============================================================================


class NodeFactory:
    """Factory for creating architecture nodes with type-specific validation."""
    
    # Validation thresholds
    SUBSYSTEM_CONFIDENCE_THRESHOLD = 0.5
    CAPABILITY_CONFIDENCE_THRESHOLD = 0.6
    BOTTLENECK_SEVERITY_MIN = 0.5
    POLICY_ENFORCEMENT_LEVELS = ["hard", "soft", "advisory"]
    VALIDATION_CONFIDENCE_THRESHOLD = 0.5
    
    # Trust gate requirements
    TRUST_GATE_APPROVAL_REQUIRED = True
    TRUST_GATE_REJECTION_ACTIONS = ["reject", "escalate", "retry"]
    
    @classmethod
    def create_subsystem(
        cls,
        id: str,
        name: str,
        description: str,
        node_subtype: Optional[str] = None,
        version: Optional[str] = None,
        confidence: float = 0.5,
    ) -> Node:
        """Create a subsystem node."""
        if confidence < cls.SUBSYSTEM_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Subsystem confidence must be >= {cls.SUBSYSTEM_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="subsystem",
            node_subtype=node_subtype,
            version=version,
            confidence=confidence,
            status="active",
            metadata={"node_type": "subsystem"},
        )
    
    @classmethod
    def create_capability(
        cls,
        id: str,
        name: str,
        description: str,
        node_subtype: str,
        confidence: float = 0.6,
        evidence_threshold: int = 1,
    ) -> Node:
        """Create a capability node."""
        if confidence < cls.CAPABILITY_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Capability confidence must be >= {cls.CAPABILITY_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="capability",
            node_subtype=node_subtype,
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "capability",
                "evidence_threshold": evidence_threshold,
            },
        )
    
    @classmethod
    def create_bottleneck(
        cls,
        id: str,
        name: str,
        description: str,
        node_subtype: str = "detection",
        severity: str = "medium",
        confidence: float = 0.7,
    ) -> Node:
        """Create a bottleneck node."""
        if confidence < cls.BOTTLENECK_SEVERITY_MIN:
            raise ValueError(f"Bottleneck confidence must be >= {cls.BOTTLENECK_SEVERITY_MIN}")

        if node_subtype not in ["detection", "analysis"]:
            raise ValueError("Bottleneck node_subtype must be 'detection' or 'analysis'")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="bottleneck",
            node_subtype=node_subtype,
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "bottleneck",
                "severity": severity,
            },
        )
    
    @classmethod
    def create_policy(
        cls,
        id: str,
        name: str,
        description: str,
        enforcement_level: str,
        applies_to: List[str],
        confidence: float = 0.8,
    ) -> Node:
        """Create a policy node."""
        if enforcement_level not in cls.POLICY_ENFORCEMENT_LEVELS:
            raise ValueError(f"Enforcement level must be one of: {cls.POLICY_ENFORCEMENT_LEVELS}")
        
        if confidence < cls.SUBSYSTEM_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Policy confidence must be >= {cls.SUBSYSTEM_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="policy",
            node_subtype="acceptance",
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "policy",
                "enforcement_level": enforcement_level,
                "applies_to": applies_to,
            },
        )
    
    @classmethod
    def create_workflow(
        cls,
        id: str,
        name: str,
        description: str,
        steps: List[str],
        governance_required: bool = True,
        confidence: float = 0.7,
    ) -> Node:
        """Create a workflow node."""
        if not steps:
            raise ValueError("Workflow must have at least one step")
        
        if confidence < cls.SUBSYSTEM_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Workflow confidence must be >= {cls.SUBSYSTEM_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="workflow",
            node_subtype="proposal",
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "workflow",
                "steps": steps,
                "governance_required": governance_required,
            },
        )
    
    @classmethod
    def create_dependency(
        cls,
        id: str,
        name: str,
        description: str,
        required_by: str,
        minimum_version: Optional[str] = None,
        confidence: float = 0.6,
    ) -> Node:
        """Create a dependency node."""
        if not required_by:
            raise ValueError("Dependency must specify required_by")
        
        if confidence < cls.SUBSYSTEM_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Dependency confidence must be >= {cls.SUBSYSTEM_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="dependency",
            node_subtype=None,
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "dependency",
                "required_by": required_by,
                "minimum_version": minimum_version,
            },
        )
    
    @classmethod
    def create_proposal(
        cls,
        id: str,
        name: str,
        description: str,
        proposed_by: str,
        proposal_type: str = "architectural",
        confidence: float = 0.5,
        required_governance: str = "operator_review",
    ) -> Node:
        """Create a proposal node."""
        if not proposed_by:
            raise ValueError("Proposal must specify proposed_by")
        
        if required_governance not in ["operator_review", "model_assisted", "none"]:
            raise ValueError(f"Invalid required_governance: {required_governance}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="proposal",
            node_subtype="proposal",
            confidence=confidence,
            status="proposed",
            metadata={
                "node_type": "proposal",
                "proposed_by": proposed_by,
                "proposal_type": proposal_type,
                "required_governance": required_governance,
                "governance_status": "pending",
            },
        )
    
    @classmethod
    def create_research_finding(
        cls,
        id: str,
        name: str,
        description: str,
        source: str,
        confidence: float = 0.6,
    ) -> Node:
        """Create a research finding node."""
        if not source:
            raise ValueError("Research finding must specify source")
        
        if confidence < cls.CAPABILITY_CONFIDENCE_THRESHOLD:
            raise ValueError(f"Research finding confidence must be >= {cls.CAPABILITY_CONFIDENCE_THRESHOLD}")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="research_finding",
            node_subtype="analysis",
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "research_finding",
                "source": source,
            },
        )
    
    @classmethod
    def create_trust_gate(
        cls,
        id: str,
        name: str,
        description: str,
        gate_type: str,
        approval_required: bool = True,
        rejection_action: str = "escalate",
        confidence: float = 0.9,
    ) -> Node:
        """Create a trust gate node."""
        if gate_type not in ["proposition", "modification", "proposal", "assimilation"]:
            raise ValueError(f"Invalid gate_type: {gate_type}")
        
        if rejection_action not in cls.TRUST_GATE_REJECTION_ACTIONS:
            raise ValueError(f"Invalid rejection_action: {rejection_action}")
        
        if confidence < 0.9:
            raise ValueError("Trust gate confidence must be >= 0.9")
        
        return Node(
            id=id,
            name=name,
            description=description,
            node_type="trust_gate",
            node_subtype=gate_type,
            confidence=confidence,
            status="active",
            metadata={
                "node_type": "trust_gate",
                "gate_type": gate_type,
                "approval_required": approval_required,
                "rejection_action": rejection_action,
            },
        )

    @classmethod
    def create_enrichment_gap_record(
        cls,
        id: str,
        name: str,
        description: str,
        source_eval: str,
        category: str,
        current_path: str,
        failure_mode: str,
        missing_skill: str,
        target_substrate: str,
        proposed_enrichment: str,
        legibility_summary: str,
        source_prompt: Optional[str] = None,
        source_prompt_fingerprint: Optional[str] = None,
        evidence_refs: Optional[List[str]] = None,
        before_score: Optional[float] = None,
        after_score: Optional[float] = None,
        affected_node_ids: Optional[List[str]] = None,
        status: str = "observed",
        operator_review_required: bool = True,
        read_only: bool = True,
        severity: str = "medium",
        confidence: float = 0.7,
    ) -> Node:
        """Create a legible enrichment-gap record on the existing graph substrate."""
        required_fields = {
            "source_eval": source_eval,
            "category": category,
            "current_path": current_path,
            "failure_mode": failure_mode,
            "missing_skill": missing_skill,
            "target_substrate": target_substrate,
            "proposed_enrichment": proposed_enrichment,
            "legibility_summary": legibility_summary,
        }
        for field_name, value in required_fields.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Enrichment gap record must specify {field_name}")

        valid_statuses = ["observed", "triaged", "proposed", "accepted", "implemented", "rejected"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid enrichment gap status: {status}")

        if source_prompt and not source_prompt_fingerprint:
            raise ValueError("source_prompt_fingerprint is required when source_prompt is stored")

        node = cls.create_bottleneck(
            id=id,
            name=name,
            description=description,
            node_subtype="analysis",
            severity=severity,
            confidence=confidence,
        )
        node.metadata.update({
            "record_kind": "enrichment_gap",
            "record_type": "enrichment_gap",
            "gap_id": id,
            "source_eval": source_eval,
            "source_prompt": source_prompt,
            "source_prompt_fingerprint": source_prompt_fingerprint,
            "category": category,
            "current_path": current_path,
            "failure_mode": failure_mode,
            "missing_skill": missing_skill,
            "target_substrate": target_substrate,
            "proposed_enrichment": proposed_enrichment,
            "evidence_refs": evidence_refs or [],
            "before_score": before_score,
            "after_score": after_score,
            "status": status,
            "operator_review_required": operator_review_required,
            "read_only": read_only,
            "legibility_summary": legibility_summary,
            "created_at": node.created_at,
            "affected_node_ids": affected_node_ids or [],
            "execution_allowed": False,
            "graph_links": {},
        })
        return node

    @classmethod
    def create_enrichment_record(
        cls,
        id: str,
        name: str,
        description: str,
        proposed_by: str,
        target_node_ids: List[str],
        gap_id: Optional[str] = None,
        enrichment_type: str = "capability",
        confidence: float = 0.6,
        required_governance: str = "operator_review",
    ) -> Node:
        """Create an explicit enrichment proposal record within the existing graph."""
        if not target_node_ids:
            raise ValueError("Enrichment record must specify target_node_ids")

        node = cls.create_proposal(
            id=id,
            name=name,
            description=description,
            proposed_by=proposed_by,
            proposal_type=enrichment_type,
            confidence=confidence,
            required_governance=required_governance,
        )
        node.metadata.update({
            "record_kind": "enrichment_record",
            "target_node_ids": target_node_ids,
            "gap_id": gap_id,
        })
        return node


# ============================================================================
# EDGE FACTORY METHODS
# ============================================================================


class EdgeFactory:
    """Factory for creating architecture edges with type-specific validation."""
    
    # Default confidence thresholds
    DEFAULT_CONFIDENCE_THRESHOLD = 0.6
    
    @classmethod
    def create_depends_on(
        cls,
        source_id: str,
        target_id: str,
        reason: str,
        confidence: float = 0.7,
    ) -> Edge:
        """Create a depends_on edge."""
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="depends_on",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
    
    @classmethod
    def create_strengthens(
        cls,
        source_id: str,
        target_id: str,
        reason: str,
        confidence: float = 0.6,
    ) -> Edge:
        """Create a strengthens edge."""
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="strengthens",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
    
    @classmethod
    def create_replaces(
        cls,
        source_id: str,
        target_id: str,
        reason: str,
        confidence: float = 0.8,
    ) -> Edge:
        """Create a replaces edge (high-risk)."""
        if confidence < 0.8:
            raise ValueError("Replaces edge requires confidence >= 0.8")
        
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="replaces",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
    
    @classmethod
    def create_bottleneck_for(
        cls,
        source_id: str,
        target_id: str,
        severity: str,
        reason: str,
        confidence: float = 0.7,
    ) -> Edge:
        """Create a bottleneck_for edge."""
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="bottleneck_for",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
            edge_subtype=severity,
        )
    
    @classmethod
    def create_governed_by(
        cls,
        source_id: str,
        target_id: str,
        enforcement_level: str,
        reason: str,
        confidence: float = 0.7,
    ) -> Edge:
        """Create a governed_by edge."""
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="governed_by",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
            edge_subtype=enforcement_level,
        )
    
    @classmethod
    def create_proposes_change_to(
        cls,
        source_id: str,
        target_id: str,
        change_type: str,
        reason: str,
        confidence: float = 0.6,
        proposed_value: Optional[str] = None,
    ) -> Edge:
        """Create a proposes_change_to edge."""
        if change_type not in ["add", "modify", "remove", "replace"]:
            raise ValueError(f"Invalid change_type: {change_type}")
        
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="proposes_change_to",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
            edge_subtype=change_type,
            change_type=change_type,
        )
    
    @classmethod
    def create_validated_by(
        cls,
        source_id: str,
        target_id: str,
        validation_status: str,
        reason: str,
        confidence: float = 0.6,
    ) -> Edge:
        """Create a validated_by edge."""
        if validation_status not in ["valid", "invalid", "pending"]:
            raise ValueError(f"Invalid validation_status: {validation_status}")
        
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="validated_by",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
            edge_subtype=validation_status,
        )
    
    @classmethod
    def create_conflicts_with(
        cls,
        source_id: str,
        target_id: str,
        conflict_type: str,
        reason: str,
        confidence: float = 0.7,
    ) -> Edge:
        """Create a conflicts_with edge (high-risk)."""
        if conflict_type not in ["contradiction", "redundancy", "incompatibility"]:
            raise ValueError(f"Invalid conflict_type: {conflict_type}")
        
        if confidence < 0.7:
            raise ValueError("Conflicts_with edge requires confidence >= 0.7")
        
        return Edge(
            source_id=source_id,
            target_id=target_id,
            edge_type="conflicts_with",
            confidence=confidence,
            reason=reason,
            evidence=[],
            created_at=int(time.time()),
            updated_at=int(time.time()),
            edge_subtype=conflict_type,
            conflict_type=conflict_type,
        )


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


class NodeValidator:
    """Validator for architecture nodes."""
    
    @classmethod
    def validate_node(cls, node: Node) -> Tuple[bool, str]:
        """Validate a node."""
        # Check required fields
        if not node.id:
            return False, "Node id is required"
        
        if not node.name:
            return False, "Node name is required"
        
        if not node.description:
            return False, "Node description is required"
        
        # Check node type
        valid_types = ["subsystem", "capability", "bottleneck", "policy", 
                       "workflow", "dependency", "proposal", "research_finding", "trust_gate"]
        if node.node_type not in valid_types:
            return False, f"Invalid node_type: {node.node_type}"
        
        # Check confidence
        if not (0.0 <= node.confidence <= 1.0):
            return False, "Node confidence must be between 0.0 and 1.0"
        
        # Check status
        valid_statuses = ["active", "deprecated", "proposed", "rejected"]
        if node.status not in valid_statuses:
            return False, f"Invalid status: {node.status}"
        
        # Check governance status
        valid_governance = ["pending", "approved", "rejected", "snoozed", "archived"]
        if node.governance_status not in valid_governance:
            return False, f"Invalid governance_status: {node.governance_status}"
        
        return True, "Valid"
    
    @classmethod
    def validate_node_subtype(cls, node: Node) -> Tuple[bool, str]:
        """Validate node subtype."""
        node_type = node.node_type
        node_subtype = node.node_subtype
        
        # Define valid subtypes per node type
        valid_subtypes = {
            "subsystem": [None, "subsystem"],
            "capability": ["detection", "normalization", "synthesis", "analysis", 
                          "synthesis_proposal", "governance", "communication"],
            "bottleneck": ["detection", "analysis"],
            "policy": ["acceptance", "validation", "governance"],
            "workflow": ["proposal", "validation"],
            "dependency": [None],
            "proposal": ["proposal"],
            "research_finding": ["analysis"],
            "trust_gate": ["proposition", "modification", "proposal", "assimilation"],
        }
        
        valid = valid_subtypes.get(node_type, [])
        if node_subtype not in valid:
            return False, f"Invalid node_subtype '{node_subtype}' for node_type '{node_type}'"
        
        return True, "Valid"
    
    @classmethod
    def validate_proposal(cls, node: Node) -> Tuple[bool, str]:
        """Validate a proposal node."""
        valid, reason = cls.validate_node(node)
        if not valid:
            return valid, reason
        
        if node.node_type != "proposal":
            return False, "Node is not a proposal"
        
        metadata = node.metadata or {}
        if "proposed_by" not in metadata:
            return False, "Proposal must have proposed_by in metadata"
        
        return True, "Valid"
    
    @classmethod
    def validate_trust_gate(cls, node: Node) -> Tuple[bool, str]:
        """Validate a trust gate node."""
        valid, reason = cls.validate_node(node)
        if not valid:
            return valid, reason
        
        if node.node_type != "trust_gate":
            return False, "Node is not a trust gate"
        
        if node.confidence < 0.9:
            return False, "Trust gate must have confidence >= 0.9"
        
        metadata = node.metadata or {}
        gate_type = metadata.get("gate_type")
        if gate_type not in ["proposition", "modification", "proposal", "assimilation"]:
            return False, f"Invalid trust_gate type: {gate_type}"
        
        return True, "Valid"

    @classmethod
    def validate_record_metadata(cls, node: Node) -> Tuple[bool, str]:
        """Validate structured metadata for enrichment records stored in existing node types."""
        metadata = node.metadata or {}
        record_kind = metadata.get("record_kind")

        if record_kind == "enrichment_gap":
            if node.node_type != "bottleneck":
                return False, "Enrichment gap records must use node_type 'bottleneck'"
            required_fields = [
                "record_type",
                "gap_id",
                "source_eval",
                "category",
                "current_path",
                "failure_mode",
                "missing_skill",
                "target_substrate",
                "proposed_enrichment",
                "status",
                "operator_review_required",
                "read_only",
                "legibility_summary",
                "created_at",
            ]
            for field_name in required_fields:
                if field_name not in metadata:
                    return False, f"Enrichment gap record requires metadata.{field_name}"

            valid_statuses = ["observed", "triaged", "proposed", "accepted", "implemented", "rejected"]
            if metadata.get("status") not in valid_statuses:
                return False, "Enrichment gap record has invalid metadata.status"
            if metadata.get("record_type") != "enrichment_gap":
                return False, "Enrichment gap record metadata.record_type must be 'enrichment_gap'"
            if metadata.get("operator_review_required") is not True:
                return False, "Enrichment gap record must require operator review"
            if metadata.get("read_only") is not True:
                return False, "Enrichment gap record helpers must remain read_only"
            if metadata.get("source_prompt") and not metadata.get("source_prompt_fingerprint"):
                return False, "Stored source_prompt requires metadata.source_prompt_fingerprint"

        if record_kind == "enrichment_record":
            if node.node_type != "proposal":
                return False, "Enrichment records must use node_type 'proposal'"
            if not metadata.get("target_node_ids"):
                return False, "Enrichment record requires metadata.target_node_ids"

        return True, "Valid"


class EdgeValidator:
    """Validator for architecture edges."""
    
    @classmethod
    def validate_edge(cls, edge: Edge) -> Tuple[bool, str]:
        """Validate an edge."""
        # Check required fields
        if not edge.source_id:
            return False, "Edge source_id is required"
        
        if not edge.target_id:
            return False, "Edge target_id is required"
        
        if not edge.edge_type:
            return False, "Edge edge_type is required"
        
        if not edge.reason:
            return False, "Edge reason is required"
        
        # Check edge type
        valid_types = ["depends_on", "strengthens", "replaces", "bottleneck_for",
                      "governed_by", "proposes_change_to", "validated_by", "conflicts_with"]
        if edge.edge_type not in valid_types:
            return False, f"Invalid edge_type: {edge.edge_type}"
        
        # Check confidence
        if not (0.0 <= edge.confidence <= 1.0):
            return False, "Edge confidence must be between 0.0 and 1.0"
        
        # High-risk edges require higher confidence
        high_risk_types = ["replaces", "conflicts_with"]
        if edge.edge_type in high_risk_types and edge.confidence < 0.8:
            return False, f"High-risk edge '{edge.edge_type}' requires confidence >= 0.8"
        
        return True, "Valid"
    
    @classmethod
    def validate_edge_subtype(cls, edge: Edge) -> Tuple[bool, str]:
        """Validate edge subtype based on edge type."""
        edge_type = edge.edge_type
        edge_subtype = edge.edge_subtype
        
        # Define valid subtypes per edge type
        valid_subtypes = {
            "bottleneck_for": ["critical", "high", "medium", "low"],
            "governed_by": ["hard", "soft", "advisory"],
            "proposes_change_to": ["add", "modify", "remove", "replace"],
            "validated_by": ["valid", "invalid", "pending"],
            "conflicts_with": ["contradiction", "redundancy", "incompatibility"],
            "depends_on": [None],
            "strengthens": [None],
            "replaces": [None],
        }
        
        valid = valid_subtypes.get(edge_type, [])
        if edge_subtype is not None and edge_subtype not in valid:
            return False, f"Invalid edge_subtype '{edge_subtype}' for edge_type '{edge_type}'"
        
        return True, "Valid"
    
    @classmethod
    def validate_high_risk_edge(cls, edge: Edge) -> Tuple[bool, str]:
        """Validate high-risk edges require governance approval."""
        high_risk_types = ["replaces", "conflicts_with"]
        
        if edge.edge_type in high_risk_types:
            if edge.confidence < 0.8:
                return False, "High-risk edge requires confidence >= 0.8"
            
            # In production, would check governance approval
            # For now, just log warning
            pass
        
        return True, "Valid"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "Node",
    "Edge",
    "Evidence",
    "NodeSubtype",
    "GovernanceStatus",
    "ProposalStatus",
    "ValidationStatus",
    "EdgeType",
    "ChangeType",
    "ConflictType",
    "NodeFactory",
    "EdgeFactory",
    "NodeValidator",
    "EdgeValidator",
]
