"""Evidence Ontology / Trust Anchor Layer (v20)

Lightweight, extensible evidence-governance substrate that strengthens
the governance spine and prepares WESLR for domain specialization.

Architecture:
  - Evidence types, statuses, and sources (enums)
  - EvidenceClaim — atomic unit of truth with provenance
  - EvidenceAttestation — operator or system attestation of claim validity
  - Integration hooks for change proposals and governance views

Rules:
  - Additive only (no breaking changes)
  - Reversible (single file removal)
  - Domain-agnostic by design (domains added via tags)
  - No runtime redesign required (pure data model expansion)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class EvidenceType(str, Enum):
    """Types of evidence claims."""
    OBSERVATION = "observation"
    MEASUREMENT = "measurement"
    ANALYSIS = "analysis"
    INTERPRETATION = "interpretation"
    PREDICTION = "prediction"
    FORECAST = "forecast"
    VALIDATION = "validation"
    REJECTION = "rejection"
    EXPERIMENT = "experiment"
    DOCUMENTATION = "documentation"
    AUDIT_LOG = "audit_log"
    OTHER = "other"


class EvidenceStatus(str, Enum):
    """Status of an evidence claim."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class EvidenceSource(str, Enum):
    """Source of evidence."""
    HUMAN_OPERATOR = "human_operator"
    AUTOMATED_SENSOR = "automated_sensor"
    EXTERNAL_API = "external_api"
    LLM_INTERPRETATION = "llm_interpretation"
    MODEL_SIMULATION = "model_simulation"
    DOCUMENTATION = "documentation"
    AUDIT_SYSTEM = "audit_system"
    OTHER = "other"


class AttestationType(str, Enum):
    """Type of attestation."""
    SIGNATURE = "signature"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    REVIEW = "review"
    APPROVAL = "approval"
    CONCURRENCE = "concurrence"


