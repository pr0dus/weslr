"""Evidence-to-Candidate Mapping - Phase B

Evidence-to-candidate mapping for evidence assimilation.
This module provides mapping from normalized evidence to internal reasoning graph candidate structures.

Phase B scope:
- CandidateEvidence: Extended evidence with candidate graph references
- ProposalPayloadWithCandidate: Extended proposal payload with candidate references
- EvidenceToCandidateMapper: Map evidence to candidate graph nodes
- EvidenceIngestion.generate_candidate_proposal(): Generate candidate proposal payloads

Constraints:
- No governance engine modification (deferred to Phase B)
- No proposal submission/application path (payload only)
- Candidate references remain clearly provisional
- Thin extensions of existing models
- No second parallel model universe
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .models import NormalizedEvidence, EvidenceProposalPayload, EvidenceSourceTypeEnum, RoutingStatus


@dataclass
class CandidateProvenance:
    """Provenance tracking for candidate evidence.
    
    Tracks the lineage from evidence source to candidate reference.
    """
    source_id: str  # Reference to EvidenceSource in evidence intake
    source_timestamp: str  # Original source timestamp
    normalized_timestamp: str  # When evidence was normalized
    confidence_score: Optional[float] = None  # Confidence from normalization
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_id": self.source_id,
            "source_timestamp": self.source_timestamp,
            "normalized_timestamp": self.normalized_timestamp,
            "confidence_score": self.confidence_score,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateProvenance":
        """Deserialize from dictionary."""
        return cls(
            source_id=data.get("source_id", ""),
            source_timestamp=data.get("source_timestamp", ""),
            normalized_timestamp=data.get("normalized_timestamp", ""),
            confidence_score=data.get("confidence_score"),
        )


@dataclass
class CandidateEvidence:
    """Extended normalized evidence with candidate graph references.
    
    This model extends NormalizedEvidence with candidate node references,
    but they remain clearly provisional - no implication of accepted graph membership.
    """
    source_id: str
    claim_text: str
    confidence_score: Optional[float] = None
    dependency_ids: List[str] = field(default_factory=list)
    normalized_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Candidate-specific fields (provisional references)
    candidate_node_id: Optional[str] = None  # Proposed node ID in graph
    candidate_node_type: Optional[str] = None  # Proposed node type in graph
    candidate_provenance: Optional[CandidateProvenance] = None  # Provenance tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "source_id": self.source_id,
            "claim_text": self.claim_text,
            "confidence_score": self.confidence_score,
            "dependency_ids": self.dependency_ids,
            "normalized_metadata": self.normalized_metadata,
            "candidate_node_id": self.candidate_node_id,
            "candidate_node_type": self.candidate_node_type,
        }
        if self.candidate_provenance:
            data["candidate_provenance"] = self.candidate_provenance.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CandidateEvidence":
        """Deserialize from dictionary."""
        candidate_provenance = None
        if data.get("candidate_provenance"):
            candidate_provenance = CandidateProvenance.from_dict(data["candidate_provenance"])
        
        return cls(
            source_id=data.get("source_id", ""),
            claim_text=data.get("claim_text", ""),
            confidence_score=data.get("confidence_score"),
            dependency_ids=data.get("dependency_ids", []),
            normalized_metadata=data.get("normalized_metadata", {}),
            candidate_node_id=data.get("candidate_node_id"),
            candidate_node_type=data.get("candidate_node_type"),
            candidate_provenance=candidate_provenance,
        )
    
    @classmethod
    def from_normalized_evidence(
        cls,
        normalized: NormalizedEvidence,
        candidate_node_id: Optional[str] = None,
        candidate_node_type: Optional[str] = None,
    ) -> "CandidateEvidence":
        """Create CandidateEvidence from NormalizedEvidence (thin extension)."""
        return cls(
            source_id=normalized.source_id,
            claim_text=normalized.claim_text,
            confidence_score=normalized.confidence_score,
            dependency_ids=normalized.dependency_ids,
            normalized_metadata=normalized.normalized_metadata,
            candidate_node_id=candidate_node_id,
            candidate_node_type=candidate_node_type,
        )


@dataclass
class ProposalPayloadWithCandidate:
    """Extended proposal payload with candidate references.
    
    This extends EvidenceProposalPayload with candidate references,
    preserving the review-gated workflow - no auto-application.
    
    Phase C extension: Routing status tracking for evidence-to-governance workflow.
    """
    evidence_id: str
    claim_text: str
    source_summary: str
    confidence: Optional[float] = None
    status: str = "DRAFT"
    routing_status: str = RoutingStatus.GENERATED.value  # Phase C: routing status
    
    # Candidate-specific fields (provisional references)
    candidate_reference: Optional[str] = None  # Reference to candidate node (node_id or label)
    candidate_node_type: Optional[str] = None  # Proposed node type
    candidate_provenance: Optional[CandidateProvenance] = None  # Provenance tracking
    candidate_confidence: Optional[float] = None  # Confidence in candidate match
    candidate_recency: Optional[str] = None  # Recency indicator (e.g., "recent", "old")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = {
            "evidence_id": self.evidence_id,
            "claim_text": self.claim_text,
            "source_summary": self.source_summary,
            "confidence": self.confidence,
            "status": self.status,
            "candidate_reference": self.candidate_reference,
            "candidate_node_type": self.candidate_node_type,
            "candidate_confidence": self.candidate_confidence,
            "candidate_recency": self.candidate_recency,
        }
        if self.candidate_provenance:
            data["candidate_provenance"] = self.candidate_provenance.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProposalPayloadWithCandidate":
        """Deserialize from dictionary."""
        candidate_provenance = None
        if data.get("candidate_provenance"):
            candidate_provenance = CandidateProvenance.from_dict(data["candidate_provenance"])
        
        return cls(
            evidence_id=data.get("evidence_id", ""),
            claim_text=data.get("claim_text", ""),
            source_summary=data.get("source_summary", ""),
            confidence=data.get("confidence"),
            status=data.get("status", "DRAFT"),
            routing_status=data.get("routing_status", RoutingStatus.GENERATED.value),
            candidate_reference=data.get("candidate_reference"),
            candidate_node_type=data.get("candidate_node_type"),
            candidate_confidence=data.get("candidate_confidence"),
            candidate_recency=data.get("candidate_recency"),
            candidate_provenance=candidate_provenance,
        )
    
    @classmethod
    def from_payload_and_candidate(
        cls,
        payload: EvidenceProposalPayload,
        candidate_reference: str,
        candidate_node_type: str,
        candidate_confidence: Optional[float] = None,
        candidate_recency: Optional[str] = None,
    ) -> "ProposalPayloadWithCandidate":
        """Create ProposalPayloadWithCandidate from EvidenceProposalPayload (thin extension)."""
        return cls(
            evidence_id=payload.evidence_id,
            claim_text=payload.claim_text,
            source_summary=payload.source_summary,
            confidence=payload.confidence,
            status=payload.status,
            candidate_reference=candidate_reference,
            candidate_node_type=candidate_node_type,
            candidate_confidence=candidate_confidence,
            candidate_recency=candidate_recency,
        )
