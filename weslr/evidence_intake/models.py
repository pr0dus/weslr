"""Evidence Data Models - Phase A

Evidence assimilation models for external evidence ingestion.
This module defines data structures for evidence sources, normalized evidence, and proposal payloads.

Phase A scope:
- EvidenceSource: External evidence identifier and metadata
- NormalizedEvidence: Standardized evidence format
- EvidenceProposalPayload: Payload for internal reasoning graph proposals

Phase B extensions (in evidence_to_candidate.py):
- CandidateEvidence: Extended evidence with candidate graph references
- CandidateProvenance: Provenance tracking for candidates
- ProposalPayloadWithCandidate: Extended payload with candidate references

Constraints:
- Read-only or operator-facing unless explicitly changed
- No hidden self-application
- No governance engine modification
- Abstract source handling (no parser complexity)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class EvidenceSourceTypeEnum(Enum):
    """Types of evidence sources supported."""
    FILE = "file"
    URL = "url"
    DOCUMENT = "document"


@dataclass
class EvidenceSource:
    """External evidence identifier and metadata.
    
    This model captures metadata about where evidence came from,
    without modifying the internal reasoning graph.
    """
    source_type: EvidenceSourceTypeEnum
    source_reference: str  # File path, URL, or document ID
    timestamp: str  # ISO format timestamp
    extracted_claims: List[str] = field(default_factory=list)
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_type": self.source_type.value,
            "source_reference": self.source_reference,
            "timestamp": self.timestamp,
            "extracted_claims": self.extracted_claims,
            "source_metadata": self.source_metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceSource":
        """Deserialize from dictionary."""
        return cls(
            source_type=EvidenceSourceTypeEnum(data.get("source_type", "file")),
            source_reference=data.get("source_reference", ""),
            timestamp=data.get("timestamp", ""),
            extracted_claims=data.get("extracted_claims", []),
            source_metadata=data.get("source_metadata", {}),
        )


@dataclass
class NormalizedEvidence:
    """Standardized evidence format for internal processing.
    
    This model normalizes evidence from various sources into a consistent
    format that can be used to generate internal reasoning graph proposals.
    """
    source_id: str  # Reference to EvidenceSource
    claim_text: str  # The normalized claim or evidence unit
    confidence_score: Optional[float] = None  # Optional confidence if available
    dependency_ids: List[str] = field(default_factory=list)  # Related evidence IDs
    normalized_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_id": self.source_id,
            "claim_text": self.claim_text,
            "confidence_score": self.confidence_score,
            "dependency_ids": self.dependency_ids,
            "normalized_metadata": self.normalized_metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedEvidence":
        """Deserialize from dictionary."""
        return cls(
            source_id=data.get("source_id", ""),
            claim_text=data.get("claim_text", ""),
            confidence_score=data.get("confidence_score"),
            dependency_ids=data.get("dependency_ids", []),
            normalized_metadata=data.get("normalized_metadata", {}),
        )


@dataclass
class EvidenceProposalPayload:
    """Payload for internal reasoning graph proposal from evidence.
    
    This is a proposal payload only - it does not apply the proposal.
    The proposal must go through GovernanceEngine for explicit approval.
    
    Phase A constraint: No submission/application path - this is pure payload.
    """
    evidence_id: str  # Reference to NormalizedEvidence
    claim_text: str  # The claim to propose for internal reasoning
    source_summary: str  # Summary of the evidence source
    confidence: Optional[float] = None  # Optional confidence
    status: str = "DRAFT"  # Proposal status, DRAFT only in Phase A
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "claim_text": self.claim_text,
            "source_summary": self.source_summary,
            "confidence": self.confidence,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceProposalPayload":
        """Deserialize from dictionary."""
        return cls(
            evidence_id=data.get("evidence_id", ""),
            claim_text=data.get("claim_text", ""),
            source_summary=data.get("source_summary", ""),
            confidence=data.get("confidence"),
            status=data.get("status", "DRAFT"),
        )
