# knowledge_ingestion.py - Self-Architecture Core v26: Scientific / Institutional Knowledge Ingestion Layer
# Create a governed ingestion layer for high-trust external knowledge: papers, institutional publications,
# technical bulletins, guidelines, research summaries.
# Additive only, evidence-first, domain-aware, reversible, no uncontrolled crawling.
# No repo drift (local to WESLR scope).

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================


class SourceClass(str, Enum):
    """Types of knowledge sources."""
    # Academic and scientific
    PAPER = "paper"  # Academic paper (journal/conference)
    RESEARCH_SUMMARY = "research_summary"  # Summarized research findings
    
    # Institutional
    INSTITUTIONAL_PUBLICATION = "institutional_publication"  # Institutional report
    TECHNICAL_BULLETIN = "technical_bulletin"  # Technical guidance
    GUIDELINE = "guideline"  # Best practices/guidelines
    
    # Data and datasets
    DATASET_NOTE = "dataset_note"  # Dataset documentation
    
    # Other
    OTHER = "other"


class IngestionStatus(str, Enum):
    """Status of knowledge ingestion and review."""
    PENDING = "pending"  # Ingestion started but not complete
    INGESTED = "ingested"  # Knowledge ingested, awaiting review
    REVIEWED = "reviewed"  # Reviewed, verified as accurate
    TRUSTED = "trusted"  # Trusted source, automatic evidence generation
    CONTESTED = "contested"  # Disputed or contested information
    SUPERSEDED = "superseded"  # Superseded by newer knowledge


class EvidenceType(str, Enum):
    """Types of evidence claims generated from ingestion."""
    FACT = "fact"  # Direct factual claim
    METHOD = "method"  # Methodology or approach
    RESULT = "result"  # Research result or finding
    CAUTION = "caution"  # Warning or limitation
    CONTEXT = "context"  # Contextual information


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class EvidenceClaim:
    """An evidence claim generated from ingested knowledge."""
    
    claim_id: str
    text: str
    evidence_type: str  # EvidenceType.value
    confidence: float = 0.7  # 0.0-1.0
    domain_tags: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)  # Reference to ingestion ID
    provenance: Optional[str] = None  # Link to source material
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "evidence_type": self.evidence_type,
            "confidence": self.confidence,
            "domain_tags": self.domain_tags,
            "source_ids": self.source_ids,
            "provenance": self.provenance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceClaim:
        """Create from dictionary representation."""
        data["domain_tags"] = data.get("domain_tags", [])
        data["source_ids"] = data.get("source_ids", [])
        return cls(**data)


@dataclass
class KnowledgeIngestion:
    """A knowledge ingestion record with metadata and generated claims.
    
    Captures the complete ingestion pipeline from source to evidence claims.
    """
    
    ingestion_id: str
    source_class: str  # SourceClass.value
    title: str
    source_reference: str  # URL, DOI, or internal reference
    
    # Content
    summary: str = ""
    domain_tags: List[str] = field(default_factory=list)
    
    # Status
    ingestion_status: str = IngestionStatus.PENDING.value
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    
    # Generated evidence
    evidence_claims: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "ingestion_id": self.ingestion_id,
            "source_class": self.source_class,
            "title": self.title,
            "source_reference": self.source_reference,
            "summary": self.summary,
            "domain_tags": self.domain_tags,
            "ingestion_status": self.ingestion_status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "evidence_claims": self.evidence_claims,
            "ingested_at": self.ingested_at,
            "last_updated": self.last_updated,
            "author": self.author,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeIngestion:
        """Create from dictionary representation."""
        data["domain_tags"] = data.get("domain_tags", [])
        data["evidence_claims"] = data.get("evidence_claims", [])
        return cls(**data)
    
    def add_claim(self, claim: EvidenceClaim) -> KnowledgeIngestion:
        """Add an evidence claim to this ingestion."""
        self.evidence_claims.append(claim.to_dict())
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self
    
    def generate_claim(self, text: str, evidence_type: str, confidence: float = 0.7) -> EvidenceClaim:
        """Generate an evidence claim from this ingestion."""
        claim = EvidenceClaim(
            claim_id=f"{self.ingestion_id}-claim-{len(self.evidence_claims)}",
            text=text,
            evidence_type=evidence_type,
            confidence=confidence,
            domain_tags=list(self.domain_tags),
            source_ids=[self.ingestion_id],
        )
        self.add_claim(claim)
        return claim
    
    def set_status(self, status: str, reviewed_by: str = None) -> KnowledgeIngestion:
        """Update ingestion status."""
        self.ingestion_status = status
        self.last_updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if reviewed_by:
            self.reviewed_by = reviewed_by
            self.reviewed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return self


# ============================================================================
# INGESTION ENGINE
# ============================================================================