class AttestationStatus(str, Enum):
    """Status of an attestation."""
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class EvidenceClaim:
    """A single evidence claim with full provenance tracking.
    
    The atomic unit of truth in the trust anchor layer.
    """
    claim_id: str
    text: str
    summary: str = ""
    
    # Classification
    evidence_type: str = EvidenceType.OTHER.value
    evidence_source: str = EvidenceSource.OTHER.value
    status: str = EvidenceStatus.DRAFT.value
    
    # Provenance
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    source_ref: Optional[str] = None  # External reference ID if applicable
    
    # Context
    domain_tags: List[str] = field(default_factory=list)  # e.g., "hospital", "aerospace", "education"
    confidence_basis: Optional[str] = None  # Brief explanation of confidence level
    confidence_score: Optional[float] = None  # 0.0-1.0 numeric score
    
    # Metadata
    parent_claim_id: Optional[str] = None  # For claim chains/derivations
    related_claims: List[str] = field(default_factory=list)  # Related claim IDs
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "summary": self.summary,
            "evidence_type": self.evidence_type,
            "evidence_source": self.evidence_source,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "source_ref": self.source_ref,
            "domain_tags": self.domain_tags,
            "confidence_basis": self.confidence_basis,
            "confidence_score": self.confidence_score,
            "parent_claim_id": self.parent_claim_id,
            "related_claims": self.related_claims,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceClaim:
        """Create from dictionary representation."""
        data["domain_tags"] = data.get("domain_tags", [])
        data["related_claims"] = data.get("related_claims", [])
        return cls(**data)
    
    def update(self, **kwargs) -> EvidenceClaim:
        """Update claim with new values and refresh timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def add_domain(self, domain: str) -> EvidenceClaim:
        """Add a domain tag."""
        if domain not in self.domain_tags:
            self.domain_tags.append(domain)
        return self
    
    def set_status(self, new_status: str) -> EvidenceClaim:
        """Update status and refresh timestamp."""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


@dataclass
class EvidenceAttestation:
    """An attestation of an evidence claim's validity or value.
    
    Operator or system attestation that supports or challenges a claim.
    """
    attestation_id: str
    claim_id: str
    attestation_type: str = AttestationType.REVIEW.value
    attestation_status: str = AttestationStatus.PENDING.value
    
    # Attestor
    attested_by: Optional[str] = None  # "operator" or system identifier
    attested_at: Optional[str] = None
    
    # Evidence
    evidence: Optional[str] = None  # Supporting evidence for the attestation
    rationale: Optional[str] = None  # Explanation for the attestation
    
    # Lifecycle
    revoked_at: Optional[str] = None
    revoked_by: Optional[str] = None
    expiry_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "attestation_id": self.attestation_id,
            "claim_id": self.claim_id,
            "attestation_type": self.attestation_type,
            "attestation_status": self.attestation_status,
            "attested_by": self.attested_by,
            "attested_at": self.attested_at,
            "evidence": self.evidence,
            "rationale": self.rationale,
            "revoked_at": self.revoked_at,
            "revoked_by": self.revoked_by,
            "expiry_at": self.expiry_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceAttestation:
        """Create from dictionary representation."""
        return cls(**data)
    
    def activate(self, attested_by: str, evidence: str = "", rationale: str = "") -> EvidenceAttestation:
        """Activate attestation."""
        self.attestation_status = AttestationStatus.ACTIVE.value
        self.attested_by = attested_by
        self.attested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.evidence = evidence
        self.rationale = rationale
        return self
    
    def revoke(self, revoked_by: str, rationale: str = "") -> EvidenceAttestation:
        """Revoke attestation."""
        self.attestation_status = AttestationStatus.REVOKED.value
        self.revoked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.revoked_by = revoked_by
        if not self.rationale:
            self.rationale = rationale
        return self
    
    def expire(self) -> EvidenceAttestation:
        """Mark attestation as expired."""
        self.attestation_status = AttestationStatus.EXPIRED.value
        return self


@dataclass
class EvidenceChain:
    """A chain of evidence claims and attestations.
    
    Represents the full provenance trail for a single line of reasoning.
    """
    chain_id: str
    root_claim_id: str
    claims: List[EvidenceClaim] = field(default_factory=list)
    attestations: List[EvidenceAttestation] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "chain_id": self.chain_id,
            "root_claim_id": self.root_claim_id,
            "claims": [c.to_dict() for c in self.claims],
            "attestations": [a.to_dict() for a in self.attestations],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceChain:
        """Create from dictionary representation."""
        data["claims"] = [EvidenceClaim.from_dict(c) for c in data.get("claims", [])]
        data["attestations"] = [EvidenceAttestation.from_dict(a) for a in data.get("attestations", [])]
        return cls(**data)
    
    def add_claim(self, claim: EvidenceClaim) -> EvidenceChain:
        """Add a claim to the chain."""
        self.claims.append(claim)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def add_attestation(self, attestation: EvidenceAttestation) -> EvidenceChain:
        """Add an attestation to the chain."""
        self.attestations.append(attestation)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================


def create_evidence_claim(
    text: str,
    summary: str = "",
    evidence_type: str = EvidenceType.OTHER.value,
    evidence_source: str = EvidenceSource.OTHER.value,
    status: str = EvidenceStatus.DRAFT.value,
    domain_tags: List[str] = None,
    author: Optional[str] = None,
    source_ref: Optional[str] = None,
    confidence_score: Optional[float] = None,
) -> EvidenceClaim:
    """Factory function to create an evidence claim with sensible defaults."""
    return EvidenceClaim(
        claim_id=str(uuid.uuid4()),
        text=text,
        summary=summary,
        evidence_type=evidence_type,
        evidence_source=evidence_source,
        status=status,
        domain_tags=domain_tags or [],
        author=author,
        source_ref=source_ref,
        confidence_score=confidence_score,
    )


def create_attestation(
    claim_id: str,
    attestation_type: str = AttestationType.REVIEW.value,
    attestation_status: str = AttestationStatus.PENDING.value,
    attested_by: Optional[str] = None,
    evidence: str = "",
    rationale: str = "",
) -> EvidenceAttestation:
    """Factory function to create an attestation."""
    return EvidenceAttestation(
        attestation_id=str(uuid.uuid4()),
        claim_id=claim_id,
        attestation_type=attestation_type,
        attestation_status=attestation_status,
        attested_by=attested_by,
        evidence=evidence,
        rationale=rationale,
    )


def create_evidence_chain(
    root_claim: EvidenceClaim,
    author: Optional[str] = None,
) -> EvidenceChain:
    """Factory function to create an evidence chain with a root claim."""
    chain = EvidenceChain(
        chain_id=str(uuid.uuid4()),
        root_claim_id=root_claim.claim_id,
        author=author,
    )
    chain.add_claim(root_claim)
    return chain


# ============================================================================
# INTEGRATION HOOKS (Minimally invasive)
# ============================================================================


def integrate_with_change_proposal(proposal_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal integration hook: add evidence references to change proposal.
    
    This is purely additive — no migration required.
    Matches ChangeProposal fields: evidence_claim_ids, evidence_chain_ids
    """
    if "evidence_claim_ids" not in proposal_dict:
        proposal_dict["evidence_claim_ids"] = []
    if "evidence_chain_ids" not in proposal_dict:
        proposal_dict["evidence_chain_ids"] = []
    return proposal_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal integration hook: add evidence summary to governance view.
    
    This is purely additive — no migration required.
    """
    if "evidence_summary" not in governance_dict:
        governance_dict["evidence_summary"] = ""
    if "evidence_confidence" not in governance_dict:
        governance_dict["evidence_confidence"] = 0.0
    return governance_dict


def integrate_with_operator_review(review_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal integration hook: add evidence fields to operator review.
    
    This is purely additive — no migration required.
    """
    if "evidence_claim_ids" not in review_dict:
        review_dict["evidence_claim_ids"] = []
    if "evidence_chain_ids" not in review_dict:
        review_dict["evidence_chain_ids"] = []
    if "evidence_summary" not in review_dict:
        review_dict["evidence_summary"] = ""
    if "evidence_confidence" not in review_dict:
        review_dict["evidence_confidence"] = 0.0
    return review_dict