class KnowledgeIngestionEngine:
    """Engine for managing knowledge ingestion and evidence claim generation.
    
    Operates independently - no network access required.
    All ingestion is transparent and reversible.
    """
    
    def __init__(self, storage_path: Optional[Any] = None):
        """Initialize knowledge ingestion engine."""
        self.storage_path = storage_path
        self.ingestions: Dict[str, KnowledgeIngestion] = {}  # ingestion_id -> Ingestion
    
    def register_ingestion(self, ingestion: KnowledgeIngestion) -> KnowledgeIngestion:
        """Register a knowledge ingestion."""
        self.ingestions[ingestion.ingestion_id] = ingestion
        return ingestion
    
    def get_ingestion(self, ingestion_id: str) -> Optional[KnowledgeIngestion]:
        """Get an ingestion by ID."""
        return self.ingestions.get(ingestion_id)
    
    def create_ingestion(
        self,
        source_class: str,
        title: str,
        source_reference: str,
        summary: str = "",
        domain_tags: List[str] = None,
    ) -> KnowledgeIngestion:
        """Create a new knowledge ingestion."""
        domain_tags = domain_tags or []
        ingestion = KnowledgeIngestion(
            ingestion_id=f"ingest-{len(self.ingestions):04d}",
            source_class=source_class,
            title=title,
            source_reference=source_reference,
            summary=summary,
            domain_tags=domain_tags,
        )
        return self.register_ingestion(ingestion)
    
    def generate_claims_from_ingestion(
        self,
        ingestion_id: str,
        claims: List[Dict[str, Any]],
    ) -> List[EvidenceClaim]:
        """Generate evidence claims from an ingestion."""
        ingestion = self.get_ingestion(ingestion_id)
        if not ingestion:
            return []
        
        generated = []
        for claim_data in claims:
            claim = EvidenceClaim(
                claim_id=f"{ingestion_id}-claim-{len(ingestion.evidence_claims)}",
                text=claim_data.get("text", ""),
                evidence_type=claim_data.get("evidence_type", EvidenceType.FACT.value),
                confidence=claim_data.get("confidence", 0.7),
                domain_tags=claim_data.get("domain_tags", []),
                source_ids=[ingestion_id],
            )
            ingestion.add_claim(claim)
            generated.append(claim)
        
        return generated
    
    def get_trusted_claims(self, domain_tags: List[str] = None) -> List[EvidenceClaim]:
        """Get trusted evidence claims, optionally filtered by domain."""
        claims = []
        for ingestion in self.ingestions.values():
            if ingestion.ingestion_status == IngestionStatus.TRUSTED.value:
                for claim_dict in ingestion.evidence_claims:
                    claim = EvidenceClaim.from_dict(claim_dict)
                    if domain_tags is None or any(tag in claim.domain_tags for tag in domain_tags):
                        claims.append(claim)
        return claims
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert engine state to dictionary."""
        return {
            "ingestion_count": len(self.ingestions),
            "ingestions": {k: v.to_dict() for k, v in self.ingestions.items()},
        }


# ============================================================================
# INTEGRATION HOOKS (Additive)
# ============================================================================


def integrate_with_evidence_ontology(ontology_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add knowledge-ingestion metadata to evidence ontology.
    
    This is purely additive — no migration required.
    """
    if "source_classes" not in ontology_dict:
        ontology_dict["source_classes"] = [sc.value for sc in SourceClass]
    if "ingestion_status_values" not in ontology_dict:
        ontology_dict["ingestion_status_values"] = [s.value for s in IngestionStatus]
    if "knowledge_ingestions" not in ontology_dict:
        ontology_dict["knowledge_ingestions"] = []
    return ontology_dict


def integrate_with_domain_ontology(ontology_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add knowledge-ingestion integration to domain ontology.
    
    This is purely additive — no migration required.
    """
    if "knowledge_sources" not in ontology_dict:
        ontology_dict["knowledge_sources"] = []
    if "trusted_sources" not in ontology_dict:
        ontology_dict["trusted_sources"] = []
    if "ingestion_requirements" not in ontology_dict:
        ontology_dict["ingestion_requirements"] = {}
    return ontology_dict


def integrate_with_governance_view(governance_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add knowledge-ingestion context to governance view.
    
    This is purely additive — no migration required.
    """
    if "knowledge_ingestion_id" not in governance_dict:
        governance_dict["knowledge_ingestion_id"] = None
    if "knowledge_status" not in governance_dict:
        governance_dict["knowledge_status"] = None
    if "knowledge_trusted" not in governance_dict:
        governance_dict["knowledge_trusted"] = False
    return governance_dict


def integrate_with_proposal_realization(realization_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add knowledge-ingestion context to proposal realization.
    
    This is purely additive — no migration required.
    """
    if "knowledge_ingestion_id" not in realization_dict:
        realization_dict["knowledge_ingestion_id"] = None
    if "knowledge_confidence" not in realization_dict:
        realization_dict["knowledge_confidence"] = 0.0
    if "knowledge_claims" not in realization_dict:
        realization_dict["knowledge_claims"] = []
    return realization_dict
